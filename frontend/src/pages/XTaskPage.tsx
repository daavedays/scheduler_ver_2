/**
 * XTaskPage.tsx
 * -------------
 * UI page for creating, editing, and viewing X task schedules (main/primary tasks).
 *
 * Renders:
 *   - Table/grid for X task assignments (soldiers as rows, weeks as columns)
 *   - Floating action buttons for navigation and saving
 *   - Dialog for assigning tasks (standard/custom) to soldiers per week
 *   - Snackbar notifications for save/conflict actions
 *
 * State:
 *   - data: Original CSV data (2D array)
 *   - headers, subheaders: Table headers (weeks, date ranges)
 *   - editData: Editable grid of assignments
 *   - customTasks: Custom X task assignments per soldier
 *   - conflicts: Map of X/Y conflicts for highlighting
 *   - modal, modalTask, modalOther: For task assignment dialog
 *   - loading, saving, error: UI states
 *   - saveSuccess, conflictWarning: Snackbar states
 *
 * Effects:
 *   - Loads X task CSV and custom tasks on mount or when year/period changes
 *   - Loads X/Y conflicts for highlighting
 *
 * User Interactions:
 *   - Assign standard/custom tasks to soldiers per week
 *   - Remove assignments
 *   - Save schedule
 *   - See conflict warnings
 *
 * Notes:
 *   - Table cells are color-coded by task type
 *   - Custom tasks show date range in cell
 *   - Inline comments explain non-obvious logic and UI structure
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import Papa from 'papaparse';
import { 
  Box, 
  Typography, 
  Button, 
  Fab, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemText, 
  TextField, 
  Snackbar, 
  Alert as MuiAlert 
} from '@mui/material';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import SaveIcon from '@mui/icons-material/Save';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import DeleteIcon from '@mui/icons-material/Delete';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import Tooltip from '@mui/material/Tooltip';

import { shortWeekRange } from '../components/utils';
import { getWorkerColor, getXTaskColor } from '../components/colors';
import Header from '../components/Header';
import { 
  PRIMARY_COLORS, 
  BACKGROUND_COLORS, 
  TEXT_COLORS, 
  TABLE_COLORS, 
  TASK_COLORS,
  CARD_COLORS 
} from '../components/colorSystem';

const STANDARD_X_TASKS = ["Guarding Duties", "RASAR", "Kitchen"];
const MAX_CUSTOM_TASK_LEN = 14;

function XTaskPage() {
  const { mode } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const query = new URLSearchParams(location.search);
  const yearParam = parseInt(query.get('year') || '') || new Date().getFullYear();
  const periodParam = parseInt(query.get('period') || '') || 1;
  const [data, setData] = useState<string[][]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [subheaders, setSubheaders] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editData, setEditData] = useState<string[][]>([]);
  const [conflicts, setConflicts] = useState<{[key: string]: {x_task: string, y_task: string}}>({});
  const [customTasks, setCustomTasks] = useState<any>({});
  const [modal, setModal] = useState<{open: boolean, row: number, col: number, weekLabel: string, weekRange: string, soldier: string}>({open: false, row: -1, col: -1, weekLabel: '', weekRange: '', soldier: ''});
  const [modalTask, setModalTask] = useState<string>('');
  const [modalOther, setModalOther] = useState<{name: string, range: [Date | null, Date | null]}>({name: '', range: [null, null]});
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [customTaskWarning, setCustomTaskWarning] = useState('');
  const [conflictWarning, setConflictWarning] = useState(false);
  const [conflictDetails, setConflictDetails] = useState<any[]>([]); // Store conflict details for popup
  const [blinkCells, setBlinkCells] = useState<{[key: string]: boolean}>({}); // Track blinking cells
  const [pendingConflict, setPendingConflict] = useState<any | null>(null); // Track unresolved conflict
  const [showResolveBtn, setShowResolveBtn] = useState(false);
  const [soldiers, setSoldiers] = useState<{id: string, name: string}[]>([]);
  const [tableDarkMode, setTableDarkMode] = useState(true); // local state

  function renderCell(cell: string, colIdx: number, rowIdx: number) {
    // Use modern colors for empty cells
    let bg = cell && cell.trim() !== '' && cell !== '-' ? getXTaskColor(cell.split('\n')[0]) : (tableDarkMode ? '#334155' : '#f1f5f9');
    let color = tableDarkMode ? '#fff' : '#1e293b';
    let task = cell.split('\n')[0];
    let isCustom = false;
    let dateRange = '';
    if (cell && cell.trim() !== '' && cell !== '-') {
      if (cell.includes('\n(')) {
        isCustom = true;
        task = cell.split('\n')[0];
        dateRange = '';
        bg = getXTaskColor('Custom');
      } else {
        bg = getXTaskColor(task);
      }
    }
    let isConflict = false;
    let conflictInfo: {x_task: string, y_task: string} | undefined = undefined;
    let shouldBlink = false;
    if (conflicts && colIdx > 0 && editData[rowIdx] && editData[rowIdx][0]) {
      const soldier = editData[rowIdx][0];
      const date = headers[colIdx];
      const key = `${soldier}|${date}`;
      if (conflicts[key]) {
        isConflict = true;
        conflictInfo = conflicts[key];
        shouldBlink = blinkCells[key];
      }
    }
    const cellContent = (
      <div style={{
        width: '100%',
        height: '100%',
        background: isConflict ? '#fecaca' : bg,
        color,
        borderRadius: 4,
        padding: '2px 4px',
        fontWeight: 600,
        fontSize: 12,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 32,
        boxSizing: 'border-box',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        border: isConflict ? (shouldBlink ? '2px solid #ef4444' : '1px solid #ef4444') : `1px solid ${tableDarkMode ? '#475569' : '#cbd5e1'}`,
        boxShadow: cell && cell.trim() !== '' && cell !== '-' ? '0 1px 3px rgba(0,0,0,0.1)' : undefined,
        textShadow: cell && cell.trim() !== '' && cell !== '-' ? '0 1px 2px rgba(0,0,0,0.3)' : undefined,
        transition: shouldBlink ? 'box-shadow 0.2s, border 0.2s, background 0.2s' : 'box-shadow 0.2s, border 0.2s',
        animation: shouldBlink ? 'blink-border 0.5s alternate 6' : undefined,
        cursor: isConflict ? 'pointer' : 'default',
        opacity: cell && cell.trim() !== '' && cell !== '-' ? 1 : 0.8,
      }}>
        <span style={{
          fontSize: isCustom ? 11 : 12,
          fontWeight: 600,
          maxWidth: 60,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>{task.length > MAX_CUSTOM_TASK_LEN ? task.slice(0, MAX_CUSTOM_TASK_LEN) + '…' : task}</span>
        {/* No date range for custom tasks on X Tasks page */}
      </div>
    );
    if (isConflict && conflictInfo) {
      return (
        <Tooltip
          title={`Conflict: ${editData[rowIdx][0]} has both X task (${conflictInfo.x_task}) and Y task (${conflictInfo.y_task}) on ${headers[colIdx]}. Please adjust the Y schedule for this date.`}
          arrow
          placement="top"
        >
          {cellContent}
        </Tooltip>
      );
    }
    return cellContent;
  }

  function isCellFilled(cell: string) {
    return cell && cell !== '-';
  }

  const handleRemoveAssignment = () => {
    const { row, col, soldier } = modal;
    const cellValue = editData[row][col];
    if (cellValue.includes('\n(')) {
      const match = cellValue.match(/(.+)\n\((\d{2}\/\d{2}\/\d{4})-(\d{2}\/\d{2}\/\d{4})\)/);
      if (match) {
        const [, taskName, start, end] = match;
        setCustomTasks((prev: any) => {
          const updated = { ...prev };
          if (updated[soldier]) {
            updated[soldier] = updated[soldier].filter((t: any) => !(t.task === taskName && t.start === start && t.end === end));
            if (updated[soldier].length === 0) delete updated[soldier];
          }
          return updated;
        });
        setEditData(prev => {
          const copy = prev.map(r => [...r]);
          for (let c = 1; c < headers.length; ++c) {
            if (copy[row][c] === cellValue) copy[row][c] = '';
          }
          return copy;
        });
      }
    } else {
      setEditData(prev => {
        const copy = prev.map(r => [...r]);
        copy[row][col] = '';
        return copy;
      });
    }
    setModal(m => ({ ...m, open: false }));
  };

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:5001/api/x-tasks?year=${yearParam}&period=${periodParam}`, { credentials: 'include' })
      .then(res => res.json())
      .then(({ csv, custom_tasks }) => {
        const parsed = Papa.parse<string[]>(csv, { skipEmptyLines: false });
        setHeaders(parsed.data[0] as string[]);
        setSubheaders(parsed.data[1] as string[]);
        setData(parsed.data.slice(2) as string[][]);
        setEditData(parsed.data.slice(2) as string[][]);
        setCustomTasks(custom_tasks || {});
        setLoading(false);
        fetchConflicts();
      })
      .catch(() => { setError('Failed to load X tasks'); setLoading(false); });
  }, [yearParam, periodParam]);

  const fetchConflicts = useCallback(() => {
    return fetch(`http://localhost:5001/api/x-tasks/conflicts?year=${yearParam}&period=${periodParam}`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        const map: {[key: string]: {x_task: string, y_task: string}} = {};
        const blink: {[key: string]: boolean} = {};
        (data.conflicts || []).forEach((c: any) => {
          map[`${c.soldier}|${c.date}`] = { x_task: c.x_task, y_task: c.y_task };
          blink[`${c.soldier}|${c.date}`] = true;
        });
        setConflicts(map);
        setConflictDetails(data.conflicts || []);
        setBlinkCells(blink);
        setConflictWarning((data.conflicts || []).length > 0);
        // Remove blinking after 3s
        setTimeout(() => setBlinkCells({}), 3000);
        return (data.conflicts || []).length;
      });
  }, [yearParam, periodParam]);

  const handleCellChange = (row: number, col: number, value: string) => {
    setEditData(prev => {
      const copy = prev.map(r => [...r]);
      copy[row][col] = value;
      return copy;
    });
  };

  const handleCellClick = (row: number, col: number) => {
    setModal({
      open: true,
      row,
      col,
              weekLabel: headers[col],
        weekRange: subheaders[col],
        soldier: editData[row][1], // Use worker name (index 1) instead of ID (index 0)
    });
    setModalTask('');
    setModalOther({name: '', range: [null, null]});
  };

  // Helper to parse dd/mm and infer year for week start/end
  function parseDMWithYear(dm: string, weekIdx: number, weeks: {start: Date, end: Date}[]): Date | null {
    // Use the actual week start/end year from the weeks array
    if (!dm) return null;
    const [d, m] = dm.split('/');
    if (!d || !m) return null;
    // For week start, use weeks[weekIdx].start; for week end, use weeks[weekIdx].end
    // If weekIdx is out of bounds, fallback to current year
    let y = new Date().getFullYear();
    if (weeks && weeks[weekIdx]) {
      // If this is the first date in the subheader, it's the week start
      // If this is the second date, it's the week end
      // We'll infer based on the column index
      // If dm matches the week start, use weeks[weekIdx].start.getFullYear()
      // If dm matches the week end, use weeks[weekIdx].end.getFullYear()
      // We'll check both
      if (dm === weeks[weekIdx].start.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit' })) {
        y = weeks[weekIdx].start.getFullYear();
      } else if (dm === weeks[weekIdx].end.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit' })) {
        y = weeks[weekIdx].end.getFullYear();
      }
    }
    return new Date(Number(y), Number(m) - 1, Number(d));
  }

  const handleModalSave = () => {
    if (modalTask === 'Other') {
      if (!modalOther.name || !modalOther.range[0] || !modalOther.range[1]) return;
      if (modalOther.name.length > MAX_CUSTOM_TASK_LEN) {
        setCustomTaskWarning(`Custom task name must be at most ${MAX_CUSTOM_TASK_LEN} characters.`);
        return;
      }
      setCustomTaskWarning('');
      const s = modal.soldier;
      const newCustom = {...customTasks};
      if (!newCustom[s]) newCustom[s] = [];
      newCustom[s].push({
        task: modalOther.name,
        start: formatDateDMY(modalOther.range[0]),
        end: formatDateDMY(modalOther.range[1]),
      });
      setCustomTasks(newCustom);
      // Build weeks array for correct year inference
      const weeksArr = headers.slice(2).map((h, i) => {
        const [startDM, endDM] = (subheaders[i+2] || '').split(' - ');
        // Use yearParam and handle year rollover for endDM
        let startYear = yearParam;
        let endYear = yearParam;
        if (i > 0 && startDM && endDM) {
          // If endDM month is January and startDM is December, increment year
          const [endD, endM] = endDM.split('/').map(Number);
          const [startD, startM] = startDM.split('/').map(Number);
          if (startM === 12 && endM === 1) {
            endYear = yearParam + 1;
          }
        }
        const weekStart = new Date(startYear, Number(startDM.split('/')[1]) - 1, Number(startDM.split('/')[0]));
        const weekEnd = new Date(endYear, Number(endDM.split('/')[1]) - 1, Number(endDM.split('/')[0]));
        return { start: weekStart, end: weekEnd };
      });
      setEditData(prev => {
        const copy = prev.map(r => [...r]);
        for (let c = 1; c < headers.length; ++c) {
          const [start, end] = (subheaders[c] || '').split(' - ');
          if (!start || !end) continue;
          // Use the new helper to get correct years
          const weekStart = parseDMWithYear(start, c-2, weeksArr);
          const weekEnd = parseDMWithYear(end, c-2, weeksArr);
          if (!weekStart || !weekEnd) continue;
          if (modalOther.range[0]! <= weekEnd && modalOther.range[1]! >= weekStart) {
            copy[modal.row][c] = `${modalOther.name}\n(${formatDateDMY(modalOther.range[0]!)}-${formatDateDMY(modalOther.range[1]!)})`;
          }
        }
        return copy;
      });
    } else if (modalTask) {
      setEditData(prev => {
        const copy = prev.map(r => [...r]);
        copy[modal.row][modal.col] = modalTask;
        return copy;
      });
    }
    setModal(m => ({...m, open: false}));
  };

  function formatDateDMY(date: Date): string {
    const d = date.getDate().toString().padStart(2, '0');
    const m = (date.getMonth() + 1).toString().padStart(2, '0');
    const y = date.getFullYear().toString();
    return `${d}/${m}/${y}`;
  }
  function parseDM(dm: string, yearHeader: string): Date | null {
    const [d, m] = dm.split('/');
    const y = new Date().getFullYear();
    try {
      return new Date(Number(y), Number(m) - 1, Number(d));
    } catch {
      return null;
    }
  }

  // Cache for Y tasks data to avoid repeated requests
  const [yTasksCache, setYTasksCache] = useState<any>(null);
  const [yTasksCacheTime, setYTasksCacheTime] = useState<number>(0);

  // Helper to get Y tasks data with caching
  async function getYTasksData() {
    const now = Date.now();
    // Cache for 30 seconds
    if (yTasksCache && (now - yTasksCacheTime) < 30000) {
      return yTasksCache;
    }
    
    const yIndexRes = await fetch('http://localhost:5001/data/y_tasks.json', { credentials: 'include' });
    const yIndex = await yIndexRes.json();
    
    // Load all Y schedule CSVs
    const ySchedules: any = {};
    for (const key in yIndex) {
      const yCsvRes = await fetch(`http://localhost:5001/data/${yIndex[key]}`, { credentials: 'include' });
      const yCsv = await yCsvRes.text();
      const rows = yCsv.split('\n').filter(Boolean).map(line => line.split(','));
      ySchedules[key] = {
        dates: rows[0].slice(1),
        rows: rows.slice(1),
        filename: yIndex[key]
      };
    }
    
    const cacheData = { yIndex, ySchedules };
    setYTasksCache(cacheData);
    setYTasksCacheTime(now);
    return cacheData;
  }

  // Helper to check for conflicts for a single cell
  async function checkCellConflict(soldier: string, date: string, xTask: string) {
    const { yIndex, ySchedules } = await getYTasksData();
    
    // Check each period
    for (const key in yIndex) {
      const [start, end] = key.split('_to_');
      const d0 = parseDMY(start);
      const d1 = parseDMY(end);
      const d = parseDMY(date);
      if (!d0 || !d1 || !d) continue;
      if (d >= d0 && d <= d1) {
        const schedule = ySchedules[key];
        const yIdx = schedule.dates.indexOf(date);
        if (yIdx === -1) continue;
        
        for (let r = 0; r < schedule.rows.length; ++r) {
          if (schedule.rows[r][yIdx + 1] === soldier) {
            // Conflict found
            return {
              soldier,
              date,
              xTask,
              yTask: schedule.rows[r][0],
              yPeriod: { start, end, filename: yIndex[key] },
              yRow: r,
              yCol: yIdx
            };
          }
        }
      }
    }
    return null;
  }
  function parseDMY(d: string) {
    const [day, month, year] = d.split('/').map(Number);
    return new Date(year, month - 1, day);
  }

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setShowResolveBtn(false);
    setPendingConflict(null);
    try {
      const csv = Papa.unparse([headers, subheaders, ...editData]);
      const res = await fetch('http://localhost:5001/api/x-tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ csv, custom_tasks: customTasks, year: yearParam, half: periodParam }),
      });
      if (!res.ok) throw new Error('Save failed');
      setSaveSuccess(true);
      // After saving, check for conflicts for changed cells only
      // For demo: check all filled cells (could optimize to only changed)
      let foundConflict = null;
      for (let r = 0; r < editData.length; ++r) {
        for (let c = 1; c < headers.length; ++c) {
          const soldier = editData[r][0];
          const cell = editData[r][c];
          const date = subheaders[c];
          if (soldier && cell && cell !== '-') {
            const conflict = await checkCellConflict(soldier, date, cell);
            if (conflict) {
              foundConflict = conflict;
              break;
            }
          }
        }
        if (foundConflict) break;
      }
      if (foundConflict) {
        setPendingConflict(foundConflict);
        setShowResolveBtn(true);
        setConflictWarning(true);
        setConflictDetails([foundConflict]);
        setBlinkCells({ [`${foundConflict.soldier}|${foundConflict.date}`]: true });
        setTimeout(() => setBlinkCells({}), 3000);
      } else {
        setShowResolveBtn(false);
        setPendingConflict(null);
      }
      // Fetch conflicts for highlighting
      fetch(`http://localhost:5001/api/x-tasks/conflicts?year=${yearParam}&period=${periodParam}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          const map: {[key: string]: {x_task: string, y_task: string}} = {};
          const blink: {[key: string]: boolean} = {};
          (data.conflicts || []).forEach((c: any) => {
            map[`${c.soldier}|${c.date}`] = { x_task: c.x_task, y_task: c.y_task };
            blink[`${c.soldier}|${c.date}`] = true;
          });
          setConflicts(map);
          setConflictDetails(data.conflicts || []);
          setBlinkCells(blink);
          setConflictWarning((data.conflicts || []).length > 0);
          // Remove blinking after 3s
          setTimeout(() => setBlinkCells({}), 3000);
        });
    } catch (e) {
      setError('An error occurred');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: BACKGROUND_COLORS.bg_main,
      position: 'relative',
      overflow: 'hidden',
      '& @keyframes blink-border': {
        '0%': {
          borderColor: '#ef4444',
          boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.4)'
        },
        '100%': {
          borderColor: '#dc2626',
          boxShadow: '0 0 0 4px rgba(239, 68, 68, 0)'
        }
      }
    }}>
      {/* Background Pattern */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.03) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(236, 72, 153, 0.02) 0%, transparent 50%)',
        pointerEvents: 'none',
        zIndex: 0
      }} />
      
      <Box sx={{ position: 'relative', zIndex: 1 }}>
        <Header 
          darkMode={true}
          onToggleDarkMode={() => setTableDarkMode(d => !d)}
          showBackButton={true}
          showHomeButton={true}
          title="X Tasks"
        />
        
        {/* Main Content Container */}
        <Box sx={{ 
          maxWidth: 1400, 
          mx: 'auto', 
          p: 4, 
          pt: 12,
          position: 'relative'
        }}>
          {/* Loading State */}
          {loading && (
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              py: 8 
            }}>
              <Box sx={{
                bgcolor: CARD_COLORS.card_bg,
                borderRadius: 4,
                p: 4,
                backdropFilter: 'blur(10px)',
                border: `1px solid ${CARD_COLORS.card_border}`,
                boxShadow: CARD_COLORS.card_shadow,
                textAlign: 'center'
              }}>
                <Typography variant="h6" sx={{ 
                  color: TEXT_COLORS.text_primary, 
                  fontWeight: 600 
                }}>
                  Loading X Task Schedule...
                </Typography>
              </Box>
            </Box>
          )}
          
          {/* Error State */}
          {error && (
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              py: 4 
            }}>
              <Box sx={{
                bgcolor: 'rgba(255, 82, 82, 0.1)',
                border: '1px solid rgba(255, 82, 82, 0.3)',
                borderRadius: 4,
                p: 4,
                backdropFilter: 'blur(10px)',
                boxShadow: CARD_COLORS.card_shadow,
                textAlign: 'center',
                maxWidth: 600
              }}>
                <Typography variant="h6" sx={{ 
                  color: '#ff5252', 
                  fontWeight: 600,
                  mb: 2
                }}>
                  Error Loading Schedule
                </Typography>
                <Typography sx={{ color: TEXT_COLORS.text_secondary }}>
                  {error}
                </Typography>
              </Box>
            </Box>
          )}
          
          {/* Schedule Selector */}
          {!loading && !error && (
            <Box sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              mb: 4
            }}>
              <Box sx={{
                bgcolor: CARD_COLORS.card_bg,
                borderRadius: 4,
                p: 3,
                backdropFilter: 'blur(10px)',
                border: `1px solid ${CARD_COLORS.card_border}`,
                boxShadow: CARD_COLORS.card_shadow,
                textAlign: 'center',
                minWidth: 500
              }}>
                <Typography variant="h5" sx={{ 
                  color: TEXT_COLORS.text_primary, 
                  fontWeight: 700, 
                  mb: 3 
                }}>
                  X Task Schedule - {yearParam} Period {periodParam}
                </Typography>
                <Box sx={{ 
                  display: 'flex', 
                  gap: 2, 
                  flexWrap: 'wrap',
                  justifyContent: 'center'
                }}>
                  <Button
                    variant="outlined"
                    onClick={() => navigate(`/x-tasks/${mode}?year=${yearParam}&period=${periodParam === 1 ? 2 : 1}`)}
                    sx={{
                      color: PRIMARY_COLORS.primary_main,
                      borderColor: PRIMARY_COLORS.primary_main,
                      fontWeight: 600,
                      px: 3,
                      py: 1.5,
                      borderRadius: 2,
                      '&:hover': {
                        borderColor: PRIMARY_COLORS.primary_main,
                        bgcolor: 'rgba(99, 102, 241, 0.1)'
                      }
                    }}
                  >
                    Switch to Period {periodParam === 1 ? 2 : 1}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => navigate(`/x-tasks/${mode}?year=${yearParam + 1}&period=1`)}
                    sx={{
                      color: PRIMARY_COLORS.secondary_main,
                      borderColor: PRIMARY_COLORS.secondary_main,
                      fontWeight: 600,
                      px: 3,
                      py: 1.5,
                      borderRadius: 2,
                      '&:hover': {
                        borderColor: PRIMARY_COLORS.secondary_main,
                        bgcolor: 'rgba(236, 72, 153, 0.1)'
                      }
                    }}
                  >
                    Next Year
                  </Button>
                </Box>
              </Box>
            </Box>
          )}
          
          {/* Action Buttons */}
          <Box sx={{ 
            position: 'fixed', 
            top: 120, 
            right: 32, 
            zIndex: 1200, 
            display: 'flex', 
            gap: 2,
            flexDirection: 'column'
          }}>
            <Fab
              color="primary"
              onClick={handleSave}
              disabled={saving}
              sx={{
                width: 60,
                height: 60,
                bgcolor: PRIMARY_COLORS.primary_main,
                boxShadow: `0 6px 25px ${PRIMARY_COLORS.primary_main}40`,
                borderRadius: '50%',
                fontWeight: 700,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'scale(1.1)',
                  bgcolor: PRIMARY_COLORS.primary_main,
                  boxShadow: `0 8px 30px ${PRIMARY_COLORS.primary_main}60`
                }
              }}
              aria-label="save"
            >
              <SaveIcon sx={{ fontSize: 28, color: '#fff' }} />
            </Fab>
            {showResolveBtn && pendingConflict && (
              <Fab
                color="error"
                onClick={() => {
                  localStorage.setItem('resolveConflict', JSON.stringify(pendingConflict));
                  navigate('/y-tasks');
                }}
                sx={{
                  width: 60,
                  height: 60,
                  bgcolor: '#ff5252',
                  boxShadow: '0 6px 25px rgba(255, 82, 82, 0.4)',
                  borderRadius: '50%',
                  fontWeight: 700,
                  animation: 'blink-border 1s alternate infinite',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'scale(1.1)',
                    boxShadow: '0 8px 30px rgba(255, 82, 82, 0.6)'
                  }
                }}
                aria-label="resolve-conflict"
                title="Resolve Conflict"
              >
                <WarningAmberIcon sx={{ fontSize: 28, color: '#fff' }} />
              </Fab>
            )}
          </Box>
          
          {/* Table Section */}
          {!loading && !error && editData.length > 0 && (
            <Box sx={{ 
              overflow: 'auto',
              borderRadius: 0.1,
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
              border: `1px solid ${CARD_COLORS.card_border}`,
              bgcolor: CARD_COLORS.card_bg,
              backdropFilter: 'blur(10px)',
              position: 'relative',
              maxHeight: '100vh',
              '&::-webkit-scrollbar': {
                width: '8px',
                height: '8px'
              },
              '&::-webkit-scrollbar-track': {
                background: tableDarkMode ? '#334155' : '#f1f5f9',
                borderRadius: '0.1px'
              },
              '&::-webkit-scrollbar-thumb': {
                background: tableDarkMode ? '#475569' : '#cbd5e1',
                borderRadius: '0.1px',
                '&:hover': {
                  background: tableDarkMode ? '#64748b' : '#94a3b8'
                }
              }
            }}>
              <Box component="table" sx={{ 
                width: '100%', 
                borderCollapse: 'separate', 
                borderSpacing: 0, 
                minWidth: 900, 
                background: 'transparent', 
                borderRadius: 0, 
                overflow: 'visible'
              }}>
                <thead>
                  <tr>
                    <th style={{
                      minWidth: 160,
                      fontWeight: 700,
                      fontSize: 16,
                      background: tableDarkMode ? TABLE_COLORS.table_sticky_bg : TABLE_COLORS.table_sticky_bg_light,
                      color: tableDarkMode ? TEXT_COLORS.text_primary : TEXT_COLORS.text_light_primary,
                      position: 'sticky',
                      left: 0,
                      zIndex: 20,
                      top: 0,
                      borderLeft: `3px solid ${tableDarkMode ? TABLE_COLORS.table_border : TABLE_COLORS.table_border_light}`,
                      paddingLeft: 16,
                      borderRight: `1px solid ${tableDarkMode ? TABLE_COLORS.table_border : TABLE_COLORS.table_border_light}`,
                      borderBottom: `1px solid ${tableDarkMode ? TABLE_COLORS.table_border : TABLE_COLORS.table_border_light}`,
                      backgroundClip: 'padding-box',
                      height: 40,
                      letterSpacing: 1,
                      boxShadow: tableDarkMode ? '2px 0 8px -4px rgba(0,0,0,0.3)' : '2px 0 8px -4px rgba(0,0,0,0.1)',
                    }}>שם</th>
                    {headers.slice(2).map((h, i) => (
                      <th key={i} style={{
                        textAlign: 'center',
                        padding: 4,
                        background: TABLE_COLORS.table_header_bg,
                        color: '#fff',
                        fontWeight: 700,
                        fontSize: 14,
                        position: 'sticky',
                        top: 0,
                        zIndex: 15,
                        minWidth: 60,
                        maxWidth: 80,
                        whiteSpace: 'nowrap',
                        borderBottom: `2px solid ${tableDarkMode ? TABLE_COLORS.table_border : TABLE_COLORS.table_border_light}`,
                        backgroundClip: 'padding-box',
                        height: 40,
                      }}>
                        <div>{h}</div>
                        <div style={{ fontSize: 10, color: TASK_COLORS.x_task_kitchen, marginTop: 1 }}>{shortWeekRange(subheaders[i+2])}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {editData.map((row, rIdx) => {
                    if (!row[1] || row[1].includes('/')) return null;
                    const soldierName = (row[1] || '').trim();
                    const rowCells = row.slice(2);
                    const numCells = headers.length - 2;
                    const paddedCells = rowCells.length < numCells ? [...rowCells, ...Array(numCells - rowCells.length).fill('')] : rowCells;
                    return (
                      <tr key={rIdx} style={{ 
                        background: rIdx % 2 === 0 ? (tableDarkMode ? 'rgba(255, 255, 255, 0.02)' : '#f8fafc') : (tableDarkMode ? 'rgba(255, 255, 255, 0.04)' : '#ffffff'),
                        transition: 'background-color 0.2s ease'
                      }}>
                        <td style={{
                          fontWeight: 600,
                          background: tableDarkMode ? TABLE_COLORS.table_sticky_bg : TABLE_COLORS.table_sticky_bg_light,
                          color: tableDarkMode ? TEXT_COLORS.text_primary : TEXT_COLORS.text_light_primary,
                          minWidth: 160,
                          position: 'sticky',
                          left: 0,
                          zIndex: 18,
                          borderLeft: `3px solid ${tableDarkMode ? TABLE_COLORS.table_border : TABLE_COLORS.table_border_light}`,
                          paddingLeft: 16,
                          borderRight: `1px solid ${tableDarkMode ? TABLE_COLORS.table_border : TABLE_COLORS.table_border_light}`,
                          borderBottom: `1px solid ${tableDarkMode ? TABLE_COLORS.table_border : TABLE_COLORS.table_border_light}`,
                          backgroundClip: 'padding-box',
                          fontSize: 16,
                          height: 40,
                          boxShadow: tableDarkMode ? '2px 0 8px -4px rgba(0,0,0,0.3)' : '2px 0 8px -4px rgba(0,0,0,0.1)',
                        }}>{soldierName}</td>
                        {paddedCells.map((cell, cIdx) => {
                          const colIdx = cIdx + 2;
                          const isFilled = cell && cell.trim() !== '' && cell !== '-';
                          return (
                            <td
                              key={colIdx}
                              style={{
                                background: isFilled
                                  ? (tableDarkMode ? getXTaskColor(cell.split('\n')[0]) : '#fef3c7')
                                  : (tableDarkMode ? 'rgba(51, 65, 85, 0.8)' : '#f8fafc'),
                                color: tableDarkMode ? TEXT_COLORS.text_primary : TEXT_COLORS.text_light_primary,
                                textShadow: tableDarkMode && isFilled ? '0 1px 2px rgba(0,0,0,0.3)' : undefined,
                                textAlign: 'center',
                                fontWeight: 600,
                                minWidth: 60,
                                maxWidth: 80,
                                border: tableDarkMode ? `1px solid ${TABLE_COLORS.table_border}` : `1px solid #e2e8f0`,
                                borderRadius: 4,
                                fontSize: 14,
                                height: 40,
                                boxSizing: 'border-box',
                                transition: 'all 0.2s ease',
                                cursor: 'pointer',
                                boxShadow: isFilled ? '0 2px 4px rgba(0,0,0,0.1)' : 'none',
                                opacity: isFilled ? 1 : 0.8,
                                padding: '4px',
                              }}
                              onClick={() => handleCellClick(rIdx, colIdx)}
                              onMouseOver={e => { 
                                (e.currentTarget as HTMLElement).style.background = '#f59e0b'; 
                                (e.currentTarget as HTMLElement).style.transform = 'scale(1.02)';
                                (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                              }}
                              onMouseOut={e => { 
                                (e.currentTarget as HTMLElement).style.background = isFilled
                                  ? (tableDarkMode ? getXTaskColor(cell.split('\n')[0]) : '#fef3c7')
                                  : (tableDarkMode ? 'rgba(51, 65, 85, 0.8)' : '#f8fafc');
                                (e.currentTarget as HTMLElement).style.transform = 'scale(1)';
                                (e.currentTarget as HTMLElement).style.boxShadow = isFilled ? '0 2px 4px rgba(0,0,0,0.1)' : 'none';
                              }}
                            >
                              {renderCell(cell, colIdx, rIdx)}
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
          
          {/* Empty State */}
          {!loading && !error && editData.length === 0 && (
            <Box sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              py: 8
            }}>
              <Box sx={{
                bgcolor: CARD_COLORS.card_bg,
                borderRadius: 4,
                p: 6,
                backdropFilter: 'blur(10px)',
                border: `1px solid ${CARD_COLORS.card_border}`,
                boxShadow: CARD_COLORS.card_shadow,
                textAlign: 'center',
                maxWidth: 600
              }}>
                <Typography variant="h5" sx={{ 
                  color: TEXT_COLORS.text_primary, 
                  fontWeight: 700,
                  mb: 3
                }}>
                  No X Task Schedule Found
                </Typography>
                <Typography variant="body1" sx={{ 
                  color: TEXT_COLORS.text_secondary,
                  mb: 4,
                  lineHeight: 1.6
                }}>
                  No X task schedule was found for {yearParam} Period {periodParam}. 
                  Please create a new schedule or check if the data exists.
                </Typography>
              </Box>
            </Box>
          )}
        </Box>
      </Box>
      {/* Task Assignment Dialog */}
      <Dialog 
        open={modal.open} 
        onClose={() => setModal(m => ({...m, open: false}))}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: 'rgba(26, 34, 51, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 0.5,
            boxShadow: '0 16px 64px rgba(0,0,0,0.5)'
          }
        }}
      >
                  <DialogTitle sx={{ 
            color: TEXT_COLORS.text_primary, 
            background: TABLE_COLORS.table_header_bg,
            borderBottom: `1px solid ${TABLE_COLORS.table_border}`,
            fontWeight: 700,
            fontSize: '1.25rem',
            borderRadius: '0.1px 0.1px 0 0'
          }}>
          Assign X Task for {modal.soldier} - Week {modal.weekLabel}
        </DialogTitle>
        <DialogContent sx={{ 
          background: 'transparent',
          pt: 3
        }}>
          <List sx={{ p: 0 }}>
            {STANDARD_X_TASKS.map((task, idx) => (
              <ListItem key={idx} disablePadding sx={{ mb: 1 }}>
                <ListItemButton 
                  selected={modalTask === task} 
                  onClick={() => setModalTask(task)} 
                                      sx={{ 
                      color: TEXT_COLORS.text_primary, 
                      background: modalTask === task ? (getXTaskColor(task) || '#e3f2fd') : 'rgba(255,255,255,0.05)',
                      borderRadius: 1,
                      border: modalTask === task ? `2px solid ${TABLE_COLORS.table_border}` : '1px solid rgba(255,255,255,0.1)',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                      background: modalTask === task ? (getXTaskColor(task) || '#e3f2fd') : 'rgba(255,255,255,0.1)',
                      transform: 'translateX(4px)'
                    }
                  }}
                >
                  <ListItemText 
                    primary={task} 
                    primaryTypographyProps={{
                      fontWeight: modalTask === task ? 700 : 500
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
            <ListItem disablePadding sx={{ mb: 1 }}>
              <ListItemButton 
                selected={modalTask === 'Other'} 
                onClick={() => setModalTask('Other')} 
                sx={{ 
                  color: '#e0e6ed', 
                  background: modalTask === 'Other' ? (getXTaskColor('Custom') || '#e3f2fd') : 'rgba(255,255,255,0.05)',
                  borderRadius: 2,
                  border: modalTask === 'Other' ? '2px solid rgba(255,255,255,0.3)' : '1px solid rgba(255,255,255,0.1)',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    background: modalTask === 'Other' ? (getXTaskColor('Custom') || '#e3f2fd') : 'rgba(255,255,255,0.1)',
                    transform: 'translateX(4px)'
                  }
                }}
              >
                <ListItemText 
                  primary="Other (Custom Task)" 
                  primaryTypographyProps={{
                    fontWeight: modalTask === 'Other' ? 700 : 500
                  }}
                />
              </ListItemButton>
            </ListItem>
          </List>
          
          {modalTask === 'Other' && (
            <Box sx={{ mt: 4, p: 3, bgcolor: 'rgba(255,255,255,0.03)', borderRadius: 3 }}>
              <TextField
                label="Custom Task Name"
                value={modalOther.name}
                onChange={e => {
                  if (e.target.value.length <= MAX_CUSTOM_TASK_LEN) setModalOther(o => ({...o, name: e.target.value}));
                }}
                fullWidth
                sx={{ mb: 3 }}
                inputProps={{ maxLength: MAX_CUSTOM_TASK_LEN }}
                helperText={customTaskWarning || `${modalOther.name.length}/${MAX_CUSTOM_TASK_LEN} characters`}
                error={!!customTaskWarning}
                InputProps={{
                  sx: {
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
                  }
                }}
                InputLabelProps={{
                  sx: { color: 'rgba(255,255,255,0.7)' }
                }}
                FormHelperTextProps={{
                  sx: { color: customTaskWarning ? '#f44336' : 'rgba(255,255,255,0.6)' }
                }}
              />
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <DatePicker
                    label="Start Date"
                    value={modalOther.range[0]}
                    onChange={(date: Date | null) => setModalOther(o => ({...o, range: [date, o.range[1]]}))}
                    format="dd/MM/yyyy"
                    slotProps={{ 
                      textField: { 
                        sx: { 
                          minWidth: 180,
                          '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                            borderColor: '#1976d2',
                          },
                        },
                        InputLabelProps: { sx: { color: 'rgba(255,255,255,0.7)' } }
                      } 
                    }}
                  />
                  <DatePicker
                    label="End Date"
                    value={modalOther.range[1]}
                    onChange={(date: Date | null) => setModalOther(o => ({...o, range: [o.range[0], date]}))}
                    format="dd/MM/yyyy"
                    slotProps={{ 
                      textField: { 
                        sx: { 
                          minWidth: 180,
                          '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                            borderColor: '#1976d2',
                          },
                        },
                        InputLabelProps: { sx: { color: 'rgba(255,255,255,0.7)' } }
                      } 
                    }}
                  />
                </Box>
              </LocalizationProvider>
            </Box>
          )}
          
          {isCellFilled(editData[modal.row]?.[modal.col] || '') && (
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={handleRemoveAssignment}
                sx={{ 
                  fontWeight: 600,
                  borderColor: 'rgba(244, 67, 54, 0.5)',
                  color: '#f44336',
                  '&:hover': {
                    borderColor: '#f44336',
                    bgcolor: 'rgba(244, 67, 54, 0.1)'
                  }
                }}
              >
                Remove Assignment
              </Button>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ 
          background: 'rgba(35, 42, 54, 0.8)',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          p: 2
        }}>
          <Button 
            onClick={() => setModal(m => ({...m, open: false}))} 
            sx={{ 
              color: '#e0e6ed',
              fontWeight: 600,
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.1)'
              }
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleModalSave} 
            disabled={modalTask === '' || (modalTask === 'Other' && (!modalOther.name || !modalOther.range[0] || !modalOther.range[1]))} 
            variant="contained"
            sx={{ 
              color: '#fff',
              bgcolor: '#1976d2',
              fontWeight: 600,
              '&:hover': {
                bgcolor: '#1565c0'
              },
              '&:disabled': {
                bgcolor: 'rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.3)'
              }
            }}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
      
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
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
          }}
        >
          X tasks saved successfully!
        </MuiAlert>
      </Snackbar>
      
      {/* Conflict Warning Snackbar */}
      <Snackbar
        open={conflictWarning}
        autoHideDuration={10000}
        onClose={() => setConflictWarning(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <MuiAlert 
          onClose={() => setConflictWarning(false)} 
          severity="warning" 
          sx={{ 
            width: '100%',
            maxWidth: 600,
            borderRadius: 3,
            fontWeight: 600,
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
          }}
        >
          <Box sx={{ mb: 2 }}>
            <strong>X/Y Task Conflict Detected!</strong>
          </Box>
          <Box component="ul" sx={{ m: 0, pl: 2 }}>
            {conflictDetails.map((c, i) => (
              <Box component="li" key={i} sx={{ mb: 1 }}>
                <strong>{c.soldier}</strong> has <strong>X: {c.x_task}</strong> and <strong>Y: {c.y_task}</strong> on <strong>{c.date}</strong>
              </Box>
            ))}
          </Box>
          <Box sx={{ mt: 2, fontSize: '0.9rem' }}>
            Please review the highlighted (blinking) cells and adjust the Y schedule as needed.
          </Box>
        </MuiAlert>
      </Snackbar>
    </Box>
  );
}

export default XTaskPage;