# ProjectHub

A self-hosted project management tool with kanban boards, phases, backlog tracking, and a built-in MCP server for Claude AI integration.

## Features

- **Projects** — kanban board, backlog, phases, and stats per project
- **Auth** — signup, login, session-based authentication
- **Settings** — profile picture upload, display name, password, appearance themes
- **MCP server** — Claude AI can read and update your tasks directly via the CLI
- **Multi-user ready** — runs on your local network, each user gets their own account

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

- **Backend** — Python, FastAPI, SQLite
- **Frontend** — Jinja2 templates, vanilla JS
- **Auth** — itsdangerous signed cookies, bcrypt
- **Container** — Docker + Docker Compose
