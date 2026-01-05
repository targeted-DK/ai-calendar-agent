#!/bin/bash
# Import Garmin health data, reconcile workouts, and plan new workouts
# Runs every 30 minutes via cron

source /home/targeteer/ai-calendar-agent/venv/bin/activate
cd /home/targeteer/ai-calendar-agent
export PYTHONPATH=/home/targeteer/ai-calendar-agent

echo "============================================================"
echo "AI Calendar Agent - $(date)"
echo "============================================================"
echo ""

# Step 1: Import Garmin data (past 3 days)
echo "📊 Step 1: Importing Garmin health data..."
python scripts/import_garmin_data.py --days=3

echo ""

# Step 2: Reconcile past workouts (compare scheduled vs actual)
echo "🔄 Step 2: Reconciling scheduled vs actual workouts..."
python scripts/reconcile_workouts.py --days=7

echo ""

# Step 3: Import Google Calendar events (past 7 days, future 90 days)
echo "📅 Step 3: Importing Google Calendar events..."
python scripts/import_calendar_events.py --past 7 --future 90

echo ""

# Step 4: Plan workouts for next 3 days
echo "🏃 Step 4: Planning workouts..."
python scripts/plan_workouts.py --days=3

echo ""
echo "============================================================"
echo "Completed - $(date)"
echo "============================================================"
echo ""
