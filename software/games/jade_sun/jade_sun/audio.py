"""Monophonic PWM sequencer: songs with envelope, vibrato, drum hits, SFX."""
import math
import random
from machine import Pin, PWM
import time

_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_freq(tok):
    n = _NAMES[tok[0]]
    i = 1
    if tok[i] == "#":
        n += 1
        i += 1
    elif tok[i] == "b":
        n -= 1
        i += 1
    midi = 12 * (int(tok[i:]) + 1) + n
    return int(440 * 2 ** ((midi - 69) / 12))


def parse(melody):
    """'A4.2 C5.1 r.3' -> [(freq, units), ...]"""
    out = []
    for tok in melody.split():
        name, _, units = tok.partition(".")
        u = int(units) if units else 1
        out.append((0 if name == "r" else note_freq(name), u))
    return out


# name: (frames per unit, melody, drums per unit, volume, vibrato)
SONGS = {
    "intro": (5, "r.6 A3.2 E4.2 A4.2 C5.2 E5.4 D5.2 C5.2 B4.4 A4.2 C5.2 E5.2 A5.6 G5.2 E5.8 "
                 "D5.2 E5.2 G5.2 A5.4 C6.6 B5.2 A5.10",
              "", 0.7, 1),
    "title": (4, "A4.2 C5.2 E5.2 A5.4 G5.2 E5.2 D5.4 E5.2 G5.2 A5.6 r.2 "
                 "C6.2 B5.2 A5.2 G5.4 E5.2 G5.2 A5.4 E5.2 D5.2 C5.6 r.2 "
                 "D5.2 E5.2 G5.2 A5.4 C6.2 D6.2 E6.6 D6.2 C6.2 A5.4 G5.2 A5.8 r.4",
              "k...h...k.k.h...", 1.0, 1),
    "village": (4, "E5.2 G5.1 A5.1 G5.2 E5.2 D5.2 E5.2 C5.4 D5.2 E5.1 G5.1 E5.2 D5.2 C5.2 A4.2 C5.4 "
                   "A4.2 C5.1 D5.1 E5.2 G5.2 A5.2 G5.2 E5.4 D5.2 C5.1 D5.1 E5.2 D5.2 C5.2 A4.2 A4.4 r.2",
                "k.......h.......", 0.8, 1),
    "jungle": (3, "A4.1 C5.1 D5.1 E5.1 G5.2 E5.2 D5.1 E5.1 D5.1 C5.1 A4.2 G4.2 "
                  "A4.1 C5.1 D5.1 E5.1 G5.2 A5.2 C6.2 A5.2 G5.4 "
                  "E5.1 G5.1 A5.1 G5.1 E5.2 D5.2 C5.1 D5.1 E5.1 D5.1 C5.2 A4.2 "
                  "C5.1 D5.1 E5.1 G5.1 A5.2 G5.2 E5.2 D5.2 A4.4",
               "k.h.s.h.k.k.s.h.", 1.0, 0),
    "cenote": (6, "A3.4 r.2 E4.2 r.4 C4.3 D4.1 E4.4 r.6 G3.4 r.2 D4.2 r.4 C4.2 B3.2 A3.6 r.8 "
                  "E4.2 r.2 A4.4 G4.2 E4.2 r.4 D4.3 C4.1 D4.4 r.8",
               "k...............", 0.55, 1),
    "temple": (4, "D4.2 F4.2 A4.2 G#4.2 A4.4 r.2 D5.2 C5.2 A4.2 F4.2 G4.2 A4.6 r.2 "
                  "F4.2 A4.2 D5.2 C#5.2 D5.4 r.2 F5.2 E5.2 D5.2 C5.2 A4.2 D5.6 r.2",
               "k..k..s.k..k..s.", 0.8, 1),
    "dread": (5, "r.6 A2.2 r.8 A#2.2 r.14 A2.2 r.6 E3.1 D#3.1 r.12",
              "k.k.............", 0.6, 0),
    "chase": (2, "A4.1 A#4.1 A4.1 E5.1 A4.1 A#4.1 A4.1 F5.1 A4.1 A#4.1 A4.1 E5.1 D#5.1 E5.1 F5.1 E5.1",
              "k.s.k.s.kks.k.ss", 1.0, 0),
    "mountain": (4, "E5.4 G5.2 A5.2 B5.4 A5.2 G5.2 E5.6 D5.2 E5.8 "
                    "G5.4 A5.2 B5.2 D6.4 B5.2 A5.2 B5.6 G5.2 A5.8 "
                    "B5.2 D6.2 E6.4 D6.2 B5.2 A5.4 G5.2 E5.2 D5.4 E5.8 r.4",
                 "k.......h...h...", 0.75, 1),
    "xibalba": (4, "E4.2 F4.2 G#4.2 A4.2 B4.2 C5.2 B4.4 r.2 A4.2 G#4.2 F4.2 E4.6 r.2 "
                   "E5.2 D5.2 C5.2 B4.2 C5.2 B4.2 G#4.2 A4.2 F4.4 E4.8 r.4",
                "k..s..k.k..s..s.", 0.8, 1),
    "boss": (2, "A4.1 A4.1 C5.1 A4.1 D5.1 A4.1 E5.1 D5.1 C5.1 A4.1 G4.1 A4.1 C5.2 D5.2 "
                "F5.1 F5.1 E5.1 D5.1 E5.2 C5.2 D5.1 C5.1 A4.1 G4.1 A4.4 "
                "E5.1 E5.1 G5.1 E5.1 A5.2 G5.2 E5.1 D5.1 C5.1 D5.1 E5.4 "
                "D5.1 C5.1 A4.1 C5.1 D5.2 E5.2 G4.1 A4.1 G4.1 E4.1 A4.4",
             "k.s.k.s.kks.k.sh", 1.0, 0),
    "final": (2, "E4.1 E5.1 E4.1 D5.1 E4.1 C5.1 E4.1 B4.1 E4.1 F5.1 E4.1 E5.1 E4.1 D5.1 E4.1 C5.1 "
                 "F4.1 F5.1 F4.1 E5.1 F4.1 D5.1 F4.1 C5.1 G#4.1 B4.1 C5.1 D5.1 E5.2 G#5.2 "
                 "A5.2 G#5.1 F5.1 E5.2 D5.1 C5.1 B4.2 C5.1 D5.1 E5.4 "
                 "F5.2 E5.1 D5.1 C5.2 B4.1 A4.1 G#4.2 A4.1 B4.1 E4.4",
              "kkskk.skkksk.kss", 1.0, 0),
    "ending": (4, "C5.2 E5.2 G5.2 C6.4 B5.2 A5.2 G5.4 E5.2 F5.2 G5.6 r.2 "
                  "A5.2 G5.2 F5.2 E5.4 D5.2 E5.2 F5.4 A5.2 G5.2 C6.8 r.2 "
                  "E5.2 G5.2 A5.4 G5.2 E5.2 D5.4 C5.2 D5.2 E5.6 G5.2 C6.8 r.6",
               "k...h...k.k.h...", 0.9, 1),
}

# SFX: list of segments (f0, f1, frames, duty, noise); duty scaled by volume.
SFX = {
    "jump": ((380, 760, 3, 1100, 0),),
    "djump": ((620, 1240, 3, 1100, 0), (1240, 1500, 1, 700, 0)),
    "land": ((140, 80, 1, 900, 0),),
    "slash": ((1800, 500, 3, 900, 1),),
    "hit": ((220, 110, 2, 1600, 1), (900, 600, 1, 1200, 0)),
    "kill": ((523, 523, 1, 1400, 0), (659, 659, 1, 1400, 0), (784, 784, 1, 1400, 0), (1047, 1047, 2, 1400, 0)),
    "hurt": ((600, 150, 5, 1800, 0),),
    "tink": ((2600, 2400, 1, 900, 0),),
    "dash": ((300, 1600, 4, 1000, 1),),
    "bolt": ((1400, 700, 3, 1000, 0),),
    "beam": ((200, 2000, 4, 1600, 0), (2000, 900, 4, 1400, 0)),
    "break": ((300, 60, 6, 2000, 1),),
    "heart": ((880, 880, 2, 1200, 0), (1319, 1319, 3, 1200, 0)),
    "save": ((523, 523, 3, 1100, 0), (659, 659, 3, 1100, 0), (784, 784, 3, 1100, 0),
             (1047, 1047, 6, 1100, 0), (1568, 1568, 6, 700, 0)),
    "blip": ((1200, 1200, 1, 500, 0),),
    "menu": ((900, 900, 1, 800, 0),),
    "select": ((660, 660, 2, 1000, 0), (990, 990, 3, 1000, 0)),
    "door": ((90, 60, 10, 2200, 1), (60, 40, 8, 1600, 1)),
    "roar": ((180, 90, 6, 2400, 1), (140, 70, 10, 2200, 1)),
    "screech": ((2400, 3200, 6, 1400, 0), (3200, 1800, 6, 1400, 0)),
    "thunder": ((120, 40, 4, 2600, 1), (90, 40, 12, 2000, 1), (60, 30, 10, 1400, 1)),
    "drip": ((2200, 900, 2, 500, 0),),
    "heartbeat": ((70, 50, 2, 2600, 0), (0, 0, 3, 0, 0), (65, 45, 2, 2200, 0)),
    "splash": ((900, 200, 4, 900, 1),),
    "bubble": ((600, 1400, 2, 500, 0),),
    "shoot": ((900, 300, 3, 900, 0),),
    "alert": ((1760, 1760, 2, 2000, 0), (0, 0, 1, 0, 0), (1760, 1760, 2, 2000, 0), (0, 0, 1, 0, 0), (2093, 2093, 4, 2000, 0)),
    "drum": ((130, 90, 1, 2400, 1),),
    "boom": ((200, 30, 10, 2800, 1),),
    "charge": ((400, 1400, 18, 500, 0),),
    "gate": ((110, 220, 12, 2400, 0), (220, 440, 12, 2400, 0), (440, 880, 12, 2000, 0)),
}

_SCALE = "C5 D5 E5 G5 A5 C6 D6 E6 G6 A6 C7".split()
CHIME = [note_freq(n) for n in _SCALE]


def tune(notes, unit=3, duty=1300):
    """Build an SFX from a melody string (used for fanfares)."""
    segs = []
    for f, u in parse(notes):
        segs.append((f, f, u * unit, duty if f else 0, 0))
    return tuple(segs)


SFX["item"] = tune("C5.1 E5.1 G5.1 C6.2 r.1 G5.1 C6.1 E6.4 r.1 D6.1 E6.1 G6.6", 3, 1500)
SFX["glyph"] = tune("A4.1 C5.1 E5.1 A5.2 G5.1 A5.1 C6.2 E6.1 D6.1 C6.1 E6.2 A6.8", 3, 1600)
SFX["levelup"] = tune("G5.1 A5.1 B5.1 D6.1 G6.4", 2, 1500)
SFX["death"] = tune("E5.2 D#5.2 D5.2 C#5.6 r.2 A3.8", 3, 1300)
SFX["shop"] = tune("E6.1 G6.1 C7.3", 2, 1100)

VOLUMES = (0.0, 0.15, 1.0, 1.6)


class Audio:
    def __init__(self):
        self.pwm = PWM(Pin(6))
        self.pwm.duty_u16(0)
        self.vol_index = 1
        self.song_name = None
        self.song = None
        self.sfx = None
        self.sfx_prio = 0
        self.seg_i = 0
        self.seg_t = 0
        self.unit_t = 0
        self.note_i = 0
        self.note_t = 0
        self.note_len = 0
        self.note_f = 0
        self.unit_count = 0
        self.t = 0
        self._last_f = -1
        self._last_d = -1
        self.chime_i = 0
        self.chime_t = 0
        self.music_on = True
        self.last_ms = time.ticks_ms()

    def pump(self):
        """Run the 25 fps sequencer for the wall time that passed, so music keeps time
        through slow frames and room bakes (the bake calls this between draw stages)."""
        now = time.ticks_ms()
        n = time.ticks_diff(now, self.last_ms) // 40
        if n <= 0:
            return
        if n > 6:
            n = 6
            self.last_ms = now
        else:
            self.last_ms += n * 40
        while n:
            self.tick()
            n -= 1

    @property
    def vol(self):
        return VOLUMES[self.vol_index]

    def cycle_volume(self):
        self.vol_index = (self.vol_index + 1) % len(VOLUMES)
        return self.vol_index

    def play_song(self, name, restart=False):
        if name == self.song_name and not restart:
            return
        song = None
        if name is not None:
            unit, mel, drums, vol, vib = SONGS[name]
            song = (unit, parse(mel), drums, vol, vib)
        self.song_name = name
        self.song = song
        self.note_i = -1
        self.note_t = 0
        self.unit_count = 0
        self.unit_t = 0

    def sfx_play(self, name, prio=1):
        if self.sfx and prio < self.sfx_prio:
            return
        self.seg_i = 0
        self.seg_t = 0
        self.sfx_prio = prio
        self.sfx = SFX[name]

    def sfx_tone(self, f0, f1, frames, duty=1100, prio=1):
        if self.sfx and prio < self.sfx_prio:
            return
        self.seg_i = 0
        self.seg_t = 0
        self.sfx_prio = prio
        self.sfx = ((f0, f1, frames, duty, 0),)

    def chime(self):
        """Rising pentatonic pickup ladder."""
        if self.chime_t <= 0:
            self.chime_i = 0
        f = CHIME[min(self.chime_i, len(CHIME) - 1)]
        self.chime_i += 1
        self.chime_t = 12
        self.sfx_tone(f, f, 2, 1000, 1)

    def _out(self, f, d):
        if d <= 0 or f < 20:
            if self._last_d != 0:
                self.pwm.duty_u16(0)
                self._last_d = 0
            return
        if f != self._last_f:
            self.pwm.freq(f)
            self._last_f = f
        if d != self._last_d:
            self.pwm.duty_u16(d)
            self._last_d = d

    def tick(self):
        self.t += 1
        if self.chime_t > 0:
            self.chime_t -= 1
        v = self.vol
        if v <= 0:
            self._out(0, 0)
            self._tick_song(False)
            return
        if self.sfx and self.seg_i >= len(self.sfx):
            self.sfx = None
            self.sfx_prio = 0
        if self.sfx:
            f0, f1, n, duty, noise = self.sfx[self.seg_i]
            if noise:
                f = random.randint(min(f0, f1), max(f0, f1) + 1)
            else:
                f = f0 + (f1 - f0) * self.seg_t // max(1, n - 1) if n > 1 else f0
            self._out(f, int(duty * v))
            self.seg_t += 1
            if self.seg_t >= n:
                self.seg_t = 0
                self.seg_i += 1
                if self.seg_i >= len(self.sfx):
                    self.sfx = None
                    self.sfx_prio = 0
            self._tick_song(False)
            return
        self._tick_song(True)

    def _tick_song(self, audible):
        s = self.song
        if not s or not self.music_on:
            if audible:
                self._out(0, 0)
            return
        unit, notes, drums, vol, vib = s
        if self.note_t <= 0:
            self.note_i = (self.note_i + 1) % len(notes)
            self.note_f, u = notes[self.note_i]
            self.note_len = u * unit
            self.note_t = self.note_len
        age = self.note_len - self.note_t
        self.note_t -= 1
        drum = None
        self.unit_t += 1
        if self.unit_t >= unit:
            self.unit_t = 0
            self.unit_count += 1
        if self.unit_t == 0 and drums:
            drum = drums[self.unit_count % len(drums)]
        if not audible:
            return
        v = self.vol * vol
        if drum == "k":
            self._out(random.randint(55, 75), int(2600 * v))
            return
        if drum == "s":
            self._out(random.randint(180, 420), int(1500 * v))
            return
        if drum == "h" and self.note_f == 0:
            self._out(random.randint(5000, 8000), int(260 * v))
            return
        f = self.note_f
        if f == 0:
            self._out(0, 0)
            return
        env = 1.0 if age < 2 else max(0.35, 0.86 ** (age - 1))
        if self.note_t < 1 and self.note_len > 3:
            env *= 0.4
        if vib and age > 4:
            f = int(f * (1 + 0.007 * math.sin(age * 1.3)))
        self._out(f, int(700 * v * env))

    def silence(self):
        self.pwm.duty_u16(0)
        self._last_d = 0
