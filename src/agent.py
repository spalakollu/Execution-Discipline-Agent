import pandas as pd
from typing import Dict
from .schemas import DisciplineReport, Violation
from .rules import check_regime_allowed, check_missing_stops
from .memory import load_memory, save_memory


class ExecutionDisciplineAgent:
    def __init__(self, memory_path="state/memory.json"):
        self.memory_path = memory_path
        self.memory = load_memory(memory_path)

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

        # Stop check
        if plan.get("stop_required", False):
            violations += check_missing_stops(trades)

        compliance_score = 1.0 - (len(violations) / max(len(trades), 1))
        compliance_score = max(0.0, round(compliance_score, 2))

        regime_mismatch_rate = (
            len([v for v in violations if v.violation_type == "Regime Mismatch"])
            / max(len(trades), 1)
        )

        report = DisciplineReport(
            compliance_score=compliance_score,
            violations=violations,
            regime_mismatch_rate=round(regime_mismatch_rate, 2)
        )

        self.memory["history"].append({
            "compliance_score": compliance_score,
            "violations": [v.__dict__ for v in violations]
        })

        save_memory(self.memory_path, self.memory)

        return report
