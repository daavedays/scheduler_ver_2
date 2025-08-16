from flask import Blueprint, jsonify, request
import os
import io
import csv
import json
from datetime import datetime, timedelta, date

try:
	from ..config import DATA_DIR
except ImportError:
	from config import DATA_DIR

try:
	from .. import x_tasks as x_tasks_module
except Exception:
	import x_tasks as x_tasks_module  # type: ignore

try:
	from ..worker import load_workers_from_json, save_workers_to_json
except Exception:
	from worker import load_workers_from_json, save_workers_to_json  # type: ignore


x_bp = Blueprint('x_tasks', __name__, url_prefix='/api')


@x_bp.route('/x-tasks', methods=['GET'])
def get_x_tasks():
	year = int(request.args.get('year', datetime.today().year))
	period = int(request.args.get('period', 1))
	filename = f"x_tasks_{year}_{period}.csv"
	path = os.path.join(DATA_DIR, filename)
	if not os.path.exists(path) or os.stat(path).st_size == 0:
		workers = x_tasks_module.load_soldiers(os.path.join(DATA_DIR, 'worker_data.json'))
		weeks = x_tasks_module.get_weeks_for_period(year, period)
		headers = ['id', 'name'] + [str(week_num) for week_num, _, _ in weeks]
		subheaders = ['', ''] + [f"{ws.strftime('%d/%m')} - {we.strftime('%d/%m')}" for _, ws, we in weeks]
		rows = []
		for w in workers:
			row = [w.id, w.name] + ['' for _ in range(len(weeks))]
			rows.append(row)
		output = io.StringIO()
		writer = csv.writer(output)
		writer.writerow(headers)
		writer.writerow(subheaders)
		writer.writerows(rows)
		csv_data = output.getvalue()
		custom_tasks = x_tasks_module.load_custom_x_tasks()
		return jsonify({"csv": csv_data, "custom_tasks": custom_tasks, "year": year, "half": period})
	else:
		with open(path, 'r', encoding='utf-8') as f:
			csv_data = f.read()
	custom_tasks = x_tasks_module.load_custom_x_tasks()
	return jsonify({"csv": csv_data, "custom_tasks": custom_tasks, "year": year, "half": period})


@x_bp.route('/x-tasks', methods=['POST'])
def save_x_tasks():
	data = request.get_json() or {}
	csv_data = data.get('csv')
	custom_tasks = data.get('custom_tasks', {})
	year = int(data.get('year', datetime.today().year))
	period = int(data.get('half', 1))
	if not csv_data or not year or not period:
		return jsonify({'error': 'Missing data'}), 400
	filename = f"x_tasks_{year}_{period}.csv"
	x_task_path = os.path.join(DATA_DIR, filename)
	with open(x_task_path, 'w', encoding='utf-8') as f:
		f.write(csv_data)
	x_tasks_module.save_custom_x_tasks(custom_tasks)
	meta_path = os.path.join(DATA_DIR, 'x_task_meta.json')
	with open(meta_path, 'w', encoding='utf-8') as f:
		json.dump({'year': year, 'half': period}, f)  # type: ignore[name-defined]
	
	# Update statistics service with new X tasks data
	try:
		from ..services.statistics_service import StatisticsService
		stats_service = StatisticsService(DATA_DIR)
		
		# Parse CSV into counts per worker_id by task type
		worker_task_counts = {}
		reader = csv.reader(io.StringIO(csv_data))
		rows = list(reader)
		if len(rows) >= 3:
			data_rows = rows[2:]
			for row in data_rows:
				if len(row) < 2:
					continue
				wid = (row[0] or '').strip()
				if not wid:
					continue
				for cell in row[2:]:
					task = (cell or '').strip()
					if not task or task == '-':
						continue
					worker_task_counts.setdefault(wid, {})
					worker_task_counts[wid][task] = worker_task_counts[wid].get(task, 0) + 1
		
		stats_service.update_x_tasks(filename, worker_task_counts)
		print(f"✅ Statistics updated for X tasks file: {filename}")
	except Exception as e:
		print(f"⚠️  Warning: Failed to update statistics for X: {e}")
	
	alerts = []
	try:
		from ..closing_schedule_calculator import ClosingScheduleCalculator
		workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
		affected_workers = set()
		reader = csv.reader(io.StringIO(csv_data))
		rows = list(reader)
		if len(rows) >= 3:
			headers = rows[0]
			subheaders = rows[1]
			data_rows = rows[2:]
			weeks = []
			for i, header in enumerate(headers[2:], 2):
				try:
					week_num = int(header)
					date_range = subheaders[i]
					weeks.append((week_num, date_range))
				except ValueError:
					continue
			for row in data_rows:
				if len(row) < 2:
					continue
				soldier_id = row[0]
				worker = next((w for w in workers if w.id == soldier_id), None)
				if worker:
					affected_workers.add(worker.id)
					worker.x_tasks = {k: v for k, v in worker.x_tasks.items() if not k.startswith(f"{year:04d}")}
					for i, (_week_num, date_range) in enumerate(weeks):
						if i + 2 < len(row):
							task = row[i + 2].strip()
							if task and task != '-':
								try:
									start_str, end_str = date_range.split('-')
									start_date = datetime.strptime(f"{start_str.strip()}/{year}", "%d/%m/%Y").date()
									end_date = datetime.strptime(f"{end_str.strip()}/{year}", "%d/%m/%Y").date()
									current = start_date
									while current <= end_date:
										date_str = current.strftime('%d/%m/%Y')
										worker.x_tasks[date_str] = task
										current += timedelta(days=1)
								except Exception as e:
									print(f"Warning: Could not parse date range {date_range}: {e}")
		for soldier_id, custom_task_list in custom_tasks.items():
			affected_workers.add(soldier_id)
			worker = next((w for w in workers if w.id == soldier_id), None)
			if worker:
				for custom_task in custom_task_list:
					try:
						start_date = datetime.strptime(custom_task['start'], '%d/%m/%Y').date()
						end_date = datetime.strptime(custom_task['end'], '%d/%m/%Y').date()
						current = start_date
						while current <= end_date:
							date_str = current.strftime('%d/%m/%Y')
							worker.x_tasks[date_str] = custom_task['task']
							current += timedelta(days=1)
					except Exception as e:
						print(f"Warning: Could not parse custom task dates: {e}")
		save_workers_to_json(workers, os.path.join(DATA_DIR, 'worker_data.json'))
		
		# Update statistics service with worker data (sanitized)
		try:
			from ..services.statistics_service import StatisticsService
			stats_service = StatisticsService(DATA_DIR)
			workers_data = []
			for w in workers:
				workers_data.append({
					'id': w.id,
					'name': w.name,
					'qualifications': getattr(w, 'qualifications', []),
					'closing_interval': getattr(w, 'closing_interval', 4),
					'officer': getattr(w, 'officer', False),
					'score': getattr(w, 'score', 0),
					'seniority': getattr(w, 'seniority', 'Unknown'),
					'closing_history': [d.isoformat() for d in getattr(w, 'closing_history', [])] if getattr(w, 'closing_history', None) else [],
					'required_closing_dates': [d.isoformat() for d in getattr(w, 'required_closing_dates', [])] if getattr(w, 'required_closing_dates', None) else [],
					'optimal_closing_dates': [d.isoformat() for d in getattr(w, 'optimal_closing_dates', [])] if getattr(w, 'optimal_closing_dates', None) else []
				})
			stats_service.update_worker_data(workers_data)
			print(f"✅ Worker statistics updated after X tasks save")
		except Exception as e:
			print(f"⚠️  Warning: Failed to update worker statistics: {e}")
		
		calculator = ClosingScheduleCalculator()
		semester_weeks = []
		if period == 1:
			start_date = date(year, 1, 1)
			end_date = date(year, 6, 30)
		else:
			start_date = date(year, 7, 1)
			end_date = date(year, 12, 31)
		current = start_date
		while current <= end_date:
			if current.weekday() == 4:
				semester_weeks.append(current)
			current += timedelta(days=1)
		calculator.update_all_worker_schedules(workers, semester_weeks)
		save_workers_to_json(workers, os.path.join(DATA_DIR, 'worker_data.json'))
		alerts = calculator.get_user_alerts()
		print(f"✅ Closing schedule recalculation completed for {len(affected_workers)} workers")
	except Exception as e:
		print(f"⚠️  Warning: Failed to update closing schedules: {e}")
		alerts = [f"Failed to update closing schedules: {e}"]
	return jsonify({'success': True, 'alerts': alerts})


@x_bp.route('/x-tasks/exists', methods=['GET'])
def x_tasks_exists():
	year = int(request.args.get('year', datetime.today().year))
	period = int(request.args.get('period', 1))
	filename = f"x_tasks_{year}_{period}.csv"
	path = os.path.join(DATA_DIR, filename)
	exists = os.path.exists(path) and os.stat(path).st_size > 0
	return jsonify({'exists': exists})


