"""Boot cinematic and the illustrated prologue."""
import math
from .hw import display, snapshot_bg, restore_bg
from .gfx import pen, _gradient, WHITE, GOLD, JADE, JADE_D, CREAM, RED, SHADOW
from . import sprites, ui, story, rig

SX, SY = 160, 74
END = 290
DROP = 228
RESTORE = 266

_STONE = pen(46, 62, 52)
_STONE_LIT = pen(128, 168, 118)
_STONE_DARK = pen(16, 26, 22)
_STONE_N = pen(28, 14, 26)
_STONE_LIT_N = pen(72, 28, 40)
_STONE_DARK_N = pen(10, 4, 12)
_TREE = pen(8, 28, 18)
_TREE_LIT = pen(28, 72, 42)
_TREE_N = pen(8, 8, 14)
_TREE_LIT_N = pen(24, 16, 28)
_GROUND = pen(6, 16, 12)
_GROUND_N = pen(10, 4, 12)
_STAR = pen(220, 230, 214)
_STAR_N = pen(180, 90, 110)
_RAY = pen(36, 120, 78)
_RAY_LIT = pen(90, 200, 140)
_BAT = pen(36, 12, 44)
_BAT_LIT = pen(96, 42, 108)
_BAT_DARK = pen(14, 4, 18)

# Pyramid courses: left, right, top, bottom, top inset. Each course is two triangles.
_COURSES = (
    (146, 174, 96, 108, 0),
    (122, 198, 108, 120, 8),
    (94, 226, 120, 134, 10),
    (60, 260, 134, 148, 12),
    (24, 296, 148, 164, 14),
)
_TREES = (
    (0, 36, 108, 160),
    (22, 64, 124, 166),
    (254, 298, 120, 166),
    (282, 320, 104, 160),
)
_STARS = (
    (16, 16, 2), (42, 36, 1), (68, 14, 2), (96, 42, 1),
    (214, 18, 1), (246, 34, 2), (278, 12, 1), (304, 40, 2),
    (18, 62, 1), (304, 66, 1), (124, 12, 1), (196, 22, 1),
)


def _dia(x, y, r, lit, dark):
    display.set_pen(lit)
    display.triangle(x, y - r, x - r, y, x + r, y)
    display.set_pen(dark)
    display.triangle(x - r, y, x + r, y, x, y + r)


def _tree(x0, x1, top, base, lit, dark):
    mid = (x0 + x1) // 2
    display.set_pen(dark)
    display.triangle(x0, base, x1, base, mid, top)
    display.set_pen(lit)
    span = (base - top) // 3
    display.triangle(x0 + 6, top + span, x1 - 6, top + span, mid, top)


def _slab(x0, x1, y0, y1, inset, mid, lit, dark):
    tx0 = x0 + inset
    tx1 = x1 - inset
    display.set_pen(mid)
    display.polygon([(x0, y1), (x1, y1), (tx1, y0), (tx0, y0)])
    display.set_pen(lit)
    display.triangle(tx0 + 4, y0 + 4, (tx0 + tx1) // 2, y0, tx1 - 4, y0 + 4)
    display.set_pen(dark)
    display.triangle(x0 + 6, y1 - 3, (x0 + x1) // 2, y1 - 1, x1 - 6, y1 - 3)


def backdrop(dark=False):
    if dark:
        _gradient((4, 2, 10), (28, 8, 18), 0, 240, 30)
        star, tree, tree_lit = _STAR_N, _TREE_N, _TREE_LIT_N
        stone, lit, lo = _STONE_N, _STONE_LIT_N, _STONE_DARK_N
        ground = _GROUND_N
    else:
        _gradient((6, 10, 26), (16, 48, 46), 0, 240, 30)
        star, tree, tree_lit = _STAR, _TREE, _TREE_LIT
        stone, lit, lo = _STONE, _STONE_LIT, _STONE_DARK
        ground = _GROUND
    for x, y, r in _STARS:
        _dia(x, y, r, star, lo)
    for x0, x1, top, base in _TREES:
        _tree(x0, x1, top, base, tree_lit, tree)
    for x0, x1, y0, y1, inset in _COURSES:
        _slab(x0, x1, y0, y1, inset, stone, lit, lo)
    if dark:
        display.set_pen(pen(180, 40, 52))
        display.line(112, 122, 132, 138)
        display.line(132, 138, 118, 156)
    else:
        _dia(160, 100, 3, pen(214, 255, 232), JADE)
    display.set_pen(ground)
    display.polygon([
        (0, 200), (40, 186), (100, 196), (160, 176), (220, 194),
        (280, 180), (319, 192), (319, 239), (0, 239),
    ])
    snapshot_bg()


def sun(x, y, t, rays=True):
    if rays:
        pulse = rig.sin64(t)
        ln = 36 + int(pulse * 5)
        k = 0
        while k < 8:
            a = (int(t) + k * 8) & 63
            ca = rig.cos64(a)
            sa = rig.sin64(a)
            px, py = -sa, ca
            display.set_pen(_RAY_LIT if sa < 0 else _RAY)
            display.triangle(
                x + int(ca * 16), y + int(sa * 16),
                x + int(ca * ln + px * 4), y + int(sa * ln + py * 4),
                x + int(ca * ln - px * 4), y + int(sa * ln - py * 4),
            )
            k += 1
    rig.gem(x, y, 14, pen(214, 255, 232), JADE, JADE_D, 8)


def broken_sun(x, y, t):
    hot = (t >> 3) & 1
    display.set_pen(pen(150, 28, 40) if hot else pen(96, 14, 26))
    rig.ngon(x, y, 26, 8, -1.5708)
    display.set_pen(pen(12, 4, 16))
    rig.ngon(x, y, 16, 8, -1.5708)
    display.set_pen(pen(220, 64, 72))
    display.line(x - 16, y - 6, x - 2, y + 3)
    display.line(x - 2, y + 3, x + 8, y - 8)
    display.line(x + 8, y - 8, x + 18, y + 6)
    display.set_pen(JADE)
    display.triangle(x + 16, y - 16, x + 32, y - 4, x + 18, y + 2)
    display.set_pen(pen(214, 255, 232))
    display.triangle(x + 18, y - 12, x + 26, y - 6, x + 20, y - 4)


def bat(x, y, t, s=1.0):
    x, y = int(x), int(y)
    flap = rig.sin64(int(t) * 4)
    rise = int((-18 + 16 * flap) * s)
    span = int(54 * s)
    body = int(7 * s)
    for side in (-1, 1):
        ix = x + side * body
        tx = x + side * span
        ty = y + rise
        lx = x + side * int(20 * s)
        ly = y + int(14 * s)
        mx = x + side * int(32 * s)
        my = y + int(rise * 0.4)
        display.set_pen(_BAT_DARK)
        display.triangle(ix, y, tx, ty, lx, ly)
        display.set_pen(_BAT_LIT if rise < -6 else _BAT)
        display.triangle(ix, y - int(2 * s), tx, ty, mx, my)
        display.set_pen(_BAT_LIT)
        display.line(ix, y, tx, ty)
        display.triangle(
            x + side * int(3 * s), y - int(4 * s),
            x + side * int(8 * s), y - int(2 * s),
            x + side * int(6 * s), y - int(16 * s),
        )
    rig.gem(x, y + int(2 * s), max(4, int(10 * s)), _BAT_LIT, _BAT, _BAT_DARK, 6)
    display.set_pen(RED)
    er = max(1, int(2 * s))
    display.circle(x - int(4 * s), y + int(1 * s), er)
    display.circle(x + int(4 * s), y + int(1 * s), er)
    display.set_pen(CREAM)
    display.triangle(x - int(3 * s), y + int(8 * s), x - int(1 * s), y + int(8 * s), x - int(2 * s), y + int(13 * s))
    display.triangle(x + int(1 * s), y + int(8 * s), x + int(3 * s), y + int(8 * s), x + int(2 * s), y + int(13 * s))


def _ease_out(u):
    return 1 - (1 - u) ** 3


def _bounce(u):
    if u < 1 / 2.75:
        return 7.5625 * u * u
    if u < 2 / 2.75:
        u -= 1.5 / 2.75
        return 7.5625 * u * u + 0.75
    if u < 2.5 / 2.75:
        u -= 2.25 / 2.75
        return 7.5625 * u * u + 0.9375
    u -= 2.625 / 2.75
    return 7.5625 * u * u + 0.984375


class Intro:
    def __init__(self, g):
        self.g = g
        self.t = 0
        self.dark = False
        self.shards = []
        backdrop(False)
        display.set_backlight(0.0)
        g.fx.set_ambience("fireflies", None)
        g.audio.play_song("intro", True)
        g.mood.override = (0, 0, 0)
        s = story.TITLE
        x0 = (320 - display.measure_text(s, 4)) // 2
        sp = display.measure_text("AA", 4) - 2 * display.measure_text("A", 4)
        self.lx = [x0 + (display.measure_text(s[:i], 4) + sp if i else 0) for i in range(len(s))]
        self.landed = [False] * len(s)
        self.home = [(-20, -20), (340, -20), (340, 260), (-20, 260)]

    def update(self, inp):
        """Returns 'done', 'skip' or None."""
        g = self.g
        t = self.t
        a = g.audio
        fx = g.fx
        if t > 8 and inp.any_pressed():
            return "skip"
        if t <= 30:
            display.set_backlight(t / 30)
        if t == 108:
            a.sfx_play("screech", 3)
            g.mood.flash((120, 0, 160), 24)
        if t == 140:
            a.play_song(None)
            a.sfx_play("boom", 4)
            fx.white(3)
            fx.kick(14)
            display.set_backlight(1.0)
            backdrop(True)
            self.dark = True
            fx.burst(SX, SY, (60, 230, 150), 40, 5, 30, 0.05, 3)
            fx.ring(SX, SY, (255, 255, 255), 20, 6, 16)
            for k in range(4):
                ang = 0.785 + k * 1.5708
                self.shards.append([float(SX), float(SY), math.cos(ang) * 1.5, math.sin(ang) * 1.5, True])
            g.inp.set_pad_leds(15)
            g.mood.flash((255, 255, 255), 6)
        if t == 147:
            a.sfx_play("thunder", 4)
        if 140 < t < 230:
            mask = 0
            for i, s in enumerate(self.shards):
                if not s[4]:
                    continue
                s[2] *= 1.07
                s[3] *= 1.07
                s[0] += s[2]
                s[1] += s[3]
                fx.burst(s[0], s[1], (60, 230, 150), 2, 1, 10, 0, 2)
                if s[0] < -20 or s[0] > 340 or s[1] < -20 or s[1] > 260:
                    s[4] = False
                    a.sfx_tone(900 - i * 150, 300, 4, 1200, 3)
                else:
                    mask |= 1 << i
            g.inp.set_pad_leds(mask)
        if t == 170:
            display.set_backlight(0.65)
        if t in (196, 206):
            a.sfx_play("heartbeat", 3)
            g.mood.flash((140, 0, 0), 8)
        if t >= DROP:
            for i in range(len(self.lx)):
                if not self.landed[i] and t - (DROP + 3 * i) >= 5:
                    self.landed[i] = True
                    a.chime()
                    fx.burst(self.lx[i] + 10, 140, (255, 220, 120), 5, 2, 12, 0.1, 2)
        if t == RESTORE:
            backdrop(False)
            self.dark = False
            display.set_backlight(1.0)
            fx.white(3, JADE)
            fx.kick(8)
            a.sfx_play("glyph", 4)
            g.mood.flash((60, 255, 160), 30)
        if RESTORE <= t < RESTORE + 20:
            g.inp.set_pad_leds((1 << min(4, (t - RESTORE) // 4 + 1)) - 1)
        if t == END - 4:
            g.inp.set_pad_leds(0)
        self.t += 1
        return "done" if t >= END else None

    def draw(self):
        g = self.g
        t = self.t
        dx, dy = g.fx.offset()
        restore_bg(dx, dy)
        if t < 140:
            u = _ease_out(min(1.0, max(0.0, (t - 45) / 65)))
            if u > 0:
                display.set_clip(0, 0, 320, 106)
                sun(SX, int(SY + 70 * (1 - u)), t, u > 0.2)
                display.remove_clip()
            if 100 <= t < 160:
                k = (t - 100) / 50
                bx = -70 + k * 460
                by = 30 + math.sin(k * 3.14) * 40
                bat(bx, by, t, 1.1)
        elif t < RESTORE:
            broken_sun(SX, SY, t)
            if t < 160:
                k = (t - 100) / 50
                bat(-70 + k * 460, 30 + math.sin(k * 3.14) * 40, t, 1.1)
            for s in self.shards:
                if s[4]:
                    sprites.draw_item("glyph", int(s[0]), int(s[1]), t)
        else:
            sun(SX, SY, t)
            k = _ease_out(min(1.0, (t - RESTORE) / 20))
            r = 22
            for i in range(4):
                ang = t * 0.02 + i * 1.5708
                tx, ty = SX + r * math.cos(ang), SY + r * math.sin(ang)
                hx, hy = self.home[i]
                sprites.draw_item("glyph", int(hx + (tx - hx) * k), int(hy + (ty - hy) * k), t)
        if t < 60:
            c = min(1.0, t / 20, (60 - t) / 15)
            ui.center("a legend for Maya", 110, 2, pen(int(255 * c), int(244 * c), int(214 * c)), False)
        if 180 <= t < DROP:
            s = "The Jade Sun is broken."
            n = min(len(s), (t - 180) // 2)
            ui.center(s[:n], 150, 2, CREAM)
        if t >= DROP:
            title = story.TITLE
            for i, ch in enumerate(title):
                u = (t - (DROP + 3 * i)) / 14
                if u <= 0:
                    continue
                y = -40 + 152 * _bounce(min(1.0, u))
                ui.text(ch, self.lx[i], int(y), 4, GOLD)
        if t >= RESTORE + 4:
            k = _ease_out(min(1.0, (t - RESTORE - 4) / 12))
            w = display.measure_text(story.SUBTITLE, 2)
            x = int(340 + ((320 - w) // 2 - 340) * k)
            ui.text(story.SUBTITLE, x, 146, 2, JADE)
        g.fx.draw_screen()
        g.fx.ambience(t)
        if g.fx.flash > 0:
            g.fx.flash -= 1
            display.set_pen(g.fx.flash_pen)
            display.clear()
        if (t >> 4) & 1 and 40 < t < DROP:
            ui.center("press any button", 228, 1, pen(70, 80, 90), False)


# --- prologue ----------------------------------------------------------------
def prologue_bake(page):
    backdrop(page >= 3)


def _bar():
    display.set_pen(SHADOW)
    display.polygon([(0, 5), (14, 0), (306, 0), (319, 5), (306, 12), (14, 12)])
    display.set_pen(pen(255, 220, 150))
    display.triangle(20, 3, 90, 1, 160, 3)
    display.triangle(160, 3, 230, 1, 300, 3)
    _dia(10, 6, 3, pen(214, 255, 232), JADE)


def prologue(g, page, shown, t):
    restore_bg()
    if page == 0:
        sun(SX, SY, t)
    elif page == 1:
        sun(SX, SY, t)
        for k in range(3):
            ph = (t + k * 20) % 60
            ui.text("z", 168 + k * 6 + int(math.sin(ph * 0.2) * 4), 110 - ph, 1 + (ph > 30), CREAM, False)
    elif page == 2:
        sun(SX, SY, t)
        bat(SX + math.sin(t * 0.05) * 50, 64 + math.sin(t * 0.09) * 10, t, 0.8)
    elif page == 3:
        broken_sun(SX, SY, t)
        for i in range(4):
            ang = 0.785 + i * 1.5708
            d = 26 + (t * 2 + i * 30) % 110
            sprites.draw_item("glyph", int(SX + d * math.cos(ang)), int(SY + d * math.sin(ang)), t)
    elif page == 4:
        broken_sun(SX, SY, t)
        if t % 22 == 0:
            g.fx.ring(160, 205, (180, 60, 40), 14, 3, 18)
            g.audio.sfx_play("drum", 2)
    else:
        blink = shown < 30 or (t % 70) < 4
        sprites.draw_fluff(g.skin, 145, 58, 1, t, True, 0, scale=3, blink=blink)
        if not blink and (t >> 3) & 1:
            display.set_pen(WHITE)
            display.pixel(166, 50)
    g.fx.draw_screen()
    g.fx.ambience(t)
    s = story.PROLOGUE[page]
    lines = ui.wrap(s, 272, 2)
    n = len(lines)
    top = 236 - 24 - n * 18
    ui.panel(8, top, 304, n * 18 + 20)
    y = top + 12
    left = int(shown)
    for ln in lines:
        if left <= 0:
            break
        ui.center(ln[:left] if left < len(ln) else ln, y, 2, CREAM)
        left -= len(ln)
        y += 18
    _bar()
    ui.text("B next   + skip", 20, 2, 1, pen(190, 196, 204), False)
    for i in range(len(story.PROLOGUE)):
        col = GOLD if i == page else pen(70, 68, 80)
        dark = pen(120, 80, 20) if i == page else pen(36, 34, 44)
        _dia(248 + i * 11, 6, 2, col, dark)
