import os
import sys

# Add the app directory to Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app
from app import app as application

# Ensure the uploads directory exists
uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

if __name__ == '__main__':
    application.run()
