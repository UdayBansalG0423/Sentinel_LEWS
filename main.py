import time
from ingestion.rainfall_loader import load_rainfall
from ingestion.sensor_loader import load_sensors
from fusion.rainfall_downscale import downscale_rainfall
from fusion.sensor_filter import filter_sensors
from fusion.terrain_fusion import fuse
from features.feature_builder import build_features
from model.predictor import predict
from decision.rule_engine import decide
from alerts.sms_sender import send_sms
from database.db_manager import save_prediction
from datetime import datetime

CYCLE_TIME = 300

while True:
    print("Cycle started")

    rain = load_rainfall("dummy_path")
    sensors = load_sensors("dummy_path")

    rain_ds = downscale_rainfall(rain)
    sensors_f = filter_sensors(sensors)

    fused = fuse(rain_ds, sensors_f)

    X = build_features(fused)

    probs = predict(X)

    for i,p in enumerate(probs):
        save_prediction(i,p,str(datetime.now()))

        if decide(p):
            send_sms(f"Landslide risk high in cell {i}")

    print("Cycle complete")
    time.sleep(CYCLE_TIME)
