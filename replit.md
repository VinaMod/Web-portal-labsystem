# Labtainer Backend System

## Project Overview
A Python Flask backend system that integrates with a Labtainer server for managing cybersecurity lab exercises. The system provides secure authentication, lab management, and real-time terminal interaction for educational cybersecurity environments.

**Current Status:** ✅ Fully functional and tested (as of October 26, 2025)

## Architecture

### Technology Stack
- **Backend Framework:** Flask with SocketIO for WebSocket support
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** Google OAuth 2.0 with .edu email restriction + JWT tokens
- **Real-time Communication:** Flask-SocketIO for WebSocket connections
- **Security:** CORS protection, JWT authentication, command whitelisting

### Key Components

1. **Database Models** (`models.py`, `database.py`)
   - User: Student accounts with Google OAuth
   - Course: Cybersecurity courses
   - Lab: Individual lab instances with status tracking
   - LabTemplate: Reusable lab configurations
   - UserCourse: Many-to-many enrollment relationship

2. **Main Application** (`app.py`)
   - REST API endpoints for lab management
   - WebSocket handlers for real-time interaction
   - Google OAuth integration with .edu validation
   - JWT token generation and verification
   - Labtainer command execution via subprocess

3. **Lab Management System**
   - Templates stored in `./labs/` directory
   - Automatic cloning with user-specific naming: `{user_id}-{template_folder}`
   - Status tracking: ENROLLED → STARTED → COMPLETED

## Important Implementation Details

### Critical Bug Fix (Oct 26, 2025)
**Issue:** Lab folder naming mismatch between creation and command execution
- **Fixed:** Added `folder_name` field to Lab model to store actual cloned folder name
- **Impact:** All Labtainer commands now target correct directories

### Database Schema
```
labs table requires:
- folder_name: The actual cloned folder name (e.g., "1-network-analysis")
- folder_path: Full path to lab directory
```

**⚠️ Note:** Database must be recreated or migrated when schema changes occur. Use `python seed_data.py` to reset.

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate Google OAuth flow
- `GET /auth/login/callback` - OAuth callback handler

### Lab Management (Requires JWT)
- `GET /dashboard` - User's enrolled courses and labs with status
- `POST /register-lab` - Register for course and clone random lab template
- `GET /labs` - List user's labs
- `GET /courses` - List all available courses

### WebSocket Events
**Client → Server:**
- `authenticate` - Authenticate with JWT token
- `start_lab` - Rebuild and start lab session
- `execute_command` - Run Labtainer commands

**Server → Client:**
- `output` - Command output/terminal text
- `lab_status` - Lab status updates
- `error` - Error messages

## Environment Configuration

### Required Secrets
```env
DATABASE_URL - PostgreSQL connection (auto-configured on Replit)
SESSION_SECRET - JWT signing key (auto-configured)
GOOGLE_OAUTH_CLIENT_ID - Google OAuth client ID (MUST be set)
GOOGLE_OAUTH_CLIENT_SECRET - Google OAuth client secret (MUST be set)
LAB_BASE_PATH - Lab templates directory (default: ./labs)
```

### Google OAuth Setup
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `https://{your-replit-domain}/auth/login/callback`
4. Set client ID and secret in Secrets

## File Structure
```
.
├── app.py                 # Main Flask application
├── models.py             # SQLAlchemy database models
├── database.py           # Database configuration
├── seed_data.py          # Database seeding script
├── test_api.py           # API testing script
├── README.md             # User documentation
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
└── labs/                 # Lab template directories
    ├── network-analysis/
    ├── buffer-overflow/
    └── sql-injection/
```

## Workflow Configuration
- **Name:** Backend API Server
- **Command:** `python app.py`
- **Port:** 5000 (Flask + SocketIO)
- **Output:** Console (backend-only API)

## Security Features
✅ .edu email validation (only university emails allowed)
✅ JWT-based API authentication
✅ Command whitelisting (only Labtainer commands)
✅ User isolation (unique lab folders per user)
✅ CORS protection with configurable origins
✅ Session-based WebSocket authentication

## User Preferences
None specified yet.

## Recent Changes

### 2025-10-26: Initial Implementation
- Created complete Flask backend with all required APIs
- Implemented Google OAuth with .edu restriction
- Added WebSocket support for real-time lab interaction
- Created database models with proper relationships
- Fixed critical folder naming bug in lab management
- Added comprehensive logging and error handling
- Created seed data with 3 courses and 3 lab templates

## Known Limitations
1. **Development Server:** Using Flask development server (suitable for testing only)
2. **Lab Templates:** Only 3 templates available (network-analysis, buffer-overflow, sql-injection)
3. **Google OAuth Required:** Cannot test auth without Google credentials configured
4. **Labtainer Server:** Assumes Labtainer is installed and commands are available

## Testing
- Health check: `curl http://localhost:5000/health`
- Run test script: `python test_api.py`
- Manual testing requires Google OAuth setup

## Deployment Notes
- Set production secrets before deploying
- Use production WSGI server (e.g., gunicorn)
- Configure proper CORS origins
- Ensure Labtainer server is accessible
- Create actual lab template content in `./labs/` directories

## Future Enhancements
- Add lab progress tracking with step completion
- Implement admin panel for course management
- Add lab session timeout and cleanup
- Create submission and grading workflow
- Add instructor monitoring dashboard
- Implement automated testing suite
- Add rate limiting for API endpoints
- Create comprehensive integration tests

## Troubleshooting

### "Google OAuth not configured"
→ Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in Secrets

### "Only .edu email addresses allowed"
→ This is by design - only university emails are permitted

### Lab commands fail
→ Verify Labtainer is installed and lab template folders exist in ./labs/

### Database errors after updates
→ Run `python seed_data.py` to recreate database with new schema
