"""
Database module for Sentinel-LEWS
Handles SQLite read operations
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'sentinel.db')


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with schema if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_id TEXT NOT NULL,
            probability REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            slope REAL,
            drainage REAL,
            rainfall_24h REAL,
            features TEXT
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            probability REAL,
            rainfall_24h REAL,
            location TEXT,
            status TEXT DEFAULT 'pending',
            acknowledged_at DATETIME
        )
    ''')
    
    # Create sensors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensors (
            sensor_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'OK',
            trust REAL DEFAULT 1.0,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            latitude REAL,
            longitude REAL,
            sensor_type TEXT
        )
    ''')
    
    # Create system_info table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_info (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default system info if not exists
    cursor.execute('SELECT COUNT(*) FROM system_info')
    if cursor.fetchone()[0] == 0:
        defaults = [
            ('model_version', 'LGBM v1.2'),
            ('inference_latency', '12.4'),
            ('network_status', 'OFFLINE'),
            ('last_ingestion', datetime.now().isoformat()),
            ('high_threshold', '0.85'),
            ('medium_threshold', '0.60'),
            ('low_threshold', '0.30'),
        ]
        cursor.executemany('INSERT INTO system_info (key, value) VALUES (?, ?)', defaults)
    
    # Insert sample sensors if empty
    cursor.execute('SELECT COUNT(*) FROM sensors')
    if cursor.fetchone()[0] == 0:
        sample_sensors = [
            ('SENS-001', 'OK', 0.98, datetime.now().isoformat(), 26.8467, 75.8007, 'Rainfall'),
            ('SENS-002', 'OK', 0.95, (datetime.now() - timedelta(minutes=5)).isoformat(), 26.8470, 75.8010, 'Rainfall'),
            ('SENS-003', 'DRIFT', 0.72, (datetime.now() - timedelta(hours=2)).isoformat(), 26.8465, 75.8015, 'Soil Moisture'),
            ('SENS-004', 'OFFLINE', 0.00, (datetime.now() - timedelta(hours=12)).isoformat(), 26.8480, 75.8020, 'Rainfall'),
            ('SENS-005', 'OK', 0.96, datetime.now().isoformat(), 26.8475, 75.8005, 'Soil Moisture'),
        ]
        cursor.executemany(
            'INSERT INTO sensors (sensor_id, status, trust, last_seen, latitude, longitude, sensor_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
            sample_sensors
        )
    
    # Insert sample predictions if empty
    cursor.execute('SELECT COUNT(*) FROM predictions')
    if cursor.fetchone()[0] == 0:
        sample_predictions = []
        for i in range(50):
            cell_id = f'CELL-{i+1:03d}'
            prob = min(0.95, max(0.05, 0.3 + (i % 10) * 0.08))
            ts = datetime.now() - timedelta(minutes=i*5)
            sample_predictions.append((
                cell_id,
                prob,
                ts.isoformat(),
                35.0 + (i % 15),
                0.6 + (i % 5) * 0.1,
                120.0 + (i % 20) * 5
            ))
        
        cursor.executemany(
            'INSERT INTO predictions (cell_id, probability, timestamp, slope, drainage, rainfall_24h) VALUES (?, ?, ?, ?, ?, ?)',
            sample_predictions
        )
    
    # Insert sample alerts if empty
    cursor.execute('SELECT COUNT(*) FROM alerts')
    if cursor.fetchone()[0] == 0:
        sample_alerts = [
            ('CELL-045', 'CRITICAL', 'Landslide risk CRITICAL at Ward 12, Sector B. Evacuate immediately.', 
             (datetime.now() - timedelta(minutes=15)).isoformat(), 0.91, 145.3, 'Ward 12, Sector B', 'pending'),
            ('CELL-032', 'HIGH', 'Landslide risk HIGH at Village Rampur. Monitor closely.', 
             (datetime.now() - timedelta(hours=1)).isoformat(), 0.78, 132.1, 'Village Rampur', 'acknowledged'),
            ('CELL-018', 'MEDIUM', 'Landslide risk MEDIUM at Hillside Colony. Stay alert.', 
             (datetime.now() - timedelta(hours=3)).isoformat(), 0.52, 118.5, 'Hillside Colony', 'acknowledged'),
        ]
        
        cursor.executemany(
            'INSERT INTO alerts (cell_id, severity, message, sent_time, probability, rainfall_24h, location, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            sample_alerts
        )
    
    conn.commit()
    conn.close()


def get_system_summary():
    """Get system summary for dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get high-risk cells count
    cursor.execute('SELECT COUNT(*) FROM predictions WHERE probability >= 0.6 AND timestamp > datetime("now", "-10 minutes")')
    high_risk_cells = cursor.fetchone()[0]
    
    # Get active alerts count
    cursor.execute('SELECT COUNT(*) FROM alerts WHERE status = "pending"')
    active_alerts = cursor.fetchone()[0]
    
    # Get sensors online percentage
    cursor.execute('SELECT COUNT(*) FROM sensors WHERE status = "OK"')
    sensors_ok = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM sensors')
    total_sensors = cursor.fetchone()[0]
    sensors_online_pct = (sensors_ok / total_sensors * 100) if total_sensors > 0 else 0
    
    # Get average rainfall 24h
    cursor.execute('SELECT AVG(rainfall_24h) FROM predictions WHERE timestamp > datetime("now", "-1 day")')
    avg_rainfall = cursor.fetchone()[0] or 0
    
    # Get system info
    cursor.execute('SELECT key, value FROM system_info')
    system_info = {row['key']: row['value'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        'high_risk_cells': high_risk_cells,
        'active_alerts': active_alerts,
        'sensors_online_pct': round(sensors_online_pct, 1),
        'avg_rainfall_24h': round(avg_rainfall, 1),
        'network_status': system_info.get('network_status', 'OFFLINE'),
        'last_ingestion': system_info.get('last_ingestion'),
        'inference_latency': system_info.get('inference_latency', '0'),
        'model_version': system_info.get('model_version', 'N/A'),
        'timestamp': datetime.now().isoformat()
    }


def get_alerts(severity='all', status='all', limit=100):
    """Get alerts with optional filtering"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM alerts WHERE 1=1'
    params = []
    
    if severity != 'all':
        query += ' AND severity = ?'
        params.append(severity.upper())
    
    if status != 'all':
        query += ' AND status = ?'
        params.append(status)
    
    query += ' ORDER BY sent_time DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    alerts = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return alerts


def get_recent_alerts(limit=10):
    """Get recent alerts for live feed"""
    return get_alerts(limit=limit)


def get_sensors():
    """Get all sensors"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM sensors ORDER BY sensor_id')
    sensors = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return sensors


def get_prediction_history(limit=100):
    """Get prediction history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM predictions 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    history = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return history


def get_system_settings():
    """Get system settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT key, value FROM system_info')
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    
    # Get disk usage (placeholder)
    settings['disk_usage'] = '42%'
    settings['db_size'] = '128 MB'
    
    conn.close()
    return settings


def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE alerts 
        SET status = 'acknowledged', acknowledged_at = ? 
        WHERE id = ?
    ''', (datetime.now().isoformat(), alert_id))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return {'success': success, 'alert_id': alert_id}


def send_alert_sms(alert_id):
    """Simulate sending SMS for an alert"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM alerts WHERE id = ?', (alert_id,))
    alert = cursor.fetchone()
    
    if not alert:
        conn.close()
        return {'success': False, 'error': 'Alert not found'}
    
    # In real implementation, this would trigger GSM modem
    # For now, just update status
    cursor.execute('''
        UPDATE alerts 
        SET status = 'sent' 
        WHERE id = ?
    ''', (alert_id,))
    
    conn.commit()
    conn.close()
    
    return {'success': True, 'alert_id': alert_id, 'message': 'SMS triggered via GSM modem'}


def get_risk_map_data():
    """Get latest risk data for map visualization"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cell_id, probability, timestamp, rainfall_24h, slope
        FROM predictions
        WHERE timestamp > datetime("now", "-10 minutes")
        ORDER BY probability DESC
        LIMIT 200
    ''')
    
    data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return data


def get_rainfall_data(hours=48):
    """Get rainfall data for charting"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            strftime('%Y-%m-%d %H:00', timestamp) as hour,
            AVG(rainfall_24h) as avg_rainfall
        FROM predictions
        WHERE timestamp > datetime("now", "-" || ? || " hours")
        GROUP BY hour
        ORDER BY hour
    ''', (hours,))
    
    data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return data


def get_risk_distribution():
    """Get risk probability distribution"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            CASE 
                WHEN probability < 0.3 THEN 'LOW'
                WHEN probability < 0.6 THEN 'MEDIUM'
                WHEN probability < 0.85 THEN 'HIGH'
                ELSE 'CRITICAL'
            END as risk_class,
            COUNT(*) as count
        FROM predictions
        WHERE timestamp > datetime("now", "-10 minutes")
        GROUP BY risk_class
    ''')
    
    data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return data


def export_history(format_type='json'):
    """Export prediction history"""
    history = get_prediction_history(limit=1000)
    
    if format_type == 'json':
        return {'data': history, 'format': 'json'}
    else:
        # For CSV/PDF, return data that frontend can process
        return {'data': history, 'format': format_type}
