from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from collections import defaultdict
import time
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_duplicates():
    client = OpenAI()
    files = client.files.list()
    
    # Group files by filename
    filename_to_ids = defaultdict(list)
    for file in files:
        filename_to_ids[file.filename].append(file.id)
    
    # Find duplicates
    duplicates = {
        filename: sorted(ids, reverse=True)  # Sort IDs in reverse order (newest first)
        for filename, ids in filename_to_ids.items()
        if len(ids) > 1
    }
    
    return duplicates

def cleanup_duplicates(duplicates):
    client = OpenAI()
    
    # Show what will be deleted
    total_to_delete = sum(len(ids) - 1 for ids in duplicates.values())
    logger.info(f"\nFound {len(duplicates)} files with duplicates. Will keep the newest version of each.")
    logger.info(f"Total files to be deleted: {total_to_delete}")
    logger.info("\nPlanned deletions:")
    
    for filename, ids in duplicates.items():
        logger.info(f"\n{filename}:")
        logger.info(f"- KEEP: {ids[0]} (newest)")
        for file_id in ids[1:]:
            logger.info(f"- DELETE: {file_id}")
    
    # Proceed with deletion
    logger.info("\nDeleting duplicate files...")
    deleted_count = 0
    
    for filename, ids in duplicates.items():
        # Skip the first ID (newest version)
        for file_id in ids[1:]:
            try:
                logger.info(f"Deleting {filename} (ID: {file_id})")
                client.files.delete(file_id)
                deleted_count += 1
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error deleting file {file_id}: {e}")
    
    logger.info(f"\nDeletion complete. Deleted {deleted_count} duplicate files.")

if __name__ == "__main__":
    load_dotenv()
    duplicates = get_duplicates()
    cleanup_duplicates(duplicates)
