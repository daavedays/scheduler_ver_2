from flask import Blueprint, jsonify, request
import os
import json
from datetime import datetime, date, timedelta

try:
	from ..config import DATA_DIR
	from ..auth_utils import is_logged_in, require_login
except ImportError:
	from config import DATA_DIR
	from auth_utils import is_logged_in, require_login  # type: ignore

try:
	from ..worker import EnhancedWorker, Worker, load_workers_from_json, save_workers_to_json
except Exception:
	from worker import EnhancedWorker, Worker, load_workers_from_json, save_workers_to_json  # type: ignore


workers_bp = Blueprint('workers', __name__, url_prefix='/api')

WORKER_JSON_PATH = os.path.join(DATA_DIR, 'worker_data.json')
WORKERS: list[EnhancedWorker] = []


def load_workers_to_memory():
	global WORKERS
	WORKERS = load_workers_from_json(WORKER_JSON_PATH)


load_workers_to_memory()


@workers_bp.route('/workers/reload', methods=['POST'])
def reload_workers():
	if not is_logged_in():
		return require_login()
	try:
		load_workers_to_memory()
		return jsonify({'success': True, 'count': len(WORKERS)})
	except Exception as e:
		return jsonify({'error': str(e)}), 500


@workers_bp.route('/workers', methods=['GET'])
def get_workers():
	if not is_logged_in():
		return require_login()
	result = [{
		'id': getattr(w, 'id', None),
		'name': w.name,
		'qualifications': w.qualifications,
		'closing_interval': getattr(w, 'closing_interval', 4),
		'officer': getattr(w, 'officer', False)
	} for w in WORKERS]
	return jsonify({'workers': result})


@workers_bp.route('/workers/<id>/qualifications', methods=['POST'])
def update_worker_qualifications(id):
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	qualifications = data.get('qualifications')
	if not isinstance(qualifications, list):
		return jsonify({'error': 'Invalid qualifications'}), 400
	updated = False
	for w in WORKERS:
		if str(getattr(w, 'id', None)) == str(id):
			w.qualifications = qualifications
			updated = True
			break
	if not updated:
		return jsonify({'error': 'Worker not found'}), 404
	# Persist only; no recalculation or extra writes outside explicit save flows
	save_workers_to_json(WORKERS, WORKER_JSON_PATH)
	return jsonify({'success': True, 'id': id, 'qualifications': qualifications})


@workers_bp.route('/workers', methods=['POST'])
def add_worker():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	required = ['id', 'name', 'qualifications', 'closing_interval']
	for field in required:
		if field not in data:
			return jsonify({'error': f'Missing field: {field}'}), 400
	w = Worker(
		id=str(data['id']),
		name=data['name'],
		start_date=data.get('start_date'),
		qualifications=data.get('qualifications', []),
		closing_interval=data.get('closing_interval', 4),
		officer=data.get('officer', False),
		seniority=data.get('seniority'),
		score=data.get('score'),
	)
	WORKERS.append(w)
	workers_data = []
	for worker in WORKERS:
		worker_dict = {
			'id': worker.id,
			'name': worker.name,
			'qualifications': worker.qualifications,
			'closing_interval': worker.closing_interval,
			'officer': worker.officer,
			'seniority': worker.seniority,
			'score': worker.score,
			'x_tasks': {str(k): v for k, v in worker.x_tasks.items()},
			'y_tasks': {str(k): v for k, v in worker.y_tasks.items()},
			'closing_history': [str(d) for d in worker.closing_history]
		}
		workers_data.append(worker_dict)
	with open(WORKER_JSON_PATH, 'w', encoding='utf-8') as f:
		json.dump(workers_data, f, ensure_ascii=False, indent=2)
	# Return the newly added worker specifically
	new_worker_payload = next((d for d in workers_data if d.get('id') == w.id), (workers_data[-1] if workers_data else {}))
	return jsonify({'success': True, 'worker': new_worker_payload})


@workers_bp.route('/workers/<id>', methods=['PUT'])
def update_worker(id):
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	updated = False
	for w in WORKERS:
		if str(getattr(w, 'id', None)) == str(id):
			w.name = data.get('name', w.name)
			w.start_date = data.get('start_date', w.start_date)
			w.qualifications = data.get('qualifications', w.qualifications)
			# Update derived qualification_ids from centralized maps if provided
			try:
				from ..constants import get_y_task_maps
			except ImportError:
				from constants import get_y_task_maps
			try:
				_, name_to_id = get_y_task_maps()
				qids = set()
				for q in (w.qualifications or []):
					qid = name_to_id.get(q)
					if isinstance(qid, int):
						qids.add(qid)
				setattr(w, 'qualification_ids', qids)
			except Exception:
				pass
			w.closing_interval = data.get('closing_interval', w.closing_interval)
			w.officer = data.get('officer', w.officer)
			seniority = data.get('seniority', w.seniority)
			w.seniority = seniority
			w.score = data.get('score', w.score)
			updated = True
			break
	if not updated:
		return jsonify({'error': 'Worker not found'}), 404
	workers_data = []
	for worker in WORKERS:
		worker_dict = {
			'id': worker.id,
			'name': worker.name,
			'qualifications': worker.qualifications,
			'closing_interval': worker.closing_interval,
			'officer': worker.officer,
			'seniority': worker.seniority,
			'score': worker.score,
			'x_tasks': {str(k): v for k, v in worker.x_tasks.items()},
			'y_tasks': {str(k): v for k, v in worker.y_tasks.items()},
			'closing_history': [str(d) for d in worker.closing_history]
		}
		workers_data.append(worker_dict)
	with open(WORKER_JSON_PATH, 'w', encoding='utf-8') as f:
		json.dump(workers_data, f, ensure_ascii=False, indent=2)
	# Return the updated worker specifically
	updated_worker_payload = next((d for d in workers_data if str(d.get('id')) == str(id)), (workers_data[0] if workers_data else {}))
	return jsonify({'success': True, 'worker': updated_worker_payload})


@workers_bp.route('/workers/<id>', methods=['DELETE'])
def delete_worker(id):
	if not is_logged_in():
		return require_login()
	global WORKERS
	before = len(WORKERS)
	WORKERS = [w for w in WORKERS if str(getattr(w, 'id', None)) != str(id)]
	after = len(WORKERS)
	workers_data = []
	for worker in WORKERS:
		worker_dict = {
			'id': worker.id,
			'name': worker.name,
			'qualifications': worker.qualifications,
			'closing_interval': worker.closing_interval,
			'officer': worker.officer,
			'seniority': worker.seniority,
			'score': worker.score,
			'x_tasks': {str(k): v for k, v in worker.x_tasks.items()},
			'y_tasks': {str(k): v for k, v in worker.y_tasks.items()},
			'closing_history': [str(d) for d in worker.closing_history]
		}
		workers_data.append(worker_dict)
	with open(WORKER_JSON_PATH, 'w', encoding='utf-8') as f:
		json.dump(workers_data, f, ensure_ascii=False, indent=2)
	if before == after:
		return jsonify({'error': 'Worker not found'}), 404
	return jsonify({'success': True})


