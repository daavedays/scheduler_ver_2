from flask import Blueprint, jsonify, request, send_from_directory
import os
import json
from datetime import datetime, timezone

try:
    from ..config import DATA_DIR, HISTORY_PATH
    from ..auth_utils import is_logged_in, require_login
    from ..constants import (
        get_y_task_types,
        get_y_task_definitions,
        set_y_task_definitions,
        add_y_task_definition,
        update_y_task_definition,
        delete_y_task_definition,
        get_x_task_definitions,
        set_x_task_definitions,
        add_x_task_definition,
        update_x_task_definition,
        delete_x_task_definition,
    )
except ImportError:
    from config import DATA_DIR, HISTORY_PATH
    from auth_utils import is_logged_in, require_login
    from constants import (
        get_y_task_types,
        get_y_task_definitions,
        set_y_task_definitions,
        add_y_task_definition,
        update_y_task_definition,
        delete_y_task_definition,
        get_x_task_definitions,
        set_x_task_definitions,
        add_x_task_definition,
        update_x_task_definition,
        delete_x_task_definition,
    )


admin_bp = Blueprint('admin', __name__)


def log_history(event):
	if not os.path.exists(HISTORY_PATH):
		history = []
	else:
		with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
			try:
				history = json.load(f)
			except Exception:
				history = []
	history.append({'event': event, 'timestamp': datetime.now(timezone.utc).isoformat()})
	with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
		json.dump(history, f, ensure_ascii=False, indent=2)


@admin_bp.route('/api/tally', methods=['GET', 'POST'])
def tally():
	if not is_logged_in():
		return require_login()
	path = os.path.join(DATA_DIR, 'soldier_state.json')
	if request.method == 'GET':
		with open(path, 'r', encoding='utf-8') as f:
			return f.read(), 200, {'Content-Type': 'application/json'}
	else:
		data = request.data.decode('utf-8')
		with open(path, 'w', encoding='utf-8') as f:
			f.write(data)
		return jsonify({'success': True})


@admin_bp.route('/api/reset', methods=['POST'])
def reset():
	if not is_logged_in():
		return require_login()
	try:
		from ..services.reset_service import perform_reset
	except Exception:
		from services.reset_service import perform_reset  # type: ignore
	try:
		opts = request.get_json() or {}
		result = perform_reset(opts, DATA_DIR)
		log_history({'event': 'settings_reset', **opts, 'removed_y_files': result.get('removed_y_files', 0), 'updated_workers': result.get('updated_workers', 0)})
		return jsonify(result)
	except Exception as e:
		return jsonify({'error': f'Reset failed: {str(e)}'}), 500


@admin_bp.route('/api/workers/reset', methods=['POST'])
def reset_workers_data():
	if not is_logged_in():
		return require_login()
	try:
		try:
			from ..services.reset_service import reset_worker_data_fields
		except Exception:
			from services.reset_service import reset_worker_data_fields  # type: ignore

		# Perform the worker data reset on disk
		result = reset_worker_data_fields(DATA_DIR)
		if not result.get('success', False):
			return jsonify({'error': result.get('error', 'Unknown error')}), 500

		# Reload in-memory workers so changes take immediate effect
		try:
			from ..blueprints.workers import load_workers_to_memory  # type: ignore
		except Exception:
			try:
				from blueprints.workers import load_workers_to_memory  # type: ignore
			except Exception:
				load_workers_to_memory = None  # type: ignore
		if callable(load_workers_to_memory):
			load_workers_to_memory()

		# Log to history
		log_history({'event': 'worker_data_reset', 'updated_workers': result.get('updated_workers', 0)})
		return jsonify({'success': True, 'updated_workers': result.get('updated_workers', 0)})
	except Exception as e:
		return jsonify({'error': f'Worker data reset failed: {str(e)}'}), 500


@admin_bp.route('/api/history', methods=['GET'])
def get_history():
	if not is_logged_in():
		return require_login()
	if not os.path.exists(HISTORY_PATH):
		return jsonify({'history': []})
	with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
		try:
			history = json.load(f)
		except Exception:
			history = []
	return jsonify({'history': history})


@admin_bp.route('/api/y-tasks/types', methods=['GET'])
def api_get_y_task_types():
	if not is_logged_in():
		return require_login()
	return jsonify({'types': get_y_task_types()})


@admin_bp.route('/api/y-tasks/types', methods=['POST'])
def api_set_y_task_types():
	# Backward-compatible endpoint to set names only
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	types = data.get('types', [])
	if not isinstance(types, list) or not all(isinstance(t, str) for t in types):
		return jsonify({'error': 'types must be a list of strings'}), 400
	# Merge with existing to preserve ids/flags
	existing = {d.get('name'): d for d in (get_y_task_definitions() or [])}
	defs = []
	next_id = max([int(d.get('id', 0)) for d in existing.values()] + [0]) + 1
	for name in types:
		if name in existing:
			defs.append(existing[name])
		else:
			defs.append({'id': next_id, 'name': name, 'requiresQualification': True, 'autoAssign': True})
			next_id += 1
	updated = set_y_task_definitions(defs)
	return jsonify({'success': True, 'definitions': updated, 'types': [d['name'] for d in updated]})


# --- Y task definitions CRUD ---
@admin_bp.route('/api/y-tasks/definitions', methods=['GET'])
def api_get_y_defs():
	if not is_logged_in():
		return require_login()
	return jsonify({'definitions': get_y_task_definitions()})


@admin_bp.route('/api/y-tasks/definitions', methods=['PUT'])
def api_set_y_defs():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	definitions = data.get('definitions', [])
	if not isinstance(definitions, list):
		return jsonify({'error': 'definitions must be a list'}), 400
	updated = set_y_task_definitions(definitions)
	return jsonify({'success': True, 'definitions': updated})


@admin_bp.route('/api/y-tasks/definitions', methods=['POST'])
def api_add_y_def():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	name = data.get('name')
	if not name:
		return jsonify({'error': 'name is required'}), 400
	req_q = bool(data.get('requiresQualification', True))
	auto = bool(data.get('autoAssign', True))
	created = add_y_task_definition(name, req_q, auto)
	return jsonify({'success': True, 'definition': created})


@admin_bp.route('/api/y-tasks/definitions/<int:task_id>', methods=['PATCH'])
def api_update_y_def(task_id: int):
	if not is_logged_in():
		return require_login()
	updates = request.get_json() or {}
	updated = update_y_task_definition(task_id, updates)
	if not updated:
		return jsonify({'error': 'Not found'}), 404
	return jsonify({'success': True, 'definition': updated})


@admin_bp.route('/api/y-tasks/definitions/<int:task_id>', methods=['DELETE'])
def api_delete_y_def(task_id: int):
	if not is_logged_in():
		return require_login()
	ok = delete_y_task_definition(task_id)
	if not ok:
		return jsonify({'error': 'Not found'}), 404
	return jsonify({'success': True})


# --- X task definitions CRUD ---
@admin_bp.route('/api/x-tasks/definitions', methods=['GET'])
def api_get_x_defs():
	if not is_logged_in():
		return require_login()
	return jsonify({'definitions': get_x_task_definitions()})


@admin_bp.route('/api/x-tasks/definitions', methods=['PUT'])
def api_set_x_defs():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	definitions = data.get('definitions', [])
	if not isinstance(definitions, list):
		return jsonify({'error': 'definitions must be a list'}), 400
	updated = set_x_task_definitions(definitions)
	return jsonify({'success': True, 'definitions': updated})


@admin_bp.route('/api/x-tasks/definitions', methods=['POST'])
def api_add_x_def():
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	name = data.get('name')
	if not name:
		return jsonify({'error': 'name is required'}), 400
	try:
		sd = int(data.get('start_day'))
		ed = int(data.get('end_day'))
	except Exception:
		return jsonify({'error': 'start_day and end_day must be integers'}), 400
	duration = data.get('duration_days')
	duration_int = None
	if duration is not None:
		try:
			duration_int = int(duration)
		except Exception:
			duration_int = None
	is_default = bool(data.get('isDefault', False))
	created = add_x_task_definition(name, sd, ed, duration_int, is_default)
	return jsonify({'success': True, 'definition': created})


@admin_bp.route('/api/x-tasks/definitions/<int:task_id>', methods=['PATCH'])
def api_update_x_def(task_id: int):
	if not is_logged_in():
		return require_login()
	updates = request.get_json() or {}
	updated = update_x_task_definition(task_id, updates)
	if not updated:
		return jsonify({'error': 'Not found'}), 404
	return jsonify({'success': True, 'definition': updated})


@admin_bp.route('/api/x-tasks/definitions/<int:task_id>', methods=['DELETE'])
def api_delete_x_def(task_id: int):
	if not is_logged_in():
		return require_login()
	ok = delete_x_task_definition(task_id)
	if not ok:
		return jsonify({'error': 'Not found'}), 404
	return jsonify({'success': True})


@admin_bp.route('/data/<path:filename>')
def serve_data(filename):
	return send_from_directory(os.path.join(DATA_DIR), filename)


