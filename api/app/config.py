# app/config.py
from typing import Literal
import os
import secrets

# --- Database ---
# Using aiosqlite for async access
DATABASE_URL = "/app/data/chat_sessions.db"  # Direct path for aiosqlite

# --- Gemini Settings ---
GEMINI_MODEL_NAME = "gemini-2.5-exp-advanced" # Or your preferred model

# --- JWT Settings ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

# --- Chat Modes ---
# Defines the allowed mode names for validation purposes.
# The actual system prompt text associated with these modes is handled by the ChatService,
# likely by importing from the prompts module.
ALLOWED_MODES = Literal["Default", "Code", "Architect", "Debug", "Ask"]