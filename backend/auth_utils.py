from datetime import datetime, timedelta, timezone
from flask import jsonify, session

try:
    from .config import USERS, SESSION_TIMEOUT_MINUTES
except ImportError:
    from config import USERS, SESSION_TIMEOUT_MINUTES


def is_logged_in() -> bool:
	user = session.get('user')
	expires_at = session.get('expires_at')
	if not user or not expires_at:
		return False
	if isinstance(expires_at, str):
		try:
			expires_at = datetime.fromisoformat(expires_at)
		except Exception:
			return False
	# Assume UTC if no timezone info
	if expires_at.tzinfo is None:
		expires_at = expires_at.replace(tzinfo=timezone.utc)
	return datetime.now(timezone.utc) < expires_at


def require_login():
	return jsonify({'error': 'Authentication required'}), 401


def login_user(username: str, password: str):
	if username in USERS and USERS[username] == password:
		session['user'] = username
		session['expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=SESSION_TIMEOUT_MINUTES)).isoformat()
		session.permanent = True
		return jsonify({'success': True, 'user': username})
	return jsonify({'error': 'Invalid credentials'}), 401


def logout_user():
	session.clear()
	return jsonify({'success': True})


def refresh_session_if_logged_in():
	if is_logged_in():
		session['expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=SESSION_TIMEOUT_MINUTES)).isoformat()
		return jsonify({'logged_in': True, 'user': session['user']})
	session.clear()
	return jsonify({'logged_in': False})


