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

def verify_file_handling():
    """Verify file handling in the app context."""
    load_dotenv()
    
    # Initialize analyzer
    analyzer = AssistantAnalyzer(
        api_key=os.getenv('OPENAI_API_KEY'),
        assistant_id=os.getenv('OPENAI_ASSISTANT_ID')
    )
    
    # Get initial state
    initial_files = analyzer.get_file_list()
    initial_count = len(initial_files)
    initial_categories = load_categories()
    
    logger.info(f"\nInitial state:")
    logger.info(f"Files in OpenAI: {initial_count}")
    logger.info(f"Categories: {len(initial_categories[0])}")
    logger.info(f"Categorized files: {len(initial_categories[1])}")
    
    # Create test file
    test_content = "This is a test file for BWE Assistant"
    test_filename = "test_bwe_verify.txt"
    
    # Write test content to a temporary file
    with open(test_filename, "w") as f:
        f.write(test_content)
    
    try:
        # Upload test file
        logger.info("\nUploading test file...")
        uploaded_file = analyzer.upload_file(test_filename)
        if not uploaded_file:
            raise Exception("Failed to upload file")
        
        test_file_id = uploaded_file.id
        logger.info(f"Test file uploaded with ID: {test_file_id}")
        
        # Verify file was uploaded
        current_files = analyzer.get_file_list()
        logger.info(f"Files after upload: {len(current_files)}")
        assert len(current_files) == initial_count + 1, "File count did not increase after upload"
        
        # Verify file appears in categories
        categories, file_categories = load_categories()
        logger.info(f"Categories after upload: {len(categories)}")
        logger.info(f"Categorized files after upload: {len(file_categories)}")
        
        # Delete test file
        logger.info("\nDeleting test file...")
        success = analyzer.delete_file(test_file_id)
        if not success:
            raise Exception("Failed to delete file")
        logger.info("Test file deleted")
        
        # Verify deletion
        time.sleep(1)  # Wait for deletion to process
        final_files = analyzer.get_file_list()
        final_count = len(final_files)
        final_categories = load_categories()
        
        logger.info(f"\nFinal state:")
        logger.info(f"Files in OpenAI: {final_count}")
        logger.info(f"Categories: {len(final_categories[0])}")
        logger.info(f"Categorized files: {len(final_categories[1])}")
        
        # Verify counts
        assert final_count == initial_count, "File count did not return to initial value"
        
        logger.info("\nVerification completed successfully!")
        logger.info("File handling in the app is working correctly.")
        
    finally:
        # Clean up local test file
        if os.path.exists(test_filename):
            os.remove(test_filename)
            logger.info("\nLocal test file cleaned up")

if __name__ == "__main__":
    verify_file_handling()
