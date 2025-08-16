#!/usr/bin/env python3
"""
Comprehensive Closing Schedule Calculator Test Script
Tests the closing schedule calculator with real worker data for extended periods.
"""

import sys
import os
from datetime import date, timedelta
from typing import List, Dict, Tuple
import statistics

# Add backend to path for imports
sys.path.append('backend')

from worker import load_workers_from_json, EnhancedWorker
from closing_schedule_calculator import ClosingScheduleCalculator

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
        
        if intervals:
            std_dev = statistics.stdev(intervals)
        else:
            std_dev = 0.0
    else:
        std_dev = 0.0
    
    # Calculate accuracy (how well the schedule follows the intended interval)
    if worker.closing_interval and optimal_weeks:
        total_deviation = 0
        for i in range(1, len(optimal_weeks)):
            actual_interval = optimal_weeks[i] - optimal_weeks[i-1]
            deviation = abs(actual_interval - worker.closing_interval)
            total_deviation += deviation
        
        avg_deviation = total_deviation / (len(optimal_weeks) - 1) if len(optimal_weeks) > 1 else 0
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

def test_closing_schedule_extended():
    """Test closing schedule calculator with real worker data for extended periods."""
    
    print("🔍 CLOSING SCHEDULE CALCULATOR COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Load real worker data
    try:
        workers = load_workers_from_json('data/worker_data.json')
        print(f"✅ Loaded {len(workers)} workers from worker_data.json")
    except Exception as e:
        print(f"❌ Failed to load worker data: {e}")
        return
    
    # Initialize calculator
    calculator = ClosingScheduleCalculator()
    calculator.debug = False  # Reduce console output
    
    # Test periods
    test_periods = [
        (2025, 1, 26),  # First half 2025 (26 weeks)
        (2025, 2, 26),  # Second half 2025 (26 weeks)
        (2026, 1, 26),  # First half 2026 (26 weeks)
        (2026, 2, 26),  # Second half 2026 (26 weeks)
        (2025, 1, 52),  # Full year 2025 (52 weeks)
        (2026, 1, 52),  # Full year 2026 (52 weeks)
    ]
    
    for year, half, weeks in test_periods:
        print(f"\n📅 TESTING PERIOD: {year} Semester {half} ({weeks} weeks)")
        print("-" * 60)
        
        # Generate semester weeks
        semester_weeks = generate_semester_weeks(year, half, weeks)
        start_date = semester_weeks[0]
        end_date = semester_weeks[-1]
        print(f"Period: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
        
        # Test each worker
        for worker in workers:
            if worker.closing_interval and worker.closing_interval > 0:
                print(f"\n👤 Worker: {worker.name}")
                print(f"   ID: {worker.id}")
                print(f"   Closing Interval: {worker.closing_interval}")
                
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

def test_specific_worker_scenarios():
    """Test specific worker scenarios with detailed analysis."""
    
    print("\n🎯 SPECIFIC WORKER SCENARIO TESTS")
    print("=" * 80)
    
    try:
        workers = load_workers_from_json('data/worker_data.json')
    except Exception as e:
        print(f"❌ Failed to load worker data: {e}")
        return
    
    calculator = ClosingScheduleCalculator()
    calculator.debug = False
    
    # Test specific scenarios
    test_scenarios = [
        (2025, 1, 26, "Short semester test"),
        (2025, 1, 52, "Full year test"),
        (2026, 2, 26, "Future semester test"),
    ]
    
    for year, half, weeks, description in test_scenarios:
        print(f"\n🔬 {description}")
        print(f"Period: {year} Semester {half} ({weeks} weeks)")
        print("-" * 60)
        
        semester_weeks = generate_semester_weeks(year, half, weeks)
        
        # Test workers with different closing intervals
        interval_groups = {}
        for worker in workers:
            if worker.closing_interval and worker.closing_interval > 0:
                if worker.closing_interval not in interval_groups:
                    interval_groups[worker.closing_interval] = []
                interval_groups[worker.closing_interval].append(worker)
        
        for interval, workers_in_group in interval_groups.items():
            print(f"\n📊 Workers with {interval}-week interval ({len(workers_in_group)} workers):")
            
            for worker in workers_in_group:
                analysis = analyze_closing_schedule(worker, semester_weeks, calculator)
                
                print(f"  {worker.name}:")
                print(f"    Required: {analysis['required_weeks']}")
                print(f"    Optimal: {analysis['optimal_weeks']}")
                print(f"    Combined: {analysis['combined_weeks']}")
                print(f"    Accuracy: {analysis['accuracy']:.1f}%")
                print(f"    Owed: {analysis['weekends_home_owed']}")

if __name__ == "__main__":
    print("🚀 Starting Closing Schedule Calculator Tests...")
    
    # Run comprehensive tests
    test_closing_schedule_extended()
    
    # Run specific scenario tests
    test_specific_worker_scenarios()
    
    print("\n✅ All tests completed!")
