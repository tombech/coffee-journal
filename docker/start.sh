#!/bin/bash

# Coffee Journal Docker Startup Script

set -e  # Exit on any error

echo "🚀 Starting Coffee Journal Docker deployment..."

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed or not in PATH"
    exit 1
fi

# Navigate to the docker directory
cd "$(dirname "$0")"

# Create data directory if it doesn't exist
if [ ! -d "../data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p ../data
fi

# Check if ports are available
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Warning: Port 3000 is already in use"
    echo "   You may need to stop other services or change the port in docker-compose.yml"
fi

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Warning: Port 5000 is already in use"
    echo "   You may need to stop other services or change the port in docker-compose.yml"
fi

# Parse command line arguments
BUILD_FLAG=""
DETACHED_FLAG=""
INIT_DB="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --detached|-d)
            DETACHED_FLAG="-d"
            shift
            ;;
        --init-db)
            INIT_DB="true"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build        Force rebuild of Docker images"
            echo "  --detached,-d  Run in detached mode (background)"
            echo "  --init-db      Initialize database with sample data"
            echo "  --help,-h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Start in foreground"
            echo "  $0 --build           # Rebuild and start"
            echo "  $0 -d --init-db      # Start in background with sample data"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Start the application
echo "🔧 Starting Docker Compose..."
docker-compose up $BUILD_FLAG $DETACHED_FLAG

# Initialize database if requested
if [ "$INIT_DB" = "true" ]; then
    echo "📊 Initializing database with sample data..."
    sleep 5  # Wait for services to be ready
    docker-compose exec backend python /app/docker/init-db.py
fi

if [ "$DETACHED_FLAG" = "-d" ]; then
    echo ""
    echo "✅ Coffee Journal is running in the background!"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:5000/api"
    echo ""
    echo "📋 Useful commands:"
    echo "   docker-compose logs -f     # View logs"
    echo "   docker-compose ps          # Check status"
    echo "   docker-compose down        # Stop application"
    echo ""
else
    echo ""
    echo "✅ Coffee Journal is running!"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:5000/api"
    echo ""
    echo "Press Ctrl+C to stop"
fi