import json
import os
import threading
from datetime import datetime, timezone
from typing import List

try:
    from .config import HISTORY_PATH, DATA_DIR
except ImportError:
    from config import HISTORY_PATH, DATA_DIR


history_lock = threading.Lock()


def log_history(event):
	with history_lock:
		if not os.path.exists(HISTORY_PATH):
			history = []
		else:
			with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
				try:
					history = json.load(f)
				except Exception:
					history = []
		history.append({
			'event': event,
			'timestamp': datetime.now(timezone.utc).isoformat()
		})
		with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
			json.dump(history, f, ensure_ascii=False, indent=2)


def append_worker_history_snapshot(workers: List):
	try:
		history_path = os.path.join(DATA_DIR, 'worker_history.json')
		if os.path.exists(history_path):
			with open(history_path, 'r', encoding='utf-8') as f:
				history = json.load(f)
		else:
			history = {}
		now = datetime.now(timezone.utc).isoformat()
		for w in workers:
			history[w.id] = {
				'id': w.id,
				'name': w.name,
				'updated_at': now,
				'score': w.score,
				'closing_interval': w.closing_interval,
				'closing_history': [d.isoformat() for d in (w.closing_history or [])],
				'required_closing_dates': [d.isoformat() for d in (w.required_closing_dates or [])],
				'optimal_closing_dates': [d.isoformat() for d in (w.optimal_closing_dates or [])],
				'weekends_home_owed': getattr(w, 'weekends_home_owed', 0),
				'y_task_counts': getattr(w, 'y_task_counts', {}),
			}
		with open(history_path, 'w', encoding='utf-8') as f:
			json.dump(history, f, indent=2, ensure_ascii=False)
	except Exception as e:
		print(f"Warning: could not write worker_history.json: {e}")


def hydrate_workers_from_history(workers: List):
	try:
		history_path = os.path.join(DATA_DIR, 'worker_history.json')
		if not os.path.exists(history_path):
			return
		with open(history_path, 'r', encoding='utf-8') as f:
			history = json.load(f)
		by_id = {w.id: w for w in workers}
		for wid, h in (history or {}).items():
			w = by_id.get(wid)
			if not w:
				continue
			try:
				if h.get('score') is not None:
					w.score = h['score']
			except Exception:
				pass
			try:
				ch = h.get('closing_history') or []
				parsed = []
				for d in ch:
					try:
						parsed.append(datetime.strptime(d, '%Y-%m-%d').date())
					except Exception:
						try:
							parsed.append(datetime.fromisoformat(str(d)).date())
						except Exception:
							continue
				if parsed:
					by_id[wid].closing_history = parsed
			except Exception:
				pass
	except Exception as e:
		print(f"Warning: hydrate from worker_history.json failed: {e}")


def cleanup_y_task_index():
	"""Clean up orphaned Y task index entries (entries that reference non-existent files)"""
	try:
		index_path = os.path.join(DATA_DIR, 'y_tasks_index.json')
		if not os.path.exists(index_path):
			return
		with open(index_path, 'r', encoding='utf-8') as f:
			index = json.load(f)
		cleaned_index = {}
		for period_key, data in index.items():
			filename = data.get('filename') if isinstance(data, dict) else None
			if filename:
				filepath = os.path.join(DATA_DIR, filename)
				if os.path.exists(filepath):
					cleaned_index[period_key] = data
				else:
					print(f"🧹 Cleaning up orphaned index entry: {period_key} -> {filename}")
		if len(cleaned_index) != len(index):
			with open(index_path, 'w', encoding='utf-8') as f:
				json.dump(cleaned_index, f, indent=2, ensure_ascii=False)
			print(f"✅ Cleaned Y task index: removed {len(index) - len(cleaned_index)} orphaned entries")
	except Exception as e:
		print(f"Error cleaning up Y task index: {e}")


def generate_fridays_between(start_date, end_date):
	"""Return list of Friday dates between start_date and end_date inclusive."""
	from datetime import timedelta
	if start_date is None or end_date is None:
		return []
	fridays = []
	current = start_date
	while current <= end_date:
		if current.weekday() == 4:
			fridays.append(current)
		current += timedelta(days=1)
	return fridays


def make_closing_calculator():
	"""Create ClosingScheduleCalculator with config if available."""
	try:
		from .closing_schedule_calculator import ClosingScheduleCalculator
		from .scoring_config import load_config
		cfg = load_config()
		return ClosingScheduleCalculator(
			allow_single_relief_min1=getattr(cfg, 'CLOSING_RELIEF_ENABLED', True),
			relief_max_per_semester=getattr(cfg, 'CLOSING_RELIEF_MAX_PER_SEMESTER', 1),
		)
	except Exception:
		from .closing_schedule_calculator import ClosingScheduleCalculator
		return ClosingScheduleCalculator()


def recalc_all_workers_between(workers: List, start_date, end_date):
	"""Recalculate closing schedules for workers for Fridays between the given dates."""
	semester_weeks = generate_fridays_between(start_date, end_date)
	calculator = make_closing_calculator()
	calculator.update_all_worker_schedules(workers, semester_weeks)
	return calculator


