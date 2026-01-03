"""
Health Monitor Agent - Analyzes health metrics and provides recommendations
Uses mock Garmin data for testing (can add real credentials later)
"""
from datetime import date, timedelta
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from integrations.garmin_connector import GarminConnector
from database.connection import insert_health_metric


class HealthMonitorAgent(BaseAgent):
    """
    Agent that monitors health metrics from Garmin and provides
    recommendations for calendar optimization.

    NOTE: Uses mock data by default. Add GARMIN_EMAIL and GARMIN_PASSWORD
    to .env file to use real Garmin data.
    """

    SYSTEM_PROMPT = """You are a health monitoring AI agent. Your role is to:

1. Analyze health metrics (sleep, heart rate, stress, recovery)
2. Identify concerning patterns or poor recovery
3. Provide specific, actionable recommendations for calendar optimization
4. Prioritize user health and recovery

When analyzing health data:
- Sleep < 6 hours = POOR (requires action)
- Sleep 6-7 hours = FAIR (monitor)
- Sleep 7-8.5 hours = GOOD
- Sleep > 8.5 hours = potential oversleep

Recovery score:
- 0-40: CRITICAL - aggressive calendar reduction needed
- 41-60: POOR - reduce non-essential activities
- 61-80: GOOD - maintain current schedule
- 81-100: EXCELLENT - can handle high load

Provide clear, specific recommendations like:
- "Reduce meeting load by 50% today"
- "Add 1-hour recovery block at 3pm"
- "Reschedule non-critical meetings"
- "Suggest light activity instead of intense workout"

Always explain your reasoning based on the data."""

    def __init__(self, garmin_connector: Optional[GarminConnector] = None):
        """
        Initialize Health Monitor Agent.

        Args:
            garmin_connector: Garmin connector instance (uses mock data if not provided)
        """
        # Define tools this agent can use
        tools = [
            {
                "name": "get_sleep_data",
                "description": "Get sleep data from Garmin for a specific date",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (optional, defaults to yesterday)"
                        }
                    }
                }
            },
            {
                "name": "get_daily_stats",
                "description": "Get daily health statistics from Garmin",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (optional, defaults to today)"
                        }
                    }
                }
            },
            {
                "name": "get_stress_data",
                "description": "Get stress data from Garmin",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (optional, defaults to today)"
                        }
                    }
                }
            },
            {
                "name": "get_recovery_score",
                "description": "Calculate overall recovery score (0-100) based on sleep, HR, and stress",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (optional)"
                        }
                    }
                }
            }
        ]

        super().__init__(system_prompt=self.SYSTEM_PROMPT, tools=tools)

        # Initialize Garmin connector (uses mock data by default)
        self.garmin = garmin_connector if garmin_connector else GarminConnector()

        print("ℹ️  HealthMonitorAgent initialized with MOCK Garmin data")
        print("   To use real data, add GARMIN_EMAIL and GARMIN_PASSWORD to .env")

        # Register tool functions
        self.register_tool("get_sleep_data", self._get_sleep_data)
        self.register_tool("get_daily_stats", self._get_daily_stats)
        self.register_tool("get_stress_data", self._get_stress_data)
        self.register_tool("get_recovery_score", self._get_recovery_score)

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            from datetime import datetime
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _get_sleep_data(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Get sleep data"""
        parsed_date = self._parse_date(target_date)
        return self.garmin.get_sleep_data(parsed_date)

    def _get_daily_stats(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Get daily stats"""
        parsed_date = self._parse_date(target_date)
        return self.garmin.get_daily_stats(parsed_date)

    def _get_stress_data(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Get stress data"""
        parsed_date = self._parse_date(target_date)
        return self.garmin.get_stress_data(parsed_date)

    def _get_recovery_score(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Get recovery score"""
        parsed_date = self._parse_date(target_date)
        score = self.garmin.get_recovery_score(parsed_date)
        return {"recovery_score": score, "date": target_date or "today"}

    def check_health(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a comprehensive health check.

        Args:
            target_date: Date to check (YYYY-MM-DD format), defaults to yesterday

        Returns:
            Dictionary with health status and recommendations
        """
        user_message = f"Analyze my health metrics for {target_date or 'yesterday'}. "
        user_message += "Provide recovery score and specific recommendations for calendar optimization."

        response = self.run(user_message)

        # Also get the raw recovery score
        parsed_date = self._parse_date(target_date)
        recovery_score = self.garmin.get_recovery_score(parsed_date)

        return {
            "recovery_score": recovery_score,
            "analysis": response,
            "requires_action": recovery_score < 60
        }

    def store_to_database(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Store health data in the database.

        Args:
            target_date: Date to store (YYYY-MM-DD format), defaults to yesterday

        Returns:
            Result of storage operation
        """
        parsed_date = self._parse_date(target_date) or (date.today() - timedelta(days=1))

        # Get all health data
        sleep = self.garmin.get_sleep_data(parsed_date)
        stats = self.garmin.get_daily_stats(parsed_date)
        stress = self.garmin.get_stress_data(parsed_date)
        recovery = self.garmin.get_recovery_score(parsed_date)

        # Prepare data for database
        health_data = {
            'timestamp': f"{parsed_date} 00:00:00",
            'source': 'garmin_mock',  # Indicates mock data
            'sleep_duration_hours': sleep.get('sleep_duration_hours'),
            'sleep_quality_score': sleep.get('sleep_quality_score'),
            'resting_heart_rate': stats.get('resting_heart_rate'),
            'stress_level': stress.get('avg_stress_level'),
            'recovery_score': recovery,
            'steps': stats.get('steps'),
            'raw_data': str({'sleep': sleep, 'stats': stats, 'stress': stress})
        }

        # Insert into database
        try:
            health_id = insert_health_metric(health_data)
            return {
                "success": True,
                "health_id": health_id,
                "date": str(parsed_date),
                "recovery_score": recovery
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience function
def create_health_monitor() -> HealthMonitorAgent:
    """Create and return a Health Monitor Agent instance"""
    return HealthMonitorAgent()
