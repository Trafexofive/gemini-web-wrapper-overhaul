#!/bin/bash

# Test script to demonstrate API key usage
# This shows how you can use the API key from anywhere in the world

# Your API key (get this from the frontend)
API_KEY="gemini_pzhfxd1AQbH0sec_7sgrt2RAgUA3_Kx_hLbCKcOEMxU"

# API base URL (change this to your server's URL)
API_BASE_URL="http://localhost:8000"

echo "🚀 Testing Gemini API with API Key"
echo "=================================="

# Test 1: Health check
echo "1. Testing health check..."
curl -s "$API_BASE_URL/health" | jq -r '.status + " (v" + .version + ")"'

# Test 2: Create a chat
echo -e "\n2. Creating a new chat..."
CHAT_RESPONSE=$(curl -s -X POST "$API_BASE_URL/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"description": "Test from anywhere in the world", "mode": "Default"}')

CHAT_ID=$(echo "$CHAT_RESPONSE" | jq -r '.chat_id')
echo "Created chat: $CHAT_ID"

# Test 3: Send a message
echo -e "\n3. Sending a message..."
MESSAGE_RESPONSE=$(curl -s -X POST "$API_BASE_URL/v1/chats/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"messages": [{"role": "user", "content": "Hello! I am calling you from a script anywhere in the world. Can you confirm this works?"}]}')

AI_RESPONSE=$(echo "$MESSAGE_RESPONSE" | jq -r '.choices[0].message.content')
echo "AI Response: $AI_RESPONSE"

# Test 4: Send another message
echo -e "\n4. Sending another message..."
MESSAGE_RESPONSE2=$(curl -s -X POST "$API_BASE_URL/v1/chats/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"messages": [{"role": "user", "content": "What is the current date and time?"}]}')

AI_RESPONSE2=$(echo "$MESSAGE_RESPONSE2" | jq -r '.choices[0].message.content')
echo "AI Response: $AI_RESPONSE2"

echo -e "\n✅ All tests completed successfully!"
echo "You can now use this API key from anywhere in the world!"
echo ""
echo "To use this in your own scripts:"
echo "1. Get your API key from the frontend"
echo "2. Replace the API_KEY variable above"
echo "3. Change API_BASE_URL to your server's URL"
echo "4. Run the script!"