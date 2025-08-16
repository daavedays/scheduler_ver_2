import json
import os
from typing import List

try:
    from .config import DATA_DIR
except ImportError:
    from config import DATA_DIR


DEFAULT_Y_TASK_TYPES: List[str] = [
	"Supervisor",
	"C&N Driver",
	"C&N Escort",
	"Southern Driver",
	"Southern Escort",
]

_TASK_TYPES_CACHE: List[str] | None = None
_TASK_TYPES_FILE = os.path.join(DATA_DIR, 'y_task_types.json')


def _load_types_from_disk() -> List[str]:
	try:
		if os.path.exists(_TASK_TYPES_FILE):
			with open(_TASK_TYPES_FILE, 'r', encoding='utf-8') as f:
				data = json.load(f)
				if isinstance(data, list) and all(isinstance(x, str) for x in data):
					return data
	except Exception:
		pass
	return DEFAULT_Y_TASK_TYPES.copy()


def get_y_task_types() -> List[str]:
	global _TASK_TYPES_CACHE
	if _TASK_TYPES_CACHE is None:
		_TASK_TYPES_CACHE = _load_types_from_disk()
	return _TASK_TYPES_CACHE.copy()


def set_y_task_types(types: List[str]) -> List[str]:
	global _TASK_TYPES_CACHE
	cleaned: List[str] = []
	for t in types:
		if isinstance(t, str):
			name = t.strip()
			if name and name not in cleaned:
				cleaned.append(name)
	if not cleaned:
		cleaned = DEFAULT_Y_TASK_TYPES.copy()
	_TASK_TYPES_CACHE = cleaned
	try:
		with open(_TASK_TYPES_FILE, 'w', encoding='utf-8') as f:
			json.dump(cleaned, f, ensure_ascii=False, indent=2)
	except Exception:
		pass
	return _TASK_TYPES_CACHE.copy()


