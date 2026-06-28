import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
FAN_POWER = 75        # Watts
PURIFIER_POWER = 40   # Watts
DT = 1                # seconds per sample
THRESHOLD = 0.65

# -----------------------------
# SYSTEM SIMULATION (Fan)
# -----------------------------
def simulate_system(y_true, y_pred):
    co2, pm = 400, 10
    co2_list, pm_list = [], []

    for occ, fan in zip(y_true, y_pred):

        # CO2 dynamics
        co2 += 2.0 if occ else 0.2
        if fan:
            co2 -= 1.5

        # PM dynamics
        if occ:
            pm += 0.5
        if fan:
            pm -= 0.4

        co2 = max(350, co2)
        pm = max(5, pm)

        co2_list.append(co2)
        pm_list.append(pm)

    return np.array(co2_list), np.array(pm_list)

# -----------------------------
# PURIFIER SIMULATION
# -----------------------------
def simulate_purifier(y_true):
    co2, pm = 400, 10
    co2_list, pm_list = [], []

    for occ in y_true:
        if occ:
            co2 += 2.0
            pm += 0.5

        pm -= 1.2  # purifier effect

        co2 = max(350, co2)
        pm = max(2, pm)

        co2_list.append(co2)
        pm_list.append(pm)

    return np.array(co2_list), np.array(pm_list)

# -----------------------------
# ENERGY
# -----------------------------
def compute_energy(y_pred, power):
    return (np.sum(y_pred) * DT / 3600) * power

# -----------------------------
# AQI PROXY
# -----------------------------
def compute_aqi_series(co2, pm):
    co2_score = (co2 - 400) / 600
    pm_score = pm / 50
    return 0.6 * co2_score + 0.4 * pm_score

# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_simulation(model, X_test, y_test):

    # Predictions
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= THRESHOLD).astype(int)

    # Systems
    co2_i, pm_i = simulate_system(y_test, y_test)
    co2_m, pm_m = simulate_system(y_test, y_pred)

    y_on = np.ones_like(y_test)
    co2_on, pm_on = simulate_system(y_test, y_on)

    co2_p, pm_p = simulate_purifier(y_test)

    # Energy
    e_i = compute_energy(y_test, FAN_POWER)
    e_m = compute_energy(y_pred, FAN_POWER)
    e_on = compute_energy(y_on, FAN_POWER)
    e_p = (len(y_test) * DT / 3600) * PURIFIER_POWER

    # AQI
    aqi_i = np.mean(compute_aqi_series(co2_i, pm_i))
    aqi_m = np.mean(compute_aqi_series(co2_m, pm_m))
    aqi_on = np.mean(compute_aqi_series(co2_on, pm_on))
    aqi_p = np.mean(compute_aqi_series(co2_p, pm_p))

    # Extra metrics
    wasted_time = np.sum((y_pred == 1) & (y_test == 0)) * DT
    missed_time = np.sum((y_pred == 0) & (y_test == 1)) * DT

    wasted_energy = (wasted_time / 3600) * FAN_POWER

    # Table
    df = pd.DataFrame([
        ["Ideal", e_i, np.mean(co2_i), np.mean(pm_i), aqi_i],
        ["AI System (0.65)", e_m, np.mean(co2_m), np.mean(pm_m), aqi_m],
        ["Always ON Fan", e_on, np.mean(co2_on), np.mean(pm_on), aqi_on],
        ["Purifier", e_p, np.mean(co2_p), np.mean(pm_p), aqi_p],
    ], columns=["System", "Energy (Wh)", "CO2", "PM", "AQI"])

    print(df)

    print("\n--- Additional Metrics ---")
    print(f"Wasted Energy (FP): {wasted_energy:.2f} Wh")
    print(f"Missed Occupancy Time (FN): {missed_time:.2f} sec")

    return co2_i, co2_m, co2_on, co2_p, pm_i, pm_m, pm_on, pm_p

# -----------------------------
# GRAPH SECTION
# -----------------------------
def plot_results(co2_i, co2_m, co2_on, co2_p,
                 pm_i, pm_m, pm_on, pm_p):

    # CO2 plot
    plt.figure()
    plt.plot(co2_i, label="Ideal")
    plt.plot(co2_m, label="AI System")
    plt.plot(co2_on, label="Always ON Fan")
    plt.plot(co2_p, label="Purifier")
    plt.title("CO2 Levels Over Time")
    plt.xlabel("Time")
    plt.ylabel("CO2 (ppm)")
    plt.legend()
    plt.grid()
    plt.show()

    # PM plot
    plt.figure()
    plt.plot(pm_i, label="Ideal")
    plt.plot(pm_m, label="AI System")
    plt.plot(pm_on, label="Always ON Fan")
    plt.plot(pm_p, label="Purifier")
    plt.title("PM Levels Over Time")
    plt.xlabel("Time")
    plt.ylabel("PM (ug/m3)")
    plt.legend()
    plt.grid()
    plt.show()

    # Energy Bar
    def plot_energy_bar(df):
        plt.figure()
        plt.bar(df["System"], df["Energy (Wh)"])
        plt.title("Energy Consumption Comparison")
        plt.xlabel("System")
        plt.ylabel("Energy (Wh)")
        plt.xticks(rotation=20)
        plt.grid(axis='y')
        plt.show()
# Run the simulation and get the results
co2_i, co2_m, co2_on, co2_p, pm_i, pm_m, pm_on, pm_p, df_results = run_simulation(model, X_test, y_test)

# Plot the results
plot_results(co2_i, co2_m, co2_on, co2_p, pm_i, pm_m, pm_on, pm_p)
plot_energy_bar(df_results)