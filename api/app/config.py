# app/config.py
from typing import Literal

# --- Database ---
# Using aiosqlite for async access
DATABASE_URL = "sqlite+aiosqlite:///./chat_sessions.db" # Relative path

# --- Gemini Settings ---
GEMINI_MODEL_NAME = "gemini-2.5-exp-advanced" # Or your preferred model

# --- Chat Modes ---
# Defines the allowed mode names for validation purposes.
# The actual system prompt text associated with these modes is handled by the ChatService,
# likely by importing from the prompts module.
ALLOWED_MODES = Literal["Default", "Code", "Architect", "Debug", "Ask"]