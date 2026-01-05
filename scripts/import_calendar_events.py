#!/usr/bin/env python3
"""
Import Google Calendar events to PostgreSQL database
Handles duplicates cleanly with ON CONFLICT
"""
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from integrations.google_calendar import GoogleCalendarClient
from database.connection import insert_calendar_event
import json


def parse_calendar_event(event: dict) -> dict:
    """Parse Google Calendar event into database format"""

    # Extract start and end times
    start = event['start'].get('dateTime') or event['start'].get('date')
    end = event['end'].get('dateTime') or event['end'].get('date')

    # Parse datetime strings
    if 'T' in start:  # DateTime
        start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
    else:  # All-day event (date only)
        start_time = datetime.fromisoformat(f"{start}T00:00:00+00:00")
        end_time = datetime.fromisoformat(f"{end}T00:00:00+00:00")

    # Check for external participants
    attendees = event.get('attendees', [])
    participant_count = len(attendees)

    # Check if creator is different from organizer (external meeting)
    creator_email = event.get('creator', {}).get('email', '')
    organizer_email = event.get('organizer', {}).get('email', '')
    has_external_participants = (
        participant_count > 1 or
        (creator_email != organizer_email and organizer_email)
    )

    # Extract tags from description or categories
    tags = []
    description = event.get('description', '')
    if 'focus' in description.lower() or 'focus' in event.get('summary', '').lower():
        tags.append('focus')
    if 'meeting' in event.get('summary', '').lower():
        tags.append('meeting')
    if attendees:
        tags.append('collaborative')

    return {
        'event_id': event['id'],
        'summary': event.get('summary', '(No title)'),
        'description': description,
        'start_time': start_time,
        'end_time': end_time,
        'has_external_participants': has_external_participants,
        'participant_count': participant_count,
        'tags': tags
    }


def import_calendar_events(days_past: int = 30, days_future: int = 90):
    """
    Import calendar events from Google Calendar to database

    Args:
        days_past: Number of days in the past to import (default: 30)
        days_future: Number of days in the future to import (default: 90)
    """
    print("=" * 60)
    print("Google Calendar Import")
    print("=" * 60 + "\n")

    # Connect to Google Calendar
    print("🔌 Connecting to Google Calendar...")
    try:
        client = GoogleCalendarClient()
        print("✅ Connected to Google Calendar\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # Calculate time range
    now = datetime.now(timezone.utc)
    time_min = now - timedelta(days=days_past)
    time_max = now + timedelta(days=days_future)

    print(f"📅 Fetching events from {time_min.date()} to {time_max.date()}...")

    try:
        # Fetch all events in range
        events = client.get_events(
            time_min=time_min,
            time_max=time_max,
            max_results=1000  # Get up to 1000 events
        )

        if not events:
            print("No events found in this time range.\n")
            return

        print(f"Found {len(events)} events\n")

        # Import events to database
        success_count = 0
        update_count = 0
        error_count = 0

        for event in events:
            try:
                # Parse event
                event_data = parse_calendar_event(event)

                # Insert to database (handles duplicates with ON CONFLICT)
                result_id = insert_calendar_event(event_data)

                if result_id:
                    success_count += 1
                    print(f"  ✅ {event_data['summary'][:50]}")
                    print(f"     {event_data['start_time'].strftime('%Y-%m-%d %H:%M')}")
                else:
                    # ON CONFLICT DO UPDATE was triggered
                    update_count += 1
                    print(f"  🔄 {event_data['summary'][:50]}")
                    print(f"     {event_data['start_time'].strftime('%Y-%m-%d %H:%M')} (updated)")

            except Exception as e:
                error_count += 1
                print(f"  ❌ Error importing event: {e}")

        # Summary
        print("\n" + "=" * 60)
        print("Import Summary")
        print("=" * 60)
        print(f"✅ New events:     {success_count}")
        print(f"🔄 Updated events: {update_count}")
        print(f"❌ Errors:         {error_count}")
        print(f"📊 Total:          {len(events)}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error fetching events: {e}\n")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='Import Google Calendar events to database')
    parser.add_argument(
        '--past',
        type=int,
        default=30,
        help='Number of days in the past to import (default: 30)'
    )
    parser.add_argument(
        '--future',
        type=int,
        default=90,
        help='Number of days in the future to import (default: 90)'
    )

    args = parser.parse_args()

    import_calendar_events(days_past=args.past, days_future=args.future)


if __name__ == "__main__":
    main()
