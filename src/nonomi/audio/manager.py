import threading
import numpy as np
import sounddevice as sd
from collections import deque
from rich.console import Console
from dataclasses import dataclass

from src.nonomi.audio.composer import MelodicGenerator

@dataclass
class PlayingNote:
    audio_data: np.ndarray
    position: int = 0
    velocity: float = 1.0
    start_delay: int = 0

    @property
    def is_finished(self) -> bool:
        return self.position >= (len(self.audio_data) + self.start_delay)

    def get_chunk(self, size: int) -> np.ndarray:
        chunk = np.zeros((size, 2), dtype=np.float32)

        if self.position < self.start_delay:
            wait_time = min(size, self.start_delay - self.position)
            self.position += wait_time
            if wait_time == size:
                return chunk
            start_idx = wait_time

        else:
            start_idx = 0

        audio_pos = self.position - self.start_delay
        remaining_audio = len(self.audio_data) - audio_pos
        copy_size = min(size - start_idx, remaining_audio)

        if copy_size > 0:
            chunk[start_idx : start_idx + copy_size] = (
                    self.audio_data[audio_pos : audio_pos + copy_size] * self.velocity
            )
            self.position += copy_size

        return chunk

class AudioManager:
    def __init__(self, sampler, composer, engine, samplerate=44100, blocksize=5096):
        self.sampler = sampler
        self.composer = composer
        self.engine = engine
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.master_bus = np.zeros((8192, 2), dtype=np.float32)

        self.playing_notes = []
        self.note_queue = deque()
        self._lock = threading.Lock()

        self.beat_duration = 0.5
        self.next_chord_time = 0
        self.current_time = 0
        self.melody_gen = MelodicGenerator(composer)

        self.enable_bass = True
        self.enable_melody = False

        self.stream = None
        self._running = False

        self.console = Console()

    def _trigger_next_chord(self):
        """Trigger the next chord"""
        self.composer.get_next_chord()

        note_names = self.composer.get_chord_notes(
            self.composer.current_root,
            3,
            randomize_voicing=True
        )

        current_strum = 0

        if self.enable_bass:
            bass_note = self.composer.get_bass_note(octave=2)
            sample = self.sampler.get_note(bass_note)
            if sample:
                playing_note = PlayingNote(
                    audio_data=sample['data'],
                    velocity=np.random.uniform(0.5, 0.7),
                    start_delay=0
                )
                self.playing_notes.append(playing_note)

        for note_name in note_names:
            sample = self.sampler.get_note(note_name)
            if sample:
                delay_samples = int(current_strum * self.samplerate)

                playing_note = PlayingNote(
                    audio_data=sample['data'],
                    velocity=np.random.uniform(0.3, 0.5),
                    start_delay=delay_samples
                )
                self.playing_notes.append(playing_note)
                current_strum += np.random.uniform(0.03, 0.06)

        if self.enable_melody:
            melody_notes = self.melody_gen.generate_melody_notes(
                num_notes=4,
                octave=4,
                use_weights=True
            )
            for i, note_name in enumerate(melody_notes):
                sample = self.sampler.get_note(note_name)
                if sample:
                    delay = int((current_strum + i * 0.25) * self.samplerate)
                    playing_note = PlayingNote(
                        audio_data=sample['data'],
                        velocity=np.random.uniform(0.4, 0.6),
                        start_delay=delay
                    )
                    self.playing_notes.append(playing_note)

    def set_progression_length(self, length: int):
        """Change progression on the fly"""
        with self._lock:
            self.composer.regenerate_progression(length)

    def set_key(self, key: str):
        """Change musical key"""
        with self._lock:
            self.composer.set_key(key)

    def toggle_bass(self):
        """Turn bass on/off"""
        self.enable_bass = not self.enable_bass

    def toggle_melody(self):
        """Turn melody on/off"""
        self.enable_melody = not self.enable_melody

    def _audio_callback(self, outdata, frames, time_info, status):
        if status:
            self.console.print(f"Audio callback status: {status}", style='yellow')

        self.master_bus[:frames].fill(0)

        with self._lock:
            self.current_time += frames / self.samplerate

            if self.current_time >= self.next_chord_time:
                self._trigger_next_chord()
                self.next_chord_time = self.current_time + self.beat_duration * 4

            finished_notes = []
            for i, note in enumerate(self.playing_notes):
                chunk = note.get_chunk(frames)
                self.master_bus[:frames] += chunk

                if note.is_finished:
                    finished_notes.append(i)

            for i in reversed(finished_notes):
                self.playing_notes.pop(i)

        self.master_bus[:frames] *= 1

        processed = self.engine.apply_master_fx(self.master_bus[:frames])
        outdata[:] = np.tanh(processed.reshape(-1, 2) * 1.5) / 1.5

    async def start(self):
        """Start the audio stream"""
        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            channels=2,
            dtype=np.float32,
            callback=self._audio_callback
        )

        self.stream.start()
        self._running = True

        with self._lock:
            self._trigger_next_chord()
            self.next_chord_time = self.current_time + self.beat_duration * 4

        self.console.print("AudioManager started :3", style='green')

    async def stop(self):
        """Stop the audio stream"""
        self._running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.console.print("AudioManager stopped :3", style='green')

    def set_tempo(self, bpm: float):
        """Change tempo (BMP)"""
        with self._lock:
            self.beat_duration = 60.0 / bpm

    def update_brightness(self, brightness: float):
        """Update filter based on camera brightness"""
        self.engine.update_filter(brightness)
