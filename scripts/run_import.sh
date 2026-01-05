#!/bin/bash
# Simple wrapper to import Garmin data
# Runs every 30 minutes via cron

source /home/targeteer/ai-calendar-agent/venv/bin/activate
cd /home/targeteer/ai-calendar-agent
python scripts/import_garmin_data.py --days=3
