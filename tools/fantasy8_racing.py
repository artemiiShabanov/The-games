#!/usr/bin/env python3
"""8-bit «Фэнтези», гонки (вид сверху, #137): зеркало `space8_racing.py` и раздела «Гонки × 8-bit»
в `pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*` это трасса (рунные плиты
лесной дороги, демка мешает два варианта и отражает их, поэтому рисунок симметричен),
`race_shallow` обочина, которая тормозит (мох и корни на плитах), `race_sand*` стена (чаща,
туда не заехать; во втором варианте гигантский цветок), `race_rock` и `race_barrel` препятствия
(рунный камень и плетёный короб), `race_buoy` фонарь-цветок на кромке, `race_finish` финишная
полоса с прозрачными краями. Транспорт в 8 направлениях из одной карты на восток: диагональ это
она же, повёрнутая на 45° (`_turn45`), остальное поворотами на 90°; индекс по часовой на экране:
0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE. Герой в гномьей вагонетке на колёсах, соперник в
гоблинской вагонетке с тараном. Парусов и мачт нет: это колёсные тележки. Палитра в
`fantasy8.py`: K чёрный, B мантия и камень, G зелень, Y золото и дерево, W свет.

    python3 tools/fantasy8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Гномья вагонетка: золотистый дощатый кузов в железной окантовке на четырёх колёсах по
# бортам (светлые ступицы); маг сидит ближе к носу, сверху видна синяя шляпа в тёмной обводке
# с золотой лентой и светлым кончиком, на корме груз кристаллов, спереди два фонаря, сзади
# искры из-под колёс (строчная `y` становится золотом, как пена `w` у шлюпки).
CART_E = [
    "................",
    "................",
    "...KKKK..KKKK...",
    "...KWWK..KWWK...",
    "..KKKKKKKKKKKK..",
    ".KYYYYYYKKKKYYK.",
    ".KYWWYYKBBBBKYKW",
    "yKYWWYYKBYWBKYK.",
    "yKYWWYYKBYWBKYK.",
    ".KYWWYYKBBBBKYKW",
    ".KYYYYYYKKKKYYK.",
    "..KKKKKKKKKKKK..",
    "...KWWK..KWWK...",
    "...KKKK..KKKK...",
    "................",
    "................",
]

# Гоблинская вагонетка: зелёный кузов клином к носу, на носу костяной таран из двух клыков,
# задние колёса крупные с золотыми ступицами, передние мелкие; внутри гоблин (зелёная макушка
# в тёмной обводке, светлые глаза смотрят вперёд) и мешок награбленного золота на корме, сзади зелёный
# чад (строчная `g` становится зеленью). Диагональ тем же поворотом на 45°.
GOBLIN_E = [
    "................",
    "................",
    "..KKKK..........",
    "..KYYK....KKK...",
    ".KKKKKKKKKKYK...",
    ".KGGGGGGGGKKKK..",
    "gKGYYGKKKKGGGKKW",
    "gKGYYGKGGWKGGGK.",
    "gKGYYGKGGWKGGGK.",
    "gKGYYGKKKKGGGKKW",
    ".KGGGGGGGGKKKK..",
    ".KKKKKKKKKKYK...",
    "..KYYK....KKK...",
    "..KKKK..........",
    "................",
    "................",
]


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def _turn45(rows):
    """Карта, повёрнутая на 45° против часовой (нос с востока на северо-восток). Плейтест
    2026-11-15: диагональ транспорта это тот же спрайт, повёрнутый, а не отдельный рисунок. Каждый
    пиксель берёт цвет большинства из девяти проб, так края выходят без дыр."""
    n = len(rows)
    mid = (n - 1) / 2.0
    k = 0.7071067811865476
    out = []
    for y in range(n):
        line = ""
        for x in range(n):
            votes = {}
            for sy in (-0.33, 0.0, 0.33):
                for sx in (-0.33, 0.0, 0.33):
                    dx, dy = x + sx - mid, y + sy - mid
                    u = int(round(dx * k - dy * k + mid))
                    v = int(round(dx * k + dy * k + mid))
                    ch = rows[v][u] if 0 <= u < n and 0 <= v < n else "."
                    votes[ch] = votes.get(ch, 0) + 1
            line += max(votes, key=lambda c: (votes[c], c != "."))
        out.append(line)
    return out


def frames(prefix, east, north_east):
    """8 направлений: `<prefix>_0..7`; строчные буквы следа становятся цветом."""
    out = {}
    e, ne = east, north_east
    for k in range(4):
        out[2 * k] = e
        out[(2 * k + 7) % 8] = ne
        e, ne = _cw(e), _cw(ne)
    return {"%s_%d" % (prefix, i): [r.replace("g", "G").replace("y", "Y") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", CART_E, _turn45(CART_E)))
SPRITES.update(frames("rival", GOBLIN_E, _turn45(GOBLIN_E)))
SPRITES.update({
    # Трасса: рунная плита со сколами по углам (при отражении тайла рисунок тот же) и блик.
    "race_water": [
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBWWBBBB",
        "BBBBBBBBBBBBWBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Второй вариант: золотая руна-ромб в середине плиты вместо блика.
    "race_water_1": [
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
        "BBBWWBBBBBBBBBBB",
        "BBBBBWBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBYYBBBBBBB",
        "BBBBBBYBBYBBBBBB",
        "BBBBBBYBBYBBBBBB",
        "BBBBBBBYYBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Обочина: кочки мха и корни поверх плит, замедляет.
    "race_shallow": [
        "BBBBBBBBBBBBBBBB",
        "BBGGBBBBBBBKBBBB",
        "BGGGKBBBBBGGKBBB",
        "BBGKBBBKBBGGGKBB",
        "BBBBBBGGBBBGKBBB",
        "BKBBBGGGKBBBBBBB",
        "BBBBBBGKBBBBBGGB",
        "BBBBGGBBBBBBGGGK",
        "BBBGGGKBBBKBBGKB",
        "BBBBGKBBBGGBBBBB",
        "BBBBBBBBGGGKBBBB",
        "BGGBBBBBBGKBBBKB",
        "GGGKBBBKBBBBBGGB",
        "BGKBBBGGKBBBGGGK",
        "BBBBBBBGBBBBBGKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Стена: чаща, сплошная листва с тенями и золотыми светляками; вагонетка сюда не
    # заезжает. Во втором варианте гигантский цветок.
    "race_sand": [
        "GGGGGGGGGGGGGGGG",
        "GGGGGKGGGGGGGGGG",
        "GGGGKKGGGGGGYGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGKGGGGG",
        "GYGGGGGGGKKGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGKG",
        "GGGKGGGGGGGGGKKG",
        "GGKKGGGGGGGGGGGG",
        "GGGGGGGGYGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGKGGGG",
        "GGGGGKGGGGKKGGGG",
        "GGGGKKGGGGGGGGYG",
        "GGGGGGGGGGGGGGGG",
    ],
    "race_sand_1": [
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGKKGGG",
        "GGGGGKKKKKGGGGGG",
        "GGGKKWWKWWKKGGGG",
        "GGKWWWWKWWWWKGGG",
        "GGKWWWKYKWWWKGGG",
        "GGGKKKYYYKKKGGGG",
        "GGKWWWKYKWWWKGGG",
        "GGKWWWWKWWWWKGGG",
        "GGGKKWWKWWKKGGGG",
        "GGGGGKKKKKGGGGGG",
        "GKGGGGGGGGGGGYGG",
        "KKGGGGGGGGGGGGGG",
        "GGGGGGGGGKGGGGGG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Препятствия: рунный камень (светлый валун со сколами и синей руной) и плетёный короб
    # сверху (квадратная корзина с плетением и ремнём крест-накрест).
    "race_rock": [
        "................",
        "................",
        "......KKKK......",
        "....KKWWWWKK....",
        "...KWWWWWWWWK...",
        "..KWWWBWWBWWWK..",
        "..KWWWBWWBWWWK..",
        ".KWWWWBBBBWWWWK.",
        ".KWWKWWBBWWWWWK.",
        ".KWWWWWBBWWWKWK.",
        "..KWWWWBBWWWWK..",
        "..KKWWWWWWWKK...",
        "....KKWWWKK.....",
        "......KKK.......",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        "................",
        "...KKKKKKKKKK...",
        "...KYYKYYKYYK...",
        "...KYKYYKYYKK...",
        "...KKYYKYYKYK...",
        "...KYYKWWKYYK...",
        "...KYKYWWYYKK...",
        "...KKYYKYYKYK...",
        "...KYYKYYKYYK...",
        "...KYKYYKYYKK...",
        "...KKKKKKKKKK...",
        "................",
        "................",
        "................",
    ],
    # Фонарь-цветок на кромке трассы, украшение без столкновений: четыре золотых лепестка
    # и светящаяся сердцевина.
    "race_buoy": [
        "................",
        "................",
        "................",
        "......KKKK......",
        "......KYYK......",
        "......KYYK......",
        "...KKKKWWKKKK...",
        "...KYYWWWWYYK...",
        "...KYYWWWWYYK...",
        "...KKKKWWKKKK...",
        "......KYYK......",
        "......KYYK......",
        "......KKKK......",
        "................",
        "................",
        "................",
    ],
    # Финиш: шахматная золотая полоса поперёк трассы, тайл кладётся вертикальной полосой.
    "race_finish": [
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), "размер карты %s" % _name
    assert set("".join(_rows)) <= set("KBGYW."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import fantasy8
        fantasy8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
