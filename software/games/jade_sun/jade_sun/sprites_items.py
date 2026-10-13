"""Projectiles, pickups and collectable items.

Low poly: dark underside, mid facet, lit tip, then a glint. Circles only for the
pearl, an eye, or a round projectile core. rig.tri counts as two primitives here
because the display implements triangle via polygon.
"""
from . import rig
from .hw import display
from .gfx import pen, shade, HUD, WHITE, GOLD, JADE, RED, CREAM, ORANGE, PURPLE, PINK, INK


def _pen(rgb, k):
    return pen(*shade(rgb, k))


OBS = pen(60, 40, 70)
OBS_M = pen(120, 85, 145)
OBS_L = pen(190, 160, 220)
WOOD_D = _pen((130, 85, 40), 0.45)
WOOD = pen(165, 115, 60)
WOOD_L = pen(215, 170, 100)
PEARL_D = _pen((120, 200, 255), 0.30)
PEARL = pen(140, 210, 255)
PEARL_L = pen(230, 248, 255)
GOLD_D = _pen((255, 190, 50), 0.38)
GOLD_L = pen(255, 244, 190)
FEA_D = _pen((60, 220, 130), 0.30)
FEA = pen(60, 220, 130)
FEA_L = pen(185, 255, 215)
QUILL = pen(200, 45, 60)
SHAFT = pen(230, 215, 170)
SP_D = pen(110, 70, 30)
SP_M = pen(168, 115, 52)
SP_L = pen(214, 165, 90)
J_D = _pen((60, 230, 150), 0.32)
J_L = pen(205, 255, 230)
SH_D = _pen((90, 240, 170), 0.32)
SH = pen(90, 240, 170)
SH_L = pen(225, 255, 240)
C_D = _pen((120, 62, 22), 0.5)
C_M = pen(156, 86, 34)
C_L = pen(214, 150, 78)
C_STEM = pen(64, 110, 42)
FIRE_D = pen(150, 36, 12)
FIRE_L = pen(255, 228, 80)
BUB_D = pen(14, 48, 78)
BUB = pen(160, 225, 250)
BUB_C = pen(8, 24, 48)
ORB_D = pen(36, 0, 52)
ROCK_D = pen(108, 80, 58)
ROCK = pen(156, 122, 90)
ROCK_L = pen(214, 184, 146)
WAVE_D = pen(160, 24, 100)
WAVE = pen(255, 130, 205)
BAT_D = pen(36, 14, 55)
BAT = pen(78, 38, 100)
BAT_L = pen(145, 95, 165)
VANE = pen(140, 155, 170)
BEAM_D = pen(170, 60, 12)


ITEM_COL = {
    "blade": (60, 40, 70), "pearl": (120, 200, 255), "dash": (255, 190, 50), "feather": (60, 220, 130),
    "spear": (255, 230, 100), "heart": (60, 230, 150), "glyph": (60, 230, 150), "shard": (90, 240, 170),
}


def _t(x, y, s, x0, y0, x1, y1, x2, y2):
    rig.tri(x, y, 1, x0 * s, y0 * s, x1 * s, y1 * s, x2 * s, y2 * s)


def _glint(x, y, t):
    display.set_pen(WHITE)
    display.pixel(x + ((t >> 3) & 1), y)


def _ray(x, y, s, a, r0, r1, w):
    c = rig.cos64(a)
    sn = rig.sin64(a)
    px, py = -sn, c
    rig.tri(x, y, 1,
            int(round((c * r0 + px * w) * s)), int(round((sn * r0 + py * w) * s)),
            int(round((c * r0 - px * w) * s)), int(round((sn * r0 - py * w) * s)),
            int(round(c * r1 * s)), int(round(sn * r1 * s)))


def _arm(x, y, vx, vy, side, ln, w):
    """One blade of a chevron. Two of these leave a gap a single triangle would fill."""
    ad = abs(vx) + abs(vy) or 1
    fx, fy = vx / ad, vy / ad
    nx, ny = -fy * side, fx * side
    display.triangle(int(x + fx * ln), int(y + fy * ln),
                     int(x - fx * 2 + nx * w), int(y - fy * 2 + ny * w),
                     int(x + fx + nx * 1.3), int(y + fy + ny * 1.3))


def draw_heart(x, y, col, r=3):
    """Pickup and HUD heart. r=3 must stay a readable heart on the 16px bar."""
    display.set_pen(INK)
    display.triangle(x - r - 2, y + 1, x + r + 2, y + 1, x, y + (r << 1) + 2)
    display.set_pen(col)
    display.triangle(x - r - 1, y, x + r + 1, y, x, y + (r << 1) + 1)
    display.triangle(x - r - 1, y, x - r + 1, y - r + 1, x, y)
    display.triangle(x + r + 1, y, x + r - 1, y - r + 1, x, y)


def draw_cacao(x, y, t):
    # Tall pod: two triangles make a quad, then a lit cap and a stem.
    display.set_pen(C_D)
    _t(x, y, 1, -2, -2, -2, 4, 2, 4)
    display.set_pen(C_M)
    _t(x, y, 1, -2, -2, 2, -2, 2, 4)
    display.set_pen(C_L)
    _t(x, y, 1, -2, -1, 2, -1, 0, -4)
    display.set_pen(C_STEM)
    _t(x, y, 1, -1, -3, 1, -3, 0, -6)
    display.set_pen(C_D)
    display.line(x, y - 1, x, y + 3)
    _glint(x - 1, y - 2, t)


def _blade(x, y, s, t):
    # Long obsidian blade, small edge teeth, short wrapped grip.
    display.set_pen(OBS)
    _t(x, y, s, 0, -9, 2, 1, 1, 4)
    _t(x, y, s, 0, -9, -2, 1, -1, 4)
    display.set_pen(OBS_M)
    _t(x, y, s, 0, -8, 1, 0, 0, 3)
    _t(x, y, s, 0, -8, -1, 0, 0, 3)
    display.set_pen(OBS_L)
    _t(x, y, s, 0, -8, -1, -4, 0, -1)
    display.set_pen(OBS_L)
    _t(x, y, s, -2, -4, -4, -3, -2, -2)
    _t(x, y, s, -2, -1, -4, 0, -2, 1)
    _t(x, y, s, -2, 2, -4, 3, -2, 4)
    _t(x, y, s, 2, -3, 4, -2, 2, -1)
    _t(x, y, s, 2, 0, 4, 1, 2, 2)
    _t(x, y, s, 2, 2, 4, 3, 2, 4)
    display.set_pen(WOOD_D)
    _t(x, y, s, -1, 8, 1, 8, 1, 5)
    _t(x, y, s, -1, 8, 1, 5, -1, 5)
    display.set_pen(JADE)
    _t(x, y, s, -2, 5, 2, 5, 2, 4)
    _t(x, y, s, -2, 5, 2, 4, -2, 4)
    _glint(x - s, y - 6 * s, t)


def _pearl(x, y, s, t):
    display.set_pen(PEARL_D)
    display.circle(x, y, 6 * s + 1)
    rig.crescent(x, y, 6 * s, 2 * s + 1, PEARL_D, PEARL)
    display.set_pen(PEARL_L)
    display.circle(x - s, y - 2 * s, s + 1)
    j = (t >> 2) & 1
    display.set_pen(WHITE)
    display.circle(x - 2 * s + j, y - 3 * s, 1 if s < 2 else 2)


def _dash(x, y, s, t):
    # Narrow bases and a gap, so the three claws do not fuse into one wedge.
    display.set_pen(GOLD_D)
    _t(x, y, s, -7, 2, -5, -7, -4, 2)
    _t(x, y, s, -1, 2, 0, -9, 2, 2)
    _t(x, y, s, 4, 2, 6, -6, 7, 2)
    display.set_pen(GOLD)
    _t(x, y, s, -6, 0, -5, -7, -4, 1)
    _t(x, y, s, -1, 0, 0, -9, 1, 1)
    _t(x, y, s, 5, 0, 6, -6, 7, 1)
    display.set_pen(GOLD_L)
    _t(x, y, s, -6, -3, -5, -7, -4, -2)
    _t(x, y, s, -1, -4, 0, -9, 1, -3)
    _t(x, y, s, 5, -2, 6, -6, 7, -1)
    _glint(x, y - 8 * s, t)


def _feather(x, y, s, t):
    display.set_pen(FEA_D)
    _t(x, y, s, 1, -8, 4, 0, 1, 6)
    _t(x, y, s, 0, 2, -3, 5, 1, 6)
    display.set_pen(FEA)
    _t(x, y, s, 0, -8, -5, -1, 0, 6)
    _t(x, y, s, -1, -4, -6, -3, -1, -1)
    _t(x, y, s, -1, 0, -5, 2, 0, 3)
    _t(x, y, s, 0, 3, -4, 6, 1, 6)
    _t(x, y, s, 1, -2, 5, 0, 1, 2)
    display.set_pen(FEA_L)
    _t(x, y, s, 0, -8, -3, -4, 2, -3)
    _t(x, y, s, 0, -9, -1, -6, 2, -6)
    display.set_pen(SHAFT)
    _t(x, y, s, 0, -7, -1, 6, 1, 6)
    display.set_pen(QUILL)
    _t(x, y, s, -1, 5, 1, 5, 0, 9)
    _glint(x - 2 * s, y - 5 * s, t)


def _spear(x, y, s, t):
    display.set_pen(SP_D)
    _t(x, y, s, -8, 8, -4, 9, 4, -1)
    _t(x, y, s, -8, 8, 4, -1, 1, -4)
    display.set_pen(SP_M)
    _t(x, y, s, -7, 6, -4, 7, 3, -3)
    _t(x, y, s, -7, 6, 3, -3, 1, -5)
    display.set_pen(SP_L)
    _t(x, y, s, -6, 5, -3, 5, 2, -4)
    display.set_pen(GOLD_D)
    _t(x, y, s, 2, -2, 9, -7, 6, 1)
    display.set_pen(GOLD)
    _t(x, y, s, 3, -4, 8, -8, 5, -2)
    display.set_pen(GOLD_L)
    _t(x, y, s, 4, -5, 7, -8, 6, -4)
    display.set_pen(QUILL)
    _t(x, y, s, -8, 6, -12, 3, -6, 5)
    display.set_pen(GOLD)
    _t(x, y, s, -7, 8, -10, 11, -4, 7)
    display.set_pen(SP_D)
    _t(x, y, s, -6, 6, -8, 11, -3, 8)
    _glint(x + 6 * s, y - 7 * s, t)


def _heart(x, y, s, t):
    # Point first. Gems are the lobe tops, with a gap so the notch stays open.
    display.set_pen(J_D)
    _t(x, y, s, -6, 3, 6, 3, 0, 9)
    _t(x, y, s, -6, 2, -5, -1, -1, 2)
    _t(x, y, s, 6, 2, 5, -1, 1, 2)
    display.set_pen(JADE)
    _t(x, y, s, -5, 2, 5, 2, 0, 8)
    _t(x, y, s, -6, 2, -4, -1, 0, 1)
    _t(x, y, s, 6, 2, 4, -1, 0, 1)
    rig.gem(x - 4 * s, y - 3 * s, 3 * s, J_L, JADE, J_D, 8)
    rig.gem(x + 4 * s, y - 3 * s, 3 * s, J_L, JADE, J_D, 8)
    _glint(x - 5 * s, y - 5 * s, t)


def _glyph(x, y, s, t):
    base = t >> 3
    display.set_pen(J_D)
    _t(x, y, s, -5, -5, 5, -5, 5, 5)
    _t(x, y, s, -5, -5, 5, 5, -5, 5)
    for i in range(4):
        _ray(x, y, s, base + i * 16, 2, 9, 1.7)
    display.set_pen(GOLD)
    for i in range(4):
        _ray(x, y, s, base + i * 16, 3, 7, 0.85)
    rig.gem(x, y, 4 * s, J_L, JADE, J_D, 8)
    display.set_pen(J_D)
    _t(x, y, s, -2, 1, 2, 1, 0, 3)
    display.set_pen(GOLD)
    display.circle(x, y - s, s)
    _glint(x - s, y - 2 * s, t)


def _shard(x, y, s, t):
    display.set_pen(SH_D)
    _t(x, y, s, -1, 4, 4, 3, 2, 0)
    _t(x, y, s, -4, 2, -1, 3, -1, -1)
    display.set_pen(SH)
    _t(x, y, s, -2, 1, 2, 1, -1, -5)
    _t(x, y, s, 0, 0, 5, 2, 2, -2)
    display.set_pen(SH_L)
    _t(x, y, s, -2, -1, 1, -1, -1, -5)
    rig.gem(x + s, y + 2 * s, 2 * s, SH_L, SH, SH_D, 4)
    _glint(x - s, y - 4 * s, t)


def draw_item(kind, x, y, t, big=False):
    s = 2 if big else 1
    y += int(rig.sin64(t) * 2 * s)
    if kind == "blade":
        _blade(x, y, s, t)
    elif kind == "pearl":
        _pearl(x, y, s, t)
    elif kind == "dash":
        _dash(x, y, s, t)
    elif kind == "feather":
        _feather(x, y, s, t)
    elif kind == "spear":
        _spear(x, y, s, t)
    elif kind == "heart":
        _heart(x, y, s, t)
    elif kind == "glyph":
        _glyph(x, y, s, t)
    else:
        _shard(x, y, s, t)


def draw_proj(p, t):
    x = int(p.x)
    y = int(p.y) + HUD
    k = p.kind
    if k == "bolt":
        f = 1 if p.vx > 0 else -1
        display.set_pen(GOLD_D)
        rig.tri(x, y, f, -7, -3, -4, 0, -7, 3)
        display.set_pen(GOLD)
        rig.tri(x, y, f, -5, -1, -5, 1, 4, 0)
        display.set_pen(GOLD_L)
        rig.tri(x, y, f, 2, -2, 2, 2, 8, 0)
        display.set_pen(WHITE)
        display.line(x - f * 3, y, x + f * 4, y)
        display.pixel(x + f * 6, y)
    elif k == "beam":
        f = 1 if p.vx > 0 else -1
        tx = x - 14 if f > 0 else x
        display.set_pen(BEAM_D)
        display.rectangle(tx, y - 3, 14, 6)
        display.set_pen(GOLD)
        display.rectangle(tx, y - 1, 14, 2)
        rig.crescent(x, y, 5, 2, BEAM_D, GOLD)
        display.set_pen(WHITE)
        display.circle(x - f, y - 1, 2)
        display.set_pen(CREAM)
        rig.tri(x, y, f, 3, -3, 8, 0, 3, 3)
    elif k == "fire":
        tip = -6 + int(rig.sin64(t << 2) * 2)
        display.set_pen(FIRE_D)
        display.triangle(x - 3, y + 3, x + 2, y + 2, x - 1, y + tip)
        display.set_pen(ORANGE)
        display.triangle(x + 1, y + 2, x + 5, y + 1, x + 2, y + tip + 2)
        display.set_pen(FIRE_L)
        display.triangle(x - 1, y + 1, x + 1, y, x, y + tip + 3)
        display.set_pen(CREAM)
        display.circle(x, y, 1)
    elif k == "bubble":
        display.set_pen(BUB_D)
        display.circle(x, y, 4)
        rig.crescent(x, y, 3, 2, BUB_D, BUB)
        display.set_pen(BUB_C)
        display.circle(x + 1, y + 1, 1)
        _glint(x - 2, y - 2, t)
    elif k == "feather":
        ad = (p.vx * p.vx + p.vy * p.vy) ** 0.5 or 1
        fx, fy = p.vx / ad, p.vy / ad
        nx, ny = -fy, fx
        display.set_pen(VANE)
        display.triangle(int(x + fx * 7), int(y + fy * 7),
                         int(x - fx * 5 + nx * 4), int(y - fy * 5 + ny * 4),
                         int(x - fx * 2), int(y - fy * 2))
        display.set_pen(WHITE)
        display.triangle(int(x + fx * 7), int(y + fy * 7),
                         int(x - fx * 4 - nx * 3), int(y - fy * 4 - ny * 3),
                         int(x - fx), int(y - fy))
        display.set_pen(GOLD_L)
        display.triangle(int(x + fx * 7), int(y + fy * 7),
                         int(x + fx * 2 + nx * 2), int(y + fy * 2 + ny * 2),
                         int(x + fx * 2 - nx * 2), int(y + fy * 2 - ny * 2))
    elif k == "orb":
        display.set_pen(ORB_D)
        display.circle(x, y, 5)
        rig.crescent(x, y, 4, 2, ORB_D, PURPLE)
        display.set_pen(PINK)
        display.circle(x, y, 2)
        display.set_pen(INK)
        display.pixel(x, y + 1)
        _glint(x - 1, y - 2, t)
    elif k == "rock":
        display.set_pen(ROCK_D)
        display.triangle(x - 5, y + 2, x + 1, y + 1, x - 1, y + 5)
        display.set_pen(ROCK)
        display.triangle(x - 4, y, x, y - 5, x + 4, y - 1)
        display.set_pen(ROCK_D)
        display.triangle(x + 1, y, x + 6, y + 2, x + 2, y + 4)
        display.set_pen(ROCK_L)
        display.triangle(x - 2, y - 1, x + 1, y - 4, x + 1, y)
    elif k == "wave":
        display.set_pen(WAVE_D)
        _arm(x, y, p.vx, p.vy, 1, 5, 4)
        display.set_pen(WAVE)
        _arm(x, y, p.vx, p.vy, -1, 5, 4)
        display.set_pen(WHITE)
        ad = abs(p.vx) + abs(p.vy) or 1
        display.pixel(int(x + p.vx / ad * 4), int(y + p.vy / ad * 4))
    elif k == "bat":
        dy = -5 if (t & 4) == 0 else 4
        display.set_pen(BAT_D)
        display.triangle(x - 1, y, x - 8, y + dy, x - 2, y + 3)
        display.triangle(x + 1, y, x + 8, y + dy, x + 2, y + 3)
        display.set_pen(BAT)
        display.triangle(x, y - 4, x - 3, y + 2, x + 3, y + 2)
        display.set_pen(BAT_L)
        display.triangle(x - 1, y - 1, x + 1, y - 1, x, y + 2)
        display.set_pen(RED)
        display.pixel(x - 1, y - 1)
        display.pixel(x + 1, y - 1)
