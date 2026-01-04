"""
OrchestratorAgent - Main coordinator for the life optimization system

This is the "brain" that:
- Coordinates all other agents (HealthMonitor, SchedulerOptimizer, etc.)
- Runs the autonomous monitoring loop 24/7
- Makes high-level decisions based on health and patterns
- Handles scheduling and triggers
- Manages system state and logs

Autonomy Levels:
- observer: Only logs and suggests, never executes
- semi_autonomous: Executes with approval for critical actions
- autonomous: Fully autonomous with safety rules
"""
import time
import json
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, Any, Optional, List
from enum import Enum

from agents.health_monitor_agent import create_health_monitor
from agents.scheduler_optimizer_agent import create_scheduler_optimizer
from database.connection import Database, log_agent_action


class AutonomyLevel(Enum):
    """Agent autonomy levels."""
    OBSERVER = "observer"
    SEMI_AUTONOMOUS = "semi_autonomous"
    AUTONOMOUS = "autonomous"


class OrchestratorAgent:
    """
    Main orchestrator that coordinates all agents and runs the autonomous loop.

    This agent doesn't use LLM directly - it uses rule-based logic to decide
    when to trigger other agents. The specialized agents (HealthMonitor,
    SchedulerOptimizer) use LLMs for their specific tasks.
    """

    def __init__(self, autonomy_level: str = "observer", skip_calendar: bool = False):
        """
        Initialize the OrchestratorAgent.

        Args:
            autonomy_level: observer, semi_autonomous, or autonomous
            skip_calendar: Skip Google Calendar (for testing)
        """
        self.autonomy_level = AutonomyLevel(autonomy_level)
        self.skip_calendar = skip_calendar

        # Initialize database
        Database.initialize_pool()

        # Initialize sub-agents
        self.health_monitor = create_health_monitor()
        self.scheduler_optimizer = create_scheduler_optimizer(
            mode="observer" if autonomy_level == "observer" else "autonomous",
            skip_calendar=skip_calendar
        )

        # State tracking
        self.last_health_check = None
        self.last_schedule_optimization = None
        self.daily_decisions = []

        print(f"\n🧠 OrchestratorAgent initialized")
        print(f"   Autonomy Level: {self.autonomy_level.value.upper()}")
        print(f"   Sub-agents: HealthMonitor, SchedulerOptimizer")

        self._log_system_event("orchestrator_initialized", {
            "autonomy_level": autonomy_level,
            "skip_calendar": skip_calendar
        })

    def _log_system_event(self, event_type: str, data: Dict[str, Any]):
        """Log system events to database."""
        log_agent_action(
            agent_name="OrchestratorAgent",
            action_type=event_type,
            data=data
        )

    def check_health_and_decide(self) -> Dict[str, Any]:
        """
        Run health check and make decisions based on results.

        This is the core decision-making function that:
        1. Gets latest health metrics
        2. Analyzes against thresholds
        3. Decides what actions to take
        4. Triggers appropriate agents

        Returns:
            Dictionary with decisions and actions taken
        """
        print("\n" + "="*60)
        print("🏥 Running Health Check & Decision Making")
        print("="*60)

        try:
            # Get health data from database
            health_data = self._get_latest_health()

            if not health_data:
                print("⚠️  No health data available yet")
                return {
                    "success": False,
                    "reason": "no_health_data",
                    "recommendation": "Run health check first to collect data"
                }

            # Extract key metrics
            recovery_score = float(health_data.get('avg_recovery', 0))
            sleep_hours = float(health_data.get('avg_sleep', 0))
            stress_level = float(health_data.get('avg_stress', 0))

            print(f"\n📊 Current Health Metrics:")
            print(f"   Recovery Score: {recovery_score:.1f}/100")
            print(f"   Sleep: {sleep_hours:.1f} hours")
            print(f"   Stress: {stress_level:.1f}/100")

            # Decision logic based on health metrics
            decisions = []
            actions_taken = []

            # RULE 1: Low recovery score
            if recovery_score < 60:
                decision = {
                    "trigger": "low_recovery",
                    "recovery_score": recovery_score,
                    "action": "optimize_schedule_for_recovery",
                    "reasoning": f"Recovery score {recovery_score:.1f} is below threshold (60)"
                }
                decisions.append(decision)

                print(f"\n⚠️  Low Recovery Detected ({recovery_score:.1f}/100)")
                print(f"   Action: Optimize schedule for recovery")

                # Trigger schedule optimization
                if self.autonomy_level != AutonomyLevel.OBSERVER:
                    result = self.scheduler_optimizer.optimize_schedule(
                        days_ahead=3,
                        context=f"Low recovery score ({recovery_score:.1f}). Need rest and recovery time."
                    )
                    actions_taken.append(result)
                else:
                    print(f"   [OBSERVER MODE] Would optimize schedule")

            # RULE 2: Poor sleep
            elif sleep_hours < 6:
                decision = {
                    "trigger": "insufficient_sleep",
                    "sleep_hours": sleep_hours,
                    "action": "reduce_morning_load",
                    "reasoning": f"Sleep duration {sleep_hours:.1f}h is below threshold (6h)"
                }
                decisions.append(decision)

                print(f"\n😴 Insufficient Sleep Detected ({sleep_hours:.1f}h)")
                print(f"   Action: Reduce morning commitments")

                if self.autonomy_level != AutonomyLevel.OBSERVER:
                    result = self.scheduler_optimizer.optimize_schedule(
                        days_ahead=2,
                        context=f"Poor sleep ({sleep_hours:.1f}h). Reduce morning workload."
                    )
                    actions_taken.append(result)
                else:
                    print(f"   [OBSERVER MODE] Would reduce morning load")

            # RULE 3: High stress
            elif stress_level > 70:
                decision = {
                    "trigger": "high_stress",
                    "stress_level": stress_level,
                    "action": "add_breaks_and_buffer",
                    "reasoning": f"Stress level {stress_level:.1f} is above threshold (70)"
                }
                decisions.append(decision)

                print(f"\n😰 High Stress Detected ({stress_level:.1f}/100)")
                print(f"   Action: Add breaks between meetings")

                if self.autonomy_level != AutonomyLevel.OBSERVER:
                    result = self.scheduler_optimizer.optimize_schedule(
                        days_ahead=2,
                        context=f"High stress ({stress_level:.1f}). Add breaks and buffer time."
                    )
                    actions_taken.append(result)
                else:
                    print(f"   [OBSERVER MODE] Would add breaks")

            # RULE 4: Good recovery - optimize for productivity
            elif recovery_score > 80:
                decision = {
                    "trigger": "good_recovery",
                    "recovery_score": recovery_score,
                    "action": "schedule_important_work",
                    "reasoning": f"Recovery score {recovery_score:.1f} is excellent (>80)"
                }
                decisions.append(decision)

                print(f"\n💪 Excellent Recovery ({recovery_score:.1f}/100)")
                print(f"   Action: Schedule important/creative work")

                if self.autonomy_level != AutonomyLevel.OBSERVER:
                    result = self.scheduler_optimizer.optimize_schedule(
                        days_ahead=2,
                        context=f"Excellent recovery ({recovery_score:.1f}). Good time for important work."
                    )
                    actions_taken.append(result)
                else:
                    print(f"   [OBSERVER MODE] Would schedule important work")

            # RULE 5: Normal state - routine check
            else:
                decision = {
                    "trigger": "normal_state",
                    "action": "maintain_balance",
                    "reasoning": "All metrics within normal ranges"
                }
                decisions.append(decision)

                print(f"\n✅ All Metrics Normal")
                print(f"   Action: Maintain current balance")

            # Log decisions
            self._log_system_event("health_check_decisions", {
                "health_metrics": health_data,
                "decisions": decisions,
                "actions_taken": len(actions_taken),
                "autonomy_level": self.autonomy_level.value
            })

            self.last_health_check = datetime.now()
            self.daily_decisions.extend(decisions)

            return {
                "success": True,
                "health_metrics": health_data,
                "decisions": decisions,
                "actions_taken": actions_taken,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"\n❌ Error in health check: {e}")
            import traceback
            traceback.print_exc()

            self._log_system_event("health_check_error", {"error": str(e)})
            return {
                "success": False,
                "error": str(e)
            }

    def _get_latest_health(self) -> Optional[Dict[str, Any]]:
        """Get latest health metrics from database."""
        query = """
        SELECT * FROM recent_health_summary
        ORDER BY date DESC
        LIMIT 1
        """
        result = Database.execute_one(query)
        return dict(result) if result else None

    def run_daily_cycle(self) -> Dict[str, Any]:
        """
        Run a complete daily cycle:
        1. Collect health data
        2. Analyze and make decisions
        3. Generate daily summary

        Returns:
            Summary of daily cycle
        """
        print("\n" + "="*60)
        print("🌅 Running Daily Cycle")
        print("="*60)

        # Step 1: Collect fresh health data
        print("\n1️⃣  Collecting health data...")
        health_result = self.health_monitor.store_to_database()

        if not health_result.get('success'):
            print(f"   ❌ Failed to collect health data")
            return {"success": False, "step": "health_collection"}

        print(f"   ✅ Health data collected (Recovery: {health_result.get('recovery_score', 'N/A')})")

        # Step 2: Analyze and make decisions
        print("\n2️⃣  Analyzing health and making decisions...")
        decision_result = self.check_health_and_decide()

        if not decision_result.get('success'):
            print(f"   ❌ Decision making failed")
            return {"success": False, "step": "decision_making"}

        print(f"   ✅ Made {len(decision_result.get('decisions', []))} decisions")

        # Step 3: Generate summary
        print("\n3️⃣  Generating daily summary...")
        summary = self._generate_daily_summary(health_result, decision_result)

        print("\n" + "="*60)
        print("✅ Daily Cycle Complete")
        print("="*60)

        return {
            "success": True,
            "health_data": health_result,
            "decisions": decision_result,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_daily_summary(self, health_data: Dict, decisions: Dict) -> str:
        """Generate human-readable daily summary."""
        recovery = health_data.get('recovery_score', 'N/A')
        num_decisions = len(decisions.get('decisions', []))

        summary = f"""
Daily Life Optimization Summary
================================

Health Status:
- Recovery Score: {recovery}/100
- Status: {health_data.get('status', 'Unknown')}

Decisions Made: {num_decisions}
"""

        for i, decision in enumerate(decisions.get('decisions', []), 1):
            summary += f"\n{i}. {decision.get('action', 'Unknown')}"
            summary += f"\n   Reason: {decision.get('reasoning', '')}\n"

        summary += f"\nAutonomy Level: {self.autonomy_level.value}"
        summary += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return summary

    def run_continuous_loop(self, check_interval_hours: int = 24):
        """
        Run the orchestrator in continuous mode (24/7 monitoring).

        Args:
            check_interval_hours: How often to run the daily cycle

        WARNING: This will run indefinitely. Use Ctrl+C to stop.
        """
        print("\n" + "="*60)
        print("🔄 Starting Continuous Monitoring Loop")
        print("="*60)
        print(f"   Check Interval: Every {check_interval_hours} hours")
        print(f"   Autonomy: {self.autonomy_level.value.upper()}")
        print(f"   Press Ctrl+C to stop")
        print("="*60)

        try:
            while True:
                # Run daily cycle
                result = self.run_daily_cycle()

                if result.get('success'):
                    print(f"\n✅ Cycle complete. Next run in {check_interval_hours} hours.")
                else:
                    print(f"\n⚠️  Cycle had issues. Will retry in {check_interval_hours} hours.")

                # Sleep until next cycle
                sleep_seconds = check_interval_hours * 3600
                next_run = datetime.now() + timedelta(seconds=sleep_seconds)
                print(f"   Next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

                time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            print("\n\n🛑 Stopping continuous loop...")
            self._log_system_event("continuous_loop_stopped", {
                "last_check": self.last_health_check.isoformat() if self.last_health_check else None
            })
            print("✅ Orchestrator stopped gracefully")

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "autonomy_level": self.autonomy_level.value,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "last_schedule_optimization": self.last_schedule_optimization.isoformat() if self.last_schedule_optimization else None,
            "decisions_today": len(self.daily_decisions),
            "sub_agents": {
                "health_monitor": "active",
                "scheduler_optimizer": "active"
            }
        }


def create_orchestrator(autonomy_level: str = "observer",
                       skip_calendar: bool = False) -> OrchestratorAgent:
    """
    Factory function to create OrchestratorAgent.

    Args:
        autonomy_level: observer, semi_autonomous, or autonomous
        skip_calendar: Skip Google Calendar (for testing)

    Returns:
        Initialized OrchestratorAgent
    """
    return OrchestratorAgent(autonomy_level=autonomy_level, skip_calendar=skip_calendar)
