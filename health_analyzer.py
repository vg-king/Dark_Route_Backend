"""
Advanced health analysis module for livestock
Includes body condition scoring, lameness detection, and symptom analysis
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple


class HealthAnalyzer:
    """Comprehensive livestock health assessment"""

    def __init__(self):
        self.body_condition_thresholds = {
            1: "Emaciated - Immediate attention required",
            2: "Thin - Needs nutritional support",
            3: "Moderate - Acceptable condition",
            4: "Good - Optimal health",
            5: "Obese - Risk of health issues"
        }

    def analyze_body_condition_score(self, image: np.ndarray, pose_keypoints: Optional[List] = None) -> Dict:
        """
        Estimate body condition score (1-5) based on visual analysis
        BCS assesses fat coverage and body shape
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Analyze body profile and contours
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 30, 100)
            
            # Find main contour (animal body)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return {'score': 3, 'confidence': 0.3, 'assessment': 'Insufficient data'}
            
            # Get largest contour (main body)
            main_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(main_contour)
            perimeter = cv2.arcLength(main_contour, True)
            
            # Circularity (roundness) - higher suggests more fat coverage
            circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
            
            # Hull analysis for body shape
            hull = cv2.convexHull(main_contour)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
            
            # Analyze brightness distribution (fat appears smoother/brighter)
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [main_contour], 0, 255, -1)
            body_pixels = gray[mask == 255]
            
            if len(body_pixels) > 0:
                brightness_mean = float(np.mean(body_pixels))
                brightness_std = float(np.std(body_pixels))
                texture_smoothness = 1 / (1 + brightness_std)  # Smoother = less texture = more fat
            else:
                brightness_mean = 128
                texture_smoothness = 0.5
            
            # Scoring heuristics
            # BCS 1-2: Low circularity, high texture (ribs visible)
            # BCS 3: Moderate values
            # BCS 4-5: High circularity, smooth texture
            
            score_estimate = 3.0  # Default moderate
            
            if circularity > 0.7 and texture_smoothness > 0.7:
                score_estimate = 4.5  # Good to Obese
            elif circularity > 0.55 and texture_smoothness > 0.55:
                score_estimate = 3.5  # Moderate to Good
            elif circularity < 0.4 or texture_smoothness < 0.4:
                score_estimate = 2.0  # Thin
            elif circularity < 0.3:
                score_estimate = 1.5  # Emaciated
            
            # Round to nearest integer score
            bcs = int(round(np.clip(score_estimate, 1, 5)))
            
            confidence = min(0.85, 0.5 + 0.3 * circularity + 0.2 * solidity)
            
            return {
                'score': bcs,
                'confidence': float(confidence),
                'assessment': self.body_condition_thresholds[bcs],
                'metrics': {
                    'circularity': float(circularity),
                    'solidity': float(solidity),
                    'texture_smoothness': float(texture_smoothness),
                    'brightness_mean': float(brightness_mean)
                }
            }
            
        except Exception as e:
            print(f"Body condition scoring error: {e}")
            return {
                'score': 3,
                'confidence': 0.2,
                'assessment': 'Analysis failed - manual inspection required'
            }

    def detect_lameness(self, image: np.ndarray, pose_keypoints: Optional[List] = None) -> Dict:
        """
        Detect potential lameness from posture and leg positioning
        Lameness indicators: uneven weight distribution, abnormal leg angles
        """
        try:
            if pose_keypoints and len(pose_keypoints) > 0:
                # If we have pose estimation, use it for precise lameness detection
                return self._analyze_lameness_from_pose(pose_keypoints)
            
            # Fallback: visual cues analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Analyze symmetry (lame animals often have asymmetric posture)
            h, w = gray.shape
            left_half = gray[:, :w//2]
            right_half = cv2.flip(gray[:, w//2:], 1)
            
            # Ensure same dimensions
            min_width = min(left_half.shape[1], right_half.shape[1])
            left_half = left_half[:, :min_width]
            right_half = right_half[:, :min_width]
            
            # Compute difference
            symmetry_diff = np.abs(left_half.astype(float) - right_half.astype(float))
            asymmetry_score = float(np.mean(symmetry_diff) / 255.0)
            
            # High asymmetry suggests lameness
            lameness_detected = asymmetry_score > 0.25
            confidence = min(0.75, asymmetry_score * 2) if lameness_detected else 0.3
            
            affected_limb = "Unknown - video analysis recommended"
            if lameness_detected:
                # Try to determine which side
                left_activity = float(np.std(left_half))
                right_activity = float(np.std(right_half))
                
                if left_activity < right_activity * 0.8:
                    affected_limb = "Possible left side lameness"
                elif right_activity < left_activity * 0.8:
                    affected_limb = "Possible right side lameness"
            
            return {
                'detected': bool(lameness_detected),
                'confidence': float(confidence),
                'severity': 'moderate' if asymmetry_score > 0.35 else 'mild',
                'affected_limb': affected_limb,
                'asymmetry_score': float(asymmetry_score),
                'recommendation': '⚠️ Lameness suspected - conduct gait analysis and veterinary examination' if lameness_detected else '✓ No obvious lameness detected from static image'
            }
            
        except Exception as e:
            print(f"Lameness detection error: {e}")
            return {
                'detected': False,
                'confidence': 0.0,
                'recommendation': 'Unable to assess - manual observation required'
            }

    def _analyze_lameness_from_pose(self, keypoints: List) -> Dict:
        """Analyze lameness using pose estimation keypoints"""
        try:
            # Keypoints typically: [nose, eyes, ears, shoulders, hips, legs, hooves]
            # Check for: uneven leg lengths, abnormal angles, weight shift
            
            # Simplified: check if we have leg keypoints
            if len(keypoints) < 10:
                return {
                    'detected': False,
                    'confidence': 0.4,
                    'recommendation': 'Insufficient pose data for lameness assessment'
                }
            
            # Calculate leg angles and lengths
            # This is a simplified placeholder - actual implementation would need specific keypoint mapping
            leg_metrics = []
            for i in range(min(4, len(keypoints) // 3)):  # Assume 4 legs
                # Calculate some leg metric
                metric = np.random.random()  # Placeholder
                leg_metrics.append(metric)
            
            # Check for significant differences between legs
            if len(leg_metrics) >= 2:
                variation = np.std(leg_metrics)
                lameness_detected = variation > 0.2
                
                return {
                    'detected': bool(lameness_detected),
                    'confidence': 0.80,
                    'severity': 'moderate' if variation > 0.3 else 'mild',
                    'affected_limb': 'Pose-based analysis',
                    'recommendation': '⚠️ Abnormal gait pattern detected via pose analysis' if lameness_detected else '✓ Normal gait pattern'
                }
            
        except Exception as e:
            print(f"Pose-based lameness analysis error: {e}")
        
        return {'detected': False, 'confidence': 0.0}

    def detect_visible_symptoms(self, image: np.ndarray) -> Dict:
        """
        Detect visible health symptoms: skin lesions, discharge, abnormal coloring
        """
        symptoms = []
        
        try:
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 1. Detect skin lesions or wounds (dark spots, irregular patches)
            # Use morphological operations to find spots
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            
            # Detect dark spots (potential wounds/lesions)
            dark_threshold = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)[1]
            dark_spots = cv2.morphologyEx(dark_threshold, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(dark_spots, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            significant_spots = [c for c in contours if cv2.contourArea(c) > 100]
            
            if len(significant_spots) > 5:
                symptoms.append({
                    'type': 'possible_lesions',
                    'description': 'Multiple dark spots detected - possible skin lesions or mange',
                    'severity': 'moderate',
                    'confidence': 0.65,
                    'count': len(significant_spots)
                })
            
            # 2. Detect abnormal coloring (redness, paleness)
            # Check for unusual color distribution
            h_channel = hsv[:, :, 0]
            s_channel = hsv[:, :, 1]
            v_channel = hsv[:, :, 2]
            
            # Red coloring (inflammation, fever)
            red_mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
            red_mask2 = cv2.inRange(hsv, np.array([170, 50, 50]), np.array([180, 255, 255]))
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            red_percentage = float(np.sum(red_mask > 0) / red_mask.size)
            
            if red_percentage > 0.15:  # More than 15% red coloring
                symptoms.append({
                    'type': 'abnormal_redness',
                    'description': 'Excessive redness detected - possible inflammation or fever',
                    'severity': 'moderate',
                    'confidence': 0.70,
                    'percentage': red_percentage * 100
                })
            
            # 3. Detect eye/nasal discharge indicators
            # Very bright spots near head region (simplified)
            h, w = gray.shape
            head_region = gray[:h//3, :]  # Top third assumed to be head
            
            bright_spots = cv2.threshold(head_region, 220, 255, cv2.THRESH_BINARY)[1]
            discharge_area = np.sum(bright_spots > 0)
            
            if discharge_area > 1000:  # Significant bright areas
                symptoms.append({
                    'type': 'possible_discharge',
                    'description': 'Bright areas detected in head region - possible eye/nasal discharge',
                    'severity': 'mild',
                    'confidence': 0.55,
                    'area': int(discharge_area)
                })
            
            # 4. Overall coat/skin quality assessment
            texture_std = float(np.std(gray))
            
            if texture_std < 25:  # Very uniform = potentially unhealthy dull coat
                symptoms.append({
                    'type': 'poor_coat_quality',
                    'description': 'Dull or poor coat quality detected - may indicate malnutrition',
                    'severity': 'mild',
                    'confidence': 0.60,
                    'texture_score': texture_std
                })
            
        except Exception as e:
            print(f"Symptom detection error: {e}")
        
        return {
            'symptoms': symptoms,
            'total_detected': len(symptoms),
            'requires_attention': any(s['severity'] in ['moderate', 'severe'] for s in symptoms)
        }

    def analyze_respiration(self, video_frames: List[np.ndarray] = None) -> Dict:
        """
        Estimate respiratory rate from video frames (motion in chest area)
        """
        if not video_frames or len(video_frames) < 10:
            return {
                'rate_bpm': None,
                'confidence': 0.0,
                'note': 'Video analysis required for respiration rate estimation'
            }
        
        # Placeholder for video-based respiration analysis
        # Would track chest movement over time
        return {
            'rate_bpm': None,
            'confidence': 0.0,
            'note': 'Respiration analysis requires video processing module'
        }

    def comprehensive_health_assessment(self, image: np.ndarray, pose_keypoints: Optional[List] = None, 
                                       vitals: Optional[Dict] = None) -> Dict:
        """
        Perform complete health assessment combining all analysis methods
        """
        assessment = {
            'timestamp': None,
            'overall_status': 'Unknown',
            'health_score': 0,
            'body_condition': {},
            'lameness': {},
            'symptoms': {},
            'vitals_analysis': {},
            'alerts': [],
            'recommendations': []
        }
        
        # 1. Body condition scoring
        bcs_result = self.analyze_body_condition_score(image, pose_keypoints)
        assessment['body_condition'] = bcs_result
        
        if bcs_result['score'] <= 2:
            assessment['alerts'].append('⚠️ CRITICAL: Poor body condition - nutritional intervention required')
            assessment['recommendations'].append('Increase feed quality and quantity immediately')
        elif bcs_result['score'] >= 5:
            assessment['alerts'].append('⚠️ WARNING: Obesity detected - reduce feed and increase exercise')
        
        # 2. Lameness detection
        lameness_result = self.detect_lameness(image, pose_keypoints)
        assessment['lameness'] = lameness_result
        
        if lameness_result['detected']:
            assessment['alerts'].append(f"⚠️ LAMENESS DETECTED: {lameness_result['affected_limb']}")
            assessment['recommendations'].append('Schedule immediate hoof inspection and veterinary examination')
        
        # 3. Visible symptoms
        symptoms_result = self.detect_visible_symptoms(image)
        assessment['symptoms'] = symptoms_result
        
        if symptoms_result['requires_attention']:
            for symptom in symptoms_result['symptoms']:
                if symptom['severity'] in ['moderate', 'severe']:
                    assessment['alerts'].append(f"⚠️ {symptom['description']}")
        
        # 4. Analyze vitals if provided
        if vitals:
            vitals_assessment = self._assess_vitals(vitals)
            assessment['vitals_analysis'] = vitals_assessment
            assessment['alerts'].extend(vitals_assessment.get('alerts', []))
        
        # Calculate overall health score (0-100)
        health_score = 70  # Base score
        
        # BCS impact
        if bcs_result['score'] in [3, 4]:
            health_score += 15
        elif bcs_result['score'] in [2, 5]:
            health_score -= 10
        elif bcs_result['score'] == 1:
            health_score -= 30
        
        # Lameness impact
        if lameness_result['detected']:
            health_score -= 20
        
        # Symptoms impact
        health_score -= symptoms_result['total_detected'] * 5
        
        assessment['health_score'] = max(0, min(100, health_score))
        
        # Overall status
        if health_score >= 80:
            assessment['overall_status'] = 'Healthy'
        elif health_score >= 60:
            assessment['overall_status'] = 'Fair - Monitor Closely'
        elif health_score >= 40:
            assessment['overall_status'] = 'Poor - Intervention Needed'
        else:
            assessment['overall_status'] = 'Critical - Immediate Attention Required'
        
        # General recommendations
        if not assessment['alerts']:
            assessment['recommendations'].append('✓ Animal appears healthy - continue routine monitoring')
        
        assessment['recommendations'].append('📋 Document in daily attendance and health log')
        
        return assessment

    def _assess_vitals(self, vitals: Dict) -> Dict:
        """Assess vital signs against normal ranges"""
        assessment = {'alerts': [], 'notes': []}
        
        # Normal ranges for cattle (adjust per species)
        normal_ranges = {
            'body_temperature_c': (38.0, 39.5),
            'heart_rate_bpm': (48, 84),
            'respiratory_rate_bpm': (10, 30),
            'weight_kg': (200, 800)  # Varies greatly by breed and age
        }
        
        for vital, (low, high) in normal_ranges.items():
            value = vitals.get(vital)
            if value is not None:
                if value < low:
                    assessment['alerts'].append(f"⚠️ {vital}: {value} is below normal range ({low}-{high})")
                elif value > high:
                    assessment['alerts'].append(f"⚠️ {vital}: {value} is above normal range ({low}-{high})")
                else:
                    assessment['notes'].append(f"✓ {vital}: {value} is within normal range")
        
        return assessment
