"""
Strava Connector - Pulls training insights that Garmin doesn't provide

Focuses on:
- Fitness & Fatigue (CTL/ATL/TSB)
- Relative Effort
- Training Load trends
- Performance metrics

Does NOT pull activity details (those come from Garmin to avoid duplication)
"""
import os
from typing import Dict, Any, Optional, List
from datetime import date, timedelta
from stravalib.client import Client


class StravaConnector:
    """
    Connector for Strava API focused on training insights.

    Strava provides unique metrics calculated from your activities:
    - Fitness (CTL - Chronic Training Load)
    - Fatigue (ATL - Acute Training Load)
    - Form (TSB - Training Stress Balance)
    - Relative Effort per activity
    """

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Strava connector.

        Args:
            access_token: Strava API access token (optional, reads from env)
        """
        self.access_token = access_token or os.getenv('STRAVA_ACCESS_TOKEN')
        self._authenticated = False

        if self.access_token:
            try:
                self.client = Client(access_token=self.access_token)
                # Test authentication
                athlete = self.client.get_athlete()
                self._authenticated = True
                print(f"✅ Connected to Strava (Athlete: {athlete.firstname} {athlete.lastname})")
            except Exception as e:
                print(f"❌ Failed to connect to Strava: {e}")
                self._authenticated = False
        else:
            print("ℹ️  Strava access token not provided. Using mock data.")
            self._authenticated = False

    def get_fitness_fatigue(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get Fitness & Fatigue metrics for a specific date.

        Strava calculates these from your training history:
        - CTL (Chronic Training Load): Long-term fitness (42-day average)
        - ATL (Acute Training Load): Short-term fatigue (7-day average)
        - TSB (Training Stress Balance): Form = CTL - ATL

        Args:
            target_date: Date to get metrics for (defaults to today)

        Returns:
            Dictionary with fitness/fatigue metrics
        """
        if not self._authenticated:
            return self._mock_fitness_fatigue(target_date)

        # Note: Strava API doesn't directly expose CTL/ATL
        # They're calculated client-side or via premium features
        # This is a placeholder for future implementation
        print("⚠️  Fitness/Fatigue requires Strava Premium or third-party calculation")
        return self._mock_fitness_fatigue(target_date)

    def get_training_load_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        Get training load trend over recent days.

        Args:
            days: Number of days to analyze (default 30)

        Returns:
            Dictionary with training load analysis
        """
        if not self._authenticated:
            return self._mock_training_load_trend(days)

        try:
            # Get recent activities
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            activities = self.client.get_activities(
                after=start_date,
                before=end_date
            )

            # Calculate training load from activity efforts
            total_relative_effort = 0
            activity_count = 0
            weekly_loads = []

            for activity in activities:
                if hasattr(activity, 'suffer_score') and activity.suffer_score:
                    total_relative_effort += activity.suffer_score
                    activity_count += 1

            avg_weekly_load = (total_relative_effort / days) * 7 if days > 0 else 0

            return {
                'period_days': days,
                'total_activities': activity_count,
                'total_relative_effort': total_relative_effort,
                'avg_weekly_load': round(avg_weekly_load, 1),
                'trend': 'increasing' if avg_weekly_load > 300 else 'moderate'
            }

        except Exception as e:
            print(f"❌ Error fetching Strava training load: {e}")
            return self._mock_training_load_trend(days)

    def get_recent_efforts(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent activity efforts (Relative Effort scores).

        Args:
            days: Number of days to look back (default 7)

        Returns:
            List of activities with effort scores
        """
        if not self._authenticated:
            return self._mock_recent_efforts(days)

        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            activities = self.client.get_activities(
                after=start_date,
                before=end_date
            )

            efforts = []
            for activity in activities:
                effort = {
                    'name': activity.name,
                    'type': activity.type,
                    'date': activity.start_date_local.date().isoformat(),
                    'relative_effort': getattr(activity, 'suffer_score', 0),
                    'duration_minutes': activity.moving_time.seconds / 60 if activity.moving_time else 0,
                    'distance_km': float(activity.distance) / 1000 if activity.distance else 0
                }
                efforts.append(effort)

            return efforts

        except Exception as e:
            print(f"❌ Error fetching Strava efforts: {e}")
            return self._mock_recent_efforts(days)

    # Mock data methods for testing without API
    def _mock_fitness_fatigue(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock fitness/fatigue data for testing."""
        import random

        if target_date is None:
            target_date = date.today()

        # Simulate realistic CTL/ATL values
        ctl = random.randint(40, 80)  # Chronic Training Load (fitness)
        atl = random.randint(30, 100)  # Acute Training Load (fatigue)
        tsb = ctl - atl  # Training Stress Balance (form)

        return {
            'date': target_date.isoformat(),
            'ctl': ctl,  # Fitness (higher = more fit)
            'atl': atl,  # Fatigue (higher = more tired)
            'tsb': tsb,  # Form (positive = fresh, negative = fatigued)
            'fitness_level': 'good' if ctl > 60 else 'moderate',
            'freshness': 'fresh' if tsb > 5 else 'fatigued' if tsb < -10 else 'balanced',
            'source': 'mock'
        }

    def _mock_training_load_trend(self, days: int) -> Dict[str, Any]:
        """Generate mock training load trend."""
        import random

        total_effort = random.randint(200, 600)
        avg_weekly = (total_effort / days) * 7

        return {
            'period_days': days,
            'total_activities': random.randint(10, 25),
            'total_relative_effort': total_effort,
            'avg_weekly_load': round(avg_weekly, 1),
            'trend': 'increasing' if avg_weekly > 300 else 'moderate',
            'source': 'mock'
        }

    def _mock_recent_efforts(self, days: int) -> List[Dict[str, Any]]:
        """Generate mock recent efforts."""
        import random
        from datetime import datetime, timedelta

        efforts = []
        for i in range(min(days, 7)):  # Up to 7 activities
            effort_date = date.today() - timedelta(days=i)
            efforts.append({
                'name': f'{"Morning Run" if i % 2 == 0 else "Evening Ride"}',
                'type': 'Run' if i % 2 == 0 else 'Ride',
                'date': effort_date.isoformat(),
                'relative_effort': random.randint(30, 150),
                'duration_minutes': random.randint(30, 90),
                'distance_km': round(random.uniform(5, 20), 2),
                'source': 'mock'
            })

        return efforts


def create_strava_connector(access_token: Optional[str] = None) -> StravaConnector:
    """
    Factory function to create StravaConnector.

    Args:
        access_token: Strava API access token (optional)

    Returns:
        Initialized StravaConnector
    """
    return StravaConnector(access_token=access_token)
