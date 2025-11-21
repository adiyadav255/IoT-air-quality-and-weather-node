import socket
import csv
from datetime import datetime
import threading
import tkinter as tk
from tkinter import ttk
from collections import deque
from datetime import datetime
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def compute_aqi_with_category(pm25, pm10):
    def sub_index(conc, breakpoints):
        for low, high, aqi_low, aqi_high in breakpoints:
            if low <= conc <= high:
                return ((aqi_high - aqi_low) / (high - low)) * (conc - low) + aqi_low
        return None

    #CPCB PM2.5 breakpoints
    pm25_bp = [
        (0, 30, 0, 50),
        (31, 60, 51, 100),
        (61, 90, 101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (251, 999, 401, 500)
    ]

    # CPCB PM10 breakpoints
    pm10_bp = [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 250, 101, 200),
        (251, 350, 201, 300),
        (351, 430, 301, 400),
        (431, 999, 401, 500)
    ]
    s25 = sub_index(pm25, pm25_bp)
    s10 = sub_index(pm10, pm10_bp)

    if s25 is None and s10 is None:
        return None, "Unknown", "#808080"

    aqi = max(s25 or 0, s10 or 0)

    categories = [
        (0, 50, "Good", "#00e400"),
        (51, 100, "Satisfactory", "#9cff9c"),
        (101, 200, "Moderate", "#ffff00"),
        (201, 300, "Poor", "#ff7e00"),
        (301, 400, "Very Poor", "#ff0000"),
        (401, 500, "Severe", "#7e0023")
    ]

    for low, high, name, color in categories:
        if low <= aqi <= high:
            return round(aqi, 2), name, color

    return round(aqi, 2), "Out of Range", "#000000"
# AQI Dashboard Application
class AQIDashboard:
    def __init__(self, udp_port=8000, history_len=50):
        self.UDP_PORT = udp_port
        self.history_len = history_len

        # history of AQI (deque for fast pops)
        self.aqi_history = deque(maxlen=self.history_len)
        self.time_history = deque(maxlen=self.history_len)

        # UDP thread control
        self.udp_thread = None
        self.udp_thread_stop = threading.Event()

        # Build UI
        self.root = tk.Tk()
        self.root.title("AQI Dashboard — Real-time (UDP)")

        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill='x', padx=8, pady=6)

        # AQI big display
        aqi_frame = ttk.Frame(top_frame)
        aqi_frame.pack(side='left', padx=6)

        ttk.Label(aqi_frame, text="Real-time AQI", font=("Arial", 12)).pack(anchor='w')
        self.aqi_label = tk.Label(aqi_frame, text="--", font=("Arial", 28), width=8, relief='ridge')
        self.aqi_label.pack(pady=4)

        self.cat_label = ttk.Label(aqi_frame, text="Category: --", font=("Arial", 11))
        self.cat_label.pack(anchor='w')

        # Prediction box
        pred_frame = ttk.Frame(top_frame)
        pred_frame.pack(side='left', padx=12)

        ttk.Label(pred_frame, text="Predicted AQI (from ESP32)", font=("Arial", 11)).pack(anchor='w')
        self.pred_label = tk.Label(pred_frame, text="--", font=("Arial", 20), width=8, relief='ridge')
        self.pred_label.pack(pady=6)

        # Sensors summary
        sensors_frame = ttk.Frame(self.root)
        sensors_frame.pack(fill='x', padx=8, pady=4)

        self.sensors_text = tk.StringVar(value="Sensors: --")
        ttk.Label(sensors_frame, textvariable=self.sensors_text, font=("Arial", 10)).pack(anchor='w')

        # Matplotlib history plot
        fig = Figure(figsize=(6,3), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_title("AQI History (last {} samples)".format(self.history_len))
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("AQI")
        self.line, = self.ax.plot([], [], marker='o', linestyle='-')

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().pack(fill='both', padx=8, pady=6)
        self.canvas = canvas

        # Controls
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill='x', padx=8, pady=6)

        self.start_btn = ttk.Button(ctrl_frame, text="Start (UDP)", command=self.start_udp)
        self.start_btn.pack(side='left', padx=6)
        self.stop_btn = ttk.Button(ctrl_frame, text="Stop (UDP)", command=self.stop_udp, state='disabled')
        self.stop_btn.pack(side='left', padx=6)
        ttk.Label(ctrl_frame, text=f"UDP port: {self.UDP_PORT}").pack(side='right')

        # Clean shutdown
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    def start_udp(self):
        if self.udp_thread and self.udp_thread.is_alive():
            return
        self.udp_thread_stop.clear()
        self.udp_thread = threading.Thread(target=self._udp_listener, daemon=True)
        self.udp_thread.start()
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

    def stop_udp(self):
        self.udp_thread_stop.set()
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
    def _udp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("0.0.0.0", self.UDP_PORT))
        except Exception as e:
            self._log_to_ui(f"Socket bind error: {e}")
            return

        sock.settimeout(1.0)
        self._log_to_ui(f"Listening on UDP port {self.UDP_PORT} ...")

        while not self.udp_thread_stop.is_set():
            try:
                data, addr = sock.recvfrom(2048)
                line = data.decode('utf-8', errors='ignore').strip()
                parts = [p.strip() for p in line.split(',') if p != '']

                # Expecting 8 values: uptime,temp,humidity,pm25,pm10,no2,co,aqi_pred
                if len(parts) < 8:
                    self._log_to_ui(f"Skipped packet (expected 8 parts): {parts}")
                    continue
                try:
                    pm25 = float(parts[3])
                    pm10 = float(parts[4])
                    aqi_pred = float(parts[7])
                except Exception:
                    self._log_to_ui(f"Number parse error, packet: {parts}")
                    continue
                aqi_val, aqi_cat, aqi_color = compute_aqi_with_category(pm25, pm10)

                # update UI on main thread
                timestamp = datetime.now().strftime("%H:%M:%S")
                sensor_summary = f"T:{parts[1]}°C  H:{parts[2]}%  PM2.5:{parts[3]}  PM10:{parts[4]}  NO2:{parts[5]}  CO:{parts[6]}"
                self.root.after(0, self._update_ui, aqi_val, aqi_cat, aqi_color, aqi_pred, sensor_summary, timestamp)

            except socket.timeout:
                continue
            except Exception as e:
                self._log_to_ui(f"UDP error: {e}")
                break

        try:
            sock.close()
        except:
            pass
        self._log_to_ui("UDP listener stopped.")
    def _update_ui(self, aqi_val, aqi_cat, aqi_color, aqi_pred, sensor_summary, timestamp):
        # AQI label & color
        display = "--" if aqi_val is None else str(aqi_val)
        self.aqi_label.config(text=display, bg=aqi_color if aqi_val is not None else "#f0f0f0")

        # category & prediction
        self.cat_label.config(text=f"Category: {aqi_cat}")
        self.pred_label.config(text=f"{aqi_pred:.1f}")

        # sensors
        self.sensors_text.set("Sensors: " + sensor_summary)

        # history
        if aqi_val is not None:
            self.aqi_history.append(aqi_val)
            self.time_history.append(timestamp)
            self._refresh_plot()

    def _refresh_plot(self):
        y = list(self.aqi_history)
        x = list(range(len(y)))
        self.line.set_data(x, y)
        self.ax.set_xlim(0, max(10, self.history_len))
        y_max = max(50, max(y) + 20) if y else 100
        self.ax.set_ylim(0, y_max)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()
    
    def _log_to_ui(self, msg):
        # simple print to console;
        print(msg)
    #shutdown handler
    def _on_close(self):
        self.stop_udp()
        self.root.after(200, self.root.destroy)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AQIDashboard(udp_port=8000, history_len=50)
    app.run()
    