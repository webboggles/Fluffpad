"""Tile room model and collision queries."""
from micropython import const
from . import world_data as wd

COLS = const(20)
ROWS = const(14)
TS = const(16)
RW = const(320)
RH = const(224)

T_EMPTY = const(0)
T_ROCK = const(1)
T_CRACK = const(2)
T_PLANK = const(3)
T_GRATE = const(4)
T_SPIKE = const(5)
T_WATER = const(6)
T_SEAL = const(7)
T_RAIN = const(8)
T_GATE = const(9)
T_SHUT = const(10)

SOLID = bytes((0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1))
_CHAR = {".": T_EMPTY, "#": T_ROCK, "%": T_CRACK, "=": T_PLANK, "g": T_GRATE,
         "^": T_SPIKE, "~": T_WATER, "S": T_SEAL, "R": T_RAIN, "G": T_GATE}


class Room:
    def __init__(self, rid, broken=()):
        d = wd.ROOMS[rid]
        self.id = rid
        self.meta = d
        self.zone = d["zone"]
        x, y = d["pos"]
        self.rx, self.ry = x, y
        self.nb_w = wd.AT.get((x - 1, y))
        self.nb_e = wd.AT.get((x + 1, y))
        self.nb_n = wd.AT.get((x, y - 1))
        self.nb_s = wd.AT.get((x, y + 1))
        self.t = bytearray(COLS * ROWS)
        self.open_as = bytearray(COLS * ROWS)
        self.spawns = []
        self.doors = []
        rows = d["map"]
        for r in range(ROWS):
            line = rows[r]
            for c in range(COLS):
                ch = line[c]
                wet = self._wet(rows, c, r)
                i = r * COLS + c
                self.open_as[i] = T_WATER if wet else T_EMPTY
                tile = _CHAR.get(ch)
                if tile is None:
                    tile = self.open_as[i]
                    if ch == "B":
                        self.doors.append(i)
                    else:
                        self.spawns.append((ch, c, r))
                self.t[i] = tile
        for i in broken:
            self.t[i] = self.open_as[i]
        self.has_water = False
        for v in self.t:
            if v == T_WATER:
                self.has_water = True
                break

    @staticmethod
    def _wet(rows, c, r):
        if rows[r][c] == "~":
            return True
        for dc, dr in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            cc, rr = c + dc, r + dr
            if 0 <= cc < COLS and 0 <= rr < ROWS and rows[rr][cc] == "~":
                return True
        return False

    def open_tiles(self, kind):
        """Turn every tile of a kind into its open state. Returns list of indices."""
        out = []
        t = self.t
        for i in range(COLS * ROWS):
            if t[i] == kind:
                t[i] = self.open_as[i]
                out.append(i)
        return out

    def shut_doors(self, shut=True):
        for i in self.doors:
            self.t[i] = T_SHUT if shut else self.open_as[i]

    def tile(self, c, r):
        if c < 0:
            return T_EMPTY if self.nb_w else T_ROCK
        if c >= COLS:
            return T_EMPTY if self.nb_e else T_ROCK
        if r < 0:
            if self.nb_n:
                return self.t[c] if self.t[c] == T_WATER else T_EMPTY
            return T_ROCK
        if r >= ROWS:
            if self.nb_s:
                return self.t[(ROWS - 1) * COLS + c] if self.t[(ROWS - 1) * COLS + c] == T_WATER else T_EMPTY
            return T_ROCK
        return self.t[r * COLS + c]

    def at(self, px, py):
        return self.tile(int(px) >> 4, int(py) >> 4)

    def solid(self, px, py):
        return SOLID[self.tile(int(px) >> 4, int(py) >> 4)]

    def water(self, px, py):
        return self.tile(int(px) >> 4, int(py) >> 4) == T_WATER

    def los(self, x0, y0, x1, y1):
        """Coarse line of sight: no solid tile on the segment."""
        dx, dy = x1 - x0, y1 - y0
        n = int(max(abs(dx), abs(dy)) / 8) + 1
        for k in range(1, n):
            if self.solid(x0 + dx * k / n, y0 + dy * k / n):
                return False
        return True
