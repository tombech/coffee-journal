#!/bin/bash

# Coffee Journal Docker Setup Script
# This script sets up the data directory and starts the application

echo "Setting up Coffee Journal..."

# Create data directory if it doesn't exist
mkdir -p ./data

# Check if data directory is empty
if [ ! "$(ls -A ./data)" ]; then
    echo "Data directory is empty. Copying test data..."
    
    # Check if test_data exists in parent directory
    if [ -d "../test_data" ]; then
        cp -r ../test_data/* ./data/
        echo "Test data copied successfully!"
    else
        echo "Warning: No test data found. The application will start with empty data."
        echo "You can manually copy data files to ./data/ directory."
    fi
else
    echo "Data directory contains files. Using existing data."
fi

echo "Starting Coffee Journal with Docker Compose..."
docker compose up -d

echo ""
echo "Coffee Journal is starting up!"
echo "Backend API: http://localhost:5000/api"
echo "Frontend: http://localhost:3000"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"