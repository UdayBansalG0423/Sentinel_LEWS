"""
Sentinel-LEWS Dashboard
District-level landslide early warning system control panel
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sentinel-lews-district-control'


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
    risk_data = db.get_risk_map_data()
    return jsonify(risk_data)


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
