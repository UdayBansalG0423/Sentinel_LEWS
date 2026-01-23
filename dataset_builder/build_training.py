import pandas as pd
import numpy as np
import os

# Construct paths
script_dir = os.path.dirname(os.path.abspath(__file__))
static_file = os.path.join(script_dir, "output", "shimla_static.csv")

# Check if file exists
if not os.path.exists(static_file):
    print(f"ERROR: {static_file} not found!")
    print("Please run build_static.py first to generate terrain data.")
    exit(1)

# Load static data - check if header exists
print(f"Loading static data from: {static_file}")
static = pd.read_csv(static_file)

# Check if columns look wrong (numeric values as column names)
if static.columns[0].replace('.', '').replace('-', '').isdigit():
    # Re-read without header and assign proper column names
    static = pd.read_csv(static_file, header=None)
    static.columns = ['cell_id', 'lat', 'lon', 'slope']
    print("Fixed column names for static data")

print(f"Original static data shape: {static.shape}")

# === SMALL VALID DATASET FOR HACKATHON ===
# 2,000 cells - gives ~3.1M rows, ~150-200 MB
# Small enough to process quickly, large enough for ML
TARGET_CELLS = 2000

np.random.seed(42)  # Reproducible sampling
# Stratified sampling: oversample high-slope areas (more landslide-prone)
high_slope = static[static['slope'] > static['slope'].quantile(0.7)]
low_slope = static[static['slope'] <= static['slope'].quantile(0.7)]

# 70% high slope (landslide-prone), 30% low slope (balanced dataset)
n_high = int(TARGET_CELLS * 0.7)
n_low = TARGET_CELLS - n_high

sampled_high = high_slope.sample(n=min(n_high, len(high_slope)), random_state=42)
sampled_low = low_slope.sample(n=min(n_low, len(low_slope)), random_state=42)
static = pd.concat([sampled_high, sampled_low], ignore_index=True)

print(f"Sampled {len(static)} cells (70% high-slope, 30% low-slope)")
print(f"Slope range: {static['slope'].min():.2f}° to {static['slope'].max():.2f}°")
print(f"Static columns: {static.columns.tolist()}")

# Load rainfall labels - USE VALID LABELS
labels_file = os.path.join(script_dir, "shimla_labels_valid.csv")
if not os.path.exists(labels_file):
    # Try original labels
    labels_file = os.path.join(script_dir, "shimla_labels.csv")
    if not os.path.exists(labels_file):
        print("ERROR: No labels file found!")
        print("Please run fix_dates_valid.py first.")
        exit(1)
    print("Warning: Using original labels (may have date mismatch)")
else:
    print("Using VALID physics-based labels")

rain = pd.read_csv(labels_file)

print(f"\nRain data shape: {rain.shape}")
print(f"Rain columns: {rain.columns.tolist()}")
print(f"Label distribution:\n{rain['label'].value_counts()}")

# Calculate expected output
total_rows = len(static) * len(rain)
print(f"\n=== DATASET CREATION ===")
print(f"Cells: {len(static):,}")
print(f"Dates: {len(rain):,}")
print(f"Expected total rows: {total_rows:,}")
print(f"Estimated size: ~{(total_rows * 60) / (1024**2):.1f} MB")

# Create training data efficiently
output_file = os.path.join(script_dir, "shimla_training.csv")

print("\nCreating training dataset...")

# Collect all chunks first (since dataset is now manageable)
chunks = []

for date_idx, rain_row in rain.iterrows():
    if date_idx % 100 == 0:
        print(f"Processing date {date_idx + 1}/{len(rain)}")
    
    # Create a copy of static data for this date
    chunk = static.copy()
    
    # Add date and rain features
    chunk['date'] = rain_row['date']
    chunk['rain_1d'] = rain_row['rain_1d']
    chunk['rain_3d'] = rain_row['rain_3d']
    chunk['rain_7d'] = rain_row['rain_7d']
    chunk['rain_15d'] = rain_row['rain_15d']
    chunk['label'] = rain_row['label']  # Use labels directly from validated file
    
    chunks.append(chunk)

# Combine all chunks
print("\nCombining chunks...")
final = pd.concat(chunks, ignore_index=True)

# Select final columns
final = final[['cell_id', 'date', 'slope', 'rain_1d', 'rain_3d', 'rain_7d', 'rain_15d', 'label']]

# Save to CSV
print(f"Saving to {output_file}...")
final.to_csv(output_file, index=False)

# Print final statistics
file_size_mb = final.memory_usage(deep=True).sum() / (1024**2)
# Calculate statistics
import os
file_size_mb_disk = os.path.getsize(output_file) / (1024**2)
label_counts = final['label'].value_counts().sort_index()
landslide_pct = (label_counts.get(1, 0) / len(final)) * 100

print(f"\n{'='*60}")
print(f"✓ TRAINING DATASET CREATED SUCCESSFULLY!")
print(f"{'='*60}")
print(f"Output file: {output_file}")
print(f"Columns: {len(final.columns)}")
print(f"  → {', '.join(final.columns)}")
print(f"\nDataset Size:")
print(f"  Total rows: {len(final):,}")
print(f"  Unique cells: {final['cell_id'].nunique():,}")
print(f"  Date range: {final['date'].min()} to {final['date'].max()}")
print(f"  Disk size: {file_size_mb_disk:.1f} MB")
print(f"  Memory usage: ~{file_size_mb:.1f} MB")
print(f"\nLabel Distribution (Landslide Events):")
for label, count in label_counts.items():
    pct = (count / len(final)) * 100
    status = "No Landslide" if label == 0 else "LANDSLIDE"
    print(f"  {label} ({status:12s}): {count:10,} rows ({pct:5.2f}%)")
print(f"\nDataset Quality:")
print(f"  Class imbalance ratio: 1:{int(label_counts.get(0,0)/max(label_counts.get(1,1),1))}")
print(f"  Suitable for ML: {'✓ YES' if landslide_pct > 1 and landslide_pct < 10 else '✗ NO (adjust thresholds)'}")
print(f"\nFeature Statistics:")
print(f"  Slope range: {final['slope'].min():.1f}° to {final['slope'].max():.1f}°")
print(f"  Rain (15d) range: {final['rain_15d'].min():.4f} to {final['rain_15d'].max():.4f} mm/hr")
print(f"{'='*60}")