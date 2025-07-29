#!/bin/bash

# Debug script to see what's different between bash client and direct curl

API_KEY="gemini_pzhfxd1AQbH0sec_7sgrt2RAgUA3_Kx_hLbCKcOEMxU"
API_BASE_URL="http://localhost:8000"

echo "🔍 Debugging API Key Authentication"
echo "=================================="

echo "1. Testing with bash client (working):"
./api_client.sh set_api_key "$API_KEY"
./api_client.sh create_chat "Debug test"

echo -e "\n2. Testing with direct curl (not working):"
curl -v -X POST "$API_BASE_URL/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"description": "Debug test", "mode": "General"}'

echo -e "\n3. Testing with bash client's exact curl command:"
# Let's see what the bash client is actually sending
bash -x ./api_client.sh create_chat "Debug test 2" 2>&1 | grep "curl"