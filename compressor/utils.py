# compressor/utils.py

import logging
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

LOG_DIR = "logs"

def setup_logging():
    """Configure the logger to output to both the console and a file."""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "process.log"

    # Prevent repeated addition of processors
    if logging.getLogger().hasHandlers():
        logging.getLogger().handlers.clear()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_file_size_mb(file_path):
    """Get the file size in MB."""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return 0

def run_command(command, cwd=None):
    """
    Execute an external command line command.

    Args:
        command (list): A list of commands and their parameters.
        cwd (str, optional): Working directory for command execution.

    Returns:
        bool: Whether the command was executed successfully.
    """
    command_str = ' '.join(command)
    logging.info(f"Execute command: {command_str}")
    
    # Make sure to include possible pipx installation paths
    env = os.environ.copy()
    home = os.path.expanduser("~")
    local_bin = os.path.join(home, ".local", "bin")
    
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
        logging.debug(f"Add {local_bin} to PATH")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=cwd,
            env=env # Use modified environment variables
        )
        if result.stdout:
            logging.debug(f"Command output:\n{result.stdout}")
        if result.stderr:
            # Distinguish between normal messages and real errors
            stderr_content = result.stderr.strip()
            if any(keyword in stderr_content.lower() for keyword in ['detected', 'diacritics', 'processing']):
                #Normal informational output from tools such as Tesseract
                logging.debug(f"Command information output:\n{stderr_content}")
            else:
                # Possible warnings or errors
                logging.warning(f"Command standard error output:\n{stderr_content}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {command_str}")
        logging.error(f"Return code: {e.returncode}")
        logging.error(f"standard output:\n{e.stdout}")
        logging.error(f"Standard Error:\n{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Command not found: {command[0]}. Please make sure the tool is installed and in the system PATH.")
        logging.error(f"Tip: If you use pipx to install, please make sure ~/.local/bin is in PATH")
        return False

def create_temp_directory():
    """Create a temporary directory."""
    return tempfile.mkdtemp()

def cleanup_directory(directory_path):
    """Clean up the temporary directory."""
    try:
        shutil.rmtree(directory_path)
        logging.debug(f"The temporary directory has been cleaned: {directory_path}")
    except Exception as e:
        logging.warning(f"Failed to clear temporary directory: {directory_path}, error: {e}")

def copy_file(src, dst):
    """Copy the file to the target location."""
    try:
        shutil.copy2(src, dst)
        logging.info(f"File copied: {src} -> {dst}")
        return True
    except Exception as e:
        logging.error(f"File copy failed: {src} -> {dst}, error: {e}")
        return False

def check_dependencies():
    """Check that the necessary external tools are installed."""
    required_tools = {
        'pdftoppm': 'poppler-utils',
        'pdfinfo': 'poppler-utils',
        'tesseract': 'tesseract-ocr tesseract-ocr-eng',
        'qpdf': 'qpdf',
        'recode_pdf': 'archive-pdf-tools (via pipx)'
    }
    
    missing_tools = []
    
    # Make sure to include the pipx installation path
    env = os.environ.copy()
    home = os.path.expanduser("~")
    local_bin = os.path.join(home, ".local", "bin")
    
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
        logging.debug(f"Add {local_bin} to PATH when checking dependencies")
    
    for tool, package in required_tools.items():
        try:
            # Use the which command to check whether the tool is in PATH
            result = subprocess.run(['which', tool], 
                                  capture_output=True, 
                                  check=True,
                                  timeout=5,
                                  env=env)
            tool_path = result.stdout.decode('utf-8').strip()
            logging.debug(f"{tool} is installed at: {tool_path}")
            
        except subprocess.CalledProcessError:
            missing_tools.append((tool, package))
            logging.debug(f"{tool} not found in PATH")
        except Exception as e:
            missing_tools.append((tool, package))
            logging.debug(f"{tool} An error occurred while checking: {e}")
    
    if missing_tools:
        logging.error(f"Missing necessary tools: {', '.join([tool for tool, _ in missing_tools])}")
        logging.error("Please install the missing tools before running the program")
        
        # Give specific installation suggestions
        apt_packages = set()
        for tool, package in missing_tools:
            if tool == 'recode_pdf':
                logging.error("Install recode_pdf: pipx install archive-pdf-tools")
            else:
                apt_packages.add(package)
        
        if apt_packages:
            logging.error(f"Install using apt: sudo apt install {' '.join(apt_packages)}")
        
        return False
    
    logging.info("All necessary tools installed")
    return True

def get_current_timestamp():
    """Get the current timestamp string."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
