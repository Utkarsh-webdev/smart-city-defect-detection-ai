"""
Municipal Administration and Department Operations Blueprint
Provides end-to-end defect triage, reclassification, worker dispatch,
maintenance lifecycle resolution, and analytical reporting.
"""
import io
import csv
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response, current_app
from flask_login import login_required, current_user

from app.models import db, Complaint, Worker, WorkerAssignment, Resolution, Feedback, Citizen
from app.routes import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Administrator Overview Dashboard with Real-Time KPIs and Map View."""
    total_complaints = Complaint.query.count()
    pending_review = Complaint.query.filter(Complaint.status.in_(['Pending', 'Admin Review', 'AI Processing'])).count()
    in_progress = Complaint.query.filter(Complaint.status.in_(['Worker Assigned', 'In Progress'])).count()
    resolved_count = Complaint.query.filter_by(status='Resolved').count()
    critical_count = Complaint.query.filter_by(severity='Critical').count()

    # Recent complaints for rapid triage
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(8).all()
    available_workers = Worker.query.filter_by(status='Available').all()

    # Defect Type Breakdown for summary pill
    defect_counts = {
        'Pothole': Complaint.query.filter_by(final_defect_type='Pothole').count(),
        'Broken Traffic Sign': Complaint.query.filter_by(final_defect_type='Broken Traffic Sign').count(),
        'Garbage Dump': Complaint.query.filter_by(final_defect_type='Garbage Dump').count(),
        'Cracked Road': Complaint.query.filter_by(final_defect_type='Cracked Road').count()
    }

    return render_template(
        'admin/dashboard.html',
        total_complaints=total_complaints,
        pending_review=pending_review,
        in_progress=in_progress,
        resolved_count=resolved_count,
        critical_count=critical_count,
        recent_complaints=recent_complaints,
        available_workers=available_workers,
        defect_counts=defect_counts
    )


@admin_bp.route('/complaints')
@login_required
@admin_required
def manage_complaints():
    """Comprehensive complaints table with multi-criteria filtering and pagination."""
    status_filter = request.args.get('status', 'all')
    defect_filter = request.args.get('defect_type', 'all')
    severity_filter = request.args.get('severity', 'all')
    zone_filter = request.args.get('zone', 'all')
    search_query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Complaint.query

    if status_filter != 'all':
        if status_filter == 'pending':
            query = query.filter(Complaint.status.in_(['Pending', 'Admin Review', 'AI Processing']))
        elif status_filter == 'in_progress':
            query = query.filter(Complaint.status.in_(['Worker Assigned', 'In Progress']))
        elif status_filter == 'resolved':
            query = query.filter_by(status='Resolved')
        elif status_filter == 'rejected':
            query = query.filter_by(status='Rejected')

    if defect_filter != 'all':
        query = query.filter_by(final_defect_type=defect_filter)

    if severity_filter != 'all':
        query = query.filter_by(severity=severity_filter)

    if zone_filter != 'all':
        query = query.filter_by(zone=zone_filter)

    if search_query:
        query = query.join(Citizen).filter(
            (Complaint.ticket_number.ilike(f'%{search_query}%')) |
            (Complaint.title.ilike(f'%{search_query}%')) |
            (Complaint.address.ilike(f'%{search_query}%')) |
            (Citizen.full_name.ilike(f'%{search_query}%'))
        )

    pagination = query.order_by(Complaint.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    all_workers = Worker.query.all()

    return render_template(
        'admin/manage_complaints.html',
        complaints=pagination.items,
        pagination=pagination,
        workers=all_workers,
        status_filter=status_filter,
        defect_filter=defect_filter,
        severity_filter=severity_filter,
        zone_filter=zone_filter,
        search_query=search_query
    )


@admin_bp.route('/complaint/<int:complaint_id>/reclassify', methods=['POST'])
@login_required
@admin_required
def reclassify_defect(complaint_id):
    """Allows municipal officer to override AI detection or update defect severity."""
    complaint = Complaint.query.get_or_404(complaint_id)
    
    new_defect = request.form.get('final_defect_type')
    new_severity = request.form.get('severity')
    admin_notes = request.form.get('admin_notes', '').strip()

    if new_defect:
        complaint.final_defect_type = new_defect
    if new_severity:
        complaint.severity = new_severity
    if admin_notes:
        complaint.admin_notes = admin_notes

    db.session.commit()
    flash(f"Complaint {complaint.ticket_number} updated: {complaint.final_defect_type} ({complaint.severity}).", 'success')
    return redirect(request.referrer or url_for('admin.manage_complaints'))


@admin_bp.route('/complaint/<int:complaint_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_worker(complaint_id):
    """Dispatches a municipal maintenance worker to address the defect."""
    complaint = Complaint.query.get_or_404(complaint_id)
    worker_id = request.form.get('worker_id', type=int)
    notes = request.form.get('notes', '').strip()

    worker = Worker.query.get(worker_id)
    if not worker:
        flash('Invalid worker selected.', 'danger')
        return redirect(request.referrer or url_for('admin.manage_complaints'))

    # Create assignment record
    assignment = WorkerAssignment(
        complaint_id=complaint.id,
        worker_id=worker.id,
        assigned_by_admin_id=current_user.id,
        notes=notes,
        status='Assigned'
    )

    # Update Complaint Status
    complaint.status = 'Worker Assigned'
    worker.active_tasks_count += 1
    if worker.active_tasks_count >= 3:
        worker.status = 'Busy'

    db.session.add(assignment)
    db.session.commit()

    flash(f"Worker '{worker.name}' successfully dispatched to {complaint.ticket_number}.", 'success')
    return redirect(request.referrer or url_for('admin.manage_complaints'))


@admin_bp.route('/complaint/<int:complaint_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_complaint(complaint_id):
    """Marks defect as resolved with repair remarks and optional proof."""
    complaint = Complaint.query.get_or_404(complaint_id)
    worker_id = request.form.get('worker_id', type=int)
    resolution_notes = request.form.get('resolution_notes', '').strip()
    material_used = request.form.get('material_used', '').strip()
    cost_estimate = request.form.get('cost_estimate', 0.0, type=float)

    if not resolution_notes:
        flash('Please describe the repair work performed.', 'warning')
        return redirect(request.referrer or url_for('admin.manage_complaints'))

    # If no worker provided, select the latest assigned or default
    if not worker_id:
        worker_id = complaint.assignments[-1].worker_id if complaint.assignments else None

    # Create Resolution record
    resolution = Resolution(
        complaint_id=complaint.id,
        worker_id=worker_id or 1,
        resolution_notes=resolution_notes,
        material_used=material_used,
        cost_estimate=cost_estimate
    )

    complaint.status = 'Resolved'

    # Update worker workload
    if worker_id:
        worker = Worker.query.get(worker_id)
        if worker:
            worker.active_tasks_count = max(0, worker.active_tasks_count - 1)
            worker.total_resolved_count += 1
            if worker.active_tasks_count < 3:
                worker.status = 'Available'

    db.session.add(resolution)
    db.session.commit()

    flash(f"Complaint {complaint.ticket_number} marked as Resolved.", 'success')
    return redirect(request.referrer or url_for('admin.manage_complaints'))


@admin_bp.route('/workers', methods=['GET', 'POST'])
@login_required
@admin_required
def workers():
    """Worker Management CRUD Route."""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            department = request.form.get('department', 'Road Works')
            zone = request.form.get('zone', 'Central Zone')

            if not name or not email or not phone:
                flash('Please fill in all required worker details.', 'warning')
            elif Worker.query.filter_by(email=email).first():
                flash('A worker with this email is already registered.', 'warning')
            else:
                new_worker = Worker(
                    name=name,
                    email=email,
                    phone=phone,
                    department=department,
                    zone=zone,
                    status='Available'
                )
                db.session.add(new_worker)
                db.session.commit()
                flash(f"Worker '{name}' added to {department}.", 'success')

        elif action == 'toggle_status':
            w_id = request.form.get('worker_id', type=int)
            worker = Worker.query.get_or_404(w_id)
            new_status = request.form.get('status', 'Available')
            worker.status = new_status
            db.session.commit()
            flash(f"Worker '{worker.name}' status changed to {new_status}.", 'info')

        return redirect(url_for('admin.workers'))

    all_workers = Worker.query.order_by(Worker.name.asc()).all()
    return render_template('admin/workers.html', workers=all_workers)


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Advanced Data Analytics, Defect Trends, and Export Options."""
    total = Complaint.query.count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0

    # Calculate average satisfaction rating
    feedbacks = Feedback.query.all()
    avg_rating = round(sum(f.rating for f in feedbacks) / len(feedbacks), 1) if feedbacks else 4.5

    # Top defects
    potholes = Complaint.query.filter_by(final_defect_type='Pothole').count()
    signs = Complaint.query.filter_by(final_defect_type='Broken Traffic Sign').count()
    garbage = Complaint.query.filter_by(final_defect_type='Garbage Dump').count()
    cracks = Complaint.query.filter_by(final_defect_type='Cracked Road').count()

    return render_template(
        'admin/analytics.html',
        total=total,
        resolved=resolved,
        resolution_rate=resolution_rate,
        avg_rating=avg_rating,
        potholes=potholes,
        signs=signs,
        garbage=garbage,
        cracks=cracks
    )


@admin_bp.route('/export/csv')
@login_required
@admin_required
def export_csv():
    """Exports all filtered complaints to CSV for municipal reporting."""
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV Header
    writer.writerow([
        'Ticket ID', 'Citizen Name', 'Reported Defect', 'AI Detected Defect',
        'AI Confidence (%)', 'Final Defect Type', 'Severity', 'Status',
        'Zone', 'Address', 'Latitude', 'Longitude', 'Created Date'
    ])

    for c in complaints:
        writer.writerow([
            c.ticket_number,
            c.citizen.full_name if c.citizen else 'Unknown',
            c.reported_defect_type,
            c.ai_detected_type or 'N/A',
            f"{int((c.ai_confidence or 0) * 100)}%",
            c.final_defect_type,
            c.severity,
            c.status,
            c.zone,
            c.address or 'N/A',
            c.latitude,
            c.longitude,
            c.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=smart_city_defects_{datetime.now().strftime('%Y%m%d')}.csv"}
    )
