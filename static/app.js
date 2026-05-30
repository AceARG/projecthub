'use strict';

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Theme Engine
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
const THEMES = {
  medieval: {
    dark: {
      '--bg':'#0e0906','--surface':'#1e1008','--surface-2':'#2e180e',
      '--surface-3':'#3e2218','--border':'#5a3018',
      '--text':'#f0ddb0','--text-muted':'#9a7050',
      '--accent':'#c8920c','--accent-h':'#e0a820',
      '--success':'#3a6e30','--warning':'#b87020','--danger':'#9a1818',
    },
    light: {
      '--bg':'#f4e8c8','--surface':'#ecd8a8','--surface-2':'#e0c888',
      '--surface-3':'#d4b870','--border':'#b09040',
      '--text':'#1a0804','--text-muted':'#6a3820',
      '--accent':'#8b4500','--accent-h':'#a05a10',
      '--success':'#1e4e18','--warning':'#704008','--danger':'#600010',
    },
  },
  midnight: {
    dark: {
      '--bg':'#0d1117','--surface':'#161b22','--surface-2':'#21262d',
      '--surface-3':'#2d333b','--border':'#30363d',
      '--text':'#e6edf3','--text-muted':'#8b949e',
      '--accent':'#58a6ff','--accent-h':'#79c0ff',
      '--success':'#3fb950','--warning':'#d29922','--danger':'#f85149',
    },
    light: {
      '--bg':'#ffffff','--surface':'#f6f8fa','--surface-2':'#eaeef2',
      '--surface-3':'#d0d7de','--border':'#d0d7de',
      '--text':'#24292f','--text-muted':'#57606a',
      '--accent':'#0969da','--accent-h':'#0550ae',
      '--success':'#1a7f37','--warning':'#9a6700','--danger':'#cf222e',
    },
  },
  ocean: {
    dark: {
      '--bg':'#050f18','--surface':'#0a1e2d','--surface-2':'#0f2d40',
      '--surface-3':'#1a3d55','--border':'#1e4d6a',
      '--text':'#cce8f4','--text-muted':'#6899b5',
      '--accent':'#0fbfdc','--accent-h':'#30d5f0',
      '--success':'#1aaa7a','--warning':'#f0a050','--danger':'#f04060',
    },
    light: {
      '--bg':'#f0f8ff','--surface':'#e4f0fa','--surface-2':'#d0e8f5',
      '--surface-3':'#b8d8ee','--border':'#90c0e0',
      '--text':'#0a1e30','--text-muted':'#3a6a90',
      '--accent':'#0080a0','--accent-h':'#0090b8',
      '--success':'#007a55','--warning':'#b07000','--danger':'#c02040',
    },
  },
  forest: {
    dark: {
      '--bg':'#060e06','--surface':'#0e1c0e','--surface-2':'#162816',
      '--surface-3':'#1e3420','--border':'#2a4a2c',
      '--text':'#c8e8c0','--text-muted':'#6a9860',
      '--accent':'#4caf50','--accent-h':'#66bb6a',
      '--success':'#81c784','--warning':'#ffb74d','--danger':'#e57373',
    },
    light: {
      '--bg':'#f0f8f0','--surface':'#e4f0e4','--surface-2':'#d4e8d4',
      '--surface-3':'#c0d8c0','--border':'#90b890',
      '--text':'#0a1e0a','--text-muted':'#3a6a3a',
      '--accent':'#2e7d32','--accent-h':'#388e3c',
      '--success':'#1b5e20','--warning':'#e65100','--danger':'#b71c1c',
    },
  },
};

let _theme = 'medieval';
let _mode  = 'dark';

function applyTheme(theme, mode) {
  const vars = THEMES[theme]?.[mode];
  if (!vars) return;
  const root = document.documentElement;
  for (const [k, v] of Object.entries(vars)) root.style.setProperty(k, v);
  _theme = theme; _mode = mode;

  document.querySelectorAll('.swatch').forEach(s =>
    s.classList.toggle('active', s.dataset.theme === theme));

  document.querySelectorAll('.mode-toggle').forEach(btn =>
    btn.textContent = mode === 'dark' ? '☀️' : '🌙');

  localStorage.setItem('ph-theme', theme);
  localStorage.setItem('ph-mode',  mode);
}

function initTheme() {
  const t = localStorage.getItem('ph-theme') || 'medieval';
  const m = localStorage.getItem('ph-mode')  || 'dark';
  applyTheme(t, m);

  document.querySelectorAll('.swatch').forEach(s =>
    s.addEventListener('click', () => applyTheme(s.dataset.theme, _mode)));

  document.querySelectorAll('.mode-toggle').forEach(btn =>
    btn.addEventListener('click', () => applyTheme(_theme, _mode === 'dark' ? 'light' : 'dark')));
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Constants
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
const STATUS_INFO = {
  'todo':        { label: 'Todo',        cls: 'sb-todo' },
  'in-progress': { label: 'In Progress', cls: 'sb-in-progress' },
  'testing':     { label: 'Testing',     cls: 'sb-testing' },
  'done':        { label: 'Done',        cls: 'sb-done' },
  'backlog':     { label: 'Backlog',     cls: 'sb-backlog' },
};

const BL_STATUS_CLS = {
  'backlog':     's-backlog',
  'todo':        's-todo',
  'in-progress': 's-inprog',
  'testing':     's-testing',
  'done':        's-done',
};

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Utils
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}

function htmlToEl(html) {
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Modal System
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function openModal(id) {
  document.getElementById(id).classList.add('open');
  const first = document.querySelector(`#${id} input:not([type=hidden]), #${id} textarea`);
  if (first) setTimeout(() => first.focus(), 50);
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
});

// â”€â”€ Type toggle (delegated, works in any modal) â”€â”€
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.type-toggle-btn');
  if (!btn) return;
  const group = btn.closest('.type-toggle');
  if (!group) return;
  group.querySelectorAll('.type-toggle-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // Sync the hidden input that follows the toggle group
  const hidden = group.parentElement?.querySelector('input[type="hidden"]');
  if (hidden) hidden.value = btn.dataset.type;
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Color Picker (dashboard)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initColorPicker() {
  document.querySelectorAll('#new-color-picker .color-option').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('#new-color-picker .color-option').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      const inp = document.getElementById('selected-color');
      if (inp) inp.value = opt.dataset.color;
    });
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Delete project
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initDeleteProject() {
  document.querySelectorAll('tr.project-row, tr.ins-row').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('.edit-project-btn, .delete-project-btn')) return;
      if (row.dataset.href) location.href = row.dataset.href;
    });
  });

  document.querySelectorAll('.delete-project-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = btn.dataset.projectId;
      if (!confirm('Delete this project and all its tasks?')) return;
      const res = await fetch(`/projects/${id}`, { method: 'DELETE' });
      if (res.ok) {
        const row = btn.closest('tr') || btn.closest('.project-card-wrapper');
        if (row) {
          row.style.transition = 'opacity .2s';
          row.style.opacity = '0';
          setTimeout(() => {
            row.remove();
            if (!document.querySelectorAll('tr.project-row').length) location.reload();
          }, 200);
        }
      }
    });
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Edit Project
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initEditProject() {
  document.querySelectorAll('.edit-project-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      document.getElementById('edit-project-id').value          = btn.dataset.projectId;
      document.getElementById('edit-project-name').value        = btn.dataset.name;
      document.getElementById('edit-project-description').value = btn.dataset.description;
      document.getElementById('edit-project-color').value       = btn.dataset.color;
      const repoEl   = document.getElementById('edit-project-repo');
      if (repoEl) repoEl.value = btn.dataset.repo || '';
      const prefixEl = document.getElementById('edit-project-prefix');
      if (prefixEl) prefixEl.value = btn.dataset.prefix || '';

      document.querySelectorAll('#edit-color-picker .color-option').forEach(opt => {
        opt.classList.toggle('selected', opt.dataset.color === btn.dataset.color);
      });

      openModal('edit-project-modal');
    });
  });

  document.querySelectorAll('#edit-color-picker .color-option').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('#edit-color-picker .color-option').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      document.getElementById('edit-project-color').value = opt.dataset.color;
    });
  });

  document.getElementById('edit-project-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id          = document.getElementById('edit-project-id').value;
    const name        = document.getElementById('edit-project-name').value.trim();
    const description = document.getElementById('edit-project-description').value.trim();
    const color       = document.getElementById('edit-project-color').value;
    const repo_path     = document.getElementById('edit-project-repo')?.value.trim() || '';
    const ticket_prefix = document.getElementById('edit-project-prefix')?.value.trim().toUpperCase() || '';
    if (!name) return;

    try {
      const project = await fetch(`/projects/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description, color, repo_path, ticket_prefix }),
      }).then(r => r.json());

      closeModal('edit-project-modal');

      const row = document.querySelector(`tr.project-row[data-href="/projects/${id}"]`);
      if (row) {
        const nameEl  = row.querySelector('.proj-name');
        const bar     = row.querySelector('.proj-color-bar');
        const descEl  = row.querySelector('.proj-desc-text');
        const editBtn = row.querySelector('.edit-project-btn');
        if (nameEl)  nameEl.textContent = project.name;
        if (bar)     bar.style.background = project.color;
        if (descEl)  descEl.textContent = project.description || '—';
        if (editBtn) {
          editBtn.dataset.name        = project.name;
          editBtn.dataset.description = project.description || '';
          editBtn.dataset.color       = project.color;
          editBtn.dataset.repo        = project.repo_path || '';
          editBtn.dataset.prefix      = project.ticket_prefix || '';
        }
      }
    } catch (err) {
      console.error('edit project failed', err);
    }
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// HTML Builders
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function makeCardHTML(task) {
  const taskType = task.type || 'task';
  const bugBadge = taskType === 'bug' ? `<span class="type-badge type-bug">🐛 Bug</span>` : '';
  return `<div class="task-card" data-task-id="${task.id}" data-status="${escapeHtml(task.status || '')}" data-type="${taskType}" draggable="true">
    <div class="task-card-header">
      <span class="priority-dot ${escapeHtml(task.priority)}"></span>
      <h4 class="task-title">${escapeHtml(task.title)}</h4>
      <div class="task-card-actions">
        <button class="btn-icon task-edit-btn" data-task-id="${task.id}" title="Edit">✎</button>
        <button class="btn-icon task-delete-btn" data-task-id="${task.id}" title="Delete">×</button>
      </div>
    </div>
    ${task.description ? `<p class="task-desc">${escapeHtml(task.description)}</p>` : ''}
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
      ${task.ticket_id ? `<span class="ticket-id">${escapeHtml(task.ticket_id)}</span>` : ''}
      ${bugBadge}
    </div>
  </div>`;
}

function makeBacklogItemHTML(task) {
  const taskType = task.type || 'task';
  const bugBadge = taskType === 'bug' ? `<span class="type-badge type-bug">🐛 Bug</span>` : '';
  const selCls = BL_STATUS_CLS[task.status] || 's-backlog';
  const opts = ['backlog','todo','in-progress','testing','done'].map(v =>
    `<option value="${v}"${task.status === v ? ' selected' : ''}>${STATUS_INFO[v]?.label || v}</option>`
  ).join('');
  return `<div class="backlog-item" data-task-id="${task.id}" data-status="${escapeHtml(task.status)}" data-type="${taskType}">
    <span class="priority-dot ${escapeHtml(task.priority)}"></span>
    ${task.ticket_id ? `<span class="ticket-id">${escapeHtml(task.ticket_id)}</span>` : ''}
    ${bugBadge}
    <div class="backlog-item-info">
      <div class="backlog-item-title">${escapeHtml(task.title)}</div>
      ${task.description ? `<div class="backlog-item-desc">${escapeHtml(task.description)}</div>` : ''}
    </div>
    <select class="bl-status-select ${selCls}" data-task-id="${task.id}">${opts}</select>
    <span class="priority-badge ${escapeHtml(task.priority)}">${escapeHtml(task.priority)}</span>
    <button class="btn-icon task-edit-btn" data-task-id="${task.id}" title="Edit">✎</button>
    <button class="btn-icon task-delete-btn" data-task-id="${task.id}" title="Delete">×</button>
  </div>`;
}

function makePhaseTaskCardHTML(task, phaseId) {
  const si = STATUS_INFO[task.status] || STATUS_INFO.backlog;
  const pid = phaseId != null ? phaseId : '';
  const taskType = task.type || 'task';
  const bugBadge = taskType === 'bug' ? `<span class="type-badge type-bug">🐛 Bug</span>` : '';
  return `<div class="phase-task-card" data-task-id="${task.id}" data-phase-id="${pid}" data-type="${taskType}" draggable="true">
    <div class="phase-task-header">
      <span class="priority-dot ${escapeHtml(task.priority)}"></span>
      <span class="phase-task-title">${escapeHtml(task.title)}</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;margin-top:2px;flex-wrap:wrap;">
      ${task.ticket_id ? `<span class="ticket-id">${escapeHtml(task.ticket_id)}</span>` : ''}
      <span class="status-badge ${si.cls}">${si.label}</span>
      ${bugBadge}
    </div>
  </div>`;
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// API helpers
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
async function apiGetTask(taskId) {
  const res = await fetch(`/tasks/${taskId}`);
  if (!res.ok) throw new Error('fetch task failed');
  return res.json();
}

async function apiCreateTask(projectId, payload) {
  const res = await fetch(`/projects/${projectId}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('create task failed');
  return res.json();
}

async function apiUpdateTask(taskId, payload) {
  const res = await fetch(`/tasks/${taskId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('update task failed');
  return res.json();
}

async function apiDeleteTask(taskId) {
  const res = await fetch(`/tasks/${taskId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('delete task failed');
  return res.json();
}

async function apiCreatePlan(projectId, payload) {
  const res = await fetch(`/projects/${projectId}/plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('create plan failed');
  return res.json();
}

async function apiGetPlan(planId) {
  const res = await fetch(`/plans/${planId}`);
  if (!res.ok) throw new Error('get plan failed');
  return res.json();
}

async function apiUpdatePlan(planId, payload) {
  const res = await fetch(`/plans/${planId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('update plan failed');
  return res.json();
}

async function apiDeletePlan(planId) {
  const res = await fetch(`/plans/${planId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('delete plan failed');
  return res.json();
}

async function apiGetPlanMessages(planId, step) {
  const res = await fetch(`/plans/${planId}/messages?step=${step}`);
  if (!res.ok) throw new Error('get messages failed');
  return res.json();
}

async function apiPostPlanMessage(planId, step, content) {
  const res = await fetch(`/plans/${planId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step, content }),
  });
  if (!res.ok) throw new Error('post message failed');
  return res.json();
}

async function apiCreateTasksFromPlan(planId, tasks) {
  const res = await fetch(`/plans/${planId}/create-tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tasks }),
  });
  if (!res.ok) throw new Error('create tasks from plan failed');
  return res.json();
}

async function apiTriggerAgent(planId, step) {
  const res = await fetch(`/plans/${planId}/run-step?step=${step}`, { method: 'POST' });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Agent trigger failed');
  }
  return res.json();
}

async function apiAutoCreateTasks(planId) {
  const res = await fetch(`/plans/${planId}/auto-create-tasks`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'auto create tasks failed');
  }
  return res.json();
}

async function apiCreatePhase(projectId, payload) {
  const res = await fetch(`/projects/${projectId}/phases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('create phase failed');
  return res.json();
}

async function apiUpdatePhase(phaseId, payload) {
  const res = await fetch(`/phases/${phaseId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('update phase failed');
  return res.json();
}

async function apiDeletePhase(phaseId) {
  const res = await fetch(`/phases/${phaseId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('delete phase failed');
  return res.json();
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Count helpers
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function refreshColumnCount(status) {
  const col = document.querySelector(`.kanban-column[data-status="${status}"]`);
  if (!col) return;
  col.querySelector('.column-count').textContent = col.querySelectorAll('.task-card').length;
}

function refreshBacklogCount() {
  const list = document.getElementById('backlog-list');
  if (!list) return;
  const n = list.querySelectorAll('.backlog-item').length;
  const el = document.getElementById('backlog-item-count');
  if (el) el.textContent = n;
  const empty = document.getElementById('backlog-empty');
  if (empty) empty.style.display = n === 0 ? '' : 'none';
}

function refreshPhaseColCount(phaseId) {
  const colId  = phaseId != null && phaseId !== '' ? `phase-col-${phaseId}` : 'phase-col-unassigned';
  const cntId  = phaseId != null && phaseId !== '' ? `phase-count-${phaseId}` : 'phase-count-unassigned';
  const cards  = document.getElementById(colId)?.querySelectorAll('.phase-task-card').length || 0;
  const cntEl  = document.getElementById(cntId);
  if (cntEl) cntEl.textContent = cards;

  // Show/hide empty placeholder
  const col = document.getElementById(colId);
  if (!col) return;
  let empty = col.querySelector('.phase-col-empty');
  if (cards === 0) {
    if (!empty) {
      empty = document.createElement('div');
      empty.className = 'phase-col-empty';
      empty.textContent = phaseId ? 'Drop tasks here' : 'Drop tasks here to unassign';
      col.appendChild(empty);
    }
  } else if (empty) {
    empty.remove();
  }
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Fade-remove
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function fadeRemove(el, cb) {
  if (!el) return;
  el.style.transition = 'opacity .15s, transform .15s';
  el.style.opacity = '0';
  el.style.transform = 'scale(.95)';
  setTimeout(() => { el.remove(); if (cb) cb(); }, 160);
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// applyTaskEdit — full DOM sync after any edit
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function applyTaskEdit(taskId, oldStatus, oldPhaseId, task) {
  const newStatus  = task.status;
  const newPhaseId = task.phase_id != null ? task.phase_id : null;
  const wasBoard   = oldStatus  !== 'backlog';
  const isBoard    = newStatus  !== 'backlog';

  // â”€â”€â”€ Kanban card â”€â”€â”€
  const card = document.querySelector(`.kanban-column .task-card[data-task-id="${taskId}"]`);

  if (wasBoard && isBoard) {
    if (oldStatus === newStatus) {
      if (card) card.replaceWith(htmlToEl(makeCardHTML(task)));
    } else {
      if (card) fadeRemove(card, () => refreshColumnCount(oldStatus));
      const dest = document.querySelector(`.kanban-column[data-status="${newStatus}"] .cards-container`);
      if (dest) { dest.insertAdjacentHTML('afterbegin', makeCardHTML(task)); refreshColumnCount(newStatus); }
    }
  } else if (wasBoard && !isBoard) {
    if (card) fadeRemove(card, () => refreshColumnCount(oldStatus));
  } else if (!wasBoard && isBoard) {
    const dest = document.querySelector(`.kanban-column[data-status="${newStatus}"] .cards-container`);
    if (dest) { dest.insertAdjacentHTML('afterbegin', makeCardHTML(task)); refreshColumnCount(newStatus); }
  }

  // â”€â”€â”€ Backlog list (phase-grouped) â”€â”€â”€
  const blItem = document.querySelector(`#tab-backlog .backlog-item[data-task-id=”${taskId}”]`);
  const oldPid = oldPhaseId != null ? String(oldPhaseId) : '';
  const newPid = newPhaseId != null ? String(newPhaseId) : '';

  if (oldPid === newPid) {
    if (blItem) blItem.replaceWith(htmlToEl(makeBacklogItemHTML(task)));
  } else {
    if (blItem) blItem.remove();
    const targetId = newPid ? `bl-phase-${newPid}` : 'bl-unassigned';
    const targetList = document.getElementById(targetId);
    if (targetList) {
      const emptyMsg = targetList.querySelector('.backlog-empty-sub');
      if (emptyMsg) emptyMsg.remove();
      targetList.insertAdjacentHTML('afterbegin', makeBacklogItemHTML(task));
    }
  }

  // â”€â”€â”€ Phase board â”€â”€â”€
  const phaseCard = document.querySelector(`.phase-task-card[data-task-id=”${taskId}”]`);

  if (oldPid === newPid) {
    // Same phase — just update the status badge in place
    if (phaseCard) phaseCard.replaceWith(htmlToEl(makePhaseTaskCardHTML(task, newPhaseId)));
  } else {
    // Phase changed — move card
    if (phaseCard) {
      phaseCard.remove();
      refreshPhaseColCount(oldPid);
    }
    const newColId  = newPid ? `phase-col-${newPid}` : 'phase-col-unassigned';
    const newColEl  = document.getElementById(newColId);
    if (newColEl) {
      newColEl.insertAdjacentHTML('afterbegin', makePhaseTaskCardHTML(task, newPhaseId));
      refreshPhaseColCount(newPid);
    }
  }
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Edit Task
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
let _editOldStatus  = null;
let _editOldPhaseId = null;

function initEditTask() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.task-edit-btn');
    if (!btn) return;

    const taskId = btn.dataset.taskId;
    try {
      const task = await apiGetTask(taskId);
      _editOldStatus  = task.status;
      _editOldPhaseId = task.phase_id != null ? task.phase_id : null;

      document.getElementById('edit-task-id').value          = task.id;
      document.getElementById('edit-task-title').value       = task.title;
      document.getElementById('edit-task-description').value = task.description || '';
      document.getElementById('edit-task-status').value      = task.status;
      document.getElementById('edit-task-priority').value    = task.priority;

      // Set type toggle
      const editType = task.type || 'task';
      const editTypeHidden = document.getElementById('edit-task-type');
      if (editTypeHidden) editTypeHidden.value = editType;
      document.querySelectorAll('#edit-task-type-toggle .type-toggle-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.type === editType);
      });

      const phaseEl = document.getElementById('edit-task-phase');
      if (phaseEl) phaseEl.value = task.phase_id != null ? String(task.phase_id) : '';

      openModal('edit-task-modal');
    } catch (err) {
      console.error('edit open failed', err);
    }
  });

  document.getElementById('edit-task-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const taskId      = document.getElementById('edit-task-id').value;
    const title       = document.getElementById('edit-task-title').value.trim();
    const description = document.getElementById('edit-task-description').value.trim();
    const status      = document.getElementById('edit-task-status').value;
    const priority    = document.getElementById('edit-task-priority').value;
    const type        = document.getElementById('edit-task-type')?.value || 'task';
    if (!title) return;

    const phaseVal = document.getElementById('edit-task-phase')?.value;
    const phase_id = phaseVal ? parseInt(phaseVal) : null;

    try {
      const task = await apiUpdateTask(taskId, { title, description, status, priority, type, phase_id });
      closeModal('edit-task-modal');
      applyTaskEdit(taskId, _editOldStatus, _editOldPhaseId, task);
      _editOldStatus  = null;
      _editOldPhaseId = null;
    } catch (err) {
      console.error('edit save failed', err);
    }
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Delete Task (delegated)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initDeleteTask() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.task-delete-btn');
    if (!btn) return;

    const taskId    = btn.dataset.taskId;
    const card      = document.querySelector(`.kanban-column .task-card[data-task-id="${taskId}"]`);
    const bItem     = document.querySelector(`.backlog-item[data-task-id="${taskId}"]`);
    const phCard    = document.querySelector(`.phase-task-card[data-task-id="${taskId}"]`);
    const colStatus = card?.closest('.kanban-column')?.dataset.status;
    const oldPid    = phCard?.dataset.phaseId;

    try {
      await apiDeleteTask(taskId);
      if (card)   fadeRemove(card,   () => refreshColumnCount(colStatus));
      if (bItem)  fadeRemove(bItem);
      if (phCard) fadeRemove(phCard, () => refreshPhaseColCount(oldPid));
    } catch (err) {
      console.error(err);
    }
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Drag & Drop (kanban)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initDragDrop() {
  const board = document.getElementById('kanban-board');
  if (!board) return;

  board.addEventListener('dragstart', (e) => {
    const card = e.target.closest('.task-card');
    if (!card) return;
    e.dataTransfer.setData('text/plain', card.dataset.taskId);
    e.dataTransfer.effectAllowed = 'move';
    requestAnimationFrame(() => card.classList.add('dragging'));
  });

  board.addEventListener('dragend', () => {
    document.querySelectorAll('.task-card.dragging').forEach(c => c.classList.remove('dragging'));
    document.querySelectorAll('.cards-container').forEach(c => c.classList.remove('drag-over'));
  });

  document.querySelectorAll('.cards-container').forEach(container => {
    container.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      container.classList.add('drag-over');
    });

    container.addEventListener('dragleave', (e) => {
      if (!container.contains(e.relatedTarget)) container.classList.remove('drag-over');
    });

    container.addEventListener('drop', async (e) => {
      e.preventDefault();
      container.classList.remove('drag-over');

      const taskId    = e.dataTransfer.getData('text/plain');
      const card      = document.querySelector(`.task-card[data-task-id="${taskId}"]`);
      if (!card) return;

      const newStatus = container.closest('.kanban-column').dataset.status;
      const oldStatus = card.closest('.kanban-column')?.dataset.status;
      if (oldStatus === newStatus) return;

      container.appendChild(card);
      card.dataset.status = newStatus;
      if (oldStatus) refreshColumnCount(oldStatus);
      refreshColumnCount(newStatus);

      // Sync backlog status select
      const blSel = document.querySelector(`#tab-backlog .bl-status-select[data-task-id="${taskId}"]`);
      if (blSel) {
        blSel.value = newStatus;
        blSel.className = `bl-status-select ${BL_STATUS_CLS[newStatus] || ''}`;
        const blItem = blSel.closest('.backlog-item');
        if (blItem) blItem.dataset.status = newStatus;
      }

      // Sync phase board status badge
      const phCard = document.querySelector(`.phase-task-card[data-task-id="${taskId}"]`);
      if (phCard) {
        const si = STATUS_INFO[newStatus];
        if (si) {
          const badge = phCard.querySelector('.status-badge');
          if (badge) { badge.textContent = si.label; badge.className = `status-badge ${si.cls}`; }
        }
      }

      try {
        await apiUpdateTask(taskId, { status: newStatus });
      } catch (err) {
        console.error(err);
      }
    });
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Phase board drag & drop
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initPhaseDragDrop() {
  const board = document.getElementById('phase-board');
  if (!board) return;

  board.addEventListener('dragstart', (e) => {
    const card = e.target.closest('.phase-task-card');
    if (!card) return;
    e.dataTransfer.setData('phase-task', card.dataset.taskId);
    e.dataTransfer.effectAllowed = 'move';
    requestAnimationFrame(() => card.classList.add('dragging'));
  });

  board.addEventListener('dragend', () => {
    document.querySelectorAll('.phase-task-card.dragging').forEach(c => c.classList.remove('dragging'));
    document.querySelectorAll('.phase-cards').forEach(c => c.classList.remove('drag-over'));
  });

  // Wire all phase-cards containers as drop zones
  function wireDropZones() {
    document.querySelectorAll('.phase-cards').forEach(container => {
      if (container._phaseDropWired) return;
      container._phaseDropWired = true;

      container.addEventListener('dragover', (e) => {
        // Only accept phase-task drags
        if (!e.dataTransfer.types.includes('phase-task')) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        container.classList.add('drag-over');
      });

      container.addEventListener('dragleave', (e) => {
        if (!container.contains(e.relatedTarget)) container.classList.remove('drag-over');
      });

      container.addEventListener('drop', async (e) => {
        e.preventDefault();
        container.classList.remove('drag-over');

        const taskId = e.dataTransfer.getData('phase-task');
        if (!taskId) return;

        const card = document.querySelector(`.phase-task-card[data-task-id="${taskId}"]`);
        if (!card) return;

        const newColEl  = container;
        const newPid    = newColEl.closest('.phase-col')?.dataset.phaseId ?? '';
        const oldPid    = card.dataset.phaseId ?? '';

        if (oldPid === newPid) return;

        // Move card in DOM
        card.dataset.phaseId = newPid;
        newColEl.insertAdjacentHTML('afterbegin', card.outerHTML);
        card.remove();
        refreshPhaseColCount(oldPid);
        refreshPhaseColCount(newPid);

        // Update API: null = unassign, int = assign
        const apiPhaseId = newPid !== '' ? parseInt(newPid) : null;
        try {
          await apiUpdateTask(taskId, { phase_id: apiPhaseId });
        } catch (err) {
          console.error(err);
        }
      });
    });
  }

  wireDropZones();
  // Expose so new phase columns can be wired after dynamic creation
  board._wireDropZones = wireDropZones;
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Add Task modal
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initAddTask(projectId) {
  if (!document.getElementById('task-modal')) return;

  document.querySelectorAll('.add-card-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('task-status').value = btn.dataset.status;
      openModal('task-modal');
    });
  });

  document.getElementById('add-backlog-task-btn')?.addEventListener('click', () => {
    document.getElementById('task-status').value = 'backlog';
    openModal('task-modal');
  });

  document.getElementById('task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title       = document.getElementById('task-title').value.trim();
    const description = document.getElementById('task-description').value.trim();
    const status      = document.getElementById('task-status').value;
    const priority    = document.getElementById('task-priority').value;
    const type        = document.getElementById('task-type')?.value || 'task';
    const phaseVal    = document.getElementById('task-phase')?.value;
    const phase_id    = phaseVal ? parseInt(phaseVal) : null;
    if (!title) return;

    try {
      const task = await apiCreateTask(projectId, { title, description, status, priority, type, phase_id });
      closeModal('task-modal');
      e.target.reset();
      document.getElementById('task-status').value = 'todo';
      // Reset type toggle to "task"
      const typeHidden = document.getElementById('task-type');
      if (typeHidden) typeHidden.value = 'task';
      document.querySelectorAll('#task-type-toggle .type-toggle-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.type === 'task');
      });

      if (status !== 'backlog') {
        const col = document.querySelector(`.kanban-column[data-status="${status}"] .cards-container`);
        if (col) { col.insertAdjacentHTML('afterbegin', makeCardHTML(task)); refreshColumnCount(status); }
      }

      // Add to phase-grouped backlog
      const blTargetId = phase_id ? `bl-phase-${phase_id}` : 'bl-unassigned';
      const blTarget = document.getElementById(blTargetId);
      if (blTarget) {
        const emptyMsg = blTarget.querySelector('.backlog-empty-sub');
        if (emptyMsg) emptyMsg.remove();
        blTarget.insertAdjacentHTML('afterbegin', makeBacklogItemHTML(task));
      }

      // Add to phase board
      if (phase_id != null) {
        const phaseCol = document.getElementById(`phase-col-${phase_id}`);
        if (phaseCol) {
          phaseCol.insertAdjacentHTML('afterbegin', makePhaseTaskCardHTML(task, phase_id));
          refreshPhaseColCount(String(phase_id));
        }
      } else {
        const unassigned = document.getElementById('phase-col-unassigned');
        if (unassigned) {
          unassigned.insertAdjacentHTML('afterbegin', makePhaseTaskCardHTML(task, null));
          refreshPhaseColCount('');
        }
      }
    } catch (err) {
      console.error(err);
    }
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Move to Board (backlog → todo)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initBacklogStatusSelect() {
  document.addEventListener('change', async (e) => {
    const sel = e.target.closest('.bl-status-select');
    if (!sel) return;

    const taskId = sel.dataset.taskId;
    const newStatus = sel.value;
    const blItem = sel.closest('.backlog-item');
    const oldStatus = blItem?.dataset.status;
    if (oldStatus === newStatus) return;

    try {
      const task = await apiUpdateTask(taskId, { status: newStatus });

      sel.className = `bl-status-select ${BL_STATUS_CLS[newStatus] || ''}`;
      if (blItem) blItem.dataset.status = newStatus;

      // Sync kanban board
      const card = document.querySelector(`.kanban-column .task-card[data-task-id="${taskId}"]`);
      if (newStatus === 'backlog') {
        if (card) fadeRemove(card, () => refreshColumnCount(oldStatus));
      } else if (oldStatus === 'backlog') {
        const dest = document.querySelector(`.kanban-column[data-status="${newStatus}"] .cards-container`);
        if (dest) { dest.insertAdjacentHTML('afterbegin', makeCardHTML(task)); refreshColumnCount(newStatus); }
      } else if (card) {
        const dest = document.querySelector(`.kanban-column[data-status="${newStatus}"] .cards-container`);
        if (dest) { dest.appendChild(card); card.dataset.status = newStatus; }
        if (oldStatus) refreshColumnCount(oldStatus);
        refreshColumnCount(newStatus);
      }

      // Sync phase task card status badge
      const phCard = document.querySelector(`.phase-task-card[data-task-id="${taskId}"]`);
      if (phCard) {
        const si = STATUS_INFO[newStatus];
        if (si) {
          const badge = phCard.querySelector('.status-badge');
          if (badge) { badge.textContent = si.label; badge.className = `status-badge ${si.cls}`; }
        }
      }
    } catch (err) {
      console.error('status update failed', err);
      if (sel && oldStatus) sel.value = oldStatus;
    }
  });
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Phases CRUD
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function makePhaseBadgeHTML(status) {
  return `<span class="phase-badge ps-${status}">${status}</span>`;
}

function makePhaseRowHTML(ph) {
  const pct = ph.task_count ? Math.round((ph.done_count || 0) / ph.task_count * 100) : 0;
  return `<tr class="phase-row" data-phase-id="${ph.id}">
    <td>
      <div class="phase-name-cell">
        <span class="phase-status-dot ps-dot-${ph.status}"></span>
        <span class="phase-row-name">${escapeHtml(ph.name)}</span>
        ${ph.description ? `<span class="phase-row-desc">${escapeHtml(ph.description)}</span>` : ''}
      </div>
    </td>
    <td>${makePhaseBadgeHTML(ph.status)}</td>
    <td class="ph-num">${ph.task_count || 0}</td>
    <td>
      <div class="tbl-progress-wrap">
        <div class="tbl-progress-bar">
          <div class="tbl-progress-fill" style="width:${pct}%"></div>
        </div>
        <span class="tbl-pct">${pct}%</span>
      </div>
    </td>
    <td>
      <div class="row-actions">
        <button class="btn-icon phase-edit-btn"
                data-phase-id="${ph.id}"
                data-name="${escapeHtml(ph.name)}"
                data-description="${escapeHtml(ph.description || '')}"
                data-status="${ph.status}"
                title="Edit phase">✎</button>
        <button class="btn-icon phase-delete-btn"
                data-phase-id="${ph.id}"
                title="Delete phase">×</button>
      </div>
    </td>
  </tr>`;
}

function makePhaseColHTML(ph) {
  return `<div class="phase-col" data-phase-id="${ph.id}" id="phase-col-container-${ph.id}">
    <div class="phase-col-header">
      <div class="phase-col-title-group">
        <span class="phase-col-dot ps-dot-${ph.status}"></span>
        <span class="phase-col-title">${escapeHtml(ph.name)}</span>
      </div>
      <span class="phase-col-count" id="phase-count-${ph.id}">0</span>
    </div>
    <div class="phase-cards" id="phase-col-${ph.id}">
      <div class="phase-col-empty">Drop tasks here</div>
    </div>
  </div>`;
}

function makePhaseSelectOptionHTML(ph) {
  return `<option value="${ph.id}">${escapeHtml(ph.name)}</option>`;
}

function initPhases(projectId) {
  let _editingPhaseId = null;

  // â”€â”€ Open "New Phase" modal â”€â”€
  document.getElementById('new-phase-btn')?.addEventListener('click', () => {
    _editingPhaseId = null;
    document.getElementById('phase-modal-title').textContent  = 'New Phase';
    document.getElementById('phase-modal-submit').textContent = 'Create Phase';
    document.getElementById('phase-modal-id').value           = '';
    document.getElementById('phase-modal-name').value         = '';
    document.getElementById('phase-modal-description').value  = '';
    document.getElementById('phase-modal-status').value       = 'planned';
    openModal('phase-modal');
  });

  // â”€â”€ Open "Edit Phase" modal (delegated) â”€â”€
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.phase-edit-btn');
    if (!btn) return;
    _editingPhaseId = btn.dataset.phaseId;
    document.getElementById('phase-modal-title').textContent  = 'Edit Phase';
    document.getElementById('phase-modal-submit').textContent = 'Save Changes';
    document.getElementById('phase-modal-id').value           = btn.dataset.phaseId;
    document.getElementById('phase-modal-name').value         = btn.dataset.name;
    document.getElementById('phase-modal-description').value  = btn.dataset.description;
    document.getElementById('phase-modal-status').value       = btn.dataset.status;
    openModal('phase-modal');
  });

  // â”€â”€ Save phase (create or update) â”€â”€
  document.getElementById('phase-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name        = document.getElementById('phase-modal-name').value.trim();
    const description = document.getElementById('phase-modal-description').value.trim();
    const status      = document.getElementById('phase-modal-status').value;
    if (!name) return;

    try {
      if (_editingPhaseId) {
        // â”€â”€ Update â”€â”€
        const ph = await apiUpdatePhase(_editingPhaseId, { name, description, status });
        closeModal('phase-modal');

        // Update table row
        const row = document.querySelector(`.phase-row[data-phase-id="${ph.id}"]`);
        if (row) {
          row.querySelector('.phase-status-dot').className = `phase-status-dot ps-dot-${ph.status}`;
          row.querySelector('.phase-row-name').textContent = ph.name;
          const descEl = row.querySelector('.phase-row-desc');
          if (ph.description) {
            if (descEl) descEl.textContent = ph.description;
            else row.querySelector('.phase-name-cell').insertAdjacentHTML('beforeend',
              `<span class="phase-row-desc">${escapeHtml(ph.description)}</span>`);
          } else if (descEl) descEl.remove();
          const badge = row.querySelector('.phase-badge');
          if (badge) { badge.textContent = ph.status; badge.className = `phase-badge ps-${ph.status}`; }
          const editBtn = row.querySelector('.phase-edit-btn');
          if (editBtn) {
            editBtn.dataset.name        = ph.name;
            editBtn.dataset.description = ph.description || '';
            editBtn.dataset.status      = ph.status;
          }
        }

        // Update phase board column header
        const colDot   = document.querySelector(`#phase-col-container-${ph.id} .phase-col-dot`);
        const colTitle = document.querySelector(`#phase-col-container-${ph.id} .phase-col-title`);
        if (colDot)   colDot.className   = `phase-col-dot ps-dot-${ph.status}`;
        if (colTitle) colTitle.textContent = ph.name;

        // Update phase-select options
        document.querySelectorAll(`.phase-select option[value="${ph.id}"]`).forEach(opt => {
          opt.textContent = ph.name;
        });

      } else {
        // â”€â”€ Create â”€â”€
        const ph = await apiCreatePhase(projectId, { name, description, status });
        closeModal('phase-modal');

        // Hide empty state if first phase
        const emptyState = document.getElementById('phases-empty-state');
        if (emptyState) {
          emptyState.remove();
          // Show table and board (were hidden by empty state)
          const tabContent = document.getElementById('tab-phases');
          if (!document.getElementById('phases-table-wrap')) {
            tabContent.insertAdjacentHTML('beforeend',
              `<div class="phases-table-wrap" id="phases-table-wrap">
                <table class="phases-table" id="phases-table">
                  <thead><tr>
                    <th>Phase</th><th>Status</th>
                    <th class="ph-num">Tasks</th>
                    <th style="width:200px;">Completion</th>
                    <th></th>
                  </tr></thead>
                  <tbody id="phases-tbody"></tbody>
                </table>
              </div>
              <div class="phase-planning-label">Task Assignment</div>
              <div class="phase-board" id="phase-board">
                <div class="phase-col" data-phase-id="" id="phase-col-container-unassigned">
                  <div class="phase-col-header">
                    <div class="phase-col-title-group">
                      <span class="phase-col-dot unassigned-dot"></span>
                      <span class="phase-col-title">Unassigned</span>
                    </div>
                    <span class="phase-col-count" id="phase-count-unassigned">0</span>
                  </div>
                  <div class="phase-cards" id="phase-col-unassigned">
                    <div class="phase-col-empty">Drop tasks here to unassign</div>
                  </div>
                </div>
              </div>`
            );
            // Move all tasks to unassigned col & re-wire drag drop
            _populateUnassignedCol();
            initPhaseDragDrop();
          }
        }

        // Add row to table
        const tbody = document.getElementById('phases-tbody');
        if (tbody) tbody.insertAdjacentHTML('beforeend', makePhaseRowHTML(ph));

        // Add column to phase board
        const phaseBoard = document.getElementById('phase-board');
        if (phaseBoard) {
          phaseBoard.insertAdjacentHTML('beforeend', makePhaseColHTML(ph));
          // Wire drop zones on the new column
          phaseBoard._wireDropZones?.();
        }

        // Add option to phase selects
        const optHtml = makePhaseSelectOptionHTML(ph);
        document.querySelectorAll('.phase-select').forEach(sel => {
          sel.insertAdjacentHTML('beforeend', optHtml);
        });
      }
    } catch (err) {
      console.error('phase save failed', err);
    }
  });

  // â”€â”€ Delete phase (delegated) â”€â”€
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.phase-delete-btn');
    if (!btn) return;

    const phaseId = btn.dataset.phaseId;
    if (!confirm('Delete this phase? Tasks will be unassigned (not deleted).')) return;

    try {
      await apiDeletePhase(phaseId);

      // Move phase column tasks to unassigned
      const phaseCards = document.getElementById(`phase-col-${phaseId}`);
      const unassigned = document.getElementById('phase-col-unassigned');
      if (phaseCards && unassigned) {
        phaseCards.querySelectorAll('.phase-task-card').forEach(card => {
          card.dataset.phaseId = '';
          unassigned.appendChild(card);
        });
        refreshPhaseColCount('');
      }

      // Remove column
      document.getElementById(`phase-col-container-${phaseId}`)?.remove();

      // Remove table row
      document.querySelector(`.phase-row[data-phase-id="${phaseId}"]`)?.remove();

      // Remove from phase selects
      document.querySelectorAll(`.phase-select option[value="${phaseId}"]`).forEach(o => o.remove());

    } catch (err) {
      console.error('phase delete failed', err);
    }
  });
}

// Populate unassigned col with tasks that have no phase (used after dynamic board creation)
function _populateUnassignedCol() {
  const unassigned = document.getElementById('phase-col-unassigned');
  if (!unassigned) return;
  // Collect all task IDs already in phase columns
  const assigned = new Set(
    [...document.querySelectorAll('.phase-task-card[data-phase-id]:not([data-phase-id=""])')]
      .map(c => c.dataset.taskId)
  );
  // Get tasks from kanban+backlog that aren't assigned
  const allTaskCards = [
    ...document.querySelectorAll('.task-card[data-task-id]'),
    ...document.querySelectorAll('.backlog-item[data-task-id]'),
  ];
  const seen = new Set();
  allTaskCards.forEach(el => {
    const id = el.dataset.taskId;
    if (!assigned.has(id) && !seen.has(id)) {
      seen.add(id);
      const status = el.dataset.status || 'backlog';
      const title  = el.querySelector('.task-title, .backlog-item-title')?.textContent || '';
      const prio   = [...el.classList].find(c => ['high','medium','low'].includes(c)) ||
                     el.querySelector('.priority-dot')?.classList[1] || 'medium';
      const si     = STATUS_INFO[status] || STATUS_INFO.backlog;
      unassigned.insertAdjacentHTML('beforeend',
        `<div class="phase-task-card" data-task-id="${id}" data-phase-id="" draggable="true">
          <div class="phase-task-header">
            <span class="priority-dot ${prio}"></span>
            <span class="phase-task-title">${escapeHtml(title)}</span>
          </div>
          <span class="status-badge ${si.cls}">${si.label}</span>
        </div>`
      );
    }
  });
  refreshPhaseColCount('');
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Tabs
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initTabs() {
  function activateTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const btn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (btn) btn.classList.add('active');
    document.getElementById(`tab-${tabName}`)?.classList.add('active');
  }

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      activateTab(tab);
      sessionStorage.setItem('activeTab', tab);
      location.reload();
    });
  });

  // Restore last active tab on page load
  const saved = sessionStorage.getItem('activeTab');
  if (saved && document.querySelector(`.tab-btn[data-tab="${saved}"]`)) {
    activateTab(saved);
  }
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Init
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
function initBacklogCollapse() {
  const wrap = document.querySelector('.backlog-sections-wrap');
  if (!wrap) return;
  wrap.addEventListener('click', (e) => {
    const header = e.target.closest('.backlog-section-header');
    if (!header) return;
    // Don't collapse if user clicked a select or button inside the header
    if (e.target.closest('select, button')) return;
    header.closest('.backlog-section').classList.toggle('collapsed');
  });
}

function passwordStrength(pw) {
  let score = 0;
  if (pw.length >= 8)           score++;
  if (/[A-Z]/.test(pw))        score++;
  if (/[0-9]/.test(pw))        score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const colors = ['', '#f85149', '#f0a050', '#d29922', '#3fb950'];
  return { score, label: labels[score] || '', color: colors[score] || '' };
}

function updateStrengthBar(pw, barEl, labelEl) {
  if (!barEl || !labelEl) return;
  const { score, label, color } = passwordStrength(pw);
  barEl.style.width  = (score * 25) + '%';
  barEl.style.background = color;
  labelEl.textContent = pw ? label : '';
  labelEl.style.color = color;
}

function initSignupPage() {
  const pwInput   = document.getElementById('signup-password');
  const bar       = document.getElementById('signup-strength-bar');
  const label     = document.getElementById('signup-strength-label');
  const confirm   = document.getElementById('signup-confirm');
  const matchLbl  = document.getElementById('signup-match-label');
  const form      = document.getElementById('signup-form');
  if (!pwInput) return;

  pwInput.addEventListener('input', () => updateStrengthBar(pwInput.value, bar, label));

  function checkMatch() {
    if (!confirm.value) { matchLbl.textContent = ''; return true; }
    const ok = pwInput.value === confirm.value;
    matchLbl.textContent = ok ? 'Passwords match' : 'Passwords do not match';
    matchLbl.style.color = ok ? '#3fb950' : '#f85149';
    return ok;
  }
  confirm.addEventListener('input', checkMatch);

  form?.addEventListener('submit', (e) => {
    if (!checkMatch()) { e.preventDefault(); }
  });
}

function initProfile() {
  // Profile button is now a direct link to /settings — no panel logic needed.
}

function initSettingsPage() {
  // Avatar upload
  const avatarInput    = document.getElementById('avatar-input');
  const avatarPreview  = document.getElementById('avatar-preview');
  const avatarInitials = document.getElementById('avatar-initials');
  const avatarError    = document.getElementById('avatar-error');

  avatarInput?.addEventListener('change', async () => {
    const file = avatarInput.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      if (avatarError) { avatarError.textContent = 'Image must be under 2MB'; avatarError.style.display = 'block'; }
      return;
    }
    if (avatarError) avatarError.style.display = 'none';

    // Show preview immediately
    const reader = new FileReader();
    reader.onload = (e) => {
      if (avatarPreview) { avatarPreview.src = e.target.result; avatarPreview.style.display = 'block'; }
      if (avatarInitials) avatarInitials.style.display = 'none';
    };
    reader.readAsDataURL(file);

    // Upload
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/settings/avatar', { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      if (avatarError) { avatarError.textContent = err.detail || 'Upload failed'; avatarError.style.display = 'block'; }
      return;
    }
    const { avatar_url } = await res.json();
    // Bust cache on all avatar images in the page
    const ts = Date.now();
    document.querySelectorAll(`img[src^="/avatars/"]`).forEach(img => {
      img.src = avatar_url + '?t=' + ts;
    });
  });

  // Name edit
  const nameDisplay  = document.getElementById('settings-name-display');
  const nameInput    = document.getElementById('settings-name-input');
  const nameEditBtn  = document.getElementById('settings-name-edit-btn');
  const nameSaveBtn  = document.getElementById('settings-name-save');
  const nameCancelBtn= document.getElementById('settings-name-cancel');

  nameEditBtn?.addEventListener('click', () => {
    nameDisplay.style.display = 'none';
    nameEditBtn.style.display = 'none';
    nameInput.style.display = '';
    nameSaveBtn.style.display = '';
    nameCancelBtn.style.display = '';
    nameInput.focus();
    nameInput.select();
  });
  nameCancelBtn?.addEventListener('click', () => {
    nameInput.style.display = 'none';
    nameSaveBtn.style.display = 'none';
    nameCancelBtn.style.display = 'none';
    nameDisplay.style.display = '';
    nameEditBtn.style.display = '';
    nameInput.value = nameDisplay.textContent;
  });
  nameSaveBtn?.addEventListener('click', async () => {
    const val = nameInput.value.trim();
    if (!val) return;
    const res = await fetch('/settings/username', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: val }),
    });
    if (res.ok) {
      nameDisplay.textContent = val;
      nameCancelBtn.click();
    }
  });
  nameInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter')  nameSaveBtn?.click();
    if (e.key === 'Escape') nameCancelBtn?.click();
  });

  // Password change
  const curPw     = document.getElementById('s-cur-pw');
  const newPw     = document.getElementById('s-new-pw');
  const confirmPw = document.getElementById('s-confirm-pw');
  const bar       = document.getElementById('s-strength-bar');
  const barLabel  = document.getElementById('s-strength-label');
  const matchLbl  = document.getElementById('s-match-label');
  const pwSave    = document.getElementById('s-pw-save');
  const pwError   = document.getElementById('s-pw-error');
  const pwSuccess = document.getElementById('s-pw-success');
  if (!pwSave) return;

  newPw?.addEventListener('input', () => updateStrengthBar(newPw.value, bar, barLabel));
  confirmPw?.addEventListener('input', () => {
    if (!confirmPw.value) { matchLbl.textContent = ''; return; }
    const ok = newPw.value === confirmPw.value;
    matchLbl.textContent = ok ? 'Passwords match' : 'Passwords do not match';
    matchLbl.style.color = ok ? 'var(--success)' : 'var(--danger)';
  });
  pwSave.addEventListener('click', async () => {
    if (pwError) pwError.style.display = 'none';
    if (pwSuccess) pwSuccess.style.display = 'none';
    if (newPw?.value !== confirmPw?.value) {
      if (pwError) { pwError.textContent = 'Passwords do not match'; pwError.style.display = 'block'; }
      return;
    }
    const res = await fetch('/settings/password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: curPw?.value, new_password: newPw?.value }),
    });
    if (res.ok) {
      if (curPw)    curPw.value = '';
      if (newPw)    newPw.value = '';
      if (confirmPw) confirmPw.value = '';
      updateStrengthBar('', bar, barLabel);
      if (matchLbl) matchLbl.textContent = '';
      if (pwSuccess) pwSuccess.style.display = 'block';
    } else {
      const err = await res.json().catch(() => ({ detail: 'Something went wrong' }));
      if (pwError) { pwError.textContent = err.detail || 'Error'; pwError.style.display = 'block'; }
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initProfile();
  initSignupPage();
  initSettingsPage();
  initColorPicker();
  initDeleteProject();
  initEditProject();
  initTabs();
  initDeleteTask();
  initEditTask();

  const projectId = document.body.dataset.projectId;
  if (projectId) {
    initDragDrop();
    initAddTask(projectId);
    initBacklogStatusSelect();
    initBacklogCollapse();
    initPhaseDragDrop();
    initPhases(projectId);
  }
});
