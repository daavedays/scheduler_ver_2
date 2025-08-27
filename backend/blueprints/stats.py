from flask import Blueprint, jsonify
import os
import glob
from datetime import datetime, date

try:
    from ..config import DATA_DIR
    from ..auth_utils import is_logged_in, require_login
    from ..services.statistics_service import StatisticsService
except ImportError:
    from config import DATA_DIR
    from auth_utils import is_logged_in, require_login
    from services.statistics_service import StatisticsService

try:
	from ..worker import load_workers_from_json
except Exception:
	from worker import load_workers_from_json  # type: ignore


stats_bp = Blueprint('stats', __name__, url_prefix='/api')


@stats_bp.route('/statistics', methods=['GET'])
def get_statistics():
	if not is_logged_in():
		return require_login()
	
	try:
		# Use the comprehensive statistics service
		stats_service = StatisticsService(DATA_DIR)
		
		# Get comprehensive statistics from the single source of truth
		statistics = stats_service.get_comprehensive_statistics()
		
		return jsonify(statistics)
		
	except Exception as e:
		print(f"Statistics error: {e}")  # Add debug logging
		return jsonify({'error': str(e)}), 500


@stats_bp.route('/statistics/refresh', methods=['POST'])
def refresh_statistics():
	"""Endpoint to manually refresh all statistics from data sources."""
	if not is_logged_in():
		return require_login()
	
	try:
		stats_service = StatisticsService(DATA_DIR)
		
		# Load current worker data to update statistics
		workers = load_workers_from_json(os.path.join(DATA_DIR, 'worker_data.json'))
		
		# Convert workers to the format expected by the service
		worker_data = []
		for worker in workers:
			worker_data.append({
				'id': getattr(worker, 'id', None),
				'name': worker.name,
				'qualifications': getattr(worker, 'qualifications', []),
				'closing_interval': getattr(worker, 'closing_interval', 4),
				'officer': getattr(worker, 'officer', False),
				'score': getattr(worker, 'score', 0),
				'seniority': getattr(worker, 'seniority', 'Unknown')
			})
		
		# Update worker data in statistics
		stats_service.update_worker_data(worker_data)
		
		# Update closing history for each worker
		for worker in workers:
			if hasattr(worker, 'closing_history') and worker.closing_history:
				closing_dates = [d.isoformat() if hasattr(d, 'isoformat') else str(d) for d in worker.closing_history]
				stats_service.update_closing_history(worker.id, closing_dates)
		
		return jsonify({'success': True, 'message': 'Statistics refreshed successfully'})
		
	except Exception as e:
		print(f"Statistics refresh error: {e}")
		return jsonify({'error': str(e)}), 500


@stats_bp.route('/statistics/reset', methods=['POST'])
def reset_statistics():
	"""Reset the comprehensive statistics file to its initial state."""
	if not is_logged_in():
		return require_login()
	try:
		stats_service = StatisticsService(DATA_DIR)
		stats = stats_service.reset_statistics()
		return jsonify({'success': True, 'message': 'Statistics reset successfully', 'metadata': stats.get('metadata', {})})
	except Exception as e:
		return jsonify({'error': str(e)}), 500


@stats_bp.route('/statistics/validate', methods=['GET'])
def validate_statistics():
    """Run server-side validation to ensure statistics are consistent."""
    if not is_logged_in():
        return require_login()
    try:
        stats_service = StatisticsService(DATA_DIR)
        result = stats_service.validate()
        return jsonify(result)
    except Exception as e:
        return jsonify({'valid': False, 'issues': [str(e)]}), 500

