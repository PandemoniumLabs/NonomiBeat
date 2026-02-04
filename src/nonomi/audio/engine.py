import numpy as np
from pedalboard import Pedalboard, Reverb, Limiter, Bitcrush, LowpassFilter

class AudioEngine:
    def __init__(self, samplerate=44100):
        self.samplerate = samplerate
        self._current_cutoff = 22000

        self.board = Pedalboard([
            LowpassFilter(cutoff_frequency_hz=self._current_cutoff),
            Bitcrush(bit_depth=16),
            Reverb(room_size=0.25, wet_level=0.3),
            Limiter()
        ])

    def apply_master_fx(self, audio_chunk):
        """Apply primary effects to the audio chunk"""
        processed = self.board(audio_chunk, self.samplerate, reset=False)
        return processed.astype(np.float32)

    def update_filter(self, brightness):
        target = 200 + brightness * (15000 - 200)
        target = max(200, min(target, 15000))

        self._current_cutoff += (target - self._current_cutoff) * 0.05
        self.board[0].cutoff_frequency_hz = self._current_cutoff
