# Smart City Pothole & Infrastructure Defect Detection System using AI

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg)](https://docs.ultralytics.com/)
[![Bootstrap 5](https://img.shields.io/badge/Bootstrap-5.3.2-purple.svg)](https://getbootstrap.com/)
[![Leaflet.js](https://img.shields.io/badge/Leaflet.js-GIS%20Maps-brightgreen.svg)](https://leafletjs.com/)

> An enterprise-grade MCA Final Major Project integrating Deep Learning (Ultralytics YOLOv8), HTML5 Geolocation, and Flask/SQLAlchemy to automate the reporting, detection, geospatial mapping, worker dispatch, and repair governance of urban infrastructure defects.

---

## 📌 Key System Features

### 👤 Citizen Portal
* **One-Click Geolocation Auto-Capture:** HTML5 Geolocation API locks GPS coordinates (Latitude & Longitude) with sub-second reverse geocoding.
* **Smart Drag-and-Drop Image Uploader:** Client-side image validation and live thumbnail preview.
* **Instant AI Defect Verification:** Identifies defect category, confidence rating, and calculated severity.
* **Interactive 5-Stage Lifecycle Stepper:** Visual tracking (`Reported` $\to$ `AI Verified` $\to$ `Admin Review` $\to$ `Worker Dispatched` $\to$ `Resolved`).
* **Citizen Feedback & Star Rating:** Post-resolution 1-5 star quality reviews and remarks.

### 🛡️ Municipal Admin Command Center
* **Live KPI Metric Cards:** Real-time counters for Total Incidents, Pending Review, Dispatched Crews, and Critical Hazards.
* **Interactive GIS Defect Heatmap:** Leaflet.js map with custom color-coded map pins, clustering, and defect popups.
* **Rapid Defect Triage & Reclassification:** Municipal officer override tool for defect classes and severity levels.
* **One-Click Field Crew Dispatch:** Assign available municipal workers with dynamic workload balancing.
* **Business Intelligence Dashboard:** Chart.js visualizations for 7-day intake trends, category distributions, and zone densities.
* **Master Audit CSV Export:** One-click spreadsheet export for municipal budget and maintenance audits.

### 🤖 YOLOv8 Computer Vision Pipeline
* **Multi-Class Defect Detection:**
  * 🔴 **Pothole** (Asphalt depressions and crater depth hazards)
  * 🟠 **Broken Traffic Sign** (Bent, vandalized, or fallen regulatory signs)
  * 🟢 **Garbage Dump** (Illegal solid waste accumulation & overflowing dumpsters)
  * 🔵 **Cracked Road** (Longitudinal, transverse, and alligator fissures)
* **Automatic Severity Assessment:** Computed dynamically from defect bounding box area ratios.
* **Quality Gate Fallback:** If confidence $< 60\%$, automatically flags ticket as `LowConfidence` for human officer verification.

---

## 📂 Project Directory Structure

```
smart_city_defect_detector/
├── app/
│   ├── __init__.py                # App factory, extensions init, login manager
│   ├── models.py                  # SQLAlchemy ORM models (Citizen, Admin, Complaint, Worker, Resolution, Feedback)
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── model_loader.py        # Safe YOLOv8 loader with weights caching & fallback
│   │   ├── detector.py            # AI defect detection engine & OpenCV bounding box renderer
│   │   └── test_ai.py             # Self-testing script for computer vision engine
│   ├── routes/
│   │   ├── __init__.py            # Auth decorators (@admin_required, @citizen_required)
│   │   ├── auth.py                # Citizen & Admin registration, login, logout, profile
│   │   ├── citizen.py             # Defect reporting, GPS ingestion, history tracking, rating
│   │   ├── admin.py               # Municipal dashboard, worker dispatch, reclassification, analytics
│   │   └── api.py                 # REST APIs for Leaflet maps, Chart.js feeds, and AJAX
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Custom styling, dark/light cards, responsive tweaks
│   │   ├── js/
│   │   │   ├── main.js            # Core utilities, toast notifications, formatting
│   │   │   ├── dashboard.js       # Chart.js analytics graphs
│   │   │   ├── maps.js            # Leaflet / OpenStreetMap interactive defect map
│   │   │   ├── upload.js          # Geolocation capture & image preview
│   │   │   └── admin.js           # AJAX complaint management & modals
│   │   └── uploads/
│   │       ├── original/          # User-uploaded defect photographs
│   │       ├── annotated/         # AI-annotated images with bounding boxes
│   │       └── resolved/          # Post-repair resolution proof images
│   └── templates/
│       ├── base.html              # Base layout with navbar, footer, flash alerts
│       ├── index.html             # High-impact landing page
│       ├── citizen/
│       │   ├── register.html      # Citizen registration
│       │   ├── login.html         # Citizen login
│       │   ├── dashboard.html     # Citizen dashboard & recent complaints
│       │   ├── upload_complaint.html # Upload form with GPS autofetch & preview
│       │   ├── complaint_status.html # Detailed status tracker & timeline
│       │   ├── history.html       # Paginated complaint history
│       │   └── profile.html       # Profile management
│       └── admin/
│           ├── login.html         # Municipal Admin login
│           ├── dashboard.html     # Admin command center & quick triage
│           ├── manage_complaints.html # Complaints table with multi-filter & modals
│           ├── analytics.html     # Deep dive analytics reports & export
│           └── workers.html       # Worker management (CRUD, status, workload)
├── database/
│   ├── schema.sql                 # Pure MySQL 8.0 DDL script with constraints and indexes
│   └── seed_data.py               # Python seeder script for demo users, workers, and complaints
├── docs/
│   └── PROJECT_REPORT.md          # Full 13-section comprehensive MCA project report
├── config.py                      # Production (MySQL) and Development (SQLite) configs
├── run.py                         # Application entry point
├── requirements.txt               # Pinned Python dependencies
└── README.md                      # Complete system setup and execution documentation
```

---

## ⚡ Quick Start Guide

### 1. Virtual Environment Setup
```powershell
# Navigate to the workspace directory
cd c:\Users\utkar\P1

# Create Python virtual environment
python -m venv venv

# Activate Virtual Environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Database Initialization & Demonstration Seeding
```powershell
python database/seed_data.py
```

### 4. Run Application Server
```powershell
python run.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🔑 Pre-Created Demonstration Credentials

| Role | Email / Username | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Municipal Administrator** | `admin@smartcity.com` (or `admin`) | `Admin@123` | Full administrative control, triage queue, worker dispatch, reclassification, analytics, CSV export |
| **Registered Citizen** | `demo@user.com` | `Demo@123` | Defect reporting, GPS capture, history view, real-time lifecycle tracking, star rating & feedback |

---

## 🧪 Testing and Verification

To verify the YOLOv8 computer vision detection and bounding box rendering independently:
```powershell
python app/ai/test_ai.py
```
* **Output:** Generates a synthetic test defect image, runs inference, prints detection metadata (class, confidence, severity, latency), and saves the annotated bounding box image to `app/ai/test_samples/sample_annotated.jpg`.

---

## 📊 Complete Academic Project Report

The complete, exhaustive 13-section Project Report formatted for MCA Capstone Project submission is located at:
📁 **[`docs/PROJECT_REPORT.md`](file:///c:/Users/utkar/P1/docs/PROJECT_REPORT.md)**

It contains:
* Full Problem Background, Societal Significance & Existing System Limitations
* Measurable Objectives & Methodology
* Hardware/Software Matrices with Versioning Justifications
* 3-Tier Architecture & Narrative Workflows
* DFD Level 0, Level 1, and Level 2 AI Pipeline Models
* Complete Entity-Relationship (ER) Modeling with Schema Mappings
* Pure MySQL 8.0 DDL & DML Scripts
* Pseudocode Specifications for all Core Modules
* 4 Standardized Municipal Reports with Production SQL Queries
* 10 Innovative Future Research Extensions (Edge AI, LiDAR, Drone Swarms, Blockchain)
* Academic Bibliography (10+ Textbooks with ISBNs + 15+ Authoritative Papers/Websites)
