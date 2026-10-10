"""HUD, dialogue, menus and full-screen scenes."""
import math
from .hw import display
from .gfx import pen, shade, HUD, WHITE, BLACK, GOLD, JADE, JADE_D, RED, CREAM, SHADOW, DARK, GREY, ZONES
from . import sprites
from . import story
from .world_data import ROOMS

BOX_Y = 164


def text(s, x, y, scale=2, col=WHITE, shadow=True, wrap=320):
    if shadow:
        display.set_pen(BLACK)
        display.text(s, x + 1, y + 1, wrap, scale)
    display.set_pen(col)
    display.text(s, x, y, wrap, scale)


def center(s, y, scale=2, col=WHITE, shadow=True):
    w = display.measure_text(s, scale)
    text(s, (320 - w) // 2, y, scale, col, shadow)


def wrap(s, width, scale=2):
    out = []
    line = ""
    for word in s.split(" "):
        test = word if not line else line + " " + word
        if display.measure_text(test, scale) <= width:
            line = test
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def panel(x, y, w, h, border=GOLD):
    display.set_pen(SHADOW)
    display.rectangle(x, y, w, h)
    display.set_pen(border)
    display.rectangle(x, y, w, 1)
    display.rectangle(x, y + h - 1, w, 1)
    display.rectangle(x, y, 1, h)
    display.rectangle(x + w - 1, y, 1, h)
    display.set_pen(pen(*shade((255, 200, 60), 0.4)))
    display.rectangle(x + 2, y + 2, w - 4, 1)


# --- HUD ---------------------------------------------------------------------
def hud(g):
    p = g
    x = 4
    for i in range(p.max_hp):
        full = i < p.hp
        sprites.draw_heart(x + 5, 5, RED if full else pen(60, 30, 40), 3)
        if full:
            display.set_pen(pen(255, 170, 180))
            display.pixel(x + 2, 4)
        x += 12
    x += 4
    text("LV%d" % p.level, x, 4, 1, GOLD, False)
    x += 26
    display.set_pen(pen(40, 40, 50))
    display.rectangle(x, 6, 34, 4)
    need = p.xp_next()
    if need:
        display.set_pen(JADE)
        display.rectangle(x, 6, int(34 * min(1, p.xp_into() / need)), 4)
    sprites.draw_cacao(258, 8, g.t)
    text("%d" % p.cacao, 265, 4, 1, CREAM, False)
    for i in range(4):
        gx = 296 + (i & 1) * 9
        gy = 3 + (i >> 1) * 6
        display.set_pen(JADE if p.glyphs() > i else pen(40, 50, 45))
        display.rectangle(gx, gy, 6, 4)


def hud_key(g):
    return (g.hp, g.max_hp, g.level, g.xp, g.cacao, g.glyphs())


def hud_clear():
    display.set_pen(SHADOW)
    display.rectangle(0, 0, 320, HUD - 1)


_wrap_cache = {}


def banner(s, t, total=80, sub=None):
    if t > total:
        return
    k = min(1.0, t / 8, (total - t) / 8)
    y = 26 + int((1 - k) * -20)
    lines = []
    if sub:
        lines = _wrap_cache.get(sub)
        if lines is None:
            lines = wrap(sub, 290, 1)[:2]
            _wrap_cache[sub] = lines
    w = display.measure_text(s, 2)
    for ln in lines:
        w = max(w, display.measure_text(ln, 1))
    h = 22 + len(lines) * 11
    display.set_pen(SHADOW)
    display.rectangle((320 - w) // 2 - 10, y - 4, w + 20, h)
    display.set_pen(GOLD)
    display.rectangle((320 - w) // 2 - 10, y + h - 5, w + 20, 1)
    center(s, y, 2, GOLD)
    for i, ln in enumerate(lines):
        center(ln, y + 18 + i * 11, 1, CREAM)


def boss_bar(b):
    if not b or b.dying:
        return
    display.set_pen(SHADOW)
    display.rectangle(40, 228, 240, 10)
    display.set_pen(pen(80, 20, 30))
    display.rectangle(42, 230, 236, 6)
    display.set_pen(RED if not b.flash else WHITE)
    display.rectangle(42, 230, int(236 * b.hp / b.max_hp), 6)
    text(b.name, 44, 219, 1, CREAM)


def prompt(x, y, t):
    if (t >> 3) & 1:
        display.set_pen(GOLD)
        display.triangle(x - 3, y, x + 3, y, x, y - 4)


# --- dialogue ------------------------------------------------------------------
class Dialogue:
    def __init__(self, lines, skin, on_action):
        self.pages = []
        for who, s in lines:
            if who == "!":
                self.pages.append(("!", s))
                continue
            ls = wrap(s, 262, 2)
            for i in range(0, len(ls), 3):
                self.pages.append((who, ls[i:i + 3]))
        self.i = -1
        self.skin = skin
        self.on_action = on_action
        self.shown = 0.0
        self.total = 0
        self.done = False
        self.waiting = False
        self.t = 0
        self._next()

    def _next(self):
        self.i += 1
        while self.i < len(self.pages) and self.pages[self.i][0] == "!":
            if self.on_action(self.pages[self.i][1]):
                self.waiting = True
                return
            self.i += 1
        if self.i >= len(self.pages):
            self.done = True
            return
        self.shown = 0.0
        self.total = sum(len(s) for s in self.pages[self.i][1])

    def resume(self):
        self.waiting = False
        self._next()

    def update(self, confirm, audio):
        if self.done or self.waiting:
            return
        self.t += 1
        if self.shown < self.total:
            before = int(self.shown)
            self.shown += 1.6
            if int(self.shown) // 2 != before // 2:
                who = self.pages[self.i][0]
                base = {"ceiba": 700, "ek": 1100, "chaac": 520, "balam": 400, "witz": 260, "fluff": 1500}.get(who, 900)
                audio.sfx_tone(base + (int(self.shown) % 3) * 60, base, 1, 450)
            if confirm:
                self.shown = self.total
        elif confirm:
            audio.sfx_play("menu")
            self._next()

    def draw(self, t):
        if self.done or self.waiting or self.i >= len(self.pages):
            return
        who, lines = self.pages[self.i]
        panel(2, BOX_Y, 316, 74)
        sprites.draw_portrait(who, 6, BOX_Y + 6, t, self.skin)
        left = int(self.shown)
        y = BOX_Y + 6
        for s in lines:
            if left <= 0:
                break
            text(s[:left], 48, y, 2, CREAM)
            left -= len(s)
            y += 20
        if self.shown >= self.total and (t >> 3) & 1:
            display.set_pen(GOLD)
            display.triangle(306, BOX_Y + 64, 314, BOX_Y + 64, 310, BOX_Y + 69)


# --- item get ----------------------------------------------------------------
def item_get(item, t):
    name, desc = story.ITEMS[item]
    icon = story.ITEM_ICON[item]
    cx, cy = 160, 92
    display.set_pen(pen(30, 24, 10))
    display.circle(cx, cy, 56)
    for k in range(12):
        a = t * 0.03 + k * 0.5236
        display.set_pen(pen(255, 210, 90) if k & 1 else pen(255, 170, 50))
        display.triangle(cx, cy, cx + int(70 * math.cos(a)), cy + int(70 * math.sin(a)),
                         cx + int(70 * math.cos(a + 0.18)), cy + int(70 * math.sin(a + 0.18)))
    display.set_pen(pen(255, 245, 210))
    display.circle(cx, cy, 22)
    sprites.draw_item(icon, cx, cy, t, True)
    panel(10, 160, 300, 70)
    center(name, 168, 2, GOLD)
    y = 190
    for s in wrap(desc, 284, 1)[:3]:
        center(s, y, 1, CREAM)
        y += 11
    if t > 30 and (t >> 3) & 1:
        center("press B", 220, 1, GREY, False)


# --- map -----------------------------------------------------------------------
def map_screen(g, t):
    display.set_pen(DARK)
    display.clear()
    center("MAP OF THE JADE SUN", 6, 2, GOLD)
    ox, oy, cw, ch = 20, 30, 40, 26
    for rid, r in ROOMS.items():
        x, y = r["pos"]
        sx, sy = ox + x * cw, oy + y * ch
        if rid not in g.visited:
            display.set_pen(pen(24, 22, 30))
            display.rectangle(sx + 1, sy + 1, cw - 2, ch - 2)
            continue
        z = ZONES[r["zone"]]
        display.set_pen(pen(*shade(z[2], 1.1)))
        display.rectangle(sx + 1, sy + 1, cw - 2, ch - 2)
        display.set_pen(pen(*shade(z[5], 0.9)))
        display.rectangle(sx + 1, sy + 1, cw - 2, 3)
        if "P" in "".join(r["map"]):
            display.set_pen(JADE)
            display.circle(sx + 8, sy + 15, 3)
        b = r.get("boss")
        if b:
            display.set_pen(GREY if g.flags.get("boss_" + b) else RED)
            display.circle(sx + cw - 9, sy + 15, 4)
        left = [i for i in r.get("items", ()) + r.get("lore", ()) if not g.has(i)]
        if left:
            text("?", sx + cw // 2 - 3, sy + 9, 1, GOLD, False)
        if rid == g.room.id and (t >> 3) & 1:
            display.set_pen(WHITE)
            display.rectangle(sx, sy, cw, 2)
            display.rectangle(sx, sy + ch - 2, cw, 2)
            display.rectangle(sx, sy, 2, ch)
            display.rectangle(sx + cw - 2, sy, 2, ch)
    secs = g.play_time // 25
    stats = "LV %d   CACAO %d   GLYPHS %d/4   %d%%   %d:%02d" % (
        g.level, g.cacao, g.glyphs(), g.completion(), secs // 60, secs % 60)
    center(stats, 168, 1, CREAM)
    panel(6, 182, 308, 40, JADE_D)
    y = 188
    for s in wrap(story.hint(g), 296, 1)[:3]:
        center(s, y, 1, JADE)
        y += 11
    center("+ close    - title    display X volume", 228, 1, GREY, False)


# --- shop --------------------------------------------------------------------------
def shop(g, cursor, t):
    panel(30, 40, 260, 130)
    center("EK CHUAH'S CACAO STALL", 48, 1, GOLD)
    y = 66
    for i, (key, name, desc, cost) in enumerate(story.SHOP):
        sold = key != "refill" and g.has(key)
        col = GREY if sold else (GOLD if i == cursor else CREAM)
        if i == cursor and (t >> 3) & 1:
            display.set_pen(GOLD)
            display.triangle(40, y + 2, 40, y + 10, 46, y + 6)
        text(name, 52, y, 1, col)
        text("SOLD" if sold else "%d" % cost, 240, y, 1, col)
        text(desc, 52, y + 11, 1, GREY, False)
        y += 26
    text("Leave", 52, y, 1, GOLD if cursor == len(story.SHOP) else CREAM)
    if cursor == len(story.SHOP) and (t >> 3) & 1:
        display.set_pen(GOLD)
        display.triangle(40, y + 1, 40, y + 9, 46, y + 5)
    text("cacao: %d" % g.cacao, 210, 154, 1, CREAM)


# --- title -----------------------------------------------------------------------
def title(t, has_save, cursor):
    cx, cy = 160, 74
    for i in range(4):
        a = t * 0.02 + i * 1.5708
        sprites.draw_item("glyph", cx + int(22 * math.cos(a)), cy + int(22 * math.sin(a)), t)
    center(story.TITLE, 112, 4, GOLD)
    center(story.SUBTITLE, 146, 2, JADE)
    if has_save:
        for i, s in enumerate(("CONTINUE", "NEW QUEST")):
            sel = i == cursor
            col = GOLD if sel else GREY
            center(("> %s <" % s) if sel and (t >> 3) & 1 else s, 176 + i * 18, 2, col)
    elif (t >> 4) & 1:
        center("PRESS B TO BEGIN", 182, 2, CREAM)
    center("a legend for Maya", 228, 1, pen(120, 160, 140), False)


def form(skin, msg, t, done):
    display.set_pen(DARK)
    display.clear()
    center("THE CEIBA SPIRIT SHAPES YOU", 16, 1, JADE)
    for k in range(16):
        a = t * 0.05 + k * 0.3927
        display.set_pen(pen(30, 60, 40) if k & 1 else pen(20, 40, 30))
        display.triangle(160, 106, 160 + int(150 * math.cos(a)), 106 + int(150 * math.sin(a)),
                         160 + int(150 * math.cos(a + 0.2)), 106 + int(150 * math.sin(a + 0.2)))
    sprites.draw_fluff(skin, 145, 86, 1, t, True, 0, scale=3, blink=(t % 50) < 3)
    center(msg, 168, 2, GOLD if done else CREAM)
    if done:
        center(sprites.FLUFF_NAMES[skin.idx], 192, 1, JADE)


def ending_scene(page, shown, t, g):
    display.set_pen(pen(4, 20, 14))
    display.clear()
    cx, cy = 160, 70
    for k in range(16):
        a = t * 0.02 + k * 0.3927
        display.set_pen(pen(40, 160, 90) if k & 1 else pen(20, 100, 60))
        display.triangle(cx, cy, cx + int(200 * math.cos(a)), cy + int(200 * math.sin(a)),
                         cx + int(200 * math.cos(a + 0.2)), cy + int(200 * math.sin(a + 0.2)))
    display.set_pen(JADE)
    display.circle(cx, cy, 30)
    display.set_pen(pen(180, 255, 210))
    display.circle(cx, cy, 20)
    sprites.draw_fluff(g.skin, 150, 120, 1, t, True, 0, scale=2)
    if page < len(story.ENDING):
        lines = wrap(story.ENDING[page], 290, 1)
        y = 168
        left = int(shown)
        panel(10, 160, 300, 60)
        for ln in lines:
            if left <= 0:
                break
            center(ln[:left] if left < len(ln) else ln, y, 1, CREAM)
            left -= len(ln)
            y += 12
    else:
        panel(10, 150, 300, 86)
        center("THE END", 156, 3, GOLD)
        secs = g.play_time // 25
        center("Time %d:%02d   Level %d   %d%% found" % (secs // 60, secs % 60, g.level, g.completion()), 186, 1, CREAM)
        center("Thank you for playing, Maya!", 202, 1, JADE)
        if (t >> 4) & 1:
            center("press B", 222, 1, GREY, False)


def death(t):
    k = min(1.0, t / 30)
    display.set_pen(pen(int(60 * k), 0, int(20 * k)))
    display.rectangle(0, 90, 320, 60)
    center("The spirits carry you home...", 112, 2, CREAM)
