from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path

# Add backend to path for worker import
sys.path.append(str(Path(__file__).parent))
try:
	from .worker import EnhancedWorker
except ImportError:
	from worker import EnhancedWorker


class ClosingScheduleCalculator:
	"""
	COMPLETELY REDESIGNED Closing Schedule Calculator
	
	This new implementation uses a constraint satisfaction approach that:
	1. Respects closing intervals (no consecutive closes possible)
	2. Integrates X tasks naturally without breaking patterns
	3. Uses dynamic programming to maximize optimal picks
	4. Ensures consistent, predictable results
	
	Key Features:
	- Gap-based processing between X tasks
	- Dynamic programming for optimal date selection
	- No possibility of consecutive closes
	- Proper handling of semester boundaries
	- Clear separation of required vs optimal closes
	"""
	
	def __init__(self, gap_slack_weeks: int = 0, allow_single_relief_min1: bool = True, relief_max_per_semester: int = 1):
		"""
		gap_slack_weeks controls how much flexibility to allow beyond the strict interval.
		- For interval I, the minimum number of home weekends between closes is I-1 (MIN_GAP).
		- We set MAX_GAP = MIN_GAP + gap_slack_weeks.
		Examples:
		- I=2 → MIN_GAP=1, MAX_GAP=1+slack (0 for exact alternating close/home)
		- I=3 → MIN_GAP=2, MAX_GAP=2+slack (0 for exactly 2 homes between closes)
		- I=4 → MIN_GAP=3, MAX_GAP=3+slack
		"""
		self.debug = True
		self.user_alerts = []  # Store alerts for impossible scenarios
		self.gap_slack_weeks = max(0, int(gap_slack_weeks))
		# When True, if a middle gap (b - a) == 2n - 1, allow inserting one relief pick at a + n
		# which creates adjacent differences n and (n - 1). Intended for extreme cases only.
		self.allow_single_relief_min1 = bool(allow_single_relief_min1)
		self.relief_max_per_semester = max(0, int(relief_max_per_semester))
	
	def calculate_worker_closing_schedule(self, worker: 'EnhancedWorker', 
											semester_weeks: List[date]) -> Dict:
		"""
		MAIN METHOD: Calculate closing schedule using the new constraint satisfaction algorithm.
		
		This method completely replaces the old sequential week-by-week approach with a
		gap-based, constraint-first algorithm that guarantees no consecutive closes.
		
		Algorithm Overview:
		1. Identify gaps between X tasks (required closes)
		2. Use greedy min-gap filling per gap to maximize valid picks
		3. Respect closing interval minimum spacing throughout (n-1 homes => diff >= n)
		4. Integrate X tasks naturally without breaking patterns
		
		Returns dict with required and optimal closing DATES (mapping week numbers back to dates).
		Internally we operate over week numbers to avoid date conversions during optimization.
		"""
		if not semester_weeks:
			# No semester weeks provided, return empty schedule
			return {
				'required_dates': [],
				'optimal_dates': [],
				'final_weekends_home_owed': worker.weekends_home_owed,
				'calculation_log': ['No semester weeks provided'],
				'user_alerts': []
			}
		
		calculation_log = []
		user_alerts = []
		
		# Configurable spacing constraints derived from worker interval
		interval = max(2, int(worker.closing_interval) if worker.closing_interval else 2)
		MIN_GAP = max(1, interval - 1)
		calculation_log.append(f"Min spacing for interval {interval}: MIN_GAP={MIN_GAP} (diff between closes >= {interval})")
		
		# Get X task weeks (required closes) as week indices (0-based → convert to 1-based for clarity)
		x_task_week_idxs_zero = self._get_x_task_weeks(worker, semester_weeks)
		required_weeks_1_based = sorted([i + 1 for i in x_task_week_idxs_zero])
		total_weeks = len(semester_weeks)
		calculation_log.append(f"Found {len(required_weeks_1_based)} required weeks: {required_weeks_1_based}")
		
		# Select optimal weeks using min-gap greedy per gap
		optimal_weeks_1_based = self._select_optimal_weeks_min_gap(
			total_weeks=total_weeks,
			required_weeks_1_based=required_weeks_1_based,
			interval_weeks=interval,
			calculation_log=calculation_log
		)

		# Optional relief: if a gap equals 2n-1, insert a relief week at a+n
		# Do not apply when interval == 2 (would cause consecutive weeks after relief)
		if self.allow_single_relief_min1 and required_weeks_1_based and interval > 2 and self.relief_max_per_semester > 0:
			# Work in weeks; combine required + optimal, then scan middle gaps
			combined = sorted(list(dict.fromkeys(required_weeks_1_based + optimal_weeks_1_based)))
			added_relief: List[int] = []
			applied = 0
			for i in range(len(combined) - 1):
				a = combined[i]
				b = combined[i + 1]
				gap = b - a
				if gap == (2 * interval - 1):
					relief_week = a + interval
					if 1 <= relief_week <= total_weeks and relief_week not in combined and relief_week not in required_weeks_1_based:
						added_relief.append(relief_week)
						applied += 1
						calculation_log.append(f"Relief inserted between {a} and {b} at {relief_week} (gap {gap} == 2n-1)")
						if applied >= self.relief_max_per_semester:
							break
			# Merge relief picks
			if added_relief:
				optimal_weeks_1_based = sorted(list(dict.fromkeys(optimal_weeks_1_based + added_relief)))
		
		# Map weeks back to dates
		required_dates = [semester_weeks[w - 1] for w in required_weeks_1_based]
		optimal_dates = [semester_weeks[w - 1] for w in optimal_weeks_1_based if (w not in required_weeks_1_based)]
		
		# Calculate weekends home owed based on missed opportunities (simple heuristic)
		weekends_home_owed = worker.weekends_home_owed
		
		if self.debug:
			print(f"  Required closes: {len(required_dates)}")
			print(f"  Optimal closes (weeks): {optimal_weeks_1_based}")
			print(f"  Weekends home owed: {weekends_home_owed}")
		
		return {
			'required_dates': required_dates,
			'optimal_dates': optimal_dates,
			'final_weekends_home_owed': weekends_home_owed,
			'calculation_log': calculation_log,
			'user_alerts': user_alerts
		}

	def _select_optimal_weeks_min_gap(self,
									  total_weeks: int,
									  required_weeks_1_based: List[int],
									  interval_weeks: int,
									  calculation_log: List[str]) -> List[int]:
		"""
		WEEK-NUMBER SELECTOR WITH MIN-GAP ONLY (HARD CONSTRAINT)
		
		Enforce minimum spacing only: for any consecutive selected closes (including required),
		the difference in week numbers must be at least interval_weeks.
		
		Strategy (greedy, optimal for max count under min-sep):
		- Sort required anchors
		- Fill before first required from week 1 upward with step=interval, but ensure last pick is at least interval from the first required
		- For each middle gap (a, b are consecutive required weeks): pick sequence starting at a+interval, step=interval, up to b-interval
		- Fill after last required from last_required+interval up to total_weeks with step=interval
		- If there are no required weeks: pick 1, 1+interval, ... up to total_weeks
		Returns list of optional weeks (excluding required weeks)
		"""
		n = max(2, int(interval_weeks))
		req = sorted([w for w in required_weeks_1_based if 1 <= w <= total_weeks])
		picks: List[int] = []
		
		if not req:
			# No anchors → start at week 1 and step by n
			w = 1
			while w <= total_weeks:
				picks.append(w)
				w += n
			calculation_log.append(f"No required: picked {len(picks)} weeks starting at 1 step {n}")
			return picks
		
		# Start gap: before first required b
		b = req[0]
		latest_allowed = b - n
		if latest_allowed >= 1:
			w = 1
			while w <= latest_allowed:
				picks.append(w)
				w += n
			calculation_log.append(f"Start gap ->{b}: picked {len([p for p in picks if p < b])} weeks up to {latest_allowed}")
		else:
			calculation_log.append(f"Start gap ->{b}: none (latest_allowed={latest_allowed})")
		
		# Middle gaps
		for i in range(len(req) - 1):
			a = req[i]
			b = req[i + 1]
			start_w = a + n
			end_w = b - n
			if start_w <= end_w:
				w = start_w
				while w <= end_w:
					picks.append(w)
					w += n
				calculation_log.append(f"Gap {a}->{b}: picked from {start_w} to {end_w} step {n}")
			else:
				calculation_log.append(f"Gap {a}->{b}: none (start {start_w} > end {end_w})")
		
		# End gap: after last required a to total_weeks
		a = req[-1]
		w = a + n
		count_before = len(picks)
		while w <= total_weeks:
			picks.append(w)
			w += n
		calculation_log.append(f"End gap {a}->end: picked {len(picks) - count_before} weeks starting {a+n} step {n}")
		
		# Ensure uniqueness and order
		picks = sorted(list(dict.fromkeys([p for p in picks if p not in req and 1 <= p <= total_weeks])))
		return picks
	
	def _calculate_weekends_home_owed(self, worker: 'EnhancedWorker', 
									 semester_weeks: List[date],
									 required_dates: List[date],
									 optimal_dates: List[date],
									 weeks_since_last_close: int) -> int:
		"""
		Calculate weekends home owed based on missed opportunities.
		
		This method calculates how many weekends home the worker is owed
		based on their closing interval and missed opportunities.
		
		Args:
			worker: Worker instance
			semester_weeks: All semester weeks
			required_dates: Dates where worker must close (X tasks)
			optimal_dates: Dates where worker should close (interval)
			weeks_since_last_close: Weeks since last close
			
		Returns:
			Number of weekends home owed
		"""
		if not worker.closing_interval or worker.closing_interval < 2:
			return worker.weekends_home_owed
		
		# Calculate expected closes based on interval
		total_weeks = len(semester_weeks)
		expected_closes = max(0, (total_weeks - weeks_since_last_close) // worker.closing_interval)
		
		# Actual closes (required + optimal)
		actual_closes = len(required_dates) + len(optimal_dates)
		
		# Calculate debt
		debt = max(0, expected_closes - actual_closes)
		
		return debt
	
	def _get_x_task_weeks(self, worker: 'EnhancedWorker', semester_weeks: List[date]) -> List[int]:
		"""
		Get list of week indices that have X tasks.
		
		This method converts the worker's X tasks (stored as date strings)
		into week indices for the semester.
		
		Args:
			worker: Worker instance with x_tasks attribute
			semester_weeks: List of Friday dates for the semester
			
		Returns:
			List of week indices (0-based) where worker has X tasks
		"""
		x_task_weeks = []
		
		for week_idx, week_date in enumerate(semester_weeks):
			date_str = week_date.strftime('%d/%m/%Y')
			if date_str in worker.x_tasks:
				x_task_weeks.append(week_idx)
		
		return x_task_weeks
	
	def _get_last_closing_date(self, worker: 'EnhancedWorker', semester_start: date) -> date:
		"""
		Get the most recent closing date that is on or before the semester start.
		
		If no such date exists, synthesize a prior closing date exactly one
		interval before the semester start so the first due close will be
		at or shortly after the start (never negative weeks-since-last-close).
		
		Args:
			worker: Worker instance with closing_history
			semester_start: Start date of the semester
			
		Returns:
			Date of last close (real or synthetic)
		"""
		if worker.closing_history:
			prior = [d for d in worker.closing_history if d <= semester_start]
			if prior:
				return max(prior)
		
		# Fallback: place a synthetic last close one full interval before start
		interval = max(1, int(worker.closing_interval) if worker.closing_interval is not None else 1)
		return semester_start - timedelta(weeks=interval)
	
	def _get_weeks_since_last_close(self, last_close_date: date, semester_start: date) -> int:
		"""
		Calculate non-negative weeks between last close and semester start.
		
		Args:
			last_close_date: Date of last close
			semester_start: Start date of semester
			
		Returns:
			Number of weeks since last close (non-negative)
		"""
		if last_close_date > semester_start:
			return 0
		delta = semester_start - last_close_date
		return max(0, delta.days // 7)

	def find_next_optimal_closing_date(self,
									closing_history: List[date],
									interval_weeks: int,
									start_after_date: date,
									semester_weeks: List[date]) -> Optional[date]:
		"""
		Find the earliest Friday on or after start_after_date that respects the
		minimum interval in weeks from ALL prior closes in closing_history.

		Args:
			closing_history: Sorted or unsorted list of previous closing dates
			interval_weeks: Required minimum spacing in weeks between any two closes
			start_after_date: Date to start searching after (exclusive)
			semester_weeks: Ordered list of Friday dates that form the scheduling window

		Returns:
			The first feasible Friday date that satisfies the min-gap, or None if none exists
		"""
		if not semester_weeks:
			return None
		n = max(2, int(interval_weeks) if interval_weeks else 2)
		prior = sorted(closing_history) if closing_history else []
		for d in semester_weeks:
			if d <= start_after_date:
				continue
			valid = True
			for p in prior:
				if abs((d - p).days) // 7 < n:
					valid = False
					break
			if valid:
				return d
		return None
	
	def update_all_worker_schedules(self, workers: List['EnhancedWorker'], 
								  semester_weeks: List[date]):
		"""
		Update closing schedules for all workers using the new algorithm.
		
		This method processes all workers and updates their closing schedules
		using the new constraint satisfaction algorithm.
		
		Args:
			workers: List of all workers to update
			semester_weeks: List of Friday dates for the semester
		"""
		print(f"\n🔄 UPDATING CLOSING SCHEDULES FOR {len(workers)} WORKERS")
		print("=" * 60)
		
		self.user_alerts = []  # Reset alerts
		
		for worker in workers:
			result = self.calculate_worker_closing_schedule(worker, semester_weeks)
			
			# Update worker attributes
			worker.required_closing_dates = result['required_dates']
			worker.optimal_closing_dates = result['optimal_dates']
			worker.weekends_home_owed = result['final_weekends_home_owed']
			worker.home_weeks_owed = worker.weekends_home_owed
			
			# Collect any alerts
			if result['user_alerts']:
				self.user_alerts.extend(result['user_alerts'])
			
			if self.debug:
				print(f"\n{worker.name}:")
				print(f"  Required closes: {len(result['required_dates'])} (X tasks)")
				print(f"  Optimal closes: {len(result['optimal_dates'])} (interval)")
				print(f"  Weekends home owed: {result['final_weekends_home_owed']}")
		
		if self.user_alerts:
			print(f"\n⚠️  USER ALERTS ({len(self.user_alerts)}):")
			for alert in self.user_alerts:
				print(f"  • {alert}")
	
	def get_user_alerts(self) -> List[str]:
		"""
		Get all user alerts from the last calculation.
		
		Returns:
			List of alert messages
		"""
		return self.user_alerts.copy()
