import pandas as pd
from typing import List
from .schemas import Violation

def check_regime_allowed(
    trades: pd.DataFrame,
    allowed_regimes: List[str],
    current_regime: str
) -> List[Violation]:
    violations = []
    if current_regime not in allowed_regimes:
        for i in range(len(trades)):
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Regime Mismatch",
                    detail=f"Trade taken during {current_regime} regime"
                )
            )
    return violations

def check_missing_stops(trades: pd.DataFrame) -> List[Violation]:
    violations = []
    for i, row in trades.iterrows():
        if pd.isna(row.get("stop_price")):
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Missing Stop",
                    detail="Stop required but not provided"
                )
            )
    return violations
