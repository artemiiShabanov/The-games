#!/usr/bin/env python3
"""Платформер 8-bit, набор «Ниндзя» (#137): те же слоты и размеры карт, что у космоса
(`pixel_sets_extra.SPACE`). Ниндзя в синем с красным шарфом и мечом за плечом, боец чужого
клана в красном с серпом, ворон-тэнгу, монета с квадратным отверстием, бумажный фонарь на
столбе, знамя нобори, черепичная крыша с золотым коньком, лаковая балка, закатные облака.
Палитра `ninja8.PALETTE`: K чёрный, B синий, R красный, W белый, Y золото.

    python3 tools/ninja8_platformer.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sets_extra import DOTS, _hero, _pad  # noqa: E402

# Торс ниндзя, 13 строк: капюшон с прорезью глаз (смотрит вправо), рукоять меча над левым
# плечом, шарф на шее с двумя концами за спиной, красный пояс, светлые кисти. Ноги в белых
# обмотках дорисовывает `_hero`. Концы шарфа стоят выше рядов 8-9: их переписывает прыжок.
_NINJA = [
    ".YY.............",
    "..YY.KKKKKK.....",
    "...YKBBBBBBK....",
    "...KBBBBBBBBK...",
    "...KBBWKWWKWK...",
    "RR.KBBBBBBBBK...",
    ".RR.KBBBBBBK....",
    "RRRRRRRRRRRK....",
    "....KBBBBBBK....",
    "...KBKBBBBKBK...",
    "...KBKBBBBKBK...",
    "...KWKRRRRKWK...",
    "....KBBBBBBK....",
]

# Черепица «рыбья чешуя»: дуги шириной 8, ряды через 4 со сдвигом на полшага, период 8 рядов.
_TILES = [
    "BBBBBBBBBBBBBBBB",
    "KBWBBBBKKBBBBBBK",
    "BKBBBBKBBKBBBBKB",
    "BBKKKKBBBBKKKKBB",
    "BBBBBBBBBBBBBBBB",
    "BBBKKBBBBBWKKBBB",
    "BBKBBKBBBBKBBKBB",
    "KKBBBBKKKKBBBBKK",
]

SPRITES = _hero(_NINJA, "W")
SPRITES.update({
    # Боец чужого клана: идёт влево, серп занесён перед собой, чёрный пояс с золотым узлом.
    "enemy_0": _pad([
        ".WWW............",
        "WW.Y..KKKKKK....",
        "W..Y.KRRRRRRK...",
        "...YKRRRRRRRRK..",
        "...YKWKWKWRRRK..",
        "...YKRRRRRRRRK..",
        "...Y.KRRRRRRK...",
        "..WWRRRRRRRRK...",
        "...YKKKKRRRRK...",
        ".....KRRRRKRK...",
        ".....KKKYKKWK...",
        ".....KRRRRRRK...",
        ".....KRRKKRRK...",
        "....KRRK..KRRK..",
        "....KBBK..KBBK..",
        "....KKKK..KKKK..",
    ]),
    "enemy_1": _pad([
        DOTS,
        ".WWW............",
        "WW.Y..KKKKKK....",
        "W..Y.KRRRRRRK...",
        "...YKRRRRRRRRK..",
        "...YKWKWKWRRRK..",
        "...YKRRRRRRRRK..",
        "...Y.KRRRRRRK...",
        "..WWRRRRRRRRK...",
        "...YKKKKRRKRK...",
        ".....KKKYKKWK...",
        ".....KRRRRRRK...",
        ".....KRRRRRRK...",
        "......KRRRRK....",
        "......KBBBBK....",
        "......KKKKKK....",
    ]),
    # Ворон-тэнгу: летит влево, красная маска с длинным носом, синее тело, золотые лапы.
    "parrot_0": _pad([
        DOTS,
        ".........KKK....",
        "........KBBBK...",
        "........KBBBBK..",
        "..KKKK..KBBBBK..",
        ".KBBBBK.KBBBK...",
        ".KRWKRBKBBBBKKK.",
        "KRRRRRBBBBBBBBBK",
        ".KKRRRBBBBBBBKK.",
        "...KKKBBBBBBK...",
        "......KYKKYK....",
        "......KK..KK....",
    ]),
    "parrot_1": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "..KKKK..........",
        ".KBBBBK.KKKK....",
        ".KRWKRBKBBBBKKK.",
        "KRRRRRBBBBBBBBBK",
        ".KKRRRBBBBBBBKK.",
        "...KKKKBBBBK....",
        "......KBBBBK....",
        ".......KBBBK....",
        "........KBBK....",
        ".........KK.....",
    ]),
    # Монета с квадратным отверстием: отверстие прозрачное.
    "coin": _pad([
        DOTS, DOTS,
        ".....KKKKKK.....",
        "....KYYYYYYK....",
        "...KYWWYYYYYK...",
        "...KYWKKKKYYK...",
        "...KYYK..KYYK...",
        "...KYYK..KYYK...",
        "...KYYKKKKYYK...",
        "...KYYYYYYYYK...",
        "....KYYYYYYK....",
        ".....KKKKKK.....",
    ]),
    # Чекпоинт: бумажный фонарь на бамбуковом столбе, каменное основание.
    "checkpoint": _pad([
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRYYRRRK...",
        "...KRRYWWYRRK...",
        "...KRRYWWYRRK...",
        "...KRRRYYRRRK...",
        "....KRRRRRRK....",
        ".....KKKKKK.....",
        "......KYYK......",
        "......KYYK......",
        "......KKKK......",
        "......KYYK......",
        "......KYYK......",
        ".....KBBBBK.....",
        "....KBBWBBBK....",
        "....KKKKKKKK....",
    ]),
    # Финиш: знамя нобори на шесте с перекладиной, красное солнце и две полосы.
    "flag": _pad([
        "...KKKKKKKKKKK..",
        "...KYKWWWWWWWK..",
        "...KYKWWWWWWWK..",
        "...KYKWWRRRWWK..",
        "...KYKWRRRRRWK..",
        "...KYKWRRRRRWK..",
        "...KYKWWRRRWWK..",
        "...KYKWWWWWWWK..",
        "...KYKRRRRRRRK..",
        "...KYKWWWWWWWK..",
        "...KYKRRRRRRRK..",
        "...KYKKKKKKKKK..",
        "...KYK..........",
        "...KYK..........",
        "..KBBBK.........",
        "..KKKKK.........",
    ]),
    # Земля: черепичная крыша, сверху золотой конёк со светлой кромкой.
    "ground": _pad([
        "WWWWWWWWWWWWWWWW",
        "YYYYYYYYYYYYYYYY",
        "KKKKKKKKKKKKKKKK",
    ] + [_TILES[y % 8] for y in range(3, 16)]),
    "ground_inner": _pad([_TILES[y % 8] for y in range(16)]),
    # Платформа: балка под красным лаком, торцы досок.
    "platform": _pad([
        "RRRRRRRRRRRRRRRR",
        "YYYYYYYYYYYYYYYY",
        "YYYKYYYYYYYKYYYY",
        "YYYYYYYYYYYYYYYY",
        "KKKKKKKKKKKKKKKK",
    ]),
    # Облака с плоским низом, как на гравюрах: снизу их золотит закат.
    "cloud_small": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "......KKKK......",
        "....KKWWWWKK....",
        "...KWWWWWWWWKK..",
        "..KWWWWWWWWWWWK.",
        ".KYYWWWWWWWYYYYK",
        "..KKKKKKKKKKKKK.",
    ]),
    "cloud_big": _pad([
        "." * 32, "." * 32, "." * 32,
        "...........KKKKKK...............",
        ".........KKWWWWWWKK.............",
        "........KWWWWWWWWWWK...KKKK.....",
        "......KKWWWWWWWWWWWWKKKWWWWK....",
        ".....KWWWWWWWWWWWWWWWWWWWWWWKK..",
        "...KKWWWWWWWWWWWWWWWWWWWWWWWWWK.",
        "..KYYYYWWWWWWWWYYYYYYWWWWWWYYYK.",
        "...KKKKKKKKKKYYYYYYYYYYKKKKKKK..",
        ".............KKKKKKKKKK.........",
    ], w=32),
})


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import ninja8
        ninja8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
