# app/core/gemini_client_v2.py
import asyncio
import os
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import tempfile
import mimetypes
from pathlib import Path

class GeminiClientV2:
    """Modern Gemini client using the official google-generativeai library."""
    
    def __init__(self):
        self.model = None
        self.chat_sessions: Dict[str, genai.ChatSession] = {}
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        print("GeminiClientV2 initialized with google-generativeai")
    
    def start_new_chat(self, chat_id: str) -> genai.ChatSession:
        """Start a new chat session."""
        if chat_id in self.chat_sessions:
            print(f"Warning: Chat session {chat_id} already exists, creating new one")
        
        chat_session = self.model.start_chat(history=[])
        self.chat_sessions[chat_id] = chat_session
        print(f"New chat session started: {chat_id}")
        return chat_session
    
    def get_chat_session(self, chat_id: str) -> Optional[genai.ChatSession]:
        """Get an existing chat session."""
        return self.chat_sessions.get(chat_id)
    
    async def send_message(
        self, 
        chat_id: str, 
        message: str, 
        files: Optional[List[str]] = None
    ) -> str:
        """Send a message to a chat session and return the response."""
        chat_session = self.get_chat_session(chat_id)
        if not chat_session:
            raise ValueError(f"Chat session {chat_id} not found")
        
        try:
            # Prepare content parts
            content_parts = [message]
            
            # Add files if provided
            if files:
                for file_path in files:
                    if os.path.exists(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if mime_type and mime_type.startswith('image/'):
                            with open(file_path, 'rb') as f:
                                image_data = f.read()
                                content_parts.append({
                                    "mime_type": mime_type,
                                    "data": image_data
                                })
            
            # Send message
            response = await asyncio.to_thread(
                chat_session.send_message,
                content_parts
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                return response.parts[0].text
            else:
                return str(response)
                
        except Exception as e:
            print(f"Error sending message to Gemini: {e}")
            raise
    
    def delete_chat_session(self, chat_id: str) -> bool:
        """Delete a chat session."""
        if chat_id in self.chat_sessions:
            del self.chat_sessions[chat_id]
            print(f"Chat session deleted: {chat_id}")
            return True
        return False
    
    def get_chat_history(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get the chat history for a session."""
        chat_session = self.get_chat_session(chat_id)
        if not chat_session:
            return []
        
        history = []
        for message in chat_session.history:
            history.append({
                "role": message.role,
                "content": message.parts[0].text if message.parts else ""
            })
        
        return history
    
    def close(self):
        """Clean up resources."""
        self.chat_sessions.clear()
        print("GeminiClientV2 closed")