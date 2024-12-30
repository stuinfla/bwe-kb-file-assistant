#!/bin/bash

# Kill any existing process on port 5002
lsof -ti:5002 | xargs kill -9 2>/dev/null

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start the application
python3 app.py &

# Wait for the app to start
sleep 2

# Open the app in browser
open http://localhost:5002

# Print success message
echo "Application started! Visit http://localhost:5002"
