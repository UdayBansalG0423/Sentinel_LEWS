import rasterio
import numpy as np
import pandas as pd
from pyproj import Transformer

# ---- FILE PATHS ----
SLOPE_RASTER = "raster/slope_shimla.tif"
OUTPUT_CSV = "output/shimla_static.csv"

# ---- OPEN RASTER ----
with rasterio.open(SLOPE_RASTER) as src:
    slope = src.read(1)
    transform = src.transform
    crs = src.crs
    nodata = src.nodata

rows, cols = slope.shape

# Coordinate transformer (to lat/lon)
transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

data = []
cell_id = 0

# ---- LOOP OVER GRID ----
for row in range(rows):
    for col in range(cols):
        val = slope[row, col]

        if nodata is not None and val == nodata:
            continue
        if np.isnan(val):
            continue

        # get x,y in raster CRS
        x, y = transform * (col + 0.5, row + 0.5)

        # convert to lat/lon
        lon, lat = transformer.transform(x, y)

        data.append([cell_id, lat, lon, float(val)])
        cell_id += 1

# ---- SAVE CSV ----
df = pd.DataFrame(data, columns=["cell_id", "lat", "lon", "slope"])
df.to_csv(OUTPUT_CSV, index=False)

print("Static dataset created:", OUTPUT_CSV)
print("Total cells:", len(df))
