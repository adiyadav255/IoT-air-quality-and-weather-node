import pandas as pd
import glob
import os
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np

INDOOR_PATH="AQI_data_indoor/*.csv"
OUTDOOR_PATH="AQI_data_outdoor/*.csv"
SAVE_DIR="processed_data/"

def compute_aqi(pm25, pm10):
    def sub_index(conc, breakpoints):
        # ensure concentration is a numeric type; if not convertible, skip
        try:
            conc = float(conc)
        except (TypeError, ValueError):
            return None
        for (low, high, aqi_low, aqi_high) in breakpoints:
            if low <= conc <= high:
                return ((aqi_high - aqi_low) / (high - low)) * (conc - low) + aqi_low
        return None
    # if both inputs are missing, return NaN early
    if pd.isna(pm25) and pd.isna(pm10):
        return np.nan
    #CPCB PM2.5 breakpoints
    pm25_bp = [
        (0, 30, 0, 50),
        (31, 60, 51, 100),
        (61, 90, 101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (251, 999, 401, 500)
    ]
    #CPCB PM10 breakpoints
    pm10_bp = [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 250, 101, 200),
        (251, 350, 201, 300),
        (351, 430, 301, 400),
        (431, 999, 401, 500)
    ]
    sub_index_pm25 = sub_index(pm25, pm25_bp)
    sub_index_pm10 = sub_index(pm10, pm10_bp)

    if sub_index_pm25 is None and sub_index_pm10 is None:
        return np.nan
    return max(sub_index_pm25 or 0, sub_index_pm10 or 0)

def load_and_clean(path_pattern, label):
    files = glob.glob(path_pattern)
    if not files:
        print(f"No files found in {path_pattern}")
        return pd.DataFrame()
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        # Coerce PM columns to numeric (invalid parsing -> NaN) if present
        for pm_col in ("PM2.5", "PM10"):
            if pm_col in df.columns:
                df[pm_col] = pd.to_numeric(df[pm_col], errors='coerce')
        # Sort by System_Time (assumes System_Time is present and already clean)
        df.sort_values("System_Time", inplace=True)
        df.drop_duplicates(subset=["System_Time"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        df["AQI"] = df.apply(lambda x: compute_aqi(x["PM2.5"], x["PM10"]), axis=1)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

indoor_df=load_and_clean(INDOOR_PATH, label="indoor")
outdoor_df=load_and_clean(OUTDOOR_PATH, label="outdoor")

combined_df = pd.concat([indoor_df, outdoor_df], ignore_index=True)
combined_df.sort_values("System_Time", inplace=True)
combined_df.reset_index(drop=True, inplace=True)

combined_df.dropna(subset=["AQI"], inplace=True)

features = ["PM2.5", "PM10"]
target = "AQI"

X = combined_df[features]
y = combined_df[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

X_train_scaled = pd.DataFrame(X_train_scaled, columns=features)
X_test_scaled = pd.DataFrame(X_test_scaled, columns=features)

os.makedirs(SAVE_DIR, exist_ok=True)
combined_df.to_csv(os.path.join(SAVE_DIR, "clean_simple_AQI_dataset.csv"), index=False)
X_train_scaled.to_csv(os.path.join(SAVE_DIR, "X_train_scaled.csv"), index=False)
X_test_scaled.to_csv(os.path.join(SAVE_DIR, "X_test_scaled.csv"), index=False)
y_train.to_csv(os.path.join(SAVE_DIR, "y_train.csv"), index=False)
y_test.to_csv(os.path.join(SAVE_DIR, "y_test.csv"), index=False)

print("Dataset Prepared Successfully!")
print(f"Total Samples: {len(combined_df)}")
print(f"Train Samples: {len(X_train)}, Test Samples: {len(X_test)}")
print("Features used:", features)
print("Scaled Mean:", scaler.mean_)
print("Scale:", scaler.scale_)
print("Files saved in:", SAVE_DIR)