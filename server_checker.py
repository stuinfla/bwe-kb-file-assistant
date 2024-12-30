import requests
import subprocess
import sys
import time
import webbrowser
import logging
import psutil
import os
from bs4 import BeautifulSoup
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServerVerifier:
    def __init__(self, port=5002):
        self.port = port
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.required_elements = [
            'BWE Chatbot Knowledge Base',
            'Financial Reports',
            'Building Management'
        ]
        self.required_files = [
            'app.py',
            'templates/index.html',
            'templates/base.html',
            'static/images/bwe-logo.jpg'
        ]

    def check_dependencies(self):
        """Check if all required files exist"""
        missing_files = []
        for file in self.required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Missing required files: {', '.join(missing_files)}")
            return False
        return True

    def kill_existing_processes(self):
        """Kill any existing processes on the port"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and str(self.port) in ' '.join(cmdline):
                        logger.info(f"Killing process {proc.info['pid']} using port {self.port}")
                        psutil.Process(proc.info['pid']).terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            time.sleep(2)  # Wait for processes to terminate
            return True
        except Exception as e:
            logger.error(f"Error killing processes: {str(e)}")
            return False

    def verify_page_content(self):
        """Verify that the page loads with expected content"""
        try:
            response = requests.get(self.base_url)
            if response.status_code != 200:
                logger.error(f"Server returned status code {response.status_code}")
                return False

            soup = BeautifulSoup(response.text, 'html.parser')
            missing_elements = []
            
            for element in self.required_elements:
                if element not in response.text:
                    missing_elements.append(element)
            
            if missing_elements:
                logger.error(f"Missing required elements: {', '.join(missing_elements)}")
                return False
                
            logger.info("✅ Page content verified successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Error accessing server: {str(e)}")
            return False

    def verify_file_access(self):
        """Verify that files can be accessed from the knowledge base"""
        try:
            response = requests.get(f"{self.base_url}/debug_files")
            if response.status_code != 200:
                logger.error("Failed to access files endpoint")
                return False
            
            files = response.json()
            if not files:
                logger.error("No files found in knowledge base")
                return False
                
            logger.info(f"✅ Successfully accessed {len(files)} files from knowledge base")
            return True
        except requests.RequestException as e:
            logger.error(f"Error accessing files: {str(e)}")
            return False

    def run_verification(self):
        """Run all verification checks"""
        logger.info("Starting server verification...")
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            return False
        logger.info("✅ Dependencies verified")
        
        # Step 2: Kill existing processes
        if not self.kill_existing_processes():
            return False
        logger.info("✅ Port cleared successfully")
        
        # Step 3: Start the server
        try:
            subprocess.Popen([sys.executable, 'app.py'])
            time.sleep(3)  # Wait for server to start
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            return False
        
        # Step 4: Verify page content
        retry_count = 0
        while retry_count < 3:
            if self.verify_page_content():
                break
            retry_count += 1
            time.sleep(2)
        else:
            logger.error("Failed to verify page content after 3 attempts")
            return False
        
        # Step 5: Verify file access
        if not self.verify_file_access():
            return False
        
        # Step 6: Open in browser
        webbrowser.open(self.base_url)
        logger.info("✅ Server verification completed successfully")
        logger.info(f"Application is running at {self.base_url}")
        return True

def main():
    verifier = ServerVerifier()
    if not verifier.run_verification():
        logger.error("❌ Server verification failed")
        sys.exit(1)
    logger.info("Server is running and verified. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    main()
