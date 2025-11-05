import socket
import csv
from datetime import datetime

UDP_IP = "0.0.0.0"
UDP_PORT = 9000
FILENAME = f"ESP32_AirData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on UDP port {UDP_PORT}...")

with open(FILENAME, "a", newline='') as f:
    writer=csv.writer(f)
    writer.writerow(["System_Time", "Uptime(ms)", "Temp", "Humidity", "PM2.5", "PM10","NO2","CO"])
    print(f"Logging data to {FILENAME} ... Press Ctrl+C to stop")
    try:
        while True:
            data, addr= sock.recvfrom(1024)
            line = data.decode('utf-8',errors='ignore').strip()
            parts=line.split(',')
            if len(parts)==7:
                writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + parts)
                f.flush()
                print(parts)
            else:
                print(f"Skipped Line, expected 7 parts : {line}")
    except KeyboardInterrupt:
        print("\nLogging Stopped")
