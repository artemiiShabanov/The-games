#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Супергерои» (#137): зеркало словаря `GOLF` из `pixel_sprites.py` и
модуля `space8_golf.py`, те же ключи и размеры карт. Герой с клюшкой лицом вправо в трёх кадрах
(0 стойка у мяча, 1 замах, клюшка за головой, 2 проводка, клюшка над передним плечом): чёрный
хохолок и маска-домино, синее трико со звездой на груди, красный пояс, жёлтые перчатки и сапоги,
жёлтый плащ за спиной (на замахе прижат, на проводке отлетает назад). Мяч со звездой 8×8
(жёлтый, синяя звезда и чёрный шов видны при вращении), лунка это открытый люк на крыше 16×8
(бетонная горловина на 2 px над землёй, в шахте жёлтая лесенка), флаг с эмблемой 16×24 древком
в колонке 3. Земля: бетон крыши с гравием (`golf_sand` верхний тайл с чёрной кромкой,
`golf_sand_inner` толща), парапет грина и ти (`golf_deck` с жёлтой кромкой, под ним кирпичная
стена `golf_hull`), вместо моря бассейн на крыше `golf_sea` (гребни сверху, над ними
прозрачно, в толще закатные блики), всплеск `golf_splash`. Пропы: лучевая пушка `golf_cannon`
(ствол вправо, катушки, красная линза, тумба с батареей) и бронированный кейс `golf_chest`
(ручка, замок, заклёпки); парапет, стена и пропы служат и сценой файтинга.

    python3 tools/superheroes8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Бетон крыши: серо-зелёная плита, гравий, трещина, кирпичная крошка и жёлтая искра стекла.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGKGGGGG",
    "GGKGGGGGGGGKGGGG",
    "GGGGGGRGGGGGKGGG",
    "GGGGGGGGGGGGKGGG",
    "GGGGGGGGGGGGGGGG",
    "GKKGGGGGGYGGGGGG",
    "GGGGGGGGGGGGGGKG",
    "GGGGGKGGGGGGGGGG",
    "GGGGKGGGGGGRGGGG",
    "GGGGKGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGYGGGGGGKKGGGGG",
    "GGGGGGGGGGGGGGKG",
    "GGGGGGGGGGGGGGGG",
]

# Кирпичная стена дома: красные кирпичи вразбежку на чёрных швах, пара бетонных заплат и
# жёлтые блики заката. Не синяя: на ней стоят бойцы файтинга, трико героя должно читаться.
HULL = [
    "RRRRRKRRRRRRRKRR",
    "RYRRRKRRRRRRRKRR",
    "RRRRRKRRRRRRRKRR",
    "KKKKKKKKKKKKKKKK",
    "RKRRRRRRRKGGGGGG",
    "RKRRRRRRRKGGGGGG",
    "RKRRRRRRRKGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "RRRRRKRRRRRRRKRR",
    "RRRRRKRRRYRRRKRR",
    "RRRRRKRRRRRRRKRR",
    "KKKKKKKKKKKKKKKK",
    "GKRRRRRRRKRRRRRR",
    "GKRRRRRRRKRRRRRR",
    "GKRRRRRRRKRRRRRR",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Стойка у мяча: клюшка от рук вниз вправо, головка у земли. Плащ висит за спиной.
    "golf_hero_0": [
        ".....KK.........",
        "....KKKKKK......",
        "...KKKKKKKK.....",
        "...KKYYYYYK.....",
        "...KYKKYKYK.....",
        "...KYYYYYYK.....",
        "....KYYYYK......",
        "..KYKBBBBKK.....",
        "..KYKBYBBBYK....",
        "..KYKBBBBKKK....",
        ".KYYKRRRRK.K....",
        ".KYYKBBBBK..K...",
        ".KYYKBBBBK...K..",
        ".KKKKBKKBK...K..",
        "...KYYKKYYK.KGK.",
        "...KKKK.KKK.KKK.",
    ],
    # Замах: руки вверх назад, клюшка за головой, плащ прижат к спине.
    "golf_hero_1": [
        "KGK...KK........",
        "KKK.KKKKKK......",
        ".K.KKKKKKKK.....",
        ".KYKKYYYYYK.....",
        "..KBKKKYKYK.....",
        "..KBYYYYYYK.....",
        "...KBYYYYK......",
        "..KYKBBBBBK.....",
        "..KYKBYBBBK.....",
        "..KYKBBBBBK.....",
        "..KYKRRRRK......",
        ".KYYKBBBBK......",
        ".KYYKBBBBK......",
        ".KKKKBKKBK......",
        "...KYYKKYYK.....",
        "...KKKK.KKK.....",
    ],
    # Проводка: шаг вперёд, клюшка над передним плечом, плащ отлетает назад.
    "golf_hero_2": [
        ".....KK......KGK",
        "....KKKKKK...KKK",
        "...KKKKKKKK.K...",
        "...KKYYYYYKK....",
        "...KYKKYKYKYK...",
        "...KYYYYYYKBK...",
        "....KYYYYKBK....",
        "...KKBBBBBK.....",
        "..KYKBYBBBK.....",
        ".KYYKBBBBBK.....",
        "KYYYKRRRRK......",
        "KKKKKBBBBK......",
        "....KBBBBK......",
        "...KBK..KBK.....",
        "...KYK..KYYK....",
        "...KK....KKK....",
    ],
    # Мяч со звездой 8×8: жёлтый, синяя звезда слева сверху и чёрный шов, видно вращение.
    "golf_ball": [
        "..KKKK..",
        ".KYBYYK.",
        "KYBBBYYK",
        "KYYBYYYK",
        "KYYYYKKK",
        "KYYYKYRK",
        ".KYYKYK.",
        "..KKKK..",
    ],
    # Лунка: открытый люк в разрезе, бетонная горловина на 2 px над землёй, в шахте лесенка.
    "golf_cup": [
        "KKKK........KKKK",
        "KGGK........KGGK",
        "KGGKKKKKKKKKKGGK",
        "KGGKKYKKKKYKKGGK",
        "KRGKKYYYYYYKKGRK",
        "KGGKKYKKKKYKKGGK",
        "KRGKKYYYYYYKKGRK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Флаг лунки: древко G в колонке 3 до низа, жёлтый шар-навершие, синее полотнище с эмблемой.
    "golf_flag": [
        "...YKKKKKKKKKK..",
        "...GBBBBBBBBBBK.",
        "...GBBBBYYBBBK..",
        "...GBBYYYYYYBBK.",
        "...GBBBYYYYBBK..",
        "...GBBBYBBYBBBK.",
        "...GKKKKKKKKKK..",
    ] + ["...G............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[5]],
    # Парапет: чёрная кромка, жёлтая полоса края крыши, под ней кирпичная стена.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY"] + HULL[2:],
    "golf_hull": HULL,
    # Бассейн на крыше: гребни с жёлтыми бликами заката сверху (над ними прозрачно), синяя
    # толща, ниже темнеет тенями волн.
    "golf_sea": [
        "....BB......BB..",
        "..BBYYBB..BBYYBB",
        "BBYYBBBBBBYYBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBYYBBBBBBBBB",
        "BBBBBBBBBBBBKKBB",
        "BKKBBBBBBBBBBBBB",
        "BBBBBBBBBYBBBBBB",
        "BBBBBBKKKBBBBBBB",
        "BBBBBBBBBBBBBBKK",
        "KKBBYBBBBBBBBBBB",
        "BBBBBBBBBBKKKBBB",
        "BBBKKKBBBBBBBBBB",
        "BBBBBBBBBBBBBYBB",
        "KBBBBBBBKKKBBBBK",
        "BBKKBBBBBBBBKKBB",
    ],
    # Всплеск: капли вверх, синий купол воды с жёлтой сердцевиной.
    "golf_splash": [
        "................",
        ".......B........",
        "....B.....B.....",
        "..B....Y.....B..",
        ".....B.B.B......",
        "...B..BBBBB..B..",
        ".....BBYYYBB....",
        "..B.BBYYYYYBB.B.",
        "....BYYBBBYYB...",
        "...BBYBBBBBYBB..",
        "..BBYBBBBBBBYBB.",
        ".BBBBBBBBBBBBBBB",
        "................",
        "................",
        "................",
        "................",
    ],
    # Лучевая пушка: ствол вправо с двумя жёлтыми катушками и красной линзой, сзади тарелка
    # отражателя, тумба с батареей на широкой плите.
    "golf_cannon": [
        "................",
        "................",
        "..KK............",
        ".KGGK...........",
        ".KGGKKKKKKKKKK..",
        ".KGGKGYGGYGGGKK.",
        ".KGGKGYGGYGGGRRK",
        ".KGGKGYGGYGGGRRK",
        ".KGGKKKKKKKKKKK.",
        ".KGGKKGGK.......",
        "..KK.KGGK.......",
        "....KKGGKK......",
        "....KGYYGK......",
        "....KGYYGK......",
        "..KKKGGGGKKK....",
        "..KKKKKKKKKK....",
    ],
    # Бронированный кейс: ручка сверху, стальной корпус с заклёпками по углам, жёлтый замок,
    # красная полоса опасности понизу.
    "golf_chest": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KGK..KGK....",
        ".KKKKKKKKKKKKKK.",
        ".KGGGGGGGGGGGGK.",
        ".KGKGGGGGGGGKGK.",
        ".KGGGGKKKKGGGGK.",
        ".KKKKKKYYKKKKKK.",
        ".KGGGGKYYKGGGGK.",
        ".KGGGGGKKGGGGGK.",
        ".KGKGGGGGGGGKGK.",
        ".KRRKRRKRRKRRKK.",
        ".KKKKKKKKKKKKKK.",
        "..KK........KK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KBYRG."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import superheroes8
        superheroes8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
