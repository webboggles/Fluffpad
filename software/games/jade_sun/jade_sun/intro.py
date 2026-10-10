"""Boot cinematic and the illustrated prologue."""
import math
import random
from .hw import display, snapshot_bg, restore_bg
from .gfx import pen, _gradient, _silhouette, WHITE, GOLD, JADE, JADE_D, CREAM, RED, SHADOW
from . import sprites, ui, story

SX, SY = 160, 74
END = 290
DROP = 228
RESTORE = 266


def backdrop(dark=False):
    random.seed(7)
    if dark:
        _gradient((2, 2, 8), (16, 8, 22), 0, 240, 30)
        display.set_pen(pen(120, 110, 150))
    else:
        _gradient((4, 6, 20), (20, 50, 46), 0, 240, 30)
        display.set_pen(pen(220, 255, 230))
    for _ in range(70):
        display.pixel(random.randint(0, 319), random.randint(0, 140))
    display.set_pen(pen(10, 10, 18) if dark else pen(14, 34, 34))
    for i in range(9):
        w = 170 - i * 18
        display.rectangle(160 - w // 2, 210 - i * 11, w, 12)
    display.rectangle(150, 210 - 9 * 11 - 8, 20, 10)
    _silhouette((6, 8, 10) if dark else (8, 24, 18), 220, 40, 50)
    display.set_pen(pen(4, 6, 6) if dark else pen(6, 16, 12))
    display.rectangle(0, 226, 320, 14)
    snapshot_bg()


def sun(x, y, t, rays=True):
    cos, sin = math.cos, math.sin
    if rays:
        for k in range(12):
            a = t * 0.02 + k * 0.5236
            ln = 60 + 10 * sin(t * 0.08 + k)
            display.set_pen(pen(28, 86, 58) if k & 1 else pen(40, 120, 80))
            display.triangle(x, y, x + int(ln * cos(a)), y + int(ln * sin(a)),
                             x + int(ln * cos(a + 0.16)), y + int(ln * sin(a + 0.16)))
    r = 18 + int(sin(t * 0.05) * 2)
    display.set_pen(pen(20, 80, 50))
    display.circle(x, y, r + 8)
    display.set_pen(JADE_D)
    display.circle(x, y, r)
    display.set_pen(JADE)
    display.circle(x, y, r - 5)
    display.set_pen(pen(190, 255, 220))
    display.circle(x - 5, y - 5, 4)


def broken_sun(x, y, t):
    display.set_pen(pen(120, 10, 30) if (t >> 3) & 1 else pen(90, 0, 20))
    display.circle(x, y, 24)
    display.set_pen(pen(8, 4, 12))
    display.circle(x, y, 21)
    display.set_pen(pen(160, 40, 50))
    for k in range(5):
        a = k * 1.256 + 0.3
        display.line(x, y, x + int(20 * math.cos(a)), y + int(20 * math.sin(a)))


def bat(x, y, t, s=1.0):
    x, y = int(x), int(y)
    f = math.sin(t * 0.55)
    wy = int(-22 * f * s)
    body = pen(16, 4, 22)
    display.set_pen(body)
    for side in (-1, 1):
        display.triangle(x + side * int(8 * s), y, x + side * int(56 * s), y + wy, x + side * int(18 * s), y + int(16 * s))
        display.triangle(x + side * int(56 * s), y + wy, x + side * int(34 * s), y + int(20 * s), x + side * int(18 * s), y + int(16 * s))
        display.triangle(x + side * int(4 * s), y - int(8 * s), x + side * int(10 * s), y - int(24 * s), x + side * int(12 * s), y - int(6 * s))
    display.circle(x, y + int(4 * s), int(14 * s))
    display.set_pen(RED)
    display.circle(x - int(5 * s), y + int(2 * s), max(1, int(2 * s)))
    display.circle(x + int(5 * s), y + int(2 * s), max(1, int(2 * s)))
    display.set_pen(WHITE)
    display.triangle(x - int(4 * s), y + int(10 * s), x - int(2 * s), y + int(10 * s), x - int(3 * s), y + int(14 * s))
    display.triangle(x + int(2 * s), y + int(10 * s), x + int(4 * s), y + int(10 * s), x + int(3 * s), y + int(14 * s))


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
    lines = ui.wrap(s, 280, 2)
    ui.panel(8, 236 - 18 - len(lines) * 20, 304, len(lines) * 20 + 12)
    y = 236 - 12 - len(lines) * 20
    left = int(shown)
    for ln in lines:
        if left <= 0:
            break
        ui.center(ln[:left] if left < len(ln) else ln, y, 2, CREAM)
        left -= len(ln)
        y += 20
    display.set_pen(SHADOW)
    display.rectangle(0, 0, 320, 12)
    ui.text("B next   + skip", 4, 2, 1, pen(110, 120, 130), False)
    for i in range(len(story.PROLOGUE)):
        display.set_pen(GOLD if i == page else pen(60, 60, 70))
        display.rectangle(250 + i * 11, 4, 8, 4)
