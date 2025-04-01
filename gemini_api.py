import json
from models.models import *
from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError
import traceback
from gemini_webapi import GeminiClient

app = FastAPI()

gemini_client = None
global_chat = None
GEMINI_MODEL_NAME = "gemini-2.5-exp-advanced"

try:
    gemini_client = GeminiClient(proxy=None)
    global_chat = gemini_client.start_chat(model=GEMINI_MODEL_NAME)
    print(f"Global chat initialized successfully with model: {GEMINI_MODEL_NAME}")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize GeminiClient or global chat. Endpoint will likely fail. Error: {e}")
    gemini_client = None
    global_chat = None
    GEMINI_MODEL_NAME = "N/A"




@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions_shared_chat(request: Request):

    # 1. Check if global chat is available
    if not global_chat:
         raise HTTPException(status_code=503, detail="Service Unavailable: Global chat instance not initialized.")

    # 2. Parse and Validate Request Body
    try:
        request_body_json = await request.json()
        validated_request = ChatCompletionRequest.model_validate(request_body_json)
    except json.JSONDecodeError as e:
         # Log the raw body if JSON parsing fails - useful for debugging client errors
         body_bytes = await request.body()
         print(f"--- Request Body Received (RAW - Invalid JSON) ---\n{body_bytes.decode('utf-8', errors='ignore')}\n---------------------------------------------------")
         raise HTTPException(status_code=400, detail=f"Could not parse request body as JSON: {e}")
    except ValidationError as e:
        print(f"!!! Pydantic Validation ERROR (422) !!!\n{e.json(indent=2)}\n--------------------------------------")
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e: # Catch other potential errors during request processing
         print(f"Unexpected error processing request: {e}")
         traceback.print_exc()
         raise HTTPException(status_code=400, detail=f"Error processing request: {e}")

    # 3. Extract Last User Message
    last_user_message_content = None
    for message in reversed(validated_request.messages):
        if message.role == "user":
            if isinstance(message.content, str):
                last_user_message_content = message.content
            elif isinstance(message.content, list):
                # Extract text from content blocks
                full_text = ""
                for block in message.content:
                     # Check structure defensively, although Pydantic should ensure it
                     if isinstance(block, dict) and block.get("type") == "text" and "text" in block:
                         full_text += block.get("text", "") + "\n"
                     elif hasattr(block, 'type') and block.type == "text" and hasattr(block, 'text'): # If it's a Pydantic model instance
                          full_text += block.text + "\n"
                last_user_message_content = full_text.strip()
            break # Found the last user message

    if not last_user_message_content:
        # This might happen if the client sends only system/assistant messages
        raise HTTPException(status_code=400, detail="No message with role 'user' found or text content could not be extracted.")

    # 4. Send message to the global Gemini chat instance
    try:
        response = await global_chat.send_message(last_user_message_content)
        response_text = response.text

        if not response_text:
             print(f"WARNING: Gemini API returned an empty response for the last message.")
             response_text = "[Model did not provide a text response]" # Provide a default

    except Exception as e:
        print(f"Error sending message via gemini_webapi: {e}")
        traceback.print_exc() # Log full traceback for server-side debugging
        raise HTTPException(status_code=500, detail=f"Error processing message with the Gemini API: {e}")

    # 5. Format Response according to OpenAI standard
    assistant_message = OpenAIMessage(role="assistant", content=response_text)
    choice = Choice(message=assistant_message)
    usage = Usage() # Placeholder for token usage

    openai_response = ChatCompletionResponse(
        model=GEMINI_MODEL_NAME, # Reflect the model used by the global chat
        choices=[choice],
        usage=usage
    )

    return openai_response

if __name__ == "__main__":
    import uvicorn
    if not global_chat: # Check if the critical component is missing
         print("\n\nWARNING: Global chat could not be initialized. Endpoint will fail.\n\n")
    uvicorn.run(app, host="0.0.0.0", port=8099)