from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

try:
    from ..worker import EnhancedWorker
    from ..engine import compute_qualification_scarcity, compute_worker_scarcity_index
except Exception:
    from backend.worker import EnhancedWorker
    from backend.engine import compute_qualification_scarcity, compute_worker_scarcity_index

from .policy import DecisionConfig, WeekContext
from .types import CandidateScore


def proximity_to_optimal_bonus(worker: EnhancedWorker, friday: date) -> Tuple[float, str]:
    if friday in getattr(worker, "optimal_closing_dates", []):
        return 1.0, "optimal_week"
    # Near-miss: +/- interval distance
    interval = max(2, worker.get_closing_interval())
    for delta in range(1, 3):
        for sign in (-1, 1):
            d = friday + timedelta(weeks=delta * sign)
            if d in getattr(worker, "optimal_closing_dates", []):
                return 0.5, f"near_optimal_{delta}w"
    return 0.0, "none"


def spacing_beyond_min_bonus(worker: EnhancedWorker, friday: date) -> Tuple[float, str]:
    if not worker.closing_history:
        return 0.0, "no_history"
    interval = max(2, worker.get_closing_interval())
    last = max(worker.closing_history)
    weeks_since = (friday - last).days // 7
    if weeks_since <= 0:
        return 0.0, "not_after"
    extra = max(0, weeks_since - interval)
    return min(1.0, extra * 0.25), f"extra_{extra}"


def compute_fairness_adjustment(worker: EnhancedWorker) -> Tuple[float, str]:
    # Lower score means higher priority in engine; here we invert to keep positive bonuses as positive priority
    # We normalize by simple clamp
    normalized = max(0.0, min(3.0, worker.score))
    # Convert existing score into a penalty; larger score => deprioritize
    return -normalized * 0.3, "score_based"


def compute_scarcity_penalty(worker: EnhancedWorker, workers: List[EnhancedWorker]) -> Tuple[float, str]:
    _, task_scarcity = compute_qualification_scarcity(workers)
    idx = compute_worker_scarcity_index(worker, task_scarcity)
    # Protect scarce workers by applying a penalty
    return idx, "scarcity_index"


def score_candidates(
    workers: List[EnhancedWorker],
    candidates: List[EnhancedWorker],
    ctx: WeekContext,
    cfg: DecisionConfig,
) -> List[CandidateScore]:
    friday = ctx.week_friday
    scored: List[CandidateScore] = []

    for w in candidates:
        prox, prox_r = proximity_to_optimal_bonus(w, friday)
        space, space_r = spacing_beyond_min_bonus(w, friday)
        fair, fair_r = compute_fairness_adjustment(w)
        scarcity, scarcity_r = compute_scarcity_penalty(w, workers)

        total = (
            cfg.weight_proximity * prox +
            cfg.weight_spacing_beyond_min * space +
            cfg.weight_fairness * fair -
            cfg.weight_scarcity_protect * scarcity
        )

        scored.append(CandidateScore(
            worker_id=w.id,
            base=0.0,
            proximity_bonus=prox,
            spacing_bonus=space,
            scarcity_penalty=scarcity,
            fairness_adjustment=fair,
            total=total,
            reasons=[prox_r, space_r, fair_r, scarcity_r]
        ))

    # Stable deterministic ordering by (-score, worker_id)
    scored.sort(key=lambda s: (-s.total, s.worker_id))
    return scored


