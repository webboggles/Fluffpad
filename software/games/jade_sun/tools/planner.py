"""Physics route planner for the playthrough bot.

Best-first search over input macros, driving clones of the live Player against a copy
of the live room, so the plan replays frame for frame in the real game.
"""
import copy
import heapq

from jade_sun.player import PW

U, D, L, R, DASH, JUMP = 1, 2, 4, 8, 16, 32
KEY_NAMES = ((U, "U"), (D, "D"), (L, "L"), (R, "R"), (DASH, "A"), (JUMP, "B"))
SETTLE_MAX = 70


def macros(has):
    out = []
    for d in (L, R, 0):
        if d:
            out.append([d] * 6)
            out.append([d] * 16)
        out.append([JUMP | d] * 22)
        out.append([JUMP | d] * 10)
        out.append([JUMP | d] * 5)
        out.append([JUMP] * 12 + [JUMP | d] * 10)
        out.append([D | JUMP] + [d] * 4)
        if has("dash"):
            out.append([DASH | d] + [d] * 8)
            out.append([JUMP | d] * 9 + [JUMP | d | DASH] + [JUMP | d] * 10)
        if has("feather"):
            for k in (8, 13, 18):
                out.append([JUMP | d] * (k - 1) + [d] + [JUMP | d] * 20)
            out.append([JUMP] * 12 + [0] + [JUMP | d] * 20)
            if has("dash"):
                out.append([JUMP | d] * 11 + [d] + [JUMP | d] * 8 + [JUMP | d | DASH] + [JUMP | d] * 10)
    return out


def clone(p):
    q = copy.copy(p)
    q.events = []
    q.trail = []
    return q


def keys_of(bits):
    return {name for bit, name in KEY_NAMES if bits & bit}


def _break(room, c, r, crack):
    stack = [(c, r)]
    cols = 20
    while stack:
        cc, rr = stack.pop()
        if 0 <= cc < cols and 0 <= rr < 14 and room.t[rr * cols + cc] == crack:
            room.t[rr * cols + cc] = room.open_as[rr * cols + cc]
            stack += [(cc + 1, rr), (cc - 1, rr), (cc, rr + 1), (cc, rr - 1)]


def _edge(room, p):
    """Room the player would leave into this frame, or None."""
    cx, cy = p.cx, p.cy
    if cx < 0 and room.nb_w:
        return room.nb_w
    if cx >= 320 and room.nb_e:
        return room.nb_e
    if cy < 0 and room.nb_n:
        return room.nb_n
    if cy >= 224 and room.nb_s:
        return room.nb_s
    p.x = max(-PW / 2 + 1 if room.nb_w else 0, min(p.x, 320 - (PW / 2 + 1 if room.nb_e else PW)))
    return None


def settled(p):
    """Standing well inside a room, the same test the bot uses for arriving."""
    return p.ground and 24 < p.cx < 296 and 20 < p.cy < 200


def _cross(p, room, nxt):
    """Move the player into the neighbour room exactly as Game._edges does."""
    if nxt == room.nb_w:
        p.x += 320
    elif nxt == room.nb_e:
        p.x -= 320
    elif nxt == room.nb_n:
        p.y += 224
        p.vy = min(p.vy, -9.0)
    else:
        p.y -= 224


def run(p, room, inputs, has, prev, done, crack, target_room=None, landing=None):
    """Play a macro then let the player settle. Returns (player, frames, prev, status).

    With a landing room, entering target_room carries on until the player stands inside it."""
    p = clone(p)
    frames = []
    track = []
    rest = 0
    crossed = False
    n = len(inputs) + SETTLE_MAX
    for f in range(n):
        held = inputs[f] if f < len(inputs) else 0
        pressed = held & ~prev
        released = prev & ~held
        prev = held
        p.update(held, pressed, released, room, has)
        for ev in p.events:
            if ev == "spike":
                return None
            if isinstance(ev, tuple) and ev[0] == "break":
                _break(room, ev[1], ev[2], crack)
        p.events = []
        nxt = _edge(room, p)
        if nxt is not None and not crossed and nxt == target_room and landing is not None:
            _cross(p, room, nxt)
            room = landing
            crossed = True
            nxt = None
        frames.append(held)
        track.append((p.x, p.y))
        if nxt is not None:
            return p, (frames, track), prev, ("room", nxt)
        if crossed:
            if settled(p):
                return p, (frames, track), prev, ("goal", None)
            continue
        if done(p, None):
            return p, (frames, track), prev, ("goal", None)
        if f >= len(inputs):
            if p.ground and abs(p.vx) < 0.05:
                rest += 1
                if rest > 1:
                    return p, (frames, track), prev, ("rest", None)
            else:
                rest = 0
    return None


def plan(player, room, has, target_room, target_xy, crack, prev0=0, budget=400, landing=None, settle=False):
    """(held bits per frame, expected (x, y) per frame) into target_room or onto target_xy.

    landing is a copy of target_room; with it the plan ends standing inside that room.
    settle plans to any standing spot inside the current room."""
    room = copy.deepcopy(room)
    if landing is not None:
        landing = copy.deepcopy(landing)
    ms = macros(has)
    tx, ty = target_xy

    def done(p, _):
        if settle:
            return settled(p)
        if target_room is not None:
            return False
        return abs(p.cx - tx) < 10 and abs(p.y - ty) < 18

    def h(p):
        return abs(p.cx - tx) + abs(p.y - ty) * 1.4

    start = clone(player)
    seen = {(round(start.x / 3), round(start.y / 2))}
    heap = [(h(start), 0, 0, start, ([], []), prev0)]
    tick = 1
    while heap and budget > 0:
        _, cost, _, p, (path, track), prev = heapq.heappop(heap)
        budget -= 1
        for m in ms:
            res = run(p, room, m, has, prev, done, crack, target_room, landing)
            if res is None:
                continue
            q, (frames, steps), nprev, (status, arg) = res
            if status == "room":
                if arg == target_room:
                    return path + frames, track + steps
                continue
            if status == "goal":
                return path + frames, track + steps
            k = (round(q.x / 3), round(q.y / 2))
            if k in seen:
                continue
            seen.add(k)
            ncost = cost + len(frames)
            heapq.heappush(heap, (h(q) + ncost * 0.15, ncost, tick, q, (path + frames, track + steps), nprev))
            tick += 1
    return None
