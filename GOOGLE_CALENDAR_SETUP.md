# Google Calendar API Setup

## Steps

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Create Project"** → Name: `Workout schedule optimization` → **Create**

### 2. Enable Google Calendar API

1. Search: **"Calendar API"** in top search bar
2. Click **"Google Calendar API"** → **"Enable"**

### 3. Create OAuth Credentials

1. Click **"Credentials"** in left sidebar
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. If prompted, configure consent screen:
   - Select **"External"** → **Create**
   - App name: `Workout schedule optimization`
   - User support email: Your email
   - Developer contact: Your email
   - **Save and Continue**
   - Add scope: `Google Calendar API` (`.../auth/calendar`)
   - Add test user: Your Gmail address
   - **Save and Continue** → **Back to Dashboard**

4. Go back to **Credentials** → **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
5. Application type: **"Desktop app"** → **Create**
6. **Download JSON** → Save as `credentials.json` in project root

### 4. Authenticate

```bash
cd /home/username/ai-calendar-agent
source venv/bin/activate
python -c "from integrations.google_calendar import GoogleCalendarClient; GoogleCalendarClient(); print('Connected!')"
```

Browser opens → Allow access → Done. Creates `token.json` (reused automatically).

### 5. Test

```bash
python scripts/test_calendar.py
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console (Step 3) |
| `Access blocked: invalid request` | Add your email as test user, use "Desktop app" type |
| Token expired | Auto-refreshes. If issues: `rm token.json` and re-run Step 4 |

## Security

- `credentials.json` and `token.json` are in `.gitignore`
- Revoke access anytime: [Google Account Permissions](https://myaccount.google.com/permissions)
