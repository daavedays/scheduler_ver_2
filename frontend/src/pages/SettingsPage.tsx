import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Switch, FormControlLabel, Button, Alert, Divider, TextField, Select, MenuItem } from '@mui/material';
import PageContainer from '../components/PageContainer';
import Header from '../components/Header';
import { fetchWithAuth, API_BASE_URL } from '../utils/api';
import { YTaskDefinition, XTaskDefinition } from '../types';

const SettingsPage: React.FC = () => {
  const [clearY, setClearY] = useState(true);
  // Removed: user cannot reset workers from UI
  const [clearHistory, setClearHistory] = useState(true);
  const [clearX, setClearX] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsResult, setStatsResult] = useState<string | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);

  // --- Worker reset state ---
  const [workerLoading, setWorkerLoading] = useState(false);
  const [workerResult, setWorkerResult] = useState<string | null>(null);
  const [workerError, setWorkerError] = useState<string | null>(null);

  // --- Y task definitions state ---
  const [yDefs, setYDefs] = useState<YTaskDefinition[]>([]);
  const [yLoading, setYLoading] = useState(false);
  const [yError, setYError] = useState<string | null>(null);
  const [ySuccess, setYSuccess] = useState<string | null>(null);
  const [newYName, setNewYName] = useState('');
  const [newYReqQual, setNewYReqQual] = useState(true);
  const [newYAuto, setNewYAuto] = useState(true);

  // --- X task definitions state ---
  const [xDefs, setXDefs] = useState<XTaskDefinition[]>([]);
  const [xLoading, setXLoading] = useState(false);
  const [xError, setXError] = useState<string | null>(null);
  const [xSuccess, setXSuccess] = useState<string | null>(null);
  const [newXName, setNewXName] = useState('');
  const [newXStartDay, setNewXStartDay] = useState<number>(0);
  const [newXEndDay, setNewXEndDay] = useState<number>(6);
  const [newXDuration, setNewXDuration] = useState<string>('');

  const DAY_OPTIONS = [
    { value: 0, label: 'Sun' },
    { value: 1, label: 'Mon' },
    { value: 2, label: 'Tue' },
    { value: 3, label: 'Wed' },
    { value: 4, label: 'Thu' },
    { value: 5, label: 'Fri' },
    { value: 6, label: 'Sat' },
  ];

  // --- Load definitions ---
  useEffect(() => {
    const load = async () => {
      try {
        setYLoading(true);
        setXLoading(true);
        const [yRes, xRes] = await Promise.all([
          fetchWithAuth(`${API_BASE_URL}/api/y-tasks/definitions`, { credentials: 'include' }),
          fetchWithAuth(`${API_BASE_URL}/api/x-tasks/definitions`, { credentials: 'include' }),
        ]);
        const yData = await yRes.json();
        const xData = await xRes.json();
        if (!yRes.ok) throw new Error(yData.error || 'Failed to load Y definitions');
        if (!xRes.ok) throw new Error(xData.error || 'Failed to load X definitions');
        setYDefs(yData.definitions || []);
        setXDefs(xData.definitions || []);
      } catch (e: any) {
        const msg = e.message || 'Failed to load definitions';
        setYError(msg);
        setXError(msg);
      } finally {
        setYLoading(false);
        setXLoading(false);
      }
    };
    load();
  }, []);

  // --- Y handlers ---
  const handleAddY = async () => {
    setYError(null); setYSuccess(null);
    try {
      if (!newYName.trim()) throw new Error('Name required');
      const res = await fetchWithAuth(`${API_BASE_URL}/api/y-tasks/definitions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: newYName.trim(), requiresQualification: newYReqQual, autoAssign: newYAuto }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Add failed');
      setYDefs((prev) => [...prev, data.definition]);
      setNewYName(''); setNewYReqQual(true); setNewYAuto(true);
      setYSuccess('Y task added');
    } catch (e: any) {
      setYError(e.message || 'Add failed');
    }
  };

  const handleUpdateY = async (id: number, updates: Partial<YTaskDefinition>) => {
    setYError(null); setYSuccess(null);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/api/y-tasks/definitions/${id}` , {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Update failed');
      setYDefs((prev) => prev.map((d) => d.id === id ? data.definition : d));
      setYSuccess('Y task updated');
    } catch (e: any) {
      setYError(e.message || 'Update failed');
    }
  };

  const handleDeleteY = async (id: number) => {
    setYError(null); setYSuccess(null);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/api/y-tasks/definitions/${id}` , {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.status === 404) throw new Error('Not found');
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Delete failed');
      }
      setYDefs((prev) => prev.filter((d) => d.id !== id));
      setYSuccess('Y task deleted');
    } catch (e: any) {
      setYError(e.message || 'Delete failed');
    }
  };

  // --- X handlers ---
  const handleAddX = async () => {
    setXError(null); setXSuccess(null);
    try {
      if (!newXName.trim()) throw new Error('Name required');
      const payload: any = { name: newXName.trim(), start_day: newXStartDay, end_day: newXEndDay };
      if (newXDuration.trim()) payload.duration_days = parseInt(newXDuration.trim(), 10);
      const res = await fetchWithAuth(`${API_BASE_URL}/api/x-tasks/definitions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Add failed');
      setXDefs((prev) => [...prev, data.definition]);
      setNewXName(''); setNewXStartDay(0); setNewXEndDay(6); setNewXDuration('');
      setXSuccess('X task added');
    } catch (e: any) {
      setXError(e.message || 'Add failed');
    }
  };

  const handleUpdateX = async (id: number, updates: Partial<XTaskDefinition>) => {
    setXError(null); setXSuccess(null);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/api/x-tasks/definitions/${id}` , {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Update failed');
      setXDefs((prev) => prev.map((d) => d.id === id ? data.definition : d));
      setXSuccess('X task updated');
    } catch (e: any) {
      setXError(e.message || 'Update failed');
    }
  };

  const handleDeleteX = async (id: number) => {
    setXError(null); setXSuccess(null);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/api/x-tasks/definitions/${id}` , {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.status === 404) throw new Error('Not found');
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Delete failed');
      }
      setXDefs((prev) => prev.filter((d) => d.id !== id));
      setXSuccess('X task deleted');
    } catch (e: any) {
      setXError(e.message || 'Delete failed');
    }
  };

  const handleReset = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        // Worker reset is disabled by policy
        body: JSON.stringify({ clear_y: clearY, clear_history: clearHistory, clear_x: clearX })
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'Reset failed');
      setResult(`Reset success. Removed Y files: ${data.removed_y_files}, Updated workers: ${data.updated_workers}`);
    } catch (e: any) {
      setError(e.message || 'Reset failed');
    } finally {
      setLoading(false);
    }
  };

  const handleResetStatistics = async () => {
    setStatsLoading(true);
    setStatsResult(null);
    setStatsError(null);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/api/statistics/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Statistics reset failed');
      setStatsResult('Statistics have been reset successfully');
    } catch (e: any) {
      setStatsError(e.message || 'Statistics reset failed');
    } finally {
      setStatsLoading(false);
    }
  };

  const handleResetWorkers = async () => {
    setWorkerLoading(true);
    setWorkerResult(null);
    setWorkerError(null);
    try {
      const confirmed = window.confirm('This will reset worker data fields (tasks, counts, closings, scores) for all workers. Continue?');
      if (!confirmed) {
        setWorkerLoading(false);
        return;
      }
      const res = await fetchWithAuth(`${API_BASE_URL}/api/workers/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'Worker data reset failed');
      setWorkerResult(`Worker data reset successfully. Updated workers: ${data.updated_workers}`);
    } catch (e: any) {
      setWorkerError(e.message || 'Worker data reset failed');
    } finally {
      setWorkerLoading(false);
    }
  };

  return (
    <PageContainer>
      <Header showBackButton={true} showHomeButton={true} title="Settings" />
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Reset Data</Typography>
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Use with care. This will clear schedules and/or worker state depending on the switches below.
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
          <FormControlLabel control={<Switch checked={clearY} onChange={e => setClearY(e.target.checked)} />} label="Clear all Y schedules" />
          <FormControlLabel control={<Switch checked={clearHistory} onChange={e => setClearHistory(e.target.checked)} />} label="Clear worker history" />
          <FormControlLabel control={<Switch checked={clearX} onChange={e => setClearX(e.target.checked)} />} label="Also clear X from workers and custom X file" />
        </Box>
        <Button variant="contained" color="error" onClick={handleReset} disabled={loading}>
          {loading ? 'Resetting...' : 'Reset Now'}
        </Button>
        {result && <Alert severity="success" sx={{ mt: 2 }}>{result}</Alert>}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Statistics Management</Typography>
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Reset the statistics database to clear all accumulated statistics data. This will not affect actual schedules or worker data.
        </Typography>
        <Button variant="contained" color="warning" onClick={handleResetStatistics} disabled={statsLoading}>
          {statsLoading ? 'Resetting Statistics...' : 'Reset Statistics'}
        </Button>
        {statsResult && <Alert severity="success" sx={{ mt: 2 }}>{statsResult}</Alert>}
        {statsError && <Alert severity="error" sx={{ mt: 2 }}>{statsError}</Alert>}
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Worker Data Reset</Typography>
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Reset worker fields like tasks, counts, closing history, and scores for all workers. This does not delete workers.
        </Typography>
        <Button variant="contained" color="error" onClick={handleResetWorkers} disabled={workerLoading}>
          {workerLoading ? 'Resetting Workers...' : 'Reset Worker Data'}
        </Button>
        {workerResult && <Alert severity="success" sx={{ mt: 2 }}>{workerResult}</Alert>}
        {workerError && <Alert severity="error" sx={{ mt: 2 }}>{workerError}</Alert>}
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Y Task Definitions</Typography>
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Manage Y tasks, toggle qualification requirement and auto-assign behavior.
        </Typography>
        {yError && <Alert severity="error" sx={{ mb: 2 }}>{yError}</Alert>}
        {ySuccess && <Alert severity="success" sx={{ mb: 2 }}>{ySuccess}</Alert>}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 2 }}>
          <TextField size="small" label="New Y Task Name" value={newYName} onChange={e => setNewYName(e.target.value)} />
          <FormControlLabel control={<Switch checked={newYReqQual} onChange={e => setNewYReqQual(e.target.checked)} />} label="Requires Qualification" />
          <FormControlLabel control={<Switch checked={newYAuto} onChange={e => setNewYAuto(e.target.checked)} />} label="Auto Assign" />
          <Button variant="contained" onClick={handleAddY} disabled={yLoading}>Add</Button>
        </Box>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {(yDefs || []).map((d) => (
            <Box key={d.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TextField size="small" label="Name" value={d.name} onChange={(e) => setYDefs(prev => prev.map(p => p.id === d.id ? { ...p, name: e.target.value } : p))} sx={{ minWidth: 220 }} />
              <FormControlLabel control={<Switch checked={!!d.requiresQualification} onChange={(e) => handleUpdateY(d.id, { requiresQualification: e.target.checked })} />} label="Requires Qualification" />
              <FormControlLabel control={<Switch checked={!!d.autoAssign} onChange={(e) => handleUpdateY(d.id, { autoAssign: e.target.checked })} />} label="Auto Assign" />
              <Button size="small" variant="outlined" onClick={() => handleUpdateY(d.id, { name: d.name })} disabled={yLoading}>Save</Button>
              <Button size="small" color="error" variant="outlined" onClick={() => handleDeleteY(d.id)} disabled={yLoading}>Delete</Button>
            </Box>
          ))}
        </Box>
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>X Task Definitions</Typography>
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Manage X tasks start/end day and optional duration. Days use Sun=0 ... Sat=6.
        </Typography>
        {xError && <Alert severity="error" sx={{ mb: 2 }}>{xError}</Alert>}
        {xSuccess && <Alert severity="success" sx={{ mb: 2 }}>{xSuccess}</Alert>}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap', mb: 2 }}>
          <TextField size="small" label="New X Task Name" value={newXName} onChange={e => setNewXName(e.target.value)} />
          <Select size="small" value={newXStartDay} onChange={(e) => setNewXStartDay(e.target.value as number)}>
            {DAY_OPTIONS.map(opt => (<MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>))}
          </Select>
          <Select size="small" value={newXEndDay} onChange={(e) => setNewXEndDay(e.target.value as number)}>
            {DAY_OPTIONS.map(opt => (<MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>))}
          </Select>
          <TextField size="small" label="Duration (days, optional)" value={newXDuration} onChange={e => setNewXDuration(e.target.value)} sx={{ width: 200 }} />
          <Button variant="contained" onClick={handleAddX} disabled={xLoading}>Add</Button>
        </Box>
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {(xDefs || []).map((d) => (
            <Box key={d.id} sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <TextField size="small" label="Name" value={d.name} onChange={(e) => setXDefs(prev => prev.map(p => p.id === d.id ? { ...p, name: e.target.value } : p))} sx={{ minWidth: 220 }} />
              <Select size="small" value={d.start_day} onChange={(e) => handleUpdateX(d.id, { start_day: e.target.value })}>
                {DAY_OPTIONS.map(opt => (<MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>))}
              </Select>
              <Select size="small" value={d.end_day} onChange={(e) => handleUpdateX(d.id, { end_day: e.target.value })}>
                {DAY_OPTIONS.map(opt => (<MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>))}
              </Select>
              <TextField size="small" label="Duration (days)" value={d.duration_days ?? ''} onChange={(e) => {
                const val = e.target.value;
                setXDefs(prev => prev.map(p => p.id === d.id ? { ...p, duration_days: (val === '' ? null : Number(val)) } : p));
              }} sx={{ width: 180 }} />
              <Button size="small" variant="outlined" onClick={() => handleUpdateX(d.id, { name: d.name, duration_days: d.duration_days ?? null })} disabled={xLoading}>Save</Button>
              <Button size="small" color="error" variant="outlined" onClick={() => handleDeleteX(d.id)} disabled={xLoading}>Delete</Button>
            </Box>
          ))}
        </Box>
      </Paper>
    </PageContainer>
  );
};

export default SettingsPage;

