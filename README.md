# AI Fitness Scheduler

**An intelligent workout scheduling system that automatically plans, adjusts, and optimizes your training based on real-time health data and calendar availability.**

Built with Python, Docker, integrating Garmin Connect, Google Calendar, and LLM (Ollama local or cloud models) to create a fully autonomous fitness planning system.

**Current Version:** v1.1.0

---

## Features

### Intelligent Workout Planning
- **LLM-powered scheduling** - Uses local or cloud LLM models with automatic fallback
- **Dual workout options** - Generates Option A and Option B for each day (user picks one)
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
│  Garmin Connect │    │ Google Calendar │    │  Ollama (LLM)   │
│      API        │    │      API        │    │ Local or Cloud  │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container (App)                       │
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
│                 Docker Container (PostgreSQL)                   │
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
├── docker/
│   ├── entrypoint.sh        # Docker entrypoint
│   └── crontab              # Cron schedule
├── tests/
│   └── test_workout_functions.py # Regression tests
├── .github/workflows/
│   └── test.yml              # CI pipeline
├── version.py                # Version tracking
├── Dockerfile                # App container
├── docker-compose.yml        # Full stack orchestration
└── logs/                     # Runtime logs
```

---

## Quick Start (Docker - Recommended)

### Prerequisites
- Docker & Docker Compose
- Ollama (on host machine)
- Google Calendar API credentials (`credentials.json`)
- Garmin Connect account

### Installation

```bash
# Clone repository
git clone https://github.com/targeted-DK/ai-calendar-agent.git
cd ai-calendar-agent

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Set up Google Calendar authentication (one-time)
pip install google-auth google-auth-oauthlib google-api-python-client
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', ['https://www.googleapis.com/auth/calendar'])
creds = flow.run_local_server(port=0)
import json
with open('token.json', 'w') as f:
    json.dump({'token': creds.token, 'refresh_token': creds.refresh_token, 'token_uri': creds.token_uri, 'client_id': creds.client_id, 'client_secret': creds.client_secret, 'scopes': creds.scopes}, f)
"

# Start everything with Docker
docker compose up -d

# Check logs
docker compose logs -f app
```

### Ollama Setup

```bash
# Install Ollama (on host, not in Docker)
# See: https://ollama.ai

# For local models:
ollama pull mistral:7b-instruct-q4_0

# For cloud models (faster, requires sign-in):
ollama signin
# Then use gpt-oss:20b-cloud in .env
```

### Running Manually

```bash
# Preview workouts (dry run)
docker compose exec app python scripts/plan_workouts.py --days=3 --dry-run

# Create workouts
docker compose exec app python scripts/plan_workouts.py --days=3

# Or use aliases (add to ~/.bashrc):
alias plan="docker compose exec app python scripts/plan_workouts.py"
alias plan-logs="docker compose logs -f app"

# Then just:
plan --dry-run
plan --days=5
```

---

## Quick Start (Without Docker)

```bash
# Clone and setup
git clone https://github.com/targeted-DK/ai-calendar-agent.git
cd ai-calendar-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env (set DATABASE_URL to your PostgreSQL)

# Initialize database
python database/init_db.py

# Run
PYTHONPATH=. python scripts/plan_workouts.py --days=3 --dry-run
```

---

## Configuration

### Environment Variables (.env)

```bash
# LLM Provider
LLM_PROVIDER=ollama
OLLAMA_MODEL=gpt-oss:20b-cloud          # Cloud model (fast, requires ollama signin)
# OLLAMA_MODEL=mistral:7b-instruct-q4_0 # Local model (slower, no auth needed)
OLLAMA_BASE_URL=http://host.docker.internal:11434  # For Docker
# OLLAMA_BASE_URL=http://localhost:11434           # For non-Docker

# Database (for Docker)
POSTGRES_USER=life_agent
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=life_optimization
DATABASE_URL=postgresql://life_agent:your_secure_password@localhost:5432/life_optimization

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=token.json

# Garmin
GARMIN_EMAIL=your_email@gmail.com
GARMIN_PASSWORD=your_garmin_password

# Timezone
USER_TIMEZONE=America/Chicago
```

### Training Goals (config/goals.yaml)

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

---

## LLM Model Support

The system supports multiple LLM models with automatic fallback:

| Model | Type | Speed | Notes |
|-------|------|-------|-------|
| `gpt-oss:20b-cloud` | Cloud | ~30 sec | Requires `ollama signin` |
| `mistral:7b-instruct-q4_0` | Local | ~2-3 min | No auth needed |
| `qwen3-vl:4b` | Local | ~3-5 min | Vision-language model |

**Fallback mechanism:** If the primary model fails (timeout/error), the system automatically tries the fallback model.

Configure in `.env`:
```bash
OLLAMA_MODEL=gpt-oss:20b-cloud  # Primary model
```

Fallback is configured in `scripts/plan_workouts.py`:
```python
models_to_try = [settings.ollama_model, "qwen3-vl:4b"]  # Primary + fallback
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

Then generates TWO personalized workout options with:
- Specific exercises, sets, reps, weights
- Target heart rate zones
- Warmup and cooldown routines
- Backup plan for low-energy days

### 3. Active Rescheduling
The system continuously monitors for:
- Config changes (removed swim? -> delete swim workouts)
- Calendar conflicts (new meeting? -> move workout to evening)
- Health changes (poor sleep? -> suggest backup plan)
- Exceeded targets (3 runs done? -> don't schedule 4th)

### 4. Reconciliation
After workouts, the system:
- Compares what was planned vs what Garmin recorded
- Updates calendar events with actual data
- Logs discrepancies for pattern learning

---

## Testing

```bash
# Run in Docker
docker compose exec app pytest tests/ -v

# Run locally
pytest tests/test_workout_functions.py -v
```

Tests cover:
- Workout response sanitization
- Time overlap detection
- Conflict finding
- Workout type matching
- Health adaptation thresholds

---

## Version History

- **v1.1.0** - LLM fallback mechanism, Docker fixes, version tracking
- **v1.0.0** - Initial release with Docker setup

---

## Tech Stack

- **Python 3.11**
- **Docker & Docker Compose** - Containerized deployment
- **PostgreSQL** - Health metrics and activity storage
- **Ollama** - Local or cloud LLM inference
- **Google Calendar API** - Schedule management
- **Garmin Connect API** - Health and fitness data
- **GitHub Actions** - CI/CD pipeline
- **pytest** - Regression testing

---

## License

MIT License - See LICENSE file for details
