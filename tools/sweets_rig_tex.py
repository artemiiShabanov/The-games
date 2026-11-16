#!/usr/bin/env python3
"""Текстуры уровня «Сладостей» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Сладости у
«продвинутых» это карамельная страна в пастели: земля из светлого бисквита с порами и цветной
посыпкой, настил из вафельных листов с клеткой, розовый сироп на месте воды, борта и стены из
долек шоколадной плитки с тиснёным ромбом, обрыв срезом слоёного торта с потёками крема, мятная
глазурь с кокосовой стружкой на месте травы, трасса из молочного шоколада с пунктиром из белой
глазури, тёмная помадка на месте грязи и полосатый фантик на месте полотнища. Плитки стыкуются
по краям: поля считаются на периодическом шуме и периодических решётках, отдельные детали не
подходят к краю. Свойства, на которые рассчитаны демки, те же, что у космоса: панели настила
32×16 вразбежку, блоки кладки 16×8 со сдвигом, колеи дороги на 19 и 45, пунктир по оси, грязь
заметно темнее дороги, вода одним плавным полем без отдельных деталей, швы полотнища на 0.4 и
32. Цвета из палитры основы 16/32 (`sweets16.PALETTE`, тона из `sweets_mesh_chars`): земля
светлая и жёлтая, чтобы пряничный человечек и красные мармеладные мишки читались на ней. Набор
подключает `rig_models.py` через `setting_sets.rig_set`.

    python3 tools/sweets_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import sweets_mesh_chars as smc  # noqa: E402

rgb, mul, mix, UNITS = rm.rgb, rm.mul, rm.mix, rm.UNITS

ICING, ICING_D = smc.ICING, smc.ICING_D
MINT, MINT_D, MINT_L = smc.MINT, smc.MINT_D, smc.MINT_L
PINK, PINK_D, PINK_L = smc.PINK, smc.PINK_D, smc.PINK_L
JELLY = smc.JELLY
CARAMEL, CARAMEL_D, CARAMEL_L = smc.CARAMEL, smc.CARAMEL_D, smc.CARAMEL_L
CHOCO, CHOCO_D, CHOCO_L = smc.CHOCO, smc.CHOCO_D, smc.CHOCO_L

SPONGE = mix(CARAMEL, CARAMEL_L, 0.45)      # бисквит: светлее карамели
WAFER = mix(CARAMEL, CARAMEL_D, 0.55)       # вафля: подрумяненная
GLAZE = mix(MINT, MINT_D, 0.25)             # мятная глазурь
ROAD = mix(CHOCO, CHOCO_L, 0.45)            # молочный шоколад трассы
FUDGE = mul(CHOCO_D, 0.92)                  # тёмная помадка
SPRINKLES = (PINK, MINT_D, JELLY, ICING, rgb("8E6CD0"))


def _arr(color):
    return np.array(color, dtype=np.float32)[None, None, :]


def _sprinkle(p, x, y, color, length=0.9, width=0.3):
    """Палочка посыпки: короткий валик со светлой спинкой и тенью под ним."""
    a = p.rng.uniform(0.0, np.pi)
    dx, dy = np.cos(a) * length / 2.0, np.sin(a) * length / 2.0
    p.line([(x - dx + 0.1, y - dy + 0.16), (x + dx + 0.1, y + dy + 0.16)], mul(SPONGE, 0.7), width, 118)
    p.line([(x - dx, y - dy), (x + dx, y + dy)], color, width, 190)
    p.line([(x - dx * 0.5, y - dy * 0.5 - 0.06), (x + dx * 0.4, y + dy * 0.4 - 0.06)], mix(color, ICING, 0.55), width * 0.4)


def paint_sand():
    """Бисквит: светлый мякиш с подрумяненными пятнами, поры, крошки, сахарная пудра и посыпка."""
    p = rm.Paint(601)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(14, 3), p.tile_noise(44, 2)
    toast = _arr(mix(SPONGE, CARAMEL_D, 0.5))

    def fn(gx, gy):
        tone = 1.0 + 0.05 * mid + 0.035 * fine
        t = np.clip(low * 0.5 + 0.2, 0.0, 0.6)[..., None]
        return (_arr(SPONGE) * (1.0 - t) + toast * t) * tone[..., None], 128.0 + low * 10.0 + mid * 14.0 + fine * 12.0
    p.field(fn)
    # Поры мякиша: тёмная ямка со светлым нижним краем.
    for _ in range(420):
        x, y = p.rng.uniform(1.5, 62.5), p.rng.uniform(1.5, 62.5)
        r = p.rng.uniform(0.14, 0.42)
        p.ellipse(x, y + r * 0.3, r * 1.1, r * 0.8, mul(SPONGE, 1.08), 138)
        p.ellipse(x, y, r, r * 0.72, mul(CARAMEL_D, 0.86), 78)
    p.speckle(0.5, 0.5, 63, 63, 1800, mul(SPONGE, 0.86), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 1500, ICING, 0.06)
    # Крошки: комочки с тенью.
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.3, 0.62)
        p.ellipse(x + 0.14, y + 0.2, r, r * 0.8, mul(SPONGE, 0.68), 112)
        p.ellipse(x, y, r, r * 0.8, mix(SPONGE, CARAMEL_D, 0.7) if p.rng.random() < 0.6 else CARAMEL_L, 186)
    for i in range(34):
        _sprinkle(p, p.rng.uniform(3, 61), p.rng.uniform(3, 61), SPRINKLES[i % len(SPRINKLES)])
    return p


def paint_planks():
    """Вафельный настил: листы 32×16 вразбежку, клетка с ямками через 4, швы, крем в ямках."""
    p = rm.Paint(603)
    base = _arr(WAFER)
    mid, fine = p.tile_noise(10, 3), p.tile_noise(48, 2)
    tones = p.rng.uniform(0.9, 1.1, (4, 2)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 16.0).astype(np.int32), 0, 3)
        shifted = (gx + (row % 2) * 16.0) % 64.0
        col = np.clip((shifted / 32.0).astype(np.int32), 0, 1)
        ex = np.minimum(shifted % 32.0, 32.0 - shifted % 32.0)
        ey = np.minimum(gy % 16.0, 16.0 - gy % 16.0)
        seam = np.clip(np.minimum(ex, ey) / 0.38, 0.0, 1.0)
        # Клетка: рёбра по кратным четырём, между ними ямка со скошенными стенками.
        cx, cy = gx % 4.0, gy % 4.0
        dx, dy = np.minimum(cx, 4.0 - cx), np.minimum(cy, 4.0 - cy)
        pit = rm._smooth_np(np.clip((np.minimum(dx, dy) - 0.55) / 0.75, 0.0, 1.0))
        # Свет сверху слева: верхняя и левая стенки ямки в тени, нижняя и правая светлее.
        wall = (1.0 - pit) * np.clip((np.minimum(dx, dy) - 0.45) / 0.3, 0.0, 1.0)
        dark_side = ((cy < 2.0) & (dy <= dx)) | ((cx < 2.0) & (dx < dy))
        shade = np.where(dark_side, 0.8, 1.14)
        tone = tones[row, col] * (1.0 + 0.07 * mid + 0.04 * fine) * (1.0 - 0.17 * pit) * (1.0 + (shade - 1.0) * wall)
        tone = tone * (0.42 + 0.58 * seam)
        return base * tone[..., None], 128.0 + 34.0 - pit * 62.0 - (1.0 - seam) * 70.0 + fine * 5.0
    p.field(fn)
    # Крем, выдавленный в ямки: розовая дорожка и несколько шоколадных клеток.
    for i in range(7):
        x, y = 34.0 + i * 4.0, 50.0
        p.rect(x - 1.2, y - 1.2, 2.4, 2.4, PINK, 150)
        p.ellipse(x, y, 1.05, 1.05, mix(PINK, PINK_L, 0.5), 168)
        p.ellipse(x - 0.3, y - 0.35, 0.34, 0.26, ICING, 176)
    for cx, cy in ((10.0, 22.0), (14.0, 22.0), (10.0, 26.0), (50.0, 10.0), (22.0, 42.0)):
        p.rect(cx - 1.2, cy - 1.2, 2.4, 2.4, CHOCO, 150)
        p.ellipse(cx, cy, 1.0, 1.0, CHOCO_L, 164)
        p.ellipse(cx - 0.3, cy - 0.35, 0.3, 0.22, mix(CHOCO_L, ICING, 0.6), 172)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(WAFER, 0.8), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 500, CARAMEL_L, 0.06)
    p.stains(2, 2, 60, 60, 10, 2.6, 0.9)
    return p


def paint_water():
    """Розовый сироп: густые плавные волны от малиновой глубины к светлым бликам."""
    p = rm.Paint(605)
    deep, mid, crest = (_arr(c)[0, 0] for c in (rgb("A22E68"), rgb("F0709E"), rgb("FFE2EA")))
    noise = p.tile_noise(6, 3)

    def fn(gx, gy):
        w = np.sin((gy + 7.0 * np.sin(gx * np.pi / 16.0)) * np.pi / 8.0) + 0.9 * np.sin((gx + gy) * np.pi / 16.0) + 0.5 * noise
        t = rm._smooth_np(np.clip((w + 1.3) / 2.6, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 1.45) / 0.4, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - top[..., None]) + crest[None, None, :] * top[..., None]
        return color, 128.0 + w * 30.0
    p.field(fn)
    return p


def paint_bricks():
    """Плитка шоколада (борта, стены): дольки 16×8 со сдвигом, фаска, тиснёный ромб, сахарная крошка."""
    p = rm.Paint(627)
    choco = _arr(mix(CHOCO, CHOCO_L, 0.2))
    mid, fine = p.tile_noise(16, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.86, 1.12, (8, 4)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        lx, ly = shifted % 16.0, gy % 8.0
        ex, ey = np.minimum(lx, 16.0 - lx), np.minimum(ly, 8.0 - ly)
        edge = np.minimum(ex, ey)
        seam = np.clip(edge / 0.4, 0.0, 1.0)
        # Фаска дольки: скос шириной 1.3, сверху и слева свет, снизу и справа тень.
        slope = 1.0 - np.clip((edge - 0.4) / 1.3, 0.0, 1.0)
        top_left = ((ly < 4.0) & (ey <= ex)) | ((lx < 8.0) & (ex < ey))
        bevel = np.where(top_left, 1.22, 0.74)
        # Тиснёный ромб посреди дольки: выпуклая рамка.
        dd = np.abs(lx - 8.0) / 4.6 + np.abs(ly - 4.0) / 2.1
        ring = np.clip(1.0 - np.abs(dd - 0.86) / 0.14, 0.0, 1.0)
        ring_lit = np.where((ly - 4.0) + (lx - 8.0) * 0.4 < 0.0, 1.2, 0.84)
        tone = tones[row, col] * (1.0 + 0.06 * mid + 0.03 * fine) * (1.0 + (bevel - 1.0) * slope * seam)
        tone = tone * (1.0 + (ring_lit - 1.0) * ring) * (0.36 + 0.64 * seam)
        height = 128.0 + 30.0 - slope * 44.0 - (1.0 - seam) * 60.0 + ring * 26.0 + fine * 4.0 + (tones[row, col] - 1.0) * 40.0
        return choco * tone[..., None], height
    p.field(fn)
    # Блик глянца на каждой дольке: короткий мазок у верхнего левого угла плато.
    for row in range(8):
        for col in range(4):
            x0 = (col * 16.0 - (row % 2) * 8.0) % 64.0
            if x0 + 6.0 < 63.5:
                p.line([(x0 + 2.6, row * 8.0 + 2.4), (x0 + 5.0, row * 8.0 + 2.2)], mix(CHOCO_L, ICING, 0.35), 0.22)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(CHOCO_D, 0.9), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 260, CHOCO_L, 0.06)
    # Сахарная крошка и розовая посыпка кучками (на месте лишайника).
    for i in range(9):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 2.5, y - 1.2, 5, 2.4, 34, ICING if i % 3 else PINK, 0.15)
    return p


def paint_cliff():
    """Обрыв: срез слоёного торта. Бисквит, джем, крем с потёками, шоколадный корж; слои идут волной."""
    p = rm.Paint(631)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(12, 3), p.tile_noise(36, 2)
    drips = p.tile_noise(16, 2)
    sponge, jam, cream, cake = _arr(mix(SPONGE, CARAMEL, 0.5)), _arr(mix(JELLY, PINK_D, 0.35)), _arr(ICING), _arr(mix(CHOCO, CHOCO_D, 0.35))

    def fn(gx, gy):
        phase = gy / 64.0 * 4.0 + low * 0.2 + mid * 0.05
        index = np.floor(phase).astype(np.int32)
        band = phase - index
        # У каждого слоя свой ряд потёков: строка шума по номеру слоя.
        cols = np.clip((gx * p.k).astype(np.int32), 0, p.n - 1)
        drip = np.clip(drips[(index % 4) * 190 + 40, cols] * 1.6, 0.0, 1.0) ** 2
        cream_end = 0.7 + 0.24 * drip
        k_jam = np.clip((band - 0.42) / 0.02, 0.0, 1.0)[..., None]
        k_cream = np.clip((band - 0.5) / 0.02, 0.0, 1.0)[..., None]
        k_cake = np.clip((band - cream_end) / 0.02, 0.0, 1.0)
        pores = 1.0 + 0.1 * mid + 0.09 * fine
        color = sponge * pores[..., None]
        color = color * (1.0 - k_jam) + jam * (1.0 + 0.08 * fine[..., None]) * k_jam
        # Крем: валик, светлый сверху, с тенью у нижней кромки.
        roll = np.clip((cream_end - band) / 0.07, 0.0, 1.0)
        color = color * (1.0 - k_cream) + cream * (0.86 + 0.14 * roll)[..., None] * k_cream
        under = 1.0 - 0.3 * np.clip(1.0 - (band - cream_end) / 0.06, 0.0, 1.0)
        color = color * (1.0 - k_cake[..., None]) + cake * (pores * under)[..., None] * k_cake[..., None]
        # Тень под шоколадным коржом на бисквите следующего слоя.
        color = color * (1.0 - 0.2 * np.clip(1.0 - band / 0.05, 0.0, 1.0))[..., None]
        in_cream = k_cream[..., 0] * (1.0 - k_cake)
        height = 128.0 - 14.0 + mid * 14.0 + fine * 14.0 + in_cream * (26.0 + roll * 26.0) + k_jam[..., 0] * (1.0 - k_cream[..., 0]) * 12.0
        return color, height
    p.field(fn)
    # Поры бисквита и коржа, крошки.
    p.speckle(0.5, 0.5, 63, 63, 520, mul(CARAMEL_D, 0.8), 0.11)
    p.speckle(0.5, 0.5, 63, 63, 380, CARAMEL_L, 0.08)
    return p


def paint_grass():
    """Мятная глазурь: пятна светлее и темнее, кокосовая стружка штрихами, сахарные бусины."""
    gd, gl = mix(GLAZE, MINT_D, 0.6), mix(MINT_L, ICING, 0.3)
    p = rm._ground(629, GLAZE, 0.1, 0.07, 20.0)
    for _ in range(1500):
        x, y = p.rng.uniform(1.2, 62.8), p.rng.uniform(1.2, 62.8)
        a = p.rng.uniform(0.0, np.pi)
        ln = p.rng.uniform(0.3, 0.75)
        p.line([(x - np.cos(a) * ln, y - np.sin(a) * ln), (x + np.cos(a) * ln, y + np.sin(a) * ln)],
               gd if p.rng.random() < 0.42 else gl, 0.13, 150)
    for i in range(28):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        c = (PINK, ICING, CARAMEL, PINK_L)[i % 4]
        p.ellipse(x + 0.12, y + 0.16, 0.44, 0.4, mix(GLAZE, MINT_D, 0.8), 120)
        p.ellipse(x, y, 0.42, 0.42, c, 186)
        p.ellipse(x - 0.12, y - 0.14, 0.15, 0.13, mix(c, ICING, 0.7), 196)
    return p


def paint_road():
    """Трасса из молочного шоколада: швы долек, укатанные следы колёс, пунктир из глазури по оси."""
    p = rm._ground(633, ROAD, 0.06, 0.05, 12.0)
    for y in (0.0, 32.0, 64.0):
        p.fold([(-1, y), (65, y)], 0.6, 0.55, 80)
    for x in (0.0, 64.0):
        p.fold([(x, -1), (x, 65)], 0.6, 0.6, 70)
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.6, 0.84, 24)
    # Пунктир выдавлен из кондитерского мешка: валик со скруглёнными концами и светлой спинкой.
    for y in (6.0, 38.0):
        p.line([(32.1, y + 0.9), (32.1, y + 11.5)], mul(ROAD, 0.7), 1.5, 116)
        p.line([(32.0, y + 0.7), (32.0, y + 11.3)], ICING_D, 1.4, 160)
        p.ellipse(32.0, y + 0.7, 0.7, 0.7, ICING_D, 160)
        p.ellipse(32.0, y + 11.3, 0.7, 0.7, ICING_D, 160)
        p.line([(31.8, y + 0.8), (31.8, y + 11.2)], ICING, 0.7, 176)
    p.speckle(0.5, 0.5, 63, 63, 1300, mul(ROAD, 0.78), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(ROAD, 1.18), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 120, CARAMEL, 0.09)
    p.wrinkles(3, 3, 58, 58, 7, 4.0, 1.0, 0.72, 50)
    p.stains(3, 3, 58, 58, 10, 2.6, 0.9)
    return p


def paint_mud():
    """Тёмная помадка: вязкие завитки, лужицы с глянцем, карамельные крошки. Заметно темнее трассы."""
    p = rm.Paint(635)
    base = _arr(FUDGE)
    low, mid = p.tile_noise(4, 3), p.tile_noise(16, 3)

    def fn(gx, gy):
        swirl = np.sin(2 * np.pi * (gy * 5.0 / UNITS + 0.5 * np.sin(2 * np.pi * gx * 2.0 / UNITS + low) + 0.35 * low))
        tone = 1.0 + 0.16 * swirl + 0.12 * low + 0.08 * mid
        return base * tone[..., None], 128.0 + swirl * 30.0 + mid * 14.0
    p.field(fn)
    for _ in range(10):
        x, y = p.rng.uniform(8, 56), p.rng.uniform(8, 56)
        rx, ry = p.rng.uniform(2.4, 4.6), p.rng.uniform(1.3, 2.6)
        p.ellipse(x, y, rx, ry, mul(FUDGE, 0.74), 96)
        p.ellipse(x + rx * 0.08, y + ry * 0.15, rx * 0.74, ry * 0.66, mul(FUDGE, 0.86), 100)
        p.line([(x - rx * 0.5, y - ry * 0.42), (x - rx * 0.05, y - ry * 0.55)], mix(FUDGE, CHOCO_L, 0.8), 0.24)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(FUDGE, 1.45), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(FUDGE, 0.55), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 70, CARAMEL_D, 0.11)
    return p


def paint_sail():
    """Фантик: кремовая бумага в розовую косую полоску с тонкой мятной ниткой, мятые складки, швы."""
    p = rm.Paint(637)
    low, mid = p.tile_noise(4, 3), p.tile_noise(16, 3)
    paper, stripe, thread = _arr(mix(ICING, CARAMEL_L, 0.12)), _arr(mix(PINK, PINK_L, 0.3)), _arr(MINT_D)

    def fn(gx, gy):
        d = (gx + gy) % 16.0
        k_pink = (np.clip((d - 1.0) / 0.25, 0.0, 1.0) * np.clip((7.0 - d) / 0.25, 0.0, 1.0))[..., None]
        k_mint = (np.clip((d - 11.0) / 0.2, 0.0, 1.0) * np.clip((12.0 - d) / 0.2, 0.0, 1.0))[..., None]
        color = paper * (1.0 - k_pink) + stripe * k_pink
        color = color * (1.0 - k_mint) + thread * k_mint
        tone = 1.0 + 0.06 * low + 0.05 * mid
        return color * tone[..., None], 128.0 + low * 14.0 + mid * 9.0
    p.field(fn)
    p.wrinkles(1, 1, 62, 62, 40, 3.2, 1.4, 0.86, 30)
    for x in (0.4, 32.0):
        p.fold([(x, 0), (x, 64)], 0.5, 0.72, 50)
    # Блики вощёной бумаги.
    for _ in range(60):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 62)
        p.line([(x, y), (x + p.rng.uniform(-0.8, 0.8), y + p.rng.uniform(-0.8, 0.8))], rgb("FFFFFF"), 0.16, 170)
    p.stains(2, 2, 60, 60, 6, 2.4, 0.93)
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
