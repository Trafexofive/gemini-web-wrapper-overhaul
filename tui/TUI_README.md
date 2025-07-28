# Gemini Web Wrapper TUI Client

A modern Terminal User Interface (TUI) client for the Gemini Web Wrapper API, built with Textual.

## Features

- 🖥️ **Modern TUI Interface**: Clean, responsive terminal interface
- 💬 **Chat Management**: Create, select, and delete chat sessions
- 🔄 **Real-time Updates**: Live chat conversation with Gemini
- 🎨 **Rich Text Display**: Colored timestamps and message formatting
- ⚡ **Async Operations**: Non-blocking API calls
- 🔧 **Flexible Configuration**: Connect to any API endpoint

## Screenshot

```
┌─ Gemini Web Wrapper TUI ──────────────────────────────────────────────┐
│ Chat Sessions                    │ No active chat                      │
│ ┌─────────────────────────────┐  │ ┌─────────────────────────────────┐ │
│ │ [New Chat] [Refresh]        │  │ │ Set Active  Delete Chat         │ │
│ │                             │  │ └─────────────────────────────────┘ │
│ │ ID         Description Mode │  │ ┌─────────────────────────────────┐ │
│ │ ────────── ─────────── ──── │  │ │ 14:30:25 You: Hello Gemini!     │ │
│ │ abc123...  Test Chat  Def.. │  │ │ 14:30:26 Gemini: Hello! How...  │ │
│ │ def456...  Code Chat  Code  │  │ │                                 │ │
│ │                             │  │ │                                 │ │
│ │                             │  │ │                                 │ │
│ └─────────────────────────────┘  │ └─────────────────────────────────┘ │
│                                  │ ┌─────────────────────────────────┐ │
│                                  │ │ Type your message here...       │ │
│                                  │ │ [Send]                          │ │
│                                  │ └─────────────────────────────────┘ │
└──────────────────────────────────┴─────────────────────────────────────┘
```

## Installation

### Quick Install

```bash
# Run the installation script
./install_tui.sh
```

### Manual Install

```bash
# Install dependencies
pip3 install -r tui_requirements.txt

# Make executable
chmod +x tui_client.py
```

## Usage

### Basic Usage

```bash
# Connect to default localhost:8000
python3 tui_client.py

# Connect to custom API endpoint
python3 tui_client.py http://192.168.1.100:8000
```

### Interface Navigation

- **Tab/Arrow Keys**: Navigate between elements
- **Enter**: Select items, send messages
- **Ctrl+C**: Exit the application
- **Mouse**: Click to interact (if supported by terminal)

### Chat Management

1. **Create New Chat**: Click "New Chat" button
2. **Select Active Chat**: 
   - Click on a chat in the list
   - Click "Set Active" button
3. **Delete Chat**: 
   - Select a chat in the list
   - Click "Delete Chat" button
4. **Refresh**: Click "Refresh" to reload chat list

### Sending Messages

1. Ensure you have an active chat selected
2. Type your message in the text area
3. Press Enter or click "Send"
4. View Gemini's response in the chat log

## Requirements

- Python 3.7+
- Terminal with color support
- Running Gemini Web Wrapper API

## Dependencies

- `textual>=0.40.0`: Modern TUI framework
- `httpx>=0.24.0`: Async HTTP client
- `rich>=13.0.0`: Rich text and formatting

## API Compatibility

This TUI client is designed to work with the Gemini Web Wrapper API endpoints:

- `GET /v1/chats` - List chat sessions
- `POST /v1/chats` - Create new chat
- `POST /v1/chats/active` - Set active chat
- `GET /v1/chats/active` - Get active chat
- `DELETE /v1/chats/{chat_id}` - Delete chat
- `POST /v1/chat/completions` - Send message

## Troubleshooting

### Connection Issues

```bash
# Check if API is running
curl http://localhost:8000/health

# Test with custom endpoint
python3 tui_client.py http://your-api-host:8000
```

### Display Issues

- Ensure your terminal supports colors
- Try resizing your terminal window
- Check if your terminal supports mouse events

### Performance Issues

- The TUI uses async operations for better performance
- Large chat histories may take time to load
- Network latency affects message response times

## Development

### Running from Source

```bash
# Clone the repository
git clone <your-repo>
cd gemini-web-wrapper-portainer

# Install TUI dependencies
pip3 install -r tui_requirements.txt

# Run the TUI client
python3 tui_client.py
```

### Customization

The TUI client can be customized by modifying:

- `CSS` styles in the `GeminiTUIApp` class
- Widget layouts in the `compose()` method
- API endpoint handling in the async methods

## License

This TUI client is part of the Gemini Web Wrapper project.