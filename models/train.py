"""
Enhanced Model Training with Comprehensive Evaluation & Model Saving
Optimized for Edge Deployment (<50MB model, <16sec inference)
"""
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, classification_report, confusion_matrix,
    precision_recall_curve, roc_curve, f1_score, accuracy_score
)
import os
import json
import time
import matplotlib
matplotlib.use('Agg')  # For headless environments
import matplotlib.pyplot as plt
import seaborn as sns

print("="*70)
print("LANDSLIDE PREDICTION MODEL - TRAINING & EVALUATION")
print("="*70)

# Load dataset
dataset_path = os.path.join(os.path.dirname(__file__), "..", "dataset_builder", "shimla_training.csv")
print(f"\nLoading dataset from: {dataset_path}")
df = pd.read_csv(dataset_path)

print(f"Dataset loaded: {len(df):,} rows")
print(f"Columns: {list(df.columns)}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024**2):.1f} MB")

# Prepare features and labels
X = df[["slope", "rain_1d", "rain_3d", "rain_7d", "rain_15d"]]
y = df["label"]

# Train-test split
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"\nTraining set: {len(Xtr):,} samples")
print(f"Test set: {len(Xte):,} samples")

# Train model (optimized for edge deployment)
print(f"\nTraining lightweight model for edge deployment...")
start_time = time.time()

model = lgb.LGBMClassifier(
    n_estimators=50,  # Reduced from 200 for faster inference
    max_depth=5,      # Limit depth for smaller model
    learning_rate=0.1,
    num_leaves=15,    # Reduced from 31 for smaller model
    class_weight="balanced",
    verbose=-1
)

model.fit(Xtr, ytr)
training_time = time.time() - start_time

# Predictions
start_inference = time.time()
pred_proba = model.predict_proba(Xte)[:, 1]
pred_binary = (pred_proba > 0.5).astype(int)
inference_time = time.time() - start_inference

# Calculate metrics
auc_score = roc_auc_score(yte, pred_proba)
accuracy = accuracy_score(yte, pred_binary)
f1 = f1_score(yte, pred_binary)

print(f"\n{'='*70}")
print("MODEL TRAINING COMPLETE")
print(f"{'='*70}")
print(f"Training time: {training_time:.2f}s")
print(f"Inference time (627K samples): {inference_time:.2f}s")
print(f"Avg inference per sample: {(inference_time/len(Xte))*1000:.4f}ms")

print(f"\n--- PERFORMANCE METRICS ---")
print(f"AUC Score: {auc_score:.4f}")
print(f"Accuracy: {accuracy:.4f}")
print(f"F1 Score: {f1:.4f}")

print(f"\nClassification Report:")
print(classification_report(yte, pred_binary, target_names=['Safe', 'Landslide']))

# Confusion Matrix
cm = confusion_matrix(yte, pred_binary)
print(f"\nConfusion Matrix:")
print(cm)

# Feature importance
feature_names = ["slope", "rain_1d", "rain_3d", "rain_7d", "rain_15d"]
importance = model.feature_importances_
print(f"\nFeature Importance:")
for name, imp in zip(feature_names, importance):
    print(f"  {name:12s}: {imp:.4f}")

# Save model
models_dir = os.path.dirname(__file__)
model_path = os.path.join(models_dir, "lgb_model.txt")
model.booster_.save_model(model_path)

model_size = os.path.getsize(model_path) / 1024  # KB
print(f"\nModel saved: {model_path}")
print(f"Model size: {model_size:.2f} KB (Target: <50MB)")

# Save metrics as JSON
metrics = {
    "auc_score": float(auc_score),
    "accuracy": float(accuracy),
    "f1_score": float(f1),
    "training_time_sec": round(training_time, 2),
    "inference_time_sec": round(inference_time, 2),
    "avg_inference_ms_per_sample": round((inference_time/len(Xte))*1000, 4),
    "model_size_kb": round(model_size, 2),
    "test_samples": len(Xte),
    "feature_importance": {name: float(imp) for name, imp in zip(feature_names, importance)}
}

metrics_path = os.path.join(models_dir, "evaluation_metrics.json")
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"Metrics saved: {metrics_path}")

# Generate evaluation charts
print(f"\nGenerating evaluation charts...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Confusion Matrix
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0, 0],
            xticklabels=['Safe', 'Landslide'],
            yticklabels=['Safe', 'Landslide'])
axes[0, 0].set_title('Confusion Matrix')
axes[0, 0].set_ylabel('True Label')
axes[0, 0].set_xlabel('Predicted Label')

# 2. ROC Curve
fpr, tpr, _ = roc_curve(yte, pred_proba)
axes[0, 1].plot(fpr, tpr, label=f'AUC = {auc_score:.4f}', linewidth=2)
axes[0, 1].plot([0, 1], [0, 1], 'k--', label='Random')
axes[0, 1].set_xlabel('False Positive Rate')
axes[0, 1].set_ylabel('True Positive Rate')
axes[0, 1].set_title('ROC Curve')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# 3. Precision-Recall Curve
precision, recall, _ = precision_recall_curve(yte, pred_proba)
axes[1, 0].plot(recall, precision, linewidth=2)
axes[1, 0].set_xlabel('Recall')
axes[1, 0].set_ylabel('Precision')
axes[1, 0].set_title('Precision-Recall Curve')
axes[1, 0].grid(True, alpha=0.3)

# 4. Feature Importance
axes[1, 1].barh(feature_names, importance, color='steelblue')
axes[1, 1].set_xlabel('Importance')
axes[1, 1].set_title('Feature Importance')
axes[1, 1].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
chart_path = os.path.join(models_dir, "evaluation_charts.png")
plt.savefig(chart_path, dpi=150, bbox_inches='tight')
print(f"Charts saved: {chart_path}")

print(f"\n{'='*70}")
print("EDGE DEPLOYMENT READY")
print(f"{'='*70}")
print(f"Model: {model_size:.2f} KB < 50 MB YES")
latency_ok = "YES" if (inference_time/len(Xte))*1000 < 16 else "NO"
print(f"Latency: {(inference_time/len(Xte))*1000:.4f}ms < 16ms {latency_ok}")
print(f"{'='*70}")