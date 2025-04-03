# models.py
from pydantic import BaseModel, Field
# <<< MODIFICADO: Adicionado Literal para validar modos >>>
from typing import List, Literal, Optional, Union, Dict, Any
import uuid
import time

# --- Constantes de Modos (opcional, mas bom para referência) ---
# Poderia carregar de um config, mas vamos definir aqui por enquanto
ALLOWED_MODES = Literal["Default", "Code", "Architect", "Debug", "Ask"]

# --- Modelos Pydantic para Conteúdo Multi-Modal ---
# (TextBlock, ImageUrlDetail, ImageUrlBlock, ContentType - iguais a antes)
class TextBlock(BaseModel): type: Literal["text"]; text: str
class ImageUrlDetail(BaseModel): url: str
class ImageUrlBlock(BaseModel): type: Literal["image_url"]; image_url: ImageUrlDetail
ContentType = Union[str, List[Union[TextBlock, ImageUrlBlock]]]

class OpenAIMessage(BaseModel):
    role: Literal["user", "assistant", "system"]; content: ContentType; name: Optional[str] = None

class OriginalChatCompletionRequest(BaseModel):
    model: Optional[str] = None; messages: List[OpenAIMessage]; temperature: Optional[float] = None
    max_tokens: Optional[int] = None; stream: Optional[bool] = False

# --- Modelos Pydantic de Resposta ---
class Choice(BaseModel): index: int = 0; message: OpenAIMessage; finish_reason: Optional[Literal["stop", "length"]] = "stop"
class Usage(BaseModel): prompt_tokens: int = 0; completion_tokens: int = 0; total_tokens: int = 0
class OriginalChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}"); object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time())); model: str; choices: List[Choice]
    usage: Usage = Field(default_factory=Usage); system_fingerprint: Optional[str] = None

class ChatCompletionResponse(OriginalChatCompletionResponse):
    chat_id: str = Field(..., description="ID of the chat session used for this response.")


# <<< MODIFICADO: Adicionado campo 'mode' >>>
class CreateChatRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    # Usa Literal para validar os modos permitidos, opcional
    mode: Optional[ALLOWED_MODES] = "Default" # Default se não for enviado

# <<< MODIFICADO: Adicionado campo 'mode' >>>
class ChatInfo(BaseModel):
    chat_id: str
    description: str | None
    mode: str | None # O modo pode ser nulo se não foi definido

class UpdateChatModeRequest(BaseModel):
    # Recebe o novo modo, validado pela Literal ALLOWED_MODES
    mode: ALLOWED_MODES
