import threading
from collections import deque

import numpy as np
import sounddevice as sd
from rich.console import Console
from dataclasses import dataclass

from src.nonomi.audio.piano import AudioComposer
from src.nonomi.audio.drums import Drums
from src.nonomi.audio.engine import PianoFX, MasterFX

@dataclass
class PlayingNote:
    """A scheduled piano note in the mix buffer."""
    audio_data: np.ndarray
    position: int = 0
    velocity: float = 1.0
    start_delay: int = 0

    @property
    def is_finished(self) -> bool:
        return self.position >= len(self.audio_data) + self.start_delay

    def get_chunk(self, size: int) -> np.ndarray:
        chunk = np.zeros((size, 2), dtype=np.float32)
        if self.position < self.start_delay:
            silence = min(size, self.start_delay - self.position)
            self.position += silence
            if silence == size:
                return chunk

            audio_start = silence
        else:
            audio_start = 0

        audio_pos   = self.position - self.start_delay
        remaining   = len(self.audio_data) - audio_pos
        copy_size   = min(size - audio_start, remaining)
        if copy_size > 0:
            chunk[audio_start:audio_start + copy_size] = (
                    self.audio_data[audio_pos:audio_pos + copy_size] * self.velocity
            )
            self.position += copy_size
        return chunk

class SequencerClock:
    """Sample-accurate clock."""
    STEPS_PER_BAR = 16

    def __init__(self, bpm: float, samplerate: int):
        self.samplerate = samplerate
        self._total_samples = 0
        self._set_bpm(bpm)
        self._swing = 1.0

    def _set_bpm(self, bpm: float):
        spb = 60.0 / bpm
        sps = spb / 4
        self._sps = max(1, round(sps * self.samplerate))
        self._bpm = bpm

    def set_bpm(self, bpm: float):
        old = self._sps
        self._set_bpm(bpm)
        if old > 0:
            frac = self._total_samples / old
            self._total_samples = int(frac * self._sps)

    def reset(self):
        self._total_samples = 0

    @property
    def samples_per_sixteenth(self) -> int:
        return self._sps

    @property
    def samples_per_bar(self) -> int:
        return self._sps * self.STEPS_PER_BAR

    def _swing_offset(self, step_in_bar: int) -> int:
        """Calculate swing offset for a given step in the bar."""
        if self._swing == 0:
            return 0

        if step_in_bar % 4 == 2:
            return round(self._sps * 2 * self._swing / 3)

        return 0

    def advance(self, frames: int) -> list:
        """Advance the clock by a given number of frames and return a list of events that occur during this time."""
        events = []
        sps    = self._sps
        start  = self._total_samples

        first_step_sample = ((start + sps - 1) // sps) * sps

        for step_sample in range(first_step_sample, start + frames, sps):
            offset      = step_sample - start
            if offset >= frames:
                break

            raw_step    = step_sample // sps
            step_in_bar = raw_step % self.STEPS_PER_BAR
            swing_delay = self._swing_offset(step_in_bar)

            events.append(("drum_step",   offset + swing_delay))
            if step_in_bar % 2 == 0:
                events.append(("melody_step", offset + swing_delay))

            if step_in_bar == 0:
                events.append(("chord_change", offset))

        self._total_samples += frames
        return events

class AudioManager:
    """Manages audio playback, sequencing, and mixing."""
    def __init__(self, sampler, bpm: float = 156.0, samplerate: int = 44100, blocksize: int = 512):
        self.sampler    = sampler
        self.samplerate = samplerate
        self.blocksize  = blocksize
        self.console    = Console()

        self.composer    = AudioComposer(progression_length=8)
        self.drums       = Drums(sampler, samplerate=samplerate)
        self.master_fx   = MasterFX(samplerate=samplerate)
        self.clock       = SequencerClock(bpm=bpm, samplerate=samplerate)

        self.piano_fx = PianoFX(samplerate=samplerate)
        self._processed_samples: dict[str, np.ndarray] = {}

        for name, sample in sampler.samples.items():
            raw = sample["data"]
            if raw.ndim == 1:
                raw = np.column_stack([raw, raw])
            self._processed_samples[name] = self.piano_fx.process(raw)

        self.playing_notes: list[PlayingNote] = []
        self._lock   = threading.Lock()
        self._stream: sd.OutputStream | None = None
        self._running = False

        self.composer.generate_progression()

        self.viz_buffer: deque[np.ndarray] = deque(maxlen=5)

    def _trigger_chord(self):
        """Play the current chord's bass and notes with a strum effect."""
        notes = self.composer.get_chord_notes(octave=3)
        bass  = self.composer.get_bass_note(octave=2)

        self._schedule_note(bass, velocity_range=(0.5, 0.7), delay_sec=0.0)

        strum = 0.0
        for note in notes:
            self._schedule_note(note, velocity_range=(0.3, 0.5), delay_sec=strum)
            strum += np.random.uniform(0.02, 0.05)

    def _trigger_melody(self):
        note = self.composer.get_melody_note()
        if note:
            self._schedule_note(note, velocity_range=(0.25, 0.40), delay_sec=0.0)

    def _advance_chord(self):
        changes = self.composer.advance_chord()

        if changes.get("randomize_drums"):
            self.drums.randomize_mutes()

        if "melody_density" in changes:
            self.composer.melody_density = changes["melody_density"]

        if "melody_off" in changes:
            self.composer.melody_off = changes["melody_off"]

    def _schedule_note(self, note_name: str, velocity_range: tuple, delay_sec: float):
        processed = self._processed_samples.get(note_name)
        if processed is None:
            self.console.print(f"Note {note_name} not found :/", style="yellow")
            return
        self.playing_notes.append(PlayingNote(
            audio_data=processed,
            velocity=np.random.uniform(*velocity_range),
            start_delay=int(delay_sec * self.samplerate),
        ))

    def _audio_callback(self, outdata, frames, time_info, status):
        if status:
            #self.console.log(f"[Audio] {status}", style="yellow")
            pass

        bus = np.zeros((frames, 2), dtype=np.float32)

        with self._lock:
            events = self.clock.advance(frames)

            for (etype, offset, *_) in events:
                if etype == "drum_step":
                    self.drums.advance_step()

                elif etype == "melody_step":
                    self._trigger_melody()

                elif etype == "chord_change":
                    self._trigger_chord()
                    self._advance_chord()

            finished = []
            for i, note in enumerate(self.playing_notes):
                bus[:frames] += note.get_chunk(frames)
                if note.is_finished:
                    finished.append(i)

            for i in reversed(finished):
                self.playing_notes.pop(i)

            bus += self.drums.get_active_hits(frames)

        processed = self.master_fx.process(bus)
        self.viz_buffer.append(processed.copy())
        outdata[:] = np.clip(processed, -1.0, 1.0)

    def start(self):
        self._stream = sd.OutputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            channels=2,
            dtype=np.float32,
            callback=self._audio_callback,
        )
        self._stream.start()

    async def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()

    def reset_clock(self):
        with self._lock:
            self.clock.reset()
            self.drums.reset_step()

    def regenerate(self):
        """JS: generateProgression button — pick new key + progression."""
        with self._lock:
            self.composer.generate_progression()
            self.clock.reset()
            self.drums.reset_step()

    def set_tempo(self, bpm: float):
        with self._lock:
            self.clock.set_bpm(bpm)

    def update_brightness(self, brightness: float):
        self.master_fx.update_filter(brightness)

    def toggle_drums(self):
        self.drums.toggle_drums()

    def toggle_melody(self):
        self.composer.melody_off = not self.composer.melody_off
