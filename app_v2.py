"""
app_v2.py - Flask Application Entry Point with Multi-Admin V2 Blueprints Registered
Imports the original Flask app instance from app.py without altering app.py.
"""

from app import app, db
from admin2_routes import admin2_bp
from admin2_api import admin2_api_bp

# Register multi-admin V2 blueprints cleanly onto original Flask app
app.register_blueprint(admin2_bp)
app.register_blueprint(admin2_api_bp)

# Ensure database tables exist for new session/admin tracking
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Run server
    app.run(host='0.0.0.0', port=5000, debug=True)
