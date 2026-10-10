"""La-Fluff-Puff and the Jade Sun: game state machine and main loop."""
import gc
import math
import random
import time
from . import hw
from .hw import display, restore_bg, U, D, L, R, BA, BB, BX, BY, PLUS, MINUS, SA, SB, SX
from .audio import Audio
from .world import Room, T_RAIN, T_GATE, T_SEAL, T_WATER, COLS
from .player import Player, PW, PH, CHARGE_FULL
from . import gfx, sprites, ui, story, save, combat, intro
from .enemies import Enemy, Lurker, MARKER
from .bosses import BOSSES, Watcher
from .fx import FX, AMBIENCE
from .world_data import ROOMS, START_ROOM, START_POS

FRAME_MS = 40
PERF = False
CONFIRM = BB | BY
BACK = BA | BX | MINUS

TITLE, PROLOGUE, FORM, PLAY, DIALOG, ITEM, MAP, SHOP, DEATH, ENDING, INTRO = range(11)

ABILITIES = ("blade", "pearl", "dash", "feather", "spear")
ALL_FINDS = ABILITIES + ("heart1", "heart2", "heart3", "heart4", "l1", "l2", "l3", "l4", "l5", "l6",
                         "g_water", "g_jaguar", "g_sky", "g_stone", "shop_heart", "shop_edge")


class Game:
    def __init__(self):
        self.inp = hw.Input()
        self.mood = hw.Mood()
        self.audio = Audio()
        self.fx = FX()
        self.t = 0
        self.state = TITLE
        self.state_t = 0
        self.backlight = 1.0
        self.bl_flash = 0
        self.title_cursor = 0
        self.has_save = save.exists()
        self.skin = sprites.FluffSkin(random.randint(0, 7))
        self.player = None
        self.room = None
        self.watcher_chase = False
        self.banner_t = 999
        self.banner_text = ""
        self.banner_sub = None
        self.dialog = None
        self.after_dialog = None
        self.after_dialog_item = None
        self.resume_dialog = None
        self.pending_gate = 0
        self.pending_talk = 0
        self.hud_cached = None
        self.new_game()
        self.intro = intro.Intro(self)
        self.go(INTRO)

    # --- progress ---------------------------------------------------------
    def new_game(self):
        self.items = set()
        self.flags = {}
        self.broken = []
        self.visited = set()
        self.level = 1
        self.xp = 0
        self.cacao = 0
        self.play_time = 0
        self.shrine = (START_ROOM, START_POS[0], START_POS[1])
        self.hp = self.max_hp

    def has(self, k):
        return k in self.items

    def glyphs(self):
        return sum(1 for k in ("g_water", "g_jaguar", "g_sky", "g_stone") if k in self.items)

    @property
    def max_hp(self):
        n = 4 + sum(1 for k in ("heart1", "heart2", "heart3", "heart4", "shop_heart") if k in self.items)
        return n + (self.level >= 3) + (self.level >= 6) + (self.level >= 9)

    def attack(self):
        return 1 + self.has("shop_edge") + self.level // 4

    def xp_next(self):
        if self.level >= len(combat.XP_TABLE):
            return 0
        return combat.XP_TABLE[self.level] - combat.XP_TABLE[self.level - 1]

    def xp_into(self):
        return self.xp - combat.XP_TABLE[self.level - 1]

    def completion(self):
        return sum(1 for k in ALL_FINDS if k in self.items) * 100 // len(ALL_FINDS)

    def save_game(self):
        data = {
            "v": 1, "room": self.shrine[0], "x": self.shrine[1], "y": self.shrine[2],
            "items": list(self.items), "flags": self.flags, "broken": self.broken,
            "visited": list(self.visited), "level": self.level, "xp": self.xp, "cacao": self.cacao,
            "skin": self.skin.idx, "time": self.play_time, "vol": self.audio.vol_index,
        }
        save.write(data)
        self.has_save = True

    def load_game(self):
        d = save.load()
        if not d:
            return False
        self.new_game()
        self.items = set(d.get("items", ()))
        self.flags = d.get("flags", {})
        self.broken = d.get("broken", [])
        self.visited = set(d.get("visited", ()))
        self.level = d.get("level", 1)
        self.xp = d.get("xp", 0)
        self.cacao = d.get("cacao", 0)
        self.play_time = d.get("time", 0)
        self.skin.set(d.get("skin", 0))
        self.audio.vol_index = d.get("vol", 2)
        self.shrine = (d.get("room", START_ROOM), d.get("x", START_POS[0]), d.get("y", START_POS[1]))
        self.hp = self.max_hp
        return True

    # --- rooms ----------------------------------------------------------------
    def enter_room(self, rid, x, y, vx=0.0, vy=0.0, from_dir=None):
        prev = self.room
        chasing = self.watcher_chase
        broken = [int(b.split(":")[1]) for b in self.broken if b.split(":")[0] == rid]
        room = Room(rid, broken)
        self.room = room
        m = room.meta
        if self.has("pearl"):
            room.open_tiles(T_RAIN)
        if self.flags.get("gate_open"):
            room.open_tiles(T_GATE)
        p = self.player or Player(x, y)
        p.x, p.y, p.vx, p.vy = float(x), float(y), vx, vy
        p.safe = (p.x, p.y)
        p.events = []
        p.trail = []
        self.player = p
        self.enemies = []
        self.eprojs = []
        self.pprojs = []
        self.pickups = []
        self.items_here = []
        self.npcs = []
        self.lores = []
        self.shrine_pos = None
        self.torches = []
        self.boss = None
        self.boss_kind = None
        self.boss_spawn = None
        self.fx.clear()
        self.combo = 0
        self.combo_t = 0
        lvl = 1 if self.glyphs() >= 2 else 0
        npc_ids = list(m.get("npcs", ()))
        item_ids = list(m.get("items", ()))
        lore_ids = list(m.get("lore", ()))
        z_spawn = None
        for ch, c, r in room.spawns:
            px, py = c * 16, r * 16
            if ch in MARKER:
                self.enemies.append(Enemy(MARKER[ch], px, py, lvl))
            elif ch == "N":
                self.npcs.append([npc_ids.pop(0), px, py])
            elif ch == "D":
                self.npcs.append(["ek", px, py])
            elif ch == "i":
                iid = item_ids.pop(0)
                if not self.has(iid):
                    self.items_here.append([iid, px + 8, py + 8])
            elif ch == "L":
                self.lores.append([lore_ids.pop(0), px, py])
            elif ch == "P":
                self.shrine_pos = (px, py)
            elif ch == "T":
                self.torches.append((px, py))
            elif ch == "c":
                self.pickups.append(combat.Pickup("cacao", px + 8, py + 8, 1, 0, 0, True))
            elif ch == "K":
                self.boss_spawn = (px, py)
            elif ch == "Z":
                z_spawn = (px, py)
        b = m.get("boss")
        if b and not self.flags.get("boss_" + b):
            self.boss_kind = b
        if m.get("lurker") and not self.flags.get("boss_xoc"):
            self.enemies.append(Lurker(120, 150))
        self.watcher_chase = False
        if m.get("watcher") and not self.flags.get("watcher_dead"):
            if chasing and from_dir:
                wx = -24 if from_dir == "W" else (320 if from_dir == "E" else x)
                wy = y - 16 if from_dir in ("W", "E") else 160
                w = Watcher(wx, wy, "chase")
                w.emerge = 40
                self.boss = w
                self.watcher_chase = True
            elif z_spawn:
                self.boss = Watcher(z_spawn[0], z_spawn[1])
        elif chasing and prev and prev.meta.get("watcher"):
            self.fx.text(160, 90, "ESCAPED!", (120, 255, 170), 50, 2)
            self.audio.sfx_play("select")
            gain = 15
            combat.gain_xp(self, gain)
        self.surfaces = []
        for i in range(len(room.t)):
            if room.t[i] == T_WATER and (i < COLS or room.t[i - COLS] != T_WATER):
                if i >= COLS or room.nb_n:
                    self.surfaces.append(((i % COLS) * 16, (i // COLS) * 16))
        self.pal = gfx.bake(room, self.glyphs())
        self.rebake = False
        self.hud_cached = None
        amb = AMBIENCE[room.zone]
        if m.get("rain"):
            amb = "rain"
        self.fx.set_ambience(amb, room)
        self.mood.base = gfx.MOOD[room.zone]
        self.mood.override = (180, 0, 0) if self.watcher_chase else None
        self.audio.play_song("chase" if self.watcher_chase else m["music"])
        if rid not in self.visited:
            self.visited.add(rid)
        if not prev or prev.zone != room.zone:
            self.banner_text = story.ZONE_TITLES[room.zone]
            self.banner_sub = m["name"]
            self.banner_t = 0
        self.inp.set_pad_leds((1 << self.glyphs()) - 1)
        self.set_backlight(1.0)
        if rid == "A0" and self.glyphs() == 4 and not self.flags.get("gate_open"):
            self.pending_gate = 30
        if rid == START_ROOM and not self.has("blade"):
            self.pending_talk = 25
        gc.collect()

    def set_backlight(self, v):
        self.backlight = v
        display.set_backlight(v)

    def flash_backlight(self):
        display.set_backlight(1.0)
        self.bl_flash = 3

    def eclipse(self):
        self.set_backlight(0.45)
        self.fx.white(3)
        self.audio.sfx_play("thunder", 3)
        self.fx.kick(10)
        self.banner_text = "ECLIPSE"
        self.banner_sub = "Camazotz swallows the light!"
        self.banner_t = 0

    def watcher_alert(self):
        self.watcher_chase = True
        self.audio.sfx_play("alert", 3)
        self.audio.play_song("chase")
        self.mood.override = (180, 0, 0)
        self.fx.kick(3)

    def watcher_calm(self):
        self.watcher_chase = False
        self.audio.play_song(self.room.meta["music"])
        self.mood.override = None

    def hurt_player(self, from_x, dmg=1, power=1.0):
        p = self.player
        if not p.hurt(from_x, power):
            return False
        self.hp -= dmg
        self.combo = 0
        self.audio.sfx_play("hurt", 3)
        self.fx.kick(6, 3)
        self.fx.burst(p.cx, p.cy, (255, 120, 140), 10, 3, 16)
        self.mood.flash((255, 0, 0), 10)
        if self.hp <= 0:
            self.hp = 0
            self.go(DEATH)
            self.audio.play_song(None)
            self.audio.sfx_play("death", 4)
        return True

    # --- grants ---------------------------------------------------------------
    def grant(self, iid):
        self.items.add(iid)
        self.item_shown = iid
        self.go(ITEM)
        self.audio.music_on = False
        self.audio.sfx_play("glyph" if iid.startswith("g_") else "item", 4)
        self.fx.white(2, gfx.GOLD)
        self.mood.flash((255, 220, 80), 40)
        self.hp = self.max_hp
        self.inp.set_pad_leds((1 << self.glyphs()) - 1)
        combat.gain_xp(self, 20 if iid.startswith("g_") else 8)

    def talk(self, key, extra=None):
        lines = list(story.DIALOGUE[key]) if key in story.DIALOGUE else [("stone", story.LORE[key])]
        if extra:
            lines += extra
        self.dialog = ui.Dialogue(lines, self.skin, self._dialog_action)
        self.after_dialog = None
        self.go(DIALOG)

    def _dialog_action(self, act):
        if act.startswith("give:"):
            self.after_dialog_item = act[5:]
            return True
        if act == "shop":
            self.after_dialog = "shop"
        elif act == "watcher":
            self.after_dialog = "watcher"
        return False

    def go(self, st):
        self.state = st
        self.state_t = 0

    # --- title / intro ----------------------------------------------------------
    def _enter_title(self, rebake=True):
        self.go(TITLE)
        self.set_backlight(1.0)
        if rebake:
            intro.backdrop(False)
        self.fx.clear()
        self.fx.set_ambience("fireflies", None)
        self.audio.play_song("title", True)
        self.mood.base = (0, 60, 40)
        self.mood.override = None
        self.inp.set_pad_leds(0)

    def update_intro(self, inp):
        r = self.intro.update(inp)
        if r:
            if r == "skip":
                self.audio.sfx_play("select", 4)
            self.intro = None
            self._enter_title(r == "skip")

    def _start_play(self, rid, x, y):
        self.go(PLAY)
        self.audio.music_on = True
        self.after_dialog_item = None
        self.resume_dialog = None
        self.pending_gate = 0
        self.pending_talk = 0
        self.watcher_chase = False
        self.room = None
        self.player = None
        self.enter_room(rid, x, y)

    def update_title(self, inp):
        if self.has_save and inp.pressed & (U | D):
            self.title_cursor ^= 1
            self.audio.sfx_play("menu")
        if inp.pressed & (CONFIRM | PLUS):
            self.audio.sfx_play("select")
            if self.has_save and self.title_cursor == 0 and self.load_game():
                r, x, y = self.shrine
                self._start_play(r, x, y)
            else:
                self.new_game()
                self.page = 0
                self.shown = 0.0
                self.fx.clear()
                intro.prologue_bake(0)
                self.go(PROLOGUE)

    def update_prologue(self, inp):
        s = story.PROLOGUE[self.page]
        self.shown += 1.2
        if int(self.shown) % 3 == 0 and self.shown < len(s):
            self.audio.sfx_tone(500, 500, 1, 250)
        if inp.pressed & PLUS:
            self.page = len(story.PROLOGUE)
        elif inp.pressed & CONFIRM:
            if self.shown < len(s):
                self.shown = len(s)
            else:
                self.page += 1
                self.shown = 0.0
                if self.page == 3:
                    intro.prologue_bake(3)
                    self.fx.white(2)
                    self.fx.kick(8)
                    self.audio.sfx_play("boom", 3)
                    self.inp.set_pad_leds(15)
                elif self.page == 4:
                    self.inp.set_pad_leds(0)
        if self.page >= len(story.PROLOGUE):
            self.inp.set_pad_leds(0)
            self.form_i = 0
            self.form_speed = 1.0
            self.form_next = 0.0
            self.form_msg = 0
            self.go(FORM)

    def update_form(self, inp):
        t = self.state_t
        done = t > 80
        if not done:
            self.form_next -= 1
            if self.form_next <= 0:
                self.form_speed *= 1.07
                self.form_next = self.form_speed
                self.skin.set(self.skin.idx + 1)
                self.audio.sfx_play("drum")
            if t % 8 == 0:
                self.form_msg = (self.form_msg + 1) % len(story.FORM_MESSAGES)
        elif t == 81:
            self.audio.sfx_play("item", 4)
            self.fx.white(2)
            self.mood.flash((255, 220, 120), 30)
        if t > 120 and inp.pressed & CONFIRM:
            self._start_play(START_ROOM, START_POS[0], START_POS[1])

    # --- play -------------------------------------------------------------------
    def update_play(self, inp):
        p = self.player
        self.play_time += 1
        if inp.pressed & (PLUS | SA | SB):
            self.audio.sfx_play("menu")
            self.go(MAP)
            return
        if self.fx.stop > 0:
            self.fx.stop -= 1
            return
        if self.pending_talk:
            self.pending_talk -= 1
            if self.pending_talk == 0:
                self.flags["met_ceiba"] = True
                self.talk("ceiba_first")
                return
        if self.pending_gate:
            self.pending_gate -= 1
            if self.pending_gate == 0:
                self.flags["gate_open"] = True
                self.room.open_tiles(T_GATE)
                self.rebake = True
                self.audio.sfx_play("gate", 4)
                self.fx.kick(14)
                self.fx.white(3, gfx.JADE)
                self.talk("gate_open")
                return

        held, pressed, released = inp.held, inp.pressed, inp.released
        if pressed & U and self._interact():
            return
        p.update(held, pressed, released, self.room, self.has)
        self._player_events()
        combat.player_attacks(self)
        combat.update_pprojs(self)

        for e in self.enemies:
            if e.alive:
                e.update(self)
        self.enemies = [e for e in self.enemies if e.alive]
        self._boss_logic()
        combat.threats(self)
        combat.collect(self)
        if self.combo_t > 0:
            self.combo_t -= 1
            if self.combo_t == 0:
                self.combo = 0
        self._ambient_events()
        if self.rebake:
            self.pal = gfx.bake(self.room, self.glyphs())
            self.rebake = False
            self.hud_cached = None
        self._edges()

    def _player_events(self):
        p = self.player
        a = self.audio
        for ev in p.events:
            if isinstance(ev, tuple):
                if ev[0] == "break":
                    combat.break_tiles(self, ev[1], ev[2])
                continue
            if ev == "jump":
                a.sfx_play("jump")
                self.fx.burst(p.cx, p.y + PH, (220, 220, 200), 4, 1.2, 8, 0.05, 1)
            elif ev == "djump":
                a.sfx_play("djump")
                self.fx.ring(p.cx, p.y + PH, (120, 255, 170), 8, 2, 10)
            elif ev == "swim":
                a.sfx_play("bubble")
                self.fx.burst(p.cx, p.y, (180, 230, 255), 3, 1, 12, -0.05, 1)
            elif ev == "land":
                a.sfx_play("land")
                self.fx.burst(p.cx, p.y + PH, (200, 190, 170), 3, 1, 6, 0, 1)
            elif ev == "slash":
                a.sfx_play("slash")
            elif ev == "dash":
                a.sfx_play("dash")
                self.fx.burst(p.cx, p.cy, (255, 220, 120), 6, 2, 10, 0)
            elif ev == "splash":
                a.sfx_play("splash")
                self.fx.burst(p.cx, p.cy, (150, 210, 255), 10, 2.5, 16, 0.2)
            elif ev == "spike":
                if self.hurt_player(p.cx - p.face, 1):
                    if self.state == PLAY:
                        p.respawn_safe()
                        p.iframes = 40
            elif ev == "charged":
                a.sfx_play("charge")
                self.mood.flash((255, 200, 40), 6)
            elif ev == "beam":
                combat.fire(self, "beam")
            elif ev == "bolt":
                combat.fire(self, "bolt")
        p.events = []

    def _interact(self):
        p = self.player
        for n in self.npcs:
            kind, nx, ny = n
            if abs(p.cx - (nx + 8)) < 22 and abs(p.cy - (ny + 8)) < 28:
                self._talk_npc(kind)
                return True
        for lo in self.lores:
            lid, lx, ly = lo
            if abs(p.cx - (lx + 8)) < 16 and abs(p.cy - (ly + 8)) < 20:
                first = not self.has(lid)
                self.items.add(lid)
                self.talk(lid)
                if first:
                    combat.gain_xp(self, 5)
                    self.audio.sfx_play("select")
                return True
        sp = self.shrine_pos
        if sp and abs(p.cx - (sp[0] + 8)) < 18 and abs(p.cy - (sp[1] + 8)) < 20:
            self.hp = self.max_hp
            self.shrine = (self.room.id, sp[0] + 3, sp[1] + 1)
            self.save_game()
            self.audio.sfx_play("save", 3)
            self.fx.ring(sp[0] + 8, sp[1] + 4, (60, 230, 150), 16, 3, 20)
            self.mood.flash((0, 255, 140), 24)
            self.talk("shrine")
            return True
        fx = p.cx + p.face * 10
        for yy in (p.y + 2, p.y + PH - 2):
            t = self.room.at(fx, yy)
            key = {T_GATE: "gate_closed", T_RAIN: "rain_closed", T_SEAL: "seal_closed"}.get(t)
            if key:
                self.talk(key)
                return True
        return False

    def _talk_npc(self, kind):
        self.flags["met_" + kind] = True
        if kind == "ceiba":
            if not self.has("blade"):
                self.talk("ceiba_first")
            else:
                self.talk_hint("ceiba")
        elif kind == "ek":
            self.talk("ek")
        elif kind == "chaac":
            self.talk("chaac_first" if not self.has("pearl") else "chaac")
        elif kind == "balam":
            self.talk("balam_first" if not self.has("dash") else "balam")
        elif kind == "witz":
            self.talk("witz_first" if not self.has("spear") else "witz")

    def talk_hint(self, who):
        self.dialog = ui.Dialogue([(who, "Listen to the forest, little one..."), (who, story.hint(self))],
                                  self.skin, self._dialog_action)
        self.after_dialog = None
        self.go(DIALOG)

    def _boss_logic(self):
        p = self.player
        b = self.boss
        if self.boss_kind and not b and self.boss_spawn:
            ok = (p.ground or p.wet) and 56 < p.cx < 264
            if ok:
                self.room.shut_doors(True)
                self.rebake = True
                kx, ky = self.boss_spawn
                self.boss = BOSSES[self.boss_kind](kx, ky)
                self.audio.play_song("final" if self.boss_kind == "camazotz" else "boss")
                self.audio.sfx_play("roar", 3)
                self.fx.kick(8)
                self.banner_text = self.boss.name
                self.banner_sub = story.BOSS_LINES[self.boss_kind]
                self.banner_t = 0
                self.mood.override = (200, 30, 0)
            return
        if not b:
            return
        b.tick(self)
        if b.dying:
            if b.dying % 5 == 0:
                r = b.rect()
                self.fx.burst(r[0] + random.randint(0, int(r[2])), r[1] + random.randint(0, int(r[3])),
                              (255, 200, 90), 10, 3, 18)
                self.audio.sfx_tone(random.randint(80, 300), 40, 4, 2400, 2)
                self.fx.kick(5)
            if b.dying > 70:
                self._boss_defeated(b)

    def _boss_defeated(self, b):
        r = b.rect()
        cx, cy = r[0] + r[2] / 2, r[1] + r[3] / 2
        self.boss = None
        self.fx.white(3)
        self.fx.ring(cx, cy, (255, 240, 180), 24, 5, 24)
        self.mood.override = None
        combat.drop_loot(self, cx, cy, 16, 100)
        combat.gain_xp(self, 50)
        if isinstance(b, Watcher):
            self.flags["watcher_dead"] = True
            self.watcher_chase = False
            self.audio.play_song(self.room.meta["music"])
            gy = min(cy, 176)
            self.items_here.append([b.reward, cx, gy])
            return
        kind = self.boss_kind
        self.flags["boss_" + kind] = True
        self.boss_kind = None
        self.room.shut_doors(False)
        self.rebake = True
        if kind == "camazotz":
            self.flags["cleared"] = True
            self.save_game()
            self.page = 0
            self.shown = 0.0
            self.audio.play_song("ending", True)
            self.set_backlight(1.0)
            self.go(ENDING)
            return
        self.audio.play_song(self.room.meta["music"])
        rx = 160
        ry = 120 if self.room.has_water else 176
        self.items_here.append([b.reward, rx, ry])

    def _ambient_events(self):
        m = self.room.meta
        t = self.t
        if m.get("rain") and random.randint(0, 260) == 0:
            self.fx.white(1)
            self.flash_backlight()
            self.audio.sfx_play("thunder", 1)
        if self.room.zone == "cenote" and random.randint(0, 120) == 0:
            self.audio.sfx_play("drip", 0)
        hp_low = self.hp == 1 and self.max_hp > 2
        if hp_low and t % 30 == 0:
            self.mood.flash((255, 0, 0), 6)
            self.audio.sfx_play("heartbeat", 0)

    def _edges(self):
        p = self.player
        room = self.room
        cx, cy = p.cx, p.cy
        if cx < 0 and room.nb_w:
            self.enter_room(room.nb_w, p.x + 320, p.y, p.vx, p.vy, "E")
        elif cx >= 320 and room.nb_e:
            self.enter_room(room.nb_e, p.x - 320, p.y, p.vx, p.vy, "W")
        elif cy < 0 and room.nb_n:
            self.enter_room(room.nb_n, p.x, p.y + 224, p.vx, min(p.vy, -9.0), "S")
        elif cy >= 224 and room.nb_s:
            self.enter_room(room.nb_s, p.x, p.y - 224, p.vx, p.vy, "N")
        else:
            p.x = max(-PW / 2 + 1 if room.nb_w else 0, min(p.x, 320 - (PW / 2 + 1 if room.nb_e else PW)))

    # --- dialog / overlays ---------------------------------------------------
    def update_dialog(self, inp):
        d = self.dialog
        d.update(inp.pressed & (CONFIRM | U), self.audio)
        item = getattr(self, "after_dialog_item", None)
        if item:
            self.after_dialog_item = None
            self.resume_dialog = d
            self.grant(item)
            return
        if d.done:
            act = self.after_dialog
            self.after_dialog = None
            self.go(PLAY)
            if act == "shop":
                self.shop_cursor = 0
                self.go(SHOP)
            elif act == "watcher" and self.boss and isinstance(self.boss, Watcher):
                self.boss.go("alert")
                self.watcher_alert()

    def update_item(self, inp):
        if self.state_t > 30 and inp.pressed & CONFIRM:
            self.audio.music_on = True
            rd = self.resume_dialog
            self.resume_dialog = None
            if self.item_shown == "g_stone":
                self.talk("watcher_dead")
            elif rd:
                rd.resume()
                self.dialog = rd
                self.go(DIALOG)
            else:
                self.go(PLAY)

    def update_shop(self, inp):
        n = len(story.SHOP) + 1
        if inp.pressed & U:
            self.shop_cursor = (self.shop_cursor - 1) % n
            self.audio.sfx_play("menu")
        elif inp.pressed & D:
            self.shop_cursor = (self.shop_cursor + 1) % n
            self.audio.sfx_play("menu")
        elif inp.pressed & BACK:
            self.go(PLAY)
        elif inp.pressed & CONFIRM:
            if self.shop_cursor == n - 1:
                self.go(PLAY)
                return
            key, name, desc, cost = story.SHOP[self.shop_cursor]
            if key != "refill" and self.has(key):
                self.audio.sfx_play("tink")
            elif self.cacao < cost:
                self.audio.sfx_play("hurt")
                self.fx.text(160, 120, "Not enough cacao!", (255, 120, 120), 30)
            else:
                self.cacao -= cost
                if key == "refill":
                    self.hp = self.max_hp
                else:
                    self.items.add(key)
                    self.hp = self.max_hp
                self.audio.sfx_play("shop", 3)
                self.mood.flash((255, 200, 60), 12)
                self.fx.text(160, 120, name + "!", (255, 220, 120), 40)

    def update_map(self, inp):
        if self.state_t > 3 and inp.pressed & (PLUS | MINUS | CONFIRM | BA | SA | SB):
            self.go(PLAY)

    def update_death(self, inp):
        t = self.state_t
        if t > 50:
            self.set_backlight(max(0.0, 1.0 - (t - 50) / 20))
        if t > 72:
            self.hp = self.max_hp
            r, x, y = self.shrine
            self.audio.music_on = True
            self.watcher_chase = False
            self.room = None
            self.go(PLAY)
            self.enter_room(r, x, y)

    def update_ending(self, inp):
        if self.page < len(story.ENDING):
            s = story.ENDING[self.page]
            self.shown += 1.2
            if inp.pressed & CONFIRM:
                if self.shown < len(s):
                    self.shown = len(s)
                else:
                    self.page += 1
                    self.shown = 0.0
                    self.audio.sfx_play("menu")
        elif self.state_t > 60 and inp.pressed & CONFIRM:
            self._enter_title()

    # --- drawing ----------------------------------------------------------------
    def draw_world(self):
        dx, dy = self.fx.offset()
        restore_bg(dx, dy)
        t = self.t
        rect = display.rectangle
        if self.surfaces:
            hi = gfx.WATER_HI
            mid = self.pal.water
            for sx, sy in self.surfaces:
                y = sy + gfx.HUD
                o = int(math.sin(t * 0.12 + sx * 0.09) * 1.5)
                display.set_pen(mid)
                rect(sx, y, 16, 2)
                display.set_pen(hi)
                rect(sx + ((t // 3 + sx) % 12), y + o, 4, 1)
        for tx, ty in self.torches:
            y = ty + gfx.HUD
            f = (t + tx) % 6
            display.set_pen(gfx.ORANGE)
            display.circle(tx + 8, y + 3, 4 + (f > 3))
            display.set_pen(gfx.GOLD)
            display.circle(tx + 8, y + 2 - (f & 1), 2)
        sp = self.shrine_pos
        if sp:
            r = 3 + ((t >> 3) & 1)
            display.set_pen(gfx.JADE)
            display.circle(sp[0] + 8, sp[1] + gfx.HUD + 2, r)
            display.set_pen(gfx.WHITE)
            display.pixel(sp[0] + 7, sp[1] + gfx.HUD + 1)
            if abs(self.player.cx - sp[0] - 8) < 18:
                ui.prompt(sp[0] + 8, sp[1] + gfx.HUD - 8, t)
        for lid, lx, ly in self.lores:
            if not self.has(lid) and (t >> 4) & 1:
                display.set_pen(gfx.GOLD)
                display.rectangle(lx + 7, ly + gfx.HUD - 4, 2, 2)
            if abs(self.player.cx - lx - 8) < 16 and abs(self.player.cy - ly - 8) < 20:
                ui.prompt(lx + 8, ly + gfx.HUD - 6, t)
        for k in self.pickups:
            if k.kind == "cacao":
                sprites.draw_cacao(int(k.x), int(k.y) + gfx.HUD, t)
            else:
                sprites.draw_heart(int(k.x), int(k.y) + gfx.HUD - 2, gfx.RED, 3)
        for iid, x, y in self.items_here:
            sprites.draw_item(story.ITEM_ICON[iid], int(x), int(y) + gfx.HUD, t)
        for kind, nx, ny in self.npcs:
            talking = False
            sprites.draw_npc(kind, nx, ny + gfx.HUD, t, talking)
            if abs(self.player.cx - nx - 8) < 22 and abs(self.player.cy - ny - 8) < 28:
                ui.prompt(nx + 8, ny + gfx.HUD - (46 if kind == "witz" else 26), t)
        for e in self.enemies:
            if e.kind == "lurker":
                sprites.draw_lurker(e, t)
            else:
                sprites.draw_enemy(e, t)
        if self.boss:
            self.boss.draw(t)
        self.draw_player()
        for pr in self.pprojs:
            sprites.draw_proj(pr, t)
        for ep in self.eprojs:
            sprites.draw_proj(ep, t)
        self.fx.draw()
        self.fx.ambience(t)
        if self.fx.flash > 0:
            self.fx.flash -= 1
            display.set_pen(self.fx.flash_pen)
            rect(0, gfx.HUD, 320, 224)
        key = ui.hud_key(self)
        if key != self.hud_cached or dx or dy:
            ui.hud_clear()
            ui.hud(self)
            if not (dx or dy):
                hw.snapshot_rows(0, gfx.HUD - 1)
                self.hud_cached = key
            else:
                self.hud_cached = None
        if self.banner_t < 90:
            ui.banner(self.banner_text, self.banner_t, 90, self.banner_sub)
            self.banner_t += 1
        if self.boss and self.boss.name != "THE WATCHER":
            ui.boss_bar(self.boss)

    def draw_player(self):
        p = self.player
        t = self.t
        if p.trail:
            sprites.draw_trail(self.skin, p.trail)
        if p.iframes > 0 and p.dash_t == 0 and (t >> 1) & 1:
            return
        sx, sy = p.x, p.y + gfx.HUD
        sprites.draw_fluff(self.skin, sx, sy, p.face, p.anim, p.ground, p.vy, p.wet, 1, (t % 120) < 4)
        if p.atk_t > 3:
            sprites.draw_slash(sx, sy, p.atk_dir, p.face, p.atk_t)
        if p.charge > 2:
            full = p.charge >= CHARGE_FULL
            sprites.draw_charge(sx, sy, t, full)
            display.set_pen(gfx.GOLD if full else gfx.ORANGE)
            display.rectangle(int(sx) - 2, int(sy) - 22, int(14 * min(1.0, p.charge / CHARGE_FULL)), 2)

    def draw(self):
        st = self.state
        t = self.t
        if st == INTRO:
            self.intro.draw()
        elif st == TITLE:
            restore_bg()
            intro.sun(160, 74, t)
            ui.title(t, self.has_save, self.title_cursor)
            self.fx.draw_screen()
            self.fx.ambience(t)
        elif st == PROLOGUE:
            intro.prologue(self, min(self.page, len(story.PROLOGUE) - 1), self.shown, t)
            if self.fx.flash > 0:
                self.fx.flash -= 1
                display.set_pen(gfx.WHITE)
                display.clear()
        elif st == FORM:
            done = self.state_t > 80
            msg = ("Maya's La-Fluff-Puff is READY!" if done else story.FORM_MESSAGES[self.form_msg])
            ui.form(self.skin, msg, t, done)
            if self.fx.flash > 0:
                self.fx.flash -= 1
                display.set_pen(gfx.WHITE)
                display.clear()
            if done and self.state_t > 120 and (t >> 4) & 1:
                ui.center("press B", 214, 1, gfx.GREY, False)
        elif st == MAP:
            ui.map_screen(self, t)
        elif st == ENDING:
            ui.ending_scene(self.page, self.shown, t, self)
        else:
            self.draw_world()
            if st == DIALOG:
                self.dialog.draw(t)
            elif st == ITEM:
                ui.item_get(self.item_shown, self.state_t)
            elif st == SHOP:
                ui.shop(self, self.shop_cursor, t)
            elif st == DEATH:
                ui.death(self.state_t)
        display.update()

    # --- loop ---------------------------------------------------------------------
    def frame(self):
        inp = self.inp
        inp.poll()
        if inp.pressed & SX:
            v = self.audio.cycle_volume()
            self.audio.sfx_play("select", 4)
            self.fx.text(160, 60, "VOLUME %s" % ("OFF", "LOW", "MID", "HIGH")[v], (255, 255, 255), 30)
        st = self.state
        if st == INTRO:
            self.update_intro(inp)
            self.fx.update()
        elif st == TITLE:
            self.update_title(inp)
            self.fx.update()
        elif st == PROLOGUE:
            self.update_prologue(inp)
            self.fx.update()
        elif st == FORM:
            self.update_form(inp)
        elif st == PLAY:
            self.update_play(inp)
            self.fx.update()
        elif st == DIALOG:
            self.update_dialog(inp)
        elif st == ITEM:
            self.update_item(inp)
            self.fx.update()
        elif st == SHOP:
            self.update_shop(inp)
            self.fx.update()
        elif st == MAP:
            self.update_map(inp)
        elif st == DEATH:
            self.update_death(inp)
            self.fx.update()
        elif st == ENDING:
            self.update_ending(inp)
        if self.bl_flash > 0:
            self.bl_flash -= 1
            if self.bl_flash == 0:
                display.set_backlight(self.backlight)
        self.audio.tick()
        self.mood.tick()
        self.draw()
        self.t += 1
        self.state_t += 1

    def run(self):
        ticks_ms, ticks_diff, sleep_ms = time.ticks_ms, time.ticks_diff, time.sleep_ms
        work = 0
        worst = 0
        while True:
            t0 = ticks_ms()
            self.frame()
            dt = ticks_diff(ticks_ms(), t0)
            if PERF:
                work += dt
                worst = max(worst, dt)
                if self.t % 100 == 0:
                    print("state", self.state, "avg_ms", work // 100, "worst_ms", worst, "free", gc.mem_free())
                    work = worst = 0
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
                g.audio.silence()
                g.mood.off()
                g.inp.set_pad_leds(0)
            display.set_pen(0)
            display.clear()
            display.update()
        except Exception:
            pass
        hw.restore_clocks()
