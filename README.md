# Labtainer Backend System

A Python Flask backend system that integrates with a Labtainer server for managing cybersecurity lab exercises. This system provides Google OAuth authentication (restricted to .edu emails), REST APIs for lab management, and WebSocket support for real-time terminal interaction.

## Features

- **Google OAuth Authentication**: Login with .edu email addresses only
- **JWT-based Authorization**: Secure API access with JSON Web Tokens
- **PostgreSQL Database**: Store users, courses, labs, and progress
- **REST APIs**: Complete CRUD operations for lab management
- **WebSocket Support**: Real-time terminal interaction with Labtainer server
- **Lab Template Cloning**: Automatic lab environment setup with unique naming
- **Status Tracking**: Monitor lab progress (ENROLLED, STARTED, COMPLETED)

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Google OAuth credentials (.edu email domain)
- Labtainer server with lab templates in `/labs` directory

## Environment Variables

Required environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for JWT and sessions
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret
- `LAB_BASE_PATH`: Path to Labtainer labs folder (default: `/labs`)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file

3. Initialize the database:
```bash
python seed_data.py
```

4. Create lab template folders:
```bash
mkdir -p /labs/network-analysis
mkdir -p /labs/buffer-overflow
mkdir -p /labs/sql-injection
```

## Running the Application

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000`

## API Endpoints

### Authentication

#### `GET /auth/login`
Initiate Google OAuth login flow

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/..."
}
```

#### `GET /auth/login/callback`
OAuth callback endpoint (handled automatically by Google)

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "student@university.edu",
    "name": "John Doe",
    "google_id": "123456789"
  }
}
```

### Dashboard

#### `GET /dashboard`
Get user's enrolled courses and labs with status

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "student@university.edu",
    "name": "John Doe"
  },
  "courses": [
    {
      "id": 1,
      "name": "Introduction to Cybersecurity",
      "description": "Learn the fundamentals...",
      "labs": [
        {
          "id": 1,
          "lab_name": "1-Network Analysis Lab",
          "status": "ENROLLED",
          "template_name": "Network Analysis Lab"
        }
      ]
    }
  ]
}
```

### Lab Management

#### `POST /register-lab`
Register for a course and get a random lab assigned

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Request Body:**
```json
{
  "course_id": 1
}
```

**Response:**
```json
{
  "message": "Lab registered successfully",
  "lab": {
    "id": 1,
    "lab_name": "1-Network Analysis Lab",
    "template_name": "Network Analysis Lab",
    "folder_path": "/labs/1-network-analysis",
    "status": "ENROLLED"
  }
}
```

#### `GET /labs`
Get all labs for the authenticated user

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

#### `GET /courses`
Get all available courses

## WebSocket Events

### Client → Server Events

#### `connect`
Connect to WebSocket server

#### `authenticate`
Authenticate WebSocket connection

**Payload:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### `start_lab`
Start a lab session (runs rebuild command)

**Payload:**
```json
{
  "lab_id": 1
}
```

#### `execute_command`
Execute a Labtainer command

**Payload:**
```json
{
  "lab_id": 1,
  "command": "labtainer start"
}
```

**Allowed commands:**
- `labtainer start <lab_name>`
- `labtainer stop <lab_name>`
- `rebuild <lab_name>`

### Server → Client Events

#### `connection_response`
Connection established confirmation

#### `authenticated`
Authentication successful

#### `output`
Command output/terminal output

**Payload:**
```json
{
  "message": "Command output text..."
}
```

#### `lab_status`
Lab status changed

**Payload:**
```json
{
  "lab_id": 1,
  "status": "STARTED"
}
```

#### `error`
Error message

**Payload:**
```json
{
  "message": "Error description"
}
```

## Database Schema

### Users
- `id`: Primary key
- `email`: Email address (.edu domain)
- `name`: Full name
- `google_id`: Google OAuth unique ID

### Courses
- `id`: Primary key
- `name`: Course name
- `description`: Course description

### Labs
- `id`: Primary key
- `user_id`: Foreign key to Users
- `course_id`: Foreign key to Courses
- `lab_name`: Unique lab name (format: `<user_id>-<template_name>`)
- `template_name`: Original template name
- `folder_path`: Path to lab folder on Labtainer server
- `status`: ENROLLED, STARTED, or COMPLETED

### LabTemplates
- `id`: Primary key
- `name`: Template display name
- `folder_name`: Folder name on server
- `description`: Template description

## Labtainer Commands

The system executes these commands on the Labtainer server:

- `rebuild <userid>-<lab_folder_name>`: Rebuild lab environment
- `labtainer start <userid>-<lab_folder_name>`: Start lab session
- `labtainer stop <userid>-<lab_folder_name>`: Stop lab session

## Security Features

- **.edu email validation**: Only university emails allowed
- **JWT authentication**: Secure token-based API access
- **Command whitelist**: Only Labtainer commands allowed
- **User isolation**: Each user gets unique lab folders
- **CORS protection**: Configurable CORS policy

## Development

### Running in Debug Mode

```bash
python app.py
```

### Resetting Database

```bash
python seed_data.py
```

This will drop all tables and recreate them with seed data.

## Google OAuth Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add authorized redirect URI:
   - `https://<your-domain>/auth/login/callback`
4. Copy Client ID and Client Secret to environment variables

## Troubleshooting

### "Google OAuth not configured" error
- Ensure `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are set

### "Only .edu email addresses are allowed"
- The system only accepts email addresses ending in `.edu`

### Lab command execution fails
- Verify Labtainer server is accessible
- Check `LAB_BASE_PATH` is correct
- Ensure lab template folders exist in `/labs`

### WebSocket connection issues
- Verify CORS settings allow your frontend origin
- Check that JWT token is valid and not expired

## License

MIT License
