"""Physics reachability solver: drives the real Player class with input macros across the rooms,
per ability stage, to prove gating, find reachability and absence of soft-locks.

Expectations come from the data: a room's "stage" and world_data.FINDS say the first stage at
which it must be reachable, and it must not be reachable at any earlier stage.

  .venv/bin/python games/jade_sun/tools/solve_world.py                 whole world from the start,
                                       also writes out/room_graph.json for the playthrough bot
  .venv/bin/python games/jade_sun/tools/solve_world.py --zone cenote   one zone from its ENTRY list;
                                       stepping into another zone counts as a safe exit
"""
import argparse
import json
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
from jade_sun.player import Player, PW  # noqa: E402

U, D, L, R, DASH, JUMP = 1, 2, 4, 8, 16, 32
ONE_WAY = {rid for rid, r in wd.ROOMS.items() if r.get("boss") == "camazotz"}  # the fight ends the game
ABIL = {"blade": {"blade"}, "pearl": {"pearl"}, "dash": {"dash"}, "feather": {"feather"},
        "spear": {"spear"}, "gate": {"gate"}}
MAX_STATES = 150000
GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "room_graph.json")


def stage_abil(name):
    out = set()
    for s in wd.STAGES:
        out |= ABIL[s]
        if s == name:
            return out
    raise KeyError(name)


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


def simulate(world, rid, x, y, inputs, touched, scope=None, links=None):
    """Play inputs then settle. Returns a resting state, ("exit", rid) on leaving scope, or None.
    Room crossings of a run that ends safely are added to links."""
    has = world.abil.__contains__
    crossed = []
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
        was = rid
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
        if rid != was:
            crossed.append((was, rid))
        if scope is not None and rid not in scope:
            return ("exit", rid)
        room = world.room(rid)
        touched.add((rid, int(p.cx) >> 3, int(p.cy) >> 3))
        if f >= len(inputs) and p.ground:
            rest += 1
            if rest > 1:
                if links is not None:
                    links.update(crossed)
                return (rid, round(p.x / 3) * 3, round(p.y))
        else:
            rest = 0
    return None


def bfs(job):
    name, entries, scope = job
    abil = stage_abil(name)
    world = World(abil)
    ms = macros(abil)
    touched = set()
    starts = []
    for rid, x, y in entries:
        s = simulate(world, rid, x, y, [], touched, scope)
        if s and s[0] != "exit":
            starts.append(s)
    seen = set(starts)
    edges = {}
    links = set()
    exits = set()
    safe = set()
    q = deque(starts)
    while q and len(seen) < MAX_STATES:
        s = q.popleft()
        rid, x, y = s
        out = set()
        for m in ms:
            r = simulate(world, rid, x, y, m, touched, scope, links)
            if not r or r == s:
                continue
            if r[0] == "exit":
                exits.add(r[1])
                safe.add(s)
                continue
            out.add(r)
            if r not in seen:
                seen.add(r)
                q.append(r)
        edges[s] = out
    rev = {}
    for a, outs in edges.items():
        for b in outs:
            rev.setdefault(b, set()).add(a)
    back = set(starts) | safe
    q = deque(back)
    while q:
        s = q.popleft()
        for a in rev.get(s, ()):
            if a not in back:
                back.add(a)
                q.append(a)
    traps = [s for s in seen if s not in back and s[0] not in ONE_WAY]
    rooms = sorted({s[0] for s in seen} | {t[0] for t in touched})
    capped = len(seen) >= MAX_STATES
    return name, rooms, touched, traps, len(seen), sorted(exits), capped, sorted(links)


def find_spots():
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", default="", help="solve one zone from its ENTRY list")
    ap.add_argument("--stages", default="", help="comma list of stages to run")
    a = ap.parse_args()
    idx = {s: i for i, s in enumerate(wd.STAGES)}
    if a.zone:
        mod = wd.ZONE_FILES[a.zone]
        scope = set(mod.ROOMS)
        entries = mod.ENTRY
        first = min(idx[e[3]] for e in entries)
        stages = wd.STAGES[first:]
        jobs = [(s, [(e[0], e[1], e[2]) for e in entries if idx[e[3]] <= idx[s]], scope) for s in stages]
    else:
        scope = None
        stages = wd.STAGES
        jobs = [(s, [(wd.START_ROOM,) + tuple(wd.START_POS)], None) for s in stages]
    if a.stages:
        keep = set(a.stages.split(","))
        jobs = [j for j in jobs if j[0] in keep]
    rooms_in = set(scope) if scope else set(wd.ROOMS)
    finds_in = {f: s for f, s in wd.FINDS.items()}
    spots = find_spots()
    finds_in = {f: s for f, s in finds_in.items() if f in spots and spots[f][0] in rooms_in}
    with Pool(min(len(jobs), cpu_count())) as pool:
        results = pool.map(bfs, jobs)
    ok = True
    if not a.zone and not a.stages:
        os.makedirs(os.path.dirname(GRAPH), exist_ok=True)
        with open(GRAPH, "w") as f:
            json.dump({r[0]: r[7] for r in results}, f, indent=0)
    for name, rooms, touched, traps, n, exits, capped, _links in results:
        si = idx[name]
        reached = set(rooms) & rooms_in
        need = {r for r in rooms_in if idx[wd.ROOMS[r]["stage"]] <= si}
        missing = need - reached
        early = reached - need
        miss_f = sorted(f for f, s in finds_in.items() if idx[s] <= si and not near(touched, *spots[f]))
        leak_f = sorted(f for f, s in finds_in.items() if idx[s] > si and near(touched, *spots[f]))
        trap_rooms = sorted({t[0] for t in traps})
        early_exits = sorted(x for x in exits if idx[wd.ROOMS[x]["stage"]] > si)
        print("[%s] states=%d rooms=%s%s" % (name, n, ",".join(sorted(reached)), "  (STATE CAP HIT)" if capped else ""))
        if exits:
            print("      exits to: %s" % ",".join(exits))
        for label, val in (("missing rooms", missing), ("rooms reachable too early", early),
                           ("exits into rooms of a later stage", early_exits),
                           ("unreached finds", miss_f), ("finds reachable too early", leak_f),
                           ("soft-lock rooms", trap_rooms)):
            if val:
                ok = False
                print("   !! %s: %s" % (label, sorted(val)))
        if traps:
            print("      trap samples (room, x, y):", traps[:6])
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
