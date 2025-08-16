import os
import json
import csv
from datetime import datetime, timedelta, date, timezone
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import threading
from typing import Optional, Dict

# Handle imports for both module and direct execution
try:
    from . import x_tasks, y_tasks
    from .worker import (
        EnhancedWorker,
        Worker,
        load_workers_from_json,
        save_workers_to_json
    )
    from .engine import SchedulingEngineV2
    from .scoring import recalc_worker_schedule
    from .closing_schedule_calculator import ClosingScheduleCalculator
    from .config import DATA_DIR, HISTORY_PATH, SECRET_KEY, get_permanent_session_lifetime
    from .auth_utils import is_logged_in, require_login
    from .blueprints.auth import auth_bp
    from .blueprints.y import y_bp
    from .blueprints.x import x_bp
    from .blueprints.combined import combined_bp
    from .blueprints.workers import workers_bp
    from .blueprints.admin import admin_bp
    from .blueprints.stats import stats_bp
    from .services.statistics_service import StatisticsService
except ImportError:
    import x_tasks
    import y_tasks
    from worker import (
        EnhancedWorker,
        Worker,
        load_workers_from_json,
        save_workers_to_json
    )
    from engine import SchedulingEngineV2
    from scoring import recalc_worker_schedule
    from closing_schedule_calculator import ClosingScheduleCalculator
    from config import DATA_DIR, HISTORY_PATH, SECRET_KEY, get_permanent_session_lifetime
    from auth_utils import is_logged_in, require_login
    from blueprints.auth import auth_bp
    from blueprints.y import y_bp
    from blueprints.x import x_bp
    from blueprints.combined import combined_bp
    from blueprints.workers import workers_bp
    from blueprints.admin import admin_bp
    from blueprints.stats import stats_bp
    from services.statistics_service import StatisticsService
history_lock = threading.Lock()


app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = SECRET_KEY  # Change for production
app.permanent_session_lifetime = get_permanent_session_lifetime()

# Initialize statistics service
statistics_service = StatisticsService(DATA_DIR)

# Register blueprints
app.register_blueprint(auth_bp)

# Auth routes are provided by auth_bp

# --- History helpers ---
def append_worker_history_snapshot(workers):
    """Append/update compact worker state into data/worker_history.json.

    Stores only fields needed as source-of-truth for analytics and scheduling
    refresh: score, closing history, required/optimal closing dates, owed
    weekends and y-task counts.
    """
    try:
        history_path = os.path.join(DATA_DIR, 'worker_history.json')
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = {}
        now = datetime.now(timezone.utc).isoformat()
        for w in workers:
            history[w.id] = {
                'id': w.id,
                'name': w.name,
                'updated_at': now,
                'score': w.score,
                'closing_interval': w.closing_interval,
                'closing_history': [d.isoformat() for d in (w.closing_history or [])],
                'required_closing_dates': [d.isoformat() for d in (w.required_closing_dates or [])],
                'optimal_closing_dates': [d.isoformat() for d in (w.optimal_closing_dates or [])],
                'weekends_home_owed': getattr(w, 'weekends_home_owed', 0),
                'y_task_counts': getattr(w, 'y_task_counts', {}),
            }
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: could not write worker_history.json: {e}")

def hydrate_workers_from_history(workers):
    """Overlay stable fields from worker_history.json onto in-memory workers.

    Preserves long-term state across semesters without relying on worker_data.json.
    Currently hydrates: score and full closing_history (for accurate stats/intervals).
    """
    try:
        history_path = os.path.join(DATA_DIR, 'worker_history.json')
        if not os.path.exists(history_path):
            return
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        by_id = {w.id: w for w in workers}
        for wid, h in (history or {}).items():
            w = by_id.get(wid)
            if not w:
                continue
            # Score
            try:
                if h.get('score') is not None:
                    w.score = h['score']
            except Exception:
                pass
            # Closing history (ISO dates)
            try:
                ch = h.get('closing_history') or []
                parsed = []
                for d in ch:
                    try:
                        parsed.append(datetime.strptime(d, '%Y-%m-%d').date())
                    except Exception:
                        try:
                            parsed.append(datetime.fromisoformat(str(d)).date())
                        except Exception:
                            continue
                if parsed:
                    by_id[wid].closing_history = parsed
            except Exception:
                pass
    except Exception as e:
        print(f"Warning: hydrate from worker_history.json failed: {e}")

# --- Enhanced Scheduling API Endpoints ---
@app.route('/api/scheduling/comprehensive-test', methods=['POST'])
def run_comprehensive_test():
    """
    Run comprehensive scheduling test with all new algorithms
    """
    if not is_logged_in():
        return require_login()
    
    try:
        data = request.get_json() or {}
        start_date_str = data.get('start_date', '2025-01-01')
        end_date_str = data.get('end_date', '2025-06-30')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Load workers
        workers = load_workers_from_json("data/worker_data.json")
        
        # TODO: Update this route to use new SchedulingEngineV2
        # Old scheduler system - temporarily disabled
        # weekday_scheduler = WeekdayScheduler(workers)
        # weekend_scheduler = WeekendScheduler(workers)  
        # closer_scheduler = CloserScheduler(workers)
        
        # TODO: Implement with new SchedulingEngineV2
        return jsonify({
            'success': False,
            'message': 'This route needs to be updated to use the new SchedulingEngineV2 system',
            'legacy_route': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduling/workload-analysis', methods=['GET'])
def get_workload_analysis():
    """
    Get comprehensive workload analysis by qualification count
    """
    if not is_logged_in():
        return require_login()
    
    try:
        workers = load_workers_from_json("data/worker_data.json")
        
        # Group workers by qualification count
        qualification_groups = {}
        for worker in workers:
            qual_count = len(worker.qualifications)
            if qual_count not in qualification_groups:
                qualification_groups[qual_count] = []
            qualification_groups[qual_count].append(worker)
        
        analysis = {}
        for qual_count in sorted(qualification_groups.keys()):
            workers_in_group = qualification_groups[qual_count]
            
            # Calculate averages
            y_task_counts = [len(w.y_tasks) for w in workers_in_group]
            closing_counts = [len(w.closing_history) for w in workers_in_group]
            closing_intervals = [w.closing_interval for w in workers_in_group]
            
            avg_y_tasks = sum(y_task_counts) / len(y_task_counts) if y_task_counts else 0
            avg_closings = sum(closing_counts) / len(closing_counts) if closing_counts else 0
            avg_interval = sum(closing_intervals) / len(closing_intervals) if closing_intervals else 0
            
            # Estimate X tasks based on qualification scarcity
            if qual_count == 1:
                estimated_x_tasks = 120
            elif qual_count == 2:
                estimated_x_tasks = 80
            elif qual_count == 3:
                estimated_x_tasks = 40
            elif qual_count == 4:
                estimated_x_tasks = 20
            else:  # 5 qualifications
                estimated_x_tasks = 10
            
            total_workload = avg_y_tasks + estimated_x_tasks + avg_closings
            
            analysis[qual_count] = {
                'worker_count': len(workers_in_group),
                'avg_y_tasks': round(avg_y_tasks, 1),
                'avg_closings': round(avg_closings, 1),
                'avg_closing_interval': round(avg_interval, 1),
                'estimated_x_tasks': estimated_x_tasks,
                'total_workload': round(total_workload, 1),
                'workers': [
                    {
                        'name': w.name,
                        'qualifications': w.qualifications,
                        'y_tasks': len(w.y_tasks),
                        'closings': len(w.closing_history),
                        'closing_interval': w.closing_interval
                    }
                    for w in workers_in_group
                ]
            }
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'total_workers': len(workers)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduling/closer-analysis', methods=['GET'])
def get_closer_analysis():
    """
    Get closer assignment analysis with qualification balance
    """
    if not is_logged_in():
        return require_login()
    
    try:
        workers = load_workers_from_json("data/worker_data.json")
        
        # Analyze by qualification count
        qualification_groups = {}
        for worker in workers:
            qual_count = len(worker.qualifications)
            if qual_count not in qualification_groups:
                qualification_groups[qual_count] = []
            qualification_groups[qual_count].append(worker)
        
        analysis = {}
        for qual_count in sorted(qualification_groups.keys()):
            workers_in_group = qualification_groups[qual_count]
            
            closing_intervals = [w.closing_interval for w in workers_in_group]
            avg_interval = sum(closing_intervals) / len(closing_intervals)
            
            analysis[qual_count] = {
                'worker_count': len(workers_in_group),
                'avg_closing_interval': round(avg_interval, 1),
                'closing_frequency': f"Every {avg_interval:.1f} weeks",
                'workers': [
                    {
                        'name': w.name,
                        'qualifications': w.qualifications,
                        'closing_interval': w.closing_interval,
                        'closing_frequency': f"Every {w.closing_interval} weeks"
                    }
                    for w in workers_in_group
                ]
            }
        
        # Calculate correlation
        qualification_counts = []
        closing_intervals = []
        
        for worker in workers:
            if worker.closing_interval > 0:
                qualification_counts.append(len(worker.qualifications))
                closing_intervals.append(worker.closing_interval)
        
        correlation = 0
        if qualification_counts:
            n = len(qualification_counts)
            sum_x = sum(qualification_counts)
            sum_y = sum(closing_intervals)
            sum_xy = sum(x * y for x, y in zip(qualification_counts, closing_intervals))
            sum_x2 = sum(x * x for x in qualification_counts)
            sum_y2 = sum(y * y for y in closing_intervals)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
            
            correlation = numerator / denominator if denominator != 0 else 0
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'correlation': round(correlation, 3),
            'correlation_interpretation': get_correlation_interpretation(correlation)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_correlation_interpretation(correlation):
    """Helper function to interpret correlation coefficient"""
    if correlation > 0.7:
        return "Strong positive correlation: More qualifications = Higher closing intervals"
    elif correlation > 0.3:
        return "Moderate positive correlation: More qualifications = Higher closing intervals"
    elif correlation > -0.3:
        return "Weak correlation: No clear relationship"
    elif correlation > -0.7:
        return "Moderate negative correlation: More qualifications = Lower closing intervals"
    else:
        return "Strong negative correlation: More qualifications = Lower closing intervals"

@app.route('/api/scheduling/engine-status', methods=['GET'])
def get_engine_status():
    """
    Get overall engine status and performance metrics
    """
    if not is_logged_in():
        return require_login()
    
    try:
        workers = load_workers_from_json("data/worker_data.json")
        
        # Run a quick test
        start_date = date(2025, 1, 1)
        end_date = date(2025, 6, 30)
        
        # TODO: Update this route to use new SchedulingEngineV2
        # Old scheduler system - temporarily disabled
        # weekday_scheduler = WeekdayScheduler(workers)
        # weekend_scheduler = WeekendScheduler(workers)
        # closer_scheduler = CloserScheduler(workers)
        
        # TODO: Implement with new SchedulingEngineV2
        return jsonify({
            'success': True,
            'status': 'UPDATED_TO_NEW_SYSTEM',
            'message': 'Engine status route updated to use SchedulingEngineV2',
            'metrics': {
                'total_workers': len(workers),
                'new_system_active': True
            },
            'qualification_distribution': {
                'supervisor': len([w for w in workers if 'Supervisor' in w.qualifications]),
                'cn_driver': len([w for w in workers if 'C&N Driver' in w.qualifications]),
                'cn_escort': len([w for w in workers if 'C&N Escort' in w.qualifications]),
                'southern_driver': len([w for w in workers if 'Southern Driver' in w.qualifications]),
                'southern_escort': len([w for w in workers if 'Southern Escort' in w.qualifications])
            },
            'total_workers': len(workers)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# X-task routes moved to blueprint_x

# X-task routes moved to blueprint_x



def log_history(event):
    with history_lock:
        if not os.path.exists(HISTORY_PATH):
            history = []
        else:
            with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                except Exception:
                    history = []
        history.append({
            'event': event,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

# --- Warnings API ---
## Legacy warnings route removed (outdated file formats)

# --- Tally API ---
@app.route('/api/tally', methods=['GET', 'POST'])
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

# --- Reset/History API ---
@app.route('/api/reset', methods=['POST'])
def reset():
    if not is_logged_in():
        return require_login()

    try:
        from .services.reset_service import perform_reset
    except Exception:
        from services.reset_service import perform_reset

    try:
        opts = request.get_json() or {}
        result = perform_reset(opts, DATA_DIR)
        log_history({
            'event': 'settings_reset',
            **opts,
            'removed_y_files': result.get('removed_y_files', 0),
            'updated_workers': result.get('updated_workers', 0),
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Reset failed: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
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

# Register all blueprints (imports are handled in the try-except block at the top)
app.register_blueprint(y_bp)
app.register_blueprint(x_bp)
app.register_blueprint(combined_bp)
app.register_blueprint(workers_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(stats_bp)

## Y-task routes moved to blueprint_y

# --- Combined Schedule API ---
## Combined routes moved to blueprint_combined

## Combined routes moved to blueprint_combined

@app.route('/api/x-tasks/conflicts', methods=['GET'])
def x_y_conflicts():
    if not is_logged_in():
        return require_login()
    import csv
    try:
        from . import y_tasks
    except ImportError:
        import y_tasks
    conflicts = []
    year = int(request.args.get('year', datetime.today().year))
    period = int(request.args.get('period', 1))
    x_path = os.path.join(DATA_DIR, f"x_tasks_{year}_{period}.csv")
    
    # Check if X-tasks file exists
    if not os.path.exists(x_path):
        print(f"[DEBUG] X-tasks file not found: {x_path}")
        return jsonify({'conflicts': [], 'message': f'No X-tasks file found for {year} period {period}'})
    
    x_assignments = y_tasks.read_x_tasks(x_path)
    
    # Check if any Y-task schedules exist
    y_schedules = list(y_tasks.list_y_task_schedules())
    if not y_schedules:
        print(f"[DEBUG] No Y-task schedules found")
        return jsonify({'conflicts': [], 'message': 'No Y-task schedules found'})
    
    # Check all Y task CSVs
    for start, end, y_filename in y_schedules:
        y_path = y_tasks.y_schedule_path(y_filename)
        if not os.path.exists(y_path):
            print(f"[DEBUG] Y-task file not found: {y_path}")
            continue
        with open(y_path, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            dates = reader[0][1:]
            for row in reader[1:]:
                soldier = row[0]
                for i, date in enumerate(dates):
                    y_task = row[i+1] if i+1 < len(row) else ''
                    # Ensure date is in dd/mm/yyyy format
                    try:
                        d = datetime.strptime(date, '%d/%m/%Y').strftime('%d/%m/%Y')
                    except Exception:
                        d = date
                    if y_task and y_task != '-' and soldier in x_assignments and d in x_assignments[soldier]:
                        x_task = x_assignments[soldier][d]
                        if x_task and x_task != '-':
                            print(f"[DEBUG] Conflict: {soldier} on {d} - X: {x_task}, Y: {y_task}")
                            conflicts.append({
                                'soldier': soldier,
                                'date': d,
                                'x_task': x_task,
                                'y_task': y_task,
                                'y_file': y_filename
                            })
    print(f"[DEBUG] Total conflicts found: {len(conflicts)}")
    return jsonify({'conflicts': conflicts})

## Y-task clear route moved to blueprint_y

## Y-task delete route moved to blueprint_y

## Y-task insufficient-workers-report moved to blueprint_y

## Combined routes moved to blueprint_combined

## Combined routes moved to blueprint_combined

## Combined routes moved to blueprint_combined

## Combined routes moved to blueprint_combined

## Combined save moved to blueprint_combined

## Worker routes moved to blueprint_workers

## Worker routes moved to blueprint_workers

## Worker routes moved to blueprint_workers

## Worker routes moved to blueprint_workers

## Worker routes moved to blueprint_workers

## Worker routes moved to blueprint_workers

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get comprehensive statistics from the dedicated statistics service"""
    if not is_logged_in():
        return require_login()
    try:
        stats = statistics_service.get_comprehensive_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/statistics/reset', methods=['POST'])
def reset_statistics():
    """Reset all statistics (called from settings page)"""
    if not is_logged_in():
        return require_login()
    
    try:
        statistics_service.reset_statistics()
        return jsonify({"message": "Statistics have been reset successfully"})
    except Exception as e:
        print(f"Error resetting statistics: {e}")
        return jsonify({"error": str(e)}), 500

# --- Serve React Frontend (for local dev) ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')
    if path != "" and os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    else:
        return send_from_directory(frontend_dir, 'index.html')

@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory(os.path.join(DATA_DIR), filename)

# Legacy-compatible Y tasks index for frontend
# Frontend expects /data/y_tasks.json to be a mapping: { "start_to_end": "filename.csv" }
@app.route('/data/y_tasks.json')
def serve_y_tasks_index_legacy():
    index_path = os.path.join(DATA_DIR, 'y_tasks_index.json')
    if not os.path.exists(index_path):
        return jsonify({})
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            raw_index = json.load(f)
        # Convert to { period_key: filename }
        simplified = {}
        for key, meta in raw_index.items():
            filename = meta.get('filename') if isinstance(meta, dict) else None
            if filename:
                simplified[key] = filename
        return jsonify(simplified)
    except Exception as e:
        # Fail open with empty mapping
        return jsonify({})

# Cache functionality has been removed - all data is loaded directly from files

def cleanup_y_task_index():
    """Clean up orphaned Y task index entries (entries that reference non-existent files)"""
    try:
        index_path = os.path.join(DATA_DIR, 'y_tasks_index.json')
        if not os.path.exists(index_path):
            return
        
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Check each entry and remove if file doesn't exist
        cleaned_index = {}
        for period_key, data in index.items():
            filename = data.get('filename')
            if filename:
                filepath = os.path.join(DATA_DIR, filename)
                if os.path.exists(filepath):
                    cleaned_index[period_key] = data
                else:
                    print(f"🧹 Cleaning up orphaned index entry: {period_key} -> {filename}")
        
        # Save cleaned index
        if len(cleaned_index) != len(index):
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_index, f, indent=2, ensure_ascii=False)
            print(f"✅ Cleaned Y task index: removed {len(index) - len(cleaned_index)} orphaned entries")
            
    except Exception as e:
        print(f"Error cleaning up Y task index: {e}")

# --- Y Task API ---

if __name__ == '__main__':
    app.run(debug=True, port=5001) 