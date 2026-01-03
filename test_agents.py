#!/usr/bin/env python3
"""
Test script for AI agents with mock data
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.health_monitor_agent import create_health_monitor
from integrations.garmin_connector import GarminConnector


def test_garmin_connector():
    """Test Garmin connector with mock data"""
    print("=" * 60)
    print("TEST 1: Garmin Connector (Mock Data)")
    print("=" * 60)

    garmin = GarminConnector()  # No credentials = mock data

    # Test sleep data
    print("\n📊 Getting sleep data...")
    sleep = garmin.get_sleep_data()
    print(f"   Sleep duration: {sleep['sleep_duration_hours']} hours")
    print(f"   Sleep quality: {sleep['sleep_quality_score']}/100")
    print(f"   Deep sleep: {sleep['deep_sleep_minutes']} min")

    # Test daily stats
    print("\n📊 Getting daily stats...")
    stats = garmin.get_daily_stats()
    print(f"   Steps: {stats['steps']:,}")
    print(f"   Resting HR: {stats['resting_heart_rate']} bpm")
    print(f"   Active calories: {stats['active_calories']}")

    # Test stress data
    print("\n📊 Getting stress data...")
    stress = garmin.get_stress_data()
    print(f"   Average stress: {stress['avg_stress_level']}/100")

    # Test recovery score
    print("\n📊 Calculating recovery score...")
    recovery = garmin.get_recovery_score()
    print(f"   Recovery score: {recovery}/100")

    if recovery < 40:
        print("   Status: CRITICAL - Needs rest!")
    elif recovery < 60:
        print("   Status: POOR - Reduce load")
    elif recovery < 80:
        print("   Status: GOOD - Maintain")
    else:
        print("   Status: EXCELLENT - Can handle high load")

    print("\n✅ Garmin connector test complete!\n")


def test_health_monitor_agent():
    """Test Health Monitor Agent"""
    print("=" * 60)
    print("TEST 2: Health Monitor Agent")
    print("=" * 60)

    print("\n🤖 Creating Health Monitor Agent...")
    agent = create_health_monitor()

    print("\n🔍 Running health check...")
    print("   (This will use Claude/GPT API to analyze the data)")
    print("   Note: Make sure ANTHROPIC_API_KEY or OPENAI_API_KEY is set in .env\n")

    try:
        result = agent.check_health()

        print(f"\n📊 Recovery Score: {result['recovery_score']}/100")
        print(f"🚨 Requires Action: {'YES' if result['requires_action'] else 'NO'}")
        print(f"\n💡 Analysis:\n{result['analysis']}\n")

        print("✅ Health Monitor Agent test complete!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nℹ️  Make sure you have set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")
        print("   Or set LLM_PROVIDER=anthropic or LLM_PROVIDER=openai\n")


def test_database_storage():
    """Test storing health data in database"""
    print("=" * 60)
    print("TEST 3: Database Storage")
    print("=" * 60)

    print("\n💾 Creating Health Monitor Agent...")
    agent = create_health_monitor()

    print("💾 Storing health data to database...")
    result = agent.store_to_database()

    if result['success']:
        print(f"   ✅ Stored successfully!")
        print(f"   Database ID: {result['health_id']}")
        print(f"   Date: {result['date']}")
        print(f"   Recovery: {result['recovery_score']}/100")
    else:
        print(f"   ❌ Failed: {result['error']}")

    print("\n✅ Database storage test complete!\n")


if __name__ == "__main__":
    print("\n🧪 Testing AI Calendar Agent Components")
    print("=" * 60)
    print("Using MOCK data (no Garmin credentials needed)")
    print("=" * 60)

    # Run tests
    test_garmin_connector()

    # Ask user if they want to test the agent (requires API key)
    response = input("Test Health Monitor Agent? (requires LLM API key) [y/N]: ")

    if response.lower() in ['y', 'yes']:
        test_health_monitor_agent()
        test_database_storage()
    else:
        print("\nℹ️  Skipping agent tests.")
        print("   To test the agent, set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env\n")

    print("=" * 60)
    print("✅ All tests complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Add your Anthropic/OpenAI API key to .env")
    print("  2. Run: python test_agents.py")
    print("  3. (Optional) Add real Garmin credentials to .env for real data\n")
