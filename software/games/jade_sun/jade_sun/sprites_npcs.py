"""Spirits in the world and dialogue portraits.

Each mass is a dark jagged plate, mid facets, then a lit top. Triangles overlap
on purpose so the seams stay visible. Ceiba is a face on the trunk. Witz is the
stone face above its marker, about 52 by 56.
"""
from .hw import display
from .gfx import pen, shade, WHITE, BLACK, GOLD, RED, SHADOW
from .rig import tri, poly, sin64
from .sprites_fluff import draw_fluff


def _k(rgb, k):
    return pen(*shade(rgb, k))


_WOOD = (168, 118, 68)
_BARK = (58, 36, 26)
_LEAF = (34, 150, 62)
_GLOWC = (170, 255, 196)
_ROBE = (150, 84, 32)
_SKIN = (226, 164, 112)
_HEADR = (190, 42, 38)
_STARC = (160, 214, 244)
_POD = (120, 68, 26)
_BLUE = (46, 124, 208)
_FUR = (216, 156, 40)
_SPOTC = (78, 40, 12)
_STONE = (120, 118, 130)
_SNOW = (230, 238, 248)
_BAT = (84, 32, 108)
_STELE = (136, 118, 84)
_JADE = (48, 198, 128)
_GOLD = (255, 196, 60)

BK = _k(_BARK, 0.75)
W0 = _k(_WOOD, 0.58)
W1 = _k(_WOOD, 0.95)
W2 = _k(_WOOD, 1.35)
LF0 = _k(_LEAF, 0.42)
LF1 = _k(_LEAF, 0.9)
LF2 = _k(_LEAF, 1.4)
GL0 = _k(_GLOWC, 0.72)
GL1 = _k(_GLOWC, 1.08)
RB0 = _k(_ROBE, 0.48)
RB1 = _k(_ROBE, 0.88)
RB2 = _k(_ROBE, 1.32)
SK0 = _k(_SKIN, 0.58)
SK1 = _k(_SKIN, 0.95)
SK2 = _k(_SKIN, 1.3)
HD0 = _k(_HEADR, 0.48)
HD1 = _k(_HEADR, 0.92)
HD2 = _k(_HEADR, 1.32)
ST1 = _k(_STARC, 1.15)
PD0 = _k(_POD, 0.55)
PD1 = _k(_POD, 1.05)
PD2 = _k(_POD, 1.4)
BL0 = _k(_BLUE, 0.42)
BL1 = _k(_BLUE, 0.82)
BL2 = _k(_BLUE, 1.22)
BL3 = _k(_BLUE, 1.5)
FU0 = _k(_FUR, 0.48)
FU1 = _k(_FUR, 0.9)
FU2 = _k(_FUR, 1.32)
SP = _k(_SPOTC, 1.0)
SN0 = _k(_STONE, 0.42)
SN1 = _k(_STONE, 0.72)
SN2 = _k(_STONE, 1.05)
SN3 = _k(_STONE, 1.42)
SW0 = _k(_SNOW, 0.7)
SW1 = _k(_SNOW, 0.95)
SW2 = pen(255, 255, 255)
BT0 = _k(_BAT, 0.42)
BT1 = _k(_BAT, 0.82)
BT2 = _k(_BAT, 1.28)
SL0 = _k(_STELE, 0.48)
SL1 = _k(_STELE, 0.88)
SL2 = _k(_STELE, 1.32)
JD0 = _k(_JADE, 0.7)
JD1 = _k(_JADE, 1.15)
GD0 = _k(_GOLD, 0.5)
GD1 = GOLD
GD2 = _k(_GOLD, 1.28)
EYE = _k((130, 255, 176), 1.0)
BG = pen(14, 11, 20)
FR_L = _k((170, 142, 88), 1.1)
FR_D = _k((170, 142, 88), 0.32)
RAIN = _k((200, 228, 255), 0.95)

CEIBA_FACE = (
    (0, -12), (6, -9), (3, -5), (11, -4), (9, 1), (12, 5), (5, 4),
    (2, 10), (-3, 8), (-8, 6), (-12, 2), (-8, -2), (-11, -5), (-4, -6), (-6, -10),
)
EK_ROBE = (
    (-9, -6), (-2, -8), (6, -5), (11, -2), (7, 4), (12, 8), (3, 12),
    (-4, 9), (-11, 11), (-13, 3), (-7, -1),
)
EK_HEAD = (
    (0, -8), (5, -6), (8, -1), (5, 3), (2, 7), (0, 9), (-3, 6), (-7, 2), (-8, -2), (-4, -6),
)
CHAAC_BODY = (
    (-16, -6), (-6, -2), (0, -8), (8, -3), (16, -6), (8, 2), (14, 7),
    (5, 10), (10, 15), (-2, 12), (-11, 15), (-6, 8), (-15, 6), (-8, 1),
)
CHAAC_HEAD = (
    (0, -7), (5, -5), (8, 0), (4, 4), (6, 7), (-1, 6), (-6, 7), (-8, 1), (-5, -5),
)
CHAAC_CROWN = (
    (-9, -2), (-7, -10), (-2, -3), (1, -12), (4, -3), (8, -9), (10, -1), (2, 0), (-4, 0),
)
# Seated haunch and head. Feet sit on the marker; ears reach about 24 px above it.
BALAM_HAUNCH = (
    (-8, 0), (-6, -6), (-1, -8), (4, -5), (5, 0), (3, 4), (-2, 5), (-7, 3),
)
BALAM_HEAD = (
    (-5, -2), (-3, -6), (2, -5), (6, -1), (5, 4), (1, 6), (-3, 5), (-6, 1),
)
WITZ_ROCK = (
    (-26, 0), (-20, -14), (-26, -28), (-14, -32), (-20, -46), (-6, -38),
    (-2, -52), (4, -42), (10, -56), (18, -46), (14, -32), (26, -30),
    (22, -14), (26, 0),
)
WITZ_FACE = (
    (-12, -40), (-2, -44), (8, -42), (14, -32), (10, -20), (4, -14),
    (-2, -12), (-10, -18), (-16, -28), (-14, -36),
)
_RAIN = ((-10, 2), (-3, 8), (4, 3), (11, 9))


def _tris(ox, oy, col, pts):
    display.set_pen(col)
    for p in pts:
        tri(ox, oy, 1, p[0], p[1], p[2], p[3], p[4], p[5])


def _spark(ox, oy, r, col):
    display.set_pen(col)
    tri(ox, oy, 1, 0, -r, -1, 0, 1, 0)
    tri(ox, oy, 1, 0, r, -1, 0, 1, 0)
    tri(ox, oy, 1, -r, 0, 0, -1, 0, 1)
    tri(ox, oy, 1, r, 0, 0, -1, 0, 1)


def _leaf(ox, oy, bx, by, tx, ty):
    display.set_pen(LF0)
    tri(ox, oy, 1, bx - 2, by + 1, tx, ty, bx + 2, by)
    display.set_pen(LF1)
    tri(ox, oy, 1, bx - 1, by, tx, ty + 1, bx + 1, by)
    display.set_pen(LF2)
    tri(ox, oy, 1, bx, by - 1, tx, ty - 1, bx + 1, by - 1)


def _eyes(x0, y0, x1, y1, col, r, blink, glint):
    display.set_pen(col)
    if blink:
        display.rectangle(x0 - r, y0, r * 2 + 1, 1)
        display.rectangle(x1 - r, y1, r * 2 + 1, 1)
        return
    display.circle(x0, y0, r)
    display.circle(x1, y1, r)
    display.set_pen(BLACK)
    display.pixel(x0, y0 + 1)
    display.pixel(x1, y1 + 1)
    if glint:
        display.set_pen(WHITE)
        display.pixel(x0 - 1, y0 - 1)
        display.pixel(x1 - 1, y1 - 1)


def _mouth(ox, oy, my, open_m, w):
    display.set_pen(BLACK)
    if open_m:
        tri(ox, oy, 1, -w, my, w, my, 0, my + 4)
    else:
        display.rectangle(ox - w, oy + my, w * 2, 1)


def _asleep(t):
    return (t & 63) > 60


def _ceiba(x, y, t, talking):
    ox, oy = x + 8, y - 5
    sw = int(sin64(t) * 3)
    sw2 = int(sin64(t + 16) * 2)
    display.set_pen(BK)
    poly(CEIBA_FACE, ox, oy, 1)
    _tris(ox, oy, W0, (
        (-3, 3, 4, 4, 0, 9),
        (6, 2, 9, 5, 3, 6),
        (-8, 2, -3, 2, -2, 6),
    ))
    _tris(ox, oy, W1, (
        (-8, -1, -2, -4, -1, 3),
        (7, 0, 2, -4, 2, 4),
        (-3, -5, 4, -6, 0, 0),
    ))
    _tris(ox, oy, W2, (
        (-3, -10, 4, -11, 0, -4),
        (-1, -8, 2, -9, 0, -5),
    ))
    _leaf(ox, oy, -11, 0, -16, -8 + sw)
    _leaf(ox, oy, 10, 2, 16, -4 + sw2)
    _leaf(ox, oy, 0, -12, 1, -17 + sw)
    display.set_pen(LF0)
    tri(ox, oy, 1, -2, 8, -4, 16, 0, 12)
    display.set_pen(LF1)
    tri(ox, oy, 1, 1, 8, 4, 15 + sw2, 2, 11)
    _eyes(ox - 4, oy - 3, ox + 4, oy - 3, GL1 if talking else GL0, 2, _asleep(t), True)
    display.set_pen(BK)
    tri(ox, oy, 1, -2, 0, 2, 0, 0, 3)
    _mouth(ox, oy, 4, talking, 3)


def _ek(x, y, t, talking):
    ox, oy = x + 8, y + 5
    hx, hy = ox, oy - 13
    bob = int(sin64(t + 8) * 2)
    display.set_pen(RB0)
    poly(EK_ROBE, ox, oy, 1)
    _tris(ox, oy, RB1, (
        (-5, -2, 0, -4, -1, 6),
        (2, -2, 8, 0, 3, 7),
    ))
    _tris(ox, oy, RB2, ((-4, -5, 5, -6, 0, -1),))
    _tris(ox, oy, RB0, ((-6, 5, 1, 6, -2, 10), (5, 4, 1, 5, 3, 10)))
    display.set_pen(SK0)
    poly(EK_HEAD, hx, hy, 1)
    _tris(hx, hy, SK1, (
        (-5, -1, -1, -3, 0, 3),
        (4, -1, 1, -3, 1, 3),
    ))
    _tris(hx, hy, SK2, ((-3, -6, 3, -6, 0, -2),))
    _tris(hx, hy, SK0, ((-2, 3, 3, 3, 0, 7),))
    display.set_pen(HD0)
    tri(hx, hy, 1, -8, -4, -3, -4, -6, -15)
    tri(hx, hy, 1, -3, -4, 3, -4, 0, -17)
    tri(hx, hy, 1, 2, -4, 8, -4, 6, -14)
    _tris(hx, hy, HD1, (
        (-6, -5, -2, -5, -5, -12),
        (-1, -5, 2, -5, 0, -14),
        (2, -5, 6, -5, 5, -12),
    ))
    _tris(hx, hy, HD2, ((-1, -8, 1, -8, 0, -13),))
    display.set_pen(SK0)
    tri(hx, hy, 1, -4, 5, 0, 6, -1, 11)
    display.set_pen(SK1)
    tri(hx, hy, 1, -1, 5, 3, 5, 1, 10)
    _spark(hx + 12, hy - 1 + bob, 4, ST1)
    display.set_pen(WHITE)
    display.pixel(hx + 12, hy - 1 + bob)
    _tris(ox, oy, PD0, ((-13, 1, -8, -2, -8, 7),))
    _tris(ox, oy, PD2, ((-12, 0, -9, -1, -10, 2),))
    _eyes(hx - 3, hy - 1, hx + 3, hy - 1, BLACK, 1, _asleep(t), False)
    display.set_pen(SK0)
    tri(hx, hy, 1, -1, 1, 1, 1, 0, 3)
    _mouth(hx, hy, 3, talking, 2)


def _chaac(x, y, t, talking):
    bob = int(sin64(t) * 2)
    ox, oy = x + 8, y - 1 + bob
    hx, hy = ox - 2, oy - 12
    display.set_pen(BL0)
    poly(CHAAC_BODY, ox, oy, 1)
    _tris(ox, oy, BL1, (
        (-7, 0, -1, -2, -2, 7),
        (2, -1, 8, 1, 3, 7),
    ))
    _tris(ox, oy, BL2, ((-4, -3, 6, -4, 1, 0),))
    _tris(ox, oy, BL0, ((-4, 7, 5, 6, 1, 12),))
    display.set_pen(BL0)
    poly(CHAAC_HEAD, hx, hy, 1)
    _tris(hx, hy, BL1, ((-4, 0, 0, -2, 0, 3), (2, -1, 5, 0, 2, 3)))
    _tris(hx, hy, BL3, ((-3, -5, 4, -6, 0, -1),))
    display.set_pen(GD0)
    poly(CHAAC_CROWN, hx, hy, 1)
    _tris(hx, hy, GD1, (
        (-7, -4, -3, -4, -6, -10),
        (-1, -4, 3, -4, 1, -12),
        (3, -4, 7, -3, 7, -9),
    ))
    _tris(hx, hy, GD2, ((0, -6, 2, -6, 1, -11),))
    display.set_pen(BL0)
    tri(hx, hy, 1, 5, 2, 18, 7, 7, 8)
    display.set_pen(BL1)
    tri(hx, hy, 1, 4, 0, 16, 3, 6, 4)
    display.set_pen(BL3)
    tri(hx, hy, 1, 5, -1, 14, 1, 8, 3)
    display.set_pen(WHITE)
    tri(hx, hy, 1, 3, 3, 5, 3, 4, 6)
    _eyes(hx - 3, hy - 1, hx + 2, hy - 1, WHITE, 2, _asleep(t), False)
    _mouth(hx, hy, 3, talking, 2)
    display.set_pen(RAIN)
    i = 0
    while i < 4:
        dx, dy = _RAIN[i]
        display.pixel(ox + dx, oy + 16 + ((dy + t * 3) & 15))
        i += 1


def _balam(x, y, t, talking):
    # Seated guardian, 18px wide and about 24px above the marker.
    ox, oy = x + 8, y - 6
    hx, hy = x + 11, y - 15
    sw = int(sin64(t) * 3)
    display.set_pen(FU0)
    poly(BALAM_HAUNCH, ox, oy, 1)
    _tris(ox, oy, FU1, (
        (-4, -3, 1, -5, -1, 1),
        (0, -2, 4, -3, 2, 2),
    ))
    _tris(ox, oy, FU2, ((-2, -6, 3, -6, 0, -2),))
    _tris(ox, oy, SP, (
        (-3, -1, -1, -2, -2, 1),
        (1, 0, 3, -1, 2, 2),
        (-1, 1, 1, 1, 0, 3),
    ))
    # Front legs: upper bone then paw.
    display.set_pen(FU0)
    tri(ox, oy, 1, 2, -4, 1, 1, 4, -2)
    tri(ox, oy, 1, 1, 0, 4, 1, 3, 5)
    display.set_pen(FU1)
    tri(ox, oy, 1, 2, -3, 2, 0, 4, -1)
    tri(ox, oy, 1, 2, 1, 4, 2, 3, 4)
    display.set_pen(FU0)
    tri(ox, oy, 1, -1, -3, -2, 2, 1, 0)
    tri(ox, oy, 1, -2, 1, 1, 2, 0, 5)
    display.set_pen(FU2)
    tri(ox, oy, 1, 0, -2, -1, 1, 1, 0)
    display.set_pen(FU0)
    poly(BALAM_HEAD, hx, hy, 1)
    _tris(hx, hy, FU1, ((-3, -1, 2, -2, 0, 2), (1, 0, 4, 1, 2, 3)))
    _tris(hx, hy, FU2, ((-2, -4, 3, -4, 1, -1),))
    display.set_pen(FU0)
    display.circle(hx - 3, hy - 6, 3)
    display.circle(hx + 2, hy - 7, 3)
    display.set_pen(_k((150, 64, 36), 0.8))
    display.circle(hx - 3, hy - 7, 1)
    display.circle(hx + 2, hy - 8, 1)
    display.set_pen(EYE if talking else _k((130, 255, 176), 0.7))
    display.circle(hx - 1, hy - 1, 1)
    display.circle(hx + 3, hy - 1, 1)
    display.set_pen(BLACK)
    display.pixel(hx - 1, hy)
    display.pixel(hx + 3, hy)
    display.set_pen(FU2)
    tri(hx, hy, 1, 0, 2, 4, 2, 2, 5)
    _mouth(hx + 2, hy, 3, talking, 2)
    display.set_pen(FU0)
    tri(ox, oy, 1, -6, -2, -4, -8, -2, -3)
    tri(ox, oy, 1, -4, -7, sw, -13, -1, -6)
    display.set_pen(FU2)
    tri(ox, oy, 1, -5, -3, -3, -8, -2, -4)
    tri(ox, oy, 1, -3, -7, 1 + sw, -12, -1, -6)


def _witz(x, y, t, talking):
    ox, oy = x + 8, y + 16
    drop = 4 if talking else 0
    awake = talking or (t % 180) > 168
    display.set_pen(SN0)
    poly(WITZ_ROCK, ox, oy, 1)
    display.set_pen(SN1)
    poly(WITZ_FACE, ox, oy, 1)
    _tris(ox, oy, SN0, (
        (-12, -26, -4, -22, -6, -14),
        (10, -24, 3, -20, 6, -14),
        (-4, -16, 5, -16, 0, -8),
    ))
    _tris(ox, oy, SN2, (
        (-8, -38, 8, -40, 0, -28),
        (-6, -30, 2, -32, -1, -22),
        (1, -30, 8, -32, 3, -22),
    ))
    _tris(ox, oy, SN3, ((-4, -42, 6, -44, 1, -34),))
    display.set_pen(SW0)
    tri(ox, oy, 1, 0, -48, 10, -56, 16, -44)
    tri(ox, oy, 1, -14, -40, -2, -50, 0, -40)
    display.set_pen(SW2)
    tri(ox, oy, 1, 3, -50, 9, -56, 10, -48)
    display.set_pen(SN0)
    tri(ox, oy, 1, -10, -36, -4, -38, -6, -28)
    tri(ox, oy, 1, 8, -36, 3, -38, 5, -28)
    display.set_pen(SN2)
    tri(ox, oy, 1, -2, -30, 3, -30, 0, -20)
    display.set_pen(SN3)
    tri(ox, oy, 1, -1, -30, 2, -30, 0, -24)
    eye = _k((160, 225, 255), 1.15) if awake else SN2
    _eyes(ox - 7, oy - 30, ox + 7, oy - 30, eye, 2, False, awake)
    display.set_pen(BLACK)
    tri(ox, oy, 1, -4, -16, 4, -16, 0, -9 + drop)
    display.set_pen(SN1)
    tri(ox, oy, 1, -7, -14 + drop, 7, -14 + drop, 0, -5 + drop)
    display.set_pen(GD2)
    tri(ox, oy, 1, -2, -43, 2, -43, 0, -39)
    display.set_pen(GD0)
    tri(ox, oy, 1, 0, -42, 3, -40, 0, -38)


def _frame(x, y):
    display.set_pen(BG)
    display.rectangle(x, y, 36, 36)
    display.set_pen(FR_L)
    display.rectangle(x, y, 36, 2)
    display.set_pen(FR_D)
    display.rectangle(x, y + 34, 36, 2)


def _p_ceiba(x, y, t, blink):
    ox, oy = x + 18, y + 18
    sw = int(sin64(t) * 2)
    display.set_pen(BK)
    poly((
        (0, -13), (6, -11), (3, -6), (12, -7), (14, 0), (8, 3), (12, 8),
        (4, 6), (1, 12), (-5, 7), (-12, 8), (-14, 1), (-8, -2), (-13, -6), (-4, -6), (-7, -12),
    ), ox, oy, 1)
    _tris(ox, oy, W0, (
        (-4, 3, 5, 4, 0, 10),
        (-9, 3, -2, 2, -2, 7),
        (8, 3, 3, 2, 4, 8),
    ))
    _tris(ox, oy, W1, (
        (-8, 0, -2, -4, -1, 4),
        (8, 0, 2, -4, 2, 5),
        (-4, -5, 5, -6, 0, 1),
        (-7, -6, -2, -2, -4, 0),
    ))
    _tris(ox, oy, W2, (
        (-4, -10, 5, -11, 0, -3),
        (-1, -8, 2, -9, 0, -4),
    ))
    _leaf(ox, oy, -12, 1, -16, -8 + sw)
    _leaf(ox, oy, 11, 2, 16, -5 + sw)
    _leaf(ox, oy, 0, -13, 1, -16)
    display.set_pen(LF0)
    tri(ox, oy, 1, -3, 7, -7, 14, -1, 11)
    display.set_pen(LF1)
    tri(ox, oy, 1, 3, 6, 8, 13, 4, 9)
    _eyes(ox - 4, oy - 2, ox + 4, oy - 2, GL1, 2, blink, True)
    display.set_pen(BK)
    tri(ox, oy, 1, -6, -5, -2, -7, -3, -2)
    tri(ox, oy, 1, 6, -5, 2, -7, 3, -2)
    tri(ox, oy, 1, -1, 1, 2, 1, 0, 4)
    _mouth(ox, oy, 5, (t >> 4) & 1, 3)


def _p_ek(x, y, t, blink):
    ox, oy = x + 18, y + 22
    display.set_pen(RB0)
    poly((
        (-11, -1), (-4, -5), (4, -3), (12, -4), (9, 3), (13, 9), (3, 13),
        (-4, 11), (-12, 13), (-14, 5),
    ), ox, oy, 1)
    _tris(ox, oy, RB1, ((-5, 1, 1, -1, 0, 8), (2, 0, 8, 2, 3, 8)))
    _tris(ox, oy, RB2, ((-3, -2, 5, -3, 1, 1),))
    hx, hy = ox, oy - 8
    display.set_pen(SK0)
    poly((
        (0, -9), (6, -7), (8, -2), (6, 3), (3, 8), (0, 10), (-4, 6), (-8, 2), (-8, -3), (-4, -7),
    ), hx, hy, 1)
    _tris(hx, hy, SK1, (
        (-5, 0, -1, -3, 0, 4),
        (5, 0, 1, -3, 1, 4),
        (-3, -5, 4, -6, 0, 0),
    ))
    _tris(hx, hy, SK2, ((-3, -7, 3, -7, 0, -2),))
    _tris(hx, hy, SK0, ((-3, 3, 3, 3, 0, 8),))
    display.set_pen(HD0)
    poly((
        (-9, -6), (-7, -16), (-2, -7), (1, -17), (4, -7), (8, -15), (10, -5), (2, -4), (-3, -4),
    ), hx, hy, 1)
    _tris(hx, hy, HD1, (
        (-7, -7, -2, -7, -6, -13),
        (-1, -7, 3, -7, 1, -14),
        (3, -7, 8, -6, 7, -12),
    ))
    _tris(hx, hy, HD2, ((0, -9, 2, -9, 1, -14),))
    display.set_pen(SK0)
    tri(hx, hy, 1, -5, 5, 0, 6, -2, 13)
    tri(hx, hy, 1, 0, 6, 5, 5, 2, 12)
    display.set_pen(SK2)
    tri(hx, hy, 1, -1, 6, 2, 6, 0, 10)
    _spark(hx, hy - 12, 3, ST1)
    display.set_pen(WHITE)
    display.pixel(hx, hy - 12)
    _tris(ox, oy, PD0, ((-14, 3, -8, 0, -8, 11),))
    _tris(ox, oy, PD2, ((-13, 3, -10, 1, -11, 5),))
    _eyes(hx - 3, hy - 1, hx + 3, hy - 1, BLACK, 2, blink, True)
    display.set_pen(HD0)
    tri(hx, hy, 1, -4, -3, -1, -5, -2, -1)
    tri(hx, hy, 1, 4, -3, 1, -5, 2, -1)
    _mouth(hx, hy, 4, (t >> 4) & 1, 2)


def _p_chaac(x, y, t, blink):
    ox, oy = x + 15, y + 22
    display.set_pen(BL0)
    poly((
        (-11, -2), (-3, -6), (5, -4), (12, -5), (7, 2), (13, 8), (2, 12), (-8, 11), (-13, 5),
    ), ox, oy, 1)
    _tris(ox, oy, BL1, ((-5, 0, 1, -2, 0, 6), (2, 0, 8, 2, 3, 7)))
    _tris(ox, oy, BL2, ((-3, -3, 6, -4, 1, 1),))
    hx, hy = ox - 2, oy - 9
    display.set_pen(BL0)
    poly(CHAAC_HEAD, hx, hy, 1)
    _tris(hx, hy, BL1, ((-4, 0, 0, -2, 0, 3), (2, 0, 5, 1, 2, 3)))
    _tris(hx, hy, BL3, ((-3, -5, 4, -6, 0, -1),))
    display.set_pen(GD0)
    poly(CHAAC_CROWN, hx, hy, 1)
    _tris(hx, hy, GD1, (
        (-7, -4, -2, -4, -6, -10),
        (0, -4, 3, -4, 1, -12),
        (3, -4, 8, -3, 7, -9),
    ))
    _tris(hx, hy, GD2, ((0, -6, 2, -6, 1, -11),))
    display.set_pen(BL0)
    tri(hx, hy, 1, 3, 1, 16, 7, 5, 7)
    display.set_pen(BL1)
    tri(hx, hy, 1, 2, -1, 14, 2, 4, 3)
    display.set_pen(BL3)
    tri(hx, hy, 1, 3, -2, 12, 0, 6, 1)
    display.set_pen(BL2)
    tri(hx, hy, 1, 12, 2, 17, 6, 13, 7)
    display.set_pen(WHITE)
    tri(hx, hy, 1, 2, 4, 4, 4, 3, 7)
    tri(hx, hy, 1, 4, 4, 6, 4, 5, 7)
    _eyes(hx - 3, hy - 1, hx + 2, hy - 1, WHITE, 2, blink, True)
    _mouth(hx, hy, 3, True, 2)
    display.set_pen(RAIN)
    i = 0
    while i < 4:
        dx, dy = _RAIN[i]
        display.pixel(ox + dx, oy + 10 + ((dy + t) & 7))
        i += 1


def _p_balam(x, y, t, blink):
    ox, oy = x + 18, y + 20
    display.set_pen(FU0)
    poly((
        (-6, -4), (0, -8), (6, -5), (11, 0), (9, 6), (3, 11), (-2, 10),
        (-9, 6), (-12, 1), (-9, -2),
    ), ox, oy, 1)
    _tris(ox, oy, FU1, (
        (-7, 0, -1, -3, -2, 5),
        (2, -1, 8, 1, 4, 6),
        (-3, -5, 4, -6, 1, 0),
    ))
    _tris(ox, oy, FU2, ((-3, -6, 4, -7, 0, -2), (-5, -2, -1, -4, -2, 0)))
    _tris(ox, oy, FU0, ((-3, 4, 4, 4, 0, 9), (5, 3, 9, 5, 4, 8)))
    display.set_pen(FU0)
    tri(ox, oy, 1, -8, -3, -14, -14, -3, -5)
    tri(ox, oy, 1, 6, -4, 13, -14, 4, -5)
    display.set_pen(FU1)
    tri(ox, oy, 1, -7, -3, -12, -12, -5, -4)
    tri(ox, oy, 1, 5, -4, 11, -12, 5, -4)
    display.set_pen(_k((150, 64, 36), 0.85))
    tri(ox, oy, 1, -7, -4, -11, -10, -5, -5)
    tri(ox, oy, 1, 5, -5, 9, -10, 5, -5)
    display.set_pen(SP)
    tri(ox, oy, 1, -5, 0, -3, -1, -4, 2)
    tri(ox, oy, 1, 4, 1, 6, 0, 5, 3)
    tri(ox, oy, 1, -1, -3, 1, -4, 0, -1)
    display.set_pen(FU2)
    tri(ox, oy, 1, -3, 5, 3, 5, 0, 9)
    display.set_pen(BLACK)
    tri(ox, oy, 1, -2, 6, 2, 6, 0, 9)
    display.set_pen(WHITE)
    tri(ox, oy, 1, -2, 7, -1, 7, -1, 10)
    tri(ox, oy, 1, 1, 7, 2, 7, 1, 10)
    _eyes(ox - 4, oy - 1, ox + 4, oy - 1, EYE, 2, blink, True)
    display.set_pen(BLACK)
    tri(ox, oy, 1, -1, 2, 1, 2, 0, 5)


def _p_witz(x, y, t, blink):
    ox, oy = x + 18, y + 19
    display.set_pen(SN0)
    poly((
        (-16, -6), (-12, -14), (-4, -10), (2, -15), (8, -11), (15, -8),
        (16, 1), (12, 8), (6, 14), (-1, 12), (-8, 14), (-14, 8), (-16, 0),
    ), ox, oy, 1)
    display.set_pen(SN1)
    poly((
        (-10, -9), (-2, -12), (6, -11), (11, -4), (9, 4), (4, 9),
        (-2, 11), (-9, 5), (-12, -1), (-11, -6),
    ), ox, oy, 1)
    _tris(ox, oy, SN0, (
        (-9, -1, -2, -3, -3, 5),
        (7, -1, 2, -3, 3, 5),
        (-3, 4, 4, 4, 0, 10),
    ))
    _tris(ox, oy, SN2, (
        (-7, -9, 6, -10, 0, -2),
        (-5, -5, 1, -7, -1, -1),
        (1, -6, 7, -7, 2, -1),
    ))
    _tris(ox, oy, SN3, ((-3, -11, 4, -12, 0, -6),))
    display.set_pen(SW0)
    tri(ox, oy, 1, -8, -12, -1, -15, 2, -11)
    tri(ox, oy, 1, 3, -12, 10, -16, 14, -8)
    display.set_pen(SW2)
    tri(ox, oy, 1, 5, -13, 9, -16, 10, -12)
    display.set_pen(SN0)
    tri(ox, oy, 1, -8, -7, -2, -9, -4, -3)
    tri(ox, oy, 1, 6, -7, 2, -9, 3, -3)
    display.set_pen(SN2)
    tri(ox, oy, 1, -2, -4, 2, -4, 0, 1)
    _eyes(ox - 5, oy - 3, ox + 5, oy - 3, _k((160, 225, 255), 1.15), 2, False, True)
    display.set_pen(BLACK)
    tri(ox, oy, 1, -4, 4, 4, 4, 0, 9)
    display.set_pen(SN1)
    tri(ox, oy, 1, -5, 5, 5, 5, 0, 11)
    display.set_pen(GD2)
    tri(ox, oy, 1, -2, -11, 2, -11, 0, -7)


def _p_stone(x, y, t):
    ox, oy = x + 18, y + 18
    hot = (t >> 3) & 1
    display.set_pen(SL0)
    poly((
        (0, -15), (4, -13), (8, -8), (5, -1), (9, 5), (6, 12), (2, 15),
        (-3, 13), (-8, 14), (-10, 6), (-7, -1), (-10, -7), (-5, -12),
    ), ox, oy, 1)
    display.set_pen(SL1)
    poly((
        (1, -10), (5, -8), (5, 0), (4, 7), (1, 11), (-3, 9), (-5, 2), (-4, -6),
    ), ox, oy, 1)
    _tris(ox, oy, SL2, ((-2, -11, 4, -12, 1, -6), (-1, -7, 3, -8, 1, -3)))
    _tris(ox, oy, SL0, (
        (-4, 2, 3, 1, 0, 9),
        (-6, -1, -2, -3, -3, 4),
        (4, 0, 1, -2, 2, 5),
        (6, -6, 8, -2, 4, -4),
        (-8, -8, -4, -10, -5, -4),
    ))
    display.set_pen(GD0)
    tri(ox, oy, 1, -3, -7, 0, -14, 1, -6)
    tri(ox, oy, 1, 0, -7, 4, -13, 2, -5)
    display.set_pen(GD2 if hot else GD1)
    tri(ox, oy, 1, -1, -8, 2, -12, 1, -6)
    display.set_pen(JD0)
    tri(ox, oy, 1, -2, -1, 2, -1, 0, 3)
    display.set_pen(JD1)
    tri(ox, oy, 1, -1, -1, 1, -1, 0, 1)
    display.set_pen(SL0)
    tri(ox, oy, 1, 5, -4, 9, 1, 4, 2)
    tri(ox, oy, 1, -8, 4, -4, 6, -6, 10)
    display.rectangle(ox - 4, oy + 5, 8, 1)
    display.rectangle(ox - 4, oy + 8, 8, 1)


def _p_bat(x, y, t, blink):
    ox, oy = x + 18, y + 18
    flap = int(sin64(t) * 2)
    display.set_pen(BT0)
    tri(ox, oy, 1, -2, -1, -16, -8 + flap, -10, 7)
    tri(ox, oy, 1, -3, 3, -13, 7, -5, 12)
    tri(ox, oy, 1, 2, -1, 16, -8 + flap, 10, 7)
    tri(ox, oy, 1, 3, 3, 13, 7, 5, 12)
    display.set_pen(BT1)
    tri(ox, oy, 1, -3, 0, -12, -3 + flap, -7, 4)
    tri(ox, oy, 1, 3, 0, 12, -3 + flap, 7, 4)
    display.set_pen(BT2)
    tri(ox, oy, 1, -4, -1, -11, -6 + flap, -7, 0)
    tri(ox, oy, 1, 4, -1, 11, -6 + flap, 7, 0)
    display.set_pen(BT0)
    poly((
        (0, -7), (5, -5), (7, 0), (4, 5), (1, 8), (0, 10), (-2, 7), (-5, 4), (-7, 0), (-4, -5),
    ), ox, oy, 1)
    _tris(ox, oy, BT1, (
        (-4, 0, 0, -2, 0, 4),
        (4, 0, 1, -2, 1, 4),
        (-2, 3, 2, 3, 0, 7),
    ))
    _tris(ox, oy, BT2, ((-3, -5, 3, -5, 0, -1),))
    display.set_pen(BT0)
    tri(ox, oy, 1, -4, -4, -8, -15, -1, -5)
    tri(ox, oy, 1, 3, -4, 8, -15, 1, -5)
    display.set_pen(BT1)
    tri(ox, oy, 1, -3, -4, -6, -12, -2, -4)
    tri(ox, oy, 1, 2, -4, 6, -12, 2, -4)
    display.set_pen(_k((36, 14, 48), 1.0))
    tri(ox, oy, 1, -3, -5, -6, -11, -2, -5)
    tri(ox, oy, 1, 2, -5, 5, -11, 2, -5)
    display.set_pen(WHITE)
    tri(ox, oy, 1, -2, 6, -1, 6, -1, 10)
    tri(ox, oy, 1, 1, 6, 2, 6, 1, 10)
    _eyes(ox - 3, oy - 1, ox + 3, oy - 1, RED, 2, blink, True)
    display.set_pen(BLACK)
    tri(ox, oy, 1, -2, 3, 2, 3, 0, 6)


def draw_npc(kind, x, y, t, talking=False):
    """x, y = marker tile top-left (screen)."""
    if kind == "ceiba":
        _ceiba(x, y, t, talking)
    elif kind == "ek":
        _ek(x, y, t, talking)
    elif kind == "chaac":
        _chaac(x, y, t, talking)
    elif kind == "balam":
        _balam(x, y, t, talking)
    elif kind == "witz":
        _witz(x, y, t, talking)


def draw_portrait(kind, x, y, t, skin=None):
    _frame(x, y)
    blink = (t % 90) >= 86
    if kind == "fluff" and skin:
        # Scale 2: ears ~23 px above the hitbox, eyes ~10 px below the origin,
        # body ~30 px down. Sit the bust so the ears clear the top bar and
        # the eyes sit above the bottom bar; the body is cut on the edge.
        draw_fluff(skin, x + 8, y + 16, 1, t, True, 0, scale=2, blink=blink)
        display.set_pen(SHADOW)
        display.rectangle(x - 8, y - 24, 52, 24)
        display.rectangle(x - 8, y + 36, 52, 36)
        display.rectangle(x - 12, y, 12, 36)
        display.rectangle(x + 36, y, 12, 36)
        display.set_pen(FR_L)
        display.rectangle(x, y, 36, 2)
        display.set_pen(FR_D)
        display.rectangle(x, y + 34, 36, 2)
        return
    if kind == "ceiba":
        _p_ceiba(x, y, t, blink)
    elif kind == "ek":
        _p_ek(x, y, t, blink)
    elif kind == "chaac":
        _p_chaac(x, y, t, blink)
    elif kind == "balam":
        _p_balam(x, y, t, blink)
    elif kind == "witz":
        _p_witz(x, y, t, blink)
    elif kind == "stone":
        _p_stone(x, y, t)
    else:
        _p_bat(x, y, t, blink)
