import socket
import csv
from datetime import datetime
import threading
import tkinter as tk

class DataLogger:
    def __init__(self, text_widget, status_label, device_label, last_time_label):
        self.is_logging = False
        self.text_widget = text_widget
        self.status_label = status_label
        self.device_label = device_label
        self.last_time_label = last_time_label
        self.sock = None
        self.f = None
        self.writer = None
        self.last_received = None
        self.device_status_checker_running = False

    def start_logging(self):
        self.is_logging = True
        self.status_label.config(text="Status: Logging...")
        self.last_received = None
        threading.Thread(target=self.run_logger, daemon=True).start()
        # Start status checker thread
        self.device_status_checker_running = True
        threading.Thread(target=self.check_device_status, daemon=True).start()

    def stop_logging(self):
        self.is_logging = False
        self.status_label.config(text="Status: Stopped")
        self.device_label.config(text="Device: Disconnected")
        if self.f:
            self.f.close()
            self.f = None
        if self.sock:
            self.sock.close()
            self.sock = None
        self.device_status_checker_running = False

    def run_logger(self):
        UDP_IP = "0.0.0.0"
        UDP_PORT = 8000
        FILENAME = f"ESP32_AirData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))

        self.text_widget.insert(tk.END, f"Listening on UDP port {UDP_PORT}...\n")
        self.f = open(FILENAME, "a", newline='')
        self.writer = csv.writer(self.f)
        self.writer.writerow(
            ["System_Time", "Uptime(ms)", "Temp", "Humidity", "PM2.5", "PM10", "NO2", "CO"]
        )
        self.text_widget.insert(tk.END, f"Logging data to {FILENAME} ... Press Stop to end\n")

        while self.is_logging:
            try:
                self.sock.settimeout(1.0)
                data, addr = self.sock.recvfrom(1024)
                line = data.decode('utf-8', errors='ignore').strip()
                parts = line.split(',')
                self.last_received = datetime.now()
                self.last_time_label.config(text=f"Last data: {self.last_received.strftime('%Y-%m-%d %H:%M:%S')}")
                if len(parts) == 7:
                    row = [self.last_received.strftime("%Y-%m-%d %H:%M:%S")] + parts
                    self.writer.writerow(row)
                    self.f.flush()
                    self.text_widget.insert(tk.END, str(parts) + "\n")
                    self.text_widget.see(tk.END)
                else:
                    skip_msg = f"Skipped Line, expected 7 parts : {line}"
                    self.text_widget.insert(tk.END, skip_msg + "\n")
                    self.text_widget.see(tk.END)
            except socket.timeout:
                continue
            except Exception as e:
                self.text_widget.insert(tk.END, f"Error: {str(e)}\n")
                self.text_widget.see(tk.END)
                break

        self.stop_logging()

    def check_device_status(self):
        # If updates stop coming for 20 seconds, mark as Disconnected
        while self.device_status_checker_running:
            now = datetime.now()
            if self.last_received is None or (now - self.last_received).seconds > 20:
                self.device_label.config(text="Device: Disconnected")
            else:
                self.device_label.config(text="Device: Connected")
            threading.Event().wait(2)  # Check every 2 seconds

# Tkinter UI setup
root = tk.Tk()
root.title("ESP32 AQI Data Logger")

status_label = tk.Label(root, text="Status: Stopped")
status_label.pack()

device_label = tk.Label(root, text="Device: Disconnected")
device_label.pack()

last_time_label = tk.Label(root, text="Last data: --")
last_time_label.pack()

text_widget = tk.Text(root, height=15, width=70)
text_widget.pack()

logger = DataLogger(text_widget, status_label, device_label, last_time_label)
tk.Button(root, text="Start Logging", command=logger.start_logging).pack()
tk.Button(root, text="Stop Logging", command=logger.stop_logging).pack()

root.mainloop()
