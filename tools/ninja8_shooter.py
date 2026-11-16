#!/usr/bin/env python3
"""8-bit «Ниндзя», шутер сверху (#137, #56): зеркало раздела «Шутер × 8-bit» в
`pixel_sprites.py` (`SHOOTER`) и модуля космоса `space8_shooter.py`, те же слоты и размеры
16×16. Палитра `ninja8.PALETTE`: K чёрный, B синий костюм героя, R шарф, лак и чужой клан,
W сталь, бумага и обмотки, Y дерево, солома и золото.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (10 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

    python3 tools/ninja8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Ниндзя сверху, лицом вправо: круглый капюшон с белой прорезью глаз вперёд, за затылком узел и
# два конца красного шарфа вилкой, над плечом золотая рукоять меча наискось, плечи куртки сверху
# и снизу с белыми обмотками запястий, в правой руке (внизу кадра) кунай остриём вперёд.
HERO_E = [
    "................",
    "................",
    "....KKKKK.......",
    "...KBBBBBK......",
    ".Y.KBBWBBK......",
    "..YKBKKKKKK.....",
    "RRKYKBBBBWWK....",
    ".RRRKBBBBKWK....",
    "..RRKBBBBKWK....",
    ".RRKKBBBBWWKKKKK",
    "RR.KBKKKKKKYYWWK",
    "...KBBWBBKKKKKK.",
    "...KBBBBBK......",
    "....KKKKK.......",
    "................",
    "................",
]

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Ниндзя чужого клана: красный капюшон, чёрная маска с белой прорезью и сведёнными бровями,
    # завязки маски торчат вбок, чёрный пояс с золотой пряжкой, в руке справа сюрикен; кадр 1
    # с броском (рука вытянута, золотая вспышка) и ногами вместе.
    "shoot_gunner_0": [
        "................",
        "....KKKKKKKK....",
        "...KRRRRRRRRK.R.",
        "..KRRRRRRRRRRKRR",
        "..KRRKKRRKKRRKR.",
        "..KRWKWWWWKWRK..",
        "..KRKKKKKKKKRK..",
        "..KRRKKKKKKRRK..",
        "...KKRRRRRRKK...",
        "...KRRKRRKRRK...",
        "..KRRRRKKRRRRKW.",
        "..KRKKKYYKKKRWWW",
        "..KRKRRRRRRK.KW.",
        "...K.KRRRRK.....",
        ".....KR..RK.....",
        ".....KK..KK.....",
    ],
    "shoot_gunner_1": [
        "................",
        "....KKKKKKKK....",
        "...KRRRRRRRRK.R.",
        "..KRRRRRRRRRRKRR",
        "..KRRKKRRKKRRKR.",
        "..KRWKWWWWKWRK..",
        "..KRKKKKKKKKRK..",
        "..KRRKKKKKKRRK..",
        "...KKRRRRRRKK.Y.",
        "...KRRKRRKRRKYWY",
        "..KRRRRKKRRRRRWY",
        "..KRKKKYYKKKKKY.",
        "..KRKRRRRRRK....",
        "...K.KRRRRK.....",
        "......KRRK......",
        "......KKKK......",
    ],
    # Выстрел героя: стальной сюрикен крестом, синяя середина.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        ".......KK.......",
        "......KWWK......",
        "....KKKWWKKK....",
        "....KWWBBWWK....",
        "....KWWBBWWK....",
        "....KKKWWKKK....",
        "......KWWK......",
        ".......KK.......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд чужого клана: красный сюрикен косым крестом с белой серединой, заметно крупнее
    # выстрела героя и другой формы.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "...KK......KK...",
        "...KRK....KRK...",
        "...KRRKKKKRRK...",
        "....KRRRRRRK....",
        ".....KRWWRK.....",
        ".....KRWWRK.....",
        "....KRRRRRRK....",
        "...KRRKKKKRRK...",
        "...KRK....KRK...",
        "...KK......KK...",
        "................",
        "................",
        "................",
    ],
    # Аптечка: тыква-горлянка с красной пробкой, перехват красным шнуром с кистью.
    "shoot_rum": [
        "................",
        ".......KK.......",
        "......KRRK......",
        "......KYYK......",
        ".....KYYYYK.....",
        "....KYWYYYYK....",
        "....KYWYYYYK....",
        ".....KYYYYK.....",
        ".....KRRRRKK....",
        "....KYYYYYYKRK..",
        "...KYWYYYYYYKRK.",
        "...KYWYYYYYYKK..",
        "...KYYYYYYYYK...",
        "...KYYYYYYYYK...",
        "....KKKKKKKK....",
        "................",
    ],
    # Настил веранды: доски по 8 пикселей со стыками вразбежку; второй тайл с гвоздями, сучком
    # и упавшим кленовым листом, демка кладёт его редко.
    "shoot_deck": [
        "YYYKYYYYYYYYYYYY",
        "YYYKYYYYYYYYYYYY",
        "YYYKYYYYYYYYYYYY",
        "YYYKYYYYYYYYYYYY",
        "YYYKYYYYYYYYYYYY",
        "YYYKYYYYYYYYYYYY",
        "YYYKYYYYYYYYYYYY",
        "KKKKKKKKKKKKKKKK",
        "YYYYYYYYYYYKYYYY",
        "YYYYYYYYYYYKYYYY",
        "YYYYYYYYYYYKYYYY",
        "YYYYYYYYYYYKYYYY",
        "YYYYYYYYYYYKYYYY",
        "YYYYYYYYYYYKYYYY",
        "YYYYYYYYYYYKYYYY",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "YYYKYYYYYYYYYYYY",
        "YYYKYYYYYYYYYYYY",
        "YYBKBYYYYYYRYYYY",
        "YYYKYYYYYRRRRYYY",
        "YYBKBYYYYYRRRRYY",
        "YYYKYYYYYYRYYKYY",
        "YYYKYYYYYYYYYYYY",
        "KKKKKKKKKKKKKKKK",
        "YYYYYYYYYYYKYYYY",
        "YYYYKKYYYYBKBYYY",
        "YYYKYYKYYYYKYYYY",
        "YYYYKKYYYYYKYYYY",
        "YYYYYYYYYYBKBYYY",
        "YYYYYYYYYYYKYYYY",
        "YYYYYYYYYYYKYYYY",
        "KKKKKKKKKKKKKKKK",
    ],
    # Край веранды: снаружи (сверху) тёмный пруд с рябью и бликом луны, к настилу золотой
    # поручень и красный лаковый брус с накладками. Угол: брус по нижней и правой кромке.
    "shoot_rail": [
        "KKKKKKKKKKKKKKKK",
        "KKBBBKKKKKKKKKKK",
        "KKKKKKKKKKKWKKKK",
        "KKKKKKKKKBBBBKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKBBKKKKKKKKK",
        "KKKKKKKKKKKKKBBK",
        "KKBKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "YYYYYYYYYYYYYYYY",
        "RRRRRRRRRRRRRRRR",
        "RRYRRRRRRRRRYRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKBBBKKKKKKKKKKK",
        "KKKKKKKKKKKWKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKBBKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKBKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKYYYYYY",
        "KKKKKKKKKKYRRRRR",
        "KKKKKKKKKKYRYRRR",
        "KKKKKKKKKKYRRRRR",
        "KKKKKKKKKKYRRRRR",
        "KKKKKKKKKKYRRRRK",
    ],
    # Мостик через пруд: дощатые ступени поперёк хода между красными перилами, по нему чужой
    # клан заходит на веранду.
    "shoot_plank": [
        "KKKKRYYYYYYRKKKK",
        "KKBKRYYYYYYRKKKK",
        "KKKKRYYYYYYRKKKK",
        "KKKKRKKKKKKRKBBK",
        "KKKKRYYYYYYRKKKK",
        "KBBKRYYYYYYRKKKK",
        "KKKKRYYYYYYRKKKK",
        "KKKKRKKKKKKRKKKK",
        "KKKKRYYYYYYRKKWK",
        "KKKKRYYYYYYRKKKK",
        "YYYKRYYYYYYRKYYY",
        "RRRKRKKKKKKRKRRR",
        "RYRKRYYYYYYRKRYR",
        "RRRKRYYYYYYRKRRR",
        "RRRKRYYYYYYRKRRR",
        "KKKKRKKKKKKRKKKK",
    ],
    # Пропы веранды: бочка сакэ в соломе (вид сверху: верёвочная оплётка, бумажная крышка с
    # красным знаком), лаковый ларец (тёмно-синий лак с бликом, золотые уголки, красный шнур
    # поперёк с золотым узлом и кистью), мортира для фейерверка (бамбуковый ствол в красных перехватах
    # жерлом вверх, деревянный лафет с гербом), дымовая завеса от поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KYYKKYYK....",
        "...KYKKKKKKYK...",
        "...KYKWRRWKYK...",
        "...KKKRRRRKKK...",
        "...KKKWRRWKKK...",
        "...KYKRWWRKYK...",
        "...KYKKKKKKYK...",
        "....KYYKKYYK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        ".KYYBBBBBBBBYYK.",
        ".KYBWWBBBBBBBYK.",
        ".KBBWBBBBBBBBBK.",
        ".KBBBBKYYKBBBBK.",
        ".KRRRRYRRYRRRRK.",
        ".KRRRRYRRYRRRRK.",
        ".KBBBBKYYKBBBBK.",
        ".KBBBBBRRBBBBBK.",
        ".KYBBBRRRRBBBYK.",
        ".KYYBBBBBBBBYYK.",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    "shoot_cannon": [
        "................",
        ".....KKKKKK.....",
        "....KYYKKYYK....",
        ".....KYYWYK.....",
        ".....KRRRRK.....",
        ".....KYYWYK.....",
        ".....KYYWYK.....",
        ".....KRRRRK.....",
        "..KKKKYYWYKKKK..",
        "..KYYKKKKKKYYK..",
        ".KBKYYYRRYYYKBK.",
        ".KBKYYRRRRYYKBK.",
        "..KYYYYRRYYYYK..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    "shoot_puff": [
        "................",
        ".....KKK...Y....",
        "...KKWWWKKK.....",
        "..KWWWWWWWWK....",
        "..KWWWBWWWWWKK..",
        ".KKWWWWWWWBWWWK.",
        "KWWWBWWWWWWWWWK.",
        "KWWWWWWWWWWWWBK.",
        "KBWWWWWBWWWWWK..",
        ".KWWWWWWWWWWWWK.",
        ".KBWWWWWWWBWWWK.",
        "..KBBWWWKBBWWK..",
        ".Y.KKKKK.KKKK...",
        "............Y...",
        "................",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KBRWY."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import ninja8
        ninja8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
