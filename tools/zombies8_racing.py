#!/usr/bin/env python3
"""8-bit «Зомби», гонки (вид сверху, #137): зеркало модуля космоса `space8_racing.py` и раздела
«Гонки × 8-bit» в `pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*` это
трасса (ночной асфальт, демка мешает два варианта и отражает их, поэтому рисунок спокойный и
стыкуется при отражении: выбоины по углам, во втором варианте стёртый штрих разметки),
`race_shallow` обочина, которая тормозит (грязь и сухой бурьян поверх асфальта), `race_sand*`
стена (тёмная кладбищенская земля в бурьяне, туда не заехать; во втором варианте могильный холм
с крестом), `race_rock` и `race_barrel` препятствия (надгробие и мусорный бак), `race_buoy`
дорожный конус на кромке, `race_finish` финишная полоса с прозрачными краями (шашечка). Транспорт
в 8 направлениях из двух карт (на восток и на северо-восток) поворотами на 90°; индекс по часовой
на экране: 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE. Диагональ это та же карта, повёрнутая на
45°, отдельно не рисуется. Герой на красном пикапе с решёткой, соперник на чёрном катафалке.
Парусов и мачт нет: это машины, силуэт сверху автомобильный.

    python3 tools/zombies8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Пикап выжившего: красный кузов, четыре колеса по бортам, сзади открытый кузов с припасами
# (ящик и канистра), кабина с белой полосой лобового стекла, капот, на носу тёмная решётка между
# белыми фарами. Строчная `g` это выхлоп за кормой, становится зелёным.
PICKUP_E = [
    "................",
    "................",
    "................",
    "..KKKK...KKKK...",
    "..KBBK...KBBK...",
    ".KKKKKKKKKKKKKK.",
    ".KRBBBBKRRWRRRWK",
    "gKRBWWBKRRWRRRKK",
    "gKRBBGBKRRWRRRKK",
    ".KRBBBBKRRWRRRWK",
    ".KKKKKKKKKKKKKK.",
    "..KBBK...KBBK...",
    "..KKKK...KKKK...",
    "................",
    "................",
    "................",
]

# Катафалк: длинный узкий чёрный кузов, колёса утоплены в борта (видны белые колпаки), на крыше
# белый крест головой вперёд, стёкла и фары светятся мертвенно-зелёным, на капоте синий блик.
# Силуэт другой: сплошной кузов без грузовой площадки, нос клином. Строчная `w` это пыль, становится белым.
HEARSE_E = [
    "................",
    "................",
    "................",
    "...KWK....KWK...",
    "..KKKKKKKKKKKK..",
    "wKKKKKKWWKKKKK..",
    ".KKKKKKWWKKGKGK.",
    ".KGKWWWWWWKGBBKK",
    ".KGKWWWWWWKGBBKK",
    ".KKKKKKWWKKGKGK.",
    "wKKKKKKWWKKKKK..",
    "..KKKKKKKKKKKK..",
    "...KWK....KWK...",
    "................",
    "................",
    "................",
]


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def _turn45(rows):
    """Карта, повёрнутая на 45° против часовой (нос с востока на северо-восток). Диагональ
    машины это тот же спрайт, повёрнутый, а не отдельный рисунок. Каждый пиксель берёт цвет
    большинства из девяти проб, так края выходят без дыр."""
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
    return {"%s_%d" % (prefix, i): [r.replace("g", "G").replace("w", "W") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", PICKUP_E, _turn45(PICKUP_E)))
SPRITES.update(frames("rival", HEARSE_E, _turn45(HEARSE_E)))
SPRITES.update({
    # Трасса: ночной асфальт, выбоины по углам (при отражении тайла рисунок тот же) и трещина.
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
        "BBBBBBBBBKBBBBBB",
        "BBBBBBBBBBKKBBBB",
        "BBBBBBBBBBBBKBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Второй вариант: стёртый штрих разметки и пучок травы, пробившей асфальт.
    "race_water_1": [
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
        "BBBGBBBBBBBBBBBB",
        "BBGKGBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBWWBWBBBBBB",
        "BBBBBBWBWWBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Обочина: лужи грязи и сухой бурьян поверх асфальта, замедляет.
    "race_shallow": [
        "BBBBBBBBBBBBBBBB",
        "BBGBGBBBBBBKKBBB",
        "BBBGBBBBBBKKKKBB",
        "BBBKBBBGBBBKKBBB",
        "BBBBBBGBGBBBBBBB",
        "BKKBBBBGBBBBBBBB",
        "KKKKBBBKBBBBGBGB",
        "BKKBBBBBBBBBBGBB",
        "BBBBBGBBBKKBBKBB",
        "BBBBGBGBKKKKBBBB",
        "BBBBBGBBBKKKBBBB",
        "BGBBBKBBBBBBBBGB",
        "GBGBBBBBBBBBBGBG",
        "BGBBBBBKKBBBBBGB",
        "BKBBBBKKKKBBBBKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Стена: тёмная кладбищенская земля в пучках бурьяна и осколках кости; сюда не заехать.
    "race_sand": [
        "KKKKKKKKKKKKKKKK",
        "KKGKGKKKKKKKKKKK",
        "KKKGKKKKKKGKKKKK",
        "KKKGKKKKKGKGKKKK",
        "KKKKKKKKKKGKKKKK",
        "KKKKKKGKKKKKKKKK",
        "KKKKKKKKKKKKKWKK",
        "KGKKKKKKKKKKKKKK",
        "GKGKKKKKGKGKKKKK",
        "KGKKKKKKKGKKKKKK",
        "KKKKKKKKKGKKKKGK",
        "KKKKWKKKKKKKKKKK",
        "KKKKKKKKKKKKGKGK",
        "KKKKKKGKKKKKKGKK",
        "KKKKKGKGKKKKKGKK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Второй вариант: могильный холм с белым крестом в изголовье.
    "race_sand_1": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKGKGK",
        "KKKKKKKWWKKKKGKK",
        "KGKKKKKWWKKKKKKK",
        "GKGKKWWWWWWKKKKK",
        "KGKKKWWWWWWKKKKK",
        "KKKKKKKWWKKKKKKK",
        "KKKKKKKWWKKKKKKK",
        "KKKKKBBWWBBKKKKK",
        "KKKKBGGBBGGBKKKK",
        "KKKKBGGGGGGBKKKK",
        "KKKKBGGGGGGBKGKK",
        "KKKKBGGGGGGBGKGK",
        "KGKKKBBBBBBKKGKK",
        "KKGKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Препятствия: надгробие (скруглённая плита с крестом, мох у подножия) и мусорный бак
    # (жестяной, ребристый, крышка с ручкой, по стенке потёк зелёной жижи).
    "race_rock": [
        "................",
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWWWKKWWBK...",
        "...KWWWKKWWBK...",
        "...KWKKKKKKBK...",
        "...KWWWKKWWBK...",
        "...KWWWKKWWBK...",
        "...KWWWKKWWBK...",
        "...KWWWWWWBBK...",
        "..KKBBBBBBBBKK..",
        "..KGGBGGGBGGGK..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        "......KKKK......",
        "....KKKWWKKK....",
        "...KWWWWWWWBK...",
        "...KKKKKKKKKK...",
        "....KWKWWKBK....",
        "....KWKWWKBK....",
        "....KWKWWKBK....",
        "....KWKGGKBK....",
        "....KWGGGGBK....",
        "....KWKGWKBK....",
        "....KKKKKKKK....",
        "................",
        "................",
        "................",
    ],
    # Дорожный конус на кромке трассы, украшение без столкновений: вид сверху, квадратная
    # подошва, красные и белые кольца.
    "race_buoy": [
        "................",
        "................",
        "................",
        "................",
        "....KKKKKKKK....",
        "....KRRRRRRK....",
        "....KRWWWWRK....",
        "....KRWRRWRK....",
        "....KRWRRWRK....",
        "....KRWWWWRK....",
        "....KRRRRRRK....",
        "....KKKKKKKK....",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: чёрно-белая шашечка поперёк трассы, тайл кладётся вертикальной полосой.
    "race_finish": [
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), "размер карты %s" % _name
    assert set("".join(_rows)) <= set("KRGWB."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import zombies8
        zombies8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
