#!/usr/bin/env python3
"""Текстуры уровня «Супергероев» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок:
крыши мегаполиса на закате. Стиль первой PlayStation: низкое разрешение, в которое втиснуто как
можно больше деталей. Все плитки стыкуются по краям: каждый пиксель ставится по модулю размера.
Цвета из палитры основы 16/32 (`superheroes16.PALETTE`) и тона к ним.

Что на что рассчитано в демках, сохранено: `sand` главная земля (бетон крыши), `planks` настил
панелями 32×16 вразбежку (клёпаные стальные балки), `water` основание мира (твердь: улицы с
огнями далеко внизу, вид сверху, а не морская вода), `rock` кладка блоками 16×8 со сдвигом
(кирпич), `sail` ткань 32×32 со швами на x = 0 и 16 (синее полотнище флага в комиксную точку со
звёздами), `grass` зелёная кровля (медь под патиной, цвет корпуса роботов), `road` асфальт с
колеями на тех же столбцах и пунктиром по оси, `mud` заметно темнее дороги (разлитый гудрон),
`wind` стрелки вперёд на прозрачном, `sky` панорама 128×64 с плиткой по горизонтали и полосой
основания мира с 56-й строки (закат, небоскрёбы, прожектор, дирижабль).

    python3 tools/superheroes_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import superheroes16 as s16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def _pal(i):
    return tuple(s16.PALETTE[i])


CONC, CONC_D, CONC_L = rgb("A6A2AE"), rgb("7A7688"), _pal(s16.GREY)  # бетон крыши
STEEL, STEEL_D, STEEL_L = rgb("5C6686"), _pal(s16.DARK), rgb("8C96B4")  # балки
BRICK, BRICK_D, BRICK_L = _pal(s16.TAN), rgb("7C4638"), rgb("DC9668")  # кирпич
MORTAR = rgb("42394C")
CLOTH, CLOTH_D, CLOTH_L = _pal(s16.SEA), _pal(s16.NAVY), rgb("5C86F0")  # полотнище флага
PATINA, PATINA_D, PATINA_L = _pal(s16.VIOLET), _pal(s16.PLUM), rgb("AED0A0")  # медь под патиной
COPPER = rgb("9A5C38")
ASPH, ASPH_D, ASPH_L = rgb("4E4C62"), rgb("2E2C40"), rgb("706E88")  # асфальт
TAR, TAR_D, TAR_L = rgb("1E1A28"), rgb("100E18"), rgb("3E3A52")  # гудрон
GOLD, BRASS = _pal(s16.GOLD), _pal(s16.BRASS)
CORAL, PEACH = _pal(s16.AQUA), _pal(s16.SKY)
WHITE, RED = _pal(s16.WHITE), _pal(s16.RED)
INK = _pal(s16.K)
NIGHT = rgb("1A1540")  # ближние небоскрёбы и кварталы внизу

STAR = ("...#...",
        "..###..",
        "#######",
        ".#####.",
        ".##.##.",
        "#.....#")


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def wget(a, x, y):
    return a.get(int(x) % a.w, int(y) % a.h)[:3]


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def crack(a, x, y, n, c, lit=None):
    """Трещина: ломаная в n шагов, идёт вправо и гуляет по высоте; `lit` это светлая кромка снизу."""
    for _ in range(n):
        wpx(a, x, y, c)
        if lit is not None:
            wpx(a, x, y + 1, lit)
        x += 1
        y += a.rng.choice((-1, 0, 0, 1))


def stamp(a, x, y, rows, c, k=1.0):
    """Рисунок по буквам поверх текстуры: `#` подмешивает цвет с силой k."""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                wpx(a, x + dx, y + dy, mix(wget(a, x + dx, y + dy), c, k))


def tex_sand():
    """Бетон крыши: пятна сырости, волосяные трещины, заплаты битума, ржавые потёки и щебень."""
    a = lm.Atlas(64, 64, 331)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.05 * math.sin(x * math.pi / 16.0 + 2.0 * math.sin(y * math.pi / 32.0)) \
                + 0.04 * math.sin((y * 3 - x) * math.pi / 32.0)
            a.px(x, y, mul(CONC, k))
    # Пятна сырости: мягкие тёмные лужицы с дизерингом по краю.
    for _ in range(6):
        cx, cy, rx, ry = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(4, 9), a.rng.randrange(2, 5)
        for y in range(-ry, ry + 1):
            for x in range(-rx, rx + 1):
                d = (x / rx) ** 2 + (y / ry) ** 2
                if d <= 1.0 and (d < 0.5 or (x + y) % 2 == 0):
                    wpx(a, cx + x, cy + y, mul(wget(a, cx + x, cy + y), 0.9))
    for _ in range(210):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), CONC_D if a.rng.random() < 0.6 else CONC_L)
    # Трещины с светлой кромкой и заплаты битума на двух из них.
    for n in (22, 15, 11, 8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        crack(a, x, y, n, mul(CONC_D, 0.7), CONC_L)
        if n > 12:
            wrect(a, x + 4, y - 1, 6, 3, TAR_L)
            wrect(a, x + 5, y - 1, 4, 1, mul(TAR_L, 1.3))
    # Ржавые потёки от арматуры: точка и след вниз.
    for _ in range(5):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, BRASS), wpx(a, x + 1, y, mul(BRASS, 0.7))
        for k in range(1, a.rng.randrange(3, 7)):
            wpx(a, x, y + k, mix(wget(a, x, y + k), BRASS, 0.5 - 0.06 * k))
    # Щебень: камешек в четыре пикселя со светом сверху слева.
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, WHITE), wpx(a, x + 1, y, CONC_L), wpx(a, x, y + 1, CONC_D), wpx(a, x + 1, y + 1, mul(CONC_D, 0.7))
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_planks():
    """Стальные балки: двутавры 32×16 вразбежку, светлые полки с рядом заклёпок, тёмная стенка с
    зигзагом раскосов, косынка на стыке, на двух балках жёлто-чёрная разметка и ржавчина."""
    a = lm.Atlas(64, 64, 333)
    a.rect(0, 0, 64, 64, STEEL)
    for row in range(4):
        y0 = row * 16
        off = (row % 2) * 16
        tone = (1.0, 0.92, 1.06, 0.96)[row]
        for col in range(2):
            x0 = off + col * 32
            t = tone * (1.0 if col == 0 else 0.94)
            # Стенка балки и раскосы зигзагом: светлая линия и тень под ней.
            wrect(a, x0, y0, 32, 16, mul(STEEL, 0.72 * t))
            for i in range(32):
                j = 5 + abs((i % 12) - 6)
                wpx(a, x0 + i, y0 + j, mul(STEEL_L, 0.86 * t))
                if j + 1 < 12:
                    wpx(a, x0 + i, y0 + j + 1, mul(STEEL_D, 1.0))
            # Полки сверху и снизу: блик, плоскость, тень на стенке.
            for fy in (1, 12):
                wrect(a, x0, y0 + fy, 32, 1, mul(STEEL_L, t))
                wrect(a, x0, y0 + fy + 1, 32, 2, mul(STEEL, t))
            wrect(a, x0, y0 + 4, 32, 1, mul(STEEL_D, 0.9))
            wrect(a, x0, y0, 32, 1, STEEL_D)
            wrect(a, x0, y0 + 15, 32, 1, mul(STEEL_D, 0.8))
            for i in range(6, 32, 4):
                for fy in (2, 13):
                    wpx(a, x0 + i, y0 + fy, STEEL_L)
                    wpx(a, x0 + i, y0 + fy + 1, STEEL_D)
            # Косынка на стыке: пластина с четырьмя заклёпками.
            wrect(a, x0, y0 + 1, 5, 14, mul(STEEL, 1.08 * t))
            wrect(a, x0, y0, 1, 16, STEEL_D)
            wrect(a, x0 + 1, y0 + 1, 1, 14, mul(STEEL_L, t))
            wrect(a, x0 + 5, y0 + 1, 1, 14, STEEL_D)
            for dy in (3, 6, 9, 12):
                wpx(a, x0 + 3, y0 + dy, STEEL_L)
                wpx(a, x0 + 3, y0 + dy + 1, STEEL_D)
    # Разметка: косые жёлто-чёрные полосы на полке одной балки, ржавые потёки на другой.
    for i in range(14):
        for j in range(2):
            wpx(a, 42 + i, 2 + j, GOLD if ((i + j) // 2) % 2 == 0 else INK)
    for x, y in ((12, 28), (20, 29), (27, 28), (52, 44), (58, 45)):
        for k in range(a.rng.randrange(3, 7)):
            wpx(a, x, y + k, mix(wget(a, x, y + k), BRASS, 0.75 - 0.1 * k))
        wpx(a, x, y, COPPER)
    # Мелом по стали: номер сборки на нижней балке.
    for dx, dy in ((0, 0), (0, 1), (0, 2), (2, 0), (3, 0), (3, 1), (2, 2), (3, 2), (5, 0), (5, 1), (5, 2), (6, 1)):
        wpx(a, 24 + dx, 55 + dy, mix(STEEL, WHITE, 0.6))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Основание мира, твердь: город далеко внизу, вид сверху. Тёмные кварталы с крышами разного
    тона, светящиеся проспект и улицы, цепочки фонарей по обочинам, фары и стоп-огни машин."""
    a = lm.Atlas(64, 64, 335)
    street, glow = rgb("3A2C5C"), rgb("7A4A6C")
    a.rect(0, 0, 64, 64, NIGHT)
    # Кварталы: проспект по x 28..33, улицы по y 14..17 и 46..49, переулок по x 60..62.
    xs, ys = ((0, 28), (34, 60), (63, 64)), ((0, 14), (18, 46), (50, 64))
    for bx0, bx1 in xs:
        for by0, by1 in ys:
            # Квартал режется на крыши: полосы по высоте, в каждой дома разной ширины.
            y = by0
            while y < by1:
                h = min(by1 - y, a.rng.randrange(5, 10))
                x = bx0
                while x < bx1:
                    w = min(bx1 - x, a.rng.randrange(4, 10))
                    c = mix(NIGHT, a.rng.choice((STEEL_D, _pal(s16.NAVY), INK, rgb("3C3466"))), a.rng.uniform(0.3, 0.9))
                    wrect(a, x, y, w, h, c)
                    # Высота дома: светлая кромка со стороны заката, тень справа и снизу.
                    wrect(a, x, y, w, 1, mix(c, CORAL, 0.28))
                    wrect(a, x, y, 1, h, mix(c, CORAL, 0.16))
                    wrect(a, x + w - 1, y, 1, h, mul(c, 0.6))
                    wrect(a, x, y + h - 1, w, 1, mul(c, 0.55))
                    if w >= 5 and h >= 5:
                        r = a.rng.random()
                        if r < 0.35:  # будка лифта или бак на крыше
                            wrect(a, x + 2, y + 2, 2, 2, mul(c, 1.5))
                            wpx(a, x + 3, y + 3, mul(c, 0.5))
                        elif r < 0.6:  # световой фонарь крыши
                            wrect(a, x + 2, y + 2, w - 4, 1, mix(c, GOLD, 0.55))
                        elif r < 0.75:  # красный огонь на высотке
                            wpx(a, x + w // 2, y + h // 2, RED)
                    x += w
                y += h
    # Улицы: полотно, подсветка по оси, фонари по обочинам.
    wrect(a, 28, 0, 6, 64, street)
    wrect(a, 0, 14, 64, 4, street)
    wrect(a, 0, 46, 64, 4, street)
    wrect(a, 60, 0, 3, 64, mul(street, 0.8))
    wrect(a, 30, 0, 2, 64, glow)
    wrect(a, 0, 15, 64, 2, glow)
    wrect(a, 0, 47, 64, 2, glow)
    wrect(a, 28, 14, 6, 4, mix(glow, GOLD, 0.35))
    wrect(a, 28, 46, 6, 4, mix(glow, GOLD, 0.35))
    for y in range(2, 64, 5):
        if y not in range(13, 19) and y not in range(45, 51):
            wpx(a, 28, y, GOLD), wpx(a, 33, y, GOLD)
            wpx(a, 27, y, mix(wget(a, 27, y), BRASS, 0.5)), wpx(a, 34, y, mix(wget(a, 34, y), BRASS, 0.5))
    for x in range(1, 64, 6):
        if x not in range(26, 36):
            for y in (14, 49):
                wpx(a, x, y, GOLD)
            wpx(a, x, 13, mix(wget(a, x, 13), BRASS, 0.5)), wpx(a, x, 50, mix(wget(a, x, 50), BRASS, 0.5))
    for y in range(4, 64, 9):
        wpx(a, 61, y, BRASS)
    # Машины: пара белых фар по одной полосе, пара красных огней по встречной.
    for y in (5, 23, 38, 56):
        wpx(a, 29, y, WHITE), wpx(a, 29, y + 1, PEACH)
        wpx(a, 32, y + 3, RED), wpx(a, 32, y + 4, mul(RED, 0.6))
    for x in (8, 20, 41, 53):
        wpx(a, x, 15, WHITE), wpx(a, x + 1, 15, PEACH)
        wpx(a, x + 4, 16, RED)
        wpx(a, x + 3, 47, RED)
        wpx(a, x - 2, 48, WHITE), wpx(a, x - 1, 48, PEACH)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_rock():
    """Кирпичная кладка: блоки 16×8 со сдвигом, у каждого свой тон, светлая кромка сверху, тёмные
    швы, часть кирпичей закопчена или сколота, жёлтая звезда по трафарету и белый потёк краски."""
    a = lm.Atlas(64, 64, 337)
    a.rect(0, 0, 64, 64, MORTAR)
    for row in range(8):
        y = row * 8
        off = (row % 2) * 8
        for col in range(4):
            x = off + col * 16
            tone = a.rng.uniform(0.84, 1.14)
            r = a.rng.random()
            base = BRICK
            if r < 0.14:
                base = mix(BRICK, MORTAR, 0.45)  # копоть
            elif r < 0.3:
                base = mix(BRICK, CORAL, 0.35)  # отсвет заката
            elif r < 0.4:
                base = BRICK_D
            wrect(a, x + 1, y + 1, 15, 7, mul(base, tone))
            wrect(a, x + 1, y + 1, 15, 1, mul(mix(base, BRICK_L, 0.7), tone))
            wrect(a, x + 1, y + 7, 15, 1, mul(base, tone * 0.72))
            wrect(a, x + 15, y + 2, 1, 5, mul(base, tone * 0.84))
            # Фактура обжига: пара тёмных пор и светлая крупинка.
            for _ in range(3):
                wpx(a, x + a.rng.randrange(2, 15), y + a.rng.randrange(2, 7), mul(base, tone * 0.78))
            wpx(a, x + a.rng.randrange(2, 15), y + a.rng.randrange(2, 7), mul(BRICK_L, tone))
            if a.rng.random() < 0.3:  # скол угла до раствора
                wrect(a, x + 1, y + 1, 2, 1, MORTAR)
                wpx(a, x + 1, y + 2, MORTAR)
            if a.rng.random() < 0.22:  # трещина через кирпич
                cx = x + a.rng.randrange(4, 12)
                for k in range(6):
                    wpx(a, cx + (k // 2) % 2, y + 1 + k, mul(BRICK_D, 0.7))
    # Трафарет героя: жёлтая звезда, в швах краска темнее.
    for dy, rw in enumerate(STAR):
        for dx, ch in enumerate(rw):
            for sx in range(2):
                for sy in range(2):
                    px_, py_ = 36 + dx * 2 + sx, 18 + dy * 2 + sy
                    if ch == "#" and a.rng.random() < 0.9:
                        seam = wget(a, px_, py_) == MORTAR
                        wpx(a, px_, py_, mix(wget(a, px_, py_), GOLD, 0.5 if seam else 0.82))
    # Белый потёк краски с карниза.
    for x, n in ((10, 9), (11, 5), (13, 12)):
        for k in range(n):
            wpx(a, x, 49 + k, mix(wget(a, x, 49 + k), WHITE, 0.7 - 0.04 * k))
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_sail():
    """Полотнище флага: синяя ткань в комиксную точку (точки крупнее к низу), мелкие жёлтые
    звёзды, шов со стежками на x = 0 и 16."""
    a = lm.Atlas(32, 32, 339)
    for y in range(32):
        for x in range(32):
            k = 1.0 + 0.07 * math.sin((x + y) * math.pi / 8.0) * math.sin((x - y) * math.pi / 16.0)
            a.px(x, y, mul(CLOTH, k if (x + y) % 2 else k * 0.95))
    # Растр комикса: решётка 4×4 со сдвигом через ряд, внизу точки в четыре пикселя.
    for gy in range(8):
        for gx in range(8):
            x, y = gx * 4 + (gy % 2) * 2 + 1, gy * 4 + 1
            wpx(a, x, y, CLOTH_L)
            if gy >= 3:
                wpx(a, x + 1, y, CLOTH_L)
            if gy >= 5:
                wpx(a, x, y + 1, CLOTH_L), wpx(a, x + 1, y + 1, mix(CLOTH_L, CLOTH, 0.4))
    # Звёзды с тёмной подложкой снизу справа.
    for sx, sy in ((5, 4), (21, 20)):
        stamp(a, sx + 1, sy + 1, STAR, CLOTH_D)
        stamp(a, sx, sy, STAR, GOLD)
        wpx(a, sx + 3, sy + 2, WHITE)
        wpx(a, sx + 3, sy + 4, BRASS)
    # Швы: тёмный рубец, светлый отворот и стежки.
    for x in (0, 16):
        wrect(a, x, 0, 1, 32, CLOTH_D)
        wrect(a, x + 1, 0, 1, 32, mul(CLOTH, 1.14))
        for y in range(1, 32, 4):
            wpx(a, x + 1, y, WHITE), wpx(a, x + 1, y + 1, WHITE)
    a.noise(0, 0, 32, 32, 0.05)
    return a


def tex_grass():
    """Зелёная кровля: листы меди под патиной 16×32 вразбежку, стоячий фальц с бликом и тенью,
    вертикальные потёки, протёртая до рыжей меди кромка, заклёпки и птичьи отметины."""
    a = lm.Atlas(64, 64, 341)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.07 * math.sin(y * math.pi / 16.0 + 1.5 * math.sin(x * math.pi / 8.0))
            a.px(x, y, mul(PATINA, k))
    # Потёки патины сверху вниз: светлые и тёмные струи разной длины.
    for _ in range(90):
        x, y, n = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 12)
        c = PATINA_L if a.rng.random() < 0.5 else mix(PATINA, PATINA_D, 0.6)
        for k in range(n):
            wpx(a, x, y + k, mix(wget(a, x, y + k), c, 0.55))
    for col in range(4):
        x0 = col * 16
        off = (col % 2) * 16
        # Стоячий фальц: блик, гребень, тень справа.
        wrect(a, x0, 0, 1, 64, PATINA_L)
        wrect(a, x0 + 1, 0, 1, 64, mul(PATINA, 0.9))
        wrect(a, x0 + 2, 0, 1, 64, PATINA_D)
        for row in range(2):
            y0 = off + row * 32
            # Поперечный стык листов с заклёпками и рыжей протёртой кромкой.
            wrect(a, x0 + 3, y0, 13, 1, PATINA_D)
            wrect(a, x0 + 3, y0 + 1, 13, 1, mul(PATINA_L, 0.96))
            for i in (5, 9, 13):
                wpx(a, x0 + i, y0 + 3, PATINA_L)
                wpx(a, x0 + i, y0 + 4, PATINA_D)
            for i in range(3, 16):
                if a.rng.random() < 0.4:
                    wpx(a, x0 + i, y0 - 1, COPPER)
                    if a.rng.random() < 0.5:
                        wpx(a, x0 + i, y0 - 2, mix(COPPER, PATINA, 0.5))
    # Пятна голой меди и птичьи отметины.
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 2, 2, mix(COPPER, PATINA, 0.3))
        wpx(a, x + 2, y + 1, mix(COPPER, PATINA, 0.6)), wpx(a, x, y, mul(COPPER, 1.2))
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, WHITE), wpx(a, x, y + 1, mix(PATINA, WHITE, 0.5))
    for _ in range(120):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), PATINA_D if a.rng.random() < 0.5 else PATINA_L)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_road():
    """Асфальт: зерно щебня, укатанные колеи, жёлтый пунктир по оси, залитые битумом швы и трещины,
    свежая заплата, масляные пятна."""
    a = lm.Atlas(64, 64, 343)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.04 * math.sin(y * math.pi / 8.0 + x * math.pi / 32.0)
            a.px(x, y, mul(ASPH, k * (0.95 if (y // 32) % 2 else 1.0)))
    for _ in range(260):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), ASPH_D if a.rng.random() < 0.55 else ASPH_L)
    # Свежая заплата темнее полотна, со светлой кромкой реза.
    wrect(a, 5, 40, 10, 8, mul(ASPH, 0.78))
    wrect(a, 5, 40, 10, 1, ASPH_L), wrect(a, 5, 40, 1, 8, ASPH_L)
    for _ in range(8):
        wpx(a, 6 + a.rng.randrange(8), 41 + a.rng.randrange(6), ASPH_D)
    # Колеи там же, где у пиратов и космоса.
    for x in (18, 19, 44, 45):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 0.84))
    for x in (20, 46):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 1.12))
    # Поперечные швы, залитые битумом, с блестящей кромкой.
    for y in (0, 32):
        a.rect(0, y, 64, 1, TAR)
        a.rect(0, y + 1, 64, 1, ASPH_L)
        for x in (4, 28, 36, 60):
            a.px(x, y + 2, TAR), a.px(x + 1, y + 2, TAR)
    a.rect(0, 0, 1, 64, ASPH_D)
    a.rect(32, 0, 1, 64, mul(ASPH, 0.8))
    # Жёлтый пунктир разметки по оси, потёртый по краям.
    for y in (6, 38):
        a.rect(31, y, 2, 12, GOLD)
        a.rect(31, y + 11, 2, 1, BRASS)
        a.px(31, y, BRASS), a.px(32, y + 5, BRASS), a.px(31, y + 8, mix(GOLD, ASPH, 0.5))
    # Трещины, залитые битумом, и масляные пятна.
    for x, y, n in ((36, 22, 14), (50, 54, 10), (4, 12, 11)):
        crack(a, x, y, n, TAR)
    for cx, cy in ((24, 26), (40, 58), (56, 12)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (1, 1), (2, 1), (0, -1)):
            wpx(a, cx + dx, cy + dy, mul(wget(a, cx + dx, cy + dy), 0.7))
        wpx(a, cx, cy, mix(ASPH_D, CLOTH, 0.3))
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_mud():
    """Разлитый гудрон: чёрные тягучие наплывы с глянцевым бликом по гребню, пузыри, радужные
    разводы закатного света. Заметно темнее асфальта."""
    a = lm.Atlas(64, 64, 345)
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 5.0 * math.sin(x * math.pi / 16.0)) * math.pi / 8.0 + 2.0 * math.sin((x + y) * math.pi / 32.0))
            c = mul(TAR, 1.0 + 0.22 * w)
            if w > 0.93:
                c = TAR_L  # глянец по гребню наплыва
            elif w < -0.9:
                c = TAR_D
            a.px(x, y, c)
    # Отсвет заката на гребнях: редкие коралловые и синие точки поверх глянца.
    for _ in range(300):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        if a.get(x, y)[:3] == TAR_L and a.rng.random() < 0.5:
            wpx(a, x, y, mix(TAR_L, a.rng.choice((CORAL, PEACH, CLOTH_L)), 0.55))
    # Пузыри: тёмная лунка, светлый серп сверху слева, блик.
    for r in (3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1):
        cx, cy = a.rng.randrange(64), a.rng.randrange(64)
        for y in range(-r - 1, r + 2):
            for x in range(-r - 1, r + 2):
                d = math.hypot(x, y)
                if d <= r - 0.5:
                    wpx(a, cx + x, cy + y, TAR_D)
                elif d <= r + 0.5:
                    wpx(a, cx + x, cy + y, TAR_L if x + y < 0 else mul(TAR, 0.8))
        wpx(a, cx - max(r - 2, 0), cy - max(r - 2, 0), mix(TAR_L, PEACH, 0.6) if r > 1 else TAR_L)
    # Вмёрзший мусор: щебень и окурок.
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, ASPH_L), wpx(a, x + 1, y + 1, TAR_D)
    for _ in range(90):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), TAR_D if a.rng.random() < 0.6 else mul(TAR_L, 0.8))
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Разгонная полоса: комиксные жёлтые стрелки вперёд с белой кромкой на прозрачном и штрихи
    скорости по бокам, текстура бежит по полосе."""
    a = lm.Atlas(32, 32, 347)
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, WHITE)
                a.px(x, row + 4 + k, GOLD)
                a.px(x, row + 5 + k, GOLD)
                a.px(x, row + 6 + k, BRASS)
        # Штрихи скорости: тают к хвосту.
        for x, y0, n in ((3, 1, 5), (28, 1, 5), (15, 12, 3), (16, 12, 3)):
            for k in range(n):
                a.px(x, row + y0 + k, PEACH, 220 - k * 36)
    return a


def _tower(a, x, base, w, h, body, lit, top="flat", seed_rows=0):
    """Небоскрёб панорамы: тело, закатная кромка слева, тень справа, сетка горящих окон, верх
    плоский, уступом или шпилем."""
    wrect(a, x, base - h, w, h, body)
    wrect(a, x, base - h, 1, h, mix(body, CORAL, 0.45))
    wrect(a, x + w - 1, base - h, 1, h, mul(body, 0.7))
    if top == "step":
        wrect(a, x + 1, base - h - 2, w - 2, 2, body)
        wrect(a, x + 1, base - h - 2, 1, 2, mix(body, CORAL, 0.45))
        wrect(a, x + w // 2, base - h - 5, 1, 3, body)
        wpx(a, x + w // 2, base - h - 6, RED)
    elif top == "spire":
        for k in range(w // 2):
            wrect(a, x + k, base - h - k - 1, w - 2 * k, 1, body)
            wpx(a, x + k, base - h - k - 1, mix(body, CORAL, 0.45))
        wrect(a, x + w // 2, base - h - w // 2 - 4, 1, 4, body)
        wpx(a, x + w // 2, base - h - w // 2 - 5, RED)
    elif top == "tank":  # водяной бак на ножках
        wrect(a, x + 1, base - h - 4, 3, 3, body)
        wrect(a, x + 1, base - h - 1, 1, 1, body), wrect(a, x + 3, base - h - 1, 1, 1, body)
        wpx(a, x + 2, base - h - 5, body)
    for j in range(base - h + 2 + seed_rows, base - 1, 2):
        for i in range(x + 2, x + w - 1, 2):
            if a.rng.random() < lit:
                wpx(a, i, j, GOLD if a.rng.random() < 0.8 else WHITE)


def tex_sky():
    """Панорама купола: закат от индиго через коралл к персиковому горизонту, солнце за домами,
    полосы облаков, дальние небоскрёбы в дымке и ближние с горящими окнами, башня с прожектором,
    дирижабль. С 56-й строки основание мира: огни улиц далеко внизу. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 349)
    stops = ((0.0, rgb("1B1648")), (0.34, rgb("3C2C86")), (0.62, rgb("B4508C")), (0.82, CORAL), (1.0, PEACH))
    for y in range(64):
        t = min(y / 55.0, 1.0)
        for k in range(len(stops) - 1):
            if stops[k][0] <= t <= stops[k + 1][0]:
                c = mix(stops[k][1], stops[k + 1][1], (t - stops[k][0]) / (stops[k + 1][0] - stops[k][0]))
        for x in range(128):
            # Дизеринг полос: соседние тона заходят друг в друга шахматкой.
            a.px(x, y, mul(c, 1.03 if (x + y) % 2 == 0 and y % 3 == 0 else 1.0))
    # Первые звёзды в верхней трети.
    for _ in range(26):
        x, y = a.rng.randrange(128), a.rng.randrange(16)
        wpx(a, x, y, mix(wget(a, x, y), WHITE, a.rng.uniform(0.4, 0.9)))
    # Облака: вытянутые полосы, снизу подсвечены закатом, сверху в тени.
    for cx, cy, rx, ry in ((20, 30, 17, 2), (30, 34, 10, 1), (66, 24, 14, 2), (110, 37, 15, 2), (58, 41, 9, 1),
                           (120, 20, 9, 1), (8, 44, 8, 1)):
        for y in range(-ry, ry + 1):
            span = int(rx * math.sqrt(max(0.0, 1.0 - (y / (ry + 0.6)) ** 2)))
            for x in range(-span, span + 1):
                if abs(x) > span - 3 and (x + y) % 2:
                    continue
                c = mix(rgb("6A3C8C"), CORAL, 0.25 + 0.3 * (cy / 44.0))
                if y == ry:
                    c = mix(PEACH, GOLD, 0.3)
                elif y > -ry:
                    c = mix(c, CORAL, 0.55)
                wpx(a, cx + x + int(y * 1.5), cy + y, c)
    # Луч прожектора с башни: расходящийся конус вверх и влево, тает с высотой.
    bx, by = 49, 23
    for k in range(1, 22):
        for i in range(-(k // 4) - 0, k // 4 + 1):
            x, y = bx - k // 2 + i, by - k
            if y >= 0 and (k < 8 or (x + y) % 2 == 0):
                wpx(a, x, y, mix(wget(a, x, y), PEACH, max(0.1, 0.62 - 0.026 * k)))
    # Дальние небоскрёбы в закатной дымке.
    haze = mix(_pal(s16.METAL), CORAL, 0.5)
    x = 0
    while x < 128:
        w = a.rng.randrange(4, 9)
        h = a.rng.randrange(7, 20)
        if x + w > 128:
            w = 128 - x
        col = mix(haze, rgb("8A4C8C"), a.rng.uniform(0.0, 0.5))
        wrect(a, x, 56 - h, w, h, col)
        wrect(a, x, 56 - h, 1, h, mix(col, PEACH, 0.5))
        if w >= 5 and a.rng.random() < 0.5:
            wrect(a, x + 2, 56 - h - 2, 1, 2, col)
        for j in range(56 - h + 2, 55, 3):
            for i in range(x + 1, x + w - 1, 2):
                if a.rng.random() < 0.3:
                    wpx(a, i, j, mix(col, PEACH, 0.7))
        x += w + a.rng.randrange(0, 3)
    # Солнце садится за ближние дома: диск с ореолом, дальние дома в его сиянии тонут.
    sx, sy, sr = 92, 52, 9
    for y in range(-sr - 6, sr + 1):
        for x in range(-sr - 6, sr + 7):
            d = math.hypot(x, y)
            if sy + y >= 56:
                continue
            if d <= sr:
                wpx(a, sx + x, sy + y, mix(WHITE, GOLD, min(1.0, d / sr) * 0.6))
            elif d <= sr + 6 and (d <= sr + 2 or (x + y) % 2 == 0):
                wpx(a, sx + x, sy + y, mix(wget(a, sx + x, sy + y), PEACH, 0.6 - 0.07 * (d - sr)))
    # Ближние небоскрёбы: тёмные, с окнами. Башня с прожектором самая высокая.
    near = ((2, 9, 17, "tank"), (13, 7, 24, "flat"), (24, 10, 13, "flat"), (44, 11, 33, "step"), (58, 8, 19, "tank"),
            (70, 9, 27, "spire"), (81, 6, 9, "flat"), (101, 7, 19, "flat"), (109, 10, 15, "tank"), (120, 6, 25, "flat"))
    for x, w, h, top in near:
        body = mix(NIGHT, _pal(s16.NAVY), a.rng.uniform(0.0, 0.8))
        _tower(a, x, 56, w, h, body, 0.42, "flat" if top == "step" else top)
        if top == "step":  # башня с прожектором: два уступа и фонарь наверху
            wrect(a, x + 2, 56 - h - 4, w - 4, 4, body)
            wrect(a, x + 2, 56 - h - 4, 1, 4, mix(body, CORAL, 0.45))
            wrect(a, x + 4, 56 - h - 8, w - 8, 4, body)
            wrect(a, x + 4, 56 - h - 9, 3, 1, GOLD)
            wpx(a, x + 5, 56 - h - 10, WHITE)
            # Эмблема героя на фасаде: звезда из окон.
            stamp(a, x + 2, 56 - h + 3, STAR, GOLD)
    # Рекламный щит на крыше низкого дома.
    wrect(a, 25, 56 - 13 - 5, 8, 4, CORAL)
    wrect(a, 26, 56 - 13 - 4, 6, 2, PEACH)
    wpx(a, 26, 56 - 13 - 1, NIGHT), wpx(a, 31, 56 - 13 - 1, NIGHT)
    # Дирижабль: корпус со светотенью, гондола, хвост и красный огонь.
    dx, dy = 104, 13
    for y in range(-3, 4):
        span = int(9 * math.sqrt(max(0.0, 1.0 - (y / 3.6) ** 2)))
        for x in range(-span, span + 1):
            c = _pal(s16.GREY) if y < 0 else (_pal(s16.METAL) if y < 2 else mix(_pal(s16.METAL), CORAL, 0.6))
            wpx(a, dx + x, dy + y, c)
    wrect(a, dx - 6, dy - 3, 9, 1, WHITE)
    wrect(a, dx - 2, dy, 5, 1, CLOTH)  # синяя полоса по борту
    wrect(a, dx - 2, dy + 4, 5, 2, NIGHT)
    wpx(a, dx - 1, dy + 4, GOLD), wpx(a, dx + 1, dy + 4, GOLD)
    for k in range(3):
        wrect(a, dx + 8 + k, dy - 2 - k, 1, 5 + 2 * k, _pal(s16.METAL))
    wpx(a, dx - 10, dy, RED)
    # Основание мира: тёмная глубина улиц, полоса зарева под горизонтом и цепочки огней.
    for y in range(56, 64):
        a.rect(0, y, 128, 1, mix(rgb("4A2C62"), NIGHT, min(1.0, (y - 56) / 4.0)))
    a.rect(0, 56, 128, 1, mix(CORAL, NIGHT, 0.35))
    for x in range(128):
        if x % 3 != 2:
            a.px(x, 57, mix(BRASS, NIGHT, 0.35 if x % 7 else 0.0))
    for y, step in ((59, 4), (61, 6), (63, 9)):
        for x in range(a.rng.randrange(step), 128, step):
            a.px(x, y, GOLD if a.rng.random() < 0.7 else WHITE)
            if a.rng.random() < 0.3:
                wpx(a, x + 1, y, RED)
    for _ in range(26):
        wpx(a, a.rng.randrange(128), 58 + a.rng.randrange(6), mix(BRASS, NIGHT, 0.4))
    a.noise(0, 0, 128, 64, 0.025)
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
