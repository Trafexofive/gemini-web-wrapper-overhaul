#!/bin/bash

# Gemini Web Wrapper API Client
# A comprehensive bash client for interacting with the Gemini API

set -e

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TOKEN_FILE="${TOKEN_FILE:-$HOME/.gemini_token}"
API_KEY_FILE="${API_KEY_FILE:-$HOME/.gemini_api_key}"
DEFAULT_USER_AGENT="Gemini-API-Client/1.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if jq is installed
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed. Please install jq first."
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed. Please install curl first."
        exit 1
    fi
}

# Load token from file
load_token() {
    if [[ -f "$TOKEN_FILE" ]]; then
        TOKEN=$(cat "$TOKEN_FILE")
        if [[ -n "$TOKEN" ]]; then
            return 0
        fi
    fi
    return 1
}

# Load API key from file
load_api_key() {
    if [[ -f "$API_KEY_FILE" ]]; then
        API_KEY=$(cat "$API_KEY_FILE")
        if [[ -n "$API_KEY" ]]; then
            return 0
        fi
    fi
    return 1
}

# Save token to file
save_token() {
    echo "$1" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
}

# Save API key to file
save_api_key() {
    echo "$1" > "$API_KEY_FILE"
    chmod 600 "$API_KEY_FILE"
}

# Make API request
api_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    local url="$API_BASE_URL$endpoint"
    local headers=(
        "Content-Type: application/json"
        "User-Agent: $DEFAULT_USER_AGENT"
    )
    
    # Add authorization header if token or API key exists
    if [[ -n "$TOKEN" ]]; then
        headers+=("Authorization: Bearer $TOKEN")
    elif [[ -n "$API_KEY" ]]; then
        headers+=("X-API-Key: $API_KEY")
    fi
    
    # Build curl command
    local curl_cmd="curl -s -X $method \"$url\""
    
    # Add headers
    for header in "${headers[@]}"; do
        curl_cmd="$curl_cmd -H \"$header\""
    done
    
    # Add data if provided
    if [[ -n "$data" ]]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    # Execute and return result
    eval "$curl_cmd"
}

# Set API key
set_api_key() {
    local api_key="$1"
    
    if [[ -z "$api_key" ]]; then
        log_error "Usage: set_api_key <api_key>"
        return 1
    fi
    
    save_api_key "$api_key"
    API_KEY="$api_key"
    log_success "API key saved successfully"
}

# Clear API key
clear_api_key() {
    rm -f "$API_KEY_FILE"
    API_KEY=""
    log_success "API key cleared successfully"
}

# Authentication functions (for local development)
login() {
    local email="$1"
    local password="$2"
    
    if [[ -z "$email" || -z "$password" ]]; then
        log_error "Usage: login <email> <password>"
        return 1
    fi
    
    local data="{\"email\":\"$email\",\"password\":\"$password\"}"
    local response=$(api_request "POST" "/v1/auth/login" "$data")
    
    if echo "$response" | jq -e '.access_token' > /dev/null 2>&1; then
        local token=$(echo "$response" | jq -r '.access_token')
        local username=$(echo "$response" | jq -r '.user.username')
        save_token "$token"
        TOKEN="$token"
        log_success "Logged in as $username"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Login failed: $error"
        return 1
    fi
}

register() {
    local email="$1"
    local password="$2"
    local username="$3"
    
    if [[ -z "$email" || -z "$password" || -z "$username" ]]; then
        log_error "Usage: register <email> <password> <username>"
        return 1
    fi
    
    local data="{\"email\":\"$email\",\"password\":\"$password\",\"username\":\"$username\"}"
    local response=$(api_request "POST" "/v1/auth/register" "$data")
    
    if echo "$response" | jq -e '.access_token' > /dev/null 2>&1; then
        local token=$(echo "$response" | jq -r '.access_token')
        local username=$(echo "$response" | jq -r '.user.username')
        save_token "$token"
        TOKEN="$token"
        log_success "Registered and logged in as $username"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Registration failed: $error"
        return 1
    fi
}

logout() {
    rm -f "$TOKEN_FILE"
    TOKEN=""
    log_success "Logged out successfully"
}

# Chat functions
list_chats() {
    local response=$(api_request "GET" "/v1/chats/")
    
    if echo "$response" | jq -e '.[]' > /dev/null 2>&1; then
        echo "$response" | jq -r '.[] | "\(.chat_id) | \(.description // "Untitled") | \(.mode // "Default")"'
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to list chats: $error"
        return 1
    fi
}

create_chat() {
    local description="$1"
    local mode="${2:-Default}"
    
    if [[ -z "$description" ]]; then
        log_error "Usage: create_chat <description> [mode]"
        return 1
    fi
    
    local data="{\"description\":\"$description\",\"mode\":\"$mode\"}"
    local response=$(api_request "POST" "/v1/chats/" "$data")
    
    if echo "$response" | jq -e '.chat_id' > /dev/null 2>&1; then
        local chat_id=$(echo "$response" | jq -r '.chat_id')
        log_success "Created chat: $chat_id"
        echo "$chat_id"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to create chat: $error"
        return 1
    fi
}

delete_chat() {
    local chat_id="$1"
    
    if [[ -z "$chat_id" ]]; then
        log_error "Usage: delete_chat <chat_id>"
        return 1
    fi
    
    local response=$(api_request "DELETE" "/v1/chats/$chat_id")
    
    if echo "$response" | jq -e '.message' > /dev/null 2>&1; then
        log_success "Deleted chat: $chat_id"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to delete chat: $error"
        return 1
    fi
}

set_active_chat() {
    local chat_id="$1"
    
    if [[ -z "$chat_id" ]]; then
        log_error "Usage: set_active_chat <chat_id>"
        return 1
    fi
    
    local data="{\"chat_id\":\"$chat_id\"}"
    local response=$(api_request "POST" "/v1/chats/active" "$data")
    
    if [[ $? -eq 0 ]]; then
        log_success "Set active chat: $chat_id"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to set active chat: $error"
        return 1
    fi
}

get_active_chat() {
    local response=$(api_request "GET" "/v1/chats/active")
    
    if echo "$response" | jq -e '.active_chat_id' > /dev/null 2>&1; then
        local active_chat_id=$(echo "$response" | jq -r '.active_chat_id')
        if [[ "$active_chat_id" != "null" ]]; then
            echo "$active_chat_id"
            return 0
        else
            log_info "No active chat"
            return 1
        fi
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to get active chat: $error"
        return 1
    fi
}

send_message() {
    local message="$1"
    local chat_id="$2"
    
    if [[ -z "$message" ]]; then
        log_error "Usage: send_message <message> [chat_id]"
        return 1
    fi
    
    # If no chat_id provided, try to get active chat
    if [[ -z "$chat_id" ]]; then
        chat_id=$(get_active_chat)
        if [[ $? -ne 0 ]]; then
            log_error "No active chat and no chat_id provided"
            return 1
        fi
    fi
    
    local data="{\"messages\":[{\"role\":\"user\",\"content\":\"$message\"}]}"
    local response=$(api_request "POST" "/v1/chats/completions" "$data")
    
    if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
        local ai_response=$(echo "$response" | jq -r '.choices[0].message.content')
        echo "$ai_response"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to send message: $error"
        return 1
    fi
}

# API Key functions
list_api_keys() {
    local response=$(api_request "GET" "/v1/auth/api-keys")
    
    if echo "$response" | jq -e '.keys' > /dev/null 2>&1; then
        echo "$response" | jq -r '.keys[] | "\(.id) | \(.name) | \(.created_at)"'
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to list API keys: $error"
        return 1
    fi
}

create_api_key() {
    local name="$1"
    
    if [[ -z "$name" ]]; then
        log_error "Usage: create_api_key <name>"
        return 1
    fi
    
    local data="{\"name\":\"$name\"}"
    local response=$(api_request "POST" "/v1/auth/api-keys" "$data")
    
    if echo "$response" | jq -e '.key' > /dev/null 2>&1; then
        local key=$(echo "$response" | jq -r '.key')
        local id=$(echo "$response" | jq -r '.id')
        log_success "Created API key: $id"
        echo "API Key: $key"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to create API key: $error"
        return 1
    fi
}

delete_api_key() {
    local key_id="$1"
    
    if [[ -z "$key_id" ]]; then
        log_error "Usage: delete_api_key <key_id>"
        return 1
    fi
    
    local response=$(api_request "DELETE" "/v1/auth/api-keys/$key_id")
    
    if echo "$response" | jq -e '.message' > /dev/null 2>&1; then
        log_success "Deleted API key: $key_id"
        return 0
    else
        local error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        log_error "Failed to delete API key: $error"
        return 1
    fi
}

# Health check
health_check() {
    local response=$(api_request "GET" "/health")
    
    if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
        local status=$(echo "$response" | jq -r '.status')
        local version=$(echo "$response" | jq -r '.version')
        log_success "API Status: $status (v$version)"
        return 0
    else
        log_error "Health check failed"
        return 1
    fi
}

# Show help
show_help() {
    cat << EOF
Gemini Web Wrapper API Client

Usage: $0 <command> [options]

API Key Management (Primary for external users):
  set_api_key <api_key>              Set API key for authentication
  clear_api_key                      Clear stored API key
  list_api_keys                      List all API keys (requires JWT)
  create_api_key <name>              Create new API key (requires JWT)
  delete_api_key <key_id>            Delete API key (requires JWT)

Authentication (Local development):
  login <email> <password>           Login with email and password
  register <email> <password> <user> Register new account
  logout                             Logout and clear token

Chat Management:
  list_chats                         List all chats
  create_chat <description> [mode]   Create new chat
  delete_chat <chat_id>              Delete chat
  set_active_chat <chat_id>          Set active chat
  get_active_chat                    Get active chat ID
  send_message <message> [chat_id]   Send message to chat

System:
  health_check                       Check API health
  help                               Show this help

Environment Variables:
  API_BASE_URL                       API base URL (default: http://localhost:8000)
  TOKEN_FILE                         Token file path (default: ~/.gemini_token)
  API_KEY_FILE                       API key file path (default: ~/.gemini_api_key)

Examples for External Users:
  # Set your API key (get this from the frontend)
  $0 set_api_key "your-api-key-here"
  
  # Check if API is accessible
  $0 health_check
  
  # Create a chat and send a message
  CHAT_ID=\$($0 create_chat "My first chat")
  $0 send_message "Hello, how are you?" "\$CHAT_ID"
  
  # List all your chats
  $0 list_chats

Examples for Local Development:
  # Register and login
  $0 register test@example.com password123 myuser
  $0 login test@example.com password123
  
  # Create an API key for external use
  $0 create_api_key "external-script"
  
  # Use the generated API key in another script
  $0 set_api_key "generated-api-key-here"
EOF
}

# Main function
main() {
    check_dependencies
    load_token || true  # Don't exit if no token
    load_api_key || true  # Don't exit if no API key
    
    local command="$1"
    
    case "$command" in
        "set_api_key")
            set_api_key "$2"
            ;;
        "clear_api_key")
            clear_api_key
            ;;
        "login")
            login "$2" "$3"
            ;;
        "register")
            register "$2" "$3" "$4"
            ;;
        "logout")
            logout
            ;;
        "list_chats")
            list_chats
            ;;
        "create_chat")
            create_chat "$2" "$3"
            ;;
        "delete_chat")
            delete_chat "$2"
            ;;
        "set_active_chat")
            set_active_chat "$2"
            ;;
        "get_active_chat")
            get_active_chat
            ;;
        "send_message")
            send_message "$2" "$3"
            ;;
        "list_api_keys")
            list_api_keys
            ;;
        "create_api_key")
            create_api_key "$2"
            ;;
        "delete_api_key")
            delete_api_key "$2"
            ;;
        "health_check")
            health_check
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"