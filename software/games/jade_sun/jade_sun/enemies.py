"""Regular enemies, enemy projectiles and pickups."""
import math
import random
from .world import SOLID, T_WATER

# kind: (w, h, hp, xp, cacao, contact damage, colour for bursts)
STATS = {
    "frog": (12, 12, 2, 3, 2, 1, (40, 120, 255)),
    "snake": (14, 10, 2, 3, 2, 1, (210, 180, 40)),
    "bat": (12, 9, 1, 2, 1, 1, (100, 70, 130)),
    "eel": (14, 8, 2, 4, 2, 1, (60, 170, 140)),
    "warrior": (14, 20, 5, 8, 4, 1, (190, 100, 60)),
    "mask": (14, 14, 3, 5, 3, 1, (120, 110, 100)),
    "swift": (12, 10, 2, 5, 2, 1, (200, 210, 230)),
    "wisp": (12, 12, 3, 6, 3, 1, (150, 90, 230)),
}
MARKER = {"f": "frog", "s": "snake", "b": "bat", "e": "eel", "w": "warrior", "m": "mask", "k": "swift", "x": "wisp"}


def overlap(a, b):
    return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]


class Enemy:
    def __init__(self, kind, x, y, level=0):
        w, h, hp, xp, cacao, dmg, col = STATS[kind]
        self.kind = kind
        self.w, self.h = w, h
        self.x = float(x + (16 - w) // 2)
        self.y = float(y + 16 - h)
        self.hp = hp + level
        self.xp = xp
        self.cacao = cacao
        self.dmg = dmg
        self.col = col
        self.vx = 0.0
        self.vy = 0.0
        self.face = -1
        self.timer = random.randint(0, 40)
        self.state = 0
        self.flash = 0
        self.knock = 0
        self.home = (self.x, self.y)
        self.alive = True
        self.armour = False
        if kind == "bat":
            self.y = float(y)
        if kind == "mask":
            self.timer = random.randint(0, 60)

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def hit(self, dmg, from_x):
        self.hp -= dmg
        self.flash = 4
        if self.kind not in ("mask",):
            self.knock = 5
            self.vx = 3.0 if self.x + self.w / 2 > from_x else -3.0
        return self.hp <= 0

    def _ground(self, room):
        return SOLID[room.at(self.x + 1, self.y + self.h)] or SOLID[room.at(self.x + self.w - 2, self.y + self.h)]

    def _walk(self, room, vx):
        nx = self.x + vx
        edge = nx + self.w if vx > 0 else nx
        if SOLID[room.at(edge, self.y + self.h - 2)] or not SOLID[room.at(edge, self.y + self.h + 2)] \
                or edge < 0 or edge > 320:
            self.face = -self.face
            return False
        self.x = nx
        return True

    def _fall(self, room, g=0.6):
        self.vy = min(self.vy + g, 7)
        ny = self.y + self.vy
        if self.vy > 0 and (SOLID[room.at(self.x + 1, ny + self.h)] or SOLID[room.at(self.x + self.w - 2, ny + self.h)]):
            ny = ((int(ny + self.h) >> 4) << 4) - self.h
            self.vy = 0
        elif self.vy < 0 and SOLID[room.at(self.x + self.w / 2, ny)]:
            self.vy = 0
            ny = self.y
        self.y = ny

    def update(self, g):
        if self.flash:
            self.flash -= 1
        room = g.room
        p = g.player
        px, py = p.cx, p.cy
        ex, ey = self.x + self.w / 2, self.y + self.h / 2
        dx, dy = px - ex, py - ey
        self.timer += 1
        k = self.kind
        if self.knock:
            self.knock -= 1
            nx = self.x + self.vx
            if 0 < nx < 320 - self.w and not SOLID[room.at(nx + (self.w if self.vx > 0 else 0), self.y + self.h / 2)]:
                self.x = nx
            self.vx *= 0.8
            if k in ("frog", "snake", "warrior"):
                self._fall(room)
            return
        if k == "frog":
            grounded = self._ground(room) and self.vy >= 0
            if grounded:
                self.vx = 0
                if self.timer > 50 and abs(dx) < 140:
                    self.timer = random.randint(0, 15)
                    self.face = 1 if dx > 0 else -1
                    self.vy = -6.0
                    self.vx = 2.2 * self.face
            else:
                nx = self.x + self.vx
                if 0 < nx < 320 - self.w and not SOLID[room.at(nx + (self.w if self.vx > 0 else 0), self.y + self.h / 2)]:
                    self.x = nx
            self._fall(room)
        elif k == "snake":
            if self.state == 0:
                self._walk(room, 1.0 * self.face)
                if abs(dy) < 20 and abs(dx) < 56 and (dx > 0) == (self.face > 0):
                    self.state = 1
                    self.timer = 0
            else:
                if not self._walk(room, 2.6 * self.face) or self.timer > 14:
                    self.state = 0
            self._fall(room)
        elif k == "bat":
            if self.state == 0:
                if abs(dx) < 90 and abs(dy) < 90:
                    self.state = 1
            else:
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.x += dx / d * 1.6
                self.y += dy / d * 1.6 + math.sin(self.timer * 0.25) * 1.2
                self.face = 1 if dx > 0 else -1
        elif k == "eel":
            wet = room.at(ex, ey) == T_WATER
            if p.wet and abs(dx) < 110 and abs(dy) < 70:
                d = math.sqrt(dx * dx + dy * dy) or 1
                vx, vy = dx / d * 1.7, dy / d * 1.7
                self.face = 1 if dx > 0 else -1
            else:
                vx, vy = 1.0 * self.face, math.sin(self.timer * 0.05) * 0.4
            nx, ny = self.x + vx, self.y + vy
            if room.at(nx + self.w / 2 + self.face * 8, ny + self.h / 2) == T_WATER:
                self.x, self.y = nx, ny
            elif room.at(ex, ny + self.h / 2) == T_WATER and wet:
                self.y = ny
                self.face = -self.face
            else:
                self.face = -self.face
        elif k == "warrior":
            if self.state == 0:
                self._walk(room, 0.8 * self.face)
                if abs(dy) < 24 and abs(dx) < 64:
                    self.face = 1 if dx > 0 else -1
                    self.state = 1
                    self.timer = 0
                    g.audio.sfx_tone(300, 500, 4, 600)
            elif self.state == 1:
                if self.timer > 14:
                    self.state = 2
                    self.timer = 0
                    g.audio.sfx_play("slash")
            elif self.state == 2:
                self._walk(room, 2.2 * self.face)
                if self.timer > 10:
                    self.state = 3
                    self.timer = 0
            else:
                if self.timer > 24:
                    self.state = 0
            self._fall(room)
        elif k == "mask":
            self.face = 1 if dx > 0 else -1
            if self.timer > 70 and abs(dx) < 220:
                self.timer = 0
                d = math.sqrt(dx * dx + dy * dy) or 1
                g.eprojs.append(EProj("fire", ex, ey, dx / d * 2.6, dy / d * 2.6))
                g.audio.sfx_play("shoot")
        elif k == "swift":
            if self.state == 0:
                self.x += 1.6 * self.face
                self.y = self.home[1] + math.sin(self.timer * 0.08) * 10
                if self.x < 8 or self.x > 300:
                    self.face = -self.face
                if abs(dx) < 24 and dy > 10:
                    self.state = 1
                    self.timer = 0
                    self.vx = dx / 14
                    self.vy = 4.5
            else:
                self.x += self.vx
                self.y += self.vy
                self.vy -= 0.32
                if self.y <= self.home[1] and self.vy < 0:
                    self.y = self.home[1]
                    self.state = 0
        elif k == "wisp":
            d = math.sqrt(dx * dx + dy * dy) or 1
            sp = 0.9 if d > 30 else 1.3
            self.x += dx / d * sp + math.cos(self.timer * 0.1) * 0.6
            self.y += dy / d * sp + math.sin(self.timer * 0.13) * 0.6
            if self.timer % 120 == 0:
                g.eprojs.append(EProj("orb", ex, ey, dx / d * 1.8, dy / d * 1.8))
        self.x = max(-4, min(316 - self.w, self.x))
        self.y = max(-4, min(222 - self.h, self.y))

    def attack_rect(self):
        if self.kind == "warrior" and self.state == 2:
            if self.face > 0:
                return (self.x + self.w, self.y + 8, 18, 6)
            return (self.x - 18, self.y + 8, 18, 6)
        return None


class Lurker:
    """Xoc's shadow in the Drowned Gallery: cannot be harmed, bites anything in the water."""
    kind = "lurker"

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w, self.h = 34, 12
        self.face = 1
        self.state = 0
        self.timer = 0
        self.hp = 999
        self.armour = True
        self.flash = 0
        self.knock = 0
        self.dmg = 1
        self.xp = 0
        self.cacao = 0
        self.alive = True
        self.col = (10, 30, 50)
        self.home_y = y

    def rect(self):
        return (self.x + 8, self.y, 24, 12)

    def hit(self, dmg, from_x):
        return False

    def attack_rect(self):
        return None

    def update(self, g):
        self.timer += 1
        p = g.player
        room = g.room
        dx = p.cx - (self.x + 20)
        dy = p.cy - self.y
        if self.state == 0:
            self.x += 0.9 * self.face
            self.y = self.home_y + math.sin(self.timer * 0.03) * 10
            if self.x < 70 or self.x > 230:
                self.face = -self.face
            if p.wet and abs(dx) < 140:
                self.state = 1
                self.timer = 0
                g.audio.sfx_play("heartbeat", 2)
                g.mood.flash((80, 0, 0), 20)
            elif not p.wet and abs(dx) < 30 and 0 < -dy < 60 and self.timer > 90:
                self.state = 3
                self.timer = 0
                self.vy = -6.5
                g.audio.sfx_play("splash", 2)
        elif self.state == 1:
            d = math.sqrt(dx * dx + dy * dy) or 1
            sp = 2.2
            nx = self.x + dx / d * sp
            ny = self.y + dy / d * sp
            if room.water(nx + 20, ny + 6):
                self.x, self.y = nx, ny
            self.face = 1 if dx > 0 else -1
            if d < 22:
                self.state = 2
                self.timer = 0
            if not p.wet and self.timer > 30:
                self.state = 4
                self.timer = 0
        elif self.state == 2:
            if self.timer > 30:
                self.state = 4
                self.timer = 0
        elif self.state == 3:
            self.y += self.vy
            self.vy += 0.45
            if self.y > self.home_y and self.vy > 0:
                self.state = 4
                self.timer = 0
        else:
            self.y += (self.home_y - self.y) * 0.05
            if self.timer > 70:
                self.state = 0


class EProj:
    def __init__(self, kind, x, y, vx, vy, life=150, dmg=1):
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.life = life
        self.dmg = dmg
        self.r = 3 if kind in ("fire", "bubble", "wave", "bat") else 4

    def update(self, g):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.kind == "bubble":
            self.vy -= 0.01
            self.x += math.sin(self.life * 0.2) * 0.5
        elif self.kind == "rock":
            self.vy += 0.35
        elif self.kind == "orb":
            p = g.player
            dx, dy = p.cx - self.x, p.cy - self.y
            d = math.sqrt(dx * dx + dy * dy) or 1
            self.vx = self.vx * 0.97 + dx / d * 0.08
            self.vy = self.vy * 0.97 + dy / d * 0.08
        if self.x < -10 or self.x > 330 or self.y < -10 or self.y > 234:
            self.life = 0
        if self.kind in ("fire", "rock") and SOLID[g.room.at(self.x, self.y)]:
            self.life = 0

    def rect(self):
        r = self.r
        return (self.x - r, self.y - r, r * 2, r * 2)


class PProj:
    def __init__(self, kind, x, y, vx):
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.vx = vx
        self.vy = 0.0
        self.life = 60 if kind == "beam" else 40
        self.dmg = 4 if kind == "beam" else 1
        self.hits = set()

    def rect(self):
        if self.kind == "beam":
            return (self.x - 8, self.y - 6, 16, 12)
        return (self.x - 6, self.y - 2, 12, 5)


class Pickup:
    """kind: 'cacao' (value), 'life'."""

    def __init__(self, kind, x, y, value=1, vx=None, vy=None, static=False):
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.vx = (random.random() - 0.5) * 4 if vx is None else vx
        self.vy = -2 - random.random() * 3 if vy is None else vy
        self.value = value
        self.t = 0
        self.static = static
        self.life = 600

    def update(self, g):
        self.t += 1
        p = g.player
        if self.static:
            return
        dx, dy = p.cx - self.x, p.cy - self.y
        if self.t > 18 and dx * dx + dy * dy < 70 * 70:
            d = math.sqrt(dx * dx + dy * dy) or 1
            sp = min(7.0, 1.5 + self.t * 0.08)
            self.x += dx / d * sp
            self.y += dy / d * sp
            return
        self.vy = min(self.vy + 0.3, 4)
        nx, ny = self.x + self.vx, self.y + self.vy
        room = g.room
        if SOLID[room.at(nx, self.y)]:
            self.vx = -self.vx * 0.5
            nx = self.x
        if SOLID[room.at(nx, ny + 3)]:
            self.vy = -self.vy * 0.4 if abs(self.vy) > 1 else 0
            self.vx *= 0.7
            ny = self.y
        self.x, self.y = nx, ny
        self.life -= 1
