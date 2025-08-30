import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ListAltIcon from '@mui/icons-material/ListAlt';
import DashboardIcon from '@mui/icons-material/Dashboard';
import HistoryIcon from '@mui/icons-material/History';
import BarChartIcon from '@mui/icons-material/BarChart';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import SettingsIcon from '@mui/icons-material/Settings';
import FadingBackground from '../components/FadingBackground';
import Footer from '../components/Footer';

function MainMenuPage() {
  const navigate = useNavigate();

  const navCards = [
    { label: 'שיבוץ משמרות', icon: <AssignmentIcon sx={{ fontSize: 48 }} />, to: '/x-tasks', desc: 'ניהול שיבוץ משמרות עיקריות' },
    { label: 'הקצאת עבודות', icon: <ListAltIcon sx={{ fontSize: 48 }} />, to: '/y-tasks', desc: 'ניהול הקצאת עבודות תמיכה' },
    { label: 'תוכנית שבועית', icon: <DashboardIcon sx={{ fontSize: 48 }} />, to: '/combined', desc: 'צפייה וניהול כל השיבוצים יחד' },
    { label: 'היסטוריית שיבוצים', icon: <HistoryIcon sx={{ fontSize: 48 }} />, to: '/reset-history', desc: 'צפייה בהיסטוריית שיבוצים קודמים' },
    { label: 'סטטיסטיקות', icon: <BarChartIcon sx={{ fontSize: 48 }} />, to: '/statistics', desc: 'צפייה בסטטיסטיקות וניתוח נתונים' },
    { label: 'הגדרות', icon: <SettingsIcon sx={{ fontSize: 48 }} />, to: '/settings', desc: 'הגדרות מערכת וניהול משימות' },
    { label: 'עזרה', icon: <HelpOutlineIcon sx={{ fontSize: 48 }} />, to: '/help', desc: 'מדריך שימוש ועזרה' },
    { label: 'ניהול עובדים', icon: <AssignmentIcon sx={{ fontSize: 48 }} />, to: '/manage-workers', desc: 'הוספה, עריכה ומחיקה של עובדים' },
  ];

  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', position: 'relative', overflow: 'hidden', bgcolor: 'transparent' }}>
      <FadingBackground />
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', pt: { xs: 8, sm: 10, md: 12 } }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4, justifyContent: 'center', width: '100%', maxWidth: 1200 }}>
          {navCards.map(card => (
            <Box
              key={card.label}
              onClick={() => navigate(card.to)}
              sx={{
                textDecoration: 'none',
                bgcolor: 'rgba(35,39,43,0.75)',
                borderRadius: 4,
                boxShadow: 6,
                p: 4,
                minWidth: 220,
                maxWidth: 260,
                minHeight: 200,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#e0e6ed',
                transition: 'transform 0.18s, box-shadow 0.18s, background 0.18s',
                cursor: 'pointer',
                '&:hover': {
                  transform: 'scale(1.045)',
                  boxShadow: 12,
                  bgcolor: 'rgba(35,39,43,0.92)',
                },
              }}
            >
              {card.icon}
              <Typography variant="h5" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>{card.label}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', textAlign: 'center' }}>{card.desc}</Typography>
            </Box>
          ))}
        </Box>
      </Box>
      <Footer />
    </Box>
  );
}

export default MainMenuPage; 