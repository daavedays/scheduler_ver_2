"""
Demo package for per-week closing assignment decisions.

This package is intentionally isolated from production code paths so we can
iterate on hard constraints, scoring, and validation with real worker data
before integrating.

Key entrypoints:
- selector.select_closers_for_week
- runner.run_demo
"""

from .types import (
    CandidateScore,
    DecisionLogEntry,
    WeekDecisionResult,
    Assignment,
)
from .policy import DecisionConfig, WeekContext
from .selector import select_closers_for_week

__all__ = [
    "CandidateScore",
    "DecisionLogEntry",
    "WeekDecisionResult",
    "Assignment",
    "DecisionConfig",
    "WeekContext",
    "select_closers_for_week",
]


