"""
Garmin Connect API integration for health data
Uses the unofficial garminconnect library
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# DATA PRIORITY LEVELS
# =============================================================================
# Priority determines what data to include in LLM prompts
# Higher priority = more impact on workout decisions

DATA_PRIORITY = {
    # 🔴 CRITICAL (Priority 1) - Always include, directly affects today's workout
    'training_readiness': 1,       # get_training_readiness() - Garmin's readiness score
    'recovery_score': 1,           # get_recovery_score() - our calculated recovery
    'sleep': 1,                    # get_sleep_data() - duration, quality, stages
    'hrv': 1,                      # get_hrv_data() - heart rate variability
    'body_battery': 1,             # get_body_battery() - energy level
    'recent_activities': 1,        # get_activities() - list of recent workouts
    'activity_details': 1,         # get_activity_details() - basic activity info
    'activity_exercise_sets': 1,   # get_activity_exercise_sets() - strength sets/reps/weights
    'activity_splits': 1,          # get_activity_splits() - cardio lap/split data

    # 🟡 IMPORTANT (Priority 2) - Include when available, useful context
    'training_load_balance': 2,    # get_training_load_balance() - acute vs chronic load
    'training_status': 2,          # get_training_status() - productive/maintaining/detraining
    'stress': 2,                   # get_stress_data() - stress levels throughout day
    'heart_rate': 2,               # get_heart_rate_data() - HR throughout day
    'activity_hr_zones': 2,        # get_activity_hr_zones() - time in each HR zone
    'daily_stats': 2,              # get_daily_stats() - steps, calories, intensity mins

    # 🟢 SECONDARY (Priority 3) - Include if space allows
    'race_predictions': 3,         # get_race_predictions() - 5K, 10K, HM, marathon times
    'personal_records': 3,         # get_personal_records() - PRs
    'gear_stats': 3,               # get_gear_stats() - all gear with usage stats
    'activity_gear': 3,            # get_activity_gear() - gear used for specific activity
    'activity_weather': 3,         # get_activity_weather() - weather during activity
    'body_composition': 3,         # get_body_composition() - weight, body fat, muscle
    'fitness_age': 3,              # get_fitness_age() - calculated fitness age

    # ⚪ LOW (Priority 4) - Skip unless specifically relevant
    'spo2': 4,                     # get_spo2_data() - blood oxygen
    'respiration': 4,              # get_respiration_data() - breathing rate
    'hydration': 4,                # get_hydration_data() - water intake
    'challenges': 4,               # get_adhoc_challenges() - badges/challenges
    'goals': 4,                    # get_goals() - Garmin goals (not our app goals)
}

def get_data_priority(data_type: str) -> int:
    """Get priority level for a data type. Lower = more important."""
    return DATA_PRIORITY.get(data_type, 5)  # Default to lowest priority


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
            email: Garmin Connect email (defaults to GARMIN_EMAIL env var)
            password: Garmin Connect password (defaults to GARMIN_PASSWORD env var)
        """
        # Check environment variables if not provided
        self.email = email or os.getenv('GARMIN_EMAIL')
        self.password = password or os.getenv('GARMIN_PASSWORD')
        self.client = None
        self._authenticated = False

        # Connect if credentials are available
        if self.email and self.password:
            self._connect()
        else:
            print("ℹ️  No Garmin credentials found - using mock data")
            print("   To connect: Add GARMIN_EMAIL and GARMIN_PASSWORD to .env")

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

            # Parse Garmin sleep data with null safety
            daily_sleep = sleep_data.get('dailySleepDTO', {}) if isinstance(sleep_data, dict) else {}

            # Helper to safely convert seconds to hours/minutes
            def safe_divide(value, divisor):
                return value / divisor if value is not None else None

            return {
                'date': target_date.isoformat(),
                'sleep_duration_hours': safe_divide(daily_sleep.get('sleepTimeSeconds'), 3600),
                'sleep_quality_score': daily_sleep.get('sleepQualityTypePK'),
                'deep_sleep_minutes': safe_divide(daily_sleep.get('deepSleepSeconds'), 60),
                'light_sleep_minutes': safe_divide(daily_sleep.get('lightSleepSeconds'), 60),
                'rem_sleep_minutes': safe_divide(daily_sleep.get('remSleepSeconds'), 60),
                'awake_time_minutes': safe_divide(daily_sleep.get('awakeSleepSeconds'), 60),
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

            # Handle different stress data formats
            if isinstance(stress, str) or stress is None or not stress:
                # No stress data available or invalid format
                return {
                    'date': target_date.isoformat(),
                    'avg_stress_level': None,
                    'max_stress_level': None,
                    'rest_stress_duration': None,
                    'low_stress_duration': None,
                    'medium_stress_duration': None,
                    'high_stress_duration': None,
                    'raw_data': stress
                }

            # Calculate average stress from stress values
            stress_values = []
            if isinstance(stress, list):
                stress_values = [s.get('stressLevel', 0) for s in stress if isinstance(s, dict) and s.get('stressLevel') is not None]

            avg_stress = sum(stress_values) / len(stress_values) if stress_values else None

            return {
                'date': target_date.isoformat(),
                'avg_stress_level': int(avg_stress) if avg_stress is not None else None,
                'max_stress_level': max(stress_values) if stress_values else None,
                'rest_stress_duration': sum(1 for s in stress if isinstance(s, dict) and s.get('stressLevel', 0) < 25),
                'low_stress_duration': sum(1 for s in stress if isinstance(s, dict) and 25 <= s.get('stressLevel', 0) < 50),
                'medium_stress_duration': sum(1 for s in stress if isinstance(s, dict) and 50 <= s.get('stressLevel', 0) < 75),
                'high_stress_duration': sum(1 for s in stress if isinstance(s, dict) and s.get('stressLevel', 0) >= 75),
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

        # Calculate recovery score with null safety
        sleep_hours = sleep.get('sleep_duration_hours')
        sleep_score = min(100, (sleep_hours / 8.0) * 100) if sleep_hours is not None else 50
        sleep_quality = sleep.get('sleep_quality_score') or 50

        # Resting HR score (lower is better, normalize around 60 bpm)
        rhr = stats.get('resting_heart_rate') or 60
        rhr_score = max(0, 100 - abs(rhr - 60) * 2)

        # Stress score (invert - lower stress = better)
        avg_stress = stress.get('avg_stress_level')
        stress_score = 100 - avg_stress if avg_stress is not None else 50

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

    # =========================================================================
    # DETAILED ACTIVITY DATA METHODS
    # =========================================================================

    def get_activity_splits(self, activity_id: str) -> Dict[str, Any]:
        """
        Get split/lap data for an activity (running, cycling).

        Returns per-lap: pace, HR, distance, elevation, cadence.
        """
        if not self._authenticated:
            return {'activity_id': activity_id, 'splits': [], 'source': 'mock'}

        try:
            splits = self.client.get_activity_splits(activity_id)
            return {
                'activity_id': activity_id,
                'splits': splits,
                'raw_data': splits
            }
        except Exception as e:
            print(f"❌ Error fetching activity splits: {e}")
            return {'activity_id': activity_id, 'splits': [], 'error': str(e)}

    def get_activity_exercise_sets(self, activity_id: str) -> Dict[str, Any]:
        """
        Get strength training exercise sets for an activity.

        Returns: exercises with sets, reps, weight for each.
        """
        if not self._authenticated:
            return {'activity_id': activity_id, 'exercises': [], 'source': 'mock'}

        try:
            sets_data = self.client.get_activity_exercise_sets(activity_id)
            return {
                'activity_id': activity_id,
                'exercises': sets_data,
                'raw_data': sets_data
            }
        except Exception as e:
            print(f"❌ Error fetching exercise sets: {e}")
            return {'activity_id': activity_id, 'exercises': [], 'error': str(e)}

    def get_activity_hr_zones(self, activity_id: str) -> Dict[str, Any]:
        """
        Get heart rate zone distribution for an activity.

        Returns time spent in each HR zone (1-5).
        """
        if not self._authenticated:
            return {'activity_id': activity_id, 'hr_zones': [], 'source': 'mock'}

        try:
            hr_zones = self.client.get_activity_hr_in_timezones(activity_id)
            return {
                'activity_id': activity_id,
                'hr_zones': hr_zones,
                'raw_data': hr_zones
            }
        except Exception as e:
            print(f"❌ Error fetching HR zones: {e}")
            return {'activity_id': activity_id, 'hr_zones': [], 'error': str(e)}

    def get_activity_weather(self, activity_id: str) -> Dict[str, Any]:
        """
        Get weather conditions during an activity.
        """
        if not self._authenticated:
            return {'activity_id': activity_id, 'weather': None, 'source': 'mock'}

        try:
            weather = self.client.get_activity_weather(activity_id)
            return {
                'activity_id': activity_id,
                'weather': weather,
                'raw_data': weather
            }
        except Exception as e:
            print(f"❌ Error fetching activity weather: {e}")
            return {'activity_id': activity_id, 'weather': None, 'error': str(e)}

    def get_activity_gear(self, activity_id: str) -> Dict[str, Any]:
        """
        Get gear/equipment used for an activity (shoes, bike, etc.).
        """
        if not self._authenticated:
            return {'activity_id': activity_id, 'gear': None, 'source': 'mock'}

        try:
            gear = self.client.get_activity_gear(activity_id)
            return {
                'activity_id': activity_id,
                'gear': gear,
                'raw_data': gear
            }
        except Exception as e:
            print(f"❌ Error fetching activity gear: {e}")
            return {'activity_id': activity_id, 'gear': None, 'error': str(e)}

    # =========================================================================
    # BODY COMPOSITION & WELLNESS
    # =========================================================================

    def get_body_composition(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get body composition data (weight, body fat, muscle mass, etc.).
        """
        if not self._authenticated:
            return self._mock_body_composition(target_date)

        try:
            if target_date is None:
                target_date = date.today()

            # Get weight data
            end_date = target_date
            start_date = target_date - timedelta(days=30)

            body_comp = self.client.get_body_composition(start_date.isoformat(), end_date.isoformat())

            return {
                'date': target_date.isoformat(),
                'body_composition': body_comp,
                'raw_data': body_comp
            }
        except Exception as e:
            print(f"❌ Error fetching body composition: {e}")
            return self._mock_body_composition(target_date)

    def get_body_battery(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get Body Battery (energy level) data for a specific date.
        """
        if not self._authenticated:
            return self._mock_body_battery(target_date)

        try:
            if target_date is None:
                target_date = date.today()

            body_battery = self.client.get_body_battery(target_date.isoformat())

            # Extract key metrics
            charged = 0
            drained = 0
            current_level = None

            if isinstance(body_battery, list) and body_battery:
                values = [b.get('bodyBatteryLevel') for b in body_battery if b.get('bodyBatteryLevel')]
                if values:
                    current_level = values[-1]  # Most recent
                    charged = max(values) - min(values) if len(values) > 1 else 0

            return {
                'date': target_date.isoformat(),
                'current_level': current_level,
                'charged': charged,
                'drained': drained,
                'raw_data': body_battery
            }
        except Exception as e:
            print(f"❌ Error fetching body battery: {e}")
            return self._mock_body_battery(target_date)

    def get_hrv_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get Heart Rate Variability (HRV) data.

        HRV is a key recovery indicator.
        """
        if not self._authenticated:
            return self._mock_hrv_data(target_date)

        try:
            if target_date is None:
                target_date = date.today()

            hrv = self.client.get_hrv_data(target_date.isoformat())

            return {
                'date': target_date.isoformat(),
                'hrv_data': hrv,
                'raw_data': hrv
            }
        except Exception as e:
            print(f"❌ Error fetching HRV data: {e}")
            return self._mock_hrv_data(target_date)

    def get_respiration_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get respiration rate data.
        """
        if not self._authenticated:
            return {'date': target_date.isoformat() if target_date else date.today().isoformat(), 'respiration': None, 'source': 'mock'}

        try:
            if target_date is None:
                target_date = date.today()

            resp = self.client.get_respiration_data(target_date.isoformat())

            return {
                'date': target_date.isoformat(),
                'respiration': resp,
                'raw_data': resp
            }
        except Exception as e:
            print(f"❌ Error fetching respiration data: {e}")
            return {'date': target_date.isoformat(), 'respiration': None, 'error': str(e)}

    def get_spo2_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get blood oxygen (SpO2) data.
        """
        if not self._authenticated:
            return {'date': target_date.isoformat() if target_date else date.today().isoformat(), 'spo2': None, 'source': 'mock'}

        try:
            if target_date is None:
                target_date = date.today()

            spo2 = self.client.get_spo2_data(target_date.isoformat())

            return {
                'date': target_date.isoformat(),
                'spo2': spo2,
                'raw_data': spo2
            }
        except Exception as e:
            print(f"❌ Error fetching SpO2 data: {e}")
            return {'date': target_date.isoformat(), 'spo2': None, 'error': str(e)}

    def get_hydration_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get hydration tracking data.
        """
        if not self._authenticated:
            return {'date': target_date.isoformat() if target_date else date.today().isoformat(), 'hydration': None, 'source': 'mock'}

        try:
            if target_date is None:
                target_date = date.today()

            hydration = self.client.get_hydration_data(target_date.isoformat())

            return {
                'date': target_date.isoformat(),
                'hydration': hydration,
                'raw_data': hydration
            }
        except Exception as e:
            print(f"❌ Error fetching hydration data: {e}")
            return {'date': target_date.isoformat(), 'hydration': None, 'error': str(e)}

    # =========================================================================
    # TRAINING & PERFORMANCE METRICS
    # =========================================================================

    def get_training_readiness(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get Training Readiness score (newer Garmin metric).

        Combines sleep, recovery, HRV, training load into readiness score.
        """
        if not self._authenticated:
            return {'date': target_date.isoformat() if target_date else date.today().isoformat(), 'readiness': None, 'source': 'mock'}

        try:
            if target_date is None:
                target_date = date.today()

            readiness = self.client.get_training_readiness(target_date.isoformat())

            return {
                'date': target_date.isoformat(),
                'readiness': readiness,
                'raw_data': readiness
            }
        except Exception as e:
            print(f"❌ Error fetching training readiness: {e}")
            return {'date': target_date.isoformat(), 'readiness': None, 'error': str(e)}

    def get_training_load_balance(self) -> Dict[str, Any]:
        """
        Get training load balance (acute vs chronic load).
        """
        if not self._authenticated:
            return {'load_balance': None, 'source': 'mock'}

        try:
            load = self.client.get_training_status()

            return {
                'load_balance': load,
                'raw_data': load
            }
        except Exception as e:
            print(f"❌ Error fetching training load balance: {e}")
            return {'load_balance': None, 'error': str(e)}

    def get_race_predictions(self) -> Dict[str, Any]:
        """
        Get race time predictions (5K, 10K, half marathon, marathon).
        """
        if not self._authenticated:
            return {'predictions': None, 'source': 'mock'}

        try:
            predictions = self.client.get_race_predictions()

            return {
                'predictions': predictions,
                'raw_data': predictions
            }
        except Exception as e:
            print(f"❌ Error fetching race predictions: {e}")
            return {'predictions': None, 'error': str(e)}

    def get_personal_records(self) -> Dict[str, Any]:
        """
        Get personal records (PRs) for various activities.
        """
        if not self._authenticated:
            return {'records': None, 'source': 'mock'}

        try:
            records = self.client.get_personal_record()

            return {
                'records': records,
                'raw_data': records
            }
        except Exception as e:
            print(f"❌ Error fetching personal records: {e}")
            return {'records': None, 'error': str(e)}

    def get_fitness_age(self) -> Dict[str, Any]:
        """
        Get fitness age calculation from Garmin.
        """
        if not self._authenticated:
            return {'fitness_age': None, 'source': 'mock'}

        try:
            # This may be part of user profile or stats
            stats = self.client.get_user_summary(date.today().isoformat())

            return {
                'fitness_age': stats.get('fitnessAge'),
                'raw_data': stats
            }
        except Exception as e:
            print(f"❌ Error fetching fitness age: {e}")
            return {'fitness_age': None, 'error': str(e)}

    # =========================================================================
    # WORKOUT PROGRAMS & GOALS
    # =========================================================================

    def get_goals(self) -> Dict[str, Any]:
        """
        Get user's fitness goals set in Garmin Connect.
        """
        if not self._authenticated:
            return {'goals': None, 'source': 'mock'}

        try:
            goals = self.client.get_goals()

            return {
                'goals': goals,
                'raw_data': goals
            }
        except Exception as e:
            print(f"❌ Error fetching goals: {e}")
            return {'goals': None, 'error': str(e)}

    def get_adhoc_challenges(self) -> Dict[str, Any]:
        """
        Get active challenges and badges.
        """
        if not self._authenticated:
            return {'challenges': None, 'source': 'mock'}

        try:
            challenges = self.client.get_adhoc_challenges()

            return {
                'challenges': challenges,
                'raw_data': challenges
            }
        except Exception as e:
            print(f"❌ Error fetching challenges: {e}")
            return {'challenges': None, 'error': str(e)}

    def get_gear_stats(self) -> Dict[str, Any]:
        """
        Get all gear/equipment with usage stats (shoe mileage, etc.).
        """
        if not self._authenticated:
            return {'gear': None, 'source': 'mock'}

        try:
            gear = self.client.get_gear_stats()

            return {
                'gear': gear,
                'raw_data': gear
            }
        except Exception as e:
            print(f"❌ Error fetching gear stats: {e}")
            return {'gear': None, 'error': str(e)}

    # =========================================================================
    # COMPREHENSIVE DATA PULL
    # =========================================================================

    def get_full_day_summary(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get ALL available data for a single day.

        Comprehensive pull for LLM context.
        """
        if target_date is None:
            target_date = date.today()

        return {
            'date': target_date.isoformat(),
            'sleep': self.get_sleep_data(target_date),
            'daily_stats': self.get_daily_stats(target_date),
            'stress': self.get_stress_data(target_date),
            'heart_rate': self.get_heart_rate_data(target_date),
            'body_battery': self.get_body_battery(target_date),
            'hrv': self.get_hrv_data(target_date),
            'recovery_score': self.get_recovery_score(target_date),
            'training_readiness': self.get_training_readiness(target_date),
            'respiration': self.get_respiration_data(target_date),
            'spo2': self.get_spo2_data(target_date),
            'hydration': self.get_hydration_data(target_date),
        }

    def get_full_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """
        Get ALL available data for a single activity.

        Comprehensive pull including splits, HR zones, sets, weather, gear.
        """
        basic = self.get_activity_details(activity_id)

        return {
            'basic': basic,
            'splits': self.get_activity_splits(activity_id),
            'hr_zones': self.get_activity_hr_zones(activity_id),
            'exercise_sets': self.get_activity_exercise_sets(activity_id),
            'weather': self.get_activity_weather(activity_id),
            'gear': self.get_activity_gear(activity_id),
        }

    def get_training_context(self) -> Dict[str, Any]:
        """
        Get overall training context for planning.

        Includes training status, load, predictions, PRs, goals.
        """
        return {
            'training_status': self.get_training_status(),
            'load_balance': self.get_training_load_balance(),
            'race_predictions': self.get_race_predictions(),
            'personal_records': self.get_personal_records(),
            'fitness_age': self.get_fitness_age(),
            'goals': self.get_goals(),
            'gear': self.get_gear_stats(),
        }

    # =========================================================================
    # ADDITIONAL MOCK DATA METHODS
    # =========================================================================

    def _mock_body_composition(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock body composition data."""
        import random
        if target_date is None:
            target_date = date.today()

        return {
            'date': target_date.isoformat(),
            'weight_kg': round(random.uniform(70, 85), 1),
            'body_fat_percent': round(random.uniform(12, 20), 1),
            'muscle_mass_kg': round(random.uniform(55, 70), 1),
            'bone_mass_kg': round(random.uniform(2.5, 3.5), 1),
            'body_water_percent': round(random.uniform(55, 65), 1),
            'bmi': round(random.uniform(22, 27), 1),
            'source': 'mock'
        }

    def _mock_body_battery(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock body battery data."""
        import random
        if target_date is None:
            target_date = date.today()

        return {
            'date': target_date.isoformat(),
            'current_level': random.randint(30, 90),
            'charged': random.randint(20, 60),
            'drained': random.randint(20, 50),
            'source': 'mock'
        }

    def _mock_hrv_data(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate mock HRV data."""
        import random
        if target_date is None:
            target_date = date.today()

        return {
            'date': target_date.isoformat(),
            'hrv_weekly_avg': random.randint(40, 80),
            'hrv_last_night': random.randint(35, 85),
            'hrv_status': random.choice(['balanced', 'low', 'high']),
            'source': 'mock'
        }

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
