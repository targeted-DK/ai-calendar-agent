#!/usr/bin/env python3
"""
Workout Reconciliation - Compare scheduled vs actual workouts AND detect conflicts

This script:
1. Gets past scheduled "Workout:" events from Google Calendar
2. Gets actual activities from Garmin
3. Matches them by date/time
4. Updates calendar events to reflect what was actually done
5. Logs discrepancies for pattern learning
6. Detects future workout conflicts with calendar events
7. Deletes conflicting workouts so planner can reschedule

Usage:
    python scripts/reconcile_workouts.py              # Reconcile + conflict check
    python scripts/reconcile_workouts.py --days=3     # Reconcile last 3 days
    python scripts/reconcile_workouts.py --dry-run    # Preview without changes
"""
import argparse
import json
import logging
import os
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
        logging.FileHandler(LOG_DIR / "reconciliation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import project modules
from integrations.google_calendar import GoogleCalendarClient
from integrations.garmin_connector import GarminConnector
from database.connection import Database

# User timezone
USER_TIMEZONE = ZoneInfo(os.getenv('USER_TIMEZONE', 'America/Chicago'))

# Activity type mapping (Garmin activity types to readable names)
GARMIN_ACTIVITY_MAP = {
    'running': 'Run',
    'cycling': 'Bike',
    'swimming': 'Swim',
    'strength_training': 'Strength',
    'walking': 'Walk',
    'hiking': 'Hike',
    'yoga': 'Yoga',
    'elliptical': 'Elliptical',
    'indoor_cycling': 'Indoor Bike',
    'treadmill_running': 'Treadmill Run',
    'lap_swimming': 'Swim',
    'open_water_swimming': 'Open Water Swim',
    'other': 'Other',
}


def get_scheduled_workouts(calendar: GoogleCalendarClient, days_back: int = 7) -> List[Dict]:
    """Get past scheduled workout events from Google Calendar."""
    now = datetime.now(USER_TIMEZONE)
    start = now - timedelta(days=days_back)

    # Only look at past events (up to now)
    events = calendar.get_events(start, now)

    workouts = []
    for event in events:
        summary = event.get('summary', '')
        # Match both "Workout:" and "🅰️ Workout:" / "🅱️ Workout:" formats
        if 'workout:' in summary.lower():
            start_time = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))

            # Extract option label (A, B, or None)
            option = None
            if '🅰️' in summary:
                option = 'A'
            elif '🅱️' in summary:
                option = 'B'

            # Extract workout type (after "Workout:")
            clean_title = summary.replace('🅰️', '').replace('🅱️', '').strip()
            planned_type = clean_title.replace('Workout:', '').strip().split()[0]

            workouts.append({
                'id': event.get('id'),
                'title': summary,
                'planned_type': planned_type,
                'option': option,
                'start_time': start_time,
                'date': start_time[:10] if start_time else None,
                'description': event.get('description', ''),
                'already_reconciled': '✓' in summary or '(Actual:' in summary,
            })

    return workouts


def get_garmin_activities(garmin: GarminConnector, days_back: int = 7) -> List[Dict]:
    """Get actual activities from Garmin."""
    activities = []
    try:
        raw_activities = garmin.get_activities(limit=50)

        cutoff = datetime.now(USER_TIMEZONE) - timedelta(days=days_back)

        for activity in raw_activities:
            # The connector returns custom format with 'timestamp' field
            start_str = activity.get('timestamp', '')
            if not start_str:
                continue

            # Parse date (format: "2026-01-04 07:39:06")
            activity_date = start_str[:10]

            # Check if within range
            try:
                activity_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                if activity_dt < cutoff.replace(tzinfo=None):
                    continue
            except:
                pass

            # Get activity type (connector returns 'activity_type' at top level)
            type_key = activity.get('activity_type', 'other').lower()
            readable_type = GARMIN_ACTIVITY_MAP.get(type_key, type_key.replace('_', ' ').title())

            # Get raw data for additional info
            raw = activity.get('raw_data', {})

            activities.append({
                'date': activity_date,
                'start_time': start_str,
                'type_key': type_key,
                'type_readable': readable_type,
                'duration_min': round(activity.get('duration_minutes', 0)),
                'calories': int(activity.get('calories_burned', 0)),
                'name': raw.get('activityName', ''),
            })

    except Exception as e:
        logger.error(f"Error getting Garmin activities: {e}")

    return activities


def match_workout_to_activity(workout: Dict, activities: List[Dict]) -> Optional[Dict]:
    """Find the Garmin activity that matches a scheduled workout."""
    workout_date = workout.get('date')
    if not workout_date:
        return None

    # Find activities on the same date
    same_day_activities = [a for a in activities if a.get('date') == workout_date]

    if not same_day_activities:
        return None

    # If only one activity, that's the match
    if len(same_day_activities) == 1:
        return same_day_activities[0]

    # Multiple activities - try to match by time proximity
    workout_time = workout.get('start_time', '')
    if workout_time:
        try:
            workout_dt = datetime.fromisoformat(workout_time.replace('Z', '+00:00'))

            best_match = None
            best_diff = timedelta(hours=24)

            for activity in same_day_activities:
                activity_time = activity.get('start_time', '')
                if activity_time:
                    activity_dt = datetime.fromisoformat(activity_time.replace('Z', '+00:00'))
                    diff = abs(workout_dt - activity_dt)
                    if diff < best_diff:
                        best_diff = diff
                        best_match = activity

            # Only match if within 4 hours
            if best_match and best_diff < timedelta(hours=4):
                return best_match
        except:
            pass

    # Fallback: return first activity of the day
    return same_day_activities[0]


def normalize_type(type_str: str) -> str:
    """Normalize workout type for comparison."""
    type_lower = type_str.lower()

    # Map variations to canonical forms
    if any(x in type_lower for x in ['run', 'treadmill']):
        return 'run'
    if any(x in type_lower for x in ['bike', 'cycling', 'cycle']):
        return 'bike'
    if any(x in type_lower for x in ['swim', 'pool']):
        return 'swim'
    if any(x in type_lower for x in ['strength', 'weight', 'lift', 'gym']):
        return 'strength'
    if any(x in type_lower for x in ['yoga', 'stretch', 'mobility']):
        return 'yoga'
    if any(x in type_lower for x in ['walk', 'hike']):
        return 'walk'
    if any(x in type_lower for x in ['rest', 'recovery']):
        return 'rest'

    return type_lower


def types_match(planned: str, actual: str) -> bool:
    """Check if planned and actual workout types match."""
    return normalize_type(planned) == normalize_type(actual)


def update_calendar_event(
    calendar: GoogleCalendarClient,
    event_id: str,
    planned_type: str,
    actual_activity: Dict,
    dry_run: bool = False
) -> bool:
    """Update calendar event to reflect actual workout (time, title, description)."""
    actual_type = actual_activity.get('type_readable', 'Unknown')
    duration = actual_activity.get('duration_min', 0)

    # Build new title
    if types_match(planned_type, actual_type):
        new_title = f"Workout: {actual_type} ✓"
    else:
        new_title = f"Workout: {actual_type} ✓ (Planned: {planned_type})"

    # Parse actual start time from Garmin
    actual_start = None
    actual_end = None
    activity_time_str = actual_activity.get('start_time', '')
    if activity_time_str:
        try:
            # Format: "2026-01-04 07:39:06"
            actual_start = datetime.strptime(activity_time_str, '%Y-%m-%d %H:%M:%S')
            actual_start = actual_start.replace(tzinfo=USER_TIMEZONE)
            actual_end = actual_start + timedelta(minutes=duration)
            logger.info(f"  Moving event to actual time: {actual_start.strftime('%H:%M')}")
        except Exception as e:
            logger.warning(f"  Could not parse activity time: {e}")

    # Build updated description
    description_update = f"""
---
✅ RECONCILED: Actual workout recorded from Garmin

Actual: {actual_type}
Duration: {duration} min
Calories: {actual_activity.get('calories', 'N/A')}
{f"Planned: {planned_type}" if not types_match(planned_type, actual_type) else ""}

Reconciled: {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M')}
"""

    if dry_run:
        logger.info(f"[DRY RUN] Would update event to: {new_title}")
        if actual_start:
            logger.info(f"[DRY RUN] Would move to: {actual_start.strftime('%Y-%m-%d %H:%M')}")
        return True

    try:
        calendar.update_event(
            event_id=event_id,
            summary=new_title,
            description=description_update,
            start_time=actual_start,
            end_time=actual_end
        )
        logger.info(f"Updated event: {new_title}")
        return True
    except Exception as e:
        logger.error(f"Failed to update event {event_id}: {e}")
        return False


def log_discrepancy(workout: Dict, actual_activity: Optional[Dict], db_conn=None):
    """Log discrepancy between planned and actual workout for learning."""
    discrepancy = {
        'date': workout.get('date'),
        'planned_type': workout.get('planned_type'),
        'actual_type': actual_activity.get('type_readable') if actual_activity else 'skipped',
        'actual_duration': actual_activity.get('duration_min') if actual_activity else 0,
        'matched': actual_activity is not None,
        'types_matched': types_match(
            workout.get('planned_type', ''),
            actual_activity.get('type_readable', '')
        ) if actual_activity else False,
        'recorded_at': datetime.now(USER_TIMEZONE).isoformat(),
    }

    # Log to file
    discrepancy_file = LOG_DIR / "workout_discrepancies.jsonl"
    with open(discrepancy_file, 'a') as f:
        f.write(json.dumps(discrepancy) + '\n')

    # TODO: Also store in PostgreSQL for pattern learning
    # if db_conn:
    #     db_conn.execute(...)

    return discrepancy


# =============================================================================
# CONFLICT DETECTION (Future workouts)
# =============================================================================

def get_future_workouts(calendar: GoogleCalendarClient, days_ahead: int = 7) -> List[Dict]:
    """Get future scheduled workout events."""
    now = datetime.now(USER_TIMEZONE)
    end = now + timedelta(days=days_ahead)

    events = calendar.get_events(now, end)

    workouts = []
    for event in events:
        summary = event.get('summary', '')
        if summary.lower().startswith('workout:'):
            start_str = event.get('start', {}).get('dateTime', '')
            end_str = event.get('end', {}).get('dateTime', '')

            if start_str and end_str:
                try:
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    workouts.append({
                        'id': event.get('id'),
                        'title': summary,
                        'start': start_dt,
                        'end': end_dt,
                        'date': start_str[:10],
                    })
                except:
                    pass

    return workouts


def get_other_events(calendar: GoogleCalendarClient, days_ahead: int = 7) -> List[Dict]:
    """Get non-workout calendar events (work, meetings, etc.)."""
    now = datetime.now(USER_TIMEZONE)
    end = now + timedelta(days=days_ahead)

    events = calendar.get_events(now, end)

    other_events = []
    for event in events:
        summary = event.get('summary', '')
        # Skip workout events
        if summary.lower().startswith('workout:'):
            continue

        start_str = event.get('start', {}).get('dateTime', '')
        end_str = event.get('end', {}).get('dateTime', '')

        if start_str and end_str:
            try:
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                other_events.append({
                    'title': summary,
                    'start': start_dt,
                    'end': end_dt,
                    'date': start_str[:10],
                })
            except:
                pass

    return other_events


def times_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
    """Check if two time ranges overlap."""
    return start1 < end2 and start2 < end1


def find_conflicts(workouts: List[Dict], other_events: List[Dict]) -> List[Dict]:
    """Find workouts that conflict with other calendar events."""
    conflicts = []

    for workout in workouts:
        for event in other_events:
            if times_overlap(workout['start'], workout['end'], event['start'], event['end']):
                conflicts.append({
                    'workout': workout,
                    'conflicts_with': event,
                })
                break  # One conflict is enough to flag this workout

    return conflicts


def resolve_conflicts(
    calendar: GoogleCalendarClient,
    conflicts: List[Dict],
    dry_run: bool = False
) -> Dict:
    """Delete workouts that conflict with other events."""
    results = {
        'total_conflicts': len(conflicts),
        'deleted': 0,
        'details': [],
    }

    for conflict in conflicts:
        workout = conflict['workout']
        other = conflict['conflicts_with']

        logger.info(f"CONFLICT: {workout['title']} ({workout['start'].strftime('%a %H:%M')})")
        logger.info(f"  overlaps with: {other['title']} ({other['start'].strftime('%H:%M')}-{other['end'].strftime('%H:%M')})")

        if dry_run:
            logger.info(f"  [DRY RUN] Would delete workout")
            results['details'].append({
                'workout': workout['title'],
                'workout_time': workout['start'].isoformat(),
                'conflict_with': other['title'],
                'action': 'would_delete',
            })
        else:
            try:
                calendar.delete_event(workout['id'])
                logger.info(f"  Deleted workout - will be rescheduled")
                results['deleted'] += 1
                results['details'].append({
                    'workout': workout['title'],
                    'workout_time': workout['start'].isoformat(),
                    'conflict_with': other['title'],
                    'action': 'deleted',
                })
            except Exception as e:
                logger.error(f"  Failed to delete: {e}")

    return results


def check_future_conflicts(calendar: GoogleCalendarClient, days_ahead: int = 7, dry_run: bool = False) -> Dict:
    """Main function to check and resolve future workout conflicts."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("CONFLICT DETECTION (future workouts)")
    logger.info(f"Checking next {days_ahead} days")
    logger.info("=" * 60)

    # Get workouts and other events
    workouts = get_future_workouts(calendar, days_ahead)
    logger.info(f"Future workouts: {len(workouts)}")

    other_events = get_other_events(calendar, days_ahead)
    logger.info(f"Other events: {len(other_events)}")

    # Find conflicts
    conflicts = find_conflicts(workouts, other_events)

    if not conflicts:
        logger.info("No conflicts found")
        return {'conflicts': 0, 'deleted': 0}

    logger.info(f"Found {len(conflicts)} conflict(s)")

    # Resolve conflicts
    results = resolve_conflicts(calendar, conflicts, dry_run)

    logger.info("")
    logger.info(f"CONFLICT RESOLUTION: {results['deleted']} workouts deleted")
    logger.info("(Planner will reschedule at better times on next run)")

    return results


# =============================================================================
# HEALTH-BASED ADAPTATION (Modify workouts based on current health)
# =============================================================================

# Thresholds for triggering adaptation
LOW_RECOVERY_THRESHOLD = 50  # Below this = suggest easier workout
LOW_SLEEP_THRESHOLD = 5.5    # Below this hours = suggest easier workout
HIGH_STRESS_THRESHOLD = 60   # Above this = suggest easier workout


def get_current_health(garmin: GarminConnector) -> Dict:
    """Get today's health metrics from Garmin."""
    today = datetime.now(USER_TIMEZONE).date()

    health = {
        'date': str(today),
        'recovery': None,
        'sleep_hours': None,
        'stress': None,
        'needs_adaptation': False,
        'reasons': [],
    }

    try:
        health['recovery'] = garmin.get_recovery_score(today)
    except:
        pass

    try:
        sleep = garmin.get_sleep_data(today - timedelta(days=1))
        health['sleep_hours'] = sleep.get('sleep_duration_hours')
    except:
        pass

    try:
        stress = garmin.get_stress_data(today)
        health['stress'] = stress.get('avg_stress_level')
    except:
        pass

    # Check if adaptation needed
    if health['recovery'] and health['recovery'] < LOW_RECOVERY_THRESHOLD:
        health['needs_adaptation'] = True
        health['reasons'].append(f"Low recovery ({health['recovery']:.0f}/100)")

    if health['sleep_hours'] and health['sleep_hours'] < LOW_SLEEP_THRESHOLD:
        health['needs_adaptation'] = True
        health['reasons'].append(f"Poor sleep ({health['sleep_hours']:.1f} hours)")

    if health['stress'] and health['stress'] > HIGH_STRESS_THRESHOLD:
        health['needs_adaptation'] = True
        health['reasons'].append(f"High stress ({health['stress']:.0f}/100)")

    return health


def get_todays_workout(calendar: GoogleCalendarClient) -> Optional[Dict]:
    """Get today's scheduled workout if it exists."""
    now = datetime.now(USER_TIMEZONE)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    events = calendar.get_events(today_start, today_end)

    for event in events:
        summary = event.get('summary', '')
        if summary.lower().startswith('workout:') and '⚠️' not in summary:
            # Skip already-adapted workouts
            return {
                'id': event.get('id'),
                'title': summary,
                'description': event.get('description', ''),
                'start': event.get('start', {}).get('dateTime', ''),
            }

    return None


def adapt_workout_for_low_energy(
    calendar: GoogleCalendarClient,
    workout: Dict,
    health: Dict,
    dry_run: bool = False
) -> bool:
    """Update workout to emphasize backup plan due to poor health."""

    reasons = ', '.join(health['reasons'])
    new_title = f"⚠️ {workout['title']} (Use Backup Plan)"

    # Prepend warning to description
    warning = f"""⚠️ LOW ENERGY ALERT ⚠️
Your body needs extra recovery today.
Reasons: {reasons}

👉 STRONGLY RECOMMEND using the BACKUP PLAN below instead of the full workout.
Listen to your body - it's okay to take it easy!

{'='*50}

"""
    new_description = warning + workout['description']

    if dry_run:
        logger.info(f"[DRY RUN] Would adapt workout: {new_title}")
        logger.info(f"  Reasons: {reasons}")
        return True

    try:
        calendar.update_event(
            event_id=workout['id'],
            summary=new_title,
            description=new_description
        )
        logger.info(f"Adapted workout: {new_title}")
        logger.info(f"  Reasons: {reasons}")
        return True
    except Exception as e:
        logger.error(f"Failed to adapt workout: {e}")
        return False


def check_health_adaptation(
    calendar: GoogleCalendarClient,
    garmin: GarminConnector,
    dry_run: bool = False
) -> Dict:
    """Check health and adapt today's workout if needed."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("HEALTH-BASED ADAPTATION CHECK")
    logger.info("=" * 60)

    results = {
        'health_checked': True,
        'adaptation_needed': False,
        'adapted': False,
    }

    # Get current health
    health = get_current_health(garmin)
    logger.info(f"Recovery: {health['recovery']}")
    logger.info(f"Sleep: {health['sleep_hours']} hours")
    logger.info(f"Stress: {health['stress']}")

    if not health['needs_adaptation']:
        logger.info("Health looks good - no adaptation needed")
        return results

    results['adaptation_needed'] = True
    logger.info(f"⚠️ Adaptation needed: {', '.join(health['reasons'])}")

    # Check if there's a workout today
    workout = get_todays_workout(calendar)
    if not workout:
        logger.info("No workout scheduled today")
        return results

    logger.info(f"Found today's workout: {workout['title']}")

    # Adapt the workout
    if adapt_workout_for_low_energy(calendar, workout, health, dry_run):
        results['adapted'] = True

    return results


def reconcile_workouts(days_back: int = 7, dry_run: bool = False, force: bool = False) -> Dict:
    """Main reconciliation function."""
    logger.info("=" * 60)
    logger.info(f"WORKOUT RECONCILIATION - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"Looking back {days_back} days (dry_run={dry_run})")
    logger.info("=" * 60)

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

    # Get data
    scheduled = get_scheduled_workouts(calendar, days_back)
    logger.info(f"Found {len(scheduled)} scheduled workouts in past {days_back} days")

    activities = get_garmin_activities(garmin, days_back)
    logger.info(f"Found {len(activities)} Garmin activities in past {days_back} days")

    # Results
    results = {
        'total_scheduled': len(scheduled),
        'already_reconciled': 0,
        'matched': 0,
        'type_mismatch': 0,
        'no_activity': 0,
        'updated': 0,
        'discrepancies': [],
    }

    for workout in scheduled:
        logger.info(f"\n--- {workout['date']}: {workout['title']} ---")

        # Skip already reconciled (unless force flag is set)
        if workout['already_reconciled'] and not force:
            logger.info("Already reconciled, skipping")
            results['already_reconciled'] += 1
            continue
        elif workout['already_reconciled'] and force:
            logger.info("Already reconciled, but --force flag set, re-processing")

        # Find matching activity
        activity = match_workout_to_activity(workout, activities)

        if not activity:
            logger.info(f"No Garmin activity found for {workout['date']}")
            results['no_activity'] += 1
            discrepancy = log_discrepancy(workout, None)
            results['discrepancies'].append(discrepancy)
            continue

        results['matched'] += 1
        planned = workout['planned_type']
        actual = activity['type_readable']

        if types_match(planned, actual):
            logger.info(f"Match! Planned: {planned}, Actual: {actual}")
        else:
            logger.info(f"MISMATCH! Planned: {planned}, Actual: {actual}")
            results['type_mismatch'] += 1
            discrepancy = log_discrepancy(workout, activity)
            results['discrepancies'].append(discrepancy)

        # Update calendar event
        if update_calendar_event(calendar, workout['id'], planned, activity, dry_run):
            results['updated'] += 1

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("RECONCILIATION SUMMARY")
    logger.info(f"  Scheduled workouts: {results['total_scheduled']}")
    logger.info(f"  Already reconciled: {results['already_reconciled']}")
    logger.info(f"  Matched to activity: {results['matched']}")
    logger.info(f"  Type mismatches: {results['type_mismatch']}")
    logger.info(f"  No activity found: {results['no_activity']}")
    logger.info(f"  Events updated: {results['updated']}")
    logger.info("=" * 60)

    results['success'] = True
    return results


def main():
    parser = argparse.ArgumentParser(description='Reconcile scheduled vs actual workouts')
    parser.add_argument('--days', type=int, default=7, help='Days to look back/ahead')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating')
    parser.add_argument('--force', action='store_true', help='Re-reconcile already processed workouts')
    args = parser.parse_args()

    # Part 1: Reconcile past workouts (plan vs actual)
    result = reconcile_workouts(days_back=args.days, dry_run=args.dry_run, force=args.force)

    # Part 2: Check for future conflicts
    if result.get('success'):
        try:
            calendar = GoogleCalendarClient()
            conflict_result = check_future_conflicts(calendar, days_ahead=args.days, dry_run=args.dry_run)
            result['conflict_check'] = conflict_result
        except Exception as e:
            logger.error(f"Conflict check failed: {e}")
            result['conflict_check'] = {'error': str(e)}

    # Part 3: Check health and adapt today's workout if needed
    if result.get('success'):
        try:
            calendar = GoogleCalendarClient()
            garmin = GarminConnector()
            health_result = check_health_adaptation(calendar, garmin, dry_run=args.dry_run)
            result['health_adaptation'] = health_result
        except Exception as e:
            logger.error(f"Health adaptation check failed: {e}")
            result['health_adaptation'] = {'error': str(e)}

    # Save result
    log_file = LOG_DIR / "last_reconciliation.json"
    with open(log_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    if not result['success']:
        exit(1)


if __name__ == "__main__":
    main()
