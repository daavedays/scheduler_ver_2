import os
import sys
import json
from datetime import datetime, timedelta
import requests


REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND_URL = "http://localhost:5001"


def dmy(date_obj):
    return date_obj.strftime('%d/%m/%Y')


def main():
    # Ensure backend package imports work if needed
    sys.path.insert(0, REPO_ROOT)
    try:
        from backend.y_tasks import read_x_tasks  # type: ignore
    except Exception as e:
        print(f"Failed to import backend.y_tasks: {e}")
        return 1

    # Use existing X CSV
    x_csv = os.path.join(REPO_ROOT, 'data', 'x_tasks_2025_1.csv')
    if not os.path.exists(x_csv):
        print(f"X CSV not found: {x_csv}")
        return 1

    # Map id->name and name->id from worker_data.json
    worker_json = os.path.join(REPO_ROOT, 'data', 'worker_data.json')
    with open(worker_json, 'r', encoding='utf-8') as f:
        workers = json.load(f)
    id_to_name = {w['id']: w.get('name', w['id']) for w in workers}
    name_to_id = {v: k for k, v in id_to_name.items()}

    # Expand X to daily assignments
    x_assignments = read_x_tasks(x_csv)

    sess = requests.Session()

    # Login
    r = sess.post(f"{BACKEND_URL}/api/login", json={"username": "Dav", "password": "8320845"})
    r.raise_for_status()

    # Choose a two-week window in 2025-H1
    start = datetime.strptime('05/01/2025', '%d/%m/%Y').date()
    end = datetime.strptime('18/01/2025', '%d/%m/%Y').date()

    # Generate Y schedule
    gen = sess.post(f"{BACKEND_URL}/api/y-tasks/generate", json={
        "start": dmy(start),
        "end": dmy(end),
        "num_closers": 2
    })
    gen.raise_for_status()
    data = gen.json()
    grid = data.get('grid', [])
    dates = data.get('dates', [])
    y_tasks = ["Supervisor", "C&N Driver", "C&N Escort", "Southern Driver", "Southern Escort"]

    # Validate: For each Friday, ensure any assigned worker with X task on Friday has X == 'Rituk'; otherwise violation
    violations = []
    for idx, ds in enumerate(dates):
        try:
            d = datetime.strptime(ds, '%d/%m/%Y').date()
        except Exception:
            continue
        if d.weekday() != 4:  # Friday
            continue
        for row, task_name in enumerate(y_tasks):
            if row >= len(grid):
                continue
            soldier_name = (grid[row][idx] or '').strip()
            if not soldier_name:
                continue
            wid = name_to_id.get(soldier_name)
            if not wid:
                # name not in mapping, skip
                continue
            x_on_day = x_assignments.get(wid, {}).get(ds)
            if x_on_day and x_on_day != 'Rituk':
                violations.append({
                    'date': ds,
                    'task': task_name,
                    'worker_id': wid,
                    'worker_name': soldier_name,
                    'x_task': x_on_day
                })

    # Report
    if violations:
        print("FAIL: Found Y-task assignments to workers with non-'Rituk' X tasks on Friday:")
        for v in violations:
            print(f"  - {v['date']} {v['task']}: {v['worker_name']} ({v['worker_id']}) has X={v['x_task']}")
        return 2
    else:
        print("PASS: No Y-task assigned to workers with non-'Rituk' X tasks on Fridays in the tested range.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())


