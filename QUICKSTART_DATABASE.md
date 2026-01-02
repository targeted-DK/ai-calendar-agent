# Database Quick Start Guide

## ✅ What's Been Created

I've set up a complete PostgreSQL database system for your Life Optimization AI:

### Files Created:
```
database/
├── schema.sql          # Complete database schema (9 tables, 3 views)
├── connection.py       # Database connection manager with connection pooling
├── init_db.py         # Database initialization script
├── test_db.py         # Comprehensive test suite
└── README.md          # Detailed documentation

setup_postgres.sh      # PostgreSQL installation script
.env                   # Environment configuration (includes DATABASE_URL)
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install PostgreSQL

```bash
./setup_postgres.sh
```

**What this does:**
- Installs PostgreSQL
- Creates database: `life_optimization`
- Creates user: `life_agent` (password: `secure_password_123`)
- Grants all permissions

**Expected output:**
```
✅ PostgreSQL installed
✅ Database 'life_optimization' created
✅ User 'life_agent' created
```

---

### Step 2: Create Database Tables

```bash
source venv/bin/activate
cd database
python init_db.py
```

**What this does:**
- Creates 9 tables (health_metrics, calendar_events, agent_actions, etc.)
- Creates 3 views (recent_health_summary, daily_productivity, agent_performance)
- Inserts default user preferences

**Expected output:**
```
✅ Database schema created successfully!

Created 9 tables:
  ✓ health_metrics
  ✓ activity_data
  ✓ calendar_events
  ✓ productivity_metrics
  ✓ learned_patterns
  ✓ agent_actions
  ✓ user_preferences
  ✓ mood_tracking
  ✓ system_metadata
```

---

### Step 3: Test Everything

```bash
python test_db.py
```

**What this does:**
- Tests database connection
- Inserts test health metric
- Inserts test calendar event
- Logs test agent action
- Verifies all tables and views

**Expected output:**
```
🧪 Testing Life Optimization AI Database

1️⃣ Testing database connection...
   ✅ Connected successfully!

2️⃣ Testing health metric insertion...
   ✅ Health metric inserted with ID: 1

3️⃣ Testing calendar event insertion...
   ✅ Calendar event inserted with ID: 1

... (8 total tests)

✅ All database tests passed successfully!
```

---

## 🎯 What You Can Do Now

### Query the database directly:

```bash
# Connect to database
psql -U life_agent -d life_optimization

# View tables
\dt

# View recent health summary
SELECT * FROM recent_health_summary;

# Check user preferences
SELECT * FROM user_preferences;

# Exit
\q
```

### Use in Python code:

```python
from database.connection import Database, get_user_preference

# Get max meetings per day
max_meetings = get_user_preference('max_meetings_per_day')
print(f"Max meetings: {max_meetings}")

# Query health metrics
health_data = Database.execute_query("""
    SELECT * FROM health_metrics
    WHERE timestamp >= NOW() - INTERVAL '7 days'
    ORDER BY timestamp DESC
""")
```

---

## 📊 Database Schema Overview

### Tables Created:

1. **health_metrics** - Garmin health data
   - Sleep (duration, quality, deep sleep, REM)
   - Heart rate (resting, avg, max, HRV)
   - Stress, recovery score, steps, etc.

2. **activity_data** - Strava workout data
   - Activity type, duration, distance
   - Heart rate, power, training load
   - Calories burned

3. **calendar_events** - Google Calendar events
   - Event details, recurrence
   - Participant info, tags
   - User modifications tracking

4. **agent_actions** - Audit log
   - Agent name, action type
   - Confidence score, reasoning
   - Before/after state, user feedback

5. **user_preferences** - Settings
   - Working hours, meeting limits
   - Protected keywords, safety rules
   - Health targets

6. **productivity_metrics** - Daily stats
   - Meeting count, duration
   - Focus time, productivity score

7. **learned_patterns** - AI insights
   - Pattern type, description
   - Triggers, outcomes
   - Confidence score

8. **mood_tracking** - Daily mood
   - Mood score (1-10)
   - Energy level, stress perception

9. **system_metadata** - System info
   - Schema version, last migration

---

## 🔧 Troubleshooting

### Problem: "connection refused"

**Solution:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

### Problem: "permission denied"

**Solution:**
```bash
# Recreate user and grant permissions
sudo -u postgres psql << EOF
DROP USER IF EXISTS life_agent;
CREATE USER life_agent WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE life_optimization TO life_agent;
\c life_optimization
GRANT ALL ON SCHEMA public TO life_agent;
EOF
```

### Problem: "DATABASE_URL not found"

**Solution:**
```bash
# Check .env file exists and has DATABASE_URL
cat .env | grep DATABASE_URL

# If missing, add it:
echo "DATABASE_URL=postgresql://life_agent:secure_password_123@localhost:5432/life_optimization" >> .env
```

---

## 🔐 Security Reminder

**IMPORTANT:** Change the default password before production use!

```bash
# Change password
sudo -u postgres psql -c "ALTER USER life_agent WITH PASSWORD 'your_new_strong_password';"

# Update .env file
nano .env
# Change DATABASE_URL to use new password
```

---

## 📝 What's Next?

After completing database setup:

1. ✅ PostgreSQL installed and running
2. ✅ Database schema created
3. ✅ Connection tested
4. ⏭️ Ready to build agents!

The database is now ready for:
- Health data storage (Garmin, Strava)
- Calendar event tracking
- Agent decision logging
- Pattern learning and RAG

---

## 🆘 Need Help?

- **Database documentation:** `database/README.md`
- **Connection examples:** See `database/connection.py`
- **Schema details:** See `database/schema.sql`
- **Test suite:** Run `python database/test_db.py`

---

## ✅ Completion Checklist

- [ ] Ran `./setup_postgres.sh` successfully
- [ ] Ran `python database/init_db.py` successfully
- [ ] Ran `python database/test_db.py` - all tests passed
- [ ] Can connect: `psql -U life_agent -d life_optimization`
- [ ] Changed default password (recommended for production)

**When all boxes are checked, your database is ready!** 🎉
