# -*- coding: utf-8 -*-


import serial
import json
from threading import Thread
import time

class UartReader:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = serial.Serial(port, baudrate, timeout=1)
        self.running = False
        self.data = {}

    def start(self):
        self.running = True
        Thread(target=self.read_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def read_loop(self):
        while self.running:
            line = self.serial.readline().decode(errors="ignore").strip()
            if line:
                try:
                    # Za³ó¿my, ¿e dane s¹ w formacie "key:value"
                    if ":" in line:
                        key, value = line.split(":", 1)
                        self.data[key] = value
                except Exception as e:
                    print("B³¹d parsowania:", e)
            time.sleep(0.1)

    def get_data_json(self):
        return json.dumps(self.data)
