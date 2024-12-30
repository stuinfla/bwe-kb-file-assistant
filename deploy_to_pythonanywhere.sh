#!/bin/bash

# Configuration
PA_USERNAME="StuartBWE"
APP_NAME="bwe_assistant"
GITHUB_REPO="https://github.com/yourusername/bwe-assist-updater.git"  # Replace with your GitHub repo

# Create a deployment package
echo "Creating deployment package..."
zip -r deployment.zip . -x "*.git*" "*__pycache__*" "*.env" "*.log" "node_modules/*"

# Upload to Python Anywhere
echo "Uploading to Python Anywhere..."
scp deployment.zip $PA_USERNAME@ssh.pythonanywhere.com:~/$APP_NAME.zip

# SSH commands to set up the app
ssh $PA_USERNAME@ssh.pythonanywhere.com << 'ENDSSH'
    # Create virtual environment if it doesn't exist
    mkvirtualenv --python=/usr/bin/python3.9 $APP_NAME

    # Unzip the deployment package
    rm -rf ~/$APP_NAME
    mkdir -p ~/$APP_NAME
    cd ~/$APP_NAME
    unzip ../$APP_NAME.zip
    rm ../$APP_NAME.zip

    # Install requirements
    workon $APP_NAME
    pip install -r requirements.txt

    # Create necessary directories
    mkdir -p uploads

    # Set up the WSGI configuration
    echo "Setting up WSGI configuration..."
    cat > /var/www/$PA_USERNAME\_pythonanywhere_com_wsgi.py << 'EOF'
import os
import sys

path = '/home/$PA_USERNAME/$APP_NAME'
if path not in sys.path:
    sys.path.append(path)

from wsgi import application
EOF

    # Reload the web app
    touch /var/www/$PA_USERNAME\_pythonanywhere_com_wsgi.py
ENDSSH

echo "Deployment complete! Visit https://$PA_USERNAME.pythonanywhere.com to see your app."
