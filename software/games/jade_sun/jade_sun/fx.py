"""Particles, floating text, shake, hit-stop, ambient weather."""
import math
import random
from .hw import display
from .gfx import pen, HUD, WHITE, GOLD

_MAX = 90


class FX:
    def __init__(self):
        self.parts = []
        self.texts = []
        self.shake = 0
        self.stop = 0
        self.flash = 0
        self.flash_pen = WHITE
        self.amb = []
        self.amb_kind = None

    def clear(self):
        self.parts = []
        self.texts = []

    def burst(self, x, y, col, n=10, speed=3.0, life=18, grav=0.15, size=2):
        p = pen(*col) if isinstance(col, tuple) else col
        parts = self.parts
        for _ in range(n):
            if len(parts) >= _MAX:
                parts.pop(0)
            a = random.random() * 6.283
            s = speed * (0.4 + random.random() * 0.8)
            parts.append([x, y, math.cos(a) * s, math.sin(a) * s - 1, life + random.randint(-4, 4), p, grav, size])

    def ring(self, x, y, col, n=12, speed=4.0, life=14):
        p = pen(*col) if isinstance(col, tuple) else col
        for i in range(n):
            a = i * 6.283 / n
            self.parts.append([x, y, math.cos(a) * speed, math.sin(a) * speed, life, p, 0.0, 2])

    def text(self, x, y, s, col=GOLD, life=30, scale=1):
        if isinstance(col, tuple):
            col = pen(*col)
        self.texts.append([x, y, s, col, life, scale])

    def kick(self, shake=4, stop=0):
        self.shake = max(self.shake, shake)
        self.stop = max(self.stop, stop)

    def white(self, frames=2, col=WHITE):
        self.flash = frames
        self.flash_pen = col

    def offset(self):
        if self.shake <= 0:
            return 0, 0
        self.shake -= 1
        m = 1 + self.shake // 3
        return random.randint(-m, m), random.randint(-m, m)

    def update(self):
        keep = []
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[6]
            p[2] *= 0.96
            p[4] -= 1
            if p[4] > 0:
                keep.append(p)
        self.parts = keep
        tk = []
        for t in self.texts:
            t[1] -= 0.6
            t[4] -= 1
            if t[4] > 0:
                tk.append(t)
        self.texts = tk

    def draw_screen(self):
        self.draw(0)

    def draw(self, oy=HUD):
        rect = display.rectangle
        for p in self.parts:
            display.set_pen(p[5])
            s = p[7] if p[4] > 6 else 1
            rect(int(p[0]), int(p[1]) + oy, s, s)
        for t in self.texts:
            display.set_pen(0)
            w = display.measure_text(t[2], t[5])
            x = int(t[0] - w // 2)
            y = int(t[1]) + oy
            display.text(t[2], x + 1, y + 1, 320, t[5])
            display.set_pen(t[3])
            display.text(t[2], x, y, 320, t[5])

    # --- ambience ------------------------------------------------------------
    def set_ambience(self, kind, room):
        self.amb_kind = kind
        self.amb = []
        n = {"fireflies": 14, "rain": 26, "bubbles": 10, "dust": 14, "snow": 26, "embers": 18}.get(kind, 0)
        for _ in range(n):
            self.amb.append([random.randint(0, 319), random.randint(0, 223), random.random() * 6.28, 0])
        self.room = room

    def ambience(self, t):
        k = self.amb_kind
        if not k:
            return
        rect = display.rectangle
        amb = self.amb
        if k == "fireflies":
            for a in amb:
                a[2] += 0.05
                a[0] = (a[0] + math.cos(a[2]) * 0.6) % 320
                a[1] = (a[1] + math.sin(a[2] * 1.3) * 0.4) % 224
                if math.sin(a[2] * 3 + a[0]) > -0.2:
                    display.set_pen(pen(200, 255, 120))
                    rect(int(a[0]), int(a[1]) + HUD, 2, 2)
        elif k == "rain":
            display.set_pen(pen(130, 170, 220))
            for a in amb:
                a[0] = (a[0] - 3) % 320
                a[1] += 11
                if a[1] > 224:
                    a[1] = random.randint(-30, 0)
                    a[0] = random.randint(0, 340)
                x, y = int(a[0]), int(a[1]) + HUD
                display.line(x, y, x + 2, y - 7)
        elif k == "bubbles":
            room = self.room
            display.set_pen(pen(170, 230, 255))
            for a in amb:
                a[1] -= 0.7
                a[2] += 0.2
                x = a[0] + math.sin(a[2]) * 1.5
                if a[1] < 0 or not room.water(x, a[1]):
                    a[0] = random.randint(0, 319)
                    a[1] = random.randint(100, 223)
                    if not room.water(a[0], a[1]):
                        a[1] = 999
                    continue
                rect(int(x), int(a[1]) + HUD, 2, 2)
        elif k == "dust":
            display.set_pen(pen(220, 190, 140))
            for a in amb:
                a[2] += 0.02
                a[0] = (a[0] + math.cos(a[2]) * 0.3) % 320
                a[1] = (a[1] + 0.15) % 224
                display.pixel(int(a[0]), int(a[1]) + HUD)
        elif k == "snow":
            display.set_pen(WHITE)
            for a in amb:
                a[2] += 0.05
                a[0] = (a[0] - 1.6 + math.sin(a[2])) % 320
                a[1] = (a[1] + 1.2) % 224
                rect(int(a[0]), int(a[1]) + HUD, 1 + (int(a[2] * 10) & 1), 1)
        elif k == "embers":
            for a in amb:
                a[2] += 0.07
                a[0] = (a[0] + math.sin(a[2]) * 0.5) % 320
                a[1] -= 0.8
                if a[1] < 0:
                    a[1] = 223
                display.set_pen(pen(255, 140, 40) if int(a[2] * 4) & 1 else pen(255, 60, 30))
                rect(int(a[0]), int(a[1]) + HUD, 2, 2)


AMBIENCE = {"jungle": "fireflies", "cenote": "bubbles", "temple": "dust", "dread": "dust",
            "mountain": "snow", "xibalba": "embers"}
