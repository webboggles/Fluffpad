"""Soak-test jade_sun.Game on the desktop Pico emulator.

Creates one Game per worker, warps into every room with several seeds and
ability sets, and drives semi-random sticky input through emu_state.buttons.

  .venv/bin/python games/jade_sun/tools/fuzz.py   (from software/)

Prints a JSON report on stdout and writes tools/out/fuzz_report.json.
"""

import json
import os
import random
import sys
import tempfile
import time
import traceback
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
EMU_DIR = PROJECT_DIR.parents[1] / "emulator"
MOCKS_DIR = EMU_DIR / "mocks"
OUT_PATH = TOOLS_DIR / "out" / "fuzz_report.json"

SEEDS = (1, 8, 21, 55)
FRAMES = 400
STUCK_LIMIT = 600
OOB_LIMIT = 5

SETS = (
    ("blade", ("blade",)),
    ("pearl", ("blade", "pearl")),
    ("dash", ("blade", "pearl", "dash")),
    ("abilities", ("blade", "pearl", "dash", "feather", "spear")),
    ("glyphs", ("blade", "pearl", "dash", "feather", "spear",
                "g_water", "g_jaguar", "g_sky", "g_stone")),
)

FLOOR = set("#%=")
SOLIDISH = set("#%SRG^")
PH = 14


def _boot_path():
    for entry in (str(EMU_DIR), str(PROJECT_DIR), str(MOCKS_DIR)):
        while entry in sys.path:
            sys.path.remove(entry)
    sys.path.insert(0, str(EMU_DIR))
    sys.path.insert(0, str(PROJECT_DIR))
    sys.path.insert(0, str(MOCKS_DIR))


def _patch_runtime():
    import gc
    import time as time_mod
    import emu_state

    def sleep(seconds):
        emu_state.virtual_us += int(float(seconds) * 1_000_000)

    def sleep_ms(ms):
        emu_state.virtual_us += int(float(ms) * 1000)

    def sleep_us(us):
        emu_state.virtual_us += int(us)

    time_mod.sleep = sleep
    time_mod.sleep_ms = sleep_ms
    time_mod.sleep_us = sleep_us
    time_mod.ticks_us = lambda: emu_state.virtual_us
    time_mod.ticks_ms = lambda: emu_state.virtual_us // 1000
    time_mod.ticks_cpu = lambda: emu_state.virtual_us
    time_mod.ticks_diff = lambda a, b: a - b
    time_mod.ticks_add = lambda a, b: a + b
    time_mod.time = lambda: emu_state.virtual_us / 1_000_000
    gc.mem_free = lambda: 8_000_000
    gc.mem_alloc = lambda: 500_000
    emu_state.reset()
    emu_state.on_frame = None
    emu_state.log_tone = lambda *args, **kwargs: None
    return emu_state


def spawn_for(rows):
    """Empty tile standing on solid ground, else any open interior tile."""
    height = len(rows)
    width = len(rows[0])
    best = None
    best_score = 10 ** 9
    for r in range(height - 1):
        line = rows[r]
        below = rows[r + 1]
        for c in range(min(len(line), len(below))):
            if line[c] != "." or below[c] not in FLOOR:
                continue
            score = abs(c - width // 2) * 2 + abs(r - (height - 4))
            if c == 0 or c == width - 1:
                score += 30
            if score < best_score:
                best_score = score
                best = (c * 16 + 3, (r + 1) * 16 - PH)
    if best is not None:
        return best
    for r in range(1, height - 1):
        line = rows[r]
        for c in range(1, min(len(line), width) - 1):
            if line[c] not in SOLIDISH:
                return (c * 16 + 3, r * 16 + 1)
    return (48, 160)


def _jobs():
    _boot_path()
    from jade_sun.world_data import ROOMS
    order = list(ROOMS)
    jobs = []
    for seed in SEEDS:
        for name, items in SETS:
            for rid in order:
                x, y = spawn_for(ROOMS[rid]["map"])
                jobs.append({
                    "kind": "room",
                    "seed": seed,
                    "set": name,
                    "items": list(items),
                    "room": rid,
                    "x": x,
                    "y": y,
                })
    jobs.append({
        "kind": "new",
        "seed": 1,
        "set": "new",
        "items": [],
        "room": "TITLE",
        "x": 0,
        "y": 0,
    })
    jobs.append({
        "kind": "probe",
        "seed": 1,
        "set": "probe",
        "items": [],
        "room": "PROBE",
        "x": 0,
        "y": 0,
    })
    return jobs


class Sticky:
    """Hold a direction, tap actions, and pulse confirm while a menu is up."""

    def __init__(self, rng):
        self.rng = rng
        self.direction = "R"
        self.dir_left = rng.randint(10, 40)
        self.charge = 0
        self.tap_cool = False
        self.menu_down = False

    def buttons(self, state):
        if state in ("DIALOG", "ITEM", "FORM", "ENDING", "TITLE", "PROLOGUE", "INTRO"):
            return self._pulse("B")
        if state == "SHOP":
            return self._pulse("A")
        if state == "MAP":
            return self._pulse("B")
        if state == "DEATH":
            return set()
        held = set()
        if self.charge > 0:
            held.add("X")
            self.charge -= 1
        elif self.rng.randrange(55) == 0:
            self.charge = 25
            held.add("X")
        if self.dir_left <= 0:
            self.direction = self.rng.choice(("L", "R", "L", "R", "D", None))
            self.dir_left = self.rng.randint(10, 40)
        self.dir_left -= 1
        if self.direction:
            held.add(self.direction)
        if self.tap_cool:
            self.tap_cool = False
        elif self.rng.randrange(14) == 0:
            held.add(self.rng.choice(("B", "Y", "A", "X")))
            self.tap_cool = True
        if self.rng.randrange(28) == 0:
            held.add("U")
        if self.rng.randrange(90) == 0:
            held.add("+")
        return held

    def _pulse(self, name):
        self.menu_down = not self.menu_down
        if self.menu_down:
            return {name}
        return set()


def _state_name(game, names):
    return names.get(game.state, str(game.state))


def _player_xy(game):
    player = game.player
    if player is None:
        return None
    try:
        return (float(player.x), float(player.y))
    except Exception:
        return None


def _oob_axes(x, y):
    axes = []
    if x < -20:
        axes.append("x<-20")
    if x > 340:
        axes.append("x>340")
    if y < -30:
        axes.append("y<-30")
    if y > 260:
        axes.append("y>260")
    return axes


def _failure(job, kind, frame, game, names, error, trace, extra=None):
    room = job["room"]
    if game is not None and getattr(game, "room", None) is not None:
        room = game.room.id
    state = _state_name(game, names) if game is not None else ""
    xy = _player_xy(game) if game is not None else None
    hp = None
    if game is not None:
        try:
            hp = game.hp
        except Exception:
            hp = None
    row = {
        "kind": kind,
        "seed": job["seed"],
        "set": job["set"],
        "items": list(job["items"]),
        "start_room": job["room"],
        "room": room,
        "state": state,
        "frame": frame,
        "xy": xy,
        "hp": hp,
        "error": error,
        "trace": trace,
    }
    if extra:
        row.update(extra)
    return row


def _step(emu_state, game, buttons):
    emu_state.buttons.clear()
    emu_state.buttons.update(buttons)
    game.frame()


def _watch(job, game, names, frame, oob_run, menu_run):
    """Return (failure or None, oob_run, menu_run)."""
    state = _state_name(game, names)
    if state in ("DIALOG", "ITEM"):
        menu_run += 1
        if menu_run > STUCK_LIMIT:
            return _failure(
                job, "stuck", frame, game, names,
                "stuck in %s for %s frames" % (state, menu_run),
                "",
                {"menu_frames": menu_run},
            ), oob_run, menu_run
    else:
        menu_run = 0
    try:
        hp = game.hp
    except Exception:
        hp = 0
    if hp < 0:
        return _failure(
            job, "hp", frame, game, names,
            "hp %s" % hp, "", {"hp": hp},
        ), oob_run, menu_run
    xy = _player_xy(game)
    if xy is not None and state == "PLAY":
        axes = _oob_axes(xy[0], xy[1])
        if axes:
            oob_run += 1
            if oob_run > OOB_LIMIT:
                return _failure(
                    job, "oob", frame, game, names,
                    "out of bounds %s at (%.1f, %.1f) for %s frames" % (
                        ",".join(axes), xy[0], xy[1], oob_run),
                    "",
                    {"axes": axes, "oob_frames": oob_run},
                ), oob_run, menu_run
        else:
            oob_run = 0
    else:
        oob_run = 0
    return None, oob_run, menu_run


def _run_room(emu_state, game, names, job, sticky):
    frames = 0
    oob_run = 0
    menu_run = 0
    random.seed(job["seed"])
    game.new_game()
    game.items = set(job["items"])
    game.hp = game.max_hp
    game._start_play(job["room"], job["x"], job["y"])
    while frames < FRAMES or (0 < menu_run <= STUCK_LIMIT):
        state = _state_name(game, names)
        try:
            _step(emu_state, game, sticky.buttons(state))
        except Exception:
            frames += 1
            return frames, _failure(
                job, "exception", frames, game, names,
                traceback.format_exc().strip().splitlines()[-1],
                traceback.format_exc(),
            )
        frames += 1
        fail, oob_run, menu_run = _watch(job, game, names, frames, oob_run, menu_run)
        if fail is not None:
            return frames, fail
    return frames, None


def _run_new(emu_state, game, names, job):
    frames = 0
    oob_run = 0
    menu_run = 0
    rng = random.Random(job["seed"])
    random.seed(job["seed"])
    sticky = Sticky(rng)

    def go(buttons):
        nonlocal frames, oob_run, menu_run
        try:
            _step(emu_state, game, buttons)
        except Exception:
            frames += 1
            return _failure(
                job, "exception", frames, game, names,
                traceback.format_exc().strip().splitlines()[-1],
                traceback.format_exc(),
            )
        frames += 1
        fail, oob_run, menu_run = _watch(job, game, names, frames, oob_run, menu_run)
        return fail

    guard = 0
    while _state_name(game, names) == "INTRO" and guard < 40:
        intro = game.intro
        tick = intro.t if intro is not None else 99
        fail = go({"B"} if tick > 8 and guard % 2 == 0 else set())
        if fail:
            return frames, fail
        guard += 1
    guard = 0
    while _state_name(game, names) == "TITLE" and guard < 6:
        fail = go({"B"} if guard % 2 else set())
        if fail:
            return frames, fail
        guard += 1
    guard = 0
    while _state_name(game, names) == "PROLOGUE" and guard < 6:
        fail = go({"+"} if guard % 2 == 0 else set())
        if fail:
            return frames, fail
        guard += 1
    guard = 0
    while _state_name(game, names) == "FORM" and guard < 500:
        if game.state_t > 120:
            fail = go({"B"} if guard % 2 == 0 else set())
        else:
            fail = go(set())
        if fail:
            return frames, fail
        guard += 1
    played = 0
    while played < FRAMES:
        state = _state_name(game, names)
        if state == "INTRO":
            buttons = {"B"} if played % 2 == 0 else set()
        elif state == "TITLE":
            buttons = {"B"} if played % 2 == 0 else set()
        elif state == "PROLOGUE":
            buttons = {"+"} if played % 2 == 0 else set()
        elif state == "FORM":
            buttons = {"B"} if game.state_t > 120 and played % 2 == 0 else set()
        else:
            buttons = sticky.buttons(state)
        fail = go(buttons)
        if fail:
            return frames, fail
        played += 1
        if menu_run > STUCK_LIMIT:
            break
    return frames, None


def _drain(emu_state, game, names, job, limit, shop=False):
    """Pulse confirm until PLAY, or until limit. Returns (frames, failure or None)."""
    frames = 0
    oob_run = 0
    menu_run = 0
    buys = 0
    while frames < limit:
        state = _state_name(game, names)
        if state in ("PLAY", "TITLE") and not getattr(game, "dialog", None):
            return frames, None
        if state == "ENDING" and frames > 40 and game.page >= 5 and game.state_t > 60:
            return frames, None
        if shop and state == "SHOP":
            if buys < 3:
                buttons = {"B"} if frames % 2 == 0 else set()
                if frames % 2 == 0:
                    buys += 1
            else:
                buttons = {"A"} if frames % 2 == 0 else set()
        elif state in ("DIALOG", "ITEM", "MAP", "ENDING", "DEATH"):
            buttons = {"B"} if frames % 2 == 0 else set()
        else:
            buttons = set()
        try:
            _step(emu_state, game, buttons)
        except Exception:
            frames += 1
            return frames, _failure(
                job, "exception", frames, game, names,
                traceback.format_exc().strip().splitlines()[-1],
                traceback.format_exc(),
                {"probe": job.get("probe")},
            )
        frames += 1
        fail, oob_run, menu_run = _watch(job, game, names, frames, oob_run, menu_run)
        if fail is not None:
            fail["probe"] = job.get("probe")
            return frames, fail
    state = _state_name(game, names)
    if state in ("DIALOG", "ITEM"):
        return frames, _failure(
            job, "stuck", frames, game, names,
            "probe stuck in %s" % state, "", {"probe": job.get("probe")},
        )
    return frames, None


def _run_probe(emu_state, game, names, job):
    """Full intro, every dialogue, shop, boss defeat, beam seal, death."""
    from jade_sun import combat, story
    from jade_sun.world_data import ROOMS

    frames = 0
    failures = []

    def note(n, fail):
        nonlocal frames
        frames += n
        if fail is not None:
            failures.append(fail)

    def burst(buttons, n):
        count = 0
        for _ in range(n):
            try:
                _step(emu_state, game, buttons)
            except Exception:
                count += 1
                return count, _failure(
                    job, "exception", frames + count, game, names,
                    traceback.format_exc().strip().splitlines()[-1],
                    traceback.format_exc(),
                    {"probe": job.get("probe")},
                )
            count += 1
        return count, None

    job["probe"] = "intro"
    guard = 0
    while _state_name(game, names) == "INTRO" and guard < 360:
        n, fail = burst(set(), 1)
        note(n, fail)
        if fail:
            return frames, failures
        guard += 1

    job["probe"] = "dialogues"
    for key in story.DIALOGUE:
        job["probe"] = "talk:" + key
        try:
            random.seed(1)
            game.new_game()
            game.cacao = 500
            game._start_play("A1", 100, 178)
            game.talk(key)
        except Exception:
            failures.append(_failure(
                job, "exception", frames, game, names,
                traceback.format_exc().strip().splitlines()[-1],
                traceback.format_exc(),
                {"probe": job["probe"]},
            ))
            return frames, failures
        n, fail = _drain(emu_state, game, names, job, 800, shop=(key == "ek"))
        note(n, fail)
        if fail and fail["kind"] == "exception":
            return frames, failures

    job["probe"] = "bosses"
    for rid, meta in ROOMS.items():
        if not meta.get("boss") and not meta.get("watcher"):
            continue
        job["probe"] = "boss:" + rid
        job["room"] = rid
        try:
            random.seed(3)
            game.new_game()
            game.items = set(("blade", "pearl", "dash", "feather", "spear",
                               "g_water", "g_jaguar", "g_sky", "g_stone"))
            game.hp = game.max_hp
            x, y = spawn_for(meta["map"])
            game._start_play(rid, x, y)
        except Exception:
            failures.append(_failure(
                job, "exception", frames, game, names,
                traceback.format_exc().strip().splitlines()[-1],
                traceback.format_exc(),
                {"probe": job["probe"]},
            ))
            return frames, failures
        for _ in range(80):
            if game.boss is not None:
                break
            dx = 150 - game.player.x
            buttons = set()
            if dx > 8:
                buttons.add("R")
            elif dx < -8:
                buttons.add("L")
            n, fail = burst(buttons, 1)
            note(n, fail)
            if fail:
                return frames, failures
            if game.boss is not None:
                break
        if game.boss is not None:
            game.player.iframes = 9999
            game.boss.hp = 1
            try:
                combat.hit_boss(game, game.boss, 5, game.player.cx, True)
            except Exception:
                failures.append(_failure(
                    job, "exception", frames, game, names,
                    traceback.format_exc().strip().splitlines()[-1],
                    traceback.format_exc(),
                    {"probe": job["probe"]},
                ))
                return frames, failures
        n, fail = _drain(emu_state, game, names, job, 500)
        note(n, fail)
        if fail and fail["kind"] == "exception":
            return frames, failures
    job["probe"] = "seal"
    job["room"] = "C1"
    try:
        game.new_game()
        game.items = {"spear", "blade"}
        game._start_play("C1", 48, 48)
        game.player.face = 1
        n, fail = burst({"X"}, 25)
        note(n, fail)
        if not fail:
            n, fail = burst(set(), 40)
            note(n, fail)
    except Exception:
        failures.append(_failure(
            job, "exception", frames, game, names,
            traceback.format_exc().strip().splitlines()[-1],
            traceback.format_exc(),
            {"probe": "seal"},
        ))

    job["probe"] = "death"
    try:
        game.new_game()
        game._start_play("A1", 100, 178)
        game.hp = 1
        game.hurt_player(0, 5)
        n, fail = burst(set(), 90)
        note(n, fail)
    except Exception:
        failures.append(_failure(
            job, "exception", frames, game, names,
            traceback.format_exc().strip().splitlines()[-1],
            traceback.format_exc(),
            {"probe": "death"},
        ))

    job["probe"] = "level"
    try:
        game.new_game()
        game._start_play("A1", 100, 178)
        game.level = 9
        game.xp = 429
        combat.gain_xp(game, 20)
        n, fail = burst(set(), 5)
        note(n, fail)
    except Exception:
        failures.append(_failure(
            job, "exception", frames, game, names,
            traceback.format_exc().strip().splitlines()[-1],
            traceback.format_exc(),
            {"probe": "level"},
        ))
    return frames, failures


def _worker(jobs):
    os.chdir(tempfile.mkdtemp(prefix="jade_fuzz_"))
    emu_state = _patch_runtime()
    from jade_sun.game import (
        DEATH, DIALOG, ENDING, FORM, Game, ITEM, MAP, PLAY, PROLOGUE, SHOP, TITLE,
    )
    names = {
        TITLE: "TITLE", PROLOGUE: "PROLOGUE", FORM: "FORM", PLAY: "PLAY",
        DIALOG: "DIALOG", ITEM: "ITEM", MAP: "MAP", SHOP: "SHOP",
        DEATH: "DEATH", ENDING: "ENDING",
    }
    try:
        from jade_sun.game import INTRO
        names[INTRO] = "INTRO"
    except ImportError:
        pass
    failures = []
    frames = 0
    scenarios = 0
    game = None
    for job in jobs:
        scenarios += 1
        if game is None:
            try:
                game = Game()
            except Exception:
                failures.append(_failure(
                    job, "exception", 0, None, names,
                    traceback.format_exc().strip().splitlines()[-1],
                    traceback.format_exc(),
                ))
                continue
        rng = random.Random((job["seed"] << 16) ^ (scenarios * 997))
        sticky = Sticky(rng)
        try:
            if job["kind"] in ("new", "probe"):
                os.chdir(tempfile.mkdtemp(prefix="jade_fuzz_new_"))
                game = Game()
            if job["kind"] == "probe":
                n, found = _run_probe(emu_state, game, names, job)
                frames += n
                failures.extend(found)
                game = None
                continue
            if job["kind"] == "new":
                n, fail = _run_new(emu_state, game, names, job)
            else:
                n, fail = _run_room(emu_state, game, names, job, sticky)
        except Exception:
            n, fail = 0, _failure(
                job, "exception", 0, game, names,
                traceback.format_exc().strip().splitlines()[-1],
                traceback.format_exc(),
            )
        frames += n
        if fail is not None:
            failures.append(fail)
            game = None
    return {"failures": failures, "frames": frames, "scenarios": scenarios}


def _chunks(items, n):
    buckets = [[] for _ in range(n)]
    for i, item in enumerate(items):
        buckets[i % n].append(item)
    return [bucket for bucket in buckets if bucket]


def _signature(row):
    if row["kind"] == "exception":
        sites = []
        for line in row.get("trace", "").splitlines():
            text = line.strip()
            if text.startswith("File ") and "jade_sun" in text:
                sites.append(text)
        site = sites[-1] if sites else row.get("error", "")
        head = row.get("error", "").split(":", 1)[0]
        return ("exception", head, site)
    if row["kind"] == "oob":
        return ("oob", tuple(row.get("axes") or ()))
    if row["kind"] == "stuck":
        return ("stuck", row.get("state"))
    return (row["kind"], row.get("error"))


def main():
    started = time.time()
    jobs = _jobs()
    workers = os.cpu_count() or 1
    if workers > len(jobs):
        workers = len(jobs)
    parts = _chunks(jobs, workers)
    if workers == 1:
        results = [_worker(parts[0])]
    else:
        import multiprocessing
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(workers) as pool:
            results = pool.map(_worker, parts)
    failures = []
    frames = 0
    scenarios = 0
    for part in results:
        failures.extend(part["failures"])
        frames += part["frames"]
        scenarios += part["scenarios"]
    grouped = []
    seen = {}
    for row in failures:
        key = _signature(row)
        if key not in seen:
            seen[key] = len(grouped)
            grouped.append({"signature": list(key), "count": 0, "examples": []})
        bucket = grouped[seen[key]]
        bucket["count"] += 1
        if len(bucket["examples"]) < 6:
            sample = dict(row)
            sample.pop("trace", None)
            bucket["examples"].append(sample)
            if row.get("trace") and "trace" not in bucket:
                bucket["trace"] = row["trace"]
    room_jobs = sum(1 for job in jobs if job["kind"] == "room")
    report = {
        "seconds": round(time.time() - started, 2),
        "workers": workers,
        "seeds": list(SEEDS),
        "sets": [name for name, _items in SETS],
        "rooms": room_jobs // (len(SEEDS) * len(SETS)),
        "room_scenarios": room_jobs,
        "frames_nominal_per_room": FRAMES,
        "frames_nominal": room_jobs * FRAMES,
        "scenarios": scenarios,
        "frames_run": frames,
        "failure_count": len(failures),
        "distinct": len(grouped),
        "groups": grouped,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
