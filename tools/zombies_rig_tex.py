#!/usr/bin/env python3
"""Текстуры уровня «Зомби» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Зомби у
«продвинутых» это ночное кладбище у пригорода: сухая кладбищенская земля с палой листвой и
костями, серые гробовые доски мостков на ржавых гвоздях, болотная жижа с ряской, замшелая
кладка ограды с выбитыми крестами, срез земли с корнями и черепом на месте обрыва, жухлая
трава с бурьяном, битый асфальт с жёлтым пунктиром, мокрая грязь с лунными лужами и латаный
армейский брезент. Плитки стыкуются по краям: поля считаются на периодическом шуме и
периодических решётках, отдельные детали не подходят к краю. Свойства, на которые рассчитаны
демки, те же, что у космоса: колеи дороги на 19 и 45, пунктир по оси, грязь заметно темнее
дороги, вода одним плавным полем без отдельных деталей, швы полотнища на 0.4 и 32. Цвета из
палитры основы 16/32 (`zombies16.PALETTE`): земля не красная и не синяя, чтобы выживший в
красной куртке и джинсах читался на ней ночью. Набор подключает `rig_models.py` через
`setting_sets.rig_set`.

    python3 tools/zombies_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import zombies16 as z16  # noqa: E402

rgb, mul, mix, UNITS = rm.rgb, rm.mul, rm.mix, rm.UNITS


def _pal(index):
    return tuple(z16.PALETTE[index])


BONE = _pal(z16.WHITE)       # кость, крест
STONE = _pal(z16.GREY)       # камень, жесть
LABEL = _pal(z16.GOLD)       # разметка, сухая трава
STRAW = _pal(z16.BRASS)      # жухлая трава
WOOD = _pal(z16.METAL)       # дерево, сухая грязь
DIRT = _pal(z16.DARK)        # тёмная грязь
BLOOD = _pal(z16.RED)
ROT = _pal(z16.VIOLET)       # ряска, мох, армейская краска
ROT_D = _pal(z16.PLUM)       # тень зелёного
NAVY, SKY = _pal(z16.NAVY), _pal(z16.SKY)

EARTH = mix(WOOD, STONE, 0.42)                 # сухая кладбищенская земля
BOARD = mix(mix(WOOD, STONE, 0.55), DIRT, 0.2)  # серая выветренная доска
SLAB = mix(STONE, ROT_D, 0.3)                  # камень ограды, с прозеленью
SLAB = mul(SLAB, 0.86)
MOSS = mix(ROT_D, ROT, 0.35)
ASPHALT = rgb("5C5E66")
MUD = mix(mul(DIRT, 0.72), rgb("2A2420"), 0.3)  # мокрая грязь, заметно темнее асфальта
DRY = mix(ROT_D, STRAW, 0.5)                   # подложка жухлой травы
TARP = mix(ROT_D, ROT, 0.3)                    # армейский брезент
RUST = rgb("9A4E26")


def _arr(color):
    return np.array(color, dtype=np.float32)


def _leaf(p, x, y, ln, ang, color):
    """Палый лист: острый овал с тенью под ним и жилкой вдоль."""
    dx, dy = np.cos(ang) * ln / 2.0, np.sin(ang) * ln / 2.0
    nx, ny = -np.sin(ang) * ln * 0.24, np.cos(ang) * ln * 0.24
    for ox, oy, col, hh in ((0.14, 0.2, None, 112), (0.0, 0.0, color, 166)):
        pts = [(x - dx + ox, y - dy + oy), (x - dx * 0.2 + nx + ox, y - dy * 0.2 + ny + oy),
               (x + dx + ox, y + dy + oy), (x - dx * 0.2 - nx + ox, y - dy * 0.2 - ny + oy)]
        p.poly(pts, col if col else mul(EARTH, 0.66), hh)
    p.line([(x - dx * 0.8, y - dy * 0.8), (x + dx * 0.9, y + dy * 0.9)], mul(color, 0.66), 0.1, 158)


def _bone(p, x, y, ln, ang, color, ground):
    """Кость: стержень с двумя суставными головками на каждом конце, тень на земле."""
    dx, dy = np.cos(ang) * ln / 2.0, np.sin(ang) * ln / 2.0
    nx, ny = -np.sin(ang) * 0.3, np.cos(ang) * 0.3
    p.line([(x - dx + 0.16, y - dy + 0.24), (x + dx + 0.16, y + dy + 0.24)], mul(ground, 0.6), 0.42, 108)
    p.line([(x - dx, y - dy), (x + dx, y + dy)], color, 0.34, 190)
    for s in (-1.0, 1.0):
        for t in (-1.0, 1.0):
            p.ellipse(x + dx * s + nx * t, y + dy * s + ny * t, 0.3, 0.3, color, 198)
    p.line([(x - dx * 0.7, y - dy * 0.7 - 0.06), (x + dx * 0.7, y + dy * 0.7 - 0.06)], mix(color, (255, 255, 255), 0.5), 0.1, 200)


def paint_sand():
    """Кладбищенская земля: сухая серо-бурая глина, трещинки, палая листва, мелкие кости,
    камешки и редкие сухие травинки."""
    p = rm.Paint(801)
    base = _arr(EARTH)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(14, 3), p.tile_noise(40, 2)

    def fn(gx, gy):
        # Плотные светлые плеши и рыхлые тёмные места.
        tone = 1.0 + 0.09 * low + 0.07 * mid + 0.04 * fine
        return base[None, None, :] * tone[..., None], 128.0 + low * 14.0 + mid * 16.0 + fine * 10.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2400, mul(EARTH, 0.8), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 1500, mul(EARTH, 1.12), 0.06)
    # Трещины пересохшей корки.
    p.wrinkles(4, 4, 56, 56, 16, 5.0, 1.3, 0.72, 46)
    for _ in range(30):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.25, 0.62)
        p.ellipse(x + 0.14, y + 0.18, r, r * 0.8, mul(EARTH, 0.62), 110)
        p.ellipse(x, y, r, r * 0.8, mul(STONE, 0.8) if p.rng.random() < 0.6 else STONE, 190)
        p.ellipse(x - r * 0.25, y - r * 0.25, r * 0.4, r * 0.3, mix(STONE, BONE, 0.5), 196)
    # Листва: бурая, охристая и редкая багровая.
    leaves = (mix(WOOD, DIRT, 0.35), mix(STRAW, WOOD, 0.4), mix(STRAW, LABEL, 0.3), mix(DIRT, BLOOD, 0.3))
    for _ in range(46):
        x, y = p.rng.uniform(3.5, 60.5), p.rng.uniform(3.5, 60.5)
        _leaf(p, x, y, p.rng.uniform(1.5, 2.6), p.rng.uniform(0.0, 3.14), leaves[int(p.rng.integers(0, 4))])
    for _ in range(7):
        x, y = p.rng.uniform(6, 58), p.rng.uniform(6, 58)
        _bone(p, x, y, p.rng.uniform(2.2, 3.4), p.rng.uniform(0.0, 3.14), mix(BONE, EARTH, 0.22), EARTH)
    # Сухие травинки пучками.
    for _ in range(10):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(6, 59)
        for _ in range(5):
            lean = p.rng.uniform(-0.9, 0.9)
            p.line([(x + lean * 0.3, y), (x + lean, y - p.rng.uniform(0.8, 1.6))], STRAW if p.rng.random() < 0.6 else mul(STRAW, 0.7), 0.14, 160)
    return p


def paint_planks():
    """Мостки из гробовых досок: шесть серых выветренных досок, стыки вразбежку, ржавые гвозди
    с потёками, продольные трещины, сучки, мох в щелях и бурое пятно."""
    p = rm.Paint(803)
    boards = 6
    width = 64.0 / boards
    p.wood(0, 0, 64, 64, boards, True, BOARD, 0.4)
    # Продольные трещины: сухая доска лопается вдоль волокон.
    for _ in range(11):
        i = int(p.rng.integers(0, boards))
        x = (i + p.rng.uniform(0.25, 0.75)) * width
        y0 = p.rng.uniform(4, 44)
        ln = p.rng.uniform(6, 15)
        p.fold([(x, y0), (x + p.rng.uniform(-0.3, 0.3), y0 + ln * 0.5), (x + p.rng.uniform(-0.3, 0.3), y0 + ln)], 0.3, 0.55, 64)
    # Сучки.
    for _ in range(7):
        i = int(p.rng.integers(0, boards))
        x, y = (i + p.rng.uniform(0.3, 0.7)) * width, p.rng.choice([p.rng.uniform(6, 12), p.rng.uniform(20, 26), p.rng.uniform(38, 44), p.rng.uniform(52, 58)])
        p.ellipse(x, y, 0.9, 1.4, mul(BOARD, 0.74), 110)
        p.ellipse(x, y, 0.5, 0.8, mul(BOARD, 0.5), 96)
        p.ellipse(x, y, 0.18, 0.3, mul(BOARD, 0.32), 86)
    # Мох в щелях между досками, не у края плитки.
    for i in range(1, boards):
        for _ in range(5):
            y = p.rng.uniform(4, 60)
            p.speckle(i * width - 0.6, y - 1.6, 1.2, 3.2, 26, MOSS if p.rng.random() < 0.6 else mul(MOSS, 0.7), 0.16)
    p.stains(2, 2, 60, 60, 14, 2.4, 0.86)
    # Бурое засохшее пятно с брызгами.
    stain = mix(mul(BLOOD, 0.5), BOARD, 0.45)
    for ox, oy, r in ((0.0, 0.0, 2.3), (1.9, 1.0, 1.5), (-1.5, 1.6, 1.2), (0.6, -1.7, 1.0)):
        p.ellipse(40.0 + ox, 36.0 + oy, r, r * 0.8, stain)
    p.speckle(34.0, 31.0, 13.0, 10.0, 30, stain, 0.22)
    p.grain(33.0, 30.0, 15.0, 12.0, 0.08, 0.6, 4.0)
    # Торцевые стыки досок вразбежку и по паре ржавых гвоздей у каждого торца.
    nail, nail_l = mul(RUST, 0.6), mix(RUST, STONE, 0.5)
    for i in range(boards):
        y = 32.0 if i % 2 == 0 else 63.5
        p.fold([(i * width + 0.5, y), ((i + 1) * width - 0.5, y)], 0.45, 0.45, 84)
        for nx in (0.26, 0.74):
            for ny in (-1.8, 1.8):
                cx = i * width + nx * width
                cy = min(max(y + ny - (0.0 if y < 60 else 1.2), 0.9), 62.6)
                # Потёк ржавчины вниз от шляпки.
                if cy < 58:
                    p.line([(cx, cy), (cx + 0.1, cy + p.rng.uniform(1.6, 3.4))], mix(RUST, BOARD, 0.45), 0.3)
                p.ellipse(cx, cy, 0.44, 0.44, mul(BOARD, 0.5), 104)
                p.ellipse(cx, cy, 0.34, 0.34, nail, 172)
                p.ellipse(cx - 0.1, cy - 0.1, 0.12, 0.12, nail_l)
    return p


def paint_water():
    """Болотная жижа: плавные волны от чёрно-зелёной глубины к бледным туманным гребням, острова
    ряски (тем же полем, без отдельных деталей)."""
    p = rm.Paint(805)
    deep, mid, crest = _arr(rgb("14261C")), _arr(mix(ROT_D, rgb("2A4A36"), 0.5)), _arr(mix(ROT, BONE, 0.42))
    weed = _arr(mul(ROT, 0.82))
    noise, patch, dots = p.tile_noise(8, 3), p.tile_noise(7, 3), p.tile_noise(36, 2)

    def fn(gx, gy):
        w = np.sin((gx + 5.0 * np.sin(gy * np.pi / 16.0)) * np.pi / 16.0) + np.sin((gy * 2.0 - gx) * np.pi / 16.0) + 0.6 * noise
        t = rm._smooth_np(np.clip((w + 1.3) / 2.8, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 1.75) / 0.5, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - top[..., None]) + crest[None, None, :] * top[..., None]
        # Ряска: пятна по крупному шуму, внутри них россыпь листочков по мелкому.
        scum = rm._smooth_np(np.clip((patch - 0.42) / 0.4, 0.0, 1.0)) * rm._smooth_np(np.clip((dots + 0.1) / 0.5, 0.0, 1.0))
        color = color * (1.0 - 0.8 * scum[..., None]) + weed[None, None, :] * (0.8 * scum * (0.9 + 0.2 * noise))[..., None]
        return color, 128.0 + w * 30.0 + scum * 14.0
    p.field(fn)
    return p


def paint_bricks():
    """Кладка кладбищенской ограды: серо-зелёные блоки со сдвигом, тёмные швы, мох по швам и
    сверху блоков, трещины, на нескольких блоках выбит крест."""
    p = rm.Paint(827)
    stone, moss = _arr(SLAB), _arr(MOSS)
    low, mid, fine = p.tile_noise(5, 2), p.tile_noise(16, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.82, 1.16, (8, 4)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        ex = np.minimum(shifted % 16.0, 16.0 - shifted % 16.0)
        ey = np.minimum(gy % 8.0, 8.0 - gy % 8.0)
        seam = np.clip(np.minimum(ex, ey) / 0.5, 0.0, 1.0)
        # Свет сверху: верхняя кромка блока светлее, нижняя в тени.
        lit = 1.0 + 0.09 * np.clip(1.0 - (gy % 8.0) / 2.0, 0.0, 1.0) - 0.07 * np.clip(1.0 - (8.0 - gy % 8.0) / 1.6, 0.0, 1.0)
        tone = tones[row, col] * (1.0 + 0.1 * mid + 0.06 * fine) * (0.36 + 0.64 * seam) * lit
        # Мох ползёт из швов и ложится на верх блока там, где сыро.
        near = np.clip(1.0 - np.minimum(ex, gy % 8.0) / 2.6, 0.0, 1.0)
        green = rm._smooth_np(np.clip((low * 0.7 + mid * 0.45 + near * 0.75 - 0.62) / 0.3, 0.0, 1.0))
        color = stone[None, None, :] * tone[..., None]
        color = color * (1.0 - green[..., None]) + moss[None, None, :] * (green * (0.8 + 0.25 * fine))[..., None]
        height = 128.0 + mid * 18.0 + fine * 8.0 - (1.0 - seam) * 80.0 + (tones[row, col] - 1.0) * 60.0 + green * 16.0
        return color, height
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(SLAB, 0.6), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 450, mul(SLAB, 1.4), 0.07)
    p.wrinkles(2, 2, 60, 60, 10, 3.4, 1.1, 0.58, 64)
    # Выбитые кресты: по одному на блок, блок целиком внутри плитки.
    for row, col in ((1, 1), (2, 3), (4, 0), (5, 2), (6, 1)):
        x0 = (col * 16.0 - (row % 2) * 8.0) % 64.0
        cx, cy = x0 + 8.0, row * 8.0 + 4.1
        cut, lip = mul(SLAB, 0.42), mul(SLAB, 1.34)
        # Светлая фаска снизу и справа, потом сама выемка.
        p.rect(cx - 0.45, cy - 2.5, 1.2, 5.3, lip, 150)
        p.rect(cx - 1.75, cy - 1.45, 3.8, 1.2, lip, 150)
        p.rect(cx - 0.6, cy - 2.7, 1.2, 5.3, cut, 62)
        p.rect(cx - 1.9, cy - 1.6, 3.8, 1.1, cut, 62)
    # Потёки сырости под швами.
    p.stains(3, 3, 58, 58, 10, 2.2, 0.84)
    return p


def _skull(p, cx, cy, s, bone, ground):
    """Череп в срезе земли, анфас: свод, скулы, глазницы, нос и ряд зубов."""
    dark = mul(ground, 0.42)
    p.ellipse(cx + 0.3 * s, cy + 0.4 * s, 3.3 * s, 3.1 * s, mul(ground, 0.62), 100)
    p.ellipse(cx, cy, 3.1 * s, 2.8 * s, bone, 196)
    p.poly([(cx - 2.3 * s, cy + 1.2 * s), (cx + 2.3 * s, cy + 1.2 * s), (cx + 1.6 * s, cy + 4.0 * s), (cx - 1.6 * s, cy + 4.0 * s)], bone, 190)
    p.ellipse(cx - 0.9 * s, cy - 1.0 * s, 1.5 * s, 1.1 * s, mix(bone, (255, 255, 255), 0.4), 204)
    for side in (-1.0, 1.0):
        p.ellipse(cx + side * 1.3 * s, cy + 0.7 * s, 0.95 * s, 0.85 * s, dark, 96)
    p.poly([(cx, cy + 1.5 * s), (cx + 0.5 * s, cy + 2.6 * s), (cx - 0.5 * s, cy + 2.6 * s)], dark, 100)
    p.rect(cx - 1.5 * s, cy + 3.1 * s, 3.0 * s, 0.22 * s, dark, 120)
    for i in range(1, 5):
        p.rect(cx - 1.5 * s + i * 0.6 * s - 0.07 * s, cy + 3.1 * s, 0.14 * s, 0.9 * s, dark, 120)


def paint_cliff():
    """Обрыв: срез кладбищенской земли пластами (дёрн, глина, щебень), вросшие камни, корни
    сверху вниз, череп и россыпь костей."""
    p = rm.Paint(831)
    clay, loam, gravel = _arr(mul(WOOD, 0.74)), _arr(mul(DIRT, 0.9)), _arr(mix(mul(STONE, 0.6), WOOD, 0.3))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(10, 3), p.tile_noise(30, 2)

    def fn(gx, gy):
        phase = gy / 64.0 * 4.0 + low * 0.5 + mid * 0.16
        band = phase - np.floor(phase)
        ledge = np.clip(band / 0.14, 0.0, 1.0) * np.clip((1.0 - band) / 0.55, 0.0, 1.0)
        kind = np.floor(phase) % 4.0
        k1 = ((kind == 1.0) | (kind == 3.0)).astype(np.float32)[..., None]
        k2 = (kind == 2.0).astype(np.float32)[..., None]
        color = loam[None, None, :] * (1.0 - k1 - k2) + clay[None, None, :] * k1 + gravel[None, None, :] * k2
        tone = (0.7 + 0.3 * ledge) * (1.0 + 0.14 * mid + 0.09 * fine)
        return color * tone[..., None], 128.0 + ledge * 58.0 - 38.0 + mid * 26.0 + fine * 14.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(DIRT, 0.6), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 600, mix(WOOD, STONE, 0.4), 0.09)
    p.wrinkles(1, 1, 62, 62, 12, 7.0, 1.2, 0.6, 60)
    # Вросшие камни со светом сверху.
    for _ in range(18):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        rx = p.rng.uniform(0.7, 1.9)
        ry = rx * p.rng.uniform(0.55, 0.8)
        col = mul(STONE, p.rng.uniform(0.5, 0.72))
        p.ellipse(x + 0.2, y + 0.34, rx * 1.06, ry * 1.06, mul(DIRT, 0.5), 96)
        p.ellipse(x, y, rx, ry, col, 196)
        p.ellipse(x - rx * 0.2, y - ry * 0.3, rx * 0.55, ry * 0.4, mul(col, 1.3), 206)
    # Корни: бурые жилы сверху вниз, ветвятся и тоньшают.
    root, root_l = mix(mul(WOOD, 0.62), DIRT, 0.4), mul(WOOD, 0.95)
    for x0 in (9.0, 24.0, 37.0, 55.0):
        x, y = x0 + p.rng.uniform(-1.5, 1.5), p.rng.uniform(3.0, 9.0)
        pts = [(x, y)]
        for _ in range(7):
            x, y = x + p.rng.uniform(-2.2, 2.2), y + p.rng.uniform(3.0, 5.2)
            pts.append((min(max(x, 3.0), 61.0), min(y, 60.5)))
        for i in range(len(pts) - 1):
            wd = 0.85 - i * 0.09
            seg = [pts[i], pts[i + 1]]
            p.line([(a + 0.2, b + 0.3) for a, b in seg], mul(DIRT, 0.5), wd + 0.2, 100)
            p.line(seg, root, wd, 186)
            p.line([(a - wd * 0.2, b) for a, b in seg], root_l, wd * 0.3, 196)
        # Боковой отросток.
        bx, by = pts[3]
        side = 1.0 if x0 < 32 else -1.0
        twig = [(bx, by), (bx + side * 2.4, by + 1.6), (bx + side * 3.6, by + 4.0)]
        p.line(twig, root, 0.4, 178)
    # Кости и череп: тонированы землёй, чтобы не спорить с героем.
    bone = mix(BONE, mul(WOOD, 0.8), 0.3)
    _skull(p, 45.5, 27.0, 1.0, bone, mul(DIRT, 0.9))
    for x, y, ln, ang in ((16.0, 20.0, 5.0, 0.35), (30.0, 47.0, 4.4, -0.5), (51.0, 50.0, 3.6, 1.2), (12.0, 52.0, 3.2, 0.1)):
        _bone(p, x, y, ln, ang, bone, mul(DIRT, 0.9))
    # Рёбра дугами рядом с черепом пониже.
    for i in range(4):
        y = 37.0 + i * 1.5
        pts = [(41.0 + 4.6 * np.cos(a), y + 1.0 * np.sin(a)) for a in np.linspace(3.5, 5.9, 8)]
        p.line(pts, bone, 0.32, 186)
    return p


def paint_grass():
    """Жухлая трава: бурая подложка с зелёными плешами, сухие охристые стебли, метёлки бурьяна,
    колючие головки репейника."""
    p = rm.Paint(829)
    base, wet = _arr(DRY), _arr(mix(ROT_D, ROT, 0.2))
    low, mid = p.tile_noise(4, 3), p.tile_noise(16, 3)

    def fn(gx, gy):
        # Зелёные плеши там, где сыро, остальное выгорело в бурое.
        damp = 0.5 * rm._smooth_np(np.clip((low + 0.2 * mid - 0.05) / 0.8, 0.0, 1.0))[..., None]
        tone = 1.0 + 0.14 * low + 0.1 * mid
        return (base[None, None, :] * (1.0 - damp) + wet[None, None, :] * damp) * tone[..., None], 128.0 + low * 20.0 + mid * 12.0
    p.field(fn)
    dark, pale, green = mul(DRY, 0.55), mix(STRAW, LABEL, 0.6), mix(ROT_D, ROT, 0.25)
    for _ in range(1500):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.6, 63)
        lean = p.rng.uniform(-0.45, 0.45)
        pick = p.rng.random()
        col = dark if pick < 0.4 else (pale if pick < 0.75 else (STRAW if pick < 0.9 else green))
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.7, 1.7))], col, 0.15, 150)
    # Бурьян: высокий стебель с метёлкой из коротких штрихов.
    for _ in range(20):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(8, 60)
        lean = p.rng.uniform(-0.8, 0.8)
        top = (x + lean, y - p.rng.uniform(3.0, 4.6))
        p.line([(x + 0.14, y + 0.1), (top[0] + 0.14, top[1] + 0.2)], dark, 0.2, 130)
        p.line([(x, y), top], mix(STRAW, BONE, 0.25), 0.2, 176)
        for k in range(5):
            t = k / 4.0
            sx, sy = x + lean * (0.55 + 0.45 * t), y + (top[1] - y) * (0.55 + 0.45 * t)
            for side in (-1.0, 1.0):
                p.line([(sx, sy), (sx + side * 0.8, sy - 0.55)], mix(pale, BONE, 0.3), 0.16, 182)
    # Репейник: бурая колючая головка на коротком стебле.
    bur = mix(DIRT, WOOD, 0.4)
    for _ in range(12):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(5, 60)
        p.line([(x, y + 1.4), (x, y)], mul(STRAW, 0.7), 0.15, 170)
        for a in np.linspace(0.0, 6.28, 9)[:-1]:
            p.line([(x, y), (x + 0.75 * np.cos(a), y + 0.75 * np.sin(a))], mul(bur, 1.3), 0.11, 186)
        p.ellipse(x, y, 0.5, 0.5, mul(bur, 0.8), 196)
        p.ellipse(x - 0.14, y - 0.14, 0.16, 0.16, mul(bur, 1.5), 200)
    return p


def paint_road():
    """Битый асфальт: крупное зерно щебня, две накатанные колеи, стёртый жёлтый пунктир по оси,
    трещины, залитые битумом, заплата, масляные пятна и след торможения."""
    p = rm._ground(833, ASPHALT, 0.08, 0.06, 12.0)
    p.speckle(0.5, 0.5, 63, 63, 2200, mul(ASPHALT, 0.74), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 1300, mul(ASPHALT, 1.22), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 260, mix(ASPHALT, STONE, 0.7), 0.1)
    # Заплата свежего асфальта: темнее, с ровным швом.
    p.rect(6.0, 40.0, 9.0, 12.0, mul(ASPHALT, 0.8), 132)
    p.speckle(6.2, 40.2, 8.6, 11.6, 160, mul(ASPHALT, 0.62), 0.08)
    p.speckle(6.2, 40.2, 8.6, 11.6, 90, mul(ASPHALT, 1.0), 0.07)
    p.fold([(6.0, 40.0), (15.0, 40.0), (15.0, 52.0), (6.0, 52.0), (6.0, 40.0)], 0.3, 0.6, 40)
    # Колеи: укатанные тёмные полосы.
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.8, 0.84, 26)
    # Пунктир по оси, краска стёрта и потрескалась.
    paint = mix(LABEL, ASPHALT, 0.25)
    for y in (6.0, 38.0):
        p.band(31.3, y, 1.4, 12.0, paint, 138, 0.1)
        p.speckle(31.2, y, 1.6, 12.0, 46, ASPHALT, 0.16)
        p.speckle(31.2, y, 1.6, 12.0, 20, mul(paint, 1.12), 0.1)
    # След торможения вдоль правой колеи.
    for dx in (-1.0, 1.0):
        p.fold([(45.0 + dx, 4.0), (45.3 + dx, 14.0), (46.2 + dx, 24.0)], 0.7, 0.66, 8)
    # Трещины: ломаные с ответвлениями, залиты битумом.
    for pts in ([(22.0, 5.0), (25.0, 9.0), (24.0, 14.0), (28.0, 19.0), (27.0, 25.0)],
                [(28.0, 19.0), (33.5, 21.0), (37.0, 20.0)],
                [(50.0, 34.0), (53.0, 39.0), (51.5, 44.0), (56.0, 50.0), (55.0, 58.0)],
                [(53.0, 39.0), (58.0, 38.0), (60.5, 40.0)],
                [(18.0, 30.0), (21.0, 33.0), (26.0, 33.5), (28.0, 37.0)],
                [(36.0, 54.0), (39.0, 57.0), (43.0, 56.5), (46.0, 60.0)]):
        # Ломаная дробится и дрожит: трещина не идёт по линейке.
        rough = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            for t in (0.25, 0.5, 0.75):
                rough.append((ax + (bx - ax) * t + p.rng.uniform(-0.5, 0.5), ay + (by - ay) * t + p.rng.uniform(-0.5, 0.5)))
            rough.append((bx, by))
        p.fold(rough, 0.3, 0.5, 70)
    p.wrinkles(3, 3, 58, 58, 8, 3.0, 1.2, 0.68, 44)
    # Масляные пятна.
    p.stains(3, 3, 58, 58, 9, 3.0, 0.82)
    return p


def paint_mud():
    """Мокрая грязь: тёмное месиво с буграми, лужи с лунным бликом, комья, зелёная слизь по краям
    луж. Заметно темнее асфальта."""
    p = rm.Paint(835)
    base = _arr(MUD)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(12, 3), p.tile_noise(36, 2)

    def fn(gx, gy):
        # Месиво: бугры и вмятины без направления.
        lump = np.sin(2 * np.pi * (gx * 3.0 / UNITS + 0.5 * mid)) * np.sin(2 * np.pi * (gy * 4.0 / UNITS + 0.5 * low))
        tone = 1.0 + 0.16 * lump + 0.14 * low + 0.1 * mid + 0.06 * fine
        return base[None, None, :] * tone[..., None], 128.0 + lump * 30.0 + mid * 20.0 + fine * 10.0
    p.field(fn)
    glint = mix(SKY, NAVY, 0.45)
    for _ in range(9):
        x, y = p.rng.uniform(9, 55), p.rng.uniform(9, 55)
        rx, ry = p.rng.uniform(2.6, 5.4), p.rng.uniform(1.5, 3.0)
        # Слизь по берегу, вода, отражение луны.
        p.speckle(x - rx * 1.2, y - ry * 1.2, rx * 2.4, ry * 2.4, 26, mul(MOSS, 0.7), 0.18)
        p.ellipse(x, y, rx * 1.12, ry * 1.14, mul(MUD, 1.26), 122)
        p.ellipse(x, y, rx, ry, mul(MUD, 0.52), 78)
        p.ellipse(x + rx * 0.08, y + ry * 0.12, rx * 0.8, ry * 0.74, mix(mul(MUD, 0.5), NAVY, 0.4), 76)
        p.ellipse(x - rx * 0.3, y - ry * 0.3, rx * 0.34, ry * 0.2, glint, 76)
    # Комья со светом сверху.
    for _ in range(90):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 62)
        r = p.rng.uniform(0.3, 0.7)
        p.ellipse(x + 0.12, y + 0.2, r, r * 0.75, mul(MUD, 0.5), 108)
        p.ellipse(x, y, r, r * 0.75, mul(MUD, p.rng.uniform(1.0, 1.3)), 176)
        p.ellipse(x - r * 0.2, y - r * 0.25, r * 0.4, r * 0.28, mul(MUD, 1.8), 184)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(MUD, 1.5), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(MUD, 0.5), 0.1)
    return p


def paint_sail():
    """Армейский брезент: зелёная плотная ткань, швы полотнищ со строчкой и люверсами, складки
    от скатки, две заплаты (серая тряпка и кожа), грязь и бурые брызги."""
    p = rm._ground(837, TARP, 0.07, 0.05, 12.0)
    p.weave(0, 0, 64, 64, 0.4, 0.08)
    # Складки от скатки: сетка заломов.
    for y in (16.0, 48.0):
        p.fold([(0, y), (64, y)], 0.4, 0.84, 30)
    p.wrinkles(2, 2, 60, 60, 26, 4.0, 1.2, 0.84, 30)
    # Швы полотнищ: подгиб, двойная строчка, люверсы.
    thread, ring = mix(TARP, BONE, 0.55), mix(STONE, WOOD, 0.3)
    for x in (0.4, 32.0):
        p.rect(x, 0.0, 2.4, 64.0, mul(TARP, 0.9), 140)
        p.fold([(x, 0), (x, 64)], 0.5, 0.7, 50)
        p.fold([(x + 2.5, 0), (x + 2.5, 64)], 0.3, 0.8, 30)
        p.stitch([(x + 0.7, 0.4), (x + 0.7, 63.6)], thread, 0.14, 0.8)
        p.stitch([(x + 1.8, 0.4), (x + 1.8, 63.6)], thread, 0.14, 0.8)
        for y in (8.0, 24.0, 40.0, 56.0):
            p.ellipse(x + 1.25, y, 0.72, 0.72, ring, 176)
            p.ellipse(x + 1.1, y - 0.14, 0.5, 0.5, mul(ring, 1.3), 180)
            p.ellipse(x + 1.25, y, 0.34, 0.34, mul(TARP, 0.3), 70)
    # Заплата из серой тряпки, пришита крупно и криво.
    rag = mix(STONE, TARP, 0.25)
    p.poly([(10.0, 25.6), (19.6, 24.8), (20.2, 33.4), (10.6, 34.2)], rag, 152)
    p.weave(10.6, 25.8, 9.0, 7.6, 0.5, 0.08, 8.0)
    for (ax, ay), (bx, by) in (((10.0, 25.6), (19.6, 24.8)), ((19.6, 24.8), (20.2, 33.4)), ((20.2, 33.4), (10.6, 34.2)), ((10.6, 34.2), (10.0, 25.6))):
        n = 6
        for i in range(n):
            t = (i + 0.5) / n
            mx, my = ax + (bx - ax) * t, ay + (by - ay) * t
            p.line([(mx - 0.5, my - 0.5), (mx + 0.5, my + 0.5)], mul(TARP, 0.36), 0.16, 160)
    # Кожаная заплата поменьше с крестом из ниток.
    hide = mix(WOOD, DIRT, 0.3)
    p.poly([(44.0, 43.0), (51.0, 43.6), (50.4, 49.6), (43.6, 49.0)], hide, 154)
    p.stitch([(44.4, 43.5), (50.5, 44.0), (50.0, 49.1), (44.1, 48.6), (44.4, 43.5)], thread, 0.14, 0.7)
    p.line([(45.6, 44.8), (49.0, 48.0)], thread, 0.16, 162)
    p.line([(49.0, 44.9), (45.6, 47.9)], thread, 0.16, 162)
    p.stains(3, 3, 58, 58, 10, 2.6, 0.86)
    # Бурые брызги.
    spot = mix(mul(BLOOD, 0.55), TARP, 0.35)
    p.ellipse(41.0, 14.0, 1.5, 1.1, spot)
    p.ellipse(42.6, 15.2, 0.8, 0.7, spot)
    p.speckle(36.0, 9.0, 12.0, 11.0, 28, spot, 0.2)
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
