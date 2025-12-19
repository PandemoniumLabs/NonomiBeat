import threading
import array
import pylibpd as pd
import pyaudio
from ..utils.logger import get_logger

logger = get_logger("AudioEngine")

class AudioEngine:
    def __init__(self, patch_path, sample_rate=44100, block_size=64):
        self.block_size = block_size
        self.patch_path = patch_path
        self.sample_rate = sample_rate

        self.patch_handle = None
        self.capturer = None
        self.manager = None
        self.stream = None
        self.pya = None

        self._running = False
        self._lock = threading.Lock()
        self._dummy_inbuf = array.array('h')

        self.ticks = block_size // 64

    async def start(self):
        pd.libpd_release()
        self.patch_handle = pd.libpd_open_patch(self.patch_path)
        self.manager = pd.PdManager(0, 2, self.sample_rate, self.ticks)

        self.pya = pyaudio.PyAudio()
        self.stream = self.pya.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.block_size,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()
        self._running = True

    def _audio_callback(self, in_data, frame_count, time_info, status):
        out_data = self.manager.process(self._dummy_inbuf)
        return out_data.tobytes(), pyaudio.paContinue

    def send_brightness(self, value):
        if self._running:
            with self._lock:
                pd.libpd_float('brightness', float(value))

    def send_hue(self, value: float):
        if self._running:
            with self._lock:
                pd.libpd_float('hue', float(value))

    def set_filter_cutoff(self, freq: float):
        if self._running:
            with self._lock:
                pd.libpd_float('filter_cutoff', float(freq))

    async def stop(self):
        self._running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.pya.terminate()

        if self.patch_handle is not None:
            pd.libpd_close_patch(self.patch_handle)