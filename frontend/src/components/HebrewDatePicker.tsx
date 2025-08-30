import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  IconButton, 
  Paper,
  Grid,
  Button
} from '@mui/material';
import { 
  ChevronRight as ChevronLeftIcon, 
  ChevronLeft as ChevronRightIcon 
} from '@mui/icons-material';

interface HebrewDatePickerProps {
  value: Date | null;
  onChange: (date: Date | null) => void;
  label?: string;
  disabled?: boolean;
}

const HebrewDatePicker: React.FC<HebrewDatePickerProps> = ({ 
  value, 
  onChange, 
  label = "בחר תאריך",
  disabled = false 
}) => {
  const [currentDate, setCurrentDate] = useState(value || new Date());
  
  const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();
  
  // Hebrew day names (Sunday = 0)
  const hebrewDays = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
  
  const handleDateClick = (day: number) => {
    const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    onChange(newDate);
  };
  
  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };
  
  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };
  
  const isSelected = (day: number) => {
    if (!value) return false;
    return value.getDate() === day && 
           value.getMonth() === currentDate.getMonth() && 
           value.getFullYear() === currentDate.getFullYear();
  };
  
  const isToday = (day: number) => {
    const today = new Date();
    return today.getDate() === day && 
           today.getMonth() === currentDate.getMonth() && 
           today.getFullYear() === currentDate.getFullYear();
  };
  
  const renderCalendarDays = () => {
    const days = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(<Box key={`empty-${i}`} sx={{ width: 40, height: 40 }} />);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(
        <Button
          key={day}
          onClick={() => handleDateClick(day)}
          disabled={disabled}
          sx={{
            minWidth: 40,
            height: 40,
            p: 0,
            bgcolor: isSelected(day) ? '#1976d2' : 'transparent',
            color: isSelected(day) ? '#fff' : (isToday(day) ? '#1976d2' : 'rgba(255,255,255,0.8)'),
            border: isToday(day) ? '2px solid #1976d2' : 'none',
            borderRadius: '50%',
            '&:hover': {
              bgcolor: isSelected(day) ? '#1565c0' : 'rgba(255,255,255,0.1)',
            },
            fontWeight: isToday(day) ? 'bold' : 'normal',
          }}
        >
          {day}
        </Button>
      );
    }
    
    return days;
  };
  
  return (
    <Paper 
      elevation={8} 
      sx={{ 
        p: 2, 
        bgcolor: '#1a1a1a',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 2,
        direction: 'rtl'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <IconButton 
          onClick={goToPreviousMonth}
          disabled={disabled}
          sx={{ color: 'rgba(255,255,255,0.7)' }}
        >
          <ChevronLeftIcon />
        </IconButton>
        
        <Typography 
          variant="h6" 
          sx={{ 
            color: '#fff', 
            fontWeight: 600,
            textAlign: 'center'
          }}
        >
          {currentDate.toLocaleDateString('he-IL', { 
            year: 'numeric', 
            month: 'long' 
          })}
        </Typography>
        
        <IconButton 
          onClick={goToNextMonth}
          disabled={disabled}
          sx={{ color: 'rgba(255,255,255,0.7)' }}
        >
          <ChevronRightIcon />
        </IconButton>
      </Box>
      
      {/* Day headers */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 0.5, mb: 1 }}>
        {hebrewDays.map((day, index) => (
          <Box key={index}>
            <Typography 
              variant="caption" 
              sx={{ 
                display: 'block', 
                textAlign: 'center', 
                color: 'rgba(255,255,255,0.6)',
                fontWeight: 600,
                fontSize: '0.75rem'
              }}
            >
              {day.charAt(0)}
            </Typography>
          </Box>
        ))}
      </Box>
      
      {/* Calendar grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 0.5 }}>
        {renderCalendarDays().map((day, index) => (
          <Box key={index}>
            {day}
          </Box>
        ))}
      </Box>
      
      {label && (
        <Typography 
          variant="caption" 
          sx={{ 
            display: 'block', 
            textAlign: 'center', 
            mt: 1, 
            color: 'rgba(255,255,255,0.5)' 
          }}
        >
          {label}
        </Typography>
      )}
    </Paper>
  );
};

export default HebrewDatePicker;
