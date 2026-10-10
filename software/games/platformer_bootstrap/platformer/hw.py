"""Hardware: clocks, display with background cache, input, RGB LED."""
import time
import machine
from machine import Pin, mem32
from micropython import const

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


def snapshot_bg():
    """Copy the current framebuffer into the background cache."""
    if _EMU:
        display.emu_snapshot()
    else:
        _MB[:] = _MF


def restore_bg():
    """Blit the background cache into the framebuffer."""
    if _EMU:
        display.emu_restore(0, 0)
    else:
        _MF[:] = _MB


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


class Input:
    def __init__(self):
        self.held = 0
        self.pressed = 0
        self.released = 0
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


led = RGBLED(26, 27, 28)
