#!/bin/bash

# Build the Docker image
echo "Building Docker image..."
if ! docker-compose build; then
    echo "Failed to build Docker image."
    exit 1
fi

# Start the Docker container
echo "Starting Docker container..."
if ! docker-compose up -d; then
    echo "Failed to start Docker container."
    exit 1
fi

# Check if the container is running
if [ "$(docker inspect -f '{{.State.Running}}' jsketcher-container)" == "true" ]; then
    echo "Application is running locally via Docker on port 3000."
else
    echo "Failed to start the application."
    exit 1
fi
