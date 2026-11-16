#!/usr/bin/env python3
"""Платформер 8-bit, набор «Сладости» (#137): те же слоты и размеры карт, что у космоса
(`pixel_sets_extra.SPACE`). Пряничный человечек с белой глазурью и красным бантом, красный
мармеладный мишка, зефир с розовыми крылышками, конфета в фантике, кекс со свечой, флаг-леденец,
вафля под розовой глазурью, облака сахарной ваты. Палитра `sweets8.PALETTE`: K чёрный,
W глазурь, G пряник, R мармелад, P розовое.

    python3 tools/sweets8_platformer.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sets_extra import DOTS, _hero, _pad  # noqa: E402

# Торс пряничного человечка, 13 строк: круглая голова без шеи, глаза и белая улыбка глазурью,
# красный бант, руки с белой каймой на концах, две пуговицы, кайма глазури над ступнями.
# Ноги (пряник) дорисовывает `_hero`.
_GINGER = [
    DOTS,
    ".....KKKKKK.....",
    "....KGGGGGGK....",
    "...KGGKGGKGGK...",
    "...KGWGGGGWGK...",
    "...KGGWWWWGGK...",
    "....KGGGGGGK....",
    "....KRRKKRRK....",
    "....KGGGGGGK....",
    "...KGKGGWGKGK...",
    "...KWKGGGGKWK...",
    "....KKGGWGKK....",
    "....KWWGGWWK....",
]

# Вафля: ямки 2×2 с шагом 4, плитка 16×16 стыкуется со всех сторон.
_WAFFLE = [
    "GGGGGGGGGGGGGGGG",
    "GKKGGKKGGKKGGKKG",
    "GKKGGKKGGKKGGKKG",
    "GGGGGGGGGGGGGGGG",
] * 2

SPRITES = _hero(_GINGER, "G")
SPRITES.update({
    # Мармеладный мишка: круглые уши, блик желе на лбу, розовая мордочка и пузо, лапы в стороны.
    "enemy_0": _pad([
        DOTS,
        "...KK......KK...",
        "..KRRK....KRRK..",
        "..KRRKKKKKKRRK..",
        "...KRRRRRRRRK...",
        "..KRWWRRRRRRRK..",
        "..KRRKRRRRKRRK..",
        "..KRRRRPPRRRRK..",
        "..KRRRPKKPRRRK..",
        "...KRRRRRRRRK...",
        "..KKRRRRRRRRKK..",
        ".KRRKRPPPPRKRRK.",
        ".KRKKRPPPPRKKRK.",
        "...KRRRRRRRRK...",
        "...KRRRKKRRRK...",
        "...KKKK..KKKK...",
    ]),
    "enemy_1": _pad([
        DOTS,
        "...KK......KK...",
        "..KRRK....KRRK..",
        "..KRRKKKKKKRRK..",
        "...KRRRRRRRRK...",
        "..KRWWRRRRRRRK..",
        "..KRRKRRRRKRRK..",
        "..KRRRRPPRRRRK..",
        "..KRRRPKKPRRRK..",
        ".KKKRRRRRRRRKKK.",
        ".KRRKRRRRRRKRRK.",
        "..KKKRPPPPRKKK..",
        "...KRRPPPPRRK...",
        "..KRRRRRRRRRRK..",
        "..KRRRK..KRRRK..",
        "..KKKK....KKKK..",
    ]),
    # Зефир с крыльями: белый бочонок с румянцем, розовые крылышки вверх и вниз.
    "parrot_0": _pad([
        DOTS, DOTS, DOTS,
        ".KK..........KK.",
        "KPPK..KKKK..KPPK",
        "KPPPKKWWWWKKPPPK",
        ".KPPKWWWWWWKPPK.",
        "..KKKWKWWKWKKK..",
        "....KWWWWWWK....",
        "....KPWKKWPK....",
        "....KWWWWWWK....",
        ".....KKKKKK.....",
    ]),
    "parrot_1": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "......KKKK......",
        "....KKWWWWKK....",
        "....KWWWWWWK....",
        ".KKKKWKWWKWKKKK.",
        "KPPPKWWWWWWKPPPK",
        "KPPKKPWKKWPKKPPK",
        ".KK.KWWWWWWK.KK.",
        ".....KKKKKK.....",
    ]),
    # Бонус: конфета в фантике, полосатая карамель и розовые хвостики.
    "coin": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "KK....KKKK....KK",
        "KPK..KRRWWK..KPK",
        "KPPKKRRWWRRKKPPK",
        "KPPPKRWWRRWKPPPK",
        "KPPPKWWRRWWKPPPK",
        "KPPKKWRRWWRKKPPK",
        "KPK..KRWWRK..KPK",
        "KK....KKKK....KK",
    ]),
    # Чекпоинт: кекс со свечой, розовый крем в гофрированной формочке.
    "checkpoint": _pad([
        ".......KK.......",
        "......KRRK......",
        "......KRWK......",
        ".......KK.......",
        "......KWWK......",
        "......KRRK......",
        "......KWWK......",
        "....KKKRRKKK....",
        "...KPPPPPPPPK...",
        "..KPPWWPPPPPPK..",
        "..KPPPPPPPPPPK..",
        "..KKKKKKKKKKKK..",
        "...KGGKGGKGGK...",
        "...KGGKGGKGGK...",
        "....KGKGGKGK....",
        "....KKKKKKKK....",
    ]),
    # Финиш: флаг-леденец, красно-белая спираль на палочке с розовым бантом.
    "flag": _pad([
        ".....KKKKKK.....",
        "...KKRRRRRRKK...",
        "..KRRRWWWWRRRK..",
        "..KRRWWRRRRWRK..",
        "..KRWWRRWWRWRK..",
        "..KRWRRWWRRWRK..",
        "..KRWRRWRRWWRK..",
        "..KRWWRRRRWRRK..",
        "..KRRWWWWWWRRK..",
        "...KKRRRRRRKK...",
        ".....KKKKKK.....",
        "....KKKWWKKK....",
        "...KPPKWWKPPK...",
        "....KKKWWKKK....",
        "......KWWK......",
        "......KKKK......",
    ]),
    # Земля: розовая глазурь с бликами и потёками, под ней вафля.
    "ground": _pad([
        "PPPPPPPPPPPPPPPP",
        "PWWPPPPPPPWPPPPP",
        "PPPPPPPPPPPPPPPP",
        "PPPPKKPPPPPKKPPP",
        "KPPKGGKPPPKGGKPK",
        "GKKGGGGKPKGGGGKG",
        "GGGGGGGGKGGGGGGG",
        "GGGGGGGGGGGGGGGG",
    ] + _WAFFLE),
    "ground_inner": _pad(_WAFFLE + _WAFFLE),
    # Платформа: вафельная плитка под белой глазурью с посыпкой.
    "platform": _pad([
        "WWWWWWWWWWWWWWWW",
        "WPWWWRWWWPWWWRWW",
        "GWWGGGWGGGGWWGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ]),
    # Облака сахарной ваты: розовые, белая кромка сверху.
    "cloud_small": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "......KKKK......",
        "....KKWWWPKKK...",
        "...KWWPPPPPPPK..",
        "..KWPPPPPPPPPPK.",
        "..KPPPPPPPPPPPK.",
        "...KPPKKPPPPKK..",
        "....KK..KKKK....",
    ]),
    "cloud_big": _pad([
        "." * 32, "." * 32,
        "..............KKKKK.............",
        "........KKKK.KWWWWPKK...........",
        ".......KWWWPKWWPPPPPPK..KKK.....",
        ".....KKWWPPPPPPPPPPPPPKKWWPK....",
        "....KWWPPPPPPPPPPPPPPPPPPPPPK...",
        "...KWPPPPPPPPPPPPPPPPPPPPPPPPK..",
        "...KPPPPPPPPPPPPPPPPPPPPPPPPPK..",
        "....KPPPPKKPPPPPPPPKKPPPPPPKK...",
        ".....KKKK..KKPPPPKK..KKKKKK.....",
        ".............KKKK...............",
    ], w=32),
})


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import sweets8
        sweets8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
