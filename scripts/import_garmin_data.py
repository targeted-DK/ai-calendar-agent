#!/usr/bin/env python3
"""
Garmin Data Import Script

Imports health metrics and activities from Garmin Connect API into PostgreSQL database.
Can be run manually or scheduled as a cron job for daily imports.

Usage:
    python scripts/import_garmin_data.py [--days=30] [--activities-only] [--health-only]
"""
import argparse
import sys
import json
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.garmin_connector import GarminConnector
from database.connection import Database, insert_health_metric
from config import settings


def import_health_data(connector: GarminConnector, days: int = 7) -> dict:
    """
    Import health data (sleep, stress, daily stats) from Garmin.

    Args:
        connector: GarminConnector instance
        days: Number of days to import (default 7)

    Returns:
        Dictionary with import statistics
    """
    print(f"\n📊 Importing health data for past {days} days...")

    stats = {'success': 0, 'errors': 0, 'skipped': 0}

    for i in range(days):
        target_date = date.today() - timedelta(days=i)

        try:
            # Get all health metrics for the date
            sleep = connector.get_sleep_data(target_date)
            daily_stats = connector.get_daily_stats(target_date)
            stress = connector.get_stress_data(target_date)
            recovery = connector.get_recovery_score(target_date)

            # Prepare data for database
            health_data = {
                'timestamp': f"{target_date} 00:00:00",
                'source': 'garmin' if connector._authenticated else 'garmin_mock',
                'sleep_duration_hours': sleep.get('sleep_duration_hours'),
                'sleep_quality_score': sleep.get('sleep_quality_score'),
                'deep_sleep_minutes': sleep.get('deep_sleep_minutes'),
                'rem_sleep_minutes': sleep.get('rem_sleep_minutes'),
                'awake_time_minutes': sleep.get('awake_time_minutes'),
                'resting_heart_rate': daily_stats.get('resting_heart_rate'),
                'avg_heart_rate': daily_stats.get('avg_heart_rate'),
                'max_heart_rate': daily_stats.get('max_heart_rate'),
                'stress_level': stress.get('avg_stress_level'),
                'recovery_score': recovery,
                'steps': daily_stats.get('steps'),
                'active_calories': daily_stats.get('active_calories'),
                'intensity_minutes': daily_stats.get('intensity_minutes'),
                'raw_data': json.dumps({
                    'sleep': sleep,
                    'daily_stats': daily_stats,
                    'stress': stress
                })
            }

            # Insert into database
            metric_id = insert_health_metric(health_data)

            if metric_id:
                print(f"  ✅ {target_date}: Recovery {recovery}/100, Sleep {sleep.get('sleep_duration_hours')}h")
                stats['success'] += 1
            else:
                print(f"  ⏭️  {target_date}: Already exists")
                stats['skipped'] += 1

        except Exception as e:
            print(f"  ❌ {target_date}: Error - {e}")
            stats['errors'] += 1

    return stats


def import_activities(connector: GarminConnector, days: int = 30) -> dict:
    """
    Import activities from Garmin.

    Args:
        connector: GarminConnector instance
        days: Number of days to look back (default 30)

    Returns:
        Dictionary with import statistics
    """
    print(f"\n🏃 Importing activities for past {days} days...")

    stats = {'success': 0, 'errors': 0, 'skipped': 0}

    try:
        start_date = date.today() - timedelta(days=days)
        activities = connector.get_activities(start_date=start_date, limit=100)

        for activity in activities:
            try:
                # Insert activity into database
                query = """
                INSERT INTO activity_data (
                    external_id, timestamp, source, activity_type,
                    duration_minutes, distance_km, elevation_gain_m,
                    avg_heart_rate, max_heart_rate, avg_power,
                    calories_burned, aerobic_training_effect,
                    anaerobic_training_effect, raw_data
                ) VALUES (
                    %(external_id)s, %(timestamp)s, %(source)s, %(activity_type)s,
                    %(duration_minutes)s, %(distance_km)s, %(elevation_gain_m)s,
                    %(avg_heart_rate)s, %(max_heart_rate)s, %(avg_power)s,
                    %(calories_burned)s, %(aerobic_training_effect)s,
                    %(anaerobic_training_effect)s, %(raw_data)s
                )
                ON CONFLICT (source, external_id) DO NOTHING
                RETURNING id
                """

                activity['source'] = 'garmin' if connector._authenticated else 'garmin_mock'
                activity['raw_data'] = json.dumps(activity.get('raw_data', {}))

                result = Database.execute_one(query, activity)

                if result:
                    act_type = activity.get('activity_type', 'unknown')
                    duration = activity.get('duration_minutes', 0)
                    distance = activity.get('distance_km', 0)
                    print(f"  ✅ {act_type}: {duration:.0f}min, {distance:.1f}km")
                    stats['success'] += 1
                else:
                    stats['skipped'] += 1

            except Exception as e:
                print(f"  ❌ Activity {activity.get('external_id')}: {e}")
                stats['errors'] += 1

    except Exception as e:
        print(f"❌ Error fetching activities: {e}")
        stats['errors'] += 1

    return stats


def main():
    """Main import function."""
    parser = argparse.ArgumentParser(description='Import data from Garmin Connect')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to import (default: 30)')
    parser.add_argument('--activities-only', action='store_true',
                       help='Import only activities')
    parser.add_argument('--health-only', action='store_true',
                       help='Import only health data')

    args = parser.parse_args()

    print("="*60)
    print("Garmin Data Import")
    print("="*60)

    # Initialize database
    Database.initialize_pool()

    # Create Garmin connector
    print("\n🔌 Connecting to Garmin...")
    connector = GarminConnector()

    total_stats = {'success': 0, 'errors': 0, 'skipped': 0}

    # Import health data
    if not args.activities_only:
        health_stats = import_health_data(connector, days=min(args.days, 30))
        for key in total_stats:
            total_stats[key] += health_stats[key]

    # Import activities
    if not args.health_only:
        activity_stats = import_activities(connector, days=args.days)
        for key in total_stats:
            total_stats[key] += activity_stats[key]

    # Summary
    print("\n" + "="*60)
    print("Import Summary")
    print("="*60)
    print(f"✅ Success: {total_stats['success']}")
    print(f"⏭️  Skipped: {total_stats['skipped']} (already in database)")
    print(f"❌ Errors:  {total_stats['errors']}")
    print("="*60)

    return 0 if total_stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
