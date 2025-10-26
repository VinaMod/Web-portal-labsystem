from flask import session, render_template, request, jsonify, redirect, url_for
from flask_login import current_user
from flask_socketio import SocketIO, emit, disconnect
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from models import Course, Lab, Enrollment, UserLab
from labtainer_integration import clone_lab_template, rebuild_lab, start_lab, stop_lab
import os
import pty
import fcntl
import termios
import struct
import select
import random

app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

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
