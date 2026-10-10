"""Stand-in game that exercises the display, pad, PWM and LED mocks."""

import gc
import time
from machine import PWM, Pin, freq
from micropython import const
from picographics import DISPLAY_PICO_DISPLAY_2, PEN_RGB565, PicoGraphics
from pimoroni import RGBLED
from pimoroni_i2c import PimoroniI2C

STEP = const(2)
_BIT_U = 1
_BIT_L = 2
_BIT_R = 3
_BIT_D = 4


def main():
    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565)
    display.set_backlight(1.0)
    display.set_font("bitmap8")
    led = RGBLED(0, 1, 2)
    pad = PimoroniI2C()
    tone = PWM(Pin(6))
    tone.freq(440)
    tone.duty_u16(0)
    _ = freq()
    _ = gc.mem_free()

    black = display.create_pen(0, 0, 0)
    white = display.create_pen(255, 255, 255)
    red = display.create_pen(220, 40, 40)
    green = display.create_pen(40, 200, 80)
    blue = display.create_pen(30, 70, 180)
    yellow = display.create_pen_hsv(0.14, 0.9, 1.0)
    orange = display.create_pen(240, 140, 30)

    x, y = 40, 100
    while True:
        raw = pad.readfrom_mem(0x21, 0, 2)
        word = raw[0] | (raw[1] << 8)
        right = (word & (1 << _BIT_R)) == 0
        left = (word & (1 << _BIT_L)) == 0
        up = (word & (1 << _BIT_U)) == 0
        down = (word & (1 << _BIT_D)) == 0
        if right:
            x += STEP
        if left:
            x -= STEP
        if up:
            y -= STEP
        if down:
            y += STEP
        if x < 0:
            x = 0
        if y < 24:
            y = 24
        if x > 300:
            x = 300
        if y > 210:
            y = 210

        display.set_pen(black)
        display.clear()
        display.set_pen(blue)
        display.rectangle(0, 0, 320, 20)
        display.set_pen(white)
        display.text("DEMO", 8, 2, scale=2)
        display.character("!", 70, 2, scale=2)
        display.set_pen(green)
        display.circle(280, 60, 18)
        display.set_pen(yellow)
        display.triangle(20, 200, 70, 160, 90, 210)
        display.set_pen(orange)
        display.polygon([(200, 180), (250, 160), (270, 200), (220, 220)])
        display.set_clip(100, 40, 80, 50)
        display.set_pen(red)
        display.rectangle(90, 30, 100, 70)
        display.remove_clip()
        display.set_pen(white)
        display.set_thickness(1)
        display.line(0, 228, 319, 228)
        display.pixel(10, 30)
        display.pixel_span(12, 30, 16)
        display.rectangle(x, y, 16, 16)
        _ = display.measure_text("DEMO", scale=2)
        _ = time.ticks_diff(time.ticks_ms(), 0)

        moving = right or left or up or down
        if moving:
            tone.freq(880)
            tone.duty_u16(20000)
            led.set_rgb(0, 40, 0)
        else:
            tone.duty_u16(0)
            led.set_rgb(20, 0, 0)
        display.update()
