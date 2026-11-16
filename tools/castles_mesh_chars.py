#!/usr/bin/env python3
"""Персонажи «Замков» для low poly и «продвинутых» (#137): рыцарь, стражник чужого замка,
чёрный рыцарь. Зеркала `pirate_hero`, `pirate_enemy`, `pirate_captain` из `lowpoly_meshes.py`
и `space_mesh_chars.py`: те же имена частей, родители и точки вращения (демки анимируют части),
рост, взгляд в −Z, ноль в подошвах; у стражника оружие в правой руке на месте сабли скелета
(алебарда наперевес, остриём вперёд). Облик и цвета из основы 16/32 (`castles16.py`): ведёрный
шлем с красным плюмажем и красный табард у рыцаря, шлем-котелок, чёрная кольчуга и багровая
туника у стражника. Плотный набор «продвинутых» получается из этих же функций (плотность и
размер атласа задаёт `lowpoly_meshes`), поэтому геометрия собирается его помощниками.

    python3 tools/castles_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета из палитры `castles16.PALETTE`; тени стали и чернёного железа подобраны к ней.
STEEL, STEEL_D, STEEL_L = rgb("9EA8BA"), rgb("6A7288"), rgb("E8ECF2")
IRON, IRON_D, IRON_L = rgb("3C4050"), rgb("23252F"), rgb("5E6478")
RED, RED_D, RED_L = rgb("D2302C"), rgb("942838"), rgb("EC5E4A")
CRIMSON, CRIMSON_D, CRIMSON_L = rgb("942838"), rgb("5A1626"), rgb("B8404C")
GOLD, GOLD_D = rgb("F4C84A"), rgb("9C642C")
LEATHER, LEATHER_D, LEATHER_L = rgb("9C642C"), rgb("5E3A1C"), rgb("C08A48")
SKIN, SKIN_D = rgb("F0C498"), rgb("C08E64")
BLACK = rgb("15131A")
BONE, BONE_D = rgb("E6DEC6"), rgb("A89C80")
FUR, FUR_D = rgb("CFCBC2"), rgb("8C8880")


def _rivets(a, x, y, w, c, step=4):
    for i in range(x + 1, x + w, step):
        a.px(i, y, c)


def _mail(a, x, y, w, h, dark=IRON, light=IRON_L):
    """Кольчуга: кольца в шахматном порядке, каждая вторая строка сдвинута."""
    for j in range(y, y + h):
        for i in range(x, x + w):
            a.px(i, j, light if (i + j) % 2 == 0 and j % 2 == 0 or (i + j) % 4 == 1 else dark)


def _plate(outline, z0, z1, face, rim):
    """Плоская пластина (щит): контур в плоскости XY выдавлен от `z0` до `z1`, лицо на `z1`
    смотрит в +Z (за спину модели), развёртка лица проекцией в `face`, торцы в `rim`."""
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    u0, v0, u1, v1 = face
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

    def uv(p):
        return (u0 + (u1 - u0) * (p[0] - min(xs)) / (max(xs) - min(xs)),
                v0 + (v1 - v0) * (max(ys) - p[1]) / (max(ys) - min(ys)))

    def add(vs, uvs, out):
        """Грань лицом в сторону `out`: при обратном обходе вершины меняются местами."""
        n = lm._cross(lm._sub(vs[1], vs[0]), lm._sub(vs[2], vs[0]))
        if n[0] * out[0] + n[1] * out[1] + n[2] * out[2] < 0.0:
            vs, uvs = [vs[0], vs[2], vs[1]], [uvs[0], uvs[2], uvs[1]]
        tris.append(lm._tri(vs, uvs))

    tris = []
    for k in range(1, len(outline) - 1):
        ps = (outline[0], outline[k], outline[k + 1])
        add([(p[0], p[1], z1) for p in ps], [uv(p) for p in ps], (0.0, 0.0, 1.0))
    r0, t0, r1, t1 = rim
    for k, p in enumerate(outline):
        q = outline[(k + 1) % len(outline)]
        out = ((p[0] + q[0]) / 2.0 - cx, (p[1] + q[1]) / 2.0 - cy, 0.0)
        a, b, c, d = (p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)
        add([a, b, c], [(r0, t1), (r1, t1), (r1, t0)], out)
        add([a, c, d], [(r0, t1), (r1, t0), (r0, t0)], out)
    return tris


# --- Рыцарь ------------------------------------------------------------------------------------

def castles_hero():
    """Рыцарь: стальные латы, красный табард с золотой короной на груди и юбкой ниже пояса,
    плоский сверху ведёрный шлем с золотым крестом и прорезью, красный гребень и хвост плюмажа
    за затылком, за спиной треугольный щит с крестом."""
    a = lm.Atlas(64, 64, 211)
    # Торс 32×20: середина куска это грудь. Сверху стальные плечи и горжет, ниже красный табард,
    # в разрезах на боках кольчуга, на груди золотая корона, на талии золотой пояс.
    a.rect(0, 0, 32, 20, RED)
    a.rect(0, 0, 32, 4, STEEL)
    a.rect(0, 0, 32, 1, STEEL_L)
    a.rect(0, 3, 32, 1, STEEL_D)
    _rivets(a, 0, 2, 32, STEEL_D, 4)
    a.rect(12, 0, 8, 2, STEEL_D)  # горжет под шлемом
    a.rect(12, 2, 8, 1, STEEL_L)
    a.rect(10, 3, 12, 1, RED), a.rect(11, 4, 10, 1, GOLD)  # вырез табарда с золотым кантом
    for x in (6, 24):
        _mail(a, x, 5, 3, 10)  # кольчуга в боковых разрезах
        a.rect(x - 1, 5, 1, 10, RED_D), a.rect(x + 3, 5, 1, 10, RED_D)
    # Корона на груди: три зубца, обруч, камни.
    for x in (13, 16, 19):
        a.rect(x, 6, 1, 2, GOLD)
    a.px(14, 7, GOLD), a.px(15, 7, GOLD), a.px(17, 7, GOLD), a.px(18, 7, GOLD)
    a.rect(13, 8, 7, 2, GOLD)
    a.rect(13, 10, 7, 1, GOLD_D)
    a.px(14, 9, RED_D), a.px(16, 9, STEEL_L), a.px(18, 9, RED_D)
    for x in (2, 10, 21, 29):
        a.rect(x, 11, 1, 3, RED_D)  # складки ткани
    a.rect(0, 14, 32, 2, GOLD)
    a.rect(0, 15, 32, 1, GOLD_D)
    a.rect(14, 13, 4, 4, GOLD_D), a.rect(15, 14, 2, 2, GOLD)  # пряжка
    for x in (3, 9, 13, 18, 22, 28):
        a.rect(x, 16, 1, 4, RED_D)
        a.px(x + 1, 17, RED_L), a.px(x + 1, 18, RED_L)
    a.shade(0, 0, 32, 20, 1.08, 0.86, 0.76)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Шлем 32×16: четыре пояса по четыре строки. Скос темени, пояс с прорезью (перёд в середине),
    # низ с дыхательными отверстиями и ободом, раструб к шее. Крест из золотых полос.
    a.rect(0, 20, 32, 16, STEEL)
    a.rect(0, 20, 32, 3, STEEL_L)
    a.rect(0, 23, 32, 1, STEEL_D)
    _rivets(a, 1, 24, 32, STEEL_D, 4)
    a.rect(8, 25, 16, 3, GOLD)  # перекладина креста вокруг прорези
    a.rect(8, 27, 16, 1, GOLD_D)
    a.rect(9, 26, 14, 1, BLACK)  # прорезь
    a.rect(15, 21, 2, 11, GOLD)  # стойка креста
    a.rect(16, 21, 1, 11, GOLD_D)
    for x, y in ((19, 28), (21, 28), (20, 29), (22, 29), (19, 30), (21, 30), (11, 29), (12, 30), (10, 30)):
        a.px(x, y, BLACK)  # дыхательные отверстия
    for x in (0, 31):
        a.rect(x, 23, 1, 9, STEEL_D)  # шов на затылке
    a.rect(4, 25, 1, 6, STEEL_L), a.rect(27, 25, 1, 6, STEEL_D)
    a.rect(0, 31, 32, 1, IRON)  # обод
    a.rect(0, 32, 32, 4, STEEL_D)
    _mail(a, 0, 33, 32, 3)
    a.shade(0, 20, 32, 16, 1.08, 0.9, 0.8)
    a.noise(0, 20, 32, 16, 0.04)
    helmet = a.region(0, 20, 32, 16)
    # Рука 16×16: наплечник с золотым кантом, кольчуга, налокотник, наруч, тёмная латная перчатка.
    a.rect(32, 0, 16, 16, STEEL)
    a.rect(32, 0, 16, 2, STEEL_L)
    a.rect(32, 3, 16, 1, GOLD_D)
    _mail(a, 32, 4, 16, 3)
    a.rect(32, 7, 16, 3, STEEL_L)
    a.rect(32, 9, 16, 1, STEEL_D)
    a.px(39, 8, GOLD), a.px(40, 8, GOLD_D)
    a.rect(39, 10, 1, 3, STEEL_D)  # ребро наруча
    a.rect(32, 12, 16, 1, STEEL_D)
    a.rect(32, 13, 16, 3, IRON_L)
    a.rect(32, 13, 16, 1, STEEL)
    for x in (35, 39, 43):
        a.rect(x, 14, 1, 2, IRON)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.76)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: кольчуга под юбкой, набедренник с ребром, наколенник с заклёпкой, поножи,
    # сегментный стальной башмак.
    a.rect(48, 0, 16, 24, STEEL)
    _mail(a, 48, 0, 16, 3)
    a.rect(48, 3, 16, 1, STEEL_L)
    a.rect(55, 3, 1, 6, STEEL_L), a.rect(56, 3, 1, 6, STEEL_D)
    a.rect(48, 8, 16, 1, STEEL_D)
    a.rect(51, 9, 10, 4, STEEL_L)
    a.rect(51, 12, 10, 1, STEEL_D)
    a.px(55, 10, GOLD), a.px(56, 10, GOLD_D)
    a.rect(48, 13, 16, 1, IRON)
    a.rect(55, 14, 2, 4, STEEL_L)
    a.rect(49, 15, 2, 1, STEEL_D), a.rect(60, 16, 2, 1, STEEL_D)
    a.rect(48, 18, 16, 6, STEEL_D)
    a.rect(48, 18, 16, 1, STEEL_L)
    for y in (20, 22):
        a.rect(48, y, 16, 1, IRON)
    a.rect(54, 21, 4, 1, STEEL)
    a.shade(48, 0, 16, 24, 1.05, 0.85, 0.76)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Плюмаж 16×12: красные перья, тёмные бороздки наискось, светлые кончики.
    a.rect(32, 16, 16, 12, RED)
    for y in range(12):
        for x in range(16):
            k = (x + y * 2) % 5
            if k == 0:
                a.px(32 + x, 16 + y, RED_D)
            elif k == 2 and y % 3 == 0:
                a.px(32 + x, 16 + y, RED_L)
    a.rect(32, 16, 16, 1, RED_L)
    a.shade(32, 16, 16, 12, 1.1, 0.78, 0.9)
    a.noise(32, 16, 16, 12, 0.06)
    plume = a.region(32, 16, 16, 12)
    # Щит 16×20: стальная кайма с заклёпками, красное поле, золотой крест, потёртости.
    a.rect(32, 28, 16, 20, STEEL)
    a.rect(33, 29, 14, 18, RED)
    a.rect(33, 29, 14, 1, RED_L)
    a.rect(39, 29, 2, 18, GOLD)
    a.rect(40, 29, 1, 18, GOLD_D)
    a.rect(33, 34, 14, 2, GOLD)
    a.rect(33, 35, 14, 1, GOLD_D)
    a.rect(39, 34, 2, 2, STEEL_L)  # умбон в перекрестье
    for x, y in ((32, 28), (47, 28), (32, 37), (47, 37), (36, 44), (43, 44)):
        a.px(x, y, IRON)
    for x, y in ((35, 31), (36, 32), (44, 39), (43, 40), (35, 40)):
        a.px(x, y, RED_D)
    # Косые кромки к острию: вдоль них кайма, как на прямых краях.
    for y in range(38, 48):
        edge = (y - 37) * 8 // 10
        a.rect(32 + edge, y, 2, 1, STEEL), a.rect(46 - edge, y, 2, 1, STEEL)
    a.shade(32, 28, 16, 20, 1.08, 0.82, 0.88)
    a.noise(32, 28, 16, 20, 0.05)
    shield = a.region(32, 28, 16, 20)
    # Юбка табарда 32×6: складки и золотая кайма по подолу.
    a.rect(0, 36, 32, 6, RED)
    for x in (2, 6, 11, 15, 20, 24, 29):
        a.rect(x, 36, 1, 5, RED_D)
        a.rect(x + 1, 37, 1, 3, RED_L)
    a.rect(0, 40, 32, 1, GOLD), a.rect(0, 41, 32, 1, GOLD_D)
    a.shade(0, 36, 32, 6, 0.95, 0.8, 0.8)
    a.noise(0, 36, 32, 6, 0.05)
    skirt = a.region(0, 36, 32, 6)
    a.rect(48, 28, 4, 4, IRON)
    a.rect(52, 28, 4, 4, STEEL_L)
    a.rect(56, 28, 4, 4, STEEL_D)
    a.rect(60, 28, 4, 4, RED)
    sole, crown, rim, red_chip = (a.region(48, 28, 4, 4), a.region(52, 28, 4, 4), a.region(56, 28, 4, 4),
                                  a.region(60, 28, 4, 4))

    parts = lm.biped(leg, torso, helmet, arm, sole, crown)
    # Ведёрный шлем вместо головы: цилиндр шире шеи с плоским теменем. Сверху гребень плюмажа,
    # от него за затылок спадает хвост перьев.
    parts["head"][1] = (
        lm.loft([(1.44, 0.075, 0.08), (1.47, 0.13, 0.14), (1.6, 0.135, 0.145), (1.73, 0.135, 0.145),
                 (1.77, 0.115, 0.125)], helmet, 6, caps=(None, crown))
        + lm.at(lm.box((0.045, 0.085, 0.25), plume, red_chip), 0.0, 1.795, 0.0)
        + lm.loft([(1.48, 0.012, 0.02, 0.0, 0.33), (1.6, 0.04, 0.05, 0.0, 0.31), (1.74, 0.045, 0.06, 0.0, 0.24),
                   (1.84, 0.03, 0.07, 0.0, 0.12)], plume, 4, caps=(None, red_chip)))
    # Юбка табарда чуть ниже бёдер и щит за спиной (спина это +Z), утоплен в спину без щели.
    parts["body"][1].extend(lm.loft([(0.74, 0.24, 0.16), (0.87, 0.19, 0.127)], skirt, 6))
    parts["body"][1].extend(_plate([(-0.17, 1.42), (0.17, 1.42), (0.17, 1.2), (0.0, 0.96), (-0.17, 1.2)],
                                   0.09, 0.168, shield, rim))
    return lm.assemble("hero", a, parts)


# --- Стражник чужого замка ---------------------------------------------------------------------

def castles_enemy():
    """Стражник: шлем-котелок с широкими полями, кольчужный капюшон, усатое лицо, багровая
    туника с чёрной башней на груди поверх чёрной кольчуги, бурые сапоги, алебарда в правой
    руке остриём вперёд."""
    a = lm.Atlas(64, 64, 223)
    # Тело 32×20, четыре пояса по пять строк: кольчужная пелерина на плечах, грудь с гербом,
    # живот с ремнём, подол туники с кольчужной каймой.
    a.rect(0, 0, 32, 20, CRIMSON)
    _mail(a, 0, 0, 32, 5)
    a.rect(12, 0, 8, 2, IRON_D)  # тень под подбородком
    for x in range(0, 32, 4):
        a.px(x, 5, IRON), a.px(x + 1, 5, IRON)  # зубцы края пелерины
    for x in (6, 24):
        _mail(a, x, 6, 2, 8)  # кольчуга в проймах
    # Чёрная башня: герб чужого замка.
    for x in (13, 15, 17, 19):
        a.px(x, 6, BLACK)
    a.rect(13, 7, 7, 1, BLACK)
    a.rect(14, 8, 5, 3, BLACK)
    a.rect(13, 11, 7, 1, BLACK)
    a.px(16, 9, CRIMSON_L), a.px(16, 10, CRIMSON_L)  # бойница
    for x in (3, 10, 22, 28):
        a.rect(x, 8, 1, 5, CRIMSON_D)
    a.rect(0, 13, 32, 2, LEATHER_D)
    a.rect(0, 13, 32, 1, LEATHER)
    a.rect(14, 12, 4, 4, GOLD_D), a.rect(15, 13, 2, 2, GOLD)
    a.rect(20, 15, 2, 3, LEATHER_D)  # кошель на ремне
    for x in (2, 7, 12, 19, 25, 30):
        a.rect(x, 15, 1, 3, CRIMSON_D)
        a.px(x + 1, 16, CRIMSON_L)
    _mail(a, 0, 18, 32, 2)
    a.shade(0, 0, 32, 20, 1.1, 0.84, 0.74)
    a.noise(0, 0, 32, 20, 0.06)
    body = a.region(0, 0, 32, 20)
    # Голова 32×16: кольчужный капюшон кругом, лицо в середине: брови, глаза, нос, усы, щетина.
    _mail(a, 0, 20, 32, 16)
    a.rect(10, 24, 12, 9, SKIN)
    a.rect(11, 33, 10, 1, SKIN_D)
    a.rect(10, 24, 12, 1, SKIN_D)  # тень от полей шлема
    a.rect(11, 25, 3, 1, LEATHER_D), a.rect(18, 25, 3, 1, LEATHER_D)  # брови
    a.px(12, 26, BLACK), a.px(13, 26, rgb("FFFFFF")), a.px(18, 26, rgb("FFFFFF")), a.px(19, 26, BLACK)
    a.rect(15, 26, 2, 3, mul(SKIN, 0.9))
    a.px(16, 28, SKIN_D)
    a.rect(12, 29, 8, 1, LEATHER_D)  # усы
    a.px(11, 30, LEATHER_D), a.px(20, 30, LEATHER_D)
    a.rect(14, 31, 4, 1, CRIMSON_D)
    for _ in range(12):
        a.px(a.rng.randrange(11, 21), a.rng.randrange(31, 33), mul(SKIN, 0.75))
    a.rect(9, 24, 1, 10, IRON_D), a.rect(22, 24, 1, 10, IRON_D)  # край капюшона
    a.shade(0, 20, 32, 16, 1.0, 0.9, 0.8)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16: короткий багровый рукав, кольчуга, кожаный наруч, перчатка.
    _mail(a, 32, 0, 16, 16)
    a.rect(32, 0, 16, 4, CRIMSON)
    a.rect(32, 3, 16, 1, CRIMSON_D)
    a.rect(32, 9, 16, 4, LEATHER_D)
    a.rect(32, 9, 16, 1, LEATHER)
    a.px(39, 11, GOLD_D)
    a.rect(32, 13, 16, 3, LEATHER)
    for x in (35, 39, 43):
        a.rect(x, 14, 1, 2, LEATHER_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.06)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×20, четыре пояса по пять строк: тёмные шоссы с заплатой на колене, сапог с
    # отворотом и ремешком, стопа.
    a.rect(32, 16, 16, 20, IRON)
    a.rect(39, 16, 1, 10, IRON_D)
    for y in (18, 21):
        a.rect(34 + (y % 3), y, 4, 1, IRON_D)
    a.rect(37, 22, 6, 3, IRON_L)
    a.rect(32, 26, 16, 10, LEATHER)
    a.rect(32, 26, 16, 2, LEATHER_L)
    a.rect(32, 28, 16, 1, LEATHER_D)
    a.rect(32, 30, 16, 1, LEATHER_D), a.px(40, 30, GOLD)
    a.rect(32, 34, 16, 2, LEATHER_D)
    a.shade(32, 16, 16, 20, 1.05, 0.85, 0.76)
    a.noise(32, 16, 16, 20, 0.06)
    leg = a.region(32, 16, 16, 20)
    # Шлем-котелок: купол 16×8 с ребром и заклёпками, поля 8×8 (вид сверху, кольцо темнее).
    a.rect(48, 0, 16, 8, STEEL)
    a.rect(48, 0, 16, 2, STEEL_L)
    a.rect(55, 0, 2, 7, STEEL_L), a.rect(57, 0, 1, 7, STEEL_D)
    a.rect(48, 7, 16, 1, STEEL_D)
    _rivets(a, 48, 6, 16, IRON, 3)
    a.noise(48, 0, 16, 8, 0.05)
    dome = a.region(48, 0, 16, 8)
    a.rect(48, 8, 8, 8, STEEL)
    a.rect(49, 9, 6, 6, STEEL_L)
    a.rect(50, 10, 4, 4, STEEL_D)
    a.px(48, 8, STEEL_D), a.px(55, 8, STEEL_D), a.px(48, 15, STEEL_D), a.px(55, 15, STEEL_D)
    a.noise(48, 8, 8, 8, 0.05)
    brim = a.region(48, 8, 8, 8)
    a.rect(56, 8, 4, 4, LEATHER_D)
    a.rect(60, 8, 4, 4, STEEL_L)
    a.rect(56, 12, 4, 4, STEEL_D)
    a.rect(60, 12, 4, 4, LEATHER)
    chip, crown, edge, palm = (a.region(56, 8, 4, 4), a.region(60, 8, 4, 4), a.region(56, 12, 4, 4),
                               a.region(60, 12, 4, 4))
    # Алебарда 32×12: слева пятка древка, справа железо: широкий топор лезвием вверх, крюк вниз,
    # длинная пика вперёд. Остальное прозрачно.
    a.rect(0, 44, 28, 1, LEATHER)
    for x in range(2, 28, 5):
        a.px(x, 44, LEATHER_D)
    a.rect(0, 44, 2, 1, STEEL_D)
    a.rect(19, 44, 5, 1, STEEL_D)  # железные полосы под топором
    for y, x0, x1 in ((38, 20, 29), (39, 20, 29), (40, 21, 28), (41, 22, 27), (42, 23, 27), (43, 24, 26)):
        a.rect(x0, y, x1 - x0 + 1, 1, STEEL)
        a.px(x0, y, STEEL_D)
    a.rect(20, 38, 10, 1, STEEL_L)  # заточенная кромка
    a.px(20, 38, STEEL), a.px(29, 38, STEEL)
    a.px(25, 40, STEEL_D), a.px(25, 41, STEEL_D), a.px(24, 41, IRON)  # прорезь в полотне
    a.rect(24, 45, 4, 1, STEEL), a.rect(23, 46, 3, 1, STEEL), a.px(23, 47, STEEL_D)  # крюк
    a.px(24, 45, STEEL_D)
    a.rect(26, 44, 6, 1, STEEL_L)  # пика
    a.rect(26, 43, 3, 1, STEEL), a.rect(26, 45, 3, 1, STEEL_D)
    halberd = a.region(0, 38, 32, 12)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.06, 0.125, x, -0.04), (0.08, 0.052, 0.062, x, -0.005), (0.3, 0.06, 0.066, x, 0.0),
                        (0.5, 0.062, 0.066, x, 0.0), (0.88, 0.08, 0.085, x, 0.0)], leg, 4, math.pi / 4.0,
                       caps=(chip, None)))
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.78, 0.165, 0.115), (0.98, 0.135, 0.092), (1.12, 0.155, 0.1), (1.36, 0.19, 0.115),
                    (1.46, 0.05, 0.05)], body, 6))
    m.part("head", (0.0, 1.46, 0.0),
           lm.loft([(1.44, 0.055, 0.06), (1.52, 0.09, 0.1), (1.64, 0.105, 0.115), (1.73, 0.075, 0.085)], head, 6,
                   caps=(None, crown))
           # Поля котелка шире плеч головы, над ними низкий купол.
           + lm.loft([(1.665, 0.215, 0.215), (1.69, 0.195, 0.195)], edge, 8, caps=(brim, brim), flat=True)
           + lm.loft([(1.69, 0.125, 0.135), (1.77, 0.105, 0.115), (1.815, 0.04, 0.045)], dome, 6, caps=(None, crown)),
           "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.04, 0.042, -0.24, 0.0), (1.08, 0.045, 0.048, -0.235, 0.0), (1.4, 0.05, 0.055, -0.215, 0.0)],
                   arm, 4, math.pi / 4.0, caps=(palm, None)), "body")
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.04, 0.042, 0.24, 0.0), (1.08, 0.045, 0.048, 0.235, 0.0), (1.4, 0.05, 0.055, 0.215, 0.0)],
                   arm, 4, math.pi / 4.0, caps=(palm, None))
           # Алебарда на месте сабли скелета: древко проходит через кисть, железо впереди.
           + lm.quad((0.24, 1.0, 0.26), (0.24, 1.0, -0.86), (0.24, 0.58, -0.86), (0.24, 0.58, 0.26), halberd), "body")
    return m


# --- Чёрный рыцарь -----------------------------------------------------------------------------

def castles_captain():
    """Чёрный рыцарь: второй боец и главарь. Крупный, в чернёных латах с багровой эмалью,
    глухой шлем с Т-образной прорезью и красными глазами, бычьи рога в стороны и вверх, шипастые
    наплечники, за спиной багровый плащ до колен с волчьим мехом на плечах и рваным подолом."""
    a = lm.Atlas(64, 64, 243)
    # Кираса 32×20: горжет и плечи, нагрудник с ребром и багровым клинком-гербом, пластины живота,
    # багровый кушак с золотой пряжкой, набедренные пластины.
    a.rect(0, 0, 32, 20, IRON)
    a.rect(0, 0, 32, 1, IRON_L)
    a.rect(12, 0, 8, 3, IRON_D)
    a.rect(12, 3, 8, 1, CRIMSON)
    a.rect(0, 4, 32, 1, IRON_D)
    _rivets(a, 0, 3, 12, GOLD_D, 3), _rivets(a, 20, 3, 12, GOLD_D, 3)
    a.rect(15, 5, 1, 9, IRON_L), a.rect(16, 5, 1, 9, IRON_D)  # ребро нагрудника
    # Герб: багровый меч остриём вниз.
    a.rect(15, 6, 2, 6, CRIMSON), a.rect(13, 7, 6, 1, CRIMSON_L), a.px(15, 5, GOLD_D), a.px(16, 5, GOLD_D)
    a.px(15, 12, CRIMSON_D)
    for x in (8, 23):
        a.rect(x, 5, 1, 9, IRON_D)  # боковые швы кирасы
        a.px(x + 1, 6, IRON_L), a.px(x + 1, 10, IRON_L)
    for y in (10, 12):
        a.rect(9, y, 14, 1, IRON_D)  # пластины живота
        a.rect(9, y + 1, 14, 1, IRON_L)
    a.rect(15, 10, 2, 4, IRON)
    a.rect(0, 14, 32, 3, CRIMSON)
    a.rect(0, 14, 32, 1, CRIMSON_L)
    a.rect(0, 16, 32, 1, CRIMSON_D)
    a.rect(14, 14, 4, 3, GOLD), a.rect(15, 15, 2, 1, BLACK)
    for x in range(0, 32, 6):
        a.rect(x, 17, 1, 3, IRON_D)  # набедренные пластины
        a.rect(x + 1, 17, 4, 1, IRON_L)
        a.px(x + 3, 18, GOLD_D)
    a.rect(0, 19, 32, 1, CRIMSON_D)
    a.shade(0, 0, 32, 20, 1.15, 0.86, 0.74)
    a.noise(0, 0, 32, 20, 0.07)
    torso = a.region(0, 0, 32, 20)
    # Шлем 32×24, четыре пояса по шесть строк: темя с гребнем, лоб с багровой полосой, лицо с
    # Т-образной прорезью (перёд в середине), кольчужная бармица.
    a.rect(0, 20, 32, 24, IRON)
    a.rect(0, 20, 32, 2, IRON_L)
    a.rect(15, 20, 2, 12, IRON_L), a.rect(17, 20, 1, 12, IRON_D)  # гребень от темени ко лбу
    a.rect(0, 29, 32, 2, CRIMSON)
    a.rect(0, 30, 32, 1, CRIMSON_D)
    _rivets(a, 0, 29, 32, GOLD_D, 4)
    a.rect(8, 31, 16, 4, IRON_L)  # окантовка прорези
    a.rect(13, 35, 6, 6, IRON_L)
    a.rect(9, 32, 14, 2, BLACK)
    a.rect(15, 34, 2, 6, BLACK)
    a.rect(11, 32, 2, 1, RED), a.px(11, 33, RED_D), a.rect(19, 32, 2, 1, RED), a.px(20, 33, RED_D)  # глаза
    for x in (10, 21):
        for y in (36, 38, 40):
            a.px(x, y, BLACK), a.px(x + (1 if x < 16 else -1), y, IRON_D)  # дыхательные щели
    for x in (0, 31):
        a.rect(x, 26, 1, 15, IRON_D)
    a.rect(3, 33, 1, 7, IRON_L), a.rect(28, 33, 1, 7, IRON_D)
    a.rect(0, 41, 32, 1, CRIMSON_D)
    _mail(a, 0, 42, 32, 2, IRON_D, IRON)
    a.shade(0, 20, 32, 24, 1.18, 0.9, 0.8)
    a.noise(0, 20, 32, 24, 0.06)
    head = a.region(0, 20, 32, 24)
    # Рука 16×16: чернёные пластины с багровым кантом, налокотник с шипом, латная рукавица.
    a.rect(32, 0, 16, 16, IRON)
    for y in (2, 5):
        a.rect(32, y, 16, 1, IRON_D)
        a.rect(32, y + 1, 16, 1, IRON_L)
    a.rect(32, 7, 16, 3, IRON_L)
    a.rect(32, 9, 16, 1, CRIMSON)
    a.px(39, 8, GOLD_D), a.px(40, 8, GOLD)
    a.rect(39, 10, 1, 3, IRON_D)
    a.rect(32, 12, 16, 1, CRIMSON_D)
    a.rect(32, 13, 16, 3, IRON_D)
    a.rect(32, 13, 16, 1, IRON_L)
    for x in (35, 39, 43):
        a.rect(x, 14, 1, 2, BLACK)
    a.shade(32, 0, 16, 16, 1.1, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.07)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: набедренник, наколенник с багровым кантом и шипом, поножи, тяжёлый башмак.
    a.rect(48, 0, 16, 24, IRON)
    _mail(a, 48, 0, 16, 2, IRON_D, IRON)
    a.rect(48, 2, 16, 1, IRON_L)
    a.rect(55, 3, 1, 5, IRON_L), a.rect(56, 3, 1, 5, IRON_D)
    a.rect(48, 8, 16, 1, IRON_D)
    a.rect(51, 9, 10, 4, IRON_L)
    a.rect(51, 12, 10, 1, CRIMSON)
    a.px(55, 10, GOLD), a.px(56, 10, GOLD_D)
    a.rect(55, 14, 2, 4, IRON_L)
    a.rect(48, 13, 16, 1, IRON_D)
    a.rect(48, 18, 16, 6, IRON_D)
    a.rect(48, 18, 16, 1, CRIMSON)
    for y in (20, 22):
        a.rect(48, y, 16, 1, BLACK)
    a.rect(54, 21, 4, 1, IRON_L)
    a.shade(48, 0, 16, 24, 1.1, 0.85, 0.75)
    a.noise(48, 0, 16, 24, 0.07)
    leg = a.region(48, 0, 16, 24)
    # Плащ 24×20: волчий мех по плечам, багровые складки, тёмная кайма и рваный подол.
    a.rect(0, 44, 24, 20, CRIMSON)
    for x in (2, 6, 10, 14, 18, 22):
        a.rect(x, 48, 1, 15, CRIMSON_D)
        a.rect(x + 1, 49, 1, 12, CRIMSON_L)
    a.rect(0, 60, 24, 2, CRIMSON_D)
    a.shade(0, 44, 24, 20, 1.08, 0.78, 0.86)
    a.rect(0, 44, 24, 4, FUR)
    for x in range(24):
        a.px(x, 44 + (x * 5) % 3, FUR_D)
        if x % 2 == 0:
            a.px(x, 47, FUR_D)
        if x % 3 == 1:
            a.px(x, 48, FUR)
    for x in range(24):
        tear = (0, 2, 1, 3, 0, 1, 2, 0)[x % 8]
        if tear:
            a.clear(x, 64 - tear, 1, tear)
    a.noise(0, 44, 24, 20, 0.07)
    # Рог 8×12: кость с кольцами роста, тёмное основание, светлое остриё.
    a.rect(40, 16, 8, 12, BONE)
    a.rect(40, 16, 8, 2, rgb("FFFFFF"))
    for y in (20, 23, 25):
        a.rect(40, y, 8, 1, BONE_D)
    a.rect(40, 26, 8, 2, IRON_D)
    a.shade(40, 16, 8, 12, 1.05, 0.8, 0.85)
    horn = a.region(40, 16, 8, 12)
    # Наплечник 16×8: чернёная пластина с багровым кантом, заклёпками и шипами по ребру.
    a.rect(32, 28, 16, 8, IRON)
    a.rect(32, 28, 16, 1, IRON_L)
    a.rect(32, 34, 16, 2, CRIMSON), a.rect(32, 35, 16, 1, CRIMSON_D)
    for x in range(33, 48, 4):
        a.px(x, 32, GOLD_D)
        a.px(x + 1, 30, IRON_L), a.px(x + 2, 30, IRON_D)
    a.noise(32, 28, 16, 8, 0.07)
    pauldron = a.region(32, 28, 16, 8)
    a.rect(32, 16, 4, 4, IRON_D)
    a.rect(36, 16, 4, 4, IRON_L)
    sole, crown = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown, 1.18)
    # Глухой шлем с округлым теменем и рога: от висков в стороны и вверх, остриями чуть внутрь.
    helm = lm.loft([(1.44, 0.07, 0.075), (1.5, 0.13, 0.14), (1.66, 0.14, 0.15), (1.78, 0.115, 0.125),
                    (1.85, 0.045, 0.05)], head, 6, caps=(None, crown))
    for s in (-1.0, 1.0):
        helm += lm.loft([(1.66, 0.045, 0.045, s * 0.1, 0.0), (1.73, 0.04, 0.04, s * 0.2, 0.0),
                         (1.83, 0.026, 0.026, s * 0.245, 0.0), (1.925, 0.003, 0.003, s * 0.225, 0.0)], horn, 3,
                        math.pi / 2.0 * s)
    parts["head"][1] = helm
    # Наплечники шире плеч: сидят на руках и качаются вместе с ними.
    for side, s in (("l", -1.0), ("r", 1.0)):
        x = s * 0.25 * 1.18
        parts["arm_" + side][1].extend(lm.at(lm.box((0.2, 0.11, 0.23), pauldron, crown, None, (0.55, 0.6)),
                                             x + s * 0.01, 1.4, 0.0))
    # Плащ: три полотнища от плеч до колен, книзу шире и дальше от спины; верх прижат к спине.
    cloak = []
    top = [(0.27, 0.1), (0.09, 0.135), (-0.09, 0.135), (-0.27, 0.1)]
    low = [(0.37, 0.3), (0.13, 0.34), (-0.13, 0.34), (-0.37, 0.3)]
    for i in range(3):
        cloak += lm.quad((top[i][0], 1.43, top[i][1]), (top[i + 1][0], 1.43, top[i + 1][1]),
                         (low[i + 1][0], 0.5, low[i + 1][1]), (low[i][0], 0.5, low[i][1]),
                         a.region(i * 8, 44, 8, 20))
    parts["body"][1].extend(cloak)
    return lm.assemble("captain", a, parts)


MODELS = [castles_hero, castles_enemy, castles_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
