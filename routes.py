from flask import session, render_template, request, jsonify, redirect, url_for
from flask_login import current_user, login_user
from flask_socketio import SocketIO, emit, disconnect
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from models import Course, Lab, Enrollment, UserLab, User
from labtainer_integration import clone_lab_template, rebuild_lab, start_lab, stop_lab
from flask_dance.contrib.google import make_google_blueprint, google
import os
import pty
import fcntl
import termios
import struct
import select
import random
import jwt
import datetime
import threading
import subprocess

app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")
if os.environ.get('GOOGLE_OAUTH_CLIENT_ID') and os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'):
    print("=================================================== start google login")
    google_bp = make_google_blueprint(
        client_id=os.environ['GOOGLE_OAUTH_CLIENT_ID'],
        client_secret=os.environ['GOOGLE_OAUTH_CLIENT_SECRET'],
        scope=["profile", "email"],
        redirect_url="/auth/google/authorized"
    )
    app.register_blueprint(google_bp, url_prefix="/auth")

@app.before_request
def make_session_permanent():
    session.permanent = True

socketio = SocketIO(app, cors_allowed_origins='*', manage_session=False)

clients = {}

@socketio.on('connect')
def handle_connect_auth():
    if not current_user.is_authenticated:
        disconnect()
        return False

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/auth/login')
def auth_login_redirect():
    print("============================================================= " + app.blueprints);
    if 'google' in app.blueprints:
        return redirect(url_for('google.login'))
    return redirect(url_for('replit_auth.login'))

@app.route('/dashboard')
@require_login
def dashboard():
    user_courses = Enrollment.query.filter_by(user_id=current_user.id).all()
    user_labs = UserLab.query.filter_by(user_id=current_user.id).all()
    all_courses = Course.query.all()
    
    return render_template('dashboard.html', 
                         user_courses=user_courses, 
                         user_labs=user_labs,
                         all_courses=all_courses,
                         user=current_user)

@app.route('/courses')
@require_login
def courses():
    all_courses = Course.query.all()
    enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(user_id=current_user.id).all()]
    return render_template('courses.html', courses=all_courses, enrolled_ids=enrolled_course_ids)

@app.route('/enroll/<int:course_id>', methods=['POST'])
@require_login
def enroll_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if existing:
        return jsonify({'status': 'already_enrolled'})
    
    enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
    db.session.add(enrollment)
    
    labs = Lab.query.filter_by(course_id=course_id).all()
    lab_template = random.choice(labs) if labs else None
    
    if lab_template:
        folder_name = f"{current_user.id}-{lab_template.template_folder}"
        
        success, message = clone_lab_template(lab_template.template_folder, folder_name)
        
        if success:
            user_lab = UserLab(
                user_id=current_user.id,
                lab_id=lab_template.id,
                folder_name=folder_name,
                status='ENROLLED'
            )
            db.session.add(user_lab)
            db.session.commit()
            return jsonify({'status': 'success', 'folder_name': folder_name, 'message': message})
        else:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Lab provisioning failed: {message}'}), 500
    
    db.session.commit()
    return jsonify({'status': 'success', 'folder_name': None})

@app.route('/terminal')
@app.route('/terminal/<int:lab_id>')
@require_login
def terminal(lab_id=None):
    user_lab = None
    if lab_id:
        user_lab = UserLab.query.filter_by(user_id=current_user.id, lab_id=lab_id).first()
        if user_lab:
            user_lab.last_accessed = db.func.now()
            db.session.commit()
    
    return render_template('terminal.html', user_lab=user_lab)

@socketio.on('init_terminal')
def handle_terminal_init(data):
    if not current_user.is_authenticated:
        emit('error', {'message': 'Not authenticated'})
        disconnect()
        return
    
    sid = request.sid
    lab_id = data.get('lab_id')
    
    print(f"Client {sid} initializing terminal for user {current_user.id}, lab {lab_id}")
    
    user_lab = None
    if lab_id:
        user_lab = UserLab.query.filter_by(user_id=current_user.id, lab_id=lab_id).first()
        if not user_lab:
            emit('error', {'message': 'Lab not found or not accessible'})
            return
    
    pid, fd = pty.fork()
    
    if pid == 0:
        if user_lab:
            lab_env = os.environ.copy()
            lab_env['LAB_FOLDER'] = user_lab.folder_name
            lab_env['LAB_ID'] = str(user_lab.lab_id)
            lab_env['PS1'] = f'[{user_lab.folder_name}] $ '
            os.execvpe('bash', ['bash'], lab_env)
        else:
            os.execvp('bash', ['bash'])
    else:
        clients[sid] = {
            'pid': pid,
            'fd': fd,
            'user_id': current_user.id,
            'lab_id': lab_id,
            'user_lab_id': user_lab.id if user_lab else None
        }
        
        if user_lab:
            user_lab.last_accessed = db.func.now()
            db.session.commit()
        
        socketio.start_background_task(target=read_and_forward_pty_output, sid=sid)
        print(f"Started background task for {sid}")

@socketio.on('pty_input')
def handle_pty_input(data):
    sid = request.sid
    if sid in clients:
        os.write(clients[sid]['fd'], data['input'].encode())

@socketio.on('pty_resize')
def handle_pty_resize(data):
    sid = request.sid
    if sid in clients:
        fd = clients[sid]['fd']
        winsize = struct.pack('HHHH', data['rows'], data['cols'], 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in clients:
        try:
            pid = clients[sid].get('pid')
            if pid:
                os.kill(pid, 9)
        except ProcessLookupError:
            pass
        finally:
            clients.pop(sid, None)
    print(f"Client disconnected: {sid}")

def read_and_forward_pty_output(sid):
    while sid in clients:
        try:
            fd = clients[sid].get('fd')
            if not fd:
                break
            
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                output = os.read(fd, 1024)
                if output:
                    socketio.emit('pty_output', {'output': output.decode()}, room=sid)
                else:
                    break
        except Exception as e:
            print(f"Error in reader task for {sid}: {e}")
            break
    
    print(f"Stopped background task for {sid}")

@app.route('/lab/<int:lab_id>/rebuild', methods=['POST'])
@require_login
def rebuild_user_lab(lab_id):
    user_lab = UserLab.query.filter_by(user_id=current_user.id, lab_id=lab_id).first_or_404()
    
    success, output = rebuild_lab(user_lab.folder_name)
    
    if success:
        return jsonify({'status': 'success', 'output': output})
    else:
        return jsonify({'status': 'error', 'message': output}), 500

@app.route('/lab/<int:lab_id>/start', methods=['POST'])
@require_login
def start_user_lab(lab_id):
    user_lab = UserLab.query.filter_by(user_id=current_user.id, lab_id=lab_id).first_or_404()
    
    success, output = start_lab(user_lab.folder_name)
    
    if success:
        user_lab.status = 'ACTIVE'
        db.session.commit()
        return jsonify({'status': 'success', 'output': output})
    else:
        return jsonify({'status': 'error', 'message': output}), 500

@app.route('/lab/<int:lab_id>/stop', methods=['POST'])
@require_login
def stop_user_lab(lab_id):
    user_lab = UserLab.query.filter_by(user_id=current_user.id, lab_id=lab_id).first_or_404()
    
    success, output = stop_lab(user_lab.folder_name)
    
    if success:
        user_lab.status = 'STOPPED'
        db.session.commit()
        return jsonify({'status': 'success', 'output': output})
    else:
        return jsonify({'status': 'error', 'message': output}), 500

@app.route('/init_sample_data')
@require_login
def init_sample_data():
    if Course.query.count() > 0:
        return jsonify({'status': 'already_initialized'})
    
    courses_data = [
        ('Introduction to Cybersecurity', 'Fundamentals of network security and ethical hacking'),
        ('Advanced Network Security', 'Deep dive into network protocols and security measures'),
        ('Web Application Security', 'Learn about OWASP vulnerabilities and secure coding')
    ]
    
    for name, desc in courses_data:
        course = Course(name=name, description=desc)
        db.session.add(course)
    
    db.session.commit()
    
    labs_data = [
        (1, 'Network Reconnaissance', 'recon-lab', 'Learn network scanning and enumeration techniques'),
        (1, 'SQL Injection Basics', 'sql-injection-lab', 'Introduction to SQL injection vulnerabilities'),
        (1, 'Buffer Overflow Introduction', 'buffer-overflow-lab', 'Understanding memory corruption vulnerabilities'),
        (2, 'Firewall Configuration', 'firewall-lab', 'Configure and test firewall rules'),
        (2, 'VPN Setup', 'vpn-lab', 'Set up and secure VPN connections'),
        (3, 'XSS Vulnerabilities', 'xss-lab', 'Cross-site scripting attack and defense'),
    ]
    
    for course_id, name, template, desc in labs_data:
        lab = Lab(course_id=course_id, name=name, template_folder=template, description=desc)
        db.session.add(lab)
    
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/auth/google/authorized')
def google_authorized_landing():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        return redirect(url_for('replit_auth.error'))
    info = resp.json() or {}
    email = info.get('email') or ''
    if not email.endswith('.edu'):
        return redirect(url_for('replit_auth.error'))
    user = User.query.get(info.get('id'))
    if not user:
        user = User(
            id=str(info.get('id')),
            email=email,
            first_name=info.get('given_name'),
            last_name=info.get('family_name'),
            profile_image_url=info.get('picture')
        )
        db.session.add(user)
    else:
        user.email = email
        user.first_name = info.get('given_name')
        user.last_name = info.get('family_name')
        user.profile_image_url = info.get('picture')
    db.session.commit()
    login_user(user)
    return redirect(url_for('dashboard'))

# ===== JWT + JSON API (Option A) =====

def _issue_jwt(user_id: str, email: str | None = None):
    payload = {
        'sub': user_id,
        'email': email,
        'iat': int(datetime.datetime.utcnow().timestamp()),
        'exp': int((datetime.datetime.utcnow() + datetime.timedelta(hours=8)).timestamp())
    }
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token

def token_required(f):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        parts = auth.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            try:
                decoded = jwt.decode(token, app.secret_key, algorithms=['HS256'])
                request.jwt = decoded
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'token_expired'}), 401
            except Exception:
                return jsonify({'error': 'invalid_token'}), 401
        return jsonify({'error': 'authorization_required'}), 401
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/api/auth/login', methods=['GET'])
def api_auth_login():
    if current_user.is_authenticated:
        token = _issue_jwt(current_user.id, getattr(current_user, 'email', None))
        user = {
            'id': current_user.id,
            'email': getattr(current_user, 'email', None),
            'first_name': getattr(current_user, 'first_name', None),
            'last_name': getattr(current_user, 'last_name', None),
        }
        return jsonify({'token': token, 'user': user})
    login_url = url_for('replit_auth.login', _external=True)
    return jsonify({'error': 'not_authenticated', 'login_url': login_url}), 401

@app.route('/api/dashboard', methods=['GET'])
@token_required
def api_dashboard():
    user_id = request.jwt.get('sub')
    enrollments = Enrollment.query.filter_by(user_id=user_id).all()
    course_ids = [e.course_id for e in enrollments]
    courses = Course.query.filter(Course.id.in_(course_ids) if course_ids else False).all()
    user_labs = UserLab.query.filter_by(user_id=user_id).all()
    labs_by_course = {}
    for ul in user_labs:
        lab = Lab.query.get(ul.lab_id)
        if not lab:
            continue
        labs_by_course.setdefault(lab.course_id, []).append({
            'lab_id': lab.id,
            'name': lab.name,
            'template_folder': lab.template_folder,
            'folder_name': ul.folder_name,
            'status': ul.status,
        })
    data = []
    for c in courses:
        data.append({
            'course_id': c.id,
            'course_name': c.name,
            'labs': labs_by_course.get(c.id, [])
        })
    return jsonify({'courses': data})

@app.route('/api/register-lab', methods=['POST'])
@token_required
def api_register_lab():
    user_id = request.jwt.get('sub')
    body = request.get_json(silent=True) or {}
    course_id = body.get('course_id')
    if not course_id:
        return jsonify({'error': 'course_id_required'}), 400
    if not Course.query.get(course_id):
        return jsonify({'error': 'course_not_found'}), 404
    if not Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first():
        enroll = Enrollment(user_id=user_id, course_id=course_id)
        db.session.add(enroll)
        db.session.commit()
    labs = Lab.query.filter_by(course_id=course_id).limit(3).all()
    if not labs:
        return jsonify({'error': 'no_labs_available'}), 400
    lab_template = random.choice(labs)
    folder_name = f"{user_id}-{lab_template.template_folder}"
    if UserLab.query.filter_by(user_id=user_id, lab_id=lab_template.id).first():
        return jsonify({'status': 'already_registered', 'folder_name': folder_name})
    success, message = clone_lab_template(lab_template.template_folder, folder_name)
    if not success:
        db.session.rollback()
        return jsonify({'error': 'provision_failed', 'message': message}), 500
    user_lab = UserLab(user_id=user_id, lab_id=lab_template.id, folder_name=folder_name, status='ENROLLED')
    db.session.add(user_lab)
    db.session.commit()
    return jsonify({'status': 'success', 'folder_name': folder_name, 'lab_id': lab_template.id})

@app.route('/api/start-lab', methods=['POST'])
@token_required
def api_start_lab():
    user_id = request.jwt.get('sub')
    body = request.get_json(silent=True) or {}
    lab_id = body.get('lab_id')
    if not lab_id:
        return jsonify({'error': 'lab_id_required'}), 400
    user_lab = UserLab.query.filter_by(user_id=user_id, lab_id=lab_id).first()
    if not user_lab:
        return jsonify({'error': 'lab_not_found'}), 404
    channel = f"lab_output:{user_id}:{lab_id}"
    def _stream_cmd(cmd_list, cwd=None):
        try:
            proc = subprocess.Popen(cmd_list, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                socketio.emit(channel, {'line': line.rstrip()})
            proc.wait()
            return proc.returncode
        except Exception as e:
            socketio.emit(channel, {'line': f'Error: {str(e)}'})
            return 1
    def _runner():
        socketio.emit(channel, {'line': f'Starting rebuild {user_lab.folder_name}...'})
        rc1 = _stream_cmd(['rebuild', user_lab.folder_name], cwd=os.environ.get('LABTAINER_PATH', '/home/labtainer'))
        if rc1 != 0:
            socketio.emit(channel, {'line': 'Rebuild failed.'})
            return
        socketio.emit(channel, {'line': f'Starting lab {user_lab.folder_name}...'})
        rc2 = _stream_cmd(['labtainer', 'start', user_lab.folder_name], cwd=os.environ.get('LABTAINER_PATH', '/home/labtainer'))
        if rc2 == 0:
            user_lab.status = 'ACTIVE'
            db.session.commit()
            socketio.emit(channel, {'line': 'Lab started successfully.'})
        else:
            socketio.emit(channel, {'line': 'Lab start failed.'})
    threading.Thread(target=_runner, daemon=True).start()
    return jsonify({'status': 'starting', 'stream_channel': channel})
