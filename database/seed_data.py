"""
Database Seed and Demonstration Data Generator
Seeds initial Admin, Citizen, Workers, AI-inspected Complaints, Resolutions, and Feedback.
"""
import os
import sys
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, Citizen, Admin, Worker, Complaint, WorkerAssignment, Resolution, Feedback, AIDetectionLog
from app.ai.detector import DefectDetector


def generate_seed_image(filename, defect_type='Pothole'):
    """Generates synthetic defect images with bounding boxes for out-of-the-box demo."""
    orig_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'uploads', 'original'))
    annot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'uploads', 'annotated'))
    
    os.makedirs(orig_dir, exist_ok=True)
    os.makedirs(annot_dir, exist_ok=True)

    orig_path = os.path.join(orig_dir, filename)
    annot_path = os.path.join(annot_dir, f"annotated_{filename}")

    # Generate synthetic image
    img = Image.new('RGB', (640, 480), color=(60, 64, 67))
    draw = ImageDraw.Draw(img)

    if defect_type == 'Pothole':
        draw.line([(320, 0), (320, 480)], fill=(230, 200, 40), width=6)
        draw.ellipse([(180, 200), (420, 340)], fill=(20, 22, 24), outline=(10, 10, 10), width=3)
    elif defect_type == 'Broken Traffic Sign':
        draw.rectangle([(290, 120), (350, 480)], fill=(120, 125, 130))
        draw.polygon([(260, 120), (380, 120), (320, 40)], fill=(220, 50, 40))
        draw.line([(280, 60), (340, 100)], fill=(10, 10, 10), width=4)
    elif defect_type == 'Garbage Dump':
        for i, color in enumerate([(139, 69, 19), (34, 139, 34), (70, 130, 180), (105, 105, 105)]):
            draw.rectangle([(150 + i * 80, 220), (260 + i * 80, 360)], fill=color, outline=(30, 30, 30))
    elif defect_type == 'Cracked Road':
        draw.line([(320, 0), (320, 480)], fill=(230, 200, 40), width=6)
        draw.line([(220, 180), (310, 260), (280, 350), (400, 420)], fill=(20, 20, 20), width=4)
        draw.line([(310, 260), (390, 240)], fill=(20, 20, 20), width=3)

    img.save(orig_path, 'JPEG')

    # Run detector to generate annotated image
    detector = DefectDetector(confidence_threshold=0.60)
    detector.detect(orig_path, output_annotated_path=annot_path, reported_hint=defect_type)

    return filename, f"annotated_{filename}"


def seed_database():
    app = create_app()
    with app.app_context():
        print(">> Dropping and recreating all database tables...")
        db.drop_all()
        db.create_all()

        print(">> Creating Administrator account...")
        admin = Admin(
            username='admin',
            email='admin@smartcity.com',
            role='SuperAdmin',
            department='Municipal Corporation'
        )
        admin.set_password('Admin@123')
        db.session.add(admin)

        print(">> Creating Demo Citizen account...")
        citizen = Citizen(
            full_name='Aarav Sharma',
            email='demo@user.com',
            phone='+91 9876543210',
            address='Flat 402, Green Valley Apts, Sector 14, Smart City'
        )
        citizen.set_password('Demo@123')
        db.session.add(citizen)
        db.session.flush()

        print(">> Seeding Municipal Maintenance Workers...")
        workers_data = [
            {'name': 'Ramesh Kumar', 'email': 'ramesh.k@smartcity.gov', 'phone': '+91 9811122233', 'dept': 'Road Works', 'zone': 'North Zone'},
            {'name': 'Anita Sharma', 'email': 'anita.s@smartcity.gov', 'phone': '+91 9822233344', 'dept': 'Sanitation & Waste', 'zone': 'South Zone'},
            {'name': 'Vikram Singh', 'email': 'vikram.s@smartcity.gov', 'phone': '+91 9833344455', 'dept': 'Traffic Safety', 'zone': 'Central Zone'},
            {'name': 'Suresh Patel', 'email': 'suresh.p@smartcity.gov', 'phone': '+91 9844455566', 'dept': 'Road Works', 'zone': 'West Zone'}
        ]

        created_workers = []
        for w in workers_data:
            worker = Worker(
                name=w['name'],
                email=w['email'],
                phone=w['phone'],
                department=w['dept'],
                zone=w['zone'],
                status='Available'
            )
            db.session.add(worker)
            created_workers.append(worker)

        db.session.flush()

        print(">> Generating seed complaints and running AI inference...")
        sample_complaints = [
            {
                'ticket': 'SCD-202608-1011',
                'title': 'Severe crater-like pothole on Main Ring Road',
                'desc': 'Deep pothole causing vehicle damage and traffic bottleneck near Pillar 45.',
                'reported': 'Pothole',
                'lat': 28.6145, 'lng': 77.2095,
                'address': 'Ring Road near Metro Pillar 45, North Zone',
                'zone': 'North Zone',
                'status': 'Worker Assigned',
                'worker_idx': 0,
                'days_ago': 3
            },
            {
                'ticket': 'SCD-202608-1012',
                'title': 'Damaged STOP sign causing blind turn danger',
                'desc': 'Traffic regulatory sign bent at 45 degrees following vehicle collision.',
                'reported': 'Broken Traffic Sign',
                'lat': 28.6250, 'lng': 77.2180,
                'address': 'Intersection of 5th Avenue and Oak Street',
                'zone': 'Central Zone',
                'status': 'Resolved',
                'worker_idx': 2,
                'days_ago': 6,
                'resolved': True
            },
            {
                'ticket': 'SCD-202608-1013',
                'title': 'Illegal municipal garbage accumulation',
                'desc': 'Uncollected municipal solid waste spilling over pedestrian walkway.',
                'reported': 'Garbage Dump',
                'lat': 28.5980, 'lng': 77.2250,
                'address': 'Behind Central Vegetable Market, South Zone',
                'zone': 'South Zone',
                'status': 'Admin Review',
                'worker_idx': None,
                'days_ago': 1
            },
            {
                'ticket': 'SCD-202608-1014',
                'title': 'Extensive asphalt surface cracking near Flyover',
                'desc': 'Longitudinal fissures appearing after heavy monsoon rainfall.',
                'reported': 'Cracked Road',
                'lat': 28.6320, 'lng': 77.1950,
                'address': 'Flyover Descent Road, West Zone',
                'zone': 'West Zone',
                'status': 'Resolved',
                'worker_idx': 3,
                'days_ago': 5,
                'resolved': True
            },
            {
                'ticket': 'SCD-202608-1015',
                'title': 'Dangerous road depression near Bus Rapid Transit lane',
                'desc': 'Pothole measuring approx 40cm width posing critical hazard to two-wheelers.',
                'reported': 'Pothole',
                'lat': 28.6180, 'lng': 77.2310,
                'address': 'BRT Corridor Junction 7, Central Zone',
                'zone': 'Central Zone',
                'status': 'In Progress',
                'worker_idx': 0,
                'days_ago': 2
            }
        ]

        for i, item in enumerate(sample_complaints):
            fname = f"seed_{item['reported'].lower().replace(' ', '_')}_{i+1}.jpg"
            orig_img, annot_img = generate_seed_image(fname, defect_type=item['reported'])

            created_time = datetime.utcnow() - timedelta(days=item['days_ago'])
            
            c = Complaint(
                ticket_number=item['ticket'],
                citizen_id=citizen.id,
                title=item['title'],
                description=item['desc'],
                reported_defect_type=item['reported'],
                ai_detected_type=item['reported'],
                ai_confidence=0.88 if i % 2 == 0 else 0.92,
                ai_defect_count=1,
                ai_processing_status='Processed',
                final_defect_type=item['reported'],
                severity='Critical' if item['reported'] == 'Pothole' else 'High',
                status=item['status'],
                latitude=item['lat'],
                longitude=item['lng'],
                address=item['address'],
                zone=item['zone'],
                original_image=orig_img,
                annotated_image=annot_img,
                created_at=created_time,
                updated_at=created_time + timedelta(hours=4)
            )
            db.session.add(c)
            db.session.flush()

            # Add AI Detection Log
            ai_log = AIDetectionLog(
                complaint_id=c.id,
                detected_classes=f"['{item['reported']}']",
                max_confidence=c.ai_confidence,
                processing_time_ms=18.4,
                bounding_boxes=f"[{{'class': '{item['reported']}', 'conf': {c.ai_confidence}}}]",
                model_version='YOLOv8n-DefectDetector-v1.0',
                created_at=created_time
            )
            db.session.add(ai_log)

            # Add Worker Assignment if assigned
            if item['worker_idx'] is not None:
                assigned_worker = created_workers[item['worker_idx']]
                assign = WorkerAssignment(
                    complaint_id=c.id,
                    worker_id=assigned_worker.id,
                    assigned_by_admin_id=admin.id,
                    assigned_at=created_time + timedelta(hours=2),
                    status='Completed' if item.get('resolved') else 'In Progress',
                    notes='Priority municipal work order assigned.'
                )
                db.session.add(assign)
                
                if not item.get('resolved'):
                    assigned_worker.active_tasks_count += 1
                    assigned_worker.status = 'Busy'

            # Add Resolution & Feedback if resolved
            if item.get('resolved'):
                assigned_worker = created_workers[item['worker_idx']]
                assigned_worker.total_resolved_count += 1
                res = Resolution(
                    complaint_id=c.id,
                    worker_id=assigned_worker.id,
                    resolution_notes='Defect completely repaired using standard bitumen cold mix & compaction. Road restored to smooth grade.',
                    material_used='Cold Bituminous Mix (50kg), Tack Coat Emulsion',
                    cost_estimate=3200.00,
                    resolved_at=created_time + timedelta(days=1)
                )
                db.session.add(res)

                # Add Citizen Feedback
                feedback = Feedback(
                    complaint_id=c.id,
                    citizen_id=citizen.id,
                    rating=5 if i % 2 == 0 else 4,
                    comments='Extremely fast response from the municipal team. Fixed within 24 hours!',
                    created_at=created_time + timedelta(days=1, hours=3)
                )
                db.session.add(feedback)

        db.session.commit()
        print("\n=======================================================")
        print("  Database Seed Completed Successfully!              ")
        print("  Admin Credentials:   admin@smartcity.com / Admin@123")
        print("  Citizen Credentials: demo@user.com      / Demo@123  ")
        print("=======================================================\n")


if __name__ == '__main__':
    seed_database()
