from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
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
import secrets
import threading
import hashlib
import logging
import ipaddress
import socket
import shlex
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    Counter = None
    Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = None

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

# ============================ Logging and Monitoring ============================

def setup_logging():
    """Initialize and configure the application logger."""
    log_dir = os.getenv('LOG_DIR', 'logs')
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = os.path.join(log_dir, 'lab_management.log')

    app_logger = logging.getLogger('lab_management_app')
    app_logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO))
    app_logger.handlers = []

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s [%(funcName)s:%(lineno)d] %(message)s')

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024)),
        backupCount=int(os.getenv('LOG_BACKUP_COUNT', 5)),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    return app_logger

logger = setup_logging()

# Kế thừa logger cho app
def attach_app_logger(flask_app):
    flask_app.logger.handlers = logger.handlers
    flask_app.logger.setLevel(logger.level)
    return flask_app

# Prometheus metrics
if Counter and Histogram:
    REQUEST_COUNT = Counter('lab_app_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status'])
    REQUEST_LATENCY = Histogram('lab_app_http_request_latency_seconds', 'HTTP request latency', ['method', 'endpoint'])
    FUNCTION_ERRORS = Counter('lab_app_function_errors_total', 'Total function errors', ['function'])
    LAB_STARTS = Counter('lab_app_lab_starts_total', 'Total lab starts')
    LAB_SUBMISSIONS = Counter('lab_app_lab_submissions_total', 'Total lab submissions')
else:
    REQUEST_COUNT = REQUEST_LATENCY = FUNCTION_ERRORS = LAB_STARTS = LAB_SUBMISSIONS = None

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app = attach_app_logger(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

configured_secret_key = os.getenv('SECRET_KEY')
if configured_secret_key:
    app.config['SECRET_KEY'] = configured_secret_key
else:
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    logger.warning('SECRET_KEY is not configured; using an ephemeral key for this process.')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost:3306/lab_management')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=int(os.getenv('SESSION_LIFETIME_HOURS', '8')))

# Google OAuth Config
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio_allowed_origins = os.getenv('SOCKETIO_ALLOWED_ORIGINS')
eventlet.monkey_patch()

if socketio_allowed_origins:
    socketio_cors_origins = [origin.strip() for origin in socketio_allowed_origins.split(',') if origin.strip()]
else:
    socketio_cors_origins = []
socketio = SocketIO(app, cors_allowed_origins=socketio_cors_origins, async_mode='eventlet')

lab_start_random_cache = {}
lab_start_random_cache_lock = threading.Lock()

# Flask request metrics middleware
@app.before_request
def before_request_metrics():
    if REQUEST_COUNT and REQUEST_LATENCY:
        request._start_time = datetime.utcnow()

@app.after_request
def after_request_metrics(response):
    if REQUEST_COUNT and REQUEST_LATENCY and hasattr(request, '_start_time'):
        method = request.method
        endpoint = request.path
        status_code = response.status_code
        duration = (datetime.utcnow() - request._start_time).total_seconds()
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    return response

@app.route('/metrics')
def metrics_endpoint():
    if generate_latest is None:
        return "Prometheus client is not installed.", 500
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'}), 200

# ============================ Logging and Monitoring ============================
LOG_DIR = os.getenv('LOG_DIR', 'logs')
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
log_file = os.path.join(LOG_DIR, 'lab_management.log')

logger = logging.getLogger('lab_management_app')
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024)),
    backupCount=int(os.getenv('LOG_BACKUP_COUNT', 5)),
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s [%(funcName)s:%(lineno)d] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Kế thừa logger cho app
def attach_app_logger(flask_app):
    flask_app.logger.handlers = logger.handlers
    flask_app.logger.setLevel(logger.level)
    return flask_app

app = attach_app_logger(app)

# Prometheus metrics
if Counter and Histogram:
    REQUEST_COUNT = Counter('lab_app_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status'])
    REQUEST_LATENCY = Histogram('lab_app_http_request_latency_seconds', 'HTTP request latency', ['method', 'endpoint'])
    FUNCTION_ERRORS = Counter('lab_app_function_errors_total', 'Total function errors', ['function'])
    LAB_STARTS = Counter('lab_app_lab_starts_total', 'Total lab starts')
    LAB_SUBMISSIONS = Counter('lab_app_lab_submissions_total', 'Total lab submissions')
else:
    REQUEST_COUNT = REQUEST_LATENCY = FUNCTION_ERRORS = LAB_STARTS = LAB_SUBMISSIONS = None


def _metrics_before_request():
    request._start_time = datetime.utcnow()


def _metrics_after_request(response):
    if REQUEST_COUNT and REQUEST_LATENCY:
        path = request.path
        method = request.method
        status = response.status_code
        REQUEST_COUNT.labels(method=method, endpoint=path, http_status=status).inc()
        duration = (datetime.utcnow() - getattr(request, '_start_time', datetime.utcnow())).total_seconds()
        REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)
    return response


# ================================================================================


def generate_lab_start_random_string(length=16):
    return secrets.token_hex(length // 2)


def cache_lab_start_random_string(student_id, random_string):
    with lab_start_random_cache_lock:
        lab_start_random_cache[str(student_id)] = random_string


def get_cached_lab_start_random_string(student_id):
    with lab_start_random_cache_lock:
        return lab_start_random_cache.get(str(student_id))


def split_submitted_flag_and_random(submitted_value):
    submitted_value = (submitted_value or "").strip()
    if not submitted_value:
        return "", ""

    if submitted_value.startswith("FLAG{"):
        closing_brace_index = submitted_value.find("}")
        if closing_brace_index != -1:
            flag_part = submitted_value[:closing_brace_index + 1].strip()
            random_part = submitted_value[closing_brace_index + 1:].strip()
            random_part = random_part.lstrip(":|#- ")
            return flag_part, random_part

    for separator in ("::", "|", ":", "#"):
        if separator in submitted_value:
            flag_part, random_part = submitted_value.rsplit(separator, 1)
            return flag_part.strip(), random_part.strip()

    return submitted_value, ""


def build_generated_flag(expected_answer, user):
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo

    user_email = user.email
    username = get_student_username(user_email)
    dt = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    date_str = dt.strftime("%d%m%Y")
    resolved_expected_answer = str(expected_answer).replace(STUDENT_NAME_LAB_PARAMETER, username)
    logger.info("========== ", date_str, user_email, resolved_expected_answer)
    flag_input = f"{date_str}_{user_email}_{resolved_expected_answer}"
    flag_hash = hashlib.sha1(flag_input.encode()).hexdigest()
    return f"FLAG{{{flag_hash}}}", resolved_expected_answer

def _normalize_flow_type(flow_type):
    ft = (flow_type or FLOW_TYPE_LABTAINER).strip().upper()
    return ft if ft in (FLOW_TYPE_LABTAINER, FLOW_TYPE_CUSTOM) else FLOW_TYPE_LABTAINER


def _web_prefix_for_flow(flow_type: str, lab_id: int) -> str:
    """
    Encode backend routing into the URL path so nginx can route by prefix
    without relying on X-FLOW-TYPE / ?flow_type.

    - CUSTOM    -> vul-lab-c (backend C)
    - LABTAINER -> vul-lab-a if lab_id even else vul-lab-b
    """
    return "vul-lab-a" if (int(lab_id) % 2 == 0) else "vul-lab-b"
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
WEB_TEST_PORT_PARAM = "${webTestPort}"
CLIENT_TEST_PORT_PARAM = "${clientTestPort}"
DB_TEST_PORT_PARAM = "${dbTestPort}"
LAB_RANDOM_STRING_PARAM = "${labRandomString}"

# Flow Type Constants
FLOW_TYPE_LABTAINER = "LABTAINER"
FLOW_TYPE_CUSTOM = "CUSTOM"

# Ensure directories exist
os.makedirs(LAB_TEMPLATES_PATH, exist_ok=True)
os.makedirs(STUDENT_LABS_PATH, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Log paths for debugging
logger.info(f"Lab Templates Path: {LAB_TEMPLATES_PATH}")
logger.info(f"Student Labs Path: {STUDENT_LABS_PATH}")
logger.info(f"Templates exist: {os.path.exists(LAB_TEMPLATES_PATH)}")
logger.info(f"Student labs exist: {os.path.exists(STUDENT_LABS_PATH)}")

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
    # Routing hint for Nginx: LABTAINER -> backend A/B, CUSTOM -> backend C
    flow_type = db.Column(db.String(20), nullable=False, default=FLOW_TYPE_LABTAINER)
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
        logger.info("Self run commands: ", self.run_commands)
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
    success_start_lab_output = db.Column(db.Text)
    checkpoint_answers = db.Column(db.Text)  # JSON: student's checkpoint answers
    checkpoint_results = db.Column(db.Text)  # JSON: validation results for each checkpoint
    generated_flag = db.Column(db.String(255))  # Auto-generated flag for this lab session
    web_port = db.Column(db.Integer, nullable=True)
    client_port = db.Column(db.Integer, nullable=True)
    db_port = db.Column(db.Integer, nullable=True)
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

class Port(db.Model):
    __tablename__ = 'ports'

    id = db.Column(db.Integer, primary_key=True)
    port_number = db.Column(db.Integer, nullable=False, unique=True)
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Helper Functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # API calls should return JSON (not an HTML redirect) so the frontend can handle it cleanly.
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Not authenticated'}), 401
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


SAFE_IDENTIFIER_RE = re.compile(r'^[a-z0-9_][a-z0-9_.-]{0,127}$', re.IGNORECASE)
SAFE_CONTAINER_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$')
BLOCKED_FETCH_HOSTS = {
    'localhost',
    '127.0.0.1',
    '::1',
    '0.0.0.0',
    '169.254.169.254',
    'metadata.google.internal',
}


def _env_flag(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def get_or_create_csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


def ensure_safe_identifier(value, field_name='value'):
    value = (value or '').strip()
    if not SAFE_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f'Invalid {field_name}')
    return value


def ensure_safe_container_name(value, field_name='container name'):
    value = (value or '').strip()
    if not SAFE_CONTAINER_RE.fullmatch(value):
        raise ValueError(f'Invalid {field_name}')
    return value


def ensure_safe_working_directory(path_value):
    if not path_value:
        raise ValueError('Working directory is required')

    resolved_path = Path(path_value).resolve(strict=False)
    allowed_roots = [
        Path(LAB_TEMPLATES_PATH).resolve(strict=False),
        Path(STUDENT_LABS_PATH).resolve(strict=False),
    ]
    if platform.system() != 'Windows':
        allowed_roots.append(Path('/home').resolve(strict=False))

    if not any(resolved_path == root or root in resolved_path.parents for root in allowed_roots):
        raise ValueError('Working directory is outside allowed roots')
    return str(resolved_path)


def is_safe_remote_url(url):
    try:
        parsed = urlparse((url or '').strip())
    except ValueError:
        return False, 'Malformed URL'

    if parsed.scheme not in {'http', 'https'}:
        return False, 'Only http/https URLs are allowed'
    if not parsed.hostname:
        return False, 'URL hostname is required'

    hostname = parsed.hostname.strip().lower()
    if hostname in BLOCKED_FETCH_HOSTS:
        return False, 'Access to local or metadata hosts is not allowed'

    try:
        ip_obj = ipaddress.ip_address(hostname)
        resolved_ips = [ip_obj]
    except ValueError:
        try:
            resolved_ips = []
            for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, parsed.port or None, type=socket.SOCK_STREAM):
                candidate_ip = sockaddr[0]
                resolved_ips.append(ipaddress.ip_address(candidate_ip))
        except socket.gaierror:
            return False, 'Unable to resolve target host'

    for ip_obj in resolved_ips:
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            return False, 'Access to internal network addresses is not allowed'

    return True, None


@app.context_processor
def inject_template_security_context():
    return {
        'csrf_token': get_or_create_csrf_token()
    }


def _is_csrf_exempt_request():
    if request.method in {'GET', 'HEAD', 'OPTIONS', 'TRACE'}:
        return True
    if request.endpoint in {'metrics_endpoint', 'login', 'static'}:
        return True
    return False


@app.before_request
def enforce_csrf_protection():
    if _is_csrf_exempt_request():
        return None
    # if True:
    #     return None
    session_token = session.get('_csrf_token')
    if not session_token:
        return jsonify({'error': 'Missing CSRF session token'}), 403

    request_token = request.headers.get('X-CSRF-Token') or request.form.get('_csrf_token')
    if not request_token or not secrets.compare_digest(session_token, request_token):
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'error': 'CSRF validation failed'}), 403
        flash('CSRF validation failed.', 'error')
        return redirect(url_for('index'))

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
    is_allowed, reason = is_safe_remote_url(url)
    if not is_allowed:
        return {
            'status': 400,
            'error': reason,
            'success': False
        }

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
            is_allowed, reason = is_safe_remote_url(url)
            if not is_allowed:
                results[url] = {
                    'available': False,
                    'error': reason
                }
                continue
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
        session.permanent = True
        session['_csrf_token'] = secrets.token_urlsafe(32)
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
    session.pop('_csrf_token', None)
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
                'flow_type': getattr(lab, 'flow_type', FLOW_TYPE_LABTAINER),
                'lab_session_id': lab_session.id if lab_session else None,
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
    payload = request.get_json(silent=True) or {}
    resource_urls = payload.get('urls', [])
    
    if not isinstance(resource_urls, list) or not resource_urls:
        return jsonify({'error': 'No URLs provided'}), 400
    if len(resource_urls) > 10:
        return jsonify({'error': 'Maximum 10 URLs allowed'}), 400
    
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
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    method = str(data.get('method', 'GET')).upper()
    headers = data.get('headers') if isinstance(data.get('headers'), dict) else None
    payload = data.get('data')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    if method not in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}:
        return jsonify({'error': 'HTTP method is not allowed'}), 400
    is_allowed, reason = is_safe_remote_url(url)
    if not is_allowed:
        return jsonify({'error': reason}), 400
    
    # Run async fetch
    result = run_async(fetch_url_async(url, method, headers, payload))
    
    return jsonify(result)

@app.route('/api/fetch_multiple', methods=['POST'])
@login_required
def fetch_multiple():
    """Fetch multiple URLs concurrently using aiohttp"""
    payload = request.get_json(silent=True) or {}
    urls = payload.get('urls', [])
    
    if not isinstance(urls, list) or not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    if len(urls) > 10:
        return jsonify({'error': 'Maximum 10 URLs allowed'}), 400
    for url in urls:
        is_allowed, reason = is_safe_remote_url(url)
        if not is_allowed:
            return jsonify({'error': f'Unsafe URL blocked: {reason}', 'url': url}), 400
    
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
    user_id = session['user']['id']
    
    lab = db.session.get(Lab, lab_id)
    if not lab:
        return jsonify({'error': 'Lab not found', 'exists': False}), 404
    
    # Check if user is enrolled in the course that contains this lab
    enrollment = Enrollment.query.filter_by(
        user_id=user_id, 
        course_id=lab.course_id,
        status='active'
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Access denied. You are not enrolled in this course.'}), 403
    
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

@app.route('/api/lab_session/<int:session_id>', methods=['PUT'])
@login_required
def update_user_lab_session(session_id):
    """Update user's own lab session"""
    user_id = session['user']['id']
    lab_session = LabSession.query.get_or_404(session_id)
    
    # Ensure the session belongs to the current user
    if lab_session.user_id != user_id:
        return jsonify({'error': 'Access denied. You can only update your own lab sessions.'}), 403
    
    data = request.json
    
    # Allow users to update certain fields only
    if 'submission_notes' in data:
        lab_session.submission_notes = data['submission_notes']
    # Users cannot update status or score directly
    
    try:
        db.session.commit()
        return jsonify({'message': 'Lab session updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/enrollment/<int:enrollment_id>', methods=['PUT'])
@login_required
def update_user_enrollment(enrollment_id):
    """Update user's own enrollment (e.g., withdraw)"""
    user_id = session['user']['id']
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    # Ensure the enrollment belongs to the current user
    if enrollment.user_id != user_id:
        return jsonify({'error': 'Access denied. You can only update your own enrollments.'}), 403
    
    data = request.json
    
    # Allow users to update status (e.g., withdraw)
    if 'status' in data and data['status'] in ['active', 'withdrawn']:
        enrollment.status = data['status']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Enrollment updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Admin Routes
@app.route('/admin')
@app.route('/admin/')
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
    
    current_user_id = session['user']['id']
    
    # Prevent admin from deactivating or changing role of themselves
    if user_id == current_user_id:
        if 'is_active' in data and data['is_active'] == False:
            return jsonify({'error': 'Cannot deactivate your own account'}), 400
        if 'role' in data and data['role'] != user.role:
            return jsonify({'error': 'Cannot change your own role'}), 400
    
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
                logger.info(f"✅ Deleted user {user_email} and Linux user {linux_username}")
                return jsonify({
                    'message': 'User and Linux user deleted successfully',
                    'linux_user_deleted': True,
                    'linux_username': linux_username
                })
            else:
                logger.info(f"⚠️ User {user_email} deleted but Linux user deletion failed: {message}")
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
        if lab_id and not str(lab_id).isdigit():
            return jsonify({'error': 'Invalid lab_id'}), 400

        file.stream.seek(0)
        header = file.stream.read(5)
        file.stream.seek(0)
        if header != b'%PDF-':
            return jsonify({'error': 'Uploaded file is not a valid PDF'}), 400
        
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
        logger.info(f"Error uploading PDF: {str(e)}")
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
        'flow_type': getattr(l, 'flow_type', FLOW_TYPE_LABTAINER),
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

    flow_type = (data.get('flow_type') or FLOW_TYPE_LABTAINER).upper()
    if flow_type not in (FLOW_TYPE_LABTAINER, FLOW_TYPE_CUSTOM):
        flow_type = FLOW_TYPE_LABTAINER
    
    lab = Lab(
        course_id=data['course_id'],
        name=data['name'],
        description=data.get('description', ''),
        template_folder=data['template_folder'],
        flow_type=flow_type,
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
    if 'flow_type' in data:
        flow_type = (data.get('flow_type') or FLOW_TYPE_LABTAINER).upper()
        if flow_type in (FLOW_TYPE_LABTAINER, FLOW_TYPE_CUSTOM):
            lab.flow_type = flow_type
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
    flow_type = _normalize_flow_type(getattr(lab_session.lab, 'flow_type', None))
    
    # Only remove per-student cloned folders. CUSTOM labs can point to a shared lab folder.
    if (
        flow_type != FLOW_TYPE_CUSTOM
        and lab_session.student_folder
        and os.path.exists(lab_session.student_folder)
    ):
        try:
            shutil.rmtree(lab_session.student_folder)
        except Exception as e:
            logger.info(f"Warning: Could not delete folder {lab_session.student_folder}: {e}")
    
    # Release ports
    if lab_session.web_port:
        release_port(lab_session.web_port)
    if lab_session.client_port:
        release_port(lab_session.client_port)
    if lab_session.db_port:
        release_port(lab_session.db_port)
    
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
        username = ensure_safe_identifier(username, 'linux username')
        # Check if user already exists
        try:
            subprocess.run(['id', username], check=True, capture_output=True)
            logger.info(f"User {username} already exists")
            return True, f"User {username} already exists"
        except subprocess.CalledProcessError:
            # User doesn't exist, create it
            pass
        
        # Set home directory
        if not home_dir:
            home_dir = f"/home/{username}"
        home_dir = ensure_safe_working_directory(home_dir)
        
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
            logger.info(error_msg)
            return False, error_msg
        
        # Set a default password (you should change this or use key-based auth)
        password = f"{username}_password"  # Simple password for lab environment
        passwd_cmd = ['sudo', 'chpasswd']
        passwd_input = f"{username}:{password}\n"
        
        result = subprocess.run(passwd_cmd, input=passwd_input, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"Failed to set password: {result.stderr}"
            logger.info(error_msg)
            return False, error_msg
        
        # Set appropriate permissions for home directory
        subprocess.run(['sudo', 'chmod', '750', home_dir], check=True)
        subprocess.run(['sudo', 'chown', f'{username}:{username}', home_dir], check=True)
        
        logger.info(f"✅ Created Linux user: {username} with home: {home_dir}")
        return True, f"User {username} created successfully"
        
    except Exception as e:
        error_msg = f"Error creating Linux user {username}: {e}"
        logger.info(error_msg)
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
        username = ensure_safe_identifier(username, 'linux username')
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
            logger.info(error_msg)
            return False, error_msg
        
        logger.info(f"✅ Deleted Linux user: {username}")
        return True, f"User {username} deleted successfully"
        
    except Exception as e:
        error_msg = f"Error deleting Linux user {username}: {e}"
        logger.info(error_msg)
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
        logger.warning('clone_lab_folder: Lab or User not found (lab_id=%s, user_id=%s)', lab_id, user_id)
        return False
    
    try:
        template_path = os.path.join(LAB_TEMPLATES_PATH, lab.template_folder)
        
        # Check if template exists
        if not os.path.exists(template_path):
            logger.error('Template folder not found: %s', template_path)
        
        # Step 1: Create Linux user for this student
        linux_username = get_student_username(user.email)
        success, message = create_linux_user(linux_username)
        if not success:
            logger.warning('Could not create Linux user for %s: %s', linux_username, message)
            # Continue anyway for development/testing
        
        # Create unique folder name for student
        student_folder_name = f"{user.email.split('@')[0]}-{lab.template_folder}"
        student_folder_path = os.path.join(STUDENT_LABS_PATH, student_folder_name)

        # 🔁 Nếu đã tồn tại thì xóa để clone lại
        if os.path.exists(student_folder_path):
            logger.warning('Student folder exists, removing: %s', student_folder_path)
            shutil.rmtree(student_folder_path)
        shutil.copytree(template_path, student_folder_path)
        logger.info('Successfully cloned lab folder: %s', student_folder_path)
        
        # Step 2: Set ownership to the Linux user (if on Linux/Unix)
        if platform.system() != 'Windows':
            try:
                # logger.info("CHOWN TO USER: ", linux_username)
                # subprocess.run([
                #     'sudo', 'chown', '-R', 
                #     f'{linux_username}:{linux_username}', 
                #     student_folder_path
                # ], check=True, capture_output=True)
                
                # Set appropriate permissions (read/write/execute for owner, read for group)
                subprocess.run([
                    'sudo', 'chmod', '-R', '750', 
                    student_folder_path
                ], check=True, capture_output=True)
                
                current_user = getpass.getuser()
                logger.debug('CURRENT USER: %s', current_user)
                # 4️⃣ Thêm user hiện tại vào group linux_username
                subprocess.run([
                    'sudo', 'usermod', '-aG', linux_username, current_user
                ], check=True, capture_output=True)

                subprocess.run(
                'sg', linux_username,
                shell=True
                )
                logger.info('Set ownership to %s for %s', linux_username, student_folder_path)
            except Exception as e:
                logger.warning('Could not set ownership: %s', e)
        
        # Create or update lab session
        lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
        if not lab_session:
            lab_session = LabSession(
                user_id=user_id,
                lab_id=lab_id,
                student_folder=student_folder_path
            )
            db.session.add(lab_session)
            logger.info('clone_lab_folder: Created new lab session for user %s, lab %s', user_id, lab_id)
        else:
            lab_session.student_folder = student_folder_path
            logger.info('clone_lab_folder: Updated existing lab session %s', lab_session.id)
        
        db.session.commit()
        logger.info('clone_lab_folder: Completed for user %s lab %s', user_id, lab_id)
        return True
        
    except Exception as e:
        logger.exception('Error cloning lab folder lab_id=%s user_id=%s: %s', lab_id, user_id, e)
        if FUNCTION_ERRORS:
            FUNCTION_ERRORS.labels(function='clone_lab_folder').inc()
        db.session.rollback()
        return False

@app.route('/api/start_lab/<int:lab_id>', methods=['POST'])
@login_required
def start_lab(lab_id):
    """Start a lab session"""
    start_ts = datetime.utcnow()
    logger.info('start_lab called: lab_id=%s, user_id=%s', lab_id, session['user']['id'])
    if LAB_STARTS:
        LAB_STARTS.inc()

    user_id = session['user']['id']
    
    # Get lab and verify user enrollment
    lab = db.session.get(Lab, lab_id)
    user = User.query.filter_by(id=user_id).first()
    if not lab:
        logger.warning('start_lab failed: lab not found lab_id=%s user_id=%s', lab_id, user_id)
        return jsonify({'error': 'Lab not found'}), 404
    
    flow_type = _normalize_flow_type(getattr(lab, 'flow_type', None))
    
    logger.info('PREPARE FOR LABS %s (flow_type=%s)', lab.name, flow_type)
    user_linux_name = get_student_username(user.email) if user and user.email else f"student_{user_id}"
    student_id = user_linux_name.replace("student_", "")
    
    enrollment = Enrollment.query.filter_by(
        user_id=user_id, course_id=lab.course_id, status='active'
    ).first()
    
    if not enrollment:
        logger.warning('start_lab unauthorized: user_id=%s not enrolled in course_id=%s', user_id, lab.course_id)
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    # Get or create lab session
    lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()


    # Clone lab folder only for LABTAINER flow_type
    if flow_type == FLOW_TYPE_LABTAINER:
        if not clone_lab_folder(user_id, lab_id):
            logger.info(f"Failed to clone lab folder for user {user_id}, lab {lab_id}")
            return jsonify({'error': 'Failed to setup lab environment. Please check if the lab template exists.'}), 500

    # Fetch or create the session
    lab_session = LabSession.query.filter_by(user_id=user_id, lab_id=lab_id).first()
    if not lab_session:
        student_folder = f"/home/hoangnth/labtainer/labs/{lab.template_folder}" if flow_type == FLOW_TYPE_CUSTOM else None
        lab_session = LabSession(
            user_id=user_id,
            lab_id=lab_id,
            student_folder=student_folder
        )
        db.session.add(lab_session)
        db.session.commit()
        logger.info('Created new lab session for user %s, lab %s (%s)', user_id, lab_id, 'with folder' if student_folder else 'no folder')
    
    # Update session status
    if lab_session.status == 'not_started':
        lab_session.status = 'in_progress'
        lab_session.started_at = datetime.utcnow()
    
    try:
        lab_session.last_accessed = datetime.utcnow()
        lab_random_string = generate_lab_start_random_string()
        cache_lab_start_random_string(student_id, lab_random_string)
        port = reserve_port(8000, 10000, user_linux_name)
        if not port:
            raise ValueError("No available web port for lab!")
        client_port = reserve_port(50000, 60000, user_linux_name)
        if not client_port:
            raise ValueError("No available client port for lab!")

        db_port = reserve_port(3000, 5000, user_linux_name)
        if not db_port:
            raise ValueError("No available database port for lab!")
        # Store ports in lab session
        lab_session.web_port = port
        lab_session.client_port = client_port
        lab_session.db_port = db_port

        logger.info('start_lab web_port=%s client_port=%s db_port=%s student=%s', port, client_port, db_port, user_linux_name)
        output_template = lab.output_result or ""
        lab_session.success_start_lab_output = output_template.replace(WEB_TEST_PORT_PARAM, str(port))
        lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(CLIENT_TEST_PORT_PARAM, str(client_port))
        lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(DB_TEST_PORT_PARAM, str(db_port))
        lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(STUDENT_ID_LAB_PARAMETER, user_linux_name.replace("student_",""))
        lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(STUDENT_NAME_LAB_PARAMETER, user_linux_name)
        lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(LAB_RANDOM_STRING_PARAM, lab_random_string)

        flow_type = _normalize_flow_type(getattr(lab, 'flow_type', None))
        base_url = request.host_url.rstrip('/')
        web_prefix = _web_prefix_for_flow(flow_type, lab_id)
        web_url = f"{base_url}/{web_prefix}/{lab_id}/web/{port}/"
        lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace("${webTestUrl}", web_url)
        lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(
            "${clientTestUrl}",
            f"{base_url}/{web_prefix}/{lab_id}/web/{client_port}/"
        )

        logger.debug('start_lab output_result: %s', lab_session.success_start_lab_output)

        db.session.commit()
        logger.info('start_lab state update complete for lab=%s user=%s', lab.name, user_linux_name)
    
        # Apply parameter file modifications if specified
        if lab.lab_parameters and lab_session.student_folder:
            apply_parameter_file_modifications(lab, lab_session.student_folder, user_linux_name, port, client_port, user.email, lab_session)
        
        # # Execute build command if specified
        # if lab.build_command and lab_session.student_folder:
        #     execute_build_command(user_linux_name, lab.build_command, lab_session.student_folder)
        
        # Execute run commands if specified
        logger.info('start_lab student_folder=%s run_commands=%s user=%s', lab_session.student_folder, lab.run_commands_list, user_linux_name)
        if lab.run_commands_list and lab_session.student_folder:
            # For qua từng command trong list
            for command in lab.run_commands_list:
                # Thay thế tất cả parameters với random values
                logger.info('start_lab raw command: %s user=%s', command, user_linux_name)
                replaced_command = replace_lab_parameters(lab, command, user)
                logger.info('start_lab executing command: %s user=%s', replaced_command, user_linux_name)
                command_ok = execute_run_command(user_linux_name, replaced_command, lab_session.student_folder, False, flow_type, lab_id, port, client_port, db_port)
                logger.info('start_lab command_ok=%s for %s user=%s', command_ok, replaced_command, user_linux_name)
                if not command_ok:
                    raise RuntimeError(f"Failed to execute run command: {replaced_command}")
            if flow_type == FLOW_TYPE_CUSTOM:
                wait_for_custom_lab_ready(user_linux_name)

        logger.info('start_lab success: lab_id=%s, lab_session_id=%s, user_id=%s, duration=%.3fs', lab_id, lab_session.id, user_id, (datetime.utcnow() - start_ts).total_seconds())
        return jsonify({
            'message': 'Lab started successfully',
            'lab_id': lab_id,
            'lab_session_id': lab_session.id,
            'flow_type': flow_type,
            'redirect_url': f'/lab/{lab.id}/{lab_session.id}/terminal?flow_type={flow_type}',
            'web_url': web_url,
            'web_proxy_url': f'/{web_prefix}/{lab_id}/web/{port}/',
            'lab_random_string': lab_random_string,
            'success_start_lab_output': lab_session.success_start_lab_output
        })
    except Exception as e:
        db.session.rollback()
        logger.exception('Error starting lab: %s', e)
        if FUNCTION_ERRORS:
            FUNCTION_ERRORS.labels(function='start_lab').inc()
        return jsonify({'error': 'Failed to start lab'}), 500

def _run_lab_commands(lab_id, lab_session_id):
    """Internal helper for running lab commands.

    This supports both the new URL format (/api/lab/<lab_id>/<lab_session_id>/...)
    and the legacy URL format (/api/lab/<lab_session_id>/...).
    """
    run_start = datetime.utcnow()
    logger.info('run_lab_commands called: lab_id=%s, lab_session_id=%s, user_id=%s', lab_id, lab_session_id, session['user']['id'])

    user_id = session['user']['id']

    # Get lab session and verify ownership
    lab_session = LabSession.query.get_or_404(lab_session_id)
    if lab_session.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Ensure the lab_id in the URL matches the lab session
    if lab_session.lab_id != lab_id:
        return jsonify({'error': 'Lab ID mismatch'}), 400

    lab = lab_session.lab
    user = User.query.filter_by(id=user_id).first()
    user_linux_name = get_student_username(user.email)
    student_id = user_linux_name.replace("student_", "")
    flow_type = _normalize_flow_type(getattr(lab, 'flow_type', None))
    logger.info('run_lab_commands PREPARE FOR LABS %s user=%s', lab.name, user_linux_name)
    if not lab:
        logger.warning('run_lab_commands lab not found lab_id=%s user=%s', lab_id, user_linux_name)
        return jsonify({'error': 'Lab not found'}), 404

    enrollment = Enrollment.query.filter_by(
        user_id=user_id, course_id=lab.course_id, status='active'
    ).first()

    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403

    # Get or create lab session
    if flow_type == FLOW_TYPE_LABTAINER:
        if not clone_lab_folder(user_id, lab_id):
            logger.error('Failed to clone lab folder for user %s, lab %s', user_id, lab_id)
            return jsonify({'error': 'Failed to setup lab environment. Please check if the lab template exists.'}), 500

    # Update session status
    if lab_session.status == 'not_started':
        lab_session.status = 'in_progress'
        lab_session.started_at = datetime.utcnow()

    lab_session.last_accessed = datetime.utcnow()
    lab_random_string = generate_lab_start_random_string()
    cache_lab_start_random_string(student_id, lab_random_string)
    port = reserve_port(8000, 10000, user_linux_name)
    if not port:
        raise ValueError("No available port for lab!")
    client_port = reserve_port(50000, 60000, user_linux_name)
    if not client_port:
        raise ValueError("No available port for lab!")

    # Store ports in lab session
    lab_session.web_port = port
    lab_session.client_port = client_port

    logger.info('run_lab_commands web_port=%s client_port=%s user=%s', port, client_port, user_linux_name)
    output_template = lab.output_result or ""
    lab_session.success_start_lab_output = output_template.replace(WEB_TEST_PORT_PARAM, str(port))
    lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(CLIENT_TEST_PORT_PARAM, str(client_port))
    lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(STUDENT_ID_LAB_PARAMETER, user_linux_name.replace("student_",""))
    lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(STUDENT_NAME_LAB_PARAMETER, user_linux_name)
    lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(LAB_RANDOM_STRING_PARAM, lab_random_string)

    flow_type = _normalize_flow_type(getattr(lab, 'flow_type', None))
    base_url = request.host_url.rstrip('/')
    web_prefix = _web_prefix_for_flow(flow_type, lab_id)
    web_url = f"{base_url}/{web_prefix}/{lab_id}/web/{port}/"
    lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace("${webTestUrl}", web_url)
    lab_session.success_start_lab_output = lab_session.success_start_lab_output.replace(
        "${clientTestUrl}",
        f"{base_url}/{web_prefix}/{lab_id}/web/{client_port}/"
    )
    logger.debug('run_lab_commands expected output result: %s', lab_session.success_start_lab_output)
    try:
        db.session.commit()
        logger.info('run_lab_commands state commit complete for lab=%s user=%s', lab.name, user_linux_name)

        # Apply parameter file modifications if specified
        if lab.lab_parameters and lab_session.student_folder:
            apply_parameter_file_modifications(lab, lab_session.student_folder, user_linux_name, port, client_port, user.email, lab_session)

        # # Execute build command if specified
        # if lab.build_command and lab_session.student_folder:
        #     execute_build_command(user_linux_name, lab.build_command, lab_session.student_folder)

        # Execute run commands if specified
        logger.info(f"Student folder: {lab_session.student_folder}")
        logger.info(f"Raw command list: {lab.run_commands_list}")
        if lab.run_commands_list and lab_session.student_folder:
            # For qua từng command trong list
            for command in lab.run_commands_list:
                # Thay thế tất cả parameters với random values
                logger.info(f"Raw run command: {command}")
                replaced_command = replace_lab_parameters(lab, command, user)
                logger.info(f"Executing run command: {replaced_command}")
                command_ok = execute_run_command(user_linux_name, replaced_command, lab_session.student_folder, True, flow_type, lab_id, lab_session.web_port, lab_session.client_port, lab_session.db_port)
                if not command_ok:
                    raise RuntimeError(f"Failed to execute run command: {replaced_command}")
            if flow_type == FLOW_TYPE_CUSTOM:
                wait_for_custom_lab_ready(user_linux_name)

        logger.info('run_lab_commands send start and ready event user=%s', user_linux_name)  
        socketio.emit('terminal_ready', {'status': 'ready'})
        labParams = LabParameter.query.filter_by(lab_id=lab_session.lab_id)
        start_command_param = labParams.filter_by(
                parameter_name='${dockerExecCommand}'
        ).first()
        linux_username = get_student_username(user.email)
        student_id = linux_username.replace("student_", "")
        working_dir = f'/home/{linux_username}' or '/tmp'
        values = json.loads(start_command_param.parameter_values) if start_command_param else None
        start_command = values[0] if values else None
        needToConnectContainer = True if start_command else False
        if not start_command:
            start_command = f'cd {working_dir} && newgrp {linux_username}'
        else:
            containerName = start_command.replace(STUDENT_ID_LAB_PARAMETER, student_id)
            start_command = f'sudo docker_client_shell_{containerName}'
        # Create terminal session
        latest_terminal = (
            TerminalSession.query
            .filter_by(lab_session_id=lab_session.id)
            .order_by(TerminalSession.last_activity.desc())
            .first()
        )

        terminal_session = TerminalSession(
            session_id=latest_terminal.session_id,
            user_id=user_id,
            lab_session_id=lab_session_id,
            current_directory=lab_session.student_folder or '/tmp'
        )    
        handle_linux_start_terminal_console('/tmp', user_linux_name, start_command, latest_terminal.session_id, lab_session, terminal_session, needToConnectContainer)

        logger.info('run_lab_commands success: lab_id=%s lab_session_id=%s user_id=%s duration=%.3fs', lab_id, lab_session_id, user_id, (datetime.utcnow() - run_start).total_seconds())
        return jsonify({
            'message': 'Lab commands executed successfully',
            'data': '',
            'lab_id': lab_id,
            'lab_session_id': lab_session.id,
            'flow_type': flow_type,
            'redirect_url': f'/lab/{lab_id}/{lab_session.id}/terminal?flow_type={flow_type}',
            'web_url': web_url,
            'web_proxy_url': f'/{web_prefix}/{lab_id}/web/{port}/',
            'lab_random_string': lab_random_string,
            'success_start_lab_output': lab_session.success_start_lab_output
        })
    except Exception as e:
        logger.exception('Error running lab commands for lab_id=%s lab_session_id=%s user_id=%s: %s', lab_id, lab_session_id, user_id, e)
        if FUNCTION_ERRORS:
            FUNCTION_ERRORS.labels(function='_run_lab_commands').inc()
        return jsonify({'error': str(e)}), 500    


@app.route('/api/lab/<int:lab_id>/<int:lab_session_id>/run-commands', methods=['POST'])
@login_required
def run_lab_commands(lab_id, lab_session_id):
    return _run_lab_commands(lab_id, lab_session_id)


@app.route('/api/lab/<int:lab_session_id>/run-commands', methods=['POST'])
@login_required
def run_lab_commands_legacy(lab_session_id):
    lab_session = LabSession.query.get_or_404(lab_session_id)
    return _run_lab_commands(lab_session.lab_id, lab_session_id)

def apply_parameter_file_modifications(lab, student_folder, user_linux_name, port, client_port, email, lab_session):
    """
    Modify files with parameter values when file_path is specified
    and rename file if file_path contains STUDENT_NAME_LAB_PARAMETER
    """
    function_start = datetime.utcnow()
    logger.info('apply_parameter_file_modifications called: lab_id=%s user_linux_name=%s', getattr(lab, 'id', None), user_linux_name)
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
    rename_files_if_contains(student_folder, user_linux_name)

    rename_files_in_matching_folders(student_folder,"dockerfiles", user_linux_name)
    rename_files_in_matching_folders(student_folder,"web-server", user_linux_name)
    rename_files_in_matching_folders(student_folder,"client", user_linux_name)
    rename_files_in_matching_folders(student_folder,"ftp", user_linux_name)
    # First pass: determine random values for all parameters
    db_port = reserve_port(3000, 5000, user_linux_name)
    if not db_port:
        raise ValueError("No available port for lab!")
    lab_session.db_port = db_port
    for param in lab.lab_parameters:
        if param.values_list:
            value = random.choice(param.values_list)
            value = value.replace(STUDENT_NAME_LAB_PARAMETER, user_linux_name)
            value = value.replace("${email}", email)
            value = value.replace(STUDENT_ID_LAB_PARAMETER, user_linux_name.replace("student_", ""))
            value = value.replace(WEB_TEST_PORT_PARAM, str(port))
            value = value.replace(DB_TEST_PORT_PARAM, str(db_port))
            value = value.replace(CLIENT_TEST_PORT_PARAM, str(client_port))
            value = value.replace("${randomKey}", get_cached_lab_start_random_string(user_linux_name.replace("student_", "")))
            if "${dockerExecCommand}" in param.parameter_name:
                create_student_docker(
                    user_linux_name,
                    user_linux_name,
                    value,
                    get_target_node_for_lab(lab)
                )
                continue
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
                import re    
                pattern = rf"{re.escape(LAB_SUB_NETWORK_IP_PREFIX)}_(\d+)"
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
            ).replace(
                STUDENT_ID_LAB_PARAMETER, user_linux_name.replace("student_", "")
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
                logger.info('Renamed file: %s -> %s', original_file_path, final_file_path)
            else:
                logger.warning('Cannot rename, file not found: %s', original_file_path)

        # đọc file sau khi rename (final_file_path)
        if not os.path.exists(final_file_path):
            logger.warning('File not found for parameter modification: %s', final_file_path)
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

            logger.info('Modified file: %s', final_file_path)
            logger.debug('Replacements: %s', parameter_replacements)

        except Exception as e:
            logger.exception('Error modifying file %s: %s', final_file_path, e)
            if FUNCTION_ERRORS:
                FUNCTION_ERRORS.labels(function='apply_parameter_file_modifications').inc()

    logger.info('apply_parameter_file_modifications completed: lab_id=%s user_linux_name=%s duration=%.3fs', getattr(lab, 'id', None), user_linux_name, (datetime.utcnow() - function_start).total_seconds())


def reserve_port(range_start, range_end, username=None):
    """Reserve an available port in the given range and mark username as owner"""
    port = Port.query.filter(
        Port.port_number.between(range_start, range_end),
        Port.is_used == False
    ).with_for_update().first()
    if port:
        logger.info('Reserving port %s for user %s', port.port_number, username)
        port.is_used = True
        port.used_by = username
        db.session.commit()
        return port.port_number
    logger.warning('No free port found in range %s-%s for user %s', range_start, range_end, username)
    return None

def release_port(port_number=None, username=None):
    """Release port(s) by number or username"""
    if port_number is not None:
        port = Port.query.filter_by(port_number=port_number).first()
        if port and port.is_used:
            logger.info('Releasing port %s (was used by %s)', port_number, port.used_by)
            port.is_used = False
            port.used_by = None
            db.session.commit()
            logger.info('Successfully released port %s', port_number)
            return True
        logger.warning('Port %s not found or not in use', port_number)
        return False

    if username:
        normalized = username
        if not normalized.startswith('student_'):
            normalized = f'student_{normalized}'

        logger.info('Looking for ports used by %s or %s', username, normalized)
        ports = Port.query.filter(
            (Port.used_by == normalized) |
            (Port.used_by == username)
        ).all()
        logger.info('Found %s ports for user %s', len(ports), username)
        released = 0
        for port in ports:
            if port.is_used:
                logger.info('Releasing port %s (used by %s)', port.port_number, port.used_by)
                port.is_used = False
                port.used_by = None
                released += 1
        if released > 0:
            db.session.commit()
            logger.info('Successfully released %s ports for user %s', released, username)
        else:
            logger.info('No ports to release for user %s', username)
        return released

    return 0

def release_ports_by_user(username):
    """Alias helper to release all ports used by username"""
    return release_port(username=username)


def get_free_port(start=8000, end=8999):
    for port in range(start, end + 1):
        cmd = f"ss -tuln | grep -q ':{port} '"
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode != 0:   # grep không tìm thấy → port rảnh
            return port
    
    return None            
def rename_files_if_contains(folder_path, user_linux_name):
    # Kiểm tra folder tồn tại
    if not os.path.exists(folder_path):
        logger.warning('Folder không tồn tại: %s', folder_path)
        return

    # Lấy danh sách file trong folder
    for file_name in os.listdir(folder_path):
        old_file_path = os.path.join(folder_path, file_name)

        # Chỉ xử lý file (không đổi tên folder con)
        if os.path.isfile(old_file_path) and (STUDENT_NAME_LAB_PARAMETER in file_name or STUDENT_ID_LAB_PARAMETER in file_name):
            new_file_name = file_name.replace(STUDENT_NAME_LAB_PARAMETER, user_linux_name)
            new_file_name = file_name.replace(STUDENT_ID_LAB_PARAMETER, user_linux_name.replace("student_", ""))
            new_file_path = os.path.join(folder_path, new_file_name)

            os.rename(old_file_path, new_file_path)
            logger.info(f"✔ Đổi: {file_name} → {new_file_name}")

def rename_files_in_matching_folders(folder_path, search_text, replace_text):
    logger.debug('PARAM FILE NAME %s', search_text)
    logger.debug('PARAM FILE NAME VALUE %s', replace_text)

    # Kiểm tra folder gốc
    if not os.path.isdir(folder_path):
        logger.info(f"Folder không tồn tại: {folder_path}")
        return

    # === 1) RENAME FILES TRONG CÁC FOLDER KHỚP SEARCH TEXT ===
    for entry in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, entry)

        if os.path.isdir(subfolder_path) and search_text in entry:
            logger.info('Found folder: %s', entry)

            for filename in os.listdir(subfolder_path):
                old_file_path = os.path.join(subfolder_path, filename)

                if os.path.isfile(old_file_path):
                    new_filename = filename

                    # Thay thế tên sinh viên hoặc ID
                    if STUDENT_NAME_LAB_PARAMETER in filename:
                        new_filename = new_filename.replace(STUDENT_NAME_LAB_PARAMETER, replace_text)

                    if STUDENT_ID_LAB_PARAMETER in filename:
                        new_filename = new_filename.replace(
                            STUDENT_ID_LAB_PARAMETER,
                            replace_text.replace("student_", "")
                        )

                    # Nếu tên mới khác tên cũ → rename
                    if new_filename != filename:
                        new_file_path = os.path.join(subfolder_path, new_filename)

                        try:
                            os.rename(old_file_path, new_file_path)
                            logger.info('Renamed file in subfolder: %s -> %s', filename, new_filename)
                        except Exception as e:
                            logger.error('Rename error %s: %s', filename, e)

    # === 2) RENAME CHÍNH CÁC FOLDER KHỚP SEARCH TEXT ===
    for entry in os.listdir(folder_path):
        old_folder_path = os.path.join(folder_path, entry)

        if os.path.isdir(old_folder_path) and search_text in entry:
            new_folder_name = entry

            if STUDENT_NAME_LAB_PARAMETER in entry:
                new_folder_name = new_folder_name.replace(STUDENT_NAME_LAB_PARAMETER, replace_text)

            if STUDENT_ID_LAB_PARAMETER in entry:
                new_folder_name = new_folder_name.replace(
                    STUDENT_ID_LAB_PARAMETER,
                    replace_text.replace("student_", "")
                )

            new_folder_path = os.path.join(folder_path, new_folder_name)

            # Chỉ rename khi có thay đổi
            if new_folder_name != entry:
                try:
                    os.rename(old_folder_path, new_folder_path)
                    logger.info('Folder rename: %s -> %s', entry, new_folder_name)
                except Exception as e:
                    logger.error('Folder rename error %s: %s', entry, e)

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
    logger.debug('STUDENT_ID = %s', user_id)
    replaced_command = command.replace("${email}", user.email)
    logger.debug('Initial replaced command: %s', replaced_command)
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
        random_value = random_value.replace(STUDENT_ID_LAB_PARAMETER, user_id)

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
            import re   
            pattern = rf"{re.escape(LAB_SUB_NETWORK_IP_PREFIX)}_(\d+)"
            # Replace từng match
            def replacer(match):
                index = int(match.group(1))
                return f"{network.subnet_ip_base}{index}"
            random_value = re.sub(pattern, replacer, random_value)      
        # Replace tất cả occurrences của parameter name = parameter value
        replaced_command = replaced_command.replace(parameter_name, str(random_value))
        
        logger.debug('Replaced %s with %s for user=%s', parameter_name, random_value, username)
    
    return replaced_command

def wait_for_custom_lab_ready(user_linux_name, timeout=600, interval=10):
    """Wait until all Docker services for this student report Running."""
    import time

    safe_user_linux_name = ensure_safe_identifier(user_linux_name, 'linux username')
    student_id = safe_user_linux_name.replace("student_", "")
    deadline = time.time() + timeout
    last_status = "No matching Docker service state found yet"

    while time.time() < deadline:
        service_result = subprocess.run(
            ['docker', 'service', 'ls', '--format', '{{.Name}}'],
            capture_output=True,
            text=True,
            timeout=30
        )
        logger.debug('[wait_for_custom_lab_ready] service ls stdout: %s', service_result.stdout.strip())
        if service_result.stderr.strip():
            logger.warning('[wait_for_custom_lab_ready] service ls stderr: %s', service_result.stderr.strip())

        services = [line.strip() for line in service_result.stdout.splitlines() if line.strip() and student_id in line]
        if services:
            latest_states = {}
            for service_name in services:
                safe_service_name = ensure_safe_container_name(service_name, 'service name')
                state_result = subprocess.run(
                    ['docker', 'service', 'ps', safe_service_name, '--format', '{{.CurrentState}}'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                logger.debug('[wait_for_custom_lab_ready] service ps stdout for %s: %s', service_name, state_result.stdout.strip())
                if state_result.stderr.strip():
                    logger.warning('[wait_for_custom_lab_ready] service ps stderr for %s: %s', service_name, state_result.stderr.strip())

                service_states = [line.strip() for line in state_result.stdout.splitlines() if line.strip()]
                if service_states:
                    # Use only the newest reported state (last line) for each service
                    latest_states[service_name] = service_states[-1]

            if latest_states and all(state.startswith("Running") for state in latest_states.values()):
                logger.info('Custom lab services are ready for %s: %s', student_id, latest_states)
                return True

            last_status = "; ".join(f"{srv}:{st}" for srv, st in latest_states.items()) if latest_states else "Service found but no state output yet"

        time.sleep(interval)

    raise TimeoutError(f"Custom lab services were not ready in 120 seconds: {last_status}")

def execute_run_command(user_linux_name, run_command, working_directory, clean_docker_only, flow_type=None, lab_id=None, web_port=None, client_port=None, db_port=None):
    """Execute run command when lab starts"""
    try:
        safe_user_linux_name = ensure_safe_identifier(user_linux_name, 'linux username')
        safe_working_directory = ensure_safe_working_directory(working_directory)

        # If flow_type is CUSTOM, calculate TARGET_NODE based on lab_id
        if flow_type == FLOW_TYPE_CUSTOM and lab_id is not None:
            TARGET_NODE = 98 if lab_id % 2 == 1 else 99
            # Add TARGET_NODE parameter to the run_command
            run_command = f"TARGET_NODE={TARGET_NODE} " + run_command
            student_id = safe_user_linux_name.replace("student_", "")
            cached_random_string = get_cached_lab_start_random_string(student_id) or ""

            # Expose the cached random string to run commands.
            run_command = f'RANDOM_KEY="{cached_random_string}" ' + run_command
        
        # Replace port parameters in run_command
        if web_port is not None:
            run_command = run_command.replace(WEB_TEST_PORT_PARAM, str(web_port))
        if client_port is not None:
            run_command = run_command.replace(CLIENT_TEST_PORT_PARAM, str(client_port))
        if db_port is not None:
            run_command = run_command.replace(DB_TEST_PORT_PARAM, str(db_port))
        
        # Dùng newgrp -c "<command>" để chạy command với group mới
        if flow_type == FLOW_TYPE_LABTAINER:
            logger.info("COMPOSE DOWN DOCKER CONTAINER ....")
            compose_down_cmd = f'cd {shlex.quote(safe_working_directory)} && sudo docker compose down'
            full_command = f'sg {shlex.quote(safe_user_linux_name)} -c {shlex.quote(compose_down_cmd)}'
            subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=500
            )
        cleanup_docker_resources(safe_user_linux_name, clean_docker_only)
        last_folder = os.path.basename(safe_working_directory)  # ví dụ: lab-1
        expected_cmd = f"rebuild {last_folder}"
        
        logger.info("================== expected_cmd ", expected_cmd)
        if flow_type == FLOW_TYPE_LABTAINER:
            subprocess.run([
                    'sudo', 'chmod', '-R', '777', 
                    safe_working_directory
                ], check=True, capture_output=True)
        if run_command == expected_cmd:
            result = subprocess.run(
            f"sudo chown -R student:student {shlex.quote(safe_working_directory)}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=500
        )
            full_command = f"cd ~/labtainer/labtainer-student && {run_command}"
        else:
            logger.info("CHOWN TO USER: %s", safe_user_linux_name)
            if flow_type == FLOW_TYPE_LABTAINER: 
                subprocess.run([
                'sudo', 'chown', '-R', f'{safe_user_linux_name}:{safe_user_linux_name}', safe_working_directory
                ], check=True, capture_output=True)

                user_cmd = f'cd {shlex.quote(safe_working_directory)} && sudo {run_command}'
                full_command = f'sg {shlex.quote(safe_user_linux_name)} -c {shlex.quote(user_cmd)}'
            else:
                full_command = f'cd {shlex.quote(safe_working_directory)} && {run_command}'
        logger.info("============ FULL COMMAND ========== %s", full_command)
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=500
        )
        
        logger.info(f"Run command executed. Exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Run output: {result.stdout}")
        if result.stderr:
            logger.info(f"Run errors: {result.stderr}")
        if flow_type == FLOW_TYPE_LABTAINER:    
            subprocess.run([
                    'sudo', 'chmod', '-R', '750', 
                    safe_working_directory
                ], check=True, capture_output=True)    
            subprocess.run([
                'sudo', 'chown', '-R', 'student:student', safe_working_directory
                ], check=True, capture_output=True)
            subprocess.run(
                f'cd /home/{shlex.quote(safe_user_linux_name)}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=500
            )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.info("Run command timed out")
        return False
    except Exception as e:
        logger.info(f"Error executing run command: {e}")
        return False
def get_target_node_for_lab(lab):
    """Return target node for CUSTOM labs based on lab id."""
    flow_type = _normalize_flow_type(getattr(lab, 'flow_type', None))
    if flow_type != FLOW_TYPE_CUSTOM or getattr(lab, 'id', None) is None:
        return None
    return 98 if lab.id % 2 == 1 else 99

def get_target_ip_for_node(target_node):
    """Map supported target nodes to their backend IPs."""
    return {
        98: "192.168.187.98",
        99: "192.168.187.99",
    }.get(target_node)

SCRIPT_TEMPLATE = r"""#!/bin/bash
ssh -t -i /home/hoangnth/labtainer/labs/lab-ssh-key student@${targetIp} "docker exec -it \$(docker ps -q -f name=${containerName} | head -n 1) bash"
"""
def     create_student_docker(username, studentId, containerName, target_node=None):
    username = ensure_safe_identifier(username, 'username')
    studentId = ensure_safe_identifier(studentId, 'student id')
    containerName = ensure_safe_container_name(containerName.replace(STUDENT_ID_LAB_PARAMETER, studentId))
    # 3. Tạo file script riêng
    script_path = f"/usr/local/bin/docker_client_shell_{containerName}"
    if os.path.exists(script_path):
        run(f"sudo rm -f {script_path}")

    # Đảm bảo thư mục tồn tại
    run("sudo mkdir -p /usr/local/bin")
    temp_script_file = f"/tmp/tmp_script_{containerName}.sh"
    run(f"sudo touch {temp_script_file}")
    run(f"sudo chmod 777 {temp_script_file}")
    target_ip = get_target_ip_for_node(target_node)
    script_content = SCRIPT_TEMPLATE.replace("${containerName}", containerName)
    if target_ip:
        script_content = script_content.replace("${targetIp}", target_ip)
    with open(f"{temp_script_file}", "w") as f:
        f.write(script_content)

    run(f"sudo mv {temp_script_file} {script_path}")
    run(f"sudo chmod 755 {script_path}")
    # 4. Thêm sudoers rule
    sudoers_rule = f"{username} ALL=(root) NOPASSWD: {script_path}\n"
    sudoers_path = f"/etc/sudoers.d/{username}"
    run("sudo mkdir -p /etc/sudoers.d")
    if os.path.exists(sudoers_path):
        run(f"sudo rm -f {sudoers_path}")

    temp_sudoer_file = f"/tmp/tmp_sudoers_{username}"
    run(f"sudo touch {temp_sudoer_file}")
    run(f"sudo chmod 777 {temp_sudoer_file}")
    with open(f"{temp_sudoer_file}", "w") as f:
        f.write(sudoers_rule)

    run(f"sudo mv {temp_sudoer_file} {sudoers_path}")
    run(f"sudo chown root:root {sudoers_path}")
    run(f"sudo chmod 440 {sudoers_path}")

    logger.info("\nDONE! Student created successfully:")
    logger.info(f"- Username: {username}")
    logger.info(f"- Student ID: {studentId}")
    logger.info(f"- Script: {script_path}")

def run(cmd):
    logger.info(f"--> {cmd}")
    result = subprocess.run(cmd, shell=True, check=False)
    if result.returncode != 0:
        logger.error("ERROR running: %s", cmd)
        raise ValueError("ERROR WHEN CREATE DOCKER EXEC")
def execute_build_command(user_linux_name, build_command, working_directory):
    """Execute build command in lab directory"""
    try:
        safe_user_linux_name = ensure_safe_identifier(user_linux_name, 'linux username')
        safe_working_directory = ensure_safe_working_directory(working_directory)
        build_cmd = f'cd {shlex.quote(safe_working_directory)} && sudo {build_command}'
        full_command = f'sg {shlex.quote(safe_user_linux_name)} -c {shlex.quote(build_cmd)}'
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        logger.info(f"Build command executed. Exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Build output: {result.stdout}")
        if result.stderr:
            logger.info(f"Build errors: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.info("Build command timed out")
        return False
    except Exception as e:
        logger.info(f"Error executing build command: {e}")
        return False

@app.route('/lab/<int:lab_id>/<int:lab_session_id>/terminal')
@login_required
def lab_terminal(lab_id, lab_session_id):
    """Display lab terminal interface"""
    user_id = session['user']['id']
    
    lab_session = LabSession.query.filter_by(id=lab_session_id, user_id=user_id).first()

    if not lab_session:
        flash('Lab session not found. Please start the lab first.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verify lab_id matches
    if lab_session.lab_id != lab_id:
        flash('Lab ID mismatch.', 'error')
        return redirect(url_for('dashboard'))
    
    # Update last accessed
    lab_session.last_accessed = datetime.utcnow()
    db.session.commit()
    
    return render_template('lab_terminal.html', lab_session=lab_session)

def _submit_lab(lab_id, lab_session_id):
    """Internal helper for lab submission.

    Supports both new path format (/api/lab/<lab_id>/<lab_session_id>/submit)
    and legacy format (/api/lab/<lab_session_id>/submit).
    """
    submit_start = datetime.utcnow()
    logger.info('submit_lab called: lab_id=%s, lab_session_id=%s, user_id=%s', lab_id, lab_session_id, session['user']['id'])
    if LAB_SUBMISSIONS:
        LAB_SUBMISSIONS.inc()

    user_id = session['user']['id']

    # Get lab session and verify ownership
    lab_session = LabSession.query.get_or_404(lab_session_id)
    if lab_session.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Ensure the lab_id in the URL matches the lab session
    if lab_session.lab_id != lab_id:
        return jsonify({'error': 'Lab ID mismatch'}), 400

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
        logger.info(
            f"[submit_lab] Start scoring: "
            f"lab_id={lab_id}, lab_session_id={lab_session_id}, user_id={user_id}, "
            f"num_checkpoints={lab.num_checkpoints}, received_answers={len(checkpoint_answers)}"
        )

        # Validate and score checkpoints
        results = validate_checkpoints_with_cached_random(lab, lab_session, checkpoint_answers, user)
        
        # Calculate score based on points from each checkpoint
        total_points = 0
        earned_points = 0
        passed_checkpoints = 0
        
        for result in results:
            total_points += result['points']
            if result['passed']:
                earned_points += result['points']
                passed_checkpoints += 1
            logger.info(
                f"[submit_lab] Checkpoint result: checkpoint={result.get('checkpoint')}, "
                f"passed={result.get('passed')}, earned_points={result.get('earned_points')}, "
                f"max_points={result.get('points')}, message={result.get('message')}"
            )
        
        # Calculate final score (scale to max_score)
        if total_points > 0:
            score = int((earned_points / total_points) * lab.max_score)
        else:
            score = 0
        
        # Determine if passed based on minimum score
        minimum_score = lab.minimum_score or 0
        passed = score >= minimum_score
        status = 'completed' if passed else 'failed'
        logger.info(
            f"[submit_lab] Final score: earned_points={earned_points}, total_points={total_points}, "
            f"score={score}, max_score={lab.max_score}, minimum_score={minimum_score}, "
            f"passed={passed}, status={status}"
        )
        
        # Update lab session
        lab_session.checkpoint_answers = json.dumps(checkpoint_answers)
        lab_session.checkpoint_results = json.dumps(results)
        lab_session.score = score
        lab_session.status = status
        lab_session.completed_at = datetime.utcnow()
        lab_session.submission_notes = data.get('notes', '')
        
        db.session.commit()
        logger.info('[submit_lab] Saved lab session result: lab_session_id=%s, status=%s, score=%s', lab_session.id, lab_session.status, lab_session.score)
        
        # Release ports
        if lab_session.web_port:
            release_port(lab_session.web_port)
        if lab_session.client_port:
            release_port(lab_session.client_port)
        if lab_session.db_port:
            release_port(lab_session.db_port)
        
        logger.info('submit_lab success: lab_id=%s lab_session_id=%s user_id=%s duration=%.3fs score=%s/%s passed=%s', lab_id, lab_session_id, user_id, (datetime.utcnow() - submit_start).total_seconds(), score, lab.max_score, passed)
        
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
        logger.exception('Error submitting lab lab_id=%s lab_session_id=%s user_id=%s: %s', lab_id, lab_session_id, user_id, e)
        if FUNCTION_ERRORS:
            FUNCTION_ERRORS.labels(function='_submit_lab').inc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/lab/<int:lab_id>/<int:lab_session_id>/submit', methods=['POST'])
@login_required
def submit_lab(lab_id, lab_session_id):
    return _submit_lab(lab_id, lab_session_id)


@app.route('/api/lab/<int:lab_session_id>/submit', methods=['POST'])
@login_required
def submit_lab_legacy(lab_session_id):
    lab_session = LabSession.query.get_or_404(lab_session_id)
    return _submit_lab(lab_session.lab_id, lab_session_id)


@app.route('/api/ports', methods=['GET'])
@login_required
def get_ports():
    """Get all ports and their status"""
    ports = Port.query.order_by(Port.port_number).all()
    return jsonify([{
        'id': p.id,
        'port_number': p.port_number,
        'is_used': p.is_used,
        'used_by': p.used_by
    } for p in ports])

@app.route('/api/ports/reserve', methods=['POST'])
@login_required
def reserve_port_api():
    """Reserve an available port in the given range"""
    data = request.json
    range_start = data.get('range_start', 8000)
    range_end = data.get('range_end', 10000)
    port = reserve_port(range_start, range_end)
    if port:
        return jsonify({'port_number': port})
    return jsonify({'error': 'No available port'}), 400


@app.route('/api/ports/release/<int:port_number>', methods=['POST'])
@login_required
def release_port_api(port_number):
    """Release a port"""
    release_port(port_number)
    return jsonify({'message': 'Port released'})


@app.route('/api/ports/user/<string:username>', methods=['GET'])
@login_required
def get_ports_by_user(username):
    """Get all ports currently reserved by a username"""
    normalized = username
    if not normalized.startswith('student_'):
        normalized = f'student_{normalized}'

    ports = Port.query.filter_by(used_by=normalized).order_by(Port.port_number).all()
    return jsonify([{
        'id': p.id,
        'port_number': p.port_number,
        'is_used': p.is_used,
        'used_by': p.used_by
    } for p in ports])


@app.route('/api/ports/release-by-user/<string:username>', methods=['POST'])
@login_required
def release_ports_by_user_api(username):
    """Release all ports assigned to a username"""
    released = release_ports_by_user(username)
    return jsonify({'message': f'Released {released} ports for {username}', 'released_count': released})


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
            try:
                from zoneinfo import ZoneInfo
            except ImportError:
                from backports.zoneinfo import ZoneInfo
            import hashlib

            user_email = user.email  # hoặc gán chuỗi trực tiếp
            username = get_student_username(user_email)
            # Lấy thời gian theo Asia/Ho_Chi_Minh và format giống hệt bash: DDMMYYYY
            dt = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
            date_str = dt.strftime("%d%m%Y")

            # Ghép chuỗi giống hệt bash
            expected_answer = expected_answer.replace(STUDENT_NAME_LAB_PARAMETER, username)
            logger.info("========== ", date_str, user_email, expected_answer)
            flag_input = f"{date_str}_{user_email}_{expected_answer}"

            # Hash SHA1 giống bash
            flag_hash = hashlib.sha1(flag_input.encode()).hexdigest()

            lab_session.generated_flag = f"FLAG{{{flag_hash}}}"
            logger.info(f"Generated flag for lab session: {lab_session.generated_flag}")

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
            logger.info("STUDENT VALUE ", student_value)
            logger.info("EXPECTED VALUE ", expected_value)
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


def validate_checkpoints_with_cached_random(lab, lab_session, checkpoint_answers, user):
    """
    Validate checkpoint answers and require a cached random string for auto flags.

    Expected submit format for auto-flag checkpoints:
    - FLAG{...}::random_string
    - FLAG{...}|random_string
    - FLAG{...}:random_string
    - FLAG{...}random_string
    """
    try:
        rules = json.loads(lab.checkpoint_rules) if lab.checkpoint_rules else []
    except Exception:
        rules = []

    results = []
    student_id = get_student_username(user.email).replace("student_", "")
    cached_random_string = get_cached_lab_start_random_string(student_id)
    logger.info(
        f"[validate_checkpoints] Start: lab_id={lab.id}, lab_session_id={lab_session.id}, "
        f"student_id={student_id}, answers={len(checkpoint_answers)}, "
        f"cached_random_exists={bool(cached_random_string)}"
    )

    for i, answer in enumerate(checkpoint_answers):
        if i < len(rules):
            rule = rules[i]
            decode_method = rule.get('decode_method', 'plain')
            expected_answer = rule.get('expected_answer', '')
            case_sensitive = rule.get('case_sensitive', False)
            points = rule.get('points', 10)
            use_auto_flag = rule.get('use_auto_flag', False)
        else:
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
        logger.info(
            f"[validate_checkpoints] Checkpoint {i + 1}: "
            f"decode_method={decode_method}, case_sensitive={case_sensitive}, "
            f"points={points}, use_auto_flag={use_auto_flag}"
        )
        logger.info(f"[validate_checkpoints] Checkpoint {i + 1}: raw_answer={answer}")

        try:
            decoded = decode_checkpoint_answer(answer, decode_method)
            result['decoded_answer'] = decoded
            logger.info(f"[validate_checkpoints] Checkpoint {i + 1}: decoded_answer={decoded}")

            generated_flag, resolved_expected_answer = build_generated_flag(expected_answer, user)
            lab_session.generated_flag = generated_flag
            logger.info(
                f"[validate_checkpoints] Checkpoint {i + 1}: "
                f"generated_flag={generated_flag}, resolved_expected_answer={resolved_expected_answer}"
            )

            expected_value = str(resolved_expected_answer).strip()
            student_value = str(decoded).strip()
            submitted_main_value, submitted_random_string = split_submitted_flag_and_random(student_value)
            result['submitted_random_string'] = submitted_random_string

            if not cached_random_string:
                result['message'] = f'Incorrect (0/{points} points)'
                logger.info(f"[validate_checkpoints] Checkpoint {i + 1}: missing cached random string")
                results.append(result)
                continue

            cached_random_value = str(cached_random_string).strip()

            if use_auto_flag:
                submitted_flag = submitted_main_value
                result['submitted_flag'] = submitted_flag
                result['expected_answer'] = '[Auto-generated Flag + Random String]'
                logger.info(
                    f"[validate_checkpoints] Checkpoint {i + 1}: auto_flag_mode, "
                    f"submitted_flag={submitted_flag}, submitted_random_present={bool(submitted_random_string)}"
                )

                expected_flag_value = str(lab_session.generated_flag or expected_value).strip()
                submitted_flag_value = str(submitted_flag).strip()
                submitted_random_value = str(submitted_random_string).strip()

                if not case_sensitive:
                    expected_flag_value = expected_flag_value.lower()
                    cached_random_value = cached_random_value.lower()
                    submitted_flag_value = submitted_flag_value.lower()
                    submitted_random_value = submitted_random_value.lower()

                is_correct = (
                    submitted_flag_value == expected_flag_value and
                    submitted_random_value == cached_random_value
                )
                logger.info(
                    f"[validate_checkpoints] Checkpoint {i + 1}: auto_flag_compare, "
                    f"flag_match={submitted_flag_value == expected_flag_value}, "
                    f"random_match={submitted_random_value == cached_random_value}, "
                    f"is_correct={is_correct}"
                )
            else:
                submitted_answer_value = str(submitted_main_value).strip()
                submitted_random_value = str(submitted_random_string).strip()

                if not case_sensitive:
                    submitted_answer_value = submitted_answer_value.lower()
                    expected_value = expected_value.lower()
                    cached_random_value = cached_random_value.lower()
                    submitted_random_value = submitted_random_value.lower()

                is_correct = (
                    submitted_answer_value == expected_value and
                    submitted_random_value == cached_random_value
                )
                logger.info(
                    f"[validate_checkpoints] Checkpoint {i + 1}: plain_compare, "
                    f"student_value={submitted_answer_value}, expected_value={expected_value}, "
                    f"random_match={submitted_random_value == cached_random_value}, "
                    f"is_correct={is_correct}"
                )

            if is_correct:
                result['passed'] = True
                result['earned_points'] = points
                result['message'] = f'Correct! (+{points} points)'
            else:
                result['message'] = f'Incorrect (0/{points} points)'
            logger.info(
                f"[validate_checkpoints] Checkpoint {i + 1}: final_result, "
                f"passed={result['passed']}, earned_points={result['earned_points']}, "
                f"message={result['message']}"
            )
        except Exception as e:
            result['message'] = f'Decode error: {str(e)}'
            logger.info(f"[validate_checkpoints] Checkpoint {i + 1}: exception={e}")

        results.append(result)

    logger.info(f"[validate_checkpoints] Finished: total_results={len(results)}")
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
    logger.info(f"Client connected: {session_id}")

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    
    if 'user' not in session:
        socketio.emit('terminal_error', {'error': 'Not authenticated'})
        return
    
    user_id = session['user']['id']

    # Get user object
    user = db.session.get(User, user_id)
    if not user:
        socketio.emit('terminal_error', {'error': 'User not found'})
        return
    user_name = get_student_username(user.email)
    logger.info(f"Client disconnected: {session_id}")
    logger.info("=============== START CLEAN UP DOCKER OF " , user_name)
    cleanup_docker_resources(user_name, False)
    logger.info("=============== END CLEAN UP DOCKER OF " , user_name)

    # Clean up terminal session and kill pty process
    if session_id in active_terminals:
        terminal_info = active_terminals[session_id]
        
        # Kill pty process if exists
        if 'pid' in terminal_info and terminal_info['pid']:
            try:
                os.kill(terminal_info['pid'], signal.SIGTERM)
                logger.info(f"Killed pty process: {terminal_info['pid']}")
            except ProcessLookupError:
                logger.info(f"Process {terminal_info['pid']} already dead")
            except Exception as e:
                logger.info(f"Error killing process: {e}")
        
        # Close pty file descriptor
        if 'pty_fd' in terminal_info and terminal_info['pty_fd']:
            try:
                os.close(terminal_info['pty_fd'])
                logger.info(f"Closed pty fd: {terminal_info['pty_fd']}")
            except Exception as e:
                logger.info(f"Error closing pty fd: {e}")
        
        try:
            terminal_session = db.session.get(TerminalSession, terminal_info['terminal_session_id'])
            if terminal_session:
                terminal_session.is_active = False
                db.session.commit()
        except Exception as e:
            logger.info(f"Warning: Could not update terminal session on disconnect: {e}")
            db.session.rollback()
        finally:
            del active_terminals[session_id]
import subprocess

def cleanup_docker_resources(student_name, clean_docker_only):
    try:
        student_name = ensure_safe_identifier(student_name, 'student name')
        student_key = student_name.replace("student_", "")

        # Remove containers
        try:
            containers_result = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            containers = [
                line.strip() for line in containers_result.stdout.splitlines()
                if line.strip() and student_key in line
            ]

            if containers:
                for c in containers:
                    safe_container = ensure_safe_container_name(c)
                    logger.info(f"Removing container: {c}")
                    subprocess.run(['docker', 'rm', '-f', safe_container], capture_output=True, timeout=30)
            else:
                logger.info(f"No containers found for {student_key}")
        except Exception as e:
            logger.info(f"Error removing containers: {e}")

        # Remove networks
        try:
            networks_result = subprocess.run(
                ['docker', 'network', 'ls', '--format', '{{.Name}}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            networks = [
                line.strip() for line in networks_result.stdout.splitlines()
                if line.strip() and student_key in line
            ]

            if networks:
                for n in networks:
                    safe_network = ensure_safe_container_name(n, 'network name')
                    logger.info(f"Removing network: {n}")
                    subprocess.run(['docker', 'network', 'rm', safe_network], capture_output=True, timeout=30)
            else:
                logger.info(f"No networks found for {student_key}")
        except Exception as e:
            logger.info(f"Error removing networks: {e}")

        # Remove services
        try:
            logger.info(f"Removing services for {student_key}")
            services_result = subprocess.run(
                ['docker', 'service', 'ls', '--filter', f'name={student_key}', '--format', '{{.ID}}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            service_ids = [line.strip() for line in services_result.stdout.splitlines() if line.strip()]
            if service_ids:
                subprocess.run(['docker', 'service', 'rm', *service_ids], capture_output=True, text=True, timeout=30)
        except Exception as e:
            logger.info(f"Error removing services: {e}")

        # Release ports held by this user (if any)
        if not clean_docker_only:
            try:
                student_username = student_name
                if not student_username.startswith('student_'):
                    student_username = f'student_{student_username}'
                released = release_ports_by_user(student_username)
                logger.info(f"Released {released} ports for user {student_username}")
            except Exception as e:
                logger.info(f"Error releasing ports: {e}")

    except Exception as e:
        logger.info(f"Error when cleaning docker resources: {e}")
         

@socketio.on('start_terminal')
def handle_start_terminal(data):
    session_id = request.sid
    lab_id = data.get('lab_id')
    lab_session_id = data.get('lab_session_id')
    
    if 'user' not in session:
        socketio.emit('terminal_error', {'error': 'Not authenticated'})
        return
    
    user_id = session['user']['id']
    
    # Verify lab session
    lab_session = LabSession.query.filter_by(id=lab_session_id, user_id=user_id).first()
    if not lab_session:
        socketio.emit('terminal_error', {'error': 'Lab session not found'})
        return
    
    # Verify lab_id matches
    if lab_session.lab_id != lab_id:
        socketio.emit('terminal_error', {'error': 'Lab ID mismatch'})
        return
    
    # Get user object
    user = db.session.get(User, user_id)
    if not user:
        socketio.emit('terminal_error', {'error': 'User not found'})
        return
    labParams = LabParameter.query.filter_by(lab_id=lab_session.lab_id)
    start_command_param = labParams.filter_by(
            parameter_name='${dockerExecCommand}'
    ).first()
    linux_username = get_student_username(user.email)
    student_id = linux_username.replace("student_", "")
    working_dir = f'/home/{linux_username}' or '/tmp'
    values = json.loads(start_command_param.parameter_values) if start_command_param else None
    start_command = values[0] if values else None
    needToConnectContainer = True if start_command else False
    if not start_command:
        start_command = f'cd {working_dir} && newgrp {linux_username}'
    else:
        containerName = start_command.replace(STUDENT_ID_LAB_PARAMETER, student_id)
        start_command = f'sudo docker_client_shell_{containerName}'
    # Create terminal session
    terminal_session = TerminalSession(
        session_id=session_id,
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
        
        socketio.emit('terminal_output', {'data': welcome_msg})
        socketio.emit('terminal_ready', {'status': 'ready'})
    else:
        # Linux: Use pty for real bash session with user isolation
        handle_linux_start_terminal_console(working_dir, linux_username, start_command, session_id, lab_session, terminal_session, needToConnectContainer)
def handle_linux_start_terminal_console(working_dir, linux_username, start_command, session_id, lab_session, terminal_session, needToConnectContainer):
    try:
            
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
                if needToConnectContainer:
                    os.execvp('sudo', [
                            'sudo',
                            '-u', linux_username,
                            '/bin/bash',
                            '-c',
                            start_command
                        ])
            except Exception as e:
                    logger.info(f"Child process error: {e}", flush=True)
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
                socketio.emit('terminal_ready', {'status': 'ready'})
                
    except Exception as e:
        error_msg = f"Failed to start terminal: {e}"
        logger.info(error_msg)
        traceback.print_exc()
        socketio.emit('terminal_error', {'error': error_msg})
        return

def read_pty_output(session_id, fd):
    """Read output from pty and send to client via WebSocket"""
    logger.info(f"Started pty reader thread for session {session_id}")
    
    try:
        while session_id in active_terminals:
            try:
                # Use select to wait for data with timeout
                readable, _, _ = select.select([fd], [], [], 0.1)
                
                if readable:
                    try:
                        # Read data from pty
                        data = os.read(fd, 4096)
                        logger.info("================ DATA OUTPUT TO EMIT ", data)
                        if data:
                            # Decode and send to client
                            output = data.decode('utf-8', errors='replace')
                            socketio.emit('terminal_output', {'data': output}, room=session_id)
                            logger.info("===== EMIT OUTPUT TO CHANNEL ", session_id)
                        else:
                            # EOF - process died
                            logger.info(f"PTY EOF for session {session_id}")
                            break
                    except OSError as e:
                        if e.errno == 5:  # EIO - process terminated
                            logger.info(f"PTY process terminated for session {session_id}")
                            break
                        raise
                        
            except Exception as e:
                logger.info(f"Error reading from pty: {e}")
                break
                
    except Exception as e:
        logger.info(f"PTY reader thread error: {e}")
    finally:
        logger.info(f"PTY reader thread stopped for session {session_id}")
        socketio.emit('terminal_error', {'error': 'Terminal session ended'}, room=session_id)

def get_prompt(current_dir):
    """Get terminal prompt"""
    dir_name = os.path.basename(current_dir) if current_dir else 'unknown'
    return f"lab:{dir_name}$ "

command_buffers = {}
@socketio.on('terminal_input')
def handle_terminal_input(data):
    session_id = request.sid
    logger.info('================= INPUT DATA FROM CHANNEL ', session_id)
    input_data = data.get('data', '')
    
    if session_id not in active_terminals:
        socketio.emit('terminal_error', {'error': 'No active terminal session'})
        return
    
    terminal_info = active_terminals[session_id]
    if not terminal_info:
        logger.info("CHANNEL NOT ACTIVE")
        return
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
                logger.info("========== EXE COMMAND ", input_data.encode('utf-8'))

                os.write(pty_fd, input_data.encode('utf-8'))
                
                # Update last activity
                terminal_session_id = terminal_info['terminal_session_id']
                try:
                    terminal_session = db.session.get(TerminalSession, terminal_session_id)
                    if terminal_session:
                        terminal_session.last_activity = datetime.utcnow()
                        terminal_session.command_count = terminal_session.command_count + 1

                        if session_id not in command_buffers:
                            command_buffers[session_id] = ''
                        command_buffers[session_id] += input_data

                        # Kiểm tra Enter (\r hoặc \n)
                        if '\n' in input_data or '\r' in input_data:
                            full_command = command_buffers[session_id].replace('\r', '').replace('\n', '')
                            logger.info(f"User command: {full_command}")  # <-- ghi log hoặc lưu DB
                            command_buffers[session_id] = ''  # reset buffer    
                            command_log = CommandLog(terminal_session_id=terminal_session.id,command=full_command,is_allowed=True,blocked_reason=None)
                            db.session.add(command_log)
                        db.session.commit()
                except Exception as e:
                    logger.info(f"Warning: Could not update last activity: {e}")
                    db.session.rollback()
                    
            except Exception as e:
                logger.info(f"Error writing to pty: {e}")
                socketio.emit('terminal_error', {'error': f'Failed to write to terminal: {e}'})
        else:
            socketio.emit('terminal_error', {'error': 'Terminal not ready'})

def handle_windows_terminal_input(session_id, input_data, terminal_info):
    """Handle terminal input for Windows (command-based mode)"""
    # Get fresh database objects using IDs
    terminal_session = db.session.get(TerminalSession, terminal_info['terminal_session_id'])
    lab_session = db.session.get(LabSession, terminal_info['lab_session_id'])
    
    if not terminal_session or not lab_session:
        socketio.emit('terminal_error', {'error': 'Terminal session expired'}, room=session_id)
        return
    
    # Handle input character by character
    if input_data == '\r' or input_data == '\n':
        # Execute command
        command = terminal_info.get('command_buffer', '').strip()
        if command:
            execute_secure_command(session_id, command, terminal_session, lab_session)
        else:
            socketio.emit('terminal_output', {'data': f'\r\n{get_prompt(terminal_session.current_directory)}'}, room=session_id)
        terminal_info['command_buffer'] = ''
        
    elif input_data == '\x7f':  # Backspace
        if terminal_info.get('command_buffer', ''):
            terminal_info['command_buffer'] = terminal_info['command_buffer'][:-1]
            socketio.emit('terminal_output', {'data': '\b \b'}, room=session_id)
            
    elif input_data == '\x03':  # Ctrl+C
        terminal_info['command_buffer'] = ''
        socketio.emit('terminal_output', {'data': f'^C\r\n{get_prompt(terminal_session.current_directory)}'}, room=session_id)
        
    elif input_data and len(input_data) == 1 and ord(input_data) >= 32:  # Printable characters
        terminal_info['command_buffer'] += input_data
        socketio.emit('terminal_output', {'data': input_data}, room=session_id)
    
    # Update last activity
    try:
        terminal_session.last_activity = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        logger.info(f"Warning: Could not update last activity: {e}")
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
        
        logger.info(f"Terminal resized to {cols}x{rows} for session {session_id}")
    except Exception as e:
        logger.info(f"Error resizing terminal: {e}")

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
        socketio.emit('terminal_output', {'data': error_msg}, room=socket_session_id)
        command_log.output = error_msg
        command_log.exit_code = 1
    else:
        # Execute command
        try:
            # Handle special commands
            if command.lower() in ['clear', 'cls']:
                socketio.emit('terminal_clear', {}, room=socket_session_id)
                socketio.emit('terminal_output', {'data': get_prompt(current_dir)}, room=socket_session_id)
                command_log.output = "Terminal cleared"
                command_log.exit_code = 0
                
            elif command.lower().startswith('cd '):
                new_dir = handle_cd_command(command, current_dir, accessible_resources)
                if new_dir != current_dir:
                    terminal_session.current_directory = new_dir
                    output = f"\r\n{get_prompt(new_dir)}"
                else:
                    output = f"\r\ncd: directory not accessible or not found\r\n{get_prompt(current_dir)}"
                socketio.emit('terminal_output', {'data': output}, room=socket_session_id)
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
                socketio.emit('terminal_output', {'data': full_output}, room=socket_session_id)
                
                command_log.output = output
                command_log.exit_code = result.returncode
                
        except subprocess.TimeoutExpired:
            error_msg = f"\r\n⏰ Command timed out\r\n{get_prompt(current_dir)}"
            socketio.emit('terminal_output', {'data': error_msg}, room=socket_session_id)
            command_log.output = "Command timed out"
            command_log.exit_code = 124
            
        except Exception as e:
            error_msg = f"\r\n❌ Error: {str(e)}\r\n{get_prompt(current_dir)}"
            socketio.emit('terminal_output', {'data': error_msg}, room=socket_session_id)
            command_log.output = f"Error: {str(e)}"
            command_log.exit_code = 1
    
    # Save command log
    try:
        db.session.add(command_log)
        
        # Update terminal session stats
        terminal_session.command_count += 1
        db.session.commit()
    except Exception as e:
        logger.info(f"Warning: Could not save command log: {e}")
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
        logger.info("✅ Sample data created successfully!")
        
        # Create sample template directories
        create_sample_templates()
        
    except Exception as e:
        logger.info(f"❌ Error creating sample data: {e}")
        db.session.rollback()

def create_sample_templates():
    """Create sample lab template directories"""
    templates = [
        {
            'name': 'sql-injection-template',
            'files': {
                'README.md': '# SQL Injection Lab\n\nLearn about SQL injection vulnerabilities.\n',
                'src/app.py': '# Flask app with SQL injection vulnerability\nlogger.info("Hello World")\n',
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
        # Best-effort schema patch for older databases (no Alembic in this repo).
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'labs' in inspector.get_table_names():
                labs_cols = [col['name'] for col in inspector.get_columns('labs')]
                if 'flow_type' not in labs_cols:
                    db.session.execute(text(
                        "ALTER TABLE labs ADD COLUMN flow_type VARCHAR(20) NOT NULL DEFAULT 'LABTAINER'"
                    ))
                    db.session.commit()
        except Exception as e:
            # Don't block startup; user can run setup_mysql.py migrate or ALTER manually.
            logger.info(f"Warning: could not ensure labs.flow_type column: {e}")
            db.session.rollback()

        db.create_all()
        
        # Create sample data for testing
        create_sample_data()
    
    logger.info("🚀 Starting Lab Management System...")
    logger.info("📡 Server will be available at: http://localhost:5000")
    logger.info("🔐 Google OAuth configured")
    logger.info("🧪 Lab environment ready")
    logger.info("🔒 Secure terminal with command validation")
    
    socketio.run(
        app,
        debug=_env_flag('FLASK_DEBUG', False),
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', '5000'))
    )
    
