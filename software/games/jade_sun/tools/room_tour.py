"""Emulator module: renders every room (and a boss fight per arena) for visual review.
Run: run_emu.py --module tools.room_tour --frames 2000 --every 1"""
import os
from jade_sun import game as G
from jade_sun.world_data import ROOMS
from tools.fuzz import spawn_for


def main():
    g = G.Game()
    g.items |= {"blade", "pearl", "dash", "feather", "spear"}
    g._start_play(G.START_ROOM, G.START_POS[0], G.START_POS[1])
    names = []
    for rid in ROOMS:
        x, y = spawn_for(ROOMS[rid]["map"])
        g.enter_room(rid, x, y)
        g.banner_t = 999
        for _ in range(18 if ROOMS[rid].get("boss") else 4):
            g.frame()
        names.append(rid)
    with open(os.environ.get("TOUR_INDEX", "/tmp/tour_index.txt"), "w") as f:
        f.write("\n".join(names))
