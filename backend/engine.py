from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Set

try:
    # Try relative imports first (when used as module)
    from .worker import EnhancedWorker
    from .closing_schedule_calculator import ClosingScheduleCalculator
    from .scoring_config import ScoringConfig, load_config
    from .scoring import (
        recalc_worker_schedule,
        update_score_on_close_early,
        update_score_on_y_fairness,
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    from worker import EnhancedWorker
    from closing_schedule_calculator import ClosingScheduleCalculator
    from scoring_config import ScoringConfig, load_config
    from scoring import (
        recalc_worker_schedule,
        update_score_on_close_early,
        update_score_on_y_fairness,
    )


try:
	from .constants import (
		get_y_task_types,
		get_y_task_definitions,
		get_y_task_maps,
	)
except ImportError:
	from constants import (
		get_y_task_types,
		get_y_task_definitions,
		get_y_task_maps,
	)

Y_TASK_TYPES = get_y_task_types()
Y_TASK_DEFS = {d['name']: bool(d.get('requiresQualification', True)) for d in (get_y_task_definitions() or [])}
Y_ID_TO_NAME, Y_NAME_TO_ID = get_y_task_maps()


def compute_qualification_scarcity(workers: List[EnhancedWorker]) -> Tuple[Dict[str, int], Dict[str, float]]:
    """Compute per-task availability counts and scarcity scores (lower is less scarce).

    scarcity[task] = 1 / max(1, num_qualified)
    """
    availability: Dict[str, int] = {t: 0 for t in Y_TASK_TYPES}
    for w in workers:
        for t in Y_TASK_TYPES:
            requires = Y_TASK_DEFS.get(t, True)
            # Prefer ID-based check; fallback to name list
            tid = Y_NAME_TO_ID.get(t)
            qualified = (tid in getattr(w, 'qualification_ids', set())) if isinstance(tid, int) else False
            if (not requires) or qualified or (t in w.qualifications):
                availability[t] += 1
    scarcity: Dict[str, float] = {}
    for t, n in availability.items():
        scarcity[t] = 1.0 / max(1, n)
    return availability, scarcity


def compute_worker_scarcity_index(worker: EnhancedWorker, task_scarcity: Dict[str, float]) -> float:
    """Average scarcity across the worker's Y-task qualifications.

    Higher value ⇒ more scarce ⇒ protect from closing/overuse.
    """
    values: List[float] = []
    for t in Y_TASK_TYPES:
        requires = Y_TASK_DEFS.get(t, True)
        tid = Y_NAME_TO_ID.get(t)
        qualified = (tid in getattr(worker, 'qualification_ids', set())) if isinstance(tid, int) else False
        if (not requires) or qualified or (t in worker.qualifications):
            values.append(task_scarcity.get(t, 0.0))
    if not values:
        return 0.0
    return sum(values) / len(values)


@dataclass
class AssignmentDecision:
    worker_id: str
    worker_name: str
    reason: str
    debug: Dict[str, float]


@dataclass
class AssignmentError:
    task_type: str
    date: date
    reason: str
    severity: str  # 'warning' or 'error'


class SchedulingEngineV2:
    """
    New and improved scheduling engine implementing the correct, unified workflow.
    """
    def __init__(self, cfg: Optional[ScoringConfig] = None):
        self.cfg = cfg or load_config()
        self.calc = ClosingScheduleCalculator(
            allow_single_relief_min1=self.cfg.CLOSING_RELIEF_ENABLED,
            relief_max_per_semester=self.cfg.CLOSING_RELIEF_MAX_PER_SEMESTER,
        )
        self.assignment_errors: List[AssignmentError] = []
        self.task_scarcity: Dict[str, float] = {}
        self.worker_scarcity_index: Dict[str, float] = {}

    def _precompute_scarcity(self, workers: List[EnhancedWorker]):
        """Computes and stores scarcity indexes."""
        _, self.task_scarcity = compute_qualification_scarcity(workers)
        self.worker_scarcity_index = {
            w.id: compute_worker_scarcity_index(w, self.task_scarcity) for w in workers
        }

    def _prioritize_tasks_by_scarcity(self, tasks: List[str]) -> List[str]:
        """Sorts tasks by their scarcity score (more scarce first)."""
        return sorted(tasks, key=lambda t: self.task_scarcity.get(t, 0), reverse=True)

    def _update_missed_optimal_close(self, worker: EnhancedWorker, missed_friday: date, semester_weeks: List[date], logs: List[str]):
        """
        If a worker misses an optimal closing date, find the next available one.
        """
        # Skip workers who cannot participate in closing
        if not worker.can_participate_in_closing():
            return
            
        if missed_friday in worker.optimal_closing_dates:
            worker.optimal_closing_dates.remove(missed_friday)
            # Find next optimal slot
            next_optimal = self.calc.find_next_optimal_closing_date(
                worker.closing_history,
                worker.closing_interval,
                missed_friday + timedelta(days=1), # Start search after the missed date
                semester_weeks
            )
            if next_optimal and next_optimal not in worker.optimal_closing_dates:
                worker.optimal_closing_dates.append(next_optimal)
                worker.optimal_closing_dates.sort()
                logs.append(f"Rescheduled optimal for {worker.name} from {missed_friday.strftime('%d/%m/%Y')} to {next_optimal.strftime('%d/%m/%Y')}")

    def assign_tasks_for_range(
        self,
        workers: List[EnhancedWorker],
        start_date: date,
        end_date: date,
        tasks_by_date: Dict[date, List[str]]
    ) -> Dict:
        """
        Main orchestration function for assigning all Y-tasks within a date range.
        Follows the user-specified workflow.
        """
        self.assignment_errors.clear()
        logs: List[str] = []
        assignments: Dict[date, List[Tuple[str, str]]] = {d: [] for d in tasks_by_date if d >= start_date and d <= end_date}
        
        # 1. Precomputation
        all_fridays_in_range = [d for d in (start_date + timedelta(i) for i in range((end_date - start_date).days + 1)) if d.weekday() == 4 and d >= start_date and d <= end_date]
        if not all_fridays_in_range:
            # Handle cases with no weekends
            logs.append("No weekends in the selected date range.")

        # Always (re)compute closing schedules from intervals/X-task state so optimal dates exist
        try:
            self.calc.update_all_worker_schedules(workers, all_fridays_in_range if all_fridays_in_range else [start_date])
        except Exception as e:
            logs.append(f"WARNING: Failed to update closing schedules: {e}")

        # Remove redundant per-worker recalc; schedules already updated via self.calc
        self._precompute_scarcity(workers)
        
        # 2. Separate dates into weekends and weekdays
        date_cursor = start_date
        while date_cursor <= end_date:
            if date_cursor.weekday() in {3, 4, 5}:  # Thursday, Friday, Saturday
                thursday = date_cursor - timedelta(days=date_cursor.weekday() - 3)
                logs.append(f"--- Processing Weekend: {thursday.strftime('%d/%m/%Y')} ---")
                
                weekend_tasks_for_dates = {
                    d: tasks_by_date.get(d, [])
                    for d in [thursday, thursday + timedelta(1), thursday + timedelta(2)]
                    if d in tasks_by_date
                }
                
                if any(weekend_tasks_for_dates.values()):
                    self._assign_weekend_tasks(
                        workers,
                        thursday,
                        weekend_tasks_for_dates,
                        assignments,
                        logs,
                        all_fridays_in_range
                    )
                
                date_cursor = thursday + timedelta(days=3) # Move to next Sunday
            else: # Weekday
                if date_cursor in tasks_by_date and tasks_by_date.get(date_cursor):
                    self._assign_weekday_tasks(
                        workers,
                        date_cursor,
                        tasks_by_date[date_cursor],
                        assignments,
                        logs
                    )
                date_cursor += timedelta(days=1)
        
        # 3. Finalization and reporting
        
        # NEW: Trigger closing schedule recalculation after all Y task assignments
        try:
            # Generate semester weeks for the entire date range
            semester_weeks = []
            current = start_date
            while current <= end_date:
                if current.weekday() == 4:  # Friday
                    semester_weeks.append(current)
                current += timedelta(days=1)
            
            # Update all worker closing schedules
            self.calc.update_all_worker_schedules(workers, semester_weeks)
            
            logs.append("✅ Closing schedule recalculation completed after Y task assignments")
            
        except Exception as e:
            logs.append(f"⚠️  Warning: Failed to update closing schedules after Y task assignments: {e}")
        
        return {"y_tasks": assignments, "logs": logs, "assignment_errors": [e.__dict__ for e in self.assignment_errors]}


    def _assign_weekend_tasks(
        self,
        workers: List[EnhancedWorker],
        thursday: date,
        weekend_tasks: Dict[date, List[str]],
        assignments: Dict[date, List[Tuple[str, str]]],
        logs: List[str],
        semester_weeks: List[date]
    ):
        friday = thursday + timedelta(days=1)
        saturday = thursday + timedelta(days=2)
        weekend_dates = [d for d in [thursday, friday, saturday] if d in weekend_tasks]

        assigned_closers: List[EnhancedWorker] = []
        
        # Dynamically determine the number of closer slots from the number of tasks
        all_weekend_tasks = sorted(list(set(t for d_tasks in weekend_tasks.values() for t in d_tasks)))
        num_slots = len(all_weekend_tasks)
        logs.append(f"Weekend of {thursday.strftime('%d/%m/%Y')} requires {num_slots} closers for tasks: {all_weekend_tasks}")

        # 0. Helper filters
        def has_non_rituk_x_on_friday(w: EnhancedWorker) -> bool:
            return w.has_x_task_on_date(friday) and not w.has_specific_x_task(friday, "Rituk")

        # Helper function to check if worker has X task conflict (for deprioritization)
        def has_x_task_conflict(w: EnhancedWorker) -> bool:
            # Check for X task conflicts on any of the weekend days
            return any(w.has_x_task_on_date(day) for day in [thursday, friday, thursday + timedelta(days=2)])

        # 1. Assign required closers (ONLY those with X task 'Rituk') and give them a Y task by scarcity
        rituk_required = [
            w for w in workers
            if w.can_participate_in_closing() and w.has_specific_x_task(friday, "Rituk")
        ]

        # Create a mutable copy of tasks to assign
        unassigned_tasks = all_weekend_tasks[:]

        # Helper: check if worker qualifies for a given Y task name
        def worker_qualifies_for(task_name: str, worker: EnhancedWorker) -> bool:
            tid_local = Y_NAME_TO_ID.get(task_name)
            qualified_by_id = (isinstance(tid_local, int) and (tid_local in getattr(worker, 'qualification_ids', set())))
            qualified_by_name = (task_name in (worker.qualifications or []))
            return qualified_by_id or qualified_by_name

        for worker in rituk_required:
            if len(assigned_closers) >= num_slots or not unassigned_tasks:
                break
            # Find the scarcest task they can do
            qualified_scarce_tasks = self._prioritize_tasks_by_scarcity(
                [t for t in unassigned_tasks if worker_qualifies_for(t, worker)]
            )
            if qualified_scarce_tasks:
                task_to_assign = qualified_scarce_tasks[0]
                assigned_closers.append(worker)
                for day in weekend_dates:
                    assignments[day].append((task_to_assign, worker.id))
                worker.assign_closing(friday)
                worker.y_task_counts[task_to_assign] = worker.y_task_counts.get(task_to_assign, 0) + 1
                logs.append(
                    f"Assigned RITUK closer {worker.name} to {task_to_assign} for weekend of {thursday.strftime('%d/%m/%Y')}"
                )
                if task_to_assign in unassigned_tasks:
                    unassigned_tasks.remove(task_to_assign)
            else:
                logs.append(
                    f"WARNING: RITUK closer {worker.name} has no qualifying Y task for this weekend; leaving for manual assignment if needed."
                )

        # Build base pool of eligible candidates for Y-task closings (include all but deprioritize X task conflicts)
        def eligible_base(w: EnhancedWorker) -> bool:
            if not w.can_participate_in_closing():
                return False
            if w.id in [c.id for c in assigned_closers]:
                return False
            # Note: Workers with X tasks are still eligible but will be deprioritized
            # Avoid back-to-back and upcoming required
            if friday - timedelta(days=7) in w.closing_history:
                return False
            if friday + timedelta(days=7) in w.required_closing_dates:
                return False
            return True

        # 2a. Prefer severely overdue candidates (fairness catch-up) before optimal
        if unassigned_tasks and len(assigned_closers) < num_slots:
            overdue_candidates = [w for w in workers if eligible_base(w)]
            # Compute overdue ratio (weeks_overdue / interval) and weeks_overdue
            overdue_candidates.sort(
                key=lambda w: (
                    has_x_task_conflict(w),  # X task conflicts last (False sorts before True)
                    -w.get_overdue_ratio(friday),  # highest ratio first
                    -w.get_weeks_overdue(friday),  # then absolute overdue
                    w.score,
                    sum(w.y_task_counts.values()),
                    w.id
                )
            )
            for worker in overdue_candidates:
                if len(assigned_closers) >= num_slots or not unassigned_tasks:
                    break
                # Only pick those actually overdue
                if worker.get_weeks_overdue(friday) <= 0:
                    break
                qualified = self._prioritize_tasks_by_scarcity([t for t in unassigned_tasks if worker_qualifies_for(t, worker)])
                if not qualified:
                    continue
                task_to_assign = qualified[0]
                assigned_closers.append(worker)
                for day in weekend_dates:
                    assignments[day].append((task_to_assign, worker.id))
                worker.assign_closing(friday)
                try:
                    worker.update_score_after_assignment("closing", friday)
                except Exception:
                    pass
                worker.y_task_counts[task_to_assign] = worker.y_task_counts.get(task_to_assign, 0) + 1
                if task_to_assign in unassigned_tasks:
                    unassigned_tasks.remove(task_to_assign)
                logs.append(
                    f"Assigned OVERDUE {worker.name} to {task_to_assign} (overdue_ratio={worker.get_overdue_ratio(friday):.2f}, weeks_overdue={worker.get_weeks_overdue(friday)})"
                )

        # 2b. Prefer candidates whose Friday is an optimal closing date
        if unassigned_tasks and len(assigned_closers) < num_slots:
            optimal_candidates = [w for w in workers if eligible_base(w) and (friday in w.optimal_closing_dates)]
            # Sort by X task conflicts first (False before True), then score asc, then total Y asc, then id
            optimal_candidates.sort(key=lambda w: (has_x_task_conflict(w), w.score, sum(w.y_task_counts.values()), w.id))
            for worker in optimal_candidates:
                if len(assigned_closers) >= num_slots or not unassigned_tasks:
                    break
                qualified = self._prioritize_tasks_by_scarcity([t for t in unassigned_tasks if worker_qualifies_for(t, worker)])
                if not qualified:
                    continue
                task_to_assign = qualified[0]
                assigned_closers.append(worker)
                for day in weekend_dates:
                    assignments[day].append((task_to_assign, worker.id))
                worker.assign_closing(friday)
                try:
                    worker.update_score_after_assignment("closing", friday)
                except Exception:
                    pass
                worker.y_task_counts[task_to_assign] = worker.y_task_counts.get(task_to_assign, 0) + 1
                if task_to_assign in unassigned_tasks:
                    unassigned_tasks.remove(task_to_assign)
                logs.append(
                    f"Assigned optimal-date {worker.name} to {task_to_assign} for weekend of {thursday.strftime('%d/%m/%Y')}"
                )

        # 3. If still missing, pick candidates closest to their optimal (min weeks_until_due), tie-break score
        if unassigned_tasks and len(assigned_closers) < num_slots:
            remaining_candidates = [w for w in workers if eligible_base(w)]
            # Sort by X task conflicts first (False before True), then proximity to due date, then score, then total Y, then id
            remaining_candidates.sort(
                key=lambda w: (has_x_task_conflict(w), w.get_weeks_until_due_to_close(friday), w.score, sum(w.y_task_counts.values()), w.id)
            )
            for worker in remaining_candidates:
                if len(assigned_closers) >= num_slots or not unassigned_tasks:
                    break
                qualified = self._prioritize_tasks_by_scarcity([t for t in unassigned_tasks if worker_qualifies_for(t, worker)])
                if not qualified:
                    continue
                task_to_assign = qualified[0]
                assigned_closers.append(worker)
                for day in weekend_dates:
                    assignments[day].append((task_to_assign, worker.id))
                worker.assign_closing(friday)
                try:
                    worker.update_score_after_assignment("closing", friday)
                except Exception:
                    pass
                worker.y_task_counts[task_to_assign] = worker.y_task_counts.get(task_to_assign, 0) + 1
                if task_to_assign in unassigned_tasks:
                    unassigned_tasks.remove(task_to_assign)
                logs.append(
                    f"Assigned proximity {worker.name} to {task_to_assign} (weeks_until_due={worker.get_weeks_until_due_to_close(friday)})"
                )

        # 3. Update workers who had an optimal date but were not picked
        for worker in workers:
            if worker not in assigned_closers and friday in worker.optimal_closing_dates:
                 self._update_missed_optimal_close(worker, friday, semester_weeks, logs)
                 
        # 4. Handle any unassigned weekend tasks
        if unassigned_tasks:
            # Check if the only remaining pool are last-week closers (blocked by policy)
            potential_last_week_only = [
                w for w in workers
                if w.can_participate_in_closing()
                and not has_non_rituk_x_on_friday(w)
                and w.id not in [c.id for c in assigned_closers]
                and (friday - timedelta(days=7)) in w.closing_history
            ]
            if potential_last_week_only:
                for task in unassigned_tasks:
                    reason = (
                        f"Missing closer for '{task}'. Only remaining candidates closed last week. Manual assignment required."
                    )
                    self.assignment_errors.append(AssignmentError(task, thursday, reason, 'error'))
                    logs.append(f"ERROR: {reason}")
            else:
                for task in unassigned_tasks:
                    reason = f"No qualified and available closers for weekend task '{task}'"
                    self.assignment_errors.append(AssignmentError(task, thursday, reason, 'warning'))
                    logs.append(f"WARNING: {reason} for weekend of {thursday.strftime('%d/%m/%Y')}")


    def _assign_weekday_tasks(
        self,
        workers: List[EnhancedWorker],
        task_date: date,
        tasks_needed: List[str],
        assignments: Dict[date, List[Tuple[str, str]]],
        logs: List[str]
    ):
        assigned_worker_ids_today = {pair[1] for pair in assignments.get(task_date, [])}
        
        # Base availability: no same-day double-assignments or recent closing
        base_available = [
            w for w in workers
            if w.id not in assigned_worker_ids_today and task_date not in w.closing_history
        ]

        # Soft constraint: prefer workers without X tasks, but allow manual assignment
        preferred_available = [
            w for w in base_available
            if not w.has_x_task_on_date(task_date)
        ]
        
        # If no preferred workers, fall back to all available (for manual assignment visibility)
        available_workers = preferred_available if preferred_available else base_available
        
        for task in self._prioritize_tasks_by_scarcity(tasks_needed):
            # Check if task already assigned today
            if any(t == task for t, _ in assignments.get(task_date, [])):
                continue
            
            requires = Y_TASK_DEFS.get(task, True)
            tid = Y_NAME_TO_ID.get(task)
            def is_worker_qualified(worker: EnhancedWorker) -> bool:
                if not requires:
                    return True
                qualified_by_id = (isinstance(tid, int) and (tid in getattr(worker, 'qualification_ids', set())))
                qualified_by_name = (task in (worker.qualifications or []))
                return qualified_by_id or qualified_by_name
            candidates_all = [w for w in available_workers if is_worker_qualified(w)]
            # Prefer workers without another Y-task this same week
            week_start = task_date - timedelta(days=task_date.weekday())
            candidates_pref = [w for w in candidates_all if w.check_multiple_y_tasks_per_week(week_start) == 0]
            candidates = candidates_pref if candidates_pref else candidates_all
            
            if not candidates:
                reason = f"No qualified workers for {task}"
                self.assignment_errors.append(AssignmentError(task, task_date, reason, 'error'))
                logs.append(f"ERROR: {reason} on {task_date.strftime('%d/%m/%Y')}")
                continue
            
            # Sort by X task conflicts first (False before True), then score, then per-task count, then total Y, then ID
            candidates.sort(key=lambda w: (
                w.has_x_task_on_date(task_date),  # X task conflicts last
                w.score,
                w.y_task_counts.get(task, 0),
                sum(w.y_task_counts.values()),
                w.id
            ))
            chosen_worker = candidates[0]
            
            assignments[task_date].append((task, chosen_worker.id))
            available_workers.remove(chosen_worker)
            
            y_tasks_this_week = 1 + chosen_worker.check_multiple_y_tasks_per_week(week_start)
            
            if y_tasks_this_week > 1:
                chosen_worker.add_score_bonus(1.0, f"Multiple Y-tasks in week of {week_start.strftime('%d/%m/%Y')}")
                logs.append(f"Applied score penalty to {chosen_worker.name} for multiple Y-tasks this week.")
            
            # Nudge score after each Y assignment
            try:
                chosen_worker.update_score_after_assignment("y_task", task_date)
            except Exception:
                pass
            chosen_worker.y_task_counts[task] = chosen_worker.y_task_counts.get(task, 0) + 1
            logs.append(f"Assigned weekday task {task} to {chosen_worker.name} on {task_date.strftime('%d/%m/%Y')}")


