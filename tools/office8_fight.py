#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Офис» (#137): бойцы 16×32 сбоку, зеркало `space8_fight.py` и раздела
«Файтинг» в `pixel_sprites.py`. Сборка кадров та же (голова 10 строк, торс 11, ноги 11, те же
смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и космосом; рисунок
частей свой.

Герой: клерк, тёмные волосы с чубом, очки, белая рубашка с красным галстуком и синим бейджем,
синие брюки, белые носки и чёрные ботинки, кулаки голые. Соперник: директор, босс сеттинга,
лысина с седым венчиком, синий костюм нараспашку, живот в белой рубашке с широким золотым
галстуком, в передней руке белая кружка «№1»: ей он и бьёт, и закрывается. Силуэты разные:
узкий клерк с чубом против грузного лысого директора с животом и кружкой.

    python3 tools/office8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Клерк -------------------------------------------------------------------------------------

# Голова вправо: чуб торчит над лбом, очки с белыми стёклами, нос, внизу белый воротник.
HEAD_CLERK = [
    "..........KK....",
    ".....KKKKKKK....",
    "....KKKKKKKKK...",
    "...KKKKYYYYYK...",
    "...KKKYYYYYYK...",
    "...KKYYWKYWKK...",
    "...KKYYYYYYYYK..",
    "....KYYYYYYYK...",
    "....KYYYYYYK....",
    ".....KWWWWK.....",
]
# Торс в стойке: задняя рука согнута у спины (рукав и кулак), передний кулак у подбородка,
# галстук по груди, бейдж у плеча, ремень с пряжкой, ниже брюки.
TORSO_GUARD = [
    "..KKKKKWWWKKKK..",
    "..KWWKWWRWKYYYK.",
    "..KWWKBWRWKYYYK.",
    "..KYYKWWRKWWKKK.",
    "..KYYKWWRKWWK...",
    "..KKKKWWRWKK....",
    "....KWWWRWWK....",
    "....KWWWRWWK....",
    "....KKKKYKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Замах верхнего: кулак отведён за плечо.
TORSO_WIND = [
    "..KKKKKWWWKKKK..",
    ".KYYYKWWRWKYYYK.",
    ".KYYYKBWRWKYYYK.",
    "..KKKKWWRWKKKK..",
    "....KWWWRWK.....",
    "....KWWWRWWK....",
    "....KWWWRWWK....",
    "....KWWWRWWK....",
    "....KKKKYKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Торс без переднего кулака: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKKWWWK.....",
    "..KWWKWWRWK.....",
    "..KWWKBWRWK.....",
    "..KYYKWWRKWWK...",
    "..KYYKWWRKWWK...",
    "..KKKKWWRWKK....",
    "....KWWWRWWK....",
    "....KWWWRWWK....",
    "....KKKKYKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Пропустил удар: корпус назад, галстук взлетел вперёд, задняя рука отброшена, передняя повисла.
TORSO_HIT = [
    "....KKWWWK......",
    "...KWWWWRWK.....",
    "..KYKWWWRRKK....",
    ".KYYKWWWWKRRK...",
    ".KKKKWWWWWKKK...",
    "....KWWWWWWK....",
    "....KWWWWWWKK...",
    "....KWWWWWKYYK..",
    "....KKKYKKKYYK..",
    "....KBBBBBBKK...",
    "....KBBBBBBK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): белый рукав с манжетой и кулак.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKYYYYK",
    "KWWWWWWWWKYYYYK",
    "KWWWWWWWWKYYYYK",
    ".KKKKKKKKKYYYYK",
    "..........KKKK.",
]
# Руки блока перед лицом (колонка 9, строка 3).
ARM_BLOCK = [
    ".KKKK.",
    "KYYYYK",
    "KYYYYK",
    "KKYYKK",
    ".KWWK.",
    ".KWWK.",
    ".KWWK.",
    ".KWWK.",
    "..KK..",
]
LEGS_STAND = [
    "....KBBKKBBK....",
    "...KBBK..KBBK...",
    "...KBBK..KBBK...",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KWWK....KWWK..",
    "..KKKK....KKKK..",
    "..KKKBK...KKKBK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KWWKKWWK....",
    "....KKKKKKKK....",
    "....KKKBKKKBK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KBBBBBBK....",
    "...KBBBBBBBBKK..",
    "..KBBKKKKKKBBBK.",
    "..KWWK....KWWK..",
    ".KKKBK...KKKBK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самого пола (24 колонки).
LEGS_KICK = [
    "....KBBBBBBK............",
    "...KBBBBBBBBKKKKKKKKKK..",
    "..KBBKKBBBBBBBBBBBBWKBK.",
    "..KWWK.KKKKKKKKKKKKKKKKK",
    ".KKKBK..............KKKK",
]
# Лежит на спине головой влево: очки на лице, галстук торчит вверх, ботинки носками в потолок.
KO_CLERK = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK....KK.....................",
    "KKYYYK..KRRK....................",
    "KKYWYKKKKWRWKKK.........KKK.KKK.",
    "KKYYYYKWWWRWWWWKKKKKKKKKKKBKKKBK",
    "KKYYYKKWWWWWWWWKBBBBBBBBWKKKWKKK",
    "KKKKKKKYYWWWWWWKBBBBBBBBWKKKWKKK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Директор ----------------------------------------------------------------------------------

# Голова шире, чем у клерка: гладкая лысина, седой венчик на затылке, тяжёлые брови, оскал,
# широкие щёки, белый воротник.
HEAD_BOSS = [
    "................",
    "....KKKKKKKK....",
    "...KYYYYYYYYK...",
    "..KWYYYYYYYYYK..",
    "..KWWYYKKYKKYK..",
    "..KWWYYWKYWKYK..",
    "..KWYYYYYYYYYYK.",
    "...KYYYWWWWWYK..",
    "...KYYYYYYYYYK..",
    ".....KWWWWK.....",
]
# Стойка: синий пиджак нараспашку, живот в рубашке вперёд, золотой галстук в две клетки,
# кружка «№1» у подбородка в передней руке, задний рукав с кулаком у спины.
BOSS_GUARD = [
    "..KKKKKWYWKWWW..",
    ".KBBKBBWYWKWRWW.",
    ".KBBKBBWYWKWRW..",
    ".KBBKBBWYWKBBKK.",
    ".KYYKBBWYYKBBK..",
    ".KKKKBBWYYWWK...",
    "...KBBBWYYWWWK..",
    "...KBBBWWYWWWK..",
    "...KBBKKKKYKKK..",
    "...KBBKBBKBBK...",
    "...KBBKBBKBBK...",
]
# Замах: задний кулак выставлен, кружка поднята без опоры на предплечье.
BOSS_WIND = [
    "..KKKKKWYWKWWW..",
    "KYYYKBBWYWKWRWW.",
    "KYYYKBBWYWKWRW..",
    ".KKKKBBWYWKKKK..",
    "...KBBBWYYWK....",
    "...KBBBWYYWWK...",
    "...KBBBWYYWWWK..",
    "...KBBBWWYWWWK..",
    "...KBBKKKKYKKK..",
    "...KBBKBBKBBK...",
    "...KBBKBBKBBK...",
]
# Без передней руки: под вытянутую руку с кружкой и под блок.
BOSS_OPEN = [
    "..KKKKKWYWK.....",
    ".KBBKBBWYWK.....",
    ".KBBKBBWYWK.....",
    ".KBBKBBWYKBBK...",
    ".KYYKBBWYKBBK...",
    ".KKKKBBWYYWWK...",
    "...KBBBWYYWWWK..",
    "...KBBBWWYWWWK..",
    "...KBBKKKKYKKK..",
    "...KBBKBBKBBK...",
    "...KBBKBBKBBK...",
]
# Пропустил удар: корпус назад, галстук взлетел, рука с кружкой повисла у бедра.
BOSS_HIT = [
    "....KKWYWK......",
    "...KBBWYWWK.....",
    "..KYKBWWYYKK....",
    ".KYYKBBWWKYYK...",
    ".KKKKBBWWWKKK...",
    "...KBBBWWWWK....",
    "...KBBBWWWWKK...",
    "...KBBBWWWKWWK..",
    "...KBBKKKKKWRK..",
    "...KBBKBBKBKK...",
    "...KBBKBBKBBK...",
]
# Удар кружкой: синий рукав, кисть, белая кружка с красной единицей.
BOSS_PUNCH = [
    "..........WWWW.",
    ".KKKKKKKKKWWWWW",
    "KBBBBBBBYYWRRWW",
    "KBBBBBBBYYWWRWW",
    ".KKKKKKKKKWWRWW",
    "..........WWWW.",
]
# Блок кружкой перед лицом.
BOSS_BLOCK = [
    "KWWWWK",
    "KWWRWK",
    "KWWRWK",
    "KKYYKK",
    ".KBBK.",
    ".KBBK.",
    ".KBBK.",
    ".KBBK.",
    "..KK..",
]
# Ноги толще, чем у клерка: брюки костюма в три клетки, чёрные туфли с отливом.
BOSS_STAND = [
    "...KBBBKKBBBK...",
    "..KBBBK..KBBBK..",
    "..KBBBK..KBBBK..",
    ".KBBBK....KBBBK.",
    ".KBBBK....KBBBK.",
    ".KBBBK....KBBBK.",
    ".KBBBK....KBBBK.",
    ".KBBBK....KBBBK.",
    ".KKKKK....KKKKK.",
    ".KKKKBK...KKKKBK",
    ".KKKKKK...KKKKKK",
]
BOSS_WALK = [
    "...KBBBKBBBK....",
    "...KBBBKBBBK....",
    "...KBBBKBBBK....",
    "...KBBBKBBBK....",
    "...KBBBKBBBK....",
    "...KBBBKBBBK....",
    "...KBBBKBBBK....",
    "...KBBBKBBBK....",
    "...KKKKKKKKK....",
    "...KKKKBKKKBK...",
    "...KKKKKKKKKK...",
]
BOSS_CROUCH = [
    "...KBBBBBBBK....",
    "..KBBBBBBBBBKK..",
    ".KBBBKKKKKKBBBK.",
    ".KBBBK....KBBK..",
    "KKKKBK...KKKBK..",
]
BOSS_KICK = [
    "...KBBBBBBBK............",
    "..KBBBBBBBBBKKKKKKKKKK..",
    ".KBBBKKBBBBBBBBBBBBBKKK.",
    ".KBBBK.KBBBBBBBBBBBBKKBK",
    "KKKKBK.KKKKKKKKKKKKKKKKK",
]
# Лежит на спине: лысина влево, живот горой с галстуком поверх, туфли носками в потолок.
KO_BOSS = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "..........KKKK..................",
    ".KKKK....KWYYWK.................",
    "KYYYYK..KBWYYWBK................",
    "KWYKYKKKKBWYYWBKK.......KKK.KKK.",
    "KWYYYYKBBBWWYWBBKKKKKKKKKKBKKKBK",
    "KWWYYKKBBBWWWWBBKBBBBBBBKKKKKKKK",
    "KKKKKKKYYBBBBBBBKBBBBBBBKKKKKKKK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# Части директора по частям клерка: сборка кадров просит часть героя, соперник отдаёт свою.
_BOSS_PARTS = (
    (TORSO_GUARD, BOSS_GUARD), (TORSO_WIND, BOSS_WIND), (TORSO_OPEN, BOSS_OPEN), (TORSO_HIT, BOSS_HIT),
    (ARM_PUNCH, BOSS_PUNCH), (ARM_BLOCK, BOSS_BLOCK),
    (LEGS_STAND, BOSS_STAND), (LEGS_WALK, BOSS_WALK), (LEGS_CROUCH, BOSS_CROUCH), (LEGS_KICK, BOSS_KICK),
)


def _boss(rows):
    """Часть директора на месте той же части клерка."""
    for mine, his in _BOSS_PARTS:
        if rows is mine:
            return his
    raise KeyError("нет части директора")


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
SPRITES.update(fighter_frames("fight_hero_", HEAD_CLERK, lambda r: r, lambda r: r, lambda r: r, KO_CLERK))
SPRITES.update(fighter_frames("fight_rival_", HEAD_BOSS, _boss, _boss, _boss, KO_BOSS))
SPRITES.update({
    # Искра удара: белая звезда с жёлтым ядром и красной серединой, по углам летят листки.
    "fight_spark": [
        "................",
        ".......W........",
        ".WW....W........",
        ".WW....W....W...",
        "...W..YWY..W....",
        "....W.YWY.W.....",
        ".....YYRYY......",
        ".WWWWWRRRWWWWW..",
        ".....YYRYY......",
        "....W.YWY.W.....",
        "...W..YWY..W....",
        "..W....W....WW..",
        ".......W....WW..",
        ".......W........",
        "................",
        "................",
    ],
    # Искра блока: удар принят на жёлтую папку с ярлыком, из неё торчит лист, слева штрихи.
    "fight_guard": [
        "................",
        ".......KKKKK....",
        "......KYYYYKKK..",
        "......KYWWWWWK..",
        "......KYYYYYYK..",
        "..WW..KYYYYYYK..",
        "......KYKKKKYK..",
        ".WWW..KYKWWKYK..",
        "......KYKKKKYK..",
        "..WW..KYYYYYYK..",
        "......KYYYYYYK..",
        "......KYYYYYYK..",
        "......KYYYYYYK..",
        "......KKKKKKKK..",
        "................",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KWBRY."), "чужой цвет в " + _name
for _mine, _his in _BOSS_PARTS:
    assert len(_mine) == len(_his) and len(_mine[0]) == len(_his[0]), "часть директора другого размера"


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import office8
        office8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
