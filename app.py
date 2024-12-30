import os
import json
import calendar
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash
from werkzeug.utils import secure_filename
import logging
import sys
from assistant_analyzer import AssistantAnalyzer
from pathlib import Path
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Completely disable all Flask logging
logging.getLogger('werkzeug').disabled = True
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.logger.disabled = True
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

# Configure app paths
UPLOAD_FOLDER = 'uploads'
CATEGORIES_FILE = 'categories.json'

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure app
app.config.update(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    CATEGORIES_FILE=CATEGORIES_FILE,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    TEMPLATES_AUTO_RELOAD=True,
    template_folder='templates',  # Explicitly set template folder
    static_folder='static'       # Explicitly set static folder
)

# Initialize OpenAI client
analyzer = None
try:
    analyzer = AssistantAnalyzer(
        api_key=os.getenv('OPENAI_API_KEY'),
        assistant_id=os.getenv('OPENAI_ASSISTANT_ID'),
        vector_store_id=os.getenv('OPENAI_VECTOR_STORE_ID')
    )
except Exception as e:
    print(f"Failed to initialize AssistantAnalyzer: {str(e)}")

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'md'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def categorize_file(filename, content):
    """Improved file categorization based on filename and content."""
    filename_lower = filename.lower()
    content_lower = content.lower() if content else ""
    
    # Financial Reports
    financial_keywords = {
        'financial', 'finance', 'budget', 'expense', 'revenue', 'assessment',
        'balance sheet', 'income', 'cash flow', 'invoice', 'payment',
        'accounting', 'fiscal', 'tax', 'audit', 'special assessment'
    }
    
    # Building Management
    building_keywords = {
        'building', 'maintenance', 'repair', 'facility', 'property',
        'renovation', 'upgrade', 'construction', 'improvement',
        'work schedule', 'inspection'
    }
    
    # Emergency & Safety
    emergency_keywords = {
        'emergency', 'safety', 'security', 'evacuation', 'fire',
        'disaster', 'hazard', 'incident', 'alert', 'warning',
        'protection', 'prevention'
    }
    
    # Legal & Governance
    legal_keywords = {
        'legal', 'law', 'regulation', 'policy', 'compliance', 'contract',
        'bylaw', 'statute', 'declaration', 'amendment', 'certificate',
        'articles', 'incorporation', 'governance'
    }
    
    # Insurance & Assessments
    insurance_keywords = {
        'insurance', 'assessment', 'claim', 'coverage', 'policy',
        'liability', 'risk', 'premium', 'deductible', 'certificate'
    }
    
    # Maintenance & Installation
    maintenance_keywords = {
        'maintenance', 'installation', 'repair', 'equipment', 'system',
        'service', 'inspection', 'replacement', 'upgrade', 'fix',
        'cleaning', 'hvac', 'elevator', 'plumbing'
    }
    
    # Meeting Documents
    meeting_keywords = {
        'meeting', 'minutes', 'agenda', 'board', 'committee',
        'discussion', 'resolution', 'vote', 'attendance', 'quorum'
    }
    
    # Resident Information
    resident_keywords = {
        'resident', 'tenant', 'owner', 'occupant', 'community',
        'neighbor', 'directory', 'contact', 'parking', 'pet',
        'move-in', 'move-out', 'handbook'
    }
    
    # Rules & Regulations
    rules_keywords = {
        'rule', 'regulation', 'guideline', 'policy', 'procedure',
        'requirement', 'standard', 'restriction', 'conduct', 'code'
    }
    
    # Structural Reports
    structural_keywords = {
        'structural', 'engineering', 'inspection', 'foundation',
        'building envelope', 'roof', 'wall', 'concrete', 'steel',
        'assessment', 'integrity', 'structure'
    }
    
    # Check content and filename against keywords
    def check_keywords(text, keywords):
        return any(keyword in text for keyword in keywords)
    
    if check_keywords(filename_lower, financial_keywords):
        return "Financial Reports"
    elif check_keywords(filename_lower, building_keywords):
        return "Building Management"
    elif check_keywords(filename_lower, emergency_keywords):
        return "Emergency & Safety"
    elif check_keywords(filename_lower, legal_keywords):
        return "Legal & Governance"
    elif check_keywords(filename_lower, insurance_keywords):
        return "Insurance & Assessments"
    elif check_keywords(filename_lower, maintenance_keywords):
        return "Maintenance & Installation"
    elif check_keywords(filename_lower, meeting_keywords):
        return "Meeting Documents"
    elif check_keywords(filename_lower, resident_keywords):
        return "Resident Information"
    elif check_keywords(filename_lower, rules_keywords):
        return "Rules & Regulations"
    elif check_keywords(filename_lower, structural_keywords):
        return "Structural Reports"
    
    # If no match found in filename, try content
    if content:
        if check_keywords(content_lower, financial_keywords):
            return "Financial Reports"
        elif check_keywords(content_lower, building_keywords):
            return "Building Management"
        elif check_keywords(content_lower, emergency_keywords):
            return "Emergency & Safety"
        elif check_keywords(content_lower, legal_keywords):
            return "Legal & Governance"
        elif check_keywords(content_lower, insurance_keywords):
            return "Insurance & Assessments"
        elif check_keywords(content_lower, maintenance_keywords):
            return "Maintenance & Installation"
        elif check_keywords(content_lower, meeting_keywords):
            return "Meeting Documents"
        elif check_keywords(content_lower, resident_keywords):
            return "Resident Information"
        elif check_keywords(content_lower, rules_keywords):
            return "Rules & Regulations"
        elif check_keywords(content_lower, structural_keywords):
            return "Structural Reports"
    
    # Special cases based on file patterns
    if 'declaration' in filename_lower or 'amendment' in filename_lower:
        return "Legal & Governance"
    elif 'assessment' in filename_lower:
        return "Insurance & Assessments"
    elif 'schedule' in filename_lower:
        return "Building Management"
    elif 'certificate' in filename_lower:
        return "Legal & Governance"
    elif 'reference' in filename_lower:
        return "Resident Information"
    
    return "General Documents"

def extract_month_year(file):
    """Extract month and year from file metadata and filename."""
    filename = file.get('filename', '').lower()
    
    # Try to find a date pattern in the filename
    date_patterns = [
        r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[- _]*(\d{4})',
        r'(\d{4})[- _]*(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)',
        r'(\d{4})[- _]*(\d{1,2})',
        r'(\d{1,2})[- _]*(\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                # Pattern with month name and year
                month_str = filename[match.start():match.end()].split(groups[0])[0].strip('- _')
                month = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }.get(month_str[:3], None)
                if month:
                    return month, int(groups[0])
            elif len(groups) == 2:
                # Pattern with numeric month and year
                if int(groups[0]) > 1000:  # Year first
                    year, month = int(groups[0]), int(groups[1])
                else:  # Month first
                    month, year = int(groups[0]), int(groups[1])
                if 1 <= month <= 12:
                    return month, year
    
    # If no date found in filename, try to use the upload date
    created_at = file.get('created_at')
    if created_at:
        try:
            date = datetime.strptime(created_at, '%Y-%m-%d')
            return date.month, date.year
        except ValueError:
            pass
    
    return None, None

def identify_gaps(files):
    """Identify gaps in monthly reports."""
    if not files:
        return []
    
    # Extract dates and sort files by date
    dated_files = []
    for file in files:
        try:
            month, year = extract_month_year(file)
            if month and year:
                dated_files.append({
                    'file': file,
                    'date': datetime(year, month, 1),
                    'month': month,
                    'year': year
                })
        except Exception as e:
            print(f"Error extracting date from file {file.get('filename', 'unknown')}: {str(e)}")
    
    # Sort by date
    dated_files.sort(key=lambda x: x['date'])
    
    # If no dated files found, return empty list
    if not dated_files:
        return []
    
    # Find the date range we should check
    end_date = datetime.now()
    start_date = dated_files[0]['date']
    
    # Only check the last 12 months
    twelve_months_ago = datetime(end_date.year, end_date.month, 1)
    if (end_date - start_date).days > 365:
        start_date = twelve_months_ago
    
    # Create a set of all months we have files for
    existing_dates = {(f['year'], f['month']) for f in dated_files}
    
    # Check each month in the range
    missing_months = []
    current_date = start_date
    while current_date <= end_date:
        if (current_date.year, current_date.month) not in existing_dates:
            missing_months.append(f"{calendar.month_name[current_date.month]} {current_date.year}")
        current_date = datetime(
            current_date.year + (current_date.month // 12),
            (current_date.month % 12) + 1,
            1
        )
    
    return missing_months

def get_file_category(file_info, file_categories):
    """Get category for a file based on its ID or filename pattern."""
    # First try to get category from file_categories mapping
    if file_info['id'] in file_categories:
        return file_categories[file_info['id']]
    
    # If not found, try to determine category from filename
    filename = file_info['filename'].lower()
    
    # Define category patterns
    patterns = {
        'Financial Reports': [
            'budget', 'financial', 'expense', 'revenue', 'assessment',
            'balance sheet', 'income', 'cash flow', 'invoice', 'payment',
            'accounting', 'fiscal', 'tax', 'audit', 'special assessment'
        ],
        'Building Management': [
            'building', 'maintenance', 'repair', 'facility', 'property',
            'renovation', 'upgrade', 'construction', 'improvement',
            'work schedule', 'inspection'
        ],
        'Emergency & Safety': [
            'emergency', 'safety', 'security', 'evacuation', 'fire',
            'disaster', 'hazard', 'incident', 'alert', 'warning',
            'protection', 'prevention'
        ],
        'Legal & Governance': [
            'legal', 'law', 'regulation', 'policy', 'compliance', 'contract',
            'bylaw', 'statute', 'declaration', 'amendment', 'certificate',
            'articles', 'incorporation', 'governance'
        ],
        'Insurance & Assessments': [
            'insurance', 'assessment', 'claim', 'coverage', 'policy',
            'liability', 'risk', 'premium', 'deductible', 'certificate'
        ],
        'Maintenance & Installation': [
            'maintenance', 'installation', 'repair', 'equipment', 'system',
            'service', 'inspection', 'replacement', 'upgrade', 'fix',
            'cleaning', 'hvac', 'elevator', 'plumbing'
        ],
        'Meeting Documents': [
            'meeting', 'minutes', 'agenda', 'board', 'committee',
            'discussion', 'resolution', 'vote', 'attendance', 'quorum'
        ],
        'Resident Information': [
            'resident', 'tenant', 'owner', 'occupant', 'community',
            'neighbor', 'directory', 'contact', 'parking', 'pet',
            'move-in', 'move-out', 'handbook'
        ],
        'Rules & Regulations': [
            'rule', 'regulation', 'guideline', 'policy', 'procedure',
            'requirement', 'standard', 'restriction', 'conduct', 'code'
        ],
        'Structural Reports': [
            'structural', 'engineering', 'inspection', 'foundation',
            'building envelope', 'roof', 'wall', 'concrete', 'steel',
            'assessment', 'integrity', 'structure'
        ]
    }
    
    # Check filename against patterns
    for category, keywords in patterns.items():
        if any(keyword in filename for keyword in keywords):
            return category
            
    # Special cases based on file patterns
    if 'declaration' in filename or 'amendment' in filename:
        return "Legal & Governance"
    elif 'assessment' in filename:
        return "Insurance & Assessments"
    elif 'schedule' in filename:
        return "Building Management"
    elif 'certificate' in filename:
        return "Legal & Governance"
    elif 'reference' in filename:
        return "Resident Information"
    
    return "General Documents"

def verify_categories_integrity():
    """Verify the integrity of categories and their contents."""
    try:
        # Load categories
        all_categories, file_categories = load_categories()
        
        # Get files from OpenAI
        if not analyzer:
            logger.error("Cannot verify categories: OpenAI analyzer not initialized")
            return False
            
        files = analyzer.get_vector_store_files()
        openai_file_ids = {f['id'] for f in files}
        category_file_ids = set(file_categories.keys())
        
        # Check 1: All default categories exist
        default_categories = [
            "Building Management", "Emergency & Safety", "Financial Reports",
            "General Documents", "Insurance & Assessments", "Legal & Governance",
            "Maintenance & Installation", "Meeting Documents", "Resident Information",
            "Rules & Regulations", "Structural Reports", "Uncategorized"
        ]
        missing_categories = [cat for cat in default_categories if cat not in all_categories]
        if missing_categories:
            logger.error(f"Missing default categories: {missing_categories}")
            return False
            
        # Check 2: All categorized files exist in OpenAI
        ghost_files = category_file_ids - openai_file_ids
        if ghost_files:
            logger.error(f"Found {len(ghost_files)} files in categories that don't exist in OpenAI")
            for file_id in ghost_files:
                del file_categories[file_id]
            save_categories(file_categories)
            
        # Check 3: All OpenAI files are categorized
        uncategorized_files = openai_file_ids - category_file_ids
        if uncategorized_files:
            logger.error(f"Found {len(uncategorized_files)} uncategorized files")
            for file_id in uncategorized_files:
                file = next(f for f in files if f['id'] == file_id)
                # Try both categorization methods
                cat = get_file_category(file, file_categories)
                if cat == "General Documents":
                    # If get_file_category returns General, try categorize_file
                    alt_cat = categorize_file(file['filename'], None)
                    if alt_cat != "General Documents":
                        cat = alt_cat
                file_categories[file_id] = cat
            save_categories(file_categories)
            
        # Check 4: All files are in valid categories
        invalid_categories = [cat for cat in set(file_categories.values()) if cat not in all_categories]
        if invalid_categories:
            logger.error(f"Found files in invalid categories: {invalid_categories}")
            for file_id, cat in file_categories.items():
                if cat not in all_categories:
                    file_categories[file_id] = "General Documents"
            save_categories(file_categories)
            
        # Check 5: Verify categorization is optimal
        changes_made = False
        for file_id, current_cat in file_categories.items():
            if current_cat in ["General Documents", "Uncategorized"]:
                file = next(f for f in files if f['id'] == file_id)
                # Try both categorization methods
                new_cat = get_file_category(file, {})  # Empty dict to force pattern matching
                if new_cat == "General Documents":
                    new_cat = categorize_file(file['filename'], None)
                if new_cat != current_cat and new_cat != "General Documents":
                    file_categories[file_id] = new_cat
                    changes_made = True
                    logger.info(f"Recategorized {file['filename']} from {current_cat} to {new_cat}")
        
        if changes_made:
            save_categories(file_categories)
            
        logger.info("Category verification complete")
        return True
    except Exception as e:
        logger.error(f"Error verifying categories: {str(e)}")
        return False

def load_categories():
    """Load categories from JSON file."""
    default_categories = [
        "Building Management",
        "Emergency & Safety",
        "Financial Reports",
        "General Documents",
        "Insurance & Assessments",
        "Legal & Governance",
        "Maintenance & Installation",
        "Meeting Documents",
        "Resident Information",
        "Rules & Regulations",
        "Structural Reports",
        "Uncategorized"
    ]
    try:
        with open(app.config['CATEGORIES_FILE'], 'r') as f:
            data = json.load(f)
            return data.get('categories', default_categories), data.get('file_categories', {})
    except FileNotFoundError:
        # If file doesn't exist, create it with default categories
        data = {
            'categories': default_categories,
            'file_categories': {}
        }
        with open(app.config['CATEGORIES_FILE'], 'w') as f:
            json.dump(data, f, indent=4)
        return default_categories, {}
    except Exception as e:
        logger.error(f"Error loading categories: {str(e)}")
        return default_categories, {}

def save_categories(file_categories):
    """Save categories to JSON file."""
    try:
        # Load existing categories or use defaults
        all_categories, _ = load_categories()
        
        # Prepare data to save
        data = {
            'categories': all_categories,
            'file_categories': file_categories
        }
        
        # Save to file
        with open(app.config['CATEGORIES_FILE'], 'w') as f:
            json.dump(data, f, indent=4)
            
        logger.info("Successfully saved categories")
        return True
    except Exception as e:
        logger.error(f"Error saving categories: {str(e)}")
        return False

@app.route('/update_category', methods=['POST'])
def update_category():
    """Update a file's category."""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        new_category = data.get('new_category')
        
        if not file_id or not new_category:
            return jsonify({'success': False, 'error': 'Missing file_id or new_category'}), 400
        
        # Load current categories
        all_categories, file_categories = load_categories()
        
        # Validate category
        if new_category not in all_categories:
            return jsonify({'success': False, 'error': f'Invalid category: {new_category}'}), 400
        
        # Get the file info from the assistant to verify it exists
        if not analyzer:
            return jsonify({'success': False, 'error': 'Assistant not initialized'}), 500
            
        files = analyzer.get_vector_store_files()
        file_exists = any(f['id'] == file_id for f in files)
        if not file_exists:
            return jsonify({'success': False, 'error': f'File not found: {file_id}'}), 404
        
        # Update category
        old_category = file_categories.get(file_id)
        file_categories[file_id] = new_category
        
        # Save updated categories
        if not save_categories(file_categories):
            return jsonify({'success': False, 'error': 'Failed to save categories'}), 500
        
        print(f"Updated category for file {file_id} from {old_category} to {new_category}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating category: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
@app.route('/category/<category>')
def index(category=None):
    try:
        # First verify categories integrity
        verify_categories_integrity()
        
        # Load categories
        all_categories, file_categories = load_categories()
        
        # Initialize empty categories
        categories = {cat: [] for cat in all_categories}
        gaps = {}
        
        if not analyzer:
            return render_template('index.html', 
                                categories=categories,
                                all_categories=all_categories,
                                selected_category=category,
                                gaps=gaps,
                                error="OpenAI configuration error. The application will work in limited mode.")
        
        # Get all files from OpenAI
        files = analyzer.get_vector_store_files() if analyzer else []
        
        # Organize files by category
        for file in files:
            try:
                cat = file_categories.get(file['id'], 'Uncategorized')
                categories[cat].append(file)
            except Exception as e:
                logger.error(f"Error organizing file {file.get('filename', 'unknown')}: {str(e)}")
                continue
        
        # Sort files and identify gaps
        for cat in categories:
            try:
                if cat in ["Financial Reports", "Building Management"]:
                    categories[cat].sort(key=lambda x: extract_month_year(x)[::-1], reverse=True)
                    gaps[cat] = identify_gaps(categories[cat])
                else:
                    categories[cat].sort(key=lambda x: x.get('created_at', ''), reverse=True)
            except Exception as e:
                logger.error(f"Error sorting category {cat}: {str(e)}")
        
        # Verify we have all categories
        for cat in all_categories:
            if cat not in categories:
                logger.error(f"Category {cat} missing after organization")
                categories[cat] = []
        
        # If category is specified but doesn't exist, redirect to home
        if category and category not in all_categories:
            return redirect(url_for('index'))
        
        return render_template('index.html', 
                             categories=categories,
                             all_categories=all_categories,
                             selected_category=category,
                             gaps=gaps)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', categories={}, error=str(e))

@app.route('/add_category', methods=['POST'])
def add_category():
    """Add a new category."""
    try:
        categories = load_categories()
        new_category = f"New Category {len(categories)}"
        categories.append(new_category)
        save_categories(categories)
        return redirect(url_for('index', category=new_category))
    except Exception as e:
        print(f"Error adding category: {str(e)}")
        return redirect(url_for('index', error="Failed to add category"))

@app.route('/delete_category', methods=['POST'])
def delete_category():
    """Delete a category."""
    try:
        category = request.form.get('category')
        if not category:
            return redirect(url_for('index', error="No category specified"))
            
        categories, file_categories = load_categories()
        if category in categories:
            # Move files to uncategorized
            if category != "Uncategorized":
                categories.remove(category)
                for file_id, cat in file_categories.items():
                    if cat == category:
                        file_categories[file_id] = 'Uncategorized'
                save_categories(file_categories)
                
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error deleting category: {str(e)}")
        return redirect(url_for('index', error="Failed to delete category"))

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        flash('No file selected', 'warning')
        return redirect(url_for('index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'warning')
        return redirect(url_for('index'))
        
    if not allowed_file(file.filename):
        flash('File type not allowed', 'warning')
        return redirect(url_for('index'))
        
    try:
        # Save file locally first
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Upload to OpenAI Assistant
        if analyzer:
            file_info = analyzer.upload_file(file_path)
            if not file_info:
                raise Exception("Failed to upload file to OpenAI Assistant")
                
            # Get file metadata from OpenAI response
            file_id = file_info.id
            created_at = datetime.fromtimestamp(file_info.created_at).strftime("%Y-%m-%d %H:%M:%S")
            filename = file_info.filename  # Use the filename from OpenAI
            
            # Show success message
            flash(f'"{filename}" has been successfully added to the knowledge base', 'success')
        else:
            # In limited mode, generate a fake file ID
            file_id = str(len(os.listdir(app.config['UPLOAD_FOLDER'])))
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            flash('File uploaded in limited mode (not added to knowledge base)', 'info')
        
        # Categorize the file
        categories, file_categories = load_categories()
        category = categorize_file(filename, None)  # We're not using content for now
        if category not in categories:
            categories.append(category)
        file_categories[file_id] = category
        save_categories(file_categories)
        
        # Delete local file since it's now in OpenAI
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return redirect(url_for('index', category=category))
    except Exception as e:
        # Clean up local file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        error_msg = str(e)
        print(f"Error uploading file: {error_msg}")
        flash(f'Failed to upload file: {error_msg}', 'danger')
        return redirect(url_for('index'))

@app.route('/delete_file/<file_id>', methods=['POST'])
def delete_file(file_id):
    """Delete a file from both OpenAI Assistant and categories."""
    try:
        # Load categories
        categories, file_categories = load_categories()
        
        # Verify file exists in categories
        if file_id not in file_categories:
            return jsonify({
                'success': False,
                'error': 'File not found in categories'
            }), 404
            
        # Get current category
        category = file_categories[file_id]
        
        # Delete from OpenAI if connected
        if analyzer and not analyzer.limited_mode:
            success = analyzer.delete_file(file_id)
            if not success:
                return jsonify({
                    'success': False,
                    'error': 'Failed to delete file from OpenAI'
                }), 500
        
        # Remove from categories
        del file_categories[file_id]
        if not save_categories(file_categories):
            return jsonify({
                'success': False,
                'error': 'Failed to save categories'
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'File has been deleted from {category}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/debug/files')
def debug_files():
    try:
        files = analyzer.get_vector_store_files()
        return jsonify({
            'files': [{
                'filename': f['filename'],
                'id': f['id'],
                'created_at': f.get('created_at')
            } for f in files]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/search_files', methods=['POST'])
def search_files():
    """Search for files by filename."""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        
        if not query:
            return jsonify({'success': False, 'error': 'No search query provided'}), 400
            
        if not analyzer:
            return jsonify({'success': False, 'error': 'Search is not available'}), 500
            
        # Get all files and their categories
        all_files = analyzer.get_vector_store_files()
        _, file_categories = load_categories()
        
        # Search through files
        results = []
        for file in all_files:
            filename = file.get('filename', '').lower()
            if query in filename:
                # Get the category for this file
                category = get_file_category(file, file_categories)
                results.append({
                    'id': file.get('id'),
                    'filename': file.get('filename'),
                    'category': category,
                    'created_at': file.get('created_at')
                })
        
        # Sort results by relevance (exact matches first, then partial matches)
        results.sort(key=lambda x: (
            query == x['filename'].lower(),  # Exact matches first
            query in x['filename'].lower(),  # Partial matches second
            x['filename'].lower()           # Alphabetical within each group
        ), reverse=True)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "message": "BWE Assistant is running"}), 200

# Error handler for 404
@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html', error="Page not found"), 404

# Error handler for 500
@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', error="Internal server error"), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)
