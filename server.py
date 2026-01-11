import io
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

try:
    from tensorflow.keras.models import load_model
except Exception:  # pragma: no cover - tensorflow may be missing during lint
    load_model = None

APP_TITLE = "Livestock Health & Identification API"
MODEL_PATH = Path(__file__).parent / "mobilenetv2_image_classifier.h5"
HEALTH_LABELS = ["cognitive", "Injured", "mange"]

app = FastAPI(title=APP_TITLE, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthPrediction(BaseModel):
    label: str
    confidence: float
    scores: Dict[str, float]


class BehaviorPrediction(BaseModel):
    label: str
    scores: Dict[str, float]


class AnalysisRecord(BaseModel):
    analysis_id: str
    animal_id: str
    identifiers: Dict[str, Optional[str]]
    behavior: BehaviorPrediction
    health: HealthPrediction
    metrics: Dict[str, Optional[float]]
    notes: Optional[str]
    location: Optional[str]
    recorded_at: str


_records: List[AnalysisRecord] = []
_model = None


def _load_health_model():
    global _model
    if _model is not None or load_model is None:
        return
    if MODEL_PATH.exists():
        try:
            _model = load_model(MODEL_PATH)
        except Exception as exc:  # pragma: no cover - log and continue without model
            print(f"[WARN] Failed to load health model: {exc}")
            _model = None


_load_health_model()


def _predict_health(image_array: np.ndarray) -> HealthPrediction:
    if _model is None:
        # Fallback: use image-based heuristics when model unavailable
        return _predict_health_fallback(image_array)

    try:
        resized = cv2.resize(image_array, (224, 224))
        normalized = resized.astype("float32") / 255.0
        batch = np.expand_dims(normalized, axis=0)

        predictions = _model.predict(batch)
        scores = predictions[0]
        scores_map = {label: float(scores[idx]) for idx, label in enumerate(HEALTH_LABELS)}
        best_idx = int(np.argmax(scores))
        return HealthPrediction(label=HEALTH_LABELS[best_idx], confidence=float(scores[best_idx]), scores=scores_map)
    except Exception as exc:
        print(f"[WARN] Model prediction failed: {exc}. Using fallback.")
        return _predict_health_fallback(image_array)


def _predict_health_fallback(image_array: np.ndarray) -> HealthPrediction:
    """Fallback health classifier using simple image analysis when TF model unavailable."""
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    
    # Extract visual features
    edge_density = float(np.sum(edges > 0) / edges.size)
    brightness = float(gray.mean())
    contrast = float(gray.std())
    
    # Heuristic health scoring (cognitive = dull/low contrast, injured = irregular edges, mange = patchy/high contrast)
    scores = {
        "cognitive": max(0.1, 0.5 * (1 - contrast / 100) + 0.3 * (1 - edge_density) + 0.2 * (brightness < 100)),
        "Injured": max(0.1, 0.6 * edge_density + 0.2 * (contrast / 100) + 0.2 * (brightness < 80)),
        "mange": max(0.1, 0.5 * (contrast / 100) + 0.3 * edge_density + 0.2 * (brightness > 150)),
    }
    
    total = sum(scores.values())
    normalized = {k: v / total for k, v in scores.items()}
    best_label = max(normalized, key=normalized.get)
    confidence = float(normalized[best_label])
    
    return HealthPrediction(label=best_label, confidence=confidence, scores=normalized)


def _predict_behavior(image_array: np.ndarray) -> BehaviorPrediction:
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    texture = float(np.std(gray))

    # Simple heuristic scoring to keep the API testable without a dedicated model.
    scores = {
        "Standing": max(0.0, 0.4 * sharpness + 0.2 * texture - 0.1 * brightness),
        "Eating": max(0.0, 0.3 * brightness + 0.3 * texture),
        "Resting": max(0.0, 0.5 * (255 - brightness) + 0.1 * (50 - texture)),
    }

    total = sum(scores.values()) or 1.0
    normalized = {k: v / total for k, v in scores.items()}
    best_label = max(normalized, key=normalized.get)
    return BehaviorPrediction(label=best_label, scores=normalized)


def _build_recommendations(behavior: BehaviorPrediction, health: HealthPrediction) -> List[str]:
    recs: List[str] = []
    
    # Health-based recommendations
    if health.label == "Injured" and health.confidence > 0.4:
        recs.append(f"⚠️ Injury detected ({health.confidence*100:.0f}% confidence). Isolate and schedule veterinary examination immediately.")
    elif health.label == "mange" and health.confidence > 0.4:
        recs.append(f"⚠️ Possible mange detected ({health.confidence*100:.0f}% confidence). Quarantine animal and treat for parasitic infection.")
    elif health.label == "cognitive" and health.confidence > 0.5:
        recs.append(f"⚠️ Cognitive/behavioral issues detected ({health.confidence*100:.0f}% confidence). Monitor for signs of neurological disease or stress.")
    
    # Behavior-based recommendations
    if behavior.label == "Resting" and behavior.scores.get("Resting", 0) > 0.7:
        recs.append("Animal showing extended resting behavior. Check for lethargy, monitor water intake and body temperature.")
    elif behavior.label == "Standing" and behavior.scores.get("Standing", 0) > 0.8:
        recs.append("Animal in standing posture. Verify normal mobility and check for lameness.")
    
    # Vitals reminder
    recs.append("📋 Update daily attendance record and track weight trends over time.")
    
    if not recs or all("attendance" in r.lower() for r in recs):
        recs.insert(0, "✓ No critical health concerns detected. Continue routine monitoring.")
    
    return recs


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "model_loaded": str(_model is not None)}


@app.post("/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    animal_id: Optional[str] = Form(None),
    ear_tag_id: Optional[str] = Form(None),
    rfid: Optional[str] = Form(None),
    qr_id: Optional[str] = Form(None),
    weight_kg: Optional[float] = Form(None),
    body_temperature_c: Optional[float] = Form(None),
    heart_rate_bpm: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
):
    start = time.time()
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert("RGB")
    array = np.array(image)

    behavior = _predict_behavior(array)
    health_pred = _predict_health(array)

    analysis_id = str(uuid.uuid4())
    recorded_at = datetime.utcnow().isoformat() + "Z"

    record = AnalysisRecord(
        analysis_id=analysis_id,
        animal_id=animal_id or "unknown",
        identifiers={"earTagId": ear_tag_id, "rfid": rfid, "qrId": qr_id},
        behavior=behavior,
        health=health_pred,
        metrics={"weightKg": weight_kg, "bodyTempC": body_temperature_c, "heartRateBpm": heart_rate_bpm},
        notes=notes,
        location=location,
        recorded_at=recorded_at,
    )
    _records.append(record)

    elapsed_ms = int((time.time() - start) * 1000)
    recommendations = _build_recommendations(behavior, health_pred)

    return {
        "analysisId": analysis_id,
        "elapsedMs": elapsed_ms,
        "behavior": record.behavior.dict(),
        "health": record.health.dict(),
        "identifiers": record.identifiers,
        "animalId": record.animal_id,
        "metrics": record.metrics,
        "location": record.location,
        "notes": record.notes,
        "recordedAt": record.recorded_at,
        "recommendations": recommendations,
    }


@app.get("/records")
def records() -> Dict[str, List[AnalysisRecord]]:
    return {"items": _records[-50:]}  # return last 50 for simplicity


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
