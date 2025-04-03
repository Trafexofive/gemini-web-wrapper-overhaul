# gemini_api.py
import base64
import tempfile
import os
import traceback
import uuid
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path # Adicionado Path
from typing import List, Dict, Any # Adicionado Tipos

# Imports do FastAPI e relacionados
from fastapi import FastAPI, HTTPException, Request, Path as FastApiPath, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ValidationError

# Imports dos seus Modelos Pydantic
from models.models import (
    TextBlock, ImageUrlBlock, OpenAIMessage, Choice, Usage,
    OriginalChatCompletionRequest, ChatCompletionResponse,
    CreateChatRequest, ChatInfo, ALLOWED_MODES, UpdateChatModeRequest
)

# Import da biblioteca Gemini
from gemini_webapi import GeminiClient

# Importa o módulo do banco de dados
import db

# --- Constantes e Variáveis Globais ---
gemini_client: GeminiClient | None = None
GEMINI_MODEL_NAME = "gemini-2.5-exp-advanced" # Ou seu modelo preferido

# Cache em memória para dados da sessão:
# Estrutura: { chat_id: {"metadata": object, "mode": str|None, "prompt_sent": bool} }
chat_sessions: Dict[str, Dict[str, Any]] = {}

# ID do chat atualmente ativo (definido via POST /v1/chats/active)
ACTIVE_CHAT_ID: str | None = None

# Dicionário com os prompts de sistema para cada modo
MODE_PROMPTS = {
    "Code": "Você é Coder, um assistente de programação expert em Python, com décadas de experiência. Foque em fornecer código claro, eficiente e bem documentado. Explique conceitos complexos de forma simples quando necessário.",
    "Architect": "Você é Architect, um arquiteto de software sênior. Seu objetivo é analisar requisitos, propor soluções de arquitetura robustas e escaláveis, discutir trade-offs e padrões de design.",
    "Debug": "Você é Debug, um especialista em encontrar e corrigir bugs. Analise o código ou o problema descrito, faça perguntas para esclarecer, identifique a causa raiz e sugira soluções precisas.",
    "Ask": "Você é Ask, um assistente geral prestativo e informativo. Responda às perguntas de forma clara e concisa, buscando informações relevantes se necessário.",
    "Default": None # Modo padrão não tem prompt extra
}

# --- Ciclo de Vida da Aplicação (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia a inicialização e finalização de recursos."""
    print("Lifespan: Iniciando aplicação...")
    global gemini_client, chat_sessions

    # 1. Inicializa Banco de Dados
    print("Lifespan: Tentando inicializar DB...")
    db_initialized = await run_in_threadpool(db._init_db_sync) # Chama a função sync em outra thread

    if db_initialized:
        print("Lifespan: DB OK. Verificando conexão...")
        if db.db_conn:
            print(">>> Lifespan Check: OK! db.db_conn NÃO é None logo após init.")
        else:
             # Isso seria muito estranho se db_initialized fosse True
            print(">>> !!!!!!! Lifespan Check: FALHOU! db.db_conn É None logo após init !!!!!!!")

        # 2. Carrega dados das sessões para o cache em memória
        print("Lifespan: Carregando dados das sessões (metadata, mode, prompt_sent)...")
        # _load_sessions_sync agora retorna o dict com a estrutura completa
        loaded_data = await run_in_threadpool(db._load_sessions_sync)
        chat_sessions = loaded_data # Atualiza cache global
        print(f"Lifespan: Dados de {len(chat_sessions)} sessões carregados para cache.")
    else:
        print("!!!!!!!! Lifespan: FALHA AO INICIALIZAR DB. Cache de sessão vazio. !!!!!!!!")
        chat_sessions = {} # Garante que o cache está vazio se o DB falhar

    # 3. Inicializa Cliente Gemini
    print("Lifespan: Tentando inicializar Gemini Client...")
    try:
        # Usa um timeout maior na inicialização, conforme discutido
        temp_client = GeminiClient(proxy=None)
        await temp_client.init(timeout=180, auto_close=False, auto_refresh=True)
        gemini_client = temp_client # Atribui ao global
        print("Lifespan: Gemini Client inicializado com sucesso (timeout init: 180s).")
    except Exception as e:
        gemini_client = None # Garante que é None se falhar
        print(f"!!!!!!!! Lifespan: FALHA AO INICIALIZAR GEMINI CLIENT !!!!!!!! Error: {e}")
        # Considerar parar a aplicação aqui se o Gemini for essencial

    print("Lifespan: Startup completo.")
    yield # Aplicação fica disponível para receber requisições

    # Código de Shutdown (executado após a aplicação parar)
    print("Lifespan: Iniciando shutdown...")
    if gemini_client:
        print("Lifespan: Fechando Gemini Client...")
        try: await gemini_client.close()
        except Exception as e: print(f"Erro ao fechar Gemini Client: {e}")
        print("Lifespan: Gemini Client fechado.")

    print("Lifespan: Fechando conexão com DB...")
    await run_in_threadpool(db._close_db_sync) # Chama a função sync em outra thread
    print("Lifespan: Shutdown completo.")


# --- Criação da Instância FastAPI ---
app = FastAPI(lifespan=lifespan) # Usa o lifespan definido acima

# --- Servir Arquivos Estáticos (Frontend) ---
current_script_dir = Path(__file__).parent
static_dir_path = current_script_dir / "static"
print(f"--- DEBUG: Montando diretório estático em: {static_dir_path} ---")
# Monta a pasta 'static' na URL '/static'
app.mount("/static", StaticFiles(directory=static_dir_path), name="static")

# Rota Raiz para servir o HTML principal
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve o arquivo HTML principal do frontend."""
    index_path = static_dir_path / "manage_chats.html"
    if not index_path.is_file():
        print(f"Erro Fatal: Arquivo frontend '{index_path}' não encontrado!")
        raise HTTPException(status_code=404, detail="Frontend file not found.")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        print(f"Erro ao ler arquivo frontend '{index_path}': {e}")
        raise HTTPException(status_code=500, detail="Error reading frontend file.")


# --- Dependências FastAPI ---
# Funções que garantem que os recursos estão prontos antes de usar nas rotas
async def get_current_gemini_client():
    """Dependência que retorna o cliente Gemini inicializado ou lança erro 503."""
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Service Unavailable: Gemini client not initialized.")
    return gemini_client

async def get_current_db_connection():
    """Dependência que retorna a conexão DB ou lança erro 503."""
    # Acessa a variável global do módulo 'db'
    if not db.db_conn:
        raise HTTPException(status_code=503, detail="Service Unavailable: Database connection not available.")
    return db.db_conn

# --- Modelo para Definir Chat Ativo ---
class SetActiveChatRequest(BaseModel):
    chat_id: str | None


# --- Endpoints da API ---

@app.get("/v1/chats", response_model=List[ChatInfo])
async def list_chats(db_conn = Depends(get_current_db_connection)):
    """Lista ID, Descrição e Modo de todas as sessões de chat existentes."""
    print("GET /v1/chats - Buscando informações no DB...")
    # Chama a função sync do DB em outra thread
    chats_info_tuples = await run_in_threadpool(db._get_all_chats_info_sync)
    # Converte o resultado para o modelo Pydantic
    chats_info = [ChatInfo(chat_id=cid, description=desc, mode=mode) for cid, desc, mode in chats_info_tuples]
    print(f"GET /v1/chats - Retornando {len(chats_info)} chats.")
    return chats_info

@app.post("/v1/chats", response_model=str)
async def create_chat(
    payload: CreateChatRequest, # Recebe descrição e modo no corpo
    gemini_client: GeminiClient = Depends(get_current_gemini_client), # Garante cliente pronto
    db_conn = Depends(get_current_db_connection) # Garante DB pronto
    ):
    """Cria uma nova sessão de chat com descrição e modo."""
    description = payload.description
    mode = payload.mode

    # Valida o modo recebido
    if mode and mode not in MODE_PROMPTS:
         print(f"WARNING: Modo inválido '{mode}' recebido ao criar chat. Usando 'Default'.")
         mode = "Default"

    print(f"POST /v1/chats - Criando chat: Desc='{description or 'N/A'}' Mode='{mode or 'Default'}'")
    try:
        new_chat_id = str(uuid.uuid4())
        # Inicia a sessão na biblioteca Gemini para pegar o metadata inicial
        chat = gemini_client.start_chat(model=GEMINI_MODEL_NAME)
        initial_metadata = chat.metadata

        # Cria a sessão no banco de dados (incluindo modo)
        success_db = await run_in_threadpool(
            db._create_session_sync,
            new_chat_id, initial_metadata, description, mode
        )

        if success_db:
            # Atualiza o cache em memória com os dados iniciais
            chat_sessions[new_chat_id] = {
                "metadata": initial_metadata,
                "mode": mode,
                "prompt_sent": False # Novo chat nunca enviou o prompt
            }
            print(f"New chat session created/saved: {new_chat_id}")
            return new_chat_id # Retorna o ID criado
        else:
             # A função do DB provavelmente logou o erro (ex: IntegrityError)
             raise HTTPException(status_code=500, detail="Failed to save new chat session to database (check logs).")
    except Exception as e:
        print(f"Error creating new chat session: {e}")
        traceback.print_exc() # Loga o traceback completo para debug
        raise HTTPException(status_code=500, detail=f"Unexpected error creating chat session: {e}")

@app.post("/v1/chats/active")
async def set_active_chat(payload: SetActiveChatRequest):
    """Define qual chat_id será usado pelas próximas chamadas a /v1/chat/completions."""
    global ACTIVE_CHAT_ID
    chat_id_to_set = payload.chat_id

    if chat_id_to_set is None:
        ACTIVE_CHAT_ID = None
        print("Active chat deactivated.")
        return {"message": "Active chat deactivated."}

    # Verifica se o chat existe no cache em memória (que reflete o DB no startup)
    if chat_id_to_set in chat_sessions:
        ACTIVE_CHAT_ID = chat_id_to_set
        print(f"Active chat set to: {ACTIVE_CHAT_ID}")
        return {"message": f"Active chat set to {ACTIVE_CHAT_ID}"}
    else:
        # Se não está no cache, provavelmente não existe ou houve falha no carregamento
        print(f"Attempted to set active chat to non-existent/non-cached ID: {chat_id_to_set}")
        raise HTTPException(status_code=404, detail=f"Chat session not found in cache: {chat_id_to_set}")

@app.get("/v1/chats/active")
async def get_active_chat():
    """Retorna o ID do chat atualmente ativo (pode ser None)."""
    # Poderia buscar descrição/modo do chat ativo aqui se necessário
    return {"active_chat_id": ACTIVE_CHAT_ID}

@app.put("/v1/chats/{chat_id}/mode")
async def update_chat_mode(
    payload: UpdateChatModeRequest,
    chat_id: str = FastApiPath(..., description="ID do chat a ter o modo atualizado"),
    db_conn = Depends(get_current_db_connection)
):
    """Atualiza o modo de um chat existente e reseta o flag 'system_prompt_sent'."""
    global chat_sessions # Acesso ao cache para atualização

    print(f"PUT /v1/chats/{chat_id}/mode - Novo modo solicitado: {payload.mode}")

    # 1. Verifica se o chat existe no cache
    if chat_id not in chat_sessions:
        print(f"Erro: Chat {chat_id} não encontrado no cache para atualizar modo.")
        raise HTTPException(status_code=404, detail="Chat session not found.")

    # 2. Chama a função do DB para atualizar modo e resetar flag
    success_db = await run_in_threadpool(
        db._update_session_mode_sync,
        chat_id,
        payload.mode # Passa o novo modo para o DB
    )

    if success_db:
        # 3. Atualiza o cache em memória
        if chat_id in chat_sessions:
            chat_sessions[chat_id]["mode"] = payload.mode
            chat_sessions[chat_id]["prompt_sent"] = False # Reseta flag no cache também
            print(f"Cache atualizado para chat {chat_id}: Novo modo '{payload.mode}', prompt_sent=False")
        else:
             print(f"WARNING: Chat {chat_id} não encontrado no cache durante atualização de modo (pós-DB).")

        return {"message": f"Modo do Chat {chat_id} atualizado para '{payload.mode}'. Prompt será enviado na próxima mensagem."}
    else:
        print(f"Erro ao tentar atualizar modo no DB para chat {chat_id}.")
        raise HTTPException(status_code=500, detail=f"Failed to update chat mode in database for {chat_id}.")

@app.delete("/v1/chats/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str = FastApiPath(..., description="The ID of the chat session to delete"),
    db_conn = Depends(get_current_db_connection) # Garante DB
    ):
    """Deleta uma sessão de chat específica do DB e da memória."""
    global ACTIVE_CHAT_ID, chat_sessions # Acesso aos globais

    # Verifica se existe no cache antes de tentar deletar
    if chat_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    # Deleta do Banco de Dados
    success_db = await run_in_threadpool(db._delete_session_sync, chat_id)

    if success_db:
        # Remove do cache em memória APÓS sucesso no DB
        if chat_id in chat_sessions:
            del chat_sessions[chat_id]
            print(f"Chat session deleted from memory cache: {chat_id}")
        else:
            # Isso seria estranho, mas apenas loga
            print(f"Warning: Chat {chat_id} deleted from DB but was already missing from cache.")

        # Se o chat deletado era o ativo, desativa-o
        if ACTIVE_CHAT_ID == chat_id:
            ACTIVE_CHAT_ID = None
            print(f"Deactivated chat {chat_id} because it was deleted.")
        # Retorna 204 No Content (sem corpo) implicitamente
    else:
        # A função do DB já logou o erro
         raise HTTPException(status_code=500, detail=f"Failed to delete chat session from database (check logs): {chat_id}")


# --- Endpoint Principal de Chat ---
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions_persistent(
    request: Request, # Recebe o Request para acessar o corpo JSON
    gemini_client: GeminiClient = Depends(get_current_gemini_client), # Garante cliente
    db_conn = Depends(get_current_db_connection) # Garante DB
    ):
    """Processa completions usando o CHAT ATIVO GLOBAL e envia o prompt do modo apenas uma vez."""
    global ACTIVE_CHAT_ID, chat_sessions # Acesso/Modificação de globais

    chat_id_to_use = ACTIVE_CHAT_ID
    current_chat_id: str | None = None
    chat_session = None
    chat_mode: str | None = None
    prompt_sent: bool = True # Assume True se não encontrar no cache
    needs_prompt_flag_update = False # Controla se precisa atualizar o flag no DB

    print(f"--- Request Completions --- Active Chat ID: {chat_id_to_use or 'None'}")

    # 1. Identifica e carrega o chat ativo a partir do cache
    if chat_id_to_use and chat_id_to_use in chat_sessions:
        print(f"Using active chat session from cache: {chat_id_to_use}")
        session_data = chat_sessions[chat_id_to_use]
        metadata = session_data.get("metadata")
        chat_mode = session_data.get("mode")
        prompt_sent = session_data.get("prompt_sent", True) # Pega flag do cache

        if metadata is None:
             print(f"ERROR: Metadata missing in cache for active chat {chat_id_to_use}!")
             raise HTTPException(status_code=500, detail="Internal error: Metadata missing for active chat.")
        try:
            # Recria o objeto de sessão da biblioteca usando o metadata
            chat_session = gemini_client.start_chat(metadata=metadata, model=GEMINI_MODEL_NAME)
            current_chat_id = chat_id_to_use # Confirma ID usado
            print(f"Continuing active chat: {current_chat_id} (Mode: {chat_mode or 'Default'}, Prompt Sent: {prompt_sent})")
        except Exception as e:
             print(f"Error loading chat session {chat_id_to_use} from metadata: {e}")
             # Pode ser metadata inválido/corrompido
             raise HTTPException(status_code=500, detail=f"Failed to load active chat session {chat_id_to_use} from metadata.")
    else:
        # Nenhum chat ativo definido ou ID ativo inválido/não encontrado no cache
        if chat_id_to_use: # Tinha um ID ativo, mas não está no cache
            print(f"ERROR: Active chat ID '{chat_id_to_use}' not found in cache!")
            ACTIVE_CHAT_ID = None # Limpa o ID inválido
            raise HTTPException(status_code=404, detail=f"Active chat session '{chat_id_to_use}' not found. Please set a valid active chat.")
        else: # Nenhum chat ativo global definido
            print("ERROR: No active chat session is set.")
            raise HTTPException(status_code=400, detail="No active chat session set. Use POST /v1/chats to create and POST /v1/chats/active to set it.")

    # 2. Valida o corpo da requisição (mensagens do usuário)
    # Nota: Usamos OriginalChatCompletionRequest porque NÃO esperamos chat_id aqui
    try:
        request_body_json = await request.json()
        validated_request = OriginalChatCompletionRequest.model_validate(request_body_json)
    except ValidationError as e:
        print(f"Request Body Validation Error: {e.json(indent=2)}")
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        print(f"Error processing request body: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing request body: {e}")

    # --- 3. Prepara a Mensagem para Enviar ---
    prompt_parts = []
    image_urls_to_process = []
    temp_file_paths = []
    response_text = "[Error processing request]" # Default

    try:
        # Extrai conteúdo da última mensagem do usuário
        last_user_message = None
        for message in reversed(validated_request.messages):
            if message.role == "user":
                last_user_message = message
                break
        if not last_user_message: raise HTTPException(status_code=400, detail="No user message found in request.")

        user_message_text = ""
        # Processa texto e identifica imagens
        if isinstance(last_user_message.content, str):
            user_message_text = last_user_message.content
        elif isinstance(last_user_message.content, list):
             for block in last_user_message.content:
                if isinstance(block, TextBlock):
                    user_message_text += block.text + "\n" # Junta múltiplos textos
                elif isinstance(block, ImageUrlBlock):
                    if block.image_url.url.startswith("data:image"):
                         image_urls_to_process.append(block.image_url.url)
                    else: print(f"Skipping non-data URI image URL: {block.image_url.url[:50]}...")
        user_message_text = user_message_text.strip()

        # Processa imagens base64 para arquivos temporários
        for img_url in image_urls_to_process:
             try:
                 header, encoded = img_url.split(",", 1); img_data = base64.b64decode(encoded)
                 mime_type = header.split(";")[0].split(":")[1]
                 # Tenta obter extensão do mime type
                 ext = mimetypes.guess_extension(mime_type) or {"image/jpg": ".jpg"}.get(mime_type) # Fallback comum
                 if ext:
                     # Validação simples de extensão (opcional)
                     if ext.lower() not in ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.heic', '.heif']:
                          print(f"Skipping image with potentially unsafe extension '{ext}' from mime type {mime_type}")
                          continue
                     with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                         temp_file.write(img_data); temp_file_paths.append(temp_file.name)
                 else: print(f"Skipping image: Could not determine extension for mime type {mime_type}")
             except Exception as img_e: print(f"Error processing data URI: {img_e}. Skipping image.")

        # Verifica se há conteúdo processável após processar imagens
        if not user_message_text and not temp_file_paths:
             raise HTTPException(status_code=400, detail="No processable text or valid image content found.")

        # Prepara o prompt final, adicionando prompt do sistema SE necessário
        final_prompt_to_send = user_message_text
        system_prompt = MODE_PROMPTS.get(chat_mode) if chat_mode else None

        if system_prompt and not prompt_sent:
            print(f"Prepending system prompt for mode '{chat_mode}' (First time)...")
            final_prompt_to_send = f"{system_prompt}\n\n---\n\n{user_message_text}"
            needs_prompt_flag_update = True # Marca para atualizar flag no DB depois
        elif system_prompt:
             print(f"System prompt for mode '{chat_mode}' already sent.")
        else:
            print("No system prompt to prepend.")

        # --- 4. Envia Mensagem para Gemini API ---
        print(f"Sending message to active chat {current_chat_id} (Files: {len(temp_file_paths)})...")
        api_response = await chat_session.send_message( final_prompt_to_send, files=temp_file_paths )

        # --- 5. Processa Resposta e Atualiza Estado ---
        updated_metadata = chat_session.metadata
        print(f"Updating metadata in DB for chat {current_chat_id}...")
        # Atualiza apenas o metadata no DB
        success_db_metadata_update = await run_in_threadpool(db._update_session_metadata_sync, current_chat_id, updated_metadata)

        # Se o prompt do sistema foi enviado nesta chamada, marca no DB e no cache
        if needs_prompt_flag_update and success_db_metadata_update:
             print(f"Marking system prompt as SENT in DB for chat {current_chat_id}...")
             success_db_flag_update = await run_in_threadpool(db._mark_system_prompt_sent_sync, current_chat_id)
             if success_db_flag_update:
                 # Atualiza flag no cache de memória local
                 if current_chat_id in chat_sessions:
                      chat_sessions[current_chat_id]["prompt_sent"] = True
                      print(f"System prompt flag updated in cache for {current_chat_id}.")
                 else: print(f"WARNING: Chat {current_chat_id} not found in cache during flag update.")
             else:
                  print(f"ERROR: Failed to mark system prompt as sent in DB for {current_chat_id}.")

        # Atualiza o cache de metadata local SE o DB foi atualizado
        if success_db_metadata_update:
            if current_chat_id in chat_sessions:
                 chat_sessions[current_chat_id]["metadata"] = updated_metadata
                 print(f"Metadata cache updated for ID: {current_chat_id}")
            # else: # Já logado acima se não achar no cache
        else:
            print(f"ERROR: Failed to update chat session {current_chat_id} metadata in database.")

        # Processa o texto da resposta
        response_text = api_response.text or "[No text response]"
        print(f"Response received: '{response_text[:100]}...'")

    # Tratamento de erro durante a interação com Gemini
    except Exception as e:
        print(f"Error during chat session interaction (ID: {current_chat_id}): {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing message/image with Gemini API (Active Chat ID: {current_chat_id}): {e}")
    finally:
        # Limpeza dos arquivos temporários de imagem
        if temp_file_paths:
             print(f"Cleaning up {len(temp_file_paths)} temporary image files...")
             for path in [str(p) for p in temp_file_paths]:
                 try:
                     if os.path.exists(path): os.remove(path)
                 except OSError as cleanup_e: print(f"Error removing temp file {path}: {cleanup_e}")

    # --- 6. Monta a Resposta Final ---
    assistant_message = OpenAIMessage(role="assistant", content=response_text)
    choice = Choice(index=0, message=assistant_message, finish_reason="stop")
    usage = Usage() # Placeholder
    openai_response = ChatCompletionResponse(
        model=GEMINI_MODEL_NAME,
        choices=[choice],
        usage=usage,
        chat_id=current_chat_id # Retorna o ID do chat que foi usado
    )
    return openai_response

# --- Execução do Servidor ---
if __name__ == "__main__":
    # Adiciona import de mimetypes aqui se não estiver no topo
    import mimetypes
    print("Starting Uvicorn server...")
    import uvicorn
    uvicorn.run(
        "gemini_api:app", host="0.0.0.0", port=8050, workers=1, reload=False
    )