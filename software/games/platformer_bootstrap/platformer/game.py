"""Platformer Bootstrap: one room, collect every coin. A starting point for new Fluffpad games."""
import time
from . import hw, __version__
from .hw import display, restore_bg, snapshot_bg, BB, BA, SX, SY
from .room import Room, bake, HUD
from .player import Player, PW, PH
from .sound import Sound

FRAME_MS = 40
JUMP = BB | BA

WHITE = display.create_pen(255, 255, 255)
HUD_BG = display.create_pen(12, 14, 28)
GOLD = display.create_pen(255, 210, 60)
GOLD_DARK = display.create_pen(190, 130, 20)
BODY = display.create_pen(255, 170, 200)
EYE = display.create_pen(30, 20, 40)


def centre(text, y, scale):
    display.text(text, (320 - display.measure_text(text, scale)) // 2, y, 320, scale)


class Game:
    def __init__(self):
        self.inp = hw.Input()
        self.sound = Sound()
        self.room = Room()
        bake(self.room)
        snapshot_bg()
        self.t = 0
        self.reset()

    def reset(self):
        x, y = self.room.start
        self.player = Player(x, y)
        self.coins = list(self.room.coins)
        self.total = len(self.coins)
        self.deaths = 0
        self.won = False

    def update(self):
        inp = self.inp
        inp.poll()
        if inp.pressed & SX:
            self.sound.toggle()
        if inp.pressed & SY:
            self.reset()
        if self.won:
            return
        p = self.player
        p.update(inp.held, inp.pressed, inp.released, JUMP, self.room)
        for ev in p.events:
            if ev == "jump" or ev == "land":
                self.sound.play(ev)
            elif ev == "spike":
                self.deaths += 1
                self.sound.play("hurt")
                hw.led.set_rgb(255, 0, 0)
                p.x, p.y = self.room.start
                p.vx = p.vy = 0.0
        p.events.clear()
        for c in self.coins:
            if abs(p.cx - c[0]) < 10 and abs(p.cy - c[1]) < 12:
                self.coins.remove(c)
                self.sound.play("coin")
                hw.led.set_rgb(255, 200, 0)
                break
        if not self.coins:
            self.won = True
            self.sound.play("win")
            hw.led.set_rgb(0, 255, 80)
        elif self.t % 8 == 0:
            hw.led.set_rgb(0, 20, 40)

    def draw(self):
        restore_bg()
        bob = (self.t >> 2) & 1
        for x, y in self.coins:
            display.set_pen(GOLD_DARK)
            display.circle(x, y + HUD + bob, 5)
            display.set_pen(GOLD)
            display.circle(x - 1, y + HUD + bob - 1, 3)
        self.draw_player()
        display.set_pen(HUD_BG)
        display.rectangle(0, 0, 320, HUD)
        display.set_pen(WHITE)
        display.text("COINS %d/%d" % (self.total - len(self.coins), self.total), 4, 4, 200, 1)
        display.text("FALLS %d" % self.deaths, 120, 4, 100, 1)
        display.text("v" + __version__, 280, 4, 40, 1)
        if self.won:
            centre("ALL COINS!", 100, 3)
            centre("Display Y to play again", 130, 1)
        display.update()

    def draw_player(self):
        p = self.player
        x, y = int(p.x), int(p.y) + HUD
        squash = 2 if p.ground and abs(p.vx) > 0.5 and (p.anim >> 2) & 1 else 0
        display.set_pen(BODY)
        display.rectangle(x, y + squash, PW, PH - squash)
        display.rectangle(x + 1, y - 3 + squash, 3, 3)
        display.rectangle(x + PW - 4, y - 3 + squash, 3, 3)
        display.set_pen(EYE)
        ex = x + (5 if p.face > 0 else 1)
        display.rectangle(ex, y + 4 + squash, 2, 3)
        display.rectangle(ex + 3, y + 4 + squash, 2, 3)

    def run(self):
        ticks_ms, ticks_diff, sleep_ms = time.ticks_ms, time.ticks_diff, time.sleep_ms
        while True:
            t0 = ticks_ms()
            self.update()
            self.sound.tick()
            self.draw()
            self.t += 1
            dt = ticks_diff(ticks_ms(), t0)
            if dt < FRAME_MS:
                sleep_ms(FRAME_MS - dt)


def main():
    g = None
    try:
        g = Game()
        g.run()
    finally:
        try:
            if g:
                g.sound.silence()
            hw.led.set_rgb(0, 0, 0)
            display.set_pen(0)
            display.clear()
            display.update()
        except Exception:
            pass
        hw.restore_clocks()
