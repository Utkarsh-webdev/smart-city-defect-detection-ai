-- ====================================================================
-- Smart City Infrastructure Defect Detection System
-- Complete MySQL 8.0+ Database Schema (DDL)
-- ====================================================================

CREATE DATABASE IF NOT EXISTS smart_city_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE smart_city_db;

-- 1. Citizens Table
CREATE TABLE IF NOT EXISTS citizens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    address TEXT NULL,
    is_active_account BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_citizen_email (email)
) ENGINE=InnoDB;

-- 2. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'Officer',
    department VARCHAR(100) DEFAULT 'Public Works',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_email (email)
) ENGINE=InnoDB;

-- 3. Maintenance Workers Table
CREATE TABLE IF NOT EXISTS workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    department VARCHAR(100) NOT NULL,
    zone VARCHAR(50) DEFAULT 'Central Zone',
    status VARCHAR(30) DEFAULT 'Available',
    active_tasks_count INT DEFAULT 0,
    total_resolved_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. Complaints Table
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(30) NOT NULL UNIQUE,
    citizen_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    reported_defect_type VARCHAR(60) NOT NULL,
    ai_detected_type VARCHAR(60) NULL,
    ai_confidence FLOAT NULL,
    ai_defect_count INT DEFAULT 1,
    ai_processing_status VARCHAR(30) DEFAULT 'Pending',
    final_defect_type VARCHAR(60) NOT NULL,
    severity ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
    status VARCHAR(30) DEFAULT 'Pending',
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    address VARCHAR(255) NULL,
    zone VARCHAR(50) DEFAULT 'Central Zone',
    original_image VARCHAR(255) NOT NULL,
    annotated_image VARCHAR(255) NULL,
    admin_notes TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (citizen_id) REFERENCES citizens(id) ON DELETE CASCADE,
    INDEX idx_complaint_ticket (ticket_number),
    INDEX idx_complaint_status (status),
    INDEX idx_complaint_defect (final_defect_type),
    INDEX idx_complaint_zone (zone)
) ENGINE=InnoDB;

-- 5. Worker Assignments Table
CREATE TABLE IF NOT EXISTS worker_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    worker_id INT NOT NULL,
    assigned_by_admin_id INT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'Assigned',
    notes TEXT NULL,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE RESTRICT,
    FOREIGN KEY (assigned_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 6. Resolutions Table
CREATE TABLE IF NOT EXISTS resolutions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL UNIQUE,
    worker_id INT NOT NULL,
    resolution_notes TEXT NOT NULL,
    resolved_image VARCHAR(255) NULL,
    material_used VARCHAR(255) NULL,
    cost_estimate DECIMAL(10, 2) DEFAULT 0.00,
    resolved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 7. Feedback & Citizen Ratings Table
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL UNIQUE,
    citizen_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comments TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    FOREIGN KEY (citizen_id) REFERENCES citizens(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. AI Detection Audit Logs Table
CREATE TABLE IF NOT EXISTS ai_detection_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    detected_classes TEXT NOT NULL,
    max_confidence FLOAT NOT NULL,
    processing_time_ms FLOAT DEFAULT 0.0,
    bounding_boxes TEXT NULL,
    model_version VARCHAR(50) DEFAULT 'YOLOv8n-DefectDetector-v1.0',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
) ENGINE=InnoDB;
