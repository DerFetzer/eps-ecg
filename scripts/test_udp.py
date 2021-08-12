import socket
import struct
import json

SERVER_IP = "192.168.178.46"
SERVER_PORT = 4210

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
s.settimeout(2)

# Lead-Off Detection
s.sendto(b"l", (SERVER_IP, SERVER_PORT))
data = s.recv(4096)
if len(data) == 2:
    print("Lead-Off: {0:b} {0:b}".format(data[0] & 0x3, data[1] & 0x3))
else:
    print("Invalid response to lead off command")
    raise RuntimeError()

# params = {"data_rate": 0, "rld_sens_p": 1, "rld_sens_n": 2, "channels": [{"gain": 1, "mux": 2}, {"gain": 2, "mux": 3}, {"gain": 3, "mux": 4}]}
#
# s.sendto(b"c" + json.dumps(params).encode("latin-1"), (SERVER_IP, SERVER_PORT))
#
# data = s.recv(4096)
# if data[0] == 1:
#     print("Config successful")
#     s.sendto(b"?", (SERVER_IP, SERVER_PORT))
#     data = s.recv(4096)
#     print(data.hex())
# else:
#     print("Config not successful")
#     raise RuntimeError()

s.sendto(b"s", (SERVER_IP, SERVER_PORT))
data = s.recv(4096)
if data[0] == 1:
    print("Start successful")
else:
    print("Start not successful")
    raise RuntimeError()

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