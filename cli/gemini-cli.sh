#!/bin/bash

# Gemini Web Wrapper CLI Client
# A command-line interface for the Gemini Web Wrapper API

set -e

# Configuration
DEFAULT_API_BASE="http://localhost:8000"
API_BASE="${GEMINI_API_URL:-$DEFAULT_API_BASE}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
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

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

# Check if required commands are available
check_dependencies() {
    local missing_deps=()
    
    for cmd in curl jq; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install: ${missing_deps[*]}"
        exit 1
    fi
}

# API request function
api_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local url="${API_BASE}${endpoint}"
    
    log_debug "Making $method request to: $url"
    
    local curl_opts=(
        -s
        -w "\n%{http_code}"
        -H "Content-Type: application/json"
        -H "Accept: application/json"
    )
    
    if [[ -n "$data" ]]; then
        curl_opts+=(-d "$data")
    fi
    
    local response
    response=$(curl "${curl_opts[@]}" -X "$method" "$url")
    
    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | head -n -1)
    
    log_debug "Response code: $http_code"
    log_debug "Response body: $body"
    
    if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
        echo "$body"
    else
        log_error "API request failed with status $http_code"
        if [[ -n "$body" ]]; then
            echo "$body" | jq -r '.detail // .message // .' 2>/dev/null || echo "$body"
        fi
        return 1
    fi
}

# Health check
check_health() {
    log_info "Checking API health..."
    if api_request "GET" "/health" >/dev/null 2>&1; then
        log_success "API is healthy"
        return 0
    else
        log_error "API is not responding"
        return 1
    fi
}

# List all chats
list_chats() {
    log_info "Fetching chat sessions..."
    local response
    response=$(api_request "GET" "/v1/chats")
    
    if [[ -n "$response" ]]; then
        echo "$response" | jq -r '.[] | "\(.chat_id[:8])... | \(.description // "No description") | \(.mode // "Default")"' 2>/dev/null || {
            log_warning "Could not parse JSON response, showing raw output:"
            echo "$response"
        }
    else
        log_info "No chat sessions found"
    fi
}

# Get active chat
get_active_chat() {
    log_info "Fetching active chat..."
    local response
    response=$(api_request "GET" "/v1/chats/active")
    
    if [[ -n "$response" ]]; then
        local active_chat_id
        active_chat_id=$(echo "$response" | jq -r '.active_chat_id // empty')
        
        if [[ -n "$active_chat_id" ]]; then
            log_success "Active chat: ${active_chat_id:0:8}..."
        else
            log_info "No active chat set"
        fi
    fi
}

# Create new chat
create_chat() {
    local description="$1"
    local mode="${2:-Default}"
    
    log_info "Creating new chat session..."
    log_debug "Description: $description"
    log_debug "Mode: $mode"
    
    local payload
    payload=$(jq -n \
        --arg desc "$description" \
        --arg mode "$mode" \
        '{
            description: $desc,
            mode: $mode
        }')
    
    local response
    response=$(api_request "POST" "/v1/chats" "$payload")
    
    if [[ -n "$response" ]]; then
        local chat_id
        chat_id=$(echo "$response" | jq -r '. // empty')
        
        if [[ -n "$chat_id" ]]; then
            log_success "Created chat session: ${chat_id:0:8}..."
            echo "$chat_id"
        else
            log_error "Failed to create chat session"
            return 1
        fi
    fi
}

# Set active chat
set_active_chat() {
    local chat_id="$1"
    
    if [[ -z "$chat_id" ]]; then
        log_error "Chat ID is required"
        return 1
    fi
    
    log_info "Setting active chat: ${chat_id:0:8}..."
    
    local payload
    payload=$(jq -n \
        --arg chat_id "$chat_id" \
        '{
            chat_id: $chat_id
        }')
    
    if api_request "POST" "/v1/chats/active" "$payload" >/dev/null; then
        log_success "Active chat set to: ${chat_id:0:8}..."
    else
        log_error "Failed to set active chat"
        return 1
    fi
}

# Delete chat
delete_chat() {
    local chat_id="$1"
    
    if [[ -z "$chat_id" ]]; then
        log_error "Chat ID is required"
        return 1
    fi
    
    log_warning "Deleting chat session: ${chat_id:0:8}..."
    
    if api_request "DELETE" "/v1/chats/$chat_id" >/dev/null; then
        log_success "Chat session deleted: ${chat_id:0:8}..."
    else
        log_error "Failed to delete chat session"
        return 1
    fi
}

# Send message
send_message() {
    local message="$1"
    local chat_id="$2"
    
    if [[ -z "$message" ]]; then
        log_error "Message is required"
        return 1
    fi
    
    log_info "Sending message..."
    log_debug "Message: $message"
    log_debug "Chat ID: $chat_id"
    
    local payload
    if [[ -n "$chat_id" ]]; then
        payload=$(jq -n \
            --arg msg "$message" \
            --arg cid "$chat_id" \
            '{
                message: $msg,
                chat_id: $cid
            }')
    else
        payload=$(jq -n \
            --arg msg "$message" \
            '{
                message: $msg
            }')
    fi
    
    local response
    response=$(api_request "POST" "/v1/chats/completions" "$payload")
    
    if [[ -n "$response" ]]; then
        local content
        content=$(echo "$response" | jq -r '.content // empty')
        
        if [[ -n "$content" ]]; then
            echo -e "${CYAN}Gemini:${NC}"
            echo "$content"
        else
            log_warning "Could not parse response, showing raw output:"
            echo "$response"
        fi
    fi
}

# Interactive chat mode
interactive_chat() {
    local chat_id="$1"
    
    log_info "Starting interactive chat mode..."
    log_info "Type 'quit' or 'exit' to end the session"
    log_info "Type 'help' for available commands"
    echo
    
    while true; do
        echo -n -e "${GREEN}You:${NC} "
        read -r message
        
        case "$message" in
            quit|exit)
                log_info "Ending chat session"
                break
                ;;
            help)
                echo "Available commands:"
                echo "  quit, exit - End the session"
                echo "  help - Show this help"
                echo "  clear - Clear the screen"
                echo "  status - Show current chat status"
                continue
                ;;
            clear)
                clear
                continue
                ;;
            status)
                if [[ -n "$chat_id" ]]; then
                    echo "Current chat: ${chat_id:0:8}..."
                else
                    echo "Using default chat"
                fi
                continue
                ;;
            "")
                continue
                ;;
        esac
        
        send_message "$message" "$chat_id"
        echo
    done
}

# Show help
show_help() {
    cat << EOF
Gemini Web Wrapper CLI Client v${VERSION}

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  health                    Check API health
  chats                     List all chat sessions
  active                    Show active chat session
  create [DESC] [MODE]      Create new chat session
  set-active <CHAT_ID>      Set active chat session
  delete <CHAT_ID>          Delete chat session
  send <MESSAGE> [CHAT_ID]  Send message to chat
  chat [CHAT_ID]            Start interactive chat mode

Options:
  -h, --help                Show this help message
  -v, --version             Show version
  -d, --debug               Enable debug output
  --api-url <URL>           Set API base URL (default: ${DEFAULT_API_BASE})

Environment Variables:
  GEMINI_API_URL            API base URL
  DEBUG                     Enable debug output (true/false)

Examples:
  $0 health
  $0 chats
  $0 create "My new chat" "Creative"
  $0 send "Hello, how are you?"
  $0 chat abc123def
  $0 --api-url http://localhost:8000 chats

EOF
}

# Show version
show_version() {
    echo "Gemini Web Wrapper CLI Client v${VERSION}"
}

# Main function
main() {
    # Check dependencies
    check_dependencies
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            --api-url)
                API_BASE="$2"
                shift 2
                ;;
            health)
                check_health
                exit $?
                ;;
            chats)
                list_chats
                exit 0
                ;;
            active)
                get_active_chat
                exit 0
                ;;
            create)
                shift
                create_chat "$1" "$2"
                exit $?
                ;;
            set-active)
                shift
                set_active_chat "$1"
                exit $?
                ;;
            delete)
                shift
                delete_chat "$1"
                exit $?
                ;;
            send)
                shift
                send_message "$1" "$2"
                exit $?
                ;;
            chat)
                shift
                interactive_chat "$1"
                exit 0
                ;;
            *)
                log_error "Unknown command: $1"
                echo
                show_help
                exit 1
                ;;
        esac
    done
    
    # If no command provided, show help
    show_help
    exit 1
}

# Run main function with all arguments
main "$@"