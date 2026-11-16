#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Ниндзя» (#137): зеркало словаря `GOLF` из `pixel_sprites.py` и модуля
космоса `space8_golf.py`, те же ключи и размеры карт. Ниндзя в синем с красным шарфом и клюшкой
лицом вправо в трёх кадрах (0 стойка у мяча, 1 замах, клюшка за головой, 2 проводка, клюшка над
передним плечом). Мяч расшитый тэмари 8×8, лунка каменная чаша цукубаи 16×8 (край на 2 px над
землёй, как комингс люка), знамя нобори 16×24 бамбуковым древком в колонке 3. Земля: белый
гравий сада камней с бороздами граблей (`golf_sand` верхний тайл с чёрной кромкой,
`golf_sand_inner` толща), помост грина и ти (`golf_deck` с лаковой кромкой, под ним дощатая
стена додзё `golf_hull`), вместо моря пруд с карпом `golf_sea` (гребни сверху, над ними
прозрачно), всплеск `golf_splash`. Пропы: мортира для фейерверка `golf_cannon` и лакированный
ларец `golf_chest`; помост, стена и пропы служат и сценой файтинга, поэтому стена золотая, не
синяя и не красная: на ней стоят синий герой и красный клан. Палитра `ninja8.PALETTE`: K чёрный,
B синий, R красный, W белый, Y золото.

    python3 tools/ninja8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Гравий сада камней: белое поле, золотые борозды граблей волной, редкие тёмные камешки.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "WWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWKWWWW",
    "WWYYYYWWWWYYYYWW",
    "YYWWWWYYYYWWWWYY",
    "WWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWW",
    "WWWKWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWW",
    "YYWWWWYYYYWWWWYY",
    "WWYYYYWWWWYYYYWW",
    "WWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWKWW",
    "WWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWW",
]

# Стена додзё: длинные золотые доски, стык один на тайл, белые шляпки гвоздей, красные
# лаковые накладки. Не синяя и не красная: на ней стоят бойцы файтинга.
HULL = [
    "YYYYYYYYYYYYYYYY",
    "YYWYYYYYYYYYYWYY",
    "YYYYYYYYYYYYYYYY",
    "KKKKKKKKKKKKKKKK",
    "YYYYYYYYYKYYYYYY",
    "YYYRRYYYYKYYYYYY",
    "YYYYYYYYYKYYYYYY",
    "KKKKKKKKKKKKKKKK",
    "YYYYYYYYYYYYYYYY",
    "YYWYYYYYYYYYYWYY",
    "YYYYYYYYYYYYYYYY",
    "KKKKKKKKKKKKKKKK",
    "YYYKYYYYYYYYYYYY",
    "YYYKYYYYYYYRRYYY",
    "YYYKYYYYYYYYYYYY",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Стойка: капюшон с прорезью глаз, концы шарфа за спиной, белые кисти на рукояти,
    # клюшка вниз к мячу, стальная головка у земли.
    "golf_hero_0": [
        "................",
        "....KKKKK.......",
        "...KBBBBBK......",
        "..KBBBBBBBK.....",
        "..KBBWKWWKK.....",
        "..KBBBBBBBK.....",
        "RR.KBBBBBK......",
        ".RRRRRRRRRK.....",
        "RR.KBBBBBWWK....",
        "...KBBBBBKKK....",
        "...KRRRRRK.K....",
        "....KBBBBK..K...",
        "....KBBBBK...K..",
        "....KWKKWK...K..",
        "...KWWKKWWK.KWK.",
        "...KKKK.KKK.KKK.",
    ],
    # Замах: руки подняты у затылка, клюшка за головой, головка вверху слева.
    "golf_hero_1": [
        "KWK.............",
        "KKK.KKKKK.......",
        ".K.KBBBBBK......",
        ".KKBBBBBBBK.....",
        ".WKBBWKWWKK.....",
        ".KBKBBBBBBK.....",
        "RKBBKBBBBK......",
        ".RRRRRRRRRK.....",
        "RR.KBBBBBBK.....",
        "...KBBBBBBK.....",
        "...KRRRRRRK.....",
        "....KBBBBK......",
        "....KBBBBK......",
        "....KWKKWK......",
        "...KWWKKWWK.....",
        "...KKKK.KKK.....",
    ],
    # Проводка: ноги шире, руки вынесены вперёд и вверх, клюшка над передним плечом.
    "golf_hero_2": [
        ".............KWK",
        "....KKKKK....KKK",
        "...KBBBBBK..K...",
        "..KBBBBBBBKK....",
        "..KBBWKWWKWW....",
        "RRKBBBBBBBKBK...",
        ".RRKBBBBBKBBK...",
        "RRRRRRRRRRBK....",
        "...KBBBBBBK.....",
        "...KBBBBBBK.....",
        "...KRRRRRRK.....",
        "....KBBBBK......",
        "....KBBBBK......",
        "...KWK..KWK.....",
        "...KWK..KWWK....",
        "...KK....KKK....",
    ],
    # Мяч: тэмари 8×8, косые стежки золота и красного по белому, синий узел (виден при вращении).
    "golf_ball": [
        "..KKKK..",
        ".KWWRYK.",
        "KWWRYYRK",
        "KWRYYRWK",
        "KRYYRWWK",
        "KYYRWWBK",
        ".KRWWBK.",
        "..KKKK..",
    ],
    # Лунка: каменная чаша цукубаи сбоку, край над землёй на 2 px, на дне золотая монета.
    "golf_cup": [
        ".KKK........KKK.",
        "KBWBK......KBWBK",
        "KBBBBKKKKKKBBBBK",
        "KBBKKKKKKKKKKBBK",
        ".KBBKKKKKKKKBBK.",
        ".KBWBKKYYKKBBBK.",
        "..KBBBKYYKBBBK..",
        "..KKKKKKKKKKKK..",
    ],
    # Знамя нобори: бамбуковое древко Y в колонке 3 до низа, узкое длинное полотнище на
    # перекладине, красное солнце, под ним знак тушью, красная кайма понизу.
    "golf_flag": [
        "...YKKKKKKKK....",
        "...YWWWWWWWK....",
        "...YWWRRRWWK....",
        "...YWRRRRRWK....",
        "...YWRRRRRWK....",
        "...YWWRRRWWK....",
        "...YWWWWWWWK....",
        "...YWKKKKKWK....",
        "...YWWWKWWWK....",
        "...YWKKKKKWK....",
        "...YWWWKWWWK....",
        "...YWWKWKWWK....",
        "...YRRRRRRRK....",
        "...YKKKKKKK.....",
    ] + ["...Y............"] * 10,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[4]],
    # Помост: чёрная кромка, красная лаковая полоса, под ней доски стены.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "RRRRRRRRRRRRRRRR"] + HULL[2:],
    "golf_hull": HULL,
    # Пруд: белые гребни сверху (над ними прозрачно), синяя толща, золотые блики заката
    # и красный карп с белым пятном.
    "golf_sea": [
        "....WW......WW..",
        "..WWBBWW..WWBBWW",
        "WWBBBBBBWWBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBYYBBBBBBBBBB",
        "BBBBBBBBBBBBWWBB",
        "BBBBBBBBBBBBBBBB",
        "BKKBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBRBBBBBBBBB",
        "BBBBBBBRRWRRBBBB",
        "BBBBBBRBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBYYBBBBBBBBBKKB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Всплеск: белые брызги вверх, купол пены с синей водой внутри.
    "golf_splash": [
        "................",
        "................",
        "......W...W.....",
        "....W..B.B..W...",
        "......WWWWW.....",
        "...W.WWBBBWW.W..",
        ".....WBBBBBW....",
        "..W.WWBBBBBWW.W.",
        "....WBBWWWBBW...",
        "...WWBWWWWWBWW..",
        "..WBBWWWWWWWBBW.",
        ".WWWWWWWWWWWWWWW",
        "................",
        "................",
        "................",
        "................",
    ],
    # Мортира для фейерверка: бамбуковый ствол наклонён вверх и вправо, красные обвязки,
    # чёрное жерло с искрой фитиля, дощатый лафет с лаковой полосой.
    "golf_cannon": [
        "..............W.",
        "..........KKKKK.",
        ".........KYYKKKK",
        "........KRYYYKKK",
        ".......KYRRYYYK.",
        "......KYYYRRYK..",
        ".....KYYYYYRRK..",
        "....KRYYYYYYK...",
        "...KYRRYYYYK....",
        "..KYYYRRYYK.....",
        "..KKYYYRRK......",
        "..KKKKKKKKK.....",
        ".KYYKYYYYKYYK...",
        ".KYYYKKKKYYYK...",
        ".KRRRRRRRRRRK...",
        ".KKKKKKKKKKKK...",
    ],
    # Лакированный ларец: красный лак, золотые уголки и гербы, белый шнур с узлом на крышке.
    "golf_chest": [
        "................",
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        ".KYRRRRRRRRRRYK.",
        ".KRRRRRWWRRRRRK.",
        ".KKKKKKWWKKKKKK.",
        ".KYRRRWYYWRRRYK.",
        ".KRRRRRWWRRRRRK.",
        ".KRRYRRWWRRYRRK.",
        ".KRYYYRWWRYYYRK.",
        ".KRRYRRWWRRYRRK.",
        ".KRRRRRWWRRRRRK.",
        ".KYRRRRWWRRRRYK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KBRWY."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import ninja8
        ninja8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
