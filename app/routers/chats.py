# app/routers/chats.py
from typing import List, Dict, Optional
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Path as FastApiPath, Request, status
from pydantic import BaseModel # For local request/response models if needed

# Import application models
from app.models import (
    ChatInfo, CreateChatRequest, UpdateChatModeRequest,
    OriginalChatCompletionRequest, ChatCompletionResponse, OpenAIMessage, ALLOWED_MODES
)
# Import service and dependencies
from app.services.chat_service import ChatService
from app.routers.dependencies import get_chat_service, get_db

# Define router
router = APIRouter(
    prefix="/v1",
    tags=["Chat Sessions"], # Group endpoints in OpenAPI docs
)

# --- Router-specific Models ---
# These models were implicitly defined or used in the old gemini_api.py but not in models.py
class SetActiveChatRequest(BaseModel):
    """Request body for setting the active chat."""
    chat_id: Optional[str] = None # Allow null to deactivate

class GetActiveChatResponse(BaseModel):
    """Response body for getting the active chat."""
    active_chat_id: Optional[str]


# --- Chat Session Endpoints ---

@router.get("/chats", response_model=List[ChatInfo])
async def list_chats_endpoint(
    service: ChatService = Depends(get_chat_service),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Retrieve a list of all existing chat sessions, including their ID,
    description, and mode.
    """
    print("Router: GET /v1/chats")
    # The service method handles fetching from the repository
    # Exceptions (like DB errors wrapped in HTTPException) from the service layer
    # will be automatically handled by FastAPI.
    return await service.list_chats(db)


@router.post("/chats", response_model=str, status_code=status.HTTP_201_CREATED)
async def create_chat_endpoint(
    payload: CreateChatRequest,
    service: ChatService = Depends(get_chat_service),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Create a new chat session. Requires an optional description and mode
    (defaults to 'Default'). Returns the ID of the newly created chat session.
    """
    print(f"Router: POST /v1/chats (Desc: {payload.description or 'N/A'}, Mode: {payload.mode or 'Default'})")
    # The service handles mode validation, interaction with Gemini client (via wrapper)
    # for initial metadata, saving to DB (via repository), and updating cache.
    new_chat_id = await service.create_chat(
        db=db,
        description=payload.description,
        mode=payload.mode # Pass the mode (Optional[ALLOWED_MODES])
    )
    return new_chat_id # Return the generated chat_id string


@router.post("/chats/active", response_model=Dict[str, str])
async def set_active_chat_endpoint(
    payload: SetActiveChatRequest, # Use the locally defined model here
    service: ChatService = Depends(get_chat_service),
    db: aiosqlite.Connection = Depends(get_db) # Add DB dependency
):
    """
    Set the globally active chat session ID. This ID will be used for all
    subsequent requests to `/v1/chat/completions`.
    Send `{"chat_id": null}` or `{}` in the body to deactivate the active chat.
    """
    print(f"Router: POST /v1/chats/active (Setting ID to: {payload.chat_id})")
    # Service method validates the chat_id against its cache and updates state.
    # Service handles validation, prompt sending (if needed), and state updates
    await service.set_active_chat(db=db, chat_id=payload.chat_id) # Await the async call and pass db

    if payload.chat_id:
        return {"message": f"Active chat session set to {payload.chat_id}"}
    else:
        return {"message": "Active chat session deactivated."}


@router.get("/chats/active", response_model=GetActiveChatResponse)
async def get_active_chat_endpoint(
    service: ChatService = Depends(get_chat_service)
    # No DB connection needed
):
    """
    Retrieve the ID of the currently active chat session.
    Returns `null` if no chat session is currently active.
    """
    print("Router: GET /v1/chats/active")
    active_id = service.get_active_chat()
    return GetActiveChatResponse(active_chat_id=active_id)


@router.put("/chats/{chat_id}/mode", response_model=Dict[str, str])
async def update_chat_mode_endpoint(
    payload: UpdateChatModeRequest,
    chat_id: str = FastApiPath(..., title="Chat ID", description="The unique identifier of the chat session to update."),
    service: ChatService = Depends(get_chat_service),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Update the mode (e.g., 'Code', 'Architect') for a specific chat session.
    Changing the mode also resets the flag indicating whether the system prompt
    has been sent, ensuring it's included in the next completion request.
    """
    print(f"Router: PUT /v1/chats/{chat_id}/mode (New Mode: {payload.mode})")
    # Service validates chat existence in cache, calls repo to update DB, updates cache.
    await service.update_chat_mode(db=db, chat_id=chat_id, new_mode=payload.mode)
    # If successful, return confirmation message. Service raises HTTPException on error.
    return {"message": f"Mode for Chat {chat_id} updated to '{payload.mode}'. System prompt will be resent."}


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_endpoint(
    chat_id: str = FastApiPath(..., title="Chat ID", description="The unique identifier of the chat session to delete."),
    service: ChatService = Depends(get_chat_service),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Delete a specific chat session permanently from the database and cache.
    If the deleted chat was the active one, the active chat will be deactivated.
    """
    print(f"Router: DELETE /v1/chats/{chat_id}")
    # Service validates existence in cache, calls repo to delete from DB, removes from cache,
    # and updates active ID state if necessary. Raises HTTPException on errors.
    await service.delete_chat(db=db, chat_id=chat_id)
    # No response body is sent for 204 No Content status code.


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions_endpoint(
    # FastAPI automatically validates the incoming body against this Pydantic model
    request_body: OriginalChatCompletionRequest,
    service: ChatService = Depends(get_chat_service),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Processes a chat completion request using the currently **active** chat session.
    This endpoint handles message history context implicitly (managed by the backend),
    prepends system prompts based on the active chat's mode (if not already sent),
    processes included images (base64 data URIs), interacts with the Gemini API,
    and updates the chat session's state.

    **Requires an active chat session to be set via `POST /v1/chats/active` first.**
    """
    print("Router: POST /v1/chat/completions received")
    # The service's handle_completion method contains the core complex logic.
    # We pass only the list of messages from the validated request body.
    response = await service.handle_completion(db=db, user_messages=request_body.messages)
    # Service method returns the fully formed ChatCompletionResponse or raises HTTPException.
    return response