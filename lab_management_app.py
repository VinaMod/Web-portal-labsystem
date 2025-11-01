from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from datetime import datetime, timedelta
import subprocess
import os
import json
import shutil
import uuid
import re
from pathlib import Path
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///lab_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth Config
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*")
oauth = OAuth(app)

# Lab Environment Config
LAB_TEMPLATES_PATH = os.getenv('LAB_TEMPLATES_PATH', './lab-templates')
STUDENT_LABS_PATH = os.getenv('STUDENT_LABS_PATH', './student-labs')
ALLOWED_COMMANDS = json.loads(os.getenv('ALLOWED_COMMANDS', '["ls", "dir", "cd", "cat", "type", "grep", "find", "findstr", "pwd", "echo", "whoami", "python", "python3", "gcc", "make", "javac", "java", "node", "npm", "git"]'))

# Ensure directories exist
os.makedirs(LAB_TEMPLATES_PATH, exist_ok=True)
os.makedirs(STUDENT_LABS_PATH, exist_ok=True)

# Google OAuth Setup
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    avatar_url = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='user', lazy=True, cascade='all, delete-orphan')
    lab_sessions = db.relationship('LabSession', backref='user', lazy=True, cascade='all, delete-orphan')

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    semester = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    max_students = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    labs = db.relationship('Lab', backref='course', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')

class Lab(db.Model):
    __tablename__ = 'labs'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    template_folder = db.Column(db.String(255), nullable=False)
    accessible_resources = db.Column(db.Text)  # JSON array
    build_command = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    deadline = db.Column(db.DateTime)
    max_score = db.Column(db.Integer, default=100)
    estimated_duration = db.Column(db.Integer)  # minutes
    difficulty = db.Column(db.String(20), default='medium')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lab_sessions = db.relationship('LabSession', backref='lab', lazy=True, cascade='all, delete-orphan')
    
    @property
    def accessible_resources_list(self):
        """Return accessible resources as a list"""
        if self.accessible_resources:
            return json.loads(self.accessible_resources)
        return []

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id'),)

class LabSession(db.Model):
    __tablename__ = 'lab_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
    student_folder = db.Column(db.String(255))
    status = db.Column(db.String(20), default='not_started')
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    last_accessed = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    submission_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'lab_id'),)
    
    # Relationships
    terminal_sessions = db.relationship('TerminalSession', backref='lab_session', lazy=True, cascade='all, delete-orphan')

class TerminalSession(db.Model):
    __tablename__ = 'terminal_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lab_session_id = db.Column(db.Integer, db.ForeignKey('lab_sessions.id'), nullable=False)
    current_directory = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    command_count = db.Column(db.Integer, default=0)
    
    # Relationships
    command_logs = db.relationship('CommandLog', backref='terminal_session', lazy=True, cascade='all, delete-orphan')

class CommandLog(db.Model):
    __tablename__ = 'command_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    terminal_session_id = db.Column(db.Integer, db.ForeignKey('terminal_sessions.id'), nullable=False)
    command = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text)
    exit_code = db.Column(db.Integer)
    is_allowed = db.Column(db.Boolean)
    blocked_reason = db.Column(db.Text)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper Functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_edu_email(email):
    """Check if email is from an educational institution"""
    pattern = os.getenv('ALLOWED_EMAIL_REGEX', r'^.+@.+\.edu(\..+)?$')
    return bool(re.match(pattern, email, re.IGNORECASE))

def validate_command_access(command, accessible_resources, current_dir):
    """
    Validate if a command is allowed based on accessible resources
    Returns (is_allowed, reason)
    """
    import shlex
    if not accessible_resources:
        return True, "No limit"
    
    # Split command into parts, handling quotes properly
    try:
        parts = shlex.split(command.strip())
    except ValueError as e:
        # If shlex fails (e.g., unclosed quotes), fall back to simple split
        parts = command.strip().split()
    
    if not parts:
        return False, "Empty command"
    
    cmd = parts[0]
    
    # Check if command is in allowed list
    if cmd not in ALLOWED_COMMANDS:
        return False, f"Command '{cmd}' is not allowed"
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\.',  # Path traversal
        r'/etc/',  # System files
        r'/usr/',  # System binaries
        r'/var/',  # System variables
        r'sudo',   # Privilege escalation
        r'rm\s+-rf',  # Dangerous deletions
        r'chmod\s+777',  # Permission changes
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains dangerous pattern: {pattern}"
    
    # Validate file/directory access for commands that take paths
    if cmd in ['cd', 'cat', 'grep', 'find', 'type'] and len(parts) > 1:
        # Check all path arguments (skip flags starting with -)
        for arg in parts[1:]:
            if arg.startswith('-'):
                continue
                
            target_path = arg
            
            # Remove quotes if present
            target_path = target_path.strip('"').strip("'")
            
            # Skip if it's a flag or option
            if target_path.startswith('-'):
                continue
            
            # Convert relative path to absolute
            if not os.path.isabs(target_path):
                target_path = os.path.join(current_dir, target_path)
            
            # Normalize path to prevent traversal
            target_path = os.path.normpath(target_path)
            
            # Check if path is within accessible resources
            is_accessible = False
            for resource in accessible_resources:
                resource_abs = os.path.join(current_dir, resource) if not os.path.isabs(resource) else resource
                resource_abs = os.path.normpath(resource_abs)
                
                if target_path.startswith(resource_abs):
                    is_accessible = True
                    break
            
            if not is_accessible:
                return False, f"Access denied to path: {target_path}"
    
    return True, "Command allowed"

# Routes
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        email = user_info['email']
        
        # # Validate .edu email
        if not is_edu_email(email):
            flash('Only .edu email addresses are allowed to access this system.', 'error')
            return redirect(url_for('index'))
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            user = User(
                email=email,
                full_name=user_info.get('name', ''),
                google_id=user_info['sub'],
                avatar_url=user_info.get('picture', '')
            )
            db.session.add(user)
        else:
            # Update user info
            user.full_name = user_info.get('name', user.full_name)
            user.avatar_url = user_info.get('picture', user.avatar_url)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Store user in session
        session['user'] = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'avatar_url': user.avatar_url,
            'role': user.role
        }
        
        return redirect(url_for('dashboard'))
    
    flash('Authentication failed. Please try again.', 'error')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user']['id']
    
    # Get user's enrolled courses with labs
    enrollments = db.session.query(Enrollment, Course).join(Course).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == 'active'
    ).all()
    
    enrolled_courses = []
    for enrollment, course in enrollments:
        # Get labs for this course
        labs = Lab.query.filter_by(course_id=course.id, is_active=True).order_by(Lab.order_index).all()
        
        course_labs = []
        for lab in labs:
            # Get lab session for this user
            lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab.id).first()
            
            lab_info = {
                'id': lab.id,
                'name': lab.name,
                'description': lab.description,
                'deadline': lab.deadline,
                'difficulty': lab.difficulty,
                'estimated_duration': lab.estimated_duration,
                'max_score': lab.max_score,
                'status': lab_session.status if lab_session else 'not_started',
                'score': lab_session.score if lab_session else None,
                'started_at': lab_session.started_at if lab_session else None,
                'completed_at': lab_session.completed_at if lab_session else None
            }
            course_labs.append(lab_info)
        
        enrolled_courses.append({
            'course': course,
            'labs': course_labs,
            'enrollment': enrollment
        })
    
    return render_template('dashboard.html', 
                         enrolled_courses=enrolled_courses,
                         current_time=datetime.utcnow())

@app.route('/api/courses')
@login_required
def get_available_courses():
    """Get all available courses for enrollment"""
    user_id = session['user']['id']
    
    # Get courses user is not enrolled in
    enrolled_course_ids = db.session.query(Enrollment.course_id).filter_by(
        user_id=user_id, status='active'
    ).subquery()
    
    available_courses = Course.query.filter(
        Course.is_active == True,
        ~Course.id.in_(enrolled_course_ids)
    ).all()
    
    courses_data = []
    for course in available_courses:
        courses_data.append({
            'id': course.id,
            'code': course.code,
            'name': course.name,
            'description': course.description,
            'semester': course.semester,
            'lab_count': len(course.labs)
        })
    
    return jsonify(courses_data)

@app.route('/api/enroll', methods=['POST'])
@login_required
def enroll_course():
    """Enroll user in a course"""
    user_id = session['user']['id']
    course_id = request.json.get('course_id')
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    # Check if course exists and is active
    course = Course.query.filter_by(id=course_id, is_active=True).first()
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if user is already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        user_id=user_id, course_id=course_id
    ).first()
    
    if existing_enrollment:
        if existing_enrollment.status == 'active':
            return jsonify({'error': 'Already enrolled in this course'}), 400
        else:
            # Reactivate enrollment
            existing_enrollment.status = 'active'
            existing_enrollment.enrolled_at = datetime.utcnow()
    else:
        # Create new enrollment
        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        db.session.add(enrollment)
    
    try:
        db.session.commit()
        
        # Clone lab folders for all labs in this course
        labs = Lab.query.filter_by(course_id=course_id, is_active=True).all()
        for lab in labs:
            clone_lab_folder(user_id, lab.id)
        
        return jsonify({'message': 'Successfully enrolled in course', 'course': course.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to enroll in course'}), 500

def clone_lab_folder(user_id, lab_id):
    """Clone lab template folder for a specific user"""
    lab = Lab.query.get(lab_id)
    user = User.query.get(user_id)
    
    if not lab or not user:
        return False
    
    try:
        template_path = os.path.join(LAB_TEMPLATES_PATH, lab.template_folder)
        print("========= template path ", template_path);
        # Create unique folder name for student
        student_folder_name = f"{user.email.split('@')[0]}-{lab.template_folder}"
        student_folder_path = os.path.join(STUDENT_LABS_PATH, student_folder_name)
        print("=========== student path ", student_folder_path)
        # Clone the template folder
        if os.path.exists(template_path) and not os.path.exists(student_folder_path):
            shutil.copytree(template_path, student_folder_path)
            
            # Create or update lab session
            lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
            if not lab_session:
                lab_session = LabSession(
                    user_id=user_id,
                    lab_id=lab_id,
                    student_folder=student_folder_path
                )
                db.session.add(lab_session)
            else:
                lab_session.student_folder = student_folder_path
            
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error cloning lab folder: {e}")
        return False
    
    return False

@app.route('/api/start_lab/<int:lab_id>', methods=['POST'])
@login_required
def start_lab(lab_id):
    """Start a lab session"""
    user_id = session['user']['id']
    
    # Get lab and verify user enrollment
    lab = Lab.query.get(lab_id)
    if not lab:
        return jsonify({'error': 'Lab not found'}), 404
    
    enrollment = Enrollment.query.filter_by(
        user_id=user_id, course_id=lab.course_id, status='active'
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    # Get or create lab session
    lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
    if not lab_session:
        # Clone lab folder if not exists
        if not clone_lab_folder(user_id, lab_id):
            return jsonify({'error': 'Failed to setup lab environment'}), 500
        lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
    
    # Update session status
    if lab_session.status == 'not_started':
        lab_session.status = 'in_progress'
        lab_session.started_at = datetime.utcnow()
    
    lab_session.last_accessed = datetime.utcnow()
    
    try:
        db.session.commit()
        
        # Execute build command if specified
        if lab.build_command and lab_session.student_folder:
            execute_build_command(lab.build_command, lab_session.student_folder)
        
        return jsonify({
            'message': 'Lab started successfully',
            'lab_session_id': lab_session.id,
            'redirect_url': f'/lab/{lab_session.id}/terminal'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to start lab'}), 500

def execute_build_command(build_command, working_directory):
    """Execute build command in lab directory"""
    try:
        result = subprocess.run(
            build_command,
            shell=True,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        print(f"Build command executed. Exit code: {result.returncode}")
        if result.stdout:
            print(f"Build output: {result.stdout}")
        if result.stderr:
            print(f"Build errors: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Build command timed out")
        return False
    except Exception as e:
        print(f"Error executing build command: {e}")
        return False

@app.route('/lab/<int:lab_id>/terminal')
@login_required
def lab_terminal(lab_id):
    """Display lab terminal interface"""
    user_id = session['user']['id']
    
    # Get lab session for current user and lab
    lab_session = LabSession.query.filter_by(lab_id=lab_id, user_id=user_id).first()
    if not lab_session:
        flash('Lab session not found. Please start the lab first.', 'error')
        return redirect(url_for('dashboard'))
    
    # Update last accessed
    lab_session.last_accessed = datetime.utcnow()
    db.session.commit()
    
    return render_template('lab_terminal.html', lab_session=lab_session)

# WebSocket Terminal Handlers
active_terminals = {}

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    print(f"Client connected: {session_id}")

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    print(f"Client disconnected: {session_id}")
    
    # Clean up terminal session
    if session_id in active_terminals:
        terminal_info = active_terminals[session_id]
        try:
            terminal_session = TerminalSession.query.get(terminal_info['terminal_session_id'])
            if terminal_session:
                terminal_session.is_active = False
                db.session.commit()
        except Exception as e:
            print(f"Warning: Could not update terminal session on disconnect: {e}")
            db.session.rollback()
        finally:
            del active_terminals[session_id]

@socketio.on('start_terminal')
def handle_start_terminal(data):
    session_id = request.sid
    lab_session_id = data.get('lab_session_id')
    
    if 'user' not in session:
        emit('terminal_error', {'error': 'Not authenticated'})
        return
    
    user_id = session['user']['id']
    
    # Verify lab session
    lab_session = LabSession.query.filter_by(id=lab_session_id, user_id=user_id).first()
    if not lab_session:
        emit('terminal_error', {'error': 'Lab session not found'})
        return
    
    # Create terminal session
    terminal_session_id = str(uuid.uuid4())
    print("===================== student_folder", lab_session.student_folder)
    terminal_session = TerminalSession(
        session_id=terminal_session_id,
        user_id=user_id,
        lab_session_id=lab_session_id,
        #current_directory=lab_session.student_folder or '/tmp'
        current_directory= '/home/student/labtainer/trunk/scripts/labtainer-student'
    )
    
    db.session.add(terminal_session)
    db.session.commit()
    
    # Store in active terminals with IDs instead of objects
    active_terminals[session_id] = {
        'terminal_session_id': terminal_session.id,
        'lab_session_id': lab_session.id,
        'command_buffer': ''
    }
    
    # Send welcome message
    welcome_msg = f"""
🧪 Lab Terminal - {lab_session.lab.name}
📁 Working Directory: {lab_session.student_folder}
⚠️  Security: Commands are validated for safety
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{get_prompt(lab_session.student_folder)}"""
    
    emit('terminal_output', {'data': welcome_msg})
    emit('terminal_ready', {'status': 'ready'})

def get_prompt(current_dir):
    """Get terminal prompt"""
    dir_name = os.path.basename(current_dir) if current_dir else 'unknown'
    return f"lab:{dir_name}$ "

@socketio.on('terminal_input')
def handle_terminal_input(data):
    session_id = request.sid
    input_data = data.get('data', '')
    
    if session_id not in active_terminals:
        emit('terminal_error', {'error': 'No active terminal session'})
        return
    
    terminal_info = active_terminals[session_id]
    
    # Get fresh database objects using IDs
    terminal_session = TerminalSession.query.get(terminal_info['terminal_session_id'])
    lab_session = LabSession.query.get(terminal_info['lab_session_id'])
    
    if not terminal_session or not lab_session:
        emit('terminal_error', {'error': 'Terminal session expired'})
        return
    
    # Handle input character by character
    if input_data == '\r' or input_data == '\n':
        # Execute command
        command = terminal_info['command_buffer'].strip()
        if command:
            execute_secure_command(session_id, command, terminal_session, lab_session)
        else:
            emit('terminal_output', {'data': f'\r\n{get_prompt(terminal_session.current_directory)}'})
        terminal_info['command_buffer'] = ''
        
    elif input_data == '\x7f':  # Backspace
        if terminal_info['command_buffer']:
            terminal_info['command_buffer'] = terminal_info['command_buffer'][:-1]
            emit('terminal_output', {'data': '\b \b'})
            
    elif input_data == '\x03':  # Ctrl+C
        terminal_info['command_buffer'] = ''
        emit('terminal_output', {'data': f'^C\r\n{get_prompt(terminal_session.current_directory)}'})
        
    elif ord(input_data) >= 32:  # Printable characters
        terminal_info['command_buffer'] += input_data
        emit('terminal_output', {'data': input_data})
    
    # Update last activity
    try:
        terminal_session.last_activity = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        print(f"Warning: Could not update last activity: {e}")
        db.session.rollback()

def execute_secure_command(socket_session_id, command, terminal_session, lab_session):
    """Execute command with security validation"""
    
    # Get accessible resources for this lab
    accessible_resources = lab_session.lab.accessible_resources_list
    current_dir = terminal_session.current_directory
    
    # Validate command
    is_allowed, reason = validate_command_access(command, accessible_resources, current_dir)
    
    # Log command
    command_log = CommandLog(
        terminal_session_id=terminal_session.id,
        command=command,
        is_allowed=is_allowed,
        blocked_reason=reason if not is_allowed else None
    )
    
    if not is_allowed:
        # Command blocked
        error_msg = f"\r\n🚫 Command blocked: {reason}\r\n"
        emit('terminal_output', {'data': error_msg}, room=socket_session_id)
        command_log.output = error_msg
        command_log.exit_code = 1
    else:
        # Execute command
        try:
            # Handle special commands
            if command.lower() in ['clear', 'cls']:
                emit('terminal_clear', {}, room=socket_session_id)
                emit('terminal_output', {'data': get_prompt(current_dir)}, room=socket_session_id)
                command_log.output = "Terminal cleared"
                command_log.exit_code = 0
                
            elif command.lower().startswith('cd '):
                new_dir = handle_cd_command(command, current_dir, accessible_resources)
                if new_dir != current_dir:
                    terminal_session.current_directory = new_dir
                    output = f"\r\n{get_prompt(new_dir)}"
                else:
                    output = f"\r\ncd: directory not accessible or not found\r\n{get_prompt(current_dir)}"
                emit('terminal_output', {'data': output}, room=socket_session_id)
                command_log.output = output
                command_log.exit_code = 0 if new_dir != current_dir else 1
                
            else:
                # Handle command aliases for cross-platform compatibility
                original_command = command
                if command.lower().startswith('ls'):
                    # Convert ls to dir on Windows
                    import platform
                    if platform.system() == 'Windows':
                        if command.lower() == 'ls':
                            command = 'dir'
                        elif command.lower().startswith('ls '):
                            command = command.replace('ls ', 'dir ', 1)
                
                elif command.lower().startswith('cat ') and platform.system() == 'Windows':
                    # Convert cat to type on Windows
                    command = command.replace('cat ', 'type ', 1)
                
                # Execute system command
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=current_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output = result.stdout
                if result.stderr:
                    output += f"\n{result.stderr}"
                
                if not output:
                    output = ""
                
                full_output = f"\r\n{output}\r\n{get_prompt(current_dir)}"
                emit('terminal_output', {'data': full_output}, room=socket_session_id)
                
                command_log.output = output
                command_log.exit_code = result.returncode
                
        except subprocess.TimeoutExpired:
            error_msg = f"\r\n⏰ Command timed out\r\n{get_prompt(current_dir)}"
            emit('terminal_output', {'data': error_msg}, room=socket_session_id)
            command_log.output = "Command timed out"
            command_log.exit_code = 124
            
        except Exception as e:
            error_msg = f"\r\n❌ Error: {str(e)}\r\n{get_prompt(current_dir)}"
            emit('terminal_output', {'data': error_msg}, room=socket_session_id)
            command_log.output = f"Error: {str(e)}"
            command_log.exit_code = 1
    
    # Save command log
    try:
        db.session.add(command_log)
        
        # Update terminal session stats
        terminal_session.command_count += 1
        db.session.commit()
    except Exception as e:
        print(f"Warning: Could not save command log: {e}")
        db.session.rollback()

def handle_cd_command(command, current_dir, accessible_resources):
    """Handle cd command with path validation"""
    parts = command.strip().split()
    if len(parts) < 2:
        return current_dir
    
    target_path = parts[1]
    
    # Convert relative path to absolute
    if not os.path.isabs(target_path):
        new_path = os.path.join(current_dir, target_path)
    else:
        new_path = target_path
    
    # Normalize path
    new_path = os.path.normpath(new_path)
    
    # Check if path exists and is accessible
    if not os.path.exists(new_path) or not os.path.isdir(new_path):
        return current_dir
    
    # Check accessibility
    for resource in accessible_resources:
        resource_abs = os.path.join(current_dir, resource) if not os.path.isabs(resource) else resource
        resource_abs = os.path.normpath(resource_abs)
        
        if new_path.startswith(resource_abs):
            return new_path
    
    return current_dir

# Helper functions for sample data
def create_sample_data():
    """Create sample courses and labs for testing"""
    if Course.query.count() > 0:
        return  # Sample data already exists
    
    try:
        # Create sample courses
        courses_data = [
            {
                'code': 'SEC301',
                'name': 'Web Application Security',
                'description': 'Learn about common web vulnerabilities and how to exploit/prevent them',
                'semester': 'Fall2025'
            },
            {
                'code': 'CS101', 
                'name': 'Introduction to Computer Science',
                'description': 'Basic programming and computer science concepts',
                'semester': 'Fall2025'
            }
        ]
        
        for course_data in courses_data:
            course = Course(**course_data)
            db.session.add(course)
        
        db.session.commit()
        
        # Create sample labs
        sec_course = Course.query.filter_by(code='SEC301').first()
        cs_course = Course.query.filter_by(code='CS101').first()
        
        labs_data = [
            {
                'course_id': sec_course.id,
                'name': 'SQL Injection Lab',
                'description': 'Learn to identify and exploit SQL injection vulnerabilities',
                'template_folder': 'sql-injection-template',
                'accessible_resources': json.dumps(['./src', './database', './logs', './scripts']),
                'build_command': 'docker-compose up -d && sleep 5',
                'deadline': datetime.utcnow() + timedelta(days=30),
                'difficulty': 'medium',
                'order_index': 1
            },
            {
                'course_id': sec_course.id,
                'name': 'XSS Prevention Lab',
                'description': 'Understanding Cross-Site Scripting attacks and defenses',
                'template_folder': 'xss-template',
                'accessible_resources': json.dumps(['./webapp', './scripts', './public']),
                'build_command': 'npm install && npm start',
                'deadline': datetime.utcnow() + timedelta(days=35),
                'difficulty': 'hard',
                'order_index': 2
            },
            {
                'course_id': cs_course.id,
                'name': 'Basic Programming Lab',
                'description': 'First programming assignment using C',
                'template_folder': 'basic-programming-template',
                'accessible_resources': json.dumps(['./src', './tests', './bin']),
                'build_command': 'gcc -o main src/main.c',
                'deadline': datetime.utcnow() + timedelta(days=14),
                'difficulty': 'easy',
                'order_index': 1
            }
        ]
        
        for lab_data in labs_data:
            lab = Lab(**lab_data)
            db.session.add(lab)
        
        db.session.commit()
        print("✅ Sample data created successfully!")
        
        # Create sample template directories
        create_sample_templates()
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.session.rollback()

def create_sample_templates():
    """Create sample lab template directories"""
    templates = [
        {
            'name': 'sql-injection-template',
            'files': {
                'README.md': '# SQL Injection Lab\n\nLearn about SQL injection vulnerabilities.\n',
                'src/app.py': '# Flask app with SQL injection vulnerability\nprint("Hello World")\n',
                'database/init.sql': '-- Database initialization\nCREATE TABLE users (id INT, username TEXT, password TEXT);\n'
            }
        },
        {
            'name': 'xss-template', 
            'files': {
                'README.md': '# XSS Prevention Lab\n\nLearn about Cross-Site Scripting.\n',
                'webapp/index.html': '<!DOCTYPE html><html><body><h1>XSS Lab</h1></body></html>\n',
                'scripts/exploit.js': '// XSS exploitation script\nconsole.log("XSS Lab");\n'
            }
        },
        {
            'name': 'basic-programming-template',
            'files': {
                'README.md': '# Basic Programming Lab\n\nWrite your first C program.\n',
                'src/main.c': '#include <stdio.h>\n\nint main() {\n    printf("Hello World!\\n");\n    return 0;\n}\n',
                'tests/test.c': '// Test file\n#include <stdio.h>\n'
            }
        }
    ]
    
    for template in templates:
        template_path = os.path.join(LAB_TEMPLATES_PATH, template['name'])
        
        if not os.path.exists(template_path):
            os.makedirs(template_path, exist_ok=True)
            
            for file_path, content in template['files'].items():
                full_file_path = os.path.join(template_path, file_path)
                os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
                
                with open(full_file_path, 'w') as f:
                    f.write(content)
    
    print("✅ Sample lab templates created!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("🚀 Starting Lab Management System...")
    print("📡 Server will be available at: http://localhost:5000")
    print("🔐 Google OAuth configured")
    print("🧪 Lab environment ready")
    print("🔒 Secure terminal with command validation")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    
    print("✅ Sample lab templates created!")