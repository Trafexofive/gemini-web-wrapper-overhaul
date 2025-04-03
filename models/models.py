from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional, Union
import uuid
import time

class TextBlock(BaseModel):
    type: Literal["text"]
    text: str

class ImageUrlDetail(BaseModel):
    url: str

class ImageUrlBlock(BaseModel):
    type: Literal["image_url"]
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

class Choice(BaseModel):
    index: int = 0
    message: OpenAIMessage
    finish_reason: Optional[Literal["stop", "length"]] = "stop"

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class OriginalChatCompletionResponse(BaseModel): # (igual a antes)
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Usage = Field(default_factory=Usage)
    system_fingerprint: Optional[str] = None


class ChatCompletionRequest(OriginalChatCompletionRequest):
    chat_id: str | None = Field(None, description="ID of the chat session to continue. If None, a new chat will be created.")

class ChatCompletionResponse(OriginalChatCompletionResponse):
    chat_id: str = Field(..., description="ID of the chat session used or created for this response.")

class CreateChatRequest(BaseModel):
    description: Optional[str] = Field(None, description="Descrição opcional para o novo chat.", max_length=255) # Limitar tamanho

# <<< NOVO: Modelo para a resposta de GET /v1/chats >>>
class ChatInfo(BaseModel):
    chat_id: str
    description: str | None # Descrição pode ser nula
