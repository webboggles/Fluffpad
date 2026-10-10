"""Physics reachability solver: drives the real Player class with input macros across all rooms,
per ability stage, to prove gating, item reachability and absence of soft-locks."""
import os
import sys
import types
from collections import deque
from multiprocessing import Pool, cpu_count

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
mp = types.ModuleType("micropython")
mp.const = lambda x: x
sys.modules["micropython"] = mp

from jade_sun import world_data as wd  # noqa: E402
from jade_sun.world import Room, T_RAIN, T_GATE, T_SEAL, T_CRACK, COLS, ROWS  # noqa: E402
from jade_sun.player import Player, PW, PH  # noqa: E402

U, D, L, R, DASH, JUMP = 1, 2, 4, 8, 16, 32
ONE_WAY = {"E2"}  # final arena: the fight ends the game, death respawns at a shrine

STAGES = [
    ("blade", {"blade"}),
    ("pearl", {"blade", "pearl"}),
    ("dash", {"blade", "pearl", "dash"}),
    ("feather", {"blade", "pearl", "dash", "feather"}),
    ("spear", {"blade", "pearl", "dash", "feather", "spear"}),
    ("gate", {"blade", "pearl", "dash", "feather", "spear", "gate"}),
]


def macros(abil):
    out = []
    for d in (L, R, 0):
        out.append([d] * 8)
        out.append([d] * 20)
        out.append([JUMP | d] * 22)
        out.append([JUMP | d] * 4)
        out.append([JUMP | d] * 10)
        out.append([D | JUMP, d])
        if "dash" in abil:
            out.append([DASH | d] + [d] * 8)
            for k in (5, 9, 13):
                out.append([JUMP | d] * k + [JUMP | d | DASH] + [JUMP | d] * 10)
        if "feather" in abil:
            for k in (8, 13, 18):
                out.append([JUMP | d] * (k - 1) + [d] + [JUMP | d] * 18)
            if "dash" in abil:
                out.append([JUMP | d] * 11 + [d] + [JUMP | d] * 8 + [JUMP | d | DASH] + [JUMP | d] * 10)
        sw = []
        for i in range(16):
            sw += [JUMP | d] + [d] * 5
        out.append(sw)
        out.append(([JUMP | d] + [d] * 5) * 4)
    return out


class World:
    def __init__(self, abil):
        self.abil = abil
        self.rooms = {}

    def room(self, rid):
        r = self.rooms.get(rid)
        if r is None:
            r = Room(rid)
            if "pearl" in self.abil:
                r.open_tiles(T_RAIN)
            if "gate" in self.abil:
                r.open_tiles(T_GATE)
            if "spear" in self.abil:
                r.open_tiles(T_SEAL)
            self.rooms[rid] = r
        return r

    def break_at(self, room, c, r):
        st = [(c, r)]
        while st:
            cc, rr = st.pop()
            if 0 <= cc < COLS and 0 <= rr < ROWS and room.t[rr * COLS + cc] == T_CRACK:
                room.t[rr * COLS + cc] = room.open_as[rr * COLS + cc]
                st += [(cc + 1, rr), (cc - 1, rr), (cc, rr + 1), (cc, rr - 1)]


def simulate(world, rid, x, y, inputs, touched):
    has = world.abil.__contains__
    room = world.room(rid)
    p = Player(x, y)
    p.update(0, 0, 0, room, has)
    p.events = []
    prev = 0
    hold_d = inputs[-1] & (L | R) if inputs else 0
    n = len(inputs) + 90
    rest = 0
    for f in range(n):
        held = inputs[f] if f < len(inputs) else hold_d
        pressed = held & ~prev
        released = prev & ~held
        prev = held
        p.update(held, pressed, released, room, has)
        for ev in p.events:
            if ev == "spike":
                return None
            if isinstance(ev, tuple) and ev[0] == "break":
                world.break_at(room, ev[1], ev[2])
        p.events = []
        cx, cy = p.cx, p.cy
        if cx < 0 and room.nb_w:
            rid = room.nb_w
            p.x += 320
        elif cx >= 320 and room.nb_e:
            rid = room.nb_e
            p.x -= 320
        elif cy < 0 and room.nb_n:
            rid = room.nb_n
            p.y += 224
            p.vy = min(p.vy, -9.0)
        elif cy >= 224 and room.nb_s:
            rid = room.nb_s
            p.y -= 224
        else:
            p.x = max(-PW / 2 + 1 if room.nb_w else 0, min(p.x, 320 - (PW / 2 + 1 if room.nb_e else PW)))
        room = world.room(rid)
        touched.add((rid, int(p.cx) >> 3, int(p.cy) >> 3))
        if f >= len(inputs) and p.ground:
            rest += 1
            if rest > 1:
                return (rid, round(p.x / 3) * 3, round(p.y))
        else:
            rest = 0
    return None


def bfs(stage):
    name, abil = stage
    world = World(abil)
    ms = macros(abil)
    sx, sy = wd.START_POS
    start = simulate(world, wd.START_ROOM, sx, sy, [], set())
    seen = {start: 0}
    edges = {}
    q = deque([start])
    touched = set()
    while q and len(seen) < 20000:
        s = q.popleft()
        rid, x, y = s
        out = set()
        for m in ms:
            r = simulate(world, rid, x, y, m, touched)
            if r and r != s:
                out.add(r)
                if r not in seen:
                    seen[r] = 1
                    q.append(r)
        edges[s] = out
    rev = {}
    for a, outs in edges.items():
        for b in outs:
            rev.setdefault(b, set()).add(a)
    back = {start}
    q = deque([start])
    while q:
        s = q.popleft()
        for a in rev.get(s, ()):
            if a not in back:
                back.add(a)
                q.append(a)
    traps = [s for s in seen if s not in back and s[0] not in ONE_WAY]
    rooms = sorted({s[0] for s in seen})
    return name, rooms, touched, traps, len(seen)


def item_spots():
    spots = {}
    for rid, r in wd.ROOMS.items():
        ids = {"i": list(r.get("items", ())), "N": list(r.get("npcs", ())), "L": list(r.get("lore", ()))}
        for row, line in enumerate(r["map"]):
            for col, ch in enumerate(line):
                if ch in ids and ids[ch]:
                    spots[ids[ch].pop(0)] = (rid, col * 16 + 8, row * 16 + 8)
    return spots


def near(touched, rid, x, y, rad=14):
    for dx in range(-rad, rad + 1, 4):
        for dy in range(-rad, rad + 1, 4):
            if (rid, int(x + dx) >> 3, int(y + dy) >> 3) in touched:
                return True
    return False


EXPECT = {
    "blade": ({"A0", "A1", "A2", "A3", "B1", "B2"}, ["ceiba", "chaac", "l1", "l2", "l3"]),
    "pearl": ({"B3", "B4", "B5", "C1", "C3", "C4"}, ["balam", "heart2", "l4"]),
    "dash": ({"C2", "D1", "D2"}, ["feather", "heart1", "l5"]),
    "feather": ({"D3", "D4"}, ["witz", "heart4"]),
    "spear": (set(), ["heart3"]),
    "gate": ({"E1", "E2"}, ["l6"]),
}
FORBID = {
    "blade": {"B3", "B4", "B5", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4", "E1", "E2"},
    "pearl": {"C2", "D1", "D2", "D3", "D4", "E1", "E2"},
    "dash": {"D3", "D4", "E1", "E2"},
    "feather": {"E1", "E2"},
    "spear": {"E1", "E2"},
    "gate": set(),
}
FORBID_ITEMS = {"blade": ["heart1", "heart2", "heart3", "heart4", "feather"],
                "pearl": ["heart1", "heart3", "heart4", "feather"],
                "dash": ["heart3", "heart4"], "feather": ["heart3"]}

if __name__ == "__main__":
    spots = item_spots()
    with Pool(min(len(STAGES), cpu_count())) as pool:
        results = pool.map(bfs, STAGES)
    ok = True
    for name, rooms, touched, traps, n in results:
        need_rooms, need_items = EXPECT[name]
        missing = need_rooms - set(rooms)
        bad = FORBID[name] & set(rooms)
        miss_items = [i for i in need_items if not near(touched, *spots[i])]
        leak_items = [i for i in FORBID_ITEMS.get(name, []) if near(touched, *spots[i])]
        trap_rooms = sorted({t[0] for t in traps})
        print(f"[{name}] states={n} rooms={','.join(rooms)}")
        for label, val in (("missing rooms", missing), ("forbidden rooms", bad), ("unreached", miss_items),
                           ("leaked items", leak_items), ("soft-lock rooms", trap_rooms)):
            if val:
                ok = False
                print(f"   !! {label}: {sorted(val) if isinstance(val, set) else val}")
        if traps:
            print("      trap samples:", traps[:6])
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
