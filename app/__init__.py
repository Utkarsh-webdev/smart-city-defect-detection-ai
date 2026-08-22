"""
Smart City Defect Detection System - Application Factory
"""
import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

from config import Config, config_by_name
from app.models import db, Citizen, Admin

login_manager = LoginManager()
migrate = Migrate()
bcrypt = Bcrypt()


def create_app(config_name=None):
    """
    Application factory for initializing the Flask app,
    extensions, blueprints, and global context handlers.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, Config))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.citizen_login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        """
        Dual user loader for polymorphic authentication (Citizen vs Admin).
        User ID strings are formatted as 'citizen_<id>' or 'admin_<id>'.
        """
        if not user_id:
            return None
        if user_id.startswith('citizen_'):
            try:
                c_id = int(user_id.split('_')[1])
                return Citizen.query.get(c_id)
            except (ValueError, IndexError):
                return None
        elif user_id.startswith('admin_'):
            try:
                a_id = int(user_id.split('_')[1])
                return Admin.query.get(a_id)
            except (ValueError, IndexError):
                return None
        return None

    # Ensure upload directories exist
    os.makedirs(app.config['ORIGINAL_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ANNOTATED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESOLVED_FOLDER'], exist_ok=True)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.citizen import citizen_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(citizen_bp, url_prefix='/citizen')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Root landing page route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Global context processors for templates
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'SmartDefect AI',
            'app_subtitle': 'AI-Powered Municipal Defect Detection & Workflow Automation',
            'current_year': 2026
        }

    # Custom HTTP error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_title="404 - Page Not Found",
                               error_msg="The page you requested does not exist or has been moved."), 404

    @app.errorhandler(413)
    def file_too_large(e):
        return render_template('base.html', error_title="413 - File Too Large",
                               error_msg="The uploaded file exceeds the 16MB maximum limit. Please upload a smaller image."), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_title="500 - Internal Server Error",
                               error_msg="An unexpected error occurred. The technical team has been notified."), 500

    return app
