from flask import Flask, render_template, request, redirect, url_for, session
import subprocess
import os
import re

app = Flask(__name__)
app.secret_key = "iot_device_secret_key"
app.config['SESSION_COOKIE_NAME'] = os.environ.get('EMAIL', 'session')
# Hardcoded cloud credentials for Gitleaks detection
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_CONNECTION_STRING = "mysql://admin:P@ssw0rd!@db01.internal.example.com:3306/production"
# Flag for demo - Gitleaks should detect this
FLAG_DEMO = "FLAG{7c9e8a3b2d1f4e6a5b8c0d9e7f6a4b2c1d3e5f8a}"

# Default credentials from the script
DEFAULT_CREDS = {
    "admin": "123456",
    "root": "xc3511"
}

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in DEFAULT_CREDS and DEFAULT_CREDS[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid credentials. Please contact your system administrator.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/playback')
def playback():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('playback.html', user=session['user'])

@app.route('/log')
def log():
    if 'user' not in session:
        return redirect(url_for('login'))
    # Simulated logs
    logs = [
        {"time": "2026-04-05 08:30:12", "user": "system", "event": "Device started successfully."},
        {"time": "2026-04-05 08:31:05", "user": "system", "event": "Network interface eth0 linked (100Mbps)."},
        {"time": "2026-04-05 09:15:22", "user": "admin", "event": "User logged in from 192.168.1.10."},
        {"time": "2026-04-05 09:16:45", "user": "admin", "event": "Modified PTZ configuration."},
    ]
    return render_template('log.html', user=session['user'], logs=logs)

@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('info.html', user=session['user']) # Default to Info/Status

@app.route('/info')
def info():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('info.html', user=session['user'])

@app.route('/network')
def network():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('network.html', user=session['user'])

@app.route('/account')
def account():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('account.html', user=session['user'])

@app.route('/storage')
def storage():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('storage.html', user=session['user'])

@app.route('/update')
def update():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('update.html', user=session['user'])

@app.route('/diagnostic', methods=['GET', 'POST'])
def diagnostic():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    result = ""
    error_msg = ""
    if request.method == 'POST':
        target = request.form.get('target')
        if target:
            # SECURITY FILTER: Blocking common command separators
            # This makes the challenge harder and requires bypassing
            if re.search(r'[;&|`$(){}]', target):
                error_msg = "Security Alert: Malicious character detected in input string!"
            else:
                # VULNERABILITY: Still uses shell=True, vulnerable to newline injection
                command = f"traceroute -m 3 {target}"
                try:
                    # Run with 2s timeout to prevent hanging the app too long
                    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True, timeout=5)
                    result = output
                except subprocess.TimeoutExpired:
                    result = "Diagnostic process timed out."
                except subprocess.CalledProcessError as e:
                    result = e.output
                except Exception as e:
                    result = f"Error: {str(e)}"
                    
    return render_template('diagnostic.html', result=result, error_msg=error_msg, user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Running on port 5000 as low-priv user
    app.run(host='0.0.0.0', port=5000)
