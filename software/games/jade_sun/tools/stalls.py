"""Find stretches of a playthrough trace where the bot jumps a lot but goes nowhere.

Usage:
  PLAY_VIDEO=0 PLAY_TRACE=/tmp/trace.txt .venv/bin/python games/jade_sun/tools/playthrough.py
  .venv/bin/python games/jade_sun/tools/stalls.py /tmp/trace.txt
"""
import sys

WINDOW = 100
MIN_JUMPS = 4
MAX_SPREAD = 56
FPS = 25


def load(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            t, room, x, y, ground, b, kind, arg = line.split()
            rows.append((int(t), room, float(x), float(y), int(ground), int(b), kind, arg))
    return rows


def stalls(rows):
    out = []
    i = 0
    n = len(rows)
    while i + WINDOW < n:
        win = rows[i:i + WINDOW]
        rooms = {r[1] for r in win}
        xs = [r[2] for r in win]
        ys = [r[3] for r in win]
        presses = sum(1 for a, b in zip(win, win[1:]) if b[5] and not a[5])
        if len(rooms) == 1 and presses >= MIN_JUMPS and max(xs) - min(xs) < MAX_SPREAD:
            j = i + WINDOW
            while j < n and rows[j][1] == win[0][1] and abs(rows[j][2] - xs[0]) < MAX_SPREAD:
                j += 1
            seg = rows[i:j]
            out.append((seg[0][0], seg[-1][0], seg[0][1], min(r[2] for r in seg), max(r[2] for r in seg),
                        min(r[3] for r in seg), max(r[3] for r in seg), seg[0][6], seg[0][7]))
            i = j
        else:
            i += 10
    return out


def main():
    rows = load(sys.argv[1])
    found = stalls(rows)
    total = 0
    for t0, t1, room, x0, x1, y0, y1, kind, arg in found:
        secs = (t1 - t0) / FPS
        total += secs
        print("%5.1fs at %s  room %s  x %.0f-%.0f  y %.0f-%.0f  goal %s %s" % (
            secs, "%d:%04.1f" % divmod(t0 / FPS, 60), room, x0, x1, y0, y1, kind, arg))
    print("stalls", len(found), "total %.1fs" % total)


if __name__ == "__main__":
    main()
