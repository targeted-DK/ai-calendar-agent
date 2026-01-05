#!/usr/bin/env python3
"""
Workout Planner - LLM-powered comprehensive workout scheduling

This script:
1. Reads your goals and context from config/goals.yaml
2. Auto-gathers health data from Garmin
3. Auto-gathers calendar events from Google Calendar
4. Sends comprehensive context to LLM
5. Creates detailed workout events in Google Calendar

Usage:
    python scripts/plan_workouts.py              # Plan workouts
    python scripts/plan_workouts.py --dry-run    # Preview without creating
    python scripts/plan_workouts.py --days=7     # Plan for 7 days
"""
import argparse
import json
import logging
import os
import yaml
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "workout_planning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import project modules
from integrations.google_calendar import GoogleCalendarClient
from integrations.garmin_connector import GarminConnector
from database.connection import Database
from config import settings

# User timezone
USER_TIMEZONE = ZoneInfo(os.getenv('USER_TIMEZONE', 'America/Chicago'))

# Paths
GOALS_FILE = Path(__file__).parent.parent / "config" / "goals.yaml"
TEMPLATES_FILE = Path(__file__).parent.parent / "config" / "workout_templates.yaml"


def load_goals() -> Dict:
    """Load goals and context from YAML config."""
    if not GOALS_FILE.exists():
        logger.warning(f"Goals file not found: {GOALS_FILE}")
        return {}

    with open(GOALS_FILE, 'r') as f:
        return yaml.safe_load(f)


def load_templates() -> Dict:
    """Load workout templates for LLM reference."""
    if not TEMPLATES_FILE.exists():
        logger.warning(f"Templates file not found: {TEMPLATES_FILE}")
        return {}

    with open(TEMPLATES_FILE, 'r') as f:
        return yaml.safe_load(f)


def get_health_context(garmin: GarminConnector, days: int = 7) -> Dict:
    """Gather health data from Garmin."""
    today = datetime.now(USER_TIMEZONE).date()

    # Get today's/yesterday's health
    try:
        recovery = garmin.get_recovery_score(today)
    except:
        recovery = None

    try:
        sleep = garmin.get_sleep_data(today - timedelta(days=1))
    except:
        sleep = {}

    try:
        stress = garmin.get_stress_data(today)
    except:
        stress = {}

    return {
        'date': str(today),
        'recovery_score': recovery,
        'sleep_hours': sleep.get('sleep_duration_hours'),
        'sleep_quality': sleep.get('sleep_quality_score'),
        'avg_stress': stress.get('avg_stress_level'),
    }


def get_recent_workouts(garmin: GarminConnector, days: int = 7) -> List[Dict]:
    """Get recent workout history from Garmin."""
    workouts = []
    try:
        activities = garmin.get_activities(limit=20)
        for activity in activities[:10]:
            # Garmin connector returns processed data with flat keys
            workouts.append({
                'type': activity.get('activity_type', 'unknown'),
                'date': activity.get('timestamp', '')[:10],
                'duration_min': round(activity.get('duration_minutes', 0)),
                'calories': activity.get('calories_burned', 0),
            })
    except Exception as e:
        logger.warning(f"Could not get workout history: {e}")

    return workouts


def get_calendar_context(calendar: GoogleCalendarClient, days: int = 7) -> Dict:
    """Get calendar events and free slots."""
    now = datetime.now(USER_TIMEZONE)
    end = now + timedelta(days=days)

    events = []
    try:
        raw_events = calendar.get_events(now, end)
        for event in raw_events:
            summary = event.get('summary', 'Busy')
            start_raw = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            end_raw = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', ''))

            # Parse times for display
            start_time = ''
            end_time = ''
            if 'T' in start_raw:
                try:
                    start_dt = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_raw.replace('Z', '+00:00'))
                    start_time = start_dt.strftime('%H:%M')
                    end_time = end_dt.strftime('%H:%M')
                except:
                    pass

            events.append({
                'title': summary,
                'start': start_raw,
                'end': end_raw,
                'start_time': start_time,
                'end_time': end_time,
                'is_workout': summary.lower().startswith('workout:'),
            })
    except Exception as e:
        logger.warning(f"Could not get calendar: {e}")

    # Group by day WITH times
    events_by_day = {}
    for event in events:
        day = event['start'][:10] if event['start'] else 'unknown'
        if day not in events_by_day:
            events_by_day[day] = []

        # Include time in the event description
        if event['start_time'] and event['end_time']:
            event_str = f"{event['start_time']}-{event['end_time']}: {event['title']}"
        else:
            event_str = event['title']
        events_by_day[day].append(event_str)

    return {
        'total_events': len(events),
        'events_by_day': events_by_day,
        'existing_workouts': [e for e in events if e.get('is_workout')],
    }


def count_scheduled_workouts(existing_workouts: List[Dict]) -> Dict:
    """Count scheduled workouts by type from calendar events."""
    counts = {'runs': 0, 'bike': 0, 'swim': 0, 'strength': 0}

    for w in existing_workouts:
        title = w.get('title', '').lower()
        if any(x in title for x in ['run', 'running', 'jog']):
            counts['runs'] += 1
        elif any(x in title for x in ['bike', 'cycling', 'cycle', 'ride']):
            counts['bike'] += 1
        elif any(x in title for x in ['swim', 'pool']):
            counts['swim'] += 1
        elif any(x in title for x in ['strength', 'lift', 'weight', 'gym', 'squat', 'deadlift', 'bench']):
            counts['strength'] += 1

    return counts


def _format_scheduled_counts(scheduled: Dict, targets: Dict) -> str:
    """Format scheduled counts with warnings for over-scheduling."""
    lines = []
    for workout_type in ['runs', 'bike', 'swim', 'strength']:
        count = scheduled.get(workout_type, 0)
        target = targets.get(workout_type, 0)
        status = ""
        if target == 0:
            status = "(not in plan)"
        elif count >= target:
            status = "⚠️ AT/OVER TARGET - DO NOT ADD MORE!"
        elif count > 0:
            status = f"({target - count} more needed)"
        else:
            status = f"(need {target})"
        lines.append(f"- {workout_type.upper()}: {count} scheduled / {target} target {status}")
    return "\n".join(lines)


def get_week_progress(recent_workouts: List[Dict], goals: Dict) -> Dict:
    """Calculate this week's training progress vs targets."""
    # Get this week's workouts
    today = datetime.now(USER_TIMEZONE).date()
    week_start = today - timedelta(days=today.weekday())  # Monday

    this_week = [w for w in recent_workouts
                 if w.get('date') and w['date'] >= str(week_start)]

    # Count by type
    counts = {}
    for w in this_week:
        wtype = w.get('type', 'unknown').lower()
        if 'run' in wtype:
            counts['runs'] = counts.get('runs', 0) + 1
        elif 'cycling' in wtype or 'bike' in wtype:
            counts['bike'] = counts.get('bike', 0) + 1
        elif 'swim' in wtype:
            counts['swim'] = counts.get('swim', 0) + 1
        elif 'strength' in wtype or 'weight' in wtype:
            counts['strength'] = counts.get('strength', 0) + 1

    # Get targets from goals
    weekly = goals.get('weekly_structure', {})

    return {
        'week_start': str(week_start),
        'completed': counts,
        'targets': {
            'runs': weekly.get('run_sessions', 3),
            'bike': weekly.get('bike_sessions', 2),
            'swim': weekly.get('swim_sessions', 2),
            'strength': weekly.get('strength_sessions', 3),
        }
    }


def build_llm_prompt(
    goals: Dict,
    health: Dict,
    recent_workouts: List[Dict],
    calendar: Dict,
    week_progress: Dict,
    target_date: date,
    templates: Dict = None,
    created_this_run: List[Dict] = None,
) -> str:
    """Build comprehensive prompt for LLM."""
    created_this_run = created_this_run or []

    # Format goals
    primary = goals.get('primary_goal', {})
    secondary = goals.get('secondary_goal', {})
    phase = goals.get('current_phase', 'base')
    weekly = goals.get('weekly_structure', {})
    hybrid_rules = goals.get('hybrid_rules', [])
    preferences = goals.get('preferences', {})
    templates = templates or {}

    # Manual context from user
    current_notes = goals.get('current_notes', '')
    life_context = goals.get('life_context', {})
    injuries = goals.get('injuries', [])
    focus_areas = goals.get('focus_areas', [])
    avoid = goals.get('avoid', [])

    prompt = f"""You are a workout planning AI for someone training for an Ironman triathlon while also building muscle (hybrid training).

=== LONG-TERM GOALS ===
Primary: {primary.get('title', 'Ironman')} - {primary.get('description', '')}
Secondary: {secondary.get('title', 'Muscle Building')} - {secondary.get('description', '')}
Current Phase: {phase}
Balance: {hybrid_rules.get('endurance_priority', 0.6)*100:.0f}% endurance / {hybrid_rules.get('strength_priority', 0.4)*100:.0f}% strength

=== USER NOTES (from config) ===
{current_notes}

Work intensity: {life_context.get('work_intensity', 'normal')}
Stress factors: {life_context.get('stress_factors', 'none')}
Injuries: {injuries if injuries else 'none'}
Focus on: {', '.join(focus_areas) if focus_areas else 'general fitness'}
Avoid: {', '.join(avoid) if avoid else 'nothing specific'}

=== CURRENT HEALTH DATA (from Garmin - use as baseline) ===
Data from: {health.get('date')} (this is the latest available data)
Recovery Score: {health.get('recovery_score', 'unknown')}/100
Last night's Sleep: {health.get('sleep_hours', 'unknown')} hours
Current Stress Level: {health.get('avg_stress', 'unknown')}/100

NOTE: Use this as baseline. For future days, assume recovery will improve if rest day or easy workout,
decrease if hard workout. We don't have future health data - use judgment based on planned activities.

=== RECENT WORKOUTS (last 7 days from Garmin) ===
{json.dumps(recent_workouts[:7], indent=2) if recent_workouts else 'No recent workouts'}

=== THIS WEEK'S PROGRESS ===
Completed (from Garmin): {json.dumps(week_progress.get('completed', {}), indent=2)}
Targets: {json.dumps(week_progress.get('targets', {}), indent=2)}

=== SCHEDULED WORKOUTS COUNT (CRITICAL!) ===
{_format_scheduled_counts(count_scheduled_workouts(calendar.get('existing_workouts', [])), week_progress.get('targets', {}))}

=== CALENDAR (next 7 days) - IMPORTANT: Avoid scheduling during these times! ===
{json.dumps(calendar.get('events_by_day', {}), indent=2)}

=== ALREADY SCHEDULED WORKOUTS (DO NOT DUPLICATE TYPES ON CONSECUTIVE DAYS!) ===
{chr(10).join(f"- {w['start'][:10]}: {w['title']}" for w in calendar.get('existing_workouts', [])) if calendar.get('existing_workouts') else 'No workouts scheduled yet'}

=== WORKOUTS JUST PLANNED IN THIS SESSION (VERY IMPORTANT!) ===
{chr(10).join(f"- {w['date']}: {w['type']} - {w['title']}" for w in created_this_run) if created_this_run else 'None yet - you are planning the first day'}

CRITICAL: Look at SCHEDULED WORKOUTS COUNT above. Do NOT exceed weekly targets!
If runs are already at target, schedule BIKE or STRENGTH instead. Vary the workout types!

NOTE: Times shown as "HH:MM-HH:MM: Event". Schedule workouts BEFORE or AFTER these busy blocks, not during!

=== HYBRID TRAINING RULES ===
{chr(10).join('- ' + r for r in hybrid_rules.get('rules', [])) if isinstance(hybrid_rules, dict) else 'Standard hybrid rules apply'}

=== PREFERENCES ===
Preferred time: {preferences.get('preferred_workout_time', 'morning')}
Morning hours: {preferences.get('morning_hours', [6, 9])}
Evening hours: {preferences.get('evening_hours', [17, 20])} (fallback if morning blocked)
Max workout duration: {preferences.get('max_workout_minutes', 90)} minutes

SCHEDULING RULE: {"Try MORNING first. If morning is blocked by calendar events, schedule in EVENING instead." if preferences.get('preferred_workout_time') == 'flexible' else f"Schedule during {preferences.get('preferred_workout_time', 'morning')} hours."}

=== WORKOUT DETAIL FORMAT (IMPORTANT!) ===
Your workout descriptions must be HIGHLY DETAILED like these examples:

STRENGTH EXAMPLE:
{templates.get('strength_template', 'Include specific exercises, sets, reps, weights, and backup plan')}

RUN EXAMPLE:
{templates.get('run_template', 'Include warmup, duration, pace/zones, and backup plan')}

{templates.get('format_instructions', '')}

=== YOUR TASK ===
Plan TWO DIFFERENT workout options for {target_date} ({target_date.strftime('%A')}).

Give the user flexibility - they may not be able to do their preferred workout due to:
- Weather (can't run outside if raining)
- Equipment (bike broken, gym closed)
- Time constraints (gym farther than running trail)
- Social (gym workout with friend vs solo run)

CRITICAL: The two options MUST be different workout TYPES (e.g., Run + Strength, Bike + Yoga).
Same type with different intensity is NOT acceptable.

Consider:
1. Recovery score and whether to go hard or easy
2. What workouts were done recently (avoid repeating same type back-to-back)
3. Weekly targets vs completed (what's missing?)
4. Calendar conflicts - CHECK BUSY TIMES and schedule around them
5. Time preference - if morning is blocked, use evening slot
6. Hybrid training rules (separate hard cardio from strength)
7. Any injuries or focus areas

Respond in this exact JSON format. All workout fields must be PLAIN TEXT strings (not nested objects or arrays):
{{
    "should_workout": true,
    "reason_if_skip": "",
    "option_a": {{
        "type": "Run",
        "title": "Easy Zone 2 Run",
        "duration_minutes": 45,
        "intensity": "easy",
        "time_suggestion": "6:30 AM",
        "warmup": "5 min brisk walk, then dynamic stretches: leg swings (10 each leg), high knees (20), butt kicks (20). 2 min very easy jog.",
        "main_workout": "30-40 min easy running at conversational pace. Target HR: Zone 2 (130-145 bpm). Cadence: 170-180 spm. Stay on flat terrain.",
        "cooldown": "3 min walk, then static stretches: quads, hamstrings, calves (30 sec each side).",
        "backup_plan": "If low energy: reduce to 20 min easy jog, or substitute with 30 min brisk walk.",
        "target_hr_zone": "Zone 2 (130-145 bpm)",
        "why_this_workout": "Easy run to build aerobic base while allowing recovery."
    }},
    "option_b": {{
        "type": "Strength",
        "title": "Upper Body Push",
        "duration_minutes": 50,
        "intensity": "moderate",
        "time_suggestion": "6:30 AM",
        "warmup": "5 min light cardio (jumping jacks, arm circles), then band pull-aparts and wall slides.",
        "main_workout": "Bench Press 4x8 @70%, Overhead Press 3x10, Incline DB Press 3x12, Tricep Dips 3x12, Face Pulls 3x15.",
        "cooldown": "Chest and shoulder stretches, foam roll upper back.",
        "backup_plan": "If low energy: reduce to 3 sets each, drop weight by 10%.",
        "target_hr_zone": "N/A - strength training",
        "why_this_workout": "Upper body push day to build pressing strength and chest development."
    }}
}}

IMPORTANT:
- Both options MUST use the SAME time_suggestion (they overlap - user picks one)
- option_a and option_b MUST be DIFFERENT workout types
- All fields must be plain text strings, NOT objects or arrays
- Write workout details as readable sentences, not structured data
- Include specific numbers (sets, reps, weights, distances, times, HR zones)

Only respond with the JSON, no other text.
"""
    return prompt


def call_llm(prompt: str) -> Dict:
    """Call LLM (Ollama or OpenAI) and parse response."""
    import requests

    provider = settings.llm_provider

    if provider == "ollama":
        # Call Ollama
        try:
            response = requests.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            text = result.get('response', '{}')
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    elif provider == "openai":
        import openai
        client = openai.OpenAI(api_key=settings.openai_api_key)
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None
    else:
        logger.error(f"Unknown LLM provider: {provider}")
        return None

    # Parse JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {e}")
        logger.error(f"Response was: {text[:500]}")
        return None


def _sanitize_single_workout(workout: Dict, label: str) -> Tuple[Dict, List[str]]:
    """Sanitize a single workout option. Returns (sanitized_workout, issues)."""
    issues = []

    # Validate and fix time
    time_str = workout.get('time_suggestion', '6:30 AM')
    try:
        hour = 6
        minute = 0

        # Handle 24-hour format (e.g., "15:00", "17:30")
        if 'AM' not in time_str.upper() and 'PM' not in time_str.upper():
            # Try to parse as 24-hour format
            clean_time = time_str.split('-')[0].strip()  # Handle "15:00-16:00" -> "15:00"
            if ':' in clean_time:
                parts = clean_time.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
            else:
                raise ValueError(f"Invalid time format: {time_str}")
        else:
            # Handle AM/PM format
            parts = time_str.upper().replace('AM', '').replace('PM', '').strip().split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if 'PM' in time_str.upper() and hour != 12:
                hour += 12
            elif 'AM' in time_str.upper() and hour == 12:
                hour = 0

        # Validate hour is reasonable (5 AM - 9 PM)
        if hour < 5:
            issues.append(f"[{label}] Time too early ({time_str}), adjusting to 6:00 AM")
            workout['time_suggestion'] = '6:00 AM'
        elif hour > 21:
            issues.append(f"[{label}] Time too late ({time_str}), adjusting to 6:00 PM")
            workout['time_suggestion'] = '6:00 PM'
        else:
            # Convert to AM/PM format for consistency
            if hour < 12:
                workout['time_suggestion'] = f"{hour}:{minute:02d} AM"
            elif hour == 12:
                workout['time_suggestion'] = f"12:{minute:02d} PM"
            else:
                workout['time_suggestion'] = f"{hour - 12}:{minute:02d} PM"
    except:
        issues.append(f"[{label}] Invalid time format ({time_str}), defaulting to 6:30 AM")
        workout['time_suggestion'] = '6:30 AM'

    # Validate duration (15-180 minutes)
    duration = workout.get('duration_minutes', 45)
    try:
        duration = int(duration)
        if duration < 15:
            issues.append(f"[{label}] Duration too short ({duration} min), adjusting to 20 min")
            workout['duration_minutes'] = 20
        elif duration > 180:
            issues.append(f"[{label}] Duration too long ({duration} min), adjusting to 90 min")
            workout['duration_minutes'] = 90
    except:
        issues.append(f"[{label}] Invalid duration, defaulting to 45 min")
        workout['duration_minutes'] = 45

    # Validate workout type
    valid_types = ['run', 'bike', 'swim', 'strength', 'rest', 'yoga', 'walk', 'hike']
    workout_type = workout.get('type', '').lower()
    if not any(t in workout_type for t in valid_types):
        issues.append(f"[{label}] Unknown workout type ({workout_type})")

    # Ensure required text fields exist
    if not workout.get('warmup'):
        workout['warmup'] = 'Light movement for 5-10 minutes'
        issues.append(f"[{label}] Missing warmup, added default")

    if not workout.get('main_workout'):
        workout['main_workout'] = 'Complete planned workout'
        issues.append(f"[{label}] Missing main_workout description")

    if not workout.get('cooldown'):
        workout['cooldown'] = 'Stretch and recover for 5 minutes'
        issues.append(f"[{label}] Missing cooldown, added default")

    if not workout.get('backup_plan'):
        workout['backup_plan'] = 'Reduce intensity/duration by 50%, or substitute with easy walk'
        issues.append(f"[{label}] Missing backup_plan, added default")

    return workout, issues


def sanitize_workout_response(response: Dict, target_date: date) -> Dict:
    """Validate and sanitize LLM workout response with dual options."""
    if not response:
        return None

    all_issues = []

    # Check for dual options (new format) or single workout (old format)
    option_a = response.get('option_a', {})
    option_b = response.get('option_b', {})

    # Backward compatibility: if old format with single 'workout', convert
    if not option_a and not option_b and response.get('workout'):
        logger.info("Sanitizer: Converting single workout to dual format")
        option_a = response.get('workout')
        # Create option_b as a copy (user will get same workout twice - fallback)
        option_b = dict(option_a)
        all_issues.append("LLM returned single workout, duplicated as both options")

    if not option_a:
        logger.warning("Sanitizer: No option_a in response")
        return None

    if not option_b:
        logger.warning("Sanitizer: No option_b in response, duplicating option_a")
        option_b = dict(option_a)
        all_issues.append("Missing option_b, duplicated option_a")

    # Sanitize both options
    option_a, issues_a = _sanitize_single_workout(option_a, "A")
    option_b, issues_b = _sanitize_single_workout(option_b, "B")
    all_issues.extend(issues_a)
    all_issues.extend(issues_b)

    # Ensure both options use the same time (they should overlap)
    if option_a.get('time_suggestion') != option_b.get('time_suggestion'):
        logger.info(f"Syncing times: A={option_a.get('time_suggestion')}, B={option_b.get('time_suggestion')}")
        # Use option_a's time for both
        option_b['time_suggestion'] = option_a.get('time_suggestion')
        all_issues.append("Synced option_b time to match option_a")

    # Warn if both options are same type
    type_a = option_a.get('type', '').lower()
    type_b = option_b.get('type', '').lower()
    if extract_workout_type(type_a) == extract_workout_type(type_b):
        all_issues.append(f"WARNING: Both options are same type ({type_a})")
        logger.warning(f"Both workout options are same type: {type_a}")

    # Log issues
    if all_issues:
        logger.warning(f"Sanitizer fixed {len(all_issues)} issues:")
        for issue in all_issues:
            logger.warning(f"  - {issue}")

    response['option_a'] = option_a
    response['option_b'] = option_b
    response['_sanitized'] = True
    response['_issues'] = all_issues

    return response


def create_workout_event(
    calendar: GoogleCalendarClient,
    target_date: date,
    workout: Dict,
    dry_run: bool = False,
    option_label: str = None
) -> Optional[Dict]:
    """Create workout event in Google Calendar.

    Args:
        option_label: "A" or "B" for dual workout options, None for single workout
    """

    # Parse suggested time
    time_str = workout.get('time_suggestion', '6:30 AM')
    try:
        hour, minute = 6, 30  # Default
        if 'AM' in time_str or 'PM' in time_str:
            parts = time_str.replace('AM', '').replace('PM', '').strip().split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if 'PM' in time_str and hour != 12:
                hour += 12
    except:
        hour, minute = 6, 30

    start = datetime.combine(
        target_date,
        datetime.min.time().replace(hour=hour, minute=minute),
        tzinfo=USER_TIMEZONE
    )
    duration = workout.get('duration_minutes', 45)
    end = start + timedelta(minutes=duration)

    # Build title with option label
    workout_title = workout.get('title', workout.get('type', 'Training'))
    if option_label:
        label_emoji = "🅰️" if option_label == "A" else "🅱️"
        title = f"{label_emoji} Workout: {workout_title}"
        other_label = "B" if option_label == "A" else "A"
        choice_note = f"\n\n🔄 This is Option {option_label}. Delete this event if you're doing Option {other_label} instead."
    else:
        title = f"Workout: {workout_title}"
        choice_note = ""

    backup_plan = workout.get('backup_plan', '')
    backup_section = f"\n⚡ BACKUP PLAN (low energy day):\n{backup_plan}\n" if backup_plan else ""

    description = f"""🎯 {workout.get('type', 'Workout')} - {workout.get('intensity', 'moderate').title()} Intensity

⏱️ Duration: {duration} minutes
{f"💓 Target: {workout.get('target_hr_zone')}" if workout.get('target_hr_zone') else ""}

🔥 WARM-UP:
{workout.get('warmup', 'Light movement for 5 minutes')}

💪 MAIN WORKOUT:
{workout.get('main_workout', 'Complete the planned workout')}

🧘 COOL-DOWN:
{workout.get('cooldown', 'Stretch and recover for 5 minutes')}
{backup_section}
💡 WHY THIS WORKOUT:
{workout.get('why_this_workout', 'Scheduled based on your training plan')}
{choice_note}
---
Auto-scheduled by AI Calendar Agent
Based on recovery score, calendar, and training goals
"""

    if dry_run:
        logger.info(f"[DRY RUN] Would create: {title}")
        logger.info(f"  Time: {start.strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"  Duration: {duration} min")
        logger.info(f"  Why: {workout.get('why_this_workout', 'N/A')}")
        return {'dry_run': True, 'title': title}

    try:
        event = calendar.create_event(
            summary=title,
            start_time=start,
            end_time=end,
            description=description
        )
        logger.info(f"Created: {title} at {start.strftime('%Y-%m-%d %H:%M')}")
        return event
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        return None


def extract_workout_type(title: str) -> str:
    """Extract workout type from title like 'Workout: Easy Run' -> 'run'."""
    title_lower = title.lower()

    # Check for known types in the title
    if any(x in title_lower for x in ['run', 'running', 'jog']):
        return 'run'
    if any(x in title_lower for x in ['bike', 'cycling', 'cycle', 'ride']):
        return 'bike'
    if any(x in title_lower for x in ['swim', 'pool']):
        return 'swim'
    if any(x in title_lower for x in ['strength', 'lift', 'weight', 'gym']):
        return 'strength'
    if any(x in title_lower for x in ['yoga', 'stretch', 'mobility']):
        return 'yoga'
    if any(x in title_lower for x in ['walk', 'hike']):
        return 'walk'
    if 'rest' in title_lower:
        return 'rest'

    # Fallback: return first word after "Workout:"
    return title.replace('Workout:', '').strip().split()[0].lower()


def get_existing_workouts(calendar: GoogleCalendarClient, target_date: date) -> List[Dict]:
    """Get all existing workouts for a date (including A/B options)."""
    day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=USER_TIMEZONE)
    day_end = day_start + timedelta(days=1)

    workouts = []
    try:
        events = calendar.get_events(day_start, day_end)
        for event in events:
            summary = event.get('summary', '')
            # Match both "Workout:" and "🅰️ Workout:" / "🅱️ Workout:" formats
            if 'workout:' in summary.lower():
                workout_type = extract_workout_type(summary)
                option = None
                if '🅰️' in summary:
                    option = 'A'
                elif '🅱️' in summary:
                    option = 'B'
                workouts.append({
                    'id': event.get('id'),
                    'title': summary,
                    'type': workout_type,
                    'option': option,
                    'start': event.get('start', {}).get('dateTime', ''),
                })
        if not workouts:
            logger.info(f"No existing workout on {target_date}")
    except Exception as e:
        logger.warning(f"Error checking workouts for {target_date}: {e}")
    return workouts


def get_existing_workout(calendar: GoogleCalendarClient, target_date: date) -> Optional[Dict]:
    """Get existing workout for a date (backward compat - returns first found)."""
    workouts = get_existing_workouts(calendar, target_date)
    return workouts[0] if workouts else None


def delete_workout(calendar: GoogleCalendarClient, event_id: str, reason: str, dry_run: bool = False) -> bool:
    """Delete a workout event."""
    if dry_run:
        logger.info(f"[DRY RUN] Would delete workout: {reason}")
        return True
    try:
        calendar.delete_event(event_id)
        logger.info(f"Deleted workout: {reason}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete workout: {e}")
        return False


def should_reschedule(existing_workout: Dict, goals: Dict, week_progress: Dict) -> Tuple[bool, str]:
    """
    Determine if an existing workout should be deleted and rescheduled.

    Returns (should_reschedule, reason)
    """
    existing_type = existing_workout.get('type', '').lower()

    # Get configured workout types from goals
    weekly = goals.get('weekly_structure', {})
    configured_types = []
    if weekly.get('run_sessions', 0) > 0:
        configured_types.append('run')
    if weekly.get('bike_sessions', 0) > 0:
        configured_types.extend(['bike', 'cycling'])
    if weekly.get('swim_sessions', 0) > 0:
        configured_types.append('swim')
    if weekly.get('strength_sessions', 0) > 0:
        configured_types.extend(['strength', 'lifting', 'weight'])

    # Check if workout type is no longer in config
    type_still_valid = any(t in existing_type for t in configured_types) if configured_types else True
    if not type_still_valid:
        return True, f"Workout type '{existing_type}' no longer in goals config"

    # Check if we've already exceeded target for this type
    completed = week_progress.get('completed', {})
    targets = week_progress.get('targets', {})

    if 'run' in existing_type:
        if completed.get('runs', 0) >= targets.get('runs', 99):
            return True, f"Already met run target ({completed.get('runs')}/{targets.get('runs')})"
    elif any(t in existing_type for t in ['bike', 'cycling']):
        if completed.get('bike', 0) >= targets.get('bike', 99):
            return True, f"Already met bike target ({completed.get('bike')}/{targets.get('bike')})"
    elif 'swim' in existing_type:
        if completed.get('swim', 0) >= targets.get('swim', 99):
            return True, f"Already met swim target ({completed.get('swim')}/{targets.get('swim')})"
    elif any(t in existing_type for t in ['strength', 'lift', 'weight']):
        if completed.get('strength', 0) >= targets.get('strength', 99):
            return True, f"Already met strength target ({completed.get('strength')}/{targets.get('strength')})"

    return False, ""


def has_existing_workout(calendar: GoogleCalendarClient, target_date: date) -> bool:
    """Check if workout already scheduled for this date (backward compat)."""
    return get_existing_workout(calendar, target_date) is not None


def plan_workouts(days_ahead: int = 3, dry_run: bool = False) -> Dict:
    """Main function to plan workouts."""
    logger.info("=" * 60)
    logger.info(f"WORKOUT PLANNING (LLM-powered) - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"Planning for next {days_ahead} days (dry_run={dry_run})")
    logger.info("=" * 60)

    # Load goals
    goals = load_goals()
    if not goals:
        logger.error("No goals configured. Please edit config/goals.yaml")
        return {'success': False, 'error': 'No goals configured'}
    logger.info(f"Loaded goals: {goals.get('primary_goal', {}).get('title', 'Unknown')}")

    # Load workout templates
    templates = load_templates()
    logger.info(f"Loaded {len(templates)} workout templates")

    # Initialize connections
    try:
        calendar = GoogleCalendarClient()
        logger.info("Google Calendar connected")
    except Exception as e:
        logger.error(f"Could not connect to Google Calendar: {e}")
        return {'success': False, 'error': str(e)}

    garmin = GarminConnector()
    logger.info("Garmin connected")

    Database.initialize_pool()

    # Gather context (auto)
    health = get_health_context(garmin)
    logger.info(f"Health: Recovery={health.get('recovery_score')}, Sleep={health.get('sleep_hours')}hrs")

    recent_workouts = get_recent_workouts(garmin)
    logger.info(f"Recent workouts: {len(recent_workouts)} in last 7 days")

    calendar_context = get_calendar_context(calendar, days=7)
    logger.info(f"Calendar: {calendar_context.get('total_events')} events")

    week_progress = get_week_progress(recent_workouts, goals)
    logger.info(f"This week: {week_progress.get('completed')}")

    results = []

    # Track workouts created in THIS run (to avoid data race)
    created_this_run = []

    for i in range(days_ahead):
        target_date = (datetime.now(USER_TIMEZONE) + timedelta(days=i)).date()
        logger.info(f"\n--- {target_date} ({target_date.strftime('%A')}) ---")

        # Check for existing workouts (may have both A and B options)
        existing_workouts = get_existing_workouts(calendar, target_date)
        if existing_workouts:
            logger.info(f"Found {len(existing_workouts)} existing workout(s): {[w['title'] for w in existing_workouts]}")

            # Check if any should be rescheduled
            all_valid = True
            for existing in existing_workouts:
                needs_reschedule, reason = should_reschedule(existing, goals, week_progress)
                if needs_reschedule:
                    logger.info(f"RESCHEDULING: {reason}")
                    delete_workout(calendar, existing['id'], reason, dry_run)
                    all_valid = False

            if all_valid:
                logger.info("Existing workout(s) still valid, keeping")
                results.append({'date': str(target_date), 'status': 'already_scheduled'})
                continue

        # Build prompt and call LLM
        prompt = build_llm_prompt(
            goals=goals,
            health=health,
            recent_workouts=recent_workouts,
            calendar=calendar_context,
            week_progress=week_progress,
            target_date=target_date,
            templates=templates,
            created_this_run=created_this_run,
        )

        logger.info("Calling LLM...")
        llm_response = call_llm(prompt)

        if not llm_response:
            logger.error("LLM failed to respond")
            results.append({'date': str(target_date), 'status': 'llm_error'})
            continue

        # Sanitize and validate the response
        llm_response = sanitize_workout_response(llm_response, target_date)
        if not llm_response:
            logger.error("Response failed sanitization")
            results.append({'date': str(target_date), 'status': 'sanitization_error'})
            continue

        # Check if LLM recommends workout
        if not llm_response.get('should_workout', True):
            reason = llm_response.get('reason_if_skip', 'Rest recommended')
            logger.info(f"LLM says skip: {reason}")
            results.append({'date': str(target_date), 'status': 'rest_day', 'reason': reason})
            continue

        # Get both workout options
        option_a = llm_response.get('option_a', {})
        option_b = llm_response.get('option_b', {})

        logger.info(f"LLM recommends:")
        logger.info(f"  Option A: {option_a.get('type')} - {option_a.get('title')}")
        logger.info(f"  Option B: {option_b.get('type')} - {option_b.get('title')}")

        # Create both events (overlapping - user picks one)
        event_a = create_workout_event(calendar, target_date, option_a, dry_run, option_label="A")
        event_b = create_workout_event(calendar, target_date, option_b, dry_run, option_label="B")

        if event_a or event_b:
            results.append({
                'date': str(target_date),
                'status': 'created' if not dry_run else 'dry_run',
                'option_a': option_a,
                'option_b': option_b,
            })

            # Track both workouts for next iteration (count as ONE workout slot)
            created_this_run.append({
                'date': str(target_date),
                'type': f"{option_a.get('type', 'Unknown')} OR {option_b.get('type', 'Unknown')}",
                'title': f"Option A: {option_a.get('title', 'Workout')} | Option B: {option_b.get('title', 'Workout')}",
            })

            # Update week progress - count as ONE workout (user will do one, not both)
            # Use option_a's type for counting since it's the "primary" recommendation
            wtype = option_a.get('type', '').lower()
            if 'run' in wtype:
                week_progress['completed']['runs'] = week_progress['completed'].get('runs', 0) + 1
            elif 'bike' in wtype or 'cycling' in wtype:
                week_progress['completed']['bike'] = week_progress['completed'].get('bike', 0) + 1
            elif 'swim' in wtype:
                week_progress['completed']['swim'] = week_progress['completed'].get('swim', 0) + 1
            elif 'strength' in wtype:
                week_progress['completed']['strength'] = week_progress['completed'].get('strength', 0) + 1

    # Summary
    created = sum(1 for r in results if r.get('status') == 'created')
    rest = sum(1 for r in results if r.get('status') == 'rest_day')

    logger.info(f"\n{'=' * 60}")
    logger.info(f"SUMMARY: Created={created}, Rest days={rest}")
    logger.info("=" * 60)

    return {
        'success': True,
        'days_planned': days_ahead,
        'created': created,
        'rest_days': rest,
        'results': results
    }


def main():
    parser = argparse.ArgumentParser(description='LLM-powered workout planning')
    parser.add_argument('--days', type=int, default=3, help='Number of days to plan')
    parser.add_argument('--dry-run', action='store_true', help='Preview without creating')
    args = parser.parse_args()

    result = plan_workouts(days_ahead=args.days, dry_run=args.dry_run)

    # Save result
    log_file = LOG_DIR / "last_workout_plan.json"
    with open(log_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    if not result['success']:
        exit(1)


if __name__ == "__main__":
    main()
