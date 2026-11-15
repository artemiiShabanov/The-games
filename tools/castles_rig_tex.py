#!/usr/bin/env python3
"""Текстуры уровня «Замков» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Замки у
«продвинутых» это сказочный день на зелёных лугах: тёплый камень, трава и доски, цвет спокойный.
Слоты: пашня (песок), доски моста, вода рва, кладка стен, мелованный обрыв холма, трава с клевером
и розами, брусчатка дороги, грязь колеи, знамя с гербом. Плитки стыкуются по краям: поля
считаются на периодическом шуме, брусчатка на периодической ячеистой сетке, отдельные детали не
подходят к краю. Грязь заметно темнее брусчатки. Набор подключает `rig_models.py` через
`castles_rig`.

    python3 tools/castles_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402

rgb, mul, UNITS = rm.rgb, rm.mul, rm.UNITS

LOAM = rgb("B49A68")
OAK = rgb("8A5E36")
MOAT = rgb("3C7C78")
MASONRY = rgb("9A9486")
CHALK = rgb("B8AE98")
MEADOW = rgb("5C9A44")
COBBLE = rgb("8C887C")
MIRE = rgb("40301E")
BANNER = rgb("A82C36")
GOLD = rgb("E2B83F")
IRON = rgb("3A3C46")


def _cells(p, count, jitter=0.38):
    """Периодическая ячеистая сетка: расстояния до двух ближайших точек и номер ближайшей."""
    gx, gy = p._grid(0, 0, UNITS, UNITS)
    px = gx / UNITS * count
    py = gy / UNITS * count
    jx = p.rng.uniform(-jitter, jitter, (count, count))
    jy = p.rng.uniform(-jitter, jitter, (count, count))
    ix, iy = np.floor(px).astype(np.int32), np.floor(py).astype(np.int32)
    d1 = np.full(px.shape, 1e9, dtype=np.float32)
    d2 = np.full(px.shape, 1e9, dtype=np.float32)
    ident = np.zeros(px.shape, dtype=np.int32)
    for oy in (-2, -1, 0, 1, 2):
        for ox in (-2, -1, 0, 1, 2):
            cx, cy = ix + ox, iy + oy
            wx, wy = cx % count, cy % count
            dx = cx + 0.5 + jx[wy, wx] - px
            dy = cy + 0.5 + jy[wy, wx] - py
            d = np.sqrt(dx * dx + dy * dy)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            ident = np.where(closer, wy * count + wx, ident)
            d1 = np.where(closer, d, d1)
    return d1, d2, ident


def paint_sand():
    """Пашня: светлая сухая земля с бороздами вдоль, соломинки, комки и мелкие камешки."""
    p = rm.Paint(441)
    base = np.array(LOAM, dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(44, 2)

    def fn(gx, gy):
        furrow = np.sin(2 * np.pi * (gy * 8.0 / UNITS + 0.07 * low + 0.04 * np.sin(2 * np.pi * gx * 2.0 / UNITS)))
        tone = 1.0 + 0.07 * low + 0.05 * mid + 0.03 * fine + 0.06 * furrow
        return base[None, None, :] * tone[..., None], 128.0 + furrow * 24.0 + mid * 14.0 + fine * 8.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2200, mul(LOAM, 0.8), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 1500, mul(LOAM, 1.15), 0.07)
    # Соломинки: короткие золотистые черты вдоль борозд.
    for _ in range(190):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 62)
        ln = p.rng.uniform(0.7, 1.7)
        tilt = p.rng.uniform(-0.25, 0.25)
        p.line([(x, y), (x + ln, y + tilt)], rgb("E4CC7C") if p.rng.random() < 0.7 else rgb("C8A458"), 0.12, 160)
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.3, 0.7)
        p.ellipse(x + 0.12, y + 0.16, r, r * 0.8, mul(LOAM, 0.6), 110)
        p.ellipse(x, y, r, r * 0.8, rgb("A8A092") if p.rng.random() < 0.6 else rgb("8C8678"), 190)
    return p


def paint_planks():
    """Настил моста: доски вдоль, у каждой свой тон и сучки, торцевые стыки вразбежку, железные
    гвозди и тёмные щели между досками."""
    p = rm.Paint(443)
    base = np.array(OAK, dtype=np.float32)
    mid, fine = p.tile_noise(10, 3), p.tile_noise(52, 2)
    boards = 8
    tones = p.rng.uniform(0.86, 1.14, (boards, 2)).astype(np.float32)
    phases = p.rng.uniform(0.0, 6.28, boards).astype(np.float32)
    cut = p.rng.uniform(14.0, 50.0, boards).astype(np.float32)
    streaks = p.rng.normal(0.0, 1.0, (boards, 64)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, boards - 1)
        local = (gy % 8.0) / 8.0
        # Каждая доска в два куска: стык по x у каждой доски свой.
        part = ((gx - cut[row]) % 64.0 < 32.0).astype(np.int32)
        ex = np.minimum((gx - cut[row]) % 32.0, 32.0 - (gx - cut[row]) % 32.0)
        ey = np.minimum(gy % 8.0, 8.0 - gy % 8.0)
        edge = np.minimum(ex, ey)
        seam = np.clip(edge / 0.3, 0.0, 1.0)
        wave = np.sin(2 * np.pi * (local * 3.0 + 0.3 * np.sin(2 * np.pi * gx / UNITS * 2.0 + phases[row])))
        streak = streaks[row, np.clip((local * 64).astype(np.int32), 0, 63)]
        fibre = 1.0 + 0.05 * wave + 0.05 * streak + 0.03 * fine
        tone = tones[row, part] * fibre * (0.42 + 0.58 * seam) * (1.0 + 0.06 * mid)
        return base[None, None, :] * tone[..., None], 128.0 + wave * 5.0 + streak * 4.0 - (1.0 - seam) * 76.0 + fine * 4.0
    p.field(fn)
    # Гвозди и железные накладки на стыках: на каждой доске пара гвоздей у каждого торца.
    for row in range(boards):
        for part in range(2):
            x0 = (cut[row] + part * 32.0) % 64.0
            for dx in (1.6, 30.4):
                x, y = (x0 + dx) % 64.0, row * 8.0 + 4.0
                if 1.2 < x < 62.8:
                    p.ellipse(x, y, 0.4, 0.4, mul(IRON, 1.0), 180)
                    p.ellipse(x - 0.1, y - 0.1, 0.14, 0.14, rgb("8C909C"))
    # Сучки.
    for _ in range(9):
        x, y = p.rng.uniform(6, 58), (p.rng.integers(0, boards) * 8.0) + 4.0
        p.ellipse(x, y, 1.0, 0.7, mul(OAK, 0.58), 96)
        p.ellipse(x, y, 0.5, 0.32, mul(OAK, 0.42), 80)
    p.stains(2, 2, 60, 60, 10, 2.4, 0.9)
    return p


def paint_water():
    """Вода рва: тёмная зелёно-бирюзовая глубина, волны к светлым гребням, листья кувшинок."""
    p = rm.Paint(445)
    deep, mid, crest = (np.array(rgb(c), dtype=np.float32) for c in ("1C4C54", "3C8478", "B8E8D8"))
    noise = p.tile_noise(8, 3)

    def fn(gx, gy):
        w = np.sin((gx + 6.0 * np.sin(gy * np.pi / 8.0)) * np.pi / 16.0) + np.sin((gy * 2.0 + gx) * np.pi / 16.0) + 0.5 * noise
        t = rm._smooth_np(np.clip((w + 1.2) / 2.6, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 1.8) / 0.45, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - top[..., None]) + crest[None, None, :] * top[..., None]
        return color, 128.0 + w * 34.0
    p.field(fn)
    # Листья кувшинок: круг с вырезом-клином, подальше от краёв плитки.
    for x, y, r in ((17.0, 20.0, 2.6), (44.0, 40.0, 3.0), (23.0, 49.0, 2.0)):
        p.ellipse(x + 0.2, y + 0.3, r, r * 0.8, rgb("183C3C"), 110)
        p.ellipse(x, y, r, r * 0.8, rgb("4E9A48"), 150)
        p.ellipse(x - r * 0.15, y - r * 0.15, r * 0.7, r * 0.55, rgb("6CB45A"), 154)
        p.poly([(x, y), (x + r * 1.1, y - r * 0.5), (x + r * 1.1, y + r * 0.1)], rgb("2C6C6C"), 120)
    p.ellipse(44.0, 38.4, 0.5, 0.5, rgb("F4EEE0"), 170)
    return p


def paint_bricks():
    """Кладка стен и башен: тёсаные блоки со сдвигом, светлые швы раствора, сколы, мох в швах."""
    p = rm.Paint(447)
    stone = np.array(MASONRY, dtype=np.float32)
    mid, fine = p.tile_noise(16, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.86, 1.14, (8, 4)).astype(np.float32)
    warm = p.rng.uniform(0.0, 1.0, (8, 4)).astype(np.float32)
    tint = np.array(rgb("B0A088"), dtype=np.float32)
    mortar = np.array(rgb("C4BCA8"), dtype=np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        ex = np.minimum(shifted % 16.0, 16.0 - shifted % 16.0)
        ey = np.minimum(gy % 8.0, 8.0 - gy % 8.0)
        edge = np.minimum(ex, ey)
        seam = np.clip(edge / 0.5, 0.0, 1.0)
        lit = 1.0 + 0.1 * np.clip(1.0 - (gy % 8.0) / 2.2, 0.0, 1.0)
        blend = warm[row, col][..., None] * 0.5
        block = stone[None, None, :] * (1.0 - blend) + tint[None, None, :] * blend
        tone = tones[row, col] * (1.0 + 0.09 * mid + 0.05 * fine) * lit
        color = block * tone[..., None]
        color = color * seam[..., None] + mortar[None, None, :] * 0.82 * (1.0 - seam[..., None])
        return color, 128.0 + mid * 16.0 + fine * 8.0 - (1.0 - seam) * 78.0 + (tones[row, col] - 1.0) * 60.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(MASONRY, 0.62), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(MASONRY, 1.3), 0.07)
    p.wrinkles(2, 2, 60, 60, 9, 3.0, 0.9, 0.64, 60)
    for _ in range(10):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 2.5, y - 1.2, 5, 2.4, 40, rgb("5E8A3E"), 0.17)
    return p


def paint_cliff():
    """Обрыв холма: слоистый светлый мел и известняк, пласты волной, трещины, пучки травы на уступах."""
    p = rm.Paint(449)
    stone = np.array(rgb("8C826E"), dtype=np.float32)
    warm = np.array(CHALK, dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(10, 3), p.tile_noise(28, 2)

    def fn(gx, gy):
        phase = gy / 64.0 * 5.0 + low * 0.55 + mid * 0.16
        band = phase - np.floor(phase)
        ledge = np.clip(band / 0.16, 0.0, 1.0) * np.clip((1.0 - band) / 0.5, 0.0, 1.0)
        layer = np.sin(np.floor(phase) * 2.4) * 0.5 + 0.5
        tone = (0.7 + 0.3 * ledge) * (1.0 + 0.12 * mid + 0.07 * fine)
        color = stone[None, None, :] * (1.0 - layer[..., None] * 0.55) + warm[None, None, :] * (layer[..., None] * 0.55)
        return color * tone[..., None], 128.0 + ledge * 62.0 - 40.0 + mid * 26.0 + fine * 12.0
    p.field(fn)
    p.wrinkles(1, 1, 62, 62, 14, 8.0, 1.2, 0.6, 70)
    p.speckle(0.5, 0.5, 63, 63, 700, rgb("544C3E"), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 450, rgb("D8D0BC"), 0.08)
    for _ in range(8):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 3.0, y - 1.0, 6, 2.0, 50, rgb("5E8A3E"), 0.16)
    return p


def paint_grass():
    """Луговая трава: пятна светлее и темнее, травинки, листья клевера и редкие розовые цветки."""
    gd, gl = mul(MEADOW, 0.72), mul(MEADOW, 1.3)
    p = rm._ground(451, MEADOW, 0.12, 0.08, 20.0)
    for _ in range(1500):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.6, 63)
        lean = p.rng.uniform(-0.3, 0.3)
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.6, 1.3))], gd if p.rng.random() < 0.5 else gl, 0.12, 150)
    # Клевер: три круглых листика.
    for _ in range(16):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        for ox, oy in ((-0.35, 0.2), (0.35, 0.2), (0.0, -0.3)):
            p.ellipse(x + ox, y + oy, 0.34, 0.3, rgb("7CB850"), 160)
        p.ellipse(x, y, 0.12, 0.12, rgb("A8D878"), 170)
    # Розы: алый цветок с тёмной серединой.
    for _ in range(9):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        p.ellipse(x, y, 0.5, 0.45, rgb("C8344A"), 176)
        p.ellipse(x, y, 0.26, 0.24, rgb("E8687A"), 180)
        p.ellipse(x, y, 0.1, 0.1, rgb("7A1830"), 176)
    return p


def paint_road():
    """Брусчатка: тёсаные камни разной формы, тёмные швы с землёй, у камней свой тон, потёртость."""
    p = rm.Paint(453)
    base = np.array(COBBLE, dtype=np.float32)
    d1, d2, ident = _cells(p, 7, 0.34)
    mid, fine = p.tile_noise(14, 3), p.tile_noise(46, 2)
    tones = p.rng.uniform(0.84, 1.16, 49).astype(np.float32)
    warm = p.rng.uniform(0.0, 1.0, 49).astype(np.float32)
    tint = np.array(rgb("A09478"), dtype=np.float32)
    gapc = np.array(rgb("4A4236"), dtype=np.float32)

    def fn(gx, gy):
        gap = d2 - d1
        seam = np.clip(gap / 0.12, 0.0, 1.0)
        dome = np.clip(gap / 0.5, 0.0, 1.0)
        mixk = warm[ident][..., None] * 0.55
        block = base[None, None, :] * (1.0 - mixk) + tint[None, None, :] * mixk
        tone = tones[ident] * (1.0 + 0.08 * mid + 0.05 * fine) * (0.86 + 0.16 * dome)
        color = block * tone[..., None]
        color = color * seam[..., None] + gapc[None, None, :] * (1.0 - seam[..., None])
        return color, 128.0 - (1.0 - seam) * 78.0 + dome * 22.0 + mid * 8.0 + fine * 6.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 1200, mul(COBBLE, 0.7), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(COBBLE, 1.22), 0.07)
    p.stains(3, 3, 58, 58, 8, 2.6, 0.9)
    return p


def paint_mud():
    """Грязь колеи: мокрая тёмная земля, две колеи от колёс, лужи с отблеском, солома и комья.
    Заметно темнее брусчатки."""
    p = rm._ground(455, MIRE, 0.16, 0.12, 30.0)
    for x in (18.0, 46.0):
        p.fold([(x, -1), (x, 65)], 3.4, 0.62, 70)
        p.line([(x + 2.2, 0), (x + 2.2, 64)], mul(MIRE, 1.3), 0.5, 150)
    for _ in range(9):
        x, y = p.rng.uniform(8, 56), p.rng.uniform(8, 56)
        rx, ry = p.rng.uniform(2.5, 5.2), p.rng.uniform(1.4, 2.8)
        p.ellipse(x, y, rx, ry, rgb("2E241A"), 70)
        p.ellipse(x + rx * 0.1, y + ry * 0.1, rx * 0.8, ry * 0.7, rgb("4A4A4A"), 72)
        p.ellipse(x - rx * 0.25, y - ry * 0.3, rx * 0.35, ry * 0.18, rgb("8A98A0"), 76)
    for _ in range(40):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.line([(x, y), (x + p.rng.uniform(0.6, 1.4), y + p.rng.uniform(-0.3, 0.3))], rgb("A88C4C"), 0.12, 150)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(MIRE, 1.4), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(MIRE, 0.55), 0.1)
    return p


def paint_sail():
    """Знамя: багровая саржа, золотая кайма у шва и золотой герб (ромб с крестом) в каждой
    половине, строчка и складки. Стыкуется по краям."""
    p = rm._ground(457, BANNER, 0.06, 0.04, 10.0)
    p.twill(0, 0, 64, 64, 0.42, 0.08)
    # Золотая кайма: вертикальные полосы по швам (на краю плитки она складывается в одну).
    for x in (0.0, 32.0):
        p.rect(x - 1.4 if x else 0.0, 0.0, 2.8 if x else 1.4, 64.0, GOLD, 150)
        p.fold([(x + 1.6, 0), (x + 1.6, 64)], 0.3, 0.8, 40)
    p.rect(62.6, 0.0, 1.4, 64.0, GOLD, 150)
    p.fold([(62.4, 0), (62.4, 64)], 0.3, 0.8, 40)
    for cx in (16.0, 48.0):
        cy = 32.0
        p.poly([(cx, cy - 8.0), (cx + 6.0, cy), (cx, cy + 8.0), (cx - 6.0, cy)], GOLD, 160)
        p.poly([(cx, cy - 6.2), (cx + 4.4, cy), (cx, cy + 6.2), (cx - 4.4, cy)], mul(BANNER, 0.84), 140)
        p.rect(cx - 0.6, cy - 4.6, 1.2, 9.2, GOLD, 164)
        p.rect(cx - 3.0, cy - 0.6, 6.0, 1.2, GOLD, 164)
        p.stitch([(cx, cy - 8.8), (cx + 6.8, cy), (cx, cy + 8.8), (cx - 6.8, cy), (cx, cy - 8.8)], mul(GOLD, 0.7), 0.14, 0.7)
    for y in (14.0, 52.0):
        p.fold([(0, y), (64, y)], 0.4, 0.86, 26)
    p.wrinkles(2, 2, 60, 60, 12, 3.0, 0.4, 0.84, 24)
    p.stains(2, 2, 60, 60, 8, 2.4, 0.9)
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
