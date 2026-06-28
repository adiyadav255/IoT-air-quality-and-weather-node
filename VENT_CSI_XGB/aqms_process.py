import os
import pandas as pd

# === CONFIG ===
INPUT_FOLDER = "aqms_raw"
OUTPUT_FOLDER = "aqms_cleaned"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clean_aqms_file(file_path):
    try:
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="latin1")
        
        # --- Step 1: Drop duplicate header row
        df = df.iloc[1:].copy()

        # --- Step 2: Rename columns properly
        df.columns = [
            "timestamp", "uptime", "temp", "humidity",
            "pm25", "pm10", "co2", "co"
        ]

        # --- Step 3: Convert timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')

        # --- Step 4: Convert required columns to numeric
        df["pm25"] = pd.to_numeric(df["pm25"], errors='coerce')
        df["co2"] = pd.to_numeric(df["co2"], errors='coerce')

        # --- Step 5: Keep only required columns
        df = df[["timestamp", "co2", "pm25"]]

        # --- Step 6: Drop invalid rows
        df = df.dropna()

        # --- Step 7: Sort by time (important!)
        df = df.sort_values("timestamp")

        # --- Step 8: Reset index
        df = df.reset_index(drop=True)

        return df

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


# === PROCESS ALL FILES ===
for filename in os.listdir(INPUT_FOLDER):
    if filename.endswith(".csv"):
        input_path = os.path.join(INPUT_FOLDER, filename)

        cleaned_df = clean_aqms_file(input_path)

        if cleaned_df is not None and not cleaned_df.empty:
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            cleaned_df.to_csv(output_path, index=False)
        else:
            print(f"Skipped: {filename}")

print("AQMS cleaning completed.")