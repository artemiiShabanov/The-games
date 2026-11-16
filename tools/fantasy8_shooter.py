#!/usr/bin/env python3
"""8-bit «Фэнтези», шутер сверху (#137, #56): зеркало `space8_shooter.py` и раздела «Шутер ×
8-bit» в `pixel_sprites.py` (`SHOOTER`), те же слоты и размеры 16×16. Палитра `fantasy8.PALETTE`:
K чёрный, B мантия и рунный камень, G гоблины, слизь и мох, Y золото и дерево, W свет.
Поляна на летающем острове: рунные плиты, по краю корень во мху, за краем облака в сумерках.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (9 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

    python3 tools/fantasy8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Маг сверху, лицом вправо: шляпа диском с золотой лентой по тулье, колпак загнут назад и
# кончается золотой кисточкой, из-под полей впереди видно лицо, по бокам плечи мантии с золотой
# каймой; в правой руке (внизу кадра) волшебная палочка со светящимся концом, направлена вперёд.
HERO_E = [
    "................",
    "................",
    ".....KKKKK......",
    "....KBBYBBK.....",
    "....KKKKKKK.....",
    "...KBBYYYBBK....",
    ".KKBBYBBBYBBWK..",
    "KYBBBYBBBYBBWWK.",
    "KYBBBYBBBYBBWWK.",
    ".KKBBYBBBYBBWK..",
    "...KBBYYYBBK....",
    "....KKKKKKKKKKK.",
    "....KBBYBBWYYYWK",
    ".....KKKKKKKKKK.",
    "................",
    "................",
]

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Гоблин-плевака: широкая голова с острыми ушами в стороны, белые глаза и зубы, жилет из
    # кожи, в правой руке кривая палочка; кадр 1 со вспышкой слизи на конце и ногами вместе.
    "shoot_gunner_0": [
        "................",
        "....KKKKKKK.....",
        "KK.KGGGGGGGK.KK.",
        "KGKGGGGGGGGGKGK.",
        "KGGGWWGGGWWGGGK.",
        ".KGGWKGGGKWGGK..",
        "..KGGGGGGGGGK...",
        "...KGWKWKWGK....",
        "....KKKKKKK.....",
        "...KYYYYYYYK....",
        "..KGYYKYKYYGKK..",
        "..KGKYYYYYKGYYWK",
        "..KK.KYYYK.KKKK.",
        ".....KGKGK......",
        "....KGK.KGK.....",
        "....KKK.KKK.....",
    ],
    "shoot_gunner_1": [
        "................",
        "....KKKKKKK.....",
        "KK.KGGGGGGGK.KK.",
        "KGKGGGGGGGGGKGK.",
        "KGGGWWGGGWWGGGK.",
        ".KGGWKGGGKWGGK..",
        "..KGGGGGGGGGK...",
        "...KGWKWKWGK....",
        "....KKKKKKK.....",
        "...KYYYYYYYK..G.",
        "..KGYYKYKYYGKKWG",
        "..KGKYYYYYKGYWWW",
        "..KK.KYYYK.KKKWG",
        ".....KGGGK....G.",
        "......KGGK......",
        "......KKKK......",
    ],
    # Выстрел героя: огненный шар, золотое пламя с белым ядром и искрами вокруг.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        ".......KK.......",
        "....Y.KYYK......",
        ".....KYWWYK.Y...",
        ".....KYWWYK.....",
        "...Y..KYYK......",
        ".......KK.......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд гоблина: ком зелёной слизи с белым бликом и каплей, заметно крупнее огненного шара.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KGGGGK.....",
        "....KGWWGGGK....",
        "....KGWGGGGK....",
        "....KGGGGGGK....",
        "....KGGGGGGK....",
        ".....KGGGGK.....",
        "......KGGK......",
        ".......KK.......",
        "................",
        ".......G........",
        "................",
        "................",
    ],
    # Аптечка: зелье маны, круглая колба с синим настоем, узкое горло под золотой пробкой.
    "shoot_rum": [
        "................",
        "................",
        "......KKKK......",
        "......KYYK......",
        "......KKKK......",
        "......KWWK......",
        ".....KKWWKK.....",
        "....KWWWWWWK....",
        "...KWBBBBBBWK...",
        "...KBBWBBBBBK...",
        "...KBWBBBBBBK...",
        "...KBBBBBBBBK...",
        "...KBBBBBBBBK...",
        "....KBBBBBBK....",
        ".....KKKKKK.....",
        "................",
    ],
    # Пол поляны: рунные плиты в два ряда со сдвигом швов; второй тайл с золотой руной,
    # кочкой мха и трещиной, демка кладёт его редко.
    "shoot_deck": [
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "BBBBBBBKBBBBBBBB",
        "BBYBBBBKBBBBBBBB",
        "BYBYBBBKBBBBGBBB",
        "BBYBBBBKBBBGGGBB",
        "BBYYBBBKBBBBGBBB",
        "BBYBBBBKBBBBBBBB",
        "BBBBBBBKBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBKBBBBBBK",
        "BBBBBBBKBBBBBBBK",
        "BBBBBBBBKKBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBK",
        "KKKKKKKKKKKKKKKK",
    ],
    # Край острова: снаружи (сверху) пустота с облаками и звездой, к поляне полоса мха и
    # корень-брус с сучками. Угол: корень по нижней и правой кромке.
    "shoot_rail": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKWWKKKK",
        "KKKKKKKKBWWWWBKK",
        "KKKKKKKKKKKKKKKK",
        "KKWKKKKKKKKKKKKK",
        "KBWWBKKKKKKKKKKK",
        "KKKKKKKKKKKKYKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGG",
        "YGYYYYYGGYYYYGYY",
        "YYKYYYYYYYYYKYYY",
        "YYYYYYKKYYYYYYYY",
        "YYYYYYYYYYYYYYYY",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKWWKKKKKKKKK",
        "KKKBWWWWBKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKYKKK",
        "KKKKKKKKKKKKKKKK",
        "KKWKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKGGGGGG",
        "KKKKKKKKKKGYGYYY",
        "KKKKKKKKKKGYKYYY",
        "KKKKKKKKKKGYYYYY",
        "KKKKKKKKKKGGYYYY",
        "KKKKKKKKKKGYYYYK",
    ],
    # Подвесной мостик: дощечки поперёк хода на белых канатах, по нему гоблины заходят на поляну.
    "shoot_plank": [
        "KKKWYYYYYYYYWKKK",
        "KKKWYYYYYYYYWKKK",
        "KKKWKKKKKKKKWKKK",
        "KKKWYYYYYYYYWKBK",
        "KKKWYYYKYYYYWKKK",
        "KWKWKKKKKKKKWKKK",
        "KKKWYYYYYYYYWKKK",
        "KKKWYYYYYYYYWKKK",
        "KKKWKKKKKKKKWKKK",
        "KKKWYYYYYYYYWKKK",
        "GGKWYYYYKYYYWKGG",
        "YYKWKKKKKKKKWKYY",
        "YYKWYYYYYYYYWKYY",
        "KYKWYYYYYYYYWKYK",
        "YYKWKKKKKKKKWKYY",
        "KKKWYYYYYYYYWKKK",
    ],
    # Пропы поляны: пень (вид сверху, годовые кольца, мох с краю, корни внизу), сундук-мимик
    # с глазами на крышке и зубастой пастью, кристалл на треноге (остриё вверх), вспышка чар
    # от поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        ".....KKKKKK.....",
        "...KKYYYYYYKK...",
        "..KGYYYYYYYYYK..",
        "..KGYYKKKKYYYK..",
        ".KGGYKYYYYKYYYK.",
        ".KGYYKYKKYKYYYK.",
        ".KYYYKYKKYKYYYK.",
        ".KYYYKYYYYKYYGK.",
        "..KYYYKKKKYYGK..",
        "..KYYYYYYYYYGK..",
        "..KKKYYYYYYKKK..",
        ".KYK.KKKKKK.KYK.",
        ".KK..........KK.",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        "................",
        "...KKKKKKKKKK...",
        "..KYYYYYYYYYYK..",
        ".KYYWWYYYYWWYYK.",
        ".KYYWKYYYYKWYYK.",
        ".KBBBBBBBBBBBBK.",
        ".KWKWKWKWKWKWKK.",
        ".KKKKKKYYKKKKKK.",
        ".KKWKWKYYKWKWKK.",
        ".KBBBBBBBBBBBBK.",
        ".KYYYYBYYBYYYYK.",
        ".KYYYYBYYBYYYYK.",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    "shoot_cannon": [
        "................",
        ".......KK.......",
        "......KWWK...Y..",
        ".....KWWBBK.....",
        ".....KWBBBK.....",
        "..W..KWBBBK.....",
        ".....KBBBBK.....",
        "......KBBK......",
        "....KKKYYKKK....",
        "...KYYYYYYYYK...",
        "....KYKYYKYK....",
        "...KYKKYYKKYK...",
        "..KYK.KYYK.KYK..",
        ".KYK..KYYK..KYK.",
        ".KKK..KKKK..KKK.",
        "................",
    ],
    "shoot_puff": [
        "................",
        ".......K........",
        "......KYK...Y...",
        "..Y...KYK.......",
        "...KKKYWYKKK....",
        "...KYYWWWYYK....",
        ".KKKYWWWWWYKKK..",
        "KYYYWWWKWWWYYYK.",
        ".KKKYWWWWWYKKK..",
        "...KYYWWWYYK....",
        "...KKKYWYKKK....",
        "......KYK....Y..",
        ".Y....KYK.......",
        ".......K........",
        "................",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KBGYW."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import fantasy8
        fantasy8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
