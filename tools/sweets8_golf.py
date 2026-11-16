#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Сладости» (#137): зеркало словаря `GOLF` из `pixel_sprites.py` и
модуля космоса `space8_golf.py`, те же ключи и размеры карт. Пряничный человечек с клюшкой
лицом вправо в трёх кадрах (0 стойка у мяча, 1 замах, клюшка за головой, 2 проводка, клюшка
над передним плечом); клюшка это карамельная трость с красным крюком. Мяч шар жвачки 8×8
(белый блик сверху и красный бок снизу видны при вращении), лунка формочка для кекса 16×8
(край на 2 px над землёй, гофрированная стенка), флаг-леденец 16×24 палочкой в колонке 3:
спираль леденца сверху, под ней розовый вымпел. Земля: бисквит с посыпкой (`golf_sand` верхний
тайл с чёрной кромкой, `golf_sand_inner` толща), грин и ти это торт под белой глазурью
(`golf_deck`, под ним слои крема и коржей `golf_hull`), вместо моря розовый сироп `golf_sea`
(гребни сверху, над ними прозрачно), всплеск `golf_splash`. Пропы: пушка с попкорном
`golf_cannon` и коробка с бантом `golf_chest`; глазурь, торт и пропы служат и сценой файтинга.
Палитра `sweets8.PALETTE`: K чёрный, W глазурь, G пряник, R мармелад, P розовое.

    python3 tools/sweets8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Бисквит: пряничный мякиш, поры, крупинки сахара, красная и розовая посыпка.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGPGGGG",
    "GGGWGGGGGGGGGGGG",
    "GGGGGGGGGGKKGGGG",
    "GGGGGGRGGGGGGGGG",
    "GGGGGGGGGGGGGGWG",
    "GKGGGGGGGGGGGGGG",
    "GGGGGGGGGPGGGGGG",
    "GGGGWGGGGGGGGGGG",
    "GGGGGGGGGGGGKGGG",
    "GGGGGGGKGGGGGGGG",
    "GGPGGGGGGGGGGGRG",
    "GGGGGGGGGGWGGGGG",
    "GGGGGKGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
]

# Торт в разрезе: розовый крем и пряничные коржи слоями, между ними джем и шоколад. Не белый
# и не сплошь пряничный: на нём стоят бойцы файтинга, пряничный человечек должен читаться.
HULL = [
    "PPPPPPPPPPPPPPPP",
    "PPWPPPPPPPPPPRPP",
    "PPPPPPPPPPPPPPPP",
    "RRRRRRRRRRRRRRRR",
    "GGGGGGGGGGGGGGGG",
    "GGGKGGGGGGGWGGGG",
    "GGGGGGGGGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
    "PPPPPPPPPPPPPPPP",
    "PPPPPRPPPPWPPPPP",
    "PPPPPPPPPPPPPPPP",
    "RRRRRRRRRRRRRRRR",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGWGGGGGKGG",
    "GGGGGGGGGGGGGGGG",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Пряничный человечек: круглая голова без шеи, завиток глазури на макушке, красный бант,
    # две пуговицы, кайма глазури на кисти и ступнях. Клюшка в тех же пикселях, что у космоса.
    "golf_hero_0": [
        "................",
        "....KKKKK.......",
        "...KWGWGWK......",
        "..KGGGGKGGK.....",
        "..KGGGGGGGK.....",
        "..KGGGGWWGK.....",
        "...KGGGGGK......",
        "...KRRKRRKK.....",
        "...KGGGWGGGK....",
        "...KGGGGGKWK....",
        "...KGGGWGK.K....",
        "....KGGGGK..K...",
        "....KGGGGK...K..",
        "....KGKKGK...K..",
        "...KWWKKWWK.KRK.",
        "...KKKK.KKK.KKK.",
    ],
    "golf_hero_1": [
        "KRK.............",
        "KKK.KKKKK.......",
        ".K.KWGWGWK......",
        ".KKGGGGKGGK.....",
        "..KWGGGGGGK.....",
        "..KGGGGWWGK.....",
        "..KGGGGGGK......",
        "...KRRKRRK......",
        "...KGGGWGGK.....",
        "...KGGGGGGK.....",
        "...KGGGWGK......",
        "....KGGGGK......",
        "....KGGGGK......",
        "....KGKKGK......",
        "...KWWKKWWK.....",
        "...KKKK.KKK.....",
    ],
    "golf_hero_2": [
        ".............KRK",
        "....KKKKK....KKK",
        "...KWGWGWK..K...",
        "..KGGGGKGGKK....",
        "..KGGGGGGGKWK...",
        "..KGGGGWWGKGK...",
        "...KGGGGGKGK....",
        "...KRRKRRGK.....",
        "...KGGGWGGK.....",
        "...KGGGGGK......",
        "...KGGGWGK......",
        "....KGGGGK......",
        "....KGGGGK......",
        "...KGK..KGK.....",
        "...KWK..KWWK....",
        "...KK....KKK....",
    ],
    # Мяч: шар жвачки 8×8, розовый с белым бликом сверху и красным боком снизу.
    "golf_ball": [
        "..KKKK..",
        ".KPWWPK.",
        "KPWWPPPK",
        "KPPPPPPK",
        "KPPPPPRK",
        "KPPPPRRK",
        ".KRRRRK.",
        "..KKKK..",
    ],
    # Лунка: формочка для кекса сбоку, гофрированный край над землёй на 2 px, красные складки
    # бумаги на стенке, сверху тёмный проём.
    "golf_cup": [
        ".KKK........KKK.",
        "KWWWK......KWWWK",
        "KWWKKKKKKKKKKWWK",
        "KWRKKKKKKKKKKRWK",
        ".KWRWWRWWRWWRWK.",
        ".KWRWWRWWRWWRWK.",
        "..KRWWRWWRWWRK..",
        "..KKKKKKKKKKKK..",
    ],
    # Флаг лунки: леденец-спираль на полосатой палочке в колонке 3, под ним розовый вымпел.
    "golf_flag": [
        "..KKK...........",
        ".KWWWK..........",
        "KWRRRWK.........",
        "KWRWRWK.........",
        "KWWWRWK.........",
        ".KRRRK..........",
        "..KKK...........",
        "...KKKKKKKK.....",
        "...RPPPPPPPK....",
        "...RPWWPPPPPPK..",
        "...WPPPPPPPK....",
        "...RKKKKKKK.....",
    ] + ["...R............", "...R............", "...W............"] * 4,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[4]],
    # Грин и ти: чёрная кромка, полоса белой глазури с потёками на крем, под ней слои торта.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "WWWWWWWWWWWWWWWW", "PWWPPPPWPPPPWWPP"] + HULL[3:],
    "golf_hull": HULL,
    # Розовый сироп: тягучие наплывы с белым бликом сверху (над ними прозрачно), малиновая
    # толща с пузырьками.
    "golf_sea": [
        "..PPP.....PPP...",
        ".PWWPP...PWWPP..",
        "PPWPPPPPPPWPPPPP",
        "PPPPPPPPPPPPPPPP",
        "PPPRRPPPPPPRRPPP",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRPRRRRR",
        "RRPRRRRRRPWPRRRR",
        "RPWPRRRRRRPRRRRR",
        "RRPRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRPRRRRRRKRR",
        "RRRRRRRRRRRRRRRR",
        "RRRKRRRRRRRPRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
    ],
    # Всплеск сиропа: капли вверх, розовый купол с белым бликом и малиновой глубиной.
    "golf_splash": [
        "................",
        "................",
        "......P..P......",
        "...P..P..P..P...",
        "...P.PPWWPP.P...",
        ".P...PWWWWP...P.",
        ".P..PPWWWWPP..P.",
        "....PWWPPWWP....",
        "...PPWPRRPWPP...",
        "..PPWPRRRRPWPP..",
        ".PPWWPRRRRPWWPP.",
        "PPPPPPPPPPPPPPPP",
        "................",
        "................",
        "................",
        "................",
    ],
    # Пушка с попкорном: полосатый ствол вправо (как стакан попкорна), из дула сыплются белые
    # хлопья, колесо из печенья с шоколадной крошкой, упор сзади.
    "golf_cannon": [
        "................",
        ".............W..",
        "...........W.WW.",
        "............WW.W",
        "...KKKKKKKKKKKK.",
        "..KRWWRWWRWWRKWW",
        "..KRWWRWWRWWRKWW",
        "..KRWWRWWRWWRKW.",
        "...KKKKKKKKKKKK.",
        "..KGKKGGGGGK....",
        ".KGKKGGKGGGGK...",
        "KGK.KGGGGGKGK...",
        "KKK.KGKGGGGGK...",
        "....KGGGGKGGK...",
        ".....KGGGGGK....",
        "......KKKKK.....",
    ],
    # Коробка с бантом: розовая коробка с крышкой, красная лента крест-накрест, пышный бант.
    "golf_chest": [
        "................",
        "...KK......KK...",
        "..KRRKK..KKRRK..",
        "..KRRRRKKRRRRK..",
        "...KKRRRRRRKK...",
        ".KKKKKKRRKKKKKK.",
        ".KPPPPKRRKPPPPK.",
        ".KPWPPKRRKPPWPK.",
        ".KKKKKKKKKKKKKK.",
        "..KPPPKRRKPPPK..",
        "..KPWPKRRKPPPK..",
        "..KRRRRRRRRRRK..",
        "..KPPPKRRKPWPK..",
        "..KPPPKRRKPPPK..",
        "..KPPPKRRKPPPK..",
        "..KKKKKKKKKKKK..",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KWGRP."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import sweets8
        sweets8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
