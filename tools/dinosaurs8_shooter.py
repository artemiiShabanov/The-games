#!/usr/bin/env python3
"""8-bit «Динозавры», шутер сверху (#137, #56): зеркало модуля космоса `space8_shooter.py`
(раздел «Шутер × 8-bit» в `pixel_sprites.py`, `SHOOTER`), те же слоты и размеры 16×16. Палитра
`dinosaurs8.PALETTE`: K чёрный, O шкура и лава, S кожа и песчаник, G зелень, W кость.

Арена это плита песчаника над лавовым озером: вместо палубы каменные плиты, вместо моря лава,
борт из частокола клыков и полосы папоротника, мостик из рёбер на двух брёвнах.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`).
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (9 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

    python3 tools/dinosaurs8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Пещерный человек сверху, лицом вправо: чёрная копна с костью поперёк макушки, лицо и нос
# вперёд, лохмы торчат назад, шкура на дальнем плече, ближнее плечо голое, в вытянутой руке
# (внизу кадра) рогатка рожками вперёд с камнем в натянутой коже.
HERO_E = [
    "................",
    "................",
    "....KKKKKK......",
    "...KOOOOOOK.....",
    "...KWKWOOOK.....",
    "..KKKWKKKKK.....",
    ".KKKKWKKKSSK....",
    "KKKKKWKKKSSSK...",
    ".KKKKWKKKSSSKKKK",
    "KKKKKWKKKSSKKWWK",
    "..KKKWKKKKSSWKSK",
    "...KWKWSSKKKKWWK",
    "...KSSSSSSK.KKK.",
    "....KKKKKK......",
    "................",
    "................",
]

# Лава снаружи арены (9 строк): оранжевый расплав с белыми жилами жара и чёрными корками.
_LAVA = [
    "OOOOOOOOOOOOOOOO",
    "OOOWWOOOOOOOKKOO",
    "OOOOOOOOOOOKKKKO",
    "OOOOOOOOOOOOKKOO",
    "OKKOOOOWWWOOOOOO",
    "KKKKOOOOOOOOOOOO",
    "OKKOOOOOOOOOWWOO",
    "OOOOOOWOOOOOOOOO",
    "OOOOOOOOOOOOOOOO",
]
# Борт: частокол клыков остриями наружу и полоса папоротника к плитам.
_BEAM = [
    "KWKKKWKKKWKKKWKK",
    "WWWKWWWKWWWKWWWK",
    "GGGGGGGGGGGGGGGG",
    "GGKGGGGSGGGGKGGG",
    "GGGGGKGGGGGGGGSG",
    "GGGGGGGGGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
]
_RAIL = _LAVA + _BEAM

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Раптор-метатель: стоит прямо, зубастая морда повёрнута к оружию, светлое брюхо, хвост
    # дугой за спиной, в когтистой лапе вправо ком лавы; кадр 1 бросок со вспышкой, ноги вместе.
    "shoot_gunner_0": [
        "................",
        "....KKKKKK......",
        "...KGGGGGGKKKK..",
        "...KGWKGGGGGGGK.",
        "...KGGGGGGGGKGK.",
        "...KGGGKWKWKWK..",
        "...KGGGKGGGGGK..",
        "....KGGGKKKKK...",
        "...KKGSSGKK.....",
        "KK.KGGSSSGGK....",
        "KGKKGGSSSGGKKKK.",
        "KGGKKGSSSGKGGOOK",
        ".KGGGGGSGGK.KKK.",
        "..KKKGGKGGK.....",
        "....KGK.KGK.....",
        "...KKKK.KKKK....",
    ],
    "shoot_gunner_1": [
        "................",
        "....KKKKKK......",
        "...KGGGGGGKKKK..",
        "...KGWKGGGGGGGK.",
        "...KGGGGGGGGKGK.",
        "...KGGGKWKWKWK..",
        "...KGGGKGGGGGK..",
        "....KGGGKKKKK...",
        "...KKGSSGKK...O.",
        "KK.KGGSSSGGK.OWO",
        "KGKKGGSSSGGKKKKO",
        "KGGKKGSSSGKGGGK.",
        ".KGGGGGSGGK.KKK.",
        "..KKKGGGGGK.....",
        ".....KGGGK......",
        ".....KKKKK......",
    ],
    # Выстрел героя: камень из рогатки, угловатый, с белым сколом.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KSWWSK.....",
        ".....KSWSSK.....",
        ".....KSSSKK.....",
        ".....KSSKSK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд раптора: ком лавы с белым жаром внутри и искрами по углам, заметно крупнее камня.
    "shoot_shot": [
        "................",
        "................",
        "....O......O....",
        "................",
        "......KKKK......",
        ".....KOOOOK.....",
        "....KOOWWOOK....",
        "....KOWWWOOK....",
        "....KOOWWOOK....",
        "....KOOOOKOK....",
        ".....KOOOOK.....",
        "......KKKK......",
        "................",
        "....O......O....",
        "................",
        "................",
    ],
    # Аптечка: жареная ножка на кости, кость с двойным набалдашником торчит вверх вправо.
    "shoot_rum": [
        "................",
        "...........KK...",
        "..........KWWKK.",
        "..........KWWWWK",
        ".........KWWKWWK",
        "........KWWK.KK.",
        "....KKKKWWK.....",
        "...KOOOOOWK.....",
        "..KOOSOOOOOK....",
        "..KOSOOOOOOK....",
        "..KOOOOOOOOK....",
        "..KOOOOOOKOK....",
        "..KOOOOOKOOK....",
        "...KOOOOOOK.....",
        "....KKKKKK......",
        "................",
    ],
    # Плиты песчаника: два ряда по 8 пикселей со стыками вразбежку и рыжими крапинами; второй
    # тайл с отпечатком аммонита, трещиной и кустиком мха, демка кладёт его редко.
    "shoot_deck": [
        "SSSSSKSSSSSSSSSS",
        "SSSSSKSSSSSSSSSS",
        "SSSSSKSSSSOSSSSS",
        "SSSSSKSSSSSSSSSS",
        "SOSSSKSSSSSSSSSS",
        "SSSSSKSSSSSSSSSS",
        "SSSSSKSSSSSSSSSS",
        "KKKKKKKKKKKKKKKK",
        "SSSSSSSSSSSSKSSS",
        "SSSSSSSSSSSSKSSS",
        "SSSOSSSSSSSSKSSS",
        "SSSSSSSSSSSSKSSS",
        "SSSSSSSSOSSSKSSS",
        "SSSSSSSSSSSSKSSS",
        "SSSSSSSSSSSSKSSS",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "SSSSSKSSSSSSSSSS",
        "SSSSSKSSSWWWSSSS",
        "SSSSSKSSWSSSWSSS",
        "SSSSSKSSWSWSWSSS",
        "SSSSSKSSWSWWSSSS",
        "SSSSSKSSSWWWWWSS",
        "SSSSSKSSSSSSSSSS",
        "KKKKKKKKKKKKKKKK",
        "SSSSSSSSSSSSKSSS",
        "SSKSSSSSSSSSKSSS",
        "SSSKSSSGSSSSKSSS",
        "SSSKKSGGGSSSKSSS",
        "SSSSSKSGSSSSKSSS",
        "SSSSSSSSSSSSKSSS",
        "SSSSSSSSSSSSKSSS",
        "KKKKKKKKKKKKKKKK",
    ],
    # Борт арены: снаружи (сверху) лава, к плитам частокол клыков и полоса папоротника.
    # Угол: частокол и папоротник по нижней и правой кромке.
    "shoot_rail": list(_RAIL),
    "shoot_rail_corner": [
        "OOOOOOOOOOOOOOOO",
        "OOOWWOOOOOOOKKOO",
        "OOOOOOOOOOOKKKKO",
        "OOOOOOOOOOOOKKOO",
        "OKKOOOOWWWOOOOOO",
        "KKKKOOOOOOOOOOOO",
        "OKKOOOOOOOOOWWOO",
        "OOOOOOWOOOOOOOOO",
        "OOOOOOOOOOOOOOOO",
        "OOOOOOOOKKWKKKWK",
        "OOWOOOOOKWWWKWWW",
        "OOOOOOOOKKWGGGGG",
        "OOOOOOOOKWWGGKGG",
        "OKKOOOOOKKWGGGGG",
        "OOOOOOOOKWWGSGGG",
        "OOOOOOOOKKWGGGGK",
    ],
    # Мостик через борт: рёбра-перекладины на двух брёвнах, по нему рапторы заходят на арену.
    "shoot_plank": [
        _RAIL[y][:2] + "KS" + ("KKKKKKKK" if y % 3 == 2 else "WWWWWWWW") + "SK" + _RAIL[y][14:]
        for y in range(16)
    ],
    # Пропы арены: гнездо с тремя яйцами (вид сверху, прутья кольцом), плетёная корзина с
    # плодами и листом, катапульта из бревна (ложка с камнем вверх, каменные колёса по бокам),
    # клуб пыли с искрами от поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        "....KKKKKKKK....",
        "..KKSSSKSSSSKK..",
        ".KSSKKKKKKKKSSK.",
        ".KSKWWWKKKKKKSK.",
        ".KSKWWWWKKWWKSK.",
        ".KSKWWOWKWWWWKK.",
        ".KKKKWWKKWOWWSK.",
        ".KSKKKKWWKWWKSK.",
        ".KSSKKWWWWKKSSK.",
        "..KSSKKWWKKSSK..",
        "...KKSSSKSSKK...",
        ".....KKKKKK.....",
        "................",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        "......KK.KKK....",
        ".....KGGKOOOK...",
        "...KKOOKKOOOOK..",
        "..KOOOOOKOOOOKK.",
        ".KKKKKKKKKKKKKK.",
        ".KSSSSSSSSSSSSK.",
        ".KKKKKKKKKKKKKK.",
        "..KSSKSSKSSKSK..",
        "..KKSSKSSKSSKK..",
        "..KSSKSSKSSKSK..",
        "..KKSSKSSKSSKK..",
        "...KSKSSKSSKK...",
        "...KKKKKKKKKK...",
        "................",
    ],
    "shoot_cannon": [
        "................",
        "......KKKK......",
        ".....KSSSSK.....",
        "....KWKSSKWK....",
        ".....KWWWWK.....",
        "......KSSK......",
        "......KSKK......",
        "......KSSK......",
        "..KKKKKSSKKKKK..",
        "..KSSKKKKKKSSK..",
        ".KOKSKKGGKKSKOK.",
        ".KOKSSKGGKSSKOK.",
        ".KOKSSSSSSSSKOK.",
        "..KSSSSSSSSSSK..",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    "shoot_puff": [
        "................",
        "....O......W....",
        ".....KKK.KK.....",
        "...KKWWWKWWKK...",
        "..KWWWWWWWWWSK..",
        "..KWWWSWWWWWSK..",
        ".KWWWWWWWWKWWSK.",
        ".KWWKWWWWWWWWSK.",
        ".KWWWWWWWSWWSSK.",
        "..KWWWWWWWWWSK..",
        "..KSWWWKWWWSSK..",
        "...KSSWWWSSKK...",
        ".O..KKSSSKK....O",
        "......KKK.......",
        "...W............",
        "................",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name
    assert set("".join(_rows)) <= set("KOSGW."), _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import dinosaurs8
        dinosaurs8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
