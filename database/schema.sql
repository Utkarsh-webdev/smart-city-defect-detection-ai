-- ====================================================================
-- Smart City Infrastructure Defect Detection System
-- Complete MySQL 8.0+ Database Schema
-- ====================================================================

CREATE DATABASE IF NOT EXISTS smart_city_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE smart_city_db;


-- ====================================================================
-- 1. CITIZENS
-- ====================================================================

CREATE TABLE IF NOT EXISTS citizens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    address TEXT NULL,
    is_active_account BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_citizen_email (email)
) ENGINE=InnoDB;


-- ====================================================================
-- 2. ADMINS
-- ====================================================================

CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Officer',
    department VARCHAR(100) NOT NULL DEFAULT 'Public Works',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_admin_email (email)
) ENGINE=InnoDB;


-- ====================================================================
-- 3. MAINTENANCE WORKERS
-- ====================================================================

CREATE TABLE IF NOT EXISTS workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    department VARCHAR(100) NOT NULL,
    zone VARCHAR(50) NOT NULL DEFAULT 'Central Zone',
    status VARCHAR(30) NOT NULL DEFAULT 'Available',
    active_tasks_count INT NOT NULL DEFAULT 0,
    total_resolved_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_worker_active_tasks CHECK (active_tasks_count >= 0),
    CONSTRAINT chk_worker_resolved_count CHECK (total_resolved_count >= 0)
) ENGINE=InnoDB;


-- ====================================================================
-- 4. COMPLAINTS
-- ====================================================================

CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(30) NOT NULL UNIQUE,
    citizen_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    reported_defect_type VARCHAR(60) NOT NULL,
    ai_detected_type VARCHAR(60) NULL,
    ai_confidence FLOAT NULL,
    ai_defect_count INT NOT NULL DEFAULT 1,
    ai_processing_status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    final_defect_type VARCHAR(60) NOT NULL,
    severity ENUM('Low', 'Medium', 'High', 'Critical') NOT NULL DEFAULT 'Medium',
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    address VARCHAR(255) NULL,
    zone VARCHAR(50) NOT NULL DEFAULT 'Central Zone',
    original_image VARCHAR(255) NOT NULL,
    annotated_image VARCHAR(255) NULL,
    admin_notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_complaint_citizen FOREIGN KEY (citizen_id) REFERENCES citizens(id) ON DELETE CASCADE,
    CONSTRAINT chk_ai_confidence CHECK (ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)),
    CONSTRAINT chk_ai_defect_count CHECK (ai_defect_count >= 0),
    CONSTRAINT chk_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_longitude CHECK (longitude BETWEEN -180 AND 180),
    
    INDEX idx_complaint_citizen (citizen_id),
    INDEX idx_complaint_status (status),
    INDEX idx_complaint_defect (final_defect_type),
    INDEX idx_complaint_zone (zone),
    INDEX idx_complaint_created (created_at)
) ENGINE=InnoDB;


-- ====================================================================
-- 5. WORKER ASSIGNMENTS
-- ====================================================================

CREATE TABLE IF NOT EXISTS worker_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    worker_id INT NOT NULL,
    assigned_by_admin_id INT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'Assigned',
    notes TEXT NULL,
    
    CONSTRAINT fk_assignment_complaint FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    CONSTRAINT fk_assignment_worker FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE RESTRICT,
    CONSTRAINT fk_assignment_admin FOREIGN KEY (assigned_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL,
    
    INDEX idx_assignment_complaint (complaint_id),
    INDEX idx_assignment_worker (worker_id),
    INDEX idx_assignment_status (status)
) ENGINE=InnoDB;


-- ====================================================================
-- 6. RESOLUTIONS
-- ====================================================================

CREATE TABLE IF NOT EXISTS resolutions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL UNIQUE,
    worker_id INT NOT NULL,
    resolution_notes TEXT NOT NULL,
    resolved_image VARCHAR(255) NULL,
    material_used VARCHAR(255) NULL,
    cost_estimate DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    resolved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_resolution_complaint FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    CONSTRAINT fk_resolution_worker FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE RESTRICT,
    CONSTRAINT chk_resolution_cost CHECK (cost_estimate >= 0),
    
    INDEX idx_resolution_worker (worker_id),
    INDEX idx_resolution_date (resolved_at)
) ENGINE=InnoDB;


-- ====================================================================
-- 7. CITIZEN FEEDBACK
-- ====================================================================

CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL UNIQUE,
    citizen_id INT NOT NULL,
    rating INT NOT NULL,
    comments TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_feedback_complaint FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    CONSTRAINT fk_feedback_citizen FOREIGN KEY (citizen_id) REFERENCES citizens(id) ON DELETE CASCADE,
    CONSTRAINT chk_feedback_rating CHECK (rating BETWEEN 1 AND 5),
    
    INDEX idx_feedback_citizen (citizen_id),
    INDEX idx_feedback_created (created_at)
) ENGINE=InnoDB;


-- ====================================================================
-- 8. AI DETECTION AUDIT LOGS
-- ====================================================================

CREATE TABLE IF NOT EXISTS ai_detection_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    detected_classes TEXT NOT NULL,
    max_confidence FLOAT NOT NULL,
    processing_time_ms FLOAT NOT NULL DEFAULT 0.0,
    bounding_boxes TEXT NULL,
    model_version VARCHAR(50) NOT NULL DEFAULT 'YOLOv8n-DefectDetector-v1.0',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ai_log_complaint FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    CONSTRAINT chk_ai_max_confidence CHECK (max_confidence >= 0 AND max_confidence <= 1),
    CONSTRAINT chk_processing_time CHECK (processing_time_ms >= 0),
    
    INDEX idx_ai_log_complaint (complaint_id),
    INDEX idx_ai_log_created (created_at)
) ENGINE=InnoDB;