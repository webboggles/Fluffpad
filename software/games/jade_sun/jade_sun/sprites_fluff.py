"""La-Fluff-Puff: faceted body, blade slash, dash trail and spear charge.

Template x is forward (+face); mirrored by f. Light stays on -y.
Body and head are the only polygons. Everything else is a triangle.
Slash outer radius stays 17, the original hit reach.
"""
import math
from . import rig
from .hw import display
from .gfx import pen, shade, HUD, WHITE, BLACK, GOLD, JADE, JADE_D, CREAM

FLUFF_COLOURS = (
    (255, 182, 193), (90, 200, 255), (152, 251, 152), (210, 200, 255),
    (255, 150, 100), (255, 236, 90), (221, 160, 221), (60, 200, 190),
)
FLUFF_NAMES = ("Pastel Pink", "Electric Blue", "Mint Green", "Lavender",
               "Coral Orange", "Sunshine Yellow", "Bubblegum Purple", "Seafoam Teal")

# Faceted egg, origin at its centre. Wider in the lower half. +y down.
# The 10x14 hitbox (centre +5, +7) sits inside; the crown and belly round it off.
_EGG = (
    (-3, -8), (0, -9), (3, -8), (5, -5),
    (6, 2), (5, 6), (3, 7), (-3, 7), (-5, 6), (-6, 2), (-5, -5),
)

_EGG_O = (
    (-4, -9), (0, -10), (4, -9), (6, -5),
    (7, 2), (6, 7), (3, 8), (-3, 8), (-6, 7), (-7, 2), (-6, -5),
)

_ARCS = {}
_ANG = [0.0] * 8

OUTLINE = pen(14, 18, 44)
RIM = pen(70, 232, 255)
EYE = pen(80, 236, 255)
EYE_D = pen(30, 150, 200)
BAND = pen(60, 230, 150)
FEATHER_LIT = pen(186, 255, 214)
OBSIDIAN = pen(26, 14, 40)
CHARGE_DIM = pen(255, 206, 100)


class FluffSkin:
    def __init__(self, idx):
        self.set(idx)

    def set(self, idx):
        self.idx = idx % len(FLUFF_COLOURS)
        c = FLUFF_COLOURS[self.idx]
        self.body = pen(*c)
        self.dark = pen(*shade(c, 0.7))
        self.light = pen(*shade(c, 1.2))
        self.deep = pen(*shade(c, 0.45))
        self.pale = pen(*shade(c, 1.4))
        self.back = pen(int(c[0] * 0.55), int(c[1] * 0.26), int(c[2] * 0.4))


def _hull(pts, ox, oy, f, s):
    rig.poly(tuple((int(x * s), int(y * s)) for x, y in pts), ox, oy, f)


def _seg(ox, oy, f, x, y, ang, ln, w, col):
    """Tapered bone as one triangle. Returns the end joint."""
    c = math.cos(ang)
    si = math.sin(ang)
    px = -si
    py = c
    tx = x + c * ln
    ty = y + si * ln
    display.set_pen(col)
    rig.tri(ox, oy, f,
            int(x + px * w * 0.5), int(y + py * w * 0.5),
            int(x - px * w * 0.5), int(y - py * w * 0.5),
            int(tx), int(ty))
    return tx, ty


def _ear(ox, oy, f, x, y, a0, bend, ln, w, dark, mid, lit):
    """Two-segment ear. Lit facet sits on the outer (upper) edge."""
    jx, jy = _seg(ox, oy, f, x, y, a0, ln * 0.5, w, dark)
    tx, ty = _seg(ox, oy, f, jx, jy, a0 + bend, ln * 0.5, w * 0.55, mid)
    display.set_pen(lit)
    rig.tri(ox, oy, f, int(x), int(y - w * 0.15), int(tx), int(ty),
            int((x + tx) * 0.5), int((y + ty) * 0.5 - w * 0.35))
    return tx, ty


def _paw(ox, oy, f, x, y, ang, ln, w, dark, mid, lit):
    """Three short triangles. Wide at the ankle, a nub at the toe, no spine."""
    c = math.cos(ang)
    si = math.sin(ang)
    px = -si
    py = c
    tx = x + c * ln
    ty = y + si * ln
    display.set_pen(dark)
    rig.tri(ox, oy, f,
            int(x + px * w * 0.55), int(y + py * w * 0.55),
            int(x - px * w * 0.55), int(y - py * w * 0.55),
            int(tx + px * w * 0.3), int(ty + py * w * 0.3))
    display.set_pen(mid)
    rig.tri(ox, oy, f,
            int(x - px * w * 0.55), int(y - py * w * 0.55),
            int(tx + px * w * 0.3), int(ty + py * w * 0.3),
            int(tx - px * w * 0.4), int(ty - py * w * 0.4))
    display.set_pen(lit)
    rig.tri(ox, oy, f, int(x), int(y - w * 0.2), int(tx), int(ty - w * 0.1),
            int((x + tx) * 0.5), int((y + ty) * 0.5 - w * 0.3))


def _pose(anim, ground, vy, wet):
    sway = rig.sin64(anim * 3) * 0.18
    step = rig.sin64(anim * 5) * 0.55
    if wet:
        drift = rig.sin64(anim * 2) * 0.35
        _ANG[0] = -2.35 + drift
        _ANG[1] = -0.25
        _ANG[2] = -0.65 - drift
        _ANG[3] = 0.2
        _ANG[4] = 2.4
        _ANG[5] = 0.7
        _ANG[6] = -2.05 + drift
        _ANG[7] = 0.15
        return
    if not ground and vy < -1:
        _ANG[0] = -2.35
        _ANG[1] = -0.55
        _ANG[2] = -2.05
        _ANG[3] = -0.4
        _ANG[4] = 2.4
        _ANG[5] = 2.1
        _ANG[6] = -2.15
        _ANG[7] = -0.15
        return
    if vy > 2:
        _ANG[0] = -1.85
        _ANG[1] = -0.15
        _ANG[2] = -1.25
        _ANG[3] = 0.1
        _ANG[4] = 1.85
        _ANG[5] = 1.4
        _ANG[6] = -2.05
        _ANG[7] = -0.1
        return
    swing = step if ground and abs(vy) < 0.1 else 0.0
    _ANG[0] = -1.66 + swing * 0.12 + sway * 0.5
    _ANG[1] = 0.05
    _ANG[2] = -1.48 - swing * 0.12 + sway * 0.5
    _ANG[3] = -0.03
    _ANG[4] = 1.75 + swing
    _ANG[5] = 1.25 - swing
    _ANG[6] = -2.3 + sway
    _ANG[7] = 0.1


def _plume(ox, oy, f, s, fa, fb):
    """Slender plume off the back of the headband. Narrower than an ear."""
    c1 = math.cos(fa)
    s1 = math.sin(fa)
    x0 = -5 * s
    y0 = -3 * s
    jx, jy = _seg(ox, oy, f, x0, y0, fa, 6 * s, 2.2 * s, JADE_D)
    _seg(ox, oy, f, jx, jy, fa + fb, 6 * s, 1.8 * s, JADE)
    c2 = math.cos(fa + fb)
    s2 = math.sin(fa + fb)
    tx = jx + c2 * 6 * s
    ty = jy + s2 * 6 * s
    display.set_pen(FEATHER_LIT)
    rig.tri(ox, oy, f, int(x0), int(y0 - s), int(tx), int(ty),
            int(jx - s1 * s), int(jy + c1 * s))


def draw_fluff(skin, x, y, face, anim, ground, vy, wet=False, scale=1, blink=False):
    """x, y = top-left of 10x14 hitbox in screen coords."""
    s = scale
    bob = 0
    if wet:
        bob = int(rig.sin64(anim * 2) * s)
    elif ground and abs(vy) < 0.1 and (anim // 6) & 1:
        bob = s
    cx = int(x + 5 * s)
    cy = int(y + 7 * s + bob)
    f = face

    # Gemini reference silhouette: upright slab ears, a compact egg body and
    # broad, blocky feet. Airborne ears trail backwards without deforming.
    lean = 0
    if wet:
        lean = -3
    elif not ground and vy < -1:
        lean = -2
    elif vy > 2:
        lean = 2

    # Feather and ears sit behind the body.
    display.set_pen(JADE_D)
    _hull(((-5, -7), (-13, -15), (-11, -8), (-5, -4)), cx, cy, f, s)
    display.set_pen(JADE)
    _hull(((-6, -8), (-12, -14), (-9, -7), (-5, -5)), cx, cy, f, s)
    display.set_pen(FEATHER_LIT)
    _hull(((-10, -12), (-12, -14), (-10, -9)), cx, cy, f, s)

    display.set_pen(OUTLINE)
    _hull(((-5, -7), (-5 + lean, -18), (-1 + lean, -18),
           (0, -7)), cx, cy, f, s)
    display.set_pen(skin.back)
    _hull(((-4, -7), (-4 + lean, -17), (-2 + lean, -17),
           (-1, -7)), cx, cy, f, s)
    display.set_pen(skin.light)
    _hull(((-3, -8), (-3 + lean, -16), (-2 + lean, -16),
           (-2, -8)), cx, cy, f, s)

    display.set_pen(OUTLINE)
    _hull(((0, -7), (1 + lean, -19), (5 + lean, -19),
           (5, -6)), cx, cy, f, s)
    display.set_pen(skin.body)
    _hull(((1, -7), (2 + lean, -18), (4 + lean, -18),
           (4, -6)), cx, cy, f, s)
    display.set_pen(skin.pale)
    _hull(((2, -8), (3 + lean, -17), (4 + lean, -17),
           (3, -8)), cx, cy, f, s)

    # Feet are deliberately chunky so the run and jump poses survive at 1x.
    step = int(rig.sin64(anim * 5) * 2) if ground and abs(vy) < 0.1 else 0
    if wet:
        feet = ((-7, 4, -1, 8), (2, 4, 8, 7))
    elif not ground and vy < -1:
        feet = ((-6, 4, -1, 9), (2, 5, 8, 8))
    elif vy > 2:
        feet = ((-5, 6, 0, 10), (2, 6, 6, 10))
    else:
        feet = ((-6 - step, 5, -1 - step, 10),
                (2 + step, 5, 7 + step, 10))
    for x0, y0, x1, y1 in feet:
        display.set_pen(OUTLINE)
        _hull(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), cx, cy, f, s)
        display.set_pen(skin.deep)
        _hull(((x0 + 1, y0 + 1), (x1, y0 + 1),
               (x1, y1 - 1), (x0 + 1, y1 - 1)), cx, cy, f, s)

    display.set_pen(OUTLINE)
    _hull(_EGG_O, cx, cy, f, s)
    display.set_pen(skin.body)
    _hull(_EGG, cx, cy, f, s)

    # Deep left shadow, pale top-left facet and cyan lower-right wet rim.
    display.set_pen(skin.back)
    rig.tri(cx, cy, f, int(-6 * s), int(-3 * s), int(-6 * s), int(5 * s), int(-2 * s), int(7 * s))
    display.set_pen(skin.dark)
    _hull(((-5, 3), (-2, 7), (3, 7), (1, 5), (-3, 5)), cx, cy, f, s)
    display.set_pen(RIM)
    rig.tri(cx, cy, f, int(5 * s), int(-2 * s), int(6 * s), int(4 * s), int(4 * s), int(7 * s))
    display.set_pen(skin.light)
    rig.tri(cx, cy, f, int(-4 * s), int(-6 * s), int(1 * s), int(-8 * s), int(-1 * s), int(-1 * s))
    display.set_pen(skin.pale)
    rig.tri(cx, cy, f, int(-4 * s), int(-6 * s), int(-1 * s), int(-7 * s), int(-3 * s), int(-3 * s))

    # Green headband and compact paired cyan eyes from the Gemini sheet.
    display.set_pen(BAND)
    _hull(((-5, -7), (5, -7), (5, -5), (-5, -5)), cx, cy, f, s)
    e1 = cx - face * s
    e2 = cx + face * 3 * s
    ey = cy - 3 * s
    if blink:
        display.set_pen(BLACK)
        display.rectangle(e1 - s, ey, 3 * s, s)
        display.rectangle(e2 - s, ey, 3 * s, s)
        return
    display.set_pen(EYE_D)
    display.rectangle(e1 - s, ey - s, 3 * s, 3 * s)
    display.rectangle(e2 - s, ey - s, 3 * s, 3 * s)
    display.set_pen(EYE)
    display.rectangle(e1, ey - s, 2 * s, 2 * s)
    display.rectangle(e2, ey - s, 2 * s, 2 * s)
    display.set_pen(WHITE)
    display.rectangle(e1, ey - s, max(1, s), max(1, s))
    display.rectangle(e2, ey - s, max(1, s), max(1, s))


def _polar(a, r):
    return int(round(r * math.cos(a))), int(round(r * math.sin(a)))


def _slash_span(d, face, f):
    k = (d, face, f)
    a = _ARCS.get(k)
    if a is None:
        grow = (8 - f) / 4.0
        if d == 0:
            mid = 0.0 if face > 0 else math.pi
            span = 1.1 + 0.35 * grow
        elif d == 1:
            mid = -math.pi / 2
            span = 1.2 + 0.3 * grow
        else:
            mid = math.pi / 2
            span = 1.2 + 0.3 * grow
        a = (mid, span)
        _ARCS[k] = a
    return a


def _wedge(cx, cy, a0, r0, a1, r1, a2, r2):
    p0 = _polar(a0, r0)
    p1 = _polar(a1, r1)
    p2 = _polar(a2, r2)
    display.triangle(cx + p0[0], cy + p0[1], cx + p1[0], cy + p1[1], cx + p2[0], cy + p2[1])


def draw_slash(px, py, d, face, f, col=None):
    """Crescent blade. Outer points sit on the original radius-17 reach."""
    mid, span = _slash_span(d, face, f)
    cx = int(px + 5)
    cy = int(py + 7)
    a0 = mid - span
    a1 = mid + span
    blade = col or CREAM
    n = 3
    display.set_pen(OBSIDIAN)
    i = 0
    while i < n:
        t0 = a0 + (a1 - a0) * i / n
        t1 = a0 + (a1 - a0) * (i + 1) / n
        _wedge(cx, cy, t0, 10, t1, 10, (t0 + t1) * 0.5, 15)
        i += 1
    i = 0
    while i < n:
        t0 = a0 + (a1 - a0) * i / n
        t1 = a0 + (a1 - a0) * (i + 1) / n
        display.set_pen(WHITE if i == 1 else blade)
        _wedge(cx, cy, t0, 17, t1, 17, (t0 + t1) * 0.5, 13)
        i += 1


def draw_trail(skin, trail):
    n = len(trail)
    i = 0
    while i < n:
        x, y = trail[i]
        cx = int(x + 5)
        cy = int(y + 7 + HUD)
        if i + 1 == n:
            display.set_pen(skin.pale)
        elif i == 0:
            display.set_pen(skin.body)
        else:
            display.set_pen(skin.light)
        display.triangle(cx - 4, cy + 4, cx + 4, cy + 5, cx, cy - 4)
        display.triangle(cx - 2, cy - 2, cx, cy - 3, cx - 1, cy - 9)
        display.triangle(cx + 1, cy - 2, cx + 2, cy - 3, cx + 2, cy - 8)
        i += 1


def _ray(cx, cy, ang, r0, r1, w):
    c = math.cos(ang)
    s = math.sin(ang)
    px = -s * w
    py = c * w
    display.triangle(int(cx + c * r0), int(cy + s * r0),
                     int(cx + c * r1 + px), int(cy + s * r1 + py),
                     int(cx + c * r1 - px), int(cy + s * r1 - py))


def draw_charge(x, y, t, full):
    cx = int(x + 5)
    cy = int(y + 7)
    if full:
        base = t * 0.22 - 1.5708
        display.set_pen(GOLD)
        i = 0
        while i < 8:
            _ray(cx, cy, base + i * 0.7854, 8, 17, 2.4)
            i += 1
        display.set_pen(WHITE)
        i = 0
        while i < 6:
            _ray(cx, cy, base + 0.4 + i * 1.047, 9, 13, 1.3)
            i += 1
    else:
        display.set_pen(CHARGE_DIM)
        ang = t * 0.45
        _ray(cx, cy, ang, 6, 10, 1.5)
        _ray(cx, cy, ang + 2.1, 6, 9, 1.2)
