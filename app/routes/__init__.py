"""
Route blueprints and authentication helpers
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app.models import Admin, Citizen


def admin_required(f):
    """Decorator to restrict access to authenticated Admin accounts only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            flash('Administrator access required. Please log in with admin credentials.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def citizen_required(f):
    """Decorator to restrict access to authenticated Citizen accounts only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Citizen):
            flash('Please log in as a citizen to access this feature.', 'warning')
            return redirect(url_for('auth.citizen_login'))
        return f(*args, **kwargs)
    return decorated_function
