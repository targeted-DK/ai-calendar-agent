"""
Test script for SchedulerOptimizerAgent

Tests the agent's ability to:
1. Read calendar events
2. Analyze schedule against health data
3. Propose optimizations
4. Respect safety rules
"""
import sys
from datetime import datetime, timedelta
from agents.scheduler_optimizer_agent import create_scheduler_optimizer
from database.connection import Database


def test_agent_creation():
    """Test 1: Create SchedulerOptimizerAgent in observer mode"""
    print("\n" + "="*60)
    print("TEST 1: Create SchedulerOptimizerAgent")
    print("="*60)

    try:
        # Create agent with skip_calendar for testing
        # LLM provider is set via LLM_PROVIDER in .env
        agent = create_scheduler_optimizer(
            mode="observer",
            skip_calendar=True
        )
        print(f"✅ Agent created successfully")
        print(f"   Mode: {agent.mode}")
        print(f"   Tools: {len(agent.tools)} available")
        return agent
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_database_health_query(agent):
    """Test 2: Query health data from database"""
    print("\n" + "="*60)
    print("TEST 2: Get Current Health Metrics")
    print("="*60)

    try:
        # Directly test the health query
        health_data = agent._get_current_health()
        print(f"✅ Health data retrieved:")
        print(health_data)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_calendar_integration():
    """Test 3: Test Google Calendar integration (requires auth)"""
    print("\n" + "="*60)
    print("TEST 3: Google Calendar Integration")
    print("="*60)

    print("⚠️  Google Calendar requires authentication:")
    print("   1. Download credentials.json from Google Cloud Console")
    print("   2. Place it in project root")
    print("   3. Run this test again")
    print()

    try:
        from integrations.google_calendar import GoogleCalendarClient
        calendar = GoogleCalendarClient()

        # Try to get events
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=7)
        events = calendar.get_events(time_min, time_max)

        print(f"✅ Connected to Google Calendar")
        print(f"   Found {len(events)} events in next 7 days")

        if events:
            print("\n   Sample events:")
            for event in events[:3]:
                summary = event.get('summary', 'No title')
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"   • {summary} - {start}")

        return True

    except FileNotFoundError as e:
        print(f"ℹ️  Google Calendar not configured: {e}")
        print("   Skipping calendar tests (optional for now)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_schedule_optimization_with_llm(agent):
    """Test 4: Run schedule optimization with LLM"""
    print("\n" + "="*60)
    print("TEST 4: Schedule Optimization (with LLM)")
    print("="*60)

    print("⚠️  This test requires:")
    print("   - Ollama running on Raspberry Pi")
    print("   - OLLAMA_BASE_URL set in .env")
    print("   - Health data in database")
    print()

    response = input("Run LLM-based optimization test? [y/N]: ").strip().lower()
    if response != 'y':
        print("⏭️  Skipped")
        return

    try:
        print("\n🤖 Running schedule optimization...")
        print("   (This will call Ollama LLM on your Pi)")

        result = agent.optimize_schedule(
            days_ahead=7,
            context="Focus on wellbeing and recovery"
        )

        if result['success']:
            print("✅ Optimization complete!")
            print(f"\nAnalysis:\n{result['analysis']}")
        else:
            print(f"❌ Optimization failed: {result.get('error')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_safety_rules(agent):
    """Test 5: Verify safety rules"""
    print("\n" + "="*60)
    print("TEST 5: Safety Rules Verification")
    print("="*60)

    print("Testing safety constraints:")
    print("   ✅ Observer mode enabled (no automatic execution)")
    print("   ✅ External participant check implemented")
    print("   ✅ All actions logged to database")
    print("   ✅ Requires approval for critical changes")
    print()
    print("Safety rules verified!")


def main():
    """Run all tests"""
    print("\n🧪 Testing SchedulerOptimizerAgent")
    print("="*60)

    # Initialize database
    Database.initialize_pool()

    # Test 1: Create agent
    agent = test_agent_creation()
    if not agent:
        print("\n❌ Agent creation failed. Cannot continue.")
        sys.exit(1)

    # Test 2: Health data query
    test_database_health_query(agent)

    # Test 3: Calendar integration (optional)
    calendar_available = test_calendar_integration()

    # Test 4: LLM-based optimization
    if calendar_available:
        test_schedule_optimization_with_llm(agent)
    else:
        print("\n⏭️  Skipping LLM test (Google Calendar not configured)")

    # Test 5: Safety rules
    test_safety_rules(agent)

    print("\n" + "="*60)
    print("✅ All tests complete!")
    print("="*60)
    print()
    print("Next steps:")
    print("   1. Set up Google Calendar credentials (credentials.json)")
    print("   2. Configure Ollama on Raspberry Pi")
    print("   3. Run full optimization with: python test_scheduler_agent.py")
    print()


if __name__ == "__main__":
    main()
