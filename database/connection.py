"""
Database connection management for Life Optimization AI
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Database:
    """PostgreSQL database connection manager"""

    _pool: Optional[SimpleConnectionPool] = None

    @classmethod
    def initialize_pool(cls, min_conn: int = 1, max_conn: int = 10):
        """Initialize connection pool"""
        if cls._pool is None:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL not found in environment variables")

            cls._pool = SimpleConnectionPool(
                min_conn,
                max_conn,
                database_url
            )
            print(f"✅ Database connection pool initialized (min={min_conn}, max={max_conn})")

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get database connection from pool"""
        if cls._pool is None:
            cls.initialize_pool()

        conn = cls._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cls._pool.putconn(conn)

    @classmethod
    def execute_query(cls, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dicts"""
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                return [dict(row) for row in cursor.fetchall()]

    @classmethod
    def execute_one(cls, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute SELECT query and return first result"""
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchone()
                return dict(result) if result else None

    @classmethod
    def execute_update(cls, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        with cls.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.rowcount

    @classmethod
    def execute_many(cls, query: str, params_list: List[tuple]) -> int:
        """Execute batch INSERT/UPDATE"""
        with cls.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                return cursor.rowcount

    @classmethod
    def close_pool(cls):
        """Close all connections in pool"""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            print("✅ Database connection pool closed")


# Convenience functions for common operations

def insert_health_metric(data: Dict[str, Any]) -> int:
    """Insert health metric and return ID (skips if duplicate)"""
    query = """
    INSERT INTO health_metrics (
        timestamp, source, sleep_duration_hours, sleep_quality_score,
        resting_heart_rate, stress_level, recovery_score, steps, raw_data
    ) VALUES (
        %(timestamp)s, %(source)s, %(sleep_duration_hours)s, %(sleep_quality_score)s,
        %(resting_heart_rate)s, %(stress_level)s, %(recovery_score)s, %(steps)s, %(raw_data)s
    )
    ON CONFLICT (timestamp, source) DO NOTHING
    RETURNING id
    """
    result = Database.execute_one(query, data)
    return result['id'] if result else None


def insert_calendar_event(data: Dict[str, Any]) -> int:
    """Insert calendar event and return ID"""
    query = """
    INSERT INTO calendar_events (
        event_id, summary, description, start_time, end_time,
        has_external_participants, participant_count, tags
    ) VALUES (
        %(event_id)s, %(summary)s, %(description)s, %(start_time)s, %(end_time)s,
        %(has_external_participants)s, %(participant_count)s, %(tags)s
    )
    ON CONFLICT (event_id) DO UPDATE SET
        summary = EXCLUDED.summary,
        description = EXCLUDED.description,
        start_time = EXCLUDED.start_time,
        end_time = EXCLUDED.end_time,
        last_modified = NOW()
    RETURNING id
    """
    result = Database.execute_one(query, data)
    return result['id'] if result else None


def log_agent_action(agent_name: str, action_type: str, data: Dict[str, Any]) -> int:
    """Log an agent action"""
    query = """
    INSERT INTO agent_actions (
        agent_name, action_type, confidence_score, reasoning,
        before_state, after_state, data_sources, executed
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s
    )
    RETURNING id
    """
    params = (
        agent_name,
        action_type,
        data.get('confidence_score'),
        data.get('reasoning'),
        data.get('before_state'),
        data.get('after_state'),
        data.get('data_sources'),
        data.get('executed', False)
    )
    result = Database.execute_one(query, params)
    return result['id'] if result else None


def get_recent_health_metrics(days: int = 7) -> List[Dict[str, Any]]:
    """Get recent health metrics"""
    query = """
    SELECT * FROM health_metrics
    WHERE timestamp >= NOW() - INTERVAL '%s days'
    ORDER BY timestamp DESC
    """
    return Database.execute_query(query, (days,))


def get_user_preference(key: str) -> Optional[Any]:
    """Get user preference by key"""
    query = "SELECT value FROM user_preferences WHERE key = %s"
    result = Database.execute_one(query, (key,))
    return result['value'] if result else None


def set_user_preference(key: str, value: Any, description: str = None) -> None:
    """Set user preference"""
    query = """
    INSERT INTO user_preferences (key, value, description)
    VALUES (%s, %s, %s)
    ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        description = COALESCE(EXCLUDED.description, user_preferences.description),
        updated_at = NOW()
    """
    Database.execute_update(query, (key, value, description))


def get_upcoming_events(hours: int = 24) -> List[Dict[str, Any]]:
    """Get upcoming calendar events"""
    query = """
    SELECT * FROM calendar_events
    WHERE start_time BETWEEN NOW() AND NOW() + INTERVAL '%s hours'
    ORDER BY start_time ASC
    """
    return Database.execute_query(query, (hours,))


# Initialize pool on import
Database.initialize_pool()
