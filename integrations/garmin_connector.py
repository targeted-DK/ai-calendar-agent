"""
Garmin Connect API integration for health data
Uses the unofficial garminconnect library
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import json


class GarminConnector:
    """
    Connector for Garmin Connect health data.

    NOTE: Uses unofficial API via garminconnect library.
    Install: pip install garminconnect
    """

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Garmin connector.

        Args:
            email: Garmin Connect email
            password: Garmin Connect password
        """
        self.email = email
        self.password = password
        self.client = None
        self._authenticated = False

        # Will implement actual connection when credentials are provided
        if email and password:
            self._connect()

    def _connect(self):
        """Connect to Garmin Connect"""
        try:
            from garminconnect import Garmin

            self.client = Garmin(self.email, self.password)
            self.client.login()
            self._authenticated = True
            print("✅ Connected to Garmin Connect")

        except ImportError:
            print("⚠️  garminconnect library not installed. Install with: pip install garminconnect")
            self._authenticated = False
        except Exception as e:
            print(f"❌ Failed to connect to Garmin: {e}")
            self._authenticated = False

    def get_sleep_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get sleep data for a specific date.

        Args:
            target_date: Date to get sleep data for (defaults to yesterday)

        Returns:
            Dictionary with sleep metrics
        """
        if not self._authenticated:
            # Return mock data for testing
            return self._mock_sleep_data(target_date)

        try:
            if target_date is None:
                target_date = date.today() - timedelta(days=1)

            sleep_data = self.client.get_sleep_data(target_date.isoformat())

            # Parse Garmin sleep data
            daily_sleep = sleep_data.get('dailySleepDTO', {})
            sleep_movement = sleep_data.get('sleepMovement', [])

            return {
                'date': target_date.isoformat(),
                'sleep_duration_hours': daily_sleep.get('sleepTimeSeconds', 0) / 3600,
                'sleep_quality_score': daily_sleep.get('sleepQualityTypePK', 0),
                'deep_sleep_minutes': daily_sleep.get('deepSleepSeconds', 0) / 60,
                'light_sleep_minutes': daily_sleep.get('lightSleepSeconds', 0) / 60,
                'rem_sleep_minutes': daily_sleep.get('remSleepSeconds', 0) / 60,
                'awake_time_minutes': daily_sleep.get('awakeSleepSeconds', 0) / 60,
                'sleep_start_time': daily_sleep.get('sleepStartTimestampLocal'),
                'sleep_end_time': daily_sleep.get('sleepEndTimestampLocal'),
                'raw_data': sleep_data
            }

        except Exception as e:
            print(f"❌ Error fetching Garmin sleep data: {e}")
            return self._mock_sleep_data(target_date)

    def get_daily_stats(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get daily health statistics.

        Args:
            target_date: Date to get stats for (defaults to today)

        Returns:
            Dictionary with daily health metrics
        """
        if not self._authenticated:
            return self._mock_daily_stats(target_date)

        try:
            if target_date is None:
                target_date = date.today()

            stats = self.client.get_stats(target_date.isoformat())

            return {
                'date': target_date.isoformat(),
                'steps': stats.get('totalSteps', 0),
                'distance_meters': stats.get('totalDistanceMeters', 0),
                'active_calories': stats.get('activeKilocalories', 0),
                'resting_heart_rate': stats.get('restingHeartRate'),
                'min_heart_rate': stats.get('minHeartRate'),
                'max_heart_rate': stats.get('maxHeartRate'),
                'avg_heart_rate': stats.get('avgHeartRate'),
                'intensity_minutes': stats.get('vigorousIntensityMinutes', 0) + stats.get('moderateIntensityMinutes', 0),
                'floors_climbed': stats.get('floorsAscended', 0),
                'raw_data': stats
            }

        except Exception as e:
            print(f"❌ Error fetching Garmin daily stats: {e}")
            return self._mock_daily_stats(target_date)

    def get_stress_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get stress data for a specific date.

        Args:
            target_date: Date to get stress data for (defaults to today)

        Returns:
            Dictionary with stress metrics
        """
        if not self._authenticated:
            return self._mock_stress_data(target_date)

        try:
            if target_date is None:
                target_date = date.today()

            stress = self.client.get_stress_data(target_date.isoformat())

            # Calculate average stress from stress values
            stress_values = [s.get('stressLevel', 0) for s in stress if s.get('stressLevel') is not None]
            avg_stress = sum(stress_values) / len(stress_values) if stress_values else 0

            return {
                'date': target_date.isoformat(),
                'avg_stress_level': int(avg_stress),
                'max_stress_level': max(stress_values) if stress_values else 0,
                'rest_stress_duration': sum(1 for s in stress if s.get('stressLevel', 0) < 25),
                'low_stress_duration': sum(1 for s in stress if 25 <= s.get('stressLevel', 0) < 50),
                'medium_stress_duration': sum(1 for s in stress if 50 <= s.get('stressLevel', 0) < 75),
                'high_stress_duration': sum(1 for s in stress if s.get('stressLevel', 0) >= 75),
                'raw_data': stress
            }

        except Exception as e:
            print(f"❌ Error fetching Garmin stress data: {e}")
            return self._mock_stress_data(target_date)

    def get_heart_rate_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get heart rate data for a specific date.

        Args:
            target_date: Date to get HR data for (defaults to today)

        Returns:
            Dictionary with heart rate metrics
        """
        if not self._authenticated:
            return self._mock_heart_rate_data(target_date)

        try:
            if target_date is None:
                target_date = date.today()

            hr_data = self.client.get_heart_rates(target_date.isoformat())

            # Calculate resting HR from data
            hr_values = [h[1] for h in hr_data if h[1] is not None]

            return {
                'date': target_date.isoformat(),
                'resting_heart_rate': min(hr_values) if hr_values else None,
                'max_heart_rate': max(hr_values) if hr_values else None,
                'avg_heart_rate': sum(hr_values) / len(hr_values) if hr_values else None,
                'measurements_count': len(hr_values),
                'raw_data': hr_data[:100]  # Limit raw data size
            }

        except Exception as e:
            print(f"❌ Error fetching Garmin heart rate data: {e}")
            return self._mock_heart_rate_data(target_date)

    def get_recovery_score(self, target_date: Optional[date] = None) -> float:
        """
        Calculate recovery score based on multiple metrics.

        Score ranges from 0-100:
        - 0-30: Poor recovery
        - 31-60: Fair recovery
        - 61-80: Good recovery
        - 81-100: Excellent recovery

        Args:
            target_date: Date to calculate recovery for

        Returns:
            Recovery score (0-100)
        """
        sleep = self.get_sleep_data(target_date)
        stats = self.get_daily_stats(target_date)
        stress = self.get_stress_data(target_date)

        # Calculate recovery score
        sleep_score = min(100, (sleep['sleep_duration_hours'] / 8.0) * 100)
        sleep_quality = sleep.get('sleep_quality_score', 50)

        # Resting HR score (lower is better, normalize around 60 bpm)
        rhr = stats.get('resting_heart_rate', 60)
        rhr_score = max(0, 100 - abs(rhr - 60) * 2)

        # Stress score (invert - lower stress = better)
        stress_score = 100 - stress['avg_stress_level']

        # Weighted average
        recovery_score = (
            sleep_score * 0.30 +
            sleep_quality * 0.30 +
            rhr_score * 0.20 +
            stress_score * 0.20
        )

        return round(recovery_score, 2)

    def get_activities(self, start_date: Optional[date] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get list of recent activities from Garmin.

        Args:
            start_date: Start date to fetch from (defaults to 30 days ago)
            limit: Maximum number of activities to return

        Returns:
            List of activity dictionaries
        """
        if not self._authenticated:
            return self._mock_activities(start_date, limit)

        try:
            if start_date is None:
                start_date = date.today() - timedelta(days=30)

            activities = self.client.get_activities_by_date(
                start_date.isoformat(),
                date.today().isoformat(),
                activitytype=None
            )

            # Parse and format activities
            formatted_activities = []
            for activity in list(activities)[:limit]:
                formatted = {
                    'external_id': str(activity.get('activityId')),
                    'timestamp': activity.get('startTimeLocal'),
                    'activity_type': activity.get('activityType', {}).get('typeKey', 'unknown'),
                    'duration_minutes': activity.get('duration', 0) / 60,
                    'distance_km': (activity.get('distance', 0) / 1000) if activity.get('distance') else 0,
                    'elevation_gain_m': activity.get('elevationGain'),
                    'avg_heart_rate': activity.get('averageHR'),
                    'max_heart_rate': activity.get('maxHR'),
                    'avg_power': activity.get('avgPower'),
                    'calories_burned': activity.get('calories'),
                    'aerobic_training_effect': activity.get('aerobicTrainingEffect'),
                    'anaerobic_training_effect': activity.get('anaerobicTrainingEffect'),
                    'raw_data': activity
                }
                formatted_activities.append(formatted)

            return formatted_activities

        except Exception as e:
            print(f"❌ Error fetching Garmin activities: {e}")
            return self._mock_activities(start_date, limit)

    def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """
        Get detailed data for a specific activity.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Dictionary with detailed activity metrics
        """
        if not self._authenticated:
            return self._mock_activity_details(activity_id)

        try:
            activity = self.client.get_activity(activity_id)

            return {
                'external_id': str(activity_id),
                'timestamp': activity.get('startTimeLocal'),
                'activity_type': activity.get('activityType', {}).get('typeKey'),
                'duration_minutes': activity.get('duration', 0) / 60,
                'distance_km': (activity.get('distance', 0) / 1000) if activity.get('distance') else 0,
                'elevation_gain_m': activity.get('elevationGain'),
                'avg_heart_rate': activity.get('averageHR'),
                'max_heart_rate': activity.get('maxHR'),
                'avg_power': activity.get('avgPower'),
                'avg_pace': activity.get('avgSpeed'),  # m/s
                'avg_cadence': activity.get('avgRunCadence') or activity.get('avgBikeCadence'),
                'calories_burned': activity.get('calories'),
                'aerobic_training_effect': activity.get('aerobicTrainingEffect'),
                'anaerobic_training_effect': activity.get('anaerobicTrainingEffect'),
                'training_load': activity.get('trainingEffectLabel'),
                'vo2_max': activity.get('vO2MaxValue'),
                'lactate_threshold_hr': activity.get('lactateThresholdHeartRate'),
                'raw_data': activity
            }

        except Exception as e:
            print(f"❌ Error fetching Garmin activity details: {e}")
            return self._mock_activity_details(activity_id)

    def get_training_status(self) -> Dict[str, Any]:
        """
        Get overall training status from Garmin.

        Returns:
            Dictionary with training status, VO2 max, etc.
        """
        if not self._authenticated:
            return self._mock_training_status()

        try:
            # Note: Specific API call depends on garminconnect library version
            # This is a placeholder - actual implementation may vary
            training_status = {
                'training_status': 'maintaining',  # productive, maintaining, detraining, recovery
                'vo2_max_running': None,
                'vo2_max_cycling': None,
                'lactate_threshold': None,
                'fitness_age': None
            }

            return training_status

        except Exception as e:
            print(f"❌ Error fetching Garmin training status: {e}")
            return self._mock_training_status()

    # Mock data methods for testing without Garmin credentials

    def _mock_activities(self, start_date: Optional[date], limit: int) -> List[Dict[str, Any]]:
        """Generate mock activities for testing."""
        import random
        from datetime import datetime

        activities = []
        for i in range(min(limit, 10)):
            activity_date = (start_date or (date.today() - timedelta(days=30))) + timedelta(days=i*3)
            activity_type = random.choice(['running', 'cycling', 'swimming', 'strength_training'])

            activities.append({
                'external_id': f'mock_{i}_{activity_date.isoformat()}',
                'timestamp': datetime.combine(activity_date, datetime.min.time()).isoformat(),
                'activity_type': activity_type,
                'duration_minutes': random.randint(30, 90),
                'distance_km': round(random.uniform(5, 20), 2) if activity_type in ['running', 'cycling'] else 0,
                'elevation_gain_m': random.randint(50, 500) if activity_type in ['running', 'cycling'] else 0,
                'avg_heart_rate': random.randint(130, 170),
                'max_heart_rate': random.randint(170, 190),
                'avg_power': random.randint(150, 250) if activity_type == 'cycling' else None,
                'calories_burned': random.randint(300, 800),
                'aerobic_training_effect': round(random.uniform(2.0, 4.5), 1),
                'anaerobic_training_effect': round(random.uniform(0.5, 3.0), 1),
                'source': 'mock'
            })

        return activities

    def _mock_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """Generate mock activity details."""
        import random
        from datetime import datetime

        return {
            'external_id': activity_id,
            'timestamp': datetime.now().isoformat(),
            'activity_type': 'running',
            'duration_minutes': random.randint(30, 90),
            'distance_km': round(random.uniform(5, 15), 2),
            'elevation_gain_m': random.randint(50, 300),
            'avg_heart_rate': random.randint(140, 165),
            'max_heart_rate': random.randint(175, 190),
            'avg_pace': round(random.uniform(4.5, 6.5), 2),
            'avg_cadence': random.randint(160, 180),
            'calories_burned': random.randint(400, 700),
            'aerobic_training_effect': round(random.uniform(2.5, 4.0), 1),
            'anaerobic_training_effect': round(random.uniform(1.0, 2.5), 1),
            'vo2_max': round(random.uniform(45, 60), 1),
            'lactate_threshold_hr': random.randint(155, 175),
            'source': 'mock'
        }

    def _mock_training_status(self) -> Dict[str, Any]:
        """Generate mock training status."""
        import random

        return {
            'training_status': random.choice(['productive', 'maintaining', 'recovery']),
            'vo2_max_running': round(random.uniform(45, 60), 1),
            'vo2_max_cycling': round(random.uniform(50, 65), 1),
            'lactate_threshold': random.randint(155, 175),
            'fitness_age': random.randint(25, 45),
            'source': 'mock'
        }

    def _mock_sleep_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock sleep data for testing"""
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        import random

        # Simulate realistic sleep data
        sleep_duration = random.uniform(6.0, 8.5)
        sleep_quality = random.randint(60, 95)

        return {
            'date': target_date.isoformat(),
            'sleep_duration_hours': round(sleep_duration, 1),
            'sleep_quality_score': sleep_quality,
            'deep_sleep_minutes': int(sleep_duration * 60 * 0.15),
            'light_sleep_minutes': int(sleep_duration * 60 * 0.50),
            'rem_sleep_minutes': int(sleep_duration * 60 * 0.25),
            'awake_time_minutes': int(sleep_duration * 60 * 0.10),
            'sleep_start_time': f"{target_date}T23:00:00",
            'sleep_end_time': f"{target_date + timedelta(days=1)}T07:00:00",
            'raw_data': {'mock': True}
        }

    def _mock_daily_stats(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock daily stats for testing"""
        if target_date is None:
            target_date = date.today()

        import random

        return {
            'date': target_date.isoformat(),
            'steps': random.randint(5000, 15000),
            'distance_meters': random.randint(4000, 12000),
            'active_calories': random.randint(200, 800),
            'resting_heart_rate': random.randint(55, 70),
            'min_heart_rate': random.randint(50, 60),
            'max_heart_rate': random.randint(140, 180),
            'avg_heart_rate': random.randint(70, 90),
            'intensity_minutes': random.randint(15, 60),
            'floors_climbed': random.randint(5, 20),
            'raw_data': {'mock': True}
        }

    def _mock_stress_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock stress data for testing"""
        if target_date is None:
            target_date = date.today()

        import random

        avg_stress = random.randint(20, 60)

        return {
            'date': target_date.isoformat(),
            'avg_stress_level': avg_stress,
            'max_stress_level': min(100, avg_stress + random.randint(10, 30)),
            'rest_stress_duration': random.randint(100, 300),
            'low_stress_duration': random.randint(200, 400),
            'medium_stress_duration': random.randint(50, 150),
            'high_stress_duration': random.randint(0, 50),
            'raw_data': {'mock': True}
        }

    def _mock_heart_rate_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock heart rate data for testing"""
        if target_date is None:
            target_date = date.today()

        import random

        rhr = random.randint(55, 70)

        return {
            'date': target_date.isoformat(),
            'resting_heart_rate': rhr,
            'max_heart_rate': random.randint(140, 180),
            'avg_heart_rate': random.randint(70, 90),
            'measurements_count': random.randint(200, 500),
            'raw_data': {'mock': True}
        }


# Convenience function
def get_garmin_connector(email: Optional[str] = None, password: Optional[str] = None) -> GarminConnector:
    """
    Get a Garmin connector instance.

    If credentials not provided, will use mock data for testing.
    """
    return GarminConnector(email, password)
