#!/bin/bash

# Default host
LAB_HOST="localhost"

# Check for argument
if [ ! -z "$1" ]; then
    LAB_HOST=$1
fi

echo "Starting OAuth 2.0 Vulnerability Lab on $LAB_HOST..."

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed."
    exit 1
fi

# Build and start containers with env var
LAB_HOST=$LAB_HOST docker compose up -d --build

echo ""
echo "=================================================="
echo "Lab Started Successfully!"
echo "=================================================="
echo "1. PhotoApp (Client): http://$LAB_HOST:8083"
echo "2. SocialID (Provider): http://$LAB_HOST:3000"
echo "3. Admin Bot: Running in background"
echo ""
echo "Your Goal: Take over the Admin account on PhotoApp to get the Flag."
echo "Hint: Analyze the OAuth authorization request."
echo "=================================================="
