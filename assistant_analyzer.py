import os
from datetime import datetime
import json
from collections import defaultdict
import re
import logging
from openai import OpenAI
from dotenv import load_dotenv
import calendar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AssistantAnalyzer:
    def __init__(self, api_key, assistant_id, vector_store_id=None):
        """Initialize the AssistantAnalyzer."""
        self.limited_mode = False
        try:
            if not api_key or not assistant_id:
                logger.warning("Missing required OpenAI configuration, running in limited mode")
                self.limited_mode = True
                return
                
            logger.info("Initializing OpenAI client...")
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.openai.com/v1"
            )
            self.assistant_id = assistant_id
            logger.info(f"Using Assistant ID: {assistant_id}")
            self.vector_store_id = vector_store_id
            logger.info(f"Using Vector Store ID: {vector_store_id}")
            
            # Test connection
            self.client.models.list()
            logger.info("Successfully connected to OpenAI API")
            
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}", exc_info=True)
            self.limited_mode = True
            
    def _configure_assistant(self):
        """Configure the assistant with proper tools and files."""
        try:
            # Get all files
            files = self.client.files.list()
            assistant_files = [f.id for f in files.data if f.purpose == "assistants"]
            
            # Sort files by creation date (newest first) and limit to 20 for code_interpreter
            sorted_files = sorted(assistant_files, reverse=True)  # Newest first
            code_interpreter_files = sorted_files[:20]  # Take latest 20 files
            
            # Configure tool resources
            tool_resources = {
                "code_interpreter": {"file_ids": code_interpreter_files},
                "file_search": {"file_ids": assistant_files}  # File search can handle more files
            }
            
            # Update assistant with files
            self.client.beta.assistants.update(
                self.assistant_id,
                tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
                tool_resources=tool_resources
            )
            logger.info(f"Successfully configured assistant with {len(code_interpreter_files)} files for code_interpreter and {len(assistant_files)} files for file_search")
            
        except Exception as e:
            logger.error(f"Error configuring assistant: {str(e)}", exc_info=True)
            raise

    def extract_date_from_filename(self, filename):
        """Extract date information from filename."""
        # Look for year-month pattern (e.g., 2023-06, June 2023, 06-2023)
        patterns = [
            r'(\d{4})[_-](\d{2})',  # 2023-06
            r'(\d{2})[_-](\d{4})',  # 06-2023
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{4})',  # June 2023
            r'(\d{4})\s*(January|February|March|April|May|June|July|August|September|October|November|December)'   # 2023 June
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups[0].isdigit():
                    year = int(groups[0])
                    month = int(groups[1]) if groups[1].isdigit() else list(calendar.month_name).index(groups[1].capitalize())
                else:
                    month = list(calendar.month_name).index(groups[0].capitalize())
                    year = int(groups[1])
                return datetime(year, month, 1)
        return None

    def find_gaps_in_sequence(self, files_by_prefix):
        """Find gaps in chronological sequences of files."""
        gaps = []
        for prefix, files in files_by_prefix.items():
            dates = []
            for file in files:
                date = self.extract_date_from_filename(file['filename'])
                if date:
                    dates.append(date)
            
            if len(dates) > 1:
                dates.sort()
                current = dates[0]
                while current <= dates[-1]:
                    if current not in dates:
                        gaps.append({
                            'prefix': prefix,
                            'missing_date': current.strftime('%B %Y')
                        })
                    current = datetime(
                        current.year + (current.month // 12),
                        ((current.month % 12) + 1),
                        1
                    )
        return gaps
        
    def get_vector_store_files(self):
        """Get list of files from the vector store."""
        if self.limited_mode:
            logger.warning("Running in limited mode - no files will be returned")
            return []
            
        try:
            # Get assistant configuration first
            logger.info(f"Retrieving assistant {self.assistant_id}")
            assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            
            # Get all files to get their metadata
            logger.info("Retrieving file list from OpenAI")
            files = self.client.files.list()
            files_by_id = {f.id: f for f in files.data}
            logger.info(f"Retrieved {len(files.data)} total files from OpenAI")
            
            # Get files attached to the assistant
            assistant_files = []
            for file_id in files_by_id:
                if files_by_id[file_id].purpose == "assistants":
                    file = files_by_id[file_id]
                    assistant_files.append({
                        'filename': file.filename,
                        'purpose': file.purpose,
                        'created_at': datetime.fromtimestamp(file.created_at).strftime('%Y-%m-%d'),
                        'bytes': file.bytes,
                        'id': file.id
                    })
            
            # Sort files chronologically
            assistant_files.sort(key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%d'))
            
            logger.info(f"Found {len(assistant_files)} files associated with assistant")
            return assistant_files
            
        except Exception as e:
            logger.error(f"Error retrieving vector store files: {str(e)}", exc_info=True)
            return []

    def get_file_content(self, file_info):
        """Get the content of a file."""
        try:
            # For now, return the filename as content for categorization
            return file_info['filename']
        except Exception as e:
            logger.error(f"Error getting file content: {str(e)}")
            return ""

    def upload_file(self, file_path):
        """Upload a file to the assistant."""
        if self.limited_mode:
            logger.warning("Cannot upload file in limited mode")
            return None
            
        try:
            # Upload file
            with open(file_path, 'rb') as file:
                uploaded_file = self.client.files.create(
                    file=file,
                    purpose='assistants'
                )
            
            # Add file to assistant
            if uploaded_file:
                logger.info(f"File uploaded successfully: {uploaded_file.id}")
                self.client.beta.assistants.files.create(
                    assistant_id=self.assistant_id,
                    file_id=uploaded_file.id
                )
                return uploaded_file.id
            return None
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None

    def delete_file(self, file_id):
        """Delete a file from the assistant."""
        if self.limited_mode:
            logger.warning("Cannot delete file in limited mode")
            return False
            
        try:
            # First remove from assistant
            self.client.beta.assistants.files.delete(
                assistant_id=self.assistant_id,
                file_id=file_id
            )
            
            # Then delete the file itself
            self.client.files.delete(file_id)
            
            logger.info(f"Successfully deleted file: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False

    def analyze_files(self):
        """Analyze the files in the vector store."""
        files = self.get_vector_store_files()
        
        # Print overall stats
        print("\n=== Vector Store Files Analysis ===\n")
        print(f"Vector Store ID: {self.vector_store_id}")
        print(f"Total Files: {len(files)}")
        
        # Categorize files
        categories = self.categorize_files(files)
        print("\n=== Files by Category ===")
        for category, category_files in categories.items():
            if category_files:
                print(f"\n{category}:")
                for f in category_files:
                    print(f"- {f['filename']} (Created: {f['created_at']})")
        
        # Print detailed file listing
        print("\n=== Detailed File Listing ===")
        for f in sorted(files, key=lambda x: x['created_at'], reverse=True):
            print(f"\n- {f['filename']}")
            print(f"  Created: {f['created_at']}")
            print(f"  Size: {f['bytes']} bytes")
            print(f"  Purpose: {f['purpose']}")
            print(f"  ID: {f['id']}")

    def categorize_files(self, files):
        """Categorize files based on their names and purposes."""
        categories = defaultdict(list)
        
        for file in files:
            filename = file['filename'].lower()
            if 'financial' in filename or 'budget' in filename:
                categories['Financial Documents'].append(file)
            elif 'statute' in filename or 'law' in filename or 'resolution' in filename:
                categories['Legal Documents'].append(file)
            elif 'history' in filename:
                categories['Historical Records'].append(file)
            elif any(ext in filename for ext in ['.doc', '.docx', '.pdf', '.txt']):
                categories['General Documents'].append(file)
            else:
                categories['Other'].append(file)
        
        return categories

if __name__ == "__main__":
    try:
        analyzer = AssistantAnalyzer(api_key=os.getenv('OPENAI_API_KEY'), assistant_id=os.getenv('OPENAI_ASSISTANT_ID'), vector_store_id=os.getenv('OPENAI_VECTOR_STORE_ID'))
        analyzer.analyze_files()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
