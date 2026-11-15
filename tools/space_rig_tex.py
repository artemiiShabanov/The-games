#!/usr/bin/env python3
"""Текстуры уровня «Космоса» для «продвинутых» (#136): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Космос у
«продвинутых» это дневная сторона луны: светлая земля под чёрным небом, цвет спокойный. Плитки
стыкуются по краям: поля считаются на периодическом шуме, отдельные детали не подходят к краю.
Набор подключает `rig_models.py` через `space_rig`.

    python3 tools/space_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402

rgb, mul, UNITS = rm.rgb, rm.mul, rm.UNITS

REG = rgb("C2C4CA")
METAL = rgb("8A92A4")
BASALT = rgb("585C6C")
MOSS = rgb("6E4AA8")
SLAB = rgb("686E7E")
DUST = rgb("3C3A48")
FOIL = rgb("C8A04C")


def _crater(p, x, y, r, base):
    """Кратер: светлый вал, тёмная чаша со светом на дальней от солнца стенке."""
    p.ellipse(x, y, r * 1.22, r * 1.1, mul(base, 1.1), 168)
    p.ellipse(x + r * 0.05, y + r * 0.05, r, r * 0.9, mul(base, 0.8), 84)
    p.ellipse(x + r * 0.2, y + r * 0.22, r * 0.72, r * 0.62, mul(base, 0.93), 96)


def paint_sand():
    """Реголит: светлая пыль с плавными пятнами, зерно, мелкие кратеры и камешки."""
    p = rm.Paint(401)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(40, 2)

    def fn(gx, gy):
        tone = 1.0 + 0.07 * low + 0.05 * mid + 0.03 * fine
        return np.array(REG, dtype=np.float32)[None, None, :] * tone[..., None], 128.0 + low * 12.0 + mid * 16.0 + fine * 10.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2600, mul(REG, 0.84), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 1600, mul(REG, 1.1), 0.06)
    for r in (3.0, 2.2, 1.7, 1.3, 1.3, 1.0, 1.0, 0.8, 0.8, 0.7, 0.6, 0.6, 0.5, 0.5):
        _crater(p, p.rng.uniform(5, 59), p.rng.uniform(5, 59), r, REG)
    for _ in range(22):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.22, 0.55)
        p.ellipse(x + 0.14, y + 0.18, r, r * 0.8, mul(REG, 0.68), 110)
        p.ellipse(x, y, r, r * 0.8, rgb("7C7E8C") if p.rng.random() < 0.6 else rgb("DADCE4"), 190)
    return p


def paint_planks():
    """Настил станции: панели 32×16 вразбежку, швы с фаской, рифление ромбом, заклёпки, потёртости."""
    p = rm.Paint(403)
    base = np.array(METAL, dtype=np.float32)
    mid, fine = p.tile_noise(12, 3), p.tile_noise(48, 2)
    tones = p.rng.uniform(0.9, 1.1, (4, 2)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 16.0).astype(np.int32), 0, 3)
        shifted = (gx + (row % 2) * 16.0) % 64.0
        col = np.clip((shifted / 32.0).astype(np.int32), 0, 1)
        ex = np.minimum(shifted % 32.0, 32.0 - shifted % 32.0)
        ey = np.minimum(gy % 16.0, 16.0 - gy % 16.0)
        edge = np.minimum(ex, ey)
        seam = np.clip(edge / 0.4, 0.0, 1.0)
        bevel = np.clip((edge - 0.4) / 0.5, 0.0, 1.0)
        # Рифление: ромбы только в середине панели.
        inner = np.clip((edge - 2.2) / 0.6, 0.0, 1.0)
        tread = np.maximum(np.sin((gx + gy) * np.pi / 1.6), 0.0) * np.maximum(np.sin((gx - gy) * np.pi / 1.6), 0.0) * inner
        # Шлифовка вдоль панели.
        brushed = 1.0 + 0.03 * np.sin(gy * 9.0 + mid * 3.0) + 0.03 * fine
        tone = tones[row, col] * brushed * (0.4 + 0.6 * seam) * (1.0 + 0.1 * (1.0 - bevel) * seam) * (1.0 + 0.1 * tread + 0.05 * mid)
        return base[None, None, :] * tone[..., None], 128.0 - (1.0 - seam) * 80.0 + tread * 44.0 + fine * 5.0
    p.field(fn)
    for row in range(4):
        for col in range(2):
            x0 = (col * 32.0 - (row % 2) * 16.0) % 64.0
            for dx, dy in ((1.6, 1.6), (30.4, 1.6), (1.6, 14.4), (30.4, 14.4)):
                x, y = (x0 + dx) % 64.0, row * 16.0 + dy
                if 0.6 < x < 63.4:
                    p.ellipse(x, y, 0.36, 0.36, mul(METAL, 0.62), 176)
                    p.ellipse(x - 0.1, y - 0.1, 0.13, 0.13, mul(METAL, 1.28))
    # Полоса разметки и решётка вентиляции.
    for i in range(6):
        p.poly([(38 + i * 2.0, 53.2), (39 + i * 2.0, 53.2), (38.4 + i * 2.0, 56.0), (37.4 + i * 2.0, 56.0)], rgb("D0703C"))
    for j in range(5):
        p.rect(8.0, 20.0 + j * 1.6, 10.0, 0.7, mul(METAL, 0.34), 60)
    p.stains(2, 2, 60, 60, 12, 2.4, 0.9)
    return p


def paint_water():
    """Плазма: плавные волны от фиолетовой глубины к бирюзовым гребням."""
    p = rm.Paint(405)
    deep, mid, crest = (np.array(rgb(c), dtype=np.float32) for c in ("2A1660", "6A38BC", "9CEAF4"))
    noise = p.tile_noise(8, 3)

    def fn(gx, gy):
        w = np.sin((gx + 6.0 * np.sin(gy * np.pi / 8.0)) * np.pi / 16.0) + np.sin((gy * 2.0 + gx) * np.pi / 16.0) + 0.5 * noise
        t = rm._smooth_np(np.clip((w + 1.2) / 2.6, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 1.8) / 0.45, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - top[..., None]) + crest[None, None, :] * top[..., None]
        return color, 128.0 + w * 34.0
    p.field(fn)
    return p


def paint_bricks():
    """Базальтовая кладка (борта, стены): блоки со сдвигом, тёмные швы, сколы, фиолетовый лишайник."""
    p = rm.Paint(427)
    stone = np.array(BASALT, dtype=np.float32)
    mid, fine = p.tile_noise(16, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.84, 1.16, (8, 4)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        ex = np.minimum(shifted % 16.0, 16.0 - shifted % 16.0)
        ey = np.minimum(gy % 8.0, 8.0 - gy % 8.0)
        seam = np.clip(np.minimum(ex, ey) / 0.45, 0.0, 1.0)
        # Свет сверху: верхняя кромка блока светлее.
        lit = 1.0 + 0.08 * np.clip(1.0 - (gy % 8.0) / 2.0, 0.0, 1.0)
        tone = tones[row, col] * (1.0 + 0.1 * mid + 0.05 * fine) * (0.4 + 0.6 * seam) * lit
        return stone[None, None, :] * tone[..., None], 128.0 + mid * 18.0 + fine * 8.0 - (1.0 - seam) * 80.0 + (tones[row, col] - 1.0) * 60.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(BASALT, 0.6), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(BASALT, 1.45), 0.07)
    p.wrinkles(2, 2, 60, 60, 9, 3.0, 0.9, 0.62, 60)
    for _ in range(9):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 2.5, y - 1.2, 5, 2.4, 40, rgb("7A56B0"), 0.17)
    return p


def paint_cliff():
    """Обрыв: слоистый тёмный базальт, пласты идут волной, трещины, редкий лишайник."""
    p = rm.Paint(431)
    stone = np.array(rgb("4A4C5A"), dtype=np.float32)
    cool = np.array(rgb("66607A"), dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(10, 3), p.tile_noise(28, 2)

    def fn(gx, gy):
        phase = gy / 64.0 * 5.0 + low * 0.55 + mid * 0.16
        band = phase - np.floor(phase)
        ledge = np.clip(band / 0.16, 0.0, 1.0) * np.clip((1.0 - band) / 0.5, 0.0, 1.0)
        layer = np.sin(np.floor(phase) * 2.4) * 0.5 + 0.5
        tone = (0.68 + 0.32 * ledge) * (1.0 + 0.13 * mid + 0.07 * fine)
        color = stone[None, None, :] * (1.0 - layer[..., None] * 0.55) + cool[None, None, :] * (layer[..., None] * 0.55)
        return color * tone[..., None], 128.0 + ledge * 62.0 - 40.0 + mid * 26.0 + fine * 12.0
    p.field(fn)
    p.wrinkles(1, 1, 62, 62, 14, 8.0, 1.2, 0.58, 70)
    p.speckle(0.5, 0.5, 63, 63, 700, rgb("2C2C38"), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 450, rgb("8E8CA0"), 0.08)
    for _ in range(6):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 3.0, y - 1.0, 6, 2.0, 44, rgb("7A56B0"), 0.16)
    return p


def paint_grass():
    """Фиолетовый мох: пятна светлее и темнее, короткие ворсинки, светящиеся споры."""
    md, ml = mul(MOSS, 0.7), mul(MOSS, 1.32)
    p = rm._ground(429, MOSS, 0.13, 0.09, 20.0)
    for _ in range(1500):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.4, 63)
        lean = p.rng.uniform(-0.3, 0.3)
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.4, 1.0))], md if p.rng.random() < 0.5 else ml, 0.13, 150)
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.ellipse(x, y, 0.42, 0.42, rgb("4C8CB0"), 150)
        p.ellipse(x, y, 0.24, 0.24, rgb("A8F0F8"), 176)
    return p


def paint_road():
    """Трасса из плит: поперечные швы, укатанные следы колёс, пунктир по оси, потёртости."""
    p = rm._ground(433, SLAB, 0.07, 0.05, 12.0)
    for y in (0.0, 32.0, 64.0):
        p.fold([(-1, y), (65, y)], 0.5, 0.52, 80)
    for x in (0.0, 64.0):
        p.fold([(x, -1), (x, 65)], 0.5, 0.6, 70)
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.6, 0.86, 24)
    for y in (6.0, 38.0):
        p.rect(31.3, y, 1.4, 12.0, rgb("C4CCD4"), 138)
    p.speckle(0.5, 0.5, 63, 63, 1400, mul(SLAB, 0.76), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(SLAB, 1.18), 0.07)
    p.wrinkles(3, 3, 58, 58, 7, 4.0, 1.0, 0.7, 50)
    p.stains(3, 3, 58, 58, 10, 2.6, 0.88)
    return p


def paint_mud():
    """Тёмная пыль: мелкие барханчики, ямы темнее, светлые крупинки. Заметно темнее трассы."""
    p = rm.Paint(435)
    base = np.array(DUST, dtype=np.float32)
    low, mid = p.tile_noise(4, 3), p.tile_noise(16, 3)

    def fn(gx, gy):
        dune = np.sin(2 * np.pi * (gy * 6.0 / UNITS + 0.4 * np.sin(2 * np.pi * gx * 2.0 / UNITS) + 0.3 * low))
        tone = 1.0 + 0.14 * dune + 0.14 * low + 0.1 * mid
        return base[None, None, :] * tone[..., None], 128.0 + dune * 30.0 + mid * 18.0
    p.field(fn)
    for _ in range(10):
        x, y = p.rng.uniform(8, 56), p.rng.uniform(8, 56)
        rx, ry = p.rng.uniform(2.5, 5.0), p.rng.uniform(1.4, 2.8)
        p.ellipse(x, y, rx, ry, mul(DUST, 0.8), 92)
        p.ellipse(x + rx * 0.1, y + ry * 0.2, rx * 0.7, ry * 0.6, mul(DUST, 0.9), 100)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(DUST, 1.5), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(DUST, 0.55), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 80, rgb("8C7CB8"), 0.1)
    return p


def paint_sail():
    """Золотистая фольга: стёганая сетка сгибов, мятые складки, блики, шов по краю полотнища."""
    p = rm._ground(437, FOIL, 0.07, 0.06, 14.0)
    for k in range(-8, 9):
        p.fold([(k * 8.0, 0.0), (k * 8.0 + 64.0, 64.0)], 0.35, 0.8, 40)
        p.fold([(k * 8.0 + 64.0, 0.0), (k * 8.0, 64.0)], 0.35, 0.8, 40)
    p.wrinkles(1, 1, 62, 62, 40, 3.2, 1.4, 0.84, 30)
    for x in (0.4, 32.0):
        p.fold([(x, 0), (x, 64)], 0.5, 0.7, 50)
    for _ in range(60):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 62)
        p.line([(x, y), (x + p.rng.uniform(-0.8, 0.8), y + p.rng.uniform(-0.8, 0.8))], rgb("F4E4A8"), 0.16, 170)
    p.stains(2, 2, 60, 60, 6, 2.4, 0.92)
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
