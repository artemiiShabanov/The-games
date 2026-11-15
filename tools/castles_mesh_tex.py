#!/usr/bin/env python3
"""Текстуры уровня «Замков» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` и у космоса в `space_mesh_tex.py` (`tex_sand` … `tex_sky`), свой рисунок.
Стиль первой PlayStation: низкое разрешение, в которое втиснуто как можно больше деталей. Все плитки
стыкуются по краям: каждый пиксель ставится по модулю размера. Основание мира у замков твердь,
поэтому `tex_water` это луг до горизонта (трава под ветром), а не вода. Слоты: sand это утоптанная
тропа с галькой и соломой, planks доски моста, rock кладка стены, sail красное знамя с золотом,
grass газон с ромашками и клевером, road булыжная мостовая с колеями (колеи на тех же столбцах,
что у пиратов), mud вспаханная тёмная земля, wind золотые стрелки вперёд на прозрачном, sky дневная
панорама с дальним замком. Набор подключает `lowpoly_meshes.py` через `castles_meshes`.

    python3 tools/castles_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

DIRT, DIRT_D, DIRT_L = rgb("B09A70"), rgb("8A7650"), rgb("D0BC90")  # тропа
OAK, OAK_D, OAK_L = rgb("8A5E3A"), rgb("55381F"), rgb("B08256")  # доски моста
IRON, IRON_D, IRON_L = rgb("4A4F5C"), rgb("23262E"), rgb("8C93A2")
STONE, STONE_D, STONE_L = rgb("9AA0AA"), rgb("626A7A"), rgb("CAD0DA")  # кладка, как латы 8-bit
MORTAR = rgb("C6C2B0")
MOSS = rgb("5E8A3C")
GRASS, GRASS_D, GRASS_L = rgb("58A040"), rgb("38722C"), rgb("8CD060")  # луг
LAWN, LAWN_D, LAWN_L = rgb("4A8C38"), rgb("2E6228"), rgb("78B84A")  # газон
RED, RED_D, RED_L = rgb("B02A2E"), rgb("6E1618"), rgb("DA4A4C")
GOLD, GOLD_D, GOLD_L = rgb("E0B040"), rgb("9A7020"), rgb("F6DC86")
COB, COB_D, COB_L = rgb("8A8E98"), rgb("4E525E"), rgb("B4B8C2")  # булыжник
SOIL, SOIL_D, SOIL_L = rgb("3E2C1E"), rgb("22160E"), rgb("5E4630")
STRAW = rgb("D8B850")


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def straw(a, x, y, ln=4):
    """Соломинка: косой штрих в два тона."""
    for k in range(ln):
        wpx(a, x + k, y - k // 2, STRAW if k % 2 == 0 else mul(STRAW, 0.8))


def tex_sand():
    """Тропа: утоптанная земля, россыпь гальки с бликом и тенью, соломинки, колея вмятин."""
    a = lm.Atlas(64, 64, 231)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.06 * math.sin((x + 7.0 * math.sin(y * math.pi / 16.0)) * math.pi / 16.0) \
                + 0.03 * math.sin((x * 2 + y * 3) * math.pi / 32.0)
            a.px(x, y, mul(DIRT, k))
    for _ in range(170):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), DIRT_D if a.rng.random() < 0.6 else DIRT_L)
    # Галька: овал 3×2 или 2×2, светлая макушка и тёмный низ.
    for _ in range(26):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        w = a.rng.choice((2, 3, 3))
        c = mul(rgb("A8A296"), a.rng.uniform(0.85, 1.15))
        wrect(a, x, y, w, 2, c)
        wpx(a, x, y, mul(c, 1.3))
        wpx(a, x + w - 1, y + 1, mul(c, 0.6))
        wpx(a, x + 1, y + 2, DIRT_D)
    for _ in range(11):
        straw(a, a.rng.randrange(64), a.rng.randrange(64), a.rng.choice((3, 4, 5)))
    # Вмятины следов: тёмная ямка с тенью сверху.
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 3, 1, DIRT_D)
        wrect(a, x, y + 1, 3, 1, mul(DIRT, 0.88))
        wpx(a, x + 2, y + 2, DIRT_L)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_planks():
    """Доски моста: ряды по 8 пикселей, торцевые стыки вразбежку, волокна, сучки, по паре
    железных гвоздей на каждом конце и две кованые полосы поперёк."""
    a = lm.Atlas(64, 64, 233)
    a.rect(0, 0, 64, 64, OAK)
    for row in range(8):
        y0 = row * 8
        cuts = [(row * 23 + 9) % 64, (row * 23 + 9 + 24 + (row % 3) * 4) % 64]
        # Две доски на ряд: от первого стыка до второго и от второго до первого (по кругу).
        bounds = sorted(cuts)
        spans = [(bounds[0], bounds[1] - bounds[0]), (bounds[1], 64 - bounds[1] + bounds[0])]
        for si, (x0, ln) in enumerate(spans):
            tone = a.rng.uniform(0.88, 1.12)
            c = mul(OAK, tone)
            wrect(a, x0, y0, ln, 8, c)
            for i in range(ln):
                for j in range(8):
                    g = math.sin((j * 1.7 + math.sin(i * 0.25 + row + si) * 1.3) * math.pi / 2.0)
                    if g > 0.82:
                        wpx(a, x0 + i, y0 + j, mul(c, 0.84))
            wrect(a, x0, y0, ln, 1, OAK_D)
            wrect(a, x0, y0 + 1, ln, 1, mul(OAK_L, tone * 0.92))
            wrect(a, x0, y0 + 7, ln, 1, mul(OAK_D, 1.2))
            wrect(a, x0, y0, 1, 8, OAK_D)
            wrect(a, x0 + 1, y0 + 2, 1, 5, mul(OAK_L, 0.85))
            # Сучок: тёмный овал с ободком.
            if a.rng.random() < 0.5:
                kx, ky = x0 + a.rng.randrange(6, max(7, ln - 6)), y0 + 3
                wrect(a, kx, ky, 2, 2, OAK_D)
                wpx(a, kx - 1, ky, mul(OAK, 0.85)), wpx(a, kx + 2, ky + 1, mul(OAK, 0.85))
            for nx in (x0 + 3, x0 + ln - 4):
                for ny in (y0 + 3,):
                    wpx(a, nx, ny, IRON_L)
                    wpx(a, nx, ny + 1, IRON_D)
    # Кованые полосы поперёк моста.
    for y in (14, 46):
        wrect(a, 0, y, 64, 3, IRON)
        wrect(a, 0, y, 64, 1, IRON_L)
        wrect(a, 0, y + 2, 64, 1, IRON_D)
        for x in range(4, 64, 12):
            wpx(a, x, y + 1, IRON_L)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Луг до горизонта (основание «твердь»): та же зыбь, что у моря пиратов, но под ветром
    колышется трава: тёмная низина, светлые гребни стеблей, редкие жёлтые и белые цветки."""
    a = lm.Atlas(64, 64, 235)
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = GRASS if w > 0.3 else GRASS_D
            if w > 1.3:
                c = mix(GRASS, GRASS_L, 0.55)
            if w > 1.75:
                c = GRASS_L
            a.px(x, y, c)
    # Стебли: вертикальные пары пикселей, светлые на гребнях и тёмные в низинах.
    for _ in range(150):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = a.get(x, y)[:3]
        k = 1.18 if a.rng.random() < 0.5 else 0.82
        wpx(a, x, y, mul(c, k)), wpx(a, x, y + 1, mul(c, k * 0.92))
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, rgb("F2E060") if a.rng.random() < 0.6 else rgb("F4F4F0"))
        wpx(a, x, y + 1, GRASS_D)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_rock():
    """Кладка стены: тёсаные блоки 16×8 вразбежку со светлым раствором, у каждого блока свой тон,
    фаска сверху слева, тёмная кромка снизу, трещины, пятна мха в нижних швах."""
    a = lm.Atlas(64, 64, 237)
    a.rect(0, 0, 64, 64, MORTAR)
    for row in range(8):
        y = row * 8
        off = (row % 2) * 8
        for col in range(4):
            x = off + col * 16
            tone = a.rng.uniform(0.86, 1.12)
            c = mul(STONE, tone)
            wrect(a, x + 1, y + 1, 15, 7, c)
            wrect(a, x + 1, y + 1, 15, 1, mul(STONE_L, tone))
            wrect(a, x + 1, y + 1, 1, 7, mul(STONE_L, tone * 0.9))
            wrect(a, x + 1, y + 7, 15, 1, mul(STONE_D, 1.05))
            wrect(a, x + 15, y + 2, 1, 6, mul(STONE_D, 1.1))
            # Грань раствора: тень под блоком.
            wrect(a, x + 1, y + 8, 15, 1, mul(MORTAR, 0.78))
            # Выщербины и трещины.
            if a.rng.random() < 0.5:
                cx, cy = x + a.rng.randrange(4, 12), y + a.rng.randrange(2, 4)
                for k in range(a.rng.randrange(2, 5)):
                    wpx(a, cx + k // 2, cy + k, STONE_D)
    for _ in range(110):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        if a.get(x, y)[:3] != MORTAR:
            wpx(a, x, y, STONE_D if a.rng.random() < 0.5 else STONE_L)
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8 + 8
        wrect(a, x, y, a.rng.randrange(2, 5), 1, MOSS)
        wpx(a, x + 1, y - 1, mul(MOSS, 0.7))
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_sail():
    """Знамя: тканый багрянец, золотая кайма поперёк и золотые ромбы герба вразбежку, швы по
    краю и по середине."""
    a = lm.Atlas(32, 32, 239)
    for y in range(32):
        for x in range(32):
            k = 1.0 + 0.07 * (1 if (x + y) % 2 == 0 else -1) + 0.05 * math.sin(y * math.pi / 8.0)
            a.px(x, y, mul(RED, k))
    # Золотая полоса с тёмными кантами.
    for y0 in (13, ):
        wrect(a, 0, y0 - 1, 32, 1, GOLD_D)
        wrect(a, 0, y0, 32, 3, GOLD)
        wrect(a, 0, y0, 32, 1, GOLD_L)
        wrect(a, 0, y0 + 3, 32, 1, GOLD_D)
        for x in range(1, 32, 4):
            wpx(a, x, y0 + 1, GOLD_D)
    # Ромбы герба с четырьмя лучами.
    for cx, cy in ((8, 4), (24, 4), (8, 24), (24, 24)):
        for d in range(-2, 3):
            w = 2 - abs(d)
            for i in range(-w, w + 1):
                wpx(a, cx + i, cy + d, GOLD if (i + d) % 2 == 0 else GOLD_L)
        wpx(a, cx, cy - 3, GOLD_D), wpx(a, cx, cy + 3, GOLD_D)
        wpx(a, cx - 3, cy, GOLD_D), wpx(a, cx + 3, cy, GOLD_D)
    for x in (0, 16):
        a.rect(x, 0, 1, 32, mul(RED, 0.62))
        a.rect(x + 1, 0, 1, 32, mul(RED, 1.12))
    for _ in range(26):
        wpx(a, a.rng.randrange(32), a.rng.randrange(32), RED_D if a.rng.random() < 0.6 else RED_L)
    a.noise(0, 0, 32, 32, 0.05)
    return a


def tex_grass():
    """Газон: пятна тоном, ворсинки в два пикселя, ромашки и красные клеверные головки,
    проплешины утоптанной земли."""
    a = lm.Atlas(64, 64, 241)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.08 * math.sin(x * math.pi / 16.0 + 1.5 * math.sin(y * math.pi / 16.0))
            a.px(x, y, mul(LAWN, k))
    for _ in range(280):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = LAWN_D if a.rng.random() < 0.55 else LAWN_L
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 3, 2, DIRT_D)
        wpx(a, x + 1, y, DIRT)
    # Ромашки: белые лепестки крестом и жёлтая серединка.
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            wpx(a, x + dx, y + dy, rgb("F4F4EC"))
        wpx(a, x, y, rgb("F0C838"))
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, rgb("C83A52")), wpx(a, x + 1, y, rgb("E8708A")), wpx(a, x, y + 1, LAWN_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_road():
    """Булыжная мостовая: ряды камней по 8 пикселей со сдвигом, у каждого свой тон и блик,
    тёмные швы; колеи обкатаны на тех же столбцах, что у пиратов (камни там темнее и глаже)."""
    a = lm.Atlas(64, 64, 243)
    a.rect(0, 0, 64, 64, COB_D)
    for row in range(8):
        y = row * 8
        widths = [10, 11, 10, 11, 11, 11]
        a.rng.shuffle(widths)
        x = (row * 5) % 11
        for w in widths:
            tone = a.rng.uniform(0.86, 1.14)
            c = mul(COB, tone)
            for j in range(1, 8):
                for i in range(1, w):
                    # Скруглённые углы камня.
                    if (i in (1, w - 1) and j in (1, 7)):
                        continue
                    wpx(a, x + i, y + j, c)
            wrect(a, x + 2, y + 1, w - 3, 1, mul(COB_L, tone))
            wpx(a, x + 1, y + 2, mul(COB_L, tone * 0.95))
            wrect(a, x + 2, y + 7, w - 2, 1, mul(COB_D, 1.2))
            wpx(a, x + w - 1, y + 3, mul(COB_D, 1.3))
            x += w
    # Колеи: колёса сгладили верх камней.
    for cx in (18, 44):
        for j in range(64):
            for i in (cx, cx + 1):
                c = a.get(i, j)[:3]
                if c != COB_D:
                    wpx(a, i, j, mul(c, 0.86))
    for _ in range(130):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        if a.get(x, y)[:3] != COB_D:
            wpx(a, x, y, COB_D if a.rng.random() < 0.5 else COB_L)
    # Травинки в швах.
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        wpx(a, x, y, GRASS_D), wpx(a, x + 1, y - 1, GRASS)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_mud():
    """Вспаханная земля: тёмные борозды волной, ямы и лужи с бликом неба, комья, соломинки.
    Заметно темнее мостовой."""
    a = lm.Atlas(64, 64, 245)
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 3.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            a.px(x, y, mul(SOIL, 1.0 + 0.2 * w))
    for _ in range(11):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 6)
        for y in range(-r, r + 1):
            for x in range(-r * 2, r * 2 + 1):
                if (x / 2.0) ** 2 + y ** 2 <= r * r:
                    wpx(a, cx + x, cy + y, SOIL_D)
        wpx(a, cx - 2, cy - r + 1, rgb("7C98B0")), wpx(a, cx - 1, cy - r + 1, rgb("A4BCD0"))
    for _ in range(210):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), SOIL_L if a.rng.random() < 0.5 else SOIL_D)
    for _ in range(14):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, mul(SOIL_L, 1.3)), wpx(a, x + 1, y, SOIL_L), wpx(a, x, y + 1, SOIL_D)
    for _ in range(5):
        straw(a, a.rng.randrange(64), a.rng.randrange(64), 3)
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Разгонная полоса: золотые стрелки вперёд на прозрачном, текстура бежит по полосе."""
    a = lm.Atlas(32, 32, 247)
    white, pale = rgb("FFF6D0"), GOLD
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, white)
                a.px(x, row + 4 + k, pale)
                a.px(x, row + 5 + k, GOLD_D)
    return a


def tex_sky():
    """Панорама: дневное небо, облака с тёмным низом, два ряда зелёных холмов, у горизонта
    замок с башнями под красными кровлями и сторожевая башня, ниже полоса луга. Плитка по
    горизонтали."""
    a = lm.Atlas(128, 64, 249)
    top, low = rgb("3E7CD0"), rgb("BCE0F0")
    for y in range(64):
        t = min(y / 52.0, 1.0)
        a.rect(0, y, 128, 1, mix(top, low, t * t))
    # Облака: валики с тенью снизу.
    for _ in range(8):
        cx, cy, w = a.rng.randrange(128), a.rng.randrange(6, 30), a.rng.randrange(12, 26)
        for k in range(w):
            h = int(2 + 3 * math.sin(math.pi * k / w) + a.rng.random() * 2)
            a.rect((cx + k) % 128, cy - h, 1, h, rgb("F6F8F4"))
            wpx(a, cx + k, cy, rgb("B8CCE0"))
            wpx(a, cx + k, cy - 1, rgb("D8E4EE"))
    # Дальние холмы (период 128 делится на 32 и 16) и ближние.
    for x in range(128):
        h = 6 + 3 * math.sin(x * math.pi / 32.0 + 0.6) + 2 * math.sin(x * math.pi / 16.0 + 2.0)
        a.rect(x, 54 - int(h), 1, int(h) + 8, rgb("7AA89A"))
        wpx(a, x, 54 - int(h), rgb("A0C8B4"))
    # Замок на дальнем холме: стена с зубцами, три башни с кровлями, флажки.
    haze, haze_l, haze_d = rgb("8A90A8"), rgb("B0B6CC"), rgb("646A84")
    roof = rgb("A8323C")
    a.rect(74, 48, 26, 8, haze)
    for x in range(74, 100, 2):
        a.rect(x, 46, 1, 2, haze)
    a.rect(74, 48, 26, 1, haze_l)
    a.rect(98, 48, 2, 8, haze_d)
    for tx, th in ((71, 14), (96, 14), (83, 18)):
        tw = 6 if th == 18 else 5
        a.rect(tx, 56 - th, tw, th, haze)
        a.rect(tx, 56 - th, 1, th, haze_l)
        a.rect(tx + tw - 1, 56 - th, 1, th, haze_d)
        for r in range(4):
            a.rect(tx - 1 + r, 56 - th - 1 - r, tw + 2 - 2 * r, 1, roof if r % 2 == 0 else mul(roof, 0.8))
        a.px(tx + tw // 2, 56 - th - 5, haze_d)
        a.px(tx + tw // 2 + 1, 56 - th - 5, rgb("D83A44"))
        a.px(tx + tw // 2, 56 - th + 4, rgb("2A2E44"))
    a.rect(85, 50, 2, 3, rgb("2A2E44"))
    # Сторожевая башня слева.
    a.rect(20, 40, 5, 16, haze)
    a.rect(20, 40, 1, 16, haze_l)
    a.rect(24, 40, 1, 16, haze_d)
    for x in (20, 22, 24):
        a.rect(x, 38, 1, 2, haze)
    a.px(22, 46, rgb("2A2E44"))
    # Ближние холмы и луг.
    for x in range(128):
        h = 3 + 2 * math.sin(x * math.pi / 16.0 + 1.0) + 1.5 * math.sin(x * math.pi / 8.0)
        a.rect(x, 58 - int(h), 1, 8, rgb("5C9A44"))
        wpx(a, x, 58 - int(h), rgb("86C460"))
    a.rect(0, 58, 128, 6, rgb("4E8C3A"))
    for _ in range(40):
        wpx(a, a.rng.randrange(128), 58 + a.rng.randrange(6), rgb("3A7030") if a.rng.random() < 0.6 else rgb("78B452"))
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
        tile = Image.new("RGBA", (im.width * 2, im.height * 2), (0x2A, 0x2E, 0x3C, 255))
        for ix in range(2):
            for iy in range(2):
                tile.alpha_composite(im, (ix * im.width, iy * im.height))
        tile = tile.resize((tile.width * scale, tile.height * scale), Image.NEAREST).convert("RGB")
        cell = Image.new("RGB", (tile.width + 8, tile.height + 20), (0x2A, 0x2E, 0x3C))
        cell.paste(tile, (4, 16))
        ImageDraw.Draw(cell).text((4, 2), "tex_%s %dx%d" % (name, im.width, im.height), fill=(230, 232, 240))
        cells.append(cell)
    per = 4
    rows = [cells[i:i + per] for i in range(0, len(cells), per)]
    sheet = Image.new("RGB", (max(sum(c.width for c in r) for r in rows), sum(max(c.height for c in r) for r in rows)),
                      (0x2A, 0x2E, 0x3C))
    y = 0
    for r in rows:
        x = 0
        for c in r:
            sheet.paste(c, (x, y))
            x += c.width
        y += max(c.height for c in r)
    sheet.save(path)
    print("лист: %s (%d×%d)" % (path, sheet.width, sheet.height))


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
