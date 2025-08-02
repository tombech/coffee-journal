#!/bin/bash

# Coffee Journal Docker Stop Script

set -e  # Exit on any error

echo "🛑 Stopping Coffee Journal Docker deployment..."

# Navigate to the docker directory
cd "$(dirname "$0")"

# Parse command line arguments
REMOVE_VOLUMES="false"
REMOVE_IMAGES="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes|-v)
            REMOVE_VOLUMES="true"
            shift
            ;;
        --images|-i)
            REMOVE_IMAGES="true"
            shift
            ;;
        --clean|-c)
            REMOVE_VOLUMES="true"
            REMOVE_IMAGES="true"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --volumes,-v   Remove Docker volumes (WARNING: This will delete data!)"
            echo "  --images,-i    Remove Docker images"
            echo "  --clean,-c     Remove both volumes and images"
            echo "  --help,-h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0             # Stop containers only"
            echo "  $0 --images    # Stop and remove images"
            echo "  $0 --clean     # Stop and remove everything (data will be lost!)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Stop the containers
echo "📦 Stopping Docker containers..."
docker-compose down

# Remove volumes if requested
if [ "$REMOVE_VOLUMES" = "true" ]; then
    echo "⚠️  WARNING: Removing Docker volumes - your database will be deleted!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing Docker volumes..."
        docker-compose down -v
    else
        echo "Cancelled - volumes preserved"
        REMOVE_VOLUMES="false"
    fi
fi

# Remove images if requested
if [ "$REMOVE_IMAGES" = "true" ]; then
    echo "🗑️  Removing Docker images..."
    docker-compose down --rmi all
fi

echo "✅ Coffee Journal stopped successfully!"

if [ "$REMOVE_VOLUMES" = "false" ]; then
    echo "📊 Your database is preserved in the ../data directory"
fi