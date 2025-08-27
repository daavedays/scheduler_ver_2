#!/usr/bin/env python3
"""
Manual Populate Workers Script
This script manually populates worker data in the statistics service.
"""

import os
import sys
import json
from pathlib import Path

# Add the backend directory to the path so we can import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.statistics_service import StatisticsService
from worker import load_workers_from_json
from config import DATA_DIR


def manual_populate_workers():
    """Manually populate worker data in statistics."""
    print("👥 Manually populating worker data...")
    print(f"📁 Data directory: {DATA_DIR}")
    
    # Initialize statistics service
    stats_service = StatisticsService(DATA_DIR)
    
    # Load workers from worker_data.json
    worker_file = os.path.join(DATA_DIR, 'worker_data.json')
    if not os.path.exists(worker_file):
        print("❌ worker_data.json not found!")
        return False
    
    print("📖 Loading workers from worker_data.json...")
    workers = load_workers_from_json(worker_file)
    print(f"✅ Loaded {len(workers)} workers")
    
    # Convert workers to the format expected by the service
    worker_data = []
    for worker in workers:
        # Convert date objects to strings to avoid JSON serialization issues
        closing_history = []
        for d in getattr(worker, 'closing_history', []):
            if hasattr(d, 'isoformat'):
                closing_history.append(d.isoformat())
            else:
                closing_history.append(str(d))
        
        required_closing_dates = []
        for d in getattr(worker, 'required_closing_dates', []):
            if hasattr(d, 'isoformat'):
                required_closing_dates.append(d.isoformat())
            else:
                required_closing_dates.append(str(d))
        
        optimal_closing_dates = []
        for d in getattr(worker, 'optimal_closing_dates', []):
            if hasattr(d, 'isoformat'):
                optimal_closing_dates.append(d.isoformat())
            else:
                optimal_closing_dates.append(str(d))
        
        worker_data.append({
            'id': getattr(worker, 'id', None),
            'name': worker.name,
            'qualifications': getattr(worker, 'qualifications', []),
            'closing_interval': getattr(worker, 'closing_interval', 4),
            'officer': getattr(worker, 'officer', False),
            'score': getattr(worker, 'score', 0),
            'seniority': getattr(worker, 'seniority', 'Unknown'),
            'closing_history': closing_history,
            'required_closing_dates': required_closing_dates,
            'optimal_closing_dates': optimal_closing_dates
        })
    
    print("🔄 Updating worker data in statistics...")
    stats_service.update_worker_data(worker_data)
    
    # Get the updated statistics
    print("📈 Getting updated statistics...")
    stats = stats_service.get_comprehensive_statistics()
    
    # Print summary
    print("\n📊 Updated Statistics Summary:")
    print(f"  Total workers: {stats['summary']['total_workers']}")
    print(f"  Total X tasks: {stats['summary']['total_x_tasks']}")
    print(f"  Total Y tasks: {stats['summary']['total_y_tasks']}")
    
    # Handle summary data safely
    x_task_files = stats['summary'].get('x_task_files', [])
    y_task_files = stats['summary'].get('y_task_files', [])
    
    if isinstance(x_task_files, list):
        print(f"  X task periods: {len(x_task_files)}")
    else:
        print(f"  X task periods: {x_task_files}")
    
    if isinstance(y_task_files, list):
        print(f"  Y task periods: {len(y_task_files)}")
    else:
        print(f"  Y task periods: {y_task_files}")
    
    print(f"  Last updated: {stats['metadata']['last_updated']}")
    
    # Check if workers are populated
    if stats['statistics']['workers']:
        print(f"✅ Workers populated: {len(stats['statistics']['workers'])} workers")
    else:
        print("❌ Workers still not populated")
        return False
    
    print(f"\n📄 Statistics file: {stats_service.stats_file}")
    return True


if __name__ == "__main__":
    success = manual_populate_workers()
    exit(0 if success else 1)
