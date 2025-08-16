#!/usr/bin/env python3
"""
Corrected Closing Schedule Calculator Test Script with X Tasks
Properly maps X task date ranges to semester dates for accurate testing.
"""

import sys
import os
import csv
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple
import statistics

# Add backend to path for imports
sys.path.append('backend')

from worker import load_workers_from_json, EnhancedWorker
from closing_schedule_calculator import ClosingScheduleCalculator

def parse_date_range(date_range: str) -> Tuple[date, date]:
    """Parse a date range like '05/01 - 11/01' and return start and end dates for 2025."""
    try:
        # Split the range
        start_part, end_part = date_range.split(' - ')
        
        # Parse start date (assuming 2025)
        start_day, start_month = map(int, start_part.split('/'))
        start_date = date(2025, start_month, start_day)
        
        # Parse end date (assuming 2025)
        end_day, end_month = map(int, end_part.split('/'))
        end_date = date(2025, end_month, end_day)
        
        return start_date, end_date
    except Exception as e:
        print(f"Error parsing date range '{date_range}': {e}")
        return None, None

def load_x_tasks_from_csv(csv_path: str) -> Dict[str, Dict[str, str]]:
    """Load X tasks from CSV file and return mapping of worker_id -> {date_string -> task_name}."""
    x_tasks = {}
    
    if not os.path.exists(csv_path):
        print(f"Warning: X tasks CSV file not found: {csv_path}")
        return x_tasks
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) < 3:
                print(f"Warning: X tasks CSV file has insufficient rows: {csv_path}")
                return x_tasks
            
            # First row: headers (id, name, week1, week2, ...)
            # Second row: date ranges
            # Third row onwards: worker data
            
            headers = rows[0]
            date_ranges = rows[1]
            
            # Process each worker row
            for row in rows[2:]:
                if len(row) < 2:
                    continue
                
                worker_id = row[0].strip()
                worker_name = row[1].strip()
                
                if not worker_id or worker_id == '':
                    continue
                
                # Initialize worker's X tasks
                x_tasks[worker_id] = {}
                
                # Process each week column (starting from column 2)
                for i in range(2, len(row)):
                    if i < len(headers) and i < len(date_ranges):
                        week_num = headers[i]
                        date_range = date_ranges[i]
                        task = row[i].strip()
                        
                        if task and task != '':
                            # Store the task with the date range as key
                            x_tasks[worker_id][date_range] = task
                            print(f"  Loaded X task for {worker_name} ({worker_id}): {task} in {date_range}")
        
        print(f"✅ Loaded X tasks for {len(x_tasks)} workers from {csv_path}")
        return x_tasks
        
    except Exception as e:
        print(f"Error loading X tasks from {csv_path}: {e}")
        return {}

def populate_workers_with_x_tasks(workers: List[EnhancedWorker], x_tasks: Dict[str, Dict[str, str]], semester_weeks: List[date]):
    """Populate worker objects with X tasks mapped to specific semester dates."""
    for worker in workers:
        if worker.id in x_tasks:
            # Convert date ranges to specific dates that match semester weeks
            worker.x_tasks = {}
            
            for date_range, task in x_tasks[worker.id].items():
                start_date, end_date = parse_date_range(date_range)
                if start_date and end_date:
                    # Find which semester week(s) this X task falls into
                    for week_idx, week_date in enumerate(semester_weeks):
                        # Check if the week_date falls within the X task date range
                        if start_date <= week_date <= end_date:
                            # Convert to the format expected by the calculator (dd/mm/yyyy)
                            date_str = week_date.strftime('%d/%m/%Y')
                            worker.x_tasks[date_str] = task
                            print(f"  Mapped {worker.name}: {task} in {date_range} → {date_str} (week {week_idx + 1})")
            
            print(f"  Populated {worker.name} with {len(worker.x_tasks)} mapped X tasks")
        else:
            worker.x_tasks = {}
            print(f"  No X tasks found for {worker.name}")

def generate_semester_weeks(year: int, half: int, weeks: int = 26) -> List[date]:
    """Generate semester weeks starting from the first Sunday of the specified half-year."""
    if half == 1:
        # First half: January to June
        start_date = date(year, 1, 1)
        # Find first Sunday
        while start_date.weekday() != 6:  # 6 = Sunday
            start_date += timedelta(days=1)
    else:
        # Second half: July to December
        start_date = date(year, 7, 1)
        # Find first Sunday
        while start_date.weekday() != 6:  # 6 = Sunday
            start_date += timedelta(days=1)
    
    # Generate weeks (each week starts on Sunday)
    semester_weeks = []
    for i in range(weeks):
        week_start = start_date + timedelta(weeks=i)
        # Use Friday of each week for closing calculations
        friday = week_start + timedelta(days=5)
        semester_weeks.append(friday)
    
    return semester_weeks

def analyze_closing_schedule(worker: EnhancedWorker, semester_weeks: List[date], 
                           calculator: ClosingScheduleCalculator) -> Dict:
    """Analyze a worker's closing schedule and return detailed metrics."""
    
    # Calculate closing schedule
    result = calculator.calculate_worker_closing_schedule(worker, semester_weeks)
    
    # Extract required and optimal dates
    required_dates = result['required_dates']
    optimal_dates = result['optimal_dates']
    
    # Convert dates to week numbers (1-based)
    required_weeks = []
    optimal_weeks = []
    
    for close_date in required_dates:
        try:
            week_idx = semester_weeks.index(close_date)
            required_weeks.append(week_idx + 1)  # Convert to 1-based
        except ValueError:
            pass
    
    for close_date in optimal_dates:
        try:
            week_idx = semester_weeks.index(close_date)
            optimal_weeks.append(week_idx + 1)  # Convert to 1-based
        except ValueError:
            pass
    
    # Sort weeks
    required_weeks.sort()
    optimal_weeks.sort()
    
    # Calculate combined schedule
    all_closing_weeks = sorted(set(required_weeks + optimal_weeks))
    
    # Calculate standard deviation from closing interval
    if worker.closing_interval and optimal_weeks:
        intervals = []
        for i in range(1, len(optimal_weeks)):
            interval = optimal_weeks[i] - optimal_weeks[i-1]
            intervals.append(interval)
        
        if len(intervals) > 1:
            std_dev = statistics.stdev(intervals)
        else:
            std_dev = 0.0
    else:
        std_dev = 0.0
    
    # Calculate accuracy (how well the schedule follows the intended interval)
    if worker.closing_interval and len(optimal_weeks) > 1:
        total_deviation = 0
        for i in range(1, len(optimal_weeks)):
            actual_interval = optimal_weeks[i] - optimal_weeks[i-1]
            deviation = abs(actual_interval - worker.closing_interval)
            total_deviation += deviation
        
        avg_deviation = total_deviation / (len(optimal_weeks) - 1)
        accuracy = max(0, 100 - (avg_deviation / worker.closing_interval * 100))
    else:
        accuracy = 100.0
    
    return {
        'required_weeks': required_weeks,
        'optimal_weeks': optimal_weeks,
        'combined_weeks': all_closing_weeks,
        'std_deviation': std_dev,
        'accuracy': accuracy,
        'weekends_home_owed': result['final_weekends_home_owed']
    }

def test_closing_schedule_with_x_tasks():
    """Test closing schedule calculator with real worker data AND properly mapped X tasks."""
    
    print("🔍 CORRECTED CLOSING SCHEDULE CALCULATOR TEST WITH X TASKS")
    print("=" * 80)
    
    # Load real worker data
    try:
        workers = load_workers_from_json('data/worker_data.json')
        print(f"✅ Loaded {len(workers)} workers from worker_data.json")
    except Exception as e:
        print(f"❌ Failed to load worker data: {e}")
        return
    
    # Load X tasks data
    x_tasks = load_x_tasks_from_csv('data/x_tasks_2025_1.csv')
    
    # Initialize calculator
    calculator = ClosingScheduleCalculator()
    calculator.debug = False  # Reduce console output
    
    # Test periods - focus on 2025 Semester 1 since that's where the X tasks are
    test_periods = [
        (2025, 1, 26, "2025 Semester 1 (26 weeks) - WITH PROPERLY MAPPED X TASKS"),
    ]
    
    for year, half, weeks, description in test_periods:
        print(f"\n📅 TESTING PERIOD: {description}")
        print("-" * 60)
        
        # Generate semester weeks
        semester_weeks = generate_semester_weeks(year, half, weeks)
        start_date = semester_weeks[0]
        end_date = semester_weeks[-1]
        print(f"Period: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
        
        # Populate workers with X tasks mapped to semester dates
        populate_workers_with_x_tasks(workers, x_tasks, semester_weeks)
        
        # Test each worker
        for worker in workers:
            if worker.closing_interval and worker.closing_interval > 0:
                print(f"\n👤 Worker: {worker.name}")
                print(f"   ID: {worker.id}")
                print(f"   Closing Interval: {worker.closing_interval}")
                
                # Show X tasks for this worker
                if worker.x_tasks:
                    print(f"   X Tasks: {worker.x_tasks}")
                else:
                    print(f"   X Tasks: None")
                
                # Analyze closing schedule
                analysis = analyze_closing_schedule(worker, semester_weeks, calculator)
                
                # Format results in requested style
                print(f"   Required closing weeks: {analysis['required_weeks']}")
                print(f"   Optimal closing weeks: {analysis['optimal_weeks']}")
                print(f"   Combined: {analysis['combined_weeks']}")
                print(f"   Standard deviation from closing interval: {analysis['std_deviation']:.2f}")
                print(f"   Accuracy: {analysis['accuracy']:.1f}%")
                print(f"   Weekends home owed: {analysis['weekends_home_owed']}")
                
                # Additional insights
                if analysis['optimal_weeks']:
                    actual_intervals = []
                    for i in range(1, len(analysis['optimal_weeks'])):
                        interval = analysis['optimal_weeks'][i] - analysis['optimal_weeks'][i-1]
                        actual_intervals.append(interval)
                    
                    if actual_intervals:
                        avg_interval = sum(actual_intervals) / len(actual_intervals)
                        print(f"   Average actual interval: {avg_interval:.1f} weeks")
                        print(f"   Target interval: {worker.closing_interval} weeks")
                        print(f"   Interval variance: {abs(avg_interval - worker.closing_interval):.1f} weeks")
            else:
                print(f"\n👤 Worker: {worker.name} (No closing interval configured)")
        
        # Summary for this period
        print(f"\n📊 PERIOD SUMMARY:")
        workers_with_interval = [w for w in workers if w.closing_interval and w.closing_interval > 0]
        if workers_with_interval:
            total_weekends_owed = sum(analysis['weekends_home_owed'] for analysis in 
                                    [analyze_closing_schedule(w, semester_weeks, calculator) 
                                     for w in workers_with_interval])
            print(f"   Total weekends home owed across all workers: {total_weekends_owed}")
        
        print("\n" + "=" * 80)

def test_specific_x_task_scenarios():
    """Test specific scenarios where X tasks should affect closing schedules."""
    
    print("\n🎯 X TASK IMPACT ANALYSIS (CORRECTED)")
    print("=" * 80)
    
    try:
        workers = load_workers_from_json('data/worker_data.json')
        x_tasks = load_x_tasks_from_csv('data/x_tasks_2025_1.csv')
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return
    
    calculator = ClosingScheduleCalculator()
    calculator.debug = False
    
    # Test specific workers with X tasks
    workers_with_x_tasks = [w for w in workers if w.id in x_tasks]
    print(f"Found {len(workers_with_x_tasks)} workers with X tasks")
    
    for worker in workers_with_x_tasks:
        if not worker.closing_interval:
            continue
            
        print(f"\n🔬 Analyzing {worker.name} (ID: {worker.id})")
        print(f"   Closing Interval: {worker.closing_interval}")
        print(f"   Original X Tasks: {x_tasks[worker.id]}")
        
        # Test with 26-week period
        semester_weeks = generate_semester_weeks(2025, 1, 26)
        
        # Populate this worker with properly mapped X tasks
        populate_workers_with_x_tasks([worker], {worker.id: x_tasks[worker.id]}, semester_weeks)
        
        analysis = analyze_closing_schedule(worker, semester_weeks, calculator)
        
        print(f"   Mapped X Tasks: {worker.x_tasks}")
        print(f"   Required closing weeks: {analysis['required_weeks']}")
        print(f"   Optimal closing weeks: {analysis['optimal_weeks']}")
        print(f"   Combined: {analysis['combined_weeks']}")
        print(f"   Weekends home owed: {analysis['weekends_home_owed']}")
        
        # Check for conflicts between X tasks and optimal closing
        if analysis['required_weeks'] and analysis['optimal_weeks']:
            conflicts = set(analysis['required_weeks']) & set(analysis['optimal_weeks'])
            if conflicts:
                print(f"   ⚠️  CONFLICTS: X tasks and optimal closing overlap in weeks: {sorted(conflicts)}")
            else:
                print(f"   ✅ No conflicts between X tasks and optimal closing")

if __name__ == "__main__":
    print("🚀 Starting Corrected Closing Schedule Calculator Tests with X Tasks...")
    
    # Run comprehensive tests with properly mapped X tasks
    test_closing_schedule_with_x_tasks()
    
    # Run specific X task impact analysis
    test_specific_x_task_scenarios()
    
    print("\n✅ All tests completed!")
