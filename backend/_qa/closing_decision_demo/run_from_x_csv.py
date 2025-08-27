from __future__ import annotations

import csv
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Optional
import re

try:
    from ..worker import (
        EnhancedWorker,
        load_workers_from_json,
        load_x_tasks_from_csv,
    )
    from ..closing_schedule_calculator import ClosingScheduleCalculator
except Exception:
    from backend.worker import (
        EnhancedWorker,
        load_workers_from_json,
        load_x_tasks_from_csv,
    )
    from backend.closing_schedule_calculator import ClosingScheduleCalculator


def _friday_in_week(start: date, end: date) -> Optional[date]:
    # Return the Friday within [start, end], if any
    d = start
    while d <= end:
        if d.weekday() == 4:
            return d
        d += timedelta(days=1)
    return None


def parse_fridays_from_x_csv(csv_path: str) -> List[date]:
    """Parse date-range headers from the second row and return Friday dates.

    Expected first two columns: id, name. Following columns: week indices on row 1,
    then ranges like "05/01 - 11/01" on row 2 (no years). Year is inferred from filename.
    """
    fridays: List[date] = []
    # Infer year from filename like x_tasks_2025_1.csv
    m = re.search(r"x_tasks_(\d{4})_", os.path.basename(csv_path))
    year = int(m.group(1)) if m else date.today().year

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header_row1 = next(reader, [])
        header_row2 = next(reader, [])
        # Collect ranges from row2 skipping first two cols
        ranges = header_row2[2:]
        for rng in ranges:
            rng = rng.strip()
            if not rng:
                continue
            # Formats like "05/01 - 11/01"
            parts = [p.strip() for p in rng.split('-')]
            if len(parts) != 2:
                continue
            try:
                start_day, start_mon = map(int, parts[0].split('/'))
                end_day, end_mon = map(int, parts[1].split('/'))
                start_dt = date(year, start_mon, start_day)
                end_dt = date(year, end_mon, end_day)
                fri = _friday_in_week(start_dt, end_dt)
                if fri:
                    fridays.append(fri)
            except Exception:
                continue
    return fridays


def load_x_tasks_semester(csv_path: str, workers: List[EnhancedWorker]):
    """Fill worker.x_tasks using the semester CSV layout (id,name + ranges on row2).

    For each non-empty cell in worker row, map the corresponding Friday date string
    (dd/mm/YYYY) to the task name.
    """
    # Build Friday dates aligned with columns starting from col index 2
    fridays = parse_fridays_from_x_csv(csv_path)
    # Map workers by ID (backend policy: IDs only)
    id_to_worker = {w.id: w for w in workers}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        row1 = next(reader, [])
        row2 = next(reader, [])
        for row in reader:
            if not row or len(row) < 2:
                continue
            worker_id = row[0].strip()
            worker = id_to_worker.get(worker_id)
            if not worker:
                continue
            # For each week column (align fridays list to columns starting at index 2)
            for i, cell in enumerate(row[2:]):
                if i >= len(fridays):
                    break
                task = (cell or '').strip()
                if not task:
                    continue
                date_str = fridays[i].strftime('%d/%m/%Y')
                worker.x_tasks[date_str] = task


def convert_dates_to_weeks(dates: List[date], semester_weeks: List[date]) -> List[int]:
    index: Dict[date, int] = {d: i + 1 for i, d in enumerate(semester_weeks)}
    weeks: List[int] = []
    for d in sorted(dates):
        if d in index:
            weeks.append(index[d])
    return weeks


def weeks_min_diff(weeks: List[int]) -> str:
    if len(weeks) < 2:
        return "N/A"
    ws = sorted(weeks)
    diffs = [ws[i] - ws[i-1] for i in range(1, len(ws))]
    return str(min(diffs)) if diffs else "N/A"


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(repo_root, 'data')
    worker_json = os.path.join(data_dir, 'worker_data.json')
    x_csv = os.path.join(data_dir, 'x_tasks_2025_1.csv')
    name_conv = os.path.join(data_dir, 'name_conv.json')

    # Load workers. For matching existing CSV worker names, we pass name conversion.
    workers: List[EnhancedWorker] = load_workers_from_json(worker_json, name_conv)

    # Load X tasks into workers and parse semester Fridays from CSV (custom layout)
    load_x_tasks_semester(x_csv, workers)
    semester_weeks = parse_fridays_from_x_csv(x_csv)
    if not semester_weeks:
        print("No valid Friday dates parsed from X-tasks CSV headers.")
        return

    calc = ClosingScheduleCalculator()
    calc.update_all_worker_schedules(workers, semester_weeks)

    # Pick one worker per target interval that has X tasks
    targets = {2: None, 3: None, 4: None, 5: None}
    for w in workers:
        if w.closing_interval in targets and targets[w.closing_interval] is None:
            if hasattr(w, 'x_tasks') and len(w.x_tasks) > 0:
                targets[w.closing_interval] = w
        if all(targets.values()):
            break

    # Produce output
    for interval in [2, 3, 4, 5]:
        w = targets.get(interval)
        if not w:
            print(f"No worker with X tasks and closing interval {interval} found.\n")
            continue

        # Recompute to get calculation log for this worker
        result = calc.calculate_worker_closing_schedule(w, semester_weeks)
        required_dates = result['required_dates']
        optimal_dates = result['optimal_dates']
        combined_dates = sorted(list({*required_dates, *optimal_dates}))
        required_weeks = convert_dates_to_weeks(required_dates, semester_weeks)
        optimal_weeks = convert_dates_to_weeks(optimal_dates, semester_weeks)
        combined_weeks = sorted(list(set(required_weeks + optimal_weeks)))
        actual_interval = weeks_min_diff(combined_weeks)

        print(f"worker name: {w.name}")
        print(f"worker closing inteval = {w.closing_interval}")
        print(f"required closing weeks = {required_weeks}")
        print(f"optimal closing weeks = {optimal_weeks}")
        print(f"combined= {combined_weeks}")
        print(f"actual inteval after generation: {actual_interval}")
        print("decisions = {")
        for line in result.get('calculation_log', []):
            print(f"  '{line}',")
        print("}")
        print()


if __name__ == '__main__':
    main()


