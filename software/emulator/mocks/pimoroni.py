"""Pimoroni helpers used by the display pack and the Qw/ST pad."""

import emu_state
from machine import Pin


def _clamp8(value):
    try:
        n = int(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    if n < 0:
        return 0
    if n > 255:
        return 255
    return n


def _pin_id(pin):
    if isinstance(pin, Pin):
        return pin.id
    if isinstance(pin, int):
        return pin
    return getattr(pin, "id", pin)


class RGBLED:
    def __init__(self, r, g, b):
        self.pins = (r, g, b)

    def set_rgb(self, r, g, b):
        emu_state.led = (_clamp8(r), _clamp8(g), _clamp8(b))


class Button:
    def __init__(self, pin, invert=True, repeat_time=200, hold_time=1000):
        self.pin = pin if isinstance(pin, Pin) else Pin(pin, Pin.IN, Pin.PULL_UP)
        self.invert = invert

    def _down(self):
        # Pin.value() is already active-low for the display buttons.
        raw = self.pin.value()
        pressed = (raw == 0)
        return pressed if self.invert else (not pressed)

    def read(self):
        return self._down()

    def is_pressed(self):
        return self._down()


class Buzzer:
    def __init__(self, pin):
        self.pin_id = _pin_id(pin)
        self._freq = 0
        self._duty = 0

    def set_tone(self, freq, volume=1):
        try:
            freq = int(freq)
        except (TypeError, ValueError):
            freq = 0
        if freq < 0:
            freq = 0
        try:
            vol = float(volume)
        except (TypeError, ValueError):
            vol = 0.0
        if vol < 0:
            vol = 0.0
        if vol > 1:
            vol = 1.0
        duty = 0 if freq <= 0 or vol <= 0 else int(vol * 32768)
        if freq == self._freq and duty == self._duty:
            return
        self._freq = freq
        self._duty = duty
        emu_state.log_tone(self.pin_id, freq, duty)
