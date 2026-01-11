#!/bin/bash

# Render deployment script
# This script helps test the deployment locally before pushing to Render

echo "🚀 Livestock Health API - Local Docker Test"
echo "==========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker found"

# Build the Docker image
echo ""
echo "📦 Building Docker image..."
docker build -t livestock-health-api:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"

# Stop any existing container
echo ""
echo "🛑 Stopping existing containers..."
docker stop livestock-health-api 2>/dev/null || true
docker rm livestock-health-api 2>/dev/null || true

# Run the container
echo ""
echo "🚀 Starting container..."
docker run -d \
  --name livestock-health-api \
  -p 8000:8000 \
  -e PORT=8000 \
  -e DATABASE_PATH=/app/data/livestock.db \
  livestock-health-api:latest

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container"
    exit 1
fi

echo "✅ Container started successfully"

# Wait for the service to be ready
echo ""
echo "⏳ Waiting for service to be ready..."
sleep 5

# Test the health endpoint
echo ""
echo "🔍 Testing health endpoint..."
response=$(curl -s http://localhost:8000/health)

if [ $? -eq 0 ]; then
    echo "✅ Health check passed:"
    echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
else
    echo "❌ Health check failed"
    echo ""
    echo "📋 Container logs:"
    docker logs livestock-health-api
    exit 1
fi

# Show container status
echo ""
echo "📊 Container status:"
docker ps | grep livestock-health-api

echo ""
echo "✨ Deployment test complete!"
echo ""
echo "📡 API is running at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
echo ""
echo "🔧 Useful commands:"
echo "  View logs:     docker logs -f livestock-health-api"
echo "  Stop service:  docker stop livestock-health-api"
echo "  Remove:        docker rm livestock-health-api"
echo ""
