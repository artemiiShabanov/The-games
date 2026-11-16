#!/usr/bin/env python3
"""8-bit «Замки», гонки (вид сверху, #136): зеркало модуля космоса `space8_racing.py` и раздела
«Гонки × 8-bit» в `pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*` это
трасса (брусчатка тракта, демка мешает два варианта и отражает их, поэтому рисунок спокойный и
стыкуется при отражении), `race_shallow` обочина, которая тормозит (солома и грязь поверх
брусчатки), `race_sand*` стена (кладка замковой стены, туда не заехать; во втором варианте на
кладке щит с гербом), `race_rock` и `race_barrel` препятствия (валун и стог сена), `race_buoy`
столбик с вымпелом на кромке, `race_finish` финишная полоса с прозрачными краями (турнирная
шашечка). Транспорт в 8 направлениях из двух карт (на восток и на северо-восток) поворотами на
90°; индекс по часовой на экране: 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE. Диагональ это та
же карта, повёрнутая на 45°, отдельно не рисуется. Герой на боевой повозке с вымпелом, соперник
на крытой повозке чужого герба.

    python3 tools/castles8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Боевая повозка рыцаря: дощатый кузов (золото это дерево), четыре колеса по бортам, спереди
# стальной таран с бликом, в кузове шлем рыцаря с красным плюмажем, с шеста на корме назад бьётся
# красный вымпел. Строчная `w` это пыль из-под задних колёс, становится белым.
CART_E = [
    "................",
    "................",
    "................",
    "..KKKK....KKK...",
    ".KKGGKKKKKGGKK..",
    "wKYYYYYYYYYYYKK.",
    ".KYYYYKGGKYYYGGK",
    "RRRRKYRGWGKYYGWK",
    "..RRKYRGGGKYYGWK",
    ".KYYYYKGGKYYYGGK",
    "wKYYYYYYYYYYYKK.",
    ".KKGGKKKKKGGKK..",
    "..KKKK....KKK...",
    "................",
    "................",
    "................",
]

# Повозка чужого герба: крытый фургон, багровый тент на чёрных дугах, два больших колеса
# посередине, спереди окованный нос с шипом. Силуэт другой: колёса одной парой и тент в полоску.
WAGON_E = [
    "................",
    "................",
    "................",
    ".....KKKKKK.....",
    ".....KGGGGK.....",
    "..KKKKKKKKKKK...",
    "wKRRKRRKRRKGGK..",
    ".KRRKRRKRRKGWGKK",
    ".KRRKRRKRRKGWGKK",
    "wKRRKRRKRRKGGK..",
    "..KKKKKKKKKKK...",
    ".....KGGGGK.....",
    ".....KKKKKK.....",
    "................",
    "................",
    "................",
]


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def _turn45(rows):
    """Карта, повёрнутая на 45° против часовой (нос с востока на северо-восток). Диагональ
    повозки это тот же спрайт, повёрнутый, а не отдельный рисунок. Каждый пиксель берёт цвет
    большинства из девяти проб, так края выходят без дыр."""
    n = len(rows)
    mid = (n - 1) / 2.0
    k = 0.7071067811865476
    out = []
    for y in range(n):
        line = ""
        for x in range(n):
            votes = {}
            for sy in (-0.33, 0.0, 0.33):
                for sx in (-0.33, 0.0, 0.33):
                    dx, dy = x + sx - mid, y + sy - mid
                    u = int(round(dx * k - dy * k + mid))
                    v = int(round(dx * k + dy * k + mid))
                    ch = rows[v][u] if 0 <= u < n and 0 <= v < n else "."
                    votes[ch] = votes.get(ch, 0) + 1
            line += max(votes, key=lambda c: (votes[c], c != "."))
        out.append(line)
    return out


def frames(prefix, east, north_east):
    """8 направлений: `<prefix>_0..7`; строчные буквы следа становятся цветом."""
    out = {}
    e, ne = east, north_east
    for k in range(4):
        out[2 * k] = e
        out[(2 * k + 7) % 8] = ne
        e, ne = _cw(e), _cw(ne)
    return {"%s_%d" % (prefix, i): [r.replace("w", "W") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", CART_E, _turn45(CART_E)))
SPRITES.update(frames("rival", WAGON_E, _turn45(WAGON_E)))
SPRITES.update({
    # Трасса: брусчатка, от камней видны только короткие стыки, один камень затёрт до блеска.
    "race_water": [
        "GGGGGGGGGGGGGGGG",
        "GGGKGGGGGGGGKGGG",
        "GGGKGGGGGGGGKGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGKGGGGGGWWKGGG",
        "GGGKGGGGGGGGKGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Второй вариант: те же стыки, блеск в другом углу и оброненная соломинка.
    "race_water_1": [
        "GGGGGGGGGGGGGGGG",
        "GGGKGGGGGGGGKGGG",
        "GGGKWWGGGGGGKGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGKGGGGGGGGKGGG",
        "GGGKGGGGGGGGKGGG",
        "GGGGGGGGGYGGGGGG",
        "GGGGGGGGGGYGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Обочина: солома пучками и комья грязи поверх брусчатки, замедляет.
    "race_shallow": [
        "GGGGGGGGGGGGGGGG",
        "GGYGGGGGGGGKGGGG",
        "GYYGGGGGGGYGGYGG",
        "GGYKGGGKGGGYYGGG",
        "GGGGGGYGGGGGYKGG",
        "GKGGGYYGGGGGGGGG",
        "GGGGGGYKGGGGGGYG",
        "GGGGYGGGGGGGGYYG",
        "GGGYYGGGGGKGGGYK",
        "GGGGYKGGGYGGGGGG",
        "GGGGGGGGGGYYGGGG",
        "GYGGGGGGGGYKGGKG",
        "YYGGGGGKGGGGGYGG",
        "GYKGGGYYGGGGGYYG",
        "GGGGGGGYKGGGGGYG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Стена: кладка замка сверху, светлые блоки вперевязку на сером растворе; сюда не заехать.
    "race_sand": [
        "WWWWWWWGWWWWWWWG",
        "WWWWWWWGWWWWWWWG",
        "WWWWWWWGWWWWWWWG",
        "GGGGGGGGGGGGGGGG",
        "WWWGWWWWWWWGWWWW",
        "WWWGWWWWWWWGWWWW",
        "WWWGWWWWWWWGWWWW",
        "GGGGGGGGGGGGGGGG",
        "WWWWWWWGWWWWWWWG",
        "WWWWWWWGWWWWWWWG",
        "WWWWWWWGWWWWWWWG",
        "GGGGGGGGGGGGGGGG",
        "WWWGWWWWWWWGWWWW",
        "WWWGWWWWWWWGWWWW",
        "WWWGWWWWWWWGWWWW",
        "GGGGGGGGGGGGGGGG",
    ],
    # Во втором на кладке висит щит с гербом: красное поле, золотой пояс.
    "race_sand_1": [
        "WWWWWWWGWWWWWWWG",
        "WWWWWWWGWWWWWWWG",
        "WWWWWWWGWWWWWWWG",
        "GGGGKKKKKKKKGGGG",
        "WWWGKRRRRRRKWWWW",
        "WWWGKRRRRRRKWWWW",
        "WWWGKYYYYYYKWWWW",
        "GGGGKYYYYYYKGGGG",
        "WWWWKRRRRRRKWWWG",
        "WWWWKRRRRRRKWWWG",
        "WWWWWKRRRRKWWWWG",
        "GGGGGGKRRKGGGGGG",
        "WWWGWWWKKWWGWWWW",
        "WWWGWWWWWWWGWWWW",
        "WWWGWWWWWWWGWWWW",
        "GGGGGGGGGGGGGGGG",
    ],
    # Препятствия: валун (окатанная глыба с трещиной, светлая макушка) и стог сена сверху
    # (золотая копна, пряди по кругу, в середине шест).
    "race_rock": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "...KKGWWWGGKK...",
        "..KGWWWWGGGGGK..",
        ".KGGWWGGGGKGGGK.",
        ".KGGGGGGGKGGGGK.",
        ".KGGGGGGKGGGGGK.",
        ".KGGGGGGKKGGGGK.",
        ".KKGGGGGGGGGGKK.",
        "..KKGGGGGGGGKK..",
        "....KKKKKKKK....",
        "................",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        ".....KKKKKK.....",
        "...KKYYYYYYKK...",
        "..KYYWWYYYKYYK..",
        "..KYWYYYYYYKYK..",
        ".KYYYYYYYYYYYYK.",
        ".KYKYYYKKYYYWYK.",
        ".KYKYYYKKYYYWYK.",
        ".KYYYYYYYYYYYYK.",
        "..KYKYYYYYYWYK..",
        "..KYYKYYYWWYYK..",
        "...KKYYYYYYKK...",
        ".....KKKKKK.....",
        "................",
        "................",
    ],
    # Столбик с вымпелом на кромке трассы, украшение без столкновений: спил столба и красный
    # хвост вымпела в сторону.
    "race_buoy": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "....KKKK........",
        "...KYYYYKRR.....",
        "...KYWYYKRRRRR..",
        "...KYYYYKRRRR...",
        "...KYYYYKRR.....",
        "....KKKK........",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: турнирная шашечка, красное с белым, поперёк трассы; тайл кладётся вертикальной
    # полосой.
    "race_finish": [
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....RRRRWWWW....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
        "....WWWWRRRR....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), "размер карты %s" % _name
    assert set("".join(_rows)) <= set("KGRYW."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import castles8
        castles8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
