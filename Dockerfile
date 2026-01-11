FROM python:3.11-bullseye

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install only essential system dependencies
# libzbar0: Required for pyzbar barcode detection
# libgomp1: Required for OpenMP parallel computing  
# curl, ca-certificates: Required for HTTP/SSL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    libgomp1 \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server_enhanced.py .
COPY database.py .
COPY identification.py .
COPY health_analyzer.py .
COPY animalpose.py .
COPY animalpose_utils.py .

# Copy model file if exists
COPY mobilenetv2_image_classifier.h5* ./

# Create directory for database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "server_enhanced.py"]
