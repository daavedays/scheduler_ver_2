/**
 * App.tsx (frontend/src/App.tsx)
 * ------------------------------
 * Main entry point for the React app. Handles global theme, authentication context, routing, and layout.
 *
 * Renders:
 *   - Navigation bar (NavBar)
 *   - All main pages (YTaskPage, XTaskPage, CombinedPage, etc.) via React Router
 *   - Global theme and dark mode
 *   - Authentication context and protected routes
 *
 * Layout:
 *   - Uses Material-UI's ThemeProvider and CssBaseline for global styling
 *   - All pages are rendered inside a <Router>
 *   - Main content is organized by routes
 *
 * State:
 *   - Auth state (loggedIn, user, error, loading)
 *   - Theme (dark mode)
 *
 * Effects:
 *   - Checks session on mount
 *   - Handles login/logout and redirects
 *
 * User Interactions:
 *   - Navigating between pages via the menu
 *   - Logging in/out
 *
 * Sections:
 *   - Navigation bar (top)
 *   - Main content (routes)
 *   - Footer (bottom)
 *
 * Notes:
 *   - All API calls are wrapped with fetchWithAuth to handle 401 redirects
 *   - Each page (YTaskPage, XTaskPage, etc.) is a separate component in /pages
 *   - Inline comments explain each major section and non-obvious logic
 */
import React, { useMemo, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography, Button, Box, TextField } from '@mui/material';
import useMediaQuery from '@mui/material/useMediaQuery';
import Snackbar from '@mui/material/Snackbar';
import MuiAlert from '@mui/material/Alert';
import Fab from '@mui/material/Fab';
import SaveIcon from '@mui/icons-material/Save';
import XTaskPage from './pages/XTaskPage';
import YTaskPage from './pages/YTaskPage';
import XTasksDashboardPage from './pages/XTasksDashboardPage';
import { useNavigate } from 'react-router-dom';
import { formatDateDMY } from './components/utils';
import { getWorkerColor } from './components/colors';
import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';
import MainMenuPage from './pages/MainMenuPage'; // Import from dedicated file
import ManageWorkersPage from './pages/ManageWorkersPage';
// Remove commented-out imports for unused pages
import StatisticsPage from './pages/StatisticsPage';
import SettingsPage from './pages/SettingsPage';


// Import shared fetch wrapper to handle 401 Unauthorized and redirect to login
import { fetchWithAuth, API_BASE_URL } from './utils/api';

// --- Theme Setup ---
import { 
  PRIMARY_COLORS, 
  BACKGROUND_COLORS, 
  TEXT_COLORS, 
  STATUS_COLORS, 
  NAVIGATION_COLORS,
  CARD_COLORS 
} from './components/colorSystem';

const getTheme = () => createTheme({
  palette: {
    mode: 'dark',
    primary: { main: PRIMARY_COLORS.primary_main },
    secondary: { main: PRIMARY_COLORS.secondary_main },
    background: {
      default: BACKGROUND_COLORS.bg_main,
      paper: BACKGROUND_COLORS.bg_secondary,
    },
    text: {
      primary: TEXT_COLORS.text_primary,
      secondary: TEXT_COLORS.text_secondary,
    },
    error: { main: STATUS_COLORS.error_main },
    warning: { main: STATUS_COLORS.warning_main },
    info: { main: STATUS_COLORS.info_main },
    success: { main: STATUS_COLORS.success_main },
  },
  typography: {
    fontFamily: "'Inter', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 500 },
    button: { fontWeight: 600 },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: { background: NAVIGATION_COLORS.nav_bg },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '8px',
          padding: '8px 16px',
          boxShadow: 'none',
          transition: 'all 0.2s',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
          },
        },
        contained: {
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: CARD_COLORS.card_shadow,
        },
      },
    },
  },
});

// --- Auth Context ---
type AuthContextType = {
  loggedIn: boolean;
  user: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
  loading: boolean;
};
const AuthContext = React.createContext<AuthContextType>({
  loggedIn: false,
  user: null,
  login: async () => {},
  logout: async () => {},
  error: null,
  loading: false,
});

function useAuth() {
  return React.useContext(AuthContext);
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { loggedIn } = useAuth();
  const location = useLocation();
  if (!loggedIn) return <Navigate to="/login" state={{ from: location }} replace />;
  // Do NOT redirect to /dashboard if logged in; just render children
  return <>{children}</>;
}

// --- Pages ---
function LoginPage() {
  const { login, error, loading, loggedIn } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  React.useEffect(() => {
    window.scrollTo(0, 0);
    // Safari/Chrome autofill workaround: scroll to top again after a short delay
    const t1 = setTimeout(() => window.scrollTo(0, 0), 100);
    const t2 = setTimeout(() => window.scrollTo(0, 0), 300);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, []);
  React.useEffect(() => {
    if (loggedIn && !loading) {
      navigate('/dashboard', { replace: true });
    }
  }, [loggedIn, loading, navigate]);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    await login(username, password);
    setSubmitting(false);
  };

  // Parallax/fade background logic
  const bgImages = [
    process.env.PUBLIC_URL + '/backgrounds/image_1.png',
    process.env.PUBLIC_URL + '/backgrounds/image_2.png',
    process.env.PUBLIC_URL + '/backgrounds/image_3.jpeg',
  ];
  // We'll use 3 sections: welcome, description, login
  // As user scrolls, fade between images
  const [scrollY, setScrollY] = useState(0);
  React.useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  // Calculate which image to show and fade amount
  const sectionHeight = 800; // px per section
  let fade = (scrollY % sectionHeight) / sectionHeight;
  let bgIndex1 = Math.floor(scrollY / sectionHeight) % bgImages.length;
  let bgIndex2 = (bgIndex1 + 1) % bgImages.length;
  // Clamp for top and bottom
  if (scrollY <= 0) {
    fade = 0;
    bgIndex1 = 0;
    bgIndex2 = 1;
  } else if (scrollY >= (bgImages.length - 1) * sectionHeight) {
    fade = 0;
    bgIndex1 = bgImages.length - 1;
    bgIndex2 = bgImages.length - 1;
  }

  // Style for the parallax/fade background
  const backgroundStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    zIndex: -1,
    pointerEvents: 'none',
    overflow: 'hidden',
  } as React.CSSProperties;

  // Style for each image (fade in/out)
  const imageStyle = (opacity: number) => ({
    position: 'absolute' as const,
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    objectFit: 'cover' as const,
    transition: 'opacity 0.7s',
    opacity,
    willChange: 'opacity',
  });



  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', overflowX: 'hidden', bgcolor: 'transparent', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', position: 'relative' }}>
      {/* Parallax/Fade Background */}
      <Box style={backgroundStyle}>
        <img src={bgImages[bgIndex1]} alt="bg1" style={imageStyle(1 - fade)} />
        <img src={bgImages[bgIndex2]} alt="bg2" style={imageStyle(fade)} />
      </Box>
      {/* Welcome Section - Better placement and styling */}
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
        <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 2 }}>
          <Box sx={{ 
            bgcolor: 'rgba(35, 39, 43, 0.65)', 
            borderRadius: 6, 
            px: 8, 
            py: 4, 
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <Typography variant="h1" sx={{ 
              fontWeight: 900, 
              color: '#e0e6ed', 
              letterSpacing: 2, 
              textShadow: '0 4px 32px #000a',
              fontSize: { xs: '3rem', sm: '4rem', md: '5rem' }
            }}>ברוכים הבאים</Typography>
          </Box>
        </Box>
      </Box>
      {/* Description Section */}
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ width: { xs: '95%', sm: '80%', md: '60%' }, bgcolor: 'rgba(35,39,43,0.65)', borderRadius: 3, boxShadow: 4, p: 4, mb: 3, textAlign: 'center', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)' }}>
          <Typography variant="h2" sx={{ mb: 2, fontWeight: 600, color: '#e0e6ed' }}>תיאור</Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            מנהל שיבוץ עבודות. בקלות תוכלו ליצור, לערוך ולצפות בשיבוצים של תורניות ועבודות בצורה מודרנית ונגישה. ניתן להשתמש בממשק מודרני ונגיש עם רקעים יפים וכניסה מאובטחת.
          </Typography>
        </Box>
      </Box>
      {/* Login Section */}
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ width: 360, maxWidth: '95vw', bgcolor: 'rgba(35,39,43,0.65)', borderRadius: 3, boxShadow: 4, p: 4, mb: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)' }}>
          <Typography variant="h5" sx={{ mb: 2, fontWeight: 700, color: '#e0e6ed' }}>Log In</Typography>
          <form onSubmit={handleSubmit} style={{ width: '100%' }}>
            <TextField
              label="Username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              fullWidth
              sx={{ mb: 2 }}
              autoFocus
              required
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              fullWidth
              sx={{ mb: 1 }}
              required
            />
            <Box sx={{ width: '100%', display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
              <Button variant="text" size="small" sx={{ textTransform: 'none' }} disabled>Forgot password?</Button>
            </Box>
            <Button
              variant="contained"
              color="primary"
              type="submit"
              disabled={submitting || loading}
              fullWidth
              sx={{ fontWeight: 700, fontSize: 18 }}
            >
              {submitting || loading ? 'Logging in...' : 'Log In'}
            </Button>
            {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
          </form>
        </Box>
      </Box>
      {/* Footer */}
      <Box sx={{ width: '100%', textAlign: 'center', py: 2, mt: 2, color: 'text.secondary', fontSize: 16, borderTop: '1px solid #ccc', opacity: 0.8 }}>
        © All Rights Reserved | Davel
      </Box>
    </Box>
  );
}

function CombinedPage() {
  const [availableSchedules, setAvailableSchedules] = React.useState<any[]>([]);
  const [selectedSchedule, setSelectedSchedule] = React.useState<any | null>(null);
  const [rowLabels, setRowLabels] = React.useState<string[]>([]);
  const [dates, setDates] = React.useState<string[]>([]);
  const [grid, setGrid] = React.useState<string[][]>([]);
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [saveSuccess, setSaveSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Load available Y schedule periods
  React.useEffect(() => {
    fetchWithAuth(`${API_BASE_URL}/api/y-tasks/list`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setAvailableSchedules(data.schedules || []);
        if (data.schedules?.length > 0) setSelectedSchedule(data.schedules[0]);
      })
      .catch(() => setError('Failed to load available schedules'));
  }, []);

  // Load combined grid when a schedule is selected
  React.useEffect(() => {
    if (!selectedSchedule) return;
    setLoading(true);
    fetchWithAuth(`${API_BASE_URL}/api/combined/by-range?start=${encodeURIComponent(selectedSchedule.start)}&end=${encodeURIComponent(selectedSchedule.end)}`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setRowLabels(data.row_labels || []);
        setDates(data.dates || []);
        setGrid(data.grid || []);
        setLoading(false);
      })
      .catch(() => { setError('Failed to load combined schedule'); setLoading(false); });
  }, [selectedSchedule]);

  // Helper function to convert worker ID to name (now handled by backend)
  const getWorkerName = (workerId: string): string => {
    return workerId; // Backend now provides names directly
  };

  const handleSave = async () => {
    if (!selectedSchedule) return;
    setSaving(true);
    try {
      // Create CSV content
      let csv = 'Task,' + dates.join(',') + '\n';
      for (let i = 0; i < rowLabels.length; i++) {
        const row = [rowLabels[i], ...grid[i].map(cell => cell || '-')];
        csv += row.join(',') + '\n';
      }
      const filename = `combined_${selectedSchedule.start.replace(/\//g, '-')}_${selectedSchedule.end.replace(/\//g, '-')}.csv`;
      const res = await fetchWithAuth(`${API_BASE_URL}/api/combined/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ csv, filename }),
      });
      if (!res.ok) throw new Error('Save failed');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      setError(e.message || 'Failed to save combined schedule');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      position: 'relative',
      overflowX: 'auto'
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
      
      <Box sx={{ position: 'relative', zIndex: 1, p: 4, pt: 12 }}>
        <Header 
          showBackButton={true}
          showHomeButton={true}
          title="Combined Schedule"
        />
        
        {/* Main Content Container */}
        <Box sx={{
          maxWidth: 1400,
          mx: 'auto',
          bgcolor: 'rgba(255,255,255,0.02)',
          borderRadius: 4,
          p: 4,
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
        }}>
          {/* Page Title */}
          <Typography variant="h3" sx={{ 
            mb: 4, 
            fontWeight: 800, 
            color: '#e0e6ed',
            textAlign: 'center',
            textShadow: '0 4px 20px rgba(0,0,0,0.5)',
            fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' }
          }}>
            Combined Schedule View
          </Typography>
          
          {/* Schedule Selection */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" sx={{ 
              mb: 3, 
              fontWeight: 700, 
              color: '#e0e6ed',
              textAlign: 'center'
            }}>
              Select Schedule Period
            </Typography>
            <Box sx={{ 
              display: 'flex', 
              gap: 2, 
              flexWrap: 'wrap', 
              justifyContent: 'center',
              mb: 3
            }}>
              {availableSchedules.map((sch: any) => (
                <Button
                  key={sch.filename}
                  variant={selectedSchedule && sch.filename === selectedSchedule.filename ? 'contained' : 'outlined'}
                  onClick={() => setSelectedSchedule(sch)}
                  sx={{ 
                    minWidth: 200,
                    borderRadius: 3,
                    textTransform: 'none',
                    fontWeight: 600,
                    fontSize: '1rem',
                    py: 1.5,
                    px: 3,
                    boxShadow: selectedSchedule && sch.filename === selectedSchedule.filename ? '0 4px 20px rgba(25, 118, 210, 0.4)' : '0 2px 8px rgba(0,0,0,0.2)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 6px 25px rgba(0,0,0,0.3)'
                    }
                  }}
                >
                  {formatDateDMY(sch.start)} TO {formatDateDMY(sch.end)}
                </Button>
              ))}
            </Box>
          </Box>

          {/* Save Button */}
          {grid.length > 0 && (
            <Box sx={{ 
              width: '100%', 
              display: 'flex', 
              justifyContent: 'center', 
              mb: 4 
            }}>
              <Fab
                color="primary"
                onClick={handleSave}
                disabled={saving || !selectedSchedule}
                sx={{ 
                  width: 70, 
                  height: 70, 
                  boxShadow: '0 6px 25px rgba(25, 118, 210, 0.4)',
                  borderRadius: '50%', 
                  fontWeight: 700,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'scale(1.1)',
                    boxShadow: '0 8px 30px rgba(25, 118, 210, 0.6)'
                  }
                }}
                aria-label="save"
              >
                <SaveIcon sx={{ fontSize: 32, color: '#fff' }} />
              </Fab>
            </Box>
          )}

          {/* Loading State */}
          {loading && (
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              py: 8 
            }}>
              <Typography variant="h6" sx={{ color: '#e0e6ed' }}>
                Loading combined schedule...
              </Typography>
            </Box>
          )}

          {/* Error State */}
          {error && (
            <Box sx={{ 
              bgcolor: 'rgba(244, 67, 54, 0.1)', 
              border: '1px solid rgba(244, 67, 54, 0.3)',
              borderRadius: 3,
              p: 3,
              mb: 3,
              textAlign: 'center'
            }}>
              <Typography color="error" variant="h6">
                {error}
              </Typography>
            </Box>
          )}

          {/* Grid */}
          {!loading && !error && grid.length > 0 && (
            <Box sx={{ 
              overflowX: 'auto',
              borderRadius: 3,
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <Box component="table" sx={{ 
                minWidth: dates.length > 0 ? Math.max(900, 180 + dates.length * 120) : 900, 
                width: '100%', 
                borderCollapse: 'separate', 
                borderSpacing: 0, 
                background: '#1a2233', 
                borderRadius: 3, 
                overflow: 'hidden'
              }}>
                <thead>
                  <tr>
                    <th style={{ 
                      minWidth: 180, 
                      background: '#22304a', 
                      color: '#fff', 
                      fontWeight: 700, 
                      fontSize: 18, 
                      position: 'sticky', 
                      left: 0, 
                      zIndex: 2, 
                      boxShadow: '0 2px 8px rgba(30,58,92,0.08)', 
                      borderBottom: '3px solid #ff9800', 
                      borderRight: '2px solid #b0bec5', 
                      height: 60, 
                      letterSpacing: 1,
                      padding: '16px'
                    }}>
                      Task
                    </th>
                    {dates.map((date, i) => (
                      <th key={i} style={{ 
                        minWidth: 120, 
                        background: '#1e3a5c', 
                        color: '#fff', 
                        fontWeight: 700, 
                        fontSize: 16, 
                        borderBottom: '3px solid #ff9800', 
                        height: 60, 
                        boxShadow: '0 2px 8px rgba(30,58,92,0.06)', 
                        borderRight: '2px solid #b0bec5',
                        padding: '16px'
                      }}>
                        {date}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rowLabels.map((task, rIdx) => (
                    <tr key={rIdx} style={{ 
                      background: rIdx % 2 === 0 ? '#232a36' : '#f9fafb' 
                    }}>
                      <td style={{ 
                        background: '#22304a', 
                        color: '#fff', 
                        fontWeight: 600, 
                        position: 'sticky', 
                        left: 0, 
                        zIndex: 1, 
                        fontSize: 18, 
                        borderRight: '3.5px solid #b0bec5', 
                        borderBottom: '2px solid #b0bec5', 
                        height: 56, 
                        paddingLeft: 32, 
                        paddingRight: 16, 
                        minWidth: 180, 
                        boxShadow: undefined 
                      }}>
                        {task}
                      </td>
                      {grid[rIdx]?.map((soldier: string, cIdx: number) => (
                        <td key={cIdx} style={{ 
                          background: soldier ? getWorkerColor(soldier, true) : '#fafbfc', 
                          color: '#1e3a5c', 
                          textAlign: 'center', 
                          fontWeight: 600, 
                          minWidth: 120, 
                          border: '2px solid #b0bec5', 
                          borderRadius: 8, 
                          fontSize: 18, 
                          height: 56, 
                          boxSizing: 'border-box', 
                          transition: 'all 0.2s ease', 
                          opacity: soldier ? 1 : 0.6, 
                          boxShadow: soldier ? '0 1px 4px rgba(30,58,92,0.06)' : undefined,
                          padding: '16px',
                          cursor: 'default'
                        }}>
                          {soldier ? getWorkerName(soldier) : ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </Box>
            </Box>
          )}
        </Box>
      </Box>

      {/* Save Success Snackbar */}
      <Snackbar 
        open={saveSuccess} 
        autoHideDuration={3000} 
        onClose={() => setSaveSuccess(false)} 
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <MuiAlert 
          onClose={() => setSaveSuccess(false)} 
          severity="success" 
          sx={{ 
            width: '100%',
            borderRadius: 3,
            fontWeight: 600
          }}
        >
          Combined schedule saved successfully!
        </MuiAlert>
      </Snackbar>
    </Box>
  );
}

function WarningsPage() {
  const [warnings, setWarnings] = React.useState<string[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    setLoading(true);
    fetchWithAuth(`${API_BASE_URL}/api/warnings`, { credentials: 'include' })
      .then((res: Response) => res.json())
      .then((data: any) => {
        setWarnings(data.warnings || []);
        setLoading(false);
      })
      .catch(() => { setError('Failed to load warnings'); setLoading(false); });
  }, []);

  if (loading) return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Typography variant="h5" sx={{ color: '#e0e6ed' }}>
        Loading warnings...
      </Typography>
    </Box>
  );
  
  if (error) return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Typography variant="h5" sx={{ color: 'error.main' }}>
        {error}
      </Typography>
    </Box>
  );

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      position: 'relative',
      overflowX: 'auto'
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
      
      <Box sx={{ position: 'relative', zIndex: 1, p: 4, pt: 12 }}>
        <Header
          showBackButton={true}
          showHomeButton={true}
          title="Warnings"
        />
        
        {/* Main Content Container */}
        <Box sx={{
          maxWidth: 800,
          mx: 'auto',
          bgcolor: 'rgba(255,255,255,0.02)',
          borderRadius: 4,
          p: 4,
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
        }}>
          {/* Page Title */}
          <Typography variant="h3" sx={{ 
            mb: 4, 
            fontWeight: 800, 
            color: '#e0e6ed',
            textAlign: 'center',
            textShadow: '0 4px 20px rgba(0,0,0,0.5)',
            fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' }
          }}>
            System Warnings
          </Typography>
          
          {/* Warnings Content */}
          {warnings.length === 0 ? (
            <Box sx={{
              textAlign: 'center',
              py: 8,
              bgcolor: 'rgba(76, 175, 80, 0.1)',
              borderRadius: 3,
              border: '1px solid rgba(76, 175, 80, 0.3)'
            }}>
              <Typography variant="h6" sx={{ 
                color: '#4caf50', 
                fontWeight: 600,
                mb: 2
              }}>
                All Clear! 🎉
              </Typography>
              <Typography variant="body1" sx={{ color: '#e0e6ed' }}>
                No warnings found. Your system is running smoothly.
              </Typography>
            </Box>
          ) : (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ 
                mb: 3, 
                color: '#ff9800', 
                fontWeight: 700,
                textAlign: 'center'
              }}>
                {warnings.length} Warning{warnings.length !== 1 ? 's' : ''} Found
              </Typography>
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 2 
              }}>
                {warnings.map((warning, i) => (
                  <Box key={i} sx={{
                    bgcolor: 'rgba(255, 152, 0, 0.1)',
                    border: '1px solid rgba(255, 152, 0, 0.3)',
                    borderRadius: 3,
                    p: 3,
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 2,
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'rgba(255, 152, 0, 0.15)',
                      transform: 'translateX(4px)'
                    }
                  }}>
                    <Box sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: '#ff9800',
                      mt: 1,
                      flexShrink: 0
                    }} />
                    <Typography sx={{ 
                      color: '#e0e6ed', 
                      fontWeight: 500,
                      lineHeight: 1.6
                    }}>
                      {warning}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

function ResetHistoryPage() {
  const [history, setHistory] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [resetting, setResetting] = React.useState(false);
  const [resetSuccess, setResetSuccess] = React.useState(false);
  const [resetError, setResetError] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const fetchHistory = React.useCallback(() => {
    setLoading(true);
    fetchWithAuth(`${API_BASE_URL}/api/history`, { credentials: 'include' })
      .then((res: Response) => res.json())
      .then((data: any) => {
        setHistory(data.history || []);
        setLoading(false);
      })
      .catch(() => { setError('Failed to load history'); setLoading(false); });
  }, []);

  React.useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleReset = async () => {
    setResetting(true);
    setResetError(null);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/api/reset`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Reset failed');
      setResetSuccess(true);
      fetchHistory();
    } catch (e: any) {
      setResetError(e.message || 'Failed to reset');
    } finally {
      setResetting(false);
    }
  };

  if (loading) return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Typography variant="h5" sx={{ color: '#e0e6ed' }}>
        Loading history...
      </Typography>
    </Box>
  );
  
  if (error) return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Typography variant="h5" sx={{ color: 'error.main' }}>
        {error}
      </Typography>
    </Box>
  );

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1a2233 0%, #2c3e50 100%)',
      position: 'relative',
      overflowX: 'auto'
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
      
      <Box sx={{ position: 'relative', zIndex: 1, p: 4, pt: 12 }}>
        <Header
          showBackButton={true}
          showHomeButton={true}
          title="Reset & History"
        />
        
        {/* Main Content Container */}
        <Box sx={{
          maxWidth: 1000,
          mx: 'auto',
          bgcolor: 'rgba(255,255,255,0.02)',
          borderRadius: 4,
          p: 4,
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
        }}>
          {/* Page Title */}
          <Typography variant="h3" sx={{ 
            mb: 4, 
            fontWeight: 800, 
            color: '#e0e6ed',
            textAlign: 'center',
            textShadow: '0 4px 20px rgba(0,0,0,0.5)',
            fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' }
          }}>
            System Reset & History
          </Typography>
          
          {/* Reset Section */}
          <Box sx={{ 
            mb: 6, 
            p: 4, 
            bgcolor: 'rgba(244, 67, 54, 0.05)', 
            borderRadius: 3,
            border: '1px solid rgba(244, 67, 54, 0.2)',
            textAlign: 'center'
          }}>
            <Typography variant="h5" sx={{ 
              mb: 3, 
              color: '#ff5252', 
              fontWeight: 700 
            }}>
              ⚠️ Danger Zone
            </Typography>
            <Typography variant="body1" sx={{ 
              mb: 4, 
              color: '#e0e6ed',
              maxWidth: 600,
              mx: 'auto',
              lineHeight: 1.6
            }}>
              This action will reset all schedules and cannot be undone. Please ensure you have backed up any important data before proceeding.
            </Typography>
            <Button 
              variant="contained" 
              color="error" 
              onClick={handleReset} 
              disabled={resetting}
              sx={{ 
                px: 4, 
                py: 2, 
                fontSize: '1.1rem',
                fontWeight: 700,
                borderRadius: 3,
                textTransform: 'none',
                boxShadow: '0 4px 20px rgba(244, 67, 54, 0.4)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 6px 25px rgba(244, 67, 54, 0.6)'
                }
              }}
            >
              {resetting ? 'Resetting...' : 'Reset All Schedules'}
            </Button>
            
            {/* Status Messages */}
            {resetSuccess && (
              <Box sx={{ 
                mt: 3, 
                p: 3, 
                bgcolor: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: 3,
                border: '1px solid rgba(76, 175, 80, 0.3)'
              }}>
                <Typography variant="h6" sx={{ 
                  color: '#4caf50', 
                  fontWeight: 600 
                }}>
                  ✅ Reset Successful!
                </Typography>
                <Typography variant="body2" sx={{ color: '#e0e6ed' }}>
                  All schedules have been reset successfully.
                </Typography>
              </Box>
            )}
            
            {resetError && (
              <Box sx={{ 
                mt: 3, 
                p: 3, 
                bgcolor: 'rgba(244, 67, 54, 0.1)', 
                borderRadius: 3,
                border: '1px solid rgba(244, 67, 54, 0.3)'
              }}>
                <Typography variant="h6" sx={{ 
                  color: '#f44336', 
                  fontWeight: 600 
                }}>
                  ❌ Reset Failed
                </Typography>
                <Typography variant="body2" sx={{ color: '#e0e6ed' }}>
                  {resetError}
                </Typography>
              </Box>
            )}
          </Box>
          
          {/* History Section */}
          <Box>
            <Typography variant="h4" sx={{ 
              mb: 3, 
              fontWeight: 700, 
              color: '#e0e6ed',
              textAlign: 'center'
            }}>
              System History
            </Typography>
            
            {history.length === 0 ? (
              <Box sx={{
                textAlign: 'center',
                py: 6,
                bgcolor: 'rgba(158, 158, 158, 0.1)',
                borderRadius: 3,
                border: '1px solid rgba(158, 158, 158, 0.3)'
              }}>
                <Typography variant="h6" sx={{ 
                  color: '#9e9e9e', 
                  fontWeight: 600,
                  mb: 2
                }}>
                  No History Available
                </Typography>
                <Typography variant="body1" sx={{ color: '#e0e6ed' }}>
                  System history will appear here after operations are performed.
                </Typography>
              </Box>
            ) : (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 2 
              }}>
                {history.map((h, i) => (
                  <Box key={i} sx={{
                    bgcolor: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 3,
                    p: 3,
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.08)',
                      transform: 'translateX(4px)'
                    }
                  }}>
                    <Typography sx={{ 
                      color: '#e0e6ed', 
                      fontWeight: 500,
                      lineHeight: 1.6,
                      fontFamily: 'monospace',
                      fontSize: '0.9rem'
                    }}>
                      {typeof h === 'string' ? h : JSON.stringify(h, null, 2)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

// --- Navigation ---
function NavBar() {
  const { loggedIn, logout } = useAuth();
  const isSmall = useMediaQuery('(max-width:900px)');
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
          <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center' }}>
            <img src={process.env.PUBLIC_URL + '/logos/nevatim.jpeg'} alt="Logo" style={{ height: 44, width: 44, marginRight: 16, borderRadius: '50%', objectFit: 'cover', background: 'none', boxShadow: '0 2px 8px #0002' }} />
          </Link>
        </Box>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>Worker Scheduling Manager</Typography>
        {loggedIn && !isLoginPage && (
          <>
            <Button color="inherit" component={Link} to="/dashboard" sx={{ fontWeight: 700, mr: 2 }}>Menu</Button>
            <Button color="inherit" onClick={logout}>Logout</Button>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
}

function AppRoutes() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  
  // Dark mode is always enabled
  const darkMode = true;

  // Scroll to top on route change
  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  // Real login/logout logic
  const login = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setLoggedIn(true);
        setUser(data.user);
        setError(null);
      } else {
        setLoggedIn(false);
        setUser(null);
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      setError('Network error');
      setLoggedIn(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };
  const logout = async () => {
    setLoading(true);
    try {
      await fetch(`${API_BASE_URL}/api/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {}
    setLoggedIn(false);
    setUser(null);
    setLoading(false);
    navigate('/login');
  };

  // Remember last visited page in localStorage
  useEffect(() => {
    if (loggedIn && location.pathname !== '/login') {
      localStorage.setItem('lastPage', location.pathname);
    }
  }, [loggedIn, location.pathname]);

  // Check session on mount
  React.useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await fetchWithAuth(`${API_BASE_URL}/api/session`, {
          credentials: 'include',
        });
        const data = await res.json();
        if (data.logged_in) {
          setLoggedIn(true);
          setUser(data.user);
        } else {
          setLoggedIn(false);
          setUser(null);
        }
      } catch {
        setLoggedIn(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <AuthContext.Provider value={{ loggedIn, user, login, logout, error, loading }}>
      {/* Only show NavBar when not on login page */}
      {location.pathname !== '/login' && <NavBar />}
      <Routes>
        <Route
          path="/"
          element={
            loggedIn
              ? <Navigate to="/dashboard" replace />
              : <Navigate to="/login" replace />
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<ProtectedRoute><MainMenuPage /></ProtectedRoute>} />
        <Route path="/x-tasks" element={<ProtectedRoute><XTasksDashboardPage /></ProtectedRoute>} />
        <Route path="/x-tasks/:mode" element={<ProtectedRoute><XTaskPage /></ProtectedRoute>} />
        <Route path="/y-tasks" element={<ProtectedRoute><YTaskPage /></ProtectedRoute>} />
        <Route path="/combined" element={<ProtectedRoute><CombinedPage /></ProtectedRoute>} />
        <Route path="/warnings" element={<ProtectedRoute><WarningsPage /></ProtectedRoute>} />
        <Route path="/reset-history" element={<ProtectedRoute><ResetHistoryPage /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        <Route path="/manage-workers" element={<ProtectedRoute><ManageWorkersPage /></ProtectedRoute>} />
        <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />

        {/* Remove commented-out routes for unused pages */}
        <Route path="/help" element={<ProtectedRoute><Box sx={{ p: 4 }}><Typography variant='h4'>דוד, אתה חוזר למילואים </Typography></Box></ProtectedRoute>} />
        {/* No catch-all redirect; let router handle refresh and unknown routes */}
      </Routes>
    </AuthContext.Provider>
  );
}

const App: React.FC = () => {
  const theme = useMemo(() => getTheme(), []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <ErrorBoundary>
          <AppRoutes />
        </ErrorBoundary>
      </Router>
    </ThemeProvider>
  );
};

export default App;
