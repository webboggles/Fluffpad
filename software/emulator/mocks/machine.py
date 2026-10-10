"""Stubs for the MicroPython machine module."""

import emu_state

# Display-pack buttons are active-low GPIO with pull-ups.
_BUTTON_PINS = {12: "DA", 13: "DB", 14: "DX", 15: "DY"}
_pin_out = {}


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _pin_id(pin):
    if isinstance(pin, Pin):
        return pin.id
    if isinstance(pin, int):
        return pin
    ident = getattr(pin, "id", pin)
    return ident if isinstance(ident, int) else _as_int(ident, ident)


def freq(hz=None):
    if hz is None:
        return emu_state.cpu_hz
    emu_state.cpu_hz = _as_int(hz, emu_state.cpu_hz)
    return None


def reset():
    return None


def unique_id():
    return b"EMUPICO2"


def idle():
    return None


class Pin:
    IN = 0
    OUT = 1
    OPEN_DRAIN = 2
    PULL_UP = 1
    PULL_DOWN = 2

    def __init__(self, id, mode=-1, pull=-1, value=None):
        self.id = id if isinstance(id, int) else _as_int(id, id)
        self.mode = mode
        self.pull = pull
        if value is not None:
            self.value(value)

    def value(self, v=None):
        if v is None:
            name = _BUTTON_PINS.get(self.id)
            if name is not None:
                return 0 if name in emu_state.buttons else 1
            return _pin_out.get(self.id, 0)
        _pin_out[self.id] = 1 if v else 0
        return None

    def __call__(self, v=None):
        return self.value(v)

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)


class PWM:
    def __init__(self, pin, freq=None, duty_u16=None):
        self._pin = _pin_id(pin)
        self._freq = 0
        self._duty = 0
        if freq is not None:
            self.freq(freq)
        if duty_u16 is not None:
            self.duty_u16(duty_u16)

    def freq(self, v=None):
        if v is None:
            return self._freq
        v = _as_int(v)
        if v < 0:
            v = 0
        if v != self._freq:
            self._freq = v
            emu_state.log_tone(self._pin, self._freq, self._duty)
        return None

    def duty_u16(self, v=None):
        if v is None:
            return self._duty
        v = _as_int(v)
        if v < 0:
            v = 0
        if v > 65535:
            v = 65535
        if v != self._duty:
            self._duty = v
            emu_state.log_tone(self._pin, self._freq, self._duty)
        return None

    def deinit(self):
        self.duty_u16(0)


class I2C:
    def __init__(self, id=0, scl=None, sda=None, freq=400000, **kwargs):
        self.id = id
        self.freq = freq

    def scan(self):
        return []

    def readfrom_mem(self, addr, memaddr, nbytes, addrsize=8):
        return bytes(int(nbytes))

    def readfrom_mem_into(self, addr, memaddr, buf, addrsize=8):
        for i in range(len(buf)):
            buf[i] = 0
        return None

    def writeto_mem(self, addr, memaddr, buf, addrsize=8):
        return len(buf)

    def writeto(self, addr, buf, stop=True):
        return len(buf)

    def readfrom(self, addr, nbytes, stop=True):
        return bytes(int(nbytes))

    def readinto(self, buf, stop=True):
        for i in range(len(buf)):
            buf[i] = 0
        return None

    def write_readinto(self, write_buf, read_buf, stop=True):
        for i in range(len(read_buf)):
            read_buf[i] = 0
        return None


class SPI:
    MSB = 0
    LSB = 1

    def __init__(self, id=0, baudrate=1_000_000, polarity=0, phase=0, bits=8,
                 firstbit=0, sck=None, mosi=None, miso=None, **kwargs):
        self.id = id
        self.baudrate = baudrate

    def write(self, buf):
        return len(buf)

    def read(self, nbytes, write=0x00):
        return bytes(int(nbytes))

    def readinto(self, buf, write=0x00):
        for i in range(len(buf)):
            buf[i] = 0
        return None

    def write_readinto(self, write_buf, read_buf):
        for i in range(len(read_buf)):
            read_buf[i] = 0
        return None


class _Mem32:
    def __init__(self):
        self._d = {}

    def __getitem__(self, addr):
        try:
            return self._d.get(int(addr), 0)
        except (TypeError, ValueError):
            return 0

    def __setitem__(self, addr, value):
        self._d[int(addr)] = _as_int(value) & 0xFFFFFFFF


mem32 = _Mem32()
