#!/bin/bash
# Local development startup script

set -e

echo "Mine Gambling Game - Development Setup"
echo "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python $(python3 --version) found"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "✓ Dependencies installed"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "⚠ Docker is not installed. Install it to use docker-compose."
    echo "  Running with local development database instead."
    export DATABASE_URL="sqlite:///./test.db"
else
    echo "✓ Docker found"
    
    # Check docker-compose
    if ! docker compose version &> /dev/null; then
        echo "⚠ Docker Compose is not installed."
        echo "  Install it for full development setup."
    else
        echo "✓ Docker Compose found"
        echo "Starting Docker Compose services..."
        docker compose up -d
        echo "✓ Services started (db on localhost:5432)"
        sleep 5
    fi
fi

echo ""
echo "Starting application..."
echo "Access at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo ""

# Run the application
python main.py
