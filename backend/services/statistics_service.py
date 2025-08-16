#!/usr/bin/env python3
"""
Dedicated Statistics Service
Maintains accurate statistics in a JSON file that serves as the single source of truth.
Updates automatically when X or Y schedules change.
"""

import json
import os
import glob
import threading
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import csv


_GLOBAL_STATS_LOCK = threading.Lock()

class StatisticsService:
    """
    Service to maintain a single source of truth for all statistics data.
    This service aggregates data from X tasks, Y tasks, closing history, and worker data
    into one comprehensive JSON file that the statistics page can read from.
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.stats_file = os.path.join(data_dir, 'statistics.json')
        # Use a module-level lock to coordinate all instances in-process
        self.lock = _GLOBAL_STATS_LOCK
        self._ensure_stats_file_exists()
    
    def _ensure_stats_file_exists(self):
        """Ensure the comprehensive statistics file exists with basic structure."""
        if not os.path.exists(self.stats_file):
            self._save_stats(self._initial_stats())

    def _initial_stats(self) -> Dict[str, Any]:
        """Return a fresh initial statistics structure."""
        now_iso = datetime.now().isoformat()
        return {
            'metadata': {
                'created_at': now_iso,
                'last_updated': now_iso,
                'version': '1.0'
            },
            'data_sources': {
                'x_task_files': [],
                'y_task_files': [],
                'worker_data': None
            },
            'statistics': {
                'workers': {},
                'x_tasks': {},
                'y_tasks': {},
                'closing_intervals': {},
                'aggregates': {}
            },
            'summary': {
                'total_workers': 0,
                'total_x_tasks': 0,
                'total_y_tasks': 0
            }
        }
    
    def _save_stats(self, stats: Dict[str, Any]):
        """Atomically save statistics to the JSON file."""
        try:
            tmp_path = f"{self.stats_file}.tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.stats_file)
        except Exception as e:
            print(f"Warning: Could not save comprehensive statistics: {e}")
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load statistics from the JSON file. If invalid/missing, reinitialize and save."""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # Rebuild a valid structure to self-heal corruption
            stats = self._initial_stats()
            self._save_stats(stats)
            return stats
    
    def update_worker_data(self, workers: List[Dict[str, Any]]):
        """Update worker information in the statistics."""
        stats = self._load_stats()
        
        # Update worker data
        stats['statistics']['workers'] = {}
        for worker in workers:
            worker_id = worker.get('id', str(worker.get('name', 'unknown')))
            stats['statistics']['workers'][worker_id] = {
                'id': worker_id,
                'name': worker.get('name', 'Unknown'),
                'qualifications': worker.get('qualifications', []),
                'closing_interval': worker.get('closing_interval', 4),
                'officer': worker.get('officer', False),
                'score': worker.get('score', 0),
                'seniority': worker.get('seniority', 'Unknown'),
                'closing_history': worker.get('closing_history', []),
                'required_closing_dates': worker.get('required_closing_dates', []),
                'optimal_closing_dates': worker.get('optimal_closing_dates', [])
            }
        
        # Update worker data source
        stats['data_sources']['worker_data'] = {
            'updated_at': datetime.now().isoformat(),
            'worker_count': len(workers)
        }
        
        # Update closing interval analysis
        self._update_closing_interval_analysis(stats)
        
        # Update aggregates
        self._update_aggregates(stats)
        
        stats['metadata']['last_updated'] = datetime.now().isoformat()
        self._save_stats(stats)
    
    def update_x_tasks(self, x_task_file: str, x_tasks_data: Dict[str, Any]):
        """Update statistics when X tasks are saved"""
        with self.lock:
            stats = self._load_stats()
            
            # Update data sources
            if x_task_file not in stats["data_sources"]["x_task_files"]:
                stats["data_sources"]["x_task_files"].append(x_task_file)
            
            # Update X tasks statistics
            stats["statistics"]["x_tasks"][x_task_file] = {
                "file": x_task_file,
                "updated_at": datetime.now().isoformat(),
                "data": x_tasks_data
            }
            
            # Update worker X task counts
            self._update_worker_x_task_counts(stats, x_tasks_data)
            
            # Update aggregates
            self._update_aggregates(stats)
            
            stats["metadata"]["last_updated"] = datetime.now().isoformat()
            self._save_stats(stats)
    
    def update_y_tasks(self, y_task_file: str, y_tasks_data: Dict[str, Any]):
        """Update statistics when Y tasks are saved"""
        with self.lock:
            stats = self._load_stats()
            
            # Update data sources
            if y_task_file not in stats["data_sources"]["y_task_files"]:
                stats["data_sources"]["y_task_files"].append(y_task_file)
            
            # Update Y tasks statistics
            stats["statistics"]["y_tasks"][y_task_file] = {
                "file": y_task_file,
                "updated_at": datetime.now().isoformat(),
                "data": y_tasks_data
            }
            
            # Update worker Y task counts
            self._update_worker_y_task_counts(stats, y_tasks_data)
            
            # Update aggregates
            self._update_aggregates(stats)
            
            stats["metadata"]["last_updated"] = datetime.now().isoformat()
            self._save_stats(stats)
    
    def update_closing_history(self, worker_id: str, closing_dates: List[str]):
        """Update closing history for a specific worker."""
        stats = self._load_stats()
        
        if 'closing_history' not in stats:
            stats['closing_history'] = {}
        
        stats['closing_history'][worker_id] = {
            'dates': closing_dates,
            'count': len(closing_dates),
            'last_updated': datetime.now().isoformat()
        }
        
        stats['summary']['total_closing_events'] = sum(
            worker_data['count'] 
            for worker_data in stats['closing_history'].values()
        )
        
        stats['metadata']['last_updated'] = datetime.now().isoformat()
        self._save_stats(stats)
    
    def _update_worker_x_task_counts(self, stats: Dict[str, Any], x_tasks_data: Dict[str, Any]):
        """Update worker X task counts from X tasks data"""
        for worker_id, tasks in x_tasks_data.items():
            if worker_id not in stats["statistics"]["workers"]:
                continue
            
            if "x_task_counts" not in stats["statistics"]["workers"][worker_id]:
                stats["statistics"]["workers"][worker_id]["x_task_counts"] = {}
            
            # Count tasks by type
            task_counts = {}
            for task_type, count in tasks.items():
                if task_type not in task_counts:
                    task_counts[task_type] = 0
                task_counts[task_type] += count
            
            stats["statistics"]["workers"][worker_id]["x_task_counts"] = task_counts
            stats["statistics"]["workers"][worker_id]["total_x_tasks"] = sum(task_counts.values())
    
    def _update_worker_y_task_counts(self, stats: Dict[str, Any], y_tasks_data: Dict[str, Any]):
        """Update worker Y task counts from Y tasks data"""
        for worker_id, tasks in y_tasks_data.items():
            if worker_id not in stats["statistics"]["workers"]:
                continue
            
            if "y_task_counts" not in stats["statistics"]["workers"][worker_id]:
                stats["statistics"]["workers"][worker_id]["y_task_counts"] = {}
            
            # Count tasks by type
            task_counts = {}
            for task_type, count in tasks.items():
                if task_type not in task_counts:
                    task_counts[task_type] = 0
                task_counts[task_type] += count
            
            stats["statistics"]["workers"][worker_id]["y_task_counts"] = task_counts
            stats["statistics"]["workers"][worker_id]["total_y_tasks"] = sum(task_counts.values())

    def _recompute_worker_y_counts_from_stats(self, stats: Dict[str, Any]):
        """Recompute all worker Y task totals from current stats['statistics']['y_tasks']."""
        # Reset
        for w in stats["statistics"]["workers"].values():
            w["y_task_counts"] = {}
            w["total_y_tasks"] = 0
        # Aggregate from remaining y_tasks entries
        y_tasks_dict = stats["statistics"].get("y_tasks", {}) or {}
        for period in y_tasks_dict.values():
            per_worker = period.get("data", {}) or {}
            for wid, counts in per_worker.items():
                if wid not in stats["statistics"]["workers"]:
                    continue
                for task, cnt in (counts or {}).items():
                    stats["statistics"]["workers"][wid].setdefault("y_task_counts", {})
                    stats["statistics"]["workers"][wid]["y_task_counts"][task] = (
                        stats["statistics"]["workers"][wid]["y_task_counts"].get(task, 0) + int(cnt)
                    )
                stats["statistics"]["workers"][wid]["total_y_tasks"] = sum(
                    stats["statistics"]["workers"][wid]["y_task_counts"].values()
                )
    
    def _update_closing_interval_analysis(self, stats: Dict[str, Any]):
        """Calculate accurate closing interval analysis"""
        closing_intervals = {}
        
        for worker_id, worker_data in stats["statistics"]["workers"].items():
            if not worker_data.get("closing_history") or worker_data.get("closing_interval", 0) <= 0:
                continue
            
            # Parse closing dates
            closing_dates = []
            for closing_str in worker_data["closing_history"]:
                try:
                    if isinstance(closing_str, str):
                        closing_date = datetime.strptime(closing_str, '%Y-%m-%d').date()
                    else:
                        closing_date = closing_str
                    closing_dates.append(closing_date)
                except (ValueError, TypeError):
                    continue
            
            if len(closing_dates) < 2:
                continue
            
            closing_dates.sort()
            
            # Calculate actual intervals between consecutive closings
            intervals = []
            for i in range(1, len(closing_dates)):
                days_between = (closing_dates[i] - closing_dates[i-1]).days
                weeks_between = days_between / 7.0
                intervals.append(weeks_between)
            
            if intervals:
                actual_avg_interval = sum(intervals) / len(intervals)
                target_interval = worker_data["closing_interval"]
                
                # Calculate accuracy percentage
                accuracy_percentage = max(0, 100 - (abs(actual_avg_interval - target_interval) / target_interval) * 100)
                
                closing_intervals[worker_id] = {
                    "worker_id": worker_id,
                    "worker_name": worker_data["name"],
                    "target_interval": target_interval,
                    "actual_avg_interval": round(actual_avg_interval, 2),
                    "min_interval": round(min(intervals), 2),
                    "max_interval": round(max(intervals), 2),
                    "total_closings": len(closing_dates),
                    "accuracy_percentage": round(accuracy_percentage, 1),
                    "intervals": [round(i, 2) for i in intervals],
                    "closing_dates": [d.isoformat() for d in closing_dates],
                    "color": 'green' if accuracy_percentage >= 80 else 'orange' if accuracy_percentage >= 60 else 'red'
                }
        
        stats["statistics"]["closing_intervals"] = closing_intervals
    
    def _update_aggregates(self, stats: Dict[str, Any]):
        """Update aggregate statistics"""
        workers = stats["statistics"]["workers"]
        
        # Calculate aggregates
        total_workers = len(workers)
        total_x_tasks = sum(w.get("total_x_tasks", 0) for w in workers.values())
        total_y_tasks = sum(w.get("total_y_tasks", 0) for w in workers.values())
        
        # Closing interval accuracy summary
        closing_intervals = stats["statistics"]["closing_intervals"]
        workers_with_closings = len(closing_intervals)
        if workers_with_closings > 0:
            avg_accuracy = sum(w["accuracy_percentage"] for w in closing_intervals.values()) / workers_with_closings
            workers_above_90 = len([w for w in closing_intervals.values() if w["accuracy_percentage"] >= 90])
            workers_above_80 = len([w for w in closing_intervals.values() if w["accuracy_percentage"] >= 80])
            workers_below_50 = len([w for w in closing_intervals.values() if w["accuracy_percentage"] < 50])
        else:
            avg_accuracy = 0
            workers_above_90 = 0
            workers_above_80 = 0
            workers_below_50 = 0
        
        stats["statistics"]["aggregates"] = {
            "total_workers": total_workers,
            "total_x_tasks": total_x_tasks,
            "total_y_tasks": total_y_tasks,
            "closing_interval_summary": {
                "workers_with_closings": workers_with_closings,
                "average_accuracy": round(avg_accuracy, 1),
                "workers_above_90_percent": workers_above_90,
                "workers_above_80_percent": workers_above_80,
                "workers_below_50_percent": workers_below_50
            }
        }
        
        # Update summary
        stats["summary"]["total_workers"] = total_workers
        stats["summary"]["total_x_tasks"] = total_x_tasks
        stats["summary"]["total_y_tasks"] = total_y_tasks
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get all statistics data in the format expected by the frontend."""
        stats = self._load_stats()
        
        # Safe access wrappers
        stats_section = stats.get('statistics', {}) or {}
        workers_dict = stats_section.get('workers', {}) or {}
        x_tasks_dict = stats_section.get('x_tasks', {}) or {}
        y_tasks_dict = stats_section.get('y_tasks', {}) or {}
        closing_intervals_dict = stats_section.get('closing_intervals', {}) or {}
        aggregates_dict = stats_section.get('aggregates', {}) or {}
        summary = stats.get('summary', {}) or {'total_workers': 0, 'total_x_tasks': 0, 'total_y_tasks': 0}

        # Legacy structure fallback (flat keys at root)
        if not workers_dict and isinstance(stats.get('workers', None), dict):
            workers_dict = stats.get('workers') or {}
        if not x_tasks_dict and isinstance(stats.get('x_tasks', None), dict):
            x_tasks_dict = stats.get('x_tasks') or {}
        if not y_tasks_dict and isinstance(stats.get('y_tasks', None), dict):
            y_tasks_dict = stats.get('y_tasks') or {}
        if not closing_intervals_dict and isinstance(stats.get('closing_intervals', None), dict):
            closing_intervals_dict = stats.get('closing_intervals') or {}
        if not aggregates_dict and isinstance(stats.get('aggregates', None), dict):
            aggregates_dict = stats.get('aggregates') or {}
        
        # If empty data, attempt a one-time refresh from files
        if not workers_dict and not x_tasks_dict and not y_tasks_dict:
            self.refresh_all_statistics()
            stats = self._load_stats()
            stats_section = stats.get('statistics', {}) or {}
            workers_dict = stats_section.get('workers', {}) or {}
            x_tasks_dict = stats_section.get('x_tasks', {}) or {}
            y_tasks_dict = stats_section.get('y_tasks', {}) or {}
            closing_intervals_dict = stats_section.get('closing_intervals', {}) or {}
            aggregates_dict = stats_section.get('aggregates', {}) or {}
            summary = stats.get('summary', {}) or {'total_workers': 0, 'total_x_tasks': 0, 'total_y_tasks': 0}
            workers = list(workers_dict.values())

        # Transform data for frontend consumption
        workers = list(workers_dict.values())
        
        # Generate pie chart data
        x_tasks_pie = []
        y_tasks_pie = []
        combined_pie = []
        
        def x_tasks_count_by_id(worker_id: str) -> int:
            total = 0
            for period in x_tasks_dict.values():
                per_worker = period.get('data', {}) or {}
                if worker_id in per_worker:
                    total += sum((per_worker.get(worker_id) or {}).values())
            return total
        
        def y_tasks_count_by_id(worker_id: str) -> int:
            total = 0
            for period in y_tasks_dict.values():
                per_worker = period.get('data', {}) or {}
                if worker_id in per_worker:
                    total += sum((per_worker.get(worker_id) or {}).values())
            return total
        
        x_total_all = 0
        y_total_all = 0
        for worker in workers:
            worker_id = worker.get('id')
            worker_name = worker.get('name', '')
            if not worker_id:
                continue
            x_count = x_tasks_count_by_id(worker_id)
            y_count = y_tasks_count_by_id(worker_id)
            x_total_all += x_count
            y_total_all += y_count
            if x_count > 0:
                x_tasks_pie.append({'name': worker_name, 'value': x_count, 'worker_id': worker_id})
            if y_count > 0:
                y_tasks_pie.append({'name': worker_name, 'value': y_count, 'worker_id': worker_id})
            if x_count > 0 or y_count > 0:
                combined_pie.append({'name': worker_name, 'value': x_count + y_count, 'worker_id': worker_id})

        # Add percentage fields expected by frontend labels
        if x_tasks_pie:
            total = sum(item['value'] for item in x_tasks_pie) or 1
            for item in x_tasks_pie:
                item['percentage'] = round(item['value'] / total * 100, 1)
        if y_tasks_pie:
            total = sum(item['value'] for item in y_tasks_pie) or 1
            for item in y_tasks_pie:
                item['percentage'] = round(item['value'] / total * 100, 1)
        
        # Generate simplified timeline data (aggregate per file/period)
        x_tasks_timeline = []
        for x_file, period_data in x_tasks_dict.items():
            data_map = period_data.get('data', {}) or {}
            total_tasks = sum(sum((task_counts or {}).values()) for task_counts in data_map.values())
            year = None
            half = None
            try:
                parts = x_file.replace('.csv', '').split('_')
                year = int(parts[2]) if len(parts) > 2 else None
                half = int(parts[3]) if len(parts) > 3 else None
            except Exception:
                pass
            entry = {'period': x_file, 'total_tasks': total_tasks}
            if year is not None and half is not None:
                entry.update({'year': year, 'half': half})
            x_tasks_timeline.append(entry)
        
        # Helpers for metrics
        def x_tasks_count(worker_id: str) -> int:
            return x_tasks_count_by_id(worker_id)
        
        def y_tasks_count(worker_id: str) -> int:
            return y_tasks_count_by_id(worker_id)
        
        # Seniority distribution
        seniority_distribution: Dict[str, Dict[str, int]] = {}
        for w in workers:
            bucket = str(w.get('seniority')) if w.get('seniority') is not None else 'Unknown'
            entry = seniority_distribution.setdefault(bucket, {'x_tasks': 0, 'y_tasks': 0, 'workers': 0})
            entry['x_tasks'] += x_tasks_count(w.get('id', ''))
            entry['y_tasks'] += y_tasks_count(w.get('id', ''))
            entry['workers'] += 1
        
        # Score vs tasks
        score_vs_tasks = [{
            'worker_name': w.get('name', ''),
            'score': w.get('score', 0),
            'total_tasks': x_tasks_count(w.get('id', '')) + y_tasks_count(w.get('id', '')),
            'x_tasks': x_tasks_count(w.get('id', '')),
            'y_tasks': y_tasks_count(w.get('id', '')),
        } for w in workers]
        
        # Qualification utilization (dict)
        qualification_utilization: Dict[str, Dict[str, float]] = {}
        for w in workers:
            for q in (w.get('qualifications') or []):
                qd = qualification_utilization.setdefault(q, {'qualified_workers': 0, 'total_tasks': 0, 'avg_tasks_per_worker': 0.0})
                qd['qualified_workers'] += 1
                qd['total_tasks'] += x_tasks_count(w.get('id', '')) + y_tasks_count(w.get('id', ''))
        for q, d in qualification_utilization.items():
            qw = d['qualified_workers'] or 1
            d['avg_tasks_per_worker'] = round(d['total_tasks'] / qw, 2)
        
        # Task distribution histogram
        def bucket(total: int) -> str:
            if total == 0:
                return '0'
            if total <= 2:
                return '1-2'
            if total <= 5:
                return '3-5'
            if total <= 9:
                return '6-9'
            return '10+'
        task_distribution_histogram: Dict[str, int] = {}
        for w in workers:
            total = x_tasks_count(w.get('id', '')) + y_tasks_count(w.get('id', ''))
            b = bucket(total)
            task_distribution_histogram[b] = task_distribution_histogram.get(b, 0) + 1
        
        # Y task analysis
        y_worker_distribution = []
        for w in workers:
            wid = w.get('id', '')
            ycnt = y_tasks_count(wid)
            if ycnt > 0:
                closing_dates = w.get('closing_history', []) or []
                y_worker_distribution.append({
                    'worker_name': w.get('name', ''),
                    'worker_id': wid,
                    'y_tasks': ycnt,
                    'score': w.get('score', 0),
                    'seniority': str(w.get('seniority')) if w.get('seniority') is not None else 'Unknown',
                    'closing_interval': w.get('closing_interval', 0),
                    'qualifications': w.get('qualifications', []) or [],
                    'closing_count': len(closing_dates),
                    'closing_dates': closing_dates,
                })
        y_counts = [r['y_tasks'] for r in y_worker_distribution]
        if y_counts:
            s_sorted = sorted(y_counts)
            n = len(s_sorted)
            median = s_sorted[n//2] if n % 2 == 1 else (s_sorted[n//2 - 1] + s_sorted[n//2]) / 2
            avg = sum(s_sorted) / n
            from math import sqrt
            std = sqrt(sum((c - avg) ** 2 for c in s_sorted) / n)
            y_statistics = {
                'total_workers_with_y_tasks': n,
                'average_y_tasks_per_worker': round(avg, 2),
                'median_y_tasks': round(median, 2) if isinstance(median, float) else median,
                'min_y_tasks': min(s_sorted),
                'max_y_tasks': max(s_sorted),
                'standard_deviation': round(std, 2),
            }
        else:
            y_statistics = {
                'total_workers_with_y_tasks': 0,
                'average_y_tasks_per_worker': 0,
                'median_y_tasks': 0,
                'min_y_tasks': 0,
                'max_y_tasks': 0,
                'standard_deviation': 0,
            }
        
        # Per-worker aggregates used for multiple sections
        per_worker = []
        for w in workers:
            xid = w.get('id', '')
            name = w.get('name', '')
            x_cnt = x_tasks_count(xid)
            y_cnt = y_tasks_count(xid)
            per_worker.append({'id': xid, 'name': name, 'x_tasks': x_cnt, 'y_tasks': y_cnt, 'total': x_cnt + y_cnt})
        total_x = sum(p['x_tasks'] for p in per_worker)
        total_y = sum(p['y_tasks'] for p in per_worker)
        total_all = total_x + total_y

        # Compute workload deviation baseline (average of workers with any tasks)
        totals_list = [p['total'] for p in per_worker if p['total'] > 0]
        avg_total_tasks = (sum(totals_list) / len(totals_list)) if totals_list else 0
        
        # Qualification analysis (array form for frontend charts)
        qualification_analysis_arr: Dict[str, Dict[str, float]] = {}
        for w in workers:
            for q in (w.get('qualifications') or []):
                d = qualification_analysis_arr.setdefault(q, {'qualified_workers': 0, 'total_tasks': 0, 'avg_tasks_per_worker': 0.0})
                d['qualified_workers'] += 1
                d['total_tasks'] += x_tasks_count(w.get('id', '')) + y_tasks_count(w.get('id', ''))
        for q, d in qualification_analysis_arr.items():
            qw = d['qualified_workers'] or 1
            d['avg_tasks_per_worker'] = round(d['total_tasks'] / qw, 2)
        qualification_analysis = [
            {
                'qualification': q,
                'qualified_workers': d['qualified_workers'],
                'total_tasks': d['total_tasks'],
                'avg_tasks_per_worker': d['avg_tasks_per_worker'],
                'utilization_rate': round((d['total_tasks'] / total_all * 100) if total_all else 0, 2),
            }
            for q, d in qualification_analysis_arr.items()
        ]
        
        # Generate workload distribution
        workload_distribution = []
        for w in workers:
            wid = w.get('id', '')
            name = w.get('name', '')
            total = x_tasks_count(wid) + y_tasks_count(wid)
            x_cnt = x_tasks_count(wid)
            y_cnt = y_tasks_count(wid)
            x_percentage = (x_cnt / total * 100) if total > 0 else 0
            y_percentage = (y_cnt / total * 100) if total > 0 else 0
            workload_distribution.append({
                'name': name,
                'total_tasks': total,
                'x_tasks': x_cnt,
                'y_tasks': y_cnt,
                'x_percentage': round(x_percentage, 1),
                'y_percentage': round(y_percentage, 1),
                'balance_score': abs(x_percentage - y_percentage),
            })
        
        # Generate closing accuracy data from closing_intervals when available
        closing_accuracy_data = []
        if closing_intervals_dict:
            for wid, ci in closing_intervals_dict.items():
                closing_accuracy_data.append({
                    'name': ci.get('worker_name', ''),
                    'target_interval': ci.get('target_interval', 0),
                    'actual_interval': ci.get('actual_avg_interval', 0),
                    'accuracy_percentage': ci.get('accuracy_percentage', 0),
                    'total_closings': ci.get('total_closings', 0),
                    'color': 'green' if ci.get('accuracy_percentage', 0) >= 80 else 'orange' if ci.get('accuracy_percentage', 0) >= 60 else 'red'
                })
        else:
            for w in workers:
                actual_closes = len(w.get('closing_history', []) or [])
                closing_accuracy_data.append({
                    'name': w.get('name', ''),
                    'target_interval': w.get('closing_interval', 0),
                    'actual_interval': 0,
                    'accuracy_percentage': 0,
                    'total_closings': actual_closes,
                    'color': 'red' if actual_closes == 0 else 'orange'
                })
        
        # Closing interval summary stats (ensure required keys with defaults)
        cis = aggregates_dict.get('closing_interval_summary', {}) or {}
        closing_stats_out = {
            'total_closing_workers': cis.get('workers_with_closings', 0),
            'average_accuracy': cis.get('average_accuracy', 0),
            'workers_above_90_percent': cis.get('workers_above_90_percent', 0),
            'workers_above_80_percent': cis.get('workers_above_80_percent', 0),
            'workers_below_50_percent': cis.get('workers_below_50_percent', 0),
            'algorithm_accuracy_percentage': cis.get('average_accuracy', 0),
        }

        fairness_metrics = {
            'seniority_distribution': seniority_distribution,
            'score_vs_tasks': score_vs_tasks,
            'qualification_utilization': qualification_utilization,
            'task_distribution_histogram': task_distribution_histogram,
            'y_task_analysis': {
                'worker_distribution': y_worker_distribution,
                'statistics': y_statistics,
            },
            'closing_interval_analysis': {
                'worker_distribution': [
                    {
                        'worker_name': ci.get('worker_name', ''),
                        'worker_id': wid,
                        'closing_interval': ci.get('target_interval', 0),
                        'total_closings': ci.get('total_closings', 0),
                        'total_weeks_served': round(sum(ci.get('intervals', []) or []), 1),
                        'actual_interval': ci.get('actual_avg_interval', 0),
                        'interval_accuracy': ci.get('accuracy_percentage', 0),
                        'last_closing_week': (ci.get('closing_dates') or [])[-1] if (ci.get('closing_dates') or []) else None,
                        'score': next((w.get('score', 0) for w in workers if w.get('id') == wid), 0)
                    }
                    for wid, ci in closing_intervals_dict.items()
                ],
                'statistics': closing_stats_out,
            },
            'worker_performance_metrics': [
                {
                    'worker_name': p['name'],
                    'worker_id': p['id'],
                    'total_tasks': p['total'],
                    'x_tasks': p['x_tasks'],
                    'y_tasks': p['y_tasks'],
                    'x_percentage': round((p['x_tasks'] / p['total'] * 100) if p['total'] else 0, 1),
                    'y_percentage': round((p['y_tasks'] / p['total'] * 100) if p['total'] else 0, 1),
                    'workload_deviation': round(((p['total'] - avg_total_tasks) / avg_total_tasks * 100) if avg_total_tasks else 0, 1),
                    'score': next((w.get('score', 0) for w in workers if w.get('id') == p['id']), 0),
                    'seniority': str(next((w.get('seniority') for w in workers if w.get('id') == p['id']), 'Unknown')),
                    'closing_interval': next((w.get('closing_interval', 0) for w in workers if w.get('id') == p['id']), 0),
                    'qualifications': next((w.get('qualifications', []) for w in workers if w.get('id') == p['id']), []),
                }
                for p in per_worker
            ],
        }
        
        # Compute summary totals if missing
        if summary.get('total_x_tasks', 0) == 0 and x_total_all:
            summary['total_x_tasks'] = x_total_all
        if summary.get('total_y_tasks', 0) == 0 and y_total_all:
            summary['total_y_tasks'] = y_total_all

        return {
            'data_sources': {
                'x_task_files': list(x_tasks_dict.keys()),
                'y_task_files': list(y_tasks_dict.keys()),
                'worker_data': {
                    'updated_at': stats.get('metadata', {}).get('last_updated'),
                    'worker_count': summary.get('total_workers', len(workers_dict)),
                }
            },
            'statistics': {
                'workers': workers_dict,
                'x_tasks': x_tasks_dict,
                'y_tasks': y_tasks_dict,
                'closing_intervals': closing_intervals_dict,
                'aggregates': aggregates_dict
            },
            'x_tasks_pie': x_tasks_pie,
            'y_tasks_pie': y_tasks_pie,
            'combined_pie': combined_pie,
            'x_tasks_timeline': x_tasks_timeline,
            'fairness_metrics': fairness_metrics,
            'summary': {
                'total_workers': summary.get('total_workers', len(workers_dict)),
                'total_x_tasks': summary.get('total_x_tasks', 0),
                'total_y_tasks': summary.get('total_y_tasks', 0),
                'total_combined': summary.get('total_x_tasks', 0) + summary.get('total_y_tasks', 0),
                'x_task_files': len(x_tasks_dict),
                'y_task_files': len(y_tasks_dict)
            },
            # Color-coded Y task bar chart entries
            'y_task_bar_chart': (lambda yd: (
                [] if not yd else (lambda avg: [
                    {
                        'name': rec['worker_name'],
                        'y_tasks': rec['y_tasks'],
                        'color': (
                            'red' if avg > 0 and rec['y_tasks'] > avg * 1.05 else
                            'blue' if avg > 0 and rec['y_tasks'] < avg * 0.95 else
                            'green'
                        ),
                        'deviation': round(rec['y_tasks'] - avg, 1),
                        'percentage': round((rec['y_tasks'] / total_y * 100) if total_y else 0, 1)
                    } for rec in yd
                ])(sum(r['y_tasks'] for r in yd) / len(yd))
            ))(y_worker_distribution),
            'score_vs_y_tasks': [
                {
                    'name': w.get('name', ''),
                    'score': w.get('score', 0),
                    'y_tasks': y_tasks_count(w.get('id', '')),
                    'ratio': 0,
                }
                for w in workers
            ],
            'closing_accuracy': closing_accuracy_data,
            'qualification_analysis': qualification_analysis,
            'workload_distribution': workload_distribution,
            'average_y_tasks': round(
                (sum(w['y_tasks'] for w in y_worker_distribution) / len(y_worker_distribution)), 2
            ) if y_worker_distribution else 0,
            'metadata': stats.get('metadata', {})
        }
    
    def refresh_all_statistics(self):
        """Rebuild statistics from data directory sources when empty or corrupted."""
        with self.lock:
            stats = self._load_stats()
            # Load workers
            workers_path = os.path.join(self.data_dir, 'worker_data.json')
            if os.path.exists(workers_path):
                try:
                    with open(workers_path, 'r', encoding='utf-8') as f:
                        workers_data = json.load(f)
                    # Ensure list
                    if isinstance(workers_data, dict) and workers_data.get('workers'):
                        workers_data = list(workers_data['workers'].values())
                    if isinstance(workers_data, list):
                        self.update_worker_data(workers_data)
                        stats = self._load_stats()
                except Exception:
                    pass
            # Load X task files
            try:
                for x_file in sorted(fn for fn in os.listdir(self.data_dir) if fn.startswith('x_tasks_') and fn.endswith('.csv')):
                    file_path = os.path.join(self.data_dir, x_file)
                    counts: Dict[str, Dict[str, int]] = {}
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            reader = list(csv.reader(f))
                        if len(reader) >= 3:
                            data_rows = reader[2:]
                            for row in data_rows:
                                if len(row) < 2:
                                    continue
                                wid = (row[0] or '').strip()
                                if not wid:
                                    continue
                                for cell in row[2:]:
                                    task = (cell or '').strip()
                                    if not task or task == '-':
                                        continue
                                    counts.setdefault(wid, {})
                                    counts[wid][task] = counts[wid].get(task, 0) + 1
                        if counts:
                            self.update_x_tasks(x_file, counts)
                            stats = self._load_stats()
                    except Exception:
                        continue
            except Exception:
                pass
            # Load Y task files
            try:
                for y_file in sorted(fn for fn in os.listdir(self.data_dir) if fn.startswith('y_tasks_') and fn.endswith('.csv')):
                    file_path = os.path.join(self.data_dir, y_file)
                    counts: Dict[str, Dict[str, int]] = {}
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            reader = list(csv.reader(f))
                        if len(reader) >= 2:
                            # header with dates, then rows per task
                            dates = reader[0][1:]
                            for row in reader[1:]:
                                if not row:
                                    continue
                                task_name = (row[0] or '').strip()
                                if not task_name:
                                    continue
                                for idx, cell in enumerate(row[1:]):
                                    wid = (cell or '').strip()
                                    if not wid or wid == '-':
                                        continue
                                    counts.setdefault(wid, {})
                                    counts[wid][task_name] = counts[wid].get(task_name, 0) + 1
                        if counts:
                            self.update_y_tasks(y_file, counts)
                            stats = self._load_stats()
                    except Exception:
                        continue
            except Exception:
                pass

    def reset_statistics(self) -> Dict[str, Any]:
        """Reset statistics to a clean initial state."""
        stats = self._initial_stats()
        self._save_stats(stats)
        return stats

    def get_worker_task_counts(self) -> Dict[str, Dict[str, int]]:
        """Get worker task counts for the frontend"""
        stats = self.get_comprehensive_statistics()
        workers = stats["statistics"]["workers"]
        
        return {
            worker_id: {
                "x_tasks": worker.get("total_x_tasks", 0),
                "y_tasks": worker.get("total_y_tasks", 0),
                "total": worker.get("total_x_tasks", 0) + worker.get("total_y_tasks", 0)
            }
            for worker_id, worker in workers.items()
        }
    
    def get_closing_accuracy_data(self) -> List[Dict[str, Any]]:
        """Get formatted closing accuracy data for the frontend"""
        stats = self.get_comprehensive_statistics()
        closing_intervals = stats["statistics"]["closing_intervals"]
        
        return [
            {
                "name": data["worker_name"],
                "target_interval": data["target_interval"],
                "actual_interval": data["actual_avg_interval"],
                "accuracy_percentage": data["accuracy_percentage"],
                "total_closings": data["total_closings"],
                "color": data["color"]
            }
            for data in closing_intervals.values()
        ]

    # --- Validation Utilities ---
    def validate(self) -> Dict[str, Any]:
        """Validate that derived statistics match underlying sources.

        Checks:
        - X/Y totals vs. per-file sums
        - Worker totals vs. per-file sums
        - Closing interval calculations vs. recomputation from closing_history
        Returns a dict { valid: bool, issues: [...], summary: {...} }
        """
        issues: List[str] = []
        stats = self._load_stats()
        stats_section = stats.get('statistics', {}) or {}
        workers = stats_section.get('workers', {}) or {}
        x_tasks_dict = stats_section.get('x_tasks', {}) or {}
        y_tasks_dict = stats_section.get('y_tasks', {}) or {}
        closing_intervals = stats_section.get('closing_intervals', {}) or {}
        summary = stats.get('summary', {}) or {}

        # Helper to sum counts from per-file maps
        def sum_file_counts(task_dict: Dict[str, Any]) -> int:
            total = 0
            for period in task_dict.values():
                data = period.get('data', {}) or {}
                for wid, counts in data.items():
                    total += sum((counts or {}).values())
            return total

        expected_x_total = sum_file_counts(x_tasks_dict)
        expected_y_total = sum_file_counts(y_tasks_dict)

        worker_x_total = sum(w.get('total_x_tasks', 0) for w in workers.values())
        worker_y_total = sum(w.get('total_y_tasks', 0) for w in workers.values())

        if worker_x_total and expected_x_total and worker_x_total != expected_x_total:
            issues.append(f"X total mismatch: workers={worker_x_total} files={expected_x_total}")
        if worker_y_total and expected_y_total and worker_y_total != expected_y_total:
            issues.append(f"Y total mismatch: workers={worker_y_total} files={expected_y_total}")

        # Summary consistency
        if summary.get('total_x_tasks', 0) and expected_x_total and summary.get('total_x_tasks') != expected_x_total:
            issues.append(f"summary.total_x_tasks={summary.get('total_x_tasks')} != files={expected_x_total}")
        if summary.get('total_y_tasks', 0) and expected_y_total and summary.get('total_y_tasks') != expected_y_total:
            issues.append(f"summary.total_y_tasks={summary.get('total_y_tasks')} != files={expected_y_total}")

        # Recompute closing intervals from workers.closing_history
        def recompute_ci(wdata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            try:
                ch = wdata.get('closing_history') or []
                if len(ch) < 2:
                    return None
                dates: List[date] = []
                for s in ch:
                    if isinstance(s, str):
                        try:
                            dates.append(datetime.strptime(s, '%Y-%m-%d').date())
                        except Exception:
                            dates.append(datetime.fromisoformat(s).date())
                    else:
                        dates.append(s)
                dates.sort()
                intervals = [(dates[i] - dates[i-1]).days/7.0 for i in range(1, len(dates))]
                if not intervals:
                    return None
                actual_avg = sum(intervals)/len(intervals)
                target = wdata.get('closing_interval', 0) or 0
                if target <= 0:
                    return None
                acc = max(0, 100 - (abs(actual_avg - target)/target)*100)
                return {
                    'actual_avg_interval': round(actual_avg, 2),
                    'accuracy_percentage': round(acc, 1),
                    'total_closings': len(dates)
                }
            except Exception:
                return None

        for wid, w in workers.items():
            recomputed = recompute_ci(w)
            if not recomputed:
                continue
            ci = closing_intervals.get(wid) or {}
            if round(ci.get('actual_avg_interval', 0), 2) != recomputed['actual_avg_interval']:
                issues.append(f"closing.actual_avg_interval mismatch for {wid}")
            if round(ci.get('accuracy_percentage', 0), 1) != recomputed['accuracy_percentage']:
                issues.append(f"closing.accuracy_percentage mismatch for {wid}")
            if ci.get('total_closings', 0) != recomputed['total_closings']:
                issues.append(f"closing.total_closings mismatch for {wid}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'expected_totals': {
                'x': expected_x_total,
                'y': expected_y_total
            },
            'worker_totals': {
                'x': worker_x_total,
                'y': worker_y_total
            },
            'summary': summary
        }
