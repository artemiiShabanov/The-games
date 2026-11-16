#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Супергерои» (#137): бойцы 16×32 сбоку, зеркало раздела «Файтинг» в
`pixel_sprites.py` и модуля `space8_fight.py`. Сборка кадров та же (голова 10 строк, торс 11,
ноги 11, те же смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами;
рисунок частей свой. Палитра `superheroes8.PALETTE`: K чёрный, B синее трико, Y жёлтое, R
красное, G зелёно-серое.

Свойства, на которые рассчитана демка: бойцы лицом вправо, ноги на нижней строке, середина
тела между колонками 7 и 8 (демка отражает влево); присед ниже на 12 строк; активные кадры
ударов 24×32, рука или нога уходит вправо за 16 колонок; KO 32×16, лёжа на спине головой назад.

Герой: синее трико, жёлтый плащ до пояса клином за спиной, жёлтые перчатки и высокие сапоги,
звезда на груди, чёрная маска-домино и хохолок вперёд (облик основы `superheroes16.py`).
Соперник это босс сеттинга, злодей-учёный: стальной шлем-купол с двумя электродами и искрами
на концах, красные очки, чёрные усы и бородка, стоячий ворот, зелёно-серый плащ за спиной до
щиколоток, красный халат с жёлтой застёжкой, стальные рукавицы. Силуэты разные: хохолок и
короткий плащ против купола с рогами электродов, ворота и длинной полы.

    python3 tools/superheroes8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Герой -------------------------------------------------------------------------------------

# Чёрные волосы с хохолком вперёд, маска-домино полосой с жёлтой прорезью глаза.
HEAD_HERO = [
    "................",
    "......KKKKKK.K..",
    ".....KKKKKKKKK..",
    "....KKKKKKKKK...",
    "....KKYYYYYYK...",
    "....KYKKKKKKK...",
    "....KYKKKYYKK...",
    "....KYYYYYYYK...",
    ".....KYYYYYK....",
    "......KBBBK.....",
]
# Торс в стойке: плащ клином слева, передняя перчатка у подбородка, звезда на груди, пояс.
TORSO_GUARD = [
    "..KKKKKBBBKKKK..",
    "..KYYKBBBBKYYYK.",
    ".KYYYKBBYBKYYYK.",
    ".KYYYKBBBKBBKKK.",
    "KYYYYKBBBKBBK...",
    "KYYYKKBBBBKK....",
    "KYYKKBBBBBBK....",
    "KKKKKYYYYYYK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Замах верхнего: передняя перчатка отведена за плечо, плащ подобран.
TORSO_WIND = [
    "..KKKKKBBBKKKK..",
    ".KYYYKBBBBKYYYK.",
    ".KYYYKBBYBKYYYK.",
    "..KKKKBBBBKKKK..",
    "..KYYKBBBBK.....",
    ".KYYYKBBBBBK....",
    ".KYYKKBBBBBK....",
    ".KKKKYYYYYYK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Торс без передней перчатки: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKKBBBK.....",
    "..KYYKBBBBK.....",
    ".KYYYKBBYBK.....",
    ".KYYYKBBBKYYK...",
    "KYYYYKBBBKYYK...",
    "KYYYKKBBBBKK....",
    "KYYKKBBBBBBK....",
    "KKKKKYYYYYYK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла, плащ смят.
TORSO_HIT = [
    "....KKBBBK......",
    "...KBBBBBBK.....",
    "..KYKBBYBBK.....",
    ".KYYKBBBBBK.....",
    ".KKKKBBBBBK.....",
    "..KYKBBBBBBK....",
    ".KYYKBBBBBBKK...",
    ".KKKKYYYYYKYYK..",
    "....KKKKKKKYYK..",
    "....KBBBBBBKK...",
    "....KBBBBBBK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): синий рукав и жёлтая перчатка.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKYYYYK",
    "KBBBBBBBBKYYYYK",
    "KBBBBBBBBKYYYYK",
    ".KKKKKKKKKYYYYK",
    "..........KKKK.",
]
# Руки блока перед лицом (колонка 9, строка 3).
ARM_BLOCK = [
    ".KKKK.",
    "KYYYYK",
    "KYYYYK",
    "KKYYKK",
    ".KBBK.",
    ".KBBK.",
    ".KBBK.",
    ".KBBK.",
    "..KK..",
]
# Ноги в трико, сапоги до середины голени.
LEGS_STAND = [
    "....KBBKKBBK....",
    "...KBBK..KBBK...",
    "...KBBK..KBBK...",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KKKK....KKKK..",
    "..KYYK....KYYK..",
    "..KYYK....KYYK..",
    "..KYYK....KYYK..",
    "..KYYYK...KYYYK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KKKKKKKK....",
    "....KYYKKYYK....",
    "....KYYKKYYK....",
    "....KYYKKYYK....",
    "....KYYYKYYYK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KBBBBBBK....",
    "...KBBBBBBBBKK..",
    "..KBBKKKKKKBBBK.",
    "..KYYK....KYYK..",
    ".KYYYK...KYYYK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самой земли (24 колонки).
LEGS_KICK = [
    "....KBBBBBBK............",
    "...KBBBBBBBBKKKKKKKKKK..",
    "..KBBKKBBBBBBBBBBBBKYYK.",
    "..KYYK.KKKKKKKKKKKKKYYYK",
    ".KYYYK..............KKKK",
]
# Лежит на спине: волосы слева, лицо вверх, плащ подстелен под спину.
KO_HERO = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK...........................",
    "KKYKYK...KKKKK..................",
    "KKYKYKKKKBBBBKK.........KKK.KKK.",
    "KKYKYYKBBBYBBBBKKKKKKKKKKYYKKYYK",
    "KKYYYYKBBBBBBBBKBBBBBBBBKYYKKYYK",
    "KKKYYKKYYYYYYYYKBBBBBBBBKYYKKYYK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Злодей-учёный (босс) ------------------------------------------------------------------------

# Стальной купол шлема с двумя электродами (жёлтые искры на концах), красные очки в два стекла,
# чёрные усы и бородка; слева за затылком стоячий ворот плаща.
HEAD_BOSS = [
    ".Y.........Y....",
    "..K.KKKKK.K.....",
    "...KGGGGGGK.....",
    "..KGGGGGGGGK....",
    "..KKKKKKKKKKK...",
    "...KYRRKRRKK....",
    "...KYYYYYYYK....",
    ".KKKYYKKKKYK....",
    ".KGKKYYKKYK.....",
    ".KGGKKKKKK......",
]
KO_BOSS = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "Y.....Y.........................",
    ".KKKKK..........................",
    "KGGGGK..........................",
    "KGGKRK...KKKKK..................",
    "KGGKYKKKKRRRRKK.........KKK.KKK.",
    "KGGKYKKRRRYRRRRKKKKKKKKKKRRKKRRK",
    "KGGKGGKRRRRRRRRKGGGGGGGGKRRKKRRK",
    "KGGGGKKGGGGGGGGKGGGGGGGGKRRKKRRK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]


def _boss_torso(rows):
    """Тело злодея из торса героя: трико становится красным халатом, звезда и пряжка это
    жёлтая застёжка в три пуговицы, перчатки стальные, клин плаща за спиной зелёно-серый и
    не кончается на поясе, а уходит полой вниз."""
    wide = rows[7][0] == "K"
    out = []
    for i, row in enumerate(rows):
        line = []
        for x, ch in enumerate(row):
            if ch == "B":
                ch = "R"
            elif ch == "Y":
                button = 0 < x < len(row) - 1 and row[x - 1] == "B" and row[x + 1] == "B"
                if i == 7 and 5 <= x <= 10:
                    ch = "Y" if x == 7 else "R"
                elif not button:
                    ch = "G"
            line.append(ch)
        if i == 5 and line[7] == "R":
            line[7] = "Y"
        line = "".join(line)
        # Пола плаща идёт ниже пояса: низ клина открыт, дальше серая полоса слева от халата.
        if i == 7:
            line = ("KGGGK" if wide else ".KGGK") + line[5:]
        elif i >= 8 and line.startswith("....K"):
            line = ("KGGG" if wide else ".KGG") + line[4:]
        out.append(line)
    return out


def _boss_legs(rows):
    """Полы халата красные до бедра, ниже серые брюки и красные резиновые сапоги; в стойке и
    шаге позади висит плащ до щиколоток."""
    skirt = 3 if len(rows) == 11 else 2
    out = [(row.replace("B", "R") if i < skirt else row.replace("B", "G")).replace("Y", "R")
           for i, row in enumerate(rows)]
    if len(rows) == 11 and len(rows[0]) == 16:
        for i in range(9):
            first = min(k for k, ch in enumerate(out[i]) if ch != ".")
            cloak = ("KGG" if i < 8 else "KKK")[-min(first, 3):] if first > 0 else ""
            out[i] = out[i][:first - len(cloak)] + cloak + out[i][first:]
    return out


def _boss_arm(rows):
    return [row.replace("B", "R").replace("Y", "G") for row in rows]


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
SPRITES.update(fighter_frames("fight_hero_", HEAD_HERO, lambda r: r, lambda r: r, lambda r: r, KO_HERO))
SPRITES.update(fighter_frames("fight_rival_", HEAD_BOSS, _boss_torso, _boss_legs, _boss_arm, KO_BOSS))
SPRITES.update({
    # Искра удара: комиксный «бах», жёлтая зубчатая вспышка с красным кольцом внутри.
    "fight_spark": [
        "................",
        ".......Y........",
        "..Y...YYY...Y...",
        "...YY.YRY.YY....",
        "...YYYYRYYYY....",
        "....YRRYRRY.....",
        "..YYYRYYYRYYY...",
        ".YYRRYYYYYRRYY..",
        "..YYYRYYYRYYY...",
        "....YRRYRRY.....",
        "...YYYYRYYYY....",
        "...YY.YRY.YY....",
        "..Y...YYY...Y...",
        ".......Y........",
        "................",
        "................",
    ],
    # Искра блока: синяя дуга силового щита с жёлтыми бликами и брызгами отбитого удара.
    "fight_guard": [
        "................",
        "......KKK.......",
        ".......KBK......",
        "........KBK.....",
        ".....Y...KBK....",
        ".........KYBK...",
        "..YY......KBK...",
        "..........KYK...",
        "....YY....KBK...",
        "..........KYK...",
        "..Y......KYBK...",
        ".........KBK....",
        ".....Y..KBK.....",
        ".......KBK......",
        "......KKK.......",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KBYRG."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import superheroes8
        superheroes8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
