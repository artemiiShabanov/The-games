#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Замки» (#136): зеркало `space8_golf.py` (и словаря `GOLF` из
`pixel_sprites.py`), те же ключи и размеры карт. Палитра `castles8.PALETTE`: K чёрный, G камень
и латы, R красный, Y золото и дерево, W блики. Рыцарь с колотушкой лицом вправо в трёх кадрах
(0 стойка у мяча, 1 замах, колотушка за головой, 2 проводка, колотушка над передним плечом).
Мяч кожаный набивной 8×8, лунка колодец 16×8 (каменный сруб на 2 px над землёй, как комингс
люка), знамя с гербом 16×24 древком в колонке 3. Земля: золотой луг (`golf_sand` верхний тайл
с чёрной кромкой, `golf_sand_inner` толща), брусчатка грина и ти (`golf_deck`, под ней кладка
`golf_hull`), вместо моря ров с водой `golf_sea` (гребни сверху, над ними прозрачно), всплеск
`golf_splash`. Пропы: баллиста `golf_cannon` и окованный ларь `golf_chest`; брусчатка, кладка
и пропы служат и сценой файтинга.

    python3 tools/castles8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Луг: сухая золотая трава, тёмные комья земли, красные цветки и светлые зёрна.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "YYYYYYYYYYYYYYYY",
    "YYYYYYYYYYYYYYYY",
    "YYYWYYYYYYYYYYYY",
    "YYYYYYYYYYKKYYYY",
    "YYYYYYYYYYYYYYYY",
    "YYYYYYYWYYYYYYYY",
    "YYYYYYYYYYYYYYYY",
    "YKYYYYYYYYYYYYWY",
    "YYYYYYYYYYYYYYYY",
    "YYYYYYYYKKYYYYYY",
    "YYYYWYYYYYYYYYYY",
    "YYYYYYYYYYYYYYYY",
    "YYYYYYYYYYYYWYYY",
    "YYRYYYYYYYYYYYYY",
    "YYYYYYYYYYYYYYYY",
]

# Кладка: каменные блоки вперевязку, чёрные швы, блик в углу блока. Не светлее камня: на ней
# стоят бойцы файтинга, рыцарь в латах должен читаться.
HULL = [
    "GGGGGGGKGGGGGGGG",
    "GWGGGGGKGWGGGGGG",
    "GGGGGGGKGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGKGGGGGGGKGGGG",
    "GGGKGGGGGGGKGGGG",
    "GWGKGWGGGGGKGWGG",
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGKGGGGGGGG",
    "GWGGGGGKGWGGGGGG",
    "GGGGGGGKGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGKGGGGGGGKGGGG",
    "GGGKGGGGGGGKGGGG",
    "GWGKGWGGGGGKGWGG",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Рыцарь: красный плюмаж, шлем с прорезью забрала вправо, красный плащ за спиной, латы.
    "golf_hero_0": [
        "................",
        "....KRRK........",
        "...KRRRRK.......",
        "..KKGGGGKK......",
        "..KGGWGGGGK.....",
        "..KGGGKKKKKK....",
        "..KGGGGGGGGK....",
        "...KKGGGGKK.....",
        "..KRKGGGGGKK....",
        "..KRKGGYGGGGK...",
        "..KRKGGGGGGKYK..",
        "...KKKGGGGKK.YK.",
        "....KGGGGK...YK.",
        "....KGKKGK..KGGK",
        "...KGGKKGGK.KGWK",
        "...KKKK.KKK.KKKK",
    ],
    "golf_hero_1": [
        "GGK.............",
        "KGGK.KRRK.......",
        ".YK.KRRRRK......",
        ".YKKGGGGKK......",
        ".YKGGWGGGGK.....",
        ".YKGGGKKKKKK....",
        "..KGGGGGGGGK....",
        "..YKKGGGGKK.....",
        "..KYKGGGGGK.....",
        "..KRYGGYGGGK....",
        "..KRKGGGGGK.....",
        "...KKKGGGGK.....",
        "....KGGGGK......",
        "....KGKKGK......",
        "...KGGKKGGK.....",
        "...KKKK.KKK.....",
    ],
    "golf_hero_2": [
        "............KGGK",
        "............GGGK",
        "...KRRK.....KYK.",
        "..KRRRRK...KYK..",
        "..KKGGGGKK.KYK..",
        "..KGGWGGGGKYKK..",
        "..KGGGKKKKYKK...",
        "..KGGGGGGYGGK...",
        "...KKGGGYGKK....",
        "..KRKGGYGGGK....",
        "..KRKGGGGGK.....",
        "...KKGGGGK......",
        "....KGGGGK......",
        "...KGK..KGK.....",
        "...KGGK.KGGK....",
        "...KKK...KKK....",
    ],
    # Мяч: кожаный набивной, красный со светлым бликом, золотые стежки и тёмный шов (виден
    # при вращении).
    "golf_ball": [
        "..KKKK..",
        ".KRWWRK.",
        "KRWRRRYK",
        "KRRRRRYK",
        "KKKKRRRK",
        "KRYRRRRK",
        ".KRYRRK.",
        "..KKKK..",
    ],
    # Лунка: колодец сбоку, каменный сруб над землёй на 2 px, чаша с бликом воды на дне.
    "golf_cup": [
        ".KKK........KKK.",
        "KWWWK......KWWWK",
        "KGGGGKKKKKKGGGGK",
        "KGKGGKKKKKKGGKGK",
        ".KGGKKKKKKKKGGK.",
        ".KGKGKKWWKKGKGK.",
        "..KGGGKWWKGGGK..",
        "..KKKKKKKKKKKK..",
    ],
    # Знамя лунки: древко G в колонке 3 до низа, золотой наконечник, красное полотнище с
    # золотым крестом.
    "golf_flag": [
        "...YKKKKKKKKK...",
        "...GRRRYYRRRK...",
        "...GRRRYYRRRRK..",
        "...GRYYYYYYYRRK.",
        "...GRRRYYRRRRK..",
        "...GRRRYYRRRK...",
        "...GKKKKKKKK....",
    ] + ["...G............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[4]],
    # Брусчатка: чёрная кромка, светлая полоса кромки, под ней кладка.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "WWWWWWWWWWWWWWWW"] + HULL[2:],
    "golf_hull": HULL,
    # Ров с водой: белые гребни сверху (над ними прозрачно), каменно-серая толща с рябью.
    "golf_sea": [
        "....WW......WW..",
        "..WWGGWW..WWGGWW",
        "WWGGWWGGWWGGWWGG",
        "GGGGGGGGGGGGGGGG",
        "KKGGKKKKKKGGKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKGGGKKKKKKKKK",
        "KKKKKKKKKKKGGGKK",
        "KKKKKKKKKKKKKKKK",
        "KGGKKKKKKKKKKKKK",
        "KKKKKKKKGWGKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKGGKKKKKKKKKK",
        "KKKKKKKKKKKKGGGK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Всплеск: брызги вверх, водяной купол с белым ядром.
    "golf_splash": [
        "................",
        "................",
        "......W...W.....",
        "....W..G.G..W...",
        "......WWWWW.....",
        "...W.WWGGGWW.W..",
        ".....WGGGGGW....",
        "..W.WWGGGGGWW.W.",
        "....WGGKKKGGW...",
        "...WWGKKKKKGWW..",
        "..WGGKKKKKKKGGW.",
        ".WWWWWWWWWWWWWWW",
        "................",
        "................",
        "................",
        "................",
    ],
    # Баллиста: ложе с болтом вправо, лук поперёк (тетива чёрная), станина на колёсах.
    "golf_cannon": [
        "................",
        "............KYK.",
        "...........KYYK.",
        "..........KYKYK.",
        "...KKKKKKKKYKYK.",
        "..KYYYYYYYYYKWWK",
        "..KRYYYYYYYYKWWK",
        "...KKKKKKKKYKYK.",
        "..........KYKYK.",
        "......KYYK......",
        ".....KYKKYK.....",
        "....KYK..KYK....",
        "...KYK....KYK...",
        "..KGGGK..KGGGK..",
        "..KGWGK..KGWGK..",
        "...KKK....KKK...",
    ],
    # Окованный ларь: дощатый короб с выпуклой крышкой, стальные обручи, замок и скобы.
    "golf_chest": [
        "................",
        "................",
        "................",
        "....KKKKKKKK....",
        "..KKYYYYYYYYKK..",
        ".KYYGYYYYYYGYYK.",
        ".KYYGYYWWYYGYYK.",
        ".KGGGGGWKGGGGGK.",
        ".KKKKKKKWKKKKKK.",
        ".KYYGYYYYYYGYYK.",
        ".KYYGYYYYYYGYYK.",
        ".KYYGYYYYYYGYYK.",
        ".KGGGGGGGGGGGGK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
        "................",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KWYRG."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import castles8
        castles8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
