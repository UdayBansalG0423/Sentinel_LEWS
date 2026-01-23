"""
Alert Manager Module
Handles alert generation, logging, and delivery (SMS/console/file).
"""
import os
import csv
from datetime import datetime

class AlertManager:
    """Manages landslide alerts and notifications."""
    
    def __init__(self, log_dir=None, enable_sms=False):
        """
        Initialize alert manager.
        
        Args:
            log_dir: Directory to store alert logs. If None, uses default.
            enable_sms: Whether to enable SMS alerts (requires GSM/Twilio setup)
        """
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        
        self.log_dir = log_dir
        self.enable_sms = enable_sms
        
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Alert log file
        self.alert_log_file = os.path.join(self.log_dir, "alerts.csv")
        
        # Initialize log file if it doesn't exist
        if not os.path.exists(self.alert_log_file):
            with open(self.alert_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'cell_id', 'lat', 'lon', 'risk_level', 
                    'probability', 'action', 'message_sent'
                ])
    
    def send_alert(self, alert_data):
        """
        Send alert for a single cell.
        
        Args:
            alert_data: dict with cell_id, lat, lon, risk_level, probability, action
            
        Returns:
            bool indicating if alert was sent successfully
        """
        timestamp = datetime.now().isoformat()
        
        # Generate alert message
        message = self._generate_alert_message(alert_data)
        
        # Console alert (always enabled)
        print(f"\n{'='*70}")
        print("🚨 ALERT TRIGGERED")
        print(f"{'='*70}")
        print(message)
        print(f"{'='*70}")
        
        # SMS alert (if enabled)
        message_sent = False
        if self.enable_sms:
            message_sent = self._send_sms(alert_data, message)
        
        # Log alert
        self._log_alert(timestamp, alert_data, message_sent)
        
        return True
    
    def send_batch_alerts(self, alert_cells_df):
        """
        Send alerts for multiple cells.
        
        Args:
            alert_cells_df: DataFrame with alert-worthy cells
            
        Returns:
            dict with summary statistics
        """
        if len(alert_cells_df) == 0:
            print("✓ No alerts to send")
            return {'total': 0, 'sent': 0, 'logged': 0}
        
        print(f"\n{'='*70}")
        print(f"SENDING {len(alert_cells_df)} ALERTS")
        print(f"{'='*70}")
        
        sent_count = 0
        for idx, row in alert_cells_df.iterrows():
            alert_data = {
                'cell_id': row['cell_id'],
                'lat': row['lat'],
                'lon': row['lon'],
                'risk_level': row['risk_level'],
                'probability': row['probability'],
                'action': row['action'],
                'slope': row.get('slope', 0)
            }
            
            if self.send_alert(alert_data):
                sent_count += 1
        
        summary = {
            'total': len(alert_cells_df),
            'sent': sent_count,
            'logged': sent_count,
            'critical': len(alert_cells_df[alert_cells_df['risk_level'] == 'CRITICAL']),
            'high': len(alert_cells_df[alert_cells_df['risk_level'] == 'HIGH'])
        }
        
        print(f"\n✓ Alert batch complete:")
        print(f"  Total alerts: {summary['total']}")
        print(f"  Successfully sent: {summary['sent']}")
        print(f"  Logged to file: {summary['logged']}")
        
        return summary
    
    def _generate_alert_message(self, alert_data):
        """Generate human-readable alert message."""
        risk = alert_data['risk_level']
        prob = alert_data['probability']
        cell_id = alert_data['cell_id']
        lat = alert_data['lat']
        lon = alert_data['lon']
        action = alert_data['action']
        
        if action == "IMMEDIATE_EVACUATION":
            urgency = "🔴 CRITICAL - EVACUATE IMMEDIATELY"
        elif action == "SEND_ALERT":
            urgency = "🟠 HIGH RISK - PREPARE TO EVACUATE"
        else:
            urgency = "🟡 ELEVATED RISK - STAY ALERT"
        
        message = f"""
{urgency}

Landslide Risk Alert
--------------------
Location: Cell {cell_id}
Coordinates: {lat:.4f}°N, {lon:.4f}°E
Risk Level: {risk}
Probability: {prob:.1%}
Action Required: {action.replace('_', ' ')}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Sentinel-LEWS Landslide Early Warning System
"""
        return message.strip()
    
    def _send_sms(self, alert_data, message):
        """
        Send SMS alert (placeholder for future implementation).
        
        To implement:
        - GSM modem integration (e.g., SIM800)
        - Twilio API
        - Other SMS gateway
        """
        # Placeholder for SMS sending
        # In production, integrate with:
        # - GSM modem: use pyserial + AT commands
        # - Twilio: use twilio library
        # - Other SMS API
        
        print("📱 SMS: (Not configured - Demo mode)")
        return False
    
    def _log_alert(self, timestamp, alert_data, message_sent):
        """Log alert to CSV file."""
        with open(self.alert_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                alert_data['cell_id'],
                alert_data['lat'],
                alert_data['lon'],
                alert_data['risk_level'],
                alert_data['probability'],
                alert_data['action'],
                message_sent
            ])
    
    def get_alert_history(self, limit=100):
        """
        Retrieve recent alert history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            list of alert records
        """
        if not os.path.exists(self.alert_log_file):
            return []
        
        with open(self.alert_log_file, 'r') as f:
            reader = csv.DictReader(f)
            alerts = list(reader)
        
        # Return most recent first
        return alerts[-limit:][::-1]
    
    def get_alert_statistics(self):
        """Get summary statistics of all alerts."""
        history = self.get_alert_history(limit=None)
        
        if not history:
            return {'total': 0}
        
        stats = {
            'total': len(history),
            'by_risk_level': {},
            'by_action': {},
            'latest_alert': history[0]['timestamp'] if history else None
        }
        
        for alert in history:
            risk = alert['risk_level']
            action = alert['action']
            
            stats['by_risk_level'][risk] = stats['by_risk_level'].get(risk, 0) + 1
            stats['by_action'][action] = stats['by_action'].get(action, 0) + 1
        
        return stats


def demo_alerts():
    """Demo: Alert system."""
    print("="*70)
    print("ALERT SYSTEM DEMO")
    print("="*70)
    
    # Initialize alert manager
    alert_mgr = AlertManager()
    
    # Simulate some alerts
    print("\nSimulating alerts...")
    
    alerts = [
        {
            'cell_id': 1001,
            'lat': 31.1050,
            'lon': 77.1734,
            'risk_level': 'CRITICAL',
            'probability': 0.92,
            'action': 'IMMEDIATE_EVACUATION',
            'slope': 48.5
        },
        {
            'cell_id': 1023,
            'lat': 31.1080,
            'lon': 77.1750,
            'risk_level': 'HIGH',
            'probability': 0.74,
            'action': 'SEND_ALERT',
            'slope': 35.2
        }
    ]
    
    for alert_data in alerts:
        alert_mgr.send_alert(alert_data)
    
    # Show statistics
    print(f"\n{'='*70}")
    print("ALERT STATISTICS")
    print(f"{'='*70}")
    stats = alert_mgr.get_alert_statistics()
    print(f"Total alerts: {stats['total']}")
    print(f"By risk level: {stats['by_risk_level']}")
    print(f"Alert log: {alert_mgr.alert_log_file}")
    
    print(f"\n✓ Alert system operational")


if __name__ == "__main__":
    demo_alerts()
