# Database Setup Guide

## Overview

This directory contains all database-related code for the Life Optimization AI Agent.

## Database Schema

The PostgreSQL database includes the following tables:

### Core Tables

1. **health_metrics** - Garmin/Strava health data (sleep, HR, stress, etc.)
2. **activity_data** - Workout and exercise data
3. **calendar_events** - Google Calendar events with metadata
4. **productivity_metrics** - Daily productivity calculations
5. **learned_patterns** - AI-learned patterns from historical data
6. **agent_actions** - Audit log of all agent decisions
7. **user_preferences** - User settings and preferences
8. **mood_tracking** - Daily mood and energy tracking
9. **system_metadata** - System configuration

### Views

- `recent_health_summary` - Last 30 days health metrics
- `daily_productivity` - Daily meeting and productivity stats
- `agent_performance` - Agent decision accuracy metrics

## Setup Instructions

### 1. Install PostgreSQL

Run the setup script from the project root:

```bash
./setup_postgres.sh
```

This will:
- Install PostgreSQL
- Create database `life_optimization`
- Create user `life_agent`
- Configure permissions

### 2. Initialize Database Schema

```bash
cd database
python init_db.py
```

This creates all tables, views, and default preferences.

### 3. Test Connection

```bash
python test_db.py
```

This runs comprehensive tests to verify everything works.

## Connection Details

From `.env` file:
```
DATABASE_URL=postgresql://life_agent:secure_password_123@localhost:5432/life_optimization
```

## Python Usage

### Using the Database class

```python
from database.connection import Database

# Execute query
results = Database.execute_query("SELECT * FROM health_metrics LIMIT 10")

# Execute single row query
result = Database.execute_one("SELECT * FROM user_preferences WHERE key = %s", ('max_meetings_per_day',))

# Insert/Update
Database.execute_update("INSERT INTO mood_tracking (date, mood_score) VALUES (%s, %s)", (date.today(), 8))
```

### Using convenience functions

```python
from database.connection import (
    insert_health_metric,
    insert_calendar_event,
    log_agent_action,
    get_user_preference,
    set_user_preference
)

# Insert health data
health_id = insert_health_metric({
    'timestamp': datetime.now(),
    'source': 'garmin',
    'sleep_duration_hours': 7.5,
    'sleep_quality_score': 85,
    'resting_heart_rate': 60
})

# Get preference
max_meetings = get_user_preference('max_meetings_per_day')

# Log agent action
log_agent_action('SchedulerAgent', 'reschedule', {
    'confidence_score': 85,
    'reasoning': 'Poor sleep detected',
    'executed': True
})
```

## File Structure

```
database/
├── __init__.py              # Package initialization
├── schema.sql               # Database schema definition
├── connection.py            # Connection pooling and utilities
├── init_db.py              # Schema initialization script
├── test_db.py              # Test suite
└── README.md               # This file
```

## Common Operations

### View all tables

```bash
psql -U life_agent -d life_optimization -c "\dt"
```

### View recent health data

```bash
psql -U life_agent -d life_optimization -c "SELECT * FROM recent_health_summary LIMIT 5;"
```

### Check agent performance

```bash
psql -U life_agent -d life_optimization -c "SELECT * FROM agent_performance;"
```

### Backup database

```bash
pg_dump -U life_agent life_optimization > backup_$(date +%Y%m%d).sql
```

### Restore database

```bash
psql -U life_agent life_optimization < backup_20250101.sql
```

## Troubleshooting

### Connection refused

Check if PostgreSQL is running:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Permission denied

Verify database user exists and has permissions:
```bash
sudo -u postgres psql -c "\du"
sudo -u postgres psql -c "\l"
```

### Schema errors

Drop and recreate database:
```bash
sudo -u postgres psql << EOF
DROP DATABASE life_optimization;
CREATE DATABASE life_optimization;
GRANT ALL PRIVILEGES ON DATABASE life_optimization TO life_agent;
EOF

python init_db.py
```

## Security Notes

**IMPORTANT:** Change the default password before production use!

```bash
sudo -u postgres psql -c "ALTER USER life_agent WITH PASSWORD 'your_new_secure_password';"
```

Then update `.env` file:
```
DATABASE_URL=postgresql://life_agent:your_new_secure_password@localhost:5432/life_optimization
```

## Performance Tips

- Connection pooling is enabled by default (max 10 connections)
- Indexes are created on frequently queried columns
- Use batch inserts for large data loads with `execute_many()`
- Views are optimized for common queries

## Maintenance

### Vacuum database (optimize performance)

```bash
psql -U life_agent -d life_optimization -c "VACUUM ANALYZE;"
```

### Check database size

```bash
psql -U life_agent -d life_optimization -c "SELECT pg_size_pretty(pg_database_size('life_optimization'));"
```

## Support

For issues, check:
1. PostgreSQL logs: `sudo journalctl -u postgresql`
2. Application logs: Check agent output
3. Connection string in `.env` is correct
