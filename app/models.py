"""
SQLAlchemy ORM Models for Smart City Defect Detection System
"""
from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Citizen(UserMixin, db.Model):
    """Citizen model for community defect reporting."""
    __tablename__ = 'citizens'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    complaints = db.relationship('Complaint', backref='citizen', lazy=True, cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='citizen', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login identifier helper
    def get_id(self):
        return f"citizen_{self.id}"

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f"<Citizen {self.full_name} ({self.email})>"


class Admin(UserMixin, db.Model):
    """Admin model for municipal officers and system administrators."""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='Officer')  # SuperAdmin, DepartmentHead, Officer
    department = db.Column(db.String(100), default='Public Works')  # Public Works, Sanitation, Traffic
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin_{self.id}"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'department': self.department
        }

    def __repr__(self):
        return f"<Admin {self.username} [{self.role}]>"


class Worker(db.Model):
    """Municipal maintenance crew and field workers."""
    __tablename__ = 'workers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(100), nullable=False)  # Road Works, Sanitation, Traffic Signals
    zone = db.Column(db.String(50), default='Central Zone')
    status = db.Column(db.String(30), default='Available')  # Available, Busy, On-Leave
    active_tasks_count = db.Column(db.Integer, default=0)
    total_resolved_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assignments = db.relationship('WorkerAssignment', backref='worker', lazy=True)
    resolutions = db.relationship('Resolution', backref='worker', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'zone': self.zone,
            'status': self.status,
            'active_tasks_count': self.active_tasks_count,
            'total_resolved_count': self.total_resolved_count
        }

    def __repr__(self):
        return f"<Worker {self.name} - {self.department} ({self.status})>"


class Complaint(db.Model):
    """Core infrastructure defect complaint record."""
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey('citizens.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Defect Categorization
    reported_defect_type = db.Column(db.String(60), nullable=False)  # Pothole, Broken Traffic Sign, Garbage Dump, Cracked Road
    ai_detected_type = db.Column(db.String(60), nullable=True)
    ai_confidence = db.Column(db.Float, nullable=True)  # Range 0.0 - 1.0
    ai_defect_count = db.Column(db.Integer, default=1)
    ai_processing_status = db.Column(db.String(30), default='Pending')  # Pending, Processed, LowConfidence, Failed
    final_defect_type = db.Column(db.String(60), nullable=False)
    
    severity = db.Column(db.String(20), default='Medium')  # Low, Medium, High, Critical
    status = db.Column(db.String(30), default='Pending')  # Pending, AI Processing, Admin Review, Worker Assigned, In Progress, Resolved, Rejected
    
    # Geolocation Data
    latitude = db.Column(db.Float(precision=10), nullable=False)
    longitude = db.Column(db.Float(precision=10), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    zone = db.Column(db.String(50), default='Central Zone')
    
    # Image Paths
    original_image = db.Column(db.String(255), nullable=False)
    annotated_image = db.Column(db.String(255), nullable=True)
    
    # Administrative Meta
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = db.relationship('WorkerAssignment', backref='complaint', lazy=True, cascade='all, delete-orphan')
    resolution = db.relationship('Resolution', backref='complaint', uselist=False, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='complaint', uselist=False, cascade='all, delete-orphan')
    ai_logs = db.relationship('AIDetectionLog', backref='complaint', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        assigned_worker = self.assignments[-1].worker.name if self.assignments else 'Unassigned'
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'citizen_name': self.citizen.full_name if self.citizen else 'Unknown',
            'title': self.title,
            'description': self.description,
            'reported_defect_type': self.reported_defect_type,
            'ai_detected_type': self.ai_detected_type,
            'ai_confidence': round(self.ai_confidence * 100, 1) if self.ai_confidence else None,
            'final_defect_type': self.final_defect_type,
            'severity': self.severity,
            'status': self.status,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'zone': self.zone,
            'original_image': self.original_image,
            'annotated_image': self.annotated_image,
            'assigned_worker': assigned_worker,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f"<Complaint {self.ticket_number} - {self.final_defect_type} ({self.status})>"


class WorkerAssignment(db.Model):
    """Log of maintenance tasks assigned to municipal workers."""
    __tablename__ = 'worker_assignments'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    assigned_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default='Assigned')  # Assigned, In Progress, Completed, Reassigned
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'worker_id': self.worker_id,
            'worker_name': self.worker.name if self.worker else 'N/A',
            'assigned_at': self.assigned_at.strftime('%Y-%m-%d %H:%M'),
            'status': self.status,
            'notes': self.notes
        }


class Resolution(db.Model):
    """Detailed resolution proof and remarks when a defect is fixed."""
    __tablename__ = 'resolutions'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), unique=True, nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    resolution_notes = db.Column(db.Text, nullable=False)
    resolved_image = db.Column(db.String(255), nullable=True)
    material_used = db.Column(db.String(255), nullable=True)
    cost_estimate = db.Column(db.Float, default=0.0)
    resolved_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'worker_name': self.worker.name if self.worker else 'N/A',
            'resolution_notes': self.resolution_notes,
            'resolved_image': self.resolved_image,
            'material_used': self.material_used,
            'cost_estimate': self.cost_estimate,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M')
        }


class Feedback(db.Model):
    """Citizen satisfaction rating and comments on resolved complaints."""
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), unique=True, nullable=False)
    citizen_id = db.Column(db.Integer, db.ForeignKey('citizens.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5 Stars
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'citizen_id': self.citizen_id,
            'rating': self.rating,
            'comments': self.comments,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }


class AIDetectionLog(db.Model):
    """Audit trail for all AI inference results, confidence, and bounding boxes."""
    __tablename__ = 'ai_detection_logs'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    detected_classes = db.Column(db.Text, nullable=False)  # JSON or CSV
    max_confidence = db.Column(db.Float, nullable=False)
    processing_time_ms = db.Column(db.Float, default=0.0)
    bounding_boxes = db.Column(db.Text, nullable=True)  # JSON serialized coordinates
    model_version = db.Column(db.String(50), default='YOLOv8n-DefectDetector-v1.0')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
