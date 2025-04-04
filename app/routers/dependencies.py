# app/routers/dependencies.py
from typing import AsyncGenerator, Optional
import aiosqlite
from fastapi import Request, HTTPException, Depends

from app.services.chat_service import ChatService
from app.config import DATABASE_URL # Used to get path if needed, though pool should be managed

# Database Connection Dependency
# This dependency assumes a single connection 'db_conn' is managed
# in app.state by the lifespan function.
# For production, using a connection pool (like aiopg or asyncpg with adapters,
# or a library like databases/encode) would be more robust.

async def get_db(request: Request) -> aiosqlite.Connection:
    """
    FastAPI dependency that provides the shared aiosqlite connection
    managed by the application's lifespan context.
    """
    db_conn = getattr(request.app.state, "db_conn", None)
    if db_conn is None:
        print("ERROR: get_db dependency - Database connection not found in app.state!")
        # Raising 503 Service Unavailable is appropriate here
        raise HTTPException(status_code=503, detail="Database service unavailable.")
    # We yield the connection managed by lifespan, no explicit open/close here.
    # Lifespan is responsible for the connection lifecycle.
    # For a pool-based approach, this would acquire and release a connection.
    return db_conn


# Service Dependency
def get_chat_service(request: Request) -> ChatService:
    """
    FastAPI dependency that retrieves the singleton ChatService instance
    stored in the application's state by the lifespan function.
    """
    chat_service = getattr(request.app.state, "chat_service", None)
    if chat_service is None:
        print("ERROR: get_chat_service dependency - ChatService not found in app.state!")
        # Raising 503 Service Unavailable is appropriate
        raise HTTPException(status_code=503, detail="Chat service unavailable.")
    return chat_service

# Convenience dependency combining DB and Service
# Not strictly necessary but can simplify endpoint signatures
# class CommonDeps:
#     def __init__(
#         self,
#         service: ChatService = Depends(get_chat_service),
#         db: aiosqlite.Connection = Depends(get_db),
#     ):
#         self.service = service
#         self.db = db