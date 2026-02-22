import numpy as np
import asyncio
from collections import deque
from rich.console import Console
from rich.live import Live
from rich.text import Text

BLOCKS = " ▁▂▃▄▅▆▇█"

class Visualizer:
    def __init__(self, bars: int = 64, refresh_rate: int = 30, smoothing: float = 0.5):
        self.bars = bars
        self.refresh = refresh_rate
        self.smoothing = max(0.0, min(1.0, smoothing))

        self.smoothed = np.zeros(self.bars, dtype=np.float32)
        self.samplerate = 44100
        self.magnitudes = np.zeros(self.bars, dtype=np.float32)

        self.text = Text()
        self.colour = "green"

    def _render(self, magnitudes: np.ndarray, width: int | None = None):
        if width is None:
            width = self.bars

        for mag in magnitudes:
            idx = int(np.clip(mag * (len(BLOCKS) -1 ), 0,len(BLOCKS) -1))
            char = BLOCKS[idx]

            if mag < 0.4:
                self.colour = "green"
            elif mag < 0.75:
                self.colour = "yellow"
            else:
                self.colour = "red"
            self.text.append(char + char, style=self.colour)
        return self.text

    async def run_visualizer(self, viz_buffer: deque, console: Console, stop_event: asyncio.Event):
        with Live("", console=console, refresh_per_second=self.refresh, transient=True) as live:
            while not stop_event.is_set():
                self._viz(viz_buffer)
                live.update(self._render(self.smoothed))
                await asyncio.sleep(1/self.refresh)

    def _viz(self, viz_buffer: deque):
        if viz_buffer:
            chunks = []
            while viz_buffer:
                chunks.append(viz_buffer.popleft())
            audio = np.concatenate(chunks, axis=0)

            mono = audio.mean(axis=1)

            fft = np.abs(np.fft.rfft(mono, n=2048))
            freqs = np.fft.rfftfreq(2048, d=1/self.samplerate)

            log_min = np.log10(20)
            log_max = np.log10(16000)
            edges = np.logspace(log_min, log_max, self.bars + 1)

            for i in range(self.bars):
                mask = (freqs >= edges[i]) & (freqs < edges[i+1])
                if mask.any():
                    self.magnitudes[i] = fft[mask].mean()

            peak = self.magnitudes.max()
            if peak > 0:
                self.magnitudes /= peak

            self.smoothed = self.smoothed * self.smoothing + self.magnitudes * (1 - self.smoothing)
            self.text = Text()
