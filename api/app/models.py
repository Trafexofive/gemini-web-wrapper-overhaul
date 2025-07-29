# app/models.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Literal, Optional, Union, Dict, Any
import uuid
import time
from datetime import datetime

# Import central ALLOWED_MODES definition
from app.config import ALLOWED_MODES

# --- Authentication Models ---
class User(BaseModel):
    id: str
    email: EmailStr
    username: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
    expires_in: int = 3600  # 1 hour

class TokenData(BaseModel):
    user_id: Optional[str] = None

class APIKey(BaseModel):
    id: str
    user_id: str
    name: str
    key_hash: str
    is_active: bool = True
    created_at: datetime
    last_used: Optional[datetime] = None

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only shown once on creation
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None

class APIKeyList(BaseModel):
    keys: List[APIKeyResponse]

# --- Modelos Pydantic para Conteúdo Multi-Modal ---
class TextBlock(BaseModel): 
    type: Literal["text"] = "text"
    text: str

class ImageUrlDetail(BaseModel): 
    url: str

class ImageUrlBlock(BaseModel): 
    type: Literal["image_url"] = "image_url"
    image_url: ImageUrlDetail

ContentType = Union[str, List[Union[TextBlock, ImageUrlBlock]]]

class OpenAIMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: ContentType
    name: Optional[str] = None

class OriginalChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[OpenAIMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[OpenAIMessage]
    temperature: Optional[float] = None

# --- Modelos Pydantic de Resposta ---
class Choice(BaseModel): 
    index: int = 0
    message: OpenAIMessage
    finish_reason: Optional[Literal["stop", "length"]] = "stop"

class Usage(BaseModel): 
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class OriginalChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Usage = Field(default_factory=Usage)
    system_fingerprint: Optional[str] = None

class ChatCompletionResponse(OriginalChatCompletionResponse):
    chat_id: str = Field(..., description="ID of the chat session used for this response.")

# --- Modelos Pydantic Específicos da API ---
class CreateChatRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    # Use imported ALLOWED_MODES for validation
    mode: Optional[ALLOWED_MODES] = "Default" # Default if not sent

class ChatInfo(BaseModel):
    chat_id: str
    description: str | None
    mode: str | None # Mode can be null if not defined or if it's 'Default' conceptually

class UpdateChatModeRequest(BaseModel):
    # Receive the new mode, validated by imported ALLOWED_MODES
    mode: ALLOWED_MODES

class Message(BaseModel):
    """Represents a single message in a chat conversation."""
    id: str
    chat_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class MessageCreate(BaseModel):
    """Request model for creating a new message."""
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    role: str
    content: str
    timestamp: datetime

class ChatHistory(BaseModel):
    """Represents the full chat history for a conversation."""
    chat_id: str
    messages: List[MessageResponse]
    total_messages: int

class SetActiveChatRequest(BaseModel):
    chat_id: Optional[str] = None

class GetActiveChatResponse(BaseModel):
    active_chat_id: Optional[str] = None