#!/usr/bin/env python3
"""
Test database connection and basic operations
"""
import sys
from datetime import datetime, timedelta
from psycopg2 import sql
from connection import (
    Database,
    insert_health_metric,
    insert_calendar_event,
    log_agent_action,
    get_user_preference,
    set_user_preference,
    get_upcoming_events
)


def test_database_connection():
    """Test database connection and basic operations"""
    print("🧪 Testing Life Optimization AI Database\n")

    try:
        # Test 1: Connection
        print("1️⃣  Testing database connection...")
        result = Database.execute_one("SELECT NOW() as current_time, version() as pg_version")
        print(f"   ✅ Connected successfully!")
        print(f"   ⏰ Server time: {result['current_time']}")
        print(f"   📊 PostgreSQL version: {result['pg_version'][:50]}...")

        # Test 2: Insert health metric
        print("\n2️⃣  Testing health metric insertion...")
        health_data = {
            'timestamp': datetime.now(),
            'source': 'test',
            'sleep_duration_hours': 7.5,
            'sleep_quality_score': 85,
            'resting_heart_rate': 60,
            'stress_level': 30,
            'recovery_score': 75.5,
            'steps': 10000,
            'raw_data': '{"test": true}'
        }
        health_id = insert_health_metric(health_data)
        print(f"   ✅ Health metric inserted with ID: {health_id}")

        # Test 3: Insert calendar event
        print("\n3️⃣  Testing calendar event insertion...")
        event_data = {
            'event_id': 'test_event_001',
            'summary': 'Test Meeting',
            'description': 'This is a test event',
            'start_time': datetime.now() + timedelta(hours=1),
            'end_time': datetime.now() + timedelta(hours=2),
            'has_external_participants': False,
            'participant_count': 3,
            'tags': '["test", "meeting"]'
        }
        event_id = insert_calendar_event(event_data)
        print(f"   ✅ Calendar event inserted with ID: {event_id}")

        # Test 4: Log agent action
        print("\n4️⃣  Testing agent action logging...")
        action_data = {
            'confidence_score': 85.5,
            'reasoning': 'Test action for database verification',
            'before_state': '{"calendar": "empty"}',
            'after_state': '{"calendar": "has_event"}',
            'data_sources': '["test"]',
            'executed': True
        }
        action_id = log_agent_action('TestAgent', 'test_action', action_data)
        print(f"   ✅ Agent action logged with ID: {action_id}")

        # Test 5: User preferences
        print("\n5️⃣  Testing user preferences...")
        pref_value = get_user_preference('working_hours_start')
        print(f"   ✅ Retrieved preference 'working_hours_start': {pref_value}")

        set_user_preference('test_preference', '{"value": 123}', 'Test preference')
        test_pref = get_user_preference('test_preference')
        print(f"   ✅ Set and retrieved test preference: {test_pref}")

        # Test 6: Query upcoming events
        print("\n6️⃣  Testing upcoming events query...")
        upcoming = get_upcoming_events(hours=24)
        print(f"   ✅ Found {len(upcoming)} upcoming event(s)")
        if upcoming:
            for event in upcoming:
                print(f"      • {event['summary']} at {event['start_time']}")

        # Test 7: Views
        print("\n7️⃣  Testing database views...")
        views = Database.execute_query("""
            SELECT viewname FROM pg_views
            WHERE schemaname = 'public'
            ORDER BY viewname
        """)
        print(f"   ✅ Found {len(views)} views:")
        for view in views:
            print(f"      • {view['viewname']}")

        # Test 8: Count all tables
        print("\n8️⃣  Testing all tables...")
        tables = Database.execute_query("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        print(f"   ✅ Database has {len(tables)} tables:")
        for table in tables:
            # Count rows in each table
            # Use sql.Identifier to safely quote table names (prevents SQL injection)
            query = sql.SQL("SELECT COUNT(*) as count FROM {}").format(
                sql.Identifier(table['tablename'])
            )
            count = Database.execute_one(query)
            print(f"      • {table['tablename']}: {count['count']} rows")

        print("\n" + "="*60)
        print("✅ All database tests passed successfully!")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Close connection pool
        Database.close_pool()


if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
