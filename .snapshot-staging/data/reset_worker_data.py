#!/usr/bin/env python3
"""
Reset Worker Data Script
Resets all worker data including x_tasks, y_tasks, closing_history, and scores
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent
WORKER_JSON_PATH = DATA_DIR / "worker_data.json"

def reset_worker_data(input_path, output_path):
    """
    Resets worker data by clearing closing history and Y-task counts.
    
    This script is intended as a one-time fix to purge corrupted data from
    the old scheduling system. It preserves core worker attributes.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        workers = json.load(f)

    for worker in workers:
        # Clear closing history
        worker['closing_history'] = []
        
        # Reset all Y-task counts to zero
        if 'y_task_counts' in worker:
            for task in worker['y_task_counts']:
                worker['y_task_counts'][task] = 0
        else:
            # If no y_task_counts field, create it
            worker['y_task_counts'] = {
                "Supervisor": 0,
                "C&N Driver": 0,
                "C&N Escort": 0,
                "Southern Driver": 0,
                "Southern Escort": 0
            }
        
        # Also reset aggregate counters
        worker['y_task_count'] = 0
        worker['x_task_count'] = 0
        worker['score'] = 100.0 # Reset score to a neutral baseline
        worker['optimal_closing_dates'] = []
        worker['required_closing_dates'] = []


    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workers, f, indent=2, ensure_ascii=False)

    print(f"Worker data has been reset and saved to {output_path}")
    print("One-time reset complete. The new engine can now operate on clean data.")

if __name__ == '__main__':
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the input and output paths relative to the script's location
    input_file = os.path.join(current_dir, 'worker_data.json')
    output_file = os.path.join(current_dir, 'worker_data_reset.json')
    
    reset_worker_data(input_file, output_file)
