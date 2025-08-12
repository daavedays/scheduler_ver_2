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


Y_TASK_TYPES = [
    "Supervisor",
    "C&N Driver",
    "C&N Escort",
    "Southern Driver",
    "Southern Escort",
]


def compute_qualification_scarcity(workers: List[EnhancedWorker]) -> Tuple[Dict[str, int], Dict[str, float]]:
    """Compute per-task availability counts and scarcity scores (lower is less scarce).

    scarcity[task] = 1 / max(1, num_qualified)
    """
    availability: Dict[str, int] = {t: 0 for t in Y_TASK_TYPES}
    for w in workers:
        for t in Y_TASK_TYPES:
            if t in w.qualifications:
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
        if t in worker.qualifications:
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
        self.calc = ClosingScheduleCalculator()
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

        for w in workers:
            recalc_worker_schedule(w, all_fridays_in_range if all_fridays_in_range else [start_date])
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

        # 1. Assign required closers (X-Task "Rituk")
        required_closers = [w for w in workers if friday in w.required_closing_dates]
        
        # Create a mutable copy of tasks to assign
        unassigned_tasks = all_weekend_tasks[:]

        for worker in required_closers:
            if len(assigned_closers) >= num_slots:
                break
            
            # Find the scarcest task they can do
            qualified_scarce_tasks = self._prioritize_tasks_by_scarcity([t for t in unassigned_tasks if t in worker.qualifications])
            
            if qualified_scarce_tasks:
                task_to_assign = qualified_scarce_tasks[0]
                
                assigned_closers.append(worker)
                
                for day in weekend_dates:
                    assignments[day].append((task_to_assign, worker.id))
                
                worker.assign_closing(friday)
                worker.y_task_counts[task_to_assign] = worker.y_task_counts.get(task_to_assign, 0) + 1
                
                logs.append(f"Assigned required closer {worker.name} to {task_to_assign} for weekend of {thursday.strftime('%d/%m/%Y')}")
                unassigned_tasks.remove(task_to_assign)
            else:
                logs.append(f"WARNING: Required closer {worker.name} has no qualifying tasks for this weekend.")

        # 2. Fill remaining closer slots based on optimal dates and score
        if len(assigned_closers) < num_slots:
            candidates = []
            for w in workers:
                if w.id in [c.id for c in assigned_closers] or w.id in [c.id for c in required_closers]:
                    continue
                
                if friday - timedelta(days=7) in w.closing_history:
                    continue
                if friday + timedelta(days=7) in w.required_closing_dates:
                    continue

                is_optimal = friday in w.optimal_closing_dates
                
                key = (0 if is_optimal else 1, w.score, w.id)
                candidates.append((w, key))

            candidates.sort(key=lambda x: x[1])

            for worker, _ in candidates:
                if len(assigned_closers) >= num_slots:
                    break

                qualified_tasks = self._prioritize_tasks_by_scarcity([t for t in unassigned_tasks if t in worker.qualifications])
                if qualified_tasks:
                    task_to_assign = qualified_tasks[0]
                    assigned_closers.append(worker)
                    
                    for day in weekend_dates:
                         assignments[day].append((task_to_assign, worker.id))

                    worker.assign_closing(friday)
                    worker.y_task_counts[task_to_assign] = worker.y_task_counts.get(task_to_assign, 0) + 1
                    
                    unassigned_tasks.remove(task_to_assign)
                    logs.append(f"Assigned {worker.name} to {task_to_assign} for weekend of {thursday.strftime('%d/%m/%Y')} (Optimal: {friday in worker.optimal_closing_dates})")

        # 3. Update workers who had an optimal date but were not picked
        for worker in workers:
            if worker not in assigned_closers and friday in worker.optimal_closing_dates:
                 self._update_missed_optimal_close(worker, friday, semester_weeks, logs)
                 
        # 4. Handle any unassigned weekend tasks
        if unassigned_tasks:
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

        # Hard constraint: never assign Y if worker has any X task that day (including Guarding Duties)
        strictly_available = [
            w for w in base_available
            if not w.has_x_task_on_date(task_date)
        ]

        available_workers = strictly_available
        
        for task in self._prioritize_tasks_by_scarcity(tasks_needed):
            # Check if task already assigned today
            if any(t == task for t, _ in assignments.get(task_date, [])):
                continue
            
            candidates = [w for w in available_workers if task in w.qualifications]
            
            if not candidates:
                reason = f"No qualified workers for {task}"
                self.assignment_errors.append(AssignmentError(task, task_date, reason, 'error'))
                logs.append(f"ERROR: {reason} on {task_date.strftime('%d/%m/%Y')}")
                continue
            
            candidates.sort(key=lambda w: (w.y_task_counts.get(task, 0), w.score, w.id))
            chosen_worker = candidates[0]
            
            assignments[task_date].append((task, chosen_worker.id))
            available_workers.remove(chosen_worker)
            
            week_start = task_date - timedelta(days=task_date.weekday())
            y_tasks_this_week = 1 + chosen_worker.check_multiple_y_tasks_per_week(week_start)
            
            if y_tasks_this_week > 1:
                chosen_worker.add_score_bonus(1.0, f"Multiple Y-tasks in week of {week_start.strftime('%d/%m/%Y')}")
                logs.append(f"Applied score penalty to {chosen_worker.name} for multiple Y-tasks this week.")
            
            chosen_worker.y_task_counts[task] = chosen_worker.y_task_counts.get(task, 0) + 1
            logs.append(f"Assigned weekday task {task} to {chosen_worker.name} on {task_date.strftime('%d/%m/%Y')}")


