# Life Optimization AI - Calendar Agent

**Autonomous AI agent that optimizes your daily schedule based on health, fitness, and productivity data.**

Integrates with Garmin, Strava, and Google Calendar to proactively manage your calendar based on:
- Sleep quality and recovery metrics
- Training load and workout patterns
- Calendar density and meeting patterns
- Learned preferences over time

---

## 🎯 Current Status

**This is a work-in-progress project being actively developed.**

**What's implemented:**
- ✅ Basic agent architecture (BaseAgent, SchedulerAgent, PatternAgent)
- ✅ Google Calendar integration (OAuth + CRUD operations)
- ✅ RAG system with ChromaDB
- ✅ Multi-LLM support (Claude, GPT-4, Gemini)
- ✅ Basic calendar tools (5 tools)

**What's planned:**
- 🚧 Garmin health data integration
- 🚧 Strava fitness data integration
- 🚧 HealthMonitorAgent (sleep, HR, stress analysis)
- 🚧 ProductivityAnalyzerAgent (calendar pattern analysis)
- 🚧 Autonomous optimization workflow
- 🚧 Safety rules and edge case detection
- 🚧 Notification system (Telegram/email)

---

## 📁 Project Structure

```
ai-calendar-agent/
├── agents/              # AI agents
│   ├── base_agent.py         # Base class with tool calling
│   ├── scheduler_agent.py    # Calendar scheduling
│   └── pattern_agent.py      # Pattern learning
├── integrations/        # External APIs
│   └── google_calendar.py    # Google Calendar OAuth + API
├── tools/              # Agent tools
│   └── calendar_tools.py     # 5 calendar manipulation tools
├── rag/                # Pattern learning
│   ├── vector_store.py       # ChromaDB wrapper
│   └── embeddings.py         # OpenAI embeddings
├── config/             # Configuration
│   └── settings.py           # Pydantic settings
├── docs/               # Documentation (reference)
│   ├── COMPLETE_MENTAL_MODEL.md
│   ├── LIFE_OPTIMIZATION_DESIGN.md
│   ├── PRACTICAL_DEPLOYMENT_FAQ.md
│   └── ...
├── main.py             # Interactive CLI
├── example_usage.py    # Usage examples
├── requirements.txt    # Dependencies
├── .env.example       # Environment template
└── setup.sh           # Quick setup script
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Calendar API credentials ([Get them here](https://developers.google.com/calendar/api/quickstart/python))
- Anthropic or OpenAI API key

### Installation

```bash
# 1. Clone and enter directory
cd ai-calendar-agent

# 2. Run setup script (creates venv, installs deps)
./setup.sh

# OR manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Add Google Calendar credentials
# Download credentials.json from Google Cloud Console
# Place in project root

# 5. Run the agent
python main.py
```

---

## 🔑 Required API Keys

Add these to your `.env` file:

```bash
# LLM Provider (choose one or more)
ANTHROPIC_API_KEY=sk-ant-...           # Claude (recommended)
OPENAI_API_KEY=sk-...                  # GPT-4 + embeddings

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=token.json

# Database (optional - defaults shown)
CHROMADB_PATH=./chroma_db
```

---

## 💡 Usage Examples

### Interactive CLI
```bash
python main.py
```

Menu options:
1. Schedule event using natural language
2. Find available time slots
3. View upcoming events
4. Analyze calendar patterns
5. Get scheduling recommendations
6. Learn from calendar history
7. Chat with scheduler agent

### Programmatic Usage
```python
from agents.scheduler_agent import SchedulerAgent

agent = SchedulerAgent()

# Schedule event
agent.schedule_event(
    "Schedule a 1-hour team meeting tomorrow at 2pm"
)

# Find optimal time
agent.find_time_for_meeting(
    duration_minutes=60,
    preferred_times=["morning"]
)

# Analyze patterns
agent.analyze_calendar_patterns(days=30)
```

---

## 📚 Documentation

**For developers and learners:**
- `docs/COMPLETE_MENTAL_MODEL.md` - Understand all concepts (agents, tools, MCP, etc.)
- `docs/LIFE_OPTIMIZATION_DESIGN.md` - Full system architecture design
- `docs/PRACTICAL_DEPLOYMENT_FAQ.md` - Deployment questions answered
- `docs/PROJECT_CONTEXT.md` - Project overview and status

---

## 🛠️ Tech Stack

- **Python 3.9+**
- **LLMs:** Anthropic Claude, OpenAI GPT-4, Google Gemini, Ollama
- **Vector DB:** ChromaDB (for RAG)
- **Database:** PostgreSQL (planned) or SQLite
- **APIs:** Google Calendar API (OAuth 2.0)
- **Future:** Garmin Connect API, Strava API

---

## 🎯 Roadmap

### Phase 1: MVP (Current)
- [x] Basic agent architecture
- [x] Google Calendar integration
- [x] Simple scheduling via CLI
- [ ] Test with real calendar data

### Phase 2: Health Integration
- [ ] Garmin Connect integration (sleep, HR, stress)
- [ ] Strava integration (workouts, training load)
- [ ] HealthMonitorAgent implementation
- [ ] Basic autonomous optimization

### Phase 3: Intelligence
- [ ] ProductivityAnalyzerAgent (calendar pattern analysis)
- [ ] PatternLearningAgent enhancements
- [ ] Multi-factor decision making
- [ ] Edge case detection

### Phase 4: Automation
- [ ] Observer mode → Semi-autonomous → Fully autonomous
- [ ] Safety rules engine
- [ ] Notification system (Telegram/email)
- [ ] Rollback/undo capability

### Phase 5: Production
- [ ] Raspberry Pi deployment
- [ ] 24/7 operation
- [ ] Web dashboard
- [ ] Monitoring and logging

---

## 🤝 Contributing

This is a personal learning project, but feedback and suggestions are welcome!

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙋 Questions?

Read the comprehensive guides in `docs/`:
- New to AI agents? Read `COMPLETE_MENTAL_MODEL.md`
- Want to understand the architecture? Read `LIFE_OPTIMIZATION_DESIGN.md`
- Deployment questions? Read `PRACTICAL_DEPLOYMENT_FAQ.md`
