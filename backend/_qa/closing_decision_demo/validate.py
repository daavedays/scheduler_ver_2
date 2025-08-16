from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

try:
    from ..worker import EnhancedWorker
except Exception:
    from backend.worker import EnhancedWorker


def validate_min_gap(worker: EnhancedWorker) -> List[str]:
    errors: List[str] = []
    interval = max(2, worker.get_closing_interval())
    hist = sorted(worker.closing_history)
    for i in range(1, len(hist)):
        diff = (hist[i] - hist[i - 1]).days // 7
        if diff < interval:
            errors.append(f"Min-gap violated for {worker.name} between {hist[i-1].isoformat()} and {hist[i].isoformat()} (diff={diff}, n={interval})")
    return errors


def validate_no_conflicts(worker: EnhancedWorker) -> List[str]:
    errors: List[str] = []
    for d in worker.closing_history:
        if worker.has_x_task_on_date(d):
            errors.append(f"X-task conflict on closing date {d.isoformat()} for {worker.name}")
        if worker.has_y_task_scheduled(d) or worker.has_y_task_scheduled(d - timedelta(days=1)) or worker.has_y_task_scheduled(d + timedelta(days=1)):
            errors.append(f"Y-task conflict around weekend of {d.isoformat()} for {worker.name}")
    return errors


def validate_capacity(assignments: List[Tuple[str, str]], weekly_capacity: int) -> List[str]:
    # assignments: List[(role, worker_id)]
    if len(assignments) > weekly_capacity:
        return [f"Weekly capacity exceeded: {len(assignments)}>{weekly_capacity}"]
    return []


