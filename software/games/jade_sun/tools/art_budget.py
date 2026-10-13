"""Draw-call budget and contact sheets for every Jade Sun asset.

Counts PicoGraphics primitives per sprite sample (max over animation frames and states),
bakes every room, and writes contact sheets so art can be reviewed as PNGs.

  .venv/bin/python games/jade_sun/tools/art_budget.py                 (from software/)
  .venv/bin/python games/jade_sun/tools/art_budget.py --baseline      record tools/out/art_baseline.json
  .venv/bin/python games/jade_sun/tools/art_budget.py --only fluff,enemies --zoom 4

Sheets: tools/out/art/<group>.png. Exit code 1 when a group is over budget.
"""
import argparse
import json
import sys
import time
import types
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
from fuzz import _boot_path, _patch_runtime  # noqa: E402

_boot_path()
_patch_runtime()

from PIL import Image  # noqa: E402
from jade_sun.hw import display  # noqa: E402
from jade_sun import gfx  # noqa: E402
# Each group imports only the modules it draws, so a half-edited file elsewhere cannot break it.

OUT = TOOLS_DIR / "out"
BASELINE = OUT / "art_baseline.json"
PRIMS = ("rectangle", "circle", "triangle", "polygon", "line", "pixel", "text", "pixel_span")
# Max draw calls per sample. The frame budget on device is ~3 ms of headroom, so moving
# sprites stay tight; baked room art is paid once per room entry (~0.12 ms per call).
CAPS = {
    "fluff": {"*": 42, "charge": 52, "trail": 40, "scale2": 42},
    "enemies": {"*": 28},
    "bosses": {"*": 72},
    "npcs": {"*": 40, "witz": 48},
    "portraits": {"*": 52},
    "items": {"*": 26, "glyph": 30, "heart_pickup": 8, "cacao": 10},
    "projectiles": {"*": 8, "wave": 5, "bubble": 6, "orb": 6, "bat": 10},
}
BAKE_MAX = 2000
BAKE_MS_MAX = 1200

_count = [0]
_depth = [0]


def _wrap():
    for name in PRIMS:
        fn = getattr(display, name, None)
        if fn is None:
            continue

        def make(f):
            def counted(*a, **k):
                # The mock draws triangle() via polygon(); count only the outermost call.
                if _depth[0] == 0:
                    _count[0] += 1
                _depth[0] += 1
                try:
                    return f(*a, **k)
                finally:
                    _depth[0] -= 1
            return counted
        setattr(display, name, make(fn))


_wrap()


def ns(**kw):
    return types.SimpleNamespace(**kw)


class Sheet:
    def __init__(self, name, cell=(64, 48), cols=8, zoom=3):
        self.name, self.cell, self.cols, self.zoom = name, cell, cols, zoom
        self.tiles = []

    def grab(self, label, cx, cy):
        w, h = self.cell
        box = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
        self.tiles.append((label, display.image.crop(box)))

    def save(self):
        if not self.tiles:
            return None
        from PIL import ImageDraw
        w, h = self.cell
        z = self.zoom
        rows = (len(self.tiles) + self.cols - 1) // self.cols
        img = Image.new("RGB", (self.cols * w * z, rows * (h * z + 12)), (16, 16, 20))
        d = ImageDraw.Draw(img)
        for i, (label, tile) in enumerate(self.tiles):
            x = (i % self.cols) * w * z
            y = (i // self.cols) * (h * z + 12)
            img.paste(tile.resize((w * z, h * z), Image.NEAREST), (x, y + 12))
            d.text((x + 2, y), label[:24], fill=(230, 230, 150))
        path = OUT / "art" / (self.name + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        return path


BG = (40, 52, 46)
HITBOX = [False]


def _bg():
    display.set_pen(gfx.pen(*BG))
    display.clear()


def _outline(r):
    from PIL import ImageDraw
    x, y, w, h = (int(v) for v in r)
    ImageDraw.Draw(display.image).rectangle((x, y, x + w - 1, y + h - 1), outline=(255, 0, 255))


def measure(sheet, label, fn, frames=(0,), cx=160, cy=120, grab=True, ent=None):
    """Draw fn(t) for each t, return max primitive count. Grabs the first frame."""
    worst = 0
    for i, t in enumerate(frames):
        _bg()
        _count[0] = 0
        fn(t)
        worst = max(worst, _count[0])
        if grab and i == 0 and sheet:
            if HITBOX[0] and ent is not None:
                if isinstance(ent, tuple):
                    _outline(ent)
                else:
                    rx, ry, rw, rh = ent.rect()
                    _outline((rx, ry + gfx.HUD, rw, rh))
            sheet.grab(label, cx, cy)
    return worst


T8 = (0, 3, 6, 9, 12, 15, 18, 21)


def group_fluff(sheet):
    from jade_sun import sprites_fluff as sprites
    skin = sprites.FluffSkin(0)
    out = {}
    samples = (
        ("idle", dict(face=1, ground=True, vy=0.0, wet=False)),
        ("idle_l", dict(face=-1, ground=True, vy=0.0, wet=False)),
        ("jump", dict(face=1, ground=False, vy=-5.0, wet=False)),
        ("fall", dict(face=1, ground=False, vy=4.0, wet=False)),
        ("swim", dict(face=1, ground=False, vy=0.5, wet=True)),
    )
    for name, kw in samples:
        out[name] = measure(sheet, name, lambda t, kw=kw: sprites.draw_fluff(
            skin, 155, 113, kw["face"], t, kw["ground"], kw["vy"], kw["wet"]), T8, ent=(155, 113, 10, 14))
    out["blink"] = measure(sheet, "blink", lambda t: sprites.draw_fluff(skin, 155, 113, 1, t, True, 0.0, False, 1, True))
    out["scale2"] = measure(sheet, "scale2", lambda t: sprites.draw_fluff(skin, 150, 110, 1, t, True, 0.0, False, 2), T8)
    for d, name in ((0, "slash_fwd"), (1, "slash_up"), (2, "slash_down")):
        out[name] = measure(sheet, name, lambda t, d=d: (
            sprites.draw_fluff(skin, 155, 113, 1, 0, d != 2, 0.0, False),
            sprites.draw_slash(155, 113, d, 1, 8 - (t % 5))), T8)
    out["charge"] = measure(sheet, "charge_full", lambda t: (
        sprites.draw_fluff(skin, 155, 113, 1, t, True, 0.0, False), sprites.draw_charge(155, 113, t, True)), T8)
    out["trail"] = measure(sheet, "dash_trail", lambda t: (
        sprites.draw_trail(skin, [(125, 97), (135, 97), (145, 97)]),
        sprites.draw_fluff(skin, 155, 113, 1, t, True, 0.0, False)), (0,))
    return out


def group_enemies(sheet):
    from jade_sun import sprites_enemies as sprites, enemies
    out = {}
    for kind in enemies.STATS:
        e = enemies.Enemy(kind, 150, 100)
        e.x, e.y = 154.0, 104.0
        for st in ((0, 1, 2) if kind == "warrior" else (0,)):
            for face in (1, -1):
                e.face, e.state = face, st
                e.timer = 60 if kind == "mask" else 0
                e.vy = -2.0 if kind == "frog" and face < 0 else 0.0
                label = "%s s%d %s" % (kind, st, "R" if face > 0 else "L")
                n = measure(sheet, label, lambda t, e=e: sprites.draw_enemy(e, t), T8, 161, 128, ent=e)
                out[kind] = max(out.get(kind, 0), n)
        e.flash = 2
        out[kind] = max(out[kind], measure(None, "", lambda t, e=e: sprites.draw_enemy(e, t), (0,), grab=False))
    lk = enemies.Lurker(138, 100)
    for st in (0, 2):
        lk.state = st
        out["lurker"] = max(out.get("lurker", 0), measure(sheet, "lurker s%d" % st,
                                                          lambda t: sprites.draw_lurker(lk, t), T8, 160, 122, ent=lk))
    return out


def group_bosses(sheet):
    from jade_sun import bosses
    out = {}
    states = {
        "xoc": ("idle", "tell", "lunge", "spit"),
        "jaguar": ("prowl", "crouch", "dashtell", "pounce", "dash", "stun"),
        "eagle": ("hover", "tell", "dive", "glide", "storm"),
        "camazotz": ("hover", "tell", "dive", "screech"),
    }
    for kind, cls in bosses.BOSSES.items():
        b = cls(140, 100)
        if kind == "xoc":
            b.x, b.y = 170.0, 100.0
            b.trail = [(170 - i * 1.5, 100 + 6 * ((i // 8) % 2)) for i in range(48)]
        elif kind == "jaguar":
            b.x, b.y = 145.0, 96.0
        else:
            b.x, b.y = 143.0, 96.0
        for st in states[kind]:
            b.state = st
            b.timer = 10
            if kind == "eagle" and st == "storm":
                b.bolts = [[136, 0], [184, 0]]
            elif kind == "eagle":
                b.bolts = []
            n = measure(sheet, "%s %s" % (kind, st), lambda t, b=b: b.draw(t), T8, 160, 118, ent=b)
            out[kind] = max(out.get(kind, 0), n)
        if kind == "camazotz":
            b.hp = 5
            b.state = "hover"
            out[kind] = max(out[kind], measure(sheet, "camazotz phase3", lambda t, b=b: b.draw(t), T8, 160, 118, ent=b))
    w = bosses.Watcher(150, 120)
    for st in ("patrol", "alert", "chase", "stagger"):
        w.state = st
        w.hp = 3 if st != "stagger" else 1
        out["watcher"] = max(out.get("watcher", 0), measure(sheet, "watcher %s" % st,
                                                            lambda t: w.draw(t), T8, 160, 128, ent=w))
    return out


def group_npcs(sheet):
    from jade_sun import sprites_npcs as sprites
    out = {}
    for kind in ("ceiba", "ek", "chaac", "balam", "witz"):
        for talking in (False, True):
            n = measure(sheet, "%s%s" % (kind, " talk" if talking else ""),
                        lambda t, k=kind, tk=talking: sprites.draw_npc(k, 152, 110, t, tk), T8, 160, 100)
            out[kind] = max(out.get(kind, 0), n)
    return out


def group_portraits(sheet):
    from jade_sun import sprites_npcs as sprites
    from jade_sun.sprites_fluff import FluffSkin
    out = {}
    skin = FluffSkin(1)
    for kind in ("fluff", "ceiba", "ek", "chaac", "balam", "witz", "stone", "camazotz"):
        out[kind] = measure(sheet, kind, lambda t, k=kind: sprites.draw_portrait(k, 142, 102, t, skin), (0, 5), 160, 120)
    return out


def group_items(sheet):
    from jade_sun import sprites_items as sprites
    out = {}
    kinds = [k for k in sprites.ITEM_COL] + (["shard"] if "shard" not in sprites.ITEM_COL else [])
    for kind in kinds:
        out[kind] = measure(sheet, kind, lambda t, k=kind: sprites.draw_item(k, 160, 120, t), T8)
        out[kind + "_big"] = measure(sheet, kind + " big", lambda t, k=kind: sprites.draw_item(k, 160, 120, t, True), (0,))
    out["heart_pickup"] = measure(sheet, "heart pickup", lambda t: sprites.draw_heart(160, 118, gfx.RED, 3))
    out["cacao"] = measure(sheet, "cacao", lambda t: sprites.draw_cacao(160, 120, t), T8)
    return out


def group_projectiles(sheet):
    from jade_sun import sprites_items as sprites
    out = {}
    for kind in ("bolt", "beam", "fire", "bubble", "feather", "orb", "rock", "wave", "bat"):
        p = ns(kind=kind, x=160.0, y=104.0, vx=3.0, vy=1.0)
        out[kind] = measure(sheet, kind, lambda t, p=p: sprites.draw_proj(p, t), T8)
    return out


def group_bake(sheet_rooms, only_rooms=None):
    from jade_sun.world import Room
    from jade_sun.world_data import ROOMS
    out = {}
    ms = {}
    for rid in ROOMS:
        if only_rooms and rid not in only_rooms:
            continue
        _count[0] = 0
        t0 = time.perf_counter()
        gfx.bake(Room(rid), 0)
        ms[rid] = int((time.perf_counter() - t0) * 1000)
        out[rid] = _count[0]
        if sheet_rooms is not None:
            sheet_rooms.tiles.append((rid + " " + ROOMS[rid]["name"], display.image.copy()))
    return out, ms


GROUPS = {
    "fluff": (group_fluff, (64, 48)),
    "enemies": (group_enemies, (64, 40)),
    "bosses": (group_bosses, (112, 80)),
    "npcs": (group_npcs, (96, 80)),
    "portraits": (group_portraits, (48, 48)),
    "items": (group_items, (40, 40)),
    "projectiles": (group_projectiles, (40, 24)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true", help="record current counts as the baseline")
    ap.add_argument("--only", default="", help="comma list of groups (fluff,enemies,bosses,npcs,portraits,"
                                               "items,projectiles,rooms)")
    ap.add_argument("--rooms", default="", help="comma list of room ids for the rooms group")
    ap.add_argument("--zoom", type=int, default=3)
    ap.add_argument("--tag", default="", help="suffix for sheet file names, e.g. _tiles")
    ap.add_argument("--hitbox", action="store_true", help="outline gameplay hit rects in magenta on the sheets")
    a = ap.parse_args()
    HITBOX[0] = a.hitbox
    only = set(filter(None, a.only.split(",")))
    base = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}
    report = {}
    bad = []
    for name, (fn, cell) in GROUPS.items():
        if only and name not in only:
            continue
        sh = Sheet(name + a.tag, cell, 8, a.zoom)
        res = fn(sh)
        report[name] = res
        path = sh.save()
        print("== %s  sheet %s" % (name, path))
        caps = CAPS[name]
        for k, v in res.items():
            b = base.get(name, {}).get(k)
            lim = caps.get(k, caps["*"] * (1.5 if k.endswith("_big") else 1))
            flag = ""
            if v > lim:
                flag = "  !! over budget (cap %d)" % lim
                bad.append("%s.%s" % (name, k))
            print("   %-16s %4d  cap %3d%s%s" % (k, v, lim, ("  orig %d" % b) if b else "", flag))
    if not only or "rooms" in only:
        rs = Sheet("rooms" + a.tag, (320, 240), 4, 1)
        rooms_only = set(filter(None, a.rooms.split(",")))
        counts, ms = group_bake(rs, rooms_only)
        report["rooms"] = counts
        path = rs.save()
        print("== rooms  sheet %s" % path)
        from jade_sun.world_data import ROOMS
        for rid, v in counts.items():
            flag = ""
            if v > BAKE_MAX or ms[rid] > BAKE_MS_MAX:
                flag = "  !! over budget (%d calls / %d ms max)" % (BAKE_MAX, BAKE_MS_MAX)
                bad.append("rooms." + rid)
            print("   %-5s %-22s %5d calls %4d ms%s" % (rid, ROOMS[rid]["name"][:22], v, ms[rid], flag))
    if a.baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(report, indent=1))
        print("baseline written", BASELINE)
    print("OVER BUDGET: " + ", ".join(bad) if bad else "BUDGET OK")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
