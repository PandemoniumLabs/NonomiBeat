import asyncio
from rich.console import Console

from src.nonomi.input.cam import CameraInput
from src.nonomi.audio.sampler import AudioSampler
from src.nonomi.audio.manager import AudioManager

class NonomiBeat:
    """Main application class for Nonomi Beat."""
    def __init__(self):
        self.manager = None
        self.sampler = AudioSampler(
            sample_dir="src/samples/PianoSamples",
            drum_dir="src/samples/DrumSamples"
        )

        self.camera  = None
        self.console = Console()

    async def main(self, ready_event: asyncio.Event = None):
        await self.sampler.start()

        self.manager = AudioManager(
            sampler=self.sampler,
            bpm=156.0,
            samplerate=44100,
            blocksize=512,
        )
        self.manager.start()
        self.manager.reset_clock()

        self.camera = CameraInput(update_rate=0.1)
        await self.camera.start()

        if ready_event:
            ready_event.set()

        while True:
            brightness, warmth = self.camera.get_values()
            self.manager.update_brightness(brightness)
            await asyncio.sleep(0.1)

    async def stop(self):
        await self.manager.stop()
        await self.camera.stop()