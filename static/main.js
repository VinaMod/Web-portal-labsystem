// Initialize the terminal
const term = new Terminal({
    cursorBlink: true
});
const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);

// Open the terminal in the 'terminal' DOM element
term.open(document.getElementById('terminal'));

// Make the terminal fit the container
fitAddon.fit();
window.addEventListener('resize', () => fitAddon.fit());

// Initialize Socket.IO connection
const socket = io();

// Handle incoming data from the server and write it to the terminal
socket.on('pty_output', function(data) {
    term.write(data.output);
});

// Handle user input in the terminal and send it to the server
term.onData(function(data) {
    socket.emit('pty_input', { 'input': data });
});

// Handle connection events
socket.on('connect', () => {
    console.log('Connected to backend');
    // You can send an initial message or command here if needed
});

socket.on('disconnect', () => {
    console.log('Disconnected from backend');
    term.write('\r\n\r\n[DISCONNECTED]\r\n');
});

//This section handles terminal resizing.
function sendTerminalSize() {
    // Check if the socket is connected before sending
    if (socket.connected) {
        socket.emit('pty_resize', { 'cols': term.cols, 'rows': term.rows });
    }
}

// Send initial size on connection
socket.on('connect', () => {
    console.log('Connected to backend');
    // Fit the terminal and send the size
    fitAddon.fit();
});

// Send new size whenever the terminal is resized
term.onResize(() => {
    sendTerminalSize();
});

// Also re-fit the terminal when the browser window resizes
window.addEventListener('resize', () => {
    fitAddon.fit();
});