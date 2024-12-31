from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_duplicates():
    load_dotenv()
    client = OpenAI()
    
    # Get all files
    files = client.files.list()
    
    # Find duplicates
    filename_to_ids = defaultdict(list)
    test_files = []
    
    for file in files:
        # Check for test files
        if file.filename.startswith('test') or file.filename == 'sample.txt':
            test_files.append((file.filename, file.id))
        else:
            filename_to_ids[file.filename].append(file.id)
    
    # Print test files if any
    if test_files:
        logger.info("\nRemaining test files:")
        for filename, file_id in test_files:
            logger.info(f"- {filename} (ID: {file_id})")
    
    # Print duplicates
    logger.info("\nDuplicate files:")
    has_duplicates = False
    for filename, ids in filename_to_ids.items():
        if len(ids) > 1:
            has_duplicates = True
            logger.info(f"\n{filename}:")
            for file_id in ids:
                logger.info(f"- ID: {file_id}")
    
    if not has_duplicates:
        logger.info("No duplicate files found.")
    
    return test_files, filename_to_ids

if __name__ == "__main__":
    find_duplicates()
