# Simple Cron Setup - Auto Import Data

## What It Does

Automatically imports Garmin health data and Google Calendar events **every 30 minutes**.

- ✅ Imports sleep, recovery, stress data from Garmin
- ✅ Imports workouts, runs, activities from Garmin
- ✅ Imports Google Calendar events (past 7 days, future 90 days)
- ✅ Skips duplicates cleanly (no errors)
- ✅ Logs everything to `logs/import.log`

## Setup (2 steps)

### 1. Edit crontab

```bash
crontab -e
```

### 2. Add this line

```bash
*/30 * * * * /home/targeteer/ai-calendar-agent/scripts/run_import.sh >> /home/targeteer/ai-calendar-agent/logs/import.log 2>&1
```

Save and exit. Done! ✅

## Schedule Options

```bash
# Every 30 minutes (recommended)
*/30 * * * * /home/targeteer/ai-calendar-agent/scripts/run_import.sh >> /home/targeteer/ai-calendar-agent/logs/import.log 2>&1

# Every 15 minutes (more frequent)
*/15 * * * * /home/targeteer/ai-calendar-agent/scripts/run_import.sh >> /home/targeteer/ai-calendar-agent/logs/import.log 2>&1

# Every hour
0 * * * * /home/targeteer/ai-calendar-agent/scripts/run_import.sh >> /home/targeteer/ai-calendar-agent/logs/import.log 2>&1

# Daily at 6 AM
0 6 * * * /home/targeteer/ai-calendar-agent/scripts/run_import.sh >> /home/targeteer/ai-calendar-agent/logs/import.log 2>&1

# Twice daily (6 AM and 6 PM)
0 6,18 * * * /home/targeteer/ai-calendar-agent/scripts/run_import.sh >> /home/targeteer/ai-calendar-agent/logs/import.log 2>&1
```

## Monitor

### View logs (real-time)
```bash
tail -f /home/targeteer/ai-calendar-agent/logs/import.log
```

### View last import
```bash
tail -20 /home/targeteer/ai-calendar-agent/logs/import.log
```

### Check cron is running
```bash
crontab -l
```

## Manual Run

Test it anytime:
```bash
bash /home/targeteer/ai-calendar-agent/scripts/run_import.sh
```

## What Gets Logged

```
============================================================
Data Import - Sun Jan 4 21:47:39 CST 2026
============================================================

📊 Importing Garmin health data...
🔌 Connecting to Garmin...
✅ Connected to Garmin Connect

📊 Importing health data for past 3 days...
  ⏭️  2026-01-04: Already exists
  ✅ 2026-01-05: Recovery 65.2/100, Sleep 7.2h

🏃 Importing activities for past 3 days...
  ✅ running: 35min, 5.2km

============================================================
Import Summary
============================================================
✅ Success: 2
⏭️  Skipped: 4 (already in database)
❌ Errors:  0
============================================================

📅 Importing Google Calendar events...
🔌 Connecting to Google Calendar...
✅ Connected to Google Calendar

📅 Fetching events from 2025-12-29 to 2026-04-05...
Found 5 events

  ✅ Team Meeting
     2026-01-05 14:00
  ✅ Focus Time
     2026-01-06 09:00

============================================================
Import Summary
============================================================
✅ New events:     5
🔄 Updated events: 0
❌ Errors:         0
📊 Total:          5
============================================================

============================================================
Import completed - Sun Jan 4 21:47:45 CST 2026
============================================================
```

## Use the Data

Run agents manually when you want analysis:

```bash
# Analyze health
python -c "from agents.health_monitor_agent import create_health_monitor; agent = create_health_monitor(); print(agent.check_health())"

# Build context
python -c "from agents.pattern_learning_agent import create_pattern_learning_agent; agent = create_pattern_learning_agent(); print(agent.build_rich_context('Check my recent patterns', 30))"
```

## Troubleshooting

**Cron not running?**
```bash
# Check if cron service is running
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog | tail -20
```

**Import failing?**
- Check Garmin credentials in `.env`
- Check venv exists: `ls venv/bin/activate`
- Test manually: `bash scripts/run_import.sh`
