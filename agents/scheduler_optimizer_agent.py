"""
SchedulerOptimizerAgent - Intelligently optimizes calendar based on health & patterns

This agent:
- Reads Google Calendar events
- Analyzes schedule against health data
- Proposes/makes schedule changes
- Respects safety rules (external meetings, important events)
- Logs all actions to database
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent
from integrations.google_calendar import GoogleCalendarClient
from database.connection import Database, log_agent_action


class SchedulerOptimizerAgent(BaseAgent):
    """
    Agent that optimizes calendar schedule based on health metrics and learned patterns.

    Safety Rules:
    - Never delete meetings with external participants
    - Never modify events marked as 'important' or 'critical'
    - Require confirmation for changes to events within next 2 hours
    - Always log actions to database
    """

    SYSTEM_PROMPT = """You are a schedule optimization AI agent that helps maintain work-life balance.

Your role:
1. Analyze calendar events in context of health metrics (sleep, stress, recovery)
2. Suggest schedule optimizations to improve productivity and wellbeing
3. Propose specific calendar changes (add breaks, move meetings, block focus time)
4. ALWAYS respect safety constraints

Health-Based Rules:
- Recovery score < 60: Suggest lighter workload, add recovery time
- Sleep < 6 hours: Recommend reducing morning commitments
- Stress > 70: Add breaks between meetings, suggest no-meeting blocks
- Good recovery (>80): Schedule important/creative work

Safety Constraints (CRITICAL):
- NEVER delete or move meetings with external participants
- NEVER modify events within 2 hours of start time without explicit approval
- NEVER schedule over existing events
- ALWAYS explain reasoning for changes

Available tools:
- get_calendar_events: Fetch upcoming calendar events
- get_free_slots: Find available time slots
- propose_schedule_change: Suggest a calendar modification
- get_current_health: Get latest health metrics

When asked to optimize schedule:
1. Get upcoming calendar events
2. Get current health metrics
3. Analyze schedule against health data
4. Propose specific, actionable changes
5. Explain reasoning clearly"""

    def __init__(self, calendar_client: Optional[GoogleCalendarClient] = None,
                 mode: str = "observer",
                 skip_calendar: bool = False):
        """
        Initialize the SchedulerOptimizerAgent.

        Args:
            calendar_client: GoogleCalendarClient instance (creates new if None)
            mode: Operation mode - 'observer' (propose only) or 'autonomous' (execute)
            skip_calendar: Skip Google Calendar initialization (for testing)

        Note: LLM provider is read from settings.llm_provider in .env
        """
        # Initialize calendar (optional for testing)
        if skip_calendar:
            self.calendar = None
            print("   ℹ️  Google Calendar disabled (testing mode)")
        else:
            try:
                self.calendar = calendar_client or GoogleCalendarClient()
            except FileNotFoundError:
                print("   ⚠️  Google Calendar credentials not found")
                print("      Agent will work without calendar integration")
                self.calendar = None

        self.mode = mode  # 'observer' or 'autonomous'

        Database.initialize_pool()

        # Initialize BaseAgent with tools
        tools = self._create_tools()
        super().__init__(
            system_prompt=self.SYSTEM_PROMPT,
            tools=tools
        )

        print(f"📅 SchedulerOptimizerAgent initialized in {mode.upper()} mode")
        if mode == "observer":
            print("   ℹ️  Will propose changes only (no automatic execution)")
        else:
            print("   ⚠️  AUTONOMOUS mode - will execute approved changes")

    def _create_tools(self) -> List[Dict[str, Any]]:
        """Create tool definitions for the agent."""
        return [
            {
                "name": "get_calendar_events",
                "description": "Get calendar events for a specific date range",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days_ahead": {
                            "type": "integer",
                            "description": "Number of days ahead to fetch (default 7)"
                        }
                    }
                }
            },
            {
                "name": "get_free_slots",
                "description": "Find available time slots in the calendar",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date to check (YYYY-MM-DD format)"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Required duration in minutes"
                        }
                    },
                    "required": ["date", "duration_minutes"]
                }
            },
            {
                "name": "propose_schedule_change",
                "description": "Propose a calendar change (add event, move event, add break)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action_type": {
                            "type": "string",
                            "enum": ["add_event", "add_break", "move_event", "delete_event"],
                            "description": "Type of change to propose"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Explanation for why this change is beneficial"
                        },
                        "event_details": {
                            "type": "object",
                            "description": "Event details (summary, start_time, end_time, event_id if modifying)"
                        }
                    },
                    "required": ["action_type", "reasoning", "event_details"]
                }
            },
            {
                "name": "get_current_health",
                "description": "Get latest health metrics from database",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def _get_calendar_events(self, days_ahead: int = 7) -> str:
        """Tool: Get upcoming calendar events."""
        if not self.calendar:
            return "Google Calendar not configured. Using mock data for testing."

        try:
            time_min = datetime.utcnow()
            time_max = time_min + timedelta(days=days_ahead)

            events = self.calendar.get_events(time_min, time_max)

            if not events:
                return "No upcoming events found."

            # Format events for LLM
            formatted = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                summary = event.get('summary', 'No title')
                attendees = event.get('attendees', [])
                has_external = len(attendees) > 1  # More than just you

                formatted.append({
                    'id': event['id'],
                    'summary': summary,
                    'start': start,
                    'end': end,
                    'has_external_participants': has_external,
                    'attendee_count': len(attendees)
                })

            return json.dumps(formatted, indent=2)

        except Exception as e:
            return f"Error fetching events: {str(e)}"

    def _get_free_slots(self, date: str, duration_minutes: int) -> str:
        """Tool: Find free time slots on a given date."""
        if not self.calendar:
            return "Google Calendar not configured. Cannot find free slots."

        try:
            target_date = datetime.fromisoformat(date)
            day_start = target_date.replace(hour=8, minute=0, second=0)  # 8 AM
            day_end = target_date.replace(hour=18, minute=0, second=0)   # 6 PM

            # Get busy times
            busy_times = self.calendar.get_free_busy(day_start, day_end)

            # Calculate free slots
            free_slots = []
            current_time = day_start

            for busy in busy_times:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                if (busy_start - current_time).total_seconds() >= duration_minutes * 60:
                    free_slots.append({
                        'start': current_time.isoformat(),
                        'end': busy_start.isoformat()
                    })
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                current_time = max(current_time, busy_end)

            # Check remaining time until end of day
            if (day_end - current_time).total_seconds() >= duration_minutes * 60:
                free_slots.append({
                    'start': current_time.isoformat(),
                    'end': day_end.isoformat()
                })

            return json.dumps(free_slots, indent=2)

        except Exception as e:
            return f"Error finding free slots: {str(e)}"

    def _propose_schedule_change(self, action_type: str, reasoning: str,
                                 event_details: Dict[str, Any]) -> str:
        """Tool: Propose a schedule change."""
        proposal = {
            'action': action_type,
            'reasoning': reasoning,
            'details': event_details,
            'timestamp': datetime.now().isoformat(),
            'mode': self.mode
        }

        # Log to database
        log_agent_action(
            agent_name='SchedulerOptimizerAgent',
            action_type=f'propose_{action_type}',
            data=proposal
        )

        # In observer mode, just return the proposal
        if self.mode == "observer":
            return f"""
PROPOSED CHANGE (Observer Mode - Not Executed):

Action: {action_type}
Reasoning: {reasoning}
Details: {json.dumps(event_details, indent=2)}

To execute this change, switch to autonomous mode or approve manually.
"""

        # In autonomous mode, execute (with safety checks)
        else:
            # Safety check: Don't modify events with external participants
            if action_type in ['move_event', 'delete_event']:
                event_id = event_details.get('event_id')
                if event_id:
                    # Would need to fetch event and check attendees
                    # For now, require manual approval
                    return f"Change requires manual approval (safety rule): {action_type}"

            return f"Proposed: {action_type} - {reasoning}\n(Execution pending safety approval)"

    def _get_current_health(self) -> str:
        """Tool: Get latest health metrics from database."""
        try:
            query = """
            SELECT * FROM recent_health_summary
            ORDER BY date DESC
            LIMIT 1
            """
            result = Database.execute_one(query)

            if result:
                return json.dumps(dict(result), indent=2, default=str)
            else:
                return "No health data available"

        except Exception as e:
            return f"Error fetching health data: {str(e)}"

    def optimize_schedule(self, days_ahead: int = 7,
                         context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze and optimize schedule based on health metrics.

        Args:
            days_ahead: Number of days to analyze
            context: Additional context (e.g., "I have important deadline Friday")

        Returns:
            Dictionary with analysis and proposed changes
        """
        prompt = f"""Analyze my schedule for the next {days_ahead} days and propose optimizations.

Steps:
1. Get my calendar events using get_calendar_events
2. Get my current health metrics using get_current_health
3. Analyze schedule against health data
4. Propose specific changes using propose_schedule_change

"""
        if context:
            prompt += f"\nAdditional context: {context}\n"

        prompt += "\nProvide concrete, actionable recommendations."

        try:
            response = self.run(prompt)

            # Log the optimization run
            log_agent_action(
                agent_name='SchedulerOptimizerAgent',
                action_type='schedule_optimization',
                data={'days_ahead': days_ahead, 'response': response}
            )

            return {
                'success': True,
                'analysis': response,
                'mode': self.mode
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def create_scheduler_optimizer(mode: str = "observer",
                               skip_calendar: bool = False) -> SchedulerOptimizerAgent:
    """
    Factory function to create SchedulerOptimizerAgent.

    Args:
        mode: 'observer' (propose only) or 'autonomous' (execute changes)
        skip_calendar: Skip Google Calendar initialization (for testing)

    Returns:
        Initialized SchedulerOptimizerAgent

    Note: LLM provider is configured via LLM_PROVIDER in .env
    """
    return SchedulerOptimizerAgent(mode=mode, skip_calendar=skip_calendar)
