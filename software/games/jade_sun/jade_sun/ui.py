"""HUD, dialogue, menus and full-screen scenes."""
import math
from .hw import display
from .gfx import pen, shade, HUD, WHITE, BLACK, GOLD, JADE, JADE_D, RED, CREAM, SHADOW, DARK, GREY, ZONES
from . import sprites, rig, story
from .world_data import ROOMS, AT

BOX_Y = 164

_PLATE = pen(10, 8, 16)
_LIT = pen(255, 228, 168)
_CORNER_DARK = pen(28, 18, 12)
_GEM_LIT = pen(214, 255, 232)
_GEM_DARK = pen(8, 64, 44)
_RAY_A = pen(255, 186, 64)
_RAY_B = pen(48, 176, 118)
_WHITE_LO = pen(176, 176, 186)
_BLOOD = pen(168, 40, 52)
_BLOOD_DARK = pen(90, 16, 28)
_METER = pen(36, 10, 16)
_TRACK = pen(28, 26, 36)
_HUD_DIM = pen(36, 44, 40)
_HUD_DIM_D = pen(18, 22, 20)

_FILL = {}
_WALL = {}
_GHOST = {}
_DARK = {}
for _z, _cols in ZONES.items():
    _cap = _cols[5]
    _rgb = shade(_cap, 0.82)
    _FILL[_z] = pen(*_rgb)
    _DARK[_z] = pen(*shade(_cap, 0.42))
    if _rgb[0] + _rgb[1] + _rgb[2] > 400:
        _WALL[_z] = pen(22, 24, 36)
        _GHOST[_z] = pen(*shade(_cap, 0.5))
    else:
        _WALL[_z] = pen(255, 236, 214)
        _GHOST[_z] = pen(*shade(_cap, 0.4))

# Shard tips for the item burst, rotated with the 64-step table.
_RAYS = []
for _i in range(8):
    _a = _i * math.pi / 4
    _ca, _sa = math.cos(_a), math.sin(_a)
    _px, _py = -_sa * 7, _ca * 7
    _RAYS.append((
        int(_ca * 22), int(_sa * 22),
        int(_ca * 62 + _px), int(_sa * 62 + _py),
        int(_ca * 62 - _px), int(_sa * 62 - _py),
    ))
_RAYS = tuple(_RAYS)

_ROOMS = ()
_DOORS = ()
_CW, _CH = 22, 15
_STAT_Y = 166
_HINT_Y = 178
_CTRL_Y = 228


def _oct(x, y, w, h, c):
    if c < 2:
        c = 2
    if c * 2 >= w:
        c = max(2, w // 3)
    if c * 2 >= h:
        c = max(2, h // 3)
    x1 = x + w - 1
    y1 = y + h - 1
    return [
        (x + c, y), (x1 - c, y),
        (x1, y + c), (x1, y1 - c),
        (x1 - c, y1), (x + c, y1),
        (x, y1 - c), (x, y + c),
    ]


def _gem(x, y, r, lit, mid, dark):
    """Layered gem: mid diamond, dark lower facet, lit cap."""
    display.set_pen(mid)
    display.triangle(x, y - r, x + r, y, x, y + r)
    display.triangle(x, y - r, x - r, y, x, y + r)
    display.set_pen(dark)
    display.triangle(x - r, y, x + r, y, x, y + r)
    display.set_pen(lit)
    display.triangle(x - r // 2, y - r // 3, x + r // 2, y - r // 3, x, y - r)


def _mark(x, y, r, col, dark):
    display.set_pen(col)
    display.triangle(x, y - r, x - r, y, x + r, y)
    display.set_pen(dark)
    display.triangle(x - r, y, x + r, y, x, y + r)


def _lip(x, y, w, c):
    """Lit top edge, three triangles, light from above."""
    x0 = x + c + 2
    x1 = x + w - c - 3
    if x1 - x0 < 8:
        return
    yt = y + 3
    yb = y + 7
    display.set_pen(_LIT)
    step = (x1 - x0) // 3
    i = 0
    while i < 3:
        xa = x0 + i * step
        xb = x1 if i == 2 else x0 + (i + 1) * step
        display.triangle(xa, yb, (xa + xb) // 2, yt, xb, yb)
        i += 1


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
    """Dark plate, mid frame, triangular corner facets, lit top edge, one gem."""
    c = 8 if w >= 48 and h >= 28 else 4
    display.set_pen(border)
    display.polygon(_oct(x, y, w, h, c))
    x1 = x + w - 1
    y1 = y + h - 1
    display.set_pen(_LIT)
    display.triangle(x, y, x + c, y, x, y + c)
    display.triangle(x1, y, x1 - c, y, x1, y + c)
    display.set_pen(_CORNER_DARK)
    display.triangle(x, y1, x + c, y1, x, y1 - c)
    display.triangle(x1, y1, x1 - c, y1, x1, y1 - c)
    ins = 3
    display.set_pen(_PLATE)
    display.polygon(_oct(x + ins, y + ins, w - ins * 2, h - ins * 2, max(2, c - 2)))
    _lip(x, y, w, c)
    _gem(x1 - c // 2, y + c // 2, 4 if c >= 8 else 3, _GEM_LIT, JADE, _GEM_DARK)


# --- HUD ---------------------------------------------------------------------
def hud(g):
    p = g
    x = 6
    for i in range(p.max_hp):
        full = i < p.hp
        sprites.draw_heart(x + 5, 6, RED if full else pen(60, 30, 40), 3)
        if full:
            display.set_pen(pen(255, 170, 180))
            display.pixel(x + 3, 4)
        x += 12
    x += 4
    text("LV%d" % p.level, x, 4, 1, GOLD, False)
    x += 26
    display.set_pen(_TRACK)
    display.rectangle(x, 6, 34, 5)
    need = p.xp_next()
    if need:
        fw = int(34 * min(1, p.xp_into() / need))
        display.set_pen(JADE)
        display.rectangle(x, 7, fw, 3)
        display.set_pen(_GEM_LIT)
        display.rectangle(x, 6, fw, 1)
    sprites.draw_cacao(252, 8, g.t)
    text("%d" % p.cacao, 258, 4, 1, CREAM, False)
    got = p.glyphs()
    for i in range(4):
        gx = 298 + (i & 1) * 9
        gy = 5 + (i >> 1) * 7
        if got > i:
            _mark(gx, gy, 2, JADE, JADE_D)
        else:
            _mark(gx, gy, 2, _HUD_DIM, _HUD_DIM_D)


def hud_key(g):
    return (g.hp, g.max_hp, g.level, g.xp, g.cacao, g.glyphs())


def hud_clear():
    display.set_pen(SHADOW)
    display.rectangle(0, 0, 320, HUD)
    display.set_pen(_LIT)
    display.triangle(0, 0, 10, 0, 0, 4)
    display.triangle(319, 0, 314, 0, 319, 3)
    display.set_pen(JADE_D)
    display.line(0, HUD - 1, 319, HUD - 1)


_wrap_cache = {}


def banner(s, t, total=80, sub=None):
    if t > total:
        return
    k = min(1.0, t / 8, (total - t) / 8)
    y = 28 + int((1 - k) * -18)
    lines = []
    if sub:
        lines = _wrap_cache.get(sub)
        if lines is None:
            lines = wrap(sub, 280, 1)[:2]
            _wrap_cache[sub] = lines
    w = display.measure_text(s, 2)
    for ln in lines:
        w = max(w, display.measure_text(ln, 1))
    bw = w + 52
    if bw > 308:
        bw = 308
    h = 32 + len(lines) * 11
    x = (320 - bw) // 2
    panel(x, y, bw, h)
    center(s, y + 12, 2, GOLD)
    for i, ln in enumerate(lines):
        center(ln, y + 30 + i * 11, 1, CREAM)


def boss_bar(b):
    if not b or b.dying:
        return
    text(b.name, 48, 214, 1, CREAM, False)
    x, y, w, h = 40, 224, 240, 14
    display.set_pen(_BLOOD)
    display.polygon(_oct(x, y, w, h, 5))
    display.set_pen(_METER)
    display.polygon(_oct(x + 2, y + 2, w - 4, h - 4, 3))
    frac = 0
    if b.max_hp:
        frac = int((w - 16) * b.hp / b.max_hp)
    display.set_pen(WHITE if b.flash else RED)
    display.rectangle(x + 6, y + 4, frac, 6)
    display.set_pen(_LIT)
    display.triangle(x + 8, y + 4, x + w // 2, y + 2, x + w - 10, y + 4)
    _gem(x + w - 14, y + 7, 3, _LIT, RED, _BLOOD_DARK)


def prompt(x, y, t):
    if (t >> 3) & 1:
        _gem(x, y - 1, 3, _LIT, GOLD, pen(140, 90, 24))


# --- dialogue ------------------------------------------------------------------
class Dialogue:
    def __init__(self, lines, skin, on_action):
        self.pages = []
        for who, s in lines:
            if who == "!":
                self.pages.append(("!", s))
                continue
            ls = wrap(s, 250, 2)
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
        sprites.draw_portrait(who, 10, BOX_Y + 14, t, self.skin)
        left = int(self.shown)
        y = BOX_Y + 14
        for s in lines:
            if left <= 0:
                break
            text(s[:left], 52, y, 2, CREAM)
            left -= len(s)
            y += 18
        if self.shown >= self.total and (t >> 3) & 1:
            _mark(300, BOX_Y + 62, 3, GOLD, pen(140, 90, 24))


# --- item get ----------------------------------------------------------------
def item_get(item, t):
    name, desc = story.ITEMS[item]
    icon = story.ITEM_ICON[item]
    cx, cy = 160, 78
    panel(cx - 72, cy - 64, 144, 128)
    ca = rig.cos64(t)
    sa = rig.sin64(t)
    i = 0
    for x0, y0, x1, y1, x2, y2 in _RAYS:
        display.set_pen(_RAY_A if i & 1 else _RAY_B)
        display.triangle(
            cx + int(x0 * ca - y0 * sa), cy + int(x0 * sa + y0 * ca),
            cx + int(x1 * ca - y1 * sa), cy + int(x1 * sa + y1 * ca),
            cx + int(x2 * ca - y2 * sa), cy + int(x2 * sa + y2 * ca),
        )
        i += 1
    rig.gem(cx, cy, 16, _GEM_LIT, JADE, _GEM_DARK, 8)
    sprites.draw_item(icon, cx, cy, t, True)
    panel(12, 150, 296, 82)
    center(name, 164, 2, GOLD)
    y = 186
    for s in wrap(desc, 268, 1)[:3]:
        center(s, y, 1, CREAM)
        y += 11
    if t > 30 and (t >> 3) & 1:
        center("press B", 216, 1, CREAM, False)


# --- map -----------------------------------------------------------------------
def _rows_open(ma, mb, ca, cb):
    """True when any shared row has both tiles passable. Rock is '#'."""
    n = min(len(ma), len(mb))
    i = 0
    while i < n:
        la = ma[i]
        lb = mb[i]
        if ca < len(la) and cb < len(lb) and la[ca] != "#" and lb[cb] != "#":
            return True
        i += 1
    return False


def _cols_open(ma, mb, ra, rb):
    if ra >= len(ma) or rb >= len(mb):
        return False
    a = ma[ra]
    b = mb[rb]
    n = min(len(a), len(b))
    i = 0
    while i < n:
        if a[i] != "#" and b[i] != "#":
            return True
        i += 1
    return False


def _edge_open(r, nb, side):
    ma = r.get("map") or ()
    mb = nb.get("map") or ()
    if side == "E":
        return _rows_open(ma, mb, 19, 0)
    if side == "W":
        return _rows_open(ma, mb, 0, 19)
    if side == "S":
        return _cols_open(ma, mb, 13, 0)
    return _cols_open(ma, mb, 0, 13)


def _build_map():
    """Edge openness once, from ROOMS. Open = any shared tile pair that is not rock."""
    global _ROOMS, _DOORS, _CW, _CH
    found = []
    for rid, r in ROOMS.items():
        pos = r.get("pos")
        if not pos or len(pos) < 2:
            continue
        found.append((rid, r, pos[0], pos[1]))
    if not found:
        _ROOMS = ()
        _DOORS = ()
        return
    minx = min(p[2] for p in found)
    maxx = max(p[2] for p in found)
    miny = min(p[3] for p in found)
    maxy = max(p[3] for p in found)
    cols = maxx - minx + 1
    rows = maxy - miny + 1
    cw = max(8, 286 // max(1, cols))
    ch = max(8, 136 // max(1, rows))
    ox = (320 - cw * cols) // 2
    oy = 26
    _CW, _CH = cw, ch
    rooms = []
    doors = []
    seen = {}
    for rid, r, x, y in found:
        sx = ox + (x - minx) * cw
        sy = oy + (y - miny) * ch
        z = r.get("zone") or "jungle"
        fill = _FILL.get(z, _FILL["jungle"])
        wall = _WALL.get(z, _WALL["jungle"])
        ghost = _GHOST.get(z, _GHOST["jungle"])
        shrine = False
        for line in r.get("map") or ():
            if "P" in line:
                shrine = True
                break
        boss = r.get("boss") or ""
        loot = tuple(r.get("items", ())) + tuple(r.get("lore", ()))
        edges = []
        for side, dx, dy in (("N", 0, -1), ("E", 1, 0), ("S", 0, 1), ("W", -1, 0)):
            nid = AT.get((x + dx, y + dy)) or ""
            nb = ROOMS.get(nid) if nid else None
            open_ = _edge_open(r, nb, side) if nb else False
            if side == "N":
                seg = (sx, sy, sx + cw - 1, sy, nid, open_)
            elif side == "S":
                seg = (sx, sy + ch - 1, sx + cw - 1, sy + ch - 1, nid, open_)
            elif side == "W":
                seg = (sx, sy, sx, sy + ch - 1, nid, open_)
            else:
                seg = (sx + cw - 1, sy, sx + cw - 1, sy + ch - 1, nid, open_)
            edges.append(seg)
            if not (open_ and nb and side in "ES" and nb.get("zone") != z):
                continue
            key = (rid, nid) if rid < nid else (nid, rid)
            if key in seen:
                continue
            seen[key] = True
            nz = nb.get("zone") or "jungle"
            if side == "E":
                dxm, dym = sx + cw - 1, sy + ch // 2
            else:
                dxm, dym = sx + cw // 2, sy + ch - 1
            doors.append((
                dxm, dym, rid, nid,
                fill, _FILL.get(nz, fill),
                _DARK.get(z, fill), _DARK.get(nz, fill),
            ))
        rooms.append((
            rid, sx, sy, fill, wall, ghost, shrine, boss,
            ("boss_" + boss) if boss else "", loot, tuple(edges),
        ))
    _ROOMS = tuple(rooms)
    _DOORS = tuple(doors)


_build_map()


def _ghost(rec, visited):
    edges = rec[10]
    hit = False
    for seg in edges:
        if seg[4] and seg[4] in visited:
            hit = True
            break
    if not hit:
        return
    display.set_pen(rec[5])
    for x1, y1, x2, y2, nid, open_ in edges:
        if open_ and nid in visited:
            continue
        display.line(x1, y1, x2, y2)


def _room_fill(rec, g, cur, blink):
    rid, sx, sy, fill, wall, ghost, shrine, boss, boss_key, loot, edges = rec
    display.set_pen(fill)
    display.rectangle(sx, sy, _CW, _CH)
    display.set_pen(wall)
    for x1, y1, x2, y2, nid, open_ in edges:
        if open_:
            continue
        display.line(x1, y1, x2, y2)
    cy = sy + _CH // 2
    if shrine:
        _mark(sx + 4, cy, 2, JADE, JADE_D)
    left = False
    for k in loot:
        if not g.has(k):
            left = True
            break
    if left:
        _mark(sx + _CW // 2, cy, 2, GOLD, pen(140, 90, 24))
    if boss:
        col = GREY if g.flags.get(boss_key) else RED
        dark = pen(70, 70, 78) if g.flags.get(boss_key) else _BLOOD_DARK
        _mark(sx + _CW - 5, cy, 2, col, dark)
    if rid == cur and blink:
        display.set_pen(WHITE)
        display.line(sx, sy, sx + _CW - 1, sy)
        display.line(sx, sy + _CH - 1, sx + _CW - 1, sy + _CH - 1)
        display.line(sx, sy, sx, sy + _CH - 1)
        display.line(sx + _CW - 1, sy, sx + _CW - 1, sy + _CH - 1)


def _draw_doors(visited):
    for x, y, a, b, pa, pb, da, db in _DOORS:
        va = a in visited
        vb = b in visited
        if not va and not vb:
            continue
        if va and vb:
            _mark(x, y, 2, WHITE, _WHITE_LO)
        elif va:
            _mark(x, y, 2, pb, db)
        else:
            _mark(x, y, 2, pa, da)


def map_screen(g, t):
    display.set_pen(DARK)
    display.clear()
    panel(36, 0, 248, 24)
    center("MAP OF THE JADE SUN", 8, 1, GOLD)
    visited = g.visited
    cur = g.room.id if g.room else ""
    blink = (t >> 3) & 1
    for rec in _ROOMS:
        if rec[0] in visited:
            continue
        _ghost(rec, visited)
    for rec in _ROOMS:
        if rec[0] not in visited:
            continue
        _room_fill(rec, g, cur, blink)
    _draw_doors(visited)
    secs = g.play_time // 25
    stats = "LV %d   CACAO %d   GLYPHS %d/4   %d%%   %d:%02d" % (
        g.level, g.cacao, g.glyphs(), g.completion(), secs // 60, secs % 60)
    center(stats, _STAT_Y, 1, CREAM)
    panel(8, _HINT_Y, 304, 44, JADE_D)
    y = _HINT_Y + 12
    for s in wrap(story.hint(g), 276, 1)[:3]:
        center(s, y, 1, JADE)
        y += 10
    center("+ close    - title    display X volume", _CTRL_Y, 1, pen(186, 190, 198), False)


def _petals(cx, cy, t, inner, outer, n, lit, mid):
    base = int(t) // 2
    step = 64 // n
    k = 0
    while k < n:
        a = base + k * step
        ca = rig.cos64(a)
        sa = rig.sin64(a)
        px, py = -sa, ca
        display.set_pen(lit if sa < 0 else mid)
        display.triangle(
            cx + int(ca * inner), cy + int(sa * inner),
            cx + int(ca * outer + px * 6), cy + int(sa * outer + py * 6),
            cx + int(ca * outer - px * 6), cy + int(sa * outer - py * 6),
        )
        k += 1


# --- shop --------------------------------------------------------------------------
def shop(g, cursor, t):
    panel(18, 28, 284, 176)
    center("EK CHUAH'S CACAO STALL", 44, 1, GOLD)
    y = 62
    for i, (key, name, desc, cost) in enumerate(story.SHOP):
        sold = key != "refill" and g.has(key)
        col = GREY if sold else (GOLD if i == cursor else CREAM)
        if i == cursor and (t >> 3) & 1:
            _mark(32, y + 4, 3, GOLD, pen(140, 90, 24))
        text(name, 44, y, 1, col)
        text("SOLD" if sold else "%d" % cost, 250, y, 1, col)
        text(desc, 44, y + 11, 1, pen(168, 172, 180), False)
        y += 26
    text("Leave", 44, y, 1, GOLD if cursor == len(story.SHOP) else CREAM)
    if cursor == len(story.SHOP) and (t >> 3) & 1:
        _mark(32, y + 4, 3, GOLD, pen(140, 90, 24))
    text("cacao: %d" % g.cacao, 188, 168, 1, GOLD)


# --- title -----------------------------------------------------------------------
def title(t, has_save, cursor):
    cx, cy = 160, 74
    base = int(t) // 4
    for i in range(4):
        a = base + i * 16
        sprites.draw_item("glyph", cx + int(30 * rig.cos64(a)), cy + int(30 * rig.sin64(a)), t)
    panel(22, 142, 276, 94)
    center(story.TITLE, 154, 3, GOLD)
    center(story.SUBTITLE, 180, 2, JADE)
    if has_save:
        for i, s in enumerate(("CONTINUE", "NEW QUEST")):
            sel = i == cursor
            col = GOLD if sel else GREY
            yy = 200 + i * 16
            center(s, yy, 2, col)
            if sel and (t >> 3) & 1:
                tw = display.measure_text(s, 2)
                _mark((320 - tw) // 2 - 10, yy + 6, 3, GOLD, pen(140, 90, 24))
    else:
        if (t >> 4) & 1:
            center("PRESS B TO BEGIN", 204, 2, CREAM)
        center("a legend for Maya", 224, 1, pen(210, 230, 214), False)


def form(skin, msg, t, done):
    display.set_pen(DARK)
    display.clear()
    center("THE CEIBA SPIRIT SHAPES YOU", 12, 1, JADE)
    _petals(160, 92, t, 34, 58, 8, pen(48, 120, 78), pen(16, 48, 36))
    sprites.draw_fluff(skin, 145, 68, 1, t, True, 0, scale=3, blink=(t % 50) < 3)
    lines = wrap(msg, 268, 2)[:2]
    n = len(lines)
    h = 26 + n * 18 + (14 if done else 0)
    top = 208 - h
    panel(12, top, 296, h, JADE_D)
    y = top + 10
    col = GOLD if done else CREAM
    for ln in lines:
        center(ln, y, 2, col)
        y += 18
    if done:
        center(sprites.FLUFF_NAMES[skin.idx], y, 1, JADE)


def ending_scene(page, shown, t, g):
    display.set_pen(pen(4, 16, 12))
    display.clear()
    _petals(160, 62, t, 20, 44, 8, pen(80, 210, 140), pen(20, 90, 60))
    rig.gem(160, 62, 16, _GEM_LIT, JADE, _GEM_DARK, 8)
    sprites.draw_fluff(g.skin, 148, 112, 1, t, True, 0, scale=2)
    if page < len(story.ENDING):
        lines = wrap(story.ENDING[page], 270, 1)
        n = len(lines)
        h = 22 + n * 12
        top = 232 - h
        panel(12, top, 296, h)
        y = top + 12
        left = int(shown)
        for ln in lines:
            if left <= 0:
                break
            center(ln[:left] if left < len(ln) else ln, y, 1, CREAM)
            left -= len(ln)
            y += 12
    else:
        panel(12, 150, 296, 82)
        center("THE END", 164, 2, GOLD)
        secs = g.play_time // 25
        center("Time %d:%02d   Level %d   %d%% found" % (secs // 60, secs % 60, g.level, g.completion()), 186, 1, CREAM)
        center("Thank you for playing, Maya!", 202, 1, JADE)
        if (t >> 4) & 1:
            center("press B", 216, 1, CREAM, False)


def death(t):
    if t < 8:
        return
    panel(16, 96, 288, 48, _BLOOD)
    center("The spirits carry you home...", 112, 2, CREAM)
