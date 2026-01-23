"""
Runtime Inference Engine for Sentinel-LEWS
Loads trained model and makes real-time predictions on new rainfall data.
"""
import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from datetime import datetime, timedelta

class LandslidePredictionEngine:
    """Real-time landslide prediction engine."""
    
    def __init__(self, model_path=None):
        """
        Initialize prediction engine.
        
        Args:
            model_path: Path to trained LightGBM model. If None, uses default location.
        """
        if model_path is None:
            # Default to models directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(root_dir, "models", "lgb_model.txt")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print(f"Loading model from: {model_path}")
        self.model = lgb.Booster(model_file=model_path)
        self.feature_names = ['slope', 'rain_1d', 'rain_3d', 'rain_7d', 'rain_15d']
        print("✓ Model loaded successfully")
    
    def compute_rolling_rainfall(self, rainfall_history, current_date):
        """
        Compute rolling rainfall features from history.
        
        Args:
            rainfall_history: DataFrame with columns ['date', 'rain']
            current_date: Date for which to compute features
            
        Returns:
            dict with rain_1d, rain_3d, rain_7d, rain_15d
        """
        # Ensure date is datetime
        if isinstance(current_date, str):
            current_date = pd.to_datetime(current_date)
        
        # Filter data up to current date
        history = rainfall_history[rainfall_history['date'] <= current_date].copy()
        history = history.sort_values('date')
        
        if len(history) < 15:
            raise ValueError(f"Need at least 15 days of history. Got {len(history)} days.")
        
        # Get last 15 days
        last_15_days = history.tail(15)
        
        # Compute features
        features = {
            'rain_1d': last_15_days.tail(1)['rain'].sum(),
            'rain_3d': last_15_days.tail(3)['rain'].sum(),
            'rain_7d': last_15_days.tail(7)['rain'].sum(),
            'rain_15d': last_15_days.tail(15)['rain'].sum()
        }
        
        return features
    
    def predict_grid_cell(self, slope, rainfall_features):
        """
        Predict landslide risk for a single grid cell.
        
        Args:
            slope: Terrain slope angle (degrees)
            rainfall_features: dict with rain_1d, rain_3d, rain_7d, rain_15d
            
        Returns:
            dict with probability and risk_level
        """
        # Prepare input
        input_data = pd.DataFrame([{
            'slope': slope,
            'rain_1d': rainfall_features['rain_1d'],
            'rain_3d': rainfall_features['rain_3d'],
            'rain_7d': rainfall_features['rain_7d'],
            'rain_15d': rainfall_features['rain_15d']
        }])
        
        # Predict
        probability = self.model.predict(input_data)[0]
        
        # Categorize risk
        if probability < 0.3:
            risk_level = "LOW"
        elif probability < 0.6:
            risk_level = "MEDIUM"
        elif probability < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        return {
            'probability': float(probability),
            'risk_level': risk_level,
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_all_cells(self, static_data, rainfall_history, current_date):
        """
        Predict landslide risk for all grid cells.
        
        Args:
            static_data: DataFrame with columns ['cell_id', 'lat', 'lon', 'slope']
            rainfall_history: DataFrame with columns ['date', 'rain']
            current_date: Date for prediction
            
        Returns:
            DataFrame with predictions for all cells
        """
        print(f"Computing predictions for {len(static_data)} cells...")
        
        # Compute rainfall features
        rainfall_features = self.compute_rolling_rainfall(rainfall_history, current_date)
        
        print(f"Rainfall features for {current_date}:")
        for key, val in rainfall_features.items():
            print(f"  {key}: {val:.4f} mm/hr")
        
        # Prepare input for all cells
        input_data = static_data[['slope']].copy()
        input_data['rain_1d'] = rainfall_features['rain_1d']
        input_data['rain_3d'] = rainfall_features['rain_3d']
        input_data['rain_7d'] = rainfall_features['rain_7d']
        input_data['rain_15d'] = rainfall_features['rain_15d']
        
        # Predict for all cells
        probabilities = self.model.predict(input_data)
        
        # Create results DataFrame
        results = static_data[['cell_id', 'lat', 'lon', 'slope']].copy()
        results['probability'] = probabilities
        results['date'] = current_date
        results['timestamp'] = datetime.now().isoformat()
        
        # Categorize risk
        results['risk_level'] = pd.cut(
            probabilities,
            bins=[0, 0.3, 0.6, 0.8, 1.0],
            labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        )
        
        # Sort by probability (highest risk first)
        results = results.sort_values('probability', ascending=False)
        
        print(f"✓ Predictions completed")
        print(f"\nRisk Distribution:")
        print(results['risk_level'].value_counts().sort_index())
        
        return results
    
    def get_high_risk_cells(self, predictions, threshold=0.6):
        """
        Filter high-risk cells that need alerts.
        
        Args:
            predictions: DataFrame from predict_all_cells
            threshold: Probability threshold for alerts (default 0.6 = MEDIUM+)
            
        Returns:
            DataFrame with only high-risk cells
        """
        high_risk = predictions[predictions['probability'] >= threshold].copy()
        print(f"\n⚠️  {len(high_risk)} cells above {threshold:.0%} risk threshold")
        return high_risk


def demo_inference():
    """Demo: Run real-time inference."""
    print("="*70)
    print("SENTINEL-LEWS RUNTIME INFERENCE DEMO")
    print("="*70)
    
    # Initialize engine
    engine = LandslidePredictionEngine()
    
    # Load static grid data
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_file = os.path.join(root_dir, "dataset_builder", "output", "shimla_static.csv")
    
    print(f"\nLoading static grid data...")
    static = pd.read_csv(static_file, nrows=1000)  # Load first 1000 cells for demo
    
    # Check if columns are wrong
    if static.columns[0].replace('.', '').replace('-', '').isdigit():
        static = pd.read_csv(static_file, header=None, nrows=1000)
        static.columns = ['cell_id', 'lat', 'lon', 'slope']
    
    print(f"✓ Loaded {len(static)} grid cells")
    
    # Load rainfall history
    rain_file = os.path.join(root_dir, "dataset_builder", "shimla_rain_features.csv")
    print(f"\nLoading rainfall history...")
    rainfall = pd.read_csv(rain_file)
    rainfall['date'] = pd.to_datetime(rainfall['date'])
    
    # Create simple history (just date and daily rain)
    rainfall_history = rainfall[['date', 'rain']].copy()
    print(f"✓ Loaded {len(rainfall_history)} days of rainfall data")
    
    # Simulate "today" - use last date in dataset
    current_date = rainfall['date'].max()
    print(f"\nSimulating prediction for: {current_date.strftime('%Y-%m-%d')}")
    
    # Run inference
    predictions = engine.predict_all_cells(static, rainfall_history, current_date)
    
    # Show top 10 high-risk cells
    print(f"\n{'='*70}")
    print("TOP 10 HIGH-RISK CELLS")
    print(f"{'='*70}")
    top_10 = predictions.head(10)
    print(top_10[['cell_id', 'lat', 'lon', 'slope', 'probability', 'risk_level']].to_string(index=False))
    
    # Get alert-worthy cells
    high_risk = engine.get_high_risk_cells(predictions, threshold=0.6)
    
    print(f"\n{'='*70}")
    print("✓ INFERENCE COMPLETE")
    print(f"{'='*70}")
    
    return predictions


if __name__ == "__main__":
    # Run demo
    predictions = demo_inference()
