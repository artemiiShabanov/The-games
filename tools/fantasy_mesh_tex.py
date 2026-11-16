#!/usr/bin/env python3
"""Текстуры уровня «Фэнтези» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок.
Стиль первой PlayStation: низкое разрешение, в которое втиснуто как можно больше деталей. Все
плитки стыкуются по краям: каждый пиксель ставится по модулю размера. Цвета из палитры
`fantasy16.PALETTE` и те же, что у моделей в `fantasy_mesh_chars.py`. Набор подключает
`lowpoly_meshes.py` через `setting_sets`.

Слоты по ролям: `sand` лесная земля острова с корнями, опавшими лепестками и светящимися
грибками, `planks` настил из горбыля живого дерева (доски вдоль, как у пиратов, стыки вразбежку,
деревянные нагели, поперёк лиана с листьями), `water` основание мира, у фэнтези это пустота:
море облаков под островами, клубы в сиреневых сумерках; `rock` рунная кладка из сиреневого камня
(блоки 16×8 со сдвигом, мох в швах, бирюзовые руны), `sail` полотнище знамени гильдии с золотыми
звёздами и полумесяцами (швы там же, где у паруса), `grass` мох с сиреневыми цветами и спорами,
`road` рунные плиты с колеями там же, где колеи у пиратов, и рунной вязью по оси, `mud` топкий
перегной с переплетением корней (заметно темнее плит), `wind` стрелки разгона на прозрачном с
искрами, `sky` панорама: сумерки, звёзды, полумесяц, летающие острова с башней мага и водопадом,
великое дерево, у горизонта гряда облаков; плитка по горизонтали.

    python3 tools/fantasy_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import fantasy16 as f16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def _pal(i):
    return tuple(f16.PALETTE[i])


SOIL, SOIL_D, SOIL_L = rgb("AE9682"), rgb("826A60"), rgb("CCB69E")  # лесная земля
WOOD, WOOD_D, WOOD_L = _pal(f16.METAL), _pal(f16.DARK), rgb("BE8A54")  # горбыль и корни
STONE, STONE_D, STONE_L = _pal(f16.GREY), rgb("5E5684"), rgb("D4CEE6")  # сиреневый камень
SLAB, SLAB_D, SLAB_L = rgb("857DA4"), rgb("4E4672"), rgb("A8A0C4")  # плиты дороги
MOSS, MOSS_D, MOSS_L = _pal(f16.TAN), rgb("3C7436"), rgb("A2DA6A")
HUMUS, HUMUS_D, HUMUS_L = rgb("30233A"), rgb("1C1426"), rgb("4E3A52")  # топкий перегной
VIOLET, PLUM, LILAC = _pal(f16.VIOLET), _pal(f16.PLUM), rgb("C89CF0")
GOLD, BRASS, GOLD_L = _pal(f16.GOLD), _pal(f16.BRASS), rgb("FFF0A8")
RUNE, RUNE_D, RUNE_L = _pal(f16.AQUA), rgb("1E8A92"), _pal(f16.SKY)
WHITE, RED, INK = _pal(f16.WHITE), _pal(f16.RED), _pal(f16.K)
CLOUD_D, CLOUD, CLOUD_L, CLOUD_T = rgb("3C2C7A"), rgb("8672C6"), rgb("C6A4E0"), rgb("F8DCEA")  # море облаков

# Руны 3×5: врезаны в камень кладки и плит.
RUNES = (("#.#", "#.#", ".#.", ".#.", ".#."),
         ("#..", "##.", "#.#", "#..", "#.."),
         (".#.", "#.#", "#.#", ".#.", ".#."),
         ("##.", "#.#", "##.", "#.#", "#.."),
         (".#.", "###", ".#.", ".#.", "#.#"),
         ("#.#", ".#.", "#.#", "#.#", ".#."))


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


def stamp(a, x, y, rows, c, shade=None):
    """Знак из строк: `#` цвет `c`, под каждым пикселем справа снизу тень `shade` (врезка)."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                if shade is not None:
                    wpx(a, x + i + 1, y + j + 1, shade)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                wpx(a, x + i, y + j, c)


def root(a, x, y, n, vert, dark, light, thick=1):
    """Корень: ломаная в `n` шагов, светлая спинка и тёмный бок, изредка отросток в сторону."""
    for i in range(n):
        for t in range(thick):
            if vert:
                wpx(a, x + t, y, light if t == 0 else mul(light, 0.86))
                wpx(a, x + thick, y, dark)
            else:
                wpx(a, x, y + t, light if t == 0 else mul(light, 0.86))
                wpx(a, x, y + thick, dark)
        if a.rng.random() < 0.12 and 2 < i < n - 3:
            s = a.rng.choice((-1, 1))
            for k in range(1, a.rng.randrange(2, 5)):
                if vert:
                    wpx(a, x + s * k + (thick if s > 0 else 0), y + k, mul(light, 0.9))
                else:
                    wpx(a, x + k, y + s * k + (thick if s > 0 else 0), mul(light, 0.9))
        step = a.rng.choice((-1, 0, 0, 1)) if a.rng.random() < 0.55 else 0
        if vert:
            y += 1
            x += step
        else:
            x += 1
            y += step


def flower(a, x, y, petal, core):
    """Цветок в пять пикселей: четыре лепестка крестом и сердцевина."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        wpx(a, x + dx, y + dy, petal)
    wpx(a, x, y, core)


def glowcap(a, x, y):
    """Светящийся грибок сверху: бирюзовая шляпка в три пикселя, блик и тень под ней."""
    wrect(a, x, y, 3, 2, RUNE)
    wpx(a, x, y, RUNE_L), wpx(a, x + 2, y + 1, RUNE_D)
    wrect(a, x + 1, y + 2, 2, 1, mul(wget(a, x + 1, y + 2), 0.7))


def tex_sand():
    """Лесная земля острова: мягкие пятна тоном, тонкие корни, опавшие сиреневые лепестки,
    камешки и светящиеся грибки."""
    a = lm.Atlas(64, 64, 231)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.06 * math.sin((x + 7.0 * math.sin(y * math.pi / 16.0)) * math.pi / 16.0) \
                + 0.04 * math.sin((y * 2 - x) * math.pi / 32.0)
            a.px(x, y, mul(SOIL, k))
    for _ in range(210):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), SOIL_D if a.rng.random() < 0.6 else SOIL_L)
    # Сухие трещинки: короткие ступеньки.
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        for k in range(a.rng.randrange(3, 6)):
            wpx(a, x + k, y + k // 2, SOIL_D)
            wpx(a, x + k, y + k // 2 + 1, SOIL_L)
    # Корни: два длинных поперёк плитки и несколько коротких.
    root(a, 3, 20, 40, False, mul(WOOD_D, 1.15), WOOD_L, 2)
    root(a, 46, 2, 34, True, mul(WOOD_D, 1.15), WOOD_L, 2)
    for _ in range(4):
        root(a, a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(7, 13), a.rng.random() < 0.5,
             SOIL_D, WOOD)
    # Камешки.
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, STONE_L), wpx(a, x + 1, y, STONE), wpx(a, x, y + 1, STONE), wpx(a, x + 1, y + 1, STONE_D)
        wpx(a, x + 2, y + 1, SOIL_D)
    # Лепестки: пары пикселей, сиреневые и розоватые.
    for _ in range(22):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = VIOLET if a.rng.random() < 0.6 else LILAC
        wpx(a, x, y, c), wpx(a, x + 1, y + a.rng.choice((0, 1)), mul(c, 0.82))
    for x, y in ((12, 44), (53, 51), (30, 8)):
        glowcap(a, x, y)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_planks():
    """Настил из горбыля: доски по 8 вдоль, у каждой свой тон, волокна и сучки, стыки вразбежку с
    деревянными нагелями, поперёк настила лиана с листьями, на одной доске вырезана руна."""
    a = lm.Atlas(64, 64, 233)
    for col in range(8):
        x0 = col * 8
        tone = (1.0, 0.9, 1.08, 0.95, 1.04, 0.88, 1.0, 0.94)[col]
        base = mul(WOOD, tone)
        wrect(a, x0, 0, 8, 64, base)
        # Волокна: длинные тёмные и светлые штрихи вдоль доски.
        for _ in range(7):
            x, y, n = x0 + a.rng.randrange(2, 7), a.rng.randrange(64), a.rng.randrange(6, 18)
            c = mul(WOOD_D, 1.5 * tone) if a.rng.random() < 0.55 else mul(WOOD_L, tone)
            for k in range(n):
                wpx(a, x, y + k, c)
        # Кромки: тёмная щель, светлая фаска, подсохший край.
        wrect(a, x0, 0, 1, 64, WOOD_D)
        wrect(a, x0 + 1, 0, 1, 64, mul(WOOD_L, tone))
        wrect(a, x0 + 7, 0, 1, 64, mul(base, 0.82))
        # Стык досок и нагели по обе стороны от него.
        y = 15 + (col % 2) * 16 + (col // 4) * 32
        wrect(a, x0 + 1, y, 7, 1, WOOD_D)
        wrect(a, x0 + 1, y + 1, 7, 1, mul(WOOD_L, tone))
        for dy in (-3, 4):
            for dx in (2, 5):
                wpx(a, x0 + dx, y + dy, rgb("E2BC84"))
                wpx(a, x0 + dx, y + dy + 1, WOOD_D)
    # Сучки: тёмное ядро в светлом кольце.
    for x, y in ((11, 40), (28, 6), (37, 52), (52, 24), (59, 58)):
        wrect(a, x, y, 2, 3, WOOD_D)
        wpx(a, x - 1, y + 1, mul(WOOD_D, 1.4)), wpx(a, x + 2, y + 1, mul(WOOD_D, 1.4))
        wpx(a, x, y - 1, WOOD_L), wpx(a, x + 1, y + 3, WOOD_L)
    # Вырезанная руна на доске.
    stamp(a, 19, 49, RUNES[1], RUNE, WOOD_D)
    stamp(a, 43, 4, RUNES[4], GOLD, WOOD_D)
    # Лиана поперёк: зелёный жгут волной, тень под ним, листья парами.
    for x in range(64):
        y = 33 + int(round(1.6 * math.sin(x * math.pi / 16.0)))
        wpx(a, x, y + 2, mul(wget(a, x, y + 2), 0.62))
        wpx(a, x, y, MOSS_L if x % 4 else MOSS)
        wpx(a, x, y + 1, MOSS_D)
        if x % 8 == 3:
            up = -1 if (x // 8) % 2 else 1
            for k, c in ((1, MOSS), (2, MOSS_L), (3, MOSS)):
                wpx(a, x + k - 1, y + up * k + (1 if up > 0 else 0), c)
            wpx(a, x + 1, y + up * 3 + (1 if up > 0 else 0), MOSS_D)
        if x % 16 == 9:
            flower(a, x, y - 2, LILAC, GOLD)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Море облаков под островами: тёмная сумеречная глубина в просветах, клубы с розовым светом
    на макушках и фиолетовой тенью снизу, редкие бирюзовые искры. Бежит как зыбь у пиратов."""
    a = lm.Atlas(64, 64, 235)
    # Глубина в просветах: тёмный фиолетовый с дальними полосами тумана.
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = mix(CLOUD_D, CLOUD, 0.32) if w > 0.9 else CLOUD_D
            if w < -1.2:
                c = mul(CLOUD_D, 0.8)
            a.px(x, y, c)
    # Гряды клубов: кружки вдоль пологой линии, дальние ряды темнее, ближние светлее.
    rows = ((6, 0.62), (22, 0.8), (38, 0.9), (54, 1.0))
    for ri, (cy, k) in enumerate(rows):
        x = a.rng.randrange(8)
        end = x + 64 - (6 if ri % 2 else 14)  # в чётных рядах остаётся просвет
        while x < end:
            r = a.rng.randrange(4, 8)
            oy = cy + a.rng.randrange(-3, 4)
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    d = math.hypot(dx, dy * 1.25)
                    if d > r:
                        continue
                    t = dy / float(r)  # -1 макушка, +1 низ
                    lit = t + 0.35 * dx / float(r)
                    if lit < -0.62:
                        c = CLOUD_T
                    elif lit < -0.2:
                        c = CLOUD_L
                    elif lit < 0.45:
                        c = mix(CLOUD_L, CLOUD, 0.7)
                    else:
                        c = mix(CLOUD, CLOUD_D, 0.45)
                    # Кромка клуба шашечкой, чтобы не резало.
                    if d > r - 0.9 and (dx + dy) % 2 and t > 0.1:
                        continue
                    wpx(a, x + dx, oy + dy, mul(c, k) if c != CLOUD_T else mix(CLOUD_L, CLOUD_T, k))
            x += r + a.rng.randrange(2, 5)
    for _ in range(14):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, RUNE_L if a.rng.random() < 0.4 else LILAC)
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_rock():
    """Рунная кладка: блоки 16×8 со сдвигом, у каждого свой тон, светлая кромка сверху, сколы и
    трещины, мох в швах и свисающие с него нитки, на нескольких блоках светятся руны."""
    a = lm.Atlas(64, 64, 237)
    a.rect(0, 0, 64, 64, STONE)
    cells = []
    for row in range(8):
        y = row * 8
        off = (row % 2) * 8
        for col in range(4):
            x = off + col * 16
            tone = a.rng.uniform(0.8, 1.08)
            base = mul(STONE, tone)
            wrect(a, x, y, 16, 8, base)
            wrect(a, x + 1, y + 1, 14, 1, mul(STONE_L, tone))
            wrect(a, x + 1, y + 2, 1, 5, mul(STONE_L, tone * 0.94))
            wrect(a, x + 1, y + 7, 15, 1, mul(base, 0.76))
            wrect(a, x + 15, y + 2, 1, 5, mul(base, 0.84))
            wrect(a, x, y, 1, 8, STONE_D)
            wrect(a, x, y, 16, 1, STONE_D)
            # Скол угла у части блоков.
            if a.rng.random() < 0.3:
                wpx(a, x + 15, y + 1, STONE_D), wpx(a, x + 14, y + 1, mul(base, 0.8)), wpx(a, x + 15, y + 2, STONE_D)
            if a.rng.random() < 0.45:
                cx, cy = x + a.rng.randrange(3, 10), y + a.rng.randrange(3, 5)
                for k in range(a.rng.randrange(2, 5)):
                    wpx(a, cx + k, cy + (k // 2), STONE_D)
                    wpx(a, cx + k, cy + (k // 2) + 1, mul(STONE_L, tone))
            cells.append((x, y))
    for _ in range(120):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), mul(STONE, 0.74) if a.rng.random() < 0.5 else STONE_L)
    # Руны на блоках: тёмная врезка, бирюзовое свечение, блик в верхнем пикселе.
    for i, n in ((1, 0), (6, 2), (11, 3), (16, 5), (21, 1), (26, 4), (31, 0)):
        x, y = cells[i]
        rx = x + 4 + (i % 3) * 3
        wrect(a, rx - 1, y + 2, 5, 5, mul(wget(a, rx, y + 4), 0.86))
        stamp(a, rx, y + 2, RUNES[n], RUNE, STONE_D)
        wpx(a, rx + RUNES[n][0].index("#"), y + 2, RUNE_L)
    # Мох в швах и нитки вниз.
    for _ in range(16):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        n = a.rng.randrange(3, 7)
        wrect(a, x, y, n, 1, MOSS)
        wrect(a, x + 1, y - 1, max(n - 3, 1), 1, MOSS_L)
        for k in range(0, n, 2):
            wrect(a, x + k, y + 1, 1, a.rng.randrange(1, 3), MOSS_D)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_sail():
    """Полотнище знамени гильдии: фиолетовая ткань в косой рубчик, золотые звёзды и полумесяцы
    вразбежку, швы там же, где у паруса, золотая строчка вдоль шва."""
    a = lm.Atlas(32, 32, 239)
    for y in range(32):
        for x in range(32):
            u = (x + y) % 4
            k = (1.0, 1.07, 1.0, 0.92)[u] + 0.05 * math.sin(y * math.pi / 8.0)
            a.px(x, y, mul(VIOLET, k))
    # Складки: мягкие полосы поперёк, как у паруса на 10 и 21.
    for y in (10, 21):
        a.rect(0, y, 32, 1, mul(VIOLET, 0.8))
        a.rect(0, y + 1, 32, 1, mul(VIOLET, 1.14))
    # Звёзды с лучами и полумесяцы.
    for x, y in ((8, 5), (24, 26)):
        for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0)):
            wpx(a, x + dx, y + dy, GOLD)
        flower(a, x, y, GOLD, GOLD_L)
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            wpx(a, x + dx, y + dy, BRASS)
    for x, y in ((24, 5), (8, 26)):
        for dx, dy, c in ((0, -2, GOLD), (-1, -1, GOLD), (-2, 0, GOLD_L), (-1, 1, GOLD), (0, 2, GOLD), (1, 2, BRASS),
                          (-1, 0, BRASS), (1, -2, BRASS)):
            wpx(a, x + dx, y + dy, c)
    for x, y in ((16, 15), (0, 16), (5, 15), (27, 16), (13, 3), (19, 29)):
        wpx(a, x, y, LILAC)
    # Швы полотнищ и золотая строчка рядом.
    for x in (0, 16):
        a.rect(x, 0, 1, 32, PLUM)
        for y in range(1, 32, 4):
            wpx(a, x + 1, y, GOLD), wpx(a, x + 1, y + 1, BRASS)
    a.noise(0, 0, 32, 32, 0.05)
    return a


def tex_grass():
    """Мох: бархатные кочки тоном, ворсинки в два пикселя, сиреневые цветы с золотой серединой,
    светящиеся споры и грибки, проплешины лесной земли."""
    a = lm.Atlas(64, 64, 241)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.09 * math.sin(x * math.pi / 8.0 + 2.0 * math.sin(y * math.pi / 16.0)) \
                * math.sin(y * math.pi / 8.0 + 1.5 * math.sin(x * math.pi / 32.0))
            a.px(x, y, mul(mix(MOSS, MOSS_D, 0.22), k))
    for _ in range(300):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = MOSS_D if a.rng.random() < 0.55 else MOSS_L
        wpx(a, x, y, c), wpx(a, x, y + 1, mul(c, 0.9))
    for _ in range(6):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 4, 2, SOIL_D), wrect(a, x + 1, y - 1, 2, 1, SOIL_D)
        wpx(a, x + 1, y, SOIL), wpx(a, x + 2, y, SOIL_L)
    # Цветы: тень под венчиком, чтобы не тонули во мху.
    for i in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x + 1, y + 2, MOSS_D), wpx(a, x, y + 2, MOSS_D)
        flower(a, x, y, LILAC if i % 3 else WHITE, GOLD)
    for x, y in ((9, 13), (41, 37), (56, 6)):
        glowcap(a, x, y)
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, RUNE_L), wpx(a, x + 1, y + 1, MOSS_D)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_road():
    """Дорога из рунных плит: плиты 32×32 со швами и фаской, укатанные колеи там же, где у
    пиратов, рунная вязь по оси вместо пунктира, малые руны по углам плит, мох в швах, выбоины."""
    a = lm.Atlas(64, 64, 243)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.04 * math.sin(y * math.pi / 8.0 + x * math.pi / 32.0)
            tone = 0.94 if ((y // 32) + (x // 32)) % 2 else 1.0
            a.px(x, y, mul(SLAB, k * tone))
    for _ in range(190):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), mul(SLAB, 0.8) if a.rng.random() < 0.55 else SLAB_L)
    # Колеи там же, где у пиратов.
    for x in (18, 19, 44, 45):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 0.82))
    for x in (20, 46):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 1.12))
    # Швы плит: поперёк и вдоль, светлая фаска за швом.
    for y in (0, 32):
        a.rect(0, y, 64, 1, SLAB_D)
        a.rect(0, y + 1, 64, 1, SLAB_L)
        a.rect(0, (y - 1) % 64, 64, 1, mul(SLAB, 0.84))
    for x in (0, 32):
        a.rect(x, 0, 1, 64, SLAB_D)
        a.rect(x + 1, 0, 1, 64, mul(SLAB_L, 0.96))
    # Рунная вязь по оси: врезанная полоса в два пикселя с засечками, светится бирюзой.
    for y0 in (6, 38):
        a.rect(30, y0 - 1, 5, 14, mul(SLAB, 0.7))
        a.rect(31, y0, 2, 12, RUNE)
        a.rect(31, y0, 1, 12, RUNE_L)
        for k in (2, 5, 9):
            a.px(30, y0 + k, RUNE), a.px(33, y0 + k + 1, RUNE)
            a.px(31, y0 + k + 1, RUNE_D), a.px(32, y0 + k - 1 if k > 2 else y0, RUNE_D)
    # Малые руны по углам плит: выбиты, без свечения.
    for i, (x, y) in enumerate(((5, 5), (55, 5), (5, 24), (55, 24), (5, 37), (55, 37), (5, 56), (55, 56))):
        stamp(a, x, y, RUNES[i % len(RUNES)], SLAB_D, SLAB_L)
    # Мох в швах.
    for _ in range(12):
        if a.rng.random() < 0.6:
            x, y, n = a.rng.randrange(64), a.rng.choice((0, 32)), a.rng.randrange(2, 6)
            wrect(a, x, y, n, 1, MOSS), wpx(a, x + 1, y + 1, MOSS_D)
        else:
            x, y, n = a.rng.choice((0, 32)), a.rng.randrange(64), a.rng.randrange(2, 5)
            wrect(a, x, y, 1, n, MOSS), wpx(a, x + 1, y + 1, MOSS_L)
    # Выбоины и трещины.
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, SLAB_D), wpx(a, x + 1, y + 1, SLAB_D), wpx(a, x + 2, y + 1, SLAB_D), wpx(a, x + 1, y + 2, SLAB_L)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_mud():
    """Топкий перегной: тёмная сырая земля волнами, лужицы с сиреневым отсветом, переплетение
    корней, прелые листья. Заметно темнее плит дороги."""
    a = lm.Atlas(64, 64, 245)
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 4.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            a.px(x, y, mul(HUMUS, 1.0 + 0.16 * w))
    # Лужицы: тёмный овал, сиреневый блик у верхнего края.
    for _ in range(9):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(2, 5)
        for y in range(-r, r + 1):
            for x in range(-r * 2, r * 2 + 1):
                if (x / 2.0) ** 2 + y ** 2 <= r * r:
                    wpx(a, cx + x, cy + y, HUMUS_D)
        wrect(a, cx - 2, cy - r + 1, 3, 1, PLUM)
        wpx(a, cx + 1, cy - r + 1, VIOLET)
    for _ in range(190):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), HUMUS_L if a.rng.random() < 0.45 else HUMUS_D)
    # Корни поверх: два толстых и сеть тонких.
    bark, bark_l = rgb("3A2630"), rgb("6A4A46")
    root(a, 0, 12, 64, False, HUMUS_D, bark_l, 2)
    root(a, 22, 0, 64, True, HUMUS_D, bark_l, 2)
    for _ in range(7):
        root(a, a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(8, 20), a.rng.random() < 0.5,
             HUMUS_D, bark if a.rng.random() < 0.5 else mul(bark_l, 0.85))
    # Прелые листья и редкие споры.
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = mul(PLUM, 0.9) if a.rng.random() < 0.6 else mul(MOSS_D, 0.8)
        wpx(a, x, y, c), wpx(a, x + 1, y, c), wpx(a, x + 1, y + 1, mul(c, 0.7))
    for _ in range(6):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), RUNE_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_wind():
    """Поток маны: золотые стрелки вперёд на прозрачном и искры между ними, текстура бежит по
    полосе."""
    a = lm.Atlas(32, 32, 247)
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, GOLD_L)
                a.px(x, row + 4 + k, GOLD)
                a.px(x, row + 5 + k, BRASS)
        # Искры: крестик под остриём и точки у крыльев.
        flower(a, 15 + (row // 16), row + 10, RUNE, RUNE_L)
        a.px(5, row + 5, RUNE_L), a.px(26, row + 6, RUNE_L)
        a.px(2, row + 14, RUNE), a.px(29, row + 15, RUNE)
    return a


def _island(a, cx, top, hw, depth, haze, sky, trees=(), tower=None, fall=None):
    """Летающий остров: плоская макушка во мху, перевёрнутый каменный конус с зубцами снизу.
    `haze` подмешивает небо (даль), `trees` смещения деревьев, `tower` смещение башни мага,
    `fall` смещение водопада."""
    def hz(c):
        return mix(c, sky, haze)

    for x in range(-hw, hw + 1):
        t = abs(x) / float(hw)
        d = depth * (1.0 - t ** 1.5) + (a.rng.randrange(3) - 1 if abs(x) < hw - 1 else 0)
        d = max(1, int(round(d)))
        for k in range(d):
            c = STONE if x < -hw * 0.35 else (mul(STONE, 0.78) if x < hw * 0.3 else STONE_D)
            if k > d * 0.55:
                c = mul(c, 0.72)
            wpx(a, cx + x, top + 2 + k, hz(c))
        wpx(a, cx + x, top, hz(MOSS_L))
        wpx(a, cx + x, top + 1, hz(MOSS_D))
    # Свисающие корни под краями.
    for x in (-hw + 2, hw - 3):
        for k in range(2):
            wpx(a, cx + x, top + 2 + k + int(depth * 0.4), hz(WOOD_D))
    for tx, r in trees:
        wrect(a, cx + tx, top - r, 1, r, hz(WOOD_D))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    c = LILAC if dx + dy < -r * 0.4 else (VIOLET if dx + dy < r * 0.7 else PLUM)
                    wpx(a, cx + tx + dx, top - r - r + dy, hz(c))
    if tower is not None:
        x = cx + tower
        wrect(a, x, top - 10, 3, 10, hz(STONE))
        wrect(a, x + 2, top - 10, 1, 10, hz(STONE_D))
        wpx(a, x + 1, top - 7, hz(GOLD)), wpx(a, x + 1, top - 3, hz(GOLD))
        for k in range(5):  # острая крыша шляпой
            wrect(a, x - 1 + (k + 1) // 2, top - 11 - k, max(5 - k - (k + 1) // 2 * 1, 1), 1, hz(_pal(f16.SEA)))
        wpx(a, x + 1, top - 16, hz(_pal(f16.SEA)))
        wpx(a, x + 1, top - 17, RUNE_L)
    if fall is not None:
        x = cx + fall
        for k in range(depth + 9):
            fade = min(1.0, k / float(depth + 9))
            wpx(a, x, top + 1 + k, mix(RUNE_L if k % 3 else WHITE, wget(a, x, top + 1 + k), fade * 0.85))


def tex_sky():
    """Панорама купола: сиреневые сумерки от индиго к розовому, звёзды и полумесяц, перистые
    облака, летающие острова (на ближнем башня мага и водопад), великое дерево с огоньками в
    кроне, у горизонта гряда облаков и море облаков под ней. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 249)
    top, midc, low = rgb("1C1650"), rgb("6E42A6"), rgb("F2AEBE")
    for y in range(64):
        t = min(y / 55.0, 1.0)
        c = mix(top, midc, t / 0.62) if t < 0.62 else mix(midc, low, (t - 0.62) / 0.38)
        a.rect(0, y, 128, 1, c)
    sky_low = mix(midc, low, 0.6)
    # Звёзды гуще к зениту, несколько крестиков.
    for _ in range(120):
        y = int(40 * a.rng.random() ** 1.7)
        k = a.rng.uniform(0.5, 1.0) * (1.0 - y / 60.0)
        wpx(a, a.rng.randrange(128), y, mix(wget(a, 0, y), rgb("FFF4E0"), k))
    for x, y in ((9, 6), (58, 4), (77, 17), (88, 7), (66, 12)):
        wpx(a, x, y, WHITE)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            wpx(a, x + dx, y + dy, mix(wget(a, x + dx, y + dy), RUNE_L, 0.6))
    # Полумесяц: диск без сдвинутого диска, вокруг слабое сияние.
    mx, my, mr = 116, 10, 6
    for y in range(-mr - 2, mr + 3):
        for x in range(-mr - 2, mr + 3):
            d = math.hypot(x, y)
            inner = math.hypot(x - 3, y + 1) <= mr - 0.5
            if d <= mr and not inner:
                wpx(a, mx + x, my + y, rgb("FFF2CC") if d < mr - 1 else rgb("F6D69A"))
            elif mr < d <= mr + 2 and (x + y) % 2 == 0 and not inner:
                wpx(a, mx + x, my + y, mix(wget(a, mx + x, my + y), rgb("F6D69A"), 0.3))
    # Перистые облака: тонкие розовые штрихи с подбоем.
    for _ in range(8):
        x, y, n = a.rng.randrange(128), a.rng.randrange(24, 46), a.rng.randrange(8, 20)
        for k in range(n):
            if 1 < k < n - 2:
                wpx(a, x + k, y - 1, mix(wget(a, x + k, y - 1), rgb("FFD6DC"), 0.75))
            wpx(a, x + k, y, mix(wget(a, x + k, y), rgb("B47CC8"), 0.7))
    # Великое дерево: ствол с расходящимися корнями, ветви, крона клубами, огоньки.
    tx = 38
    trunk, trunk_l = mix(rgb("3A2448"), sky_low, 0.12), mix(rgb("7A5470"), sky_low, 0.12)
    for y in range(24, 60):
        hw = 2 + ((y - 30) ** 2) / 75.0 if y > 30 else 2
        hw = int(round(hw))
        for x in range(-hw, hw + 1):
            wpx(a, tx + x, y, trunk_l if x <= -hw + 1 else trunk)
        if y % 5 == 0:
            wpx(a, tx, y, trunk_l), wpx(a, tx + 1, y + 1, trunk_l)
    for sx, n in ((-1, 12), (1, 12), (-1, 7), (1, 7)):  # ветви
        for k in range(n):
            y = (27 if n == 12 else 23) - k // (2 if n == 12 else 1)
            wpx(a, tx + sx * (2 + k), y, trunk)
            wpx(a, tx + sx * (2 + k), y + 1, trunk)
    for dx, dy, r in ((-15, 2, 6), (15, 2, 6), (-9, -3, 7), (9, -3, 7), (0, -7, 8), (-4, 1, 6), (5, 1, 6), (-20, 6, 4),
                      (20, 6, 4)):
        cx, cy = tx + dx, 18 + dy
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                d = math.hypot(x, y * 1.15)
                if d > r:
                    continue
                lit = (x + y * 1.4) / float(r)
                c = LILAC if lit < -0.75 else (VIOLET if lit < 0.35 else PLUM)
                if d > r - 1 and (x + y) % 2 and y > 0:
                    continue
                wpx(a, cx + x, cy + y, mix(c, sky_low, 0.14))
    for dx, dy in ((-17, 9), (-12, 6), (-6, 8), (7, 9), (13, 6), (19, 10), (0, 4), (-21, 11)):  # лианы и огоньки
        for k in range(2 + (dx % 3)):
            wpx(a, tx + dx, 18 + dy + k, mix(PLUM, sky_low, 0.2))
        wpx(a, tx + dx, 18 + dy + 2 + (dx % 3), RUNE_L if dx % 2 else GOLD_L)
    # Летающие острова: дальние в дымке, ближний с башней мага и водопадом.
    _island(a, 6, 30, 7, 6, 0.5, midc, trees=((-3, 2), (3, 1)))
    _island(a, 122, 44, 5, 4, 0.55, sky_low, trees=((0, 1),))
    _island(a, 70, 40, 6, 5, 0.45, sky_low, trees=((-2, 2),))
    _island(a, 96, 36, 13, 10, 0.1, sky_low, trees=((-9, 2), (-5, 3), (8, 2)), tower=1, fall=10)
    # Гряда облаков у горизонта и море облаков под ней.
    for x in range(128):
        h = 4 + 2.2 * math.sin(x * math.pi / 16.0) + 1.6 * math.sin(x * math.pi / 8.0 + 1.0) + 1.5 * math.sin(x * math.pi / 32.0 + 2.0)
        h = max(1, int(round(h)))
        a.rect(x, 56 - h, 1, h, CLOUD_L)
        a.px(x, 56 - h, CLOUD_T)
        if h > 3:
            a.px(x, 56 - h + 1, mix(CLOUD_L, CLOUD_T, 0.5))
        a.px(x, 55, mix(CLOUD_L, CLOUD, 0.6))
    for y in range(56, 64):
        a.rect(0, y, 128, 1, mix(CLOUD, CLOUD_D, (y - 56) / 12.0))
    for x in range(128):
        if math.sin(x * math.pi / 8.0) + math.sin(x * math.pi / 32.0 + 1.0) > 0.4:
            a.px(x, 57, CLOUD_L)
        if math.sin(x * math.pi / 16.0 + 2.0) > 0.3:
            a.px(x, 60, mix(CLOUD, CLOUD_L, 0.6))
    for _ in range(24):
        wpx(a, a.rng.randrange(128), 58 + a.rng.randrange(6), mix(CLOUD, CLOUD_D, 0.5))
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
