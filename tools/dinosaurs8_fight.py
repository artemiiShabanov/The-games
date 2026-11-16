#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Динозавры» (#137): бойцы 16×32 сбоку, зеркало `space8_fight.py` и
раздела «Файтинг» в `pixel_sprites.py`. Сборка кадров та же (голова 10 строк, торс 11, ноги 11,
те же смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и космосом;
рисунок частей свой.

Герой: пещерный человек, чёрная копна с костью поперёк макушки, оранжевая пятнистая шкура
наискось через переднее плечо, голое заднее плечо, костяной браслет, обмотки из шкуры на
голенях, босые ступни. Соперник это босс сеттинга: вождь-шаман в черепе тираннозавра, белый
череп шире головы с глазницей и зубами над лицом, зелёная туника из кожи раптора, ожерелье и
пояс из зубов, плащ из перепонки птеродактиля за спиной до колен, костяные поножи. Силуэты
разные: узкая лохматая голова с костью против широкого черепа с плащом.

Палитра в `dinosaurs8.py`: K чёрный, O шкура, S кожа, G зелень, W кость.

    python3 tools/dinosaurs8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Пещерный человек ----------------------------------------------------------------------------

# Кость продета сквозь пучок на макушке: набалдашники по сторонам копны. Лицо вправо, тяжёлая
# челюсть, волосы закрывают затылок до шеи.
HEAD_CAVE = [
    "..W...KKK...W...",
    "..WWWWWWWWWWW...",
    "..W.KKKKKKK.W...",
    "...KKKKKKKKKK...",
    "...KKKSSSSSSK...",
    "...KKSSSSKSSK...",
    "...KKSSSSSSSSK..",
    "...KKSSSKKKSK...",
    "....KKSSSSSK....",
    ".....KSSSSK.....",
]
# Подол шкуры с пятнами: общий низ торса (строки 6..10).
_SKIRT = [
    "....KOOKOOOK....",
    "....KOOOOKOK....",
    "....KOOOOOOK....",
    "....KOOKOOOK....",
    "....KOOOOOOK....",
]
# Торс в стойке: задняя рука согнута слева, передний кулак у подбородка, шкура идёт наискось от
# переднего плеча к заднему бедру, заднее плечо голое.
TORSO_GUARD = [
    "..KKKKSSOOKKKK..",
    "..KSSKSOOOKSSSK.",
    "..KSSKOOKOKSSSK.",
    "..KSSKOOOKSSKKK.",
    "..KSSKOOOKSSK...",
    "..KKKKOOOOKK....",
] + _SKIRT
# Замах верхнего: оба кулака подняты к плечам, локти разведены.
TORSO_WIND = [
    "..KKKKSSOOKKKK..",
    ".KSSSKSOOOKSSSK.",
    ".KSSSKOOKOKSSSK.",
    "..KKKKOOOOKKKK..",
    "....KOOOOOK.....",
    "....KOOKOOOK....",
] + _SKIRT
# Торс без переднего кулака: под вытянутую руку удара и под руки блока.
TORSO_OPEN = [
    "..KKKKSSOOK.....",
    "..KSSKSOOOK.....",
    "..KSSKOOKOK.....",
    "..KSSKOOOKSSK...",
    "..KSSKOOOKSSK...",
    "..KKKKOOOOKK....",
] + _SKIRT
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла у бедра.
TORSO_HIT = [
    "....KKSOOK......",
    "...KSSOOOOK.....",
    "..KSKOOKOOK.....",
    ".KSSKOOOOOK.....",
    ".KKKKOOOOOK.....",
    "....KOOKOOOK....",
    "....KOOOOOOKK...",
    "....KOOOOKKSSK..",
    "....KOOOOOKSSK..",
    "....KOOKOOOKK...",
    "....KOOOOOOK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): голая рука, костяной браслет, кулак.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKSSSSK",
    "KSSSSSSSWWSSSSK",
    "KSSSSSSSWWSSKSK",
    ".KKKKKKKKKSSSSK",
    "..........KKKK.",
]
# Руки блока перед лицом (колонка 9, строка 3): кулак сверху, браслет под ним.
ARM_BLOCK = [
    ".KKKK.",
    "KSSSSK",
    "KSKSSK",
    "KKSSKK",
    ".KWWK.",
    ".KSSK.",
    ".KSSK.",
    ".KSSK.",
    "..KK..",
]
# Ноги: рваный край шкуры сверху, голые колени, обмотки на голенях, босые ступни.
LEGS_STAND = [
    "....KOSKKSOK....",
    "...KSSK..KSSK...",
    "...KSSK..KSSK...",
    "..KSSK....KSSK..",
    "..KSSK....KSSK..",
    "..KSSK....KSSK..",
    "..KKKK....KKKK..",
    "..KOOK....KOOK..",
    "..KOOK....KOOK..",
    "..KSSSK...KSSSK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KOSKKSOK....",
    "....KSSKKSSK....",
    "....KSSKKSSK....",
    "....KSSKKSSK....",
    "....KSSKKSSK....",
    "....KSSKKSSK....",
    "....KKKKKKKK....",
    "....KOOKKOOK....",
    "....KOOKKOOK....",
    "....KSSSKSSSK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KOOOOOOK....",
    "...KOOKOOOOOKK..",
    "..KSSKKKKKKSSSK.",
    "..KOOK....KOOK..",
    ".KSSSK...KSSSK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самой земли (24 колонки).
LEGS_KICK = [
    "....KOOOOOOK............",
    "...KOOKOOOOOKKKKKKKKKK..",
    "..KSSKKSSSSSSSSSSOOOKSK.",
    "..KOOK.KKKKKKKKKKKKKSSSK",
    ".KSSSK..............KKKK",
]
# Лежит на спине головой влево: кость торчит поперёк затылка, шкура на груди, ступни вверх.
KO_CAVE = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "WWKKK...........................",
    ".WKSSK...KKKKK..................",
    ".WKSKSKKKSSOOKK.........KKK.KKK.",
    ".WKSSSKSSOOKOOOKKKKKKKKKKSSKKSSK",
    ".WKKSSKSOOOOOKOKSSSSSSSSKOOKKOOK",
    ".WKKKKKOOOOOOOOKSSSSSSSSKOOKKOOK",
    "WWKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Вождь-шаман в черепе тираннозавра -------------------------------------------------------------

# Череп шире головы: высокий затылок с чёрной глазницей, морда с ноздрёй вытянута вперёд,
# верхняя челюсть зубами вниз над лицом, скула черепа закрывает затылок. Под черепом лицо с
# полосой охры на щеке.
HEAD_SHAMAN = [
    "...KKKKKKK......",
    "..KWWWWWWWKKKK..",
    ".KWWKKWWWWWWWWK.",
    ".KWWKKWWWWWWKWWK",
    ".KWWWWWWWWWWWWWK",
    ".KWWKWKWKWKWKWK.",
    ".KWKSSSSSKSSK...",
    ".KWKOOSSSSSSSK..",
    "..KKSSSSKKKSK...",
    "....KKSSSSK.....",
]
# Лежит: череп съехал набок глазницей вверх, плащ расстелен под спиной, костяные поножи вверх.
KO_SHAMAN = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "..KKKK..........................",
    ".KWWWWK.........................",
    "KWWKKWKKKKKKKKK.................",
    "KWWKKWWKSSGGGKK.........KKK.KKK.",
    "KWWWWKWKSGWGGGGKKKKKKKKKKSSKKSSK",
    "KWKWKSKSGGGGWGGKSSSSSSSSKWWKKWWK",
    "KOOOOKKOOOOOOOOKSSSSSSSSKWWKKWWK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]


def _shaman_torso(rows):
    """Тело вождя из торса героя: шкура становится зелёной туникой из кожи раптора (пятна это
    чешуя), на груди ожерелье из зубов, пояс костяной, руки голые. За спиной ниже плеч висит
    оранжевый плащ из перепонки птеродактиля."""
    out = []
    for i, row in enumerate(rows):
        line = list(row.replace("O", "G"))
        if i == 1:
            # Ожерелье: зубы через один по вырезу туники.
            for x in range(6, 10):
                if line[x] == "G" and x % 2 == 1:
                    line[x] = "W"
        if i == 7 and row[4] == "K":
            # Пояс из зубов поверх туники.
            for x in range(5, 11):
                if line[x] in "GK" and row[x] != "S" and x < row.rindex("O") + 1:
                    line[x] = "W" if x % 2 == 1 else "K"
        line = "".join(line)
        if i >= 5 and line.startswith("....K"):
            line = ".KOO" + line[4:]
        out.append(line)
    return out


def _shaman_legs(rows):
    """Край туники зелёный, ноги голые, обмотки это костяные поножи; в стойке и шаге позади
    висит плащ до колен."""
    out = []
    for i, row in enumerate(rows):
        hem = i < 2
        out.append(row.replace("O", "G" if hem else "W"))
    if len(rows) == 11 and len(rows[0]) == 16:
        for i in range(7):
            first = min(k for k, ch in enumerate(out[i]) if ch != ".")
            cloak = ("KOO" if i < 6 else "KKK")[-min(first, 3):] if first > 0 else ""
            out[i] = out[i][:first - len(cloak)] + cloak + out[i][first:]
    return out


def _shaman_arm(rows):
    """Рука вождя: вместо костяного браслета зелёный наруч из кожи раптора."""
    return [row.replace("W", "G") for row in rows]


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
SPRITES.update(fighter_frames("fight_hero_", HEAD_CAVE, lambda r: r, lambda r: r, lambda r: r, KO_CAVE))
SPRITES.update(fighter_frames("fight_rival_", HEAD_SHAMAN, _shaman_torso, _shaman_legs, _shaman_arm, KO_SHAMAN))
SPRITES.update({
    # Искра удара: зубчатая вспышка, оранжевый край и костяное ядро.
    "fight_spark": [
        "................",
        ".......O........",
        "..O....O....O...",
        "...OO.OOO.OO....",
        "....OOOWOOO.....",
        "...OOWWWWWOO....",
        "..OOWWWWWWWOO...",
        "OOOOWWWWWWWOOOO.",
        "..OOWWWWWWWOO...",
        "...OOWWWWWOO....",
        "....OOOWOOO.....",
        "...OO.OOO.OO....",
        "..O....O....O...",
        ".......O........",
        "................",
        "................",
    ],
    # Искра блока: удар принят на изогнутый бивень, от него летят оранжевые осколки.
    "fight_guard": [
        "................",
        "......KKKK......",
        "......KWWK......",
        ".......KWWK..O..",
        "........KWWK....",
        ".........KWWK...",
        ".........KWWK.O.",
        ".........KWWK...",
        ".........KWWK.O.",
        ".........KWWK...",
        "........KWWK....",
        ".......KWWK..O..",
        "......KWWK......",
        "......KKKK......",
        "................",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KOSGW."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import dinosaurs8
        dinosaurs8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
