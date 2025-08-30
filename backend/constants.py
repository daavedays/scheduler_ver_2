import json
import os
from typing import List, Dict, Any, Tuple, Optional

try:
    from .config import DATA_DIR
except ImportError:
    from config import DATA_DIR

_TASKS_JSON_PATH = os.path.join(DATA_DIR, 'tasks.json')

# Caches
_TASKS_CACHE: Optional[Dict[str, Any]] = None
_Y_DEFS_CACHE: Optional[List[Dict[str, Any]]] = None
_X_DEFS_CACHE: Optional[List[Dict[str, Any]]] = None
_Y_NAME_TO_ID: Optional[Dict[str, int]] = None
_Y_ID_TO_NAME: Optional[Dict[int, str]] = None
_X_NAME_TO_ID: Optional[Dict[str, int]] = None
_X_ID_TO_NAME: Optional[Dict[int, str]] = None


def _load_tasks_json() -> Dict[str, Any]:
	"""Load and cache data/tasks.json."""
	global _TASKS_CACHE
	if _TASKS_CACHE is not None:
		return _TASKS_CACHE
	try:
		with open(_TASKS_JSON_PATH, 'r', encoding='utf-8') as f:
			_TASKS_CACHE = json.load(f) or {}
		return _TASKS_CACHE
	except Exception:
		_TASKS_CACHE = {}
		return _TASKS_CACHE


def reload_tasks_config() -> None:
	"""Clear all caches so next access reloads tasks.json."""
	global _TASKS_CACHE, _Y_DEFS_CACHE, _X_DEFS_CACHE
	global _Y_NAME_TO_ID, _Y_ID_TO_NAME, _X_NAME_TO_ID, _X_ID_TO_NAME
	_TASKS_CACHE = None
	_Y_DEFS_CACHE = None
	_X_DEFS_CACHE = None
	_Y_NAME_TO_ID = None
	_Y_ID_TO_NAME = None
	_X_NAME_TO_ID = None
	_X_ID_TO_NAME = None


def get_y_task_definitions(department: str = 'default') -> List[Dict[str, Any]]:
	"""Return Y-task definitions from tasks.json for a department (default).

	Each definition should include at least: id (int), name (str),
	and optionally requiresQualification (bool), autoAssign (bool).
	"""
	global _Y_DEFS_CACHE
	if _Y_DEFS_CACHE is not None:
		return _Y_DEFS_CACHE.copy()
	data = _load_tasks_json()
	defs_list: List[Dict[str, Any]] = []
	try:
		y = data.get('y_tasks', {})
		departments = y.get('departments', {})
		defs_list = list(departments.get(department, {}).get('definitions', []))
	except Exception:
		defs_list = []
	_Y_DEFS_CACHE = defs_list
	return _Y_DEFS_CACHE.copy()


def get_y_task_types(department: str = 'default') -> List[str]:
	"""Return ordered list of Y-task names from tasks.json (fallback empty)."""
	return [str(d.get('name')) for d in get_y_task_definitions(department) if d.get('name')]


def get_y_task_types_with_auto_assign(department: str = 'default') -> List[Tuple[str, bool]]:
	"""Return ordered list of Y-task names with their autoAssign status from tasks.json."""
	return [(str(d.get('name')), bool(d.get('autoAssign', True))) for d in get_y_task_definitions(department) if d.get('name')]


def get_y_task_ids(department: str = 'default') -> List[int]:
	"""Return ordered list of Y-task IDs from tasks.json."""
	ids: List[int] = []
	for d in get_y_task_definitions(department):
		try:
			ids.append(int(d.get('id')))
		except Exception:
			continue
	return ids


def get_y_task_maps(department: str = 'default') -> Tuple[Dict[int, str], Dict[str, int]]:
	"""Return (id->name, name->id) maps for Y tasks."""
	global _Y_NAME_TO_ID, _Y_ID_TO_NAME
	if _Y_NAME_TO_ID is not None and _Y_ID_TO_NAME is not None:
		return _Y_ID_TO_NAME.copy(), _Y_NAME_TO_ID.copy()
	id_to_name: Dict[int, str] = {}
	name_to_id: Dict[str, int] = {}
	for d in get_y_task_definitions(department):
		try:
			id_val = int(d.get('id'))
			name_val = str(d.get('name'))
			id_to_name[id_val] = name_val
			name_to_id[name_val] = id_val
		except Exception:
			continue
	_Y_ID_TO_NAME = id_to_name
	_Y_NAME_TO_ID = name_to_id
	return id_to_name.copy(), name_to_id.copy()


def y_task_id_from_name(name: str, department: str = 'default') -> Optional[int]:
	"""Lookup Y-task ID by name (None if not found)."""
	_, name_to_id = get_y_task_maps(department)
	return name_to_id.get(name)


def y_task_name_from_id(task_id: int, department: str = 'default') -> Optional[str]:
	"""Lookup Y-task name by ID (None if not found)."""
	id_to_name, _ = get_y_task_maps(department)
	return id_to_name.get(task_id)


def get_x_task_definitions() -> List[Dict[str, Any]]:
	"""Return X-task definitions from tasks.json."""
	global _X_DEFS_CACHE
	if _X_DEFS_CACHE is not None:
		return _X_DEFS_CACHE.copy()
	data = _load_tasks_json()
	defs_list: List[Dict[str, Any]] = []
	try:
		x = data.get('x_tasks', {})
		defs_list = list(x.get('definitions', []))
	except Exception:
		defs_list = []
	_X_DEFS_CACHE = defs_list
	return _X_DEFS_CACHE.copy()


def get_x_task_maps() -> Tuple[Dict[int, str], Dict[str, int]]:
	"""Return (id->name, name->id) maps for X tasks."""
	global _X_NAME_TO_ID, _X_ID_TO_NAME
	if _X_NAME_TO_ID is not None and _X_ID_TO_NAME is not None:
		return _X_ID_TO_NAME.copy(), _X_NAME_TO_ID.copy()
	id_to_name: Dict[int, str] = {}
	name_to_id: Dict[str, int] = {}
	for d in get_x_task_definitions():
		try:
			id_val = int(d.get('id'))
			name_val = str(d.get('name'))
			id_to_name[id_val] = name_val
			name_to_id[name_val] = id_val
		except Exception:
			continue
	_X_ID_TO_NAME = id_to_name
	_X_NAME_TO_ID = name_to_id
	return id_to_name.copy(), name_to_id.copy()


def x_task_id_from_name(name: str) -> Optional[int]:
	"""Lookup X-task ID by name (None if not found)."""
	_, name_to_id = get_x_task_maps()
	return name_to_id.get(name)


def x_task_name_from_id(task_id: int) -> Optional[str]:
	"""Lookup X-task name by ID (None if not found)."""
	id_to_name, _ = get_x_task_maps()
	return id_to_name.get(task_id)


# ---------------------------------------------------------------------------
# Mutators for tasks.json (centralized control with IDs)
# ---------------------------------------------------------------------------

def _save_tasks_json(data: Dict[str, Any]) -> None:
	"""Atomically save tasks.json and clear caches."""
	try:
		tmp_path = f"{_TASKS_JSON_PATH}.tmp"
		with open(tmp_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		os.replace(tmp_path, _TASKS_JSON_PATH)
	except Exception:
		# Fallback to direct write
		with open(_TASKS_JSON_PATH, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
	finally:
		reload_tasks_config()


def _ensure_structure(data: Dict[str, Any]) -> Dict[str, Any]:
	"""Ensure minimal structure exists in tasks.json data."""
	data = data or {}
	if 'y_tasks' not in data:
		data['y_tasks'] = { 'departments': { 'default': { 'definitions': [] } } }
	else:
		data['y_tasks'].setdefault('departments', {})
		data['y_tasks']['departments'].setdefault('default', {})
		data['y_tasks']['departments']['default'].setdefault('definitions', [])
	if 'x_tasks' not in data:
		data['x_tasks'] = { 'definitions': [] }
	else:
		data['x_tasks'].setdefault('definitions', [])
	return data


# ----------------------------- Y task mutators ------------------------------

def set_y_task_definitions(definitions: List[Dict[str, Any]], department: str = 'default') -> List[Dict[str, Any]]:
	"""Replace Y task definitions for a department with the provided list.

	Each item should contain: id (int), name (str), requiresQualification (bool), autoAssign (bool)
	"""
	data = _ensure_structure(_load_tasks_json())
	data['y_tasks']['departments'].setdefault(department, {})
	# Normalize and sort by id
	normalized: List[Dict[str, Any]] = []
	for d in definitions or []:
		try:
			id_val = int(d.get('id'))
			name_val = str(d.get('name'))
			req_q = bool(d.get('requiresQualification', True))
			auto = bool(d.get('autoAssign', True))
			normalized.append({'id': id_val, 'name': name_val, 'requiresQualification': req_q, 'autoAssign': auto})
		except Exception:
			continue
	data['y_tasks']['departments'][department]['definitions'] = sorted(normalized, key=lambda x: x['id'])
	_save_tasks_json(data)
	return get_y_task_definitions(department)


def add_y_task_definition(name: str, requiresQualification: bool = True, autoAssign: bool = True, department: str = 'default') -> Dict[str, Any]:
	"""Add a new Y task definition and return it."""
	data = _ensure_structure(_load_tasks_json())
	defs_list: List[Dict[str, Any]] = list(get_y_task_definitions(department))
	# Determine next ID
	existing_ids = [int(d['id']) for d in defs_list if 'id' in d]
	next_id = (max(existing_ids) + 1) if existing_ids else 1
	new_def = {
		'id': next_id,
		'name': str(name),
		'requiresQualification': bool(requiresQualification),
		'autoAssign': bool(autoAssign),
	}
	defs_list.append(new_def)
	data['y_tasks']['departments'][department]['definitions'] = sorted(defs_list, key=lambda x: x['id'])
	_save_tasks_json(data)
	return new_def


def update_y_task_definition(task_id: int, updates: Dict[str, Any], department: str = 'default') -> Optional[Dict[str, Any]]:
	"""Update fields on a Y task definition. Returns updated def or None if not found."""
	data = _ensure_structure(_load_tasks_json())
	defs_list: List[Dict[str, Any]] = list(get_y_task_definitions(department))
	updated: Optional[Dict[str, Any]] = None
	for d in defs_list:
		if int(d.get('id')) == int(task_id):
			if 'name' in updates:
				d['name'] = str(updates['name'])
			if 'requiresQualification' in updates:
				d['requiresQualification'] = bool(updates['requiresQualification'])
			if 'autoAssign' in updates:
				d['autoAssign'] = bool(updates['autoAssign'])
			updated = d
			break
	if updated is None:
		return None
	data['y_tasks']['departments'][department]['definitions'] = sorted(defs_list, key=lambda x: x['id'])
	_save_tasks_json(data)
	return updated


def delete_y_task_definition(task_id: int, department: str = 'default') -> bool:
	"""Delete a Y task definition by ID. Returns True if removed."""
	data = _ensure_structure(_load_tasks_json())
	defs_list: List[Dict[str, Any]] = list(get_y_task_definitions(department))
	new_list = [d for d in defs_list if int(d.get('id')) != int(task_id)]
	if len(new_list) == len(defs_list):
		return False
	data['y_tasks']['departments'][department]['definitions'] = sorted(new_list, key=lambda x: x['id'])
	_save_tasks_json(data)
	return True


# ----------------------------- X task mutators ------------------------------

def set_x_task_definitions(definitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""Replace X task definitions with the provided list.

	Each item should contain: id (int), name (str), start_day (int 0-6, Sun=0), end_day (int 0-6),
	optional duration_days (int), and optional isDefault (bool).
	"""
	data = _ensure_structure(_load_tasks_json())
	normalized: List[Dict[str, Any]] = []
	for d in definitions or []:
		try:
			id_val = int(d.get('id'))
			name_val = str(d.get('name'))
			sd = int(d.get('start_day'))
			ed = int(d.get('end_day'))
			is_default = bool(d.get('isDefault', False))
			duration = d.get('duration_days')
			nd: Dict[str, Any] = {
				'id': id_val,
				'name': name_val,
				'isDefault': is_default,
				'start_day': sd,
				'end_day': ed,
			}
			if duration is not None:
				try:
					nd['duration_days'] = int(duration)
				except Exception:
					pass
			normalized.append(nd)
		except Exception:
			continue
	data['x_tasks']['definitions'] = sorted(normalized, key=lambda x: x['id'])
	_save_tasks_json(data)
	return get_x_task_definitions()


def add_x_task_definition(name: str, start_day: int, end_day: int, duration_days: Optional[int] = None, isDefault: bool = False) -> Dict[str, Any]:
	"""Add a new X task definition and return it."""
	data = _ensure_structure(_load_tasks_json())
	defs_list: List[Dict[str, Any]] = list(get_x_task_definitions())
	existing_ids = [int(d['id']) for d in defs_list if 'id' in d]
	next_id = (max(existing_ids) + 1) if existing_ids else 1
	new_def: Dict[str, Any] = {
		'id': next_id,
		'name': str(name),
		'isDefault': bool(isDefault),
		'start_day': int(start_day),
		'end_day': int(end_day),
	}
	if duration_days is not None:
		try:
			new_def['duration_days'] = int(duration_days)
		except Exception:
			pass
	defs_list.append(new_def)
	data['x_tasks']['definitions'] = sorted(defs_list, key=lambda x: x['id'])
	_save_tasks_json(data)
	return new_def


def update_x_task_definition(task_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
	"""Update fields on an X task definition. Returns updated def or None if not found."""
	data = _ensure_structure(_load_tasks_json())
	defs_list: List[Dict[str, Any]] = list(get_x_task_definitions())
	updated: Optional[Dict[str, Any]] = None
	for d in defs_list:
		if int(d.get('id')) == int(task_id):
			if 'name' in updates:
				d['name'] = str(updates['name'])
			if 'isDefault' in updates:
				d['isDefault'] = bool(updates['isDefault'])
			if 'start_day' in updates:
				d['start_day'] = int(updates['start_day'])
			if 'end_day' in updates:
				d['end_day'] = int(updates['end_day'])
			if 'duration_days' in updates:
				try:
					d['duration_days'] = int(updates['duration_days'])
				except Exception:
					if 'duration_days' in d:
						d.pop('duration_days', None)
			updated = d
			break
	if updated is None:
		return None
	data['x_tasks']['definitions'] = sorted(defs_list, key=lambda x: x['id'])
	_save_tasks_json(data)
	return updated


def delete_x_task_definition(task_id: int) -> bool:
	"""Delete an X task definition by ID. Returns True if removed."""
	data = _ensure_structure(_load_tasks_json())
	defs_list: List[Dict[str, Any]] = list(get_x_task_definitions())
	new_list = [d for d in defs_list if int(d.get('id')) != int(task_id)]
	if len(new_list) == len(defs_list):
		return False
	data['x_tasks']['definitions'] = sorted(new_list, key=lambda x: x['id'])
	_save_tasks_json(data)
	return True

