from assistant_analyzer import AssistantAnalyzer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_file_operations():
    # Initialize the AssistantAnalyzer
    analyzer = AssistantAnalyzer(
        api_key=os.getenv('OPENAI_API_KEY'),
        assistant_id=os.getenv('OPENAI_ASSISTANT_ID')
    )

    # Create a test file
    with open('test.txt', 'w') as f:
        f.write('Test content')

    # Get initial file count
    print('Current files:', len(analyzer.get_file_list()))

    # Upload the file
    file_id = analyzer.upload_file('test.txt')
    print('Upload successful:', file_id is not None)

    # Get updated file count
    print('Files after upload:', len(analyzer.get_file_list()))

    # Delete the file if upload was successful
    if file_id:
        deleted = analyzer.delete_file(file_id)
        print('Delete successful:', deleted)
        print('Files after delete:', len(analyzer.get_file_list()))

    # Clean up
    os.remove('test.txt')

if __name__ == '__main__':
    test_file_operations()
