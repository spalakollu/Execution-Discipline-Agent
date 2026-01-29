from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Violation:
    trade_index: int
    violation_type: str
    detail: str

@dataclass
class DisciplineReport:
    compliance_score: float
    violations: List[Violation]
    regime_mismatch_rate: float

def to_dict(obj):
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return obj
