import React, { useState } from 'react';
import { Box, Typography, Paper, Switch, FormControlLabel, Button, Alert } from '@mui/material';
import PageContainer from '../components/PageContainer';
import Header from '../components/Header';
import { fetchWithAuth } from '../utils/api';

const SettingsPage: React.FC = () => {
  const [clearY, setClearY] = useState(true);
  const [resetWorkers, setResetWorkers] = useState(true);
  const [clearHistory, setClearHistory] = useState(true);
  const [clearX, setClearX] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleReset = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fetchWithAuth('http://localhost:5001/api/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ clear_y: clearY, reset_workers: resetWorkers, clear_history: clearHistory, clear_x: clearX })
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

  return (
    <PageContainer>
      <Header darkMode={true} onToggleDarkMode={() => {}} showBackButton={true} showHomeButton={true} title="Settings" />
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Reset Data</Typography>
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Use with care. This will clear schedules and/or worker state depending on the switches below.
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
          <FormControlLabel control={<Switch checked={clearY} onChange={e => setClearY(e.target.checked)} />} label="Clear all Y schedules" />
          <FormControlLabel control={<Switch checked={resetWorkers} onChange={e => setResetWorkers(e.target.checked)} />} label="Reset workers (Y data, closings, scores)" />
          <FormControlLabel control={<Switch checked={clearHistory} onChange={e => setClearHistory(e.target.checked)} />} label="Clear worker history" />
          <FormControlLabel control={<Switch checked={clearX} onChange={e => setClearX(e.target.checked)} />} label="Also clear X from workers and custom X file" />
        </Box>
        <Button variant="contained" color="error" onClick={handleReset} disabled={loading}>
          {loading ? 'Resetting...' : 'Reset Now'}
        </Button>
        {result && <Alert severity="success" sx={{ mt: 2 }}>{result}</Alert>}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </Paper>
    </PageContainer>
  );
};

export default SettingsPage;

