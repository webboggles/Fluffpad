"""PimoroniI2C with a TCA9555 gamepad at address 0x21.

The 16-bit input word is active-low (1 = released). Bit positions:
U=1, L=2, R=3, D=4, '-'=5, '+'=11, B=12, Y=13, A=14, X=15.
"""

import emu_state

_BITS = {
    "U": 1,
    "L": 2,
    "R": 3,
    "D": 4,
    "-": 5,
    "+": 11,
    "B": 12,
    "Y": 13,
    "A": 14,
    "X": 15,
}


class PimoroniI2C:
    def __init__(self, sda=4, scl=5, baudrate=400000):
        self.sda = sda
        self.scl = scl
        self.baudrate = baudrate
        # Registers 2..7 are config/output latches. 0 and 1 are live inputs.
        self._regs = [0xFF] * 8

    def scan(self):
        return [0x21]

    def _input_word(self):
        word = 0xFFFF
        for name in emu_state.buttons:
            bit = _BITS.get(name)
            if bit is not None:
                word &= ~(1 << bit)
        return word

    def _reg_byte(self, reg):
        if reg <= 1:
            return (self._input_word() >> (8 * reg)) & 0xFF
        if 2 <= reg <= 7:
            return self._regs[reg]
        return 0xFF

    def readfrom_mem(self, addr, reg, n, addrsize=8):
        n = int(n)
        reg = int(reg)
        if addr != 0x21:
            return bytes([0xFF]) * n
        return bytes(self._reg_byte(reg + i) for i in range(n))

    def readfrom_mem_into(self, addr, reg, buf, addrsize=8):
        data = self.readfrom_mem(addr, reg, len(buf))
        for i, value in enumerate(data):
            buf[i] = value
        return None

    def writeto_mem(self, addr, reg, buf, addrsize=8):
        data = bytes(buf)
        reg = int(reg)
        if addr == 0x21:
            for i, value in enumerate(data):
                index = reg + i
                if 0 <= index <= 7:
                    self._regs[index] = value & 0xFF
        return len(data)

    def writeto(self, addr, buf, stop=True):
        data = bytes(buf)
        if not data:
            return 0
        self.writeto_mem(addr, data[0], data[1:])
        return len(data)

    def readfrom(self, addr, n, stop=True):
        return bytes([0xFF]) * int(n)
