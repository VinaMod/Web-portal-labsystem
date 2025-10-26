"""
Labtainer Integration Module

This module provides functions to interact with Labtainer system commands.
In production, these would execute actual Labtainer commands on the server.
"""

import os
import subprocess
from typing import Tuple, Optional

LABTAINER_PATH = os.environ.get('LABTAINER_PATH', '/home/labtainer')
LABS_PATH = os.path.join(LABTAINER_PATH, 'labs')

def clone_lab_template(template_folder: str, user_lab_folder: str) -> Tuple[bool, str]:
    """
    Clone a Labtainer lab template to create a user-specific lab instance.
    
    Args:
        template_folder: Name of the template folder (e.g., 'recon-lab')
        user_lab_folder: Name for the new lab folder (e.g., '12345-recon-lab')
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    source_path = os.path.join(LABS_PATH, 'templates', template_folder)
    dest_path = os.path.join(LABS_PATH, 'instances', user_lab_folder)
    
    try:
        result = subprocess.run(
            ['cp', '-r', source_path, dest_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, f"Lab folder {user_lab_folder} created successfully"
        else:
            return False, f"Failed to clone lab: {result.stderr}"
    
    except subprocess.TimeoutExpired:
        return False, "Lab cloning timeout"
    except FileNotFoundError:
        return False, f"Template folder not found: {template_folder}"
    except Exception as e:
        return False, f"Error cloning lab: {str(e)}"

def rebuild_lab(lab_folder: str) -> Tuple[bool, str]:
    """
    Rebuild a Labtainer lab environment.
    
    Args:
        lab_folder: Name of the lab folder to rebuild
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['rebuild', lab_folder],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=LABTAINER_PATH
        )
        
        return result.returncode == 0, result.stdout
    
    except subprocess.TimeoutExpired:
        return False, "Rebuild command timeout"
    except FileNotFoundError:
        return False, "Rebuild command not found. Is Labtainer installed?"
    except Exception as e:
        return False, f"Error rebuilding lab: {str(e)}"

def start_lab(lab_folder: str) -> Tuple[bool, str]:
    """
    Start a Labtainer lab environment.
    
    Args:
        lab_folder: Name of the lab folder to start
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['labtainer', 'start', lab_folder],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=LABTAINER_PATH
        )
        
        return result.returncode == 0, result.stdout
    
    except subprocess.TimeoutExpired:
        return False, "Start command timeout"
    except FileNotFoundError:
        return False, "Labtainer command not found. Is Labtainer installed?"
    except Exception as e:
        return False, f"Error starting lab: {str(e)}"

def stop_lab(lab_folder: str) -> Tuple[bool, str]:
    """
    Stop a Labtainer lab environment.
    
    Args:
        lab_folder: Name of the lab folder to stop
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['labtainer', 'stop', lab_folder],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=LABTAINER_PATH
        )
        
        return result.returncode == 0, result.stdout
    
    except subprocess.TimeoutExpired:
        return False, "Stop command timeout"
    except FileNotFoundError:
        return False, "Labtainer command not found. Is Labtainer installed?"
    except Exception as e:
        return False, f"Error stopping lab: {str(e)}"

def get_lab_status(lab_folder: str) -> Tuple[bool, Optional[str]]:
    """
    Get the status of a Labtainer lab.
    
    Args:
        lab_folder: Name of the lab folder
    
    Returns:
        Tuple of (is_running: bool, status_message: Optional[str])
    """
    try:
        result = subprocess.run(
            ['labtainer', 'status', lab_folder],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=LABTAINER_PATH
        )
        
        if result.returncode == 0:
            is_running = 'running' in result.stdout.lower()
            return is_running, result.stdout
        else:
            return False, None
    
    except Exception:
        return False, None

def execute_in_lab(lab_folder: str, command: str) -> Tuple[bool, str]:
    """
    Execute a command within a specific lab environment.
    This would be used for automated grading or setup tasks.
    
    Args:
        lab_folder: Name of the lab folder
        command: Command to execute
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['labtainer', 'exec', lab_folder, '--', command],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=LABTAINER_PATH
        )
        
        return result.returncode == 0, result.stdout
    
    except subprocess.TimeoutExpired:
        return False, "Command execution timeout"
    except Exception as e:
        return False, f"Error executing command: {str(e)}"

def cleanup_user_labs(user_id: str) -> Tuple[bool, str]:
    """
    Clean up all lab instances for a specific user.
    Use with caution - this will delete user's lab data.
    
    Args:
        user_id: User ID whose labs should be cleaned up
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    instances_path = os.path.join(LABS_PATH, 'instances')
    user_prefix = f"{user_id}-"
    
    try:
        deleted_count = 0
        for folder in os.listdir(instances_path):
            if folder.startswith(user_prefix):
                folder_path = os.path.join(instances_path, folder)
                subprocess.run(['rm', '-rf', folder_path], check=True)
                deleted_count += 1
        
        return True, f"Cleaned up {deleted_count} lab instances"
    
    except Exception as e:
        return False, f"Error during cleanup: {str(e)}"

"""
Usage Examples:

1. When user enrolls in a course:
   success, msg = clone_lab_template('recon-lab', '12345-recon-lab')
   if success:
       # Update database status to ENROLLED
       pass

2. User wants to start their lab:
   success, output = start_lab('12345-recon-lab')
   if success:
       # Update database status to ACTIVE
       # Show output to user
       pass

3. User wants to rebuild lab:
   success, output = rebuild_lab('12345-recon-lab')
   # Show output to user

4. Check if lab is running before allowing terminal access:
   is_running, status = get_lab_status('12345-recon-lab')
   if not is_running:
       # Prompt user to start the lab first
       pass

5. Automated grading:
   success, output = execute_in_lab('12345-recon-lab', 'cat /root/flag.txt')
   # Parse output for grading
"""
