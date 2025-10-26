# Labtainer Lab Management System

## Overview
A comprehensive web-based lab management system that integrates with Labtainer for cybersecurity education. The system provides user authentication, course enrollment, lab management, and a browser-based terminal for accessing lab environments.

**Technology Stack:**
- Backend: Flask with Flask-SocketIO, Flask-Login, Flask-Dance (OAuth)
- Frontend: HTML/CSS with xterm.js terminal emulator
- Database: SQLite with SQLAlchemy ORM
- Authentication: Replit Auth (supports Google, GitHub, email/password)
- Real-time Communication: Socket.IO over WebSockets

## Purpose
This system enables educational institutions to:
- Manage cybersecurity lab exercises using Labtainer
- Control user access with .edu email verification
- Track student progress across courses and labs
- Provide browser-based terminal access to lab environments
- Automatically provision lab instances when students enroll

## Current State
✅ Fully functional lab management system
✅ Authentication with .edu email requirement
✅ Course and lab enrollment system
✅ Dashboard showing user progress
✅ Web-based terminal with PTY support
✅ Automatic lab folder creation on enrollment
✅ SQLite database with proper relationships

## Recent Changes (October 26, 2025)
- Migrated from aiohttp to Flask for better authentication support
- Integrated Replit Auth with .edu email verification
- Created SQLAlchemy models for Users, Courses, Labs, Enrollments, UserLabs
- Built complete dashboard UI with course browsing and enrollment
- Implemented automatic lab provisioning (userid-labname format)
- Added Flask-SocketIO for terminal websocket connections
- Created responsive templates for landing, dashboard, courses, terminal
- Set up session management and OAuth token handling

## Project Architecture

### Backend Structure
```
main.py              - Application entry point
app.py               - Flask app initialization and database setup
models.py            - SQLAlchemy database models
routes.py            - Route handlers and SocketIO events
replit_auth.py       - Authentication blueprint and decorators
database.py          - Legacy SQLite helper (can be removed)
```

### Database Models

#### User (Required for Replit Auth)
- id: String (from OAuth provider)
- email: String (must end with .edu)
- first_name, last_name, profile_image_url
- Relationships: enrollments, user_labs

#### OAuth (Required for Replit Auth)
- Stores OAuth tokens per user/session

#### Course
- id, name, description
- Relationships: labs, enrollments

#### Lab
- id, course_id, name, template_folder, description
- Represents lab templates available in Labtainer

#### Enrollment
- User-Course relationship
- Automatically created when user enrolls

#### UserLab
- Individual lab instances for each user
- folder_name: Format is `{user_id}-{template_folder}`
- status: ENROLLED, ACTIVE, COMPLETED
- Tracks last_accessed time

### Frontend Templates
- `landing.html` - Public landing page with login button
- `dashboard.html` - User dashboard showing courses and labs
- `courses.html` - Course catalog with enrollment functionality
- `terminal.html` - Web terminal interface with xterm.js
- `403.html` - Error page for non-.edu email attempts

### Key Features

#### 1. Authentication & Authorization
- Replit Auth OAuth flow (Google, GitHub, email/password)
- .edu email verification in `save_user()` function
- Session management with Flask-Login
- Protected routes using `@require_login` decorator

#### 2. Course Management
- Browse available courses
- Enroll in courses with one click
- View enrolled courses on dashboard
- Automatic lab assignment on enrollment

#### 3. Lab Provisioning
- When user enrolls in a course:
  1. System randomly selects a lab template from the course
  2. Creates unique folder name: `{user_id}-{template_folder}`
  3. Records lab instance in database with status ENROLLED
- In production, this would trigger Labtainer folder cloning

#### 4. Web Terminal
- Full PTY (pseudo-terminal) support
- Real-time bidirectional communication via Socket.IO
- Terminal resizing support
- Each client gets isolated bash shell
- Can be accessed standalone or tied to specific lab

#### 5. Labtainer Integration Points
The system is designed to integrate with Labtainer commands:
- `rebuild <folder-name>` - Rebuild a lab environment
- `labtainer start <folder-name>` - Start a lab
- `labtainer stop <folder-name>` - Stop a lab

These commands can be executed through the web terminal interface.

## User Workflow

1. **Login** - User visits site, clicks "Login with .edu Account"
2. **OAuth** - Replit Auth handles authentication with chosen provider
3. **Email Verification** - System verifies email ends with .edu
4. **Dashboard** - User sees their enrolled courses and active labs
5. **Browse Courses** - User can view available courses
6. **Enroll** - Clicking "Enroll" automatically:
   - Creates enrollment record
   - Selects random lab template
   - Creates unique lab folder
   - Updates database
7. **Access Terminal** - User can open terminal for specific lab or standalone
8. **Work in Lab** - Execute Labtainer commands in browser terminal

## Running the Application

The server runs automatically via the configured Flask workflow:
```bash
python3 main.py
```

Server binds to `0.0.0.0:5000` and is accessible through Replit's webview.

## Sample Data Initialization

Visit `/init_sample_data` while logged in to populate the database with:
- 3 sample courses (Intro to Cybersecurity, Advanced Network Security, Web App Security)
- 6 sample labs (recon-lab, sql-injection-lab, buffer-overflow-lab, firewall-lab, vpn-lab, xss-lab)

## Security Considerations

### Current Security Features
✅ .edu email verification
✅ OAuth-based authentication (no password storage)
✅ Session management with secure cookies
✅ PKCE flow for OAuth
✅ Token refresh handling
✅ Isolated bash shells per user session

### ⚠️ CRITICAL: NOT PRODUCTION READY
**Do NOT deploy this to production or give access to untrusted users.**

This is a development/prototype implementation with known security vulnerabilities:
- ❌ Path traversal possible in lab operations
- ❌ Command injection risk in Labtainer commands
- ❌ WebSocket authentication incomplete
- ❌ Lab provisioning lacks transaction safety
- ❌ Terminal doesn't actually enter Labtainer containers
- ❌ No input sanitization on folder names
- ❌ Status updates not verified against actual state

**See KNOWN_LIMITATIONS.md for complete security analysis and remediation steps.**

### Additional Important Notes
⚠️ Users get full bash shell access - only use in sandboxed environments
⚠️ SESSION_SECRET should be set in production (currently uses fallback)
⚠️ SQLite is suitable for development; consider PostgreSQL for production
⚠️ File system isolation between lab instances not yet implemented
⚠️ Actual Labtainer integration requires production hardening

## Future Enhancements

### Planned Features
- [ ] Actual Labtainer integration (folder cloning, command execution)
- [ ] File system isolation per lab instance
- [ ] Progress tracking and completion status
- [ ] Lab submission and grading system
- [ ] Admin panel for course/lab management
- [ ] User activity logging
- [ ] Resource limits and quotas
- [ ] Migrate to PostgreSQL for production
- [ ] Add lab instructions and documentation viewer
- [ ] Implement lab checkpoints and save states

## Environment Variables

- `SESSION_SECRET` - Flask session secret (auto-generated in dev)
- `REPL_ID` - Replit project ID (for OAuth)
- `ISSUER_URL` - OAuth issuer URL (defaults to https://replit.com/oidc)

## API Endpoints

### Public Routes
- `GET /` - Landing page
- `GET /auth/login` - Start OAuth flow
- `GET /auth/logout` - Logout and clear session

### Protected Routes (require login)
- `GET /dashboard` - User dashboard
- `GET /courses` - Browse courses
- `POST /enroll/<course_id>` - Enroll in course
- `GET /terminal` - Standalone terminal
- `GET /terminal/<lab_id>` - Lab-specific terminal
- `GET /init_sample_data` - Initialize sample data

### WebSocket Events
- `connect` - Client connects, spawns PTY
- `pty_input` - Send input to terminal
- `pty_resize` - Update terminal dimensions
- `pty_output` - Receive terminal output
- `disconnect` - Cleanup PTY and process

## Development Notes

### File Changes from Original
- Renamed `app.py` → `app_old.py` (aiohttp version)
- Created new Flask-based application structure
- Migrated terminal functionality to Flask-SocketIO
- Removed `database.py` dependency (using SQLAlchemy models)
- Updated `requirements.txt` to Flask ecosystem
- Modified `static/main.js` removed (integrated into templates)

### Database Schema
The SQLAlchemy models automatically create tables with proper foreign keys and constraints. The schema supports:
- One-to-many: Course → Labs
- Many-to-many: Users ↔ Courses (through Enrollments)
- One-to-many: Users → UserLabs
- Unique constraints on enrollments and user labs
