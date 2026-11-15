#!/usr/bin/env python3
"""8-bit «Замки», шутер сверху (#136): зеркало раздела «Шутер × 8-bit» в `pixel_sprites.py`
(`SHOOTER`), те же слоты и размеры 16×16. Палитра `castles8.PALETTE`: K чёрный, G камень и
латы, R красный, Y золото и дерево, W блики.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя (болт), `shoot_shot` это снаряд врага (каменное ядро; так в
  демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта (зубчатой стены) «снаружи»
  сверху (9 строк), брус к плитам двора снизу; у угла брус по нижней и правой кромке; демка их
  поворачивает.

    python3 tools/castles8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Рыцарь сверху, лицом вправо: стальной шлем с красным плюмажем вдоль хребта, красный плащ
# сзади, наплечники сверху и снизу, арбалет в правой руке (внизу кадра) стволом вперёд:
# деревянное ложе и поперечная дуга на конце.
HERO_E = [
    "................",
    "................",
    "....KKKKK.......",
    "...KGGGGGK......",
    "...KGGWGGK......",
    "..KKGKKKKKK.....",
    ".KRKKGGGGGGK.YK.",
    ".KRKGGGGGGGGKYK.",
    ".KRKGRRRRRGGKYK.",
    ".KRKGGGGGGGKYYK.",
    "..KKGKKKKKKYYYYK",
    "...KGGWGGKKKKYK.",
    "...KGGGGGK...YK.",
    "....KKKKK....KK.",
    "................",
    "................",
]

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Стражник вражеского замка: красная туника, стальной шлем с носовой пластиной, золотая
    # пряжка, арбалет вправо; кадр 1 со вспышкой выстрела и ногами вместе.
    "shoot_gunner_0": [
        "................",
        "......KKKK......",
        "....KKGGGGKK....",
        "...KGGGGGGGGK...",
        "...KGKKWWKKGK...",
        "...KGKKGGKKGK...",
        "...KGGGGGGGGK...",
        "....KKKGGKKK....",
        "...KRRRRRRRRK...",
        "..KRRRYYYRRRKKK.",
        "..KGKRRRRRRKYYYK",
        "..KGKRRRRRRK.KY.",
        "...K.KRRRRK..KY.",
        ".....KRKKRK.....",
        ".....KGK.KGK....",
        ".....KKK.KKK....",
    ],
    "shoot_gunner_1": [
        "................",
        "......KKKK......",
        "....KKGGGGKK....",
        "...KGGGGGGGGK...",
        "...KGKKWWKKGK...",
        "...KGKKGGKKGK...",
        "...KGGGGGGGGK...",
        "....KKKGGKKK....",
        "...KRRRRRRRRK.Y.",
        "..KRRRYYYRRRKYWY",
        "..KGKRRRRRRKKKY.",
        "..KGKRRRRRRKYYYK",
        "...K.KRRRRK..KY.",
        ".....KRKKRK..KY.",
        "......KGGK......",
        "......KKKK......",
    ],
    # Болт героя: тонкий золотой болт с белым остриём, смотрит вправо (демка вращает сама).
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        ".....K.....K....",
        "....KYKKKKKWK...",
        ".....KYYYYYWWK..",
        "....KRKKKKKWK...",
        ".....K.....K....",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд врага: каменное ядро, заметно крупнее болта и круглое, с бликом и красной искрой.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KGGGGK.....",
        "....KGWWGGGK....",
        "....KGWGGGGK....",
        "....KGGGGGKK....",
        "....KGGGGKRK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Зелье: круглый пузырёк с красной жидкостью, пробка и блик.
    "shoot_rum": [
        "................",
        "................",
        "......KKKK......",
        "......KYYK......",
        ".....KKGGKK.....",
        "......KGGK......",
        "....KKGGGGKK....",
        "...KGRRRRRRGK...",
        "..KGRRWRRRRRGK..",
        "..KGRWRRRRRRGK..",
        "..KGRRRRRRRRGK..",
        "..KGRRRRRRRRGK..",
        "...KGRRRRRRGK...",
        "....KKGGGGKK....",
        ".....KKKKKK.....",
        "................",
    ],
    # Плиты двора: тёмные швы через 8 пикселей, вторая плита с трещиной и мхом-пятном (золотое
    # пятно как лишайник), демка кладёт её редко.
    "shoot_deck": [
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGWKGGGGGGG",
        "GGGGGGGGKGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGWGG",
        "GGGKKGGGGGGGGGGG",
        "GGGGGKKGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    # Зубчатая стена: снаружи (сверху) тёмный ров, к плитам двора каменные зубцы с бойницами
    # и кладка. Угол: кладка по нижней и правой кромке.
    "shoot_rail": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KGGGGGGKKGGGGGGK",
        "KGWGGGGKKGWGGGGK",
        "KGGGGGGKKGGGGGGK",
        "GGGGGGGGGGGGGGGG",
        "GGWGGGGGGGGGGGGG",
        "GGGGKGGGGGGGKGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKGGGGGK",
        "KKKKKKKKKKGWGGGK",
        "KKKKKKKKKKGGGGGK",
        "KKKKKKKKKKGGGGGK",
        "KKKKKKKKKKGGGKGK",
        "KKKKKKKKKKGGGGGK",
    ],
    # Подъёмный мост: деревянные доски поперёк стены с гвоздями, по нему стража выходит во двор.
    "shoot_plank": [
        "KKKKYYKYYKYYKKKK",
        "KKKKYYKYYKYYKKKK",
        "KKKKYYKYYKYYKKKK",
        "KKKKYWKYYKYWKKKK",
        "KKKKYYKYYKYYKKKK",
        "KKKKYYKYYKYYKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKYYKYYKYYKKKK",
        "KKKKYYKYYKYYKKKK",
        "KKKKYWKYYKYYKKKK",
        "KGGKYYKYYKYYKGGK",
        "GGGKYYKYYKYYKGGG",
        "GGGKKKKKKKKKKGGG",
        "GGGKYYKYYKYYKGGG",
        "GGGKYYKYYKYYKGGG",
        "KKKKYYKYYKYYKKKK",
    ],
    # Пропы двора: бочонок эля (вид сверху, золотые обручи, пробка в центре), окованный ларь с
    # замком, баллиста (дуга и ложе с болтом вверх, колёса по бокам), клубок пыли от павшего врага.
    "shoot_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KYYYYYYK....",
        "...KYKKKKKKYK...",
        "...KYKYYYYKYK...",
        "...KYKYKKYKYK...",
        "...KYKYKKYKYK...",
        "...KYKYYYYKYK...",
        "...KYKKKKKKYK...",
        "....KYYYYYYK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        "................",
        "...KKKKKKKKKK...",
        "..KYYYYYYYYYYK..",
        ".KYYYYYYYYYYYYK.",
        ".KGGGGGGGGGGGGK.",
        ".KYYYYKKKKYYYYK.",
        ".KYYYKWWWWKYYYK.",
        ".KYYYKWKKWKYYYK.",
        ".KYYYYKKKKYYYYK.",
        ".KGGGGGGGGGGGGK.",
        ".KYYYYYYYYYYYYK.",
        "..KYYYYYYYYYYK..",
        "...KKKKKKKKKK...",
        "................",
    ],
    "shoot_cannon": [
        "................",
        "......KWK.......",
        "......KGK.......",
        "...KKKKGKKKK....",
        "..KYKKKGKKKYK...",
        "..KYK..G..KYK...",
        "...KK..G..KK....",
        "......KYYK......",
        "......KRRK......",
        "..KKKKKYYKKKKK..",
        "..KGGKKYYKKGGK..",
        ".KWKGGKYYKGGKWK.",
        ".KGKGGGYYGGGKGK.",
        ".KGKKKKKKKKKKGK.",
        "..KK........KK..",
        "................",
    ],
    "shoot_puff": [
        "................",
        ".......W........",
        "......KKK....W..",
        "....KKGGGKKK....",
        "...KGGWWWWGGK...",
        "..KGWWWKWWWWGK..",
        "..KGWWWWWWWWGK..",
        ".KGWWKWWWWWWWGK.",
        ".KGWWWWWWWKWWGK.",
        "..KGWWWWWWWWGK..",
        "..KGWWWKWWWWGK..",
        "...KGGWWWWGGK...",
        "..G.KKKGGGKK....",
        ".......KKK......",
        "..........G.....",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KGRYW."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import castles8
        castles8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
