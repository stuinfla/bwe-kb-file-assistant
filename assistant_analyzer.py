import os
from datetime import datetime
import json
from collections import defaultdict
import re
import logging
from openai import OpenAI
from dotenv import load_dotenv
import calendar
import time

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
                default_headers={"OpenAI-Beta": "assistants=v2"}
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
        """Configure the assistant with the latest file list."""
        if self.limited_mode:
            return

        try:
            # Get current file list
            files = self.get_file_list()
            logger.info(f"Retrieved {len(files)} total files from OpenAI")
            
            # Get current assistant configuration
            assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            logger.info(f"Assistant configuration: {assistant}")
            
            # Get current tool resources
            tool_resources = getattr(assistant, 'tool_resources', None)
            logger.info(f"Current tool resources: {tool_resources}")
            
            # Get current vector store IDs
            vector_store_ids = []
            if tool_resources and hasattr(tool_resources, 'file_search'):
                file_search = tool_resources.file_search
                if hasattr(file_search, 'vector_store_ids'):
                    vector_store_ids = file_search.vector_store_ids
            
            # Get current file IDs for code interpreter
            code_interpreter_file_ids = []
            if tool_resources and hasattr(tool_resources, 'code_interpreter'):
                code_interpreter = tool_resources.code_interpreter
                if hasattr(code_interpreter, 'file_ids'):
                    code_interpreter_file_ids = code_interpreter.file_ids
            
            # Update assistant configuration
            self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
                tool_resources={
                    "code_interpreter": {
                        "file_ids": code_interpreter_file_ids
                    },
                    "file_search": {
                        "vector_store_ids": vector_store_ids
                    }
                }
            )
            logger.info("Successfully updated assistant configuration")
            
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
        
    def get_file_list(self):
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
            logger.info(f"Attempting to upload file: {file_path}")
            with open(file_path, 'rb') as file:
                logger.info("File opened successfully, creating OpenAI file...")
                uploaded_file = self.client.files.create(
                    file=file,
                    purpose='assistants'
                )
                logger.info(f"File created in OpenAI with ID: {uploaded_file.id}")
            
            # Add file to assistant
            if uploaded_file:
                logger.info(f"Adding file {uploaded_file.id} to assistant {self.assistant_id}...")
                
                # Get current assistant configuration
                assistant = self.client.beta.assistants.retrieve(self.assistant_id)
                logger.info(f"Assistant configuration: {assistant}")
                
                # Get current tool resources
                tool_resources = getattr(assistant, 'tool_resources', None)
                logger.info(f"Current tool resources: {tool_resources}")
                
                # Get current files from code_interpreter
                current_files = []
                if tool_resources and hasattr(tool_resources, 'code_interpreter'):
                    code_interpreter = tool_resources.code_interpreter
                    if hasattr(code_interpreter, 'file_ids'):
                        current_files = code_interpreter.file_ids
                
                logger.info(f"Current files: {current_files}")
                
                # Add new file to list if not already present
                if uploaded_file.id not in current_files:
                    current_files.append(uploaded_file.id)
                
                # Update assistant with new file list
                logger.info("Updating assistant with new configuration...")
                updated_assistant = self.client.beta.assistants.update(
                    assistant_id=self.assistant_id,
                    tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
                    tool_resources={
                        "code_interpreter": {
                            "file_ids": current_files
                        }
                    }
                )
                logger.info(f"Updated assistant configuration: {updated_assistant}")
                
                # Update assistant configuration
                self._configure_assistant()
                return uploaded_file
            return None
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}", exc_info=True)
            return None

    def delete_file(self, file_id):
        """Delete a file from OpenAI."""
        try:
            # Delete the file
            logger.info(f"Attempting to delete file {file_id}")
            if isinstance(file_id, dict) and 'id' in file_id:
                file_id = file_id['id']
            elif hasattr(file_id, 'id'):
                file_id = file_id.id
            self.client.files.delete(file_id=file_id)
            logger.info(f"Successfully deleted file {file_id}")
            
            # Update assistant configuration
            self._configure_assistant()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}", exc_info=True)
            return False

    def analyze_files(self):
        """Analyze the files in the vector store."""
        files = self.get_file_list()
        
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

    def create_thread(self):
        """Create a new thread for conversation."""
        if self.limited_mode:
            logger.warning("Cannot create thread in limited mode")
            return None
            
        try:
            thread = self.client.beta.threads.create()
            logger.info(f"Created new thread with ID: {thread.id}")
            return thread
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            return None

    def add_message_to_thread(self, thread_id, content, file_ids=None):
        """Add a message to an existing thread."""
        if self.limited_mode:
            logger.warning("Cannot add message in limited mode")
            return None
            
        try:
            message_params = {
                "role": "user",
                "content": content
            }
            
            if file_ids:
                message_params["attachments"] = [
                    {"file_id": file_id, "tools": [{"type": "code_interpreter"}]} 
                    for file_id in file_ids
                ]
            
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                **message_params
            )
            logger.info(f"Added message to thread {thread_id}")
            return message
        except Exception as e:
            logger.error(f"Error adding message to thread: {str(e)}")
            return None

    def run_assistant(self, thread_id, instructions=None):
        """Run the assistant on a thread."""
        if self.limited_mode:
            logger.warning("Cannot run assistant in limited mode")
            return None
            
        try:
            run_params = {
                "assistant_id": self.assistant_id,
                "thread_id": thread_id
            }
            
            if instructions:
                run_params["instructions"] = instructions
            
            run = self.client.beta.threads.runs.create(**run_params)
            logger.info(f"Started run {run.id} on thread {thread_id}")
            return run
        except Exception as e:
            logger.error(f"Error starting run: {str(e)}")
            return None

    def wait_for_run(self, thread_id, run_id, timeout=300):
        """Wait for a run to complete and return the final status."""
        if self.limited_mode:
            logger.warning("Cannot wait for run in limited mode")
            return None
            
        try:
            start_time = datetime.now()
            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status in ['completed', 'failed', 'expired', 'cancelled']:
                    logger.info(f"Run {run_id} finished with status: {run.status}")
                    return run
                
                # Check for timeout
                if (datetime.now() - start_time).total_seconds() > timeout:
                    logger.warning(f"Run {run_id} timed out after {timeout} seconds")
                    return run
                
                # Check for required actions
                if run.status == 'requires_action':
                    logger.info(f"Run {run_id} requires action")
                    return run
                
                time.sleep(1)  # Wait before checking again
                
        except Exception as e:
            logger.error(f"Error waiting for run: {str(e)}")
            return None

    def get_messages(self, thread_id, limit=100):
        """Get messages from a thread."""
        if self.limited_mode:
            logger.warning("Cannot get messages in limited mode")
            return []
            
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=limit
            )
            return messages.data
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []

    def process_message_annotations(self, message):
        """Process annotations in a message."""
        try:
            if not message.content or not message.content[0].text:
                return ""
                
            message_content = message.content[0].text
            annotations = message_content.annotations
            citations = []
            
            # Process annotations
            for index, annotation in enumerate(annotations):
                # Replace the text with a footnote
                message_content.value = message_content.value.replace(
                    annotation.text, 
                    f' [{index}]'
                )
                
                # Gather citations
                if hasattr(annotation, 'file_citation'):
                    file = self.client.files.retrieve(annotation.file_citation.file_id)
                    citations.append(
                        f'[{index}] {annotation.file_citation.quote} from {file.filename}'
                    )
                elif hasattr(annotation, 'file_path'):
                    file = self.client.files.retrieve(annotation.file_path.file_id)
                    citations.append(
                        f'[{index}] Generated file: {file.filename}'
                    )
            
            # Add footnotes to the message
            if citations:
                message_content.value += '\n\n' + '\n'.join(citations)
            
            return message_content.value
            
        except Exception as e:
            logger.error(f"Error processing message annotations: {str(e)}")
            return ""

if __name__ == "__main__":
    try:
        analyzer = AssistantAnalyzer(api_key=os.getenv('OPENAI_API_KEY'), assistant_id=os.getenv('OPENAI_ASSISTANT_ID'), vector_store_id=os.getenv('OPENAI_VECTOR_STORE_ID'))
        analyzer.analyze_files()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
