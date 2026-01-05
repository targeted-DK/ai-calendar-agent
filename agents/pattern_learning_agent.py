"""
Pattern Learning Agent - Learns from historical data and provides rich context
"""
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from rag.vector_store import VectorStore
from database.connection import Database
import json


class PatternLearningAgent(BaseAgent):
    """
    Agent that learns patterns from historical health, activity, and calendar data.
    Provides rich context to other agents for intelligent decision-making.
    """

    SYSTEM_PROMPT = """You are a pattern learning AI agent. Your role is to:

1. Analyze historical health, activity, and calendar data
2. Identify meaningful patterns and correlations
3. Provide rich context for schedule optimization decisions
4. Learn what works well and what doesn't for the user

When analyzing patterns:
- Look for correlations between recovery score and schedule density
- Identify optimal times for different types of activities
- Recognize stress patterns and their triggers
- Learn from user modifications and feedback

Provide context that includes:
- Historical trends (30-90 day view)
- Similar past situations and their outcomes
- Learned correlations (e.g., "meetings before 10am correlate with 15% lower stress")
- User goals and preferences

Always explain patterns with confidence scores and supporting data."""

    def __init__(self):
        """Initialize Pattern Learning Agent."""
        tools = [
            {
                "name": "get_historical_health",
                "description": "Get historical health metrics for pattern analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 30)"
                        }
                    }
                }
            },
            {
                "name": "get_historical_activities",
                "description": "Get historical activities for pattern analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 30)"
                        }
                    }
                }
            },
            {
                "name": "get_calendar_patterns",
                "description": "Get calendar event patterns from vector store",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query for similar patterns"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "store_learned_pattern",
                "description": "Store a newly learned pattern",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern_type": {
                            "type": "string",
                            "description": "Type of pattern (schedule_correlation, recovery_trigger, etc.)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the pattern"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence score 0-100"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional metadata about the pattern"
                        }
                    },
                    "required": ["pattern_type", "description", "confidence"]
                }
            }
        ]

        super().__init__(system_prompt=self.SYSTEM_PROMPT, tools=tools)

        # Initialize vector store for pattern storage
        self.vector_store = VectorStore()

        # Register tool functions
        self.register_tool("get_historical_health", self._get_historical_health)
        self.register_tool("get_historical_activities", self._get_historical_activities)
        self.register_tool("get_calendar_patterns", self._get_calendar_patterns)
        self.register_tool("store_learned_pattern", self._store_learned_pattern)

        print("✅ PatternLearningAgent initialized")

    def _get_historical_health(self, days: int = 30) -> Dict[str, Any]:
        """Tool: Get historical health metrics."""
        query = """
        SELECT
            DATE(timestamp) as date,
            sleep_duration_hours,
            sleep_quality_score,
            resting_heart_rate,
            stress_level,
            recovery_score,
            steps,
            active_calories,
            intensity_minutes
        FROM health_metrics
        WHERE timestamp >= NOW() - INTERVAL '%s days'
        ORDER BY timestamp DESC
        LIMIT 100
        """

        try:
            results = Database.execute_query(query, (days,))

            if not results:
                return {
                    "status": "no_data",
                    "message": f"No health data found for past {days} days"
                }

            # Calculate trends
            metrics = {
                'sleep_avg': 0,
                'recovery_avg': 0,
                'stress_avg': 0,
                'records': []
            }

            sleep_sum = 0
            recovery_sum = 0
            stress_sum = 0
            count = 0

            for row in results:
                record = {
                    'date': str(row[0]),
                    'sleep_hours': float(row[1]) if row[1] else None,
                    'sleep_quality': int(row[2]) if row[2] else None,
                    'resting_hr': int(row[3]) if row[3] else None,
                    'stress': int(row[4]) if row[4] else None,
                    'recovery': float(row[5]) if row[5] else None,
                    'steps': int(row[6]) if row[6] else None,
                }
                metrics['records'].append(record)

                if row[1]:
                    sleep_sum += float(row[1])
                    count += 1
                if row[5]:
                    recovery_sum += float(row[5])
                if row[4]:
                    stress_sum += int(row[4])

            if count > 0:
                metrics['sleep_avg'] = round(sleep_sum / count, 2)
                metrics['recovery_avg'] = round(recovery_sum / count, 2)
                metrics['stress_avg'] = round(stress_sum / count, 2)

            metrics['total_records'] = len(results)
            metrics['days_analyzed'] = days

            return metrics

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error fetching health data: {str(e)}"
            }

    def _get_historical_activities(self, days: int = 30) -> Dict[str, Any]:
        """Tool: Get historical activities."""
        query = """
        SELECT
            DATE(timestamp) as date,
            activity_type,
            duration_minutes,
            distance_km,
            avg_heart_rate,
            aerobic_training_effect,
            anaerobic_training_effect,
            calories_burned
        FROM activity_data
        WHERE timestamp >= NOW() - INTERVAL '%s days'
        ORDER BY timestamp DESC
        LIMIT 100
        """

        try:
            results = Database.execute_query(query, (days,))

            if not results:
                return {
                    "status": "no_data",
                    "message": f"No activity data found for past {days} days"
                }

            activities = []
            total_duration = 0
            total_calories = 0

            for row in results:
                activity = {
                    'date': str(row[0]),
                    'type': row[1],
                    'duration_min': int(row[2]) if row[2] else 0,
                    'distance_km': float(row[3]) if row[3] else 0,
                    'avg_hr': int(row[4]) if row[4] else None,
                    'aerobic_effect': float(row[5]) if row[5] else None,
                    'anaerobic_effect': float(row[6]) if row[6] else None,
                    'calories': int(row[7]) if row[7] else 0
                }
                activities.append(activity)

                if row[2]:
                    total_duration += int(row[2])
                if row[7]:
                    total_calories += int(row[7])

            summary = {
                'total_activities': len(results),
                'total_duration_minutes': total_duration,
                'total_calories': total_calories,
                'avg_duration_per_activity': round(total_duration / len(results), 1) if results else 0,
                'activities': activities,
                'days_analyzed': days
            }

            return summary

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error fetching activity data: {str(e)}"
            }

    def _get_calendar_patterns(self, query: str) -> Dict[str, Any]:
        """Tool: Search for similar patterns in vector store."""
        try:
            patterns = self.vector_store.search_patterns(query, n_results=5)

            if not patterns:
                return {
                    "status": "no_patterns",
                    "message": "No similar patterns found"
                }

            return {
                "status": "success",
                "patterns": [
                    {
                        'description': p['document'],
                        'metadata': p['metadata'],
                        'relevance': 1 - p['distance'] if p['distance'] else None
                    }
                    for p in patterns
                ]
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error searching patterns: {str(e)}"
            }

    def _store_learned_pattern(
        self,
        pattern_type: str,
        description: str,
        confidence: float,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Tool: Store a learned pattern."""
        try:
            # Create unique pattern ID
            pattern_id = f"{pattern_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Prepare metadata
            meta = metadata or {}
            meta.update({
                'pattern_type': pattern_type,
                'confidence': confidence,
                'learned_at': datetime.now().isoformat()
            })

            # Store in vector database
            self.vector_store.add_pattern(
                pattern_id=pattern_id,
                pattern_text=description,
                metadata=meta
            )

            # Also store in PostgreSQL for structured queries
            query = """
            INSERT INTO learned_patterns (
                pattern_type, pattern_description, confidence_score,
                triggers, outcomes, last_seen
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """

            result = Database.execute_one(
                query,
                (
                    pattern_type,
                    description,
                    confidence,
                    json.dumps(meta.get('triggers', {})),
                    json.dumps(meta.get('outcomes', {})),
                    datetime.now()
                )
            )

            return {
                "status": "success",
                "pattern_id": pattern_id,
                "db_id": result[0] if result else None,
                "message": f"Pattern stored with {confidence}% confidence"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error storing pattern: {str(e)}"
            }

    def build_rich_context(self, situation_query: str, days_lookback: int = 30) -> Dict[str, Any]:
        """
        Build rich context for decision-making by analyzing historical data.

        Args:
            situation_query: Description of current situation
            days_lookback: How many days of history to analyze

        Returns:
            Dictionary with comprehensive context including trends, patterns, and recommendations
        """
        user_message = f"""Analyze the current situation and build rich context:

Current situation: {situation_query}

Please:
1. Get historical health data for the past {days_lookback} days
2. Get historical activities for the past {days_lookback} days
3. Search for similar past situations
4. Identify relevant patterns and correlations
5. Provide context summary with trends, learned patterns, and recommendations

Focus on actionable insights that can inform schedule optimization decisions."""

        response = self.run(user_message)

        return {
            "situation": situation_query,
            "context_analysis": response,
            "lookback_days": days_lookback,
            "generated_at": datetime.now().isoformat()
        }

    def learn_from_outcome(
        self,
        situation: str,
        action_taken: str,
        outcome: str,
        user_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Learn from the outcome of an action to improve future recommendations.

        Args:
            situation: Description of the situation
            action_taken: What action was taken
            outcome: Result of the action
            user_feedback: Optional user feedback ('approved', 'rejected', 'modified')

        Returns:
            Result of learning operation
        """
        user_message = f"""Learn from this outcome to improve future recommendations:

Situation: {situation}
Action taken: {action_taken}
Outcome: {outcome}
User feedback: {user_feedback or 'none'}

Please:
1. Analyze what worked well and what didn't
2. Identify any new patterns or correlations
3. Store learned patterns for future use
4. Provide confidence score for the pattern

Store any significant patterns you discover."""

        response = self.run(user_message)

        return {
            "status": "learned",
            "analysis": response,
            "situation": situation,
            "learned_at": datetime.now().isoformat()
        }


# Convenience function
def create_pattern_learning_agent() -> PatternLearningAgent:
    """Create and return a Pattern Learning Agent instance"""
    return PatternLearningAgent()
