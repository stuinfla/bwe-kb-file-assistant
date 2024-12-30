# BWE Assistant Updater

A sophisticated document management system built specifically for BWE (Building and Work Environment) documentation. This application helps organize, categorize, and manage building-related documents using OpenAI's intelligent categorization.

## Features

### 1. Intelligent Document Management
- **Smart Categorization**: Automatically categorizes documents into predefined BWE categories
- **Category Verification**: Continuously verifies and optimizes document categorization
- **Bulk Processing**: Handles multiple documents efficiently
- **File Deduplication**: Prevents duplicate document uploads

### 2. BWE-Specific Categories
- Building Management
- Emergency & Safety
- Financial Reports
- Insurance & Assessments
- Legal & Governance
- Maintenance & Installation
- Meeting Documents
- Resident Information
- Rules & Regulations
- Structural Reports

### 3. Advanced Search & Organization
- **Full-Text Search**: Search through document contents and filenames
- **Category Filtering**: Filter documents by specific categories
- **Smart Date Detection**: Automatically extracts and organizes documents by date
- **Gap Analysis**: Identifies missing monthly reports or documentation

### 4. File Operations
- **Secure Upload**: Handle files up to 16MB
- **Category Management**: Add, delete, or modify categories
- **File Deletion**: Remove files from both local storage and OpenAI
- **Batch Operations**: Handle multiple files simultaneously

### 5. System Management
- **Auto-Recovery**: Automatic system recovery from errors
- **Port Management**: Smart handling of port conflicts
- **Browser Integration**: Automatic browser launch and verification
- **State Verification**: Continuous verification of system state

## Technical Architecture

### Backend (Python/Flask)
- Flask web server with RESTful endpoints
- OpenAI integration for intelligent categorization
- File system management with error recovery
- Logging and monitoring system

### Frontend
- Responsive web interface
- Real-time updates
- Category management interface
- File upload progress tracking

### OpenAI Integration
- Uses OpenAI Assistant for document analysis
- Vector store for efficient document searching
- Smart categorization based on document content

## Environment Setup

### Required Environment Variables
```
OPENAI_API_KEY=your_api_key
OPENAI_ASSISTANT_ID=your_assistant_id
OPENAI_VECTOR_STORE_ID=your_vector_store_id
```

### Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
npm install  # for Netlify deployment
```

### Local Development
Run the application locally:
```bash
python3 manage_server.py
```

The server will:
- Auto-detect available ports
- Kill any conflicting processes
- Launch browser automatically
- Verify successful startup

## Deployment to Netlify

### Prerequisites
1. Install Netlify CLI:
```bash
npm install -g netlify-cli
```

2. Login to Netlify:
```bash
netlify login
```

### Environment Setup
Set these variables in Netlify dashboard:
- `OPENAI_API_KEY`
- `OPENAI_ASSISTANT_ID`
- `OPENAI_VECTOR_STORE_ID`

### Deployment Steps
1. Initialize Netlify site:
```bash
netlify init
```

2. Deploy to production:
```bash
netlify deploy --prod
```

Access the site at: https://app.netlify.com/teams/sikerr/sites

## Security Features
- Secure file handling
- Environment variable protection
- Error logging and monitoring
- Safe category management
- Automatic backup system

## Error Recovery
- Automatic port conflict resolution
- System state verification
- Category integrity checks
- File system monitoring
- OpenAI connection recovery

## Maintenance Scripts
- `manage_server.py`: Handles server lifecycle
- `assistant_analyzer.py`: Manages OpenAI integration
- `server_checker.py`: Monitors system health

## Best Practices
- Always use `manage_server.py` to start/stop the server
- Regularly verify category integrity
- Monitor the logs for any issues
- Keep environment variables secure
- Regular system verification checks

## Limitations
- Maximum file size: 16MB
- Supported file types: PDF, DOC, DOCX, TXT
- Requires stable internet connection
- OpenAI API rate limits apply

## Support
For issues or questions, please check:
1. System logs
2. Category verification status
3. OpenAI API status
4. Network connectivity
5. Environment variables
