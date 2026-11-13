#!/usr/bin/env python3
"""Модели «продвинутых» (threed, #119): цельная сетка на скелете и текстуры высокого разрешения.

Прототип на матросе. В отличие от `lowpoly_meshes.py`, где модель это набор жёстких кусков,
здесь тело одна сетка: каждое кольцо трубы знает, каким костям и с каким весом принадлежит, у
суставов веса переходят плавно, поэтому сгиб гладкий. Вершины ткани помечены (колыхание в
шейдере), отдельные кости пружинные (хвост банданы). Текстура рисуется сразу крупной: формы
сглажены, ткань и кожа с процедурным узором, из высоты узора получается карта рельефа.

    python3 tools/rig_models.py [--list] [--preview out.png]

Пишет `thegames/assets/settings/<сеттинг>/rig/<имя>.tres` (ресурс `RigModelDef`), `<имя>.png`
(цвет) и `<имя>_n.png` (рельеф).
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames", "assets", "settings")
RES = 512
UNITS = 64.0
SUPER = 2


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mul(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3])


def mix(a, b, k):
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))


# --- Художник ---------------------------------------------------------------------------------

class Paint:
    """Холст в условных единицах 64×64, рисуется в `RES` пикселей со сглаживанием.

    Рядом с цветом ведётся высота (серый слой): складки, швы и узор ткани поднимают или
    опускают поверхность, из неё потом считается карта рельефа.
    """

    def __init__(self, seed=1):
        self.n = RES * SUPER
        self.k = self.n / UNITS
        self.im = Image.new("RGB", (self.n, self.n), (128, 128, 128))
        self.h = Image.new("L", (self.n, self.n), 128)
        # Прозрачность: вырезы (рёбра скелета, рваные края); шейдер режет по половине.
        self.a = Image.new("L", (self.n, self.n), 255)
        self.d = ImageDraw.Draw(self.im)
        self.dh = ImageDraw.Draw(self.h)
        self.rng = np.random.default_rng(seed)

    def _box(self, x, y, w, h):
        k = self.k
        return [x * k, y * k, max((x + w) * k - 1, x * k), max((y + h) * k - 1, y * k)]

    def rect(self, x, y, w, h, color, height=None):
        self.d.rectangle(self._box(x, y, w, h), fill=color)
        if height is not None:
            self.dh.rectangle(self._box(x, y, w, h), fill=height)

    def ellipse(self, cx, cy, rx, ry, color, height=None):
        box = self._box(cx - rx, cy - ry, rx * 2, ry * 2)
        self.d.ellipse(box, fill=color)
        if height is not None:
            self.dh.ellipse(box, fill=height)

    def poly(self, points, color, height=None):
        pts = [(x * self.k, y * self.k) for x, y in points]
        self.d.polygon(pts, fill=color)
        if height is not None:
            self.dh.polygon(pts, fill=height)

    def line(self, points, color, width, height=None):
        pts = [(x * self.k, y * self.k) for x, y in points]
        self.d.line(pts, fill=color, width=max(1, int(round(width * self.k))), joint="curve")
        if height is not None:
            self.dh.line(pts, fill=height, width=max(1, int(round(width * self.k))), joint="curve")

    def cut(self, x, y, w, h):
        """Прозрачный прямоугольник."""
        ImageDraw.Draw(self.a).rectangle(self._box(x, y, w, h), fill=0)

    def cut_ellipse(self, cx, cy, rx, ry):
        ImageDraw.Draw(self.a).ellipse(self._box(cx - rx, cy - ry, rx * 2, ry * 2), fill=0)

    def solid(self, points):
        """Непрозрачный многоугольник поверх выреза (лист пальмы, колесо)."""
        ImageDraw.Draw(self.a).polygon([(px * self.k, py * self.k) for px, py in points], fill=255)

    def solid_ellipse(self, cx, cy, rx, ry):
        ImageDraw.Draw(self.a).ellipse(self._box(cx - rx, cy - ry, rx * 2, ry * 2), fill=255)

    def _slice(self, x, y, w, h):
        k = self.k
        return slice(int(y * k), int((y + h) * k)), slice(int(x * k), int((x + w) * k))

    def _apply(self, x, y, w, h, factor, lift=None):
        """Умножить цвет куска на поле `factor` (массив по размеру куска), высоту сдвинуть на `lift`."""
        ys, xs = self._slice(x, y, w, h)
        a = np.asarray(self.im, dtype=np.float32).copy()
        a[ys, xs] = np.clip(a[ys, xs] * factor[..., None], 0, 255)
        self.im = Image.fromarray(a.astype(np.uint8))
        self.d = ImageDraw.Draw(self.im)
        if lift is not None:
            hh = np.asarray(self.h, dtype=np.float32).copy()
            hh[ys, xs] = np.clip(hh[ys, xs] + lift, 0, 255)
            self.h = Image.fromarray(hh.astype(np.uint8))
            self.dh = ImageDraw.Draw(self.h)

    def _grid(self, x, y, w, h):
        ys, xs = self._slice(x, y, w, h)
        gy, gx = np.mgrid[ys, xs].astype(np.float32)
        return gx / self.k, gy / self.k

    def weave(self, x, y, w, h, period=0.34, depth=0.07, relief=16.0):
        """Ткань: мелкое переплетение нитей."""
        gx, gy = self._grid(x, y, w, h)
        t = np.sin(gx * 2 * np.pi / period) * np.sin(gy * 2 * np.pi / period)
        self._apply(x, y, w, h, 1.0 + t * depth, t * relief)

    def twill(self, x, y, w, h, period=0.42, depth=0.08, relief=18.0):
        """Плотная ткань с диагональным рубчиком (штаны)."""
        gx, gy = self._grid(x, y, w, h)
        t = np.sin((gx + gy) * 2 * np.pi / period)
        self._apply(x, y, w, h, 1.0 + t * depth, t * relief)

    def grain(self, x, y, w, h, amount=0.06, blur=1.2, relief=10.0):
        """Мягкий шум: кожа, потёртости."""
        ys, xs = self._slice(x, y, w, h)
        shape = (ys.stop - ys.start, xs.stop - xs.start)
        noise = self.rng.normal(0.0, 1.0, shape).astype(np.float32)
        img = Image.fromarray(np.clip(noise * 40 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur * SUPER))
        t = (np.asarray(img, dtype=np.float32) - 128.0) / 40.0
        self._apply(x, y, w, h, 1.0 + t * amount, t * relief)

    def shade_v(self, x, y, w, h, top=1.0, bottom=0.8):
        """Затемнение по высоте куска: сверху светлее."""
        gx, gy = self._grid(x, y, w, h)
        self._apply(x, y, w, h, top + (bottom - top) * (gy - y) / h)

    def shade_round(self, x, y, w, h, edge=0.78, power=2.0):
        """Объём по окружности: кусок обёрнут вокруг тела, перёд в середине, шов сзади по краям."""
        gx, gy = self._grid(x, y, w, h)
        t = np.abs((gx - x) / w * 2.0 - 1.0) ** power
        self._apply(x, y, w, h, 1.0 + (edge - 1.0) * t)

    def fold(self, points, width=0.5, dark=0.75, depth=70):
        """Складка или шов: тёмная линия, вдавленная в рельеф."""
        ys, xs = self._slice(0, 0, UNITS, UNITS)
        layer = Image.new("L", (self.n, self.n), 0)
        ImageDraw.Draw(layer).line([(px * self.k, py * self.k) for px, py in points], fill=255,
                                   width=max(1, int(round(width * self.k))), joint="curve")
        layer = layer.filter(ImageFilter.GaussianBlur(width * self.k * 0.45))
        t = np.asarray(layer, dtype=np.float32) / 255.0
        self._apply(0, 0, UNITS, UNITS, 1.0 + (dark - 1.0) * t, -t * depth)

    # --- Случайные детали: неровности, которые делают поверхность живой -----------------------

    def uneven(self, x, y, w, h, amount=0.07, scale=3.0):
        """Крупные разводы: неровная окраска и выгоревшие места."""
        self.grain(x, y, w, h, amount, scale * 2.2, 3.0)

    def stains(self, x, y, w, h, count=6, size=1.2, dark=0.86):
        """Пятна: мягкие тёмные кляксы случайной формы."""
        layer = Image.new("L", (self.n, self.n), 0)
        d = ImageDraw.Draw(layer)
        for _ in range(count):
            cx, cy = x + self.rng.uniform(0.1, 0.9) * w, y + self.rng.uniform(0.1, 0.9) * h
            for _ in range(4):
                r = size * self.rng.uniform(0.35, 1.0)
                ox, oy = self.rng.uniform(-size, size) * 0.5, self.rng.uniform(-size, size) * 0.5
                d.ellipse(self._box(cx + ox - r, cy + oy - r * 0.8, r * 2, r * 1.6), fill=int(self.rng.uniform(90, 200)))
        layer = layer.filter(ImageFilter.GaussianBlur(size * self.k * 0.3))
        ys, xs = self._slice(x, y, w, h)
        t = np.asarray(layer, dtype=np.float32)[ys, xs] / 255.0
        self._apply(x, y, w, h, 1.0 + (dark - 1.0) * t)

    def wrinkles(self, x, y, w, h, count=8, length=3.0, slant=0.3, dark=0.88, depth=26):
        """Мелкие складки ткани: короткие изогнутые линии в случайных местах."""
        for _ in range(count):
            cx, cy = x + self.rng.uniform(0.08, 0.92) * w, y + self.rng.uniform(0.08, 0.92) * h
            half = length * self.rng.uniform(0.5, 1.0) / 2.0
            tilt = self.rng.uniform(-slant, slant)
            bow = self.rng.uniform(-0.5, 0.5)
            pts = [(min(max(cx + half * t, x), x + w), min(max(cy + tilt * half * t + bow * (1.0 - t * t), y), y + h)) for t in (-1.0, -0.4, 0.3, 1.0)]
            self.fold(pts, self.rng.uniform(0.25, 0.5), dark, depth)

    def stitch(self, points, color, width=0.16, dash=0.55):
        """Строчка: пунктир вдоль ломаной, чуть выпуклый."""
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            dist = math.hypot(bx - ax, by - ay)
            steps = max(1, int(dist / dash))
            for i in range(steps):
                if i % 2:
                    continue
                t0, t1 = i / steps, min((i + 0.8) / steps, 1.0)
                self.line([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)], color, width, 150)

    def speckle(self, x, y, w, h, count, color, size=0.12):
        """Крапинки: веснушки, пыль, ворсинки."""
        for _ in range(count):
            r = size * self.rng.uniform(0.5, 1.3)
            self.ellipse(x + self.rng.uniform(0.0, 1.0) * w, y + self.rng.uniform(0.0, 1.0) * h, r, r, color)

    def band(self, x, y, w, h, color, height=None, wobble=0.12):
        """Полоса с неровным краем: нарисованная от руки, а не по линейке."""
        steps = 24
        top = [(x + w * i / steps, y + self.rng.uniform(-wobble, wobble)) for i in range(steps + 1)]
        bottom = [(x + w * i / steps, y + h + self.rng.uniform(-wobble, wobble)) for i in range(steps, -1, -1)]
        self.poly(top + bottom, color, height)

    def wood(self, x, y, w, h, boards, vertical=True, base=(122, 82, 48), gap=0.22):
        """Доски: у каждой свой тон, волокна вдоль, тёмные щели между досками. Узор вдоль доски
        периодичен по куску, поэтому кусок во весь холст стыкуется сам с собой."""
        gx, gy = self._grid(x, y, w, h)
        across, along = ((gx - x), (gy - y)) if vertical else ((gy - y), (gx - x))
        span, length = (w, h) if vertical else (h, w)
        width = span / boards
        index = np.clip((across / width).astype(np.int32), 0, boards - 1)
        tones = self.rng.uniform(0.86, 1.12, boards).astype(np.float32)
        phases = self.rng.uniform(0.0, 6.28, boards).astype(np.float32)
        local = across / width - index
        # Волокна: линии вдоль доски, слегка гуляют; прожилки случайной силы поперёк.
        streaks = self.rng.normal(0.0, 1.0, (boards, 48)).astype(np.float32)
        streak = streaks[index, np.clip((local * 48).astype(np.int32), 0, 47)]
        wave = np.sin(2 * np.pi * (local * 5.0 + 0.35 * np.sin(2 * np.pi * along / length * 2.0 + phases[index])))
        fibre = 1.0 + 0.05 * wave + 0.045 * streak
        edge = np.minimum(local, 1.0 - local) * width
        seam = np.clip(edge / gap, 0.0, 1.0)
        factor = tones[index] * fibre * (0.45 + 0.55 * seam)
        ys, xs = self._slice(x, y, w, h)
        a = np.asarray(self.im, dtype=np.float32).copy()
        a[ys, xs] = np.clip(np.array(base, dtype=np.float32)[None, None, :] * factor[..., None], 0, 255)
        self.im = Image.fromarray(a.astype(np.uint8))
        self.d = ImageDraw.Draw(self.im)
        hh = np.asarray(self.h, dtype=np.float32).copy()
        hh[ys, xs] = np.clip(128.0 + wave * 5.0 + streak * 4.0 - (1.0 - seam) * 70.0, 0, 255)
        self.h = Image.fromarray(hh.astype(np.uint8))
        self.dh = ImageDraw.Draw(self.h)

    def field(self, fn):
        """Весь холст по формуле: `fn(gx, gy)` отдаёт цвет (массив …×3) и высоту (массив или None)."""
        gx, gy = self._grid(0, 0, UNITS, UNITS)
        color, height = fn(gx, gy)
        self.im = Image.fromarray(np.clip(color, 0, 255).astype(np.uint8))
        self.d = ImageDraw.Draw(self.im)
        if height is not None:
            self.h = Image.fromarray(np.clip(height, 0, 255).astype(np.uint8))
            self.dh = ImageDraw.Draw(self.h)

    def tile_noise(self, cells=16, octaves=3):
        """Шум, который стыкуется по краям холста: сумма плавных решёток, значения около −1..1."""
        out = np.zeros((self.n, self.n), dtype=np.float32)
        gx, gy = self._grid(0, 0, UNITS, UNITS)
        amp = 1.0
        for _ in range(octaves):
            grid = self.rng.normal(0.0, 1.0, (cells, cells)).astype(np.float32)
            fx, fy = gx / UNITS * cells, gy / UNITS * cells
            ix, iy = np.floor(fx).astype(np.int32) % cells, np.floor(fy).astype(np.int32) % cells
            tx, ty = _smooth_np(fx - np.floor(fx)), _smooth_np(fy - np.floor(fy))
            a, b = grid[iy, ix], grid[iy, (ix + 1) % cells]
            c, d = grid[(iy + 1) % cells, ix], grid[(iy + 1) % cells, (ix + 1) % cells]
            out += amp * ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
            amp *= 0.5
            cells *= 2
        return out / 1.6

    def region(self, x, y, w, h):
        """Кусок в долях текстуры, чуть внутрь, чтобы фильтр не тянул соседей."""
        e = 0.12
        return ((x + e) / UNITS, (y + e) / UNITS, (x + w - e) / UNITS, (y + h - e) / UNITS)

    def finish(self):
        """Цвет и карта рельефа в `RES` пикселей."""
        color = self.im.resize((RES, RES), Image.LANCZOS).convert("RGBA")
        color.putalpha(self.a.resize((RES, RES), Image.LANCZOS).point(lambda v: 255 if v >= 128 else 0))
        height = np.asarray(self.h.filter(ImageFilter.GaussianBlur(SUPER * 0.8)).resize((RES, RES), Image.LANCZOS), dtype=np.float32)
        strength = 0.045
        dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * strength
        dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * strength
        nz = np.ones_like(dx)
        length = np.sqrt(dx * dx + dy * dy + nz * nz)
        # Зелёный вверх (как ждёт Godot): высота растёт вниз по картинке, поэтому знак у dy прямой.
        normal = np.stack([(-dx / length) * 0.5 + 0.5, (dy / length) * 0.5 + 0.5, (nz / length) * 0.5 + 0.5], axis=-1)
        return color, Image.fromarray((normal * 255).astype(np.uint8))


# --- Сетка на скелете ---------------------------------------------------------------------------

class Rig:
    """Сетка с общими вершинами: место, развёртка, кости с весами, доля ткани; и скелет."""

    def __init__(self, name):
        self.name = name
        self.bones = []          # (имя, родитель или None, (x, y, z) в покое)
        self.springs = []        # (кость, жёсткость, затухание, тяжесть)
        self.verts, self.uvs, self.weights, self.cloth, self.tris = [], [], [], [], []

    def bone(self, name, parent, pos):
        self.bones.append((name, parent, pos))

    def spring(self, name, stiffness=60.0, damping=7.0, gravity=0.6, rest=(0.0, -1.0, 0.35)):
        """Пружинная кость: жёсткость, затухание, тяжесть и куда в покое смотрит её хвост."""
        self.springs.append((name, stiffness, damping, gravity, rest))

    def vert(self, pos, uv, weights, cloth=0.0):
        self.verts.append(pos)
        self.uvs.append(uv)
        total = sum(w for _, w in weights) or 1.0
        self.weights.append([(b, w / total) for b, w in sorted(weights, key=lambda x: -x[1])[:4] if w > 0.0])
        self.cloth.append(cloth)
        return len(self.verts) - 1

    def tri(self, a, b, c, out):
        """Треугольник лицом в сторону `out` (против часовой стрелки, если смотреть снаружи)."""
        pa, pb, pc = (np.array(self.verts[i]) for i in (a, b, c))
        if np.dot(np.cross(pb - pa, pc - pa), np.array(out)) < 0.0:
            b, c = c, b
        self.tris.append((a, b, c))

    def tube(self, rings, n, region, weight_fn, cloth_fn=None, cap_bottom=None, cap_top=None, v_range=None, skip=()):
        """Труба из колец снизу вверх `(y, rx, rz, cx, cz)`: по `n` точек, шов сзади, перёд (−Z) в
        середине куска. По вертикали развёртка идёт по высоте `y` (или по `v_range` высот)."""
        u0, v0, u1, v1 = region
        y_lo, y_hi = v_range if v_range else (rings[0][0], rings[-1][0])
        rows = []
        for y, rx, rz, cx, cz in rings:
            row = []
            v = v1 - (v1 - v0) * (y - y_lo) / (y_hi - y_lo)
            for k in range(n + 1):
                a = 2.0 * math.pi * k / n
                pos = (cx + rx * math.sin(a), y, cz + rz * math.cos(a))
                row.append(self.vert(pos, (u0 + (u1 - u0) * k / n, v), weight_fn(y), cloth_fn(y) if cloth_fn else 0.0))
            rows.append(row)
        for i in range(len(rows) - 1):
            lo, hi = rings[i], rings[i + 1]
            for k in range(n):
                if (i, k) in skip:
                    continue
                a, b, c, d = rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]
                mid = np.mean([self.verts[j] for j in (a, b, c, d)], axis=0)
                out = (mid[0] - (lo[3] + hi[3]) / 2.0, 0.0, mid[2] - (lo[4] + hi[4]) / 2.0)
                self.tri(a, b, c, out)
                self.tri(a, c, d, out)
        for cap, ring, row, out in ((cap_bottom, rings[0], rows[0], (0, -1, 0)), (cap_top, rings[-1], rows[-1], (0, 1, 0))):
            if cap is None:
                continue
            c0, d0, c1, d1 = cap
            y, rx, rz, cx, cz = ring
            center = self.vert((cx, y, cz), ((c0 + c1) / 2.0, (d0 + d1) / 2.0), weight_fn(y))
            rim = []
            for k in range(n):
                p = self.verts[row[k]]
                uv = (c0 + (c1 - c0) * (0.5 + (p[0] - cx) / (2.0 * rx)), d0 + (d1 - d0) * (0.5 + (p[2] - cz) / (2.0 * rz)))
                rim.append(self.vert(p, uv, weight_fn(y)))
            for k in range(n):
                self.tri(center, rim[k], rim[(k + 1) % n], out)
        return rows

    def sleeve(self, rows, i0, i1, k0, k1, side, bends, rings, region, weight_fn, cap=None):
        """Рукав, вращённый в тело: в трубе тела вырезано окно (кольца `i0..i1`, точки `k0..k1`,
        его грани пропущены через `skip`), рукав начинается с края окна теми же точками и уходит
        вбок и вниз. Поверхность непрерывна: одежда единая, без стыка в плече.

        `bends`: кольца перехода `(середина, угол от «вбок» к «вниз» в градусах, радиус вперёд,
        радиус поперёк)`; `rings`: дальше обычные кольца руки сверху вниз `(y, rx, rz, cx, cz)`.
        """
        loop = [rows[i0][k] for k in range(k0, k1 + 1)] + [rows[i][k1] for i in range(i0 + 1, i1 + 1)] \
            + [rows[i1][k] for k in range(k1 - 1, k0 - 1, -1)] + [rows[i][k0] for i in range(i1 - 1, i0, -1)]
        pts = [np.array(self.verts[j]) for j in loop]
        center = np.mean(pts, axis=0)
        front = np.array([0.0, 0.0, -1.0])
        frame = lambda deg: np.cross(np.array([side * math.cos(math.radians(deg)), -math.sin(math.radians(deg)), 0.0]), front)
        g0 = frame(0.0)
        # Угол каждой точки окна вокруг оси рукава: все кольца рукава берут те же углы, рукав не скручен.
        order = sorted(range(len(pts)), key=lambda j: math.atan2(np.dot(pts[j] - center, g0), np.dot(pts[j] - center, front)))
        angles = [math.atan2(np.dot(pts[j] - center, g0), np.dot(pts[j] - center, front)) for j in order]
        m = len(angles)
        shape = [("loop", None)] + [("bend", b) for b in bends] + [("ring", r) for r in rings]
        # Длина вдоль рукава для развёртки.
        mids = [center] + [np.array(b[0]) for b in bends] + [np.array([r[3], r[0], r[4]]) for r in rings]
        along = [0.0]
        for a, b in zip(mids, mids[1:]):
            along.append(along[-1] + float(np.linalg.norm(b - a)))
        u0, v0, u1, v1 = region
        grid = []
        for index, (kind, spec) in enumerate(shape):
            v = v0 + (v1 - v0) * along[index] / along[-1]
            row = []
            for k in range(m + 1):
                phi = angles[k % m]
                if kind == "loop":
                    pos = pts[order[k % m]]
                elif kind == "bend":
                    c, deg, rf, rg = spec
                    pos = np.array(c) + front * rf * math.cos(phi) + frame(deg) * rg * math.sin(phi)
                else:
                    y, rx, rz, cx, cz = spec
                    pos = np.array([cx, y, cz]) + front * rz * math.cos(phi) + frame(90.0) * rx * math.sin(phi)
                row.append(self.vert(tuple(float(x) for x in pos), (u0 + (u1 - u0) * k / m, v), weight_fn(index, float(pos[1]))))
            grid.append(row)
        for i in range(len(grid) - 1):
            for k in range(m):
                a, b, c, d = grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]
                mid = np.mean([self.verts[j] for j in (a, b, c, d)], axis=0)
                out = mid - (mids[i] + mids[i + 1]) / 2.0
                self.tri(a, b, c, out)
                self.tri(a, c, d, out)
        if cap is not None:
            c0, d0, c1, d1 = cap
            last = len(grid) - 1
            hub = self.vert(tuple(float(x) for x in mids[-1]), ((c0 + c1) / 2.0, (d0 + d1) / 2.0), weight_fn(last, float(mids[-1][1])))
            rim = [self.vert(self.verts[grid[last][k]], (c0 + (c1 - c0) * (0.5 + 0.45 * math.cos(angles[k])),
                                                        d0 + (d1 - d0) * (0.5 + 0.45 * math.sin(angles[k]))),
                             weight_fn(last, self.verts[grid[last][k]][1])) for k in range(m)]
            for k in range(m):
                self.tri(hub, rim[k], rim[(k + 1) % m], (0.0, -1.0, 0.0))

    def strip(self, points, width_dir, half, region, weight_fn, cloth_from=0.0, cloth_to=1.0, taper=0.35):
        """Лента вдоль `points` шириной `half`·2 поперёк `width_dir`, двусторонняя: ткань (доля
        колыхания растёт к концу) или жёсткая вещь вроде клинка (`cloth_to` 0)."""
        u0, v0, u1, v1 = region
        rows = []
        for i, p in enumerate(points):
            t = i / (len(points) - 1)
            row = []
            for side, u in ((-1.0, u0), (1.0, u1)):
                pos = tuple(p[j] + width_dir[j] * half * side * (1.0 - taper * t) for j in range(3))
                row.append(self.vert(pos, (u, v0 + (v1 - v0) * t), weight_fn(t), cloth_from + (cloth_to - cloth_from) * t))
            rows.append(row)
        for i in range(len(rows) - 1):
            a, b, c, d = rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]
            pa, pb, pc = (np.array(self.verts[j]) for j in (a, b, c))
            face = np.cross(pb - pa, pc - pa)
            for out in (face, -face):
                self.tri(a, b, c, out)
                self.tri(a, c, d, out)

    def normals(self):
        """Гладкие нормали: среднее по граням, вершины в одной точке (швы) делят нормаль."""
        acc = {}
        key = lambda p: (round(p[0], 4), round(p[1], 4), round(p[2], 4))
        for a, b, c in self.tris:
            pa, pb, pc = (np.array(self.verts[i]) for i in (a, b, c))
            n = np.cross(pb - pa, pc - pa)
            for i in (a, b, c):
                acc[key(self.verts[i])] = acc.get(key(self.verts[i]), np.zeros(3)) + n
        out = []
        for p in self.verts:
            n = acc.get(key(p), np.array([0.0, 1.0, 0.0]))
            length = np.linalg.norm(n)
            out.append(tuple(n / length) if length > 1e-9 else (0.0, 1.0, 0.0))
        return out

    def write(self, folder, setting, color, normal):
        os.makedirs(folder, exist_ok=True)
        color.save(os.path.join(folder, self.name + ".png"))
        normal.save(os.path.join(folder, self.name + "_n.png"))
        names = [b[0] for b in self.bones]
        num = lambda x: ("%.4f" % x).rstrip("0").rstrip(".") if abs(x) > 5e-5 else "0"
        flat = lambda rows: ", ".join(num(v) for row in rows for v in row)
        bone_ids, bone_weights = [], []
        for ws in self.weights:
            ws = ws + [(names[0], 0.0)] * (4 - len(ws))
            bone_ids += [names.index(b) for b, _ in ws]
            bone_weights += [w for _, w in ws]
        base = "res://assets/settings/%s/rig/%s" % (setting, self.name)
        lines = [
            '[gd_resource type="Resource" script_class="RigModelDef" load_steps=4 format=3]',
            "",
            '[ext_resource type="Script" path="res://scripts/demos/rig_model_def.gd" id="1_def"]',
            '[ext_resource type="Texture2D" path="%s.png" id="2_tex"]' % base,
            '[ext_resource type="Texture2D" path="%s_n.png" id="3_nrm"]' % base,
            "",
            "[resource]",
            'script = ExtResource("1_def")',
            'texture = ExtResource("2_tex")',
            'normal_map = ExtResource("3_nrm")',
            "bone_names = PackedStringArray(%s)" % ", ".join('"%s"' % n for n in names),
            "bone_parents = PackedInt32Array(%s)" % ", ".join(str(names.index(b[1]) if b[1] else -1) for b in self.bones),
            "bone_rests = PackedVector3Array(%s)" % flat([b[2] for b in self.bones]),
            "spring_bones = PackedStringArray(%s)" % ", ".join('"%s"' % s[0] for s in self.springs),
            "spring_params = PackedVector3Array(%s)" % flat([s[1:4] for s in self.springs]),
            "spring_dirs = PackedVector3Array(%s)" % flat([s[4] for s in self.springs]),
            "vertices = PackedVector3Array(%s)" % flat(self.verts),
            "normals = PackedVector3Array(%s)" % flat(self.normals()),
            "uvs = PackedVector2Array(%s)" % flat(self.uvs),
            "cloth = PackedFloat32Array(%s)" % ", ".join(num(c) for c in self.cloth),
            "bones = PackedInt32Array(%s)" % ", ".join(str(i) for i in bone_ids),
            "weights = PackedFloat32Array(%s)" % ", ".join(num(w) for w in bone_weights),
            "indices = PackedInt32Array(%s)" % ", ".join(str(i) for t in self.tris for i in t),
            "",
        ]
        with open(os.path.join(folder, self.name + ".tres"), "w") as f:
            f.write("\n".join(lines))


def blend(y, stops):
    """Веса костей по высоте: `stops` это [(кость, от, до), …] сверху вниз или снизу вверх; между
    соседними костями вес переходит плавно на ширине перехода `до − от` вокруг сустава."""
    out = {}
    for i, (name, lo, hi) in enumerate(stops):
        nxt = stops[i + 1] if i + 1 < len(stops) else None
        prev = stops[i - 1] if i > 0 else None
        w = 1.0
        if prev is not None:
            a, b = prev[2], lo
            w *= 0.0 if y <= a else (1.0 if y >= b else _smooth((y - a) / (b - a)))
        if nxt is not None:
            a, b = hi, nxt[1]
            w *= 1.0 if y <= a else (0.0 if y >= b else 1.0 - _smooth((y - a) / (b - a)))
        if w > 0.001:
            out[name] = w
    return list(out.items())


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def _smooth_np(t):
    return t * t * (3.0 - 2.0 * t)


# --- Пираты: матрос -----------------------------------------------------------------------------

SKIN, SKIN_D, SKIN_L = rgb("D9A27C"), rgb("A8704F"), rgb("EBC0A0")
HAIR = rgb("3A2A20")
WHITE, NAVY = rgb("EAE4D4"), rgb("2B4470")
RED, RED_D = rgb("B5362E"), rgb("7C2320")
PANTS, PANTS_D = rgb("3C5C8C"), rgb("2A4268")
BOOT, BOOT_L = rgb("2E241E"), rgb("5A4636")
BELT, GOLD, GOLD_D = rgb("4A3222"), rgb("E0B040"), rgb("9A7020")


def paint_sailor():
    """Атлас матроса: торс 32×22, голова 32×20, рука 16×26, нога 20×34, сапог, подошва, хвост банданы."""
    p = Paint(11)
    # Торс: развёртка по высоте 1,47 (верх) → 0,86 (низ), 22 единицы; перёд в середине (x = 16).
    p.rect(0, 0, 32, 22, WHITE, 128)
    for i in range(6):
        p.band(0, 2.6 + i * 2.6, 32, 1.3, mul(NAVY, p.rng.uniform(0.9, 1.08)), 124)
    p.weave(0, 0, 32, 18.6)
    p.uneven(0, 0, 32, 18.6, 0.06)
    p.wrinkles(0, 4, 32, 14, 14, 3.4, 0.35, 0.9)
    p.stains(0, 9, 32, 9, 5, 1.3, 0.9)
    p.speckle(0, 0, 32, 18.6, 60, mul(WHITE, 0.86), 0.07)
    p.poly([(12.6, 0), (19.4, 0), (16, 4.4)], SKIN, 118)
    p.line([(12.4, 0), (16, 4.7), (19.6, 0)], mul(WHITE, 0.82), 0.5, 140)
    p.rect(0, 18.6, 32, 2.0, BELT, 150)
    p.grain(0, 18.6, 32, 2.0, 0.1)
    p.stitch([(0, 18.9), (32, 18.9)], mul(BELT, 1.5), 0.1, 0.5)
    p.stitch([(0, 20.3), (32, 20.3)], mul(BELT, 1.5), 0.1, 0.5)
    for hx in (18.6, 20.0, 21.4):
        p.ellipse(hx, 19.6, 0.18, 0.18, mul(BELT, 0.5), 110)
    p.stitch([(12.4, 0.5), (16, 5.2), (19.6, 0.5)], mul(WHITE, 0.7), 0.1, 0.45)
    p.rect(14.9, 18.4, 2.2, 2.4, GOLD, 175)
    p.rect(15.5, 19.0, 1.0, 1.2, GOLD_D, 150)
    p.rect(0, 20.6, 32, 1.4, PANTS, 128)
    for x in (9.5, 22.5):
        p.fold([(x, 6.0), (x + 0.3, 12.0), (x, 17.5)], 0.9, 0.86, 30)
    p.fold([(0, 18.5), (32, 18.5)], 0.35, 0.6, 60)
    p.shade_v(0, 0, 32, 18.6, 1.04, 0.9)
    p.shade_round(0, 0, 32, 22, 0.74)
    # Голова: высота 1,76 → 1,47, 20 единиц; перёд x = 48.
    p.rect(32, 0, 32, 20, SKIN, 128)
    p.rect(32, 4.6, 8.5, 6.6, HAIR, 136)
    p.rect(55.5, 4.6, 8.5, 6.6, HAIR, 136)
    p.rect(32, 0, 32, 5.2, RED, 142)
    p.weave(32, 0, 32, 5.2, 0.3, 0.06)
    p.uneven(32, 0, 32, 5.2, 0.08, 2.0)
    for i in range(22):
        p.ellipse(33 + i * 1.45, 1.2 + (i % 2) * 2.2, 0.26, 0.26, mul(WHITE, 0.95))
    p.wrinkles(32, 0.4, 32, 4.4, 9, 3.0, 0.2, 0.86)
    p.fold([(32, 5.2), (64, 5.2)], 0.4, 0.62, 55)
    p.fold([(32, 2.4), (41, 2.9), (48, 2.2), (55, 2.9), (64, 2.4)], 0.45, 0.84, 25)
    for sx in (-1.0, 1.0):
        ex = 48 + sx * 2.9
        p.ellipse(ex, 8.1, 1.15, 0.72, rgb("F4EEE2"), 132)
        p.ellipse(ex + sx * 0.1, 8.15, 0.5, 0.6, rgb("3A2C22"))
        p.ellipse(ex + sx * 0.1 - 0.15, 7.95, 0.14, 0.14, rgb("FFFFFF"))
        p.line([(ex - 1.3, 6.9), (ex, 6.55), (ex + 1.3, 6.9 + 0.1 * sx)], HAIR, 0.42, 138)
        p.line([(ex - 1.2, 7.4), (ex + 1.2, 7.4)], SKIN_D, 0.18)
        p.ellipse(48 + sx * 8.2, 9.3, 0.9, 1.5, mul(SKIN, 0.92), 140)
        p.ellipse(48 + sx * 8.2, 9.3, 0.4, 0.9, SKIN_D, 120)
    p.poly([(47.3, 8.0), (48.7, 8.0), (49.3, 11.0), (46.7, 11.0)], SKIN_L, 150)
    p.line([(46.9, 11.1), (48, 11.45), (49.1, 11.1)], SKIN_D, 0.3, 112)
    p.line([(46.2, 13.2), (48, 13.55), (49.8, 13.2)], rgb("8A4A3C"), 0.42, 112)
    p.line([(46.6, 13.9), (49.4, 13.9)], mul(SKIN, 0.9), 0.3)
    # Щетина и тень под скулами.
    ys, xs = p._slice(40.5, 10.5, 15, 6.0)
    gx, gy = p._grid(40.5, 10.5, 15, 6.0)
    side = np.clip(np.abs((gx - 48) / 7.5), 0, 1)
    jaw = _smooth_np(np.clip((gy - 10.5) / 4.0, 0, 1)) * (0.55 + 0.45 * side) * (1.0 - side ** 6)
    p._apply(40.5, 10.5, 15, 6.0, 1.0 - 0.22 * jaw)
    p.grain(40.5, 6.0, 15, 10.5, 0.035, 0.9, 5.0)
    # Румянец, веснушки, шрам на щеке, морщинки у глаз.
    for sx in (-1.0, 1.0):
        p.stains(48 + sx * 4.2 - 1.6, 10.0, 3.2, 2.4, 2, 1.0, 0.93)
        p.line([(48 + sx * 4.3, 7.9), (48 + sx * 5.0, 7.6)], SKIN_D, 0.1)
        p.line([(48 + sx * 4.3, 8.4), (48 + sx * 5.0, 8.6)], SKIN_D, 0.1)
    p.speckle(43.5, 8.6, 9, 3.2, 26, mul(SKIN, 0.8), 0.07)
    p.speckle(42, 12.2, 12, 4.0, 150, mul(HAIR, 1.25), 0.05)
    p.line([(51.6, 10.4), (53.0, 12.3)], mul(SKIN, 1.14), 0.16, 150)
    p.line([(45.0, 5.9), (51.0, 5.8)], SKIN_D, 0.08)
    p.fold([(41, 16.6), (48, 17.3), (55, 16.6)], 0.9, 0.72, 20)
    p.shade_round(32, 0, 32, 20, 0.8)
    # Рука: высота 1,44 → 0,74, 26 единиц: рукав до локтя, предплечье, кисть.
    p.rect(0, 22, 16, 26, SKIN, 128)
    p.rect(0, 22, 16, 8.6, WHITE, 134)
    for i in range(3):
        p.rect(0, 23.6 + i * 2.6, 16, 1.3, NAVY, 130)
    p.weave(0, 22, 16, 8.6)
    p.rect(0, 30.2, 16, 0.6, mul(WHITE, 0.8), 146)
    p.fold([(0, 30.9), (16, 30.9)], 0.3, 0.7, 40)
    p.grain(0, 31, 16, 17, 0.03, 1.0, 4.0)
    p.uneven(0, 31, 16, 17, 0.05, 2.5)
    p.wrinkles(0, 23, 16, 7, 6, 2.6, 0.3, 0.9)
    # Якорь-наколка на предплечье, волоски, костяшки.
    ink = rgb("3C5670")
    p.line([(8, 34.2), (8, 38.6)], ink, 0.22)
    p.line([(6.9, 35.0), (9.1, 35.0)], ink, 0.2)
    p.line([(6.4, 37.6), (7.0, 38.6), (8, 39.0), (9.0, 38.6), (9.6, 37.6)], ink, 0.22)
    p.ellipse(8, 33.8, 0.38, 0.38, ink)
    p.ellipse(8, 33.8, 0.17, 0.17, SKIN)
    p.speckle(1, 32, 14, 10, 90, mul(SKIN, 0.82), 0.045)
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.ellipse(fx + 0.9, 45.0, 0.5, 0.3, mul(SKIN, 0.9), 140)
    p.fold([(0, 44.0), (16, 44.0)], 0.35, 0.86, 18)
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.line([(fx, 45.6), (fx, 48)], SKIN_D, 0.2, 112)
    p.shade_round(0, 22, 16, 26, 0.76)
    # Нога: высота 0,95 → 0,07, 34 единицы: штаны с рубчиком, складки у колена, подгиб.
    p.rect(16, 22, 20, 34, PANTS, 128)
    p.twill(16, 22, 20, 34)
    p.fold([(16, 22.2), (36, 22.2)], 0.4, 0.7, 30)
    for fy, dark in ((38.6, 0.82), (39.9, 0.88), (41.4, 0.9)):
        p.fold([(19, fy), (26, fy + 0.5), (33, fy)], 0.55, dark, 28)
    p.fold([(26, 22), (26.2, 54)], 0.25, 0.84, 22)
    p.uneven(16, 22, 20, 34, 0.09, 3.0)
    p.wrinkles(16, 24, 20, 12, 10, 3.6, 0.5, 0.9)
    p.wrinkles(16, 42, 20, 11, 12, 3.0, 0.25, 0.88)
    p.stitch([(25.4, 22.6), (25.6, 53.4)], mul(PANTS, 1.45), 0.1, 0.5)
    p.stitch([(26.8, 22.6), (27.0, 53.4)], mul(PANTS, 1.45), 0.1, 0.5)
    # Карман со строчкой, заплата на колене, потёртости.
    p.stitch([(18.5, 24.2), (22.6, 24.2), (22.9, 28.0), (20.6, 29.2), (18.3, 28.0), (18.5, 24.2)], mul(PANTS, 1.45), 0.1, 0.45)
    p.rect(28.6, 37.2, 4.4, 3.8, mul(PANTS, 0.82), 142)
    p.twill(28.6, 37.2, 4.4, 3.8, 0.36, 0.1)
    p.stitch([(28.9, 37.5), (32.7, 37.5), (32.7, 40.7), (28.9, 40.7), (28.9, 37.5)], rgb("D8CCA8"), 0.11, 0.5)
    ys, xs = p._slice(19, 37, 8, 5)
    gx, gy = p._grid(19, 37, 8, 5)
    worn = np.exp(-(((gx - 23) / 3.0) ** 2 + ((gy - 39.5) / 1.8) ** 2))
    p._apply(19, 37, 8, 5, 1.0 + 0.22 * worn)
    p.stains(16, 44, 20, 9, 5, 1.4, 0.88)
    p.rect(16, 53.6, 20, 2.4, PANTS_D, 140)
    p.fold([(16, 53.5), (36, 53.5)], 0.3, 0.7, 40)
    p.shade_v(16, 22, 20, 34, 1.03, 0.88)
    p.shade_round(16, 22, 20, 34, 0.74)
    # Сапог, подошва, кожа, хвост банданы.
    p.rect(40, 24, 12, 6, BOOT_L, 128)
    p.grain(40, 24, 12, 6, 0.12, 1.4, 14.0)
    p.wrinkles(40, 24.3, 12, 5.4, 9, 2.4, 0.4, 0.8, 34)
    p.stitch([(40, 29.4), (52, 29.4)], rgb("C8B090"), 0.1, 0.5)
    p.stains(40, 27, 12, 3, 3, 0.9, 0.82)
    p.fold([(40, 26.4), (52, 26.4)], 0.4, 0.7, 40)
    p.shade_round(40, 24, 12, 6, 0.7)
    p.rect(54, 24, 6, 6, BOOT, 128)
    p.rect(54, 32, 6, 6, SKIN, 128)
    p.rect(40, 34, 12, 8, RED, 128)
    p.weave(40, 34, 12, 8, 0.3, 0.06)
    for i in range(10):
        p.ellipse(41 + (i % 5) * 2.5, 35.6 + (i // 5) * 3.6, 0.26, 0.26, mul(WHITE, 0.95))
    p.wrinkles(40, 34, 12, 8, 5, 3.0, 0.6, 0.86)
    p.fold([(44, 34), (44.5, 42)], 0.5, 0.8, 30)
    p.fold([(48, 34), (47.6, 42)], 0.5, 0.82, 30)
    return p


# Раскладка атласа у всех людей одна: конструктор тела знает, куда что развёрнуто.
def regions(p):
    return {"torso": p.region(0, 0, 32, 22), "head": p.region(32, 0, 32, 20), "arm": p.region(0, 22, 16, 26),
            "leg": p.region(16, 22, 20, 34), "boot": p.region(40, 24, 12, 6), "sole": p.region(54, 24, 6, 6),
            "skin": p.region(54, 32, 6, 6), "strip": p.region(40, 34, 12, 8), "skirt": p.region(36, 44, 28, 20),
            "hat": p.region(0, 48, 16, 16), "crown": p.region(46, 1, 4, 3)}


def build_body(name, reg, bulk=1.0, limb=1.0, leg="bell"):
    """Конструктор тела: человек ростом 1,76 м на скелете из 17 костей, одной сеткой.

    `bulk` ширина торса и плеч, `limb` толщина рук и ног (у скелета кости тонкие), `leg` низ
    штанины: `bell` клёш с колыханием или `straight` под сапог. Возвращает сетку и кольца торса
    (к ним персонаж добавляет своё: полы, шляпу, хвосты).
    """
    r = Rig(name)
    k = bulk
    r.bone("hips", None, (0.0, 0.92, 0.0))
    r.bone("spine", "hips", (0.0, 1.06, 0.0))
    r.bone("chest", "spine", (0.0, 1.24, 0.0))
    r.bone("neck", "chest", (0.0, 1.46, 0.0))
    r.bone("head", "neck", (0.0, 1.53, 0.0))
    for side, sx in (("l", -1.0), ("r", 1.0)):
        r.bone("arm_" + side, "chest", (sx * 0.215 * k, 1.4, 0.0))
        r.bone("fore_" + side, "arm_" + side, (sx * 0.232 * k, 1.12, 0.0))
        r.bone("hand_" + side, "fore_" + side, (sx * 0.24 * k, 0.87, 0.0))
        r.bone("leg_" + side, "hips", (sx * 0.095 * k, 0.9, 0.0))
        r.bone("shin_" + side, "leg_" + side, (sx * 0.095 * k, 0.49, 0.0))
        r.bone("foot_" + side, "shin_" + side, (sx * 0.095 * k, 0.08, 0.0))
    n = 16
    # Торс и голова одной трубой. В боках торса окна под рукава: кольца 8..11 (высота 1,25–1,415),
    # по две грани вокруг бока (точки 3..5 справа, 11..13 слева).
    body = lambda y: blend(y, [("hips", 0.0, 0.97), ("spine", 1.07, 1.14), ("chest", 1.26, 1.435), ("neck", 1.475, 1.495), ("head", 1.53, 9.0)])
    holes = {(i, kk) for i in (8, 9, 10) for kk in (3, 4, 11, 12)}
    rows = r.tube([(0.86, 0.15 * k, 0.11 * k, 0, 0), (0.9, 0.156 * k, 0.116 * k, 0, 0), (0.95, 0.152 * k, 0.112 * k, 0, 0),
                   (1.0, 0.142 * k, 0.103 * k, 0, 0), (1.06, 0.14 * k, 0.1 * k, 0, 0), (1.12, 0.148 * k, 0.104 * k, 0, 0),
                   (1.17, 0.16 * k, 0.11 * k, 0, 0), (1.21, 0.172 * k, 0.116 * k, 0, 0), (1.25, 0.18 * k, 0.12 * k, 0, 0),
                   (1.31, 0.186 * k, 0.12 * k, 0, 0), (1.365, 0.184 * k, 0.114 * k, 0, 0), (1.415, 0.16 * k, 0.1 * k, 0, 0),
                   (1.445, 0.1, 0.08, 0, 0), (1.47, 0.058, 0.06, 0, 0)], n, reg["torso"], body, cap_bottom=reg["sole"], skip=holes)
    r.tube([(1.47, 0.056, 0.06, 0, 0), (1.5, 0.054, 0.058, 0, -0.002), (1.525, 0.07, 0.076, 0, -0.004),
            (1.555, 0.09, 0.098, 0, -0.006), (1.59, 0.101, 0.112, 0, -0.006), (1.63, 0.106, 0.117, 0, -0.005),
            (1.67, 0.106, 0.116, 0, -0.004), (1.705, 0.098, 0.108, 0, -0.003), (1.735, 0.078, 0.088, 0, -0.002),
            (1.755, 0.045, 0.052, 0, 0.0)], n, reg["head"], body, cap_top=reg["crown"], v_range=(1.47, 1.76))
    t = limb
    for side, sx in (("l", -1.0), ("r", 1.0)):
        s = side
        # Рука вращена в торс: рукав начинается с края окна в боку, плечо, локоть, запястье, кисть.
        x = sx * 0.228 * k

        def aw(index, y, s=s):
            # У окна ткань ещё держится за грудь, дальше по руке веса идут по высоте.
            if index == 0:
                return [("chest", 0.8), ("arm_" + s, 0.2)]
            if index == 1:
                return [("chest", 0.45), ("arm_" + s, 0.55)]
            if index == 2:
                return [("chest", 0.12), ("arm_" + s, 0.88)]
            return blend(y, [("hand_" + s, 0.0, 0.855), ("fore_" + s, 0.895, 1.075), ("arm_" + s, 1.165, 9.0)])

        k0 = 3 if sx > 0 else 11
        top = 0.5 + 0.5 * t
        r.sleeve(rows, 8, 11, k0, k0 + 2, sx,
                 [((sx * 0.202 * k, 1.352, 0.0), 28.0, 0.074 * top, 0.076 * top), ((sx * 0.224 * k, 1.318, 0.0), 62.0, 0.068 * top, 0.07 * top)],
                 [(1.27, 0.06 * t, 0.064 * t, x, 0), (1.21, 0.055 * t, 0.059 * t, x * 1.01, 0), (1.165, 0.05 * t, 0.054 * t, x * 1.015, 0),
                  (1.13, 0.047 * t, 0.051 * t, x * 1.02, 0), (1.1, 0.046 * t, 0.05 * t, x * 1.022, 0), (1.06, 0.045 * t, 0.048 * t, x * 1.026, 0),
                  (1.0, 0.042 * t, 0.045 * t, x * 1.033, 0), (0.93, 0.037 * t, 0.04 * t, x * 1.042, 0), (0.875, 0.031 * t, 0.034 * t, x * 1.05, 0),
                  (0.85, 0.03, 0.04, x * 1.054, 0), (0.81, 0.033, 0.05, x * 1.058, 0), (0.77, 0.031, 0.047, x * 1.062, 0),
                  (0.745, 0.024, 0.034, x * 1.064, 0)], reg["arm"], aw, cap=reg["skin"])
        # Нога: клёш с колыханием у низа или ровная штанина под сапог.
        x = sx * 0.095 * k
        lw = lambda y, s=s: blend(y, [("foot_" + s, 0.0, 0.07), ("shin_" + s, 0.11, 0.43), ("leg_" + s, 0.55, 0.86), ("hips", 0.96, 9.0)])
        if leg == "bell":
            hem = lambda y: max(0.0, min(1.0, (0.36 - y) / 0.26)) * 0.55
            low = [(0.07, 0.094, 0.1, x, 0.004), (0.1, 0.092, 0.098, x, 0.004), (0.16, 0.084, 0.09, x, 0.003), (0.24, 0.076, 0.082, x, 0.002)]
        else:
            hem = None
            low = [(0.07, 0.056 * t, 0.06 * t, x, 0.0), (0.12, 0.06 * t, 0.064 * t, x, 0.0), (0.18, 0.066 * t, 0.07 * t, x, 0.002),
                   (0.25, 0.071 * t, 0.076 * t, x, 0.004)]
        r.tube(low + [(0.32, 0.071 * t, 0.077 * t, x, 0.001), (0.4, 0.068 * t, 0.074 * t, x, 0), (0.45, 0.067 * t, 0.073 * t, x, 0),
                      (0.49, 0.068 * t, 0.075 * t, x, -0.002), (0.53, 0.07 * t, 0.077 * t, x, -0.002), (0.6, 0.076 * t, 0.082 * t, x, 0),
                      (0.7, 0.085 * t, 0.091 * t, x, 0), (0.8, 0.093 * t, 0.099 * t, x, 0), (0.88, 0.097 * t, 0.103 * t, x * 0.98, 0),
                      (0.95, 0.09 * t, 0.098 * t, x * 0.9, 0)], 12, reg["leg"], lw, hem, cap_bottom=reg["sole"], v_range=(0.07, 0.95))
        # Сапог: носок вперёд (−Z).
        fw = lambda y, s=s: [("foot_" + s, 1.0)]
        r.tube([(0.0, 0.05, 0.115, x, -0.045), (0.035, 0.054, 0.12, x, -0.047), (0.07, 0.052, 0.1, x, -0.03),
                (0.105, 0.05, 0.062, x, -0.004), (0.14, 0.048, 0.055, x, 0.0)], 10, reg["boot"], fw, cap_bottom=reg["sole"], cap_top=reg["sole"])
    return r, rows


def add_tricorn(r, reg):
    """Треуголка: тулья и поля, загнутые вверх; сидит на голове."""
    hw = lambda y: [("head", 1.0)]
    r.tube([(1.7, 0.118, 0.128, 0, -0.004), (1.715, 0.205, 0.215, 0, -0.004), (1.74, 0.225, 0.235, 0, -0.004),
            (1.765, 0.19, 0.2, 0, -0.004)], 16, reg["hat"], hw, v_range=(1.7, 1.86))
    r.tube([(1.71, 0.112, 0.122, 0, -0.004), (1.76, 0.108, 0.118, 0, -0.004), (1.81, 0.094, 0.104, 0, -0.004),
            (1.835, 0.06, 0.066, 0, -0.004)], 16, reg["hat"], hw, cap_top=reg["sole"], v_range=(1.64, 1.86))


def pirate_sailor():
    """Матрос: тельняшка, штаны клёш, сапоги, бандана с хвостами."""
    p = paint_sailor()
    reg = regions(p)
    r, _ = build_body("hero", reg)
    # Хвосты банданы: две ленты из узла на затылке, ткань с пружинной костью.
    r.bone("tail", "head", (0.0, 1.665, 0.105))
    r.spring("tail", 45.0, 5.0, 1.2)
    for dx, lean in ((-0.025, -0.05), (0.03, 0.06)):
        pts = [(dx, 1.665 - 0.055 * i, 0.108 + 0.022 * i + abs(lean) * 0.1 * i) for i in range(6)]
        pts = [(x + lean * i * 0.2, y, z) for i, (x, y, z) in enumerate(pts)]
        r.strip(pts, (1.0, 0.0, 0.0), 0.028, reg["strip"], lambda t: [("head", 1.0 - t), ("tail", t)] if t < 1.0 else [("tail", 1.0)], 0.2)
    return r, p


# --- Пираты: капитан ----------------------------------------------------------------------------

COAT, COAT_D = rgb("9C2A26"), rgb("6A1C1C")
BLACK, FELT = rgb("1C1A1E"), rgb("26232A")
BONE, BONE_D = rgb("E4DCC4"), rgb("A89C80")
STEEL = rgb("B8BEC8")


def paint_captain():
    """Атлас капитана: красный камзол с золотом, жабо, борода, белые бриджи, высокие сапоги, полы, треуголка."""
    p = Paint(31)
    # Камзол: борта с золотыми пуговицами, жабо у ворота, кушак.
    p.rect(0, 0, 32, 22, COAT, 128)
    p.weave(0, 0, 32, 22, 0.4, 0.05)
    p.uneven(0, 0, 32, 22, 0.08, 3.0)
    p.poly([(13.2, 0), (18.8, 0), (17.2, 6.5), (14.8, 6.5)], rgb("EEE8DA"), 150)
    for i in range(4):
        p.fold([(14.2, 1.2 + i * 1.5), (16, 1.9 + i * 1.5), (17.8, 1.2 + i * 1.5)], 0.3, 0.84, 30)
    for sx in (-1.0, 1.0):
        p.poly([(16 + sx * 2.9, 0), (16 + sx * 6.4, 0), (16 + sx * 3.0, 9.5), (16 + sx * 1.5, 7.0)], COAT_D, 140)
        p.line([(16 + sx * 6.4, 0), (16 + sx * 3.0, 9.5), (16 + sx * 2.4, 18.4)], GOLD, 0.34, 152)
        for i in range(5):
            p.ellipse(16 + sx * 3.5, 8.2 + i * 2.3, 0.5, 0.5, GOLD, 170)
            p.ellipse(16 + sx * 3.5 - 0.12, 8.08 + i * 2.3, 0.2, 0.2, rgb("FFF2B0"))
        # Эполет на плече.
        p.rect(16 + sx * 11.6 - 2.2, 0.4, 4.4, 1.8, GOLD, 165)
        for i in range(5):
            p.line([(16 + sx * 11.6 - 1.8 + i * 0.9, 2.2), (16 + sx * 11.6 - 1.8 + i * 0.9, 3.3)], GOLD_D, 0.24, 150)
    p.rect(0, 17.4, 32, 2.6, rgb("D8B25A"), 152)
    p.wrinkles(0, 17.5, 32, 2.4, 10, 3.0, 0.15, 0.82)
    p.rect(0, 20.0, 32, 2.0, COAT, 128)
    p.wrinkles(0, 6, 32, 11, 12, 3.4, 0.4, 0.88)
    p.stains(0, 8, 32, 9, 4, 1.4, 0.88)
    p.shade_v(0, 0, 32, 17.4, 1.04, 0.9)
    p.shade_round(0, 0, 32, 22, 0.72)
    # Голова: смуглая кожа, чёрная борода и усы, повязка на глазу.
    p.rect(32, 0, 32, 20, SKIN, 128)
    p.rect(32, 3.0, 9.0, 9.5, BLACK, 138)
    p.rect(55.0, 3.0, 9.0, 9.5, BLACK, 138)
    p.rect(32, 0, 32, 3.4, BLACK, 134)
    beard = [(41.0, 10.6), (43.0, 12.0), (48, 12.6), (53.0, 12.0), (55.0, 10.6), (55.2, 16.0), (51.5, 19.4), (48, 20), (44.5, 19.4), (40.8, 16.0)]
    p.poly(beard, BLACK, 150)
    p.speckle(41, 11, 14, 8.6, 260, rgb("3A3640"), 0.08)
    for i in range(9):
        p.fold([(42.4 + i * 1.4, 12.8), (42.8 + i * 1.3, 19.0)], 0.22, 0.8, 26)
    for sx in (-1.0, 1.0):
        ex = 48 + sx * 2.9
        p.line([(ex - 1.5, 6.6), (ex, 6.1), (ex + 1.5, 6.6 + 0.2 * sx)], BLACK, 0.6, 142)
        p.ellipse(48 + sx * 8.2, 9.3, 0.9, 1.5, mul(SKIN, 0.92), 140)
        p.line([(48 + sx * 0.3, 12.3), (48 + sx * 2.2, 12.0), (48 + sx * 3.6, 12.9)], BLACK, 0.55, 150)
    p.ellipse(50.9, 8.1, 1.15, 0.72, rgb("F4EEE2"), 132)
    p.ellipse(51.0, 8.15, 0.5, 0.6, rgb("2A2018"))
    p.ellipse(45.1, 8.2, 1.7, 1.45, BLACK, 150)
    p.line([(40.5, 5.2), (45.1, 8.0), (55.5, 4.6)], BLACK, 0.3, 146)
    p.poly([(47.2, 8.0), (48.8, 8.0), (49.5, 11.1), (46.5, 11.1)], SKIN_L, 152)
    p.line([(46.7, 11.2), (48, 11.6), (49.3, 11.2)], SKIN_D, 0.3, 112)
    p.grain(41, 3.4, 14, 8.0, 0.04, 0.9, 5.0)
    p.line([(43.2, 4.3), (52.8, 4.2)], SKIN_D, 0.1)
    p.line([(44.0, 5.0), (52.0, 4.9)], SKIN_D, 0.08)
    p.shade_round(32, 0, 32, 20, 0.8)
    # Рукав камзола во всю длину, золотой обшлаг, кисть.
    p.rect(0, 22, 16, 26, COAT, 128)
    p.weave(0, 22, 16, 21, 0.4, 0.05)
    p.uneven(0, 22, 16, 21, 0.08, 2.5)
    p.wrinkles(0, 24, 16, 15, 12, 2.8, 0.35, 0.88)
    for fy in (33.0, 33.9):
        p.fold([(2, fy), (8, fy + 0.4), (14, fy)], 0.4, 0.84, 26)
    p.rect(0, 39.6, 16, 3.2, COAT_D, 146)
    p.rect(0, 39.5, 16, 0.5, GOLD, 158)
    p.rect(0, 42.6, 16, 0.5, GOLD, 158)
    for bx in (4.0, 8.0, 12.0):
        p.ellipse(bx, 41.2, 0.42, 0.42, GOLD, 168)
    p.rect(0, 43.1, 16, 0.8, rgb("EEE8DA"), 150)
    p.rect(0, 43.9, 16, 4.1, SKIN, 128)
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.line([(fx, 45.8), (fx, 48)], SKIN_D, 0.2, 112)
    p.shade_round(0, 22, 16, 26, 0.74)
    # Нога: белые бриджи до колена, ниже высокий чёрный сапог с отворотом.
    p.rect(16, 22, 20, 34, rgb("E4DCCA"), 128)
    p.weave(16, 22, 20, 17, 0.36, 0.05)
    p.wrinkles(16, 23, 20, 14, 12, 3.2, 0.4, 0.88)
    p.stains(16, 30, 20, 8, 4, 1.2, 0.9)
    p.rect(16, 39.0, 20, 17, BLACK, 136)
    p.grain(16, 39.0, 20, 17, 0.14, 1.6, 16.0)
    p.rect(16, 38.2, 20, 2.6, rgb("3A3238"), 158)
    p.fold([(16, 40.9), (36, 40.9)], 0.4, 0.6, 50)
    p.stitch([(16, 38.7), (36, 38.7)], rgb("8A7A60"), 0.1, 0.5)
    p.wrinkles(16, 44, 20, 9, 9, 3.2, 0.2, 0.75, 40)
    ys, xs = p._slice(22, 41, 8, 14)
    gx, gy = p._grid(22, 41, 8, 14)
    p._apply(22, 41, 8, 14, 1.0 + 0.55 * np.exp(-(((gx - 26) / 1.1) ** 2)))
    p.shade_round(16, 22, 20, 34, 0.74)
    # Сапог, подошва, кожа.
    p.rect(40, 24, 12, 6, BLACK, 128)
    p.grain(40, 24, 12, 6, 0.14, 1.4, 14.0)
    p.wrinkles(40, 24.3, 12, 5.4, 8, 2.4, 0.4, 0.75, 34)
    p.rect(44.6, 24.4, 2.8, 2.0, GOLD, 160)
    p.rect(45.3, 24.9, 1.4, 1.0, BLACK, 130)
    p.shade_round(40, 24, 12, 6, 0.7)
    p.rect(54, 24, 6, 6, BLACK, 128)
    p.rect(54, 32, 6, 6, SKIN, 128)
    # Перо на шляпе.
    p.rect(40, 34, 12, 8, rgb("ECE6D8"), 128)
    for i in range(18):
        p.fold([(40.3 + i * 0.66, 34), (40.9 + i * 0.66, 42)], 0.16, 0.8, 24)
    p.fold([(46, 34), (46, 42)], 0.35, 0.7, 40)
    # Полы камзола: ткань, золотой кант по краю и по низу, складки сверху вниз.
    p.rect(36, 44, 28, 20, COAT, 128)
    p.weave(36, 44, 28, 20, 0.4, 0.05)
    p.uneven(36, 44, 28, 20, 0.09, 3.0)
    for i in range(9):
        p.fold([(37.5 + i * 3.1, 44.4), (37.2 + i * 3.25, 62.6)], 0.55, 0.82, 40)
    p.rect(36, 62.4, 28, 0.7, GOLD, 158)
    p.stains(36, 56, 28, 6, 5, 1.3, 0.86)
    p.shade_v(36, 44, 28, 20, 1.02, 0.84)
    # Треуголка: чёрный фетр, золотой галун.
    p.rect(0, 48, 16, 16, FELT, 128)
    p.grain(0, 48, 16, 16, 0.12, 1.2, 12.0)
    p.rect(0, 48, 16, 0.9, GOLD, 160)
    p.rect(0, 57.6, 16, 0.6, GOLD, 156)
    p.stitch([(0, 49.3), (16, 49.3)], GOLD_D, 0.1, 0.45)
    return p


def pirate_captain():
    """Капитан: крупнее матроса, камзол с полами на пружинной кости, треуголка с пером, борода."""
    p = paint_captain()
    reg = regions(p)
    r, _ = build_body("captain", reg, bulk=1.16, leg="straight")
    add_tricorn(r, reg)
    # Полы камзола: колокол от пояса до середины бедра, спереди распахнут; качается целиком и
    # отстаёт от шага.
    r.bone("skirt", "hips", (0.0, 1.0, 0.02))
    r.spring("skirt", 70.0, 6.0, 0.4, (0.0, -1.0, 0.0))

    def sw(y):
        t = max(0.0, min(1.0, (1.0 - y) / 0.4))
        return [("hips", 1.0 - 0.75 * t), ("skirt", 0.75 * t)]

    open_front = {(i, kk) for i in range(5) for kk in (7, 8)}
    r.tube([(0.56, 0.272, 0.262, 0, -0.022), (0.66, 0.254, 0.236, 0, -0.016), (0.76, 0.232, 0.204, 0, -0.01),
            (0.86, 0.206, 0.17, 0, -0.004), (0.94, 0.184, 0.142, 0, 0.0), (1.0, 0.17, 0.126, 0, 0.0)], 16, reg["skirt"], sw,
           lambda y: max(0.0, min(1.0, (0.9 - y) / 0.34)) * 0.5, skip=open_front)
    # Перо: лента от тульи назад и вверх, на своей пружинной кости.
    r.bone("feather", "head", (0.07, 1.8, 0.06))
    r.spring("feather", 55.0, 5.0, 0.3, (0.3, 0.55, 0.78))
    pts = [(0.07 + 0.012 * i, 1.8 + 0.036 * i - 0.004 * i * i, 0.06 + 0.05 * i) for i in range(7)]
    r.strip(pts, (1.0, 0.0, 0.0), 0.04, reg["strip"], lambda t: [("head", 1.0 - t), ("feather", t)] if t < 1.0 else [("feather", 1.0)], 0.1, 0.8, 0.5)
    return r, p


# --- Пираты: скелет -----------------------------------------------------------------------------

def paint_skeleton():
    """Атлас скелета: рёбра с вырезами, череп, кости рук и ног, рваный кушак, треуголка."""
    p = Paint(53)
    # Грудная клетка: кость, между рёбрами пусто; грудина спереди, хребет сзади, внизу таз.
    p.rect(0, 0, 32, 22, BONE, 128)
    p.grain(0, 0, 32, 22, 0.08, 1.4, 12.0)
    for i in range(5):
        y = 2.2 + i * 2.5
        for x0, x1 in ((1.6, 14.6), (17.4, 30.4)):
            p.cut(x0, y + 1.2, x1 - x0, 1.3)
        p.fold([(1.0, y + 0.4), (31.0, y + 0.4)], 0.3, 0.86, 26)
    p.cut(1.6, 14.6, 28.8, 3.0)
    p.rect(15.0, 0, 2.0, 15.0, mul(BONE, 0.94), 140)
    for sx in (-1.0, 1.0):
        p.cut_ellipse(16 + sx * 5.2, 20.2, 2.6, 1.3)
    p.stains(0, 0, 32, 22, 9, 1.2, 0.84)
    p.speckle(0, 0, 32, 22, 70, BONE_D, 0.09)
    p.shade_round(0, 0, 32, 22, 0.7)
    # Череп: глазницы, провал носа, зубы, трещина.
    p.rect(32, 0, 32, 20, BONE, 128)
    p.grain(32, 0, 32, 20, 0.07, 1.4, 12.0)
    for sx in (-1.0, 1.0):
        p.ellipse(48 + sx * 3.0, 8.0, 1.9, 1.7, rgb("1A1410"), 70)
        p.ellipse(48 + sx * 3.0, 8.3, 0.5, 0.45, rgb("C8482E"))
        p.fold([(48 + sx * 6.4, 9.5), (48 + sx * 5.4, 12.6), (48 + sx * 3.8, 14.2)], 0.5, 0.78, 30)
    p.poly([(48, 9.8), (49.0, 11.9), (47.0, 11.9)], rgb("1A1410"), 70)
    p.rect(43.6, 13.3, 8.8, 2.3, mul(BONE, 1.05), 140)
    p.line([(43.6, 14.45), (52.4, 14.45)], rgb("2A2018"), 0.22, 90)
    for i in range(8):
        p.line([(44.2 + i * 1.1, 13.4), (44.2 + i * 1.1, 15.5)], rgb("5A4C3A"), 0.14, 100)
    p.fold([(49.6, 0.8), (50.6, 2.6), (49.9, 4.2), (51.2, 5.6)], 0.22, 0.6, 50)
    p.cut(40.4, 16.6, 15.2, 3.4)
    p.stains(32, 0, 32, 20, 8, 1.3, 0.86)
    p.speckle(32, 0, 32, 20, 60, BONE_D, 0.09)
    p.shade_round(32, 0, 32, 20, 0.76)
    # Кости рук и ног: утолщения суставов, трещины.
    for x, y, w, h, joints in ((0, 22, 16, 26, (22.6, 32.6, 42.8)), (16, 22, 20, 34, (23.0, 39.6, 54.2))):
        p.rect(x, y, w, h, BONE, 128)
        p.grain(x, y, w, h, 0.08, 1.4, 12.0)
        for jy in joints:
            p.rect(x, jy - 0.9, w, 1.8, mul(BONE, 1.06), 150)
            p.fold([(x, jy), (x + w, jy)], 0.3, 0.7, 44)
        p.wrinkles(x, y + 1, w, h - 2, 8, 2.4, 2.0, 0.78, 30)
        p.stains(x, y, w, h, 7, 1.1, 0.84)
        p.speckle(x, y, w, h, 60, BONE_D, 0.08)
        p.shade_round(x, y, w, h, 0.66)
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.line([(fx, 43.8), (fx, 48)], rgb("3A3024"), 0.26, 90)
    # Стопа, подошва, «кожа» (торец кости), рваный кушак, клинок, треуголка.
    p.rect(40, 24, 12, 6, BONE, 128)
    p.grain(40, 24, 12, 6, 0.08, 1.2, 10.0)
    for i in range(5):
        p.line([(41.4 + i * 2.2, 24), (41.4 + i * 2.2, 30)], rgb("5A4C3A"), 0.2, 96)
    p.rect(54, 24, 6, 6, BONE_D, 128)
    p.rect(54, 32, 6, 6, BONE, 128)
    p.rect(40, 34, 12, 8, RED, 128)
    p.weave(40, 34, 12, 8, 0.3, 0.07)
    p.wrinkles(40, 34, 12, 8, 7, 3.0, 0.8, 0.8)
    p.stains(40, 34, 12, 8, 5, 1.0, 0.8)
    for i in range(6):
        p.cut(40.4 + i * 2.0, 40.6 + (i % 2) * 0.6, 1.1, 1.6)
    p.rect(36, 44, 28, 20, STEEL, 128)
    ys, xs = p._slice(36, 44, 28, 20)
    gx, gy = p._grid(36, 44, 28, 20)
    p._apply(36, 44, 28, 20, 0.78 + 0.34 * np.abs((gx - 36) / 28.0 * 2.0 - 1.0))
    p.grain(36, 44, 28, 20, 0.06, 0.8, 6.0)
    p.stains(36, 44, 28, 20, 8, 1.2, 0.82)
    p.rect(0, 48, 16, 16, FELT, 128)
    p.grain(0, 48, 16, 16, 0.14, 1.2, 12.0)
    p.rect(0, 48, 16, 0.8, BONE_D, 150)
    p.stains(0, 48, 16, 16, 6, 1.4, 0.8)
    return p


def pirate_skeleton():
    """Скелет: тонкие кости, грудная клетка с просветами, треуголка, сабля, рваный кушак."""
    p = paint_skeleton()
    reg = regions(p)
    r, _ = build_body("enemy", reg, bulk=0.9, limb=0.46, leg="straight")
    add_tricorn(r, reg)
    # Рваный кушак на поясе: два хвоста на пружинной кости.
    r.bone("sash", "hips", (-0.1, 0.98, 0.07))
    r.spring("sash", 40.0, 5.0, 1.0)
    for dx, lean in ((-0.13, -0.03), (-0.07, 0.03)):
        pts = [(dx + lean * i, 0.99 - 0.06 * i, 0.085 + 0.012 * i) for i in range(6)]
        r.strip(pts, (1.0, 0.0, 0.0), 0.032, reg["strip"], lambda t: [("hips", 1.0 - t), ("sash", t)] if t < 1.0 else [("sash", 1.0)], 0.2)
    # Сабля в правой руке: клинок вперёд, жёсткий.
    hand_x = 0.228 * 0.9 * 1.058
    pts = [(hand_x, 0.8 + 0.012 * i, -0.02 - 0.115 * i) for i in range(7)]
    r.strip(pts, (0.0, 1.0, 0.0), 0.03, reg["skirt"], lambda t: [("hand_r", 1.0)], 0.0, 0.0, 0.75)
    return r, p


# --- Пираты: реквизит и уровень «продвинутых» ---------------------------------------------------
# Сетки реквизита пишет `lowpoly_meshes.py` (плотный набор `threed`); здесь его текстуры
# рисуются заново крупными по той же раскладке атласа и ложатся поверх увеличенных.

WOOD, WOOD_D = rgb("7A5230"), rgb("4E3420")
IRON, IRON_L = rgb("3A3C44"), rgb("6C707C")
SAND, SAND_D, SAND_L = rgb("D8BC82"), rgb("B89860"), rgb("ECD6A0")


def paint_sand():
    """Песок: рябь от ветра, зерно, редкие камешки и ракушки. Стыкуется по краям."""
    p = Paint(301)
    low = p.tile_noise(4, 3)
    mid = p.tile_noise(16, 3)

    def fn(gx, gy):
        ripple = np.sin(2 * np.pi * (gx * 5.0 / UNITS + 0.5 * np.sin(2 * np.pi * gy * 2.0 / UNITS) + 0.25 * low))
        tone = 1.0 + 0.06 * ripple + 0.07 * low + 0.04 * mid
        return np.array(SAND, dtype=np.float32)[None, None, :] * tone[..., None], 128.0 + ripple * 26.0 + mid * 14.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 2600, mul(SAND, 0.82), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 1800, mul(SAND, 1.12), 0.06)
    for _ in range(26):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.25, 0.6)
        p.ellipse(x + 0.12, y + 0.16, r, r * 0.8, mul(SAND, 0.7), 110)
        p.ellipse(x, y, r, r * 0.8, rgb("8E8A84") if p.rng.random() < 0.6 else rgb("E8DCC8"), 190)
    return p


def paint_planks():
    """Настил: восемь досок с волокнами и щелями, стыки вразбежку с гвоздями. Стыкуется по краям."""
    p = Paint(303)
    p.wood(0, 0, 64, 64, 8, True, WOOD, 0.3)
    for i in range(8):
        for y in ((15.5, 47.5) if i % 2 == 0 else (31.5, 63.3)):
            p.fold([(i * 8 + 0.4, y), (i * 8 + 7.6, y)], 0.4, 0.5, 80)
            for nx in (2.0, 6.0):
                for ny in (-1.7, 1.7):
                    p.ellipse(i * 8 + nx, min(max(y + ny, 0.6), 63.4), 0.34, 0.34, IRON, 170)
                    p.ellipse(i * 8 + nx - 0.1, min(max(y + ny, 0.6), 63.4) - 0.1, 0.12, 0.12, IRON_L)
    for _ in range(7):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(6, 58)
        p.ellipse(x, y, 0.9, 1.3, mul(WOOD_D, 0.9), 104)
        p.ellipse(x, y, 0.45, 0.7, mul(WOOD_D, 0.6), 90)
    p.stains(2, 2, 60, 60, 16, 2.2, 0.88)
    return p


def paint_water():
    """Вода: плавные волны от тёмной глубины к светлым гребням с пеной. Стыкуется по краям."""
    p = Paint(305)
    deep, mid, foam = np.array(rgb("1B4A86"), dtype=np.float32), np.array(rgb("3A7CC2"), dtype=np.float32), np.array(rgb("C4E2F4"), dtype=np.float32)
    noise = p.tile_noise(8, 3)

    def fn(gx, gy):
        w = np.sin((gx + 6.0 * np.sin(gy * np.pi / 8.0)) * np.pi / 16.0) + np.sin((gy * 2.0 + gx) * np.pi / 16.0) + 0.5 * noise
        t = _smooth_np(np.clip((w + 1.2) / 2.6, 0.0, 1.0))
        crest = _smooth_np(np.clip((w - 1.35) / 0.5, 0.0, 1.0))
        color = deep[None, None, :] * (1.0 - t[..., None]) + mid[None, None, :] * t[..., None]
        color = color * (1.0 - crest[..., None]) + foam[None, None, :] * crest[..., None]
        return color, 128.0 + w * 34.0
    p.field(fn)
    return p


def paint_crate():
    """Ящик (атлас 32×32, здесь вдвое крупнее): четыре бока 16×32 в ряд, крышка 32×32 под ними."""
    p = Paint(307)
    for i in range(4):
        x = i * 16
        p.wood(x, 0, 16, 32, 3, True, WOOD, 0.22)
        # Рама, раскос, гвозди в углах.
        frame = mul(WOOD_D, 1.05)
        for rx, ry, rw, rh in ((x, 0, 16, 3.4), (x, 28.6, 16, 3.4), (x, 0, 2.6, 32), (x + 13.4, 0, 2.6, 32)):
            p.rect(rx, ry, rw, rh, frame, 172)
        p.poly([(x + 2.6, 26.0), (x + 4.6, 28.6), (x + 13.4, 6.0), (x + 11.4, 3.4)], frame, 164)
        for nx, ny in ((1.3, 1.7), (14.7, 1.7), (1.3, 30.3), (14.7, 30.3)):
            p.ellipse(x + nx, ny, 0.5, 0.5, IRON, 196)
            p.ellipse(x + nx - 0.14, ny - 0.14, 0.18, 0.18, IRON_L)
    p.rect(21.6, 12.4, 5.2, 5.0, rgb("8E2A26"), 140)
    p.line([(22.6, 13.4), (25.8, 16.4)], rgb("E8D8C0"), 0.5)
    p.line([(25.8, 13.4), (22.6, 16.4)], rgb("E8D8C0"), 0.5)
    p.grain(0, 0, 64, 32, 0.08, 1.2, 10.0)
    p.stains(0, 0, 64, 32, 12, 1.6, 0.84)
    p.shade_v(0, 0, 64, 32, 1.05, 0.82)
    p.wood(0, 32, 32, 32, 4, False, WOOD, 0.22)
    for rx, ry, rw, rh in ((0, 32, 32, 2.8), (0, 61.2, 32, 2.8), (0, 32, 2.8, 32), (29.2, 32, 2.8, 32)):
        p.rect(rx, ry, rw, rh, mul(WOOD_D, 1.05), 172)
    p.stains(0, 32, 32, 32, 6, 1.6, 0.86)
    return p


def paint_barrel():
    """Бочка (атлас 32×32, здесь вдвое крупнее): клёпки 64×48 вокруг, два железных обруча, крышка 16×16."""
    p = Paint(309)
    p.wood(0, 0, 64, 48, 12, True, WOOD, 0.24)
    for y in (6.0, 38.0):
        p.rect(0, y, 64, 3.6, IRON, 190)
        p.rect(0, y, 64, 0.9, IRON_L, 198)
        p.grain(0, y, 64, 3.6, 0.14, 1.0, 8.0)
        for i in range(8):
            p.ellipse(4 + i * 8, y + 2.0, 0.5, 0.5, IRON_L, 215)
        p.fold([(0, y + 3.9), (64, y + 3.9)], 0.45, 0.6, 60)
    p.stains(0, 10, 64, 28, 14, 1.8, 0.84)
    p.shade_v(0, 0, 64, 48, 1.08, 0.8)
    p.wood(0, 48, 16, 16, 3, False, WOOD, 0.2)
    p.ellipse(8, 56, 7.6, 7.6, WOOD_D, 100)
    p.ellipse(8, 56, 6.8, 6.8, mul(WOOD, 0.95), 140)
    for i in range(3):
        p.fold([(1.6, 51.6 + i * 4.4), (14.4, 51.6 + i * 4.4)], 0.3, 0.62, 60)
    p.stains(1, 49, 14, 14, 4, 1.2, 0.84)
    return p


def paint_keg():
    """Бочонок: та же раскладка, что у бочки, свой рисунок волокон."""
    p = paint_barrel()
    p.stains(0, 10, 64, 28, 6, 2.2, 0.8)
    return p


def _bands(p, x, y, w, h, xs, width=3.0):
    """Железные полосы поперёк досок с заклёпками."""
    for bx in xs:
        p.rect(x + bx, y, width, h, IRON, 188)
        p.rect(x + bx, y, width * 0.3, h, IRON_L, 196)
        for i in range(int(h // 4) + 1):
            p.ellipse(x + bx + width / 2.0, y + 1.6 + i * 4.0, 0.42, 0.42, IRON_L, 214)
    p.grain(x, y, w, h, 0.07, 1.0, 8.0)


def paint_chest():
    """Сундук (атлас 64×32: по вертикали единицы вдвое крупнее): бока, бока крышки, верх крышки, дно."""
    p = Paint(311)
    bands = (6.6, 22.6, 38.6, 54.6)
    p.wood(0, 0, 64, 24, 4, False, WOOD, 0.3)
    _bands(p, 0, 0, 64, 24, bands)
    p.rect(5.6, 2.0, 5.0, 8.0, GOLD_D, 205)
    p.ellipse(8.1, 5.0, 0.9, 1.4, BLACK, 110)
    p.rect(7.8, 5.6, 0.6, 2.6, BLACK, 110)
    p.stains(0, 0, 64, 24, 10, 1.8, 0.84)
    p.shade_v(0, 0, 64, 24, 1.04, 0.8)
    p.wood(0, 24, 64, 16, 3, False, mul(WOOD, 1.06), 0.3)
    _bands(p, 0, 24, 64, 16, bands)
    p.rect(0, 24, 64, 1.4, GOLD_D, 190)
    p.shade_v(0, 24, 64, 16, 1.08, 0.86)
    p.wood(0, 40, 24, 24, 4, False, mul(WOOD, 1.08), 0.3)
    _bands(p, 0, 40, 24, 24, (4.0, 17.0))
    p.stains(0, 40, 24, 24, 5, 1.6, 0.86)
    p.rect(24, 40, 4, 8, WOOD_D, 128)
    return p


def _wheel(p, x, y, w, h):
    """Колесо: обод, спицы, железная ступица; вокруг прозрачно. Кусок `w`×`h` единиц."""
    cx, cy, rx, ry = x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0
    p.cut(x, y, w, h)
    p.solid_ellipse(cx, cy, rx * 0.97, ry * 0.97)
    p.ellipse(cx, cy, rx * 0.97, ry * 0.97, WOOD_D, 170)
    p.ellipse(cx, cy, rx * 0.72, ry * 0.72, rgb("241C16"), 80)
    for i in range(8):
        a = math.pi * i / 4.0
        p.line([(cx, cy), (cx + math.cos(a) * rx * 0.78, cy + math.sin(a) * ry * 0.78)], WOOD, rx * 0.13, 160)
    p.ellipse(cx, cy, rx * 0.26, ry * 0.26, IRON, 200)
    p.ellipse(cx, cy, rx * 0.1, ry * 0.1, IRON_L, 220)
    for i in range(12):
        a = math.pi * i / 6.0
        p.ellipse(cx + math.cos(a) * rx * 0.86, cy + math.sin(a) * ry * 0.86, rx * 0.035, ry * 0.035, IRON_L, 210)


def paint_cannon():
    """Пушка (атлас 64×32): ствол, жерло, колесо, обод колеса, лафет."""
    p = Paint(313)
    iron = rgb("34363C")
    p.rect(0, 0, 32, 32, iron, 128)
    for by, bh in ((1.0, 2.6), (9.0, 1.6), (20.0, 1.6), (27.4, 3.0)):
        p.rect(0, by, 32, bh, mul(iron, 1.3), 180)
        p.fold([(0, by + bh + 0.3), (32, by + bh + 0.3)], 0.4, 0.6, 50)
    p.grain(0, 0, 32, 32, 0.12, 1.4, 12.0)
    p.stains(0, 0, 32, 32, 9, 1.4, 0.8)
    p.speckle(0, 0, 32, 32, 90, rgb("6A4A36"), 0.1)
    p.shade_round(0, 0, 32, 32, 0.55, 1.6)
    p.rect(32, 0, 8, 16, mul(iron, 1.2), 150)
    p.ellipse(36, 8, 2.8, 5.6, rgb("0C0C0E"), 40)
    _wheel(p, 40, 0, 16, 32)
    p.rect(56, 0, 8, 8, WOOD_D, 128)
    p.grain(56, 0, 8, 8, 0.1)
    p.wood(0, 32, 32, 24, 3, False, WOOD, 0.3)
    _bands(p, 0, 32, 32, 24, (3.0, 26.0), 2.4)
    p.stains(0, 32, 32, 24, 6, 1.6, 0.84)
    return p


def paint_palm():
    """Пальма (атлас 32×32, здесь вдвое крупнее): ствол с кольцами, лист с вырезанными перьями."""
    p = Paint(315)
    bark, bark_d = rgb("8A6A42"), rgb("5C4428")
    p.rect(0, 0, 32, 64, bark, 128)
    for i in range(16):
        y = i * 4.0
        p.rect(0, y, 32, 1.1, bark_d, 96)
        p.fold([(0, y + 1.3), (32, y + 1.3)], 0.4, 0.8, 30)
        for j in range(5):
            x = (j * 6.4 + (i % 2) * 3.2) % 32
            p.line([(x, y + 1.4), (x + 0.6, y + 3.6)], mul(bark, 1.18), 0.4, 150)
    p.grain(0, 0, 32, 64, 0.1, 1.2, 12.0)
    p.shade_round(0, 0, 32, 64, 0.7)
    leaf, leaf_d, leaf_l = rgb("3E8A3A"), rgb("255E2C"), rgb("7CC050")
    p.cut(32, 0, 32, 64)
    p.rect(32, 0, 32, 64, leaf, 128)
    count = 26
    for i in range(count):
        t = (i + 0.5) / count
        y = 2.0 + t * 60.0
        reach = 2.0 + 13.0 * math.sin(math.pi * min(t / 0.94, 1.0)) ** 0.7
        for side in (-1.0, 1.0):
            pts = [(48, y - 0.9), (48 + side * reach, y + 2.6), (48 + side * reach * 0.94, y + 3.5), (48, y + 0.9)]
            p.solid(pts)
            p.poly(pts, leaf_l if i % 3 == 0 else (leaf if i % 2 else mul(leaf, 0.9)), 140)
            p.line([(48, y), (48 + side * reach * 0.96, y + 3.0)], leaf_d, 0.18, 110)
    p.solid([(47.3, 0), (48.7, 0), (48.5, 63), (47.5, 63)])
    p.line([(48, 0), (48, 63)], leaf_d, 1.0, 160)
    p.grain(32, 0, 32, 64, 0.08, 1.0, 8.0)
    return p


def paint_rock():
    """Камень: гранёные пятна, трещины, мох."""
    p = Paint(317)
    stone = np.array(rgb("6E6A66"), dtype=np.float32)
    low, mid = p.tile_noise(4, 3), p.tile_noise(12, 3)

    def fn(gx, gy):
        tone = 1.0 + 0.16 * low + 0.1 * mid
        return stone[None, None, :] * tone[..., None], 128.0 + low * 40.0 + mid * 22.0
    p.field(fn)
    p.wrinkles(2, 2, 60, 60, 16, 9.0, 1.4, 0.62, 60)
    p.speckle(0.5, 0.5, 63, 63, 600, rgb("46423E"), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 400, rgb("96928A"), 0.08)
    for _ in range(9):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        p.stains(x - 3, y - 2, 6, 4, 2, 1.6, 0.9)
        p.speckle(x - 2.5, y - 1.5, 5, 3, 40, rgb("5E8A3E"), 0.16)
    return p


def paint_flag():
    """Флаг (атлас 64×32): чёрное полотнище с черепом и костями, древко, каменное основание."""
    p = Paint(319)
    p.rect(0, 0, 32, 40, BLACK, 128)
    p.weave(0, 0, 32, 40, 0.34, 0.1)
    p.uneven(0, 0, 32, 40, 0.14, 2.4)
    bone = rgb("ECE4D0")
    for sx in (-1.0, 1.0):
        p.line([(16 - sx * 8.0, 9.0), (16 + sx * 8.0, 31.0)], bone, 1.3, 150)
        for ex, ey in ((16 - sx * 8.0, 9.0), (16 + sx * 8.0, 31.0)):
            p.ellipse(ex - 0.6, ey - 0.7, 0.9, 1.5, bone, 150)
            p.ellipse(ex + 0.6, ey + 0.7, 0.9, 1.5, bone, 150)
    p.ellipse(16, 16.5, 5.2, 9.0, bone, 156)
    p.rect(12.8, 23.0, 6.4, 5.0, bone, 156)
    for sx in (-1.0, 1.0):
        p.ellipse(16 + sx * 2.1, 16.5, 1.4, 2.6, BLACK, 100)
    p.poly([(16, 20.2), (16.9, 23.0), (15.1, 23.0)], BLACK, 100)
    for i in range(5):
        p.line([(13.6 + i * 1.2, 24.4), (13.6 + i * 1.2, 27.6)], BLACK, 0.2)
    p.wrinkles(0, 2, 32, 36, 9, 5.0, 2.5, 0.8, 40)
    for i in range(7):
        p.cut(30.6 + (i % 2) * 0.5, 2.0 + i * 5.4, 1.4 - (i % 2) * 0.5, 1.8)
    p.wood(32, 0, 8, 64, 2, True, mul(WOOD, 0.9), 0.2)
    p.shade_round(32, 0, 8, 64, 0.6)
    p.rect(40, 0, 8, 16, rgb("6E6A66"), 128)
    p.grain(40, 0, 8, 16, 0.14, 1.2, 14.0)
    return p


def paint_lighthouse():
    """Маяк: башня в красную и белую полосу с кирпичом, окнами и дверью, фонарь, крыша, камень."""
    p = Paint(321)
    white, red = rgb("E8E2D4"), rgb("B5362E")
    for i in range(5):
        p.rect(0, i * 8.0, 64, 8.0, red if i % 2 == 0 else white, 128)
    # Кирпич: ряды со сдвигом.
    for row in range(20):
        y = row * 2.0
        p.fold([(0, y), (64, y)], 0.14, 0.86, 26)
        for col in range(17):
            x = col * 4.0 + (row % 2) * 2.0
            p.fold([(x, y), (x, y + 2.0)], 0.14, 0.88, 22)
    p.uneven(0, 0, 64, 40, 0.1, 3.0)
    p.stains(0, 0, 64, 40, 22, 2.0, 0.84)
    for wx, wy in ((8.0, 6.0), (40.0, 14.0), (24.0, 22.0), (56.0, 9.0)):
        p.rect(wx - 1.5, wy - 2.2, 3.0, 4.4, rgb("EBD9A8"), 160)
        p.rect(wx - 1.1, wy - 1.8, 2.2, 3.6, rgb("2A3440"), 90)
        p.line([(wx, wy - 1.8), (wx, wy + 1.8)], rgb("EBD9A8"), 0.2)
    p.rect(29.6, 31.4, 4.8, 8.6, WOOD_D, 110)
    p.wood(30.1, 32.0, 3.8, 8.0, 3, True, WOOD, 0.14)
    p.ellipse(33.2, 36.2, 0.3, 0.3, GOLD, 190)
    p.shade_v(0, 0, 64, 40, 1.04, 0.84)
    p.rect(0, 40, 32, 8, rgb("F6DE7A"), 150)
    ys, xs = p._slice(0, 40, 32, 8)
    gx, gy = p._grid(0, 40, 32, 8)
    p._apply(0, 40, 32, 8, 1.0 + 0.18 * np.cos((gx % 4.0 - 2.0) * 1.2))
    for i in range(9):
        p.rect(i * 4.0 - 0.35, 40, 0.7, 8, rgb("3A3C44"), 190)
    p.rect(0, 40, 32, 0.8, rgb("3A3C44"), 190)
    p.rect(0, 47.2, 32, 0.8, rgb("3A3C44"), 190)
    p.rect(32, 40, 16, 8, mul(red, 0.9), 128)
    for row in range(4):
        for col in range(9):
            p.fold([(32 + col * 2.0 + (row % 2), 40 + row * 2.0), (33 + col * 2.0 + (row % 2), 42 + row * 2.0)], 0.2, 0.74, 36)
        p.fold([(32, 40 + row * 2.0), (48, 40 + row * 2.0)], 0.2, 0.7, 40)
    p.rect(48, 40, 8, 8, rgb("6E6A66"), 128)
    p.grain(48, 40, 8, 8, 0.14, 1.2, 14.0)
    return p


def paint_cart(rival):
    """Шлюпка на колёсах: борт с полосой, палуба, колесо, обод, мачта, парус."""
    p = Paint(323 if not rival else 325)
    p.wood(0, 0, 64, 12, 3, False, WOOD, 0.3)
    p.rect(0, 2.0, 64, 3.0, BLACK if rival else RED, 150)
    p.rect(0, 5.0, 64, 0.9, GOLD_D if rival else WHITE, 158)
    p.stitch([(0, 9.6), (64, 9.6)], IRON_L, 0.26, 2.0)
    p.stains(0, 0, 64, 12, 12, 1.5, 0.84)
    p.shade_v(0, 0, 64, 12, 1.06, 0.82)
    p.wood(0, 12, 16, 16, 4, True, mul(WOOD, 1.1), 0.24)
    p.stains(0, 12, 16, 16, 4, 1.2, 0.86)
    _wheel(p, 16, 12, 16, 16)
    p.rect(32, 12, 8, 4, WOOD_D, 128)
    p.wood(40, 12, 8, 16, 2, True, mul(WOOD, 0.92), 0.16)
    p.shade_round(40, 12, 8, 16, 0.62)
    cloth = BLACK if rival else rgb("E4DCC8")
    p.rect(0, 32, 32, 28, cloth, 128)
    if rival:
        bone = rgb("ECE4D0")
        for sx in (-1.0, 1.0):
            p.line([(16 - sx * 6.0, 40.0), (16 + sx * 6.0, 54.0)], bone, 1.1, 150)
        p.ellipse(16, 45.0, 4.0, 4.6, bone, 156)
        p.rect(13.6, 48.2, 4.8, 3.4, bone, 156)
        for sx in (-1.0, 1.0):
            p.ellipse(16 + sx * 1.6, 45.0, 1.1, 1.3, BLACK, 100)
    else:
        for i in range(3):
            p.band(0, 36.0 + i * 8.0, 32, 2.6, NAVY, 124, 0.1)
    p.weave(0, 32, 32, 28, 0.36, 0.08)
    p.uneven(0, 32, 32, 28, 0.1, 2.6)
    for sx in (10.6, 21.3):
        p.fold([(sx, 32), (sx + 0.2, 60)], 0.3, 0.84, 30)
        p.stitch([(sx + 0.7, 32.4), (sx + 0.9, 59.6)], mul(cloth, 0.7) if not rival else rgb("5A5660"), 0.12, 0.6)
    p.wrinkles(0, 33, 32, 26, 9, 5.0, 0.6, 0.86, 30)
    p.stains(0, 34, 32, 24, 5, 1.8, 0.88)
    return p


def paint_bricks():
    """Каменная кладка (борта, обрывы): блоки со сдвигом, тёмные швы, мох. Стыкуется по краям."""
    p = Paint(327)
    stone = np.array(rgb("6E6A66"), dtype=np.float32)
    mid = p.tile_noise(16, 3)
    tones = p.rng.uniform(0.84, 1.14, (8, 4)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 8.0).astype(np.int32), 0, 7)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        ex = np.minimum(shifted % 16.0, 16.0 - shifted % 16.0)
        ey = np.minimum(gy % 8.0, 8.0 - gy % 8.0)
        seam = np.clip(np.minimum(ex, ey) / 0.45, 0.0, 1.0)
        tone = tones[row, col] * (1.0 + 0.09 * mid) * (0.42 + 0.58 * seam)
        return stone[None, None, :] * tone[..., None], 128.0 + mid * 16.0 - (1.0 - seam) * 80.0 + (tones[row, col] - 1.0) * 60.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 700, rgb("46423E"), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, rgb("96928A"), 0.07)
    for _ in range(10):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 2.5, y - 1.2, 5, 2.4, 46, rgb("5E8A3E"), 0.17)
    return p


def paint_cliff():
    """Скала обрыва (#121): слоистый природный камень с тёплым оттенком, трещины, редкий мох.
    Слои идут волной и стыкуются по краям."""
    p = Paint(331)
    stone = np.array(rgb("7C7264"), dtype=np.float32)
    warm = np.array(rgb("94826A"), dtype=np.float32)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(10, 3), p.tile_noise(28, 2)

    def fn(gx, gy):
        # Пласты: пять волнистых слоёв на высоту текстуры, у каждого тёмная кромка снизу.
        phase = gy / 64.0 * 5.0 + low * 0.55 + mid * 0.16
        band = phase - np.floor(phase)
        ledge = np.clip(band / 0.16, 0.0, 1.0) * np.clip((1.0 - band) / 0.5, 0.0, 1.0)
        layer = np.sin(np.floor(phase) * 2.4) * 0.5 + 0.5
        tone = (0.7 + 0.3 * ledge) * (1.0 + 0.12 * mid + 0.07 * fine)
        color = stone[None, None, :] * (1.0 - layer[..., None] * 0.55) + warm[None, None, :] * (layer[..., None] * 0.55)
        return color * tone[..., None], 128.0 + ledge * 62.0 - 40.0 + mid * 26.0 + fine * 12.0
    p.field(fn)
    p.wrinkles(1, 1, 62, 62, 14, 8.0, 1.2, 0.6, 70)
    p.speckle(0.5, 0.5, 63, 63, 700, rgb("4A433A"), 0.09)
    p.speckle(0.5, 0.5, 63, 63, 450, rgb("A89C88"), 0.08)
    for _ in range(7):
        x, y = p.rng.uniform(5, 59), p.rng.uniform(5, 59)
        p.speckle(x - 3.0, y - 1.0, 6, 2.0, 50, rgb("5E8A3E"), 0.16)
    return p


def _ground(seed, base, low_amp, mid_amp, relief):
    p = Paint(seed)
    color = np.array(base, dtype=np.float32)
    low, mid = p.tile_noise(4, 3), p.tile_noise(16, 3)

    def fn(gx, gy):
        tone = 1.0 + low_amp * low + mid_amp * mid
        return color[None, None, :] * tone[..., None], 128.0 + low * relief + mid * relief * 0.6
    p.field(fn)
    return p


def paint_grass():
    """Трава: пятна светлее и темнее, травинки, редкие цветы. Стыкуется по краям."""
    g, gd, gl = rgb("4E8A3C"), rgb("386C30"), rgb("86BC54")
    p = _ground(329, g, 0.12, 0.08, 20.0)
    for _ in range(1500):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.6, 63)
        lean = p.rng.uniform(-0.3, 0.3)
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.6, 1.3))], gd if p.rng.random() < 0.5 else gl, 0.12, 150)
    for _ in range(22):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.ellipse(x, y, 0.3, 0.3, rgb("F2E6A0") if p.rng.random() < 0.6 else rgb("E8E8F0"), 170)
    return p


def paint_road():
    """Укатанная дорога: две колеи вдоль, камешки, следы. Стыкуется по краям."""
    dirt = rgb("8E7250")
    p = _ground(331, dirt, 0.1, 0.07, 18.0)
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.2, 0.8, 60)
        p.line([(x + 1.6, 0), (x + 1.6, 64)], mul(dirt, 1.16), 0.5, 150)
    p.speckle(0.5, 0.5, 63, 63, 1500, mul(dirt, 0.78), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(dirt, 1.16), 0.07)
    for _ in range(30):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.3, 0.7)
        p.ellipse(x + 0.12, y + 0.16, r, r * 0.8, mul(dirt, 0.66), 110)
        p.ellipse(x, y, r, r * 0.8, rgb("9A948A"), 186)
    return p


def paint_mud():
    """Грязь: мокрая тёмная земля с лужами и комьями. Стыкуется по краям."""
    mud = rgb("4A3524")
    p = _ground(333, mud, 0.16, 0.12, 30.0)
    for _ in range(11):
        x, y = p.rng.uniform(8, 56), p.rng.uniform(8, 56)
        rx, ry = p.rng.uniform(2.5, 5.5), p.rng.uniform(1.4, 3.0)
        p.ellipse(x, y, rx, ry, mul(mud, 0.62), 70)
        p.ellipse(x - rx * 0.25, y - ry * 0.3, rx * 0.4, ry * 0.25, rgb("7A8894"), 74)
    p.speckle(0.5, 0.5, 63, 63, 900, mul(mud, 1.4), 0.1)
    p.speckle(0.5, 0.5, 63, 63, 700, mul(mud, 0.6), 0.1)
    return p


def paint_sail():
    """Парусина: полотнища со швами и строчкой, заплата. Стыкуется по краям."""
    cloth = rgb("D8D0B8")
    p = _ground(335, cloth, 0.06, 0.04, 10.0)
    p.weave(0, 0, 64, 64, 0.4, 0.07)
    for x in (0.4, 32.0):
        p.fold([(x, 0), (x, 64)], 0.5, 0.78, 44)
        p.stitch([(x + 1.2, 0.4), (x + 1.2, 63.6)], mul(cloth, 0.66), 0.14, 0.8)
    for y in (20.0, 42.0):
        p.fold([(0, y), (64, y)], 0.4, 0.86, 26)
    p.rect(10.0, 28.0, 8.0, 6.0, mul(cloth, 0.84), 150)
    p.stitch([(10.4, 28.4), (17.6, 28.4), (17.6, 33.6), (10.4, 33.6), (10.4, 28.4)], mul(cloth, 0.6), 0.14, 0.7)
    p.stains(2, 2, 60, 60, 9, 2.4, 0.9)
    return p


PROPS = {"pirates": {"tex_sand": paint_sand, "tex_planks": paint_planks, "tex_water": paint_water, "tex_rock": paint_bricks,
                     "tex_cliff": paint_cliff,
                     "tex_grass": paint_grass, "tex_road": paint_road, "tex_mud": paint_mud, "tex_sail": paint_sail,
                     "crate": paint_crate, "barrel": paint_barrel, "keg": paint_keg, "chest": paint_chest, "cannon": paint_cannon,
                     "palm": paint_palm, "rock": paint_rock, "flag": paint_flag, "lighthouse": paint_lighthouse,
                     "cart": lambda: paint_cart(False), "cart_rival": lambda: paint_cart(True)}}
SETS = {"pirates": [pirate_sailor, pirate_captain, pirate_skeleton]}


def main():
    only_list = "--list" in sys.argv
    preview = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
    for setting, makers in SETS.items():
        folder = os.path.join(ROOT, setting, "rig")
        for make in makers:
            rig, paint = make()
            color, normal = paint.finish()
            print("%-8s %-8s костей %d, вершин %d, треугольников %d, пружинных костей %d, текстура %d×%d" % (
                setting, rig.name, len(rig.bones), len(rig.verts), len(rig.tris), len(rig.springs), RES, RES))
            if preview:
                color.save(preview)
                normal.save(preview.replace(".png", "_n.png"))
            if not only_list:
                rig.write(folder, setting, color, normal)
        # Текстуры реквизита и уровня поверх увеличенных из `lowpoly_meshes.py`.
        for name, make in PROPS.get(setting, {}).items():
            color, normal = make().finish()
            print("%-8s %-10s текстура %d×%d поверх увеличенной" % (setting, name, RES, RES))
            if preview and name in preview:
                color.save(preview)
            if not only_list:
                out = os.path.join(ROOT, setting, "threed")
                (color.convert("RGB") if name.startswith("tex_") else color).save(os.path.join(out, name + ".png"))
                normal.save(os.path.join(out, name + "_n.png"))


if __name__ == "__main__":
    main()
