#!/usr/bin/env python3
"""Текстуры уровня «Динозавров» для «продвинутых» (#144): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Динозавры
у «продвинутых» это доисторический день у вулкана: красная глина, растрескавшаяся такыром, со
следами раптора и ракушкой аммонита; настил из колотых брёвен, стянутых лианой на стыках; лава
вместо воды, от тёмной корки к жёлтым гребням жара; кладка из окатанных глыб лавового камня с
зелёным мхом в швах и костями в камне; слоистый обрыв из глины, охры и пепла с окаменелым
хребтом в пласте; лесная подстилка с вайями папоротника и палыми листьями; дорога из плит
лавового камня с колеями там же, где колеи у пиратов, и костями вместо пунктира по оси; вязкий
вулканический пепел с лужами смолы и тлеющими угольками (заметно темнее дороги); и растянутая
пятнистая шкура с жильной строчкой по шву (слот `tex_sail`: у динозавров это шкуры тотемов и
навесов, парусов в сеттинге нет). Плитки стыкуются по краям: поля считаются на периодическом
шуме и периодических решётках, отдельные детали не подходят к краю. Цвета из палитры основы
16/32 (`dinosaurs16.PALETTE`) через `dinosaurs_mesh_chars`.

    python3 tools/dinosaurs_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import dinosaurs_mesh_chars as dmc  # noqa: E402

rgb, mul, UNITS = rm.rgb, rm.mul, rm.UNITS


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


BONE, BONE_D, BONE_DD = dmc.BONE, dmc.BONE_D, dmc.BONE_DD
HIDE, HIDE_D, HIDE_L = dmc.HIDE, dmc.HIDE_D, dmc.HIDE_L
HAIR, HAIR_D = dmc.HAIR, dmc.HAIR_D
LEAF, LEAF_D, LEAF_L = dmc.SCALE, dmc.SCALE_D, dmc.SCALE_L
GOLD, BRASS = dmc.BELLY, dmc.BELLY_D
STONE, STONE_D = dmc.STONE, dmc.STONE_D
CLAY = mix(dmc.SKIN_D, dmc.SKIN, 0.42)    # красная глина на свету: земля островов и дюны
CLAY_D = dmc.CLAY
OCHRE = rgb("C89A54")
LITTER = mix(LEAF, LEAF_D, 0.62)          # подстилка джунглей
SLAB = rgb("94828A")                      # плиты дороги: лавовый камень, вытертый до светлого
ASH = rgb("3A2C2C")                       # вязкий пепел
LOG = rgb("8E5A34")                       # колотое бревно


def _arr(color):
    return np.array(color, dtype=np.float32)


def _ammonite(p, cx, cy, r, shell, turn=0.0):
    """Ракушка аммонита: спираль в два с половиной оборота, поперечные рёбра, тень под ней."""
    p.ellipse(cx + r * 0.1, cy + r * 0.14, r * 1.02, r * 1.02, mul(shell, 0.42), 96)
    steps = 46
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = turn + t * math.pi * 5.0
        rad = r * (1.0 - 0.86 * t)
        pts.append((cx + math.cos(a) * rad * 0.82, cy + math.sin(a) * rad * 0.82, rad))
    for i in range(steps):
        (x0, y0, r0), (x1, y1, _) = pts[i], pts[i + 1]
        p.line([(x0, y0), (x1, y1)], mul(shell, 0.62), max(r0 * 0.5, 0.2), 150)
    for i in range(steps):
        (x0, y0, r0), (x1, y1, _) = pts[i], pts[i + 1]
        p.line([(x0, y0), (x1, y1)], shell if i % 2 else mul(shell, 0.84), max(r0 * 0.34, 0.12), 176)
    p.ellipse(cx, cy, r * 0.1, r * 0.1, mul(shell, 0.5), 140)


def _track(p, x, y, size, turn, dark):
    """След раптора: три пальца веером с когтями и пятка, вдавлен в грунт."""
    for da, ln in ((-0.5, 0.86), (0.0, 1.0), (0.5, 0.86)):
        a = turn + da
        ex, ey = x + math.sin(a) * size * ln, y - math.cos(a) * size * ln
        p.line([(x, y), (ex, ey)], dark, size * 0.26, 78)
        p.ellipse(ex, ey, size * 0.15, size * 0.15, dark, 72)
        p.line([(ex, ey), (ex + math.sin(a) * size * 0.24, ey - math.cos(a) * size * 0.24)], mul(dark, 0.8), size * 0.1, 70)
    hx, hy = x - math.sin(turn) * size * 0.2, y + math.cos(turn) * size * 0.2
    p.ellipse(hx, hy, size * 0.26, size * 0.26, dark, 74)


def _bone(p, x0, y0, x1, y1, width, color=None):
    """Кость: стержень с двумя шишками на каждом конце и тенью снизу."""
    color = color or BONE
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    p.line([(x0 + 0.16, y0 + 0.22), (x1 + 0.16, y1 + 0.22)], mul(BONE_DD, 0.5), width * 1.2, 100)
    for ex, ey in ((x0, y0), (x1, y1)):
        for s in (-1.0, 1.0):
            p.ellipse(ex + nx * width * 0.5 * s, ey + ny * width * 0.5 * s, width * 0.62, width * 0.62, BONE_D, 176)
    p.line([(x0, y0), (x1, y1)], BONE_D, width, 180)
    p.line([(x0 - nx * width * 0.16, y0 - ny * width * 0.16), (x1 - nx * width * 0.16, y1 - ny * width * 0.16)], color, width * 0.6, 196)
    for ex, ey in ((x0, y0), (x1, y1)):
        for s in (-1.0, 1.0):
            p.ellipse(ex + nx * width * 0.5 * s - 0.08, ey + ny * width * 0.5 * s - 0.08, width * 0.4, width * 0.4, color, 196)


def _frond(p, x, y, length, turn, color, vein):
    """Вайя папоротника: стебель дугой и парные листочки, к концу короче."""
    steps = 9
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = turn + 0.5 * t * t
        pts.append((x + math.sin(a) * length * t, y - math.cos(a) * length * t, a))
    for i in range(1, steps + 1):
        px, py, a = pts[i]
        t = i / steps
        leaf = length * 0.36 * (1.0 - t * 0.82) * min(t * 4.0, 1.0)
        for s in (-1.0, 1.0):
            la = a + s * 1.15
            ex, ey = px + math.sin(la) * leaf, py - math.cos(la) * leaf
            mx, my = px + math.sin(la - s * 0.3) * leaf * 0.55, py - math.cos(la - s * 0.3) * leaf * 0.55
            p.poly([(px, py), (mx - math.cos(la) * 0.3, my - math.sin(la) * 0.3), (ex, ey),
                    (mx + math.cos(la) * 0.3, my + math.sin(la) * 0.3)], color, 156)
    p.line([(px, py) for px, py, _ in pts], vein, 0.2, 168)


def paint_sand():
    """Красная глина: такыр из плиток с тёмными трещинами, зерно, галька, следы раптора, аммонит."""
    p = rm.Paint(601)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(40, 2)
    base, pale = _arr(CLAY), _arr(mix(CLAY, OCHRE, 0.7))
    # Узлы плиток такыра: решётка 5×5 со сдвигом, расстояния считаются по тору, плитка стыкуется.
    cells = 5
    step = UNITS / cells
    nodes = [((i + p.rng.uniform(0.2, 0.8)) * step, (j + p.rng.uniform(0.2, 0.8)) * step) for i in range(cells) for j in range(cells)]

    def fn(gx, gy):
        wx, wy = gx + 1.6 * mid, gy + 1.6 * np.roll(mid, 37, axis=0)
        d1 = np.full(gx.shape, 1e9, dtype=np.float32)
        d2 = np.full(gx.shape, 1e9, dtype=np.float32)
        for nx, ny in nodes:
            dx = np.abs(wx - nx) % UNITS
            dy = np.abs(wy - ny) % UNITS
            dx, dy = np.minimum(dx, UNITS - dx), np.minimum(dy, UNITS - dy)
            d = np.sqrt(dx * dx + dy * dy)
            d2 = np.where(d < d1, d1, np.minimum(d2, d))
            d1 = np.minimum(d1, d)
        # Трещина идёт там, где до двух ближайших узлов одинаково далеко.
        crack = (d2 - d1) / 0.45
        seam = rm._smooth_np(np.clip(crack, 0.0, 1.0))
        lip = np.clip(crack / 5.0, 0.0, 1.0)
        dry = np.clip(low * 0.6 + 0.5, 0.0, 1.0) * 0.4
        color = base[None, None, :] * (1.0 - dry[..., None]) + pale[None, None, :] * dry[..., None]
        tone = (1.0 + 0.07 * low + 0.06 * mid + 0.04 * fine) * (0.5 + 0.5 * seam) * (1.06 - 0.06 * lip)
        return color * tone[..., None], 128.0 + lip * 22.0 - (1.0 - seam) * 74.0 + mid * 10.0 + fine * 8.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2200, mul(CLAY, 0.78), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 1400, mul(CLAY, 1.16), 0.06)
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.25, 0.6)
        p.ellipse(x + 0.14, y + 0.18, r, r * 0.8, mul(CLAY, 0.58), 104)
        p.ellipse(x, y, r, r * 0.8, STONE if p.rng.random() < 0.6 else BONE_D, 186)
    # Цепочка следов наискось и одинокий след в стороне.
    dark = mul(CLAY, 0.62)
    for i, (x, y) in enumerate(((14.0, 50.0), (21.0, 40.5), (25.0, 29.0), (32.0, 19.5))):
        _track(p, x, y, 3.0, 0.52 + (0.16 if i % 2 else -0.16), dark)
    _track(p, 49.0, 47.0, 2.2, -0.9, dark)
    _ammonite(p, 47.0, 17.0, 2.6, GOLD, 0.6)
    return p


def paint_planks():
    """Настил: колотые брёвна 32×16 вразбежку, выпуклые, с волокнами и сучками, торцы стянуты лианой."""
    p = rm.Paint(603)
    base = _arr(LOG)
    mid, fine = p.tile_noise(12, 3), p.tile_noise(48, 2)
    tones = p.rng.uniform(0.86, 1.14, (4, 2)).astype(np.float32)
    phases = p.rng.uniform(0.0, 6.28, (4, 2)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 16.0).astype(np.int32), 0, 3)
        shifted = (gx + (row % 2) * 16.0) % 64.0
        col = np.clip((shifted / 32.0).astype(np.int32), 0, 1)
        ex = np.minimum(shifted % 32.0, 32.0 - shifted % 32.0)
        v = (gy % 16.0) / 16.0
        ey = np.minimum(v, 1.0 - v) * 16.0
        seam = np.clip(np.minimum(ex / 0.5, ey / 0.7), 0.0, 1.0)
        # Бревно круглое поперёк: свет на горбе, тень к щели.
        dome = np.sin(v * np.pi)
        # Волокна вдоль бревна, слегка гуляют; периодичны по плитке.
        ph = phases[row, col]
        fibre = np.sin((v * 9.0 + 0.5 * np.sin(gx * 2 * np.pi / 32.0 + ph) + mid * 0.5) * 2 * np.pi)
        tone = tones[row, col] * (0.62 + 0.42 * dome) * (1.0 + 0.07 * fibre + 0.05 * fine) * (0.4 + 0.6 * seam)
        return base[None, None, :] * tone[..., None], 100.0 + dome * 56.0 + fibre * 7.0 + fine * 5.0 - (1.0 - seam) * 70.0
    p.field(fn)
    vine, vine_l = LEAF_D, mix(LEAF, LEAF_L, 0.4)
    for row in range(4):
        y0 = row * 16.0
        for col in range(2):
            x0 = (col * 32.0 - (row % 2) * 16.0) % 64.0
            # Сучок с годовыми кольцами в середине бревна.
            kx, ky = (x0 + p.rng.uniform(9.0, 23.0)) % 64.0, y0 + p.rng.uniform(5.0, 11.0)
            if 3.0 < kx < 61.0:
                p.ellipse(kx, ky, 1.5, 0.95, mul(LOG, 0.74), 122)
                p.ellipse(kx, ky, 1.0, 0.62, mul(LOG, 0.52), 112)
                p.ellipse(kx, ky, 0.5, 0.3, mul(LOG, 0.86), 118)
            # Обвязка лианой у обоих торцов: три витка поперёк бревна и листок.
            for dx in (2.6, 29.4):
                x = (x0 + dx) % 64.0
                if not 2.0 < x < 62.0:
                    continue
                for k in (-0.7, 0.0, 0.7):
                    p.line([(x + k - 0.3, y0 + 1.0), (x + k + 0.3, y0 + 15.0)], mul(vine, 0.6), 0.62, 150)
                    p.line([(x + k - 0.3, y0 + 1.0), (x + k + 0.3, y0 + 15.0)], vine if k else vine_l, 0.36, 178)
                lx, ly = x + 1.2, y0 + 8.0 + p.rng.uniform(-3.0, 3.0)
                p.poly([(lx - 0.3, ly), (lx + 0.8, ly - 0.7), (lx + 2.0, ly), (lx + 0.8, ly + 0.7)], LEAF, 170)
                p.line([(lx, ly), (lx + 1.8, ly)], LEAF_D, 0.12, 164)
    p.wrinkles(3, 3, 58, 58, 14, 5.0, 0.12, 0.72, 44)
    p.stains(2, 2, 60, 60, 10, 2.4, 0.9)
    return p


def paint_water():
    """Лава: плавные волны от тёмной корки через красный жар к жёлтым гребням."""
    p = rm.Paint(605)
    deep, mid, crest = (_arr(rgb(c)) for c in ("3A1614", "D8481C", "FFE27C"))
    hot = _arr(rgb("F48A2C"))
    noise, skin = p.tile_noise(8, 3), p.tile_noise(20, 2)

    def fn(gx, gy):
        w = np.sin((gx + 6.0 * np.sin(gy * np.pi / 8.0)) * np.pi / 16.0) + np.sin((gy * 2.0 + gx) * np.pi / 16.0) + 0.5 * noise
        t = rm._smooth_np(np.clip((w + 1.1) / 2.2, 0.0, 1.0))
        glow = rm._smooth_np(np.clip((w - 0.7) / 1.1, 0.0, 1.0))
        top = rm._smooth_np(np.clip((w - 1.75) / 0.45, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - glow[..., None]) + hot[None, None, :] * glow[..., None]
        color = color * (1.0 - top[..., None]) + crest[None, None, :] * top[..., None]
        # Корка на остывших местах шершавая, жар гладкий.
        crust = (1.0 - t) * skin
        return color * (1.0 + 0.16 * crust)[..., None], 128.0 + w * 34.0 + crust * 14.0
    p.field(fn)
    return p


def paint_bricks():
    """Кладка из лавового камня (борта, стены): окатанные глыбы со сдвигом, мох в швах, кости в камне."""
    p = rm.Paint(627)
    stone, moss = _arr(STONE), _arr(mix(LEAF, LEAF_D, 0.5))
    mid, fine = p.tile_noise(16, 3), p.tile_noise(40, 2)
    tones = p.rng.uniform(0.82, 1.16, (8, 4)).astype(np.float32)
    warm = p.rng.uniform(0.0, 1.0, (8, 4)).astype(np.float32)
    rust = _arr(mix(STONE, CLAY_D, 0.5))

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        u = np.abs((shifted % 16.0) / 8.0 - 1.0)
        v = np.abs((gy % 8.0) / 4.0 - 1.0)
        # Глыба скруглена: в углах между соседями остаются тёмные карманы со мхом.
        d = (u ** 4.0 + v ** 4.0) ** 0.25 + 0.04 * mid
        seam = rm._smooth_np(np.clip((0.98 - d) / 0.1, 0.0, 1.0))
        dome = np.clip(1.0 - d * d, 0.0, 1.0)
        lit = 1.0 + 0.12 * np.clip(1.0 - (gy % 8.0) / 3.0, 0.0, 1.0)
        k = (warm[row, col] > 0.7).astype(np.float32)[..., None] * 0.6
        body = stone[None, None, :] * (1.0 - k) + rust[None, None, :] * k
        tone = tones[row, col] * (1.0 + 0.1 * mid + 0.06 * fine) * (0.82 + 0.2 * dome) * lit
        green = (1.0 - seam) * np.clip(0.55 + 0.6 * mid, 0.0, 1.0)
        color = body * (tone * (0.34 + 0.66 * seam))[..., None]
        color = color * (1.0 - green[..., None]) + moss[None, None, :] * (green * (0.7 + 0.2 * fine))[..., None]
        return color, 96.0 + dome * 50.0 + mid * 12.0 + fine * 8.0 - (1.0 - seam) * 44.0 + green * 16.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(STONE, 0.6), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(STONE, 1.36), 0.07)
    # Поры лавы: тёмные ямки со светлым краем.
    for _ in range(46):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 62)
        r = p.rng.uniform(0.2, 0.42)
        p.ellipse(x - 0.06, y - 0.06, r * 1.25, r * 1.1, mul(STONE, 1.16))
        p.ellipse(x, y, r, r * 0.86, mul(STONE, 0.46), 84)
    # Окаменелости в середине глыб: аммонит и два обломка кости.
    _ammonite(p, 24.0, 20.0, 2.3, BONE_D, 1.2)
    _bone(p, 37.0, 43.4, 42.6, 44.6, 0.7)
    _bone(p, 52.4, 11.4, 57.2, 12.6, 0.6, BONE_D)
    p.wrinkles(2, 2, 60, 60, 7, 2.6, 0.9, 0.62, 56)
    return p


def paint_cliff():
    """Обрыв: пласты глины, охры и пепла идут волной, трещины, окаменелый хребет с рёбрами в пласте."""
    p = rm.Paint(631)
    clay, ochre, ash = _arr(mul(CLAY_D, 1.06)), _arr(mul(OCHRE, 0.86)), _arr(mul(STONE, 0.86))
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(10, 3), p.tile_noise(28, 2)

    def fn(gx, gy):
        phase = gy / 64.0 * 6.0 + low * 0.5 + mid * 0.14
        band = phase - np.floor(phase)
        index = np.floor(phase).astype(np.int32) % 6
        ledge = np.clip(band / 0.16, 0.0, 1.0) * np.clip((1.0 - band) / 0.5, 0.0, 1.0)
        tone = (0.66 + 0.34 * ledge) * (1.0 + 0.12 * mid + 0.07 * fine)
        # Шесть пластов на плитку: глина, охра, глина, пепел, глина потемнее, охра.
        kind = np.array([0, 1, 0, 2, 0, 1], dtype=np.int32)[index]
        shade = np.array([1.0, 1.0, 0.86, 1.0, 0.74, 0.9], dtype=np.float32)[index]
        color = np.where((kind == 0)[..., None], clay[None, None, :],
                         np.where((kind == 1)[..., None], ochre[None, None, :], ash[None, None, :]))
        # Тонкие прослойки внутри пласта.
        lam = 1.0 + 0.05 * np.sin(phase * 2 * np.pi * 5.0)
        return color * (tone * shade * lam)[..., None], 128.0 + ledge * 62.0 - 40.0 + mid * 26.0 + fine * 12.0
    p.field(fn)
    p.wrinkles(1, 1, 62, 62, 12, 8.0, 1.2, 0.56, 70)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(CLAY_D, 0.5), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 450, mul(OCHRE, 1.14), 0.08)
    # Хребет: позвонки дугой, рёбра вниз, длинный череп с глазницей и зубами.
    spine = []
    for i in range(11):
        t = i / 10.0
        spine.append((16.0 + t * 26.0, 29.0 - math.sin(t * math.pi) * 2.6 + t * 2.0))
    p.line([(x + 0.2, y + 0.3) for x, y in spine], mul(CLAY_D, 0.42), 1.3, 96)
    for i, (x, y) in enumerate(spine):
        t = i / 10.0
        if 0.1 < t < 0.78:
            rib = 5.2 * math.sin((t - 0.1) / 0.68 * math.pi) + 1.6
            pts = [(x, y), (x - 0.7, y + rib * 0.5), (x - 0.2, y + rib)]
            p.line([(a + 0.16, b + 0.2) for a, b in pts], mul(CLAY_D, 0.42), 0.6, 100)
            p.line(pts, BONE_D, 0.42, 176)
            p.line(pts[:2], BONE, 0.22, 190)
        p.ellipse(x, y, 0.8, 0.7, BONE_D, 180)
        p.ellipse(x - 0.12, y - 0.14, 0.48, 0.4, BONE, 194)
    hx, hy = spine[0]
    skull = [(hx + 0.4, hy - 1.7), (hx - 3.2, hy - 1.9), (hx - 7.6, hy - 0.4), (hx - 7.8, hy + 0.7), (hx - 3.0, hy + 1.3),
             (hx + 0.4, hy + 1.1)]
    p.poly([(a + 0.2, b + 0.3) for a, b in skull], mul(CLAY_D, 0.42), 96)
    p.poly(skull, BONE_D, 182)
    p.poly([(hx + 0.1, hy - 1.4), (hx - 3.2, hy - 1.6), (hx - 7.2, hy - 0.3), (hx - 3.0, hy + 0.2), (hx + 0.1, hy + 0.1)], BONE, 194)
    p.ellipse(hx - 1.7, hy - 0.5, 0.8, 0.66, mul(CLAY_D, 0.46), 110)
    p.ellipse(hx - 6.4, hy - 0.2, 0.3, 0.24, mul(CLAY_D, 0.46), 120)
    for k in range(5):
        tx = hx - 3.4 - k * 0.9
        p.poly([(tx - 0.3, hy + 0.9), (tx + 0.3, hy + 0.9), (tx, hy + 1.9)], BONE, 186)
    # Хвост: позвонки мельчают.
    tx, ty = spine[-1]
    for k in range(1, 8):
        r = 0.66 - k * 0.06
        p.ellipse(tx + k * 1.5, ty + k * 0.34 + 0.02 * k * k, r, r * 0.86, BONE_D, 176)
        p.ellipse(tx + k * 1.5 - 0.1, ty + k * 0.34 + 0.02 * k * k - 0.1, r * 0.56, r * 0.5, BONE, 188)
    _ammonite(p, 14.0, 51.0, 2.2, BONE_D, 2.0)
    _ammonite(p, 50.0, 10.0, 1.6, BONE_D, 0.4)
    return p


def paint_grass():
    """Подстилка джунглей: тёмная зелень пятнами, вайи папоротника веером, палые листья, споры."""
    p = rm._ground(629, LITTER, 0.14, 0.09, 20.0)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(LITTER, 0.7), 0.1)
    for _ in range(700):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.4, 63)
        lean = p.rng.uniform(-0.4, 0.4)
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.4, 1.0))], LEAF_D if p.rng.random() < 0.5 else LEAF, 0.13, 146)
    # Палые листья: охра и глина, с жилкой.
    for _ in range(16):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        a = p.rng.uniform(0.0, math.pi)
        c, s = math.cos(a), math.sin(a)
        tint = OCHRE if p.rng.random() < 0.55 else mix(CLAY, HIDE, 0.4)
        p.poly([(x - c * 1.3, y - s * 1.3), (x - s * 0.5, y + c * 0.5), (x + c * 1.3, y + s * 1.3), (x + s * 0.5, y - c * 0.5)],
               mul(tint, 0.9), 150)
        p.line([(x - c * 1.2, y - s * 1.2), (x + c * 1.2, y + s * 1.2)], mul(tint, 0.62), 0.12, 144)
    # Вайи: тёмные снизу, светлые поверх. Каждая рисуется и со сдвигом на плитку, поэтому вайя,
    # вышедшая за край, продолжается с другой стороны.
    for i in range(30):
        x, y = p.rng.uniform(0, 64), p.rng.uniform(0, 64)
        length = p.rng.uniform(6.5, 10.0)
        turn = p.rng.uniform(-math.pi, math.pi)
        for ox in (-UNITS, 0.0, UNITS):
            for oy in (-UNITS, 0.0, UNITS):
                if not (-12.0 < x + ox < 76.0 and -12.0 < y + oy < 76.0):
                    continue
                if i < 12:
                    _frond(p, x + ox, y + oy, length, turn, mul(LEAF_D, 0.92), mul(LEAF_D, 0.66))
                else:
                    _frond(p, x + ox, y + oy, length, turn, LEAF if i % 3 else LEAF_L, LEAF_D)
    for _ in range(22):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.ellipse(x, y, 0.34, 0.34, BRASS, 150)
        p.ellipse(x - 0.06, y - 0.06, 0.18, 0.18, GOLD, 172)
    return p


def paint_road():
    """Дорога из плит лавового камня: поперечные швы, колеи от колёс-валунов, кости по оси."""
    p = rm._ground(633, SLAB, 0.08, 0.05, 12.0)
    for y in (0.0, 32.0, 64.0):
        p.fold([(-1, y), (65, y)], 0.55, 0.5, 80)
    for x in (0.0, 64.0):
        p.fold([(x, -1), (x, 65)], 0.5, 0.58, 70)
    # Плиты колотые: по одному излому на каждую половину, не доходят до швов.
    p.fold([(4.0, 13.0), (11.0, 16.5), (14.5, 22.0), (12.0, 28.5)], 0.32, 0.6, 60)
    p.fold([(50.0, 3.5), (53.5, 10.0), (59.5, 12.0)], 0.32, 0.6, 60)
    p.fold([(52.0, 36.0), (55.0, 44.0), (51.5, 51.0), (54.0, 60.0)], 0.32, 0.6, 60)
    p.fold([(5.0, 58.0), (9.0, 50.0), (7.0, 41.0)], 0.32, 0.6, 60)
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.6, 0.84, 26)
    p.speckle(0.5, 0.5, 63, 63, 1400, mul(SLAB, 0.74), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(SLAB, 1.16), 0.07)
    # Красная пыль глины, набитая в колеи и к швам.
    for x in (19.0, 45.0):
        p.speckle(x - 1.6, 0.5, 3.2, 63, 260, mix(SLAB, CLAY, 0.7), 0.1)
    for _ in range(40):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.2, 0.4)
        p.ellipse(x, y, r, r * 0.86, mul(SLAB, 0.52), 92)
    # Разметка по оси: две кости там же, где пунктир у пиратов.
    for y in (6.0, 38.0):
        _bone(p, 32.0, y + 1.0, 32.0, y + 11.0, 1.1)
    p.wrinkles(3, 3, 58, 58, 6, 4.0, 1.0, 0.72, 46)
    p.stains(3, 3, 58, 58, 10, 2.6, 0.88)
    return p


def paint_mud():
    """Вязкий пепел: тёмные наплывы, лужи смолы с бликом, пузыри, тлеющие угольки. Заметно темнее дороги."""
    p = rm.Paint(635)
    base = _arr(ASH)
    low, mid = p.tile_noise(4, 3), p.tile_noise(16, 3)

    def fn(gx, gy):
        dune = np.sin(2 * np.pi * (gy * 6.0 / UNITS + 0.4 * np.sin(2 * np.pi * gx * 2.0 / UNITS) + 0.3 * low))
        tone = 1.0 + 0.15 * dune + 0.14 * low + 0.1 * mid
        return base[None, None, :] * tone[..., None], 128.0 + dune * 30.0 + mid * 18.0
    p.field(fn)
    tar = rgb("18100E")
    for _ in range(9):
        x, y = p.rng.uniform(9, 55), p.rng.uniform(9, 55)
        rx, ry = p.rng.uniform(2.6, 5.0), p.rng.uniform(1.4, 2.6)
        p.ellipse(x, y, rx * 1.12, ry * 1.16, mul(ASH, 1.22), 140)
        p.ellipse(x, y, rx, ry, tar, 96)
        p.ellipse(x - rx * 0.3, y - ry * 0.34, rx * 0.34, ry * 0.2, rgb("5C4A52"), 100)
        # Пузырь на смоле: кольцо и блик.
        bx, by = x + rx * 0.3, y + ry * 0.16
        p.ellipse(bx, by, 0.6, 0.48, mul(ASH, 1.3), 120)
        p.ellipse(bx, by, 0.42, 0.32, tar, 106)
        p.ellipse(bx - 0.14, by - 0.12, 0.12, 0.1, rgb("8C7880"), 124)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(ASH, 1.5), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(ASH, 0.5), 0.1)
    # Угольки: красный ореол, жёлтая сердцевина.
    for _ in range(30):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.ellipse(x, y, 0.4, 0.34, HIDE_D, 140)
        p.ellipse(x, y, 0.24, 0.2, HIDE_L, 150)
        p.ellipse(x - 0.04, y - 0.04, 0.1, 0.09, rgb("FFE27C"), 156)
    return p


def paint_sail():
    """Шкура: рыжий мех с тёмными пятнами как у героя, ворс штрихами, складки, жильная строчка по шву."""
    p = rm._ground(637, HIDE, 0.08, 0.06, 14.0)
    # Ворс: короткие штрихи вниз, светлые и тёмные.
    for _ in range(1800):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1, 62)
        lean = p.rng.uniform(-0.25, 0.25)
        p.line([(x, y), (x + lean, y + p.rng.uniform(0.5, 1.1))], HIDE_L if p.rng.random() < 0.5 else HIDE_D, 0.13, 142)
    # Пятна: неровные кляксы из двух-трёх овалов, светлая сердцевина; держатся в стороне от швов.
    for cx in (8.5, 23.5, 40.5, 55.5):
        for row in range(5):
            x = cx + p.rng.uniform(-2.2, 2.2)
            y = 6.5 + row * 12.6 + (5.5 if int(cx) % 2 else 0.0) + p.rng.uniform(-1.6, 1.6)
            y = min(max(y, 5.0), 59.0)
            r = p.rng.uniform(1.5, 2.5)
            blobs = [(x, y, r, r * 0.8)]
            for _ in range(2):
                blobs.append((x + p.rng.uniform(-r, r) * 0.7, y + p.rng.uniform(-r, r) * 0.6, r * 0.62, r * 0.52))
            for bx, by, rx, ry in blobs:
                p.ellipse(bx, by, rx, ry, HAIR, 132)
            p.ellipse(x, y, r * 0.5, r * 0.38, mix(HAIR, HIDE_D, 0.45), 130)
    for _ in range(260):
        x, y = p.rng.uniform(2, 62), p.rng.uniform(2, 61)
        p.line([(x, y), (x + p.rng.uniform(-0.2, 0.2), y + p.rng.uniform(0.4, 0.9))], HAIR_D, 0.12, 138)
    p.wrinkles(1, 1, 62, 62, 26, 4.0, 1.2, 0.84, 30)
    # Шов полотнища: сыромятная кромка и стежки жилой крест-накрест.
    for x in (0.4, 32.0):
        p.fold([(x, 0), (x, 64)], 0.7, 0.62, 56)
    for k in range(16):
        y = k * 4.0 + 1.0
        p.line([(30.9, y), (33.1, y + 2.0)], mul(BONE_DD, 0.7), 0.4, 150)
        p.line([(30.9, y), (33.1, y + 2.0)], BONE, 0.22, 176)
    p.stains(2, 2, 60, 60, 6, 2.4, 0.9)
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
