"""
Smart City Infrastructure Defect Detection System
Configuration Module
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

# Load .env during local development.
# Render will use its Environment Variables instead.
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


# ============================================================
# DATABASE URL
# ============================================================

database_url = os.environ.get("DATABASE_URL")

# Render / older PostgreSQL URLs may use postgres://
# SQLAlchemy expects postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )


class Config:
    """Base configuration."""

    # ========================================================
    # SECURITY
    # ========================================================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "smart-city-defect-detector-super-secret-key-2026"
    )

    # ========================================================
    # DATABASE
    # ========================================================

    # Local MySQL settings
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "root")
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
    MYSQL_DB = os.environ.get("MYSQL_DB", "smart_city_db")

    DEFAULT_MYSQL_URI = (
        f"mysql+pymysql://"
        f"{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )

    # Local SQLite fallback
    SQLITE_URI = (
        f"sqlite:///{os.path.join(basedir, 'smart_city.db')}"
    )

    # Priority:
    #
    # Render:
    # DATABASE_URL -> PostgreSQL
    #
    # Local:
    # SQLite fallback
    #
    SQLALCHEMY_DATABASE_URI = (
        database_url or SQLITE_URI
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # ========================================================
    # SESSION & SECURITY
    # ========================================================

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # HTTPS on production
    SESSION_COOKIE_SECURE = (
        os.environ.get("FLASK_ENV") == "production"
    )

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ========================================================
    # FILE UPLOAD
    # ========================================================

    UPLOAD_FOLDER = os.path.join(
        basedir,
        "app",
        "static",
        "uploads"
    )

    ORIGINAL_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "original"
    )

    ANNOTATED_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "annotated"
    )

    RESOLVED_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "resolved"
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    ALLOWED_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }

    # ========================================================
    # AI / YOLOv8
    # ========================================================

    AI_CONFIDENCE_THRESHOLD = float(
        os.environ.get(
            "AI_CONFIDENCE_THRESHOLD",
            0.60
        )
    )

    YOLO_MODEL_PATH = os.path.join(
        basedir,
        "app",
        "ai",
        "weights",
        "yolov8n.pt"
    )

    YOLO_DEFECT_CLASSES = {
        0: "Pothole",
        1: "Broken Traffic Sign",
        2: "Garbage Dump",
        3: "Cracked Road"
    }

    # ========================================================
    # PAGINATION
    # ========================================================

    ITEMS_PER_PAGE = 10

    # ========================================================
    # MAP
    # ========================================================

    MAP_DEFAULT_LAT = 28.6139
    MAP_DEFAULT_LNG = 77.2090
    MAP_DEFAULT_ZOOM = 12


# ============================================================
# DEVELOPMENT
# ============================================================

class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


# ============================================================
# PRODUCTION
# ============================================================

class ProductionConfig(Config):
    """Production configuration for Render."""

    DEBUG = False

    # DATABASE_URL supplied by Render.
    #
    # Example:
    # postgresql://username:password@host/database
    #
    SQLALCHEMY_DATABASE_URI = (
        database_url or Config.SQLITE_URI
    )

    # Never expose detailed errors in production
    PROPAGATE_EXCEPTIONS = False


# ============================================================
# TESTING
# ============================================================

class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"
    )

    WTF_CSRF_ENABLED = False


# ============================================================
# CONFIGURATION MAP
# ============================================================

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}