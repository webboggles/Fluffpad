"""Tile art baked into the room background, plus the live tile effects drawn each frame.

Edge rock is a dark body, a 3 to 4 px lit surface band, a 2 to 3 px underside,
and a 1 px rim. Interior runs are one rectangle plus a few short cracks.
"""
import math
import random
from .hw import display
from .gfx import (pen, shade, pump, HUD, GOLD, JADE, JADE_D, ORANGE, WATER_HI, INK, WHITE)
from .world import (COLS, ROWS, SOLID, T_ROCK, T_CRACK, T_PLANK, T_GRATE, T_SPIKE, T_WATER,
                    T_SEAL, T_RAIN, T_GATE, T_SHUT)

BONE = pen(196, 176, 146)
SPIKE_HI = pen(236, 236, 250)
SPIKE_MID = pen(160, 160, 184)
SPIKE_LO = pen(48, 46, 68)
WET = pen(210, 245, 255)
SUN_HI = pen(255, 236, 160)
SEAL_LO = pen(78, 52, 16)
SEAL_MID = pen(150, 104, 36)
DROP = pen(140, 200, 255)
DROP_HI = pen(220, 245, 255)
DROP_LO = pen(28, 48, 70)
GATE_LO = pen(32, 12, 52)
GATE_MID = pen(72, 32, 104)
GEM_OFF = pen(26, 8, 38)
GEM_HI = pen(210, 255, 226)
SHUT_LO = pen(36, 32, 34)
SHUT_MID = pen(116, 106, 96)
SHUT_HI = pen(168, 156, 140)
LOCK = pen(196, 32, 36)
LOCK_HI = pen(255, 140, 120)
STONE = pen(104, 102, 114)
STONE_HI = pen(158, 156, 168)
STONE_LO = pen(46, 44, 54)
WOOD = pen(96, 62, 34)
WOOD_HI = pen(156, 108, 58)
WOOD_LO = pen(48, 30, 18)


def _n(c, r, k):
    return (c * 13 + r * 29 + k * 17) & 15


def _bev(c, r, k):
    return 3 + (_n(c, r, k) & 3)


def _mass_t(t):
    if t == T_SHUT:
        return True
    return t == T_ROCK or t == T_CRACK or (t > 0 and SOLID[t])


def _at(room, c, r):
    if c < 0 or r < 0 or c >= COLS or r >= ROWS:
        return room.tile(c, r)
    return room.t[r * COLS + c]


def _mask(room):
    w = COLS + 2
    m = bytearray(w * (ROWS + 2))
    for r in range(-1, ROWS + 1):
        for c in range(-1, COLS + 1):
            if _mass_t(_at(room, c, r)):
                m[(r + 1) * w + (c + 1)] = 1
    return m, w


def _soft(room, c, r):
    t = _at(room, c, r)
    return t == 0 or t == T_WATER


def _interior(room, m, w, c, r):
    if room.t[r * COLS + c] != T_ROCK:
        return False
    i = (r + 1) * w + (c + 1)
    return m[i - 1] and m[i + 1] and m[i - w] and m[i + w]


def _shell(room, m, w, c, r):
    t = room.t[r * COLS + c]
    if t != T_ROCK and t != T_CRACK:
        return False
    if t == T_ROCK and _interior(room, m, w, c, r):
        return False
    return True


def _exp(m, w, c, r):
    i = (r + 1) * w + (c + 1)
    return (not m[i - w], not m[i + w], not m[i - 1], not m[i + 1])


def _outline(x0, y0, x1, y1, nw, ne, se, sw):
    """Clipped quad. Jagged silhouette is the triangle layers, not holes in the fill."""
    pts = []
    if nw:
        pts.append((x0 + nw, y0))
    else:
        pts.append((x0, y0))
    if ne:
        pts.append((x1 - ne, y0))
        pts.append((x1, y0 + ne))
    else:
        pts.append((x1, y0))
    if se:
        pts.append((x1, y1 - se))
        pts.append((x1 - se, y1))
    else:
        pts.append((x1, y1))
    if sw:
        pts.append((x0 + sw, y1))
        pts.append((x0, y1 - sw))
    else:
        pts.append((x0, y1))
    if nw:
        pts.append((x0, y0 + nw))
    return pts


def _tones(pal):
    """Body darker than the backdrop rock, underside darker still, rim nearly black.

    Dread and xibalba air is near-black, so those bodies stay a readable mid-tone.
    """
    z = pal.zone
    if z == "dread":
        return pen(96, 100, 128), pen(54, 56, 78), pen(20, 18, 32)
    if z == "xibalba":
        return pen(98, 44, 96), pen(52, 20, 48), pen(20, 8, 18)
    body = pen(*shade(pal.raw[2], 0.52))
    under = pen(*shade(pal.raw[4], 0.62))
    rim = pen(*shade(pal.raw[4], 0.35))
    return body, under, rim


def _surface(pal):
    """Lit top band: grass, moss, gilt, bone, snow, ember."""
    z = pal.zone
    if z == "jungle":
        return pal.cap, pen(*shade(pal.raw[5], 1.35))
    if z == "cenote":
        return pal.cap, WET
    if z == "temple":
        return pal.cap, GOLD
    if z == "dread":
        return BONE, pal.hi
    if z == "mountain":
        return pal.cap, WHITE
    return pal.accent, pal.hi


def _drip_col(pal):
    z = pal.zone
    if z == "jungle":
        return pal.cap_d
    if z == "cenote":
        return pal.hi
    if z == "mountain":
        return pal.cap
    if z == "xibalba" or z == "dread":
        return pal.accent
    return pal.lo


def _lip(col_a, col_b, x0, x1, y, depth, sign, phase):
    """Overlapping triangles, 3 to 4 px into the mass. sign +1 points down."""
    if x1 - x0 < 4:
        return
    x = x0
    k = 0
    while x < x1 - 3:
        n = (x * 3 + phase * 5 + k * 7) & 15
        w = 8 + (n & 7)
        if x + w > x1:
            w = x1 - x
        if w < 4:
            break
        d = depth + (n & 1)
        span = w - 3
        if span < 1:
            span = 1
        tip = x + 2 + ((n >> 1) % span)
        display.set_pen(col_a if (k & 1) == 0 else col_b)
        display.triangle(x, y, x + w, y, tip, y + sign * d)
        x += 4 + (n & 3)
        k += 1


def _tufts(col, x0, x1, y, phase):
    """Sparse peaks above a top edge. Not one per tile."""
    if x1 - x0 < 8:
        return
    x = x0 + 1 + (phase & 5)
    k = 0
    while x < x1 - 3:
        n = (x * 5 + phase + k * 11) & 15
        if (n & 7) == 0:
            h = 3 + (n & 3)
            half = 2 + (n & 1)
            b = x + half * 2
            if b > x1:
                b = x1
            display.set_pen(col)
            display.triangle(x, y, b, y, x + half, y - h)
        x += 9 + (n & 7)
        k += 1


def _drips(col, x0, x1, y, phase):
    if x1 - x0 < 8:
        return
    x = x0 + (phase & 7)
    k = 0
    while x < x1 - 3:
        n = (x * 5 + phase * 3 + k * 9) & 15
        if (n & 7) == 0:
            h = 3 + (n & 3)
            half = 2 + (n & 1)
            b = x + half * 2
            if b > x1:
                b = x1
            display.set_pen(col)
            display.triangle(x, y, b, y, x + half, y + h)
        x += 8 + (n & 7)
        k += 1


def _side_bands(hi, lo, x, y0, y1, inward):
    """Lit top and dark foot on a vertical edge, tucked into the mass."""
    h = y1 - y0
    if h < 6:
        return
    mid = y0 + h // 2
    display.set_pen(hi)
    display.triangle(x, y0, x, mid, x + inward * 3, y0 + 3)
    display.set_pen(lo)
    display.triangle(x, y1, x, mid, x + inward * 3, y1 - 2)


def _rim(col, x0, y0, x1, y1, up, dn, left, right):
    display.set_pen(col)
    if up:
        display.line(x0, y0, x1 - 1, y0)
    if dn:
        display.line(x0, y1 - 1, x1 - 1, y1 - 1)
    if left:
        display.line(x0, y0, x0, y1 - 1)
    if right:
        display.line(x1 - 1, y0, x1 - 1, y1 - 1)


def _corner(outer, inner, ax, ay, bx, by, px, py):
    display.set_pen(outer)
    display.triangle(ax, ay, bx, by, px, py)
    display.set_pen(inner)
    display.triangle(ax, ay, (ax + bx) // 2, (ay + by) // 2, (ax + px) // 2, (ay + py) // 2)


def _spark(pal, c, r, x, y):
    if (_n(c, r, 8) & 7) != 0:
        return
    z = pal.zone
    if z == "cenote":
        display.set_pen(WET)
        display.triangle(x + 4, y + 2, x + 10, y + 3, x + 6, y + 7)
    elif z == "dread":
        display.set_pen(pal.accent)
        display.line(x + 6, y + 4, x + 7, y + 12)
        display.line(x + 7, y + 8, x + 11, y + 6)
    elif z == "xibalba":
        display.set_pen(pal.accent)
        display.line(x + 7, y + 4, x + 8, y + 12)
        display.line(x + 8, y + 8, x + 12, y + 9)
    elif z == "temple":
        display.set_pen(pal.lo)
        display.triangle(x + 4, y + 5, x + 11, y + 7, x + 6, y + 12)


def _shell_run(room, pal, m, w, c0, c1, r):
    up, dn, left, right = _exp(m, w, c0, r)
    right = _exp(m, w, c1, r)[3]
    x0 = c0 * 16
    x1 = (c1 + 1) * 16
    y0 = HUD + r * 16
    y1 = y0 + 16
    nw = _bev(c0, r, 0) if up and left else 0
    ne = _bev(c1, r, 1) if up and right else 0
    se = _bev(c1, r, 2) if dn and right else 0
    sw = _bev(c0, r, 3) if dn and left else 0
    body, under, rim = _tones(pal)
    lit, lit2 = _surface(pal)
    display.set_pen(body)
    if nw or ne or se or sw:
        display.polygon(_outline(x0, y0, x1, y1, nw, ne, se, sw))
    else:
        display.rectangle(x0, y0, x1 - x0, y1 - y0)
    if nw:
        _corner(body, pal.hi, x0 + nw, y0, x0, y0 + nw, x0 + 1, y0 + 1)
    if ne:
        _corner(body, pal.hi, x1 - ne, y0, x1, y0 + ne, x1 - 1, y0 + 1)
    if se:
        _corner(body, under, x1, y1 - se, x1 - se, y1, x1 - 1, y1 - 1)
    if sw:
        _corner(body, under, x0, y1 - sw, x0 + sw, y1, x0 + 1, y1 - 1)
    if up:
        span = (x1 - ne) - (x0 + nw)
        if span > 0:
            display.set_pen(lit)
            display.rectangle(x0 + nw, y0, span, 4)
            _lip(lit2, lit, x0 + nw, x1 - ne, y0 + 1, 3, 1, _n(c0, r, 3))
        if _soft(room, c0, r - 1):
            _tufts(lit2, x0 + nw, x1 - ne, y0, _n(c0, r, 1))
    if dn:
        span = (x1 - se) - (x0 + sw)
        if span > 0:
            display.set_pen(under)
            display.rectangle(x0 + sw, y1 - 3, span, 3)
            _lip(rim, under, x0 + sw, x1 - se, y1 - 1, 2, -1, _n(c0, r, 5))
        if _soft(room, c0, r + 1):
            _drips(_drip_col(pal), x0 + sw, x1 - se, y1, _n(c0, r, 4))
    if left:
        _side_bands(lit, under, x0, y0 + nw, y1 - sw, 1)
    if right:
        _side_bands(lit, under, x1 - 1, y0 + ne, y1 - se, -1)
    _rim(rim, x0, y0, x1, y1, up, dn, left, right)
    c = c0
    while c <= c1:
        _spark(pal, c, r, c * 16, y0)
        c += 1


def _reseed(room):
    seed = 91
    for ch in room.id:
        seed = seed * 31 + ord(ch)
    random.seed(seed)


def _vein(col, hot, x, y):
    """A slanted crack and a short fork. No crossbar, so it is not an arrow."""
    x0 = x + 3 + random.randrange(7)
    lean = random.randrange(-4, 5)
    x1 = x0 + lean
    if x1 < x + 1:
        x1 = x + 1
    if x1 > x + 14:
        x1 = x + 14
    y0 = y + 1
    y1 = y + 14
    display.set_pen(col)
    display.line(x0, y0, x1, y1)
    cut = 5 + random.randrange(4)
    mx = x0 + (x1 - x0) * cut // 12
    my = y0 + (y1 - y0) * cut // 12
    fork = lean // 2
    if fork >= 0:
        fork += 2
    else:
        fork -= 2
    display.set_pen(hot)
    display.line(mx, my, mx + fork, my + 4)


def _crack_cols(pal):
    z = pal.zone
    if z == "dread":
        return pal.vein_d, pal.accent
    if z == "xibalba":
        return pen(*shade(pal.raw[6], 0.55)), pal.accent
    if z == "jungle":
        return pal.cap_d, pal.cap
    if z == "cenote":
        return pal.lo, pal.cap
    if z == "temple":
        return pal.lo, pal.hi
    return pal.lo, pen(*shade(pal.raw[2], 0.8))


def _veins(pal, x, y, wid):
    """About one short crack per 3 to 5 interior tiles."""
    tiles = wid // 16
    if tiles < 1:
        return
    col, hot = _crack_cols(pal)
    i = random.randrange(3)
    while i < tiles:
        _vein(col, hot, x + i * 16, y)
        i += random.randrange(3, 6)


def _interiors(room, pal, m, w):
    _reseed(room)
    body = _tones(pal)[0]
    for r in range(ROWS):
        c = 0
        y = HUD + r * 16
        while c < COLS:
            if _interior(room, m, w, c, r):
                c1 = c
                while c1 + 1 < COLS and _interior(room, m, w, c1 + 1, r):
                    c1 += 1
                x = c * 16
                wid = (c1 - c + 1) * 16
                display.set_pen(body)
                display.rectangle(x, y, wid, 16)
                _veins(pal, x, y, wid)
                c = c1 + 1
            else:
                c += 1


def _shells(room, pal, m, w):
    for r in range(ROWS):
        c = 0
        while c < COLS:
            if _shell(room, m, w, c, r):
                up, dn = _exp(m, w, c, r)[0], _exp(m, w, c, r)[1]
                c1 = c
                while c1 + 1 < COLS and _shell(room, m, w, c1 + 1, r):
                    u2, d2 = _exp(m, w, c1 + 1, r)[0], _exp(m, w, c1 + 1, r)[1]
                    if u2 != up or d2 != dn:
                        break
                    c1 += 1
                _shell_run(room, pal, m, w, c, c1, r)
                c = c1 + 1
            else:
                c += 1


def _fillets(room, pal, m, w):
    lit, lit2 = _surface(pal)
    under = _tones(pal)[1]
    for r in range(ROWS):
        for c in range(COLS):
            t = room.t[r * COLS + c]
            if t != 0 and t != T_WATER:
                continue
            i = (r + 1) * w + (c + 1)
            x = c * 16
            y = HUD + r * 16
            north = m[i - w] and r > 0
            south = m[i + w] and r + 1 < ROWS
            west = m[i - 1] and c > 0
            east = m[i + 1] and c + 1 < COLS
            if north and west:
                b = _bev(c, r, 0)
                _corner(under, pal.lo, x, y, x + b, y, x, y + b)
            if north and east:
                b = _bev(c, r, 1)
                _corner(under, pal.lo, x + 16, y, x + 16 - b, y, x + 16, y + b)
            if south and west:
                b = _bev(c, r, 3)
                _corner(lit, lit2, x, y + 16, x + b, y + 16, x, y + 16 - b)
            if south and east:
                b = _bev(c, r, 2)
                _corner(lit, lit2, x + 16, y + 16, x + 16 - b, y + 16, x + 16, y + 16 - b)


def _cracks(room, pal):
    glow = pal.zone == "dread" or pal.zone == "xibalba" or pal.zone == "cenote"
    for r in range(ROWS):
        for c in range(COLS):
            if room.t[r * COLS + c] != T_CRACK:
                continue
            x = c * 16
            y = HUD + r * 16
            display.set_pen(pal.lo)
            display.triangle(x + 2, y + 1, x + 8, y + 8, x + 4, y + 15)
            display.triangle(x + 9, y + 1, x + 14, y + 6, x + 11, y + 3)
            display.set_pen(pal.accent if glow else INK)
            display.triangle(x + 5, y + 3, x + 11, y + 7, x + 8, y + 14)


def _wk(r):
    k = 1.0 - r * 0.04
    if k < 0.55:
        k = 0.55
    return k


def _water(room, pal):
    for r in range(ROWS):
        c = 0
        y = HUD + r * 16
        k = _wk(r)
        while c < COLS:
            if room.t[r * COLS + c] == T_WATER:
                c1 = c
                while c1 + 1 < COLS and room.t[r * COLS + c1 + 1] == T_WATER:
                    c1 += 1
                x = c * 16
                n = c1 - c + 1
                display.set_pen(pen(*shade(pal.raw[7], k)))
                display.rectangle(x, y, n * 16, 16)
                above = r == 0 or room.t[(r - 1) * COLS + c] != T_WATER
                if above:
                    hi = k * 1.4
                    if hi > 1.6:
                        hi = 1.6
                    display.set_pen(pen(*shade(pal.raw[7], hi)))
                    display.rectangle(x, y, n * 16, 3)
                    display.set_pen(WATER_HI)
                    display.rectangle(x + 3, y, 5, 1)
                    if n > 3:
                        display.rectangle(x + n * 8, y + 1, 4, 1)
                else:
                    display.set_pen(pen(*shade(pal.raw[7], k * 1.25)))
                    display.rectangle(x + 4, y + 6, 4, 1)
                    if n > 4:
                        display.rectangle(x + n * 8, y + 10, 5, 1)
                c = c1 + 1
            else:
                c += 1


def _plank_run(pal, x, y, n, c, r):
    w = n * 16
    display.set_pen(pal.plank_lo)
    display.polygon([(x, y + 2), (x + w, y + 1), (x + w, y + 6), (x, y + 6)])
    display.set_pen(pal.plank)
    display.polygon([(x, y), (x + w, y), (x + w, y + 3), (x, y + 3)])
    shift = _n(c, r, 1) & 7
    display.set_pen(pal.plank_hi)
    display.triangle(x, y, x + w, y, x + w // 3 + shift, y - 2)
    display.set_pen(pal.plank)
    display.triangle(x + 2, y + 1, x + w - 2, y, x + (w * 2) // 3, y - 1)
    display.set_pen(pal.plank_lo)
    display.triangle(x, y + 4, x + w, y + 4, x + w // 2 + (shift & 3), y + 8)
    display.set_pen(WOOD_LO)
    display.triangle(x + 3, y + 5, x + w - 3, y + 5, x + w // 3, y + 8)
    i = 1
    while i < n:
        bx = x + i * 16
        display.set_pen(INK)
        display.triangle(bx, y, bx + 1, y + 4, bx, y + 3)
        i += 1


def _grate_run(pal, x, y, n):
    w = n * 16
    display.set_pen(pal.hi)
    display.triangle(x, y, x + w, y, x + w // 2, y + 4)
    display.set_pen(pal.lo)
    display.triangle(x + 1, y + 1, x + w - 1, y + 2, x + w // 3, y + 6)
    k = 0
    bars = n * 4
    while k < bars:
        bx = x + 1 + k * 4
        display.set_pen(pal.lo)
        display.triangle(bx, y + 3, bx + 3, y + 3, bx + 1, y + 15)
        display.set_pen(pal.hi)
        display.triangle(bx, y + 3, bx + 2, y + 4, bx + 1, y + 10)
        k += 1


def _spike(x, y):
    k = 0
    while k < 3:
        bx = x + 1 + k * 5
        tip = y + 3 + (k & 1)
        display.set_pen(SPIKE_LO)
        display.triangle(bx, y + 16, bx + 5, y + 16, bx + 2, tip)
        display.set_pen(SPIKE_MID)
        display.triangle(bx + 1, y + 16, bx + 4, y + 16, bx + 2, tip + 3)
        display.set_pen(SPIKE_HI)
        display.triangle(bx + 2, tip, bx + 1, tip + 4, bx + 3, tip + 3)
        k += 1


def _oct(x, y, s, b):
    return [(x + b, y), (x + s - b, y), (x + s, y + b), (x + s, y + s - b),
            (x + s - b, y + s), (x + b, y + s), (x, y + s - b), (x, y + b)]


def _seal(x, y):
    display.set_pen(SEAL_LO)
    display.polygon(_oct(x, y, 16, 3))
    display.set_pen(SEAL_MID)
    display.polygon(_oct(x + 2, y + 2, 12, 2))
    display.set_pen(GOLD)
    display.triangle(x + 8, y + 3, x + 4, y + 8, x + 12, y + 8)
    display.triangle(x + 8, y + 13, x + 4, y + 8, x + 12, y + 8)
    display.triangle(x + 3, y + 8, x + 8, y + 4, x + 8, y + 12)
    display.triangle(x + 13, y + 8, x + 8, y + 4, x + 8, y + 12)
    display.set_pen(SUN_HI)
    display.triangle(x + 8, y + 5, x + 6, y + 8, x + 10, y + 7)


def _rain(x, y):
    display.set_pen(DROP_LO)
    display.polygon(_oct(x, y, 16, 3))
    display.set_pen(pen(48, 82, 114))
    display.polygon(_oct(x + 2, y + 2, 12, 2))
    display.set_pen(DROP)
    display.triangle(x + 8, y + 3, x + 4, y + 9, x + 12, y + 9)
    display.triangle(x + 4, y + 9, x + 12, y + 9, x + 8, y + 13)
    display.set_pen(DROP_HI)
    display.triangle(x + 7, y + 5, x + 6, y + 8, x + 9, y + 7)


def _gem(cx, cy, on):
    if on:
        display.set_pen(JADE_D)
        display.triangle(cx, cy - 3, cx - 3, cy + 2, cx + 3, cy + 2)
        display.set_pen(JADE)
        display.triangle(cx, cy - 2, cx - 2, cy, cx + 2, cy + 1)
        display.set_pen(GEM_HI)
        display.triangle(cx - 1, cy - 1, cx, cy - 2, cx + 1, cy)
    else:
        display.set_pen(GEM_OFF)
        display.triangle(cx, cy - 3, cx - 3, cy + 2, cx + 3, cy + 2)


def _gate(x, y, c, lit):
    display.set_pen(GATE_LO)
    display.polygon(_oct(x, y, 16, 3))
    display.set_pen(GATE_MID)
    display.polygon(_oct(x + 2, y + 2, 12, 2))
    k = 0
    while k < 2:
        idx = (c % 2) * 2 + k
        _gem(x + 5 + k * 6, y + 9, lit > idx)
        k += 1


def _shut(x, y):
    display.set_pen(SHUT_LO)
    display.rectangle(x, y, 16, 16)
    k = 0
    while k < 3:
        bx = x + 1 + k * 5
        display.set_pen(SHUT_MID)
        display.triangle(bx, y + 1, bx + 4, y, bx, y + 15)
        display.triangle(bx + 4, y, bx + 3, y + 16, bx, y + 15)
        display.set_pen(SHUT_HI)
        display.triangle(bx, y + 1, bx + 4, y, bx + 2, y + 5)
        display.set_pen(SHUT_LO)
        display.triangle(bx, y + 11, bx + 3, y + 16, bx + 1, y + 15)
        k += 1
    display.set_pen(LOCK)
    display.triangle(x + 8, y + 5, x + 4, y + 9, x + 12, y + 9)
    display.set_pen(LOCK_HI)
    display.triangle(x + 8, y + 6, x + 6, y + 8, x + 10, y + 8)


def _runs(room, kind, fn):
    for r in range(ROWS):
        c = 0
        y = HUD + r * 16
        while c < COLS:
            if room.t[r * COLS + c] == kind:
                c1 = c
                while c1 + 1 < COLS and room.t[r * COLS + c1 + 1] == kind:
                    c1 += 1
                fn(c * 16, y, c1 - c + 1, c, r)
                c = c1 + 1
            else:
                c += 1


def _shrine_base(x, y):
    display.set_pen(STONE_LO)
    display.triangle(x - 13, y + 15, x + 13, y + 15, x - 2, y + 6)
    display.triangle(x - 12, y + 14, x + 13, y + 15, x + 5, y + 5)
    display.set_pen(STONE)
    display.triangle(x - 10, y + 8, x + 10, y + 8, x, y + 2)
    display.set_pen(STONE_HI)
    display.triangle(x - 7, y + 7, x + 5, y + 6, x - 1, y + 3)
    display.set_pen(JADE_D)
    display.triangle(x, y - 4, x - 4, y + 3, x + 4, y + 3)
    display.set_pen(JADE)
    display.triangle(x, y - 2, x - 2, y + 2, x + 2, y + 1)


def _stele(x, y, pal):
    display.set_pen(pal.lo)
    display.polygon([(x + 4, y), (x + 12, y), (x + 14, y + 16), (x + 2, y + 16)])
    display.set_pen(STONE_HI)
    display.triangle(x + 4, y + 1, x + 12, y + 1, x + 8, y + 6)
    display.set_pen(pal.hi)
    display.triangle(x + 5, y + 2, x + 10, y + 2, x + 7, y + 5)
    display.set_pen(pal.hi)
    display.triangle(x + 3, y + 3, x + 6, y + 8, x + 3, y + 13)
    display.set_pen(pal.lo)
    display.triangle(x + 12, y + 3, x + 14, y + 15, x + 10, y + 9)
    display.set_pen(INK)
    display.triangle(x + 6, y + 8, x + 10, y + 8, x + 8, y + 11)
    display.triangle(x + 6, y + 12, x + 10, y + 12, x + 8, y + 15)


def _torch(x, y):
    display.set_pen(WOOD)
    display.triangle(x + 6, y + 8, x + 10, y + 8, x + 8, y + 16)
    display.set_pen(WOOD_HI)
    display.triangle(x + 7, y + 8, x + 10, y + 9, x + 9, y + 15)
    display.set_pen(WOOD_LO)
    display.triangle(x + 3, y + 6, x + 13, y + 6, x + 8, y + 10)
    display.set_pen(WOOD_HI)
    display.triangle(x + 5, y + 6, x + 11, y + 6, x + 8, y + 8)


def draw_room(room, pal, glyphs=0):
    m, w = _mask(room)
    pump()
    _water(room, pal)
    pump()
    _interiors(room, pal, m, w)
    pump()
    _shells(room, pal, m, w)
    pump()
    _fillets(room, pal, m, w)
    pump()
    _cracks(room, pal)
    pump()
    _runs(room, T_PLANK, lambda x, y, n, c, r: _plank_run(pal, x, y, n, c, r))
    _runs(room, T_GRATE, lambda x, y, n, c, r: _grate_run(pal, x, y, n))
    for r in range(ROWS):
        y = HUD + r * 16
        pump()
        for c in range(COLS):
            k = room.t[r * COLS + c]
            x = c * 16
            if k == T_SPIKE:
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
            _stele(x, y, pal)
        elif ch == "T":
            _torch(x, y)


# --- live effects, drawn every frame over the baked background ---------------------------
def draw_surfaces(surfaces, pal, t):
    rect = display.rectangle
    hi = WATER_HI
    mid = pal.water
    for sx, sy in surfaces:
        y = sy + HUD
        o = int(math.sin(t * 0.12 + sx * 0.09) * 1.5)
        display.set_pen(mid)
        rect(sx, y, 16, 2)
        display.set_pen(hi)
        rect(sx + ((t // 3 + sx) % 12), y + o, 4, 1)


def draw_flame(tx, ty, t):
    """Torch flame; tx, ty = torch tile top-left in room coords."""
    y = ty + HUD
    wob = (t + tx) & 3
    display.set_pen(ORANGE)
    display.triangle(tx + 8, y - 2 - (wob & 1), tx + 3, y + 7, tx + 13, y + 6)
    display.set_pen(GOLD)
    display.triangle(tx + 8, y + (wob & 1), tx + 6, y + 6, tx + 11, y + 5)


def draw_shrine_glow(sx, sy, t):
    """Shrine orb; sx, sy = shrine tile top-left in room coords."""
    cx = sx + 8
    cy = sy + HUD + 2
    r = 3 + ((t >> 3) & 1)
    display.set_pen(JADE)
    display.triangle(cx, cy - r, cx - r, cy + 1, cx + r, cy + 1)
    display.set_pen(WHITE)
    display.triangle(cx, cy - r + 2, cx - 1, cy, cx + 1, cy - 1)


def draw_lore_glint(lx, ly, t):
    """Unread stele marker; lx, ly = stele tile top-left in room coords."""
    if (t >> 4) & 1:
        display.set_pen(GOLD)
        display.triangle(lx + 8, ly + HUD - 6, lx + 6, ly + HUD - 3, lx + 10, ly + HUD - 3)
