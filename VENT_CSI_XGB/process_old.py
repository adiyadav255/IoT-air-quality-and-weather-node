import os
import pandas as pd
import numpy as np
import ast

# ========= CONFIG =========
CSI_FOLDER = "csi_data"
AQMS_FOLDER = "aqms_cleaned"
AQMS_BUFFER_SEC = 10

# ========= LOAD AQMS =========
def load_aqms(folder):
    dfs = []

    for f in os.listdir(folder):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(folder, f))

            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df["co2"] = pd.to_numeric(df["co2"], errors="coerce")
            df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")

            df = df.dropna().sort_values("timestamp")
            dfs.append(df)

    aqms = pd.concat(dfs, ignore_index=True)
    aqms = aqms.sort_values("timestamp").reset_index(drop=True)

    print("AQMS loaded:", len(aqms), "rows")
    return aqms


# ========= CSI PARSER =========
def parse_csi(data_str):
    try:
        if isinstance(data_str, str) and "[" in data_str:
            raw = ast.literal_eval(data_str)
        else:
            raw = list(map(int, str(data_str).split()))

        I = np.array(raw[::2])
        Q = np.array(raw[1::2])
        return I + 1j * Q
    except:
        return None


# ========= CSI FEATURES =========
def extract_csi_features(df):
    amps = []

    for d in df["data"]:
        csi = parse_csi(d)
        if csi is not None:
            amps.append(np.abs(csi))

    if len(amps) < 5:
        return None

    W = np.array(amps)

    # --- Optional normalization (reduces environment bias) ---
    W = (W - np.mean(W)) / (np.std(W) + 1e-6)

    mean = W.mean()
    std = W.std()
    var = W.var()

    diff = np.diff(W, axis=0)
    motion_energy = np.mean(diff**2)

    rssi_mean = df["rssi"].mean()
    rssi_std = df["rssi"].std()

    temporal_stability = np.std(W.mean(axis=1))
    subcarrier_variation = np.std(W.mean(axis=0))

    motion_ratio = motion_energy / (std + 1e-6)

    return np.array([
        mean, std, var, motion_energy,
        rssi_mean, rssi_std,
        temporal_stability,
        subcarrier_variation,
        motion_ratio
    ])


# ========= AQMS FEATURES =========
def extract_aqms_features(aqms, t_start, t_end):
    buffer = pd.Timedelta(seconds=AQMS_BUFFER_SEC)

    window = aqms[
        (aqms["timestamp"] >= t_start - buffer) &
        (aqms["timestamp"] <= t_end + buffer)
    ]

    if len(window) < 1:
        return None

    co2 = window["co2"].values
    pm = window["pm25"].values

    co2_delta = co2[-1] - co2[0] if len(co2) > 1 else 0
    co2_rate  = co2_delta / max(len(co2), 1)

    pm_mean  = np.mean(pm)
    pm_spike = np.max(pm) - np.min(pm)

    return np.array([
        co2_delta,
        co2_rate,
        pm_mean,
        pm_spike
    ])


# ========= BUILD DATASET =========
def build_dataset(csi_folder, aqms):

    X = []
    y = []
    file_ids = []
    group_ids = []   # (session-level grouping)

    for label_folder, label in [("someone", 1), ("none", 0)]:
        base_path = os.path.join(csi_folder, label_folder)

        for subfolder in os.listdir(base_path):
            sub_path = os.path.join(base_path, subfolder)

            if not os.path.isdir(sub_path):
                continue

            for file in os.listdir(sub_path):
                if not file.endswith(".csv"):
                    continue

                path = os.path.join(sub_path, file)

                try:
                    df = pd.read_csv(path)
                except:
                    continue

                if "timestamp" not in df.columns or "data" not in df.columns:
                    continue

                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df = df.dropna(subset=["timestamp"])

                if len(df) < 10:
                    continue

                t_start = df["timestamp"].iloc[0]
                t_end   = df["timestamp"].iloc[-1]

                csi_feat = extract_csi_features(df)
                aqms_feat = extract_aqms_features(aqms, t_start, t_end)

                if csi_feat is None or aqms_feat is None:
                    continue

                feat = np.concatenate([csi_feat, aqms_feat])

                X.append(feat)
                y.append(label)
                file_ids.append(path)

                #  group by session folder
                group_ids.append(sub_path)

    return (
        np.array(X),
        np.array(y),
        np.array(file_ids),
        np.array(group_ids)
    )


# ========= MAIN =========
if __name__ == "__main__":

    print("Loading AQMS...")
    aqms = load_aqms(AQMS_FOLDER)

    print("Building dataset...")
    X, y, file_ids, group_ids = build_dataset(CSI_FOLDER, aqms)

    print("\nSaving dataset...")
    np.save("X.npy", X)
    np.save("y.npy", y)
    np.save("file_ids.npy", file_ids)
    np.save("group_ids.npy", group_ids)   

    print("\nDone.")
    print("Total samples:", len(X))
    print("Unique sessions:", len(np.unique(group_ids)))

    if len(X) > 0:
        print("Feature shape:", X.shape)