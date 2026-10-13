"""On-device per-subsystem frame profile. Deploy first, then: mpremote run games/jade_sun/tools/device_profile.py"""
import time, sys
import jade_sun.game as G
from jade_sun import ui, hw
from jade_sun.world_data import ROOMS

PROFILE_ROOMS = ("A1", "C5", "F4", "E7")
T = {}


def spawn(rows):
    for r in range(len(rows) - 2, 0, -1):
        for c in range(2, 18):
            if rows[r][c] == "." and rows[r - 1][c] == "." and rows[r + 1][c] in "#=%g":
                return c * 16 + 3, (r + 1) * 16 - 14
    return 48, 160


def wrap(obj, name, label):
    f = getattr(obj, name)

    def w(*a, **k):
        t = time.ticks_us()
        r = f(*a, **k)
        T[label] = T.get(label, 0) + time.ticks_diff(time.ticks_us(), t)
        return r
    setattr(obj, name, w)


try:
    g = G.Game()
    g.items |= {"blade", "pearl", "dash", "feather", "spear"}
    g._start_play("A1", 100, 178)
    wrap(g.inp, "poll", "poll")
    wrap(g, "update_play", "update")
    wrap(g.audio, "tick", "audio")
    wrap(g.mood, "tick", "mood")
    wrap(G, "restore_bg", "restore")
    wrap(ui, "hud", "hud")
    wrap(g.fx, "ambience", "ambience")
    wrap(g.fx, "draw", "fxdraw")
    wrap(g, "draw_player", "player")
    wrap(g, "draw", "draw_total")
    for name in ("draw_surfaces", "draw_flame", "draw_shrine_glow", "draw_lore_glint"):
        wrap(G.tiles, name, name[5:])
    for name in ("draw_enemy", "draw_npc", "draw_cacao", "draw_item", "draw_proj", "draw_heart"):
        wrap(G.sprites, name, name[5:])
    for rid in PROFILE_ROOMS:
        x, y = spawn(ROOMS[rid]["map"])
        g.enter_room(rid, x, y)
        T.clear()
        N = 80
        for i in range(N):
            g.frame()
        print(rid, " ".join("%s=%.1f" % (k, v / N / 1000) for k, v in sorted(T.items())))
except Exception as e:
    sys.print_exception(e)
finally:
    hw.restore_clocks()
