// Centralized TypeScript interfaces for the Worker Scheduling Manager

export interface Worker {
  id: string;
  name: string;
  start_date: string;
  qualifications: string[];
  closing_interval: number;
  officer: boolean;
  seniority: string;
  score: number;
  y_tasks: number;
  x_tasks: number;
  closings: number;
}

export interface YTaskDefinition {
  id: number;
  name: string;
  requiresQualification: boolean;
  autoAssign: boolean;
  isNew?: boolean;
}

export interface XTaskDefinition {
  id: number;
  name: string;
  start_day: number;
  end_day: number;
  duration_days?: number | null;
}

export interface Schedule {
  filename: string;
  start: string;
  end: string;
  period?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  error?: string;
  data?: T;
}

export interface ResetResponse {
  success: boolean;
  removed_y_files?: number;
  updated_workers?: number;
  error?: string;
}

export interface StatisticsData {
  x_tasks_pie: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  y_tasks_pie: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  worker_scores: Array<{
    name: string;
    score: number;
  }>;
  weekly_trends: Array<{
    week: string;
    x_tasks: number;
    y_tasks: number;
    avg_score: number;
  }>;
}