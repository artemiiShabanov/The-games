#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Ниндзя» (#137): бойцы 16×32 сбоку, зеркало `space8_fight.py` и раздела
«Файтинг» в `pixel_sprites.py`. Сборка кадров та же (голова 10 строк, торс 11, ноги 11, те же
смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и космосом; рисунок
частей свой. Палитра `ninja8.PALETTE`: K чёрный, B синий, R красный, W белый, Y золото.

Герой: ниндзя в синем, капюшон с прорезью глаз, рукоять меча над плечом, красный шарф с концами
за спиной, красный пояс с золотым узлом, белые обмотки на кулаках и голенях. Соперник это босс
сеттинга, сёгун: шлем с двумя золотыми рогами и назатыльником, красная маска демона с белыми
клыками, чёрный лаковый доспех в золотой шнуровке, наплечник, юбка из пластин, красные хакама,
золотые поножи и рукавицы, ножны меча торчат за спиной у пояса. Силуэты разные: узкая фигура с
шарфом против широкого рогатого доспеха с юбкой.

    python3 tools/ninja8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Ниндзя ------------------------------------------------------------------------------------

# Капюшон с прорезью (смотрит вправо), рукоять меча над плечом слева, шарф на шее и верхний
# конец шарфа за затылком.
HEAD_NINJA = [
    "................",
    ".YY..KKKKKK.....",
    "..YYKBBBBBBK....",
    "...KBBBBBBBBK...",
    "...KBBBKKKKKK...",
    "...KBBBWWKWKK...",
    "...KBBBBBBBBK...",
    "RR..KBBBBBBK....",
    ".RRRRRRRRRRK....",
    "....KRRRRRK.....",
]
# Торс в стойке: второй конец шарфа висит за спиной, передний кулак в обмотках у подбородка.
TORSO_GUARD = [
    "..RRKKKBBBKKKK..",
    ".RR.KBBBBBKWWWK.",
    ".RR.KBBBBBKWWWK.",
    "..RRKBBBBKBBKKK.",
    "..R.KBBBBKBBK...",
    "....KBBBBBKK....",
    "....KBBBBBBK....",
    "....KRRRYRRK....",
    "....KBBBRBBK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Замах верхнего: передний кулак отведён за плечо, шарф сбился ниже.
TORSO_WIND = [
    "..KKKKKBBBKKKK..",
    ".KWWWKBBBBKBBWK.",
    ".KWWWKBBBBKBBWK.",
    "..KKKKBBBBKKKK..",
    "..RRKBBBBBK.....",
    ".RR.KBBBBBBK....",
    "....KBBBBBBK....",
    "....KRRRYRRK....",
    "....KBBBRBBK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Торс без переднего кулака: под вытянутую руку удара и под руки блока; задний кулак у груди.
TORSO_OPEN = [
    "..RRKKKBBBK.....",
    ".RR.KBBBBBK.....",
    ".RR.KBBBBBK.....",
    "..RRKBBBBKWWK...",
    "..R.KBBBBKWWK...",
    "....KBBBBBKK....",
    "....KBBBBBBK....",
    "....KRRRYRRK....",
    "....KBBBRBBK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла.
TORSO_HIT = [
    "....KKBBBK......",
    "...KBBBBBBK.....",
    "..KWKBBBBBK.....",
    ".KWWKBBBBBK.....",
    ".KKKKBBBBBK.....",
    "....KBBBBBBK....",
    "....KBBBBBBKK...",
    "....KRRRYRKBBK..",
    "....KBBBRBKWWK..",
    "....KBBBBBBKK...",
    "....KBBBBBBK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): рукав, обмотки предплечья, кулак.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKWWWWK",
    "KBBBBBWBWBWWWWK",
    "KBBBBBWBWBWWKWK",
    ".KKKKKKKKKWWWWK",
    "..........KKKK.",
]
# Руки блока перед капюшоном (колонка 9, строка 3).
ARM_BLOCK = [
    ".KKKK.",
    "KWWWWK",
    "KWWWWK",
    "KKWWKK",
    ".KBBK.",
    ".KWWK.",
    ".KBBK.",
    ".KBBK.",
    "..KK..",
]
# Ноги: синие штаны, белые обмотки на голенях с перевязкой, синие таби.
LEGS_STAND = [
    "....KBBKKBBK....",
    "...KBBK..KBBK...",
    "...KBBK..KBBK...",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KWWK....KWWK..",
    "..KBBK....KBBK..",
    "..KWWK....KWWK..",
    "..KWWK....KWWK..",
    "..KBBBK...KBBBK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KWWKKWWK....",
    "....KBBKKBBK....",
    "....KWWKKWWK....",
    "....KWWKKWWK....",
    "....KBBBKBBBK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KBBBBBBK....",
    "...KBBBBBBBBKK..",
    "..KBBKKKKKKBBBK.",
    "..KWWK....KWWK..",
    ".KBBBK...KBBBK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самого пола (24 колонки).
LEGS_KICK = [
    "....KBBBBBBK............",
    "...KBBBBBBBBKKKKKKKKKK..",
    "..KBBKKBBBBBBBWBWWBWKBK.",
    "..KWWK.KKKKKKKKKKKKKBBBK",
    ".KBBBK..............KKKK",
]
# Лежит на спине головой влево: прорезь капюшона вверх, шарф стёк на пол, носки таби вверх.
KO_NINJA = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK...........................",
    "KBKWBK...KKKKK..................",
    "KBKKBKRKKBBBBKK.........KKK.KKK.",
    "KBKWBKRBBBBRBBBKKKKKKKKKKBBKKBBK",
    "KBBBBKRBBBBRBBBKBBBBWBWWKBBKKBBK",
    "KBBBBKRRRBBYBBBKBBBBWBWWKBBKKBBK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Сёгун (босс сеттинга) -----------------------------------------------------------------------

# Шлем с двумя золотыми рогами и золотым козырьком, полосатый назатыльник слева, красная маска
# демона: белый глаз под чёрной бровью, нос вперёд, белые клыки.
HEAD_SHOGUN = [
    "..Y.........Y...",
    "..YY.......YY...",
    "...YYKKKKKYY....",
    "...KYYKKKYYYK...",
    "..KYKKKKKKKYKK..",
    "..KYYYYYYYYYYYK.",
    ".KYKYKRRKKKKRK..",
    ".KKYKYRRWWKRRRK.",
    ".KYKYKRRRRRRRK..",
    "..KKKKRWRWRWK...",
]
# Низ доспеха, общий для всех торсов: красный пояс с золотым узлом, юбка из пластин в два ряда,
# белые ножны меча торчат назад из-за пояса.
_SKIRT = [
    "...KRRRYYRRRK...",
    ".WKYYKYYKYYYK...",
    "W.KKKKKKKKKKK...",
    ".KYYYKYYKYYYYK..",
]
# Верх доспеха по позам героя: наплечник полосами слева, шнуровка зигзагом на чёрной кирасе,
# золотая рукавица на красном рукаве.
_SHOGUN_TOP = {
    "guard": [
        ".KKKKKKKKKKKKK..",
        ".KYYYKKYKKKYYYK.",
        ".KKKKKYKYKKYYYK.",
        ".KYYYKKYKKRRKKK.",
        ".KKKKKYKYKRRK...",
        "..KYYKKYKKKK....",
        "...KKKYKYKKK....",
    ],
    "wind": [
        ".KKKKKKKKKKKKK..",
        "KYYYYKKYKKKYYYK.",
        "KYYYYKYKYKKKKKK.",
        ".KRRKKKYKKKYYYK.",
        "..KKKKYKYKKKKK..",
        "..KYYKKYKKK.....",
        "...KKKYKYKKK....",
    ],
    "open": [
        ".KKKKKKKKKK.....",
        ".KYYYKKYKKK.....",
        ".KKKKKYKYKK.....",
        ".KYYYKKYKKYYK...",
        ".KKKKKYKYKYYK...",
        "..KYYKKYKKKK....",
        "...KKKYKYKKK....",
    ],
}
_SHOGUN_HIT = [
    "....KKKKKK......",
    "..KKKKYKKKK.....",
    ".KYKKYKYKKK.....",
    "KYYKKKYKKKK.....",
    "KKKKKYKYKKK.....",
    "...KKKYKKKKK....",
    "...KKYKYKKKKK...",
    "...KRRRYYRKRRK..",
    ".WKYYKYYKYKYYK..",
    "W.KKKKKKKKKKKK..",
    ".KYYYKYYKYYYYK..",
]
_SHOGUN_ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKYYYYK",
    "KRRRRRYKYKYYYYK",
    "KRRRRRYKYKYYKYK",
    ".KKKKKKKKKYYYYK",
    "..........KKKK.",
]
_SHOGUN_ARM_BLOCK = [
    ".KKKK.",
    "KYYYYK",
    "KYKYYK",
    "KKYYKK",
    ".KRRK.",
    ".KYYK.",
    ".KRRK.",
    ".KRRK.",
    "..KK..",
]
# Красные хакама шире ног героя, под коленом золотые поножи с перехватом, ступни там же.
_SHOGUN_LEGS_STAND = [
    "...KRRRKKRRRK...",
    "..KRRRK..KRRRK..",
    "..KRRRK..KRRRK..",
    ".KRRRK....KRRRK.",
    ".KRRRK....KRRRK.",
    ".KKKKK....KKKKK.",
    "..KYYK....KYYK..",
    "..KKKK....KKKK..",
    "..KYYK....KYYK..",
    "..KYYYK...KYYYK.",
    "..KKKKK...KKKKK.",
]
_SHOGUN_LEGS_WALK = [
    "...KRRRKKRRRK...",
    "...KRRRKKRRRK...",
    "...KRRRKKRRRK...",
    "...KRRRKKRRRK...",
    "...KRRRKKRRRK...",
    "...KKKKKKKKKK...",
    "....KYYKKYYK....",
    "....KKKKKKKK....",
    "....KYYKKYYK....",
    "....KYYYKYYYK...",
    "....KKKKKKKKK...",
]
_SHOGUN_LEGS_CROUCH = [
    "...KRRRRRRRRK...",
    "..KRRRRRRRRRRKK.",
    ".KRRRKKKKKKRRRRK",
    "..KYYK....KYYK..",
    ".KYYYK...KYYYK..",
]
_SHOGUN_LEGS_KICK = [
    "...KRRRRRRRRK...........",
    "..KRRRRRRRRRRKKKKKKKKK..",
    ".KRRRKKRRRRRRRKYKYYYKYK.",
    "..KYYK.KKKKKKKKKKKKKYYYK",
    ".KYYYK..............KKKK",
]
# Лежит на спине головой влево: рога шлема торчат вверх, маска кверху, поножи носками вверх.
KO_SHOGUN = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".Y..Y...........................",
    ".YY.YY..........................",
    ".KYKKY..........................",
    "KYKRRK...KKKKK..................",
    "KYKWRRKKKYKYKKK.........KKK.KKK.",
    "KYKRWKKYYKYKYKYKKKKKKKKKKYYKKYYK",
    "KYKRRKKKKKYKYKYKRRRRRKYYKYYKKYYK",
    "KKYKKKKYYKKYKKYKRRRRRKYYKYYKKYYK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

_SHOGUN_TORSO = {
    id(TORSO_GUARD): _SHOGUN_TOP["guard"] + _SKIRT,
    id(TORSO_WIND): _SHOGUN_TOP["wind"] + _SKIRT,
    id(TORSO_OPEN): _SHOGUN_TOP["open"] + _SKIRT,
    id(TORSO_HIT): _SHOGUN_HIT,
}
_SHOGUN_LEGS = {
    id(LEGS_STAND): _SHOGUN_LEGS_STAND,
    id(LEGS_WALK): _SHOGUN_LEGS_WALK,
    id(LEGS_CROUCH): _SHOGUN_LEGS_CROUCH,
    id(LEGS_KICK): _SHOGUN_LEGS_KICK,
}
_SHOGUN_ARM = {id(ARM_PUNCH): _SHOGUN_ARM_PUNCH, id(ARM_BLOCK): _SHOGUN_ARM_BLOCK}


def _shogun_torso(rows):
    """Торс сёгуна под ту же позу героя: рисунок свой, строки и колонки опоры те же."""
    return _SHOGUN_TORSO[id(rows)]


def _shogun_legs(rows):
    return _SHOGUN_LEGS[id(rows)]


def _shogun_arm(rows):
    return _SHOGUN_ARM[id(rows)]


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
SPRITES.update(fighter_frames("fight_hero_", HEAD_NINJA, lambda r: r, lambda r: r, lambda r: r, KO_NINJA))
SPRITES.update(fighter_frames("fight_rival_", HEAD_SHOGUN, _shogun_torso, _shogun_legs, _shogun_arm, KO_SHOGUN))
SPRITES.update({
    # Искра удара: косой крест двух росчерков клинка, золотое ядро, белые лучи и брызги.
    "fight_spark": [
        "................",
        ".W...........W..",
        "..W....Y....W...",
        "...W.......W....",
        "....WW...WW.....",
        ".....WY.YW......",
        "......YWY.......",
        ".Y...YWWWY...Y..",
        "......YWY.......",
        ".....WY.YW......",
        "....WW...WW.....",
        "...W.......W....",
        "..W....Y....W...",
        ".W...........W..",
        "................",
        "................",
    ],
    # Искра блока: дуга отбитого клинка, сталь белым по золотой кромке, две искры с краёв.
    "fight_guard": [
        "................",
        "......KKK...Y...",
        ".......KYK......",
        "........KWK.....",
        ".........KWK....",
        ".........KWYK...",
        "..........KWK...",
        "..........KWK...",
        "..........KWK...",
        "..........KWK...",
        ".........KWYK...",
        ".........KWK....",
        "........KWK.....",
        ".......KYK......",
        "......KKK...Y...",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KBRWY."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import ninja8
        ninja8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
