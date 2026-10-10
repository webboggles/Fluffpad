"""Static checks for jade_sun/world_data.py: sizes, edge alignment, marker/meta counts."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "..", "..", "emulator", "mocks"))

from jade_sun import world_data as wd  # noqa: E402

OPEN = set(".~=g^RBP NDiLTKZcfsbewmkx%SG")
SOLIDISH = set("#")
errors = []


def passable(ch):
    return ch not in SOLIDISH


for rid, r in wd.ROOMS.items():
    m = r["map"]
    if len(m) != 14:
        errors.append(f"{rid}: {len(m)} rows")
    for i, line in enumerate(m):
        if len(line) != 20:
            errors.append(f"{rid} row {i}: len {len(line)}")
    counts = {k: sum(line.count(k) for line in m) for k in "NiLD"}
    if counts["N"] != len(r.get("npcs", ())):
        errors.append(f"{rid}: N markers {counts['N']} vs npcs {r.get('npcs')}")
    if counts["i"] != len(r.get("items", ())):
        errors.append(f"{rid}: i markers {counts['i']} vs items {r.get('items')}")
    if counts["L"] != len(r.get("lore", ())):
        errors.append(f"{rid}: L markers {counts['L']} vs lore {r.get('lore')}")
    if r.get("boss") and sum(line.count("K") for line in m) != 1:
        errors.append(f"{rid}: boss room needs exactly one K")

for rid, r in wd.ROOMS.items():
    x, y = r["pos"]
    m = r["map"]
    nb = {
        "E": wd.AT.get((x + 1, y)), "W": wd.AT.get((x - 1, y)),
        "N": wd.AT.get((x, y - 1)), "S": wd.AT.get((x, y + 1)),
    }
    if nb["E"]:
        o = wd.ROOMS[nb["E"]]["map"]
        for row in range(14):
            a, b = m[row][19], o[row][0]
            if passable(a) != passable(b):
                errors.append(f"{rid}->{nb['E']} row {row}: '{a}' vs '{b}'")
    if nb["S"]:
        o = wd.ROOMS[nb["S"]]["map"]
        for col in range(20):
            a, b = m[13][col], o[0][col]
            if passable(a) != passable(b):
                errors.append(f"{rid}->{nb['S']} col {col}: '{a}' vs '{b}'")

for e in errors:
    print("ERR", e)
print("rooms", len(wd.ROOMS), "errors", len(errors))
sys.exit(1 if errors else 0)
