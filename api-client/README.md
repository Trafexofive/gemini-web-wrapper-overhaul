# Gemini API Client

A comprehensive bash client for interacting with the Gemini Web Wrapper API. Supports both JWT authentication (for local development) and API key authentication (for external users).

## Features

- **API Key Authentication**: Primary method for external users
- **JWT Authentication**: For local development and admin tasks
- **Chat Management**: Create, list, delete, and manage chats
- **Messaging**: Send messages and get AI responses
- **API Key Management**: Create, list, and delete API keys
- **Health Checks**: Verify API status
- **Token/Key Persistence**: Automatically saves and loads authentication

## Requirements

- `bash` (version 4.0 or higher)
- `curl` for HTTP requests
- `jq` for JSON parsing

## Installation

1. Make sure you have the required dependencies:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install curl jq
   
   # On macOS
   brew install curl jq
   
   # On CentOS/RHEL
   sudo yum install curl jq
   ```

2. Make the script executable:
   ```bash
   chmod +x api_client.sh
   ```

## Configuration

The client uses the following environment variables:

- `API_BASE_URL`: API base URL (default: `http://localhost:8000/v1`)
- `TOKEN_FILE`: JWT token file path (default: `~/.gemini_token`)
- `API_KEY_FILE`: API key file path (default: `~/.gemini_api_key`)

## Usage

### For External Users (API Key Authentication)

This is the primary method for users who want to use the API from external scripts or systems.

```bash
# 1. Get your API key from the frontend
# Go to your Gemini frontend -> API Keys -> Create new key

# 2. Set your API key
./api_client.sh set_api_key "your-api-key-here"

# 3. Check if API is accessible
./api_client.sh health_check

# 4. Create a chat and send a message
CHAT_ID=$(./api_client.sh create_chat "My first chat")
./api_client.sh send_message "Hello, how are you?" "$CHAT_ID"

# 5. List all your chats
./api_client.sh list_chats

# 6. Clear your API key when done
./api_client.sh clear_api_key
```

### For Local Development (JWT Authentication)

This is for developers who want to manage the API locally.

```bash
# Show help
./api_client.sh help

# Check API health
./api_client.sh health_check

# Register a new account
./api_client.sh register test@example.com password123 myusername

# Login
./api_client.sh login test@example.com password123

# Create an API key for external use
./api_client.sh create_api_key "external-script"

# Logout
./api_client.sh logout
```

### Chat Management

```bash
# List all chats
./api_client.sh list_chats

# Create a new chat
./api_client.sh create_chat "My new chat" "Code"

# Set active chat
./api_client.sh set_active_chat "chat_id_here"

# Get active chat ID
./api_client.sh get_active_chat

# Delete a chat
./api_client.sh delete_chat "chat_id_here"
```

### Messaging

```bash
# Send a message to the active chat
./api_client.sh send_message "Hello, how are you?"

# Send a message to a specific chat
./api_client.sh send_message "What's the weather like?" "chat_id_here"
```

### API Key Management (requires JWT)

```bash
# List all API keys
./api_client.sh list_api_keys

# Create a new API key
./api_client.sh create_api_key "my-api-key"

# Delete an API key
./api_client.sh delete_api_key "key_id_here"
```

## Examples

### Complete Workflow for External Users

```bash
#!/bin/bash
# Example script for external users

# Set your API key (get this from the frontend)
./api_client.sh set_api_key "your-api-key-here"

# Check API health
./api_client.sh health_check

# Create a chat for code review
CHAT_ID=$(./api_client.sh create_chat "Code Review Session" "Code")

# Send code for review
CODE=$(cat my_script.py)
./api_client.sh send_message "Please review this code: $CODE" "$CHAT_ID"

# Get the response
RESPONSE=$(./api_client.sh send_message "What improvements would you suggest?" "$CHAT_ID")
echo "AI Response: $RESPONSE"

# Clean up
./api_client.sh clear_api_key
```

### Using with Different API URLs

```bash
# Use a different API URL
API_BASE_URL=http://my-server:8000/v1 ./api_client.sh health_check

# Use custom token/key files
TOKEN_FILE=/path/to/my/token ./api_client.sh login user@example.com password
API_KEY_FILE=/path/to/my/api_key ./api_client.sh set_api_key "my-key"
```

## Error Handling

The client provides colored output for different types of messages:

- 🔵 **Blue**: Information messages
- 🟢 **Green**: Success messages
- 🟡 **Yellow**: Warning messages
- 🔴 **Red**: Error messages

## Security

- Authentication tokens and API keys are stored with restricted permissions (600)
- API keys are displayed only once when created
- All sensitive data is handled securely
- API keys are sent via `X-API-Key` header (not Authorization)

## Troubleshooting

### Common Issues

1. **"jq is required but not installed"**
   - Install jq: `sudo apt-get install jq` (Ubuntu/Debian) or `brew install jq` (macOS)

2. **"curl is required but not installed"**
   - Install curl: `sudo apt-get install curl` (Ubuntu/Debian) or `brew install curl` (macOS)

3. **"Could not validate credentials"**
   - Check if your API key is correct
   - Make sure the API is running and accessible
   - Verify the API key was generated from the frontend

4. **"Failed to send message: No active chat"**
   - Create a chat first: `./api_client.sh create_chat "My chat"`
   - Or specify a chat ID: `./api_client.sh send_message "Hello" "chat_id"`

5. **"Connection refused"**
   - Check if the API server is running
   - Verify the `API_BASE_URL` is correct

### Getting Your API Key

1. **Access the Frontend**: Go to your Gemini web wrapper frontend
2. **Navigate to API Keys**: Click on the API Keys link in the header
3. **Create New Key**: Click "Create" and enter a name for your key
4. **Copy the Key**: The API key will be displayed once - copy it immediately
5. **Use in Script**: Set it in your script with `./api_client.sh set_api_key "your-key"`

### Debug Mode

To see detailed curl commands, you can modify the script to add `-v` flag to curl:

```bash
# In the api_request function, change:
local curl_cmd="curl -s -X $method \"$url\""

# To:
local curl_cmd="curl -s -v -X $method \"$url\""
```

## Integration Examples

### Python Script Integration

```python
#!/usr/bin/env python3
import subprocess
import json

def call_api_client(command, *args):
    """Call the bash API client and return the result"""
    cmd = ["./api_client.sh", command] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

# Set API key
stdout, code = call_api_client("set_api_key", "your-api-key-here")
if code != 0:
    print(f"Failed to set API key: {stdout}")
    exit(1)

# Create chat and send message
chat_id, code = call_api_client("create_chat", "Python Script Chat")
if code == 0:
    response, code = call_api_client("send_message", "Hello from Python!", chat_id)
    print(f"AI Response: {response}")
```

### Shell Script Integration

```bash
#!/bin/bash
# Example automation script

# Set API key
./api_client.sh set_api_key "your-api-key-here"

# Create a chat for automated tasks
CHAT_ID=$(./api_client.sh create_chat "Automated Tasks" "General")

# Send a message and capture response
RESPONSE=$(./api_client.sh send_message "What's the current date and time?" "$CHAT_ID")
echo "Current info: $RESPONSE"

# Send another message
RESPONSE=$(./api_client.sh send_message "What's the weather like today?" "$CHAT_ID")
echo "Weather info: $RESPONSE"

# Clean up
./api_client.sh clear_api_key
```

## License

MIT License - see the main project license for details.