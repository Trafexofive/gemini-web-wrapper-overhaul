#!/bin/bash

# Gemini Web Wrapper CLI Client
# Supports both free (cookies) and paid (API key) modes

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
CURRENT_MODE=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[CLI]${NC} $1"
}

# Function to make API calls
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE_URL$endpoint"
    else
        curl -s -X "$method" \
            -H "Content-Type: application/json" \
            "$API_BASE_URL$endpoint"
    fi
}

# Function to get current mode
get_current_mode() {
    local response=$(api_call "GET" "/v1/chats/client-mode")
    CURRENT_MODE=$(echo "$response" | jq -r '.mode // "unknown"')
    echo "$response" | jq -r '.description // "Unknown mode"'
}

# Function to switch mode
switch_mode() {
    local mode="$1"
    if [ "$mode" != "free" ] && [ "$mode" != "paid" ]; then
        print_error "Mode must be 'free' or 'paid'"
        return 1
    fi
    
    print_status "Switching to $mode mode..."
    local response=$(api_call "POST" "/v1/chats/client-mode?mode=$mode")
    echo "$response" | jq -r '.message // "Mode switch failed"'
    
    # Update current mode
    get_current_mode > /dev/null
}

# Function to list chats
list_chats() {
    print_header "Listing all chat sessions..."
    local response=$(api_call "GET" "/v1/chats")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.[] | "ID: \(.chat_id) | Mode: \(.mode) | Description: \(.description // "No description")"'
    else
        print_error "Failed to list chats"
    fi
}

# Function to create a new chat
create_chat() {
    local description="$1"
    local mode="${2:-Default}"
    
    print_header "Creating new chat session..."
    local data=$(jq -n \
        --arg desc "$description" \
        --arg mode "$mode" \
        '{"description": $desc, "mode": $mode}')
    
    local response=$(api_call "POST" "/v1/chats" "$data")
    
    if [ $? -eq 0 ]; then
        local chat_id=$(echo "$response" | jq -r '.chat_id')
        print_status "Chat created with ID: $chat_id"
        echo "$response" | jq -r '.message'
    else
        print_error "Failed to create chat"
    fi
}

# Function to set active chat
set_active_chat() {
    local chat_id="$1"
    
    if [ -z "$chat_id" ]; then
        print_error "Chat ID is required"
        return 1
    fi
    
    print_header "Setting active chat to: $chat_id"
    local data=$(jq -n --arg chat_id "$chat_id" '{"chat_id": $chat_id}')
    local response=$(api_call "POST" "/v1/chats/active" "$data")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.message'
    else
        print_error "Failed to set active chat"
    fi
}

# Function to get active chat
get_active_chat() {
    print_header "Getting active chat..."
    local response=$(api_call "GET" "/v1/chats/active")
    
    if [ $? -eq 0 ]; then
        local active_chat=$(echo "$response" | jq -r '.active_chat_id // "None"')
        print_status "Active chat: $active_chat"
    else
        print_error "Failed to get active chat"
    fi
}

# Function to send a message
send_message() {
    local message="$1"
    
    if [ -z "$message" ]; then
        print_error "Message is required"
        return 1
    fi
    
    print_header "Sending message..."
    local data=$(jq -n \
        --arg msg "$message" \
        '{"messages": [{"role": "user", "content": $msg}]}')
    
    local response=$(api_call "POST" "/v1/chats/completions" "$data")
    
    if [ $? -eq 0 ]; then
        local assistant_message=$(echo "$response" | jq -r '.choices[0].message.content // "No response"')
        print_status "Assistant response:"
        echo "$assistant_message"
    else
        print_error "Failed to send message"
    fi
}

# Function to update chat mode
update_chat_mode() {
    local chat_id="$1"
    local mode="$2"
    
    if [ -z "$chat_id" ] || [ -z "$mode" ]; then
        print_error "Chat ID and mode are required"
        return 1
    fi
    
    print_header "Updating chat $chat_id mode to: $mode"
    local data=$(jq -n --arg mode "$mode" '{"mode": $mode}')
    local response=$(api_call "PUT" "/v1/chats/$chat_id/mode" "$data")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.message'
    else
        print_error "Failed to update chat mode"
    fi
}

# Function to delete a chat
delete_chat() {
    local chat_id="$1"
    
    if [ -z "$chat_id" ]; then
        print_error "Chat ID is required"
        return 1
    fi
    
    print_header "Deleting chat: $chat_id"
    local response=$(api_call "DELETE" "/v1/chats/$chat_id")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.message'
    else
        print_error "Failed to delete chat"
    fi
}

# Function to get chat messages
get_messages() {
    local chat_id="$1"
    local limit="${2:-100}"
    
    if [ -z "$chat_id" ]; then
        print_error "Chat ID is required"
        return 1
    fi
    
    print_header "Getting messages for chat: $chat_id"
    local response=$(api_call "GET" "/v1/messages/$chat_id?limit=$limit")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.messages[] | "\(.timestamp): \(.role) - \(.content)"'
    else
        print_error "Failed to get messages"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Gemini Web Wrapper CLI Client

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  mode                    Show current client mode (free/paid)
  mode-switch <mode>      Switch between free and paid modes
  list                    List all chat sessions
  create [desc] [mode]    Create a new chat session
  active [chat_id]        Set active chat session (or show current)
  send <message>          Send a message to active chat
  update-mode <id> <mode> Update chat mode
  delete <chat_id>        Delete a chat session
  messages <chat_id>      Get chat messages
  help                    Show this help message

Modes:
  free                    Free mode (uses browser cookies, unlimited)
  paid                    Paid mode (uses API key, pay per request)
  Default                 Default chat mode
  Code                    Programming expert mode
  Architect               Software architecture mode
  Debug                   Debugging expert mode
  Ask                     General assistant mode

Examples:
  $0 mode-switch free     # Switch to free mode
  $0 create "My chat" Code # Create chat in Code mode
  $0 active abc123        # Set active chat
  $0 send "Hello world"   # Send message
  $0 messages abc123      # Get chat history

Environment Variables:
  API_BASE_URL           API base URL (default: http://localhost:8000)

EOF
}

# Main script logic
case "${1:-help}" in
    "mode")
        print_header "Current client mode:"
        get_current_mode
        ;;
    "mode-switch")
        if [ -z "$2" ]; then
            print_error "Mode is required (free or paid)"
            exit 1
        fi
        switch_mode "$2"
        ;;
    "list")
        list_chats
        ;;
    "create")
        create_chat "${2:-}" "${3:-Default}"
        ;;
    "active")
        if [ -z "$2" ]; then
            get_active_chat
        else
            set_active_chat "$2"
        fi
        ;;
    "send")
        if [ -z "$2" ]; then
            print_error "Message is required"
            exit 1
        fi
        send_message "$2"
        ;;
    "update-mode")
        if [ -z "$2" ] || [ -z "$3" ]; then
            print_error "Chat ID and mode are required"
            exit 1
        fi
        update_chat_mode "$2" "$3"
        ;;
    "delete")
        if [ -z "$2" ]; then
            print_error "Chat ID is required"
            exit 1
        fi
        delete_chat "$2"
        ;;
    "messages")
        if [ -z "$2" ]; then
            print_error "Chat ID is required"
            exit 1
        fi
        get_messages "$2" "$3"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac