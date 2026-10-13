"""Static checks for the jade_sun world: sizes, grid, edge alignment, markers vs meta, stages, finds.

  .venv/bin/python games/jade_sun/tools/check_world.py                (from software/)
  .venv/bin/python games/jade_sun/tools/check_world.py --zone mountain   only that zone and its edges
"""
import argparse
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
mp = types.ModuleType("micropython")
mp.const = lambda x: x
sys.modules["micropython"] = mp

from jade_sun import world_data as wd  # noqa: E402

OPEN = set(".~=g^RBPNDiLTKZcfsbewmkx%SG")
MARKERS = set("PNDiLTKZcfsbewmkxB")
BOSS_STAGE = {"xoc": "pearl", "jaguar": "dash", "eagle": "feather", "camazotz": "gate"}


def passable(ch):
    return ch != "#"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", default="")
    a = ap.parse_args()
    errors, warns = [], []
    scope = set(wd.ZONE_FILES[a.zone].ROOMS) if a.zone else set(wd.ROOMS)
    items = set()
    try:
        from jade_sun import story
        items = set(story.ITEMS)
    except Exception as e:  # story imports hw on some paths; the check still runs
        warns.append("story not importable: %s" % e)

    seen_pos = {}
    for rid, r in wd.ROOMS.items():
        if r["pos"] in seen_pos:
            errors.append("%s and %s share pos %s" % (seen_pos[r["pos"]], rid, r["pos"]))
        seen_pos[r["pos"]] = rid
    for rid in sorted(scope):
        r = wd.ROOMS[rid]
        m = r["map"]
        if len(m) != 14:
            errors.append("%s: %d rows" % (rid, len(m)))
            continue
        for i, line in enumerate(m):
            if len(line) != 20:
                errors.append("%s row %d: len %d" % (rid, i, len(line)))
            bad = set(line) - OPEN - {"#"}
            if bad:
                errors.append("%s row %d: unknown chars %s" % (rid, i, "".join(sorted(bad))))
        if r.get("stage") not in wd.STAGES:
            errors.append("%s: stage %r not in %s" % (rid, r.get("stage"), wd.STAGES))
        if r.get("zone") not in wd.ZONE_FILES:
            errors.append("%s: zone %r" % (rid, r.get("zone")))
        counts = {k: sum(line.count(k) for line in m) for k in "NiLDPKZ"}
        for ch, key in (("N", "npcs"), ("i", "items"), ("L", "lore")):
            if counts[ch] != len(r.get(key, ())):
                errors.append("%s: %s markers %d vs %s %s" % (rid, ch, counts[ch], key, r.get(key)))
        if counts["P"] > 1:
            errors.append("%s: more than one shrine P" % rid)
        b = r.get("boss")
        if b:
            if counts["K"] != 1:
                errors.append("%s: boss room needs exactly one K" % rid)
            if r["stage"] != BOSS_STAGE.get(b, r["stage"]):
                warns.append("%s: boss %s room stage %s, expected %s" % (rid, b, r["stage"], BOSS_STAGE[b]))
        elif counts["K"]:
            errors.append("%s: K without boss" % rid)
        if counts["Z"] and not r.get("watcher"):
            errors.append("%s: Z without watcher flag" % rid)
        if "balam" in r.get("npcs", ()) and not counts["Z"]:
            errors.append("%s: Balam's room needs a Z watcher spawn" % rid)
        if r.get("lurker") and m[9][7] != "~" and m[9][8] != "~":
            errors.append("%s: lurker spawns at tile (7, 9) which must be water" % rid)
        for key in ("items", "npcs", "lore"):
            for f in r.get(key, ()):
                if f not in wd.FINDS:
                    errors.append("%s: %s %s has no FINDS stage" % (rid, key, f))
                elif wd.STAGES.index(wd.FINDS[f]) < wd.STAGES.index(r["stage"]):
                    errors.append("%s: find %s stage %s is before its room stage %s" % (rid, f, wd.FINDS[f], r["stage"]))
                if key == "items" and items and f not in items:
                    errors.append("%s: item %s missing from story.ITEMS" % (rid, f))
                if key == "lore" and f not in wd.LORE:
                    errors.append("%s: lore %s missing from LORE" % (rid, f))
        if r.get("music") is None:
            errors.append("%s: no music" % rid)
        for i in range(13):
            for j in range(19):
                a, b, c, d = m[i][j], m[i][j + 1], m[i + 1][j], m[i + 1][j + 1]
                if (a != "#" and d != "#" and b == "#" and c == "#") or \
                   (b != "#" and c != "#" and a == "#" and d == "#"):
                    errors.append("%s: corner pinch at col %d row %d (open cells touch only diagonally)" % (rid, j, i))

    for rid, r in wd.ROOMS.items():
        x, y = r["pos"]
        m = r["map"]
        for side, (dx, dy) in (("E", (1, 0)), ("S", (0, 1)), ("W", (-1, 0)), ("N", (0, -1))):
            nb = wd.AT.get((x + dx, y + dy))
            if rid not in scope and (nb not in scope):
                continue
            if side in "EW":
                col = 19 if side == "E" else 0
                edge = [m[row][col] for row in range(14)]
            else:
                row = 13 if side == "S" else 0
                edge = list(m[row])
            if not nb:
                if any(passable(ch) for ch in edge) and rid in scope:
                    warns.append("%s: open %s edge with no neighbour (drawn open, solid in play)" % (rid, side))
                continue
            if side not in "ES":
                continue
            o = wd.ROOMS[nb]["map"]
            other = [o[row][0] for row in range(14)] if side == "E" else list(o[0])
            for k in range(len(edge)):
                if passable(edge[k]) != passable(other[k]):
                    errors.append("%s->%s %s %d: '%s' vs '%s'" % (rid, nb, "row" if side == "E" else "col", k,
                                                                edge[k], other[k]))

    for f, s in wd.FINDS.items():
        if s not in wd.STAGES:
            errors.append("FINDS %s: stage %r" % (f, s))
    for zone, mod in wd.ZONE_FILES.items():
        for e in mod.ENTRY:
            if e[0] not in mod.ROOMS or e[3] not in wd.STAGES:
                errors.append("%s ENTRY %r invalid" % (zone, e))

    for w in warns:
        print("WARN", w)
    for e in errors:
        print("ERR", e)
    print("rooms %d (checked %d) errors %d warnings %d" % (len(wd.ROOMS), len(scope), len(errors), len(warns)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
