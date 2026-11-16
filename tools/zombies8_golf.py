#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Зомби» (#137): зеркало словаря `GOLF` из `pixel_sprites.py` и модуля
`space8_golf.py`, те же ключи и размеры карт. Выживший с лопатой вместо клюшки лицом вправо в
трёх кадрах (0 стойка у мяча, 1 замах, лопата за головой, 2 проводка, лопата над передним
плечом): синяя бейсболка козырьком вправо, красная куртка, зелёный рюкзак за спиной, джинсы и
белые кеды. Мяч тыква 8×8 (зелёный хвостик, чёрные дольки и блик видны при вращении), лунка
разрытая могила 16×8 (отвалы земли на 2 px над землёй, на дне кость), флаг убежища 16×24
древком в колонке 3. Земля: жухлая трава кладбища (`golf_sand` верхний тайл с чёрной кромкой,
`golf_sand_inner` толща), плиты грина и ти (`golf_deck`, под ними кладка склепа `golf_hull`),
вместо моря болотная жижа `golf_sea` (зелёные гребни сверху, над ними прозрачно), всплеск жижи
`golf_splash`. Пропы: самодельный миномёт `golf_cannon` и армейский ящик `golf_chest`; плиты,
кладка и пропы служат и сценой файтинга.

    python3 tools/zombies8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Жухлая трава кладбища: зелёный дёрн, тёмные комья, белые косточки и сухие стебли, капля крови.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGWGGGGGGGGKGGGG",
    "GGGWGGGGGGGGKGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGKKGGGGGGG",
    "GGGGGGGGGGGGGGWG",
    "GKGGGGGGGGGGGWGG",
    "GGKGGGGGGGGGGGGG",
    "GGGGGGGGGRGGGGGG",
    "GGGGWWGGGGGGGGGG",
    "GGGGGGGGGGGGGKGG",
    "GGGGGGGGKGGGGGGG",
    "GGKGGGGGGKGGGGWG",
    "GGGGGGGGGGGGGGGG",
]

# Кладка склепа: ряды синего камня со швами вразбежку, белые сколы, зелёный мох в швах,
# трещина. Не зелёная и не красная: на ней стоят бойцы файтинга, куртка и зомби читаются.
HULL = [
    "BBBBBBKBBBBBBBBB",
    "BWBBBBKBBBBBBGBB",
    "BBBBBBKBBBBBGGBB",
    "KKKKKKKKKKKKKKKK",
    "BBBBBBBBBBBKBBBB",
    "BBBBKBBBBBBKBBWB",
    "BGBBBKBBBBBKBBBB",
    "KKKKKKKKKKKKKKKK",
    "BBBKBBBBBBBBBBBB",
    "BBBKBBBBWWBBBBBB",
    "BBBKBBBBBBBBBBBB",
    "KKKKKKKKKKKKKKKK",
    "BBBBBBBBBKBBBBBB",
    "BBWBBBBBBKBBBBBB",
    "BBBBBBGGBKBBBBWB",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Выживший: козырёк смотрит вправо, рюкзак слева за спиной, штык лопаты у мяча.
    "golf_hero_0": [
        "................",
        "....KKKKK.......",
        "...KBBBBBK......",
        "..KBBBBBBBBK....",
        "...KWWWKWK......",
        "...KWWWWWK......",
        "...KKWWWK.......",
        "..KGKRRRRKK.....",
        "..KGKRRWRRRK....",
        "..KGKRRRRKWK....",
        "...KKKKKKK.K....",
        "....KBBBBK..K...",
        "....KBBBBK...K..",
        "....KBKKBK...K..",
        "...KWWKKWWK.KWK.",
        "...KKKK.KKK.KKK.",
    ],
    "golf_hero_1": [
        "KWK.............",
        "KKK..KKKKK......",
        ".K..KBBBBBK.....",
        ".KKKBBBBBBBBK...",
        "..KKKWWWKWK.....",
        "..KRKWWWWWK.....",
        "...KRKWWWK......",
        "..KGKRRRRRK.....",
        "..KGKRRWRRK.....",
        "..KGKRRRRRK.....",
        "...KKKKKKK......",
        "....KBBBBK......",
        "....KBBBBK......",
        "....KBKKBK......",
        "...KWWKKWWK.....",
        "...KKKK.KKK.....",
    ],
    "golf_hero_2": [
        ".............KWK",
        "....KKKKK....KKK",
        "...KBBBBBK..K...",
        "..KBBBBBBBBKK...",
        "...KWWWKWKKK....",
        "...KWWWWWKRK....",
        "...KKWWWKRK.....",
        "..KGKRRRRRK.....",
        "..KGKRRWRRK.....",
        "..KGKRRRRRK.....",
        "...KKKKKKK......",
        "....KBBBBK......",
        "....KBBBBK......",
        "...KBK..KBK.....",
        "...KWK..KWWK....",
        "...KK....KKK....",
    ],
    # Мяч: тыква 8×8, зелёный хвостик сверху, чёрные дольки и белый блик сбоку (видны при вращении).
    "golf_ball": [
        "..KGGK..",
        ".KRGGRK.",
        "KRKRRKRK",
        "KWKRRKRK",
        "KWKRRKRK",
        "KRKRRKRK",
        ".KRRRRK.",
        "..KKKK..",
    ],
    # Лунка: разрытая могила сбоку, отвалы земли над землёй на 2 px, в яме белеет кость.
    "golf_cup": [
        ".KKK........KKK.",
        "KBWBK......KBBBK",
        "KBBBBKKKKKKBBWBK",
        "KBBKKKKKKKKKKBBK",
        ".KBBKKKKKKKKBBK.",
        ".KBBBKWKKWKBBBK.",
        "..KBBBKWWKBBBK..",
        "..KKKKKKKKKKKK..",
    ],
    # Флаг убежища: древко W в колонке 3 до низа, красный фонарь сверху, зелёное рваное
    # полотнище с белым крестом.
    "golf_flag": [
        "...RKKKKKKKKK...",
        "...WGGGWWGGGGK..",
        "...WGGGWWGGGK...",
        "...WGWWWWWWGGK..",
        "...WGGGWWGGGK...",
        "...WGGGWWGGGGK..",
        "...WKKKKKKKKK...",
    ] + ["...W............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[5]],
    # Плиты: чёрная кромка, белая полоса тёсаного камня, под ней кладка склепа.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "WWWWWWWWWWWWWWWW"] + HULL[2:],
    "golf_hull": HULL,
    # Болотная жижа: зелёные гребни с белым бликом сверху (над ними прозрачно), чёрная толща
    # с ряской, синей рябью и пузырями.
    "golf_sea": [
        "....GG......GG..",
        "..GGWWGG..GGWWGG",
        "GGWWGGGGGGWWGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKGGGGKKKKGGGGKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKBBBKKKKKKKKK",
        "KKKKKKKKKKKGGKKK",
        "KGKKKKKKKKKKKKKK",
        "KKKKKKKBBBKKKKKK",
        "KKKKKKKKKKKKKKBB",
        "KKKGWKKKKKKKKKKK",
        "KKKGGKKKKKBBBKKK",
        "BKKKKKKKKKKKKKKK",
        "KKKKKBBKKKKKKGKK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Всплеск жижи: тягучие капли вверх, зелёная корона с белым бликом.
    "golf_splash": [
        "................",
        "................",
        "....G......G....",
        "....G..G...G....",
        "..G....G......G.",
        "..G..G.GG..G..G.",
        "...G.GWGG.GG.G..",
        ".G.GGGWGGGGGGG.G",
        "...GWGGGGGGGWG..",
        "..GGWGGKKKGGGGG.",
        ".GGGGGKKKKKGGGGG",
        ".GGGGGGGGGGGGGG.",
        "................",
        "................",
        "................",
        "................",
    ],
    # Самодельный миномёт: труба под углом вверх-вправо с красной изолентой и светлым срезом
    # дула, сошка, опорная плита из жести.
    "golf_cannon": [
        "................",
        "..........KKKK..",
        ".........KBBWWK.",
        "........KBBBBK..",
        ".......KBBBBK...",
        "......KRRBBK....",
        ".....KBRRBKK....",
        "....KBBBBK.KK...",
        "...KBBBBK...KK..",
        "..KBBBBK.....K..",
        "..KBBBK......KK.",
        "..KBBK........K.",
        ".KKKKKK.......K.",
        "KWWWWWWK......K.",
        "KWBBBBWK.....KWK",
        "KKKKKKKK.....KKK",
    ],
    # Армейский ящик: зелёные доски, крышка с белыми защёлками, трафарет и красная метка.
    "golf_chest": [
        "................",
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        ".KGGGGGGGGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KKKKKKKKKKKKKK.",
        ".KGGKWKGGKWKGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KGWGWWGWGGRRGK.",
        ".KGGGGGGGGGRRGK.",
        ".KGWWGWGWWGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KBBBBBBBBBBBBK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KRGWB."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import zombies8
        zombies8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
