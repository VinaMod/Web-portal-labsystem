import os
import pty
import asyncio
from aiohttp import web
import socketio
import fcntl
import termios
import struct

# --- Basic Setup ---
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# A dictionary to hold the pty information for each client
clients = {}

# --- Serve Frontend Files ---
async def index(request):
    """Serve the index.html file."""
    return web.FileResponse('./templates/index.html')

# Setup static routes for your JS file
app.router.add_static('/static/', path='./static/', name='static')
app.router.add_get('/', index)

@sio.event
async def pty_resize(sid, data):
    """
    Called when the browser terminal is resized.
    """
    if sid in clients:
        # Get the file descriptor for the client's pty
        fd = clients[sid]['fd']
        
        # Pack the new window size into a binary structure.
        # 'HHHH' means four unsigned short integers.
        # The values are: rows, cols, xpixel, ypixel
        winsize = struct.pack('HHHH', data['rows'], data['cols'], 0, 0)
        
        # Use an ioctl system call to set the new window size
        # for the pty. This makes the bash shell inside aware of
        # the new dimensions.
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

# --- Core WebSocket Logic ---
@sio.event
async def connect(sid, environ):
    """
    This function is called when a new client connects.
    """
    print(f"Client connected: {sid}")

    # Fork a new pseudo-terminal (pty) for the client
    pid, fd = pty.fork()

    if pid == 0:  # Child process
        # Start a bash shell, replaces the child process entirely.
        os.execvp('bash', ['bash'])
    else:  # The parent (server) process
        # Store the process ID and file descriptor
        clients[sid] = {'pid': pid, 'fd': fd}
        
        # Start an asyncio task to read from the pty
        # Handle I/O
        asyncio.create_task(read_and_forward_pty_output(sid))
        print(f"Started asyncio reader task for {sid}")

@sio.event
async def pty_input(sid, data):
    """
    Received data from the browser, write it to the pty.
    """
    if sid in clients:
        os.write(clients[sid]['fd'], data['input'].encode())

@sio.event
async def disconnect(sid):
    """
    Called when a client disconnects.
    """
    if sid in clients:
        try:
            pid = clients[sid].get('pid')
            if pid:
                os.kill(pid, 9)  # Force-kill the bash process
        except ProcessLookupError:
            pass
        finally:
            clients.pop(sid, None)  # Clean up the client entry
    print(f"Client disconnected: {sid}")


# --- The Asynchronous PTY Reader ---
async def read_and_forward_pty_output(sid):
    """
    The core task that reads from the pty and sends to the browser.
    """
    loop = asyncio.get_event_loop()
    
    while sid in clients:
        try:
            fd = clients[sid].get('fd')
            if not fd:
                break
            
            # Wait for data to be available without blocking the whole server
            output = await loop.run_in_executor(None, os.read, fd, 1024)
            
            if output:
                await sio.emit('pty_output', {'output': output.decode()}, room=sid)
            else:
                # Empty output means the process (bash) has exited
                break
        except Exception as e:
            print(f"Error in reader task for {sid}: {e}")
            break
            
    print(f"Stopped asyncio reader task for {sid}")


# --- Main Entry Point ---
if __name__ == '__main__':
    print("Starting aiohttp server on http://0.0.0.0:5000")
    web.run_app(app, host='0.0.0.0', port=5000)