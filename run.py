"""
Smart City Pothole & Infrastructure Defect Detection System using AI
Main Application Entrypoint
"""
import os
from app import create_app
from app.models import db

# Create application using environment configuration or default
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        print(">> Database tables initialized successfully.")
    
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"\n=======================================================")
    print(f"  Smart City Defect Detection System (MCA Project)     ")
    print(f"  Server running on http://{host}:{port}             ")
    print(f"=======================================================\n")
    
    app.run(host=host, port=port, debug=app.config.get('DEBUG', True))
