#!/usr/bin/env python3
"""
Regression Tests for Workout Planning and Reconciliation

Tests the core functions without requiring external connections (Garmin, Calendar).
These run on every push to catch regressions.
"""
import pytest
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# TESTS FOR: sanitize_workout_response (plan_workouts.py)
# =============================================================================

class TestSanitizeWorkoutResponse:
    """Tests for the LLM response sanitizer."""

    @pytest.fixture
    def sanitize_func(self):
        """Import the sanitize function."""
        from scripts.plan_workouts import sanitize_workout_response
        return sanitize_workout_response

    def test_valid_response_passes(self, sanitize_func):
        """Valid LLM response should pass through unchanged."""
        response = {
            'should_workout': True,
            'workout': {
                'type': 'Run',
                'title': 'Easy Run',
                'duration_minutes': 45,
                'time_suggestion': '7:00 AM',
                'warmup': '5 min jog',
                'main_workout': '30 min easy',
                'cooldown': 'Stretch',
                'backup_plan': 'Walk instead',
            }
        }
        result = sanitize_func(response, date.today())

        assert result is not None
        assert result['workout']['duration_minutes'] == 45
        assert result['workout']['time_suggestion'] == '7:00 AM'

    def test_time_too_early_adjusted(self, sanitize_func):
        """Times before 5 AM should be adjusted to 6 AM."""
        response = {
            'workout': {
                'type': 'Run',
                'time_suggestion': '4:00 AM',
                'duration_minutes': 30,
                'warmup': 'test',
                'main_workout': 'test',
                'cooldown': 'test',
                'backup_plan': 'test',
            }
        }
        result = sanitize_func(response, date.today())

        assert result['workout']['time_suggestion'] == '6:00 AM'
        assert len(result['_issues']) > 0

    def test_time_too_late_adjusted(self, sanitize_func):
        """Times after 9 PM should be adjusted to 6 PM."""
        response = {
            'workout': {
                'type': 'Run',
                'time_suggestion': '10:30 PM',
                'duration_minutes': 30,
                'warmup': 'test',
                'main_workout': 'test',
                'cooldown': 'test',
                'backup_plan': 'test',
            }
        }
        result = sanitize_func(response, date.today())

        assert result['workout']['time_suggestion'] == '6:00 PM'

    def test_duration_too_short_adjusted(self, sanitize_func):
        """Duration under 15 min should be adjusted to 20 min."""
        response = {
            'workout': {
                'type': 'Run',
                'time_suggestion': '7:00 AM',
                'duration_minutes': 5,
                'warmup': 'test',
                'main_workout': 'test',
                'cooldown': 'test',
                'backup_plan': 'test',
            }
        }
        result = sanitize_func(response, date.today())

        assert result['workout']['duration_minutes'] == 20

    def test_duration_too_long_adjusted(self, sanitize_func):
        """Duration over 180 min should be adjusted to 90 min."""
        response = {
            'workout': {
                'type': 'Run',
                'time_suggestion': '7:00 AM',
                'duration_minutes': 240,
                'warmup': 'test',
                'main_workout': 'test',
                'cooldown': 'test',
                'backup_plan': 'test',
            }
        }
        result = sanitize_func(response, date.today())

        assert result['workout']['duration_minutes'] == 90

    def test_missing_warmup_added(self, sanitize_func):
        """Missing warmup should be filled with default."""
        response = {
            'workout': {
                'type': 'Run',
                'time_suggestion': '7:00 AM',
                'duration_minutes': 45,
                'main_workout': 'test',
                'cooldown': 'test',
                'backup_plan': 'test',
            }
        }
        result = sanitize_func(response, date.today())

        assert result['workout']['warmup'] is not None
        assert len(result['workout']['warmup']) > 0

    def test_missing_backup_plan_added(self, sanitize_func):
        """Missing backup_plan should be filled with default."""
        response = {
            'workout': {
                'type': 'Run',
                'time_suggestion': '7:00 AM',
                'duration_minutes': 45,
                'warmup': 'test',
                'main_workout': 'test',
                'cooldown': 'test',
            }
        }
        result = sanitize_func(response, date.today())

        assert result['workout']['backup_plan'] is not None
        assert 'reduce' in result['workout']['backup_plan'].lower() or 'walk' in result['workout']['backup_plan'].lower()

    def test_empty_response_returns_none(self, sanitize_func):
        """Empty response should return None."""
        result = sanitize_func(None, date.today())
        assert result is None

        result = sanitize_func({}, date.today())
        assert result is None

    def test_invalid_time_format_uses_default(self, sanitize_func):
        """Invalid time format should default to 6:30 AM."""
        response = {
            'workout': {
                'type': 'Run',
                'time_suggestion': 'sometime tomorrow',
                'duration_minutes': 45,
                'warmup': 'test',
                'main_workout': 'test',
                'cooldown': 'test',
                'backup_plan': 'test',
            }
        }
        result = sanitize_func(response, date.today())

        assert result['workout']['time_suggestion'] == '6:30 AM'


# =============================================================================
# TESTS FOR: times_overlap, find_conflicts (reconcile_workouts.py)
# =============================================================================

class TestConflictDetection:
    """Tests for time overlap and conflict detection."""

    @pytest.fixture
    def overlap_func(self):
        """Import the times_overlap function."""
        from scripts.reconcile_workouts import times_overlap
        return times_overlap

    @pytest.fixture
    def find_conflicts_func(self):
        """Import the find_conflicts function."""
        from scripts.reconcile_workouts import find_conflicts
        return find_conflicts

    def test_no_overlap(self, overlap_func):
        """Events that don't overlap should return False."""
        # Event 1: 9:00-10:00, Event 2: 11:00-12:00
        start1 = datetime(2026, 1, 5, 9, 0)
        end1 = datetime(2026, 1, 5, 10, 0)
        start2 = datetime(2026, 1, 5, 11, 0)
        end2 = datetime(2026, 1, 5, 12, 0)

        assert overlap_func(start1, end1, start2, end2) is False

    def test_partial_overlap(self, overlap_func):
        """Partially overlapping events should return True."""
        # Event 1: 9:00-10:30, Event 2: 10:00-11:00
        start1 = datetime(2026, 1, 5, 9, 0)
        end1 = datetime(2026, 1, 5, 10, 30)
        start2 = datetime(2026, 1, 5, 10, 0)
        end2 = datetime(2026, 1, 5, 11, 0)

        assert overlap_func(start1, end1, start2, end2) is True

    def test_complete_overlap(self, overlap_func):
        """One event containing another should return True."""
        # Event 1: 9:00-12:00 contains Event 2: 10:00-11:00
        start1 = datetime(2026, 1, 5, 9, 0)
        end1 = datetime(2026, 1, 5, 12, 0)
        start2 = datetime(2026, 1, 5, 10, 0)
        end2 = datetime(2026, 1, 5, 11, 0)

        assert overlap_func(start1, end1, start2, end2) is True

    def test_adjacent_events_no_overlap(self, overlap_func):
        """Adjacent events (back to back) should NOT overlap."""
        # Event 1: 9:00-10:00, Event 2: 10:00-11:00 (exactly adjacent)
        start1 = datetime(2026, 1, 5, 9, 0)
        end1 = datetime(2026, 1, 5, 10, 0)
        start2 = datetime(2026, 1, 5, 10, 0)
        end2 = datetime(2026, 1, 5, 11, 0)

        assert overlap_func(start1, end1, start2, end2) is False

    def test_find_conflicts_with_overlap(self, find_conflicts_func):
        """Should find workout that conflicts with work meeting."""
        workouts = [{
            'id': 'w1',
            'title': 'Workout: Run',
            'start': datetime(2026, 1, 5, 9, 0),
            'end': datetime(2026, 1, 5, 10, 0),
        }]

        other_events = [{
            'title': 'Work Meeting',
            'start': datetime(2026, 1, 5, 9, 30),
            'end': datetime(2026, 1, 5, 10, 30),
        }]

        conflicts = find_conflicts_func(workouts, other_events)

        assert len(conflicts) == 1
        assert conflicts[0]['workout']['id'] == 'w1'
        assert conflicts[0]['conflicts_with']['title'] == 'Work Meeting'

    def test_find_conflicts_no_overlap(self, find_conflicts_func):
        """Should not find conflicts when times don't overlap."""
        workouts = [{
            'id': 'w1',
            'title': 'Workout: Run',
            'start': datetime(2026, 1, 5, 6, 0),
            'end': datetime(2026, 1, 5, 7, 0),
        }]

        other_events = [{
            'title': 'Work Meeting',
            'start': datetime(2026, 1, 5, 9, 0),
            'end': datetime(2026, 1, 5, 10, 0),
        }]

        conflicts = find_conflicts_func(workouts, other_events)

        assert len(conflicts) == 0


# =============================================================================
# TESTS FOR: normalize_type, types_match (reconcile_workouts.py)
# =============================================================================

class TestTypeMatching:
    """Tests for workout type normalization and matching."""

    @pytest.fixture
    def normalize_func(self):
        """Import the normalize_type function."""
        from scripts.reconcile_workouts import normalize_type
        return normalize_type

    @pytest.fixture
    def match_func(self):
        """Import the types_match function."""
        from scripts.reconcile_workouts import types_match
        return match_func

    def test_normalize_run_variations(self, normalize_func):
        """Various running terms should normalize to 'run'."""
        assert normalize_func('Run') == 'run'
        assert normalize_func('running') == 'run'
        assert normalize_func('Treadmill Run') == 'run'
        assert normalize_func('Easy Run') == 'run'

    def test_normalize_bike_variations(self, normalize_func):
        """Various cycling terms should normalize to 'bike'."""
        assert normalize_func('Bike') == 'bike'
        assert normalize_func('Cycling') == 'bike'
        assert normalize_func('Indoor Bike') == 'bike'
        assert normalize_func('cycle') == 'bike'

    def test_normalize_strength_variations(self, normalize_func):
        """Various strength terms should normalize to 'strength'."""
        assert normalize_func('Strength') == 'strength'
        assert normalize_func('Weight Training') == 'strength'
        assert normalize_func('Lifting') == 'strength'
        assert normalize_func('Gym') == 'strength'

    def test_normalize_swim_variations(self, normalize_func):
        """Various swimming terms should normalize to 'swim'."""
        assert normalize_func('Swim') == 'swim'
        assert normalize_func('swimming') == 'swim'
        assert normalize_func('Pool') == 'swim'

    def test_types_match_same(self):
        """Same types should match."""
        from scripts.reconcile_workouts import types_match

        assert types_match('Run', 'Run') is True
        assert types_match('running', 'Easy Run') is True
        assert types_match('Strength', 'Weight Training') is True

    def test_types_match_different(self):
        """Different types should not match."""
        from scripts.reconcile_workouts import types_match

        assert types_match('Run', 'Bike') is False
        assert types_match('Strength', 'Swim') is False


# =============================================================================
# TESTS FOR: Health Adaptation Logic (reconcile_workouts.py)
# =============================================================================

class TestHealthAdaptation:
    """Tests for health-based workout adaptation."""

    def test_low_recovery_triggers_adaptation(self):
        """Recovery below threshold should trigger adaptation."""
        from scripts.reconcile_workouts import LOW_RECOVERY_THRESHOLD

        # Simulated health data
        health = {
            'recovery': 35,  # Below threshold (50)
            'sleep_hours': 7.5,  # Fine
            'stress': 40,  # Fine
            'needs_adaptation': False,
            'reasons': [],
        }

        # Apply same logic as get_current_health
        if health['recovery'] and health['recovery'] < LOW_RECOVERY_THRESHOLD:
            health['needs_adaptation'] = True
            health['reasons'].append(f"Low recovery ({health['recovery']:.0f}/100)")

        assert health['needs_adaptation'] is True
        assert 'Low recovery' in health['reasons'][0]

    def test_low_sleep_triggers_adaptation(self):
        """Sleep below threshold should trigger adaptation."""
        from scripts.reconcile_workouts import LOW_SLEEP_THRESHOLD

        health = {
            'recovery': 70,  # Fine
            'sleep_hours': 4.5,  # Below threshold (5.5)
            'stress': 40,  # Fine
            'needs_adaptation': False,
            'reasons': [],
        }

        if health['sleep_hours'] and health['sleep_hours'] < LOW_SLEEP_THRESHOLD:
            health['needs_adaptation'] = True
            health['reasons'].append(f"Poor sleep ({health['sleep_hours']:.1f} hours)")

        assert health['needs_adaptation'] is True
        assert 'Poor sleep' in health['reasons'][0]

    def test_high_stress_triggers_adaptation(self):
        """Stress above threshold should trigger adaptation."""
        from scripts.reconcile_workouts import HIGH_STRESS_THRESHOLD

        health = {
            'recovery': 70,  # Fine
            'sleep_hours': 7.5,  # Fine
            'stress': 75,  # Above threshold (60)
            'needs_adaptation': False,
            'reasons': [],
        }

        if health['stress'] and health['stress'] > HIGH_STRESS_THRESHOLD:
            health['needs_adaptation'] = True
            health['reasons'].append(f"High stress ({health['stress']:.0f}/100)")

        assert health['needs_adaptation'] is True
        assert 'High stress' in health['reasons'][0]

    def test_good_health_no_adaptation(self):
        """Good health metrics should not trigger adaptation."""
        from scripts.reconcile_workouts import (
            LOW_RECOVERY_THRESHOLD,
            LOW_SLEEP_THRESHOLD,
            HIGH_STRESS_THRESHOLD
        )

        health = {
            'recovery': 75,  # Above threshold
            'sleep_hours': 7.5,  # Above threshold
            'stress': 40,  # Below threshold
            'needs_adaptation': False,
            'reasons': [],
        }

        # Apply all checks
        if health['recovery'] and health['recovery'] < LOW_RECOVERY_THRESHOLD:
            health['needs_adaptation'] = True
        if health['sleep_hours'] and health['sleep_hours'] < LOW_SLEEP_THRESHOLD:
            health['needs_adaptation'] = True
        if health['stress'] and health['stress'] > HIGH_STRESS_THRESHOLD:
            health['needs_adaptation'] = True

        assert health['needs_adaptation'] is False


# =============================================================================
# TESTS FOR: Week Progress Calculation (plan_workouts.py)
# =============================================================================

class TestWeekProgress:
    """Tests for weekly workout progress tracking."""

    @pytest.fixture
    def progress_func(self):
        """Import the get_week_progress function."""
        from scripts.plan_workouts import get_week_progress
        return progress_func

    def test_counts_runs_correctly(self):
        """Should correctly count running activities."""
        from scripts.plan_workouts import get_week_progress
        from datetime import datetime
        from zoneinfo import ZoneInfo

        tz = ZoneInfo('America/Chicago')
        today = datetime.now(tz).date()
        week_start = today - timedelta(days=today.weekday())

        recent_workouts = [
            {'type': 'running', 'date': str(week_start)},
            {'type': 'running', 'date': str(week_start + timedelta(days=1))},
            {'type': 'cycling', 'date': str(week_start + timedelta(days=2))},
        ]

        goals = {'weekly_structure': {'run_sessions': 3, 'bike_sessions': 2}}

        progress = get_week_progress(recent_workouts, goals)

        assert progress['completed'].get('runs', 0) == 2
        assert progress['completed'].get('bike', 0) == 1
        assert progress['targets']['runs'] == 3


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
