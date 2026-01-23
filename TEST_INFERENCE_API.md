# Testing Inference API - Quick Guide

## Overview

You can now trigger inference directly from the dashboard with custom input data!

## Method 1: Using Dashboard UI (Easiest)

1. **Start Dashboard**

   ```bash
   cd dashboard
   python app.py
   ```

2. **Open Browser**
   - Visit: http://localhost:5000

3. **Run Inference**
   - Click the **"🔮 Run Inference"** button (top right)
   - Modal will appear
   - **Option A**: Enter custom rainfall (e.g., 150 mm)
   - **Option B**: Leave empty to use current historical data
   - Click **"▶ Run Inference"**

4. **Watch Results**
   - Modal shows statistics (cells analyzed, alerts triggered, etc.)
   - Dashboard auto-refreshes after 2 seconds
   - KPIs and alert feed update with new predictions
   - "Last Data Update" timestamp changes

## Method 2: Using API Directly (Advanced)

### Endpoint 1: Trigger Prediction Cycle

**URL:** `POST /api/trigger_cycle`

**Request:**

```bash
curl -X POST http://localhost:5000/api/trigger_cycle \
  -H "Content-Type: application/json" \
  -d '{"custom_rainfall": 150.5}'
```

**Response:**

```json
{
  "success": true,
  "cycle_completed": true,
  "timestamp": "2026-01-23T10:30:45",
  "statistics": {
    "total_cells": 2000,
    "alerts_triggered": 5,
    "risk_distribution": {
      "LOW": 1850,
      "MEDIUM": 120,
      "HIGH": 25,
      "CRITICAL": 5
    },
    "avg_probability": 0.234,
    "max_probability": 0.912,
    "latest_rainfall": 150.5
  }
}
```

### Endpoint 2: Run Inference with Custom Data

**URL:** `POST /api/run_inference`

**Request:**

```bash
curl -X POST http://localhost:5000/api/run_inference \
  -H "Content-Type: application/json" \
  -d '{
    "rainfall_mm": 200.0,
    "num_days": 15
  }'
```

**Response:**

```json
{
  "success": true,
  "predictions_generated": 2000,
  "alerts_triggered": 8,
  "high_risk_cells": 6,
  "critical_cells": 2,
  "timestamp": "2026-01-23T10:35:12"
}
```

## Method 3: Python Script

```python
import requests
import json

# Trigger inference with custom rainfall
response = requests.post(
    'http://localhost:5000/api/trigger_cycle',
    headers={'Content-Type': 'application/json'},
    json={'custom_rainfall': 180.5}
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Total Cells: {result['statistics']['total_cells']}")
print(f"Alerts: {result['statistics']['alerts_triggered']}")
print(f"Avg Probability: {result['statistics']['avg_probability']:.3f}")
```

## What Happens Behind the Scenes

1. **API receives request** with optional rainfall value
2. **Creates rainfall history** (custom or historical data)
3. **Runs prediction engine** on all 2000 cells
4. **Processes with decision engine** to identify alerts
5. **Writes to dashboard database**:
   - 50 random sample predictions
   - All high/critical alerts
   - Updates system info (timestamp, network status)
6. **Returns results** with statistics
7. **Dashboard auto-refreshes** and shows new data

## Testing Different Scenarios

### Low Risk (Low Rainfall)

```bash
curl -X POST http://localhost:5000/api/trigger_cycle \
  -H "Content-Type: application/json" \
  -d '{"custom_rainfall": 30.0}'
```

**Expected:** Mostly LOW risk, few alerts

### Medium Risk

```bash
curl -X POST http://localhost:5000/api/trigger_cycle \
  -H "Content-Type: application/json" \
  -d '{"custom_rainfall": 100.0}'
```

**Expected:** Mix of LOW/MEDIUM risk, some alerts

### High Risk (Heavy Rainfall)

```bash
curl -X POST http://localhost:5000/api/trigger_cycle \
  -H "Content-Type: application/json" \
  -d '{"custom_rainfall": 200.0}'
```

**Expected:** More HIGH/CRITICAL risk, many alerts

### Extreme Risk

```bash
curl -X POST http://localhost:5000/api/trigger_cycle \
  -H "Content-Type: application/json" \
  -d '{"custom_rainfall": 300.0}'
```

**Expected:** High probability scores, numerous critical alerts

## Verification Checklist

- [ ] Dashboard button appears (top right)
- [ ] Modal opens when clicking "Run Inference"
- [ ] Can enter custom rainfall value
- [ ] Can submit with or without rainfall value
- [ ] Success message shows statistics
- [ ] Dashboard refreshes automatically
- [ ] "Last Data Update" changes
- [ ] Alert feed shows new alerts
- [ ] KPI cards update with new counts
- [ ] Network status shows "ONLINE"

## Troubleshooting

### Error: "Realtime system not available"

**Fix:** Make sure inference engine is properly initialized

```python
# Check app.py startup logs
✓ Realtime system integrated with dashboard
```

### No alerts appearing

**Normal:** Low rainfall won't trigger many alerts
**Try:** Use higher rainfall values (150-300mm)

### Dashboard not refreshing

**Fix:** Check browser console (F12) for errors
**Workaround:** Click "Refresh" button manually

## Benefits

✅ **Interactive Testing** - Test different rainfall scenarios instantly  
✅ **No Command Line Needed** - User-friendly UI interface  
✅ **Real-Time Updates** - Dashboard reflects changes immediately  
✅ **API Integration** - Can be called from external systems  
✅ **Statistics** - Get detailed results of each inference run

---

**Status:** ✅ Fully Functional  
**Date:** January 2026
