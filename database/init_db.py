#!/usr/bin/env python3
"""
Initialize PostgreSQL database with schema
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def init_database():
    """Initialize database with schema"""
    print("🔧 Initializing Life Optimization AI database...")

    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in .env file")
        sys.exit(1)

    # Read schema file
    schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.exists(schema_file):
        print(f"❌ ERROR: Schema file not found: {schema_file}")
        sys.exit(1)

    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    # Connect and execute schema
    try:
        print("📊 Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True

        print("📝 Executing schema...")
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)

        print("✅ Database schema created successfully!")

        # Verify tables
        print("\n📋 Verifying tables...")
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = cursor.fetchall()

            print(f"\nCreated {len(tables)} tables:")
            for table in tables:
                print(f"  ✓ {table[0]}")

        # Check system metadata
        print("\n🔍 Checking system metadata...")
        with conn.cursor() as cursor:
            cursor.execute("SELECT key, value FROM system_metadata")
            metadata = cursor.fetchall()

            print("\nSystem info:")
            for key, value in metadata:
                print(f"  {key}: {value}")

        conn.close()
        print("\n✅ Database initialization complete!")
        return True

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
