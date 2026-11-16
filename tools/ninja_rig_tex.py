#!/usr/bin/env python3
"""Текстуры уровня «Ниндзя» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Ниндзя у
«продвинутых» это старая Япония на закате: гравий сада камней с бороздами от граблей, кедровый
настил веранды с клинышками-бабочками на стыках, тёмный пруд с золотой дорожкой заката, стена
замка из подогнанных валунов со мхом в швах, слоистый сланец обрыва со мхом на уступах, мох с
упавшими листьями клёна, дорожка из каменных плит с колеями там же, где колеи у пиратов, и
светлыми камнями по оси, раскисшая земля рисового поля с лужами, в которых закат (заметно темнее
дорожки), и полотнище знамени нобори с красными кругами-гербами (слот `tex_sail`: у ниндзя это
ткань знамён и навесов, парусов в сеттинге нет). Плитки стыкуются по краям: поля считаются на
периодическом шуме и периодических решётках, отдельные детали не подходят к краю. Цвета из
палитры основы 16/32 (`ninja16.PALETTE`).

    python3 tools/ninja_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import ninja16 as n16  # noqa: E402

rgb, mul, UNITS = rm.rgb, rm.mul, rm.UNITS


def _pal(index):
    return tuple(n16.PALETTE[index])


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


NAVY, SEA = _pal(n16.NAVY), _pal(n16.SEA)          # глубина пруда и сумеречный синий
CORAL, GLOW = _pal(n16.AQUA), _pal(n16.SKY)        # коралл заката и золото у горизонта
WHITE, GREY = _pal(n16.WHITE), _pal(n16.GREY)
GOLD, BRASS = _pal(n16.GOLD), _pal(n16.BRASS)
STONE, LACQ = _pal(n16.METAL), _pal(n16.DARK)      # камень и чёрный лак
RED, CLAY = _pal(n16.RED), _pal(n16.TAN)
MOSS, PINE = _pal(n16.VIOLET), _pal(n16.PLUM)      # мох и тень зелени
GRAVEL = rgb("CDC4B2")                             # гравий сада камней, тёплый от заката
CEDAR = rgb("96583A")                              # кедр настила
SLATE = rgb("56506A")                              # сланец обрыва
PAVE = mix(STONE, GREY, 0.3)                       # плиты дорожки
PADDY = rgb("3C2A2C")                              # земля рисового поля
CLOTH = rgb("E6DCC4")                              # небелёное полотно знамени


def _wrap(d):
    """Расстояние по одной оси на замкнутом холсте."""
    d = np.abs(d)
    return np.minimum(d, UNITS - d)


def _leaf(p, x, y, r, turn, color, height=150):
    """Лист клёна: пять острых лопастей веером и черешок."""
    pts = []
    lobes = (-112, -56, 0, 56, 112)
    for i, deg in enumerate(lobes):
        a = math.radians(deg) + turn
        k = (0.62, 0.86, 1.0, 0.86, 0.62)[i]
        if i:
            b = math.radians(deg - 28) + turn
            pts.append((x + math.sin(b) * r * 0.36, y - math.cos(b) * r * 0.36))
        pts.append((x + math.sin(a) * r * k, y - math.cos(a) * r * k))
    pts.append((x - math.sin(turn) * r * 0.12, y + math.cos(turn) * r * 0.12))
    p.poly(pts, color, height)
    sx, sy = -math.sin(turn), math.cos(turn)
    p.line([(x, y), (x + sx * r * 0.7, y + sy * r * 0.7)], mul(color, 0.6), 0.14, height - 10)
    p.line([(x, y), (x - sx * r * 0.7, y - sy * r * 0.7)], mul(color, 0.72), 0.1, height - 14)


def paint_sand():
    """Гравий сада камней: борозды от граблей, круги вокруг двух валунов, зерно и камешки."""
    p = rm.Paint(501)
    base = np.array(GRAVEL, dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(40, 2)
    rocks = ((20.0, 23.0, 3.0), (45.0, 43.0, 2.3))

    def fn(gx, gy):
        # Борозды идут вдоль X: десять на плитку, чуть гуляют.
        wave = np.sin(2 * np.pi * (gy * 10.0 / UNITS + 0.05 * np.sin(2 * np.pi * gx / UNITS)))
        for cx, cy, r in rocks:
            d = np.hypot(gx - cx, gy - cy)
            w = rm._smooth_np(np.clip(1.0 - (d - r - 5.0) / 3.5, 0.0, 1.0))
            ring = np.sin(2 * np.pi * (d - r) / 3.2 + np.pi * 0.5)
            wave = wave * (1.0 - w) + ring * w
        tone = 1.0 + 0.09 * wave + 0.05 * low + 0.04 * mid + 0.04 * fine
        return base[None, None, :] * tone[..., None], 128.0 + wave * 34.0 + mid * 8.0 + fine * 12.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 3000, mul(GRAVEL, 0.78), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 2000, mul(GRAVEL, 1.12), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 260, mix(GRAVEL, CORAL, 0.5), 0.09)
    for cx, cy, r in rocks:
        # Валун: тень на гравии, тёмный камень, свет заката слева сверху, мох у подножия.
        p.ellipse(cx + r * 0.25, cy + r * 0.3, r * 1.12, r * 0.92, mul(GRAVEL, 0.62), 110)
        p.poly([(cx - r, cy + r * 0.2), (cx - r * 0.7, cy - r * 0.62), (cx - r * 0.1, cy - r * 0.86),
                (cx + r * 0.66, cy - r * 0.6), (cx + r, cy + r * 0.1), (cx + r * 0.6, cy + r * 0.74),
                (cx - r * 0.5, cy + r * 0.8)], mul(STONE, 0.72), 214)
        p.poly([(cx - r * 0.8, cy - r * 0.1), (cx - r * 0.6, cy - r * 0.54), (cx - r * 0.1, cy - r * 0.74),
                (cx + r * 0.42, cy - r * 0.5), (cx + r * 0.1, cy - r * 0.1)], mix(STONE, GREY, 0.45), 236)
        p.line([(cx - r * 0.56, cy - r * 0.5), (cx - r * 0.1, cy - r * 0.7)], mix(GREY, CORAL, 0.4), 0.2, 240)
        p.line([(cx + r * 0.1, cy - r * 0.1), (cx + r * 0.3, cy + r * 0.6)], mul(STONE, 0.5), 0.16, 190)
        p.speckle(cx - r * 0.9, cy + r * 0.4, r * 1.7, r * 0.5, 46, MOSS, 0.2)
        p.speckle(cx - r * 0.9, cy + r * 0.5, r * 1.7, r * 0.4, 30, PINE, 0.18)
    for _ in range(18):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.25, 0.5)
        p.ellipse(x + 0.14, y + 0.18, r, r * 0.8, mul(GRAVEL, 0.66), 112)
        p.ellipse(x, y, r, r * 0.8, mul(STONE, 0.9) if p.rng.random() < 0.6 else WHITE, 188)
    return p


def paint_planks():
    """Кедровый настил веранды: восемь досок с волокнами, стыки вразбежку с тёмными клинышками-
    бабочками, сучки, натёртые ногами светлые дорожки."""
    p = rm.Paint(503)
    p.wood(0, 0, 64, 64, 8, True, CEDAR, 0.26)
    for i in range(8):
        for y in ((11.5, 43.5) if i % 2 == 0 else (27.5, 59.5)):
            x = i * 8.0
            p.fold([(x + 0.3, y), (x + 7.7, y)], 0.34, 0.5, 80)
            # Клин-бабочка поперёк стыка: два треугольника вершинами друг к другу.
            c = x + 4.0
            p.poly([(c - 1.3, y - 1.9), (c + 1.3, y - 1.9), (c + 0.5, y), (c + 1.3, y + 1.9),
                    (c - 1.3, y + 1.9), (c - 0.5, y)], mul(LACQ, 1.1), 146)
            p.line([(c - 1.1, y - 1.75), (c + 1.1, y - 1.75)], mul(CEDAR, 0.9), 0.12, 150)
            p.line([(c - 1.25, y - 1.8), (c - 0.5, y), (c - 1.25, y + 1.8)], mul(LACQ, 0.6), 0.12, 96)
            p.line([(c + 1.25, y - 1.8), (c + 0.5, y), (c + 1.25, y + 1.8)], mul(LACQ, 0.6), 0.12, 96)
    # Сучки: тёмный глазок с кольцами волокон вокруг.
    for _ in range(9):
        i = int(p.rng.integers(0, 8))
        x, y = i * 8.0 + p.rng.uniform(2.4, 5.6), p.rng.uniform(4, 60)
        p.ellipse(x, y, 0.9, 1.3, mul(CEDAR, 0.8), 122)
        p.ellipse(x, y, 0.55, 0.8, mul(CEDAR, 0.56), 112)
        p.ellipse(x, y, 0.24, 0.36, mul(CEDAR, 0.36), 100)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(CEDAR, 1.24), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(CEDAR, 0.66), 0.08)
    p.wrinkles(2, 2, 60, 60, 16, 5.0, 0.05, 0.8, 30)
    p.stains(2, 2, 60, 60, 9, 2.6, 0.88)
    return p


def paint_water():
    """Тёмный пруд: плавная зыбь от чёрно-синей глубины к синему, на гребнях золото заката."""
    p = rm.Paint(505)
    deep, mid, crest = (np.array(c, dtype=np.float32) for c in (mul(NAVY, 0.62), mix(NAVY, SEA, 0.7), GLOW))
    warm = np.array(CORAL, dtype=np.float32)
    noise = p.tile_noise(8, 3)

    def fn(gx, gy):
        w = np.sin((gy + 5.0 * np.sin(gx * np.pi / 16.0)) * np.pi / 8.0) + np.sin((gx + gy * 2.0) * np.pi / 32.0) + 0.5 * noise
        t = rm._smooth_np(np.clip((w + 1.3) / 2.8, 0.0, 1.0))
        rim = rm._smooth_np(np.clip((w - 1.55) / 0.4, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 2.0) / 0.3, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - rim[..., None] * 0.7) + warm[None, None, :] * (rim[..., None] * 0.7)
        color = color * (1.0 - top[..., None]) + crest[None, None, :] * top[..., None]
        return color, 128.0 + w * 30.0
    p.field(fn)
    return p


def paint_bricks():
    """Стена замка (борта, стены): подогнанные друг к другу валуны разной формы, тёмные глубокие
    швы, свет на верхней кромке камня, мох в швах."""
    p = rm.Paint(527)
    stone = np.array(mix(STONE, GREY, 0.12), dtype=np.float32)
    warm = np.array(mix(STONE, CLAY, 0.3), dtype=np.float32)
    mid, fine = p.tile_noise(16, 3), p.tile_noise(40, 2)
    # Камни: зёрна на сбитой решётке 5×6, расстояния считаются по замкнутому холсту.
    seeds = []
    for j in range(6):
        for i in range(5):
            seeds.append(((i + 0.5 + (j % 2) * 0.5) * 12.8 + p.rng.uniform(-3.4, 3.4),
                          (j + 0.5) * UNITS / 6.0 + p.rng.uniform(-2.6, 2.6)))
    tones = p.rng.uniform(0.8, 1.16, len(seeds)).astype(np.float32)
    tints = p.rng.uniform(0.0, 1.0, len(seeds)).astype(np.float32)
    seam_holder = {}

    def fn(gx, gy):
        f1 = np.full(gx.shape, 1e9, dtype=np.float32)
        f2 = np.full(gx.shape, 1e9, dtype=np.float32)
        idx = np.zeros(gx.shape, dtype=np.int32)
        dy1 = np.zeros(gx.shape, dtype=np.float32)
        for k, (sx, sy) in enumerate(seeds):
            ry = (gy - sy + UNITS / 2.0) % UNITS - UNITS / 2.0
            # Камни шире, чем выше: по вертикали расстояние растянуто.
            d = np.hypot(_wrap(gx - sx % UNITS), ry * 1.25)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            idx = np.where(closer, k, idx)
            dy1 = np.where(closer, ry, dy1)
            f1 = np.where(closer, d, f1)
        gap = f2 - f1 + mid * 0.25
        seam = rm._smooth_np(np.clip((gap - 0.25) / 0.9, 0.0, 1.0))
        dome = rm._smooth_np(np.clip(gap / 4.5, 0.0, 1.0))
        lit = 1.0 + 0.12 * np.clip(-dy1 / 4.0, -1.0, 1.0)
        tone = tones[idx] * (1.0 + 0.09 * mid + 0.06 * fine) * (0.3 + 0.7 * seam) * lit
        tint = (tints[idx] * 0.5)[..., None]
        color = stone[None, None, :] * (1.0 - tint) + warm[None, None, :] * tint
        seam_holder["seam"] = seam
        return color * tone[..., None], 70.0 + seam * 40.0 + dome * 46.0 + mid * 12.0 + fine * 8.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(STONE, 0.56), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 560, mul(GREY, 1.0), 0.07)
    p.wrinkles(2, 2, 60, 60, 10, 2.6, 0.9, 0.62, 56)
    # Мох садится только в швы: пятно шума, умноженное на близость к шву.
    seam = seam_holder["seam"]
    patch = np.clip((p.tile_noise(5, 3) - 0.02) / 0.3, 0.0, 1.0) * np.clip(1.0 - seam * 1.05, 0.0, 1.0)
    grain = 0.8 + 0.3 * p.tile_noise(48, 2)
    a = np.asarray(p.im, dtype=np.float32)
    moss = np.array(mix(MOSS, PINE, 0.45), dtype=np.float32)[None, None, :] * grain[..., None]
    k = np.clip(patch * 1.5, 0.0, 0.92)[..., None]
    from PIL import Image
    p.im = Image.fromarray(np.clip(a * (1.0 - k) + moss * k, 0, 255).astype(np.uint8))
    from PIL import ImageDraw
    p.d = ImageDraw.Draw(p.im)
    return p


def paint_cliff():
    """Обрыв: слоистый тёмный сланец, пласты расколоты на блоки отвесными трещинами, мох на
    уступах, закатный свет на кромках."""
    p = rm.Paint(531)
    stone = np.array(SLATE, dtype=np.float32)
    warm = np.array(mix(SLATE, CLAY, 0.45), dtype=np.float32)
    moss = np.array(mix(MOSS, PINE, 0.35), dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(10, 3), p.tile_noise(28, 2)
    layers = np.array([0.1, 0.8, 0.35, 1.0, 0.55, 0.0, 0.7], dtype=np.float32)
    shifts = np.array([0.0, 5.0, 11.0, 2.0, 8.0, 13.0, 4.0], dtype=np.float32)

    def fn(gx, gy):
        phase = gy / UNITS * 7.0 + low * 0.4 + mid * 0.12
        band = phase - np.floor(phase)
        n = np.mod(np.floor(phase), 7.0).astype(np.int32)
        ledge = np.clip(band / 0.14, 0.0, 1.0) * np.clip((1.0 - band) / 0.55, 0.0, 1.0)
        # Отвесные трещины: у каждого пласта свой сдвиг, шаг 16.
        cx = np.mod(gx + shifts[n] + mid * 1.2, 16.0)
        crack = np.clip(np.minimum(cx, 16.0 - cx) / 0.5, 0.0, 1.0)
        layer = layers[n]
        tone = (0.62 + 0.38 * ledge) * (1.0 + 0.12 * mid + 0.07 * fine) * (0.5 + 0.5 * crack)
        color = stone[None, None, :] * (1.0 - layer[..., None] * 0.6) + warm[None, None, :] * (layer[..., None] * 0.6)
        color = color * tone[..., None]
        # Мох лежит на верхней кромке пласта там, где шум разрешает.
        top = np.clip((0.3 - band) / 0.12, 0.0, 1.0) * np.clip(band / 0.05, 0.0, 1.0)
        green = (top * np.clip((low + mid * 0.6 + 0.25) / 0.3, 0.0, 1.0) * (0.8 + 0.2 * fine))[..., None]
        color = color * (1.0 - green * 0.85) + moss[None, None, :] * (green * 0.85)
        return color, 128.0 + ledge * 60.0 - 40.0 + mid * 24.0 + fine * 12.0 - (1.0 - crack) * 46.0
    p.field(fn)
    p.wrinkles(1, 1, 62, 62, 12, 5.0, 1.2, 0.6, 64)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(SLATE, 0.55), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 420, mix(SLATE, CORAL, 0.5), 0.08)
    return p


def paint_grass():
    """Мох: бархатные подушки светлее и темнее, крапины ворса, упавшие листья клёна."""
    base = mix(MOSS, PINE, 0.38)
    p = rm.Paint(529)
    color = np.array(base, dtype=np.float32)
    lightc = np.array(mix(MOSS, GLOW, 0.2), dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(14, 3), p.tile_noise(44, 2)

    def fn(gx, gy):
        # Подушки: бугры среднего шума, между ними тёмные ложбины.
        bump = rm._smooth_np(np.clip((mid + 0.55) / 1.0, 0.0, 1.0))
        tone = (0.72 + 0.4 * bump) * (1.0 + 0.1 * low + 0.07 * fine)
        k = (bump * 0.4)[..., None]
        return (color[None, None, :] * (1.0 - k) + lightc[None, None, :] * k) * tone[..., None], 104.0 + bump * 44.0 + fine * 12.0 + low * 10.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2600, mul(base, 0.7), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 2200, mix(MOSS, GLOW, 0.3), 0.09)
    reds = (RED, mix(RED, CORAL, 0.6), mul(RED, 0.74), mix(CORAL, GOLD, 0.5))
    for i in range(30):
        x, y = p.rng.uniform(3.5, 60.5), p.rng.uniform(3.5, 60.5)
        r = p.rng.uniform(1.3, 2.1)
        turn = p.rng.uniform(0, math.tau)
        p.ellipse(x + 0.3, y + 0.36, r * 0.7, r * 0.6, mul(base, 0.56), None)
        _leaf(p, x, y, r, turn, reds[i % len(reds)], 168)
    return p


def paint_road():
    """Каменная дорожка: плиты вразбежку с глубокими швами, две укатанные колеи вдоль, светлые
    квадратные камни по оси, мох в швах, потёртости."""
    p = rm.Paint(533)
    base = np.array(PAVE, dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(44, 2)
    tones = p.rng.uniform(0.88, 1.12, (4, 4)).astype(np.float32)

    def fn(gx, gy):
        # Плиты 16×16 лежат столбцами вдоль дороги, соседние столбцы сдвинуты на полплиты.
        col = np.clip((gx / 16.0).astype(np.int32), 0, 3)
        shifted = (gy + (col % 2) * 8.0) % UNITS
        row = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        ex = np.minimum(gx % 16.0, 16.0 - gx % 16.0)
        ey = np.minimum(shifted % 16.0, 16.0 - shifted % 16.0)
        edge = np.minimum(ex, ey) + mid * 0.12
        seam = np.clip(edge / 0.5, 0.0, 1.0)
        bevel = np.clip((edge - 0.5) / 1.0, 0.0, 1.0)
        tone = tones[row, col] * (1.0 + 0.07 * low + 0.06 * mid + 0.05 * fine) * (0.36 + 0.64 * seam) * (0.9 + 0.1 * bevel)
        return base[None, None, :] * tone[..., None], 128.0 - (1.0 - seam) * 84.0 - (1.0 - bevel) * 12.0 + mid * 10.0 + fine * 8.0
    p.field(fn)
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.6, 0.84, 30)
        p.fold([(x + 2.0, -1), (x + 2.0, 65)], 0.5, 1.1, -8)
    # Светлые камни по оси: квадрат на угол, шаг 16, не касаются края плитки.
    for y in (8.0, 24.0, 40.0, 56.0):
        p.poly([(32.0, y - 2.5), (34.5, y), (32.0, y + 2.5), (29.5, y)], mul(LACQ, 0.9), 70)
        p.poly([(32.0, y - 2.0), (34.0, y), (32.0, y + 2.0), (30.0, y)], mix(GREY, WHITE, 0.4), 142)
        p.line([(30.4, y), (32.0, y - 1.6)], WHITE, 0.14, 150)
    p.speckle(0.5, 0.5, 63, 63, 1400, mul(PAVE, 0.74), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(PAVE, 1.16), 0.07)
    # Мох в швах: крапины вдоль стыков столбцов.
    for x in (16.0, 48.0):
        for _ in range(7):
            y = p.rng.uniform(3, 58)
            p.speckle(x - 0.5, y, 1.0, 3.0, 22, MOSS if p.rng.random() < 0.6 else PINE, 0.16)
    p.wrinkles(3, 3, 58, 58, 7, 3.6, 1.0, 0.7, 50)
    p.stains(3, 3, 58, 58, 8, 2.4, 0.9)
    return p


def paint_mud():
    """Раскисшая земля рисового поля: тёмная грязь с комьями, лужи с отражением заката, ростки
    риса. Заметно темнее дорожки."""
    p = rm._ground(535, PADDY, 0.16, 0.12, 30.0)
    for _ in range(10):
        x, y = p.rng.uniform(9, 55), p.rng.uniform(8, 56)
        rx, ry = p.rng.uniform(3.0, 5.6), p.rng.uniform(1.5, 2.8)
        p.ellipse(x, y, rx * 1.12, ry * 1.18, mul(PADDY, 0.66), 104)
        p.ellipse(x, y, rx, ry, mix(NAVY, PADDY, 0.6), 86)
        # Закат в луже: коралловая полоса и золотой блик.
        p.ellipse(x - rx * 0.1, y - ry * 0.12, rx * 0.7, ry * 0.5, mix(PADDY, CORAL, 0.45), 86)
        p.ellipse(x - rx * 0.2, y - ry * 0.2, rx * 0.34, ry * 0.2, mix(CORAL, GLOW, 0.5), 86)
    for _ in range(80):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 62)
        r = p.rng.uniform(0.3, 0.7)
        p.ellipse(x + 0.12, y + 0.16, r, r * 0.7, mul(PADDY, 0.56), 110)
        p.ellipse(x, y, r, r * 0.7, mul(PADDY, 1.34), 164)
    # Ростки риса: пучки из трёх травинок рядами.
    for row in range(4):
        for col in range(4):
            x = 8.0 + col * 16.0 + p.rng.uniform(-1.2, 1.2)
            y = 9.0 + row * 16.0 + p.rng.uniform(-1.2, 1.2)
            for lean in (-0.55, 0.0, 0.55):
                p.line([(x, y), (x + lean, y - p.rng.uniform(1.0, 1.7))], MOSS if lean else mix(MOSS, GLOW, 0.4), 0.16, 170)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(PADDY, 1.5), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(PADDY, 0.5), 0.1)
    return p


def paint_sail():
    """Полотнище знамени нобори: небелёная ткань в два полотна со швами и красной строчкой,
    красные круги-гербы с тремя просветами, мелкие складки."""
    p = rm._ground(537, CLOTH, 0.06, 0.04, 10.0)
    p.weave(0, 0, 64, 64, 0.4, 0.07)
    for x in (0.4, 32.0):
        p.fold([(x, 0), (x, 64)], 0.5, 0.76, 44)
        p.stitch([(x + 1.0, 0.3), (x + 1.0, 63.7)], RED, 0.16, 0.7)
    # Герб на каждом полотне, соседние сдвинуты на полплитки.
    for cx, cy in ((16.5, 16.0), (48.5, 48.0)):
        p.ellipse(cx, cy, 7.4, 7.4, mul(RED, 0.94), 122)
        p.ellipse(cx, cy, 6.0, 6.0, CLOTH, 128)
        p.ellipse(cx, cy, 5.2, 5.2, RED, 122)
        for k in range(3):
            a = math.radians(90 + k * 120)
            p.ellipse(cx + math.cos(a) * 2.5, cy - math.sin(a) * 2.5, 1.5, 1.5, CLOTH, 128)
        p.ellipse(cx, cy, 0.7, 0.7, CLOTH, 128)
    # Тушью: три коротких мазка под гербом, как подпись клана.
    for cx, cy in ((16.5, 44.0), (48.5, 12.0)):
        for i, w in enumerate((7.0, 5.0, 7.0)):
            p.band(cx - w / 2.0, cy + i * 2.6, w, 1.1, mul(LACQ, 0.9), 126, 0.14)
    p.weave(0, 0, 64, 64, 0.4, 0.04)
    p.wrinkles(1, 1, 62, 62, 26, 3.4, 1.2, 0.88, 26)
    p.stains(2, 2, 60, 60, 6, 2.2, 0.93)
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
