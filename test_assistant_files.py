import os
import time
from openai import OpenAI
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assistant_files.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AssistantFileManager:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()
        self.assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
        self.vector_store_id = os.getenv('OPENAI_VECTOR_STORE_ID')
        
    def verify_file_upload(self, file_path):
        """Upload a file and verify it's added to the assistant."""
        try:
            # Upload file
            logger.info(f"Uploading file: {file_path}")
            with open(file_path, "rb") as file:
                file_obj = self.client.files.create(
                    file=file,
                    purpose="assistants"
                )
            
            # Wait for file processing
            max_retries = 10
            retry_count = 0
            while retry_count < max_retries:
                file_status = self.client.files.retrieve(file_obj.id)
                if file_status.status == "processed":
                    logger.info(f"File processed successfully: {file_obj.id}")
                    break
                time.sleep(2)
                retry_count += 1
            
            if retry_count >= max_retries:
                logger.error("File processing timed out")
                return False
            
            # Add file to vector store
            vector_store = self.client.beta.vector_stores.create(
                name=f"Test Store - {os.path.basename(file_path)}",
                file_ids=[file_obj.id]
            )
            
            # Poll for vector store readiness
            retry_count = 0
            while retry_count < max_retries:
                store_status = self.client.beta.vector_stores.retrieve(vector_store.id)
                if store_status.status == "completed":
                    logger.info(f"Vector store ready: {vector_store.id}")
                    break
                time.sleep(2)
                retry_count += 1
            
            if retry_count >= max_retries:
                logger.error("Vector store processing timed out")
                return False
            
            # Update assistant with new vector store
            assistant = self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
            )
            
            logger.info(f"File {file_obj.id} successfully added to assistant")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False
    
    def verify_file_deletion(self, file_id, vector_store_id):
        """Verify file deletion from assistant."""
        try:
            # Delete file
            logger.info(f"Deleting file: {file_id}")
            self.client.files.delete(file_id)
            
            # Delete vector store
            logger.info(f"Deleting vector store: {vector_store_id}")
            self.client.beta.vector_stores.delete(vector_store_id)
            
            # Verify file is deleted by checking it doesn't exist
            try:
                self.client.files.retrieve(file_id)
                logger.error(f"File {file_id} still exists after deletion")
                return False
            except Exception as e:
                if "No such File object" in str(e):
                    logger.info(f"File {file_id} successfully deleted")
                    return True
                else:
                    logger.error(f"Unexpected error checking file deletion: {str(e)}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error in deletion process: {str(e)}")
            return False

def test_file_operations():
    """Run end-to-end test of file operations."""
    manager = AssistantFileManager()
    vector_store_id = None
    file_id = None
    
    try:
        # Test file upload
        test_file = "test_data/sample.txt"  # Create this test file
        if not os.path.exists("test_data"):
            os.makedirs("test_data")
            
        # Create a sample test file
        with open(test_file, "w") as f:
            f.write("This is a test document for the BWE Assistant.")
        
        # Test upload
        success = manager.verify_file_upload(test_file)
        if not success:
            logger.error("File upload test failed")
            return False
            
        # Get the uploaded file and vector store IDs
        files = manager.client.files.list()
        test_files = [f for f in files if f.filename == "sample.txt"]
        
        if not test_files:
            logger.error("Uploaded test file not found in file list")
            return False
            
        file_id = test_files[0].id
        
        # Get vector store ID
        vector_stores = manager.client.beta.vector_stores.list()
        test_stores = [vs for vs in vector_stores.data if vs.name == f"Test Store - sample.txt"]
        
        if not test_stores:
            logger.error("Vector store not found")
            return False
            
        vector_store_id = test_stores[0].id
            
        # Test deletion
        success = manager.verify_file_deletion(file_id, vector_store_id)
        if not success:
            logger.error("File deletion test failed")
            return False
            
        logger.info("All file operations tests passed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False
        
    finally:
        # Cleanup in case of any failures
        if file_id:
            try:
                manager.client.files.delete(file_id)
            except:
                pass
        if vector_store_id:
            try:
                manager.client.beta.vector_stores.delete(vector_store_id)
            except:
                pass

if __name__ == "__main__":
    test_file_operations()
