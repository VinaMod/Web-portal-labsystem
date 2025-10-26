import os
import json
import logging
import subprocess
import random
import shutil
from datetime import datetime, timedelta
from functools import wraps

import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import jwt
from oauthlib.oauth2 import WebApplicationClient
from dotenv import load_dotenv

from database import db
from models import User, Course, Lab, UserCourse, LabTemplate, LabStatus

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

JWT_SECRET = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

LAB_BASE_PATH = os.environ.get("LAB_BASE_PATH", "./labs")

client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None


def create_jwt_token(user_id, email):
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        user = db.session.get(User, payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated


def validate_edu_email(email):
    return '.edu' in email.lower()


def execute_labtainer_command(command, lab_folder_name):
    try:
        full_command = f"{command} {lab_folder_name}"
        logger.info(f"Executing Labtainer command: {full_command}")
        
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=LAB_BASE_PATH
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {full_command}")
        return {
            'success': False,
            'error': 'Command execution timeout'
        }
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def clone_lab_template(template_folder, user_id, lab_name):
    try:
        source_path = os.path.join(LAB_BASE_PATH, template_folder)
        new_folder_name = f"{user_id}-{template_folder}"
        dest_path = os.path.join(LAB_BASE_PATH, new_folder_name)
        
        if os.path.exists(dest_path):
            logger.warning(f"Lab folder already exists: {dest_path}")
            return new_folder_name, dest_path
        
        shutil.copytree(source_path, dest_path)
        logger.info(f"Cloned lab template from {source_path} to {dest_path}")
        
        return new_folder_name, dest_path
    except Exception as e:
        logger.error(f"Error cloning lab template: {str(e)}")
        raise


@app.route('/')
def index():
    if 'user_email' in session:
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))


@app.route('/login')
def login_page():
    return render_template('login.html', current_user=None)


@app.route('/dashboard')
def dashboard_page():
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html', current_user=session.get('user_email'))


@app.route('/labs')
def labs_page():
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    return render_template('labs.html', current_user=session.get('user_email'))


@app.route('/terminal/<int:lab_id>')
def terminal_page(lab_id):
    if 'user_email' not in session:
        return redirect(url_for('login_page'))
    return render_template('terminal.html', current_user=session.get('user_email'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200


@app.route('/auth/login', methods=['GET'])
def login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({
            'error': 'Google OAuth not configured. Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables.'
        }), 500
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        redirect_uri = request.base_url + "/callback"
        print("============================= ", redirect_uri)
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
        print("VERIFY URI =======================")
        verify = jsonify({'authorization_url': request_uri});
        print("VERIFY RESULT ================================", str(verify))
        return verify, 200
    except Exception as e:
        print("ERROR =================================== ", str(e))
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Failed to initiate login process'}), 500


@app.route('/auth/login/callback', methods=['GET'])
def login_callback():
    print("CALLBACK ==================================")
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    
    try:
        code = request.args.get("code")
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        userinfo = userinfo_response.json()
        
        if not userinfo.get("email_verified"):
            return jsonify({'error': 'Email not verified by Google'}), 400
        
        email = userinfo["email"]
        
        print("EMAIL =============================", email)
        if not validate_edu_email(email):
            return redirect(url_for('login_page') + '?error=Only .edu email addresses are allowed')
        
        name = userinfo.get("name", userinfo.get("given_name", "Unknown"))
        google_id = userinfo["sub"]
        
        user = db.session.query(User).filter_by(google_id=google_id).first()
        
        if not user:
            user = User(
                email=email,
                name=name,
                google_id=google_id
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user registered: {email}")
        else:
            logger.info(f"Existing user logged in: {email}")
        
        token = create_jwt_token(user.id, user.email)
        
        session['user_email'] = user.email
        session['user_id'] = user.id
        session['jwt_token'] = token
        
        return render_template('auth_success.html', token=token, user=user.to_dict())
        
    except Exception as e:
        logger.error(f"Error during login callback: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 500


@app.route('/dashboard', methods=['GET'])
@token_required
def dashboard(user):
    try:
        user_courses = db.session.query(UserCourse).filter_by(user_id=user.id).all()
        
        dashboard_data = {
            'user': user.to_dict(),
            'courses': []
        }
        
        for uc in user_courses:
            course = db.session.get(Course, uc.course_id)
            if course:
                labs = db.session.query(Lab).filter_by(
                    user_id=user.id,
                    course_id=course.id
                ).all()
                
                course_data = course.to_dict()
                course_data['labs'] = [lab.to_dict() for lab in labs]
                dashboard_data['courses'].append(course_data)
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500


@app.route('/register-lab', methods=['POST'])
@token_required
def register_lab(user):
    try:
        data = request.get_json()
        
        if not data or 'course_id' not in data:
            return jsonify({'error': 'course_id is required'}), 400
        
        course_id = data['course_id']
        
        course = db.session.get(Course, course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        user_course = db.session.query(UserCourse).filter_by(
            user_id=user.id,
            course_id=course_id
        ).first()
        
        if not user_course:
            user_course = UserCourse(user_id=user.id, course_id=course_id)
            db.session.add(user_course)
            db.session.commit()
            logger.info(f"User {user.id} enrolled in course {course_id}")
        
        lab_templates = db.session.query(LabTemplate).all()
        
        if not lab_templates:
            return jsonify({'error': 'No lab templates available'}), 404
        
        selected_template = random.choice(lab_templates)
        
        try:
            lab_folder_name, lab_path = clone_lab_template(
                selected_template.folder_name,
                user.id,
                selected_template.name
            )
        except Exception as e:
            return jsonify({'error': f'Failed to clone lab template: {str(e)}'}), 500
        
        lab = Lab(
            user_id=user.id,
            course_id=course_id,
            lab_name=f"{user.id}-{selected_template.name}",
            template_name=selected_template.name,
            folder_name=lab_folder_name,
            folder_path=lab_path,
            status=LabStatus.ENROLLED
        )
        
        db.session.add(lab)
        db.session.commit()
        
        logger.info(f"Lab registered: {lab.lab_name} for user {user.id}")
        
        return jsonify({
            'message': 'Lab registered successfully',
            'lab': lab.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering lab: {str(e)}")
        return jsonify({'error': 'Failed to register lab'}), 500


@app.route('/labs', methods=['GET'])
@token_required
def get_labs(user):
    try:
        labs = db.session.query(Lab).filter_by(user_id=user.id).all()
        return jsonify({
            'labs': [lab.to_dict() for lab in labs]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching labs: {str(e)}")
        return jsonify({'error': 'Failed to fetch labs'}), 500


@app.route('/courses', methods=['GET'])
def get_courses():
    try:
        courses = db.session.query(Course).all()
        return jsonify({
            'courses': [course.to_dict() for course in courses]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        return jsonify({'error': 'Failed to fetch courses'}), 500


active_sessions = {}


@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected', 'session_id': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")
    if request.sid in active_sessions:
        del active_sessions[request.sid]


@socketio.on('authenticate')
def handle_authenticate(data):
    try:
        token = data.get('token')
        if not token:
            emit('error', {'message': 'Token is required'})
            disconnect()
            return
        
        payload = verify_jwt_token(token)
        if not payload:
            emit('error', {'message': 'Invalid or expired token'})
            disconnect()
            return
        
        user = db.session.get(User, payload['user_id'])
        if not user:
            emit('error', {'message': 'User not found'})
            disconnect()
            return
        
        active_sessions[request.sid] = {
            'user_id': user.id,
            'email': user.email
        }
        
        emit('authenticated', {'user_id': user.id, 'email': user.email})
        logger.info(f"User {user.id} authenticated on WebSocket")
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        emit('error', {'message': 'Authentication failed'})
        disconnect()


@socketio.on('start_lab')
def handle_start_lab(data):
    try:
        if request.sid not in active_sessions:
            emit('error', {'message': 'Not authenticated'})
            return
        
        user_id = active_sessions[request.sid]['user_id']
        lab_id = data.get('lab_id')
        
        if not lab_id:
            emit('error', {'message': 'lab_id is required'})
            return
        
        lab = db.session.get(Lab, lab_id)
        
        if not lab or lab.user_id != user_id:
            emit('error', {'message': 'Lab not found or access denied'})
            return
        
        emit('output', {'message': f'Starting lab: {lab.lab_name}...\n'})
        
        result = execute_labtainer_command('rebuild', lab.folder_name)
        
        if result['success']:
            emit('output', {'message': f"Rebuild output:\n{result['stdout']}\n"})
            
            lab.status = LabStatus.STARTED
            db.session.commit()
            
            emit('lab_status', {'lab_id': lab.id, 'status': 'STARTED'})
            emit('output', {'message': 'Lab started successfully!\n'})
        else:
            emit('output', {'message': f"Error during rebuild:\n{result.get('stderr', result.get('error', 'Unknown error'))}\n"})
            emit('error', {'message': 'Failed to start lab'})
        
    except Exception as e:
        logger.error(f"Error starting lab: {str(e)}")
        emit('error', {'message': f'Failed to start lab: {str(e)}'})


@socketio.on('execute_command')
def handle_execute_command(data):
    try:
        if request.sid not in active_sessions:
            emit('error', {'message': 'Not authenticated'})
            return
        
        user_id = active_sessions[request.sid]['user_id']
        lab_id = data.get('lab_id')
        command = data.get('command', '').strip()
        
        if not lab_id or not command:
            emit('error', {'message': 'lab_id and command are required'})
            return
        
        lab = db.session.get(Lab, lab_id)
        
        if not lab or lab.user_id != user_id:
            emit('error', {'message': 'Lab not found or access denied'})
            return
        
        if command.startswith('labtainer start'):
            result = execute_labtainer_command('labtainer start', lab.folder_name)
            if result['success']:
                lab.status = LabStatus.STARTED
                db.session.commit()
                emit('lab_status', {'lab_id': lab.id, 'status': 'STARTED'})
        elif command.startswith('labtainer stop'):
            result = execute_labtainer_command('labtainer stop', lab.folder_name)
            if result['success']:
                lab.status = LabStatus.COMPLETED
                db.session.commit()
                emit('lab_status', {'lab_id': lab.id, 'status': 'COMPLETED'})
        elif command.startswith('rebuild'):
            result = execute_labtainer_command('rebuild', lab.folder_name)
        else:
            result = {
                'success': False,
                'stderr': 'Only Labtainer commands are allowed (labtainer start, labtainer stop, rebuild)'
            }
        
        if result['success']:
            emit('output', {'message': result['stdout']})
        else:
            emit('output', {'message': result.get('stderr', result.get('error', 'Command failed'))})
        
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        emit('error', {'message': f'Command execution failed: {str(e)}'})


with app.app_context():
    from models import User, Course, Lab, UserCourse, LabTemplate, LabStatus
    db.create_all()
    logger.info("Database tables created successfully")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
