import socket
from datetime import datetime

UDP_IP = "0.0.0.0"
UDP_PORT = 9000
FILENAME = "ESP32_AirData_.csv"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on UDP port {UDP_PORT}...")

with open(FILENAME, "a") as f:
    f.write("timestamp,temp,humidity,pm25,pm10\n")
    while True:
        data, addr = sock.recvfrom(1024)
        line = data.decode().strip()
        timestamp = datetime.now().isoformat()
        csv_line = f"{timestamp},{line}\n"
        print(csv_line.strip())
        f.write(csv_line)
        f.flush()
