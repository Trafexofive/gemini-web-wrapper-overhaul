# Gemini Web Wrapper with Portainer

A comprehensive Gemini API wrapper with session management, featuring a web interface, modern TUI client, and powerful CLI client.

## 🏗️ Project Structure

```
gemini-web-wrapper-portainer/
├── api/                    # Backend API files
│   ├── app/               # FastAPI application
│   │   ├── core/          # Core components (Gemini client)
│   │   ├── models.py      # Pydantic models
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── config.py      # Configuration
│   │   ├── routers/       # API routes
│   │   ├── services/      # Business logic
│   │   ├── repositories/  # Data access layer
│   │   └── prompts/       # System prompts
│   ├── Dockerfile         # API container definition
│   └── requirements.txt   # API dependencies
├── tui/                   # Terminal User Interface
│   ├── tui_client.py      # TUI application
│   ├── Dockerfile         # TUI container definition
│   ├── requirements.txt   # TUI dependencies
│   ├── install_tui.sh     # Installation script
│   └── README.md          # TUI documentation
├── cli/                   # Command Line Interface
│   ├── gemini-cli.sh      # Main CLI script
│   ├── install.sh         # CLI installation script
│   └── README.md          # CLI documentation
├── static/                # Frontend web interface
├── docker-compose.yml     # Docker services configuration
├── Makefile              # Docker management commands
├── main.py               # Root entry point for API
├── requirements.txt      # Combined dependencies
└── README.md            # This file
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start API only
docker-compose up gemini-api

# Start both API and TUI
docker-compose --profile tui up

# Or use Makefile
make up                    # API only
make up profile=tui        # API + TUI
```

### Option 2: Local Development

```bash
# Install all dependencies
pip install -r requirements.txt

# Start the API server
python main.py

# In another terminal, start the TUI client
cd tui
python tui_client.py
```

### Option 3: Individual Docker Services

```bash
# Build and run API
cd api
docker build -t gemini-api .
docker run -p 8000:8000 gemini-api

# Build and run TUI
cd tui
docker build -t gemini-tui .
docker run -it --rm gemini-tui
```

## 🖥️ TUI Client

The project includes a modern Terminal User Interface client:

```bash
# Navigate to TUI directory
cd tui

# Install TUI dependencies
pip install -r tui_requirements.txt

# Run the TUI client
python tui_client.py

# Connect to custom API endpoint
python tui_client.py http://your-api-host:8000
```

### TUI Features
- 📋 Chat session management
- 💬 Real-time messaging with Gemini
- 🎨 Rich text display with timestamps
- ⚡ Async operations for smooth performance

## 💻 CLI Client

The project includes a powerful Command Line Interface client for automation and scripting:

```bash
# Quick installation
cd cli
./install.sh

# Basic usage
./cli/gemini-cli.sh --help
./cli/gemini-cli.sh health
./cli/gemini-cli.sh chats
./cli/gemini-cli.sh send "Hello, how are you?"
./cli/gemini-cli.sh chat
```

### CLI Features
- 🚀 **Full API Coverage**: All API endpoints supported
- 🎨 **Colored Output**: Beautiful, readable terminal output
- 🔧 **Interactive Mode**: Chat directly from the command line
- 📝 **JSON Handling**: Automatic JSON parsing and formatting
- 🐛 **Debug Mode**: Detailed logging for troubleshooting
- 🔗 **Flexible Configuration**: Environment variables and command-line options

### CLI Commands
- `health` - Check API health
- `chats` - List all chat sessions
- `active` - Show active chat session
- `create [DESC] [MODE]` - Create new chat session
- `set-active <CHAT_ID>` - Set active chat session
- `delete <CHAT_ID>` - Delete chat session
- `send <MESSAGE> [CHAT_ID]` - Send message to chat
- `chat [CHAT_ID]` - Start interactive chat mode

### CLI Examples
```bash
# Create and use a chat session
CHAT_ID=$(./cli/gemini-cli.sh create "Project brainstorming" "Creative")
./cli/gemini-cli.sh send "Help me plan a new project" "$CHAT_ID"

# Interactive chat mode
./cli/gemini-cli.sh chat

# Connect to remote API
./cli/gemini-cli.sh --api-url http://my-server:8000 health
```

For detailed CLI documentation, see [cli/README.md](cli/README.md).

## 🌐 Web Interface

Access the web interface at `http://localhost:8000` after starting the API server.

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./gemini_chats.db
```

### API Endpoints

- `GET /v1/chats` - List all chat sessions
- `POST /v1/chats` - Create new chat session
- `POST /v1/chats/active` - Set active chat
- `GET /v1/chats/active` - Get active chat
- `DELETE /v1/chats/{chat_id}` - Delete chat session
- `POST /v1/chat/completions` - Send message to Gemini

## 🐳 Docker Support

### Using Makefile

```bash
# Start services
make up

# Start with TUI
make up profile=tui

# View logs
make logs

# Stop services
make down

# Rebuild and restart
make re
```

### Using Docker Compose Directly

```bash
# Start API only
docker-compose up gemini-api

# Start both services
docker-compose --profile tui up

# Build images
docker-compose build

# View logs
docker-compose logs
```

### Docker Services

- **gemini-api**: Main API service (port 8000)
- **gemini-tui**: TUI client (interactive terminal)

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🛠️ Development

### Running Tests

```bash
# From the api directory
cd api
python -m pytest
```

### Code Formatting

```bash
# Format code with black
black api/app/

# Sort imports with isort
isort api/app/
```

## 📦 Dependencies

### API Dependencies
- FastAPI - Modern web framework
- Uvicorn - ASGI server
- aiosqlite - Async SQLite support
- google-generativeai - Gemini API client
- Pydantic - Data validation

### TUI Dependencies
- Textual - Modern TUI framework
- httpx - Async HTTP client
- Rich - Rich text formatting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
