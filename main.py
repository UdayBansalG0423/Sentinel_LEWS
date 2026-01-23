"""
Sentinel-LEWS Main System Loop
Real-time landslide early warning system orchestrator.
"""
import os
import time
import pandas as pd
from datetime import datetime, timedelta
import argparse
import sqlite3
import sys
import random

# Import system modules
from runtime.inference import LandslidePredictionEngine
from data.ingestion import RainfallDataIngestion
from decision.rule_engine import LandslideDecisionEngine
from alerts.alert_manager import AlertManager

# Import dashboard database
sys.path.append(os.path.join(os.path.dirname(__file__), 'dashboard'))
import db as dashboard_db


class SentinelLEWS:
    """Main orchestrator for Sentinel-LEWS early warning system."""
    
    def __init__(self, continuous=False, cycle_interval=300):
        """
        Initialize Sentinel-LEWS system.
        
        Args:
            continuous: Whether to run in continuous mode (default: False for demo)
            cycle_interval: Time between cycles in seconds (default: 300 = 5 min)
        """
        print("="*70)
        print("SENTINEL-LEWS - Landslide Early Warning System")
        print("="*70)
        print("Initializing system components...")
        
        # Initialize components
        self.prediction_engine = LandslidePredictionEngine()
        self.data_ingestion = RainfallDataIngestion()
        self.decision_engine = LandslideDecisionEngine()
        self.alert_manager = AlertManager()
        
        self.continuous = continuous
        self.cycle_interval = cycle_interval
        self.cycle_count = 0
        
        # Load static grid data (terrain)
        root_dir = os.path.dirname(os.path.abspath(__file__))
        static_file = os.path.join(root_dir, "dataset_builder", "output", "shimla_static.csv")
        
        print(f"Loading terrain data...")
        self.static_data = pd.read_csv(static_file, nrows=2000)  # Load first 2000 cells
        
        # Fix columns if needed
        if self.static_data.columns[0].replace('.', '').replace('-', '').isdigit():
            self.static_data = pd.read_csv(static_file, header=None, nrows=2000)
            self.static_data.columns = ['cell_id', 'lat', 'lon', 'slope']
        
        print(f"✓ Loaded {len(self.static_data)} grid cells")
        
        # Load historical rainfall
        print(f"Loading historical rainfall data...")
        self.rainfall_history = self.data_ingestion.load_historical_data()
        
        print("\n✓ System initialization complete")
        print(f"  Mode: {'CONTINUOUS' if continuous else 'SINGLE RUN'}")
        if continuous:
            print(f"  Cycle interval: {cycle_interval} seconds ({cycle_interval/60:.1f} minutes)")
        
        # Initialize dashboard database
        self._init_dashboard_db()
        print("✓ Dashboard database ready for real-time updates")
    
    def run_cycle(self, current_date=None):
        """
        Run one prediction cycle.
        
        Args:
            current_date: Date for prediction. If None, uses latest data date.
            
        Returns:
            dict with cycle results
        """
        self.cycle_count += 1
        cycle_start = time.time()
        
        print(f"\n{'='*70}")
        print(f"CYCLE #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        # Step 1: Data Ingestion
        print("\n[1/5] Data Ingestion")
        print("-" * 70)
        
        # In demo mode, use latest historical date
        # In production, would ingest new real-time data
        if current_date is None:
            current_date = self.rainfall_history['date'].max()
            print(f"Using latest available date: {current_date.strftime('%Y-%m-%d')}")
        
        # Get updated rainfall history (in production, this would include new data)
        rainfall_data = self.data_ingestion.get_updated_history(self.rainfall_history)
        
        # Step 2: Run Inference
        print(f"\n[2/5] Running Inference")
        print("-" * 70)
        
        inference_start = time.time()
        
        predictions = self.prediction_engine.predict_all_cells(
            self.static_data,
            rainfall_data,
            current_date
        )
        
        inference_time = time.time() - inference_start
        print(f"✓ Predictions complete in {inference_time:.3f}s")
        
        # Step 3: Apply Decision Rules
        print(f"\n[3/5] Applying Decision Rules")
        print("-" * 70)
        
        # Add rain_15d for decision engine
        rainfall_features = self.prediction_engine.compute_rolling_rainfall(
            rainfall_data, current_date
        )
        predictions['rain_15d'] = rainfall_features['rain_15d']
        
        processed = self.decision_engine.process_predictions(predictions)
        alert_cells = self.decision_engine.get_alert_cells(processed)
        
        print(f"✓ Decision rules applied")
        print(f"  Alert cells: {len(alert_cells)}")
        
        # Step 4: Trigger Alerts
        print(f"\n[4/5] Triggering Alerts")
        print("-" * 70)
        
        if len(alert_cells) > 0:
            alert_summary = self.alert_manager.send_batch_alerts(alert_cells)
            # Write real-time data to dashboard
            self._write_to_dashboard(predictions, alert_cells, rainfall_data, inference_time)
        else:
            print("✓ No alerts required - all areas safe")
            alert_summary = {'total': 0, 'sent': 0}
            # Still write predictions to dashboard
            self._write_to_dashboard(predictions, [], rainfall_data, inference_time)
        
        # Step 5: Generate Summary
        print(f"\n[5/5] Cycle Summary")
        print("-" * 70)
        
        cycle_time = time.time() - cycle_start
        
        summary = {
            'cycle': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'prediction_date': current_date.strftime('%Y-%m-%d'),
            'cells_analyzed': len(predictions),
            'cells_alerted': len(alert_cells),
            'alerts_sent': alert_summary.get('sent', 0),
            'critical_alerts': alert_summary.get('critical', 0),
            'high_alerts': alert_summary.get('high', 0),
            'cycle_time_seconds': round(cycle_time, 2),
            'risk_distribution': predictions['risk_level'].value_counts().to_dict()
        }
        
        print(f"✓ Cycle #{self.cycle_count} complete in {cycle_time:.2f}s")
        print(f"  Cells analyzed: {summary['cells_analyzed']}")
        print(f"  Alerts triggered: {summary['cells_alerted']}")
        print(f"  Risk distribution:")
        for risk, count in summary['risk_distribution'].items():
            print(f"    {risk}: {count}")
        
        return summary
    
    def run_continuous(self):
        """Run system in continuous mode."""
        print(f"\n{'='*70}")
        print("STARTING CONTINUOUS MONITORING")
        print(f"{'='*70}")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Run cycle
                summary = self.run_cycle()
                
                # Wait for next cycle
                if self.continuous:
                    print(f"\n⏱️  Waiting {self.cycle_interval}s until next cycle...")
                    time.sleep(self.cycle_interval)
                else:
                    # In demo mode, just run once
                    break
        
        except KeyboardInterrupt:
            print(f"\n\n{'='*70}")
            print("SYSTEM STOPPED BY USER")
            print(f"{'='*70}")
            print(f"Total cycles completed: {self.cycle_count}")
    
    def run_demo(self):
        """Run single demo cycle."""
        print(f"\n{'='*70}")
        print("RUNNING DEMO CYCLE")
        print(f"{'='*70}")
        
        summary = self.run_cycle()
        
        print(f"\n{'='*70}")
        print("✓ DEMO COMPLETE")
        print(f"{'='*70}")
        
        return summary
    
    def _init_dashboard_db(self):
        """Initialize dashboard database."""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'sentinel.db')
            sys.path.append(os.path.join(os.path.dirname(__file__), 'dashboard'))
            import db as dashboard_db
            dashboard_db.init_db()
        except Exception as e:
            print(f"  ⚠ Warning: Dashboard DB init error: {e}")
    
    def _write_to_dashboard(self, predictions, alerts, rainfall_data, inference_time):
        """Write real-time predictions and alerts to dashboard database."""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'sentinel.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Clear old predictions (keep last 500)
            cursor.execute('DELETE FROM predictions WHERE id NOT IN (SELECT id FROM predictions ORDER BY timestamp DESC LIMIT 500)')
            
            # Get latest rainfall
            latest_rainfall = rainfall_data.iloc[-1]['rain_mm'] if len(rainfall_data) > 0 else 0
            
            # Write sample of predictions (50 random cells for performance)
            sample_size = min(50, len(predictions))
            sample_indices = random.sample(range(len(predictions)), sample_size)
            
            for idx in sample_indices:
                row = predictions.iloc[idx]
                cursor.execute('''
                    INSERT INTO predictions (cell_id, probability, timestamp, slope, rainfall_24h)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    row['cell_id'],
                    float(row['probability']),
                    datetime.now().isoformat(),
                    float(row['slope']),
                    float(latest_rainfall)
                ))
            
            # Write alerts (all high/critical alerts)
            for alert in alerts:
                severity = alert['risk_level']
                message = f"Landslide risk {severity} at {alert['cell_id']}. {alert['action']}."
                location = f"Cell {alert['cell_id']} ({alert['latitude']:.4f}, {alert['longitude']:.4f})"
                
                cursor.execute('''
                    INSERT INTO alerts (cell_id, severity, message, sent_time, probability, location, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert['cell_id'],
                    severity,
                    message,
                    datetime.now().isoformat(),
                    float(alert['probability']),
                    location,
                    'pending'
                ))
            
            # Update system info
            cursor.execute('UPDATE system_info SET value = ?, updated_at = ? WHERE key = "last_ingestion"',
                         (datetime.now().isoformat(), datetime.now().isoformat()))
            cursor.execute('UPDATE system_info SET value = ?, updated_at = ? WHERE key = "inference_latency"',
                         (f"{inference_time*1000:.1f}", datetime.now().isoformat()))
            cursor.execute('UPDATE system_info SET value = ?, updated_at = ? WHERE key = "network_status"',
                         ('ONLINE' if self.continuous else 'OFFLINE', datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Dashboard updated: {sample_size} predictions, {len(alerts)} alerts")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not update dashboard: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Sentinel-LEWS Early Warning System')
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run in continuous mode (default: single demo run)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Cycle interval in seconds (default: 300)'
    )
    
    args = parser.parse_args()
    
    # Initialize system
    system = SentinelLEWS(
        continuous=args.continuous,
        cycle_interval=args.interval
    )
    
    # Run system
    if args.continuous:
        system.run_continuous()
    else:
        system.run_demo()

    def _write_predictions_to_db(self, predictions, rainfall_data):
        """Write predictions to dashboard database for real-time display."""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'sentinel.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Clear old predictions (keep last 1000)
            cursor.execute('DELETE FROM predictions WHERE id NOT IN (SELECT id FROM predictions ORDER BY timestamp DESC LIMIT 1000)')
            
            # Get latest rainfall value
            latest_rainfall = rainfall_data.iloc[-1]['rain_mm'] if len(rainfall_data) > 0 else 0
            
            # Insert new predictions (sample 100 cells to avoid overwhelming DB)
            import random
            sample_size = min(100, len(predictions))
            sample_predictions = random.sample(predictions, sample_size)
            
            for pred in sample_predictions:
                cursor.execute('''
                    INSERT INTO predictions (cell_id, probability, timestamp, slope, rainfall_24h)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    pred['cell_id'],
                    pred['probability'],
                    datetime.now().isoformat(),
                    pred['slope'],
                    latest_rainfall
                ))
            
            conn.commit()
            conn.close()
            print(f"  → Wrote {sample_size} predictions to dashboard database")
        except Exception as e:
            print(f"  ⚠ Warning: Could not write to dashboard DB: {e}")
    
    def _write_alerts_to_db(self, alerts):
        """Write alerts to dashboard database for real-time display."""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'sentinel.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Sample alerts to avoid overwhelming DB
            sample_size = min(20, len(alerts))
            import random
            sample_alerts = random.sample(alerts, sample_size)
            
            for alert in sample_alerts:
                severity = alert['risk_level']
                message = f"Landslide risk {severity} at {alert['cell_id']}. {alert['action']}."
                location = f"Cell {alert['cell_id']} ({alert['latitude']:.4f}, {alert['longitude']:.4f})"
                
                cursor.execute('''
                    INSERT INTO alerts (cell_id, severity, message, sent_time, probability, location, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert['cell_id'],
                    severity,
                    message,
                    datetime.now().isoformat(),
                    alert['probability'],
                    location,
                    'pending'
                ))
            
            conn.commit()
            conn.close()
            print(f"  → Wrote {sample_size} alerts to dashboard database")
        except Exception as e:
            print(f"  ⚠ Warning: Could not write alerts to dashboard DB: {e}")
    
    def _update_system_info(self, inference_time):
        """Update system info in dashboard database."""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'sentinel.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Update system info
            cursor.execute('''
                UPDATE system_info SET value = ?, updated_at = ?
                WHERE key = 'last_ingestion'
            ''', (datetime.now().isoformat(), datetime.now().isoformat()))
            
            cursor.execute('''
                UPDATE system_info SET value = ?, updated_at = ?
                WHERE key = 'inference_latency'
            ''', (f"{inference_time*1000:.1f}", datetime.now().isoformat()))
            
            cursor.execute('''
                UPDATE system_info SET value = ?, updated_at = ?
                WHERE key = 'network_status'
            ''', ('ONLINE' if self.continuous else 'OFFLINE', datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ⚠ Warning: Could not update system info: {e}")

if __name__ == "__main__":
    main()

