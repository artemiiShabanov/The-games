#!/usr/bin/env python3
"""8-bit «Динозавры», гонки (вид сверху, #137): зеркало модуля космоса `space8_racing.py` и
раздела «Гонки × 8-bit» в `pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*`
это трасса (утоптанный песчаник, демка мешает два варианта и отражает их, поэтому рисунок
симметричен по углам; во втором варианте трёхпалый след), `race_shallow` обочина, которая
тормозит (папоротники и хвощи на песке), `race_sand*` стена (заросли джунглей, туда не заехать;
во втором варианте лужа лавы), `race_rock` и `race_barrel` препятствия (глыба лавы в горячих
трещинах и плетёная корзина с плодами), `race_buoy` маячок на кромке (костёр в кольце камней),
`race_finish` финишная полоса из костяных плиток с прозрачными краями. Транспорт в 8
направлениях из одной карты на восток: диагональ это она же, повёрнутая на 45° (`_turn45`),
остальное поворотами на 90°; индекс по часовой на экране: 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N,
7 NE. Герой на каменной тележке с колёсами-валунами, соперник-раптор на тележке из костей.
Парусов и мачт нет: это повозки на четырёх колёсах. Палитра в `dinosaurs8.py`: K чёрный,
O шкура и лава, S песчаник и дерево, G зелень, W кость.

    python3 tools/dinosaurs8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Каменная тележка: плита песчаника в трещинах на четырёх колёсах-валунах по бортам (задние
# крупнее), посередине пещерный человек: плечи в оранжевой шкуре, чёрная копна, кость продета
# поперёк волос. Спереди два бивня, сзади пыль (строчная `s` становится песком, как пена `w`
# у шлюпки).
CART_E = [
    "................",
    "................",
    "..KKKKK..KKKK...",
    ".KWWWWWKKWWWWK..",
    ".KWWKWWKKWKWWK..",
    ".KKKKKKKKKKKKKK.",
    ".KSSSSOOWSSSSSKW",
    "sKSKSSOOKKKSSSK.",
    "sKSSSSOOKKKSKSK.",
    ".KSSSSOOWSSSSSKW",
    ".KKKKKKKKKKKKKK.",
    ".KWWKWWKKWKWWK..",
    ".KWWWWWKKWWWWK..",
    "..KKKKK..KKKK...",
    "................",
    "................",
]

# Тележка из костей: рама из рёбер поперёк хода, колёса это спилы бревна со ступицей, на носу
# череп с двумя рогами вперёд. Правит зелёный раптор: хвост назад, туловище шире, узкая морда
# к носу. Сзади костяная пыль (строчная `w` становится костью). Диагональ тем же поворотом.
BONES_E = [
    "................",
    "................",
    "...KKK....KKK...",
    "..KSSSK..KSSSK..",
    "..KSKSK..KSKSK..",
    ".KKKKKKKKKKKKKK.",
    ".KWKWGGGGKKKWWK.",
    "wKGGGGGGGGGGKWKW",
    "wKGGGGGGGGGGKWKW",
    ".KWKWGGGGKKKWWK.",
    ".KKKKKKKKKKKKKK.",
    "..KSKSK..KSKSK..",
    "..KSSSK..KSSSK..",
    "...KKK....KKK...",
    "................",
    "................",
]


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def _turn45(rows):
    """Карта, повёрнутая на 45° против часовой (нос с востока на северо-восток): диагональ
    транспорта это тот же спрайт, повёрнутый, а не отдельный рисунок. Каждый пиксель берёт цвет
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
    return {"%s_%d" % (prefix, i): [r.replace("s", "S").replace("w", "W") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", CART_E, _turn45(CART_E)))
SPRITES.update(frames("rival", BONES_E, _turn45(BONES_E)))
SPRITES.update({
    # Трасса: утоптанный песчаник, по углам комки красной глины (при отражении тайла рисунок
    # тот же), посередине осколок кости.
    "race_water": [
        "SSSSSSSSSSSSSSSS",
        "SOSSSSSSSSSSSSOS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSWWSSSS",
        "SSSSSSSSSSSSWSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SOSSSSSSSSSSSSOS",
        "SSSSSSSSSSSSSSSS",
    ],
    # Второй вариант: трёхпалый след динозавра, вдавленный в глину.
    "race_water_1": [
        "SSSSSSSSSSSSSSSS",
        "SOSSSSSSSSSSSSOS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSOSSSSSSSSS",
        "SSSSSSOSSOSSSSSS",
        "SSSOSSOSOOSSSSSS",
        "SSSOOSOOOSSSSSSS",
        "SSSSOOOOSSSSSSSS",
        "SSSSSOOOSSSSSSSS",
        "SSSSSSOOSSSSSSSS",
        "SSSSSSSSSSSWSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SOSSSSSSSSSSSSOS",
        "SSSSSSSSSSSSSSSS",
    ],
    # Обочина: кустики папоротника и хвощи на песке, замедляет.
    "race_shallow": [
        "SSSSSSSSSSSSSSSS",
        "SSGSGSSSSSSSGSSS",
        "SSSGSSSSSSGSGSGS",
        "SSGKGSSSSSSGKGSS",
        "SSSSSSSGSSGSGSGS",
        "SSSSSGSGSGSSSSSS",
        "SGSSSSGKGSSSSSSS",
        "SSSSSGSGSGSSSGSS",
        "SSSGSSSSSSSSGKGS",
        "SGSGSGSSSSSSSGSS",
        "SSGKGSSSSGSGSSSS",
        "SGSGSGSSSSGKGSSS",
        "SSSSSSSSSGSGSGSS",
        "SSSSSGSSSSSSSSSS",
        "SSSSGKGSSSSSSGSS",
        "SSSSSSSSSSSSSSSS",
    ],
    # Стена: заросли джунглей, плотная листва с тёмными просветами; тележка сюда не заезжает.
    # Во втором варианте среди зелени лужа лавы.
    "race_sand": [
        "GGGGGGGGGGGGGGGG",
        "GGKGGGGGGGGKGGGG",
        "GKGKGGGGGGKGKGGG",
        "GGKGGGGWGGGKGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGKGGGGGGGGKG",
        "GGGGKGKGGGGGGKGK",
        "GGGGGKGGGGGGGGKG",
        "GWGGGGGGGKGGGGGG",
        "GGGGGGGGKGKGGGGG",
        "GGKGGGGGGKGGGGGG",
        "GKGKGGGGGGGGGWGG",
        "GGKGGGGGGGGGKGGG",
        "GGGGGGKGGGGKGKGG",
        "GGGGGKGKGGGGKGGG",
        "GGGGGGKGGGGGGGGG",
    ],
    "race_sand_1": [
        "GGGGGGGGGGGGGGGG",
        "GGKGGGGGGGGGKGGG",
        "GKGKGGGGGGGKGKGG",
        "GGKGGKKKKKGGKGGG",
        "GGGGKKOOOOKKGGGG",
        "GGGKOOOOWOOOKGGG",
        "GGGKOOWWOOOOKGGG",
        "GGGKOOOWWOOOOKGG",
        "GGGKKOOOOOWOOKGG",
        "GGGGKOOWOOOOKGGG",
        "GGGGGKKOOOKKGGGG",
        "GGKGGGGKKKGGGGGG",
        "GKGKGGGGGGGGGKGG",
        "GGKGGGGGGGGGKGKG",
        "GGGGGGGKGGGGGKGG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Препятствия: глыба лавы (чёрный камень, в трещинах светится жар, край оплавлен) и плетёная
    # корзина сверху (костяной обод, плетение в клетку, внутри плоды).
    "race_rock": [
        "................",
        "................",
        "......KKKK......",
        "....KKOOKKKK....",
        "...KOOKKKKOOK...",
        "..KOKKKWKKKKOK..",
        "..KOKKOKKKOKKK..",
        ".KKKKOOKKOOKKOK.",
        ".KOKKKOOOOKKKOK.",
        ".KOKKKKOWKKKKKK.",
        "..KKKOKKOKKKOK..",
        "..KKOOKKKOKOO...",
        "....KKOKKKK.....",
        "......KKK.......",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWSKSKSKWK...",
        "...KWKOOGOSWK...",
        "...KWSOGOOKWK...",
        "...KWKOOOGSWK...",
        "...KWSGOOOKWK...",
        "...KWKSKSKSWK...",
        "....KWWWWWWK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    # Маячок на кромке трассы: костёр в кольце камней, искры по сторонам; украшение без
    # столкновений.
    "race_buoy": [
        "................",
        "................",
        "................",
        ".......O........",
        "......KKKK......",
        ".....KWKKWK.....",
        "....KKOOOOKK....",
        "...OKWOWWOKK.O..",
        "....KKOWWOWK....",
        "....KKOOOOKK....",
        ".....KWKKWK.....",
        "......KKKK......",
        "........O.......",
        "................",
        "................",
        "................",
    ],
    # Финиш: шахматная полоса из костяных и обожжённых плиток поперёк трассы, тайл кладётся
    # вертикальной полосой.
    "race_finish": [
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), "размер карты %s" % _name
    assert set("".join(_rows)) <= set("KOSGW."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import dinosaurs8
        dinosaurs8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
