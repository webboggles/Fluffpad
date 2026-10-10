"""Hardware: clocks, display buffers, input, LEDs."""
import time
import machine
from machine import Pin, mem32
from micropython import const

_CLOCKS = const(0x40010000)
_PERI_CTRL = const(0x40010048)
_PERI_DIV = const(0x4001004C)
_PERI_SRC_USB = const(2)


def _set_peri(src, div):
    mem32[_PERI_CTRL] &= ~(1 << 11)
    time.sleep_us(10)
    mem32[_PERI_CTRL] = (mem32[_PERI_CTRL] & ~(7 << 5)) | (src << 5)
    mem32[_PERI_DIV] = div << 16
    mem32[_PERI_CTRL] |= 1 << 11
    time.sleep_us(10)


def turbo():
    # The SDK still believes clk_peri is 48 MHz, so SPI ends up at clk_sys / 4.
    try:
        machine.freq(250_000_000)
    except Exception:
        machine.freq(200_000_000)
    _set_peri(0, 2)


def restore_clocks():
    try:
        _set_peri(_PERI_SRC_USB, 1)
        machine.freq(150_000_000)
    except Exception:
        pass


turbo()

from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import RGBLED
from pimoroni_i2c import PimoroniI2C

FB = bytearray(320 * 240 * 2)
BG = bytearray(320 * 240 * 2)
_MF = memoryview(FB)
_MB = memoryview(BG)

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0, buffer=FB)
display.set_font("bitmap8")
display.set_backlight(1.0)
WIDTH, HEIGHT = display.get_bounds()
_EMU = hasattr(display, "emu_snapshot")

_ROW = const(640)


def snapshot_bg():
    """Copy the current framebuffer into the background cache."""
    if _EMU:
        display.emu_snapshot()
    else:
        _MB[:] = _MF


def snapshot_rows(y0, y1):
    """Copy framebuffer rows [y0, y1) into the background cache."""
    if _EMU:
        display.emu_snapshot_rows(y0, y1)
    else:
        _MB[y0 * _ROW:y1 * _ROW] = _MF[y0 * _ROW:y1 * _ROW]


def restore_bg(dx=0, dy=0):
    """Blit the background cache into the framebuffer, optionally shaken."""
    if _EMU:
        display.emu_restore(dx, dy)
        return
    if dx == 0 and dy == 0:
        _MF[:] = _MB
        return
    off = dy * _ROW + dx * 2
    if off > 0:
        _MF[off:] = _MB[:-off]
        _MF[:off] = _MB[:off]
    else:
        off = -off
        _MF[:-off] = _MB[off:]
        _MF[-off:] = _MB[-off:]


# --- Input -----------------------------------------------------------------
U = const(1)
D = const(2)
L = const(4)
R = const(8)
BA = const(16)
BB = const(32)
BX = const(64)
BY = const(128)
PLUS = const(256)
MINUS = const(512)
SA = const(1024)
SB = const(2048)
SX = const(4096)
SY = const(8192)

# TCA9555 input bit -> our bit (pad is active low)
_PAD_MAP = ((1, U), (2, L), (3, R), (4, D), (5, MINUS), (11, PLUS),
            (12, BB), (13, BY), (14, BA), (15, BX))
_PAD_ADDR = const(0x21)
_LED_BITS = (0x0040, 0x0080, 0x0200, 0x0400)


class Input:
    def __init__(self):
        self.held = 0
        self.pressed = 0
        self.released = 0
        self._led_word = -1
        self._pad_ok = False
        self._retry = 0
        self.i2c = PimoroniI2C(sda=4, scl=5, baudrate=100_000)
        self._side = ((Pin(12, Pin.IN, Pin.PULL_UP), SA), (Pin(13, Pin.IN, Pin.PULL_UP), SB),
                      (Pin(14, Pin.IN, Pin.PULL_UP), SX), (Pin(15, Pin.IN, Pin.PULL_UP), SY))
        self._init_pad()

    def _init_pad(self):
        try:
            self.i2c.writeto_mem(_PAD_ADDR, 0x04, b"\x00\x00")
            self.i2c.writeto_mem(_PAD_ADDR, 0x06, b"\x3f\xf9")
            self._pad_ok = True
            self._led_word = -1
        except OSError:
            self._pad_ok = False

    def poll(self):
        bits = 0
        if self._pad_ok:
            try:
                b = self.i2c.readfrom_mem(_PAD_ADDR, 0x00, 2)
                w = ~(b[0] | (b[1] << 8))
                for src, dst in _PAD_MAP:
                    if w & (1 << src):
                        bits |= dst
            except OSError:
                self._pad_ok = False
        else:
            self._retry += 1
            if self._retry > 50:
                self._retry = 0
                self._init_pad()
        for pin, dst in self._side:
            if not pin.value():
                bits |= dst
        self.pressed = bits & ~self.held
        self.released = self.held & ~bits
        self.held = bits

    def any_pressed(self):
        return self.pressed & (BA | BB | BX | BY | PLUS | SA | SB | SY)

    def set_pad_leds(self, mask):
        word = 0xFFFF
        for i in range(4):
            if mask & (1 << i):
                word &= ~_LED_BITS[i]
        if word == self._led_word or not self._pad_ok:
            return
        self._led_word = word
        try:
            self.i2c.writeto_mem(_PAD_ADDR, 0x02, bytes((word & 0xFF, word >> 8)))
        except OSError:
            self._pad_ok = False


# --- RGB LED ---------------------------------------------------------------
class Mood:
    """Breathing RGB LED with one-shot flashes."""

    def __init__(self):
        self.led = RGBLED(26, 27, 28)
        self.base = (0, 40, 20)
        self.flash_col = None
        self.flash_t = 0
        self.t = 0
        self.override = None

    def flash(self, col, frames=8):
        self.flash_col = col
        self.flash_t = frames

    def tick(self):
        self.t += 1
        if self.flash_t > 0:
            self.flash_t -= 1
            r, g, b = self.flash_col
        elif self.override:
            r, g, b = self.override
        else:
            k = (self.t % 100) / 50.0
            k = 0.35 + 0.65 * (k if k < 1 else 2 - k)
            r, g, b = self.base
            r, g, b = int(r * k), int(g * k), int(b * k)
        self.led.set_rgb(r, g, b)

    def off(self):
        self.led.set_rgb(0, 0, 0)
