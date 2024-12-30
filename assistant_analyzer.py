import os
from datetime import datetime
import json
from collections import defaultdict
import re
import logging
import openai
from dotenv import load_dotenv
import calendar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AssistantAnalyzer:
    def __init__(self, api_key=None, assistant_id=None, vector_store_id=None):
        """Initialize the analyzer with OpenAI credentials."""
        self.limited_mode = False
        self.api_key = api_key
        self.assistant_id = assistant_id
        self.vector_store_id = vector_store_id
        
        try:
            if not api_key or not assistant_id or not vector_store_id:
                logger.warning("Missing OpenAI configuration, running in limited mode")
                self.limited_mode = True
                return
            
            logger.info("Initializing OpenAI client...")
            logger.info(f"Using Assistant ID: {assistant_id}")
            logger.info(f"Using Vector Store ID: {vector_store_id}")
            
            # Initialize OpenAI client
            try:
                # Set API key
                openai.api_key = api_key
                
                # Create client
                self.client = openai
                
                # Test the connection
                models = self.client.Model.list()
                logger.info(f"Successfully connected to OpenAI API")
            except Exception as e:
                logger.error(f"Failed to connect to OpenAI API: {str(e)}")
                self.limited_mode = True
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.limited_mode = True
            
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
            # Return sample files in limited mode for testing
            sample_files = [
                {
                    'filename': 'Budget_2023-12.pdf',
                    'purpose': 'assistants',
                    'created_at': '2023-12-01',
                    'bytes': 1024,
                    'id': 'file-1Nm1QGSx7wGJBjgN9mhuEWPv'
                },
                {
                    'filename': 'Budget_2023-11.pdf',
                    'purpose': 'assistants',
                    'created_at': '2023-11-01',
                    'bytes': 1024,
                    'id': 'file-AelwhTKBuYAmzcCTJGgySAzI'
                },
                {
                    'filename': 'Maintenance_Report_2023-12.pdf',
                    'purpose': 'assistants',
                    'created_at': '2023-12-15',
                    'bytes': 2048,
                    'id': 'file-BwpXdzFVD9MG5StLuvD4mn5f'
                },
                {
                    'filename': 'Emergency_Plan_2023.pdf',
                    'purpose': 'assistants',
                    'created_at': '2023-12-01',
                    'bytes': 3072,
                    'id': 'file-YRJiDnZakMCHoAcbFPAiv7n9'
                }
            ]
            logger.info(f"Running in limited mode. Returning {len(sample_files)} sample files.")
            return sample_files
            
        try:
            # List all files
            files = self.client.File.list()
            
            # Filter for files associated with assistants
            files_info = []
            for file in files.data:
                if file.purpose == "assistants":
                    files_info.append({
                        'filename': file.filename,
                        'purpose': file.purpose,
                        'created_at': datetime.fromtimestamp(file.created_at).strftime('%Y-%m-%d'),
                        'bytes': file.bytes,
                        'id': file.id
                    })
            
            # Group files by prefix to find sequences
            files_by_prefix = defaultdict(list)
            for file in files_info:
                # Extract prefix (e.g., "Budget" from "Budget_2023-06.pdf")
                prefix = re.split(r'[_\s-]', file['filename'])[0]
                files_by_prefix[prefix].append(file)
            
            # Find gaps in sequences
            gaps = self.find_gaps_in_sequence(files_by_prefix)
            if gaps:
                logger.warning("Found gaps in file sequences:")
                for gap in gaps:
                    logger.warning(f"Missing {gap['prefix']} for {gap['missing_date']}")
            
            # Sort files chronologically
            files_info.sort(key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%d'))
            
            logger.info(f"Retrieved {len(files_info)} files from assistant {self.assistant_id}")
            return files_info
        except Exception as e:
            logger.error(f"Error retrieving vector store files: {str(e)}")
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
                uploaded_file = self.client.File.create(
                    file=file,
                    purpose='assistants'
                )
            
            # Attach to assistant
            self.client.AssistantFile.create(
                assistant_id=self.assistant_id,
                file_id=uploaded_file.id
            )
            
            logger.info(f"Successfully uploaded file: {file_path}")
            return uploaded_file
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise

    def delete_file(self, file_id):
        """Delete a file from the assistant."""
        if self.limited_mode:
            logger.warning("Cannot delete file in limited mode")
            return False
            
        try:
            # First check if the file exists
            try:
                self.client.File.retrieve(file_id)
            except Exception as e:
                logger.error(f"File {file_id} not found in OpenAI: {str(e)}")
                return False

            # First try to remove from assistant
            try:
                self.client.AssistantFile.delete(
                    assistant_id=self.assistant_id,
                    file_id=file_id
                )
                logger.info(f"Removed file {file_id} from assistant")
            except Exception as e:
                logger.error(f"Error removing file from assistant: {str(e)}")
                # Continue to delete the file even if removing from assistant fails
                
            # Then delete the file itself
            try:
                self.client.File.delete(file_id)
                logger.info(f"Deleted file {file_id} from OpenAI")
            except Exception as e:
                logger.error(f"Error deleting file from OpenAI: {str(e)}")
                return False
            
            logger.info(f"Successfully deleted file: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in delete_file: {str(e)}")
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
