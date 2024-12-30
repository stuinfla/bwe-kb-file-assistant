#!/bin/bash

# Kill any existing processes on port 8000
echo "Killing any existing processes on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "Starting custom server..."
python3 custom_server.py
