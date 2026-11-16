#!/usr/bin/env python3
"""Текстуры уровня «Ниндзя» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок.
Стиль первой PlayStation: низкое разрешение, в которое втиснуто как можно больше деталей. Все
плитки стыкуются по краям: каждый пиксель ставится по модулю размера. Цвета из палитры
`ninja16.PALETTE` и те же, что у моделей в `ninja_mesh_chars.py`.

Слоты по ролям: `sand` гравий сада камней с бороздами от граблей и кругами вокруг валунов,
`planks` кедровый настил веранды с клинышками на стыках, `water` основание мира, у ниндзя это
жидкость: тёмный пруд с лунной дорожкой, листьями кувшинок и упавшими листьями клёна (зыбь та
же, что у моря пиратов); `rock` кладка замковой стены из подогнанных валунов со мхом в швах,
`sail` бумага воздушного змея с бамбуковыми рейками и красными кругами-гербами, `grass` мох с
красными листьями клёна, `road` каменная дорожка из плит с колеями там же, где колеи у пиратов,
и светлой вставкой по оси, `mud` раскисшая земля рисового поля с лужами, в которых закат
(заметно темнее дорожки), `wind` стрелки разгона на прозрачном, `sky` панорама: закат от индиго
до золота, красное солнце, горы в тумане, замок на утёсе и пагода, плитка по горизонтали.

    python3 tools/ninja_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import ninja_mesh_chars as nc  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга: основа из `ninja_mesh_chars` (палитра 16/32), свои тона для земли и неба.
INDIGO, DUSK = nc.BLUE_D, nc.BLUE  # верх неба и сумеречный синий
CORAL, GLOW = nc._pal(nc.n16.AQUA), nc._pal(nc.n16.SKY)  # коралл заката и золото у горизонта
RED, RED_D, RED_L = nc.RED, nc.RED_D, nc.RED_L
WHITE, GREY = nc.WHITE, nc.GREY
GOLD = nc.GOLD
LACQ, LACQ_D = nc.LACQ, nc.LACQ_D
GRAVEL, GRAVEL_D, GRAVEL_L = rgb("CFC8B8"), rgb("9C968C"), rgb("EFEADC")  # гравий сада камней
CEDAR, CEDAR_D, CEDAR_L = rgb("9A5A30"), rgb("5C3220"), rgb("C4844A")  # кедр настила
STONE, STONE_D, STONE_L = nc.STEEL, rgb("3E3E50"), rgb("A2A4B0")  # камень стены и дорожки
MOSS, MOSS_D, MOSS_L = nc._pal(nc.n16.VIOLET), nc._pal(nc.n16.PLUM), rgb("9CCB62")
POND, POND_D, POND_L = rgb("161A44"), rgb("0C0E28"), rgb("2C3A82")  # тёмный пруд
PAPER, PAPER_D = rgb("EADFC4"), rgb("C4B492")  # бумага змея
BAMBOO, BAMBOO_D = rgb("B2762E"), rgb("70461E")


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def wdist(x, y, cx, cy, w, h, sx=1.0, sy=1.0):
    """Расстояние до точки на плитке, свёрнутой в тор: ближайшая из копий центра."""
    dx = (x - cx + w / 2.0) % w - w / 2.0
    dy = (y - cy + h / 2.0) % h - h / 2.0
    return math.hypot(dx * sx, dy * sy)


def maple(a, x, y, c=None, dark=None):
    """Лист клёна в пять пикселей крестом с черешком: красное пятно, которое читается издали."""
    c = c or RED
    dark = dark or RED_D
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (-2, -1), (2, -1), (-1, 1), (1, 1)):
        wpx(a, x + dx, y + dy, c)
    wpx(a, x, y, RED_L)
    wpx(a, x, y + 1, dark), wpx(a, x, y + 2, dark)


def tex_sand():
    """Гравий сада камней: борозды от граблей идут волной, вокруг двух валунов расходятся кругами."""
    a = lm.Atlas(64, 64, 331)
    rocks = ((18, 20, 5), (47, 50, 4))
    for y in range(64):
        for x in range(64):
            phase = y + 1.6 * math.sin(x * math.pi / 16.0)
            for cx, cy, r in rocks:
                d = wdist(x, y, cx, cy, 64, 64, 0.8, 1.0)
                if d < r + 9:
                    phase = d
            p = int(math.floor(phase)) % 4
            c = (GRAVEL_D, GRAVEL_L, GRAVEL, GRAVEL)[p]
            k = 1.0 + 0.04 * math.sin((x + y * 2) * math.pi / 32.0)
            a.px(x, y, mul(c, k))
    for _ in range(150):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), GRAVEL_D if a.rng.random() < 0.5 else GRAVEL_L)
    # Валуны: тёмный камень со светлой макушкой, шапкой мха и тенью справа снизу.
    for cx, cy, r in rocks:
        for y in range(-r - 1, r + 3):
            for x in range(-r - 3, r + 5):
                d = math.hypot(x * 0.8, y)
                if d <= r:
                    k = 1.15 - 0.5 * ((x + y) / (2.0 * r) + 0.5)
                    c = mul(STONE, k)
                    if y < -r * 0.35 and x < r * 0.5:
                        c = MOSS if (x + y) % 3 else MOSS_L
                    if d > r - 1.0:
                        c = STONE_D
                    wpx(a, cx + x, cy + y, c)
                elif math.hypot((x - 2) * 0.8, y - 1.5) <= r:
                    wpx(a, cx + x, cy + y, mul(GRAVEL_D, 0.8))
    maple(a, 38, 12), maple(a, 8, 44), maple(a, 58, 30)
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_planks():
    """Кедровый настил веранды: доски по 8 вдоль, стыки вразбежку с парой клинышков, волокна,
    сучки и полоса блика на натёртом дереве."""
    a = lm.Atlas(64, 64, 333)
    for col in range(8):
        x0 = col * 8
        tone = (1.0, 0.9, 1.06, 0.95, 1.1, 0.92, 1.02, 0.86)[col]
        wob = a.rng.uniform(0.0, 6.28)
        for y in range(64):
            for i in range(8):
                g = math.sin((i + 1.2 * math.sin(y * math.pi / 16.0 + wob)) * math.pi / 2.0)
                c = mul(CEDAR, tone * (1.0 + 0.09 * g))
                if i == 0:
                    c = CEDAR_D
                elif i == 1:
                    c = mul(CEDAR_L, tone)
                a.px(x0 + i, y, c)
        # Стык досок: тёмный шов, светлая фаска под ним, два чёрных клинышка.
        jy = (col * 24 + 10) % 64
        wrect(a, x0 + 1, jy, 7, 1, CEDAR_D)
        wrect(a, x0 + 1, jy + 1, 7, 1, mul(CEDAR_L, tone))
        for dy in (-3, 4):
            wrect(a, x0 + 3, jy + dy, 2, 2, LACQ_D)
            wpx(a, x0 + 3, jy + dy, LACQ)
        # Сучок с кольцом волокон вокруг.
        if col % 3 != 1:
            kx, ky = x0 + 4, (jy + 30 + col * 5) % 64
            for dx, dy in ((-1, -1), (0, -1), (1, -1), (-2, 0), (2, 0), (-1, 1), (0, 1), (1, 1)):
                wpx(a, kx + dx, ky + dy, mul(CEDAR_D, 1.25))
            wpx(a, kx, ky, CEDAR_D), wpx(a, kx - 1, ky, mul(CEDAR, 0.8)), wpx(a, kx + 1, ky, mul(CEDAR, 0.8))
    # Блик натёртого дерева: две мягкие поперечные полосы.
    for y in range(64):
        k = 1.0 + 0.07 * max(0.0, math.sin(y * math.pi / 16.0)) ** 3
        for x in range(64):
            if x % 8:
                a.px(x, y, mul(a.get(x, y), k))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Тёмный пруд: та же зыбь, что у моря пиратов, почти чёрная глубина, синие гребни, штрихи
    лунной дорожки, листья кувшинок и упавшие листья клёна."""
    a = lm.Atlas(64, 64, 335)
    moon = rgb("FFF2C4")
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = POND if w > 0.3 else POND_D
            if w > 1.35:
                c = POND_L
            if w > 1.8:
                c = rgb("4A5CB8")
            a.px(x, y, c)
    # Лунная дорожка: короткие золотые штрихи, гуще к середине плитки.
    for _ in range(26):
        x = int(32 + a.rng.gauss(0.0, 9.0))
        y = a.rng.randrange(64)
        n = a.rng.randrange(2, 6)
        wrect(a, x, y, n, 1, GLOW)
        wpx(a, x + n // 2, y, moon)
    # Кувшинки: круглый лист с вырезом и светлой кромкой, у одной цветок.
    for cx, cy, r, flower in ((12, 14, 4, True), (50, 40, 5, False), (22, 52, 3, False)):
        for y in range(-r, r + 1):
            for x in range(-r - 1, r + 2):
                d = math.hypot(x * 0.85, y)
                if d <= r and not (x > 0 and abs(y) < x * 0.45):
                    c = MOSS_D if d > r - 1.2 else mul(MOSS, 0.8)
                    if y < 0 and d < r - 1.2 and (x + y) % 3 == 0:
                        c = MOSS
                    wpx(a, cx + x, cy + y, c)
        wrect(a, cx - r, cy + r + 1, r * 2, 1, POND_D)
        if flower:
            wpx(a, cx - 1, cy - 1, WHITE), wpx(a, cx, cy - 1, rgb("F4A8B4")), wpx(a, cx - 1, cy, rgb("F4A8B4"))
            wpx(a, cx, cy, GOLD)
    maple(a, 38, 10, RED, POND_D), maple(a, 6, 36, CORAL, POND_D), maple(a, 58, 58, RED, POND_D)
    for _ in range(24):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), POND_L if a.rng.random() < 0.6 else rgb("4A5CB8"))
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_rock():
    """Кладка замковой стены: валуны неправильной формы подогнаны без раствора, у каждого свой
    тон, светлая кромка сверху и тень снизу, в швах мох, на крупных камнях трещины."""
    a = lm.Atlas(64, 64, 337)
    seeds = []
    for row in range(5):
        for col in range(4):
            seeds.append((col * 16 + (row % 2) * 8 + a.rng.uniform(-4.0, 4.0), row * 12.8 + a.rng.uniform(-2.5, 2.5),
                          a.rng.uniform(0.8, 1.14)))
    own = [[0] * 64 for _ in range(64)]
    edge = [[False] * 64 for _ in range(64)]
    for y in range(64):
        for x in range(64):
            ds = sorted((wdist(x, y, s[0], s[1], 64, 64, 0.75, 1.0), i) for i, s in enumerate(seeds))
            own[y][x] = ds[0][1]
            edge[y][x] = ds[1][0] - ds[0][0] < 1.1
    for y in range(64):
        for x in range(64):
            if edge[y][x]:
                a.px(x, y, STONE_D)
                continue
            s = seeds[own[y][x]]
            dy = (y - s[1] + 32.0) % 64.0 - 32.0
            c = mul(STONE, s[2] * (1.0 - 0.03 * dy))
            if edge[(y - 1) % 64][x] or edge[y][(x - 1) % 64]:
                c = mul(STONE_L, s[2])
            elif edge[(y + 1) % 64][x]:
                c = mul(STONE, s[2] * 0.72)
            a.px(x, y, c)
    for _ in range(140):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        if not edge[y][x]:
            a.px(x, y, mul(a.get(x, y), 0.82 if a.rng.random() < 0.55 else 1.16))
    # Трещины на нескольких камнях и мох, который лезет из швов вниз.
    for i in (1, 6, 10, 13, 18):
        cx, cy = int(seeds[i][0]), int(seeds[i][1])
        for k in range(5):
            x, y = (cx - 2 + k) % 64, (cy - 1 + (k * 2) // 3) % 64
            if not edge[y][x]:
                a.px(x, y, STONE_D)
    for _ in range(46):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        if edge[y][x] and not edge[(y + 1) % 64][x]:
            wpx(a, x, y, MOSS), wpx(a, x, y + 1, MOSS_D)
            if a.rng.random() < 0.5:
                wpx(a, x + 1, y, MOSS_L), wpx(a, x + 1, y + 1, MOSS)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_sail():
    """Бумага воздушного змея: волокна васи, бамбуковые рейки с узлами по шву, красные
    круги-гербы в шахматном порядке и синяя кайма."""
    a = lm.Atlas(32, 32, 339)
    for y in range(32):
        for x in range(32):
            k = 1.0 + 0.04 * math.sin((x * 3 + y) * math.pi / 16.0) + 0.03 * math.sin(y * math.pi / 4.0)
            a.px(x, y, mul(PAPER, k))
    for _ in range(34):
        x, y = a.rng.randrange(32), a.rng.randrange(32)
        wpx(a, x, y, PAPER_D), wpx(a, x + 1, y, PAPER_D)
        if a.rng.random() < 0.4:
            wpx(a, x + 2, y + 1, PAPER_D)
    # Гербы: красный круг с белым кольцом и точкой, два на плитку в шахматном порядке.
    for cx, cy in ((8, 8), (24, 24)):
        for y in range(-5, 6):
            for x in range(-5, 6):
                d = math.hypot(x, y)
                if d <= 4.6:
                    c = RED if d > 3.4 or d <= 2.3 else PAPER
                    if d <= 2.3 and x + y < -1:
                        c = RED_L
                    if d > 3.4 and x + y > 3:
                        c = RED_D
                    wpx(a, cx + x, cy + y, c)
    # Синяя кайма штрихами между гербами.
    for cx, cy in ((24, 8), (8, 24)):
        for k in range(-3, 4):
            wpx(a, cx + k, cy - 2 + abs(k) % 2, nc.BLUE)
            wpx(a, cx + k, cy + 2 - abs(k) % 2, nc.BLUE)
        wpx(a, cx, cy, nc.BLUE_D)
    # Рейки по шву, как швы паруса у пиратов: бамбук с узлами и тенью.
    for x in (0, 16):
        a.rect(x, 0, 1, 32, BAMBOO)
        wrect(a, x + 1, 0, 1, 32, PAPER_D)
        for y in (5, 15, 26):
            a.px(x, y, BAMBOO_D), a.px(x, y + 1, rgb("D8A050"))
    wrect(a, 0, 0, 32, 1, mul(PAPER_D, 0.92))
    wrect(a, 0, 16, 32, 1, mul(PAPER_D, 0.92))
    a.px(0, 0, BAMBOO_D), a.px(16, 0, BAMBOO_D), a.px(0, 16, BAMBOO_D), a.px(16, 16, BAMBOO_D)
    a.noise(0, 0, 32, 32, 0.04)
    return a


def tex_grass():
    """Мох: бархатные кочки тоном, ворсинки в два пикселя, красные листья клёна, белые цветы
    и серые камешки."""
    a = lm.Atlas(64, 64, 341)
    base = mix(MOSS, MOSS_D, 0.25)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.1 * math.sin(x * math.pi / 8.0 + 1.5 * math.sin(y * math.pi / 16.0)) \
                * math.sin(y * math.pi / 8.0 + 1.2 * math.sin(x * math.pi / 32.0))
            a.px(x, y, mul(base, k))
    for _ in range(300):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = MOSS_D if a.rng.random() < 0.5 else (MOSS if a.rng.random() < 0.6 else MOSS_L)
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
    for _ in range(5):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 3, 2, STONE)
        wpx(a, x, y, STONE_L), wpx(a, x + 1, y, STONE_L), wpx(a, x + 2, y + 1, STONE_D)
        wrect(a, x, y + 2, 3, 1, MOSS_D)
    for i in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        maple(a, x, y, RED if i % 3 else CORAL, MOSS_D)
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, WHITE), wpx(a, x, y + 1, MOSS_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_road():
    """Каменная дорожка: плиты разной ширины в четыре ряда, тёмные швы с мхом, колеи от повозок
    там же, где у пиратов, по оси вставка из светлых камней."""
    a = lm.Atlas(64, 64, 343)
    slab, slab_d, slab_l = rgb("84828C"), rgb("4A4858"), rgb("A8A6AE")
    cuts = ((0, 24, 40, 56), (12, 28, 52), (4, 20, 44), (8, 32, 48))
    for row in range(4):
        y0 = row * 16
        xs = cuts[row]
        for i, x0 in enumerate(xs):
            w = (xs[(i + 1) % len(xs)] - x0) % 64 or 64
            tone = a.rng.uniform(0.88, 1.12)
            warm = mix(slab, rgb("94806C"), a.rng.uniform(0.0, 0.3))
            for j in range(16):
                for k in range(w):
                    wpx(a, x0 + k, y0 + j, mul(warm, tone * (1.0 + 0.03 * math.sin((k + j * 2) * 0.7))))
            wrect(a, x0, y0, w, 1, slab_d)
            wrect(a, x0, y0, 1, 16, slab_d)
            wrect(a, x0 + 1, y0 + 1, w - 1, 1, mul(slab_l, tone))
            wrect(a, x0 + 1, y0 + 2, 1, 14, mul(slab_l, tone * 0.94))
            wrect(a, x0 + 1, y0 + 15, w - 1, 1, mul(warm, tone * 0.8))
            # Скол в углу плиты.
            if a.rng.random() < 0.6:
                wpx(a, x0 + w - 1, y0 + 14, slab_d), wpx(a, x0 + w - 2, y0 + 15, slab_d)
    # Колеи там же, где у пиратов.
    for x in (18, 19, 44, 45):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y), 0.8))
    for x in (20, 46):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y), 1.12))
    # Вставка по оси: ряд светлых камней с тёмной кромкой.
    for y in (6, 38):
        a.rect(30, y - 1, 4, 14, slab_d)
        for j in range(0, 12, 4):
            a.rect(31, y + j, 2, 3, WHITE)
            a.px(32, y + j + 2, GREY)
    for _ in range(150):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), slab_d if a.rng.random() < 0.5 else slab_l)
    # Мох в швах.
    for _ in range(22):
        x, y = a.rng.randrange(64), a.rng.randrange(4) * 16
        if 28 <= x <= 35:
            continue
        wrect(a, x, y, a.rng.randrange(2, 5), 1, MOSS)
        wpx(a, x + 1, y + 1, MOSS_D)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_mud():
    """Раскисшая земля рисового поля: борозды, лужи с отсветом заката по краю, ростки риса и
    соломинки. Заметно темнее дорожки."""
    a = lm.Atlas(64, 64, 345)
    mud, mud_d, mud_l = rgb("3C2A2E"), rgb("22161C"), rgb("5E4640")
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 3.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            a.px(x, y, mul(mud, 1.0 + 0.16 * w))
    for _ in range(9):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 6)
        for y in range(-r, r + 1):
            for x in range(-r * 2, r * 2 + 1):
                d = (x / 2.0) ** 2 + y ** 2
                if d <= r * r:
                    c = mix(mud_d, INDIGO, 0.5)
                    if d > (r - 1) ** 2 and y < 0:
                        c = mix(mud, CORAL, 0.55)
                    wpx(a, cx + x, cy + y, c)
        wpx(a, cx - 1, cy, mix(INDIGO, GLOW, 0.6)), wpx(a, cx, cy, mix(INDIGO, GLOW, 0.35))
    for _ in range(190):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), mud_l if a.rng.random() < 0.45 else mud_d)
    # Ростки риса парами и соломинки.
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, MOSS), wpx(a, x, y - 1, MOSS_L), wpx(a, x + 1, y - 2, MOSS), wpx(a, x, y + 1, mud_d)
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, nc.STRAW_D), wpx(a, x + 1, y, nc.STRAW), wpx(a, x + 2, y + 1, nc.STRAW_D)
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Попутный ветер: золотые стрелки вперёд на прозрачном, текстура бежит по полосе."""
    a = lm.Atlas(32, 32, 347)
    white, pale = rgb("FFF8E4"), GLOW
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, white)
                a.px(x, row + 4 + k, pale)
                a.px(x, row + 5 + k, mul(CORAL, 0.95))
    return a


def _castle(a, cx, by):
    """Замок на утёсе: белёные ярусы, тёмные крыши с загнутыми углами, огни в окнах."""
    wall, roof = mix(WHITE, CORAL, 0.35), rgb("1C1830")
    y = by
    for i, (bw, bh, rw) in enumerate(((10, 3, 0), (8, 3, 14), (6, 3, 10), (4, 2, 8))):
        y -= bh
        col = rgb("4A4658") if i == 0 else wall
        wrect(a, cx - bw // 2, y, bw, bh, col)
        wrect(a, cx + bw // 2 - 1, y, 1, bh, mul(col, 0.7))
        if i:
            wpx(a, cx - 1, y + 1, GOLD)
            if bw > 4:
                wpx(a, cx + 1, y + 1, GOLD)
            # Крыша яруса ниже: полоса шире стен, концы загнуты вверх.
            wrect(a, cx - rw // 2, y + bh, rw, 1, roof)
            wpx(a, cx - rw // 2 - 1, y + bh - 1, roof), wpx(a, cx + rw // 2, y + bh - 1, roof)
    wrect(a, cx - 3, y - 1, 6, 1, roof)
    wrect(a, cx - 1, y - 2, 2, 1, roof)
    wpx(a, cx - 4, y - 2, roof), wpx(a, cx + 3, y - 2, roof)
    wpx(a, cx - 1, y - 3, GOLD)


def _pagoda(a, cx, by):
    """Пагода силуэтом: пять сужающихся крыш на тонком стволе и шпиль."""
    dark = rgb("241E3C")
    for i, w in enumerate((9, 7, 7, 5, 5)):
        y = by - 2 - i * 3
        wrect(a, cx - w // 2, y, w, 1, dark)
        wpx(a, cx - w // 2 - 1, y - 1, dark), wpx(a, cx + w // 2 + 1, y - 1, dark)
        wrect(a, cx - 1, y - 2, 3, 2, dark)
        wpx(a, cx, y - 1, GOLD if i % 2 == 0 else dark)
    wrect(a, cx - 1, by - 1, 3, 1, dark)
    wrect(a, cx, by - 19, 1, 4, dark)


def tex_sky():
    """Панорама заката: индиго сверху, коралл и золото у горизонта, красное солнце, полосы
    облаков, дальняя гряда с белой вершиной, туман, ближние холмы с соснами, замок на утёсе
    и пагода, внизу тёмная гладь пруда. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 349)
    stops = ((0, rgb("121236")), (16, INDIGO), (30, DUSK), (42, CORAL), (54, GLOW), (64, GLOW))
    for y in range(64):
        for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
            if y0 <= y < y1:
                # Переход между полосами дизерингом через строку, как у приставки.
                for x in range(128):
                    t = (y - y0) / float(y1 - y0)
                    t = min(1.0, max(0.0, t + (0.08 if (x + y) % 2 else -0.08)))
                    a.px(x, y, mix(c0, c1, round(t * 5) / 5.0))
    # Первые звёзды в верхней трети.
    for _ in range(34):
        k = a.rng.uniform(0.5, 1.0)
        wpx(a, a.rng.randrange(128), a.rng.randrange(18), (int(250 * k), int(236 * k), int(210 * k)))
    # Солнце: красный диск со светлой серединой и ореолом.
    sx, sy, sr = 46, 42, 9
    for y in range(-sr - 3, sr + 4):
        for x in range(-sr - 3, sr + 4):
            d = math.hypot(x, y)
            if d <= sr:
                wpx(a, sx + x, sy + y, mix(rgb("FF8A4A"), RED, min(1.0, d / sr + 0.25)) if d > 3.5 else rgb("FFB05A"))
            elif d <= sr + 2.5 and (x + y) % 2 == 0:
                wpx(a, sx + x, sy + y, rgb("FFD08A"))
    # Полосы облаков: тёмный верх, коралловое брюхо, одна режет солнце.
    for cx, cy, rx, top, low in ((46, 40, 15, rgb("8A2E4A"), rgb("5A2048")), (100, 26, 20, rgb("7A3A70"), CORAL),
                                 (20, 20, 16, rgb("3A2E78"), rgb("A8507A")), (74, 12, 12, rgb("2C2864"), rgb("5A3C88")),
                                 (118, 38, 14, rgb("B8506A"), GLOW), (8, 34, 10, rgb("9A4670"), rgb("F4A070"))):
        for x in range(-rx, rx + 1):
            h = 1 if abs(x) > rx * 0.6 else 2
            if abs(x) > rx - 2 and x % 2:
                continue
            wrect(a, cx + x, cy, 1, h, top)
            wpx(a, cx + x + 3, cy + h, low)
    # Стая птиц галочками.
    for x, y in ((66, 24), (71, 22), (76, 25), (30, 10)):
        wpx(a, x, y, LACQ_D), wpx(a, x + 1, y + 1, LACQ_D), wpx(a, x + 2, y, LACQ_D)
    # Дальняя гряда со священной вершиной в снегу.
    far, far_l = rgb("5A4684"), rgb("8A6A9C")
    px = 100
    for x in range(128):
        h = 7 + 3 * math.sin(x * math.pi / 32.0 + 1.0) + 2 * math.sin(x * math.pi / 16.0) + 1.5 * math.sin(x * math.pi / 8.0 + 2.0)
        dx = abs((x - px + 64) % 128 - 64)
        cone = 27 - max(dx - 2, 0) * 0.95
        peak = cone > h
        h = int(max(h, cone))
        for j in range(h):
            y = 56 - h + j
            c = far if (x + y) % 5 else mul(far, 0.9)
            if peak and dx < 8 and j < 7 - dx + (dx % 3):
                c = mix(WHITE, CORAL, 0.25) if dx < 2 or (x + j) % 3 else far_l
            elif j == 0:
                c = far_l
            a.px(x, y, c)
    # Туман у подножия: полосы золота дизерингом.
    for y in range(47, 54):
        for x in range(128):
            n = math.sin(x * math.pi / 16.0 + y) + math.sin(x * math.pi / 32.0 - y * 0.5)
            if n > 0.2 - (y - 47) * 0.2 and (x + y) % 2 == 0:
                a.px(x, y, mix(GLOW, CORAL, 0.35))
            elif n > 1.0:
                a.px(x, y, mix(GLOW, CORAL, 0.2))
    # Ближние холмы, утёс под замком и сосны по гребню.
    near, near_l = rgb("201A3A"), rgb("4A3668")
    cx = 16
    tops = []
    for x in range(128):
        h = 4 + 2 * math.sin(x * math.pi / 16.0 + 0.5) + 1.5 * math.sin(x * math.pi / 8.0) + 1.5 * math.sin(x * math.pi / 32.0 + 2.0)
        dx = abs((x - cx + 64) % 128 - 64)
        if dx < 12:
            h = max(h, 13 - max(dx - 6, 0) * 1.6)
        h = max(2, int(h))
        tops.append(56 - h)
        a.rect(x, 56 - h, 1, h, near)
        a.px(x, 56 - h, near_l)
        if dx < 12 and h > 6 and x % 3 == 0:
            a.rect(x, 56 - h + 2, 1, h - 3, near_l)
    for x in (36, 41, 58, 63, 84, 90, 96, 112, 124, 2):
        y = tops[x]
        wrect(a, x, y - 3, 1, 3, near)
        for i, w in enumerate((1, 3, 5)):
            wrect(a, x - w // 2, y - 6 + i, w, 1, MOSS_D if i else near)
        wpx(a, x - 1, y - 5, mul(MOSS_D, 1.3))
    _castle(a, cx, tops[cx])
    _pagoda(a, 74, tops[74] + 1)
    # Гладь пруда: тёмная полоса с отсветами заката под солнцем.
    a.rect(0, 56, 128, 8, rgb("1C1A44"))
    a.rect(0, 56, 128, 1, mix(GLOW, CORAL, 0.5))
    for _ in range(30):
        x = int(sx + a.rng.gauss(0.0, 10.0))
        wrect(a, x, 57 + a.rng.randrange(7), a.rng.randrange(2, 5), 1, CORAL if a.rng.random() < 0.6 else GLOW)
    for _ in range(26):
        wpx(a, a.rng.randrange(128), 57 + a.rng.randrange(7), rgb("36407E"))
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
