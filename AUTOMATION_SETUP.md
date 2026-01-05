# Automation Setup Guide

This guide shows you how to automate health monitoring and calendar optimization.

## Quick Start

Run the setup script:

```bash
bash scripts/setup_automation.sh
```

Choose your preferred method:
1. **Cron Job** - Simple, runs at specific intervals
2. **Systemd Timer** - Production-ready with better logging
3. **Manual** - Run on demand only

## Automation Features

The automation script **every 30 minutes** (configurable):

1. ✅ **Imports Garmin Data** (smart caching - only when needed)
   - Health metrics: sleep, recovery, stress
   - Activities: workouts, runs, rides
   - Only imports once per 6 hours (avoids rate limiting)

2. 📊 **Analyzes Health Status**
   - Calculates recovery score (0-100)
   - Identifies concerning patterns
   - Flags low recovery conditions

3. 🧠 **Builds Rich Context**
   - Analyzes 30 days of historical data
   - Identifies patterns and correlations
   - Provides insights for optimization

4. 📝 **Generates Recommendations**
   - Suggests calendar modifications based on recovery
   - Logs all actions for transparency
   - (Auto-execution coming soon)

## Option 1: Cron Job Setup

### Installation

```bash
# Run setup script and choose option 1
bash scripts/setup_automation.sh
```

### Manual Installation

1. Edit crontab:
   ```bash
   crontab -e
   ```

2. Add this line (runs every 30 minutes):
   ```bash
   */30 * * * * /home/targeteer/ai-calendar-agent/scripts/run_daily_automation.sh >> ~/.local/share/ai-calendar-agent/automation.log 2>&1
   ```

### Alternative Schedules

```bash
# Every 15 minutes
*/15 * * * * /path/to/run_daily_automation.sh >> ...

# Every hour
0 * * * * /path/to/run_daily_automation.sh >> ...

# Daily at 6 AM
0 6 * * * /path/to/run_daily_automation.sh >> ...

# Twice daily (6 AM and 6 PM)
0 6,18 * * * /path/to/run_daily_automation.sh >> ...
```

### View Logs

```bash
tail -f ~/.local/share/ai-calendar-agent/automation.log
```

## Option 2: Systemd Timer (Recommended)

### Installation

```bash
# Run setup script and choose option 2
bash scripts/setup_automation.sh
```

This creates:
- `~/.config/systemd/user/ai-calendar-automation.service`
- `~/.config/systemd/user/ai-calendar-automation.timer`

### Check Status

```bash
# Timer status
systemctl --user status ai-calendar-automation.timer

# View upcoming runs
systemctl --user list-timers

# View logs (real-time)
journalctl --user -u ai-calendar-automation.service -f

# View last 50 log lines
journalctl --user -u ai-calendar-automation.service -n 50
```

### Manual Trigger

```bash
systemctl --user start ai-calendar-automation.service
```

### Stop/Disable

```bash
# Stop timer
systemctl --user stop ai-calendar-automation.timer

# Disable (won't start on boot)
systemctl --user disable ai-calendar-automation.timer

# Re-enable
systemctl --user enable ai-calendar-automation.timer
systemctl --user start ai-calendar-automation.timer
```

## Option 3: Manual Execution

### Run Once

```bash
source venv/bin/activate
python scripts/daily_automation.py
```

### View Results

```bash
cat ~/.local/share/ai-calendar-agent/daily_automation.json
```

## How It Works

### Smart Import Caching

The script **doesn't hammer Garmin API** every run:

- ✅ Imports data if >6 hours since last import
- ✅ Imports data if new day detected
- ⏭️ Skips import if recently imported
- ✅ Always analyzes health (no API calls)
- ✅ Always optimizes calendar (no API calls)

### Current Behavior

Right now, the automation **generates recommendations** but doesn't modify your calendar automatically. You'll see:

- 🔴 **Critical Recovery (<40%)**: Aggressive schedule reduction needed
- 🟡 **Fair Recovery (40-60%)**: Reduce meeting density by 30%
- 🟢 **Good Recovery (60-80%)**: Normal schedule maintained
- ✅ **Excellent Recovery (>80%)**: Can handle high load

### Future: Auto-Execution

Coming soon:
- Automatic calendar modifications (with user approval)
- Integration with SchedulerOptimizerAgent
- Smart rescheduling based on recovery
- Focus time block insertion

## Monitoring

### Check Last Run

```bash
# Systemd
journalctl --user -u ai-calendar-automation.service -n 1

# Cron
tail -1 ~/.local/share/ai-calendar-agent/automation.log

# Results file
cat ~/.local/share/ai-calendar-agent/daily_automation.json | jq .
```

### Database Logs

All recommendations are logged to the database:

```sql
SELECT
    timestamp,
    agent_name,
    action_type,
    reasoning,
    confidence_score
FROM agent_actions
ORDER BY timestamp DESC
LIMIT 10;
```

## Troubleshooting

### Automation Not Running

**Cron:**
```bash
# Check if cron is running
sudo systemctl status cron

# Check crontab
crontab -l

# Check logs
grep CRON /var/log/syslog
```

**Systemd:**
```bash
# Check timer status
systemctl --user status ai-calendar-automation.timer

# Check service status
systemctl --user status ai-calendar-automation.service

# View errors
journalctl --user -u ai-calendar-automation.service --since today
```

### Import Errors

If Garmin import fails:
- Check credentials in `.env`
- Verify Garmin account is active
- Check internet connection
- See logs for specific errors

### Low Recovery Warnings

If you see critical recovery warnings:
- Review your sleep patterns
- Check calendar for overload
- Consider manual schedule adjustments
- Consult recommendations in logs

## Next Steps

1. ✅ Set up automation (choose cron or systemd)
2. ✅ Monitor for 24-48 hours
3. ✅ Review recommendations in logs
4. ⏳ Wait for SchedulerOptimizerAgent integration (coming soon)
5. ⏳ Enable auto-calendar modifications (when ready)

## Security

- Automation runs as your user (no root needed)
- Garmin credentials stored locally in `.env`
- All data stays on your machine
- Logs contain no sensitive information
- Database is local PostgreSQL

## Performance

- Typical run time: **10-15 seconds**
- Most runs skip import (fast)
- Health analysis: ~5 seconds
- Context building: ~5 seconds
- Calendar optimization: <1 second

Running every 30 minutes is very lightweight!
