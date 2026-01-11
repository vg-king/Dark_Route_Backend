"""
Animal identification module
Supports ear tags, QR codes, RFID, and biometric features
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple

# Try to import pyzbar for QR code detection
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] pyzbar import failed: {e}")
    print("[WARN] QR code detection will be disabled")
    PYZBAR_AVAILABLE = False
    pyzbar = None


class AnimalIdentifier:
    """Handles multiple identification methods for livestock"""

    def __init__(self):
        self.face_cascade = None
        self._load_cascades()
        self.qr_detection_available = PYZBAR_AVAILABLE

    def _load_cascades(self):
        """Load OpenCV cascades for detection"""
        try:
            # Try to load face cascade (can work for animal faces too)
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except Exception as e:
            print(f"Could not load cascades: {e}")

    def detect_qr_codes(self, image: np.ndarray) -> List[Dict]:
        """
        Detect and decode QR codes in image
        Returns list of detected QR codes with data and location
        """
        detected_codes = []
        
        # Skip QR detection if pyzbar is not available
        if not PYZBAR_AVAILABLE:
            return detected_codes
        
        try:
            # Decode QR codes
            decoded_objects = pyzbar.decode(image)
            
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                qr_type = obj.type
                
                # Get bounding box
                x, y, w, h = obj.rect
                
                detected_codes.append({
                    'type': qr_type,
                    'data': qr_data,
                    'bbox': (x, y, w, h),
                    'confidence': 0.95  # QR codes are highly reliable when detected
                })
        except Exception as e:
            print(f"[WARN] QR detection error: {e}")
        
        return detected_codes

    def detect_ear_tags(self, image: np.ndarray) -> List[Dict]:
        """
        Detect potential ear tags using color and shape detection
        Returns list of potential ear tag regions
        """
        ear_tags = []
        
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Common ear tag colors: yellow, orange, green, blue
            color_ranges = [
                # Yellow tags
                {'name': 'yellow', 'lower': np.array([20, 100, 100]), 'upper': np.array([30, 255, 255])},
                # Orange tags
                {'name': 'orange', 'lower': np.array([5, 100, 100]), 'upper': np.array([15, 255, 255])},
                # Green tags
                {'name': 'green', 'lower': np.array([40, 100, 100]), 'upper': np.array([80, 255, 255])},
                # Blue tags
                {'name': 'blue', 'lower': np.array([100, 100, 100]), 'upper': np.array([130, 255, 255])},
            ]
            
            for color_range in color_ranges:
                mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
                
                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    
                    # Filter by size (ear tags are usually visible)
                    if 500 < area < 50000:
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Aspect ratio check (tags are usually wider than tall or square)
                        aspect_ratio = float(w) / h if h > 0 else 0
                        
                        if 0.5 < aspect_ratio < 3.0:
                            ear_tags.append({
                                'color': color_range['name'],
                                'bbox': (x, y, w, h),
                                'area': area,
                                'confidence': min(0.85, 0.5 + (area / 50000) * 0.35)
                            })
            
            # Sort by confidence
            ear_tags = sorted(ear_tags, key=lambda x: x['confidence'], reverse=True)
            
        except Exception as e:
            print(f"Ear tag detection error: {e}")
        
        return ear_tags[:3]  # Return top 3 candidates

    def extract_facial_features(self, image: np.ndarray) -> Optional[Dict]:
        """
        Extract facial biometric features for identification
        Uses feature points and texture analysis
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces/heads
            if self.face_cascade:
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    # Take the largest face detected
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest_face
                    
                    # Extract face region
                    face_region = gray[y:y+h, x:x+w]
                    
                    # Compute features
                    # 1. HOG features for texture
                    face_resized = cv2.resize(face_region, (128, 128))
                    
                    # 2. Simple feature vector (histogram)
                    hist = cv2.calcHist([face_resized], [0], None, [32], [0, 256])
                    hist = cv2.normalize(hist, hist).flatten()
                    
                    # Create signature
                    signature = {
                        'bbox': (x, y, w, h),
                        'feature_vector': hist.tolist()[:32],  # First 32 bins
                        'confidence': 0.75,
                        'method': 'facial_detection'
                    }
                    
                    return signature
            
            # Fallback: use general feature extraction
            # SIFT or ORB features
            orb = cv2.ORB_create(nfeatures=50)
            keypoints, descriptors = orb.detectAndCompute(gray, None)
            
            if descriptors is not None and len(descriptors) > 0:
                # Use descriptor statistics as signature
                feature_vector = [
                    float(np.mean(descriptors)),
                    float(np.std(descriptors)),
                    float(np.median(descriptors)),
                    len(keypoints)
                ]
                
                return {
                    'bbox': (0, 0, image.shape[1], image.shape[0]),
                    'feature_vector': feature_vector,
                    'keypoint_count': len(keypoints),
                    'confidence': 0.65,
                    'method': 'orb_features'
                }
                
        except Exception as e:
            print(f"Facial feature extraction error: {e}")
        
        return None

    def extract_muzzle_pattern(self, image: np.ndarray) -> Optional[Dict]:
        """
        Extract muzzle pattern for identification (unique like fingerprints)
        Focuses on nose/muzzle region texture
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Look for the lower center region (typical muzzle location)
            h, w = gray.shape
            muzzle_region = gray[int(h*0.5):int(h*0.9), int(w*0.3):int(w*0.7)]
            
            if muzzle_region.size == 0:
                return None
            
            # Apply edge detection to capture pattern
            edges = cv2.Canny(muzzle_region, 50, 150)
            
            # Extract texture features using Local Binary Pattern concept
            # Simplified version: compute histogram of edge orientations
            
            # Calculate gradient orientations
            sobelx = cv2.Sobel(muzzle_region, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(muzzle_region, cv2.CV_64F, 0, 1, ksize=3)
            
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            orientation = np.arctan2(sobely, sobelx)
            
            # Create histogram of orientations (weighted by magnitude)
            hist, _ = np.histogram(orientation, bins=16, range=(-np.pi, np.pi), weights=magnitude)
            hist = hist / (np.sum(hist) + 1e-6)  # Normalize
            
            pattern = {
                'feature_vector': hist.tolist(),
                'edge_density': float(np.sum(edges > 0) / edges.size),
                'texture_complexity': float(np.std(muzzle_region)),
                'confidence': 0.70,
                'method': 'muzzle_pattern'
            }
            
            return pattern
            
        except Exception as e:
            print(f"Muzzle pattern extraction error: {e}")
        
        return None

    def identify_animal(self, image: np.ndarray, known_identifiers: Dict = None) -> Dict:
        """
        Comprehensive identification using all available methods
        Returns consolidated identification results
        """
        results = {
            'qr_codes': [],
            'ear_tags': [],
            'facial_features': None,
            'muzzle_pattern': None,
            'confidence_score': 0.0,
            'primary_method': None,
            'detected_identifiers': {}
        }
        
        # 1. Check QR codes (highest confidence)
        qr_codes = self.detect_qr_codes(image)
        results['qr_codes'] = qr_codes
        if qr_codes:
            results['confidence_score'] = max(results['confidence_score'], qr_codes[0]['confidence'])
            results['primary_method'] = 'qr_code'
            results['detected_identifiers']['qr_id'] = qr_codes[0]['data']
        
        # 2. Check ear tags
        ear_tags = self.detect_ear_tags(image)
        results['ear_tags'] = ear_tags
        if ear_tags and not qr_codes:
            results['confidence_score'] = max(results['confidence_score'], ear_tags[0]['confidence'])
            results['primary_method'] = 'ear_tag'
            results['detected_identifiers']['ear_tag_color'] = ear_tags[0]['color']
        
        # 3. Extract facial features
        facial_features = self.extract_facial_features(image)
        results['facial_features'] = facial_features
        if facial_features and not results['primary_method']:
            results['confidence_score'] = max(results['confidence_score'], facial_features['confidence'])
            results['primary_method'] = 'facial_biometric'
        
        # 4. Extract muzzle pattern
        muzzle_pattern = self.extract_muzzle_pattern(image)
        results['muzzle_pattern'] = muzzle_pattern
        if muzzle_pattern and not results['primary_method']:
            results['confidence_score'] = max(results['confidence_score'], muzzle_pattern['confidence'])
            results['primary_method'] = 'muzzle_biometric'
        
        # 5. Match with known identifiers if provided
        if known_identifiers:
            if known_identifiers.get('qr_id') and qr_codes:
                for qr in qr_codes:
                    if qr['data'] == known_identifiers['qr_id']:
                        results['confidence_score'] = 0.98
                        results['matched'] = True
                        break
        
        return results

    def draw_identifications(self, image: np.ndarray, identification_results: Dict) -> np.ndarray:
        """
        Draw identification markers on image for visualization
        """
        output = image.copy()
        
        # Draw QR codes
        for qr in identification_results.get('qr_codes', []):
            x, y, w, h = qr['bbox']
            cv2.rectangle(output, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(output, f"QR: {qr['data'][:20]}", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw ear tags
        for tag in identification_results.get('ear_tags', []):
            x, y, w, h = tag['bbox']
            cv2.rectangle(output, (x, y), (x+w, y+h), (0, 165, 255), 2)
            cv2.putText(output, f"Tag: {tag['color']}", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
        
        # Draw facial detection
        facial = identification_results.get('facial_features')
        if facial and 'bbox' in facial:
            x, y, w, h = facial['bbox']
            cv2.rectangle(output, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(output, "Face Detected", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return output


def compare_biometric_signatures(sig1: List[float], sig2: List[float], threshold: float = 0.85) -> Tuple[bool, float]:
    """
    Compare two biometric signatures and return match status and similarity score
    Uses cosine similarity
    """
    try:
        if not sig1 or not sig2:
            return False, 0.0
        
        # Ensure same length
        min_len = min(len(sig1), len(sig2))
        sig1 = np.array(sig1[:min_len])
        sig2 = np.array(sig2[:min_len])
        
        # Cosine similarity
        dot_product = np.dot(sig1, sig2)
        norm1 = np.linalg.norm(sig1)
        norm2 = np.linalg.norm(sig2)
        
        if norm1 == 0 or norm2 == 0:
            return False, 0.0
        
        similarity = dot_product / (norm1 * norm2)
        similarity = float(np.clip(similarity, 0, 1))
        
        is_match = similarity >= threshold
        return is_match, similarity
        
    except Exception as e:
        print(f"Signature comparison error: {e}")
        return False, 0.0
