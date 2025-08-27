from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple


@dataclass
class CandidateScore:
    worker_id: str
    base: float
    proximity_bonus: float
    spacing_bonus: float
    scarcity_penalty: float
    fairness_adjustment: float
    total: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class DecisionLogEntry:
    worker_id: str
    message: str
    data: Dict[str, float] = field(default_factory=dict)


@dataclass
class Assignment:
    worker_id: str
    is_required: bool
    role: Optional[str] = None


@dataclass
class WeekDecisionResult:
    week_friday: date
    assignments: List[Assignment]
    candidate_scores: List[CandidateScore]
    logs: List[DecisionLogEntry]
    errors: List[str]


