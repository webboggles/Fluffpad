"""PicoGraphics framebuffer backed by a Pillow image."""

import colorsys

from PIL import Image, ImageDraw

import emu_state

DISPLAY_PICO_DISPLAY_2 = 1
PEN_RGB565 = 0
PEN_RGB332 = 1
PEN_P8 = 2

WIDTH = 320
HEIGHT = 240

# Pimoroni bitmap8 (font8): 8px columns, bit 0 is the top row, proportional widths.
_WIDTHS = (3, 1, 3, 5, 4, 4, 4, 1, 3, 3, 3, 3, 2, 3, 2, 4, 4, 3, 4, 4, 4, 4, 4, 4, 4, 4, 1, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 4, 4, 4, 5, 4, 4, 4, 4, 4, 4, 5, 4, 4, 5, 4, 4, 4, 2, 4, 2, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 4, 4, 3, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 4, 4, 4, 3, 1, 3, 4, 1)
_COLS = bytes((0,0,0,0,0,95,0,0,0,0,3,0,3,0,0,40,124,40,124,40,36,122,47,18,0,102,16,8,102,0,54,73,73,124,0,3,0,0,0,0,28,34,65,0,0,65,34,28,0,0,84,56,84,0,0,16,56,16,0,0,128,96,0,0,0,16,16,16,0,0,96,96,0,0,0,96,24,6,1,0,62,65,65,62,0,66,127,64,0,0,98,81,73,70,0,33,73,77,51,0,24,22,17,127,0,79,73,73,49,0,60,74,73,48,0,1,97,25,7,0,54,73,73,54,0,6,73,41,30,0,51,0,0,0,0,128,108,0,0,0,16,40,68,0,0,40,40,40,0,0,68,40,16,0,0,2,81,9,6,0,62,73,85,94,0,126,9,9,126,0,127,73,73,54,0,62,65,65,34,0,127,65,65,62,0,127,73,73,65,0,127,9,9,1,0,62,65,73,121,0,127,8,8,127,0,65,127,65,0,0,48,64,64,63,0,127,8,20,99,0,127,64,64,64,0,127,2,4,2,127,127,2,4,127,0,62,65,65,62,0,127,9,9,6,0,62,65,33,94,0,127,9,25,102,0,70,73,73,49,0,1,1,127,1,1,63,64,64,63,0,127,64,32,31,0,63,64,32,64,63,119,8,8,119,0,71,72,72,63,0,113,73,69,67,0,127,65,0,0,0,1,6,24,96,0,65,127,0,0,0,4,2,4,0,0,64,64,64,0,0,1,1,0,0,0,32,84,84,120,0,127,68,68,56,0,56,68,68,40,0,56,68,68,127,0,56,84,84,88,0,126,9,9,2,0,24,164,164,124,0,127,4,4,120,0,4,125,64,0,0,96,128,128,125,0,127,16,40,68,0,1,127,64,0,0,124,4,120,4,120,124,4,4,120,0,56,68,68,56,0,252,36,36,24,0,24,36,36,252,0,124,8,4,4,0,72,84,84,36,0,62,68,68,32,0,60,64,64,124,0,124,64,32,28,0,60,64,32,64,60,108,16,16,108,0,28,160,160,124,0,100,84,76,0,0,8,62,65,0,0,127,0,0,0,0,65,62,8,0,0,8,4,8,4,0,0,0,0,0,0))
_GLYPHS = {}


def _i(value):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0


def _coord(value):
    """Drawing coordinate. Clamped so a wild value cannot hang Pillow."""
    n = _i(value)
    if n > 20000:
        return 20000
    if n < -20000:
        return -20000
    return n


def _text_scale(value):
    n = _i(value)
    if n < 1:
        return 1
    if n > 8:
        return 8
    return n


def _glyph_width(ch, fixed_width):
    o = ord(ch) if ch else 0
    if o < 32 or o > 127:
        return 0
    if fixed_width:
        return 5
    return _WIDTHS[o - 32]


def _glyph(ch, scale):
    """bitmap8 column mask, nearest-scaled. Cached."""
    key = (ch, scale)
    cached = _GLYPHS.get(key)
    if cached is not None:
        return cached
    gw = _glyph_width(ch, False)
    height = 8 * scale
    img = Image.new("L", (max(1, gw * scale), height), 0)
    if gw:
        px = img.load()
        base = (ord(ch) - 32) * 5
        for cx in range(gw):
            col = _COLS[base + cx]
            x0 = cx * scale
            bit = 1
            for cy in range(8):
                if col & bit:
                    y0 = cy * scale
                    for dy in range(scale):
                        for dx in range(scale):
                            px[x0 + dx, y0 + dy] = 255
                bit <<= 1
    _GLYPHS[key] = img
    return img


class PicoGraphics:
    def __init__(self, display, pen_type=PEN_RGB565, rotate=0, buffer=None):
        self.display = display
        self.pen_type = pen_type
        self.rotate = rotate
        self.buffer = buffer  # accepted; the live pixels stay in self.image
        self.image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        self._pen = 0
        self._thickness = 1
        self._clip = None  # (x, y, w, h) or None
        self.font = None

    def get_bounds(self):
        return (WIDTH, HEIGHT)

    def set_backlight(self, v):
        try:
            emu_state.backlight = float(v)
        except (TypeError, ValueError):
            emu_state.backlight = 0.0

    def set_font(self, name):
        self.font = name

    def create_pen(self, r, g, b):
        def ch(v):
            n = _i(v)
            if n < 0:
                return 0
            if n > 255:
                return 255
            return n
        return (ch(r) << 16) | (ch(g) << 8) | ch(b)

    def create_pen_hsv(self, h, s, v):
        try:
            h = float(h) % 1.0
            s = min(1.0, max(0.0, float(s)))
            v = min(1.0, max(0.0, float(v)))
        except (TypeError, ValueError):
            return 0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return self.create_pen(int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))

    def set_pen(self, p):
        # Pens are 0xRRGGBB, far outside the coordinate clamp.
        try:
            self._pen = int(p) & 0xFFFFFF
        except (TypeError, ValueError, OverflowError):
            self._pen = 0

    def _rgb(self):
        p = self._pen
        return ((p >> 16) & 255, (p >> 8) & 255, p & 255)

    def _clip_box(self):
        """None = no clip. False = clip is empty. Else (x, y, w, h) on screen."""
        if self._clip is None:
            return None
        x, y, w, h = self._clip
        if w <= 0 or h <= 0:
            return False
        x0 = 0 if x < 0 else x
        y0 = 0 if y < 0 else y
        x1 = WIDTH if x + w > WIDTH else x + w
        y1 = HEIGHT if y + h > HEIGHT else y + h
        if x1 <= x0 or y1 <= y0:
            return False
        return (x0, y0, x1 - x0, y1 - y0)

    def _mutate(self, fn):
        # Draw straight onto the framebuffer, or onto a scratch copy and paste
        # only the clip rectangle back, so every primitive honours set_clip.
        box = self._clip_box()
        if box is False:
            return
        if box is None:
            fn(self.image)
            return
        scratch = self.image.copy()
        fn(scratch)
        x, y, w, h = box
        self.image.paste(scratch.crop((x, y, x + w, y + h)), (x, y))

    def clear(self):
        colour = self._rgb()

        def fn(img):
            ImageDraw.Draw(img).rectangle((0, 0, WIDTH - 1, HEIGHT - 1), fill=colour)

        self._mutate(fn)

    def rectangle(self, x, y, w, h):
        x, y, w, h = _coord(x), _coord(y), _i(w), _i(h)
        if w <= 0 or h <= 0:
            return
        x0 = 0 if x < 0 else x
        y0 = 0 if y < 0 else y
        x1 = x + w
        y1 = y + h
        if x1 > WIDTH:
            x1 = WIDTH
        if y1 > HEIGHT:
            y1 = HEIGHT
        if x1 <= x0 or y1 <= y0:
            return
        colour = self._rgb()

        def fn(img):
            # Pillow's rectangle is inclusive of both corners.
            ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=colour)

        self._mutate(fn)

    def circle(self, x, y, r):
        x, y, r = _coord(x), _coord(y), _i(r)
        if r <= 0:
            self.pixel(x, y)
            return
        if r > 4000:
            r = 4000
        colour = self._rgb()
        box = (x - r, y - r, x + r, y + r)

        def fn(img):
            ImageDraw.Draw(img).ellipse(box, fill=colour)

        self._mutate(fn)

    def pixel(self, x, y):
        x, y = _coord(x), _coord(y)
        if x < 0 or y < 0 or x >= WIDTH or y >= HEIGHT:
            return
        colour = self._rgb()

        def fn(img):
            img.putpixel((x, y), colour)

        self._mutate(fn)

    def pixel_span(self, x, y, length):
        length = _i(length)
        if length <= 0:
            return
        self.rectangle(x, y, length, 1)

    def set_thickness(self, t):
        t = _i(t)
        self._thickness = 1 if t < 1 else (64 if t > 64 else t)

    def line(self, x1, y1, x2, y2, thickness=None):
        x1, y1, x2, y2 = _coord(x1), _coord(y1), _coord(x2), _coord(y2)
        t = self._thickness if thickness is None else _i(thickness)
        if t < 1:
            t = 1
        if t > 64:
            t = 64
        colour = self._rgb()

        def fn(img):
            ImageDraw.Draw(img).line((x1, y1, x2, y2), fill=colour, width=t)

        self._mutate(fn)

    def triangle(self, x1, y1, x2, y2, x3, y3):
        self.polygon(((x1, y1), (x2, y2), (x3, y3)))

    def polygon(self, points):
        try:
            pts = [(_coord(p[0]), _coord(p[1])) for p in points]
        except (TypeError, IndexError, ValueError):
            return
        if len(pts) < 3:
            return
        colour = self._rgb()

        def fn(img):
            ImageDraw.Draw(img).polygon(pts, fill=colour)

        self._mutate(fn)

    def measure_text(self, text, scale=2, spacing=1, fixed_width=False):
        scale = _text_scale(scale)
        gap = _i(spacing) * scale
        text = "" if text is None else str(text)
        widest = 0
        for line in text.split("\n"):
            # This board's bitmap8 measure includes the trailing gap.
            width = 0
            for ch in line:
                width += _glyph_width(ch, fixed_width) * scale + gap
            if width > widest:
                widest = width
        return widest

    def _line_mask(self, text, scale, spacing, fixed_width=False):
        height = 8 * scale
        gap = spacing * scale
        width = 0
        for ch in text:
            width += _glyph_width(ch, fixed_width) * scale + gap
        if width < 1:
            return Image.new("L", (1, height), 0)
        mask = Image.new("L", (width, height), 0)
        x = 0
        for ch in text:
            gw = _glyph_width(ch, fixed_width)
            if gw:
                mask.paste(_glyph(ch, scale), (x, 0))
            x += gw * scale + gap
        return mask

    def text(self, text, x, y, wordwrap=-1, scale=2, angle=0, spacing=1, fixed_width=False):
        x, y = _coord(x), _coord(y)
        scale = _text_scale(scale)
        spacing = _i(spacing)
        lines = self._wrap(text, wordwrap, scale, spacing)
        if not lines:
            return
        lh = 9 * scale
        masks = [self._line_mask(line, scale, spacing, fixed_width) for line in lines]
        block_w = max(m.size[0] for m in masks)
        block_h = lh * (len(masks) - 1) + 8 * scale
        block = Image.new("L", (max(1, block_w), max(1, block_h)), 0)
        for i, mask in enumerate(masks):
            block.paste(mask, (0, i * lh))
        angle = _i(angle) % 360
        if angle:
            block = block.rotate(angle, expand=True, resample=Image.Resampling.NEAREST)
        colour = self._rgb()

        def fn(img):
            tint = Image.new("RGB", block.size, colour)
            img.paste(tint, (x, y), block)

        self._mutate(fn)

    def _wrap(self, text, wordwrap, scale, spacing):
        text = "" if text is None else str(text)
        limit = _i(wordwrap)
        lines = []
        for para in text.split("\n"):
            if limit <= 0:
                lines.append(para)
                continue
            cur = ""
            for word in para.split(" "):
                trial = word if cur == "" else cur + " " + word
                if cur == "" or self.measure_text(trial, scale, spacing) <= limit:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = word
            lines.append(cur)
        return lines

    def character(self, ch, x, y, scale=2):
        if isinstance(ch, int):
            try:
                ch = chr(ch)
            except (ValueError, OverflowError):
                ch = ""
        else:
            ch = "" if ch is None else str(ch)[:1]
        self.text(ch, x, y, wordwrap=-1, scale=scale)

    def set_clip(self, x, y, w, h):
        self._clip = (_coord(x), _coord(y), _i(w), _i(h))

    def remove_clip(self):
        self._clip = None

    def partial_update(self, x, y, w, h):
        return None

    def emu_snapshot(self):
        """Stands in for the device's memcpy of the framebuffer into the background cache."""
        self._bg = self.image.copy()

    def emu_snapshot_rows(self, y0, y1):
        if getattr(self, "_bg", None) is None:
            self._bg = self.image.copy()
        self._bg.paste(self.image.crop((0, y0, WIDTH, y1)), (0, y0))

    def emu_restore(self, dx=0, dy=0):
        bg = getattr(self, "_bg", None)
        if bg is None:
            return
        if dx or dy:
            self.image.paste(bg, (0, 0))
            self.image.paste(bg, (dx, dy))
        else:
            self.image.paste(bg, (0, 0))

    def set_palette(self, *args, **kwargs):
        return None

    def update_pen(self, *args, **kwargs):
        return None

    def reset_pen(self, *args, **kwargs):
        return None

    def update(self):
        emu_state.frames += 1
        emu_state.virtual_us += int(emu_state.frame_us)
        hook = emu_state.on_frame
        if hook is not None:
            hook(self)
