#!/usr/bin/env python3
"""
TUI Client for Gemini Web Wrapper
A terminal user interface for managing chat sessions and conversations with Gemini.
"""

import asyncio
import json
import sys
from typing import List, Optional, Dict, Any
import httpx
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, DataTable, Header, Footer, Input, Label, 
    Log, Select, Static, TextArea, RichLog
)
from textual.widgets.data_table import RowKey
from textual.reactive import reactive
from textual import events
from textual import work
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
import time

# Configuration
import os
DEFAULT_API_BASE = "http://localhost:8000"
API_BASE = os.getenv("API_BASE_URL", DEFAULT_API_BASE)

class ChatInfo:
    """Represents a chat session"""
    def __init__(self, chat_id: str, description: str = None, mode: str = None):
        self.chat_id = chat_id
        self.description = description or "No description"
        self.mode = mode or "Default"

class ChatListWidget(DataTable):
    """Widget for displaying and managing chat sessions"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_columns("ID", "Description", "Mode")
        self.chats: List[ChatInfo] = []
        self.selected_chat_id: Optional[str] = None
    
    def update_chats(self, chats: List[ChatInfo]):
        """Update the chat list with new data"""
        self.chats = chats
        self.clear()
        
        for chat in chats:
            self.add_row(
                chat.chat_id[:8] + "...",  # Truncate ID for display
                chat.description,
                chat.mode,
                key=chat.chat_id
            )
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle chat selection"""
        if event.row_key:
            self.selected_chat_id = event.row_key.value
            self.post_message(self.ChatSelected(self.selected_chat_id))
    
    class ChatSelected:
        """Message sent when a chat is selected"""
        def __init__(self, chat_id: str):
            self.chat_id = chat_id

class ChatInputWidget(Container):
    """Widget for inputting chat messages"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_input = TextArea()
        self.message_input.text = "Type your message here..."
        self.send_button = Button("Send", variant="primary")
    
    def compose(self) -> ComposeResult:
        yield self.message_input
        yield self.send_button
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle send button press"""
        if event.button == self.send_button:
            message = self.message_input.text.strip()
            if message:
                self.post_message(self.MessageSent(message))
                self.message_input.text = ""
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses"""
        if event.key == "enter":
            event.prevent_default()
            self.send_button.press()
    
    class MessageSent:
        """Message sent when user submits a message"""
        def __init__(self, message: str):
            self.message = message

class ChatLogWidget(RichLog):
    """Widget for displaying chat conversation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, timestamp: str = None):
        """Add a message to the chat log"""
        if timestamp is None:
            timestamp = time.strftime("%H:%M:%S")
        
        if role == "user":
            self.write(f"[bold blue]{timestamp}[/bold blue] [bold]You:[/bold] {content}")
        elif role == "assistant":
            self.write(f"[bold green]{timestamp}[/bold green] [bold]Gemini:[/bold] {content}")
        elif role == "system":
            self.write(f"[bold yellow]{timestamp}[/bold yellow] [bold]System:[/bold] {content}")
        
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
    
    def clear_messages(self):
        """Clear all messages"""
        self.clear()
        self.messages.clear()

class GeminiTUIApp(App):
    """Main TUI application for Gemini Web Wrapper"""
    
    CSS = """
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #sidebar {
        width: 30%;
        border-right: solid green;
        layout: vertical;
    }
    
    #chat-area {
        width: 70%;
        layout: vertical;
    }
    
    #chat-controls {
        height: auto;
        padding: 1;
        border-bottom: solid green;
    }
    
    #chat-log {
        height: 1fr;
        border: solid green;
        margin: 1;
    }
    
    #chat-input {
        height: auto;
        padding: 1;
        border-top: solid green;
    }
    
    #chat-input TextArea {
        height: 3;
        margin-bottom: 1;
    }
    
    #status-bar {
        height: auto;
        padding: 1;
        background: $accent;
        color: $text;
    }
    
    .error {
        color: red;
    }
    
    .success {
        color: green;
    }
    
    .warning {
        color: yellow;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.api_base = API_BASE
        self.active_chat_id: Optional[str] = None
        self.chats: List[ChatInfo] = []
        self.http_client: Optional[httpx.AsyncClient] = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Container(id="sidebar"):
                yield Label("Chat Sessions", classes="title")
                yield Button("New Chat", id="new-chat-btn", variant="primary")
                yield Button("Refresh", id="refresh-btn")
                yield ChatListWidget(id="chat-list")
            
            with Container(id="chat-area"):
                with Container(id="chat-controls"):
                    yield Label("No active chat", id="active-chat-label")
                    yield Button("Set Active", id="set-active-btn")
                    yield Button("Delete Chat", id="delete-chat-btn", variant="error")
                
                yield ChatLogWidget(id="chat-log")
                
                with Container(id="chat-input"):
                    yield ChatInputWidget()
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted"""
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.load_chats()
    
    def on_unmount(self) -> None:
        """Called when the app is unmounted"""
        if self.http_client:
            asyncio.create_task(self.http_client.aclose())
    
    @work
    async def load_chats(self) -> None:
        """Load chat sessions from the API"""
        try:
            response = await self.http_client.get(f"{self.api_base}/v1/chats")
            response.raise_for_status()
            
            chats_data = response.json()
            self.chats = [
                ChatInfo(
                    chat_id=chat["chat_id"],
                    description=chat["description"],
                    mode=chat["mode"]
                )
                for chat in chats_data
            ]
            
            # Update the UI
            chat_list = self.query_one("#chat-list", ChatListWidget)
            chat_list.update_chats(self.chats)
            
            # Get active chat
            await self.load_active_chat()
            
        except Exception as e:
            self.log.error(f"Failed to load chats: {e}")
            self.notify(f"Error loading chats: {e}", severity="error")
    
    @work
    async def load_active_chat(self) -> None:
        """Load the currently active chat"""
        try:
            response = await self.http_client.get(f"{self.api_base}/v1/chats/active")
            response.raise_for_status()
            
            data = response.json()
            self.active_chat_id = data.get("active_chat_id")
            
            # Update UI
            active_label = self.query_one("#active-chat-label", Label)
            if self.active_chat_id:
                active_label.update(f"Active: {self.active_chat_id[:8]}...")
            else:
                active_label.update("No active chat")
                
        except Exception as e:
            self.log.error(f"Failed to load active chat: {e}")
    
    @work
    async def create_chat(self, description: str = None, mode: str = "Default") -> None:
        """Create a new chat session"""
        try:
            payload = {
                "description": description,
                "mode": mode
            }
            
            response = await self.http_client.post(
                f"{self.api_base}/v1/chats",
                json=payload
            )
            response.raise_for_status()
            
            new_chat_id = response.json()
            self.notify(f"Created new chat: {new_chat_id[:8]}...", severity="information")
            
            # Reload chats
            await self.load_chats()
            
        except Exception as e:
            self.log.error(f"Failed to create chat: {e}")
            self.notify(f"Error creating chat: {e}", severity="error")
    
    @work
    async def set_active_chat(self, chat_id: str) -> None:
        """Set the active chat session"""
        try:
            payload = {"chat_id": chat_id}
            
            response = await self.http_client.post(
                f"{self.api_base}/v1/chats/active",
                json=payload
            )
            response.raise_for_status()
            
            self.active_chat_id = chat_id
            await self.load_active_chat()
            
            # Clear chat log for new active chat
            chat_log = self.query_one("#chat-log", ChatLogWidget)
            chat_log.clear_messages()
            chat_log.add_message("system", f"Switched to chat: {chat_id[:8]}...")
            
            self.notify(f"Active chat set to: {chat_id[:8]}...", severity="information")
            
        except Exception as e:
            self.log.error(f"Failed to set active chat: {e}")
            self.notify(f"Error setting active chat: {e}", severity="error")
    
    @work
    async def delete_chat(self, chat_id: str) -> None:
        """Delete a chat session"""
        try:
            response = await self.http_client.delete(f"{self.api_base}/v1/chats/{chat_id}")
            response.raise_for_status()
            
            self.notify(f"Deleted chat: {chat_id[:8]}...", severity="information")
            
            # If this was the active chat, clear it
            if self.active_chat_id == chat_id:
                self.active_chat_id = None
                await self.load_active_chat()
                
                chat_log = self.query_one("#chat-log", ChatLogWidget)
                chat_log.clear_messages()
                chat_log.add_message("system", "Active chat deleted")
            
            # Reload chats
            await self.load_chats()
            
        except Exception as e:
            self.log.error(f"Failed to delete chat: {e}")
            self.notify(f"Error deleting chat: {e}", severity="error")
    
    @work
    async def send_message(self, message: str) -> None:
        """Send a message to the active chat"""
        if not self.active_chat_id:
            self.notify("No active chat selected", severity="warning")
            return
        
        try:
            # Add user message to log
            chat_log = self.query_one("#chat-log", ChatLogWidget)
            chat_log.add_message("user", message)
            
            # Prepare request payload
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
            
            # Send to API
            response = await self.http_client.post(
                f"{self.api_base}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            assistant_message = data["choices"][0]["message"]["content"]
            
            # Add assistant response to log
            chat_log.add_message("assistant", assistant_message)
            
        except Exception as e:
            self.log.error(f"Failed to send message: {e}")
            self.notify(f"Error sending message: {e}", severity="error")
            chat_log.add_message("system", f"Error: {e}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "new-chat-btn":
            # Create a simple new chat
            asyncio.create_task(self.create_chat())
        
        elif button_id == "refresh-btn":
            asyncio.create_task(self.load_chats())
        
        elif button_id == "set-active-btn":
            chat_list = self.query_one("#chat-list", ChatListWidget)
            if chat_list.selected_chat_id:
                asyncio.create_task(self.set_active_chat(chat_list.selected_chat_id))
            else:
                self.notify("Please select a chat first", severity="warning")
        
        elif button_id == "delete-chat-btn":
            chat_list = self.query_one("#chat-list", ChatListWidget)
            if chat_list.selected_chat_id:
                asyncio.create_task(self.delete_chat(chat_list.selected_chat_id))
            else:
                self.notify("Please select a chat first", severity="warning")
    
    def on_chat_list_chat_selected(self, event: ChatListWidget.ChatSelected) -> None:
        """Handle chat selection"""
        # This is handled by the ChatListWidget itself
        pass
    
    def on_chat_input_message_sent(self, event: ChatInputWidget.MessageSent) -> None:
        """Handle message submission"""
        asyncio.create_task(self.send_message(event.message))

def main():
    """Main entry point"""
    # Check if API base URL is provided as command line argument
    global API_BASE
    if len(sys.argv) > 1:
        API_BASE = sys.argv[1]
    
    print(f"Connecting to Gemini API at: {API_BASE}")
    print("Press Ctrl+C to exit")
    
    try:
        app = GeminiTUIApp()
        app.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()