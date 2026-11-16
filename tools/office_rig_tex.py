#!/usr/bin/env python3
"""Текстуры уровня «Офиса» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Офис у
«продвинутых» это опенспейс под ровным светом ламп: серое с яркими стикерами. Земля это серый
ковролин плитками, настил это светлый ламинат, вода налита из кулера (светлая, с сеткой
бликов), стены и борта это тканевые перегородки в алюминиевых рамах, обрыв сложен из стопок
бумаги и папок, трава это зелёный ковёр зоны отдыха с конфетти от дырокола, трасса это плитка
коридора с разметкой жёлтым скотчем, грязь это пролитый кофе (заметно темнее трассы), полотно
это стена жёлтых стикеров. Плитки стыкуются по краям: поля считаются на периодическом шуме и
периодических решётках, отдельные детали не подходят к краю. Цвета из палитры основы 16/32
(`office16.PALETTE`) через `office_mesh_chars`. Набор подключает `rig_models.py` через
`setting_sets.rig_set`.

    python3 tools/office_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
from office_mesh_chars import (AQUA, COFFEE, DARK, GOLD, GOLD_L, GREY, METAL, METAL_L, RED, SEA, SEA_L,  # noqa: E402
                               SKY, WHITE)

rgb, mul, mix, UNITS = rm.rgb, rm.mul, rm.mix, rm.UNITS

CARPET = mix(GREY, METAL, 0.3)       # серый ковролин опенспейса
OAK = rgb("D9B98A")                  # светлый ламинат
GREEN = rgb("4F9C86")                # зелёный ковёр (ковролин основы 16/32)
LINO = mix(METAL, DARK, 0.18)        # плитка коридора
PINK = rgb("F08CA8")                 # розовый стикер


def _arr(c):
    return np.array(c, dtype=np.float32)[None, None, :]


def _confetti(p, count, colors, r0=0.3, r1=0.5):
    """Кружки от дырокола: плоский кружок с тенью снизу."""
    for _ in range(count):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(r0, r1)
        c = colors[int(p.rng.integers(0, len(colors)))]
        p.ellipse(x + 0.1, y + 0.14, r, r, (30, 40, 44), 120)
        p.ellipse(x, y, r, r, c, 150)


def paint_sand():
    """Серый ковролин плитками 32×32: у соседних плиток ворс уложен поперёк, тонкие стыки,
    пёстрые ворсинки, редкие кружки от дырокола и скрепка."""
    p = rm.Paint(601)
    base = _arr(CARPET)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(64, 2)

    def fn(gx, gy):
        cx, cy = (gx / 32.0).astype(np.int32) % 2, (gy / 32.0).astype(np.int32) % 2
        odd = ((cx + cy) % 2).astype(np.float32)
        # Петли ворса: рубчик вдоль или поперёк, в шахматном порядке.
        rib = np.where(odd > 0.5, np.sin(gx * np.pi * 2.0 / 1.0), np.sin(gy * np.pi * 2.0 / 1.0))
        knot = np.where(odd > 0.5, np.sin(gy * np.pi * 2.0 / 0.5), np.sin(gx * np.pi * 2.0 / 0.5))
        ex = np.minimum(gx % 32.0, 32.0 - gx % 32.0)
        ey = np.minimum(gy % 32.0, 32.0 - gy % 32.0)
        seam = np.clip(np.minimum(ex, ey) / 0.3, 0.0, 1.0)
        tone = (1.0 + (odd - 0.5) * 0.07) * (1.0 + 0.06 * rib + 0.025 * knot + 0.05 * low + 0.04 * mid + 0.05 * fine)
        tone = tone * (0.72 + 0.28 * seam)
        return base * tone[..., None], 128.0 + rib * 14.0 + knot * 5.0 + fine * 8.0 + mid * 8.0 - (1.0 - seam) * 46.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2200, mul(CARPET, 0.76), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 1500, mul(CARPET, 1.14), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 380, SEA_L, 0.07)
    p.speckle(0.5, 0.5, 63, 63, 220, GREEN, 0.07)
    p.stains(4, 4, 56, 56, 7, 2.6, 0.93)
    _confetti(p, 16, [WHITE, WHITE, GOLD, PINK], 0.26, 0.42)
    # Скрепка: две вложенные петли проволоки.
    for x, y, s in ((20.0, 45.0, 1.0), (47.0, 14.0, -1.0)):
        pts = [(x - 1.5, y - 0.5 * s), (x + 1.3, y - 0.5 * s), (x + 1.7, y), (x + 1.3, y + 0.5 * s), (x - 1.0, y + 0.5 * s),
               (x - 1.3, y + 0.15 * s), (x - 1.0, y - 0.15 * s), (x + 0.8, y - 0.15 * s)]
        p.line([(a + 0.1, b + 0.16) for a, b in pts], mul(CARPET, 0.6), 0.2, 118)
        p.line(pts, rgb("E4E8F0"), 0.16, 168)
    return p


def paint_planks():
    """Светлый ламинат: доски 32×8 со сдвигом по рядам, тонкие фаски, волокна вдоль доски,
    сучки, потёртости от кресел."""
    p = rm.Paint(603)
    base = _arr(OAK)
    warm = _arr(mul(OAK, 0.8))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(12, 3), p.tile_noise(48, 2)
    tones = p.rng.uniform(0.9, 1.08, (8, 2)).astype(np.float32)
    phase = p.rng.uniform(0.0, 6.28, (8, 2)).astype(np.float32)
    shift = np.array([0.0, 12.0, 24.0, 4.0, 16.0, 28.0, 8.0, 20.0], dtype=np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + shift[row]) % 64.0
        col = np.clip((shifted / 32.0).astype(np.int32), 0, 1)
        ex = np.minimum(shifted % 32.0, 32.0 - shifted % 32.0)
        ey = np.minimum(gy % 8.0, 8.0 - gy % 8.0)
        edge = np.minimum(ex, ey)
        seam = np.clip(edge / 0.22, 0.0, 1.0)
        bevel = np.clip((edge - 0.22) / 0.4, 0.0, 1.0)
        # Волокна: линии вдоль доски, которые шум гнёт в плавные «языки».
        grain = np.sin(gy * np.pi * 2.0 / 1.15 + phase[row, col] + mid * 5.0 + low * 3.0)
        vein = np.clip(grain, 0.0, 1.0) ** 3
        tone = tones[row, col] * (1.0 + 0.04 * grain + 0.035 * fine) * (0.5 + 0.5 * seam) * (1.0 + 0.07 * (1.0 - bevel) * seam)
        k = (vein * 0.42)[..., None]
        return (base * (1.0 - k) + warm * k) * tone[..., None], 128.0 - (1.0 - seam) * 70.0 + grain * 4.0 + fine * 3.0
    p.field(fn)
    # Сучки: тёмный глазок в светлом кольце, вытянут вдоль доски.
    for row in range(8):
        if row % 3 == 1:
            continue
        x, y = p.rng.uniform(6, 58), row * 8.0 + p.rng.uniform(2.6, 5.4)
        p.ellipse(x, y, 1.5, 0.75, mul(OAK, 0.84), 126)
        p.ellipse(x, y, 0.9, 0.45, mul(OAK, 0.66), 122)
        p.ellipse(x + 0.1, y, 0.35, 0.2, mul(OAK, 0.46), 118)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(OAK, 0.82), 0.06)
    p.wrinkles(3, 3, 58, 58, 12, 5.0, 0.5, 0.93, 14)
    p.stains(3, 3, 58, 58, 8, 2.6, 0.93)
    return p


def paint_water():
    """Вода из кулера: светлая голубая, сетка бликов по дну, пузырьки."""
    p = rm.Paint(605)
    deep, mid, crest = _arr(rgb("3A8AC6")), _arr(AQUA), _arr(rgb("EAF8FC"))
    n1, n2, soft = p.tile_noise(5, 2), p.tile_noise(7, 2), p.tile_noise(4, 2)

    def fn(gx, gy):
        # Каустика: тонкие светлые жилки там, где шум проходит через ноль.
        r1 = 1.0 - np.clip(np.abs(n1) / 0.17, 0.0, 1.0)
        r2 = 1.0 - np.clip(np.abs(n2 + 0.2 * np.sin(gx * np.pi / 16.0)) / 0.13, 0.0, 1.0)
        web = np.maximum(rm._smooth_np(r1), rm._smooth_np(r2) * 0.7)
        t = rm._smooth_np(np.clip(soft * 0.5 + 0.5, 0.0, 1.0))
        color = deep * (1.0 - t[..., None]) + mid * t[..., None]
        k = (web * 0.82)[..., None]
        return color * (1.0 - k) + crest * k, 128.0 + soft * 30.0 + web * 34.0
    p.field(fn)
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.3, 0.75)
        p.ellipse(x, y, r, r, rgb("2E78B4"), 150)
        p.ellipse(x, y, r * 0.78, r * 0.78, rgb("7CC6E6"), 160)
        p.ellipse(x - r * 0.3, y - r * 0.3, r * 0.3, r * 0.3, rgb("FFFFFF"), 176)
    return p


def paint_bricks():
    """Перегородки опенспейса (борта, стены): тканевые панели 32×16 вразбежку в алюминиевых
    рамах, переплетение ткани, стикеры, лист с графиком и кнопки."""
    p = rm.Paint(627)
    cloth, frame = _arr(SEA), _arr(METAL_L)
    mid, fine = p.tile_noise(16, 3), p.tile_noise(48, 2)
    tones = p.rng.uniform(0.9, 1.12, (4, 2)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 16.0).astype(np.int32), 0, 3)
        shifted = (gx + (row % 2) * 16.0) % 64.0
        col = np.clip((shifted / 32.0).astype(np.int32), 0, 1)
        ex = np.minimum(shifted % 32.0, 32.0 - shifted % 32.0)
        ey = np.minimum(gy % 16.0, 16.0 - gy % 16.0)
        edge = np.minimum(ex, ey)
        seam = np.clip(edge / 0.22, 0.0, 1.0)
        rail = 1.0 - np.clip((edge - 0.95) / 0.2, 0.0, 1.0)
        inset = np.clip((edge - 1.15) / 0.8, 0.0, 1.0)
        weave = np.sin(gx * np.pi * 2.0 / 0.8) * np.sin(gy * np.pi * 2.0 / 0.8)
        # Свет ламп сверху: верх панели светлее.
        lit = 1.0 + 0.1 * np.clip(1.0 - (gy % 16.0) / 7.0, 0.0, 1.0)
        fabric = cloth * (tones[row, col] * (1.0 + 0.09 * weave + 0.07 * mid + 0.05 * fine) * (0.76 + 0.24 * inset) * lit)[..., None]
        metal = frame * ((0.5 + 0.5 * seam) * (1.0 + 0.04 * fine) * (1.08 - 0.16 * np.clip(edge / 0.95, 0.0, 1.0)))[..., None]
        k = rail[..., None]
        height = 128.0 + rail * 34.0 - (1.0 - seam) * 90.0 + (1.0 - rail) * (weave * 9.0 + mid * 6.0 - 10.0)
        return fabric * (1.0 - k) + metal * k, height
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(SEA, 1.3), 0.06)

    def note(x, y, c, lines=2):
        p.rect(x + 0.2, y + 0.3, 3.4, 3.4, mul(SEA, 0.55), 128)
        p.rect(x, y, 3.4, 3.4, c, 152)
        p.rect(x, y, 3.4, 0.6, mul(c, 0.88), 152)
        p.poly([(x + 2.5, y + 3.4), (x + 3.4, y + 3.4), (x + 3.4, y + 2.5)], mul(c, 0.72), 146)
        for i in range(lines):
            p.line([(x + 0.5, y + 1.4 + i * 0.8), (x + 2.7 - i * 0.6, y + 1.4 + i * 0.8)], mul(c, 0.5), 0.14, 152)

    # Все детали внутри своих панелей и не ближе трёх единиц к краю плитки.
    note(5.0, 4.0, GOLD), note(9.4, 6.4, PINK, 1), note(52.0, 36.5, GOLD, 3), note(22.0, 54.0, SKY, 2)
    note(38.5, 22.0, GOLD, 1)
    # Лист с графиком на кнопке.
    x, y = 40.0, 3.6
    p.rect(x + 0.25, y + 0.3, 6.4, 8.6, mul(SEA, 0.55), 128)
    p.rect(x, y, 6.4, 8.6, WHITE, 150)
    for i in range(3):
        p.line([(x + 0.8, y + 1.5 + i * 0.8), (x + 5.4 - i, y + 1.5 + i * 0.8)], GREY, 0.16, 150)
    for i, h in enumerate((1.2, 2.0, 1.6, 3.0)):
        p.rect(x + 0.9 + i * 1.2, y + 7.6 - h, 0.8, h, (AQUA, SEA_L, AQUA, RED)[i], 152)
    p.line([(x + 0.7, y + 7.7), (x + 5.7, y + 7.7)], DARK, 0.14, 150)
    # Фото в рамке и календарный лист, поверх них кнопки.
    p.rect(11.2, 40.3, 4.4, 3.6, WHITE, 150), p.rect(11.6, 40.7, 3.6, 2.4, AQUA, 150)
    p.poly([(11.6, 43.1), (13.0, 41.6), (14.0, 42.5), (14.6, 42.0), (15.2, 43.1)], GREEN, 150)
    p.rect(25.0, 24.6, 4.4, 4.8, WHITE, 150), p.rect(25.0, 24.6, 4.4, 1.2, RED, 152)
    for j in range(3):
        for i in range(4):
            p.rect(25.5 + i * 0.95, 26.3 + j * 0.95, 0.5, 0.5, GREY if (i + j) % 4 else DARK, 150)
    for bx, by, c in ((x + 3.2, y + 0.6, RED), (13.4, 40.5, RED), (27.2, 25.2, GOLD)):
        p.ellipse(bx + 0.12, by + 0.18, 0.5, 0.5, mul(SEA, 0.5), 140)
        p.ellipse(bx, by, 0.5, 0.5, c, 184)
        p.ellipse(bx - 0.15, by - 0.15, 0.17, 0.17, mix(c, WHITE, 0.7), 190)
    return p


# Слои обрыва сверху вниз: высота слоя и что это (None бумага, иначе цвет папки). В сумме 64.
_LAYERS = [(7.0, None), (3.0, GOLD), (9.0, None), (2.5, SEA_L), (8.0, None), (3.0, RED), (6.5, None), (2.5, GREEN),
           (10.0, None), (3.0, GOLD), (7.0, None), (2.5, METAL_L)]


def paint_cliff():
    """Обрыв из стопок бумаги и папок: слои листов торцом, между ними цветные папки с
    наклейками, стопки сдвинуты друг относительно друга, под каждым слоем тень."""
    p = rm.Paint(631)
    paper = _arr(rgb("E8E9EE"))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(14, 3), p.tile_noise(40, 2)
    tops = np.cumsum([0.0] + [h for h, _ in _LAYERS]).astype(np.float32)
    n = len(_LAYERS)
    is_paper = np.array([1.0 if c is None else 0.0 for _, c in _LAYERS], dtype=np.float32)
    colors = np.array([(232, 233, 238) if c is None else c for _, c in _LAYERS], dtype=np.float32)
    gaps = p.rng.uniform(0.0, 32.0, n).astype(np.float32)
    waves = p.rng.integers(1, 4, n).astype(np.float32)
    phases = p.rng.uniform(0.0, 6.28, n).astype(np.float32)
    tint = p.rng.uniform(0.93, 1.05, n).astype(np.float32)

    def fn(gx, gy):
        idx = np.clip(np.searchsorted(tops, gy, side="right") - 1, 0, n - 1)
        top, h = tops[idx], (tops[idx + 1] - tops[idx])
        v = (gy - top) / h
        isp = is_paper[idx]
        # Стопки в слое: щель между соседними каждые 32 единицы, у слоя свой сдвиг.
        d = (gx - gaps[idx]) % 32.0
        gap = np.clip(np.minimum(d, 32.0 - d) / 0.4, 0.0, 1.0)
        pile = np.floor(((gx - gaps[idx]) % 64.0) / 32.0)
        # Слой выступает волной, соседняя стопка сдвинута глубже.
        out = np.sin(gx * np.pi * 2.0 / 64.0 * waves[idx] + phases[idx]) * 0.5 + (pile - 0.5) * 0.7 + low * 0.3
        # Торцы листов: тонкие линии, отдельные листы торчат темнее и светлее.
        sheet = np.sin((gy - top) * np.pi * 2.0 / 0.55 + mid * 0.5)
        stray = np.clip(np.sin((gy - top) * np.pi * 2.0 / 2.3 + mid * 0.9 + phases[idx]) - 0.8, 0.0, 1.0) * 5.0
        ptone = 1.0 + 0.055 * sheet - 0.12 * stray + 0.04 * fine + 0.05 * out
        # Папка: корешок скруглён, блик сверху, тень снизу.
        ftone = (0.78 + 0.34 * np.sin(np.clip(v, 0.0, 1.0) * np.pi) ** 0.7) * (1.0 + 0.04 * fine + 0.04 * mid)
        tone = np.where(isp > 0.5, ptone, ftone) * tint[idx]
        # Тень под верхним слоем и тёмный стык снизу.
        under = 1.0 - 0.3 * np.clip(1.0 - (gy - top) / 1.3, 0.0, 1.0)
        joint = np.clip(np.minimum(gy - top, top + h - gy) / 0.2, 0.0, 1.0)
        tone = tone * under * (0.55 + 0.45 * joint) * (0.5 + 0.5 * gap)
        height = 128.0 + out * 34.0 + np.where(isp > 0.5, sheet * 6.0 - stray * 14.0, np.sin(np.clip(v, 0.0, 1.0) * np.pi) * 22.0)
        height = height - (1.0 - joint) * 50.0 - (1.0 - gap) * 70.0 + fine * 4.0
        return colors[idx] * tone[..., None] + paper * 0.0, height
    p.field(fn)
    # Наклейки на корешках папок и закладки-стикеры в бумаге, не ближе четырёх единиц к краю.
    for i, (h, c) in enumerate(_LAYERS):
        y = float(tops[i])
        if c is not None:
            # Наклейка в начале каждой стопки слоя, если она целиком помещается вдали от края.
            for x in ((float(gaps[i]) + 3.0 + 32.0 * j) % 64.0 for j in range(2)):
                if not 4.0 < x < 50.0:
                    continue
                p.rect(x, y + h * 0.22, 6.0, h * 0.56, WHITE, 150)
                p.line([(x + 0.7, y + h * 0.42), (x + 4.6, y + h * 0.42)], DARK, 0.16, 150)
                p.line([(x + 0.7, y + h * 0.62), (x + 3.2, y + h * 0.62)], GREY, 0.14, 150)
                p.ellipse(x + 8.4, y + h * 0.5, h * 0.2, h * 0.2, mul(c, 0.5), 110)
        else:
            for _ in range(3):
                x, yy = p.rng.uniform(5, 57), y + p.rng.uniform(1.0, h - 1.6)
                col = (GOLD, PINK, AQUA, GOLD_L)[int(p.rng.integers(0, 4))]
                p.rect(x, yy, 2.2, 0.5, col, 168)
                p.rect(x, yy + 0.5, 2.2, 0.18, mul(col, 0.6), 150)
    p.speckle(0.5, 0.5, 63, 63, 300, rgb("9AA2B4"), 0.06)
    return p


def paint_grass():
    """Зелёный ковёр зоны отдыха: пятна светлее и темнее, длинный ворс, конфетти от дырокола."""
    gd, gl = mul(GREEN, 0.66), mul(GREEN, 1.28)
    p = rm._ground(629, GREEN, 0.12, 0.08, 20.0)
    for _ in range(1700):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.4, 63)
        lean = p.rng.uniform(-0.45, 0.45)
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.4, 0.9))], gd if p.rng.random() < 0.55 else gl, 0.14, 152)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(GREEN, 0.56), 0.08)
    _confetti(p, 34, [WHITE, WHITE, GOLD, PINK, SKY], 0.3, 0.48)
    return p


def paint_road():
    """Плитка коридора: стыки плит, крошка терраццо, блестящие следы колёсиков, пунктир жёлтым
    скотчем по оси, потёртости."""
    p = rm._ground(633, LINO, 0.06, 0.04, 8.0)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(LINO, 0.72), 0.13)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(LINO, 1.3), 0.12)
    p.speckle(0.5, 0.5, 63, 63, 260, rgb("D8DCE6"), 0.15)
    p.speckle(0.5, 0.5, 63, 63, 120, mix(LINO, GOLD, 0.5), 0.13)
    for y in (0.0, 32.0, 64.0):
        p.fold([(-1, y), (65, y)], 0.45, 0.5, 80)
    for x in (0.0, 64.0):
        p.fold([(x, -1), (x, 65)], 0.45, 0.58, 70)
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.6, 0.87, 22)
        for dx in (-0.8, 0.8):
            p.fold([(x + dx, -1), (x + dx, 65)], 0.3, 0.9, 14)
    # Скотч: жёлтая лента с чёрной кромкой и бликом, края чуть неровные.
    for y in (6.0, 38.0):
        p.band(31.1, y, 1.8, 12.0, mul(GOLD, 0.55), 140, 0.0)
        p.rect(31.3, y + 0.15, 1.4, 11.7, GOLD, 142)
        p.rect(31.45, y + 0.4, 0.3, 11.2, GOLD_L, 144)
        for i in range(4):
            p.line([(31.3, y + 2.6 + i * 2.6), (32.7, y + 2.0 + i * 2.6)], mul(GOLD, 0.8), 0.12, 140)
    p.wrinkles(3, 3, 58, 58, 8, 4.0, 1.0, 0.76, 40)
    p.stains(3, 3, 58, 58, 10, 2.6, 0.88)
    return p


def paint_mud():
    """Пролитый кофе на тёмном ковролине: глянцевые лужи с тёмной каймой, мокрый ворс вокруг,
    кремовые пузырьки пены. Заметно темнее трассы."""
    p = rm.Paint(635)
    wet, pool, rim = _arr(mix(COFFEE, DARK, 0.45)), _arr(mul(COFFEE, 0.62)), _arr(mul(COFFEE, 0.36))
    shine = _arr(rgb("A87A4C"))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(14, 3), p.tile_noise(64, 2)
    gloss = p.tile_noise(6, 2)

    def fn(gx, gy):
        m = low + 0.25 * mid
        inside = rm._smooth_np(np.clip((m - 0.02) / 0.1, 0.0, 1.0))
        edge = 1.0 - np.clip(np.abs(m - 0.07) / 0.09, 0.0, 1.0)
        rib = np.sin(gy * np.pi * 2.0 / 1.0)
        carpet = wet * (1.0 + 0.1 * rib + 0.1 * fine + 0.12 * mid)[..., None]
        # Блик на луже: светлая полоса там, где второй шум высок.
        gl = rm._smooth_np(np.clip((gloss - 0.42) / 0.22, 0.0, 1.0)) * inside
        liquid = pool * (1.0 + 0.1 * gloss)[..., None]
        liquid = liquid * (1.0 - gl[..., None] * 0.6) + shine * (gl[..., None] * 0.6)
        color = carpet * (1.0 - inside[..., None]) + liquid * inside[..., None]
        k = (rm._smooth_np(edge) * 0.7)[..., None]
        color = color * (1.0 - k) + rim * k
        height = 128.0 + (1.0 - inside) * (rib * 12.0 + fine * 9.0 + 14.0) - inside * 18.0 + gloss * inside * 6.0
        return color, height
    p.field(fn)
    for _ in range(46):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.2, 0.5)
        p.ellipse(x, y, r, r, rgb("8A6038"), 132)
        p.ellipse(x - r * 0.25, y - r * 0.25, r * 0.45, r * 0.45, rgb("E6CF9E"), 140)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(COFFEE, 0.4), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 260, rgb("7A5A3C"), 0.08)
    return p


def paint_sail():
    """Стена жёлтых стикеров: листки 16×16 чуть разного тона, клейкая полоса сверху, отогнутый
    уголок с тенью, строчки каракулей и галочки."""
    p = rm.Paint(637)
    base = _arr(GOLD)
    mid, fine = p.tile_noise(16, 3), p.tile_noise(48, 2)
    tones = p.rng.uniform(0.9, 1.08, (4, 4)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 16.0).astype(np.int32), 0, 3)
        col = np.clip((gx / 16.0).astype(np.int32), 0, 3)
        u, v = gx % 16.0, gy % 16.0
        edge = np.minimum(np.minimum(u, 16.0 - u), np.minimum(v, 16.0 - v))
        seam = np.clip(edge / 0.28, 0.0, 1.0)
        # Листок приклеен верхом, низ отходит от стены: к низу светлее и выше, под ним тень.
        lift = np.clip((v - 9.0) / 7.0, 0.0, 1.0)
        glue = np.clip(1.0 - v / 3.0, 0.0, 1.0)
        shadow = np.clip(1.0 - v / 1.6, 0.0, 1.0)
        tone = tones[row, col] * (1.0 + 0.05 * mid + 0.03 * fine) * (0.6 + 0.4 * seam) * (1.0 + 0.09 * lift - 0.07 * glue - 0.16 * shadow)
        return base * tone[..., None], 128.0 + lift * 46.0 - (1.0 - seam) * 60.0 + mid * 8.0 + fine * 3.0
    p.field(fn)
    ink = mul(GOLD, 0.42)
    for row in range(4):
        for col in range(4):
            x, y = col * 16.0, row * 16.0
            kind = (row * 3 + col * 5) % 4
            if kind == 0:      # строчки каракулей
                for i in range(3):
                    n = 5
                    w = p.rng.uniform(6.5, 10.0)
                    p.line([(x + 2.6 + w * j / n, y + 5.0 + i * 2.6 + p.rng.uniform(-0.35, 0.35)) for j in range(n + 1)], ink, 0.3, 124)
            elif kind == 1:    # галочка
                p.line([(x + 4.6, y + 8.4), (x + 6.8, y + 10.8), (x + 11.2, y + 4.8)], mix(RED, GOLD, 0.15), 0.6, 126)
            elif kind == 2:    # список с квадратиками
                for i in range(3):
                    p.rect(x + 3.0, y + 4.6 + i * 2.6, 1.1, 1.1, ink, 124)
                    p.line([(x + 5.0, y + 5.15 + i * 2.6), (x + 5.0 + p.rng.uniform(4.0, 7.2), y + 5.15 + i * 2.6)], ink, 0.3, 124)
            else:              # стрелка вверх: рост показателей
                p.line([(x + 3.6, y + 11.0), (x + 6.4, y + 8.2), (x + 8.4, y + 9.6), (x + 12.0, y + 5.0)], mix(SEA, GOLD, 0.2), 0.45, 126)
                p.poly([(x + 12.6, y + 4.2), (x + 12.3, y + 6.6), (x + 10.4, y + 4.9)], mix(SEA, GOLD, 0.2), 126)
            # Отогнутый уголок: светлый треугольник с тенью.
            p.poly([(x + 11.6, y + 15.4), (x + 15.4, y + 15.4), (x + 15.4, y + 11.6)], mul(GOLD, 0.6), 150)
            p.poly([(x + 11.6, y + 15.4), (x + 15.4, y + 11.6), (x + 12.2, y + 12.2)], GOLD_L, 186)
    p.wrinkles(1, 1, 62, 62, 14, 3.0, 1.2, 0.93, 18)
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
