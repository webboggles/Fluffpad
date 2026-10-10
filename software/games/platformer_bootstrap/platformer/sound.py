"""One-voice PWM sound effects: each effect is a list of (start_hz, end_hz, frames) sweeps."""
from machine import Pin, PWM

SFX = {
    "jump": ((300, 700, 4),),
    "land": ((120, 80, 2),),
    "coin": ((990, 990, 2), (1320, 1320, 4)),
    "hurt": ((400, 100, 8),),
    "win": ((523, 523, 4), (659, 659, 4), (784, 784, 4), (1047, 1047, 10)),
}


class Sound:
    def __init__(self, pin=6, duty=1200):
        self.pwm = PWM(Pin(pin))
        self.pwm.duty_u16(0)
        self.duty = duty
        self.on = True
        self.fx = None
        self.i = 0
        self.t = 0

    def play(self, name):
        self.fx = SFX[name]
        self.i = 0
        self.t = 0

    def toggle(self):
        self.on = not self.on
        if not self.on:
            self.silence()

    def tick(self):
        if not self.fx:
            return
        f0, f1, n = self.fx[self.i]
        if self.on:
            self.pwm.freq(f0 + (f1 - f0) * self.t // max(1, n - 1))
            self.pwm.duty_u16(self.duty)
        self.t += 1
        if self.t >= n:
            self.t = 0
            self.i += 1
            if self.i >= len(self.fx):
                self.fx = None
                self.silence()

    def silence(self):
        self.pwm.duty_u16(0)
