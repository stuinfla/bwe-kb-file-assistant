#!/bin/bash

# Install Deta CLI
curl -fsSL https://get.deta.dev/cli.sh | sh

# Add to path for this session
export PATH="/Users/stuartkerr/.deta/bin:$PATH"

# Initialize Deta project
deta new --python bwe-assistant

# Set environment variables from .env
source .env
deta update -e OPENAI_API_KEY="$OPENAI_API_KEY"
deta update -e OPENAI_ASSISTANT_ID="$OPENAI_ASSISTANT_ID"
deta update -e OPENAI_VECTOR_STORE_ID="$OPENAI_VECTOR_STORE_ID"

# Deploy
deta deploy

# Get the URL and open it
URL=$(deta details | grep "endpoint:" | awk '{print $2}')
echo "Your app is deployed at: $URL"
open "$URL"
