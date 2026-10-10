"""Build emulator input scripts. Usage: make_input.py NAME > file.json"""
import json
import sys


def intro():
    s = [[10, 11, ["B"]], [20, 21, ["+"]]]
    s += [[f, f + 1, ["B"]] for f in range(160, 640, 14)]
    return s, 640


def walk_canopy(start):
    s = [[start, start + 400, ["R"]]]
    s += [[f, f + 8, ["B"]] for f in range(start + 20, start + 400, 45)]
    s += [[f, f + 1, ["Y"]] for f in range(start + 10, start + 400, 17)]
    return s


SCRIPTS = {}


def build(name):
    s, t = intro()
    if name == "intro":
        return s
    if name == "canopy":
        return s + walk_canopy(t)
    if name == "map":
        return s + [[t + 10, t + 11, ["+"]]]
    raise SystemExit("unknown script " + name)


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1])))
