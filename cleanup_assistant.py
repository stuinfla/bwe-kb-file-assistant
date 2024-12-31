from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_assistant():
    load_dotenv()
    client = OpenAI()
    assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
    
    # Get all files
    files = client.files.list()
    test_files = [file for file in files if file.filename.startswith('test') or file.filename == 'sample.txt']
    
    # Delete test files
    for file in test_files:
        try:
            logger.info(f"Deleting file: {file.filename} (ID: {file.id})")
            client.files.delete(file.id)
            time.sleep(1)  # Rate limiting
        except Exception as e:
            logger.error(f"Error deleting file {file.id}: {e}")
    
    # Get all vector stores
    vector_stores = client.beta.vector_stores.list()
    test_stores = [store for store in vector_stores.data if store.name is None or store.name.lower().startswith('test')]
    
    # Delete test vector stores
    for store in test_stores:
        try:
            logger.info(f"Deleting vector store: {store.name} (ID: {store.id})")
            client.beta.vector_stores.delete(store.id)
            time.sleep(1)  # Rate limiting
        except Exception as e:
            logger.error(f"Error deleting vector store {store.id}: {e}")

if __name__ == "__main__":
    cleanup_assistant()
