from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import os

@dataclass
class ScoringConfig:
    # Early close scoring
    EARLY_CLOSE_BONUS: float = 1.0
    EARLY_CLOSE_BONUS_PER_WEEK: float = 0.5
    
    # Overdue penalties
    OVERDUE_REDUCTION_PER_WEEK: float = 0.5
    
    # Weekend compensation
    OWE_TO_SCORE_CONVERSION: float = 0.5
    
    # Y-task fairness
    Y_TASK_FAIRNESS_WEIGHT: float = 0.3
    
    # Multiple Y tasks in same week
    MULTIPLE_Y_TASK_WEEK_THRESHOLD: int = 1
    MULTIPLE_Y_TASK_WEEK_BONUS: float = 0.5
    
    # Closing relief settings
    CLOSING_RELIEF_ENABLED: bool = True
    CLOSING_RELIEF_MAX_PER_SEMESTER: int = 1
    
    # Assignment reversal penalties
    SWITCH_PENALTY_Y_TASK: float = 0.5
    SWITCH_PENALTY_CLOSING: float = 1.0
    
    # Task weights for weighted calculations
    TASK_WEIGHTS: Dict[str, float] = None
    
    def __post_init__(self):
        if self.TASK_WEIGHTS is None:
            # Initialize with empty dict - will be populated dynamically from backend
            self.TASK_WEIGHTS = {}

def load_config(overrides_path: Optional[str] = None) -> ScoringConfig:
    """Load scoring configuration from file or return defaults."""
    if overrides_path and os.path.exists(overrides_path):
        try:
            with open(overrides_path, 'r', encoding='utf-8') as f:
                overrides = json.load(f)
            return ScoringConfig(**overrides)
        except Exception as e:
            print(f"Warning: Could not load scoring config from {overrides_path}: {e}")
    
    return ScoringConfig()


