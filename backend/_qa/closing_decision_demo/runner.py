from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import os

try:
    from ..worker import load_workers_from_json, EnhancedWorker
    from ..closing_schedule_calculator import ClosingScheduleCalculator
except Exception:
    from backend.worker import load_workers_from_json, EnhancedWorker
    from backend.closing_schedule_calculator import ClosingScheduleCalculator

from .policy import DecisionConfig
from .selector import select_closers_for_week


def _generate_fridays(start_date: date, end_date: date) -> List[date]:
    fridays: List[date] = []
    current = start_date
    while current <= end_date:
        if current.weekday() == 4:
            fridays.append(current)
        current += timedelta(days=1)
    return fridays


def run_demo(
    data_dir: str,
    start_date_str: str,
    end_date_str: str,
    weekly_capacity: int = 2,
) -> List[Dict]:
    start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
    end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()

    worker_file_path = os.path.join(data_dir, 'worker_data.json')
    # Per project policy, backend logic should rely on worker IDs only; avoid name conversion here
    workers: List[EnhancedWorker] = load_workers_from_json(worker_file_path)

    # Precompute closing schedules to populate required/optimal sets
    fridays = _generate_fridays(start_date, end_date)
    if not fridays:
        fridays = [start_date]
    calc = ClosingScheduleCalculator()
    calc.update_all_worker_schedules(workers, fridays)

    cfg = DecisionConfig(weekly_capacity=weekly_capacity)

    results: List[Dict] = []
    for friday in fridays:
        res = select_closers_for_week(workers, friday, fridays, cfg)
        results.append({
            'friday': friday.strftime('%d/%m/%Y'),
            'assignments': [{'worker_id': a.worker_id, 'required': a.is_required} for a in res.assignments],
            'errors': res.errors,
            'logs': [{'worker_id': l.worker_id, 'msg': l.message, 'data': l.data} for l in res.logs],
            'top_candidates': [{
                'worker_id': s.worker_id,
                'total': round(s.total, 3),
                'proximity': s.proximity_bonus,
                'spacing': s.spacing_bonus,
                'scarcity': s.scarcity_penalty,
                'fairness': s.fairness_adjustment,
                'reasons': s.reasons,
            } for s in res.candidate_scores[:10]],
        })

    return results


if __name__ == '__main__':
    # Example: prints a compact preview for quick smoke testing
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
    data_dir = os.path.abspath(data_dir)
    preview = run_demo(data_dir, '01/01/2025', '31/03/2025', weekly_capacity=2)
    for week in preview:
        print(week['friday'], 'assignments=', week['assignments'], 'errors=', len(week['errors']))


