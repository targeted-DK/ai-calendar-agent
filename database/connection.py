"""
Database connection management for Life Optimization AI
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, Dict, List, Any, Tuple
from contextlib import contextmanager


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

            # Set SSL mode if not specified (disable for local Docker, require for production)
            if 'sslmode=' not in database_url:
                database_url += '&sslmode=disable' if '?' in database_url else '?sslmode=disable'

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
    def execute_query(cls, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dicts"""
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                return [dict(row) for row in cursor.fetchall()]

    @classmethod
    def execute_one(cls, query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """Execute SELECT query and return first result"""
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchone()
                return dict(result) if result else None

    @classmethod
    def execute_update(cls, query: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        with cls.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.rowcount

    @classmethod
    def execute_many(cls, query: str, params_list: List[Tuple]) -> int:
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

def insert_health_metric(data: Dict[str, Any]) -> Optional[int]:
    """Insert health metric and return ID (skips if duplicate)"""
    query = """
    INSERT INTO health_metrics (
        timestamp, source, sleep_duration_hours, sleep_quality_score,
        resting_heart_rate, stress_level, recovery_score, steps, raw_data
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (timestamp, source) DO NOTHING
    RETURNING id
    """
    params = (
        data.get('timestamp'),
        data.get('source'),
        data.get('sleep_duration_hours'),
        data.get('sleep_quality_score'),
        data.get('resting_heart_rate'),
        data.get('stress_level'),
        data.get('recovery_score'),
        data.get('steps'),
        data.get('raw_data')
    )
    result = Database.execute_one(query, params)
    return result['id'] if result else None


def insert_calendar_event(data: Dict[str, Any]) -> Optional[int]:
    """Insert calendar event and return ID"""
    query = """
    INSERT INTO calendar_events (
        event_id, summary, description, start_time, end_time,
        has_external_participants, participant_count, tags
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (event_id) DO UPDATE SET
        summary = EXCLUDED.summary,
        description = EXCLUDED.description,
        start_time = EXCLUDED.start_time,
        end_time = EXCLUDED.end_time,
        last_modified = NOW()
    RETURNING id
    """
    params = (
        data.get('event_id'),
        data.get('summary'),
        data.get('description'),
        data.get('start_time'),
        data.get('end_time'),
        data.get('has_external_participants'),
        data.get('participant_count'),
        data.get('tags')
    )
    result = Database.execute_one(query, params)
    return result['id'] if result else None


def log_agent_action(agent_name: str, action_type: str, data: Dict[str, Any]) -> Optional[int]:
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
    WHERE timestamp >= NOW() - INTERVAL %s days
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
    params = (key, value, description)
    Database.execute_update(query, params)


def get_upcoming_events(hours: int = 24) -> List[Dict[str, Any]]:
    """Get upcoming calendar events"""
    query = """
    SELECT * FROM calendar_events
    WHERE start_time BETWEEN NOW() AND NOW() + INTERVAL %s hours
    ORDER BY start_time ASC
    """
    return Database.execute_query(query, (hours,))


# Note: Call Database.initialize_pool() explicitly in scripts that need DB access