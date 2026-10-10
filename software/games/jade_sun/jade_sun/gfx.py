"""Pens, palettes and room baking into the background cache."""
import math
import random
from .hw import display, snapshot_bg
from .world import (COLS, ROWS, SOLID, T_ROCK, T_CRACK, T_PLANK, T_GRATE, T_SPIKE, T_WATER,
                    T_SEAL, T_RAIN, T_GATE, T_SHUT)

HUD = 16
_pens = {}


def pen(r, g, b):
    k = (r << 16) | (g << 8) | b
    p = _pens.get(k)
    if p is None:
        p = display.create_pen(r, g, b)
        _pens[k] = p
    return p


def mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def shade(c, k):
    return (min(255, int(c[0] * k)), min(255, int(c[1] * k)), min(255, int(c[2] * k)))


BLACK = pen(0, 0, 0)
WHITE = pen(255, 255, 255)
CREAM = pen(255, 244, 214)
GOLD = pen(255, 200, 60)
JADE = pen(60, 230, 150)
JADE_D = pen(20, 120, 80)
RED = pen(235, 50, 60)
PINK = pen(255, 120, 160)
SKY = pen(120, 200, 255)
GREY = pen(120, 120, 130)
DARK = pen(14, 12, 20)
SHADOW = pen(6, 6, 10)
ORANGE = pen(255, 140, 40)
PURPLE = pen(170, 90, 230)
WATER_HI = pen(150, 220, 255)

# zone: sky top, sky bottom, rock, rock hi, rock lo, cap, accent, water, plank
ZONES = {
    "jungle": ((6, 14, 30), (24, 70, 56), (78, 58, 42), (120, 92, 64), (42, 30, 24),
               (70, 160, 70), (240, 200, 90), (24, 80, 120), (128, 86, 48)),
    "cenote": ((4, 10, 26), (8, 44, 64), (52, 64, 76), (96, 116, 128), (24, 30, 40),
               (40, 140, 120), (120, 230, 220), (18, 64, 120), (70, 90, 60)),
    "temple": ((26, 18, 16), (52, 34, 24), (128, 96, 64), (178, 138, 90), (72, 52, 36),
               (200, 160, 80), (240, 190, 70), (30, 70, 110), (110, 100, 90)),
    "dread": ((8, 6, 12), (22, 14, 24), (64, 58, 74), (100, 94, 112), (30, 26, 38),
              (80, 76, 96), (190, 30, 40), (20, 40, 70), (80, 74, 90)),
    "mountain": ((6, 8, 30), (56, 70, 120), (92, 92, 108), (146, 146, 160), (50, 50, 66),
                 (232, 238, 248), (180, 220, 255), (40, 80, 140), (120, 90, 60)),
    "xibalba": ((26, 2, 18), (80, 12, 34), (62, 30, 52), (112, 60, 92), (30, 12, 26),
                (150, 60, 110), (255, 90, 40), (60, 20, 70), (90, 50, 70)),
}

MOOD = {
    "jungle": (10, 70, 30), "cenote": (0, 40, 90), "temple": (90, 50, 0), "dread": (70, 0, 10),
    "mountain": (40, 50, 110), "xibalba": (90, 0, 40),
}


class Palette:
    def __init__(self, zone):
        z = ZONES[zone]
        self.zone = zone
        self.raw = z
        self.rock = pen(*z[2])
        self.hi = pen(*z[3])
        self.lo = pen(*z[4])
        self.cap = pen(*z[5])
        self.cap_d = pen(*shade(z[5], 0.6))
        self.accent = pen(*z[6])
        self.water = pen(*z[7])
        self.water_d = pen(*shade(z[7], 0.7))
        self.plank = pen(*z[8])
        self.plank_hi = pen(*shade(z[8], 1.35))
        self.plank_lo = pen(*shade(z[8], 0.6))
        self.speck = pen(*shade(z[2], 0.8))
        self.speck_hi = pen(*shade(z[2], 1.15))
        self.crack = pen(*shade(z[2], 0.92))


# --- backdrop ----------------------------------------------------------------
def _gradient(top, bot, y0=HUD, y1=240, bands=26):
    h = (y1 - y0) / bands
    for i in range(bands):
        display.set_pen(pen(*mix(top, bot, i / (bands - 1))))
        display.rectangle(0, int(y0 + i * h), 320, int(h) + 2)


def _silhouette(col, base_y, amp, step, seed_off=0):
    display.set_pen(pen(*col))
    x = 0
    y = base_y
    while x < 320:
        ny = base_y - random.randint(0, amp)
        display.triangle(x, 240, x + step, 240, x + step // 2, ny)
        display.rectangle(x, (y + ny) // 2 + 8, step, 240)
        x += step // 2
        y = ny


def _backdrop_jungle(rid, z):
    _gradient(z[0], z[1])
    display.set_pen(pen(200, 255, 220))
    for _ in range(40):
        display.pixel(random.randint(0, 319), random.randint(HUD, 110))
    # distant pyramid
    far = mix(z[0], z[1], 0.55)
    display.set_pen(pen(*far))
    px = random.randint(60, 240)
    for i in range(7):
        w = 90 - i * 12
        display.rectangle(px - w // 2, 150 - i * 9, w, 10)
    display.rectangle(px - 6, 150 - 7 * 9 - 6, 12, 8)
    _silhouette(shade(z[1], 0.55), 175, 40, 60)
    # trunks and canopy
    trunk = pen(*shade(z[1], 0.35))
    leaf = (pen(*shade(z[1], 0.45)), pen(*shade(z[1], 0.6)), pen(*shade(z[5], 0.35)))
    for _ in range(6):
        x = random.randint(0, 310)
        w = random.randint(6, 12)
        display.set_pen(trunk)
        display.rectangle(x, 40, w, 200)
    for _ in range(26):
        display.set_pen(leaf[random.randint(0, 2)])
        display.circle(random.randint(0, 320), random.randint(HUD, 60), random.randint(10, 22))
    vine = pen(*shade(z[5], 0.45))
    display.set_pen(vine)
    for _ in range(14):
        x = random.randint(0, 319)
        ln = random.randint(20, 90)
        display.line(x, HUD, x + random.randint(-4, 4), HUD + ln)
        display.pixel(x + 1, HUD + ln)
    if rid == "A1":
        _ceiba_tree()


def _ceiba_tree():
    bark = pen(92, 70, 52)
    bark_d = pen(60, 44, 34)
    display.set_pen(bark_d)
    display.polygon([(30, 240), (44, 120), (70, 120), (86, 240)])
    display.set_pen(bark)
    display.polygon([(38, 240), (48, 120), (64, 120), (74, 240)])
    display.set_pen(bark_d)
    for i in range(5):
        display.line(50 + i * 3, 140, 46 + i * 5, 205)
    display.triangle(20, 208, 48, 170, 46, 208)
    display.triangle(96, 208, 66, 170, 70, 208)
    for col, r in (((22, 70, 40), 30), ((34, 100, 54), 24), ((60, 150, 70), 14)):
        display.set_pen(pen(*col))
        for cx, cy in ((40, 70), (70, 60), (100, 76), (20, 86), (58, 92)):
            display.circle(cx, cy + 10, r - random.randint(0, 6))
    display.set_pen(pen(255, 230, 120))
    for _ in range(12):
        display.pixel(random.randint(10, 120), random.randint(50, 110))


def _backdrop_cenote(rid, z):
    _gradient(z[0], z[1])
    wall = shade(z[1], 0.75)
    for _ in range(30):
        display.set_pen(pen(*shade(wall, random.randint(70, 110) / 100)))
        display.circle(random.randint(0, 320), random.randint(HUD, 240), random.randint(10, 30))
    display.set_pen(pen(*shade(z[1], 1.25)))
    for _ in range(3):
        x = random.randint(20, 280)
        display.polygon([(x, HUD), (x + 18, HUD), (x + 70, 240), (x + 40, 240)])
    display.set_pen(pen(*shade(z[2], 0.7)))
    for _ in range(10):
        x = random.randint(0, 310)
        display.triangle(x, HUD, x + 12, HUD, x + 6, HUD + random.randint(14, 40))


def _bricks(base, mortar, y0=HUD):
    display.set_pen(pen(*mortar))
    display.rectangle(0, y0, 320, 240 - y0)
    for row in range((240 - y0) // 10 + 1):
        off = (row & 1) * 12
        y = y0 + row * 10
        for col in range(-1, 14):
            display.set_pen(pen(*shade(base, random.randint(85, 110) / 100)))
            display.rectangle(col * 24 + off + 1, y + 1, 22, 8)


def _glyph(x, y, col, s=1):
    display.set_pen(col)
    display.rectangle(x, y, 12 * s, 12 * s)
    display.set_pen(BLACK)
    display.rectangle(x + 2 * s, y + 2 * s, 8 * s, 8 * s)
    display.set_pen(col)
    k = random.randint(0, 3)
    if k == 0:
        display.circle(x + 6 * s, y + 6 * s, 2 * s)
    elif k == 1:
        display.rectangle(x + 4 * s, y + 3 * s, 4 * s, 6 * s)
    elif k == 2:
        display.rectangle(x + 3 * s, y + 5 * s, 6 * s, 2 * s)
        display.rectangle(x + 5 * s, y + 3 * s, 2 * s, 6 * s)
    else:
        display.triangle(x + 3 * s, y + 9 * s, x + 9 * s, y + 9 * s, x + 6 * s, y + 3 * s)


def _backdrop_temple(rid, z, dread=False):
    base = shade(z[1], 1.3)
    _bricks(base, shade(z[1], 0.6))
    col = pen(*shade(z[1], 0.75))
    for x in (40, 150, 260):
        display.set_pen(col)
        display.rectangle(x, HUD, 22, 224)
        display.set_pen(pen(*shade(base, 1.2)))
        display.rectangle(x - 3, HUD, 28, 6)
    g = pen(*(shade(z[6], 0.45) if dread else shade(z[6], 0.4)))
    for _ in range(5):
        _glyph(random.randint(0, 300), random.randint(30, 200), g, random.randint(1, 2))
    if dread:
        display.set_pen(pen(*shade(z[0], 0.6)))
        for _ in range(6):
            x = random.randint(0, 300)
            y = random.randint(30, 200)
            for k in range(3):
                display.line(x + k * 5, y, x + k * 5 + 8, y + 22)
        display.set_pen(pen(120, 10, 20))
        for _ in range(3):
            x = random.randint(20, 300)
            y = random.randint(40, 150)
            display.circle(x, y, 2)
            display.circle(x + 10, y, 2)


def _backdrop_mountain(rid, z):
    _gradient(z[0], z[1])
    for _ in range(90):
        b = random.randint(120, 255)
        display.set_pen(pen(b, b, min(255, b + 20)))
        display.pixel(random.randint(0, 319), random.randint(HUD, 170))
    display.set_pen(pen(240, 240, 220))
    mx, my = random.randint(220, 290), random.randint(36, 60)
    display.circle(mx, my, 12)
    display.set_pen(pen(*z[0]))
    display.circle(mx + 5, my - 3, 10)
    for k, (yb, amp) in enumerate(((170, 70), (200, 50))):
        c = shade(z[1], 0.55 - k * 0.15)
        x = -20
        while x < 340:
            w = random.randint(50, 90)
            h = random.randint(amp // 2, amp)
            display.set_pen(pen(*c))
            display.triangle(x, 240, x + w, 240, x + w // 2, yb - h)
            display.set_pen(pen(*shade(z[5], 0.75 - k * 0.2)))
            display.triangle(x + w // 2 - w // 8, yb - h + h // 4, x + w // 2 + w // 8, yb - h + h // 4, x + w // 2, yb - h)
            x += w - 20
    display.set_pen(pen(*shade(z[1], 1.15)))
    for _ in range(5):
        cx, cy = random.randint(0, 320), random.randint(60, 150)
        for k in range(4):
            display.circle(cx + k * 9, cy + (k & 1) * 3, 8)


def _backdrop_xibalba(rid, z):
    _gradient(z[0], z[1])
    display.set_pen(pen(255, 80, 40))
    sx, sy = random.randint(80, 240), random.randint(50, 80)
    display.circle(sx, sy, 22)
    display.set_pen(pen(10, 0, 8))
    display.circle(sx, sy, 19)
    for _ in range(5):
        x, y = random.randint(0, 300), random.randint(70, 190)
        w = random.randint(26, 60)
        display.set_pen(pen(*shade(z[0], 0.7)))
        display.rectangle(x, y, w, 6)
        display.triangle(x, y + 6, x + w, y + 6, x + w // 2, y + 6 + w // 2)
    display.set_pen(pen(255, 120, 60))
    for _ in range(30):
        display.pixel(random.randint(0, 319), random.randint(HUD, 239))
    g = pen(*shade(z[6], 0.35))
    for _ in range(4):
        _glyph(random.randint(0, 300), random.randint(30, 200), g, 2)


BACKDROPS = {
    "jungle": _backdrop_jungle, "cenote": _backdrop_cenote, "temple": _backdrop_temple,
    "dread": lambda rid, z: _backdrop_temple(rid, z, True), "mountain": _backdrop_mountain,
    "xibalba": _backdrop_xibalba,
}


# --- tiles -----------------------------------------------------------------
def _is_solidish(room, c, r):
    t = room.tile(c, r)
    return SOLID[t] and t != T_SHUT


def _rock(room, pal, c, r, x, y, crack=False):
    rect = display.rectangle
    up = _is_solidish(room, c, r - 1)
    dn = _is_solidish(room, c, r + 1)
    lf = _is_solidish(room, c - 1, r)
    rt = _is_solidish(room, c + 1, r)
    z = pal.zone
    display.set_pen(pal.crack if crack else pal.rock)
    rect(x, y, 16, 16)
    if z in ("temple", "dread"):
        display.set_pen(pal.lo)
        rect(x, y + 7, 16, 1)
        o = 4 if (r & 1) else 11
        rect(x + o, y, 1, 7)
        rect(x + (o + 7) % 16, y + 8, 1, 8)
        if up and dn and lf and rt and random.randint(0, 5) == 0:
            _glyph(x + 2, y + 2, pal.accent if z == "dread" else pal.hi)
    else:
        for _ in range(3):
            display.set_pen(pal.speck if random.randint(0, 1) else pal.speck_hi)
            rect(x + random.randint(0, 13), y + random.randint(0, 13), random.randint(2, 3), 2)
    if crack:
        display.set_pen(pal.lo)
        px, py = x + 3, y + 1
        for _ in range(4):
            nx, ny = x + random.randint(2, 13), py + 4
            display.line(px, py, nx, ny)
            px, py = nx, ny
        display.line(x + 12, y + 2, x + 9, y + 9)
    if not lf:
        display.set_pen(pal.hi)
        rect(x, y, 1, 16)
    if not rt:
        display.set_pen(pal.lo)
        rect(x + 15, y, 1, 16)
    if not dn:
        display.set_pen(pal.lo)
        rect(x, y + 14, 16, 2)
        if z in ("jungle", "cenote") and random.randint(0, 2) == 0:
            display.set_pen(pal.cap_d)
            vx = x + random.randint(2, 13)
            ln = random.randint(4, 14)
            rect(vx, y + 16, 1, ln)
            display.set_pen(pal.cap)
            rect(vx - 1, y + 16 + ln // 2, 3, 2)
            rect(vx, y + 16 + ln, 2, 2)
    if not up:
        display.set_pen(pal.hi)
        rect(x, y, 16, 2)
        if z in ("jungle", "cenote", "mountain", "xibalba"):
            display.set_pen(pal.cap)
            rect(x, y, 16, 3 if z != "mountain" else 4)
            display.set_pen(pal.cap_d)
            rect(x, y + 3, 16, 1)
            display.set_pen(pal.cap)
            for _ in range(3):
                bx = x + random.randint(0, 14)
                rect(bx, y - random.randint(1, 3), 1, 3)
        elif z == "temple":
            display.set_pen(pal.cap)
            rect(x, y, 16, 1)


def _plank(pal, x, y):
    display.set_pen(pal.plank_lo)
    display.rectangle(x, y, 16, 6)
    display.set_pen(pal.plank)
    display.rectangle(x, y, 16, 4)
    display.set_pen(pal.plank_hi)
    display.rectangle(x, y, 16, 1)
    display.set_pen(pal.plank_lo)
    display.rectangle(x + 7, y + 1, 1, 3)
    display.pixel(x + 2, y + 2)
    display.pixel(x + 13, y + 2)


def _grate(pal, x, y):
    display.set_pen(pal.lo)
    display.rectangle(x, y, 16, 4)
    display.set_pen(pal.hi)
    display.rectangle(x, y, 16, 1)
    display.set_pen(pal.lo)
    for k in range(0, 16, 4):
        display.rectangle(x + k + 1, y + 4, 2, 10)
    display.rectangle(x, y + 12, 16, 2)


def _spike(x, y):
    for k in range(3):
        bx = x + k * 5 + 1
        display.set_pen(pen(40, 36, 56))
        display.triangle(bx, y + 16, bx + 5, y + 16, bx + 2, y + 5)
        display.set_pen(pen(170, 170, 200))
        display.line(bx + 2, y + 5, bx + 2, y + 14)


def _water(pal, x, y, r):
    k = max(0.55, 1.0 - r * 0.04)
    display.set_pen(pen(*shade(pal.raw[7], k)))
    display.rectangle(x, y, 16, 16)
    display.set_pen(pen(*shade(pal.raw[7], k * 1.35)))
    for _ in range(2):
        display.rectangle(x + random.randint(0, 10), y + random.randint(0, 15), random.randint(3, 6), 1)


def _seal(x, y):
    display.set_pen(pen(150, 110, 40))
    display.rectangle(x, y, 16, 16)
    display.set_pen(pen(90, 60, 20))
    display.rectangle(x, y, 16, 1)
    display.rectangle(x, y + 15, 16, 1)
    display.set_pen(GOLD)
    display.circle(x + 8, y + 8, 4)
    for a in range(8):
        ang = a * 0.785
        display.line(x + 8, y + 8, x + 8 + int(7 * math.cos(ang)), y + 8 + int(7 * math.sin(ang)))
    display.set_pen(pen(255, 240, 160))
    display.pixel(x + 7, y + 7)


def _rain(x, y):
    display.set_pen(pen(60, 90, 120))
    display.rectangle(x, y, 16, 16)
    display.set_pen(pen(30, 50, 70))
    display.rectangle(x + 15, y, 1, 16)
    display.rectangle(x, y + 15, 16, 1)
    display.set_pen(pen(140, 200, 255))
    display.circle(x + 8, y + 10, 3)
    display.triangle(x + 5, y + 9, x + 11, y + 9, x + 8, y + 3)


def _gate(x, y, c, lit):
    display.set_pen(pen(70, 30, 100))
    display.rectangle(x, y, 16, 16)
    display.set_pen(pen(130, 70, 170))
    display.rectangle(x, y, 16, 2)
    for k in range(2):
        idx = (c % 2) * 2 + k
        display.set_pen(JADE if lit > idx else pen(30, 10, 40))
        display.circle(x + 4 + k * 8, y + 9, 3)


def _shut(x, y):
    display.set_pen(pen(40, 34, 30))
    display.rectangle(x, y, 16, 16)
    display.set_pen(pen(110, 100, 90))
    for k in range(0, 16, 5):
        display.rectangle(x + k + 1, y, 3, 16)
    display.set_pen(pen(200, 40, 40))
    display.rectangle(x + 6, y + 6, 4, 4)


def _shrine_base(x, y):
    display.set_pen(pen(70, 70, 80))
    display.rectangle(x - 10, y + 6, 20, 10)
    display.set_pen(pen(120, 120, 130))
    display.rectangle(x - 12, y + 4, 24, 3)
    display.set_pen(pen(40, 40, 50))
    display.rectangle(x - 6, y + 9, 12, 2)
    display.set_pen(JADE_D)
    display.rectangle(x - 3, y - 2, 6, 6)


def _stele(x, y):
    display.set_pen(pen(90, 84, 70))
    display.rectangle(x + 3, y + 1, 10, 15)
    display.set_pen(pen(140, 130, 110))
    display.rectangle(x + 3, y + 1, 10, 2)
    display.set_pen(pen(50, 44, 36))
    for k in range(3):
        display.rectangle(x + 5, y + 5 + k * 3, 6, 1)


def _torch(x, y):
    display.set_pen(pen(60, 40, 30))
    display.rectangle(x + 6, y + 8, 4, 8)
    display.set_pen(pen(120, 90, 50))
    display.rectangle(x + 4, y + 6, 8, 3)


def bake(room, glyphs=0):
    """Render the static room into the framebuffer and snapshot it as background."""
    rid = room.id
    seed = 0
    for ch in rid:
        seed = seed * 31 + ord(ch)
    random.seed(seed)
    pal = Palette(room.zone)
    z = pal.raw
    BACKDROPS[room.zone](rid, z)
    t = room.t
    for r in range(ROWS):
        y = HUD + r * 16
        for c in range(COLS):
            k = t[r * COLS + c]
            if k == 0:
                continue
            x = c * 16
            if k == T_ROCK:
                _rock(room, pal, c, r, x, y)
            elif k == T_CRACK:
                _rock(room, pal, c, r, x, y, True)
            elif k == T_WATER:
                _water(pal, x, y, r)
            elif k == T_PLANK:
                _plank(pal, x, y)
            elif k == T_GRATE:
                _grate(pal, x, y)
            elif k == T_SPIKE:
                _spike(x, y)
            elif k == T_SEAL:
                _seal(x, y)
            elif k == T_RAIN:
                _rain(x, y)
            elif k == T_GATE:
                _gate(x, y, c, glyphs)
            elif k == T_SHUT:
                _shut(x, y)
    for ch, c, r in room.spawns:
        x, y = c * 16, HUD + r * 16
        if ch == "P":
            _shrine_base(x + 8, y)
        elif ch == "L":
            _stele(x, y)
        elif ch == "T":
            _torch(x, y)
    display.set_pen(SHADOW)
    display.rectangle(0, 0, 320, HUD)
    display.set_pen(pen(*shade(z[5], 0.5)))
    display.rectangle(0, HUD - 1, 320, 1)
    snapshot_bg()
    return pal
