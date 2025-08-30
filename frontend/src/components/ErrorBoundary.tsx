import React, { Component, ReactNode } from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { PRIMARY_COLORS, TEXT_COLORS, BACKGROUND_COLORS } from './colorSystem';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Paper 
          sx={{ 
            p: 4, 
            m: 2, 
            textAlign: 'center',
            backgroundColor: BACKGROUND_COLORS.bg_secondary,
            borderRadius: 2,
            border: `1px solid ${PRIMARY_COLORS.primary_main}`
          }}
        >
          <Typography 
            variant="h5" 
            sx={{ 
              mb: 2, 
              color: TEXT_COLORS.text_primary,
              fontWeight: 600 
            }}
          >
            שגיאה במערכת
          </Typography>
          <Typography 
            variant="body1" 
            sx={{ 
              mb: 3, 
              color: TEXT_COLORS.text_secondary,
              direction: 'rtl' 
            }}
          >
            אירעה שגיאה לא צפויה. אנא נסה לרענן את הדף או חזור לתפריט הראשי.
          </Typography>
          {this.state.error && (
            <Typography 
              variant="body2" 
              sx={{ 
                mb: 3, 
                color: TEXT_COLORS.text_secondary, 
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                backgroundColor: 'rgba(0,0,0,0.2)',
                p: 2,
                borderRadius: 1
              }}
            >
              {this.state.error.message}
            </Typography>
          )}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={this.handleReset}
              sx={{ direction: 'rtl' }}
            >
              נסה שוב
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => window.location.href = '/'}
              sx={{ direction: 'rtl' }}
            >
              תפריט ראשי
            </Button>
          </Box>
        </Paper>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;