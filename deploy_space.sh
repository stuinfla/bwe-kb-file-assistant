#!/bin/bash

# Install Space CLI
curl -fsSL https://deta.space/assets/space-cli.sh | sh

# Add to path for this session
export PATH="/Users/stuartkerr/.detaspace/bin:$PATH"

# Initialize Space project
space new

# Set environment variables from .env
source .env
space env set OPENAI_API_KEY="$OPENAI_API_KEY"
space env set OPENAI_ASSISTANT_ID="$OPENAI_ASSISTANT_ID"
space env set OPENAI_VECTOR_STORE_ID="$OPENAI_VECTOR_STORE_ID"

# Deploy
space push

# Get the URL and open it
URL=$(space link)
echo "Your app is deployed at: $URL"
open "$URL"
