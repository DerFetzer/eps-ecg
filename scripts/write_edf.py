"""Example program to demonstrate how to send a multi-channel time-series
with proper meta-data to LSL."""
from datetime import datetime
import json
import time

import socket
import struct

import numpy as np
from pyedflib import highlevel

SERVER_IP = "192.168.178.46"
SERVER_PORT = 4210

SAMPLE_RATE = 1000

NUMBER_OF_CHANNELS = 4
GAIN = 12
RESOLUTION = 16
VREF = 2.4


def main():
    time.sleep(2)

    channel_names = ["I", "II", "III", "NA"]
    signal_headers = highlevel.make_signal_headers(channel_names, dimension='uV', sample_rate=SAMPLE_RATE,
                                                   physical_min=-1*(VREF/GAIN)*1000*1000-100, physical_max=(VREF/GAIN)*1000*1000+100)

    params = {"data_rate": 3,
              "rld_sens_p": -1,
              "rld_sens_n": -1,
              "channels": [
                  {"gain": 6, "mux": 0},
                  {"gain": 6, "mux": 0},
                  {"gain": 6, "mux": 0},
                  {"gain": 6, "mux": 2}
              ]}

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.settimeout(2)

    # s.sendto(b"c" + json.dumps(params).encode("latin-1"), (SERVER_IP, SERVER_PORT))
    #
    # data = s.recv(4096)
    # if data[0] == 1:
    #     print("Config successful")
    #     s.sendto(b"?", (SERVER_IP, SERVER_PORT))
    #     data = s.recv(4096)
    #     for b in data:
    #         print(f"{bin(b)}")
    #     print(data.hex(" ", 1))
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

    conversion_factor = ((2.0 * VREF) / GAIN / (pow(2, RESOLUTION) - 1)) * 1000 * 1000

    channels = [[] for _ in range(NUMBER_OF_CHANNELS)]

    try:
        while True:
            data = s.recv(4096)
            i = 0
            while data:
                raw_sample = struct.unpack(">h", data[:2])[0]
                conv_sample = int(round(raw_sample * conversion_factor))
                channels[i % NUMBER_OF_CHANNELS].append(int(round(conv_sample)))
                data = data[2:]
                i += 1
            # print(chunk)
    finally:
        s.sendto(b"f", (SERVER_IP, SERVER_PORT))
        highlevel.write_edf("edf_{}.edf".format(int(datetime.now().timestamp())), np.array(channels), signal_headers)


if __name__ == '__main__':
    main()
