#!/usr/bin/env python3
"""8-bit «Космос», шутер сверху (#136, #56): зеркало раздела «Шутер × 8-bit» в
`pixel_sprites.py` (`SHOOTER`), те же слоты и размеры 16×16. Палитра `space8.PALETTE`:
K чёрный, W скафандр, C бирюза и энергия, V пришельцы, G металл.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (9 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

    python3 tools/space8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Космонавт сверху, лицом вправо: круглый шлем с визором вперёд, ранец сзади, плечи скафандра
# сверху и снизу, лучевой пистолет в правой руке (внизу кадра) стволом вперёд.
HERO_E = [
    "................",
    "................",
    "....KKKKK.......",
    "...KWWWWWK......",
    "...KWWGWWK......",
    "..KKWKKKKKK.....",
    ".KGKKWWWWCCK....",
    ".KGKWWWWWCCK....",
    ".KGKWWWWWCCK....",
    ".KGKKWWWWCCKKKKK",
    "..KKWKKKKKKGGCCK",
    "...KWWGWWKKKKKK.",
    "...KWWWWWK......",
    "....KKKKK.......",
    "................",
    "................",
]

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Пришелец-стрелок: большая голова с усиками и чёрными глазами, металлический нагрудник с
    # огоньком, бластер вправо; кадр 1 со вспышкой и ногами вместе.
    "shoot_gunner_0": [
        "....C......C....",
        "....KK....KK....",
        "...KKVVVVVVKK...",
        "..KVVVVVVVVVVK..",
        "..KVKKVVVVKKVK..",
        "..KVKKKVVKKKVK..",
        "..KVVVVVVVVVVK..",
        "...KVVVKKVVVK...",
        "....KKKKKKKK....",
        "...KGGGCCGGGK...",
        "..KVGGGCCGGGVKK.",
        "..KVKGGGGGGKGKKK",
        "..KVKGGGGGGK.KK.",
        "...K.KVVVVK.....",
        ".....KV..VK.....",
        ".....KK..KK.....",
    ],
    "shoot_gunner_1": [
        "....C......C....",
        "....KK....KK....",
        "...KKVVVVVVKK...",
        "..KVVVVVVVVVVK..",
        "..KVKKVVVVKKVK..",
        "..KVKKKVVKKKVK..",
        "..KVVVVVVVVVVK..",
        "...KVVVKKVVVK...",
        "....KKKKKKKK..C.",
        "...KGGGCCGGGKCWC",
        "..KVGGGCCGGGKKKC",
        "..KVKGGGGGGKGKK.",
        "..KVKGGGGGGK.KK.",
        "...K.KVVVVK.....",
        "......KVVK......",
        "......KKKK......",
    ],
    # Выстрел героя: бирюзовый сгусток с белым ядром.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KCCCCK.....",
        ".....KCWWCK.....",
        ".....KCWWCK.....",
        ".....KCCCCK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд пришельца: фиолетовая плазма с белой искрой, заметно крупнее выстрела героя.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KVVVVK.....",
        "....KVVWWVVK....",
        "....KVWWVVVK....",
        "....KVVVVVVK....",
        "....KVVVVVVK....",
        ".....KVVVVK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Аптечка: батарея с клеммой и тремя делениями заряда.
    "shoot_rum": [
        "................",
        "................",
        "......KKKK......",
        "......KGGK......",
        "....KKKKKKKK....",
        "....KWWWWWWK....",
        "....KWCCCCWK....",
        "....KWWWWWWK....",
        "....KWCCCCWK....",
        "....KWWWWWWK....",
        "....KWCCCCWK....",
        "....KWWWWWWK....",
        "....KGGGGGGK....",
        "....KGGGGGGK....",
        ".....KKKKKK.....",
        "................",
    ],
    # Настил станции: металлические полосы по 8 пикселей; второй тайл со стыком панелей,
    # заклёпками и огоньком, демка кладёт его редко.
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
        "GGGGGGGGKGGGGGGG",
        "GGGGGGGWKGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGGGGG",
        "GGGKKKKGGGGGGGGG",
        "GGGKCCKGGGGGGGGG",
        "GGGKKKKGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    # Борт отсека: снаружи (сверху) пустота со звёздами, к палубе белый поручень и металлический
    # брус с заклёпками. Угол: брус по нижней и правой кромке.
    "shoot_rail": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKWKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKCKK",
        "KKKKKKKKKKKKKKKK",
        "KWKKKKKKKKKKKKKK",
        "KKKKKKKKKCKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "WWWWWWWWWWWWWWWW",
        "GGGGGGGGGGGGGGGG",
        "GGKGGGGGGGGGKGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKWKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KWKKKKKKKKKKKKKK",
        "KKKKKKCKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKWWWWWW",
        "KKKKKKKKKKWGGGGG",
        "KKKKKKKKKKWGKGGG",
        "KKKKKKKKKKWGGGGG",
        "KKKKKKKKKKWGGGGG",
        "KKKKKKKKKKWGGGGK",
    ],
    # Стыковочный мостик: светлые ступени поперёк борта, по нему пришельцы заходят в отсек.
    "shoot_plank": [
        "KKKKWWKWWKWWKKKK",
        "KKKKWWKWWKWWKKKK",
        "KWKKWWKWWKWWKKKK",
        "KKKKWWKWWKWWKKCK",
        "KKKKWWKWWKWWKKKK",
        "KKKKWWKWWKWWKKKK",
        "KKKKCWKCWKCWKKKK",
        "KKKKWWKWWKWWKKKK",
        "KKKKWWKWWKWWKKKK",
        "KKKKWWKWWKWWKKKK",
        "WWWKWWKWWKWWKWWW",
        "GGGKWWKWWKWWKGGG",
        "GGKKCWKCWKCWKKGG",
        "GGGKWWKWWKWWKGGG",
        "GGGKWWKWWKWWKGGG",
        "KKKKWWKWWKWWKKKK",
    ],
    # Пропы отсека: топливный баллон (вид сверху, вентиль в центре), грузовая капсула с окошком
    # и белыми обручами, лазерная турель (излучатель вверх), вспышка от поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KGGGGGGK....",
        "...KGKKKKKKGK...",
        "...KGKWWWWKGK...",
        "...KGKWCCWKGK...",
        "...KGKWCCWKGK...",
        "...KGKWWWWKGK...",
        "...KGKKKKKKGK...",
        "....KGGGGGGK....",
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
        "..KGGGGGGGGGGK..",
        ".KGGGGGGGGGGGGK.",
        ".KWWWWWWWWWWWWK.",
        ".KGGGGKKKKGGGGK.",
        ".KGGGKCCCCKGGGK.",
        ".KGGGKCCCCKGGGK.",
        ".KGGGGKKKKGGGGK.",
        ".KWWWWWWWWWWWWK.",
        ".KGGGGGGGGGGGGK.",
        "..KGGGGGGGGGGK..",
        "...KKKKKKKKKK...",
        "................",
    ],
    "shoot_cannon": [
        "................",
        "......KKKK......",
        ".....KKCCKK.....",
        "......KCCK......",
        "......KWGK......",
        "......KWGK......",
        ".....KKWGKK.....",
        "..KKKKKWGKKKKK..",
        "..KGGKKKKKKGGK..",
        ".KCKGKKCCKKGKCK.",
        ".KCKGGKCCKGGKCK.",
        ".KCKGGGGGGGGKCK.",
        "..KGGGGGGGGGGK..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    "shoot_puff": [
        "................",
        ".......C........",
        "......KKK....C..",
        "....KKCCCKKK....",
        "...KCCWWWWCCK...",
        "..KCWWWKWWWWCK..",
        "..KCWWWWWWWWCK..",
        ".KCWWKWWWWWWWCK.",
        ".KCWWWWWWWKWWCK.",
        "..KCWWWWWWWWCK..",
        "..KCWWWKWWWWCK..",
        "...KCCWWWWCCK...",
        "..C.KKKCCCKK....",
        ".......KKK......",
        "..........C.....",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KWCVG."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import space8
        space8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
