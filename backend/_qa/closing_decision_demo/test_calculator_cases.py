from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple
import os
import copy

try:
    from ..worker import EnhancedWorker, load_workers_from_json
    from ..closing_schedule_calculator import ClosingScheduleCalculator
except Exception:
    from backend.worker import EnhancedWorker, load_workers_from_json
    from backend.closing_schedule_calculator import ClosingScheduleCalculator


def generate_fridays(start: date, weeks: int) -> List[date]:
    # Normalize to the next Friday
    d = start
    while d.weekday() != 4:
        d += timedelta(days=1)
    return [d + timedelta(weeks=i) for i in range(weeks)]


def set_x_tasks_by_weeks(worker: EnhancedWorker, week_numbers: List[int], semester_weeks: List[date], task_name: str = "X"):
    worker.x_tasks = {}
    for w in week_numbers:
        if 1 <= w <= len(semester_weeks):
            worker.x_tasks[semester_weeks[w - 1].strftime('%d/%m/%Y')] = task_name


def clone_worker_with_interval(base: EnhancedWorker, interval: int) -> EnhancedWorker:
    # Create a fresh worker-like object with the desired interval
    w = copy.deepcopy(base)
    w.closing_interval = interval
    w.x_tasks = {}
    w.required_closing_dates = []
    w.optimal_closing_dates = []
    w.closing_history = []
    return w


def min_diff_weeks(weeks: List[int]) -> Optional[int]:
    if len(weeks) < 2:
        return None
    ws = sorted(weeks)
    diffs = [ws[i] - ws[i - 1] for i in range(1, len(ws))]
    return min(diffs) if diffs else None


def to_weeks(dates: List[date], semester_weeks: List[date]) -> List[int]:
    idx = {d: i + 1 for i, d in enumerate(semester_weeks)}
    return [idx[d] for d in sorted(dates) if d in idx]


def run_case(title: str, worker: EnhancedWorker, semester_weeks: List[date], relief_max: int = 1) -> Tuple[bool, str]:
    calc = ClosingScheduleCalculator(allow_single_relief_min1=True, relief_max_per_semester=relief_max)
    result = calc.calculate_worker_closing_schedule(worker, semester_weeks)
    req = to_weeks(result['required_dates'], semester_weeks)
    opt = to_weeks(result['optimal_dates'], semester_weeks)
    combined = sorted(list(set(req + opt)))

    n = max(2, worker.closing_interval)
    logs = result.get('calculation_log', [])
    relief_events = [l for l in logs if 'Relief inserted between' in l]

    # Verify constraints
    ok = True
    problems: List[str] = []

    # 1) No optional inside strictly tight gaps (< 2n)
    anchors = sorted(req)
    for i in range(len(anchors) - 1):
        a, b = anchors[i], anchors[i + 1]
        if b - a < 2 * n:
            inside = [w for w in combined if a < w < b]
            # If relief present and equals 2n-1 gap, allow exactly one at a+n for n>2
            allowed = []
            if b - a == 2 * n - 1 and n > 2:
                allowed = [a + n]
            if any(w not in allowed for w in inside):
                ok = False
                problems.append(f"tight-gap violation between anchors {a}-{b}: inside={inside}, allowed={allowed}")

    # 2) Relief usage matches rule: only when gap == 2n-1 and interval>2, <= relief_max
    if len(relief_events) > relief_max:
        ok = False
        problems.append(f"relief limit exceeded: {len(relief_events)}>{relief_max}")

    if n == 2 and relief_events:
        ok = False
        problems.append("n=2 should not have relief events")

    # 3) Start gap pattern: picks at 1,1+n,... <= first_anchor-n
    if anchors:
        first = anchors[0]
        latest_allowed = first - n
        expected = []
        if latest_allowed >= 1:
            w = 1
            while w <= latest_allowed:
                expected.append(w)
                w += n
        actual = [w for w in combined if w < first]
        if set(actual) != set(expected):
            ok = False
            problems.append(f"start-gap mismatch: expected {expected}, actual {actual}")

    # 4) End gap pattern: last_anchor+n, step n
    if anchors:
        last = anchors[-1]
        expected = []
        w = last + n
        while w <= len(semester_weeks):
            expected.append(w)
            w += n
        actual = [w for w in combined if w > last]
        # With relief, actual may include one additional point placed in a middle gap; filter to > last only
        if set(actual) != set(expected):
            ok = False
            problems.append(f"end-gap mismatch: expected {expected}, actual {actual}")

    return ok, ("PASS: " + title) if ok else ("FAIL: " + title + " -> " + "; ".join(problems))


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(repo_root, 'data')
    worker_json = os.path.join(data_dir, 'worker_data.json')
    workers = load_workers_from_json(worker_json)

    # Build a 26-week semester starting near Jan 2025
    semester_weeks = generate_fridays(date(2025, 1, 1), 26)

    # Find base workers for intervals (fallback to any if missing)
    any_worker = workers[0]
    base2 = next((w for w in workers if w.closing_interval == 2), any_worker)
    base3 = next((w for w in workers if w.closing_interval == 3), any_worker)
    base4 = next((w for w in workers if w.closing_interval == 4), any_worker)

    print("Calculator edge-case tests:\n")

    # Case A: No required weeks -> should pick 1,1+n,...
    wA = clone_worker_with_interval(base3, 3)
    set_x_tasks_by_weeks(wA, [], semester_weeks)
    ok, msg = run_case("A: no required weeks (n=3)", wA, semester_weeks)
    print(msg)

    # Case B: Tight middle gap < 2n -> no picks inside
    wB = clone_worker_with_interval(base4, 4)
    set_x_tasks_by_weeks(wB, [6, 13], semester_weeks)  # gap 7 -> equals 2n-1 triggers relief; use 6 and 12 for 6 -> 2n-2
    ok, msg = run_case("B: tight gap exactly 2n-1 (n=4)", wB, semester_weeks)
    print(msg)

    wB2 = clone_worker_with_interval(base4, 4)
    set_x_tasks_by_weeks(wB2, [6, 12], semester_weeks)  # gap 6 -> < 2n -> no picks inside
    ok, msg = run_case("B2: tight gap < 2n, no picks (n=4)", wB2, semester_weeks)
    print(msg)

    # Case C: Start gap behavior
    wC = clone_worker_with_interval(base3, 3)
    set_x_tasks_by_weeks(wC, [8], semester_weeks)
    ok, msg = run_case("C: start gap fill (n=3, first anchor=8)", wC, semester_weeks)
    print(msg)

    # Case D: End gap behavior
    wD = clone_worker_with_interval(base2, 2)
    set_x_tasks_by_weeks(wD, [20], semester_weeks)
    ok, msg = run_case("D: end gap fill (n=2, last anchor=20)", wD, semester_weeks)
    print(msg)

    # Case E: Relief forbidden for n=2
    wE = clone_worker_with_interval(base2, 2)
    set_x_tasks_by_weeks(wE, [1, 4], semester_weeks)  # gap 3 == 2n-1, but n=2 should not relief
    ok, msg = run_case("E: relief disabled for n=2", wE, semester_weeks)
    print(msg)

    # Case F: Relief limit knob across multiple 2n-1 gaps
    wF = clone_worker_with_interval(base4, 4)
    # Gaps: (1,8) and (15,22) both 7 == 2n-1
    set_x_tasks_by_weeks(wF, [1, 8, 15, 22], semester_weeks)
    ok, msg = run_case("F: relief limited to 1 per semester (n=4)", wF, semester_weeks, relief_max=1)
    print(msg)

    wF2 = clone_worker_with_interval(base4, 4)
    set_x_tasks_by_weeks(wF2, [1, 8, 15, 22], semester_weeks)
    ok, msg = run_case("F2: relief limit=2 allows two insertions (n=4)", wF2, semester_weeks, relief_max=2)
    print(msg)


if __name__ == '__main__':
    main()


