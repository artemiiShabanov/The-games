#!/usr/bin/env python3
"""8-bit «Динозавры», платформер (#137): зеркало блока «Космос» в `pixel_sets_extra.py`, те же
слоты и размеры карт. Пещерный человек в оранжевой шкуре через плечо, с костью в лохматых
волосах (герой), прямоходящий раптор (ходячий враг), птеродактиль (летун), аммонит (монета),
рогатый череп на шесте (чекпоинт), тотем со шкурой (финиш), красная глина в трещинах под
зелёной подстилкой (земля), хребет из позвонков (платформа), дым вулкана с отсветом лавы
(облака). Палитра в `dinosaurs8.py`: K чёрный, O шкура и глина, S кожа и дерево, G зелень,
W кость.

    python3 tools/dinosaurs8_platformer.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sets_extra import DOTS, _pad  # noqa: E402

# Пещерный человек: чёрная копна с пучком, сквозь пучок продета кость (два набалдашника по
# сторонам макушки), лицо вправо с тяжёлой челюстью, шкура наискось через переднее плечо,
# заднее плечо голое, рваный подол, босые ноги. Верх в 13 строк общий для кадров бега.
_CAVEMAN = [
    "..W...KKK..W....",
    "..WWWWWWWWWW....",
    "..W.KKKKKK.W....",
    "...KKKKKKKKK....",
    "...KKKSSSSSK....",
    "...KKSSSKSSK....",
    "...KKSSSSSSSK...",
    "...KKSSSKKSK....",
    "....KKSSSSK.....",
    "...KSSSSOOOSK...",
    "..KSSKSOOOOKSK..",
    "..KSSKOOKOOKSK..",
    "....KOOKOOOK....",
]

SPRITES = {
    "hero_run_0": _CAVEMAN + [
        "....KSSKKSSK....",
        "...KSSK..KSSK...",
        "...KKKK..KKKK...",
    ],
    "hero_run_1": _CAVEMAN + [
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        ".....KKKKKK.....",
    ],
    "hero_run_2": _CAVEMAN + [
        "....KSSKKSSK....",
        "..KSSK....KSSK..",
        "..KKKK....KKKK..",
    ],
    # Прыжок: руки вскинуты в стороны, ноги поджаты.
    "hero_jump": [
        "..W...KKK..W....",
        "..WWWWWWWWWW....",
        "..W.KKKKKK.W....",
        "...KKKKKKKKK....",
        "...KKKSSSSSK....",
        "...KKSSSKSSK....",
        "...KKSSSSSSSK...",
        "KSKKKSSSKKSK.KSK",
        "KSSKKKSSSSK.KSSK",
        ".KSSSSSSOOOSSSK.",
        "..KKKKSOOOOKKK..",
        ".....KOOKOOK....",
        "....KOOKOOOK....",
        "....KSSKKSSK....",
        "...KSSK..KSSK...",
        "...KKK....KKK...",
    ],
    # Дэш: бросок рыбкой, голова и рука впереди, ноги вытянуты назад, слева полосы скорости
    # цветом W.
    "hero_dash": [
        DOTS,
        DOTS,
        DOTS,
        DOTS,
        "..........W.KK.W",
        "..........WWWWWW",
        "WW........WKKKKW",
        ".........KKKKKKK",
        "WWW.KKKKKKKSSKSK",
        "..KSSKOOOKKSSSSS",
        "WWKSSKOOKOKSSKK.",
        "..KKKKOOOOSSSSSK",
        "WWW..KKKKKKKKKK.",
        DOTS,
        DOTS,
        DOTS,
    ],
    # Раптор: стоит прямо мордой влево, длинная пасть с зубами, светлое брюхо, короткая лапка,
    # хвост назад. Два кадра шага: ноги и кончик хвоста.
    "enemy_0": [
        DOTS,
        "...KKKKK........",
        "..KGGGGGK.......",
        ".KGGWKGGGK......",
        "KGGGGGGGGK......",
        "KWKWKGGGGK......",
        ".KKKKSGGGK......",
        "....KSSGGK....K.",
        "..KKKSSGGGK..KGK",
        "..KGKSSGGGGKKGGK",
        "...KKSSGGGGGGGK.",
        "....KSSGGGGGKK..",
        "....KGGKKGGK....",
        "....KGK..KGK....",
        "...KGGK.KGGK....",
        "...KKKK.KKKK....",
    ],
    "enemy_1": [
        DOTS,
        "...KKKKK........",
        "..KGGGGGK.......",
        ".KGGWKGGGK......",
        "KGGGGGGGGK......",
        "KWKWKGGGGK......",
        ".KKKKSGGGK......",
        "....KSSGGK......",
        "..KKKSSGGGK.....",
        "..KGKSSGGGGKKKK.",
        "...KKSSGGGGGGGGK",
        "....KSSGGGGGKKK.",
        "....KGGKKGGK....",
        "...KGK....KGK...",
        "..KGGK...KGGK...",
        "..KKKK...KKKK...",
    ],
    # Птеродактиль: летит влево, клюв костяной, гребень назад, перепонка крыла светлее.
    # Кадр 0 крыло вверх, кадр 1 крыло вниз.
    "parrot_0": _pad([
        DOTS,
        DOTS,
        "........KKK.....",
        ".......KOOOK....",
        ".......KOSOOK...",
        "....KK..KOSOOK..",
        "..KKOOK.KOSSOK..",
        ".KWWOKOKKOSSOK..",
        "KWWKOOOOOOOOOOKK",
        ".KK.KKOOOOOOKK..",
        "......KKOKOK....",
        "........K.K.....",
    ]),
    "parrot_1": _pad([
        DOTS,
        DOTS,
        DOTS,
        DOTS,
        "....KK..........",
        "..KKOOK.........",
        ".KWWOKOKKKKKKK..",
        "KWWKOOOOOOOOOOKK",
        ".KK.KKOSSSOOKK..",
        ".....KOSSSOK....",
        "......KOSSOK....",
        ".......KOSOK....",
        "........KOOK....",
        ".........KK.....",
    ]),
    # Аммонит: закрученная раковина с бликом и устьем.
    "coin": _pad([
        DOTS, DOTS, DOTS,
        "....KKKKKK......",
        "...KSSWWSSK.....",
        "..KSSKKKKSSK....",
        "..KSKSSSSKSK....",
        "..KSKSKKSKSK....",
        "..KSKSSKSKSK....",
        "..KSSKKKSKSKK...",
        "...KSSSSSKSOOK..",
        "....KKKKKKKKK...",
    ]),
    # Чекпоинт: рогатый череп на шесте, шест вбит в кучу камней.
    "checkpoint": [
        DOTS,
        "..KK.......KK...",
        "..KWK.....KWK...",
        "...KWKKKKKWK....",
        "...KWWWWWWWK....",
        "...KWKKWKKWK....",
        "...KWKKWKKWK....",
        "....KWWWWWK.....",
        ".....KWKWK......",
        ".....KKKKK......",
        "......KSK.......",
        "......KSK.......",
        "......KSK.......",
        "......KSK.......",
        "....KKSSSKK.....",
        "...KSSSSSSSK....",
    ],
    # Финиш: тотем из двух личин с пучком листьев наверху, на перекладине висит шкура с
    # пятнами и рваным краем.
    "flag": [
        "....KGKGKGK.....",
        "....KGGGGGK.....",
        "..KKKKKKKKKKKKKK",
        "..KSSSSSSSKOOOOK",
        "..KSKKSKKSKOKOOK",
        "..KSSSSSSSKOOOOK",
        "..KSWKWKWSKOOKOK",
        "..KKKKKKKKKOOOOK",
        "..KOOOOOOOKOKOOK",
        "..KOKKOKKOKOOOOK",
        "..KOOOOOOOKOKOKK",
        "..KOWKWKWOKK.K..",
        "..KKKKKKKKK.....",
        "...KSSSSSK......",
        "..KSSSSSSSK.....",
        "..KKKKKKKKK.....",
    ],
    # Земля: зелёная подстилка сверху, под ней красная глина в трещинах с камешками.
    "ground": [
        "GGGGGGGGGGGGGGGG",
        "GOGGGOOGGGOGGGOG",
        "OOOOOOOOOOOOOOOO",
        "OSOOOOOKOOOOOSOO",
        "OOOOOOOKOOOOOOOO",
        "KKKOOOKKKKOOOOKK",
        "OOOKKKOOOOKKKKOO",
        "OOOOKOOOOOOOKOOO",
        "OSOOKOOOSOOOKOOO",
        "OOOOKOOOOOOOKOOO",
        "OOKKKKOOOOOKKKOO",
        "KKOOOOKKKKKOOOKK",
        "OOOOOOOOKOOOOOOO",
        "OOSOOOOOKOOOOSOO",
        "OOOOOOOOKOOOOOOO",
        "OOOOOOOKKOOOOOOO",
    ],
    # Глубже та же глина, в ячейке между трещин вмурована кость.
    "ground_inner": [
        "OOOOOOOKOOOOOOOO",
        "OOOOOOOKOOOOOOOO",
        "OOOOOOOKOOOOOOOO",
        "OSOOOOOKOOOOOSOO",
        "OOOOOOOKOOOOOOOO",
        "KKKOOOKKKKOOOOKK",
        "OOOKKKOOOOKKKKOO",
        "OOOOKOWOOOWOKOOO",
        "OOOOKOWWWWWOKOOO",
        "OOOOKOWOOOWOKOOO",
        "OOKKKKOOOOOKKKOO",
        "KKOOOOKKKKKOOOKK",
        "OOOOOOOOKOOOOOOO",
        "OOSOOOOOKOOOOSOO",
        "OOOOOOOOKOOOOOOO",
        "OOOOOOOKKOOOOOOO",
    ],
    # Платформа: хребет из позвонков, два позвонка на плитку.
    "platform": _pad([
        "WWWWWWWKWWWWWWWK",
        "WWWWWWWKWWWWWWWK",
        "SWWWWWSKSWWWWWSK",
        "KSSSSSKKKSSSSSKK",
        ".KKKKK...KKKKK..",
    ]),
    # Облака: клубы вулканического дыма, снизу отсвет лавы.
    "cloud_small": _pad([
        DOTS, DOTS, DOTS,
        ".......KKK......",
        "....KKKWWWK.....",
        "...KWWWWWWWKK...",
        "..KWWWWSWWWWWK..",
        "..KWSWWWWWSWWK..",
        "..KSSSWSSSSSSK..",
        "...KOSSSOOSOK...",
        "....KKKKKKKK....",
    ]),
    "cloud_big": _pad([
        "." * 32, "." * 32,
        "............KKKKK...............",
        "..........KKWWWWWKK.....KKK.....",
        ".....KKKKKWWWWWWWWWK..KKWWWKK...",
        "....KWWWWWWWWSWWWWWWKKWWWWWWWK..",
        "...KWWWSWWWWWWWWWWWWWWWWWSWWWWK.",
        "..KWWWWWWWWWSWWWWWSWWWWWWWWWWWK.",
        "..KWSWWWWSWWWWWWWWWWWWSWWWWSWWK.",
        "..KSSSWSSSSSWWSSSSWSSSSSSWSSSSK.",
        "...KOSSSSOOSSSSSOOSSSSOOSSSSOK..",
        "....KKOOOOKKOOOOKKKOOOKKKOOKK...",
        "......KKKK..KKKK...KKK...KK.....",
    ], w=32),
}

if __name__ == "__main__":
    import dinosaurs8
    if "--preview" in sys.argv:
        dinosaurs8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES)
