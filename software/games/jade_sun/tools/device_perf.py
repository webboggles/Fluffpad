"""On-device timing per room. Deploy first, then: mpremote run games/jade_sun/tools/device_perf.py"""
import time, gc, sys
t0 = time.ticks_ms()
import jade_sun.game as G
print("import_ms", time.ticks_diff(time.ticks_ms(), t0))
try:
    g = G.Game()
    g.items |= {"blade", "pearl", "dash", "feather", "spear"}
    g._start_play("A1", 100, 178)
    for rid, x, y in (("A2", 40, 178), ("B1", 160, 60), ("B2", 300, 60), ("C1", 160, 178), ("C3", 100, 178),
                      ("D1", 160, 100), ("E1", 160, 178), ("C2", 150, 178)):
        t = time.ticks_ms()
        g.enter_room(rid, x, y)
        bake = time.ticks_diff(time.ticks_ms(), t)
        work = worst = 0
        for i in range(60):
            t = time.ticks_ms()
            g.frame()
            dt = time.ticks_diff(time.ticks_ms(), t)
            work += dt
            worst = max(worst, dt)
        gc.collect()
        print(rid, "enter_ms", bake, "frame_avg", work // 60, "worst", worst, "free", gc.mem_free())
    t = time.ticks_ms()
    gc.collect()
    print("gc_ms", time.ticks_diff(time.ticks_ms(), t))
except Exception as e:
    sys.print_exception(e)
finally:
    G.hw.restore_clocks()
