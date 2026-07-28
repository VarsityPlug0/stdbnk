"""
admin2_models.py - Multi-Admin Model Helpers & Isolated Data Access Layer
Extends Admin authentication and provides strict per-admin data isolation queries.
"""

import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Import database instance and models from existing app
from app import (
    db, Admin, Submission, OtpAuthorizationRequest, 
    OtpVerificationRequest, TransactionCancellationRequest, UserActivity
)

def register_admin(username, password):
    """
    Registers a new admin user with a hashed password and unique referral link ID.
    Returns (admin_instance, None) on success, or (None, error_message) on failure.
    """
    username = username.strip()
    if not username or not password:
        return None, "Username and password are required."
    
    existing = Admin.query.filter_by(username=username).first()
    if existing:
        return None, "Username already exists."
    
    hashed_pwd = generate_password_hash(password, method='pbkdf2:sha256')
    unique_link = str(uuid.uuid4())
    
    new_admin = Admin(
        username=username,
        password_hash=hashed_pwd,
        unique_link_id=unique_link,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    try:
        db.session.add(new_admin)
        db.session.commit()
        return new_admin, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def authenticate_admin(username, password):
    """
    Authenticates admin credentials against stored hash.
    Returns Admin instance if valid, else None.
    """
    admin = Admin.query.filter_by(username=username).first()
    if not admin or not admin.is_active:
        return None
    
    # Try werkzeug check_password_hash
    if check_password_hash(admin.password_hash, password):
        return admin
    
    # Fallback check if plain password match for legacy seeds
    if admin.password_hash == password:
        # Upgrade to hash
        admin.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        db.session.commit()
        return admin
        
    return None


def get_admin_submissions(admin_id):
    """Fetch submissions belonging strictly to the given admin_id."""
    return Submission.query.filter_by(admin_id=admin_id).order_by(Submission.submitted_at.desc()).all()


def get_admin_otp_requests(admin_id):
    """Fetch OTP authorization requests belonging strictly to the given admin_id."""
    return OtpAuthorizationRequest.query.filter_by(admin_id=admin_id).order_by(OtpAuthorizationRequest.requested_at.desc()).all()


def get_admin_otp_verifications(admin_id):
    """Fetch OTP verification requests belonging strictly to the given admin_id."""
    return OtpVerificationRequest.query.filter_by(admin_id=admin_id).order_by(OtpVerificationRequest.submitted_at.desc()).all()


def get_admin_transaction_cancellations(admin_id):
    """Fetch transaction cancellation requests belonging strictly to the given admin_id."""
    return TransactionCancellationRequest.query.filter_by(admin_id=admin_id).order_by(TransactionCancellationRequest.submitted_at.desc()).all()


def get_admin_activities(admin_id):
    """Fetch activity logs associated with clients belonging to the given admin_id."""
    # Find all client session user_identifiers from submissions for this admin
    admin_submissions = Submission.query.filter_by(admin_id=admin_id).all()
    submission_ids = [s.id for s in admin_submissions]
    
    # Also find user_identifiers from OTP requests for this admin
    otp_reqs = OtpAuthorizationRequest.query.filter_by(admin_id=admin_id).all()
    user_identifiers = set(r.user_identifier for r in otp_reqs if r.user_identifier)
    
    # Match user activities containing admin_id or matching user_identifiers
    activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).limit(200).all()
    
    filtered_activities = []
    for act in activities:
        # Check if additional_data contains admin_id
        if act.additional_data and f'"admin_id": {admin_id}' in act.additional_data:
            filtered_activities.append(act)
        elif act.user_identifier in user_identifiers:
            filtered_activities.append(act)
            
    return filtered_activities
