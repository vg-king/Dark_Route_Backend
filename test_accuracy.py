"""
Model Accuracy Refinement and Testing System
Tests health analysis and identification models with JSON data
Includes accuracy scoring and model tuning
"""

import json
import time
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path

# Enhanced health analysis with refined algorithms
class EnhancedHealthAnalyzer:
    """Refined health analyzer with improved accuracy"""
    
    def __init__(self):
        self.accuracy_scores = {
            'body_condition': [],
            'lameness': [],
            'symptoms': [],
            'overall': []
        }
        
    def analyze_body_condition_refined(self, metrics: Dict) -> Dict:
        """
        Refined body condition scoring with multiple indicators
        Accuracy target: >85%
        """
        # Extract metrics
        circularity = metrics.get('circularity', 0.5)
        solidity = metrics.get('solidity', 0.7)
        texture_smoothness = metrics.get('texture_smoothness', 0.5)
        brightness_mean = metrics.get('brightness_mean', 128)
        
        # Weight distribution for scoring (refined weights)
        score = 0.0
        confidence = 0.0
        
        # Circularity contribution (35% weight)
        if circularity > 0.75:
            score += 4.5 * 0.35
            confidence += 0.35
        elif circularity > 0.65:
            score += 4.0 * 0.35
            confidence += 0.32
        elif circularity > 0.55:
            score += 3.5 * 0.35
            confidence += 0.30
        elif circularity > 0.45:
            score += 3.0 * 0.35
            confidence += 0.25
        elif circularity > 0.35:
            score += 2.5 * 0.35
            confidence += 0.22
        else:
            score += 1.5 * 0.35
            confidence += 0.18
        
        # Texture smoothness (30% weight)
        if texture_smoothness > 0.75:
            score += 4.5 * 0.30
            confidence += 0.30
        elif texture_smoothness > 0.60:
            score += 3.5 * 0.30
            confidence += 0.28
        elif texture_smoothness > 0.45:
            score += 3.0 * 0.30
            confidence += 0.25
        else:
            score += 2.0 * 0.30
            confidence += 0.20
        
        # Solidity (20% weight)
        if solidity > 0.85:
            score += 4.0 * 0.20
            confidence += 0.20
        elif solidity > 0.75:
            score += 3.5 * 0.20
            confidence += 0.18
        elif solidity > 0.65:
            score += 3.0 * 0.20
            confidence += 0.16
        else:
            score += 2.5 * 0.20
            confidence += 0.14
        
        # Brightness (15% weight)
        brightness_score = 3.0  # Default
        if brightness_mean > 160:
            brightness_score = 4.0
        elif brightness_mean > 140:
            brightness_score = 3.5
        elif brightness_mean < 100:
            brightness_score = 2.5
        elif brightness_mean < 80:
            brightness_score = 2.0
        
        score += brightness_score * 0.15
        confidence += 0.15
        
        # Final score (1-5)
        final_score = int(round(np.clip(score, 1, 5)))
        final_confidence = min(0.95, confidence)
        
        assessment_map = {
            1: "Emaciated - Immediate veterinary attention required",
            2: "Thin - Needs nutritional support and monitoring",
            3: "Moderate - Acceptable condition, maintain diet",
            4: "Good - Optimal health condition",
            5: "Obese - Risk of health issues, reduce feed"
        }
        
        return {
            'score': final_score,
            'confidence': float(final_confidence),
            'assessment': assessment_map[final_score],
            'metrics': {
                'circularity': float(circularity),
                'solidity': float(solidity),
                'texture_smoothness': float(texture_smoothness),
                'brightness_mean': float(brightness_mean)
            }
        }
    
    def detect_lameness_refined(self, metrics: Dict) -> Dict:
        """
        Refined lameness detection with better accuracy
        Accuracy target: >80%
        """
        asymmetry_score = metrics.get('asymmetry_score', 0.15)
        left_activity = metrics.get('left_activity', 50)
        right_activity = metrics.get('right_activity', 50)
        posture_deviation = metrics.get('posture_deviation', 0.1)
        
        # Multi-factor lameness scoring
        lameness_score = 0.0
        
        # Asymmetry factor (40% weight)
        if asymmetry_score > 0.35:
            lameness_score += 0.40
            severity = 'severe'
        elif asymmetry_score > 0.25:
            lameness_score += 0.35
            severity = 'moderate'
        elif asymmetry_score > 0.18:
            lameness_score += 0.25
            severity = 'mild'
        else:
            severity = 'none'
        
        # Activity difference (35% weight)
        activity_diff = abs(left_activity - right_activity) / max(left_activity, right_activity, 1)
        if activity_diff > 0.25:
            lameness_score += 0.35
        elif activity_diff > 0.15:
            lameness_score += 0.25
        
        # Posture deviation (25% weight)
        if posture_deviation > 0.20:
            lameness_score += 0.25
        elif posture_deviation > 0.12:
            lameness_score += 0.15
        
        # Determine affected limb
        affected_limb = "Unknown"
        if lameness_score > 0.3:
            if left_activity < right_activity * 0.85:
                affected_limb = "Left side (probable)"
            elif right_activity < left_activity * 0.85:
                affected_limb = "Right side (probable)"
            else:
                affected_limb = "Both sides or hind legs"
        
        lameness_detected = lameness_score > 0.25
        confidence = min(0.90, lameness_score + 0.20) if lameness_detected else 0.35
        
        recommendation = (
            f"⚠️ {severity.capitalize()} lameness detected - "
            f"Conduct gait analysis and veterinary examination"
            if lameness_detected else
            "✓ No significant lameness detected from analysis"
        )
        
        return {
            'detected': bool(lameness_detected),
            'confidence': float(confidence),
            'severity': severity,
            'lameness_score': float(lameness_score),
            'affected_limb': affected_limb,
            'asymmetry_score': float(asymmetry_score),
            'activity_difference': float(activity_diff),
            'recommendation': recommendation
        }
    
    def detect_symptoms_refined(self, metrics: Dict) -> Dict:
        """
        Refined symptom detection with improved accuracy
        Accuracy target: >75%
        """
        symptoms = []
        
        # Lesion detection (refined thresholds)
        dark_spots_count = metrics.get('dark_spots_count', 0)
        if dark_spots_count > 8:
            symptoms.append({
                'type': 'severe_lesions',
                'description': 'Multiple significant dark spots detected - possible severe skin lesions or mange',
                'severity': 'severe',
                'confidence': 0.75,
                'count': dark_spots_count
            })
        elif dark_spots_count > 5:
            symptoms.append({
                'type': 'moderate_lesions',
                'description': 'Several dark spots detected - possible skin lesions or parasitic infection',
                'severity': 'moderate',
                'confidence': 0.68,
                'count': dark_spots_count
            })
        
        # Color abnormality detection
        red_percentage = metrics.get('red_percentage', 0.0)
        if red_percentage > 0.20:
            symptoms.append({
                'type': 'severe_inflammation',
                'description': 'Significant redness detected - possible severe inflammation, fever, or infection',
                'severity': 'severe',
                'confidence': 0.78,
                'percentage': red_percentage * 100
            })
        elif red_percentage > 0.12:
            symptoms.append({
                'type': 'moderate_inflammation',
                'description': 'Moderate redness detected - possible inflammation or mild fever',
                'severity': 'moderate',
                'confidence': 0.70,
                'percentage': red_percentage * 100
            })
        
        # Discharge detection (refined)
        discharge_area = metrics.get('discharge_area', 0)
        if discharge_area > 2000:
            symptoms.append({
                'type': 'significant_discharge',
                'description': 'Significant bright areas in head region - likely eye/nasal discharge',
                'severity': 'moderate',
                'confidence': 0.65,
                'area': int(discharge_area)
            })
        elif discharge_area > 800:
            symptoms.append({
                'type': 'possible_discharge',
                'description': 'Bright areas detected in head region - possible eye/nasal discharge',
                'severity': 'mild',
                'confidence': 0.58,
                'area': int(discharge_area)
            })
        
        # Coat quality (refined)
        texture_std = metrics.get('texture_std', 30)
        if texture_std < 20:
            symptoms.append({
                'type': 'poor_coat',
                'description': 'Dull or very poor coat quality - may indicate malnutrition or illness',
                'severity': 'moderate',
                'confidence': 0.72,
                'texture_score': float(texture_std)
            })
        elif texture_std < 25:
            symptoms.append({
                'type': 'fair_coat',
                'description': 'Somewhat dull coat quality - monitor nutrition',
                'severity': 'mild',
                'confidence': 0.62,
                'texture_score': float(texture_std)
            })
        
        requires_attention = any(s['severity'] in ['moderate', 'severe'] for s in symptoms)
        
        return {
            'symptoms': symptoms,
            'total_detected': len(symptoms),
            'requires_attention': requires_attention,
            'highest_severity': max([s['severity'] for s in symptoms], default='none', 
                                   key=lambda x: {'severe': 3, 'moderate': 2, 'mild': 1, 'none': 0}[x])
        }
    
    def calculate_accuracy_score(self, predicted: Dict, ground_truth: Dict) -> float:
        """Calculate accuracy score comparing prediction to ground truth"""
        score = 0.0
        total_weight = 0.0
        
        # Body condition accuracy (35% weight)
        if 'body_condition' in ground_truth:
            gt_bcs = ground_truth['body_condition']
            pred_bcs = predicted.get('score', 3)
            diff = abs(gt_bcs - pred_bcs)
            accuracy = max(0, 1 - (diff / 4))  # Max difference is 4
            score += accuracy * 0.35
            total_weight += 0.35
        
        # Lameness accuracy (35% weight)
        if 'lameness_present' in ground_truth:
            gt_lame = ground_truth['lameness_present']
            pred_lame = predicted.get('detected', False)
            if gt_lame == pred_lame:
                score += 0.35
            total_weight += 0.35
        
        # Symptom count accuracy (30% weight)
        if 'symptom_count' in ground_truth:
            gt_count = ground_truth['symptom_count']
            pred_count = predicted.get('total_detected', 0)
            diff = abs(gt_count - pred_count)
            accuracy = max(0, 1 - (diff / 5))  # Max reasonable difference
            score += accuracy * 0.30
            total_weight += 0.30
        
        return (score / total_weight * 100) if total_weight > 0 else 0.0


class ModelTester:
    """Comprehensive model testing with JSON test cases"""
    
    def __init__(self):
        self.analyzer = EnhancedHealthAnalyzer()
        self.test_results = []
        
    def load_test_cases(self) -> List[Dict]:
        """Load test cases from JSON"""
        test_cases = [
            # Test Case 1: Healthy cattle
            {
                'name': 'Healthy_Cattle_1',
                'input': {
                    'circularity': 0.72,
                    'solidity': 0.85,
                    'texture_smoothness': 0.68,
                    'brightness_mean': 145,
                    'asymmetry_score': 0.12,
                    'left_activity': 55,
                    'right_activity': 53,
                    'posture_deviation': 0.08,
                    'dark_spots_count': 2,
                    'red_percentage': 0.05,
                    'discharge_area': 200,
                    'texture_std': 32
                },
                'expected': {
                    'body_condition': 4,
                    'lameness_present': False,
                    'symptom_count': 0
                }
            },
            # Test Case 2: Thin animal
            {
                'name': 'Thin_Cattle_1',
                'input': {
                    'circularity': 0.38,
                    'solidity': 0.68,
                    'texture_smoothness': 0.35,
                    'brightness_mean': 95,
                    'asymmetry_score': 0.15,
                    'left_activity': 48,
                    'right_activity': 50,
                    'posture_deviation': 0.10,
                    'dark_spots_count': 3,
                    'red_percentage': 0.08,
                    'discharge_area': 450,
                    'texture_std': 22
                },
                'expected': {
                    'body_condition': 2,
                    'lameness_present': False,
                    'symptom_count': 1
                }
            },
            # Test Case 3: Lame animal
            {
                'name': 'Lame_Cattle_1',
                'input': {
                    'circularity': 0.58,
                    'solidity': 0.75,
                    'texture_smoothness': 0.52,
                    'brightness_mean': 135,
                    'asymmetry_score': 0.32,
                    'left_activity': 38,
                    'right_activity': 55,
                    'posture_deviation': 0.22,
                    'dark_spots_count': 4,
                    'red_percentage': 0.10,
                    'discharge_area': 350,
                    'texture_std': 28
                },
                'expected': {
                    'body_condition': 3,
                    'lameness_present': True,
                    'symptom_count': 0
                }
            },
            # Test Case 4: Diseased animal
            {
                'name': 'Diseased_Cattle_1',
                'input': {
                    'circularity': 0.45,
                    'solidity': 0.70,
                    'texture_smoothness': 0.40,
                    'brightness_mean': 110,
                    'asymmetry_score': 0.18,
                    'left_activity': 45,
                    'right_activity': 48,
                    'posture_deviation': 0.14,
                    'dark_spots_count': 9,
                    'red_percentage': 0.22,
                    'discharge_area': 2200,
                    'texture_std': 18
                },
                'expected': {
                    'body_condition': 2,
                    'lameness_present': False,
                    'symptom_count': 4
                }
            },
            # Test Case 5: Obese animal
            {
                'name': 'Obese_Cattle_1',
                'input': {
                    'circularity': 0.82,
                    'solidity': 0.90,
                    'texture_smoothness': 0.78,
                    'brightness_mean': 165,
                    'asymmetry_score': 0.10,
                    'left_activity': 52,
                    'right_activity': 54,
                    'posture_deviation': 0.08,
                    'dark_spots_count': 1,
                    'red_percentage': 0.04,
                    'discharge_area': 150,
                    'texture_std': 35
                },
                'expected': {
                    'body_condition': 5,
                    'lameness_present': False,
                    'symptom_count': 0
                }
            },
            # Test Case 6: Severe lameness
            {
                'name': 'Severe_Lame_Cattle_1',
                'input': {
                    'circularity': 0.52,
                    'solidity': 0.72,
                    'texture_smoothness': 0.48,
                    'brightness_mean': 128,
                    'asymmetry_score': 0.42,
                    'left_activity': 28,
                    'right_activity': 58,
                    'posture_deviation': 0.28,
                    'dark_spots_count': 3,
                    'red_percentage': 0.15,
                    'discharge_area': 600,
                    'texture_std': 26
                },
                'expected': {
                    'body_condition': 3,
                    'lameness_present': True,
                    'symptom_count': 2
                }
            }
        ]
        
        return test_cases
    
    def run_test(self, test_case: Dict) -> Dict:
        """Run a single test case"""
        name = test_case['name']
        inputs = test_case['input']
        expected = test_case['expected']
        
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {name}")
        print(f"{'='*60}")
        
        # Test body condition
        bcs_result = self.analyzer.analyze_body_condition_refined(inputs)
        print(f"\n📊 Body Condition Score:")
        print(f"   Predicted: {bcs_result['score']}/5 (confidence: {bcs_result['confidence']:.2%})")
        print(f"   Expected:  {expected['body_condition']}/5")
        print(f"   Assessment: {bcs_result['assessment']}")
        
        # Test lameness
        lameness_result = self.analyzer.detect_lameness_refined(inputs)
        print(f"\n🦵 Lameness Detection:")
        print(f"   Predicted: {'Yes' if lameness_result['detected'] else 'No'} "
              f"({lameness_result['severity']}, confidence: {lameness_result['confidence']:.2%})")
        print(f"   Expected:  {'Yes' if expected['lameness_present'] else 'No'}")
        if lameness_result['detected']:
            print(f"   Affected: {lameness_result['affected_limb']}")
        
        # Test symptoms
        symptoms_result = self.analyzer.detect_symptoms_refined(inputs)
        print(f"\n🔍 Symptom Detection:")
        print(f"   Predicted: {symptoms_result['total_detected']} symptoms")
        print(f"   Expected:  {expected['symptom_count']} symptoms")
        if symptoms_result['symptoms']:
            for sym in symptoms_result['symptoms']:
                print(f"   - {sym['type']}: {sym['description'][:60]}...")
        
        # Calculate accuracy
        predictions = {
            'score': bcs_result['score'],
            'detected': lameness_result['detected'],
            'total_detected': symptoms_result['total_detected']
        }
        
        accuracy = self.analyzer.calculate_accuracy_score(predictions, expected)
        
        print(f"\n✅ Accuracy Score: {accuracy:.2f}%")
        
        result = {
            'test_name': name,
            'body_condition': bcs_result,
            'lameness': lameness_result,
            'symptoms': symptoms_result,
            'accuracy': accuracy,
            'passed': accuracy >= 75.0
        }
        
        return result
    
    def run_all_tests(self) -> Dict:
        """Run all test cases and generate report"""
        print("\n" + "="*60)
        print("🚀 Starting Comprehensive Model Testing")
        print("="*60)
        
        test_cases = self.load_test_cases()
        results = []
        
        start_time = time.time()
        
        for test_case in test_cases:
            result = self.run_test(test_case)
            results.append(result)
            self.test_results.append(result)
        
        elapsed = time.time() - start_time
        
        # Calculate overall statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['passed'])
        avg_accuracy = np.mean([r['accuracy'] for r in results])
        
        print(f"\n\n{'='*60}")
        print("📊 FINAL TEST REPORT")
        print(f"{'='*60}")
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Average Accuracy: {avg_accuracy:.2f}%")
        print(f"   Execution Time: {elapsed:.2f}s")
        
        # Individual test breakdown
        print(f"\n📋 Individual Test Results:")
        for r in results:
            status = "✅ PASS" if r['passed'] else "❌ FAIL"
            print(f"   {status} | {r['test_name']}: {r['accuracy']:.2f}%")
        
        # Save results to JSON
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'average_accuracy': float(avg_accuracy),
            'execution_time': float(elapsed),
            'test_results': results
        }
        
        report_path = Path('test_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Full report saved to: {report_path.absolute()}")
        
        # Generate recommendations
        print(f"\n💡 Recommendations:")
        if avg_accuracy >= 85:
            print("   ✅ Excellent accuracy! Models are production-ready.")
        elif avg_accuracy >= 75:
            print("   ⚠️  Good accuracy, but some refinement recommended.")
            print("   Consider increasing test cases for failed scenarios.")
        else:
            print("   ❌ Accuracy below target. Model refinement needed.")
            print("   Review failed test cases and adjust thresholds.")
        
        print(f"\n{'='*60}\n")
        
        return report


def main():
    """Main testing function"""
    tester = ModelTester()
    report = tester.run_all_tests()
    
    return report


if __name__ == "__main__":
    report = main()
    print(f"\n🎉 Testing Complete! Average Accuracy: {report['average_accuracy']:.2f}%")
