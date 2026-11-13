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

    def region(self, x, y, w, h):
        """Кусок в долях текстуры, чуть внутрь, чтобы фильтр не тянул соседей."""
        e = 0.12
        return ((x + e) / UNITS, (y + e) / UNITS, (x + w - e) / UNITS, (y + h - e) / UNITS)

    def finish(self):
        """Цвет и карта рельефа в `RES` пикселей."""
        color = self.im.resize((RES, RES), Image.LANCZOS)
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

    def spring(self, name, stiffness=60.0, damping=7.0, gravity=0.6):
        self.springs.append((name, stiffness, damping, gravity))

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

    def strip(self, points, width_dir, half, region, weight_fn, cloth_from=0.0):
        """Лента ткани вдоль `points` шириной `half`·2 поперёк `width_dir`, двусторонняя."""
        u0, v0, u1, v1 = region
        rows = []
        for i, p in enumerate(points):
            t = i / (len(points) - 1)
            row = []
            for side, u in ((-1.0, u0), (1.0, u1)):
                pos = tuple(p[j] + width_dir[j] * half * side * (1.0 - 0.35 * t) for j in range(3))
                row.append(self.vert(pos, (u, v0 + (v1 - v0) * t), weight_fn(t), cloth_from + (1.0 - cloth_from) * t))
            rows.append(row)
        for i in range(len(rows) - 1):
            a, b, c, d = rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]
            for out in ((0, 0, 1), (0, 0, -1)):
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
            "spring_params = PackedVector3Array(%s)" % flat([s[1:] for s in self.springs]),
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


def pirate_sailor():
    """Матрос: тельняшка, штаны клёш, сапоги, бандана с хвостами."""
    p = paint_sailor()
    torso, head = p.region(0, 0, 32, 22), p.region(32, 0, 32, 20)
    arm, leg = p.region(0, 22, 16, 26), p.region(16, 22, 20, 34)
    boot, sole, skin, tail = p.region(40, 24, 12, 6), p.region(54, 24, 6, 6), p.region(54, 32, 6, 6), p.region(40, 34, 12, 8)
    r = Rig("sailor")
    # Скелет: таз в корне, позвоночник, шея, голова; руки и ноги по три кости; хвост банданы.
    r.bone("hips", None, (0.0, 0.92, 0.0))
    r.bone("spine", "hips", (0.0, 1.06, 0.0))
    r.bone("chest", "spine", (0.0, 1.24, 0.0))
    r.bone("neck", "chest", (0.0, 1.46, 0.0))
    r.bone("head", "neck", (0.0, 1.53, 0.0))
    r.bone("tail", "head", (0.0, 1.665, 0.105))
    r.spring("tail", 45.0, 5.0, 1.2)
    for side, sx in (("l", -1.0), ("r", 1.0)):
        r.bone("arm_" + side, "chest", (sx * 0.215, 1.4, 0.0))
        r.bone("fore_" + side, "arm_" + side, (sx * 0.232, 1.12, 0.0))
        r.bone("hand_" + side, "fore_" + side, (sx * 0.24, 0.87, 0.0))
        r.bone("leg_" + side, "hips", (sx * 0.095, 0.9, 0.0))
        r.bone("shin_" + side, "leg_" + side, (sx * 0.095, 0.49, 0.0))
        r.bone("foot_" + side, "shin_" + side, (sx * 0.095, 0.08, 0.0))
    n = 16
    # Торс и голова одной трубой. В боках торса окна под рукава: кольца 8..11 (высота 1,25–1,415),
    # по две грани вокруг бока (точки 3..5 справа, 11..13 слева).
    body = lambda y: blend(y, [("hips", 0.0, 0.97), ("spine", 1.07, 1.14), ("chest", 1.26, 1.435), ("neck", 1.475, 1.495), ("head", 1.53, 9.0)])
    holes = {(i, k) for i in (8, 9, 10) for k in (3, 4, 11, 12)}
    rows = r.tube([(0.86, 0.15, 0.11, 0, 0), (0.9, 0.156, 0.116, 0, 0), (0.95, 0.152, 0.112, 0, 0), (1.0, 0.142, 0.103, 0, 0),
                   (1.06, 0.14, 0.1, 0, 0), (1.12, 0.148, 0.104, 0, 0), (1.17, 0.16, 0.11, 0, 0), (1.21, 0.172, 0.116, 0, 0),
                   (1.25, 0.18, 0.12, 0, 0), (1.31, 0.186, 0.12, 0, 0), (1.365, 0.184, 0.114, 0, 0), (1.415, 0.16, 0.1, 0, 0),
                   (1.445, 0.1, 0.08, 0, 0), (1.47, 0.058, 0.06, 0, 0)], n, torso, body, cap_bottom=sole, skip=holes)
    r.tube([(1.47, 0.056, 0.06, 0, 0), (1.5, 0.054, 0.058, 0, -0.002), (1.525, 0.07, 0.076, 0, -0.004),
            (1.555, 0.09, 0.098, 0, -0.006), (1.59, 0.101, 0.112, 0, -0.006), (1.63, 0.106, 0.117, 0, -0.005),
            (1.67, 0.106, 0.116, 0, -0.004), (1.705, 0.098, 0.108, 0, -0.003), (1.735, 0.078, 0.088, 0, -0.002),
            (1.755, 0.045, 0.052, 0, 0.0)], n, head, body, cap_top=p.region(46, 1, 4, 3), v_range=(1.47, 1.76))
    # Хвосты банданы: две ленты из узла на затылке, ткань с пружинной костью.
    for dx, lean in ((-0.025, -0.05), (0.03, 0.06)):
        pts = [(dx, 1.665 - 0.055 * i, 0.108 + 0.022 * i + abs(lean) * 0.1 * i) for i in range(6)]
        pts = [(x + lean * i * 0.2, y, z) for i, (x, y, z) in enumerate(pts)]
        r.strip(pts, (1.0, 0.0, 0.0), 0.028, tail, lambda t: [("head", 1.0 - t), ("tail", t)] if t < 1.0 else [("tail", 1.0)], 0.2)
    for side, sx in (("l", -1.0), ("r", 1.0)):
        s = side
        # Рука вращена в торс: рукав начинается с края окна в боку, плечо, локоть, запястье, кисть.
        x = sx * 0.228

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
        r.sleeve(rows, 8, 11, k0, k0 + 2, sx,
                 [((sx * 0.202, 1.352, 0.0), 28.0, 0.074, 0.076), ((sx * 0.224, 1.318, 0.0), 62.0, 0.068, 0.07)],
                 [(1.27, 0.06, 0.064, x, 0), (1.21, 0.055, 0.059, x * 1.01, 0), (1.165, 0.05, 0.054, x * 1.015, 0),
                  (1.13, 0.047, 0.051, x * 1.02, 0), (1.1, 0.046, 0.05, x * 1.022, 0), (1.06, 0.045, 0.048, x * 1.026, 0),
                  (1.0, 0.042, 0.045, x * 1.033, 0), (0.93, 0.037, 0.04, x * 1.042, 0), (0.875, 0.031, 0.034, x * 1.05, 0),
                  (0.85, 0.03, 0.04, x * 1.054, 0), (0.81, 0.033, 0.05, x * 1.058, 0), (0.77, 0.031, 0.047, x * 1.062, 0),
                  (0.745, 0.024, 0.034, x * 1.064, 0)], arm, aw, cap=skin)
        # Нога: штаны клёш, низ штанины колышется.
        x = sx * 0.095
        lw = lambda y, s=s: blend(y, [("foot_" + s, 0.0, 0.07), ("shin_" + s, 0.11, 0.43), ("leg_" + s, 0.55, 0.86), ("hips", 0.96, 9.0)])
        hem = lambda y: max(0.0, min(1.0, (0.36 - y) / 0.26)) * 0.55
        r.tube([(0.07, 0.094, 0.1, x, 0.004), (0.1, 0.092, 0.098, x, 0.004), (0.16, 0.084, 0.09, x, 0.003),
                (0.24, 0.076, 0.082, x, 0.002), (0.32, 0.071, 0.077, x, 0.001), (0.4, 0.068, 0.074, x, 0),
                (0.45, 0.067, 0.073, x, 0), (0.49, 0.068, 0.075, x, -0.002), (0.53, 0.07, 0.077, x, -0.002),
                (0.6, 0.076, 0.082, x, 0), (0.7, 0.085, 0.091, x, 0), (0.8, 0.093, 0.099, x, 0), (0.88, 0.097, 0.103, x * 0.98, 0),
                (0.95, 0.09, 0.098, x * 0.9, 0)], 12, leg, lw, hem, cap_bottom=sole, v_range=(0.07, 0.95))
        # Сапог: носок вперёд (−Z).
        fw = lambda y, s=s: [("foot_" + s, 1.0)]
        r.tube([(0.0, 0.05, 0.115, x, -0.045), (0.035, 0.054, 0.12, x, -0.047), (0.07, 0.052, 0.1, x, -0.03),
                (0.105, 0.05, 0.062, x, -0.004), (0.14, 0.048, 0.055, x, 0.0)], 10, boot, fw, cap_bottom=sole, cap_top=sole)
    return r, p


SETS = {"pirates": [pirate_sailor]}


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


if __name__ == "__main__":
    main()
