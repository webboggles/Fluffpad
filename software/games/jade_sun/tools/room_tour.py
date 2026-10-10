"""Emulator module: renders every room (and a boss fight per arena) for visual review.
Run: run_emu.py --module tools.room_tour --frames 400 --every 1"""
import os
from jade_sun import game as G
from jade_sun.world_data import ROOMS

ORDER = ("A0", "A1", "A2", "A3", "B1", "B2", "B3", "B4", "B5", "C1", "C2", "C3", "C4",
         "D1", "D2", "D3", "D4", "E1", "E2")
SPAWN = {"B3": (150, 100), "B4": (160, 150), "B5": (110, 100), "D4": (60, 178), "E2": (150, 178),
         "C2": (150, 178), "D3": (150, 178), "A0": (250, 178), "E1": (120, 178)}


def main():
    g = G.Game()
    g.items |= {"blade", "pearl", "dash", "feather", "spear"}
    g._start_play("A1", 100, 178)
    names = []
    for rid in ORDER:
        x, y = SPAWN.get(rid, (160, 100))
        g.enter_room(rid, x, y)
        g.banner_t = 999
        for _ in range(18 if ROOMS[rid].get("boss") else 4):
            g.frame()
        names.append(rid)
    with open(os.environ.get("TOUR_INDEX", "/tmp/tour_index.txt"), "w") as f:
        f.write("\n".join(names))
