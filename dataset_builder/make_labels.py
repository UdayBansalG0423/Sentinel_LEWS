import pandas as pd

rain = pd.read_csv("shimla_rain_features.csv")
rain["date"] = pd.to_datetime(rain["date"])

ls = pd.read_csv("shimla_landslides.csv")
ls["date"] = pd.to_datetime(ls["date"])

rain["label"] = rain["date"].isin(ls["date"]).astype(int)
rain.to_csv("shimla_labels.csv", index=False)

print("Labels added")