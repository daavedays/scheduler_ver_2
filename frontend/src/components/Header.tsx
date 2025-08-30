import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import HomeIcon from '@mui/icons-material/Home';
import MenuIcon from '@mui/icons-material/Menu';


interface HeaderProps {
  showBackButton?: boolean;
  showHomeButton?: boolean;
  showMenuButton?: boolean;
  title?: string;
  onBackClick?: () => void;
  onHomeClick?: () => void;
  onMenuClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({
  showBackButton = false,
  showHomeButton = false,
  showMenuButton = false,
  title = "מנהל שיבוץ עבודות",
  onBackClick,
  onHomeClick,
  onMenuClick
}) => {
  const navigate = useNavigate();

  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate(-1);
    }
  };

  const handleHomeClick = () => {
    if (onHomeClick) {
      onHomeClick();
    } else {
      navigate('/dashboard');
    }
  };

  const handleMenuClick = () => {
    if (onMenuClick) {
      onMenuClick();
    } else {
      navigate('/dashboard');
    }
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: 70,
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(51, 65, 85, 0.7) 100%)',
        backdropFilter: 'blur(15px)',
        WebkitBackdropFilter: 'blur(15px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 4,
        zIndex: 1200,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), 0 2px 8px rgba(0, 0, 0, 0.2)',
      }}
    >
      {/* Left side - Logo and Title */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
        {/* Logo */}
        <Box
          sx={{
            width: 45,
            height: 45,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4), 0 2px 8px rgba(139, 92, 246, 0.3)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Calendar/Schedule Icon */}
          <Box
            sx={{
              width: 24,
              height: 24,
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* Calendar base */}
            <Box
              sx={{
                width: 18,
                height: 16,
                border: '2px solid #fff',
                borderRadius: '3px 3px 6px 6px',
                position: 'relative',
              }}
            />
            {/* Calendar top */}
            <Box
              sx={{
                position: 'absolute',
                top: -3,
                left: 3,
                width: 14,
                height: 5,
                background: '#fff',
                borderRadius: '3px 3px 0 0',
              }}
            />
            {/* Calendar rings */}
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 2,
                width: 3,
                height: 3,
                background: '#6366f1',
                borderRadius: '50%',
              }}
            />
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                right: 2,
                width: 3,
                height: 3,
                background: '#6366f1',
                borderRadius: '50%',
              }}
            />
          </Box>
        </Box>
        {/* Title */}
        <Typography
          variant="h5"
          sx={{
            color: '#ffffff',
            fontWeight: 700,
            fontSize: 22,
            letterSpacing: 0.5,
            textAlign: 'right',
            textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
          }}
        >
          {title}
        </Typography>
      </Box>

      {/* Right side - Action Buttons */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {showBackButton && (
          <IconButton
            onClick={handleBackClick}
            sx={{
              color: '#ffffff',
              bgcolor: 'rgba(255,255,255,0.08)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255,255,255,0.1)',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.18)',
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 16px rgba(255,255,255,0.15)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            <ArrowBackIcon />
          </IconButton>
        )}
        {showHomeButton && (
          <IconButton
            onClick={handleHomeClick}
            sx={{
              color: '#ffffff',
              bgcolor: 'rgba(255,255,255,0.08)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255,255,255,0.1)',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.18)',
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 16px rgba(255,255,255,0.15)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            <HomeIcon />
          </IconButton>
        )}
        {showMenuButton && (
          <IconButton
            onClick={handleMenuClick}
            sx={{
              color: '#ffffff',
              bgcolor: 'rgba(255,255,255,0.08)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255,255,255,0.1)',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.18)',
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 16px rgba(255,255,255,0.15)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            <MenuIcon />
          </IconButton>
        )}
      </Box>
    </Box>
  );
};

export default Header; 