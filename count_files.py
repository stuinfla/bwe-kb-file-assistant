from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def count_files():
    load_dotenv()
    client = OpenAI()
    
    # Get all files
    files = client.files.list()
    
    # Count by extension
    extension_count = defaultdict(int)
    total_files = 0
    
    for file in files:
        if not file.filename.startswith('test') and file.filename != 'sample.txt':
            total_files += 1
            ext = os.path.splitext(file.filename)[1].lower()
            if ext:
                extension_count[ext] += 1
            else:
                extension_count['no extension'] += 1
    
    # Print results
    logger.info(f"\nTotal BWE Files: {total_files}")
    logger.info("\nBreakdown by type:")
    for ext, count in sorted(extension_count.items()):
        logger.info(f"- {ext}: {count} files")

if __name__ == "__main__":
    count_files()
