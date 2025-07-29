# app/routers/chats.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import aiosqlite

# Import the new service
from app.services.chat_service_hybrid import ChatServiceHybrid
from app.models import (
    ChatInfo, CreateChatRequest, UpdateChatModeRequest, 
    SetActiveChatRequest, GetActiveChatResponse,
    ChatCompletionRequest, ChatCompletionResponse, OpenAIMessage, ALLOWED_MODES, User
)
from app.routers.dependencies import get_db, get_chat_service
from app.routers.auth import get_current_user_any

router = APIRouter(prefix="/v1/chats", tags=["Chats"])

@router.get("/test-simple", response_model=dict)
async def test_simple():
    """Simple test endpoint without authentication."""
    print("DEBUG: test_simple endpoint called")
    return {"message": "Simple test working"}

@router.get("/test-auth", response_model=dict)
async def test_auth(
    current_user: User = Depends(get_current_user_any)
):
    """Test endpoint to verify authentication is working."""
    print(f"DEBUG: test_auth endpoint called for user: {current_user.username}")
    return {"message": "Authentication working", "user": current_user.username}

@router.get("/", response_model=List[ChatInfo])
async def list_chats(
    db: aiosqlite.Connection = Depends(get_db),
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """List all available chat sessions."""
    return await service.list_chats(db)

@router.post("/", response_model=dict)
async def create_chat(
    request: CreateChatRequest,
    db: aiosqlite.Connection = Depends(get_db),
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """Create a new chat session."""
    chat_id = await service.create_chat(db, request.description, request.mode)
    return {"chat_id": chat_id, "message": f"Chat session created with ID: {chat_id}"}

@router.post("/active", response_model=dict)
async def set_active_chat(
    payload: SetActiveChatRequest,
    db: aiosqlite.Connection = Depends(get_db),
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """Set the globally active chat session."""
    await service.set_active_chat(db, payload.chat_id)
    if payload.chat_id:
        return {"message": f"Active chat session set to {payload.chat_id}"}
    else:
        return {"message": "Active chat session deactivated."}

@router.get("/active", response_model=GetActiveChatResponse)
async def get_active_chat(
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """Get the currently active chat session ID."""
    active_chat_id = service.get_active_chat()
    return GetActiveChatResponse(active_chat_id=active_chat_id)

@router.put("/{chat_id}/mode", response_model=dict)
async def update_chat_mode(
    chat_id: str,
    payload: UpdateChatModeRequest,
    db: aiosqlite.Connection = Depends(get_db),
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """Update the mode for a specific chat session."""
    await service.update_chat_mode(db, chat_id, payload.mode)
    # If successful, return confirmation message. Service raises HTTPException on error.
    return {"message": f"Mode for Chat {chat_id} updated to '{payload.mode}'. System prompt will be resent."}

@router.delete("/{chat_id}", response_model=dict)
async def delete_chat(
    chat_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """Delete a chat session."""
    await service.delete_chat(db, chat_id)
    return {"message": f"Chat session {chat_id} deleted successfully."}

@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request_body: ChatCompletionRequest,
    db: aiosqlite.Connection = Depends(get_db),
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """
    Handle chat completion requests.
    
    This endpoint handles message history context implicitly (managed by the backend),
    so clients only need to send the current user message(s) they want to process.
    The backend will:
    1. Store the user message in the database
    2. Send it to the active Gemini chat session
    3. Store the assistant's response in the database
    4. Return the response in OpenAI-compatible format
    """
    print("Router: POST /v1/chat/completions received")
    # We pass only the list of messages from the validated request body.
    response = await service.handle_completion(db=db, user_messages=request_body.messages)
    return response

# New endpoints for client mode switching
@router.post("/client-mode", response_model=dict)
async def switch_client_mode(
    mode: str,
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """Switch between free and paid client modes."""
    if mode not in ["free", "paid"]:
        raise HTTPException(status_code=400, detail="Mode must be 'free' or 'paid'")
    
    success = await service.switch_client_mode(mode)
    if success:
        return {
            "message": f"Successfully switched to {mode} mode",
            "mode": mode,
            "description": "free" if mode == "free" else "paid (API key required)"
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to switch to {mode} mode")

@router.get("/client-mode", response_model=dict)
async def get_client_mode(
    service: ChatServiceHybrid = Depends(get_chat_service),
    current_user: User = Depends(get_current_user_any)
):
    """Get the current client mode."""
    current_mode = service.get_current_client_mode()
    return {
        "mode": current_mode,
        "description": "free (unlimited, uses browser cookies)" if current_mode == "free" else "paid (API key, pay per request)"
    }