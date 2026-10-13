"""Pens, palettes and room baking into the background cache."""
import random
from .hw import display, snapshot_bg

HUD = 16
_pens = {}


_pump = [None]


def pump():
    f = _pump[0]
    if f:
        f()


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
INK = pen(10, 10, 22)
RIM = pen(140, 235, 255)

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

# Backdrop scenery is dimmed so sprites and tiles read against it (sky, rock x3, cap, accent, water, plank).
BACKDROP_DIM = (0.55, 0.5, 0.5, 0.5, 0.5, 0.55, 0.8, 0.6, 0.55)

GLOW_ZONES = ("cenote", "dread", "xibalba")

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
        self.vein = pen(*z[6]) if zone in GLOW_ZONES else self.lo
        self.vein_d = pen(*shade(z[6], 0.45)) if zone in GLOW_ZONES else self.lo


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


def bake(room, glyphs=0):
    """Render the static room into the framebuffer and snapshot it as background."""
    from . import backdrops, tiles
    seed = 0
    for ch in room.id:
        seed = seed * 31 + ord(ch)
    random.seed(seed)
    pal = Palette(room.zone)
    backdrops.BACKDROPS[room.zone](room.id, tuple(shade(c, BACKDROP_DIM[i]) for i, c in enumerate(pal.raw)))
    tiles.draw_room(room, pal, glyphs)
    display.set_pen(SHADOW)
    display.rectangle(0, 0, 320, HUD)
    display.set_pen(pen(*shade(pal.raw[5], 0.5)))
    display.rectangle(0, HUD - 1, 320, 1)
    snapshot_bg()
    return pal
