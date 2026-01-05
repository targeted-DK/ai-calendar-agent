# AI Fitness Scheduler

**An intelligent workout scheduling system that automatically plans, adjusts, and optimizes your training based on real-time health data and calendar availability.**

Built with Python, integrating Garmin Connect, Google Calendar, and local LLM (Ollama + Mistral) to create a fully autonomous fitness planning system.

---

## Features

### Intelligent Workout Planning
- **LLM-powered scheduling** - Uses local Mistral 7B to generate detailed, personalized workout plans
- **Health-aware decisions** - Adjusts intensity based on recovery score, sleep quality, and stress levels
- **Calendar-aware** - Automatically avoids scheduling conflicts with work, meetings, and other events
- **Flexible timing** - Schedules morning workouts by default, falls back to evening if morning is blocked

### Active Rescheduling
- **Config-driven updates** - Change your goals in YAML, workouts automatically adjust
- **Conflict detection** - Detects when calendar changes conflict with scheduled workouts
- **Smart rebalancing** - Removes workout types you no longer want, replaces with current priorities

### Health-Based Adaptation
- **Recovery monitoring** - Reads recovery score from Garmin
- **Sleep tracking** - Adjusts workout intensity based on sleep quality
- **Stress awareness** - Suggests easier workouts on high-stress days
- **Backup plans** - Every workout includes a low-energy alternative

### Workout Reconciliation
- **Planned vs Actual** - Compares scheduled workouts with Garmin activities
- **Automatic updates** - Marks completed workouts, logs discrepancies
- **Pattern learning** - Tracks when you deviate from plan for future optimization

---

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Garmin Connect │    │ Google Calendar │    │ Ollama+Mistral  │
│      API        │    │      API        │    │  (Local LLM)    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CRON (every 30 min)                      │
└─────────────────────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Garmin Import  │    │  Reconciliation │    │ Workout Planner │
│                 │    │                 │    │                 │
│ • Sleep data    │    │ • Compare plan  │    │ • Read config   │
│ • Recovery      │    │   vs actual     │    │ • Check health  │
│ • Activities    │    │ • Detect        │    │ • Check calendar│
│ • Stress        │    │   conflicts     │    │ • Call LLM      │
└────────┬────────┘    │ • Health adapt  │    │ • Create events │
         │             └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PostgreSQL                              │
│              (health_metrics, activity_data, patterns)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
ai-calendar-agent/
├── scripts/
│   ├── plan_workouts.py      # LLM-powered workout planning
│   ├── reconcile_workouts.py # Compare planned vs actual + conflict detection
│   ├── import_garmin_data.py # Import health/activity data
│   └── run_import.sh         # Cron orchestrator
├── config/
│   ├── goals.yaml            # Training goals and preferences
│   └── workout_templates.yaml# Detailed workout templates for LLM
├── integrations/
│   ├── google_calendar.py    # Google Calendar API client
│   └── garmin_connector.py   # Garmin Connect API client
├── database/
│   ├── connection.py         # PostgreSQL connection pool
│   └── init_db.py           # Schema initialization
├── tests/
│   └── test_workout_functions.py # Regression tests
├── .github/workflows/
│   └── test.yml              # CI pipeline
└── logs/                     # Runtime logs
```

---

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Ollama with Mistral model (or OpenAI API key)
- Google Calendar API credentials
- Garmin Connect account

### Installation

```bash
# Clone repository
git clone https://github.com/targeted-DK/ai-calendar-agent.git
cd ai-calendar-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python database/init_db.py

# Set up Google Calendar (follow prompts)
python scripts/test_calendar.py

# Install Ollama + Mistral (if using local LLM)
# See: https://ollama.ai
ollama pull mistral:7b-instruct-q4_0
```

### Configuration

Edit `config/goals.yaml` to set your training goals:

```yaml
weekly_structure:
  swim_sessions: 0
  bike_sessions: 2
  run_sessions: 2
  strength_sessions: 3

preferences:
  preferred_workout_time: "flexible"  # morning, evening, or flexible
  morning_hours: [5, 8]
  evening_hours: [17, 20]
```

### Running

```bash
# Manual run (preview)
python scripts/plan_workouts.py --days=5 --dry-run

# Manual run (create workouts)
python scripts/plan_workouts.py --days=5

# Set up cron (every 30 minutes)
crontab -e
# Add: */30 * * * * cd /path/to/ai-calendar-agent && ./scripts/run_import.sh
```

---

## Environment Variables

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=calendar_agent
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# LLM Provider
LLM_PROVIDER=ollama              # but this is up to the user's preference
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct-q4_0

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=token.json

# Garmin
GARMIN_EMAIL=your_email
GARMIN_PASSWORD=your_password

# Timezone
USER_TIMEZONE=America/Chicago
```

---

## How It Works

### 1. Health Data Collection
Every 30 minutes, the system imports from Garmin:
- Sleep duration and quality
- Recovery score (Body Battery)
- Stress levels
- Completed activities

### 2. Workout Planning
The LLM receives:
- Your training goals (from config)
- Current health metrics (from Garmin)
- Calendar events (from Google Calendar)
- Recent workout history
- Detailed workout templates

Then generates a personalized workout with:
- Specific exercises, sets, reps, weights
- Target heart rate zones
- Warmup and cooldown routines
- Backup plan for low-energy days

### 3. Active Rescheduling
The system continuously monitors for:
- Config changes (removed swim? → delete swim workouts)
- Calendar conflicts (new meeting? → move workout to evening)
- Health changes (poor sleep? → suggest backup plan)
- Exceeded targets (3 runs done? → don't schedule 4th)

### 4. Reconciliation
After workouts, the system:
- Compares what was planned vs what Garmin recorded
- Updates calendar events with actual data
- Logs discrepancies for pattern learning

---

## Testing

```bash
# Run regression tests
pytest tests/ -v

# Run specific test file
pytest tests/test_workout_functions.py -v
```

Tests cover:
- Workout response sanitization
- Time overlap detection
- Conflict finding
- Workout type matching
- Health adaptation thresholds

---

## Tech Stack

- **Python 3.11**
- **PostgreSQL** - Health metrics and activity storage
- **Ollama + Mistral 7B** - Local LLM for workout generation
- **Google Calendar API** - Schedule management
- **Garmin Connect API** - Health and fitness data
- **GitHub Actions** - CI/CD pipeline
- **pytest** - Regression testing

---

## License

MIT License - See LICENSE file for details