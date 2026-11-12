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
        self.im.save(path)


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
            '[ext_resource type="Texture2D" path="res://assets/settings/%s/lowpoly/%s.png" id="2_tex"]' % (setting, self.name),
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

    m = Model("hero", a)
    for side, x in (("l", -0.1), ("r", 0.1)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               loft([(0.0, 0.07, 0.13, x, -0.04), (0.1, 0.065, 0.085, x, -0.01), (0.47, 0.075, 0.08, x, 0.0),
                     (0.88, 0.1, 0.105, x, 0.0)], leg, 5, caps=(boot_chip, None)))
    m.part("body", (0.0, 0.86, 0.0),
           loft([(0.82, 0.17, 0.115), (1.02, 0.155, 0.1), (1.27, 0.2, 0.125), (1.42, 0.17, 0.105), (1.47, 0.06, 0.06)],
                torso, 6))
    m.part("head", (0.0, 1.46, 0.0),
           loft([(1.44, 0.055, 0.06), (1.52, 0.09, 0.1, 0.0, -0.005), (1.64, 0.105, 0.115), (1.74, 0.07, 0.08)],
                head, 6, caps=(None, red_chip))
           + at(box((0.07, 0.06, 0.1), red_chip, red_chip, red_chip), 0.04, 1.63, 0.14), "body")
    for side, x in (("l", -0.25), ("r", 0.25)):
        m.part("arm_" + side, (x, 1.38, 0.0),
               loft([(0.78, 0.035, 0.045, x * 1.08, 0.0), (1.1, 0.045, 0.05, x * 1.06, 0.0), (1.4, 0.06, 0.065, x, 0.0)],
                    arm, 4, math.pi / 4.0, caps=(boot_chip, None)), "body")
    return m


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
    # Колесо: обод, спицы, ступица.
    a.rect(40, 0, 16, 16, WOOD)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            if d > 7.6:
                a.clear(40 + i, j)
            elif d > 5.6:
                a.px(40 + i, j, WOOD_D)
            elif d < 1.8:
                a.px(40 + i, j, IRON_L)
            elif abs(i - 7.5) > 0.9 and abs(j - 7.5) > 0.9 and abs(abs(i - 7.5) - abs(j - 7.5)) > 1.2:
                a.px(40 + i, j, BLACK)
    wheel = a.region(40, 0, 16, 16)
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
        "models": [pirate_hero, pirate_enemy, pirate_coin, pirate_rock, pirate_barrel, pirate_chest, pirate_flag,
                   pirate_cannon],
        "textures": {"sand": tex_sand, "planks": tex_planks, "water": tex_water, "rock": tex_rock, "sail": tex_sail,
                     "sky": tex_sky},
    },
}


def main():
    only_list = "--list" in sys.argv
    bad = False
    for setting, content in SETS.items():
        folder = os.path.join(ROOT, setting, "lowpoly")
        for make in content["models"]:
            m = make()
            over = m.tris() > MAX_TRIS
            bad = bad or over
            print("%-8s %-8s частей %d, треугольников %3d, атлас %d×%d%s" % (
                setting, m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h, "  БОЛЬШЕ %d" % MAX_TRIS if over else ""))
            if not only_list:
                m.write(folder, setting)
        for name, make in content["textures"].items():
            a = make()
            print("%-8s tex_%-8s %d×%d" % (setting, name, a.w, a.h))
            if not only_list:
                os.makedirs(folder, exist_ok=True)
                a.save(os.path.join(folder, "tex_%s.png" % name))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
