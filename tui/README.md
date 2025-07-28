# Gemini Web Wrapper TUI Client

A modern Terminal User Interface (TUI) client for the Gemini Web Wrapper API.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r tui_requirements.txt

# Run the TUI client
python tui_client.py

# Connect to custom API endpoint
python tui_client.py http://your-api-host:8000
```

### Docker

```bash
# Build the TUI image
docker build -t gemini-tui .

# Run with default API endpoint (localhost:8000)
docker run -it --rm gemini-tui

# Run with custom API endpoint
docker run -it --rm -e API_BASE_URL=http://your-api-host:8000 gemini-tui
```

### Docker Compose

```bash
# Start both API and TUI services
docker-compose --profile tui up

# Or run just the TUI (requires API to be running)
docker-compose --profile tui run gemini-tui
```

## Features

- 🖥️ Modern TUI interface using Textual
- 💬 Real-time chat with Gemini
- 📋 Chat session management
- 🎨 Rich text display with timestamps
- ⚡ Async operations

## Environment Variables

- `API_BASE_URL`: API endpoint URL (default: http://localhost:8000)

## Navigation

- **Tab/Arrow Keys**: Navigate between elements
- **Enter**: Select items, send messages
- **Ctrl+C**: Exit the application
- **Mouse**: Click to interact (if supported)

## Troubleshooting

### Connection Issues

```bash
# Check if API is running
curl http://localhost:8000/health

# Test with custom endpoint
python tui_client.py http://your-api-host:8000
```

### Docker Issues

```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs gemini-tui
```