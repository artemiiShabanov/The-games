#!/usr/bin/env python3
"""8-bit «Космос», гонки (вид сверху, #136): зеркало раздела «Гонки × 8-bit» в `pixel_sprites.py`.
Те же слоты и роли, что у пиратов: `race_water*` это трасса (гладкие плиты станции, демка мешает
два варианта и отражает их, поэтому рисунок симметричен), `race_shallow` обочина, которая
тормозит (россыпь камней на плитах), `race_sand*` стена (реголит, туда не заехать; во втором
варианте кратер), `race_rock` и `race_barrel` препятствия, `race_buoy` маячок на кромке,
`race_finish` финишная полоса с прозрачными краями. Транспорт в 8 направлениях из двух карт (на
восток и на северо-восток) поворотами на 90°; индекс по часовой на экране: 0 E, 1 SE, 2 S, 3 SW,
4 W, 5 NW, 6 N, 7 NE. Герой на луноходе, соперник на ховере пришельцев.

    python3 tools/space8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Луноход: белый корпус, бирюзовый колпак кабины впереди, четыре колеса по бортам, сзади пыль
# (строчная `g` становится металлом, как пена `w` у шлюпки).
ROVER_E = [
    "................",
    "................",
    "................",
    "..KKKK...KKKK...",
    "..KGGK...KGGK...",
    ".KKKKKKKKKKKKK..",
    ".KWWWWWWKCCCWWK.",
    "gKWGGWWKCCCCCWWK",
    "gKWGGWWKCCCCCWWK",
    ".KWWWWWWKCCCWWK.",
    ".KKKKKKKKKKKKK..",
    "..KGGK...KGGK...",
    "..KKKK...KKKK...",
    "................",
    "................",
    "................",
]

# Ховер пришельцев: фиолетовая капля острым носом вперёд, бирюзовый купол, сзади два сопла
# со свечением (строчная `c` становится бирюзой).
HOVER_E = [
    "................",
    "................",
    "................",
    "...KKK..........",
    "..KVVVKKKKK.....",
    ".cKVVVVVVVVKK...",
    "cCKKVVKCCKVVVKK.",
    ".cKVVKCCCCKVVVVK",
    ".cKVVKCCCCKVVVVK",
    "cCKKVVKCCKVVVKK.",
    ".cKVVVVVVVVKK...",
    "..KVVVKKKKK.....",
    "...KKK..........",
    "................",
    "................",
    "................",
]

HOVER_NE = [
    "................",
    "..........KKKKK.",
    "........KKVVVVK.",
    "......KKVVVVVVK.",
    ".....KVVVKCCVVK.",
    "....KVVVKCCCCVK.",
    "...KVVVVKCCCCVK.",
    "..KVVVVVVKCCVK..",
    ".KKVVVVVVVVVVK..",
    ".KVVKKVVVVVVK...",
    ".KVVKcKVVVKK....",
    "..KKcCKVVVK.....",
    "...cC.KVVK......",
    "..cC..KKKK......",
    "..c.............",
    "................",
]


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def _turn45(rows):
    """Карта, повёрнутая на 45° против часовой (нос с востока на северо-восток). Плейтест
    2026-11-15: диагональ лунохода это тот же спрайт, повёрнутый, а не отдельный рисунок. Каждый
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
    return {"%s_%d" % (prefix, i): [r.replace("g", "G").replace("c", "C") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", ROVER_E, _turn45(ROVER_E)))
SPRITES.update(frames("rival", HOVER_E, HOVER_NE))
SPRITES.update({
    # Трасса: плита с заклёпками по углам (при отражении тайла рисунок тот же) и блик.
    "race_water": [
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGWWGGGG",
        "GGGGGGGGGGGGWGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Второй вариант: световая метка разметки вместо блика.
    "race_water_1": [
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
        "GGGWWGGGGGGGGGGG",
        "GGGGGWGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGCCGGGGGGG",
        "GGGGGGGCCGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Обочина: россыпь камней на плитах, замедляет.
    "race_shallow": [
        "GGGGGGGGGGGGGGGG",
        "GGWWGGGGGGGKGGGG",
        "GGWKGGGGGGWWKGGG",
        "GGGGGGGKGGWWKGGG",
        "GGGGGGWWGGGKGGGG",
        "GKGGGGWKGGGGGGGG",
        "GGGGGGGGGGGGGWWG",
        "GGGGWWGGGGGGGWKG",
        "GGGWWWKGGGKGGGGG",
        "GGGGWKGGGWWGGGGG",
        "GGGGGGGGGWKGGGGG",
        "GWWGGGGGGGGGGGKG",
        "GWKGGGGKGGGGGWWG",
        "GGGGGGWWKGGGGWKG",
        "GGGGGGGWGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Стена: реголит, светлый грунт в оспинах; луноход сюда не заезжает. Во втором кратер.
    "race_sand": [
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWGWWWW",
        "WWWGWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWGGWWWWWWW",
        "WWWWWWWWGWWWWWWW",
        "WWWWWWWWWWWWWGWW",
        "WWWWWWWWWWWWWWWW",
        "WGWWWWWWWWWWWWWW",
        "WWWWWWWWWWGWWWWW",
        "WWWWGWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWGW",
        "WWWWWWWGWWWWWWWW",
        "WWGWWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
    ],
    "race_sand_1": [
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWWGWWW",
        "WWWWWWWWWWWWWWWW",
        "WWGWWWWWWWWWWWWW",
        "WWWWWKKKKKWWWWWW",
        "WWWWKGGGGGKWWWWW",
        "WWWKGGGGGGGKWWWW",
        "WWWKGGGGGGWKWWWW",
        "WWWKGGGGGWWKWWWW",
        "WWWWKGGWWWKWWWWW",
        "WWWWWKKKKKWWWGWW",
        "WWWWWWWWWWWWWWWW",
        "WGWWWWWWWWWWWWWW",
        "WWWWWWWWWGWWWWWW",
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
    ],
    # Препятствия: метеорит (угловатая глыба с жилой кристалла) и топливный баллон сверху.
    "race_rock": [
        "................",
        "................",
        "......KKKK......",
        "....KKGGGGKK....",
        "...KGGWWGGGGK...",
        "..KGGWWGGGGGGK..",
        "..KGGGGGGVGGGK..",
        ".KGGGKGGVVGGGGK.",
        ".KGGGGGGVGGGKGK.",
        ".KGGGGGGGGGGGGK.",
        "..KGGGKGGGGGGK..",
        "..KKGGGGGGGKK...",
        "....KKGGGKK.....",
        "......KKK.......",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWKKKKKKWK...",
        "...KWKVVVVKWK...",
        "...KWKVCCVKWK...",
        "...KWKVCCVKWK...",
        "...KWKVVVVKWK...",
        "...KWKKKKKKWK...",
        "....KWWWWWWK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    # Маячок на кромке трассы, украшение без столкновений.
    "race_buoy": [
        "................",
        "................",
        "................",
        "................",
        ".......CC.......",
        "......KKKK......",
        ".....KCCCCK.....",
        "....CKCWWCKC....",
        "....CKCWWCKC....",
        ".....KCCCCK.....",
        "......KKKK......",
        ".......CC.......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: шахматная световая полоса поперёк трассы, тайл кладётся вертикальной полосой.
    "race_finish": [
        "....KKKKCCCC....",
        "....KKKKCCCC....",
        "....KKKKCCCC....",
        "....KKKKCCCC....",
        "....CCCCKKKK....",
        "....CCCCKKKK....",
        "....CCCCKKKK....",
        "....CCCCKKKK....",
        "....KKKKCCCC....",
        "....KKKKCCCC....",
        "....KKKKCCCC....",
        "....KKKKCCCC....",
        "....CCCCKKKK....",
        "....CCCCKKKK....",
        "....CCCCKKKK....",
        "....CCCCKKKK....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), "размер карты %s" % _name
    assert set("".join(_rows)) <= set("KWCVG."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import space8
        space8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
