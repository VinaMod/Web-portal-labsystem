let term;
let socket;
let fitAddon;
let currentLabId;

function initTerminal() {
    term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
            background: '#000000',
            foreground: '#ffffff',
            cursor: '#ffffff',
            selection: '#ffffff33'
        }
    });

    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);

    const terminalDiv = document.getElementById('terminal');
    term.open(terminalDiv);
    fitAddon.fit();

    window.addEventListener('resize', () => {
        fitAddon.fit();
    });

    term.writeln('Welcome to Labtainer Terminal');
    term.writeln('Connecting to server...\n');
}

function initWebSocket() {
    socket = io({
        transports: ['websocket', 'polling']
    });

    socket.on('connect', () => {
        updateConnectionStatus(true);
        term.writeln('\x1b[32mConnected to server\x1b[0m');
        
        const token = AuthManager.getToken();
        if (token) {
            socket.emit('authenticate', { token: token });
        } else {
            term.writeln('\x1b[31mNo authentication token found\x1b[0m');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
    });

    socket.on('disconnect', () => {
        updateConnectionStatus(false);
        term.writeln('\n\x1b[31mDisconnected from server\x1b[0m');
        disableControls();
    });

    socket.on('connection_response', (data) => {
        term.writeln(`Session ID: ${data.session_id}\n`);
    });

    socket.on('authenticated', (data) => {
        term.writeln(`\x1b[32mAuthenticated as: ${data.email}\x1b[0m\n`);
        enableControls();
    });

    socket.on('output', (data) => {
        term.write(data.message);
    });

    socket.on('lab_status', (data) => {
        updateLabStatus(data.status);
        term.writeln(`\n\x1b[33m[Lab Status: ${data.status}]\x1b[0m\n`);
    });

    socket.on('error', (data) => {
        term.writeln(`\n\x1b[31mError: ${data.message}\x1b[0m\n`);
    });
}

function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-text');
    
    if (connected) {
        indicator.classList.remove('disconnected');
        indicator.classList.add('connected');
        text.textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        indicator.classList.add('disconnected');
        text.textContent = 'Disconnected';
    }
}

function updateLabStatus(status) {
    const statusElement = document.getElementById('lab-status');
    statusElement.textContent = status;
    statusElement.className = `lab-status status-${status.toLowerCase()}`;
}

function enableControls() {
    document.getElementById('start-lab-btn').disabled = false;
    document.getElementById('stop-lab-btn').disabled = false;
    document.getElementById('rebuild-btn').disabled = false;
}

function disableControls() {
    document.getElementById('start-lab-btn').disabled = true;
    document.getElementById('stop-lab-btn').disabled = true;
    document.getElementById('rebuild-btn').disabled = true;
}

document.getElementById('start-lab-btn').addEventListener('click', () => {
    if (currentLabId && socket && socket.connected) {
        term.writeln('\n\x1b[36mStarting lab...\x1b[0m\n');
        socket.emit('start_lab', { lab_id: currentLabId });
    }
});

document.getElementById('stop-lab-btn').addEventListener('click', () => {
    if (currentLabId && socket && socket.connected) {
        term.writeln('\n\x1b[36mStopping lab...\x1b[0m\n');
        socket.emit('execute_command', {
            lab_id: currentLabId,
            command: 'labtainer stop'
        });
    }
});

document.getElementById('rebuild-btn').addEventListener('click', () => {
    if (currentLabId && socket && socket.connected) {
        term.writeln('\n\x1b[36mRebuilding lab...\x1b[0m\n');
        socket.emit('execute_command', {
            lab_id: currentLabId,
            command: 'rebuild'
        });
    }
});

document.getElementById('clear-btn').addEventListener('click', () => {
    term.clear();
});

async function loadLabInfo() {
    const pathParts = window.location.pathname.split('/');
    currentLabId = parseInt(pathParts[pathParts.length - 1]);

    if (!currentLabId || isNaN(currentLabId)) {
        term.writeln('\x1b[31mInvalid lab ID\x1b[0m');
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
        return;
    }

    try {
        const response = await AuthManager.fetchWithAuth('/labs');
        const data = await response.json();
        
        const lab = data.labs.find(l => l.id === currentLabId);
        
        if (lab) {
            document.getElementById('lab-title').textContent = lab.lab_name;
            updateLabStatus(lab.status);
        } else {
            term.writeln('\x1b[31mLab not found\x1b[0m');
        }
    } catch (err) {
        term.writeln(`\x1b[31mError loading lab info: ${err.message}\x1b[0m`);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (!AuthManager.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    
    initTerminal();
    initWebSocket();
    loadLabInfo();
});
