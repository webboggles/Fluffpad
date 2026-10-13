"""Emulator module: scripted end-to-end exercise of every system with a simple combat bot.
Run: run_emu.py --module tools.scenario --frames 40000 --shots ..."""
from jade_sun import game as G, hw, save
from jade_sun.bosses import Watcher
from jade_sun.world_data import ROOMS, AT

LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print("[scenario]", s)


class Bot:
    def __init__(self, g):
        self.g = g
        self.script = []
        self.prev = 0
        self.auto = None

    def poll(self):
        inp = self.g.inp
        held = 0
        if self.script:
            held = self.script.pop(0)
        elif self.auto:
            held = self.auto()
        inp.pressed = held & ~self.prev
        inp.released = self.prev & ~held
        inp.held = held
        self.prev = held


def spot(rid, ch):
    """Standing position on the first marker ch in room rid."""
    for r, line in enumerate(ROOMS[rid]["map"]):
        c = line.find(ch)
        if c >= 0:
            return c * 16 + 3, (r + 1) * 16 - 14
    raise AssertionError("no %s in %s" % (ch, rid))


def spawn_floor(rid):
    from tools.fuzz import spawn_for
    return spawn_for(ROOMS[rid]["map"])


def arena_spot(rid):
    """Floor spot inside the boss trigger band (56 < cx < 264), water counts as open."""
    rows = ROOMS[rid]["map"]
    for c in (6, 5, 7, 4, 8, 13, 14, 12, 15):
        for r in range(12, 0, -1):
            if rows[r][c] in ".~" and rows[r + 1][c] in "#=%":
                return c * 16 + 3, (r + 1) * 16 - 14
    raise AssertionError("no arena floor in " + rid)


def room_with(key, val):
    for rid, m in ROOMS.items():
        if val in m.get(key, ()):
            return rid
    raise AssertionError("no room with %s %s" % (key, val))


def watcher_exit():
    """A Z room, a dread neighbour beside it, and a walkable spot on the shared edge."""
    for rid, m in sorted(ROOMS.items()):
        rows = m["map"]
        if "Z" not in "".join(rows):
            continue
        cx, cy = m["pos"]
        for dx, col, x0, x1 in ((-1, 0, 20, -6), (1, 19, 290, 316)):
            nb = AT.get((cx + dx, cy))
            if not nb or not ROOMS[nb].get("watcher"):
                continue
            for r in range(1, 13):
                if rows[r][col] != "#" and rows[r - 1][col] != "#" and rows[r + 1][col] in "#=%g":
                    return rid, nb, x0, x1, (r + 1) * 16 - 14
    raise AssertionError("no watcher room with a walkable side exit")


def run(g, n):
    for _ in range(n):
        g.frame()


def press(bot, g, bits, n=1, gap=2):
    for _ in range(n):
        bot.script += [bits] + [0] * gap
    run(g, (gap + 1) * n)


def until(g, cond, limit, label):
    for i in range(limit):
        if cond():
            return i
        g.frame()
    raise AssertionError("timeout: " + label)


def mash_until(bot, g, cond, limit, label, bits=hw.BB):
    for i in range(limit):
        if cond():
            return i
        if not bot.script:
            bot.script = [bits, 0, 0]
        g.frame()
    raise AssertionError("timeout: " + label)


def fighter(g, ranged=False):
    def ai():
        p = g.player
        b = g.boss
        if not b or b.dying:
            return 0
        r = b.rect()
        bx = r[0] + r[2] / 2
        by = r[1] + r[3] / 2
        dx = bx - p.cx
        bits = 0
        if abs(dx) > 18:
            bits |= hw.R if dx > 0 else hw.L
        if g.t % 6 == 0:
            bits |= hw.BY
            if by < p.cy - 30:
                bits |= hw.U
        if (by < p.cy - 20 or p.wet) and g.t % 9 == 0:
            bits |= hw.BB
        if ranged and g.t % 30 < 20:
            bits |= hw.BX
        return bits
    return ai


def main():
    save.wipe()
    g = G.Game()
    bot = Bot(g)
    g.inp.poll = bot.poll

    # intro skip -> title -> new quest -> prologue skip -> form
    mash_until(bot, g, lambda: g.state == G.TITLE, 2000, "intro skip")
    run(g, 10)
    press(bot, g, hw.BB)
    assert g.state == G.PROLOGUE
    press(bot, g, hw.PLUS)
    assert g.state == G.FORM, g.state
    run(g, 125)
    press(bot, g, hw.BB)
    assert g.state == G.PLAY and g.room.id == "A1"
    log("form ok, skin", g.skin.idx)

    # Ceiba auto dialogue and blade grant mid-dialogue
    until(g, lambda: g.state == G.DIALOG, 60, "ceiba talk")
    mash_until(bot, g, lambda: g.state == G.ITEM, 400, "blade item")
    assert g.has("blade")
    run(g, 32)
    press(bot, g, hw.BB)
    assert g.state == G.DIALOG, "dialog resumes after item"
    mash_until(bot, g, lambda: g.state == G.PLAY, 600, "ceiba done")
    log("blade ok, xp", g.xp)

    # shop: buy refill with cacao
    g.cacao = 200
    shop = next(r for r in sorted(ROOMS) if "D" in "".join(ROOMS[r]["map"]))
    if shop != g.room.id:
        g.enter_room(shop, *spot(shop, "D"))
    g.player.x, g.player.y = spot(shop, "D")
    run(g, 3)
    press(bot, g, hw.U)
    mash_until(bot, g, lambda: g.state == G.SHOP, 300, "shop open")
    press(bot, g, hw.BY)
    assert g.has("shop_heart"), "bought heart shard"
    press(bot, g, hw.D)
    press(bot, g, hw.BY)
    assert g.has("shop_edge") and g.cacao == 50, g.cacao
    press(bot, g, hw.BA)
    assert g.state == G.PLAY
    log("shop ok, max_hp", g.max_hp, "atk", g.attack())

    # lore and shrine save
    g.enter_room("A1", *spot("A1", "L"))
    run(g, 4)
    press(bot, g, hw.U)
    assert g.state == G.DIALOG and g.has("l1")
    mash_until(bot, g, lambda: g.state == G.PLAY, 300, "lore done")
    shrine = next(r for r in sorted(ROOMS) if r.startswith("A") and "P" in "".join(ROOMS[r]["map"]))
    g.enter_room(shrine, *spot(shrine, "P"))
    run(g, 4)
    press(bot, g, hw.U)
    assert save.exists(), "saved"
    mash_until(bot, g, lambda: g.state == G.PLAY, 200, "shrine done")
    log("lore + save ok")

    # map open / close
    press(bot, g, hw.PLUS)
    assert g.state == G.MAP
    run(g, 5)
    press(bot, g, hw.PLUS)
    assert g.state == G.PLAY
    log("map ok")

    # Chaac pearl
    chaac = room_with("npcs", "chaac")
    g.enter_room(chaac, *spot(chaac, "N"))
    run(g, 8)
    press(bot, g, hw.U)
    mash_until(bot, g, lambda: g.state == G.ITEM, 500, "pearl item")
    run(g, 32)
    mash_until(bot, g, lambda: g.state == G.PLAY, 500, "chaac done")
    assert g.has("pearl")
    log("pearl ok")

    # lurker bite in the trench
    lurk = next(r for r in sorted(ROOMS) if ROOMS[r].get("lurker"))
    g.enter_room(lurk, 112, 120)
    hp = g.hp
    g.player.x, g.player.y = 112, 140
    run(g, 120)
    log("lurker trench hp", hp, "->", g.hp)

    # bosses
    for boss, ranged in (("xoc", False), ("jaguar", False), ("eagle", False), ("camazotz", True)):
        rid = next(r for r in sorted(ROOMS) if ROOMS[r].get("boss") == boss)
        g.items |= {"dash", "feather", "spear"}
        g.enter_room(rid, *arena_spot(rid))
        bot.auto = fighter(g, ranged)
        g.hp = 99
        until(g, lambda: g.boss is not None, 200, rid + " boss spawn")
        name = g.boss.name
        states = set()
        for i in range(6000):
            if g.boss:
                states.add(g.boss.state)
                g.hp = 99
            if g.state != G.PLAY or not g.boss:
                break
            g.frame()
        bot.auto = None
        log(rid, name, "states", sorted(states), "state", g.state, "frames", i, "room", g.room.id)
        if rid == "E2":
            assert g.state == G.ENDING, "ending reached"
            break
        if g.state == G.PLAY and g.items_here:
            it = g.items_here[-1]
            g.player.x, g.player.y = it[1] - 5, it[2] - 7
        mash_until(bot, g, lambda: g.state == G.ITEM, 600, rid + " reward", 0)
        run(g, 32)
        press(bot, g, hw.BB)
        assert g.state == G.PLAY

    # ending -> title
    mash_until(bot, g, lambda: g.state == G.TITLE, 3000, "ending to title")
    log("ending ok")

    # continue from save, Watcher chase, spear kill
    press(bot, g, hw.BB)
    assert g.state == G.PLAY
    log("continue ok room", g.room.id, "items", len(g.items))
    g.flags.pop("watcher_dead", None)
    g.items.discard("g_stone")
    zr, nb, x0, x1, wy = watcher_exit()
    g.enter_room(zr, x0, wy)
    run(g, 3)
    assert isinstance(g.boss, Watcher)
    g.boss.go("alert")
    g.watcher_alert()
    g.hp = 99
    g.player.x, g.player.y = x0, wy
    run(g, 40)
    g.player.x, g.player.y, g.player.vx = x1, wy, (-3 if x1 < 0 else 3)
    run(g, 2)
    assert g.room.id == nb, (g.room.id, nb)
    assert isinstance(g.boss, Watcher) and g.boss.state == "chase", "watcher followed"
    log("watcher followed into", g.room.id)
    g.player.x, g.player.y = spawn_floor(g.room.id)
    w = g.boss
    w.x = g.player.x + (120 if g.player.x < 160 else -120)
    w.y, w.emerge = g.player.y + 14 - w.h, 0

    def charger():
        p = g.player
        p.face = 1 if w.x > p.x else -1
        g.hp = 99
        return hw.BX if g.t % 26 < 22 else 0
    bot.auto = charger
    until(g, lambda: g.boss is None or g.state != G.PLAY, 3000, "watcher killed")
    bot.auto = None
    log("watcher dead", g.flags.get("watcher_dead"))
    g.items_here[0][1:] = [g.player.cx, g.player.cy]
    run(g, 3)
    assert g.state == G.ITEM and g.item_shown == "g_stone"
    run(g, 32)
    press(bot, g, hw.BB)
    mash_until(bot, g, lambda: g.state == G.PLAY, 400, "watcher dead dialog")

    # gate
    g.flags.pop("gate_open", None)
    g.enter_room("A0", *spawn_floor("A0"))
    mash_until(bot, g, lambda: g.flags.get("gate_open") and g.state == G.PLAY, 600, "gate opens")
    log("gate ok")

    # death -> respawn at shrine
    g.hp = 1
    g.hurt_player(g.player.cx + 5, 1)
    assert g.state == G.DEATH
    until(g, lambda: g.state == G.PLAY, 200, "respawn")
    assert g.hp == g.max_hp
    log("death respawn ok at", g.room.id)
    log("ALL OK")
    raise SystemExit(0)
