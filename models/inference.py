"""
Inference Pipeline for Edge Deployment
Handles data preprocessing and real-time prediction
"""
import pandas as pd
import lightgbm as lgb
import numpy as np
import os
import time
import json

class LandslidePredictor:
    """Lightweight predictor for edge devices"""
    
    def __init__(self, model_path=None):
        """Initialize predictor with trained model"""
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "lgb_model.txt")
        
        self.model = lgb.Booster(model_file=model_path)
        self.feature_names = ["slope", "rain_1d", "rain_3d", "rain_7d", "rain_15d"]
        print(f"Model loaded from: {model_path}")
    
    def preprocess(self, data):
        """
        Preprocess input data for prediction
        
        Parameters:
        -----------
        data : dict or pd.DataFrame
            Input features with keys/columns matching feature_names
        
        Returns:
        --------
        np.ndarray : Preprocessed features ready for prediction
        """
        if isinstance(data, dict):
            # Convert dict to DataFrame
            data = pd.DataFrame([data])
        
        # Ensure correct column order
        X = data[self.feature_names].values
        return X
    
    def predict(self, data):
        """
        Make prediction on preprocessed data
        
        Returns:
        --------
        dict : {
            'probability': float,  # Probability of landslide (0-1)
            'prediction': int,     # Binary prediction (0=Safe, 1=Landslide)
            'risk_level': str,     # Risk category
            'inference_time_ms': float
        }
        """
        start_time = time.time()
        
        # Preprocess
        X = self.preprocess(data)
        
        # Predict
        proba = self.model.predict(X)[0]
        prediction = 1 if proba > 0.5 else 0
        
        # Risk categorization
        if proba < 0.3:
            risk_level = "LOW"
        elif proba < 0.6:
            risk_level = "MEDIUM"
        elif proba < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        inference_time = (time.time() - start_time) * 1000  # ms
        
        return {
            'probability': round(float(proba), 4),
            'prediction': int(prediction),
            'risk_level': risk_level,
            'inference_time_ms': round(inference_time, 2)
        }
    
    def predict_batch(self, data_batch):
        """Batch prediction for efficiency"""
        start_time = time.time()
        
        X = self.preprocess(data_batch)
        probas = self.model.predict(X)
        predictions = (probas > 0.5).astype(int)
        
        inference_time = (time.time() - start_time) * 1000
        
        return {
            'probabilities': probas.tolist(),
            'predictions': predictions.tolist(),
            'batch_size': len(probas),
            'total_inference_time_ms': round(inference_time, 2),
            'avg_inference_time_ms': round(inference_time / len(probas), 2)
        }


def load_rainfall_data(lat, lon, days=15):
    """
    Simulate loading rainfall data for a location
    In production, this would query actual rainfall APIs/databases
    """
    # Placeholder - replace with actual data source
    return {
        'rain_1d': np.random.uniform(0.01, 0.1),
        'rain_3d': np.random.uniform(0.05, 0.15),
        'rain_7d': np.random.uniform(0.1, 0.3),
        'rain_15d': np.random.uniform(0.15, 0.5)
    }


def get_terrain_data(lat, lon):
    """
    Get terrain slope for a location
    In production, query terrain database or raster
    """
    # Placeholder - replace with actual DEM data
    return {'slope': np.random.uniform(20, 70)}


if __name__ == "__main__":
    print("="*70)
    print("LANDSLIDE PREDICTION - INFERENCE DEMO")
    print("="*70)
    
    # Initialize predictor
    predictor = LandslidePredictor()
    
    # Example 1: Single prediction
    print("\n--- SINGLE PREDICTION ---")
    example_data = {
        'slope': 45.5,
        'rain_1d': 0.05,
        'rain_3d': 0.12,
        'rain_7d': 0.25,
        'rain_15d': 0.40
    }
    
    result = predictor.predict(example_data)
    print(f"Input: {example_data}")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Example 2: Batch prediction
    print("\n--- BATCH PREDICTION (100 samples) ---")
    batch_data = pd.DataFrame({
        'slope': np.random.uniform(20, 70, 100),
        'rain_1d': np.random.uniform(0.01, 0.1, 100),
        'rain_3d': np.random.uniform(0.05, 0.15, 100),
        'rain_7d': np.random.uniform(0.1, 0.3, 100),
        'rain_15d': np.random.uniform(0.15, 0.5, 100)
    })
    
    batch_result = predictor.predict_batch(batch_data)
    print(f"Batch size: {batch_result['batch_size']}")
    print(f"Total inference time: {batch_result['total_inference_time_ms']:.2f}ms")
    print(f"Avg per sample: {batch_result['avg_inference_time_ms']:.2f}ms")
    
    # Example 3: Real-world scenario
    print("\n--- REAL-WORLD SCENARIO ---")
    lat, lon = 31.1048, 77.1734  # Shimla coordinates
    
    # Get current data
    rainfall = load_rainfall_data(lat, lon)
    terrain = get_terrain_data(lat, lon)
    
    input_data = {**terrain, **rainfall}
    prediction = predictor.predict(input_data)
    
    print(f"Location: ({lat}, {lon})")
    print(f"Features: {input_data}")
    print(f"Prediction: {prediction['risk_level']} risk ({prediction['probability']*100:.1f}%)")
    print(f"Inference time: {prediction['inference_time_ms']:.2f}ms")
    
    print("\n" + "="*70)
