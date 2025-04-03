import base64
import tempfile
import os
import traceback
import uuid
from contextlib import asynccontextmanager
from typing import List

# Importa Depends para injeção (opcional, mas bom)
from fastapi import FastAPI, HTTPException, Request, Path as FastApiPath, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ValidationError # Importa BaseModel

# Modelos Pydantic (Importa todos necessários, incluindo os novos)
from models.models import (
    TextBlock, ImageUrlBlock, OpenAIMessage, Choice, Usage,
    OriginalChatCompletionRequest, # Usaremos este para /completions
    ChatCompletionResponse,
    CreateChatRequest, ChatInfo # Novos modelos
)
from gemini_webapi import GeminiClient

# Importa o módulo 'db'
import db

# --- Variáveis Globais ---
gemini_client: GeminiClient | None = None
GEMINI_MODEL_NAME = "gemini-2.5-exp-advanced"
# Cache em memória apenas para METADATA (descrição será lida do DB quando necessário)
chat_sessions: dict = {}
ACTIVE_CHAT_ID: str | None = None

# --- Lifespan (Igual ao anterior) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carrega apenas METADATA para o cache chat_sessions
    print("Lifespan: Iniciando aplicação...")
    global gemini_client, chat_sessions
    print("Lifespan: Tentando inicializar DB...")
    db_initialized = await run_in_threadpool(db._init_db_sync)
    if db_initialized:
        print("Lifespan: DB inicializado com sucesso. Verificando db.db_conn imediatamente...")
        if db.db_conn: print(">>> Lifespan Check: OK! db.db_conn NÃO é None logo após init.")
        else: print(">>> !!!!!!! Lifespan Check: FALHOU! db.db_conn É None logo após init !!!!!!!")
        print("Lifespan: Carregando metadados das sessões...")
        # _load_sessions_sync agora carrega só metadata
        loaded_metadata = await run_in_threadpool(db._load_sessions_sync)
        chat_sessions = loaded_metadata # Guarda só metadata no cache
        print(f"Lifespan: Metadados de {len(chat_sessions)} sessões carregados para cache.")
    else:
        print("!!!!!!!! Lifespan: FALHA AO INICIALIZAR DB. Cache de sessão vazio. !!!!!!!!")
        chat_sessions = {}
    print("Lifespan: Tentando inicializar Gemini Client...")
    try:
        temp_client = GeminiClient(proxy=None)
        await temp_client.init(timeout=30, auto_close=False, auto_refresh=True)
        gemini_client = temp_client
        print("Lifespan: Gemini Client inicializado com sucesso.")
    except Exception as e:
        gemini_client = None
        print(f"!!!!!!!! Lifespan: FALHA AO INICIALIZAR GEMINI CLIENT !!!!!!!! Error: {e}")
    print("Lifespan: Startup completo.")
    yield # Aplicação roda
    print("Lifespan: Iniciando shutdown...")
    if gemini_client: await gemini_client.close(); print("Lifespan: Gemini Client fechado.")
    print("Lifespan: Fechando conexão com DB...")
    await run_in_threadpool(db._close_db_sync)
    print("Lifespan: Shutdown completo.")

# --- Criação do App FastAPI ---
app = FastAPI(lifespan=lifespan)

# --- Dependências (Opcional, mas bom para garantir recursos prontos) ---
async def get_current_gemini_client():
    if not gemini_client: raise HTTPException(status_code=503, detail="Service Unavailable: Gemini client.")
    return gemini_client
async def get_current_db_connection():
    # Acessa a conexão via módulo db
    if not db.db_conn: raise HTTPException(status_code=503, detail="Service Unavailable: Database connection.")
    return db.db_conn

# --- Endpoints ---

# <<< MODIFICADO: Retorna lista de ChatInfo (ID + Descrição) >>>
@app.get("/v1/chats", response_model=List[ChatInfo])
async def list_chats(
    db_conn = Depends(get_current_db_connection) # Garante DB pronto
    ):
    """Lista ID e Descrição de todas as sessões de chat existentes."""
    print("GET /v1/chats - Buscando informações no DB...")
    # Busca ID e Descrição do banco
    chats_info_tuples = await run_in_threadpool(db._get_all_chats_info_sync)
    # Converte lista de tuplas para lista de objetos ChatInfo
    chats_info = [ChatInfo(chat_id=cid, description=desc) for cid, desc in chats_info_tuples]
    print(f"GET /v1/chats - Retornando {len(chats_info)} chats.")
    return chats_info

# <<< MODIFICADO: Aceita corpo JSON com descrição opcional >>>
@app.post("/v1/chats", response_model=str) # Ainda retorna só o ID
async def create_chat(
    payload: CreateChatRequest, # Usa o novo modelo Pydantic para o corpo
    gemini_client: GeminiClient = Depends(get_current_gemini_client),
    db_conn = Depends(get_current_db_connection)
    ):
    """Cria uma nova sessão de chat com descrição opcional, salva no DB e retorna seu ID."""
    description = payload.description # Pega a descrição do payload
    print(f"POST /v1/chats - Tentando criar chat com descrição: '{description or 'N/A'}'")
    try:
        new_chat_id = str(uuid.uuid4())
        chat = gemini_client.start_chat(model=GEMINI_MODEL_NAME)
        initial_metadata = chat.metadata

        # <<< MODIFICADO: Usa _create_session_sync com descrição >>>
        success_db = await run_in_threadpool(
            db._create_session_sync,
            new_chat_id,
            initial_metadata,
            description # Passa a descrição para o DB
        )

        if success_db:
            # Atualiza o cache de METADATA em memória
            chat_sessions[new_chat_id] = initial_metadata
            print(f"New chat session created and saved: {new_chat_id}")
            return new_chat_id # Retorna só o ID
        else:
             # _create_session_sync falhou (ex: ID já existe, erro de DB)
             raise HTTPException(status_code=500, detail="Failed to save new chat session to database (maybe chat ID collision?).")

    except Exception as e:
        print(f"Error creating new chat session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create new chat session: {e}")

# --- Endpoints de Chat Ativo (iguais a antes) ---
class SetActiveChatRequest(BaseModel): chat_id: str | None
@app.post("/v1/chats/active")
async def set_active_chat(payload: SetActiveChatRequest):
    global ACTIVE_CHAT_ID
    chat_id_to_set = payload.chat_id
    if chat_id_to_set is None:
        ACTIVE_CHAT_ID = None; print("Active chat deactivated.")
        return {"message": "Active chat deactivated."}
    # Verifica se o ID existe no cache de metadata (que foi carregado do DB)
    if chat_id_to_set in chat_sessions:
        ACTIVE_CHAT_ID = chat_id_to_set; print(f"Active chat set to: {ACTIVE_CHAT_ID}")
        return {"message": f"Active chat set to {ACTIVE_CHAT_ID}"}
    else:
        print(f"Attempted to set active chat to non-existent/non-cached ID: {chat_id_to_set}")
        raise HTTPException(status_code=404, detail=f"Chat session not found: {chat_id_to_set}")
@app.get("/v1/chats/active")
async def get_active_chat():
    # Poderia buscar a descrição do chat ativo no DB se quisesse mostrar aqui
    return {"active_chat_id": ACTIVE_CHAT_ID}

@app.delete("/v1/chats/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str = FastApiPath(..., description="The ID of the chat session to delete"),
    db_conn = Depends(get_current_db_connection) # Garante DB
    ):
    global ACTIVE_CHAT_ID
    # Verifica se existe no cache de metadata
    if chat_id not in chat_sessions: raise HTTPException(status_code=404, detail="Chat session not found.")

    success_db = await run_in_threadpool(db._delete_session_sync, chat_id)
    if success_db:
        if chat_id in chat_sessions: del chat_sessions[chat_id] # Remove do cache de metadata
        print(f"Chat session deleted from memory cache: {chat_id}")
        if ACTIVE_CHAT_ID == chat_id:
            print(f"Deactivated chat {chat_id} because it was deleted.")
            ACTIVE_CHAT_ID = None
    else:
        # _delete_session_sync já logou o erro de DB, mas retornou False (não achou ou falhou)
         raise HTTPException(status_code=500, detail=f"Failed to delete chat session from database or session not found in DB: {chat_id}")


# --- Endpoint Principal de Chat (MODIFICADO para usar _update...) ---
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions_persistent(
    request: Request, # Precisa do request para pegar o corpo JSON
    gemini_client: GeminiClient = Depends(get_current_gemini_client),
    db_conn = Depends(get_current_db_connection)
    ):
    """Processa completions usando o CHAT ATIVO GLOBAL."""
    global ACTIVE_CHAT_ID
    chat_id_to_use = ACTIVE_CHAT_ID
    current_chat_id: str | None = None
    chat_session = None

    print(f"--- Request Completions --- Attempting to use Active Chat ID: {chat_id_to_use or 'None'}")

    if chat_id_to_use and chat_id_to_use in chat_sessions: # Checa ID ativo e se existe no cache
        print(f"Using active chat session from memory cache: {chat_id_to_use}")
        metadata = chat_sessions[chat_id_to_use] # Pega metadata do cache
        try:
            chat_session = gemini_client.start_chat(metadata=metadata, model=GEMINI_MODEL_NAME)
            current_chat_id = chat_id_to_use
            print(f"Continuing active chat: {current_chat_id}")
        except Exception as e:
             print(f"Error loading chat session {chat_id_to_use} from metadata: {e}")
             raise HTTPException(status_code=500, detail=f"Failed to load active chat session {chat_id_to_use}.")
    else:
        if chat_id_to_use: # ID ativo inválido
            print(f"ERROR: Active chat ID '{chat_id_to_use}' not found in cache!")
            ACTIVE_CHAT_ID = None
            raise HTTPException(status_code=404, detail=f"Active chat session '{chat_id_to_use}' not found. Set a valid active chat.")
        else: # Nenhum ativo
            print("ERROR: No active chat session set.")
            raise HTTPException(status_code=400, detail="No active chat session set. Use POST /v1/chats/active.")

    # Valida o corpo da requisição (NÃO espera chat_id aqui)
    try:
        request_body_json = await request.json()
        # Usa o modelo Original que NÃO tem chat_id
        validated_request = OriginalChatCompletionRequest.model_validate(request_body_json)
    except ValidationError as e: raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e: raise HTTPException(status_code=400, detail=f"Error processing request body: {e}")

    # --- Lógica de Processamento da Mensagem ---
    prompt_parts = []
    image_urls_to_process = []
    temp_file_paths = []
    response_text = "[Error processing request]"

    try:
        # (Lógica para extrair prompt e processar imagens - igual anterior)
        last_user_message = None
        for message in reversed(validated_request.messages):
            if message.role == "user": last_user_message = message; break
        if not last_user_message: raise HTTPException(status_code=400, detail="No user message.")
        if isinstance(last_user_message.content, str): prompt_parts.append(last_user_message.content)
        elif isinstance(last_user_message.content, list):
             for block in last_user_message.content:
                if isinstance(block, TextBlock): prompt_parts.append(block.text)
                elif isinstance(block, ImageUrlBlock):
                    if block.image_url.url.startswith("data:image"): image_urls_to_process.append(block.image_url.url); # Processa imagem abaixo
                    else: print(f"Skipping non-data URI: {block.image_url.url[:50]}...")
        # Processa imagens salvas
        for img_url in image_urls_to_process:
             try:
                 header, encoded = img_url.split(",", 1); img_data = base64.b64decode(encoded)
                 mime_type = header.split(";")[0].split(":")[1]
                 ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "image/heic": ".heic", "image/heif": ".heif"}.get(mime_type)
                 if ext:
                     with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                         temp_file.write(img_data); temp_file_paths.append(temp_file.name)
                 else: print(f"Skipping unsupported mime type: {mime_type}")
             except Exception as img_e: print(f"Error processing data URI: {img_e}. Skipping.")
        final_prompt_text = "\n".join(prompt_parts).strip()
        if not final_prompt_text and not temp_file_paths: raise HTTPException(status_code=400, detail="No processable content.")

        # Envia para a API Gemini
        print(f"Sending message to active chat {current_chat_id} (Files: {len(temp_file_paths)})...")
        api_response = await chat_session.send_message( final_prompt_text, files=temp_file_paths )

        # <<< MODIFICADO: Usa _update_session_metadata_sync >>>
        updated_metadata = chat_session.metadata
        print(f"Updating metadata in DB for chat {current_chat_id}...")
        success_db_update = await run_in_threadpool(
            db._update_session_metadata_sync, # <--- Chama a função de update
            current_chat_id,
            updated_metadata
        )
        if success_db_update:
            # Atualiza o cache de METADATA em memória
            chat_sessions[current_chat_id] = updated_metadata
            print(f"Metadata updated successfully in DB and memory for ID: {current_chat_id}")
        else:
            print(f"ERROR: Failed to update chat session {current_chat_id} metadata in database after response.")

        response_text = api_response.text or "[No text response]"
        print(f"Response received from active chat {current_chat_id}: '{response_text[:100]}...'")

    except Exception as e:
        print(f"Error during chat session interaction (ID: {current_chat_id}): {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing message/image with Gemini API (Active Chat ID: {current_chat_id}): {e}")
    finally:
        if temp_file_paths: # Limpeza
             print(f"Cleaning up {len(temp_file_paths)} temporary image files...")
             for path in [str(p) for p in temp_file_paths]:
                 try:
                     if os.path.exists(path): os.remove(path)
                 except OSError as cleanup_e: print(f"Error removing temp file {path}: {cleanup_e}")

    # --- Monta a Resposta ---
    assistant_message = OpenAIMessage(role="assistant", content=response_text)
    choice = Choice(index=0, message=assistant_message, finish_reason="stop")
    usage = Usage()
    openai_response = ChatCompletionResponse(
        model=GEMINI_MODEL_NAME,
        choices=[choice],
        usage=usage,
        chat_id=current_chat_id # Retorna o ID do chat que FOI usado
    )
    return openai_response

# --- Execução do Servidor ---
if __name__ == "__main__":
    print("Starting Uvicorn server...")
    import uvicorn
    uvicorn.run(
        "gemini_api:app", host="0.0.0.0", port=8050, workers=1, reload=False
    )
