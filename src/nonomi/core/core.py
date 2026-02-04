import asyncio
from rich.console import Console

from src.nonomi.audio.sampler import AudioSampler
from src.nonomi.audio.composer import AudioComposer
from src.nonomi.audio.engine import AudioEngine
from src.nonomi.audio.manager import AudioManager
from src.nonomi.input.cam import CameraInput

class NonomiBeat:
    def __init__(self):
        self.sampler = AudioSampler("src/samples/PianoSamples")
        self.composer = AudioComposer()
        self.engine = AudioEngine(samplerate=44100)
        self.manager = None
        self.camera = None
        self.console = Console()

    async def main(self):
        self.manager = AudioManager(
            sampler=self.sampler,
            composer=self.composer,
            engine=self.engine,
            samplerate=44100,
            blocksize=512
        )

        await self.manager.start()

        self.camera = CameraInput(update_rate=0.1)
        await self.camera.start()

        try:
            while True:
                brightness, warmth = self.camera.get_values()

                self.manager.update_brightness(brightness)
                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            await self.stop()

    async def stop(self):
        self.console.print("Shutting down... :3", style='green')

        await self.manager.stop()
        await self.camera.stop()
