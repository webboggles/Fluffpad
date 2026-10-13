# La-Fluff-Puff and the Jade Sun

Flip-screen metroidvania RPG for Pico Plus 2 W + Pico Display Pack 2.8" + Qw/ST Pad.

## Hardware notes

- `clk_peri` is remapped to `clk_sys / 2` at 250 MHz so the ST7789 SPI runs at 62.5 MHz: `update()` drops from 61 ms to 23 ms.
- Static room art is baked once into a background buffer and memcpy'd into the framebuffer each frame (3.7 ms).
- Fixed 25 fps step. Pad LEDs 1 to 4 show collected Sun Glyphs. RGB LED breathes the zone mood.

## Controls

| Input | Action |
| --- | --- |
| D-pad | Move, `U` talk / read / save, `D` + jump drops through planks, `D` + attack in air = pogo |
| B | Jump (double jump with Quetzal Feather, swim with Rain Pearl) |
| Y | Obsidian Blade |
| A | Jaguar Dash |
| X | Sun Spear (hold to charge) |
| + / display A | Map and stats |
| - / display B | Pause |
| display X | Volume |

## World

54 rooms in six zones, one file each (`jade_sun/world_<zone>.py`), composed by `world_data.py`. Room counts: Rainforest 11, Sacred Cenote 13, Temple of the Jaguar 7, Dread Halls 7, Mountain of Witz 9, Xibalba 7. Zone links below are taken from the solver's room graph (`tools/out/room_graph.json`); labels give the first ability stage at which the crossing works.

```mermaid
flowchart LR
  subgraph Rainforest
    A1[A1 Ceiba Village - start, Ceiba] --- A0[A0 Great Pyramid - Sun Gate]
    A3[A3 Temple Approach]
    A7[A7 Strangler Fig]
    A8[A8 Root Hollow]
    A9[A9 Fern Gully]
    A10[A10 Waterfall Pool]
  end
  subgraph Cenote[Sacred Cenote]
    B1[B1 Cenote Mouth]
    B2[B2 Drowned Gallery - Chaac, Rain Pearl]
    B4[B4 Lair of Xoc]
    B6[B6 Dripstone Hall]
    B11[B11 Upper Falls]
    B13[B13 Sluice Tunnel]
  end
  subgraph Temple[Temple of the Jaguar]
    C1[C1 Hall of Jaguars]
    C2[C2 Jaguar Throne - Balam's Shadow]
    C7[C7 Sunken Stair]
    C8[C8 Upper Colonnade]
  end
  subgraph Dread[Dread Halls]
    F1[F1 Dread Halls]
    F4[F4 Watcher's Deep - Balam, Jaguar Dash]
    F7[F7 Collapsed Sluice]
  end
  subgraph Mountain[Mountain of Witz]
    D1[D1 Misty Ascent]
    D3[D3 Storm Peak - Ikal]
    D4[D4 Summit of Witz - Witz, Sun Spear]
    D5[D5 Hanging Monastery]
    D6[D6 Wind Caves - Quetzal Feather]
    D8[D8 Sky Bridge]
  end
  subgraph Xibalba
    E1[E1 Road of Xibalba]
    E2[E2 Roost of Camazotz]
  end
  A9 <-->|blade| B1
  A8 <-->|blade| B6
  A3 <-->|pearl| C1
  B13 <-->|pearl| F7
  C7 <-->|pearl| F1
  A10 <-->|dash| B11
  A3 <-->|dash| D1
  D5 -->|one way| A7
  D8 -->|one way| C8
  A0 <-->|4 glyphs| E1
```

## Progression

```mermaid
flowchart TD
  Blade[Obsidian Blade from Ceiba] --> Pearl[Rain Pearl, Burenia-style flooded dread]
  Pearl --> Xoc[Xoc - Glyph of Water]
  Pearl --> Temple[Temple door opens]
  Temple --> Dash[Jaguar Dash, escape the Stone Watcher]
  Dash --> Jaguar[Balam's Shadow - Glyph of Jaguar]
  Dash --> Feather[Quetzal Feather]
  Feather --> Eagle[Ikal - Glyph of Sky]
  Eagle --> Spear[Sun Spear from Witz]
  Spear --> Watcher[Shatter the Watcher - Glyph of Stone]
  Watcher --> Gate[Sun Gate]
  Gate --> Camazotz[Camazotz - Jade Sun restored]
```

## Files

All paths are under `software/games/jade_sun/`.

- `jade_sun/` game package, `main.py` entry point.
- `tools/check_world.py` map validator (sizes, seams, markers, stages, corner pinches), `tools/solve_world.py` physics reachability solver; a whole-world run also writes `tools/out/room_graph.json`, which `tools/playthrough.py` routes over.
- `tools/zone_map.py` renders a zone sheet, `tools/art_budget.py` counts draw calls per sprite and room bake against the device caps.
- `tools/fuzz.py`, `tools/boss_test.py`, `tools/scenario.py`, `tools/room_tour.py` emulator soak and story tests; `tools/playthrough.py` bot playthrough to MP4.
- `tools/device_perf.py`, `tools/device_profile.py` on-device timing.
