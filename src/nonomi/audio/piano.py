import random
from dataclasses import dataclass
from typing import List, Optional, Any

MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]
NOTE_TO_SEMITONE: dict[str, int] = {
    "C": 0,
    "Csharp": 1,
    "D": 2,
    "Dsharp": 3,
    "E": 4,
    "F": 5,
    "Fsharp": 6,
    "G": 7,
    "Gsharp": 8,
    "A": 9,
    "Asharp": 10,
    "B": 11,
}
SEMITONE_TO_NOTE: dict[int, str] = {v: k for k, v in NOTE_TO_SEMITONE.items()}

ALL_KEYS = list(NOTE_TO_SEMITONE.keys())
FIVE_TO_FIVE = [-5, -3, -1, 0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19]
INTERVAL_WEIGHTS = [0.10, 0.30, 0.20, 0.15, 0.15, 0.025, 0.025, 0.05]

def semitone_to_note_name(semitone: int) -> str:
    return SEMITONE_TO_NOTE[semitone % 12]

def note_name_to_semitone(note: str) -> int:
    if note not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unknown note: '{note}'")
    return NOTE_TO_SEMITONE[note]

def degrees_to_indices(degrees: List[int]) -> List[int]:
    return [d - 1 for d in degrees]

@dataclass
class Chord:
    degree: int
    intervals: List[int]
    next_chord_idxs: List[int]

    @property
    def semitone_dist(self) -> int:
        """Calculate the semitone distance from the root note based on the chord's degree in the major scale."""
        return MAJOR_SCALE_SEMITONES[self.degree - 1]

    def next_chord_idx(self) -> int:
        return random.choice(self.next_chord_idxs)

    def generate_voicing(self, size: int) -> List[int]:
        """Generate a voicing for the chord by shuffling the intervals (except the root) and ensuring they are in ascending order."""
        if size < 3:
            return self.intervals[:3]

        voicing = list(self.intervals[1:size])
        random.shuffle(voicing)
        for i in range(1, len(voicing)):
            while voicing[i] < voicing[i - 1]:
                voicing[i] += 12

        voicing.insert(0, 0)
        return voicing

    def generate_mode(self) -> List[int]:
        """1:1 port of JS Chord.generateMode()"""
        return [(n - 12 if n >= 12 else n) for n in self.intervals]

CHORD_I   = Chord(1, [0,4,7,11,14,17,21], degrees_to_indices([2,3,4,5,6,7]))
CHORD_ii  = Chord(2, [0,3,7,10,14,17,21], degrees_to_indices([3,5,7]))
CHORD_iii = Chord(3, [0,3,7,10,13,17,20], degrees_to_indices([4,6]))
CHORD_IV  = Chord(4, [0,4,7,11,14,18,21], degrees_to_indices([2,5]))
CHORD_V   = Chord(5, [0,4,7,10,14,17,21], degrees_to_indices([1,3,6]))
CHORD_vi  = Chord(6, [0,3,7,10,14,17,20], degrees_to_indices([2,4]))
CHORD_vii = Chord(7, [0,3,6,10,13,17,20], degrees_to_indices([1,3]))

ALL_CHORDS = [CHORD_I, CHORD_ii, CHORD_iii, CHORD_IV, CHORD_V, CHORD_vi, CHORD_vii]

class ChordProgression:
    @staticmethod
    def generate(length: int) -> Optional[List[Chord]]:
        if length < 2:
            return None
        progression = []
        chord = random.choice(ALL_CHORDS)

        for _ in range(length):
            progression.append(Chord(chord.degree, list(chord.intervals), list(chord.next_chord_idxs)))
            chord = ALL_CHORDS[chord.next_chord_idx()]

        return progression

class AudioComposer:
    """Manages progression state."""
    def __init__(self, progression_length: int = 8):
        self.progression: List[Chord] = ChordProgression.generate(progression_length)
        self.progress: int = 0
        self.current_key: str = "C"
        self.scale: List[int] = []
        self.scale_pos: int = 0
        self.melody_density: float = 0.33
        self.melody_off: bool = False
        self.voicing_size: int = 4

    def generate_progression(self):
        """Randomly select a key and generate a new chord progression, resetting progress and melody parameters."""
        self.current_key = random.choice(ALL_KEYS)
        self.progression = ChordProgression.generate(8)
        self.progress = 0

        self.scale = list(FIVE_TO_FIVE)
        self.scale_pos = random.randint(0, len(self.scale) - 1)

    @property
    def current_chord(self) -> Chord:
        return self.progression[self.progress]

    def advance_chord(self):
        """Advance to the next chord, randomise drums at certain points, and adjust melody parameters."""
        next_progress = 0 if self.progress == len(self.progression) - 1 else self.progress + 1

        changes: dict[str, Any] = {"progress": next_progress}
        if self.progress == 4:
            changes["randomize_drums"] = True

        elif self.progress == 0:
            changes["randomize_drums"] = True
            changes["melody_density"] = random.uniform(0.02, 0.05)
            changes["melody_off"] = random.random() < 0.25

        self.progress = next_progress
        return changes

    def get_chord_notes(self, octave: int = 3) -> List[str]:
        """Calculate chord tones based on current key, chord intervals, and octave."""
        root_semitone = note_name_to_semitone(self.current_key) + (octave * 12)
        root_semitone += self.current_chord.semitone_dist
        voicing = self.current_chord.generate_voicing(self.voicing_size)
        notes = []

        for interval in voicing:
            total = root_semitone + interval
            note_name = semitone_to_note_name(total)
            final_octave = total // 12
            if 1 <= final_octave <= 6:
                notes.append(f"{note_name}{final_octave}")

        return notes

    def get_bass_note(self, octave: int = 2) -> str:
        root_semitone = note_name_to_semitone(self.current_key) + (octave * 12)
        root_semitone += self.current_chord.semitone_dist
        note_name = semitone_to_note_name(root_semitone)
        final_octave = root_semitone // 12

        return f"{note_name}{final_octave}"

    def get_melody_note(self) -> Optional[str]:
        """Select a melody note based on the current scale and position, with weighted random step distance."""
        if self.melody_off or not self.scale:
            return None

        if random.random() >= self.melody_density:
            return None

        descend_range = min(self.scale_pos, 7)
        ascend_range  = min(len(self.scale) - 1 - self.scale_pos, 7)

        can_descend = descend_range >= 1
        can_ascend  = ascend_range >= 1

        if can_descend and can_ascend:
            going_up = random.random() > 0.5

        elif can_ascend:
            going_up = True

        elif can_descend:
            going_up = False

        else:
            return None

        max_steps = ascend_range if going_up else descend_range
        step_dist = self._weighted_step(max_steps)

        self.scale_pos += step_dist if going_up else -step_dist
        self.scale_pos = max(0, min(len(self.scale) - 1, self.scale_pos))

        key_semitone = note_name_to_semitone(self.current_key) + (5 * 12)
        total = key_semitone + self.scale[self.scale_pos]
        note_name = semitone_to_note_name(total)

        final_octave = total // 12
        if 1 <= final_octave <= 6:
            return f"{note_name}{final_octave}"

        return None

    @staticmethod
    def _weighted_step(max_steps: int) -> int:
        """Returns a random step distance from 1 to max_steps, weighted by INTERVAL_WEIGHTS."""
        available = INTERVAL_WEIGHTS[1: max_steps + 1]
        if not available:
            return 1

        total = sum(available)
        weights = [w / total for w in available]
        roll = random.random()
        cumulative = 0.0

        for i, w in enumerate(weights):
            cumulative += w
            if roll <= cumulative:
                return i + 1

        return 1
