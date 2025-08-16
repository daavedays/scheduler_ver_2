from flask import Blueprint, jsonify, request, send_from_directory
import os
import json
from datetime import datetime, timezone

try:
    from ..config import DATA_DIR, HISTORY_PATH
    from ..auth_utils import is_logged_in, require_login
    from ..constants import get_y_task_types, set_y_task_types
except ImportError:
    from config import DATA_DIR, HISTORY_PATH
    from auth_utils import is_logged_in, require_login
    from constants import get_y_task_types, set_y_task_types


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
	if not is_logged_in():
		return require_login()
	data = request.get_json() or {}
	types = data.get('types', [])
	if not isinstance(types, list) or not all(isinstance(t, str) for t in types):
		return jsonify({'error': 'types must be a list of strings'}), 400
	updated = set_y_task_types(types)
	return jsonify({'success': True, 'types': updated})


@admin_bp.route('/data/<path:filename>')
def serve_data(filename):
	return send_from_directory(os.path.join(DATA_DIR), filename)


