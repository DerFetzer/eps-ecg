"""Example program to demonstrate how to send a multi-channel time-series
with proper meta-data to LSL."""
from datetime import datetime

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
    channel_names = ["I", "II", "III", "NA"]
    signal_headers = highlevel.make_signal_headers(channel_names, dimension='uV', sample_rate=SAMPLE_RATE,
                                                   physical_min=-1*(VREF/GAIN)*1000*1000-100, physical_max=(VREF/GAIN)*1000*1000+100)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

    s.sendto(b"s", (SERVER_IP, SERVER_PORT))

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
