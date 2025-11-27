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
import asyncio
import aiohttp
import platform
from concurrent.futures import ThreadPoolExecutor
import pymysql
import traceback
import signal
from dotenv import load_dotenv
import getpass

load_dotenv()  # tự động tìm file .env trong cwd

# Unix/Linux-only imports (not available on Windows)
if platform.system() != 'Windows':
    import pty
    import select
    import struct
    import fcntl
    import termios
else:
    # Windows fallback - these will not be used
    pty = None
    select = None
    struct = None
    fcntl = None
    termios = None

# Install PyMySQL as MySQLdb (for compatibility)
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
print("DATABASE URL: ", os.getenv('DATABASE_URL'))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost:3306/lab_management')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

# Google OAuth Config
print("Google client id: ", os.getenv('GOOGLE_CLIENT_ID'))
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*")
oauth = OAuth(app)

# Lab Environment Config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LAB_TEMPLATES_PATH = os.getenv('LAB_TEMPLATES_PATH', os.path.join(BASE_DIR, 'lab-templates'))
STUDENT_LABS_PATH = os.getenv('STUDENT_LABS_PATH', os.path.join(BASE_DIR, 'student-labs'))
ALLOWED_COMMANDS = json.loads(os.getenv('ALLOWED_COMMANDS', '["ls", "dir", "cd", "cat", "type", "grep", "find", "findstr", "pwd", "echo", "whoami", "python", "python3", "gcc", "make", "javac", "java", "node", "npm", "git"]'))

# PDF Upload Config
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'pdfs')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

STUDENT_NAME_LAB_PARAMETER = "${studentName}"
STUDENT_ID_LAB_PARAMETER = "${studentId}"
LAB_NETWORK_MASK_PARAMETER = "${labNetworkMask}"
LAB_NETWORK_GATEWAY_PARAMETER = "${labNetworkGateway}"
LAB_SUB_NETWORK_IP_PREFIX = "${labSubnetIpPrefix}"

# Ensure directories exist
os.makedirs(LAB_TEMPLATES_PATH, exist_ok=True)
os.makedirs(STUDENT_LABS_PATH, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Log paths for debugging
print(f"Lab Templates Path: {LAB_TEMPLATES_PATH}")
print(f"Student Labs Path: {STUDENT_LABS_PATH}")
print(f"Templates exist: {os.path.exists(LAB_TEMPLATES_PATH)}")
print(f"Student labs exist: {os.path.exists(STUDENT_LABS_PATH)}")

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
    minimum_score = db.Column(db.Integer, default=0)  # Minimum score to pass the lab
    estimated_duration = db.Column(db.Integer)  # minutes
    difficulty = db.Column(db.String(20), default='medium')
    is_active = db.Column(db.Boolean, default=True)
    run_commands = db.Column(db.Text)  # JSON array of commands to run when lab starts
    num_checkpoints = db.Column(db.Integer, default=0)  # Number of checkpoints for submission
    checkpoint_rules = db.Column(db.Text)  # JSON: rules for decoding/validating checkpoints
    pdf_instruction_url = db.Column(db.String(500))  # URL or path to PDF instruction file
    output_result = db.Column(db.Text)  # Expected output result to display after running commands
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lab_sessions = db.relationship('LabSession', backref='lab', lazy=True, cascade='all, delete-orphan')
    lab_parameters = db.relationship('LabParameter', backref='lab', lazy=True, cascade='all, delete-orphan')
    
    @property
    def accessible_resources_list(self):
        """Return accessible resources as a list"""
        if self.accessible_resources:
            return json.loads(self.accessible_resources)
        return []
    
    @property
    def run_commands_list(self):
        """Return run commands as a list"""
        print("Self run commands: ", self.run_commands)
        if not self.run_commands:
            return []

        try:
            # Nếu self.run_commands là JSON list, load bình thường
            commands = json.loads(self.run_commands)
            if isinstance(commands, list):
                return commands
            # Nếu JSON là string, bọc thành list
            return [commands]
        except json.JSONDecodeError:
            # Nếu không phải JSON, coi như là string bình thường
            return [self.run_commands]
    
    @property
    def checkpoint_rules_dict(self):
        """Return checkpoint rules as a dictionary"""
        if self.checkpoint_rules:
            return json.loads(self.checkpoint_rules)
        return {}

class LabParameter(db.Model):
    __tablename__ = 'lab_parameters'
    
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
    parameter_name = db.Column(db.String(100), nullable=False)  # e.g., ${fieldName}
    parameter_values = db.Column(db.Text, nullable=False)  # JSON array of possible values
    file_path = db.Column(db.String(500))  # Optional: path to file that should be modified
    description = db.Column(db.Text)  # Optional description
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def values_list(self):
        """Return parameter values as a list"""
        if self.parameter_values:
            return json.loads(self.parameter_values)
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
    checkpoint_answers = db.Column(db.Text)  # JSON: student's checkpoint answers
    checkpoint_results = db.Column(db.Text)  # JSON: validation results for each checkpoint
    generated_flag = db.Column(db.String(255))  # Auto-generated flag for this lab session
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
class LabsNetwork(db.Model):
    __tablename__ = 'labs_network'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)           # Tên mạng
    subnet_ip_base = db.Column(db.String(15), nullable=False) # Base IP cho container
    mask = db.Column(db.String(18), nullable=False)           # Subnet mask
    gateway = db.Column(db.String(15), nullable=False)        # Gateway
    used = db.Column(db.Boolean, default=False)               # Đã dùng hay chưa
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LabsNetwork {self.name} ({self.subnet_ip_base})>"    

# Helper Functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session['user']['role'] != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def is_edu_email(email):
    """Check if email is from an educational institution"""
    pattern = os.getenv('ALLOWED_EMAIL_REGEX', r'^.+@.+\.edu(\..+)?$')
    return bool(re.match(pattern, email, re.IGNORECASE))

# Async HTTP helpers using aiohttp
async def fetch_url_async(url, method='GET', headers=None, data=None, timeout=30):
    """
    Async function to fetch URL using aiohttp
    
    Args:
        url: URL to fetch
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers dict
        data: Optional data for POST requests
        timeout: Request timeout in seconds
    
    Returns:
        dict with status, headers, and content
    """
    async with aiohttp.ClientSession() as session:
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=timeout_obj
            ) as response:
                content = await response.text()
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'content': content,
                    'success': response.status < 400
                }
        except asyncio.TimeoutError:
            return {
                'status': 408,
                'error': 'Request timeout',
                'success': False
            }
        except Exception as e:
            return {
                'status': 500,
                'error': str(e),
                'success': False
            }

async def fetch_multiple_urls_async(urls):
    """
    Fetch multiple URLs concurrently using aiohttp
    
    Args:
        urls: List of URLs to fetch
    
    Returns:
        List of response dicts
    """
    tasks = [fetch_url_async(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

def run_async(coro):
    """
    Helper to run async function in sync context
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def check_lab_resource_availability(resource_urls):
    """
    Check if lab resources (external APIs, services) are available
    
    Args:
        resource_urls: List of resource URLs to check
    
    Returns:
        dict with availability status for each resource
    """
    results = {}
    async with aiohttp.ClientSession() as session:
        for url in resource_urls:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get(url, timeout=timeout) as response:
                    results[url] = {
                        'available': response.status < 500,
                        'status': response.status,
                        'response_time': response.headers.get('X-Response-Time', 'N/A')
                    }
            except Exception as e:
                results[url] = {
                    'available': False,
                    'error': str(e)
                }
    return results

def validate_command_access(command, accessible_resources, current_dir):
    """
    Validate if a command is allowed based on accessible resources
    Returns (is_allowed, reason)
    """
    import shlex
    
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
    # if cmd not in ALLOWED_COMMANDS:
    #     return False, f"Command '{cmd}' is not allowed"
    
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
    # if cmd in ['cd', 'cat', 'grep', 'find', 'type'] and len(parts) > 1:
    #     # Check all path arguments (skip flags starting with -)
    #     for arg in parts[1:]:
    #         if arg.startswith('-'):
    #             continue
                
    #         target_path = arg
            
    #         # Remove quotes if present
    #         target_path = target_path.strip('"').strip("'")
            
    #         # Skip if it's a flag or option
    #         if target_path.startswith('-'):
    #             continue
            
    #         # Convert relative path to absolute
    #         if not os.path.isabs(target_path):
    #             target_path = os.path.join(current_dir, target_path)
            
    #         # Normalize path to prevent traversal
    #         target_path = os.path.normpath(target_path)
            
    #         # Check if path is within accessible resources
    #         is_accessible = False
    #         for resource in accessible_resources:
    #             resource_abs = os.path.join(current_dir, resource) if not os.path.isabs(resource) else resource
    #             resource_abs = os.path.normpath(resource_abs)
                
    #             if target_path.startswith(resource_abs):
    #                 is_accessible = True
    #                 break
            
    #         if not is_accessible:
    #             return False, f"Access denied to path: {target_path}"
    
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
    return google.authorize_redirect(redirect_uri,
        access_type="offline",
        prompt="consent")

@app.route('/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        email = user_info['email']
        
        # # Validate .edu email
        # if not is_edu_email(email):
        #     flash('Only .edu email addresses are allowed to access this system.', 'error')
        #     return redirect(url_for('index'))
        
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

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_id = session['user']['id']
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    total_enrollments = Enrollment.query.filter_by(user_id=user_id).count()
    completed_labs = LabSession.query.filter_by(user_id=user_id, status='completed').count()
    in_progress_labs = LabSession.query.filter_by(user_id=user_id, status='in_progress').count()
    
    # Get average score
    completed_sessions = LabSession.query.filter_by(user_id=user_id, status='completed').all()
    avg_score = sum(s.score for s in completed_sessions if s.score) / len(completed_sessions) if completed_sessions else 0
    
    # Get recent lab sessions
    recent_sessions = db.session.query(LabSession, Lab).join(Lab).filter(
        LabSession.user_id == user_id
    ).order_by(LabSession.started_at.desc()).limit(10).all()
    
    return render_template('profile.html', 
                         user=user,
                         total_enrollments=total_enrollments,
                         completed_labs=completed_labs,
                         in_progress_labs=in_progress_labs,
                         avg_score=round(avg_score, 1),
                         recent_sessions=recent_sessions)

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    user_id = session['user']['id']
    user = User.query.get_or_404(user_id)
    return render_template('settings.html', user=user)

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update user settings"""
    user_id = session['user']['id']
    user = User.query.get_or_404(user_id)
    
    data = request.json
    
    try:
        if 'full_name' in data:
            user.full_name = data['full_name']
            session['user']['full_name'] = data['full_name']
        
        if 'email' in data and data['email'] != user.email:
            # Check if email already exists
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
            session['user']['email'] = data['email']
        
        db.session.commit()
        return jsonify({'message': 'Settings updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/check_resources', methods=['POST'])
@login_required
def check_resources():
    """Check availability of external resources using aiohttp"""
    resource_urls = request.json.get('urls', [])
    
    if not resource_urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    # Run async function in sync context
    results = run_async(check_lab_resource_availability(resource_urls))
    
    return jsonify({
        'resources': results,
        'checked_at': datetime.utcnow().isoformat()
    })

@app.route('/api/fetch_url', methods=['POST'])
@login_required
def fetch_url():
    """Fetch a URL using aiohttp (for lab exercises)"""
    data = request.json
    url = data.get('url')
    method = data.get('method', 'GET')
    headers = data.get('headers')
    payload = data.get('data')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Run async fetch
    result = run_async(fetch_url_async(url, method, headers, payload))
    
    return jsonify(result)

@app.route('/api/fetch_multiple', methods=['POST'])
@login_required
def fetch_multiple():
    """Fetch multiple URLs concurrently using aiohttp"""
    urls = request.json.get('urls', [])
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    if len(urls) > 10:
        return jsonify({'error': 'Maximum 10 URLs allowed'}), 400
    
    # Run async fetch for multiple URLs
    results = run_async(fetch_multiple_urls_async(urls))
    
    return jsonify({
        'results': results,
        'count': len(results)
    })

@app.route('/api/check_lab_template/<int:lab_id>')
@login_required
def check_lab_template(lab_id):
    """Check if lab template exists"""
    lab = db.session.get(Lab, lab_id)
    if not lab:
        return jsonify({'error': 'Lab not found', 'exists': False}), 404
    
    template_path = os.path.join(LAB_TEMPLATES_PATH, lab.template_folder)
    exists = os.path.exists(template_path)
    
    # List available templates
    available_templates = []
    if os.path.exists(LAB_TEMPLATES_PATH):
        available_templates = [d for d in os.listdir(LAB_TEMPLATES_PATH) 
                             if os.path.isdir(os.path.join(LAB_TEMPLATES_PATH, d))]
    
    return jsonify({
        'lab_id': lab_id,
        'lab_name': lab.name,
        'template_folder': lab.template_folder,
        'template_path': template_path,
        'exists': exists,
        'available_templates': available_templates,
        'LAB_TEMPLATES_PATH': LAB_TEMPLATES_PATH
    })

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    users = User.query.all()
    courses = Course.query.all()
    labs = Lab.query.all()
    enrollments = Enrollment.query.all()
    lab_sessions = LabSession.query.all()
    
    stats = {
        'total_users': len(users),
        'total_courses': len(courses),
        'total_labs': len(labs),
        'total_enrollments': len(enrollments),
        'total_lab_sessions': len(lab_sessions),
        'active_users': User.query.filter_by(is_active=True).count(),
        'active_courses': Course.query.filter_by(is_active=True).count(),
    }
    
    return render_template('admin.html', 
                         users=users, 
                         courses=courses, 
                         labs=labs,
                         enrollments=enrollments,
                         stats=stats)

# User Management
@app.route('/admin/users')
@admin_required
def admin_users():
    """Get all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([{
        'id': u.id,
        'email': u.email,
        'full_name': u.full_name,
        'role': u.role,
        'is_active': u.is_active,
        'created_at': u.created_at.isoformat() if u.created_at else None,
        'last_login': u.last_login.isoformat() if u.last_login else None
    } for u in users])

@app.route('/admin/user/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user"""
    user = User.query.get_or_404(user_id)
    data = request.json
    
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    try:
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user and corresponding Linux user"""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == session['user']['id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    try:
        user_email = user.email
        
        # Delete from database first
        db.session.delete(user)
        db.session.commit()
        
        # Delete Linux user if on Linux system
        if platform.system() != 'Windows':
            linux_username = get_student_username(user_email)
            success, message = delete_linux_user(linux_username, remove_home=True)
            
            if success:
                print(f"✅ Deleted user {user_email} and Linux user {linux_username}")
                return jsonify({
                    'message': 'User and Linux user deleted successfully',
                    'linux_user_deleted': True,
                    'linux_username': linux_username
                })
            else:
                print(f"⚠️ User {user_email} deleted but Linux user deletion failed: {message}")
                return jsonify({
                    'message': 'User deleted but Linux user deletion failed',
                    'warning': message,
                    'linux_user_deleted': False
                })
        else:
            return jsonify({
                'message': 'User deleted successfully',
                'linux_user_deleted': False,
                'note': 'Not running on Linux system'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Course Management
@app.route('/admin/courses')
@admin_required
def admin_courses():
    """Get all courses"""
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return jsonify([{
        'id': c.id,
        'code': c.code,
        'name': c.name,
        'description': c.description,
        'semester': c.semester,
        'is_active': c.is_active,
        'max_students': c.max_students,
        'lab_count': len(c.labs),
        'enrollment_count': len(c.enrollments),
        'created_at': c.created_at.isoformat() if c.created_at else None
    } for c in courses])

@app.route('/admin/course', methods=['POST'])
@admin_required
def create_course():
    """Create new course"""
    data = request.json
    
    course = Course(
        code=data['code'],
        name=data['name'],
        description=data.get('description', ''),
        semester=data.get('semester', ''),
        max_students=data.get('max_students', 50),
        instructor_id=session['user']['id']
    )
    
    try:
        db.session.add(course)
        db.session.commit()
        return jsonify({'message': 'Course created successfully', 'id': course.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/course/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    """Update course"""
    course = Course.query.get_or_404(course_id)
    data = request.json
    
    if 'code' in data:
        course.code = data['code']
    if 'name' in data:
        course.name = data['name']
    if 'description' in data:
        course.description = data['description']
    if 'semester' in data:
        course.semester = data['semester']
    if 'is_active' in data:
        course.is_active = data['is_active']
    if 'max_students' in data:
        course.max_students = data['max_students']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Course updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/course/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    """Delete course"""
    course = Course.query.get_or_404(course_id)
    
    try:
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': 'Course deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# PDF Upload Helper Functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename_custom(filename):
    """Create a secure filename"""
    # Remove any path components
    filename = os.path.basename(filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove any characters that aren't alphanumeric, underscore, hyphen, or dot
    filename = re.sub(r'[^\w\-.]', '', filename)
    return filename

@app.route('/api/upload-lab-pdf', methods=['POST'])
@admin_required
def upload_lab_pdf():
    """Upload PDF file for lab instructions"""
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['pdf']
        lab_id = request.form.get('lab_id')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Create secure filename with lab_id prefix
        original_filename = secure_filename_custom(file.filename)
        filename = f"lab_{lab_id}_{original_filename}" if lab_id else f"lab_{original_filename}"
        
        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Return URL path
        pdf_url = f"/static/pdfs/{filename}"
        return jsonify({
            'message': 'PDF uploaded successfully',
            'pdf_url': pdf_url,
            'filename': filename
        })
    
    except Exception as e:
        print(f"Error uploading PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Lab Management
@app.route('/admin/labs')
@admin_required
def admin_labs():
    """Get all labs"""
    labs = Lab.query.order_by(Lab.course_id, Lab.order_index).all()
    return jsonify([{
        'id': l.id,
        'name': l.name,
        'course_id': l.course_id,
        'course_name': l.course.name,
        'description': l.description,
        'template_folder': l.template_folder,
        'accessible_resources': l.accessible_resources,
        'build_command': l.build_command,
        'run_commands': l.run_commands,
        'num_checkpoints': l.num_checkpoints,
        'checkpoint_rules': l.checkpoint_rules,
        'pdf_instruction_url': l.pdf_instruction_url,
        'output_result': l.output_result,
        'difficulty': l.difficulty,
        'is_active': l.is_active,
        'order_index': l.order_index,
        'max_score': l.max_score,
        'minimum_score': l.minimum_score,
        'estimated_duration': l.estimated_duration,
        'deadline': l.deadline.isoformat() if l.deadline else None,
        'created_at': l.created_at.isoformat() if l.created_at else None,
        'parameters': [{
            'id': p.id,
            'parameter_name': p.parameter_name,
            'parameter_values': p.parameter_values,
            'file_path': p.file_path,
            'description': p.description
        } for p in l.lab_parameters]
    } for l in labs])

@app.route('/admin/lab', methods=['POST'])
@admin_required
def create_lab():
    """Create new lab"""
    data = request.json
    
    lab = Lab(
        course_id=data['course_id'],
        name=data['name'],
        description=data.get('description', ''),
        template_folder=data['template_folder'],
        accessible_resources=json.dumps(data.get('accessible_resources', [])),
        build_command=data.get('build_command', ''),
        run_commands=json.dumps(data.get('run_commands', [])),
        num_checkpoints=data.get('num_checkpoints', 0),
        checkpoint_rules=json.dumps(data.get('checkpoint_rules', {})),
        pdf_instruction_url=data.get('pdf_instruction_url'),
        output_result=data.get('output_result'),
        order_index=data.get('order_index', 0),
        difficulty=data.get('difficulty', 'medium'),
        max_score=data.get('max_score', 100),
        minimum_score=data.get('minimum_score', 0),
        estimated_duration=data.get('estimated_duration', 60)
    )
    
    if 'deadline' in data and data['deadline']:
        lab.deadline = datetime.fromisoformat(data['deadline'])
    
    try:
        db.session.add(lab)
        db.session.commit()
        
        # Create parameters if provided
        if 'parameters' in data and data['parameters']:
            for param_data in data['parameters']:
                param = LabParameter(
                    lab_id=lab.id,
                    parameter_name=param_data['parameter_name'],
                    parameter_values=json.dumps(param_data.get('parameter_values', [])),
                    file_path=param_data.get('file_path'),
                    description=param_data.get('description', '')
                )
                db.session.add(param)
            db.session.commit()
        
        return jsonify({'message': 'Lab created successfully', 'id': lab.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lab/<int:lab_id>', methods=['PUT'])
@admin_required
def update_lab(lab_id):
    """Update lab"""
    lab = Lab.query.get_or_404(lab_id)
    data = request.json
    
    if 'name' in data:
        lab.name = data['name']
    if 'description' in data:
        lab.description = data['description']
    if 'template_folder' in data:
        lab.template_folder = data['template_folder']
    if 'accessible_resources' in data:
        lab.accessible_resources = json.dumps(data['accessible_resources'])
    if 'build_command' in data:
        lab.build_command = data['build_command']
    if 'run_commands' in data:
        lab.run_commands = json.dumps(data['run_commands'])
    if 'num_checkpoints' in data:
        lab.num_checkpoints = data['num_checkpoints']
    if 'checkpoint_rules' in data:
        lab.checkpoint_rules = json.dumps(data['checkpoint_rules'])
    if 'pdf_instruction_url' in data:
        lab.pdf_instruction_url = data['pdf_instruction_url']
    if 'output_result' in data:
        lab.output_result = data['output_result']
    if 'order_index' in data:
        lab.order_index = data['order_index']
    if 'difficulty' in data:
        lab.difficulty = data['difficulty']
    if 'max_score' in data:
        lab.max_score = data['max_score']
    if 'minimum_score' in data:
        lab.minimum_score = data['minimum_score']
    if 'estimated_duration' in data:
        lab.estimated_duration = data['estimated_duration']
    if 'is_active' in data:
        lab.is_active = data['is_active']
    if 'deadline' in data:
        lab.deadline = datetime.fromisoformat(data['deadline']) if data['deadline'] else None
    
    # Update parameters if provided
    if 'parameters' in data:
        # Delete old parameters
        LabParameter.query.filter_by(lab_id=lab_id).delete()
        
        # Create new parameters
        for param_data in data['parameters']:
            param = LabParameter(
                lab_id=lab_id,
                parameter_name=param_data['parameter_name'],
                parameter_values=json.dumps(param_data.get('parameter_values', [])),
                file_path=param_data.get('file_path'),
                description=param_data.get('description', '')
            )
            db.session.add(param)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Lab updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lab/<int:lab_id>', methods=['DELETE'])
@admin_required
def delete_lab(lab_id):
    """Delete lab"""
    lab = Lab.query.get_or_404(lab_id)
    
    try:
        db.session.delete(lab)
        db.session.commit()
        return jsonify({'message': 'Lab deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Lab Parameters Management
@app.route('/admin/lab/<int:lab_id>/parameters')
@admin_required
def get_lab_parameters(lab_id):
    """Get all parameters for a lab"""
    lab = Lab.query.get_or_404(lab_id)
    return jsonify([{
        'id': p.id,
        'parameter_name': p.parameter_name,
        'parameter_values': p.parameter_values,
        'values_list': p.values_list,
        'file_path': p.file_path,
        'description': p.description,
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in lab.lab_parameters])

@app.route('/admin/lab/<int:lab_id>/parameter', methods=['POST'])
@admin_required
def create_lab_parameter(lab_id):
    """Create new lab parameter"""
    lab = Lab.query.get_or_404(lab_id)
    data = request.json
    
    param = LabParameter(
        lab_id=lab_id,
        parameter_name=data['parameter_name'],
        parameter_values=json.dumps(data.get('parameter_values', [])),
        file_path=data.get('file_path', None),
        description=data.get('description', '')
    )
    
    try:
        db.session.add(param)
        db.session.commit()
        return jsonify({'message': 'Parameter created successfully', 'id': param.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lab_parameter/<int:param_id>', methods=['PUT'])
@admin_required
def update_lab_parameter(param_id):
    """Update lab parameter"""
    param = LabParameter.query.get_or_404(param_id)
    data = request.json
    
    if 'parameter_name' in data:
        param.parameter_name = data['parameter_name']
    if 'parameter_values' in data:
        param.parameter_values = json.dumps(data['parameter_values'])
    if 'file_path' in data:
        param.file_path = data['file_path']
    if 'description' in data:
        param.description = data['description']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Parameter updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lab_parameter/<int:param_id>', methods=['DELETE'])
@admin_required
def delete_lab_parameter(param_id):
    """Delete lab parameter"""
    param = LabParameter.query.get_or_404(param_id)
    
    try:
        db.session.delete(param)
        db.session.commit()
        return jsonify({'message': 'Parameter deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Enrollment Management
@app.route('/admin/enrollments')
@admin_required
def admin_enrollments():
    """Get all enrollments"""
    enrollments = db.session.query(Enrollment, User, Course)\
        .join(User, Enrollment.user_id == User.id)\
        .join(Course, Enrollment.course_id == Course.id)\
        .order_by(Enrollment.enrolled_at.desc()).all()
    return jsonify([{
        'id': e.id,
        'user_id': e.user_id,
        'user_name': u.full_name,
        'user_email': u.email,
        'course_id': e.course_id,
        'course_name': c.name,
        'course_code': c.code,
        'status': e.status,
        'enrolled_at': e.enrolled_at.isoformat() if e.enrolled_at else None
    } for e, u, c in enrollments])

@app.route('/admin/enrollment/<int:enrollment_id>', methods=['PUT'])
@admin_required
def update_enrollment(enrollment_id):
    """Update enrollment status"""
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    data = request.json
    
    if 'status' in data:
        enrollment.status = data['status']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Enrollment updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/enrollment/<int:enrollment_id>', methods=['DELETE'])
@admin_required
def delete_enrollment(enrollment_id):
    """Delete enrollment"""
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    try:
        db.session.delete(enrollment)
        db.session.commit()
        return jsonify({'message': 'Enrollment deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Lab Session Management
@app.route('/admin/lab_sessions')
@admin_required
def admin_lab_sessions():
    """Get all lab sessions"""
    sessions = db.session.query(LabSession, User, Lab, Course)\
        .join(User, LabSession.user_id == User.id)\
        .join(Lab, LabSession.lab_id == Lab.id)\
        .join(Course, Lab.course_id == Course.id)\
        .order_by(LabSession.created_at.desc()).all()
    return jsonify([{
        'id': ls.id,
        'user_id': ls.user_id,
        'user_name': u.full_name,
        'user_email': u.email,
        'lab_id': ls.lab_id,
        'lab_name': l.name,
        'course_name': c.name,
        'course_code': c.code,
        'status': ls.status,
        'student_folder': ls.student_folder,
        'score': ls.score,
        'started_at': ls.started_at.isoformat() if ls.started_at else None,
        'completed_at': ls.completed_at.isoformat() if ls.completed_at else None,
        'last_accessed': ls.last_accessed.isoformat() if ls.last_accessed else None,
        'created_at': ls.created_at.isoformat() if ls.created_at else None
    } for ls, u, l, c in sessions])

@app.route('/admin/lab_session', methods=['POST'])
@admin_required
def create_lab_session():
    """Create new lab session"""
    data = request.json
    
    user_id = data['user_id']
    lab_id = data['lab_id']
    
    # Check if session already exists
    existing = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
    if existing:
        return jsonify({'error': 'Lab session already exists for this user'}), 400
    
    # Clone lab folder
    if not clone_lab_folder(user_id, lab_id):
        return jsonify({'error': 'Failed to setup lab environment'}), 500
    
    # Get the newly created session
    lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
    
    return jsonify({'message': 'Lab session created successfully', 'id': lab_session.id})

@app.route('/admin/lab_session/<int:session_id>', methods=['PUT'])
@admin_required
def update_lab_session(session_id):
    """Update lab session"""
    lab_session = LabSession.query.get_or_404(session_id)
    data = request.json
    
    if 'status' in data:
        lab_session.status = data['status']
    if 'score' in data:
        lab_session.score = data['score']
    if 'submission_notes' in data:
        lab_session.submission_notes = data['submission_notes']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Lab session updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lab_session/<int:session_id>/commands')
@admin_required
def get_lab_session_commands(session_id):
    """Get command logs for a lab session"""
    lab_session = LabSession.query.get_or_404(session_id)
    
    # Get all terminal sessions for this lab session
    terminal_sessions = TerminalSession.query.filter_by(lab_session_id=session_id).all()
    
    # Get all commands from all terminal sessions
    commands = []
    for ts in terminal_sessions:
        session_commands = CommandLog.query.filter_by(
            terminal_session_id=ts.id
        ).order_by(CommandLog.executed_at.asc()).all()
        commands.extend(session_commands)
    
    # Sort all commands by execution time
    commands.sort(key=lambda x: x.executed_at)
    
    # Count statistics
    total_commands = len(commands)
    blocked_commands = sum(1 for cmd in commands if not cmd.is_allowed)
    
    return jsonify({
        'commands': [{
            'id': cmd.id,
            'command': cmd.command,
            'output': cmd.output,
            'exit_code': cmd.exit_code,
            'is_allowed': cmd.is_allowed,
            'blocked_reason': cmd.blocked_reason,
            'executed_at': cmd.executed_at.isoformat() if cmd.executed_at else None
        } for cmd in commands],
        'total_commands': total_commands,
        'blocked_commands': blocked_commands
    })

@app.route('/admin/lab_session/<int:session_id>', methods=['DELETE'])
@admin_required
def delete_lab_session(session_id):
    """Delete lab session"""
    lab_session = LabSession.query.get_or_404(session_id)
    
    # Delete student folder if exists
    if lab_session.student_folder and os.path.exists(lab_session.student_folder):
        try:
            shutil.rmtree(lab_session.student_folder)
        except Exception as e:
            print(f"Warning: Could not delete folder {lab_session.student_folder}: {e}")
    
    try:
        db.session.delete(lab_session)
        db.session.commit()
        return jsonify({'message': 'Lab session deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Linux User Management Functions
def create_linux_user(username, home_dir=None):
    """
    Create a Linux user for student isolation
    
    Args:
        username: Username to create (e.g., student_21020939)
        home_dir: Home directory path (default: /home/{username})
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Check if user already exists
        try:
            subprocess.run(['id', username], check=True, capture_output=True)
            print(f"User {username} already exists")
            return True, f"User {username} already exists"
        except subprocess.CalledProcessError:
            # User doesn't exist, create it
            pass
        
        # Set home directory
        if not home_dir:
            home_dir = f"/home/{username}"
        
        # Create user with home directory
        create_cmd = [
            'sudo', 'useradd',
            '-m',  # Create home directory
            '-s', '/bin/bash',  # Set shell to bash
            '-d', home_dir,  # Home directory
            username
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"Failed to create user: {result.stderr}"
            print(error_msg)
            return False, error_msg
        
        # Set a default password (you should change this or use key-based auth)
        password = f"{username}_password"  # Simple password for lab environment
        passwd_cmd = ['sudo', 'chpasswd']
        passwd_input = f"{username}:{password}\n"
        
        result = subprocess.run(passwd_cmd, input=passwd_input, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"Failed to set password: {result.stderr}"
            print(error_msg)
            return False, error_msg
        
        # Set appropriate permissions for home directory
        subprocess.run(['sudo', 'chmod', '775', home_dir], check=True)
        subprocess.run(['sudo', 'chown', f'{username}:{username}', home_dir], check=True)
        
        print(f"✅ Created Linux user: {username} with home: {home_dir}")
        return True, f"User {username} created successfully"
        
    except Exception as e:
        error_msg = f"Error creating Linux user {username}: {e}"
        print(error_msg)
        traceback.print_exc()
        return False, error_msg

def delete_linux_user(username, remove_home=True):
    """
    Delete a Linux user
    
    Args:
        username: Username to delete
        remove_home: Whether to remove home directory
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Check if user exists
        try:
            subprocess.run(['id', username], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            return True, f"User {username} does not exist"
        
        # Kill all processes owned by the user
        subprocess.run(['sudo', 'pkill', '-u', username], capture_output=True)
        
        # Delete user
        delete_cmd = ['sudo', 'userdel']
        if remove_home:
            delete_cmd.append('-r')  # Remove home directory
        delete_cmd.append(username)
        
        result = subprocess.run(delete_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"Failed to delete user: {result.stderr}"
            print(error_msg)
            return False, error_msg
        
        print(f"✅ Deleted Linux user: {username}")
        return True, f"User {username} deleted successfully"
        
    except Exception as e:
        error_msg = f"Error deleting Linux user {username}: {e}"
        print(error_msg)
        return False, error_msg

def get_student_username(user_email):
    """
    Generate a safe Linux username from user email
    
    Args:
        user_email: User's email address
    
    Returns:
        str: Safe username (e.g., student_21020939)
    """
    # Extract username part from email (before @)
    username_part = user_email.split('@')[0]
    
    # Remove special characters and make it lowercase
    safe_username = re.sub(r'[^a-z0-9_]', '', username_part.lower())
    
    # Prefix with 'student_' to avoid conflicts
    return f"student_{safe_username}"

def clone_lab_folder(user_id, lab_id):
    """Clone lab template folder for a specific user"""
    lab = db.session.get(Lab, lab_id)
    user = db.session.get(User, user_id)
    
    if not lab or not user:
        print(f"Error: Lab or User not found (lab_id={lab_id}, user_id={user_id})")
        return False
    
    try:
        template_path = os.path.join(LAB_TEMPLATES_PATH, lab.template_folder)
        
        # Check if template exists
        if not os.path.exists(template_path):
            print(f"Error: Template folder not found: {template_path}") 
        
        # Step 1: Create Linux user for this student
        linux_username = get_student_username(user.email)
        success, message = create_linux_user(linux_username)
        if not success:
            print(f"Warning: Could not create Linux user: {message}")
            # Continue anyway for development/testing
        
        # Create unique folder name for student
        student_folder_name = f"{user.email.split('@')[0]}-{lab.template_folder}"
        student_folder_path = os.path.join(STUDENT_LABS_PATH, student_folder_name)
        
        # Clone the template folder if it doesn't exist
        if not os.path.exists(student_folder_path):
            shutil.copytree(template_path, student_folder_path)
            print(f"Successfully cloned lab folder: {student_folder_path}")
            
            # Step 2: Set ownership to the Linux user (if on Linux/Unix)
            if platform.system() != 'Windows':
                try:
                    print("CHOWN TO USER: ", linux_username)
                    subprocess.run([
                        'sudo', 'chown', '-R', 
                        f'{linux_username}:{linux_username}', 
                        student_folder_path
                    ], check=True, capture_output=True)
                    
                    # Set appropriate permissions (read/write/execute for owner, read for group)
                    subprocess.run([
                        'sudo', 'chmod', '-R', '775', 
                        student_folder_path
                    ], check=True, capture_output=True)
                    
                    current_user = getpass.getuser()
                    print("CURRENT USER: ", current_user)
                    # 4️⃣ Thêm user hiện tại vào group linux_username
                    subprocess.run([
                        'sudo', 'usermod', '-aG', linux_username, current_user
                    ], check=True, capture_output=True)

                    subprocess.run(
                    'sg', linux_username,
                    shell=True
                    )
                    print(f"✅ Set ownership to {linux_username} for {student_folder_path}")
                except Exception as e:
                    print(f"Warning: Could not set ownership: {e}")
        else:
            print(f"Student folder already exists: {student_folder_path}")
        
        # Create or update lab session
        lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
        if not lab_session:
            lab_session = LabSession(
                user_id=user_id,
                lab_id=lab_id,
                student_folder=student_folder_path
            )
            db.session.add(lab_session)
            print(f"Created new lab session for user {user_id}, lab {lab_id}")
        else:
            lab_session.student_folder = student_folder_path
            print(f"Updated existing lab session {lab_session.id}")
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Error cloning lab folder: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

@app.route('/api/start_lab/<int:lab_id>', methods=['POST'])
@login_required
def start_lab(lab_id):
    """Start a lab session"""
    user_id = session['user']['id']
    
    # Get lab and verify user enrollment
    lab = db.session.get(Lab, lab_id)
    user = User.query.filter_by(id=user_id).first()
    user_linux_name = get_student_username(user.email)
    print("PREPARE FOR LABS ", lab.name)
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
        # Clone lab folder and create session
        if not clone_lab_folder(user_id, lab_id):
            print(f"Failed to clone lab folder for user {user_id}, lab {lab_id}")
            return jsonify({'error': 'Failed to setup lab environment. Please check if the lab template exists.'}), 500
        # Fetch the newly created session
        lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
        if not lab_session:
            print(f"Lab session not found after cloning for user {user_id}, lab {lab_id}")
            return jsonify({'error': 'Failed to create lab session'}), 500
    
    # Update session status
    if lab_session.status == 'not_started':
        lab_session.status = 'in_progress'
        lab_session.started_at = datetime.utcnow()
    
    lab_session.last_accessed = datetime.utcnow()
    
    try:
        db.session.commit()
        print("PREPARE FOR LABS ", lab.name)
        # Apply parameter file modifications if specified
        if lab.lab_parameters and lab_session.student_folder:
            apply_parameter_file_modifications(lab, lab_session.student_folder, user_linux_name)
        
        # # Execute build command if specified
        # if lab.build_command and lab_session.student_folder:
        #     execute_build_command(user_linux_name, lab.build_command, lab_session.student_folder)
        
        # Execute run commands if specified
        print(f"Student folder: {lab_session.student_folder}")
        print(f"Raw command list: {lab.run_commands_list}")
        if lab.run_commands_list and lab_session.student_folder:
            # For qua từng command trong list
            for command in lab.run_commands_list:
                # Thay thế tất cả parameters với random values
                print(f"Raw run command: {command}")
                replaced_command = replace_lab_parameters(lab, command, user)
                print(f"Executing run command: {replaced_command}")
                execute_run_command(user_linux_name, replaced_command, lab_session.student_folder)
        
        return jsonify({
            'message': 'Lab started successfully',
            'lab_session_id': lab_session.id,
            'redirect_url': f'/lab/{lab_session.id}/terminal'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error starting lab: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to start lab'}), 500

def apply_parameter_file_modifications(lab, student_folder, user_linux_name):
    """
    Modify files with parameter values when file_path is specified
    and rename file if file_path contains STUDENT_NAME_LAB_PARAMETER
    """
    import random
    import os

    # Store parameter replacements to use consistently
    parameter_replacements = {}
    current_user = getpass.getuser()
    full_command = f'sudo setfacl -R -m u:{current_user}:rwx {os.path.join(student_folder)}'
    subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=500
        )
    # First pass: determine random values for all parameters
    for param in lab.lab_parameters:
        if param.values_list:
            value = random.choice(param.values_list)
            value = value.replace(STUDENT_NAME_LAB_PARAMETER, user_linux_name)

            network = None
            if LAB_NETWORK_MASK_PARAMETER in value:
                network = LabsNetwork.query.filter_by(used=False).first()
                if not network:
                    raise ValueError("No available network for lab!")
                value = value.replace(LAB_NETWORK_MASK_PARAMETER, network.mask)
            if LAB_NETWORK_GATEWAY_PARAMETER in value:     
                if network is None:
                    network = LabsNetwork.query.filter_by(used=False).first()
                    if not network:
                        raise ValueError("No available network for lab!")
                value = value.replace(LAB_NETWORK_GATEWAY_PARAMETER, network.gateway) 
            if LAB_SUB_NETWORK_IP_PREFIX in value:     
                if network is None:
                    network = LabsNetwork.query.filter_by(used=False).first()
                    if not network:
                        raise ValueError("No available network for lab!")
                pattern = rf"{re.escape(LAB_SUB_NETWORK_IP_PREFIX)}_(\d+)"
                import re
                # Replace từng match
                def replacer(match):
                    index = int(match.group(1))
                    return f"{network.subnet_ip_base}{index}"
                value = re.sub(pattern, replacer, value)                    
            parameter_replacements[param.parameter_name] = value

    # Second pass: modify files and rename if needed
    for param in lab.lab_parameters:
        if not param.file_path:
            continue

        original_file_path = os.path.join(student_folder, param.file_path)
        final_file_path = original_file_path

        # 🔥 Nếu file_path chứa STUDENT_NAME_LAB_PARAMETER -> đổi tên fil
        if STUDENT_NAME_LAB_PARAMETER in param.file_path:
            new_relative_path = param.file_path.replace(
                STUDENT_NAME_LAB_PARAMETER, user_linux_name
            )
            final_file_path = os.path.join(student_folder, new_relative_path)

            # Tạo folder nếu chưa tồn tại
            folder_of_file = os.path.dirname(final_file_path)
            os.makedirs(folder_of_file, exist_ok=True)

            # --- Áp ACL: chỉ owner + manager có quyền ghi ---
            # chmod chuẩn: owner rwx, group r-x, others ---
            # set ACL cho manager
            full_command = f'sudo setfacl -R -m u:{current_user}:rwx {os.path.join(folder_of_file)}'
            subprocess.run(
                    full_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=500
                )
            # Đổi tên file (nếu file cũ tồn tại)
            if os.path.exists(original_file_path):
                os.rename(original_file_path, final_file_path)
                print(f"🔄 Renamed file: {param.file_path} → {new_relative_path}")
            else:
                print(f"⚠️ Cannot rename, file not found: {original_file_path}")
                continue


        # đọc file sau khi rename (final_file_path)
        if not os.path.exists(final_file_path):
            print(f"⚠️ File not found for parameter modification: {final_file_path}")
            continue

        try:
            with open(final_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace all parameters inside file content
            modified_content = content
            for param_name, param_value in parameter_replacements.items():
                modified_content = modified_content.replace(param_name, str(param_value))

            with open(final_file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            print(f"✅ Modified file: {final_file_path}")
            print(f"   Replacements: {parameter_replacements}")

        except Exception as e:
            print(f"❌ Error modifying file {final_file_path}: {e}")


def replace_lab_parameters(lab, command, user):
    """
    Replace lab parameters in command with random values from their ranges
    For qua tất cả parameters của lab, chọn random value và replace vào command
    
    Args:
        lab: Lab object with parameters
        command: Command string with parameters like ${fieldName}
    
    Returns:
        Command with parameters replaced
    """
    import random
    
    username = get_student_username(user.email)
    user_id = username.replace("student_","")
    print("================ STUDENT_ID ============= ", user_id)
    replaced_command = command.replace("${email}", user.email)
    print("========================= ", replaced_command)
    replaced_command = replaced_command.replace(STUDENT_ID_LAB_PARAMETER, user_id)
    # For qua tất cả parameters của bài lab
    for param in lab.lab_parameters:
        parameter_name = param.parameter_name  # e.g., ${fieldName}
        values_list = param.values_list  # List các giá trị có thể
        
        if not values_list:
            continue
        
        # Chọn random 1 giá trị từ list
        random_value = random.choice(values_list)
        random_value = random_value.replace(STUDENT_NAME_LAB_PARAMETER, username)
        network = None
        if LAB_NETWORK_MASK_PARAMETER in random_value:
            network = LabsNetwork.query.filter_by(used=False).first()
            if not network:
                raise ValueError("No available network for lab!")
            random_value = random_value.replace(LAB_NETWORK_MASK_PARAMETER, network.mask)
        if LAB_NETWORK_GATEWAY_PARAMETER in random_value:     
            if network is None:
                network = LabsNetwork.query.filter_by(used=False).first()
                if not network:
                    raise ValueError("No available network for lab!")
            random_value = random_value.replace(LAB_NETWORK_GATEWAY_PARAMETER, network.gateway)   
        if LAB_SUB_NETWORK_IP_PREFIX in random_value:     
            if network is None:
                network = LabsNetwork.query.filter_by(used=False).first()
                if not network:
                    raise ValueError("No available network for lab!")
            pattern = rf"{re.escape(LAB_SUB_NETWORK_IP_PREFIX)}_(\d+)"
            import re
            # Replace từng match
            def replacer(match):
                index = int(match.group(1))
                return f"{network.subnet_ip_base}{index}"
            random_value = re.sub(pattern, replacer, random_value)      
        # Replace tất cả occurrences của parameter name = parameter value
        replaced_command = replaced_command.replace(parameter_name, str(random_value))
        
        print(f"Replaced {parameter_name} with {random_value}")
    
    return replaced_command

def execute_run_command(user_linux_name, run_command, working_directory):
    """Execute run command when lab starts"""
    try:
        # Dùng newgrp -c "<command>" để chạy command với group mới
        print("COMPOSE DOWN DOCKER CONTAINER ....")
        full_command = f'sg {user_linux_name} -c "cd {working_directory} && sudo docker compose down"'
        subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=500
        )
        last_folder = os.path.basename(working_directory)  # ví dụ: lab-1
        expected_cmd = f"rebuild_{last_folder}"

        if run_command == expected_cmd:
            full_command = run_command
        else:
            full_command = f'sg {user_linux_name} -c "cd {working_directory} && sudo {run_command}"'

        print("============ FULL COMMAND ========== ", full_command)
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=500
        )
        
        print(f"Run command executed. Exit code: {result.returncode}")
        if result.stdout:
            print(f"Run output: {result.stdout}")
        if result.stderr:
            print(f"Run errors: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Run command timed out")
        return False
    except Exception as e:
        print(f"Error executing run command: {e}")
        return False

def execute_build_command(user_linux_name, build_command, working_directory):
    """Execute build command in lab directory"""
    try:
        full_command = f'sg {user_linux_name} -c "cd {working_directory} && sudo {build_command}"'
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
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

@app.route('/api/lab/<int:lab_session_id>/submit', methods=['POST'])
@login_required
def submit_lab(lab_session_id):
    """Submit lab with checkpoint answers"""
    user_id = session['user']['id']
    
    # Get lab session and verify ownership
    lab_session = LabSession.query.get_or_404(lab_session_id)
    if lab_session.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    lab = lab_session.lab
    data = request.json
    user = db.session.get(User, user_id)
    # Validate number of checkpoints
    if lab.num_checkpoints == 0:
        return jsonify({'error': 'This lab does not have checkpoints configured'}), 400
    
    checkpoint_answers = data.get('checkpoint_answers', [])
    if len(checkpoint_answers) != lab.num_checkpoints:
        return jsonify({
            'error': f'Expected {lab.num_checkpoints} checkpoint answers, got {len(checkpoint_answers)}'
        }), 400
    
    try:
        # Validate and score checkpoints
        results = validate_checkpoints(lab, lab_session, checkpoint_answers, user)
        
        # Calculate score based on points from each checkpoint
        total_points = 0
        earned_points = 0
        passed_checkpoints = 0
        
        for result in results:
            total_points += result['points']
            if result['passed']:
                earned_points += result['points']
                passed_checkpoints += 1
        
        # Calculate final score (scale to max_score)
        if total_points > 0:
            score = int((earned_points / total_points) * lab.max_score)
        else:
            score = 0
        
        # Determine if passed based on minimum score
        minimum_score = lab.minimum_score or 0
        passed = score >= minimum_score
        status = 'completed' if passed else 'failed'
        
        # Update lab session
        lab_session.checkpoint_answers = json.dumps(checkpoint_answers)
        lab_session.checkpoint_results = json.dumps(results)
        lab_session.score = score
        lab_session.status = status
        lab_session.completed_at = datetime.utcnow()
        lab_session.submission_notes = data.get('notes', '')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lab submitted successfully',
            'score': score,
            'max_score': lab.max_score,
            'minimum_score': minimum_score,
            'passed': passed,
            'status': status,
            'earned_points': earned_points,
            'total_points': total_points,
            'passed_checkpoints': passed_checkpoints,
            'total_checkpoints': lab.num_checkpoints,
            'results': results
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting lab: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def validate_checkpoints(lab, lab_session, checkpoint_answers, user):
    """
    Validate checkpoint answers based on lab rules
    
    Args:
        lab: Lab object with checkpoint_rules (JSON array with decode_method, expected_answer, case_sensitive, points, use_auto_flag)
        lab_session: LabSession object with generated_flag
        checkpoint_answers: List of student answers
    
    Returns:
        List of validation results with points
    """
    import base64
    import hashlib
    
    # Parse checkpoint rules
    try:
        rules = json.loads(lab.checkpoint_rules) if lab.checkpoint_rules else []
    except:
        rules = []
    
    results = []
    
    for i, answer in enumerate(checkpoint_answers):
        # Get rule for this checkpoint
        if i < len(rules):
            rule = rules[i]
            decode_method = rule.get('decode_method', 'plain')
            expected_answer = rule.get('expected_answer', '')
            case_sensitive = rule.get('case_sensitive', False)
            points = rule.get('points', 10)
            use_auto_flag = rule.get('use_auto_flag', False)  # New option for auto-generated flag
        else:
            # Default if no rule configured
            decode_method = 'plain'
            expected_answer = ''
            case_sensitive = False
            points = 10
            use_auto_flag = False
        
        result = {
            'checkpoint': i + 1,
            'passed': False,
            'student_answer': answer,
            'decoded_answer': None,
            'expected_answer': expected_answer,
            'points': points,
            'earned_points': 0,
            'message': ''
        }
        
        try:
            # Decode answer based on method
            decoded = decode_checkpoint_answer(answer, decode_method)
            result['decoded_answer'] = decoded
            
            # Generate unique flag for this lab session
            # Format: Flag{SHA1(date_email_lab-key)}
            from datetime import datetime
            from zoneinfo import ZoneInfo
            import hashlib

            user_email = user.email  # hoặc gán chuỗi trực tiếp
            username = get_student_username(user_email)
            # Lấy thời gian theo Asia/Ho_Chi_Minh và format giống hệt bash: DDMMYYYY
            dt = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
            date_str = dt.strftime("%d%m%Y")

            # Ghép chuỗi giống hệt bash
            expected_answer = expected_answer.replace(STUDENT_NAME_LAB_PARAMETER, username)
            print("========== ", date_str, user_email, expected_answer)
            flag_input = f"{date_str}_{user_email}_{expected_answer}"

            # Hash SHA1 giống bash
            flag_hash = hashlib.sha1(flag_input.encode()).hexdigest()

            lab_session.generated_flag = f"FLAG{{{flag_hash}}}"
            print(f"Generated flag for lab session: {lab_session.generated_flag}")

            # Determine expected value
            if use_auto_flag:
                # Use auto-generated flag from lab session
                expected_value = lab_session.generated_flag if lab_session.generated_flag else expected_answer
                result['expected_answer'] = '[Auto-generated Flag]'
            else:
                expected_value = str(expected_answer)
            
            # Compare with expected answer
            student_value = str(decoded).strip()
            expected_value = str(expected_value).strip()
            
            if not case_sensitive:
                student_value = student_value.lower()
                expected_value = expected_value.lower()
            print("STUDENT VALUE ", student_value)
            print("EXPECTED VALUE ", expected_value)
            if student_value == expected_value:
                result['passed'] = True
                result['earned_points'] = points
                result['message'] = f'✓ Correct! (+{points} points)'
            else:
                result['message'] = f'✗ Incorrect (0/{points} points)'
                
        except Exception as e:
            result['message'] = f'Decode error: {str(e)}'
        
        results.append(result)
    
    return results

def decode_checkpoint_answer(answer, method):
    """
    Decode checkpoint answer using specified method
    
    Args:
        answer: Raw answer string
        method: Decoding method (base64, md5, sha256, sha1, plain, reverse, hex)
    
    Returns:
        Decoded value (for comparison with expected answer)
        
    Note:
        - plain: Direct text (no transformation)
        - base64: Decode base64 to text
        - md5/sha1/sha256: Hash methods - answer should be the hash itself (for verification)
        - reverse: Reverse the string
        - hex: Decode hex to text
    """
    import base64
    import hashlib
    
    if method == 'plain':
        # Direct comparison - no transformation
        return answer
    
    elif method == 'base64':
        # Decode base64 encoded input
        try:
            return base64.b64decode(answer).decode('utf-8')
        except:
            raise ValueError('Invalid base64 string')
    
    elif method == 'md5':
        # For hash methods: answer is already the hash, just return it for comparison
        # Expected answer should be the hash of the secret value
        return answer.lower().strip()
    
    elif method == 'sha256':
        # For hash methods: answer is already the hash, just return it for comparison
        return answer.lower().strip()
    
    elif method == 'sha1':
        # For hash methods: answer is already the hash, just return it for comparison
        return answer.lower().strip()
    
    elif method == 'reverse':
        # Reverse the string
        return answer[::-1]
    
    elif method == 'hex':
        # Decode hex to text
        try:
            return bytes.fromhex(answer).decode('utf-8')
        except:
            raise ValueError('Invalid hex string')
    
    else:
        raise ValueError(f'Unknown decode method: {method}')

# WebSocket Terminal Handlers
active_terminals = {}  # {session_id: {'terminal_session_id': int, 'lab_session_id': int, 'pty_fd': int, 'pid': int, 'read_thread': Thread}}

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    print(f"Client connected: {session_id}")

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    
    if 'user' not in session:
        emit('terminal_error', {'error': 'Not authenticated'})
        return
    
    user_id = session['user']['id']

    # Get user object
    user = db.session.get(User, user_id)
    if not user:
        emit('terminal_error', {'error': 'User not found'})
        return
    user_name = get_student_username(user.email)
    print(f"Client disconnected: {session_id}")
    print("=============== START CLEAN UP DOCKER OF " , user_name)
    cleanup_docker_resources(user_name)
    print("=============== END CLEAN UP DOCKER OF " , user_name)

    # Clean up terminal session and kill pty process
    if session_id in active_terminals:
        terminal_info = active_terminals[session_id]
        
        # Kill pty process if exists
        if 'pid' in terminal_info and terminal_info['pid']:
            try:
                os.kill(terminal_info['pid'], signal.SIGTERM)
                print(f"Killed pty process: {terminal_info['pid']}")
            except ProcessLookupError:
                print(f"Process {terminal_info['pid']} already dead")
            except Exception as e:
                print(f"Error killing process: {e}")
        
        # Close pty file descriptor
        if 'pty_fd' in terminal_info and terminal_info['pty_fd']:
            try:
                os.close(terminal_info['pty_fd'])
                print(f"Closed pty fd: {terminal_info['pty_fd']}")
            except Exception as e:
                print(f"Error closing pty fd: {e}")
        
        try:
            terminal_session = db.session.get(TerminalSession, terminal_info['terminal_session_id'])
            if terminal_session:
                terminal_session.is_active = False
                db.session.commit()
        except Exception as e:
            print(f"Warning: Could not update terminal session on disconnect: {e}")
            db.session.rollback()
        finally:
            del active_terminals[session_id]
import subprocess

def cleanup_docker_resources(student_name):
    try:
        # Escape student_name để tránh lỗi shell injection
        student_name = student_name.replace("'", "")

        # Remove containers
        cmd_containers = f"docker ps -a --format '{{{{.Names}}}}' | grep '{student_name}' || true"
        containers = subprocess.getoutput(cmd_containers)

        if containers.strip():
            for c in containers.splitlines():
                print(f"Removing container: {c}")
                subprocess.call(f"docker rm -f {c}", shell=True)
        else:
            print(f"No containers found for {student_name}")

        # Remove networks
        cmd_networks = f"docker network ls --format '{{{{.Name}}}}' | grep '{student_name}' || true"
        networks = subprocess.getoutput(cmd_networks)

        if networks.strip():
            for n in networks.splitlines():
                print(f"Removing network: {n}")
                subprocess.call(f"docker network rm {n}", shell=True)
        else:
            print(f"No networks found for {student_name}")

    except Exception as e:
        print(f"Error when cleaning docker resources: {e}")
         

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
    
    # Get user object
    user = db.session.get(User, user_id)
    if not user:
        emit('terminal_error', {'error': 'User not found'})
        return
    
    # Create terminal session
    terminal_session_id = str(uuid.uuid4())
    terminal_session = TerminalSession(
        session_id=terminal_session_id,
        user_id=user_id,
        lab_session_id=lab_session_id,
        current_directory=lab_session.student_folder or '/tmp'
    )
    
    db.session.add(terminal_session)
    db.session.commit()
    
    # Check if Windows or Linux
    is_windows = platform.system() == 'Windows'
    
    if is_windows:
        # Windows: Simple command-based mode (no pty)
        active_terminals[session_id] = {
            'terminal_session_id': terminal_session.id,
            'lab_session_id': lab_session.id,
            'command_buffer': '',
            'is_windows': True
        }
        
        welcome_msg = f"""
🧪 Lab Terminal - {lab_session.lab.name}
📁 Working Directory: {lab_session.student_folder}
⚠️  Security: Commands are validated for safety
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{get_prompt(lab_session.student_folder)}"""
        
        emit('terminal_output', {'data': welcome_msg})
        emit('terminal_ready', {'status': 'ready'})
    else:
        # Linux: Use pty for real bash session with user isolation
        try:
            linux_username = get_student_username(user.email)
            working_dir = lab_session.student_folder or '/tmp'
            
            # Fork a pty process
            pid, fd = pty.fork()
            
            if pid == 0:
                # Child process - this will exec into bash as student user
                try:
                    # Set environment variables
                    os.environ['HOME'] = working_dir
                    os.environ['USER'] = linux_username
                    os.environ['LOGNAME'] = linux_username
                    os.environ['SHELL'] = '/bin/bash'
                    os.environ['TERM'] = 'xterm-256color'
                    
                    # # Change to working directory
                    # os.chdir(working_dir)
                    
                    # # Execute bash as the student user
                    # os.execvp('sudo', ['sudo', '-u', linux_username, '/bin/bash'])
                    # child process, vẫn ở folder Python hiện tại
                    
                    os.execvp('sudo', [
                        'sudo',
                        '-u', linux_username,
                        '/bin/bash',
                        '-c',
                        f'cd {working_dir} && newgrp {linux_username}'
                    ])
                except Exception as e:
                    print(f"Child process error: {e}", flush=True)
                    os._exit(1)
            else:
                # Parent process - read from pty and send to client
                # Set fd to non-blocking
                import fcntl
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                # Store terminal info
                active_terminals[session_id] = {
                    'terminal_session_id': terminal_session.id,
                    'lab_session_id': lab_session.id,
                    'pty_fd': fd,
                    'pid': pid,
                    'is_windows': False
                }
                
                # Start reading thread for pty output
                import threading
                read_thread = threading.Thread(
                    target=read_pty_output,
                    args=(session_id, fd),
                    daemon=True
                )
                read_thread.start()
                active_terminals[session_id]['read_thread'] = read_thread
                
                print(f"✅ Started pty session - PID: {pid}, FD: {fd}, User: {linux_username}")
                result = subprocess.run(['id'], capture_output=True, text=True)
                print("Output of `id`:", result.stdout.strip())
                emit('terminal_ready', {'status': 'ready'})
                
        except Exception as e:
            error_msg = f"Failed to start terminal: {e}"
            print(error_msg)
            traceback.print_exc()
            emit('terminal_error', {'error': error_msg})
            return

def read_pty_output(session_id, fd):
    """Read output from pty and send to client via WebSocket"""
    print(f"Started pty reader thread for session {session_id}")
    
    try:
        while session_id in active_terminals:
            try:
                # Use select to wait for data with timeout
                readable, _, _ = select.select([fd], [], [], 0.1)
                
                if readable:
                    try:
                        # Read data from pty
                        data = os.read(fd, 4096)
                        if data:
                            # Decode and send to client
                            output = data.decode('utf-8', errors='replace')
                            socketio.emit('terminal_output', {'data': output}, room=session_id)
                        else:
                            # EOF - process died
                            print(f"PTY EOF for session {session_id}")
                            break
                    except OSError as e:
                        if e.errno == 5:  # EIO - process terminated
                            print(f"PTY process terminated for session {session_id}")
                            break
                        raise
                        
            except Exception as e:
                print(f"Error reading from pty: {e}")
                break
                
    except Exception as e:
        print(f"PTY reader thread error: {e}")
    finally:
        print(f"PTY reader thread stopped for session {session_id}")
        socketio.emit('terminal_error', {'error': 'Terminal session ended'}, room=session_id)

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
    
    # Check if Windows or Linux mode
    if terminal_info.get('is_windows', False):
        # Windows mode - command-based execution
        handle_windows_terminal_input(session_id, input_data, terminal_info)
    else:
        # Linux mode - pty-based, just forward input to pty
        pty_fd = terminal_info.get('pty_fd')
        if pty_fd:
            try:
                # Write input directly to pty
                os.write(pty_fd, input_data.encode('utf-8'))
                
                # Update last activity
                try:
                    terminal_session = db.session.get(TerminalSession, terminal_info['terminal_session_id'])
                    if terminal_session:
                        terminal_session.last_activity = datetime.utcnow()
                        db.session.commit()
                except Exception as e:
                    print(f"Warning: Could not update last activity: {e}")
                    db.session.rollback()
                    
            except Exception as e:
                print(f"Error writing to pty: {e}")
                emit('terminal_error', {'error': f'Failed to write to terminal: {e}'})
        else:
            emit('terminal_error', {'error': 'Terminal not ready'})

def handle_windows_terminal_input(session_id, input_data, terminal_info):
    """Handle terminal input for Windows (command-based mode)"""
    # Get fresh database objects using IDs
    terminal_session = db.session.get(TerminalSession, terminal_info['terminal_session_id'])
    lab_session = db.session.get(LabSession, terminal_info['lab_session_id'])
    
    if not terminal_session or not lab_session:
        emit('terminal_error', {'error': 'Terminal session expired'}, room=session_id)
        return
    
    # Handle input character by character
    if input_data == '\r' or input_data == '\n':
        # Execute command
        command = terminal_info.get('command_buffer', '').strip()
        if command:
            execute_secure_command(session_id, command, terminal_session, lab_session)
        else:
            emit('terminal_output', {'data': f'\r\n{get_prompt(terminal_session.current_directory)}'}, room=session_id)
        terminal_info['command_buffer'] = ''
        
    elif input_data == '\x7f':  # Backspace
        if terminal_info.get('command_buffer', ''):
            terminal_info['command_buffer'] = terminal_info['command_buffer'][:-1]
            emit('terminal_output', {'data': '\b \b'}, room=session_id)
            
    elif input_data == '\x03':  # Ctrl+C
        terminal_info['command_buffer'] = ''
        emit('terminal_output', {'data': f'^C\r\n{get_prompt(terminal_session.current_directory)}'}, room=session_id)
        
    elif input_data and len(input_data) == 1 and ord(input_data) >= 32:  # Printable characters
        terminal_info['command_buffer'] += input_data
        emit('terminal_output', {'data': input_data}, room=session_id)
    
    # Update last activity
    try:
        terminal_session.last_activity = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        print(f"Warning: Could not update last activity: {e}")
        db.session.rollback()

@socketio.on('terminal_resize')
def handle_terminal_resize(data):
    """Handle terminal resize events (for pty)"""
    session_id = request.sid
    
    if session_id not in active_terminals:
        return
    
    terminal_info = active_terminals[session_id]
    
    # Only handle resize for pty-based terminals (Linux)
    if terminal_info.get('is_windows', False):
        return
    
    pty_fd = terminal_info.get('pty_fd')
    if not pty_fd:
        return
    
    try:
        cols = data.get('cols', 80)
        rows = data.get('rows', 24)
        
        # Set terminal window size
        winsize = struct.pack('HHHH', rows, cols, 0, 0)
        fcntl.ioctl(pty_fd, termios.TIOCSWINSZ, winsize)
        
        print(f"Terminal resized to {cols}x{rows} for session {session_id}")
    except Exception as e:
        print(f"Error resizing terminal: {e}")

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
                    if platform.system() == 'Windows':
                        if command.lower() == 'ls':
                            command = 'dir'
                        elif command.lower().startswith('ls '):
                            command = command.replace('ls ', 'dir ', 1)
                
                elif command.lower().startswith('cat ') and platform.system() == 'Windows':
                    # Convert cat to type on Windows
                    command = command.replace('cat ', 'type ', 1)
                
                elif command.lower() == 'pwd' and platform.system() == 'Windows':
                    # Convert pwd to cd on Windows (shows current directory)
                    command = 'cd'
                
                # Execute system command with user isolation (Linux only)
                if platform.system() != 'Windows':
                    # Get Linux username for this student
                    linux_username = get_student_username(lab_session.user.email)
                    
                    # Run command as the specific Linux user using sudo
                    # This provides isolation between students
                    wrapped_command = [
                        'sudo', '-u', linux_username,
                        'bash', '-c',
                        f'cd {current_dir} && {command}'
                    ]
                    
                    result = subprocess.run(
                        wrapped_command,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                else:
                    # On Windows, run normally (no user isolation)
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
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create sample data for testing
        create_sample_data()
    
    print("🚀 Starting Lab Management System...")
    print("📡 Server will be available at: http://localhost:5000")
    print("🔐 Google OAuth configured")
    print("🧪 Lab environment ready")
    print("🔒 Secure terminal with command validation")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    