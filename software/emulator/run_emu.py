"""Headless emulator for a Pimoroni Pico Display Pack 2.8 (320x240) game.

Runs a MicroPython game loop on CPython. Each display.update() is one frame.
Before the game starts, the process changes into a fresh temp directory
(printed on stdout) so save files stay out of the project tree. Pass --cwd
to choose that directory instead.

--game is a folder from software/games (default jade_sun). Without --module
the game's main.py runs as __main__, exactly as it would on the board. With
--module, that module is imported from the game folder and its main() called.

Examples:
  python run_emu.py --game skedaddle --frames 600 --shots 1,300 --press '60:Y:2'

  python run_emu.py --module demo_game --frames 120 --shots 1,60,120 \\
      --gif 1:60:2 --press '10:R:40' --wav out/demo.wav

  python run_emu.py --frames 600 --shots 1,300 --every 60 --input buttons.json

--press format: frame:BTN[,BTN]:duration segments separated by ';'.
Duration is a frame count starting at that frame, so 10:R:40 holds R on
frames 10 through 49 inclusive.
--input JSON is a list of [start_frame, end_frame, ["U", "A"]] inclusive
ranges. Names: U D L R A B X Y + - DA DB DX DY.
Shots are frame_NNNNN.png in --out. A 24px strip under the screen shows the
LED swatch, frame number and held buttons, then the whole image is
nearest-neighbour scaled by --scale. GIF frames are 30ms each.
"""

import argparse
import array
import cProfile
import gc
import importlib
import json
import os
import pstats
import runpy
import sys
import tempfile
import time
import traceback
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

EMU_DIR = Path(__file__).resolve().parent
GAMES_DIR = EMU_DIR.parent / "games"
MOCKS_DIR = EMU_DIR / "mocks"
SCREEN_W = 320
SCREEN_H = 240
STRIP_H = 24
BUTTON_ORDER = ("U", "D", "L", "R", "A", "B", "X", "Y", "+", "-", "DA", "DB", "DX", "DY")


def _parse_args(argv):
    p = argparse.ArgumentParser(description="Headless Pico Display emulator")
    p.add_argument("--game", default="jade_sun", help="folder name in software/games, or a path")
    p.add_argument("--module", default="", help="module with main(); default runs main.py")
    p.add_argument("--frames", type=int, default=600)
    p.add_argument("--shots", default="", help="comma separated frame numbers")
    p.add_argument("--every", type=int, default=0, help="also save every K frames")
    p.add_argument("--gif", default="", help="START:END[:STEP]")
    p.add_argument("--out", default=str(EMU_DIR / "out"))
    p.add_argument("--scale", type=int, default=2)
    p.add_argument("--input", default="", help="JSON button script")
    p.add_argument("--press", default="", help="inline button script")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--wav", default="", help="write the PWM tone log as WAV")
    p.add_argument("--profile", action="store_true")
    p.add_argument("--frame-us", type=int, default=23000)
    p.add_argument("--cwd", default="", help="directory to run the game in")
    return p.parse_args(argv)


def _resolve(path_text):
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _parse_gif(text):
    if not text:
        return None
    parts = text.split(":")
    if len(parts) not in (2, 3):
        raise SystemExit("gif must be START:END[:STEP]")
    start, end = int(parts[0]), int(parts[1])
    step = int(parts[2]) if len(parts) == 3 else 1
    if step < 1:
        raise SystemExit("gif step must be >= 1")
    return (start, end, step)


def _parse_press(text):
    ranges = []
    if not text:
        return ranges
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        bits = part.split(":")
        if len(bits) < 2:
            raise SystemExit("bad --press segment: %s" % part)
        frame = int(bits[0])
        names = [b.strip() for b in bits[1].split(",") if b.strip()]
        duration = int(bits[2]) if len(bits) > 2 else 1
        if duration < 1:
            continue
        ranges.append((frame, frame + duration - 1, names))
    return ranges


def _parse_input(path):
    ranges = []
    if not path:
        return ranges
    data = json.loads(Path(path).read_text())
    for item in data:
        start, end, names = item[0], item[1], item[2]
        ranges.append((int(start), int(end), list(names)))
    return ranges


def _buttons_at(frame, ranges):
    held = []
    for start, end, names in ranges:
        if start <= frame <= end:
            for name in names:
                if name not in held:
                    held.append(name)
    return held


def _game_dir(text):
    path = GAMES_DIR / text
    if not path.is_dir():
        path = _resolve(text)
    if not path.is_dir():
        raise SystemExit("no game folder: %s" % text)
    return path


def _install_import_path(game_dir):
    for entry in (str(EMU_DIR), str(game_dir), str(MOCKS_DIR)):
        if entry in sys.path:
            sys.path.remove(entry)
    # mocks first so picographics/machine/time-adjacent imports hit the stubs
    sys.path.insert(0, str(EMU_DIR))
    sys.path.insert(0, str(game_dir))
    sys.path.insert(0, str(MOCKS_DIR))


def _patch_time(emu_state):
    def sleep(seconds):
        emu_state.virtual_us += int(float(seconds) * 1_000_000)

    def sleep_ms(ms):
        emu_state.virtual_us += int(float(ms) * 1000)

    def sleep_us(us):
        emu_state.virtual_us += int(us)

    def ticks_us():
        return emu_state.virtual_us

    def ticks_ms():
        return emu_state.virtual_us // 1000

    def ticks_cpu():
        return emu_state.virtual_us

    def ticks_diff(a, b):
        return a - b

    def ticks_add(a, b):
        return a + b

    def now():
        return emu_state.virtual_us / 1_000_000

    time.sleep = sleep
    time.sleep_ms = sleep_ms
    time.sleep_us = sleep_us
    time.ticks_us = ticks_us
    time.ticks_ms = ticks_ms
    time.ticks_cpu = ticks_cpu
    time.ticks_diff = ticks_diff
    time.ticks_add = ticks_add
    time.time = now


def _patch_gc():
    gc.mem_free = lambda: 8_000_000
    gc.mem_alloc = lambda: 500_000


def _compose(screen, frame_no, led, buttons, scale):
    canvas = Image.new("RGB", (SCREEN_W, SCREEN_H + STRIP_H), (24, 24, 28))
    canvas.paste(screen, (0, 0))
    draw = ImageDraw.Draw(canvas)
    r, g, b = led
    draw.rectangle((4, SCREEN_H + 4, 19, SCREEN_H + 19), fill=(int(r), int(g), int(b)))
    draw.rectangle((4, SCREEN_H + 4, 19, SCREEN_H + 19), outline=(180, 180, 180))
    shown = [name for name in BUTTON_ORDER if name in buttons]
    label = "f=%05d  %s" % (frame_no, " ".join(shown) if shown else "-")
    draw.text((26, SCREEN_H + 6), label, fill=(230, 230, 230), font=ImageFont.load_default())
    if scale > 1:
        canvas = canvas.resize(
            (SCREEN_W * scale, (SCREEN_H + STRIP_H) * scale),
            Image.Resampling.NEAREST,
        )
    return canvas


def _write_wav(path, events, duration_us, rate=22050):
    path.parent.mkdir(parents=True, exist_ok=True)
    duration_us = int(duration_us)
    if duration_us < 0:
        duration_us = 0
    # Keep a runaway sleep from writing a multi-gigabyte file.
    if duration_us > 180_000_000:
        duration_us = 180_000_000
    n = int(duration_us * rate / 1_000_000)
    if n < 1:
        n = 1
    by_pin = {}
    for t, pin, freq, duty in events:
        by_pin.setdefault(pin, []).append((int(t), int(freq), int(duty)))
    pins = []
    for seq in by_pin.values():
        seq.sort(key=lambda item: item[0])
        pins.append(seq)
    index = [0] * len(pins)
    current = [(0, 0)] * len(pins)
    samples = array.array("h")
    for i in range(n):
        t_us = i * 1_000_000 // rate
        acc = 0.0
        for p, seq in enumerate(pins):
            k = index[p]
            while k < len(seq) and seq[k][0] <= t_us:
                current[p] = (seq[k][1], seq[k][2])
                k += 1
            index[p] = k
            freq, duty = current[p]
            if freq <= 0 or duty <= 0:
                continue
            amp = (duty if duty < 32768 else 32768) / 32768.0
            if (t_us * freq) % 1_000_000 < 500_000:
                acc += amp
            else:
                acc -= amp
        if acc > 1.0:
            acc = 1.0
        elif acc < -1.0:
            acc = -1.0
        samples.append(int(acc * 32767))
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(samples.tobytes())


def main(argv=None):
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.frames < 1:
        raise SystemExit("--frames must be >= 1")
    scale = args.scale if args.scale >= 1 else 1
    shots = set()
    if args.shots.strip():
        for part in args.shots.split(","):
            part = part.strip()
            if part:
                shots.add(int(part))
    gif_spec = _parse_gif(args.gif)
    game_dir = _game_dir(args.game)
    out_dir = _resolve(args.out)
    wav_path = _resolve(args.wav) if args.wav else None
    input_path = _resolve(args.input) if args.input else None
    ranges = []
    if input_path is not None:
        ranges.extend(_parse_input(input_path))
    ranges.extend(_parse_press(args.press))

    if args.cwd:
        work = _resolve(args.cwd)
        work.mkdir(parents=True, exist_ok=True)
    else:
        work = Path(tempfile.mkdtemp(prefix="pico_emu_"))
    print("cwd: %s" % work)
    os.chdir(work)

    _install_import_path(game_dir)
    import emu_state

    emu_state.reset()
    emu_state.frame_us = args.frame_us
    _patch_time(emu_state)
    _patch_gc()
    if args.seed is not None:
        import random
        random.seed(args.seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    gif_frames = []
    exit_code = 0
    profile = cProfile.Profile() if args.profile else None

    def on_frame(display):
        n = emu_state.frames
        want_png = n in shots or (args.every > 0 and n % args.every == 0)
        want_gif = False
        if gif_spec is not None:
            start, end, step = gif_spec
            want_gif = start <= n <= end and (n - start) % step == 0
        if want_png or want_gif:
            image = _compose(display.image, n, emu_state.led, set(emu_state.buttons), scale)
            if want_png:
                image.save(out_dir / ("frame_%05d.png" % n))
            if want_gif:
                gif_frames.append(image)
        if n >= args.frames:
            raise emu_state.EmuStop()
        nxt = _buttons_at(n + 1, ranges)
        emu_state.buttons.clear()
        emu_state.buttons.update(nxt)

    emu_state.on_frame = on_frame
    emu_state.buttons.update(_buttons_at(1, ranges))

    try:
        if profile is not None:
            profile.enable()
        if args.module:
            importlib.import_module(args.module).main()
        else:
            runpy.run_path(str(game_dir / "main.py"), run_name="__main__")
    except emu_state.EmuStop:
        pass
    except KeyboardInterrupt:
        print("KeyboardInterrupt at frame %s" % emu_state.frames)
        exit_code = 130
    except SystemExit as exc:
        print("SystemExit at frame %s: %s" % (emu_state.frames, exc))
        if exc.code is None:
            exit_code = 0
        elif isinstance(exc.code, int):
            exit_code = exc.code
        else:
            exit_code = 1
    except Exception:
        traceback.print_exc()
        print("frame: %s" % emu_state.frames)
        exit_code = 1
    finally:
        if profile is not None:
            profile.disable()

    if gif_frames:
        gif_path = out_dir / "gif.gif"
        gif_frames[0].save(
            gif_path,
            save_all=True,
            append_images=gif_frames[1:],
            duration=30,
            loop=0,
            optimize=False,
        )
    if wav_path is not None:
        _write_wav(wav_path, list(emu_state.tone_log), emu_state.virtual_us)

    virtual_s = emu_state.virtual_us / 1_000_000
    print(
        "frames %s  virtual_s %.3f  tone_events %s  led %s"
        % (emu_state.frames, virtual_s, len(emu_state.tone_log), tuple(emu_state.led))
    )
    if profile is not None:
        stats = pstats.Stats(profile)
        stats.sort_stats("cumtime")
        stats.print_stats(25)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
