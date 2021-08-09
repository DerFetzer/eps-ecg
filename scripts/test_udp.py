import socket
import struct
import json

SERVER_IP = "192.168.178.46"
SERVER_PORT = 4210

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

params = {"data_rate": 0, "rld_sens_p": 1, "rld_sens_n": 2, "channels": [{"gain": 1, "mux": 2}, {"gain": 2, "mux": 3}, {"gain": 3, "mux": 4}]}

s.sendto(b"s" + json.dumps(params).encode("latin-1"), (SERVER_IP, SERVER_PORT))

for i in range(5):
    data = s.recv(4096)
    print(f"data: {data}")

    chunk = [[] for _ in range(4)]

    j = 0
    while data:
        sample = struct.unpack(">h", data[:2])[0]
        chunk[j % 4].append(sample)
        data = data[2:]
        j += 1
    print(chunk)

s.sendto(b"f", (SERVER_IP, SERVER_PORT))