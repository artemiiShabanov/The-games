#!/usr/bin/env python3
"""8-bit «Сладости», шутер сверху (#137, #56): зеркало `space8_shooter.py` и раздела
«Шутер × 8-bit» в `pixel_sprites.py` (`SHOOTER`), те же слоты и размеры 16×16. Палитра
`sweets8.PALETTE`: K чёрный (горький шоколад), W глазурь и сахар, G пряник и печенье,
R мармелад и бант, P розовая глазурь и сироп.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (9 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

Состав: пряничный человечек с кондитерским шприцем, мармеладный мишка с кремовым мешком,
драже героя и капля желе врага, бутылочка сиропа, пол из печенья, борт над розовым сиропом,
вафельный мостик, желе на блюдце, коробка с бантом, пушка с попкорном, хлопок попкорна.

    python3 tools/sweets8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Пряничный человечек сверху, лицом вправо: круглая голова с глазами и белой улыбкой глазурью
# вперёд, красный бант сзади, плечи с белыми манжетами сверху и снизу, кондитерский шприц в
# правой руке (внизу кадра): белый корпус, розовый крем на носике.
HERO_E = [
    "................",
    "................",
    "....KKKKK.......",
    "...KGGGGGK......",
    "...KGGWGGK......",
    "..KKGKKKKKK.....",
    ".KRKKGGGGKGK....",
    ".KRRKGWGGGWK....",
    ".KRRKGWGGGWK....",
    ".KRKKGGGGKGKKKKK",
    "..KKGKKKKKKWWPPK",
    "...KGGWGGKKKKKK.",
    "...KGGGGGK......",
    "....KKKKK.......",
    "................",
    "................",
]

# Розовый сироп за бортом: гладь с белыми бликами, 9 строк.
_SYRUP = [
    "PPPPPPPPPPPPPPPP",
    "PPPPPWWPPPPPPPPP",
    "PPPPPPPPPPPPPPPP",
    "PPPPPPPPPPPPWWPP",
    "PPPPPPPPPPPPPPPP",
    "PWWPPPPPPPPPPPPP",
    "PPPPPPPPWWPPPPPP",
    "PPPPPPPPPPPPPPPP",
    "PPPPPPPPPPPPPPPP",
]
# Вафля мостика, 8 пикселей поперёк: ямки 2×2 с шагом 4.
_WAFER = ["GGGGGGGG", "GKKGGKKG", "GKKGGKKG", "GGGGGGGG"] * 4

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Мармеладный мишка-стрелок: круглые уши, блик желе на лбу, розовая мордочка и пузо,
    # кремовый мешок с розовым носиком вправо; кадр 1 с брызгом крема и лапами вместе.
    "shoot_gunner_0": [
        "..KK........KK..",
        ".KRRK......KRRK.",
        ".KRRKKKKKKKKRRK.",
        "..KRRRRRRRRRRK..",
        "..KRWWRRRRRRRK..",
        "..KRKKRRRRKKRK..",
        "..KRRRRPPRRRRK..",
        "...KRRPKKPRRK...",
        "....KKKKKKKK....",
        "...KRRPPPPRRK...",
        "..KRRRPPPPRRKKKK",
        "..KRKRPPPPRKWWPK",
        "..KRKRRRRRRKKKK.",
        "...K.KRRRRK.....",
        ".....KR..RK.....",
        ".....KK..KK.....",
    ],
    "shoot_gunner_1": [
        "..KK........KK..",
        ".KRRK......KRRK.",
        ".KRRKKKKKKKKRRK.",
        "..KRRRRRRRRRRK..",
        "..KRWWRRRRRRRK..",
        "..KRKKRRRRKKRK..",
        "..KRRRRPPRRRRK..",
        "...KRRPKKPRRK...",
        "....KKKKKKKK..P.",
        "...KRRPPPPRRKPWP",
        "..KRRRPPPPRRKKKP",
        "..KRKRPPPPRKWWK.",
        "..KRKRRRRRRKKK..",
        "...K.KRRRRK.....",
        "......KRRK......",
        "......KKKK......",
    ],
    # Выстрел героя: розовое драже с белым бликом.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KPPPPK.....",
        ".....KPWWPK.....",
        ".....KPWPPK.....",
        ".....KPPPPK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд мишки: красная капля желе с белым бликом, заметно крупнее выстрела героя.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KRRRRK.....",
        "....KRRWWRRK....",
        "....KRWWRRRK....",
        "....KRRRRRRK....",
        "....KRRRRRRK....",
        ".....KRRRRK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Аптечка: бутылочка сиропа с пряничной пробкой и белой этикеткой с красным сердечком.
    "shoot_rum": [
        "................",
        "......KKKK......",
        "......KGGK......",
        "......KKKK......",
        "......KWPK......",
        ".....KKWPKK.....",
        "....KPPPPPPK....",
        "...KPWPPPPPPK...",
        "...KPWPPPPPPK...",
        "...KKKKKKKKKK...",
        "...KWWRWWRWWK...",
        "...KWWRRRRWWK...",
        "...KWWWRRWWWK...",
        "...KKKKKKKKKK...",
        "...KPPPPPPPPK...",
        "....KKKKKKKK....",
    ],
    # Пол кондитерской: печенье в перевязку, ряды по 8 пикселей, в каждом печенье проколы;
    # второй тайл с лужицей розовой глазури и крошкой сахара, демка кладёт его редко.
    "shoot_deck": [
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGKGGGKGGGKGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGKGGGKGGGKGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGK",
        "GGGGGGGGGGGGGGGK",
        "GGGGGGGKGGGGGGGK",
        "GGGGGGGGGGGGGGGK",
        "GGGGGGGKGGGGGGGK",
        "GGGGGGGGGGGGGGGK",
        "GGGGGGGGGGGGGGGK",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGWGGGG",
        "GGGKGGGKGGGGGGGG",
        "GGGGGGGKGGGGGWGG",
        "GGGKGGGKGGGGGGGG",
        "GGGGGGGKGGWGGGGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGK",
        "GGGPPPPPGGGGGGGK",
        "GGPPWWPPPGGGGGGK",
        "GGPPWPPPPPGGGGGK",
        "GGGPPPPPPGGGGGGK",
        "GGGGPPPGGGGGGGGK",
        "GGGGGGGGGGGGGGGK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Борт: снаружи (сверху) розовый сироп с бликами, к полу кромка белой глазури и пряничный
    # брус с шоколадной крошкой. Угол: брус по нижней и правой кромке.
    "shoot_rail": _SYRUP + [
        "KKKKKKKKKKKKKKKK",
        "WWWWWWWWWWWWWWWW",
        "GGGGGGGGGGGGGGGG",
        "GGKGGGGGGGGGKGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "PPPPPPPPPPPPPPPP",
        "PPPPPWWPPPPPPPPP",
        "PPPPPPPPPPPPPPPP",
        "PPPPPPPPPPPPWWPP",
        "PPPPPPPPPPPPPPPP",
        "PWWPPPPPPPPPPPPP",
        "PPPPPPPPPPPPPPPP",
        "PPPPPWWPPPPPPPPP",
        "PPPPPPPPPPPPPPPP",
        "PPPPPPPPPKKKKKKK",
        "PPPPPPPPPKWWWWWW",
        "PPPPPPPPPKWGGGGG",
        "PWWPPPPPPKWGKGGG",
        "PPPPPPPPPKWGGGGG",
        "PPPPPPPPPKWGGGGG",
        "PPPPPPPPPKWGGGGK",
    ],
    # Вафельный мостик поперёк борта: по нему мишки заходят на пол кондитерской.
    "shoot_plank": [
        left + "K" + _WAFER[y] + "K" + right for y, (left, right) in enumerate(
            [("PPP", "PPP"), ("PWW", "PPP"), ("PPP", "PPP"), ("PPP", "PWW"), ("PPP", "PPP"),
             ("PPP", "PPP"), ("WWP", "PPP"), ("PPP", "WWP"), ("PPP", "PPP"),
             ("KKK", "KKK"), ("WWW", "WWW"), ("GGG", "GGG"), ("GKG", "GKG"), ("GGG", "GGG"),
             ("GGG", "GGG"), ("KKK", "KKK")])
    ],
    # Пропы: розовое желе с вишенкой на белом блюдце (вид сверху), коробка конфет с красным
    # бантом, пушка с попкорном (жерло вверх, полосатое ведёрко, колёса из печенья), хлопок
    # попкорна от поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWWKKKKWWK...",
        "...KWKPPPPKWK...",
        "...KWKPWRRKWK...",
        "...KWKPPRRKWK...",
        "...KWKPPPPKWK...",
        "...KWWKKKKWWK...",
        "....KWWWWWWK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    "shoot_chest": [
        "................",
        "....KK....KK....",
        "...KRRK..KRRK...",
        "...KRRRKKRRRK...",
        ".KKKKRRRRRRKKKK.",
        ".KWWWWKRRKWWWWK.",
        ".KKKKKKRRKKKKKK.",
        ".KPPPPKRRKPPPPK.",
        ".KPWPPKRRKPPWPK.",
        ".KPPPPKRRKPPPPK.",
        ".KPPWPKRRKPWPPK.",
        ".KPPPPKRRKPPPPK.",
        ".KPWPPKRRKPPWPK.",
        ".KPPPPKRRKPPPPK.",
        ".KKKKKKKKKKKKKK.",
        "................",
    ],
    "shoot_cannon": [
        "......KWWK......",
        ".....KWWKWK.....",
        ".....KKKKKK.....",
        ".....KGGGGK.....",
        "......KGGK......",
        "......KGGK......",
        ".....KKGGKK.....",
        "..KKKKKKKKKKKK..",
        "..KRWWRWWRWWRK..",
        "..KRWWRWWRWWRK..",
        "..KRWWRWWRWWRK..",
        "...KRWRWWRWRK...",
        "..KKKKKKKKKKKK..",
        "..KGGK....KGGK..",
        "...KK......KK...",
        "................",
    ],
    "shoot_puff": [
        "................",
        ".......P........",
        "...KKK.KKK...G..",
        "..KWWWKWWWKKK...",
        "..KWWWWWWWWWWK..",
        ".KKWWWPWWWWWWK..",
        "KWWWWWWWWWPWWKK.",
        "KWWPWWWWWWWWWWWK",
        "KWWWWWWWPWWWWWWK",
        ".KWWWWWWWWWWPWK.",
        ".KKWWPWWWWWWWKK.",
        "..KWWWWKWWWWK...",
        "G..KKKK.KKKK....",
        "..........P.....",
        ".....G..........",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KWGRP."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import sweets8
        sweets8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
