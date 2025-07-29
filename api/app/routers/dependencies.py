# app/routers/dependencies.py
from fastapi import Request, HTTPException, status
import aiosqlite
from app.config import DATABASE_URL
from app.services.chat_service_hybrid import ChatServiceHybrid
from app.repositories.message_repository import SqliteMessageRepository

def get_db(request: Request) -> aiosqlite.Connection:
    """
    FastAPI dependency that provides a database connection.
    This connection is shared across the application lifecycle.
    """
    db_conn = getattr(request.app.state, "db_conn", None)
    if db_conn is None:
        print("ERROR: get_db dependency - Database connection not found in app.state!")
        raise HTTPException(status_code=503, detail="Database unavailable.")
    return db_conn

def get_chat_service(request: Request) -> ChatServiceHybrid:
    """
    FastAPI dependency that retrieves the singleton ChatServiceHybrid instance
    stored in the application's state by the lifespan function.
    """
    chat_service = getattr(request.app.state, "chat_service", None)
    if chat_service is None:
        print("ERROR: get_chat_service dependency - ChatServiceHybrid not found in app.state!")
        raise HTTPException(status_code=503, detail="Chat service unavailable.")
    return chat_service

# Message Repository Dependency
def get_message_repository(request: Request) -> SqliteMessageRepository:
    """
    FastAPI dependency that provides a message repository instance.
    """
    return SqliteMessageRepository()