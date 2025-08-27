#!/usr/bin/env python3
"""
Basic scoring behavior checks after changes:
- Early close bonus scales by weeks early
- Weekly multi-Y bonus triggers starting from second Y in a week
- Above-average Y count bonus applied within same-qualification cohort
"""

import sys
from datetime import date, timedelta

sys.path.append('backend')

from worker import EnhancedWorker
from scoring_config import load_config
from scoring import update_score_on_y_fairness


def sunday_of(dt: date) -> date:
    return dt - timedelta(days=dt.weekday())


def test_early_close_scaling():
    cfg = load_config()
    w = EnhancedWorker(id='1', name='A', start_date=date(2024,1,1), qualifications=[], closing_interval=6)
    # Last close 1 week ago; interval 6 → 5 weeks until due
    last_friday = date(2025,1,3)
    w.closing_history = [last_friday]
    this_friday = date(2025,1,10)
    before = w.score
    weeks_until_due = w.get_weeks_until_due_to_close(this_friday)
    from scoring import update_score_on_close_early
    update_score_on_close_early(w, weeks_until_due, cfg)
    assert w.score - before == weeks_until_due * cfg.EARLY_CLOSE_BONUS_PER_WEEK


def test_multi_y_week_bonus():
    cfg = load_config()
    cfg.MULTIPLE_Y_TASK_WEEK_THRESHOLD = 1
    cfg.MULTIPLE_Y_TASK_WEEK_BONUS = 0.5
    w = EnhancedWorker(id='2', name='B', start_date=date(2024,1,1), qualifications=[], closing_interval=0)
    d1 = date(2025,1,6)  # Monday
    week = sunday_of(d1)
    before = w.score
    # First Y in week: no bonus (simulate engine order: increment before assign)
    w.increment_score_for_multiple_y_tasks(week, threshold=cfg.MULTIPLE_Y_TASK_WEEK_THRESHOLD, per_excess_bonus=cfg.MULTIPLE_Y_TASK_WEEK_BONUS)
    w.assign_y_task(d1, 'T1')
    mid = w.score
    # Second Y in same week: triggers bonus of 1 * 0.5 (increment before assign)
    w.increment_score_for_multiple_y_tasks(week, threshold=cfg.MULTIPLE_Y_TASK_WEEK_THRESHOLD, per_excess_bonus=cfg.MULTIPLE_Y_TASK_WEEK_BONUS)
    w.assign_y_task(d1 + timedelta(days=1), 'T2')
    assert abs((w.score - mid) - cfg.MULTIPLE_Y_TASK_WEEK_BONUS) < 1e-9


def test_cohort_above_average_bonus():
    cfg = load_config()
    # Same-qualification cohort (ids 1..3): all have empty qualifications
    w1 = EnhancedWorker(id='1', name='A', start_date=date(2024,1,1), qualifications=[], closing_interval=0)
    w2 = EnhancedWorker(id='2', name='B', start_date=date(2024,1,1), qualifications=[], closing_interval=0)
    w3 = EnhancedWorker(id='3', name='C', start_date=date(2024,1,1), qualifications=[], closing_interval=0)
    # Give w1 more Y tasks than cohort average
    for _ in range(4):
        w1.y_task_counts['T'] = w1.y_task_counts.get('T', 0) + 1
    w2.y_task_counts['T'] = 1
    w3.y_task_counts['T'] = 1
    before = w1.score
    update_score_on_y_fairness(w1, [w1, w2, w3], cfg)
    assert w1.score > before


if __name__ == '__main__':
    test_early_close_scaling()
    test_multi_y_week_bonus()
    test_cohort_above_average_bonus()
    print('✅ Scoring bonus tests passed')


