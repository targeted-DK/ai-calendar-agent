#!/bin/bash
# Import Garmin health data and Google Calendar events
# Runs every 30 minutes via cron

source /home/targeteer/ai-calendar-agent/venv/bin/activate
cd /home/targeteer/ai-calendar-agent
export PYTHONPATH=/home/targeteer/ai-calendar-agent

echo "============================================================"
echo "Data Import - $(date)"
echo "============================================================"
echo ""

# Import Garmin data (past 3 days)
echo "📊 Importing Garmin health data..."
python scripts/import_garmin_data.py --days=3

echo ""

# Import Google Calendar events (past 7 days, future 90 days)
echo "📅 Importing Google Calendar events..."
python scripts/import_calendar_events.py --past 7 --future 90

echo ""

# Plan workouts for next 3 days
echo "🏃 Planning workouts..."
python scripts/plan_workouts.py --days=3

echo ""
echo "============================================================"
echo "Import & Planning completed - $(date)"
echo "============================================================"
echo ""
