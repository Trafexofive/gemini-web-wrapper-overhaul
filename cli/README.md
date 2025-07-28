# Gemini Web Wrapper CLI Client

A powerful command-line interface for the Gemini Web Wrapper API, providing easy access to all features from your terminal.

## Features

- 🚀 **Full API Coverage**: All API endpoints supported
- 🎨 **Colored Output**: Beautiful, readable terminal output
- 🔧 **Interactive Mode**: Chat directly from the command line
- 📝 **JSON Handling**: Automatic JSON parsing and formatting
- 🐛 **Debug Mode**: Detailed logging for troubleshooting
- 🔗 **Flexible Configuration**: Environment variables and command-line options

## Installation

### Prerequisites

The CLI requires the following dependencies:

- `bash` (version 4.0 or higher)
- `curl` (for HTTP requests)
- `jq` (for JSON parsing)

### Install Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install curl jq
```

#### CentOS/RHEL/Fedora:
```bash
sudo yum install curl jq
# or for newer versions:
sudo dnf install curl jq
```

#### macOS:
```bash
brew install curl jq
```

### Setup

1. Make the script executable:
```bash
chmod +x cli/gemini-cli.sh
```

2. (Optional) Add to your PATH:
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/your/project/cli"

# Or create a symlink
sudo ln -s /path/to/your/project/cli/gemini-cli.sh /usr/local/bin/gemini-cli
```

## Quick Start

### 1. Check API Health
```bash
./cli/gemini-cli.sh health
```

### 2. List Chat Sessions
```bash
./cli/gemini-cli.sh chats
```

### 3. Create a New Chat
```bash
./cli/gemini-cli.sh create "My first chat" "Creative"
```

### 4. Send a Message
```bash
./cli/gemini-cli.sh send "Hello, how are you?"
```

### 5. Interactive Chat Mode
```bash
./cli/gemini-cli.sh chat
```

## Usage

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `health` | Check API health | `./cli/gemini-cli.sh health` |
| `chats` | List all chat sessions | `./cli/gemini-cli.sh chats` |
| `active` | Show active chat session | `./cli/gemini-cli.sh active` |
| `create` | Create new chat session | `./cli/gemini-cli.sh create "Description" "Mode"` |
| `set-active` | Set active chat session | `./cli/gemini-cli.sh set-active abc123def` |
| `delete` | Delete chat session | `./cli/gemini-cli.sh delete abc123def` |
| `send` | Send message to chat | `./cli/gemini-cli.sh send "Message" [chat_id]` |
| `chat` | Start interactive chat mode | `./cli/gemini-cli.sh chat [chat_id]` |

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `-h, --help` | Show help message | `./cli/gemini-cli.sh --help` |
| `-v, --version` | Show version | `./cli/gemini-cli.sh --version` |
| `-d, --debug` | Enable debug output | `./cli/gemini-cli.sh -d chats` |
| `--api-url` | Set API base URL | `./cli/gemini-cli.sh --api-url http://localhost:8000 health` |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_URL` | API base URL | `http://localhost:8000` |
| `DEBUG` | Enable debug output | `false` |

## Examples

### Chat Session Management

```bash
# Create a new chat session
./cli/gemini-cli.sh create "Project brainstorming" "Creative"

# List all chats
./cli/gemini-cli.sh chats

# Set a chat as active
./cli/gemini-cli.sh set-active abc123def

# Delete a chat session
./cli/gemini-cli.sh delete abc123def
```

### Sending Messages

```bash
# Send to active chat
./cli/gemini-cli.sh send "What's the weather like?"

# Send to specific chat
./cli/gemini-cli.sh send "Hello there!" abc123def

# Send with debug output
./cli/gemini-cli.sh -d send "Debug this message"
```

### Interactive Chat Mode

```bash
# Start interactive chat with default chat
./cli/gemini-cli.sh chat

# Start interactive chat with specific chat
./cli/gemini-cli.sh chat abc123def
```

In interactive mode, you can use these commands:
- `quit` or `exit` - End the session
- `help` - Show available commands
- `clear` - Clear the screen
- `status` - Show current chat status

### Using Different API Endpoints

```bash
# Connect to remote API
./cli/gemini-cli.sh --api-url http://my-server:8000 health

# Using environment variable
export GEMINI_API_URL="http://my-server:8000"
./cli/gemini-cli.sh chats
```

## Docker Integration

### Using with Docker Compose

```bash
# Check health of containerized API
./cli/gemini-cli.sh --api-url http://localhost:8000 health

# Interactive chat with containerized API
./cli/gemini-cli.sh --api-url http://localhost:8000 chat
```

### Running CLI in Container

```bash
# Run CLI from within the API container
docker-compose exec gemini-api ./cli/gemini-cli.sh health

# Or SSH into container and run CLI
make ssh service=gemini-api
./cli/gemini-cli.sh chats
```

## Troubleshooting

### Common Issues

#### 1. "Missing required dependencies"
**Error**: `Missing required dependencies: curl jq`

**Solution**: Install the missing packages:
```bash
# Ubuntu/Debian
sudo apt install curl jq

# CentOS/RHEL
sudo yum install curl jq

# macOS
brew install curl jq
```

#### 2. "API is not responding"
**Error**: `API is not responding`

**Solutions**:
- Check if the API server is running
- Verify the API URL is correct
- Check firewall settings
- Ensure the API is accessible from your network

#### 3. "Permission denied"
**Error**: `Permission denied`

**Solution**: Make the script executable:
```bash
chmod +x cli/gemini-cli.sh
```

#### 4. "Could not parse JSON response"
**Error**: `Could not parse JSON response, showing raw output`

**Solutions**:
- Check if the API is returning valid JSON
- Enable debug mode to see the raw response
- Verify the API endpoint is correct

### Debug Mode

Enable debug mode to see detailed information about API requests and responses:

```bash
# Enable debug for a single command
./cli/gemini-cli.sh -d send "Hello"

# Enable debug globally
export DEBUG=true
./cli/gemini-cli.sh chats
```

### Testing API Connectivity

```bash
# Test basic connectivity
curl -s http://localhost:8000/health

# Test with authentication (if required)
curl -s -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/v1/chats
```

## Advanced Usage

### Scripting

The CLI can be used in scripts for automation:

```bash
#!/bin/bash

# Create a new chat and send a message
CHAT_ID=$(./cli/gemini-cli.sh create "Automated chat" "Default")
./cli/gemini-cli.sh send "This is an automated message" "$CHAT_ID"
```

### Integration with Other Tools

```bash
# Pipe output to other commands
./cli/gemini-cli.sh chats | grep "My Chat"

# Use in combination with other tools
./cli/gemini-cli.sh send "Generate a random number" | jq -r '.content' | grep -o '[0-9]*'
```

## Contributing

To contribute to the CLI client:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This CLI client is part of the Gemini Web Wrapper project and follows the same license terms.