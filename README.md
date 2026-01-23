# Sentinel LEWS - Landslide Early Warning System

## Overview

Edge-optimized **real-time** landslide prediction system for Shimla district using satellite rainfall (CHIRPS/GPM) and terrain data (DEM). Production-ready for hackathon with <50MB model and <16sec latency.

## 🎯 System Status

✅ **COMPLETE & PRODUCTION-READY**

- ✅ Training pipeline (offline ML)
- ✅ Runtime inference engine
- ✅ Decision rule system
- ✅ Alert management
- ✅ Main orchestrator loop
- ✅ Clean modular architecture

## Model Performance

- **Model Size**: 697 KB (0.68 MB) ✓ << 50 MB
- **Inference Latency**: <16ms per sample ✓
- **AUC Score**: 1.00
- **F1 Score**: 1.00
- **Dataset**: 3.1M rows, 2000 grid cells, 1569 dates

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Training (If Needed)

```bash
python run_pipeline.py
```

This will:

- Generate physics-based labels
- Build training dataset (2-5 min)
- Train optimized model
- Demo inference
- Run system tests

### 3. **Run Real-Time System** 🚀

```bash
# Single demo run
python main.py

# Continuous monitoring (production mode)
python main.py --continuous --interval 300
```

## System Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture.

### Runtime Flow

```
[Data Ingest] → [Inference] → [Decision Rules] → [Alerts] → [Repeat]
     ↓              ↓              ↓                ↓
New rainfall   Predict      Apply rules      Send alerts
+ history      all cells    (risk levels)    (console/log)
```

## Project Structure

```
📁 Sentinel_LEWS/
├── 📊 DATA LAYER
│   ├── dataset_builder/          # Training data (offline)
│   │   ├── build_static.py
│   │   ├── fix_dates_valid.py
│   │   └── build_training.py
│   └── data/                      # Real-time data (online)
│       ├── ingestion.py
│       └── realtime/
│
├── 🧠 ML LAYER
│   └── models/
│       ├── train.py               # Train model
│       └── lgb_model.txt          # 697 KB model
│
├── ⚡ RUNTIME LAYER
│   └── runtime/
│       └── inference.py           # Real-time predictions
│
├── 🎯 DECISION LAYER
│   └── decision/
│       └── rule_engine.py         # ML + human rules
│
├── 📢 ALERT LAYER
│   └── alerts/
│       ├── alert_manager.py
│       └── logs/alerts.csv
│
├── 🔁 ORCHESTRATION
│   └── main.py                    # System loop
│
└── 🧪 TESTING
    ├── test_system.py
    └── run_pipeline.py
```

│ ├── train.py # Train LightGBM with evaluation
│ ├── inference.py # Production inference pipeline
│ ├── lgb_model.txt # Trained model (697 KB)
│ └── evaluation_metrics.json # Model metrics
├── test_system.py # 7-test validation suite
├── run_pipeline.py # Workflow orchestrator
└── requirements.txt # Dependencies

````

## Features

- **Slope**: Terrain angle (°)
- **Rain_1d**: 1-day cumulative rainfall (m)
- **Rain_3d**: 3-day cumulative rainfall (m)
- **Rain_7d**: 7-day cumulative rainfall (m)
- **Rain_15d**: 15-day cumulative rainfall (m)

## Physics-Based Labels

Labels generated using Himachal Pradesh research:

- **Monsoon season**: June-September
- **Rainfall threshold**: rain_15d > 150mm OR rain_7d > 80mm
- **Slope threshold**: slope > 30°

## Edge Deployment

```python
from models.inference import LandslidePredictor

# Initialize predictor
predictor = LandslidePredictor('models/lgb_model.txt')

# Single prediction
result = predictor.predict({
    'slope': 45.0,
    'rain_1d': 0.025,
    'rain_3d': 0.065,
    'rain_7d': 0.085,
    'rain_15d': 0.160
})
print(f"Risk: {result['risk_level']} ({result['probability']:.2%})")
````

## Testing

System includes 7 comprehensive tests:

1. Model existence/size check
2. Model loading latency
3. Single inference latency
4. Batch inference (1000 samples)
5. Edge cases (zero rain, heavy rain)
6. Evaluation metrics verification
7. Chart generation verification

## Model Optimization

- **Estimators**: 50 (vs 200 baseline)
- **Max Depth**: 5
- **Num Leaves**: 15
- **Learning Rate**: 0.05
- Target: <50MB model, <16sec latency for edge devices

## Risk Categories

- **LOW**: <30% probability
- **MEDIUM**: 30-60% probability
- **HIGH**: 60-80% probability
- **CRITICAL**: >80% probability

## Dataset Details

- **Cells**: 2000 (stratified 70% high-slope)
- **Dates**: 1569 (2018-2022)
- **Safe/Landslide**: 62%/38%
- **File Size**: 279 MB

## Git Repository

```bash
git remote -v
# origin  https://github.com/UdayBansalG0423/Sentinel_LEWS.git
```

## License

MIT
