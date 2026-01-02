from typing import Dict, List, Optional
import datetime
from integrations import GoogleCalendarClient
from rag import VectorStore


class CalendarTools:
    """Tools for calendar operations that agents can use."""

    def __init__(self):
        self.calendar = GoogleCalendarClient()
        self.vector_store = VectorStore()

    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """
        Get upcoming events for the next N days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of upcoming events
        """
        time_min = datetime.datetime.utcnow()
        time_max = time_min + datetime.timedelta(days=days)

        events = self.calendar.get_events(time_min, time_max)

        # Format for agent consumption
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': event.get('id'),
                'summary': event.get('summary', 'Untitled'),
                'start': event.get('start', {}).get('dateTime', ''),
                'end': event.get('end', {}).get('dateTime', ''),
                'description': event.get('description', ''),
            })

        return formatted_events

    def create_calendar_event(
        self,
        summary: str,
        start_time: str,
        duration_minutes: int,
        description: str = ""
    ) -> Dict:
        """
        Create a new calendar event.

        Args:
            summary: Event title
            start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
            duration_minutes: Event duration in minutes
            description: Event description

        Returns:
            Created event details
        """
        start_dt = datetime.datetime.fromisoformat(start_time)
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

        event = self.calendar.create_event(
            summary=summary,
            start_time=start_dt,
            end_time=end_dt,
            description=description
        )

        if event:
            # Add to vector store for future RAG
            self.vector_store.add_event(event)

        return {
            'success': event is not None,
            'event_id': event.get('id') if event else None,
            'summary': summary,
            'start': start_time
        }

    def find_free_slots(
        self,
        date: str,
        duration_minutes: int,
        working_hours_start: int = 9,
        working_hours_end: int = 17
    ) -> List[Dict]:
        """
        Find free time slots on a given date.

        Args:
            date: Date in YYYY-MM-DD format
            duration_minutes: Required duration in minutes
            working_hours_start: Start of working hours (24h format)
            working_hours_end: End of working hours (24h format)

        Returns:
            List of available time slots
        """
        target_date = datetime.datetime.fromisoformat(date)
        time_min = target_date.replace(hour=working_hours_start, minute=0, second=0)
        time_max = target_date.replace(hour=working_hours_end, minute=0, second=0)

        # Get busy times
        busy_times = self.calendar.get_free_busy(time_min, time_max)

        # Calculate free slots
        free_slots = []
        current_time = time_min

        for busy_block in busy_times:
            busy_start = datetime.datetime.fromisoformat(busy_block['start'].replace('Z', '+00:00'))
            busy_end = datetime.datetime.fromisoformat(busy_block['end'].replace('Z', '+00:00'))

            # Check if there's a gap before this busy block
            if (busy_start - current_time).total_seconds() / 60 >= duration_minutes:
                free_slots.append({
                    'start': current_time.isoformat(),
                    'end': busy_start.isoformat(),
                    'duration_minutes': int((busy_start - current_time).total_seconds() / 60)
                })

            current_time = max(current_time, busy_end)

        # Check for free time after last busy block
        if (time_max - current_time).total_seconds() / 60 >= duration_minutes:
            free_slots.append({
                'start': current_time.isoformat(),
                'end': time_max.isoformat(),
                'duration_minutes': int((time_max - current_time).total_seconds() / 60)
            })

        return free_slots

    def search_similar_events(self, query: str) -> List[Dict]:
        """
        Search for similar past events using RAG.

        Args:
            query: Search query describing the event

        Returns:
            List of similar events from history
        """
        similar_events = self.vector_store.search_similar_events(query, n_results=5)
        return similar_events

    def get_event_statistics(self, days: int = 30) -> Dict:
        """
        Get statistics about calendar usage.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary of statistics
        """
        time_min = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        time_max = datetime.datetime.utcnow()

        events = self.calendar.get_events(time_min, time_max, max_results=1000)

        total_events = len(events)
        total_duration = 0

        event_types = {}

        for event in events:
            # Calculate duration
            start = event.get('start', {}).get('dateTime')
            end = event.get('end', {}).get('dateTime')

            if start and end:
                start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                duration = (end_dt - start_dt).total_seconds() / 3600
                total_duration += duration

            # Categorize by summary keywords
            summary = event.get('summary', '').lower()
            categorized = False
            for keyword in ['meeting', 'call', 'sync', 'standup']:
                if keyword in summary:
                    event_types[keyword] = event_types.get(keyword, 0) + 1
                    categorized = True
                    break

            if not categorized:
                event_types['other'] = event_types.get('other', 0) + 1

        return {
            'total_events': total_events,
            'total_hours': round(total_duration, 2),
            'average_events_per_day': round(total_events / days, 2),
            'event_types': event_types,
            'period_days': days
        }


# Tool definitions for LLM function calling
CALENDAR_TOOL_DEFINITIONS = [
    {
        "name": "get_upcoming_events",
        "description": "Get upcoming calendar events for the next N days",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default: 7)"
                }
            }
        }
    },
    {
        "name": "create_calendar_event",
        "description": "Create a new event on the calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Event title or summary"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration of the event in minutes"
                },
                "description": {
                    "type": "string",
                    "description": "Event description or notes"
                }
            },
            "required": ["summary", "start_time", "duration_minutes"]
        }
    },
    {
        "name": "find_free_slots",
        "description": "Find available time slots on a specific date",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Required duration in minutes"
                },
                "working_hours_start": {
                    "type": "integer",
                    "description": "Start of working hours in 24h format (default: 9)"
                },
                "working_hours_end": {
                    "type": "integer",
                    "description": "End of working hours in 24h format (default: 17)"
                }
            },
            "required": ["date", "duration_minutes"]
        }
    },
    {
        "name": "search_similar_events",
        "description": "Search for similar past events to understand patterns",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Description of the type of event to search for"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_event_statistics",
        "description": "Get statistics about calendar usage patterns",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)"
                }
            }
        }
    }
]
