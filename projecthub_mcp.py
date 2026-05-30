#!/usr/bin/env python3
"""
ProjectHub MCP Server
─────────────────────
Connects to a running ProjectHub instance over HTTP.
No database files or personal directory paths required.

Requirements (install locally, NOT inside Docker):
    pip install mcp

Configuration:
    Set PROJECTHUB_URL to point at your ProjectHub server (default: http://localhost:8000).

    Register via CLI:
        claude mcp add projecthub python /path/to/projecthub_mcp.py

    Or add to ~/.claude/settings.json:
        {
          "mcpServers": {
            "projecthub": {
              "command": "python",
              "args": ["/path/to/projecthub_mcp.py"],
              "env": { "PROJECTHUB_URL": "http://localhost:8000" }
            }
          }
        }

Environment variables:
    PROJECTHUB_URL  — base URL of the ProjectHub server  (default: http://localhost:8000)
"""

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from mcp.server.fastmcp import FastMCP

BASE_URL = os.getenv("PROJECTHUB_URL", "http://localhost:8000").rstrip("/")

mcp = FastMCP("ProjectHub")


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(path: str, params: dict | None = None) -> object:
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


def _post(path: str, body: dict) -> object:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE_URL + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _put(path: str, body: dict) -> object:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE_URL + path, data=data,
        headers={"Content-Type": "application/json"}, method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _delete(path: str) -> object:
    req = urllib.request.Request(BASE_URL + path, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_projects() -> list[dict]:
    """
    List all ProjectHub projects with their id, name, description,
    repo_path, color, and task counts.
    """
    return _get("/api/projects")


def _normalize_git_url(url: str) -> str:
    url = url.strip()
    if url.startswith("git@"):
        url = url.replace(":", "/", 1).replace("git@", "https://", 1)
    if url.endswith(".git"):
        url = url[:-4]
    return url.lower().rstrip("/")


def _git_remote_url(directory: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=directory, capture_output=True, text=True, timeout=3,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        if result.returncode == 0 and result.stdout.strip():
            return _normalize_git_url(result.stdout.strip())
    except Exception:
        pass
    return None


@mcp.tool()
def find_project_by_repo(path: str) -> dict | None:
    """
    Find the ProjectHub project that matches the given path or URL.

    Pass the current working directory — the tool will:
      1. Check if the directory's git remote (origin) matches any stored repo_path
      2. Fall back to direct URL matching if a URL is passed

    Works with both GitHub URLs (https://github.com/user/repo.git) and local paths.
    """
    lookup_url = None

    if os.path.isdir(path):
        lookup_url = _git_remote_url(path)

    if not lookup_url and path.startswith(("http", "git@")):
        lookup_url = _normalize_git_url(path)

    if lookup_url:
        result = _get("/api/projects/by-repo", {"url": lookup_url})
        if result:
            return result

    # Fallback: list all projects and do local path matching
    projects = _get("/api/projects")
    if isinstance(projects, list):
        norm = os.path.normpath(path).lower()
        best = None
        for p in projects:
            repo = p.get("repo_path", "")
            if not repo or repo.startswith(("http", "git@")):
                continue
            repo_norm = os.path.normpath(repo).lower()
            if norm == repo_norm or norm.startswith(repo_norm + os.sep):
                if best is None or len(repo) > len(best.get("repo_path", "")):
                    best = p
        return best
    return None


@mcp.tool()
def get_project_context(project_id: int) -> str:
    """
    Return a full plain-text summary of a project: description, repo path,
    phases (with status and completion), all tasks grouped by status,
    and any active/pending plans that need attention.
    Feed this to yourself at the start of a coding session.
    """
    data = _get(f"/api/projects/{project_id}/context")
    if "error" in data:
        return f"Error: {data['error']}"

    proj   = data.get("project", {})
    tasks  = data.get("tasks", [])
    phases = data.get("phases", [])
    plans  = data.get("plans", [])

    lines = [
        f"# {proj.get('name', project_id)}",
        f"Description : {proj.get('description') or '(none)'}",
        f"Repo        : {proj.get('repo_path') or '(not set)'}",
        "",
    ]

    _agent_actions = {
        "scope-pending":        "-> YOUR TURN: call get_plan({id}) then post_plan_message / submit_scope",
        "scope-review":         "-> Awaiting user approval in web UI",
        "technical-pending":    "-> USER'S TURN: technical analysis (or submit_technical_analysis({id}, doc))",
        "technical-review":     "-> Awaiting user approval in web UI",
        "architecture-pending": "-> YOUR TURN: call get_plan({id}) then post_plan_message / submit_architecture",
        "architecture-review":  "-> Awaiting user approval in web UI",
    }
    if plans:
        lines.append("## Plans Needing Attention")
        for p in plans:
            hint = _agent_actions.get(p["status"], "").replace("{id}", str(p["id"]))
            lines.append(f"  Plan #{p['id']} [{p['status'].upper():22}]  {p['name']}")
            if hint:
                lines.append(f"           {hint}")
        lines.append("")

    if phases:
        lines.append("## Phases")
        for ph in phases:
            ph_tasks = [t for t in tasks if t.get("phase_id") == ph["id"]]
            done = sum(1 for t in ph_tasks if t["status"] == "done")
            pct  = round(done / len(ph_tasks) * 100) if ph_tasks else 0
            lines.append(f"  [{ph['status'].upper():8}] {ph['name']}  --  {len(ph_tasks)} tasks, {pct}% done")
        lines.append("")

    by_status: dict = {"in-progress": [], "todo": [], "testing": [], "backlog": [], "done": []}
    for t in tasks:
        by_status.setdefault(t["status"], []).append(t)

    for label, key in [("In Progress", "in-progress"), ("Todo", "todo"),
                       ("Testing", "testing"), ("Backlog", "backlog"), ("Done", "done")]:
        group = by_status.get(key, [])
        if not group:
            continue
        lines.append(f"## {label} ({len(group)})")
        for t in group:
            phase_name = ""
            if t.get("phase_id"):
                ph = next((p for p in phases if p["id"] == t["phase_id"]), None)
                if ph:
                    phase_name = f"  [{ph['name']}]"
            lines.append(f"  #{t['id']} [{t['priority'].upper():6}]{phase_name}  {t['title']}")
            if t.get("description"):
                lines.append(f"           {t['description']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def list_tasks(
    project_id: int,
    status: str   = "",
    priority: str = "",
    phase_id: int = 0,
) -> list[dict]:
    """
    List tasks for a project with optional filters.

    status   : backlog | todo | in-progress | testing | done  (empty = all)
    priority : low | medium | high                            (empty = all)
    phase_id : phase id to filter by                         (0 = all phases)
    """
    params: dict = {}
    if status:   params["status"]   = status
    if priority: params["priority"] = priority
    if phase_id: params["phase_id"] = phase_id
    return _get(f"/api/projects/{project_id}/tasks", params or None)


@mcp.tool()
def get_task(task_id: int) -> dict:
    """Get full details for a single task by id, including its ticket ID."""
    return _get(f"/tasks/{task_id}")


@mcp.tool()
def update_task_status(task_id: int, status: str) -> dict:
    """
    Update a task's status.
    Valid values: backlog | todo | in-progress | testing | done

    Use this to mark tasks in-progress when you start working on them,
    and done when you finish.
    """
    valid = {"backlog", "todo", "in-progress", "testing", "done"}
    if status not in valid:
        return {"error": f"Invalid status '{status}'. Choose from: {', '.join(sorted(valid))}"}
    return _put(f"/tasks/{task_id}", {"status": status})


@mcp.tool()
def create_task(
    project_id:  int,
    title:       str,
    description: str = "",
    status:      str = "todo",
    priority:    str = "medium",
    type:        str = "task",
    phase_id:    int = 0,
) -> dict:
    """
    Create a new task in a project.

    priority : low | medium | high        (default: medium)
    status   : backlog | todo | in-progress | testing | done  (default: todo)
    type     : task | bug                 (default: task)
    phase_id : assign to a phase immediately  (0 = no phase)

    Returns the created task with its ticket_id (e.g. NCF-9).
    """
    body: dict = {
        "title": title, "description": description,
        "status": status, "priority": priority, "type": type,
    }
    if phase_id:
        body["phase_id"] = phase_id
    return _post(f"/projects/{project_id}/tasks", body)


@mcp.tool()
def list_phases(project_id: int) -> list[dict]:
    """
    List all phases for a project with task counts and completion percentage.
    """
    return _get(f"/api/projects/{project_id}/phases")


@mcp.tool()
def get_active_phase_tasks(project_id: int) -> dict:
    """
    Return tasks for the currently active phase, grouped by status.

    Use this at the start of a session to see exactly what is in scope for
    the current sprint/phase without manually looking up phase IDs.

    Returns:
      {
        "phase":       { id, name, status, completion_pct },
        "in_progress": [...tasks],
        "todo":        [...tasks],
        "testing":     [...tasks],
        "done":        [...tasks],
        "backlog":     [...tasks],
      }

    If no phase has status='active', returns {"error": "No active phase"}.
    """
    return _get(f"/api/projects/{project_id}/active-phase-tasks")


# ── Plans ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_plan_messages(plan_id: int, step: int) -> list[dict]:
    """
    Return the chat history for a specific step of a plan.
    step: 1 (scope), 2 (technical), 3 (architecture)
    """
    return _get(f"/plans/{plan_id}/messages", {"step": step})


@mcp.tool()
def post_plan_message(plan_id: int, step: int, message: str) -> dict:
    """
    Post a message as the agent in the plan's step chat.
    step: 1 (scope discussion), 3 (architecture discussion)
    """
    return _post(f"/plans/{plan_id}/messages", {"step": step, "content": message, "role": "agent"})


@mcp.tool()
def list_plans(project_id: int, status: str = "") -> list[dict]:
    """
    List plans for a project (summary only, no full doc content).
    Optionally filter by status.
    """
    params = {"status": status} if status else None
    return _get(f"/projects/{project_id}/plans", params)


@mcp.tool()
def get_plan(plan_id: int) -> dict:
    """
    Get full plan details: scope_doc, technical_analysis, architecture_doc, status.
    """
    return _get(f"/plans/{plan_id}")


@mcp.tool()
def submit_scope(plan_id: int, scope_doc: str) -> dict:
    """
    Submit the completed scope analysis document.
    Transitions: scope-pending -> scope-review (user approves in web UI).
    """
    return _put(f"/plans/{plan_id}", {"scope_doc": scope_doc, "status": "scope-review"})


@mcp.tool()
def submit_technical_analysis(plan_id: int, technical_analysis: str) -> dict:
    """
    Submit the technical analysis document.
    Transitions: technical-pending -> technical-review (user approves in web UI).
    """
    return _put(f"/plans/{plan_id}", {"technical_analysis": technical_analysis, "status": "technical-review"})


@mcp.tool()
def submit_architecture(plan_id: int, architecture_doc: str) -> dict:
    """
    Submit the architecture document.
    Transitions: architecture-pending -> architecture-review (user approves in web UI).
    """
    return _put(f"/plans/{plan_id}", {"architecture_doc": architecture_doc, "status": "architecture-review"})


@mcp.tool()
def create_tasks_from_plan(plan_id: int, tasks: list[dict]) -> dict:
    """
    Create backlog tasks from the approved architecture and mark the plan as done.

    Each task dict fields:
      title        (required)
      description  (optional)
      priority     (optional) — low | medium | high
      type         (optional) — task | bug
      phase_id     (optional) — assign to an existing phase (int)
    """
    return _post(f"/plans/{plan_id}/create-tasks", {"tasks": tasks})


@mcp.tool()
def get_plans_needing_attention(project_id: int) -> list[dict]:
    """
    Return plans that need agent action right now (scope-pending, technical-pending,
    or architecture-pending). Use this as your starting point when checking in on a project.
    """
    all_plans = _get(f"/projects/{project_id}/plans")
    if not isinstance(all_plans, list):
        return all_plans
    pending = {"scope-pending", "technical-pending", "architecture-pending"}
    return [p for p in all_plans if p.get("status") in pending]


@mcp.tool()
def update_plan(plan_id: int, name: str = "", description: str = "", notes: str = "") -> dict:
    """
    Update mutable plan fields. Pass only the fields you want to change.
    """
    body = {}
    if name:        body["name"]        = name
    if description: body["description"] = description
    if notes:       body["notes"]       = notes
    if not body:
        return _get(f"/plans/{plan_id}")
    return _put(f"/plans/{plan_id}", body)


@mcp.tool()
def delete_plan(plan_id: int) -> dict:
    """
    Permanently delete a plan and all its messages.
    """
    return _delete(f"/plans/{plan_id}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
