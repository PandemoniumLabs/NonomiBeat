import random
import numpy as np
from dataclasses import dataclass

@dataclass
class DrumHit:
    audio_data: np.ndarray
    position: int = 0
    velocity: float = 1.0

    @property
    def is_finished(self) -> bool:
        return self.position >= len(self.audio_data)

    def get_chunk(self, size: int) -> np.ndarray:
        chunk = np.zeros((size, 2), dtype=np.float32)
        remaining = len(self.audio_data) - self.position

        copy_size = min(size, remaining)
        if copy_size > 0:
            chunk[:copy_size] = self.audio_data[self.position:self.position + copy_size] * self.velocity
            self.position += copy_size

        return chunk

class Drums:
    """Drum sequencer"""
    STEPS = 32
    KICK_SLOTS  = {0: 0.9, 14: 0.9, 16: 0.9, 20: 0.1}
    SNARE_SLOTS = {8: 0.80, 24: 0.80}
    HAT_SLOTS   = {s: 0.80 for s in range(0, 32, 4)}

    def __init__(self, sampler, samplerate: int = 44100):
        self.sampler = sampler
        self.samplerate = samplerate
        self.current_step = 0
        self.active_hits: list[DrumHit] = []
        self.enable_drums = True
        self.drum_vol = 0.25

        self.kick_off  = False
        self.snare_off = False
        self.hat_off   = False

    def _maybe_fire(self, off_flag, slots, name, vel_range):
        if off_flag:
            return

        prob = slots.get(self.current_step)
        if prob and random.random() < prob:
            self._fire(name, velocity=np.random.uniform(*vel_range))

    def advance_step(self):
        """Fires hits for the current step."""
        if self.enable_drums:
            instruments = [
                (self.kick_off,  self.KICK_SLOTS,  "kick",  (0.85, 1.0)),
                (self.snare_off, self.SNARE_SLOTS, "snare", (0.7, 0.9)),
                (self.hat_off,   self.HAT_SLOTS,   "hihat", (0.3, 0.8)),
            ]

            for off_flag, slots, name, vel_range in instruments:
                self._maybe_fire(off_flag, slots, name, vel_range)

        self.current_step = (self.current_step + 1) % self.STEPS


    def randomize_mutes(self):
        """Randomizes which drum parts are muted for the next 8 steps."""
        self.kick_off  = random.random() < 0.15
        self.snare_off = random.random() < 0.20
        self.hat_off   = random.random() < 0.25

    def _fire(self, drum_name: str, velocity: float):
        sample = self.sampler.get_drum(drum_name)
        if not sample:
            return

        data = sample["data"]
        if data.ndim == 1:
            data = np.column_stack([data, data])

        self.active_hits.append(DrumHit(audio_data=data, velocity=velocity))

    def get_active_hits(self, frames: int) -> np.ndarray:
        mix = np.zeros((frames, 2), dtype=np.float32)
        finished = []
        for i, hit in enumerate(self.active_hits):
            mix += hit.get_chunk(frames) * self.drum_vol
            if hit.is_finished:
                finished.append(i)

        for i in reversed(finished):
            self.active_hits.pop(i)

        return mix

    def reset_step(self):
        self.current_step = 0

    def toggle_drums(self):
        self.enable_drums = not self.enable_drums
