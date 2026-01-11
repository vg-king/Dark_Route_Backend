"""
Enhanced Livestock Health & Identification API
Comprehensive system with database, identification, health analysis, and attendance tracking
"""

import io
import json
import os
import time
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image

# Import custom modules
from database import LivestockDatabase
from identification import AnimalIdentifier
from health_analyzer import HealthAnalyzer

_tf_available: bool = True
_load_model_available: bool = True
_model_error: Optional[str] = None

try:
    from tensorflow.keras.models import load_model
except Exception as exc:
    # TensorFlow/Keras not available in this Python version/env
    _tf_available = False
    _load_model_available = False
    load_model = None
    _model_error = f"TensorFlow/Keras import failed: {exc}"

APP_TITLE = "Livestock Health & Identification API - Enhanced"
MODEL_PATH = Path(__file__).parent / "mobilenetv2_image_classifier.h5"
HEALTH_LABELS = ["cognitive", "Injured", "mange"]

app = FastAPI(title=APP_TITLE, version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
db = LivestockDatabase()
identifier = AnimalIdentifier()
health_analyzer = HealthAnalyzer()
_model = None


def _load_health_model():
    global _model
    global _model_error
    if _model is not None or load_model is None:
        return
    if MODEL_PATH.exists():
        try:
            _model = load_model(MODEL_PATH)
            print("[INFO] Health classification model loaded successfully")
        except Exception as exc:
            print(f"[WARN] Failed to load health model (Keras version issue): {exc}")
            print("[INFO] Using fallback heuristic health analysis instead")
            _model = None
            _model_error = str(exc)


_load_health_model()


def _predict_health_ml(image_array: np.ndarray) -> Dict:
    """ML-based health prediction using TensorFlow model"""
    if _model is None:
        return None

    try:
        resized = cv2.resize(image_array, (224, 224))
        normalized = resized.astype("float32") / 255.0
        batch = np.expand_dims(normalized, axis=0)

        predictions = _model.predict(batch, verbose=0)
        scores = predictions[0]
        scores_map = {label: float(scores[idx]) for idx, label in enumerate(HEALTH_LABELS)}
        best_idx = int(np.argmax(scores))
        
        return {
            "label": HEALTH_LABELS[best_idx],
            "confidence": float(scores[best_idx]),
            "scores": scores_map
        }
    except Exception as exc:
        print(f"[WARN] Model prediction failed: {exc}")
        return None


def _predict_behavior(image_array: np.ndarray) -> Dict:
    """Behavior classification using image analysis"""
    try:
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # Motion/sharpness analysis
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(gray.mean())
        
        # Edge density (activity indicator)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0) / edges.size)
        
        # Texture analysis
        texture = float(np.std(gray))
        
        # Heuristic scoring
        scores = {
            "Standing": max(0.0, 0.3 * (laplacian_var / 100) + 0.3 * edge_density + 0.2 * (texture / 50)),
            "Eating": max(0.0, 0.4 * (brightness / 255) + 0.3 * edge_density + 0.2 * (texture / 50)),
            "Resting": max(0.0, 0.5 * (1 - edge_density) + 0.3 * (1 - laplacian_var / 200) + 0.2 * (200 - brightness) / 200),
            "Walking": max(0.0, 0.4 * edge_density + 0.3 * (laplacian_var / 100) + 0.2 * (texture / 50)),
        }
        
        total = sum(scores.values()) or 1.0
        normalized = {k: v / total for k, v in scores.items()}
        best_label = max(normalized, key=normalized.get)
        
        return {"label": best_label, "scores": normalized}
        
    except Exception as e:
        print(f"Behavior prediction error: {e}")
        return {"label": "Unknown", "scores": {}}


@app.get("/")
def root() -> Dict:
    """Root endpoint - API information and status"""
    return {
        "name": APP_TITLE,
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health (GET)",
            "docs": "/docs (GET)",
            "analyze": "/analyze/image (POST)",
            "records": "/records (GET)",
            "animals": "/animals/register (POST)",
            "growth": "/growth/{animal_id} (GET)",
            "attendance": "/attendance/{animal_id} (POST)"
        },
        "frontend": "Access frontend at http://localhost:3000",
        "documentation": "API docs available at /docs"
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    """API health check endpoint"""
    return {
        "status": "ok",
        "model_loaded": str(_model is not None),
        "database": "connected",
        "version": "2.0.0",
        # Diagnostics
        "model_path_exists": str(MODEL_PATH.exists()),
        "tf_available": str(_tf_available),
        "load_model_imported": str(_load_model_available),
        "model_error": _model_error or ""
    }


@app.post("/animals/register")
async def register_animal(
    animal_id: str = Form(...),
    species: str = Form("cattle"),
    breed: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    ear_tag_id: Optional[str] = Form(None),
    rfid: Optional[str] = Form(None),
    qr_id: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Register a new animal in the system"""
    try:
        # Extract biometric signatures if image provided
        facial_signature = None
        muzzle_signature = None
        
        if file:
            content = await file.read()
            image = Image.open(io.BytesIO(content)).convert("RGB")
            array = np.array(image)
            
            # Extract biometric features
            id_results = identifier.identify_animal(array)
            
            if id_results.get('facial_features'):
                facial_signature = json.dumps(id_results['facial_features'].get('feature_vector', []))
            
            if id_results.get('muzzle_pattern'):
                muzzle_signature = json.dumps(id_results['muzzle_pattern'].get('feature_vector', []))
        
        # Register in database
        animal_data = {
            'animal_id': animal_id,
            'species': species,
            'breed': breed,
            'date_of_birth': date_of_birth,
            'gender': gender,
            'ear_tag_id': ear_tag_id,
            'rfid': rfid,
            'qr_id': qr_id,
            'facial_signature': facial_signature,
            'muzzle_signature': muzzle_signature,
            'current_location': location,
            'notes': notes
        }
        
        registered_id = db.register_animal(animal_data)
        
        return {
            "success": True,
            "animal_id": registered_id,
            "message": "Animal registered successfully",
            "biometric_captured": facial_signature is not None or muzzle_signature is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


@app.post("/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    animal_id: Optional[str] = Form(None),
    ear_tag_id: Optional[str] = Form(None),
    rfid: Optional[str] = Form(None),
    qr_id: Optional[str] = Form(None),
    weight_kg: Optional[float] = Form(None),
    body_temperature_c: Optional[float] = Form(None),
    heart_rate_bpm: Optional[int] = Form(None),
    respiratory_rate: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    recorded_by: Optional[str] = Form("system"),
):
    """
    Comprehensive livestock analysis:
    - Animal identification (QR, ear tags, biometrics)
    - Health assessment (disease, body condition, lameness)
    - Behavior classification
    - Attendance marking
    """
    start = time.time()
    analysis_id = str(uuid.uuid4())
    
    try:
        # Load and process image
        content = await file.read()
        print(f"[DEBUG] Image loaded: {len(content)} bytes")
        image = Image.open(io.BytesIO(content)).convert("RGB")
        array = np.array(image)
        bgr_array = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        print(f"[DEBUG] Image converted: {array.shape}")
        
        # 1. IDENTIFICATION
        print("[DEBUG] Starting identification...")
        try:
            id_results = identifier.identify_animal(
                bgr_array,
                known_identifiers={'qr_id': qr_id, 'rfid': rfid, 'ear_tag_id': ear_tag_id}
            )
            print(f"[DEBUG] Identification OK: {id_results.get('primary_method')}")
        except Exception as id_err:
            print(f"[ERROR] Identification failed: {id_err}")
            raise
        
        # Try to match existing animal
        detected_animal = None
        try:
            if id_results['detected_identifiers'].get('qr_id'):
                detected_animal = db.get_animal(qr_id=id_results['detected_identifiers']['qr_id'])
            elif ear_tag_id:
                detected_animal = db.get_animal(ear_tag=ear_tag_id)
            elif animal_id:
                detected_animal = db.get_animal(animal_id=animal_id)
            print(f"[DEBUG] Animal lookup: found={detected_animal is not None}")
        except Exception as lookup_err:
            print(f"[ERROR] Animal lookup failed: {lookup_err}")
        
        # Use detected or provided animal_id
        final_animal_id = detected_animal['animal_id'] if detected_animal else (animal_id or "unknown")
        
        # 2. BEHAVIOR ANALYSIS
        print("[DEBUG] Starting behavior analysis...")
        try:
            behavior = _predict_behavior(array)
            print(f"[DEBUG] Behavior OK: {behavior['label']}")
        except Exception as bhv_err:
            print(f"[ERROR] Behavior failed: {bhv_err}")
            behavior = {"label": "Unknown", "scores": {}}
        
        # 3. HEALTH ANALYSIS
        print("[DEBUG] Starting health analysis...")
        # Try ML model first
        try:
            health_ml = _predict_health_ml(array)
            print(f"[DEBUG] ML Health OK: {health_ml}")
        except Exception as ml_err:
            print(f"[ERROR] ML Health failed: {ml_err}")
            health_ml = None
        
        # Comprehensive health assessment
        vitals = {
            'weight_kg': weight_kg,
            'body_temperature_c': body_temperature_c,
            'heart_rate_bpm': heart_rate_bpm,
            'respiratory_rate_bpm': respiratory_rate
        }
        
        print("[DEBUG] Starting comprehensive health assessment...")
        try:
            comprehensive_health = health_analyzer.comprehensive_health_assessment(
                bgr_array,
                pose_keypoints=None,  # Can be integrated with pose estimation
                vitals=vitals
            )
            print(f"[DEBUG] Comprehensive health OK: {comprehensive_health.get('overall_status')}")
        except Exception as comp_err:
            print(f"[ERROR] Comprehensive health failed: {comp_err}")
            # Fallback health assessment
            comprehensive_health = {
                'overall_status': 'Unknown',
                'health_score': 0,
                'body_condition': {'score': 0, 'assessment': 'Unknown'},
                'lameness': {'detected': False},
                'symptoms': {'symptoms': [], 'total_detected': 0},
                'recommendations': ['Please review manually'],
                'alerts': []
            }
        
        # Merge ML health prediction with comprehensive analysis
        if health_ml:
            final_health = {
                'label': health_ml['label'],
                'confidence': health_ml['confidence'],
                'scores': health_ml['scores'],
                'comprehensive': comprehensive_health
            }
        else:
            # Use comprehensive assessment primary finding
            final_health = {
                'label': comprehensive_health.get('overall_status', 'Unknown'),
                'confidence': (comprehensive_health.get('health_score', 0) or 0) / 100,
                'scores': {},
                'comprehensive': comprehensive_health
            }
        print(f"[DEBUG] Health finalized: {final_health['label']}")
        
        # 4. BUILD RECOMMENDATIONS
        recommendations = list(comprehensive_health.get('recommendations', []))
        recommendations.extend(comprehensive_health.get('alerts', []))
        
        # 5. SAVE TO DATABASE
        print("[DEBUG] Building database record...")
        try:
            record = {
                'analysis_id': analysis_id,
                'animal_id': final_animal_id,
                'health_status': final_health.get('label', 'Unknown'),
                'health_confidence': final_health.get('confidence', 0),
                'health_scores': final_health.get('scores', {}),
                'behavior_status': behavior.get('label', 'Unknown'),
                'behavior_scores': behavior.get('scores', {}),
                'weight_kg': weight_kg,
                'body_temperature_c': body_temperature_c,
                'heart_rate_bpm': heart_rate_bpm,
                'respiratory_rate': respiratory_rate,
                'body_condition_score': comprehensive_health.get('body_condition', {}).get('score'),
                'lameness_detected': comprehensive_health.get('lameness', {}).get('detected', False),
                'posture_issues': json.dumps(comprehensive_health.get('posture_issues', [])),
                'visible_injuries': json.dumps(comprehensive_health.get('symptoms', {}).get('symptoms', [])),
                'symptoms': notes,
                'recommendations': recommendations,
                'location': location,
                'recorded_by': recorded_by
            }
            
            db.add_health_record(record)
            print("[DEBUG] Record saved to database")
        except Exception as db_err:
            print(f"[WARN] Database save failed (continuing): {db_err}")
        
        # 6. MARK ATTENDANCE
        try:
            if final_animal_id != "unknown":
                db.mark_attendance(
                    final_animal_id,
                    location=location,
                    detection_method=id_results.get('primary_method', 'manual')
                )
                print("[DEBUG] Attendance marked")
        except Exception as att_err:
            print(f"[WARN] Attendance marking failed (continuing): {att_err}")
        
        # 7. LOG IDENTIFICATION EVENT
        try:
            if id_results.get('primary_method'):
                db.log_identification_event({
                    'animal_id': final_animal_id,
                    'detection_method': id_results['primary_method'],
                    'identifier_value': str(id_results.get('detected_identifiers', {})),
                    'confidence': id_results.get('confidence_score', 0),
                    'location': location
                })
                print("[DEBUG] Identification event logged")
        except Exception as log_err:
            print(f"[WARN] Event logging failed (continuing): {log_err}")
        
        elapsed_ms = int((time.time() - start) * 1000)
        print(f"[DEBUG] Analysis complete in {elapsed_ms}ms")
        
        # Response
        return {
            "analysisId": analysis_id,
            "elapsedMs": elapsed_ms,
            "animalId": final_animal_id,
            "animalFound": detected_animal is not None,
            "identification": {
                "method": id_results.get('primary_method'),
                "confidence": id_results['confidence_score'],
                "qr_detected": len(id_results.get('qr_codes', [])) > 0,
                "ear_tags_detected": len(id_results.get('ear_tags', [])) > 0,
                "biometric_available": id_results.get('facial_features') is not None
            },
            "behavior": behavior,
            "health": final_health,
            "identifiers": {
                "earTagId": ear_tag_id,
                "rfid": rfid,
                "qrId": qr_id
            },
            "metrics": vitals,
            "location": location,
            "notes": notes,
            "recordedAt": datetime.utcnow().isoformat() + "Z",
            "recommendations": recommendations,
            "attendanceMarked": final_animal_id != "unknown"
        }
        
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/animals")
def get_animals(status: str = Query("active")):
    """Get all registered animals"""
    animals = db.get_all_animals(status=status)
    return {"items": animals, "count": len(animals)}


@app.get("/animals/{animal_id}")
def get_animal(animal_id: str):
    """Get specific animal details"""
    animal = db.get_animal(animal_id=animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    # Get health history
    health_records = db.get_health_records(animal_id, limit=10)
    growth_history = db.get_growth_history(animal_id)
    
    return {
        "animal": animal,
        "health_records": health_records,
        "growth_history": growth_history
    }


@app.get("/records")
def get_records(limit: int = Query(50, le=200)):
    """Get recent health analysis records"""
    records = db.get_recent_records(limit=limit)
    return {"items": records, "count": len(records)}


@app.get("/attendance")
def get_attendance(date: Optional[str] = Query(None)):
    """Get attendance report for specific date or today"""
    report = db.get_attendance_report(date=date)
    
    present = [r for r in report if r['check_in_time'] is not None]
    absent = [r for r in report if r['check_in_time'] is None]
    
    return {
        "date": date or str(datetime.now().date()),
        "total_animals": len(report),
        "present": len(present),
        "absent": len(absent),
        "attendance_rate": f"{(len(present)/len(report)*100):.1f}%" if report else "0%",
        "details": report
    }


@app.get("/statistics")
def get_statistics():
    """Get system-wide statistics"""
    stats = db.get_statistics()
    return stats


@app.post("/growth/record")
async def record_growth(
    animal_id: str = Form(...),
    weight_kg: Optional[float] = Form(None),
    height_cm: Optional[float] = Form(None),
    length_cm: Optional[float] = Form(None),
    girth_cm: Optional[float] = Form(None),
    body_condition_score: Optional[int] = Form(None),
    notes: Optional[str] = Form(None)
):
    """Record growth measurements"""
    try:
        measurements = {
            'weight_kg': weight_kg,
            'height_cm': height_cm,
            'length_cm': length_cm,
            'girth_cm': girth_cm,
            'body_condition_score': body_condition_score,
            'notes': notes
        }
        
        success = db.add_growth_measurement(animal_id, measurements)
        
        return {
            "success": success,
            "animal_id": animal_id,
            "message": "Growth measurement recorded"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/growth/{animal_id}")
def get_growth_history(animal_id: str):
    """Get growth tracking history for an animal"""
    history = db.get_growth_history(animal_id)
    return {"animal_id": animal_id, "history": history, "count": len(history)}


if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting {APP_TITLE}")
    print(f"📊 Database initialized: livestock.db")
    print(f"🤖 ML Model loaded: {_model is not None}")
    print(f"🔍 Identification system: Active")
    print(f"🏥 Health analyzer: Active")
    print(f"📡 Server running on {host}:{port}")
    
    uvicorn.run("server_enhanced:app", host=host, port=port, reload=False)
