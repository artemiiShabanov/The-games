#!/usr/bin/env python3
"""8-bit «Супергерои», гонки (вид сверху, #137): зеркало `space8_racing.py` и раздела «Гонки ×
8-bit» в `pixel_sprites.py`. Те же слоты и роли, что у пиратов: `race_water*` это трасса (асфальт
улицы, демка мешает два варианта и отражает их, поэтому рисунок симметричен), `race_shallow`
обочина, которая тормозит (битый кирпич и трещины на асфальте), `race_sand*` стена (кирпичная
крыша квартала, туда не заехать; во втором варианте световой люк), `race_rock` и `race_barrel`
препятствия (обломок бетона с арматурой и гидрант), `race_buoy` дорожный конус на кромке,
`race_finish` финишная полоса с прозрачными краями. Транспорт в 8 направлениях из двух карт (на
восток и на северо-восток) поворотами на 90°; индекс по часовой на экране: 0 E, 1 SE, 2 S, 3 SW,
4 W, 5 NW, 6 N, 7 NE. Диагональ это прямой кадр, повёрнутый на 45°, отдельно не рисуется. Герой
на синей спортивной машине с жёлтой полосой и спойлером, соперник на красно-чёрной машине
злодея с открытым мотором и острым носом. Парусов и мачт нет: это автомобили на четырёх колёсах.

    python3 tools/superheroes8_racing.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Машина героя: синий кузов, сзади жёлтый спойлер во всю ширину, тёмное стекло кабины с бликом,
# по капоту жёлтая гоночная полоса, фары на носу, четыре колеса с колпаками по бортам. Сзади
# выхлоп (строчная `y` становится жёлтым, как пена `w` у шлюпки).
HERO_E = [
    "................",
    "................",
    "...KKK....KKK...",
    "...KGK....KGK...",
    ".KKKKKKKKKKKKK..",
    ".KYBBBBBBBBBBBK.",
    ".KYBBKGGKKBBBBYK",
    "yKYBBKGKKKYYYYBK",
    "yKYBBKKKKKYYYYBK",
    ".KYBBKKKKKBBBBYK",
    ".KYBBBBBBBBBBBK.",
    ".KKKKKKKKKKKKK..",
    "...KGK....KGK...",
    "...KKK....KKK...",
    "................",
    "................",
]

# Машина злодея: красный клин острым носом вперёд, кабина в чёрной раме с жёлтой щелью стекла, перед
# ней открытый серый мотор, жёлтые фары-глаза, сзади две выхлопные трубы (строчная `r` становится
# красным пламенем).
VILLAIN_E = [
    "................",
    "................",
    "..KKK....KKK....",
    "..KGK....KGK....",
    ".KKKKKKKKKKK....",
    ".KRRKKKKGGGRKK..",
    "rKRRKKKYGKGRRYK.",
    ".KRRKRRYGGGRRRRK",
    ".KRRKRRYGGGRRRRK",
    "rKRRKKKYGKGRRYK.",
    ".KRRKKKKGGGRKK..",
    ".KKKKKKKKKKK....",
    "..KGK....KGK....",
    "..KKK....KKK....",
    "................",
    "................",
]


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def _turn45(rows):
    """Карта, повёрнутая на 45° против часовой (нос с востока на северо-восток): диагональ это
    тот же спрайт, повёрнутый, а не отдельный рисунок. Каждый пиксель берёт цвет большинства из
    девяти проб, так края выходят без дыр."""
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
    return {"%s_%d" % (prefix, i): [r.replace("y", "Y").replace("r", "R") for r in out[i]] for i in range(8)}


SPRITES = {}
SPRITES.update(frames("boat", HERO_E, _turn45(HERO_E)))
SPRITES.update(frames("rival", VILLAIN_E, _turn45(VILLAIN_E)))
SPRITES.update({
    # Трасса: асфальт с тёмными выбоинами по углам (при отражении тайла рисунок тот же) и
    # короткой трещиной.
    "race_water": [
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGKKGGGG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Второй вариант: жёлтая метка разметки в центре и трещина в другом углу.
    "race_water_1": [
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
        "GGGKKGGGGGGGGGGG",
        "GGGGGKGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGYYGGGGGGG",
        "GGGGGGGYYGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GKGGGGGGGGGGGGKG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Обочина: битый кирпич с тенью и трещины на асфальте, замедляет.
    "race_shallow": [
        "GGGGGGGGGGGGGGGG",
        "GGRRGGGGGGGKGGGG",
        "GGRKGGGGGGRRKGGG",
        "GGGGGGGKGGRRKGGG",
        "GGGGGGRRGGGKGGGG",
        "GKGGGGRKGGGGGGGG",
        "GGKGGGGGGGGGGRRG",
        "GGGKRRGGGGGGGRKG",
        "GGGRRRKGGGKGGGGG",
        "GGGGRKGGGRRGGGGG",
        "GGGGGGGGGRKGGGGG",
        "GRRGGGGGGGGKGGKG",
        "GRKGGGGKGGGGKRRG",
        "GGGGGGRRKGGGGRKG",
        "GGGGGGGRGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
    ],
    # Стена: кирпичная крыша квартала, кладка со швами вразбежку; машина сюда не заезжает. Во
    # втором варианте световой люк с горящим окном.
    "race_sand": [
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "KKKKKKKKKKKKKKKK",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "KKKKKKKKKKKKKKKK",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "RRRKRRRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    "race_sand_1": [
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "RRRRRRRKRRRRRRRK",
        "KKKKKKKKKKKKKKKK",
        "RRRKGGGGGGGGKRRR",
        "RRRKGKKKKKKGKRRR",
        "RRRKGKYYKYYGKRRR",
        "KKKKGKYYKYYGKKKK",
        "RRRKGKKKKKKGKRRK",
        "RRRKGKYYKYYGKRRK",
        "RRRKGKYYKYYGKRRK",
        "KKKKGKKKKKKGKKKK",
        "RRRKGGGGGGGGKRRR",
        "RRRKKKKKKKKKKRRR",
        "RRRKRRRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    # Препятствия: обломок бетона (угловатая плита в трещинах, из края торчит красная арматура)
    # и пожарный гидрант сверху (красный корпус, жёлтая крышка, два боковых патрубка, лужица).
    "race_rock": [
        "................",
        "..........R.....",
        "....KKKKKKRK....",
        "...KGGGGGKRGK...",
        "..KGGGKGGGKGGK..",
        "..KGGGGKGGGGGKK.",
        ".KGGGGGGKKGGGGK.",
        ".KGKGGGGGKGGGGK.",
        ".KGGKKGGGGGGKGK.",
        "RRKGGGKGGGGGGK..",
        "..KGGGGGGGKGGK..",
        "..KKGGGGGGGGKK..",
        "....KKGGGKKK....",
        "......KKKR......",
        ".........R......",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        "......KKKK......",
        "......KYYK......",
        "....KKKRRKKK....",
        "...KRRRRRRRRK...",
        ".KKKRRKKKKRRKKK.",
        ".KYKRRKYYKRRKYK.",
        ".KYKRRKYYKRRKYK.",
        ".KKKRRKKKKRRKKK.",
        "...KRRRRRRRRK...",
        "....KKKRRKKK....",
        "......KBBK.B....",
        ".....BBBBBB.....",
        ".......BB.......",
        "................",
    ],
    # Дорожный конус на кромке трассы, вид сверху: квадратная подошва, жёлтое кольцо, красная
    # вершина. Украшение без столкновений.
    "race_buoy": [
        "................",
        "................",
        "................",
        "................",
        "....KKKKKKKK....",
        "....KRRRRRRK....",
        "....KRYYYYRK....",
        "....KRYRRYRK....",
        "....KRYRRYRK....",
        "....KRYYYYRK....",
        "....KRRRRRRK....",
        "....KKKKKKKK....",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: шахматная жёлто-чёрная полоса поперёк трассы, тайл кладётся вертикальной полосой.
    "race_finish": [
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....KKKKYYYY....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
        "....YYYYKKKK....",
    ],
})

for _name, _rows in SPRITES.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), "размер карты %s" % _name
    assert set("".join(_rows)) <= set("KBYRG."), "чужой символ в %s" % _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import superheroes8
        superheroes8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
