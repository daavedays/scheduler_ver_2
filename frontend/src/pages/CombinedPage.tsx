import React from 'react';
import { Box, Typography, Button, Snackbar, Fab } from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import SaveIcon from '@mui/icons-material/Save';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import MailOutlineIcon from '@mui/icons-material/MailOutline';
import PhoneIcon from '@mui/icons-material/Phone';
import { formatDateDMY } from '../components/utils';
import Header from '../components/Header';
import { fetchWithAuth, API_BASE_URL } from '../utils/api';

export default function CombinedPage() {
  const [availableSchedules, setAvailableSchedules] = React.useState<any[]>([]);
  const [selectedSchedule, setSelectedSchedule] = React.useState<any | null>(null);
  const [rowLabels, setRowLabels] = React.useState<string[]>([]);
  const [dates, setDates] = React.useState<string[]>([]);
  const [grid, setGrid] = React.useState<string[][]>([]);
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [saveSuccess, setSaveSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  
  // Task filtering and table size state
  const [showAllTasks, setShowAllTasks] = React.useState(true);
  const [showYTasks, setShowYTasks] = React.useState(false);
  const [showXTasks, setShowXTasks] = React.useState(false);
  const [tableSize, setTableSize] = React.useState<'small' | 'medium' | 'large'>('medium');
  const [y_task_names, setYTaskNames] = React.useState<string[]>([]);

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
        
        // Extract Y task names for filtering (kept as-is)
        const yTasks = data.row_labels?.slice(0, 6) || []; 
        setYTaskNames(yTasks);
        
        setLoading(false);
      })
      .catch(() => { setError('Failed to load combined schedule'); setLoading(false); });
  }, [selectedSchedule]);

  const handleSave = async () => {
    if (!selectedSchedule) return;
    setSaving(true);
    try {
      let csv = 'משימה,' + dates.join(',') + '\n';
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
      if (!res.ok) throw new Error('שמירה נכשלה');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      setError(e.message || 'שמירת לוח זמנים משולב נכשלה');
    } finally {
      setSaving(false);
    }
  };

  const handleWhatsAppShare = () => {
    alert('שיתוף ב-WhatsApp יבוא בקרוב');
  };

  const handleEmailShare = () => {
    alert('שליחה במייל תבוא בקרוב');
  };

  const handleBrowserSave = () => {
    if (!selectedSchedule) return;
    let csv = 'משימה,' + dates.join(',') + '\n';
    for (let i = 0; i < rowLabels.length; i++) {
      const row = [rowLabels[i], ...grid[i].map(cell => cell || '-')];
      csv += row.join(',') + '\n';
    }
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

  // ====== STYLE TOKENS ======
  const tokens = {
    bg: 'linear-gradient(135deg, #0c1530 0%, #0f1e3d 40%, #12264d 100%)',
    panel: 'rgba(17, 24, 39, 0.7)',
    panelBorder: 'rgba(148, 163, 184, 0.2)',
    glow: '0 20px 40px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.04)',
    accent: '#8b5cf6',
    accentSoft: '#a78bfa',
    accentDeep: '#7c3aed',
    textPrimary: '#e5e7eb',
    textSecondary: '#cbd5e1',
    tableOdd: '#1f2a44',
    tableEven: '#1a2440',
    tableHover: '#283454',
    weekend: '#2a1b3f',
    weekendHover: '#342052',
    chipBg: '#f8fafc',
    chipBorder: '#cbd5e1',
    stickyShadow: '2px 0 12px rgba(0,0,0,.35)',
  };

  const cellHeights = {
    small: { header: 52, row: 44, chip: 26 },
    medium: { header: 64, row: 56, chip: 30 },
    large: { header: 72, row: 64, chip: 34 },
  }[tableSize];

  return (
    <Box sx={{ 
      minHeight: '100vh',
      position: 'relative',
      overflowX: 'hidden',
      // Dark blue background + subtle decorative lights
      background: tokens.bg,
      '&::before': {
        content: '""',
        position: 'absolute',
        inset: 0,
        backgroundImage: `
          radial-gradient(1200px 600px at 110% -10%, rgba(139, 92, 246, .10) 0%, transparent 60%),
          radial-gradient(900px 500px at -10% 110%, rgba(56, 189, 248, .08) 0%, transparent 60%),
          radial-gradient(800px 400px at 50% 10%, rgba(255,255,255,.06) 0%, transparent 55%)
        `,
        pointerEvents: 'none',
        zIndex: 0
      }
    }}>
      <Box sx={{ position: 'relative', zIndex: 1, p: { xs: 2, md: 4 }, pt: 12 }}>
        <Header 
          showBackButton={true}
          showHomeButton={true}
          title="לוח זמנים משולב"
        />

        {/* TITLE */}
        <Box sx={{ maxWidth: 1400, mx: 'auto', textAlign: 'center', direction: 'rtl', mb: 3 }}>
          <Typography 
            variant="h3" 
            sx={{ 
              fontWeight: 900, 
              letterSpacing: '.5px',
              color: tokens.textPrimary,
              textShadow: '0 2px 16px rgba(124,58,237,.35)',
              fontSize: { xs: '1.9rem', sm: '2.4rem', md: '2.8rem' }
            }}
          >
            לוח זמנים משולב — משימות X / Y
          </Typography>
          <Typography variant="body1" sx={{ color: tokens.textSecondary, opacity: .9, mt: .5 }}>
            תצוגה מרוכזת, נקייה וחדה. קל לסריקה. קל לשיתוף.
          </Typography>
        </Box>

        {/* MAIN PANEL */}
        <Box sx={{
          maxWidth: 1400,
          mx: 'auto',
          bgcolor: tokens.panel,
          border: `1px solid ${tokens.panelBorder}`,
          borderRadius: 4,
          boxShadow: tokens.glow,
          backdropFilter: 'blur(10px)',
          overflow: 'hidden',
          direction: 'rtl'
        }}>
          {/* SCHEDULE PICKER */}
          <Box sx={{ 
            p: { xs: 2.5, md: 3 },
            borderBottom: `1px solid ${tokens.panelBorder}`,
            background: 'linear-gradient(180deg, rgba(148,163,184,.10), rgba(148,163,184,0))'
          }}>
            <Typography variant="h6" sx={{ 
              color: tokens.textPrimary, 
              fontWeight: 800, 
              mb: 2 
            }}>
              בחירת תקופת לוח זמנים
            </Typography>
            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
              {availableSchedules.map((sch: any) => {
                const active = selectedSchedule && sch.filename === selectedSchedule.filename;
                return (
                  <Button
                    key={sch.filename}
                    onClick={() => setSelectedSchedule(sch)}
                    variant={active ? 'contained' : 'outlined'}
                    sx={{
                      borderRadius: 999,
                      textTransform: 'none',
                      fontWeight: 700,
                      px: 2.2,
                      py: 1.1,
                      minHeight: 40,
                      backdropFilter: 'blur(4px)',
                      transition: 'all .2s ease',
                      ...(active
                        ? {
                            backgroundColor: tokens.accent,
                            borderColor: tokens.accent,
                            boxShadow: '0 8px 24px rgba(139,92,246,.35)',
                            '&:hover': { backgroundColor: tokens.accentDeep, transform: 'translateY(-1px)' }
                          }
                        : {
                            color: tokens.textSecondary,
                            borderColor: 'rgba(167,139,250,.4)',
                            '&:hover': { borderColor: tokens.accentSoft, backgroundColor: 'rgba(167,139,250,.08)' }
                          })
                    }}
                  >
                    {formatDateDMY(sch.start)} — {formatDateDMY(sch.end)}
                  </Button>
                );
              })}
            </Box>
          </Box>



          {/* ACTIONS */}
          {!loading && !error && grid.length > 0 && (
            <Box sx={{ 
              p: { xs: 2.5, md: 3 },
              borderBottom: `1px solid ${tokens.panelBorder}`,
              background: 'linear-gradient(180deg, rgba(124,58,237,.10), rgba(124,58,237,0))'
            }}>
              <Typography variant="h6" sx={{ color: tokens.textPrimary, fontWeight: 800, mb: 2, textAlign: 'center' }}>
                פעולות על הלוח
              </Typography>
              <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Fab
                    color="primary"
                    onClick={handleSave}
                    disabled={saving || !selectedSchedule}
                    sx={{
                      width: 64, height: 64,
                      boxShadow: '0 12px 28px rgba(139,92,246,.45)',
                      background: `linear-gradient(180deg, ${tokens.accent}, ${tokens.accentDeep})`,
                      '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 16px 36px rgba(139,92,246,.60)' },
                      transition: 'all .2s ease'
                    }}
                  >
                    <SaveIcon sx={{ fontSize: 26 }} />
                  </Fab>
                  <Typography variant="caption" sx={{ color: tokens.textSecondary, display: 'block', mt: 1, fontWeight: 700 }}>
                    שמירה
                  </Typography>
                </Box>

                <Box sx={{ textAlign: 'center' }}>
                  <Fab
                    onClick={handleWhatsAppShare}
                    sx={{
                      width: 64, height: 64,
                      backgroundColor: '#25D366', color: '#fff',
                      boxShadow: '0 12px 28px rgba(37,211,102,.35)',
                      '&:hover': { backgroundColor: '#128C7E', transform: 'translateY(-2px)' },
                      transition: 'all .2s ease'
                    }}
                  >
                    <PhoneIcon sx={{ fontSize: 26 }} />
                  </Fab>
                  <Typography variant="caption" sx={{ color: tokens.textSecondary, display: 'block', mt: 1, fontWeight: 700 }}>
                    WhatsApp
                  </Typography>
                </Box>

                <Box sx={{ textAlign: 'center' }}>
                  <Fab
                    onClick={handleEmailShare}
                    sx={{
                      width: 64, height: 64,
                      backgroundColor: '#ea4335', color: '#fff',
                      boxShadow: '0 12px 28px rgba(234,67,53,.35)',
                      '&:hover': { backgroundColor: '#d93025', transform: 'translateY(-2px)' },
                      transition: 'all .2s ease'
                    }}
                  >
                    <MailOutlineIcon sx={{ fontSize: 26 }} />
                  </Fab>
                  <Typography variant="caption" sx={{ color: tokens.textSecondary, display: 'block', mt: 1, fontWeight: 700 }}>
                    מייל
                  </Typography>
                </Box>

                <Box sx={{ textAlign: 'center' }}>
                  <Fab
                    onClick={handleBrowserSave}
                    sx={{
                      width: 64, height: 64,
                      backgroundColor: tokens.accent, color: '#fff',
                      boxShadow: '0 12px 28px rgba(139,92,246,.45)',
                      '&:hover': { backgroundColor: tokens.accentDeep, transform: 'translateY(-2px)' },
                      transition: 'all .2s ease'
                    }}
                  >
                    <FileDownloadIcon sx={{ fontSize: 26 }} />
                  </Fab>
                  <Typography variant="caption" sx={{ color: tokens.textSecondary, display: 'block', mt: 1, fontWeight: 700 }}>
                    הורדה
                  </Typography>
                </Box>
              </Box>
            </Box>
          )}

          {/* LOADING */}
          {loading && (
            <Box sx={{ py: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="h6" sx={{ color: tokens.textSecondary }}>
                טוען לוח זמנים משולב...
              </Typography>
            </Box>
          )}

          {/* ERROR */}
          {error && (
            <Box sx={{ 
              p: 3, textAlign: 'center',
              background: 'linear-gradient(180deg, rgba(239,68,68,.12), rgba(239,68,68,.06))',
              borderTop: `1px solid ${tokens.panelBorder}`
            }}>
              <Typography color="error" variant="h6">
                {error}
              </Typography>
            </Box>
          )}

          {/* EMPTY STATES */}
          {!loading && !error && (!availableSchedules || availableSchedules.length === 0) && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" sx={{ color: tokens.textPrimary, mb: 1.5 }}>אין לוחות זמנים זמינים</Typography>
              <Typography variant="body2" sx={{ color: tokens.textSecondary }}>
                אנא צור לוח זמנים חדש בעמוד משימות Y
              </Typography>
            </Box>
          )}

          {!loading && !error && availableSchedules.length > 0 && grid.length === 0 && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" sx={{ color: tokens.textPrimary, mb: 1.5 }}>אין נתונים בלוח הזמנים הנבחר</Typography>
              <Typography variant="body2" sx={{ color: tokens.textSecondary }}>
                בחר תקופה אחרת או צור לוח זמנים חדש
              </Typography>
            </Box>
          )}
          {/* CONTROLS */}
          {!loading && !error && grid.length > 0 && (
            <Box sx={{
              p: { xs: 2.5, md: 3 },
              display: 'flex',
              gap: 2,
              rowGap: 2.5,
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: `1px solid ${tokens.panelBorder}`,
              background: 'linear-gradient(180deg, rgba(167,139,250,.08), rgba(167,139,250,0))'
            }}>
              {/* Filters */}
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <Typography sx={{ color: tokens.textSecondary, fontWeight: 800, mr: 1 }}>סינון</Typography>
                <Button
                  variant={showAllTasks ? 'contained' : 'outlined'}
                  onClick={() => setShowAllTasks(true)}
                  sx={{
                    borderRadius: 999,
                    textTransform: 'none',
                    fontWeight: 700,
                    px: 2,
                    ...(showAllTasks
                      ? { backgroundColor: tokens.accent, borderColor: tokens.accent, color: '#fff' }
                      : { color: tokens.accentSoft, borderColor: tokens.accentSoft, '&:hover': { backgroundColor: 'rgba(167,139,250,.08)' } })
                  }}
                >
                  כל המשימות
                </Button>
                <Button
                  variant={!showAllTasks && showYTasks ? 'contained' : 'outlined'}
                  onClick={() => { setShowAllTasks(false); setShowYTasks(true); setShowXTasks(false); }}
                  sx={{
                    borderRadius: 999,
                    textTransform: 'none',
                    fontWeight: 700,
                    px: 2,
                    ...(!showAllTasks && showYTasks
                      ? { backgroundColor: tokens.accent, borderColor: tokens.accent, color: '#fff' }
                      : { color: tokens.accentSoft, borderColor: tokens.accentSoft, '&:hover': { backgroundColor: 'rgba(167,139,250,.08)' } })
                  }}
                >
                  משימות Y
                </Button>
                <Button
                  variant={!showAllTasks && !showYTasks && showXTasks ? 'contained' : 'outlined'}
                  onClick={() => { setShowAllTasks(false); setShowYTasks(false); setShowXTasks(true); }}
                  sx={{
                    borderRadius: 999,
                    textTransform: 'none',
                    fontWeight: 700,
                    px: 2,
                    ...(!showAllTasks && !showYTasks && showXTasks
                      ? { backgroundColor: tokens.accent, borderColor: tokens.accent, color: '#fff' }
                      : { color: tokens.accentSoft, borderColor: tokens.accentSoft, '&:hover': { backgroundColor: 'rgba(167,139,250,.08)' } })
                  }}
                >
                  משימות X
                </Button>
              </Box>

              {/* Size */}
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <Typography sx={{ color: tokens.textSecondary, fontWeight: 800, mr: 1 }}>גודל</Typography>
                <Button
                  size="small"
                  variant={tableSize === 'small' ? 'contained' : 'outlined'}
                  onClick={() => setTableSize('small')}
                  sx={{
                    borderRadius: 999, textTransform: 'none', fontWeight: 800, px: 1.8,
                    ...(tableSize === 'small'
                      ? { backgroundColor: tokens.accent, borderColor: tokens.accent, color: '#fff' }
                      : { color: tokens.accentSoft, borderColor: tokens.accentSoft })
                  }}
                >
                  קטן
                </Button>
                <Button
                  size="small"
                  variant={tableSize === 'medium' ? 'contained' : 'outlined'}
                  onClick={() => setTableSize('medium')}
                  sx={{
                    borderRadius: 999, textTransform: 'none', fontWeight: 800, px: 1.8,
                    ...(tableSize === 'medium'
                      ? { backgroundColor: tokens.accent, borderColor: tokens.accent, color: '#fff' }
                      : { color: tokens.accentSoft, borderColor: tokens.accentSoft })
                  }}
                >
                  בינוני
                </Button>
                <Button
                  size="small"
                  variant={tableSize === 'large' ? 'contained' : 'outlined'}
                  onClick={() => setTableSize('large')}
                  sx={{
                    borderRadius: 999, textTransform: 'none', fontWeight: 800, px: 1.8,
                    ...(tableSize === 'large'
                      ? { backgroundColor: tokens.accent, borderColor: tokens.accent, color: '#fff' }
                      : { color: tokens.accentSoft, borderColor: tokens.accentSoft })
                  }}
                >
                  גדול
                </Button>
              </Box>
            </Box>
          )}
          {/* TABLE */}
          {!loading && !error && grid.length > 0 && (
            <Box
              sx={{
                position: 'relative',
                borderTop: `1px solid ${tokens.panelBorder}`,
                // Scroll container
                overflow: 'auto',
                WebkitOverflowScrolling: 'touch',
                // Edge masks for polish
                maskImage: {
                  xs: 'linear-gradient(to left, transparent, black 24px, black calc(100% - 24px), transparent)',
                  md: 'linear-gradient(to left, transparent, black 36px, black calc(100% - 36px), transparent)'
                } as any,
              }}
            >
              {/* scroll shadows */}
              <Box sx={{
                position: 'fixed', top: 0, left: 0, right: 0, height: 0, zIndex: 20,
                '&::before, &::after': {
                  content: '""', position: 'absolute', top: 0, height: '100%',
                  width: 36, pointerEvents: 'none'
                },
                '&::before': { right: 0, background: 'linear-gradient(270deg, rgba(0,0,0,.35), rgba(0,0,0,0))' },
                '&::after': { left: 0, background: 'linear-gradient(90deg, rgba(0,0,0,.35), rgba(0,0,0,0))' }
              }} />

              <Box
                component="table"
                sx={{
                  minWidth: dates.length > 0 ? Math.max(900, 220 + dates.length * 140) : 900,
                  width: '100%',
                  borderCollapse: 'separate',
                  borderSpacing: 0,
                  direction: 'rtl',
                  backgroundColor: '#0f172a'
                }}
              >
                <thead>
                  <tr>
                    {/* Sticky task header */}
                    <th
                      style={{
                        width: 260,
                        position: 'sticky',
                        right: 0,
                        zIndex: 12,
                        background: `linear-gradient(180deg, ${tokens.accent}, ${tokens.accentDeep})`,
                        color: '#fff',
                        fontWeight: 900,
                        fontSize: '1.05rem',
                        borderLeft: `1px solid ${tokens.panelBorder}`,
                        borderBottom: `1px solid ${tokens.panelBorder}`,
                        height: cellHeights.header,
                        padding: '14px 18px',
                        textAlign: 'right',
                        boxShadow: tokens.stickyShadow,
                        transform: 'translateZ(0)',
                        willChange: 'transform',  
                        backfaceVisibility: 'hidden'
                      } as React.CSSProperties}
                    >
                      משימה
                    </th>

                    {dates.map((date, i) => {
                      const [day, month, year] = date.split('/');
                      const dateObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
                      const dayOfWeek = dateObj.getDay(); // 0..6
                      const isWeekend = dayOfWeek === 4 || dayOfWeek === 5 || dayOfWeek === 6; // kept as in your code

                      return (
                        <th
                          key={i}
                          style={{
                            minWidth: 140,
                            background: isWeekend
                              ? `linear-gradient(180deg, ${tokens.weekend}, #1b1430)`
                              : 'linear-gradient(180deg, #1b2450, #182043)',
                            color: '#e5e7eb',
                            fontWeight: 800,
                            fontSize: '.95rem',
                            borderBottom: `1px solid ${tokens.panelBorder}`,
                            borderLeft: `1px solid ${tokens.panelBorder}`,
                            height: cellHeights.header,
                            padding: '10px 8px',
                            textAlign: 'center',
                            position: 'sticky',
                            top: 0,
                            zIndex: 10
                          } as React.CSSProperties}
                        >
                          <Box sx={{ direction: 'rtl' }}>
                            <div style={{ fontWeight: 900, letterSpacing: '.3px' }}>{formatDateDMY(date)}</div>
                            <div style={{ fontSize: '.8rem', opacity: .9, marginTop: 4 }}>
                              {['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ש'][dayOfWeek]}
                            </div>
                          </Box>
                        </th>
                      );
                    })}
                  </tr>
                </thead>

                <tbody>
                  {rowLabels.map((task, rIdx) => {
                    const isYTask = rIdx < y_task_names?.length || false;
                    const isXTask = !isYTask;

                    let shouldShow = true;
                    if (!showAllTasks) {
                      if (showYTasks && !isYTask) shouldShow = false;
                      if (showXTasks && !isXTask) shouldShow = false;
                    }
                    if (!shouldShow) return null;

                    const rowBg = rIdx % 2 === 0 ? tokens.tableOdd : tokens.tableEven;

                    return (
                      <tr
                        key={rIdx}
                        style={{
                          transition: 'background .15s ease'
                        }}
                        onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.backgroundColor = tokens.tableHover; }}
                        onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.backgroundColor = ''; }}
                      >
                        {/* Sticky task name cell */}
                        <td
                          style={{
                            position: 'sticky',
                            right: 0,
                            zIndex: 3,
                            background: `linear-gradient(180deg, rgba(139,92,246,.85), rgba(124,58,237,.85))`,
                            color: '#fff',
                            fontWeight: 800,
                            borderLeft: `1px solid ${tokens.panelBorder}`,
                            borderBottom: `1px solid ${tokens.panelBorder}`,
                            height: cellHeights.row,
                            padding: '14px 18px',
                            width: 260,
                            textAlign: 'right',
                            boxShadow: tokens.stickyShadow,
                            transform: 'translateZ(0)',
                            willChange: 'transform',         
                            backfaceVisibility: 'hidden'   
                          } as React.CSSProperties}
                        >
                          <span style={{ fontSize: tableSize === 'small' ? '.95rem' : tableSize === 'medium' ? '1.05rem' : '1.15rem' }}>
                            {task}
                          </span>
                        </td>

                        {grid[rIdx]?.map((soldier: string, cIdx: number) => {
                          const [day, month, year] = dates[cIdx].split('/');
                          const dateObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
                          const dayOfWeek = dateObj.getDay();
                          const isWeekend = dayOfWeek === 4 || dayOfWeek === 5 || dayOfWeek === 6;

                          return (
                            <td
                              key={cIdx}
                              style={{
                                backgroundColor: isWeekend ? tokens.weekend : rowBg,
                                color: tokens.textPrimary,
                                textAlign: 'center',
                                fontWeight: 600,
                                minWidth: 140,
                                borderLeft: `1px solid ${tokens.panelBorder}`,
                                borderBottom: `1px solid ${tokens.panelBorder}`,
                                height: cellHeights.row,
                                padding: '6px 8px',
                                verticalAlign: 'middle',
                                transition: 'all .15s ease',
                                cursor: 'default'
                              } as React.CSSProperties}
                              onMouseEnter={(e) => {
                                (e.currentTarget as HTMLTableCellElement).style.backgroundColor = isWeekend ? tokens.weekendHover : tokens.tableHover;
                                (e.currentTarget as HTMLTableCellElement).style.transform = 'scale(1.005)';
                              }}
                              onMouseLeave={(e) => {
                                (e.currentTarget as HTMLTableCellElement).style.backgroundColor = isWeekend ? tokens.weekend : rowBg;
                                (e.currentTarget as HTMLTableCellElement).style.transform = 'scale(1)';
                              }}
                            >
                              {soldier && (
                                <Box
                                  sx={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    px: 1.2,
                                    height: cellHeights.chip,
                                    lineHeight: `${cellHeights.chip}px`,
                                    fontSize: tableSize === 'small' ? '.82rem' : tableSize === 'medium' ? '.9rem' : '1rem',
                                    fontWeight: 800,
                                    color: '#0f172a',
                                    backgroundColor: tokens.chipBg,
                                    border: `1px solid ${tokens.chipBorder}`,
                                    borderRadius: 1.5,
                                    boxShadow: '0 2px 8px rgba(0,0,0,.20)',
                                    transition: 'all .15s ease',
                                    userSelect: 'none',
                                    maxWidth: 120,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    ':hover': { transform: 'translateY(-1px)', boxShadow: '0 4px 12px rgba(0,0,0,.28)' }
                                  }}
                                  title={soldier}
                                >
                                  {soldier}
                                </Box>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </Box>
            </Box>
          )}
        </Box>
      </Box>

      {/* SUCCESS SNACKBAR */}
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
            borderRadius: 2,
            fontWeight: 700,
            direction: 'rtl',
            background: `linear-gradient(180deg, ${tokens.accent}, ${tokens.accentDeep})`,
            color: '#fff',
            '& .MuiAlert-message': { textAlign: 'right' }
          }}
        >
          לוח זמנים משולב נשמר בהצלחה!
        </MuiAlert>
      </Snackbar>
    </Box>
  );
}
