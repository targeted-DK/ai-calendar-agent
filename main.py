#!/usr/bin/env python3
"""
AI Calendar Agent - Main Entry Point

An intelligent calendar management system using AI agents and RAG.
"""

import os
import sys
from datetime import datetime, timedelta
from agents import SchedulerAgent, PatternLearningAgent
from config import settings


def print_header():
    """Print application header."""
    print("=" * 60)
    print("AI Calendar Agent".center(60))
    print("Intelligent Calendar Management with AI & RAG".center(60))
    print("=" * 60)
    print()


def check_configuration():
    """Check if required configuration is present."""
    issues = []

    # Check LLM API keys
    if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        issues.append("ANTHROPIC_API_KEY not set")
    elif settings.llm_provider == "openai" and not settings.openai_api_key:
        issues.append("OPENAI_API_KEY not set")

    # Check for .env file
    if not os.path.exists(".env"):
        issues.append(".env file not found (copy from .env.example)")

    # Check for Google Calendar credentials
    if not os.path.exists(settings.google_calendar_credentials_path):
        issues.append(
            f"Google Calendar credentials not found at {settings.google_calendar_credentials_path}\n"
            "  Download from: https://console.cloud.google.com/apis/credentials"
        )

    if issues:
        print("Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before running the agent.")
        return False

    return True


def interactive_mode():
    """Run the agent in interactive mode."""
    print_header()

    if not check_configuration():
        return

    print(f"Using LLM Provider: {settings.llm_provider}")
    print(f"Model: {getattr(settings, f'{settings.llm_provider}_model')}")
    print()

    # Initialize agents
    print("Initializing AI agents...")
    scheduler = SchedulerAgent()
    pattern_learner = PatternLearningAgent()
    print("Agents initialized successfully!")
    print()

    # Main menu
    while True:
        print("\nWhat would you like to do?")
        print("1. Schedule an event (natural language)")
        print("2. Find available time slots")
        print("3. View upcoming events")
        print("4. Analyze calendar patterns")
        print("5. Get scheduling recommendations")
        print("6. Learn from calendar history")
        print("7. Chat with scheduler agent")
        print("8. Exit")
        print()

        choice = input("Enter your choice (1-8): ").strip()

        if choice == "1":
            request = input("\nDescribe the event you want to schedule: ")
            print("\nProcessing...")
            response = scheduler.schedule_event(request)
            print(f"\n{response}")

        elif choice == "2":
            date = input("\nEnter date (YYYY-MM-DD) or press Enter for tomorrow: ").strip()
            if not date:
                date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            duration = input("Enter required duration in minutes (default: 60): ").strip()
            duration = int(duration) if duration else 60

            request = f"Find available time slots on {date} for a {duration} minute meeting"
            print("\nSearching for available slots...")
            response = scheduler.run(request)
            print(f"\n{response}")

        elif choice == "3":
            days = input("\nNumber of days to look ahead (default: 7): ").strip()
            days = int(days) if days else 7

            request = f"Show me my upcoming events for the next {days} days"
            print("\nFetching events...")
            response = scheduler.run(request)
            print(f"\n{response}")

        elif choice == "4":
            print("\nAnalyzing your calendar patterns...")
            response = scheduler.analyze_calendar_patterns()
            print(f"\n{response}")

        elif choice == "5":
            query = input("\nWhat kind of event do you need recommendations for? ")
            print("\nGenerating recommendations based on your patterns...")
            response = pattern_learner.get_recommendations(query)
            print(f"\n{response}")

        elif choice == "6":
            days = input("\nHow many days of history to analyze (default: 90)? ").strip()
            days = int(days) if days else 90

            print(f"\nLearning from {days} days of calendar history...")
            print("This may take a moment...")

            patterns = pattern_learner.learn_from_history(days)

            print("\nLearned patterns:")
            for pattern_id, pattern_data in patterns.items():
                print(f"\n{pattern_id}:")
                print(f"  {pattern_data['description']}")

            print(f"\n{len(patterns)} patterns learned and stored in RAG system!")

        elif choice == "7":
            print("\nChat with Scheduler Agent (type 'back' to return to menu)")
            print("-" * 60)

            while True:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['back', 'exit', 'quit']:
                    break

                if not user_input:
                    continue

                print("\nAgent: ", end="", flush=True)
                response = scheduler.run(user_input)
                print(response)

        elif choice == "8":
            print("\nThank you for using AI Calendar Agent!")
            break

        else:
            print("\nInvalid choice. Please try again.")


def demo_mode():
    """Run a quick demo of the system."""
    print_header()
    print("DEMO MODE - Demonstrating AI Calendar Agent capabilities")
    print()

    if not check_configuration():
        return

    print("Initializing agents...")
    scheduler = SchedulerAgent()
    print("Scheduler agent ready!")
    print()

    # Demo 1: Get upcoming events
    print("Demo 1: Checking upcoming events")
    print("-" * 60)
    response = scheduler.run("Show me my events for the next 7 days")
    print(response)
    print()

    # Demo 2: Find free slots
    print("\nDemo 2: Finding available time slots")
    print("-" * 60)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    response = scheduler.run(f"Find me free 30-minute slots on {tomorrow}")
    print(response)
    print()

    # Demo 3: Calendar statistics
    print("\nDemo 3: Calendar usage statistics")
    print("-" * 60)
    response = scheduler.run("Give me statistics about my calendar usage for the past 30 days")
    print(response)
    print()

    print("\nDemo complete!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        interactive_mode()
