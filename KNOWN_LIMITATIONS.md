# Known Limitations and Production Requirements

## Current Implementation Status

### ✅ What's Been Built and Works

1. **Authentication System**
   - Replit OAuth integration with Google, GitHub, email/password
   - .edu email verification enforced
   - Session management with Flask-Login
   - Protected routes requiring authentication

2. **Database Schema**
   - Complete SQLAlchemy models (Users, Courses, Labs, Enrollments, UserLabs)
   - Proper foreign key relationships
   - Unique constraints preventing duplicate enrollments
   - SQLite database with migration capability to PostgreSQL

3. **User Interface**
   - Landing page with login
   - Dashboard showing enrolled courses and labs
   - Course browsing and enrollment
   - Web terminal with xterm.js
   - Responsive design

4. **Course Management**
   - Sample data initialization
   - Course browsing and enrollment workflow
   - Lab assignment on enrollment
   - Folder naming: `{user_id}-{template_folder}`

5. **Basic Terminal Functionality**
   - WebSocket-based terminal
   - PTY (pseudo-terminal) management
   - Terminal resizing support
   - Multiple concurrent sessions

6. **Labtainer Integration Framework**
   - Integration module with documented functions
   - Command wrappers for rebuild/start/stop
   - HTTP endpoints for lab operations
   - UI buttons for lab commands

## ⚠️ Critical Limitations Requiring Production Fixes

### 1. Lab Provisioning Transaction Safety

**Issue:** Lab creation is not atomic and lacks proper error handling.

**Problems:**
- No validation that template folder exists before database commit
- Partial failures can create orphaned database records
- No filesystem cleanup if database operations fail
- Multiple labs for same user/course could bypass error handling

**Production Fix Required:**
```python
def enroll_course_safe(course_id, user_id):
    # 1. Verify template exists
    # 2. Begin transaction
    # 3. Clone folder
    # 4. Create DB records
    # 5. Commit transaction
    # 6. On any error: rollback DB AND remove filesystem artifacts
```

### 2. WebSocket Authentication Security

**Issue:** Socket authentication is incomplete and vulnerable.

**Problems:**
- Flask-Login context may not load in Socket.IO background threads
- No signed tokens for socket connections
- Lab ownership not validated on every socket event
- Potential for session hijacking or unauthorized lab access

**Production Fix Required:**
```python
@socketio.on('connect')
def handle_connect():
    # Verify current_user is actually loaded
    # Issue signed token tied to session
    # Store token in clients dict for validation
    
@socketio.on('init_terminal')
def handle_terminal_init(data):
    # Validate signed token
    # Re-verify lab ownership on EVERY event
    # Use thread-safe session access
```

### 3. Terminal Doesn't Actually Enter Labtainer Environment

**Issue:** Terminal launches generic bash shell, not Labtainer instance.

**Problems:**
- Sets LAB_FOLDER environment variable but doesn't cd into it
- Doesn't invoke `labtainer start` to actually launch the lab
- User gets host shell, not containerized lab environment
- No integration with Docker containers (which Labtainer uses)

**Production Fix Required:**
```python
if user_lab:
    # 1. Start Labtainer if not running
    success = start_lab(user_lab.folder_name)
    
    # 2. Get container ID for the lab
    container_id = get_lab_container_id(user_lab.folder_name)
    
    # 3. Execute shell INSIDE the container
    os.execvp('docker', ['docker', 'exec', '-it', container_id, '/bin/bash'])
```

### 4. Path Traversal and Command Injection Vulnerabilities

**Issue:** User-controlled input not sanitized in critical operations.

**Problems:**
- `folder_name` is user-controlled and passed to subprocess commands
- No validation that folder_name matches expected pattern
- Potential for path traversal: `../../etc/passwd`
- Command injection possible in lab operations

**Production Fix Required:**
```python
import re

def validate_folder_name(folder_name, user_id):
    # Only allow: userid-template format
    pattern = f"^{re.escape(user_id)}-[a-z0-9-]+$"
    if not re.match(pattern, folder_name):
        raise ValueError("Invalid folder name")
    
    # Verify folder is within labs directory
    abs_path = os.path.realpath(os.path.join(LABS_PATH, folder_name))
    if not abs_path.startswith(os.path.realpath(LABS_PATH)):
        raise ValueError("Path traversal attempt detected")
    
    return folder_name

# Use in all Labtainer operations
@app.route('/lab/<int:lab_id>/start', methods=['POST'])
def start_user_lab(lab_id):
    user_lab = UserLab.query.filter_by(user_id=current_user.id, lab_id=lab_id).first_or_404()
    
    # VALIDATE before using
    safe_folder = validate_folder_name(user_lab.folder_name, current_user.id)
    
    success, output = start_lab(safe_folder)
    ...
```

### 5. Lab Status Not Synchronized with Reality

**Issue:** Status updates don't verify actual state changes.

**Problems:**
- Status set to ACTIVE/STOPPED without checking if command succeeded
- No verification that Labtainer is actually running
- Race conditions between status changes
- Users can't trust status field

**Production Fix Required:**
```python
@app.route('/lab/<int:lab_id>/start', methods=['POST'])
def start_user_lab(lab_id):
    user_lab = UserLab.query.filter_by(user_id=current_user.id, lab_id=lab_id).first_or_404()
    
    success, output = start_lab(user_lab.folder_name)
    
    if success:
        # VERIFY it's actually running before updating
        is_running, status_msg = get_lab_status(user_lab.folder_name)
        if is_running:
            user_lab.status = 'ACTIVE'
            db.session.commit()
            return jsonify({'status': 'success', 'output': output})
        else:
            return jsonify({'status': 'error', 'message': 'Lab started but not running'}), 500
    else:
        return jsonify({'status': 'error', 'message': output}), 500
```

## Additional Production Requirements

### Infrastructure

1. **Labtainer Installation**
   - System must have Labtainer installed at expected path
   - Lab template folders must exist in correct directory structure
   - Docker runtime must be available

2. **File System Permissions**
   - Application needs permissions to clone lab folders
   - Need isolation between user lab instances
   - Disk space quotas to prevent abuse

3. **Database Migration**
   - Move from SQLite to PostgreSQL for concurrent access
   - Add connection pooling
   - Implement proper database backups

4. **Environment Configuration**
   - Set `SESSION_SECRET` environment variable
   - Configure `LABTAINER_PATH` correctly
   - Set up proper logging and monitoring

### Security Hardening

1. **Input Validation**
   - Sanitize all user inputs
   - Validate file paths against whitelist
   - Use parameterized queries (already using SQLAlchemy)
   - Implement rate limiting

2. **Resource Limits**
   - Limit number of labs per user
   - Set CPU/memory limits for lab containers
   - Implement session timeouts
   - Add disk quota enforcement

3. **Audit Logging**
   - Log all lab operations
   - Track failed authentication attempts
   - Monitor for suspicious activity
   - Implement log rotation

### Scalability

1. **Asynchronous Operations**
   - Move lab provisioning to background task queue (Celery)
   - Send email/notifications on completion
   - Handle long-running operations gracefully

2. **Load Balancing**
   - Multiple application servers
   - Shared session storage (Redis)
   - Container orchestration for lab instances

3. **Caching**
   - Cache course/lab catalog
   - Use CDN for static assets
   - Implement query result caching

## Testing Requirements

### Unit Tests Needed
- Authentication flow with .edu validation
- Lab provisioning transaction rollback
- Folder name validation and sanitization
- Database model relationships
- Labtainer command error handling

### Integration Tests Needed
- End-to-end enrollment workflow
- Terminal connection and lab binding
- Labtainer command execution
- WebSocket authentication
- Session management

### Security Tests Needed
- Path traversal attempts
- Command injection attempts
- Session hijacking attempts
- Cross-site request forgery
- SQL injection (though SQLAlchemy protects)

## Migration Path from Current Implementation

### Phase 1: Critical Security (1-2 weeks)
1. Implement input validation and sanitization
2. Harden WebSocket authentication
3. Add path traversal protection
4. Fix transaction safety in lab provisioning

### Phase 2: Labtainer Integration (2-3 weeks)
1. Install and configure Labtainer on server
2. Modify terminal to launch inside containers
3. Implement proper lab lifecycle management
4. Add status synchronization with actual state

### Phase 3: Production Hardening (2-3 weeks)
1. Migrate to PostgreSQL
2. Add comprehensive error handling
3. Implement audit logging
4. Set up monitoring and alerts

### Phase 4: Scale and Polish (1-2 weeks)
1. Add background task queue
2. Implement caching layer
3. Add email notifications
4. Create admin dashboard

## Conclusion

This implementation provides a **solid foundation** with:
- Working authentication with .edu verification
- Complete database schema and relationships
- Functional user interface
- Terminal infrastructure in place
- Labtainer integration framework

However, it is **NOT production-ready** due to:
- Security vulnerabilities (path traversal, command injection)
- Incomplete lab provisioning (no actual Labtainer integration)
- WebSocket authentication weaknesses
- Lack of transaction safety

**Recommendation:** Use this as a development/testing environment to validate the user workflow and UI/UX. Do NOT deploy to production or give access to untrusted users until the security issues are addressed and actual Labtainer integration is completed.
