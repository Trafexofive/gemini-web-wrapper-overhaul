#!/bin/bash

# Gemini Web Wrapper CLI Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_SCRIPT="$SCRIPT_DIR/gemini-cli.sh"

echo "🚀 Gemini Web Wrapper CLI Installation"
echo "======================================"
echo

# Check if we're in the right directory
if [[ ! -f "$CLI_SCRIPT" ]]; then
    log_error "CLI script not found at: $CLI_SCRIPT"
    log_info "Please run this script from the cli/ directory"
    exit 1
fi

# Check dependencies
log_info "Checking dependencies..."

missing_deps=()

# Check for curl
if ! command -v curl &> /dev/null; then
    missing_deps+=("curl")
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    missing_deps+=("jq")
fi

# Check for bash version
bash_version=$(bash --version | head -n1 | grep -oE '[0-9]+\.[0-9]+' | head -n1)
required_version="4.0"

if [[ "$(printf '%s\n' "$required_version" "$bash_version" | sort -V | head -n1)" != "$required_version" ]]; then
    log_warning "Bash version $bash_version detected, version 4.0+ recommended"
fi

# Install missing dependencies
if [[ ${#missing_deps[@]} -gt 0 ]]; then
    log_warning "Missing dependencies: ${missing_deps[*]}"
    echo
    
    # Detect OS and provide installation commands
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                log_info "Installing dependencies on Ubuntu/Debian..."
                sudo apt update
                sudo apt install -y "${missing_deps[@]}"
                ;;
            centos|rhel|fedora)
                log_info "Installing dependencies on CentOS/RHEL/Fedora..."
                if command -v dnf &> /dev/null; then
                    sudo dnf install -y "${missing_deps[@]}"
                else
                    sudo yum install -y "${missing_deps[@]}"
                fi
                ;;
            *)
                log_error "Unsupported OS: $ID"
                log_info "Please install the following packages manually:"
                for dep in "${missing_deps[@]}"; do
                    echo "  - $dep"
                done
                exit 1
                ;;
        esac
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "Installing dependencies on macOS..."
        if command -v brew &> /dev/null; then
            brew install "${missing_deps[@]}"
        else
            log_error "Homebrew not found. Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    else
        log_error "Unsupported OS. Please install the following packages manually:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
    
    # Verify installation
    for dep in "${missing_deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Failed to install $dep"
            exit 1
        fi
    done
    
    log_success "Dependencies installed successfully"
else
    log_success "All dependencies are already installed"
fi

echo

# Make CLI script executable
log_info "Setting up CLI script..."
chmod +x "$CLI_SCRIPT"
log_success "CLI script is now executable"

# Test the CLI
log_info "Testing CLI installation..."
if "$CLI_SCRIPT" --version &> /dev/null; then
    log_success "CLI installation test passed"
else
    log_error "CLI installation test failed"
    exit 1
fi

echo

# Installation options
log_info "Installation options:"
echo "1. Add to PATH (recommended)"
echo "2. Create symlink in /usr/local/bin"
echo "3. Skip (use with full path)"

read -p "Choose an option (1-3): " choice

case $choice in
    1)
        log_info "Adding to PATH..."
        shell_rc=""
        if [[ -f "$HOME/.bashrc" ]]; then
            shell_rc="$HOME/.bashrc"
        elif [[ -f "$HOME/.zshrc" ]]; then
            shell_rc="$HOME/.zshrc"
        elif [[ -f "$HOME/.profile" ]]; then
            shell_rc="$HOME/.profile"
        fi
        
        if [[ -n "$shell_rc" ]]; then
            if ! grep -q "$SCRIPT_DIR" "$shell_rc"; then
                echo "" >> "$shell_rc"
                echo "# Gemini Web Wrapper CLI" >> "$shell_rc"
                echo "export PATH=\"\$PATH:$SCRIPT_DIR\"" >> "$shell_rc"
                log_success "Added to $shell_rc"
                log_info "Please restart your terminal or run: source $shell_rc"
            else
                log_warning "PATH already configured in $shell_rc"
            fi
        else
            log_error "Could not find shell configuration file"
            log_info "Please manually add the following to your shell config:"
            echo "export PATH=\"\$PATH:$SCRIPT_DIR\""
        fi
        ;;
    2)
        log_info "Creating symlink..."
        if sudo ln -sf "$CLI_SCRIPT" /usr/local/bin/gemini-cli; then
            log_success "Symlink created: /usr/local/bin/gemini-cli"
            log_info "You can now use: gemini-cli --help"
        else
            log_error "Failed to create symlink"
        fi
        ;;
    3)
        log_info "Skipping PATH setup"
        ;;
    *)
        log_error "Invalid option"
        exit 1
        ;;
esac

echo
log_success "Installation completed successfully!"
echo
echo "Usage examples:"
echo "  $CLI_SCRIPT --help"
echo "  $CLI_SCRIPT health"
echo "  $CLI_SCRIPT chats"
echo "  $CLI_SCRIPT chat"
echo
echo "For more information, see: $SCRIPT_DIR/README.md"