#!/usr/bin/env python3
"""Текстуры уровня «Зомби» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок:
ночное кладбище у пригорода. Стиль первой PlayStation: низкое разрешение, в которое втиснуто как
можно больше деталей. Все плитки стыкуются по краям: каждый пиксель ставится по модулю размера.
Цвета из палитры основы 16/32 (`zombies16.PALETTE`) и тона к ним.

Что на что рассчитано в демках, сохранено: `sand` главная земля (сырая кладбищенская земля),
`planks` настил панелями 32×16 вразбежку (плиты кладбища), `water` основание мира с той же зыбью,
что у моря пиратов (болотная жижа, не морская вода), `rock` кладка блоками 16×8 со сдвигом
(кирпич склепа), `sail` ткань 32×32 со швами на x = 0 и 16 (брезент убежища), `grass` жухлая
трава, `road` асфальт с колеями на тех же столбцах и пунктиром по оси, `mud` заметно темнее
дороги, `wind` стрелки вперёд на прозрачном, `sky` панорама 128×64 с плиткой по горизонтали и
полосой основания мира с 56-й строки.

    python3 tools/zombies_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import zombies16 as z16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def _pal(i):
    return tuple(z16.PALETTE[i])


EARTH, EARTH_D, EARTH_L = rgb("6E5642"), _pal(z16.DARK), _pal(z16.METAL)  # кладбищенская земля
SLAB, SLAB_D, SLAB_L = rgb("7E837E"), rgb("464A4C"), _pal(z16.GREY)  # плиты кладбища
BRICK, BRICK_D, BRICK_L = rgb("6E4036"), rgb("2E2228"), rgb("925A48")  # кирпич склепа
TARP, TARP_D, TARP_L = rgb("7C7C54"), rgb("4E5038"), rgb("A6A474")  # брезент убежища
DRY, DRY_D, DRY_L = rgb("7C7038"), rgb("4E4A2A"), _pal(z16.GOLD)  # жухлая трава
ASPH, ASPH_D, ASPH_L = rgb("50525C"), rgb("2C2E38"), rgb("70727C")  # асфальт
SLIME, SLIME_D, SLIME_L = _pal(z16.PLUM), rgb("1C3428"), _pal(z16.VIOLET)  # болотная жижа
ROT_L = rgb("A6CC86")
BONE, BONE_D = _pal(z16.WHITE), rgb("B4B09E")
BLOOD, BLOOD_D = rgb("8E2420"), rgb("5A1A1C")
LEAF, LEAF_D = _pal(z16.BRASS), rgb("7A4A2A")
YELLOW = _pal(z16.GOLD)
NIGHT = rgb("0E1226")  # силуэты на фоне неба


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def wget(a, x, y):
    return a.get(int(x) % a.w, int(y) % a.h)[:3]


def crack(a, x, y, n, c, dx=1, lit=None):
    """Трещина: ломаная из `n` пикселей, идёт вбок и понемногу вниз; `lit` светлая кромка под ней."""
    for k in range(n):
        wpx(a, x, y, c)
        if lit is not None:
            wpx(a, x, y + 1, lit)
        x += dx
        r = a.rng.random()
        if r < 0.3:
            y += 1
        elif r < 0.42:
            y -= 1


def bone(a, x, y, horiz=True):
    """Косточка: стержень в четыре пикселя и раздвоенные головки на концах, тень снизу."""
    for k in range(4):
        px, py = (x + k, y) if horiz else (x, y + k)
        wpx(a, px + (0 if horiz else 1), py + (1 if horiz else 0), EARTH_D)
        wpx(a, px, py, BONE)
    for k in (-1, 4):
        for s in (-1, 1):
            px, py = (x + k, y + s) if horiz else (x + s, y + k)
            wpx(a, px, py, BONE if s < 0 else BONE_D)


def leaf(a, x, y, c, flip=False):
    """Палый лист: три пикселя наискось и прожилка темнее."""
    s = -1 if flip else 1
    wpx(a, x, y, c), wpx(a, x + s, y + 1, c), wpx(a, x + s, y, mul(c, 0.72)), wpx(a, x + 2 * s, y + 1, mul(c, 0.6))


def tex_sand():
    """Сырая кладбищенская земля: бурые разводы, комья с бликом и тенью, камешки, палые листья,
    пара косточек, пучки сухого бурьяна и след ботинка."""
    a = lm.Atlas(64, 64, 331)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.07 * math.sin(x * math.pi / 16.0 + 2.0 * math.sin(y * math.pi / 16.0)) \
                + 0.05 * math.sin((y * 3 - x) * math.pi / 32.0)
            a.px(x, y, mul(EARTH, k))
    for _ in range(230):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), mul(EARTH, 0.78) if a.rng.random() < 0.6 else mul(EARTH, 1.2))
    # Комья: светлый верх слева, тень справа снизу.
    for _ in range(16):
        x, y, s = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(2, 4)
        wrect(a, x, y, s, s - 1, mul(EARTH, 1.16))
        wrect(a, x, y, s, 1, EARTH_L)
        wrect(a, x + 1, y + s - 1, s, 1, EARTH_D)
        wpx(a, x + s, y + s - 2, EARTH_D)
    # Камешки.
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, SLAB_L), wpx(a, x + 1, y, SLAB), wpx(a, x, y + 1, SLAB_D), wpx(a, x + 1, y + 1, EARTH_D)
    # След ботинка: подошва из поперечных штрихов и каблук.
    for j in range(0, 8, 2):
        wrect(a, 40 + (1 if j in (0, 6) else 0), 12 + j, 4 - (1 if j in (0, 6) else 0), 1, EARTH_D)
    wrect(a, 41, 22, 3, 2, EARTH_D)
    bone(a, 10, 20, True), bone(a, 50, 44, False)
    for i, (x, y) in enumerate(((5, 6), (28, 34), (58, 26), (20, 52), (36, 58), (48, 4), (14, 40))):
        leaf(a, x, y, LEAF if i % 2 else LEAF_D, i % 3 == 0)
    # Пучки сухого бурьяна: три стебелька веером.
    for x, y in ((26, 10), (6, 54), (54, 60)):
        for dx, h in ((-1, 3), (0, 4), (1, 3)):
            for k in range(h):
                wpx(a, x + dx * (1 + k // 2), y - k, DRY_L if k == h - 1 else DRY)
        wpx(a, x, y + 1, EARTH_D)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_planks():
    """Плиты кладбища: камень 32×16 вразбежку, тёмные швы со светлой фаской, мох в швах, сколы
    по углам, трещины; на одной плите выбит крест со строками эпитафии, на другой лишайник."""
    a = lm.Atlas(64, 64, 333)
    a.rect(0, 0, 64, 64, SLAB)
    for row in range(4):
        y0 = row * 16
        off = (row % 2) * 16
        tone = (1.0, 0.9, 1.06, 0.95)[row]
        for col in range(2):
            x0 = off + col * 32
            t = tone * (1.0 if col == 0 else 0.93)
            for j in range(16):
                for i in range(32):
                    k = 1.0 + 0.05 * math.sin((i + x0) * math.pi / 8.0 + (j + y0) * math.pi / 4.0)
                    wpx(a, x0 + i, y0 + j, mul(SLAB, t * k))
            # Выщербины: тёмная точка со светлой под ней.
            for _ in range(7):
                i, j = a.rng.randrange(3, 29), a.rng.randrange(3, 13)
                wpx(a, x0 + i, y0 + j, mul(SLAB_D, 1.2)), wpx(a, x0 + i, y0 + j + 1, mul(SLAB_L, t))
            wrect(a, x0, y0, 32, 1, SLAB_D)
            wrect(a, x0, y0 + 1, 32, 1, mul(SLAB_L, t))
            wrect(a, x0, y0, 1, 16, SLAB_D)
            wrect(a, x0 + 1, y0 + 2, 1, 14, mul(SLAB_L, 0.92 * t))
            wrect(a, x0 + 2, y0 + 15, 30, 1, mul(SLAB, 0.8 * t))
            # Скол угла.
            if (row + col) % 2 == 0:
                wpx(a, x0 + 1, y0 + 1, SLAB_D), wpx(a, x0 + 2, y0 + 1, SLAB_D), wpx(a, x0 + 1, y0 + 2, SLAB_D)
    # Трещины через две плиты.
    crack(a, 5, 21, 13, SLAB_D, 1, mul(SLAB_L, 0.9))
    crack(a, 44, 52, 10, SLAB_D, 1, mul(SLAB_L, 0.95))
    crack(a, 52, 4, 7, SLAB_D, -1, SLAB_L)
    # Выбитый крест и строки эпитафии на верхней левой плите.
    wrect(a, 8, 4, 1, 9, SLAB_D), wrect(a, 6, 6, 5, 1, SLAB_D)
    wrect(a, 9, 5, 1, 8, SLAB_L), wrect(a, 6, 7, 2, 1, SLAB_L)
    for j, w in ((5, 13), (8, 10), (11, 12)):
        for i in range(0, w, 3):
            wrect(a, 14 + i, j, 2, 1, SLAB_D)
            wpx(a, 14 + i, j + 1, SLAB_L)
    # Лишайник пятном и мох в швах.
    for _ in range(26):
        x, y = 36 + a.rng.randrange(-5, 6), 40 + a.rng.randrange(-3, 4)
        wpx(a, x, y, SLIME_L if a.rng.random() < 0.5 else SLIME)
    for _ in range(18):
        x, y = a.rng.randrange(64), a.rng.randrange(4) * 16
        wrect(a, x, y, a.rng.randrange(2, 6), 1, SLIME)
        wpx(a, x + 1, y + 1, SLIME_L if a.rng.random() < 0.5 else SLIME_D)
    for _ in range(6):
        row = a.rng.randrange(4)
        x, y = (row % 2) * 16 + a.rng.randrange(2) * 32, row * 16 + a.rng.randrange(3, 13)
        wrect(a, x, y, 1, a.rng.randrange(2, 4), SLIME)
    leaf(a, 50, 26, LEAF), leaf(a, 22, 56, LEAF_D, True)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Основание мира, жидкость: болотная жижа. Та же зыбь, что у моря пиратов, тёмная зелёная
    глубина и светлые тягучие гребни; островки ряски, пузыри с бликом, плёнка тумана."""
    a = lm.Atlas(64, 64, 335)
    deep, mid, crest = SLIME_D, mul(SLIME, 0.9), mix(SLIME, SLIME_L, 0.75)
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = mid if w > 0.3 else deep
            if w > 1.35:
                c = mix(mid, crest, 0.45)
            if w > 1.78:
                c = crest
            if w < -1.5:
                c = mul(deep, 0.78)
            a.px(x, y, c)
    # Ряска: кучки светлых точек.
    for _ in range(7):
        cx, cy = a.rng.randrange(64), a.rng.randrange(64)
        for _ in range(8):
            wpx(a, cx + a.rng.randrange(-3, 4), cy + a.rng.randrange(-2, 3), ROT_L if a.rng.random() < 0.4 else rgb("5E8A4E"))
    # Пузыри: тёмное кольцо, светлая середина, блик сверху слева.
    for cx, cy, r in ((12, 10, 2), (44, 30, 2), (28, 50, 1), (56, 58, 1), (4, 38, 1)):
        for y in range(-r - 1, r + 2):
            for x in range(-r - 1, r + 2):
                d = math.hypot(x, y)
                if d <= r - 0.3:
                    wpx(a, cx + x, cy + y, mix(SLIME, SLIME_L, 0.55))
                elif d <= r + 0.7:
                    wpx(a, cx + x, cy + y, mul(SLIME_D, 0.7) if x + y > 0 else SLIME_L)
        wpx(a, cx - (1 if r > 1 else 0), cy - (1 if r > 1 else 0), rgb("E4F4C8"))
    for _ in range(26):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), rgb("D0E8B0") if a.rng.random() < 0.3 else rgb("2A4A34"))
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_rock():
    """Кирпичная кладка склепа: кирпичи 16×8 со сдвигом, у каждого свой тон, светлая кромка
    сверху, часть закопчена, часть заменена серым камнем; сколы, трещины, мох в швах, потёк."""
    a = lm.Atlas(64, 64, 337)
    a.rect(0, 0, 64, 64, BRICK)
    for row in range(8):
        y = row * 8
        off = (row % 2) * 8
        for col in range(4):
            x = off + col * 16
            tone = a.rng.uniform(0.82, 1.16)
            r = a.rng.random()
            base = BRICK if r < 0.74 else (mix(BRICK, BRICK_D, 0.5) if r < 0.88 else SLAB)
            lit = BRICK_L if base != SLAB else SLAB_L
            wrect(a, x, y, 16, 8, mul(base, tone))
            # Пористый обжиг: точки темнее и светлее.
            for _ in range(7):
                i, j = a.rng.randrange(2, 15), a.rng.randrange(2, 7)
                wpx(a, x + i, y + j, mul(base, tone * (0.8 if a.rng.random() < 0.6 else 1.18)))
            wrect(a, x + 1, y + 1, 14, 1, mul(lit, tone))
            wrect(a, x + 1, y + 7, 15, 1, mul(base, tone * 0.7))
            wrect(a, x, y, 1, 8, BRICK_D)
            wrect(a, x, y, 16, 1, BRICK_D)
            if a.rng.random() < 0.4:
                cx, cy = x + a.rng.randrange(3, 11), y + a.rng.randrange(2, 5)
                for k in range(a.rng.randrange(2, 5)):
                    wpx(a, cx + k, cy + (k // 2), BRICK_D)
            if a.rng.random() < 0.3:  # скол угла до раствора
                wpx(a, x + 15, y + 1, BRICK_D), wpx(a, x + 15, y + 2, BRICK_D), wpx(a, x + 14, y + 1, BRICK_D)
    # Мох в швах свисает на пиксель-два.
    for _ in range(16):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        w = a.rng.randrange(2, 6)
        wrect(a, x, y, w, 1, SLIME)
        wpx(a, x + 1, y + 1, SLIME_L), wpx(a, x + w - 1, y + 1, SLIME_D)
    # Зелёный потёк по стене.
    for k in range(13):
        wpx(a, 38 + (1 if k in (4, 5, 9) else 0), 17 + k, mix(wget(a, 38, 17 + k), SLIME_L, 0.55))
    wpx(a, 38, 30, SLIME_L)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_sail():
    """Брезент убежища: плетение в клетку, прошитые швы полотнищ, заплата на стежках, люверсы
    у шва, потёки грязи и бурое пятно."""
    a = lm.Atlas(32, 32, 339)
    for y in range(32):
        for x in range(32):
            k = 1.0 + 0.05 * math.sin(y * math.pi / 8.0 + x * math.pi / 16.0)
            k *= 1.06 if (x + y) % 2 == 0 else 0.95  # плетение
            a.px(x, y, mul(TARP, k))
    # Складки: мягкие косые полосы.
    for y in range(32):
        for x in range(32):
            if (x * 2 + y) % 32 in (9, 10):
                wpx(a, x, y, mul(wget(a, x, y), 1.12))
            elif (x * 2 + y) % 32 in (11, 12):
                wpx(a, x, y, mul(wget(a, x, y), 0.86))
    # Швы полотнищ со стежками.
    for x in (0, 16):
        a.rect(x, 0, 1, 32, TARP_D)
        for y in range(1, 32, 4):
            a.px(x + 1, y, TARP_L), a.px(x + 1, y + 1, TARP_L)
    # Заплата светлее на крупных стежках.
    wrect(a, 20, 6, 8, 7, mul(TARP_L, 0.96))
    wrect(a, 20, 12, 8, 1, mul(TARP, 0.9))
    for i in range(0, 8, 2):
        wpx(a, 20 + i, 5, BONE_D), wpx(a, 20 + i, 13, BONE_D)
    for j in range(0, 7, 2):
        wpx(a, 19, 6 + j, BONE_D), wpx(a, 28, 6 + j, BONE_D)
    # Люверсы: кольцо с дыркой.
    for ex, ey in ((4, 4), (4, 20)):
        wrect(a, ex - 1, ey - 1, 3, 3, rgb("B8BCB4"))
        wpx(a, ex, ey, NIGHT), wpx(a, ex + 1, ey + 1, rgb("6E7270")), wpx(a, ex, ey + 1, rgb("6E7270"))
    # Бурое пятно и потёки грязи.
    for _ in range(16):
        wpx(a, 9 + a.rng.randrange(-3, 4), 25 + a.rng.randrange(-2, 3), BLOOD if a.rng.random() < 0.6 else BLOOD_D)
    for x, y, n in ((24, 20, 6), (12, 9, 4), (29, 26, 4)):
        for k in range(n):
            wpx(a, x, y + k, mul(TARP_D, 1.05))
    for _ in range(18):
        wpx(a, a.rng.randrange(32), a.rng.randrange(32), TARP_D if a.rng.random() < 0.6 else TARP_L)
    a.noise(0, 0, 32, 32, 0.05)
    return a


def tex_grass():
    """Жухлая трава: бурые пятна тоном, сухие травинки в два пикселя, соломенные метёлки,
    проплешины земли, палые листья и бледные поганки."""
    a = lm.Atlas(64, 64, 341)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.09 * math.sin(x * math.pi / 16.0 + 1.5 * math.sin(y * math.pi / 16.0)) \
                + 0.04 * math.sin((x + y * 2) * math.pi / 8.0)
            a.px(x, y, mul(DRY, k))
    for _ in range(300):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        r = a.rng.random()
        c = DRY_D if r < 0.5 else (mul(DRY, 1.25) if r < 0.85 else rgb("5E7A3E"))
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
    # Проплешины земли с тёмной кромкой снизу.
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 4, 2, EARTH), wrect(a, x + 1, y - 1, 2, 1, EARTH)
        wrect(a, x, y + 2, 4, 1, DRY_D), wpx(a, x + 1, y, EARTH_L)
    # Соломенные метёлки: стебель в три пикселя и светлая макушка.
    for _ in range(22):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        s = 1 if a.rng.random() < 0.5 else -1
        wpx(a, x, y, DRY_D), wpx(a, x, y - 1, mul(DRY_L, 0.8)), wpx(a, x + s, y - 2, DRY_L)
    for i in range(6):
        leaf(a, a.rng.randrange(64), a.rng.randrange(64), LEAF_D if i % 2 else BLOOD, i % 3 == 0)
    # Поганки: бледная шляпка, ножка, тень.
    for _ in range(5):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 3, 1, BONE), wpx(a, x + 2, y, BONE_D), wpx(a, x + 1, y + 1, BONE_D), wpx(a, x + 1, y + 2, DRY_D)
        wpx(a, x + 2, y + 1, DRY_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_road():
    """Разбитый асфальт: укатанные следы шин на тех же столбцах, что колеи у пиратов, жёлтый
    стёртый пунктир по оси, залитые гудроном швы и трещины, заплата, щебень, бурый след волока."""
    a = lm.Atlas(64, 64, 343)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.04 * math.sin(y * math.pi / 8.0 + x * math.pi / 32.0) + 0.03 * math.sin(x * math.pi / 4.0 + y * math.pi / 16.0)
            a.px(x, y, mul(ASPH, k))
    # Щебень в битуме.
    for _ in range(260):
        r = a.rng.random()
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), ASPH_D if r < 0.5 else (ASPH_L if r < 0.9 else rgb("9A9CA2")))
    # Заплата свежего асфальта с гудроновой кромкой.
    wrect(a, 4, 40, 11, 9, ASPH_D), wrect(a, 5, 41, 9, 7, mul(ASPH, 0.82))
    for _ in range(10):
        wpx(a, 5 + a.rng.randrange(9), 41 + a.rng.randrange(7), mul(ASPH, 0.98))
    # Следы шин.
    for x in (18, 19, 44, 45):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 0.8))
    for x in (20, 46):
        for y in range(64):
            a.px(x, y, mul(a.get(x, y)[:3], 1.12))
    # Швы плит дороги залиты гудроном, под ними светлая кромка.
    for y in (0, 32):
        for x in range(64):
            dy = (0, 0, 1, 0, 0, -1, 0, 0)[(x + y) // 3 % 8]
            wpx(a, x, y + dy, ASPH_D)
            wpx(a, x, y + dy + 1, mix(wget(a, x, y + dy + 1), ASPH_L, 0.6))
    a.rect(0, 0, 1, 64, ASPH_D)
    # Трещины от шва в стороны.
    crack(a, 24, 33, 9, ASPH_D, 1)
    crack(a, 50, 1, 8, ASPH_D, 1)
    crack(a, 12, 14, 7, ASPH_D, -1)
    crack(a, 56, 44, 6, ASPH_D, -1)
    # Пунктир разметки по оси: жёлтый, стёртый.
    for y0 in (6, 38):
        for y in range(y0, y0 + 12):
            for x in (31, 32):
                if a.rng.random() < 0.82:
                    a.px(x, y, YELLOW if a.rng.random() < 0.7 else LEAF)
    # Бурый след волока поперёк полосы и пятно масла.
    for k in range(14):
        wpx(a, 36 + k, 22 + k // 4, mix(wget(a, 36 + k, 22 + k // 4), BLOOD, 0.7))
        if k % 3:
            wpx(a, 36 + k, 23 + k // 4, mix(wget(a, 36 + k, 23 + k // 4), BLOOD_D, 0.6))
    for y in range(-2, 3):
        for x in range(-3, 4):
            if x * x / 9.0 + y * y / 4.0 <= 1.0:
                wpx(a, 10 + x, 56 + y, mul(wget(a, 10 + x, 56 + y), 0.72))
    wpx(a, 9, 55, rgb("6A5E8C")), wpx(a, 11, 56, rgb("4E7A6A"))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_mud():
    """Раскисшая чёрная грязь: тягучие складки, лужи с зелёной жижей и бликом луны, комья,
    торчащие корешки. Заметно темнее асфальта."""
    a = lm.Atlas(64, 64, 345)
    mud, mud_d, mud_l = rgb("2E2622"), rgb("1A1516"), rgb("4E4034")
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 4.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            a.px(x, y, mul(mud, 1.0 + 0.18 * w))
    # Лужи: тёмный берег, зелёная жижа, светлая кромка сверху.
    for _ in range(10):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 6)
        for y in range(-r, r + 1):
            for x in range(-r * 2, r * 2 + 1):
                d = (x / 2.0) ** 2 + y ** 2
                if d <= (r - 1) * (r - 1):
                    wpx(a, cx + x, cy + y, mix(mud_d, SLIME, 0.55 if y == 0 and abs(x) < r else 0.32))
                elif d <= r * r:
                    wpx(a, cx + x, cy + y, mud_d)
        wpx(a, cx - 2, cy - r + 2, SLIME), wpx(a, cx - 1, cy - r + 2, SLIME_L)
    for _ in range(190):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), mud_l if a.rng.random() < 0.45 else mud_d)
    # Комья с бликом.
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 2, 2, mud_l), wpx(a, x, y, rgb("6E5642")), wpx(a, x + 1, y + 2, mud_d), wpx(a, x + 2, y + 1, mud_d)
    # Корешки.
    for _ in range(6):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, rgb("86624A")), wpx(a, x + 1, y + 1, rgb("86624A")), wpx(a, x + 2, y + 1, rgb("5E4636"))
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Разгонная полоса: стрелки вперёд цвета зелёного тумана на прозрачном, текстура бежит по
    полосе."""
    a = lm.Atlas(32, 32, 347)
    white, pale = rgb("F0FFE0"), ROT_L
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, white)
                a.px(x, row + 4 + k, pale)
                a.px(x, row + 5 + k, mul(pale, 0.7))
    return a


def _hill(x):
    """Высота холма с часовней: один горб на плитку с вершиной на x = 96, по краям низина."""
    s = math.sin((x - 32) * math.pi / 128.0) ** 2
    return int(round(3 + 15 * s * s + 0.8 * math.sin(x * math.pi / 8.0)))


def _house(a, x, base, w, h, roof, lit=()):
    """Силуэт дома: стена, двускатная крыша, труба; `lit` окна со светом (смещения от угла)."""
    wrect(a, x, base - h, w, h, NIGHT)
    for k in range(roof):
        wrect(a, x - 1 + k, base - h - 1 - k, max(w + 2 - 2 * k, 1), 1, NIGHT)
    wrect(a, x + w - 3, base - h - roof, 1, roof - 1, NIGHT)
    # Лунный свет по левому скату.
    for k in range(roof):
        wpx(a, x - 1 + k, base - h - 1 - k, rgb("2A3660"))
    for dx, dy in lit:
        wpx(a, x + dx, base - dy, YELLOW), wpx(a, x + dx, base - dy + 1, LEAF)


def _dead_tree(a, x, base, h):
    """Мёртвое дерево: ствол и голые сучья в стороны."""
    wrect(a, x, base - h, 1, h, NIGHT)
    for k, (dy, s, n) in enumerate(((h - 2, -1, 3), (h - 4, 1, 3), (h - 1, 1, 2), (h - 6, -1, 2))):
        if dy < 2:
            continue
        for i in range(1, n + 1):
            wpx(a, x + s * i, base - dy - i + (1 if k % 2 else 0), NIGHT)
    wpx(a, x - 1, base - h - 1, NIGHT)


def tex_sky():
    """Панорама ночи: чёрно-синее небо, редкие звёзды, большая луна с ореолом и полосой туч,
    вороны; у горизонта силуэт пригорода с огнями в окнах, столбы с проводами, водонапорная башня,
    холм с часовней, крестами и мёртвыми деревьями; понизу зелёный туман и полоса болотной жижи.
    Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 349)
    top, mid, low = rgb("070818"), rgb("1C2850"), rgb("5E9080")
    for y in range(64):
        t = min(y / 55.0, 1.0)
        c = mix(top, mid, min(t / 0.6, 1.0)) if t < 0.6 else mix(mid, low, (t - 0.6) / 0.4)
        a.rect(0, y, 128, 1, c)
    # Звёзды: редкие, тусклее к горизонту.
    for _ in range(90):
        x, y = a.rng.randrange(128), a.rng.randrange(40)
        k = a.rng.uniform(0.35, 0.95) * (1.0 - y / 60.0)
        wpx(a, x, y, mix(a.get(x, y)[:3], rgb("DCE4F4"), k))
    # Луна: ореол дизерингом, диск с кратерами, тень по правому нижнему краю.
    mx, my, mr = 34, 17, 9
    for y in range(-17, 18):
        for x in range(-17, 18):
            d = math.hypot(x, y)
            if mr < d <= 17 and (x + y) % 2 == 0:
                wpx(a, mx + x, my + y, mix(wget(a, mx + x, my + y), rgb("93B2CE"), 0.42 * (1.0 - (d - mr) / 8.0) ** 1.5 if d < 17 else 0))
    for y in range(-mr, mr + 1):
        for x in range(-mr, mr + 1):
            d = math.hypot(x, y)
            if d <= mr + 0.3:
                c = _pal(z16.WHITE)
                if math.hypot(x - 3, y - 3) > mr - 1.5:
                    c = rgb("FFFDF0")
                if math.hypot(x + 3, y + 3) > mr - 0.5:
                    c = rgb("C4C8B8")
                wpx(a, mx + x, my + y, c)
    for cx, cy, r in ((-3, -3, 2), (3, 1, 2), (-2, 4, 1), (4, -4, 1), (0, -1, 1), (-5, 1, 1)):
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if x * x + y * y <= r * r:
                    wpx(a, mx + cx + x, my + cy + y, rgb("C6CABC") if x + y <= 0 else rgb("DAD9CB"))
    # Тучи: длинные рваные полосы, одна перечёркивает луну.
    for cx, cy, w, col in ((18, 21, 40, rgb("1C2A52")), (70, 9, 30, rgb("141C3C")), (96, 27, 34, rgb("1C2A52")), (2, 34, 22, rgb("22345A"))):
        for k in range(w):
            h = 1 + int(1.6 * math.sin(math.pi * k / w) + a.rng.random())
            wrect(a, cx + k, cy - h // 2, 1, h, col)
            if h > 1:
                wpx(a, cx + k, cy - h // 2, mix(col, _pal(z16.AQUA), 0.45))
    # Вороны: галочки.
    for x, y in ((52, 12), (58, 16), (112, 14), (12, 8)):
        for dx, dy in ((-2, -1), (-1, 0), (0, 1), (1, 0), (2, -1)):
            wpx(a, x + dx, y + dy, NIGHT)
    # Холм с низиной: тёмный силуэт со светлой кромкой от луны.
    hill = [_hill(x) for x in range(128)]
    for x in range(128):
        a.rect(x, 57 - hill[x], 1, hill[x], rgb("121830"))
        a.px(x, 57 - hill[x], rgb("2C3C62"))
    # Пригород в низине: дома, водонапорная башня, столбы с проводами.
    for x, w, h, roof, lit in ((1, 8, 6, 4, ((2, 4),)), (13, 7, 5, 3, ()), (22, 9, 8, 4, ((2, 6), (6, 6), (6, 3))),
                               (41, 8, 6, 4, ((5, 3),)), (50, 7, 5, 3, ((2, 3),)), (119, 7, 6, 3, ((2, 4),))):
        _house(a, x, 57 - min(hill[x % 128], hill[(x + w) % 128]) + 1, w, h, roof, lit)
    tx = 33
    wrect(a, tx, 57 - hill[tx] - 9, 5, 4, NIGHT), wrect(a, tx + 1, 57 - hill[tx] - 10, 3, 1, NIGHT)
    wpx(a, tx, 57 - hill[tx] - 9, rgb("2A3660")), wpx(a, tx, 57 - hill[tx] - 8, rgb("2A3660"))
    for dx in (0, 4):
        wrect(a, tx + dx, 57 - hill[tx] - 5, 1, 6, NIGHT)
    wpx(a, tx + 1, 57 - hill[tx] - 3, NIGHT), wpx(a, tx + 3, 57 - hill[tx] - 3, NIGHT), wpx(a, tx + 2, 57 - hill[tx] - 2, NIGHT)
    poles = (10, 37, 60, 116)
    for x in poles:
        wrect(a, x, 57 - hill[x] - 10, 1, 10, NIGHT), wrect(a, x - 1, 57 - hill[x] - 9, 3, 1, NIGHT)
    for i, x0 in enumerate(poles):
        x1 = poles[(i + 1) % len(poles)] + (128 if i == len(poles) - 1 else 0)
        y0, y1 = 57 - hill[x0] - 9, 57 - hill[x1 % 128] - 9
        if x1 - x0 > 40:
            continue  # через холм провода не идут
        for x in range(x0 + 2, x1 - 1):
            t = (x - x0) / float(x1 - x0)
            wpx(a, x, y0 + (y1 - y0) * t + 2.6 * math.sin(math.pi * t), NIGHT)
    # Кладбище на склоне: кресты, надгробия, мёртвые деревья.
    for x in (70, 76, 83, 107, 112):
        b = 57 - hill[x]
        wrect(a, x, b - 3, 1, 4, NIGHT), wrect(a, x - 1, b - 2, 3, 1, NIGHT)
    for x in (73, 79, 104, 110):
        b = 57 - hill[x]
        wrect(a, x, b - 2, 2, 3, NIGHT), wpx(a, x, b - 2, rgb("2C3C62"))
    _dead_tree(a, 86, 57 - hill[86] + 1, 9)
    _dead_tree(a, 114, 57 - hill[114] + 1, 7)
    _dead_tree(a, 66, 57 - hill[66] + 1, 6)
    _dead_tree(a, 57, 57 - hill[57] + 1, 5)
    # Часовня на вершине: неф под двускатной крышей, колокольня со шпилем и крестом, колокол.
    cx = 93
    cb = 57 - min(hill[cx:cx + 10]) + 1
    wrect(a, cx + 3, cb - 6, 8, 6, NIGHT)
    for k in range(4):
        wrect(a, cx + 2 + k, cb - 7 - k, 10 - 2 * k, 1, NIGHT)
        wpx(a, cx + 2 + k, cb - 7 - k, rgb("2A3660"))
    wrect(a, cx, cb - 13, 4, 13, NIGHT)
    wrect(a, cx, cb - 13, 1, 13, rgb("222C50"))
    for k in range(4):
        wrect(a, cx + (k + 1) // 2, cb - 14 - k, 4 - 2 * ((k + 1) // 2), 1, NIGHT)
    wrect(a, cx + 1, cb - 19, 2, 2, NIGHT)
    wrect(a, cx + 1, cb - 23, 1, 4, NIGHT), wrect(a, cx, cb - 22, 3, 1, NIGHT)
    # Проём звонницы с колоколом, стрельчатое окно и дверь со светом.
    wrect(a, cx + 1, cb - 12, 2, 3, rgb("365E58")), wpx(a, cx + 1, cb - 11, YELLOW), wpx(a, cx + 2, cb - 11, LEAF)
    wrect(a, cx + 6, cb - 5, 1, 3, YELLOW), wpx(a, cx + 6, cb - 6, LEAF)
    wrect(a, cx + 9, cb - 4, 1, 2, LEAF)
    wrect(a, cx + 1, cb - 3, 2, 3, rgb("06070F"))
    # Зелёный туман: дизеринг гуще к низу и три стелющихся пряди.
    fog = rgb("6E9C6E")
    for y in range(49, 57):
        k = (y - 49) / 9.0
        for x in range(128):
            wave = 0.5 + 0.5 * math.sin(x * math.pi / 16.0 + y * 0.9)
            if (x + y) % 2 == 0 and a.rng.random() < k * (0.45 + 0.5 * wave):
                a.px(x, y, mix(a.get(x, y)[:3], fog, 0.25 + 0.3 * k))
    for x0, y, w in ((6, 53, 30), (58, 54, 26), (98, 52, 22), (40, 55, 44)):
        for k in range(w):
            if a.rng.random() < 0.85:
                wpx(a, x0 + k, y + (1 if math.sin(k * 0.5) > 0.6 else 0), mix(wget(a, x0 + k, y), rgb("93B2CE"), 0.32))
    # Полоса основания мира: болотная жижа с отблеском луны и ряской.
    a.rect(0, 56, 128, 8, SLIME_D)
    a.rect(0, 56, 128, 1, rgb("5E8A62"))
    for y in range(57, 64):
        for x in range(128):
            if math.sin((x + 3 * y) * math.pi / 8.0) + math.sin(x * math.pi / 16.0) > 1.1:
                a.px(x, y, SLIME)
    for j in range(0, 6, 2):
        w = 8 - j
        wrect(a, mx - w // 2 + (j // 2 % 2) * 2 - 1, 57 + j, w, 1, mix(SLIME, _pal(z16.WHITE), 0.45 - 0.05 * j))
    for _ in range(26):
        wpx(a, a.rng.randrange(128), 57 + a.rng.randrange(7), SLIME_L if a.rng.random() < 0.5 else rgb("12241C"))
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
