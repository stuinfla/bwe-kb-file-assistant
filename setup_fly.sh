#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Installing Fly.io CLI...${NC}"
brew install flyctl

echo -e "${BLUE}Step 2: Creating Fly.io configuration...${NC}"
# Create fly.toml configuration file
cat > fly.toml << EOL
app = "bwe-assistant"
primary_region = "ord"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
EOL

# Create Procfile for Fly.io
echo "web: gunicorn app:app" > Procfile

echo -e "${BLUE}Step 3: Logging into Fly.io...${NC}"
flyctl auth login

echo -e "${BLUE}Step 4: Creating Fly.io application...${NC}"
flyctl apps create bwe-assistant

echo -e "${BLUE}Step 5: Setting up environment variables...${NC}"
# Load variables from .env file
source .env

# Set environment variables in Fly.io
flyctl secrets set OPENAI_API_KEY="$OPENAI_API_KEY"
flyctl secrets set OPENAI_ASSISTANT_ID="$OPENAI_ASSISTANT_ID"
flyctl secrets set OPENAI_VECTOR_STORE_ID="$OPENAI_VECTOR_STORE_ID"

echo -e "${BLUE}Step 6: Deploying application...${NC}"
flyctl deploy

echo -e "${GREEN}Setup complete! Your application is being deployed.${NC}"
echo -e "${GREEN}Once deployment is finished, your app will be available at: https://bwe-assistant.fly.dev${NC}"

# Verify deployment
echo -e "${BLUE}Verifying deployment...${NC}"
sleep 30  # Wait for deployment to stabilize
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://bwe-assistant.fly.dev)

if [ $STATUS_CODE -eq 200 ]; then
    echo -e "${GREEN}Deployment successful! Application is responding correctly.${NC}"
    open https://bwe-assistant.fly.dev
else
    echo -e "\033[0;31mWarning: Application might need a few more minutes to start up fully.${NC}"
    echo -e "\033[0;31mPlease wait a few minutes and then visit https://bwe-assistant.fly.dev${NC}"
fi

echo -e "${BLUE}Future deployments:${NC}"
echo -e "To deploy updates in the future, simply run: ${GREEN}flyctl deploy${NC}"
