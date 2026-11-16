#!/usr/bin/env python3
"""8-bit «Офис», гонки (вид сверху, #137): зеркало `space8_racing.py` и раздела «Гонки × 8-bit» в
`pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*` это трасса (гладкий линолеум
коридора, демка мешает два варианта и отражает их, поэтому рисунок симметричен), `race_shallow`
обочина, которая тормозит (рассыпанные листы и стикеры), `race_sand*` стена (синяя ткань
перегородок, туда не заехать; во втором варианте рабочее место с монитором), `race_rock` и
`race_barrel` препятствия (коробка бумаги и кулер), `race_buoy` табличка «мокрый пол» на кромке,
`race_finish` финишная полоса с прозрачными краями. Транспорт в 8 направлениях из одной карты
на восток: диагональ это она же, повёрнутая на 45° (`_turn45`), остальное поворотами на 90°;
индекс по часовой на экране: 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE. Герой катит почтовую
тележку на колёсиках, соперник едет на офисном кресле. Парусов, мачт и корабельных силуэтов нет:
оба транспорта это низкие колёсные тележки. Палитра `office8.PALETTE`: K чёрный, W белый,
B синий, R красный, Y тёплый жёлтый.

    python3 tools/office8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Почтовая тележка: прямоугольный синий короб на четырёх колёсиках по углам, внутри конверты
# и письмо с красной маркой; на корме поручень, за ним клерк (белая рубашка, тёмная макушка,
# красный галстук к носу), спереди красная бирка отдела. Жёлтого в транспорте нет: на жёлтом
# линолеуме он читается дырой.
CART_E = [
    "................",
    "................",
    "................",
    ".......KK...KK..",
    ".KKKKKKKKKKKKKK.",
    "KWWWWKKBBBBBBBK.",
    "KWWWWKKBWWWKWBK.",
    "KWKKRKKBWKWKRBKR",
    "KWKKRKKBWWWKWBKR",
    "KWWWWKKBKWWWWBK.",
    "KWWWWKKBBBBBBBK.",
    ".KKKKKKKKKKKKKK.",
    ".......KK...KK..",
    "................",
    "................",
    "................",
]

# Офисное кресло соперника: круглое красное сиденье с валиком спинки, под ним колёсики
# крестовины (два сверху, два снизу, одно спереди), в кресле сотрудник в чёрном костюме: плечи,
# макушка с синим отливом, на коленях бумаги. Сзади толстая чёрная спинка. Круглый
# силуэт против прямоугольной тележки героя.
CHAIR_E = [
    "................",
    "................",
    "....KK....KK....",
    "...KKKKKKKKK....",
    "..KRRRRRRRRRK...",
    ".KKRKKKKRRRRRK..",
    ".KKRKKKKKKKRRK..",
    ".KKRKBBKKWWRRKKK",
    ".KKRKBBKKWWRRKKK",
    ".KKRKKKKKKKRRK..",
    ".KKRKKKKRRRRRK..",
    "..KRRRRRRRRRK...",
    "...KKKKKKKKK....",
    "....KK....KK....",
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
    """8 направлений: `<prefix>_0..7`; строчные буквы следа (если есть) становятся цветом."""
    out = {}
    e, ne = east, north_east
    for k in range(4):
        out[2 * k] = e
        out[(2 * k + 7) % 8] = ne
        e, ne = _cw(e), _cw(ne)
    return {"%s_%d" % (prefix, i): [r.replace("w", "W").replace("y", "Y") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", CART_E, _turn45(CART_E)))
SPRITES.update(frames("rival", CHAIR_E, _turn45(CHAIR_E)))
SPRITES.update({
    # Трасса: плитка линолеума с точками по углам (при отражении тайла рисунок тот же) и блик.
    "race_water": [
        "YYYYYYYYYYYYYYYY",
        "YKYYYYYYYYYYYYKY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYWWYYYY",
        "YYYYYYYYYYYYWYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YKYYYYYYYYYYYYKY",
        "YYYYYYYYYYYYYYYY",
    ],
    # Второй вариант: синяя метка разметки коридора вместо блика.
    "race_water_1": [
        "YYYYYYYYYYYYYYYY",
        "YKYYYYYYYYYYYYKY",
        "YYYYYYYYYYYYYYYY",
        "YYYWWYYYYYYYYYYY",
        "YYYYYWYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYBBYYYYYYY",
        "YYYYYYYBBYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "YKYYYYYYYYYYYYKY",
        "YYYYYYYYYYYYYYYY",
    ],
    # Обочина: рассыпанные листы со строчками и стикеры на линолеуме, замедляет.
    "race_shallow": [
        "YYYYYYYYYYYYYYYY",
        "YWWWYYYYYYYYRRYY",
        "YWKWKYYYYYYYRRKY",
        "YWWWKYYYWWWYYKKY",
        "YYKKKYYYWKWKYYYY",
        "YYYYYYYYWWWKYYYY",
        "YYYYYBBYYKKKYYYY",
        "YYYYYBBKYYYYYWWW",
        "YWWWYYKKYYYYYWKW",
        "YWKWKYYYYYYYYWWW",
        "YWKWKYYYYWWWYYKK",
        "YWWWKYYYYWKWKYYY",
        "YYKKKYRRYWWWKYYY",
        "YYYYYYRRKYKKKYYY",
        "YYYYYYYKKYYYYYYY",
        "YYYYYYYYYYYYYYYY",
    ],
    # Стена: синяя ткань перегородок в мелкую точку; тележка сюда не заезжает. Во втором
    # варианте рабочее место: столешница, монитор и лист.
    "race_sand": [
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBKBBBB",
        "BBBKBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBKKBBBBBBB",
        "BBBBBBBBKBBBBBBB",
        "BBBBBBBBBBBBBKBB",
        "BBBBBBBBBBBBBBBB",
        "BKBBBBBBBBBBBBBB",
        "BBBBBBBBBBKBBBBB",
        "BBBBKBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBKB",
        "BBBBBBBKBBBBBBBB",
        "BBKBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    "race_sand_1": [
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBKBBB",
        "BBBBBBBBBBBBBBBB",
        "BBKKKKKKKKKKBBBB",
        "BBKYYYYYYYYKBBBB",
        "BBKYKKKKKYYKBBBB",
        "BBKYKWWWKYYKBBBB",
        "BBKYKWWWKYYKBBBB",
        "BBKYKKKKKYWKBBBB",
        "BBKYYYKYYWWKBBBB",
        "BBKYYKKKYYYKBBKB",
        "BBKKKKKKKKKKBBBB",
        "BKBBBBBBBBBBBBBB",
        "BBBBBBBBBKBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Препятствия: коробка бумаги (квадратная белая пачка с синими полосами, красный скотч и ярлык) и
    # кулер сверху (белый корпус, круглая синяя бутыль с бликом).
    "race_rock": [
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        "..KWWWWRRWWWWK..",
        "..KBBBBRRBBBBK..",
        "..KWWWWRRWWWWK..",
        "..KWKKWRRWWWWK..",
        "..KKKKKRRKKKKK..",
        "..KWWWWRRWWWWK..",
        "..KWWWWRRWKKWK..",
        "..KBBBBRRBBBBK..",
        "..KWWWWRRWKKWK..",
        "..KWWWWRRWWWWK..",
        "..KKKKKKKKKKKK..",
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
        "...KWKBWWBKWK...",
        "...KWKBWBBKWK...",
        "...KWKBBBBKWK...",
        "...KWKBBBBKWK...",
        "...KWKKKKKKWK...",
        "....KWWRRWWK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    # Табличка «мокрый пол» на кромке трассы: жёлтый домик с красным восклицательным знаком,
    # украшение без столкновений.
    "race_buoy": [
        "................",
        "................",
        "................",
        "................",
        ".......KK.......",
        "......KYYK......",
        "......KRRK......",
        ".....KYRRYK.....",
        ".....KYRRYK.....",
        "....KYYYYYYK....",
        "....KYYRRYYK....",
        "....KKKKKKKK....",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: шахматная полоса поперёк коридора, тайл кладётся вертикальной полосой.
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
    assert set("".join(_rows)) <= set("KWBRY."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import office8
        office8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
