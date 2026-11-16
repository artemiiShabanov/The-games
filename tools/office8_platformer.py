#!/usr/bin/env python3
"""Платформер 8-bit, набор «Офис» (#137): те же слоты и размеры карт, что у космоса
(`pixel_sets_extra.SPACE`). Клерк в белой рубашке с красным галстуком, в очках и с бейджем,
сотрудник в чёрном костюме с усами и папкой под мышкой, бумажный самолётик, жетон на кофе,
часы на стойке (отметка прихода), флажок «пятница», шкафы-картотеки под столешницей, полка,
летящие листы бумаги и стикеры. Палитра `office8.PALETTE`: K чёрный, W белый, B синий,
R красный, Y тёплый жёлтый.

    python3 tools/office8_platformer.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sets_extra import DOTS, _hero, _pad  # noqa: E402

# Торс клерка, 13 строк: тёмные волосы с чубом, лицо вправо, круглые очки, белая рубашка,
# красный галстук, синий бейдж на груди, кисти цвета кожи. Синие брюки дорисовывает `_hero`.
# Ряды 8-9 переписывает прыжок: в них только плечи и руки.
_CLERK = [
    DOTS,
    ".....KKKKKKK....",
    "....KKKKKKKKK...",
    "...KKKYYYYYYK...",
    "...KKYWKYWKYK...",
    "...KKYYYYYYYK...",
    "....KYYYYYYK....",
    ".....KWRRWK.....",
    "....KWWRRWWK....",
    "...KWKWRRBKWK...",
    "...KWKWRRWKWK...",
    "...KYKWWRWKYK...",
    "....KBBBBBBK....",
]

# Ящик картотеки: 7 рядов и шов, рамка ярлыка с белой карточкой и жёлтая ручка под ней.
_DRAWER = [
    "BBBBBBBBBBBBBBBK",
    "BBBBKKKKKKKBBBBK",
    "BBBBKWWWWWKBBBBK",
    "BBBBKKKKKKKBBBBK",
    "BBBBBBBBBBBBBBBK",
    "BBBBBBYYYBBBBBBK",
    "BBBBBBBBBBBBBBBK",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = _hero(_CLERK, "B")
SPRITES.update({
    # Сотрудник в чёрном костюме: идёт влево, усы торчат вперёд, папка под мышкой, отлив
    # лацканов и стрелки брюк синим, чтобы костюм не сливался в пятно.
    "enemy_0": _pad([
        DOTS,
        "....KKKKKKK.....",
        "...KKKKKKKKK....",
        "...KYYYYYKKK....",
        "...KYKYKYYKK....",
        "..KKKKKKYYYK....",
        "...KYYYYYYK.....",
        "...KKBWKWBKK....",
        "..KKKKBWKBKKK...",
        ".KYYYKKBKBKKK...",
        ".KYYYYKKKKBKK...",
        ".KYYYKKKKKKKK...",
        "..KKKKKKKKKK....",
        "....KKBK.KBKK...",
        "....KKBK.KBKK...",
        "...KKKKK.KKKK...",
    ]),
    "enemy_1": _pad([
        DOTS,
        "....KKKKKKK.....",
        "...KKKKKKKKK....",
        "...KYYYYYKKK....",
        "...KYKYKYYKK....",
        "..KKKKKKYYYK....",
        "...KYYYYYYK.....",
        "...KKBWKWBKK....",
        "..KKKKBWKBKKK...",
        ".KYYYKKBKBKKK...",
        ".KYYYYKKKKBKK...",
        ".KYYYKKKKKKKK...",
        "..KKKKKKKKKK....",
        ".....KKBKBKK....",
        ".....KKBKBK.....",
        "....KKKKKKK.....",
    ]),
    # Бумажный самолётик: нос влево, верхнее крыло белое, сгиб и нижнее крыло в синей тени.
    "parrot_0": _pad([
        DOTS, DOTS, DOTS,
        ".............WW.",
        "..........WWWWW.",
        ".......WWWWWWW..",
        "....WWWWWWWWWW..",
        ".WWWWWWWWWWWW...",
        "BBBBBBBBBBBBB...",
        "...BBBWWWBBB....",
        "......BBWBB.....",
        ".........B......",
    ]),
    "parrot_1": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "............WWW.",
        "........WWWWWWW.",
        "....WWWWWWWWWW..",
        ".WWWWWWWWWWWW...",
        "BBBBBBBBBBBBB...",
        "...BBBWWWBBB....",
        "......BBWWBB....",
        ".........BWB....",
        "..........B.....",
    ]),
    # Жетон на кофе: жёлтый кружок с чашкой.
    "coin": _pad([
        DOTS, DOTS,
        ".....KKKKKK.....",
        "...KKYYYYYYKK...",
        "..KYWWYYYYYYYK..",
        "..KYKKKKKKYYYK..",
        "..KYKWWWWKKKYK..",
        "..KYKWWWWKYKYK..",
        "..KYKWWWWKKKYK..",
        "..KYYKKKKYYYYK..",
        "..KYYYYYYYYYYK..",
        "...KKYYYYYYKK...",
        ".....KKKKKK.....",
    ]),
    # Чекпойнт: настенные часы на стойке, стрелки показывают девять.
    "checkpoint": _pad([
        ".....KKKKKK.....",
        "...KKWWRRWWKK...",
        "..KWWWWKKWWWWK..",
        "..KWWWWKKWWWWK..",
        "..KRKKKKKWWWRK..",
        "..KWWWWWWWWWWK..",
        "..KWWWWWWWWWWK..",
        "...KKWWRRWWKK...",
        ".....KKKKKK.....",
        "......KBBK......",
        "......KBBK......",
        "......KBBK......",
        "......KBBK......",
        ".....KKBBKK.....",
        "....KBBBBBBK....",
        "....KKKKKKKK....",
    ]),
    # Финиш: настольный флажок «пятница» с пятёркой на красном полотнище.
    "flag": _pad([
        "...KK...........",
        "..KYYK..........",
        "..KWKKKKKKKKKK..",
        "..KWKRRRRRRRRRK.",
        "..KWKRRWWWWRRRK.",
        "..KWKRRWRRRRRK..",
        "..KWKRRWWWRRRK..",
        "..KWKRRRRRWRRRK.",
        "..KWKRRWWWRRRRK.",
        "..KWKRRRRRRRRK..",
        "..KWKKKKKKKKK...",
        "..KWK...........",
        "..KWK...........",
        "..KWK...........",
        ".KKWKK..........",
        "KBBBBBK.........",
    ]),
    # Земля: белая кромка столешницы, под ней ящики картотеки.
    "ground": _pad(["WWWWWWWWWWWWWWWW"] + _DRAWER[1:] + _DRAWER),
    "ground_inner": _pad(_DRAWER + _DRAWER),
    # Платформа: полка, белая кромка, тёплая доска с сучками.
    "platform": _pad([
        "WWWWWWWWWWWWWWWW",
        "YYYYYYYYYYYYYYYY",
        "YYKYYYYYYYKKYYYY",
        "YYYYYYYYYYYYYYYY",
        "KKKKKKKKKKKKKKKK",
    ]),
    # Вместо облаков летят бумаги: лист со строчками.
    "cloud_small": _pad([
        DOTS, DOTS, DOTS,
        "......KKKKKK....",
        ".....KWWWWWK....",
        ".....KWBBBWK....",
        "....KWWWWWK.....",
        "....KWBBBWK.....",
        "...KWWWWWK......",
        "...KWBBWWK......",
        "...KWWWWWK......",
        "...KKKKKK.......",
    ]),
    # Стопка разлетелась: два листа и жёлтый стикер между ними.
    "cloud_big": _pad([
        "." * 32, "." * 32,
        "....KKKKKKK.....................",
        "...KWWWWWWK...........KKKKKKK...",
        "...KWBBBBWK..KKKKKKK..KWWWWWWK..",
        "..KWWWWWWK...KYYYYYK..KWBBBBWK..",
        "..KWBBBWWK...KYKKKYK...KWWWWWWK.",
        ".KWWWWWWK....KYYYYYK...KWBBBWWK.",
        ".KWBBBBWK....KYKKYYK...KWWWWWWK.",
        ".KWWWWWWK....KYYYKK.....KWBBBBWK",
        ".KKKKKKKK....KKKKK......KWWWWWWK",
        "........................KKKKKKKK",
    ], w=32),
})

if __name__ == "__main__":
    if "--preview" in sys.argv:
        import office8
        office8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
