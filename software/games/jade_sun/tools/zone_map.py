"""Stitch baked rooms into a picture at their grid positions, for reviewing level flow.

  .venv/bin/python games/jade_sun/tools/zone_map.py --zone cenote          tools/out/maps/cenote.png (1x)
  .venv/bin/python games/jade_sun/tools/zone_map.py --scale 0.25           whole world, quarter size
  add --items to draw every ability-locked tile and marker letter on top
"""
import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
from fuzz import _boot_path, _patch_runtime  # noqa: E402

_boot_path()
_patch_runtime()

from PIL import Image, ImageDraw  # noqa: E402
from jade_sun.hw import display  # noqa: E402
from jade_sun import gfx  # noqa: E402
from jade_sun.world import Room  # noqa: E402
from jade_sun import world_data as wd  # noqa: E402

LABEL = {"i": "item", "N": "npc", "L": "lore", "P": "shrine", "K": "boss", "Z": "watcher", "D": "trader"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", default="")
    ap.add_argument("--scale", type=float, default=0.0, help="default 1 for a zone, 0.25 for the world")
    ap.add_argument("--items", action="store_true", help="overlay marker letters")
    a = ap.parse_args()
    rooms = list(wd.ZONE_FILES[a.zone].ROOMS) if a.zone else list(wd.ROOMS)
    scale = a.scale or (1.0 if a.zone else 0.25)
    xs = [wd.ROOMS[r]["pos"][0] for r in rooms]
    ys = [wd.ROOMS[r]["pos"][1] for r in rooms]
    x0, y0 = min(xs), min(ys)
    cw, ch = int(320 * scale), int(224 * scale)
    gap = 2
    img = Image.new("RGB", ((max(xs) - x0 + 1) * (cw + gap), (max(ys) - y0 + 1) * (ch + gap)), (8, 8, 12))
    d = ImageDraw.Draw(img)
    for rid in rooms:
        r = wd.ROOMS[rid]
        gfx.bake(Room(rid), 0)
        shot = display.image.crop((0, 16, 320, 240))
        if a.items:
            sd = ImageDraw.Draw(shot)
            for row, line in enumerate(r["map"]):
                for col, c in enumerate(line):
                    if c in LABEL:
                        sd.rectangle((col * 16 + 3, row * 16 + 3, col * 16 + 13, row * 16 + 13), outline=(255, 255, 0))
                        sd.text((col * 16 + 5, row * 16 + 3), c, fill=(255, 255, 0))
        if scale != 1:
            shot = shot.resize((cw, ch), Image.LANCZOS)
        px, py = r["pos"]
        ox, oy = (px - x0) * (cw + gap), (py - y0) * (ch + gap)
        img.paste(shot, (ox, oy))
        d.text((ox + 3, oy + 2), "%s %s [%s]" % (rid, r["name"], r["stage"]), fill=(255, 255, 160))
    out = TOOLS_DIR / "out" / "maps" / ((a.zone or "world") + ".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
