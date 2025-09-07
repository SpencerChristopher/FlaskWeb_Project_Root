#!/bin/bash
set -e

# Check for required environment variables
if [ -z "$SECRET_KEY" ] || [ -z "$LOG_LEVEL" ]; then
  echo "Error: Required environment variables (SECRET_KEY, LOG_LEVEL) are not set."
  exit 1
fi

echo "Creating .env file for deployment..."
# Write the environment variables to a .env file
# This is the most reliable way to pass them to docker-compose
echo "SECRET_KEY=${SECRET_KEY}" > .env
echo "LOG_LEVEL=${LOG_LEVEL}" >> .env
echo "MONGO_URI=mongodb://mongo:27017/flaskdb" >> .env


echo "Starting Docker Compose services..."
# docker-compose will automatically use the .env file in the current directory
docker compose up -d --build

# Clean up the temporary .env file so the secret doesn't remain on disk
rm .env

echo "Deployment complete."