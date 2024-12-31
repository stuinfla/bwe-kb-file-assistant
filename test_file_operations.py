from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_file_count():
    client = OpenAI()
    files = client.files.list()
    return len(list(files))

def test_file_operations():
    load_dotenv()
    client = OpenAI()
    
    # Get initial file count
    initial_count = get_file_count()
    logger.info(f"\nInitial file count: {initial_count}")
    
    # Create test file content
    test_content = "This is a test file for BWE Assistant"
    test_filename = "test_bwe_file.txt"
    
    # Write test content to a temporary file
    with open(test_filename, "w") as f:
        f.write(test_content)
    
    try:
        # Upload test file
        logger.info("\nUploading test file...")
        with open(test_filename, "rb") as f:
            response = client.files.create(
                file=f,
                purpose="assistants"
            )
        test_file_id = response.id
        logger.info(f"Test file uploaded with ID: {test_file_id}")
        
        # Verify file count increased
        count_after_upload = get_file_count()
        logger.info(f"File count after upload: {count_after_upload}")
        assert count_after_upload == initial_count + 1, "File count did not increase after upload"
        
        # Delete test file
        logger.info("\nDeleting test file...")
        client.files.delete(test_file_id)
        logger.info("Test file deleted")
        
        # Verify file count returned to initial
        time.sleep(1)  # Wait for deletion to process
        final_count = get_file_count()
        logger.info(f"Final file count: {final_count}")
        assert final_count == initial_count, "File count did not return to initial value"
        
        logger.info("\nTest completed successfully!")
        logger.info(f"Initial count: {initial_count}")
        logger.info(f"Count after upload: {count_after_upload}")
        logger.info(f"Final count: {final_count}")
        
    finally:
        # Clean up local test file
        if os.path.exists(test_filename):
            os.remove(test_filename)
            logger.info("\nLocal test file cleaned up")

if __name__ == "__main__":
    test_file_operations()
