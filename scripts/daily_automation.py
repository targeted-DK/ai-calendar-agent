#!/usr/bin/env python3
"""
Continuous Automation Script - Runs health monitoring and calendar optimization

This script:
1. Imports latest Garmin data (smart caching - only imports when needed)
2. Analyzes health status and recovery
3. Builds rich context from historical patterns
4. Optimizes calendar based on current condition
5. Logs all actions for transparency

Can be run:
- Via cron every 30 mins: */30 * * * * /path/to/daily_automation.py
- Via systemd timer (recommended for production)
- Manually: python scripts/daily_automation.py

Smart Import Logic:
- Only imports from Garmin once per day (or if >6 hours since last import)
- Always analyzes health and optimizes calendar (fast, no API calls)
"""
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
import json
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.garmin_connector import GarminConnector
from agents.pattern_learning_agent import create_pattern_learning_agent
from agents.health_monitor_agent import create_health_monitor
from database.connection import Database, log_agent_action
from scripts.import_garmin_data import import_health_data, import_activities


def log(message: str, level: str = "INFO"):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def should_import_data() -> bool:
    """Check if we should import data (avoid rate limiting)."""
    cache_file = Path.home() / '.local' / 'share' / 'ai-calendar-agent' / 'last_import.json'

    if not cache_file.exists():
        return True  # Never imported before

    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)

        last_import = datetime.fromisoformat(cache['timestamp'])
        hours_since = (datetime.now() - last_import).total_seconds() / 3600

        # Import if:
        # 1. More than 6 hours since last import, OR
        # 2. It's a new day and we haven't imported today
        if hours_since > 6:
            log(f"⏰ {hours_since:.1f} hours since last import - importing now", "INFO")
            return True

        if cache.get('date') != date.today().isoformat():
            log(f"📅 New day detected - importing fresh data", "INFO")
            return True

        log(f"⏭️  Skipping import (last import: {hours_since:.1f}h ago)", "INFO")
        return False

    except Exception as e:
        log(f"⚠️  Cache error: {e} - importing anyway", "WARN")
        return True


def update_import_cache():
    """Update last import timestamp."""
    cache_file = Path.home() / '.local' / 'share' / 'ai-calendar-agent' / 'last_import.json'
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with open(cache_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'date': date.today().isoformat()
        }, f)


def import_latest_garmin_data(force: bool = False) -> dict:
    """
    Import latest Garmin data (yesterday + recent activities).

    Args:
        force: Force import even if recently imported

    Returns:
        Dict with import results
    """
    log("=" * 60)
    log("STEP 1: Importing Garmin Data")
    log("=" * 60)

    # Check if we should import (smart caching)
    if not force and not should_import_data():
        return {
            'status': 'skipped',
            'reason': 'Recent import exists',
            'total_imported': 0
        }

    try:
        connector = GarminConnector()

        if not connector._authenticated:
            log("⚠️  Using mock data - no Garmin credentials configured", "WARN")

        # Import yesterday's health data + last 2 days (in case we missed a day)
        log("📊 Importing health metrics (last 3 days)...")
        health_stats = import_health_data(connector, days=3)

        # Import recent activities (last 7 days)
        log("🏃 Importing activities (last 7 days)...")
        activity_stats = import_activities(connector, days=7)

        total_imported = health_stats['success'] + activity_stats['success']
        total_skipped = health_stats['skipped'] + activity_stats['skipped']
        total_errors = health_stats['errors'] + activity_stats['errors']

        log(f"✅ Import complete: {total_imported} new, {total_skipped} skipped, {total_errors} errors")

        # Update cache
        update_import_cache()

        return {
            'status': 'success',
            'health': health_stats,
            'activities': activity_stats,
            'total_imported': total_imported
        }

    except Exception as e:
        log(f"❌ Import failed: {e}", "ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }


def analyze_current_health() -> dict:
    """Analyze current health status and recovery."""
    log("=" * 60)
    log("STEP 2: Analyzing Health Status")
    log("=" * 60)

    try:
        health_agent = create_health_monitor()

        # Get yesterday's health check
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        health_check = health_agent.check_health(yesterday)

        recovery_score = health_check['recovery_score']
        requires_action = health_check['requires_action']

        log(f"📊 Recovery Score: {recovery_score:.1f}/100")

        if recovery_score < 40:
            log("🔴 CRITICAL - Poor recovery detected", "WARN")
        elif recovery_score < 60:
            log("🟡 FAIR - Reduced recovery", "WARN")
        elif recovery_score < 80:
            log("🟢 GOOD - Normal recovery", "INFO")
        else:
            log("✅ EXCELLENT - High recovery", "INFO")

        return {
            'status': 'success',
            'recovery_score': recovery_score,
            'requires_action': requires_action,
            'analysis': health_check['analysis']
        }

    except Exception as e:
        log(f"❌ Health analysis failed: {e}", "ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }


def build_rich_context(recovery_score: float) -> dict:
    """Build rich context from historical patterns."""
    log("=" * 60)
    log("STEP 3: Building Context from Historical Data")
    log("=" * 60)

    try:
        pattern_agent = create_pattern_learning_agent()

        # Build context based on current situation
        situation = f"Recovery score {recovery_score:.1f}/100. Analyzing optimal schedule for today."

        log("🧠 Analyzing 30 days of historical patterns...")
        context = pattern_agent.build_rich_context(
            situation_query=situation,
            days_lookback=30
        )

        log("✅ Context built successfully")

        return {
            'status': 'success',
            'context': context
        }

    except Exception as e:
        log(f"❌ Context building failed: {e}", "ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }


def optimize_calendar(recovery_score: float, context: dict) -> dict:
    """Optimize calendar based on health status and context."""
    log("=" * 60)
    log("STEP 4: Calendar Optimization")
    log("=" * 60)

    # TODO: This will use SchedulerOptimizerAgent when implemented
    # For now, we'll log recommendations

    try:
        recommendations = []

        if recovery_score < 40:
            recommendations.append({
                'action': 'reschedule_non_critical',
                'reason': 'Critical recovery level - minimize stress',
                'confidence': 95
            })
            recommendations.append({
                'action': 'add_recovery_block',
                'details': 'Add 2-hour recovery block in afternoon',
                'confidence': 90
            })
            log("🔴 RECOMMENDATION: Aggressive schedule reduction needed", "WARN")

        elif recovery_score < 60:
            recommendations.append({
                'action': 'reduce_meeting_density',
                'reason': 'Fair recovery - reduce load by 30%',
                'confidence': 85
            })
            recommendations.append({
                'action': 'add_breaks',
                'details': 'Ensure 15-min breaks between meetings',
                'confidence': 80
            })
            log("🟡 RECOMMENDATION: Reduce meeting density", "INFO")

        elif recovery_score >= 80:
            recommendations.append({
                'action': 'can_handle_high_load',
                'reason': 'Excellent recovery - can optimize for productivity',
                'confidence': 90
            })
            log("✅ RECOMMENDATION: High performance day - maintain current schedule", "INFO")

        else:
            log("🟢 RECOMMENDATION: Normal schedule maintained", "INFO")

        # Log action to database
        for rec in recommendations:
            try:
                log_agent_action(
                    agent_name='DailyAutomation',
                    action_type=rec['action'],
                    data={
                        'confidence_score': rec.get('confidence'),
                        'reasoning': rec.get('reason'),
                        'data_sources': json.dumps({'recovery_score': recovery_score}),
                        'executed': False  # Not auto-executing yet
                    }
                )
            except Exception as e:
                log(f"⚠️  Failed to log action to database: {e}", "WARN")

        log(f"📝 Generated {len(recommendations)} recommendations")

        return {
            'status': 'success',
            'recommendations': recommendations
        }

    except Exception as e:
        log(f"❌ Calendar optimization failed: {e}", "ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }


def generate_summary(results: dict) -> str:
    """Generate human-readable summary."""
    summary = []
    summary.append("\n" + "=" * 60)
    summary.append("DAILY AUTOMATION SUMMARY")
    summary.append("=" * 60)

    # Import results
    if results['import']['status'] == 'success':
        summary.append(f"✅ Data Import: {results['import']['total_imported']} new records")
    elif results['import']['status'] == 'skipped':
        summary.append(f"⏭️  Data Import: {results['import']['reason']}")
    else:
        summary.append(f"❌ Data Import: Failed")

    # Health analysis
    if results['health']['status'] == 'success':
        score = results['health']['recovery_score']
        summary.append(f"📊 Recovery Score: {score:.1f}/100")
    else:
        summary.append(f"❌ Health Analysis: Failed")

    # Context
    if results['context']['status'] == 'success':
        summary.append(f"🧠 Historical Context: Built successfully")
    else:
        summary.append(f"❌ Context Building: Failed")

    # Optimization
    if results['optimization']['status'] == 'success':
        rec_count = len(results['optimization']['recommendations'])
        summary.append(f"📝 Recommendations: {rec_count} actions suggested")
    else:
        summary.append(f"❌ Optimization: Failed")

    summary.append("=" * 60)
    summary.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("=" * 60 + "\n")

    return "\n".join(summary)


def main():
    """Main automation workflow."""
    log("🚀 Starting Daily Automation")
    log(f"📅 Date: {date.today().isoformat()}")
    log(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")

    # Initialize database
    Database.initialize_pool()

    results = {
        'import': {},
        'health': {},
        'context': {},
        'optimization': {}
    }

    # Step 1: Import latest Garmin data
    results['import'] = import_latest_garmin_data()

    if results['import']['status'] == 'error':
        log("⚠️  Import failed, continuing with existing data", "WARN")

    # Step 2: Analyze health
    results['health'] = analyze_current_health()

    if results['health']['status'] == 'error':
        log("❌ Cannot continue without health analysis", "ERROR")
        return 1

    recovery_score = results['health']['recovery_score']

    # Step 3: Build context
    results['context'] = build_rich_context(recovery_score)

    # Step 4: Optimize calendar
    results['optimization'] = optimize_calendar(
        recovery_score,
        results['context'].get('context')
    )

    # Generate and print summary
    summary = generate_summary(results)
    print(summary)

    # Save results to file for review
    results_file = Path.home() / '.local' / 'share' / 'ai-calendar-agent' / 'daily_automation.json'
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump({
            'date': date.today().isoformat(),
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)

    log(f"💾 Results saved to: {results_file}")

    return 0 if all(r.get('status') != 'error' for r in results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
