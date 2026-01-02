from .base_agent import BaseAgent
from tools import CalendarTools, CALENDAR_TOOL_DEFINITIONS


class SchedulerAgent(BaseAgent):
    """
    Specialized agent for scheduling and calendar management.
    Uses RAG to learn from past events and make intelligent scheduling decisions.
    """

    SYSTEM_PROMPT = """You are an intelligent calendar scheduling assistant. Your role is to help users manage their calendar efficiently by:

1. Understanding their scheduling requests in natural language
2. Finding optimal time slots based on their calendar availability
3. Creating events with appropriate details
4. Learning from past events to suggest better scheduling
5. Providing statistics and insights about calendar usage

When scheduling:
- Always check for conflicts using find_free_slots
- Use search_similar_events to learn from past similar events
- Consider the user's working hours and preferences
- Create events with clear, descriptive titles and useful descriptions
- Be proactive in suggesting optimal times

Use the available tools to interact with the calendar and provide helpful scheduling assistance."""

    def __init__(self):
        super().__init__(
            system_prompt=self.SYSTEM_PROMPT,
            tools=CALENDAR_TOOL_DEFINITIONS
        )

        # Initialize calendar tools
        self.calendar_tools = CalendarTools()

        # Register tool functions
        self.register_tool("get_upcoming_events", self.calendar_tools.get_upcoming_events)
        self.register_tool("create_calendar_event", self.calendar_tools.create_calendar_event)
        self.register_tool("find_free_slots", self.calendar_tools.find_free_slots)
        self.register_tool("search_similar_events", self.calendar_tools.search_similar_events)
        self.register_tool("get_event_statistics", self.calendar_tools.get_event_statistics)

    def schedule_event(self, request: str) -> str:
        """
        Schedule an event based on natural language request.

        Args:
            request: Natural language scheduling request

        Returns:
            Response from the agent
        """
        return self.run(request)

    def find_time_for_meeting(self, meeting_description: str, duration_minutes: int, preferred_date: str = None) -> str:
        """
        Find the best time for a meeting based on description and duration.

        Args:
            meeting_description: Description of the meeting
            duration_minutes: Required duration in minutes
            preferred_date: Optional preferred date

        Returns:
            Suggested time slots and scheduling options
        """
        query = f"I need to schedule a {duration_minutes} minute meeting: {meeting_description}."
        if preferred_date:
            query += f" Preferably on {preferred_date}."
        query += " What are the best available time slots?"

        return self.run(query)

    def analyze_calendar_patterns(self) -> str:
        """
        Analyze calendar usage patterns and provide insights.

        Returns:
            Analysis and insights about calendar usage
        """
        return self.run("Analyze my calendar usage patterns for the past 30 days and provide insights.")
