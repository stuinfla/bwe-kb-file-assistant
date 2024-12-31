from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_assistant_state():
    load_dotenv()
    client = OpenAI()
    assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
    
    # Get assistant details
    assistant = client.beta.assistants.retrieve(assistant_id)
    logger.info(f"\nAssistant Name: {assistant.name}")
    
    # Get all files
    files = client.files.list()
    logger.info("\nBWE Files in OpenAI:")
    for file in files:
        if not file.filename.startswith('test') and file.filename != 'sample.txt':
            logger.info(f"- {file.filename} (ID: {file.id})")
    
    # Get all vector stores
    vector_stores = client.beta.vector_stores.list()
    logger.info("\nNamed Vector Stores:")
    for store in vector_stores.data:
        if store.name:  # Only show named vector stores
            logger.info(f"- {store.name} (ID: {store.id})")

if __name__ == "__main__":
    show_assistant_state()
