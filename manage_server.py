import os
import signal
import subprocess
import sys
import time
import webbrowser
import psutil
import requests
from pathlib import Path
import logging
import socket
import threading
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServerManager:
    def __init__(self, port=5002, startup_timeout=10, max_retries=3):
        self.port = port
        self.startup_timeout = startup_timeout
        self.max_retries = max_retries
        self.server_process = None
        self.base_dir = Path(__file__).parent
        
        # List of commands that are safe to run without user confirmation
        self.safe_commands = {
            'python3': True,  # Safe to run Python scripts
            'kill': True,     # Safe to kill processes
            'lsof': True,     # Safe to list open files/ports
            'ps': True        # Safe to list processes
        }

    def is_command_safe(self, command):
        """Check if a command is in the safe list."""
        return self.safe_commands.get(command, False)

    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        required_files = [
            ('app.py', 'Main application file'),
            ('templates/base.html', 'Base template'),
            ('templates/index.html', 'Index template'),
            ('templates/category.html', 'Category template'),
            ('static/images/bwe-logo.jpg', 'BWE logo image')
        ]

        missing_files = []
        for file_path, description in required_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                missing_files.append((file_path, description))

        if missing_files:
            logger.error("Missing required files:")
            for file_path, description in missing_files:
                logger.error(f"  - {file_path} ({description})")
            return False
        return True

    def find_python_processes(self):
        """Find all Python processes that might be our server."""
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('app.py' in arg for arg in cmdline):
                        python_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return python_processes

    def is_port_in_use(self):
        """Check if the port is already in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', self.port)) == 0

    def kill_process_on_port(self):
        """Kill any process running on the target port."""
        try:
            # Find process using the port
            result = subprocess.run(['lsof', '-i', f':{self.port}'], 
                                 capture_output=True, 
                                 text=True)
            
            if result.stdout:
                # Extract PIDs (skip header line)
                pids = []
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        pid = line.split()[1]
                        if pid not in pids:
                            pids.append(pid)
                
                if pids:
                    # Kill each process
                    kill_cmd = ['kill', '-9'] + pids
                    subprocess.run(kill_cmd, check=True)
                    logger.info(f"Killed processes: {', '.join(pids)}")
                    time.sleep(1)  # Wait for processes to fully terminate
                    return True
            
            return not self.is_port_in_use()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error killing process on port {self.port}: {str(e)}")
            return False

    def verify_server_running(self):
        """Verify the server is running and functioning correctly."""
        max_retries = 10
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # Check if server responds
                response = requests.get(f"http://127.0.0.1:{self.port}")
                if response.status_code != 200:
                    logger.warning(f"Server responded with status code {response.status_code}")
                    time.sleep(retry_delay)
                    continue

                # Parse the response content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for error messages
                error_alert = soup.find('div', class_='alert-warning')
                if error_alert:
                    error_message = error_alert.get_text(strip=True)
                    logger.error(f"Application error detected: {error_message}")
                    return False

                # Check if categories are loaded
                category_items = soup.find_all('div', class_='category-item')
                if not category_items:
                    logger.error("No categories found in the response")
                    return False

                # Check if any categories have files
                file_counts = [int(badge.get_text(strip=True)) for badge in soup.find_all('span', class_='badge')]
                total_files = sum(file_counts)
                
                if total_files == 0:
                    logger.error("No files found in any category. Application is not loading data correctly.")
                    return False

                logger.info(f"Server verified running with {len(category_items)} categories and {total_files} total files")
                return True

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Server not responding yet: {str(e)}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to verify server: {str(e)}")
                    return False

        return False

    def monitor_server_health(self):
        """Monitor server health and data integrity."""
        try:
            response = requests.get(f"http://127.0.0.1:{self.port}")
            if response.status_code != 200:
                logger.error(f"Server health check failed: Status code {response.status_code}")
                return False

            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for application errors
            error_alert = soup.find('div', class_='alert-warning')
            if error_alert:
                error_message = error_alert.get_text(strip=True)
                logger.error(f"Application error detected: {error_message}")
                return False

            # Verify data integrity
            file_counts = [int(badge.get_text(strip=True)) for badge in soup.find_all('span', class_='badge')]
            total_files = sum(file_counts)
            
            if total_files == 0:
                logger.error("Health check failed: No files found in categories")
                return False

            return True

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def heartbeat_check(self):
        """Periodically check server status and content."""
        while True:
            time.sleep(10)  # Check every 10 seconds
            if not self.verify_server_running():
                logger.error("Heartbeat check failed, attempting to restart server...")
                self.stop_server()
                self.start_server()
                break

    def start_server(self):
        """Start the Flask server and verify it's running correctly."""
        # Check dependencies first
        if not self.check_dependencies():
            logger.error("Missing required dependencies. Cannot start server.")
            return False

        # Kill any existing process on the port
        if not self.kill_process_on_port():
            logger.error(f"Failed to free up port {self.port}")
            return False

        # Start the Flask application
        logger.info(f"Starting server on port {self.port}...")
        
        for attempt in range(self.max_retries):
            try:
                # Start Flask with output redirection
                self.server_process = subprocess.Popen(
                    [sys.executable, 'app.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                    universal_newlines=True
                )
                
                # Start a thread to monitor the output
                def log_output():
                    while True:
                        line = self.server_process.stderr.readline()
                        if not line and self.server_process.poll() is not None:
                            break
                        if line:
                            logger.error(f"Flask error: {line.strip()}")
                
                log_thread = threading.Thread(target=log_output, daemon=True)
                log_thread.start()

                # Verify the server is running
                if self.verify_server_running():
                    # Set up continuous health monitoring
                    def monitor():
                        while True:
                            time.sleep(5)  # Check every 5 seconds
                            if not self.monitor_server_health():
                                logger.error("Server health check failed, restarting...")
                                self.stop_server()
                                self.start_server()
                                break
                    
                    # Start health monitoring in a separate thread
                    monitor_thread = threading.Thread(target=monitor, daemon=True)
                    monitor_thread.start()
                    
                    # Start heartbeat check in a separate thread
                    heartbeat_thread = threading.Thread(target=self.heartbeat_check, daemon=True)
                    heartbeat_thread.start()
                    
                    # Open the browser
                    url = f"http://127.0.0.1:{self.port}"
                    logger.info(f"Opening {url} in browser...")
                    webbrowser.open(url)
                    logger.info("Server started successfully. Press Ctrl+C to stop.")
                    return True
                else:
                    # Check for startup errors
                    if self.server_process.poll() is not None:
                        stdout, stderr = self.server_process.communicate()
                        logger.error(f"Server failed to start. Error output:\n{stderr}")
                        if attempt < self.max_retries - 1:
                            logger.info(f"Retrying... (attempt {attempt + 2}/{self.max_retries})")
                            time.sleep(2)
                            continue
                    else:
                        self.server_process.terminate()
                        try:
                            self.server_process.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            self.server_process.kill()
                            self.server_process.wait()
            except Exception as e:
                logger.error(f"Error starting server: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying... (attempt {attempt + 2}/{self.max_retries})")
                    time.sleep(2)
                    continue

        logger.error("Failed to start server after multiple attempts")
        return False

    def stop_server(self):
        """Stop the server gracefully."""
        if self.server_process:
            logger.info("Shutting down server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't shut down gracefully, forcing...")
                self.server_process.kill()
                self.server_process.wait()
            logger.info("Server stopped")

def main():
    manager = ServerManager()
    
    try:
        if manager.start_server():
            while True:
                time.sleep(1)
                # Check if server is still running
                if manager.server_process.poll() is not None:
                    stdout, stderr = manager.server_process.communicate()
                    logger.error(f"Server stopped unexpectedly. Error output:\n{stderr}")
                    break
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        manager.stop_server()

if __name__ == "__main__":
    main()