#!/usr/bin/env python3
"""
Example usage of the AI Calendar Agent system.
Demonstrates key features and capabilities.
"""

from agents import SchedulerAgent, PatternLearningAgent
from datetime import datetime, timedelta


def example_1_natural_language_scheduling():
    """Example 1: Schedule events using natural language."""
    print("\n" + "="*60)
    print("Example 1: Natural Language Scheduling")
    print("="*60)

    scheduler = SchedulerAgent()

    # Example requests
    requests = [
        "Schedule a team standup for tomorrow at 10am, 15 minutes",
        "I need a 2-hour focus block next Tuesday afternoon",
        "Create a lunch meeting with Sarah on Friday at noon"
    ]

    for request in requests:
        print(f"\nRequest: {request}")
        response = scheduler.schedule_event(request)
        print(f"Response: {response}")
        print("-" * 60)


def example_2_smart_time_finding():
    """Example 2: Find optimal time slots using AI."""
    print("\n" + "="*60)
    print("Example 2: Smart Time Finding")
    print("="*60)

    scheduler = SchedulerAgent()

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nFinding time for a sprint planning meeting ({tomorrow})...")
    response = scheduler.find_time_for_meeting(
        meeting_description="Sprint planning with engineering team",
        duration_minutes=90,
        preferred_date=tomorrow
    )
    print(f"Response: {response}")


def example_3_pattern_learning():
    """Example 3: Learn patterns from calendar history."""
    print("\n" + "="*60)
    print("Example 3: Pattern Learning with RAG")
    print("="*60)

    pattern_agent = PatternLearningAgent()

    print("\nLearning from 90 days of calendar history...")
    patterns = pattern_agent.learn_from_history(days_back=90)

    print("\nDiscovered patterns:")
    for pattern_id, pattern_data in patterns.items():
        print(f"\n{pattern_id}:")
        print(f"  {pattern_data['description']}")
        print(f"  Metadata: {pattern_data['metadata']}")


def example_4_rag_recommendations():
    """Example 4: Get recommendations based on learned patterns."""
    print("\n" + "="*60)
    print("Example 4: RAG-Based Recommendations")
    print("="*60)

    pattern_agent = PatternLearningAgent()

    queries = [
        "When should I schedule project planning meetings?",
        "What's the best time for deep focus work?",
        "When do I typically have team meetings?"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        response = pattern_agent.get_recommendations(query)
        print(f"Recommendation: {response}")
        print("-" * 60)


def example_5_calendar_analysis():
    """Example 5: Analyze calendar usage and get insights."""
    print("\n" + "="*60)
    print("Example 5: Calendar Analysis & Insights")
    print("="*60)

    scheduler = SchedulerAgent()

    print("\nAnalyzing calendar patterns...")
    response = scheduler.analyze_calendar_patterns()
    print(f"Analysis: {response}")


def example_6_tool_usage():
    """Example 6: Direct tool usage (lower-level API)."""
    print("\n" + "="*60)
    print("Example 6: Direct Tool Usage")
    print("="*60)

    from tools import CalendarTools

    tools = CalendarTools()

    # Get upcoming events
    print("\nUpcoming events (next 7 days):")
    events = tools.get_upcoming_events(days=7)
    for event in events[:5]:  # Show first 5
        print(f"  - {event['summary']} at {event['start']}")

    # Get statistics
    print("\nCalendar statistics (last 30 days):")
    stats = tools.get_event_statistics(days=30)
    print(f"  Total events: {stats['total_events']}")
    print(f"  Total hours: {stats['total_hours']}")
    print(f"  Average events/day: {stats['average_events_per_day']}")
    print(f"  Event types: {stats['event_types']}")

    # Search similar events
    print("\nSearching for similar events to 'team meeting':")
    similar = tools.search_similar_events("team meeting")
    for event in similar[:3]:  # Show first 3
        print(f"  - {event['document']} (similarity: {event.get('distance', 'N/A')})")


def example_7_multi_agent_workflow():
    """Example 7: Multi-agent collaboration workflow."""
    print("\n" + "="*60)
    print("Example 7: Multi-Agent Workflow")
    print("="*60)

    scheduler = SchedulerAgent()
    pattern_agent = PatternLearningAgent()

    # Step 1: Learn patterns
    print("\nStep 1: Pattern agent learns from history...")
    patterns = pattern_agent.learn_from_history(days_back=30)
    print(f"Learned {len(patterns)} patterns")

    # Step 2: Get recommendations
    print("\nStep 2: Get recommendations for 1-on-1 meetings...")
    recommendation = pattern_agent.suggest_optimal_time("1-on-1 meeting", 30)
    print(f"Recommendation: {recommendation}")

    # Step 3: Scheduler uses insights to find time
    print("\nStep 3: Scheduler finds optimal time slot...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    response = scheduler.find_time_for_meeting(
        meeting_description="1-on-1 with team member",
        duration_minutes=30,
        preferred_date=tomorrow
    )
    print(f"Available slots: {response}")


def example_8_conversational_agent():
    """Example 8: Conversational interaction with agent."""
    print("\n" + "="*60)
    print("Example 8: Conversational Agent Interaction")
    print("="*60)

    scheduler = SchedulerAgent()

    conversation = [
        "What do I have scheduled for tomorrow?",
        "When is my next meeting?",
        "Do I have any free time on Friday afternoon?",
    ]

    print("\nSimulating conversation with scheduler agent:")
    for message in conversation:
        print(f"\nUser: {message}")
        response = scheduler.run(message)
        print(f"Agent: {response}")
        print("-" * 40)


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("AI CALENDAR AGENT - EXAMPLE USAGE")
    print("="*60)
    print("\nThis script demonstrates key features and capabilities")
    print("of the AI Calendar Agent system.\n")

    examples = [
        ("Natural Language Scheduling", example_1_natural_language_scheduling),
        ("Smart Time Finding", example_2_smart_time_finding),
        ("Pattern Learning", example_3_pattern_learning),
        ("RAG Recommendations", example_4_rag_recommendations),
        ("Calendar Analysis", example_5_calendar_analysis),
        ("Direct Tool Usage", example_6_tool_usage),
        ("Multi-Agent Workflow", example_7_multi_agent_workflow),
        ("Conversational Agent", example_8_conversational_agent),
    ]

    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. Run all examples")

    choice = input("\nEnter your choice (0-8): ").strip()

    if choice == "0":
        for name, func in examples:
            try:
                func()
            except Exception as e:
                print(f"\nError in {name}: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        name, func = examples[int(choice) - 1]
        try:
            func()
        except Exception as e:
            print(f"\nError: {e}")
    else:
        print("Invalid choice")

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
