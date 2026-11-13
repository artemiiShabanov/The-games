#!/usr/bin/env python3
"""Генератор мешей и текстур low poly (#108, полный набор пиратов в #110).

Стиль эпохи первой PlayStation (решение 2026-11-12): не фигурки из ящиков, а малополигональные
модели с настоящими пропорциями и текстуры низкого разрешения, в которые втиснуто как можно
больше деталей (лицо, складки, доски, заклёпки) с запечённой светотенью. Тело собирается лофтом:
кольца из нескольких точек вдоль оси с разными радиусами, развёртка цилиндром в свой кусок
атласа модели. Атлас 64×64 рисуется здесь же по пикселям.

Пишет в `thegames/assets/settings/<сеттинг>/lowpoly/`:
  <имя>.tres  ресурс `LowpolyModelDef`: части с точками вращения, вершины, нормали, развёртка;
  <имя>.png   атлас модели;
  tex_<имя>.png  текстуры уровня (песок, доски, вода, скала, парус, небо), плиткой.

Единицы метры, Y вверх, модель смотрит в −Z (вперёд у Godot), ноль в подошвах. Треугольники
против часовой стрелки наружу; порядок вершин под Godot меняет загрузчик. Предел: 300
треугольников на объект. После записи: `Godot --headless --path thegames --import`.

  python3 tools/lowpoly_meshes.py            # записать всё
  python3 tools/lowpoly_meshes.py --list     # только таблица: модель, части, треугольники
"""
import math
import os
import random
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames", "assets", "settings")
MAX_TRIS = 300
## Набор «продвинутых» (threed, #118): те же описания моделей, но тела вращения вдвое плотнее по
## окружности и по высоте (кольца сглажены), атласы вчетверо крупнее и сглажены.
MAX_TRIS_DENSE = 1500
DENSE = 1
TEX_SCALE = 1
FOLDER = "lowpoly"


# --- Рисование атласа ---------------------------------------------------------------------------

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mul(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3])


class Atlas:
    """Картинка модели и её куски: кусок это прямоугольник в пикселях, развёртка берёт его в долях."""

    def __init__(self, w=64, h=64, seed=1):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.rng = random.Random(seed)

    def px(self, x, y, c, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im.putpixel((x, y), tuple(c[:3]) + (a,))

    def get(self, x, y):
        return self.im.getpixel((x, y))

    def rect(self, x, y, w, h, c, a=255):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.px(i, j, c, a)

    def clear(self, x, y, w=1, h=1):
        for j in range(y, y + h):
            for i in range(x, x + w):
                if 0 <= i < self.w and 0 <= j < self.h:
                    self.im.putpixel((i, j), (0, 0, 0, 0))

    def noise(self, x, y, w, h, amount=0.08):
        """Зерно: яркость каждого пикселя гуляет на ±amount."""
        for j in range(y, y + h):
            for i in range(x, x + w):
                c = self.get(i, j)
                if c[3] > 0:
                    self.px(i, j, mul(c, 1.0 + self.rng.uniform(-amount, amount)), c[3])

    def shade(self, x, y, w, h, top=1.0, bottom=1.0, sides=1.0):
        """Запечённая светотень: сверху вниз от `top` до `bottom`, к левому и правому краю `sides`."""
        for j in range(y, y + h):
            kv = top + (bottom - top) * ((j - y) / max(h - 1, 1))
            for i in range(x, x + w):
                edge = abs((i - x) / max(w - 1, 1) - 0.5) * 2.0
                c = self.get(i, j)
                if c[3] > 0:
                    self.px(i, j, mul(c, kv * (1.0 + (sides - 1.0) * edge * edge)), c[3])

    def region(self, x, y, w, h):
        """Кусок атласа в долях, на четверть пикселя внутрь, чтобы не тянуло соседей."""
        e = 0.25
        return ((x + e) / self.w, (y + e) / self.h, (x + w - e) / self.w, (y + h - e) / self.h)

    def save(self, path):
        if TEX_SCALE <= 1:
            self.im.save(path)
            return
        # Крупная текстура для «продвинутых»: гладкое увеличение (по цвету с учётом прозрачности,
        # чтобы вырезанные пиксели не давали тёмной каймы) и лёгкое зерно.
        from PIL import Image
        big = self.im.convert("RGBa").resize((self.w * TEX_SCALE, self.h * TEX_SCALE), Image.BICUBIC).convert("RGBA")
        grain = random.Random(self.w * 131 + self.h)
        px = big.load()
        for y in range(big.height):
            for x in range(big.width):
                r, g, b, a = px[x, y]
                k = 1.0 + grain.uniform(-0.035, 0.035)
                px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), 255 if a >= 128 else 0)
        big.save(path)


# --- Геометрия ----------------------------------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    d = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    return (a[0] / d, a[1] / d, a[2] / d) if d > 1e-9 else (0.0, 1.0, 0.0)


def _tri(vs, uvs, ns=None):
    """Треугольник: вершины, развёртка, нормали (без них плоская нормаль грани)."""
    if ns is None:
        n = _norm(_cross(_sub(vs[1], vs[0]), _sub(vs[2], vs[0])))
        ns = [n, n, n]
    return (list(vs), list(uvs), list(ns))


def loft(rings, region, n=6, phase=0.0, caps=(None, None), flat=False):
    """Тело вращения: кольца снизу вверх `(y, rx, rz[, cx, cz])`, по `n` точек в кольце.

    Развёртка цилиндром в `region`: по горизонтали вокруг тела (середина куска это перёд, −Z, шов
    сзади), по вертикали вдоль колец сверху вниз. `caps`: куски для нижней и верхней крышки
    (плоская проекция сверху) или None. `flat` даёт гранёные нормали вместо округлых.
    """
    u0, v0, u1, v1 = region
    full = []
    for r in rings:
        full.append((r[0], r[1], r[2], r[3] if len(r) > 3 else 0.0, r[4] if len(r) > 4 else 0.0))
    if DENSE > 1 and not flat:
        # Плотный набор: вдвое больше точек в кольце, между кольцами вставлено сглаженное.
        n *= DENSE
        if len(full) >= 3:
            smooth = []
            for i in range(len(full) - 1):
                p0, p1, p2, p3 = full[max(i - 1, 0)], full[i], full[i + 1], full[min(i + 2, len(full) - 1)]
                mid = tuple(0.5 * (p1[j] + p2[j]) + 0.0625 * (p1[j] + p2[j] - p0[j] - p3[j]) for j in range(5))
                smooth += [p1, (0.5 * (p1[0] + p2[0]), max(mid[1], 0.0), max(mid[2], 0.0), mid[3], mid[4])]
            full = smooth + [full[-1]]
    tris = []

    def point(ring, k):
        y, rx, rz, cx, cz = ring
        a = phase + 2.0 * math.pi * k / n
        return (cx + rx * math.sin(a), y, cz + rz * math.cos(a))

    def normal(ring, k):
        _, rx, rz, _, _ = ring
        a = phase + 2.0 * math.pi * k / n
        return _norm((math.sin(a) * max(rz, 1e-4), 0.0, math.cos(a) * max(rx, 1e-4)))

    last = len(full) - 1
    for i in range(last):
        lo, hi = full[i], full[i + 1]
        vlo = v1 - (v1 - v0) * i / last
        vhi = v1 - (v1 - v0) * (i + 1) / last
        for k in range(n):
            ua = u0 + (u1 - u0) * k / n
            ub = u0 + (u1 - u0) * (k + 1) / n
            a, b, c, d = point(lo, k), point(lo, k + 1), point(hi, k + 1), point(hi, k)
            na, nb, nc, nd = normal(lo, k), normal(lo, k + 1), normal(hi, k + 1), normal(hi, k)
            if lo[1] > 0.0 or lo[2] > 0.0 or True:
                if _sub(b, a) != (0.0, 0.0, 0.0):
                    tris.append(_tri([a, b, c], [(ua, vlo), (ub, vlo), (ub, vhi)], None if flat else [na, nb, nc]))
                if _sub(c, d) != (0.0, 0.0, 0.0):
                    tris.append(_tri([a, c, d], [(ua, vlo), (ub, vhi), (ua, vhi)], None if flat else [na, nc, nd]))
    for which, ring in ((0, full[0]), (1, full[last])):
        cap = caps[which]
        if cap is None or ring[1] <= 0.0 or ring[2] <= 0.0:
            continue
        c0, d0, c1, d1 = cap
        pts = [point(ring, k) for k in range(n)]
        ext_x = max(abs(p[0] - ring[3]) for p in pts) or 1.0
        ext_z = max(abs(p[2] - ring[4]) for p in pts) or 1.0
        uv = lambda p: (c0 + (c1 - c0) * (0.5 + (p[0] - ring[3]) / (2.0 * ext_x)),
                        d0 + (d1 - d0) * (0.5 + (p[2] - ring[4]) / (2.0 * ext_z)))
        up = (0.0, 1.0, 0.0) if which == 1 else (0.0, -1.0, 0.0)
        for k in range(1, n - 1):
            a, b, c = pts[0], pts[k], pts[k + 1]
            if which == 0:
                b, c = c, b
            tris.append(_tri([a, b, c], [uv(a), uv(b), uv(c)], [up, up, up]))
    return tris


def box(size, side, top=None, bottom=None, taper=(1.0, 1.0)):
    """Ящик с центром в нуле: бока развёрнуты лентой в `side`, крышки в `top` и `bottom`."""
    hx, hy, hz = size[0] / 2.0 * math.sqrt(2.0), size[1] / 2.0, size[2] / 2.0 * math.sqrt(2.0)
    return loft([(-hy, hx, hz), (hy, hx * taper[0], hz * taper[1])], side, 4, math.pi / 4.0, (bottom, top), True)


def quad(tl, tr, br, bl, region, double=True):
    """Плоскость по четырём углам (вид с лица); `double` рисует и изнанку."""
    u0, v0, u1, v1 = region
    tris = [_tri([tl, bl, br], [(u0, v0), (u0, v1), (u1, v1)]), _tri([tl, br, tr], [(u0, v0), (u1, v1), (u1, v0)])]
    if double:
        tris += [_tri([tl, br, bl], [(u0, v0), (u1, v1), (u0, v1)]), _tri([tl, tr, br], [(u0, v0), (u1, v0), (u1, v1)])]
    return tris


def flip(tris):
    """Изнанка: тот же набор граней лицом внутрь (сетка кольца, внутренность трубы)."""
    return [([vs[0], vs[2], vs[1]], [uvs[0], uvs[2], uvs[1]], [tuple(-c for c in n) for n in (ns[0], ns[2], ns[1])])
            for vs, uvs, ns in tris]


def rot(tris, rx=0.0, ry=0.0, rz=0.0):
    """Поворот в градусах вокруг X, потом Y, потом Z."""
    def turn(v):
        x, y, z = v
        a = math.radians(rx)
        y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
        a = math.radians(ry)
        x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
        a = math.radians(rz)
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        return (x, y, z)
    return [([turn(v) for v in vs], uvs, [turn(n) for n in ns]) for vs, uvs, ns in tris]


def at(tris, x=0.0, y=0.0, z=0.0):
    return [([(v[0] + x, v[1] + y, v[2] + z) for v in vs], uvs, ns) for vs, uvs, ns in tris]


class Model:
    """Части модели (имя, родитель, точка вращения, треугольники в координатах модели) и её атлас."""

    def __init__(self, name, atlas):
        self.name = name
        self.atlas = atlas
        self.parts = []

    def part(self, name, pivot, tris, parent=None):
        self.parts.append((name, parent, pivot, tris))
        return self

    def tris(self):
        return sum(len(p[3]) for p in self.parts)

    def write(self, folder, setting):
        names = [p[0] for p in self.parts]
        pivots = {p[0]: p[2] for p in self.parts}
        parents, local, counts, verts, normals, uvs = [], [], [], [], [], []
        for name, parent, pivot, tris in self.parts:
            parents.append(names.index(parent) if parent else -1)
            local.extend(_sub(pivot, pivots[parent] if parent else (0.0, 0.0, 0.0)))
            counts.append(len(tris))
            for vs, ts, ns in tris:
                for v, t, n in zip(vs, ts, ns):
                    verts.extend(_sub(v, pivot))
                    normals.extend(n)
                    uvs.extend(t)
        num = lambda x: ("%.4f" % x).rstrip("0").rstrip(".") if abs(x) > 5e-5 else "0"
        lines = [
            '[gd_resource type="Resource" script_class="LowpolyModelDef" load_steps=3 format=3]',
            "",
            '[ext_resource type="Script" path="res://scripts/demos/lowpoly_model_def.gd" id="1_def"]',
            '[ext_resource type="Texture2D" path="res://assets/settings/%s/%s/%s.png" id="2_tex"]' % (setting, FOLDER, self.name),
            "",
            "[resource]",
            'script = ExtResource("1_def")',
            'texture = ExtResource("2_tex")',
            "part_names = PackedStringArray(%s)" % ", ".join('"%s"' % n for n in names),
            "part_parents = PackedInt32Array(%s)" % ", ".join(str(p) for p in parents),
            "part_pivots = PackedVector3Array(%s)" % ", ".join(num(x) for x in local),
            "part_tris = PackedInt32Array(%s)" % ", ".join(str(c) for c in counts),
            "vertices = PackedVector3Array(%s)" % ", ".join(num(x) for x in verts),
            "normals = PackedVector3Array(%s)" % ", ".join(num(x) for x in normals),
            "uvs = PackedVector2Array(%s)" % ", ".join(num(x) for x in uvs),
            "",
        ]
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, self.name + ".tres"), "w") as f:
            f.write("\n".join(lines))
        self.atlas.save(os.path.join(folder, self.name + ".png"))


# --- Пираты: цвета ------------------------------------------------------------------------------

SKIN, SKIN_D = rgb("D9A27C"), rgb("A8704F")
HAIR = rgb("3A2A20")
WHITE, NAVY = rgb("E6E0D0"), rgb("2B4470")
RED, RED_D = rgb("B5362E"), rgb("7C2320")
PANTS, PANTS_D = rgb("3C5C8C"), rgb("2A4268")
BOOT, BOOT_L = rgb("2E241E"), rgb("5A4636")
BELT, GOLD, GOLD_D = rgb("4A3222"), rgb("E0B040"), rgb("9A7020")
BONE, BONE_D = rgb("D8D2BC"), rgb("8E8872")
BLACK = rgb("1C1A20")
WOOD, WOOD_D, WOOD_L = rgb("7A5230"), rgb("4E3420"), rgb("9A6E42")
IRON, IRON_L = rgb("3A3C44"), rgb("6C707C")
STONE, STONE_D, STONE_L = rgb("6E6A66"), rgb("46423E"), rgb("96928A")
SAND, SAND_D, SAND_L = rgb("D8BC82"), rgb("B89860"), rgb("ECD6A0")


def stripes(a, x, y, w, h, c0, c1, step=2):
    for j in range(h):
        a.rect(x, y + j, w, 1, c0 if (j // step) % 2 == 0 else c1)


def planks(a, x, y, w, h, vertical=True, width=6):
    """Доски: щели, сучки, светлые волокна."""
    a.rect(x, y, w, h, WOOD)
    span = w if vertical else h
    for k in range(0, span, width):
        tone = a.rng.uniform(0.85, 1.12)
        for j in range(h):
            for i in range(w):
                pos = i if vertical else j
                if k <= pos < k + width:
                    c = mul(WOOD, tone * (1.0 + 0.06 * math.sin((j if vertical else i) * 1.7 + k)))
                    a.px(x + i, y + j, WOOD_D if pos == k else c)
    for _ in range(max(1, w * h // 90)):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), WOOD_D)
    a.noise(x, y, w, h, 0.07)


def biped(leg, torso, head, arm, sole, crown, bulk=1.0):
    """Части человека ростом 1,74 м: куски атласа для ноги, торса, головы и руки, подошвы и макушки.

    `bulk` ширина плеч, груди и конечностей. Возвращает словарь: часть → [точка вращения,
    треугольники, родитель]; модель потом дописывает к частям своё (шляпу, узел банданы).
    """
    k = bulk
    parts = {}

    def cut(region, top, bottom):
        """Полоса куска атласа по высоте: доли от верха."""
        u0, v0, u1, v1 = region
        return (u0, v0 + (v1 - v0) * top, u1, v0 + (v1 - v0) * bottom)

    # Нога из бедра и голени с коленом на 0,47 м, рука из плеча и предплечья с локтем на 1,1 м:
    # половины чуть заходят друг в друга и закрыты крышками, чтобы сгиб не открывал дыру.
    for side, x in (("l", -0.1 * k), ("r", 0.1 * k)):
        parts["leg_" + side] = [(x, 0.86, 0.0),
                                loft([(0.44, 0.072 * k, 0.078 * k, x, 0.0), (0.88, 0.1 * k, 0.105 * k, x, 0.0)],
                                     cut(leg, 0.0, 0.5), 5, caps=(cut(leg, 0.4, 0.5), None)), None]
        parts["shin_" + side] = [(x, 0.47, 0.0),
                                 loft([(0.0, 0.07 * k, 0.13, x, -0.04), (0.1, 0.065 * k, 0.085, x, -0.01),
                                       (0.5, 0.075 * k, 0.08 * k, x, 0.0)],
                                      cut(leg, 0.43, 1.0), 5, caps=(sole, cut(leg, 0.4, 0.5))), "leg_" + side]
    parts["body"] = [(0.0, 0.86, 0.0),
                     loft([(0.82, 0.17 * k, 0.115 * k), (1.02, 0.155 * k, 0.1 * k), (1.27, 0.2 * k, 0.125 * k),
                           (1.42, 0.17 * k, 0.105 * k), (1.47, 0.06, 0.06)], torso, 6), None]
    parts["head"] = [(0.0, 1.46, 0.0),
                     loft([(1.44, 0.055, 0.06), (1.52, 0.09, 0.1, 0.0, -0.005), (1.64, 0.105, 0.115), (1.74, 0.07, 0.08)],
                          head, 6, caps=(None, crown)), "body"]
    for side, x in (("l", -0.25 * k), ("r", 0.25 * k)):
        parts["arm_" + side] = [(x, 1.38, 0.0),
                                loft([(1.07, 0.046 * k, 0.05 * k, x * 1.06, 0.0), (1.4, 0.06 * k, 0.065 * k, x, 0.0)],
                                     cut(arm, 0.0, 0.53), 4, math.pi / 4.0, caps=(cut(arm, 0.45, 0.53), None)), "body"]
        parts["fore_" + side] = [(x * 1.06, 1.1, 0.0),
                                 loft([(0.78, 0.035 * k, 0.045, x * 1.08, 0.0), (1.13, 0.045 * k, 0.05 * k, x * 1.06, 0.0)],
                                      cut(arm, 0.47, 1.0), 4, math.pi / 4.0, caps=(sole, cut(arm, 0.45, 0.53))), "arm_" + side]
    return parts


def assemble(name, atlas, parts):
    m = Model(name, atlas)
    for key in ("leg_l", "leg_r", "body", "head", "arm_l", "arm_r", "shin_l", "shin_r", "fore_l", "fore_r"):
        pivot, tris, parent = parts[key]
        m.part(key, pivot, tris, parent)
    return m


# --- Пираты: модели -----------------------------------------------------------------------------

def pirate_hero():
    """Матрос: тельняшка, синие штаны, сапоги, красная бандана, щетина."""
    a = Atlas(64, 64, 11)
    # Торс 32×20: ворот, полосы тельняшки, ремень с пряжкой спереди (середина куска).
    stripes(a, 0, 0, 32, 17, WHITE, NAVY)
    a.rect(13, 0, 6, 2, SKIN)
    a.rect(14, 2, 4, 1, SKIN_D)
    a.rect(0, 17, 32, 3, BELT)
    a.rect(15, 17, 2, 3, GOLD)
    a.px(15, 18, GOLD_D)
    a.shade(0, 0, 32, 20, 1.08, 0.86, 0.72)
    a.noise(0, 0, 32, 20, 0.06)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×16: бандана, волосы сзади и на висках, лицо в середине.
    a.rect(0, 20, 32, 16, SKIN)
    a.rect(0, 20, 32, 5, RED)
    a.rect(0, 24, 32, 1, RED_D)
    for x in (5, 12, 19, 26):
        a.px(x, 22, RED_D)
    a.rect(0, 21, 3, 3, RED_D)
    a.rect(29, 21, 3, 3, RED_D)
    a.rect(0, 25, 8, 7, HAIR)
    a.rect(24, 25, 8, 7, HAIR)
    a.rect(8, 27, 1, 3, SKIN_D)
    a.rect(23, 27, 1, 3, SKIN_D)
    a.rect(11, 27, 3, 1, HAIR)
    a.rect(18, 27, 3, 1, HAIR)
    a.px(12, 28, WHITE), a.px(13, 28, BLACK), a.px(18, 28, BLACK), a.px(19, 28, WHITE)
    a.rect(15, 28, 2, 2, mul(SKIN, 0.9))
    a.px(16, 30, SKIN_D)
    a.rect(13, 32, 6, 1, RED_D)
    for _ in range(26):
        a.px(a.rng.randrange(10, 22), a.rng.randrange(31, 35), mul(SKIN, 0.72))
    a.rect(0, 34, 32, 2, SKIN_D)
    a.shade(0, 20, 32, 16, 1.06, 0.92, 0.8)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16: рукав тельняшки до локтя, предплечье, кисть.
    stripes(a, 32, 0, 16, 8, WHITE, NAVY)
    a.rect(32, 8, 16, 8, SKIN)
    a.rect(32, 13, 16, 1, SKIN_D)
    for x in (35, 39, 43):
        a.px(x, 15, SKIN_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.06)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: штаны со складками, сапог с отворотом.
    a.rect(48, 0, 16, 18, PANTS)
    a.rect(55, 0, 1, 18, PANTS_D)
    for y in (4, 9, 13):
        a.rect(50 + (y % 3), y, 4, 1, PANTS_D)
    a.rect(48, 18, 16, 6, BOOT)
    a.rect(48, 18, 16, 1, BOOT_L)
    a.rect(54, 21, 4, 1, BOOT_L)
    a.shade(48, 0, 16, 24, 1.05, 0.85, 0.75)
    a.noise(48, 0, 16, 24, 0.07)
    leg = a.region(48, 0, 16, 24)
    a.rect(32, 16, 4, 4, RED)
    a.rect(36, 16, 4, 4, BOOT)
    red_chip, boot_chip = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4)

    parts = biped(leg, torso, head, arm, boot_chip, red_chip)
    parts["head"][1].extend(at(box((0.07, 0.06, 0.1), red_chip, red_chip, red_chip), 0.04, 1.63, 0.14))
    return assemble("hero", a, parts)


def pirate_enemy():
    """Скелет в треуголке с саблей: рёбра вырезаны прозрачными пикселями, в черепе глазницы и зубы."""
    a = Atlas(64, 64, 23)
    # Грудная клетка 32×20: рёбра полосами, между ними пусто; грудина спереди, хребет сзади.
    a.rect(0, 0, 32, 20, BONE)
    for y in (3, 4, 7, 8, 11, 12):
        a.clear(1, y, 14, 1)
        a.clear(17, y, 14, 1)
    for y in (14, 15, 16):
        a.clear(2, y, 12, 1)
        a.clear(18, y, 12, 1)
    a.rect(0, 17, 32, 3, BONE_D)
    a.shade(0, 0, 32, 20, 1.05, 0.85, 0.75)
    a.noise(0, 0, 32, 20, 0.07)
    ribs = a.region(0, 0, 32, 20)
    # Череп 32×16: глазницы, нос, зубы, трещина.
    a.rect(0, 20, 32, 16, BONE)
    a.rect(10, 25, 4, 4, BLACK)
    a.rect(18, 25, 4, 4, BLACK)
    a.px(11, 26, RED), a.px(20, 26, RED)
    a.rect(15, 29, 2, 2, BLACK)
    for x in range(10, 22):
        a.px(x, 32, BLACK if x % 2 == 0 else BONE)
        a.px(x, 33, BONE_D if x % 2 == 0 else BONE)
    a.rect(0, 34, 32, 2, BONE_D)
    for x, y in ((24, 22), (25, 23), (25, 24), (26, 25)):
        a.px(x, y, BONE_D)
    a.shade(0, 20, 32, 16, 1.05, 0.88, 0.78)
    a.noise(0, 20, 32, 16, 0.06)
    skull = a.region(0, 20, 32, 16)
    # Кость 16×16 с суставами и треуголка 16×8 с золотым кантом.
    a.rect(32, 0, 16, 16, BONE)
    a.rect(32, 7, 16, 2, BONE_D)
    a.rect(32, 0, 16, 1, BONE_D)
    a.rect(32, 15, 16, 1, BONE_D)
    a.shade(32, 0, 16, 16, 1.0, 0.9, 0.7)
    a.noise(32, 0, 16, 16, 0.07)
    bone = a.region(32, 0, 16, 16)
    a.rect(48, 0, 16, 8, BLACK)
    a.rect(48, 6, 16, 2, GOLD)
    a.rect(55, 1, 2, 3, BONE)
    a.noise(48, 0, 16, 8, 0.1)
    hat = a.region(48, 0, 16, 8)
    a.rect(48, 8, 8, 8, BLACK)
    a.rect(48, 8, 8, 1, GOLD)
    a.rect(48, 15, 8, 1, GOLD)
    a.rect(48, 8, 1, 8, GOLD)
    a.rect(55, 8, 1, 8, GOLD)
    brim = a.region(48, 8, 8, 8)
    # Сабля 16×4: клинок с бликом и золотая гарда.
    a.rect(32, 16, 16, 4, IRON_L)
    a.rect(32, 16, 16, 1, WHITE)
    a.rect(32, 19, 16, 1, IRON)
    a.rect(32, 16, 3, 4, GOLD)
    blade = a.region(32, 16, 16, 4)
    a.rect(56, 8, 4, 4, BONE_D)
    chip = a.region(56, 8, 4, 4)

    m = Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               loft([(0.0, 0.05, 0.11, x, -0.04), (0.06, 0.03, 0.035, x, 0.0), (0.46, 0.04, 0.04, x, 0.0),
                     (0.88, 0.035, 0.035, x, 0.0)], bone, 4, math.pi / 4.0, caps=(chip, None)))
    m.part("body", (0.0, 0.86, 0.0),
           loft([(0.84, 0.13, 0.08), (0.94, 0.05, 0.05), (1.06, 0.15, 0.1), (1.36, 0.17, 0.11), (1.46, 0.04, 0.04)],
                ribs, 6))
    m.part("head", (0.0, 1.46, 0.0),
           loft([(1.45, 0.05, 0.055), (1.52, 0.085, 0.095), (1.64, 0.105, 0.115), (1.73, 0.07, 0.08)], skull, 6,
                caps=(None, chip))
           + loft([(1.7, 0.24, 0.22), (1.72, 0.24, 0.22)], hat, 3, math.pi, caps=(brim, brim), flat=True)
           + loft([(1.72, 0.11, 0.11), (1.82, 0.08, 0.08)], hat, 5, caps=(None, brim)), "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           loft([(0.76, 0.03, 0.03, -0.22, 0.0), (1.08, 0.035, 0.035, -0.215, 0.0), (1.4, 0.03, 0.03, -0.2, 0.0)],
                bone, 4, math.pi / 4.0, caps=(chip, None)), "body")
    m.part("arm_r", (0.2, 1.38, 0.0),
           loft([(0.76, 0.03, 0.03, 0.22, 0.0), (1.08, 0.035, 0.035, 0.215, 0.0), (1.4, 0.03, 0.03, 0.2, 0.0)],
                bone, 4, math.pi / 4.0, caps=(chip, None))
           + quad((0.22, 0.83, -0.02), (0.22, 0.83, -0.72), (0.22, 0.75, -0.72), (0.22, 0.75, -0.02), blade), "body")
    return m


def pirate_coin():
    """Дублон: восьмигранный диск на ребре с черепом на аверсе."""
    a = Atlas(32, 32, 5)
    a.rect(0, 0, 16, 16, GOLD)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            if d > 6.2:
                a.px(i, j, GOLD_D)
            elif d > 5.0:
                a.px(i, j, mul(GOLD, 1.15))
    a.rect(6, 5, 4, 4, GOLD_D)
    a.px(7, 6, GOLD), a.px(8, 6, GOLD)
    a.rect(7, 9, 2, 2, GOLD_D)
    a.px(4, 4, WHITE), a.px(5, 3, WHITE)
    a.noise(0, 0, 16, 16, 0.06)
    face = a.region(0, 0, 16, 16)
    stripes(a, 16, 0, 16, 4, GOLD_D, GOLD, 1)
    edge = a.region(16, 0, 16, 4)
    m = Model("coin", a)
    return m.part("body", (0.0, 0.35, 0.0),
                  at(rot(loft([(-0.035, 0.28, 0.28), (0.035, 0.28, 0.28)], edge, 8, math.pi / 8.0, caps=(face, face), flat=True),
                         rx=90.0), 0.0, 0.35))


def pirate_rock():
    a = Atlas(32, 32, 7)
    a.rect(0, 0, 32, 32, STONE)
    for _ in range(40):
        x, y = a.rng.randrange(32), a.rng.randrange(32)
        a.rect(x, y, a.rng.randrange(1, 4), 1, STONE_D if a.rng.random() < 0.6 else STONE_L)
    for x, y in ((6, 4), (7, 5), (8, 7), (8, 8), (20, 14), (21, 15), (22, 17), (12, 22), (13, 23)):
        a.px(x, y, BLACK)
    a.shade(0, 0, 32, 32, 1.15, 0.75, 0.9)
    a.noise(0, 0, 32, 32, 0.1)
    stone = a.region(0, 0, 32, 32)
    m = Model("rock", a)
    return m.part("body", (0.0, 0.0, 0.0),
                  loft([(0.0, 0.55, 0.5), (0.3, 0.5, 0.42, 0.05, 0.02), (0.58, 0.3, 0.26, -0.06, 0.04), (0.72, 0.1, 0.08, -0.08, 0.02)],
                       stone, 6, 0.3, caps=(None, stone), flat=True)
                  + at(loft([(0.0, 0.3, 0.28), (0.22, 0.24, 0.2), (0.36, 0.08, 0.07)], stone, 5, 1.1, caps=(None, stone), flat=True),
                       0.5, 0.0, 0.3))


def pirate_barrel():
    a = Atlas(32, 32, 9)
    planks(a, 0, 0, 32, 24, True, 4)
    for y in (3, 4, 19, 20):
        a.rect(0, y, 32, 1, IRON if y in (4, 20) else IRON_L)
    for x in range(2, 32, 8):
        a.px(x, 3, WHITE), a.px(x, 19, WHITE)
    a.shade(0, 0, 32, 24, 1.1, 0.8, 0.85)
    side = a.region(0, 0, 32, 24)
    planks(a, 0, 24, 8, 8, False, 3)
    a.rect(0, 24, 8, 1, WOOD_D), a.rect(0, 31, 8, 1, WOOD_D), a.rect(0, 24, 1, 8, WOOD_D), a.rect(7, 24, 1, 8, WOOD_D)
    lid = a.region(0, 24, 8, 8)
    m = Model("barrel", a)
    return m.part("body", (0.0, 0.0, 0.0),
                  loft([(0.0, 0.3, 0.3), (0.26, 0.37, 0.37), (0.6, 0.37, 0.37), (0.86, 0.3, 0.3)], side, 8, caps=(lid, lid)))


def pirate_chest():
    a = Atlas(64, 32, 13)
    planks(a, 0, 0, 64, 12, False, 4)
    for x in (7, 23, 39, 55):
        a.rect(x, 0, 3, 12, IRON)
        a.rect(x, 0, 1, 12, IRON_L)
        a.px(x + 1, 2, WHITE), a.px(x + 1, 9, WHITE)
    a.rect(30, 3, 4, 5, GOLD)
    a.rect(31, 5, 2, 2, BLACK)
    a.shade(0, 0, 64, 12, 1.05, 0.8, 1.0)
    side = a.region(0, 0, 64, 12)
    planks(a, 0, 12, 64, 8, False, 4)
    for x in (7, 23, 39, 55):
        a.rect(x, 12, 3, 8, IRON)
    a.rect(0, 19, 64, 1, WOOD_D)
    lid_side = a.region(0, 12, 64, 8)
    planks(a, 0, 20, 24, 12, False, 4)
    for x in (4, 18):
        a.rect(x, 20, 3, 12, IRON)
        a.rect(x, 20, 1, 12, IRON_L)
    lid_top = a.region(0, 20, 24, 12)
    a.rect(24, 20, 4, 4, WOOD_D)
    under = a.region(24, 20, 4, 4)
    m = Model("chest", a)
    return m.part("body", (0.0, 0.0, 0.0),
                  at(box((0.8, 0.4, 0.5), side, None, under), 0.0, 0.2)
                  + at(box((0.82, 0.2, 0.52), lid_side, lid_top, None, (1.0, 0.55)), 0.0, 0.5))


def pirate_flag():
    """Флаг с черепом и костями на шесте; полотно отдельной частью, качается у шеста."""
    a = Atlas(64, 32, 17)
    a.rect(0, 0, 32, 20, BLACK)
    a.rect(12, 4, 8, 7, BONE)
    a.rect(13, 11, 6, 2, BONE)
    a.rect(13, 6, 2, 3, BLACK), a.rect(17, 6, 2, 3, BLACK)
    a.px(15, 9, BLACK), a.px(16, 9, BLACK)
    for x in (14, 16, 18):
        a.px(x, 12, BLACK)
    for i in range(10):
        a.px(11 + i, 13 + i // 2, BONE), a.px(20 - i, 13 + i // 2, BONE)
    for y in range(0, 20, 5):
        a.rect(0, y, 32, 1, mul(BLACK, 1.5))
    a.rect(30, 0, 2, 20, mul(BLACK, 1.6))
    a.noise(0, 0, 32, 20, 0.12)
    cloth = a.region(0, 0, 32, 20)
    planks(a, 32, 0, 8, 32, True, 4)
    pole = a.region(32, 0, 8, 32)
    a.rect(40, 0, 8, 8, STONE_D)
    a.noise(40, 0, 8, 8, 0.15)
    base = a.region(40, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, base))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


def pirate_cannon():
    a = Atlas(64, 32, 19)
    a.rect(0, 0, 32, 16, IRON)
    for y in (2, 9, 14):
        a.rect(0, y, 32, 1, IRON_L)
        a.rect(0, y + 1, 32, 1, BLACK)
    a.rect(13, 4, 6, 1, IRON_L)
    a.shade(0, 0, 32, 16, 1.0, 1.0, 0.6)
    a.noise(0, 0, 32, 16, 0.12)
    barrel = a.region(0, 0, 32, 16)
    a.rect(32, 0, 8, 8, BLACK)
    a.rect(33, 1, 6, 6, IRON)
    a.rect(34, 2, 4, 4, BLACK)
    bore = a.region(32, 0, 8, 8)
    planks(a, 0, 16, 32, 12, False, 4)
    a.rect(0, 16, 32, 1, IRON), a.rect(0, 27, 32, 1, IRON)
    carriage = a.region(0, 16, 32, 12)
    wheel = paint_wheel(a, 40, 0)
    a.rect(56, 0, 8, 4, WOOD_D)
    rim = a.region(56, 0, 8, 4)
    m = Model("cannon", a)
    return m.part("body", (0.0, 0.0, 0.0),
                  at(rot(loft([(-0.5, 0.2, 0.2), (-0.3, 0.17, 0.17), (0.5, 0.13, 0.13), (0.56, 0.15, 0.15)], barrel, 8,
                              caps=(bore, bore)), rx=-90.0), 0.0, 0.52, -0.1)
                  + at(box((0.46, 0.22, 0.85), carriage, carriage, None, (0.8, 1.0)), 0.0, 0.3, 0.1)
                  + at(rot(loft([(-0.04, 0.24, 0.24), (0.04, 0.24, 0.24)], rim, 8, caps=(wheel, wheel), flat=True), rz=90.0),
                       -0.28, 0.24, 0.2)
                  + at(rot(loft([(-0.04, 0.24, 0.24), (0.04, 0.24, 0.24)], rim, 8, caps=(wheel, wheel), flat=True), rz=90.0),
                       0.28, 0.24, 0.2))


def pirate_captain():
    """Капитан: второй боец и главарь. Красный камзол с золотыми пуговицами, борода, повязка на глазу, треуголка."""
    a = Atlas(64, 64, 43)
    coat, coat_d = rgb("8E2A2A"), rgb("5C1A1C")
    a.rect(0, 0, 32, 17, coat)
    for x in (10, 21):
        a.rect(x, 0, 2, 17, coat_d)
    a.rect(13, 0, 6, 5, WHITE)
    a.rect(15, 0, 2, 3, SKIN)
    for y in (6, 9, 12, 15):
        a.px(14, y, GOLD), a.px(17, y, GOLD)
    a.rect(0, 0, 4, 2, GOLD), a.rect(28, 0, 4, 2, GOLD)
    a.rect(0, 17, 32, 3, BLACK)
    a.rect(14, 17, 4, 3, GOLD)
    a.rect(15, 18, 2, 1, BLACK)
    a.shade(0, 0, 32, 20, 1.1, 0.82, 0.7)
    a.noise(0, 0, 32, 20, 0.07)
    torso = a.region(0, 0, 32, 20)
    a.rect(0, 20, 32, 16, SKIN)
    a.rect(0, 20, 32, 4, BLACK)
    a.rect(0, 24, 9, 9, BLACK), a.rect(23, 24, 9, 9, BLACK)
    a.rect(11, 26, 3, 1, BLACK), a.rect(18, 26, 3, 1, BLACK)
    a.rect(11, 27, 3, 3, BLACK)
    a.rect(0, 26, 32, 1, BLACK)
    a.px(19, 28, BLACK), a.px(20, 28, WHITE)
    a.rect(15, 28, 2, 2, mul(SKIN, 0.85))
    a.rect(9, 30, 14, 6, BLACK)
    a.rect(13, 31, 6, 1, RED_D)
    for _ in range(14):
        a.px(a.rng.randrange(9, 23), a.rng.randrange(31, 36), IRON_L)
    a.shade(0, 20, 32, 16, 1.05, 0.9, 0.8)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    a.rect(32, 0, 16, 16, coat)
    a.rect(32, 9, 16, 3, GOLD)
    a.rect(32, 10, 16, 1, GOLD_D)
    a.rect(32, 12, 16, 4, SKIN)
    a.rect(32, 15, 16, 1, SKIN_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.07)
    arm = a.region(32, 0, 16, 16)
    a.rect(48, 0, 16, 10, rgb("2A2630"))
    a.rect(48, 10, 16, 5, WHITE)
    a.rect(48, 15, 16, 9, BOOT)
    a.rect(48, 15, 16, 2, BOOT_L)
    a.rect(54, 20, 4, 2, GOLD)
    a.shade(48, 0, 16, 24, 1.05, 0.85, 0.75)
    a.noise(48, 0, 16, 24, 0.07)
    leg = a.region(48, 0, 16, 24)
    a.rect(32, 16, 16, 8, BLACK)
    a.rect(32, 22, 16, 2, GOLD)
    a.rect(39, 17, 2, 3, BONE)
    a.noise(32, 16, 16, 8, 0.1)
    hat = a.region(32, 16, 16, 8)
    a.rect(32, 24, 8, 8, BLACK)
    a.rect(32, 24, 8, 1, GOLD), a.rect(32, 31, 8, 1, GOLD), a.rect(32, 24, 1, 8, GOLD), a.rect(39, 24, 1, 8, GOLD)
    brim = a.region(32, 24, 8, 8)
    a.rect(40, 24, 4, 4, BOOT)
    sole = a.region(40, 24, 4, 4)
    parts = biped(leg, torso, head, arm, sole, brim, 1.18)
    parts["head"][1].extend(loft([(1.7, 0.27, 0.25), (1.72, 0.27, 0.25)], hat, 3, math.pi, caps=(brim, brim), flat=True)
                            + loft([(1.72, 0.12, 0.12), (1.84, 0.09, 0.09)], hat, 5, caps=(None, brim)))
    return assemble("captain", a, parts)


def pirate_palm():
    """Пальма: изогнутый ствол с кольцами и семь листьев плоскостями с вырезом по прозрачности."""
    a = Atlas(32, 32, 45)
    bark, bark_d = rgb("8A6A46"), rgb("5E4630")
    a.rect(0, 0, 16, 32, bark)
    for y in range(0, 32, 4):
        a.rect(0, y, 16, 1, bark_d)
        for x in range(0, 16, 3):
            a.px(x + (y // 4) % 3, y + 1, mul(bark, 1.15))
    a.shade(0, 0, 16, 32, 0.95, 1.0, 0.7)
    a.noise(0, 0, 16, 32, 0.08)
    trunk = a.region(0, 0, 16, 32)
    leaf_c, leaf_d, leaf_l = rgb("3E8A3A"), rgb("255E2C"), rgb("6CB04A")
    for y in range(32):
        half = int(1 + 6.5 * math.sin(math.pi * min(y / 30.0, 1.0)) ** 0.7)
        for x in range(16):
            dx = abs(x - 7.5)
            if dx <= half and (int(dx) + y) % 3 != 0 or dx < 1.0:
                a.px(16 + x, y, leaf_d if dx < 1.0 else (leaf_l if (x + y) % 5 == 0 else leaf_c))
    a.noise(16, 0, 16, 32, 0.08)
    leaf = a.region(16, 0, 16, 32)
    top = (0.55, 4.2, 0.1)
    tris = loft([(0.0, 0.2, 0.2), (1.0, 0.16, 0.16, 0.08, 0.0), (2.2, 0.14, 0.14, 0.26, 0.04), (3.3, 0.12, 0.12, 0.44, 0.08),
                 (4.2, 0.1, 0.1, 0.55, 0.1)], trunk, 5)
    for k in range(7):
        ang = 2.0 * math.pi * k / 7.0 + 0.3
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * 0.38, 0.0, -math.sin(ang) * 0.38)
        droop = 0.9 + 0.35 * (k % 2)
        far = (top[0] + d[0] * 2.0, top[1] - droop, top[2] + d[2] * 2.0)
        mid = (top[0] + d[0] * 0.2, top[1] + 0.25, top[2] + d[2] * 0.2)
        tris += quad((mid[0] - q[0], mid[1], mid[2] - q[2]), (mid[0] + q[0], mid[1], mid[2] + q[2]),
                     (far[0] + q[0], far[1], far[2] + q[2]), (far[0] - q[0], far[1], far[2] - q[2]), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def pirate_bottle():
    """Бутылка рома: бонус. Зелёное стекло с бликом, этикетка, пробка."""
    a = Atlas(16, 16, 47)
    glass, glass_d = rgb("2E6A4A"), rgb("1C4634")
    a.rect(0, 0, 16, 12, glass)
    a.rect(0, 0, 16, 3, glass_d)
    a.rect(5, 5, 7, 5, rgb("E0D4A8"))
    a.rect(6, 6, 5, 1, RED_D), a.rect(7, 8, 3, 1, BLACK)
    a.rect(9, 1, 1, 10, rgb("9CD8B4"))
    a.shade(0, 0, 16, 12, 1.1, 0.85, 0.75)
    a.noise(0, 0, 16, 12, 0.06)
    body = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, rgb("B08A58"))
    cork = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, glass_d)
    under = a.region(4, 12, 4, 4)
    return Model("bottle", a).part("body", (0.0, 0.25, 0.0),
                                   loft([(0.0, 0.11, 0.11), (0.26, 0.11, 0.11), (0.33, 0.045, 0.045), (0.48, 0.04, 0.04),
                                         (0.5, 0.055, 0.055)], body, 6, caps=(under, cork)))


def pirate_ball():
    """Ядро: снаряд. Чугунный шар из шести меридианов с бликом и раковинами."""
    a = Atlas(16, 16, 49)
    a.rect(0, 0, 16, 16, IRON)
    a.rect(6, 3, 3, 2, IRON_L)
    a.px(7, 3, WHITE)
    for _ in range(10):
        a.px(a.rng.randrange(16), a.rng.randrange(16), BLACK)
    a.shade(0, 0, 16, 16, 1.25, 0.6, 0.8)
    a.noise(0, 0, 16, 16, 0.1)
    iron = a.region(0, 0, 16, 16)
    r = 0.18
    rings = [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in (0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35)]
    return Model("ball", a).part("body", (0.0, r, 0.0), loft(rings, iron, 6, caps=(iron, iron)))


def pirate_crate():
    """Ящик: препятствие. Доски в раме с раскосом и клеймом."""
    a = Atlas(32, 32, 51)
    planks(a, 0, 0, 32, 16, True, 4)
    for x in (0, 8, 16, 24):
        a.rect(x, 0, 8, 2, WOOD_D), a.rect(x, 14, 8, 2, WOOD_D)
        a.rect(x, 0, 1, 16, WOOD_D), a.rect(x + 7, 0, 1, 16, WOOD_D)
        for i in range(6):
            a.px(x + 1 + i, 3 + i * 2 // 1 % 10, WOOD_L)
            a.px(x + 1 + i, 2 + i * 2, WOOD_D)
    a.rect(11, 6, 3, 3, RED_D)
    a.shade(0, 0, 32, 16, 1.05, 0.8, 1.0)
    side = a.region(0, 0, 32, 16)
    planks(a, 0, 16, 16, 16, False, 4)
    a.rect(0, 16, 16, 1, WOOD_D), a.rect(0, 31, 16, 1, WOOD_D), a.rect(0, 16, 1, 16, WOOD_D), a.rect(15, 16, 1, 16, WOOD_D)
    top = a.region(0, 16, 16, 16)
    return Model("crate", a).part("body", (0.0, 0.0, 0.0), at(box((0.85, 0.85, 0.85), side, top, top), 0.0, 0.425))


def pirate_lighthouse():
    """Маяк: финиш. Полосатая башня с дверью, балкон, фонарь с переплётом, красная крыша."""
    a = Atlas(64, 64, 53)
    white, red = rgb("D8D2C4"), rgb("A8322C")
    for y in range(40):
        a.rect(0, y, 64, 1, red if (y // 8) % 2 == 0 else white)
    for y in range(0, 40, 4):
        for x in range((y // 4 % 2) * 4, 64, 8):
            a.px(x, y, mul(white, 0.75)), a.px(x, y + 1, mul(white, 0.8))
    a.rect(29, 31, 6, 9, WOOD_D)
    a.rect(30, 32, 4, 8, WOOD)
    a.px(33, 36, GOLD)
    for wx, wy in ((31, 10), (12, 20), (50, 20)):
        a.rect(wx, wy, 3, 4, BLACK)
        a.px(wx + 1, wy + 1, rgb("9CC8E8"))
    a.shade(0, 0, 64, 40, 1.05, 0.85, 0.7)
    a.noise(0, 0, 64, 40, 0.06)
    tower = a.region(0, 0, 64, 40)
    a.rect(0, 40, 32, 8, rgb("F2D060"))
    for x in range(0, 32, 4):
        a.rect(x, 40, 1, 8, BLACK)
    a.rect(0, 40, 32, 1, BLACK), a.rect(0, 47, 32, 1, BLACK)
    a.rect(13, 42, 6, 4, WHITE)
    lamp = a.region(0, 40, 32, 8)
    a.rect(32, 40, 16, 8, red)
    for x in range(32, 48, 4):
        a.rect(x, 40, 1, 8, mul(red, 0.7))
    a.shade(32, 40, 16, 8, 1.2, 0.8, 1.0)
    roof = a.region(32, 40, 16, 8)
    a.rect(48, 40, 8, 8, STONE_D)
    a.noise(48, 40, 8, 8, 0.15)
    stone = a.region(48, 40, 8, 8)
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0),
                                       loft([(0.0, 1.5, 1.5), (3.4, 1.25, 1.25), (6.8, 1.0, 1.0)], tower, 8)
                                       + loft([(6.8, 1.35, 1.35), (7.0, 1.35, 1.35)], stone, 8, caps=(stone, stone), flat=True)
                                       + loft([(7.0, 0.75, 0.75), (8.0, 0.75, 0.75)], lamp, 8)
                                       + loft([(8.0, 0.95, 0.95), (9.0, 0.04, 0.04)], roof, 8, caps=(stone, None)))


def paint_wheel(a, x0, y0):
    """Колесо 16×16: обод, спицы, железная ступица; вокруг прозрачно."""
    a.rect(x0, y0, 16, 16, WOOD)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            if d > 7.6:
                a.clear(x0 + i, y0 + j)
            elif d > 5.6:
                a.px(x0 + i, y0 + j, WOOD_D)
            elif d < 1.8:
                a.px(x0 + i, y0 + j, IRON_L)
            elif abs(i - 7.5) > 0.9 and abs(j - 7.5) > 0.9 and abs(abs(i - 7.5) - abs(j - 7.5)) > 1.2:
                a.px(x0 + i, y0 + j, BLACK)
    return a.region(x0, y0, 16, 16)


def make_cart(name, rival):
    """Сухопутная шлюпка под парусом: транспорт гонок. Оси с колёсами отдельными частями, крутятся.

    У героя борт с красной полосой и белый парус в синюю полоску, у соперника чёрный борт и
    чёрный парус с черепом.
    """
    a = Atlas(64, 64, 61 if not rival else 63)
    planks(a, 0, 0, 64, 12, False, 4)
    a.rect(0, 2, 64, 3, BLACK if rival else RED)
    a.rect(0, 5, 64, 1, GOLD_D if rival else WHITE)
    for x in range(3, 64, 8):
        a.px(x, 9, IRON_L)
    a.shade(0, 0, 64, 12, 1.08, 0.8, 1.0)
    hull = a.region(0, 0, 64, 12)
    planks(a, 0, 12, 16, 16, True, 4)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12)
    a.rect(32, 12, 8, 4, WOOD_D)
    rim = a.region(32, 12, 8, 4)
    planks(a, 40, 12, 8, 16, True, 4)
    mast = a.region(40, 12, 8, 16)
    if rival:
        a.rect(0, 32, 32, 28, BLACK)
        a.rect(12, 38, 8, 7, BONE), a.rect(13, 45, 6, 2, BONE)
        a.rect(13, 40, 2, 3, BLACK), a.rect(17, 40, 2, 3, BLACK)
        for i in range(10):
            a.px(11 + i, 48 + i // 2, BONE), a.px(20 - i, 48 + i // 2, BONE)
    else:
        stripes(a, 0, 32, 32, 28, rgb("E2DCC8"), rgb("E2DCC8"), 4)
        for y in (38, 39, 48, 49):
            a.rect(0, y, 32, 1, NAVY)
    for x in (0, 16):
        a.rect(x, 32, 1, 28, mul(a.get(x, 33), 0.8))
    a.noise(0, 32, 32, 28, 0.07)
    sail = a.region(0, 32, 32, 28)
    m = Model(name, a)
    m.part("body", (0.0, 0.0, 0.0),
           at(box((1.0, 0.36, 2.0), hull, deck, deck, (1.12, 1.0)), 0.0, 0.58)
           + at(box((0.62, 0.3, 0.55), hull, deck, deck, (0.5, 0.6)), 0.0, 0.6, -1.22)
           + at(box((0.8, 0.12, 0.3), deck, deck, deck), 0.0, 0.84, 0.55)
           + at(loft([(0.0, 0.05, 0.05), (2.0, 0.035, 0.035)], mast, 4), 0.0, 0.76, -0.25)
           + at(box((1.5, 0.07, 0.07), mast, mast, mast), 0.0, 2.62, -0.25)
           + quad((-0.72, 2.6, -0.28), (0.72, 2.6, -0.28), (0.62, 1.2, -0.38), (-0.62, 1.2, -0.38), sail))
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-0.05, 0.32, 0.32), (0.05, 0.32, 0.32)], rim, 8, caps=(wheel, wheel), flat=True), rz=90.0), x, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def pirate_cart():
    return make_cart("cart", False)


def pirate_cart_rival():
    return make_cart("cart_rival", True)


def pirate_pistol():
    """Кремнёвый пистолет в руке: оружие вида от первого лица, ствол смотрит в −Z, ноль в рукояти."""
    a = Atlas(32, 32, 65)
    a.rect(0, 0, 16, 8, IRON)
    a.rect(0, 2, 16, 1, IRON_L), a.rect(0, 6, 16, 1, BLACK)
    a.rect(0, 0, 16, 1, GOLD_D)
    a.noise(0, 0, 16, 8, 0.1)
    iron = a.region(0, 0, 16, 8)
    a.rect(16, 0, 4, 4, BLACK)
    bore = a.region(16, 0, 4, 4)
    planks(a, 0, 8, 16, 8, False, 4)
    a.rect(0, 8, 16, 1, GOLD_D)
    a.px(4, 12, GOLD), a.px(11, 12, GOLD)
    wood = a.region(0, 8, 16, 8)
    a.rect(0, 16, 16, 8, SKIN)
    a.rect(0, 19, 16, 1, SKIN_D)
    for x in (3, 7, 11):
        a.rect(x, 16, 1, 3, SKIN_D)
    a.shade(0, 16, 16, 8, 1.05, 0.85, 0.8)
    a.noise(0, 16, 16, 8, 0.05)
    hand = a.region(0, 16, 16, 8)
    stripes(a, 16, 8, 16, 16, WHITE, NAVY)
    a.shade(16, 8, 16, 16, 1.0, 0.85, 0.75)
    a.noise(16, 8, 16, 16, 0.06)
    sleeve = a.region(16, 8, 16, 16)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0),
                                   at(rot(loft([(-0.17, 0.024, 0.024), (0.17, 0.02, 0.02)], iron, 6, caps=(bore, bore)), rx=-90.0), 0.0, 0.06, -0.2)
                                   + at(box((0.045, 0.05, 0.3), wood, wood, wood), 0.0, 0.02, -0.14)
                                   + at(rot(box((0.045, 0.15, 0.06), wood, wood, wood), rx=-20.0), 0.0, -0.05, 0.03)
                                   + at(box((0.02, 0.05, 0.04), iron, iron, iron), 0.0, 0.1, -0.02)
                                   + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, -0.04, 0.03)
                                   + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.08, 0.07))


def pirate_hoop():
    """Кольцо на мачте: цель спорта. Щит из досок с белой рамкой, железный обруч, верёвочная сетка."""
    a = Atlas(64, 64, 67)
    planks(a, 0, 0, 32, 24, False, 6)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1), (10, 9, 1, 10), (21, 9, 1, 10)):
        a.rect(x, y, w, h, WHITE)
    a.rect(0, 0, 32, 1, WOOD_D), a.rect(0, 23, 32, 1, WOOD_D), a.rect(0, 0, 1, 24, WOOD_D), a.rect(31, 0, 1, 24, WOOD_D)
    board = a.region(0, 0, 32, 24)
    a.rect(32, 0, 16, 4, RED)
    a.rect(32, 0, 16, 1, mul(RED, 1.3)), a.rect(32, 3, 16, 1, RED_D)
    ring = a.region(32, 0, 16, 4)
    rope = rgb("D8CCA8")
    for y in range(16):
        for x in range(32):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                a.px(32 + x, 8 + y, rope if (x + y) % 8 else mul(rope, 0.8))
    net = a.region(32, 8, 32, 16)
    planks(a, 0, 24, 8, 32, True, 4)
    post = a.region(0, 24, 8, 32)
    rim_y, rim_z = 3.05, -0.42
    ring_tris = []
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        p = lambda r, t: (r * math.sin(t), rim_y, rim_z + r * math.cos(t))
        ring_tris += quad(p(0.19, a0), p(0.19, a1), p(0.245, a1), p(0.245, a0), ring)
    basket = at(loft([(rim_y - 0.42, 0.13, 0.13), (rim_y, 0.215, 0.215)], net, 8), 0.0, 0.0, rim_z)
    # Щит собран из граней без ящика внутри: лицо и изнанка целой текстурой по 2×2 плитки
    # (аффинное наложение не перекашивает рамку), торцы полосками. Слоёв друг под другом нет:
    # при дрожании вершин нечему просвечивать.
    faces = []
    u0, v0, u1, v1 = board
    for z, mirror in ((-0.15, 1.0), (-0.09, -1.0)):
        for ix in range(2):
            for iy in range(2):
                xa, xb = 0.65 - 0.65 * ix, 0.65 - 0.65 * (ix + 1)
                ya, yb = 3.875 - 0.475 * iy, 3.875 - 0.475 * (iy + 1)
                part = (u0 + (u1 - u0) * ix / 2.0, v0 + (v1 - v0) * iy / 2.0, u0 + (u1 - u0) * (ix + 1) / 2.0, v0 + (v1 - v0) * (iy + 1) / 2.0)
                faces += quad((xa * mirror, ya, z), (xb * mirror, ya, z), (xb * mirror, yb, z), (xa * mirror, yb, z), part, False)
    edge = (u0, v0, u0 + (u1 - u0) / 16.0, v1)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


def pirate_keg():
    """Бочонок: мяч. Маленький, с обручами, летит и крутится."""
    a = Atlas(16, 16, 69)
    planks(a, 0, 0, 16, 12, True, 4)
    a.rect(0, 2, 16, 1, IRON_L), a.rect(0, 9, 16, 1, IRON_L)
    a.shade(0, 0, 16, 12, 1.15, 0.75, 0.85)
    side = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, WOOD_D)
    a.px(1, 13, WOOD_L)
    lid = a.region(0, 12, 4, 4)
    return Model("keg", a).part("body", (0.0, 0.15, 0.0),
                                loft([(0.0, 0.1, 0.1), (0.08, 0.15, 0.15), (0.22, 0.15, 0.15), (0.3, 0.1, 0.1)], side, 6, caps=(lid, lid)))


def tex_road():
    """Укатанная грунтовая дорога: колеи, камешки, следы."""
    a = Atlas(64, 64, 71)
    dirt, dirt_d, dirt_l = rgb("8E7250"), rgb("6A5238"), rgb("A88C62")
    a.rect(0, 0, 64, 64, dirt)
    for x in (18, 19, 44, 45):
        a.rect(x, 0, 1, 64, dirt_d)
    for x in (20, 46):
        a.rect(x, 0, 1, 64, dirt_l)
    for _ in range(200):
        a.px(a.rng.randrange(64), a.rng.randrange(64), dirt_d if a.rng.random() < 0.55 else dirt_l)
    for _ in range(16):
        x, y = a.rng.randrange(62), a.rng.randrange(62)
        a.px(x, y, STONE_L), a.px(x + 1, y, STONE), a.px(x, y + 1, STONE_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_mud():
    """Грязь: тёмная мокрая земля с лужами и комьями."""
    a = Atlas(64, 64, 73)
    mud, mud_d, mud_l = rgb("4A3524"), rgb("2E2016"), rgb("6A4E34")
    a.rect(0, 0, 64, 64, mud)
    for _ in range(14):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(3, 7)
        for y in range(-r, r + 1):
            for x in range(-r * 2, r * 2 + 1):
                if (x / 2.0) ** 2 + y ** 2 <= r * r:
                    a.px((cx + x) % 64, (cy + y) % 64, mud_d)
        a.px((cx - 1) % 64, (cy - 1) % 64, rgb("8A8478"))
    for _ in range(220):
        a.px(a.rng.randrange(64), a.rng.randrange(64), mud_l if a.rng.random() < 0.5 else mud_d)
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Попутный ветер: белые стрелки вперёд на прозрачном, текстура бежит по полосе."""
    a = Atlas(32, 32, 75)
    white, pale = rgb("F4F8FF"), rgb("B8DCF4")
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, white)
                a.px(x, row + 4 + k, white)
                a.px(x, row + 5 + k, pale)
    return a


def tex_grass():
    a = Atlas(64, 64, 55)
    g, gd, gl = rgb("4E8A3C"), rgb("386C30"), rgb("78AE4C")
    a.rect(0, 0, 64, 64, g)
    for _ in range(260):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = gd if a.rng.random() < 0.55 else gl
        a.px(x, y, c), a.px(x, (y + 1) % 64, c)
    for _ in range(12):
        x, y = a.rng.randrange(62), a.rng.randrange(62)
        a.px(x, y, rgb("E8D860")), a.px(x + 1, y + 1, gd)
    for _ in range(8):
        x, y = a.rng.randrange(60), a.rng.randrange(60)
        a.rect(x, y, 3, 2, SAND_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


# --- Пираты: текстуры уровня (плиткой) ----------------------------------------------------------

def tex_sand():
    a = Atlas(64, 64, 31)
    a.rect(0, 0, 64, 64, SAND)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.07 * math.sin((x + 9.0 * math.sin(y * math.pi / 16.0)) * math.pi / 8.0)
            a.px(x, y, mul(SAND, k))
    for _ in range(150):
        a.px(a.rng.randrange(64), a.rng.randrange(64), SAND_D if a.rng.random() < 0.6 else SAND_L)
    for _ in range(10):
        x, y = a.rng.randrange(62), a.rng.randrange(62)
        a.px(x, y, STONE_L), a.px(x + 1, y, STONE), a.px(x, y + 1, STONE_D)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_planks():
    a = Atlas(64, 64, 33)
    planks(a, 0, 0, 64, 64, True, 8)
    for y in (15, 47):
        for x in range(0, 64, 8):
            a.rect(x, y + (x // 8 % 2) * 16, 8, 1, WOOD_D)
            a.px(x + 2, y + (x // 8 % 2) * 16 + 2, IRON), a.px(x + 5, y + (x // 8 % 2) * 16 + 2, IRON)
    return a


def tex_water():
    a = Atlas(64, 64, 35)
    deep, mid, foam = rgb("1F4E8C"), rgb("2F6FB5"), rgb("9CC8E8")
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            a.px(x, y, mid if w > 0.3 else deep)
            if w > 1.55:
                a.px(x, y, foam)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_rock():
    a = Atlas(64, 64, 37)
    a.rect(0, 0, 64, 64, STONE)
    for y in range(0, 64, 8):
        off = (y // 8 % 2) * 8
        a.rect(0, y, 64, 1, STONE_D)
        for x in range(off, 64 + off, 16):
            a.rect(x % 64, y, 1, 8, STONE_D)
            a.rect((x + 1) % 64, y + 1, 6, 1, STONE_L)
    for _ in range(120):
        a.px(a.rng.randrange(64), a.rng.randrange(64), STONE_D if a.rng.random() < 0.5 else STONE_L)
    for _ in range(14):
        x, y = a.rng.randrange(64), a.rng.randrange(60)
        a.rect(x, y, 1, a.rng.randrange(2, 5), rgb("4E6A3A"))
    a.shade(0, 0, 64, 64, 1.1, 0.8, 1.0)
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_sail():
    a = Atlas(32, 32, 39)
    cloth = rgb("D8D0B8")
    a.rect(0, 0, 32, 32, cloth)
    for x in (0, 16):
        a.rect(x, 0, 1, 32, mul(cloth, 0.8))
    for y in (10, 21):
        a.rect(0, y, 32, 1, mul(cloth, 0.86))
    a.rect(5, 14, 4, 3, mul(cloth, 0.75))
    a.noise(0, 0, 32, 32, 0.06)
    return a


def tex_sky():
    """Панорама неба: градиент, пиксельные облака, далёкие острова у горизонта. Плитка по горизонтали."""
    a = Atlas(128, 64, 41)
    top, low = rgb("3E7CC4"), rgb("B4DCEC")
    for y in range(64):
        t = min(y / 52.0, 1.0)
        a.rect(0, y, 128, 1, tuple(int(top[i] + (low[i] - top[i]) * t * t) for i in range(3)))
    for _ in range(9):
        cx, cy, w = a.rng.randrange(128), a.rng.randrange(8, 40), a.rng.randrange(10, 24)
        for k in range(w):
            h = int(2 + 3 * math.sin(math.pi * k / w) + a.rng.random() * 2)
            a.rect((cx + k) % 128, cy - h, 1, h, rgb("F2F4F0"))
            a.px((cx + k) % 128, cy, rgb("C2D4E0"))
    for cx, w, h in ((14, 26, 7), (70, 18, 5), (104, 30, 9)):
        for k in range(w):
            a.rect((cx + k) % 128, 56 - int(h * math.sin(math.pi * k / w)), 1, int(h * math.sin(math.pi * k / w)) + 1, rgb("5E8C7C"))
    a.rect(0, 56, 128, 8, rgb("2F6FB5"))
    a.noise(0, 0, 128, 64, 0.03)
    return a


SETS = {
    "pirates": {
        "models": [pirate_hero, pirate_enemy, pirate_captain, pirate_coin, pirate_bottle, pirate_ball, pirate_rock,
                   pirate_barrel, pirate_crate, pirate_chest, pirate_cannon, pirate_palm, pirate_flag, pirate_lighthouse,
                   pirate_cart, pirate_cart_rival, pirate_pistol, pirate_hoop, pirate_keg],
        "textures": {"sand": tex_sand, "planks": tex_planks, "water": tex_water, "rock": tex_rock, "sail": tex_sail,
                     "grass": tex_grass, "road": tex_road, "mud": tex_mud, "wind": tex_wind, "sky": tex_sky},
    },
}


def main():
    global DENSE, TEX_SCALE, FOLDER
    only_list = "--list" in sys.argv
    bad = False
    # Два набора из одних описаний: low poly и плотный для «продвинутых» (threed).
    for FOLDER, DENSE, TEX_SCALE, limit in (("lowpoly", 1, 1, MAX_TRIS), ("threed", 2, 4, MAX_TRIS_DENSE)):
        for setting, content in SETS.items():
            folder = os.path.join(ROOT, setting, FOLDER)
            for make in content["models"]:
                m = make()
                over = m.tris() > limit
                bad = bad or over
                print("%-8s %-8s %-8s частей %d, треугольников %4d, атлас %d×%d%s" % (
                    FOLDER, setting, m.name, len(m.parts), m.tris(), m.atlas.w * TEX_SCALE, m.atlas.h * TEX_SCALE,
                    "  БОЛЬШЕ %d" % limit if over else ""))
                if not only_list:
                    m.write(folder, setting)
            for name, make in content["textures"].items():
                a = make()
                print("%-8s %-8s tex_%-8s %d×%d" % (FOLDER, setting, name, a.w * TEX_SCALE, a.h * TEX_SCALE))
                if not only_list:
                    os.makedirs(folder, exist_ok=True)
                    a.save(os.path.join(folder, "tex_%s.png" % name))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
