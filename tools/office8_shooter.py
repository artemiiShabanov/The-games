#!/usr/bin/env python3
"""8-bit «Офис», шутер сверху (#137, #56): зеркало раздела «Шутер × 8-bit» в
`pixel_sprites.py` (`SHOOTER`) и модуля космоса `space8_shooter.py`, те же слоты и размеры
16×16. Палитра `office8.PALETTE`: K чёрный (костюмы, волосы, обводка), W рубашка и бумага,
B ковролин, шкафы и стекло, R галстук, степлер и всё опасное, Y кожа, стикеры и столешница.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (9 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

Состав: клерк со степлером, сотрудник в чёрном костюме с усами и папкой, скрепка героя и
красная канцелярская кнопка врага, стакан кофе вместо аптечки, ковролин плитками, вдоль стены
столешница под окном с ночным городом, красная ковровая дорожка в дверях, кулер, сейф и копир,
стреляющий бумагой, разлетевшиеся листы вместо вспышки.

    python3 tools/office8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Клерк сверху, лицом вправо: тёмная макушка с синим отливом, лоб и нос вперёд, под подбородком
# красный галстук, белые плечи рубашки сверху и снизу кадра, спина рубашки сзади, кисти цвета
# кожи. В правой руке (внизу кадра) красный степлер с белой скобой, носиком вперёд.
HERO_E = [
    "................",
    "................",
    "....KKKKKK......",
    "...KWWWWWYK.....",
    "...KWWWWWYK.....",
    "..KKKKKKKKK.....",
    ".KWKKBBKYYWK....",
    ".KWKBKKKYYYRK...",
    ".KWKBKKKYYYRK...",
    ".KWKKKKKYYWKKKKK",
    "..KKKKKKKKKRRRRK",
    "...KWWWWWYYKWWWK",
    "...KWWWWWKKKKKK.",
    "....KKKKK.......",
    "................",
    "................",
]

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Сотрудник в чёрном костюме: зачёс, усы полосой шире лица, белая рубашка клином между синих
    # лацканов, жёлтая папка под мышкой, степлер вправо; кадр 1 со вспышкой скобы, рука
    # отдёрнута отдачей, ноги вместе.
    "shoot_gunner_0": [
        "................",
        ".....KKKKKK.....",
        "....KKKKKKKK....",
        "....KKYYYYKK....",
        "....KYKYYKYK....",
        "....KYYYYYYK....",
        "...KKKKKKKKKK...",
        ".....KYYYYK.....",
        "...KKKBWWBKKK...",
        "..KKKKKBWBKKKK..",
        ".KYYYKKBKBKKYRRK",
        ".KYWYKKKKKKKKWWK",
        ".KYYYKKKKKKK.KK.",
        "..KKKKBKKBKK....",
        "....KKBK.KBKK...",
        "....KKKK.KKKK...",
    ],
    "shoot_gunner_1": [
        "................",
        ".....KKKKKK.....",
        "....KKKKKKKK....",
        "....KKYYYYKK....",
        "....KYKYYKYK....",
        "....KYYYYYYK....",
        "...KKKKKKKKKK...",
        ".....KYYYYK.....",
        "...KKKBWWBKKK...",
        "..KKKKKBWBKKK.Y.",
        ".KYYYKKBKBKYRRWY",
        ".KYWYKKKKKKKWWY.",
        ".KYYYKKKKKKK....",
        "..KKKKBKKBKK....",
        ".....KKBBKK.....",
        ".....KKKKKK.....",
    ],
    # Выстрел героя: белая скрепка, проволока завитком.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "....KKKKKKKK....",
        "....KWWWWWWK....",
        "....KWKKKKWK....",
        "....KWKWWWWK....",
        "....KWKKKKKK....",
        "....KWWWWWK.....",
        "....KKKKKKK.....",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд сотрудника: красная канцелярская кнопка шляпкой к зрителю, блик и остриё в центре,
    # заметно крупнее скрепки героя.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KRRRRK.....",
        "....KRWWRRRK....",
        "....KRWRKKRK....",
        "....KRRKKRRK....",
        "....KRRRRRRK....",
        ".....KRRRRK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Аптечка: стакан кофе с крышкой, картонный пояс с красной меткой, пар над крышкой.
    "shoot_rum": [
        ".......W........",
        "......W..W......",
        ".......W.W......",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KKKKKKKKKK...",
        "....KWWWWWWK....",
        "....KYYYYYYK....",
        "....KYYRRYYK....",
        "....KYYRRYYK....",
        "....KYYYYYYK....",
        ".....KWWWWK.....",
        ".....KWWWWK.....",
        ".....KKKKKK.....",
        "................",
        "................",
    ],
    # Ковролин плитками: ряды по 8 пикселей, стыки вразбежку; второй тайл с оброненным
    # стикером и листком, демка кладёт его редко.
    "shoot_deck": [
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBYYYYBBBBBBBBK",
        "BBBYYYYBBBBBBBBK",
        "BBBYYYKBBBBBBBBK",
        "BBBYYKKBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBWWWWBB",
        "BBBBBBBKBBWKKWBB",
        "BBBBBBBKBBWWWWBB",
        "BBBBBBBKBBWKWWBB",
        "BBBBBBBKBBWWWWBB",
        "BBBBBBBKBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
    ],
    # Стена опенспейса: снаружи (сверху) ночной город за окном, огни окон вразброс и синяя
    # кромка стекла; к ковролину белый подоконник и столешница с листком и красной ручкой.
    # Угол: столешница по нижней и правой кромке.
    "shoot_rail": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKYKKKKKKKKK",
        "KKKKKKYKKKKKKBKK",
        "KKYKKKKKKKKKKKKK",
        "KKKKKKKKKKYYKKKK",
        "KKKKKKKKKKKKKKKK",
        "KBBKKKKKKKKKKYKK",
        "KKKKKKYKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBBBBBBBBBB",
        "WWWWWWWWWWWWWWWW",
        "YYYYYYYYYYYYYYYY",
        "YYWWWKYYYYYRRKYY",
        "YYWWWKYYYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKYKKKKKKKKK",
        "KKKKKKYKKKKKKKKK",
        "KKYKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KBBKKKKKKKKKKKKK",
        "KKKKKKYKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKBBBBBBB",
        "KKKKKKKKKBWWWWWW",
        "KKKKKKKKKBWYYYYY",
        "KKKKKKKKKBWYWWKY",
        "KKKKKKKKKBWYWWKY",
        "KKKKKKKKKBWYYYYY",
        "KKKKKKKKKBWYYYYK",
    ],
    # Дверной проём: красная ковровая дорожка с жёлтой каймой и ромбами поперёк стены, по ней
    # сотрудники заходят в отдел.
    "shoot_plank": [
        "KKKKYRRRRRRYKKKK",
        "KKKKYRRRRRRYKKKK",
        "KYKKYRRYYRRYKKKK",
        "KKKKYRYRRYRYKKBK",
        "KKKKYRRYYRRYKKKK",
        "KKKKYRRRRRRYKKKK",
        "KKKKYRRRRRRYKYKK",
        "KKKKYRRRRRRYKKKK",
        "KKKKYRRYYRRYKKKK",
        "BBBKYRYRRYRYKBBB",
        "WWWKYRRYYRRYKWWW",
        "YYYKYRRRRRRYKYYY",
        "YYYKYRRRRRRYKYYY",
        "YYYKYRRRRRRYKYYY",
        "YYYKYRRYYRRYKYYY",
        "KKKKYRYRRYRYKKKK",
    ],
    # Пропы отдела: кулер (синяя бутыль горлом вниз на белой тумбе, красный и синий краники над поддоном),
    # сейф (белый корпус, синяя дверца, жёлтый лимб замка, ручка), копир, стреляющий бумагой
    # (лист вылетает вверх из щели, красная кнопка, синяя тумба с лотком), разлетевшиеся листы
    # и стикеры от поверженного сотрудника.
    "shoot_barrel": [
        "......KKKK......",
        ".....KBBBBK.....",
        ".....KBWBBK.....",
        ".....KBWBBK.....",
        ".....KBBBBK.....",
        ".....KBBBBK.....",
        "......KBBK......",
        "....KKKKKKKK....",
        "....KWWWWWWK....",
        "....KWRWWBWK....",
        "....KWKWWKWK....",
        "....KKKKKKKK....",
        "....KWWWWWWK....",
        "....KWWYYWWK....",
        "....KKKKKKKK....",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        "..KWWWWWWWWWWK..",
        "..KWKKKKKKKKWK..",
        "..KWKBBBBBBKWK..",
        "..KWKBBYYBBKWK..",
        "..KWKBYKKYBKWK..",
        "..KWKBYKKYBKWK..",
        "..KWKBBYYBBKWK..",
        "..KWKBBBBWWKWK..",
        "..KWKKKKKKKKWK..",
        "..KWWWWWWWWWWK..",
        "..KKKKKKKKKKKK..",
        "..KK........KK..",
        "................",
    ],
    "shoot_cannon": [
        "................",
        ".....KKKKKK.....",
        ".....KWWWWK.....",
        ".....KWKKWK.....",
        ".....KWWWWK.....",
        "..KKKKWKKWKKKK..",
        "..KWWKKKKKKWWK..",
        "..KWBBWWWWWWRK..",
        "..KWWWWWWWWWWK..",
        "..KKKKKKKKKKKK..",
        "..KBBBBBBBBBBK..",
        "..KBBWWWWWWBBK..",
        "..KBBBBBBBBBBK..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    "shoot_puff": [
        "................",
        "..KKK.....Y.....",
        ".KWWWK...KKKK...",
        ".KWKWK..KWWWWK..",
        "..KWWWK.KWKKWK..",
        "...KKK..KWWWWK..",
        ".Y...KKK.KKKK...",
        "....KWWWK.....Y.",
        "...KWKKWK..KK...",
        "...KWWWWK.KYYK..",
        "....KKKK..KYYK..",
        ".KKK.......KK...",
        "KWWWK..KKKK.....",
        "KWKWK.KWWWWK.Y..",
        ".KKK..KWKKWK....",
        ".......KKKK.....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KWBRY."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import office8
        office8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
