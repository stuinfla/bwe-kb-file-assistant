import os
import requests
import time
import json
from pathlib import Path

API_TOKEN = '749bfcf54e952bf2aae0251a96b7fb4fc862ebd0'
USERNAME = 'StuartBWE'
DOMAIN = f'https://{USERNAME}.pythonanywhere.com'
API_BASE = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

def create_directories():
    """Create necessary directories on PythonAnywhere."""
    print("Creating directories...")
    
    directories = [
        '/home/StuartBWE/bwe_assistant',
        '/home/StuartBWE/bwe_assistant/static',
        '/home/StuartBWE/bwe_assistant/templates',
        '/home/StuartBWE/bwe_assistant/static/images',
    ]
    
    for directory in directories:
        response = requests.post(
            f'{API_BASE}/files/path{directory}',
            headers=HEADERS
        )
        if response.status_code in [200, 201, 404]:  # 404 means directory already exists
            print(f"Created/verified directory: {directory}")
        else:
            print(f"Error creating directory {directory}: {response.status_code}")

def upload_file(local_path, remote_path):
    """Upload a file to PythonAnywhere."""
    print(f"Uploading {local_path} to {remote_path}...")
    
    try:
        with open(local_path, 'rb') as f:
            content = f.read()
            
        response = requests.post(
            f'{API_BASE}/files/path{remote_path}',
            headers=HEADERS,
            files={'content': content}
        )
        
        if response.status_code in [200, 201]:
            print(f"Successfully uploaded {local_path}")
        else:
            print(f"Error uploading {local_path}: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error uploading {local_path}: {str(e)}")

def configure_webapp():
    """Configure the web app settings."""
    print("Configuring web app...")
    
    config = {
        'python_version': '3.9',
        'virtualenv_path': f'/home/{USERNAME}/.virtualenvs/bwe_assistant',
        'source_directory': f'/home/{USERNAME}/bwe_assistant',
        'working_directory': f'/home/{USERNAME}/bwe_assistant'
    }
    
    response = requests.patch(
        f'{API_BASE}/webapps/{USERNAME}.pythonanywhere.com/config/',
        headers=HEADERS,
        json=config
    )
    
    if response.status_code == 200:
        print("Web app configured successfully")
    else:
        print(f"Error configuring web app: {response.status_code}")
        print(response.text)

def update_wsgi():
    """Update the WSGI configuration file."""
    print("Updating WSGI configuration...")
    
    wsgi_content = f'''import os
import sys

path = '/home/{USERNAME}/bwe_assistant'
if path not in sys.path:
    sys.path.append(path)

from app import app as application

# Load environment variables
os.environ['FLASK_ENV'] = 'production'
'''
    
    # Add environment variables from .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    wsgi_content += f"os.environ['{key}'] = '{value}'\n"
    
    response = requests.patch(
        f'{API_BASE}/files/path/var/www/{USERNAME}_pythonanywhere_com_wsgi.py',
        headers=HEADERS,
        json={'content': wsgi_content}
    )
    
    if response.status_code == 200:
        print("WSGI configuration updated successfully")
    else:
        print(f"Error updating WSGI: {response.status_code}")
        print(response.text)

def reload_webapp():
    """Reload the web app."""
    print("Reloading web app...")
    
    response = requests.post(
        f'{API_BASE}/webapps/{USERNAME}.pythonanywhere.com/reload/',
        headers=HEADERS
    )
    
    if response.status_code == 200:
        print("Web app reloaded successfully")
    else:
        print(f"Error reloading web app: {response.status_code}")
        print(response.text)

def main():
    # Create necessary directories
    create_directories()
    
    # Upload application files
    files_to_upload = [
        ('app.py', '/home/StuartBWE/bwe_assistant/app.py'),
        ('wsgi.py', '/home/StuartBWE/bwe_assistant/wsgi.py'),
        ('requirements.txt', '/home/StuartBWE/bwe_assistant/requirements.txt'),
        ('assistant_analyzer.py', '/home/StuartBWE/bwe_assistant/assistant_analyzer.py'),
    ]
    
    # Upload template files
    template_dir = Path('templates')
    if template_dir.exists():
        for template in template_dir.glob('*.html'):
            remote_path = f'/home/StuartBWE/bwe_assistant/templates/{template.name}'
            files_to_upload.append((str(template), remote_path))
    
    # Upload static files
    static_dir = Path('static/images')
    if static_dir.exists():
        for image in static_dir.glob('*.*'):
            remote_path = f'/home/StuartBWE/bwe_assistant/static/images/{image.name}'
            files_to_upload.append((str(image), remote_path))
    
    # Upload all files
    for local_path, remote_path in files_to_upload:
        upload_file(local_path, remote_path)
    
    # Configure the web app
    configure_webapp()
    
    # Update WSGI configuration
    update_wsgi()
    
    # Reload the web app
    reload_webapp()
    
    print(f"\nDeployment completed! Your app should be available at: {DOMAIN}")

if __name__ == '__main__':
    main()
