#!/usr/bin/env python3
"""Гольф × 8-bit, набор «Динозавры» (#137): зеркало словаря `GOLF` из `pixel_sprites.py` и модуля
`space8_golf.py`, те же ключи и размеры карт. Пещерный человек с костяной дубиной лицом вправо
в трёх кадрах (0 стойка у мяча, 1 замах, дубина за головой, 2 проводка, дубина над передним
плечом).
Мяч яйцо динозавра 8×8 в рыжих крапинах, лунка гнездо из веток 16×8 (края на 2 px над землёй,
как комингс люка, на дне скорлупа), флаг шкура на шесте 16×24, шест в колонке 3. Земля: красная
глина (`golf_sand` верхний тайл с чёрной кромкой, `golf_sand_inner` толща), подстилка грина и
ти (`golf_deck`, под ней песчаник с окаменелостями `golf_hull`), вместо моря лава `golf_sea`
(пузыри сверху, над ними прозрачно), всплеск лавы `golf_splash`. Пропы: катапульта из бревна
`golf_cannon` (бросает вправо) и гнездо с яйцами `golf_chest`; подстилка, песчаник и пропы
служат и сценой файтинга. Палитра в `dinosaurs8.py`: K чёрный, O шкура, глина и лава, S кожа,
дерево и песчаник, G зелень, W кость и скорлупа.

    python3 tools/dinosaurs8_golf.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Красная глина: рыжий грунт, чёрные трещины уголком, светлые песчинки.
SAND = [
    "KKKKKKKKKKKKKKKK",
    "OOOOOOOOOOOOOOOO",
    "OOOOOOOOOOOOSOOO",
    "OOOKOOOOOOOOOOOO",
    "OOOOKKOOOOOOOOOO",
    "OOOOOKOOOOOKOOOO",
    "OSOOOOOOOOKKOOOO",
    "OOOOOOOOOOOOOOOO",
    "OOOOOOOSOOOOOOOK",
    "KKOOOOOOOOOOOOKK",
    "OOKOOOOOOOOOOOOO",
    "OOOOOOOOKOOOSOOO",
    "OOOOSOOOKKOOOOOO",
    "OOOOOOOOOKOOOOOO",
    "OOOOOOOOOOOOOOOO",
    "OOKOOOOOOOOOOSOO",
]

# Песчаник: блоки вперевязку, в них окаменелости костью (спираль аммонита, ребро, зуб) и
# рыжие прожилки. Не рыжий и не зелёный целиком: на нём стоят бойцы файтинга, герой в шкуре
# и раптор должны читаться.
HULL = [
    "SSSSSSSKSSSSSSSS",
    "SSSWSSSKSSSSOSSS",
    "SSSSSSSKSSSSSSSS",
    "KKKKKKKKKKKKKKKK",
    "SSSKSSSSWWWSSSSS",
    "SSSKSSSWSSSWSSSS",
    "SOSKSSSWSWWWSSSS",
    "SSSKSSSSWSSSSSKS",
    "KKKKKKKKKKKKKKKK",
    "SSSSSSSSSSKSSSSS",
    "SWWWWWSSSSKSSOSS",
    "SSSSSSWSSSKSSSSS",
    "KKKKKKKKKKKKKKKK",
    "SSSSSKSSSSSSSWSS",
    "SSOSSKSSSSSSWWSS",
    "KKKKKKKKKKKKKKKK",
]

SPRITES = {
    # Стойка: шкура наискось через переднее плечо, руки вперёд и вниз, дубина утолщением у мяча.
    "golf_hero_0": [
        "...W..KK..W.....",
        "...WWWWWWWW.....",
        "...W.KKKK.W.....",
        "...KKKKKKKK.....",
        "...KKSSSSSK.....",
        "...KKSSKSSK.....",
        "...KKSSSSSSK....",
        "...KKSSKKSK.....",
        "....KKSSSK......",
        "...KSSOOOSK.....",
        "..KSKOOOOSSK....",
        "..KSKOOKOOKSK...",
        "...KKOOOOK.KWK..",
        "....KSKKSK..KWKK",
        "...KSSKKSSKKWWWK",
        "...KKKK.KKKKWWWK",
    ],
    # Замах: голова довёрнута, обе руки за затылком, дубина торчит вверх за спиной.
    "golf_hero_1": [
        "WWK.W..KK..W....",
        "WWWKWWWWWWWW....",
        "KWWKW.KKKK.W....",
        ".KWKKKKKKKKK....",
        "..KSKKSSSSSK....",
        "..KSKKSSKSSK....",
        "..KSKKSSSSSSK...",
        "..KSKKSSKKSK....",
        "..KSSKKSSSK.....",
        "...KSSOOOSK.....",
        "....KOOOOOK.....",
        "....KOOKOOK.....",
        "....KOOOOK......",
        "....KSKKSK......",
        "...KSSKKSSK.....",
        "...KKKK.KKK.....",
    ],
    # Проводка: руки вынесены перед лицом, дубина над передним плечом, ноги врозь.
    "golf_hero_2": [
        "...W..KK..W..KWW",
        "...WWWWWWWW.KWWW",
        "...W.KKKK.WKWWK.",
        "...KKKKKKKKKWK..",
        "...KKSSSSSKSK...",
        "...KKSSKSSKSK...",
        "...KKSSSSSKSK...",
        "...KKSSKKSKSK...",
        "....KKSSSKSSK...",
        "...KSSOOOSSK....",
        "....KOOOOOK.....",
        "....KOOKOOK.....",
        "....KOOOOK......",
        "...KSK..KSK.....",
        "...KSK..KSSK....",
        "...KK....KKK....",
    ],
    # Мяч: яйцо динозавра 8×8, костяная скорлупа в рыжих крапинах (видны при вращении), снизу
    # тёплая тень.
    "golf_ball": [
        "..KKKK..",
        ".KWWWWK.",
        "KWWOWWWK",
        "KWWWWWOK",
        "KWOWWWWK",
        "KWWWWOSK",
        ".KWWSSK.",
        "..KKKK..",
    ],
    # Лунка: гнездо сбоку, края из веток на 2 px над землёй, в чаше осколки скорлупы.
    "golf_cup": [
        ".KSK........KSK.",
        "KSSGK......KSSSK",
        "KSKSSKKKKKKGSKSK",
        "KSSKKKKKKKKKKSSK",
        ".KSSKKKKKKKKSSK.",
        ".KSKSKKWWKKSKSK.",
        "..KSSSKWWKSSSK..",
        "..KKKKKKKKKKKK..",
    ],
    # Флаг лунки: шест S в колонке 3 до низа, сверху костяной набалдашник, рваная шкура
    # с пятном и следом когтей.
    "golf_flag": [
        "...WKKKKKKKK....",
        "...SOOOOOOOOK...",
        "...SOOKOOWOOOK..",
        "...SOKKOWOWOOOK.",
        "...SOOOOWOWOOK..",
        "...SOOOOOOOOK...",
        "...SKOKKOOKK....",
    ] + ["...S............"] * 17,
    "golf_sand": SAND,
    "golf_sand_inner": SAND[1:] + [SAND[7]],
    # Подстилка грина и ти: чёрная кромка, зелёная полоса папоротника, бахрома по песчанику.
    "golf_deck": ["KKKKKKKKKKKKKKKK", "GGGGGGGGGGGGGGGG", "GSGGSSGKGSGGSSGS"] + HULL[3:],
    "golf_hull": HULL,
    # Лава: пузыри и раскалённая кромка сверху (над ними прозрачно), рыжая толща с чёрными
    # плитами корки и светлыми искрами.
    "golf_sea": [
        "..........SS....",
        "...SS....SWWS...",
        "SSSWWSSSSSWWSSSS",
        "WWSSSSSSWWSSSSSS",
        "SSSOOSSSSSSOOOSS",
        "OOOOOOOOOOOOOOOO",
        "OOKKOOOOOOSOOOOO",
        "OKKKKOOOOOOOOOOO",
        "OOKKOOOOOOOOKKOO",
        "OOOOOOOSOOOKKKKO",
        "OOOOOOOOOOOOKKOO",
        "OOSOOOOOOOOOOOOO",
        "OOOOOOKKKOOOOOOO",
        "OOOOOOOKKOOOSOOO",
        "OOOOOOOOOOOOOOOO",
        "OOOOOOOOOOOOOOOO",
    ],
    # Всплеск лавы: брызги вверх, рыжий купол с раскалённым ядром.
    "golf_splash": [
        "................",
        "................",
        "......O...S.....",
        "....S..W.O..O...",
        "......OSSSO.....",
        "...O.OSWWWSO.S..",
        ".....OSWWWSO....",
        "..S.OOSWWWSOO.O.",
        "....OSSWWWSSO...",
        "...OOSSSWSSSOO..",
        "..OOOSSSSSSSOOO.",
        ".OOOOOOOOOOOOOOO",
        "................",
        "................",
        "................",
        "................",
    ],
    # Катапульта из бревна: рычаг наискось вправо-вверх, в ложке камень, стойка, рама на
    # двух валунах.
    "golf_cannon": [
        "................",
        "................",
        "................",
        "................",
        "...........KKK..",
        "..........KWWWK.",
        ".........KKWWWK.",
        ".......KKSSSSSK.",
        ".....KKSSSKKKK..",
        "...KKSSKSSK.....",
        "..KSSKKKSSK.....",
        ".KKKKKKKSSKKKKK.",
        ".KSSKSSSSSSKSSK.",
        ".KKWWKKKKKKWWKK.",
        ".KWWWWK..KWWWWK.",
        "..KKKK....KKKK..",
    ],
    # Гнездо с яйцами: три яйца в крапинах над плетёной чашей из веток с листом.
    "golf_chest": [
        "................",
        "................",
        "................",
        ".......KK.......",
        "......KWWK......",
        "..KK.KWOWWK.KK..",
        ".KWWKKWWWWKKWWK.",
        ".KWOWKWWOWKWOWK.",
        "KSKWWKWWWWKWWKSK",
        "KSSKKSKKKKSKKSSK",
        "KSKSSSSKSSSSKGSK",
        "KSSSKSSSSKSSGGKK",
        ".KSKSSSKSSSSKSK.",
        ".KSSSSKSSKSSSSK.",
        "..KSSKSSSSKSSK..",
        "...KKKKKKKKKK...",
    ],
}
for _name, _rows in SPRITES.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
    assert set("".join(_rows)) <= set("KOSGW."), "чужой символ в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import dinosaurs8
        dinosaurs8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
