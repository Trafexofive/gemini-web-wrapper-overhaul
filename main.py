#!/usr/bin/env python3
"""
Main entry point for the Gemini Web Wrapper API
This file allows running the API from the root directory while keeping backend files in ./api
"""

import sys
import os
from pathlib import Path

# Add the api directory to Python path
api_dir = Path(__file__).parent / "api"
sys.path.insert(0, str(api_dir))

# Import and run the FastAPI app from api/app/main.py
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)