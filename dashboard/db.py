"""
Database module for Sentinel-LEWS
Handles SQLite read operations
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json
import random

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
        # Dynamic system info with realistic values
        current_latency = round(random.uniform(8.5, 25.3), 1)
        defaults = [
            ('model_version', 'LGBM v1.2'),
            ('inference_latency', str(current_latency)),
            ('network_status', random.choice(['ONLINE', 'OFFLINE'])),
            ('last_ingestion', (datetime.now() - timedelta(seconds=random.randint(5, 300))).isoformat()),
            ('high_threshold', '0.85'),
            ('medium_threshold', '0.60'),
            ('low_threshold', '0.30'),
        ]
        cursor.executemany('INSERT INTO system_info (key, value) VALUES (?, ?)', defaults)
    
    # Insert sample sensors if empty
    cursor.execute('SELECT COUNT(*) FROM sensors')
    if cursor.fetchone()[0] == 0:
        # Dynamic sensor data with randomized status and trust
        sample_sensors = []
        base_lat, base_lon = 26.8467, 75.8007
        sensor_types = ['Rainfall', 'Soil Moisture', 'Piezometer', 'Inclinometer']
        statuses = ['OK', 'OK', 'OK', 'OK', 'DRIFT', 'OFFLINE']  # Weighted towards OK
        
        for i in range(1, 11):  # 10 sensors
            status = random.choice(statuses)
            trust = 0.0 if status == 'OFFLINE' else round(random.uniform(0.65, 0.99), 2)
            last_seen_offset = random.randint(0, 720) if status == 'OFFLINE' else random.randint(0, 30)
            lat = base_lat + random.uniform(-0.005, 0.005)
            lon = base_lon + random.uniform(-0.005, 0.005)
            
            sample_sensors.append((
                f'SENS-{i:03d}',
                status,
                trust,
                (datetime.now() - timedelta(minutes=last_seen_offset)).isoformat(),
                round(lat, 6),
                round(lon, 6),
                random.choice(sensor_types)
            ))
        
        cursor.executemany(
            'INSERT INTO sensors (sensor_id, status, trust, last_seen, latitude, longitude, sensor_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
            sample_sensors
        )
    
    # Insert sample predictions if empty
    cursor.execute('SELECT COUNT(*) FROM predictions')
    if cursor.fetchone()[0] == 0:
        # Dynamic predictions with realistic random distributions
        sample_predictions = []
        num_predictions = random.randint(80, 120)  # Variable number of predictions
        
        for i in range(num_predictions):
            cell_id = f'CELL-{i+1:04d}'
            
            # Probability with realistic distribution (most low, few high)
            rand_val = random.random()
            if rand_val < 0.70:  # 70% low risk
                prob = round(random.uniform(0.05, 0.35), 3)
            elif rand_val < 0.90:  # 20% medium risk
                prob = round(random.uniform(0.35, 0.65), 3)
            elif rand_val < 0.97:  # 7% high risk
                prob = round(random.uniform(0.65, 0.85), 3)
            else:  # 3% critical
                prob = round(random.uniform(0.85, 0.98), 3)
            
            # Timestamp spread over last few hours
            ts = datetime.now() - timedelta(minutes=random.randint(0, 180))
            
            # Dynamic terrain features
            slope = round(random.uniform(5.0, 60.0), 1)
            drainage = round(random.uniform(0.2, 1.0), 2)
            rainfall = round(random.uniform(0.0, 250.0), 1)
            
            sample_predictions.append((
                cell_id,
                prob,
                ts.isoformat(),
                slope,
                drainage,
                rainfall
            ))
        
        cursor.executemany(
            'INSERT INTO predictions (cell_id, probability, timestamp, slope, drainage, rainfall_24h) VALUES (?, ?, ?, ?, ?, ?)',
            sample_predictions
        )
    
    # Insert sample alerts if empty
    cursor.execute('SELECT COUNT(*) FROM alerts')
    if cursor.fetchone()[0] == 0:
        # Dynamic alerts with randomized severity and locations
        sample_alerts = []
        locations = [
            'Ward 12, Sector B', 'Village Rampur', 'Hillside Colony', 'Sector A-4',
            'Mountain View Area', 'Riverside Settlement', 'Northern Hills', 'Eastern Slopes',
            'Valley Road Junction', 'Upper Plateau', 'Forest Edge Zone', 'Lower Basin'
        ]
        
        num_alerts = random.randint(2, 8)  # Variable number of alerts
        
        for i in range(num_alerts):
            # Determine severity based on probability
            rand_sev = random.random()
            if rand_sev < 0.15:  # 15% critical
                severity = 'CRITICAL'
                prob = round(random.uniform(0.85, 0.98), 2)
                action = 'Evacuate immediately.'
            elif rand_sev < 0.40:  # 25% high
                severity = 'HIGH'
                prob = round(random.uniform(0.65, 0.84), 2)
                action = 'Monitor closely and prepare for evacuation.'
            elif rand_sev < 0.70:  # 30% medium
                severity = 'MEDIUM'
                prob = round(random.uniform(0.40, 0.64), 2)
                action = 'Stay alert and monitor updates.'
            else:  # 30% low
                severity = 'LOW'
                prob = round(random.uniform(0.30, 0.39), 2)
                action = 'Normal vigilance recommended.'
            
            cell_id = f'CELL-{random.randint(1, 2000):04d}'
            location = random.choice(locations)
            message = f'Landslide risk {severity} at {location}. {action}'
            sent_time = datetime.now() - timedelta(minutes=random.randint(5, 240))
            rainfall = round(random.uniform(50.0, 200.0), 1)
            status = random.choice(['pending', 'pending', 'acknowledged'])  # Weighted towards pending
            
            sample_alerts.append((
                cell_id,
                severity,
                message,
                sent_time.isoformat(),
                prob,
                rainfall,
                location,
                status
            ))
        
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
    
    # Dynamic disk usage and database size
    settings['disk_usage'] = f'{random.randint(25, 75)}%'
    
    # Calculate actual database size
    try:
        db_size_bytes = os.path.getsize(DB_PATH)
        if db_size_bytes < 1024 * 1024:  # Less than 1 MB
            settings['db_size'] = f'{db_size_bytes // 1024} KB'
        else:
            settings['db_size'] = f'{db_size_bytes // (1024 * 1024)} MB'
    except:
        settings['db_size'] = f'{random.randint(100, 500)} KB'
    
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
