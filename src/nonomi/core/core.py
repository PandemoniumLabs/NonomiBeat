from ..utils.logger import get_logger
from ..audio.audio import AudioEngine
from ..input.cam import CameraInput
import asyncio

logger = get_logger("NonomiCore")

class NonomiBeat:
    def __init__(self, patch_path: str):
        self.camera = CameraInput()
        self.audio = AudioEngine(patch_path=patch_path)
        self._running = False
        self._task = None
        self._last_track = -1

    async def start(self):
        """Start all systems and main loop"""
        self._running = True

        await self.camera.start()
        await self.audio.start()
        await self._main_loop()

        logger.info("NonomiBeat started :3")

    async def stop(self):
        """Stop all systems"""
        self._running = False
        if self._task:
            await self._task

        await self.camera.stop()
        await self.audio.stop()

        logger.info("NonomiBeat stopped :3")

    async def _main_loop(self):
        """Main processing loop"""
        try:
            while self._running:
                brightness, hue = self.camera.get_values()

                self.audio.send_brightness(brightness)
                self.audio.send_hue(hue)

                # Track selection
                # track_id = self._select_track(brightness)
                # if track_id != self._last_track:
                #     self.audio.play_track(track_id)
                #     self._last_track = track_id
                #     logger.debug(f"Switched to track {track_id}")
                #
                # # Filter control (now actually used)
                # cutoff = self._brightness_to_filter(brightness)
                # self.audio.set_filter_cutoff(cutoff)
                #
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Main loop error: {e}")
            await self.stop()

    @staticmethod
    def _select_track(brightness: float) -> int:
        """Map brightness to track ID (0-9)"""
        return int(brightness * 9)

    @staticmethod
    def _brightness_to_filter(brightness: float) -> float:
        """Map brightness to lowpass filter cutoff"""
        min_freq = 500   # Hz
        max_freq = 8000  # Hz
        return min_freq + (brightness * (max_freq - min_freq))