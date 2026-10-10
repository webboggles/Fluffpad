"""Boss fights and story flow on the desktop emulator.

Run:
  .venv/bin/python emulator/run_emu.py \\
    --module tools.boss_test --frames 30000 --seed 1 \\
    --cwd /tmp/jade_boss_cwd --out games/jade_sun/tools/out/boss   (from software/)
"""
import json
import os
import traceback
from pathlib import Path

import emu_state
from jade_sun import combat, hw, save, story
from jade_sun import game as G
from jade_sun.bosses import Watcher
from jade_sun.hw import display
from jade_sun.world import T_GATE, T_SHUT

OUT = Path(__file__).resolve().parent / "out" / "boss"
GLYPHS = ("g_water", "g_jaguar", "g_sky", "g_stone")
ABILITIES = ("blade", "pearl", "dash", "feather", "spear")
SHOTS = []
RESULTS = []


def shot(name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    display.image.copy().save(path)
    SHOTS.append(str(path))
    print("shot %s" % path, flush=True)


def step(g, names=(), god=False, place=False):
    if place and g.boss and not g.boss.dying:
        _place_for_hit(g)
    emu_state.buttons.clear()
    emu_state.buttons.update(names)
    if god and g.state == G.PLAY and g.player:
        g.hp = g.max_hp
    g.frame()


def boot(items=(), room="A1", x=100, y=178, flags=None):
    save.wipe()
    g = G.Game()
    g.items |= set(items)
    if flags:
        g.flags.update(flags)
    g._start_play(room, x, y)
    return g


def led_word(glyphs):
    word = 0xFFFF
    for i, bit in enumerate(hw._LED_BITS):
        if glyphs > i:
            word &= ~bit
    return word


def assert_led(g, glyphs):
    expect = led_word(glyphs)
    got = g.inp._led_word
    assert got == expect, "led word 0x%04X expected 0x%04X glyphs=%s" % (got & 0xFFFF, expect, glyphs)
    lo, hi = g.inp.i2c._regs[2], g.inp.i2c._regs[3]
    assert lo == (expect & 0xFF) and hi == ((expect >> 8) & 0xFF), (lo, hi, expect)


def doors_shut(g):
    assert g.room.doors, "room %s has no boss doors" % g.room.id
    bad = [i for i in g.room.doors if g.room.t[i] != T_SHUT]
    assert not bad, "doors not shut %s" % bad


def doors_open(g):
    bad = [i for i in g.room.doors if g.room.t[i] == T_SHUT]
    assert not bad, "doors still shut %s" % bad


def dialog_text(g):
    parts = []
    for who, body in g.dialog.pages:
        if who == "!":
            parts.append(body)
        else:
            parts.append(" ".join(body))
    return " ".join(parts)


def bot_names(g):
    names = set()
    b = g.boss
    p = g.player
    if g.state != G.PLAY or not b or b.dying or not p:
        return names
    rect = b.rect()
    bx = rect[0] + rect[2] / 2
    by = rect[1] + rect[3] / 2
    if abs(bx - p.cx) > 14:
        names.add("R" if bx > p.cx else "L")
    if g.t % 6 == 0:
        names.add("Y")
    if by < p.cy - 12 and g.t % 10 == 0:
        names.add("B")
    return names


def _place_for_hit(g):
    b = g.boss
    p = g.player
    rect = b.rect()
    if rect[0] > 48:
        p.x = rect[0] - 16
        p.face = 1
    else:
        p.x = rect[0] + rect[2] + 2
        p.face = -1
    p.y = rect[1]
    p.vx = 0.0
    p.vy = 0.0
    p.x = max(2.0, min(p.x, 300.0))
    p.y = max(4.0, min(p.y, 200.0))


def press_at(g, x, y, btn):
    g.player.x = float(x)
    g.player.y = float(y)
    g.player.vx = 0.0
    g.player.vy = 0.0
    step(g, (btn,))


def drive_grant_dialog(g, item_id, limit=900, shot_name=None):
    """Mash confirm through dialogue, including an ITEM interrupt, back to PLAY."""
    saw = False
    pictured = False
    for i in range(limit):
        if g.state == G.ITEM and getattr(g, "item_shown", None) == item_id:
            saw = True
            assert item_id in g.items, item_id
            if shot_name and not pictured:
                shot(shot_name)
                pictured = True
            for _ in range(90):
                if g.state != G.ITEM:
                    break
                step(g, ("B",) if g.state_t > 30 else ())
            else:
                raise AssertionError("stuck on ITEM for %s" % item_id)
            assert g.state == G.DIALOG, "after %s item, state %s (wanted DIALOG)" % (item_id, g.state)
        elif g.state == G.PLAY and saw:
            assert item_id in g.items
            return
        else:
            step(g, ("B",) if i % 3 == 0 else ())
    raise AssertionError("dialog did not finish item=%s state=%s saw_item=%s" % (item_id, g.state, saw))


def confirm_hit(g, shot_name=None):
    pictured = False
    assisted = False
    start = g.boss.hp
    for i in range(900):
        b = g.boss
        if b is None or g.state != G.PLAY:
            raise AssertionError("fight ended before a real hit state=%s" % g.state)
        if not pictured and shot_name and b.state != "intro":
            shot(shot_name)
            pictured = True
        if b.hp < start:
            return {"from": start, "to": b.hp, "frame": i, "assist": assisted, "state": b.state}
        assist = i > 160 and b.state != "intro"
        if assist:
            assisted = True
        names = {"Y"} if assist and i % 12 == 0 else (set() if assist else bot_names(g))
        step(g, names, god=True, place=assist)
    b = g.boss
    raise AssertionError(
        "no player damage hp=%s state=%s p=(%.0f,%.0f) b=(%.0f,%.0f)"
        % (b.hp, b.state, g.player.x, g.player.y, b.x, b.y)
    )


def kill_and_animate(g):
    b = g.boss
    if b and not b.dying:
        combat.hit_boss(g, b, max(1, b.hp), g.player.cx)
    peak = 0
    for _ in range(140):
        if g.boss is None:
            break
        peak = max(peak, g.boss.dying)
        step(g, (), god=True)
    else:
        raise AssertionError("death anim stuck dying=%s" % g.boss.dying)
    # _boss_defeated runs in the same tick that increments dying from 70 to 71,
    # so the last value observable on the live boss is 70.
    assert peak >= 70, "death anim peak %s" % peak
    return peak


def pickup(g, reward, shot_name=None):
    if g.state == G.ITEM and g.item_shown == reward:
        pass
    else:
        assert any(it[0] == reward for it in g.items_here), "reward %s not in %s" % (reward, g.items_here)
        for i in range(320):
            if g.state == G.ITEM:
                break
            iid, x, y = g.items_here[0]
            assert iid == reward
            p = g.player
            names = set()
            if x > p.cx + 4:
                names.add("R")
            elif x < p.cx - 4:
                names.add("L")
            if p.wet and y < p.cy - 8 and i % 7 == 0:
                names.add("B")
            step(g, names, god=True)
        else:
            iid, x, y = g.items_here[0]
            for _ in range(10):
                if g.state == G.ITEM:
                    break
                g.player.x = x - 5
                g.player.y = y - 7
                g.player.vx = g.player.vy = 0.0
                step(g, (), god=True)
    assert g.state == G.ITEM and g.item_shown == reward, (g.state, getattr(g, "item_shown", None))
    assert reward in g.items
    if shot_name:
        shot(shot_name)
    for _ in range(90):
        if g.state != G.ITEM:
            break
        step(g, ("B",) if g.state_t > 30 else ())
    else:
        raise AssertionError("stuck on reward ITEM")


def run_boss(kind, room, x, y, items, shot_name, reward=None, flags=None, ending=False):
    g = boot(items, room, x, y, flags)
    for _ in range(100):
        if g.boss is not None:
            break
        step(g, god=True)
    else:
        p = g.player
        raise AssertionError(
            "no boss ground=%s wet=%s cx=%.1f cy=%.1f" % (p.ground, p.wet, p.cx, p.cy)
        )
    assert g.boss_kind == kind, g.boss_kind
    doors_shut(g)
    info = confirm_hit(g, shot_name)
    eclipse = None
    if kind == "camazotz":
        b = g.boss
        assert b and not b.dying, "camazotz died before phase 3"
        if b.hp > 13:
            combat.hit_boss(g, b, b.hp - 13, g.player.cx)
        assert g.boss and g.boss.phase() == 3 and not g.boss.dying, (
            "phase %s hp %s dying %s" % (g.boss.phase() if g.boss else None, g.boss.hp if g.boss else None, g.boss.dying if g.boss else None)
        )
        eclipse = False
        for _ in range(25):
            if g.boss is None:
                break
            step(g, (), god=True)
            if g.boss and g.boss.eclipse:
                eclipse = True
                shot("camazotz_eclipse.png")
                break
        assert eclipse, "eclipse missing hp=%s backlight=%s banner=%s" % (
            g.boss.hp if g.boss else None, g.backlight, g.banner_text
        )
        assert g.backlight == 0.45, g.backlight
        assert g.banner_text == "ECLIPSE", g.banner_text
    peak = kill_and_animate(g)
    assert g.flags.get("boss_" + kind) is True, g.flags
    doors_open(g)
    detail = "real %s->%s frame %s assist=%s dying>%s" % (
        info["from"], info["to"], info["frame"], info["assist"], peak
    )
    if ending:
        assert g.state == G.ENDING, g.state
        assert g.flags.get("cleared") is True
        assert_led(g, 4)
        seen = set()
        pictured = False
        for i in range(900):
            seen.add(g.page)
            if g.state == G.TITLE:
                break
            if g.page >= len(story.ENDING) and not pictured:
                shot("ending.png")
                pictured = True
            step(g, ("B",) if i % 3 == 0 else ())
        else:
            raise AssertionError("ending timeout page=%s state_t=%s state=%s" % (g.page, g.state_t, g.state))
        assert g.state == G.TITLE
        assert set(range(len(story.ENDING) + 1)) <= seen, sorted(seen)
        return detail + " ending pages %s" % sorted(seen)
    led_before = led_word(0 if reward not in GLYPHS else g.glyphs() - (1 if reward in g.items else 0))
    assert g.state == G.PLAY, g.state
    glyphs_before = g.glyphs() - (1 if reward in g.items else 0)
    pickup(g, reward, "glyph_item.png" if reward == "g_water" else None)
    assert g.state == G.PLAY, "after B state %s" % g.state
    assert reward in g.items
    assert_led(g, g.glyphs())
    assert g.inp._led_word != led_before
    assert g.glyphs() == glyphs_before + 1
    return detail + " %s led 0x%04X" % (reward, g.inp._led_word)


def check(name, fn):
    print("RUN " + name, flush=True)
    try:
        detail = fn() or ""
    except Exception as exc:
        RESULTS.append((name, "FAIL", exc, traceback.format_exc()))
        print("FAIL " + name, flush=True)
        traceback.print_exc()
    else:
        RESULTS.append((name, "PASS", detail, ""))
        print("PASS " + name + (" | " + detail if detail else ""), flush=True)


def check_ceiba():
    g = boot((), "A1", 100, 178)
    for _ in range(50):
        if g.state == G.DIALOG:
            break
        step(g)
    else:
        raise AssertionError("ceiba_first did not start state=%s" % g.state)
    assert "met_ceiba" in g.flags
    drive_grant_dialog(g, "blade", shot_name="ceiba_blade.png")
    assert "blade" in g.items and g.state == G.PLAY


def check_shop():
    g = boot(("blade",), "A1", 250, 176)
    g.cacao = 80
    press_at(g, 250, 176, "U")
    assert g.state == G.DIALOG, "ek did not talk state=%s" % g.state
    for i in range(200):
        if g.state == G.SHOP:
            break
        step(g, ("B",) if i % 3 == 0 else ())
    else:
        raise AssertionError("shop did not open state=%s text=%s" % (g.state, dialog_text(g)[:80]))
    step(g)
    before = g.cacao
    step(g, ("B",))
    assert "shop_heart" in g.items, g.items
    assert g.cacao == before - 60, g.cacao
    return "cacao %s->%s" % (before, g.cacao)


def check_shrine_continue():
    g = boot(("blade",), "A1", 160, 176)
    g.cacao = 77
    g.flags["proved"] = 1
    press_at(g, 160, 176, "U")
    assert g.state == G.DIALOG, g.state
    assert "remembered" in dialog_text(g)
    path = os.path.join(os.getcwd(), save.PATH)
    assert save.exists() and os.path.isfile(path), path
    data = json.loads(open(path).read())
    assert data["cacao"] == 77, data.get("cacao")
    assert "blade" in data["items"]
    assert data["room"] == "A1"
    assert data["flags"].get("proved") == 1
    g.cacao = 0
    g.items.clear()
    g.flags.clear()
    g._enter_title()
    assert g.state == G.TITLE and g.has_save and g.title_cursor == 0
    step(g, ("B",))
    assert g.state == G.PLAY, g.state
    assert g.room.id == "A1", g.room.id
    assert g.cacao == 77, g.cacao
    assert "blade" in g.items
    assert g.flags.get("proved") == 1
    return path


def check_chaac():
    g = boot(("blade",), "B2", 30, 78)
    press_at(g, 30, 78, "U")
    assert g.state == G.DIALOG, "chaac state=%s" % g.state
    drive_grant_dialog(g, "pearl")
    assert "pearl" in g.items


def check_balam():
    g = boot(("blade",), "C4", 240, 34)
    assert isinstance(g.boss, Watcher), type(g.boss)
    press_at(g, 240, 34, "U")
    assert g.state == G.DIALOG, g.state
    saw = False
    for i in range(900):
        if g.state == G.ITEM and g.item_shown == "dash":
            saw = True
            assert "dash" in g.items
            for _ in range(90):
                if g.state != G.ITEM:
                    break
                step(g, ("B",) if g.state_t > 30 else ())
            assert g.state == G.DIALOG, g.state
        elif g.state == G.PLAY and saw:
            break
        else:
            step(g, ("B",) if i % 3 == 0 else ())
    else:
        raise AssertionError("balam dialog state=%s saw=%s" % (g.state, saw))
    assert "dash" in g.items
    assert isinstance(g.boss, Watcher)
    assert g.boss.state == "alert", g.boss.state
    assert g.audio.song_name == "chase", g.audio.song_name
    assert g.watcher_chase is True
    for _ in range(30):
        step(g, god=True)
    assert g.boss.state == "chase", g.boss.state
    assert g.audio.song_name == "chase"
    return "alert then chase"


def check_witz():
    g = boot(("blade",), "D4", 190, 176)
    press_at(g, 190, 176, "U")
    assert g.state == G.DIALOG, g.state
    drive_grant_dialog(g, "spear")
    assert "spear" in g.items


def check_watcher_beam():
    g = boot(("blade", "spear"), "C3", 80, 178)
    assert isinstance(g.boss, Watcher)
    w = g.boss
    hits = []
    orig = w.hit

    def wrapped(dmg, from_x, beam=False):
        result = orig(dmg, from_x, beam=beam)
        if beam:
            hits.append(result)
        return result

    w.hit = wrapped
    for n in range(3):
        for _ in range(80):
            if w.state != "stagger" and g.fx.stop == 0 and not w.dying:
                break
            step(g, (), god=True)
        before = w.hp
        for _ in range(20):
            g.player.x, g.player.y = 80.0, 178.0
            g.player.vx = g.player.vy = 0.0
            g.player.face = 1
            w.x, w.y = 150.0, 162.0
            w.vx = w.vy = 0.0
            step(g, ("X",), god=True)
        assert g.player.charge >= 18, g.player.charge
        step(g, (), god=True)
        assert any(pr.kind == "beam" for pr in g.pprojs) or w.hp < before or w.dying, "no beam"
        for _ in range(40):
            if w.hp < before or w.dying or g.boss is None:
                break
            step(g, (), god=True)
        assert w.hp < before or (g.boss is None), "beam %s did not damage hp %s" % (n, before)
    assert [r for r in hits if r] == [1, 1, 2], hits
    peak = 0
    for _ in range(140):
        if g.boss is None:
            break
        peak = max(peak, g.boss.dying)
        step(g, (), god=True)
    else:
        raise AssertionError("watcher death stuck")
    assert peak >= 70, peak
    assert g.flags.get("watcher_dead") is True
    shot("watcher_dead.png")
    pickup(g, "g_stone")
    assert g.state == G.DIALOG, "after g_stone B, state %s" % g.state
    assert "Watcher crumbles" in dialog_text(g), dialog_text(g)
    for i in range(400):
        if g.state == G.PLAY:
            break
        step(g, ("B",) if i % 3 == 0 else ())
    else:
        raise AssertionError("watcher_dead dialog state=%s" % g.state)
    assert "g_stone" in g.items
    assert_led(g, g.glyphs())
    return "beam hits %s led 0x%04X" % (hits, g.inp._led_word)


def check_watcher_block():
    g = boot(("blade",), "C4", 200, 178)
    w = g.boss
    assert isinstance(w, Watcher)
    hp = w.hp
    result = w.hit(1, g.player.cx, False)
    assert result == 0 and w.hp == hp, (result, w.hp)
    before = g.hp
    g.player.iframes = 0
    g.player.x = w.x + 2
    g.player.y = w.y + 4
    g.player.vx = g.player.vy = 0.0
    step(g)
    touched = g.hp
    assert touched < before, "contact hp %s -> %s p=%s w=%s" % (before, touched, g.player.rect(), w.rect())
    for _ in range(15):
        if g.fx.stop == 0:
            break
        step(g, (), god=True)
    calls = []
    orig = w.hit

    def wrapped(dmg, from_x, beam=False):
        result = orig(dmg, from_x, beam=beam)
        calls.append((dmg, beam, result))
        return result

    w.hit = wrapped
    # Cols 4-7 of C4's floor are spikes; stand on the rock at col 8+.
    for i in range(10):
        g.player.x, g.player.y = 130.0, 178.0
        g.player.face = 1
        g.player.vx = g.player.vy = 0.0
        g.player.atk_cd = 0
        w.x, w.y = 150.0, 162.0
        w.vx = 0.0
        step(g, ("Y",) if i == 0 else (), god=True)
    assert w.hp == hp, w.hp
    assert any((not beam) and result == 0 for _dmg, beam, result in calls), calls
    return "hit()=0 contact %s->%s slash %s" % (before, touched, calls)


def check_gate():
    g = boot(GLYPHS, "A0", 40, 178)
    assert g.glyphs() == 4
    assert g.pending_gate == 30, g.pending_gate
    assert any(t == T_GATE for t in g.room.t)
    for _ in range(45):
        if g.flags.get("gate_open") and g.state == G.DIALOG:
            break
        step(g)
    else:
        raise AssertionError("gate pending=%s flag=%s state=%s" % (g.pending_gate, g.flags.get("gate_open"), g.state))
    assert not any(t == T_GATE for t in g.room.t)
    assert "Sun Gate" in dialog_text(g), dialog_text(g)
    shot("gate_open.png")
    return "gate tiles opened"


def main():
    print("cwd %s" % os.getcwd(), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    check("A1 ceiba_first grants blade then resumes", check_ceiba)
    check("A1 ek shop purchase", check_shop)
    check("A1 shrine save and TITLE continue", check_shrine_continue)
    check("B2 chaac grants pearl", check_chaac)
    check("C4 balam grants dash and alerts watcher", check_balam)
    check("D4 witz grants spear", check_witz)
    check("B4 xoc", lambda: run_boss(
        "xoc", "B4", 160, 96, ("blade", "pearl"), "xoc_fight.png", "g_water"))
    check("C2 jaguar", lambda: run_boss(
        "jaguar", "C2", 150, 178, ("blade", "pearl", "dash"), "jaguar_fight.png", "g_jaguar"))
    check("D3 eagle", lambda: run_boss(
        "eagle", "D3", 150, 178, ("blade", "pearl", "dash", "feather"), "eagle_fight.png", "g_sky"))
    check("E2 camazotz eclipse and ending", lambda: run_boss(
        "camazotz", "E2", 150, 178,
        ABILITIES + GLYPHS, "camazotz_fight.png",
        flags={"gate_open": True}, ending=True))
    check("C3 watcher charged beam", check_watcher_beam)
    check("C4 watcher blade blocked and contact", check_watcher_block)
    check("A0 four glyphs open the sun gate", check_gate)
    print("---")
    failed = 0
    for name, status, detail, tb in RESULTS:
        if status == "PASS":
            print("PASS %s" % name)
        else:
            failed += 1
            print("FAIL %s" % name)
            print(tb)
    print("shots:")
    for path in SHOTS:
        print(path)
    report = OUT / "report.txt"
    with open(report, "w") as handle:
        for name, status, detail, tb in RESULTS:
            handle.write("%s\t%s\t%s\n" % (status, name, detail if status == "PASS" else ""))
            if tb:
                handle.write(tb)
                handle.write("\n")
        handle.write("shots\n")
        for path in SHOTS:
            handle.write(path + "\n")
    print("failed %s / %s" % (failed, len(RESULTS)))
    if failed:
        raise SystemExit(1)
