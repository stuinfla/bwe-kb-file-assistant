from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_assistant_state():
    load_dotenv()
    client = OpenAI()
    assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
    
    # Get assistant details
    assistant = client.beta.assistants.retrieve(assistant_id)
    logger.info(f"\nAssistant Name: {assistant.name}")
    
    # Get all files
    files = client.files.list()
    logger.info("\nFiles in OpenAI:")
    for file in files:
        logger.info(f"- {file.filename} (ID: {file.id})")
    
    # Get all vector stores
    vector_stores = client.beta.vector_stores.list()
    logger.info("\nVector Stores:")
    for store in vector_stores.data:
        logger.info(f"- {store.name} (ID: {store.id})")
        
    # Get assistant's vector stores
    if hasattr(assistant, 'tool_resources') and assistant.tool_resources:
        file_search = assistant.tool_resources.get('file_search', {})
        if file_search:
            vector_store_ids = file_search.get('vector_store_ids', [])
            logger.info("\nAssistant's Vector Store IDs:")
            for vs_id in vector_store_ids:
                logger.info(f"- {vs_id}")

if __name__ == "__main__":
    check_assistant_state()
