#!/usr/bin/env python3
"""8-bit «Сладости», гонки (вид сверху, #137): зеркало модуля космоса `space8_racing.py` и раздела
«Гонки × 8-bit» в `pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*` это
трасса (бисквитный корж, демка мешает два варианта и отражает их, поэтому рисунок спокойный и
крошки стоят по углам), `race_shallow` обочина, которая тормозит (лужицы липкого розового сиропа
на корже), `race_sand*` стена (взбитые сливки с посыпкой, туда не заехать; во втором варианте в
сливках мятный леденец-спираль), `race_rock` и `race_barrel` препятствия (кусок сахара и кубик
желе на блюдце), `race_buoy` леденец на палочке на кромке, `race_finish` финишная полоса с
прозрачными краями (шашечка из горького и белого шоколада). Транспорт в 8 направлениях из одной
карты на восток: диагональ это она же, повёрнутая на 45° (`_turn45`), остальное поворотами на
90°; индекс по часовой на экране: 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE. Герой на эклере
с колёсами из печенья, соперник на кексе на колёсах. Парусов, мачт и корабельных силуэтов нет:
это машинки, вид сверху читается по четырём колёсам по бортам.

Палитра `sweets8.PALETTE`: K горький шоколад, W сливки и сахар, G бисквит и пряник, R мармелад,
P розовая глазурь.

    python3 tools/sweets8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Эклер на колёсах: вытянутая заварная булка (края теста видны по кругу), сверху розовая глазурь
# с белой посыпкой, по бортам четыре колеса из печенья-сэндвича ребром (между шоколадных половинок
# полоска крема). Ближе к скруглённому носу голова пряничного человечка с завитком глазури, за
# ней красный бант. Сзади крошки (строчная `w` становится белым, как пена у шлюпки).
ECLAIR_E = [
    "................",
    "................",
    "...KKKK..KKKK...",
    "...KWWK..KWWK...",
    "..KKKKKKKKKKKK..",
    ".KGPPPPPPPWPPGK.",
    ".KGPWPPPKKKKPGK.",
    "wKGPPRRKGWWGKGGK",
    "wKGPWRRKGGGGKGGK",
    ".KGPPPPPKKKKPGK.",
    ".KGPPWPPPPPPPGK.",
    "..KKKKKKKKKKKK..",
    "...KWWK..KWWK...",
    "...KKKK..KKKK...",
    "................",
    "................",
]

# Кекс на колёсах: круглая красная формочка с шапкой белого крема на вафельной тележке (края
# тележки с бампером видны спереди и сзади), четыре колеса из печенья по углам. В креме сидит
# мармеладный мишка с бликом, мордой к носу; спереди две сахарные фары, сзади розовая крошка
# (строчная `p` становится розовым). Диагональ тем же поворотом на 45°.
CUPCAKE_E = [
    "................",
    "................",
    "................",
    ".KKK..KKKK..KKK.",
    ".KWKKKRRRRKKKWK.",
    ".KKKRRWWWWRRKKK.",
    ".KGKRWWRRRWRKGKW",
    "pKGKRWRRWRRRKGK.",
    "pKGKRWRRRRRRKGK.",
    ".KGKRWWRRRWRKGKW",
    ".KKKRRWWWWRRKKK.",
    ".KWKKKRRRRKKKWK.",
    ".KKK..KKKK..KKK.",
    "................",
    "................",
    "................",
]


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def _turn45(rows):
    """Карта, повёрнутая на 45° против часовой (нос с востока на северо-восток): диагональ это
    тот же спрайт, повёрнутый, а не отдельный рисунок. Каждый пиксель берёт цвет большинства из
    девяти проб, так края выходят без дыр."""
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
    return {"%s_%d" % (prefix, i): [r.replace("w", "W").replace("p", "P") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", ECLAIR_E, _turn45(ECLAIR_E)))
SPRITES.update(frames("rival", CUPCAKE_E, _turn45(CUPCAKE_E)))
SPRITES.update({
    # Трасса: бисквитный корж, шоколадные крошки по углам (при отражении тайла рисунок тот же)
    # и пара крупинок сахара.
    "race_water": [
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGWGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGWGGGGG",
        "GGGGGGGGGGGWGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Второй вариант: штрих разметки белой глазурью посередине вместо крупинок.
    "race_water_1": [
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGWWGGGGGGG",
        "GGGGGGWWWWGGGGGG",
        "GGGGGGWWWWGGGGGG",
        "GGGGGGGWWGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Обочина: лужицы липкого розового сиропа с бликом на корже, замедляет.
    "race_shallow": [
        "GGGGGGGGGGGGGGGG",
        "GGPPPGGGGGGGGGGG",
        "GPPWPPGGGGPPGGGG",
        "GPPPPPGGGPPPPGGG",
        "GGPPPGGGGPWPPPGG",
        "GGGGGGGGGGPPPPGG",
        "GGGGGGPPGGGPPGGG",
        "GGGGGPPPPGGGGGGG",
        "GPPGGPWPPPGGGGGG",
        "GPPGGGPPPPGGGPPG",
        "GGGGGGGPPGGGPPPP",
        "GGGPPGGGGGGGPWPP",
        "GGPPPPGGGGGGGPPG",
        "GGPWPPPGGGPGGGGG",
        "GGGPPPGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Стена: взбитые сливки, розовые завитки и красные точки посыпки; эклер сюда не заезжает.
    # Во втором варианте в сливки вдавлен мятный леденец-спираль.
    "race_sand": [
        "WWWWWWWWWWWWWWWW",
        "WWWWPPWWWWWWWRWW",
        "WWWPWWWWWWWWWWWW",
        "WWWPWWWWWWPPPWWW",
        "WRWWWWWWWPWWWPWW",
        "WWWWWWWWWWWWWPWW",
        "WWWWWWRWWWWWPWWW",
        "WWWWWWWWWWWWWWWW",
        "WWPPPWWWWWWWWWWW",
        "WPWWWPWWWWWRWWWW",
        "WWWWWPWWWWWWWWWW",
        "WWWWPWWWWWWWWPPW",
        "WWWWWWWWWWWWPWWW",
        "WWWWWWWWRWWWPWWW",
        "WWRWWWWWWWWWWWWW",
        "WWWWWWWWWWWWWWWW",
    ],
    "race_sand_1": [
        "WWWWWWWWWWWWWWWW",
        "WWWWWWWWWWWWRWWW",
        "WWPWWWWWWWWWWWWW",
        "WWWWWKKKKKKWWWWW",
        "WWWWKRRWWWRKWWWW",
        "WWWKWRRRWWRRKWWW",
        "WWWKWWRRWRRRKWWW",
        "WWWKWWWKKRRWKWWW",
        "WWWKWRRKKWWWKWWW",
        "WWWKRRRWRRWWKWWW",
        "WWWKRRWWRRRWKWWW",
        "WWWWKRWWWRRKWWWW",
        "WWWWWKKKKKKWWPWW",
        "WRWWWWWWWWWWWWWW",
        "WWWWWWWWWPWWWWWW",
        "WWWWWWWWWWWWWWWW",
    ],
    # Препятствия: кусок сахара (белый куб, розовая тень на боковой грани, крупинки) и кубик
    # красного желе с бликом на белом блюдце.
    "race_rock": [
        "................",
        "................",
        "...KKKKKKKKK....",
        "..KWWWWWWWWWK...",
        "..KWWKWWWWWWKK..",
        "..KWWWWWWKWWKPK.",
        "..KWWWWWWWWWKPK.",
        "..KWKWWWWWWWKPK.",
        "..KWWWWWKWWWKPK.",
        "..KWWWWWWWWWKPK.",
        "..KWWWWWWWWWKPK.",
        "..KKKKKKKKKKKPK.",
        "...KPPPPPPPPPPK.",
        "....KKKKKKKKKK..",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "...KKWWWWWWKK...",
        "..KWWKKKKKKWWK..",
        "..KWKRRRRRRKWK..",
        "..KWKRWWRRRKWK..",
        "..KWKRWRRRRKWK..",
        "..KWKRRRRRPKWK..",
        "..KWKRRRRPPKWK..",
        "..KWWKKKKKKWWK..",
        "...KKWWWWWWKK...",
        ".....KKKKKK.....",
        "................",
        "................",
    ],
    # Леденец на палочке на кромке трассы, украшение без столкновений: красно-белая спираль
    # и пряничная палочка.
    "race_buoy": [
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KRRWWK.....",
        "....KRWWRRWK....",
        "....KRWRKWRK....",
        "....KWRKRWRK....",
        "....KWRRWWRK....",
        ".....KWWRRK.....",
        "......KKKK......",
        ".......KGK......",
        ".......KGK......",
        "........K.......",
        "................",
        "................",
    ],
    # Финиш: шашечка из плиток горького и белого шоколада поперёк трассы, тайл кладётся
    # вертикальной полосой.
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
    assert set("".join(_rows)) <= set("KWGRP."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import sweets8
        sweets8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
