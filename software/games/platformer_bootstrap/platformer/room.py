"""The single room: tile map, collision queries and baked background art."""
from micropython import const
from .hw import display

COLS = const(20)
ROWS = const(14)
TS = const(16)
HUD = const(16)

T_EMPTY = const(0)
T_ROCK = const(1)
T_PLANK = const(2)
T_SPIKE = const(3)

SOLID = bytes((0, 1, 0, 0))
_CHAR = {".": T_EMPTY, "#": T_ROCK, "=": T_PLANK, "^": T_SPIKE}

# '#' rock, '=' one-way plank (Down + jump drops through), '^' spikes,
# 'o' coin, 'P' player start. Every row is exactly COLS wide.
MAP = (
    "####################",
    "#..................#",
    "#..o...........o...#",
    "#.====.......====..#",
    "#..................#",
    "#........o.........#",
    "#......======......#",
    "#..o...........o...#",
    "#####.........######",
    "#.........o........#",
    "#...===.......===..#",
    "#.P................#",
    "#.......^^^^.......#",
    "####################",
)


class Room:
    def __init__(self):
        self.t = bytearray(COLS * ROWS)
        self.coins = []
        self.start = (32, 160)
        for r in range(ROWS):
            line = MAP[r]
            for c in range(COLS):
                ch = line[c]
                tile = _CHAR.get(ch)
                if tile is None:
                    tile = T_EMPTY
                    if ch == "o":
                        self.coins.append((c * TS + 8, r * TS + 8))
                    elif ch == "P":
                        self.start = (c * TS + 3, r * TS + 2)
                self.t[r * COLS + c] = tile

    def tile(self, c, r):
        if c < 0 or c >= COLS or r < 0 or r >= ROWS:
            return T_ROCK
        return self.t[r * COLS + c]

    def at(self, px, py):
        return self.tile(int(px) >> 4, int(py) >> 4)


SKY = display.create_pen(24, 32, 56)
ROCK = display.create_pen(92, 84, 110)
ROCK_TOP = display.create_pen(130, 200, 120)
ROCK_EDGE = display.create_pen(60, 54, 76)
PLANK = display.create_pen(170, 120, 70)
PLANK_EDGE = display.create_pen(110, 72, 40)
SPIKE = display.create_pen(220, 220, 235)


def bake(room):
    """Draw static tiles once; the game snapshots this into the background cache."""
    display.set_pen(SKY)
    display.clear()
    for r in range(ROWS):
        for c in range(COLS):
            t = room.t[r * COLS + c]
            x, y = c * TS, r * TS + HUD
            if t == T_ROCK:
                display.set_pen(ROCK)
                display.rectangle(x, y, TS, TS)
                display.set_pen(ROCK_EDGE)
                display.rectangle(x, y + TS - 2, TS, 2)
                if room.tile(c, r - 1) != T_ROCK:
                    display.set_pen(ROCK_TOP)
                    display.rectangle(x, y, TS, 3)
            elif t == T_PLANK:
                display.set_pen(PLANK)
                display.rectangle(x, y, TS, 5)
                display.set_pen(PLANK_EDGE)
                display.rectangle(x, y + 5, TS, 1)
            elif t == T_SPIKE:
                display.set_pen(SPIKE)
                for k in range(0, TS, 8):
                    display.triangle(x + k, y + TS, x + k + 4, y + 7, x + k + 8, y + TS)
