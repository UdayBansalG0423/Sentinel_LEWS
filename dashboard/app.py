"""
Sentinel-LEWS Dashboard
District-level landslide early warning system control panel
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import db
import sys
import os
import sqlite3
import random
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from runtime.inference import LandslidePredictionEngine
    from data.ingestion import RainfallDataIngestion
    from decision.rule_engine import LandslideDecisionEngine
    REALTIME_ENABLED = True
except ImportError:
    REALTIME_ENABLED = False
    print("⚠ Running in demo mode - realtime system not available")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sentinel-lews-district-control'

# Initialize realtime components if available
if REALTIME_ENABLED:
    try:
        inference_engine = LandslidePredictionEngine()
        data_ingestion = RainfallDataIngestion()
        decision_engine = LandslideDecisionEngine()
        
        # Load static grid data
        grid_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'static_grid.csv')
        if os.path.exists(grid_path):
            static_data = pd.read_csv(grid_path)
            if len(static_data.columns) == 4 and 'cell_id' not in static_data.columns:
                static_data.columns = ['cell_id', 'lat', 'lon', 'slope']
        else:
            # Create dummy grid data if file doesn't exist
            static_data = pd.DataFrame({
                'cell_id': [f'CELL-{i:04d}' for i in range(1, 2001)],
                'lat': [26.85 + (i % 50) * 0.001 for i in range(2000)],
                'lon': [75.80 + (i // 50) * 0.001 for i in range(2000)],
                'slope': [20.0 + (i % 40) for i in range(2000)]
            })
        
        print("✓ Realtime system integrated with dashboard")
        print(f"✓ Loaded {len(static_data)} grid cells")
    except Exception as e:
        REALTIME_ENABLED = False
        print(f"⚠ Realtime system error: {e}")


@app.route('/')
def index():
    """Overview/Dashboard page"""
    return render_template('overview.html')


@app.route('/overview')
def overview():
    """Overview/Dashboard page"""
    return render_template('overview.html')


@app.route('/alerts')
def alerts():
    """Alerts page"""
    severity = request.args.get('severity', 'all')
    status = request.args.get('status', 'all')
    
    alerts_data = db.get_alerts(severity=severity, status=status)
    return render_template('alerts.html', alerts=alerts_data)


@app.route('/sensors')
def sensors():
    """Sensors monitoring page"""
    sensors_data = db.get_sensors()
    return render_template('sensors.html', sensors=sensors_data)


@app.route('/history')
def history():
    """Prediction history page"""
    limit = request.args.get('limit', 100, type=int)
    history_data = db.get_prediction_history(limit=limit)
    return render_template('history.html', history=history_data)


@app.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')


@app.route('/settings')
def settings():
    """Settings page"""
    settings_data = db.get_system_settings()
    return render_template('settings.html', settings=settings_data)


# API Endpoints
@app.route('/api/summary')
def api_summary():
    """Get system summary for live updates"""
    summary = db.get_system_summary()
    
    # Add current time to show dashboard is live
    summary['current_time'] = datetime.now().isoformat()
    summary['last_refresh'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add realtime system info
    if REALTIME_ENABLED:
        try:
            # Get latest predictions
            rain_data = data_ingestion.get_updated_history()
            predictions = inference_engine.predict_all_cells(rain_data)
            decisions = decision_engine.process_predictions(predictions)
            high_risk = decision_engine.get_alert_cells(decisions)
            
            summary.update({
                'realtime_enabled': True,
                'total_cells': len(predictions),
                'high_risk_cells': len([d for d in high_risk if d['risk_level'] == 'HIGH']),
                'critical_cells': len([d for d in high_risk if d['risk_level'] == 'CRITICAL']),
                'last_inference': datetime.now().isoformat(),
                'model_loaded': True,
                'rainfall_days': len(rain_data)
            })
        except Exception as e:
            summary['realtime_error'] = str(e)
            summary['realtime_enabled'] = False
    else:
        summary['realtime_enabled'] = False
    
    return jsonify(summary)


@app.route('/api/alerts/recent')
def api_recent_alerts():
    """Get recent alerts"""
    limit = request.args.get('limit', 10, type=int)
    alerts = db.get_recent_alerts(limit=limit)
    return jsonify(alerts)


@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def api_acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    result = db.acknowledge_alert(alert_id)
    return jsonify(result)


@app.route('/api/alerts/<int:alert_id>/send_sms', methods=['POST'])
def api_send_sms(alert_id):
    """Trigger SMS for an alert"""
    result = db.send_alert_sms(alert_id)
    return jsonify(result)


@app.route('/api/map/risk_data')
def api_map_risk_data():
    """Get risk map data"""
    if REALTIME_ENABLED:
        try:
            # Get fresh predictions from realtime system
            rain_data = data_ingestion.get_updated_history()
            predictions = inference_engine.predict_all_cells(rain_data)
            decisions = decision_engine.process_predictions(predictions)
            
            # Format for map display
            risk_data = [{
                'cell_id': d['cell_id'],
                'latitude': d['latitude'],
                'longitude': d['longitude'],
                'probability': d['probability'],
                'risk_level': d['risk_level'],
                'action': d['action']
            } for d in decisions]
            
            return jsonify({'source': 'realtime', 'data': risk_data, 'timestamp': datetime.now().isoformat()})
        except Exception as e:
            print(f"Realtime error: {e}")
            # Fallback to database
            risk_data = db.get_risk_map_data()
            return jsonify({'source': 'database', 'data': risk_data})
    else:
        risk_data = db.get_risk_map_data()
        return jsonify({'source': 'demo', 'data': risk_data})


@app.route('/api/charts/rainfall')
def api_rainfall_chart():
    """Get rainfall chart data (48h)"""
    hours = request.args.get('hours', 48, type=int)
    data = db.get_rainfall_data(hours=hours)
    return jsonify(data)


@app.route('/api/charts/risk_distribution')
def api_risk_distribution():
    """Get risk probability distribution"""
    data = db.get_risk_distribution()
    return jsonify(data)


@app.route('/api/export/history', methods=['POST'])
def api_export_history():
    """Export prediction history"""
    format_type = request.json.get('format', 'json')
    data = db.export_history(format_type)
    return jsonify(data)


@app.route('/api/run_inference', methods=['POST'])
def api_run_inference():
    """Run inference with provided data and update dashboard"""
    if not REALTIME_ENABLED:
        return jsonify({'success': False, 'error': 'Realtime system not available'}), 503
    
    try:
        # Get input data from request
        data = request.get_json()
        rainfall_mm = data.get('rainfall_mm', None)
        num_days = data.get('num_days', 15)
        
        # If no rainfall provided, use current historical data
        if rainfall_mm is None:
            rainfall_data = data_ingestion.get_updated_history()
        else:
            # Create synthetic rainfall history with provided value
            dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')
            rainfall_data = pd.DataFrame({
                'date': dates,
                'rain': [rainfall_mm] * num_days
            })
        
        # Run inference with all required arguments
        current_date = datetime.now()
        predictions = inference_engine.predict_all_cells(static_data, rainfall_data, current_date)
        
        # Process with decision engine
        decisions = decision_engine.process_predictions(predictions)
        alert_cells = decision_engine.get_alert_cells(decisions)
        
        # Write to dashboard database
        _write_predictions_to_db(predictions, alert_cells, rainfall_data)
        
        return jsonify({
            'success': True,
            'predictions_generated': len(predictions),
            'alerts_triggered': len(alert_cells),
            'high_risk_cells': len([p for p in alert_cells if p['risk_level'] == 'HIGH']),
            'critical_cells': len([p for p in alert_cells if p['risk_level'] == 'CRITICAL']),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trigger_cycle', methods=['POST'])
def api_trigger_cycle():
    """Trigger a manual prediction cycle with current or custom data"""
    if not REALTIME_ENABLED:
        return jsonify({'success': False, 'error': 'Realtime system not available'}), 503
    
    try:
        # Get optional parameters
        data = request.get_json() or {}
        custom_rainfall = data.get('custom_rainfall', None)
        
        # Get current rainfall data
        if custom_rainfall:
            # Use custom rainfall value
            dates = pd.date_range(end=datetime.now(), periods=15, freq='D')
            rainfall_data = pd.DataFrame({
                'date': dates,
                'rain': [float(custom_rainfall)] * 15
            })
        else:
            # Use actual historical data
            rainfall_data = data_ingestion.get_updated_history()
        
        # Run full prediction cycle with all required arguments
        current_date = datetime.now()
        predictions = inference_engine.predict_all_cells(static_data, rainfall_data, current_date)
        decisions = decision_engine.process_predictions(predictions)
        alert_cells = decision_engine.get_alert_cells(decisions)
        
        # Write to database
        _write_predictions_to_db(predictions, alert_cells, rainfall_data)
        
        # Get statistics
        risk_dist = predictions['risk_level'].value_counts().to_dict()
        
        return jsonify({
            'success': True,
            'cycle_completed': True,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_cells': len(predictions),
                'alerts_triggered': len(alert_cells),
                'risk_distribution': risk_dist,
                'avg_probability': float(predictions['probability'].mean()),
                'max_probability': float(predictions['probability'].max()),
                'latest_rainfall': float(rainfall_data.iloc[-1]['rain' if 'rain' in rainfall_data.columns else 'rain_mm']) if len(rainfall_data) > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _write_predictions_to_db(predictions, alerts, rainfall_data):
    """Helper function to write predictions and alerts to dashboard database"""
    db_path = os.path.join(os.path.dirname(__file__), 'sentinel.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear old predictions (keep last 500)
        cursor.execute('DELETE FROM predictions WHERE id NOT IN (SELECT id FROM predictions ORDER BY timestamp DESC LIMIT 500)')
        
        # Get latest rainfall
        rainfall_col = 'rain' if 'rain' in rainfall_data.columns else 'rain_mm'
        latest_rainfall = rainfall_data.iloc[-1][rainfall_col] if len(rainfall_data) > 0 else 0
        
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
                float(row.get('slope', 0)),
                float(latest_rainfall)
            ))
        
        # Write alerts (all high/critical alerts)
        for idx, alert in alerts.iterrows():
            severity = alert['risk_level']
            message = f"Landslide risk {severity} at {alert['cell_id']}. {alert['action']}."
            location = f"Cell {alert['cell_id']} ({alert.get('lat', 0):.4f}, {alert.get('lon', 0):.4f})"
            
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
        cursor.execute('UPDATE system_info SET value = ?, updated_at = ? WHERE key = "network_status"',
                     ('ONLINE', datetime.now().isoformat()))
        
        conn.commit()
        
    finally:
        conn.close()


@app.template_filter('timeago')
def timeago_filter(timestamp):
    """Convert timestamp to relative time"""
    if not timestamp:
        return 'N/A'
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return 'Just now'
    elif diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f'{mins}m ago'
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f'{hours}h ago'
    else:
        days = int(diff.total_seconds() / 86400)
        return f'{days}d ago'


@app.template_filter('format_datetime')
def format_datetime_filter(timestamp, format_str='%Y-%m-%d %H:%M:%S'):
    """Format timestamp"""
    if not timestamp:
        return 'N/A'
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    
    return timestamp.strftime(format_str)


@app.template_filter('risk_class')
def risk_class_filter(probability):
    """Convert probability to risk class"""
    if probability is None:
        return 'UNKNOWN'
    
    prob = float(probability)
    if prob < 0.3:
        return 'LOW'
    elif prob < 0.6:
        return 'MEDIUM'
    elif prob < 0.85:
        return 'HIGH'
    else:
        return 'CRITICAL'


@app.template_filter('risk_color')
def risk_color_filter(probability):
    """Convert probability to risk color class"""
    if probability is None:
        return 'risk-unknown'
    
    prob = float(probability)
    if prob < 0.3:
        return 'risk-low'
    elif prob < 0.6:
        return 'risk-medium'
    elif prob < 0.85:
        return 'risk-high'
    else:
        return 'risk-critical'


if __name__ == '__main__':
    # Initialize database
    db.init_db()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
