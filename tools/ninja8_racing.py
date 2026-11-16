#!/usr/bin/env python3
"""8-bit «Ниндзя», гонки (вид сверху, #137): зеркало модуля космоса `space8_racing.py` и раздела
«Гонки × 8-bit» в `pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*` это
трасса (каменная дорожка сада, демка мешает два варианта и отражает их, поэтому рисунок
симметричен), `race_shallow` обочина, которая тормозит (мох, солома и палые листья клёна на
камне), `race_sand*` стена (белёная стена усадьбы, туда не заехать; во втором варианте герб
клана), `race_rock` и `race_barrel` препятствия (каменный фонарь и бочка сакэ в соломе),
`race_buoy` бумажный фонарик на кромке, `race_finish` финишная полоса с прозрачными краями
(красно-белая шашечка знамени). Транспорт в 8 направлениях из одной карты на восток: диагональ
это она же, повёрнутая на 45° (`_turn45`), остальное поворотами на 90°; индекс по часовой на
экране: 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE. Герой на двухколёсной повозке-рикше,
соперник на крытой лакированной повозке чужого клана. Парусов и мачт нет: силуэт колёсный.

    python3 tools/ninja8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Рикша героя: кузов из светлого дерева на одной оси, два больших колеса по бортам (белые точки
# это спицы), на корме сложенный белый бумажный верх, на светлом сиденье ниндзя в синем
# капюшоне (белое лицо в прорези смотрит вперёд, красный шарф за затылком), вперёд уходят две
# оглобли с перекладиной, между ними пусто: по этой скобе нос читается с любого угла. Строчная
# `w` это пыль из-под колёс, становится белым.
RICKSHAW_E = [
        "................",
        "................",
        "....KKKKKK......",
        "....KWKKWK......",
        "..KKKKKKKKKKKKK.",
        ".KWWWKYYYYYYYYYK",
    ".KWWWKYYYYYKKKYK",
    "wKWWWKYRBBWK..YK",
    "wKWWWKYRBBWK..YK",
    ".KWWWKYYYYYKKKYK",
        ".KWWWKYYYYYYYYYK",
        "..KKKKKKKKKKKKK.",
        "....KWKKWK......",
        "....KKKKKK......",
        "................",
        "................",
]

# Повозка чужого клана: длинный красный лакированный короб на четырёх малых колёсах (белые
# ступицы), над кузовом крыша с чёрными гвоздями по краям, на козлах возница в чёрном капюшоне
# с белой прорезью глаз, нос скошен клином, на нём золотой фонарь. Диагональ тем же поворотом.
WAGON_E = [
        "................",
        "................",
        "................",
        "..KWK....KWK....",
        ".KKKKKKKKKKKKK..",
        ".KRRRRRRRRKRRKK.",
    "wKRKRKRKRRKKKRKK",
    "wKRRRRRRRRKKWRYK",
    "wKRRRRRRRRKKWRYK",
    "wKRKRKRKRRKKKRKK",
        ".KRRRRRRRRKRRKK.",
        ".KKKKKKKKKKKKK..",
        "..KWK....KWK....",
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
    """8 направлений: `<prefix>_0..7`; строчная `w` следа становится белым."""
    out = {}
    e, ne = east, north_east
    for k in range(4):
        out[2 * k] = e
        out[(2 * k + 7) % 8] = ne
        e, ne = _cw(e), _cw(ne)
    return {"%s_%d" % (prefix, i): [r.replace("w", "W") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", RICKSHAW_E, _turn45(RICKSHAW_E)))
SPRITES.update(frames("rival", WAGON_E, _turn45(WAGON_E)))
SPRITES.update({
    # Трасса: синеватый камень дорожки, короткие швы плит стоят зеркально (при отражении тайла
    # рисунок тот же), светлый скол посередине.
    "race_water": [
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBKKBBBBKKBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBWWBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBKKBBBBKKBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Второй вариант: на плите лежит красный лист клёна с золотым черешком.
    "race_water_1": [
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBKKBBBBKKBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBRBRBBBBBB",
        "BBBBBBBRRRBBBBBB",
        "BBBBBBRRRRRBBBBB",
        "BBBBBBBBYBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBKKBBBBKKBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBKB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Обочина: камень под мхом и соломой, поверх палые листья клёна; замедляет.
    "race_shallow": [
        "BBBBBBBBBBBBBBBB",
        "BBYYBBBBBBBRBBBB",
        "BBYKBBBBBBRRRBBB",
        "BBBBBBBYBBBYBBBB",
        "BBBBBBYYKBBBBBBB",
        "BRBBBBYKBBBBBBBB",
        "RRRBBBBBBBBBBYYB",
        "BYBBRBBBBBBBBYKB",
        "BBBRRRBBBBYBBBBB",
        "BBBBYBBBBYYKBBBB",
        "BBBBBBBBBYKBBBBB",
        "BYYBBBBBBBBBBBRB",
        "BYKBBBBRBBBBBRRR",
        "BBBBBBRRRBBBBBYB",
        "BBBBBBBYBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Стена: белёная стена усадьбы под тёмной балкой, на штукатурке золотистые щербины; повозка
    # сюда не заезжает. Во втором варианте герб клана: красное солнце в чёрном кольце.
    "race_sand": [
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWYWWWW",
        "WWWYWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWYYWWWWWWW",
        "WWWWWWWWYWWWWWWW",
        "WWWWWWWWWWWWWYWW",
        "KKKKKKKKKKKKKKKK",
        "WYWWWWWWWWWWWWWW",
        "WWWWWWWWWWYWWWWW",
        "WWWWYWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWYW",
        "WWWWWWWYWWWWWWWW",
        "WWYWWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
    ],
    "race_sand_1": [
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWWYWWW",
        "WWWWWWWWWWWWWWWW",
        "WWYWWWKKKKWWWWWW",
        "WWWWKKRRRRKKWWWW",
        "WWWKRRRRRRRRKWWW",
        "WWWKRRRRRRRRKWWW",
        "KKKKRRRRRRRRKKKK",
        "WWWKRRRRRRRRKWWW",
        "WWWKRRRRRRRRKWWW",
        "WWWWKKRRRRKKWWWW",
        "WWWWWWKKKKWWWYWW",
        "WYWWWWWWWWWWWWWW",
        "WWWWWWWWWYWWWWWW",
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
    ],
    # Препятствия: каменный фонарь (сверху видна крыша с загнутыми углами, в середине огонь) и
    # бочка сакэ в соломенной оплётке с красным знаком на крышке.
    "race_rock": [
        "................",
        "................",
        "..KK........KK..",
        "..KWK......KWK..",
        "...KWKKKKKKWK...",
        "....KWWWWWWK....",
        "....KWBBBBWK....",
        "....KWBYYBWK....",
        "....KWBYYBWK....",
        "....KWBBBBWK....",
        "....KWWWWWWK....",
        "...KWKKKKKKWK...",
        "..KWK......KWK..",
        "..KK........KK..",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        ".....KKKKKK.....",
        "...KKYYYYYYKK...",
        "..KYYKKKKKKYYK..",
        "..KYKWWWWWWKYK..",
        ".KYKWWWRRWWWKYK.",
        ".KYKWWRRRRWWKYK.",
        ".KYKWWRRRRWWKYK.",
        ".KYKWWWRRWWWKYK.",
        "..KYKWWWWWWKYK..",
        "..KYYKKKKKKYYK..",
        "...KKYYYYYYKK...",
        ".....KKKKKK.....",
        "................",
        "................",
    ],
    # Бумажный фонарик на кромке трассы, украшение без столкновений.
    "race_buoy": [
        "................",
        "................",
        "................",
        "................",
        ".......YY.......",
        "......KKKK......",
        ".....KRRRRK.....",
        "....YKRYYRKY....",
        "....YKRYYRKY....",
        ".....KRRRRK.....",
        "......KKKK......",
        ".......YY.......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: красно-белая шашечка знамени поперёк трассы, тайл кладётся вертикальной полосой.
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
    assert set("".join(_rows)) <= set("KBRWY."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import ninja8
        ninja8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
