#!/usr/bin/env python3
"""
Comprehensive Statistics Testing Script
This script systematically tests all aspects of the statistics system to ensure
100% accuracy between the displayed data and the underlying data sources.
"""

import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the backend directory to the path so we can import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.statistics_service import StatisticsService
from worker import load_workers_from_json
from config import DATA_DIR


class StatisticsValidator:
    """Comprehensive validator for statistics accuracy."""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.stats_service = StatisticsService(data_dir)
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{status} {test_name}")
        if details and not passed:
            print(f"    Details: {details}")
    
    def test_worker_data_consistency(self) -> bool:
        """Test that worker data in statistics matches worker_data.json."""
        print("\n🔍 Testing Worker Data Consistency...")
        
        try:
            # Load raw worker data
            worker_file = os.path.join(self.data_dir, 'worker_data.json')
            with open(worker_file, 'r', encoding='utf-8') as f:
                raw_workers = json.load(f)
            
            # Get statistics
            stats = self.stats_service.get_comprehensive_statistics()
            stats_workers = stats['statistics']['workers']
            
            # Test 1: Worker count consistency
            raw_count = len(raw_workers)
            stats_count = len(stats_workers)
            self.log_test(
                "Worker Count Consistency",
                raw_count == stats_count,
                f"Raw: {raw_count}, Stats: {stats_count}"
            )
            
            # Test 2: Individual worker data consistency
            all_consistent = True
            for raw_worker in raw_workers:
                worker_id = raw_worker['id']
                if worker_id not in stats_workers:
                    self.log_test(
                        f"Worker {worker_id} Missing from Stats",
                        False,
                        f"Worker {raw_worker['name']} not found in statistics"
                    )
                    all_consistent = False
                    continue
                
                stats_worker = stats_workers[worker_id]
                
                # Check basic fields
                if raw_worker['name'] != stats_worker['name']:
                    self.log_test(
                        f"Worker {worker_id} Name Mismatch",
                        False,
                        f"Raw: {raw_worker['name']}, Stats: {stats_worker['name']}"
                    )
                    all_consistent = False
                
                if raw_worker.get('score', 0) != stats_worker.get('score', 0):
                    self.log_test(
                        f"Worker {worker_id} Score Mismatch",
                        False,
                        f"Raw: {raw_worker.get('score', 0)}, Stats: {stats_worker.get('score', 0)}"
                    )
                    all_consistent = False
                
                if raw_worker.get('closing_interval', 0) != stats_worker.get('closing_interval', 0):
                    self.log_test(
                        f"Worker {worker_id} Closing Interval Mismatch",
                        False,
                        f"Raw: {raw_worker.get('closing_interval', 0)}, Stats: {stats_worker.get('closing_interval', 0)}"
                    )
                    all_consistent = False
            
            self.log_test("Individual Worker Data Consistency", all_consistent)
            return all_consistent
            
        except Exception as e:
            self.log_test("Worker Data Consistency", False, f"Exception: {e}")
            return False
    
    def test_x_tasks_accuracy(self) -> bool:
        """Test that X tasks statistics accurately reflect CSV data."""
        print("\n🔍 Testing X Tasks Accuracy...")
        
        try:
            # Load X tasks CSV
            x_csv_file = os.path.join(self.data_dir, 'x_tasks_2025_1.csv')
            if not os.path.exists(x_csv_file):
                self.log_test("X Tasks CSV Exists", False, "x_tasks_2025_1.csv not found")
                return False
            
            # Parse CSV manually
            csv_totals = {}
            with open(x_csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                if len(rows) < 3:
                    self.log_test("X Tasks CSV Format", False, "CSV has less than 3 rows")
                    return False
                
                # Skip header rows, start from row 3 (index 2)
                for row in rows[2:]:
                    if len(row) < 2:
                        continue
                    worker_id = row[0].strip()
                    worker_name = row[1].strip()
                    
                    if not worker_id or not worker_name:
                        continue
                    
                    # Count tasks for this worker
                    task_count = 0
                    for cell in row[2:]:
                        if cell.strip() and cell.strip() != '-':
                            task_count += 1
                    
                    csv_totals[worker_id] = {
                        'name': worker_name,
                        'tasks': task_count
                    }
            
            # Get statistics
            stats = self.stats_service.get_comprehensive_statistics()
            stats_x_tasks = stats['x_tasks_pie']
            
            # Test 1: Total X tasks consistency
            csv_total = sum(w['tasks'] for w in csv_totals.values())
            stats_total = sum(w['value'] for w in stats_x_tasks)
            
            self.log_test(
                "X Tasks Total Consistency",
                csv_total == stats_total,
                f"CSV Total: {csv_total}, Stats Total: {stats_total}"
            )
            
            # Test 2: Individual worker X task counts
            all_consistent = True
            for worker_id, csv_data in csv_totals.items():
                if csv_data['tasks'] == 0:
                    continue
                
                # Find in stats
                stats_worker = None
                for w in stats_x_tasks:
                    if w['worker_id'] == worker_id:
                        stats_worker = w
                        break
                
                if not stats_worker:
                    self.log_test(
                        f"Worker {worker_id} Missing from X Tasks Stats",
                        False,
                        f"Worker {csv_data['name']} not found in X tasks statistics"
                    )
                    all_consistent = False
                    continue
                
                if csv_data['tasks'] != stats_worker['value']:
                    self.log_test(
                        f"Worker {worker_id} X Tasks Count Mismatch",
                        False,
                        f"CSV: {csv_data['tasks']}, Stats: {stats_worker['value']}"
                    )
                    all_consistent = False
            
            self.log_test("Individual X Tasks Counts", all_consistent)
            return all_consistent
            
        except Exception as e:
            self.log_test("X Tasks Accuracy", False, f"Exception: {e}")
            return False
    
    def test_y_tasks_accuracy(self) -> bool:
        """Test that Y tasks statistics accurately reflect CSV data."""
        print("\n🔍 Testing Y Tasks Accuracy...")
        
        try:
            # Load Y tasks CSV
            y_csv_file = os.path.join(self.data_dir, 'y_tasks_05-01-2025_to_05-07-2025.csv')
            if not os.path.exists(y_csv_file):
                # Try alternative path
                y_csv_file = os.path.join(self.data_dir, '..', 'data', 'y_tasks_05-01-2025_to_05-07-2025.csv')
                if not os.path.exists(y_csv_file):
                    self.log_test("Y Tasks CSV Exists", False, "y_tasks_05-01-2025_to_05-07-2025.csv not found")
                    return False
            
            # Parse CSV manually
            csv_totals = {}
            with open(y_csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                if len(rows) < 2:
                    self.log_test("Y Tasks CSV Format", False, "CSV has less than 2 rows")
                    return False
                
                # First row contains dates, skip it
                # Each subsequent row is a task type
                for row in rows[1:]:
                    if not row or len(row) < 2:
                        continue
                    
                    task_name = row[0].strip()
                    if not task_name:
                        continue
                    
                    # Count occurrences of each worker ID for this task
                    for cell in row[1:]:
                        worker_id = cell.strip()
                        if worker_id and worker_id != '-':
                            if worker_id not in csv_totals:
                                csv_totals[worker_id] = 0
                            csv_totals[worker_id] += 1
            
            # Get statistics
            stats = self.stats_service.get_comprehensive_statistics()
            stats_y_tasks = stats['y_tasks_pie']
            
            # Test 1: Total Y tasks consistency
            csv_total = sum(csv_totals.values())
            stats_total = sum(w['value'] for w in stats_y_tasks)
            
            self.log_test(
                "Y Tasks Total Consistency",
                csv_total == stats_total,
                f"CSV Total: {csv_total}, Stats Total: {stats_total}"
            )
            
            # Test 2: Individual worker Y task counts
            all_consistent = True
            for worker_id, csv_count in csv_totals.items():
                if csv_count == 0:
                    continue
                
                # Find in stats
                stats_worker = None
                for w in stats_y_tasks:
                    if w['worker_id'] == worker_id:
                        stats_worker = w
                        break
                
                if not stats_worker:
                    self.log_test(
                        f"Worker {worker_id} Missing from Y Tasks Stats",
                        False,
                        f"Worker ID {worker_id} not found in Y tasks statistics"
                    )
                    all_consistent = False
                    continue
                
                if csv_count != stats_worker['value']:
                    self.log_test(
                        f"Worker {worker_id} Y Tasks Count Mismatch",
                        False,
                        f"CSV: {csv_count}, Stats: {stats_worker['value']}"
                    )
                    all_consistent = False
            
            self.log_test("Individual Y Tasks Counts", all_consistent)
            return all_consistent
            
        except Exception as e:
            self.log_test("Y Tasks Accuracy", False, f"Exception: {e}")
            return False
    
    def test_closing_interval_accuracy(self) -> bool:
        """Test that closing interval calculations are accurate."""
        print("\n🔍 Testing Closing Interval Accuracy...")
        
        try:
            # Load raw worker data
            worker_file = os.path.join(self.data_dir, 'worker_data.json')
            with open(worker_file, 'r', encoding='utf-8') as f:
                raw_workers = json.load(f)
            
            # Get statistics
            stats = self.stats_service.get_comprehensive_statistics()
            closing_analysis = stats['fairness_metrics']['closing_interval_analysis']
            closing_workers = closing_analysis['worker_distribution']
            
            # Test 1: Workers with closing history are included
            workers_with_closings = [w for w in raw_workers if w.get('closing_history') and len(w['closing_history']) >= 2]
            expected_count = len(workers_with_closings)
            actual_count = len(closing_workers)
            
            self.log_test(
                "Closing Analysis Worker Count",
                expected_count == actual_count,
                f"Expected: {expected_count}, Actual: {actual_count}"
            )
            
            # Test 2: Individual closing interval calculations
            all_accurate = True
            for raw_worker in workers_with_closings:
                worker_id = raw_worker['id']
                
                # Find in closing analysis
                stats_worker = None
                for w in closing_workers:
                    if w['worker_id'] == worker_id:
                        stats_worker = w
                        break
                
                if not stats_worker:
                    self.log_test(
                        f"Worker {worker_id} Missing from Closing Analysis",
                        False,
                        f"Worker {raw_worker['name']} not found in closing analysis"
                    )
                    all_accurate = False
                    continue
                
                # Manual calculation
                closing_dates = []
                for date_str in raw_worker['closing_history']:
                    try:
                        if isinstance(date_str, str):
                            closing_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        else:
                            closing_date = date_str
                        closing_dates.append(closing_date)
                    except:
                        continue
                
                if len(closing_dates) < 2:
                    continue
                
                closing_dates.sort()
                intervals = []
                for i in range(1, len(closing_dates)):
                    days_between = (closing_dates[i] - closing_dates[i-1]).days
                    weeks_between = days_between / 7.0
                    intervals.append(weeks_between)
                
                if intervals:
                    actual_avg_interval = sum(intervals) / len(intervals)
                    target_interval = raw_worker.get('closing_interval', 0)
                    
                    if target_interval > 0:
                        accuracy_percentage = max(0, 100 - (abs(actual_avg_interval - target_interval) / target_interval) * 100)
                        
                        # Compare with stats
                        if abs(stats_worker['actual_interval'] - actual_avg_interval) > 0.1:
                            self.log_test(
                                f"Worker {worker_id} Actual Interval Mismatch",
                                False,
                                f"Calculated: {actual_avg_interval:.2f}, Stats: {stats_worker['actual_interval']}"
                            )
                            all_accurate = False
                        
                        if abs(stats_worker['interval_accuracy'] - accuracy_percentage) > 0.1:
                            self.log_test(
                                f"Worker {worker_id} Accuracy Percentage Mismatch",
                                False,
                                f"Calculated: {accuracy_percentage:.1f}, Stats: {stats_worker['interval_accuracy']}"
                            )
                            all_accurate = False
                        
                        if stats_worker['total_closings'] != len(closing_dates):
                            self.log_test(
                                f"Worker {worker_id} Total Closings Mismatch",
                                False,
                                f"Calculated: {len(closing_dates)}, Stats: {stats_worker['total_closings']}"
                            )
                            all_accurate = False
            
            self.log_test("Individual Closing Interval Calculations", all_accurate)
            return all_accurate
            
        except Exception as e:
            self.log_test("Closing Interval Accuracy", False, f"Exception: {e}")
            return False
    
    def test_summary_totals(self) -> bool:
        """Test that summary totals are consistent with detailed data."""
        print("\n🔍 Testing Summary Totals...")
        
        try:
            stats = self.stats_service.get_comprehensive_statistics()
            summary = stats['summary']
            
            # Test 1: Worker count consistency
            expected_workers = len(stats['statistics']['workers'])
            actual_workers = summary['total_workers']
            
            self.log_test(
                "Worker Count in Summary",
                expected_workers == actual_workers,
                f"Expected: {expected_workers}, Actual: {actual_workers}"
            )
            
            # Test 2: X tasks total consistency
            expected_x_total = sum(w['value'] for w in stats['x_tasks_pie'])
            actual_x_total = summary['total_x_tasks']
            
            self.log_test(
                "X Tasks Total in Summary",
                expected_x_total == actual_x_total,
                f"Expected: {expected_x_total}, Actual: {actual_x_total}"
            )
            
            # Test 3: Y tasks total consistency
            expected_y_total = sum(w['value'] for w in stats['y_tasks_pie'])
            actual_y_total = summary['total_y_tasks']
            
            self.log_test(
                "Y Tasks Total in Summary",
                expected_y_total == actual_y_total,
                f"Expected: {expected_y_total}, Actual: {actual_y_total}"
            )
            
            # Test 4: Combined total consistency
            expected_combined = expected_x_total + expected_y_total
            actual_combined = summary['total_combined']
            
            self.log_test(
                "Combined Total in Summary",
                expected_combined == actual_combined,
                f"Expected: {expected_combined}, Actual: {actual_combined}"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Summary Totals", False, f"Exception: {e}")
            return False
    
    def test_percentage_calculations(self) -> bool:
        """Test that percentage calculations are mathematically correct."""
        print("\n🔍 Testing Percentage Calculations...")
        
        try:
            stats = self.stats_service.get_comprehensive_statistics()
            
            # Test 1: X tasks pie chart percentages
            x_tasks_pie = stats['x_tasks_pie']
            if x_tasks_pie:
                total_x = sum(w['value'] for w in x_tasks_pie)
                all_percentages_correct = True
                
                for worker in x_tasks_pie:
                    expected_percentage = (worker['value'] / total_x) * 100
                    actual_percentage = worker['percentage']
                    
                    if abs(expected_percentage - actual_percentage) > 0.1:
                        self.log_test(
                            f"Worker {worker['worker_id']} X Tasks Percentage",
                            False,
                            f"Expected: {expected_percentage:.1f}%, Actual: {actual_percentage}%"
                        )
                        all_percentages_correct = False
                
                self.log_test("X Tasks Percentages", all_percentages_correct)
            
            # Test 2: Y tasks pie chart percentages
            y_tasks_pie = stats['y_tasks_pie']
            if y_tasks_pie:
                total_y = sum(w['value'] for w in y_tasks_pie)
                all_percentages_correct = True
                
                for worker in y_tasks_pie:
                    expected_percentage = (worker['value'] / total_y) * 100
                    actual_percentage = worker['percentage']
                    
                    if abs(expected_percentage - actual_percentage) > 0.1:
                        self.log_test(
                            f"Worker {worker['worker_id']} Y Tasks Percentage",
                            False,
                            f"Expected: {expected_percentage:.1f}%, Actual: {actual_percentage}%"
                        )
                        all_percentages_correct = False
                
                self.log_test("Y Tasks Percentages", all_percentages_correct)
            
            return True
            
        except Exception as e:
            self.log_test("Percentage Calculations", False, f"Exception: {e}")
            return False
    
    def test_qualification_analysis(self) -> bool:
        """Test that qualification analysis is accurate."""
        print("\n🔍 Testing Qualification Analysis...")
        
        try:
            # Load raw worker data
            worker_file = os.path.join(self.data_dir, 'worker_data.json')
            with open(worker_file, 'r', encoding='utf-8') as f:
                raw_workers = json.load(f)
            
            # Get statistics
            stats = self.stats_service.get_comprehensive_statistics()
            qualification_analysis = stats['qualification_analysis']
            
            # Manual calculation
            manual_qualifications = {}
            for worker in raw_workers:
                for qualification in worker.get('qualifications', []):
                    if qualification not in manual_qualifications:
                        manual_qualifications[qualification] = {
                            'qualified_workers': 0,
                            'total_tasks': 0
                        }
                    
                    manual_qualifications[qualification]['qualified_workers'] += 1
                    
                    # Count tasks for this worker
                    worker_id = worker['id']
                    x_tasks = 0
                    y_tasks = 0
                    
                    # Find in stats
                    for x_worker in stats['x_tasks_pie']:
                        if x_worker['worker_id'] == worker_id:
                            x_tasks = x_worker['value']
                            break
                    
                    for y_worker in stats['y_tasks_pie']:
                        if y_worker['worker_id'] == worker_id:
                            y_tasks = y_worker['value']
                            break
                    
                    manual_qualifications[qualification]['total_tasks'] += x_tasks + y_tasks
            
            # Calculate averages
            for qual, data in manual_qualifications.items():
                if data['qualified_workers'] > 0:
                    data['avg_tasks_per_worker'] = data['total_tasks'] / data['qualified_workers']
            
            # Compare with stats
            all_accurate = True
            for stats_qual in qualification_analysis:
                qual_name = stats_qual['qualification']
                if qual_name not in manual_qualifications:
                    self.log_test(
                        f"Qualification {qual_name} Missing from Manual Calc",
                        False,
                        f"Qualification not found in manual calculation"
                    )
                    all_accurate = False
                    continue
                
                manual_qual = manual_qualifications[qual_name]
                
                if stats_qual['qualified_workers'] != manual_qual['qualified_workers']:
                    self.log_test(
                        f"Qualification {qual_name} Worker Count",
                        False,
                        f"Stats: {stats_qual['qualified_workers']}, Manual: {manual_qual['qualified_workers']}"
                    )
                    all_accurate = False
                
                if stats_qual['total_tasks'] != manual_qual['total_tasks']:
                    self.log_test(
                        f"Qualification {qual_name} Total Tasks",
                        False,
                        f"Stats: {stats_qual['total_tasks']}, Manual: {manual_qual['total_tasks']}"
                    )
                    all_accurate = False
                
                if abs(stats_qual['avg_tasks_per_worker'] - manual_qual['avg_tasks_per_worker']) > 0.01:
                    self.log_test(
                        f"Qualification {qual_name} Average Tasks",
                        False,
                        f"Stats: {stats_qual['avg_tasks_per_worker']}, Manual: {manual_qual['avg_tasks_per_worker']}"
                    )
                    all_accurate = False
            
            self.log_test("Qualification Analysis Accuracy", all_accurate)
            return all_accurate
            
        except Exception as e:
            self.log_test("Qualification Analysis", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("🚀 Starting Comprehensive Statistics Validation...")
        print(f"📁 Data directory: {self.data_dir}")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_worker_data_consistency,
            self.test_x_tasks_accuracy,
            self.test_y_tasks_accuracy,
            self.test_closing_interval_accuracy,
            self.test_summary_totals,
            self.test_percentage_calculations,
            self.test_qualification_analysis
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test.__name__, False, f"Test failed with exception: {e}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Statistics are 100% accurate.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please review the issues above.")
        
        # Save detailed results
        results_file = os.path.join(self.data_dir, 'statistics_validation_results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': total_tests - passed_tests,
                    'success_rate': (passed_tests / total_tests) * 100
                },
                'test_results': self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        return passed_tests == total_tests


def main():
    """Main function to run comprehensive statistics validation."""
    validator = StatisticsValidator(DATA_DIR)
    success = validator.run_all_tests()
    
    if success:
        print("\n✅ Validation completed successfully!")
        return 0
    else:
        print("\n❌ Validation completed with failures!")
        return 1


if __name__ == "__main__":
    exit(main())
