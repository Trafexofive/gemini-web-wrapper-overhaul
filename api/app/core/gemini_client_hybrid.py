# app/core/gemini_client_hybrid.py
import asyncio
import os
import tempfile
import mimetypes
import json
import sqlite3
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
import subprocess
import shutil

try:
    from gemini_webapi import GeminiClient, ChatSession
    GEMINI_WEBAPI_AVAILABLE = True
except ImportError:
    GEMINI_WEBAPI_AVAILABLE = False
    print("WARNING: gemini_webapi not available")

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GOOGLE_GENERATIVEAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENERATIVEAI_AVAILABLE = False
    print("WARNING: google-generativeai not available")

class GeminiClientHybrid:
    """Hybrid Gemini client that supports both free (cookies) and paid (API) modes."""
    
    def __init__(self):
        self._free_client = None
        self._paid_client = None
        self._sessions: Dict[str, Any] = {}
        self._mode: Literal["free", "paid"] = "free"
        self._initialized = False
        
        print("GeminiClientHybrid initialized")
    
    def _extract_firefox_cookies(self) -> Dict[str, str]:
        """Extract cookies from Firefox profile automatically."""
        cookies = {}
        
        try:
            # Common Firefox profile locations
            firefox_paths = [
                Path.home() / ".mozilla" / "firefox",
                Path("/root/.mozilla/firefox"),  # Docker
                Path("/home/user/.mozilla/firefox"),  # Alternative Docker
            ]
            
            for firefox_path in firefox_paths:
                if not firefox_path.exists():
                    continue
                
                print(f"Checking Firefox profile at: {firefox_path}")
                
                # Find the default profile
                profiles_ini = firefox_path / "profiles.ini"
                if not profiles_ini.exists():
                    continue
                
                # Parse profiles.ini to find default profile
                default_profile = None
                with open(profiles_ini, 'r') as f:
                    for line in f:
                        if line.startswith("Path="):
                            default_profile = line.split("=", 1)[1].strip()
                            break
                
                if not default_profile:
                    continue
                
                # Look for cookies.sqlite in the profile
                profile_path = firefox_path / default_profile
                cookies_db = profile_path / "cookies.sqlite"
                
                if not cookies_db.exists():
                    print(f"Cookies database not found at: {cookies_db}")
                    continue
                
                print(f"Found cookies database at: {cookies_db}")
                
                # Extract Gemini cookies
                try:
                    # Copy the database to avoid locking issues
                    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite')
                    shutil.copy2(cookies_db, temp_db.name)
                    
                    conn = sqlite3.connect(temp_db.name)
                    cursor = conn.cursor()
                    
                    # Query for Gemini cookies
                    cursor.execute("""
                        SELECT name, value FROM moz_cookies 
                        WHERE host LIKE '%google.com%' 
                        AND (name LIKE '%Secure_1PSID%' OR name LIKE '%Secure_1PSIDTS%')
                    """)
                    
                    for name, value in cursor.fetchall():
                        cookies[name] = value
                        print(f"Found cookie: {name}")
                    
                    conn.close()
                    os.unlink(temp_db.name)
                    
                    if cookies:
                        print(f"Successfully extracted {len(cookies)} cookies from Firefox")
                        return cookies
                        
                except Exception as e:
                    print(f"Error extracting cookies from {cookies_db}: {e}")
                    if temp_db:
                        os.unlink(temp_db.name)
            
            print("No cookies found in Firefox profiles")
            return {}
            
        except Exception as e:
            print(f"Error during Firefox cookie extraction: {e}")
            return {}
    
    def _load_cookies_from_env(self) -> Dict[str, str]:
        """Load cookies from environment variables."""
        cookies = {}
        
        secure_1psid = os.getenv("Secure_1PSID")
        secure_1psidts = os.getenv("Secure_1PSIDTS")
        
        if secure_1psid and secure_1psidts:
            cookies["Secure_1PSID"] = secure_1psid
            cookies["Secure_1PSIDTS"] = secure_1psidts
            print("Loaded cookies from environment variables")
        
        return cookies
    
    async def init_client(self, mode: Literal["free", "paid"] = "free", timeout: int = 180) -> bool:
        """Initialize the Gemini client in the specified mode."""
        self._mode = mode
        
        if mode == "free":
            return await self._init_free_client(timeout)
        else:
            return await self._init_paid_client(timeout)
    
    async def _init_free_client(self, timeout: int) -> bool:
        """Initialize the free client using cookies."""
        if not GEMINI_WEBAPI_AVAILABLE:
            print("ERROR: gemini_webapi not available for free mode")
            return False
        
        try:
            print("Initializing free Gemini client...")
            
            # Try to get cookies
            cookies = self._load_cookies_from_env()
            if not cookies:
                print("No cookies in environment, attempting Firefox extraction...")
                cookies = self._extract_firefox_cookies()
            
            if not cookies:
                print("WARNING: No cookies found, will try to load from browser")
            
            # Create client
            if cookies:
                self._free_client = GeminiClient(cookies=cookies)
                print("Free client initialized with cookies")
            else:
                self._free_client = GeminiClient()
                print("Free client initialized, attempting to load browser cookies")
            
            # Test connection
            await asyncio.wait_for(self._test_free_connection(), timeout=timeout)
            
            self._initialized = True
            print("Free Gemini client initialization successful!")
            return True
            
        except asyncio.TimeoutError:
            print(f"ERROR: Free client initialization timed out after {timeout}s")
            return False
        except Exception as e:
            print(f"ERROR: Free client initialization failed: {e}")
            return False
    
    async def _init_paid_client(self, timeout: int) -> bool:
        """Initialize the paid client using official API."""
        if not GOOGLE_GENERATIVEAI_AVAILABLE:
            print("ERROR: google-generativeai not available for paid mode")
            return False
        
        try:
            print("Initializing paid Gemini client...")
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for paid mode")
            
            # Configure the API
            genai.configure(api_key=api_key)
            
            # Initialize the model
            self._paid_client = genai.GenerativeModel(
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
            
            # Test connection
            await asyncio.wait_for(self._test_paid_connection(), timeout=timeout)
            
            self._initialized = True
            print("Paid Gemini client initialization successful!")
            return True
            
        except Exception as e:
            print(f"ERROR: Paid client initialization failed: {e}")
            return False
    
    async def _test_free_connection(self):
        """Test the free client connection."""
        try:
            test_session = await self._free_client.start_chat()
            if test_session:
                print("Free client connection test successful")
                return True
            else:
                raise Exception("Failed to create test session")
        except Exception as e:
            print(f"Free client connection test failed: {e}")
            raise
    
    async def _test_paid_connection(self):
        """Test the paid client connection."""
        try:
            # Create a test chat session
            test_session = self._paid_client.start_chat(history=[])
            if test_session:
                print("Paid client connection test successful")
                return True
            else:
                raise Exception("Failed to create test session")
        except Exception as e:
            print(f"Paid client connection test failed: {e}")
            raise
    
    def start_new_chat(self, chat_id: str = None) -> Any:
        """Start a new chat session."""
        if not self._initialized:
            raise RuntimeError("Gemini client not initialized")
        
        if self._mode == "free":
            return self._start_free_chat(chat_id)
        else:
            return self._start_paid_chat(chat_id)
    
    def _start_free_chat(self, chat_id: str = None) -> ChatSession:
        """Start a new free chat session."""
        try:
            chat_session = self._free_client.start_chat()
            
            if chat_id:
                self._sessions[chat_id] = chat_session
            
            return chat_session
        except Exception as e:
            print(f"Error starting free chat: {e}")
            raise
    
    def _start_paid_chat(self, chat_id: str = None) -> Any:
        """Start a new paid chat session."""
        try:
            chat_session = self._paid_client.start_chat(history=[])
            
            if chat_id:
                self._sessions[chat_id] = chat_session
            
            return chat_session
        except Exception as e:
            print(f"Error starting paid chat: {e}")
            raise
    
    def load_chat_from_metadata(self, metadata: Dict[str, Any]) -> Any:
        """Load a chat session from metadata."""
        if not self._initialized:
            raise RuntimeError("Gemini client not initialized")
        
        try:
            session_id = metadata.get("session_id")
            if not session_id:
                raise ValueError("No session_id in metadata")
            
            # Try to get existing session
            if session_id in self._sessions:
                return self._sessions[session_id]
            
            # Create new session and store it
            chat_session = self.start_new_chat(session_id)
            return chat_session
            
        except Exception as e:
            print(f"Error loading chat from metadata: {e}")
            raise
    
    async def send_message(
        self, 
        chat_session: Any, 
        prompt: str, 
        files: Optional[List[str]] = None
    ):
        """Send a message to a chat session."""
        if not self._initialized:
            raise RuntimeError("Gemini client not initialized")
        
        try:
            if self._mode == "free":
                return await self._send_free_message(chat_session, prompt, files)
            else:
                return await self._send_paid_message(chat_session, prompt, files)
                
        except Exception as e:
            print(f"Error sending message: {e}")
            raise
    
    async def _send_free_message(self, chat_session: ChatSession, prompt: str, files: Optional[List[str]] = None):
        """Send message using free client."""
        try:
            # Prepare files if provided
            file_data = []
            if files:
                for file_path in files:
                    if os.path.exists(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if mime_type and mime_type.startswith('image/'):
                            with open(file_path, 'rb') as f:
                                file_data.append({
                                    "mime_type": mime_type,
                                    "data": f.read()
                                })
            
            # Send message
            if file_data:
                response = await chat_session.send_message(prompt, files=file_data)
            else:
                response = await chat_session.send_message(prompt)
            
            return response
            
        except Exception as e:
            print(f"Error sending free message: {e}")
            raise
    
    async def _send_paid_message(self, chat_session: Any, prompt: str, files: Optional[List[str]] = None):
        """Send message using paid client."""
        try:
            # Prepare content parts
            content_parts = [prompt]
            
            # Add files if provided
            if files:
                for file_path in files:
                    if os.path.exists(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if mime_type and mime_type.startswith('image/'):
                            with open(file_path, 'rb') as f:
                                content_parts.append({
                                    "mime_type": mime_type,
                                    "data": f.read()
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
            print(f"Error sending paid message: {e}")
            raise
    
    async def switch_mode(self, new_mode: Literal["free", "paid"]) -> bool:
        """Switch between free and paid modes."""
        if new_mode == self._mode:
            print(f"Already in {new_mode} mode")
            return True
        
        print(f"Switching from {self._mode} to {new_mode} mode...")
        
        # Close current sessions
        await self.close_client()
        
        # Initialize new mode
        success = await self.init_client(new_mode)
        if success:
            print(f"Successfully switched to {new_mode} mode")
        else:
            print(f"Failed to switch to {new_mode} mode")
        
        return success
    
    async def close_client(self):
        """Close the client and clean up resources."""
        try:
            # Close all sessions
            for session in self._sessions.values():
                try:
                    if hasattr(session, 'close'):
                        await session.close()
                except:
                    pass
            
            self._sessions.clear()
            self._free_client = None
            self._paid_client = None
            self._initialized = False
            print("Gemini client closed")
        except Exception as e:
            print(f"Error closing client: {e}")
    
    @property
    def mode(self) -> str:
        """Get current mode."""
        return self._mode
    
    @property
    def is_initialized(self) -> bool:
        """Check if the client is properly initialized."""
        return self._initialized