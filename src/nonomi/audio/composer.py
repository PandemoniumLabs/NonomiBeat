import random
from dataclasses import dataclass
from typing import List
import numpy as np

MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]

def to_chord_idxs(degrees: List[int]) -> List[int]:
    return [d - 1 for d in degrees]

@dataclass
class Chord:
    degree: int
    intervals: List[int]
    next_idxs: List[int]

    @property
    def semitone_dist(self) -> int:
        """Get the root note's distance from tonic in semitones"""
        return MAJOR_SCALE[self.degree - 1]

    def get_next_chord_idx(self) -> int:
        """Pick a random valid next chord"""
        return random.choice(self.next_idxs)

    def generate_voicing(self, size: int) -> List[int]:
        if size < 3:
            return self.intervals[:3]

        voicing = self.intervals[1:size]
        random.shuffle(voicing)

        for i in range(1, len(voicing)):
            while voicing[i] < voicing[i-1]:
                voicing[i] += 12

        voicing.insert(0, 0)
        return voicing

    def generate_mode(self) -> List[int]:
        """Get intervals within one octave. Basically collapses everything to 0-11 semitones."""
        return [n - 12 if n >= 12 else n for n in self.intervals]

CHORD_I = Chord(
    degree=1,
    intervals=[0, 4, 7, 11, 14, 17, 21],
    next_idxs=to_chord_idxs([2, 3, 4, 5, 6, 7])
)

CHORD_ii = Chord(
    degree=2,
    intervals=[0, 3, 7, 10, 14, 17, 21],
    next_idxs=to_chord_idxs([3, 5, 7])
)

CHORD_iii = Chord(
    degree=3,
    intervals=[0, 3, 7, 10, 13, 17, 20],
    next_idxs=to_chord_idxs([4, 6])
)

CHORD_IV = Chord(
    degree=4,
    intervals=[0, 4, 7, 11, 14, 18, 21],
    next_idxs=to_chord_idxs([2, 5])
)

CHORD_V = Chord(
    degree=5,
    intervals=[0, 4, 7, 10, 14, 17, 21],
    next_idxs=to_chord_idxs([1, 3, 6])
)

CHORD_vi = Chord(
    degree=6,
    intervals=[0, 3, 7, 10, 14, 17, 20],
    next_idxs=to_chord_idxs([2, 4])
)

CHORD_vii = Chord(
    degree=7,
    intervals=[0, 3, 6, 10, 13, 17, 20],
    next_idxs=to_chord_idxs([1, 3])
)

ALL_CHORDS = [CHORD_I, CHORD_ii, CHORD_iii, CHORD_IV, CHORD_V, CHORD_vi, CHORD_vii]

class ChordProgression:
    """Generates dynamic chord progressions"""
    @staticmethod
    def generate(length: int) -> List[Chord] | None:
        """Generate a chord progression of given length"""
        if length < 2:
            return None

        progression = []
        current_chord = random.choice(ALL_CHORDS)

        for _ in range(length):
            progression.append(Chord(
                degree=current_chord.degree,
                intervals=current_chord.intervals.copy(),
                next_idxs=current_chord.next_idxs.copy()
            ))

            next_idx = current_chord.get_next_chord_idx()
            current_chord = ALL_CHORDS[next_idx]

        return progression

INTERVAL_WEIGHTS = [0.10, 0.30, 0.20, 0.15, 0.15, 0.025, 0.025, 0.05]

class AudioComposer:
    def __init__(self, progression_length: int = 4):
        """Initialize with a generated chord progression."""
        self.progression = ChordProgression.generate(progression_length)
        self.current_chord_idx = 0

        self.root_notes = ["C", "Dsharp", "Fsharp", "A"]
        self.current_root = random.choice(self.root_notes)

        self.voicing_size = 5

    @property
    def current_chord(self) -> Chord:
        """Get the current chord we're on"""
        return self.progression[self.current_chord_idx]

    def get_next_chord(self) -> Chord:
        """Move to the next chord in the progression."""
        self.current_chord_idx = (self.current_chord_idx + 1) % len(self.progression)

        if random.random() < 0.1:
            self.current_root = random.choice(self.root_notes)

        return self.current_chord

    def get_chord_notes(self, root: str, octave: int, randomize_voicing: bool = True) -> List[str]:
        """
        Get the note names for the current chord.

        Args:
            root: Root note name (e.g., "C", "Fsharp")
            octave: Base octave to build from
            randomize_voicing: If True, shuffles the voicing each time

        Returns:
            List of note names like ["C3", "E3", "G4", "B4"]
        """
        semitones_map = {
            "C": 0, "Csharp": 1, "D": 2, "Dsharp": 3,
            "E": 4, "F": 5, "Fsharp": 6, "G": 7,
            "Gsharp": 8, "A": 9, "Asharp": 10, "B": 11
        }
        rev_map = {v: k for k, v in semitones_map.items()}

        root_val = semitones_map.get(root)
        if root_val is None:
            raise ValueError(f"Invalid root note: {root}")

        if randomize_voicing:
            intervals = self.current_chord.generate_voicing(self.voicing_size)

        else:
            intervals = self.current_chord.intervals[:self.voicing_size]

        chord_root_offset = self.current_chord.semitone_dist

        notes = []
        for interval in intervals:
            total = root_val + chord_root_offset + interval
            oct_offset = total // 12
            note_val = total % 12
            note_name = rev_map[note_val]
            final_octave = octave + oct_offset

            if final_octave < 1 or final_octave > 6:
                continue

            notes.append(f"{note_name}{final_octave}")

        return notes

    def regenerate_progression(self, length: int = 4):
        """Generate a whole new progression"""
        self.progression = ChordProgression.generate(length)
        self.current_chord_idx = 0

    def set_key(self, root: str):
        """Change the key center"""
        semitones_map = {
            "C": 0, "Csharp": 1, "D": 2, "Dsharp": 3,
            "E": 4, "F": 5, "Fsharp": 6, "G": 7,
            "Gsharp": 8, "A": 9, "Asharp": 10, "B": 11
        }

        if root not in semitones_map:
            raise ValueError(f"Invalid key: {root}")
        self.current_root = root

    def set_voicing_size(self, size: int):
        """Change how thicc your chords are (3-7 notes)"""
        self.voicing_size = max(3, min(7, size))

    def get_bass_note(self, octave: int = 2) -> str:
        """Get just the root note for basslines."""
        semitones_map = {
            "C": 0, "Csharp": 1, "D": 2, "Dsharp": 3,
            "E": 4, "F": 5, "Fsharp": 6, "G": 7,
            "Gsharp": 8, "A": 9, "Asharp": 10, "B": 11
        }
        rev_map = {v: k for k, v in semitones_map.items()}

        root_val = semitones_map[self.current_root]
        chord_offset = self.current_chord.semitone_dist

        total = root_val + chord_offset
        note_name = rev_map[total % 12]
        final_octave = octave + (total // 12)

        return f"{note_name}{final_octave}"

    def get_progression_info(self) -> dict:
        """Get info about current progression"""
        return {
            "length": len(self.progression),
            "current_idx": self.current_chord_idx,
            "current_degree": self.current_chord.degree,
            "key": self.current_root,
            "voicing_size": self.voicing_size,
            "chord_sequence": [c.degree for c in self.progression]
        }

class MelodicGenerator:
    def __init__(self, composer: 'AudioComposer'):
        self.composer = composer

    def generate_melody_notes(self, num_notes: int, octave: int, use_weights: bool = True) -> List[str]:
        mode = self.composer.current_chord.generate_mode()
        root_val = self._get_root_semitone()
        chord_offset = self.composer.current_chord.semitone_dist

        melody = []
        for _ in range(num_notes):
            if use_weights:
                interval = np.random.choice(mode, p=self._normalize_weights(len(mode)))
            else:
                interval = random.choice(mode)

            total = root_val + chord_offset + interval
            note_name = self._semitone_to_note(total % 12)
            oct = octave + (total // 12)

            if 1 <= oct <= 6:
                melody.append(f"{note_name}{oct}")

        return melody

    @staticmethod
    def _normalize_weights(length: int) -> List[float]:
        """Normalize interval weights to match the mode length"""
        weights = INTERVAL_WEIGHTS[:length]
        total = sum(weights)
        return [w / total for w in weights]

    def _get_root_semitone(self) -> int:
        semitones_map = {
            "C": 0, "Csharp": 1, "D": 2, "Dsharp": 3,
            "E": 4, "F": 5, "Fsharp": 6, "G": 7,
            "Gsharp": 8, "A": 9, "Asharp": 10, "B": 11
        }
        return semitones_map[self.composer.current_root]

    @staticmethod
    def _semitone_to_note(semitone: int) -> str:
        notes = ["C", "Csharp", "D", "Dsharp", "E", "F",
                 "Fsharp", "G", "Gsharp", "A", "Asharp", "B"]
        return notes[semitone]

