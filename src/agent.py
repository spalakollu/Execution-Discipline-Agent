import pandas as pd
from typing import Dict
from .schemas import DisciplineReport, Violation
from .rules import check_regime_allowed, check_missing_stops, check_oversized_for_regime, check_r_multiple
from .memory import load_memory, save_memory


class ExecutionDisciplineAgent:
    def __init__(self, memory_path="state/memory.json"):
        self.memory_path = memory_path
        self.memory = load_memory(memory_path)
    
    def _calculate_compliance_trend(self) -> str:
        """
        Calculate compliance trend over the last 5 runs.
        Returns: 'improving', 'worsening', or 'flat'
        """
        history = self.memory.get("history", [])
        
        if len(history) < 2:
            return "flat"  # Not enough data
        
        # Get last 5 compliance scores (or all if less than 5)
        scores = [entry.get("compliance_score", 0.0) for entry in history[-5:]]
        
        if len(scores) < 2:
            return "flat"
        
        # Simple trend: compare average of first half vs second half
        # For 5 scores: compare first 2 vs last 3
        # For fewer scores: compare first half vs second half
        mid_point = len(scores) // 2
        
        if len(scores) >= 4:
            # Use first half vs second half
            first_half = scores[:mid_point]
            second_half = scores[mid_point:]
        else:
            # For 2-3 scores, compare first vs last
            first_half = scores[:1]
            second_half = scores[-1:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        # Determine trend with a small threshold to avoid noise
        threshold = 0.02  # 2% change threshold
        
        if avg_second > avg_first + threshold:
            return "improving"
        elif avg_second < avg_first - threshold:
            return "worsening"
        else:
            return "flat"

    def run(
        self,
        trades: pd.DataFrame,
        plan: Dict,
        regime_label: str
    ) -> DisciplineReport:

        violations = []

        # Regime check
        violations += check_regime_allowed(
            trades,
            plan["allowed_regimes"],
            regime_label
        )

        # Stop compliance
        if plan.get("stop_required", False):
            violations += check_missing_stops(trades)

        # Regime-aware sizing compliance
        account_size = float(plan.get("account_size", 0) or 0)
        position_limits_by_regime = plan.get("position_limits_by_regime", {}) or {}
        violations += check_oversized_for_regime(
            trades,
            account_size=account_size,
            position_limits_by_regime=position_limits_by_regime,
            current_regime=regime_label
        )

        # R-multiple check (Early Exit, Late Exit)
        violations += check_r_multiple(trades)

        compliance_score = 1.0 - (len(violations) / max(len(trades), 1))
        compliance_score = max(0.0, round(compliance_score, 2))

        regime_mismatch_rate = (
            len([v for v in violations if v.violation_type == "Regime Mismatch"])
            / max(len(trades), 1)
        )

        # Aggregate violations by violation_type
        violation_summary = {}
        for violation in violations:
            violation_type = violation.violation_type
            violation_summary[violation_type] = violation_summary.get(violation_type, 0) + 1

        # Save current run to memory before calculating trend
        self.memory["history"].append({
            "compliance_score": compliance_score,
            "violations": [v.__dict__ for v in violations],
            "violation_summary": violation_summary
        })
        save_memory(self.memory_path, self.memory)

        # Calculate compliance trend (includes current run)
        compliance_trend = self._calculate_compliance_trend()

        report = DisciplineReport(
            compliance_score=compliance_score,
            violations=violations,
            regime_mismatch_rate=round(regime_mismatch_rate, 2),
            violation_summary=violation_summary,
            compliance_trend=compliance_trend
        )

        return report
