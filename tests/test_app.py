"""
Comprehensive Automated Test Suite for Smart City Defect Detection System
Tests Authentication, Role-based Access, Citizen Ingestion, AI Detection Pipeline,
Admin Management, Worker Dispatch, Resolution Lifecycle, APIs, and CSV Export.
"""
import os
import sys

# Ensure YOLO_CONFIG_DIR is set to project directory before any ultralytics imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['YOLO_CONFIG_DIR'] = os.path.join(BASE_DIR, '.yolo')
sys.path.insert(0, BASE_DIR)

import io
import unittest
from PIL import Image, ImageDraw

from app import create_app
from app.models import db, Citizen, Admin, Worker, Complaint, WorkerAssignment, Resolution, Feedback, AIDetectionLog
from app.ai.detector import DefectDetector


def create_test_image_bytes():
    """Generates an in-memory test image with a synthetic defect."""
    img = Image.new('RGB', (320, 240), color=(60, 60, 60))
    draw = ImageDraw.Draw(img)
    draw.line([(160, 0), (160, 240)], fill=(220, 180, 20), width=4)
    draw.ellipse([(100, 100), (220, 160)], fill=(20, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf


class SmartCitySystemTestCase(unittest.TestCase):
    """Primary Test Case using TestingConfig (in-memory SQLite)."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

        # Seed an admin
        self.admin = Admin(
            username='admin_test',
            email='admin@test.com',
            role='SuperAdmin',
            department='PWD'
        )
        self.admin.set_password('Admin@123')
        db.session.add(self.admin)

        # Seed a citizen
        self.citizen = Citizen(
            full_name='Citizen Tester',
            email='citizen@test.com',
            phone='9876543210',
            address='123 Test Street'
        )
        self.citizen.set_password('Citizen@123')
        db.session.add(self.citizen)

        # Seed a worker
        self.worker = Worker(
            name='Worker John',
            email='john@worker.com',
            phone='9998887776',
            department='Road Works',
            zone='Central Zone',
            status='Available'
        )
        db.session.add(self.worker)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =========================================================================
    # 1. AUTHENTICATION & ACCESS CONTROL TESTS
    # =========================================================================

    def test_citizen_registration_success(self):
        response = self.client.post('/auth/register', data={
            'full_name': 'New Citizen',
            'email': 'newcitizen@test.com',
            'phone': '9123456789',
            'address': 'Green Park',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        new_user = Citizen.query.filter_by(email='newcitizen@test.com').first()
        self.assertIsNotNone(new_user)
        self.assertTrue(new_user.check_password('Password@123'))

    def test_citizen_registration_mismatched_password(self):
        response = self.client.post('/auth/register', data={
            'full_name': 'New Citizen',
            'email': 'mismatch@test.com',
            'phone': '9123456789',
            'address': 'Green Park',
            'password': 'Password@123',
            'confirm_password': 'DifferentPassword'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', response.data)
        self.assertIsNone(Citizen.query.filter_by(email='mismatch@test.com').first())

    def test_citizen_registration_duplicate_email(self):
        response = self.client.post('/auth/register', data={
            'full_name': 'Duplicate',
            'email': 'citizen@test.com',
            'phone': '9123456789',
            'address': 'Test',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertIn(b'already exists', response.data)

    def test_citizen_login_and_logout(self):
        response = self.client.post('/auth/login', data={
            'email': 'citizen@test.com',
            'password': 'Citizen@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Citizen Portal', response.data)

        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'logged out successfully', response.data)

    def test_citizen_login_invalid_password(self):
        response = self.client.post('/auth/login', data={
            'email': 'citizen@test.com',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)

    def test_admin_login_and_logout(self):
        response = self.client.post('/auth/admin/login', data={
            'email': 'admin@test.com',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Municipal Command Center', response.data)

        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_role_based_access_restriction(self):
        # Unauthenticated access to admin dashboard redirects to admin login
        response = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/admin/login', response.headers['Location'])

        # Log in as citizen and try to access admin dashboard -> redirected
        self.client.post('/auth/login', data={'email': 'citizen@test.com', 'password': 'Citizen@123'})
        response = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/admin/login', response.headers['Location'])

    # =========================================================================
    # 2. CITIZEN COMPLAINT INGESTION & LIFECYCLE TESTS
    # =========================================================================

    def test_upload_complaint_with_image_and_gps(self):
        self.client.post('/auth/login', data={'email': 'citizen@test.com', 'password': 'Citizen@123'})

        image_data = create_test_image_bytes()
        response = self.client.post('/citizen/complaints/new', data={
            'title': 'Test Pothole on 5th Street',
            'description': 'Dangerous deep depression near crossing',
            'defect_type': 'Pothole',
            'latitude': '28.6139',
            'longitude': '77.2090',
            'address': '5th Street Crossing, Central Zone',
            'zone': 'Central Zone',
            'defect_image': (image_data, 'test_pothole.jpg')
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Complaint registered', response.data)

        complaint = Complaint.query.filter_by(citizen_id=self.citizen.id).first()
        self.assertIsNotNone(complaint)
        self.assertEqual(complaint.title, 'Test Pothole on 5th Street')
        self.assertIn(complaint.status, ['Admin Review', 'Pending'])
        self.assertIsNotNone(complaint.original_image)
        self.assertIsNotNone(complaint.annotated_image)
        self.assertIsNotNone(complaint.ai_confidence)
        self.assertGreater(complaint.ai_confidence, 0.0)

        ai_log = AIDetectionLog.query.filter_by(complaint_id=complaint.id).first()
        self.assertIsNotNone(ai_log)

    def test_complaint_status_page(self):
        c = Complaint(
            ticket_number='SCD-TEST-0001',
            citizen_id=self.citizen.id,
            title='Sample Defect',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='High',
            status='Admin Review',
            latitude=28.61,
            longitude=77.20,
            original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        self.client.post('/auth/login', data={'email': 'citizen@test.com', 'password': 'Citizen@123'})
        response = self.client.get(f'/citizen/complaint/{c.ticket_number}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SCD-TEST-0001', response.data)
        self.assertIn(b'Sample Defect', response.data)

    def test_complaint_history_filter(self):
        c1 = Complaint(
            ticket_number='SCD-TEST-0002',
            citizen_id=self.citizen.id,
            title='Resolved Defect',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='Medium',
            status='Resolved',
            latitude=28.61, longitude=77.20, original_image='test1.jpg'
        )
        c2 = Complaint(
            ticket_number='SCD-TEST-0003',
            citizen_id=self.citizen.id,
            title='Pending Defect',
            reported_defect_type='Garbage Dump',
            final_defect_type='Garbage Dump',
            severity='Low',
            status='Admin Review',
            latitude=28.62, longitude=77.21, original_image='test2.jpg'
        )
        db.session.add_all([c1, c2])
        db.session.commit()

        self.client.post('/auth/login', data={'email': 'citizen@test.com', 'password': 'Citizen@123'})
        
        res = self.client.get('/citizen/complaints/history?status=resolved')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Resolved Defect', res.data)
        self.assertNotIn(b'Pending Defect', res.data)

    def test_feedback_submission(self):
        c = Complaint(
            ticket_number='SCD-TEST-0004',
            citizen_id=self.citizen.id,
            title='Resolved for Feedback',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='High',
            status='Resolved',
            latitude=28.61, longitude=77.20, original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        self.client.post('/auth/login', data={'email': 'citizen@test.com', 'password': 'Citizen@123'})
        response = self.client.post(f'/citizen/complaint/{c.id}/feedback', data={
            'rating': '5',
            'comments': 'Great job fixing this quickly!'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        feedback = Feedback.query.filter_by(complaint_id=c.id).first()
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.comments, 'Great job fixing this quickly!')

    def test_feedback_rejected_for_unresolved_complaint(self):
        c = Complaint(
            ticket_number='SCD-TEST-0005',
            citizen_id=self.citizen.id,
            title='In Progress Defect',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            status='Worker Assigned',
            latitude=28.61, longitude=77.20, original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        self.client.post('/auth/login', data={'email': 'citizen@test.com', 'password': 'Citizen@123'})
        response = self.client.post(f'/citizen/complaint/{c.id}/feedback', data={
            'rating': '5'
        }, follow_redirects=True)
        self.assertIn(b'Feedback can only be submitted for resolved complaints', response.data)

    # =========================================================================
    # 3. ADMIN WORKFLOWS & WORKER DISPATCH TESTS
    # =========================================================================

    def test_admin_dashboard_render(self):
        self.client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'Admin@123'})
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Municipal Command Center', response.data)
        self.assertIn(b'TOTAL DEFECTS', response.data)

    def test_admin_reclassify_defect(self):
        c = Complaint(
            ticket_number='SCD-TEST-0006',
            citizen_id=self.citizen.id,
            title='Misclassified Defect',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='Low',
            status='Admin Review',
            latitude=28.61, longitude=77.20, original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        self.client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'Admin@123'})
        response = self.client.post(f'/admin/complaint/{c.id}/reclassify', data={
            'final_defect_type': 'Cracked Road',
            'severity': 'Critical',
            'admin_notes': 'Verified on site: large longitudinal crack.'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        updated = db.session.get(Complaint, c.id)
        self.assertEqual(updated.final_defect_type, 'Cracked Road')
        self.assertEqual(updated.severity, 'Critical')
        self.assertEqual(updated.admin_notes, 'Verified on site: large longitudinal crack.')

    def test_admin_assign_and_resolve_worker(self):
        c = Complaint(
            ticket_number='SCD-TEST-0007',
            citizen_id=self.citizen.id,
            title='Defect for Worker',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='High',
            status='Admin Review',
            latitude=28.61, longitude=77.20, original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        self.client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'Admin@123'})
        
        # 1. Assign Worker
        res_assign = self.client.post(f'/admin/complaint/{c.id}/assign', data={
            'worker_id': str(self.worker.id),
            'notes': 'Urgent repair needed.'
        }, follow_redirects=True)
        self.assertEqual(res_assign.status_code, 200)

        c_assigned = db.session.get(Complaint, c.id)
        self.assertEqual(c_assigned.status, 'Worker Assigned')
        w = db.session.get(Worker, self.worker.id)
        self.assertEqual(w.active_tasks_count, 1)

        # 2. Resolve Complaint
        res_resolve = self.client.post(f'/admin/complaint/{c.id}/resolve', data={
            'worker_id': str(self.worker.id),
            'resolution_notes': 'Patched with bitumen cold mix.',
            'material_used': 'Cold mix bitumen (50kg)',
            'cost_estimate': '2500.00'
        }, follow_redirects=True)
        self.assertEqual(res_resolve.status_code, 200)

        c_resolved = db.session.get(Complaint, c.id)
        self.assertEqual(c_resolved.status, 'Resolved')
        w_resolved = db.session.get(Worker, self.worker.id)
        self.assertEqual(w_resolved.active_tasks_count, 0)
        self.assertEqual(w_resolved.total_resolved_count, 1)

        resolution = Resolution.query.filter_by(complaint_id=c.id).first()
        self.assertIsNotNone(resolution)
        self.assertEqual(resolution.cost_estimate, 2500.00)

    def test_admin_worker_crud(self):
        self.client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'Admin@123'})

        # Add worker
        res = self.client.post('/admin/workers', data={
            'action': 'add',
            'name': 'New Crew Member',
            'email': 'crew@smartcity.gov',
            'phone': '9988776655',
            'department': 'Sanitation & Waste',
            'zone': 'East Zone'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        new_w = Worker.query.filter_by(email='crew@smartcity.gov').first()
        self.assertIsNotNone(new_w)

        # Toggle status
        res2 = self.client.post('/admin/workers', data={
            'action': 'toggle_status',
            'worker_id': str(new_w.id),
            'status': 'Busy'
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        updated_w = db.session.get(Worker, new_w.id)
        self.assertEqual(updated_w.status, 'Busy')

    def test_export_csv(self):
        c = Complaint(
            ticket_number='SCD-CSV-0001',
            citizen_id=self.citizen.id,
            title='CSV Export Test',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='Medium',
            status='Resolved',
            latitude=28.61, longitude=77.20, original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        self.client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'Admin@123'})
        response = self.client.get('/admin/export/csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn(b'Ticket ID,Citizen Name', response.data)
        self.assertIn(b'SCD-CSV-0001', response.data)

    # =========================================================================
    # 4. REST API ENDPOINTS TESTS
    # =========================================================================

    def test_api_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertIn('total', json_data['data'])
        self.assertIn('pending', json_data['data'])

    def test_api_defects_map(self):
        c = Complaint(
            ticket_number='SCD-MAP-0001',
            citizen_id=self.citizen.id,
            title='Map Defect',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='High',
            status='Admin Review',
            latitude=28.6139, longitude=77.2090, original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        response = self.client.get('/api/defects-map')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertGreaterEqual(json_data['count'], 1)
        self.assertEqual(json_data['markers'][0]['ticket'], 'SCD-MAP-0001')

    def test_api_analytics_data(self):
        response = self.client.get('/api/analytics-data')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('trends', json_data)
        self.assertIn('categories', json_data)
        self.assertIn('severities', json_data)
        self.assertIn('zones', json_data)

    def test_api_complaint_detail(self):
        c = Complaint(
            ticket_number='SCD-API-0001',
            citizen_id=self.citizen.id,
            title='Detail Defect',
            reported_defect_type='Pothole',
            final_defect_type='Pothole',
            severity='Critical',
            status='Admin Review',
            latitude=28.6139, longitude=77.2090, original_image='test.jpg'
        )
        db.session.add(c)
        db.session.commit()

        response = self.client.get(f'/api/complaint/{c.id}')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['complaint']['ticket_number'], 'SCD-API-0001')


if __name__ == '__main__':
    unittest.main(verbosity=2)
