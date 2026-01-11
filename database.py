"""
Database module for livestock management system
Handles SQLite operations for animals, health records, attendance, and analytics
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


class LivestockDatabase:
    def __init__(self, db_path: str = "livestock.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self.initialize_database()

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def initialize_database(self):
        """Create all necessary tables"""
        conn = self.connect()
        cursor = conn.cursor()

        # Animals master table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id TEXT UNIQUE NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                date_of_birth DATE,
                gender TEXT,
                ear_tag_id TEXT UNIQUE,
                rfid TEXT UNIQUE,
                qr_id TEXT UNIQUE,
                facial_signature TEXT,
                muzzle_signature TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_location TEXT,
                status TEXT DEFAULT 'active',
                notes TEXT
            )
        """)

        # Health records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT UNIQUE NOT NULL,
                animal_id TEXT NOT NULL,
                health_status TEXT NOT NULL,
                health_confidence REAL,
                health_scores TEXT,
                behavior_status TEXT,
                behavior_scores TEXT,
                weight_kg REAL,
                body_temperature_c REAL,
                heart_rate_bpm INTEGER,
                respiratory_rate INTEGER,
                body_condition_score INTEGER,
                lameness_detected BOOLEAN DEFAULT 0,
                posture_issues TEXT,
                visible_injuries TEXT,
                symptoms TEXT,
                recommendations TEXT,
                veterinarian_notes TEXT,
                treatment_prescribed TEXT,
                image_path TEXT,
                location TEXT,
                recorded_by TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animals(animal_id)
            )
        """)

        # Attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id TEXT NOT NULL,
                attendance_date DATE NOT NULL,
                check_in_time TIME,
                location TEXT,
                detection_method TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animals(animal_id),
                UNIQUE(animal_id, attendance_date)
            )
        """)

        # Growth tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS growth_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id TEXT NOT NULL,
                measurement_date DATE NOT NULL,
                weight_kg REAL,
                height_cm REAL,
                length_cm REAL,
                girth_cm REAL,
                body_condition_score INTEGER,
                notes TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animals(animal_id)
            )
        """)

        # Identification events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS identification_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id TEXT,
                detection_method TEXT NOT NULL,
                identifier_value TEXT,
                confidence REAL,
                image_path TEXT,
                location TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def register_animal(self, animal_data: Dict) -> str:
        """Register a new animal in the system"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO animals (
                animal_id, species, breed, date_of_birth, gender,
                ear_tag_id, rfid, qr_id, facial_signature, muzzle_signature,
                current_location, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            animal_data.get('animal_id'),
            animal_data.get('species', 'cattle'),
            animal_data.get('breed'),
            animal_data.get('date_of_birth'),
            animal_data.get('gender'),
            animal_data.get('ear_tag_id'),
            animal_data.get('rfid'),
            animal_data.get('qr_id'),
            animal_data.get('facial_signature'),
            animal_data.get('muzzle_signature'),
            animal_data.get('current_location'),
            animal_data.get('notes')
        ))

        conn.commit()
        animal_id = animal_data.get('animal_id')
        conn.close()
        return animal_id

    def add_health_record(self, record: Dict) -> str:
        """Add a health analysis record"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO health_records (
                analysis_id, animal_id, health_status, health_confidence, health_scores,
                behavior_status, behavior_scores, weight_kg, body_temperature_c,
                heart_rate_bpm, respiratory_rate, body_condition_score, lameness_detected,
                posture_issues, visible_injuries, symptoms, recommendations,
                veterinarian_notes, treatment_prescribed, image_path, location, recorded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get('analysis_id'),
            record.get('animal_id'),
            record.get('health_status'),
            record.get('health_confidence'),
            json.dumps(record.get('health_scores', {})),
            record.get('behavior_status'),
            json.dumps(record.get('behavior_scores', {})),
            record.get('weight_kg'),
            record.get('body_temperature_c'),
            record.get('heart_rate_bpm'),
            record.get('respiratory_rate'),
            record.get('body_condition_score'),
            record.get('lameness_detected', False),
            record.get('posture_issues'),
            record.get('visible_injuries'),
            record.get('symptoms'),
            json.dumps(record.get('recommendations', [])),
            record.get('veterinarian_notes'),
            record.get('treatment_prescribed'),
            record.get('image_path'),
            record.get('location'),
            record.get('recorded_by')
        ))

        conn.commit()
        conn.close()
        return record.get('analysis_id')

    def mark_attendance(self, animal_id: str, location: str = None, detection_method: str = "manual") -> bool:
        """Mark daily attendance for an animal"""
        conn = self.connect()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        try:
            cursor.execute("""
                INSERT INTO attendance (animal_id, attendance_date, check_in_time, location, detection_method)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(animal_id, attendance_date) DO UPDATE SET
                    check_in_time = excluded.check_in_time,
                    location = excluded.location,
                    detection_method = excluded.detection_method
            """, (animal_id, today, datetime.now().time(), location, detection_method))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Attendance marking failed: {e}")
            conn.close()
            return False

    def get_animal(self, animal_id: str = None, ear_tag: str = None, rfid: str = None, qr_id: str = None) -> Optional[Dict]:
        """Retrieve animal by any identifier"""
        conn = self.connect()
        cursor = conn.cursor()

        if animal_id:
            cursor.execute("SELECT * FROM animals WHERE animal_id = ?", (animal_id,))
        elif ear_tag:
            cursor.execute("SELECT * FROM animals WHERE ear_tag_id = ?", (ear_tag,))
        elif rfid:
            cursor.execute("SELECT * FROM animals WHERE rfid = ?", (rfid,))
        elif qr_id:
            cursor.execute("SELECT * FROM animals WHERE qr_id = ?", (qr_id,))
        else:
            conn.close()
            return None

        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None

    def get_health_records(self, animal_id: str, limit: int = 50) -> List[Dict]:
        """Get health history for an animal"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM health_records 
            WHERE animal_id = ? 
            ORDER BY recorded_at DESC 
            LIMIT ?
        """, (animal_id, limit))

        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_all_animals(self, status: str = "active") -> List[Dict]:
        """Get all animals with optional status filter"""
        conn = self.connect()
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM animals WHERE status = ? ORDER BY registration_date DESC", (status,))
        else:
            cursor.execute("SELECT * FROM animals ORDER BY registration_date DESC")

        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_attendance_report(self, date: str = None) -> List[Dict]:
        """Get attendance report for a specific date or today"""
        conn = self.connect()
        cursor = conn.cursor()

        target_date = date or datetime.now().date()
        
        cursor.execute("""
            SELECT a.animal_id, a.species, a.breed, a.current_location,
                   att.check_in_time, att.location as attendance_location,
                   att.detection_method
            FROM animals a
            LEFT JOIN attendance att ON a.animal_id = att.animal_id 
                AND att.attendance_date = ?
            WHERE a.status = 'active'
            ORDER BY att.check_in_time DESC
        """, (target_date,))

        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_recent_records(self, limit: int = 50) -> List[Dict]:
        """Get most recent health records across all animals"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT hr.*, a.species, a.breed 
            FROM health_records hr
            JOIN animals a ON hr.animal_id = a.animal_id
            ORDER BY hr.recorded_at DESC 
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            rec = dict(row)
            if rec.get('health_scores'):
                rec['health_scores'] = json.loads(rec['health_scores'])
            if rec.get('behavior_scores'):
                rec['behavior_scores'] = json.loads(rec['behavior_scores'])
            if rec.get('recommendations'):
                rec['recommendations'] = json.loads(rec['recommendations'])
            records.append(rec)
        
        return records

    def add_growth_measurement(self, animal_id: str, measurements: Dict) -> bool:
        """Add growth tracking measurement"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO growth_tracking (
                animal_id, measurement_date, weight_kg, height_cm, 
                length_cm, girth_cm, body_condition_score, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            animal_id,
            measurements.get('measurement_date', datetime.now().date()),
            measurements.get('weight_kg'),
            measurements.get('height_cm'),
            measurements.get('length_cm'),
            measurements.get('girth_cm'),
            measurements.get('body_condition_score'),
            measurements.get('notes')
        ))

        conn.commit()
        conn.close()
        return True

    def get_growth_history(self, animal_id: str) -> List[Dict]:
        """Get growth tracking history"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM growth_tracking 
            WHERE animal_id = ? 
            ORDER BY measurement_date ASC
        """, (animal_id,))

        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def log_identification_event(self, event: Dict) -> bool:
        """Log an identification detection event"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO identification_events (
                animal_id, detection_method, identifier_value, 
                confidence, image_path, location
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event.get('animal_id'),
            event.get('detection_method'),
            event.get('identifier_value'),
            event.get('confidence'),
            event.get('image_path'),
            event.get('location')
        ))

        conn.commit()
        conn.close()
        return True

    def get_statistics(self) -> Dict:
        """Get overall system statistics"""
        conn = self.connect()
        cursor = conn.cursor()

        stats = {}

        # Total animals
        cursor.execute("SELECT COUNT(*) as count FROM animals WHERE status = 'active'")
        stats['total_active_animals'] = cursor.fetchone()['count']

        # Today's attendance
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE attendance_date = ?", (today,))
        stats['todays_attendance'] = cursor.fetchone()['count']

        # Health alerts (recent concerning cases)
        cursor.execute("""
            SELECT COUNT(*) as count FROM health_records 
            WHERE health_status IN ('Injured', 'mange') 
            AND health_confidence > 0.4
            AND DATE(recorded_at) >= DATE('now', '-7 days')
        """)
        stats['recent_health_alerts'] = cursor.fetchone()['count']

        # Total records
        cursor.execute("SELECT COUNT(*) as count FROM health_records")
        stats['total_health_records'] = cursor.fetchone()['count']

        conn.close()
        return stats
