#!/bin/bash

echo "======================================"
echo "AI Calendar Agent - Setup Script"
echo "======================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created!"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your API keys:"
echo "   cp .env.example .env"
echo ""
echo "2. Get Google Calendar credentials:"
echo "   - Go to https://console.cloud.google.com/apis/credentials"
echo "   - Create OAuth 2.0 credentials"
echo "   - Download as credentials.json in this directory"
echo ""
echo "3. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "4. Run the application:"
echo "   python main.py"
echo ""
echo "For a quick demo:"
echo "   python main.py --demo"
echo ""
