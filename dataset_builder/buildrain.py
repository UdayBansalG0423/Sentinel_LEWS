import pandas as pd

df = pd.read_csv("shimla_rain_daily.csv")
df["date"] = pd.to_datetime(df["date"])

df["rain_1d"]  = df["rain"]
df["rain_3d"]  = df["rain"].rolling(3).sum()
df["rain_7d"]  = df["rain"].rolling(7).sum()
df["rain_15d"] = df["rain"].rolling(15).sum()

df = df.dropna().reset_index(drop=True)
df.to_csv("shimla_rain_features.csv", index=False)

print("Rainfall rolling features ready")