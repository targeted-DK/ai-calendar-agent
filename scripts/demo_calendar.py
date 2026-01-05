#!/usr/bin/env python3
"""
Demo script showing Google Calendar capabilities
"""
from integrations.google_calendar import GoogleCalendarClient
from datetime import datetime, timedelta, timezone

def main():
    print("\n" + "="*60)
    print("Google Calendar Demo")
    print("="*60 + "\n")

    client = GoogleCalendarClient()

    # 1. Create a test event
    print("📝 Creating test event: 'Focus Time' tomorrow at 2 PM...")
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    start = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=2)

    event = client.create_event(
        summary="Focus Time",
        start_time=start,
        end_time=end,
        description="Deep work session - created by AI Calendar Agent"
    )

    print(f"✅ Created event: {event['summary']}")
    print(f"   ID: {event['id']}")
    print(f"   Link: {event['htmlLink']}\n")

    # 2. Get upcoming events
    print("📅 Fetching all upcoming events...\n")
    events = client.get_events(
        time_min=datetime.now(timezone.utc),
        time_max=datetime.now(timezone.utc) + timedelta(days=30)
    )

    if events:
        print(f"Found {len(events)} upcoming events:\n")
        for evt in events[:5]:  # Show first 5
            start = evt['start'].get('dateTime', evt['start'].get('date'))
            print(f"  📌 {evt['summary']}")
            print(f"     Start: {start}")
            print(f"     ID: {evt['id']}\n")
    else:
        print("No upcoming events found.\n")

    # 3. Update the event we just created
    print(f"✏️  Updating event to 'Deep Work Session'...")
    updated = client.update_event(
        event_id=event['id'],
        summary="Deep Work Session",
        description="Updated by AI Calendar Agent - 2 hour focus block"
    )
    print(f"✅ Updated event title\n")

    # 4. Option to delete
    print("🗑️  Cleaning up test event...")
    client.delete_event(event['id'])
    print("✅ Deleted test event\n")

    print("="*60)
    print("✅ Demo complete! Your calendar integration is ready.")
    print("="*60)
    print("\nNext steps:")
    print("  • Import events to database with sync script")
    print("  • Use SchedulerOptimizerAgent to optimize your calendar")
    print("  • Auto-create focus blocks based on health data\n")

if __name__ == "__main__":
    main()
