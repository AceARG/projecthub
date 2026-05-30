from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import sqlite3
import os
import json
import re
from datetime import date, timedelta, datetime
from collections import defaultdict
import time as _time
import asyncio
import urllib.request

app = FastAPI(title="ProjectHub")

# ── PM-20: Rate limiting ──
_rate_store: dict = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = _time.time()
    limit = 60 if request.method in ("POST", "PUT", "DELETE", "PATCH") else 200
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < 60.0]
    if len(_rate_store[ip]) >= limit:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            {"detail": "Rate limit exceeded. Please slow down."},
            status_code=429,
            headers={"Retry-After": "60"},
        )
    _rate_store[ip].append(now)
    return await call_next(request)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def _fmt_date(value):
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%b %d").replace(" 0", " ")
    except Exception:
        return value

templates.env.filters["fmt_date"] = _fmt_date

DATABASE   = os.getenv("DATABASE_PATH", "./data/projects.db")
SECRET_KEY = os.getenv("SECRET_KEY", "ph-dev-secret-key-2026")
_signer    = URLSafeTimedSerializer(SECRET_KEY)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _make_session(user_id: int) -> str:
    return _signer.dumps({"uid": user_id})


def _read_session(token: str) -> dict | None:
    try:
        return _signer.loads(token, max_age=60 * 60 * 24 * 30)
    except Exception:
        return None


AVATARS_DIR = os.getenv("AVATARS_DIR", "/data/avatars")


def _get_session_user(request: Request) -> dict | None:
    token = request.cookies.get("ph_session")
    if not token:
        return None
    data = _read_session(token)
    if not data:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT id, username, email, avatar FROM users WHERE id = ?", (data["uid"],)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")   # 64 MB page cache
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 268435456") # 256 MB memory-mapped I/O
    return conn


def _generate_prefix(name: str) -> str:
    """Auto-generate a ticket prefix from a project name.
    'Nova Core Forge' → 'NCF', 'Backend' → 'BACK', 'My API' → 'MA'
    """
    words = [w for w in name.split() if w]
    if not words:
        return 'PROJ'
    if len(words) == 1:
        return words[0][:4].upper()
    return ''.join(w[0] for w in words[:4]).upper()


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            color       TEXT    DEFAULT '#58a6ff',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migrations
    for col in [
        "ALTER TABLE projects ADD COLUMN repo_path      TEXT    DEFAULT ''",
        "ALTER TABLE projects ADD COLUMN ticket_prefix  TEXT    DEFAULT ''",
    ]:
        try:
            conn.execute(col)
        except Exception:
            pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            status      TEXT    DEFAULT 'backlog'
                        CHECK(status IN ('backlog','todo','in-progress','done')),
            priority    TEXT    DEFAULT 'medium'
                        CHECK(priority IN ('low','medium','high')),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phases (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL,
            name        TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            status      TEXT    DEFAULT 'planned'
                        CHECK(status IN ('planned','active','done')),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)
    for col in [
        "ALTER TABLE tasks ADD COLUMN phase_id     INTEGER REFERENCES phases(id)",
        "ALTER TABLE tasks ADD COLUMN ticket_num   INTEGER DEFAULT 0",
        "ALTER TABLE tasks ADD COLUMN type         TEXT DEFAULT 'task' CHECK(type IN ('task','bug'))",
        "ALTER TABLE tasks ADD COLUMN due_date     TEXT DEFAULT NULL",
        "ALTER TABLE tasks ADD COLUMN assigned_to  INTEGER REFERENCES users(id)",
    ]:
        try:
            conn.execute(col)
        except Exception:
            pass

    # Migrate tasks table to include 'testing' status if not already present
    schema_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'"
    ).fetchone()
    if schema_row and "'testing'" not in schema_row['sql']:
        conn.execute("ALTER TABLE tasks RENAME TO tasks_old")
        conn.execute("""
            CREATE TABLE tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER NOT NULL,
                title       TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                status      TEXT    DEFAULT 'backlog'
                            CHECK(status IN ('backlog','todo','in-progress','done','testing')),
                priority    TEXT    DEFAULT 'medium'
                            CHECK(priority IN ('low','medium','high')),
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                phase_id    INTEGER REFERENCES phases(id),
                ticket_num  INTEGER DEFAULT 0,
                type        TEXT    DEFAULT 'task' CHECK(type IN ('task','bug')),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            INSERT INTO tasks (id, project_id, title, description, status, priority, created_at, phase_id, ticket_num, type)
            SELECT id, project_id, title, description, status, priority, created_at, phase_id, ticket_num, type
            FROM tasks_old
        """)
        conn.execute("DROP TABLE tasks_old")

    # Back-fill ticket_num for existing tasks (assign per-project sequence by id order)
    conn.execute("""
        UPDATE tasks SET ticket_num = (
            SELECT COUNT(*) FROM tasks t2
            WHERE t2.project_id = tasks.project_id AND t2.id <= tasks.id
        )
        WHERE ticket_num = 0 OR ticket_num IS NULL
    """)

    # Back-fill ticket_prefix for existing projects that don't have one
    projects = conn.execute("SELECT id, name FROM projects WHERE ticket_prefix = '' OR ticket_prefix IS NULL").fetchall()
    for p in projects:
        conn.execute("UPDATE projects SET ticket_prefix = ? WHERE id = ?",
                     (_generate_prefix(p['name']), p['id']))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS plan_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id    INTEGER NOT NULL,
            step       INTEGER NOT NULL CHECK(step IN (1,2,3)),
            role       TEXT    NOT NULL CHECK(role IN ('agent','user')),
            content    TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id          INTEGER NOT NULL,
            name                TEXT    NOT NULL,
            description         TEXT    DEFAULT '',
            status              TEXT    DEFAULT 'draft'
                                CHECK(status IN (
                                    'draft','scope-pending','scope-review',
                                    'technical-pending','technical-review',
                                    'architecture-pending','architecture-review','done'
                                )),
            scope_doc           TEXT    DEFAULT '',
            technical_analysis  TEXT    DEFAULT '',
            architecture_doc    TEXT    DEFAULT '',
            notes               TEXT    DEFAULT '',
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)
    for col in [
        "ALTER TABLE plans ADD COLUMN notes TEXT DEFAULT ''",
    ]:
        try:
            conn.execute(col)
        except Exception:
            pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            avatar        TEXT    DEFAULT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT NULL")
    except Exception:
        pass

    # PM-17: Task comments
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_comments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id    INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            content    TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id)  ON DELETE CASCADE
        )
    """)
    # PM-19: Task dependencies
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_dependencies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     INTEGER NOT NULL,
            depends_on  INTEGER NOT NULL,
            UNIQUE(task_id, depends_on),
            FOREIGN KEY(task_id)   REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY(depends_on) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """)
    # PM-21: Webhook configurations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhook_configs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            url        TEXT    NOT NULL,
            events     TEXT    DEFAULT '["task.status_changed"]',
            active     INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)
    # PM-7: Notifications
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            type       TEXT    NOT NULL,
            title      TEXT    NOT NULL,
            body       TEXT    DEFAULT '',
            link       TEXT    DEFAULT '',
            is_read    INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    # PM-8: Chat rooms, members, messages
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_rooms (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    DEFAULT '',
            type       TEXT    NOT NULL DEFAULT 'group'
                       CHECK(type IN ('direct','group')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_members (
            room_id    INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            PRIMARY KEY (room_id, user_id),
            FOREIGN KEY(room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id)      ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id    INTEGER NOT NULL,
            sender_id  INTEGER NOT NULL,
            body       TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(room_id)   REFERENCES chat_rooms(id) ON DELETE CASCADE,
            FOREIGN KEY(sender_id) REFERENCES users(id)      ON DELETE CASCADE
        )
    """)

    # Indexes for high-volume queries
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_tasks_project    ON tasks(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_status     ON tasks(status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_phase      ON tasks(phase_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_priority   ON tasks(priority)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_proj_stat  ON tasks(project_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_proj_phase ON tasks(project_id, phase_id)",
        "CREATE INDEX IF NOT EXISTS idx_phases_project   ON phases(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_plans_project    ON plans(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_plans_status     ON plans(status)",
        "CREATE INDEX IF NOT EXISTS idx_messages_plan    ON plan_messages(plan_id, step)",
        "CREATE INDEX IF NOT EXISTS idx_users_email      ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_due_date   ON tasks(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_comments_task    ON task_comments(task_id)",
        "CREATE INDEX IF NOT EXISTS idx_deps_task        ON task_dependencies(task_id)",
        "CREATE INDEX IF NOT EXISTS idx_deps_on          ON task_dependencies(depends_on)",
        "CREATE INDEX IF NOT EXISTS idx_webhooks_proj    ON webhook_configs(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_assignee   ON tasks(assigned_to)",
        "CREATE INDEX IF NOT EXISTS idx_notif_user       ON notifications(user_id, is_read)",
        "CREATE INDEX IF NOT EXISTS idx_chat_members     ON chat_members(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages    ON chat_messages(room_id, created_at)",
    ]
    for idx in indexes:
        conn.execute(idx)

    conn.commit()
    conn.close()


_PLAN_STATUS_LABEL = {
    'draft':                'Draft',
    'scope-pending':        'Scope Pending',
    'scope-review':         'Scope Review',
    'technical-pending':    'Tech Pending',
    'technical-review':     'Tech Review',
    'architecture-pending': 'Arch Pending',
    'architecture-review':  'Arch Review',
    'done':                 'Done',
}


def _plan_step(status: str) -> int:
    if status in ('draft', 'scope-pending', 'scope-review'):
        return 1
    if status in ('technical-pending', 'technical-review'):
        return 2
    return 3


@app.on_event("startup")
async def startup():
    init_db()


# ──────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────

@app.get("/search")
async def search(request: Request, q: str = ""):
    user = _get_session_user(request)
    if not user:
        return {"results": []}
    q = q.strip()
    if len(q) < 2:
        return {"results": []}
    conn = get_db()
    pattern = f"%{q}%"
    tasks = conn.execute("""
        SELECT t.id, t.title, t.status, t.project_id,
               p.name AS project_name, p.ticket_prefix, t.ticket_num
        FROM tasks t
        JOIN projects p ON p.id = t.project_id
        WHERE t.title LIKE ? OR t.description LIKE ?
        ORDER BY t.created_at DESC
        LIMIT 10
    """, (pattern, pattern)).fetchall()
    projects = conn.execute("""
        SELECT id, name, color
        FROM projects
        WHERE name LIKE ? OR description LIKE ?
        LIMIT 5
    """, (pattern, pattern)).fetchall()
    conn.close()
    results = [
        {"type": "task", "id": t["id"], "title": t["title"],
         "status": t["status"], "project_id": t["project_id"],
         "project_name": t["project_name"],
         "ticket_id": f"{t['ticket_prefix']}-{t['ticket_num']}"}
        for t in tasks
    ] + [
        {"type": "project", "id": p["id"], "title": p["name"], "color": p["color"]}
        for p in projects
    ]
    return {"results": results}


# ──────────────────────────────────────────────
# Pages
# ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = _get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    projects = conn.execute("""
        SELECT p.*,
               COUNT(t.id)                                        AS task_count,
               SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) AS done_count
        FROM projects p
        LEFT JOIN tasks t ON t.project_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects, "current_user": user})


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_view(request: Request, project_id: int):
    user = _get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,)
    ).fetchall()

    # Phases with per-phase task counts
    phases_raw = conn.execute("""
        SELECT ph.*,
               COUNT(t.id)                                            AS task_count,
               SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END)    AS done_count
        FROM phases ph
        LEFT JOIN tasks t ON t.phase_id = ph.id
        WHERE ph.project_id = ?
        GROUP BY ph.id
        ORDER BY ph.created_at ASC
    """, (project_id,)).fetchall()

    # Plans — must query before conn.close()
    plans_raw_db = conn.execute(
        "SELECT id, name, description, status, created_at FROM plans WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,)
    ).fetchall()

    # PM-19: blocked task IDs (have at least one incomplete blocker)
    blocked_ids_raw = conn.execute("""
        SELECT DISTINCT d.task_id
        FROM task_dependencies d
        JOIN tasks t ON t.id = d.depends_on
        WHERE t.project_id = ? AND t.status != 'done'
    """, (project_id,)).fetchall()
    blocked_ids = {r[0] for r in blocked_ids_raw}

    # PM-21: webhooks for this project
    webhooks_raw = conn.execute(
        "SELECT * FROM webhook_configs WHERE project_id = ? ORDER BY created_at",
        (project_id,),
    ).fetchall()

    # PM-6: all users for assignee picker
    all_users_raw = conn.execute(
        "SELECT id, username, avatar FROM users ORDER BY username"
    ).fetchall()

    conn.close()
    all_users = [dict(u) for u in all_users_raw]
    webhooks = [dict(w) for w in webhooks_raw]

    plan_items = []
    for p in plans_raw_db:
        d = dict(p)
        d['step'] = _plan_step(d['status'])
        d['status_label'] = _PLAN_STATUS_LABEL.get(d['status'], d['status'])
        plan_items.append(d)

    phases = []
    for ph in phases_raw:
        d = dict(ph)
        d['done_count'] = d['done_count'] or 0
        tc = d['task_count'] or 0
        d['completion_pct'] = round(d['done_count'] / tc * 100) if tc else 0
        phases.append(d)

    # Kanban: filter to active phase if one exists
    active_phase = next((ph for ph in phases if ph['status'] == 'active'), None)
    active_phase_task_ids = set()
    if active_phase:
        active_phase_task_ids = {
            t['id'] for t in tasks if t['phase_id'] == active_phase['id']
        }
        board_tasks_pool = [t for t in tasks if t['id'] in active_phase_task_ids]
    else:
        board_tasks_pool = tasks

    kanban = {
        "backlog":     [t for t in tasks if t["status"] == "backlog"],
        "todo":        [t for t in board_tasks_pool if t["status"] == "todo"],
        "in-progress": [t for t in board_tasks_pool if t["status"] == "in-progress"],
        "testing":     [t for t in board_tasks_pool if t["status"] == "testing"],
        "done":        [t for t in board_tasks_pool if t["status"] == "done"],
    }

    # Phase task grouping for the planning board
    unassigned_tasks = [t for t in tasks if t['phase_id'] is None]
    phase_task_map = {}
    for t in tasks:
        pid = t['phase_id']
        if pid is not None:
            phase_task_map.setdefault(pid, []).append(t)

    total    = len(tasks)
    done     = sum(1 for t in tasks if t['status'] == 'done')
    inp      = sum(1 for t in tasks if t['status'] == 'in-progress')
    todo     = sum(1 for t in tasks if t['status'] == 'todo')
    testing  = sum(1 for t in tasks if t['status'] == 'testing')
    back     = sum(1 for t in tasks if t['status'] == 'backlog')

    def pct(n): return round(n / total * 100) if total else 0

    high_done = sum(1 for t in tasks if t['status'] == 'done' and t['priority'] == 'high')
    p_high    = sum(1 for t in tasks if t['priority'] == 'high')
    p_med     = sum(1 for t in tasks if t['priority'] == 'medium')
    p_low     = sum(1 for t in tasks if t['priority'] == 'low')

    # Phase summaries
    phase_summaries = []
    for ph in phases:
        ph_tasks = phase_task_map.get(ph['id'], [])
        ph_total = len(ph_tasks)
        ph_done  = sum(1 for t in ph_tasks if t['status'] == 'done')
        ph_pct   = round(ph_done / ph_total * 100) if ph_total else 0
        phase_summaries.append({
            'id': ph['id'], 'name': ph['name'], 'status': ph['status'],
            'total': ph_total, 'done': ph_done, 'pct': ph_pct,
        })

    active_phase_pct = 0
    if active_phase:
        ap_tasks = phase_task_map.get(active_phase['id'], [])
        ap_total = len(ap_tasks)
        ap_done  = sum(1 for t in ap_tasks if t['status'] == 'done')
        active_phase_pct = round(ap_done / ap_total * 100) if ap_total else 0

    unassigned_count = len(unassigned_tasks)

    insights = []
    if total == 0:
        insights.append({'icon': '📋', 'text': 'No tasks yet — add some to get started', 'type': 'neutral'})
    else:
        if pct(done) == 100:
            insights.append({'icon': '🎉', 'text': 'All tasks completed!', 'type': 'good'})
        if active_phase:
            insights.append({'icon': '🚀', 'text': f"Active phase: {active_phase['name']} — {active_phase_pct}% complete", 'type': 'info'})
        if testing > 0:
            insights.append({'icon': '🧪', 'text': f"{testing} task{'s' if testing != 1 else ''} in testing — nearly done!", 'type': 'good'})
        if inp > 0:
            insights.append({'icon': '⚡', 'text': f"{inp} task{'s' if inp != 1 else ''} currently in progress", 'type': 'info'})
        high_rem = p_high - high_done
        if high_rem > 0:
            insights.append({'icon': '🔴', 'text': f"{high_rem} high-priority task{'s' if high_rem != 1 else ''} not yet done", 'type': 'warn'})
        if back > 0:
            insights.append({'icon': '📥', 'text': f"{back} task{'s' if back != 1 else ''} waiting in backlog", 'type': 'neutral'})
        if unassigned_count > 0 and phases:
            insights.append({'icon': '📌', 'text': f"{unassigned_count} task{'s' if unassigned_count != 1 else ''} not assigned to any phase", 'type': 'warn'})
        remaining = total - done
        if 0 < pct(done) < 100:
            insights.append({'icon': '🎯', 'text': f"{remaining} task{'s' if remaining != 1 else ''} remaining to reach 100%", 'type': 'info'})

    stats = {
        'total': total, 'done': done, 'in_progress': inp, 'todo': todo,
        'testing': testing, 'backlog': back,
        'active': inp + todo + testing,
        'priority_high': p_high, 'priority_medium': p_med, 'priority_low': p_low,
        'completion_pct': pct(done),
        'done_pct': pct(done), 'in_progress_pct': pct(inp),
        'todo_pct': pct(todo), 'testing_pct': pct(testing), 'backlog_pct': pct(back),
        'high_pct': pct(p_high), 'medium_pct': pct(p_med), 'low_pct': pct(p_low),
        'phase_summaries': phase_summaries,
        'active_phase_name': active_phase['name'] if active_phase else None,
        'active_phase_pct': active_phase_pct,
        'unassigned_count': unassigned_count,
        'insights': insights,
    }

    today_str = date.today().isoformat()
    soon_str  = (date.today() + timedelta(days=3)).isoformat()

    return templates.TemplateResponse("project.html", {
        "request": request,
        "project": project,
        "tasks": tasks,
        "kanban": kanban,
        "stats": stats,
        "phases": phases,
        "unassigned_tasks": unassigned_tasks,
        "phase_task_map": phase_task_map,
        "plan_items": plan_items,
        "active_phase": active_phase,
        "current_user": user,
        "today": today_str,
        "soon": soon_str,
        "blocked_ids": blocked_ids,
        "webhooks": webhooks,
        "all_users": all_users,
    })


# ──────────────────────────────────────────────
# Projects API
# ──────────────────────────────────────────────

@app.post("/projects")
async def create_project(
    name: str           = Form(...),
    description: str    = Form(""),
    color: str          = Form("#58a6ff"),
    repo_path: str      = Form(""),
    ticket_prefix: str  = Form(""),
):
    prefix = ticket_prefix.strip().upper() or _generate_prefix(name)
    conn = get_db()
    conn.execute(
        "INSERT INTO projects (name, description, color, repo_path, ticket_prefix) VALUES (?, ?, ?, ?, ?)",
        (name, description, color, repo_path, prefix),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=303)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    repo_path: Optional[str] = None
    ticket_prefix: Optional[str] = None


@app.put("/projects/{project_id}")
async def update_project(project_id: int, data: ProjectUpdate):
    fields = {k: v for k, v in data.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn = get_db()
    conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", (*fields.values(), project_id))
    conn.commit()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ──────────────────────────────────────────────
# Tasks API
# ──────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    status: Optional[str] = "backlog"
    priority: Optional[str] = "medium"
    phase_id: Optional[int] = None
    type: Optional[str] = "task"
    due_date: Optional[str] = None
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    phase_id: Optional[int] = None
    type: Optional[str] = None
    due_date: Optional[str] = None
    assigned_to: Optional[int] = None


def _create_notification(conn, user_id: int, ntype: str, title: str, body: str = "", link: str = ""):
    conn.execute(
        "INSERT INTO notifications (user_id, type, title, body, link) VALUES (?, ?, ?, ?, ?)",
        (user_id, ntype, title, body, link),
    )


def _task_with_ticket(conn, task_id: int) -> dict:
    """Fetch a task row and attach ticket_id, is_blocked, and assignee info."""
    row = conn.execute("""
        SELECT t.*, p.ticket_prefix,
               u.username AS assignee_username
        FROM tasks t
        JOIN projects p ON p.id = t.project_id
        LEFT JOIN users u ON u.id = t.assigned_to
        WHERE t.id = ?
    """, (task_id,)).fetchone()
    if not row:
        return {}
    d = dict(row)
    d['ticket_id'] = f"{d.get('ticket_prefix', '')}-{d.get('ticket_num', 0)}"
    blocked = conn.execute("""
        SELECT COUNT(*) FROM task_dependencies d
        JOIN tasks t ON t.id = d.depends_on
        WHERE d.task_id = ? AND t.status != 'done'
    """, (task_id,)).fetchone()[0]
    d['is_blocked'] = blocked > 0
    return d


@app.post("/projects/{project_id}/tasks")
async def create_task(project_id: int, task: TaskCreate):
    conn = get_db()
    # Next ticket number for this project
    next_num = conn.execute(
        "SELECT COALESCE(MAX(ticket_num), 0) + 1 FROM tasks WHERE project_id = ?",
        (project_id,)
    ).fetchone()[0]
    cur = conn.execute(
        "INSERT INTO tasks (project_id, title, description, status, priority, phase_id, ticket_num, type, due_date, assigned_to) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (project_id, task.title, task.description, task.status, task.priority, task.phase_id, next_num, task.type or 'task', task.due_date, task.assigned_to),
    )
    task_id = cur.lastrowid
    if task.assigned_to:
        _create_notification(conn, task.assigned_to, "assignment",
            "You were assigned a task", task.title, f"/projects/{project_id}")
    conn.commit()
    result = _task_with_ticket(conn, task_id)
    conn.close()
    return result


async def _fire_webhooks(project_id: int, task: dict, old_status: str):
    """Fire project webhooks for task status changes (PM-21, non-blocking)."""
    conn = get_db()
    hooks = conn.execute(
        "SELECT url, events FROM webhook_configs WHERE project_id = ? AND active = 1",
        (project_id,),
    ).fetchall()
    conn.close()
    payload = json.dumps({
        "event": "task.status_changed",
        "task_id": task.get("id"),
        "task_title": task.get("title"),
        "ticket_id": task.get("ticket_id"),
        "project_id": project_id,
        "old_status": old_status,
        "new_status": task.get("status"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }).encode()
    for hook in hooks:
        events = json.loads(hook["events"] or "[]")
        if "task.status_changed" not in events:
            continue
        try:
            req = urllib.request.Request(
                hook["url"],
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "ProjectHub/1.0"},
                method="POST",
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda r=req: urllib.request.urlopen(r, timeout=5))
        except Exception:
            pass


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: TaskUpdate):
    updates = {}
    for k, v in task.dict().items():
        if v is not None:
            updates[k] = v
        elif k in task.__fields_set__:
            updates[k] = None
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_db()
    old_row = conn.execute("SELECT status, assigned_to FROM tasks WHERE id = ?", (task_id,)).fetchone()
    old_status   = old_row["status"]      if old_row else None
    old_assigned = old_row["assigned_to"] if old_row else None
    conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", (*updates.values(), task_id))
    result = _task_with_ticket(conn, task_id)
    new_assigned = updates.get("assigned_to")
    if new_assigned and new_assigned != old_assigned:
        _create_notification(conn, new_assigned, "assignment",
            "You were assigned a task",
            result.get("title", ""),
            f"/projects/{result.get('project_id', '')}")
    conn.commit()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    new_status = updates.get("status")
    if new_status and old_status and new_status != old_status:
        asyncio.create_task(_fire_webhooks(result.get("project_id"), result, old_status))
    return result


@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    conn = get_db()
    result = _task_with_ticket(conn, task_id)
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── PM-18: Bulk task actions ──────────────────

class BulkTaskAction(BaseModel):
    task_ids: List[int]
    action: str   # "status" | "priority" | "delete"
    value: Optional[str] = None

@app.post("/projects/{project_id}/tasks/bulk")
async def bulk_task_action(project_id: int, data: BulkTaskAction):
    if not data.task_ids:
        return {"ok": True, "affected": 0}
    conn = get_db()
    ph = ",".join("?" * len(data.task_ids))
    if data.action == "delete":
        conn.execute(
            f"DELETE FROM tasks WHERE project_id = ? AND id IN ({ph})",
            (project_id, *data.task_ids),
        )
    elif data.action in ("status", "priority") and data.value:
        col = "status" if data.action == "status" else "priority"
        conn.execute(
            f"UPDATE tasks SET {col} = ? WHERE project_id = ? AND id IN ({ph})",
            (data.value, project_id, *data.task_ids),
        )
    conn.commit()
    conn.close()
    return {"ok": True, "affected": len(data.task_ids)}


# ── PM-17: Task comments ──────────────────────

class CommentCreate(BaseModel):
    content: str

@app.get("/tasks/{task_id}/comments")
async def get_task_comments(task_id: int):
    conn = get_db()
    rows = conn.execute("""
        SELECT c.id, c.content, c.created_at, u.id AS user_id, u.username
        FROM task_comments c
        JOIN users u ON u.id = c.user_id
        WHERE c.task_id = ?
        ORDER BY c.created_at
    """, (task_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/tasks/{task_id}/comments")
async def create_task_comment(request: Request, task_id: int, data: CommentCreate):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO task_comments (task_id, user_id, content) VALUES (?, ?, ?)",
        (task_id, user["id"], content),
    )
    cid = cur.lastrowid
    # Parse @mentions and notify mentioned users
    task_info = conn.execute("SELECT title, project_id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    for username in set(re.findall(r'@(\w+)', content)):
        mentioned = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if mentioned and mentioned["id"] != user["id"]:
            _create_notification(conn, mentioned["id"], "mention",
                f"{user['username']} mentioned you in a comment",
                content[:120],
                f"/projects/{task_info['project_id']}" if task_info else "")
    conn.commit()
    row = conn.execute("""
        SELECT c.id, c.content, c.created_at, u.id AS user_id, u.username
        FROM task_comments c JOIN users u ON u.id = c.user_id
        WHERE c.id = ?
    """, (cid,)).fetchone()
    conn.close()
    return dict(row)

@app.delete("/comments/{comment_id}")
async def delete_comment(request: Request, comment_id: int):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conn = get_db()
    conn.execute("DELETE FROM task_comments WHERE id = ? AND user_id = ?", (comment_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── PM-19: Task dependencies ──────────────────

class DependencyCreate(BaseModel):
    depends_on: int

@app.get("/tasks/{task_id}/dependencies")
async def get_task_dependencies(task_id: int):
    conn = get_db()
    blockers = conn.execute("""
        SELECT d.id AS dep_id, t.id, t.title, t.status,
               (p.ticket_prefix || '-' || t.ticket_num) AS ticket_id
        FROM task_dependencies d
        JOIN tasks t ON t.id = d.depends_on
        JOIN projects p ON p.id = t.project_id
        WHERE d.task_id = ?
    """, (task_id,)).fetchall()
    conn.close()
    return {"blockers": [dict(r) for r in blockers]}

@app.post("/tasks/{task_id}/dependencies")
async def add_task_dependency(task_id: int, data: DependencyCreate):
    if task_id == data.depends_on:
        raise HTTPException(status_code=400, detail="A task cannot depend on itself")
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO task_dependencies (task_id, depends_on) VALUES (?, ?)",
            (task_id, data.depends_on),
        )
        conn.commit()
        dep_id = cur.lastrowid
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    row = conn.execute("""
        SELECT d.id AS dep_id, t.id, t.title, t.status,
               (p.ticket_prefix || '-' || t.ticket_num) AS ticket_id
        FROM task_dependencies d
        JOIN tasks t ON t.id = d.depends_on
        JOIN projects p ON p.id = t.project_id
        WHERE d.id = ?
    """, (dep_id,)).fetchone()
    conn.close()
    return dict(row) if row else {"ok": True}

@app.delete("/task-dependencies/{dep_id}")
async def delete_task_dependency(dep_id: int):
    conn = get_db()
    conn.execute("DELETE FROM task_dependencies WHERE id = ?", (dep_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── PM-21: Webhooks ───────────────────────────

class WebhookCreate(BaseModel):
    url: str
    events: Optional[List[str]] = None

@app.get("/projects/{project_id}/webhooks")
async def list_webhooks(project_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM webhook_configs WHERE project_id = ? ORDER BY created_at",
        (project_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/projects/{project_id}/webhooks")
async def create_webhook(project_id: int, data: WebhookCreate):
    events = data.events or ["task.status_changed"]
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO webhook_configs (project_id, url, events) VALUES (?, ?, ?)",
        (project_id, data.url.strip(), json.dumps(events)),
    )
    wh_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM webhook_configs WHERE id = ?", (wh_id,)).fetchone()
    conn.close()
    return dict(row)

@app.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: int):
    conn = get_db()
    conn.execute("DELETE FROM webhook_configs WHERE id = ?", (webhook_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ──────────────────────────────────────────────
# Phases API
# ──────────────────────────────────────────────

class PhaseCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    status: Optional[str] = "planned"


class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@app.post("/projects/{project_id}/phases")
async def create_phase(project_id: int, phase: PhaseCreate):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO phases (project_id, name, description, status) VALUES (?,?,?,?)",
        (project_id, phase.name, phase.description, phase.status),
    )
    phase_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM phases WHERE id = ?", (phase_id,)).fetchone()
    conn.close()
    return dict(row)


@app.put("/phases/{phase_id}")
async def update_phase(phase_id: int, data: PhaseUpdate):
    fields = {k: v for k, v in data.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn = get_db()
    conn.execute(f"UPDATE phases SET {set_clause} WHERE id = ?", (*fields.values(), phase_id))
    conn.commit()
    row = conn.execute("SELECT * FROM phases WHERE id = ?", (phase_id,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/phases/{phase_id}")
async def delete_phase(phase_id: int):
    conn = get_db()
    # Unassign tasks — don't delete them, just clear their phase
    conn.execute("UPDATE tasks SET phase_id = NULL WHERE phase_id = ?", (phase_id,))
    conn.execute("DELETE FROM phases WHERE id = ?", (phase_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ──────────────────────────────────────────────
# Plans API
# ──────────────────────────────────────────────

class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    scope_doc: Optional[str] = None
    technical_analysis: Optional[str] = None
    architecture_doc: Optional[str] = None
    notes: Optional[str] = None


class PlanMessageCreate(BaseModel):
    step: int
    content: str
    role: Optional[str] = "user"


class TaskItem(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    type: Optional[str] = "task"
    phase_id: Optional[int] = None


class TasksFromPlan(BaseModel):
    tasks: List[TaskItem] = []


_PLAN_AWAITING = {
    'scope-review':         'user',
    'technical-review':     'user',
    'architecture-review':  'user',
    'scope-pending':        'agent',
    'technical-pending':    'agent',
    'architecture-pending': 'agent',
}


def _plan_dict(row) -> dict:
    d = dict(row)
    d['step'] = _plan_step(d['status'])
    d['status_label'] = _PLAN_STATUS_LABEL.get(d['status'], d['status'])
    d['agent_running'] = False
    d['awaiting'] = _PLAN_AWAITING.get(d['status'], '')
    return d


@app.get("/projects/{project_id}/plans")
async def list_plans_api(project_id: int, status: Optional[str] = None):
    conn = get_db()
    sql = "SELECT id, name, description, status, created_at FROM plans WHERE project_id = ?"
    params: list = [project_id]
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_plan_dict(r) for r in rows]


@app.post("/projects/{project_id}/plans")
async def create_plan(project_id: int, plan: PlanCreate):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO plans (project_id, name, description) VALUES (?,?,?)",
        (project_id, plan.name, plan.description),
    )
    plan_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    return _plan_dict(row)


@app.get("/plans/{plan_id}")
async def get_plan(plan_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _plan_dict(row)


@app.put("/plans/{plan_id}")
async def update_plan(plan_id: int, data: PlanUpdate):
    # Allow empty string updates (scope_doc etc. can be empty)
    fields = {k: v for k, v in data.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn = get_db()
    conn.execute(f"UPDATE plans SET {set_clause} WHERE id = ?", (*fields.values(), plan_id))
    conn.commit()
    row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _plan_dict(row)


@app.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int):
    conn = get_db()
    conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/plans/{plan_id}/messages")
async def get_plan_messages(plan_id: int, step: Optional[int] = None):
    conn = get_db()
    if step:
        rows = conn.execute(
            "SELECT * FROM plan_messages WHERE plan_id = ? AND step = ? ORDER BY created_at",
            (plan_id, step)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM plan_messages WHERE plan_id = ? ORDER BY created_at",
            (plan_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/plans/{plan_id}/messages")
async def post_plan_message(plan_id: int, msg: PlanMessageCreate):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO plan_messages (plan_id, step, role, content) VALUES (?,?,?,?)",
        (plan_id, msg.step, msg.role, msg.content),
    )
    msg_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM plan_messages WHERE id = ?", (msg_id,)).fetchone()
    conn.close()
    return dict(row)


@app.post("/plans/{plan_id}/create-tasks")
async def create_plan_tasks(plan_id: int, body: TasksFromPlan):
    conn = get_db()
    plan = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        raise HTTPException(status_code=404, detail="Plan not found")

    project_id = plan["project_id"]
    task_ids = []
    for t in body.tasks:
        next_num = conn.execute(
            "SELECT COALESCE(MAX(ticket_num), 0) + 1 FROM tasks WHERE project_id = ?",
            (project_id,)
        ).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO tasks (project_id, title, description, status, priority, type, ticket_num, phase_id) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (project_id, t.title, t.description or '', 'backlog',
             t.priority or 'medium', t.type or 'task', next_num, t.phase_id),
        )
        task_ids.append(cur.lastrowid)

    conn.execute("UPDATE plans SET status = 'done' WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    return {"created": len(task_ids), "task_ids": task_ids, "plan_status": "done"}


# ──────────────────────────────────────────────
# Agent runner endpoints
# ──────────────────────────────────────────────

def _extract_tasks_json(doc: str) -> list:
    """Extract a JSON task array from an architecture document."""
    m = re.search(r'```json\s*(\[[\s\S]*?\])\s*```', doc, re.MULTILINE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r'(\[\s*\{[\s\S]*?\}\s*\])', doc)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return []




@app.post("/plans/{plan_id}/auto-create-tasks")
async def auto_create_plan_tasks(plan_id: int):
    conn = get_db()
    plan = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        conn.close()
        raise HTTPException(status_code=404, detail="Plan not found")

    tasks = _extract_tasks_json(plan["architecture_doc"] or "")
    if not tasks:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="No task JSON found in architecture document. Ask the agent to regenerate.",
        )

    project_id = plan["project_id"]
    task_ids = []
    for t in tasks:
        next_num = conn.execute(
            "SELECT COALESCE(MAX(ticket_num), 0) + 1 FROM tasks WHERE project_id = ?",
            (project_id,)
        ).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO tasks (project_id, title, description, status, priority, type, ticket_num, phase_id) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                project_id,
                t.get("title", "Untitled"),
                t.get("description", ""),
                "backlog",
                t.get("priority", "medium"),
                t.get("type", "task"),
                next_num,
                t.get("phase_id"),
            ),
        )
        task_ids.append(cur.lastrowid)

    conn.execute("UPDATE plans SET status = 'done' WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    return {"created": len(task_ids), "plan_status": "done"}


# ──────────────────────────────────────────────
# JSON API — for MCP / external clients
# ──────────────────────────────────────────────

@app.get("/api/projects")
async def api_list_projects():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.*,
               COUNT(t.id) AS task_count,
               SUM(CASE WHEN t.status='done'        THEN 1 ELSE 0 END) AS done_count,
               SUM(CASE WHEN t.status='in-progress' THEN 1 ELSE 0 END) AS inprog_count,
               SUM(CASE WHEN t.status='todo'        THEN 1 ELSE 0 END) AS todo_count
        FROM projects p LEFT JOIN tasks t ON t.project_id = p.id
        GROUP BY p.id ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/projects/by-repo")
async def api_project_by_repo(url: str):
    norm = url.lower().rstrip("/")
    if norm.endswith(".git"):
        norm = norm[:-4]
    conn = get_db()
    rows = conn.execute("SELECT * FROM projects WHERE repo_path != ''").fetchall()
    conn.close()
    for r in rows:
        stored = r["repo_path"].lower().rstrip("/")
        if stored.endswith(".git"):
            stored = stored[:-4]
        if norm == stored:
            return dict(r)
    return None


@app.get("/api/projects/{project_id}/tasks")
async def api_list_tasks(
    project_id: int,
    status: str = "",
    priority: str = "",
    phase_id: int = 0,
    limit: int = 200,
    offset: int = 0,
):
    where: list = ["t.project_id = ?"]
    params: list = [project_id]
    if status:
        where.append("t.status = ?");   params.append(status)
    if priority:
        where.append("t.priority = ?"); params.append(priority)
    if phase_id:
        where.append("t.phase_id = ?"); params.append(phase_id)
    sql = (
        f"SELECT t.*, p.ticket_prefix, "
        f"(p.ticket_prefix || '-' || t.ticket_num) AS ticket_id "
        f"FROM tasks t JOIN projects p ON p.id = t.project_id "
        f"WHERE {' AND '.join(where)} ORDER BY t.priority DESC, t.created_at "
        f"LIMIT ? OFFSET ?"
    )
    params += [limit, offset]
    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/projects/{project_id}/phases")
async def api_list_phases(project_id: int):
    conn = get_db()
    rows = conn.execute("""
        SELECT ph.*,
               COUNT(t.id) AS task_count,
               SUM(CASE WHEN t.status='done' THEN 1 ELSE 0 END) AS done_count
        FROM phases ph LEFT JOIN tasks t ON t.phase_id = ph.id
        WHERE ph.project_id = ?
        GROUP BY ph.id ORDER BY ph.created_at
    """, (project_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        tc = d.get("task_count") or 0
        dc = d.get("done_count") or 0
        d["completion_pct"] = round(dc / tc * 100) if tc else 0
        result.append(d)
    return result


@app.get("/api/projects/{project_id}/active-phase-tasks")
async def api_active_phase_tasks(project_id: int):
    conn = get_db()
    phase = conn.execute(
        "SELECT * FROM phases WHERE project_id = ? AND status = 'active' ORDER BY created_at LIMIT 1",
        (project_id,)
    ).fetchone()
    if not phase:
        conn.close()
        return {"error": "No active phase"}
    phase_dict = dict(phase)
    tasks = [dict(r) for r in conn.execute(
        "SELECT t.*, p.ticket_prefix, (p.ticket_prefix || '-' || t.ticket_num) AS ticket_id "
        "FROM tasks t JOIN projects p ON p.id = t.project_id "
        "WHERE t.phase_id = ? ORDER BY t.priority DESC, t.created_at",
        (phase["id"],)
    ).fetchall()]
    conn.close()
    total = len(tasks)
    done  = sum(1 for t in tasks if t["status"] == "done")
    phase_dict["completion_pct"] = round(done / total * 100) if total else 0
    grouped: dict = {"in_progress": [], "todo": [], "testing": [], "done": [], "backlog": []}
    for t in tasks:
        key = "in_progress" if t["status"] == "in-progress" else t["status"]
        grouped.setdefault(key, []).append(t)
    return {"phase": phase_dict, **grouped}


@app.get("/api/projects/{project_id}/context")
async def api_project_context(project_id: int):
    conn = get_db()
    proj = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not proj:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")
    tasks  = [dict(r) for r in conn.execute(
        "SELECT * FROM tasks WHERE project_id = ? ORDER BY priority DESC, created_at",
        (project_id,)
    ).fetchall()]
    phases = [dict(r) for r in conn.execute(
        "SELECT * FROM phases WHERE project_id = ? ORDER BY created_at", (project_id,)
    ).fetchall()]
    plans  = [dict(r) for r in conn.execute(
        "SELECT id, name, status, description FROM plans "
        "WHERE project_id = ? AND status NOT IN ('draft','done') ORDER BY created_at",
        (project_id,)
    ).fetchall()]
    conn.close()
    return {"project": dict(proj), "phases": phases, "tasks": tasks, "plans": plans}


# ──────────────────────────────────────────────
# Insights
# ──────────────────────────────────────────────

@app.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request):
    user = _get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    rows = conn.execute("""
        SELECT p.*,
               COUNT(t.id)                                                          AS task_count,
               SUM(CASE WHEN t.status='done'        THEN 1 ELSE 0 END)             AS done_count,
               SUM(CASE WHEN t.status='in-progress' THEN 1 ELSE 0 END)             AS inprog_count,
               SUM(CASE WHEN t.status='todo'        THEN 1 ELSE 0 END)             AS todo_count,
               SUM(CASE WHEN t.status='backlog'     THEN 1 ELSE 0 END)             AS backlog_count,
               SUM(CASE WHEN t.priority='high'      THEN 1 ELSE 0 END)             AS high_count,
               SUM(CASE WHEN t.priority='medium'    THEN 1 ELSE 0 END)             AS medium_count,
               SUM(CASE WHEN t.priority='low'       THEN 1 ELSE 0 END)             AS low_count,
               SUM(CASE WHEN t.priority='high' AND t.status!='done' THEN 1 ELSE 0 END) AS high_pending
        FROM projects p
        LEFT JOIN tasks t ON t.project_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()

    def p(n, t): return round(n / t * 100) if t else 0

    tt = sum(r['task_count']    for r in rows)
    td = sum((r['done_count']   or 0) for r in rows)
    ti = sum((r['inprog_count'] or 0) for r in rows)
    to = sum((r['todo_count']   or 0) for r in rows)
    tb = sum((r['backlog_count']or 0) for r in rows)
    th = sum((r['high_count']   or 0) for r in rows)
    tm = sum((r['medium_count'] or 0) for r in rows)
    tl = sum((r['low_count']    or 0) for r in rows)
    thp= sum((r['high_pending'] or 0) for r in rows)

    stats = {
        'projects': len(rows), 'tasks': tt,
        'done': td, 'in_progress': ti, 'todo': to, 'backlog': tb,
        'high': th, 'medium': tm, 'low': tl,
        'completion_pct': p(td, tt),
        'done_pct': p(td,tt), 'inprog_pct': p(ti,tt),
        'todo_pct': p(to,tt), 'backlog_pct': p(tb,tt),
        'high_pct': p(th,tt), 'medium_pct': p(tm,tt), 'low_pct': p(tl,tt),
    }

    project_rows = sorted(
        [{**dict(r), 'completion_pct': p(r['done_count'] or 0, r['task_count'])} for r in rows],
        key=lambda x: x['completion_pct'], reverse=True
    )

    ins = []
    if tt == 0:
        ins.append({'icon': '📋', 'text': 'No tasks across any project yet', 'type': 'neutral'})
    else:
        done_proj = [r for r in project_rows if r['completion_pct'] == 100 and r['task_count'] > 0]
        empty_proj = [r for r in project_rows if r['task_count'] == 0]
        if done_proj:
            n = len(done_proj)
            ins.append({'icon': '🏆', 'text': f"{n} project{'s are' if n != 1 else ' is'} fully complete", 'type': 'good'})
        if empty_proj:
            n = len(empty_proj)
            ins.append({'icon': '📭', 'text': f"{n} project{'s have' if n != 1 else ' has'} no tasks yet", 'type': 'neutral'})
        if ti > 0:
            ins.append({'icon': '⚡', 'text': f"{ti} task{'s' if ti != 1 else ''} currently in progress across all projects", 'type': 'info'})
        if thp > 0:
            ins.append({'icon': '🔴', 'text': f"{thp} high-priority task{'s' if thp != 1 else ''} still pending", 'type': 'warn'})
        busiest = max(project_rows, key=lambda x: x['inprog_count'] or 0)
        if (busiest['inprog_count'] or 0) > 0:
            ins.append({'icon': '📌', 'text': f"'{busiest['name']}' is the most active ({busiest['inprog_count']} in progress)", 'type': 'info'})
        remaining = tt - td
        if remaining > 0:
            ins.append({'icon': '🎯', 'text': f"{remaining} task{'s' if remaining != 1 else ''} left to complete across all projects", 'type': 'info'})

    return templates.TemplateResponse("insights.html", {
        "request": request, "stats": stats,
        "project_rows": project_rows, "insights": ins,
        "current_user": user,
    })


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _get_session_user(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email:    str = Form(...),
    password: str = Form(...),
):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    conn.close()
    if not row or not _verify_password(password, row["password_hash"]):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Invalid email or password",
        }, status_code=401)
    token = _make_session(row["id"])
    resp  = RedirectResponse("/", status_code=302)
    resp.set_cookie("ph_session", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return resp


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    if _get_session_user(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})


@app.post("/signup", response_class=HTMLResponse)
async def signup_post(
    request:  Request,
    username: str = Form(...),
    email:    str = Form(...),
    password: str = Form(...),
    confirm:  str = Form(...),
):
    if password != confirm:
        return templates.TemplateResponse("signup.html", {
            "request": request, "error": "Passwords do not match",
        }, status_code=400)
    if len(password) < 8:
        return templates.TemplateResponse("signup.html", {
            "request": request, "error": "Password must be at least 8 characters",
        }, status_code=400)
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    if existing:
        conn.close()
        return templates.TemplateResponse("signup.html", {
            "request": request, "error": "An account with that email already exists",
        }, status_code=400)
    hashed = _hash_password(password)
    cur = conn.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username.strip(), email.lower().strip(), hashed),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    token = _make_session(user_id)
    resp  = RedirectResponse("/", status_code=302)
    resp.set_cookie("ph_session", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return resp


@app.post("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("ph_session")
    return resp


class UsernameUpdate(BaseModel):
    username: str


@app.post("/settings/username")
async def update_username(request: Request, data: UsernameUpdate):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    name = data.username.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    conn = get_db()
    conn.execute("UPDATE users SET username = ? WHERE id = ?", (name, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True, "username": name}


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


@app.post("/settings/password")
async def update_password(request: Request, data: PasswordUpdate):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conn = get_db()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE id = ?", (user["id"],)
    ).fetchone()
    if not row or not _verify_password(data.current_password, row["password_hash"]):
        conn.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 8:
        conn.close()
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (_hash_password(data.new_password), user["id"]),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    user = _get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("settings.html", {"request": request, "current_user": user})


from fastapi import UploadFile, File
from fastapi.responses import Response as FastAPIResponse


@app.post("/settings/avatar")
async def upload_avatar(request: Request, file: UploadFile = File(...)):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 2MB")
    os.makedirs(AVATARS_DIR, exist_ok=True)
    path = os.path.join(AVATARS_DIR, str(user["id"]))
    with open(path, "wb") as f:
        f.write(content)
    conn = get_db()
    conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (file.content_type, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True, "avatar_url": f"/avatars/{user['id']}"}


@app.get("/avatars/{user_id}")
async def get_avatar(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT avatar FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not row or not row["avatar"]:
        raise HTTPException(status_code=404)
    path = os.path.join(AVATARS_DIR, str(user_id))
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    with open(path, "rb") as f:
        content = f.read()
    return FastAPIResponse(
        content=content,
        media_type=row["avatar"],
        headers={"Cache-Control": "no-store"},
    )


# ── PM-6: Users list (for assignee picker) ────────────────────────────────────

@app.get("/api/users")
async def list_users(request: Request):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    conn = get_db()
    rows = conn.execute("SELECT id, username, avatar FROM users ORDER BY username").fetchall()
    conn.close()
    return [{"id": r["id"], "username": r["username"], "has_avatar": bool(r["avatar"])} for r in rows]


# ── PM-7: Notifications ───────────────────────────────────────────────────────

@app.get("/notifications")
async def get_notifications(request: Request):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM notifications WHERE user_id = ?
        ORDER BY is_read ASC, created_at DESC LIMIT 30
    """, (user["id"],)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/notifications/unread-count")
async def get_unread_count(request: Request):
    user = _get_session_user(request)
    if not user:
        return {"count": 0}
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
        (user["id"],)
    ).fetchone()[0]
    conn.close()
    return {"count": count}


@app.post("/notifications/{notif_id}/read")
async def mark_notification_read(request: Request, notif_id: int):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                 (notif_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/notifications/read-all")
async def mark_all_read(request: Request):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── PM-8: Chat ────────────────────────────────────────────────────────────────

class ChatRoomCreate(BaseModel):
    name: str
    member_ids: List[int] = []

class DirectRoomCreate(BaseModel):
    other_user_id: int

class MessageCreate(BaseModel):
    body: str


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    user = _get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    all_users = conn.execute(
        "SELECT id, username, avatar FROM users WHERE id != ? ORDER BY username",
        (user["id"],)
    ).fetchall()
    conn.close()
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "current_user": user,
        "all_users": [dict(u) for u in all_users],
    })


@app.get("/api/chat/rooms")
async def list_chat_rooms(request: Request):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    conn = get_db()
    rooms = conn.execute("""
        SELECT r.id, r.name, r.type,
               (SELECT body FROM chat_messages WHERE room_id = r.id
                ORDER BY created_at DESC LIMIT 1) AS last_message,
               (SELECT created_at FROM chat_messages WHERE room_id = r.id
                ORDER BY created_at DESC LIMIT 1) AS last_at
        FROM chat_rooms r
        JOIN chat_members m ON m.room_id = r.id
        WHERE m.user_id = ?
        ORDER BY last_at DESC, r.created_at DESC
    """, (user["id"],)).fetchall()
    result = []
    for r in rooms:
        d = dict(r)
        if r["type"] == "direct":
            other = conn.execute("""
                SELECT u.id, u.username FROM users u
                JOIN chat_members cm ON cm.user_id = u.id
                WHERE cm.room_id = ? AND u.id != ?
            """, (r["id"], user["id"])).fetchone()
            if other:
                d["name"] = other["username"]
                d["other_user_id"] = other["id"]
        members = conn.execute("""
            SELECT u.id, u.username FROM users u
            JOIN chat_members cm ON cm.user_id = u.id WHERE cm.room_id = ?
        """, (r["id"],)).fetchall()
        d["members"] = [{"id": m["id"], "username": m["username"]} for m in members]
        result.append(d)
    conn.close()
    return result


@app.post("/api/chat/rooms")
async def create_group_room(request: Request, data: ChatRoomCreate):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Room name required")
    conn = get_db()
    cur = conn.execute("INSERT INTO chat_rooms (name, type) VALUES (?, 'group')", (data.name.strip(),))
    room_id = cur.lastrowid
    member_ids = list({user["id"]} | set(data.member_ids))
    for uid in member_ids:
        conn.execute("INSERT OR IGNORE INTO chat_members (room_id, user_id) VALUES (?, ?)", (room_id, uid))
    conn.commit()
    conn.close()
    return {"id": room_id, "name": data.name, "type": "group"}


@app.post("/api/chat/rooms/direct")
async def get_or_create_direct(request: Request, data: DirectRoomCreate):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    if user["id"] == data.other_user_id:
        raise HTTPException(status_code=400, detail="Cannot DM yourself")
    conn = get_db()
    existing = conn.execute("""
        SELECT r.id FROM chat_rooms r
        JOIN chat_members m1 ON m1.room_id = r.id AND m1.user_id = ?
        JOIN chat_members m2 ON m2.room_id = r.id AND m2.user_id = ?
        WHERE r.type = 'direct' LIMIT 1
    """, (user["id"], data.other_user_id)).fetchone()
    if existing:
        conn.close()
        return {"id": existing["id"], "type": "direct"}
    cur = conn.execute("INSERT INTO chat_rooms (type) VALUES ('direct')")
    room_id = cur.lastrowid
    conn.execute("INSERT INTO chat_members (room_id, user_id) VALUES (?, ?)", (room_id, user["id"]))
    conn.execute("INSERT INTO chat_members (room_id, user_id) VALUES (?, ?)", (room_id, data.other_user_id))
    conn.commit()
    conn.close()
    return {"id": room_id, "type": "direct"}


@app.get("/api/chat/rooms/{room_id}/messages")
async def get_messages(request: Request, room_id: int, since: str = ""):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    conn = get_db()
    if not conn.execute("SELECT 1 FROM chat_members WHERE room_id=? AND user_id=?",
                        (room_id, user["id"])).fetchone():
        conn.close()
        raise HTTPException(status_code=403)
    if since:
        rows = conn.execute("""
            SELECT m.id, m.body, m.created_at, u.id AS sender_id, u.username AS sender_name
            FROM chat_messages m JOIN users u ON u.id = m.sender_id
            WHERE m.room_id = ? AND m.created_at > ?
            ORDER BY m.created_at ASC LIMIT 50
        """, (room_id, since)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.id, m.body, m.created_at, u.id AS sender_id, u.username AS sender_name
            FROM chat_messages m JOIN users u ON u.id = m.sender_id
            WHERE m.room_id = ?
            ORDER BY m.created_at DESC LIMIT 60
        """, (room_id,)).fetchall()
        rows = list(reversed(rows))
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/chat/rooms/{room_id}/messages")
async def send_message(request: Request, room_id: int, data: MessageCreate):
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=401)
    body = data.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    conn = get_db()
    if not conn.execute("SELECT 1 FROM chat_members WHERE room_id=? AND user_id=?",
                        (room_id, user["id"])).fetchone():
        conn.close()
        raise HTTPException(status_code=403)
    cur = conn.execute(
        "INSERT INTO chat_messages (room_id, sender_id, body) VALUES (?, ?, ?)",
        (room_id, user["id"], body),
    )
    msg_id = cur.lastrowid
    # Notify all room members (except sender) of the new message
    members = conn.execute(
        "SELECT user_id FROM chat_members WHERE room_id = ? AND user_id != ?",
        (room_id, user["id"])
    ).fetchall()
    room_name = conn.execute("SELECT name, type FROM chat_rooms WHERE id = ?", (room_id,)).fetchone()
    notif_title = (f"{user['username']}" if room_name and room_name["type"] == "direct"
                   else f"{user['username']} in {room_name['name'] or 'chat'}")
    for m in members:
        _create_notification(conn, m["user_id"], "message",
            notif_title, body[:120], "/chat")
    # Also handle @mentions specifically
    for username in set(re.findall(r'@(\w+)', body)):
        mentioned = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if mentioned and mentioned["id"] != user["id"]:
            _create_notification(conn, mentioned["id"], "mention",
                f"{user['username']} mentioned you in chat", body[:120], "/chat")
    conn.commit()
    row = conn.execute("""
        SELECT m.id, m.body, m.created_at, u.id AS sender_id, u.username AS sender_name
        FROM chat_messages m JOIN users u ON u.id = m.sender_id WHERE m.id = ?
    """, (msg_id,)).fetchone()
    conn.close()
    return dict(row)
