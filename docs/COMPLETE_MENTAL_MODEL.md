# Complete Mental Model - AI Systems Terminology

**Purpose:** Build a comprehensive understanding of all concepts before implementation
**Last Updated:** 2025-12-30
**For:** Life Optimization AI Calendar Agent Project

---

## 🎯 The Big Picture First

Think of your Life Optimization AI like running a **small company**:

```
YOUR LIFE OPTIMIZATION AI COMPANY
├── EMPLOYEES (Agents) - Smart workers who make decisions
├── DEPARTMENTS (Subagents) - Specialized teams
├── TOOLS (Hammers, calculators) - What employees use to do work
├── KNOWLEDGE BASE (Memory) - What the company remembers
├── COMMUNICATION PROTOCOLS (MCP) - How departments talk
├── WORKPLACE (IDE) - Where work happens
└── SHORTCUTS (Slash commands, skills) - Quick actions
```

Now let's break down each piece...

---

# PART 1: THE WORKERS (Who Does the Work?)

## 🤖 **AGENT**

**Simple Definition:** An autonomous AI worker that can think, make decisions, and take actions.

**Real-world analogy:** A smart personal assistant who:
- Understands your requests
- Figures out what to do
- Uses tools to complete tasks
- Reports back to you

**In your project:**
```python
# OrchestratorAgent is an agent
class OrchestratorAgent:
    """
    This is a worker that:
    1. Reads your health data
    2. Thinks: "Sleep was bad, should I reduce meetings?"
    3. Decides: "Yes, reschedule 2 meetings"
    4. Takes action: Calls Google Calendar to reschedule
    5. Reports: "Done! I rescheduled your meetings."
    """
```

**Key characteristics:**
- ✅ Can think and reason (uses LLM like Claude or GPT-4)
- ✅ Can use tools (call APIs, read databases)
- ✅ Works autonomously (doesn't need you to tell it every step)
- ✅ Has a specific purpose/role

**Example agents in your system:**
- `OrchestratorAgent` - The manager who coordinates everything
- `HealthMonitorAgent` - The doctor who watches your health
- `SchedulerOptimizerAgent` - The calendar expert
- `PatternLearningAgent` - The data scientist who finds patterns

---

## 👥 **SUBAGENT**

**Simple Definition:** A specialized agent that works under another agent.

**Real-world analogy:** In a company:
- CEO (main agent)
- Department heads (subagents): HR head, Finance head, Engineering head

**In your project:**
```
OrchestratorAgent (main agent - "the CEO")
    ├── HealthMonitorAgent (subagent - "the health department")
    ├── ProductivityAgent (subagent - "the productivity department")
    └── SchedulerAgent (subagent - "the calendar department")
```

**Key difference from Agent:**
- Agent = Independent worker
- Subagent = Specialized worker that another agent calls

**Example:**
```python
class OrchestratorAgent:
    def run(self):
        # OrchestratorAgent calls subagents
        health_status = HealthMonitorAgent().check_health()
        calendar_plan = SchedulerAgent().optimize(health_status)

        # Orchestrator makes final decision
        self.execute(calendar_plan)
```

**When to use the term:**
- "HealthMonitorAgent is a subagent of OrchestratorAgent"
- "We have 5 subagents, each handling different tasks"

---

# PART 2: HOW AGENTS THINK

## 💭 **PROMPT**

**Simple Definition:** Instructions you give to an AI in natural language.

**Real-world analogy:** Telling your assistant:
- "Check my calendar for tomorrow"
- "Schedule a meeting with John on Tuesday"

**In your project:**
```python
# This is a prompt
prompt = """
You are a health monitoring agent. Analyze this data:

Sleep: 4.5 hours (quality: 42/100)
Heart rate: 68 bpm (baseline: 58 bpm)
Stress: 72/100

Should we reduce the user's calendar load today?
Provide your recommendation and reasoning.
"""

# Send to Claude/GPT
response = claude.generate(prompt)
```

**Types of prompts:**

1. **User Prompt** - What YOU say
   - "Optimize my schedule today"

2. **System Prompt** - Instructions for the agent's role/behavior
   - "You are a calendar optimization agent. Always prioritize user health."

3. **Few-shot Prompt** - Examples to guide behavior
   - "Here are 3 examples of good scheduling decisions..."

**Key point:** Prompts are HOW you communicate with AI. The better your prompt, the better the result.

---

## 🧠 **CONTEXT**

**Simple Definition:** All the information the agent knows about RIGHT NOW.

**Real-world analogy:** What's on your desk when you're working:
- Your notes
- Recent emails
- Current task
- Relevant documents

**In your project:**
```python
# Building context for the agent
context = {
    "current_time": "2025-12-30 14:00",
    "user_health": {
        "sleep_last_night": "4.5 hours",
        "recovery_score": 38
    },
    "todays_calendar": [
        {"time": "9am", "title": "Team standup"},
        {"time": "10:30am", "title": "Code review"},
        # ...
    ],
    "learned_patterns": [
        "User is most productive Tuesdays 9-11am",
        "User needs 2+ hour focus blocks for coding"
    ],
    "conversation_history": [
        "User: Optimize my schedule",
        "Agent: I see you had poor sleep..."
    ]
}

# Agent uses this context to make decisions
prompt = f"""
Given this context:
{context}

What should we do with today's calendar?
"""
```

**Context includes:**
- Current state (time, date, weather)
- User data (health, calendar, preferences)
- Conversation history (what was said before)
- Learned patterns (historical knowledge)

**Important:** Context is TEMPORARY - what the agent knows during THIS conversation.

---

## 💾 **MEMORY**

**Simple Definition:** Information that persists across conversations/sessions.

**Real-world analogy:** Your brain remembering things from yesterday, last week, last year.

**Difference from Context:**
- **Context** = What's in your working memory RIGHT NOW (temporary)
- **Memory** = What's stored long-term (persistent)

**Types of memory in your project:**

### 1. **Short-term Memory** (Conversation History)
```python
# Stored during one conversation session
conversation_history = [
    {"role": "user", "content": "Optimize my schedule"},
    {"role": "agent", "content": "I'll check your health data..."},
    {"role": "user", "content": "Also consider my workout"}
]
# Lost when session ends
```

### 2. **Long-term Memory** (Database/Vector Store)
```python
# Stored in PostgreSQL
agent_memory = {
    "user_preferences": {
        "never_schedule_before": "8am",
        "preferred_workout_time": "6am",
        "max_meetings_per_day": 5
    },
    "learned_patterns": [
        "Poor sleep → reduce meetings next day",
        "Best focus time: Tuesday mornings"
    ],
    "past_decisions": [
        {"date": "2025-12-29", "action": "rescheduled meeting", "reason": "poor sleep"}
    ]
}
# Persists forever (or until deleted)
```

### 3. **Episodic Memory** (RAG/Vector Embeddings)
```python
# Stored in ChromaDB - semantic memory
# Remembers similar situations
vector_store.search("times I had poor sleep")
# Returns: All past instances with similar patterns
```

**Key point:** Agents need memory to learn and improve over time.

---

## 🎭 **MODE**

**Simple Definition:** Different operating states or behaviors for an agent.

**Real-world analogy:** Your car has modes: Park, Drive, Sport, Eco.

**In AI systems:**

### **Common Modes:**

1. **Observer Mode** (Watch only, don't act)
   ```python
   if mode == "observer":
       # Agent suggests but doesn't execute
       print("I would reschedule this meeting, but I'm in observer mode")
       ask_user_for_approval()
   ```

2. **Semi-Autonomous Mode** (Act but ask permission)
   ```python
   if mode == "semi_autonomous":
       # Agent acts on routine things, asks about edge cases
       if confidence > 80 and not edge_case:
           execute_action()
       else:
           ask_user_for_approval()
   ```

3. **Fully Autonomous Mode** (Act independently)
   ```python
   if mode == "autonomous":
       # Agent acts on its own (within safety rules)
       if confidence > 70:
           execute_action()
           notify_user()
   ```

4. **Plan Mode** (Planning only, not executing)
   ```python
   if mode == "plan":
       # Create detailed plan, show to user for approval
       plan = create_optimization_plan()
       present_to_user(plan)
       # Wait for user to approve before executing
   ```

**In your project:**
- Start in **Observer Mode** (safe, learn patterns)
- Move to **Semi-Autonomous** after 2 weeks
- Eventually **Fully Autonomous** (with safety rules)

---

# PART 3: WHAT AGENTS USE (The Toolbox)

## 🔧 **TOOLS**

**Simple Definition:** Functions/capabilities an agent can call to interact with the world.

**Real-world analogy:** Tools in a toolbox:
- Hammer (to build)
- Calculator (to compute)
- Phone (to communicate)

**In your project:**
```python
# These are tools
tools = [
    {
        "name": "get_calendar_events",
        "description": "Fetch events from Google Calendar",
        "parameters": {
            "date": "string",
            "calendar_id": "string"
        }
    },
    {
        "name": "get_sleep_data",
        "description": "Get last night's sleep data from Garmin",
        "parameters": {
            "date": "string"
        }
    },
    {
        "name": "reschedule_meeting",
        "description": "Move a meeting to a different time",
        "parameters": {
            "event_id": "string",
            "new_time": "string"
        }
    }
]
```

**How agents use tools:**
```python
# Agent (Claude) decides which tool to call

User: "Optimize my schedule for tomorrow"

Claude thinks:
1. "I need to see tomorrow's calendar"
   → Calls tool: get_calendar_events(date="2025-12-31")

2. "I should check if user slept well"
   → Calls tool: get_sleep_data(date="2025-12-30")

3. "Sleep was poor (4.5h), meetings too packed (6 meetings)"
   → Calls tool: reschedule_meeting(event_id="abc123", new_time="2026-01-02")

4. Returns to user: "Done! I rescheduled 2 meetings because..."
```

**Key characteristics of tools:**
- ✅ Well-defined function (clear input/output)
- ✅ Has a description (so agent knows when to use it)
- ✅ Has parameters (what information it needs)
- ✅ Returns a result

**Tools in your system:**
- `get_calendar_events()` - Read calendar
- `create_calendar_event()` - Make new event
- `get_sleep_data()` - Fetch Garmin sleep
- `get_heart_rate()` - Fetch heart rate
- `reschedule_meeting()` - Move meeting
- `search_similar_events()` - RAG search

---

## 🔌 **PLUGINS**

**Simple Definition:** Pre-packaged bundles of tools and functionality you can add to your system.

**Real-world analogy:** Browser extensions:
- Grammarly (spelling checker)
- AdBlock (ad blocker)
- You install them to add new capabilities

**Difference from Tools:**
- **Tool** = Single function (one hammer)
- **Plugin** = Bundle of related tools + logic (entire toolbox)

**Example:**
```python
# Plugin: Google Calendar Plugin
class GoogleCalendarPlugin:
    """Bundles all calendar-related tools together"""

    tools = [
        "get_events",
        "create_event",
        "reschedule_event",
        "delete_event",
        "find_free_slots"
    ]

    def __init__(self, credentials):
        self.calendar_api = GoogleCalendarAPI(credentials)

    def get_events(self, date):
        return self.calendar_api.list_events(date)

    # ... other tool implementations
```

**In practice:**
- Plugins are optional add-ons
- Tools are individual functions
- Plugins often contain multiple tools

**For your project:** You might not need formal "plugins" - just organize related tools together.

---

## 🎯 **SKILLS**

**Simple Definition:** Pre-defined workflows or complex tasks an agent can perform.

**Real-world analogy:** Learned procedures:
- "How to change a tire" (multi-step skill)
- "How to bake a cake" (recipe = skill)

**Difference from Tools:**
- **Tool** = Single action (hammer a nail)
- **Skill** = Multi-step procedure (build a chair)

**Example Skill:**
```python
# Skill: "Optimize Calendar After Poor Sleep"
class OptimizeAfterPoorSleepSkill:
    """
    A pre-defined workflow that:
    1. Checks sleep quality
    2. If poor, analyzes today's calendar
    3. Identifies optional meetings
    4. Reschedules them
    5. Adds recovery blocks
    6. Notifies user
    """

    def execute(self):
        # Step 1
        sleep = self.get_sleep_data()

        # Step 2
        if sleep.quality < 60:
            # Step 3
            calendar = self.get_calendar()
            optional = self.find_optional_meetings(calendar)

            # Step 4
            for meeting in optional[:2]:  # Reschedule top 2
                self.reschedule_meeting(meeting)

            # Step 5
            self.add_recovery_block("3pm", duration=60)

            # Step 6
            self.notify_user("Optimized your calendar due to poor sleep")
```

**Skills vs Tools:**
- Skill = Orchestrates multiple tools
- Tool = Single atomic action

**In Claude Code CLI:**
- Skills are invoked with slash commands (we'll cover this next)

---

## ⚡ **SLASH COMMANDS**

**Simple Definition:** Quick shortcuts to trigger specific actions or skills.

**Real-world analogy:** Keyboard shortcuts:
- `Ctrl+C` = Copy
- `Ctrl+V` = Paste
- `/help` = Show help menu

**In your project (if you build a CLI):**
```bash
# User types commands:
$ /optimize-schedule
→ Triggers the "Optimize Schedule" skill

$ /health-check
→ Runs HealthMonitorAgent and shows report

$ /learn-patterns
→ Runs PatternLearningAgent to analyze history

$ /undo-last-change
→ Reverts last calendar modification
```

**Slash commands are just:**
- User-friendly shortcuts
- Map to underlying skills or agent actions
- Common in chat interfaces

**You might implement:**
```python
# CLI command handler
def handle_command(command):
    if command == "/optimize-schedule":
        OrchestratorAgent().run_optimization()

    elif command == "/health-check":
        health = HealthMonitorAgent().get_status()
        print(health)

    elif command == "/learn-patterns":
        PatternLearningAgent().learn_from_history(days=90)
```

---

## 🪝 **HOOKS**

**Simple Definition:** Automated triggers that run code when specific events happen.

**Real-world analogy:**
- "When the doorbell rings → camera starts recording" (trigger → action)
- "When you get paid → auto-save 10%" (event → automated response)

**In your project:**
```python
# Hook: When new health data arrives, check if optimization needed
@hook.on("garmin_data_synced")
def on_health_data_updated(data):
    """This runs automatically when Garmin syncs"""

    recovery_score = calculate_recovery(data)

    if recovery_score < 50:
        # Trigger optimization agent
        OrchestratorAgent().run_emergency_optimization()
        NotificationAgent().alert("Poor recovery detected")

# Hook: Before agent modifies calendar, run safety check
@hook.before("calendar_modification")
def safety_check(action):
    """This runs before any calendar change"""

    if action.affects_external_participants:
        # Block action, require approval
        return {"allowed": False, "reason": "External participants"}

    return {"allowed": True}

# Hook: After agent takes action, log it
@hook.after("agent_action")
def log_action(action, result):
    """This runs after every agent action"""
    database.log({
        "timestamp": now(),
        "action": action,
        "result": result,
        "agent": action.agent_name
    })
```

**Common hook types:**
1. **Trigger hooks** - When event X happens, do Y
2. **Before hooks** - Run before an action (can block it)
3. **After hooks** - Run after an action (logging, cleanup)

**Real examples in your system:**
- `on_poor_sleep` → Trigger calendar optimization
- `before_reschedule` → Check safety rules
- `after_calendar_change` → Send notification
- `on_user_override` → Learn from correction

---

# PART 4: HOW SYSTEMS COMMUNICATE

## 🔗 **MCP (Model Context Protocol)**

**Simple Definition:** A standardized way for AI agents to connect to external tools and data sources.

**Real-world analogy:** USB-C:
- One universal connector
- Works with many devices
- Standardized protocol

**Without MCP (messy):**
```python
# Different APIs, different authentication, different formats
google_calendar_api.authenticate(oauth_token)
google_events = google_calendar_api.get_events()

garmin_api.login(username, password)
garmin_data = garmin_api.fetch_sleep()

strava_api.oauth_login(token)
strava_activities = strava_api.get_activities()
```

**With MCP (clean):**
```python
# Standardized interface for all external systems
mcp_client.call_tool("google_calendar:get_events", {"date": "2025-12-31"})
mcp_client.call_tool("garmin:get_sleep_data", {"date": "2025-12-30"})
mcp_client.call_tool("strava:get_activities", {"limit": 10})

# Same pattern for everything!
```

**What MCP provides:**
1. **Standard protocol** - Same interface for all integrations
2. **Tool discovery** - Agent can ask "what tools are available?"
3. **Authentication** - Built-in OAuth/API key management
4. **Type safety** - Tools have defined input/output schemas

**MCP Server:**
- A service that exposes tools via MCP protocol
- Example: "Google Calendar MCP Server" exposes calendar tools
- Example: "Garmin Health MCP Server" exposes health data tools

**In your project:**
```
Your Agent (Claude)
    ↓ (uses MCP protocol)
├── Google Calendar MCP Server → Google Calendar API
├── Garmin Health MCP Server → Garmin Connect API
├── Strava MCP Server → Strava API
└── PostgreSQL MCP Server → Database
```

**Key benefit:** Build it once, works everywhere. Other projects can use your MCP servers too.

---

## 📝 **LSP (Language Server Protocol)**

**Simple Definition:** A protocol that lets code editors understand programming languages.

**Real-world analogy:** A translator that helps your editor understand code:
- Shows errors while you type
- Provides autocomplete
- Enables "go to definition"

**What it does:**
```
Your Code Editor (VS Code, Vim, etc.)
    ↔ LSP ↔
Python Language Server
    ↓
Analyzes your code:
- "This variable is undefined" → Red squiggly line
- You type "cal" → Suggests "calculate_recovery_score()"
- Right-click function → "Go to definition"
```

**For your project:**
- LSP is mostly invisible to you
- It's what makes VS Code smart about Python
- Helps you write code with autocomplete and error detection

**You don't need to build LSP** - it's already built into your editor.

**Related to MCP:**
- LSP = For code editing tools
- MCP = For AI agent tools
- Both are standardized protocols

---

# PART 5: WHERE WORK HAPPENS

## 💻 **IDE (Integrated Development Environment)**

**Simple Definition:** The application where you write code.

**Examples:** VS Code, PyCharm, Vim, Sublime Text

**What it provides:**
- Text editor
- File browser
- Terminal
- Debugger
- Extensions/plugins

**For your project:**
- You're using VS Code
- This is where you'll write your Python code
- Claude Code CLI can integrate with it

**IDE Integration:**
- Your AI agent can interact with your IDE
- Example: Agent can read files, make edits, run tests
- This is done via MCP or LSP

---

## 🔄 **WORKFLOW**

**Simple Definition:** A sequence of steps to accomplish a task.

**Real-world analogy:** Morning routine:
1. Wake up
2. Shower
3. Make coffee
4. Check emails
5. Start work

**In your project:**

### **Example Workflow: "Daily Optimization"**
```python
def daily_optimization_workflow():
    """Runs every morning at 7am"""

    # Step 1: Collect data
    sleep_data = garmin_sync()
    calendar_data = google_calendar_sync()

    # Step 2: Analyze health
    health_status = HealthMonitorAgent().analyze(sleep_data)

    # Step 3: Check calendar
    productivity_forecast = ProductivityAgent().analyze(calendar_data)

    # Step 4: Decide if optimization needed
    if health_status.requires_action or productivity_forecast.overloaded:
        # Step 5: Create optimization plan
        plan = SchedulerOptimizerAgent().create_plan(
            health_status,
            productivity_forecast
        )

        # Step 6: Execute (if confident) or ask approval
        if plan.confidence > 80:
            execute_plan(plan)
        else:
            request_user_approval(plan)

        # Step 7: Notify user
        NotificationAgent().send_summary(plan)

    # Step 8: Log results
    database.log_daily_run(health_status, plan)
```

**Workflows are:**
- Pre-defined sequences
- Can be triggered manually or automatically
- Orchestrate multiple agents/tools

---

# PART 6: ACCESS CONTROL

## 🔐 **PERMISSIONS**

**Simple Definition:** Rules that control what an agent can and cannot do.

**Real-world analogy:** Employee permissions:
- Intern: Can read files, cannot delete
- Manager: Can approve expenses up to $5,000
- CEO: Can approve any expense

**In your project:**
```python
# Permission rules for agents
AGENT_PERMISSIONS = {
    "HealthMonitorAgent": {
        "can_read": ["garmin_data", "strava_data", "calendar"],
        "can_write": ["health_metrics_db"],
        "cannot_modify": ["calendar", "user_preferences"]
    },

    "SchedulerOptimizerAgent": {
        "can_read": ["calendar", "health_metrics_db"],
        "can_write": ["calendar"],  # Can modify calendar
        "requires_approval_for": [
            "deleting_events",
            "external_participant_changes",
            "weekend_modifications"
        ],
        "max_changes_per_day": 5
    },

    "OrchestratorAgent": {
        "can_read": ["*"],  # Read everything
        "can_write": ["*"],  # Write everything
        "can_invoke": ["all_subagents"]
    }
}
```

**Permission checks:**
```python
def reschedule_meeting(event_id, new_time):
    # Check permissions before acting
    if not agent.has_permission("modify_calendar"):
        raise PermissionError("Agent cannot modify calendar")

    if event.has_external_participants:
        if not agent.has_permission("modify_external_meetings"):
            # Require user approval
            return request_user_approval(action)

    # Proceed with reschedule
    calendar.update_event(event_id, new_time)
```

**Why permissions matter:**
- Safety (prevent agent from doing too much)
- Trust (you control what agent can do)
- Debugging (know what went wrong)

---

# PART 7: HOW EVERYTHING FITS TOGETHER

## 🗺️ Complete Mental Model

Let's put it ALL together with your Life Optimization AI:

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR LIFE (The Goal)                    │
│         "I want my calendar optimized for health            │
│          and productivity automatically"                    │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                 AI SYSTEM (The Solution)                    │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │         ORCHESTRATOR AGENT (The Manager)           │   │
│  │  • Has CONTEXT (current health, calendar)          │   │
│  │  • Has MEMORY (learned patterns, preferences)      │   │
│  │  • Uses PROMPTS to reason                          │   │
│  │  • Operates in different MODES (observer/auto)     │   │
│  │  • Has PERMISSIONS (what it can/cannot do)         │   │
│  └────────┬───────────────────────────────────────────┘   │
│           │                                                │
│           │ Calls SUBAGENTS ────────────┐                 │
│           ↓                              ↓                 │
│  ┌─────────────────┐           ┌─────────────────┐        │
│  │ HEALTH MONITOR  │           │ SCHEDULER       │        │
│  │ SUBAGENT        │           │ OPTIMIZER       │        │
│  │                 │           │ SUBAGENT        │        │
│  │ Uses TOOLS:     │           │                 │        │
│  │ • get_sleep()   │           │ Uses TOOLS:     │        │
│  │ • get_hr()      │           │ • reschedule()  │        │
│  └────────┬────────┘           └────────┬────────┘        │
│           │                              │                 │
│           │ Via MCP PROTOCOL             │                 │
│           ↓                              ↓                 │
│  ┌─────────────────┐           ┌─────────────────┐        │
│  │  GARMIN MCP     │           │ GOOGLE CAL MCP  │        │
│  │  SERVER         │           │ SERVER          │        │
│  │  (Connector)    │           │ (Connector)     │        │
│  └────────┬────────┘           └────────┬────────┘        │
│           │                              │                 │
└───────────┼──────────────────────────────┼─────────────────┘
            ↓                              ↓
┌─────────────────────┐       ┌─────────────────────┐
│  GARMIN API         │       │ GOOGLE CALENDAR API │
│  (External)         │       │ (External)          │
└─────────────────────┘       └─────────────────────┘
```

### **The Complete Flow:**

1. **Morning at 7am** - WORKFLOW triggered (scheduled task)

2. **OrchestratorAgent wakes up** (AGENT)
   - Loads CONTEXT (current date, user location, etc.)
   - Loads MEMORY (learned patterns from database)

3. **Checks permissions** (PERMISSIONS)
   - "Am I allowed to modify calendar today?"
   - "What are my limits?"

4. **Calls SUBAGENTS:**

   **HealthMonitorAgent:**
   - Receives PROMPT: "Analyze today's health data"
   - Uses TOOL: `get_sleep_data()` via MCP → Garmin Server → Garmin API
   - Uses TOOL: `get_heart_rate()` via MCP → Garmin Server
   - Returns: "Recovery score: 38/100 (poor sleep)"

   **ProductivityAgent:**
   - Uses TOOL: `get_calendar_events()` via MCP → Calendar Server
   - Analyzes meeting density
   - Returns: "6 meetings today (overloaded)"

5. **OrchestratorAgent reasons:**
   - PROMPT: "Poor recovery (38) + overloaded calendar (6 meetings) → what to do?"
   - Uses MEMORY: "Last time this happened, user approved rescheduling 2 meetings"
   - Checks MODE: "I'm in semi-autonomous mode"

6. **Calls SchedulerOptimizerAgent** (SUBAGENT):
   - Generates optimization plan
   - Uses TOOLS:
     - `find_optional_meetings()`
     - `check_external_participants()`
   - Creates plan: "Reschedule 2 meetings, add 1 recovery block"

7. **Safety checks:**
   - HOOK: `before_calendar_modification` runs
   - Checks PERMISSIONS
   - EdgeCaseDetector runs (utility)
   - Confidence: 82%

8. **Execution:**
   - MODE check: Semi-autonomous + confidence 82% = Execute
   - Uses TOOL: `reschedule_meeting()` via MCP → Calendar Server
   - Uses TOOL: `create_event()` for recovery block

9. **Logging & Notification:**
   - HOOK: `after_action` runs → logs to database
   - NotificationAgent sends Telegram message
   - Stores in MEMORY for future learning

10. **User sees notification:**
    - Can use SLASH COMMAND `/undo` if they disagree
    - HOOK: `on_user_override` learns from the feedback

---

## 📚 Quick Reference Table

| Term | Category | Simple Definition | Example in Your Project |
|------|----------|-------------------|-------------------------|
| **Agent** | Worker | Autonomous AI that makes decisions | OrchestratorAgent |
| **Subagent** | Worker | Specialized agent called by another | HealthMonitorAgent |
| **Prompt** | Communication | Instructions to AI in natural language | "Analyze this health data..." |
| **Context** | Knowledge | Temporary info agent knows right now | Current health + today's calendar |
| **Memory** | Knowledge | Persistent info stored long-term | User preferences, learned patterns |
| **Mode** | Behavior | Operating state of agent | Observer, Semi-autonomous, Autonomous |
| **Tool** | Action | Single function agent can call | `get_sleep_data()` |
| **Plugin** | Action | Bundle of related tools | Google Calendar Plugin |
| **Skill** | Action | Multi-step workflow/procedure | "Optimize After Poor Sleep" skill |
| **Slash Command** | Interface | Quick shortcut to trigger action | `/optimize-schedule` |
| **Hook** | Automation | Auto-triggered code on events | `on_poor_sleep` → optimize |
| **MCP** | Protocol | Standard way to connect to external systems | How agent talks to Google Calendar |
| **LSP** | Protocol | Standard for code editor features | VS Code understanding Python |
| **IDE** | Environment | Where you write code | VS Code |
| **Workflow** | Process | Sequence of steps to accomplish task | Daily optimization routine |
| **Permissions** | Security | What agent can/cannot do | "Can reschedule max 3 meetings/day" |

---

## 🎓 Test Your Understanding

**Question 1:** What's the difference between a Tool and a Skill?
<details>
<summary>Answer</summary>
- Tool = Single action (e.g., `get_sleep_data()`)
- Skill = Multi-step procedure using multiple tools (e.g., "Optimize Schedule" uses get_sleep, analyze_calendar, reschedule, notify)
</details>

**Question 2:** What's the difference between Context and Memory?
<details>
<summary>Answer</summary>
- Context = Temporary, what agent knows RIGHT NOW in this session
- Memory = Persistent, what agent remembers across sessions (stored in database)
</details>

**Question 3:** Is EdgeCaseDetector an Agent or a Utility?
<details>
<summary>Answer</summary>
Utility (not an agent). It's a helper function that agents call to check for edge cases. It doesn't make autonomous decisions.
</details>

**Question 4:** What's the purpose of MCP?
<details>
<summary>Answer</summary>
MCP provides a standardized way for agents to connect to external systems (Google Calendar, Garmin, databases) using a unified protocol - like USB-C for AI.
</details>

**Question 5:** Why do we need different Modes?
<details>
<summary>Answer</summary>
Different modes control how autonomous the agent is:
- Observer = Safe, just watch and suggest
- Semi-autonomous = Act on routine, ask about edge cases
- Autonomous = Act independently within safety rules

This lets you gradually build trust in the system.
</details>

---

## ✅ Summary: The Minimum You Need to Remember

### **3 Core Concepts:**

1. **AGENTS** are autonomous AI workers that use **TOOLS** to get things done

2. **AGENTS** think using **PROMPTS**, remember using **MEMORY**, and know current situation via **CONTEXT**

3. **AGENTS** connect to external systems via **MCP**, follow **WORKFLOWS**, and operate in different **MODES**

### **Everything else is details!**

- Subagents = specialized agents
- Skills = multi-tool workflows
- Hooks = automated triggers
- Permissions = safety rules
- Slash commands = shortcuts
- Plugins = tool bundles
- LSP/IDE = code editing stuff (less important for your project)

---

## 🚀 Now You're Ready!

With this mental model, you can now:
1. ✅ Understand the architecture we design
2. ✅ Make informed decisions about what to build
3. ✅ Ask specific questions when confused
4. ✅ Start implementing with confidence

**Next step:** Review any confusing terms, then we'll start building!

Questions?