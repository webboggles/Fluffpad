"""Save slot on flash (JSON)."""
import json
import os
import sys

PATH = "/jade_sun_save.json" if sys.implementation.name == "micropython" else "jade_sun_save.json"


def exists():
    try:
        os.stat(PATH)
        return True
    except OSError:
        return False


def load():
    try:
        with open(PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write(data):
    tmp = PATH + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(data, f)
        try:
            os.remove(PATH)
        except OSError:
            pass
        os.rename(tmp, PATH)
        return True
    except OSError:
        return False


def wipe():
    try:
        os.remove(PATH)
    except OSError:
        pass
