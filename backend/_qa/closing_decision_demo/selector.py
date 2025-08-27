from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

try:
    from ..worker import EnhancedWorker
    from ..engine import Y_TASK_TYPES
except Exception:
    from backend.worker import EnhancedWorker
    from backend.engine import Y_TASK_TYPES

from .types import Assignment, CandidateScore, DecisionLogEntry, WeekDecisionResult
from .policy import DecisionConfig, WeekContext, get_required_closers_for_week, respects_required_anchor_spacing
from .eligibility import compute_eligible_workers
from .scoring import score_candidates
from .validate import validate_capacity, validate_min_gap, validate_no_conflicts


def select_closers_for_week(
    workers: List[EnhancedWorker],
    week_friday: date,
    semester_weeks: List[date],
    cfg: Optional[DecisionConfig] = None,
    roles_needed: Optional[List[str]] = None,
) -> WeekDecisionResult:
    cfg = cfg or DecisionConfig()
    ctx = WeekContext(week_friday, semester_weeks)
    logs: List[DecisionLogEntry] = []
    errors: List[str] = []

    # Determine required closers from X tasks
    required = get_required_closers_for_week(workers, week_friday)
    roles_needed = roles_needed or []

    # Weekly capacity derived from roles needed if provided
    weekly_capacity = cfg.weekly_capacity
    if roles_needed:
        weekly_capacity = min(weekly_capacity, len(roles_needed))

    assignments: List[Assignment] = []

    # 1) Place required closers first
    for w in required:
        assignments.append(Assignment(worker_id=w.id, is_required=True, role=None))
        logs.append(DecisionLogEntry(w.id, "assigned_required", {}))

    # 2) Fill remaining with scored optional candidates
    remaining_slots = max(0, weekly_capacity - len(assignments))
    if remaining_slots > 0:
        candidates = compute_eligible_workers(workers, ctx, cfg)
        # Exclude already required
        candidate_ids_excl = {w.id for w in required}
        candidates = [w for w in candidates if w.id not in candidate_ids_excl and respects_required_anchor_spacing(w, week_friday)]
        scored = score_candidates(workers, candidates, ctx, cfg)

        for s in scored:
            if remaining_slots <= 0:
                break
            assignments.append(Assignment(worker_id=s.worker_id, is_required=False, role=None))
            remaining_slots -= 1
            logs.append(DecisionLogEntry(s.worker_id, "assigned_optional", {
                "total": s.total,
                "proximity": s.proximity_bonus,
                "spacing": s.spacing_bonus,
                "scarcity": s.scarcity_penalty,
                "fairness": s.fairness_adjustment,
            }))

        candidate_scores = scored
    else:
        candidate_scores = []

    # 3) Validation
    cap_errors = validate_capacity([(a.role or "closing", a.worker_id) for a in assignments], weekly_capacity)
    errors.extend(cap_errors)

    id_to_worker = {w.id: w for w in workers}
    for a in assignments:
        w = id_to_worker.get(a.worker_id)
        if not w:
            continue
        # Tentatively add to closing history for validation-only simulation
        if week_friday not in w.closing_history:
            w.closing_history.append(week_friday)
            w.closing_history.sort()
        errors.extend(validate_min_gap(w))
        errors.extend(validate_no_conflicts(w))
        # revert tentative add to avoid side-effects in demo mode
        w.closing_history = [d for d in w.closing_history if d != week_friday]

    result = WeekDecisionResult(
        week_friday=week_friday,
        assignments=assignments,
        candidate_scores=candidate_scores,
        logs=logs,
        errors=errors,
    )
    return result


