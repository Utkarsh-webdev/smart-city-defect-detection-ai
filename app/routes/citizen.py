"""
Citizen Portal Routes
Handles complaint ingestion, GPS auto-capture, AI analysis trigger,
status tracking timeline, and resolution feedback.
"""
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.models import db, Complaint, AIDetectionLog, Feedback
from app.routes import citizen_required
from app.ai.detector import DefectDetector

citizen_bp = Blueprint('citizen', __name__)


def allowed_file(filename):
    """Checks if uploaded file has a permissible image extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def generate_ticket_number():
    """Generates an enterprise tracking ticket ID (e.g. SCD-202608-8421)."""
    now = datetime.utcnow()
    unique_suffix = str(uuid.uuid4().int)[:4]
    return f"SCD-{now.strftime('%Y%m')}-{unique_suffix}"


@citizen_bp.route('/dashboard')
@login_required
@citizen_required
def dashboard():
    """Citizen central dashboard with recent activity and overview metrics."""
    complaints = Complaint.query.filter_by(citizen_id=current_user.id)\
        .order_by(Complaint.created_at.desc()).limit(10).all()

    total_count = Complaint.query.filter_by(citizen_id=current_user.id).count()
    pending_count = Complaint.query.filter_by(citizen_id=current_user.id)\
        .filter(Complaint.status.in_(['Pending', 'AI Processing', 'Admin Review'])).count()
    in_progress_count = Complaint.query.filter_by(citizen_id=current_user.id)\
        .filter(Complaint.status.in_(['Worker Assigned', 'In Progress'])).count()
    resolved_count = Complaint.query.filter_by(citizen_id=current_user.id)\
        .filter_by(status='Resolved').count()

    return render_template(
        'citizen/dashboard.html',
        complaints=complaints,
        total_count=total_count,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count
    )


@citizen_bp.route('/complaints/new', methods=['GET', 'POST'])
@login_required
@citizen_required
def upload_complaint():
    """Defect reporting route with image upload, GPS capture, and AI inference."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        reported_defect = request.form.get('defect_type', 'Pothole')
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        address = request.form.get('address', '').strip()
        zone = request.form.get('zone', 'Central Zone')

        # Validation
        if not title:
            flash('Please provide a short title for the complaint.', 'warning')
            return render_template('citizen/upload_complaint.html')

        if 'defect_image' not in request.files:
            flash('Defect image is required for AI inspection.', 'danger')
            return render_template('citizen/upload_complaint.html')

        file = request.files['defect_image']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Please upload a valid image file (JPG, PNG, WEBP).', 'warning')
            return render_template('citizen/upload_complaint.html')

        # Geolocation fallback defaults (e.g. City Center) if browser denied GPS
        try:
            lat = float(latitude) if latitude else current_app.config['MAP_DEFAULT_LAT']
            lng = float(longitude) if longitude else current_app.config['MAP_DEFAULT_LNG']
        except ValueError:
            lat = current_app.config['MAP_DEFAULT_LAT']
            lng = current_app.config['MAP_DEFAULT_LNG']

        # Save Original Image
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}_{int(datetime.utcnow().timestamp())}.{ext}"
        original_filepath = os.path.join(current_app.config['ORIGINAL_FOLDER'], unique_filename)
        annotated_filename = f"annotated_{unique_filename}"
        annotated_filepath = os.path.join(current_app.config['ANNOTATED_FOLDER'], annotated_filename)

        file.save(original_filepath)

        # Trigger YOLOv8 Defect Detection Pipeline
        detector = DefectDetector(confidence_threshold=current_app.config['AI_CONFIDENCE_THRESHOLD'])
        ai_result = detector.detect(
            image_path=original_filepath,
            output_annotated_path=annotated_filepath,
            reported_hint=reported_defect
        )

        ticket = generate_ticket_number()

        # Create Complaint record
        complaint = Complaint(
            ticket_number=ticket,
            citizen_id=current_user.id,
            title=title,
            description=description,
            reported_defect_type=reported_defect,
            ai_detected_type=ai_result['primary_defect'],
            ai_confidence=ai_result['confidence'],
            ai_defect_count=ai_result['defect_count'],
            ai_processing_status=ai_result['ai_status'],
            final_defect_type=ai_result['primary_defect'] if ai_result['confidence'] >= current_app.config['AI_CONFIDENCE_THRESHOLD'] else reported_defect,
            severity=ai_result['severity'],
            status='Admin Review',  # AI processed; ready for municipal triage
            latitude=lat,
            longitude=lng,
            address=address or 'Location coordinates captured via GPS',
            zone=zone,
            original_image=unique_filename,
            annotated_image=annotated_filename
        )

        db.session.add(complaint)
        db.session.flush()  # Obtain complaint.id

        # Create AI Detection Log audit record
        ai_log = AIDetectionLog(
            complaint_id=complaint.id,
            detected_classes=str([d['class_name'] for d in ai_result['detections']]),
            max_confidence=ai_result['confidence'],
            processing_time_ms=ai_result['processing_time_ms'],
            bounding_boxes=str(ai_result['detections']),
            model_version='YOLOv8-SmartCity-v1.0'
        )
        db.session.add(ai_log)
        db.session.commit()

        confidence_pct = int(ai_result['confidence'] * 100)
        flash(
            f"Complaint registered ({ticket})! AI detected: '{ai_result['primary_defect']}' "
            f"with {confidence_pct}% confidence [Severity: {ai_result['severity']}].",
            'success'
        )
        return redirect(url_for('citizen.complaint_status', ticket_number=ticket))

    return render_template('citizen/upload_complaint.html')


@citizen_bp.route('/complaint/<string:ticket_number>')
@login_required
@citizen_required
def complaint_status(ticket_number):
    """Detailed status tracking and lifecycle timeline for a specific complaint."""
    complaint = Complaint.query.filter_by(ticket_number=ticket_number, citizen_id=current_user.id).first_or_404()
    return render_template('citizen/complaint_status.html', complaint=complaint)


@citizen_bp.route('/complaints/history')
@login_required
@citizen_required
def complaint_history():
    """Full filterable history of citizen reported issues."""
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    query = Complaint.query.filter_by(citizen_id=current_user.id)

    if status_filter == 'pending':
        query = query.filter(Complaint.status.in_(['Pending', 'AI Processing', 'Admin Review']))
    elif status_filter == 'in_progress':
        query = query.filter(Complaint.status.in_(['Worker Assigned', 'In Progress']))
    elif status_filter == 'resolved':
        query = query.filter_by(status='Resolved')

    pagination = query.order_by(Complaint.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    return render_template(
        'citizen/history.html',
        complaints=pagination.items,
        pagination=pagination,
        current_status=status_filter
    )


@citizen_bp.route('/complaint/<int:complaint_id>/feedback', methods=['POST'])
@login_required
@citizen_required
def submit_feedback(complaint_id):
    """Submit citizen satisfaction rating and comments on resolved issues."""
    complaint = Complaint.query.filter_by(id=complaint_id, citizen_id=current_user.id).first_or_404()

    if complaint.status != 'Resolved':
        flash('Feedback can only be submitted for resolved complaints.', 'warning')
        return redirect(url_for('citizen.complaint_status', ticket_number=complaint.ticket_number))

    rating = request.form.get('rating', type=int)
    comments = request.form.get('comments', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating between 1 and 5 stars.', 'warning')
        return redirect(url_for('citizen.complaint_status', ticket_number=complaint.ticket_number))

    existing_feedback = Feedback.query.filter_by(complaint_id=complaint.id).first()
    if existing_feedback:
        existing_feedback.rating = rating
        existing_feedback.comments = comments
    else:
        new_feedback = Feedback(
            complaint_id=complaint.id,
            citizen_id=current_user.id,
            rating=rating,
            comments=comments
        )
        db.session.add(new_feedback)

    db.session.commit()
    flash('Thank you! Your feedback has been submitted successfully.', 'success')
    return redirect(url_for('citizen.complaint_status', ticket_number=complaint.ticket_number))
