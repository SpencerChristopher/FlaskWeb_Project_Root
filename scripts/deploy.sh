#!/bin/bash
set -e

# Check for required environment variables
if [ -z "$SECRET_KEY" ] || [ -z "$LOG_LEVEL" ] || [ -z "$ADMIN_USERNAME" ] || [ -z "$ADMIN_PASSWORD" ]; then
  echo "Error: Required environment variables are not set."
  exit 1
fi

echo "Creating persistent .env file with secure permissions..."
# Write the environment variables to a .env file
echo "SECRET_KEY=${SECRET_KEY}" > .env
echo "LOG_LEVEL=${LOG_LEVEL}" >> .env
echo "MONGO_URI=mongodb://mongo:27017/flaskdb" >> .env
echo "ADMIN_USERNAME=${ADMIN_USERNAME}" >> .env
echo "ADMIN_PASSWORD=${ADMIN_PASSWORD}" >> .env

# Set strict file permissions (read/write for owner only)
chmod 600 .env

echo "Starting Docker Compose services..."
# docker-compose will automatically use the .env file in the current directory
docker compose up -d --build

echo "Deployment complete. The .env file has been left for manual operations."