"""Example program to demonstrate how to send a multi-channel time-series
with proper meta-data to LSL."""
import sys
import socket
import struct

import time
from random import random as rand

import pylsl

SERVER_IP = "192.168.178.46"
SERVER_PORT = 4210

NUMBER_OF_CHANNELS = 4
GAIN = 8
RESOLUTION = 16
VREF = 2.4

def main():
    srate = 1000
    name = 'LSLExampleAmp'
    stream_type = 'ECG'
    channel_names = ["I", "II", "III", "0"]
    n_channels = len(channel_names)

    # first create a new stream info (here we set the name to BioSemi,
    # the content-type to EEG, 8 channels, 100 Hz, and float-valued data) The
    # last value would be the serial number of the device or some other more or
    # less locally unique identifier for the stream as far as available (you
    # could also omit it but interrupted connections wouldn't auto-recover).
    info = pylsl.StreamInfo(name, stream_type, n_channels, srate, 'float32', 'myuid2424')

    # append some meta-data
    info.desc().append_child_value("manufacturer", "LSLExampleAmp")
    chns = info.desc().append_child("channels")
    for label in channel_names:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("unit", "microvolts")
        ch.append_child_value("type", "ECG")
    info.desc().append_child_value("manufacturer", "LSLExamples")

    # next make an outlet; we set the transmission chunk size to 30 samples and
    # the outgoing buffer size to 360 seconds (max.)
    outlet = pylsl.StreamOutlet(info, 30, 360)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.settimeout(2)

    s.sendto(b"s", (SERVER_IP, SERVER_PORT))

    conversion_factor = ((2.0 * VREF) / GAIN / (pow(2, RESOLUTION) - 1)) * 1000 * 1000

    try:
        while True:
            data = s.recv(4096)
            # print(f"data: {data}")

            chunk = []
            current_samples = []

            i = 0
            while data:
                sample = struct.unpack(">h", data[:2])[0]
                sample = sample * conversion_factor
                current_samples.append(sample)
                if i % NUMBER_OF_CHANNELS == NUMBER_OF_CHANNELS - 1:
                    chunk.append(current_samples)
                    current_samples = []
                data = data[2:]
                i += 1
            # print(chunk)
            outlet.push_chunk(chunk)
    finally:
        s.sendto(b"f", (SERVER_IP, SERVER_PORT))


if __name__ == '__main__':
    main()
