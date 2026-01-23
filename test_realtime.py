"""
Test script to verify real-time dashboard integration
"""
import sqlite3
import os
from datetime import datetime

def check_dashboard_updates():
    """Check if dashboard database is being updated"""
    db_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'sentinel.db')
    
    if not os.path.exists(db_path):
        print("❌ Dashboard database not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check predictions
    cursor.execute('SELECT COUNT(*), MAX(timestamp) FROM predictions')
    pred_count, latest_pred = cursor.fetchone()
    print(f"\n✓ Predictions: {pred_count} rows")
    print(f"  Latest: {latest_pred}")
    
    # Check alerts
    cursor.execute('SELECT COUNT(*), MAX(sent_time) FROM alerts')
    alert_count, latest_alert = cursor.fetchone()
    print(f"\n✓ Alerts: {alert_count} rows")
    print(f"  Latest: {latest_alert}")
    
    # Check system info
    cursor.execute('SELECT key, value, updated_at FROM system_info ORDER BY updated_at DESC LIMIT 5')
    system_info = cursor.fetchall()
    print(f"\n✓ System Info:")
    for key, value, updated_at in system_info:
        print(f"  {key}: {value} (updated: {updated_at})")
    
    conn.close()
    
    # Check if data is recent (within last 5 minutes)
    if latest_pred:
        from datetime import datetime, timedelta
        try:
            pred_time = datetime.fromisoformat(latest_pred.replace('Z', ''))
            time_diff = datetime.now() - pred_time
            if time_diff < timedelta(minutes=5):
                print(f"\n✅ Dashboard is LIVE! (last update {time_diff.seconds}s ago)")
                return True
            else:
                print(f"\n⚠️  Dashboard data is stale (last update {time_diff.seconds//60} minutes ago)")
                return False
        except:
            pass
    
    print(f"\n⚠️  Dashboard has data but timestamps couldn't be verified")
    return False

if __name__ == '__main__':
    print("="*70)
    print("SENTINEL-LEWS REAL-TIME DASHBOARD TEST")
    print("="*70)
    
    check_dashboard_updates()
    
    print("\n" + "="*70)
    print("INSTRUCTIONS:")
    print("="*70)
    print("1. Run: python main.py")
    print("2. Wait 30 seconds for first prediction cycle")
    print("3. Run: python test_realtime.py (to verify updates)")
    print("4. Open dashboard: python dashboard/app.py")
    print("5. Visit: http://localhost:5000")
    print("6. Watch the 'Last Data Update' timestamp change every 15s")
    print("="*70)
