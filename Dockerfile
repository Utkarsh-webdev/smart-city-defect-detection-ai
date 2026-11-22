# Multi-stage Dockerfile for Smart City Defect Detection System
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV YOLO_CONFIG_DIR=/app/.yolo

# Install system dependencies for OpenCV and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY . .

# Ensure upload and yolo directories exist with write permissions
RUN mkdir -p app/static/uploads/original \
             app/static/uploads/annotated \
             app/static/uploads/resolved \
             app/ai/weights \
             .yolo

# Seed database on build / first run
RUN python database/seed_data.py

EXPOSE 5000

# Run with Gunicorn WSGI production server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "run:app"]
