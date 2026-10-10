"""Player physics: run, variable-height jump, coyote time, jump buffer, one-way planks."""
from micropython import const
from .hw import L, R, D
from .room import T_PLANK, T_SPIKE, SOLID

PW = const(10)
PH = const(14)
RUN = 3.2
GRAV = 0.75
MAX_FALL = 8.5
JUMP_V = -9.0
CUT_V = -3.0


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.face = 1
        self.ground = False
        self.coyote = 0
        self.jbuf = 0
        self.drop_t = 0
        self.anim = 0
        self.events = []

    @property
    def cx(self):
        return self.x + PW / 2

    @property
    def cy(self):
        return self.y + PH / 2

    def update(self, held, pressed, released, jump_key, room):
        ev = self.events
        self.anim += 1
        if self.coyote:
            self.coyote -= 1
        if self.jbuf:
            self.jbuf -= 1
        if self.drop_t:
            self.drop_t -= 1
        if pressed & jump_key:
            self.jbuf = 5

        if self.ground and held & D and self.jbuf and self._standing_on(room, T_PLANK):
            self.drop_t = 8
            self.jbuf = 0
            self.y += 2
            self.ground = False

        move = (1 if held & R else 0) - (1 if held & L else 0)
        target = move * RUN
        acc = 0.9 if self.ground else 0.6
        if self.vx < target:
            self.vx = min(target, self.vx + acc)
        elif self.vx > target:
            self.vx = max(target, self.vx - acc)
        if move:
            self.face = move
        self.vy = min(self.vy + GRAV, MAX_FALL)

        if self.jbuf and (self.ground or self.coyote):
            self.vy = JUMP_V
            self.jbuf = 0
            self.coyote = 0
            self.ground = False
            ev.append("jump")
        if released & jump_key and self.vy < CUT_V:
            self.vy = CUT_V

        was_ground = self.ground
        self._move_x(room, self.vx)
        self._move_y(room, self.vy)
        self.ground = self._on_floor(room)
        if self.ground:
            self.coyote = 0
            if not was_ground:
                ev.append("land")
        elif was_ground and self.vy >= 0:
            self.coyote = 4
        if self._on_spikes(room):
            ev.append("spike")

    def _on_spikes(self, room):
        y = self.y + PH - 1
        if room.at(self.x + 2, y) == T_SPIKE or room.at(self.x + PW - 3, y) == T_SPIKE:
            return (int(y) & 15) >= 6
        return False

    def _standing_on(self, room, kind):
        y = self.y + PH + 1
        return room.at(self.x + 1, y) == kind or room.at(self.x + PW - 2, y) == kind

    def _on_floor(self, room):
        if self.vy < 0:
            return False
        y = self.y + PH
        for px in (self.x + 1, self.x + PW - 2):
            t = room.at(px, y)
            if SOLID[t]:
                return True
            if t == T_PLANK and self.drop_t == 0 and (int(y) & 15) == 0:
                return True
        return False

    def _move_x(self, room, dx):
        if dx == 0:
            return
        nx = self.x + dx
        edge = nx + PW - 1 if dx > 0 else nx
        for py in (self.y + 1, self.y + PH / 2, self.y + PH - 2):
            if SOLID[room.at(edge, py)]:
                c = int(edge) >> 4
                nx = c * 16 - PW if dx > 0 else c * 16 + 16
                self.vx = 0.0
                break
        self.x = nx

    def _move_y(self, room, dy):
        if dy == 0:
            return
        ny = self.y + dy
        if dy > 0:
            edge = ny + PH
            old = self.y + PH
            for px in (self.x + 1, self.x + PW - 2):
                t = room.at(px, edge - 0.01)
                top = (int(edge - 0.01) >> 4) * 16
                if SOLID[t] or (t == T_PLANK and self.drop_t == 0 and old <= top + 0.5):
                    ny = top - PH
                    self.vy = 0.0
                    break
        else:
            for px in (self.x + 1, self.x + PW - 2):
                if SOLID[room.at(px, ny)]:
                    ny = ((int(ny) >> 4) + 1) * 16
                    self.vy = 0.0
                    break
        self.y = ny
