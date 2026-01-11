# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment to noninteractive to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Clear APT cache and update with robust error handling
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    mkdir -p /var/lib/apt/lists/partial && \
    apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::AllowInsecureRepositories=true || true && \
    apt-get install -y --no-install-recommends --allow-unauthenticated \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libzbar0 \
    libxcb1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    curl \
    ca-certificates \
    || true && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip and install Python dependencies with retry logic
RUN pip install --upgrade --no-cache-dir pip setuptools wheel && \
    pip install --no-cache-dir --retries 5 -r requirements.txt || \
    pip install --no-cache-dir --retries 5 -r requirements.txt

# Copy application files
COPY server_enhanced.py .
COPY database.py .
COPY identification.py .
COPY health_analyzer.py .
COPY animalpose.py .
COPY animalpose_utils.py .

# Copy model file if exists (optional)
COPY mobilenetv2_image_classifier.h5* ./

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD uvicorn server_enhanced:app --host 0.0.0.0 --port $PORT
