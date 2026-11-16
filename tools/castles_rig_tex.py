#!/usr/bin/env python3
"""Текстуры уровня «Замков» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Замки у
«продвинутых» это сказочный день на зелёных холмах: утоптанная земля ристалища, дубовый настил
подъёмного моста с коваными полосами, вода рва, тёсаная кладка стен, бутовая подпорная стенка
на месте обрыва, луг с ромашками, брусчатка с колеями, пашня и красное полотнище с золотыми
лилиями. Плитки стыкуются по краям: поля считаются на периодическом шуме и периодических
решётках, отдельные детали не подходят к краю (лилии на краю нарисованы с обеих сторон).
Цвета из палитры основы 16/32 (`castles16.PALETTE`). Набор подключает `rig_models.py` через
`setting_sets.rig_set`.

    python3 tools/castles_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import castles16 as c16  # noqa: E402

rgb, mul, mix, UNITS = rm.rgb, rm.mul, rm.mix, rm.UNITS


def _pal(index):
    return tuple(c16.PALETTE[index])


STONE = _pal(c16.METAL)      # камень кладки
STONE_L = _pal(c16.GREY)     # светлый камень
IRON = _pal(c16.DARK)        # железо, швы кладки
WOOD = _pal(c16.BRASS)       # дерево
GOLD = _pal(c16.GOLD)
RED = _pal(c16.RED)
CRIMSON = _pal(c16.TAN)
GREEN = _pal(c16.VIOLET)     # трава
GREEN_D = _pal(c16.PLUM)     # тень зелени
WHITE = _pal(c16.WHITE)
NAVY, SEA, AQUA, SKY = _pal(c16.NAVY), _pal(c16.SEA), _pal(c16.AQUA), _pal(c16.SKY)

EARTH = mix(WOOD, _pal(c16.SKIN), 0.62)   # утоптанная земля ристалища
OAK = mix(WOOD, IRON, 0.36)               # морёный дуб моста
COBBLE = mix(STONE, STONE_L, 0.4)         # булыжник
RUBBLE = mix(STONE, WOOD, 0.3)            # бутовый камень, теплее кладки
SOIL = mix(mul(WOOD, 0.42), IRON, 0.25)   # пашня
MEADOW = mix(GREEN, GREEN_D, 0.16)


def _arr(color):
    return np.array(color, dtype=np.float32)


def paint_sand():
    """Земля ристалища: тёплая утоптанная глина, вмятины, россыпь соломы, камешки, кустики травы."""
    p = rm.Paint(701)
    base = _arr(EARTH)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(14, 3), p.tile_noise(40, 2)

    def fn(gx, gy):
        # Плотные светлые проплешины и рыхлые тёмные места.
        tone = 1.0 + 0.08 * low + 0.06 * mid + 0.035 * fine
        return base[None, None, :] * tone[..., None], 128.0 + low * 14.0 + mid * 14.0 + fine * 9.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2400, mul(EARTH, 0.82), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 1500, mul(EARTH, 1.1), 0.06)
    # Вмятины от подков и каблуков: мелкие тёмные дужки.
    for _ in range(9):
        x, y = p.rng.uniform(6, 58), p.rng.uniform(6, 58)
        r = p.rng.uniform(1.0, 1.5)
        turn = p.rng.uniform(0.0, 6.28)
        pts = [(x + r * np.cos(turn + a), y + r * 0.8 * np.sin(turn + a)) for a in np.linspace(0.6, 5.7, 9)]
        p.fold(pts, 0.42, 0.8, 40)
    # Солома: короткие золотистые стебли вразброс, чуть выпуклые.
    straw, straw_d = mix(GOLD, WHITE, 0.3), mix(GOLD, WOOD, 0.5)
    for _ in range(120):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        a, ln = p.rng.uniform(0.0, 3.14), p.rng.uniform(1.0, 2.6)
        dx, dy = np.cos(a) * ln / 2.0, np.sin(a) * ln / 2.0
        p.line([(x - dx + 0.1, y - dy + 0.14), (x + dx + 0.1, y + dy + 0.14)], mul(EARTH, 0.7), 0.16, 120)
        p.line([(x - dx, y - dy), (x + dx, y + dy)], straw if p.rng.random() < 0.7 else straw_d, 0.15, 160)
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.25, 0.6)
        p.ellipse(x + 0.14, y + 0.18, r, r * 0.8, mul(EARTH, 0.64), 110)
        p.ellipse(x, y, r, r * 0.8, STONE if p.rng.random() < 0.6 else STONE_L, 190)
        p.ellipse(x - r * 0.25, y - r * 0.25, r * 0.4, r * 0.3, mix(STONE_L, WHITE, 0.5), 196)
    # Кустики травы пробиваются там, где не топчут.
    for _ in range(12):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(6, 59)
        for _ in range(6):
            lean = p.rng.uniform(-0.8, 0.8)
            p.line([(x + lean * 0.3, y), (x + lean, y - p.rng.uniform(0.8, 1.6))], GREEN if p.rng.random() < 0.6 else GREEN_D, 0.14, 160)
    return p


def paint_planks():
    """Настил подъёмного моста: шесть дубовых досок, стыки вразбежку, две кованые полосы поперёк
    с гранёными заклёпками, сучки и потёртости."""
    p = rm.Paint(703)
    boards = 6
    width = 64.0 / boards
    p.wood(0, 0, 64, 64, boards, True, OAK, 0.34)
    # Торцевые стыки досок: между полосами, через одну.
    for i in range(boards):
        y = 32.0 if i % 2 == 0 else 63.4
        p.fold([(i * width + 0.5, y), ((i + 1) * width - 0.5, y)], 0.45, 0.5, 80)
        for nx in (0.25, 0.75):
            for ny in (-1.6, 1.6):
                cy = min(max(y + ny - (0.0 if y < 60 else 1.0), 0.7), 63.0)
                p.ellipse(i * width + nx * width, cy, 0.34, 0.34, mul(IRON, 0.8), 168)
                p.ellipse(i * width + nx * width - 0.1, cy - 0.1, 0.12, 0.12, mix(IRON, WHITE, 0.4))
    # Сучки.
    for _ in range(8):
        x, y = p.rng.uniform(4, 60), p.rng.choice([p.rng.uniform(4, 10), p.rng.uniform(22, 28), p.rng.uniform(36, 42), p.rng.uniform(54, 60)])
        p.ellipse(x, y, 0.9, 1.4, mul(OAK, 0.72), 108)
        p.ellipse(x, y, 0.5, 0.8, mul(OAK, 0.5), 96)
        p.ellipse(x, y, 0.18, 0.3, mul(OAK, 0.34), 88)
    p.stains(2, 2, 60, 60, 14, 2.2, 0.88)
    # Кованые полосы во всю ширину: тёмное железо, светлая кромка сверху, тень снизу на досках.
    iron_l, iron_d = mix(IRON, STONE_L, 0.35), mul(IRON, 0.62)
    for y0 in (13.0, 45.0):
        p.rect(0.0, y0 + 4.0, 64.0, 0.7, mul(OAK, 0.5), 96)
        p.rect(0.0, y0, 64.0, 4.0, IRON, 176)
        p.rect(0.0, y0, 64.0, 0.5, iron_l, 168)
        p.rect(0.0, y0 + 3.5, 64.0, 0.5, iron_d, 160)
        p.grain(0.0, y0 + 0.5, 64.0, 3.0, 0.1, 0.7, 6.0)
        # Следы молота: мелкие вмятины.
        for _ in range(34):
            x = p.rng.uniform(1.0, 63.0)
            p.ellipse(x, y0 + p.rng.uniform(1.0, 3.0), 0.4, 0.26, mul(IRON, 0.86), 168)
        # Гранёная заклёпка посередине каждой доски: четыре грани пирамидкой.
        for i in range(boards):
            cx, cy, r = (i + 0.5) * width, y0 + 2.0, 1.05
            p.poly([(cx - r, cy - r), (cx + r, cy - r), (cx, cy)], iron_l, 214)
            p.poly([(cx - r, cy - r), (cx, cy), (cx - r, cy + r)], mix(IRON, STONE_L, 0.18), 206)
            p.poly([(cx + r, cy - r), (cx + r, cy + r), (cx, cy)], mul(IRON, 0.8), 206)
            p.poly([(cx - r, cy + r), (cx, cy), (cx + r, cy + r)], iron_d, 200)
    return p


def paint_water():
    """Вода рва: спокойная, длинная рябь поперёк течения, от тёмной зеленоватой глубины к
    голубым бликам; тонкие светлые штрихи на гребнях."""
    p = rm.Paint(705)
    deep = _arr(mix(NAVY, GREEN_D, 0.42))
    mid = _arr(mix(SEA, GREEN, 0.14))
    lit = _arr(AQUA)
    glint = _arr(SKY)
    low, noise = p.tile_noise(4, 3), p.tile_noise(10, 3)
    tau = 2.0 * np.pi

    def fn(gx, gy):
        u, v = gx / UNITS, gy / UNITS
        # Две системы длинных волн: все частоты целые, плитка стыкуется.
        a = np.sin(tau * (v * 4.0 + 0.16 * np.sin(tau * u * 2.0) + 0.22 * low))
        b = np.sin(tau * (v * 7.0 - u * 1.0 + 0.2 * noise))
        c = np.sin(tau * (v * 2.0 + u * 3.0 + 0.3 * low))
        w = a + 0.6 * b + 0.3 * c + 0.35 * noise
        t = rm._smooth_np(np.clip((w + 1.5) / 3.0, 0.0, 1.0))
        hi = rm._smooth_np(np.clip((w - 0.7) / 0.9, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 1.62) / 0.3, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - 0.7 * hi[..., None]) + lit[None, None, :] * (0.7 * hi[..., None])
        color = color * (1.0 - top[..., None]) + glint[None, None, :] * top[..., None]
        return color, 128.0 + w * 26.0
    p.field(fn)
    return p


# Ряды тёсаной кладки: (верх ряда, высота, ширина блока, сдвиг). Высокие и низкие ряды
# чередуются, как в настоящей стене; ширины делят 64 нацело.
_COURSES = ((0.0, 10.0, 16.0, 0.0), (10.0, 6.0, 32.0 / 3.0, 5.0), (16.0, 10.0, 16.0, 8.0), (26.0, 6.0, 16.0, 3.0),
            (32.0, 10.0, 64.0 / 3.0, 12.0), (42.0, 6.0, 32.0 / 3.0, 0.0), (48.0, 10.0, 16.0, 4.0), (58.0, 6.0, 16.0, 11.0))


def paint_bricks():
    """Тёсаная кладка стены: ряды разной высоты, блоки серого камня с тёплыми вставками, светлая
    фаска сверху, тёмные швы с мхом, сколы и следы зубила."""
    p = rm.Paint(727)
    stone, warm, pale = _arr(STONE), _arr(mix(STONE, WOOD, 0.28)), _arr(mix(STONE, STONE_L, 0.55))
    mid, fine = p.tile_noise(16, 3), p.tile_noise(44, 2)
    tones = p.rng.uniform(0.86, 1.16, (8, 8)).astype(np.float32)
    kinds = p.rng.random((8, 8)).astype(np.float32)

    def fn(gx, gy):
        color = np.zeros(gx.shape + (3,), dtype=np.float32)
        height = np.zeros(gx.shape, dtype=np.float32)
        for index, (y0, h, w, shift) in enumerate(_COURSES):
            mask = (gy >= y0) & (gy < y0 + h)
            shifted = (gx + shift) % 64.0
            count = int(round(64.0 / w))
            col = np.clip((shifted / w).astype(np.int32), 0, count - 1)
            lx, ly = shifted - col * w, gy - y0
            edge = np.minimum(np.minimum(lx, w - lx), np.minimum(ly, h - ly))
            seam = np.clip((edge - 0.1) / 0.45, 0.0, 1.0)
            bevel = np.clip((edge - 0.5) / 0.9, 0.0, 1.0)
            tone = tones[index, col]
            kind = kinds[index, col]
            # Свет сверху: верхняя фаска светлее, нижняя темнее.
            lit = 1.0 + 0.14 * np.clip(1.0 - ly / 1.6, 0.0, 1.0) - 0.1 * np.clip(1.0 - (h - ly) / 1.4, 0.0, 1.0)
            # Следы зубила: мелкая косая насечка в середине блока.
            tool = np.sin((lx * 0.8 + ly * 1.6) * np.pi + mid * 2.0) * bevel
            body = stone[None, None, :] + (warm - stone)[None, None, :] * (kind < 0.24)[..., None] + (pale - stone)[None, None, :] * (kind > 0.84)[..., None]
            shade = tone * (1.0 + 0.09 * mid + 0.05 * fine + 0.025 * tool) * (0.36 + 0.64 * seam) * lit
            c = body * shade[..., None]
            hh = 128.0 + mid * 14.0 + fine * 8.0 + tool * 5.0 - (1.0 - seam) * 84.0 - (1.0 - bevel) * 14.0 + (tone - 1.0) * 70.0
            color = np.where(mask[..., None], c, color)
            height = np.where(mask, hh, height)
        return color, height
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(STONE, 0.66), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(STONE, 1.34), 0.07)
    p.wrinkles(2, 2, 60, 60, 8, 3.2, 0.9, 0.62, 60)
    # Мох сидит в горизонтальных швах и свисает на блок ниже.
    moss, moss_l = mix(GREEN_D, GREEN, 0.35), GREEN
    for _ in range(11):
        y0 = _COURSES[int(p.rng.integers(1, 8))][0]
        x = p.rng.uniform(6, 54)
        span = p.rng.uniform(3.0, 7.0)
        p.speckle(x, y0 - 0.5, span, 1.3, int(span * 14), moss, 0.2)
        p.speckle(x + 0.4, y0 - 0.3, span - 0.8, 0.8, int(span * 6), moss_l, 0.14)
    # Знак каменотёса на одном блоке.
    for x, y in ((40.0, 36.0),):
        p.line([(x, y), (x + 2.4, y + 2.4)], mul(STONE, 0.56), 0.24, 86)
        p.line([(x + 2.4, y), (x, y + 2.4)], mul(STONE, 0.56), 0.24, 86)
        p.line([(x + 1.2, y - 0.4), (x + 1.2, y + 2.8)], mul(STONE, 0.56), 0.24, 86)
    return p


def paint_cliff():
    """Подпорная стенка из бута на месте обрыва: дикие камни разного размера без раствора, земля
    в щелях, свет на верхних гранях, мох и травинки между камнями."""
    p = rm.Paint(731)
    cols, rows = 5, 8
    cw, ch = 64.0 / cols, 64.0 / rows
    px = np.zeros(cols * rows, dtype=np.float32)
    py = np.zeros(cols * rows, dtype=np.float32)
    for j in range(rows):
        for i in range(cols):
            px[j * cols + i] = ((i + 0.5 + (0.5 if j % 2 else 0.0) + p.rng.uniform(-0.3, 0.3)) * cw) % 64.0
            py[j * cols + i] = ((j + 0.5 + p.rng.uniform(-0.28, 0.28)) * ch) % 64.0
    tones = p.rng.uniform(0.8, 1.18, cols * rows).astype(np.float32)
    kinds = p.rng.random(cols * rows).astype(np.float32)
    rubble, cool, pale = _arr(RUBBLE), _arr(STONE), _arr(mix(RUBBLE, STONE_L, 0.5))
    earth = _arr(mix(mul(WOOD, 0.52), STONE, 0.25))
    mid, fine = p.tile_noise(12, 3), p.tile_noise(36, 2)

    def fn(gx, gy):
        # Ближайший и второй камень по периодическому расстоянию: камни шире, чем выше.
        f1 = np.full(gx.shape, 1e9, dtype=np.float32)
        f2 = np.full(gx.shape, 1e9, dtype=np.float32)
        who = np.zeros(gx.shape, dtype=np.int32)
        up = np.zeros(gx.shape, dtype=np.float32)
        wx, wy = gx + mid * 0.8, gy + fine * 0.5
        for k in range(cols * rows):
            dx = np.abs(wx - px[k])
            dx = np.minimum(dx, 64.0 - dx)
            dy = wy - py[k]
            dy = (dy + 32.0) % 64.0 - 32.0
            d = np.sqrt(dx * dx + (dy * 1.55) ** 2)
            nearer = d < f1
            f2 = np.where(nearer, f1, np.minimum(f2, d))
            who = np.where(nearer, k, who)
            up = np.where(nearer, dy, up)
            f1 = np.where(nearer, d, f1)
        edge = (f2 - f1) * 0.5
        seam = rm._smooth_np(np.clip((edge - 0.12) / 0.5, 0.0, 1.0))
        dome = rm._smooth_np(np.clip(edge / 2.4, 0.0, 1.0))
        tone, kind = tones[who], kinds[who]
        body = rubble[None, None, :] + (cool - rubble)[None, None, :] * (kind < 0.3)[..., None] + (pale - rubble)[None, None, :] * (kind > 0.8)[..., None]
        # Свет сверху: верх камня светлее, низ в тени.
        lit = 1.0 - 0.07 * np.clip(up / 2.4, -1.0, 1.0)
        shade = tone * (0.8 + 0.2 * dome) * (1.0 + 0.1 * mid + 0.06 * fine) * lit
        color = body * shade[..., None] * seam[..., None] + earth[None, None, :] * ((1.0 - seam) * (0.8 + 0.2 * fine))[..., None]
        return color, 128.0 - 74.0 * (1.0 - seam) + dome * 52.0 - 18.0 + mid * 10.0 + fine * 8.0 + (tone - 1.0) * 40.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(RUBBLE, 0.62), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(RUBBLE, 1.36), 0.07)
    p.wrinkles(2, 2, 60, 60, 10, 2.6, 1.0, 0.64, 56)
    # Мох и травинки в щелях: вокруг случайных стыков.
    for _ in range(10):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(6, 59)
        p.speckle(x - 2.0, y - 0.8, 4.0, 1.6, 34, mix(GREEN_D, GREEN, 0.3), 0.18)
        for _ in range(4):
            bx = x + p.rng.uniform(-1.6, 1.6)
            p.line([(bx, y), (bx + p.rng.uniform(-0.5, 0.5), y - p.rng.uniform(0.9, 1.7))], GREEN, 0.14, 150)
    return p


def paint_grass():
    """Луг: сочная трава с пятнами света, травинки, тёмные островки клевера, ромашки и редкие
    жёлтые лютики."""
    gd, gl = mix(GREEN_D, GREEN, 0.3), mix(GREEN, GOLD, 0.3)
    p = rm._ground(729, MEADOW, 0.13, 0.09, 20.0)
    for _ in range(1500):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.6, 63)
        lean = p.rng.uniform(-0.35, 0.35)
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.6, 1.4))], gd if p.rng.random() < 0.5 else gl, 0.12, 150)
    # Клевер: трилистники кучками.
    clover, clover_l = mix(GREEN_D, GREEN, 0.12), mix(GREEN_D, GREEN, 0.55)
    for _ in range(9):
        cx, cy = p.rng.uniform(6, 58), p.rng.uniform(6, 58)
        for _ in range(7):
            x, y = cx + p.rng.uniform(-2.6, 2.6), cy + p.rng.uniform(-2.0, 2.0)
            turn = p.rng.uniform(0.0, 6.28)
            for k in range(3):
                a = turn + k * 2.094
                p.ellipse(x + 0.42 * np.cos(a), y + 0.42 * np.sin(a), 0.36, 0.36, clover, 158)
                p.ellipse(x + 0.42 * np.cos(a) - 0.08, y + 0.42 * np.sin(a) - 0.08, 0.14, 0.14, clover_l, 162)
    # Ромашки: шесть белых лепестков вокруг золотой серединки.
    for _ in range(20):
        x, y = p.rng.uniform(3.5, 60.5), p.rng.uniform(3.5, 60.5)
        turn = p.rng.uniform(0.0, 1.0)
        for k in range(6):
            a = turn + k * 1.047
            p.ellipse(x + 0.5 * np.cos(a), y + 0.5 * np.sin(a), 0.3, 0.3, WHITE, 172)
        p.ellipse(x, y, 0.27, 0.27, GOLD, 184)
    for _ in range(14):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.ellipse(x, y, 0.3, 0.3, GOLD, 174)
        p.ellipse(x, y, 0.12, 0.12, mix(GOLD, WOOD, 0.5), 176)
    return p


def paint_road():
    """Брусчатка: ряды округлых булыжников вразбежку, у каждого свой тон, земля в швах, две
    накатанные колеи вдоль, солома и травинки между камней."""
    p = rm.Paint(733)
    sw, sh = 8.0, 6.4
    stone, warm, pale = _arr(COBBLE), _arr(mix(COBBLE, WOOD, 0.22)), _arr(mix(COBBLE, WHITE, 0.3))
    gap = _arr(mix(mul(WOOD, 0.5), STONE, 0.3))
    mid, fine = p.tile_noise(14, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.86, 1.14, (10, 8)).astype(np.float32)
    kinds = p.rng.random((10, 8)).astype(np.float32)
    grow = p.rng.uniform(-0.25, 0.3, (10, 8)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / sh).astype(np.int32), 0, 9)
        shifted = (gx + (row % 2) * (sw / 2.0)) % 64.0
        col = np.clip((shifted / sw).astype(np.int32), 0, 7)
        lx, ly = shifted - col * sw, gy - row * sh
        # Скруглённый камень: расстояние до края с радиусом в углах; у камней разный зазор.
        inset = 0.3 - grow[row, col] * 0.3
        ex = np.minimum(lx, sw - lx) - inset
        ey = np.minimum(ly, sh - ly) - inset
        r = 1.9
        q = np.sqrt(np.maximum(r - ex, 0.0) ** 2 + np.maximum(r - ey, 0.0) ** 2)
        edge = np.where((ex < 0.0) | (ey < 0.0), -1.0, r - q)
        seam = rm._smooth_np(np.clip(edge / 0.5, 0.0, 1.0))
        dome = rm._smooth_np(np.clip(edge / r, 0.0, 1.0))
        tone, kind = tones[row, col], kinds[row, col]
        body = stone[None, None, :] + (warm - stone)[None, None, :] * (kind < 0.28)[..., None] + (pale - stone)[None, None, :] * (kind > 0.82)[..., None]
        lit = 1.0 + 0.1 * np.clip(1.0 - ly / 2.4, 0.0, 1.0) - 0.1 * np.clip(1.0 - (sh - ly) / 2.0, 0.0, 1.0)
        shade = tone * (0.84 + 0.16 * dome) * (1.0 + 0.07 * mid + 0.05 * fine) * lit
        color = body * shade[..., None] * seam[..., None] + gap[None, None, :] * ((1.0 - seam) * (0.85 + 0.15 * fine))[..., None]
        return color, 128.0 - 66.0 * (1.0 - seam) + dome * 44.0 - 14.0 + fine * 6.0 + (tone - 1.0) * 30.0
    p.field(fn)
    # Колеи: камень в них вытерт до тёмного блеска и просел.
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 3.2, 0.78, 34)
    p.speckle(0.5, 0.5, 63, 63, 1200, mul(COBBLE, 0.74), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(COBBLE, 1.18), 0.07)
    p.wrinkles(3, 3, 58, 58, 6, 2.4, 1.0, 0.7, 44)
    p.stains(3, 3, 58, 58, 9, 2.6, 0.9)
    # Трава в швах: пучки на границах рядов, не у края плитки.
    for _ in range(16):
        row = int(p.rng.integers(1, 10))
        x, y = p.rng.uniform(4, 60), row * sh + p.rng.uniform(-0.2, 0.2)
        for _ in range(5):
            bx = x + p.rng.uniform(-0.9, 0.9)
            p.line([(bx, y + 0.2), (bx + p.rng.uniform(-0.4, 0.4), y - p.rng.uniform(0.6, 1.3))], GREEN if p.rng.random() < 0.6 else GREEN_D, 0.14, 150)
    straw = mix(GOLD, WHITE, 0.3)
    for _ in range(30):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        a, ln = p.rng.uniform(0.0, 3.14), p.rng.uniform(0.8, 2.0)
        p.line([(x - np.cos(a) * ln / 2, y - np.sin(a) * ln / 2), (x + np.cos(a) * ln / 2, y + np.sin(a) * ln / 2)], straw, 0.14, 150)
    return p


def paint_mud():
    """Пашня: тёмная влажная земля бороздами поперёк пути, комья на гребнях, стерня и камешки.
    Заметно темнее брусчатки."""
    p = rm.Paint(735)
    base = _arr(SOIL)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(44, 2)

    def fn(gx, gy):
        # Восемь борозд на плитку, гребни слегка гуляют.
        phase = gy * 8.0 / UNITS + 0.1 * np.sin(2 * np.pi * gx * 2.0 / UNITS) + 0.16 * low + 0.05 * mid
        saw = phase - np.floor(phase)
        # Отвал плуга: пологий подъём и крутой срез в борозду.
        ridge = np.where(saw < 0.7, saw / 0.7, (1.0 - saw) / 0.3)
        ridge = rm._smooth_np(ridge)
        tone = (0.66 + 0.5 * ridge) * (1.0 + 0.12 * mid + 0.1 * fine)
        return base[None, None, :] * tone[..., None], 128.0 + (ridge - 0.5) * 84.0 + mid * 14.0 + fine * 12.0
    p.field(fn)
    # Комья: мелкие бугорки со светом сверху.
    for _ in range(170):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 62)
        r = p.rng.uniform(0.3, 0.75)
        p.ellipse(x + 0.12, y + 0.2, r, r * 0.75, mul(SOIL, 0.56), 110)
        p.ellipse(x, y, r, r * 0.75, mul(SOIL, p.rng.uniform(0.95, 1.3)), 178)
        p.ellipse(x - r * 0.2, y - r * 0.25, r * 0.45, r * 0.3, mul(SOIL, 1.6), 186)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(SOIL, 1.45), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(SOIL, 0.55), 0.1)
    # Стерня: короткие светлые стебли торчат из гребней.
    stub = mix(GOLD, WOOD, 0.45)
    for _ in range(70):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.line([(x, y), (x + p.rng.uniform(-0.5, 0.5), y - p.rng.uniform(0.7, 1.5))], stub, 0.14, 172)
    for _ in range(12):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        r = p.rng.uniform(0.3, 0.6)
        p.ellipse(x, y, r, r * 0.8, STONE, 190)
        p.ellipse(x - r * 0.25, y - r * 0.25, r * 0.4, r * 0.3, STONE_L, 194)
    return p


# Геральдическая лилия в своих единицах (высота около 10, центр в нуле): лепесток посередине,
# два отогнутых по бокам, перевязь и ножка.
_LILY = (
    [(0.0, -5.2), (1.0, -3.8), (1.5, -2.2), (1.2, -0.6), (0.6, 0.8), (-0.6, 0.8), (-1.2, -0.6), (-1.5, -2.2), (-1.0, -3.8)],
    [(0.9, 0.8), (1.5, -0.9), (2.5, -2.4), (3.8, -2.6), (4.6, -1.6), (4.5, -0.3), (3.7, 0.3), (3.3, -0.6), (2.7, -0.7), (2.3, 0.8)],
    [(-0.9, 0.8), (-1.5, -0.9), (-2.5, -2.4), (-3.8, -2.6), (-4.6, -1.6), (-4.5, -0.3), (-3.7, 0.3), (-3.3, -0.6), (-2.7, -0.7), (-2.3, 0.8)],
    [(-2.8, 0.8), (2.8, 0.8), (2.8, 1.9), (-2.8, 1.9)],
    [(-0.7, 1.9), (0.7, 1.9), (1.2, 3.2), (0.0, 4.6), (-1.2, 3.2)],
    [(1.0, 1.9), (2.3, 1.9), (3.0, 3.3), (1.7, 2.9)],
    [(-1.0, 1.9), (-2.3, 1.9), (-3.0, 3.3), (-1.7, 2.9)],
)


def _lily(p, cx, cy, size, color, height, grow=0.0):
    """Лилия с центром в (cx, cy); `grow` раздувает каждый кусок от его середины (обводка)."""
    for part in _LILY:
        mx = sum(x for x, _ in part) / len(part)
        my = sum(y for _, y in part) / len(part)
        pts = []
        for x, y in part:
            dx, dy = x - mx, y - my
            ln = max((dx * dx + dy * dy) ** 0.5, 1e-6)
            pts.append((cx + (x + dx / ln * grow) * size, cy + (y + dy / ln * grow) * size))
        p.poly(pts, color, height)


def paint_sail():
    """Полотнище знамени: красное сукно с золотыми лилиями в шахматном порядке, ромбовая
    простёжка, шов полотнищ с золотой строчкой, мягкие складки."""
    p = rm._ground(737, RED, 0.07, 0.05, 12.0)
    # Тканый ромбовый узор тоном темнее: диагонали с целым шагом, стыкуются по краям.
    for k in range(-4, 5):
        p.fold([(k * 16.0, 0.0), (k * 16.0 + 64.0, 64.0)], 0.5, 0.86, 22)
        p.fold([(k * 16.0 + 64.0, 0.0), (k * 16.0, 64.0)], 0.5, 0.86, 22)
    gold_d, gold_l = mix(GOLD, WOOD, 0.6), mix(GOLD, WHITE, 0.45)
    # Лилии в шахматном порядке; ряд на краю нарисован с обеих сторон плитки.
    spots = [(16.0, 16.0), (48.0, 16.0), (0.0, 48.0), (32.0, 48.0), (64.0, 48.0)]
    for cx, cy in spots:
        _lily(p, cx + 0.3, cy + 0.4, 1.3, mul(CRIMSON, 0.8), 118, 0.36)
        _lily(p, cx, cy, 1.3, gold_d, 160, 0.3)
        _lily(p, cx, cy, 1.3, GOLD, 172)
        # Блик на среднем лепестке и перевязи.
        p.line([(cx - 0.5, cy - 4.6), (cx - 0.9, cy - 2.4)], gold_l, 0.4, 178)
        p.rect(cx - 3.3, cy + 1.2, 6.6, 0.4, gold_l, 178)
    # Малые золотые крестики между лилиями.
    for cx, cy in ((0.0, 16.0), (32.0, 16.0), (64.0, 16.0), (16.0, 48.0), (48.0, 48.0)):
        for dx, dy in ((1.5, 0.0), (0.0, 1.5)):
            p.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], gold_d, 0.8, 156)
            p.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], GOLD, 0.44, 166)
    p.weave(0, 0, 64, 64, 0.4, 0.07)
    p.wrinkles(1, 1, 62, 62, 12, 6.0, 1.2, 0.86, 30)
    # Швы полотнищ через полплитки, между лилиями и крестиками, с золотой строчкой.
    for x in (8.0, 40.0):
        p.fold([(x, 0), (x, 64)], 0.5, 0.72, 46)
    for x in (9.1, 41.1):
        p.stitch([(x, 0.4), (x, 63.6)], gold_d, 0.16, 0.8)
    p.stains(2, 2, 60, 60, 6, 2.6, 0.92)
    return p


PROPS = {"tex_sand": paint_sand, "tex_planks": paint_planks, "tex_water": paint_water, "tex_rock": paint_bricks,
         "tex_cliff": paint_cliff, "tex_grass": paint_grass, "tex_road": paint_road, "tex_mud": paint_mud,
         "tex_sail": paint_sail}


def preview(path, cell=192):
    """Лист: цвет каждой текстуры плиткой 2×2 и рядом её карта рельефа."""
    from PIL import Image, ImageDraw
    cells = []
    for name, make in PROPS.items():
        color, normal = make().finish()
        tile = Image.new("RGB", (cell * 3, cell * 2), (0x1B, 0x1A, 0x33))
        small = color.convert("RGB").resize((cell, cell), Image.LANCZOS)
        for ix in range(2):
            for iy in range(2):
                tile.paste(small, (ix * cell, iy * cell))
        tile.paste(normal.convert("RGB").resize((cell, cell), Image.LANCZOS), (cell * 2, 0))
        box = Image.new("RGB", (tile.width + 8, tile.height + 20), (0x1B, 0x1A, 0x33))
        box.paste(tile, (4, 16))
        ImageDraw.Draw(box).text((4, 2), "%s %dx%d" % (name, color.width, color.height), fill=(220, 225, 240))
        cells.append(box)
    per = 3
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
