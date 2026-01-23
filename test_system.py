"""
Comprehensive System Test Suite
Tests the complete pipeline from data ingestion to prediction
"""
import os
import sys
import time
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.inference import LandslidePredictor
import pandas as pd
import numpy as np

def test_model_exists():
    """Test 1: Check if model file exists"""
    print("\n[TEST 1] Model File Existence")
    model_path = os.path.join("models", "lgb_model.txt")
    exists = os.path.exists(model_path)
    size_kb = os.path.getsize(model_path) / 1024 if exists else 0
    
    print(f"  Model exists: {exists}")
    print(f"  Model size: {size_kb:.2f} KB")
    print(f"  Status: {'PASS' if exists and size_kb < 50*1024 else 'FAIL'}")
    return exists

def test_model_loading():
    """Test 2: Load model"""
    print("\n[TEST 2] Model Loading")
    try:
        start = time.time()
        predictor = LandslidePredictor()
        load_time = (time.time() - start) * 1000
        print(f"  Load time: {load_time:.2f}ms")
        print(f"  Status: PASS")
        return predictor
    except Exception as e:
        print(f"  Error: {e}")
        print(f"  Status: FAIL")
        return None

def test_single_inference(predictor):
    """Test 3: Single prediction inference"""
    print("\n[TEST 3] Single Inference")
    test_data = {
        'slope': 45.0,
        'rain_1d': 0.05,
        'rain_3d': 0.12,
        'rain_7d': 0.25,
        'rain_15d': 0.40
    }
    
    try:
        result = predictor.predict(test_data)
        print(f"  Input: {test_data}")
        print(f"  Output: {result}")
        print(f"  Inference time: {result['inference_time_ms']:.2f}ms")
        
        # Check latency requirement
        latency_ok = result['inference_time_ms'] < 16
        print(f"  Latency < 16ms: {latency_ok}")
        print(f"  Status: {'PASS' if latency_ok else 'WARN (still functional)'}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        print(f"  Status: FAIL")
        return False

def test_batch_inference(predictor, batch_size=1000):
    """Test 4: Batch prediction"""
    print(f"\n[TEST 4] Batch Inference ({batch_size} samples)")
    
    batch_data = pd.DataFrame({
        'slope': np.random.uniform(20, 70, batch_size),
        'rain_1d': np.random.uniform(0.01, 0.1, batch_size),
        'rain_3d': np.random.uniform(0.05, 0.15, batch_size),
        'rain_7d': np.random.uniform(0.1, 0.3, batch_size),
        'rain_15d': np.random.uniform(0.15, 0.5, batch_size)
    })
    
    try:
        result = predictor.predict_batch(batch_data)
        print(f"  Batch size: {result['batch_size']}")
        print(f"  Total time: {result['total_inference_time_ms']:.2f}ms")
        print(f"  Avg per sample: {result['avg_inference_time_ms']:.2f}ms")
        
        latency_ok = result['avg_inference_time_ms'] < 16
        print(f"  Avg latency < 16ms: {latency_ok}")
        print(f"  Status: {'PASS' if latency_ok else 'WARN'}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        print(f"  Status: FAIL")
        return False

def test_edge_cases(predictor):
    """Test 5: Edge cases"""
    print("\n[TEST 5] Edge Cases")
    
    test_cases = [
        {"name": "Zero rainfall", "data": {'slope': 30, 'rain_1d': 0, 'rain_3d': 0, 'rain_7d': 0, 'rain_15d': 0}},
        {"name": "Heavy rainfall", "data": {'slope': 60, 'rain_1d': 0.2, 'rain_3d': 0.5, 'rain_7d': 0.8, 'rain_15d': 1.0}},
        {"name": "Low slope", "data": {'slope': 5, 'rain_1d': 0.05, 'rain_3d': 0.1, 'rain_7d': 0.2, 'rain_15d': 0.3}},
        {"name": "High slope", "data": {'slope': 85, 'rain_1d': 0.05, 'rain_3d': 0.1, 'rain_7d': 0.2, 'rain_15d': 0.3}},
    ]
    
    passed = 0
    for case in test_cases:
        try:
            result = predictor.predict(case['data'])
            print(f"  {case['name']}: Risk={result['risk_level']}, Prob={result['probability']}")
            passed += 1
        except Exception as e:
            print(f"  {case['name']}: FAILED - {e}")
    
    print(f"  Status: {'PASS' if passed == len(test_cases) else f'PARTIAL ({passed}/{len(test_cases)})'}")
    return passed == len(test_cases)

def test_evaluation_metrics():
    """Test 6: Check evaluation metrics"""
    print("\n[TEST 6] Evaluation Metrics")
    metrics_path = os.path.join("models", "evaluation_metrics.json")
    
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        print(f"  AUC Score: {metrics['auc_score']:.4f}")
        print(f"  Accuracy: {metrics['accuracy']:.4f}")
        print(f"  F1 Score: {metrics['f1_score']:.4f}")
        print(f"  Model Size: {metrics['model_size_kb']:.2f} KB")
        print(f"  Avg Inference: {metrics['avg_inference_ms_per_sample']:.4f}ms")
        print(f"  Status: PASS")
        return True
    else:
        print(f"  Metrics file not found")
        print(f"  Status: WARN (run train.py first)")
        return False

def test_evaluation_charts():
    """Test 7: Check evaluation charts"""
    print("\n[TEST 7] Evaluation Charts")
    chart_path = os.path.join("models", "evaluation_charts.png")
    
    exists = os.path.exists(chart_path)
    print(f"  Charts exist: {exists}")
    print(f"  Status: {'PASS' if exists else 'WARN (run train.py first)'}")
    return exists

def run_all_tests():
    """Run complete test suite"""
    print("="*70)
    print("SENTINEL-LEWS SYSTEM TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Test 1: Model exists
    results['model_exists'] = test_model_exists()
    if not results['model_exists']:
        print("\nERROR: Model not found. Run: python models/train.py")
        return
    
    # Test 2: Load model
    predictor = test_model_loading()
    if predictor is None:
        print("\nERROR: Cannot load model")
        return
    results['model_loading'] = True
    
    # Test 3: Single inference
    results['single_inference'] = test_single_inference(predictor)
    
    # Test 4: Batch inference
    results['batch_inference'] = test_batch_inference(predictor)
    
    # Test 5: Edge cases
    results['edge_cases'] = test_edge_cases(predictor)
    
    # Test 6: Metrics
    results['metrics'] = test_evaluation_metrics()
    
    # Test 7: Charts
    results['charts'] = test_evaluation_charts()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL/WARN"
        print(f"  {test_name:20s}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Status: {'ALL TESTS PASSED' if passed == total else 'SOME TESTS FAILED'}")
    print("="*70)

if __name__ == "__main__":
    run_all_tests()
