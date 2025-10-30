import socket, csv, time

UDP_IP = "0.0.0.0"      # listen on all interfaces
UDP_PORT = 5005
filename = "data_log.csv"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on UDP {UDP_PORT} ...")
with open(filename, "a", newline="") as f:
    writer = csv.writer(f)
    while True:
        data, addr = sock.recvfrom(1024)
        line = data.decode().strip()
        print("Received:", line)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp] + line.split(","))
        f.flush()
