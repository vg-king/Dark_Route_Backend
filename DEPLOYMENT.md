# Deployment Guide

## Local Development

### Backend (FastAPI)
```bash
cd c:\Users\KIIT0001\Downloads\Animal-Behaviour-and-Disease-Detection-main\Animal-Behaviour-and-Disease-Detection-main
.\myenv\Scripts\activate.bat
python server_enhanced.py
```
Backend runs on: `http://localhost:8000`

### Frontend (Static HTML/JS)
```bash
python -m http.server 3000 --directory frontend
```
Frontend runs on: `http://localhost:3000`

---

## Render.com Deployment

### Backend Deployment

1. Push your code to GitHub
2. Create a new Render service:
   - **Name**: `livestock-api`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server_enhanced.py`
   - **Environment Variables**:
     ```
     PORT=10000
     HOST=0.0.0.0
     ```

3. Render will expose the service at: `https://livestock-api.onrender.com`

### Frontend Deployment

1. Create a new Render service:
   - **Name**: `livestock-frontend`
   - **Environment**: `Static Site`
   - **Publish directory**: `frontend`

2. Set environment at build time or inject via HTML script tag:
   ```html
   <script>
     window.API_BASE = "https://livestock-api.onrender.com";
   </script>
   ```
   Add this to `frontend/index.html` before `script.js`

3. Frontend will be available at: `https://livestock-frontend.onrender.com`

---

## Environment Variables

### Backend
- `PORT` (default: 8000) - Server port
- `HOST` (default: 0.0.0.0) - Server host

### Frontend
- Configured via `window.API_BASE` in JavaScript
- Auto-detects production domains and uses same origin
- Falls back to `http://localhost:8000` for local development

---

## API Endpoints (JSON only)

All endpoints return JSON:

```
GET  /health              - Server health check
GET  /docs                - API documentation (Swagger UI)
POST /analyze/image       - Analyze livestock image
GET  /records             - Get all analysis records
GET  /growth/{animal_id}  - Get growth history
POST /attendance/{animal_id}
... and more
```

Example request:
```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@image.jpg" \
  -F "animal_id=Barn-12" \
  -F "ear_tag_id=TAG123"
```

All responses are JSON formatted.
