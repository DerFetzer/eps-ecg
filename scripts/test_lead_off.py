import socket
import struct
import time

SERVER_IP = "192.168.178.46"
SERVER_PORT = 4210

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
s.settimeout(2)

while True:
    # Lead-Off Detection
    s.sendto(b"l", (SERVER_IP, SERVER_PORT))
    data = s.recv(4096)
    if len(data) == 16:
        print("Lead-Off: {:b} {:b} {:b}".format(data[0] & 0xF, data[1] & 0xF, data[2]))
        data = data[8:]

        while data:
            sample = struct.unpack(">h", data[:2])[0]
            print("Channel value: {}".format(sample))
            data = data[2:]
    else:
        print("Invalid response to lead off command")
        raise RuntimeError()
    time.sleep(0.2)
