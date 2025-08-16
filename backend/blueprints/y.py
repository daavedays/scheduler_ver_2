from flask import Blueprint, jsonify, request
import os
import csv
from datetime import datetime, timedelta, date
import json

try:
    from ..config import DATA_DIR
    from ..utils import cleanup_y_task_index, hydrate_workers_from_history, append_worker_history_snapshot
    from ..auth_utils import is_logged_in, require_login
except ImportError:
    from config import DATA_DIR
    from utils import cleanup_y_task_index, hydrate_workers_from_history, append_worker_history_snapshot
    from auth_utils import is_logged_in, require_login

try:
	from ..y_task_manager import get_y_task_manager
except Exception:
	from y_task_manager import get_y_task_manager  # type: ignore

try:
	from ..worker import load_workers_from_json, save_workers_to_json
except Exception:
	from worker import load_workers_from_json, save_workers_to_json  # type: ignore


y_bp = Blueprint('y_tasks', __name__, url_prefix='/api')


@y_bp.route('/y-tasks/list', methods=['GET'])
def list_y_task_schedules():
	if not is_logged_in():
		return require_login()
	cleanup_y_task_index()
	try:
		y_task_manager = get_y_task_manager(DATA_DIR)
	except Exception:
		return jsonify({'error': 'Y task manager not available'}), 500
	periods = y_task_manager.list_y_task_periods()
	schedules = [{
		'start': p['start_date'],
		'end': p['end_date'],
		'filename': p['filename']
	} for p in periods]
	return jsonify({'schedules': schedules})


@y_bp.route('/y-tasks', methods=['GET'])
def get_y_tasks():
	if not is_logged_in():
		return require_login()
	try:
		y_task_manager = get_y_task_manager(DATA_DIR)
	except Exception:
		return jsonify({'error': 'Y task manager not available'}), 500
	date_q = request.args.get('date')
	start = request.args.get('start')
	end = request.args.get('end')
	filename = None
	if date_q:
		periods = y_task_manager.list_y_task_periods()
		for period in periods:
			try:
				d = datetime.strptime(date_q, '%d/%m/%Y').date()
				s = datetime.strptime(period['start_date'], '%d/%m/%Y').date()
				e = datetime.strptime(period['end_date'], '%d/%m/%Y').date()
				if s <= d <= e:
					filename = period['filename']
					break
			except Exception:
				continue
	elif start and end:
		periods = y_task_manager.list_y_task_periods()
		for period in periods:
			if period['start_date'] == start and period['end_date'] == end:
				filename = period['filename']
				break
	if not filename:
		periods = y_task_manager.list_y_task_periods()
		available = [{
			'start': p['start_date'],
			'end': p['end_date'],
			'filename': p['filename']
		} for p in periods]
		return jsonify({'error': 'No Y task schedule found for given date/range.', 'available': available}), 404
	path = os.path.join(DATA_DIR, filename)
	if not os.path.exists(path):
		return jsonify({'error': 'Y task CSV file missing.'}), 404
	with open(path, 'r', encoding='utf-8') as f:
		return f.read(), 200, {'Content-Type': 'text/csv'}


@y_bp.route('/y-tasks', methods=['POST'])
def save_y_tasks():
	if not is_logged_in():
		return require_login()
	data = request.json or {}
	filename = data.get('filename')
	csv_data = data.get('csv_data')
	dates = data.get('dates') or []
	y_task_names = data.get('y_tasks') or []
	grid = data.get('grid') or []
	start = data.get('start')
	end = data.get('end')
	if not filename and start and end:
		safe_start = start.replace('/', '-')
		safe_end = end.replace('/', '-')
		filename = f"y_tasks_{safe_start}_to_{safe_end}.csv"
	# Normalize to IDs
	if dates and y_task_names and grid:
		workers_for_norm = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
		id_map_norm = {w.id: w for w in workers_for_norm}
		name_map_norm = {w.name: w for w in workers_for_norm}
		normalized_grid = []
		for i, _task in enumerate(y_task_names):
			row = grid[i] if i < len(grid) else []
			norm_row = []
			for j in range(len(dates)):
				cell = (row[j] if j < len(row) else '').strip()
				if not cell or cell == '-':
					norm_row.append('')
					continue
				wid = cell if cell in id_map_norm else (name_map_norm.get(cell).id if name_map_norm.get(cell) else '')
				norm_row.append(wid)
			normalized_grid.append(norm_row)
		# rebuild csv
		import io
		buf = io.StringIO()
		writer = csv.writer(buf)
		writer.writerow(['Y Task'] + dates)
		for i, task in enumerate(y_task_names):
			row_vals = normalized_grid[i] if i < len(normalized_grid) else [''] * len(dates)
			row_vals = (row_vals + [''] * len(dates))[:len(dates)]
			writer.writerow([task] + row_vals)
		csv_data = buf.getvalue()
	if not filename or not csv_data or not dates or not y_task_names or not grid:
		return jsonify({'error': 'Missing required data (need filename/csv_data or start/end, plus dates, y_tasks, grid)'}), 400
	file_path = os.path.join(DATA_DIR, filename)
	with open(file_path, 'w', newline='', encoding='utf-8') as f:
		f.write(csv_data)
	# Update index
	try:
		if start and end:
			start_date_str, end_date_str = start, end
		else:
			start_date_str = filename.split('_to_')[0].replace('y_tasks_', '').replace('-', '/')
			end_date_str = filename.split('_to_')[1].replace('.csv', '').replace('-', '/')
		index_path = os.path.join(DATA_DIR, 'y_tasks_index.json')
		index = {}
		if os.path.exists(index_path):
			with open(index_path, 'r', encoding='utf-8') as f:
				index = json.load(f)
			# migrate legacy string entries
			migrated = False
			for period_key, val in list(index.items()):
				if isinstance(val, str):
					try:
						s, e = period_key.split('_to_')
						s = s.replace('-', '/')
						e = e.replace('-', '/')
						index[period_key] = {
							'filename': val,
							'start_date': s,
							'end_date': e,
							'created_at': datetime.now().isoformat(),
						}
						migrated = True
					except Exception:
						continue
			if migrated:
				with open(index_path, 'w', encoding='utf-8') as f:
					json.dump(index, f, indent=2, ensure_ascii=False)
		key = f"{start_date_str}_to_{end_date_str}"
		index[key] = {
			'filename': filename,
			'start_date': start_date_str,
			'end_date': end_date_str,
			'created_at': datetime.now().isoformat(),
		}
		with open(index_path, 'w', encoding='utf-8') as f:
			json.dump(index, f, indent=2, ensure_ascii=False)
	except Exception as e:
		print(f"Error updating y_tasks_index.json: {e}")
	# Update worker data
	worker_file_path = os.path.join(DATA_DIR, 'worker_data.json')
	workers = load_workers_from_json(worker_file_path)
	hydrate_workers_from_history(workers)
	id_map = {w.id: w for w in workers}
	for i, task in enumerate(y_task_names):
		row = normalized_grid[i] if i < len(normalized_grid) else []  # type: ignore[name-defined]
		for j, worker_id in enumerate(row):
			if not worker_id or j >= len(dates):
				continue
			date_str = dates[j]
			try:
				date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
			except Exception:
				continue
			worker = id_map.get(worker_id)
			if not worker:
				continue
			worker.assign_y_task(date_obj, task)
			if date_obj.weekday() in {3, 4, 5} and worker.can_participate_in_closing():
				friday = date_obj if date_obj.weekday() == 4 else date_obj - timedelta(days=(date_obj.weekday() - 4))
				worker.assign_closing(friday)
	save_workers_to_json(workers, worker_file_path)
	
	# Update statistics service with new Y tasks data
	try:
		from ..services.statistics_service import StatisticsService
		stats_service = StatisticsService(DATA_DIR)
		
		# Build counts per worker_id by task type from normalized_grid
		worker_task_counts = {}
		for i, task in enumerate(y_task_names):
			row = normalized_grid[i] if i < len(normalized_grid) else []
			for j, wid in enumerate(row):
				if not wid or j >= len(dates):
					continue
				worker_task_counts.setdefault(wid, {})
				worker_task_counts[wid][task] = worker_task_counts[wid].get(task, 0) + 1
		
		stats_service.update_y_tasks(filename, worker_task_counts)
		print(f"✅ Statistics updated for Y tasks file: {filename}")
		
		# Update worker data in statistics
		worker_data = []
		for worker in workers:
			worker_data.append({
				'id': worker.id,
				'name': worker.name,
				'qualifications': worker.qualifications,
				'closing_interval': getattr(worker, 'closing_interval', 4),
				'officer': getattr(worker, 'officer', False),
				'score': worker.score,
				'seniority': getattr(worker, 'seniority', 'Unknown'),
				'closing_history': [d.isoformat() for d in getattr(worker, 'closing_history', [])] if getattr(worker, 'closing_history', None) else []
			})
		stats_service.update_worker_data(worker_data)
		print(f"✅ Worker statistics updated after Y tasks save")
	except Exception as e:
		print(f"⚠️  Warning: Failed to update statistics: {e}")
	
	try:
		append_worker_history_snapshot(workers)
	except Exception:
		pass
	# Recalculate closing schedules (DRY helper)
	try:
		if start and end:
			start_date = datetime.strptime(start, '%d/%m/%Y').date()
			end_date = datetime.strptime(end, '%d/%m/%Y').date()
		else:
			start_str = filename.split('_to_')[0].replace('y_tasks_', '').replace('-', '/')  # type: ignore[union-attr]
			end_str = filename.split('_to_')[1].replace('.csv', '').replace('-', '/')
			start_date = datetime.strptime(start_str, '%d/%m/%Y').date()
			end_date = datetime.strptime(end_str, '%d/%m/%Y').date()
		from ..utils import recalc_all_workers_between
		recalc_all_workers_between(workers, start_date, end_date)
		save_workers_to_json(workers, worker_file_path)
		print("✅ Closing schedule recalculation completed after Y tasks save")
	except Exception as e:
		print(f"⚠️  Warning: Failed to update closing schedules after Y tasks save: {e}")
	return jsonify({'success': True, 'message': f'Y tasks saved to {filename}', 'filename': filename})


@y_bp.route('/y-tasks/generate', methods=['POST'])
def generate_y_tasks_schedule():
	if not is_logged_in():
		return require_login()
	data = request.json
	start_date_str = data.get('start')
	end_date_str = data.get('end')
	num_closers = int(data.get('num_closers', 2))
	workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
	hydrate_workers_from_history(workers)
	d0 = datetime.strptime(start_date_str, '%d/%m/%Y').date()
	d1 = datetime.strptime(end_date_str, '%d/%m/%Y').date()
	# Preload X assignments
	try:
		try:
			from . import y_tasks as y_tasks_module
		except ImportError:
			import y_tasks as y_tasks_module  # type: ignore
		x_assignments_merged = {}
		periods_to_load = set()
		for dt in [d0, d1]:
			periods_to_load.add((dt.year, 1 if dt.month <= 6 else 2))
		if d0.year == d1.year and (d0.month <= 6 < d1.month):
			periods_to_load.add((d0.year, 1))
			periods_to_load.add((d0.year, 2))
		for (yr, half) in periods_to_load:
			x_csv = os.path.join(DATA_DIR, f"x_tasks_{yr}_{half}.csv")
			if os.path.exists(x_csv):
				per = y_tasks_module.read_x_tasks(x_csv)
				for wid, days in per.items():
					x_assignments_merged.setdefault(wid, {}).update(days)
		if x_assignments_merged:
			id_to_worker = {w.id: w for w in workers}
			for wid, day_map in x_assignments_merged.items():
				w = id_to_worker.get(wid)
				if not w:
					continue
				for ds, task in day_map.items():
					try:
						x_date = datetime.strptime(ds, '%d/%m/%Y').date()
					except Exception:
						continue
					w.assign_x_task(x_date, task)
	except Exception as e:
		print(f"Warning: could not preload X assignments: {e}")
	# Build tasks_by_date
	tasks_by_date = {}
	try:
		from ..constants import get_y_task_types
	except ImportError:
		from constants import get_y_task_types
	Y_TASKS_ORDER = get_y_task_types()
	current_date = d0
	while current_date <= d1:
		tasks_by_date[current_date] = Y_TASKS_ORDER.copy()
		current_date += timedelta(days=1)
	from ..engine import SchedulingEngineV2
	engine = SchedulingEngineV2()
	result = engine.assign_tasks_for_range(
		workers=workers,
		start_date=d0,
		end_date=d1,
		tasks_by_date=tasks_by_date
	)
	schedule = {}
	for date_obj, assignments in result.get('y_tasks', {}).items():
		schedule[date_obj] = {}
		for task_type, worker_id in assignments:
			worker_name = next((w.name for w in workers if w.id == worker_id), "Unknown")
			schedule[date_obj][task_type] = worker_name
	all_fridays_in_range = [d for d in (d0 + timedelta(i) for i in range((d1 - d0).days + 1)) if d.weekday() == 4]
	from ..scoring import recalc_worker_schedule
	for worker in workers:
		recalc_worker_schedule(worker, all_fridays_in_range)
	try:
		from ..utils import recalc_all_workers_between
		recalc_all_workers_between(workers, d0, d1)
		print(f"✅ Closing schedule recalculation completed after Y task generation")
	except Exception as e:
		print(f"⚠️  Warning: Failed to update closing schedules after Y task generation: {e}")
	save_workers_to_json(workers, os.path.join(DATA_DIR, 'worker_data.json'))
	try:
		append_worker_history_snapshot(workers)
	except Exception:
		pass
	grid = []
	all_dates = [(d0 + timedelta(days=i)) for i in range((d1 - d0).days + 1)]
	for y_task in Y_TASKS_ORDER:
		row = []
		for d in all_dates:
			row.append(schedule.get(d, {}).get(y_task, ''))
		grid.append(row)
	return jsonify({
		"grid": grid,
		"dates": [d.strftime('%d/%m/%Y') for d in all_dates],
		"y_tasks": Y_TASKS_ORDER,
		"logs": result.get('logs', []),
		"success": not result.get('assignment_errors')
	})


@y_bp.route('/y-tasks/available-soldiers', methods=['POST'])
def available_soldiers_for_y_task():
	if not is_logged_in():
		return require_login()
	try:
		from . import y_tasks as y_tasks_module
	except ImportError:
		import y_tasks as y_tasks_module  # type: ignore
	data = request.get_json() or {}
	date_str = data.get('date')
	task = data.get('task')
	current_assignments = data.get('current_assignments', {})
	if not date_str or not task:
		return jsonify({'error': 'Missing date or task'}), 400
	try:
		date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
		workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
		hydrate_workers_from_history(workers)
		year = date_obj.year
		period = 1 if date_obj.month <= 6 else 2
		x_csv = os.path.join(DATA_DIR, f"x_tasks_{year}_{period}.csv")
		if os.path.exists(x_csv):
			x_assignments = y_tasks_module.read_x_tasks(x_csv)
			for worker in workers:
				if worker.id in x_assignments:
					for dstr, task_name in x_assignments[worker.id].items():
						try:
							x_date_obj = datetime.strptime(dstr, '%d/%m/%Y').date()
							worker.assign_x_task(x_date_obj, task_name)
						except Exception:
							pass
		for worker in workers:
			for wid, days in current_assignments.items():
				if wid == worker.id:
					for day_str, task_name in days.items():
						if task_name and task_name != '-':
							try:
								y_date_obj = datetime.strptime(day_str, '%d/%m/%Y').date()
								worker.y_tasks[y_date_obj] = task_name
							except Exception:
								pass
		available = []
		for worker in workers:
			if task not in worker.qualifications:
				continue
			if worker.has_x_task_on_date(date_obj):
				continue
			if date_obj in worker.y_tasks:
				continue
			recently_finished = False
			for i in range(1, 3):
				check_date = date_obj - timedelta(days=i)
				if check_date in worker.x_tasks:
					recently_finished = True
					break
			if recently_finished:
				continue
			available.append(worker)
		return jsonify({'available': [{'id': w.id, 'name': w.name} for w in available]})
	except Exception as e:
		return jsonify({'error': f'Failed to get available soldiers: {str(e)}'}), 500


@y_bp.route('/y-tasks/clear', methods=['POST'])
def clear_y_task_schedule():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	start = data.get('start')
	end = data.get('end')
	if not start or not end:
		return jsonify({'error': 'Missing start or end date'}), 400
	try:
		try:
			from ..y_task_manager import get_y_task_manager
			y_task_manager = get_y_task_manager(DATA_DIR)
		except ImportError:
			from y_task_manager import get_y_task_manager  # type: ignore
			y_task_manager = get_y_task_manager(DATA_DIR)
		index_path = os.path.join(DATA_DIR, 'y_tasks_index.json')
		if not os.path.exists(index_path):
			return jsonify({'error': 'Y task index not found'}), 404
		with open(index_path, 'r', encoding='utf-8') as f:
			index = json.load(f)
		period_key = None
		for key, entry in index.items():
			if isinstance(entry, dict):
				if entry.get('filename') == data.get('filename'):
					period_key = key
					break
			elif isinstance(entry, str):
				if entry == data.get('filename'):
					period_key = key
					break
		if not period_key and data.get('filename', '').startswith('y_tasks_') and '_to_' in data.get('filename', ''):
			try:
				name_part = data.get('filename', '').replace('y_tasks_', '').replace('.csv', '')
				start_part, end_part = name_part.split('_to_')
				derived_key = f"{start_part}_to_{end_part}"
				if derived_key in index:
					period_key = derived_key
			except Exception:
				pass
		if not period_key:
			return jsonify({'error': 'Schedule not found in index'}), 404
		start_date = period_key.split('_to_')[0].replace('-', '/')
		end_date = period_key.split('_to_')[1].replace('-', '/')
		success = y_task_manager.delete_y_task_period(start_date, end_date)
		if success:
			try:
				from ..utils import recalc_all_workers_between
				workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
				start_date_obj = datetime.strptime(start_date, '%d/%m/%Y').date()
				end_date_obj = datetime.strptime(end_date, '%d/%m/%Y').date()
				recalc_all_workers_between(workers, start_date_obj, end_date_obj)
				save_workers_to_json(workers, os.path.join(DATA_DIR, 'worker_data.json'))
				print(f"✅ Closing schedule recalculation completed after deleting Y tasks")
			except Exception as e:
				print(f"⚠️  Warning: Failed to update closing schedules after deleting Y tasks: {e}")
			return jsonify({'success': True})
		else:
			return jsonify({'error': 'Failed to delete schedule'}), 500
	except Exception as e:
		return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@y_bp.route('/y-tasks/delete', methods=['POST'])
def delete_y_task_schedule():
	"""Alias for deleting a Y-task schedule (frontend compatibility).

	Expects JSON with at least `filename` and optionally `start`/`end` in dd/mm/YYYY.
	This mirrors the logic in `/y-tasks/clear` and also synchronizes statistics.
	"""
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	# Reuse the same deletion flow as clear_y_task_schedule
	try:
		try:
			from ..y_task_manager import get_y_task_manager
			y_task_manager = get_y_task_manager(DATA_DIR)
		except ImportError:
			from y_task_manager import get_y_task_manager  # type: ignore
			y_task_manager = get_y_task_manager(DATA_DIR)
		index_path = os.path.join(DATA_DIR, 'y_tasks_index.json')
		if not os.path.exists(index_path):
			return jsonify({'error': 'Y task index not found'}), 404
		with open(index_path, 'r', encoding='utf-8') as f:
			index = json.load(f)
		period_key = None
		for key, entry in index.items():
			if isinstance(entry, dict):
				if entry.get('filename') == data.get('filename'):
					period_key = key
					break
			elif isinstance(entry, str):
				if entry == data.get('filename'):
					period_key = key
					break
		if not period_key and data.get('filename', '').startswith('y_tasks_') and '_to_' in data.get('filename', ''):
			try:
				name_part = data.get('filename', '').replace('y_tasks_', '').replace('.csv', '')
				start_part, end_part = name_part.split('_to_')
				derived_key = f"{start_part}_to_{end_part}"
				if derived_key in index:
					period_key = derived_key
			except Exception:
				pass
		if not period_key:
			return jsonify({'error': 'Schedule not found in index'}), 404
		start_date = period_key.split('_to_')[0].replace('-', '/')
		end_date = period_key.split('_to_')[1].replace('-', '/')
		success = y_task_manager.delete_y_task_period(start_date, end_date)
		if success:
			# Recalc closings
			try:
				from ..utils import recalc_all_workers_between
				workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
				start_date_obj = datetime.strptime(start_date, '%d/%m/%Y').date()
				end_date_obj = datetime.strptime(end_date, '%d/%m/%Y').date()
				recalc_all_workers_between(workers, start_date_obj, end_date_obj)
				save_workers_to_json(workers, os.path.join(DATA_DIR, 'worker_data.json'))
				print(f"✅ Closing schedule recalculation completed after deleting Y tasks")
			except Exception as e:
				print(f"⚠️  Warning: Failed to update closing schedules after deleting Y tasks: {e}")
			# Sync statistics (remove file entry and recompute totals)
			try:
				from ..services.statistics_service import StatisticsService
				stats_service = StatisticsService(DATA_DIR)
				stats = stats_service._load_stats()
				if data.get('filename') in (stats.get('data_sources', {}).get('y_task_files') or []):
					stats['data_sources']['y_task_files'] = [f for f in stats['data_sources']['y_task_files'] if f != data.get('filename')]
				if data.get('filename') in (stats.get('statistics', {}).get('y_tasks') or {}):
					stats['statistics']['y_tasks'].pop(data.get('filename'), None)
				stats_service._recompute_worker_y_counts_from_stats(stats)
				stats_service._update_aggregates(stats)
				stats_service._save_stats(stats)
				print("✅ Statistics synchronized after Y schedule deletion")
			except Exception as e:
				print(f"⚠️  Warning: Failed to sync statistics after deleting Y tasks: {e}")
			return jsonify({'success': True})
		else:
			return jsonify({'error': 'Failed to delete schedule'}), 500
	except Exception as e:
		return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@y_bp.route('/y-tasks/insufficient-workers-report', methods=['POST'])
def get_insufficient_workers_report():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	start = data.get('start')
	end = data.get('end')
	if not start or not end:
		return jsonify({'error': 'Missing start or end date'}), 400
	try:
		d0 = datetime.strptime(start, '%d/%m/%Y').date()
		d1 = datetime.strptime(end, '%d/%m/%Y').date()
		workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
		x_assignments = {}
		try:
			start_period = 1 if d0.month <= 6 else 2
			end_period = 1 if d1.month <= 6 else 2
			periods_to_load = {start_period, end_period}
			if start_period != end_period:
				periods_to_load.update({1, 2})
			try:
				from . import y_tasks as y_tasks_module
			except ImportError:
				import y_tasks as y_tasks_module  # type: ignore
			for period in periods_to_load:
				x_csv = os.path.join(DATA_DIR, f"x_tasks_{d0.year}_{period}.csv")
				if os.path.exists(x_csv):
					period_assignments = y_tasks_module.read_x_tasks(x_csv)
					for worker_id, assignments in period_assignments.items():
						x_assignments.setdefault(worker_id, {}).update(assignments)
			for worker in workers:
				if worker.id in x_assignments:
					for date_str, task_name in x_assignments[worker.id].items():
						try:
							date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
							worker.assign_x_task(date_obj, task_name)
						except Exception:
							pass
		except Exception as e:
			print(f"Warning: Could not load X task data: {e}")
		try:
			from ..constants import get_y_task_types
		except ImportError:
			from constants import get_y_task_types
		Y_TASKS_ORDER = get_y_task_types()
		task_availability = {}
		for task in Y_TASKS_ORDER:
			qualified_workers = [w for w in workers if task in w.qualifications]
			task_availability[task] = {'total_qualified': len(qualified_workers), 'qualified_workers': [w.name for w in qualified_workers]}
		y_task_issues = []
		for task, info in task_availability.items():
			if info['total_qualified'] < 2:
				y_task_issues.append({'task': task, 'qualified_count': info['total_qualified'], 'qualified_workers': info['qualified_workers'], 'severity': 'high' if info['total_qualified'] == 0 else 'medium'})
		weekend_closing_issues = []
		total_workers = len(workers)
		if total_workers < 4:
			weekend_closing_issues.append({'issue': 'insufficient_total_workers', 'total_workers': total_workers, 'recommended_minimum': 4})
		report = {
			'y_task_issues': y_task_issues,
			'weekend_closing_issues': weekend_closing_issues,
			'task_availability': task_availability,
			'summary': {'total_workers': total_workers, 'total_issues': len(y_task_issues) + len(weekend_closing_issues)},
			'detailed_y_task_issues': [],
			'period': f"{start} to {end}"
		}
		report['x_task_overlaps'] = {}
		for w in workers:
			overlaps = {}
			for day_str, task_name in w.x_tasks.items():
				try:
					d = datetime.strptime(day_str, '%d/%m/%Y').date()
				except Exception:
					continue
				if d0 <= d <= d1:
					overlaps[day_str] = task_name
			if overlaps:
				report['x_task_overlaps'][w.id] = overlaps
		return jsonify(report), 200
	except Exception as e:
		return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500


