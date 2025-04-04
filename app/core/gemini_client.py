# app/core/gemini_client.py
import traceback
from typing import Optional, List, Dict, Any

from gemini_webapi import GeminiClient, ChatSession
from fastapi import HTTPException

from app.config import GEMINI_MODEL_NAME

class GeminiClientWrapper:
    """Manages the GeminiClient instance and interactions."""

    def __init__(self):
        self._client: Optional[GeminiClient] = None

    async def init_client(self, timeout: int = 180):
        """Initializes the GeminiClient."""
        if self._client:
            print("Gemini client already initialized.")
            return

        print(f"Initializing Gemini Client (Timeout: {timeout}s)...")
        try:
            # Consider proxy settings if needed from config
            temp_client = GeminiClient(proxy=None)
            # Use specified timeout, auto_close=False, auto_refresh=True
            await temp_client.init(timeout=timeout, auto_close=False, auto_refresh=True)
            self._client = temp_client
            print("Gemini Client initialized successfully.")
        except Exception as e:
            self._client = None # Ensure client is None if init fails
            print(f"!!!!!!!! FAILED TO INITIALIZE GEMINI CLIENT !!!!!!!! Error: {e}")
            traceback.print_exc()
            # Depending on requirements, could raise an exception here to halt startup
            # raise RuntimeError(f"Failed to initialize Gemini Client: {e}") from e

    async def close_client(self):
        """Closes the GeminiClient connection."""
        if self._client:
            print("Closing Gemini Client...")
            try:
                await self._client.close()
                print("Gemini Client closed.")
            except Exception as e:
                print(f"Error closing Gemini Client: {e}")
            finally:
                self._client = None
        else:
            print("Gemini Client was not initialized or already closed.")

    def get_client(self) -> GeminiClient:
        """Returns the initialized GeminiClient instance, raising an error if not ready."""
        if not self._client:
            # This indicates a programming error or failed startup, internal server error is appropriate
            raise HTTPException(status_code=503, detail="Service Unavailable: Gemini client not initialized.")
        return self._client

    def start_new_chat(self, model: str = GEMINI_MODEL_NAME) -> ChatSession:
        """Starts a new chat session using the underlying client."""
        client = self.get_client()
        # Let exceptions from start_chat propagate up
        return client.start_chat(model=model)

    def load_chat_from_metadata(self, metadata: Dict[str, Any], model: str = GEMINI_MODEL_NAME) -> ChatSession:
        """Loads an existing chat session from metadata."""
        client = self.get_client()
        try:
            # Recreate the session object from metadata
            chat_session = client.start_chat(metadata=metadata, model=model)
            return chat_session
        except Exception as e:
            print(f"Error loading chat session from metadata: {e}")
            # Raise HTTPException here so the service layer can catch it
            raise HTTPException(status_code=500, detail=f"Failed to load chat session from metadata: {e}") from e

    async def send_message(
        self,
        chat_session: ChatSession,
        prompt: str,
        files: Optional[List[str]] = None
    ) -> Any: # Return type depends on gemini_webapi response object, using Any for now
        """Sends a message using the provided ChatSession."""
        # The ChatSession object should belong to the initialized client
        # No need to call get_client() here if chat_session is managed correctly
        if not chat_session:
             raise ValueError("Invalid ChatSession provided to send_message.")
        print(f"Sending message via GeminiClientWrapper (Files: {len(files or [])})...")
        try:
            # Let exceptions propagate
            response = await chat_session.send_message(prompt, files=files)
            print(f"Response received via GeminiClientWrapper.")
            return response
        except Exception as e:
            print(f"Error sending message via Gemini: {e}")
            traceback.print_exc()
            # Raise a specific exception or HTTPException for the service to handle
            raise HTTPException(status_code=500, detail=f"Error communicating with Gemini API: {e}") from e