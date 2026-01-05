#!/usr/bin/env python3
"""
Test Google Calendar connection
Run this after placing credentials.json in project root
"""
from integrations.google_calendar import GoogleCalendarClient
from datetime import datetime, timedelta

def test_connection():
    print("\n" + "="*60)
    print("Testing Google Calendar Connection")
    print("="*60 + "\n")

    try:
        # Initialize client (this will open browser for first-time auth)
        print("🔌 Connecting to Google Calendar...")
        client = GoogleCalendarClient()
        print("✅ Successfully connected!\n")

        # Get upcoming events
        print("📅 Fetching upcoming events (next 7 days)...\n")
        events = client.get_events(
            time_min=datetime.utcnow(),
            time_max=datetime.utcnow() + timedelta(days=7),
            max_results=10
        )

        if events:
            print(f"Found {len(events)} upcoming events:\n")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', '(No title)')
                print(f"  📌 {summary}")
                print(f"     {start}\n")
        else:
            print("No upcoming events found.\n")

        print("="*60)
        print("✅ Google Calendar integration is working!")
        print("="*60)

    except FileNotFoundError as e:
        print("❌ Error: credentials.json not found")
        print("\nPlease follow GOOGLE_CALENDAR_SETUP.md to:")
        print("  1. Create Google Cloud Project")
        print("  2. Enable Calendar API")
        print("  3. Download credentials.json")
        print(f"\nSave it to: /home/targeteer/ai-calendar-agent/credentials.json\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
        print("Check GOOGLE_CALENDAR_SETUP.md for troubleshooting.\n")

if __name__ == "__main__":
    test_connection()
