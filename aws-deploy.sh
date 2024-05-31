#!/usr/bin/bash

# Exit script if any command fails
set -e

# Log in to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 585881032377.dkr.ecr.us-east-1.amazonaws.com

# Build the Docker image
docker build -t v3-client .

# Tag the Docker image
docker tag v3-client:latest 585881032377.dkr.ecr.us-east-1.amazonaws.com/v3-client:latest

# Push the Docker image to AWS ECR
docker push 585881032377.dkr.ecr.us-east-1.amazonaws.com/v3-client:latest

# Update the AWS ECS service (suppressing verbose output)
aws ecs update-service --cluster v3-cluster --service v3-client-service --force-new-deployment > /dev/null 2>&1