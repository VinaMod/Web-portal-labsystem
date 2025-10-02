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
const socket = io("http://localhost:5000")

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
    fitAddon.fit();
    sendTerminalSize();
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

function checkFlag(flagNumber) {//checks the submitted flags.
    // Define the correct answers
    const correctFlags = {
        1: "flag-1-collect-data",
        2: "flag-2-upload-file",
        3: "flag-3-read-system-file"
    };

    // Get the input element and its value
    const inputElement = document.getElementById(`flag${flagNumber}`);
    const userValue = inputElement.value.trim(); // .trim() removes whitespace

    // Check if the user's value matches the correct flag
    if (userValue === correctFlags[flagNumber]) {
        // If correct, add the 'correct' class for the green border
        inputElement.classList.add('correct');
    } else {
        // If incorrect, remove the class to clear the border
        inputElement.classList.remove('correct');
    }
}