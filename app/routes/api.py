"""
REST API Endpoints for AJAX interactions, Map GeoJSON Markers,
and Chart.js Data Feeds.
"""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models import db, Complaint, Worker, Feedback, AIDetectionLog

api_bp = Blueprint('api', __name__)


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Returns high-level metric counts for dynamic dashboard counters."""
    total = Complaint.query.count()
    pending = Complaint.query.filter(Complaint.status.in_(['Pending', 'Admin Review', 'AI Processing'])).count()
    in_progress = Complaint.query.filter(Complaint.status.in_(['Worker Assigned', 'In Progress'])).count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    critical = Complaint.query.filter_by(severity='Critical').count()

    return jsonify({
        'status': 'success',
        'data': {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'resolved': resolved,
            'critical': critical
        }
    })


@api_bp.route('/defects-map', methods=['GET'])
def get_defects_map():
    """
    Returns geo-tagged complaints formatted for Leaflet.js markers.
    Supports filtering by status or defect_type.
    """
    status = request.args.get('status')
    defect_type = request.args.get('defect_type')

    query = Complaint.query

    if status and status != 'all':
        query = query.filter_by(status=status)
    if defect_type and defect_type != 'all':
        query = query.filter_by(final_defect_type=defect_type)

    complaints = query.all()

    markers = []
    for c in complaints:
        markers.append({
            'id': c.id,
            'ticket': c.ticket_number,
            'title': c.title,
            'defect_type': c.final_defect_type,
            'severity': c.severity,
            'status': c.status,
            'lat': c.latitude,
            'lng': c.longitude,
            'address': c.address or 'Address not specified',
            'zone': c.zone,
            'confidence': int((c.ai_confidence or 0) * 100),
            'image_url': f"/static/uploads/annotated/{c.annotated_image}" if c.annotated_image else f"/static/uploads/original/{c.original_image}",
            'created_at': c.created_at.strftime('%b %d, %Y')
        })

    return jsonify({
        'status': 'success',
        'count': len(markers),
        'markers': markers
    })


@api_bp.route('/analytics-data', methods=['GET'])
def get_analytics_data():
    """
    Returns formatted data structures for Chart.js:
    - 7-Day intake trend
    - Defect category distribution
    - Severity breakdown
    - Zone distribution
    """
    # 1. 7-Day Intake Trend
    today = datetime.utcnow().date()
    date_labels = []
    intake_counts = []
    resolved_counts = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        date_str = day.strftime('%b %d')
        date_labels.append(date_str)

        start_dt = datetime.combine(day, datetime.min.time())
        end_dt = datetime.combine(day, datetime.max.time())

        day_intake = Complaint.query.filter(Complaint.created_at >= start_dt, Complaint.created_at <= end_dt).count()
        intake_counts.append(day_intake)

        day_resolved = Complaint.query.filter(Complaint.status == 'Resolved',
                                              Complaint.updated_at >= start_dt,
                                              Complaint.updated_at <= end_dt).count()
        resolved_counts.append(day_resolved)

    # 2. Defect Type Distribution
    categories = ['Pothole', 'Broken Traffic Sign', 'Garbage Dump', 'Cracked Road']
    cat_counts = [Complaint.query.filter_by(final_defect_type=cat).count() for cat in categories]

    # 3. Severity Breakdown
    severities = ['Low', 'Medium', 'High', 'Critical']
    sev_counts = [Complaint.query.filter_by(severity=s).count() for s in severities]

    # 4. Zone Breakdown
    zones = ['North Zone', 'South Zone', 'East Zone', 'West Zone', 'Central Zone']
    zone_counts = [Complaint.query.filter_by(zone=z).count() for z in zones]

    return jsonify({
        'trends': {
            'labels': date_labels,
            'intake': intake_counts,
            'resolved': resolved_counts
        },
        'categories': {
            'labels': categories,
            'counts': cat_counts
        },
        'severities': {
            'labels': severities,
            'counts': sev_counts
        },
        'zones': {
            'labels': zones,
            'counts': zone_counts
        }
    })


@api_bp.route('/complaint/<int:complaint_id>', methods=['GET'])
def get_complaint_detail(complaint_id):
    """Returns single complaint details as JSON for modal rendering."""
    complaint = Complaint.query.get_or_404(complaint_id)
    return jsonify({
        'status': 'success',
        'complaint': complaint.to_dict()
    })
