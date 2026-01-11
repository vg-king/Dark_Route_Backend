@echo off
REM Render deployment test script for Windows
REM This script helps test the deployment locally before pushing to Render

echo ================================================
echo Livestock Health API - Local Docker Test
echo ================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    echo Download from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

echo [OK] Docker found
echo.

REM Build the Docker image
echo Building Docker image...
docker build -t livestock-health-api:latest .

if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed
    exit /b 1
)

echo [OK] Docker image built successfully
echo.

REM Stop any existing container
echo Stopping existing containers...
docker stop livestock-health-api 2>nul
docker rm livestock-health-api 2>nul

REM Run the container
echo.
echo Starting container...
docker run -d --name livestock-health-api -p 8000:8000 -e PORT=8000 -e DATABASE_PATH=/app/data/livestock.db livestock-health-api:latest

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start container
    exit /b 1
)

echo [OK] Container started successfully
echo.

REM Wait for the service to be ready
echo Waiting for service to be ready...
timeout /t 5 /nobreak >nul

REM Test the health endpoint
echo.
echo Testing health endpoint...
curl -s http://localhost:8000/health

if %errorlevel% equ 0 (
    echo.
    echo [OK] Health check passed
) else (
    echo [ERROR] Health check failed
    echo.
    echo Container logs:
    docker logs livestock-health-api
    exit /b 1
)

REM Show container status
echo.
echo Container status:
docker ps | findstr livestock-health-api

echo.
echo ================================================
echo Deployment test complete!
echo ================================================
echo.
echo API is running at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo.
echo Useful commands:
echo   View logs:     docker logs -f livestock-health-api
echo   Stop service:  docker stop livestock-health-api
echo   Remove:        docker rm livestock-health-api
echo.
