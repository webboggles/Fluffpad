"""Boss art. Each draw_<kind>(b, t) renders a boss from its live state (screen coords)."""
import math
from .hw import display
from .gfx import pen, shade, HUD, WHITE, BLACK, GOLD, RED, JADE, CREAM
from .rig import tri, poly, sin64, cos64


def _tone(rgb, k):
    r, g, b = shade(rgb, k)
    return pen(r, g, b)


_XO = (42, 136, 124)
X_LIT = _tone(_XO, 1.65)
X_MID = _tone(_XO, 1.0)
X_EDGE = _tone(_XO, 0.36)
X_BELLY = pen(214, 208, 128)
_JA = (124, 66, 154)
J_BACK = _tone(_JA, 1.9)
J_LIT = _tone(_JA, 1.45)
J_MID = _tone(_JA, 0.85)
J_EDGE = _tone(_JA, 0.38)
J_SPOT = pen(28, 12, 36)
J_EYE = pen(160, 255, 186)
_EA = (72, 86, 128)
E_LIT = _tone(_EA, 1.85)
E_MID = _tone(_EA, 1.0)
E_EDGE = _tone(_EA, 0.38)
E_TIP = pen(236, 240, 250)
E_HEAD_D = pen(176, 184, 196)
_WA = (132, 128, 140)
W_LIT = _tone(_WA, 1.42)
W_MID = _tone(_WA, 0.76)
W_EDGE = _tone(_WA, 0.34)
_CA = (116, 30, 124)
C_LIT = _tone(_CA, 1.5)
C_MID = _tone(_CA, 0.82)
C_EDGE = _tone(_CA, 0.34)
_C3 = (176, 32, 40)
C3_LIT = _tone(_C3, 1.45)
C3_MID = _tone(_C3, 0.8)
C3_EDGE = _tone(_C3, 0.28)
C_TIP = pen(214, 140, 206)
C3_TIP = pen(255, 186, 160)
MOUTH = pen(96, 16, 30)
BOLT = pen(150, 200, 255)
SIGHT = pen(255, 48, 40)
SIGHT_HOT = pen(255, 230, 180)
GOLD_D = pen(150, 96, 24)

_EAGLE_MASS = ((-15, -9), (-6, -18), (3, -9), (11, -17), (15, -9), (20, 2), (15, 9), (2, 16), (-7, 9), (-15, 9), (-20, 1))
_HELM = ((2, 13), (4, 4), (7, -4), (11, 1), (15, -5), (19, 3), (21, 12), (12, 15), (6, 14))
_WATCH_MASS = ((0, 0), (8, -8), (14, 0), (22, 0), (26, 12), (22, 22), (22, 30), (10, 34), (0, 30), (-5, 16))
_CAM_MASS = ((-17, -12), (-9, -20), (0, -12), (11, -19), (17, -12), (22, 2), (17, 12), (4, 18), (-6, 12), (-17, 12), (-22, 1))


def _flip(ang, f):
    if f < 0:
        return math.pi - ang
    return ang


def _rod(x, y, ang, ln, w0, w1, dark, mid):
    """Tapered bone, two triangles. Polygon is reserved for the big masses."""
    c = math.cos(ang)
    s = math.sin(ang)
    ex = x + c * ln
    ey = y + s * ln
    nx = -s
    ny = c
    x0 = int(x + nx * w0)
    y0 = int(y + ny * w0)
    x1 = int(x - nx * w0)
    y1 = int(y - ny * w0)
    x2 = int(ex + nx * w1)
    y2 = int(ey + ny * w1)
    x3 = int(ex - nx * w1)
    y3 = int(ey - ny * w1)
    display.set_pen(dark)
    display.triangle(x1, y1, x2, y2, x3, y3)
    display.set_pen(mid)
    display.triangle(x0, y0, x2, y2, x1, y1)
    return ex, ey


def _feat(x, y, ang, ln, w, p):
    c = math.cos(ang)
    s = math.sin(ang)
    display.set_pen(p)
    display.triangle(int(x - s * w * 0.4), int(y + c * w * 0.4),
                     int(x + c * ln), int(y + s * ln),
                     int(x + s * w), int(y - c * w))


def _seg(x0, y0, x1, y1, h, edge, mid, lit):
    """Fat scale between two trail points. h is half the body height, about 5 to 7."""
    dx = x1 - x0
    dy = y1 - y0
    ln = math.sqrt(dx * dx + dy * dy) or 1.0
    fx = dx / ln
    fy = dy / ln
    ux = -fy
    uy = fx
    if uy > 0:
        ux = -ux
        uy = -uy
    ax = x0 - fx * 3.0
    ay = y0 - fy * 3.0
    bx = x1 + fx * 3.0
    by = y1 + fy * 3.0
    ht = h * 0.96
    atx = ax + ux * ht
    aty = ay + uy * ht
    abx = ax - ux * ht
    aby = ay - uy * ht
    btx = bx + ux * ht
    bty = by + uy * ht
    bbx = bx - ux * ht
    bby = by - uy * ht
    mx = (x0 + x1) * 0.5
    my = (y0 + y1) * 0.5
    display.set_pen(edge)
    display.triangle(int(abx), int(aby), int(bbx), int(bby), int(mx - ux * h), int(my - uy * h))
    display.set_pen(mid)
    display.triangle(int(atx), int(aty), int(btx), int(bty), int(bbx), int(bby))
    display.triangle(int(atx), int(aty), int(abx), int(aby), int(bbx), int(bby))
    display.set_pen(lit)
    display.triangle(int(atx), int(aty), int(btx), int(bty), int(mx + ux * h * 0.55), int(my + uy * h * 0.55))
    display.triangle(int(mx - fx * 1.6 + ux * ht), int(my - fy * 1.6 + uy * ht),
                     int(mx + ux * (h + 3)), int(my + uy * (h + 3)),
                     int(mx + fx * 1.6 + ux * ht), int(my + fy * 1.6 + uy * ht))


def _plumes(x, y, ang, ln, w, dark, lit):
    """Broad feather: dark underside, lit top edge. ang is the feather axis."""
    c = math.cos(ang)
    s = math.sin(ang)
    px = -s
    py = c
    if py > 0:
        px = -px
        py = -py
    tx = x + c * ln
    ty = y + s * ln
    display.set_pen(dark)
    display.triangle(int(x - px * w), int(y - py * w),
                     int(x + c * ln * 0.15), int(y + s * ln * 0.15),
                     int(tx - px * w * 0.4), int(ty - py * w * 0.4))
    display.set_pen(lit)
    display.triangle(int(x + px * w * 0.15), int(y + py * w * 0.15),
                     int(x + c * ln * 0.3 + px * w * 0.65), int(y + s * ln * 0.3 + py * w * 0.65),
                     int(tx + px * w * 0.2), int(ty + py * w * 0.2))


def _wing(sx, sy, ang, bend, l1, l2, dark, mid, lit, tip, n, fln, spread):
    c = math.cos(ang)
    s = math.sin(ang)
    ex = sx + c * l1
    ey = sy + s * l1
    a2 = ang + bend
    c2 = math.cos(a2)
    s2 = math.sin(a2)
    k = 0
    while k < 2:
        u = 0.3 + k * 0.4
        _plumes(sx + c * l1 * u, sy + s * l1 * u, ang + spread * (1.2 + k * 0.18), fln * 0.95, 8.5, dark, mid)
        k += 1
    k = 0
    while k < 2:
        u = 0.28 + k * 0.42
        _plumes(ex + c2 * l2 * u, ey + s2 * l2 * u, a2 + spread * (1.15 + k * 0.16), fln, 7.5, mid, lit)
        k += 1
    wx = ex + c2 * l2
    wy = ey + s2 * l2
    i = 0
    while i < n:
        a = a2 + spread * (i - (n - 1) * 0.5) * 0.45
        _feat(wx, wy, a, fln + 3 - i * 2, 3.8, tip if i == 0 else lit)
        i += 1
    _rod(sx, sy, ang, l1, 3.6, 2.2, dark, mid)
    _rod(ex, ey, a2, l2, 2.2, 0.9, mid, lit)


def _bat_wing(sx, sy, ang, bend, l1, l2, dark, mid, lit, tip):
    c = math.cos(ang)
    s = math.sin(ang)
    ex = sx + c * l1
    ey = sy + s * l1
    a2 = ang + bend
    c2 = math.cos(a2)
    s2 = math.sin(a2)
    wx = ex + c2 * l2
    wy = ey + s2 * l2
    display.set_pen(dark)
    display.triangle(int(sx), int(sy + 8), int(ex), int(ey + 2), int(wx), int(wy))
    display.triangle(int(ex), int(ey + 3), int(wx), int(wy), int(ex + s2 * 10), int(ey - c2 * 10))
    display.set_pen(mid)
    display.triangle(int(sx), int(sy), int(ex), int(ey - 2), int(wx), int(wy - 1))
    _feat(wx, wy, a2 - 0.42, l2 * 0.95, 2.6, mid)
    _feat(wx, wy, a2, l2 * 1.12, 2.4, lit)
    _feat(wx, wy, a2 + 0.4, l2 * 0.78, 2.3, tip)
    display.set_pen(CREAM)
    display.triangle(int(wx + c2 * l2), int(wy + s2 * l2),
                     int(wx + c2 * l2 * 1.18), int(wy + s2 * l2 * 1.18),
                     int(wx + c2 * l2 + s2 * 3), int(wy + s2 * l2 - c2 * 3))
    _rod(sx, sy, ang, l1, 4.4, 2.6, dark, mid)
    _rod(ex, ey, a2, l2, 2.5, 1.0, mid, lit)


def draw_xoc(b, t):
    edge = b.body_pen(X_EDGE)
    mid = b.body_pen(X_MID)
    lit = b.body_pen(X_LIT)
    st = b.state
    step = 5
    i = 45
    nseg = 0
    while i > 0 and nseg < 12:
        j = i - step
        if j < 0:
            j = 0
        x0, y0 = b.trail[i]
        x1, y1 = b.trail[j]
        near = (45 - j) / 45.0
        _seg(x0, y0 + HUD, x1, y1 + HUD, 6.2 + near * 0.9, edge, mid, lit)
        nseg += 1
        if j == 0:
            break
        i = j
    x = int(b.x)
    y = int(b.y) + HUD
    px, py = b.trail[4]
    dx = b.x - px
    dy = b.y - py
    if dx * dx + dy * dy > 4:
        f = 1 if dx > 0 else -1
    else:
        f = b.face if b.face else -1
    display.set_pen(edge)
    tri(x, y, f, -10, 2, 6, 8, -8, 8)
    tri(x, y, f, 0, 3, 14, 7, 4, 8)
    display.set_pen(mid)
    tri(x, y, f, -11, -6, 16, 0, -8, 7)
    tri(x, y, f, 1, -2, 18, 2, 5, 7)
    display.set_pen(lit)
    tri(x, y, f, -8, -8, 10, -6, 2, 0)
    tri(x, y, f, 3, -4, 17, -1, 9, 2)
    display.set_pen(GOLD_D)
    tri(x, y, f, -6, -5, -2, -12, 2, -5)
    tri(x, y, f, 2, -4, 7, -11, 11, -3)
    display.set_pen(GOLD)
    tri(x, y, f, -3, -6, 1, -10, 6, -5)
    op = 0.18
    if st == "tell":
        op = 1.0
    elif st == "spit":
        op = 1.1 + sin64(t * 4) * 0.12
    elif st == "lunge":
        op = 0.72
    if f > 0:
        ua = -0.4
        la = op
    else:
        ua = math.pi + 0.4
        la = math.pi - op
    hx = x + f * 5
    hy = y + 3
    display.set_pen(MOUTH)
    display.triangle(int(hx), int(hy), int(hx + math.cos(ua) * 9), int(hy + math.sin(ua) * 9),
                     int(hx + math.cos(la) * 9), int(hy + math.sin(la) * 9))
    _rod(hx, hy, ua, 12, 3.2, 1.1, edge, lit)
    _rod(hx, hy, la, 11, 2.8, 1.0, edge, X_BELLY)
    ux = hx + math.cos(ua) * 10
    uy = hy + math.sin(ua) * 10
    fang = 7 if op > 0.5 else 4
    display.set_pen(CREAM)
    display.triangle(int(ux), int(uy), int(ux + f * 2), int(uy + fang), int(ux - f * 2), int(uy + 1))
    display.triangle(int(ux - f * 3), int(uy), int(ux - f * 1), int(uy + fang - 1), int(ux - f * 4), int(uy + 1))
    if st == "spit":
        display.set_pen(RED)
        display.triangle(int(hx + math.cos(la) * 6), int(hy + math.sin(la) * 6),
                         int(hx + f * 12), int(hy + 4), int(hx + f * 4), int(hy + 2))
    ecol = RED if st == "tell" or st == "lunge" or st == "spit" else GOLD
    display.set_pen(BLACK)
    display.circle(x + f * 3, y - 2, 4 if ecol == RED else 3)
    display.set_pen(ecol)
    display.circle(x + f * 3, y - 2, 3 if ecol == RED else 2)


def _legtri(ox, oy, f, x, y, ang, ln, w, p):
    a = _flip(ang, f)
    c = math.cos(a)
    s = math.sin(a)
    hx = ox + f * x
    hy = oy + y
    display.set_pen(p)
    display.triangle(int(hx), int(hy), int(hx + c * ln), int(hy + s * ln),
                     int(hx + c * ln * 0.4 - s * w), int(hy + s * ln * 0.4 + c * w))


def draw_jaguar(b, t):
    edge = b.body_pen(J_EDGE)
    mid = b.body_pen(J_MID)
    lit = b.body_pen(J_LIT)
    back_c = b.body_pen(J_BACK)
    oy = int(b.y) + HUD
    ox = int(b.x) + 15
    f = b.face if b.face else -1
    st = b.state
    ph = sin64(t * 3 + 8)
    dy = 0
    reach = 0
    ear_flat = 0
    eye = J_EYE
    ln = 8
    rear_n = 2.05 + ph * 0.55
    front_n = 0.65 - ph * 0.5
    rear_f = 1.55 - ph * 0.4
    front_f = 1.2 + ph * 0.4
    tail_base = 0.4
    tail_amp = 0.35
    if st == "crouch":
        dy = 2
        reach = -1
        ln = 5
        rear_n, front_n = 2.35, 0.95
        rear_f, front_f = 2.05, 1.15
        tail_base = 0.9
        tail_amp = 0.1
        if ((t >> 1) & 1) == 0:
            eye = WHITE
    elif st == "dashtell":
        dy = 2
        reach = -3
        ear_flat = 1
        eye = WHITE
        ln = 5
        rear_n, front_n = 2.5, 0.5
        rear_f, front_f = 2.2, 0.85
        tail_base = 0.15
        tail_amp = 0.04
    elif st == "pounce":
        reach = 3
        ln = 9
        rear_n, front_n = 2.7, 0.22
        rear_f, front_f = 2.35, 0.55
        tail_base = 0.2
        tail_amp = 0.08
    elif st == "dash":
        reach = 3
        ear_flat = 1
        ln = 9
        rear_n = 2.75 + ph * 0.3
        front_n = 0.12 - ph * 0.22
        rear_f = 2.25 - ph * 0.25
        front_f = 0.55 + ph * 0.25
        tail_base = 0.08
        tail_amp = 0.05
    elif st == "stun" or st == "land":
        dy = 2
        reach = -2
        ear_flat = 1
        eye = BLACK
        ln = 6
        rear_n, front_n = 1.9, 1.25
        rear_f, front_f = 1.6, 1.45
        tail_base = 0.95
        tail_amp = 0.12
    sw = sin64(t * 2 + 4) * tail_amp
    rx = ox + f * (-15)
    ty = oy + 9 + dy
    a = _flip(math.pi + tail_base + sw, f)
    ex, ey = _rod(rx, ty, a, 8, 2.4, 1.6, edge, mid)
    a = _flip(math.pi + tail_base + sw * 1.7, f)
    ex, ey = _rod(ex, ey, a, 7, 1.6, 1.0, edge, mid)
    _rod(ex, ey, _flip(math.pi + tail_base + sw * 2.4, f), 6, 1.0, 0.3, edge, edge)
    _legtri(ox, oy, f, -10, 13 + dy, rear_f, ln - 1, 3.2, edge)
    _legtri(ox, oy, f, 2, 12 + dy, front_f, ln - 1, 3.2, edge)
    display.set_pen(edge)
    tri(ox, oy, f, -12, 12 + dy, 6, 15 + dy, -3, 17 + dy)
    tri(ox, oy, f, 2, 13 + dy, 11, 14 + dy, 6, 17 + dy)
    display.set_pen(mid)
    tri(ox, oy, f, -14, 8 + dy, 8, 3 + dy, 2, 16 + dy)
    tri(ox, oy, f, -5, 7 + dy, 13, 7 + dy, 5, 16 + dy)
    display.set_pen(lit)
    tri(ox, oy, f, -13, 8 + dy, -1, 5 + dy, 7, 1 + dy)
    display.set_pen(back_c)
    tri(ox, oy, f, 2, 4 + dy, 8, -3 + dy, 12, 5 + dy)
    display.set_pen(mid)
    tri(ox, oy, f, 7, 4 + dy, 17 + reach, 9 + dy, 10, 13 + dy)
    display.set_pen(edge)
    tri(ox, oy, f, -16, 11 + dy, -9, 6 + dy, -11, 15 + dy)
    display.set_pen(J_SPOT)
    tri(ox, oy, f, -8, 9 + dy, -6, 7 + dy, -7, 11 + dy)
    tri(ox, oy, f, -1, 11 + dy, 1, 13 + dy, 0, 9 + dy)
    tri(ox, oy, f, 5, 6 + dy, 8, 8 + dy, 4, 8 + dy)
    _legtri(ox, oy, f, -6, 14 + dy, rear_n, ln, 4.0, mid)
    _legtri(ox, oy, f, 7, 13 + dy, front_n, ln, 4.0, lit)
    hx = ox + f * (10 + reach)
    hy = oy + 6 + dy
    display.set_pen(mid)
    tri(hx, hy, f, -5, 0, 4, 0, 0, 6)
    display.set_pen(lit)
    tri(hx, hy, f, -3, -2, 5, -2, 2, 3)
    display.set_pen(edge)
    tri(hx, hy, f, 1, 3, 12, 7, 3, 6)
    if ear_flat:
        display.set_pen(mid)
        tri(hx, hy, f, -4, 1, -1, -3, 1, 1)
        display.set_pen(back_c)
        tri(hx, hy, f, 1, 0, 5, -4, 6, 1)
    else:
        display.set_pen(mid)
        tri(hx, hy, f, -3, -1, -1, -9, 1, 0)
        display.set_pen(back_c)
        tri(hx, hy, f, 0, -2, 3, -12, 6, -1)
    display.set_pen(BLACK)
    display.circle(hx + f * 2, hy + 1, 3)
    display.set_pen(eye)
    display.circle(hx + f * 2, hy + 1, 2)
    if st == "stun" or st == "land":
        display.set_pen(GOLD)
        k = 0
        while k < 2:
            a = t * 2 + k * 21
            sx = hx + sin64(a) * 10
            sy = hy - 8 + cos64(a) * 3
            display.triangle(int(sx), int(sy), int(sx + 3), int(sy - 4), int(sx - 2), int(sy - 1))
            k += 1


def draw_eagle(b, t):
    for bx, _ in b.bolts:
        if b.timer < 34:
            if (t >> 1) & 1:
                display.set_pen(BOLT)
                display.rectangle(bx - 1, HUD, 2, 224)
        else:
            display.set_pen(WHITE)
            display.rectangle(bx - 4, HUD, 8, 224)
            display.set_pen(BOLT)
            display.rectangle(bx - 7, HUD, 3, 224)
            display.rectangle(bx + 4, HUD, 3, 224)
    edge = b.body_pen(E_EDGE)
    mid = b.body_pen(E_MID)
    lit = b.body_pen(E_LIT)
    tip = b.body_pen(E_TIP)
    st = b.state
    f = b.face if b.face else -1
    cx = int(b.x) + 15
    cy = int(b.y) + HUD + 9
    fl = sin64(t * 3)
    n = 4
    fln = 12
    l1, l2 = 15, 12
    if st == "dive":
        back = math.pi if f > 0 else 0.0
        ar = back + 0.7
        al = back - 0.7
        br, bl = 0.45, -0.45
        l1, l2 = 8, 6
        n = 2
        fln = 6
    elif st == "glide":
        ar, al = 0.42, math.pi - 0.42
        br, bl = 0.18, -0.18
        l1, l2 = 17, 14
        fln = 13
    elif st == "tell":
        ar, al = -1.3, math.pi + 1.3
        br, bl = 0.08, -0.08
        l1, l2 = 16, 13
        fln = 10
    elif st == "storm":
        ar, al = -0.8, math.pi + 0.8
        br, bl = 0.15, -0.15
        l1, l2 = 17, 15
        fln = 13
    else:
        ar = -0.15 - fl * 0.95
        al = math.pi + 0.15 + fl * 0.95
        br, bl = 0.4, -0.4
    if f > 0:
        _wing(cx - 4, cy - 2, al, bl, l1, l2, edge, edge, mid, mid, n, fln, -1)
        _wing(cx + 4, cy - 2, ar, br, l1, l2, edge, mid, lit, tip, n, fln, 1)
    else:
        _wing(cx + 4, cy - 2, ar, br, l1, l2, edge, edge, mid, mid, n, fln, 1)
        _wing(cx - 4, cy - 2, al, bl, l1, l2, edge, mid, lit, tip, n, fln, -1)
    tax = cx - f * 9
    tay = cy + 2
    _feat(tax, tay, _flip(math.pi - 0.2, f), 12, 3.0, tip)
    _feat(tax, tay, _flip(math.pi + 0.35, f), 10, 2.6, lit)
    _feat(tax, tay, _flip(math.pi + 0.75, f), 8, 2.2, mid)
    display.set_pen(edge)
    poly(_EAGLE_MASS, cx, cy, 1)
    display.set_pen(mid)
    display.triangle(cx - 11, cy - 4, cx + 9, cy - 2, cx + 1, cy + 6)
    display.triangle(cx - 2, cy, cx + 13, cy + 2, cx + 4, cy + 8)
    display.set_pen(lit)
    display.triangle(cx - 7, cy - 3, cx + 2, cy - 8, cx + 8, cy - 1)
    hx = cx + f * 7
    hy = cy - 4
    display.set_pen(E_HEAD_D)
    tri(hx, hy, f, -3, 4, 5, -5, 11, 1)
    tri(hx, hy, f, -1, 3, 10, 2, 4, 7)
    display.set_pen(WHITE)
    tri(hx, hy, f, -1, 1, 5, -5, 9, 0)
    tri(hx, hy, f, 1, 2, 8, 0, 5, 5)
    beak = 9 if st == "tell" or st == "dive" else 4
    display.set_pen(GOLD_D)
    tri(hx, hy, f, 6, 2, 14, beak, 7, 6)
    display.set_pen(GOLD)
    tri(hx, hy, f, 5, -1, 16, 1, 8, 3)
    display.set_pen(edge)
    display.triangle(cx - 3, cy + 8, cx, cy + 14, cx - 6, cy + 10)
    display.triangle(cx + 2, cy + 8, cx + 6, cy + 14, cx + 1, cy + 11)
    display.set_pen(GOLD)
    tri(hx, hy, f, 2, -4, 5, -7, 7, -2)
    display.set_pen(RED if st == "tell" else BLACK)
    display.circle(hx + f * 4, hy, 2)


def draw_watcher(b, t):
    if b.emerge > 0 and (b.emerge >> 1) & 1:
        return
    edge = b.body_pen(W_EDGE)
    mid = b.body_pen(W_MID)
    lit = b.body_pen(W_LIT)
    st = b.state
    f = b.face if b.face else -1
    x = int(b.x)
    y = int(b.y) + HUD
    hunting = st == "alert" or st == "chase" or st == "gloat"
    lean = 0
    drop = 0
    if st == "chase":
        lean = 5 * f
    elif st == "alert":
        lean = -2 * f
    elif st == "stagger":
        lean = -4 * f
        drop = 0
    ph = sin64(t * 2)
    if st == "chase":
        swing = 0.6
    elif st == "patrol" or st == "idle":
        swing = 0.3
    else:
        swing = 0.0
        ph = 0.0
    if st == "stagger":
        a0, a1 = 0.75, 2.35
        d0, d1 = 0.85, -0.7
    elif st == "alert":
        a0, a1 = 1.05, 2.05
        d0, d1 = 0.5, -0.45
    else:
        a0 = 1.4 + ph * swing
        a1 = 1.4 - ph * swing
        d0, d1 = 0.3, -0.28
    display.set_pen(edge)
    poly(_WATCH_MASS, x, y, 1)
    k0x, k0y = _rod(x + 5, y + 19, a0, 7, 4.2, 3.0, edge, mid)
    f0x, f0y = _rod(k0x, k0y, a0 + d0, 6, 2.8, 2.0, edge, mid)
    k1x, k1y = _rod(x + 16, y + 19, a1, 7, 4.2, 3.0, edge, mid)
    f1x, f1y = _rod(k1x, k1y, a1 + d1, 6, 2.8, 2.0, edge, mid)
    display.set_pen(lit)
    display.triangle(int(k0x - 3), int(k0y), int(k0x), int(k0y - 5), int(k0x + 3), int(k0y))
    display.triangle(int(k1x - 3), int(k1y), int(k1x), int(k1y - 5), int(k1x + 3), int(k1y))
    display.set_pen(edge)
    display.triangle(int(f0x - 4), int(f0y), int(f0x + 3), int(f0y + 1), int(f0x), int(f0y + 4))
    display.triangle(int(f1x - 3), int(f1y), int(f1x + 4), int(f1y + 1), int(f1x + 1), int(f1y + 4))
    lx = x + lean
    ly = y + drop
    display.set_pen(edge)
    display.triangle(x - 1, y + 15, x + 23, y + 14, x + 6, y + 29)
    display.triangle(x + 20, y + 16, x + 27, y + 20, x + 16, y + 28)
    display.triangle(x - 4, y + 16, x + 3, y + 14, x - 1, y + 26)
    display.set_pen(mid)
    display.triangle(lx + 3, ly + 11, lx + 13, ly + 8, lx + 7, ly + 22)
    display.triangle(lx + 11, ly + 9, lx + 22, ly + 13, lx + 14, ly + 23)
    display.set_pen(lit)
    display.triangle(lx + 6, ly + 9, lx + 13, ly + 4, lx + 17, ly + 12)
    display.triangle(lx - 1, ly + 10, lx + 5, ly + 5, lx + 7, ly + 13)
    display.triangle(lx + 16, ly + 11, lx + 24, ly + 6, lx + 26, ly + 14)
    if st == "alert":
        la, lb = math.pi + 1.2, -1.2
        ba, bb = -0.25, 0.25
    elif st == "chase":
        if f > 0:
            la, lb = 0.4, 2.6
        else:
            la, lb = math.pi - 0.1, 0.7
        ba, bb = 0.35, -0.3
    elif st == "stagger":
        la, lb = 2.3, 0.75
        ba, bb = 0.7, -0.6
    else:
        la, lb = math.pi - 0.5, 0.5
        ba, bb = 0.2, -0.2
    hax, hay = _rod(lx + 1, ly + 13, la, 8, 3.6, 2.4, edge, mid)
    hax, hay = _rod(hax, hay, la + ba, 7, 2.4, 1.2, edge, lit)
    hbx, hby = _rod(lx + 20, ly + 13, lb, 8, 3.6, 2.4, edge, mid)
    hbx, hby = _rod(hbx, hby, lb + bb, 7, 2.4, 1.2, edge, lit)
    display.set_pen(lit)
    display.triangle(int(hax - 2), int(hay), int(hax - 5), int(hay + 4), int(hax + 1), int(hay + 2))
    display.triangle(int(hbx + 2), int(hby), int(hbx + 5), int(hby + 4), int(hbx - 1), int(hby + 2))
    display.set_pen(edge)
    poly(_HELM, lx, ly, 1)
    display.set_pen(mid)
    display.triangle(lx + 5, ly + 3, lx + 12, ly + 6, lx + 8, ly + 12)
    display.triangle(lx + 12, ly + 4, lx + 19, ly + 5, lx + 15, ly + 12)
    display.set_pen(lit)
    display.triangle(lx + 7, ly + 1, lx + 12, ly - 2, lx + 15, ly + 3)
    horn = 4 if st == "stagger" else 11
    display.triangle(lx + 4, ly + 2, lx + 8, ly - horn, lx + 11, ly + 1)
    display.triangle(lx + 12, ly + 2, lx + 16, ly - 10, lx + 19, ly + 2)
    display.set_pen(edge)
    display.triangle(lx + 6, ly, lx + 9, ly - horn + 4, lx + 10, ly + 1)
    display.set_pen(BLACK)
    display.triangle(lx + 5, ly + 5, lx + 17, ly + 4, lx + 16, ly + 9)
    display.triangle(lx + 5, ly + 5, lx + 7, ly + 10, lx + 16, ly + 9)
    ex = lx + 11 + (f * 3 if hunting else int(b.eye * 4))
    ey = ly + 7
    display.set_pen(BLACK)
    display.circle(ex, ey, 4 if hunting else 3)
    if st == "stagger" and ((t >> 1) & 1) == 0:
        eye = WHITE
    elif hunting:
        eye = RED
    else:
        eye = GOLD
    display.set_pen(eye)
    display.circle(ex, ey, 3 if hunting else 2)
    if hunting:
        reach = 46
        x2 = ex + f * reach
        display.set_pen(SIGHT)
        if f > 0:
            display.rectangle(ex, ey - 1, reach, 3)
        else:
            display.rectangle(x2, ey - 1, reach, 3)
        display.set_pen(SIGHT_HOT)
        display.line(ex, ey, x2, ey + int(sin64(t * 3) * 4))
    n = 3 - b.hp
    if n < 0:
        n = 0
    k = 0
    display.set_pen(BLACK)
    while k < n:
        display.line(lx + 6 + k * 5, ly + 9, lx + 10 + k * 5, ly + 20)
        k += 1


def draw_camazotz(b, t):
    ph3 = b.phase() >= 3
    if ph3:
        edge = b.body_pen(C3_EDGE)
        mid = b.body_pen(C3_MID)
        lit = b.body_pen(C3_LIT)
        tip = b.body_pen(C3_TIP)
        eye_c = GOLD
    else:
        edge = b.body_pen(C_EDGE)
        mid = b.body_pen(C_MID)
        lit = b.body_pen(C_LIT)
        tip = b.body_pen(C_TIP)
        eye_c = JADE
    st = b.state
    f = b.face if b.face else -1
    x = int(b.x)
    y = int(b.y) + HUD
    ox = x + 17
    oy = y + 12
    fl = sin64(t * 3)
    l1, l2 = 18, 14
    if st == "dive":
        back = math.pi if f > 0 else 0.0
        ar = back + 0.55
        al = back - 0.55
        br, bl = 0.4, -0.4
        l1, l2 = 10, 8
    elif st == "glide":
        ar, al = 0.5, math.pi - 0.5
        br, bl = 0.16, -0.16
        l1, l2 = 20, 16
    elif st == "tell" or st == "summon":
        ar, al = -1.2, math.pi + 1.2
        br, bl = 0.08, -0.08
    elif st == "screech":
        ar, al = -0.05, math.pi + 0.05
        br, bl = 0.02, -0.02
        l1, l2 = 21, 17
    else:
        ar = -0.22 - fl * 0.85
        al = math.pi + 0.22 + fl * 0.85
        br, bl = 0.36, -0.36
    _bat_wing(ox + 7, oy - 4, ar, br, l1, l2, edge, mid, lit, tip)
    _bat_wing(ox - 7, oy - 4, al, bl, l1, l2, edge, mid, lit, tip)
    display.set_pen(edge)
    poly(_CAM_MASS, ox, oy, 1)
    display.set_pen(mid)
    display.triangle(ox - 12, oy - 4, ox + 12, oy - 2, ox + 1, oy + 7)
    display.triangle(ox - 4, oy - 1, ox + 15, oy + 1, ox + 5, oy + 9)
    display.set_pen(lit)
    display.triangle(ox - 5, oy - 6, ox + 6, oy - 10, ox + 3, oy)
    display.set_pen(edge)
    display.triangle(ox - 8, oy + 9, ox - 13, oy + 16, ox - 3, oy + 12)
    display.triangle(ox + 5, oy + 9, ox + 12, oy + 16, ox + 2, oy + 12)
    tri(ox, oy - 8, 1, -7, 1, -16, -14, -2, -2)
    tri(ox, oy - 8, 1, 5, 1, 15, -12, 2, -1)
    display.set_pen(GOLD_D)
    display.triangle(ox - 12, oy - 8, ox - 8, oy - 14, ox - 4, oy - 7)
    display.triangle(ox + 4, oy - 7, ox + 9, oy - 14, ox + 12, oy - 6)
    display.set_pen(GOLD)
    display.triangle(ox - 9, oy - 9, ox - 7, oy - 17, ox - 4, oy - 9)
    display.triangle(ox - 2, oy - 10, ox + 1, oy - 19, ox + 4, oy - 10)
    gem = RED if ph3 else JADE
    display.set_pen(gem)
    display.triangle(ox - 2, oy - 11, ox, oy - 15, ox + 2, oy - 11)
    open_m = st == "tell" or st == "screech" or st == "dive" or st == "summon"
    display.set_pen(MOUTH)
    if open_m:
        display.triangle(ox - 6, oy + 2, ox + 6, oy + 2, ox, oy + 9)
    else:
        display.triangle(ox - 4, oy + 3, ox + 4, oy + 3, ox, oy + 6)
    fang = 10 if open_m else 5
    display.set_pen(CREAM)
    display.triangle(ox - 3, oy + 3, ox - 1, oy + 3, ox - 3, oy + fang)
    display.triangle(ox + 1, oy + 3, ox + 3, oy + 3, ox + 3, oy + fang)
    er = 4 if ph3 else 3
    display.set_pen(BLACK)
    display.circle(ox - 5 + f, oy - 2, er)
    display.circle(ox + 5 + f, oy - 2, er)
    display.set_pen(eye_c)
    display.circle(ox - 5 + f, oy - 2, 3 if ph3 else 2)
    display.circle(ox + 5 + f, oy - 2, 3 if ph3 else 2)
    if ph3:
        display.set_pen(WHITE)
        display.circle(ox - 5 + f, oy - 2, 1)
        display.circle(ox + 5 + f, oy - 2, 1)
