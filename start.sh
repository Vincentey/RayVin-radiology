#!/bin/bash
# Radiology AI Assistant - Production Startup Script

set -e

echo "=============================================="
echo "  Radiology AI Assistant - Startup"
echo "=============================================="

# Check for .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy config.example.env to .env and configure your settings:"
    echo "  cp config.example.env .env"
    echo "  nano .env"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Validate required variables
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    echo "ERROR: OPENAI_API_KEY not configured in .env"
    exit 1
fi

if [ -z "$PINECONE_API_KEY" ] || [ "$PINECONE_API_KEY" = "your-pinecone-api-key-here" ]; then
    echo "ERROR: PINECONE_API_KEY not configured in .env"
    exit 1
fi

if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "CHANGE_THIS_TO_A_STRONG_RANDOM_KEY" ]; then
    echo "ERROR: JWT_SECRET_KEY not configured in .env"
    echo "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    exit 1
fi

echo "✓ Environment variables validated"

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Docker detected. Starting with Docker Compose..."
    docker-compose up --build -d
    echo ""
    echo "✓ Services started!"
    echo "  Frontend: http://localhost:${FRONTEND_PORT:-80}"
    echo "  API:      http://localhost:${API_PORT:-8000}"
    echo "  API Docs: http://localhost:${API_PORT:-8000}/docs"
    echo ""
    echo "View logs: docker-compose logs -f"
    echo "Stop:      docker-compose down"
else
    echo "Docker not available. Starting locally..."
    
    # Check for Python virtual environment
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
    
    # Create uploads directory
    mkdir -p uploads
    
    # Start API server in background
    echo "Starting API server..."
    uvicorn radio_assistance.mainapp.process_dicom_endpoint:app --host 0.0.0.0 --port ${API_PORT:-8000} &
    API_PID=$!
    
    # Start frontend server
    echo "Starting frontend server..."
    cd frontend && python -m http.server ${FRONTEND_PORT:-3000} &
    FRONTEND_PID=$!
    
    echo ""
    echo "✓ Services started!"
    echo "  Frontend: http://localhost:${FRONTEND_PORT:-3000}"
    echo "  API:      http://localhost:${API_PORT:-8000}"
    echo "  API Docs: http://localhost:${API_PORT:-8000}/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Trap to cleanup on exit
    trap "kill $API_PID $FRONTEND_PID 2>/dev/null" EXIT
    
    # Wait for processes
    wait
fi



