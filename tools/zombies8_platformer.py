#!/usr/bin/env python3
"""Платформер 8-bit, набор «Зомби» (#137): те же слоты и размеры карт, что у космоса
(`pixel_sets_extra.SPACE`). Выживший в красной куртке и синей бейсболке с рюкзаком, зомби-ходок
в лохмотьях, ворон, банка консервов, фонарь на столбе, флаг убежища, плиты кладбища под мхом,
ночные облака. Палитра `zombies8.PALETTE`: K чёрный, R красный, G мёртвая зелень, W кость,
B синий сланец.

    python3 tools/zombies8_platformer.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sets_extra import DOTS, _hero, _pad  # noqa: E402

# Торс выжившего, 13 строк: бейсболка с козырьком вправо, лицо, куртка, зелёный рюкзак за
# спиной, рука с кистью. Ноги (джинсы) дорисовывает `_hero`.
_SURVIVOR = [
    DOTS,
    ".....KKKKKK.....",
    "....KBBBBBBK....",
    "...KBBBBBBBBK...",
    "...KBBBBBBBBBBK.",
    "...KKWWKWWKWKK..",
    "...KWWWKWWKWK...",
    "....KWWWWWWK....",
    "....KRRRRRRK....",
    "...KGKRRRWKRK...",
    "...KGKRRRWKRK...",
    "...KGKRRRRKWK...",
    "....KBBBBBBK....",
]

SPRITES = _hero(_SURVIVOR, "B")
SPRITES.update({
    # Зомби-ходок: идёт влево, руки вытянуты вперёд, красные глаза, оскал, рваная рубаха.
    "enemy_0": _pad([
        DOTS,
        "......KKKKKK....",
        ".....KGGGGGGK...",
        "....KGGGGGGGGK..",
        "....KKKGGKKGGK..",
        "....KRKGGRKGGK..",
        "....KGGGGGGGGK..",
        ".....KWKWKGGK...",
        "..KKKKKKWWWWK...",
        ".KGGGGGGWWBWK...",
        "..KKKKKKWBWWK...",
        "......KWWWWWK...",
        "......KBBBBBK...",
        ".....KBBKKBBK...",
        "....KGGK..KGGK..",
        "....KKKK..KKKK..",
    ]),
    "enemy_1": _pad([
        DOTS,
        "......KKKKKK....",
        ".....KGGGGGGK...",
        "....KGGGGGGGGK..",
        "....KKKGGKKGGK..",
        "....KRKGGRKGGK..",
        "....KGGGGGGGGK..",
        ".....KWKWKGGK...",
        "......KKWWWWK...",
        "..KKKKKKWWBWK...",
        ".KGGGGGGWBWWK...",
        "..KKKKKKWWWWK...",
        "......KBBBBBK...",
        "......KBBKBBK...",
        ".....KGGKGGK....",
        ".....KKKKKKK....",
    ]),
    # Ворон: летит вправо, красный глаз, светлый клюв; кадры это взмах вверх и вниз.
    "parrot_0": _pad([
        DOTS, DOTS,
        "......KK........",
        ".....KBBK.......",
        ".....KBBBK......",
        "......KBBK.KKK..",
        ".KKK..KBBKKBBBK.",
        "KBBBKKBBBBBBRBWK",
        ".KKBBBBBBBBBBKK.",
        "...KKBBBBBBKK...",
        ".....KKKKKK.....",
        "......K.K.......",
    ]),
    "parrot_1": _pad([
        DOTS, DOTS, DOTS, DOTS, DOTS,
        "...........KKK..",
        ".KKK..KKKKKBBBK.",
        "KBBBKKBBBBBBRBWK",
        ".KKBBBBBBBBBBKK.",
        "...KKBBBBBKK....",
        ".....KBBBK......",
        ".....KBBK.......",
        "......KK........",
    ]),
    # Банка консервов: жестяная, с красной этикеткой.
    "coin": _pad([
        DOTS, DOTS,
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "....KKKKKKKK....",
        "....KWWWWWBK....",
        "....KRRRRRRK....",
        "....KRWWWRRK....",
        "....KRRRRRRK....",
        "....KWWWWWBK....",
        "....KKKKKKKK....",
        ".....KKKKKK.....",
    ]),
    # Контрольная точка: керосиновый фонарь на столбе.
    "checkpoint": _pad([
        ".......KK.......",
        "......KBBK......",
        ".....KKKKKK.....",
        ".....KWRRWK.....",
        ".....KWRRWK.....",
        ".....KWWWWK.....",
        ".....KKKKKK.....",
        ".......KK.......",
        "......KBBK......",
        "......KBBK......",
        "......KBBK......",
        "......KBBK......",
        "......KBBK......",
        ".....KBBBBK.....",
        "....KBBBBBBK....",
        "....KKKKKKKK....",
    ]),
    # Финиш: флаг убежища, зелёное полотнище с белым крестом, рваный край.
    "flag": _pad([
        "...KK...........",
        "..KWWK..........",
        "...KKKKKKKKKK...",
        "...KBKGGGGGGGK..",
        "...KBKGGWWGGGGK.",
        "...KBKGWWWWGGK..",
        "...KBKGGWWGGGGK.",
        "...KBKGGGGGGGK..",
        "...KBKKKKKKKK...",
        "...KBK..........",
        "...KBK..........",
        "...KBK..........",
        "...KBK..........",
        "...KBK..........",
        "..KBBBK.........",
        "..KKKKK.........",
    ]),
    # Земля: плиты кладбища, сверху мох и жухлая трава, в камне трещины и обломки костей.
    "ground": _pad([
        "GGGGGGGGGGGGGGGG",
        "GBGGGBGGGGBGGGBG",
        "BBBBBBBBBBBBBBBB",
        "BWBBBBBBBBKBBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBKBBBBBBBBBB",
        "BBBBBKBBBWWBBBBB",
        "BBGBBKBBBBBBBBKB",
        "BBBBBKBBBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBBBBBKBBBB",
        "BBBKBBBBBBBKBBGB",
        "BWBBKBBBBBBKBBBB",
        "BBBBBBBBBBBKBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBKBBBBBBBB",
    ]),
    "ground_inner": _pad([
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBGBBB",
        "BWBBBBBKBBBBBBBB",
        "BBBBBBBKBBKBBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBKBBBBBBBBBB",
        "BBBBBKBBBWWBBBBB",
        "BBGBBKBBBBBBBBKB",
        "BBBBBKBBBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBBBBBKBBBB",
        "BBBKBBBBBBBKBBGB",
        "BWBBKBBBBBBKBBBB",
        "BBBBBBBBBBBKBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBKBBBBBBBB",
    ]),
    # Платформа: надгробная плита плашмя, верх высветлен луной.
    "platform": _pad([
        "WWWWWWWWWWWWWWWW",
        "BBBBBBBBBBBBBBBB",
        "BBKBBBBBGBBBBKBB",
        "BBBBBBBBBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
    ]),
    # Ночные облака с лунной кромкой.
    "cloud_small": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "......KKK.......",
        "....KKWWBKKK....",
        "...KWWBBBBBBK...",
        "..KWBBBBBBBBBK..",
        "..KBBBBBBBBBBK..",
        "...KBBKKBBBKK...",
        "....KK..KKK.....",
    ]),
    "cloud_big": _pad([
        "." * 32, "." * 32,
        "...............KKKK.............",
        ".........KKK.KKWWWBKK...........",
        "........KWWBKWWBBBBBBK.KKK......",
        "......KKWBBBBBBBBBBBBBKWBBK.....",
        ".....KWWBBBBBBBBBBBBBBBBBBBK....",
        "....KWBBBBBBBBBBBBBBBBBBBBBBK...",
        "....KBBBBBBBBBBBBBBBBBBBBBBBK...",
        ".....KBBBKKBBBBBBBKKBBBBBBKK....",
        "......KKK..KKBBBKK..KKKKKK......",
        ".............KKK................",
    ], w=32),
})


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import zombies8
        zombies8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
