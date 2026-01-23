# Sentinel-LEWS System Architecture

## 🏗️ Clean Modular Structure

```
Sentinel_LEWS/
│
├── 📊 DATA LAYER
│   ├── dataset_builder/          # Training data preparation (OFFLINE)
│   │   ├── build_static.py       # Extract terrain from DEM raster
│   │   ├── fix_dates_valid.py    # Generate physics-based labels
│   │   ├── build_training.py     # Merge terrain + rainfall → training dataset
│   │   └── output/
│   │       └── shimla_static.csv # 100m×100m grid cells with slope
│   │
│   └── data/                      # Real-time data (ONLINE)
│       ├── ingestion.py           # Ingest new rainfall data
│       └── realtime/              # New rainfall files (CSV)
│
├── 🧠 ML LAYER
│   └── models/
│       ├── train.py               # Train LightGBM model (OFFLINE)
│       ├── inference.py           # Edge deployment predictor (moved to runtime/)
│       └── lgb_model.txt          # Trained model (697 KB)
│
├── ⚡ RUNTIME LAYER (NEW - CRITICAL)
│   └── runtime/
│       └── inference.py           # Real-time prediction engine
│           ├── LandslidePredictionEngine
│           ├── compute_rolling_rainfall()
│           ├── predict_grid_cell()
│           └── predict_all_cells()
│
├── 🎯 DECISION LAYER
│   └── decision/
│       └── rule_engine.py         # Human-logic safety rules
│           ├── LandslideDecisionEngine
│           ├── apply_rules()      # ML + terrain + rainfall → action
│           └── get_alert_cells()
│
├── 📢 ALERT LAYER
│   └── alerts/
│       ├── alert_manager.py       # Alert generation & delivery
│       │   ├── send_alert()
│       │   ├── send_batch_alerts()
│       │   └── _log_alert()       # CSV logging
│       └── logs/
│           └── alerts.csv         # Alert history
│
├── 🔁 ORCHESTRATION LAYER (BRAIN)
│   └── main.py                    # System loop orchestrator
│       └── SentinelLEWS
│           ├── run_cycle()        # Single prediction cycle
│           ├── run_continuous()   # Continuous monitoring
│           └── run_demo()         # Hackathon demo
│
├── 🧪 TESTING & DEPLOYMENT
│   ├── test_system.py             # System validation tests
│   ├── run_pipeline.py            # Training pipeline orchestrator
│   └── requirements.txt           # Dependencies
│
└── 📚 DOCUMENTATION
    ├── README.md                  # User guide
    ├── ARCHITECTURE.md            # This file
    └── FIXES_APPLIED.md           # Bug fix log
```

## 🔄 System Flow

### Training Phase (OFFLINE)

```
1. build_static.py      → Extract slope from DEM
2. fix_dates_valid.py   → Generate physics-based labels
3. build_training.py    → Create 3.1M row dataset
4. train.py             → Train LightGBM model (697 KB)
```

### Runtime Phase (ONLINE)

```
┌─────────────────────────────────────────────────────────────┐
│                     MAIN.PY ORCHESTRATOR                    │
└─────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    [1] INGEST         [2] INFERENCE    [3] DECISION
    data/ingestion.py  runtime/         decision/
                      inference.py      rule_engine.py
    • Load rainfall    • Load model     • Apply rules
    • Merge history    • Compute        • Categorize risk
    • Add new data       features       • Determine action
                       • Predict all
                         cells
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                      [4] ALERTS
                      alerts/
                      alert_manager.py
                      • Filter high-risk
                      • Send console alerts
                      • Log to CSV
                      • (Future: SMS/Dashboard)
                             │
                             ▼
                      [5] REPEAT
                      (Every 5 min)
```

## 🎯 Component Responsibilities

### 1. **Data Ingestion** (`data/ingestion.py`)

- **Purpose**: Load new rainfall data
- **Input**: CSV files from `data/realtime/`
- **Output**: Updated rainfall history DataFrame
- **Frequency**: Every cycle (5 min)

### 2. **Runtime Inference** (`runtime/inference.py`)

- **Purpose**: Real-time landslide prediction
- **Input**: Grid cells + rainfall history + date
- **Output**: Probability + risk level per cell
- **Model**: LightGBM (697 KB)

### 3. **Decision Engine** (`decision/rule_engine.py`)

- **Purpose**: Convert ML predictions → actions
- **Rules**:
  - Probability > 0.8 + Slope > 45° → **CRITICAL**
  - Probability > 0.6 → **HIGH** → Send alert
  - Probability > 0.3 → **MEDIUM** → Monitor
  - Else → **LOW** → Normal
- **Output**: Actionable decisions

### 4. **Alert Manager** (`alerts/alert_manager.py`)

- **Purpose**: Send alerts & log history
- **Outputs**:
  - Console: ✅ (Always)
  - CSV Log: ✅ (`alerts/logs/alerts.csv`)
  - SMS: 🔜 (Future: Twilio/GSM)
  - Dashboard: 🔜 (Future: Flask/Leaflet)

### 5. **Main Orchestrator** (`main.py`)

- **Purpose**: System loop controller
- **Modes**:
  - `python main.py` → Single demo run
  - `python main.py --continuous` → Infinite loop
  - `python main.py --interval 60` → 1-minute cycles
- **Cycle Steps**: Ingest → Predict → Decide → Alert

## 📦 Removed/Unused Files

**Deleted**:

- ❌ `fix.py` → Duplicate preprocessing logic
- ❌ `rain.csv` → Test file
- ❌ `fusion/`, `ingestion/`, `features/` → Obsolete modules (pre-refactor)
- ❌ `dataset_builder/show_summary.py` → One-time analysis script

**Why**:

- Reduces confusion
- Cleaner architecture
- Easier navigation

## 🚀 Usage

### Quick Start

```bash
# Training (if needed)
python run_pipeline.py

# Runtime - Single Demo
python main.py

# Runtime - Continuous (Production)
python main.py --continuous --interval 300
```

### Module Testing

```bash
# Test inference
python runtime/inference.py

# Test data ingestion
python data/ingestion.py

# Test alerts
python alerts/alert_manager.py
```

## 🔧 Configuration

**Model**: `models/lgb_model.txt` (697 KB)

- Estimators: 50
- Max depth: 5
- Features: slope, rain_1d, rain_3d, rain_7d, rain_15d

**Decision Thresholds**:

- Critical: 0.8 probability
- High: 0.6 probability
- Medium: 0.3 probability

**Cycle Interval**: 300 seconds (5 minutes)

## 📊 Data Flow

```
Historical Rainfall (1569 days)
         ↓
   New Data Ingest (simulated)
         ↓
   Updated History
         ↓
   Rolling Features (1d, 3d, 7d, 15d)
         ↓
   Static Grid (2000 cells) + Features
         ↓
   LightGBM Model
         ↓
   Probability per cell
         ↓
   Decision Rules (slope + rainfall)
         ↓
   Risk Level + Action
         ↓
   Alerts (console + log)
```

## 🎯 Hackathon Readiness

### ✅ Complete Components

- [x] Data pipeline (offline training)
- [x] ML model (LightGBM 697 KB)
- [x] Runtime inference engine
- [x] Decision rule engine
- [x] Alert system (console + CSV)
- [x] Main orchestrator (demo + continuous)
- [x] Clean modular architecture

### 🔜 Future Enhancements

- [ ] SMS alerts (Twilio/GSM)
- [ ] Web dashboard (Flask + Leaflet)
- [ ] Database (PostgreSQL/SQLite)
- [ ] API endpoints (REST)
- [ ] Docker containerization

## 🏆 Key Metrics

- **Model Size**: 697 KB ✅ (<50 MB target)
- **Inference Latency**: <16 ms per sample ✅
- **Grid Resolution**: 100m × 100m cells
- **Prediction Frequency**: Every 5 minutes (configurable)
- **Alert Latency**: <1 second from prediction to console

---

**Status**: ✅ Production-ready for hackathon demo
