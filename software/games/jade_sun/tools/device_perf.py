"""On-device timing per room. Deploy first, then: mpremote run games/jade_sun/tools/device_perf.py
Optional: set ROOMS_ONLY below to a tuple of room ids to time a subset."""
import time, gc, sys
ROOMS_ONLY = None
FRAMES = 30
t0 = time.ticks_ms()
import jade_sun.game as G
from jade_sun.world_data import ROOMS
print("import_ms", time.ticks_diff(time.ticks_ms(), t0))


def spawn(rows):
    for r in range(len(rows) - 2, 0, -1):
        for c in range(2, 18):
            if rows[r][c] == "." and rows[r - 1][c] == "." and rows[r + 1][c] in "#=%g":
                return c * 16 + 3, (r + 1) * 16 - 14
    return 48, 160


try:
    g = G.Game()
    g.items |= {"blade", "pearl", "dash", "feather", "spear"}
    g._start_play("A1", 100, 178)
    worst_enter = worst_frame = 0
    for rid in sorted(ROOMS_ONLY or ROOMS):
        x, y = spawn(ROOMS[rid]["map"])
        t = time.ticks_ms()
        g.enter_room(rid, x, y)
        bake = time.ticks_diff(time.ticks_ms(), t)
        work = worst = 0
        for i in range(FRAMES):
            t = time.ticks_ms()
            g.frame()
            dt = time.ticks_diff(time.ticks_ms(), t)
            work += dt
            worst = max(worst, dt)
        gc.collect()
        worst_enter = max(worst_enter, bake)
        worst_frame = max(worst_frame, worst)
        print(rid, "enter_ms", bake, "frame_avg", work // FRAMES, "worst", worst, "free", gc.mem_free())
    t = time.ticks_ms()
    gc.collect()
    print("gc_ms", time.ticks_diff(time.ticks_ms(), t))
    print("WORST enter_ms", worst_enter, "frame_ms", worst_frame)
except Exception as e:
    sys.print_exception(e)
finally:
    G.hw.restore_clocks()
