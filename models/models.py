import uuid
import time
from pydantic import BaseModel, Field, ValidationError
from typing import List, Literal, Optional, Union

class ContentBlock(BaseModel):
    type: str
    text: str

class OpenAIMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: Union[str, List[ContentBlock]]

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None # Client might suggest a model
    messages: List[OpenAIMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class Choice(BaseModel):
    index: int = 0
    message: OpenAIMessage
    finish_reason: Optional[Literal["stop", "length"]] = "stop"

class Usage(BaseModel):
    prompt_tokens: int = 0 # Note: Actual token usage is not retrieved from gemini-webapi
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str # The model actually used
    choices: List[Choice]
    usage: Usage = Field(default_factory=Usage)
    system_fingerprint: Optional[str] = None