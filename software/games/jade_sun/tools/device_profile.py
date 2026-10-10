"""On-device per-subsystem frame profile. Deploy first, then: mpremote run games/jade_sun/tools/device_profile.py"""
import time, gc, sys
import jade_sun.game as G
from jade_sun import ui, hw

T = {}


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
    g._start_play("A2", 40, 178)
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
    for rid, x, y in (("A2", 40, 178), ("C1", 160, 178)):
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
