import asyncio
import numpy as np
import soundfile as sf
from pathlib import Path
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor

class AudioSampler:
    """Sample loader and pre-processor for melodic and drum samples."""
    def __init__(self, sample_dir, drum_dir=None):
        self._loaded = None
        self.console = Console()
        self.samples = {}
        self.drums = {}
        self.sample_dir = Path(sample_dir)
        self.drum_dir = Path(drum_dir) if drum_dir else None

        self.notes = ["A", "Asharp", "B", "C", "Csharp", "D", "Dsharp", "E", "F", "Fsharp", "G", "Gsharp"]
        self.octaves = [1, 2, 3, 4, 5, 6]

    async def start(self):
        """Start shit"""
        await asyncio.to_thread(self.load_samples)

        if self.drum_dir:
            await asyncio.to_thread(self.load_drums)
        self._loaded = True

    @staticmethod
    def _load_one(note_key, file_path):
        data, samplerate = sf.read(str(file_path), dtype='float32')
        data = data - np.mean(data)
        if data.ndim == 1:
            data = np.column_stack([data, data])

        return note_key, {"data": data.astype(np.float32), "samplerate": samplerate}

    def load_samples(self):
        paths = []
        for note in self.notes:
            for octv in self.octaves:
                key = f"{note}{octv}"
                path = self.sample_dir / f"{key}v1.ogg"
                if path.exists():
                    paths.append((key, path))

        with ThreadPoolExecutor() as ex:
            results = ex.map(lambda p: self._load_one(*p), paths)

        self.samples = dict(results)

    @staticmethod
    def to_stereo(data):
        if len(data.shape) == 1:
            data = np.column_stack([data, data])
            return data

        elif len(data.shape) == 2:
            return data

        else:
            return None

    def load_drums(self):
        """Load drum samples from drum directory"""
        drum_files = {
            "kick": "kick.ogg",
            "snare": "snare-rev.ogg",
            "hihat": "hat.ogg",
        }

        for drum_name, filename in drum_files.items():
            file_path = self.drum_dir / filename

            if file_path.exists():
                try:
                    data, samplerate = sf.read(str(file_path), dtype='float32')
                    data = data - np.mean(data)

                    self.drums[drum_name] = {
                        "data": data.astype(np.float32),
                        "samplerate": samplerate
                    }

                except Exception as e:
                    self.console.print(f"Failed to load {filename}: {e} :(", style='red')
            else:
                self.console.print(f"{filename} not found in {self.drum_dir} :/", style='yellow')

    def get_drum(self, drum_name):
        """Return pre-processed drum sample"""
        sample = self.drums.get(drum_name)

        if sample is None:
            self.console.print(f"Drum {drum_name} not loaded :/", style='yellow')

        return sample

    def get_available_drums(self):
        """List all loaded drums"""
        return list(self.drums.keys())
