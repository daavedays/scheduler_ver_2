from flask import Blueprint, jsonify, request
import os
import csv
import io
import glob
import re
from datetime import datetime, timedelta

try:
    from ..config import DATA_DIR
    from ..auth_utils import is_logged_in, require_login
except ImportError:
    from config import DATA_DIR
    from auth_utils import is_logged_in, require_login


combined_bp = Blueprint('combined', __name__, url_prefix='/api/combined')


@combined_bp.route('', methods=['GET'])
def get_combined():
	if not is_logged_in():
		return require_login()
	try:
		try:
			from . import y_tasks
		except ImportError:
			import y_tasks  # type: ignore
		schedules = y_tasks.list_y_task_schedules()
		if not schedules:
			return '', 200, {'Content-Type': 'text/csv'}
		start, end, y_filename = schedules[0]
		y_path = y_tasks.y_schedule_path(y_filename)
		if not os.path.exists(y_path):
			return '', 200, {'Content-Type': 'text/csv'}
		with open(y_path, 'r', encoding='utf-8') as f:
			rows = list(csv.reader(f))
		if not rows or len(rows) < 2:
			return '', 200, {'Content-Type': 'text/csv'}
		dates = rows[0][1:]
		y_task_names = [r[0] for r in rows[1:]]
		y_grid = [r[1:] for r in rows[1:]]
		x_files = glob.glob(os.path.join(DATA_DIR, 'x_tasks_*.csv'))
		x_assignments = {}
		if x_files:
			def extract_year_period(fname):
				m = re.search(r'x_tasks_(\d+)_(\d+)\.csv', fname)
				if m:
					return int(m.group(1)), int(m.group(2))
				return (0, 0)
			x_files.sort(key=extract_year_period, reverse=True)
			x_csv = x_files[0]
			x_assignments = y_tasks.read_x_tasks(x_csv)
		out = io.StringIO()
		writer = csv.writer(out)
		writer.writerow(["Y Tasks"] + dates)
		for i, task in enumerate(y_task_names):
			writer.writerow([task] + y_grid[i])
		x_task_set = set()
		for name, day_map in x_assignments.items():
			for d in dates:
				t = day_map.get(d, '-')
				if t and t != '-' and t not in y_task_names:
					x_task_set.add(t)
		if x_task_set:
			writer.writerow([])
			writer.writerow(["X Tasks"] + ["" for _ in dates])
			for xt in sorted(x_task_set):
				row = []
				for d in dates:
					assigned = ''
					for name, day_map in x_assignments.items():
						if day_map.get(d, '-') == xt:
							assigned = name
							break
					row.append(assigned)
				writer.writerow([xt] + row)
		csv_text = out.getvalue()
		return csv_text, 200, {'Content-Type': 'text/csv'}
	except Exception:
		return '', 200, {'Content-Type': 'text/csv'}


@combined_bp.route('/grid', methods=['GET'])
def get_combined_grid():
	if not is_logged_in():
		return require_login()
	try:
		try:
			from . import y_tasks
		except ImportError:
			import y_tasks  # type: ignore
		start = request.args.get('start')
		end = request.args.get('end')
		y_schedules = y_tasks.list_y_task_schedules()
		if start and end:
			y_filename = None
			for s, e, f in y_schedules:
				if s == start and e == end:
					y_filename = f
					break
			if not y_filename:
				return jsonify({'error': 'Y schedule not found for given period'}), 404
		else:
			if not y_schedules:
				return jsonify({'error': 'No Y schedules found'}), 404
			start, end, y_filename = y_schedules[0]
		y_path = y_tasks.y_schedule_path(y_filename)
		if not os.path.exists(y_path):
			return jsonify({'error': 'Y schedule CSV not found'}), 404
		with open(y_path, 'r', encoding='utf-8') as f:
			reader = list(csv.reader(f))
			if not reader or len(reader) < 2:
				return jsonify({'error': 'Invalid Y schedule CSV format'}), 400
			dates = reader[0][1:]
			y_tasks_list = [row[0] for row in reader[1:]]
			y_grid = [row[1:] for row in reader[1:]]
		DATA = os.path.join(os.path.dirname(__file__), '..', 'data')
		x_files = glob.glob(os.path.join(DATA_DIR, 'x_tasks_*.csv'))
		if not x_files:
			x_assignments = {}
		else:
			def extract_year_period(fname):
				m = re.search(r'x_tasks_(\d+)_(\d+)\.csv', fname)
				if m:
					return int(m.group(1)), int(m.group(2))
				return (0, 0)
			x_files.sort(key=extract_year_period, reverse=True)
			x_csv = x_files[0]
			try:
				x_assignments = y_tasks.read_x_tasks(x_csv)
			except Exception:
				x_assignments = {}
		x_tasks_set = set()
		for name, day_map in x_assignments.items():
			for d in dates:
				t = day_map.get(d, '-')
				if t and t != '-' and t not in y_tasks_list:
					x_tasks_set.add(t)
		x_grid = []
		for x_task in sorted(x_tasks_set):
			row = []
			for d in dates:
				found = ''
				for name, day_map in x_assignments.items():
					if day_map.get(d, '-') == x_task:
						found = name
						break
				row.append(found)
			x_grid.append(row)
		row_labels = y_tasks_list + sorted(x_tasks_set)
		grid = y_grid + x_grid
		return jsonify({'row_labels': row_labels, 'dates': dates, 'grid': grid, 'y_period': {'start': start, 'end': end, 'filename': y_filename}})
	except Exception:
		return jsonify({'error': 'Failed'}), 500


@combined_bp.route('/available-dates', methods=['GET'])
def get_combined_available_dates():
	try:
		try:
			from . import y_tasks
		except ImportError:
			import y_tasks  # type: ignore
		y_schedules = y_tasks.list_y_task_schedules()
		all_dates = set()
		for start, end, y_filename in y_schedules:
			y_path = y_tasks.y_schedule_path(y_filename)
			if not os.path.exists(y_path):
				continue
			with open(y_path, 'r', encoding='utf-8') as f:
				reader = list(csv.reader(f))
				if not reader or len(reader) < 2:
					continue
				dates = reader[0][1:]
				all_dates.update(dates)
		all_dates = sorted(all_dates, key=lambda d: [int(x) for x in d.split('/')][::-1])
		return jsonify({'dates': all_dates})
	except Exception:
		return jsonify({'dates': []})


@combined_bp.route('/by-date', methods=['GET'])
def get_combined_by_date():
	if not is_logged_in():
		return require_login()
	date = request.args.get('date')
	if not date:
		return jsonify({'error': 'Missing date'}), 400
	try:
		try:
			from . import y_tasks, x_tasks
		except ImportError:
			import y_tasks, x_tasks  # type: ignore
		y_schedules = y_tasks.list_y_task_schedules()
		y_assignments = {}
		y_tasks_list = ["Supervisor", "C&N Driver", "C&N Escort", "Southern Driver", "Southern Escort"]
		for start, end, y_filename in y_schedules:
			y_path = y_tasks.y_schedule_path(y_filename)
			if not os.path.exists(y_path):
				continue
			with open(y_path, 'r', encoding='utf-8') as f:
				reader = list(csv.reader(f))
				if not reader or len(reader) < 2:
					continue
				header = reader[0]
				date_idx = None
				for i, d in enumerate(header[1:]):
					if d == date:
						date_idx = i + 1
						break
				if date_idx is None:
					continue
				for row in reader[1:]:
					y_task = row[0]
					if y_task in y_tasks_list:
						soldier = row[date_idx] if date_idx < len(row) else ''
						y_assignments[y_task] = soldier
		x_files = glob.glob(os.path.join(DATA_DIR, 'x_tasks_*.csv'))
		if not x_files:
			x_assignments = {}
			x_tasks_set = set()
		else:
			def extract_year_period(fname):
				m = re.search(r'x_tasks_(\d+)_(\d+)\.csv', fname)
				if m:
					return int(m.group(1)), int(m.group(2))
				return (0, 0)
			x_files.sort(key=extract_year_period, reverse=True)
			x_csv = x_files[0]
			x_assignments = y_tasks.read_x_tasks(x_csv)
			x_tasks_set = set()
			for name, day_map in x_assignments.items():
				task = day_map.get(date, '-')
				if task and task != '-' and task not in y_tasks_list:
					x_tasks_set.add(task)
		x_tasks_list = sorted(x_tasks_set)
		x_assignments_by_task = {task: '' for task in x_tasks_list}
		for name, day_map in x_assignments.items():
			task = day_map.get(date, '-')
			if task and task != '-' and task in x_tasks_list:
				x_assignments_by_task[task] = name
		return jsonify({'date': date, 'y_tasks': y_tasks_list, 'x_tasks': x_tasks_list, 'y_assignments': y_assignments, 'x_assignments': x_assignments_by_task})
	except Exception:
		return jsonify({'error': 'Failed'}), 500


@combined_bp.route('/grid-full', methods=['GET'])
def get_combined_grid_full():
	if not is_logged_in():
		return require_login()
	try:
		try:
			from . import y_tasks
		except ImportError:
			import y_tasks  # type: ignore
		y_schedules = y_tasks.list_y_task_schedules()
		all_dates = set()
		y_data_by_date = {}
		for start, end, y_filename in y_schedules:
			y_path = y_tasks.y_schedule_path(y_filename)
			if not os.path.exists(y_path):
				continue
			with open(y_path, 'r', encoding='utf-8') as f:
				reader = list(csv.reader(f))
				if not reader or len(reader) < 2:
					continue
				dates = reader[0][1:]
				for d in dates:
					all_dates.add(d)
				for row in reader[1:]:
					y_task = row[0]
					for i, d in enumerate(dates):
						if d not in y_data_by_date:
							y_data_by_date[d] = {}
						y_data_by_date[d][y_task] = row[i+1] if i+1 < len(row) else ''
		all_dates = sorted(all_dates, key=lambda d: [int(x) for x in d.split('/')][::-1])
		x_files = glob.glob(os.path.join(DATA_DIR, 'x_tasks_*.csv'))
		if not x_files:
			x_assignments = {}
			x_tasks_set = set()
		else:
			def extract_year_period(fname):
				m = re.search(r'x_tasks_(\d+)_(\d+)\.csv', fname)
				if m:
					return int(m.group(1)), int(m.group(2))
				return (0, 0)
			x_files.sort(key=extract_year_period, reverse=True)
			x_csv = x_files[0]
			x_assignments = y_tasks.read_x_tasks(x_csv)
			x_tasks_set = set()
			for name, day_map in x_assignments.items():
				for d, task in day_map.items():
					if task and task != '-' and task not in ["Supervisor", "C&N Driver", "C&N Escort", "Southern Driver", "Southern Escort"]:
						x_tasks_set.add(task)
		x_tasks_list = sorted(x_tasks_set)
		grid = []
		y_tasks_list = ["Supervisor", "C&N Driver", "C&N Escort", "Southern Driver", "Southern Escort"]
		for y_task in y_tasks_list:
			row = []
			for d in all_dates:
				row.append(y_data_by_date.get(d, {}).get(y_task, ''))
			grid.append(row)
		for x_task in x_tasks_list:
			row = []
			for d in all_dates:
				found = []
				for name, day_map in x_assignments.items():
					if day_map.get(d, '-') == x_task:
						found.append(name)
				row.append(', '.join(found))
			grid.append(row)
		row_labels = y_tasks_list + x_tasks_list
		return jsonify({'row_labels': row_labels, 'dates': all_dates, 'grid': grid})
	except Exception:
		return jsonify({'error': 'Failed'}), 500


@combined_bp.route('/by-range', methods=['GET'])
def get_combined_by_range():
	if not is_logged_in():
		return require_login()
	start = request.args.get('start')
	end = request.args.get('end')
	if not start or not end:
		return jsonify({'error': 'Missing start or end date'}), 400
	try:
		try:
			from ..y_task_manager import get_y_task_manager
		except Exception:
			from y_task_manager import get_y_task_manager  # type: ignore
		y_task_manager = get_y_task_manager(DATA_DIR)
		d0 = datetime.strptime(start, '%d/%m/%Y').date()
		d1 = datetime.strptime(end, '%d/%m/%Y').date()
		dates_set = set()
		y_data_by_date = {}
		periods = y_task_manager.list_y_task_periods()
		for period in periods:
			period_start = period['start_date']
			period_end = period['end_date']
			filename = period['filename']
			try:
				p_start = datetime.strptime(period_start, '%d/%m/%Y').date()
				p_end = datetime.strptime(period_end, '%d/%m/%Y').date()
				req_start = d0
				req_end = d1
				if p_start <= req_end and p_end >= req_start:
					y_path = os.path.join(DATA_DIR, filename)
					if os.path.exists(y_path):
						with open(y_path, 'r', encoding='utf-8') as f:
							reader = list(csv.reader(f))
							if not reader or len(reader) < 2:
								continue
							file_dates = reader[0][1:]
							for row in reader[1:]:
								y_task = row[0]
								for i, d in enumerate(file_dates):
									try:
										dd = datetime.strptime(d, '%d/%m/%Y').date()
									except Exception:
										continue
									if dd < d0 or dd > d1:
										continue
									dates_set.add(d)
									if d not in y_data_by_date:
										y_data_by_date[d] = {}
									y_data_by_date[d][y_task] = row[i+1] if i+1 < len(row) else ''
			except Exception:
				continue
			dates = sorted(list(dates_set), key=lambda ds: datetime.strptime(ds, '%d/%m/%Y').date())
		x_files = glob.glob(os.path.join(DATA_DIR, 'x_tasks_*.csv'))
		if not x_files:
			x_assignments = {}
		else:
			def extract_year_period(fname):
				m = re.search(r'x_tasks_(\d+)_(\d+)\.csv', fname)
				if m:
					return int(m.group(1)), int(m.group(2))
				return (0, 0)
			x_files.sort(key=extract_year_period)
			x_csv = x_files[0] if x_files else None
			x_assignments = {}
			if x_csv and os.path.exists(x_csv):
				try:
					try:
						from . import y_tasks as y_tasks_module
					except ImportError:
						import y_tasks as y_tasks_module  # type: ignore
					x_assignments = y_tasks_module.read_x_tasks(x_csv)
				except Exception:
					x_assignments = {}
		x_tasks_set = set()
		for name, day_map in x_assignments.items():
			for d in dates:
				task = day_map.get(d, '-')
				if task and task != '-' and task not in ["Supervisor", "C&N Driver", "C&N Escort", "Southern Driver", "Southern Escort"]:
					x_tasks_set.add(task)
		x_tasks_list = sorted(x_tasks_set)
		x_grid = []
		from ..worker import load_workers_from_json
		workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
		worker_id_to_name = {w.id: w.name for w in workers}
		for x_task in x_tasks_list:
			row = []
			for d in dates:
				found = []
				for name, day_map in x_assignments.items():
					if day_map.get(d, '-') == x_task:
						worker_name = worker_id_to_name.get(name, name)
						found.append(worker_name)
				row.append(', '.join(found))
			x_grid.append(row)
		y_tasks_list = ["Supervisor", "C&N Driver", "C&N Escort", "Southern Driver", "Southern Escort"]
		grid = []
		for y_task in y_tasks_list:
			row = []
			for d in dates:
				row.append(y_data_by_date.get(d, {}).get(y_task, ''))
			grid.append(row)
		row_labels = y_tasks_list + x_tasks_list
		grid = grid + x_grid
		return jsonify({'row_labels': row_labels, 'dates': dates, 'grid': grid})
	except Exception:
		return jsonify({'error': 'Failed'}), 500


@combined_bp.route('/save', methods=['POST'])
def save_combined_csv():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	csv_data = data.get('csv')
	filename = data.get('filename')
	if not csv_data or not filename:
		return jsonify({'error': 'Missing csv or filename'}), 400
	try:
		m = re.search(r'combined_(\d{2}-\d{2}-\d{4})_(\d{2}-\d{2}-\d{4})', filename)
		inferred_dates = []
		if m:
			start_str = m.group(1).replace('-', '/')
			end_str = m.group(2).replace('-', '/')
			try:
				from ..y_task_manager import get_y_task_manager
				y_task_manager = get_y_task_manager(DATA_DIR)
			except Exception:
				y_task_manager = None
			if y_task_manager:
				periods = y_task_manager.list_y_task_periods()
				for period in periods:
					if period['start_date'] == start_str and period['end_date'] == end_str:
						y_path = os.path.join(DATA_DIR, period['filename'])
						if os.path.exists(y_path):
							with open(y_path, 'r', encoding='utf-8') as yf:
								rows = list(csv.reader(yf))
								if rows:
									inferred_dates = rows[0][1:]
						break
		buf = io.StringIO(csv_data)
		rows = list(csv.reader(buf))
		if rows:
			header = rows[0]
			if inferred_dates:
				rows[0] = ["Task"] + inferred_dates
			else:
				cleaned = ["Task"]
				for h in header[1:]:
					if re.fullmatch(r"\d+", h or ""):
						continue
					if h and h.lower() != 'name':
						cleaned.append(h)
				rows[0] = cleaned if len(cleaned) > 1 else header
			for r in range(1, len(rows)):
				rows[r] = [ ('' if (c == '-' or c is None) else c) for c in rows[r] ]
		out = io.StringIO()
		writer = csv.writer(out)
		writer.writerows(rows)
		csv_data = out.getvalue()
	except Exception:
		pass
	path = os.path.join(DATA_DIR, filename)
	with open(path, 'w', encoding='utf-8') as f:
		f.write(csv_data)
	# Do not recalc or persist worker data on combined save; only CSV is updated
	return jsonify({'success': True, 'filename': filename})


