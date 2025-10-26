import serial
import csv
from datetime import datetime

port = 'COM3'    
baud = 115200

ser = serial.Serial(port, baud)
ser.flushInput()
filename = f"ESP32_AirData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["System_Time", "Uptime(ms)", "Temp", "Humidity", "PM2.5", "PM10","CO2","CO"])
    print(f"Logging data to {filename} ... Press Ctrl+C to stop.")
    try:
        while True:
            line = ser.readline().decode('utf-8',errors='ignore').strip()
            if line:
                parts = line.split(',')
                if len(parts) == 7:
                    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + parts)
                    f.flush()
                    print(parts)
                else:
                    print(f"Skipped line (Wrong length, expected 5 parts): {line}")

    except KeyboardInterrupt:
        print("\nLogging stopped.")
    finally:
        ser.close()
