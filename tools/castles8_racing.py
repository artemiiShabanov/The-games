#!/usr/bin/env python3
"""8-bit «Замки», гонки (вид сверху, #136): зеркало раздела «Гонки × 8-bit» в `pixel_sprites.py`
через готовый модуль космоса `space8_racing.py`. Палитра `castles8.PALETTE`: K чёрный, G камень и
железо, R красный, Y золото и дерево, W блики. Те же слоты и роли, что у пиратов и космоса:
`race_water*` это трасса (брусчатка, демка мешает два варианта и отражает их, поэтому рисунок
симметричен), `race_shallow` обочина, которая тормозит (солома на брусчатке), `race_sand*` стена
(каменная кладка, туда не заехать; во втором варианте круглая сторожевая башенка), `race_rock` и
`race_barrel` препятствия (валун и стог сена), `race_buoy` столбик с вымпелом на кромке,
`race_finish` финишная полоса с прозрачными краями (гербовая шахматка). Транспорт в 8
направлениях из одной карты на восток: нечётные кадры это та же карта, повёрнутая на 45°, а чётные
поворачиваются на 90°; индекс по часовой на экране: 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N,
7 NE. Герой на боевой повозке с красным вымпелом, соперник на железной повозке чужого герба.

    python3 tools/castles8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Боевая повозка героя, нос на восток: четыре колеса по бортам, дощатый кузов, парусиновый верх,
# стальная морда впереди, сзади на древке вьётся красный вымпел (строчная `g` это пыль
# колёс, становится камнем `G`, как пена у шлюпки).
WAGON_E = [
    "................",
    "................",
    "................",
    "...KKKK...KKKK..",
    "...KGGK...KGGK..",
    "..KKKKKKKKKKKKK.",
    "RRKYYYYYYYYYGGK.",
    "RRRYWWWWWWWYYGGK",
    "RRRYWWWWWWWYYGGK",
    "RRKYYYYYYYYYGGK.",
    "..KKKKKKKKKKKKK.",
    "...KGGK...KGGK..",
    "...KKKK...KKKK..",
    "................",
    "................",
    "................",
]

# Железная повозка соперника, нос на восток: тёмный клёпаный кузов, багровая крыша, таранный
# клин впереди с острым белым наконечником, шипы на задней кромке.
IRON_E = [
    "................",
    "................",
    "................",
    "...KKKK..KKKK...",
    "...KGGK..KGGK...",
    "..KKKKKKKKKKKK..",
    ".KKGKGGGGGGKGKW.",
    ".KKGRRRRRRRGGKWW",
    ".KKGRRRRRRRGGKWW",
    ".KKGKGGGGGGKGKW.",
    "..KKKKKKKKKKKK..",
    "...KGGK..KGGK...",
    "...KKKK..KKKK...",
    "................",
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
    """8 направлений: `<prefix>_0..7`; строчная `g` это пыль и становится камнем."""
    out = {}
    e, ne = east, north_east
    for k in range(4):
        out[2 * k] = e
        out[(2 * k + 7) % 8] = ne
        e, ne = _cw(e), _cw(ne)
    return {"%s_%d" % (prefix, i): [r.replace("g", "G") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", WAGON_E, _turn45(WAGON_E)))
SPRITES.update(frames("rival", IRON_E, _turn45(IRON_E)))
SPRITES.update({
    # Трасса: брусчатка с тонким швом, плиты разного размера (при отражении тайла
    # швы те же), блик на каждой плите.
    "race_water": [
    "WWGGGKWWGGKWWGGG",
    "WGGGGKWGGGKWGGGG",
    "GGGGGKGGGGKGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGKWWGGGGGGKWWG",
    "GGGKWGGGGGGGKWGG",
    "GGGKGGGGGGGGKGGG",
    "GGGKGGGGGGGGKGGG",
    "GGGKGGGGGGGGKGGG",
    "GGGKGGGGGGGGKGGG",
    "GGGKGGGGGGGGKGGG",
    "GGGKGGGGGGGGKGGG",
    "KKKKKKKKKKKKKKKK",
    "WWGGGKWWGGKWWGGG",
    "WGGGGKWGGGKWGGGG",
    "GGGGGKGGGGKGGGGG",
    ],
    # Второй вариант: трещина и сколы на плитах.
    "race_water_1": [
    "GGGGGKGGGGKGGGKG",
    "GGGGGKGGGGKGGGKG",
    "GGGGGKGGGGKGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGKGGGGGGGGKGGG",
    "GGGKGGGGGGGGKGGG",
    "GGGKGGGKGGGGKGGG",
    "GKGKGGKGGGGGKGGG",
    "GGKKGGGKGGGGKGGG",
    "GGGKGGGGKGGGKGGG",
    "GGGKGGGGKGGGKGGG",
    "GGGKGGGGGGGGKGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGGGKGGGGKGGGGG",
    "GGGGGWGWGGKGGGGG",
    "GGGGGKGGGGKGGGGG",
    ],
    # Обочина: солома разбросана по брусчатке, замедляет.
    "race_shallow": [
    "GGGGGKGGGYYGGGGG",
    "GYGGGYGGGGKGGGGG",
    "GGYYYYGYGGYGGGGG",
    "KKKKYKKKKKYYYYKK",
    "GGGKGGGGYYYGKGGG",
    "GYYKGGGGGGGGYGGG",
    "GGGKGYYYGGGGKGYG",
    "GGGKGGGGYGGGKGGG",
    "GGYYGGGGGGGGYGGG",
    "GGGKGGGGGYGGKGYG",
    "GGGYYGYGGYYYKYYG",
    "GGYKGYYGGGGGKGGG",
    "KKKKKYYYYYKKKKKK",
    "GGGGGKGGGGKGGYYG",
    "GYYGGKGGGGYYGGGG",
    "GGGGGKGGGGYYGGGG",
    ],
    # Стена: каменная кладка (светлые блоки на серой растворной сетке, ряды со смещением);
    # повозка сюда не заезжает. Во втором варианте круглая сторожевая башенка с зубцами.
    "race_sand": [
        "GGGGGGGGGGGGGGGG",
        "WWWWWWWGWWWWWWWG",
        "WWGWWWWGWWWWWGWG",
        "WWWWWWWGWWWWWWWG",
        "GGGGGGGGGGGGGGGG",
        "WWWGWWWWWWWGWWWW",
        "WWWGWWGWWWWGWWWW",
        "WWWGWWWWWWWGWWWW",
        "GGGGGGGGGGGGGGGG",
        "WWWWWWWGWWWWWWWG",
        "WWWWGWWGWWWWWWWG",
        "WWWWWWWGWWGWWWWG",
        "GGGGGGGGGGGGGGGG",
        "WWWGWWWWWWWGWWWW",
        "WWWGWWWWWWWGWWGW",
        "WWWGWWWWWWWGWWWW",
    ],
    "race_sand_1": [
        "GGGGGGGGGGGGGGGG",
        "WWWWWWWKKWWWWWWG",
        "WWGWKKKGGKKKWGWG",
        "WWWKKGRRRRGKKWWG",
        "GGKKGRRRRRRGKKGG",
        "WWKGRKRRRRKRGKWW",
        "WWKRRRKRRKRRRKWW",
        "WKGRRRRWWRRRRGKW",
        "GKGRRRRWWRRRRGKG",
        "WWKRRRKRRKRRRKWG",
        "WWKGRKRRRRKRGKWG",
        "WWKKGRRRRRRGKKWG",
        "GGGKKGRRRRGKKGGG",
        "WWWGKKKGGKKKWWWW",
        "WWWGWWWKKWWGWWGW",
        "WWWGWWWWWWWGWWWW",
    ],
    # Препятствия: валун (круглая глыба с трещиной) и стог сена сверху (спираль соломы).
    "race_rock": [
        "................",
        "................",
        "......KKKKK.....",
        "....KKWWWGGKK...",
        "...KWWWGGGGGGK..",
        "..KWWWGGGGGGGGK.",
        "..KWWGGGGGKGGGK.",
        ".KGWGGGGGKKGGGGK",
        ".KGGGGGGKKGGGGGK",
        ".KGGGGGGGKGGGGGK",
        "..KGGGGGGGGGGGK.",
        "..KGGGGKGGGGGGK.",
        "...KKGGGKGGGKK..",
        ".....KKKKKKK....",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        ".....KKKKKK.....",
        "....KYYYKYWK....",
        "...KKYYYYKYWK...",
        "..KYYKYYYYKYWK..",
        "..KYYYKYYYYKYK..",
        "..KYYYYKKYYYKK..",
        "..KKYYYKKYYYYK..",
        "..KYKYYYYKYYYK..",
        "..KWYKYYYYKYYK..",
        "...KWYKYYYYKK...",
        "....KWYKYYYK....",
        ".....KKKKKK.....",
        "................",
        "................",
    ],
    # Столбик с вымпелом на кромке трассы, украшение без столкновений: каменное основание
    # сверху, красный вымпел вьётся вправо.
    "race_buoy": [
        "................",
        "................",
        "................",
        "....KKKK........",
        "...KGGGGK.......",
        "..KGWGGGGKKRR...",
        "..KGGGYYKRRRRRR.",
        "..KGGGYYKKRRRR..",
        "..KGGGGGGKKRR...",
        "...KGGGGK.......",
        "....KKKK........",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: гербовая шахматка поперёк трассы, тайл кладётся вертикальной полосой.
    "race_finish": [
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), "размер карты %s" % _name
    assert set("".join(_rows)) <= set("KWRYG."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import castles8
        castles8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
