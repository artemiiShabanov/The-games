#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Зомби» (#137): бойцы 16×32 сбоку, зеркало раздела «Файтинг» в
`pixel_sprites.py` и модуля `space8_fight.py`. Сборка кадров та же (голова 10 строк, торс 11,
ноги 11, те же смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и
космосом; рисунок частей свой.

Герой: выживший, синяя бейсболка с козырьком вперёд, красная куртка с белой полосой по подолу,
зелёный рюкзак за спиной, голые кулаки, джинсы и белые кроссовки. Соперник это босс сеттинга,
зомби-мясник: лысая зелёная голова шире плеч героя, в темени застрял тесак рукоятью назад,
красный глаз и оскал, белый фартук в крови на большом животе, голые зелёные руки и босые
ступни, синие штаны под подолом фартука. Силуэты разные: кепка с козырьком и горб рюкзака
против тесака над макушкой и пуза вперёд.

    python3 tools/zombies8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Выживший ----------------------------------------------------------------------------------

# Голова лицом вправо: купол бейсболки, козырёк торчит вперёд, под ним лицо с глазом, сзади
# волосы из-под кепки.
HEAD_SURVIVOR = [
    "................",
    ".....KKKKKK.....",
    "....KBBBBWBK....",
    "...KBBBBBBBBKK..",
    "...KBBBBBBBBBBK.",
    "...KKKKKKKKKKKK.",
    "...KKWWWKWWK....",
    "....KWWWKWWK....",
    "....KWWWWWK.....",
    ".....KWWWWK.....",
]
# Торс в стойке: рюкзак с пряжкой слева, передний кулак у подбородка, молния на груди, белый
# подол футболки над ремнём, ниже джинсы.
TORSO_GUARD = [
    "..KKKKKRRRKKKK..",
    "..KGGKRRRRKWWWK.",
    "..KGGKRRWRKWWWK.",
    "..KGWKRRRKRRKKK.",
    "..KGGKRRRKRRK...",
    "..KKKKRRRRKK....",
    "....KRRRRRRK....",
    "....KWWWWWWK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Замах верхнего: передний кулак отведён за плечо, поверх рюкзака.
TORSO_WIND = [
    "..KKKKKRRRKKKK..",
    ".KWWWKRRRRKWWWK.",
    ".KWWWKRRWRKWWWK.",
    "..KKKKRRRRKKKK..",
    "..KGKRRRRRK.....",
    "..KKKRRRRRRK....",
    "....KRRRRRRK....",
    "....KWWWWWWK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Торс без переднего кулака: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKKRRRK.....",
    "..KGGKRRRRK.....",
    "..KGGKRRWRK.....",
    "..KGWKRRRKWWK...",
    "..KGGKRRRKWWK...",
    "..KKKKRRRRKK....",
    "....KRRRRRRK....",
    "....KWWWWWWK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Пропустил удар: корпус назад, рюкзак съехал, передняя рука повисла (рукав и кулак).
TORSO_HIT = [
    "....KKRRRK......",
    "...KRRRRRRK.....",
    "..KGKRRWRRK.....",
    ".KGGKRRRRRK.....",
    ".KKKKRRRRRK.....",
    "....KRRRRRRK....",
    "....KRRRRRRKK...",
    "....KWWWWWKRRK..",
    "....KKKKKKKWWK..",
    "....KBBBBBBKK...",
    "....KBBBBBBK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): красный рукав и кулак.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKWWWWK",
    "KRRRRRRRRKWWWWK",
    "KRRRRRRRRKWWKWK",
    ".KKKKKKKKKWWWWK",
    "..........KKKK.",
]
# Руки блока перед лицом (колонка 9, строка 3): кулаки сверху, рукава вниз.
ARM_BLOCK = [
    ".KKKK.",
    "KWWWWK",
    "KWKWWK",
    "KKWWKK",
    ".KRRK.",
    ".KRRK.",
    ".KRRK.",
    ".KRRK.",
    "..KK..",
]
LEGS_STAND = [
    "....KBBKKBBK....",
    "...KBBK..KBBK...",
    "...KBBK..KBBK...",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KKKK....KKKK..",
    "..KWWK....KWWK..",
    "..KWRK....KWRK..",
    "..KWWWK...KWWWK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KKKKKKKK....",
    "....KWWKKWWK....",
    "....KWRKKWRK....",
    "....KWWWKWWWK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KBBBBBBK....",
    "...KBBBBBBBBKK..",
    "..KBBKKKKKKBBBK.",
    "..KWWK....KWWK..",
    ".KWWWK...KWWWK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самой земли (24 колонки).
LEGS_KICK = [
    "....KBBBBBBK............",
    "...KBBBBBBBBKKKKKKKKKK..",
    "..KBBKKBBBBBBBBBBBBBKWK.",
    "..KWWK.KKKKKKKKKKKKKWWWK",
    ".KWWWK..............KKKK",
]
KO_SURVIVOR = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK...........................",
    "KBBBBK...KKKKK..................",
    "KBBBBKKKKRRRRKK.........KKK.KKK.",
    "KWKKWKKRRRWRRRRKKKKKKKKKKWWKKWWK",
    "KWWWWWKRRRRRRRWKBBBBBBBBKWRKKWRK",
    "KWWWWKKGGGGGGGGKBBBBBBBBKWWKKWWK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Зомби-мясник (босс) -------------------------------------------------------------------------

# Лысая широкая голова, в темени тесак: рукоять торчит назад и вверх, лезвие ушло в череп, у
# раны кровь. Красный глаз в чёрной глазнице, оскал с зубами, толстая шея.
HEAD_BUTCHER = [
    ".KK.............",
    "KBBKKKK.........",
    ".KKWWWWK........",
    "..KWWWWWKKKK....",
    "...KRRWWGGGGK...",
    "..KGGRGGKKKGGK..",
    "..KGGGGGKRKGGK..",
    "..KGGGGGGGGGGK..",
    "..KGGGGKWKWKK...",
    "....KKGGGGKK....",
]
# Торс в стойке: толстое плечо задней руки слева, нагрудник фартука в крови, передний кулак у
# подбородка, ниже живот шире груди.
B_GUARD = [
    "..KKKKKGGGKKKK..",
    ".KGGGKWWWWKGGGK.",
    ".KGGGKWRWWKGGGK.",
    ".KGGGKWWWKGGKKK.",
    ".KGGKWWRWKGGK...",
    "..KKKWWWWWWKK...",
    "...KWWWRRWWWK...",
    "...KWRWWWWWWK...",
    "...KWWWWWWRWK...",
    "....KWWWWWWK....",
    "....KWWRWWWK....",
]
B_WIND = [
    "..KKKKKGGGKKKK..",
    "KGGGGKWWWWKGGGK.",
    "KGGGGKWRWWKGGGK.",
    ".KKKKKWWWWKKKK..",
    "..KGKWWRWWK.....",
    "..KKKWWWWWWKK...",
    "...KWWWRRWWWK...",
    "...KWRWWWWWWK...",
    "...KWWWWWWRWK...",
    "....KWWWWWWK....",
    "....KWWRWWWK....",
]
B_OPEN = [
    "..KKKKKGGGK.....",
    ".KGGGKWWWWK.....",
    ".KGGGKWRWWK.....",
    ".KGGGKWWWKGGK...",
    ".KGGKWWRWKGGK...",
    "..KKKWWWWWWKK...",
    "...KWWWRRWWWK...",
    "...KWRWWWWWWK...",
    "...KWWWWWWRWK...",
    "....KWWWWWWK....",
    "....KWWRWWWK....",
]
B_HIT = [
    "....KKGGGK......",
    "...KWWWWWWK.....",
    "..KGKWRWWWK.....",
    ".KGGKWWWWWK.....",
    ".KKKKWWRWWK.....",
    "...KWWWWWWWK....",
    "...KWWWRRWWKK...",
    "...KWRWWWWKGGK..",
    "...KWWWWWWKGGK..",
    "....KWWWWWWKK...",
    "....KWWRWWWK....",
]
# Голая рука с тяжёлым кулаком, костяшки в крови.
B_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKGGGGK",
    "KGGGGGGGGGGGGRK",
    "KGGGGGGGGKGGGRK",
    ".KKKKKKKKKGGGGK",
    "..........KKKK.",
]
B_BLOCK = [
    ".KKKK.",
    "KGGGGK",
    "KGRGGK",
    "KKGGKK",
    ".KGGK.",
    ".KGGK.",
    ".KGGK.",
    ".KGGK.",
    "..KK..",
]
# Ноги: подол фартука свисает между бёдер, синие штаны, босые зелёные ступни.
B_STAND = [
    "....KWWWWWWK....",
    "...KBKWWWWKBK...",
    "...KBBKWWKBBK...",
    "..KBBK.KK.KBBK..",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KKKK....KKKK..",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KGGGK...KGGGK.",
    "..KKKKK...KKKKK.",
]
B_WALK = [
    "....KWWWWWWK....",
    "....KBKWWKBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KKKKKKKK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGGKGGGK...",
    "....KKKKKKKKK...",
]
B_CROUCH = [
    "....KWWWWWWK....",
    "...KBBWWRWBBKK..",
    "..KBBKKKKKKBBBK.",
    "..KGGK....KGGK..",
    ".KGGGK...KGGGK..",
]
B_KICK = [
    "....KWWWWWWK............",
    "...KBBWWRWBBKKKKKKKKKK..",
    "..KBBKKBBBBBBBBBBBBBKGK.",
    "..KGGK.KKKKKKKKKKKKKGGGK",
    ".KGGGK..............KKKK",
]
# Лежит на спине головой влево: тесак торчит из темени, живот в фартуке горой.
KO_BUTCHER = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "...KK...........................",
    "..KBK.......KKKKK...............",
    ".KKWWK....KKWWRWWKK.............",
    "KGGWWKKKKKWWWWWWWWWK............",
    "KGRGGKGGKWWRWWWWWWWK....KKK.KKK.",
    "KGKGGGKGKWWWWWWWRWWKKKKKKGGKKGGK",
    "KGGGGGKGGKWWWWWWWWKBBBBBKGGKKGGK",
    "KKWKWKKGGGKWWWWWWKBBBBBBKGGKKGGK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

_BUTCHER = {}
for _hero, _boss in ((TORSO_GUARD, B_GUARD), (TORSO_WIND, B_WIND), (TORSO_OPEN, B_OPEN),
                     (TORSO_HIT, B_HIT), (ARM_PUNCH, B_PUNCH), (ARM_BLOCK, B_BLOCK),
                     (LEGS_STAND, B_STAND), (LEGS_WALK, B_WALK), (LEGS_CROUCH, B_CROUCH),
                     (LEGS_KICK, B_KICK)):
    assert len(_hero) == len(_boss) and len(_hero[0]) == len(_boss[0])
    _BUTCHER[tuple(_hero)] = _boss


def _butcher_part(rows):
    """Часть мясника на месте той же части выжившего: у босса свой рисунок каждой части, размеры
    и место в кадре те же."""
    return _BUTCHER[tuple(rows)]


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
SPRITES.update(fighter_frames("fight_hero_", HEAD_SURVIVOR, lambda r: r, lambda r: r, lambda r: r, KO_SURVIVOR))
SPRITES.update(fighter_frames("fight_rival_", HEAD_BUTCHER, _butcher_part, _butcher_part, _butcher_part, KO_BUTCHER))
SPRITES.update({
    # Искра удара: белая звезда с кровавым ядром и красными брызгами по диагоналям.
    "fight_spark": [
        "................",
        ".......W........",
        ".......W........",
        "..R....W....R...",
        "...R..RWR..R....",
        "....W.RWR.W.....",
        ".....RRWRR......",
        ".WWWWWWWWWWWWW..",
        ".....RRWRR......",
        "....W.RWR.W.....",
        "...R..RWR..R....",
        "..R....W....R...",
        ".......W........",
        ".......W........",
        "................",
        "................",
    ],
    # Искра блока: дуга глухого удара, синий сланец с белыми бликами.
    "fight_guard": [
        "................",
        "......KKK.......",
        ".......KWK......",
        "........KBK.....",
        ".........KBK....",
        ".........KWBK...",
        "..........KBK...",
        "..........KWK...",
        "..........KBK...",
        "..........KWK...",
        ".........KWBK...",
        ".........KBK....",
        "........KBK.....",
        ".......KWK......",
        "......KKK.......",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KRGWB."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import zombies8
        zombies8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
