import cv2
import numpy as np
import asyncio
from collections import deque

class CameraInput:
    def __init__(self, buffer_size=30, update_rate=0.05):
        self.brightness_buffer = deque(maxlen=buffer_size)
        self.hue_buffer = deque(maxlen=buffer_size)
        self.update_rate = update_rate

        self.brightness = 0.5
        self.hue = 0

        self.cap = None
        self._running = False

    async def start(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("RIP: Camera won't open.")
            return

        self._running = True
        asyncio.create_task(self._capture_loop())
        print("Camera task spawned (^_^)v")

    async def _capture_loop(self):
        while self._running:
            ret = False
            for _ in range(5):
                ret, frame = self.cap.read()

            if not ret or frame is None:
                print("Camera dropped a frame...")
                await asyncio.sleep(self.update_rate)
                continue

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            b_val = np.mean(hsv[:, :, 2]) / 255.0
            h_val = np.mean(hsv[:, :, 0]) / 180.0

            self.brightness_buffer.append(b_val)
            self.hue_buffer.append(h_val)

            if self.brightness_buffer:
                self.brightness = sum(self.brightness_buffer) / len(self.brightness_buffer)
                self.hue = sum(self.hue_buffer) / len(self.hue_buffer)

            await asyncio.sleep(self.update_rate)

    async def stop(self):
        self._running = False

    def get_values(self):
        return self.brightness, self.hue