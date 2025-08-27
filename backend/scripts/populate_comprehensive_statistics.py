#!/usr/bin/env python3
"""
Script to populate the comprehensive statistics file with existing data.
This script reads all existing X tasks, Y tasks, and worker data to create
a single source of truth for the statistics page.
"""

import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path

# Add the backend directory to the path so we can import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.statistics_service import StatisticsService
from worker import load_workers_from_json
from config import DATA_DIR


def populate_x_tasks_statistics(stats_service):
    """Populate X tasks statistics from existing CSV files."""
    print("📊 Populating X tasks statistics...")
    
    x_task_files = list(Path(DATA_DIR).glob('x_tasks_*.csv'))
    
    for x_file in x_task_files:
        try:
            # Extract year and period from filename
            filename = x_file.name
            parts = filename.replace('.csv', '').split('_')
            if len(parts) >= 4:
                year = int(parts[2])
                period = int(parts[3])
                
                # Read CSV data
                with open(x_file, 'r', encoding='utf-8') as f:
                    csv_data = f.read()
                
                # Update statistics
                stats_service.update_x_tasks_data(year, period, csv_data)
                print(f"  ✅ Updated X tasks: {year}-{period}")
            else:
                print(f"  ⚠️  Skipping {filename} - invalid format")
        except Exception as e:
            print(f"  ❌ Error processing {x_file.name}: {e}")


def populate_y_tasks_statistics(stats_service):
    """Populate Y tasks statistics from existing CSV files."""
    print("📊 Populating Y tasks statistics...")
    
    y_task_files = list(Path(DATA_DIR).glob('y_tasks_*.csv'))
    
    for y_file in y_task_files:
        try:
            # Extract start and end dates from filename
            filename = y_file.name
            if '_to_' in filename:
                date_part = filename.replace('y_tasks_', '').replace('.csv', '')
                start_date, end_date = date_part.split('_to_')
                
                # Convert from filename format to display format
                start_date = start_date.replace('-', '/')
                end_date = end_date.replace('-', '/')
                
                # Read CSV data
                with open(y_file, 'r', encoding='utf-8') as f:
                    csv_data = f.read()
                
                # Update statistics
                stats_service.update_y_tasks_data(start_date, end_date, csv_data)
                print(f"  ✅ Updated Y tasks: {start_date} to {end_date}")
            else:
                print(f"  ⚠️  Skipping {filename} - invalid format")
        except Exception as e:
            print(f"  ❌ Error processing {y_file.name}: {e}")


def populate_worker_statistics(stats_service):
    """Populate worker statistics from existing worker data."""
    print("📊 Populating worker statistics...")
    
    try:
        # Load workers
        worker_file = os.path.join(DATA_DIR, 'worker_data.json')
        if os.path.exists(worker_file):
            workers = load_workers_from_json(worker_file)
            
            # Convert to the format expected by the service
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
            
            # Update statistics
            stats_service.update_worker_data(worker_data)
            print(f"  ✅ Updated {len(workers)} workers")
            
            # Update closing history for each worker
            for worker in workers:
                if hasattr(worker, 'closing_history') and worker.closing_history:
                    closing_dates = []
                    for d in worker.closing_history:
                        if hasattr(d, 'isoformat'):
                            closing_dates.append(d.isoformat())
                        else:
                            closing_dates.append(str(d))
                    
                    if closing_dates:
                        stats_service.update_closing_history(worker.id, closing_dates)
                        print(f"    ✅ Updated closing history for {worker.name}")
        else:
            print("  ⚠️  No worker_data.json found")
    except Exception as e:
        print(f"  ❌ Error processing worker data: {e}")


def main():
    """Main function to populate comprehensive statistics."""
    print("🚀 Starting comprehensive statistics population...")
    print(f"📁 Data directory: {DATA_DIR}")
    
    # Initialize statistics service
    stats_service = StatisticsService(DATA_DIR)
    
    # Populate all statistics
    populate_worker_statistics(stats_service)
    populate_x_tasks_statistics(stats_service)
    populate_y_tasks_statistics(stats_service)
    
    # Get final statistics to verify
    try:
        final_stats = stats_service.get_comprehensive_statistics()
        print("\n📈 Final Statistics Summary:")
        print(f"  Total workers: {final_stats['summary']['total_workers']}")
        print(f"  Total X tasks: {final_stats['summary']['total_x_tasks']}")
        print(f"  Total Y tasks: {final_stats['summary']['total_y_tasks']}")
        print(f"  X task periods: {len(final_stats['summary']['x_task_files'])}")
        print(f"  Y task periods: {len(final_stats['summary']['y_task_files'])}")
        print(f"  Last updated: {final_stats['metadata']['last_updated']}")
        
        print("\n✅ Comprehensive statistics population completed successfully!")
        print(f"📄 Statistics file: {stats_service.stats_file}")
        
    except Exception as e:
        print(f"\n❌ Error getting final statistics: {e}")


if __name__ == "__main__":
    main()
