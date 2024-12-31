# BWE Assistant Updater

A sophisticated document management system built specifically for BWE (Building and Work Environment) documentation. This application helps organize, categorize, and manage building-related documents using OpenAI's intelligent categorization.

## Resources and Configuration

### OpenAI Integration
This application uses the following OpenAI resources:
- Assistant ID: asst_pvAYFhGmPmIDtv2B7jVs8r1g
- Vector Store ID: file-qwZcKqbTWnqVcQPCGPqQIZUx
- API Key: [Set in environment variable]

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_key
OPENAI_ASSISTANT_ID=asst_pvAYFhGmPmIDtv2B7jVs8r1g
OPENAI_VECTOR_STORE_ID=file-qwZcKqbTWnqVcQPCGPqQIZUx

# Server Configuration
PORT=5002  # Default port, overridden by Railway in production
```

## Deployment

This application uses automated deployment via Railway.app with GitHub integration.

### Automated Deployment Process
1. **Local Development**
   ```bash
   # Start local server with auto-restart
   python3 manage_server.py
   ```
   - Server automatically kills existing processes on port 5002
   - Opens browser to verify application
   - Monitors server health every 5 seconds

2. **Code Changes & Testing**
   ```bash
   # After making changes, test locally
   python3 manage_server.py
   ```
   - Server logs in server.log
   - Application logs in app.log
   - Auto-verification of server health

3. **Automated Deployment**
   ```bash
   # Commit changes
   git add .
   git commit -m "Description of changes"
   git push
   ```
   - Railway automatically detects GitHub push
   - Builds and deploys new version
   - No manual deployment steps needed

### Railway.app Configuration
- **GitHub Integration**: Connected to repository
- **Auto-Deploy**: Enabled for main branch
- **Environment Variables**:
  ```
  OPENAI_API_KEY=your_key
  OPENAI_ASSISTANT_ID=asst_pvAYFhGmPmIDtv2B7jVs8r1g
  OPENAI_VECTOR_STORE_ID=file-qwZcKqbTWnqVcQPCGPqQIZUx
  PORT=auto_assigned_by_railway
  ```

### Deployment Verification
- Railway dashboard shows deployment status
- Automatic health checks
- Logs available in Railway dashboard
- No manual intervention required

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

### Dependencies Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (if needed)
npm install
```

### Required Environment Variables
```
OPENAI_API_KEY=your_api_key
OPENAI_ASSISTANT_ID=asst_pvAYFhGmPmIDtv2B7jVs8r1g
OPENAI_VECTOR_STORE_ID=file-qwZcKqbTWnqVcQPCGPqQIZUx
```

## Deployment Options

### Railway.app (Primary)
- Automated deployment via GitHub integration
- Built-in monitoring and logging
- Auto-scaling and reliability

### Vercel (Alternative)
- Alternative deployment option
- Use `setup_env.sh` for environment configuration
- Similar automated deployment process

## Testing
- Automated file operation tests
- Category integrity verification
- Server health monitoring
- End-to-end functionality tests

## Limitations
- Maximum file size: 16MB
- Supported file types: txt, pdf, doc, docx, xls, xlsx, csv, md
- Requires stable internet connection
- OpenAI API rate limits apply

## Maintenance

### Logging
- Application logs are available in Railway.app dashboard
- Local development logs in app.log and server.log

### Monitoring
- Railway.app provides built-in monitoring
- Health checks every 5 seconds
- Automatic restart on failure

### Updates
1. Make changes locally and test
2. Commit and push to GitHub
3. Railway automatically rebuilds and deploys

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

## Support
For issues or questions, please check:
1. System logs
2. Category verification status
3. OpenAI API status
4. Network connectivity
5. Environment variables
