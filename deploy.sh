#!/bin/bash

# Configuration
PA_USERNAME="StuartBWE"
APP_NAME="bwe_assistant"
REMOTE_DIR="/home/$PA_USERNAME/$APP_NAME"
VENV_PATH="/home/$PA_USERNAME/.virtualenvs/$APP_NAME"

# Create directories and virtual environment
ssh $PA_USERNAME@ssh.pythonanywhere.com << EOF
    # Create directories
    mkdir -p $REMOTE_DIR
    mkdir -p $REMOTE_DIR/static
    mkdir -p $REMOTE_DIR/templates
    mkdir -p $REMOTE_DIR/static/images
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        python3 -m venv $VENV_PATH
    fi
    
    # Activate virtual environment and install requirements
    source $VENV_PATH/bin/activate
    pip install flask flask-cors python-dotenv openai werkzeug gunicorn requests
EOF

# Copy files
scp app.py $PA_USERNAME@ssh.pythonanywhere.com:$REMOTE_DIR/
scp wsgi.py $PA_USERNAME@ssh.pythonanywhere.com:$REMOTE_DIR/
scp requirements.txt $PA_USERNAME@ssh.pythonanywhere.com:$REMOTE_DIR/
scp assistant_analyzer.py $PA_USERNAME@ssh.pythonanywhere.com:$REMOTE_DIR/
scp templates/* $PA_USERNAME@ssh.pythonanywhere.com:$REMOTE_DIR/templates/
scp static/images/* $PA_USERNAME@ssh.pythonanywhere.com:$REMOTE_DIR/static/images/

# Configure WSGI file
ssh $PA_USERNAME@ssh.pythonanywhere.com << EOF
    cat > $REMOTE_DIR/wsgi.py << 'END'
import os
import sys

# Add your project directory to the sys.path
path = os.path.expanduser('~/bwe_assistant')
if path not in sys.path:
    sys.path.append(path)

from app import app as application
END

    # Reload the web app
    touch $REMOTE_DIR/wsgi.py
EOF

echo "Deployment completed! Your app should be available at: https://$PA_USERNAME.pythonanywhere.com"
