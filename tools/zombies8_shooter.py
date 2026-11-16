#!/usr/bin/env python3
"""8-bit «Зомби», шутер сверху (#137, #56): зеркало `space8_shooter.py` и раздела «Шутер ×
8-bit» в `pixel_sprites.py` (`SHOOTER`), те же слоты и размеры 16×16. Палитра
`zombies8.PALETTE`: K чёрный, R куртка и кровь, G мёртвая кожа и слизь, W кость, мешки и
жесть, B бейсболка, джинсы и плиты.

Двор убежища ночью: плиты кладбища, по краю баррикада из мешков с песком, за ней тёмная грязь
с бурьяном, через пролом по доскам лезут зомби.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, рука вправо (влево демка зеркалит), кадр 1 с плевком у руки.
- `shoot_ball` это выстрел героя (гвоздь шляпкой к зрителю), `shoot_shot` это плевок зомби
  (так в демке: `hostile`); оба без направления, демка их не поворачивает.
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (9 строк),
  мешки к двору снизу; у угла мешки в нижнем правом углу; демка их поворачивает.

    python3 tools/zombies8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Выживший сверху, лицом вправо: синяя бейсболка с пуговкой и козырьком вперёд, зелёный рюкзак
# сзади, плечи красной куртки сверху и снизу, револьвер в правой руке (внизу кадра) стволом
# вперёд.
HERO_E = [
    "................",
    "................",
    "....KKKKK.......",
    "...KRRRRRK......",
    "...KRRWRRK......",
    "..KKRKKKKKK.....",
    ".KGKKBBBBBKK....",
    ".KGKBBWBBBBBK...",
    ".KGKBBBBBBBBK...",
    ".KGKKBBBBBKKKKKK",
    "..KKRKKKKKKWBBWK",
    "...KRRWRRKKKKKK.",
    "...KRRRRRK......",
    "....KKKKK.......",
    "................",
    "................",
]

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Зомби-плевун: узкая голова с проплешиной до кости, красные глаза, оскал, рваная рубаха в
    # крови, рука тянется вправо; кадр 1 с раскрытой пастью, плевком у руки и ногами вместе.
    "shoot_gunner_0": [
        "................",
        ".....KKKKKK.....",
        "....KGGGWWGK....",
        "...KGGGGGWGGK...",
        "...KGKKGGKKGK...",
        "...KGRKGGRKGK...",
        "...KGGGGGGGGK...",
        "....KGWKWKGK....",
        "....KKKKKKKK....",
        "...KWWWRWWWWK...",
        "..KGWWBWWRWWKKK.",
        "..KGKWWWWBWKGGGK",
        "..KGKWBWWWWK.KK.",
        "...K.KBBBBK.....",
        ".....KB..BK.....",
        ".....KK..KK.....",
    ],
    "shoot_gunner_1": [
        "................",
        ".....KKKKKK.....",
        "....KGGGWWGK....",
        "...KGGGGGWGGK...",
        "...KGKKGGKKGK...",
        "...KGRKGGRKGK...",
        "...KGGKKKKGGK...",
        "....KGKRRKGK....",
        "....KKKKKKKK..G.",
        "...KWWWRWWWWKGWG",
        "..KGWWBWWRWWKKKG",
        "..KGKWWWWBWKGKK.",
        "..KGKWBWWWWK.KK.",
        "...K.KBBBBK.....",
        "......KBBK......",
        "......KKKK......",
    ],
    # Выстрел героя: гвоздь шляпкой к зрителю, белая шляпка с красными искрами по углам.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KRWWRK.....",
        ".....KWWWWK.....",
        ".....KWWBWK.....",
        ".....KRWWRK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Плевок зомби: зелёный сгусток слизи с бликом и пузырём, заметно крупнее выстрела героя.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KGGGGK.....",
        "....KGWWGGGK....",
        "....KGWGGGGK....",
        "....KGGGGKGK....",
        "....KGGGGGGK....",
        ".....KGGGGK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Аптечка: белый чемоданчик с ручкой и красным крестом, синяя тень по низу.
    "shoot_rum": [
        "................",
        "................",
        "......KKKK......",
        ".....KK..KK.....",
        "..KKKKKKKKKKKK..",
        "..KWWWWWWWWWWK..",
        "..KWWWWRRWWWWK..",
        "..KWWWWRRWWWWK..",
        "..KWWRRRRRRWWK..",
        "..KWWRRRRRRWWK..",
        "..KWWWWRRWWWWK..",
        "..KWWWWRRWWWWK..",
        "..KBBBBBBBBBBK..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    # Двор убежища: плиты кладбища вперевязку, по 8 пикселей в высоту; второй тайл с трещиной,
    # мхом в шве, костью и пятном крови, демка кладёт его редко.
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
        "BBKBBBBKBBBBBBBB",
        "BBBKBBBKBBBWWBBB",
        "BBBKKBBKBBWBBWBB",
        "BBBBBKBGBBBWWBBB",
        "BBBBBBKGBBBBBBBB",
        "BBBBBBBGBBBBBBBB",
        "KKKKGGKKKKKKKKKK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBRRBBBBK",
        "BBBBBBBBRRRRBBBK",
        "BBWBBBBBBRRBBBBK",
        "BBBBBBBBBBBBRBBK",
        "BBBBBBBBBBBBBBBK",
        "BBBBBBBBBBBBBBBG",
        "KKKKKKKKKKKKKGGK",
    ],
    # Баррикада: снаружи (сверху) ночная грязь с пучками бурьяна и костями, ко двору два ряда
    # мешков с песком вперевязку. Угол: мешки в нижнем правом углу, стыкуются с бортами.
    "shoot_rail": [
        "KKKKKKKKKKKKKKKK",
        "KKKKGKKKKKKKKKKK",
        "KKKGKGKKKKKKWKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKGKKKKK",
        "KWKKKKKKKGKGKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "WWWWWWWKWWWWWWWK",
        "WWWWWWBKWWWWWWBK",
        "KKKKKKKKKKKKKKKK",
        "WWWKWWWWWWWKWWWW",
        "WWBKWWWWWWBKWWWW",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKKKGKKKKKKKKKKK",
        "KKKGKGKKKKKKKKKK",
        "KKKKKKKKKKKKWKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KWKKKKGKKKKKKKKK",
        "KKKKKGKGKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKWWWWKW",
        "KKKKKKKKKKWWWBKW",
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKWWKWWW",
        "KKKKKKKKKKWBKWWB",
        "KKKKKKKKKKWWKWWK",
    ],
    # Пролом в баррикаде: светлые доски поперёк мешков, синие сучки и
    # кровавые следы; по ним зомби заходят во двор.
    "shoot_plank": [
        "KKKKWWKWWKWWKKKK",
        "KKKKWWKWWKWWKKKK",
        "KGKKWWKWBKWWKKKK",
        "GKGKWWKWWKWWKKWK",
        "KKKKWBKWWKWWKKKK",
        "KKKKWWKRWKWWKKKK",
        "KKKKWWKRRKWWKGKK",
        "KKKKWWKWWKWBGKGK",
        "KKKKWWKWWKWWKKKK",
        "KKKKWWKWWKWWKKKK",
        "WWWKWWKWWKWWKWWK",
        "WWBKWWKWWKRWKWBK",
        "KKKKWBKWWKWWKKKK",
        "WWWKWWKWWKWWKWWW",
        "WWBKWWKWBKWWKWWW",
        "KKKKWWKWWKWWKKKK",
    ],
    # Пропы двора: мусорный бак (вид сверху, ребристая крышка с ручкой), армейский ящик со
    # звездой по трафарету и защёлкой, самодельный миномёт (труба вверх, сошки, плита),
    # облако зелёного тумана с осколками костей от поверженного зомби.
    "shoot_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KBBBBBBK....",
        "...KBWWWWWWBK...",
        "...KBWBBBBWBK...",
        "...KBWKKKKWBK...",
        "...KBWKWWKWBK...",
        "...KBWBBBBWBK...",
        "...KBWWWWWWBK...",
        "....KBBBBBBK....",
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
        ".KGGGGGGGGGGGGK.",
        ".KGKGGGWWGGGKGK.",
        ".KGGGWWWWWWGGGK.",
        ".KGGGGWWWWGGGGK.",
        ".KGKGGWGGWGGKGK.",
        ".KGGGGGGGGGGGGK.",
        ".KKKKKKKKKKKKKK.",
        ".KGGGGKWWKGGGGK.",
        ".KGGGGKKKKGGGGK.",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    "shoot_cannon": [
        "................",
        ".....KKKKKK.....",
        ".....KWKKBK.....",
        ".....KWWBBK.....",
        "......KWBK......",
        "......KRRK......",
        "......KWBK......",
        ".....KKWBKK.....",
        "....KGKWBKGK....",
        "...KGKKWBKKGK...",
        "..KGK.KWBK.KGK..",
        "..KK.KKKKKK.KK..",
        "...KKBBBBBBKK...",
        "..KBBWBBBBBBBK..",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    "shoot_puff": [
        "................",
        ".......R........",
        "......KKK....G..",
        "....KKGGGKKK....",
        "...KGGWWGGGGK...",
        "..KGGWWWGKGGGK..",
        "..KGGGGGGGGWGK..",
        ".KGGKGGWWGGGGGK.",
        ".KGGGGGWWGGKGGK.",
        "..KGWGGGGGGGGK..",
        "..KGGGGKGGWWGK..",
        "...KGGGGGGWGK...",
        "..R.KKKGGGKK....",
        ".......KKK......",
        "..........G.....",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KRGWB."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import zombies8
        zombies8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
