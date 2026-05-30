# ProjectHub

A self-hosted project management and team collaboration tool. Kanban boards, phases, real-time chat, notifications, and a built-in MCP server for Claude AI integration — all running in a single Docker container.

## Features

### Project Management
- **Kanban board** — drag-and-drop tasks across Todo, In Progress, Testing, and Done columns
- **Backlog** — full task list grouped by phase with inline status updates and bulk actions
- **Phases** — organise tasks into sprints or milestones with a planning drag-and-drop board
- **Tasks** — title, description, type (task/bug), priority, status, due date, assignee, phase assignment
- **Dependencies** — mark tasks as blocked by other tasks
- **Comments** — threaded comments on tasks with @mention notifications
- **Webhooks** — POST a JSON payload to any URL on task status change
- **Stats** — completion ring, status breakdown, priority distribution, phase summaries, insights

### Real-time Chat
- **Direct messages** — one-on-one conversations with any team member
- **Group rooms** — create named rooms, add/remove members, search and filter with avatar-chip picker
- **WebSocket delivery** — messages appear instantly with no polling delay
- **@mention autocomplete** — type `@` to get a filtered dropdown of room members; highlighted in rendered messages
- **Read receipts** — "Seen by X" indicator on your last read message
- **Notifications** — bell icon with unread count; clicking a notification opens the relevant chat room

### People & Settings
- **Multi-user** — each person gets their own account; runs on your local network
- **Profile** — upload a profile photo (updates nav icon instantly), edit display name
- **Password** — change password with strength indicator
- **Themes** — 6 colour themes × light/dark mode: Professional, Hacking, Tron, Emerald Valley, Ember, Crimson

## Setup

**Requirements:** [Docker](https://www.docker.com/products/docker-desktop/) + [Docker Compose](https://docs.docker.com/compose/)

```bash
# Clone the repo
git clone https://github.com/AceARG/projecthub.git
cd projecthub

# Build and start
docker compose up -d --build
```

Open **http://localhost:8000** — create an account and you're in.

```bash
# Stop
docker compose down

# Restart (no rebuild)
docker compose restart

# View logs
docker compose logs -f
```

> Your database and uploaded avatars are stored in `./data/` on your machine and are never committed to git.

## MCP Integration (Claude AI)

Register the MCP server once with the Claude CLI:

```bash
claude mcp add projecthub python "/path/to/projecthub_mcp.py"
```

If your server is not at `http://localhost:8000`:

```bash
claude mcp add projecthub python "/path/to/projecthub_mcp.py" --env PROJECTHUB_URL=http://your-host:8000
```

Then from inside any repo, Claude can auto-detect and manage your project:

```
> find_project_by_repo(".")   # link this repo to a project
> get_project_context(id)     # full project summary
> get_active_phase_tasks(id)  # current sprint tasks
> list_tasks(id, phase_id=X)  # filter by phase
```

## Tech Stack

- **Backend** — Python, FastAPI, SQLite (WAL mode)
- **Real-time** — WebSockets (FastAPI native)
- **Frontend** — Jinja2 templates, vanilla JS
- **Auth** — itsdangerous signed cookies, bcrypt
- **Container** — Docker + Docker Compose
