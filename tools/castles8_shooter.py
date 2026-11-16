#!/usr/bin/env python3
"""8-bit «Замки», шутер сверху (#136, #56): зеркало раздела «Шутер × 8-bit» в
`pixel_sprites.py` (`SHOOTER`) и модуля `space8_shooter.py`, те же слоты и размеры 16×16.
Палитра `castles8.PALETTE`: K чёрный, G камень и латы, R красный (плюмаж, табард, туника),
Y золото, дерево и солома, W блики стали и лицо. Место действия: гребень крепостной стены,
стража чужого замка лезет на него по перекидным мосткам.

Свойства, на которые рассчитана демка `shooter_bit8.gd`:
- `shoot_hero_0..3`: вправо, вниз, влево, вверх; из одной карты лицом вправо поворотами на 90°.
- `shoot_gunner_0..1`: анфас, оружие вправо (влево демка зеркалит), кадр 1 со вспышкой.
- `shoot_ball` это выстрел героя, `shoot_shot` это снаряд врага (так в демке: `hostile`);
  демка их не поворачивает, поэтому оба нарисованы «в торец», без направления.
- `shoot_deck*`, `shoot_rail*`, `shoot_plank` сплошные; у борта «снаружи» сверху (9 строк),
  брус к палубе снизу; у угла брус по нижней и правой кромке; демка их поворачивает.

    python3 tools/castles8_shooter.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


# Рыцарь сверху, лицом вправо: стальной шлем со смотровой щелью вперёд, красный плюмаж гребнем
# от макушки назад, наплечники с бликом сверху и снизу, между ними полоски красного табарда,
# арбалет в правой руке (внизу кадра): ложе вперёд, стальная дуга поперёк, жало болта.
HERO_E = [
    "................",
    "................",
    "....KKKKK.......",
    "...KWWWWGK......",
    "...KWGGGGK......",
    "..KKRKKKKKK.....",
    ".KRKKGGGGGGK....",
    ".KRRRRRWGKGK....",
    ".KRRRRRGGKGK....",
    ".KRKKGGGGGGK.K..",
    "..KKRKKKKKKKKGK.",
    "...KWGGGGYYYYGWK",
    "...KWWWWGKKKKGK.",
    "....KKKKK....K..",
    "................",
    "................",
]

SPRITES = {}
SPRITES.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
SPRITES.update({
    # Стражник-арбалетчик чужого замка: широкополая железная шапка, лицо в чёрном кольчужном
    # капюшоне, багровая туника с золотым гербом и поясом, арбалет вправо (ложе, дуга поперёк,
    # жало болта). Кадр 1: болт ушёл, на дуге белая вспышка тетивы, ноги вместе.
    "shoot_gunner_0": [
        "................",
        ".....KKKKKK.....",
        "....KGGWWGGK....",
        "..KKKGGGGGGKKK..",
        "..KGGWGGGGGGGK..",
        "...KKKKKKKKKK...",
        "...KKWKWWKWKK...",
        "...KKWWWWWWKK...",
        "....KKKKKKKK....",
        "...KRRRYYRRRK.G.",
        "..KGRRRYYRRRKKGK",
        "..KGKRRRRRRKYYGW",
        "..KGKYYYYYYK.KGK",
        "...K.KRRRRK...G.",
        ".....KG..GK.....",
        ".....KK..KK.....",
    ],
    "shoot_gunner_1": [
        "................",
        ".....KKKKKK.....",
        "....KGGWWGGK....",
        "..KKKGGGGGGKKK..",
        "..KGGWGGGGGGGK..",
        "...KKKKKKKKKK...",
        "...KKWKWWKWKK...",
        "...KKWWWWWWKK...",
        "....KKKKKKKK...W",
        "...KRRRYYRRRK.GY",
        "..KGRRRYYRRRKKGW",
        "..KGKRRRRRRKYYWW",
        "..KGKYYYYYYK.KGW",
        "...K.KRRRRK...GY",
        "......KGGK.....W",
        "......KKKK......",
    ],
    # Выстрел героя: арбалетный болт в торец, стальное перекрестье с золотым древком в центре.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        ".......KK.......",
        "......KWWK......",
        ".....KWYYWK.....",
        ".....KWYYWK.....",
        "......KWWK......",
        ".......KK.......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Снаряд стражи: горящий болт, красное пламя с золотым и белым ядром, заметно крупнее
    # выстрела героя.
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KRRRRK.....",
        "....KRRYYRRK....",
        "....KRYWWYRK....",
        "....KRYWWYRK....",
        "....KRRYYRRK....",
        ".....KRRRRK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    # Аптечка: зелье в круглой колбе, пробка, узкое стеклянное горло, красный настой с бликом.
    "shoot_rum": [
        "................",
        "................",
        "......KKKK......",
        "......KYYK......",
        "......KKKK......",
        "......KWGK......",
        "......KWGK......",
        ".....KKWGKK.....",
        "....KWWWGGGK....",
        "...KRRRRRRRRK...",
        "...KRWWRRRRRK...",
        "...KRWRRRRRRK...",
        "...KRRRRRRRRK...",
        "....KRRRRRRK....",
        ".....KKKKKK.....",
        "................",
    ],
    # Гребень стены: каменные плиты в два ряда по 8 пикселей со сдвигом швов; второй тайл с
    # трещиной и пучком соломы, демка кладёт его редко.
    "shoot_deck": [
        "GGGGKGGGGGGGGGGG",
        "GGGGKGGGGGGGGGGG",
        "GGGGKGGGGGGGGGGG",
        "GGGGKGGGGGGGGGGG",
        "GGGGKGGGGGGGGGGG",
        "GGGGKGGGGGGGGGGG",
        "GGGGKGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "GGGGKGGGGGGGGGGG",
        "GGGGKGGGGWKGGGGG",
        "GGGGKGGGGGKGGGGG",
        "GGGGKGGGGGGKKGGG",
        "GGGGKGGGGGGGKGGG",
        "GGGGKGGGGGGGGKGG",
        "GGGGKGGGGGGGGKGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGKGGG",
        "GGYGGGGGGGGGKGGG",
        "GGGYYGGYGGGGKGGG",
        "GGGGYYYGGGGGKGGG",
        "GGGYGGYYGGGGKGGG",
        "GGGGGGGGYGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    # Парапет: снаружи (сверху) темнота под стеной и зубцы с бликом по внешней кромке, к плитам
    # светлая кромка и каменный брус со швами. Угол: угловой зубец, брус по нижней и правой кромке.
    "shoot_rail": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKGKKKKKKKKKK",
        "KKKKKKKKKKKKKKKK",
        "KWWWWWWKKWWWWWWK",
        "KGGGGGGKKGGGGGGK",
        "KGGGGGGKKGGGGGGK",
        "KGGGGGGKKGGGGGGK",
        "KGGGGGGKKGGGGGGK",
        "KGGGGGGKKGGGGGGK",
        "KKKKKKKKKKKKKKKK",
        "WWWWWWWWWWWWWWWW",
        "GGGGGGGGGGGGGGGG",
        "GGGGKGGGGGGGKGGG",
        "GGGGKGGGGGGGKGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "KKKKKKKKKKKKKKKK",
        "KKKKKKKKKKKGKKKK",
        "KKKKKKKKKKKKKKKK",
        "KKKWWWWWWKWWWWWK",
        "KKKWGGGGGKGGGGGK",
        "KKKWGGGGGKGGGGGK",
        "KKKWGGGGGKGGGGGK",
        "KKKWGGGGGKGGGGGK",
        "KKKWGGGGGKGGGGGK",
        "KKKKKKKKKKKKKKKK",
        "KKKWGGGGGKWWWWWW",
        "KGKWGGGGGKWGGGGG",
        "KKKWGGGGGKWGKKGG",
        "KKKWGGGGGKWGKGGG",
        "KKKWGGGGGKWGGGGG",
        "KKKKKKKKKKWGGGGK",
    ],
    # Перекидной мосток: три доски поперёк парапета с железными полосами на заклёпках, по бокам
    # обрубки зубцов; по нему стража заходит на стену.
    "shoot_plank": [
        "KKKKYYKYYKYYKKKK",
        "KKKKYYKYYKYYKKKK",
        "KKKKGWGGGGWGKKKK",
        "KWWKYYKYYKYYKWWK",
        "KGGKYYKYYKYYKGGK",
        "KGGKYYKYYKYYKGGK",
        "KGGKYYKYYKYYKGGK",
        "KGGKYYKYYKYYKGGK",
        "KGGKYYKYYKYYKGGK",
        "KKKKYYKYYKYYKKKK",
        "WWWKYYKYYKYYKWWW",
        "GGGKYYKYYKYYKGGG",
        "GGGKGWGGGGWGKGGG",
        "GGGKYYKYYKYYKGGG",
        "GGGKYYKYYKYYKGGG",
        "KKKKYYKYYKYYKKKK",
    ],
    # Пропы стены: стог сена (копна с прядями и торчащими соломинами), окованный ларь (доски,
    # две железные полосы, замок), баллиста (болт вверх, плечи в стороны, тетива к вороту),
    # облако пыли с искрами от поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        "......KKKK......",
        ".....KYWYYK.....",
        "....KYWYYKYK....",
        "...KYWYYKYYYK...",
        "...KYWYKYYKYK...",
        "..KYWYYKYYKYYK..",
        "..KYWYKYYKYYKK..",
        "..KYYYKYYKYYKYK.",
        ".KYWYKYYKYYKYYK.",
        ".KYYKYYKYYYKYYK.",
        ".KYKKYKKYKKYKYK.",
        "..K..K..K..K.K..",
        "................",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        ".KYWGWWWWWWGWYK.",
        ".KYYGYYYYYYGYYK.",
        ".KYYGYYYYYYGYYK.",
        ".KKKKKKKKKKKKKK.",
        ".KYYGYYKKYYGYYK.",
        ".KYYGYKWWKYGYYK.",
        ".KYYGYKWWKYGYYK.",
        ".KYYGYYKKYYGYYK.",
        ".KYYGYYYYYYGYYK.",
        ".KGGGGGGGGGGGGK.",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    "shoot_cannon": [
        ".......KK.......",
        "......KWWK......",
        "......KWWK......",
        ".KK...KGGK...KK.",
        "KYYKK.KGGK.KKYYK",
        "KWKYYKKYYKKYYKWK",
        ".KWKKYYYYYYKKWK.",
        "..KWKKKYYKKKWK..",
        "...KWK.YY.KWK...",
        "....KWKYYKWK....",
        "..KKKKWYYWKKKK..",
        "..KGGKYYYYKGGK..",
        "..KGGKYWWYKGGK..",
        "..KGGKYYYYKGGK..",
        "..KKKKKKKKKKKK..",
        "................",
    ],
    "shoot_puff": [
        "................",
        "......Y.........",
        "....KKK..KKK....",
        "...KWWWKKWWWK.Y.",
        "..KWWWWWWWWWGK..",
        ".KKWWGWWWWWWGK..",
        "KWWWWWWWWKWWWKK.",
        "KWWWWKWWWWWWWWGK",
        "KGWWWWWWWWWGWWGK",
        ".KGWWWWGWWWWWGK.",
        ".KKGWWWWWWKWGGK.",
        "Y.KGGWWWGGWGGK..",
        "...KKGGGKKGGK...",
        ".....KKK..KK...Y",
        "................",
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
