"""
Module Connection Test Script
Tests all imports and data flow between components
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("SENTINEL-LEWS MODULE CONNECTION TEST")
print("=" * 60)

# Test 1: Core Modules
print("\n[Test 1] Core Module Imports...")
try:
    import main
    print("  ✓ main.py imported successfully")
except ImportError as e:
    print(f"  ✗ main.py import failed: {e}")

try:
    from runtime.inference import LandslidePredictionEngine
    print("  ✓ runtime.inference imported successfully")
except ImportError as e:
    print(f"  ✗ runtime.inference import failed: {e}")

try:
    from data.ingestion import RainfallDataIngestion
    print("  ✓ data.ingestion imported successfully")
except ImportError as e:
    print(f"  ✗ data.ingestion import failed: {e}")

try:
    from decision.rule_engine import LandslideDecisionEngine
    print("  ✓ decision.rule_engine imported successfully")
except ImportError as e:
    print(f"  ✗ decision.rule_engine import failed: {e}")

try:
    from alerts.alert_manager import AlertManager
    print("  ✓ alerts.alert_manager imported successfully")
except ImportError as e:
    print(f"  ✗ alerts.alert_manager import failed: {e}")

# Test 2: Training Modules
print("\n[Test 2] Training Module Imports...")
try:
    from models import train
    print("  ✓ models.train imported successfully")
except ImportError as e:
    print(f"  ✗ models.train import failed: {e}")

try:
    from dataset_builder import build_training
    print("  ✓ dataset_builder.build_training imported successfully")
except ImportError as e:
    print(f"  ✗ dataset_builder.build_training import failed: {e}")

# Test 3: Dashboard Module
print("\n[Test 3] Dashboard Module...")
try:
    from dashboard import app as dashboard_app
    print("  ✓ dashboard.app imported successfully")
except ImportError as e:
    print(f"  ✗ dashboard.app import failed: {e}")

try:
    from dashboard import db as dashboard_db
    print("  ✓ dashboard.db imported successfully")
except ImportError as e:
    print(f"  ✗ dashboard.db import failed: {e}")

# Test 4: Data Flow
print("\n[Test 4] Data Flow Test...")
try:
    print("  → Testing: Data Ingestion → Inference")
    ingestion = RainfallDataIngestion()
    rain_data = ingestion.get_updated_history()
    print(f"    ✓ Loaded {len(rain_data)} days of rainfall history")
    
    engine = LandslidePredictionEngine()
    predictions = engine.predict_all_cells(rain_data)
    print(f"    ✓ Generated {len(predictions)} predictions")
    
except Exception as e:
    print(f"    ✗ Data flow test failed: {e}")

try:
    print("  → Testing: Inference → Decision → Alerts")
    decision = LandslideDecisionEngine()
    decisions = decision.process_predictions(predictions)
    print(f"    ✓ Processed {len(decisions)} decisions")
    
    high_risk = decision.get_alert_cells(decisions)
    print(f"    ✓ Identified {len(high_risk)} high-risk cells")
    
    alert_mgr = AlertManager()
    print(f"    ✓ Alert manager initialized")
    
except Exception as e:
    print(f"    ✗ Decision flow test failed: {e}")

# Test 5: File System
print("\n[Test 5] Critical Files Check...")
files_to_check = [
    ("Model file", "models/lgb_model.txt"),
    ("Static features", "dataset_builder/shimla_static.csv"),
    ("Rain history", "dataset_builder/shimla_rain_features.csv"),
    ("Config", "config/config.yaml"),
]

for name, path in files_to_check:
    if os.path.exists(path):
        size_kb = os.path.getsize(path) / 1024
        print(f"  ✓ {name}: {path} ({size_kb:.1f} KB)")
    else:
        print(f"  ✗ {name}: {path} (NOT FOUND)")

# Test 6: Dependencies
print("\n[Test 6] Python Package Dependencies...")
dependencies = [
    "pandas",
    "numpy",
    "lightgbm",
    "flask",
    "rasterio",
]

for pkg in dependencies:
    try:
        __import__(pkg)
        print(f"  ✓ {pkg} installed")
    except ImportError:
        print(f"  ✗ {pkg} NOT installed")

print("\n" + "=" * 60)
print("MODULE CONNECTION TEST COMPLETE")
print("=" * 60)
print("\nIf all tests passed (✓), the system is fully connected!")
print("If any tests failed (✗), review the error messages above.")
