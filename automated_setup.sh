#!/bin/bash

# Automated Setup Script for Life Optimization AI
# Handles entire installation and configuration with error logging

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="setup_log_$(date +%Y%m%d_%H%M%S).txt"
ERROR_LOG="setup_errors_$(date +%Y%m%d_%H%M%S).txt"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error_log() {
    echo -e "${RED}[ERROR $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$ERROR_LOG"
}

warn_log() {
    echo -e "${YELLOW}[WARN $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to handle errors
handle_error() {
    error_log "Setup failed at: $1"
    error_log "Check $ERROR_LOG for details"
    exit 1
}

# Trap errors
trap 'handle_error "$BASH_COMMAND"' ERR

echo "================================================"
echo "  Life Optimization AI - Automated Setup"
echo "================================================"
echo ""

# Step 1: Check Python version
log "Step 1: Checking Python version..."
if ! command_exists python3; then
    error_log "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log "Found Python $PYTHON_VERSION"

# Step 2: Check if virtual environment exists
log "Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv || handle_error "Failed to create venv"
else
    log "Virtual environment already exists"
fi

# Step 3: Activate virtual environment and install dependencies
log "Step 3: Installing Python dependencies..."
source venv/bin/activate

# Upgrade pip first
log "Upgrading pip..."
pip install --upgrade pip >> "$LOG_FILE" 2>&1 || handle_error "Failed to upgrade pip"

# Install dependencies
log "Installing requirements..."
if pip install -r requirements.txt >> "$LOG_FILE" 2>&1; then
    log "✓ All dependencies installed successfully"
else
    error_log "Failed to install some dependencies. Check $LOG_FILE"
    # Continue anyway - might be partial success
fi

# Step 4: Add garminconnect to requirements
log "Step 4: Installing additional dependencies for health tracking..."
if pip install garminconnect stravalib >> "$LOG_FILE" 2>&1; then
    log "✓ Health tracking libraries installed"
else
    warn_log "Failed to install garminconnect or stravalib. Will log for manual fix."
    echo "garminconnect - FAILED" >> "$ERROR_LOG"
    echo "stravalib - FAILED" >> "$ERROR_LOG"
fi

# Step 5: Check for .env file
log "Step 5: Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log "Creating .env from template..."
        cp .env.example .env
        warn_log "⚠ Please edit .env file with your API keys"
        echo "TODO: Edit .env with API keys" >> "$ERROR_LOG"
    else
        error_log ".env.example not found!"
    fi
else
    log "✓ .env file exists"
fi

# Step 6: Check for Google Calendar credentials
log "Step 6: Checking Google Calendar credentials..."
if [ ! -f "credentials.json" ]; then
    warn_log "⚠ credentials.json not found"
    warn_log "Please download from Google Cloud Console:"
    warn_log "https://developers.google.com/calendar/api/quickstart/python"
    echo "TODO: Download credentials.json from Google Cloud Console" >> "$ERROR_LOG"
else
    log "✓ Google Calendar credentials found"
fi

# Step 7: Create necessary directories
log "Step 7: Creating data directories..."
mkdir -p data
mkdir -p logs
mkdir -p chroma_db
log "✓ Directories created"

# Step 8: Test imports
log "Step 8: Testing Python imports..."
python3 << EOF >> "$LOG_FILE" 2>&1
try:
    import anthropic
    print("✓ anthropic")
except ImportError as e:
    print(f"✗ anthropic: {e}")

try:
    import openai
    print("✓ openai")
except ImportError as e:
    print(f"✗ openai: {e}")

try:
    import chromadb
    print("✓ chromadb")
except ImportError as e:
    print(f"✗ chromadb: {e}")

try:
    from google.oauth2.credentials import Credentials
    print("✓ google-auth")
except ImportError as e:
    print(f"✗ google-auth: {e}")

try:
    import pydantic
    print("✓ pydantic")
except ImportError as e:
    print(f"✗ pydantic: {e}")
EOF

if [ $? -eq 0 ]; then
    log "✓ All critical imports successful"
else
    warn_log "Some imports failed. Check $LOG_FILE for details"
fi

# Step 9: Check database (PostgreSQL optional, SQLite as fallback)
log "Step 9: Checking database options..."
if command_exists psql; then
    log "✓ PostgreSQL found"
else
    warn_log "PostgreSQL not installed (optional)"
    warn_log "Will use SQLite as fallback"
    echo "INFO: Using SQLite instead of PostgreSQL" >> "$LOG_FILE"
fi

# Step 10: Summary
echo ""
echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo ""

# Check for errors
if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
    echo -e "${YELLOW}⚠ Setup completed with warnings/errors${NC}"
    echo -e "${YELLOW}Check $ERROR_LOG for details${NC}"
    echo ""
    echo "Issues to resolve:"
    cat "$ERROR_LOG"
else
    echo -e "${GREEN}✓ Setup completed successfully!${NC}"
    rm -f "$ERROR_LOG"  # Remove empty error log
fi

echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Download credentials.json from Google Cloud Console"
echo "3. Run: python main.py"
echo ""
echo "Logs saved to: $LOG_FILE"
