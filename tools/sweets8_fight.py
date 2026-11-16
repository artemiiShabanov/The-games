#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Сладости» (#137): бойцы 16×32 сбоку, зеркало `space8_fight.py` и
раздела «Файтинг» в `pixel_sprites.py`. Сборка кадров та же (голова 10 строк, торс 11, ноги 11,
те же смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и космосом;
рисунок частей свой. Палитра `sweets8.PALETTE`: K чёрный (горький шоколад), W глазурь,
G пряник и карамель, R мармелад и бант, P розовая глазурь.

Герой: пряничный человечек, круглая голова без шеи, глаз и белая улыбка глазурью, красный бант
под подбородком, толстые руки и ноги с белой каймой глазури у круглых концов, розовые пуговицы и
волна глазури на животе. Соперник это босс сеттинга, шоколадный король: голова из горького
шоколада с карамельным бликом, корона из белой глазури с тремя зубцами и красными драже, усы и
борода глазурью, красная мантия с белой оторочкой и карамельным поясом, белые перчатки, розовый плащ
глазури за спиной до колен. Силуэты разные: круглый гладкий пряник против зубчатой короны и плаща.

    python3 tools/sweets8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Пряничный человечек -------------------------------------------------------------------------

HEAD_GINGER = [
    "................",
    ".....KKKKKK.....",
    "....KGGGGGGK....",
    "...KGGGGGGGGK...",
    "...KGGGGGKGGK...",
    "...KGGGGGKGGK...",
    "...KGGGGGGGWK...",
    "...KGGGGGWWGK...",
    "....KGGGGGGK....",
    ".....KRRKRRK....",
]
# Торс в стойке: задняя рука слева опущена, передняя поднята кулаком к подбородку; у круглых
# концов рук белая кайма глазури, на груди розовые пуговицы, на животе волна глазури.
TORSO_GUARD = [
    "..KKKKKGGGKKKK..",
    "..KGGKGGGGKGGGK.",
    "..KGGKGGPGKWWWK.",
    "..KWWKGGGKGGKKK.",
    "..KGGKGGGKGGK...",
    "..KKKKGGPGKK....",
    "....KGGGGGGK....",
    "....KWGGWGGK....",
    "....KGWWGWWK....",
    "....KGGGGGGK....",
    "....KGGGGGGK....",
]
# Замах верхнего: передняя рука отведена за плечо.
TORSO_WIND = [
    "..KKKKKGGGKKKK..",
    ".KGGGKGGGGKGGGK.",
    ".KGWWKGGPGKWWGK.",
    "..KKKKGGGGKKKK..",
    "....KGGGGGK.....",
    "....KGGPGGGK....",
    "....KGGGGGGK....",
    "....KWGGWGGK....",
    "....KGWWGWWK....",
    "....KGGGGGGK....",
    "....KGGGGGGK....",
]
# Торс без передней руки: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKKGGGK.....",
    "..KGGKGGGGK.....",
    "..KGGKGGPGK.....",
    "..KWWKGGGKWGK...",
    "..KGGKGGGKWGK...",
    "..KKKKGGPGKK....",
    "....KGGGGGGK....",
    "....KWGGWGGK....",
    "....KGWWGWWK....",
    "....KGGGGGGK....",
    "....KGGGGGGK....",
]
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла.
TORSO_HIT = [
    "....KKGGGK......",
    "...KGGGGGGK.....",
    "..KGKGGPGGK.....",
    ".KGWKGGGGGK.....",
    ".KKKKGGPGGK.....",
    "....KGGGGGGK....",
    "....KGGGGGGKK...",
    "....KWGGWGKWWK..",
    "....KGWWGWKGGK..",
    "....KGGGGGGKK...",
    "....KGGGGGGK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): кайма глазури и круглый конец.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKGGGGK",
    "KGGGGGGGWWGGGGK",
    "KGGGGGGGWWGGGGK",
    ".KKKKKKKKKGGGGK",
    "..........KKKK.",
]
# Руки блока перед головой (колонка 9, строка 3).
ARM_BLOCK = [
    ".KKKK.",
    "KGGGGK",
    "KGGGGK",
    "KKWWKK",
    ".KGGK.",
    ".KGGK.",
    ".KGGK.",
    ".KGGK.",
    "..KK..",
]
LEGS_STAND = [
    "....KGGKKGGK....",
    "...KGGK..KGGK...",
    "...KGGK..KGGK...",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KWWK....KWWK..",
    "..KGGK....KGGK..",
    "..KGGGK...KGGGK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KWWKKWWK....",
    "....KGGKKGGK....",
    "....KGGGKGGGK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KGGGGGGK....",
    "...KGGGGGGGGKK..",
    "..KGGKKKKKKGGGK.",
    "..KWWK....KWWK..",
    ".KGGGK...KGGGK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самого пола (24 колонки).
LEGS_KICK = [
    "....KGGGGGGK............",
    "...KGGGGGGGGKKKKKKKKKK..",
    "..KGGKKGGGGGGGGGGGWWGGK.",
    "..KWWK.KKKKKKKKKKKKKGGGK",
    ".KGGGK..............KKKK",
]
KO_GINGER = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK...........................",
    "KGGGGK...KKKKK..................",
    "KGKGGKKKKGGGGKK.........KKK.KKK.",
    "KGGGGKRGGGPGGGGKKKKKKKKKKGGKKGGK",
    "KGWWGKRGGGGGGGGKGGGGGGWWKGGKKGGK",
    "KGGGGKKGGGPGGGGKGGGGGGWWKGGKKGGK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Шоколадный король ---------------------------------------------------------------------------

# Корона из белой глазури: три раздельных зубца и обод с красными драже; голова из горького
# шоколада с карамельным бликом на затылке, два белых глаза, нос уступом, усы и борода глазурью.
HEAD_KING = [
    "..KWK.KWK.KWK...",
    "..KWWKWWWKWWK...",
    "..KWRWWRWWRWK...",
    "..KWWWWWWWWWK...",
    "...KGKKKKKKK....",
    "...KGKKKWKWK....",
    "...KGKKKWKWKK...",
    "...KKKKKKKKKK...",
    "...KKKWWWWWWK...",
    "....KKKWWWWK....",
]
# Части короля в том же порядке и тех же размеров, что у пряника: мантия красная с белой
# оторочкой посередине, пояс карамельный, перчатки белые, плащ розовой глазури слева за спиной.
KING_GUARD = [
    ".KKKKKKRRRKKKK..",
    ".KPPPKRRWRKWWWK.",
    ".KPPPKRRWRKWWWK.",
    ".KPPPKRRWKRRKKK.",
    ".KPPPKRRWKRRK...",
    ".KPPPKRRWRKK....",
    ".KPPKRRRWRRK....",
    ".KPPKGGGGGGK....",
    ".KPPKRRRWRRK....",
    ".KPPKRRRWRRK....",
    ".KPPKRRRWRRK....",
]
KING_WIND = [
    ".KKKKKKRRRKKKK..",
    ".KWWWKRRWRKWWWK.",
    ".KWWWKRRWRKWWWK.",
    ".KKKKKRRWRKKKK..",
    ".KPPPKRRWRK.....",
    ".KPPPKRRWRRK....",
    ".KPPKRRRWRRK....",
    ".KPPKGGGGGGK....",
    ".KPPKRRRWRRK....",
    ".KPPKRRRWRRK....",
    ".KPPKRRRWRRK....",
]
KING_OPEN = [
    ".KKKKKKRRRK.....",
    ".KPPPKRRWRK.....",
    ".KPPPKRRWRK.....",
    ".KPPPKRRWKWWK...",
    ".KPPPKRRWKWWK...",
    ".KPPPKRRWRKK....",
    ".KPPKRRRWRRK....",
    ".KPPKGGGGGGK....",
    ".KPPKRRRWRRK....",
    ".KPPKRRRWRRK....",
    ".KPPKRRRWRRK....",
]
KING_HIT = [
    "....KKRRRK......",
    "...KRRRWRRK.....",
    "..KWKRRWRRK.....",
    ".KWWKRRWRRK.....",
    ".KKKKRRWRRK.....",
    "..KPKRRRWRRK....",
    "..KPKRRRWRRKK...",
    "..KPKGGGGGKWWK..",
    "..KPKRRRWRKWWK..",
    "..KPKRRRWRRKK...",
    "..KPKRRRWRRK....",
]
KING_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKWWWWK",
    "KRRRRRRRRPWWWWK",
    "KRRRRRRRRPWWWWK",
    ".KKKKKKKKKWWWWK",
    "..........KKKK.",
]
KING_BLOCK = [
    ".KKKK.",
    "KWWWWK",
    "KWWWWK",
    "KKPPKK",
    ".KRRK.",
    ".KRRK.",
    ".KRRK.",
    ".KRRK.",
    "..KK..",
]
# Ноги красные, сапоги карамельные; в стойке и шаге позади висит плащ до колен.
KING_STAND = [
    ".KPPKRRKKRRK....",
    ".KPKRRK..KRRK...",
    ".KPKRRK..KRRK...",
    "KPKRRK....KRRK..",
    "KPKRRK....KRRK..",
    "KKKRRK....KRRK..",
    "..KKKK....KKKK..",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KGGGK...KGGGK.",
    "..KKKKK...KKKKK.",
]
KING_WALK = [
    ".KPPKRRKKRRK....",
    ".KPPKRRKKRRK....",
    ".KPPKRRKKRRK....",
    ".KPPKRRKKRRK....",
    ".KPPKRRKKRRK....",
    "..KKKRRKKRRK....",
    "....KKKKKKKK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGGKGGGK...",
    "....KKKKKKKKK...",
]
KING_CROUCH = [
    ".KPPKRRRRRRK....",
    ".KPKRRRRRRRRKK..",
    ".KKRRKKKKKKRRRK.",
    "..KGGK....KGGK..",
    ".KGGGK...KGGGK..",
]
KING_KICK = [
    ".KPPKRRRRRRK............",
    ".KPKRRRRRRRRKKKKKKKKKK..",
    ".KKRRKKRRRRRRRRRRRRRKGK.",
    "..KGGK.KKKKKKKKKKKKKGGGK",
    ".KGGGK..............KKKK",
]
# Нокаут: король на спине, корона сползла на затылок, плащ под ним.
KO_KING = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK...........................",
    "KWWKKK..........................",
    "KRWKWK...KKKKK..................",
    "KWWKKKKKKWWWWKK.........KKK.KKK.",
    "KRWKKKKRRRRRGRRKKKKKKKKKKGGKKGGK",
    "KWWKWKKRRRRRGRRKRRRRRRRRKGGKKGGK",
    "KRWKWKKPPPPPPPPKRRRRRRRRKGGKKGGK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

_KING_PARTS = (
    (TORSO_GUARD, KING_GUARD), (TORSO_WIND, KING_WIND), (TORSO_OPEN, KING_OPEN),
    (TORSO_HIT, KING_HIT), (ARM_PUNCH, KING_PUNCH), (ARM_BLOCK, KING_BLOCK),
    (LEGS_STAND, KING_STAND), (LEGS_WALK, KING_WALK), (LEGS_CROUCH, KING_CROUCH),
    (LEGS_KICK, KING_KICK),
)
for _hero_part, _king_part in _KING_PARTS:
    assert len(_hero_part) == len(_king_part) and len(_hero_part[0]) == len(_king_part[0])


def _king(rows):
    """Часть короля на месте той же части пряника: сборка кадров общая, рисунок свой."""
    for hero_part, king_part in _KING_PARTS:
        if rows is hero_part:
            return king_part
    raise KeyError("нет части короля")


# --- Сборка кадров (как `pixel_sprites.fighter_frames`) --------------------------------------------

def _blank(w, h):
    return [["."] * w for _ in range(h)]


def _paste(canvas, rows, x, y):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != "." and 0 <= y + dy < len(canvas) and 0 <= x + dx < len(canvas[0]):
                canvas[y + dy][x + dx] = ch


def fighter_frames(prefix, head, torso, legs, arm, ko):
    """Кадры бойца: стойка 2, шаг, верхний удар (замах и удар 24×32), присед и нижний удар
    24×32, блок, пропустил, KO 32×16. Смещения частей те же, что у пиратов."""
    def frame(w, parts):
        c = _blank(w, 32)
        for rows, x, y in parts:
            _paste(c, rows, x, y)
        return ["".join(r) for r in c]

    h = head
    t = torso
    crouch_top = [(h, 0, 12), (t(TORSO_GUARD)[:5], 0, 22)]
    return {
        prefix + "idle_0": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_GUARD), 0, 10), (h, 0, 0)]),
        prefix + "idle_1": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_GUARD)[:10], 0, 11), (h, 0, 1)]),
        prefix + "walk": frame(16, [(legs(LEGS_WALK), 0, 21), (t(TORSO_GUARD)[:10], 0, 11), (h, 0, 1)]),
        prefix + "high_0": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_WIND), 0, 10), (h, -1, 0)]),
        prefix + "high_1": frame(24, [(legs(LEGS_STAND), 0, 21), (t(TORSO_OPEN), 0, 10), (h, 1, 0), (arm(ARM_PUNCH), 9, 8)]),
        prefix + "crouch": frame(16, [(legs(LEGS_CROUCH), 0, 27)] + crouch_top),
        prefix + "low_1": frame(24, [(legs(LEGS_KICK), 0, 27), (h, -1, 12), (t(TORSO_GUARD)[:5], -1, 22)]),
        prefix + "block": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_OPEN), 0, 10), (h, -1, 0), (arm(ARM_BLOCK), 9, 3)]),
        prefix + "hit": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_HIT), 0, 10), (h, -2, 1)]),
        prefix + "ko": ko,
    }


SPRITES = {}
SPRITES.update(fighter_frames("fight_hero_", HEAD_GINGER, lambda r: r, lambda r: r, lambda r: r, KO_GINGER))
SPRITES.update(fighter_frames("fight_rival_", HEAD_KING, _king, _king, _king, KO_KING))
SPRITES.update({
    # Искра удара: розовая сахарная звезда с белым крестом, вокруг летят крошки печенья.
    "fight_spark": [
        "................",
        ".......W........",
        ".......W........",
        "..G...PWP...G...",
        "...G.PPWPP.G....",
        "....PPWWWPP.....",
        "...PPWWWWWPP....",
        ".WWWWWWWWWWWWW..",
        "...PPWWWWWPP....",
        "....PPWWWPP.....",
        "...G.PPWPP.G....",
        "..G...PWP...G...",
        ".......W........",
        ".......W........",
        "................",
        "................",
    ],
    # Искра блока: дуга карамельной трости в красно-белую полоску.
    "fight_guard": [
        "................",
        "......KKKK......",
        "......KRWWK.....",
        ".......KRRWK....",
        ".......KWRRK....",
        "........KWWRK...",
        "........KRWWK...",
        "........KRRWK...",
        "........KWRRK...",
        "........KWWRK...",
        "........KRWWK...",
        ".......KRRWK....",
        ".......KWRRK....",
        "......KWWRK.....",
        "......KKKK......",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KWGRP."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import sweets8
        sweets8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
