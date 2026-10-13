"""Low-poly enemies and the cenote lurker (screen coords)."""
import math
from .hw import display
from .gfx import pen, shade, HUD, WHITE, BLACK, GOLD, RED, CREAM, ORANGE
from .rig import tri, poly, joint, sin64


def _tone(c, k):
    return pen(*shade(c, k))


def _ink(flash, c):
    return WHITE if flash else c


def _t(x0, y0, x1, y1, x2, y2):
    tri(0, 0, 1, int(x0), int(y0), int(x1), int(y1), int(x2), int(y2))


def _mir(f, a):
    if f > 0:
        return a
    return math.pi - a


def _bone(x, y, ang, ln, w, lit, mid, dark):
    """One scale: dark belly, mid shard, lit crest. Three triangles."""
    ex, ey = joint(x, y, ang, ln)
    c = math.cos(ang)
    s = math.sin(ang)
    mx = x + c * ln * 0.62
    my = y + s * ln * 0.62
    px = -s * w
    py = c * w
    display.set_pen(dark)
    _t(x, y + 1, ex, ey + 1, mx + px * 0.25, my + py * 0.25 + w)
    display.set_pen(mid)
    _t(x, y, ex, ey, mx - px * 0.7, my - py * 0.7)
    display.set_pen(lit)
    _t(x, y, mx + px * 0.15, my - w, ex, ey)
    return ex, ey


def _bone2(x, y, ang, ln, w, mid, dark):
    ex, ey = joint(x, y, ang, ln)
    c = math.cos(ang)
    s = math.sin(ang)
    mx = x + c * ln * 0.55
    my = y + s * ln * 0.55
    px = -s * w
    py = c * w
    display.set_pen(dark)
    _t(x, y + 1, ex, ey + 1, mx + px * 0.3, my + py * 0.3 + w)
    display.set_pen(mid)
    _t(x, y, ex, ey, mx - px * 0.55, my - py * 0.55 - w * 0.4)
    return ex, ey


_FROG = (40, 120, 255)
FROG = pen(*_FROG)
FROG_L = _tone(_FROG, 1.6)
FROG_D = _tone(_FROG, 0.45)
FROG_DD = _tone(_FROG, 0.26)
TOE = pen(255, 145, 24)
TOE_D = pen(160, 62, 14)

_SNAKE = (210, 180, 40)
SNAKE = pen(*_SNAKE)
SNAKE_L = _tone(_SNAKE, 1.3)
SNAKE_D = _tone(_SNAKE, 0.42)
_BAND = (130, 74, 22)
BAND = pen(*_BAND)
BAND_L = _tone(_BAND, 1.5)
BAND_D = _tone(_BAND, 0.4)

_BAT = (100, 70, 130)
BAT = pen(*_BAT)
BAT_L = _tone(_BAT, 1.65)
BAT_D = _tone(_BAT, 0.48)
BAT_DD = _tone(_BAT, 0.26)

_EEL = (60, 170, 140)
EEL = pen(*_EEL)
EEL_L = _tone(_EEL, 1.4)
EEL_D = _tone(_EEL, 0.4)
EEL_DD = _tone(_EEL, 0.22)
EEL_EYE = pen(255, 230, 70)

_CLAY = (190, 100, 60)
CLAY = pen(*_CLAY)
CLAY_L = _tone(_CLAY, 1.38)
CLAY_D = _tone(_CLAY, 0.52)
CLAY_DD = _tone(_CLAY, 0.3)
_FEAT = (32, 176, 96)
FEAT = pen(*_FEAT)
FEAT_D = _tone(_FEAT, 0.4)
_SP = (176, 186, 198)
SP_D = _tone(_SP, 0.45)
_OBS = (28, 30, 38)
OBS = pen(*_OBS)
GOLD_L = _tone((255, 200, 60), 1.15)
GOLD_D = _tone((255, 200, 60), 0.48)

_MASK = (124, 112, 100)
MASK = pen(*_MASK)
MASK_L = _tone(_MASK, 1.5)
MASK_D = _tone(_MASK, 0.5)
MASK_DD = _tone(_MASK, 0.28)
FIRE = pen(255, 96, 16)
FIRE_L = pen(255, 220, 130)
FIRE_D = pen(110, 28, 8)

_SWIFT = (206, 214, 232)
SWIFT = pen(*_SWIFT)
SWIFT_L = _tone(_SWIFT, 1.12)
SWIFT_D = _tone(_SWIFT, 0.55)
SWIFT_DD = _tone(_SWIFT, 0.34)

_WISP = (150, 90, 230)
WISP = pen(*_WISP)
WISP_L = _tone(_WISP, 1.45)
WISP_D = _tone(_WISP, 0.4)
WISP_DD = _tone(_WISP, 0.2)
WISP_C = pen(240, 224, 255)
EMBER = pen(255, 140, 40)
EMBER_L = pen(255, 214, 140)

_LURK = (16, 52, 78)
LURK = pen(*_LURK)
LURK_L = pen(64, 176, 196)
LURK_D = pen(5, 16, 30)
LURK_DD = pen(2, 8, 16)
MAW = pen(180, 26, 34)

_MASK_CORE = ((-6, -2), (-3, -6), (2, -7), (6, -3), (6, 3), (2, 6), (-3, 6), (-6, 2))
_MASK_FACE = ((-6, -3), (-2, -6), (3, -5), (6, 0), (4, 5), (-1, 6), (-5, 4), (-6, 0))
_FROG_BODY = ((-6, -1), (-4, -4), (0, -3), (4, -4), (6, 0), (5, 4), (1, 6), (-3, 5), (-6, 2))
_FROG_HEAD = ((-2, -5), (2, -6), (5, -2), (3, 1), (-1, 0), (-3, -2))
_BAT_BODY = ((-4, -1), (0, -3), (4, 0), (3, 4), (-1, 5), (-4, 2))
_WAR_BODY = ((-6, -3), (2, -5), (6, -1), (5, 4), (1, 8), (-5, 6), (-6, 1))
_WAR_HEAD = ((-4, -2), (0, -5), (4, -2), (3, 3), (-1, 4), (-4, 1))
_SWIFT_BODY = ((-5, -1), (2, -3), (6, -1), (4, 2), (-1, 3), (-5, 1))
_WISP_CORE = ((-4, 0), (-1, -4), (3, -3), (4, 2), (0, 4), (-4, 2))
_LURK_HEAD = ((-3, -3), (3, -4), (8, -1), (7, 3), (1, 4), (-3, 1))
# w, neck drop, wave phase, band index. Head first, tail last.
_SNAKE_SEG = ((4, 0.55, 0, 0), (4, 0.22, 7, 1), (3, 0.08, 14, 0), (3, 0.0, 21, 1), (2, -0.08, 28, 0))
_SNAKE_HEAD = ((-2, 0), (3, -3), (5, 0), (2, 3), (-2, 2))
_SNAKE_BANDS = ((SNAKE_L, SNAKE, SNAKE_D), (BAND_L, BAND, BAND_D), (SNAKE_L, SNAKE, SNAKE_D))
_SNAKE_FLASH = ((WHITE, WHITE, WHITE), (WHITE, WHITE, WHITE), (WHITE, WHITE, WHITE))


def _frog(e, x, y, t, flash):
    f = e.face
    leap = e.vy < 0
    lit = _ink(flash, FROG_L)
    mid = _ink(flash, FROG)
    dark = _ink(flash, FROG_D)
    deep = _ink(flash, FROG_DD)
    cx, cy = x + 6, y + 6
    if leap:
        a1, a2, l1, l2, arm = 2.65, 3.0, 6, 5, 0.3
        cy -= 1
    else:
        a1, a2, l1, l2, arm = 2.05, 0.85, 4, 3, 1.15
        cy += int(sin64(t * 3 + 16))
    hipx, hipy = cx - f * 2, cy + 2
    knee = joint(hipx, hipy + 1, _mir(f, a1 + 0.4), l1 - 1)
    foot = joint(knee[0], knee[1], _mir(f, a2 + 0.35), l2)
    display.set_pen(deep)
    _t(hipx, hipy, knee[0], knee[1], foot[0], foot[1])
    display.set_pen(dark)
    _t(knee[0], knee[1], foot[0], foot[1], foot[0] - f, foot[1] + 2)
    knee = joint(hipx, hipy, _mir(f, a1), l1)
    foot = joint(knee[0], knee[1], _mir(f, a2), l2)
    display.set_pen(dark)
    _t(hipx, hipy, knee[0], knee[1], knee[0], knee[1] + 2)
    display.set_pen(mid)
    _t(knee[0], knee[1], foot[0], foot[1], foot[0] + f * 2, foot[1] + 1)
    display.set_pen(lit)
    _t(hipx, hipy - 1, knee[0], knee[1] - 1, foot[0], foot[1] - 1)
    display.set_pen(TOE)
    _t(foot[0], foot[1], foot[0] + f * 3, foot[1] + 2, foot[0] - f, foot[1] + 2)
    display.set_pen(deep)
    poly(_FROG_BODY, cx, cy, f)
    display.set_pen(dark)
    tri(cx, cy, f, -5, 2, 0, 6, 5, 2)
    display.set_pen(mid)
    tri(cx, cy, f, -6, -1, 1, -3, 6, 2)
    display.set_pen(lit)
    tri(cx, cy, f, -3, -2, 2, -5, 4, -1)
    display.set_pen(mid)
    poly(_FROG_HEAD, cx + f * 2, cy - 1, f)
    display.set_pen(lit)
    tri(cx, cy, f, 1, -4, 5, -3, 3, 0)
    display.set_pen(dark)
    tri(cx, cy, f, 2, 0, 7, 2, 3, 3)
    hand = joint(cx + f * 3, cy + 2, _mir(f, arm), 3)
    display.set_pen(dark)
    _t(cx + f * 2, cy + 1, hand[0], hand[1], hand[0], hand[1] + 2)
    display.set_pen(mid)
    _t(cx + f * 3, cy, hand[0], hand[1] - 1, cx + f * 4, cy + 2)
    display.set_pen(TOE_D)
    _t(hand[0], hand[1], hand[0] + f * 2, hand[1] + 1, hand[0], hand[1] + 2)
    display.set_pen(WHITE)
    display.circle(int(cx - f), int(cy - 3), 2)
    display.circle(int(cx + f * 2), int(cy - 3), 3)
    display.set_pen(BLACK)
    display.circle(int(cx - f + f), int(cy - 3), 1)
    display.circle(int(cx + f * 3), int(cy - 3), 1)


def _snake(e, x, y, t, flash):
    f = e.face
    strike = e.state == 1
    amp = 0.12 if strike else 0.32
    stretch = 4 if strike else 3
    back = math.pi if f > 0 else 0.0
    hx = x + 7 + f * 4
    hy = y + 2
    cols = _SNAKE_FLASH if flash else _SNAKE_BANDS
    px, py = hx, hy
    i = 0
    while i < 5:
        w, drop, phase, band = _SNAKE_SEG[i]
        wave = sin64(t * 3 + phase) * amp
        lit, mid, dark = cols[band]
        px, py = _bone(px, py, back - f * (drop + wave), stretch + (1 if i < 2 else 0), w, lit, mid, dark)
        if i == 2:
            display.set_pen(dark)
            _t(px, py - 1, px - f, py - 4, px + f * 2, py - 1)
        i += 1
    display.set_pen(_ink(flash, SNAKE_D))
    poly(_SNAKE_HEAD, hx, hy, f)
    display.set_pen(_ink(flash, SNAKE))
    _t(hx, hy + 1, hx + f * 4, hy + 2, hx + f, hy + 3)
    display.set_pen(_ink(flash, SNAKE_L))
    _t(hx - f, hy - 1, hx + f * 4, hy - 3, hx + f * 2, hy + 1)
    display.set_pen(BLACK)
    display.circle(int(hx + f), int(hy - 1), 1)
    display.set_pen(CREAM)
    display.pixel(hx + f * 2, hy - 2)
    flick = 4 if (t & 8) else 3
    display.set_pen(RED)
    _t(hx + f * 3, hy + 1, hx + f * (3 + flick), hy - 1, hx + f * (2 + flick), hy + 2)


def _wing(cx, cy, a1, a2, l1, l2, w, lit, mid, dark, layers):
    elbow = joint(cx, cy, a1, l1)
    tip = joint(elbow[0], elbow[1], a2, l2)
    ex, ey = elbow
    tx, ty = tip
    px = -math.sin(a1) * w
    py = math.cos(a1) * w
    display.set_pen(dark)
    _t(cx, cy, tx, ty, ex + px, ey + py + w * 0.35)
    if layers > 1:
        display.set_pen(mid)
        _t(cx, cy, ex, ey, tx, ty)
    if layers > 2:
        display.set_pen(lit)
        _t(cx, cy - 1, ex - px * 0.4, ey - w * 0.7, tx, ty)
    return tx, ty


def _bat_wing(cx, cy, side, spread, membrane, bone, edge):
    """side -1 is screen left. Two bones, membrane then a lit leading edge."""
    a1 = math.pi + spread if side < 0 else -spread
    a2 = math.pi + spread * 0.4 if side < 0 else -spread * 0.4
    elbow = joint(cx, cy, a1, 7)
    tip = joint(elbow[0], elbow[1], a2, 6)
    ex, ey = elbow
    tx, ty = tip
    px = -math.sin(a1) * 4
    py = math.cos(a1) * 4
    display.set_pen(membrane)
    _t(cx, cy, ex, ey, ex + px, ey + py)
    _t(ex, ey, tx, ty, tx + px * 0.6, ty + py * 0.6)
    display.set_pen(bone)
    _t(cx, cy, ex, ey, tx, ty)
    display.set_pen(edge)
    _t(cx, cy - 1, ex, ey - 2, tx, ty)
    return tx, ty


def _bat(e, x, y, t, flash):
    flap = sin64(t * 4 + 16)
    spread = 0.5 + flap * 0.45
    lit = _ink(flash, BAT_L)
    mid = _ink(flash, BAT)
    dark = _ink(flash, BAT_D)
    deep = _ink(flash, BAT_DD)
    cx, cy = x + 6, y + 4
    _bat_wing(cx, cy, -1, spread + 0.12, dark, mid, mid)
    tip = _bat_wing(cx, cy, 1, spread, dark, mid, lit)
    display.set_pen(deep)
    poly(_BAT_BODY, cx, cy + 1, 1)
    display.set_pen(mid)
    _t(cx - 3, cy, cx + 2, cy - 2, cx + 3, cy + 3)
    display.set_pen(lit)
    _t(cx - 2, cy - 2, cx + 2, cy - 4, cx + 1, cy)
    display.set_pen(deep)
    _t(cx - 3, cy - 1, cx - 1, cy - 8, cx, cy)
    _t(cx + 1, cy - 1, cx + 2, cy - 8, cx + 4, cy)
    display.set_pen(lit)
    _t(cx - 2, cy - 2, cx - 1, cy - 6, cx, cy - 1)
    display.set_pen(CREAM)
    _t(cx - 1, cy + 2, cx, cy + 5, cx + 2, cy + 2)
    display.set_pen(RED)
    display.circle(cx - 1, cy - 1, 1)
    display.circle(cx + 2, cy - 1, 1)
    display.set_pen(lit)
    _t(tip[0], tip[1], tip[0] + 2, tip[1] + 1, tip[0] - 1, tip[1] + 2)


def _eel(e, x, y, t, flash):
    f = e.face
    lit = _ink(flash, EEL_L)
    mid = _ink(flash, EEL)
    dark = _ink(flash, EEL_D)
    deep = _ink(flash, EEL_DD)
    back = math.pi if f > 0 else 0.0
    hx = x + 7 + f * 2
    hy = y + 5
    a0 = sin64(t * 2) * 0.5
    a1 = sin64(t * 2 + 16) * 0.55
    a2 = sin64(t * 2 + 40) * 0.55
    px, py = _bone(hx, hy, back + a0, 5, 3, lit, mid, dark)
    rx, ry = px, py
    px, py = _bone(px, py, back + a1, 5, 2, lit, mid, dark)
    px, py = _bone(px, py, back + a2, 4, 2, lit, mid, deep)
    px, py = _bone(px, py, back + sin64(t * 2 + 52) * 0.4, 3, 2, lit, dark, deep)
    display.set_pen(deep)
    _t(px, py, px - f * 6, py - 4, px - f * 2, py)
    display.set_pen(lit)
    _t(px, py, px - f * 5, py + 4, px - f, py + 1)
    display.set_pen(mid)
    _t(rx, ry, rx - f, ry - 5, rx + f * 2, ry - 1)
    display.set_pen(lit)
    _t(hx, hy - 2, hx + f * 5, hy - 1, hx + f * 2, hy + 1)
    display.set_pen(EEL_EYE)
    display.circle(int(hx + f), int(hy - 1), 1)
    display.set_pen(BLACK)
    display.pixel(hx + f * 2, hy - 1)


def _spear(x, y, ang, reach, flash):
    """Shaft from the hand to a single obsidian leaf."""
    bx, by = joint(x, y, ang, reach)
    tx, ty = joint(x, y, ang, reach + 6)
    nx = -math.sin(ang)
    ny = math.cos(ang)
    display.set_pen(WHITE if flash else SP_D)
    display.line(int(x), int(y), int(bx), int(by))
    display.line(int(x + nx), int(y + ny), int(bx + nx), int(by + ny))
    display.set_pen(WHITE if flash else OBS)
    _t(tx, ty, bx + nx * 2.2, by + ny * 2.2, bx - nx * 1.5, by - ny * 1.5)


def _warrior(e, x, y, t, flash):
    f = e.face
    st = e.state
    step = sin64(t * 3 + 16)
    lit = _ink(flash, CLAY_L)
    mid = _ink(flash, CLAY)
    dark = _ink(flash, CLAY_D)
    deep = _ink(flash, CLAY_DD)
    if st == 1:
        lean = -f * 2
        far_a, far_b = 2.3, 1.15
        near_a, near_b = 2.0, 1.1
        a1, a2, sang, reach = -2.4, -2.05, -2.15, 11
    elif st == 2:
        lean = f * 2
        far_a, far_b = 2.5, 1.9
        near_a, near_b = 0.95, 1.2
        a1, a2, sang, reach = -0.1, 0.05, 0.0, 14
    else:
        lean = 0
        far_a, far_b = 2.1 + step * 0.3, 1.2 - step * 0.15
        near_a, near_b = 1.4 - step * 0.4, 1.05 + step * 0.25
        a1, a2, sang, reach = -1.0 + step * 0.1, -0.35, -0.5, 8
    bx = x + lean
    hx, hy = bx + 7, y + 4
    sx, sy = bx + 7 + f * 3, y + 8
    elbow = joint(sx, sy, _mir(f, a1), 5)
    hand = joint(elbow[0], elbow[1], _mir(f, a2), 4)
    if st == 1:
        _spear(hand[0], hand[1], _mir(f, sang), reach, flash)
    # far leg, one bent shard
    hk = joint(x + 5 - f, y + 15, _mir(f, far_a), 5)
    hf = joint(hk[0], hk[1], _mir(f, far_b), 4)
    display.set_pen(deep)
    _t(x + 5 - f, y + 15, hk[0], hk[1], hf[0], hf[1])
    display.set_pen(dark)
    _t(hk[0], hk[1], hf[0], hf[1], hf[0] - f, hf[1] - 1)
    # near leg, three layers
    nk = joint(x + 8 + f, y + 14, _mir(f, near_a), 5)
    nf = joint(nk[0], nk[1], _mir(f, near_b), 4)
    display.set_pen(dark)
    _t(x + 8 + f, y + 14, nk[0], nk[1], nf[0], nf[1])
    display.set_pen(mid)
    _t(x + 7 + f, y + 13, nk[0], nk[1], nk[0] - f * 3, nk[1] - 1)
    display.set_pen(lit)
    _t(nk[0], nk[1], nf[0], nf[1], nf[0] + f * 2, nf[1] - 2)
    display.set_pen(_ink(flash, FEAT_D))
    tri(hx, hy, f, 0, -1, -8, -9, -2, 2)
    display.set_pen(_ink(flash, FEAT))
    tri(hx, hy, f, -1, -2, -6, -10, 0, -1)
    display.set_pen(deep)
    poly(_WAR_BODY, bx + 7, y + 11, f)
    display.set_pen(mid)
    tri(bx + 7, y + 10, f, -6, -3, 5, -2, 3, 4)
    display.set_pen(lit)
    tri(bx + 7, y + 8, f, -3, -4, 2, -6, 4, -1)
    display.set_pen(_ink(flash, GOLD_D))
    poly(_WAR_HEAD, hx, hy, f)
    display.set_pen(_ink(flash, GOLD_L))
    tri(hx, hy, f, -3, -3, 2, -5, 3, -1)
    display.set_pen(RED if st == 1 else BLACK)
    ew = 3 if st == 1 else 2
    display.rectangle(hx - 3, hy - (1 if st == 1 else 0), ew, 2 if st == 1 else 1)
    display.rectangle(hx + 1, hy - (1 if st == 1 else 0), ew, 2 if st == 1 else 1)
    display.set_pen(dark)
    _t(sx, sy, elbow[0], elbow[1], elbow[0], elbow[1] + 2)
    display.set_pen(mid)
    _t(elbow[0], elbow[1], hand[0], hand[1], hand[0], hand[1] + 2)
    if st != 1:
        _spear(hand[0], hand[1], _mir(f, sang), reach, flash)


def _mask(e, x, y, t, flash):
    f = e.face
    glow = e.timer > 50
    oy = y + 7 + int(sin64(t * 2 + 16))
    ox = x + 7
    deep = _ink(flash, MASK_DD)
    dark = _ink(flash, MASK_D)
    stone = _ink(flash, MASK)
    lit = _ink(flash, MASK_L)
    display.set_pen(deep)
    poly(_MASK_CORE, ox + 1, oy + 2, 1)
    display.set_pen(stone)
    poly(_MASK_FACE, ox, oy, 1)
    display.set_pen(dark)
    _t(ox - 5, oy + 1, ox, oy + 7, ox + 5, oy + 2)
    display.set_pen(stone)
    _t(ox - 6, oy, ox - 1, oy - 5, ox + 5, oy + 2)
    display.set_pen(lit)
    _t(ox - 5, oy - 3, ox, oy - 8, ox + 5, oy - 2)
    display.set_pen(dark)
    _t(ox - 6, oy, ox - 11, oy - 2, ox - 5, oy + 4)
    _t(ox + 6, oy, ox + 11, oy - 2, ox + 5, oy + 4)
    _t(ox - 2, oy - 6, ox + 1, oy - 12, ox + 3, oy - 5)
    eye = FIRE_L if glow else FIRE_D
    display.set_pen(eye)
    tri(ox, oy, f, -5, -3, -2, -1, -4, 1)
    tri(ox, oy, f, 2, -3, 5, -1, 3, 1)
    display.set_pen(FIRE if glow else FIRE_D)
    _t(ox - 3, oy + 2, ox + 3, oy + 2, ox + f, oy + 6)
    if glow:
        flick = int(sin64(t * 5) * 2)
        display.set_pen(FIRE)
        _t(ox - 7, oy - 1, ox - 12, oy - 3 + flick, ox - 5, oy + 2)
        _t(ox + 7, oy - 1, ox + 12, oy - 3 - flick, ox + 5, oy + 2)
        display.set_pen(FIRE_L)
        _t(ox - 2, oy + 5, ox + 2, oy + 5, ox, oy + 11 + flick)
        display.set_pen(CREAM)
        display.pixel(ox - 3 + f, oy - 2)
        display.pixel(ox + 3 + f, oy - 2)


def _swift(e, x, y, t, flash):
    f = e.face
    dive = e.state == 1
    flap = sin64(t * 3 + 12) * (0.08 if dive else 0.3)
    up = 0.15 if dive else 0.75 + flap
    lit = _ink(flash, SWIFT_L)
    mid = _ink(flash, SWIFT)
    dark = _ink(flash, SWIFT_D)
    deep = _ink(flash, SWIFT_DD)
    cx, cy = x + 6, y + 5
    if f > 0:
        a1, a2 = math.pi + up, math.pi + up * 0.15
        b1, b2 = math.pi - 0.45 - flap, math.pi - 0.05
    else:
        a1, a2 = -up, -up * 0.15
        b1, b2 = 0.45 + flap, 0.05
    _wing(cx, cy, b1, b2, 8, 6, 3, dark, dark, deep, 2)
    tip = _wing(cx, cy, a1, a2, 9, 7, 3, lit, mid, dark, 3)
    display.set_pen(deep)
    poly(_SWIFT_BODY, cx, cy, f)
    display.set_pen(dark)
    tri(cx, cy, f, -5, 1, 2, 3, 5, 0)
    display.set_pen(mid)
    tri(cx, cy, f, -4, -1, 5, -2, 3, 2)
    display.set_pen(lit)
    tri(cx, cy, f, -2, -2, 4, -3, 3, 0)
    display.set_pen(deep)
    tri(cx, cy, f, -2, 0, -8, -4, -5, 1)
    tri(cx, cy, f, -2, 1, -8, 4, -5, 0)
    display.set_pen(ORANGE)
    tri(cx, cy, f, 3, -1, 9, 0, 4, 2)
    display.set_pen(BLACK)
    display.circle(int(cx + f * 3), int(cy - 1), 1)
    display.set_pen(SWIFT_L)
    _t(tip[0], tip[1], tip[0] - f * 3, tip[1] - 1, tip[0] - f, tip[1] + 2)


def _wisp(e, x, y, t, flash):
    f = e.face
    deep = _ink(flash, WISP_DD)
    dark = _ink(flash, WISP_D)
    mid = _ink(flash, WISP)
    lit = _ink(flash, WISP_L)
    core = _ink(flash, WISP_C)
    flick = int(sin64(t * 4 + 16) * 3)
    flick2 = int(sin64(t * 3 + 8) * 2)
    cx, cy = x + 6, y + 6
    display.set_pen(deep)
    poly(_WISP_CORE, cx, cy + 1, 1)
    _t(cx - 5, cy + 1, cx + 5, cy + 2, cx + flick, cy - 9)
    _t(cx - 6, cy, cx - 2, cy + 4, cx - 8, cy + 2 + flick2)
    _t(cx + 5, cy, cx + 1, cy + 4, cx + 8, cy + 1 - flick)
    display.set_pen(dark)
    _t(cx - 4, cy, cx + 4, cy + 1, cx + flick2, cy - 6)
    _t(cx - 4, cy + 2, cx + 3, cy + 3, cx - flick, cy + 7)
    display.set_pen(mid)
    _t(cx - 5, cy, cx + 4, cy + 1, cx + 1, cy - 4)
    _t(cx - 5, cy + 1, cx + 5, cy + 2, cx, cy + 6)
    display.set_pen(lit)
    _t(cx - 2, cy, cx + 3, cy, cx + flick, cy - 7)
    _t(cx - 2, cy + 1, cx + 2, cy + 1, cx, cy - 2)
    display.set_pen(core)
    _t(cx - 3, cy + 1, cx + 3, cy + 2, cx, cy - 3)
    display.set_pen(CREAM)
    display.circle(cx + f - 2, cy, 1)
    display.circle(cx + f + 1, cy, 1)
    display.set_pen(deep)
    _t(cx + f - 1, cy + 2, cx + f + 2, cy + 2, cx + f, cy + 4)
    display.set_pen(EMBER)
    _t(cx - 7, cy, cx - 5, cy + 1, cx - 9, cy - 3 + flick2)
    display.set_pen(EMBER_L)
    _t(cx + 5, cy + 2, cx + 8, cy + 1, cx + 7, cy + 4)


def draw_enemy(e, t):
    x = int(e.x)
    y = int(e.y) + HUD
    flash = e.flash > 0
    k = e.kind
    if k == "frog":
        _frog(e, x, y, t, flash)
    elif k == "snake":
        _snake(e, x, y, t, flash)
    elif k == "bat":
        _bat(e, x, y, t, flash)
    elif k == "eel":
        _eel(e, x, y, t, flash)
    elif k == "warrior":
        _warrior(e, x, y, t, flash)
    elif k == "mask":
        _mask(e, x, y, t, flash)
    elif k == "swift":
        _swift(e, x, y, t, flash)
    elif k == "wisp":
        _wisp(e, x, y, t, flash)


def draw_lurker(e, t):
    x = int(e.x)
    y = int(e.y) + HUD
    f = e.face
    flash = e.flash > 0
    lung = e.state == 2
    lit = _ink(flash, LURK_L)
    mid = _ink(flash, LURK)
    dark = _ink(flash, LURK_D)
    deep = _ink(flash, LURK_DD)
    amp = 0.08 if lung else 0.35
    back = math.pi if f > 0 else 0.0
    hx = x + 16 + f * 6 + (f * 2 if lung else 0)
    hy = y + 6
    px, py = _bone(hx, hy, back + sin64(t * 2) * amp, 12, 6, lit, mid, dark)
    rx, ry = px, py
    px, py = _bone(px, py, back + sin64(t * 2 + 12) * amp, 10, 4, lit, mid, deep)
    display.set_pen(deep)
    _t(px, py, px - f * 8, py - 4, px - f * 2, py + 1)
    display.set_pen(dark)
    _t(px, py, px - f * 7, py + 5, px - f, py + 1)
    display.set_pen(mid)
    _t(rx - f, ry, rx + f * 2, ry - 2, rx, ry - 8)
    display.set_pen(deep)
    poly(_LURK_HEAD, hx, hy, f)
    display.set_pen(mid)
    _t(hx - f, hy - 1, hx + f * 6, hy - 2, hx + f * 2, hy + 2)
    display.set_pen(lit)
    _t(hx, hy - 3, hx + f * 5, hy - 3, hx + f * 2, hy)
    hinge_x = hx + f * 2
    hinge_y = hy + 2
    jaw = joint(hinge_x, hinge_y, _mir(f, 1.25 if lung else 0.28), 7)
    display.set_pen(MAW if lung else deep)
    _t(hinge_x, hinge_y, hx + f * 5, hy + 1, jaw[0], jaw[1])
    display.set_pen(deep)
    _t(hinge_x, hinge_y + 1, jaw[0], jaw[1], jaw[0] - f, jaw[1] + 2)
    display.set_pen(CREAM if lung else dark)
    _t(hinge_x + f, hinge_y, jaw[0], jaw[1], hinge_x + f * 2, hinge_y + (4 if lung else 1))
    display.set_pen(GOLD)
    display.circle(int(hx + f * 3), int(hy - 2), 2)
    display.set_pen(BLACK)
    display.circle(int(hx + f * 4), int(hy - 2), 1)
