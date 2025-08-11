/**
 * XTasksDashboardPage.tsx
 * ----------------------
 * Dashboard page for managing X task schedules (main/primary tasks).
 *
 * Renders:
 *   - Parallax/fading background
 *   - Main title
 *   - Action cards for creating or editing X task schedules
 *   - Year/period selectors
 *   - GO buttons for navigation
 *
 * State:
 *   - year, period: Selected year and half (1st/2nd)
 *   - scheduleExists: Whether a schedule already exists for the selection
 *   - bgIndex, fade: For background animation
 *
 * Effects:
 *   - Animates/fades background images
 *   - Checks if schedule exists for selected year/period
 *
 * User Interactions:
 *   - Select year/period
 *   - Navigate to create/edit X task schedule
 *
 * Notes:
 *   - Inline comments explain non-obvious logic and UI structure
 */
import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import FadingBackground from '../components/FadingBackground';
import Footer from '../components/Footer';
import Snackbar from '@mui/material/Snackbar';
import MuiAlert from '@mui/material/Alert';
import Header from '../components/Header';
import { fetchWithAuth } from '../utils/api';

function XTasksDashboardPage() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [period, setPeriod] = useState(1);
  const navigate = useNavigate();
  const [scheduleExists, setScheduleExists] = useState(false);
  const [exists1, setExists1] = useState(false);
  const [exists2, setExists2] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMsg, setSnackbarMsg] = useState('');
  const [loading, setLoading] = useState(false);
  // Restore year options
  const currentYear = new Date().getFullYear();
  const nextYear = currentYear + 1;
  const yearOptions = [currentYear, nextYear];

  // Check if schedules exist for both periods of the selected year
  const checkSchedulesExist = async () => {
    setLoading(true);
    try {
      const [res1, res2] = await Promise.all([
        fetchWithAuth(`http://localhost:5001/api/x-tasks/exists?year=${year}&period=1`, { credentials: 'include' }),
        fetchWithAuth(`http://localhost:5001/api/x-tasks/exists?year=${year}&period=2`, { credentials: 'include' })
      ]);
      
      const data1 = await res1.json();
      const data2 = await res2.json();
      
      console.log(`[DEBUG] Year ${year}: Period 1 exists: ${data1.exists}, Period 2 exists: ${data2.exists}`);
      
      setExists1(!!data1.exists);
      setExists2(!!data2.exists);
    } catch (error) {
      console.error('Error checking schedules:', error);
      // If there's an auth error, fetchWithAuth will redirect to login
      // For other errors, set to false to allow creation
      setExists1(false);
      setExists2(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkSchedulesExist();
  }, [year]);

  useEffect(() => {
    if (period === 1) setScheduleExists(exists1);
    else setScheduleExists(exists2);
    console.log(`[DEBUG] Period ${period} selected. Schedule exists: ${period === 1 ? exists1 : exists2}`);
  }, [period, exists1, exists2]);

  const handleGo = (mode: 'create' | 'edit') => {
    navigate(`/x-tasks/${mode}?year=${year}&period=${period}`);
  };

  const handleDisabledDoubleClick = (type: 'create' | 'edit') => {
    if (type === 'create') {
      setSnackbarMsg('A schedule for this year and period already exists. Try editing it, or select a different year/period.');
    } else {
      setSnackbarMsg('No schedule exists for this year and period yet. Try creating one, or select a different year/period.');
    }
    setSnackbarOpen(true);
  };

  // Helper: can create schedule for current period?
  const canCreate = period === 1 ? !exists1 : !exists2;
  // Helper: can edit schedule for current period?
  const canEdit = period === 1 ? exists1 : exists2;

  console.log(`[DEBUG] Current state - Period: ${period}, canCreate: ${canCreate}, canEdit: ${canEdit}, exists1: ${exists1}, exists2: ${exists2}`);

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background Pattern */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'radial-gradient(circle at 25% 25%, rgba(255,255,255,0.05) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(255,255,255,0.03) 0%, transparent 50%)',
        pointerEvents: 'none',
        zIndex: 0
      }} />
      
      <Box sx={{ position: 'relative', zIndex: 1 }}>
        <Header 
          darkMode={true}
          onToggleDarkMode={() => {}}
          showBackButton={true}
          showHomeButton={true}
          title="Main Tasks Dashboard"
        />
        
        {/* Main content */}
        <Box sx={{ 
          minHeight: 'calc(100vh - 80px)', 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          pt: 6, 
          position: 'relative'
        }}>
          {/* Main Title */}
          <Typography variant="h2" sx={{ 
            fontWeight: 900, 
            mb: 8, 
            color: '#e0e6ed', 
            letterSpacing: 2, 
            textShadow: '0 4px 32px rgba(0,0,0,0.5)',
            fontSize: { xs: '2.5rem', sm: '3rem', md: '4rem' },
            textAlign: 'center'
          }}>
            Main Tasks
          </Typography>
          
          {/* Year and Period Selection */}
          <Box sx={{ 
            mb: 8, 
            display: 'flex', 
            gap: 4, 
            flexWrap: 'wrap', 
            justifyContent: 'center',
            alignItems: 'center'
          }}>
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel sx={{ color: '#e0e6ed' }}>Year</InputLabel>
              <Select
                value={year}
                onChange={(e) => setYear(e.target.value as number)}
                sx={{
                  color: '#e0e6ed',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.3)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#1976d2',
                  },
                  '& .MuiSvgIcon-root': {
                    color: '#e0e6ed',
                  },
                }}
              >
                {yearOptions.map((y) => (
                  <MenuItem key={y} value={y} sx={{ color: '#1e3a5c' }}>
                    {y}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel sx={{ color: '#e0e6ed' }}>Period</InputLabel>
              <Select
                value={period}
                onChange={(e) => setPeriod(e.target.value as number)}
                sx={{
                  color: '#e0e6ed',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.3)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#1976d2',
                  },
                  '& .MuiSvgIcon-root': {
                    color: '#e0e6ed',
                  },
                }}
              >
                <MenuItem value={1} sx={{ color: '#1e3a5c' }}>1st Half</MenuItem>
                <MenuItem value={2} sx={{ color: '#1e3a5c' }}>2nd Half</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          {/* Action Cards */}
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 6, 
            justifyContent: 'center', 
            width: '100%', 
            maxWidth: 1200,
            px: 4
          }}>
            {/* Create Card */}
            <Box
              sx={{
                bgcolor: canCreate ? 'rgba(76, 175, 80, 0.15)' : 'rgba(158, 158, 158, 0.15)',
                borderRadius: 4,
                p: 4,
                width: { xs: '100%', sm: 300, md: 350 },
                textAlign: 'center',
                border: canCreate ? '2px solid rgba(76, 175, 80, 0.3)' : '2px solid rgba(158, 158, 158, 0.3)',
                backdropFilter: 'blur(10px)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: canCreate ? 'translateY(-8px)' : 'none',
                  boxShadow: canCreate ? '0 12px 40px rgba(76, 175, 80, 0.3)' : '0 8px 32px rgba(0,0,0,0.3)',
                }
              }}
            >
              <Typography variant="h4" sx={{ 
                fontWeight: 800, 
                mb: 3, 
                color: canCreate ? '#4caf50' : '#9e9e9e',
                textShadow: '0 2px 8px rgba(0,0,0,0.3)'
              }}>
                Create New Schedule
              </Typography>
              <Typography variant="body1" sx={{ 
                mb: 4, 
                color: '#e0e6ed',
                lineHeight: 1.6
              }}>
                Create a new main task schedule for {year} - {period === 1 ? '1st' : '2nd'} Half
              </Typography>
              <Button
                variant="contained"
                onClick={() => handleGo('create')}
                disabled={!canCreate || loading}
                onDoubleClick={() => handleDisabledDoubleClick('create')}
                sx={{
                  bgcolor: canCreate ? '#4caf50' : '#9e9e9e',
                  color: '#fff',
                  px: 4,
                  py: 2,
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  borderRadius: 3,
                  textTransform: 'none',
                  boxShadow: canCreate ? '0 4px 20px rgba(76, 175, 80, 0.4)' : '0 2px 8px rgba(0,0,0,0.2)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    bgcolor: canCreate ? '#45a049' : '#9e9e9e',
                    transform: canCreate ? 'translateY(-2px)' : 'none',
                    boxShadow: canCreate ? '0 6px 25px rgba(76, 175, 80, 0.6)' : '0 2px 8px rgba(0,0,0,0.2)',
                  }
                }}
              >
                {loading ? 'Loading...' : 'GO'}
              </Button>
            </Box>

            {/* Edit Card */}
            <Box
              sx={{
                bgcolor: canEdit ? 'rgba(255, 152, 0, 0.15)' : 'rgba(158, 158, 158, 0.15)',
                borderRadius: 4,
                p: 4,
                width: { xs: '100%', sm: 300, md: 350 },
                textAlign: 'center',
                border: canEdit ? '2px solid rgba(255, 152, 0, 0.3)' : '2px solid rgba(158, 158, 158, 0.3)',
                backdropFilter: 'blur(10px)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: canEdit ? 'translateY(-8px)' : 'none',
                  boxShadow: canEdit ? '0 12px 40px rgba(255, 152, 0, 0.3)' : '0 8px 32px rgba(0,0,0,0.3)',
                }
              }}
            >
              <Typography variant="h4" sx={{ 
                fontWeight: 800, 
                mb: 3, 
                color: canEdit ? '#ff9800' : '#9e9e9e',
                textShadow: '0 2px 8px rgba(0,0,0,0.3)'
              }}>
                Edit Schedule
              </Typography>
              <Typography variant="body1" sx={{ 
                mb: 4, 
                color: '#e0e6ed',
                lineHeight: 1.6
              }}>
                Modify existing main task schedule for {year} - {period === 1 ? '1st' : '2nd'} Half
              </Typography>
              <Button
                variant="contained"
                onClick={() => handleGo('edit')}
                disabled={!canEdit || loading}
                onDoubleClick={() => handleDisabledDoubleClick('edit')}
                sx={{
                  bgcolor: canEdit ? '#ff9800' : '#9e9e9e',
                  color: '#fff',
                  px: 4,
                  py: 2,
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  borderRadius: 3,
                  textTransform: 'none',
                  boxShadow: canEdit ? '0 4px 20px rgba(255, 152, 0, 0.4)' : '0 2px 8px rgba(0,0,0,0.2)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    bgcolor: canEdit ? '#f57c00' : '#9e9e9e',
                    transform: canEdit ? 'translateY(-2px)' : 'none',
                    boxShadow: canEdit ? '0 6px 25px rgba(255, 152, 0, 0.6)' : '0 2px 8px rgba(0,0,0,0.2)',
                  }
                }}
              >
                {loading ? 'Loading...' : 'GO'}
              </Button>
            </Box>
          </Box>
        </Box>
      <Footer/>
      </Box>

      {/* Snackbar for messages */}
      <Snackbar 
        open={snackbarOpen} 
        autoHideDuration={4000} 
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <MuiAlert 
          onClose={() => setSnackbarOpen(false)} 
          severity="info" 
          sx={{ 
            width: '100%',
            borderRadius: 3,
            fontWeight: 600
          }}
        >
          {snackbarMsg}
        </MuiAlert>
      </Snackbar>
    </Box>
  );
}

export default XTasksDashboardPage; 