#!/bin/bash
# Initialize project - run once after clone/download

set -e

echo "================================"
echo "Mine Gambling Game - Setup"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env created. Review it before running docker-compose up"
else
    echo "✓ .env already exists"
fi

# Create required directories
mkdir -p logs
echo "✓ Created logs directory"

# Make scripts executable
chmod +x run.sh 2>/dev/null || true
chmod +x kubernetes/deploy.sh 2>/dev/null || true
chmod +x kubernetes/undeploy.sh 2>/dev/null || true
echo "✓ Made scripts executable"

# Check for Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✓ Docker found: $DOCKER_VERSION"
    
    if command -v docker-compose &> /dev/null; then
        DC_VERSION=$(docker-compose --version)
        echo "✓ Docker Compose found: $DC_VERSION"
    else
        echo "⚠ Docker Compose not found. Install it for full setup."
    fi
else
    echo "⚠ Docker not found. Install it to use docker-compose setup."
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review .env file"
echo "2. Run: docker-compose up -d"
echo "3. Visit: http://localhost:8000"
echo ""
echo "For more info, see QUICKSTART.md"
