#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Замки» (#136): зеркало словаря `GOLF` из `pixel_sprites.py` и модуля
`space8_golf.py`, те же ключи и размеры карт. Рыцарь с деревянной киянкой лицом вправо в трёх
кадрах (0 стойка у мяча, 1 замах, киянка за головой, 2 проводка, киянка над передним плечом):
ведёрный шлем с прорезью, красный плюмаж и табард, золотой пояс. Мяч кожаный набивной 8×8 (шов
и красная латка видны при вращении), лунка колодец 16×8 (каменный венец на 2 px над землёй,
внизу блик воды), знамя с гербом 16×24 древком в колонке 3. Земля: песок ристалища
(`golf_sand` верхний тайл с чёрной кромкой, `golf_sand_inner` толща), брусчатка грина и ти
(`golf_deck`, под ней кладка замковой стены `golf_hull`), вместо моря ров `golf_sea` (тёмная
вода, гребни сверху, над ними прозрачно), всплеск `golf_splash`. Пропы: баллиста `golf_cannon`
и окованный ларь `golf_chest`; брусчатка, кладка и пропы служат и сценой файтинга.

    python3 tools/castles8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Песок ристалища: утоптанный золотой грунт, соломинки, камешки и красные лепестки с турнира.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "YYYYYYYYYYYYYYYY",
    "YYYYYYYYYYYYYYYY",
    "YYWWYYYYYYYYYYYY",
    "YYYYYYYYYYKYYYYY",
    "YYYYYYYYYYYYYRYY",
    "YYYYYYWWYYYYYYYY",
    "YYYYYYYYYYYYYYYY",
    "YKYYYYYYYYYYYYYY",
    "YYYYYYYYYYYWWYYY",
    "YYYYRYYYYYYYYYYY",
    "YYYYYYYYKYYYYYYY",
    "YYYYYYYYYYYYYYYY",
    "YWWYYYYYYYYYYKYY",
    "YYYYYYYYYYYYYYYY",
    "YYYYYYYWYYYYYYYY",
]

# Кладка замковой стены: ряды камня со швами вразбежку, светлые сколы, жёлтый лишайник.
HULL = [
    "GGGGGKGGGGGGGGGG",
    "GWGGGKGGGGGGWGGG",
    "GGGGGKGGGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGKGGGG",
    "GGGGGGWGGGGKGGGG",
    "GGGYGGGGGGGKGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGGGKGGGGGGGGGG",
    "GGGGGKGGGGGGGGWG",
    "GGGGGKGGWGGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGKGGGG",
    "GWGGGGGGGGGKGYYG",
    "GGGGGGGGGGGKGGGG",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Рыцарь: плюмаж над шлемом, прорезь забрала смотрит вправо, киянка у мяча.
    "golf_hero_0": [
        "...RR...........",
        "..RRRR..........",
        "...KKKKKKKK.....",
        "..KGGGGGGWK.....",
        "..KGGKKKKKK.....",
        "..KGGGGKGGK.....",
        "...KGGGGGK......",
        "..KGKRRRRKK.....",
        "..KGKRRYRRGK....",
        "..KGKRRRRKKK....",
        "...KYYYYYK.K....",
        "....KRRRRK..K...",
        "....KGGGGK...K..",
        "....KGKKGK...K..",
        "...KGGKKGGK.KYK.",
        "...KKKK.KKK.KKK.",
    ],
    "golf_hero_1": [
        "KYK.RR..........",
        "KKKRRRR.........",
        ".K..KKKKKKKK....",
        ".KKKGGGGGGWK....",
        "..KKGGKKKKKK....",
        "..KGGGGGKGGK....",
        "...KKGGGGGK.....",
        "..KGKRRRRRK.....",
        "..KGKRRYRRK.....",
        "..KGKRRRRRK.....",
        "...KYYYYYK......",
        "....KRRRRK......",
        "....KGGGGK......",
        "....KGKKGK......",
        "...KGGKKGGK.....",
        "...KKKK.KKK.....",
    ],
    "golf_hero_2": [
        "...RR........KYK",
        "..RRRR.......KKK",
        "...KKKKKKKK.K...",
        "..KGGGGGGWKK....",
        "..KGGKKKKKKK....",
        "..KGGGGKGGK.....",
        "...KGGGGGK......",
        "..KGKRRRRRK.....",
        "..KGKRRYRRK.....",
        "..KGKRRRRRK.....",
        "...KYYYYYK......",
        "....KRRRRK......",
        "....KGGGGK......",
        "...KGK..KGK.....",
        "...KGK..KGGK....",
        "...KK....KKK....",
    ],
    # Мяч: кожаный набивной 8×8, чёрный шов дугой, блик и красная латка сбоку (видно вращение).
    "golf_ball": [
        "..KKKK..",
        ".KWYKYK.",
        "KWYYKYYK",
        "KYYYKKKK",
        "KKKYYYYK",
        "KYYKYRRK",
        ".KYKRRK.",
        "..KKKK..",
    ],
    # Лунка: колодец сбоку, каменный венец над землёй на 2 px, тёмный ствол с бликом воды.
    "golf_cup": [
        ".KKK........KKK.",
        "KGWGK......KGWGK",
        "KGGGGKKKKKKGGGGK",
        "KKKKKKKKKKKKKKKK",
        ".KGGKKKKKKKKGGK.",
        ".KGKGKKKKKKGKGK.",
        "..KGGGKWWKGGGK..",
        "..KKKKKKKKKKKK..",
    ],
    # Знамя лунки: древко G в колонке 3 до низа, золотое навершие, красное полотнище с золотым
    # крестом и ласточкиным хвостом.
    "golf_flag": [
        "...YKKKKKKKKKKK.",
        "...GRRRYYRRRRRRK",
        "...GRRRYYRRRRKK.",
        "...GYYYYYYYYK...",
        "...GRRRYYRRRRKK.",
        "...GRRRYYRRRRRRK",
        "...GKKKKKKKKKKK.",
    ] + ["...G............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[4]],
    # Брусчатка: чёрная кромка, светлая полоса тёсаного камня, под ней кладка стены.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "WWWWWWWWWWWWWWWW"] + HULL[2:],
    "golf_hull": HULL,
    # Ров: серые гребни с белой пеной сверху (над ними прозрачно), тёмная вода с рябью и бликами.
    "golf_sea": [
        "....WW......WW..",
        "..WWGGWW..WWGGWW",
        "WWGGGGGGWWGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKGGGGKKKKGGGGKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKGGGKKKKKKKKK",
        "KKKKKKKKKKKWGGKK",
        "KGGKKKKKKKKKKKKK",
        "KKKKKKKGGGKKKKKK",
        "KKKKKKKKKKKKKKGG",
        "KKKGGWKKKKKKKKKK",
        "KKKKKKKKKKGGGKKK",
        "GKKKKKKKKKKKKKKK",
        "KKKKKGGKKKKKKWGK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Всплеск рва: брызги вверх, серая корона воды с белой пеной.
    "golf_splash": [
        "................",
        "................",
        "...W........W...",
        ".....W.W..W.....",
        "..G..W.....W..G.",
        "...GW..WW...WG..",
        "...GWW.WW..WWG..",
        ".G..GWWWWWWWG..G",
        "....GWWWWWWWG...",
        "...GGWWGGGWWGG..",
        "..GGWGGGGGGGWGG.",
        ".GGGGGGGGGGGGGG.",
        "................",
        "................",
        "................",
        "................",
    ],
    # Баллиста: деревянное ложе на козлах, стальные плечи лука дугой, болт с белым жалом вправо.
    "golf_cannon": [
        "................",
        "................",
        "................",
        "........KK......",
        ".......KGGK.....",
        "........KGGK....",
        ".KK......KGK.K..",
        "KYYKKKKKKKGKKWK.",
        "KYYYYYYYYYGYYWWK",
        "KYYKKYYKKKGKKWK.",
        ".KKKYYK..KGK.K..",
        "..KYYK..KGGK....",
        ".KYKKYKKGGK.....",
        "KYK..KYKKK......",
        "KYK..KYYK.......",
        "KKK..KKKK.......",
    ],
    # Окованный ларь: дощатый короб с выпуклой крышкой, железные полосы, замок с белой накладкой.
    "golf_chest": [
        "................",
        "................",
        "................",
        "...KKKKKKKKKK...",
        "..KYYGYYYYGYYK..",
        ".KYWYGYYYYGYYYK.",
        ".KYYYGYYYYGYYYK.",
        ".KKKKKKKKKKKKKK.",
        ".KGGGGKWWKGGGGK.",
        ".KYYYGKWKKGYYYK.",
        ".KYYYGYKKYGYYYK.",
        ".KYYYGYYYYGYYYK.",
        ".KYKYGYYYYGYKYK.",
        ".KGGGGGGGGGGGGK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KGRYW."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import castles8
        castles8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
