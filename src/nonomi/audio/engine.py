import numpy as np
from pedalboard import Pedalboard, Limiter, MP3Compressor, LowpassFilter, Bitcrush

class PianoFX:
    """PianoFX chain with a simple lowpass filter and stereo widener."""
    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate
        self.board = Pedalboard([
            LowpassFilter(cutoff_frequency_hz=1000.0),
        ])
        self.widener_amount = 0.5

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.ndim == 1:
            audio = np.column_stack([audio, audio])

        processed = self.board(audio, self.samplerate, reset=False)
        return self._stereo_widen(processed, self.widener_amount)

    @staticmethod
    def _stereo_widen(audio: np.ndarray, amount: float) -> np.ndarray:
        """Mid-side stereo widening."""
        if audio.ndim != 2 or audio.shape[1] != 2:
            return audio

        mid  = (audio[:, 0] + audio[:, 1]) * 0.5
        side = (audio[:, 0] - audio[:, 1]) * 0.5
        side *= (1.0 + amount)
        left  = mid + side
        right = mid - side

        return np.column_stack([left, right]).astype(np.float32)

class MasterFX:
    """Master FX"""
    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate
        self._lpf_cutoff = 2000.0
        self.board = Pedalboard([
            #MP3Compressor(vbr_quality=8),
            LowpassFilter(cutoff_frequency_hz=self._lpf_cutoff),
            Limiter(threshold_db=-0.5),
            Bitcrush(bit_depth=32)
        ])
        self._master_vol = 0.5

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.ndim == 1:
            audio = np.column_stack([audio, audio])

        processed = self.board(audio, self.samplerate, reset=False)
        processed = np.tanh(processed * 0.8) * self._master_vol
        return processed.astype(np.float32)

    def update_filter(self, brightness: float):
        """Camera brightness modulates the master LPF"""
        target = 200 + brightness * (15000 - 200)
        target = max(200.0, min(target, 15000.0))

        self._lpf_cutoff += (target - self._lpf_cutoff) * 0.05
        self.board[0].cutoff_frequency_hz = self._lpf_cutoff
