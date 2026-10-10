"""Bosses and the Stone Watcher. hit() returns 0 blocked, 1 damaged, 2 defeated."""
import math
import random
from .hw import display
from .world import SOLID, T_PLANK
from .gfx import pen, HUD, WHITE, BLACK, GOLD, RED, JADE, PURPLE
from .enemies import EProj, Enemy, overlap

FLOOR = 192


class Boss:
    name = ""
    title = ""
    reward = None
    max_hp = 10
    contact = 1

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.hp = self.max_hp
        self.timer = 0
        self.state = "intro"
        self.flash = 0
        self.dying = 0
        self.face = -1
        self.t = 0

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def hurt_rects(self):
        return (self.rect(),)

    def vulnerable(self, beam):
        return True

    def hit(self, dmg, from_x, beam=False):
        if self.state == "intro" or self.dying:
            return 0
        if not self.vulnerable(beam):
            return 0
        self.hp -= dmg
        self.flash = 4
        if self.hp <= 0:
            self.hp = 0
            self.dying = 1
            return 2
        return 1

    def go(self, state):
        self.state = state
        self.timer = 0

    def phase2(self):
        return self.hp * 2 <= self.max_hp

    def tick(self, g):
        self.t += 1
        if self.flash:
            self.flash -= 1
        if self.dying:
            self.dying += 1
            return
        self.timer += 1
        if self.state == "intro":
            if self.timer > 45:
                self.go("idle")
            return
        self.update(g)

    def update(self, g):
        pass

    def body_pen(self, normal):
        return WHITE if self.flash else normal


# --- Xoc ---------------------------------------------------------------------
class Xoc(Boss):
    name = "XOC"
    title = "THE DEEP SERPENT"
    reward = "g_water"
    max_hp = 22
    w = 18
    h = 16

    def __init__(self, x, y):
        super().__init__(x, y)
        self.trail = [(x, y)] * 48
        self.tx, self.ty = 160.0, 110.0
        self.dirx, self.diry = -1.0, 0.0

    def hurt_rects(self):
        out = [(self.x - 9, self.y - 8, 18, 16)]
        for i in range(8, 48, 8):
            sx, sy = self.trail[i]
            out.append((sx - 6, sy - 6, 12, 12))
        return out

    def rect(self):
        return (self.x - 9, self.y - 8, 18, 16)

    def _steer(self, tx, ty, sp, turn=0.12):
        dx, dy = tx - self.x, ty - self.y
        d = math.sqrt(dx * dx + dy * dy) or 1
        self.dirx += (dx / d - self.dirx) * turn
        self.diry += (dy / d - self.diry) * turn
        n = math.sqrt(self.dirx ** 2 + self.diry ** 2) or 1
        self.dirx /= n
        self.diry /= n
        self.x = max(24, min(296, self.x + self.dirx * sp))
        self.y = max(24, min(196, self.y + self.diry * sp))
        return d

    def update(self, g):
        p = g.player
        st = self.state
        sp = 3.0 if self.phase2() else 2.2
        if st == "idle":
            if self._steer(self.tx, self.ty, sp) < 20 or self.timer % 50 == 0:
                self.tx, self.ty = random.randint(40, 280), random.randint(40, 190)
            if self.timer > (70 if self.phase2() else 100):
                self.go("tell" if random.randint(0, 1) else "spit")
        elif st == "tell":
            self.x += random.randint(-2, 2)
            if self.timer == 1:
                g.audio.sfx_play("roar", 2)
            if self.timer > 20:
                dx, dy = p.cx - self.x, p.cy - self.y
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx, self.vy = dx / d * 6.5, dy / d * 6.5
                self.dirx, self.diry = dx / d, dy / d
                self.go("lunge")
        elif st == "lunge":
            self.x = max(20, min(300, self.x + self.vx))
            self.y = max(20, min(200, self.y + self.vy))
            if self.timer > 20:
                self.go("idle")
                self.tx, self.ty = random.randint(40, 280), random.randint(40, 190)
        elif st == "spit":
            self._steer(p.cx, p.cy, 0.8)
            if self.timer == 12:
                n = 5 if self.phase2() else 3
                base = math.atan2(p.cy - self.y, p.cx - self.x)
                for i in range(n):
                    a = base + (i - (n - 1) / 2) * 0.35
                    g.eprojs.append(EProj("bubble", self.x, self.y, math.cos(a) * 1.8, math.sin(a) * 1.8, 200))
                g.audio.sfx_play("bubble")
            if self.timer > 30:
                self.go("idle")
        self.face = 1 if self.dirx > 0 else -1
        self.trail.insert(0, (self.x, self.y))
        self.trail.pop()

    def draw(self, t):
        body = self.body_pen(pen(40, 120, 110))
        belly = pen(200, 210, 120)
        for i in range(47, 0, -6):
            sx, sy = self.trail[i]
            r = 7 - i // 12
            display.set_pen(body)
            display.circle(int(sx), int(sy) + HUD, r)
            display.set_pen(belly)
            display.circle(int(sx), int(sy) + HUD + 2, max(1, r - 4))
        x, y = int(self.x), int(self.y) + HUD
        f = self.face
        display.set_pen(body)
        display.circle(x, y, 9)
        display.triangle(x + f * 4, y - 6, x + f * 16, y - 2, x + f * 4, y + 6)
        display.set_pen(GOLD)
        display.triangle(x - 6, y - 7, x - 2, y - 15, x + 2, y - 7)
        display.triangle(x, y - 8, x + 4, y - 16, x + 8, y - 8)
        display.set_pen(RED if self.state == "tell" else pen(255, 230, 60))
        display.circle(x + f * 4, y - 3, 2)
        if self.state in ("lunge", "spit"):
            display.set_pen(pen(120, 20, 30))
            display.triangle(x + f * 6, y + 1, x + f * 16, y + 1, x + f * 8, y + 6)


# --- Balam's Shadow ------------------------------------------------------------
class Jaguar(Boss):
    name = "BALAM'S SHADOW"
    title = "STOLEN BY CAMAZOTZ"
    reward = "g_jaguar"
    max_hp = 26
    w = 30
    h = 18

    def __init__(self, x, y):
        super().__init__(x, FLOOR - 18)

    def _floor(self):
        if self.y >= FLOOR - self.h:
            self.y = float(FLOOR - self.h)
            self.vy = 0.0
            return True
        return False

    def update(self, g):
        p = g.player
        st = self.state
        dx = p.cx - (self.x + self.w / 2)
        if st in ("idle", "prowl"):
            self.face = 1 if dx > 0 else -1
            self.x += self.face * (2.0 if self.phase2() else 1.4)
            if self.timer > 40:
                self.go("crouch" if random.randint(0, 2) else "dashtell")
        elif st == "crouch":
            if self.timer == 1:
                g.audio.sfx_play("roar", 2)
            if self.timer > 14:
                tgt = p.cx - self.w / 2
                self.vx = (tgt - self.x) / 26
                self.vy = -8.5
                self.go("pounce")
        elif st == "pounce":
            self.x += self.vx
            self.vy += 0.65
            self.y += self.vy
            if self.vy > 0 and self._floor():
                g.fx.kick(5)
                g.audio.sfx_play("boom")
                if self.phase2():
                    cx = self.x + self.w / 2
                    g.eprojs.append(EProj("wave", cx, FLOOR - 4, 3.2, 0, 80))
                    g.eprojs.append(EProj("wave", cx, FLOOR - 4, -3.2, 0, 80))
                self.go("land")
        elif st == "land":
            if self.timer > 22:
                self.go("prowl")
        elif st == "dashtell":
            self.face = 1 if dx > 0 else -1
            self.x -= self.face * 0.8
            if self.timer > 18:
                self.go("dash")
                g.audio.sfx_play("dash")
        elif st == "dash":
            self.x += self.face * 6.5
            if self.x < 18 or self.x > 302 - self.w:
                self.x = max(18, min(302 - self.w, self.x))
                g.fx.kick(8)
                g.audio.sfx_play("boom")
                if self.phase2():
                    for _ in range(3):
                        g.eprojs.append(EProj("rock", random.randint(30, 290), 0, 0, 1, 120))
                self.go("stun")
        elif st == "stun":
            if self.timer > 30:
                self.go("prowl")
        self.x = max(16, min(304 - self.w, self.x))
        if st != "pounce":
            self._floor()

    def draw(self, t):
        x, y = int(self.x), int(self.y) + HUD
        f = self.face
        crouch = 4 if self.state in ("crouch", "dashtell") else 0
        body = self.body_pen(pen(30, 20, 40))
        display.set_pen(body)
        display.rectangle(x + 4, y + 4 + crouch, 22, 10 - crouch)
        hx = x + (24 if f > 0 else 6)
        display.circle(hx, y + 5 + crouch, 7)
        display.triangle(hx - 6, y + crouch, hx - 3, y - 6 + crouch, hx, y + crouch)
        display.triangle(hx, y + crouch, hx + 3, y - 6 + crouch, hx + 6, y + crouch)
        step = (t >> 2) & 1 if self.state in ("prowl", "idle", "dash") else 0
        for lx in (x + 6, x + 22):
            display.rectangle(lx + step * 2, y + 13, 3, 5)
        tail = int(math.sin(t * 0.2) * 5)
        display.line(x + (2 if f > 0 else 28), y + 6, x + (-8 if f > 0 else 38), y + tail)
        display.set_pen(pen(90, 60, 130))
        for sx, sy in ((10, 7), (15, 10), (19, 6), (13, 5)):
            display.circle(x + sx, y + sy + crouch // 2, 1)
        eye = pen(120, 255, 160) if not (self.state == "crouch" and (t >> 1) & 1) else WHITE
        display.set_pen(eye)
        display.rectangle(hx + f * 2, y + 3 + crouch, 2, 2)
        display.rectangle(hx + f * 5, y + 3 + crouch, 2, 2)
        if self.state in ("stun", "land"):
            display.set_pen(GOLD)
            for k in range(3):
                a = t * 0.2 + k * 2.1
                display.pixel(hx + int(8 * math.cos(a)), y - 6 + int(3 * math.sin(a)))


# --- Ikal the Storm Eagle ----------------------------------------------------------
class Eagle(Boss):
    name = "IKAL"
    title = "THE STORM EAGLE"
    reward = "g_sky"
    max_hp = 30
    w = 30
    h = 18

    def __init__(self, x, y):
        super().__init__(x, 30)
        self.bolts = []

    def update(self, g):
        p = g.player
        st = self.state
        cx = self.x + self.w / 2
        if st in ("idle", "hover"):
            tx = p.cx + (60 if p.cx < 160 else -60) - self.w / 2
            self.x += (tx - self.x) * 0.03
            self.y = 30 + math.sin(self.t * 0.08) * 10
            self.face = 1 if p.cx > cx else -1
            if self.phase2() and self.timer % 28 == 0:
                g.eprojs.append(EProj("feather", cx, self.y + 14, (p.cx - cx) / 60, 3.2, 100))
            if self.timer > 70:
                self.go("tell" if random.randint(0, 2) else "storm")
        elif st == "tell":
            if self.timer == 1:
                g.audio.sfx_play("screech", 2)
            self.y -= 0.5
            if self.timer > 16:
                dx, dy = p.cx - cx, p.cy - (self.y + 9)
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx, self.vy = dx / d * 6.2, dy / d * 6.2
                self.face = 1 if dx > 0 else -1
                self.go("dive")
        elif st == "dive":
            self.x += self.vx
            self.y += self.vy
            if self.y > 158 or self.timer > 40:
                self.y = min(self.y, 158)
                self.vx = self.face * 4.0
                self.go("glide")
        elif st == "glide":
            self.x += self.vx
            if self.x < 10 or self.x > 310 - self.w or self.timer > 40:
                self.face = -self.face
                self.go("rise")
        elif st == "rise":
            self.y -= 3
            self.x += self.face * 1.5
            if self.y < 34:
                self.go("hover")
        elif st == "storm":
            if self.timer == 1:
                xs = [p.cx, random.randint(20, 300), random.randint(20, 300)]
                if self.phase2():
                    xs.append(random.randint(20, 300))
                self.bolts = [[int(x), 0] for x in xs]
                g.audio.sfx_play("screech")
            if self.timer == 34:
                g.audio.sfx_play("thunder", 3)
                g.fx.white(2)
                g.flash_backlight()
                g.fx.kick(6)
            if 34 <= self.timer < 42:
                for bx, _ in self.bolts:
                    if overlap((bx - 7, 0, 14, 224), p.rect()):
                        g.hurt_player(bx, 1)
            if self.timer > 50:
                self.bolts = []
                self.go("hover")
        self.x = max(0, min(320 - self.w, self.x))

    def draw(self, t):
        x, y = int(self.x), int(self.y) + HUD
        f = self.face
        for bx, _ in self.bolts:
            if self.timer < 34:
                if (t >> 1) & 1:
                    display.set_pen(pen(150, 200, 255))
                    display.rectangle(bx - 1, HUD, 2, 224)
            else:
                display.set_pen(WHITE)
                display.rectangle(bx - 4, HUD, 8, 224)
                display.set_pen(pen(150, 200, 255))
                display.rectangle(bx - 7, HUD, 3, 224)
                display.rectangle(bx + 4, HUD, 3, 224)
        flap = (t >> 2) & 1 if self.state not in ("dive", "glide") else 0
        body = self.body_pen(pen(70, 80, 120))
        display.set_pen(pen(200, 210, 240) if not self.flash else WHITE)
        if self.state in ("dive", "glide"):
            display.triangle(x - 4, y + 4, x + 34, y + 4, x + 15, y + 12)
        elif flap:
            display.triangle(x + 4, y + 8, x - 10, y - 10, x + 14, y + 6)
            display.triangle(x + 26, y + 8, x + 40, y - 10, x + 16, y + 6)
        else:
            display.triangle(x + 4, y + 6, x - 12, y + 20, x + 14, y + 10)
            display.triangle(x + 26, y + 6, x + 42, y + 20, x + 16, y + 10)
        display.set_pen(body)
        display.circle(x + 15, y + 9, 8)
        display.triangle(x + 15 - f * 6, y + 12, x + 15 - f * 16, y + 18, x + 15 - f * 4, y + 16)
        display.set_pen(WHITE)
        display.circle(x + 15 + f * 6, y + 4, 5)
        display.set_pen(GOLD)
        display.triangle(x + 15 + f * 9, y + 3, x + 15 + f * 16, y + 6, x + 15 + f * 9, y + 7)
        display.set_pen(RED if self.state == "tell" else BLACK)
        display.circle(x + 15 + f * 7, y + 3, 1)


# --- The Stone Watcher ---------------------------------------------------------------
class Watcher(Boss):
    name = "THE WATCHER"
    title = ""
    reward = "g_stone"
    max_hp = 3
    w = 22
    h = 30
    contact = 2

    def __init__(self, x, y, state="patrol"):
        super().__init__(x, y - 14)
        self.state = state
        self.lost = 0
        self.eye = 0.0
        self.emerge = 0

    def vulnerable(self, beam):
        return beam and self.state != "stagger"

    def hit(self, dmg, from_x, beam=False):
        r = super().hit(1 if beam else 0, from_x, beam)
        if r == 1:
            self.go("stagger")
            self.vx = 3.0 if self.x + self.w / 2 > from_x else -3.0
        return r

    def sees(self, g):
        p = g.player
        cx, cy = self.x + self.w / 2, self.y + 8
        dx, dy = p.cx - cx, p.cy - cy
        if abs(dx) > 180 or abs(dy) > 50:
            return False
        if self.state == "patrol" and (dx > 0) != (self.face > 0):
            return False
        return g.room.los(cx, cy, p.cx, p.cy)

    def _physics(self, g):
        room = g.room
        self.vy = min(self.vy + 0.7, 8)
        ny = self.y + self.vy
        if self.vy > 0:
            for px in (self.x + 2, self.x + self.w - 3):
                t = room.at(px, ny + self.h)
                if SOLID[t] or (t == T_PLANK and self.y + self.h <= ((int(ny + self.h) >> 4) << 4) + 1):
                    ny = ((int(ny + self.h) >> 4) << 4) - self.h
                    self.vy = 0
                    break
        elif SOLID[room.at(self.x + self.w / 2, ny)]:
            self.vy = 0
            ny = self.y
        self.y = ny
        nx = self.x + self.vx
        edge = nx + self.w if self.vx > 0 else nx
        if SOLID[room.at(edge, self.y + 4)] or SOLID[room.at(edge, self.y + self.h - 3)]:
            self.vx = 0
            return True
        self.x = max(-10, min(310 - self.w, nx))
        return False

    def grounded(self, g):
        return SOLID[g.room.at(self.x + self.w / 2, self.y + self.h + 1)] or g.room.at(self.x + self.w / 2, self.y + self.h + 1) == T_PLANK

    def update(self, g):
        p = g.player
        st = self.state
        self.eye = math.sin(self.t * 0.05)
        if self.emerge > 0:
            self.emerge -= 1
            return
        if st in ("patrol", "idle"):
            self.vx = 0.8 * self.face
            if self._physics(g) or self.timer > 160:
                self.face = -self.face
                self.timer = 0
            if self.sees(g):
                self.go("alert")
                g.watcher_alert()
        elif st == "alert":
            self.vx = 0
            self._physics(g)
            self.face = 1 if p.cx > self.x + self.w / 2 else -1
            if self.timer > 16:
                self.go("chase")
        elif st == "chase":
            dx = p.cx - (self.x + self.w / 2)
            self.face = 1 if dx > 0 else -1
            self.vx = 2.5 * self.face
            blocked = self._physics(g)
            up = p.cy < self.y - 10
            if (blocked or (up and abs(dx) < 60)) and self.grounded(g):
                self.vy = -9.5
            if self.sees(g):
                self.lost = 0
            else:
                self.lost += 1
                if self.lost > 120:
                    self.go("patrol")
                    g.watcher_calm()
        elif st == "gloat":
            self.vx = 0
            self._physics(g)
            if self.timer > 50:
                self.go("chase")
        elif st == "stagger":
            self.vx *= 0.9
            self._physics(g)
            if self.timer > 40:
                self.go("chase")

    def draw(self, t):
        if self.emerge > 0 and (self.emerge >> 1) & 1:
            return
        x, y = int(self.x), int(self.y) + HUD
        stone = self.body_pen(pen(96, 92, 104))
        dark = pen(54, 50, 62)
        step = (t >> 3) & 1 if self.state in ("chase", "patrol") else 0
        display.set_pen(dark)
        display.rectangle(x + 2, y + 22 + step, 7, 8 - step)
        display.rectangle(x + 13, y + 22 + (1 - step), 7, 8 - (1 - step))
        display.set_pen(stone)
        display.rectangle(x, y + 8, 22, 16)
        display.rectangle(x + 3, y, 16, 10)
        display.set_pen(dark)
        display.rectangle(x + 3, y + 14, 16, 2)
        display.rectangle(x - 3, y + 10, 4, 12)
        display.rectangle(x + 21, y + 10, 4, 12)
        hunting = self.state in ("alert", "chase", "gloat")
        eye = RED if hunting else pen(255, 200, 60)
        if self.state == "stagger" and (t >> 1) & 1:
            eye = WHITE
        ex = x + 11 + int((self.face * 3) if hunting else self.eye * 4)
        display.set_pen(BLACK)
        display.circle(ex, y + 5, 4)
        display.set_pen(eye)
        display.circle(ex, y + 5, 2 if not hunting else 3)
        if hunting:
            display.set_pen(pen(120, 0, 0))
            display.line(ex, y + 5, ex + self.face * 30, y + 5 + int(math.sin(t * 0.3) * 4))
        for k in range(3 - self.hp):
            display.set_pen(BLACK)
            display.line(x + 4 + k * 6, y + 9, x + 8 + k * 6, y + 20)


# --- Camazotz ------------------------------------------------------------------
class Camazotz(Boss):
    name = "CAMAZOTZ"
    title = "BAT KING OF XIBALBA"
    reward = None
    max_hp = 44
    w = 34
    h = 24

    def __init__(self, x, y):
        super().__init__(x, 30)
        self.eclipse = False

    def phase(self):
        r = self.hp / self.max_hp
        return 1 if r > 0.6 else (2 if r > 0.3 else 3)

    def update(self, g):
        p = g.player
        st = self.state
        ph = self.phase()
        cx = self.x + self.w / 2
        if ph == 3 and not self.eclipse:
            self.eclipse = True
            g.eclipse()
        if st in ("idle", "hover"):
            tx = p.cx - self.w / 2
            self.x += (tx - self.x) * 0.025
            self.y = 32 + math.sin(self.t * 0.07) * 12
            self.face = 1 if p.cx > cx else -1
            if ph == 3 and self.timer % 45 == 0:
                g.eprojs.append(EProj("orb", cx, self.y + 12, 0, 1.5, 220))
            if self.timer > (60 if ph == 1 else 45):
                opts = ["tell", "screech"]
                if ph >= 2:
                    opts.append("summon")
                self.go(opts[random.randint(0, len(opts) - 1)])
        elif st == "tell":
            if self.timer == 1:
                g.audio.sfx_play("screech", 2)
            if self.timer > 14:
                dx, dy = p.cx - cx, p.cy - (self.y + 12)
                d = math.sqrt(dx * dx + dy * dy) or 1
                sp = 6.0 + ph * 0.6
                self.vx, self.vy = dx / d * sp, dy / d * sp
                self.go("dive")
        elif st == "dive":
            self.x += self.vx
            self.y += self.vy + math.sin(self.timer * 0.6) * 2
            if self.y > 160 or self.timer > 40:
                self.y = min(self.y, 160)
                self.vx = (4.5 if p.cx > cx else -4.5)
                self.go("glide")
        elif st == "glide":
            self.x += self.vx
            self.y += math.sin(self.timer * 0.3) * 1.5
            if self.x < 10 or self.x > 310 - self.w or self.timer > 34:
                self.go("rise")
        elif st == "rise":
            self.y -= 3.2
            if self.y < 34:
                self.go("hover")
        elif st == "screech":
            if self.timer == 10:
                n = 8 + (ph - 1) * 4
                for i in range(n):
                    a = i * 6.283 / n + self.t * 0.1
                    g.eprojs.append(EProj("wave", cx, self.y + 12, math.cos(a) * 2.4, math.sin(a) * 2.4, 120))
                g.audio.sfx_play("screech", 2)
                g.fx.ring(cx, self.y + 12, (255, 120, 200), 16, 5)
            if self.timer > 30:
                self.go("hover")
        elif st == "summon":
            if self.timer == 8:
                bats = sum(1 for e in g.enemies if e.kind == "bat")
                for i in range(min(3, 5 - bats)):
                    e = Enemy("bat", int(cx) - 16 + i * 16, int(self.y), 0)
                    e.state = 1
                    e.y = self.y
                    e.cacao = 1
                    g.enemies.append(e)
                g.audio.sfx_play("screech")
            if self.timer > 30:
                self.go("hover")
        self.x = max(0, min(320 - self.w, self.x))

    def draw(self, t):
        x, y = int(self.x), int(self.y) + HUD
        flap = (t >> 2) & 1
        wing = self.body_pen(pen(70, 20, 80))
        body = self.body_pen(pen(40, 10, 50))
        display.set_pen(wing)
        if self.state in ("dive", "glide"):
            display.triangle(x - 14, y + 6, x + 17, y + 2, x + 6, y + 16)
            display.triangle(x + 48, y + 6, x + 17, y + 2, x + 28, y + 16)
        else:
            wy = -12 if flap else 14
            display.triangle(x + 8, y + 6, x - 20, y + wy, x + 4, y + 18)
            display.triangle(x - 20, y + wy, x - 6, y + 20, x + 4, y + 18)
            display.triangle(x + 26, y + 6, x + 54, y + wy, x + 30, y + 18)
            display.triangle(x + 54, y + wy, x + 40, y + 20, x + 30, y + 18)
        display.set_pen(body)
        display.circle(x + 17, y + 12, 11)
        display.triangle(x + 8, y + 4, x + 6, y - 12, x + 14, y + 2)
        display.triangle(x + 26, y + 4, x + 28, y - 12, x + 20, y + 2)
        display.set_pen(GOLD)
        display.rectangle(x + 9, y - 2, 16, 3)
        display.triangle(x + 12, y - 2, x + 17, y - 9, x + 22, y - 2)
        display.set_pen(JADE if self.phase() < 3 else RED)
        display.circle(x + 13, y + 9, 2)
        display.circle(x + 21, y + 9, 2)
        display.set_pen(WHITE)
        display.triangle(x + 13, y + 16, x + 15, y + 16, x + 14, y + 20)
        display.triangle(x + 19, y + 16, x + 21, y + 16, x + 20, y + 20)


BOSSES = {"xoc": Xoc, "jaguar": Jaguar, "eagle": Eagle, "camazotz": Camazotz}
