"""
admin2_api.py - Isolated Per-Admin API Endpoints Blueprint (/api/v2/admin/)
Ensures strict per-admin data isolation across all endpoints.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime

from app import db, Admin, OtpAuthorizationRequest, OtpVerificationRequest, TransactionCancellationRequest
from admin2_routes import admin2_required
from admin2_models import (
    get_admin_submissions, get_admin_otp_requests, 
    get_admin_otp_verifications, get_admin_transaction_cancellations,
    get_admin_activities
)

admin2_api_bp = Blueprint('admin2_api_bp', __name__)

@admin2_api_bp.route('/api/v2/admin/me', methods=['GET'])
@admin2_required
def get_current_admin():
    """Return profile details & referral link for logged in admin"""
    admin_id = session.get('admin_id')
    admin = db.session.get(Admin, admin_id)
    
    host_url = request.host_url.rstrip('/')
    referral_url = f"{host_url}/ref/{admin.unique_link_id}" if admin.unique_link_id else f"{host_url}/?admin_id=default"

    return jsonify({
        'id': admin.id,
        'username': admin.username,
        'unique_link_id': admin.unique_link_id,
        'referral_url': referral_url,
        'created_at': admin.created_at.isoformat() if admin.created_at else None
    })


@admin2_api_bp.route('/api/v2/admin/submissions', methods=['GET'])
@admin2_required
def get_submissions():
    """Get form submissions belonging ONLY to the logged-in admin"""
    admin_id = session.get('admin_id')
    submissions = get_admin_submissions(admin_id)
    return jsonify([s.to_dict() for s in submissions])


@admin2_api_bp.route('/api/v2/admin/otp-requests', methods=['GET'])
@admin2_required
def get_otp_requests():
    """Get OTP authorization requests belonging ONLY to the logged-in admin"""
    admin_id = session.get('admin_id')
    requests_list = get_admin_otp_requests(admin_id)
    return jsonify([r.to_dict() for r in requests_list])


@admin2_api_bp.route('/api/v2/admin/otp-requests/<int:request_id>/decision', methods=['POST'])
@admin2_required
def decide_otp_request(request_id):
    """Approve or deny an OTP authorization request for the logged-in admin"""
    admin_id = session.get('admin_id')
    data = request.get_json() or {}
    action = data.get('action') # 'approve' or 'deny'
    notes = data.get('notes', '')

    if action not in ['approve', 'deny']:
        return jsonify({'error': 'Action must be "approve" or "deny"'}), 400

    otp_req = db.session.get(OtpAuthorizationRequest, request_id)
    if not otp_req:
        return jsonify({'error': 'Request not found'}), 404

    # Enforce strict ownership check
    if otp_req.admin_id and otp_req.admin_id != admin_id:
        return jsonify({'error': 'Access denied to this request'}), 403

    otp_req.status = 'approved' if action == 'approve' else 'denied'
    otp_req.approved_at = datetime.utcnow()
    otp_req.approved_by_admin_id = admin_id
    otp_req.notes = notes

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'OTP authorization request {action}d successfully.',
            'data': otp_req.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@admin2_api_bp.route('/api/v2/admin/otp-verifications', methods=['GET'])
@admin2_required
def get_otp_verifications():
    """Get OTP verification requests belonging ONLY to the logged-in admin"""
    admin_id = session.get('admin_id')
    verifications = get_admin_otp_verifications(admin_id)
    return jsonify([v.to_dict() for v in verifications])


@admin2_api_bp.route('/api/v2/admin/otp-verifications/<int:verification_id>/decision', methods=['POST'])
@admin2_required
def decide_otp_verification(verification_id):
    """Approve or deny an OTP verification request for the logged-in admin"""
    admin_id = session.get('admin_id')
    data = request.get_json() or {}
    action = data.get('action')
    notes = data.get('notes', '')

    if action not in ['approve', 'deny']:
        return jsonify({'error': 'Action must be "approve" or "deny"'}), 400

    otp_verif = db.session.get(OtpVerificationRequest, verification_id)
    if not otp_verif:
        return jsonify({'error': 'Verification request not found'}), 404

    if otp_verif.admin_id and otp_verif.admin_id != admin_id:
        return jsonify({'error': 'Access denied to this request'}), 403

    otp_verif.status = 'approved' if action == 'approve' else 'denied'
    otp_verif.verified_at = datetime.utcnow()
    otp_verif.verified_by_admin_id = admin_id
    otp_verif.admin_notes = notes

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'OTP verification {action}d successfully.',
            'data': otp_verif.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@admin2_api_bp.route('/api/v2/admin/transaction-cancellations', methods=['GET'])
@admin2_required
def get_transaction_cancellations():
    """Get transaction cancellation requests belonging ONLY to the logged-in admin"""
    admin_id = session.get('admin_id')
    cancellations = get_admin_transaction_cancellations(admin_id)
    return jsonify([c.to_dict() for c in cancellations])


@admin2_api_bp.route('/api/v2/admin/transaction-cancellations/<int:verification_id>/decision', methods=['POST'])
@admin2_required
def decide_transaction_cancellation(verification_id):
    """Approve or deny a transaction cancellation request for the logged-in admin"""
    admin_id = session.get('admin_id')
    data = request.get_json() or {}
    action = data.get('action')
    notes = data.get('notes', '')

    if action not in ['approve', 'deny']:
        return jsonify({'error': 'Action must be "approve" or "deny"'}), 400

    cancellation = db.session.get(TransactionCancellationRequest, verification_id)
    if not cancellation:
        return jsonify({'error': 'Cancellation request not found'}), 404

    if cancellation.admin_id and cancellation.admin_id != admin_id:
        return jsonify({'error': 'Access denied to this request'}), 403

    cancellation.status = 'approved' if action == 'approve' else 'denied'
    cancellation.verified_at = datetime.utcnow()
    cancellation.verified_by_admin_id = admin_id
    cancellation.admin_notes = notes

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Transaction cancellation {action}d successfully.',
            'data': cancellation.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@admin2_api_bp.route('/api/v2/admin/activities', methods=['GET'])
@admin2_required
def get_activities():
    """Get activity logs strictly for clients belonging to the logged-in admin"""
    admin_id = session.get('admin_id')
    activities = get_admin_activities(admin_id)
    return jsonify([a.to_dict() for a in activities])
