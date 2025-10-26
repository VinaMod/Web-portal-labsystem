# Web Terminal Lab System

## Overview
This is a web-based terminal application that provides an interactive bash shell through a browser interface. It includes a CTF (Capture The Flag) style challenge system with three flag submission fields at the bottom of the terminal.

**Technology Stack:**
- Backend: Python 3.11 with aiohttp and python-socketio
- Frontend: xterm.js terminal emulator with Socket.IO client
- Real-time communication via WebSockets

## Purpose
This application creates a virtualized terminal environment accessible through a web browser, useful for:
- Educational lab systems
- CTF challenges
- Remote shell access in controlled environments
- Teaching command-line skills

## Current State
✅ Fully configured for Replit environment
✅ Dependencies installed
✅ Socket.IO connection using relative URLs (Replit-compatible)
✅ Server configured to run on 0.0.0.0:5000
✅ Workflow configured and running

## Recent Changes (October 26, 2025)
- Migrated from GitHub to Replit
- Fixed Socket.IO client connection to use relative URL instead of hardcoded localhost
- Installed Python 3.11 and all dependencies (aiohttp, python-socketio)
- Configured workflow for automatic server startup
- Added .gitignore for Python projects

## Project Architecture

### Backend (app.py)
- **Framework:** aiohttp async web server
- **WebSocket:** python-socketio for real-time communication
- **PTY Management:** Uses Python's pty module to fork bash shells for each client
- **Key Features:**
  - Creates isolated bash shell per client connection
  - Handles terminal resizing
  - Manages I/O between browser and shell process
  - Automatic cleanup on disconnect

### Frontend
- **Terminal:** xterm.js with fit addon for responsive terminal
- **Layout:** Terminal occupies top portion, flag submission UI at bottom
- **Connection:** Socket.IO client connects automatically on page load
- **Features:**
  - Real-time terminal I/O
  - Responsive terminal sizing
  - Three flag submission inputs with validation
  - Visual feedback (green border) for correct flags

### Static Files
- `templates/index.html` - Main HTML structure
- `static/main.js` - Terminal initialization and Socket.IO logic

## Flag Answers
The correct flags are hardcoded in `static/main.js`:
1. flag-1-collect-data
2. flag-2-upload-file
3. flag-3-read-system-file

## Running the Application
The server runs automatically via the configured workflow on port 5000. Access it through the Replit webview.

## Security Considerations
⚠️ This application gives users direct bash shell access. Only use in controlled, sandboxed environments like Replit.
