#!/usr/bin/env python3
"""
Y-Task Manager for Worker Scheduling System
Handles saving and loading Y tasks from CSV files with caching.
Prevents JSON file bloat during long-range tests.
"""

import os
import csv
import json
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class YTaskManager:
    """
    Manages Y-task assignments using CSV files.
    Prevents JSON file bloat and provides direct access to Y-task data.
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
    
    def save_y_tasks_to_csv(self, start_date: str, end_date: str, grid_data: List[List[str]], 
                           dates: List[str], y_tasks: List[str]) -> str:
        """
        Save Y tasks to CSV file.
        
        Args:
            start_date: Start date in dd/mm/yyyy format
            end_date: End date in dd/mm/yyyy format
            grid_data: 2D array of worker assignments
            dates: List of dates
            y_tasks: List of Y task types
            
        Returns:
            Filename of saved CSV
        """
        # Create filename
        safe_start = start_date.replace('/', '-')
        safe_end = end_date.replace('/', '-')
        filename = f"y_tasks_{safe_start}_to_{safe_end}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row with dates
            header = ['Y Task'] + dates
            writer.writerow(header)
            
            # Write data rows
            for i, y_task in enumerate(y_tasks):
                row = [y_task] + grid_data[i]
                writer.writerow(row)
        
        # Update index file
        self._update_y_task_index(start_date, end_date, filename)
        
        # NEW: Trigger closing schedule recalculation after Y tasks are saved
        try:
            from .closing_schedule_calculator import ClosingScheduleCalculator
            from .worker import load_workers_from_json, save_workers_to_json
            
            # Load workers
            worker_file_path = os.path.join(self.data_dir, 'worker_data.json')
            workers = load_workers_from_json(worker_file_path)
            
            # Parse start and end dates
            start_date_obj = datetime.strptime(start_date, '%d/%m/%Y').date()
            end_date_obj = datetime.strptime(end_date, '%d/%m/%Y').date()
            
            # Generate semester weeks (Fridays) for the date range
            semester_weeks = []
            current = start_date_obj
            while current <= end_date_obj:
                if current.weekday() == 4:  # Friday
                    semester_weeks.append(current)
                current += timedelta(days=1)
            
            # Trigger closing schedule recalculation
            from .scoring_config import load_config
            cfg = load_config()
            calculator = ClosingScheduleCalculator(
                allow_single_relief_min1=cfg.CLOSING_RELIEF_ENABLED,
                relief_max_per_semester=cfg.CLOSING_RELIEF_MAX_PER_SEMESTER,
            )
            calculator.update_all_worker_schedules(workers, semester_weeks)
            
            # Save updated worker data with new optimal closing dates
            save_workers_to_json(workers, worker_file_path)
            
            print(f"✅ Closing schedule recalculation completed after Y tasks save via manager")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to update closing schedules after Y tasks save via manager: {e}")
        
        print(f"✅ Y tasks saved to {filename}")
        return filename
    
    def load_y_tasks_from_csv(self, filename: str) -> Tuple[List[List[str]], List[str], List[str]]:
        """
        Load Y tasks from CSV file.
        
        Args:
            filename: CSV filename
            
        Returns:
            Tuple of (grid_data, dates, y_tasks)
        """
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Y task file not found: {filepath}")
        
        grid_data = []
        dates = []
        y_tasks = []
        
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Read header row
            header = next(reader)
            dates = header[1:]  # Skip 'Y Task' column
            
            # Read data rows
            for row in reader:
                if len(row) > 1:
                    y_tasks.append(row[0])
                    grid_data.append(row[1:])
        
        return grid_data, dates, y_tasks
    
    def get_y_task_assignments(self, start_date: str, end_date: str) -> Dict[str, Dict[str, str]]:
        """
        Get Y task assignments for a date range.
        
        Args:
            start_date: Start date in dd/mm/yyyy format
            end_date: End date in dd/mm/yyyy format
            
        Returns:
            Dictionary of worker_id -> date -> task assignments
        """
        # Load from CSV files
        assignments = {}
        
        # Find relevant CSV files
        csv_files = self._find_y_task_files_in_range(start_date, end_date)
        
        for filename in csv_files:
            try:
                grid_data, dates, y_tasks = self.load_y_tasks_from_csv(filename)
                
                # Convert grid data to assignments
                for i, y_task in enumerate(y_tasks):
                    for j, worker_name in enumerate(grid_data[i]):
                        if worker_name and worker_name.strip() and worker_name.strip() != '-':
                            date_str = dates[j]
                            # Find worker ID by name
                            worker_id = self._get_worker_id_by_name(worker_name.strip())
                            if worker_id:
                                if worker_id not in assignments:
                                    assignments[worker_id] = {}
                                assignments[worker_id][date_str] = y_task
            except Exception as e:
                print(f"Error loading Y tasks from {filename}: {e}")
        
        return assignments
    
    def _find_y_task_files_in_range(self, start_date: str, end_date: str) -> List[str]:
        """Find Y task CSV files that overlap with the date range"""
        relevant_files = []
        
        # Parse dates
        start_dt = datetime.strptime(start_date, '%d/%m/%Y').date()
        end_dt = datetime.strptime(end_date, '%d/%m/%Y').date()
        
        # Check all Y task files
        for filename in os.listdir(self.data_dir):
            if filename.startswith('y_tasks_') and filename.endswith('.csv'):
                # Extract date range from filename
                try:
                    date_range = filename.replace('y_tasks_', '').replace('.csv', '')
                    file_start, file_end = date_range.split('_to_')
                    
                    file_start_dt = datetime.strptime(file_start.replace('-', '/'), '%d/%m/%Y').date()
                    file_end_dt = datetime.strptime(file_end.replace('-', '/'), '%d/%m/%Y').date()
                    
                    # Check if ranges overlap
                    if (file_start_dt <= end_dt and file_end_dt >= start_dt):
                        relevant_files.append(filename)
                except Exception as e:
                    print(f"Error parsing filename {filename}: {e}")
        
        return relevant_files
    
    def _get_worker_id_by_name(self, worker_name: str) -> Optional[str]:
        """Get worker ID by name from name_conv.json mapping"""
        try:
            # Load name conversion mapping (Hebrew name -> ID)
            name_conv_path = os.path.join(self.data_dir, 'name_conv.json')
            if os.path.exists(name_conv_path):
                with open(name_conv_path, 'r', encoding='utf-8') as f:
                    name_conv_list = json.load(f)
                
                # Create reverse mapping: Hebrew name -> ID
                hebrew_to_id = {}
                for entry in name_conv_list:
                    for worker_id, hebrew_name in entry.items():
                        hebrew_to_id[hebrew_name] = worker_id
                
                # Return the ID for the Hebrew name
                return hebrew_to_id.get(worker_name.strip())
            else:
                print(f"Warning: name_conv.json not found at {name_conv_path}")
        except Exception as e:
            print(f"Error getting worker ID for {worker_name}: {e}")
        
        return None
    
    def _update_y_task_index(self, start_date: str, end_date: str, filename: str):
        """Update the Y task index file"""
        index_path = os.path.join(self.data_dir, 'y_tasks_index.json')
        
        # Load existing index
        index = {}
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            except Exception as e:
                print(f"Error loading Y task index: {e}")
        
        # Add new entry
        period_key = f"{start_date}_to_{end_date}"
        index[period_key] = {
            'filename': filename,
            'start_date': start_date,
            'end_date': end_date,
            'created_at': datetime.now().isoformat()
        }
        
        # Save updated index
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving Y task index: {e}")
    
    def list_y_task_periods(self) -> List[Dict]:
        """List all available Y task periods"""
        index_path = os.path.join(self.data_dir, 'y_tasks_index.json')
        
        if not os.path.exists(index_path):
            return []
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            periods = []
            for period_key, data in index.items():
                if isinstance(data, dict):
                    periods.append({
                        'period': period_key,
                        'filename': data.get('filename', ''),
                        'start_date': data.get('start_date', period_key.split('_to_')[0].replace('-', '/')),
                        'end_date': data.get('end_date', period_key.split('_to_')[1].replace('-', '/')),
                        'created_at': data.get('created_at', '')
                    })
                else:
                    # Legacy value was just the filename string
                    try:
                        s, e = period_key.split('_to_')
                        s = s.replace('-', '/')
                        e = e.replace('-', '/')
                        periods.append({
                            'period': period_key,
                            'filename': str(data),
                            'start_date': s,
                            'end_date': e,
                            'created_at': ''
                        })
                    except Exception:
                        continue
            # Sort by start date ascending
            def parse(d):
                try:
                    return datetime.strptime(d, '%d/%m/%Y')
                except Exception:
                    return datetime.min
            periods.sort(key=lambda p: parse(p['start_date']))
            return periods
        except Exception as e:
            print(f"Error loading Y task periods: {e}")
            return []
    
    def delete_y_task_period(self, start_date: str, end_date: str) -> bool:
        """Delete Y task period and its CSV file"""
        period_key = f"{start_date}_to_{end_date}"
        index_path = os.path.join(self.data_dir, 'y_tasks_index.json')
        
        try:
            # Load index
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)

            if period_key in index:
                entry = index[period_key]
                filename = entry['filename'] if isinstance(entry, dict) else str(entry)
                filepath = os.path.join(self.data_dir, filename)
                
                # Delete CSV file
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"✅ Deleted Y task file: {filename}")
                
                # Remove from index
                del index[period_key]
                
                # Save updated index
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump(index, f, indent=2, ensure_ascii=False)
                
                # NEW: Trigger closing schedule recalculation after deleting Y task period
                try:
                    from .closing_schedule_calculator import ClosingScheduleCalculator
                    from .worker import load_workers_from_json, save_workers_to_json
                    
                    # Load workers
                    worker_file_path = os.path.join(self.data_dir, 'worker_data.json')
                    workers = load_workers_from_json(worker_file_path)
                    
                    # Parse start and end dates
                    start_date_obj = datetime.strptime(start_date, '%d/%m/%Y').date()
                    end_date_obj = datetime.strptime(end_date, '%d/%m/%Y').date()
                    
                    # Generate semester weeks (Fridays) for the date range
                    semester_weeks = []
                    current = start_date_obj
                    while current <= end_date_obj:
                        if current.weekday() == 4:  # Friday
                            semester_weeks.append(current)
                        current += timedelta(days=1)
                    
                    # Trigger closing schedule recalculation
                    from .scoring_config import load_config
                    cfg = load_config()
                    calculator = ClosingScheduleCalculator(
                        allow_single_relief_min1=cfg.CLOSING_RELIEF_ENABLED,
                        relief_max_per_semester=cfg.CLOSING_RELIEF_MAX_PER_SEMESTER,
                    )
                    calculator.update_all_worker_schedules(workers, semester_weeks)
                    
                    # Save updated worker data with new optimal closing dates
                    save_workers_to_json(workers, worker_file_path)
                    
                    print(f"✅ Closing schedule recalculation completed after deleting Y task period via manager")
                    
                except Exception as e:
                    print(f"⚠️  Warning: Failed to update closing schedules after deleting Y task period: {e}")
                
                return True
            else:
                print(f"❌ Y task period not found: {period_key}")
                return False
                
        except Exception as e:
            print(f"Error deleting Y task period: {e}")
            return False
    
    def clear_worker_y_tasks_from_json(self, worker_id: str):
        """Clear Y tasks from worker's JSON data to prevent bloat"""
        worker_data_path = os.path.join(self.data_dir, 'worker_data.json')
        
        if not os.path.exists(worker_data_path):
            return
        
        try:
            with open(worker_data_path, 'r', encoding='utf-8') as f:
                workers = json.load(f)
            
            # Find and clear Y tasks for the worker
            for worker in workers:
                if worker.get('id') == worker_id:
                    worker['y_tasks'] = {}
                    break
            
            # Save updated worker data
            with open(worker_data_path, 'w', encoding='utf-8') as f:
                json.dump(workers, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Cleared Y tasks from worker {worker_id} in JSON")
            
        except Exception as e:
            print(f"Error clearing worker Y tasks: {e}")


# Global Y task manager instance
y_task_manager = None

def get_y_task_manager(data_dir: str) -> YTaskManager:
    """Get or create global Y task manager instance"""
    global y_task_manager
    if y_task_manager is None:
        y_task_manager = YTaskManager(data_dir)
    return y_task_manager 