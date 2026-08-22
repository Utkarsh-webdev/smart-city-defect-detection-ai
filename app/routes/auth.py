"""
Authentication and User Session Management Routes
Supports polymorphic authentication for Citizens and Municipal Admins.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Citizen, Admin

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def citizen_register():
    """Citizen Registration Route."""
    if current_user.is_authenticated:
        if isinstance(current_user, Citizen):
            return redirect(url_for('citizen.dashboard'))
        elif isinstance(current_user, Admin):
            return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        address = request.form.get('address', '').strip()

        # Validation
        if not full_name or not email or not phone or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('citizen/register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please verify your input.', 'danger')
            return render_template('citizen/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters in length.', 'warning')
            return render_template('citizen/register.html')

        # Check existing citizen or admin email
        if Citizen.query.filter_by(email=email).first() or Admin.query.filter_by(email=email).first():
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.citizen_login'))

        # Create new citizen account
        new_citizen = Citizen(
            full_name=full_name,
            email=email,
            phone=phone,
            address=address
        )
        new_citizen.set_password(password)

        try:
            db.session.add(new_citizen)
            db.session.commit()
            flash('Registration successful! You can now log in to report defects.', 'success')
            return redirect(url_for('auth.citizen_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')

    return render_template('citizen/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def citizen_login():
    """Citizen Login Route."""
    if current_user.is_authenticated:
        if isinstance(current_user, Citizen):
            return redirect(url_for('citizen.dashboard'))
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        citizen = Citizen.query.filter_by(email=email).first()
        if citizen and citizen.check_password(password):
            login_user(citizen, remember=remember)
            flash(f'Welcome back, {citizen.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('citizen.dashboard'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')

    return render_template('citizen/login.html')


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Municipal Administrator / Officer Login Route."""
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):
            return redirect(url_for('admin.dashboard'))
        logout_user()  # Switch session if citizen was logged in

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        admin = Admin.query.filter((Admin.email == email) | (Admin.username == email)).first()
        if admin and admin.check_password(password):
            login_user(admin, remember=remember)
            flash(f'Administrative access granted. Welcome, {admin.username} ({admin.role}).', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid administrator credentials. Access denied.', 'danger')

    return render_template('admin/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Universal Logout Route."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User Profile management."""
    if request.method == 'POST':
        if isinstance(current_user, Citizen):
            current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
            current_user.phone = request.form.get('phone', current_user.phone).strip()
            current_user.address = request.form.get('address', current_user.address).strip()
            
            new_pwd = request.form.get('new_password', '').strip()
            if new_pwd:
                current_user.set_password(new_pwd)
                
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
    return render_template('citizen/profile.html', user=current_user)
