/**
 * CombinedPage.tsx
 * ---------------
 * Professional Hebrew RTL Combined Schedule page showing both X and Y task assignments.
 * NEW: Modernized with professional design, Hebrew RTL, dynamic task names 30/08/2025 13:30
 */
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Fab, 
  Snackbar, 
  Alert as MuiAlert,
  Paper,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import ShareIcon from '@mui/icons-material/Share';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import MailOutlineIcon from '@mui/icons-material/MailOutline';
import PhoneIcon from '@mui/icons-material/Phone';
import AssignmentIcon from '@mui/icons-material/Assignment';
import PageContainer from '../components/PageContainer';
import Header from '../components/Header';
import { fetchWithAuth, API_BASE_URL } from '../utils/api';
import { formatDateDMY } from '../components/utils';
import { getWorkerColor } from '../components/colors';
import { 
  PRIMARY_COLORS, 
  BACKGROUND_COLORS, 
  TEXT_COLORS, 
  TABLE_COLORS,
  CARD_COLORS,
  INTERACTIVE_COLORS 
} from '../components/colorSystem';
import { Schedule } from '../types';

interface CombinedData {
  row_labels: string[];
  dates: string[];
  grid: string[][];
  y_period?: {
    start: string;
    end: string;
    filename: string;
  };
}

const CombinedPage: React.FC = () => {
  const [availableSchedules, setAvailableSchedules] = useState<Schedule[]>([]);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);
  const [data, setData] = useState<CombinedData | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available Y schedule periods
  useEffect(() => {
    fetchWithAuth(`${API_BASE_URL}/api/y-tasks/list`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setAvailableSchedules(data.schedules || []);
        if (data.schedules?.length > 0) setSelectedSchedule(data.schedules[0]);
      })
      .catch(() => setError('טעינת לוחות הזמנים נכשלה'));
  }, []);

  // Load combined grid when a schedule is selected
  useEffect(() => {
    if (!selectedSchedule) return;
    setLoading(true);
    setError(null);
    fetchWithAuth(`${API_BASE_URL}/api/combined/by-range?start=${encodeURIComponent(selectedSchedule.start)}&end=${encodeURIComponent(selectedSchedule.end)}`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(() => { 
        setError('טעינת לוח זמנים משולב נכשלה'); 
        setLoading(false); 
      });
  }, [selectedSchedule]);

  const handleSave = async () => {
    if (!selectedSchedule || !data) return;
    setSaving(true);
    try {
      // Create CSV content
      let csv = 'משימה,' + data.dates.join(',') + '\n';
      for (let i = 0; i < data.row_labels.length; i++) {
        const row = [data.row_labels[i], ...data.grid[i].map(cell => cell || '-')];
        csv += row.join(',') + '\n';
      }
      const filename = `combined_${selectedSchedule.start.replace(/\//g, '-')}_${selectedSchedule.end.replace(/\//g, '-')}.csv`;
      const res = await fetchWithAuth(`${API_BASE_URL}/api/combined/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ csv, filename }),
      });
      if (!res.ok) throw new Error('שמירה נכשלה');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      setError(e.message || 'שמירת לוח זמנים משולב נכשלה');
    } finally {
      setSaving(false);
    }
  };

  // NEW: Dummy action handlers 30/08/2025 13:30
  const handleWhatsAppShare = () => {
    // Placeholder for WhatsApp sharing
    alert('שיתוף ב-WhatsApp יבוא בקרוב');
  };

  const handleEmailShare = () => {
    // Placeholder for email sharing
    alert('שליחה במייל תבוא בקרוב');
  };

  const handleBrowserSave = () => {
    if (!data || !selectedSchedule) return;
    
    // Create CSV content for download
    let csv = 'משימה,' + data.dates.join(',') + '\n';
    for (let i = 0; i < data.row_labels.length; i++) {
      const row = [data.row_labels[i], ...data.grid[i].map(cell => cell || '-')];
      csv += row.join(',') + '\n';
    }
    
    // Create and trigger download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `לוח_משולב_${selectedSchedule.start.replace(/\//g, '-')}_${selectedSchedule.end.replace(/\//g, '-')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <PageContainer>
      <Header 
        darkMode={true}
        onToggleDarkMode={() => {}}
        showBackButton={true}
        showHomeButton={true}
        title="לוח זמנים משולב"
      />
      
      {/* NEW: Professional main container with improved design 30/08/2025 13:30 */}
      <Box sx={{ 
        direction: 'rtl',
        mt: 3,
        minHeight: 'calc(100vh - 200px)'
      }}>
        
        {/* Page Title */}
        <Typography 
          variant="h3" 
          sx={{ 
            mb: 4, 
            fontWeight: 700, 
            color: TEXT_COLORS.text_primary,
            textAlign: 'center',
            fontSize: { xs: '1.8rem', sm: '2.2rem', md: '2.5rem' }
          }}
        >
          לוח זמנים משולב - משימות X ו-Y
        </Typography>
        
        {/* Schedule Selection */}
        <Paper sx={{ 
          p: 3, 
          mb: 3,
          backgroundColor: CARD_COLORS.card_background,
          border: `1px solid ${CARD_COLORS.card_border}`,
          borderRadius: 3
        }}>
          <Typography 
            variant="h5" 
            sx={{ 
              mb: 3, 
              fontWeight: 600, 
              color: TEXT_COLORS.text_primary,
              textAlign: 'center',
              direction: 'rtl'
            }}
          >
            בחירת תקופת לוח זמנים
          </Typography>
          
          <Box sx={{ 
            display: 'flex', 
            gap: 2, 
            flexWrap: 'wrap', 
            justifyContent: 'center',
            direction: 'rtl'
          }}>
            {availableSchedules.map((sch: Schedule) => (
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
                  direction: 'rtl',
                  backgroundColor: selectedSchedule && sch.filename === selectedSchedule.filename 
                    ? PRIMARY_COLORS.primary_main 
                    : 'transparent',
                  borderColor: INTERACTIVE_COLORS.button_border,
                  color: selectedSchedule && sch.filename === selectedSchedule.filename 
                    ? TEXT_COLORS.text_primary 
                    : TEXT_COLORS.text_secondary,
                  boxShadow: selectedSchedule && sch.filename === selectedSchedule.filename 
                    ? `0 4px 20px ${PRIMARY_COLORS.primary_main}40` 
                    : '0 2px 8px rgba(0,0,0,0.2)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 6px 25px rgba(0,0,0,0.3)',
                    borderColor: INTERACTIVE_COLORS.button_border_hover
                  }
                }}
              >
                {formatDateDMY(sch.start)} עד {formatDateDMY(sch.end)}
              </Button>
            ))}
          </Box>
        </Paper>

        {/* NEW: Action Buttons Section 30/08/2025 13:30 */}
        {data && data.grid.length > 0 && (
          <Paper sx={{ 
            p: 3, 
            mb: 3,
            backgroundColor: CARD_COLORS.card_background,
            border: `1px solid ${CARD_COLORS.card_border}`,
            borderRadius: 3
          }}>
            <Typography 
              variant="h6" 
              sx={{ 
                mb: 2, 
                fontWeight: 600, 
                color: TEXT_COLORS.text_primary,
                textAlign: 'center',
                direction: 'rtl'
              }}
            >
              פעולות על הלוח
            </Typography>
            
            <Box sx={{ 
              display: 'flex', 
              gap: 2, 
              justifyContent: 'center',
              flexWrap: 'wrap',
              direction: 'rtl'
            }}>
              {/* Save Button */}
              <Tooltip title="שמירה במערכת">
                <Fab
                  color="primary"
                  onClick={handleSave}
                  disabled={saving || !selectedSchedule}
                  sx={{ 
                    width: 60, 
                    height: 60,
                    backgroundColor: PRIMARY_COLORS.primary_main,
                    '&:hover': {
                      backgroundColor: PRIMARY_COLORS.primary_darker,
                      transform: 'scale(1.05)'
                    }
                  }}
                >
                  <SaveIcon sx={{ fontSize: 24 }} />
                </Fab>
              </Tooltip>

              {/* WhatsApp Share */}
              <Tooltip title="שיתוף ב-WhatsApp">
                <Fab
                  onClick={handleWhatsAppShare}
                  sx={{ 
                    width: 60, 
                    height: 60,
                    backgroundColor: '#25D366',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: '#128C7E',
                      transform: 'scale(1.05)'
                    }
                  }}
                >
                  <PhoneIcon sx={{ fontSize: 24 }} />
                </Fab>
              </Tooltip>

              {/* Email Share */}
              <Tooltip title="שליחה במייל">
                <Fab
                  onClick={handleEmailShare}
                  sx={{ 
                    width: 60, 
                    height: 60,
                    backgroundColor: '#ea4335',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: '#d93025',
                      transform: 'scale(1.05)'
                    }
                  }}
                >
                  <MailOutlineIcon sx={{ fontSize: 24 }} />
                </Fab>
              </Tooltip>

              {/* Browser Save/Download */}
              <Tooltip title="הורדה לקובץ">
                <Fab
                  onClick={handleBrowserSave}
                  sx={{ 
                    width: 60, 
                    height: 60,
                    backgroundColor: '#1976d2',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: '#1565c0',
                      transform: 'scale(1.05)'
                    }
                  }}
                >
                  <FileDownloadIcon sx={{ fontSize: 24 }} />
                </Fab>
              </Tooltip>
            </Box>
          </Paper>
        )}

        {/* Loading State */}
        {loading && (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            py: 8,
            direction: 'rtl'
          }}>
            <Typography variant="h6" sx={{ color: TEXT_COLORS.text_secondary }}>
              טוען לוח זמנים משולב...
            </Typography>
          </Box>
        )}

        {/* Error State */}
        {error && (
          <MuiAlert 
            severity="error" 
            onClose={() => setError(null)}
            sx={{ 
              mb: 3,
              direction: 'rtl',
              '& .MuiAlert-message': {
                textAlign: 'right'
              }
            }}
          >
            {error}
          </MuiAlert>
        )}

        {/* NEW: Professional Combined Schedule Table 30/08/2025 13:30 */}
        {!loading && !error && data && data.grid.length > 0 && (
          <Paper sx={{ 
            borderRadius: 3,
            overflow: 'hidden',
            backgroundColor: TABLE_COLORS.table_background,
            border: `1px solid ${TABLE_COLORS.table_border}`,
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
          }}>
            <Box sx={{ 
              overflowX: 'auto',
              direction: 'rtl'
            }}>
              <Box 
                component="table" 
                sx={{ 
                  minWidth: data.dates.length > 0 ? Math.max(900, 200 + data.dates.length * 140) : 900, 
                  width: '100%', 
                  borderCollapse: 'separate', 
                  borderSpacing: 0,
                  direction: 'rtl'
                }}
              >
                <thead>
                  <tr>
                    {/* Header: Dates (RTL order) */}
                    {data.dates.slice().reverse().map((date, i) => (
                      <th 
                        key={i} 
                        style={{ 
                          minWidth: 140, 
                          background: TABLE_COLORS.header_background,
                          color: TEXT_COLORS.text_primary, 
                          fontWeight: 700, 
                          fontSize: '0.9rem', 
                          borderBottom: `3px solid ${PRIMARY_COLORS.primary_main}`, 
                          height: 60, 
                          borderLeft: `1px solid ${TABLE_COLORS.table_border}`,
                          padding: '12px',
                          textAlign: 'center',
                          verticalAlign: 'middle'
                        }}
                      >
                        {formatDateDMY(date)}
                      </th>
                    ))}
                    
                    {/* Header: Task column (rightmost in RTL) */}
                    <th 
                      style={{ 
                        minWidth: 200, 
                        background: TABLE_COLORS.header_background,
                        color: TEXT_COLORS.text_primary, 
                        fontWeight: 700, 
                        fontSize: '1.1rem', 
                        position: 'sticky', 
                        right: 0, 
                        zIndex: 2, 
                        borderBottom: `3px solid ${PRIMARY_COLORS.primary_main}`, 
                        borderLeft: `2px solid ${TABLE_COLORS.table_border}`, 
                        height: 60, 
                        padding: '16px',
                        textAlign: 'center',
                        verticalAlign: 'middle'
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                        <AssignmentIcon sx={{ fontSize: 20 }} />
                        <span>משימה</span>
                      </Box>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.row_labels.map((task, rIdx) => (
                    <tr 
                      key={rIdx} 
                      style={{ 
                        background: rIdx % 2 === 0 
                          ? TABLE_COLORS.row_even 
                          : TABLE_COLORS.row_odd 
                      }}
                    >
                      {/* Data cells (RTL order) */}
                      {data.grid[rIdx]?.slice().reverse().map((soldier: string, cIdx: number) => (
                        <td 
                          key={cIdx} 
                          style={{ 
                            background: soldier 
                              ? getWorkerColor(soldier, true) 
                              : 'transparent', 
                            color: TEXT_COLORS.text_primary, 
                            textAlign: 'center', 
                            fontWeight: 600, 
                            minWidth: 140, 
                            borderLeft: `1px solid ${TABLE_COLORS.table_border}`, 
                            borderBottom: `1px solid ${TABLE_COLORS.table_border}`,
                            fontSize: '0.9rem', 
                            height: 50, 
                            boxSizing: 'border-box', 
                            transition: 'all 0.2s ease', 
                            opacity: soldier ? 1 : 0.6, 
                            padding: '8px',
                            verticalAlign: 'middle',
                            position: 'relative'
                          }}
                        >
                          {soldier && (
                            <Box sx={{
                              backgroundColor: 'rgba(0,0,0,0.1)',
                              borderRadius: 2,
                              padding: '4px 8px',
                              fontSize: '0.85rem',
                              fontWeight: 700,
                              textAlign: 'center'
                            }}>
                              {soldier}
                            </Box>
                          )}
                        </td>
                      ))}
                      
                      {/* Task name column (rightmost in RTL) */}
                      <td 
                        style={{ 
                          background: TABLE_COLORS.header_background,
                          color: TEXT_COLORS.text_primary, 
                          fontWeight: 700, 
                          position: 'sticky', 
                          right: 0, 
                          zIndex: 1, 
                          fontSize: '1rem', 
                          borderLeft: `2px solid ${TABLE_COLORS.table_border}`, 
                          borderBottom: `1px solid ${TABLE_COLORS.table_border}`, 
                          height: 50, 
                          paddingRight: 20, 
                          paddingLeft: 16, 
                          minWidth: 200, 
                          textAlign: 'right',
                          verticalAlign: 'middle'
                        }}
                      >
                        <Box sx={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'flex-end',
                          gap: 1
                        }}>
                          <span>{task}</span>
                          <Box sx={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: PRIMARY_COLORS.primary_main,
                            opacity: 0.7
                          }} />
                        </Box>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Box>
            </Box>
          </Paper>
        )}

        {/* Empty State */}
        {!loading && !error && (!data || data.grid.length === 0) && (
          <Paper sx={{ 
            p: 6, 
            textAlign: 'center',
            backgroundColor: CARD_COLORS.card_background,
            border: `1px solid ${CARD_COLORS.card_border}`,
            borderRadius: 3
          }}>
            <Typography 
              variant="h6" 
              sx={{ 
                color: TEXT_COLORS.text_secondary,
                direction: 'rtl'
              }}
            >
              לא נמצא לוח זמנים לתקופה הנבחרת
            </Typography>
          </Paper>
        )}
      </Box>

      {/* Success Snackbar */}
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
            fontWeight: 600,
            direction: 'rtl',
            '& .MuiAlert-message': {
              textAlign: 'right'
            }
          }}
        >
          לוח זמנים משולב נשמר בהצלחה!
        </MuiAlert>
      </Snackbar>
    </PageContainer>
  );
};

export default CombinedPage;