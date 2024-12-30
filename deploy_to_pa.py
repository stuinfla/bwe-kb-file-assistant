import os
import requests
import time
import json

API_TOKEN = '749bfcf54e952bf2aae0251a96b7fb4fc862ebd0'
USERNAME = 'StuartBWE'
DOMAIN = f'https://{USERNAME}.pythonanywhere.com'
API_BASE = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

def create_web_app():
    print("Creating/updating web app configuration...")
    response = requests.post(
        f'{API_BASE}/webapps/',
        headers=HEADERS,
        json={
            'domain_name': f'{USERNAME}.pythonanywhere.com',
            'python_version': '3.9',
        }
    )
    if response.status_code in [200, 201]:
        print("Web app configuration created/updated successfully")
    else:
        print(f"Web app already exists or error: {response.status_code}")

def update_wsgi_file():
    print("Updating WSGI configuration...")
    wsgi_content = f'''import os
import sys

path = '/home/{USERNAME}/bwe_assistant'
if path not in sys.path:
    sys.path.append(path)

from wsgi import application
'''
    response = requests.put(
        f'{API_BASE}/webapps/{USERNAME}.pythonanywhere.com/wsgi',
        headers=HEADERS,
        json={'content': wsgi_content}
    )
    if response.status_code == 200:
        print("WSGI configuration updated successfully")
    else:
        print(f"Error updating WSGI: {response.status_code}")

def create_virtualenv():
    print("Creating virtual environment...")
    response = requests.post(
        f'{API_BASE}/webapps/{USERNAME}.pythonanywhere.com/virtualenv/',
        headers=HEADERS,
        json={'python_version': '3.9'}
    )
    if response.status_code in [200, 201]:
        print("Virtual environment created successfully")
    else:
        print(f"Virtual environment already exists or error: {response.status_code}")

def update_static_files():
    print("Configuring static files...")
    response = requests.put(
        f'{API_BASE}/webapps/{USERNAME}.pythonanywhere.com/static_files/',
        headers=HEADERS,
        json={
            '/static/': '/home/StuartBWE/bwe_assistant/static',
        }
    )
    if response.status_code == 200:
        print("Static files configured successfully")
    else:
        print(f"Error configuring static files: {response.status_code}")

def reload_web_app():
    print("Reloading web app...")
    response = requests.post(
        f'{API_BASE}/webapps/{USERNAME}.pythonanywhere.com/reload/',
        headers=HEADERS
    )
    if response.status_code == 200:
        print("Web app reloaded successfully")
    else:
        print(f"Error reloading web app: {response.status_code}")

def main():
    # Create web app
    create_web_app()
    time.sleep(2)  # Give PA time to process

    # Update WSGI
    update_wsgi_file()
    time.sleep(2)

    # Create virtualenv
    create_virtualenv()
    time.sleep(2)

    # Update static files
    update_static_files()
    time.sleep(2)

    # Reload the web app
    reload_web_app()

    print(f"\nDeployment completed! Your app should be available at: {DOMAIN}")
    print("Note: You'll need to use the PythonAnywhere web console to:")
    print("1. Upload your code files")
    print("2. Install requirements using: pip install -r requirements.txt")
    print("3. Set up your environment variables in the Web tab")

if __name__ == '__main__':
    main()
