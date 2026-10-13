"""Room maps, merged from the zone files. 20x14 tiles of 16px. Legend:
.  air          #  rock          %  cracked (dash / beam)   =  plank (one-way, drop with down+jump)
g  grate        ^  spikes        ~  water                   S  sun seal (beam)
R  rain door    G  sun gate      B  boss door
P  shrine       N  spirit (npcs) D  trader                  i  item (items)    L  lore (lore)
T  torch        K  boss          Z  watcher spawn           c  cacao
f frog  s snake  b bat  e eel  w clay warrior  m fire mask  k swift  x wisp

Rooms sit on a global grid ("pos"); neighbours are the rooms in the four adjacent cells.
"stage" is the first ability stage at which a room can be reached; FINDS does the same for
items, spirits and lore. tools/solve_world.py proves both.
"""
from . import world_jungle, world_cenote, world_temple, world_dread, world_mountain, world_xibalba

STAGES = ("blade", "pearl", "dash", "feather", "spear", "gate")
ZONE_FILES = {
    "jungle": world_jungle, "cenote": world_cenote, "temple": world_temple,
    "dread": world_dread, "mountain": world_mountain, "xibalba": world_xibalba,
}

ROOMS = {}
LORE = {}
FINDS = {}
for _m in ZONE_FILES.values():
    ROOMS.update(_m.ROOMS)
    LORE.update(_m.LORE)
    FINDS.update(_m.FINDS)

AT = {}
for _rid, _r in ROOMS.items():
    AT[_r["pos"]] = _rid

START_ROOM = world_jungle.ENTRY[0][0]
START_POS = world_jungle.ENTRY[0][1:3]
