"""Procedural sprites drawn with PicoGraphics primitives (screen coords)."""
import math
from .hw import display
from .gfx import pen, shade, HUD, WHITE, BLACK, GOLD, JADE, JADE_D, RED, CREAM, ORANGE, PURPLE, PINK

FLUFF_COLOURS = (
    (255, 182, 193), (90, 200, 255), (152, 251, 152), (210, 200, 255),
    (255, 150, 100), (255, 236, 90), (221, 160, 221), (60, 200, 190),
)
FLUFF_NAMES = ("Pastel Pink", "Electric Blue", "Mint Green", "Lavender",
               "Coral Orange", "Sunshine Yellow", "Bubblegum Purple", "Seafoam Teal")

_ARCS = {}


def _arc(cx, cy, r0, r1, a0, a1, n=6):
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((int(cx + r1 * math.cos(a)), int(cy + r1 * math.sin(a))))
    for i in range(n, -1, -1):
        a = a0 + (a1 - a0) * i / n
        pts.append((int(cx + r0 * math.cos(a)), int(cy + r0 * math.sin(a))))
    return pts


def _arc_template(d, face, f):
    k = (d, face, f)
    a = _ARCS.get(k)
    if a is None:
        grow = (8 - f) / 4.0
        if d == 0:
            mid = 0.0 if face > 0 else math.pi
            span = 1.1 + 0.35 * grow
        elif d == 1:
            mid, span = -math.pi / 2, 1.2 + 0.3 * grow
        else:
            mid, span = math.pi / 2, 1.2 + 0.3 * grow
        a = (_arc(0, 0, 9, 17, mid - span, mid + span), _arc(0, 0, 13, 17, mid - span * 0.8, mid + span * 0.8))
        _ARCS[k] = a
    return a


class FluffSkin:
    def __init__(self, idx):
        self.set(idx)

    def set(self, idx):
        self.idx = idx % len(FLUFF_COLOURS)
        c = FLUFF_COLOURS[self.idx]
        self.body = pen(*c)
        self.dark = pen(*shade(c, 0.7))
        self.light = pen(*shade(c, 1.2))


def draw_fluff(skin, x, y, face, anim, ground, vy, wet=False, scale=1, blink=False):
    """x, y = top-left of 10x14 hitbox in screen coords."""
    s = scale
    cx = int(x + 5 * s)
    by = int(y + 9 * s)
    bob = 0
    if ground and abs(vy) < 0.1:
        bob = 1 if (anim // 6) & 1 else 0
    if wet:
        bob = int(math.sin(anim * 0.2) * 1.5)
    by += bob
    hx = cx + face * s
    hy = by - 6 * s
    ear_lift = 2 if vy > 2 else 0
    rect = display.rectangle
    circ = display.circle
    display.set_pen(skin.dark)
    rect(hx - face * 3 * s - 1, hy - (11 + ear_lift) * s, 3 * s, 8 * s)
    if not ground and vy < -1:
        rect(cx - 4 * s, by + 3 * s, 3 * s, 3 * s)
        rect(cx + 1 * s, by + 3 * s, 3 * s, 3 * s)
    else:
        step = (anim // 3) & 3 if ground and abs(vy) < 0.1 else 0
        o = (0, 1, 0, -1)[step] if ground else 0
        rect(cx - 4 * s, by + 3 * s + o, 3 * s, 4 * s - o)
        rect(cx + 1 * s, by + 3 * s - o, 3 * s, 4 * s + o)
    display.set_pen(skin.body)
    circ(cx, by, 6 * s)
    circ(hx, hy, 5 * s)
    rect(hx + face * 1 * s - 1, hy - (12 + ear_lift) * s, 3 * s, 9 * s)
    display.set_pen(skin.light)
    circ(cx - face * 2 * s, by - 2 * s, 2 * s)
    display.set_pen(pen(255, 210, 220))
    rect(hx + face * 1 * s, hy - (10 + ear_lift) * s, 1 * s, 5 * s)
    # quetzal feather headband
    display.set_pen(pen(40, 200, 120))
    rect(hx - 5 * s, hy - 3 * s, 10 * s, 2 * s)
    display.set_pen(pen(30, 170, 90))
    display.triangle(hx - face * 4 * s, hy - 3 * s, hx - face * 10 * s, hy - 9 * s, hx - face * 7 * s, hy - 2 * s)
    display.set_pen(RED)
    display.pixel(hx - face * 4 * s, hy - 2 * s)
    # eyes
    ex = hx + face * 2 * s
    if blink:
        display.set_pen(BLACK)
        rect(ex - 2 * s, hy, 4 * s, 1 * s)
    else:
        display.set_pen(WHITE)
        circ(ex - face * 2 * s, hy, 2 * s)
        circ(ex + face * 2 * s, hy, 2 * s)
        display.set_pen(BLACK)
        circ(ex - face * 2 * s + face * s, hy, 1 * s)
        circ(ex + face * 2 * s + face * s, hy, 1 * s)
    display.set_pen(pen(255, 110, 140))
    display.pixel(ex + face * 4 * s, hy + 2 * s)


def draw_slash(px, py, d, face, f, col=None):
    """Crescent slash centred on the player."""
    outer, inner = _arc_template(d, face, f)
    cx = int(px + 5)
    cy = int(py + 7)
    display.set_pen(col or CREAM)
    display.polygon([(cx + a, cy + b) for a, b in outer])
    display.set_pen(WHITE)
    display.polygon([(cx + a, cy + b) for a, b in inner])


def draw_trail(skin, trail):
    display.set_pen(skin.dark)
    for i, (x, y) in enumerate(trail):
        display.circle(int(x + 5), int(y + 9 + HUD), 3 + i)


def draw_charge(x, y, t, full):
    cx, cy = int(x + 5), int(y + 7)
    if full:
        display.set_pen(GOLD if (t >> 1) & 1 else WHITE)
        for a in range(6):
            ang = t * 0.3 + a * 1.047
            display.pixel(cx + int(12 * math.cos(ang)), cy + int(12 * math.sin(ang)))
            display.pixel(cx + int(13 * math.cos(ang)), cy + int(13 * math.sin(ang)))
    else:
        display.set_pen(pen(255, 230, 140))
        ang = t * 0.5
        display.pixel(cx + int(9 * math.cos(ang)), cy + int(9 * math.sin(ang)))


# --- enemies -----------------------------------------------------------------
def draw_enemy(e, t):
    x = int(e.x)
    y = int(e.y) + HUD
    k = e.kind
    flash = e.flash > 0
    rect = display.rectangle
    circ = display.circle
    f = e.face
    if k == "frog":
        display.set_pen(WHITE if flash else pen(40, 120, 255))
        circ(x + 6, y + 6, 6)
        rect(x, y + 5, 12, 5)
        display.set_pen(BLACK)
        rect(x + 3, y + 7, 2, 2)
        rect(x + 8, y + 4, 2, 2)
        display.set_pen(pen(255, 160, 30))
        if e.vy < 0:
            rect(x - 2, y + 9, 4, 2)
            rect(x + 10, y + 9, 4, 2)
        else:
            rect(x, y + 10, 3, 2)
            rect(x + 9, y + 10, 3, 2)
        display.set_pen(WHITE)
        circ(x + 6 + f * 3, y + 1, 2)
        display.set_pen(BLACK)
        display.pixel(x + 6 + f * 4, y + 1)
    elif k == "snake":
        body = WHITE if flash else pen(210, 180, 40)
        band = pen(90, 60, 20)
        for i in range(4):
            sx = x + 7 - f * (i * 4) + (2 if f > 0 else -2)
            sy = y + 6 + int(2 * math.sin(t * 0.3 + i))
            display.set_pen(body if i & 1 == 0 else band)
            circ(sx, sy, 3)
        hx = x + 7 + f * 5
        display.set_pen(body)
        circ(hx, y + 5, 3)
        display.set_pen(BLACK)
        display.pixel(hx + f, y + 4)
        if (t >> 3) & 1:
            display.set_pen(RED)
            rect(hx + f * 3, y + 6, f * 3 if f > 0 else 3, 1)
    elif k == "bat":
        flap = (t >> 2) & 1
        display.set_pen(WHITE if flash else pen(100, 70, 130))
        circ(x + 6, y + 5, 3)
        wy = y + (1 if flap else 7)
        display.triangle(x + 4, y + 5, x - 3, wy, x + 2, y + 8)
        display.triangle(x + 8, y + 5, x + 15, wy, x + 10, y + 8)
        display.set_pen(RED)
        display.pixel(x + 5, y + 4)
        display.pixel(x + 7, y + 4)
    elif k == "eel":
        body = WHITE if flash else pen(60, 170, 140)
        display.set_pen(body)
        for i in range(3):
            circ(x + 7 - f * (i * 5 - 3), y + 4 + int(math.sin(t * 0.3 + i) * 1.5), 3 - (i == 2))
        display.triangle(x + 7 - f * 12, y + 4, x + 7 - f * 17, y, x + 7 - f * 17, y + 8)
        display.set_pen(pen(255, 230, 60))
        display.pixel(x + 7 + f * 4, y + 3)
    elif k == "warrior":
        wind = e.state == 1
        display.set_pen(WHITE if flash or (wind and (t >> 1) & 1) else pen(190, 100, 60))
        rect(x + 1, y + 6, 12, 14)
        display.set_pen(pen(150, 70, 40))
        rect(x + 1, y + 14, 12, 2)
        display.set_pen(GOLD)
        circ(x + 7, y + 4, 5)
        display.set_pen(BLACK)
        rect(x + 4 + f, y + 3, 2, 2)
        rect(x + 8 + f, y + 3, 2, 2)
        rect(x + 5, y + 7, 4, 1)
        display.set_pen(pen(200, 200, 210))
        reach = 14 if e.state == 2 else 6
        sx = x + 7 + f * 4
        display.line(sx, y + 11, sx + f * reach, y + 11)
        display.triangle(sx + f * reach, y + 9, sx + f * reach, y + 13, sx + f * (reach + 5), y + 11)
    elif k == "mask":
        display.set_pen(WHITE if flash else pen(120, 110, 100))
        rect(x, y, 14, 14)
        display.set_pen(pen(80, 70, 60))
        rect(x, y + 12, 14, 2)
        glow = ORANGE if e.timer > 50 else pen(120, 40, 20)
        display.set_pen(glow)
        rect(x + 3, y + 3, 3, 3)
        rect(x + 8, y + 3, 3, 3)
        rect(x + 4 + f, y + 8, 6, 3)
    elif k == "swift":
        flap = (t >> 2) & 1
        display.set_pen(WHITE if flash else pen(200, 210, 230))
        display.triangle(x, y + 5, x + 12, y + 3, x + 12, y + 7)
        display.set_pen(pen(120, 130, 160))
        if flap:
            display.triangle(x + 4, y + 4, x + 9, y + 4, x + 7, y - 4)
        else:
            display.triangle(x + 4, y + 6, x + 9, y + 6, x + 7, y + 12)
        display.set_pen(ORANGE)
        display.pixel(x + (12 if f > 0 else 0), y + 5)
    elif k == "wisp":
        r = 6 + ((t >> 2) & 1)
        display.set_pen(WHITE if flash else pen(120, 60, 200))
        circ(x + 6, y + 6, r)
        display.set_pen(pen(200, 140, 255))
        circ(x + 6, y + 6, r - 3)
        display.set_pen(BLACK)
        rect(x + 3, y + 4, 2, 3)
        rect(x + 8, y + 4, 2, 3)
        rect(x + 5, y + 9, 3, 1)


def draw_lurker(e, t):
    x = int(e.x)
    y = int(e.y) + HUD
    dark = pen(8, 22, 40)
    display.set_pen(dark)
    for i in range(6):
        display.circle(x + 20 - e.face * (i * 7), y + 6 + int(math.sin(t * 0.15 + i) * 2), 7 - i // 2)
    if e.state == 2:
        display.set_pen(pen(200, 40, 40))
        display.triangle(x + 20 + e.face * 6, y + 2, x + 20 + e.face * 16, y + 6, x + 20 + e.face * 6, y + 10)
    display.set_pen(pen(255, 220, 60) if (t >> 4) % 6 else dark)
    display.circle(x + 22 + e.face * 2, y + 3, 1)
    display.circle(x + 18 + e.face * 2, y + 3, 1)


# --- projectiles / pickups -------------------------------------------------
def draw_proj(p, t):
    x = int(p.x)
    y = int(p.y) + HUD
    k = p.kind
    circ = display.circle
    if k == "bolt":
        display.set_pen(GOLD)
        display.rectangle(x - 6, y - 1, 12, 3)
        display.set_pen(WHITE)
        display.rectangle(x - 3, y, 7, 1)
    elif k == "beam":
        display.set_pen(ORANGE)
        circ(x, y, 7)
        display.set_pen(GOLD)
        display.rectangle(x - 14 * (1 if p.vx > 0 else -1) - 6, y - 3, 14, 7)
        circ(x, y, 5)
        display.set_pen(WHITE)
        circ(x, y, 3)
    elif k == "fire":
        display.set_pen(ORANGE)
        circ(x, y, 4)
        display.set_pen(pen(255, 240, 120))
        circ(x, y, 2)
    elif k == "bubble":
        display.set_pen(pen(200, 240, 255))
        circ(x, y, 4)
        display.set_pen(pen(30, 90, 140))
        circ(x, y, 2)
        display.set_pen(WHITE)
        display.pixel(x - 1, y - 2)
    elif k == "feather":
        display.set_pen(pen(230, 230, 255))
        display.line(x - int(p.vx * 2), y - int(p.vy * 2), x, y, 2)
    elif k == "orb":
        display.set_pen(PURPLE)
        circ(x, y, 5)
        display.set_pen(pen(30, 0, 40))
        circ(x, y, 2)
    elif k == "rock":
        display.set_pen(pen(130, 110, 90))
        circ(x, y, 5)
        display.set_pen(pen(80, 64, 50))
        display.rectangle(x - 2, y, 4, 2)
    elif k == "wave":
        display.set_pen(pen(255, 120, 200))
        circ(x, y, 3)
    elif k == "bat":
        flap = (t >> 1) & 1
        display.set_pen(pen(70, 30, 90))
        circ(x, y, 3)
        display.triangle(x - 2, y, x - 9, y + (-4 if flap else 4), x - 2, y + 3)
        display.triangle(x + 2, y, x + 9, y + (-4 if flap else 4), x + 2, y + 3)
        display.set_pen(RED)
        display.pixel(x, y - 1)


def draw_heart(x, y, col, r=3):
    display.set_pen(col)
    display.circle(x - r + 1, y, r)
    display.circle(x + r - 1, y, r)
    display.triangle(x - 2 * r + 1, y + 1, x + 2 * r - 1, y + 1, x, y + 2 * r + 1)


def draw_cacao(x, y, t):
    display.set_pen(pen(150, 80, 30))
    display.circle(x, y, 3)
    display.rectangle(x - 2, y - 4, 4, 8)
    display.set_pen(pen(220, 150, 80))
    display.pixel(x - 1, y - 2)
    if (t + x) % 24 < 3:
        display.set_pen(WHITE)
        display.pixel(x + 2, y - 3)


ITEM_COL = {
    "blade": (60, 40, 70), "pearl": (120, 200, 255), "dash": (255, 190, 50), "feather": (60, 220, 130),
    "spear": (255, 230, 100), "heart": (60, 230, 150), "glyph": (60, 230, 150),
}


def draw_item(kind, x, y, t, big=False):
    s = 2 if big else 1
    bob = int(math.sin(t * 0.12) * 2 * s)
    y += bob
    col = pen(*ITEM_COL.get(kind, (255, 255, 255)))
    if not big:
        display.set_pen(pen(255, 240, 180))
        for a in range(4):
            ang = t * 0.08 + a * 1.57
            display.pixel(x + int(10 * math.cos(ang)), y + int(10 * math.sin(ang)))
    if kind == "heart":
        draw_heart(x, y - 2 * s, JADE, 4 * s)
        display.set_pen(WHITE)
        display.pixel(x - 3 * s, y - 3 * s)
    elif kind == "glyph":
        display.set_pen(JADE_D)
        display.circle(x, y, 8 * s)
        display.set_pen(JADE)
        display.circle(x, y, 6 * s)
        display.set_pen(GOLD)
        display.circle(x, y, 2 * s)
        for a in range(8):
            ang = a * 0.785 + t * 0.05
            display.line(x + int(3 * s * math.cos(ang)), y + int(3 * s * math.sin(ang)),
                         x + int(5 * s * math.cos(ang)), y + int(5 * s * math.sin(ang)))
    elif kind == "blade":
        display.set_pen(pen(140, 100, 60))
        display.rectangle(x - 1 * s, y + 2 * s, 3 * s, 6 * s)
        display.set_pen(col)
        display.triangle(x - 3 * s, y + 3 * s, x + 3 * s, y + 3 * s, x, y - 9 * s)
        display.set_pen(pen(160, 140, 200))
        display.line(x, y - 7 * s, x, y + 2 * s)
    elif kind == "pearl":
        display.set_pen(col)
        display.circle(x, y, 6 * s)
        display.set_pen(WHITE)
        display.circle(x - 2 * s, y - 2 * s, 2 * s)
    elif kind == "dash":
        display.set_pen(col)
        display.circle(x, y, 6 * s)
        display.set_pen(pen(90, 50, 10))
        for dx, dy in ((-3, -2), (2, -3), (0, 2), (3, 2), (-3, 3)):
            display.circle(x + dx * s, y + dy * s, s)
    elif kind == "feather":
        display.set_pen(col)
        display.triangle(x - 2 * s, y + 7 * s, x + 2 * s, y + 7 * s, x + 4 * s, y - 8 * s)
        display.set_pen(RED)
        display.triangle(x - 1 * s, y + 7 * s, x + 1 * s, y + 7 * s, x, y + 2 * s)
    elif kind == "spear":
        display.set_pen(pen(150, 100, 50))
        display.line(x - 7 * s, y + 7 * s, x + 4 * s, y - 4 * s, 2 * s)
        display.set_pen(col)
        display.triangle(x + 2 * s, y - 6 * s, x + 8 * s, y - 8 * s, x + 6 * s, y - 2 * s)
    else:
        display.set_pen(col)
        display.circle(x, y, 5 * s)


# --- spirits -----------------------------------------------------------------
def draw_npc(kind, x, y, t, talking=False):
    """x, y = marker tile top-left (screen)."""
    circ = display.circle
    rect = display.rectangle
    if kind == "ceiba":
        glow = pen(140, 255, 170) if (t >> 4) & 1 else pen(110, 230, 150)
        display.set_pen(glow)
        circ(x + 6, y - 20, 2)
        circ(x + 14, y - 20, 2)
        display.set_pen(pen(70, 50, 36))
        rect(x + 6, y - 13, 9, 2)
        if talking and (t >> 2) & 1:
            rect(x + 8, y - 12, 5, 3)
        for i in range(3):
            a = t * 0.04 + i * 2.1
            display.set_pen(pen(120, 230, 120))
            circ(x + 10 + int(18 * math.cos(a)), y - 10 + int(10 * math.sin(a)), 1)
    elif kind == "ek":
        display.set_pen(pen(150, 90, 40))
        rect(x - 4, y + 1, 12, 13)
        display.set_pen(pen(90, 160, 200))
        circ(x + 9, y + 8, 6)
        display.set_pen(pen(210, 150, 100))
        circ(x + 10, y + 3, 4)
        display.set_pen(pen(200, 60, 60))
        rect(x + 4, y - 3, 12, 3)
        rect(x + 7, y - 6, 6, 3)
        display.set_pen(BLACK)
        display.pixel(x + 11, y + 2)
        display.set_pen(pen(150, 80, 30))
        circ(x - 2, y - 1, 3)
    elif kind == "chaac":
        hover = int(math.sin(t * 0.08) * 3)
        yy = y - 10 + hover
        display.set_pen(pen(40, 110, 200))
        rect(x + 2, yy + 8, 12, 16)
        display.set_pen(pen(80, 170, 240))
        circ(x + 8, yy + 4, 7)
        display.triangle(x + 12, yy + 2, x + 22, yy - 2, x + 13, yy + 6)
        display.set_pen(WHITE)
        circ(x + 9, yy + 2, 2)
        display.set_pen(BLACK)
        display.pixel(x + 10, yy + 2)
        display.set_pen(GOLD)
        rect(x + 1, yy - 4, 14, 3)
        display.set_pen(pen(150, 210, 255))
        for i in range(4):
            dx = (t * 2 + i * 23) % 40 - 12
            dy = (t * 3 + i * 17) % 30
            display.pixel(x + dx, yy - 8 + dy)
    elif kind == "balam":
        display.set_pen(pen(230, 170, 50))
        rect(x - 2, y + 4, 18, 10)
        circ(x + 16, y + 2, 6)
        display.triangle(x + 11, y - 2, x + 14, y - 8, x + 16, y - 2)
        display.triangle(x + 17, y - 2, x + 20, y - 8, x + 21, y - 1)
        display.set_pen(pen(90, 50, 10))
        for dx, dy in ((0, 6), (5, 9), (9, 5), (2, 11), (12, 8)):
            circ(x + dx, y + dy, 1)
        display.set_pen(pen(120, 255, 160))
        display.pixel(x + 15, y + 1)
        display.pixel(x + 19, y + 1)
        display.set_pen(pen(230, 170, 50))
        tail = int(math.sin(t * 0.1) * 4)
        display.line(x - 2, y + 6, x - 9, y + tail)
    elif kind == "witz":
        stone = pen(110, 110, 125)
        display.set_pen(pen(70, 70, 82))
        rect(x - 18, y - 40, 52, 56)
        display.set_pen(stone)
        rect(x - 14, y - 36, 44, 50)
        open_ = talking or (t % 160) > 150
        display.set_pen(pen(40, 40, 50))
        rect(x - 8, y - 24, 12, 3)
        rect(x + 12, y - 24, 12, 3)
        if open_:
            display.set_pen(pen(150, 220, 255))
            rect(x - 5, y - 26, 6, 5)
            rect(x + 15, y - 26, 6, 5)
        display.set_pen(pen(70, 70, 82))
        rect(x + 3, y - 18, 10, 14)
        rect(x - 4, y + 2, 24, 3 if not talking or (t >> 2) & 1 else 6)
        display.set_pen(pen(232, 238, 248))
        rect(x - 18, y - 42, 52, 6)


def draw_portrait(kind, x, y, t, skin=None):
    display.set_pen(pen(20, 18, 30))
    display.rectangle(x, y, 36, 36)
    display.set_pen(pen(90, 80, 60))
    display.rectangle(x, y, 36, 2)
    display.rectangle(x, y + 34, 36, 2)
    cx, cy = x + 18, y + 20
    circ = display.circle
    blink = (t % 90) < 4
    if kind == "fluff" and skin:
        draw_fluff(skin, cx - 10, cy - 10, 1, t, True, 0, scale=2, blink=blink)
        return
    if kind == "ceiba":
        display.set_pen(pen(92, 70, 52))
        circ(cx, cy + 4, 14)
        display.set_pen(pen(40, 120, 60))
        circ(cx - 8, cy - 10, 8)
        circ(cx + 8, cy - 11, 8)
        eye = pen(140, 255, 170)
    elif kind == "ek":
        display.set_pen(pen(210, 150, 100))
        circ(cx, cy + 2, 12)
        display.set_pen(pen(200, 60, 60))
        display.rectangle(cx - 14, cy - 12, 28, 6)
        eye = BLACK
    elif kind == "chaac":
        display.set_pen(pen(80, 170, 240))
        circ(cx, cy + 2, 12)
        display.triangle(cx + 6, cy, cx + 18, cy - 6, cx + 8, cy + 6)
        display.set_pen(GOLD)
        display.rectangle(cx - 12, cy - 14, 24, 4)
        eye = WHITE
    elif kind == "balam":
        display.set_pen(pen(230, 170, 50))
        circ(cx, cy + 2, 12)
        display.triangle(cx - 12, cy - 4, cx - 8, cy - 16, cx - 3, cy - 8)
        display.triangle(cx + 12, cy - 4, cx + 8, cy - 16, cx + 3, cy - 8)
        eye = pen(120, 255, 160)
    elif kind == "witz":
        display.set_pen(pen(110, 110, 125))
        display.rectangle(cx - 13, cy - 12, 26, 26)
        display.set_pen(pen(232, 238, 248))
        display.rectangle(cx - 13, cy - 14, 26, 4)
        eye = pen(150, 220, 255)
    elif kind == "stone":
        display.set_pen(pen(90, 84, 70))
        display.rectangle(cx - 9, cy - 14, 18, 28)
        display.set_pen(pen(50, 44, 36))
        for k in range(4):
            display.rectangle(cx - 6, cy - 9 + k * 5, 12, 2)
        return
    else:
        display.set_pen(pen(60, 20, 70))
        circ(cx, cy, 12)
        display.triangle(cx - 16, cy - 2, cx - 6, cy - 6, cx - 10, cy + 8)
        display.triangle(cx + 16, cy - 2, cx + 6, cy - 6, cx + 10, cy + 8)
        eye = RED
    display.set_pen(eye)
    if blink:
        display.rectangle(cx - 7, cy, 5, 1)
        display.rectangle(cx + 2, cy, 5, 1)
    else:
        circ(cx - 5, cy, 2)
        circ(cx + 5, cy, 2)
