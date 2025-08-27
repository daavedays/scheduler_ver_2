import os
import json
from typing import Dict

from datetime import datetime, timezone

try:
    from ..constants import get_y_task_types
except ImportError:
    from constants import get_y_task_types


def _zero_y_task_counts() -> Dict[str, int]:
    keys = get_y_task_types()
    return {k: 0 for k in keys}


def perform_reset(opts: Dict, data_dir: str) -> Dict:
    """Execute reset operations.

    Arguments:
        opts: flags from request body
        data_dir: absolute path to data directory

    Returns a dict suitable for jsonify.
    """
    clear_y = bool(opts.get("clear_y", False))
    clear_y_index_only = bool(opts.get("clear_y_index_only", False))
    # Policy: do NOT allow worker resets via API
    reset_workers_requested = bool(opts.get("reset_workers", False))
    reset_workers = False
    clear_history = bool(opts.get("clear_history", False))
    clear_x = bool(opts.get("clear_x", False))

    removed_y_files = 0

    # 1) Clear Y schedules and index (optional)
    if clear_y or clear_y_index_only:
        import glob
        if clear_y and not clear_y_index_only:
            for path in glob.glob(os.path.join(data_dir, "y_tasks_*.csv")):
                try:
                    os.remove(path)
                    removed_y_files += 1
                except Exception:
                    pass
        # reset index
        index_path = os.path.join(data_dir, "y_tasks_index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

    # 2) Reset worker data (optional)
    updated_workers = 0
    worker_path = os.path.join(data_dir, "worker_data.json")
    if reset_workers:
        try:
            from ..worker import load_workers_from_json, save_workers_to_json
        except Exception:
            # When imported as script
            from worker import load_workers_from_json, save_workers_to_json

        workers = load_workers_from_json(worker_path)
        for w in workers:
            if clear_x:
                w.x_tasks = {}
            # Clear Y tasks and counts
            w.y_tasks = {}
            w.y_task_counts = _zero_y_task_counts()
            try:
                w.y_task_count = 0
            except Exception:
                pass
            if clear_x:
                try:
                    w.x_task_count = 0
                except Exception:
                    pass
            # Clear closings and recomputed schedule fields
            w.closing_history = []
            w.required_closing_dates = []
            w.optimal_closing_dates = []
            w.weekends_home_owed = 0
            w.home_weeks_owed = 0
            # Reset score to neutral baseline
            try:
                w.score = 0.0
            except Exception:
                pass
            updated_workers += 1
        save_workers_to_json(workers, worker_path)

        # Also ensure worker_history.json does not rehydrate stale per-worker Y counts
        try:
            hist_path = os.path.join(data_dir, "worker_history.json")
            history = {}
            if os.path.exists(hist_path):
                with open(hist_path, "r", encoding="utf-8") as f:
                    history = json.load(f) or {}
            now = datetime.now(timezone.utc).isoformat()
            for wid, rec in list(history.items()):
                if not isinstance(rec, dict):
                    history[wid] = {}
                history[wid]["updated_at"] = now
                history[wid]["y_task_counts"] = _zero_y_task_counts()
                history[wid]["y_task_count"] = 0
            with open(hist_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # 3) Clear worker history completely (optional)
    if clear_history:
        try:
            with open(os.path.join(data_dir, "worker_history.json"), "w", encoding="utf-8") as f:
                json.dump({}, f)
        except Exception:
            pass

    # 4) Clear custom X tasks and X CSVs (optional)
    if clear_x:
        try:
            custom_x = os.path.join(data_dir, "custom_x_tasks.json")
            if os.path.exists(custom_x):
                with open(custom_x, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            import glob
            for path in glob.glob(os.path.join(data_dir, "x_tasks_*.csv")):
                try:
                    os.remove(path)
                except Exception:
                    pass
            x_meta = os.path.join(data_dir, "x_task_meta.json")
            if os.path.exists(x_meta):
                with open(x_meta, "w", encoding="utf-8") as f:
                    json.dump({}, f)
        except Exception:
            pass

    result = {
        "success": True,
        "removed_y_files": removed_y_files,
        "updated_workers": updated_workers,
    }
    if reset_workers_requested:
        # Surface to caller that the request was ignored
        result["reset_workers_ignored"] = True
    return result


def reset_worker_data_fields(data_dir: str) -> Dict:
    """Reset specific fields in data/worker_data.json to remove stale values.

    Fields reset:
    - score (0.0)
    - x_tasks (empty {})
    - y_tasks (empty {})
    - closing_history (empty [])
    - required_closing_dates (empty [])
    - optimal_closing_dates (empty [])
    - y_task_counts (zeros using current Y task types)
    - x_task_count (0)
    - y_task_count (0 if present)
    """
    worker_path = os.path.join(data_dir, "worker_data.json")
    try:
        try:
            from ..worker import load_workers_from_json, save_workers_to_json
        except Exception:
            from worker import load_workers_from_json, save_workers_to_json  # type: ignore

        workers = load_workers_from_json(worker_path)
        # Build latest map for qualification name -> id
        try:
            from ..constants import get_y_task_maps  # type: ignore
        except Exception:
            from constants import get_y_task_maps  # type: ignore
        _, name_to_id = get_y_task_maps()
        for w in workers:
            # Preserve qualifications; recompute qualification_ids from current definitions
            try:
                qids: set[int] = set()
                for q in (getattr(w, 'qualifications', []) or []):
                    qid = name_to_id.get(q)
                    if isinstance(qid, int):
                        qids.add(qid)
                setattr(w, 'qualification_ids', qids)
            except Exception:
                pass

            # Reset scores and tasks
            try:
                w.score = 0.0
            except Exception:
                pass
            try:
                w.x_tasks = {}
            except Exception:
                pass
            try:
                w.y_tasks = {}
            except Exception:
                pass

            # Reset closing history and precomputed schedules
            try:
                w.closing_history = []
            except Exception:
                pass
            try:
                w.required_closing_dates = []
            except Exception:
                pass
            try:
                w.optimal_closing_dates = []
            except Exception:
                pass

            # Reset counters
            try:
                w.y_task_counts = _zero_y_task_counts()
            except Exception:
                pass
            try:
                w.x_task_count = 0
            except Exception:
                pass
            try:
                w.y_task_count = 0
            except Exception:
                pass

            # Also zero weekend/home debt fields if present
            try:
                w.weekends_home_owed = 0
                w.home_weeks_owed = 0
            except Exception:
                pass

        save_workers_to_json(workers, worker_path)
        return {"success": True, "updated_workers": len(workers)}
    except Exception as e:
        return {"success": False, "error": str(e)}


