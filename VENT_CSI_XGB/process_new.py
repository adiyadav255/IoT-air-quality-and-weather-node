import os
import numpy as np
import pandas as pd
import ast

CSI_FOLDER = "new_data"
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
    return aqms.sort_values("timestamp").reset_index(drop=True)


# ========= CSI PARSER =========
def parse_csi(data_str):
    try:
        if "[" in str(data_str):
            raw = ast.literal_eval(data_str)
        else:
            raw = list(map(int, str(data_str).split()))

        I = np.array(raw[::2])
        Q = np.array(raw[1::2])
        return I + 1j * Q
    except:
        return None


# ========= CSI FEATURES =========
def extract_csi(df):
    amps = []

    for d in df["data"]:
        csi = parse_csi(d)
        if csi is not None:
            amps.append(np.abs(csi))

    if len(amps) < 5:
        return None

    W = np.array(amps)
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
def extract_aqms(aqms, t_start, t_end):
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
def build_dataset(root, aqms):

    X, y = [], []

    for session in os.listdir(root):
        session_path = os.path.join(root, session)
        if not os.path.isdir(session_path):
            continue

        for subfolder in os.listdir(session_path):
            sub_path = os.path.join(session_path, subfolder)
            if not os.path.isdir(sub_path):
                continue

            if "empty" in subfolder.lower():
                label = 0
            elif "occupied" in subfolder.lower():
                label = 1
            else:
                continue

            for file in os.listdir(sub_path):
                if not file.endswith(".csv"):
                    continue

                path = os.path.join(sub_path, file)

                try:
                    df = pd.read_csv(path)
                except:
                    continue

                if "timestamp" not in df.columns:
                    continue

                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df = df.dropna(subset=["timestamp"])

                if len(df) < 10:
                    continue

                t_start = df["timestamp"].iloc[0]
                t_end   = df["timestamp"].iloc[-1]

                csi_feat = extract_csi(df)
                aqms_feat = extract_aqms(aqms, t_start, t_end)

                if csi_feat is None or aqms_feat is None:
                    continue

                feat = np.concatenate([csi_feat, aqms_feat])

                X.append(feat)
                y.append(label)

    return np.array(X), np.array(y)


# ========= RUN =========
if __name__ == "__main__":

    aqms = load_aqms(AQMS_FOLDER)

    X, y = build_dataset(CSI_FOLDER, aqms)

    np.save("X_new.npy", X)
    np.save("y_new.npy", y)

    print("Done")
    print("Shape:", X.shape)