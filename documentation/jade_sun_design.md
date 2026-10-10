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

```mermaid
flowchart LR
  subgraph Mountain
    D3[Storm Peak - Ikal boss] --- D4[Summit of Witz - Sun Spear]
    D1[Misty Ascent - Quetzal Feather] --- D2[Eagle Cliffs - heart]
    D1 -->|double jump| D3
  end
  subgraph Surface
    A0[Great Pyramid - Sun Gate] --- A1[Ceiba Village - start]
    A1 --- A2[Canopy] --- A3[Temple Approach]
  end
  subgraph Cenote
    B2[Drowned Gallery - Rain Pearl] --- B1[Cenote Mouth]
    B1 -->|Pearl| B3[Abyss] --- B4[Xoc boss]
    B4 --> B5[Waterfall Shaft]
  end
  subgraph Temple
    C1[Temple Hall] -->|Dash wall| C2[Jaguar Throne - Shadow boss]
    C1 --- C3[Dread Halls I] --- C4[Dread Halls II - Jaguar Dash]
  end
  subgraph Xibalba
    E1[Road of Xibalba] --> E2[Camazotz]
  end
  A2 --> B1
  B5 -->|grate, one way| A3
  A3 -->|Rain door, Pearl| C1
  A3 -->|Dash chasm| D1
  A0 -->|4 glyphs| E1
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
- `tools/check_world.py` map validator, `tools/solve_world.py` physics reachability solver.
- `tools/fuzz.py`, `tools/boss_test.py`, `tools/scenario.py`, `tools/room_tour.py` emulator soak and story tests; `tools/playthrough.py` bot playthrough to MP4.
- `tools/device_perf.py`, `tools/device_profile.py` on-device timing.
