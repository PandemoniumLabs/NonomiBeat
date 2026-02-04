import soundfile as sf
from pathlib import Path
from rich.console import Console
import numpy as np

class AudioSampler:
    def __init__(self, sample_dir):
        self.console = Console()
        self.samples = {}
        self.sample_dir = Path(sample_dir)

        self.notes = ["A", "Asharp", "B", "C", "Csharp", "D", "Dsharp", "E", "F", "Fsharp", "G", "Gsharp"]
        self.octaves = [1, 2, 3, 4, 5, 6]
        self.load_samples()

    def load_samples(self):
        for note in self.notes:
            for octv in self.octaves:
                note_key = f"{note}{octv}"
                file_path = self.sample_dir / f"{note_key}v1.ogg"

                if file_path.exists():
                    data, samplerate = sf.read(str(file_path), dtype='float32')
                    data = data - np.mean(data)
                    self.samples[note_key] = {"data": data, "samplerate": samplerate}

                    if len(data.shape) > 1:
                        data = data.astype(np.float32)

                    self.samples[note_key] = {
                        "data": data,
                        "samplerate": samplerate
                    }
                else:
                    self.console.print(f"File {note_key}v1.ogg not found! Skipping... :/", style='red')

    def get_note(self, note_name):
        """Return pre-processed audio sample"""
        sample = self.samples.get(note_name)
        self.console.print(note_name)

        if sample is None:
            self.console.print(f"Note {note_name} not loaded :/", style='yellow')

        return sample