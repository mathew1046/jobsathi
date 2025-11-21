# Multi-stage build for JobSathi Backend
FROM python:3.10-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=200 --retries 10 -r requirements.txt

# Copy application code
COPY backend/app /app

# Create database directory
RUN mkdir -p /app/database

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

ENV PIP_DEFAULT_TIMEOUT=200
ENV PIP_RETRIES=10
ENV PIP_PROGRESS_BAR=off