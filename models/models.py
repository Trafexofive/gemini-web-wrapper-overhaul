# (Coloque no início do seu arquivo, junto com os outros imports e modelos)
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional, Union
import uuid
import time

# --- Modelos Pydantic para Conteúdo Multi-Modal ---
class TextBlock(BaseModel):
    type: Literal["text"]
    text: str

class ImageUrlDetail(BaseModel):
    # Aceita strings genéricas, podem ser URL http/https ou data URI
    url: str
    # detail: Optional[Literal["low", "high", "auto"]] = "auto" # Campo opcional OpenAI

class ImageUrlBlock(BaseModel):
    type: Literal["image_url"]
    image_url: ImageUrlDetail

# O conteúdo da mensagem pode ser string OU uma lista de blocos de texto/imagem
ContentType = Union[str, List[Union[TextBlock, ImageUrlBlock]]]

class OpenAIMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: ContentType
    name: Optional[str] = None # Campo opcional OpenAI

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[OpenAIMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False # Mantendo caso queira implementar depois

# --- Modelos Pydantic de Resposta (sem grandes alterações) ---
class Choice(BaseModel):
    index: int = 0
    message: OpenAIMessage # Note: a resposta ainda será formatada como texto simples
    finish_reason: Optional[Literal["stop", "length"]] = "stop"

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Usage = Field(default_factory=Usage)
    system_fingerprint: Optional[str] = None
