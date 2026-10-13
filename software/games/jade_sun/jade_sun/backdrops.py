"""Zone backdrops baked behind the tiles: triangular scenery, far to near."""
import random
from .hw import display
from .gfx import pen, mix, shade, pump, HUD


def _salt(rid):
    h = 0
    for ch in rid:
        h = (h * 33 + ord(ch)) & 0x7fffffff
    return h


def _ink(c):
    pump()
    display.set_pen(pen(c[0], c[1], c[2]))


def _fill(c):
    _ink(c)
    display.triangle(0, HUD, 319, HUD, 0, 239)
    display.triangle(319, HUD, 319, 239, 0, 239)


def _tri(c, x0, y0, x1, y1, x2, y2):
    _ink(c)
    display.triangle(x0, y0, x1, y1, x2, y2)


def _zenith(c, reach):
    """Light from above: pale wedges, not gradient bands."""
    _ink(c)
    display.triangle(0, HUD, 150, HUD, 64, reach)
    display.triangle(170, HUD, 319, HUD, 256, reach)
    display.triangle(70, HUD, 250, HUD, 160, reach + 8)


def _peak(x, yb, w, h, lit, mid, dark, snow=None):
    tip = x + w // 2 + random.randint(-max(1, w // 8), max(1, w // 8))
    tipy = yb - h
    _tri(dark, x, yb + 4, x + w, yb, tip, tipy)
    _tri(mid, x + w // 6, yb - h // 8, x + (w * 5) // 6, yb - h // 10, tip, tipy)
    _tri(lit, tip - w // 6, tipy + h // 3, tip + w // 5, tipy + h // 3, tip, tipy)
    if snow is not None and h > 22:
        _tri(snow, tip - w // 8, tipy + h // 6, tip + w // 7, tipy + h // 5, tip, tipy)


def _ridge(y, n, amp, lit, mid, dark, snow=None, simple=False, x0=-16, x1=340):
    span = max(1, x1 - x0)
    step = span // max(1, n)
    x = x0
    i = 0
    while i < n and x < x1:
        w = step + random.randint(-6, 12)
        h = random.randint(max(8, amp // 3), amp)
        if simple:
            tip = x + w // 2 + random.randint(-5, 5)
            _tri(mid, x, y + 14, x + w, y + 6, tip, y - h)
            _tri(lit, tip - w // 5, y - h // 3, tip + w // 4, y - h // 4, tip, y - h)
        else:
            _peak(x, y, max(12, w), h, lit, mid, dark, snow)
        x += max(8, w // 2)
        i += 1


def _teeth(y, n, amp, col, down=True, x0=-8, x1=332):
    step = max(8, (x1 - x0) // max(1, n))
    x = x0
    i = 0
    while i < n and x < x1:
        w = step + random.randint(-3, 7)
        h = random.randint(max(6, amp // 3), amp)
        tip = x + w // 2 + random.randint(-3, 3)
        if down:
            _tri(col, x, y, x + w, y, tip, y + h)
        else:
            _tri(col, x, y, x + w, y, tip, y - h)
        x += max(6, (w * 3) // 4)
        i += 1


def _tree(x, yb, h, lit, mid, dark, bark, bark_d):
    """Stacked boughs leaning left and right, not a single cone."""
    tw = max(5, h // 7)
    lean = random.randint(-8, 8)
    _tri(bark_d, x, yb, x + tw + 4, yb, x + tw, yb - h)
    _tri(bark, x + 1, yb - 1, x + tw - 1, yb, x + 2, yb - h + 3)
    cy = yb - h // 2
    reach = h // 2 + random.randint(0, 8)
    _tri(dark, x + tw // 2, cy, x - reach, cy + 10, x + 1, cy + 5)
    _tri(mid, x + tw // 2, cy - 3, x - reach + 8, cy + 2, x - 4, cy - 10)
    _tri(lit, x - 2, cy - 6, x - reach // 2, cy - 1, x - 6, cy - 16)
    cy2 = yb - (h * 2) // 3
    reach2 = h // 2 + random.randint(-4, 6)
    _tri(dark, x + tw // 2, cy2, x + tw + reach2, cy2 + 12, x + tw, cy2 + 3)
    _tri(mid, x + tw // 2, cy2 - 4, x + reach2, cy2 + 1, x + tw + 2, cy2 - 12)
    _tri(lit, x + tw // 2, cy2 - 8, x + reach2 // 2, cy2 - 2, x + tw, cy2 - 16)
    # upper shelves stay split so the crown is not one cone
    _tri(dark, x - 2, cy2 - 8, x - reach // 2, cy2 - 4, x + lean, cy2 - 18)
    _tri(lit, x + tw, cy2 - 8, x + tw + reach2 // 2, cy2 - 2, x + tw + lean, cy2 - 18)


def _vine(x, y, ln, dark, mid, leaf):
    cx, cy = x, y
    i = 0
    while i < 3:
        nx = cx + random.randint(-8, 8)
        ny = cy + ln // 3
        w = 3 - i
        _tri(mid if i == 0 else dark, cx - w, cy, cx + w + 1, cy, nx, ny)
        cx, cy = nx, ny
        i += 1
    _tri(leaf, cx - 6, cy, cx + 2, cy + 2, cx - 2, cy + 9)
    _tri(leaf, cx, cy + 1, cx + 6, cy + 2, cx + 3, cy + 8)


def _shaft(x, y0, y1, w, col, core):
    _tri(col, x, y0, x + w, y0, x + w // 3, y1)
    _tri(core, x + w // 3, y0, x + (w * 3) // 5, y0, x + w // 3 + 1, y1)


def _pyramid(cx, base, h, lit, mid, dark, steps):
    _tri(dark, cx - h, base + 6, cx + h, base, cx, base - h)
    _tri(mid, cx - (h * 3) // 4, base, cx + h // 4, base - 2, cx - h // 10, base - h + 4)
    _tri(lit, cx - h // 3, base - h // 2, cx + h // 8, base - h // 2, cx - h // 12, base - h)
    s = 0
    while s < steps:
        yy = base - (h * s) // steps
        ww = (h * (steps - s)) // steps
        _tri(lit if s + 1 == steps else mid, cx - ww // 2, yy, cx + ww // 2, yy + 3, cx, yy - max(8, h // steps))
        s += 1
    _tri(dark, cx + h // 8, base - h + 6, cx + h - 2, base, cx + h // 2, base - h // 3)
    _tri(shade(dark, 0.75), cx - 5, base, cx + 6, base, cx, base - h // 5)


def _pillar(x, y0, y1, w, lit, mid, dark):
    """Tapered shaft. The silhouette is a wedge, not a box."""
    _tri(dark, x - w // 2, y1, x + w + w // 2, y1, x + w // 2, y0 + 16)
    _tri(mid, x, y1 - 6, x + w, y1 - 4, x + w // 2, y0 + 20)
    _tri(lit, x + w // 10, y1 - 12, x + w // 2, y1 - 18, x + w // 3, y0 + 22)
    _tri(lit, x - w, y0 + 20, x + w * 2, y0 + 16, x + w // 2, y0)
    _tri(mid, x - w // 2, y0 + 26, x + w + w // 2, y0 + 22, x + w // 2, y0 + 8)
    _tri(dark, x - w, y1, x + w * 2, y1 + 2, x + w // 2, y1 - 14)
    _tri(dark, x + w, (y0 + y1) // 2, x + w + 8, (y0 + y1) // 2 + 14, x + w // 2, y0 + (y1 - y0) // 3)


def _stone(x, y, w, h, lit, mid, dark):
    _tri(dark, x, y + h, x + w, y + h - 3, x + w // 2 + 2, y)
    _tri(mid, x + 2, y + h - 1, x + (w * 3) // 5, y + h, x + w // 5, y + h // 3)
    _tri(lit, x + w // 6, y + h // 2, x + (w * 2) // 3, y + h // 2, x + w // 2, y + 1)


def _blocks(n, y0, y1, lit, mid, dark, salt, big=False):
    i = 0
    while i < n:
        x = (salt * (i + 2) + i * 73) % 280
        span = max(1, y1 - y0)
        y = y0 + (salt // (i + 1) + i * 29) % span
        w = (36 if big else 26) + (salt + i * 11) % (32 if big else 20)
        h = (18 if big else 14) + (i * 5) % 10
        _stone(x, y, w, h, lit, mid, dark)
        i += 1


def _frieze(x, y, n, gap, lit, mid, dark):
    i = 0
    while i < n:
        xi = x + i * gap
        k = (i + (xi // 7)) & 3
        if k == 0:
            _tri(lit, xi, y + 8, xi + 9, y + 8, xi + 4, y)
            _tri(dark, xi + 2, y + 5, xi + 7, y + 5, xi + 4, y + 2)
        elif k == 1:
            _tri(mid, xi, y + 1, xi + 9, y, xi + 4, y + 8)
            _tri(lit, xi + 2, y + 3, xi + 6, y + 3, xi + 4, y)
        elif k == 2:
            _tri(dark, xi, y + 4, xi + 4, y, xi + 9, y + 4)
            _tri(lit, xi + 1, y + 4, xi + 8, y + 4, xi + 4, y + 9)
        else:
            _tri(mid, xi, y + 2, xi + 8, y + 1, xi + 2, y + 8)
            _tri(dark, xi + 3, y + 2, xi + 9, y + 3, xi + 7, y + 8)
        i += 1


def _flame(x, y, hot, mid, dark):
    _tri(dark, x - 9, y + 2, x + 9, y + 2, x, y - 4)
    _tri(shade(dark, 0.7), x - 6, y + 1, x + 6, y, x, y - 7)
    lean = random.randint(-2, 2)
    _tri(mid, x - 4, y - 2, x + 5, y - 1, x + lean, y - 15)
    _tri(hot, x - 2, y - 6, x + 2, y - 5, x + lean, y - 20)


def _statue(x, y, lit, mid, dark, broken, s=1):
    _tri(dark, x - 12 * s, y, x + 12 * s, y, x, y - 8 * s)
    _tri(mid, x - 7 * s, y - 6 * s, x + 7 * s, y - 6 * s, x + s, y - 28 * s)
    _tri(lit, x - 3 * s, y - 12 * s, x + 4 * s, y - 14 * s, x, y - 26 * s)
    if broken:
        _tri(dark, x + 2 * s, y - 18 * s, x + 20 * s, y - 8 * s, x + 6 * s, y - 14 * s)
        _tri(mid, x - 6 * s, y - 26 * s, x + 2 * s, y - 24 * s, x - 2 * s, y - 34 * s)
        _tri(dark, x - 8 * s, y - 6 * s, x - 1 * s, y - 16 * s, x - 16 * s, y)
    else:
        _tri(mid, x - 5 * s, y - 26 * s, x + 5 * s, y - 26 * s, x, y - 40 * s)
        _tri(lit, x - 2 * s, y - 32 * s, x + 3 * s, y - 32 * s, x, y - 40 * s)
        _tri(dark, x + 4 * s, y - 20 * s, x + 16 * s, y - 26 * s, x + 5 * s, y - 14 * s)


def _mask(cx, cy, lit, mid, dark, eye, s=1):
    _tri(dark, cx - 22 * s, cy + 14 * s, cx + 22 * s, cy + 14 * s, cx, cy - 28 * s)
    _tri(mid, cx - 14 * s, cy + 6 * s, cx + 15 * s, cy + 8 * s, cx, cy - 18 * s)
    _tri(lit, cx - 7 * s, cy - 2 * s, cx + 8 * s, cy - 1 * s, cx, cy - 20 * s)
    _tri(dark, cx - 16 * s, cy - 2 * s, cx - 2 * s, cy, cx - 10 * s, cy - 16 * s)
    _tri(dark, cx + 2 * s, cy, cx + 16 * s, cy - 2 * s, cx + 10 * s, cy - 16 * s)
    _tri(dark, cx - 13 * s, cy + 3 * s, cx - 4 * s, cy + 4 * s, cx - 8 * s, cy - 8 * s)
    _tri(dark, cx + 4 * s, cy + 4 * s, cx + 13 * s, cy + 3 * s, cx + 8 * s, cy - 8 * s)
    _tri(eye, cx - 11 * s, cy + 1 * s, cx - 6 * s, cy + 2 * s, cx - 8 * s, cy - 5 * s)
    _tri(eye, cx + 6 * s, cy + 2 * s, cx + 11 * s, cy + 1 * s, cx + 8 * s, cy - 5 * s)
    _tri(dark, cx - 8 * s, cy + 10 * s, cx + 8 * s, cy + 10 * s, cx, cy + 4 * s)


def _skull(cx, cy, bone, lit, dark, s):
    jaw = shade(bone, 0.7)
    # wide shallow crown, side cheeks, short jaw: a head, not a diamond
    _tri(bone, cx - 11 * s, cy - 3 * s, cx + 11 * s, cy - 3 * s, cx, cy - 8 * s)
    _tri(lit, cx - 4 * s, cy - 4 * s, cx + 4 * s, cy - 4 * s, cx, cy - 8 * s)
    _tri(bone, cx - 12 * s, cy - 2 * s, cx - 5 * s, cy + 3 * s, cx - 7 * s, cy - 6 * s)
    _tri(bone, cx + 5 * s, cy + 3 * s, cx + 12 * s, cy - 2 * s, cx + 7 * s, cy - 6 * s)
    _tri(jaw, cx - 7 * s, cy + 2 * s, cx + 7 * s, cy + 2 * s, cx - 2 * s, cy + 7 * s)
    _tri(bone, cx - 5 * s, cy + 3 * s, cx + 6 * s, cy + 2 * s, cx + 2 * s, cy + 6 * s)
    _tri(dark, cx - 7 * s, cy - 1 * s, cx - 3 * s, cy, cx - 5 * s, cy - 4 * s)
    _tri(dark, cx + 3 * s, cy, cx + 7 * s, cy - 1 * s, cx + 5 * s, cy - 4 * s)


def _spire(x, yb, h, w, lit, mid, dark):
    _tri(dark, x - w, yb, x + w // 3, yb + 4, x - w // 8, yb - h)
    _tri(mid, x - w // 4, yb, x + w, yb - 2, x + w // 5, yb - h + 4)
    _tri(lit, x - w // 6, yb - (h * 2) // 3, x + w // 4, yb - h // 2, x, yb - h)
    _tri(dark, x + w // 5, yb - h // 3, x + w // 2, yb, x + w // 6, yb - h + h // 5)


def _cloud(x, y, w, lit, mid, dark):
    _tri(dark, x, y + 6, x + w, y + 3, x + w // 2, y - 2)
    _tri(mid, x + 2, y + 2, x + w // 2, y + 4, x + w // 5, y - 9)
    _tri(mid, x + w // 3, y + 3, x + w - 2, y + 1, x + (w * 3) // 4, y - 11)
    _tri(lit, x + w // 6, y - 1, x + w // 2, y - 2, x + w // 3, y - 10)
    _tri(lit, x + w // 2, y, x + w - 4, y - 1, x + (w * 2) // 3, y - 8)


def _glint(x, y, c, s):
    _tri(c, x, y - s, x + s, y, x, y + s)
    _tri(c, x, y - s, x - s, y, x, y + s)


def _stal(x, y, w, h, lit, mid, dark):
    _tri(dark, x, y, x + w, y, x + w // 2, y + h)
    _tri(mid, x + w // 5, y, x + (w * 4) // 5, y, x + w // 2, y + (h * 2) // 3)
    _tri(lit, x + w // 3, y, x + w // 2 + 1, y, x + w // 2, y + h // 5)


def _ceiba_tree(z):
    """Spreading ceiba: faceted trunk near x 40-100, wide stacked boughs."""
    bark_d = z[4]
    bark = shade(z[2], 0.95)
    bark_l = shade(z[3], 1.18)
    leaf_d = shade(z[5], 0.34)
    leaf = shade(z[5], 0.68)
    leaf_l = shade(z[5], 1.12)
    gold = shade(z[6], 0.92)
    # buttresses flare outside the trunk
    _tri(bark_d, 6, 238, 50, 222, 32, 162)
    _tri(bark_d, 128, 238, 88, 220, 104, 158)
    _tri(bark_d, 14, 238, 44, 230, 24, 196)
    _tri(bark_d, 112, 238, 80, 228, 116, 188)
    # trunk facets, centre left clear enough for the spirit around x 40-75
    _tri(bark_d, 38, 236, 68, 236, 50, 98)
    _tri(bark, 52, 236, 96, 234, 70, 86)
    _tri(bark_d, 74, 236, 108, 226, 86, 104)
    _tri(bark_l, 46, 156, 78, 164, 58, 90)
    _tri(bark, 48, 200, 86, 206, 64, 186)
    _tri(bark_d, 44, 214, 78, 220, 56, 204)
    # tiers are wide through the middle and droop at the tips
    tiers = ((146, 30, 24), (120, 56, 46), (94, 76, 70), (68, 62, 74), (44, 38, 34))
    for y, left, right in tiers:
        left = left + random.randint(-3, 4)
        right = right + random.randint(-3, 4)
        _tri(leaf_d, 58, y + 2, 58 - left, y + 16, 60, y + 7)
        _tri(leaf, 58, y - 2, 64 - left, y + 4, 56, y - 10)
        _tri(leaf_l, 56, y - 6, 58 - left // 2, y - 2, 52, y - 16)
        _tri(leaf, 58 - left + 6, y + 8, 54 - left, y + 18, 58 - left // 2, y + 1)
        _tri(leaf_d, 78, y + 2, 78 + right, y + 14, 76, y + 7)
        _tri(leaf, 78, y - 2, 72 + right, y + 4, 80, y - 10)
        _tri(leaf_l, 80, y - 6, 78 + right // 2, y, 84, y - 16)
        _tri(leaf, 78 + right - 6, y + 6, 84 + right, y + 16, 78 + right // 2, y)
    _tri(leaf, 28, 38, 58, 30, 36, 12)
    _tri(leaf_l, 50, 32, 82, 26, 66, 6)
    _tri(leaf, 80, 34, 118, 28, 104, 14)
    _tri(leaf_d, 42, 28, 96, 24, 70, 16)
    _tri(leaf_d, 18, 126, 8, 152, 30, 130)
    _tri(leaf_d, 116, 120, 132, 148, 106, 124)
    i = 0
    while i < 5:
        gx = 28 + random.randint(0, 78)
        gy = 16 + random.randint(0, 48)
        _tri(gold, gx, gy + 2, gx + 4, gy + 1, gx + 1, gy - 3)
        i += 1


def _backdrop_jungle(rid, z):
    salt = _salt(rid)
    sky = mix(z[0], z[1], 0.5)
    far = mix(sky, shade(z[5], 1.15), 0.4)
    far_l = shade(far, 1.3)
    mid = shade(z[5], 0.55)
    mid_l = shade(z[5], 0.95)
    mid_d = shade(z[5], 0.36)
    near = shade(z[4], 0.75)
    stone = mix(sky, z[3], 0.62)
    stone_l = shade(z[3], 1.05)
    stone_d = shade(z[2], 0.55)
    bark = shade(z[2], 0.88)
    bark_d = z[4]
    shaft = mix(sky, z[6], 0.28)
    core = mix(sky, z[6], 0.5)
    _fill(sky)
    _zenith(mix(sky, shade(z[6], 0.55), 0.28), 64 + (salt % 14))
    _ridge(132 + (salt % 22), 8, 36, far_l, far, shade(far, 0.8), simple=True)
    if rid == "A1":
        px, ph, steps = 236, 58, 3
    elif rid in ("A0", "A4"):
        px, ph, steps = 28 + (salt % 48), 116, 5
    else:
        px = 24 if (salt & 1) else 200
        px = px + (salt % 36)
        ph, steps = 48 + (salt % 22), 3
    _pyramid(px, 188, ph, stone_l, stone, stone_d, steps)
    if rid in ("A0", "A4"):
        _tri(shade(z[6], 0.75), px - 10, 188 - ph + 8, px + 12, 188 - ph + 12, px, 188 - ph - 10)
    elif rid != "A1":
        _pyramid((px + 150) % 200 + 40, 170, max(34, ph // 2), shade(stone, 1.1), shade(stone, 0.8), stone_d, 3)
    nshaft = 5 if rid in ("A0", "A2", "A5") else 4
    s = 0
    while s < nshaft:
        sx = 8 + s * (300 // nshaft) + (salt // (3 + s)) % 18
        if rid == "A1" and 20 < sx < 140:
            sx = 160 + s * 28
        _shaft(sx, HUD, 120 + (salt + s * 23) % 70, 22 + (s & 1) * 10, shaft, core)
        s += 1
    if rid == "A1":
        count = 3
    elif rid == "A6":
        count = 2
    elif rid in ("A7", "A10"):
        count = 5
    else:
        count = 4
    gap = 300 // max(1, count)
    t = 0
    while t < count:
        tx = 6 + (salt % 16) + t * gap + random.randint(-8, 10)
        if rid == "A1" and tx < 150:
            tx = 168 + t * 36
        if rid in ("A0", "A4") and abs(tx - px) < 50:
            tx = px + 80
        _tree(tx, 236, 58 + (salt + t * 17) % 36, mid_l, mid, mid_d, bark, bark_d)
        t += 1
    if rid == "A7":
        _tree(150, 240, 96, mid_l, mid, mid_d, bark, bark_d)
    if rid == "A1":
        _teeth(HUD, 6, 22, near, True, 150, 330)
    else:
        _teeth(HUD, 10, 28, near, True)
        _teeth(HUD + 2, 5, 14, shade(near, 0.7), True)
    if rid == "A7":
        vines = 10
    elif rid == "A6":
        vines = 9
    elif rid == "A1":
        vines = 4
    else:
        vines = 6
    v = 0
    while v < vines:
        vx = (salt * (v + 2) + v * 53) % 310
        if rid == "A1" and 16 < vx < 140:
            vx = 155 + (vx % 150)
        _vine(vx, HUD, 34 + (salt + v * 13) % (90 if rid == "A6" else 58), near, mid_d, mid)
        v += 1
    if rid == "A1":
        _ceiba_tree(z)


def _opening(cx, cy, rx, ry, sky, rim, hot):
    _tri(rim, cx - rx - 10, cy + ry, cx - rx // 4, cy + 6, cx - rx, cy - ry // 2)
    _tri(rim, cx + rx + 12, cy + ry // 2, cx + rx // 4, cy + 4, cx + rx, cy - ry)
    _tri(rim, cx - rx // 2, cy - ry - 8, cx + rx // 2, cy - ry - 2, cx, cy - 2)
    _tri(sky, cx - (rx * 2) // 3, cy + 2, cx + (rx * 2) // 3, cy, cx, cy - (ry * 3) // 4)
    _tri(sky, cx - rx // 2, cy + 6, cx + rx // 3, cy + 8, cx + 4, cy + ry // 2)
    _tri(hot, cx - rx // 4, cy, cx + rx // 5, cy + 2, cx, cy - ry // 2)


def _root(x, y, ln, dark, mid):
    mx = x + random.randint(-14, 14)
    my = y + ln // 2
    ex = mx + random.randint(-10, 10)
    ey = y + ln
    _tri(mid, x - 3, y, x + 4, y, mx, my)
    _tri(dark, mx - 3, my, mx + 4, my, ex, ey)
    _tri(dark, ex - 6, ey, ex + 4, ey, ex - 1, ey + 9)
    _tri(mid, ex - 2, ey, ex + 5, ey + 1, ex + 8, ey + 8)


def _backdrop_cenote(rid, z):
    salt = _salt(rid)
    sky = mix(z[0], z[1], 0.42)
    far = mix(sky, z[3], 0.58)
    far_l = shade(far, 1.22)
    mid = mix(z[1], z[3], 0.78)
    mid_l = shade(mid, 1.18)
    mid_d = shade(mid, 0.62)
    near = shade(z[4], 0.62)
    root_c = shade(mix(z[5], z[4], 0.45), 0.9)
    root_d = shade(z[4], 0.5)
    hole = mix(z[1], z[6], 0.5)
    hole_h = shade(z[6], 0.85)
    _fill(sky)
    # far wall slabs, pale
    ox = 70 + (salt % 120)
    _tri(far, ox - 40, 48, ox + 90, 36, ox + 10, 190)
    _tri(far_l, ox - 10, 40, ox + 60, 44, ox + 16, 150)
    _tri(shade(far, 0.85), 210 + (salt % 30), 50, 330, 40, 260, 180)
    deep = rid in ("B3", "B4", "B9", "B10")
    mouth = rid in ("B1", "B12", "B11")
    if mouth:
        _opening(100 + (salt % 70), 40, 86, 34, hole, mid_d, hole_h)
        _shaft(120 + (salt % 40), 52, 176, 30, mix(sky, z[6], 0.22), mix(sky, z[6], 0.42))
    elif deep:
        _shaft(80 + (salt % 120), HUD, 110, 9, mix(z[0], z[6], 0.2), shade(z[6], 0.35))
    else:
        _opening(ox, 32, 44, 18, mix(z[1], z[6], 0.3), far, shade(z[6], 0.55))
        _shaft(ox, 40, 130, 16, mix(sky, z[6], 0.16), mix(sky, z[6], 0.32))
    # far short stalactites, then longer mid ones
    i = 0
    nfar = 4 if mouth else 6
    while i < nfar:
        _stal(10 + i * (300 // nfar) + random.randint(-6, 8), HUD, 10, 16 + (salt + i * 5) % 18, far_l, far, shade(far, 0.75))
        i += 1
    nstal = 5 if mouth else (9 if deep else 7)
    i = 0
    while i < nstal:
        h = (28 if mouth else 46) + (salt + i * 19) % (36 if not deep else 70)
        _stal((salt + i * 41) % 300, HUD, 12 + (i & 1) * 6, h, mid_l, mid, mid_d)
        i += 1
    piers = 1 if mouth else (3 if rid in ("B6", "B2", "B8") else 2)
    p = 0
    while p < piers:
        px = 48 + p * (200 // max(1, piers)) + (salt // (4 + p)) % 24
        _pillar(px, 70 + (p & 1) * 18, 228, 14, mid_l, mid, mid_d)
        p += 1
    roots = 4 if mouth else (9 if deep else 6)
    r = 0
    while r < roots:
        _root((salt * (r + 3)) % 304, HUD, 40 + (salt + r * 17) % 90, root_d, root_c)
        r += 1
    if rid in ("B5", "B11"):
        fx = 246 if rid == "B11" else 40
        y = 28
        while y < 200:
            _tri(mix(z[7], hole, 0.4), fx, y, fx + 16, y + 3, fx + 7, y + 18)
            _tri(shade(z[6], 0.5), fx + 4, y + 2, fx + 12, y + 4, fx + 7, y + 16)
            y += 18
    jaw = 36 + (salt % 28)
    _tri(near, 0, HUD, jaw, HUD + 8, 0, 120 + (salt % 40))
    _tri(near, 0, 150, jaw - 8, 210, 0, 239)
    _tri(near, 319, HUD, 319 - jaw, HUD + 12, 319, 140)
    _tri(near, 300, 190, 319, 150, 319, 239)
    _teeth(200 + (salt % 16), 7, 26 + (salt % 12), near, False)
    g = 0
    glints = 14 if rid == "B12" else 8
    while g < glints:
        _glint(16 + (salt * (g + 1)) % 290, 110 + (g * 23 + salt) % 100, shade(z[6], 0.9), 2 + (g & 1))
        g += 1


def _backdrop_temple(rid, z):
    salt = _salt(rid)
    sky = mix(z[0], z[1], 0.62)
    far = mix(sky, z[3], 0.4)
    far_l = shade(far, 1.24)
    wall = mix(z[2], z[1], 0.45)
    wall_l = shade(z[3], 0.9)
    wall_d = shade(z[4], 0.9)
    near = shade(z[4], 0.55)
    hot = z[6]
    warm = mix(wall, hot, 0.34)
    _fill(sky)
    _zenith(mix(sky, hot, 0.12), 48)
    throne = rid == "C2"
    colonnade = rid == "C8"
    _blocks(5 if throne else 7, 28, 90, far_l, far, shade(far, 0.75), salt)
    _blocks(6 if throne else 9, 70, 180, wall_l, wall, wall_d, salt // 3 + 5, True)
    bx = 70 + (salt % 40)
    bx2 = 210 + (salt % 36)
    _shaft(bx, 150, 28, 18, warm, mix(warm, hot, 0.55))
    _shaft(bx2, 162, 34, 16, warm, mix(warm, hot, 0.5))
    if throne or rid == "C1":
        _shaft(156, 136, 24, 20, warm, mix(hot, warm, 0.5))
    fy = 46 + (salt % 10)
    _tri(wall_d, 0, fy + 1, 170, fy + 4, 0, fy + 14)
    _tri(wall_d, 150, fy + 3, 319, fy, 319, fy + 14)
    _frieze(8, fy + 2, 14, 22, shade(hot, 0.7), wall_l, wall_d)
    if rid in ("C6", "C9"):
        fy2 = fy + 26
        _tri(wall_d, 0, fy2, 160, fy2 + 2, 0, fy2 + 13)
        _tri(wall_d, 150, fy2 + 2, 319, fy2, 319, fy2 + 13)
        _frieze(18, fy2 + 1, 12, 24, wall_l, wall, wall_d)
    if colonnade:
        cols = (12, 74, 140, 206, 272)
    elif throne:
        cols = (18, 262)
    elif rid == "C9":
        cols = (16, 292)
    else:
        cols = (20, 108, 212, 300)
    for x in cols:
        _pillar(x, 18, 234, 16 if not colonnade else 12, wall_l, wall, wall_d)
    if rid in ("C1", "C2", "C5"):
        _mask(160, 86 if throne else 96, shade(wall, 0.72), wall_d, near, shade(hot, 1.35), 2 if throne else 1)
    _flame(bx + 6, 158, shade(hot, 1.2), hot, shade(hot, 0.38))
    _flame(bx2 + 4, 170, shade(hot, 1.2), hot, shade(hot, 0.38))
    if rid in ("C2", "C6", "C1"):
        _flame(160, 148, shade(hot, 1.25), hot, shade(hot, 0.4))
    _teeth(HUD, 9, 18, near, True)
    _tri(near, 0, HUD, 32, 36, 0, 190)
    _tri(near, 292, 40, 319, HUD, 319, 200)
    _tri(near, 0, 220, 48, 239, 0, 239)
    _tri(near, 270, 239, 319, 214, 319, 239)


def _eyes(x, y, col):
    _tri(col, x, y, x + 6, y + 1, x + 2, y - 4)
    _tri(col, x + 9, y + 1, x + 15, y, x + 11, y - 4)


def _vein(x, y, n, col, glow):
    cx, cy = x, y
    i = 0
    while i < n:
        nx = max(0, min(319, cx + random.randint(-20, 28)))
        ny = cy + random.randint(12, 26)
        _tri(glow, cx - 4, cy, cx + 5, cy, nx, ny)
        _tri(col, cx - 1, cy, cx + 2, cy, nx, ny)
        cx, cy = nx, ny
        i += 1


def _backdrop_dread(rid, z):
    salt = _salt(rid)
    sky = mix(z[0], z[1], 0.78)
    far = mix(sky, z[3], 0.26)
    far_l = shade(far, 1.2)
    mid = mix(z[2], z[1], 0.5)
    mid_l = shade(z[3], 0.72)
    mid_d = shade(z[4], 0.8)
    near = shade(z[0], 0.45)
    vein_c = z[6]
    vein_g = shade(z[6], 0.38)
    _fill(sky)
    # far hall: a flat wall and piers, not a peak
    _tri(far, 36, 200, 284, 192, 150, 70)
    _tri(far_l, 80, 170, 240, 164, 160, 78)
    _tri(shade(far, 0.8), 24, 48, 150, 40, 40, 120)
    _tri(shade(far, 0.8), 170, 44, 300, 36, 280, 124)
    _pillar(28, 30, 220, 14, far_l, far, shade(far, 0.7))
    _pillar(268, 34, 224, 14, far_l, far, shade(far, 0.7))
    _tri(mid_d, 20, 46, 300, 40, 160, 64)
    _tri(mid, 40, 38, 280, 36, 160, 52)
    _blocks(4, 80, 150, shade(far_l, 0.9), far, mid_d, salt)
    _vein(20 + (salt % 30), 28, 5, vein_c, vein_g)
    _vein(170 + (salt % 40), 32, 5, vein_c, vein_g)
    if rid not in ("F6",):
        _vein(60 + (salt % 80), 90, 4, shade(vein_c, 0.8), vein_g)
    statues = 3 if rid in ("F3", "F5", "F7") else 2
    if rid == "F6":
        statues = 1
    big = rid in ("F1", "F2", "F4")
    if rid != "F3":
        _mask(158 + (salt % 16) - 8, 92, mid_l, mid, shade(z[0], 0.7), vein_c, 2 if big else 1)
    else:
        _mask(90, 100, mid_l, mid, shade(z[0], 0.7), vein_c, 1)
        _mask(220, 108, mid_l, mid, shade(z[0], 0.7), vein_c, 1)
    if rid == "F6":
        e = 0
        while e < 6:
            _eyes(18 + e * 50, 40 + (e & 1) * 36, vein_c)
            e += 1
    else:
        _eyes(18 + (salt % 20), 36, shade(vein_c, 0.75))
        _eyes(270, 48, shade(vein_c, 0.75))
    _tri(mid_d, 8, 130, 120, 158, 30, 172)
    _tri(near, 200, 124, 318, 148, 230, 166)
    if statues == 1:
        spots = (160,)
    elif statues == 2:
        spots = (78, 236)
    else:
        spots = (64, 160, 250)
    s = 0
    while s < statues:
        broken = ((salt >> s) & 1) == 1 or rid in ("F5", "F7")
        _statue(spots[s], 188, shade(z[3], 1.15), z[3], shade(z[4], 0.6), broken, 2)
        s += 1
    _teeth(HUD, 8, 20, near, True)
    _tri(near, 0, HUD, 30, 70, 0, 210)
    _tri(near, 290, 60, 319, HUD, 319, 220)
    _teeth(210, 6, 22, near, False)


def _sun(cx, cy, r, lit, mid):
    ray = r // 2
    _tri(mid, cx - r, cy + r // 4, cx + r, cy + r // 4, cx, cy - r // 2)
    _tri(lit, cx - r // 2, cy, cx + r // 2, cy, cx, cy - r // 2)
    _tri(lit, cx - 2, cy - r // 4, cx + 2, cy - r // 4, cx, cy - r // 2 - ray)
    _tri(lit, cx - r // 3, cy, cx - r // 3, cy + 2, cx - r // 2 - ray, cy)
    _tri(lit, cx + r // 3, cy, cx + r // 3, cy + 2, cx + r // 2 + ray, cy)
    _tri(mid, cx - 2, cy + 1, cx + 2, cy + 1, cx, cy + r // 2)


def _bolt(x, y, ln, col):
    cx, cy = x, y
    i = 0
    while i < 5:
        nx = cx + (10 if (i & 1) == 0 else -8)
        ny = cy + ln // 5
        _tri(col, cx, cy, cx + 3, cy + 1, nx, ny)
        cx, cy = nx, ny
        i += 1


def _streak(x, y, ln, c):
    _tri(c, x, y, x + ln, y - 2, x + ln - 14, y + 3)


def _backdrop_mountain(rid, z):
    salt = _salt(rid)
    storm = rid in ("D3", "D9")
    sky = z[0] if storm else mix(z[0], z[1], 0.3)
    horizon = shade(z[1], 0.8 if storm else 1.0)
    far = mix(sky, z[1], 0.5)
    far_l = shade(far, 1.24)
    mid = mix(z[2], z[1], 0.4)
    mid_l = shade(z[3], 0.95)
    mid_d = shade(z[4], 0.85)
    near = shade(z[4], 0.5)
    snow = z[5]
    snow_d = shade(z[5], 0.8)
    wind = mix(horizon, z[6], 0.35)
    _fill(sky)
    _tri(horizon, -40, 156, 180, 184, 10, 78)
    _tri(horizon, 100, 168, 360, 150, 260, 84)
    if rid == "D4":
        _sun(70 + (salt % 30), 52, 22, shade(z[6], 1.3), snow)
    elif not storm and rid not in ("D6", "D1"):
        _sun(230 + (salt % 24) - 10, 44, 11, shade(z[6], 1.15), snow_d)
    _ridge(156, 6, 48, far_l, far, shade(far, 0.78), snow_d, simple=True)
    clouds = 6 if storm or rid == "D1" else 4
    c = 0
    while c < clouds:
        _cloud((salt + c * 68) % 260, 28 + (c * 9 + salt) % 26, 34 + (c & 1) * 18,
               snow, mix(snow, z[1], 0.3), shade(z[1], 0.65))
        c += 1
    _ridge(230, 4, 120, mid_l, mid, mid_d, snow, simple=False)
    if rid == "D6":
        _teeth(HUD, 7, 44, mid_d, True)
        _tri(mid_d, 0, HUD, 90, HUD, 10, 110)
        _tri(mid_d, 230, HUD, 319, HUD, 300, 120)
    _ridge(252, 7, 48, shade(near, 1.2), near, shade(near, 0.65), snow if rid in ("D2", "D4", "D7", "D8") else None)
    streaks = 11 if rid in ("D2", "D6", "D8", "D9") else 6
    s = 0
    while s < streaks:
        _streak((salt * (s + 1)) % 200, 34 + (s * 13 + salt) % 100, 48 + (s * 9) % 46, wind)
        s += 1
    if storm:
        _bolt(60 + (salt % 70), 18, 100, shade(z[6], 1.4))
        if rid == "D9":
            _bolt(210, 24, 80, snow)
    if rid == "D1":
        _tri(mix(horizon, snow, 0.35), -10, 120, 160, 140, 40, 100)
        _tri(mix(horizon, snow, 0.28), 140, 130, 330, 126, 220, 108)


def _river(y, lit, mid, dark, n):
    step = 340 // n
    x = -16
    i = 0
    while i < n:
        _tri(dark, x, y - 4, x + step + 20, y - 8, x + step // 2, y + 20)
        _tri(mid, x + 2, y + 1, x + step + 12, y - 1, x + step // 2, y + 16)
        x += step
        i += 1
    x = -8
    i = 0
    while i < n:
        _tri(lit, x + step // 5, y + 3, x + (step * 4) // 5, y + 2, x + step // 2, y + 12)
        x += step
        i += 1


def _bat(x, y, col):
    _tri(col, x - 8, y + 3, x, y, x - 2, y - 4)
    _tri(col, x + 8, y + 3, x, y, x + 2, y - 4)
    _tri(col, x - 2, y, x + 2, y + 3, x, y - 3)


def _ember(x, y, hot, mid):
    _tri(mid, x - 4, y + 3, x + 4, y + 3, x, y - 7)
    _tri(hot, x - 2, y, x + 2, y + 1, x, y - 6)


def _backdrop_xibalba(rid, z):
    salt = _salt(rid)
    cold = rid == "E5"
    sky = mix(z[0], z[1], 0.26 if cold else 0.48)
    far = mix(sky, z[3], 0.34)
    far_l = shade(far, 1.28)
    mid = shade(z[2], 0.72)
    mid_l = shade(z[3], 0.9)
    mid_d = shade(z[4], 0.75)
    near = shade(z[0], 0.55)
    hot = shade(z[6], 0.4 if cold else 1.0)
    hot_l = shade(z[6], 0.65 if cold else 1.25)
    bone = shade(mix(z[3], z[5], 0.25), 1.45)
    bone_l = shade(bone, 1.2)
    _fill(sky)
    i = 0
    while i < 9:
        x = -24 + i * 42 + random.randint(-4, 6)
        h = 36 + (salt + i * 11) % 28
        _tri(far, x, 188, x + 18, 198, x + 6, 188 - h)
        _tri(far_l, x + 3, 160, x + 12, 168, x + 6, 192 - h)
        i += 1
    spires = 7 if rid == "E2" else 5
    i = 0
    while i < spires:
        x = 16 + i * (300 // spires) + random.randint(-6, 8)
        h = 100 + (salt + i * 23) % 60
        if rid == "E2":
            h += 30
        _spire(x, 240, h, 16 + (i & 1) * 8, mid_l, mid, mid_d)
        if i & 1:
            _ember(x, 240 - h + 16, hot_l, hot)
        i += 1
    bank = shade(z[4], 0.65)
    blood = shade(hot, 0.5 if cold else 0.8)
    blood_l = shade(hot_l, 0.55 if cold else 1.0)
    ry = 150 if rid == "E3" else 178
    # gorge lip above the river
    _teeth(ry - 16, 8, 20, bank, True)
    _river(ry, blood_l, blood, shade(hot, 0.35), 10 if rid == "E3" else 8)
    embers = 2 if cold else (7 if rid in ("E1", "E2") else 4)
    e = 0
    while e < embers:
        _ember(24 + (salt * (e + 2)) % 270, 36 + (salt + e * 31) % 90, hot_l, hot)
        e += 1
    if rid in ("E2", "E6"):
        _skull(164, 72, bone, bone_l, near, 3)
    _skull(34 + (salt % 16), 112, bone, bone_l, near, 2)
    _skull(246, 104, bone, bone_l, near, 2)
    if rid in ("E4", "E7", "E3"):
        _skull(150, 126, bone, bone_l, near, 1)
    if rid == "E7":
        b = 0
        while b < 7:
            _bat(24 + b * 44 + random.randint(-4, 6), 30 + (b & 1) * 16, near)
            b += 1
    _teeth(HUD, 7, 24 if rid != "E4" else 46, near, True)
    jaw = 40 + (salt % 24)
    _tri(near, 0, HUD, jaw, HUD + 16, 0, 180)
    _tri(near, 319 - jaw, HUD + 10, 319, HUD, 319, 190)
    _tri(near, 0, 214, 80, 239, 0, 239)
    _tri(near, 240, 239, 319, 206, 319, 239)


BACKDROPS = {
    "jungle": _backdrop_jungle,
    "cenote": _backdrop_cenote,
    "temple": _backdrop_temple,
    "dread": _backdrop_dread,
    "mountain": _backdrop_mountain,
    "xibalba": _backdrop_xibalba,
}
