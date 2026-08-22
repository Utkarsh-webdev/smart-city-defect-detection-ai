"""
Smart City Infrastructure Defect Detection System
Configuration Module
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration with safe defaults."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-city-defect-detector-super-secret-key-2026')
    
    # Database Configuration:
    # Uses MySQL by default if configured, otherwise falls back gracefully to SQLite
    # Format for MySQL: mysql+pymysql://username:password@localhost:3306/smart_city_db
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'smart_city_db')
    
    DEFAULT_MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    SQLITE_URI = f"sqlite:///{os.path.join(basedir, 'smart_city.db')}"
    
    # Select database URI based on environment or availability
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', SQLITE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # Session & Security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # File Upload Settings
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ORIGINAL_FOLDER = os.path.join(UPLOAD_FOLDER, 'original')
    ANNOTATED_FOLDER = os.path.join(UPLOAD_FOLDER, 'annotated')
    RESOLVED_FOLDER = os.path.join(UPLOAD_FOLDER, 'resolved')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max image upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    # AI Model Parameters
    AI_CONFIDENCE_THRESHOLD = float(os.environ.get('AI_CONFIDENCE_THRESHOLD', 0.60))
    YOLO_MODEL_PATH = os.path.join(basedir, 'app', 'ai', 'weights', 'yolov8n.pt')
    YOLO_DEFECT_CLASSES = {
        0: 'Pothole',
        1: 'Broken Traffic Sign',
        2: 'Garbage Dump',
        3: 'Cracked Road'
    }

    # Pagination & UI
    ITEMS_PER_PAGE = 10
    MAP_DEFAULT_LAT = 28.6139  # Default center coordinates (e.g. New Delhi)
    MAP_DEFAULT_LNG = 77.2090
    MAP_DEFAULT_ZOOM = 12


class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration with robust settings."""
    DEBUG = False
    # Use MySQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', Config.DEFAULT_MYSQL_URI)


class TestingConfig(Config):
    """Testing configuration with in-memory SQLite database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
