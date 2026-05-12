# Lab Management System — Agent Guide

## Quick start

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python lab_management_app.py
```

Server starts at `http://localhost:5000`.

## Entrypoint

`lab_management_app.py` (~4500 lines) — single Flask app containing all routes, models, socket handlers, DB migrations, and Docker orchestration. There is no package split; everything lives in this one file.

## Architecture

- **3 nginx backends**: A (`192.168.187.99:5000`), B (`192.168.187.98:5000`), C (`127.0.0.1:5000`)
- **2 flow types**: `LABTAINER` → backend A (even lab_id) or B (odd lab_id); `CUSTOM` → backend C
- Routing is defined in `nginx/labtainer.local.com.conf` — it's the authoritative source for which backend handles which request.
- Socket.IO sessions route to the same backend as the lab (by lab_id parity).
- Port ranges are DB-managed: web 8000–10000, client 50000–60000, db 3000–5000. Populate with `python setup_mysql.py ports`.

## Setup commands

| Task | Command |
|------|---------|
| DB migration | `python setup_mysql.py migrate` |
| Check DB status | `python setup_mysql.py status` |
| Create sample lab | `python setup_mysql.py sample` |
| Populate ports table | `python setup_mysql.py ports` |
| Docker deployment | `docker compose up -d` |

## Database

- MySQL via `pymysql` (with `install_as_MySQLdb()`).
- `DATABASE_URL` in `.env`, format: `mysql+pymysql://user:pass@host:3306/lab_management`
- Tables auto-created on startup via `db.create_all()`.
- Best-effort schema patching at startup (adds `flow_type` column if missing). For proper migrations use `setup_mysql.py`.
- 9 tables: `users`, `courses`, `labs`, `lab_parameters`, `enrollments`, `lab_sessions`, `terminal_sessions`, `command_logs`, `labs_network`, `ports`.

## Config

- `.env` file loaded via `python-dotenv`. Template in `.env.template`.
- Docker secrets override `.env` at runtime via `entrypoint.sh` (uses `envsubst` on `.env.template`).
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` must be set for login to work.
- `ALLOWED_COMMANDS` is a JSON array (command validation is **commented out** in `validate_command_access`).
- `ALLOWED_EMAIL_REGEX` restricts login to `.edu` emails (validation is **commented out** in `auth_callback`).

## Key conventions

- **No tests, no linter, no formatter, no typechecker** configured.
- `.vscode/settings.json` maps `*.html` → `jinja-html` language mode.
- CSRF protection via `X-CSRF-Token` header (auto-injected by frontend fetch wrapper).
- Student Linux usernames follow `student_{email_prefix}` pattern.
- Lab parameter placeholders: `${studentName}`, `${studentId}`, `${labNetworkMask}`, `${labNetworkGateway}`, `${labSubnetIpPrefix}`, `${webTestPort}`, `${clientTestPort}`, `${dbTestPort}`, `${labRandomString}`, `${webTestUrl}`, `${clientTestUrl}`, `${dockerExecCommand}`, `${email}`, `${randomKey}`.
- Auto badge generation: `FLAG{SHA1(DDMMYYYY_email_expectedAnswer)}` (timezone Asia/Ho_Chi_Minh).
- Checkpoint submission format for auto-flag: `FLAG{...}::random_string` or `FLAG{...}|random_string`.
- `validate_command_access` has most checks **commented out** — only dangerous pattern regex (`..`, `/etc/`, etc.) is active.
- `is_edu_email` validation in `auth_callback` is **commented out** — all Google accounts can log in.

## Docker / Linux

- `cleanup_docker_resources(student_name, clean_docker_only)` removes containers, networks, and services by student key.
- `create_student_docker()` generates a shell script at `/usr/local/bin/docker_client_shell_{containerName}` and a sudoers rule for the student user.
- `entrypoint.sh` reads Docker secrets and renders `.env` via `envsubst`.
- CMD: `python lab_management_app.py`.

## Monitoring

- Prometheus `/metrics` endpoint (optional — requires `prometheus_client`).
- Health check at `/healthz`.
- Logs go to `logs/lab_management.log` with rotation (10MB, 5 backups).

## Deployment

- Nginx config expects self-signed certs at `/etc/nginx/self.crt` and `/etc/nginx/self.key`.
- `labtainer.local.com` is the server_name — access via host header or local DNS.
- `proxy_read_timeout` for lab start: 1200s; web proxy: 600s; WebSocket: 3600s.


# Distributed Cybersecurity Lab Platform Architecture

## Overview

The system is a distributed cybersecurity lab platform built on top of Docker Swarm.  
It is designed to dynamically provision isolated vulnerable lab environments for each student.

Each student receives:
- A dedicated Docker Swarm stack
- Separate vulnerable containers
- Isolated internal networking
- Dedicated web terminal access
- Dynamically generated flags and environment variables

The platform supports multiple vulnerability labs such as:
- SQL Injection
- XSS
- IDOR
- Race Condition
- SMB Exploitation
- SSH Brute Force
- FTP/SSH Exploitation

---

# System Architecture

## Main Components

### 1. Manager Node
Responsibilities:
- Run backend Python APIs
- Execute Docker Swarm commands
- Deploy/remove student lab stacks
- Allocate available ports
- Route requests via Nginx
- Manage web terminal sessions

Technologies:
- Docker Swarm Manager
- Python Backend (Flask/FastAPI)
- Nginx Reverse Proxy

---

### 2. Worker Nodes
Responsibilities:
- Run vulnerable lab containers
- Execute student environments
- Store pulled Docker images locally

Characteristics:
- Joined into Docker Swarm cluster
- Identified using labels:
  ```bash
  docker node update --label-add labnode=98 <node-id>


Deployment Model
Stack Per Student

Each student receives a separate Docker Stack.

Naming convention:

lab_<lab_id>_<student_id>

Example:

lab_4_hoangnth

Generated services:

lab_4_hoangnth_web
lab_4_hoangnth_db
lab_4_hoangnth_client
Container Placement Strategy

All containers of a single lab are forced to run on the same worker node.

Docker Swarm placement constraint:

deploy:
  placement:
    constraints:
      - node.labels.labnode == ${TARGET_NODE}

Benefits:

Shared local volumes
Reduced latency
Simplified networking
Better isolation
Easier terminal attachmen