#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Офис» (#137): зеркало `space8_golf.py` и словаря `GOLF` из
`pixel_sprites.py`, те же ключи и размеры карт. Клерк в рубашке с галстуком лицом вправо в трёх
кадрах (0 стойка у мяча, 1 замах, зонт за головой, 2 проводка, зонт над передним плечом):
вместо клюшки зонт-трость ручкой вниз. Мяч-антистресс 8×8 с рожицей (видна при вращении), лунка
это кружка, утопленная в пол, 16×8 (края на 2 px над полом, между ними пусто), флажок лунки
16×24: стикер на спице в колонке 3, сверху красная кнопка. Земля: ковролин (`golf_sand` верхний
тайл с чёрной кромкой, `golf_sand_inner` толща), ламинат грина и ти (`golf_deck`, под ним доски
`golf_hull`), вместо моря завал бумаг `golf_sea` (углы листов сверху, над ними прозрачно),
всплеск `golf_splash` это взлетевшие листы. Пропы: копир, стреляющий бумагой, `golf_cannon`
(лоток с листом вправо) и сейф `golf_chest`; ламинат, доски и пропы служат и сценой файтинга,
поэтому доски жёлтые, а не белые и не чёрные: на них читаются и рубашка, и костюм.
Палитра `office8.PALETTE`: K чёрный, W белый, B синий, R красный, Y тёплый жёлтый.

    python3 tools/office8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ковролин: синий ворс, тёмные петли плетения ровной сеткой вразбежку и пара светлых ворсинок.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "BBBBBBBBBBBBBBBB",
    "BBKBBBBBBBKBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBKBBBBBBBKB",
    "BBBBBBBBBBBBWBBB",
    "BBKBBBBBBBKBBBBB",
    "BBBBBBBBBBBBBBBB",
    "BBBBBBKBBBBBBBKB",
    "BBBBBBBBBBBBBBBB",
    "BBKBBBBBBBKBBBBB",
    "BBBBWBBBBBBBBBBB",
    "BBBBBBKBBBBBBBKB",
    "BBBBBBBBBBBBBBBB",
    "BBKBBBBBBBKBBBBB",
    "BBBBBBBBBBBBBBBB",
]

# Доски ламината: жёлтые планки, тёмные швы, стыки вразбежку, светлые прожилки и редкий сучок.
HULL = [
    "YYYYYYYYYYYYYYYY",
    "YYWWWYYYYYYYYWWY",
    "YYYYYYYYYYYYYYYY",
    "KKKKKKKKKKKKKKKK",
    "YYYYYYYYYKYYYYYY",
    "YYYWWYYYYKYYRYYY",
    "YYYYYYYYYKYYYYYY",
    "KKKKKKKKKKKKKKKK",
    "YYYYYYYYYYYYYYYY",
    "YWWYYYYYYWWWYYYY",
    "YYYYYYYYYYYYYYYY",
    "KKKKKKKKKKKKKKKK",
    "YYYKYYYYYYYYYYYY",
    "YYYKYYYYYYWWWYYY",
    "YYYKYYYYYYYYYYYY",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Клерк: тёмные волосы, очки, белая рубашка, красный галстук, синий бейдж и брюки. Зонт
    # держит двумя руками, ручка-крюк у мяча.
    "golf_hero_0": [
        "................",
        "....KKKKK.......",
        "...KKKKKKK......",
        "...KKYYYYK......",
        "...KKYWKYWK.....",
        "...KKYYYYYK.....",
        "....KYYYYK......",
        "....KWWRWK......",
        "...KWWWRWWK.....",
        "...KWBWRWWYK....",
        "....KWWWWK.K....",
        "....KBBBBK..K...",
        "....KBBBBK...K..",
        "....KBKKBK...K..",
        "....KBKKBK..KYK.",
        "....KKK.KKK.KKK.",
    ],
    "golf_hero_1": [
        "KYK.............",
        "KKK.KKKKK.......",
        ".K.KKKKKKK......",
        ".KYKKYYYYK......",
        "..WKKYWKYWK.....",
        "..WKKYYYYYK.....",
        "..WWKYYYYK......",
        "...WWWWRWK......",
        "...KWWWRWWK.....",
        "...KWBWRWWK.....",
        "....KWWWWK......",
        "....KBBBBK......",
        "....KBBBBK......",
        "....KBKKBK......",
        "....KBKKBK......",
        "....KKK.KKK.....",
    ],
    "golf_hero_2": [
        ".............KYK",
        "....KKKKK....KKK",
        "...KKKKKKK...K..",
        "...KKYYYYK..K...",
        "...KKYWKYWK.K...",
        "...KKYYYYYKK....",
        "....KYYYYKYK....",
        "....KWWRWWWK....",
        "...KWWWRWWK.....",
        "...KWBWRWK......",
        "....KWWWWK......",
        "....KBBBBK......",
        "....KBBBBK......",
        "...KBK..KBK.....",
        "...KBK..KBK.....",
        "...KKK..KKKK....",
    ],
    # Мяч-антистресс 8×8: жёлтый, с бликом, рожицей и красной тенью снизу.
    "golf_ball": [
        "..KKKK..",
        ".KYWWYK.",
        "KYKYYKYK",
        "KYYYYYYK",
        "KYKYYKYK",
        "KYYKKYRK",
        ".KYYYRK.",
        "..KKKK..",
    ],
    # Лунка: белая кружка, утопленная в пол. Края на 2 px над полом, синяя полоска по стенке,
    # на дне красная лужица.
    "golf_cup": [
        ".KKK........KKK.",
        "KWWK........KWWK",
        "KWWKKKKKKKKKKWWK",
        "KBBKKKKKKKKKKBBK",
        "KWWKKKKKKKKKKWWK",
        "KWWKKKRRRRKKKWWK",
        ".KWWWWWWWWWWWWK.",
        "..KKKKKKKKKKKK..",
    ],
    # Флажок лунки: спица W в колонке 3 до низа, красная кнопка сверху, стикер с пометками
    # и загнутым уголком.
    "golf_flag": [
        "...RKKKKKKKKK...",
        "...WYYYYYYYYK...",
        "...WYKKKKKKYK...",
        "...WYYYYYYYYK...",
        "...WYKKKKYYYK...",
        "...WYYYYYYWK....",
        "...WKKKKKKK.....",
    ] + ["...W............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[4]],
    # Ламинат грина: чёрная кромка, белая полоса кромки, под ней доски.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "WWWWWWWWWWWWWWWW"] + HULL[2:],
    "golf_hull": HULL,
    # Завал бумаг: углы листов сверху (над ними прозрачно), ниже стопки: синие срезы пачек
    # вразбежку и чёрные строчки текста.
    "golf_sea": [
        "....WW......WW..",
        "..WWWWWW..WWWWWW",
        "WWWKKWWWWWWKKWWW",
        "WWWWWWWWWWWWWWWW",
        "BBBBBBWWBBBBBBBB",
        "WWWWWWWWWWWWWWWW",
        "WWKKKWWWWWWKKWWW",
        "BBBBBBBBBBBBWWBB",
        "WWWWWWWWWWWWWWWW",
        "WWWWWWKKKKWWWWWW",
        "BBWWBBBBBBBBBBBB",
        "WWWWWWWWWWWWWWWW",
        "WKKWWWWWWWWKKKWW",
        "BBBBBBBBBWWBBBBB",
        "WWWWWWWWWWWWWWWW",
        "WWWWKKKWWWWWWWWW",
    ],
    # Всплеск: листы взлетают веером, внизу вздыбленная стопка.
    "golf_splash": [
        "................",
        "................",
        "..WW......WW....",
        ".WBW...W..WBW...",
        ".WW...WWW..WW...",
        "......WBW.......",
        "...W..WWW..W....",
        "..WWW.....WWW...",
        "..WBW.WWW.WBW...",
        "...W.WWBWW.W....",
        "..WWWWBWBWWWW...",
        ".WWWWWWWWWWWWWW.",
        "................",
        "................",
        "................",
        "................",
    ],
    # Копир: крышка, белый корпус с синим экраном и красной кнопкой, лоток вправо с листом,
    # синяя тумба с ящиком бумаги на колёсиках.
    "golf_cannon": [
        "................",
        "................",
        "................",
        "................",
        "..KKKKKKKK......",
        ".KWWWWWWWWK.....",
        ".KKKKKKKKKKKKKK.",
        ".KWBBBWWWWKWWWWK",
        ".KWBBBWRWWKKKKK.",
        ".KWWWWWWWWK.....",
        ".KKKKKKKKKK.....",
        ".KBBBBBBBBK.....",
        ".KBBKYYKBBK.....",
        ".KBBBBBBBBK.....",
        ".KKKKKKKKKK.....",
        "..KK....KK......",
    ],
    # Сейф: синий корпус, утопленная дверца, белый лимб с чёрной ручкой, жёлтый рычаг, ножки.
    "golf_chest": [
        "................",
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        ".KBBBBBBBBBBBBK.",
        ".KBKKKKKKKKKKBK.",
        ".KBKBBBBBBBBKBK.",
        ".KBKBBWWBBBYKBK.",
        ".KBKBWKKWBBYKBK.",
        ".KBKBWKKWBBYKBK.",
        ".KBKBBWWBBBBKBK.",
        ".KBKBBBBBBBBKBK.",
        ".KBKKKKKKKKKKBK.",
        ".KBBBBBBBBBBBBK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KWBRY."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import office8
        office8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
