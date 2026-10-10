"""Hit resolution, rewards, tile breaking."""
import random
from .world import T_CRACK, T_SEAL, SOLID, COLS, ROWS
from .enemies import overlap, Pickup, PProj
from .player import PW, PH

XP_TABLE = (0, 12, 30, 55, 90, 135, 190, 260, 340, 430)


def break_tiles(g, c, r, kinds=(T_CRACK,)):
    room = g.room
    if not (0 <= c < COLS and 0 <= r < ROWS):
        return 0
    kind = room.t[r * COLS + c]
    if kind not in kinds:
        return 0
    stack = [(c, r)]
    n = 0
    col = g.pal.raw[2] if kind == T_CRACK else (240, 190, 60)
    while stack:
        cc, rr = stack.pop()
        if not (0 <= cc < COLS and 0 <= rr < ROWS):
            continue
        i = rr * COLS + cc
        if room.t[i] != kind:
            continue
        room.t[i] = room.open_as[i]
        g.broken.append("%s:%d" % (room.id, i))
        g.fx.burst(cc * 16 + 8, rr * 16 + 8, col, 8, 3.5, 22, 0.25, 3)
        n += 1
        stack.extend(((cc + 1, rr), (cc - 1, rr), (cc, rr + 1), (cc, rr - 1)))
    if n:
        g.audio.sfx_play("break", 2)
        g.fx.kick(7, 3)
        g.rebake = True
        if kind == T_SEAL:
            g.audio.sfx_play("gate", 3)
            g.fx.text(160, 100, "SEAL BROKEN!", (255, 220, 120), 50, 2)
    return n


def gain_xp(g, n):
    g.xp += n
    while g.level < len(XP_TABLE) and g.xp >= XP_TABLE[g.level]:
        g.level += 1
        g.hp = g.max_hp
        g.audio.sfx_play("levelup", 3)
        g.fx.text(g.player.cx, g.player.y - 10, "LEVEL UP!", (255, 230, 90), 60, 2)
        g.fx.ring(g.player.cx, g.player.cy, (255, 230, 90), 18, 4, 20)
        g.mood.flash((255, 200, 0), 20)
        g.banner_text = "LEVEL %d" % g.level
        g.banner_sub = "Hearts mended. You feel stronger."
        g.banner_t = 0


def drop_loot(g, x, y, cacao, life_chance=12):
    for _ in range(cacao):
        g.pickups.append(Pickup("cacao", x, y, 1))
    if g.hp < g.max_hp and random.randint(0, 99) < life_chance:
        g.pickups.append(Pickup("life", x, y))


def hit_enemy(g, e, dmg, from_x, pogo=False):
    if e.armour:
        g.audio.sfx_play("tink")
        g.fx.burst(e.x + e.w / 2, e.y + e.h / 2, (200, 220, 255), 4, 2, 8)
        return
    g.combo += 1
    g.combo_t = 45
    killed = e.hit(dmg, from_x)
    cx, cy = e.x + e.w / 2, e.y + e.h / 2
    g.fx.text(cx, e.y - 4, str(dmg), (255, 255, 255), 18)
    if killed:
        e.alive = False
        mult = 1 + g.combo // 4
        gain = e.xp * mult
        g.fx.burst(cx, cy, e.col, 16, 3.5, 22)
        g.fx.ring(cx, cy, (255, 240, 200), 10, 3, 10)
        g.fx.kick(4, 4)
        g.audio.sfx_play("kill", 2)
        g.mood.flash((255, 255, 255), 3)
        drop_loot(g, cx, cy, e.cacao)
        gain_xp(g, gain)
        g.fx.text(cx, cy - 12, "+%d XP" % gain, (120, 255, 170), 30)
    else:
        g.fx.burst(cx, cy, (255, 255, 255), 6, 2.5, 10)
        g.fx.kick(2, 2)
        g.audio.sfx_play("hit")
    if g.combo >= 3:
        g.fx.text(g.player.cx, g.player.y - 18, "x%d COMBO" % g.combo, (255, 200, 60), 24)
    if pogo:
        g.player.pogo()


def hit_boss(g, b, dmg, from_x, beam=False, pogo=False):
    r = b.hit(dmg, from_x, beam)
    br = b.rect()
    cx, cy = br[0] + br[2] / 2, br[1] + br[3] / 2
    if r == 0:
        g.audio.sfx_play("tink")
        g.fx.burst(cx, cy, (220, 220, 255), 5, 2, 8)
        if pogo:
            g.player.pogo()
        return
    g.combo += 1
    g.combo_t = 45
    g.fx.text(cx, br[1] - 4, str(dmg), (255, 230, 120), 20, 2 if dmg > 2 else 1)
    g.fx.burst(cx, cy, (255, 255, 255), 8, 3, 12)
    g.fx.kick(3, 3)
    g.audio.sfx_play("hit", 2)
    if pogo:
        g.player.pogo()
    if r == 2:
        g.fx.kick(12, 8)
        g.audio.sfx_play("boom", 3)
        g.mood.flash((255, 255, 255), 20)


def player_attacks(g):
    p = g.player
    box = p.attack_box()
    if not box:
        return
    pogo = p.atk_dir == 2
    if not hasattr(p, "hit_ids"):
        p.hit_ids = set()
    if p.atk_t == 8:
        p.hit_ids = set()
    dmg = g.attack()
    for e in g.enemies:
        if e.alive and id(e) not in p.hit_ids and overlap(box, e.rect()):
            p.hit_ids.add(id(e))
            hit_enemy(g, e, dmg, p.cx, pogo)
            pogo = False
    b = g.boss
    if b and not b.dying and id(b) not in p.hit_ids:
        for r in b.hurt_rects():
            if overlap(box, r):
                p.hit_ids.add(id(b))
                hit_boss(g, b, dmg, p.cx, False, pogo)
                break
    if pogo and p.atk_dir == 2:
        y = box[1] + box[3] - 2
        if g.room.at(p.cx, y) == 5:
            p.pogo()
            g.audio.sfx_play("tink")


def fire(g, kind):
    p = g.player
    vx = 7.0 if kind == "bolt" else 9.0
    pr = PProj(kind, p.cx + p.face * 8, p.y + 6, vx * p.face)
    g.pprojs.append(pr)
    if kind == "beam":
        g.audio.sfx_play("beam", 2)
        g.fx.kick(4)
        g.mood.flash((255, 200, 60), 6)
        p.vx -= p.face * 2.5
    else:
        g.audio.sfx_play("bolt")


def update_pprojs(g):
    keep = []
    room = g.room
    for pr in g.pprojs:
        pr.x += pr.vx
        pr.life -= 1
        t = room.at(pr.x, pr.y)
        if pr.kind == "beam" and t in (T_CRACK, T_SEAL):
            break_tiles(g, int(pr.x) >> 4, int(pr.y) >> 4, (T_CRACK, T_SEAL))
            t = room.at(pr.x, pr.y)
        if SOLID[t] or pr.x < -10 or pr.x > 330 or pr.life <= 0:
            g.fx.burst(pr.x, pr.y, (255, 220, 120), 6 if pr.kind == "bolt" else 14, 2.5, 12)
            continue
        alive = True
        r = pr.rect()
        for e in g.enemies:
            if e.alive and id(e) not in pr.hits and overlap(r, e.rect()):
                pr.hits.add(id(e))
                hit_enemy(g, e, pr.dmg, pr.x)
                if pr.kind == "bolt":
                    alive = False
                    break
        b = g.boss
        if alive and b and not b.dying and id(b) not in pr.hits:
            for hr in b.hurt_rects():
                if overlap(r, hr):
                    pr.hits.add(id(b))
                    hit_boss(g, b, pr.dmg, pr.x, pr.kind == "beam")
                    if pr.kind == "bolt":
                        alive = False
                    break
        if alive:
            if pr.kind == "beam" and g.t & 1:
                g.fx.burst(pr.x, pr.y, (255, 230, 120), 1, 1, 8, 0)
            keep.append(pr)
    g.pprojs = keep


def threats(g):
    """Enemy contact, attacks and projectiles against the player."""
    p = g.player
    pr = p.rect()
    for e in g.enemies:
        if not e.alive:
            continue
        if overlap(pr, e.rect()) or (e.attack_rect() and overlap(pr, e.attack_rect())):
            if e.kind == "lurker" and not p.wet and e.state != 3:
                continue
            g.hurt_player(e.x + e.w / 2, e.dmg)
    b = g.boss
    if b and not b.dying and b.state != "intro":
        if b.state != "stagger":
            for r in b.hurt_rects():
                if overlap(pr, r):
                    if g.hurt_player(r[0] + r[2] / 2, b.contact, 1.6 if b.contact > 1 else 1.0) and b.name == "THE WATCHER":
                        b.go("gloat")
                        g.audio.sfx_play("roar", 3)
                    break
    keep = []
    for ep in g.eprojs:
        ep.update(g)
        if ep.life <= 0:
            continue
        if overlap(pr, ep.rect()):
            if g.hurt_player(ep.x, ep.dmg):
                g.fx.burst(ep.x, ep.y, (255, 160, 80), 6, 2, 10)
                continue
        keep.append(ep)
    g.eprojs = keep


def collect(g):
    p = g.player
    pr = (p.x - 4, p.y - 4, PW + 8, PH + 8)
    keep = []
    for k in g.pickups:
        k.update(g)
        if overlap(pr, (k.x - 4, k.y - 4, 8, 8)) and k.t > 6:
            if k.kind == "cacao":
                g.cacao += k.value
                g.audio.chime()
                g.fx.burst(k.x, k.y, (255, 200, 90), 3, 1.5, 8)
            else:
                g.hp = min(g.max_hp, g.hp + 1)
                g.audio.sfx_play("heart")
                g.fx.text(k.x, k.y - 6, "+1", (255, 120, 140), 24)
            continue
        if k.life > 0:
            keep.append(k)
    g.pickups = keep
    for it in g.items_here:
        iid, x, y = it
        if overlap(pr, (x - 8, y - 8, 16, 16)):
            g.items_here.remove(it)
            g.grant(iid)
            break
