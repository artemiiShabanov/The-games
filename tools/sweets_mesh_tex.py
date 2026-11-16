#!/usr/bin/env python3
"""Текстуры уровня «Сладостей» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок.
Стиль первой PlayStation: низкое разрешение, в которое втиснуто как можно больше деталей. Все
плитки стыкуются по краям: каждый пиксель ставится по модулю размера. Цвета из палитры
`sweets16.PALETTE` и те же, что у моделей в `sweets_mesh_chars.py`.

Слоты по ролям: `sand` бисквит с порами, крупинками сахара и редкой посыпкой, `planks` вафельный
настил (листы вдоль, как доски у пиратов, стыки вразбежку, клетки 8×8, в ямках карамель, поперёк
струйка шоколада), `water` основание мира, у сладостей это жидкость: розовый сироп с той же
зыбью, что у моря, светлыми бликами и пузырьками; `rock` кладка из долек молочного шоколада
(блоки 16×8 со сдвигом, фаска, тиснёная вставка, белая глазурь подтёками в швах), `sail`
полосатая карамельная ткань в розовую и кремовую полосу (швы там же, где у паруса), `grass`
мятная глазурь с завитками и цветной посыпкой, `road` плиты песочного печенья с колеями там
же, где колеи у пиратов, проколами от вилки и пунктиром белой глазури по оси, `mud` растопленный
тёмный шоколад с глянцевыми лужами (заметно темнее печенья), `wind` стрелки разгона на
прозрачном, белые с розовым следом и сахарными искрами, `sky` панорама: пастельное мятное небо,
карамельное солнце, облака сахарной ваты, горы из шариков мороженого с сиропом и вишней, у
горизонта мятные холмы с леденцами и полоса сиропа; плитка по горизонтали.

    python3 tools/sweets_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import sweets_mesh_chars as smc  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Общие цвета сеттинга те же, что у моделей.
ICING, ICING_D = smc.ICING, smc.ICING_D
MINT, MINT_D, MINT_L = smc.MINT, smc.MINT_D, smc.MINT_L
PINK, PINK_D, PINK_L = smc.PINK, smc.PINK_D, smc.PINK_L
JELLY, JELLY_L = smc.JELLY, smc.JELLY_L
CARAMEL, CARAMEL_D, CARAMEL_L = smc.CARAMEL, smc.CARAMEL_D, smc.CARAMEL_L
CHOCO, CHOCO_D, CHOCO_L = smc.CHOCO, smc.CHOCO_D, smc.CHOCO_L
BLACK = smc.BLACK

BISCUIT, BISCUIT_D, BISCUIT_L = rgb("F0CE86"), rgb("C99A50"), rgb("FFE8B4")  # бисквит
WAFER, WAFER_D, WAFER_L = rgb("DCA24C"), rgb("A86C2A"), rgb("F6CC7E")  # вафля
COOKIE, COOKIE_D, COOKIE_L = rgb("D2A262"), rgb("A07238"), rgb("EEC88E")  # песочное печенье
FUDGE, FUDGE_D, FUDGE_L = rgb("3E2222"), rgb("261216"), rgb("66382E")  # растопленный шоколад
SPRINKLES = (PINK, ICING, CARAMEL, JELLY, rgb("6CC4F0"), PINK_D)


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wget(a, x, y):
    return a.get(int(x) % a.w, int(y) % a.h)[:3]


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def wdisc(a, cx, cy, r, c):
    for y in range(-int(r) - 1, int(r) + 2):
        for x in range(-int(r) - 1, int(r) + 2):
            if x * x + y * y <= r * r:
                wpx(a, cx + x, cy + y, c)


def sprinkle(a, x, y, c, way):
    """Палочка посыпки в три пикселя: вдоль, поперёк или наискось, под ней тень."""
    dx, dy = ((1, 0), (0, 1), (1, 1), (1, -1))[way % 4]
    for k in range(3):
        wpx(a, x + dx * k, y + dy * k + 1, mul(wget(a, x + dx * k, y + dy * k + 1), 0.78))
    for k in range(3):
        wpx(a, x + dx * k, y + dy * k, c if k else mix(c, ICING, 0.45))


def tex_sand():
    """Бисквит: тёплый мякиш с плавными пятнами, поры с тенью сверху и светлым краем снизу,
    крупинки сахара, крошки и редкая цветная посыпка."""
    a = lm.Atlas(64, 64, 231)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.03 * math.sin((x + 9.0 * math.sin(y * math.pi / 16.0)) * math.pi / 8.0) \
                + 0.04 * math.sin((y * 3 - x) * math.pi / 32.0)
            a.px(x, y, mul(BISCUIT, k))
    for _ in range(170):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), BISCUIT_D if a.rng.random() < 0.6 else BISCUIT_L)
    # Поры: мелкие овалы, крупных несколько.
    for w in (4, 4, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, w, 1, mul(BISCUIT_D, 0.86))
        if w > 2:
            wrect(a, x + 1, y - 1, w - 2, 1, mul(BISCUIT_D, 0.74))
            wrect(a, x, y, w, 1, BISCUIT_D)
        wrect(a, x, y + 1, w, 1, BISCUIT_L)
    # Сахар: белая крупинка с тенью справа снизу.
    for _ in range(16):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, ICING), wpx(a, x + 1, y + 1, BISCUIT_D)
    for i in range(5):
        sprinkle(a, a.rng.randrange(64), a.rng.randrange(64), SPRINKLES[i], a.rng.randrange(4))
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_planks():
    """Вафельный настил: листы шириной 16 вдоль, стыки вразбежку, клетки 8×8 с тенью под
    рёбрами и светом на дальнем скате, в нескольких ямках карамель, поперёк струйка шоколада."""
    a = lm.Atlas(64, 64, 233)
    for y in range(64):
        for x in range(64):
            sheet = x // 16
            tone = (1.0, 0.94, 1.04, 0.97)[sheet]
            u, v = x % 8, y % 8
            if u == 0 or v == 0:
                c = WAFER_L  # ребро клетки
            elif u == 1 or v == 1:
                c = WAFER_D  # тень под ребром
            elif u == 7 or v == 7:
                c = mix(WAFER, WAFER_L, 0.45)  # освещённый скат
            else:
                c = mul(WAFER, 0.92 if (u + v) % 2 else 0.88)
            a.px(x, y, mul(c, tone))
    # Швы листов и торцы вразбежку, как у досок.
    for x in range(0, 64, 16):
        a.rect(x, 0, 1, 64, mul(WAFER_D, 0.72))
        a.rect(x + 1, 0, 1, 64, WAFER_L)
    for y in (16, 48):
        for sheet in range(4):
            yy = (y + (sheet % 2) * 16) % 64
            a.rect(sheet * 16 + 1, yy, 15, 1, mul(WAFER_D, 0.72))
            wrect(a, sheet * 16 + 1, yy + 1, 15, 1, WAFER_L)
    # Карамель в ямках: золотая лужица с бликом.
    for cx, cy in ((2, 1), (5, 4), (1, 6), (6, 7), (3, 3)):
        x0, y0 = cx * 8 + 2, cy * 8 + 2
        a.rect(x0, y0, 5, 5, CARAMEL_D)
        a.rect(x0 + 1, y0, 4, 4, CARAMEL)
        a.px(x0 + 3, y0 + 1, ICING), a.px(x0 + 2, y0 + 1, CARAMEL_L)
    # Струйка шоколада зигзагом поперёк листов, замкнута по горизонтали.
    for x in range(64):
        y = 27 + int(round(4.0 * math.sin(x * math.pi / 8.0)))
        wpx(a, x, y + 2, mul(wget(a, x, y + 2), 0.74))
        wpx(a, x, y, CHOCO), wpx(a, x, y + 1, CHOCO_D)
        if x % 8 in (3, 4):
            wpx(a, x, y, CHOCO_L)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Розовый сироп: та же зыбь, что у моря пиратов, малиновая глубина, розовая толща,
    светлые глянцевые гребни, искры и пузырьки."""
    a = lm.Atlas(64, 64, 235)
    deep, mid, crest = rgb("D4508E"), rgb("F47EAE"), rgb("FFC8DC")
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = mid if w > 0.3 else deep
            if w < -1.45:
                c = mix(deep, PINK_D, 0.55)
            if w > 1.35:
                c = mix(mid, crest, 0.55)
            if w > 1.78:
                c = crest
            a.px(x, y, c)
    # Пузырьки: светлое колечко с бликом.
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            wpx(a, x + dx, y + dy, crest)
        wpx(a, x - 1, y - 1, ICING)
    for _ in range(36):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), ICING if a.rng.random() < 0.35 else PINK_D)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_rock():
    """Кладка из долек молочного шоколада: блоки 16×8 со сдвигом, у каждого свой тон, фаска
    (свет сверху и слева, тень снизу и справа), тиснёная вставка, белая глазурь стекает из швов,
    крошка ореха."""
    a = lm.Atlas(64, 64, 237)
    a.rect(0, 0, 64, 64, CHOCO)
    for row in range(8):
        y = row * 8
        off = (row % 2) * 8
        for col in range(4):
            x = off + col * 16
            tone = a.rng.uniform(0.88, 1.14)
            wrect(a, x, y, 16, 8, mul(CHOCO, tone))
            wrect(a, x + 1, y + 1, 14, 1, mul(CHOCO_L, tone))
            wrect(a, x + 1, y + 2, 1, 5, mul(CHOCO_L, tone * 0.92))
            wrect(a, x + 1, y + 7, 15, 1, mul(CHOCO_D, 1.12))
            wrect(a, x + 15, y + 1, 1, 6, mul(CHOCO_D, 1.2))
            wrect(a, x, y, 1, 8, CHOCO_D)
            wrect(a, x, y, 16, 1, CHOCO_D)
            # Тиснение: вдавленная плашка, тень у верхнего края, свет у нижнего.
            wrect(a, x + 4, y + 3, 9, 1, mul(CHOCO_D, 1.25))
            wrect(a, x + 4, y + 4, 9, 1, mul(CHOCO, tone * 0.9))
            wrect(a, x + 4, y + 5, 9, 1, mul(CHOCO_L, tone))
            wpx(a, x + 4, y + 4, mul(CHOCO_D, 1.25))
            if a.rng.random() < 0.4:
                wpx(a, x + a.rng.randrange(6, 11), y + 4, mul(CHOCO_L, 1.15))
    for _ in range(90):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), CHOCO_D if a.rng.random() < 0.5 else CHOCO_L)
    # Глазурь в швах: полоска и капли вниз разной длины.
    for _ in range(13):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        n = a.rng.randrange(3, 8)
        wrect(a, x, y, n, 1, ICING)
        for i in range(n):
            drop = (0, 1, 2, 1, 0, 3, 1, 0)[(i + x) % 8] if 0 < i < n - 1 else 0
            wrect(a, x + i, y + 1, 1, drop, ICING)
            wpx(a, x + i, y + 1 + drop, ICING_D)
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, CARAMEL), wpx(a, x + 1, y, CARAMEL_D)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_sail():
    """Карамельная ткань в полоску: розовые и кремовые полосы по 8, мягкие складки, швы по
    стыкам полотнищ, две строчки стежков поперёк, мятная заплатка."""
    a = lm.Atlas(32, 32, 239)
    for y in range(32):
        for x in range(32):
            c = PINK if (x // 8) % 2 == 0 else ICING
            fold = 1.0 + 0.07 * math.cos((x % 8 - 3.5) * math.pi / 4.0) + 0.03 * math.sin(y * math.pi / 8.0)
            c = mul(c, fold)
            if x % 8 == 0:
                c = mix(c, PINK_D, 0.35)
            elif x % 8 == 7 and (x // 8) % 2 == 0:
                c = mix(c, PINK_L, 0.6)
            a.px(x, y, c)
    for x in (0, 16):
        a.rect(x, 0, 1, 32, mix(PINK_D, ICING_D, 0.35))
        a.rect(x + 1, 0, 1, 32, PINK_L)
    for y in (10, 21):
        for x in range(32):
            c = wget(a, x, y)
            wpx(a, x, y, mul(c, 0.84) if x % 4 < 2 else mix(c, CARAMEL, 0.7))
    # Заплатка: мятный лоскут со стежками по углам.
    a.rect(4, 13, 6, 5, MINT_D)
    a.rect(4, 13, 5, 4, MINT)
    for x, y in ((4, 13), (8, 13), (4, 16), (8, 16)):
        a.px(x, y, ICING)
    for _ in range(14):
        wpx(a, a.rng.randrange(32), a.rng.randrange(32), CARAMEL_L)
    a.noise(0, 0, 32, 32, 0.05)
    return a


def tex_grass():
    """Мятная глазурь: завитки тоном, пики крема в два пикселя (свет над тенью), сахарные
    жемчужины и цветная посыпка палочками во все стороны."""
    a = lm.Atlas(64, 64, 241)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.07 * math.sin(x * math.pi / 16.0 + 1.5 * math.sin(y * math.pi / 16.0)) \
                + 0.04 * math.sin((x + y * 2) * math.pi / 8.0)
            a.px(x, y, mul(MINT, k))
    for _ in range(200):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, MINT_L), wpx(a, x, y + 1, mix(MINT, MINT_D, 0.6))
    # Мазки шпателя: короткие тёмные дуги.
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        for k in range(5):
            wpx(a, x + k, y + (0, 1, 1, 1, 0)[k], mix(MINT, MINT_D, 0.75))
            wpx(a, x + k, y + (0, 1, 1, 1, 0)[k] - 1, MINT_L)
    for i in range(34):
        sprinkle(a, a.rng.randrange(64), a.rng.randrange(64), SPRINKLES[i % len(SPRINKLES)], a.rng.randrange(4))
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 2, 2, ICING)
        wpx(a, x + 1, y + 1, ICING_D), wpx(a, x + 2, y + 2, MINT_D), wpx(a, x + 1, y + 2, MINT_D)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_road():
    """Дорога из плит песочного печенья: поперечные швы, укатанные колеи, проколы от вилки,
    пунктир белой глазури по оси, крошки и подрумяненные края."""
    a = lm.Atlas(64, 64, 243)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.04 * math.sin(y * math.pi / 8.0 + x * math.pi / 32.0)
            # Румянец к швам плит.
            edge = min(y % 32, 31 - y % 32)
            k *= 0.9 + 0.1 * min(edge / 5.0, 1.0)
            a.px(x, y, mul(COOKIE, k * (0.96 if (y // 32) % 2 else 1.0)))
    # Колеи там же, где колеи у пиратов.
    for x in (18, 19, 44, 45):
        for y in range(64):
            a.px(x, y, mul(wget(a, x, y), 0.84))
    for x in (20, 46):
        for y in range(64):
            a.px(x, y, mul(wget(a, x, y), 1.1))
    for y in (0, 32):
        a.rect(0, y, 64, 1, COOKIE_D)
        a.rect(0, y + 1, 64, 1, COOKIE_L)
    a.rect(0, 0, 1, 64, COOKIE_D)
    a.rect(32, 0, 1, 64, mul(COOKIE, 0.8))
    # Проколы от вилки: ряды тёмных точек со светлым краем снизу.
    for y0 in (0, 32):
        for y in (y0 + 8, y0 + 24):
            for x in (5, 10, 15, 25, 38, 51, 56, 61):
                a.px(x, y, mul(COOKIE_D, 0.8)), a.px(x, y + 1, COOKIE_L)
    # Пунктир глазури по оси: мазок с тенью и скруглёнными концами.
    for y in (6, 38):
        a.rect(31, y, 2, 12, ICING)
        a.rect(33, y + 1, 1, 11, mul(COOKIE_D, 0.9))
        a.px(31, y, ICING_D), a.px(32, y + 11, ICING_D)
    for _ in range(150):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), COOKIE_D if a.rng.random() < 0.55 else COOKIE_L)
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, CHOCO), wpx(a, x + 1, y, CHOCO_D), wpx(a, x, y + 1, COOKIE_D)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_mud():
    """Растопленный тёмный шоколад: тягучие волны, лужи темнее с глянцевым бликом, крошка
    ореха и редкая розовая посыпка. Заметно темнее печенья дороги."""
    a = lm.Atlas(64, 64, 245)
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 4.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            c = mul(FUDGE, 1.0 + 0.2 * w)
            if w > 0.9:
                c = FUDGE_L
            a.px(x, y, c)
    for _ in range(11):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 6)
        for y in range(-r, r + 1):
            for x in range(-r * 2, r * 2 + 1):
                d = (x / 2.0) ** 2 + y ** 2
                if d <= r * r:
                    wpx(a, cx + x, cy + y, FUDGE_D if d <= (r - 1) ** 2 else mul(FUDGE, 0.8))
        # Глянец: дуга блика у верхнего левого края лужи.
        for k in range(r):
            wpx(a, cx - r + k, cy - r + 2 - (1 if k else 0), FUDGE_L)
        wpx(a, cx - r + 1, cy - r + 1, rgb("B08A7A"))
    for _ in range(150):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), FUDGE_L if a.rng.random() < 0.45 else FUDGE_D)
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, CARAMEL_D), wpx(a, x + 1, y, mul(CARAMEL_D, 0.7))
    for _ in range(6):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), PINK_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_wind():
    """Разгонная полоса: белые стрелки вперёд с розовым следом на прозрачном, между ними
    сахарные искры; текстура бежит по полосе."""
    a = lm.Atlas(32, 32, 247)
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, ICING)
                a.px(x, row + 4 + k, PINK_L)
                a.px(x, row + 5 + k, PINK)
        for x, y in ((4, 2), (27, 4), (15, 13), (16, 14)):
            a.px(x, row + y, ICING, 200)
        a.px(9, row + 14, CARAMEL_L, 200), a.px(22, row + 15, CARAMEL_L, 200)
    return a


def _scoop(a, cx, cy, r, body, body_d, body_l, sauce=None, sauce_d=None):
    """Шарик мороженого: свет слева сверху, тень дизерингом справа снизу, тёмный край, по низу
    оборка из наплывов; сироп шапкой сверху с потёками."""
    for y in range(-r, r + 3):
        for x in range(-r - 1, r + 2):
            d = math.hypot(x, y)
            skirt = y >= r - 2 and abs(x) <= r + 1 and y <= r - 1 + (1 if (x + cx) % 4 < 2 else 2)
            if d > r + 0.3 and not skirt:
                continue
            k = (-x - y * 1.3) / (2.0 * r)
            c = body
            if k > 0.28:
                c = body_l
            elif k < -0.42 or (k < -0.18 and (x + y) % 2 == 0):
                c = body_d
            if d > r - 0.7 and x + y > 0:
                c = body_d
            if skirt and y >= r - 1:
                c = body_l if (x + cx) % 4 < 2 else body
            if sauce is not None:
                edge = -r * 0.25 + 2.0 * abs(math.sin((x + cx) * math.pi / 4.0)) + abs(x) * 0.25
                if y < edge and d <= r + 0.3:
                    c = sauce_d if (x > r * 0.35 or y > edge - 1.0) else sauce
                    if k > 0.62:
                        c = mix(sauce, ICING, 0.55)
            wpx(a, cx + x, cy + y, c)


def _cherry(a, x, y):
    wdisc(a, x, y, 2, JELLY)
    wpx(a, x - 1, y - 1, JELLY_L), wpx(a, x + 1, y + 1, PINK_D), wpx(a, x, y + 2, PINK_D)
    wpx(a, x + 1, y - 3, CHOCO_D), wpx(a, x + 2, y - 4, CHOCO_D), wpx(a, x + 3, y - 4, CHOCO_D)


def _floss(a, cx, cy, lumps, body, lit, shade):
    """Облако сахарной ваты: клубы кругами, светлый верх, тень дизерингом снизу."""
    for dx, dy, r in lumps:
        wdisc(a, cx + dx, cy + dy, r, body)
    for dx, dy, r in lumps:
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if x * x + y * y > r * r:
                    continue
                if y < -r * 0.35 and (x + y) % 2 == 0 or y <= -r + 1:
                    wpx(a, cx + dx + x, cy + dy + y, lit)
                elif y > r * 0.45 and (x + y) % 2 == 0:
                    wpx(a, cx + dx + x, cy + dy + y, shade)


def tex_sky():
    """Панорама купола: пастельное небо от голубого к мятному крему с розовой дымкой у горизонта,
    карамельное солнце со спиралью, облака сахарной ваты, горы из шариков мороженого с сиропом,
    гряда мятных холмов и полоса розового сиропа. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 249)
    top, low, haze = rgb("62A8D0"), rgb("D3F6E4"), rgb("FFE0E6")
    for y in range(64):
        t = min(y / 50.0, 1.0)
        c = mix(top, low, t ** 0.8)
        if y > 40:
            c = mix(c, haze, min((y - 40) / 14.0, 1.0) * 0.7)
        a.rect(0, y, 128, 1, c)
    # Сахарные искры в верхней части неба.
    for _ in range(26):
        wpx(a, a.rng.randrange(128), a.rng.randrange(26), rgb("E4F8F4"))
    # Карамельное солнце: ореол дизерингом, диск, спираль леденца.
    sx, sy = 18, 15
    for y in range(-10, 11):
        for x in range(-10, 11):
            d = math.hypot(x, y)
            if 7.0 < d <= 10.0 and (x + y) % 2 == 0 and d < 8.5 + 1.5 * math.cos(math.atan2(y, x) * 8.0):
                wpx(a, sx + x, sy + y, CARAMEL_L)
            elif d <= 7.0:
                turn = (d * 0.9 - math.atan2(y, x) * 2.0 / math.pi * 2.0) % 4.0
                c = CARAMEL if turn < 2.4 else CARAMEL_D
                if d > 6.0:
                    c = CARAMEL_D if x + y > 0 else CARAMEL_L
                wpx(a, sx + x, sy + y, c)
    wpx(a, sx - 3, sy - 4, ICING), wpx(a, sx - 2, sy - 4, ICING), wpx(a, sx - 4, sy - 3, ICING)
    # Облака сахарной ваты: розовые и белое.
    floss_pink = (PINK, PINK_L, rgb("E66CA0"))
    floss_white = (ICING, rgb("FFFFFF"), ICING_D)
    _floss(a, 52, 12, ((-9, 2, 4), (-3, 0, 6), (5, 1, 5), (11, 3, 3)), *floss_pink)
    _floss(a, 92, 24, ((-7, 1, 3), (-2, 0, 4), (4, 1, 3)), *floss_white)
    _floss(a, 120, 9, ((-6, 1, 3), (0, 0, 5), (7, 2, 3)), *floss_pink)
    _floss(a, 24, 33, ((-5, 0, 2), (0, 0, 3), (5, 1, 2)), *floss_white)
    # Горы мороженого: шарики горкой, дальние раньше ближних, на макушке сироп и вишня.
    berry = (PINK, rgb("E66CA0"), PINK_L)
    cream = (rgb("FFF0C8"), CARAMEL, rgb("FFFBEA"))
    cocoa = (CHOCO_L, CHOCO, rgb("C89070"))
    mint = (MINT, MINT_D, MINT_L)
    _scoop(a, 66, 47, 9, *cocoa, ICING, ICING_D)
    _scoop(a, 34, 49, 9, *cream)
    _scoop(a, 54, 50, 8, *mint)
    _scoop(a, 44, 37, 10, *berry, ICING, ICING_D)
    _cherry(a, 44, 25)
    _scoop(a, 92, 49, 9, *berry)
    _scoop(a, 114, 49, 9, *mint)
    _scoop(a, 103, 46, 11, *cream)
    _scoop(a, 103, 30, 9, *cream, JELLY, PINK_D)
    _cherry(a, 103, 19)
    # Гряда мятных холмов у горизонта с леденцами на гребне и полоса сиропа.
    for x in range(128):
        h = 4 + 2.5 * math.sin(x * math.pi / 16.0) + 1.5 * math.sin(x * math.pi / 8.0 + 1.0) + 2 * math.sin(x * math.pi / 32.0)
        h = max(1, int(h))
        a.rect(x, 56 - h, 1, h, rgb("2E8E86"))
        a.px(x, 56 - h, MINT_D)
        if h > 2 and x % 3 == 0:
            a.px(x, 56 - h + 2, rgb("277A74"))
        if x in (12, 80, 124):
            a.px(x, 56 - h - 1, CHOCO_L), a.px(x, 56 - h - 2, CHOCO_L)
            wdisc(a, x, 56 - h - 4, 1.5, JELLY if x != 80 else CARAMEL)
            wpx(a, x - 1, 56 - h - 5, ICING)
    a.rect(0, 56, 128, 8, rgb("F47EAE"))
    a.rect(0, 56, 128, 1, PINK_L)
    for _ in range(26):
        x, y = a.rng.randrange(128), 58 + a.rng.randrange(6)
        wrect(a, x, y, a.rng.randrange(2, 6), 1, rgb("D4508E") if a.rng.random() < 0.6 else PINK_L)
    a.noise(0, 0, 128, 64, 0.02)
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
