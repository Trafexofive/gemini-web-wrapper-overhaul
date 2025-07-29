# 🌍 Using Gemini API from Anywhere in the World

## Quick Start

### 1. Get Your API Key
1. Go to your Gemini frontend: `http://localhost:3000` (or your server URL)
2. Click "API Keys" in the header
3. Click "Create" and enter a name (e.g., "My Script")
4. **Copy the API key immediately** - it's only shown once!

### 2. Use the API Key

#### Option A: Use the Bash Client
```bash
# Download the API client
wget https://your-server.com/api-client/api_client.sh
chmod +x api_client.sh

# Set your API key
./api_client.sh set_api_key "your-api-key-here"

# Test it works
./api_client.sh health_check

# Create a chat and send a message
CHAT_ID=$(./api_client.sh create_chat "My Chat")
./api_client.sh send_message "Hello from anywhere!" "$CHAT_ID"
```

#### Option B: Use Direct curl
```bash
# Your API key
API_KEY="your-api-key-here"
API_URL="http://your-server.com"

# Create a chat
curl -X POST "$API_URL/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"description": "My Chat", "mode": "Default"}'

# Send a message
curl -X POST "$API_URL/v1/chats/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

#### Option C: Use in Python
```python
import requests

API_KEY = "your-api-key-here"
API_URL = "http://your-server.com"

# Create chat
response = requests.post(
    f"{API_URL}/v1/chats/",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"description": "Python Chat", "mode": "Default"}
)
chat_id = response.json()["chat_id"]

# Send message
response = requests.post(
    f"{API_URL}/v1/chats/completions",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"messages": [{"role": "user", "content": "Hello from Python!"}]}
)
ai_response = response.json()["choices"][0]["message"]["content"]
print(ai_response)
```

## Available Modes
- `Default` - General conversation
- `Code` - Programming assistance
- `Architect` - System design
- `Debug` - Debugging help
- `Ask` - Q&A mode

## Example Scripts

### Simple Chat Script
```bash
#!/bin/bash
API_KEY="your-api-key-here"
API_URL="http://your-server.com"

echo "🤖 Gemini Chat Script"
echo "===================="

# Create chat
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"description": "Script Chat", "mode": "Default"}')

CHAT_ID=$(echo "$CHAT_RESPONSE" | jq -r '.chat_id')
echo "Created chat: $CHAT_ID"

# Send message
echo -n "You: "
read MESSAGE

RESPONSE=$(curl -s -X POST "$API_URL/v1/chats/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$MESSAGE\"}]}")

AI_RESPONSE=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
echo "AI: $AI_RESPONSE"
```

### Code Review Script
```bash
#!/bin/bash
API_KEY="your-api-key-here"
API_URL="http://your-server.com"

# Create code review chat
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"description": "Code Review", "mode": "Code"}')

CHAT_ID=$(echo "$CHAT_RESPONSE" | jq -r '.chat_id')

# Send code for review
CODE=$(cat "$1")
curl -s -X POST "$API_URL/v1/chats/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"Please review this code: $CODE\"}]}" | \
  jq -r '.choices[0].message.content'
```

## Security Notes
- Keep your API key secret
- Don't commit it to version control
- Use environment variables in production
- API keys are tied to your user account

## Troubleshooting
- **"Could not validate credentials"**: Check your API key
- **"Connection refused"**: Check the API URL
- **"Invalid mode"**: Use one of: Default, Code, Architect, Debug, Ask

## Ready to Use! 🚀

Your API key works from anywhere in the world. Just replace:
- `your-api-key-here` with your actual API key
- `your-server.com` with your server's URL

Happy coding! 🎉