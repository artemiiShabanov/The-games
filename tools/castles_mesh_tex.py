#!/usr/bin/env python3
"""Текстуры уровня «Замков» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок.
Стиль первой PlayStation: низкое разрешение, в которое втиснуто как можно больше деталей. Все
плитки стыкуются по краям: каждый пиксель ставится по модулю размера. Цвета из палитры
`castles16.PALETTE` и те же, что у моделей в `castles_mesh_chars.py`.

Слоты по ролям: `sand` утоптанный двор замка, `planks` дубовый настил моста с железными полосами,
`water` основание мира, у замков это твердь: луг до горизонта, по которому ветер гонит волны;
`rock` кладка стены, `sail` полосатое полотно турнирного шатра, `grass` газон с клевером и
ромашками, `road` брусчатка с колеями там же, где колеи у пиратов, `mud` раскисшая после дождя
земля (заметно темнее брусчатки), `wind` стрелки разгона на прозрачном, `sky` панорама: день,
облака, холмы и замок с башнями, плитка по горизонтали.

    python3 tools/castles_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

STONE, STONE_D, STONE_L = rgb("8C8884"), rgb("3C4050"), rgb("B4B2AC")  # кладка, швы, блик камня
EARTH, EARTH_D, EARTH_L = rgb("C2A272"), rgb("94744A"), rgb("DCC090")  # утоптанный двор
OAK, OAK_D, OAK_L = rgb("9C642C"), rgb("5E3A1C"), rgb("C08A48")  # дуб моста
IRON, IRON_D, IRON_L = rgb("3C4050"), rgb("23252F"), rgb("5E6478")
GRASS, GRASS_D, GRASS_L = rgb("5CAE4A"), rgb("2A6A3E"), rgb("8CD060")
RED, RED_D = rgb("D2302C"), rgb("942838")
GOLD, GOLD_D = rgb("F4C84A"), rgb("9C642C")
CREAM = rgb("EADFC4")
WHITE = rgb("E8ECF2")


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def spans(rng, total, sizes):
    """Режет отрезок `total` на куски из `sizes` в случайном порядке: [(начало, длина), …]."""
    out, x = [], 0
    while x < total:
        fit = [s for s in sizes if total - x - s == 0 or total - x - s >= min(sizes)]
        s = rng.choice(fit) if fit else total - x
        out.append((x, s))
        x += s
    return out


def hoof(a, x, y, c):
    """След подковы: дужка 4×3, открытая вниз."""
    for dx, dy in ((1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2)):
        wpx(a, x + dx, y + dy, c)


def tex_sand():
    """Утоптанный двор замка: светлая глина пятнами, соломинки, камешки, следы подков."""
    a = lm.Atlas(64, 64, 231)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.05 * math.sin(x * math.pi / 16.0 + 2.0 * math.sin(y * math.pi / 32.0)) \
                + 0.04 * math.sin((y * 3 - x) * math.pi / 32.0)
            a.px(x, y, mul(EARTH, k))
    for _ in range(200):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), EARTH_D if a.rng.random() < 0.55 else EARTH_L)
    # Мелкие трещины сухой глины: ломаные в три-пять пикселей.
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        for k in range(a.rng.randrange(3, 6)):
            wpx(a, x + k, y + (k * a.rng.choice((0, 1, 1))) // 2, mul(EARTH_D, 0.9))
    # Соломинки: короткие жёлтые штрихи с тенью снизу.
    for _ in range(11):
        x, y, d = a.rng.randrange(64), a.rng.randrange(64), a.rng.choice((-1, 0, 1))
        for k in range(a.rng.randrange(3, 5)):
            wpx(a, x + k, y + (k * d) // 2, rgb("E4CC84"))
            wpx(a, x + k, y + (k * d) // 2 + 1, EARTH_D)
    for _ in range(5):
        hoof(a, a.rng.randrange(64), a.rng.randrange(64), mul(EARTH_D, 0.92))
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, STONE_L), wpx(a, x + 1, y, STONE), wpx(a, x, y + 1, STONE), wpx(a, x + 1, y + 1, EARTH_D)
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_planks():
    """Дубовый настил моста: широкие доски по 16 с волокном и сучками, стыки вразбежку, поперёк
    две железные полосы с заклёпками."""
    a = lm.Atlas(64, 64, 233)
    for col in range(4):
        x0 = col * 16
        tone = (1.0, 0.9, 1.06, 0.95)[col]
        ph = a.rng.uniform(0.0, 6.0)
        for y in range(64):
            for i in range(16):
                # Волокно: вытянутые вдоль доски полосы, чуть гуляют.
                g = math.sin((i + 1.5 * math.sin(y * math.pi / 32.0 + ph)) * math.pi / 2.0 + ph)
                wpx(a, x0 + i, y, mul(OAK, tone * (1.0 + 0.09 * g)))
        wrect(a, x0, 0, 1, 64, OAK_D)
        wrect(a, x0 + 1, 0, 1, 64, mul(OAK_L, tone))
        wrect(a, x0 + 15, 0, 1, 64, mul(OAK, tone * 0.8))
        # Стык досок по торцу и сучок с кольцом.
        jy = (9, 41, 25, 57)[col]
        wrect(a, x0 + 1, jy, 15, 1, OAK_D)
        wrect(a, x0 + 1, jy + 1, 14, 1, mul(OAK_L, tone))
        ky = (jy + 22 + a.rng.randrange(6)) % 64
        kx = x0 + a.rng.randrange(5, 11)
        for dx, dy in ((-2, 0), (2, 0), (-1, -1), (0, -1), (1, -1), (-1, 1), (0, 1), (1, 1)):
            wpx(a, kx + dx, ky + dy, mul(OAK_D, 1.25))
        wpx(a, kx, ky, OAK_D), wpx(a, kx - 1, ky, OAK_D), wpx(a, kx + 1, ky, OAK_D)
    # Железные полосы поперёк досок: кромка, блик, заклёпка на каждой доске.
    for y0 in (16, 48):
        wrect(a, 0, y0, 64, 5, IRON)
        wrect(a, 0, y0, 64, 1, IRON_L)
        wrect(a, 0, y0 + 4, 64, 1, IRON_D)
        wrect(a, 0, y0 + 5, 64, 1, OAK_D)
        for x in range(8, 64, 16):
            wpx(a, x, y0 + 2, WHITE), wpx(a, x + 1, y0 + 2, IRON_L)
            wpx(a, x, y0 + 3, IRON_D), wpx(a, x + 1, y0 + 3, IRON_D)
        for _ in range(8):
            wpx(a, a.rng.randrange(64), y0 + 1 + a.rng.randrange(3), rgb("7A4A30"))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Основание мира, твердь: луг до горизонта. Та же зыбь, что у моря пиратов, только это ветер
    гонит светлые волны по траве; клевер тёмными пятнами, ромашки, лютики и маки точками."""
    a = lm.Atlas(64, 64, 235)
    deep, mid, crest = rgb("5E9C46"), rgb("82B850"), rgb("C6DC78")
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = mid if w > 0.3 else deep
            if w > 1.35:
                c = mix(mid, crest, 0.45)
            if w > 1.78:
                c = crest
            if w < -1.5:
                c = mul(deep, 0.88)
            a.px(x, y, c)
    # Травинки: штрих в два пикселя темнее или светлее.
    for _ in range(170):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = rgb("3E7C3C") if a.rng.random() < 0.5 else rgb("A8D062")
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
    # Куртины клевера.
    for _ in range(6):
        cx, cy = a.rng.randrange(64), a.rng.randrange(64)
        for _ in range(9):
            wpx(a, cx + a.rng.randrange(-3, 4), cy + a.rng.randrange(-2, 3), rgb("3E7C3C"))
        wpx(a, cx, cy, rgb("E89CC0")), wpx(a, cx + 2, cy + 1, rgb("E89CC0"))
    for _ in range(16):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, WHITE), wpx(a, x, y + 1, rgb("3E7C3C"))
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, GOLD), wpx(a, x, y + 1, rgb("3E7C3C"))
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, RED), wpx(a, x + 1, y, RED_D), wpx(a, x, y + 1, rgb("3E7C3C"))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_rock():
    """Кладка стены: высокие ряды тёсаных блоков чередуются с низкими, длина блоков разная, у
    каждого свой тон, светлая кромка сверху и тень снизу, сколы, трещины, мох в швах."""
    a = lm.Atlas(64, 64, 237)
    a.rect(0, 0, 64, 64, STONE_D)
    y = 0
    for row in range(8):
        h = 10 if row % 2 == 0 else 6
        off = a.rng.randrange(16)
        for x, w in spans(a.rng, 64, (8, 12, 16, 20) if h == 10 else (8, 12, 16)):
            x += off
            tone = a.rng.uniform(0.86, 1.14)
            warm = a.rng.random() < 0.25
            base = mix(STONE, rgb("A89878"), 0.45) if warm else STONE
            wrect(a, x + 1, y + 1, w - 1, h - 1, mul(base, tone))
            wrect(a, x + 1, y + 1, w - 1, 1, mul(STONE_L, tone))
            wrect(a, x + 1, y + 2, 1, h - 3, mul(base, tone * 1.1))
            wrect(a, x + 1, y + h - 1, w - 1, 1, mul(base, tone * 0.74))
            wrect(a, x + w - 1, y + 2, 1, h - 2, mul(base, tone * 0.84))
            # Скол угла и трещина.
            if a.rng.random() < 0.35:
                wpx(a, x + w - 1, y + 1, STONE_D), wpx(a, x + w - 2, y + 1, mul(base, tone * 0.8))
            if a.rng.random() < 0.4 and w >= 12:
                cx, cy = x + a.rng.randrange(3, w - 5), y + a.rng.randrange(3, h - 2)
                for k in range(a.rng.randrange(2, 5)):
                    wpx(a, cx + k, min(cy + (k + 1) // 2, y + h - 2), mul(base, tone * 0.66))
            # Насечка каменотёса: редкие светлые и тёмные точки.
            for _ in range(w * h // 14):
                wpx(a, x + a.rng.randrange(2, w - 1), y + a.rng.randrange(3, h - 1),
                    mul(base, tone * (0.86 if a.rng.random() < 0.6 else 1.12)))
        y += h
    # Мох в швах: лежит на горизонтальном шве и свисает на пиксель-два.
    seams = (0, 10, 16, 26, 32, 42, 48, 58)
    for _ in range(13):
        x, y = a.rng.randrange(64), a.rng.choice(seams)
        w = a.rng.randrange(3, 8)
        wrect(a, x, y, w, 1, GRASS)
        for i in range(w):
            if a.rng.random() < 0.6:
                wpx(a, x + i, y + 1, GRASS_D)
        wpx(a, x + 1, y - 1, GRASS_L)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_sail():
    """Полотно турнирного шатра: красная и кремовая полосы по 16, складки тоном, переплетение
    нитей, золотой кант у шва, на красном золотая корона, на кремовом красный крест."""
    a = lm.Atlas(32, 32, 239)
    for y in range(32):
        for x in range(32):
            base = RED if x < 16 else CREAM
            k = 1.0 + 0.09 * math.cos((x % 16) * math.pi / 8.0 + math.pi) + 0.03 * math.sin(y * math.pi / 8.0)
            if y % 2 == 0:
                k *= 0.95
            if (x + y) % 4 == 0:
                k *= 1.05
            a.px(x, y, mul(base, k))
    for x in (0, 16):
        a.rect(x, 0, 1, 32, mul(RED_D, 0.8))
        # Золотой кант: стежки через один.
        for y in range(0, 32, 2):
            a.px(x + 1, y, GOLD)
            a.px(x + 1, y + 1, GOLD_D)
    # Корона на красной полосе: три зубца, обод, тень.
    for cy in (6, 22):
        for dx in (0, 3, 6):
            a.px(5 + dx, cy, GOLD)
            a.px(5 + dx, cy + 1, GOLD)
        a.px(6, cy + 1, GOLD), a.px(10, cy + 1, GOLD)
        a.rect(5, cy + 2, 7, 2, GOLD)
        a.rect(5, cy + 4, 7, 1, GOLD_D)
        a.px(8, cy + 2, RED_D)
    # Лапчатый крест на кремовой полосе.
    for cy in (14, 30):
        for k in range(-3, 4):
            wpx(a, 24 + k, cy, RED), wpx(a, 24, cy + k, RED)
        for sx, sy in ((-3, -1), (-3, 1), (3, -1), (3, 1), (-1, -3), (1, -3), (-1, 3), (1, 3)):
            wpx(a, 24 + sx, cy + sy, RED_D)
    a.noise(0, 0, 32, 32, 0.05)
    return a


def tex_grass():
    """Газон замка: густая трава пятнами, травинки в два пикселя, трилистники клевера, ромашки с
    жёлтой серединкой, проплешины земли."""
    a = lm.Atlas(64, 64, 241)
    g = rgb("4E9E46")
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.08 * math.sin(x * math.pi / 16.0 + 1.5 * math.sin(y * math.pi / 16.0)) \
                + 0.04 * math.sin((x + 2 * y) * math.pi / 32.0)
            a.px(x, y, mul(g, k))
    for _ in range(300):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = GRASS_D if a.rng.random() < 0.5 else GRASS_L
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
    # Пучки: три травинки веером.
    for _ in range(14):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, GRASS_L), wpx(a, x + 1, y + 1, GRASS_L), wpx(a, x + 2, y, GRASS_L)
        wpx(a, x + 1, y + 2, GRASS_D), wpx(a, x, y + 2, GRASS_D), wpx(a, x + 2, y + 2, GRASS_D)
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 3, 2, EARTH_D)
        wpx(a, x + 1, y, EARTH)
    # Клевер: тёмный трилистник.
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        for dx, dy in ((0, 0), (2, 0), (1, 1), (1, -1)):
            wpx(a, x + dx, y + dy, mul(GRASS_D, 1.15))
    # Ромашки: белый крестик, жёлтая серединка.
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            wpx(a, x + dx, y + dy, WHITE)
        wpx(a, x, y, GOLD)
        wpx(a, x + 1, y + 1, GRASS_D)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_road():
    """Брусчатка: ряды округлых камней разной длины, у каждого блик сверху и тень снизу, колеи
    повозок там же, где у пиратов, по оси ряд крупных плит, в швах земля и травинки."""
    a = lm.Atlas(64, 64, 243)
    cob, seam = rgb("86827E"), rgb("4A4640")
    a.rect(0, 0, 64, 64, seam)
    for row in range(8):
        y = row * 8
        off = a.rng.randrange(8)
        for x, w in spans(a.rng, 64, (6, 8, 10)):
            x += off
            tone = a.rng.uniform(0.86, 1.14)
            base = mix(cob, rgb("9C8C74"), 0.5) if a.rng.random() < 0.3 else cob
            for j in range(1, 8):
                for i in range(1, w):
                    corner = (i in (1, w - 1)) and (j in (1, 7))
                    if corner:
                        continue
                    k = tone
                    if j == 1 or (i == 1 and j < 6):
                        k *= 1.2
                    elif j == 7 or i == w - 1:
                        k *= 0.74
                    elif j == 2:
                        k *= 1.08
                    wpx(a, x + i, y + j, mul(base, k))
    # Колеи: камень в них стёрт и темнее, рядом светлая кромка.
    for x in (18, 19, 44, 45):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 0.82))
    for x in (20, 46):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 1.12))
    # Осевой ряд крупных плит: вместо разметки.
    for y0 in (0, 32):
        tone = 1.06 if y0 == 0 else 0.98
        a.rect(29, y0, 6, 32, seam)
        a.rect(30, y0 + 1, 4, 30, mul(rgb("A09C96"), tone))
        a.rect(30, y0 + 1, 4, 1, mul(rgb("C4C0B8"), tone))
        a.rect(30, y0 + 30, 4, 1, mul(rgb("706C68"), tone))
        a.rect(33, y0 + 2, 1, 28, mul(rgb("86827E"), tone))
        for k in range(3):
            a.px(31 + k % 2, y0 + 9 + k * 6, mul(rgb("706C68"), tone))
    # Земля и трава в швах.
    for _ in range(60):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        wpx(a, x, y, EARTH_D)
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        if 28 <= x <= 35:
            continue
        wpx(a, x, y, GRASS), wpx(a, x + 1, y, GRASS_D), wpx(a, x, y - 1, GRASS_L)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_mud():
    """Раскисшая земля после дождя: тёмные борозды, лужи с отражением неба, следы подков, комья.
    Заметно темнее брусчатки."""
    a = lm.Atlas(64, 64, 245)
    mud, mud_d, mud_l = rgb("46342A"), rgb("2A1E1A"), rgb("6A5040")
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 4.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            a.px(x, y, mul(mud, 1.0 + 0.15 * w))
    # Лужи: тёмный берег, синеватая вода, полоска отражения.
    for _ in range(6):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 6)
        for y in range(-r - 1, r + 2):
            for x in range(-r * 2 - 1, r * 2 + 2):
                d = (x / 2.0) ** 2 + y ** 2
                if d <= (r - 0.8) ** 2:
                    wpx(a, cx + x, cy + y, rgb("2E3C5C") if y > -r + 2 else rgb("3E5078"))
                elif d <= r * r:
                    wpx(a, cx + x, cy + y, mud_d)
        for k in range(-r + 1, r):
            wpx(a, cx + k, cy - 1, rgb("86BEE8") if abs(k) < r - 2 else rgb("4676C0"))
        wpx(a, cx + r, cy + 1, rgb("D3ECF6"))
    for _ in range(210):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), mud_l if a.rng.random() < 0.45 else mud_d)
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        hoof(a, x, y, mud_d)
        wpx(a, x + 1, y + 1, mud_l), wpx(a, x + 2, y + 1, mud_l)
    # Комья с бликом и редкие соломинки.
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, mud_l), wpx(a, x + 1, y, mud_l), wpx(a, x, y + 1, mud_d), wpx(a, x + 1, y + 1, mud_d)
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, rgb("A89058")), wpx(a, x + 1, y, rgb("A89058")), wpx(a, x + 2, y + 1, rgb("A89058"))
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Разгонная полоса: белые стрелки вперёд с золотой кромкой, как шевроны на вымпеле, на
    прозрачном; текстура бежит по полосе."""
    a = lm.Atlas(32, 32, 247)
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, WHITE)
                a.px(x, row + 4 + k, GOLD)
                a.px(x, row + 5 + k, mul(GOLD_D, 1.15))
    return a


def _cloud(a, cx, cy, w):
    """Кучевое облако: плоское дно, три-четыре бугра, тень снизу, блик сверху."""
    for k in range(w):
        t = k / float(w - 1)
        h = int(round(1 + 5.0 * math.sin(math.pi * t) * (0.72 + 0.28 * abs(math.sin(t * math.pi * 3.2 + cx)))))
        for j in range(h):
            c = rgb("F6F8F6") if j < h - 1 else rgb("FFFFFF")
            if j == 0:
                c = rgb("B4CCE0")
            elif j == 1 and h > 3:
                c = rgb("DCE8F0")
            a.px((cx + k) % 128, cy - j, c)


def _fir(a, x, y, h, c):
    """Ель силуэтом: треугольник с зубцами, основание в (x, y)."""
    for j in range(h):
        half = (j * 2 // 3 + (j % 2)) // 1
        half = min(half, 2)
        for i in range(-half, half + 1):
            a.px((x + i) % 128, y - h + 1 + j, c)


def _tower(a, x, y, w, h, roof, flag=None):
    """Башня: светлая грань слева, тень справа, зубцы или красная крыша конусом, бойница."""
    wall, wall_d, wall_l = rgb("B4B2B4"), rgb("86848E"), rgb("D8D8D8")
    for i in range(w):
        c = wall_l if i == 0 else (wall_d if i >= w - max(1, w // 3) else wall)
        a.rect((x + i) % 128, y - h, 1, h, c)
    if roof:
        rh = w // 2 + 2
        for j in range(rh):
            half = (w / 2.0 + 0.5) * (j + 1) / rh
            for i in range(-int(half) - (1 if j == rh - 1 else 0), int(half) + 1 + (1 if j == rh - 1 else 0)):
                cx = x + w // 2 + i
                a.px(cx % 128, y - h - rh + j, RED if i <= 0 else RED_D)
        top = y - h - rh
    else:
        for i in range(-1, w + 1):
            a.px((x + i) % 128, y - h, wall_d if i >= w - 1 else wall)
            if (i + 1) % 2 == 0:
                a.px((x + i) % 128, y - h - 1, wall_l if i < w - 1 else wall)
        top = y - h - 1
    a.px((x + w // 2) % 128, y - h + 3, rgb("3C4050"))
    a.px((x + w // 2) % 128, y - h + 4, rgb("3C4050"))
    if flag:
        mx = x + w // 2
        a.rect(mx % 128, top - 4, 1, 4, rgb("3C4050"))
        a.px((mx + 1) % 128, top - 4, flag), a.px((mx + 2) % 128, top - 4, flag)
        a.px((mx + 1) % 128, top - 3, flag), a.px((mx + 2) % 128, top - 3, mul(flag, 0.8))
        a.px((mx + 3) % 128, top - 4, mul(flag, 0.8))


def tex_sky():
    """Панорама неба: синий день, солнце, кучевые облака, дальняя гряда синих гор, зелёные холмы
    с ельником, замок с башнями и знамёнами и сторожевая башня на другом холме, у горизонта
    полоса лугов и пашен. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 249)
    top, low = rgb("3A66B8"), rgb("D3ECF6")
    for y in range(64):
        t = min(y / 50.0, 1.0)
        a.rect(0, y, 128, 1, mix(top, low, t * t * 0.9 + t * 0.1))
    # Солнце с ореолом.
    sx, sy = 104, 13
    for y in range(-7, 8):
        for x in range(-7, 8):
            d = math.hypot(x, y)
            if d <= 3.3:
                a.px(sx + x, sy + y, rgb("FFF6C8") if d < 2.4 else rgb("FBE488"))
            elif d <= 7.0 and (x + y) % 2 == 0:
                a.px(sx + x, sy + y, mix(a.get(sx + x, sy + y)[:3], rgb("FFF2B0"), 0.5 * (1.0 - d / 7.0) + 0.1))
    for cx, cy, w in ((6, 14, 22), (40, 9, 14), (58, 24, 26), (92, 30, 16), (116, 22, 18), (22, 33, 12), (74, 38, 10)):
        _cloud(a, cx, cy, w)
    # Дальние горы: синяя гряда со светлой кромкой и снегом на вершинах.
    for x in range(128):
        h = 7 + 4 * math.sin(x * math.pi / 32.0 + 0.6) + 3 * math.sin(x * math.pi / 16.0 + 2.0) + 2 * abs(math.sin(x * math.pi / 8.0))
        h = max(2, int(h))
        a.rect(x, 54 - h, 1, h, rgb("7E9CD0"))
        a.px(x, 54 - h, rgb("A8C4E8"))
        if h >= 13:
            a.px(x, 54 - h, WHITE), a.px(x, 55 - h, rgb("C8DCF0"))
    # Ближние холмы: два горба на плитку, на них ельник.
    hill = []
    for x in range(128):
        h = 5 + 5 * math.sin((x - 22) * math.pi / 64.0) ** 2 + 1.5 * math.sin(x * math.pi / 16.0)
        hill.append(max(2, int(round(h))))
        a.rect(x, 57 - hill[x], 1, hill[x], rgb("4E9A48"))
        a.px(x, 57 - hill[x], rgb("86C458"))
        if hill[x] > 4 and x % 3 == 0:
            a.px(x, 59 - hill[x] + (x // 3) % 3, rgb("3E8240"))
    for x in (4, 9, 13, 30, 70, 76, 81, 86, 96, 122, 126):
        _fir(a, x, 57 - hill[x % 128] + 1, 5 + (x % 3), rgb("2A6A3E"))
        a.px(x % 128, 57 - hill[x % 128] - 2, rgb("3E8A4A"))
    # Замок на левом холме: стена с зубцами и воротами, донжон и две башни под красными крышами.
    bx = 42
    by = 57 - min(hill[bx:bx + 26]) + 1
    _tower(a, bx + 10, by, 7, 17, True, RED)
    a.rect(bx + 2, by - 7, 22, 7, rgb("B4B2B4"))
    a.rect(bx + 2, by - 7, 22, 1, rgb("D8D8D8"))
    a.rect(bx + 14, by - 6, 10, 6, rgb("9C9AA2"))
    for i in range(2, 24, 2):
        a.px(bx + i, by - 8, rgb("D8D8D8") if i < 14 else rgb("B4B2B4"))
    _tower(a, bx, by, 5, 12, True, GOLD)
    _tower(a, bx + 22, by, 5, 11, True)
    # Ворота и бойницы.
    a.rect(bx + 12, by - 4, 3, 4, rgb("5E3A1C"))
    a.px(bx + 13, by - 5, rgb("5E3A1C"))
    for i in (6, 9, 18, 20):
        a.px(bx + i, by - 4, rgb("3C4050"))
    # Сторожевая башня с зубцами на правом холме.
    wx = 108
    _tower(a, wx, 57 - hill[wx] + 1, 4, 9, False, RED)
    # Полоса лугов и пашен у горизонта.
    a.rect(0, 56, 128, 8, rgb("6CAC4C"))
    a.rect(0, 56, 128, 1, rgb("A4D468"))
    for x0, w, c in ((8, 18, rgb("C6CC68")), (52, 12, rgb("8CC058")), (84, 22, rgb("D8C870")), (116, 14, rgb("5E9C46"))):
        for j in range(3):
            a.rect((x0 + j * 2) % 128, 58 + j * 2, min(w, 128 - (x0 + j * 2) % 128), 2, c)
            if (x0 + j * 2) % 128 + w > 128:
                a.rect(0, 58 + j * 2, (x0 + j * 2) % 128 + w - 128, 2, c)
    for _ in range(26):
        x, y = a.rng.randrange(128), 57 + a.rng.randrange(7)
        a.px(x, y, rgb("3E8240"))
    # Дорога от ворот к краю кадра.
    for j in range(7):
        a.px(bx + 13 + j // 2, 57 + j, rgb("DCC090"))
        a.px(bx + 14 + j // 2, 57 + j, rgb("C2A272"))
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
