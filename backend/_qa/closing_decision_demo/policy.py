from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

try:
    from ..worker import EnhancedWorker
except Exception:
    from backend.worker import EnhancedWorker


@dataclass
class DecisionConfig:
    # Hard constraints
    enforce_min_gap: bool = True
    enforce_availability: bool = True
    enforce_qualification: bool = True
    enforce_conflict_with_xy: bool = True
    weekly_capacity: int = 2
    role_capacity: Optional[Dict[str, int]] = None

    # Soft preferences
    weight_proximity: float = 2.0
    weight_spacing_beyond_min: float = 0.5
    weight_scarcity_protect: float = 1.0
    weight_fairness: float = 1.0

    # Operational
    deterministic_tie_break: bool = True


class WeekContext:
    def __init__(self, week_friday: date, semester_weeks: List[date]):
        self.week_friday = week_friday
        self.semester_weeks = semester_weeks

    def week_index(self) -> int:
        try:
            return self.semester_weeks.index(self.week_friday)
        except ValueError:
            return -1


def get_required_closers_for_week(workers: List[EnhancedWorker], friday: date) -> List[EnhancedWorker]:
    return [w for w in workers if friday in getattr(w, "required_closing_dates", []) and w.can_participate_in_closing()]


def is_worker_available_for_closing(worker: EnhancedWorker, friday: date) -> bool:
    # Availability/eligibility: X-task on same day blocks; Y-task rules: weekday Y ok, weekend Y conflicts via engine
    if worker.has_x_task_on_date(friday):
        return False
    # Conflicts with Y tasks across weekend: consider Thu/Fri/Sat
    for delta in (0, -1, 1):
        d = friday + timedelta(days=delta)
        if worker.has_y_task_scheduled(d):
            return False
    return True


def respects_min_gap(worker: EnhancedWorker, friday: date) -> bool:
    interval = max(2, worker.get_closing_interval())
    if not worker.closing_history:
        return True
    # Enforce: difference between any two closes ≥ interval weeks
    for prev in worker.closing_history:
        diff_weeks = abs((friday - prev).days) // 7
        if diff_weeks < interval:
            return False
    return True


def is_qualified_for_role(worker: EnhancedWorker, role: Optional[str]) -> bool:
    if role is None:
        return True
    return role in (worker.qualifications or [])


def respects_required_anchor_spacing(worker: EnhancedWorker, friday: date) -> bool:
    """Ensure adding a close on 'friday' does not violate min-gap vs any required anchor.

    For each required closing date (X-task) for this worker, the absolute week
    difference must be at least the interval, unless the anchor is exactly the same
    date (i.e., the week is itself required).
    """
    interval = max(2, worker.get_closing_interval())
    anchors = getattr(worker, "required_closing_dates", []) or []
    if not anchors:
        return True
    for a in anchors:
        if a == friday:
            continue  # allowed, will be handled as required
        diff_weeks = abs((friday - a).days) // 7
        if diff_weeks < interval:
            return False
    return True

