import React, { useEffect, useState } from 'react';
import { Box, Typography, Table, TableHead, TableRow, TableCell, TableBody, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Select, MenuItem, Chip, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import Checkbox from '@mui/material/Checkbox';
import PageContainer from '../components/PageContainer';
import TableContainer from '../components/TableContainer';
import { API_BASE_URL } from '../utils/api';
import { YTaskDefinition } from '../types';

function UpdateWorkersPage({ darkMode, onToggleDarkMode }: { darkMode: boolean; onToggleDarkMode: () => void }) {
  const [workers, setWorkers] = useState<any[]>([]);
  const [qualifications, setQualifications] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [editDialog, setEditDialog] = useState<{open: boolean, worker: any | null}>({open: false, worker: null});
  const [addDialog, setAddDialog] = useState(false);
  const [newWorker, setNewWorker] = useState<any>({ id: '', name: '', start_date: '', qualifications: [], closing_interval: 4, officer: false, seniority: '', score: 0 });

  useEffect(() => {
    fetchWorkers();
    fetchQualifications();
  }, []);

  const fetchWorkers = () => {
    setLoading(true);
    fetch(`${API_BASE_URL}/api/workers`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => { setWorkers(data.workers || []); setLoading(false); });
  };

  const fetchQualifications = () => {
    fetch(`${API_BASE_URL}/api/y-tasks/definitions`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        const quals = (data.definitions || []).map((def: YTaskDefinition) => def.name);
        setQualifications(quals);
      })
      .catch(() => {});
  };

  const handleEdit = (worker: any) => setEditDialog({ open: true, worker: { ...worker } });
  const handleDelete = (id: string) => {
    fetch(`${API_BASE_URL}/api/workers/${id}`, { method: 'DELETE', credentials: 'include' })
      .then(res => res.json())
      .then(() => fetchWorkers());
  };
  const handleSaveEdit = () => {
    fetch(`${API_BASE_URL}/api/workers/${editDialog.worker.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(editDialog.worker)
    })
      .then(res => res.json())
      .then(() => { setEditDialog({ open: false, worker: null }); fetchWorkers(); });
  };
  const handleAdd = () => {
    fetch(`${API_BASE_URL}/api/workers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(newWorker)
    })
      .then(res => res.json())
      .then(() => { setAddDialog(false); setNewWorker({ id: '', name: '', start_date: '', qualifications: [], closing_interval: 4, officer: false, seniority: '', score: 0 }); fetchWorkers(); });
  };

  return (
    <PageContainer>
      <Typography variant="h5" sx={{ mb: 2 }}>Update Workers</Typography>
      <Button variant="contained" sx={{ mb: 2 }} onClick={() => setAddDialog(true)}>Add Worker</Button>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Qualifications</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {workers.map(worker => (
              <TableRow key={worker.id}>
                <TableCell>{worker.id}</TableCell>
                <TableCell>{worker.name}</TableCell>
                <TableCell>{worker.qualifications.join(', ')}</TableCell>
                <TableCell>
                  <Button variant="outlined" size="small" onClick={() => handleEdit(worker)}>Edit</Button>
                  <IconButton color="error" onClick={() => handleDelete(worker.id)}><DeleteIcon /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {/* Edit Dialog */}
      <Dialog open={editDialog.open} onClose={() => setEditDialog({ open: false, worker: null })}>
        <DialogTitle>Edit Worker</DialogTitle>
        <DialogContent>
          <TextField label="Name" value={editDialog.worker?.name || ''} onChange={e => setEditDialog(d => ({ ...d, worker: { ...d.worker, name: e.target.value } }))} fullWidth sx={{ mb: 2 }} />
          <TextField label="Start Date" value={editDialog.worker?.start_date || ''} onChange={e => setEditDialog(d => ({ ...d, worker: { ...d.worker, start_date: e.target.value } }))} fullWidth sx={{ mb: 2 }} />
          <Select
            multiple
            value={editDialog.worker?.qualifications || []}
            onChange={e => setEditDialog(d => ({ ...d, worker: { ...d.worker, qualifications: e.target.value } }))}
            fullWidth
            renderValue={selected => (<Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>{selected.map((val: string) => (<Chip key={val} label={val} />))}</Box>)}
            sx={{ mb: 2 }}
          >
            {qualifications.map(q => <MenuItem key={q} value={q}>{q}</MenuItem>)}
          </Select>
          <TextField label="Closing Interval" type="number" value={editDialog.worker?.closing_interval || 4} onChange={e => setEditDialog(d => ({ ...d, worker: { ...d.worker, closing_interval: Number(e.target.value) } }))} fullWidth sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Checkbox checked={!!editDialog.worker?.officer} onChange={e => setEditDialog(d => ({ ...d, worker: { ...d.worker, officer: e.target.checked } }))} /> Officer
          </Box>
          <TextField label="Seniority" value={editDialog.worker?.seniority || ''} onChange={e => setEditDialog(d => ({ ...d, worker: { ...d.worker, seniority: e.target.value } }))} fullWidth sx={{ mb: 2 }} />
          <TextField label="Score" type="number" value={editDialog.worker?.score || 0} onChange={e => setEditDialog(d => ({ ...d, worker: { ...d.worker, score: Number(e.target.value) } }))} fullWidth sx={{ mb: 2 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false, worker: null })}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
      {/* Add Dialog */}
      <Dialog open={addDialog} onClose={() => setAddDialog(false)}>
        <DialogTitle>Add Worker</DialogTitle>
        <DialogContent>
          <TextField label="ID" value={newWorker.id} onChange={e => setNewWorker((w: any) => ({ ...w, id: e.target.value }))} fullWidth sx={{ mb: 2 }} />
          <TextField label="Name" value={newWorker.name} onChange={e => setNewWorker((w: any) => ({ ...w, name: e.target.value }))} fullWidth sx={{ mb: 2 }} />
          <TextField label="Start Date" value={newWorker.start_date} onChange={e => setNewWorker((w: any) => ({ ...w, start_date: e.target.value }))} fullWidth sx={{ mb: 2 }} />
          <Select
            multiple
            value={newWorker.qualifications}
            onChange={e => setNewWorker((w: any) => ({ ...w, qualifications: e.target.value }))}
            fullWidth
            renderValue={selected => (<Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>{selected.map((val: string) => (<Chip key={val} label={val} />))}</Box>)}
            sx={{ mb: 2 }}
          >
            {qualifications.map(q => <MenuItem key={q} value={q}>{q}</MenuItem>)}
          </Select>
          <TextField label="Closing Interval" type="number" value={newWorker.closing_interval} onChange={e => setNewWorker((w: any) => ({ ...w, closing_interval: Number(e.target.value) }))} fullWidth sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Checkbox checked={!!newWorker.officer} onChange={e => setNewWorker((w: any) => ({ ...w, officer: e.target.checked }))} /> Officer
          </Box>
          <TextField label="Seniority" value={newWorker.seniority} onChange={e => setNewWorker((w: any) => ({ ...w, seniority: e.target.value }))} fullWidth sx={{ mb: 2 }} />
          <TextField label="Score" type="number" value={newWorker.score} onChange={e => setNewWorker((w: any) => ({ ...w, score: Number(e.target.value) }))} fullWidth sx={{ mb: 2 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialog(false)}>Cancel</Button>
          <Button onClick={handleAdd} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>
    </PageContainer>
  );
}

export default UpdateWorkersPage; 