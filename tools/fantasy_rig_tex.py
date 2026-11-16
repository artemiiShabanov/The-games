#!/usr/bin/env python3
"""Текстуры уровня «Фэнтези» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Фэнтези у
«продвинутых» это летающие острова в сиреневых сумерках: светлая тропа с опавшей сиреневой
листвой, настил из тёплых досок с перевязью лиан и резными рунами, волшебная вода от индиго к
бирюзе, кладка из рунных плит, слоистый бок острова с корнями и жилами кристалла, мох с
мухоморами и колокольчиками, дорога из рваного плитняка с рунной осью, тёмный перегной с корнями
и фиолетовое знамя гильдии с золотыми звёздами и полумесяцами. Плитки стыкуются по краям: поля
считаются на периодическом шуме и периодических решётках, отдельные детали не подходят к краю
(знаки знамени на краю нарисованы с обеих сторон). Цвета из палитры основы 16/32
(`fantasy16.PALETTE`). Набор подключает `rig_models.py` через `setting_sets.rig_set`.

    python3 tools/fantasy_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import fantasy16 as f16  # noqa: E402

rgb, mul, mix, UNITS = rm.rgb, rm.mul, rm.mix, rm.UNITS


def _pal(index):
    return tuple(f16.PALETTE[index])


INK = _pal(f16.K)
NAVY, SEA, AQUA, SKY = _pal(f16.NAVY), _pal(f16.SEA), _pal(f16.AQUA), _pal(f16.SKY)
WHITE = _pal(f16.WHITE)
STONE = _pal(f16.GREY)       # сиреневый камень
SKIN = _pal(f16.SKIN)
GREEN = _pal(f16.TAN)        # мох, лианы
GOLD, BRASS = _pal(f16.GOLD), _pal(f16.BRASS)
WOOD = _pal(f16.METAL)       # дерево
BARK = _pal(f16.DARK)        # тёмная кора
RED = _pal(f16.RED)
VIOLET, PLUM = _pal(f16.VIOLET), _pal(f16.PLUM)

PATH = mix(SKIN, STONE, 0.5)               # светлая земля тропы: тёплая с сиреневым
PLANK = mix(WOOD, BRASS, 0.3)              # тёплая доска
SLAB = mix(STONE, PLUM, 0.22)              # рунная плита кладки
FLAG = mix(STONE, mix(NAVY, PLUM, 0.5), 0.36)   # плитняк дороги, темнее и холоднее кладки
CRAG = mix(STONE, PLUM, 0.5)               # бок острова
MOSS = mix(GREEN, mul(GREEN, 0.5), 0.3)
HUMUS = mix(mul(BARK, 0.74), PLUM, 0.14)   # перегной
LEAF = mix(VIOLET, STONE, 0.12)            # сиреневая листва

# Руны: ломаные в квадрате −1..1, штрихи как у резьбы по камню.
RUNES = [
    [[(0.0, 1.0), (0.0, -1.0)], [(0.0, -0.55), (0.7, -1.0)], [(0.0, 0.05), (0.7, -0.4)]],
    [[(0.0, -1.0), (0.6, -0.3), (0.0, 0.4), (-0.6, -0.3), (0.0, -1.0)], [(0.0, 0.4), (0.0, 1.0)]],
    [[(0.0, 1.0), (0.0, -1.0)], [(-0.6, -0.3), (0.0, -1.0), (0.6, -0.3)]],
    [[(-0.5, -1.0), (0.45, -0.35), (-0.45, 0.35), (0.5, 1.0)]],
    [[(-0.6, 1.0), (-0.6, -1.0), (0.0, -0.15), (0.6, -1.0), (0.6, 1.0)]],
    [[(-0.6, -1.0), (0.6, 1.0)], [(0.6, -1.0), (-0.6, 1.0)], [(-0.75, 0.0), (0.75, 0.0)]],
]


def _arr(color):
    return np.array(color, dtype=np.float32)


def _glow(p, strokes, width, color, strength=0.6):
    """Свечение вокруг линий: размытый след прибавляется к цвету, рельеф не трогает."""
    from PIL import Image, ImageDraw, ImageFilter
    layer = Image.new("L", (p.n, p.n), 0)
    d = ImageDraw.Draw(layer)
    for pts in strokes:
        d.line([(x * p.k, y * p.k) for x, y in pts], fill=255, width=max(1, int(round(width * p.k))), joint="curve")
    t = np.asarray(layer.filter(ImageFilter.GaussianBlur(width * p.k * 0.7)), dtype=np.float32) / 255.0
    a = np.asarray(p.im, dtype=np.float32)
    a = a + (_arr(color)[None, None, :] - a) * (t * strength)[..., None]
    p.im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    p.d = ImageDraw.Draw(p.im)


def _rune(p, cx, cy, size, kind, width=0.42, lit=True):
    """Руна: резная канавка, в ней бирюзовый свет со светлой сердцевиной (или тёмная, без света)."""
    strokes = [[(cx + x * size * 0.62, cy + y * size) for x, y in part] for part in RUNES[kind % len(RUNES)]]
    if lit:
        _glow(p, strokes, width * 3.4, AQUA, 0.42)
    for pts in strokes:
        p.line(pts, mul(PLUM, 0.5), width * 2.0, 62)
    if lit:
        for pts in strokes:
            p.line(pts, AQUA, width, 84)
        for pts in strokes:
            p.line(pts, SKY, width * 0.36, 90)
    else:
        for pts in strokes:
            p.line(pts, mul(PLUM, 0.62), width * 0.9, 50)


def _leaf(p, x, y, length, turn, color, height=150):
    """Опавший лист сверху: остроносый овал с жилкой."""
    c, s = math.cos(turn), math.sin(turn)
    shape = [(-1.0, 0.0), (-0.45, 0.42), (0.25, 0.46), (1.0, 0.0), (0.25, -0.46), (-0.45, -0.42)]
    p.poly([(x + (u * c - v * s) * length, y + (u * s + v * c) * length) for u, v in shape], color, height)
    p.line([(x - c * length * 1.25, y - s * length * 1.25), (x + c * length * 0.8, y + s * length * 0.8)], mul(color, 0.66), 0.13, height - 6)


def _star(p, x, y, r, color, height=None, turn=0.0, thin=0.3):
    """Четырёхлучевая звезда."""
    pts = []
    for i in range(8):
        a = turn + i * math.pi / 4.0
        rr = r if i % 2 == 0 else r * thin
        pts.append((x + math.sin(a) * rr, y - math.cos(a) * rr))
    p.poly(pts, color, height)


def _cells(p, nx, ny, jitter=0.36):
    """Рваная мозаика, стыкуется по краям: для каждой точки номер ближайшего узла, расстояние до
    границы с соседом и смещение от узла."""
    gx, gy = p._grid(0, 0, UNITS, UNITS)
    sx, sy = UNITS / nx, UNITS / ny
    best = np.full(gx.shape, 1e9, dtype=np.float32)
    second = np.full(gx.shape, 1e9, dtype=np.float32)
    index = np.zeros(gx.shape, dtype=np.int32)
    for j in range(ny):
        for i in range(nx):
            px = (i + 0.5 + p.rng.uniform(-jitter, jitter)) * sx
            py = (j + 0.5 + p.rng.uniform(-jitter, jitter)) * sy
            dx = (gx - px + UNITS / 2.0) % UNITS - UNITS / 2.0
            dy = (gy - py + UNITS / 2.0) % UNITS - UNITS / 2.0
            dist = np.sqrt(dx * dx + dy * dy)
            closer = dist < best
            second = np.where(closer, best, np.minimum(second, dist))
            index = np.where(closer, j * nx + i, index)
            best = np.where(closer, dist, best)
    return index, (second - best) * 0.5, best


def paint_sand():
    """Тропа острова: светлая тёплая земля с сиреневым отливом, мелкие вмятины, камешки, опавшие
    сиреневые листья и золотая пыльца."""
    p = rm.Paint(801)
    base, cool = _arr(PATH), _arr(mix(PATH, VIOLET, 0.2))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(14, 3), p.tile_noise(40, 2)

    def fn(gx, gy):
        tone = 1.0 + 0.06 * low + 0.05 * mid + 0.03 * fine
        k = np.clip(0.5 + 0.7 * low, 0.0, 1.0)[..., None]
        color = base[None, None, :] * (1.0 - k * 0.5) + cool[None, None, :] * (k * 0.5)
        return color * tone[..., None], 128.0 + low * 12.0 + mid * 16.0 + fine * 9.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2400, mul(PATH, 0.84), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 1500, mul(PATH, 1.1), 0.06)
    # Вмятины: мягкие следы.
    for _ in range(9):
        x, y = p.rng.uniform(6, 58), p.rng.uniform(6, 58)
        r = p.rng.uniform(1.2, 2.4)
        p.ellipse(x, y, r, r * 0.7, mul(PATH, 0.93), 112)
        p.ellipse(x + r * 0.1, y + r * 0.12, r * 0.7, r * 0.45, mul(PATH, 0.98), 118)
    # Камешки с тенью.
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.25, 0.6)
        p.ellipse(x + 0.14, y + 0.18, r, r * 0.8, mul(PATH, 0.66), 112)
        p.ellipse(x, y, r, r * 0.8, mix(STONE, PLUM, 0.3) if p.rng.random() < 0.6 else mix(STONE, WHITE, 0.4), 186)
        p.ellipse(x - r * 0.25, y - r * 0.25, r * 0.36, r * 0.3, WHITE)
    # Опавшая листва: сиреневая, реже золотая.
    for _ in range(30):
        x, y = p.rng.uniform(3.5, 60.5), p.rng.uniform(3.5, 60.5)
        turn, length = p.rng.uniform(0.0, 6.28), p.rng.uniform(0.9, 1.5)
        kind = p.rng.random()
        color = LEAF if kind < 0.55 else (mix(VIOLET, PLUM, 0.5) if kind < 0.85 else BRASS)
        _leaf(p, x + 0.16, y + 0.2, length, turn, mul(PATH, 0.7), 120)
        _leaf(p, x, y, length, turn, color, 156)
    p.speckle(2, 2, 60, 60, 90, GOLD, 0.09)
    return p


def paint_planks():
    """Настил: шесть тёплых досок, поперёк две перевязи из кручёной лианы с листьями, на досках
    резные руны с бирюзовым светом, сучки и потёртости."""
    p = rm.Paint(803)
    boards = 6
    width = 64.0 / boards
    p.wood(0, 0, 64, 64, boards, True, PLANK, 0.34)
    # Торцевые стыки досок вразбежку, по деревянному нагелю с каждой стороны.
    for i in range(boards):
        y = 31.0 if i % 2 == 0 else 63.2
        p.fold([(i * width + 0.5, y), ((i + 1) * width - 0.5, y)], 0.45, 0.5, 80)
        for ny in (-1.7, 1.7):
            cy = min(max(y + ny - (0.0 if y < 60 else 1.2), 0.8), 62.8)
            cx = i * width + width * 0.5
            p.ellipse(cx, cy, 0.5, 0.5, mul(PLANK, 0.5), 110)
            p.ellipse(cx, cy, 0.36, 0.36, mul(PLANK, 1.2), 150)
    # Сучки.
    for _ in range(7):
        x, y = p.rng.uniform(4, 60), float(p.rng.choice([p.rng.uniform(4, 9), p.rng.uniform(22, 27), p.rng.uniform(36, 41), p.rng.uniform(54, 59)]))
        p.ellipse(x, y, 0.9, 1.4, mul(PLANK, 0.72), 108)
        p.ellipse(x, y, 0.5, 0.8, mul(PLANK, 0.5), 96)
        p.ellipse(x, y, 0.18, 0.3, mul(PLANK, 0.34), 88)
    p.stains(2, 2, 60, 60, 12, 2.2, 0.88)
    # Руны на досках: по одной между перевязями, через доску.
    spots = [(0, 24.0, 0), (2, 6.0, 1), (3, 25.5, 2), (5, 7.0, 3), (1, 56.0, 4), (4, 55.0, 5), (2, 38.0, 3), (5, 37.0, 0)]
    for board, y, kind in spots:
        _rune(p, (board + 0.5) * width, y, 2.9, kind, 0.4)
    # Перевязи из лианы: две пряди, витки с наклоном, тень на досках, листья.
    vine, vine_d, vine_l = mix(GREEN, WOOD, 0.3), mix(mul(GREEN, 0.5), BARK, 0.4), mix(GREEN, GOLD, 0.35)
    for y0 in (13.0, 45.0):
        p.rect(0.0, y0 + 3.4, 64.0, 0.8, mul(PLANK, 0.5), 98)
        p.rect(0.0, y0, 64.0, 3.6, vine_d, 150)
        for strand in (0, 1):
            ys = y0 + 0.1 + strand * 1.75
            for k in range(-1, 33):
                x = k * 2.0 + strand * 1.0
                p.poly([(x, ys + 1.7), (x + 0.75, ys), (x + 2.0, ys), (x + 1.25, ys + 1.7)], vine, 190)
                p.line([(x + 0.9, ys + 0.25), (x + 1.75, ys + 0.25)], vine_l, 0.22, 198)
                p.line([(x + 0.1, ys + 1.6), (x + 0.8, ys + 0.1)], vine_d, 0.2, 150)
        # Листья на перевязи: парами, не у края плитки.
        for x in (7.0, 20.5, 33.0, 47.0, 58.0):
            x += p.rng.uniform(-1.0, 1.0)
            for side in (-1.0, 1.0):
                turn = side * p.rng.uniform(0.9, 1.4)
                cx, cy = x + math.cos(turn) * 1.4, y0 + 1.8 + math.sin(turn) * 2.6
                _leaf(p, cx + 0.2, cy + 0.25, 1.5, turn, mul(PLANK, 0.52), 110)
                _leaf(p, cx, cy, 1.5, turn, GREEN if side > 0 else mix(GREEN, GOLD, 0.25), 204)
    return p


def paint_water():
    """Волшебная вода: глубина цвета индиго, синие волны, бирюзовые гребни со светлой пеной,
    сиреневые отсветы и искры на гребнях."""
    p = rm.Paint(805)
    deep, mid, crest, foam, dusk = (_arr(c) for c in (mul(NAVY, 0.8), SEA, AQUA, SKY, mix(PLUM, VIOLET, 0.4)))
    noise, low = p.tile_noise(8, 3), p.tile_noise(3, 2)
    tau = 2.0 * np.pi

    def fn(gx, gy):
        u, v = gx / UNITS, gy / UNITS
        w = (np.sin(tau * (v * 4.0 + 0.16 * np.sin(tau * u * 2.0) + 0.06 * noise))
             + np.sin(tau * (u * 2.0 + v * 3.0 + 0.1 * np.sin(tau * v * 2.0))) + 0.5 * noise)
        t = rm._smooth_np(np.clip((w + 1.3) / 2.6, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 1.3) / 0.5, 0.0, 1.0))
        tip = rm._smooth_np(np.clip((w - 1.85) / 0.3, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        # Сиреневые отсветы неба в спокойных местах.
        k = (np.clip(low * 0.9, 0.0, 1.0) * (1.0 - t) * 0.6)[..., None]
        color = color * (1.0 - k) + dusk[None, None, :] * k
        color = color * (1.0 - top[..., None] * 0.85) + crest[None, None, :] * (top[..., None] * 0.85)
        color = color * (1.0 - tip[..., None]) + foam[None, None, :] * tip[..., None]
        return color, 128.0 + w * 34.0
    p.field(fn)
    # Искры: редкие звёздочки, не у края.
    for _ in range(16):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        r = p.rng.uniform(0.5, 1.0)
        _star(p, x, y, r, SKY, None, 0.0, 0.22)
        p.ellipse(x, y, r * 0.22, r * 0.22, WHITE)
    return p


def paint_bricks():
    """Кладка из рунных плит (борта, стены): сиреневые блоки со сдвигом, тёмные швы со мхом,
    сколы, на части блоков резная руна, на некоторых она светится бирюзой."""
    p = rm.Paint(827)
    stone, warm = _arr(SLAB), _arr(mix(SLAB, SKIN, 0.2))
    gap = _arr(mul(PLUM, 0.42))
    mid, fine = p.tile_noise(16, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.86, 1.14, (8, 4)).astype(np.float32)
    kinds = p.rng.random((8, 4)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        ex = np.minimum(shifted % 16.0, 16.0 - shifted % 16.0)
        ey = np.minimum(gy % 8.0, 8.0 - gy % 8.0)
        edge = np.minimum(ex, ey)
        seam = np.clip(edge / 0.5, 0.0, 1.0)
        bevel = np.clip((edge - 0.5) / 0.7, 0.0, 1.0)
        # Свет сверху: верхняя фаска блока светлее, нижняя темнее.
        lit = 1.0 + 0.12 * np.clip(1.0 - (gy % 8.0) / 1.6, 0.0, 1.0) - 0.1 * np.clip(1.0 - (8.0 - gy % 8.0) / 1.4, 0.0, 1.0)
        tone = tones[row, col] * (1.0 + 0.08 * mid + 0.05 * fine) * lit
        body = stone[None, None, :] + (warm - stone)[None, None, :] * (kinds[row, col] > 0.7)[..., None]
        color = body * tone[..., None] * seam[..., None] + gap[None, None, :] * (1.0 - seam)[..., None]
        return color, 128.0 + mid * 14.0 + fine * 7.0 - (1.0 - seam) * 84.0 - (1.0 - bevel) * 14.0 + (tones[row, col] - 1.0) * 50.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(SLAB, 0.72), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(SLAB, 1.16), 0.07)
    p.wrinkles(2, 2, 60, 60, 8, 3.0, 0.9, 0.66, 56)
    # Сколы по углам блоков.
    for _ in range(12):
        row, col = int(p.rng.integers(0, 8)), int(p.rng.integers(0, 4))
        x = (col * 16.0 - (row % 2) * 8.0) % 64.0 + float(p.rng.choice([0.6, 15.4]))
        y = row * 8.0 + float(p.rng.choice([0.7, 7.3]))
        if 2.0 < x < 62.0:
            r = p.rng.uniform(0.6, 1.1)
            p.ellipse(x, y, r, r * 0.7, mul(SLAB, 0.62), 84)
            p.ellipse(x + r * 0.12, y + r * 0.1, r * 0.6, r * 0.4, mul(SLAB, 0.8), 92)
    # Руны: в середине блока, через блок; каждая третья светится.
    count = 0
    for row in range(8):
        for col in range(4):
            if (row * 3 + col * 2) % 5 not in (0, 3):
                continue
            x = (col * 16.0 + 8.0 - (row % 2) * 8.0) % 64.0
            if x < 4.0 or x > 60.0:
                continue
            _rune(p, x, row * 8.0 + 4.0, 2.3, row + col * 2, 0.34, count % 3 != 1)
            count += 1
    # Мох в швах: подушки вдоль горизонтальных швов, не у края плитки.
    for _ in range(16):
        x, y = p.rng.uniform(5, 59), float(p.rng.integers(1, 8)) * 8.0
        w = p.rng.uniform(2.0, 4.5)
        p.speckle(x - w * 0.5, y - 0.6, w, 1.3, int(w * 16), mul(GREEN, 0.62), 0.2)
        p.speckle(x - w * 0.4, y - 0.6, w * 0.8, 0.9, int(w * 9), GREEN, 0.15)
    return p


def paint_cliff():
    """Бок летающего острова: слоистый сиреневый камень, пласты волной, трещины, свисающие
    корни и бирюзовые жилы кристалла с гранёными друзами."""
    p = rm.Paint(831)
    stone, cool = _arr(CRAG), _arr(mix(NAVY, PLUM, 0.5))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(10, 3), p.tile_noise(28, 2)

    def fn(gx, gy):
        phase = gy / 64.0 * 5.0 + low * 0.5 + mid * 0.16
        band = phase - np.floor(phase)
        ledge = np.clip(band / 0.16, 0.0, 1.0) * np.clip((1.0 - band) / 0.5, 0.0, 1.0)
        layer = np.sin((np.floor(phase) % 5.0) * 2.4) * 0.5 + 0.5
        tone = (0.64 + 0.36 * ledge) * (1.0 + 0.13 * mid + 0.07 * fine)
        color = stone[None, None, :] * (1.0 - layer[..., None] * 0.4) + cool[None, None, :] * (layer[..., None] * 0.4)
        return color * tone[..., None], 128.0 + ledge * 62.0 - 40.0 + mid * 26.0 + fine * 12.0
    p.field(fn)
    p.wrinkles(1, 1, 62, 62, 12, 8.0, 1.2, 0.6, 66)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(CRAG, 0.56), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 450, mul(CRAG, 1.3), 0.08)
    # Жилы кристалла: ломаные со свечением, на изломах друзы из гранёных осколков.
    for _ in range(4):
        x, y = p.rng.uniform(10, 54), p.rng.uniform(10, 54)
        pts = [(x, y)]
        for _ in range(3):
            x, y = x + p.rng.uniform(-6.0, 6.0), y + p.rng.uniform(2.0, 4.5)
            pts.append((min(max(x, 5.0), 59.0), min(max(y, 5.0), 59.0)))
        _glow(p, [pts], 1.5, AQUA, 0.4)
        p.line(pts, mul(SEA, 0.7), 0.6, 110)
        p.line(pts, AQUA, 0.3, 150)
        cx, cy = pts[int(p.rng.integers(1, 3))]
        for k in range(4):
            a = -1.57 + (k - 1.5) * 0.55 + p.rng.uniform(-0.15, 0.15)
            ln, wd = p.rng.uniform(1.6, 2.8), 0.5
            tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
            nx, ny = -math.sin(a) * wd, math.cos(a) * wd
            mx, my = cx + math.cos(a) * ln * 0.6, cy + math.sin(a) * ln * 0.6
            p.poly([(cx - nx, cy - ny), (mx - nx, my - ny), tip, (cx, cy)], AQUA, 200)
            p.poly([(cx + nx, cy + ny), (mx + nx, my + ny), tip, (cx, cy)], mix(SEA, AQUA, 0.4), 190)
            p.line([(cx, cy), tip], SKY, 0.14, 214)
    # Корни: свисают сверху вниз, ветвятся, толще у начала; не доходят до края плитки.
    root, root_d, root_l = mix(WOOD, BARK, 0.3), mul(BARK, 0.7), mix(WOOD, BRASS, 0.4)
    for _ in range(7):
        x, y = p.rng.uniform(6, 58), p.rng.uniform(4, 30)
        length = p.rng.uniform(14.0, 26.0)
        pts, sway = [], p.rng.uniform(0.0, 6.28)
        for i in range(9):
            t = i / 8.0
            pts.append((min(max(x + math.sin(sway + t * 5.0) * 1.6 * t, 3.0), 61.0), min(y + length * t, 60.5)))
        for a, b, i in zip(pts, pts[1:], range(8)):
            wd = 1.1 - i * 0.11
            p.line([(a[0] + 0.35, a[1] + 0.2), (b[0] + 0.35, b[1] + 0.2)], mul(CRAG, 0.5), wd, 96)
        for a, b, i in zip(pts, pts[1:], range(8)):
            wd = 1.1 - i * 0.11
            p.line([a, b], root_d, wd, 176)
            p.line([a, b], root, wd * 0.62, 190)
            p.line([(a[0] - wd * 0.16, a[1]), (b[0] - wd * 0.16, b[1])], root_l, wd * 0.18, 196)
        p.ellipse(pts[0][0], pts[0][1], 0.9, 0.6, root_d, 180)
        p.ellipse(pts[0][0], pts[0][1] - 0.1, 0.55, 0.32, root, 192)
        # Боковой отросток.
        bx, by = pts[4]
        side = 1.0 if p.rng.random() < 0.5 else -1.0
        tip = (min(max(bx + side * 3.0, 3.0), 61.0), min(by + 4.5, 60.5))
        p.line([(bx, by), (bx + side * 1.6, by + 1.6), tip], root_d, 0.5, 170)
        p.line([(bx, by), (bx + side * 1.6, by + 1.6), tip], root, 0.26, 182)
    # Мох на уступах.
    for _ in range(7):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 3.0, y - 0.9, 6, 1.8, 50, mul(GREEN, 0.7), 0.18)
        p.speckle(x - 2.4, y - 0.9, 4.8, 1.2, 26, GREEN, 0.13)
    return p


def paint_grass():
    """Мох: бархатные подушки светлее и темнее, крапчатый ворс, мухоморы шляпками вверх,
    сиреневые колокольчики и золотые светлячки."""
    p = rm.Paint(829)
    base, deep, lime = _arr(MOSS), _arr(mix(mul(GREEN, 0.42), NAVY, 0.22)), _arr(mix(GREEN, GOLD, 0.3))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(9, 2), p.tile_noise(40, 2)

    def fn(gx, gy):
        # Подушки: между буграми тёмные ложбины.
        cushion = np.clip(np.abs(mid) * 2.4, 0.0, 1.0)
        k = np.clip(0.5 + 0.6 * low, 0.0, 1.0)[..., None]
        color = base[None, None, :] * (1.0 - k * 0.35) + lime[None, None, :] * (k * 0.35)
        color = color * cushion[..., None] + (deep[None, None, :] * 0.5 + color * 0.5) * (1.0 - cushion[..., None])
        tone = 1.0 + 0.08 * low + 0.06 * fine
        return color * tone[..., None], 128.0 + cushion * 30.0 - 18.0 + low * 12.0 + fine * 8.0
    p.field(fn)
    # Ворс мха: мелкие звёздочки-побеги и крапины.
    p.speckle(0.5, 0.5, 63, 63, 2600, mul(MOSS, 0.74), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 2200, mix(GREEN, GOLD, 0.25), 0.08)
    for _ in range(420):
        x, y = p.rng.uniform(1.2, 62.8), p.rng.uniform(1.2, 62.8)
        turn, r = p.rng.uniform(0.0, 1.0), p.rng.uniform(0.3, 0.55)
        color = mix(GREEN, GOLD, 0.3) if p.rng.random() < 0.6 else mul(MOSS, 0.66)
        for k in range(3):
            a = turn + k * 1.047
            p.line([(x - math.cos(a) * r, y - math.sin(a) * r), (x + math.cos(a) * r, y + math.sin(a) * r)], color, 0.11, 150)
    # Колокольчики: пять сиреневых лепестков, светлая серединка.
    for _ in range(18):
        x, y = p.rng.uniform(3.5, 60.5), p.rng.uniform(3.5, 60.5)
        turn = p.rng.uniform(0.0, 1.2)
        for k in range(5):
            a = turn + k * 1.2566
            p.ellipse(x + 0.52 * math.cos(a), y + 0.52 * math.sin(a), 0.34, 0.34, mix(VIOLET, WHITE, 0.25), 170)
        p.ellipse(x, y, 0.24, 0.24, SKY, 182)
    # Мухоморы сверху: тень, красная шляпка с тёмным краем, белые крапины.
    for _ in range(9):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        r = p.rng.uniform(0.9, 1.5)
        p.ellipse(x + 0.3, y + 0.38, r, r * 0.92, mul(MOSS, 0.5), 112)
        p.ellipse(x, y, r, r * 0.92, mul(RED, 0.7), 196)
        p.ellipse(x - r * 0.06, y - r * 0.08, r * 0.84, r * 0.76, RED, 210)
        p.ellipse(x - r * 0.3, y - r * 0.32, r * 0.3, r * 0.22, mix(RED, WHITE, 0.4), 216)
        for k in range(5):
            a = k * 1.2566 + p.rng.uniform(0.0, 0.6)
            d = r * (0.56 if k else 0.0)
            p.ellipse(x + math.cos(a) * d, y + math.sin(a) * d * 0.9, r * 0.17, r * 0.15, WHITE, 220)
    # Светлячки.
    for _ in range(14):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.ellipse(x, y, 0.42, 0.42, mix(GOLD, MOSS, 0.5), 150)
        p.ellipse(x, y, 0.2, 0.2, mix(GOLD, WHITE, 0.5), 170)
    return p


def paint_road():
    """Дорога из рваного плитняка: плиты неправильной формы, у каждой свой тон, мох в швах, две
    вытертые колеи вдоль, по оси пунктир из вделанных рунных пластин с бирюзовым светом."""
    p = rm.Paint(833)
    index, edge, _dist = _cells(p, 5, 6, 0.34)
    count = 30
    stone, warm, cool = _arr(FLAG), _arr(mix(FLAG, SKIN, 0.16)), _arr(mix(FLAG, SEA, 0.06))
    gap = _arr(mix(mul(GREEN, 0.4), mul(PLUM, 0.5), 0.5))
    mid, fine = p.tile_noise(14, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.9, 1.1, count).astype(np.float32)
    kinds = p.rng.random(count).astype(np.float32)

    def fn(gx, gy):
        seam = rm._smooth_np(np.clip((edge - 0.14) / 0.36, 0.0, 1.0))
        bevel = rm._smooth_np(np.clip((edge - 0.3) / 1.3, 0.0, 1.0))
        tone, kind = tones[index], kinds[index]
        body = stone[None, None, :] + (warm - stone)[None, None, :] * (kind < 0.3)[..., None] + (cool - stone)[None, None, :] * (kind > 0.74)[..., None]
        shade = tone * (0.9 + 0.1 * bevel) * (1.0 + 0.06 * mid + 0.04 * fine)
        color = body * shade[..., None] * seam[..., None] + gap[None, None, :] * ((1.0 - seam) * (0.85 + 0.15 * fine))[..., None]
        return color, 128.0 - 70.0 * (1.0 - seam) + bevel * 16.0 - 8.0 + fine * 6.0 + (tone - 1.0) * 40.0
    p.field(fn)
    # Колеи: камень вытерт и просел.
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.8, 0.84, 26)
    p.speckle(0.5, 0.5, 63, 63, 1200, mul(FLAG, 0.78), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(FLAG, 1.16), 0.07)
    p.wrinkles(3, 3, 58, 58, 7, 3.4, 1.0, 0.7, 46)
    p.stains(3, 3, 58, 58, 8, 2.6, 0.9)
    # Мох в швах: пятна по плитке, остаются только там, где шов.
    for _ in range(46):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        ix, iy = int(x * p.k), int(y * p.k)
        if edge[iy, ix] < 0.5 and not (29.0 < x < 35.0):
            p.speckle(x - 1.0, y - 0.7, 2.0, 1.4, 14, mul(GREEN, 0.7), 0.17)
            p.speckle(x - 0.7, y - 0.5, 1.4, 1.0, 7, GREEN, 0.12)
    # Ось: вделанные пластины тёмного камня с золотой кромкой и светящейся руной.
    plate = mix(NAVY, PLUM, 0.4)
    for n, y in enumerate((6.0, 38.0)):
        p.rect(30.9, y - 0.4, 2.2, 12.8, mul(FLAG, 0.5), 96)
        p.rect(31.1, y - 0.2, 1.8, 12.4, BRASS, 150)
        p.rect(31.3, y, 1.4, 12.0, plate, 138)
        strokes = [[(32.0, y + 0.9), (32.0, y + 11.1)]]
        _glow(p, strokes, 1.6, AQUA, 0.35)
        p.line(strokes[0], AQUA, 0.36, 146)
        for k in range(4):
            cy = y + 1.9 + k * 2.75
            p.poly([(32.0, cy - 0.8), (32.55, cy), (32.0, cy + 0.8), (31.45, cy)], SKY if (k + n) % 2 == 0 else AQUA, 150)
    return p


def paint_mud():
    """Перегной под деревьями: тёмная бурая земля с лиловым отливом, бугры и ямы, узловатые
    корни поверх, прелые листья и светлые крупинки. Заметно темнее дороги."""
    p = rm.Paint(835)
    base, wet = _arr(HUMUS), _arr(mix(mul(BARK, 0.5), NAVY, 0.3))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(12, 3), p.tile_noise(36, 2)

    def fn(gx, gy):
        lump = rm._smooth_np(np.clip(0.5 + 0.8 * mid, 0.0, 1.0))
        tone = 1.0 + 0.16 * (lump - 0.5) + 0.12 * low + 0.06 * fine
        k = np.clip(-low * 1.2, 0.0, 1.0)[..., None]
        color = base[None, None, :] * (1.0 - k * 0.6) + wet[None, None, :] * (k * 0.6)
        return color * tone[..., None], 128.0 + (lump - 0.5) * 50.0 + low * 14.0 + fine * 12.0
    p.field(fn)
    for _ in range(9):
        x, y = p.rng.uniform(8, 56), p.rng.uniform(8, 56)
        rx, ry = p.rng.uniform(2.2, 4.4), p.rng.uniform(1.3, 2.6)
        p.ellipse(x, y, rx, ry, mul(HUMUS, 0.76), 92)
        p.ellipse(x + rx * 0.1, y + ry * 0.2, rx * 0.7, ry * 0.6, mul(HUMUS, 0.88), 100)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(HUMUS, 1.5), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(HUMUS, 0.55), 0.1)
    # Корни: толстые у начала и тонкие к концу, с боковыми корешками, тенью и светлой спинкой.
    root, root_d, root_l = mix(WOOD, BARK, 0.45), mul(BARK, 0.6), mix(WOOD, STONE, 0.3)

    def run(x, y, turn, length, thick):
        sway = p.rng.uniform(0.0, 6.28)
        pts = []
        for i in range(9):
            t = i / 8.0
            px = x + math.cos(turn) * length * t - math.sin(turn) * math.sin(sway + t * 4.0) * length * 0.07
            py = y + math.sin(turn) * length * t + math.cos(turn) * math.sin(sway + t * 4.0) * length * 0.07
            pts.append((min(max(px, 3.0), 61.0), min(max(py, 3.0), 61.0)))
        widths = [thick * (1.0 - 0.8 * i / 8.0) for i in range(8)]
        for a, b, wd in zip(pts, pts[1:], widths):
            p.line([(a[0] + 0.3, a[1] + 0.45), (b[0] + 0.3, b[1] + 0.45)], mul(HUMUS, 0.5), wd, 100)
        for a, b, wd in zip(pts, pts[1:], widths):
            p.line([a, b], root_d, wd, 184)
            p.ellipse(a[0], a[1], wd * 0.5, wd * 0.5, root_d, 184)
        for a, b, wd in zip(pts, pts[1:], widths):
            p.line([a, b], root, wd * 0.62, 200)
            p.line([(a[0], a[1] - wd * 0.17), (b[0], b[1] - wd * 0.17)], root_l, wd * 0.16, 208)
        return pts

    for _ in range(5):
        x, y = p.rng.uniform(6, 30), p.rng.uniform(8, 56)
        turn, length = p.rng.uniform(-0.5, 0.5), p.rng.uniform(18.0, 28.0)
        # Корешки рисуются первыми, чтобы основной корень лёг поверх их начала.
        state = p.rng.bit_generator.state
        spine = run(x, y, turn, length, 0.0)
        for i in (2, 4, 5):
            side = 1.0 if p.rng.random() < 0.5 else -1.0
            run(spine[i][0], spine[i][1], turn + side * p.rng.uniform(0.6, 1.1), length * p.rng.uniform(0.22, 0.36), 0.7)
        after = p.rng.bit_generator.state
        p.rng.bit_generator.state = state
        run(x, y, turn, length, 1.7)
        p.rng.bit_generator.state = after
        # Узел у начала корня.
        p.ellipse(x, y, 1.15, 1.0, root_d, 190)
        p.ellipse(x - 0.1, y - 0.15, 0.7, 0.56, root, 204)
    # Прелые листья.
    for _ in range(16):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        _leaf(p, x, y, p.rng.uniform(0.8, 1.3), p.rng.uniform(0.0, 6.28),
              mix(PLUM, HUMUS, 0.35) if p.rng.random() < 0.7 else mix(BRASS, HUMUS, 0.45), 150)
    p.speckle(0.5, 0.5, 63, 63, 70, mix(VIOLET, STONE, 0.4), 0.1)
    return p


def _crescent(p, cx, cy, r, color, height=None):
    """Полумесяц рогами вправо: внешняя дуга и внутренняя со сдвигом."""
    outer = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in np.linspace(0.9, 2.0 * math.pi - 0.9, 22)]
    ox, rr = r * 0.46, r * 0.84
    a0 = math.atan2(outer[-1][1] - cy, outer[-1][0] - cx - ox)
    a1 = math.atan2(outer[0][1] - cy, outer[0][0] - cx - ox)
    inner = [(cx + ox + math.cos(a) * rr, cy + math.sin(a) * rr) for a in np.linspace(a0 + 2.0 * math.pi, a1, 18)]
    p.poly(outer + inner, color, height)


def paint_sail():
    """Знамя гильдии: фиолетовое сукно, тканая сетка ромбов, в шахматном порядке золотые
    полумесяцы со звездой и малые звёзды, шов полотнищ с золотой строчкой, мягкие складки."""
    p = rm._ground(837, VIOLET, 0.07, 0.05, 12.0)
    for k in range(-4, 5):
        p.fold([(k * 16.0, 0.0), (k * 16.0 + 64.0, 64.0)], 0.5, 0.86, 22)
        p.fold([(k * 16.0 + 64.0, 0.0), (k * 16.0, 64.0)], 0.5, 0.86, 22)
    gold_d, gold_l = mix(GOLD, BRASS, 0.7), mix(GOLD, WHITE, 0.5)
    shade = mul(PLUM, 0.9)
    # Полумесяц со звездой между рогами; ряд на краю нарисован с обеих сторон плитки.
    for cx, cy in ((16.0, 16.0), (48.0, 16.0), (0.0, 48.0), (32.0, 48.0), (64.0, 48.0)):
        _crescent(p, cx - 0.4, cy + 0.5, 4.6, shade, 118)
        _crescent(p, cx - 0.8, cy, 4.9, gold_d, 160)
        _crescent(p, cx - 0.8, cy, 4.3, GOLD, 172)
        p.line([(cx - 4.3, cy - 1.6), (cx - 3.4, cy - 3.0)], gold_l, 0.4, 178)
        _star(p, cx + 2.5, cy + 0.5, 2.5, shade, 118, 0.0, 0.34)
        _star(p, cx + 2.1, cy, 2.6, gold_d, 160, 0.0, 0.36)
        _star(p, cx + 2.1, cy, 2.1, GOLD, 172, 0.0, 0.32)
        p.ellipse(cx + 2.1, cy, 0.4, 0.4, gold_l, 180)
    # Малые звёзды между знаками, бирюзовая точка в середине.
    for cx, cy in ((0.0, 16.0), (32.0, 16.0), (64.0, 16.0), (16.0, 48.0), (48.0, 48.0)):
        _star(p, cx, cy, 2.4, gold_d, 156, math.pi / 4.0, 0.3)
        _star(p, cx, cy, 1.9, GOLD, 166, math.pi / 4.0, 0.26)
        p.ellipse(cx, cy, 0.45, 0.45, AQUA, 174)
    p.weave(0, 0, 64, 64, 0.4, 0.07)
    p.wrinkles(1, 1, 62, 62, 12, 6.0, 1.2, 0.86, 30)
    # Швы полотнищ через полплитки, между знаками, с золотой строчкой.
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
