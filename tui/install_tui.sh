#!/bin/bash

echo "Installing TUI Client for Gemini Web Wrapper..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r tui_requirements.txt

# Make the TUI client executable
chmod +x tui_client.py

echo "Installation complete!"
echo ""
echo "Usage:"
echo "  python3 tui_client.py                    # Connect to localhost:8000"
echo "  python3 tui_client.py http://other-host:8000  # Connect to custom host"
echo ""
echo "Make sure your Gemini Web Wrapper API is running before starting the TUI client."