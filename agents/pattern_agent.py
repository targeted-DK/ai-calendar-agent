from .base_agent import BaseAgent
from tools import CalendarTools
from rag import VectorStore
from typing import List, Dict
import datetime


class PatternLearningAgent(BaseAgent):
    """
    Agent specialized in learning user patterns and preferences.
    Uses RAG to analyze historical data and make recommendations.
    """

    SYSTEM_PROMPT = """You are a pattern recognition and learning assistant for calendar management. Your role is to:

1. Analyze historical calendar data to identify patterns
2. Learn user preferences and working styles
3. Detect recurring meeting types and their characteristics
4. Identify optimal times for different types of activities
5. Suggest improvements to calendar organization

You should be analytical and data-driven, providing insights based on actual calendar usage patterns."""

    def __init__(self):
        super().__init__(system_prompt=self.SYSTEM_PROMPT)

        self.calendar_tools = CalendarTools()
        self.vector_store = VectorStore()

    def learn_from_history(self, days_back: int = 90) -> Dict:
        """
        Learn patterns from historical calendar data.

        Args:
            days_back: Number of days of history to analyze

        Returns:
            Dictionary of learned patterns
        """
        # Get historical events
        time_min = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
        time_max = datetime.datetime.utcnow()

        events = self.calendar_tools.calendar.get_events(time_min, time_max, max_results=500)

        # Store in vector database for RAG
        self.vector_store.add_events_batch(events)

        # Analyze patterns
        patterns = self._analyze_patterns(events)

        # Store learned patterns
        for pattern_id, pattern_data in patterns.items():
            self.vector_store.add_pattern(
                pattern_id=pattern_id,
                pattern_text=pattern_data["description"],
                metadata=pattern_data["metadata"]
            )

        return patterns

    def _analyze_patterns(self, events: List[Dict]) -> Dict:
        """
        Analyze events to identify patterns.

        Args:
            events: List of calendar events

        Returns:
            Dictionary of identified patterns
        """
        patterns = {}

        # Time-of-day preferences
        time_slots = {"morning": 0, "afternoon": 0, "evening": 0}

        # Meeting types
        meeting_types = {}

        # Day-of-week patterns
        day_patterns = {i: 0 for i in range(7)}

        for event in events:
            start = event.get('start', {}).get('dateTime')
            if not start:
                continue

            start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            hour = start_dt.hour
            day_of_week = start_dt.weekday()

            # Classify time of day
            if 6 <= hour < 12:
                time_slots["morning"] += 1
            elif 12 <= hour < 17:
                time_slots["afternoon"] += 1
            else:
                time_slots["evening"] += 1

            # Track day of week
            day_patterns[day_of_week] += 1

            # Classify meeting types
            summary = event.get('summary', '').lower()
            for keyword in ['standup', 'meeting', 'call', 'sync', 'review', 'planning']:
                if keyword in summary:
                    meeting_types[keyword] = meeting_types.get(keyword, 0) + 1

        # Create pattern descriptions
        patterns["time_preference"] = {
            "description": f"User typically schedules {max(time_slots, key=time_slots.get)} meetings",
            "metadata": {"time_slots": time_slots, "type": "time_preference"}
        }

        patterns["day_preference"] = {
            "description": f"User most active on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][max(day_patterns, key=day_patterns.get)]}",
            "metadata": {"day_patterns": day_patterns, "type": "day_preference"}
        }

        patterns["meeting_types"] = {
            "description": f"Common meeting types: {', '.join(meeting_types.keys())}",
            "metadata": {"meeting_types": meeting_types, "type": "meeting_types"}
        }

        return patterns

    def get_recommendations(self, query: str) -> str:
        """
        Get scheduling recommendations based on learned patterns.

        Args:
            query: User query about scheduling

        Returns:
            Recommendations based on patterns
        """
        # Search for relevant patterns
        relevant_patterns = self.vector_store.search_patterns(query, n_results=3)

        # Search for similar events
        similar_events = self.vector_store.search_similar_events(query, n_results=5)

        # Build context for the agent
        context = f"Query: {query}\n\n"
        context += "Relevant patterns:\n"
        for pattern in relevant_patterns:
            context += f"- {pattern['document']}\n"

        context += "\nSimilar past events:\n"
        for event in similar_events:
            context += f"- {event['document']} (on {event['metadata'].get('start', 'unknown date')})\n"

        context += "\nBased on these patterns and similar events, provide scheduling recommendations."

        return self.run(context)

    def suggest_optimal_time(self, event_type: str, duration_minutes: int) -> Dict:
        """
        Suggest optimal time for an event based on learned patterns.

        Args:
            event_type: Type of event (e.g., "meeting", "focus time")
            duration_minutes: Required duration

        Returns:
            Suggested time and reasoning
        """
        # Search for similar events
        similar_events = self.vector_store.search_similar_events(event_type, n_results=10)

        if not similar_events:
            return {
                "suggestion": "No historical data available for this event type",
                "reasoning": "No similar events found in history"
            }

        # Analyze when similar events typically occur
        hours = []
        for event in similar_events:
            start = event['metadata'].get('start')
            if start:
                start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                hours.append(start_dt.hour)

        if hours:
            avg_hour = sum(hours) // len(hours)
            return {
                "suggestion": f"Based on past {event_type} events, optimal time is around {avg_hour}:00",
                "reasoning": f"Analyzed {len(similar_events)} similar events",
                "typical_hour": avg_hour
            }

        return {
            "suggestion": "Insufficient data for recommendation",
            "reasoning": "Could not determine pattern from available events"
        }
