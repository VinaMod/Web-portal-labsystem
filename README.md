## Installation and Setup (Linux & Windows WSL)

The setup process is identical for a native Linux environment and for a WSL environment on Windows.

### Prerequisites
- **Python 3.8+**: Check your version with `python3 --version`.
- **pip**: The Python package installer.
- **venv**: The standard Python tool for creating virtual environments. If it's not installed, run:
  ```bash
  sudo apt update && sudo apt install python3-venv -y
  ```

### Step 1: Get the Code
Clone the repository or download the source code into a folder on your machine.

If you are on WSL, you can place this folder either inside the WSL filesystem (e.g., `/home/user/`) or on a mounted Windows drive (e.g., `/mnt/c/Users/YourUser/Projects/`). You can open WSL in your folder by typing wsl in the file address field of File Explorer.

### Step 2: Set Up the Environment
Open a terminal (or your WSL terminal) and navigate into the project directory.

```bash
# Example path, change it to your actual project path
cd /path/to/Web-portal-labsystem
```

1.  **Create a Python virtual environment:**
    ```bash
    python3 -m venv venv
    ```
    This creates a `venv` folder that will contain an isolated copy of Python and its packages.

2.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate
    ```
    Your terminal prompt should now be prefixed with `(venv)`, indicating the environment is active.

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```
    This command reads the `requirements.txt` file and installs the necessary libraries into your virtual environment.

---

## Running the Application

1.  **Activate the virtual environment** (if it's not already active):
    ```bash
    source venv/bin/activate
    ```

2.  **Start the Python server:**
    ```bash
    python3 app.py
    ```
    You should see output confirming the server has started, like this:
    ```
    Starting aiohttp server on http://0.0.0.0:5000
    ```
    The terminal will now be occupied by the running server.

3.  **Access the Web Terminal:**
    Open a modern web browser (like Chrome, Firefox, or Edge) and navigate to the following address:
    ```
    http://localhost:5000
    ```
    You should see the web terminal interface, ready to accept commands.

### Stopping the Server
To stop the application, go back to the terminal where the server is running and press **`Ctrl + C`**.