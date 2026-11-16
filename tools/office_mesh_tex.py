#!/usr/bin/env python3
"""Текстуры уровня «Офиса» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок.
Стиль первой PlayStation: низкое разрешение, в которое втиснуто как можно больше деталей. Все
плитки стыкуются по краям: каждый пиксель ставится по модулю размера. Цвета из палитры
`office16.PALETTE` и те же, что у моделей в `office_mesh_chars.py` и `office_mesh_big.py`.

Слоты по ролям: `sand` серый ковролин плитками, ворс соседних плиток повёрнут на четверть
оборота, на нём скрепки, конфетти дырокола и стикер; `planks` ламинат под светлый дуб, планки
вразбежку с волокном и сучками; `water` основание мира, у офиса это твердь: тёмно-зелёный
ковролин опенспейса до горизонта с корпоративным узором из ромбов и синих вставок (не жидкость,
зыби нет); `rock` стена картотечных шкафов: ящики 16×8 с ручкой, рамкой ярлыка и стикерами;
`sail` растяжка из листов бумаги в линейку с красным полем и скрепками (шов по краю листа, как
у фольги космоса); `grass` зелёный ковролин с длинным ворсом; `road` линолеум коридора: швы
полотен, укатанные следы колёсиков там же, где колеи у пиратов, пунктир жёлтой ленты по оси;
`mud` тёмный ковёр с лужами пролитого кофе, заметно темнее трассы; `wind` стрелки разгона на
прозрачном; `sky` панорама по горизонтали: потолок с лампами, лента окон с городом, ряды
перегородок с мониторами и фикусами, внизу полоса ковролина в цвет основания.

    python3 tools/office_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from office_mesh_chars import (NAVY, SEA, SEA_L, AQUA, SKY, WHITE, GREY, GREY_D, GOLD, BRASS, GOLD_L,  # noqa: E402
                               METAL, METAL_L, DARK, DARK_L, DARK_D, RED, COFFEE)
from office_mesh_big import GREEN, GREEN_D, GREEN_L, CARD, CARD_D, TAPE  # noqa: E402

rgb, mul = lm.rgb, lm.mul

PILE, PILE_D, PILE_L = rgb("A2A9B8"), rgb("7E8698"), rgb("C0C6D2")  # серый ковролин
BASE, BASE_D, BASE_L = rgb("2A605C"), rgb("1C4644"), rgb("3C7C72")  # ковролин основания мира
LINO, LINO_D, LINO_L = rgb("8A93A6"), rgb("666E82"), rgb("A8B0C0")  # линолеум коридора


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def clip(a, x, y, flat=True):
    """Скрепка: вытянутая петля из светлой проволоки с тенью под ней."""
    if flat:
        wrect(a, x, y, 5, 1, WHITE), wrect(a, x + 1, y + 2, 4, 1, GREY)
        wpx(a, x + 5, y + 1, WHITE), wpx(a, x, y + 1, GREY)
        wrect(a, x + 1, y + 3, 5, 1, PILE_D)
    else:
        wrect(a, x, y, 1, 5, WHITE), wrect(a, x + 2, y + 1, 1, 4, GREY)
        wpx(a, x + 1, y + 5, WHITE), wpx(a, x + 1, y, GREY)
        wrect(a, x + 3, y + 1, 1, 5, PILE_D)


def tex_sand():
    """Серый ковролин плитками 32×32: ворс соседних плиток повёрнут на четверть оборота, швы
    едва видны; скрепки, белые кружки от дырокола и один жёлтый стикер."""
    a = lm.Atlas(64, 64, 131)
    for y in range(64):
        for x in range(64):
            turned = ((x // 32) + (y // 32)) % 2 == 1
            u, v = (y, x) if turned else (x, y)
            k = (1.07, 0.98, 0.92, 1.02)[(u + (v // 2) % 2 * 2) % 4]
            k *= 1.0 + 0.04 * math.sin(x * math.pi / 16.0 + 2.0 * math.sin(y * math.pi / 32.0))
            a.px(x, y, mul(PILE, k * (0.96 if turned else 1.0)))
    for s in (0, 32):
        wrect(a, s, 0, 1, 64, PILE_D), wrect(a, s + 1, 0, 1, 64, mul(PILE_L, 0.96))
        wrect(a, 0, s, 64, 1, PILE_D), wrect(a, 0, s + 1, 64, 1, mul(PILE_L, 0.96))
    for _ in range(150):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), PILE_D if a.rng.random() < 0.6 else PILE_L)
    # Конфетти дырокола: белые точки с тенью снизу справа.
    for _ in range(11):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, WHITE), wpx(a, x + 1, y, GREY), wpx(a, x + 1, y + 1, PILE_D)
    clip(a, 9, 12), clip(a, 44, 20, False), clip(a, 22, 49), clip(a, 52, 54, False)
    # Упавший стикер с загнутым уголком.
    wrect(a, 38, 40, 5, 5, GOLD), wrect(a, 38, 40, 5, 1, GOLD_L)
    wpx(a, 42, 44, BRASS), wpx(a, 41, 44, BRASS), wpx(a, 42, 43, BRASS)
    wrect(a, 39, 45, 5, 1, PILE_D), wrect(a, 43, 41, 1, 4, PILE_D)
    wrect(a, 39, 42, 3, 1, BRASS)
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_planks():
    """Ламинат под светлый дуб: планки 32×8 вразбежку, у каждой свой тон, волокно вдоль, сучки,
    тёмный шов со светлой фаской."""
    a = lm.Atlas(64, 64, 133)
    a.rect(0, 0, 64, 64, CARD)
    for row in range(8):
        y0 = row * 8
        off = (row * 20) % 32
        for col in range(2):
            x0 = off + col * 32
            tone = a.rng.uniform(0.9, 1.1)
            wrect(a, x0, y0, 32, 8, mul(CARD, tone))
            # Волокно: длинные волнистые прожилки вдоль планки.
            for j in (2, 4, 6):
                ph = a.rng.uniform(0.0, 6.0)
                for i in range(1, 32):
                    dy = int(round(0.8 * math.sin(i * math.pi / 8.0 + ph)))
                    if a.rng.random() < 0.8:
                        wpx(a, x0 + i, y0 + j + dy, mul(CARD_D, tone * (1.08 if j == 4 else 1.2)))
            for _ in range(5):
                wrect(a, x0 + a.rng.randrange(2, 26), y0 + a.rng.randrange(2, 7), a.rng.randrange(2, 5), 1,
                      mul(TAPE, tone * 0.94))
            if a.rng.random() < 0.45:
                kx, ky = x0 + a.rng.randrange(5, 26), y0 + 4
                wrect(a, kx - 1, ky - 1, 4, 3, mul(CARD_D, tone))
                wrect(a, kx, ky, 2, 1, mul(COFFEE, 1.1))
                wpx(a, kx - 2, ky, mul(CARD_D, tone)), wpx(a, kx + 3, ky, mul(CARD_D, tone))
            wrect(a, x0, y0, 32, 1, mul(CARD_D, 0.82))
            wrect(a, x0 + 1, y0 + 1, 31, 1, mul(TAPE, tone))
            wrect(a, x0, y0, 1, 8, mul(CARD_D, 0.82))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Основание мира: ковролин опенспейса до горизонта. Тёмно-зелёные плитки 32×32 с
    корпоративным узором: ромбы из штрихов, синие квадратные вставки на стыках, мелкий ворс."""
    a = lm.Atlas(64, 64, 135)
    for y in range(64):
        for x in range(64):
            k = (1.06, 0.95)[(x + y) % 2] * (1.0 if ((x // 32) + (y // 32)) % 2 == 0 else 0.92)
            a.px(x, y, mul(BASE, k))
    # Ромбы: две решётки диагоналей шагом 16, штрих через пиксель.
    for y in range(64):
        for x in range(64):
            u, v = (x + y) % 16, (x - y) % 16
            if u == 0 or v == 0:
                wpx(a, x, y, BASE_L if (x + y // 2) % 4 < 3 else BASE)
            elif u == 1 or v == 15:
                wpx(a, x, y, BASE_D)
    # Середина каждого второго ромба: светлая зелёная точка-узел.
    for cy in range(0, 64, 16):
        for cx in range(8, 64, 16):
            wrect(a, cx - 1, cy + 7, 2, 2, mul(GREEN, 0.9))
            wpx(a, cx, cy + 9, BASE_D)
    # Швы плиток и синие вставки на перекрестьях.
    for s in (0, 32):
        wrect(a, s, 0, 1, 64, BASE_D), wrect(a, 0, s, 64, 1, BASE_D)
    for cx, cy in ((0, 0), (32, 32)):
        wrect(a, cx - 3, cy - 3, 7, 7, SEA)
        wrect(a, cx - 3, cy - 3, 7, 1, SEA_L), wrect(a, cx - 3, cy - 3, 1, 7, SEA_L)
        wrect(a, cx - 3, cy + 3, 7, 1, NAVY), wrect(a, cx + 3, cy - 3, 1, 7, NAVY)
        wrect(a, cx - 1, cy - 1, 3, 3, mul(AQUA, 0.8))
    for cx, cy in ((32, 0), (0, 32)):
        wrect(a, cx - 2, cy - 2, 5, 5, mul(GREEN, 0.86))
        wrect(a, cx - 2, cy + 2, 5, 1, BASE_D), wrect(a, cx + 2, cy - 2, 1, 5, BASE_D)
        wpx(a, cx, cy, GREEN_L)
    for _ in range(120):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), BASE_D if a.rng.random() < 0.6 else BASE_L)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_rock():
    """Стена картотечных шкафов: ящики 16×8, у каждого свой тон, светлая кромка сверху, ручка,
    рамка с ярлыком, замочек; кое-где жёлтые и голубые стикеры и вмятины."""
    a = lm.Atlas(64, 64, 137)
    a.rect(0, 0, 64, 64, METAL)
    for row in range(8):
        y = row * 8
        for col in range(4):
            x = col * 16
            tone = a.rng.uniform(0.9, 1.1)
            wrect(a, x, y, 16, 8, mul(METAL, tone))
            wrect(a, x + 1, y + 1, 14, 1, mul(METAL_L, tone * 1.06))
            wrect(a, x + 1, y + 7, 15, 1, mul(DARK_L, 1.1))
            wrect(a, x, y, 1, 8, DARK_L)
            wrect(a, x, y, 16, 1, DARK_L)
            wrect(a, x + 15, y + 1, 1, 6, mul(METAL, tone * 0.86))
            # Рамка ярлыка с бумажкой и строчкой текста.
            wrect(a, x + 3, y + 2, 6, 3, DARK_L)
            wrect(a, x + 4, y + 3, 4, 1, WHITE if a.rng.random() < 0.8 else GOLD_L)
            wpx(a, x + 5 + a.rng.randrange(2), y + 3, GREY_D)
            # Ручка-скоба с бликом и тенью под ней.
            wrect(a, x + 5, y + 5, 6, 1, mul(METAL_L, 1.2))
            wrect(a, x + 5, y + 6, 6, 1, DARK)
            wpx(a, x + 12, y + 3, DARK_D), wpx(a, x + 12, y + 2, METAL_L)
            if a.rng.random() < 0.3:
                cx, cy = x + a.rng.randrange(10, 13), y + a.rng.randrange(4, 6)
                wpx(a, cx, cy, mul(METAL, 0.78)), wpx(a, cx + 1, cy + 1, mul(METAL_L, 1.1))
    # Стикеры поверх ящиков: яркие пятна на сером.
    for x, y, c, c2 in ((10, 9, GOLD, BRASS), (43, 26, AQUA, SEA), (27, 41, GOLD, BRASS), (58, 50, RED, DARK),
                        (4, 58, GOLD, BRASS), (51, 2, GOLD, BRASS)):
        wrect(a, x, y, 4, 4, c), wrect(a, x, y, 4, 1, mix(c, WHITE, 0.4))
        wrect(a, x + 1, y + 2, 2, 1, c2), wpx(a, x + 3, y + 3, c2)
    for _ in range(90):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), DARK_L if a.rng.random() < 0.4 else METAL_L)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_sail():
    """Растяжка из листов бумаги: два листа 16×32 в линейку с красным полем, шов по краю листа,
    скрепки на стыке, пометки маркером и загнутый уголок."""
    a = lm.Atlas(32, 32, 139)
    for y in range(32):
        for x in range(32):
            k = 1.0 - 0.05 * abs(math.sin(x * math.pi / 16.0)) + 0.02 * math.sin(y * math.pi / 8.0)
            a.px(x, y, mul(WHITE, min(k, 1.0)))
    for y in range(3, 32, 4):
        a.rect(0, y, 32, 1, mix(WHITE, AQUA, 0.55))
    for x0 in (0, 16):
        a.rect(x0, 0, 1, 32, GREY_D)
        a.rect(x0 + 1, 0, 1, 32, GREY)
        a.rect(x0 + 4, 0, 1, 32, mix(WHITE, RED, 0.6))
        # Дырки под скоросшиватель.
        for y in (6, 22):
            a.px(x0 + 2, y, DARK_L), a.px(x0 + 2, y + 1, GREY_D)
    # Строчки текста карандашом и пометка маркером.
    for x0, rows in ((6, (2, 6, 10, 18, 26)), (22, (2, 10, 14, 22, 30))):
        for y in rows:
            n = a.rng.randrange(5, 9)
            for i in range(n):
                if a.rng.random() < 0.8:
                    a.px(x0 + i, y, GREY_D if a.rng.random() < 0.7 else METAL)
    a.rect(6, 13, 7, 2, mix(GOLD, WHITE, 0.25))
    a.rect(22, 25, 6, 2, mix(GOLD, WHITE, 0.25))
    a.px(27, 18, RED), a.px(28, 17, RED), a.px(29, 16, RED), a.px(26, 17, RED)
    # Скрепки на стыках листов.
    for x0, y in ((15, 3), (31, 19)):
        for j in range(4):
            wpx(a, x0, y + j, METAL), wpx(a, x0 + 2, y + j, METAL)
        wpx(a, x0 + 1, y - 1, METAL), wpx(a, x0 + 1, y + 4, METAL_L)
    a.noise(0, 0, 32, 32, 0.03)
    return a


def tex_grass():
    """Зелёный ковролин с длинным ворсом: пятна тоном, ворсинки в два пикселя, примятые места,
    светлые кончики."""
    a = lm.Atlas(64, 64, 141)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.08 * math.sin(x * math.pi / 16.0 + 1.5 * math.sin(y * math.pi / 16.0)) \
                + 0.04 * math.sin((x - y) * math.pi / 8.0)
            a.px(x, y, mul(GREEN, k))
    for _ in range(330):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = GREEN_D if a.rng.random() < 0.55 else GREEN_L
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
        if c == GREEN_L and a.rng.random() < 0.4:
            wpx(a, x + 1, y - 1, mul(GREEN_L, 1.1))
    # Примятые места: тёмные овалы от ножек стульев с вмятиной посередине.
    for _ in range(6):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 4, 2, mul(GREEN_D, 1.08)), wrect(a, x + 1, y - 1, 2, 4, mul(GREEN_D, 1.08))
        wpx(a, x + 1, y, mul(GREEN_D, 0.82)), wpx(a, x + 2, y + 1, mul(GREEN_D, 0.82))
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, WHITE), wpx(a, x + 1, y + 1, GREEN_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_road():
    """Линолеум коридора: крап, поперечные швы полотен с накладкой, укатанные следы колёсиков,
    пунктир жёлтой ленты по оси, потёртости от подошв."""
    a = lm.Atlas(64, 64, 143)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.04 * math.sin(y * math.pi / 8.0 + x * math.pi / 32.0)
            a.px(x, y, mul(LINO, k * (0.95 if (y // 32) % 2 else 1.0)))
    # Крап линолеума: светлые и тёмные хлопья, редкие синие.
    for _ in range(230):
        r = a.rng.random()
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), LINO_D if r < 0.5 else (LINO_L if r < 0.9 else SEA))
    # Следы колёсиков там же, где колеи у пиратов.
    for x in (18, 19, 44, 45):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 0.84))
    for x in (20, 46):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 1.1))
    # Швы полотен: алюминиевая накладка с шурупами.
    for y in (0, 32):
        a.rect(0, y, 64, 1, LINO_D)
        a.rect(0, y + 1, 64, 1, METAL_L)
        a.rect(0, y + 2, 64, 1, mul(LINO_D, 0.9))
        for x in (4, 28, 36, 60):
            a.px(x, y + 1, DARK_L), a.px(x + 1, y + 1, WHITE)
    a.rect(0, 0, 1, 64, LINO_D)
    # Пунктир жёлтой ленты по оси, с потёртыми краями.
    for y in (6, 38):
        a.rect(31, y, 2, 12, GOLD)
        a.rect(31, y, 2, 1, GOLD_L)
        a.px(31, y + 5, BRASS), a.px(32, y + 9, BRASS), a.px(32, y + 11, BRASS)
    # Чёрные росчерки от подошв.
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(4, 62)
        wpx(a, x, y, DARK_L), wpx(a, x + 1, y + 1, DARK_L), wpx(a, x + 2, y + 1, DARK_L), wpx(a, x + 3, y + 2, LINO_D)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_mud():
    """Тёмный ковёр с пролитым кофе: петельный ворс, коричневые лужи со светлой каймой и
    бликом, брызги. Заметно темнее трассы."""
    a = lm.Atlas(64, 64, 145)
    rug, rug_d, rug_l = DARK, DARK_D, DARK_L
    cof, cof_d, cof_l = rgb("4A2E1C"), rgb("2E1C12"), rgb("7A5232")
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 4.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            a.px(x, y, mul(rug, (1.0 + 0.1 * w) * (1.06, 0.94)[(x + y) % 2]))
    for _ in range(11):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 6)
        for y in range(-r - 1, r + 2):
            for x in range(-r * 2 - 1, r * 2 + 2):
                d = (x / 2.0) ** 2 + y ** 2
                if d <= (r - 0.8) ** 2:
                    wpx(a, cx + x, cy + y, cof if (x + y) % 3 else cof_d)
                elif d <= r * r:
                    wpx(a, cx + x, cy + y, cof_l if y < 0 else cof_d)
        wpx(a, cx - 2, cy - r + 2, rgb("B08C64")), wpx(a, cx - 1, cy - r + 2, rgb("B08C64"))
        # Брызги рядом с лужей.
        for _ in range(3):
            wpx(a, cx + a.rng.randrange(-r * 2 - 4, r * 2 + 5), cy + a.rng.randrange(-r - 3, r + 4), cof)
    for _ in range(170):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), rug_l if a.rng.random() < 0.45 else rug_d)
    for _ in range(8):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), METAL)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_wind():
    """Разгонная полоса: белые стрелки вперёд с голубой тенью на прозрачном, текстура бежит по
    полосе. Стрелка сложена как бумажный самолётик: светлое крыло и сгиб по оси."""
    a = lm.Atlas(32, 32, 147)
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, WHITE)
                a.px(x, row + 4 + k, SKY)
                a.px(x, row + 5 + k, AQUA)
        # Сгиб по оси: короткая складка под остриём.
        for j in range(3):
            a.px(15, row + 6 + j, SKY), a.px(16, row + 6 + j, mul(AQUA, 0.9))
    return a


def tex_sky():
    """Панорама опенспейса: потолок из плит с лампами, лента окон с небом и городом, под ней
    ряды перегородок с мониторами, фикусами и стикерами, внизу полоса ковролина в цвет
    основания. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 149)
    ceil, ceil_d = rgb("DDE1EA"), rgb("B7BFCF")
    # Потолок: плиты 16×6 с крапом, светильник в каждой четвёртой.
    for y in range(18):
        a.rect(0, y, 128, 1, mul(ceil, 0.86 + 0.14 * y / 17.0))
    for y in (5, 11, 17):
        a.rect(0, y, 128, 1, ceil_d)
    for x in range(0, 128, 16):
        a.rect(x, 0, 1, 18, ceil_d)
    for _ in range(80):
        wpx(a, a.rng.randrange(128), a.rng.randrange(17), ceil_d)
    for x0, y0 in ((17, 6), (81, 6), (49, 12), (113, 12), (33, 0), (97, 0)):
        wrect(a, x0, y0, 15, 5, SKY)
        wrect(a, x0 + 1, y0 + 1, 13, 3, WHITE)
        wrect(a, x0 + 7, y0, 1, 5, mix(SKY, AQUA, 0.5))
    # Балка над окнами.
    a.rect(0, 18, 128, 2, GREY_D)
    a.rect(0, 20, 128, 1, DARK_L)
    # Окна: небо с облаками и город.
    sky_t, sky_b = rgb("7CC6E8"), rgb("DCF2F8")
    for y in range(21, 45):
        a.rect(0, y, 128, 1, mix(sky_t, sky_b, (y - 21) / 23.0))
    for cx, cy, w in ((14, 25, 9), (58, 28, 12), (101, 24, 8)):
        wrect(a, cx, cy, w, 2, WHITE), wrect(a, cx + 2, cy - 1, w - 5, 1, WHITE)
        wrect(a, cx + 1, cy + 2, w - 2, 1, SKY)
    # Дальний ряд небоскрёбов, светлый.
    x = 0
    while x < 128:
        w = a.rng.randrange(5, 10)
        h = a.rng.randrange(6, 15)
        a.rect(x, 45 - h, min(w, 128 - x), h, mix(SEA_L, sky_b, 0.5))
        x += w + a.rng.randrange(0, 3)
    # Ближний ряд: тёмно-синие башни с окнами и антеннами.
    x = 2
    while x < 124:
        w = a.rng.randrange(7, 13)
        h = a.rng.randrange(8, 20)
        w = min(w, 126 - x)
        col = SEA if a.rng.random() < 0.6 else mix(SEA, NAVY, 0.5)
        a.rect(x, 45 - h, w, h, col)
        a.rect(x, 45 - h, 1, h, mul(col, 1.25))
        a.rect(x, 45 - h, w, 1, mul(col, 1.25))
        for wy in range(45 - h + 2, 44, 3):
            for wx in range(x + 2, x + w - 1, 2):
                r = a.rng.random()
                a.px(wx, wy, GOLD_L if r < 0.25 else (SKY if r < 0.55 else mul(col, 0.8)))
        if a.rng.random() < 0.4 and h > 10:
            a.rect(x + w // 2, 45 - h - 3, 1, 3, NAVY)
            a.px(x + w // 2, 45 - h - 4, RED)
        x += w + a.rng.randrange(1, 4)
    # Переплёты окон: стойка каждые 32 пикселя, тонкий импост посередине.
    for x0 in range(0, 128, 32):
        a.rect(x0, 21, 2, 24, GREY_D)
        a.rect(x0 + 2, 21, 1, 24, WHITE)
        a.rect(x0 + 16, 21, 1, 24, GREY)
    a.rect(0, 33, 128, 1, GREY)
    # Подоконник.
    a.rect(0, 45, 128, 1, WHITE)
    a.rect(0, 46, 128, 1, GREY_D)
    # Стена под окном.
    a.rect(0, 47, 128, 3, GREY)
    # Дальний ряд перегородок.
    a.rect(0, 49, 128, 3, mix(SEA, GREY, 0.35))
    a.rect(0, 49, 128, 1, GREY)
    # Ближний ряд перегородок: кабинки по 32, панель ткани в рамке, монитор, фикус, стикеры.
    for x0 in range(0, 128, 32):
        a.rect(x0, 52, 32, 6, SEA)
        a.rect(x0, 51, 32, 1, WHITE)
        a.rect(x0, 52, 32, 1, GREY_D)
        a.rect(x0, 51, 1, 7, GREY_D)
        a.rect(x0 + 1, 53, 1, 5, SEA_L)
        for i in range(3, 31, 2):
            a.px(x0 + i, 54 + (i // 2) % 2 * 2, NAVY)
        # Монитор над перегородкой.
        mx = x0 + 6 + a.rng.randrange(4)
        a.rect(mx, 46, 8, 5, DARK)
        a.rect(mx + 1, 47, 6, 3, AQUA)
        a.rect(mx + 1, 47, 3, 1, SKY)
        a.px(mx + 5, 49, SEA)
        # Фикус в горшке или вешалка через кабинку.
        fx = x0 + 22
        if (x0 // 32) % 2 == 0:
            a.rect(fx, 48, 3, 3, BRASS)
            a.rect(fx, 48, 3, 1, CARD)
            for dx, dy in ((0, -1), (1, -2), (2, -1), (-1, -3), (1, -4), (3, -3), (0, -5), (2, -5), (1, -6), (-1, -1),
                           (3, -1)):
                a.px(fx + dx, 48 + dy, GREEN if (dx + dy) % 2 else GREEN_L)
            a.px(fx + 1, 47, GREEN_D), a.px(fx + 1, 45, GREEN_D)
        else:
            a.rect(fx + 1, 41, 1, 10, DARK)
            a.rect(fx - 1, 41, 5, 1, DARK)
            a.rect(fx - 1, 42, 2, 5, RED), a.px(fx - 1, 47, mul(RED, 0.7))
            a.rect(fx + 3, 42, 1, 3, GOLD)
        # Стикеры на перегородке.
        for sx, sc in ((x0 + 5, GOLD), (x0 + 9, AQUA if x0 % 64 else GOLD_L), (x0 + 26, GOLD)):
            a.rect(sx, 54, 2, 2, sc)
    # Ковролин до горизонта: в цвет основания мира, со светлой кромкой и швами плиток.
    a.rect(0, 58, 128, 6, BASE)
    a.rect(0, 58, 128, 1, DARK_D)
    a.rect(0, 59, 128, 1, BASE_L)
    for x in range(0, 128, 8):
        a.px(x, 61, BASE_D), a.px(x + 4, 63, BASE_D)
    for _ in range(40):
        wpx(a, a.rng.randrange(128), 60 + a.rng.randrange(4), BASE_D if a.rng.random() < 0.6 else BASE_L)
    a.noise(0, 0, 128, 64, 0.03)
    return a


TEXTURES = {"sand": tex_sand, "planks": tex_planks, "water": tex_water, "rock": tex_rock, "sail": tex_sail,
            "grass": tex_grass, "road": tex_road, "mud": tex_mud, "wind": tex_wind, "sky": tex_sky}


def preview(path, scale=3):
    """Лист: каждая текстура плиткой 2×2 (швы видны посередине), подпись сверху."""
    from PIL import Image, ImageDraw
    cells = []
    for name, make in TEXTURES.items():
        im = make().im
        tile = Image.new("RGBA", (im.width * 2, im.height * 2), (0x1B, 0x1A, 0x33, 255))
        for ix in range(2):
            for iy in range(2):
                tile.alpha_composite(im, (ix * im.width, iy * im.height))
        tile = tile.resize((tile.width * scale, tile.height * scale), Image.NEAREST).convert("RGB")
        cell = Image.new("RGB", (tile.width + 8, tile.height + 20), (0x1B, 0x1A, 0x33))
        cell.paste(tile, (4, 16))
        ImageDraw.Draw(cell).text((4, 2), "tex_%s %dx%d" % (name, im.width, im.height), fill=(220, 225, 240))
        cells.append(cell)
    per = 4
    rows = [cells[i:i + per] for i in range(0, len(cells), per)]
    sheet = Image.new("RGB", (max(sum(c.width for c in r) for r in rows), sum(max(c.height for c in r) for r in rows)),
                      (0x1B, 0x1A, 0x33))
    y = 0
    for r in rows:
        x = 0
        for c in r:
            sheet.paste(c, (x, y))
            x += c.width
        y += max(c.height for c in r)
    sheet.save(path)
    print("лист: %s" % path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
