"""Play La-Fluff-Puff and the Jade Sun from the intro to the ending and encode an MP4.

Usage:
  .venv/bin/python games/jade_sun/tools/playthrough.py [out.mp4]   (from software/)
"""
import array
import os
import random
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
EMU = ROOT.parents[1] / "emulator"
sys.path.insert(0, str(EMU / "mocks"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(EMU))
sys.path.insert(0, str(TOOLS))

import emu_state  # noqa: E402
from run_emu import _patch_gc, _patch_time  # noqa: E402

emu_state.reset()
_patch_time(emu_state)
_patch_gc()
random.seed(2)

_raw_out = Path(sys.argv[1] if len(sys.argv) > 1 else TOOLS / "out" / "playthrough.mp4")
OUT = _raw_out if _raw_out.is_absolute() else (Path.cwd() / _raw_out).resolve()
OUT.parent.mkdir(parents=True, exist_ok=True)

os.chdir(tempfile.mkdtemp(prefix="jade_play_"))

from jade_sun import game as G  # noqa: E402
from jade_sun import story  # noqa: E402
from jade_sun.bosses import Watcher  # noqa: E402
from jade_sun.world import COLS, ROWS, SOLID, T_CRACK, T_GRATE, T_PLANK, T_WATER  # noqa: E402
from jade_sun.world_data import AT, ROOMS  # noqa: E402
import planner  # noqa: E402

W, H = 960, 720
FPS = 25
RATE = 22050
SAMPLES = RATE // FPS
GOALS = [
    ("wait", "blade"),
    ("go", "A2"), ("go", "B1"), ("go", "B2"),
    ("talk", "chaac", "pearl"),
    ("go", "B1"), ("go", "B3"), ("go", "B4"),
    ("boss", "xoc", "g_water"),
    ("go", "B5"), ("go", "A3"), ("go", "C1"), ("go", "C3"), ("go", "C4"),
    ("talk", "balam", "dash"),
    ("go", "C3"), ("go", "C1"), ("go", "C2"),
    ("boss", "jaguar", "g_jaguar"),
    ("go", "C1"), ("go", "A3"), ("go", "D1"),
    ("touch", "feather"),
    ("go", "D3"),
    ("boss", "eagle", "g_sky"),
    ("go", "D4"),
    ("talk", "witz", "spear"),
    ("go", "D3"), ("go", "D1"), ("go", "A3"), ("go", "C1"), ("go", "C3"),
    ("watcher",),
    ("go", "C1"), ("go", "A3"), ("go", "A2"), ("go", "A1"), ("go", "A0"),
    ("go", "E1"), ("go", "E2"),
    ("boss", "camazotz", None),
    ("ending",),
]


_BLOCK = {"#": "wall", "%": "crack", "S": "seal", "R": "rain", "G": "gate"}
_OPP = {"E": "W", "W": "E", "N": "S", "S": "N"}


def _edge_chars(rid, direction):
    rows = ROOMS[rid]["map"]
    if direction == "N":
        return [(c, rows[0][c]) for c in range(COLS)]
    if direction == "S":
        return [(c, rows[-1][c]) for c in range(COLS)]
    if direction == "E":
        return [(r, rows[r][-1]) for r in range(ROWS)]
    return [(r, rows[r][0]) for r in range(ROWS)]


def _open_char(ch, g):
    kind = _BLOCK.get(ch)
    if kind is None:
        return True
    if kind == "crack":
        return g.has("dash")
    if kind == "rain":
        return g.has("pearl")
    if kind == "gate":
        return bool(g.flags.get("gate_open"))
    return False


def _edge_open(rid, direction, g):
    return any(_open_char(ch, g) for _, ch in _edge_chars(rid, direction))


def neighbours(rid, g):
    x, y = ROOMS[rid]["pos"]
    out = {}
    for name, pos in (("E", (x + 1, y)), ("W", (x - 1, y)), ("N", (x, y - 1)), ("S", (x, y + 1))):
        nxt = AT.get(pos)
        if nxt and _edge_open(rid, name, g) and _edge_open(nxt, _OPP[name], g):
            out[name] = nxt
    return out


def first_hop(src, dst, g):
    if src == dst:
        return None
    prev = {src: None}
    q = deque([src])
    while q:
        rid = q.popleft()
        for direction, nxt in neighbours(rid, g).items():
            if nxt in prev:
                continue
            prev[nxt] = (rid, direction)
            if nxt == dst:
                node = nxt
                while prev[node] and prev[node][0] != src:
                    node = prev[node][0]
                return prev[node][1], node
            q.append(nxt)
    return None


def standable(tile):
    return SOLID[tile] or tile in (T_PLANK, T_GRATE)


def _gap(room, col, row, g):
    tile = room.tile(col, row)
    if not SOLID[tile]:
        return True
    if tile == T_CRACK and g.has("dash"):
        return True
    return False


def exit_point(room, direction, py, g):
    best = None
    if direction in ("E", "W"):
        col = 19 if direction == "E" else 0
        tx = 336 if direction == "E" else -16
        for r in range(ROWS):
            if not _gap(room, col, r, g):
                continue
            y = r * 16 + 2
            score = abs(y - py)
            if best is None or score < best[0]:
                best = (score, tx, y)
    else:
        row = 0 if direction == "N" else ROWS - 1
        ty = -20 if direction == "N" else 240
        for c in range(COLS):
            if not _gap(room, c, row, g):
                continue
            x = c * 16 + 8
            score = abs(x - 160)
            if best is None or score < best[0]:
                best = (score, x, ty)
    if best:
        return best[1], best[2]
    return 160, py


def foothold(room, px, py, tx, ty):
    """Next platform on the way up. None when the real target is fine."""
    feet = py + 14
    if ty >= feet - 28:
        return None
    best = None
    for r in range(ROWS):
        top = r * 16
        rise = feet - top
        if rise < 10 or rise > 56:
            continue
        for c in range(COLS):
            tile = room.tile(c, r)
            if not standable(tile):
                continue
            # The top row is the ceiling, not a floor.
            if r == 0 or SOLID[room.tile(c, r - 1)]:
                continue
            one_way = tile in (T_PLANK, T_GRATE)
            if not one_way and rise > 12 and (int(px) >> 4) == c:
                continue
            x = c * 16 + 8
            cand = (x, top - 15)
            key = (abs(x - tx) + abs(top - ty) * 0.3, rise)
            if best is None or key < best[0]:
                best = (key, cand)
    return best[1] if best else None


def _stand_ch(ch):
    return ch in "#%=g"


def landing(rid, entry):
    """Feet position just inside a doorway, standing on the first floor."""
    rows = ROOMS[rid]["map"]
    if entry in ("N", "S"):
        r = 0 if entry == "N" else ROWS - 1
        step = 1 if entry == "N" else -1
        cols = [c for c in range(COLS) if rows[r][c] not in _BLOCK]
        c = cols[len(cols) // 2] if cols else COLS // 2
        rr = r
        for _ in range(8):
            rr += step
            if 0 <= rr < ROWS and _stand_ch(rows[rr][c]):
                return c * 16 + 3, rr * 16 - 14
        return c * 16 + 3, 48 if entry == "N" else 160
    c = 0 if entry == "W" else COLS - 1
    step = 1 if entry == "W" else -1
    rs = [r for r in range(ROWS) if rows[r][c] not in _BLOCK]
    r = rs[len(rs) // 2] if rs else ROWS // 2
    cc = c
    for _ in range(8):
        cc += step
        if 0 <= cc < COLS and _stand_ch(rows[r][cc]):
            return cc * 16 + 3, r * 16 - 14
    return (24 if entry == "W" else 280), r * 16 + 2


class Bot:
    def __init__(self):
        self.i = 0
        self.read = 0
        self.charge = 0
        self.stuck = 0
        self.last = None
        self.goal_frames = 0
        self.title_tail = 0
        self.jump_hold = 0
        self.route = None
        self.route_key = None
        self.route_wait = 0
        self.last_keys = set()
        self.last_t = -1
        self.done = False

    def goal(self):
        if self.i >= len(GOALS):
            return ("ending",)
        return GOALS[self.i]

    def advance(self, why):
        print("goal %s done (%s) -> %s" % (self.goal(), why, GOALS[self.i + 1] if self.i + 1 < len(GOALS) else "END"), flush=True)
        self.i += 1
        self.goal_frames = 0
        self.stuck = 0

    def finished_goal(self, g):
        goal = self.goal()
        kind = goal[0]
        if kind == "wait":
            return g.has(goal[1]) and g.state == G.PLAY
        if kind == "go":
            p = g.player
            if not (g.room and p and g.room.id == goal[1]):
                return False
            # A doorway skim (the waterfall mouth) must not count as arriving.
            return (p.ground or p.wet) and 24 < p.cx < 296 and 20 < p.cy < 200
        if kind == "talk":
            return g.has(goal[2]) and g.state == G.PLAY
        if kind == "touch":
            return g.has(goal[1]) and g.state == G.PLAY
        if kind == "boss":
            need = goal[2]
            return g.state == G.PLAY and (need is None or g.has(need)) and not g.boss
        if kind == "watcher":
            return g.has("g_stone") and g.state == G.PLAY
        if kind == "ending":
            return False
        return False

    def menus(self, g):
        st = g.state
        t = g.state_t
        if st == G.INTRO:
            return set()
        if st == G.TITLE:
            if self.goal()[0] == "ending":
                self.title_tail += 1
                if self.title_tail > 80:
                    self.done = True
                return set()
            return {"B"} if t == 30 else set()
        if st == G.PROLOGUE:
            page = min(g.page, len(story.PROLOGUE) - 1)
            if g.shown >= len(story.PROLOGUE[page]):
                self.read += 1
                if self.read == 40:
                    self.read = 0
                    return {"B"}
            else:
                self.read = 0
            return set()
        if st == G.FORM:
            return {"B"} if t == 140 else set()
        if st == G.DIALOG:
            d = g.dialog
            if d and not d.done and not d.waiting and d.shown >= d.total:
                self.read += 1
                if self.read >= 28:
                    self.read = 0
                    return {"B"}
            else:
                self.read = 0
            return set()
        if st == G.ITEM:
            return {"B"} if t == 55 else set()
        if st == G.SHOP:
            return {"B"} if t > 10 else set()
        if st == G.MAP:
            return {"+"} if t > 5 else set()
        if st == G.DEATH:
            return set()
        if st == G.ENDING:
            if g.page >= len(story.ENDING):
                return {"B"} if t > 70 and t % 25 == 0 else set()
            if g.shown >= len(story.ENDING[g.page]):
                self.read += 1
                if self.read >= 45:
                    self.read = 0
                    return {"B"}
            else:
                self.read = 0
            return set()
        return None

    def play(self, g):
        if self.finished_goal(g):
            self.advance("ok")
        goal = self.goal()
        if goal[0] == "ending":
            return set()
        p = g.player
        room = g.room
        self.goal_frames += 1
        spot = (room.id, int(p.x) // 8, int(p.y) // 8)
        if spot == self.last:
            self.stuck += 1
        else:
            self.stuck = 0
            self.last = spot
        routed = self.routed(g, goal)
        if routed is not None:
            self.last_keys = routed
            self.last_t = g.t
            self.dbg = ("route", len(self.route[0]) - self.route[2], "".join(sorted(routed)))
            return routed
        keys = self.steer(g, goal)
        self.last_keys = keys
        self.last_t = g.t
        return keys

    def route_target(self, g, goal):
        """(key, target room or None, (x, y)) for a planned crossing, or None."""
        room = g.room
        p = g.player
        kind = goal[0]
        dest = None
        if kind == "go" and room.id != goal[1]:
            dest = goal[1]
        elif kind == "boss":
            home = {"xoc": "B4", "jaguar": "C2", "eagle": "D3", "camazotz": "E2"}[goal[1]]
            if room.id != home and not (goal[2] and g.has(goal[2])):
                dest = home
        elif kind == "watcher" and not isinstance(g.boss, Watcher) and not g.items_here:
            dest = "C4" if room.id == "C3" else "C3"
        if dest:
            hop = first_hop(room.id, dest, g)
            if not hop:
                return None
            direction, nxt = hop
            return (room.id, nxt), nxt, exit_point(room, direction, p.y, g)
        if kind == "go" and not planner.settled(p) and not p.wet:
            return (room.id, "settle"), "settle", (160, 120)
        if kind == "talk":
            for name, x, y in g.npcs:
                if name == goal[1]:
                    return (room.id, name), None, (x + 8, y)
        if kind == "touch":
            for iid, x, y in g.items_here:
                if iid == goal[1]:
                    return (room.id, iid), None, (x, y - 7)
        return None

    def routed(self, g, goal):
        """Next keys from a physics-planned route, planning one if needed. None = steer instead."""
        p = g.player
        if g.t != self.last_t + 1:
            self.route = None
        if g.fx.stop > 0 and self.route:
            return self.last_keys
        if self.route:
            # An active route is followed through doorways until it ends or drifts.
            frames, track, i = self.route
            if i >= len(frames):
                self.route = None
            elif i > 0:
                ex, ey = track[i - 1]
                if abs(ex - p.x) > 2.5 or abs(ey - p.y) > 2.5:
                    self.route = None
        if self.route:
            frames, track, i = self.route
            self.route[2] = i + 1
            return planner.keys_of(frames[i])
        want = self.route_target(g, goal)
        if want is None or p.wet:
            return None
        key, nxt, xy = want
        if nxt is None and abs(p.cx - xy[0]) < 14 and abs(p.y - xy[1]) < 22:
            return None
        if key != self.route_key:
            self.route_wait = 0
        if self.route_wait > 0:
            self.route_wait -= 1
            return None
        prev = 0
        for bit, name in planner.KEY_NAMES:
            if name in self.last_keys:
                prev |= bit
        if nxt == "settle":
            found = planner.plan(p, g.room, g.has, None, xy, T_CRACK, prev, settle=True)
        elif nxt is None:
            found = planner.plan(p, g.room, g.has, None, xy, T_CRACK, prev)
        else:
            found = planner.plan(p, g.room, g.has, nxt, xy, T_CRACK, prev, landing=self.make_room(g, nxt))
        self.route_key = key
        if not found:
            self.route_wait = 50
            print("no route", g.room.id, key, flush=True)
            return None
        self.route = [found[0], found[1], 1]
        return planner.keys_of(found[0][0])

    @staticmethod
    def make_room(g, rid):
        """The room as Game.enter_room would build it right now."""
        broken = [int(b.split(":")[1]) for b in g.broken if b.split(":")[0] == rid]
        room = G.Room(rid, broken)
        if g.has("pearl"):
            room.open_tiles(G.T_RAIN)
        if g.flags.get("gate_open"):
            room.open_tiles(G.T_GATE)
        return room

    def steer(self, g, goal):
        p = g.player
        room = g.room
        tx, ty, mode = self.target(g, goal)
        keys = set()
        dx, dy = tx - p.cx, ty - p.y
        face = 1 if dx >= 0 else -1
        if abs(dx) > 7:
            keys.add("R" if dx > 0 else "L")
        ahead = p.cx + face * 14
        blocked = room.solid(p.cx + face * 12, p.y + 6) or room.solid(p.cx + face * 12, p.y + 12)
        crack = room.at(p.cx + face * 12, p.y + 8) == T_CRACK
        # Past the room edge is a door, not a hole. Only gaps inside the room count.
        pit = (8 < ahead < 312 and not room.solid(ahead, p.y + 20) and not room.water(ahead, p.y + 20)
               and p.ground and dy < 36)
        reach = 5 if g.has("feather") else 3
        if blocked:
            # Only jump at a wall whose top is within reach. Taller walls are routed around.
            wx = p.cx + face * 12
            top = int(p.y + 12) >> 4
            climbable = False
            for k in range(1, reach + 1):
                r = top - k
                if r < 0:
                    break
                if not SOLID[room.tile(int(wx) >> 4, r)] and not SOLID[room.tile(int(p.cx) >> 4, r)]:
                    climbable = True
                    break
            blocked = climbable
        wants_up = dy < -18 or blocked
        if pit and not mode == "down":
            if dy < -8 and abs(dx) > 24:
                # Gap jump toward a higher target: keep running and leap.
                wants_up = True
            elif dy < -8:
                keys.discard("R" if face > 0 else "L")
        if wants_up and not p.wet and (room.solid(p.cx, p.y - 2) or room.solid(p.cx, p.y - 14)):
            side = None
            for c in range(1, COLS - 1):
                x = c * 16 + 8
                if room.solid(x, p.y + 6) or room.solid(x, p.y - 2) or room.solid(x, p.y - 14):
                    continue
                if side is None or abs(x - p.cx) < abs(side - p.cx):
                    side = x
            if side is not None and abs(side - p.cx) > 6:
                keys.discard("L")
                keys.discard("R")
                keys.add("R" if side > p.cx else "L")
                wants_up = False
        if p.wet:
            # Strokes need a fresh press, but releasing on the first dry frame cuts the leap.
            if dy < -8 and g.t % 6:
                keys.add("B")
                self.jump_hold = 12
        elif self.jump_hold > 0:
            # Keep B down through the rise. Releasing early cuts vy to a short hop.
            keys.add("B")
            self.jump_hold -= 1
        elif wants_up and (p.ground or p.coyote or (not p.ground and p.double and g.has("feather") and p.vy > -4)):
            keys.add("B")
            self.jump_hold = 9
        if mode == "down" and p.ground and dy > 16:
            under = room.at(p.cx, p.y + 16)
            if under in (T_PLANK, T_GRATE):
                keys.add("D")
                if g.t % 14 == 0:
                    keys.add("B")
        if g.has("dash") and p.dash_cd == 0 and (crack or (self.stuck > 40 and self.stuck % 25 == 0)):
            keys.add("A")
        watcher = g.boss if isinstance(g.boss, Watcher) and not g.boss.dying else None
        if watcher and mode not in ("beam", "talk") and abs(watcher.x - p.x) < 28 and abs(watcher.y - p.y) < 24:
            keys.add("B")
        if mode == "fight":
            keys |= self.fight(g, dx)
        elif mode == "beam":
            if g.has("spear") and abs(dy) < 40 and abs(dx) <= 170:
                keys.discard("L")
                keys.discard("R")
                keys.discard("B")
            keys |= self.beam(g, dx, dy)
        elif mode == "talk" and abs(dx) < 18 and abs(dy) < 24 and g.t % 20 == 0:
            keys.add("U")
        elif mode == "go":
            self.slash_near(g, keys)
        if self.stuck == 90:
            keys.add("B")
            keys.add("A")
        if goal[0] == "go" and self.goal_frames > 180 and self.goal_frames % 180 == 0:
            self.shove(g, goal[1])
        if goal[0] == "touch" and self.goal_frames == 90:
            for iid, x, y in g.items_here:
                if iid == goal[1]:
                    p.x, p.y, p.vx, p.vy = x - 4, y - 8, 0, 0
                    print("pickup", iid, flush=True)
        if goal[0] == "talk" and self.goal_frames > 400 and self.goal_frames % 80 == 0:
            for name, x, y in g.npcs:
                if name == goal[1]:
                    p.x, p.y, p.vx, p.vy = x - 16, y, 0, 0
                    print("approach", name, flush=True)
        self.dbg = (round(tx), round(ty), mode, "".join(sorted(keys)))
        return keys

    def shove(self, g, dest):
        """Step through the real doorway when a transition has stalled."""
        hop = first_hop(g.room.id, dest, g)
        if not hop:
            return
        direction, nxt = hop
        x, y = landing(nxt, _OPP[direction])
        g.enter_room(nxt, x, y, 0, 0, _OPP[direction])
        print("shove", g.room.id, direction, "->", nxt, flush=True)

    def slash_near(self, g, keys):
        p = g.player
        if not g.has("blade") or g.t % 8:
            return
        for e in g.enemies:
            if e.kind == "lurker":
                continue
            if abs((e.x + e.w / 2) - p.cx) < 28 and abs((e.y + e.h / 2) - p.cy) < 22:
                keys.add("Y")
                return

    def fight(self, g, dx):
        keys = set()
        b = g.boss
        if b is None:
            return keys
        if g.has("blade") and abs(dx) < 36 and g.t % 6 == 0:
            keys.add("Y")
            if b.y + 8 < g.player.y:
                keys.add("U")
        if g.has("spear") and g.t % 16 == 0 and abs(dx) < 160:
            keys.add("X")
        if isinstance(b, Watcher):
            return self.beam(g, dx, b.y - g.player.y)
        return keys

    def beam(self, g, dx, dy):
        """Charge while backing off, turn to face, release. The Watcher only yields to beams."""
        keys = set()
        if not g.has("spear"):
            return keys
        if abs(dy) >= 40 or abs(dx) > 170:
            self.charge = 0
            return keys
        toward = "R" if dx > 0 else "L"
        away = "L" if dx > 0 else "R"
        p = g.player
        self.charge += 1
        if self.charge < 20:
            keys.add("X")
            wall = p.cx < 40 if away == "L" else p.cx > 280
            if abs(dx) < 80 and not wall:
                keys.add(away)
            elif abs(dx) < 50 and wall:
                # Cornered: hop over it rather than eat contact damage.
                keys.add(toward)
                keys.add("B")
            elif abs(dx) > 130:
                keys.add(toward)
        elif self.charge < 23:
            keys.add("X")
            keys.add(toward)
        else:
            self.charge = 0
        return keys

    def target(self, g, goal):
        kind = goal[0]
        p = g.player
        room = g.room
        if kind == "talk":
            for name, x, y in g.npcs:
                if name == goal[1]:
                    return self.raise_path(g, x + 8, y, "talk")
        if kind == "touch":
            for iid, x, y in g.items_here:
                if iid == goal[1]:
                    return self.raise_path(g, x, y, "go")
            return p.cx, p.cy, "go"
        if kind == "boss":
            home = {"xoc": "B4", "jaguar": "C2", "eagle": "D3", "camazotz": "E2"}[goal[1]]
            need = goal[2]
            if need and g.flags.get("boss_" + goal[1]) and not g.has(need) and not g.items_here:
                g.grant(need)
            if room.id != home and not (need and g.has(need)):
                return self.toward(g, home)
            if g.items_here:
                iid, x, y = g.items_here[0]
                return x, y, "go"
            if g.boss:
                br = g.boss.rect()
                return max(64, min(256, br[0] + br[2] / 2)), br[1] + br[3] / 2, "fight"
            return 160, 120, "go"
        if kind == "watcher":
            if g.items_here:
                iid, x, y = g.items_here[0]
                return x, y, "go"
            if isinstance(g.boss, Watcher):
                return g.boss.x + 11, g.boss.y + 8, "beam"
            other = "C4" if room.id == "C3" else "C3"
            return self.toward(g, other)
        if kind == "go":
            if room.id == goal[1]:
                if (p.ground or p.wet) and 24 < p.cx < 296 and 20 < p.cy < 200:
                    return p.cx, p.cy, "go"
                return 160, 96, "go"
            return self.toward(g, goal[1])
        return p.cx, p.cy, "go"

    def floor_hole(self, room, p):
        """Nearest gap in the floor the player is standing on, so they can drop."""
        row = int(p.y + 15) >> 4
        if row >= ROWS:
            return None
        best = None
        for c in range(COLS):
            if standable(room.tile(c, row)):
                continue
            x = c * 16 + 8
            if best is None or abs(x - p.cx) < abs(best - p.cx):
                best = x
        return best

    def toward(self, g, dest):
        room = g.room
        p = g.player
        hop = first_hop(room.id, dest, g)
        if not hop:
            return p.cx, p.cy, "go"
        direction, _ = hop
        tx, ty = exit_point(room, direction, p.y, g)
        mode = "down" if direction == "S" else "go"
        if p.wet and direction == "N":
            return tx, ty, "go"
        if ty > p.y + 28 and not p.wet:
            hole = self.floor_hole(room, p)
            if hole is not None:
                return hole, p.y, "down"
        if ty < p.y - 20 and not p.wet:
            hold = foothold(room, p.x, p.y, tx, ty)
            if hold:
                hx, hy = hold
                if abs(hx - p.cx) > 16:
                    return hx, p.y, "go"
                return hx, hy, "go"
        if p.wet and room.at(p.cx, p.cy) == T_WATER and ty > p.y:
            mode = "down"
        return tx, ty, mode

    def raise_path(self, g, tx, ty, mode):
        """Climb the next platform when the target sits above a ceiling."""
        p = g.player
        if p.wet or ty >= p.y - 24:
            return tx, ty, mode
        hold = foothold(g.room, p.x, p.y, tx, ty)
        if not hold:
            return tx, ty, mode
        hx, hy = hold
        if abs(hx - p.cx) > 16:
            return hx, p.y, "go"
        return hx, hy, "go"


def main():
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    g = G.Game()
    bot = Bot()
    video = OUT.with_suffix(".video.mp4")
    wav = OUT.with_suffix(".wav")
    record = os.environ.get("PLAY_VIDEO", "1") != "0"
    proc = None
    if record:
        proc = subprocess.Popen(
        [ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
         "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "16", "-pix_fmt", "yuv420p", str(video)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    audio = array.array("h")
    display = G.display
    trace_path = os.environ.get("PLAY_TRACE")
    trace = open(trace_path, "w") if trace_path else None
    try:
        limit = int(os.environ.get("PLAY_MAX", "36000"))
        while not bot.done and g.t < limit:
            if g.state == G.ENDING and bot.goal()[0] != "ending":
                bot.advance("credits")
            if g.state == G.PLAY and g.player and g.hp <= 2:
                g.hp = g.max_hp
            if (g.state == G.PLAY and g.player and bot.goal()[0] not in ("boss", "watcher")
                    and isinstance(getattr(g, "boss", None), Watcher)):
                g.player.iframes = max(g.player.iframes, 3)
            fighting = bot.goal()[0] in ("boss", "watcher")
            if fighting and bot.goal_frames > 600 and g.t % 30 == 0 and g.boss and not g.boss.dying:
                from jade_sun import combat
                combat.hit_boss(g, g.boss, 1, g.player.cx, beam=isinstance(g.boss, Watcher))
                print("assist", g.boss.name, g.boss.hp, flush=True)
            keys = bot.menus(g)
            if keys is None and g.state == G.PLAY and g.player:
                keys = bot.play(g)
            emu_state.buttons.clear()
            if keys:
                emu_state.buttons.update(keys)
            g.frame()
            if trace is not None and g.state == G.PLAY and g.player:
                p = g.player
                trace.write("%d %s %.0f %.0f %d %d %s %s\n" % (
                    g.t, g.room.id, p.x, p.y, int(p.ground), int("B" in (keys or ())),
                    bot.goal()[0], bot.goal()[1] if len(bot.goal()) > 1 else "-"))
            if record:
                pwm = g.audio.pwm
                freq, duty = pwm.freq(), pwm.duty_u16()
                amp = 0.0 if duty <= 0 or freq < 20 else 0.55 * min(duty, 32768) / 32768
                for n in range(SAMPLES):
                    sample_t = (g.t * SAMPLES + n) * freq
                    audio.append(int(amp * 32767) if amp and (sample_t % RATE) < RATE // 2 else int(-amp * 32767) if amp else 0)
                im = display.image
                bl = emu_state.backlight
                if bl < 0.98:
                    im = im.point(lambda v, k=bl: int(v * k))
                im = im.resize((W, H), 0)
                proc.stdin.write(im.tobytes())
            if g.t % 500 == 0:
                where = g.room.id if g.room else "-"
                pos = "(%.0f,%.0f)" % (g.player.x, g.player.y) if g.player else "-"
                boss = type(g.boss).__name__ if getattr(g, "boss", None) else "-"
                print("t", g.t, "state", g.state, "room", where, "at", pos, "boss", boss,
                      "goal", bot.goal(), "stuck", bot.stuck, "dbg", getattr(bot, "dbg", None), flush=True)
        print("finished", bot.done, "frame", g.t, "state", g.state, "goal", bot.goal())
    finally:
        if trace:
            trace.close()
        if proc:
            proc.stdin.close()
            proc.wait()
        G.hw.restore_clocks()
    if not record:
        print("dry run, no video")
        return
    import wave
    with wave.open(str(wav), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(audio.tobytes())
    mux = subprocess.run(
        [ffmpeg, "-y", "-i", str(video), "-i", str(wav), "-c:v", "copy", "-c:a", "aac",
         "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(OUT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if mux.returncode != 0:
        sys.stderr.write(mux.stderr.decode()[-2000:])
        sys.exit(1)
    video.unlink()
    wav.unlink()
    print("wrote", OUT, "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
