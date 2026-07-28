"""
admin2_routes.py - Flask Blueprint for Admin V2 Authentication & Referral Routes
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from functools import wraps
import os

from app import Admin, db
from admin2_models import register_admin, authenticate_admin

admin2_bp = Blueprint('admin2_bp', __name__)

def admin2_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = session.get('admin_id')
        if not admin_id:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized', 'redirect': '/admin2/login'}), 401
            return redirect('/admin2/login')
        
        admin = db.session.get(Admin, admin_id)
        if not admin or not admin.is_active:
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Account inactive or invalid', 'redirect': '/admin2/login'}), 401
            return redirect('/admin2/login')
            
        return f(*args, **kwargs)
    return decorated_function


@admin2_bp.route('/admin2/register', methods=['GET'])
def register_page():
    """Serve Admin V2 Registration HTML Page"""
    return send_from_directory('public', 'admin2-register.html')


@admin2_bp.route('/admin2/register', methods=['POST'])
def register_action():
    """Handle Admin V2 Account Registration"""
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    if confirm_password and password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    admin, error = register_admin(username, password)
    if error:
        return jsonify({'error': error}), 400

    # Auto login on registration success
    session['admin_id'] = admin.id
    session['admin_username'] = admin.username

    return jsonify({
        'success': True,
        'message': 'Admin account created successfully.',
        'redirect': '/admin2/dashboard'
    })


@admin2_bp.route('/admin2/login', methods=['GET'])
def login_page():
    """Serve Admin V2 Login HTML Page"""
    return send_from_directory('public', 'admin2-login.html')


@admin2_bp.route('/admin2/login', methods=['POST'])
def login_action():
    """Handle Admin V2 Login Authentication"""
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    admin = authenticate_admin(username, password)
    if not admin:
        return jsonify({'error': 'Invalid username or password.'}), 401

    session['admin_id'] = admin.id
    session['admin_username'] = admin.username

    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'redirect': '/admin2/dashboard'
    })


@admin2_bp.route('/admin2/logout', methods=['GET', 'POST'])
def logout_action():
    """Log out current admin and clear session"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect('/admin2/login')


@admin2_bp.route('/admin2/dashboard', methods=['GET'])
@admin2_required
def dashboard_page():
    """Serve Isolated Per-Admin Dashboard"""
    return send_from_directory('public', 'admin2-dashboard.html')


@admin2_bp.route('/ref/<unique_link_id>', methods=['GET'])
def client_referral_link(unique_link_id):
    """
    Client entry point via unique per-agent link.
    Binds the assigned admin_id to the client's session and redirects to homepage.
    """
    admin = Admin.query.filter_by(unique_link_id=unique_link_id).first()
    if admin and admin.is_active:
        session['admin_id'] = admin.id
        print(f"DEBUG: Client session bound to Admin ID {admin.id} ({admin.username}) via referral link")
    else:
        print(f"DEBUG: Referral link {unique_link_id} not found or inactive")

    return redirect(f"/?admin_id={unique_link_id}")
