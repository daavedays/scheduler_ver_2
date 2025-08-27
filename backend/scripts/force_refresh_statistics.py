#!/usr/bin/env python3
"""
Force Refresh Statistics Script
This script forces the statistics service to rebuild all statistics from existing data files.
"""

import os
import sys
import json
from pathlib import Path

# Add the backend directory to the path so we can import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.statistics_service import StatisticsService
from config import DATA_DIR


def force_refresh_statistics():
    """Force the statistics service to refresh all data."""
    print("🔄 Force refreshing statistics...")
    print(f"📁 Data directory: {DATA_DIR}")
    
    # Initialize statistics service
    stats_service = StatisticsService(DATA_DIR)
    
    # Force a complete refresh
    print("📊 Refreshing all statistics...")
    stats_service.refresh_all_statistics()
    
    # Get the updated statistics
    print("📈 Getting updated statistics...")
    stats = stats_service.get_comprehensive_statistics()
    
    # Print summary
    print("\n📊 Updated Statistics Summary:")
    print(f"  Total workers: {stats['summary']['total_workers']}")
    print(f"  Total X tasks: {stats['summary']['total_x_tasks']}")
    print(f"  Total Y tasks: {stats['summary']['total_y_tasks']}")
    print(f"  X task periods: {len(stats['summary']['x_task_files'])}")
    print(f"  Y task periods: {len(stats['summary']['y_task_files'])}")
    print(f"  Last updated: {stats['metadata']['last_updated']}")
    
    # Validate the results
    print("\n🔍 Validating statistics...")
    validation = stats_service.validate()
    
    if validation['valid']:
        print("✅ Statistics are valid!")
    else:
        print("❌ Statistics have issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    print(f"\n📄 Statistics file: {stats_service.stats_file}")
    return validation['valid']


if __name__ == "__main__":
    success = force_refresh_statistics()
    exit(0 if success else 1)
