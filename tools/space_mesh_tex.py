#!/usr/bin/env python3
"""Текстуры уровня «Космоса» для low poly (#136): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`), свой рисунок. Стиль первой PlayStation: низкое
разрешение, в которое втиснуто как можно больше деталей. Все плитки стыкуются по краям: каждый
пиксель ставится по модулю размера. Набор подключает `lowpoly_meshes.py` через `space_meshes`.

    python3 tools/space_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

REG, REG_D, REG_L = rgb("B4B7C2"), rgb("8C8FA0"), rgb("D6D8E0")  # реголит
METAL, METAL_D, METAL_L = rgb("7A8396"), rgb("4A5062"), rgb("A4ACBC")  # настил станции
BASALT, BASALT_D, BASALT_L = rgb("4C5062"), rgb("2E3040"), rgb("6C7084")
MOSS, MOSS_D, MOSS_L = rgb("7448B4"), rgb("4E2E86"), rgb("9E72DC")
GLOW = rgb("7FE3F0")
HAZARD = rgb("F06A3A")


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def crater(a, cx, cy, r, base):
    """Кратер: тёмная чаша с тенью у верхнего левого края и светлый вал справа снизу."""
    for y in range(-r - 1, r + 2):
        for x in range(-r - 1, r + 2):
            d = math.hypot(x, y)
            if d <= r - 0.6:
                k = 0.74 + 0.2 * ((x + y) / (2.0 * r) + 0.5)
                wpx(a, cx + x, cy + y, mul(base, k))
            elif d <= r + 0.5:
                wpx(a, cx + x, cy + y, mul(base, 1.16 if x + y > 0 else 0.7))


def tex_sand():
    """Лунный реголит: светлая пыль, плавные пятна, россыпь мелких кратеров и камешков."""
    a = lm.Atlas(64, 64, 131)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.05 * math.sin(x * math.pi / 16.0 + 2.0 * math.sin(y * math.pi / 32.0)) \
                + 0.04 * math.sin((y * 3 + x) * math.pi / 32.0)
            a.px(x, y, mul(REG, k))
    for _ in range(190):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), REG_D if a.rng.random() < 0.6 else REG_L)
    for r in (5, 3, 3, 2, 2, 2, 1, 1, 1, 1):
        crater(a, a.rng.randrange(64), a.rng.randrange(64), r, REG)
    for _ in range(9):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, REG_L), wpx(a, x + 1, y, BASALT_L), wpx(a, x, y + 1, BASALT), wpx(a, x + 1, y + 1, REG_D)
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_planks():
    """Настил станции: панели 32×16 вразбежку, тёмные швы со светлой фаской, заклёпки по углам,
    рифление, решётка вентиляции и полоса разметки."""
    a = lm.Atlas(64, 64, 133)
    a.rect(0, 0, 64, 64, METAL)
    for row in range(4):
        y0 = row * 16
        off = (row % 2) * 16
        tone = (1.0, 0.93, 1.05, 0.97)[row]
        for col in range(2):
            x0 = off + col * 32
            wrect(a, x0, y0, 32, 16, mul(METAL, tone * (1.0 if col == 0 else 0.95)))
            # Рифление: короткие косые штрихи в шахматном порядке.
            for j in range(3, 14, 3):
                for i in range(4 + (j % 2) * 3, 30, 6):
                    wpx(a, x0 + i, y0 + j, mul(METAL_L, tone))
                    wpx(a, x0 + i + 1, y0 + j + 1, mul(METAL_D, 1.15))
            wrect(a, x0, y0, 32, 1, METAL_D)
            wrect(a, x0, y0 + 1, 32, 1, METAL_L)
            wrect(a, x0, y0, 1, 16, METAL_D)
            wrect(a, x0 + 1, y0 + 2, 1, 14, mul(METAL_L, 0.94))
            for dx, dy in ((3, 3), (29, 3), (3, 13), (29, 13)):
                wpx(a, x0 + dx, y0 + dy, METAL_L)
                wpx(a, x0 + dx, y0 + dy + 1, METAL_D)
    # Решётка вентиляции и оранжевая полоса разметки на двух панелях.
    for j in range(5):
        wrect(a, 9, 20 + j * 2, 10, 1, BASALT_D)
    for i in range(0, 12, 2):
        wrect(a, 40 + i, 54, 1, 3, HAZARD)
    wpx(a, 22, 38, GLOW), wpx(a, 23, 38, mul(GLOW, 0.7))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Плазма: та же зыбь, что у моря пиратов, фиолетовая глубина и бирюзовые гребни."""
    a = lm.Atlas(64, 64, 135)
    deep, mid, crest = rgb("2E1668"), rgb("6A34C0"), rgb("8CE8F4")
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = mid if w > 0.3 else deep
            if w > 1.35:
                c = mix(mid, crest, 0.4)
            if w > 1.78:
                c = crest
            a.px(x, y, c)
    for _ in range(40):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), rgb("E8FFFF") if a.rng.random() < 0.3 else rgb("A05CE8"))
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_rock():
    """Базальтовая кладка: блоки 16×8 со сдвигом, у каждого свой тон, светлая кромка сверху,
    трещины и фиолетовый лишайник в швах."""
    a = lm.Atlas(64, 64, 137)
    a.rect(0, 0, 64, 64, BASALT)
    for row in range(8):
        y = row * 8
        off = (row % 2) * 8
        for col in range(4):
            x = off + col * 16
            tone = a.rng.uniform(0.84, 1.16)
            wrect(a, x, y, 16, 8, mul(BASALT, tone))
            wrect(a, x + 1, y + 1, 14, 1, mul(BASALT_L, tone))
            wrect(a, x + 1, y + 7, 15, 1, mul(BASALT_D, 1.1))
            wrect(a, x, y, 1, 8, BASALT_D)
            wrect(a, x, y, 16, 1, BASALT_D)
            if a.rng.random() < 0.5:
                cx, cy = x + a.rng.randrange(3, 12), y + a.rng.randrange(2, 5)
                for k in range(a.rng.randrange(2, 5)):
                    wpx(a, cx + k, cy + (k // 2), BASALT_D)
    for _ in range(130):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), BASALT_D if a.rng.random() < 0.5 else BASALT_L)
    for _ in range(14):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        wrect(a, x, y, a.rng.randrange(2, 5), 1, MOSS)
        wpx(a, x + 1, y + 1, MOSS_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_sail():
    """Золотистая фольга солнечной панели: стёганые ромбы, блики на сгибах, шов по краю."""
    a = lm.Atlas(32, 32, 139)
    foil = rgb("C9A24A")
    for y in range(32):
        for x in range(32):
            u, v = (x + y) % 8, (x - y) % 8
            k = 1.0 + 0.1 * math.cos(u * math.pi / 4.0) * math.cos(v * math.pi / 4.0)
            c = mul(foil, k)
            if u == 0 or v == 0:
                c = mul(foil, 0.76)
            elif u == 1 or v == 1:
                c = mul(foil, 1.22)
            a.px(x, y, c)
    for x in (0, 16):
        a.rect(x, 0, 1, 32, mul(foil, 0.62))
    for _ in range(26):
        wpx(a, a.rng.randrange(32), a.rng.randrange(32), rgb("F6E6A8"))
    a.noise(0, 0, 32, 32, 0.06)
    return a


def tex_grass():
    """Фиолетовый мох: пятна тоном, ворсинки в два пикселя, светящиеся споры, проплешины реголита."""
    a = lm.Atlas(64, 64, 141)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.08 * math.sin(x * math.pi / 16.0 + 1.5 * math.sin(y * math.pi / 16.0))
            a.px(x, y, mul(MOSS, k))
    for _ in range(280):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = MOSS_D if a.rng.random() < 0.55 else MOSS_L
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 3, 2, REG_D)
        wpx(a, x + 1, y, REG)
    for _ in range(14):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, GLOW), wpx(a, x + 1, y + 1, MOSS_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_road():
    """Трасса из плит: поперечные швы, укатанные следы колёс, пунктир по оси, заклёпки, потёртости."""
    a = lm.Atlas(64, 64, 143)
    slab, slab_d, slab_l = rgb("5E6476"), rgb("3C4050"), rgb("7E8498")
    a.rect(0, 0, 64, 64, slab)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.04 * math.sin(y * math.pi / 8.0 + x * math.pi / 32.0)
            a.px(x, y, mul(slab, k * (0.95 if (y // 32) % 2 else 1.0)))
    # Следы колёс там же, где колеи у пиратов.
    for x in (18, 19, 44, 45):
        a.rect(x, 0, 1, 64, mul(slab, 0.84))
    for x in (20, 46):
        a.rect(x, 0, 1, 64, mul(slab, 1.1))
    for y in (0, 32):
        a.rect(0, y, 64, 1, slab_d)
        a.rect(0, y + 1, 64, 1, slab_l)
        for x in (4, 28, 36, 60):
            a.px(x, y + 3, slab_l), a.px(x, y + 4, slab_d)
    a.rect(0, 0, 1, 64, slab_d)
    a.rect(32, 0, 1, 64, mul(slab, 0.8))
    # Пунктир разметки по оси.
    for y in (6, 38):
        a.rect(31, y, 2, 12, rgb("C8D4DC"))
    for _ in range(170):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), slab_d if a.rng.random() < 0.55 else slab_l)
    for _ in range(10):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, slab_d), wpx(a, x + 1, y + 1, slab_d), wpx(a, x + 2, y + 1, slab_d)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_mud():
    """Тёмная пыль: мягкие барханчики, ямы темнее, редкие светлые крупинки. Заметно темнее трассы."""
    a = lm.Atlas(64, 64, 145)
    dust, dust_d, dust_l = rgb("34323E"), rgb("201E28"), rgb("54505E")
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 4.0 * math.sin(x * math.pi / 16.0)) * math.pi / 4.0)
            a.px(x, y, mul(dust, 1.0 + 0.16 * w))
    for _ in range(12):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 6)
        for y in range(-r, r + 1):
            for x in range(-r * 2, r * 2 + 1):
                if (x / 2.0) ** 2 + y ** 2 <= r * r:
                    wpx(a, cx + x, cy + y, dust_d)
        wpx(a, cx - 2, cy - r, dust_l), wpx(a, cx - 1, cy - r, dust_l)
    for _ in range(200):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), dust_l if a.rng.random() < 0.45 else dust_d)
    for _ in range(10):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), rgb("8C7CB8"))
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Разгонная полоса: бирюзовые стрелки вперёд на прозрачном, текстура бежит по полосе."""
    a = lm.Atlas(32, 32, 147)
    white, pale = rgb("F0FFFF"), GLOW
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, white)
                a.px(x, row + 4 + k, pale)
                a.px(x, row + 5 + k, mul(pale, 0.7))
    return a


def tex_sky():
    """Панорама купола: чёрно-синее небо со звёздами, туманность, планета с кольцом, у горизонта
    гряда лунных гор и полоса равнины. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 149)
    top, low = rgb("04040C"), rgb("1C1848")
    for y in range(64):
        t = min(y / 54.0, 1.0)
        a.rect(0, y, 128, 1, mix(top, low, t * t))
    # Туманность: два облака точек с дизерингом.
    for cx, cy, rx, ry, col in ((34, 22, 22, 9, rgb("4A2A8C")), (44, 26, 12, 5, rgb("2E5A9C")), (100, 34, 16, 6, rgb("3A2472"))):
        for y in range(-ry, ry + 1):
            for x in range(-rx, rx + 1):
                d = (x / rx) ** 2 + (y / ry) ** 2
                if d <= 1.0 and (d < 0.35 or (x + y) % 2 == 0) and a.rng.random() > d * 0.5:
                    wpx(a, cx + x, cy + y, mix(a.get((cx + x) % 128, (cy + y) % 64)[:3], col, 0.75 - 0.4 * d))
    # Звёзды: мелкие точки и несколько крестиков.
    for _ in range(170):
        k = a.rng.uniform(0.45, 1.0)
        wpx(a, a.rng.randrange(128), a.rng.randrange(54), (int(235 * k), int(240 * k), int(255 * k)))
    for _ in range(7):
        x, y = a.rng.randrange(128), a.rng.randrange(4, 44)
        wpx(a, x, y, rgb("FFFFFF"))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            wpx(a, x + dx, y + dy, rgb("8CA8E0"))
    # Планета с кольцом.
    px, py, pr = 84, 17, 8
    for y in range(-pr, pr + 1):
        for x in range(-pr, pr + 1):
            if x * x + y * y <= pr * pr:
                band = (0.86, 1.0, 0.78, 1.08)[(y + pr) // 3 % 4]
                lit = 0.6 + 0.4 * max(0.0, (-x - y) / (1.5 * pr) + 0.5)
                wpx(a, px + x, py + y, mul(rgb("D08A5A"), band * min(lit, 1.0)))
    for x in range(-14, 15):
        y = int(round(x * 0.22))
        if abs(x) > pr - 2 or y > 0:
            wpx(a, px + x, py + y + 1, rgb("E8D0A8"))
            wpx(a, px + x, py + y + 2, rgb("9A7E64"))
    # Гряда гор у горизонта и равнина.
    for x in range(128):
        h = 4 + 3 * math.sin(x * math.pi / 16.0) + 2 * math.sin(x * math.pi / 8.0 + 1.0) + 2 * math.sin(x * math.pi / 32.0)
        h = max(1, int(h))
        a.rect(x, 56 - h, 1, h, rgb("3A3C52"))
        a.px(x, 56 - h, rgb("9A9CB0"))
    a.rect(0, 56, 128, 8, rgb("6C6E82"))
    a.rect(0, 56, 128, 1, rgb("A8AABC"))
    for _ in range(30):
        wpx(a, a.rng.randrange(128), 57 + a.rng.randrange(7), rgb("50526A"))
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
