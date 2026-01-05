# Google Calendar API Setup Guide

This guide shows you how to connect your Google Calendar so the AI can read and modify events.

## Overview

You need to:
1. Create a Google Cloud Project
2. Enable Google Calendar API
3. Download OAuth credentials
4. Run authentication (opens browser once)
5. Test the connection

## Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)

2. Click **"Create Project"** (top left)
   - Name: `Workout schedule optimization`
   - Click **Create**

3. Wait for project creation (30 seconds)

### Step 2: Enable Google Calendar API

1. In the search bar at top, search: **"Calendar API"**

2. Click **"Google Calendar API"**

3. Click **"Enable"**

4. Wait for API to enable (10 seconds)

### Step 3: Create OAuth Credentials

1. Click **"Credentials"** in left sidebar

2. Click **"+ CREATE CREDENTIALS"** at top

3. Select **"OAuth client ID"**

4. If prompted "Configure consent screen":
   - Click **"Configure Consent Screen"**
   - Select **"External"** (unless you have Workspace)
   - Click **Create**

   Fill in:
   - **App name**: `Workout schedule optimization`
   - **User support email**: Your email
   - **Developer contact**: Your email
   - Click **Save and Continue**

   Scopes page:
   - Click **Add or Remove Scopes**
   - Search: `calendar`
   - Check: **Google Calendar API** (`.../auth/calendar`)
   - Click **Update**
   - Click **Save and Continue**

   Test users:
   - Click **+ Add Users**
   - Enter your Gmail address
   - Click **Save and Continue**

   Summary:
   - Click **Back to Dashboard**

5. Now go back to **Credentials** tab (left sidebar)

6. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**

7. Application type: **"Desktop app"**
   - Name: `Workout schedule optimization Desktop`
   - Click **Create**

8. **Download credentials:**
   - Click **Download JSON** (download icon)
   - Save as `credentials.json` in your project root:
     ```bash
     /home/targeteer/ai-calendar-agent/credentials.json
     ```

### Step 4: First-Time Authentication

Run this to authenticate (opens browser once):

```bash
cd /home/targeteer/ai-calendar-agent
source venv/bin/activate
python -c "from integrations.google_calendar import GoogleCalendarClient; client = GoogleCalendarClient(); print('✅ Connected!')"
```

**What happens:**
1. Browser opens automatically
2. Google asks: "AI Calendar Agent wants to access your Google Calendar"
3. Click **Continue**
4. Select your Google account
5. Click **Allow**
6. You'll see: "The authentication flow has completed"
7. Close browser tab

**Result:** Creates `token.json` (saved automatically, reused forever)

### Step 5: Test It!

Get your upcoming events:

```bash
python -c "
from integrations.google_calendar import GoogleCalendarClient
from datetime import datetime, timedelta

client = GoogleCalendarClient()
events = client.get_events(
    time_min=datetime.utcnow(),
    time_max=datetime.utcnow() + timedelta(days=7)
)

print(f'Found {len(events)} events in the next 7 days:')
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(f\"  - {event['summary']} at {start}\")
"
```

## What You Can Do Now

### Read Events

```python
from integrations.google_calendar import GoogleCalendarClient
from datetime import datetime, timedelta

client = GoogleCalendarClient()

# Get next 7 days
events = client.get_events(
    time_min=datetime.utcnow(),
    time_max=datetime.utcnow() + timedelta(days=7)
)

for event in events:
    print(f"{event['summary']} - {event['start']['dateTime']}")
```

### Create Event

```python
from integrations.google_calendar import GoogleCalendarClient
from datetime import datetime, timedelta

client = GoogleCalendarClient()

# Create "Focus Time" block tomorrow at 2 PM
tomorrow = datetime.utcnow() + timedelta(days=1)
start = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
end = start + timedelta(hours=2)

event = client.create_event(
    summary="Focus Time",
    start_time=start,
    end_time=end,
    description="Deep work - no interruptions"
)

print(f"✅ Created: {event['htmlLink']}")
```

### Update Event

```python
client = GoogleCalendarClient()

# Get event
events = client.get_events(max_results=1)
event = events[0]

# Move it 1 hour later
start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
new_start = start + timedelta(hours=1)
new_end = new_start + timedelta(hours=1)

updated = client.update_event(
    event_id=event['id'],
    start_time=new_start,
    end_time=new_end
)

print(f"✅ Rescheduled to {new_start}")
```

### Delete Event

```python
client = GoogleCalendarClient()

# Get event
events = client.get_events(max_results=1)
event_id = events[0]['id']

# Delete it
client.delete_event(event_id)
print("✅ Deleted")
```

## File Structure

After setup, you'll have:

```
ai-calendar-agent/
├── credentials.json    ← OAuth credentials (keep private!)
├── token.json          ← Access token (auto-generated, auto-refreshed)
└── .gitignore          ← Both files already ignored
```

Both files are already in `.gitignore` - they won't be committed to git.

## Security

- ✅ **credentials.json** - OAuth client credentials (not a secret, but don't share)
- ✅ **token.json** - Your access token (KEEP PRIVATE!)
- ✅ Both are in `.gitignore` - won't be pushed to GitHub
- ✅ Token auto-refreshes - no need to re-authenticate
- ✅ You can revoke access anytime in [Google Account Settings](https://myaccount.google.com/permissions)

## Troubleshooting

### Error: "credentials.json not found"

**Solution:** Download credentials from Google Cloud Console (Step 3)

### Error: "Access blocked: This app's request is invalid"

**Solution:** Make sure you:
1. Added your email as a test user
2. Selected the correct scopes (calendar API)
3. Used "Desktop app" type (not Web application)

### Token expired

**Automatic!** The code auto-refreshes tokens. You'll never need to re-authenticate.

### Want to re-authenticate

```bash
rm token.json
# Then run the authentication command again
```

## Privacy

**What access do you grant:**
- ✅ Read your calendar events
- ✅ Create new events
- ✅ Modify existing events
- ✅ Delete events

**What the AI won't do:**
- ❌ Share your calendar with others
- ❌ Send invites to other people (unless you explicitly ask)
- ❌ Access your Gmail
- ❌ Access other Google services

**You control everything:**
- Revoke access anytime: [Google Account Permissions](https://myaccount.google.com/permissions)
- All data stays on your machine
- No cloud storage of calendar data

## Next Steps

Once connected, you can:

1. **Import calendar events to database:**
   ```bash
   python -c "from integrations.google_calendar import GoogleCalendarClient; from database.connection import insert_calendar_event; client = GoogleCalendarClient(); events = client.get_events(); [insert_calendar_event(e) for e in events]"
   ```

2. **Create SchedulerOptimizerAgent** (coming soon)
   - Analyzes your calendar density
   - Suggests reschedules based on recovery
   - Auto-creates focus time blocks

3. **Full automation** (coming soon)
   - Monitors health every 30 mins
   - Automatically optimizes calendar
   - User approval before changes

## Quick Reference

```python
from integrations.google_calendar import GoogleCalendarClient
from datetime import datetime, timedelta

client = GoogleCalendarClient()

# Get upcoming events
events = client.get_events()

# Create event
event = client.create_event(
    summary="Meeting",
    start_time=datetime.now() + timedelta(hours=2),
    end_time=datetime.now() + timedelta(hours=3)
)

# Update event
client.update_event(
    event_id=event['id'],
    summary="Updated Meeting Title"
)

# Delete event
client.delete_event(event['id'])
```

## Support

- [Google Calendar API Docs](https://developers.google.com/calendar/api/v3/reference)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
