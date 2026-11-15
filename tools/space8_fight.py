#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Космос» (#136): бойцы 16×32 сбоку, зеркало раздела «Файтинг» в
`pixel_sprites.py`. Сборка кадров та же (голова 10 строк, торс 11, ноги 11, те же смещения), так
что позы, высоты ударов и точки опоры совпадают с пиратами; рисунок частей свой.

Герой: космонавт, круглый шлем с бирюзовым визором, ранец за спиной, металлические перчатки и
ботинки. Соперник: командир пришельцев, широкий стеклянный купол с мозгом, серый плащ за
спиной до колен, фиолетовое тело, светящийся пояс. Силуэты разные: узкий шлем с ранцем против
широкого купола с плащом.

    python3 tools/space8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Космонавт ---------------------------------------------------------------------------------

HEAD_ASTRO = [
    "................",
    ".....KKKKKK.....",
    "....KWWWWWWK....",
    "...KWWWWWWWWK...",
    "...KWWWKKKKKWK..",
    "...KWWKCCCCCKK..",
    "...KWWKCWCCCKK..",
    "...KWWWKKKKKWK..",
    "....KWWWWWWWK...",
    ".....KGGGGGK....",
]
# Торс в стойке: ранец слева, передняя перчатка у подбородка, огонёк пульта на груди.
TORSO_GUARD = [
    "..KKKKKWWWKKKK..",
    "..KGGKWWWWKGGGK.",
    "..KGGKWWCWKGGGK.",
    "..KGGKWWWKWWKKK.",
    "..KGGKWWWKWWK...",
    "..KKKKWWWWKK....",
    "....KWWWWWWK....",
    "....KGGGGGGK....",
    "....KKKKKKKK....",
    "....KWWWWWWK....",
    "....KWWWWWWK....",
]
# Замах верхнего: передняя перчатка отведена за плечо.
TORSO_WIND = [
    "..KKKKKWWWKKKK..",
    ".KGGGKWWWWKGGGK.",
    ".KGGGKWWCWKGGGK.",
    "..KKKKWWWWKKKK..",
    "....KWWWWWK.....",
    "....KWWWWWWK....",
    "....KWWWWWWK....",
    "....KGGGGGGK....",
    "....KKKKKKKK....",
    "....KWWWWWWK....",
    "....KWWWWWWK....",
]
# Торс без передней перчатки: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKKWWWK.....",
    "..KGGKWWWWK.....",
    "..KGGKWWCWK.....",
    "..KGGKWWWKGGK...",
    "..KGGKWWWKGGK...",
    "..KKKKWWWWKK....",
    "....KWWWWWWK....",
    "....KGGGGGGK....",
    "....KKKKKKKK....",
    "....KWWWWWWK....",
    "....KWWWWWWK....",
]
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла.
TORSO_HIT = [
    "....KKWWWK......",
    "...KWWWWWWK.....",
    "..KGKWWCWWK.....",
    ".KGGKWWWWWK.....",
    ".KKKKWWWWWK.....",
    "....KWWWWWWK....",
    "....KWWWWWWKK...",
    "....KGGGGGKGGK..",
    "....KKKKKKKGGK..",
    "....KWWWWWWKK...",
    "....KWWWWWWK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): рукав и перчатка.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKGGGGK",
    "KWWWWWWWWWGGGGK",
    "KWWWWWWWWCGGGGK",
    ".KKKKKKKKKGGGGK",
    "..........KKKK.",
]
# Руки блока перед шлемом (колонка 9, строка 3).
ARM_BLOCK = [
    ".KKKK.",
    "KGGGGK",
    "KGGGGK",
    "KKGGKK",
    ".KWWK.",
    ".KWWK.",
    ".KWWK.",
    ".KWWK.",
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
# Нижний удар: присед, передняя нога выброшена вперёд у самой палубы (24 колонки).
LEGS_KICK = [
    "....KWWWWWWK............",
    "...KWWWWWWWWKKKKKKKKKK..",
    "..KWWKKWWWWWWWWWWWWWKGK.",
    "..KGGK.KKKKKKKKKKKKKGGGK",
    ".KGGGK..............KKKK",
]
KO_ASTRO = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK...........................",
    "KWWWWK...KKKKK..................",
    "KWCCWKKKKWWWWKK.........KKK.KKK.",
    "KWCWCWKWWWCWWWWKKKKKKKKKKGGKKGGK",
    "KWCCCWKWWWWWWWWKWWWWWWWWKGGKKGGK",
    "KWWWWKKGGGGGGGGKWWWWWWWWKGGKKGGK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Командир пришельцев -------------------------------------------------------------------------

# Широкий стеклянный купол с мозгом (извилины бирюзой, блик стекла белым), под ним лицо шире
# шеи с большим чёрным глазом и бирюзовым бликом.
HEAD_ALIEN = [
    "...KKKKKKKKKK...",
    "..KCVVCVVCVWWK..",
    ".KVVCVVVCVVCVWK.",
    ".KCVVCVVVCVVCVK.",
    "..KKKKKKKKKKKK..",
    "...KVVVVVVVVK...",
    "...KVVVVKKKVVK..",
    "...KVVVVKCKVVK..",
    "...KVVVVVVVVK...",
    "....KKVVVVKK....",
]
KO_ALIEN = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "..KKKK..........................",
    ".KCVVCK.........................",
    "KVVCVVKKKKKKKKK.................",
    "KCVVCVKKKVVVVKK.........KKK.KKK.",
    "KVVKVVKGGVVCVVVKKKKKKKKKKGGKKGGK",
    "KKVVVVKGGVVVVVVKVVVVVVVVKGGKKGGK",
    "KKKKKKKGGGGGGGGKVVVVVVVVKGGKKGGK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]


def _alien_torso(rows):
    """Тело командира из торса космонавта: скафандр фиолетовым, перчатки это руки, ранец слева
    становится серым плащом (остаётся металлом), пояс светится бирюзой."""
    out = []
    for i, row in enumerate(rows):
        line = []
        for x, ch in enumerate(row):
            if ch == "W":
                ch = "V"
            elif ch == "G":
                if i == 7 and 4 <= x <= 10 and row[4] == "K":
                    ch = "C"
                elif x >= 5:
                    ch = "V"
            line.append(ch)
        line = "".join(line)
        # Плащ спадает за спиной ниже плеч: серая пола слева от тела.
        if i >= 5 and line.startswith("....K"):
            line = ".KGG" + line[4:]
        out.append(line)
    return out


def _alien_legs(rows):
    """Ноги фиолетовые, ботинки металл; в стойке и шаге позади висит плащ до колен."""
    out = [row.replace("W", "V") for row in rows]
    if len(rows) == 11 and len(rows[0]) == 16:
        for i in range(7):
            first = min(k for k, ch in enumerate(out[i]) if ch != ".")
            cloak = ("KGG" if i < 6 else "KKK")[-min(first, 3):] if first > 0 else ""
            out[i] = out[i][:first - len(cloak)] + cloak + out[i][first:]
    return out


def _alien_arm(rows):
    return [row.replace("W", "V").replace("G", "V") for row in rows]


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
SPRITES.update(fighter_frames("fight_hero_", HEAD_ASTRO, lambda r: r, lambda r: r, lambda r: r, KO_ASTRO))
SPRITES.update(fighter_frames("fight_rival_", HEAD_ALIEN, _alien_torso, _alien_legs, _alien_arm, KO_ALIEN))
SPRITES.update({
    # Искра удара: белая звезда с бирюзовым ядром.
    "fight_spark": [
        "................",
        ".......W........",
        ".......W........",
        "..W....W....W...",
        "...W..CWC..W....",
        "....W.CWC.W.....",
        ".....CCWCC......",
        ".WWWWWWWWWWWWW..",
        ".....CCWCC......",
        "....W.CWC.W.....",
        "...W..CWC..W....",
        "..W....W....W...",
        ".......W........",
        ".......W........",
        "................",
        "................",
    ],
    # Искра блока: дуга силового щита бирюзой с белыми бликами.
    "fight_guard": [
        "................",
        "......KKK.......",
        ".......KWK......",
        "........KCK.....",
        ".........KCK....",
        ".........KWCK...",
        "..........KCK...",
        "..........KWK...",
        "..........KCK...",
        "..........KWK...",
        ".........KWCK...",
        ".........KCK....",
        "........KCK.....",
        ".......KWK......",
        "......KKK.......",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KWCVG."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import space8
        space8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
