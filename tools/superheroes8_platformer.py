#!/usr/bin/env python3
"""Платформер × 8-bit, набор «Супергерои» (#137): зеркало словаря `pixel_sets_extra.SPACE`, те же
ключи и размеры карт. Герой анфас: чёрный хохолок и маска-домино, синее трико со звездой на
груди, жёлтый плащ за плечами, жёлтые сапоги (бег 0-2 с теми же ногами, что у космонавта;
прыжок с кулаками вверх и раскрытым плащом; дэш это полёт лицом вправо, кулак вперёд, плащ
над спиной). Враг `enemy_*` робот-приспешник с одним красным глазом и клешнями, летун
`parrot_*` дрон-шпион с двумя винтами и красным объективом. `coin` значок со звездой,
`checkpoint` сигнальный прожектор с эмблемой на стойке, `flag` финишный флаг с эмблемой.
Земля: бетонный парапет крыши над кирпичной кладкой (`ground`), толща кладки
(`ground_inner`, ряды продолжают верхний тайл), `platform` балка в полосах ограждения. Фон:
закатное облако `cloud_small` и дирижабль `cloud_big` 32×16. Обводка у всех персонажей
замкнута в самих картах, `outlined` им ничего не добавляет.

    python3 tools/superheroes8_platformer.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sets_extra import DOTS, _pad  # noqa: E402

# Голова анфас: хохолок, волосы, лоб, маска с глазами, щёки, подбородок.
_HEAD = [
    "........KK......",
    ".....KKKKKK.....",
    "....KKKKKKKK....",
    "....KYYYYYYK....",
    "....KKYKKYKK....",
    "....KYYYYYYK....",
    "....KKYYYYKK....",
]
# Корпус в стойке: плечи, руки по швам, звезда на груди, пояс; плащ висит за спиной до голеней.
_BODY = [
    "...KBBBBBBBBK...",
    "..KYBKBYYBKBYK..",
    "..KYBKBYYBKBYK..",
    ".KYYBKBBBBKBYYK.",
    ".KYYKKYYYYKKYYK.",
    ".KYYYKBBBBKYYYK.",
]
# Тот же корпус на шаге: плащ подлетает в стороны, полы короче.
_BODY_STEP = [
    "...KBBBBBBBBK...",
    ".KKYBKBYYBKBYKK.",
    "KYYYBKBYYBKBYYYK",
    "KYYKBKBBBBKBKYYK",
    ".KK.KKYYYYKK.KK.",
    "....KBBBBBBK....",
]

SPRITES = {
    "hero_run_0": _HEAD + _BODY + [
        ".KYYKBBKKBBKYYK.",
        ".KKKYYK..KYYKKK.",
        "...KKKK..KKKK...",
    ],
    "hero_run_1": _HEAD + _BODY + [
        ".KYYKBBBBBBKYYK.",
        ".KKK.KYYYYK.KKK.",
        ".....KKKKKK.....",
    ],
    "hero_run_2": _HEAD + _BODY_STEP + [
        "...KKBBKKBBKK...",
        "..KYYKK..KKYYK..",
        "..KKKK....KKKK..",
    ],
    "hero_jump": [
        "........KK......",
        ".....KKKKKK.....",
        "....KKKKKKKK....",
        ".KK.KYYYYYYK.KK.",
        "KYYKKKYKKYKKKYYK",
        "KYYKKYYYYYYKKYYK",
        ".KBK.KYYYYK.KBK.",
        ".KBBKKBBBBKKBBK.",
        "..KKBBBYYBBBKK..",
        ".KYYKBBYYBBKYYK.",
        "KYYYKBBBBBBKYYYK",
        "KYYKKYYYYYYKKYYK",
        ".KK.KBBBBBBK.KK.",
        "....KBBKKBBK....",
        "...KYYK..KYYK...",
        "...KKK....KKK...",
    ],
    "hero_dash": [
        DOTS, DOTS, DOTS, DOTS,
        "..........KKKK..",
        ".........KKKKKK.",
        ".........KKYYYK.",
        "..KKKKK..KKKYKK.",
        ".KYYYYYKKKYYYYK.",
        "KYYYYYYYYKKYYK..",
        ".KKKKKYYKBBKKKKK",
        "KYYKBBBBBBBBBYYK",
        "KYYKBBBBYBBKKKK.",
        ".KKKKKKKKKKK....",
        DOTS, DOTS,
    ],
    "enemy_0": [
        DOTS,
        ".......KK.......",
        "......KYYK......",
        "...KKKKKKKKKK...",
        "..KGGGGGGGGGGK..",
        "..KGGKRYRRKGGK..",
        "..KGGKRRRRKGGK..",
        "..KGGGKKKKGGGK..",
        "...KKKKKKKKKK...",
        ".KKKGGGGGGGGKKK.",
        "KGGKGYYYYYYGKGGK",
        "KGKKGGGGGGGGKKGK",
        "KKK.KKKKKKKK.KKK",
        "....KGGKKGGK....",
        "...KGGK..KGGK...",
        "...KKKK..KKKK...",
    ],
    "enemy_1": [
        DOTS,
        ".......KK.......",
        "......KRRK......",
        "...KKKKKKKKKK...",
        "..KGGGGGGGGGGK..",
        "..KGGKRRYRKGGK..",
        "..KGGKRRRRKGGK..",
        "..KGGGKKKKGGGK..",
        "...KKKKKKKKKK...",
        ".KKKGGGGGGGGKKK.",
        "KGGKGYYYYYYGKGGK",
        "KGGKGGGGGGGGKGGK",
        ".KK.KKKKKKKK.KK.",
        "....KGGKKGGK....",
        "....KGK..KGK....",
        "....KKK..KKK....",
    ],
    "parrot_0": _pad([
        DOTS, DOTS,
        ".KKKKK....KKKKK.",
        "KGGGGGK..KGGGGGK",
        ".KKKKK....KKKKK.",
        "...KK......KK...",
        "..KKKKKKKKKKKK..",
        ".KGGGGKKKKGGGGK.",
        ".KGYGKRYRRKGYGK.",
        ".KGGGKRRRRKGGGK.",
        "..KKKGKKKKGKKK..",
        "....KGK..KGK....",
        "....KK....KK....",
    ]),
    "parrot_1": _pad([
        DOTS, DOTS,
        "...KKK....KKK...",
        "..KGGGK..KGGGK..",
        "...KKK....KKK...",
        "...KK......KK...",
        "..KKKKKKKKKKKK..",
        ".KGGGGKKKKGGGGK.",
        ".KGGGKRRYRKGGGK.",
        ".KGYGKRRRRKGYGK.",
        "..KKKGKKKKGKKK..",
        "....KGK..KGK....",
        "....KK....KK....",
    ]),
    "coin": _pad([
        DOTS, DOTS,
        ".....KKKKKK.....",
        "...KKYYYYYYKK...",
        "..KYYBBYYBBYYK..",
        "..KYBBBYYBBBYK..",
        ".KYBYYYYYYYYBYK.",
        ".KYBBYYYYYYBBYK.",
        ".KYBBBYYYYBBBYK.",
        ".KYBBYYBBYYBBYK.",
        "..KYBYBBBBYBYK..",
        "..KYYBBBBBBYYK..",
        "...KKYYYYYYKK...",
        ".....KKKKKK.....",
    ]),
    "checkpoint": [
        DOTS,
        ".....KKKKKK.....",
        "...KKYYYYYYKK...",
        "..KYYYYBBYYYYK..",
        "..KYYBBBBBBYYK..",
        "..KYYYBBBBYYYK..",
        "..KYYYBYYBYYYK..",
        "...KKYYYYYYKK...",
        "..KGKKKKKKKKGK..",
        "..KGGGGGGGGGGK..",
        "...KKKKGGKKKK...",
        "......KGGK......",
        "......KGGK......",
        ".....KGGGGK.....",
        "....KGGGGGGK....",
        "....KKKKKKKK....",
    ],
    "flag": [
        "...KK...........",
        "..KYYK..........",
        "..KKKKKKKKKKKKK.",
        "...KGKBBBBBBBBBK",
        "...KGKBBBYYBBBK.",
        "...KGKBYYYYYYBK.",
        "...KGKBBYYYYBBBK",
        "...KGKBBYBBYBBK.",
        "...KGKBBBBBBBBK.",
        "...KGKKKKKKKKKKK",
        "...KGK..........",
        "...KGK..........",
        "...KGK..........",
        "..KKGKK.........",
        ".KGGGGGK........",
        ".KKKKKKK........",
    ],
    "ground": [
        "YYYYYYYYYYYYYYYY",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGKGGGGGGGK",
        "KKKKKKKKKKKKKKKK",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "KKKKKKKKKKKKKKKK",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    "ground_inner": [
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "KKKKKKKKKKKKKKKK",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "KKKKKKKKKKKKKKKK",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    "platform": _pad([
        "GGGGGGGGGGGGGGGG",
        "YYKKYYKKYYKKYYKK",
        "YKKYYKKYYKKYYKKY",
        "KKYYKKYYKKYYKKYY",
        "KKKKKKKKKKKKKKKK",
    ]),
    "cloud_small": _pad([
        DOTS, DOTS, DOTS, DOTS,
        ".....KKK........",
        "....KRRRK.KKK...",
        "..KKRRRRRKRRRK..",
        ".KRRRRRRRRRRRRK.",
        ".KRRRRRRRRRRRRK.",
        "..KKYYYYYYYYKK..",
        "....KKKKKKKK....",
    ]),
    "cloud_big": _pad([
        "." * 32, "." * 32, "." * 32,
        "..........KKKKKKKKKKKK..........",
        ".......KKKGGGGGGGGGGGGKKK.......",
        "..KK..KGGGGGGGGGGGGGGGGGGKK.....",
        ".KRRKKGGGGGGGGGGGGGGGGGGGGGK....",
        ".KRRRKGGGGGGGGGGGGGGGGGGGGGGK...",
        "..KRRKYYYYYYYYYYYYYYYYYYYYYYK...",
        ".KRRRKGGGGGGGGGGGGGGGGGGGGGGK...",
        ".KRRKKGGGGGGGGGGGGGGGGGGGGGK....",
        "..KK..KGGGGGGGGGGGGGGGGGGKK.....",
        ".......KKKGGGGGGGGGGGGKKK.......",
        "..........KKKKKKKKKKKK..........",
        ".............KYGYGYK............",
        ".............KKKKKKK............",
    ], w=32),
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KBYRG."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import superheroes8
        superheroes8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
