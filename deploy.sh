#!/usr/bin/bash

# Define the Docker compose service name
SERVICE_NAME="jinn"

# Build the Docker image
build_image() {
    # Build the Docker image using the Dockerfile specified in the Docker Compose for the service
    docker-compose build $SERVICE_NAME || {
        echo "Failed to build Docker image for service: $SERVICE_NAME"
        exit 1
    }
}

# Stop any existing containers for the service
stop_existing_container() {
    docker-compose stop $SERVICE_NAME || {
        echo "Failed to stop existing container for service: $SERVICE_NAME"
        exit 1
    }
    docker-compose rm -f $SERVICE_NAME || {
        echo "Failed to remove existing container for service: $SERVICE_NAME"
        exit 1
    }
}

# Start a new container for the service
run_container() {
    docker-compose up -d $SERVICE_NAME || {
        echo "Failed to run Docker container for service: $SERVICE_NAME"
        exit 1
    }
}

# Determine the operating system
UNAME=$(uname)

# Execute the commands based on the operating system
if [[ "$UNAME" == "Darwin" || "$UNAME" == "Linux" || "$UNAME" == "MINGW"* || "$UNAME" == "MSYS_NT"* ]]; then
    build_image && stop_existing_container && run_container
else
    echo "Unsupported operating system: $UNAME"
    exit 1
fi
