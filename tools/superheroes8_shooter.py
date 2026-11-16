#!/usr/bin/env python3
"""8-bit «Супергерои», шутер сверху (#137, #56): зеркало раздела «Шутер × 8-bit» в
`pixel_sprites.py` (`SHOOTER`) и модуля `space8_shooter.py`, те же слоты и размеры 16×16.
Палитра `superheroes8.PALETTE`: K чёрный, B синее трико, Y жёлтое (плащ, перчатки, энергия,
огни), R красное (глаз робота, кирпич, опасность), G зелёно-серое (роботы, бетон, металл).
Место действия это крыша небоскрёба: бетонные плиты, кирпичный парапет, за ним огни улиц
далеко внизу.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (10 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

    python3 tools/superheroes8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Герой сверху, лицом вправо: чёрная макушка с хохолком, жёлтое лицо вперёд, синие плечи трико
# сверху и снизу, жёлтый плащ веером за спиной, перчатка-бластер в правой руке (внизу кадра)
# с красным зарядом на конце.
HERO_E = [
    "................",
    "................",
    ".....KKKKK......",
    "..KKKBBBBBK.....",
    ".KYYKBBBBBK.....",
    "KYYYYKKKKKKK....",
    "KYYYYKKKKYYK....",
    "KYYYYKKKKYYYK...",
    "KYYYYKKKKYYYK...",
    "KYYYYKKKKYYK....",
    "KYYYYKKKKKKKKKKK",
    ".KYYKBBBBBKYYRRK",
    "..KKKBBBBBKKKKKK",
    ".....KKKKK......",
    "................",
    "................",
]

# Борт крыши: снаружи (сверху) ночные улицы с огнями далеко внизу, к крыше бетонная крышка
# парапета и кирпичная кладка в два ряда вперевязку.
_RAIL = [
    "KKKKKKKKKKKKKKKK",
    "KKKYKKKKKKKKKKKK",
    "KKKYKKKKKKKBKKKK",
    "KKKKKKKKKKKKKKKK",
    "KKKKKKKKYKKKKKKK",
    "KKKKKKKKKKKKKYKK",
    "KRKKKKKKKKKKKYKK",
    "KKKKKKYKKKKKKKKK",
    "KKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGGGGGG",
    "RRRKRRRRRRRKRRRR",
    "RRRKRRRRRRRKRRRR",
    "KKKKKKKKKKKKKKKK",
    "RRRRRRRKRRRRRRRK",
    "KKKKKKKKKKKKKKKK",
]


def _plank():
    """Стальная балка поперёк борта: полки по краям, посередине жёлто-чёрная разметка."""
    out = []
    for y, row in enumerate(_RAIL):
        beam = "KGK" + "".join("Y" if (x + y) % 4 < 2 else "K" for x in range(4)) + "KGK"
        if y % 4 == 1:
            beam = "KKK" + beam[3:7] + "KKK"  # заклёпки на полках
        out.append(row[:3] + beam + row[13:])
    return out


SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Робот-приспешник: квадратная голова с антенной и одним красным глазом в тёмном забрале,
    # жёлтый огонь на груди, слева клешня, справа рука-пушка; кадр 1 со вспышкой и ногами вместе.
    "shoot_gunner_0": [
        ".......KK.......",
        "......KYYK......",
        "....KKKKKKKK....",
        "...KGGGGGGGGK...",
        "...KGKKKKKKGK...",
        "...KGKKRRKKGK...",
        "...KGKKRRKKGK...",
        "...KGGGGGGGGK...",
        "....KKKKKKKK....",
        "..KKKGGYYGGKKK..",
        ".KGGKGGYYGGKGKKK",
        ".KGKKGGGGGGKGGRK",
        "KGKGKGGGGGGKKKKK",
        "KKKKKGGKKGGK....",
        "....KGK..KGK....",
        "....KKK..KKK....",
    ],
    "shoot_gunner_1": [
        ".......KK.......",
        "......KYYK......",
        "....KKKKKKKK....",
        "...KGGGGGGGGK...",
        "...KGKKKKKKGK...",
        "...KGKKRRKKGK...",
        "...KGKKRRKKGK...",
        "...KGGGGGGGGK...",
        "....KKKKKKKK....",
        "..KKKGGYYGGKKKR.",
        ".KGGKGGYYGGKGKYR",
        ".KGKKGGGGGGKGKYY",
        "KGKGKGGGGGGKKKYR",
        "KKKKKKGGGGKK..R.",
        ".....KGGGGK.....",
        ".....KKKKKK.....",
    ],
    # Выстрел героя: жёлтый энергозаряд в синем ореоле.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KBYYBK.....",
        ".....KYYYYK.....",
        ".....KYYYYK.....",
        ".....KBYYBK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд робота: красный сгусток с жёлтой искрой, заметно крупнее выстрела героя.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KRRRRK.....",
        "....KRRYYRRK....",
        "....KRYYRRRK....",
        "....KRRRRRRK....",
        "....KRRRRRRK....",
        ".....KRRRRK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Аптечка: энергоколба с жёлтой пробкой, стеклянным горлом и синим зарядом с искрами.
    "shoot_rum": [
        "................",
        "......KKKK......",
        "......KYYK......",
        "......KKKK......",
        "......KGGK......",
        "......KGGK......",
        ".....KKGGKK.....",
        "....KGGGGGGK....",
        "...KGBBBBBBGK...",
        "...KBBYBBBBBK...",
        "...KBYYBBBBBK...",
        "...KBBBBBBBBK...",
        "...KBBBBBYBBK...",
        "....KBBBBBBK....",
        ".....KKKKKK.....",
        "................",
    ],
    # Крыша: бетонные плиты в два ряда со стыками вперевязку; второй тайл с вентиляционной
    # решёткой и трещиной, демка кладёт его редко.
    "shoot_deck": [
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGKGGGGGGGGGGGG",
        "GGGKGGGGGGGGGGGG",
        "GGGKGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGKGGGG",
        "GGGGGGGGGGGKGGGG",
        "GGGGGGGGGGGKGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGKGGGGG",
        "GGGGGGGGGGGKGGGG",
        "GGGGGGGGGGKGGGGG",
        "GGGKGGGGGGGKKGGG",
        "GGGKGGGGGGGGGGGG",
        "GGGKGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGG",
        "GGKKKKKKKGGGGGGG",
        "GGKGKGKGKGGGGGGG",
        "GGKGKGKGKGGGGGGG",
        "GGKGKGKGKGGKGGGG",
        "GGKKKKKKKGGKGGGG",
        "GGGGGGGGGGGKGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail": _RAIL,
    # Угол парапета: бетонная крышка по верхней и левой кромке бруса, кирпич внутри.
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKKYKKKKKKKKKKKK",
        "KKKYKKKKKKKBKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKYKKKKKKK",
        "KKKKKKKKKKKKKYKK",
        "KRKKKKKKKKKKKYKK",
        "KKKKKKYKKKKKKKKK",
        "KKKYKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKGGGGGG",
        "KKKKKKKKKKGRRKRR",
        "KKKKKKKKKKGRRKRR",
        "KKKKKKKKKKGKKKKK",
        "KKKKKKKKKKGRRRRK",
        "KKKKKKKKKKGKKKKK",
    ],
    # Мостик: стальная балка в полосах ограждения, по ней роботы заходят на крышу.
    "shoot_plank": _plank(),
    # Пропы крыши: водяной бак (вид сверху, клёпаная крыша клином и жёлтый люк в центре),
    # бронированный кейс с ручкой, замками и красной эмблемой, лучевая пушка на треноге
    # (излучатель с раскалённой линзой вверх, жёлтые витки катушки на стволе), комиксная вспышка-звезда от
    # поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        ".....KKKKKK.....",
        "...KKGGKKGGKK...",
        "..KGGGGKKGGGGK..",
        "..KGKGGGGGGKGK..",
        ".KGGGKGKKGKGGGK.",
        ".KKKGGKYYKGGKKK.",
        ".KKKGGKYYKGGKKK.",
        ".KGGGKGKKGKGGGK.",
        "..KGKGGGGGGKGK..",
        "..KGGGGKKGGGGK..",
        "...KKGGKKGGKK...",
        ".....KKKKKK.....",
        "................",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        ".....KKKKKK.....",
        ".....KGGGGK.....",
        ".....KGKKGK.....",
        ".KKKKKKKKKKKKKK.",
        ".KKGGGGGGGGGGKK.",
        ".KGGGGGGGGGGGGK.",
        ".KGYYGGKKGGYYGK.",
        ".KKKKKKRRKKKKKK.",
        ".KGGGGKRRKGGGGK.",
        ".KGGGGGKKGGGGGK.",
        ".KGGGGGGGGGGGGK.",
        ".KKGGGGGGGGGGKK.",
        ".KKKKKKKKKKKKKK.",
        "................",
    ],
    "shoot_cannon": [
        "......KKKK......",
        ".....KRYYRK.....",
        ".....KRYYRK.....",
        "....KKKKKKKK....",
        "....KGGGGGGK....",
        ".....KYYYYK.....",
        ".....KGGGGK.....",
        ".....KYYYYK.....",
        ".....KGGGGK.....",
        "..KKKKKKKKKKKK..",
        ".KGGGGKBBKGGGGK.",
        ".KGKGGKBBKGGKGK.",
        ".KGGGGGGGGGGGGK.",
        ".KKKKKKKKKKKKKK.",
        "..KGK......KGK..",
        "..KKK......KKK..",
    ],
    "shoot_puff": [
        ".......K........",
        "..K...KRK...K...",
        ".KRK..KRK..KRK..",
        ".KRRKKRYRKKRRK..",
        "..KRRRYYYRRRK...",
        "..KRYYYYYYYRK...",
        ".KKRYYYKYYYRRKK.",
        "KRRYYYYYYYYYYRRK",
        ".KKRYYYYYKYYRKK.",
        "..KRYYKYYYYRK...",
        "..KRRYYYYYRRK...",
        ".KRRKRRYRRKRRK..",
        ".KRK.KRYRK.KRK..",
        "..K...KRK...K...",
        ".......K........",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KBYRG."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import superheroes8
        superheroes8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
