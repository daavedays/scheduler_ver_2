from flask import Blueprint, request

try:
    from ..auth_utils import login_user, logout_user, refresh_session_if_logged_in
except ImportError:
    from auth_utils import login_user, logout_user, refresh_session_if_logged_in


auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/login', methods=['POST'])
def login():
	data = request.get_json() or {}
	return login_user(data.get('username'), data.get('password'))


@auth_bp.route('/logout', methods=['POST'])
def logout():
	return logout_user()


@auth_bp.route('/session', methods=['GET'])
def check_session():
	return refresh_session_if_logged_in()


