#!/bin/bash

echo "Starting Gemini Web Wrapper API..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import fastapi, uvicorn" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Start the API server
echo "Starting API server on http://localhost:8000"
echo "Press Ctrl+C to stop"
python3 main.py