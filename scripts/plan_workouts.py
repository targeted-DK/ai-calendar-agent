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
from typing import Dict, List, Optional
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


def load_goals() -> Dict:
    """Load goals and context from YAML config."""
    if not GOALS_FILE.exists():
        logger.warning(f"Goals file not found: {GOALS_FILE}")
        return {}

    with open(GOALS_FILE, 'r') as f:
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
            workouts.append({
                'type': activity.get('activityType', {}).get('typeKey', 'unknown'),
                'date': activity.get('startTimeLocal', '')[:10],
                'duration_min': round(activity.get('duration', 0) / 60),
                'calories': activity.get('calories', 0),
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
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            events.append({
                'title': summary,
                'start': start,
                'is_workout': summary.lower().startswith('workout:'),
            })
    except Exception as e:
        logger.warning(f"Could not get calendar: {e}")

    # Group by day
    events_by_day = {}
    for event in events:
        day = event['start'][:10] if event['start'] else 'unknown'
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event['title'])

    return {
        'total_events': len(events),
        'events_by_day': events_by_day,
        'existing_workouts': [e for e in events if e.get('is_workout')],
    }


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
) -> str:
    """Build comprehensive prompt for LLM."""

    # Format goals
    primary = goals.get('primary_goal', {})
    secondary = goals.get('secondary_goal', {})
    phase = goals.get('current_phase', 'base')
    weekly = goals.get('weekly_structure', {})
    hybrid_rules = goals.get('hybrid_rules', [])
    preferences = goals.get('preferences', {})

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

=== TODAY'S HEALTH (from Garmin) ===
Date: {health.get('date')}
Recovery Score: {health.get('recovery_score', 'unknown')}/100
Sleep: {health.get('sleep_hours', 'unknown')} hours
Stress Level: {health.get('avg_stress', 'unknown')}/100

=== RECENT WORKOUTS (last 7 days from Garmin) ===
{json.dumps(recent_workouts[:7], indent=2) if recent_workouts else 'No recent workouts'}

=== THIS WEEK'S PROGRESS ===
Completed: {json.dumps(week_progress.get('completed', {}), indent=2)}
Targets: {json.dumps(week_progress.get('targets', {}), indent=2)}

=== CALENDAR (next 7 days) ===
{json.dumps(calendar.get('events_by_day', {}), indent=2)}
Existing workouts scheduled: {len(calendar.get('existing_workouts', []))}

=== HYBRID TRAINING RULES ===
{chr(10).join('- ' + r for r in hybrid_rules.get('rules', [])) if isinstance(hybrid_rules, dict) else 'Standard hybrid rules apply'}

=== PREFERENCES ===
Preferred time: {preferences.get('preferred_workout_time', 'morning')}
Morning hours: {preferences.get('morning_hours', [6, 9])}
Max workout duration: {preferences.get('max_workout_minutes', 90)} minutes

=== YOUR TASK ===
Plan a workout for {target_date} ({target_date.strftime('%A')}).

Consider:
1. Recovery score and whether to go hard or easy
2. What workouts were done recently (avoid repeating same type back-to-back)
3. Weekly targets vs completed (what's missing?)
4. Calendar conflicts
5. Hybrid training rules (separate hard cardio from strength)
6. Any injuries or focus areas

Respond in this exact JSON format:
{{
    "should_workout": true/false,
    "reason_if_skip": "reason if should_workout is false",
    "workout": {{
        "type": "Run/Bike/Swim/Strength/Rest",
        "title": "Short title for calendar event",
        "duration_minutes": 45,
        "intensity": "easy/moderate/hard",
        "time_suggestion": "6:30 AM",
        "warmup": "5 min description",
        "main_workout": "Detailed main workout description",
        "cooldown": "5 min description",
        "target_hr_zone": "Zone 2 (130-145 bpm)" or null,
        "why_this_workout": "2-3 sentence explanation of why this workout fits today"
    }}
}}

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


def create_workout_event(
    calendar: GoogleCalendarClient,
    target_date: date,
    workout: Dict,
    dry_run: bool = False
) -> Optional[Dict]:
    """Create workout event in Google Calendar."""

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

    # Build description
    title = f"Workout: {workout.get('title', workout.get('type', 'Training'))}"

    description = f"""🎯 {workout.get('type', 'Workout')} - {workout.get('intensity', 'moderate').title()} Intensity

⏱️ Duration: {duration} minutes
{f"💓 Target: {workout.get('target_hr_zone')}" if workout.get('target_hr_zone') else ""}

🔥 WARM-UP:
{workout.get('warmup', 'Light movement for 5 minutes')}

💪 MAIN WORKOUT:
{workout.get('main_workout', 'Complete the planned workout')}

🧘 COOL-DOWN:
{workout.get('cooldown', 'Stretch and recover for 5 minutes')}

💡 WHY THIS WORKOUT:
{workout.get('why_this_workout', 'Scheduled based on your training plan')}

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


def has_existing_workout(calendar: GoogleCalendarClient, target_date: date) -> bool:
    """Check if workout already scheduled for this date."""
    day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=USER_TIMEZONE)
    day_end = day_start + timedelta(days=1)

    try:
        events = calendar.get_events(day_start, day_end)
        for event in events:
            if event.get('summary', '').lower().startswith('workout:'):
                return True
    except:
        pass
    return False


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

    for i in range(days_ahead):
        target_date = (datetime.now(USER_TIMEZONE) + timedelta(days=i)).date()
        logger.info(f"\n--- {target_date} ({target_date.strftime('%A')}) ---")

        # Check for existing workout
        if has_existing_workout(calendar, target_date):
            logger.info("Already has workout scheduled, skipping")
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
        )

        logger.info("Calling LLM...")
        llm_response = call_llm(prompt)

        if not llm_response:
            logger.error("LLM failed to respond")
            results.append({'date': str(target_date), 'status': 'llm_error'})
            continue

        # Check if LLM recommends workout
        if not llm_response.get('should_workout', True):
            reason = llm_response.get('reason_if_skip', 'Rest recommended')
            logger.info(f"LLM says skip: {reason}")
            results.append({'date': str(target_date), 'status': 'rest_day', 'reason': reason})
            continue

        workout = llm_response.get('workout', {})
        logger.info(f"LLM recommends: {workout.get('type')} - {workout.get('title')}")

        # Create event
        event = create_workout_event(calendar, target_date, workout, dry_run)

        if event:
            results.append({
                'date': str(target_date),
                'status': 'created' if not dry_run else 'dry_run',
                'workout': workout
            })

            # Update week progress for next iteration
            wtype = workout.get('type', '').lower()
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
