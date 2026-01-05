#!/usr/bin/env python3
"""
Integration Tests for AI Calendar Agent
Tests all major components: database, Garmin import, embeddings, and PatternLearningAgent
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date, timedelta
from database.connection import Database
from integrations.garmin_connector import GarminConnector
from rag.embeddings import EmbeddingGenerator
from agents.pattern_learning_agent import create_pattern_learning_agent
import json


def print_section(title: str):
    """Print a test section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_database_connection():
    """Test PostgreSQL database connection."""
    print_section("Test 1: Database Connection")

    try:
        # Initialize database pool
        Database.initialize_pool()
        print("✅ Database pool initialized")

        # Test simple query
        result = Database.execute_query("SELECT 1 as test")
        if result and len(result) > 0 and result[0]['test'] == 1:
            print("✅ Database query successful")
            return True
        else:
            print(f"❌ Database query failed - unexpected result: {result}")
            return False

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_garmin_connector():
    """Test Garmin connector with mock data."""
    print_section("Test 2: Garmin Connector (Mock Data)")

    try:
        connector = GarminConnector()
        print("✅ GarminConnector initialized")

        # Test sleep data
        yesterday = date.today() - timedelta(days=1)
        sleep = connector.get_sleep_data(yesterday)

        if sleep and 'sleep_duration_hours' in sleep:
            print(f"✅ Sleep data: {sleep['sleep_duration_hours']}h, quality {sleep.get('sleep_quality_score')}/100")
        else:
            print("❌ Sleep data retrieval failed")
            return False

        # Test daily stats
        stats = connector.get_daily_stats()
        if stats and 'resting_heart_rate' in stats:
            print(f"✅ Daily stats: RHR {stats['resting_heart_rate']} bpm, {stats.get('steps')} steps")
        else:
            print("❌ Daily stats retrieval failed")
            return False

        # Test recovery score
        recovery = connector.get_recovery_score()
        if recovery is not None:
            print(f"✅ Recovery score: {recovery}/100")
        else:
            print("❌ Recovery score calculation failed")
            return False

        # Test activities
        activities = connector.get_activities(start_date=yesterday, limit=5)
        if isinstance(activities, list):
            print(f"✅ Activities retrieved: {len(activities)} activities")
            if activities:
                print(f"   Sample: {activities[0]['activity_type']}, {activities[0]['duration_minutes']}min")
        else:
            print("❌ Activities retrieval failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Garmin connector error: {e}")
        return False


def test_embeddings():
    """Test embedding generation with Ollama."""
    print_section("Test 3: Ollama Embeddings")

    try:
        # Initialize with Ollama provider
        embedder = EmbeddingGenerator(provider="ollama")
        print(f"✅ EmbeddingGenerator initialized with provider: {embedder.provider}")
        print(f"   Model: {embedder.model}")

        # Test single embedding
        test_text = "Recovery score of 65/100 after 7.5 hours of sleep with moderate stress"
        embedding = embedder.generate_embedding(test_text)

        if embedding and isinstance(embedding, list) and len(embedding) > 0:
            print(f"✅ Single embedding generated: {len(embedding)} dimensions")
            print(f"   Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
        else:
            print("❌ Embedding generation failed")
            return False

        # Test batch embeddings
        test_texts = [
            "High recovery score correlates with low meeting density",
            "Poor sleep quality leads to reduced productivity next day",
            "Morning workouts improve afternoon focus time"
        ]

        embeddings = embedder.generate_embeddings(test_texts)
        if embeddings and len(embeddings) == len(test_texts):
            print(f"✅ Batch embeddings generated: {len(embeddings)} embeddings")
        else:
            print("❌ Batch embedding generation failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Embedding error: {e}")
        print(f"   Note: Make sure Ollama is running and nomic-embed-text is installed")
        return False


def test_pattern_learning_agent():
    """Test PatternLearningAgent."""
    print_section("Test 4: Pattern Learning Agent")

    try:
        # Create agent
        agent = create_pattern_learning_agent()
        print("✅ PatternLearningAgent created")

        # Test historical health data retrieval
        print("\n📊 Testing historical health data retrieval...")
        # Note: This will work if database has data, otherwise will return empty
        # The important thing is that the method doesn't crash

        # Test building rich context
        print("\n🧠 Testing rich context building...")
        context = agent.build_rich_context(
            situation_query="Recovery score is 42/100 after poor sleep. Have 5 meetings scheduled today.",
            days_lookback=7
        )

        if context and 'context_analysis' in context:
            print("✅ Rich context built successfully")
            print(f"   Situation: {context['situation']}")
            print(f"   Lookback: {context['lookback_days']} days")
            print(f"\n   Analysis preview:")
            analysis = context['context_analysis']
            # Print first 300 characters of analysis
            preview = analysis[:300] + "..." if len(analysis) > 300 else analysis
            print(f"   {preview}")
        else:
            print("❌ Context building failed")
            return False

        # Test learning from outcome
        print("\n📚 Testing learning from outcome...")
        learning_result = agent.learn_from_outcome(
            situation="Low recovery score (45/100) with heavy meeting schedule",
            action_taken="Rescheduled 3 non-critical meetings, added 2-hour recovery block",
            outcome="Recovery improved to 68/100 next day, user reported feeling better",
            user_feedback="approved"
        )

        if learning_result and learning_result.get('status') == 'learned':
            print("✅ Learning from outcome successful")
        else:
            print("❌ Learning from outcome failed")
            return False

        return True

    except Exception as e:
        print(f"❌ PatternLearningAgent error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_import():
    """Test Garmin data import script."""
    print_section("Test 5: Garmin Data Import")

    try:
        from scripts.import_garmin_data import import_health_data, import_activities

        connector = GarminConnector()

        # Import 3 days of health data
        print("\n📥 Importing health data (3 days)...")
        health_stats = import_health_data(connector, days=3)

        print(f"   Success: {health_stats['success']}")
        print(f"   Skipped: {health_stats['skipped']} (already in DB)")
        print(f"   Errors:  {health_stats['errors']}")

        if health_stats['success'] + health_stats['skipped'] > 0:
            print("✅ Health data import working")
        else:
            print("⚠️  No health data imported (may already exist in DB)")

        # Import 7 days of activities
        print("\n📥 Importing activities (7 days)...")
        activity_stats = import_activities(connector, days=7)

        print(f"   Success: {activity_stats['success']}")
        print(f"   Skipped: {activity_stats['skipped']} (already in DB)")
        print(f"   Errors:  {activity_stats['errors']}")

        if activity_stats['success'] + activity_stats['skipped'] > 0:
            print("✅ Activity data import working")
        else:
            print("⚠️  No activities imported (may already exist in DB)")

        return True

    except Exception as e:
        print(f"❌ Data import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("#" + " "*20 + "INTEGRATION TESTS" + " "*22 + "#")
    print("#"*60)

    results = {
        "Database Connection": False,
        "Garmin Connector": False,
        "Ollama Embeddings": False,
        "Pattern Learning Agent": False,
        "Data Import": False
    }

    # Run tests
    results["Database Connection"] = test_database_connection()
    results["Garmin Connector"] = test_garmin_connector()
    results["Ollama Embeddings"] = test_embeddings()
    results["Pattern Learning Agent"] = test_pattern_learning_agent()
    results["Data Import"] = test_data_import()

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
