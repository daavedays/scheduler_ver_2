import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Card, 
  CardContent,
  CircularProgress,
  Alert,
  Button
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  ComposedChart
} from 'recharts';
import PageContainer from '../components/PageContainer';

interface StatisticsData {
  x_tasks_pie: Array<{
    name: string;
    value: number;
    worker_id: string;
    percentage: number;
  }>;
  y_tasks_pie: Array<{
    name: string;
    value: number;
    worker_id: string;
    percentage: number;
  }>;
  combined_pie: Array<{
    name: string;
    value: number;
    worker_id: string;
    percentage: number;
  }>;
  x_tasks_timeline: Array<{
    period: string;
    year: number;
    half: number;
    total_tasks: number;
  }>;
  fairness_metrics: {
    seniority_distribution: Record<string, { x_tasks: number; y_tasks: number; workers: number }>;
    score_vs_tasks: Array<{
      worker_name: string;
      score: number;
      total_tasks: number;
      x_tasks: number;
      y_tasks: number;
    }>;
    qualification_utilization: Record<string, {
      qualified_workers: number;
      total_tasks: number;
      avg_tasks_per_worker: number;
    }>;
    task_distribution_histogram: Record<string, number>;
    y_task_analysis: {
      worker_distribution: Array<{
        worker_name: string;
        worker_id: string;
        y_tasks: number;
        score: number;
        seniority: string;
        closing_interval: number;
        qualifications: string[];
        closing_count: number;
        closing_dates: string[];
      }>;
      statistics: {
        total_workers_with_y_tasks: number;
        average_y_tasks_per_worker: number;
        median_y_tasks: number;
        min_y_tasks: number;
        max_y_tasks: number;
        standard_deviation: number;
      };
    };
    closing_interval_analysis: {
      worker_distribution: Array<{
        worker_name: string;
        worker_id: string;
        closing_interval: number;
        total_closings: number;
        total_weeks_served: number;
        actual_interval: number;
        interval_accuracy: number;
        last_closing_week: string | null;
        score: number;
      }>;
      statistics: {
        total_closing_workers: number;
        average_accuracy: number;
        workers_above_90_percent: number;
        workers_above_80_percent: number;
        workers_below_50_percent: number;
        algorithm_accuracy_percentage: number;
      };
    };
    worker_performance_metrics: Array<{
      worker_name: string;
      worker_id: string;
      total_tasks: number;
      x_tasks: number;
      y_tasks: number;
      x_percentage: number;
      y_percentage: number;
      workload_deviation: number;
      score: number;
      seniority: string;
      closing_interval: number;
      qualifications: string[];
    }>;
  };
  summary: {
    total_workers: number;
    total_x_tasks: number;
    total_y_tasks: number;
    total_combined: number;
    x_task_files: number;
    y_task_files: number;
  };
  // ENHANCED: New comprehensive statistics
  y_task_bar_chart: Array<{
    name: string;
    y_tasks: number;
    color: string;
    deviation: number;
    percentage: number;
  }>;
  score_vs_y_tasks: Array<{
    name: string;
    score: number;
    y_tasks: number;
    ratio: number;
  }>;
  closing_accuracy: Array<{
    name: string;
    target_interval: number;
    actual_interval: number;
    accuracy_percentage: number;
    total_closings: number;
    color: string;
  }>;
  qualification_analysis: Array<{
    qualification: string;
    qualified_workers: number;
    total_tasks: number;
    avg_tasks_per_worker: number;
    utilization_rate: number;
  }>;
  workload_distribution: Array<{
    name: string;
    total_tasks: number;
    x_tasks: number;
    y_tasks: number;
    x_percentage: number;
    y_percentage: number;
    balance_score: number;
  }>;
  seniority_analysis: Array<{
    seniority: string;
    worker_count: number;
    total_tasks: number;
    avg_tasks_per_worker: number;
  }>;
  task_timeline_analysis: Array<{
    period: string;
    total_tasks: number;
  }>;
  average_y_tasks: number;
}

// Generate colors for pie charts
const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8',
  '#82CA9D', '#FFC658', '#FF6B6B', '#4ECDC4', '#45B7D1',
  '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
  '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA', '#F1948A'
];

function StatisticsPage() {
  const [data, setData] = useState<StatisticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Fetching statistics...');
      const response = await fetch('http://localhost:5001/api/statistics', {
        credentials: 'include'
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }
      
      const statisticsData = await response.json();
      console.log('Statistics data received:', statisticsData);
      setData(statisticsData);
    } catch (err) {
      console.error('Error fetching statistics:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Paper sx={{ p: 2, border: '1px solid #ccc' }}>
          <Typography variant="body2" color="text.secondary">
            <strong>{data.name}</strong>
          </Typography>
          <Typography variant="body2">
            Tasks: {data.value}
          </Typography>
          <Typography variant="body2">
            Percentage: {data.percentage}%
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  const BarTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 2, border: '1px solid #ccc' }}>
          <Typography variant="body2" color="text.secondary">
            <strong>Period: {label}</strong>
          </Typography>
          <Typography variant="body2">
            Total X Tasks: {payload[0].value}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  console.log('StatisticsPage render - loading:', loading, 'error:', error, 'data:', data);
  
  if (loading) {
    return (
      <PageContainer>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </PageContainer>
    );
  }

  if (!data) {
    return (
      <PageContainer>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Worker Task Statistics
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchStatistics}
            disabled={loading}
          >
            Refresh Data
          </Button>
        </Box>
        <Alert severity="info">
          No statistics data available. Click "Refresh Data" to load statistics.
        </Alert>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          Worker Task Statistics
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchStatistics}
          disabled={loading}
        >
          Refresh Data
        </Button>
      </Box>

      {/* Empty dataset notice */}
      {(!data.summary || (data.summary.total_workers === 0 && data.summary.total_x_tasks === 0 && data.summary.total_y_tasks === 0 && data.summary.x_task_files === 0 && data.summary.y_task_files === 0)) && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No statistics available yet. Generate and save X/Y schedules to populate this page.
        </Alert>
      )}

        {/* Summary Cards */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              Total Workers
            </Typography>
            <Typography variant="h4">
              {data.summary.total_workers}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              Total X Tasks
            </Typography>
            <Typography variant="h4" color="primary">
              {data.summary.total_x_tasks}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              Total Y Tasks
            </Typography>
            <Typography variant="h4" color="secondary">
              {data.summary.total_y_tasks}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography color="text.secondary" gutterBottom>
              Combined Tasks
            </Typography>
            <Typography variant="h4" color="success.main">
              {data.summary.total_combined}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* TOP: Y Tasks Pie (All Workers), then X Tasks Pie (All Workers) */}
      <Paper sx={{ p: 3, mb: 6, height: '900px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          Y Tasks Distribution (All Workers)
        </Typography>
        {data.y_tasks_pie.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.y_tasks_pie}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name}: ${(percentage ?? 0)}%`}
                outerRadius={180}
                fill="#8884d8"
                dataKey="value"
              >
                {data.y_tasks_pie.map((entry, index) => (
                  <Cell key={`cell-y-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const row = payload[0].payload;
                  return (
                    <Paper sx={{ p: 2, border: '1px solid #ccc' }}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>{row.name}</strong>
                      </Typography>
                      <Typography variant="body2">Tasks: {row.value}</Typography>
                      <Typography variant="body2">Percentage: {row.percentage}%</Typography>
                    </Paper>
                  );
                }
                return null;
              }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No Y tasks data available</Typography>
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3, mb: 6, height: '900px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          X Tasks Distribution (All Workers)
        </Typography>
        {data.x_tasks_pie.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.x_tasks_pie}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name}: ${(percentage ?? 0)}%`}
                outerRadius={180}
                fill="#8884d8"
                dataKey="value"
              >
                {data.x_tasks_pie.map((entry, index) => (
                  <Cell key={`cell-x-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const row = payload[0].payload;
                  return (
                    <Paper sx={{ p: 2, border: '1px solid #ccc' }}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>{row.name}</strong>
                      </Typography>
                      <Typography variant="body2">Tasks: {row.value}</Typography>
                      <Typography variant="body2">Percentage: {row.percentage}%</Typography>
                    </Paper>
                  );
                }
                return null;
              }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No X tasks data available</Typography>
          </Box>
        )}
      </Paper>

      {/* Y Tasks Distribution Pie Chart */}
      <Paper sx={{ p: 3, mb: 6, height: '900px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          Y Tasks Distribution Analysis (All Workers)
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Shows the distribution of Y task assignments among all workers. Larger slices indicate more Y tasks assigned.
        </Typography>
        {data.fairness_metrics?.y_task_analysis?.worker_distribution?.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.fairness_metrics?.y_task_analysis?.worker_distribution ?? []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ worker_name, y_tasks }) => `${worker_name}: ${y_tasks}`}
                outerRadius={250}
                fill="#8884d8"
                dataKey="y_tasks"
              >
                {(data.fairness_metrics?.y_task_analysis?.worker_distribution ?? []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider' }}>
                        <Typography variant="body2">
                          <strong>{data.worker_name}</strong><br />
                          Y Tasks: {data.y_tasks}<br />
                          Score: {data.score}<br />
                          Seniority: {data.seniority}<br />
                          Closing Interval: {data.closing_interval}<br />
                          Actual Closings: {data.closing_count || 0}<br />
                          {data.closing_dates && data.closing_dates.length > 0 && (
                            <>
                              Closing Dates: {data.closing_dates.slice(0, 3).join(', ')}
                              {data.closing_dates.length > 3 && '...'}
                            </>
                          )}
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No Y tasks data available</Typography>
          </Box>
        )}
      </Paper>

      {/* Worker Task Count Bar Chart */}
      <Paper sx={{ p: 3, mb: 3, height: '600px' }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          Total Tasks per Worker
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Shows the total number of tasks (X + Y) assigned to each worker. Bar width represents the worker, height represents task count.
        </Typography>
        {data.fairness_metrics?.worker_performance_metrics?.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data.fairness_metrics?.worker_performance_metrics ?? []}
              margin={{ top: 20, right: 30, left: 100, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="worker_name" 
                label={{ value: 'Worker Name', position: 'insideBottom', offset: -10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'Number of Tasks', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider' }}>
                        <Typography variant="body2">
                          <strong>{data.worker_name}</strong><br />
                          Total Tasks: {data.total_tasks}<br />
                          X Tasks: {data.x_tasks}<br />
                          Y Tasks: {data.y_tasks}<br />
                          Score: {data.score}<br />
                          Seniority: {data.seniority}<br />
                          Workload Deviation: {data.workload_deviation}%
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Bar 
                dataKey="total_tasks" 
                fill="#8884d8"
                name="Total Tasks" 
              >
                {(data.fairness_metrics?.worker_performance_metrics ?? []).map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={
                      entry.total_tasks >= 10 ? '#ff4444' : // Red for high workload
                      entry.total_tasks >= 5 ? '#ff8800' : // Orange for medium workload
                      entry.total_tasks >= 2 ? '#ffff00' : // Yellow for low workload
                      '#82ca9d' // Green for very low workload
                    } 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No worker task data available</Typography>
          </Box>
        )}
      </Paper>

      {/* Debug Info */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Debug Information
        </Typography>
        <Typography variant="body2">
          X Tasks Pie Data: {data.x_tasks_pie.length} items
        </Typography>
        <Typography variant="body2">
          Y Tasks Pie Data: {data.y_tasks_pie.length} items
        </Typography>
        <Typography variant="body2">
          Combined Pie Data: {data.combined_pie.length} items
        </Typography>
        <Typography variant="body2">
          Timeline Data: {data.x_tasks_timeline.length} items
        </Typography>
      </Paper>

      {/* Y Task Statistics Summary */}
      <Paper sx={{ p: 3, mb: 6, height: '900px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          Y Task Statistics
        </Typography>
        {data.fairness_metrics?.y_task_analysis?.statistics ? (
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Distribution Summary</Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              Total Workers with Y Tasks: {data.fairness_metrics?.y_task_analysis?.statistics?.total_workers_with_y_tasks ?? 0}
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              Average Y Tasks per Worker: {(data.fairness_metrics?.y_task_analysis?.statistics?.average_y_tasks_per_worker ?? 0).toFixed(2)}
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              Median Y Tasks: {data.fairness_metrics?.y_task_analysis?.statistics?.median_y_tasks ?? 0}
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              Min Y Tasks: {data.fairness_metrics?.y_task_analysis?.statistics?.min_y_tasks ?? 0}
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              Max Y Tasks: {data.fairness_metrics?.y_task_analysis?.statistics?.max_y_tasks ?? 0}
            </Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>
              Standard Deviation: {(data.fairness_metrics?.y_task_analysis?.statistics?.standard_deviation ?? 0).toFixed(2)}
            </Typography>
            
            <Typography variant="h6" sx={{ mb: 2 }}>Top 10 Y Task Workers</Typography>
            {(data.fairness_metrics?.y_task_analysis?.worker_distribution ?? []).slice(0, 10).map((worker, index) => (
              <Box key={worker.worker_id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="body2">
                  {index + 1}. {worker.worker_name}: {worker.y_tasks} Y tasks (Score: {worker.score})
                </Typography>
              </Box>
            ))}
          </Box>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No Y task statistics available</Typography>
          </Box>
        )}
      </Paper>

      {/* Closing Interval vs Actual Closing Delta Chart */}
      <Paper sx={{ p: 3, mb: 6, height: '800px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          Closing Interval Delta Analysis
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Shows the difference between actual and target closing intervals. <strong>Negative bars</strong> = closing more frequently than target (shorter intervals), 
          <strong> Positive bars</strong> = closing less frequently than target (longer intervals = more weekends home).
        </Typography>
        <Typography variant="body2" sx={{ mb: 3, textAlign: 'center', color: 'text.secondary', fontStyle: 'italic' }}>
          Most workers should have small negative deltas (closing slightly more frequently than target). Large positive deltas indicate workers getting many more weekends home than intended.
        </Typography>
        
        {/* Delta Summary */}
        {data.fairness_metrics?.closing_interval_analysis?.worker_distribution?.length > 0 && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
            {(() => {
              const deltas = (data.fairness_metrics?.closing_interval_analysis?.worker_distribution ?? []).map(w => w.actual_interval - w.closing_interval);
              const negativeCount = deltas.filter(d => d < 0).length;
              const positiveCount = deltas.filter(d => d > 0).length;
              const zeroCount = deltas.filter(d => d === 0).length;
              const medianAbsDelta = deltas.length > 0 ? 
                deltas.map(d => Math.abs(d)).sort((a, b) => a - b)[Math.floor(deltas.length / 2)] : 0;
              const lowCoverageCount = (data.fairness_metrics?.closing_interval_analysis?.worker_distribution ?? []).filter(w => w.total_closings < 2).length;
              
              return (
                <>
                  <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="info.dark">{negativeCount}</Typography>
                    <Typography variant="body2" color="info.dark">Closing More Frequently</Typography>
                  </Box>
                  <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="success.dark">{positiveCount}</Typography>
                    <Typography variant="body2" color="success.dark">Closing Less Frequently</Typography>
                  </Box>
                  <Box sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="warning.dark">{zeroCount}</Typography>
                    <Typography variant="body2" color="warning.dark">Perfect Match</Typography>
                  </Box>
                  <Box sx={{ p: 2, bgcolor: 'secondary.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="secondary.dark">{medianAbsDelta.toFixed(1)}</Typography>
                    <Typography variant="body2" color="secondary.dark">Median Abs Delta</Typography>
                  </Box>
                </>
              );
            })()}
          </Box>
        )}
        
        {/* Low Coverage Warning */}
        {data.fairness_metrics?.closing_interval_analysis?.worker_distribution?.length > 0 && 
         (data.fairness_metrics?.closing_interval_analysis?.worker_distribution ?? []).filter(w => w.total_closings < 2).length > 0 && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Note:</strong> {(data.fairness_metrics?.closing_interval_analysis?.worker_distribution ?? []).filter(w => w.total_closings < 2).length} worker(s) have fewer than 2 closings. 
              Their accuracy and delta calculations may not be reliable (marked with ⚠️ in tooltips).
            </Typography>
          </Alert>
        )}
        
        {data.fairness_metrics?.closing_interval_analysis?.worker_distribution?.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={(data.fairness_metrics?.closing_interval_analysis?.worker_distribution ?? []).map(worker => ({
                ...worker,
                interval_delta: worker.actual_interval - worker.closing_interval
              }))}
              margin={{ top: 20, right: 30, left: 100, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="worker_name" 
                label={{ value: 'Worker Name', position: 'insideBottom', offset: -10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'Interval Delta (weeks)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    const delta = data.actual_interval - data.closing_interval;
                    const isLowCoverage = data.total_closings < 2;
                    return (
                      <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider' }}>
                        <Typography variant="body2">
                          <strong>{data.worker_name}</strong><br />
                          Target Interval: {data.closing_interval} weeks<br />
                          Actual Interval: {data.actual_interval} weeks<br />
                          Delta: {delta.toFixed(1)} weeks<br />
                          {delta < 0 ? 'Closing MORE frequently than target' : 'Closing LESS frequently than target'}<br />
                          {isLowCoverage && (
                            <Typography variant="body2" color="warning.main" sx={{ fontWeight: 'bold' }}>
                              ⚠️ Low Coverage (N/A)
                            </Typography>
                          )}
                          Accuracy: {data.interval_accuracy}%<br />
                          Total Closings: {data.total_closings}<br />
                          Total Weeks: {data.total_weeks_served}<br />
                          Score: {data.score}
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Bar 
                dataKey="interval_delta" 
                fill="#82ca9d"
                name="Interval Delta (weeks)" 
              >
                {(data.fairness_metrics?.closing_interval_analysis?.worker_distribution ?? []).map((entry, index) => {
                  const delta = entry.actual_interval - entry.closing_interval;
                  return (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={
                        delta <= 1 ? '#00ff00' : // Green for excellent (close to target)
                        delta <= 3 ? '#ffff00' : // Yellow for good
                        delta <= 5 ? '#ff8800' : // Orange for fair
                        '#ff0000' // Red for poor
                      } 
                    />
                  );
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No closing interval data available</Typography>
          </Box>
        )}
      </Paper>

      {/* X Tasks Timeline Bar Chart */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          X Tasks Timeline
        </Typography>
        {data.x_tasks_timeline.length > 0 ? (
          <ResponsiveContainer width="100%" height={600}>
            <BarChart 
              data={data.x_tasks_timeline}
              layout="vertical"
              margin={{ top: 20, right: 30, left: 80, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="period" width={80} />
              <Tooltip content={<BarTooltip />} />
              <Legend />
              <Bar dataKey="total_tasks" fill="#8884d8" name="Total X Tasks" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="600px">
            <Typography color="text.secondary">No timeline data available</Typography>
          </Box>
        )}
      </Paper>

      {/* Closing Interval Analysis Section */}
      <Typography variant="h5" sx={{ mb: 3, mt: 4, textAlign: 'center' }}>
        Closing Interval Analysis
      </Typography>

      {/* Closing Interval Accuracy Chart */}
      <Paper sx={{ p: 3, mb: 3, height: '800px' }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          Closing Interval Accuracy Distribution (All Workers)
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Shows how accurately workers are assigned to close according to their target intervals. Higher bars indicate better accuracy.
        </Typography>
        
        {/* Accuracy Summary */}
        {data.fairness_metrics.closing_interval_analysis.worker_distribution.length > 0 && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
            {(() => {
              const accuracies = data.fairness_metrics.closing_interval_analysis.worker_distribution.map(w => w.interval_accuracy);
              const medianAccuracy = accuracies.length > 0 ? 
                accuracies.sort((a, b) => a - b)[Math.floor(accuracies.length / 2)] : 0;
              const weightedAvgAccuracy = data.fairness_metrics.closing_interval_analysis.statistics?.average_accuracy || 0;
              const highAccuracyCount = accuracies.filter(a => a >= 80).length;
              const lowAccuracyCount = accuracies.filter(a => a < 50).length;
              
              return (
                <>
                  <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="success.dark">{medianAccuracy.toFixed(1)}%</Typography>
                    <Typography variant="body2" color="success.dark">Median Accuracy</Typography>
                  </Box>
                  <Box sx={{ p: 2, bgcolor: 'primary.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="primary.dark">{weightedAvgAccuracy.toFixed(1)}%</Typography>
                    <Typography variant="body2" color="primary.dark">Weighted Average</Typography>
                  </Box>
                  <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="info.dark">{highAccuracyCount}</Typography>
                    <Typography variant="body2" color="info.dark">High Accuracy (≥80%)</Typography>
                  </Box>
                  <Box sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="warning.dark">{lowAccuracyCount}</Typography>
                    <Typography variant="body2" color="warning.dark">Low Accuracy (&lt;50%)</Typography>
                  </Box>
                </>
              );
            })()}
          </Box>
        )}
        
        {data.fairness_metrics.closing_interval_analysis.worker_distribution.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data.fairness_metrics.closing_interval_analysis.worker_distribution}
              margin={{ top: 20, right: 30, left: 100, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="worker_name" 
                label={{ value: 'Worker Name', position: 'insideBottom', offset: -10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'Interval Accuracy (%)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    const isLowCoverage = data.total_closings < 2;
                    return (
                      <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider' }}>
                        <Typography variant="body2">
                          <strong>{data.worker_name}</strong><br />
                          Accuracy: {data.interval_accuracy}%<br />
                          {isLowCoverage && (
                            <Typography variant="body2" color="warning.main" sx={{ fontWeight: 'bold' }}>
                              ⚠️ Low Coverage (N/A)
                            </Typography>
                          )}
                          Target Interval: {data.closing_interval} weeks<br />
                          Actual Interval: {data.actual_interval} weeks<br />
                          Total Closings: {data.total_closings}<br />
                          Total Weeks: {data.total_weeks_served}<br />
                          Score: {data.score}
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Bar dataKey="interval_accuracy" fill="#82ca9d" name="Interval Accuracy %" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No closing interval data available</Typography>
          </Box>
        )}
      </Paper>

      {/* Removed Accuracy Deviation Scatter Plot */}

      {/* Algorithm Accuracy Summary */}
      <Paper sx={{ p: 3, mb: 3, height: '400px' }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          Algorithm Accuracy Summary
        </Typography>
        {data.fairness_metrics.closing_interval_analysis.statistics ? (
          <Box sx={{ p: 2 }}>
            <Typography variant="h4" sx={{ mb: 2, textAlign: 'center', color: 'primary.main' }}>
              {data.fairness_metrics.closing_interval_analysis.statistics.algorithm_accuracy_percentage.toFixed(1)}%
            </Typography>
            <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
              Overall Algorithm Accuracy
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 3 }}>
              <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                <Typography variant="h6" color="success.dark">
                  {data.fairness_metrics.closing_interval_analysis.statistics.workers_above_90_percent}
                </Typography>
                <Typography variant="body2" color="success.dark">
                  Workers Above 90% Accuracy
                </Typography>
              </Box>
              <Box sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                <Typography variant="h6" color="warning.dark">
                  {data.fairness_metrics.closing_interval_analysis.statistics.workers_above_80_percent}
                </Typography>
                <Typography variant="body2" color="warning.dark">
                  Workers Above 80% Accuracy
                </Typography>
              </Box>
              <Box sx={{ p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                <Typography variant="h6" color="error.dark">
                  {data.fairness_metrics.closing_interval_analysis.statistics.workers_below_50_percent}
                </Typography>
                <Typography variant="body2" color="error.dark">
                  Workers Below 50% Accuracy
                </Typography>
              </Box>
              <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="h6" color="info.dark">
                  {data.fairness_metrics.closing_interval_analysis.statistics.total_closing_workers}
                </Typography>
                <Typography variant="body2" color="info.dark">
                  Total Closing Workers
                </Typography>
              </Box>
            </Box>
          </Box>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No closing interval statistics available</Typography>
          </Box>
        )}
      </Paper>

      {/* Worker Performance Analysis */}
      <Typography variant="h5" sx={{ mb: 3, mt: 4, textAlign: 'center' }}>
        Worker Performance Analysis
      </Typography>

      {/* Workload Deviation Analysis */}
      <Paper sx={{ p: 3, mb: 3, height: '800px' }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          Workload Deviation Analysis (All Workers)
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Shows how much each worker's total task load deviates from the average. Red = Overworked, Blue = Underworked, Green = Balanced.
        </Typography>
        {data.fairness_metrics.worker_performance_metrics.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data.fairness_metrics.worker_performance_metrics}
              margin={{ top: 20, right: 30, left: 100, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="worker_name" 
                label={{ value: 'Worker Name', position: 'insideBottom', offset: -10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'Workload Deviation (%)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider' }}>
                        <Typography variant="body2">
                          <strong>{data.worker_name}</strong><br />
                          Workload Deviation: {data.workload_deviation}%<br />
                          Total Tasks: {data.total_tasks}<br />
                          X Tasks: {data.x_tasks} ({data.x_percentage}%)<br />
                          Y Tasks: {data.y_tasks} ({data.y_percentage}%)<br />
                          Score: {data.score}<br />
                          Seniority: {data.seniority}
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Bar 
                dataKey="workload_deviation" 
                fill="#82ca9d"
                name="Workload Deviation %" 
              >
                {data.fairness_metrics.worker_performance_metrics.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={
                      entry.workload_deviation > 20 ? '#ff4444' : // Red for overworked
                      entry.workload_deviation < -20 ? '#4444ff' : // Blue for underworked
                      '#82ca9d' // Green for balanced
                    } 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No workload deviation data available</Typography>
          </Box>
        )}
      </Paper>

      {/* Worker Performance Summary Cards */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          Worker Performance Summary
        </Typography>
        {data.fairness_metrics?.worker_performance_metrics?.length > 0 ? (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
            <Box sx={{ p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
              <Typography variant="h6" color="error.dark">
                {(data.fairness_metrics?.worker_performance_metrics ?? []).filter(w => w.workload_deviation > 20).length}
              </Typography>
              <Typography variant="body2" color="error.dark">
                Overworked Workers (&gt;20%)
              </Typography>
            </Box>
            <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="h6" color="info.dark">
                {(data.fairness_metrics?.worker_performance_metrics ?? []).filter(w => w.workload_deviation < -20).length}
              </Typography>
              <Typography variant="body2" color="info.dark">
                Underworked Workers (&lt;-20%)
              </Typography>
            </Box>
            <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
              <Typography variant="h6" color="success.dark">
                {(data.fairness_metrics?.worker_performance_metrics ?? []).filter(w => w.workload_deviation >= -20 && w.workload_deviation <= 20).length}
              </Typography>
              <Typography variant="body2" color="success.dark">
                Balanced Workers (±20%)
              </Typography>
            </Box>
            <Box sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
              <Typography variant="h6" color="warning.dark">
                {data.fairness_metrics?.worker_performance_metrics?.length ?? 0}
              </Typography>
              <Typography variant="body2" color="warning.dark">
                Total Workers Analyzed
              </Typography>
            </Box>
          </Box>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100px">
            <Typography color="text.secondary">No worker performance data available</Typography>
          </Box>
        )}
      </Paper>

      



      {/* Qualification Utilization */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          Qualification Utilization Analysis
        </Typography>
        {Object.keys(data.fairness_metrics.qualification_utilization).length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart
              data={Object.entries(data.fairness_metrics.qualification_utilization).map(([qual, data]) => ({
                qualification: qual,
                qualified_workers: data.qualified_workers,
                total_tasks: data.total_tasks,
                avg_tasks_per_worker: Math.round(data.avg_tasks_per_worker * 100) / 100
              }))}
              margin={{ top: 20, right: 30, left: 80, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="qualification" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="qualified_workers" fill="#8884d8" name="Qualified Workers" />
              <Bar yAxisId="left" dataKey="total_tasks" fill="#82ca9d" name="Total Tasks" />
              <Line yAxisId="right" type="monotone" dataKey="avg_tasks_per_worker" stroke="#ff7300" name="Avg Tasks/Worker" />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="400px">
            <Typography color="text.secondary">No qualification utilization data available</Typography>
          </Box>
        )}
      </Paper>

      {/* Task Distribution Histogram */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, textAlign: 'center' }}>
          Task Distribution Histogram
        </Typography>
        {Object.keys(data.fairness_metrics.task_distribution_histogram || {}).length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={Object.entries(data.fairness_metrics.task_distribution_histogram).map(([range, count]) => ({
                range,
                workers: count
              }))}
              margin={{ top: 20, right: 30, left: 80, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="workers" fill="#8884d8" name="Number of Workers" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="400px">
            <Typography color="text.secondary">No histogram data available</Typography>
          </Box>
        )}
      </Paper>

      {/* ENHANCED: Y Task Distribution Bar Chart with Color Coding */}
      <Paper sx={{ p: 3, mb: 3, height: '600px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          Y Task Distribution Analysis (Color Coded)
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Red: Overworked (above average +5%), Green: Average range (±5%), Blue: Underworked (below average -5%)
        </Typography>
        {data.y_task_bar_chart && data.y_task_bar_chart.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data.y_task_bar_chart}
              margin={{ top: 20, right: 30, left: 100, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                label={{ value: 'Worker Name', position: 'insideBottom', offset: -10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'Y Tasks', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider' }}>
                        <Typography variant="body2">
                          <strong>{data.name}</strong><br />
                          Y Tasks: {data.y_tasks}<br />
                          Deviation: {data.deviation > 0 ? '+' : ''}{data.deviation}<br />
                          Percentage: {data.percentage}%<br />
                          Status: {data.color === 'red' ? 'Overworked' : data.color === 'blue' ? 'Underworked' : 'Average'}
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="y_tasks" fill="#8884d8">
                {data.y_task_bar_chart.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No Y task distribution data available</Typography>
          </Box>
        )}
      </Paper>

      

      {/* ENHANCED: Closing Interval Accuracy */}
      <Paper sx={{ p: 3, mb: 3, height: '600px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          Closing Interval Accuracy Analysis
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Green: ≥80% accuracy, Orange: 60-79% accuracy, Red: &lt;60% accuracy
        </Typography>
        {data.closing_accuracy && data.closing_accuracy.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data.closing_accuracy}
              margin={{ top: 20, right: 30, left: 100, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                label={{ value: 'Worker Name', position: 'insideBottom', offset: -10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'Accuracy Percentage', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <Box sx={{ bgcolor: 'background.paper', p: 2, border: 1, borderColor: 'divider' }}>
                        <Typography variant="body2">
                          <strong>{data.name}</strong><br />
                          Target Interval: {data.target_interval}<br />
                          Actual Interval: {data.actual_interval}<br />
                          Accuracy: {data.accuracy_percentage}%<br />
                          Total Closings: {data.total_closings}
                        </Typography>
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="accuracy_percentage" fill="#8884d8">
                {data.closing_accuracy.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No closing accuracy data available</Typography>
          </Box>
        )}
      </Paper>

      {/* ENHANCED: Qualification Analysis */}
      <Paper sx={{ p: 3, mb: 3, height: '600px' }}>
        <Typography variant="h5" sx={{ mb: 2, textAlign: 'center' }}>
          Qualification Utilization Analysis
        </Typography>
        <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
          Shows how effectively each qualification is being utilized
        </Typography>
        {data.qualification_analysis && data.qualification_analysis.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={data.qualification_analysis}
              margin={{ top: 20, right: 30, left: 80, bottom: 80 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="qualification" 
                label={{ value: 'Qualification', position: 'insideBottom', offset: -10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis yAxisId="left" label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'Rate (%)', angle: 90, position: 'insideRight' }} />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="qualified_workers" fill="#8884d8" name="Qualified Workers" />
              <Bar yAxisId="left" dataKey="total_tasks" fill="#82ca9d" name="Total Tasks" />
              <Line yAxisId="right" type="monotone" dataKey="utilization_rate" stroke="#ff7300" name="Utilization Rate (%)" />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height="100%">
            <Typography color="text.secondary">No qualification analysis data available</Typography>
          </Box>
        )}
      </Paper>

      

      

      

      {/* Enhanced Summary Card */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Enhanced Statistics Summary
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 2 }}>
          <Typography variant="body2">
            <strong>Average Y Tasks:</strong> {data.average_y_tasks}
          </Typography>
          <Typography variant="body2">
            <strong>Overworked Workers:</strong> {data.y_task_bar_chart?.filter(w => w.color === 'red').length || 0}
          </Typography>
          <Typography variant="body2">
            <strong>Underworked Workers:</strong> {data.y_task_bar_chart?.filter(w => w.color === 'blue').length || 0}
          </Typography>
          <Typography variant="body2">
            <strong>Average Workers:</strong> {data.y_task_bar_chart?.filter(w => w.color === 'green').length || 0}
          </Typography>
          <Typography variant="body2">
            <strong>High Accuracy Closings:</strong> {data.closing_accuracy?.filter(w => w.color === 'green').length || 0}
          </Typography>
          <Typography variant="body2">
            <strong>Low Accuracy Closings:</strong> {data.closing_accuracy?.filter(w => w.color === 'red').length || 0}
          </Typography>
        </Box>
      </Paper>

      {/* Data Files Info */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Data Files Information
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2 }}>
          <Typography variant="body2">
            <strong>X Task Files:</strong> {data.summary.x_task_files}
          </Typography>
          <Typography variant="body2">
            <strong>Y Task Files:</strong> {data.summary.y_task_files}
          </Typography>
        </Box>
      </Paper>
    </PageContainer>
  );
}

export default StatisticsPage; 