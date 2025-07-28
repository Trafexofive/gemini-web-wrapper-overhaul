#!/bin/bash

echo "Starting Gemini Web Wrapper TUI Client..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Navigate to TUI directory
cd tui

# Check if requirements are installed
if ! python3 -c "import textual, httpx, rich" &> /dev/null; then
    echo "Installing TUI dependencies..."
    pip3 install -r tui_requirements.txt
fi

# Get API endpoint from command line or use default
API_ENDPOINT=${1:-http://localhost:8000}

echo "Connecting to API at: $API_ENDPOINT"
echo "Press Ctrl+C to exit"

# Start the TUI client
python3 tui_client.py "$API_ENDPOINT"