#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Космос» (#136): зеркало словаря `GOLF` из `pixel_sprites.py`, те же
ключи и размеры карт. Космонавт с клюшкой лицом вправо в трёх кадрах (0 стойка у мяча, 1 замах,
клюшка за головой, 2 проводка, клюшка над передним плечом). Мяч энергосфера 8×8, лунка кратер
16×8 (вал на 2 px над землёй, как комингс люка), флаг экспедиции 16×24 штангой в колонке 3.
Земля: реголит (`golf_sand` верхний тайл с чёрной кромкой, `golf_sand_inner` толща), настил
грина и ти (`golf_deck`, под ним борт станции `golf_hull`), вместо моря озеро плазмы
`golf_sea` (гребни сверху, над ними прозрачно), вспышка `golf_splash`. Пропы: лазерная турель
`golf_cannon` и грузовая капсула `golf_chest`; настил, борт и пропы служат и сценой файтинга.

    python3 tools/space8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Реголит: серый грунт, тёмные камешки и светлые крупинки.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGWGGGGGGGGGGGG",
    "GGGGGGGGGGKKGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGWGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GKGGGGGGGGGGGGWG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGKKGGGGGG",
    "GGGGWGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGWGGG",
    "GGKGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
]

# Борт станции: металлические панели, швы, белые заклёпки, бирюзовые огоньки. Не белый:
# на нём стоят бойцы файтинга, космонавт в белом должен читаться.
HULL = [
    "GGGGGGGGGGGGGGGG",
    "GGWGGGGGGGGGGWGG",
    "GGGGGGGGGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGKGGGGGG",
    "GGGCCGGGGKGGGGGG",
    "GGGGGGGGGKGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGGGGGG",
    "GGWGGGGGGGGGGWGG",
    "GGGGGGGGGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "GGGKGGGGGGGGGGGG",
    "GGGKGGGGGGGCCGGG",
    "GGGKGGGGGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    "golf_hero_0": [
        "................",
        "....KKKKK.......",
        "...KWWWWWK......",
        "..KWWKKKKWK.....",
        "..KWKCCWCKK.....",
        "..KWKCCCCKK.....",
        "...KWKKKKK......",
        "..KGKWWWWKK.....",
        "..KGKWWCWWWK....",
        "..KGKWWWWKKK....",
        "...KKGGGGK.K....",
        "....KWWWWK..K...",
        "....KWWWWK...K..",
        "....KWKKWK...K..",
        "...KGGKKGGK.KGK.",
        "...KKKK.KKK.KKK.",
    ],
    "golf_hero_1": [
        "KGK.............",
        "KKK.KKKKK.......",
        ".K.KWWWWWK......",
        ".KKWWKKKKWK.....",
        "..KKWKCCWCKK....",
        "..KWWKCCCCKK....",
        "...KWWKKKKK.....",
        "..KGKWWWWWK.....",
        "..KGKWWCWWK.....",
        "..KGKWWWWWK.....",
        "...KKGGGGK......",
        "....KWWWWK......",
        "....KWWWWK......",
        "....KWKKWK......",
        "...KGGKKGGK.....",
        "...KKKK.KKK.....",
    ],
    "golf_hero_2": [
        ".............KGK",
        "....KKKKK....KKK",
        "...KWWWWWK..K...",
        "..KWWKKKKWKK....",
        "..KWKCCWCKKK....",
        "..KWKCCCCKK.....",
        "...KWKKKKK......",
        "..KGKWWWWWK.....",
        "..KGKWWCWWK.....",
        "..KGKWWWWWK.....",
        "...KKGGGGK......",
        "....KWWWWK......",
        "....KWWWWK......",
        "...KWK..KWK.....",
        "...KGK..KGGK....",
        "...KK....KKK....",
    ],
    # Мяч: энергосфера 8×8, бирюзовая с белым бликом и тёмным поясом (виден при вращении).
    "golf_ball": [
        "..KKKK..",
        ".KCWWCK.",
        "KCWWCCCK",
        "KCCCCCCK",
        "KKKKCCCK",
        "KCCCCCVK",
        ".KCCCVK.",
        "..KKKK..",
    ],
    # Лунка: кратер сбоку, вал над землёй на 2 px, чаша с бирюзовым маячком на дне.
    "golf_cup": [
        ".KKK........KKK.",
        "KGGGK......KGGGK",
        "KGGGGKKKKKKGGGGK",
        "KGGKKKKKKKKKKGGK",
        ".KGGKKKKKKKKGGK.",
        ".KGGGKKCCKKGGGK.",
        "..KGGGKCCKGGGK..",
        "..KKKKKKKKKKKK..",
    ],
    # Флаг лунки: штанга G в колонке 3 до низа, маячок сверху, вымпел с планетой.
    "golf_flag": [
        "...CKKKKKKKKK...",
        "...GVVVVVVVVK...",
        "...GVVVWWVVVVK..",
        "...GVWWWWWWVVVK.",
        "...GVVVWWVVVVK..",
        "...GVVVVVVVVK...",
        "...GKKKKKKKK....",
    ] + ["...G............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[4]],
    # Настил: чёрная кромка, белая полоса кромки, под ней панели борта.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "WWWWWWWWWWWWWWWW"] + HULL[2:],
    "golf_hull": HULL,
    # Озеро плазмы: бирюзовые гребни сверху (над ними прозрачно), фиолетовая толща с искрами.
    "golf_sea": [
        "....CC......CC..",
        "..CCWWCC..CCWWCC",
        "CCWWCCCCCCWWCCCC",
        "CCCCCCCCCCCCCCCC",
        "VVCCCCVVVVCCCCVV",
        "VVVVVVVVVVVVVVVV",
        "VVVVVVCCVVVVVVVV",
        "VVVVVVVVCVVVVVVV",
        "VVVVVVVVVVVVVVVV",
        "VVKVVVVVVVVVVVVV",
        "VVVVVVVVVVVVVVVV",
        "VVVVVVVVVVVVCCVV",
        "VVVCVVVVVVVVVVVV",
        "VVVVVVVVVVKVVVVV",
        "VVVVVVVVVVVVVVVV",
        "VVVVVVVVVVVVVVVV",
    ],
    # Вспышка плазмы: искры вверх, бирюзовый купол с белым ядром.
    "golf_splash": [
        "................",
        "................",
        "......C...C.....",
        "....C..W.W..C...",
        "......CCCCC.....",
        "...C.CCWWWCC.C..",
        ".....CWWWWWC....",
        "..C.CCWWWWWCC.C.",
        "....CWWVVVWWC...",
        "...CCWVVVVVWCC..",
        "..CWWVVVVVVVWWC.",
        ".CCCCCCCCCCCCCCC",
        "................",
        "................",
        "................",
        "................",
    ],
    # Лазерная турель: ствол вправо с бирюзовым излучателем, поворотный купол, тренога.
    "golf_cannon": [
        "................",
        "................",
        "................",
        "................",
        "....KKKKKK......",
        "...KWWWWWWKKKKK.",
        "..KWWCCWWWGGGGCK",
        "..KWWCCWWWGGGGCK",
        "...KWWWWWWKKKKK.",
        "....KKGGKK......",
        ".....KGGK.......",
        "....KKGGKK......",
        "...KGGGGGGK.....",
        "..KGGKKKKGGK....",
        ".KGGK....KGGK...",
        ".KKK......KKK...",
    ],
    # Грузовая капсула: белый бочонок с металлическими обручами, окошко, фиолетовая метка.
    "golf_chest": [
        "................",
        "................",
        "................",
        "...KKKKKKKKKK...",
        "..KWWWWWWWWWWK..",
        ".KWWWWKKKKWWWWK.",
        ".KWWWKCCWCKWWWK.",
        ".KWWWKCCCCKWWWK.",
        ".KWWWWKKKKWWWWK.",
        ".KGGGGGGGGGGGGK.",
        ".KKKKKKKKKKKKKK.",
        ".KWWVVWWWWWWWWK.",
        ".KWWVVWWWWWWWWK.",
        ".KGGGGGGGGGGGGK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KWCVG."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import space8
        space8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
