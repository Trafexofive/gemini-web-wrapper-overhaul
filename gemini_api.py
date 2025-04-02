import json
import uuid # Ensure uuid is imported
import time  # Ensure time is imported
import base64 # Needed for image processing
import tempfile # Needed for image processing
import os       # Needed for image processing
import traceback
from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

# Importe seus modelos (ajuste o caminho se necessário)
from models.models import (
    ChatCompletionRequest, ChatCompletionResponse, OpenAIMessage, Choice, Usage,
    TextBlock, ImageUrlBlock # Certifique-se de importar os blocos
)

# --- Biblioteca e Globais ---
from gemini_webapi import GeminiClient

app = FastAPI()

gemini_client = None
global_chat = None
GEMINI_MODEL_NAME = "gemini-2.5-exp-advanced" # Seu modelo padrão

try:
    gemini_client = GeminiClient(proxy=None)
    global_chat = gemini_client.start_chat(model=GEMINI_MODEL_NAME)
    print(f"Global chat initialized successfully with model: {GEMINI_MODEL_NAME}")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize GeminiClient or global chat. Endpoint will likely fail. Error: {e}")
    gemini_client = None
    global_chat = None
    GEMINI_MODEL_NAME = "N/A"

# --- Endpoint Principal ---
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions_shared_chat_with_images(request: Request): # Nome atualizado

    if not global_chat:
         raise HTTPException(status_code=503, detail="Service Unavailable: Global chat instance not initialized.")

    # --- Parse e Validação (Usa modelos atualizados) ---
    try:
        request_body_json = await request.json()
        validated_request = ChatCompletionRequest.model_validate(request_body_json) # Validará texto E imagem
        print(f"--- Request Received (Processing for global_chat with potential images) ---")
    except ValidationError as e:
        print(f"!!! Pydantic Validation ERROR (422) !!!\n{e.json(indent=2)}\n--------------------------------------")
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        print(f"Error processing request body: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing request: {e}")

    # --- Processar Última Mensagem (Texto e Imagens) ---
    prompt_parts = []
    image_urls_to_process = []
    temp_file_paths = [] # Para guardar caminhos temporários

    last_user_message = None
    for message in reversed(validated_request.messages):
        if message.role == "user":
            last_user_message = message
            break

    if not last_user_message:
         raise HTTPException(status_code=400, detail="No user message found.")

    # Extrair texto e URLs de imagem
    if isinstance(last_user_message.content, str):
        prompt_parts.append(last_user_message.content)
    elif isinstance(last_user_message.content, list):
        for block in last_user_message.content:
            if isinstance(block, TextBlock):
                prompt_parts.append(block.text)
            elif isinstance(block, ImageUrlBlock):
                image_urls_to_process.append(block.image_url.url)

    final_prompt_text = "\n".join(prompt_parts).strip()

    # Validar se há algo para enviar (pode ser só imagem)
    if not final_prompt_text and not image_urls_to_process:
         raise HTTPException(status_code=400, detail="No processable content (text or image) found.")

    # --- Lógica Principal: Processar Imagens e Chamar API ---
    response_text = "[Error processing request]" # Default
    try:
        # Processar Data URIs -> Arquivos Temporários (igual à lógica anterior)
        for img_url in image_urls_to_process:
            if img_url.startswith("data:image"):
                try:
                    header, encoded = img_url.split(",", 1)
                    img_data = base64.b64decode(encoded)
                    mime_type = header.split(";")[0].split(":")[1]
                    ext = { "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp", "image/gif": ".gif" }.get(mime_type, ".png")
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                        temp_file.write(img_data)
                        temp_file_paths.append(temp_file.name)
                        print(f"Saved image data to temporary file: {temp_file.name}")
                except Exception as img_e:
                     print(f"Error processing data URI for an image: {img_e}. Skipping this image.")
            else:
                 print(f"Skipping non-data URI image URL (download not implemented): {img_url}")

        # --- Chamar global_chat.send_message com texto E arquivos ---
        print(f"Sending message to global_chat with text and {len(temp_file_paths)} files...")
        # *** A CHAMADA CHAVE MODIFICADA ***
        api_response = await global_chat.send_message(
            final_prompt_text,
            files=temp_file_paths # Passa a lista de caminhos temporários
        )
        # *** FIM DA CHAMADA ***

        response_text = api_response.text
        print(f"Response received from global_chat: '{response_text[:100]}...'")
        if not response_text:
            print(f"WARNING: Gemini response was empty or None!")
            response_text = "[Model did not provide a text response]"

    except Exception as e:
        print(f"Error during global_chat interaction: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing message/image with Gemini API: {e}")
    finally:
        # --- Limpeza OBRIGATÓRIA dos Arquivos Temporários ---
        if temp_file_paths:
             print(f"Cleaning up {len(temp_file_paths)} temporary image files...")
             for path in temp_file_paths:
                 try: os.remove(path)
                 except OSError as cleanup_e: print(f"Error removing temp file {path}: {cleanup_e}")

    # --- Formatar Resposta OpenAI ---
    assistant_message = OpenAIMessage(role="assistant", content=response_text)
    choice = Choice(message=assistant_message)
    usage = Usage()

    openai_response = ChatCompletionResponse(
        model=GEMINI_MODEL_NAME, # Modelo do chat global
        choices=[choice],
        usage=usage
    )
    return openai_response

# --- Execução ---
if __name__ == "__main__":
    import uvicorn
    if not global_chat:
         print("\n\nWARNING: Global chat could not be initialized. Endpoint will fail.\n\n")
    # Mantendo a porta 8050 que você usou no último trecho
    uvicorn.run(app, host="0.0.0.0", port=8050)