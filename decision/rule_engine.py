"""
Decision Rule Engine
Applies human-logic safety rules on top of ML predictions.
"""
import pandas as pd
from datetime import datetime

class LandslideDecisionEngine:
    """Applies decision rules to convert predictions into actionable risk levels."""
    
    def __init__(self, 
                 critical_threshold=0.8,
                 high_threshold=0.6,
                 medium_threshold=0.3,
                 slope_critical=45,
                 slope_high=30):
        """
        Initialize decision engine with thresholds.
        
        Args:
            critical_threshold: Probability threshold for CRITICAL risk (default 0.8)
            high_threshold: Probability threshold for HIGH risk (default 0.6)
            medium_threshold: Probability threshold for MEDIUM risk (default 0.3)
            slope_critical: Slope angle for critical terrain (degrees)
            slope_high: Slope angle for high-risk terrain (degrees)
        """
        self.critical_threshold = critical_threshold
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.slope_critical = slope_critical
        self.slope_high = slope_high
    
    def apply_rules(self, probability, slope, rainfall_15d=None):
        """
        Apply decision rules to determine risk level and action.
        
        Args:
            probability: ML predicted probability (0-1)
            slope: Terrain slope (degrees)
            rainfall_15d: Optional 15-day cumulative rainfall (mm/hr)
            
        Returns:
            dict with risk_level, action, and reasoning
        """
        # Base risk from probability
        if probability >= self.critical_threshold:
            base_risk = "CRITICAL"
        elif probability >= self.high_threshold:
            base_risk = "HIGH"
        elif probability >= self.medium_threshold:
            base_risk = "MEDIUM"
        else:
            base_risk = "LOW"
        
        # Apply terrain rules
        reasons = []
        
        # Rule 1: Extreme slope overrides to CRITICAL
        if slope >= self.slope_critical and probability >= self.high_threshold:
            risk_level = "CRITICAL"
            reasons.append(f"Extreme slope ({slope:.1f}°)")
        else:
            risk_level = base_risk
        
        # Rule 2: Steep slope + medium probability = HIGH
        if slope >= self.slope_high and probability >= self.medium_threshold:
            if risk_level not in ["CRITICAL", "HIGH"]:
                risk_level = "HIGH"
                reasons.append(f"Steep slope ({slope:.1f}°) + elevated probability")
        
        # Rule 3: Heavy sustained rainfall boosts risk
        if rainfall_15d is not None and rainfall_15d > 0.15:  # >150mm in 15 days
            if risk_level == "MEDIUM":
                risk_level = "HIGH"
                reasons.append(f"Heavy sustained rainfall ({rainfall_15d:.3f} mm/hr)")
            reasons.append("Prolonged rainfall event")
        
        # Determine action
        if risk_level == "CRITICAL":
            action = "IMMEDIATE_EVACUATION"
        elif risk_level == "HIGH":
            action = "SEND_ALERT"
        elif risk_level == "MEDIUM":
            action = "MONITOR"
        else:
            action = "NORMAL"
        
        return {
            'risk_level': risk_level,
            'action': action,
            'probability': probability,
            'base_risk': base_risk,
            'reasoning': reasons if reasons else ["Standard ML prediction"]
        }
    
    def process_predictions(self, predictions_df):
        """
        Apply decision rules to all predictions.
        
        Args:
            predictions_df: DataFrame with columns ['probability', 'slope', 'rain_15d']
            
        Returns:
            DataFrame with added decision columns
        """
        results = []
        
        for idx, row in predictions_df.iterrows():
            decision = self.apply_rules(
                probability=row['probability'],
                slope=row['slope'],
                rainfall_15d=row.get('rain_15d', None)
            )
            results.append(decision)
        
        # Add decision columns to DataFrame
        df = predictions_df.copy()
        df['risk_level'] = [r['risk_level'] for r in results]
        df['action'] = [r['action'] for r in results]
        df['reasoning'] = ['; '.join(r['reasoning']) for r in results]
        
        return df
    
    def get_alert_cells(self, processed_predictions):
        """
        Filter cells that require immediate alerts.
        
        Args:
            processed_predictions: DataFrame from process_predictions
            
        Returns:
            DataFrame with only cells requiring alerts (HIGH or CRITICAL)
        """
        alert_cells = processed_predictions[
            processed_predictions['action'].isin(['SEND_ALERT', 'IMMEDIATE_EVACUATION'])
        ].copy()
        
        alert_cells = alert_cells.sort_values('probability', ascending=False)
        
        return alert_cells
    
    def generate_alert_summary(self, alert_cells):
        """
        Generate human-readable alert summary.
        
        Args:
            alert_cells: DataFrame from get_alert_cells
            
        Returns:
            str with formatted alert summary
        """
        if len(alert_cells) == 0:
            return "No alerts at this time. All areas safe."
        
        summary = []
        summary.append(f"⚠️  LANDSLIDE ALERT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        summary.append(f"{'='*70}")
        
        critical = len(alert_cells[alert_cells['risk_level'] == 'CRITICAL'])
        high = len(alert_cells[alert_cells['risk_level'] == 'HIGH'])
        
        summary.append(f"Total Alert Cells: {len(alert_cells)}")
        if critical > 0:
            summary.append(f"  🔴 CRITICAL: {critical} cells - IMMEDIATE EVACUATION REQUIRED")
        if high > 0:
            summary.append(f"  🟠 HIGH: {high} cells - ALERT ISSUED")
        
        summary.append(f"\nTop 5 Highest Risk Locations:")
        summary.append(f"{'='*70}")
        
        for idx, row in alert_cells.head(5).iterrows():
            summary.append(
                f"Cell {row['cell_id']}: "
                f"{row['risk_level']:8s} "
                f"({row['probability']:.1%}) "
                f"Lat: {row['lat']:.4f}, Lon: {row['lon']:.4f}"
            )
            summary.append(f"  Action: {row['action']}")
            summary.append(f"  Reason: {row['reasoning']}")
            summary.append("")
        
        return "\n".join(summary)


# Backward compatibility
def decide(prob):
    """Legacy function for simple decision (kept for compatibility)."""
    return prob > 0.7
