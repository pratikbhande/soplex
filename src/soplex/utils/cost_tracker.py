"""
Cost tracking and analysis for soplex.
Tracks LLM vs CODE call costs and calculates savings.
"""
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from ..runtime.state import ExecutionState


@dataclass
class SessionCostData:
    """Cost data for a single execution session."""
    session_id: str
    sop_name: str
    timestamp: str
    duration_seconds: float

    # Step counts
    total_steps: int
    llm_steps: int
    code_steps: int
    hybrid_steps: int
    branch_steps: int

    # Cost breakdown
    total_cost: float
    llm_cost: float
    code_cost: float
    pure_llm_cost: float  # What it would cost with pure LLM

    # Token usage
    total_tokens: int
    llm_calls: int
    code_calls: int

    # Efficiency metrics
    savings_amount: float
    savings_percent: float

    # Provider info
    provider: str
    model: str

    # Execution info
    status: str
    errors: int
    warnings: int


class CostTracker:
    """
    Tracks and analyzes costs across multiple SOP executions.
    Provides insights into savings and efficiency.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize cost tracker with optional storage directory."""
        self.storage_dir = storage_dir or Path.home() / ".soplex" / "cost_data"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.sessions_file = self.storage_dir / "sessions.jsonl"

    def record_session(
        self,
        state: ExecutionState,
        sop_name: str,
        provider: str = "unknown",
        model: str = "unknown"
    ) -> SessionCostData:
        """
        Record costs from an execution session.

        Args:
            state: Execution state with cost data
            sop_name: Name of the SOP that was executed
            provider: LLM provider used
            model: Model used

        Returns:
            SessionCostData object
        """
        summary = state.get_summary()

        # Calculate what pure LLM would have cost
        pure_llm_cost = self._calculate_pure_llm_cost(
            total_steps=summary["steps_executed"],
            provider=provider,
            model=model
        )

        # Calculate savings
        actual_cost = summary["costs"]["total_cost"]
        savings_amount = pure_llm_cost - actual_cost
        savings_percent = (savings_amount / pure_llm_cost * 100) if pure_llm_cost > 0 else 0.0

        session_data = SessionCostData(
            session_id=state.session_id,
            sop_name=sop_name,
            timestamp=datetime.now().isoformat(),
            duration_seconds=summary["duration_seconds"],
            total_steps=summary["steps_executed"],
            llm_steps=summary["usage"].get("llm_calls", 0),
            code_steps=summary["usage"].get("code_calls", 0),
            hybrid_steps=0,  # TODO: Track hybrid steps separately
            branch_steps=0,  # TODO: Track branch steps separately
            total_cost=actual_cost,
            llm_cost=summary["costs"]["llm_cost"],
            code_cost=summary["costs"]["code_cost"],
            pure_llm_cost=pure_llm_cost,
            total_tokens=summary["usage"]["total_tokens"],
            llm_calls=summary["usage"]["llm_calls"],
            code_calls=summary["usage"]["code_calls"],
            savings_amount=savings_amount,
            savings_percent=savings_percent,
            provider=provider,
            model=model,
            status=summary["status"],
            errors=summary["errors"],
            warnings=summary["warnings"],
        )

        # Store the session data
        self._store_session(session_data)

        return session_data

    def get_aggregate_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregate statistics for recent sessions.

        Args:
            days: Number of days to look back

        Returns:
            Aggregate statistics
        """
        recent_sessions = self._load_recent_sessions(days)

        if not recent_sessions:
            return {
                "total_sessions": 0,
                "total_savings": 0.0,
                "average_savings_percent": 0.0,
                "total_cost": 0.0,
                "total_llm_calls": 0,
                "total_code_calls": 0,
                "average_duration": 0.0,
                "most_used_provider": "none",
                "most_used_model": "none",
                "error_rate": 0.0,
            }

        # Calculate aggregates
        total_sessions = len(recent_sessions)
        total_savings = sum(s.savings_amount for s in recent_sessions)
        total_cost = sum(s.total_cost for s in recent_sessions)
        total_llm_calls = sum(s.llm_calls for s in recent_sessions)
        total_code_calls = sum(s.code_calls for s in recent_sessions)
        total_duration = sum(s.duration_seconds for s in recent_sessions)

        # Calculate averages
        avg_savings_percent = sum(s.savings_percent for s in recent_sessions) / total_sessions
        avg_duration = total_duration / total_sessions

        # Count providers and models
        providers = {}
        models = {}
        failed_sessions = 0

        for session in recent_sessions:
            providers[session.provider] = providers.get(session.provider, 0) + 1
            models[session.model] = models.get(session.model, 0) + 1
            if session.status == "failed":
                failed_sessions += 1

        most_used_provider = max(providers.items(), key=lambda x: x[1])[0] if providers else "none"
        most_used_model = max(models.items(), key=lambda x: x[1])[0] if models else "none"
        error_rate = (failed_sessions / total_sessions * 100) if total_sessions > 0 else 0.0

        return {
            "total_sessions": total_sessions,
            "total_savings": round(total_savings, 6),
            "average_savings_percent": round(avg_savings_percent, 1),
            "total_cost": round(total_cost, 6),
            "total_llm_calls": total_llm_calls,
            "total_code_calls": total_code_calls,
            "average_duration": round(avg_duration, 2),
            "most_used_provider": most_used_provider,
            "most_used_model": most_used_model,
            "error_rate": round(error_rate, 1),
            "efficiency_ratio": round(total_code_calls / (total_llm_calls + total_code_calls) * 100, 1) if (total_llm_calls + total_code_calls) > 0 else 0.0,
        }

    def get_savings_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """
        Get detailed savings breakdown.

        Args:
            days: Number of days to analyze

        Returns:
            Detailed savings analysis
        """
        recent_sessions = self._load_recent_sessions(days)

        if not recent_sessions:
            return {"message": "No recent sessions found"}

        # Group by SOP
        sop_stats = {}
        for session in recent_sessions:
            sop_name = session.sop_name
            if sop_name not in sop_stats:
                sop_stats[sop_name] = {
                    "sessions": 0,
                    "total_savings": 0.0,
                    "total_cost": 0.0,
                    "avg_savings_percent": 0.0,
                    "llm_calls": 0,
                    "code_calls": 0,
                }

            stats = sop_stats[sop_name]
            stats["sessions"] += 1
            stats["total_savings"] += session.savings_amount
            stats["total_cost"] += session.total_cost
            stats["llm_calls"] += session.llm_calls
            stats["code_calls"] += session.code_calls

        # Calculate averages
        for sop_name, stats in sop_stats.items():
            sessions_for_sop = [s for s in recent_sessions if s.sop_name == sop_name]
            stats["avg_savings_percent"] = sum(s.savings_percent for s in sessions_for_sop) / len(sessions_for_sop)

        # Sort by total savings
        sorted_sops = sorted(sop_stats.items(), key=lambda x: x[1]["total_savings"], reverse=True)

        return {
            "analysis_period_days": days,
            "total_sessions": len(recent_sessions),
            "sop_breakdown": dict(sorted_sops),
            "top_saver": sorted_sops[0][0] if sorted_sops else None,
            "total_savings_all": sum(s.savings_amount for s in recent_sessions),
        }

    def export_data(self, output_file: Path, format: str = "json") -> None:
        """
        Export all cost data to a file.

        Args:
            output_file: Output file path
            format: Export format ("json" or "csv")
        """
        all_sessions = self._load_all_sessions()

        if format.lower() == "json":
            with open(output_file, 'w') as f:
                json.dump([asdict(session) for session in all_sessions], f, indent=2)

        elif format.lower() == "csv":
            import csv

            if not all_sessions:
                return

            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(all_sessions[0]).keys())
                writer.writeheader()
                for session in all_sessions:
                    writer.writerow(asdict(session))
        else:
            raise ValueError(f"Unsupported format: {format}")

    def clear_data(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear stored cost data.

        Args:
            older_than_days: Only clear data older than this many days. If None, clear all.

        Returns:
            Number of sessions cleared
        """
        if older_than_days is None:
            # Clear all data
            if self.sessions_file.exists():
                self.sessions_file.unlink()
            return -1  # Unknown count since we deleted the whole file

        # Clear only old data
        all_sessions = self._load_all_sessions()
        cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)

        kept_sessions = []
        cleared_count = 0

        for session in all_sessions:
            session_time = datetime.fromisoformat(session.timestamp).timestamp()
            if session_time >= cutoff_time:
                kept_sessions.append(session)
            else:
                cleared_count += 1

        # Rewrite file with kept sessions
        if kept_sessions:
            with open(self.sessions_file, 'w') as f:
                for session in kept_sessions:
                    f.write(json.dumps(asdict(session)) + '\n')
        elif self.sessions_file.exists():
            self.sessions_file.unlink()

        return cleared_count

    def _calculate_pure_llm_cost(self, total_steps: int, provider: str, model: str) -> float:
        """Calculate what pure LLM approach would cost."""
        from ..config import PRICING

        # Estimate tokens per step for pure LLM
        avg_tokens_per_step = 200  # Conservative estimate

        total_tokens = total_steps * avg_tokens_per_step
        pricing = PRICING.get(model, {"input": 0.15, "output": 0.60})  # Default to gpt-4o-mini

        # Assume 70% input, 30% output tokens
        input_tokens = total_tokens * 0.7
        output_tokens = total_tokens * 0.3

        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

        return cost

    def _store_session(self, session_data: SessionCostData) -> None:
        """Store session data to file."""
        with open(self.sessions_file, 'a') as f:
            f.write(json.dumps(asdict(session_data)) + '\n')

    def _load_recent_sessions(self, days: int) -> List[SessionCostData]:
        """Load sessions from the last N days."""
        all_sessions = self._load_all_sessions()
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        recent_sessions = []
        for session in all_sessions:
            session_time = datetime.fromisoformat(session.timestamp).timestamp()
            if session_time >= cutoff_time:
                recent_sessions.append(session)

        return recent_sessions

    def _load_all_sessions(self) -> List[SessionCostData]:
        """Load all stored sessions."""
        if not self.sessions_file.exists():
            return []

        sessions = []
        try:
            with open(self.sessions_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        sessions.append(SessionCostData(**data))
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or missing, return empty list
            pass

        return sessions


# Global cost tracker instance
_global_tracker = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker()
    return _global_tracker


def record_session_costs(
    state: ExecutionState,
    sop_name: str,
    provider: str = "unknown",
    model: str = "unknown"
) -> SessionCostData:
    """Convenience function to record session costs."""
    tracker = get_cost_tracker()
    return tracker.record_session(state, sop_name, provider, model)