#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Замки» (#136): бойцы 16×32 сбоку, зеркало раздела «Файтинг» в
`pixel_sprites.py` и модуля `space8_fight.py`. Сборка кадров та же (голова 10 строк, торс 11,
ноги 11, те же смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и
космосом; рисунок частей свой.

Герой: рыцарь, ведёрный шлем с плоским верхом и чёрной прорезью, красный плюмаж летит за
затылком, красный табард с золотым крестом и поясом, стальные наплечники, латные перчатки с
золотой манжетой и поножи. Соперник это босс сеттинга, чёрный рыцарь: рогатый шлем с золотыми
рогами и багровой светящейся прорезью, чернёные латы (чёрная заливка, серая кромка по верху
каждой пластины), багровый плащ за спиной до колен. Силуэты разные: ровная коробка шлема с
хвостом плюмажа против рогов врозь и широкой полы плаща.

    python3 tools/castles8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Рыцарь ------------------------------------------------------------------------------------

# Ведёрный шлем лицом вправо: плоский верх, блик на темени, прорезь до передней грани, под ней
# дыхательные отверстия, тёмный обод, стальной ворот. Плюмаж растёт из макушки и падает назад.
HEAD_KNIGHT = [
    "..KKK...........",
    ".KRRRKKKKKKKK...",
    "KRRRKWWGGGGGK...",
    "KRRKKWGGGGGGK...",
    "KRRKKGGKKKKKK...",
    "KRK.KGGGGGGGK...",
    ".K..KGGGKGKGK...",
    "....KGGGGGGGK...",
    "....KKKKKKKKK...",
    "......KGGGGK....",
]
# Торс в стойке: задняя рука с наплечником слева, передняя перчатка у подбородка, на груди
# золотой крест, пояс золотой, ниже юбка табарда.
TORSO_GUARD = [
    "..KKKKKGGGKKKK..",
    "..KGWKRYRRKWGGK.",
    "..KGGKYYYRKGGGK.",
    "..KGGKRYRKYGKKK.",
    "..KGGKRYRKGGK...",
    "..KKKKRRRRKK....",
    "....KRRRRRRK....",
    "....KYYYYYYK....",
    "....KRRRRRRK....",
    "....KRRRRRRK....",
    "....KRRKRRRK....",
]
# Замах верхнего: передняя перчатка отведена за плечо.
TORSO_WIND = [
    "..KKKKKGGGKKKK..",
    ".KGWGKRYRRKWGGK.",
    ".KGGGKYYYRKGGGK.",
    "..KKKKRYRRKKKK..",
    "....KRRYRRK.....",
    "....KRRRRRRK....",
    "....KRRRRRRK....",
    "....KYYYYYYK....",
    "....KRRRRRRK....",
    "....KRRRRRRK....",
    "....KRRKRRRK....",
]
# Торс без передней перчатки: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKKGGGK.....",
    "..KGWKRYRRK.....",
    "..KGGKYYYRK.....",
    "..KGGKRYRKWGK...",
    "..KGGKRYRKGGK...",
    "..KKKKRRRRKK....",
    "....KRRRRRRK....",
    "....KYYYYYYK....",
    "....KRRRRRRK....",
    "....KRRRRRRK....",
    "....KRRKRRRK....",
]
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла.
TORSO_HIT = [
    "....KKGGGK......",
    "...KRRRYRRK.....",
    "..KGKRYYYRK.....",
    ".KGWKRRYRRK.....",
    ".KKKKRRRRRK.....",
    "....KRRRRRRK....",
    "....KRRRRRRKK...",
    "....KYYYYYKWGK..",
    "....KRRRRRKGGK..",
    "....KRRRRRRKK...",
    "....KRRKRRRK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): наруч, золотая манжета и латная перчатка.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKWGGGK",
    "KGWWGGGGGYGGGGK",
    "KGGGGGGGGYGGGGK",
    ".KKKKKKKKKGGGGK",
    "..........KKKK.",
]
# Руки блока перед шлемом (колонка 9, строка 3): перчатки сверху, манжета, наручи.
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
# Ноги: поножи со светлым наколенником, ниже чёрного ремня латный башмак.
LEGS_STAND = [
    "....KGGKKGGK....",
    "...KGGK..KGGK...",
    "...KGGK..KGGK...",
    "..KWWK....KWWK..",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KKKK....KKKK..",
    "..KGGK....KGGK..",
    "..KGGK....KGGK..",
    "..KGGWK...KGGWK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KWWKKWWK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KKKKKKKK....",
    "....KGGKKGGK....",
    "....KGGKKGGK....",
    "....KGGWKGGWK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KYYYYYYK....",
    "...KGGGGGGGGKK..",
    "..KWGKKKKKKGWGK.",
    "..KGGK....KGGK..",
    ".KGGWK...KGGWK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самой земли (24 колонки).
LEGS_KICK = [
    "....KYYYYYYK............",
    "...KGGGGGGGGKKKKKKKKKK..",
    "..KWGKKGGGGGWWGGGGGGKGK.",
    "..KGGK.KKKKKKKKKKKKKGGWK",
    ".KGGWK..............KKKK",
]
# Лежит на спине головой влево: шлем прорезью вверх, плюмаж на земле, рука на груди, носки
# башмаков торчат вверх.
KO_KNIGHT = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "....KKKKK.......................",
    ".KKKGGKGGK..KKK.................",
    "KRRKWGKGGKKKGWGKK.......KKK.KKK.",
    "KRRKGGGKGKGRRGGYRKKKKKKKKGGKKGGK",
    "KRRKGGGGGKGRYRRYRGGGWWGGKWGKKWGK",
    ".KRKWGGGGKGRRRRYRGGGGGGGKGGKKGGK",
    "..KKKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Чёрный рыцарь, босс -------------------------------------------------------------------------

# Рогатый шлем: золотые рога с белыми остриями расходятся в стороны и вверх, шлем чернёный с
# серой кромкой по темени и затылку, прорезь светится багровым.
HEAD_BLACK = [
    ".KK...........KK",
    ".KWK.........KWK",
    ".KYYKKKKKKKKKYYK",
    "..KYKGGGGGGGKYK.",
    "...KKGKKKKKKKK..",
    "....KGKKRRRRK...",
    "....KGKKKKKKK...",
    "....KGKKGKGKK...",
    "....KKGGGGGKK...",
    "......KKKKKK....",
]
# Лежит на плаще: рога смотрят влево, прорезь вверх, под телом багровая пола.
KO_BLACK = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KK.............................",
    "KWYKKKKKK.......................",
    ".KYYGGRGGK..KKK.................",
    "..KKGKRKGKKKGGGKK.......KKK.KKK.",
    ".KKKGKKGKKGGKKKYGKKKKKKKKGGKKGGK",
    "KWYYGKKKKKKKRKKYKGGGGGGGKKGKKKGK",
    ".KKRRRRRRRRRRRRRRKKKKKKKKKKKKKKK",
    "..KKKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]
_PLATE = "GWR"


def _black(rows, belt=()):
    """Чернёные латы из частей рыцаря: сталь и табард чёрные, серыми остаются блики и верхняя
    кромка каждой пластины (пиксель, над которым обводка или пусто). Золото становится багровой
    эмалью, кроме строк `belt`: пояс у босса золотой."""
    out = []
    for i, row in enumerate(rows):
        line = []
        for x, ch in enumerate(row):
            if ch in _PLATE:
                above = rows[i - 1][x] if i > 0 else "K"
                ch = "G" if ch == "W" or above in "K." else "K"
            elif ch == "Y" and i not in belt:
                ch = "R"
            line.append(ch)
        out.append("".join(line))
    return out


def _cloak(rows, upto, hem=-1, narrow=0, start=0):
    """Багровый плащ за спиной: пола слева от тела в строках до `upto`, до трёх пикселей шириной
    (в первых `narrow` строках один: там плащ выглядывает из-за руки), выше строки `start`
    плаща нет. Строка `hem` это чёрный подол."""
    out = list(rows)
    for i in range(start, min(upto, len(rows))):
        first = min(k for k, ch in enumerate(rows[i]) if ch != ".")
        n = min(first - 1, 1 if i < narrow else 3)
        if n <= 0:
            continue
        fill = "K" * (n + 1) if i == hem else "K" + "R" * n
        out[i] = rows[i][:first - n - 1] + fill + rows[i][first:]
    return out


def _black_torso(rows):
    out = _black(rows, belt=(7,))
    # Корпус откинут назад (пропустил удар): плащ начинается ниже плеч, а не лезет на шлем.
    return _cloak(out, len(out), narrow=5, start=5 if rows[0].startswith("....") else 0)


def _black_legs(rows):
    """Ноги чернёные; в стойке и шаге позади висит плащ до колен, в приседе лежит на земле."""
    if len(rows) == 11:
        return _cloak(_black(rows), 7, hem=6)
    return _cloak(_black(rows, belt=(0,)), len(rows))


def _black_arm(rows):
    return _black(rows)


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
SPRITES.update(fighter_frames("fight_hero_", HEAD_KNIGHT, lambda r: r, lambda r: r, lambda r: r, KO_KNIGHT))
SPRITES.update(fighter_frames("fight_rival_", HEAD_BLACK, _black_torso, _black_legs, _black_arm, KO_BLACK))
SPRITES.update({
    # Искра удара: лязг стали, белый крест с золотым ядром и красными брызгами по диагоналям.
    "fight_spark": [
        "................",
        ".......W........",
        ".R.....W.....R..",
        "..Y....W....Y...",
        "...Y...W...Y....",
        "....Y.YWY.Y.....",
        ".....YYWYY......",
        ".WWWWWWWWWWWWW..",
        ".....YYWYY......",
        "....Y.YWY.Y.....",
        "...Y...W...Y....",
        "..Y....W....Y...",
        ".R.....W.....R..",
        ".......W........",
        "................",
        "................",
    ],
    # Искра блока: кромка стального щита дугой, золотые заклёпки и белые блики.
    "fight_guard": [
        "................",
        "......KKK.......",
        ".......KGK......",
        "........KWK.....",
        "........KGWK....",
        ".........KYGK...",
        ".........KGWK...",
        ".........KGWK...",
        ".........KYGK...",
        ".........KGWK...",
        ".........KYGK...",
        "........KGWK....",
        "........KWK.....",
        ".......KGK......",
        "......KKK.......",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KGRYW."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import castles8
        # Фон листа светлее обычного: чернёные латы босса на тёмном не видны.
        castles8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10,
                            bg=(0x5A, 0x6E, 0x8C, 255))
