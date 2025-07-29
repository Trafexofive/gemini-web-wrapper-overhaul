# app/routers/messages.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import aiosqlite

from app.models import ChatHistory, MessageResponse, MessageCreate
from app.repositories.message_repository import SqliteMessageRepository
from app.routers.dependencies import get_db, get_message_repository

router = APIRouter(prefix="/v1/messages", tags=["Messages"])

@router.get("/{chat_id}", response_model=ChatHistory)
async def get_chat_messages(
    chat_id: str,
    limit: int = 100,
    db: aiosqlite.Connection = Depends(get_db),
    message_repo: SqliteMessageRepository = Depends(get_message_repository)
):
    """Get all messages for a specific chat."""
    try:
        messages = await message_repo.get_messages_by_chat_id(db, chat_id, limit)
        total_count = await message_repo.get_message_count(db, chat_id)
        
        message_responses = [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            )
            for msg in messages
        ]
        
        return ChatHistory(
            chat_id=chat_id,
            messages=message_responses,
            total_messages=total_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )

@router.post("/{chat_id}", response_model=MessageResponse)
async def create_message(
    chat_id: str,
    message_data: MessageCreate,
    db: aiosqlite.Connection = Depends(get_db),
    message_repo: SqliteMessageRepository = Depends(get_message_repository)
):
    """Create a new message in a chat."""
    try:
        message = await message_repo.create_message(db, chat_id, message_data)
        await db.commit()
        
        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
        )

@router.delete("/{chat_id}")
async def delete_chat_messages(
    chat_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    message_repo: SqliteMessageRepository = Depends(get_message_repository)
):
    """Delete all messages for a specific chat."""
    try:
        success = await message_repo.delete_messages_by_chat_id(db, chat_id)
        if success:
            await db.commit()
            return {"message": f"All messages for chat {chat_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete messages"
            )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete messages: {str(e)}"
        )