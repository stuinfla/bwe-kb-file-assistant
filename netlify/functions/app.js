const serverless = require('serverless-http');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Get the Python executable path
const PYTHON_PATH = process.env.PYTHON_PATH || '/usr/local/bin/python3';

exports.handler = async (event, context) => {
  try {
    // Set up environment
    const rootDir = path.join(__dirname, '..', '..');
    process.env.PYTHONPATH = rootDir;
    
    // Ensure uploads directory exists
    const uploadsDir = path.join('/tmp', 'uploads');
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }

    // Create Python process
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn(PYTHON_PATH, ['-c', `
import sys
import os
sys.path.append('${rootDir}')
from app import app

# Set up environment
os.environ['FLASK_ENV'] = 'production'
os.environ['UPLOADS_FOLDER'] = '${uploadsDir}'

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
      `]);

      let output = '';
      let error = '';

      pythonProcess.stdout.on('data', (data) => {
        output += data;
        console.log('Python output:', data.toString());
      });

      pythonProcess.stderr.on('data', (data) => {
        error += data;
        console.error('Python error:', data.toString());
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          console.error('Process exited with code:', code);
          resolve({
            statusCode: 500,
            body: JSON.stringify({ error: error || 'Internal server error' })
          });
          return;
        }

        resolve({
          statusCode: 200,
          headers: {
            'Content-Type': 'text/html'
          },
          body: output || 'Application started successfully'
        });
      });

      pythonProcess.on('error', (err) => {
        console.error('Failed to start Python process:', err);
        reject(err);
      });
    });
  } catch (error) {
    console.error('Handler error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
