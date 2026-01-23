"""
Real-time Data Ingestion Module
Simulates new rainfall data ingestion for hackathon demo.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class RainfallDataIngestion:
    """Handles ingestion of new rainfall data."""
    
    def __init__(self, history_file=None, realtime_dir=None):
        """
        Initialize data ingestion.
        
        Args:
            history_file: Path to historical rainfall CSV
            realtime_dir: Directory for real-time data files
        """
        if history_file is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            history_file = os.path.join(root_dir, "dataset_builder", "shimla_rain_features.csv")
        
        if realtime_dir is None:
            realtime_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "realtime")
        
        self.history_file = history_file
        self.realtime_dir = realtime_dir
        
        # Ensure realtime directory exists
        os.makedirs(self.realtime_dir, exist_ok=True)
    
    def load_historical_data(self):
        """Load historical rainfall data."""
        print(f"Loading historical data from: {self.history_file}")
        df = pd.read_csv(self.history_file)
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert to simple format (date, rain)
        rainfall_history = df[['date', 'rain']].copy()
        print(f"✓ Loaded {len(rainfall_history)} days of historical data")
        print(f"  Date range: {rainfall_history['date'].min()} to {rainfall_history['date'].max()}")
        
        return rainfall_history
    
    def simulate_new_rainfall(self, base_value=0.02, variation=0.01):
        """
        Simulate new rainfall data for demo.
        
        Args:
            base_value: Base rainfall value (mm/hr)
            variation: Random variation range
            
        Returns:
            dict with date and rain value
        """
        # Get current date
        current_date = datetime.now().date()
        
        # Simulate rainfall with random variation
        rain = base_value + np.random.uniform(-variation, variation)
        rain = max(0, rain)  # Ensure non-negative
        
        return {
            'date': pd.to_datetime(current_date),
            'rain': rain,
            'timestamp': datetime.now().isoformat()
        }
    
    def ingest_new_data(self, rain_value=None, date=None):
        """
        Ingest new rainfall data.
        
        Args:
            rain_value: Rainfall value (mm/hr). If None, simulates random value.
            date: Date for the data. If None, uses today.
            
        Returns:
            dict with the ingested data
        """
        if date is None:
            date = datetime.now().date()
        
        if rain_value is None:
            # Simulate rainfall
            data = self.simulate_new_rainfall()
        else:
            data = {
                'date': pd.to_datetime(date),
                'rain': rain_value,
                'timestamp': datetime.now().isoformat()
            }
        
        # Save to realtime directory
        filename = f"rainfall_{date}.csv"
        filepath = os.path.join(self.realtime_dir, filename)
        
        df = pd.DataFrame([data])
        df.to_csv(filepath, index=False)
        
        print(f"✓ Ingested new rainfall data:")
        print(f"  Date: {data['date'].strftime('%Y-%m-%d')}")
        print(f"  Rainfall: {data['rain']:.4f} mm/hr")
        print(f"  Saved to: {filepath}")
        
        return data
    
    def get_updated_history(self, historical_data):
        """
        Merge historical data with new real-time data.
        
        Args:
            historical_data: DataFrame with historical rainfall
            
        Returns:
            Updated DataFrame with historical + new data
        """
        # Load all realtime files
        realtime_files = [f for f in os.listdir(self.realtime_dir) if f.endswith('.csv')]
        
        if not realtime_files:
            print("No new real-time data found")
            return historical_data
        
        # Read all realtime data
        realtime_data = []
        for file in realtime_files:
            filepath = os.path.join(self.realtime_dir, file)
            df = pd.read_csv(filepath)
            realtime_data.append(df)
        
        realtime_df = pd.concat(realtime_data, ignore_index=True)
        realtime_df['date'] = pd.to_datetime(realtime_df['date'])
        realtime_df = realtime_df[['date', 'rain']]  # Keep only necessary columns
        
        # Merge with historical
        combined = pd.concat([historical_data, realtime_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        combined = combined.sort_values('date')
        
        print(f"✓ Merged historical + real-time data: {len(combined)} days total")
        
        return combined
    
    def clear_realtime_data(self):
        """Clear all real-time data files (for testing)."""
        files = [f for f in os.listdir(self.realtime_dir) if f.endswith('.csv')]
        for file in files:
            os.remove(os.path.join(self.realtime_dir, file))
        print(f"✓ Cleared {len(files)} real-time data files")


def demo_ingestion():
    """Demo: Simulate data ingestion."""
    print("="*70)
    print("REAL-TIME DATA INGESTION DEMO")
    print("="*70)
    
    # Initialize ingestion
    ingestion = RainfallDataIngestion()
    
    # Load historical data
    historical = ingestion.load_historical_data()
    
    print(f"\n{'='*70}")
    print("SIMULATING NEW RAINFALL DATA")
    print(f"{'='*70}")
    
    # Simulate 3 days of new data
    for i in range(3):
        date = datetime.now().date() + timedelta(days=i)
        rain = 0.025 + np.random.uniform(-0.005, 0.015)
        data = ingestion.ingest_new_data(rain_value=rain, date=date)
        print()
    
    # Get updated history
    print(f"{'='*70}")
    print("MERGING WITH HISTORICAL DATA")
    print(f"{'='*70}")
    updated = ingestion.get_updated_history(historical)
    
    print(f"\n✓ Data ingestion complete")
    print(f"  Historical: {len(historical)} days")
    print(f"  Updated: {len(updated)} days")
    print(f"  New data: {len(updated) - len(historical)} days")
    
    return updated


if __name__ == "__main__":
    demo_ingestion()
