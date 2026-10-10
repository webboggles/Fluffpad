"""Player physics and actions. Pure logic: emits events for the game to react to."""
from micropython import const
from .world import T_PLANK, T_GRATE, T_SPIKE, T_CRACK, T_WATER, SOLID

U = const(1)
D = const(2)
L = const(4)
R = const(8)
K_DASH = const(16)
K_JUMP = const(32)
K_SPEAR = const(64)
K_ATK = const(128)

PW = const(10)
PH = const(14)
RUN = 3.2
GRAV = 0.75
MAX_FALL = 8.5
JUMP_V = -9.0
DJUMP_V = -8.0
CUT_V = -3.0
DASH_V = 8.5
DASH_T = const(7)
WADE = 1.5
SWIM = 2.8
CHARGE_FULL = const(18)


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
        self.double = False
        self.air_dash = False
        self.dash_t = 0
        self.dash_cd = 0
        self.drop_t = 0
        self.wet = False
        self.iframes = 0
        self.knock_t = 0
        self.atk_t = 0
        self.atk_cd = 0
        self.atk_dir = 0
        self.charge = 0
        self.bolt_cd = 0
        self.anim = 0
        self.safe = (self.x, self.y)
        self.events = []
        self.frozen = False
        self.trail = []

    # --- helpers ---------------------------------------------------------
    @property
    def cx(self):
        return self.x + PW / 2

    @property
    def cy(self):
        return self.y + PH / 2

    def rect(self):
        return (self.x, self.y, PW, PH)

    def attack_box(self):
        if self.atk_t < 4:
            return None
        if self.atk_dir == 1:
            return (self.x - 6, self.y - 18, PW + 12, 20)
        if self.atk_dir == 2:
            return (self.x - 6, self.y + PH - 2, PW + 12, 18)
        if self.face > 0:
            return (self.x + PW - 2, self.y - 4, 24, PH + 8)
        return (self.x - 22, self.y - 4, 24, PH + 8)

    def pogo(self):
        self.vy = -7.5
        self.double = True
        self.air_dash = False

    def hurt(self, from_x, power=1.0):
        if self.iframes > 0:
            return False
        self.iframes = 40
        self.knock_t = 8
        self.dash_t = 0
        self.vx = 3.6 * power * (1 if self.cx >= from_x else -1)
        self.vy = -4.5 * power
        return True

    def respawn_safe(self):
        self.x, self.y = self.safe
        self.vx = self.vy = 0.0
        self.dash_t = 0

    # --- update ----------------------------------------------------------
    def update(self, held, pressed, released, room, has):
        ev = self.events
        self.anim += 1
        for name in ("iframes", "knock_t", "atk_t", "atk_cd", "dash_cd", "drop_t", "bolt_cd", "coyote", "jbuf"):
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, v - 1)
        if self.frozen:
            held = pressed = released = 0

        wet = room.water(self.cx, self.cy)
        if wet != self.wet:
            self.wet = wet
            if abs(self.vy) > 1.5:
                ev.append("splash")
        pearl = has("pearl")
        move = (1 if held & R else 0) - (1 if held & L else 0)

        if pressed & K_JUMP:
            self.jbuf = 5

        # drop through planks
        if self.ground and held & D and self.jbuf and self._standing_on(room, T_PLANK):
            self.drop_t = 8
            self.jbuf = 0
            self.y += 2
            self.ground = False

        # dash
        if pressed & K_DASH and has("dash") and self.dash_cd == 0 and (self.ground or not self.air_dash or wet):
            self.dash_t = DASH_T
            self.dash_cd = 16
            if not self.ground:
                self.air_dash = True
            self.iframes = max(self.iframes, DASH_T + 2)
            if move:
                self.face = move
            ev.append("dash")

        if self.dash_t > 0:
            self.dash_t -= 1
            spd = DASH_V * (0.6 if wet and not pearl else 1.0)
            self.vx = self.face * spd
            self.vy = 0.0
            self.trail.append((self.x, self.y))
            if len(self.trail) > 4:
                self.trail.pop(0)
        else:
            if self.trail:
                self.trail.pop(0)
            if self.knock_t == 0:
                top = RUN if not wet else (SWIM if pearl else WADE)
                target = move * top
                acc = 0.9 if self.ground else 0.6
                if self.vx < target:
                    self.vx = min(target, self.vx + acc)
                elif self.vx > target:
                    self.vx = max(target, self.vx - acc)
                if move and self.atk_t == 0:
                    self.face = move
            if wet:
                g, mf = (0.3, 3.0) if pearl else (0.22, 2.2)
            else:
                g, mf = GRAV, MAX_FALL
            self.vy = min(self.vy + g, mf)

            # jumping / swimming
            if self.jbuf:
                if wet:
                    head_out = not room.water(self.cx, self.y - 4)
                    if head_out:
                        self.vy = -7.5
                        self.jbuf = 0
                        ev.append("jump")
                    elif pearl:
                        self.vy = -5.2
                        self.jbuf = 0
                        ev.append("swim")
                    elif self.ground:
                        self.vy = -3.4
                        self.jbuf = 0
                        ev.append("swim")
                elif self.ground or self.coyote:
                    self.vy = JUMP_V
                    self.jbuf = 0
                    self.coyote = 0
                    self.ground = False
                    ev.append("jump")
                elif self.double and has("feather"):
                    self.vy = DJUMP_V
                    self.double = False
                    self.jbuf = 0
                    ev.append("djump")
            if released & K_JUMP and self.vy < CUT_V and not wet:
                self.vy = CUT_V

        # attack
        if pressed & K_ATK and self.atk_cd == 0 and has("blade"):
            if held & U:
                self.atk_dir = 1
            elif held & D and not self.ground:
                self.atk_dir = 2
            else:
                self.atk_dir = 0
            self.atk_t = 8
            self.atk_cd = 11
            ev.append("slash")

        # spear
        if has("spear"):
            if held & K_SPEAR:
                self.charge += 1
                if self.charge == CHARGE_FULL:
                    ev.append("charged")
            if released & K_SPEAR:
                if self.charge >= CHARGE_FULL:
                    ev.append("beam")
                elif self.bolt_cd == 0:
                    ev.append("bolt")
                    self.bolt_cd = 8
                self.charge = 0

        was_ground = self.ground
        self._move_x(room, self.vx)
        self._move_y(room, self.vy)
        self.ground = self._on_floor(room)
        if self.ground:
            self.double = True
            self.air_dash = False
            self.coyote = 0
            if not was_ground and self.vy >= 0:
                ev.append("land")
            if self.anim % 6 == 0 and not self._hazard(room):
                c = room.at(self.cx, self.y + PH + 1)
                if c != T_CRACK and c != T_PLANK:
                    self.safe = (self.x, self.y)
        elif was_ground and self.vy >= 0:
            self.coyote = 4
        if wet:
            self.double = True
            self.air_dash = False

        if self._hazard(room):
            ev.append("spike")

    def _hazard(self, room):
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
            if (t == T_GRATE or (t == T_PLANK and self.drop_t == 0)) and (int(y) & 15) == 0:
                return True
        return False

    def _move_x(self, room, dx):
        if dx == 0:
            return
        nx = self.x + dx
        edge = nx + PW - 1 if dx > 0 else nx
        for py in (self.y + 1, self.y + PH / 2, self.y + PH - 2):
            t = room.at(edge, py)
            if SOLID[t]:
                if t == T_CRACK and self.dash_t > 0:
                    self.events.append(("break", int(edge) >> 4, int(py) >> 4))
                    continue
                c = int(edge) >> 4
                nx = c * 16 - PW if dx > 0 else c * 16 + 16
                self.vx = 0.0
                if self.dash_t > 0:
                    self.dash_t = 0
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
                if SOLID[t] or ((t == T_GRATE or (t == T_PLANK and self.drop_t == 0)) and old <= top + 0.5):
                    ny = top - PH
                    self.vy = 0.0
                    break
        else:
            edge = ny
            for px in (self.x + 1, self.x + PW - 2):
                if SOLID[room.at(px, edge)]:
                    ny = ((int(edge) >> 4) + 1) * 16
                    self.vy = 0.0
                    break
        self.y = ny
