#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Замки» (#136): бойцы 16×32 сбоку, зеркало раздела «Файтинг» в
`pixel_sprites.py` и модуля `space8_fight.py`. Сборка кадров та же (голова 10 строк, торс 11,
ноги 11, те же смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и
космосом; рисунок частей свой. Палитра `castles8.PALETTE`: K чёрный, G камень и латы, R красный,
Y золото и дерево, W блики.

Герой: рыцарь, закрытый шлем с красным плюмажем и щелью для глаз, стальные латы, красный
табард с золотым поясом, на спине щит с золотым умбоном, золотые шпоры на сапогах. Соперник:
чёрный рыцарь, босс сеттинга: рогатый шлем с костяными рогами и красной щелью, чёрные доспехи
с каменной окантовкой, багровый плащ за спиной до колен. Силуэты разные: гладкий шлем с
плюмажем против двух рогов и длинного плаща.

    python3 tools/castles8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Рыцарь ------------------------------------------------------------------------------------

# Закрытый шлем: красный плюмаж стелется назад, горизонтальная щель, три дыхательных отверстия.
HEAD_KNIGHT = [
    "................",
    ".KRRRRRRK.......",
    "KRRRRKGGGGK.....",
    "..KKKGWWGGGK....",
    "...KGGWGGGGGK...",
    "...KGGKKKKKKGK..",
    "...KGGGGGGGGGK..",
    "...KGGGKGKGKGK..",
    "....KGGGGGGGK...",
    ".....KGGGGGK....",
]
# Торс в стойке: щит на спине слева, передняя рука согнута у подбородка, табард и золотой пояс.
TORSO_GUARD = [
    "..KKKKKGGGKKKK..",
    "..KRRKGWGGKGGGK.",
    "..KRYKGRRGKGGGK.",
    "..KRYKGRRKGGKKK.",
    "..KRRKGRRKGGK...",
    "..KKKKGRRGKK....",
    "....KGRRRRGK....",
    "....KYYYYYYK....",
    "....KKKKKKKK....",
    "....KRRRRRRK....",
    "....KRRRRRRK....",
]
# Замах верхнего: передняя рука отведена за плечо.
TORSO_WIND = [
    "..KKKKKGGGKKKK..",
    ".KRRRKGWGGKGGGK.",
    ".KRYRKGRRGKGGGK.",
    "..KKKKGRRGKKKK..",
    "....KGRRRGK.....",
    "....KGRRRRGK....",
    "....KGRRRRGK....",
    "....KYYYYYYK....",
    "....KKKKKKKK....",
    "....KRRRRRRK....",
    "....KRRRRRRK....",
]
# Торс без передней руки: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKKGGGK.....",
    "..KRRKGWGGK.....",
    "..KRYKGRRGK.....",
    "..KRYKGRRKGGK...",
    "..KRRKGRRKGGK...",
    "..KKKKGRRGKK....",
    "....KGRRRRGK....",
    "....KYYYYYYK....",
    "....KKKKKKKK....",
    "....KRRRRRRK....",
    "....KRRRRRRK....",
]
# Пропустил удар: корпус назад, щит слетел набок, передняя рука повисла.
TORSO_HIT = [
    "....KKGGGK......",
    "...KGWGGGGK.....",
    "..KRKGGRGGK.....",
    ".KRYKGGRRGK.....",
    ".KKKKGRRRGK.....",
    "....KGRRRRGK....",
    "....KGRRRRGKK...",
    "....KYYYYYKGGK..",
    "....KKKKKKKGGK..",
    "....KRRRRRRKK...",
    "....KRRRRRRK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): наруч, золотая манжета, стальная перчатка.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKWWGGK",
    "KGGGGGGGGYWGGGK",
    "KWWWWWWWWYGGGGK",
    ".KKKKKKKKKGGGGK",
    "..........KKKK.",
]
# Руки блока перед шлемом (колонка 9, строка 3): перчатка вверху, наручи, золотая манжета.
ARM_BLOCK = [
    ".KKKK.",
    "KWGGGK",
    "KGGGGK",
    "KKYYKK",
    ".KGGK.",
    ".KWGK.",
    ".KGGK.",
    ".KGGK.",
    "..KK..",
]
LEGS_STAND = [
    "....KWWKKWWK....",
    "...KWWK..KWWK...",
    "...KWWK..KWWK...",
    "..KWWK....KWWK..",
    "..KWWK....KWWK..",
    "..KWWK....KWWK..",
    "..KKKK....KKKK..",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KGGGK...KGGGK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KWWKKWWK....",
    "....KWWKKWWK....",
    "....KWWKKWWK....",
    "....KWWKKWWK....",
    "....KWWKKWWK....",
    "....KWWKKWWK....",
    "....KKKKKKKK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGGKGGGK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KWWWWWWK....",
    "...KWWWWWWWWKK..",
    "..KWWKKKKKKWWWK.",
    "..KGGK....KGGK..",
    ".KGGGK...KGGGK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самой земли (24 колонки).
LEGS_KICK = [
    "....KWWWWWWK............",
    "...KWWWWWWWWKKKKKKKKKK..",
    "..KWWKKWWWWWWWWWWWWWKGK.",
    "..KGGK.KKKKKKKKKKKKKGGGK",
    ".KGGGK..............KKKK",
]
# Рыцарь лежит на спине: плюмаж на шлеме, щель вверх, табард по груди, ноги, шпоры вверх.
KO_KNIGHT = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".RRR............................",
    "RRRRK...........................",
    ".KKKK...........................",
    "KGGGGK...KKKKK..................",
    "KGKKGKKKKGGGGKK.........KKK.KKK.",
    "KGGGGGKGGRRGGGGKKKKKKKKKKYYKKYYK",
    "KGGGGGKGGRRRGGGKGWGGGGGGKYYKKYYK",
    "KGGGGKKYYYYYYYYKGGGGGGGGKYYKKYYK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Чёрный рыцарь ------------------------------------------------------------------------------

# Рогатый шлем: два костяных рога дугой вверх, тёмный купол с каменной кромкой, красная щель.
HEAD_BLACK = [
    "................",
    "..W..........W..",
    "..WK........KW..",
    "..KWGGGGGGGGWK..",
    "...KGKKKKKKKGK..",
    "...KGKRRRRRKKK..",
    "...KGKKKKKKKGK..",
    "...KGGKGKGKGGK..",
    "....KGKKKKKGK...",
    ".....KGGGGGK....",
]
# Торс в стойке: багровый плащ за спиной, чёрные латы, каменная кромка, золотая пряжка пояса.
RIVAL_GUARD = [
    "..KKKKKGGGKKKK..",
    "..KRRKGKKGKGGGK.",
    "..KRRKGKRGKGGGK.",
    "..KRRKGKKKGGKKK.",
    "..KRRKGKKKGGK...",
    "..KRRKGGKKKK....",
    ".KRRKGKKKKKK....",
    ".KRRKKKYYKKK....",
    ".KRRKKKKKKKK....",
    ".KRRKGKKKKGK....",
    ".KRRKGKKKKGK....",
]
RIVAL_WIND = [
    "..KKKKKGGGKKKK..",
    ".KRRRKGKKGKGGGK.",
    ".KRRRKGKRGKGGGK.",
    "..KKKKGKKGKKKK..",
    "..KRRKGKKKK.....",
    ".KRRKGKKKKGK....",
    ".KRRKGKKKKGK....",
    ".KRRKKKYYKKK....",
    ".KRRKKKKKKKK....",
    ".KRRKGKKKKGK....",
    ".KRRKGKKKKGK....",
]
RIVAL_OPEN = [
    "..KKKKKGGGK.....",
    "..KRRKGKKGK.....",
    "..KRRKGKRGK.....",
    "..KRRKGKKKGGK...",
    "..KRRKGKKKGGK...",
    "..KRRKGGKKK.....",
    ".KRRKGKKKKKK....",
    ".KRRKKKYYKKK....",
    ".KRRKKKKKKKK....",
    ".KRRKGKKKKGK....",
    ".KRRKGKKKKGK....",
]
# Пропустил удар: корпус назад, плащ взметнулся вверх, передняя рука повисла.
RIVAL_HIT = [
    "....KKGGGK......",
    "..KRKGGKKGK.....",
    ".KRRKGKRGGK.....",
    "KRRRKGKKKGK.....",
    "KKKKKGKKKKK.....",
    "....KGKKKKKK....",
    "....KGKKKKKKK...",
    "....KKKYYKKGGK..",
    "....KKKKKKKGGK..",
    "....KGKKKKGKK...",
    "....KGKKKKGK....",
]
# Вытянутая рука верхнего удара: чёрный наруч с каменной кромкой, багровая манжета, перчатка.
RIVAL_ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKGGWGK",
    "KKKKKKKKKRGGGGK",
    "KGGGGGGGGRGGGGK",
    ".KKKKKKKKKGGGGK",
    "..........KKKK.",
]
RIVAL_ARM_BLOCK = [
    ".KKKK.",
    "KWGGGK",
    "KGGGGK",
    "KKRRKK",
    ".KKGK.",
    ".KKGK.",
    ".KKGK.",
    ".KKGK.",
    "..KK..",
]
# Чёрный рыцарь лежит: рог вверх, щель красная, плащ расстелился под ним по земле.
KO_BLACK = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "W...............................",
    "KWKKK...........................",
    "KGGGGK...KKKKK..................",
    "KKKKGKKKKGGGGKK.........KKK.KKK.",
    "KRRKGKKGKKRKKGGKKKKKKKKKKGGKKGGK",
    "KKKKGKKGKKKKKKGKGKKKKKKGKGGKKGGK",
    "KGGGGKKKYYKKKKGKGKKKKKKGKGGKKGGK",
    "KKKKKKKRRRRRRRRRRRRRRRRRRRRRRRRK",
    ".KRRRRRRRRRRRRRRRRRRRRRRRRRRRRK.",
    "..KKKKKKKKKKKKKKKKKKKKKKKKKKKK..",
]


def _runs(row):
    """Серии подряд идущих W в строке: (начало, конец включительно)."""
    out, k = [], 0
    while k < len(row):
        if row[k] == "W":
            e = k
            while e + 1 < len(row) and row[e + 1] == "W":
                e += 1
            out.append((k, e))
            k = e + 1
        else:
            k += 1
    return out


def _hero_legs(rows):
    """Ноги рыцаря: стальные латы, сапоги золотой кожей, блик на колене (третья строка)."""
    out = []
    for i, row in enumerate(rows):
        line = list(row.replace("G", "Y").replace("W", "G"))
        if i == 2 and len(rows) == 11:
            for s0, e0 in _runs(row):
                line[s0] = "W"
        out.append("".join(line))
    return out


def _rival_legs(rows):
    """Ноги чёрного рыцаря: чёрные поножи с каменной кромкой по краям серий, железные сапоги; в
    стойке и шаге позади висит плащ до колен."""
    out = []
    for row in rows:
        line = list(row)
        for s0, e0 in _runs(row):
            for k in range(s0, e0 + 1):
                line[k] = "G" if k in (s0, e0) and e0 - s0 >= 4 else ("G" if k == s0 else "K")
        out.append("".join(line))
    if len(rows) == 11 and len(rows[0]) == 16:
        for i in range(7):
            first = min(k for k, ch in enumerate(out[i]) if ch != ".")
            cloak = ("KRR" if i < 6 else "KKK")[-min(first, 3):] if first > 0 else ""
            out[i] = out[i][:first - len(cloak)] + cloak + out[i][first:]
    return out


def _same(rows):
    return rows


# --- Сборка кадров (как `pixel_sprites.fighter_frames`) --------------------------------------------

def _blank(w, h):
    return [["."] * w for _ in range(h)]


def _paste(canvas, rows, x, y):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != "." and 0 <= y + dy < len(canvas) and 0 <= x + dx < len(canvas[0]):
                canvas[y + dy][x + dx] = ch


def fighter_frames(prefix, head, torsos, legs, arms, ko):
    """Кадры бойца: стойка 2, шаг, верхний удар (замах и удар 24×32), присед и нижний удар
    24×32, блок, пропустил, KO 32×16. Смещения частей те же, что у пиратов. `torsos` это
    (стойка, замах, открытый, пропустил), `arms` это (удар, блок)."""
    guard, wind, opened, hit = torsos
    punch, block = arms

    def frame(w, parts):
        c = _blank(w, 32)
        for rows, x, y in parts:
            _paste(c, rows, x, y)
        return ["".join(r) for r in c]

    h = head
    crouch_top = [(h, 0, 12), (guard[:5], 0, 22)]
    return {
        prefix + "idle_0": frame(16, [(legs(LEGS_STAND), 0, 21), (guard, 0, 10), (h, 0, 0)]),
        prefix + "idle_1": frame(16, [(legs(LEGS_STAND), 0, 21), (guard[:10], 0, 11), (h, 0, 1)]),
        prefix + "walk": frame(16, [(legs(LEGS_WALK), 0, 21), (guard[:10], 0, 11), (h, 0, 1)]),
        prefix + "high_0": frame(16, [(legs(LEGS_STAND), 0, 21), (wind, 0, 10), (h, -1, 0)]),
        prefix + "high_1": frame(24, [(legs(LEGS_STAND), 0, 21), (opened, 0, 10), (h, 1, 0), (punch, 9, 8)]),
        prefix + "crouch": frame(16, [(legs(LEGS_CROUCH), 0, 27)] + crouch_top),
        prefix + "low_1": frame(24, [(legs(LEGS_KICK), 0, 27), (h, -1, 12), (guard[:5], -1, 22)]),
        prefix + "block": frame(16, [(legs(LEGS_STAND), 0, 21), (opened, 0, 10), (h, -1, 0), (block, 9, 3)]),
        prefix + "hit": frame(16, [(legs(LEGS_STAND), 0, 21), (hit, 0, 10), (h, -2, 1)]),
        prefix + "ko": ko,
    }


SPRITES = {}
SPRITES.update(fighter_frames(
    "fight_hero_", HEAD_KNIGHT, (TORSO_GUARD, TORSO_WIND, TORSO_OPEN, TORSO_HIT),
    _hero_legs, (ARM_PUNCH, ARM_BLOCK), KO_KNIGHT))
SPRITES.update(fighter_frames(
    "fight_rival_", HEAD_BLACK, (RIVAL_GUARD, RIVAL_WIND, RIVAL_OPEN, RIVAL_HIT),
    _rival_legs, (RIVAL_ARM_PUNCH, RIVAL_ARM_BLOCK), KO_BLACK))
SPRITES.update({
    # Искра удара: белая звезда с золотым ядром.
    "fight_spark": [
        "................",
        ".......W........",
        ".......W........",
        "..W....W....W...",
        "...W..YWY..W....",
        "....W.YWY.W.....",
        ".....YYWYY......",
        ".WWWWWWWWWWWWW..",
        ".....YYWYY......",
        "....W.YWY.W.....",
        "...W..YWY..W....",
        "..W....W....W...",
        ".......W........",
        ".......W........",
        "................",
        "................",
    ],
    # Искра блока: край щита дугой, каменная пластина с золотыми заклёпками и бликами.
    "fight_guard": [
        "................",
        "......KKK.......",
        ".......KWK......",
        "........KGK.....",
        ".........KYK....",
        ".........KWGK...",
        "..........KGK...",
        "..........KYK...",
        "..........KGK...",
        "..........KWK...",
        ".........KYGK...",
        ".........KGK....",
        "........KGK.....",
        ".......KWK......",
        "......KKK.......",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KWGRY."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import castles8
        castles8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
