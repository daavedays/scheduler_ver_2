from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

try:
    from ..worker import EnhancedWorker
except Exception:
    from backend.worker import EnhancedWorker

from .policy import (
    DecisionConfig,
    WeekContext,
    is_worker_available_for_closing,
    respects_min_gap,
    is_qualified_for_role,
)


def compute_eligible_workers(
    workers: List[EnhancedWorker],
    ctx: WeekContext,
    cfg: DecisionConfig,
    role: Optional[str] = None,
) -> List[EnhancedWorker]:
    friday = ctx.week_friday
    eligible: List[EnhancedWorker] = []

    for w in workers:
        if not w.can_participate_in_closing():
            continue
        if cfg.enforce_availability and not is_worker_available_for_closing(w, friday):
            continue
        if cfg.enforce_min_gap and not respects_min_gap(w, friday):
            continue
        if cfg.enforce_qualification and not is_qualified_for_role(w, role):
            continue
        eligible.append(w)

    return eligible


