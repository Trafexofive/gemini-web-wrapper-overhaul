# app/services/chat_service_hybrid.py
import uuid
import base64
import tempfile
import os
import re
import mimetypes
import traceback
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

import aiosqlite
from fastapi import HTTPException

from app.repositories.chat_repository import SqliteChatRepository
from app.repositories.message_repository import SqliteMessageRepository
from app.core.gemini_client_hybrid import GeminiClientHybrid
from app.models import ChatInfo, OpenAIMessage, TextBlock, ImageUrlBlock, ChatCompletionResponse, Choice, Usage, MessageCreate
from app.config import ALLOWED_MODES, GEMINI_MODEL_NAME

# Mock prompts for now - can be loaded from prompts.py later
MODE_PROMPT_TEXTS: Dict[ALLOWED_MODES, Optional[str]] = {
    "Code": "You are an expert programmer. Provide clear, well-documented code solutions with explanations.",
    "Architect": "You are a software architect. Design scalable, maintainable solutions with best practices.",
    "Debug": "You are a debugging expert. Help identify and fix issues systematically.",
    "Ask": "You are a helpful assistant. Answer questions clearly and provide useful information.",
    "Default": None
}

class ChatServiceHybrid:
    """Hybrid chat service that supports both free and paid modes with switching."""

    def __init__(self, repository: SqliteChatRepository, gemini_client: GeminiClientHybrid):
        self.repository = repository
        self.message_repository = SqliteMessageRepository()
        self.gemini_client = gemini_client
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._active_chat_id: Optional[str] = None
        self._current_mode: Literal["free", "paid"] = "free"
        self._chat_sessions: Dict[str, Any] = {}
        print("ChatServiceHybrid initialized.")

    async def load_initial_cache(self, db: aiosqlite.Connection):
        """Loads all session data from DB into the cache."""
        print("ChatServiceHybrid: Loading initial cache from database...")
        try:
            self._cache = await self.repository.get_all_session_data(db)
            print(f"ChatServiceHybrid: Initial cache loaded with {len(self._cache)} sessions.")
        except Exception as e:
            print(f"ChatServiceHybrid CRITICAL ERROR: Failed to load initial cache: {e}")
            self._cache = {}

    async def list_chats(self, db: aiosqlite.Connection) -> List[ChatInfo]:
        """Lists all available chat sessions."""
        return await self.repository.get_chat_info_list(db)

    async def create_chat(self, db: aiosqlite.Connection, description: Optional[str], mode: Optional[ALLOWED_MODES]) -> str:
        """Creates a new chat session."""
        new_chat_id = str(uuid.uuid4())
        final_mode = mode or "Default"
        
        print(f"ServiceHybrid: Creating chat - ID: {new_chat_id}, Desc: '{description or 'N/A'}', Mode: '{final_mode}'")
        
        try:
            # Start new chat session with Gemini
            chat_session = self.gemini_client.start_new_chat(new_chat_id)
            
            # Create metadata with current client mode
            initial_metadata = {
                "chat_id": new_chat_id, 
                "mode": final_mode,
                "client_mode": self._current_mode,
                "session_id": new_chat_id
            }
            
            success_db = await self.repository.create_chat(db, new_chat_id, initial_metadata, description, final_mode)
            if not success_db:
                raise HTTPException(status_code=500, detail="Failed to save new chat session to database.")
            
            self._cache[new_chat_id] = {
                "metadata": initial_metadata,
                "mode": final_mode,
                "prompt_sent": False,
                "client_mode": self._current_mode
            }
            self._chat_sessions[new_chat_id] = chat_session
            
            print(f"ServiceHybrid: Chat {new_chat_id} created and added to cache.")
            return new_chat_id
            
        except Exception as e:
            print(f"ServiceHybrid Error creating chat: {e}")
            traceback.print_exc()
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Unexpected error creating chat session: {e}")

    async def set_active_chat(self, db: aiosqlite.Connection, chat_id: Optional[str]):
        """Sets the globally active chat ID and sends system prompt if needed."""
        if chat_id is None:
            if self._active_chat_id is not None:
                print(f"ServiceHybrid: Deactivating active chat {self._active_chat_id}.")
            self._active_chat_id = None
            return

        print(f"ServiceHybrid: Attempting to activate chat: {chat_id}")

        if chat_id not in self._cache:
            print(f"ServiceHybrid ERROR: Cannot activate chat - ID '{chat_id}' not found in cache.")
            raise HTTPException(status_code=404, detail=f"Chat session not found in active cache: {chat_id}")

        session_data = self._cache[chat_id]
        mode = session_data.get("mode", "Default")
        prompt_sent = session_data.get("prompt_sent", False)
        system_prompt = MODE_PROMPT_TEXTS.get(mode)

        # Send system prompt if needed
        if system_prompt and not prompt_sent:
            print(f"ServiceHybrid: Activating chat {chat_id}: System prompt needed (Mode: {mode}). Sending...")
            try:
                # Send system prompt
                chat_session = self.gemini_client.load_chat_from_metadata(session_data["metadata"])
                await self.gemini_client.send_message(chat_session, system_prompt)
                print(f"ServiceHybrid: System prompt sent successfully for {chat_id}.")

                # Store system message in database
                system_message = MessageCreate(
                    role="system",
                    content=system_prompt,
                    metadata={"type": "system_prompt", "mode": mode, "client_mode": self._current_mode}
                )
                await self.message_repository.create_message(db, chat_id, system_message)

                # Update DB and cache
                flag_ok = await self.repository.mark_prompt_sent(db, chat_id)
                if flag_ok:
                    self._cache[chat_id]["prompt_sent"] = True
                    self._chat_sessions[chat_id] = chat_session
                    print("ServiceHybrid: prompt_sent flag cache updated.")
                else:
                    print(f"ServiceHybrid ERROR: Failed to mark prompt sent flag in DB for {chat_id}.")

            except Exception as send_error:
                print(f"ServiceHybrid ERROR sending system prompt during activation for {chat_id}: {send_error}")
                traceback.print_exc()

        # Set active ID
        self._active_chat_id = chat_id
        print(f"ServiceHybrid: Active chat set to {self._active_chat_id}")

    def get_active_chat(self) -> Optional[str]:
        """Gets the currently active chat ID."""
        return self._active_chat_id

    async def update_chat_mode(self, db: aiosqlite.Connection, chat_id: str, new_mode: ALLOWED_MODES):
        """Updates the mode for a chat and sends new system prompt if active."""
        print(f"ServiceHybrid: Updating mode for chat {chat_id} to '{new_mode}'")
        
        if new_mode not in MODE_PROMPT_TEXTS:
            print(f"ServiceHybrid Warning: Invalid mode '{new_mode}' passed to update_chat_mode.")
            raise HTTPException(status_code=422, detail=f"Invalid mode provided: {new_mode}")
        
        if chat_id not in self._cache:
            print(f"ServiceHybrid ERROR: Chat {chat_id} not found in cache for mode update.")
            raise HTTPException(status_code=404, detail="Chat session not found.")

        # Update DB and cache
        success_db = await self.repository.update_mode_and_reset_flag(db, chat_id, new_mode)
        if not success_db:
            print(f"ServiceHybrid ERROR: Failed to update mode in DB for chat {chat_id}.")
            raise HTTPException(status_code=500, detail="Failed to update chat mode in database.")

        self._cache[chat_id]["mode"] = new_mode
        self._cache[chat_id]["prompt_sent"] = False
        print(f"ServiceHybrid: Mode updated to '{new_mode}' for chat {chat_id} in cache.")

        # If this is the active chat, send new system prompt immediately
        if self._active_chat_id == chat_id:
            print(f"ServiceHybrid: Active chat {chat_id} mode changed to '{new_mode}'. Sending new system prompt...")
            new_system_prompt = MODE_PROMPT_TEXTS.get(new_mode)
            if new_system_prompt:
                try:
                    # Send new system prompt
                    chat_session = self.gemini_client.load_chat_from_metadata(self._cache[chat_id]["metadata"])
                    await self.gemini_client.send_message(chat_session, new_system_prompt)
                    print(f"ServiceHybrid: New system prompt sent successfully for {chat_id}.")

                    # Store new system message in database
                    system_message = MessageCreate(
                        role="system",
                        content=new_system_prompt,
                        metadata={"type": "system_prompt", "mode": new_mode, "client_mode": self._current_mode}
                    )
                    await self.message_repository.create_message(db, chat_id, system_message)

                    # Update DB and cache
                    flag_ok = await self.repository.mark_prompt_sent(db, chat_id)
                    if flag_ok:
                        self._cache[chat_id]["prompt_sent"] = True
                        print(f"ServiceHybrid: Mode change and system prompt completed for active chat {chat_id}.")
                    else:
                        print(f"ServiceHybrid ERROR: Failed to update prompt flag after mode change for {chat_id}.")

                except Exception as mode_e:
                    print(f"ServiceHybrid ERROR sending new system prompt after mode change for {chat_id}: {mode_e}")
                    traceback.print_exc()
            else:
                print(f"ServiceHybrid Warning: No system prompt found for mode '{new_mode}'. Skipping prompt send.")

    async def switch_client_mode(self, new_mode: Literal["free", "paid"]) -> bool:
        """Switch between free and paid client modes."""
        print(f"ServiceHybrid: Switching client mode from {self._current_mode} to {new_mode}")
        
        try:
            success = await self.gemini_client.switch_mode(new_mode)
            if success:
                self._current_mode = new_mode
                print(f"ServiceHybrid: Successfully switched to {new_mode} mode")
                return True
            else:
                print(f"ServiceHybrid: Failed to switch to {new_mode} mode")
                return False
        except Exception as e:
            print(f"ServiceHybrid ERROR switching client mode: {e}")
            return False

    def get_current_client_mode(self) -> str:
        """Get the current client mode."""
        return self._current_mode

    async def delete_chat(self, db: aiosqlite.Connection, chat_id: str):
        """Deletes a chat session and removes it from cache."""
        try:
            # Delete messages first (due to foreign key constraint)
            await self.message_repository.delete_messages_by_chat_id(db, chat_id)
            
            # Delete chat session
            success = await self.repository.delete_chat(db, chat_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"Chat session not found: {chat_id}")
            
            # Remove from cache
            if chat_id in self._cache:
                del self._cache[chat_id]
                print(f"ServiceHybrid: Chat {chat_id} removed from cache.")
            if self._active_chat_id == chat_id:
                self._active_chat_id = None
                print(f"ServiceHybrid: Deactivated chat {chat_id} because it was deleted.")
        except Exception as e:
            print(f"ServiceHybrid Error deleting chat {chat_id}: {e}")
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {e}")

    async def handle_completion(self, db: aiosqlite.Connection, user_messages: List[OpenAIMessage]) -> ChatCompletionResponse:
        """Handles sending user messages to Gemini and storing responses."""
        if not self._active_chat_id:
            raise HTTPException(status_code=400, detail="No active chat session set. Use POST /v1/chats/active.")

        current_chat_id = self._active_chat_id
        print(f"ServiceHybrid: Handling completion for active chat: {current_chat_id}")

        # Verify chat exists
        if current_chat_id not in self._cache:
            print(f"ServiceHybrid CRITICAL ERROR: Active chat ID '{current_chat_id}' is set but not found in cache!")
            self._active_chat_id = None
            raise HTTPException(status_code=404, detail=f"Active chat session '{current_chat_id}' state not found. Please set active chat again.")

        # Process user input
        last_user_message = next((msg for msg in reversed(user_messages) if msg.role == "user"), None)
        if not last_user_message:
            raise HTTPException(status_code=400, detail="No user message found in the request.")

        user_message_text = ""
        image_urls_to_process = []
        temp_file_paths = []
        
        try:
            content = last_user_message.content
            if isinstance(content, str):
                user_message_text = content
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, TextBlock):
                        user_message_text += block.text + "\n"
                    elif isinstance(block, ImageUrlBlock) and block.image_url.url.startswith("data:image"):
                        image_urls_to_process.append(block.image_url.url)
            
            user_message_text = user_message_text.strip()
            
            # Process images
            for img_url in image_urls_to_process:
                try:
                    header, encoded = img_url.split(",", 1)
                    img_data = base64.b64decode(encoded)
                    mime_type = header.split(";")[0].split(":")[1] if ':' in header else 'application/octet-stream'
                    ext = mimetypes.guess_extension(mime_type) or ""
                    safe_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.heic', '.heif']
                    
                    if ext.lower() in safe_extensions:
                        fd, temp_path = tempfile.mkstemp(suffix=ext)
                        os.write(fd, img_data)
                        os.close(fd)
                        temp_file_paths.append(temp_path)
                        print(f"ServiceHybrid: Saved image data URI ({mime_type}) to temp file: {temp_path}")
                    else:
                        print(f"ServiceHybrid Warning: Skipping image with potentially unsafe extension '{ext or 'unknown'}' from mime type '{mime_type}'")
                except Exception as img_e:
                    print(f"ServiceHybrid Error processing data URI: {img_e}. Skipping image.")
            
            if not user_message_text and not temp_file_paths:
                raise HTTPException(status_code=400, detail="No processable content found.")
                
        except Exception as proc_e:
            self._cleanup_temp_files(temp_file_paths)
            raise HTTPException(status_code=400, detail=f"Error processing user message content: {proc_e}")

        # Store user message in database
        try:
            user_message = MessageCreate(
                role="user",
                content=user_message_text,
                metadata={
                    "has_images": len(temp_file_paths) > 0,
                    "client_mode": self._current_mode
                }
            )
            await self.message_repository.create_message(db, current_chat_id, user_message)
            print(f"ServiceHybrid: User message stored in database for chat {current_chat_id}")
        except Exception as store_e:
            print(f"ServiceHybrid WARNING: Failed to store user message in database: {store_e}")

        # Send to Gemini
        try:
            print(f"ServiceHybrid: Sending message to Gemini for chat {current_chat_id} (Mode: {self._current_mode})...")
            chat_session = self._chat_sessions.get(current_chat_id)
            if not chat_session:
                chat_session = self.gemini_client.load_chat_from_metadata(self._cache[current_chat_id]["metadata"])
                self._chat_sessions[current_chat_id] = chat_session
            response_text = await self.gemini_client.send_message(
                chat_session=chat_session,
                prompt=user_message_text,
                files=temp_file_paths
            )
            print(f"ServiceHybrid: Response received from Gemini for chat {current_chat_id}.")

            # Store assistant message in database
            try:
                assistant_message = MessageCreate(
                    role="assistant",
                    content=response_text,
                    metadata={
                        "response_length": len(response_text),
                        "client_mode": self._current_mode
                    }
                )
                await self.message_repository.create_message(db, current_chat_id, assistant_message)
                print(f"ServiceHybrid: Assistant message stored in database for chat {current_chat_id}")
            except Exception as store_e:
                print(f"ServiceHybrid WARNING: Failed to store assistant message in database: {store_e}")

            # Format response
            assistant_message = OpenAIMessage(role="assistant", content=response_text)
            choice = Choice(message=assistant_message)
            usage = Usage()
            openai_response = ChatCompletionResponse(
                model=GEMINI_MODEL_NAME,
                choices=[choice],
                usage=usage,
                chat_id=current_chat_id
            )
            return openai_response

        except Exception as e:
            print(f"ServiceHybrid Error during completion for {current_chat_id}: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error communicating with Gemini API: {e}")
        finally:
            # Cleanup temp files
            self._cleanup_temp_files(temp_file_paths)

    def _cleanup_temp_files(self, file_paths: List[str]):
        """Safely removes temporary files created for image uploads."""
        if file_paths:
            print(f"ServiceHybrid: Cleaning up {len(file_paths)} temporary image files...")
            for path in file_paths:
                try:
                    if path and os.path.exists(path):
                        os.remove(path)
                except OSError as cleanup_e:
                    print(f"ServiceHybrid Error removing temp file '{path}': {cleanup_e}")
                except Exception as general_e:
                    print(f"ServiceHybrid Error during temp file '{path}' cleanup: {general_e}")