#!/bin/bash

# Load environment variables
source .env

# Set environment variables in Vercel
vercel env add OPENAI_API_KEY production <<< "$OPENAI_API_KEY"
vercel env add OPENAI_ASSISTANT_ID production <<< "$OPENAI_ASSISTANT_ID"
vercel env add OPENAI_VECTOR_STORE_ID production <<< "$OPENAI_VECTOR_STORE_ID"

# Redeploy with environment variables
vercel --prod
