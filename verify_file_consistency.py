from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import time
import json
from assistant_analyzer import AssistantAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_categories():
    """Load categories from JSON file."""
    categories_file = 'categories.json'
    if os.path.exists(categories_file):
        with open(categories_file, 'r') as f:
            data = json.load(f)
            return data.get('categories', []), data.get('file_categories', {})
    return [], {}

def save_categories(file_categories):
    """Save categories to JSON file."""
    categories_file = 'categories.json'
    categories = list(set(file_categories.values()))
    data = {
        'categories': categories,
        'file_categories': file_categories
    }
    with open(categories_file, 'w') as f:
        json.dump(data, f, indent=4)

def verify_file_consistency():
    """Verify consistency between OpenAI files and categories."""
    load_dotenv()
    
    # Initialize analyzer
    analyzer = AssistantAnalyzer(
        api_key=os.getenv('OPENAI_API_KEY'),
        assistant_id=os.getenv('OPENAI_ASSISTANT_ID')
    )
    
    # Get files from OpenAI
    openai_files = analyzer.get_file_list()
    openai_file_ids = {f['id'] for f in openai_files}
    
    # Get categorized files
    categories, file_categories = load_categories()
    categorized_file_ids = set(file_categories.keys())
    
    # Find inconsistencies
    missing_from_openai = categorized_file_ids - openai_file_ids
    missing_from_categories = openai_file_ids - categorized_file_ids
    
    logger.info(f"\nFile Consistency Check:")
    logger.info(f"Files in OpenAI: {len(openai_files)}")
    logger.info(f"Files in categories: {len(file_categories)}")
    
    if missing_from_openai:
        logger.warning(f"\nFiles in categories but not in OpenAI ({len(missing_from_openai)}):")
        for file_id in missing_from_openai:
            logger.warning(f"- {file_id}: {file_categories[file_id]}")
            
        # Clean up categories
        logger.info("\nCleaning up categories...")
        cleaned_categories = {k: v for k, v in file_categories.items() if k in openai_file_ids}
        save_categories(cleaned_categories)
        logger.info("Categories cleaned up")
    else:
        logger.info("\nAll categorized files exist in OpenAI")
        
    if missing_from_categories:
        logger.warning(f"\nFiles in OpenAI but not categorized ({len(missing_from_categories)}):")
        for file_id in missing_from_categories:
            file_info = next((f for f in openai_files if f['id'] == file_id), None)
            if file_info:
                logger.warning(f"- {file_id}: {file_info['filename']}")
    else:
        logger.info("\nAll OpenAI files are categorized")

if __name__ == "__main__":
    verify_file_consistency()
