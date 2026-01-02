# AI Calendar Agent - Setup Guide

This guide will walk you through setting up the AI Calendar Agent system.

## Prerequisites

- Python 3.9 or higher
- Google account with Google Calendar access
- API key from at least one LLM provider (Anthropic, OpenAI, or Google)

## Step 1: Install Dependencies

### Option A: Automated Setup (Recommended)

```bash
./setup.sh
```

### Option B: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Keys

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:

```env
# Choose your LLM provider
LLM_PROVIDER=anthropic  # Options: anthropic, openai, gemini, ollama

# Add your API key(s)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

### Getting API Keys

**Anthropic Claude:**
- Visit: https://console.anthropic.com/
- Go to API Keys section
- Create a new API key

**OpenAI:**
- Visit: https://platform.openai.com/api-keys
- Create a new API key

**Google Gemini:**
- Visit: https://makersuite.google.com/app/apikey
- Create an API key

## Step 3: Set Up Google Calendar API

### Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure the OAuth consent screen if prompted:
   - User Type: External
   - App name: AI Calendar Agent
   - Add your email as a test user
4. Create OAuth Client ID:
   - Application type: Desktop app
   - Name: AI Calendar Agent
5. Download the credentials JSON file
6. Save it as `credentials.json` in the project root directory

### First-Time Authentication

When you first run the application, it will:
1. Open a browser window for Google OAuth
2. Ask you to grant calendar access
3. Save the token locally for future use

## Step 4: Run the Application

### Activate Virtual Environment

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Run Interactive Mode

```bash
python main.py
```

### Run Demo Mode

```bash
python main.py --demo
```

## Key Features Demonstration

### 1. Natural Language Scheduling

```python
scheduler = SchedulerAgent()
scheduler.schedule_event("Schedule a 1-hour team meeting tomorrow at 2pm")
```

### 2. Pattern Learning with RAG

```python
pattern_agent = PatternLearningAgent()
pattern_agent.learn_from_history(days_back=90)
recommendations = pattern_agent.get_recommendations("project planning meeting")
```

### 3. Smart Time Finding

```python
scheduler.find_time_for_meeting(
    meeting_description="sprint planning",
    duration_minutes=90,
    preferred_date="2024-01-15"
)
```

## Architecture Overview

### Multi-Agent System

The system uses specialized AI agents:

1. **SchedulerAgent**: Handles scheduling operations
   - Natural language event creation
   - Free slot finding
   - Calendar management

2. **PatternLearningAgent**: Learns from history
   - Analyzes calendar patterns
   - Provides recommendations
   - Stores insights in vector database

### RAG (Retrieval-Augmented Generation)

- **Vector Store**: ChromaDB for semantic search
- **Embeddings**: OpenAI's text-embedding-3-small
- **Use Cases**:
  - Finding similar past events
  - Learning user preferences
  - Making intelligent scheduling suggestions

### Tool Calling

Agents have access to tools:
- `get_upcoming_events`: Retrieve calendar events
- `create_calendar_event`: Create new events
- `find_free_slots`: Find available time slots
- `search_similar_events`: RAG-based event search
- `get_event_statistics`: Analyze calendar usage

### Multi-LLM Support

Easily switch between providers:
- Anthropic Claude (recommended)
- OpenAI GPT-4
- Google Gemini
- Ollama (local models)

## Troubleshooting

### Issue: "Credentials file not found"

**Solution**: Make sure `credentials.json` is in the project root directory.

### Issue: "API key not set"

**Solution**: Check your `.env` file has the correct API key for your chosen provider.

### Issue: "Module not found" errors

**Solution**: Make sure you've activated the virtual environment:
```bash
source venv/bin/activate
```

### Issue: ChromaDB errors

**Solution**: Delete the `chroma_db` directory and restart:
```bash
rm -rf chroma_db
python main.py
```

## What Makes This Project Stand Out for Job Applications

### 1. RAG Implementation
- Vector embeddings with ChromaDB
- Semantic search for calendar events
- Pattern storage and retrieval

### 2. Multi-Agent Architecture
- Specialized agents with distinct roles
- Agent orchestration and communication
- Demonstrates understanding of agentic workflows

### 3. Tool Use / Function Calling
- Modern LLM interaction patterns
- Complex tool chains
- Real-world API integration

### 4. Production-Ready Code
- Proper error handling
- Configuration management
- Clean architecture with separation of concerns
- Type hints and documentation

### 5. Multi-LLM Support
- Provider abstraction
- Easy switching between models
- Future-proof design

### 6. Real-World Application
- Solves actual productivity problems
- Google Calendar integration
- Natural language interface

## Next Steps for Enhancement

1. **Add more agents**:
   - PrioritizationAgent for task ranking
   - ConflictResolutionAgent for scheduling conflicts

2. **Enhance RAG**:
   - More sophisticated embedding strategies
   - Hybrid search (keyword + semantic)
   - Reranking for better results

3. **Web Interface**:
   - FastAPI backend
   - React frontend
   - Real-time updates

4. **Advanced Features**:
   - Meeting preparation summaries
   - Automatic event categorization
   - Smart notifications

5. **Deployment**:
   - Docker containerization
   - Cloud deployment (AWS/GCP)
   - CI/CD pipeline

## Resources

- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Google Calendar API](https://developers.google.com/calendar)
- [ChromaDB Documentation](https://docs.trychroma.com/)
