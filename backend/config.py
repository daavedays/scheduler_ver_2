import os
from datetime import timedelta


# Session and security
SESSION_TIMEOUT_MINUTES = 120
SECRET_KEY = 'super_secret_key_for_local_dev'  # Change for production

# Data directories
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
HISTORY_PATH = os.path.join(BASE_DIR, '..', 'data', 'history.json')

# Simple in-memory user store
USERS = {
	'bossy_bobby': 'QWE123..',
	'Dav': '8320845',
}


def get_permanent_session_lifetime() -> timedelta:
	return timedelta(minutes=SESSION_TIMEOUT_MINUTES)


