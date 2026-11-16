#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Фэнтези» (#137): зеркало `space8_golf.py`, те же ключи и размеры карт.
Юный маг в синей мантии и остроконечной шляпе бьёт посохом, лицом вправо, в трёх кадрах
(0 стойка у мяча, навершие посоха у земли справа, 1 замах, посох за головой, 2 проводка, посох
над передним плечом). Мяч хрустальный шар 8×8 с золотой искрой (видна при вращении), лунка
ведьмин круг 16×8 (шляпки грибов на 2 px над землёй, как комингс люка), знамя гильдии 16×24
древком в колонке 3. Земля: мох (`golf_sand` верхний тайл с чёрной кромкой, `golf_sand_inner`
толща), рунные плиты грина и ти (`golf_deck`, под ними кладка `golf_hull`), вместо моря облака
под островами `golf_sea` (клубы сверху, над ними прозрачно), всплеск тумана `golf_splash`.
Пропы: кристалл на треноге `golf_cannon` и сундук-мимик `golf_chest`; плиты, кладка и пропы
служат и сценой файтинга. Палитра в `fantasy8.py`: K чёрный, B мантия и камень, G зелень,
Y золото и дерево, W свет.

    python3 tools/fantasy8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Мох: зелёный ковёр, тёмные проплешины, золотые цветки и белые росинки.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGYGGGGGGGGKGGG",
    "GGGGGGGGGGGKGGGG",
    "GGGGGGKGGGGGGGGG",
    "GGGGGKGGGGGGGGWG",
    "GGGGGGGGGGGGGGGG",
    "GKGGGGGGGGYGGGGG",
    "KGGGGGGGGGGGGGGG",
    "GGGGGGGGKGGGGGGG",
    "GGGGWGGKGGGGGGGG",
    "GGGGGGGGGGGGGKGG",
    "GGGGGGGGGGGGKGGG",
    "GGKGGGGYGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
]

# Кладка острова: синие каменные плиты вперевязку, чёрные швы и сколы, золотые руны, мох в
# углах. Не белая и не сплошь синяя: на ней стоят бойцы файтинга, мантия мага должна читаться.
HULL = [
    "BBBBBBBKBBBBBBBB",
    "BKBBBBBKBBBYBBBB",
    "BBBBKBBKBBYBYBKB",
    "KKKKKKKKKKKKKKKK",
    "BBBKBBBBBBBKBBBB",
    "BBBKBBBKBBBKBGGB",
    "GBBKBKBBBBBKGGBB",
    "KKKKKKKKKKKKKKKK",
    "BBBBBBBKBBBBBBBB",
    "BBYBYBBKBBBBBKBB",
    "BBBYBBBKBKBBBBBB",
    "KKKKKKKKKKKKKKKK",
    "BBBKBBBBBBBKBBBB",
    "BGBKBBBBKBBKBBKB",
    "GGBKBBKBBBBKBBBB",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Стойка: маг чуть наклонён к мячу, обе руки на посохе, навершие с кристаллом у земли.
    "golf_hero_0": [
        ".....KK.........",
        "....KBBK........",
        "....KBBBK.......",
        "...KBBBBBK......",
        "..KYYYYYYYK.....",
        ".KBBBBBBBBBK....",
        "..KKYWWWKWK.....",
        "...KYWWWWWK.....",
        "...KBBBBBBKK....",
        "..KBBBBBBBWWK...",
        "..KBBBBBBKKYK...",
        "..KBBBBBBK.KYK..",
        ".KBBBBBBBBK.KYK.",
        ".KYYYYYYYYK..KYK",
        "..KBBKKBBK..KWYK",
        "..KKK..KKK..KKK.",
    ],
    # Замах: посох за головой, кристалл над затылком, руки подняты слева от шляпы.
    "golf_hero_1": [
        "KWK...KK........",
        "KYK..KBBK.......",
        ".KYK.KBBBK......",
        "..KYKBBBBBK.....",
        "..KWWYYYYYYK....",
        "..KBBBBBBBBBK...",
        "..KBKYWWWKWK....",
        "..KBBYWWWWWK....",
        "...KBBBBBBK.....",
        "...KBBBBBBK.....",
        "..KBBBBBBBK.....",
        "..KBBBBBBBK.....",
        ".KBBBBBBBBBK....",
        ".KYYYYYYYYYK....",
        "..KBBKKBBK......",
        "..KKK..KKK......",
    ],
    # Проводка: посох над передним плечом, кристалл вверху справа, ноги в шаге.
    "golf_hero_2": [
        ".....KK......KWK",
        "....KBBK.....KYK",
        "....KBBBK...KYK.",
        "...KBBBBBK.KYK..",
        "..KYYYYYYYKWWK..",
        ".KBBBBBBBBBBK...",
        "..KKYWWWKWKBK...",
        "...KYWWWWWBBK...",
        "...KBBBBBBBK....",
        "..KBBBBBBBK.....",
        "..KBBBBBBK......",
        "..KBBBBBBK......",
        ".KBBBBBBBBK.....",
        ".KYYYYYYYYK.....",
        "..KBK..KBBK.....",
        "..KK....KKK.....",
    ],
    # Мяч: хрустальный шар 8×8, белый блик сверху, синяя глубина, золотая искра сбоку.
    "golf_ball": [
        "..KKKK..",
        ".KWWWBK.",
        "KWWWBBBK",
        "KWWBBBBK",
        "KWBBBYBK",
        "KBBBYYBK",
        ".KBBBBK.",
        "..KKKK..",
    ],
    # Лунка: ведьмин круг сбоку. Два гриба с золотыми шляпками над землёй на 2 px, между ними
    # ямка во мху с золотым свечением на дне.
    "golf_cup": [
        ".KKK........KKK.",
        "KYWYK......KYWYK",
        "KKWKKKKKKKKKKWKK",
        "KGWKKKKKKKKKKWGK",
        ".KGGKKKKKKKKGGK.",
        ".KGGGKKYYKKGGGK.",
        "..KGGGKYYKGGGK..",
        "..KKKKKKKKKKKK..",
    ],
    # Знамя гильдии: древко Y в колонке 3 до низа, кристалл сверху, синее полотнище с золотой
    # звездой и ласточкиным хвостом.
    "golf_flag": [
        "...WKKKKKKKKKKK.",
        "...YBBBBBBBBBBBK",
        "...YBBBYBBBBBBK.",
        "...YBBYWYBBBBK..",
        "...YBBBYBBBBBBK.",
        "...YBBBBBBBBBBBK",
        "...YKKKKKKKKKKK.",
    ] + ["...Y............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[4]],
    # Плиты: чёрная кромка, золотая полоса каймы, под ней кладка.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY"] + HULL[2:],
    "golf_hull": HULL,
    # Море облаков: белые клубы сверху (над ними прозрачно), синяя толща с белыми прядями
    # тумана и золотыми искрами.
    "golf_sea": [
        "...WWW.....WW...",
        ".WWWWWWW.WWWWWW.",
        "WWWWWWWWWWWWWWWW",
        "WWBBWWWWWWBBWWWW",
        "BBBBBBWWBBBBBBWW",
        "BBBBBBBBBBBBBBBB",
        "BBBWWWBBBBBBBBBB",
        "BBBBBBBBBBBYBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBWWWWBBB",
        "BYBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBWWWBBBBBBBBB",
        "BBBBBBBBBBBBBYBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Всплеск тумана: клочья летят вверх, белый клуб с синей тенью, золотые искры.
    "golf_splash": [
        "................",
        "................",
        "......W...Y.....",
        "...Y..WW.W..W...",
        ".....WWWWW......",
        "..W.WWWWWWW..W..",
        "....WWWBWWWW....",
        ".W.WWWWWWWBWW.W.",
        "...WWBWWWWWWW...",
        "..WWWWWWWBWWWW..",
        ".WWBBWWWWWWBBWW.",
        "WWWWBBBBBBBBWWWW",
        "................",
        "................",
        "................",
        "................",
    ],
    # Кристалл на треноге: гранёный кристалл остриём вверх (свет слева, синяя грань справа) в
    # золотой чаше, тренога с распоркой.
    "golf_cannon": [
        "................",
        ".......KK.......",
        "......KWBK......",
        ".....KWWBBK.....",
        ".....KWWBBK.....",
        "....KWWWBBBK....",
        "....KWWWBBBK....",
        "....KWWBBBBK....",
        ".....KWBBBK.....",
        "...KKYYYYYYKK...",
        "...KYYKYYKYYK...",
        "....KKKYYKKK....",
        "....KYKYYKYK....",
        "...KYKKYYKKYK...",
        "..KYK.KYYK.KYK..",
        "..KKK.KKKK.KKK..",
    ],
    # Сундук-мимик: крышка приоткрыта, в щели глаз и белые зубы, зелёный язык свисает через
    # край, золотое дерево с чёрными обручами.
    "golf_chest": [
        "................",
        "................",
        "................",
        "...KKKKKKKKKK...",
        "..KYYKYYYYKYYK..",
        ".KYYYKYYYYKYYYK.",
        ".KYYYKYYYYKYYYK.",
        ".KKKKKKKKKKKKKK.",
        ".KKWKKKKKKKWKKK.",
        ".KWKWKWKWKWKWKK.",
        ".KKKKKKGGKKKKKK.",
        ".KYYYKYGGYKYYYK.",
        ".KYYYKYGGYKYYYK.",
        ".KYYYKYYYYKYYYK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KBGYW."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import fantasy8
        fantasy8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
