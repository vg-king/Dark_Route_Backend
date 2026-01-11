# 🚀 Quick Start Guide - Livestock Health & Identification System

## Setup (5 minutes)

### 1. Activate Virtual Environment
```bash
cd C:\Users\KIIT0001\Downloads\Animal-Behaviour-and-Disease-Detection-main\Animal-Behaviour-and-Disease-Detection-main
.\myenv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Enhanced Server
```bash
python server_enhanced.py
```

You should see:
```
🚀 Starting Livestock Health & Identification API - Enhanced
📊 Database initialized: livestock.db
🤖 ML Model loaded: True/False
🔍 Identification system: Active
🏥 Health analyzer: Active
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 4. Open Frontend
Open `frontend/index.html` in your browser or run:
```bash
# In a new terminal
cd frontend
python -m http.server 5500
```
Then visit: http://localhost:5500

---

## 🎯 Quick Test

### Test 1: Health Check
```bash
curl http://localhost:8080/health
```
Expected: `{"status": "ok", ...}`

### Test 2: Register an Animal
```bash
curl -X POST http://localhost:8080/animals/register \
  -F "animal_id=COW-001" \
  -F "species=cattle" \
  -F "breed=Holstein" \
  -F "ear_tag_id=TAG-001"
```

### Test 3: Analyze Image
Using the frontend:
1. Click "Animal Image" and select any livestock photo
2. Fill in "Animal ID": COW-001
3. (Optional) Add vitals: weight, temperature, heart rate
4. Click "Analyze"

You'll see:
- ✅ Identification results (QR, ear tags, biometrics)
- 📊 Behavior classification (Standing/Eating/Resting/Walking)
- 🏥 Health assessment with body condition score
- ⚠️ Lameness detection
- 🔍 Symptom detection
- 📋 Recommendations
- ✅ Attendance auto-marked

---

## 📊 View Data

### Check Database
```bash
sqlite3 livestock.db
```
```sql
.tables
SELECT * FROM animals;
SELECT * FROM health_records;
SELECT * FROM attendance WHERE attendance_date = date('now');
.quit
```

### API Endpoints
- **Animals**: http://localhost:8080/animals
- **Records**: http://localhost:8080/records
- **Attendance**: http://localhost:8080/attendance
- **Statistics**: http://localhost:8080/statistics

---

## ⚡ Features

✅ **Zero Mock Data** - Everything is real:
- Real QR code detection (pyzbar)
- Real ear tag detection (OpenCV)
- Real biometric extraction (facial/muzzle)
- Real SQLite database (livestock.db)
- Real health analysis (body condition, lameness, symptoms)
- Real attendance tracking

✅ **Multi-Species**:
- Cattle, buffaloes, goats, sheep, pigs, camels

✅ **Identification**:
- QR codes on collars
- Ear tags (colored)
- RFID (manual entry)
- Facial biometrics
- Muzzle patterns

✅ **Health Analysis**:
- Body condition score (1-5)
- Lameness detection
- Symptom detection (lesions, discharge, coat)
- Vitals validation
- Disease classification (if ML model available)

✅ **Attendance**:
- Auto-marked on analysis
- Daily reports
- Detection method logged

---

## 🐛 Troubleshooting

### Port 8080 in use?
```python
# Edit server_enhanced.py line ~450
uvicorn.run("server_enhanced:app", host="0.0.0.0", port=8081, reload=True)
```

### TensorFlow not installed?
System works without it using heuristic analysis. To install:
```bash
pip install tensorflow
```

### pyzbar DLL error (Windows)?
Download Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 📖 Full Documentation

See [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) for:
- Complete feature list
- Testing procedures
- API documentation
- Database schema
- Troubleshooting guide

---

## 🎉 You're Ready!

The system is fully functional with zero mock data. All analysis, identification, and database operations are real.

**Next Steps**:
1. Test with your own livestock images
2. Register multiple animals
3. Track growth over time
4. Monitor daily attendance
5. Review health trends

**Questions?** Check the comprehensive [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)
