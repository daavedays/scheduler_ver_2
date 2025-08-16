import os
import sys
import json
from datetime import datetime, timedelta, date


REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)


def dmy(d: date) -> str:
    return d.strftime('%d/%m/%Y')


def main() -> int:
    try:
        from backend.worker import load_workers_from_json
        from backend.engine import SchedulingEngineV2
        from backend.y_tasks import read_x_tasks
        from backend.constants import get_y_task_types
    except Exception as e:
        print(f"Import error: {e}")
        return 1

    # Inputs
    worker_json = os.path.join(REPO_ROOT, 'data', 'worker_data.json')
    x_csv = os.path.join(REPO_ROOT, 'data', 'x_tasks_2025_1.csv')
    if not os.path.exists(worker_json):
        print(f"Missing workers file: {worker_json}")
        return 1
    if not os.path.exists(x_csv):
        print(f"Missing X CSV: {x_csv}")
        return 1

    # Load workers
    workers = load_workers_from_json(worker_json)
    id_to_worker = {w.id: w for w in workers}

    # Expand X tasks to daily assignments and attach to workers
    x_assignments = read_x_tasks(x_csv)
    for wid, per_day in x_assignments.items():
        w = id_to_worker.get(wid)
        if not w:
            continue
        for ds, task in per_day.items():
            try:
                dt = datetime.strptime(ds, '%d/%m/%Y').date()
            except Exception:
                continue
            w.assign_x_task(dt, task)

    # Choose a 2-week span within the CSV range
    start = datetime.strptime('05/01/2025', '%d/%m/%Y').date()
    end = datetime.strptime('18/01/2025', '%d/%m/%Y').date()

    # Build tasks_by_date with Y task types each day
    y_types = get_y_task_types()
    tasks_by_date = {}
    cur = start
    while cur <= end:
        tasks_by_date[cur] = y_types.copy()
        cur += timedelta(days=1)

    # Run engine
    engine = SchedulingEngineV2()
    result = engine.assign_tasks_for_range(
        workers=workers,
        start_date=start,
        end_date=end,
        tasks_by_date=tasks_by_date,
    )

    assignments = result.get('y_tasks', {})
    errors = result.get('assignment_errors', [])

    # Validate: On Fridays, no worker with non-"Rituk" X task may be assigned a Y task
    violations = []
    for day, pairs in assignments.items():
        if isinstance(day, str):
            try:
                day_obj = datetime.strptime(day, '%Y-%m-%d').date()  # not expected, but guard
            except Exception:
                continue
        else:
            day_obj = day
        if day_obj.weekday() != 4:
            continue
        for task_type, wid in pairs:
            w = id_to_worker.get(wid)
            if not w:
                continue
            ds = dmy(day_obj)
            x_task = w.x_tasks.get(ds)
            if x_task and x_task != 'Rituk':
                violations.append({
                    'date': ds,
                    'task': task_type,
                    'worker_id': wid,
                    'worker_name': w.name,
                    'x_task': x_task,
                })

    # Output
    print(f"Checked range {dmy(start)} to {dmy(end)}")
    print(f"Engine errors reported: {len(errors)}")
    for e in errors[:10]:
        print("  -", e)
    if violations:
        print("FAIL: Violations found (Y assigned while non-Rituk X present on Friday):")
        for v in violations:
            print(f"  - {v['date']} {v['task']}: {v['worker_name']} ({v['worker_id']}) X={v['x_task']}")
        return 2
    print("PASS: No Friday Y assignment to workers with non-'Rituk' X tasks.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


