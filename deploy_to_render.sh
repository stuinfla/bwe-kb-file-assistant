#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Building Docker image...${NC}"
docker build -t bwe-assistant .

echo -e "${BLUE}Step 2: Creating Render service...${NC}"
render blueprint create

echo -e "${BLUE}Step 3: Deploying to Render...${NC}"
render deploy

echo -e "${GREEN}Deployment initiated! Your app will be available at: https://bwe-assistant.onrender.com${NC}"
echo -e "${GREEN}Note: First deployment may take a few minutes to complete.${NC}"

# Wait for deployment and verify it's working
echo -e "${BLUE}Waiting for deployment to complete...${NC}"
sleep 60  # Give it some time to deploy

# Check if the service is up
response=$(curl -s -o /dev/null -w "%{http_code}" https://bwe-assistant.onrender.com/health)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}Deployment successful! Application is responding correctly.${NC}"
    open https://bwe-assistant.onrender.com
else
    echo -e "\033[0;31mNote: Application might need a few more minutes to start up fully.${NC}"
    echo -e "\033[0;31mPlease wait and then visit https://bwe-assistant.onrender.com${NC}"
fi
