#!/usr/bin/env python3
"""Персонажи «Зомби» для low poly и «продвинутых» (#137): выживший, зомби-ходок, зомби-мясник.
Зеркала `pirate_hero`, `pirate_enemy`, `pirate_captain` из `lowpoly_meshes.py` и космических из
`space_mesh_chars.py`: те же имена частей, родители и точки вращения (демки анимируют части),
взгляд в −Z, ноль в подошвах, рост не выше 1,93 м; у ходока оружие в правой руке на месте сабли
скелета (лопата могильщика). Цвета и облик из основы 16/32 (`zombies16.PALETTE`): красная куртка,
синяя бейсболка и рюкзак со скаткой у героя, серые лохмотья и зелёная мёртвая кожа у зомби.
Плотный набор «продвинутых» получается из этих же функций (плотность и размер атласа задаёт
`lowpoly_meshes`), поэтому геометрия собирается его помощниками.

    python3 tools/zombies_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import zombies16 as z16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def _pal(i):
    return tuple(z16.PALETTE[i])


# Цвета из палитры основы 16/32, светлые и тёмные тона к ним.
BLACK = _pal(z16.K)
JACKET, JACKET_D, JACKET_L = _pal(z16.RED), rgb("8E2420"), rgb("EC6A4E")
DENIM, DENIM_D, DENIM_L = _pal(z16.SEA), _pal(z16.NAVY), _pal(z16.AQUA)
BONE, BONE_D = _pal(z16.WHITE), rgb("C4C0AE")
RAG, RAG_D, RAG_L = _pal(z16.GREY), rgb("6E7270"), rgb("C6C8BE")
SKIN, SKIN_D = _pal(z16.SKIN), _pal(z16.TAN)
LABEL, LABEL_D = _pal(z16.GOLD), _pal(z16.BRASS)
LEATHER, LEATHER_D, LEATHER_L = _pal(z16.METAL), _pal(z16.DARK), rgb("A88462")
ROT, ROT_D, ROT_L = _pal(z16.VIOLET), _pal(z16.PLUM), rgb("A6CC86")
BLOOD, BLOOD_D = rgb("B02A24"), rgb("6E1A1C")
STEEL, STEEL_D, STEEL_L = rgb("8C9296"), rgb("50565C"), rgb("C8CED0")
RUBBER, RUBBER_D = rgb("2E2A30"), rgb("1C1A20")


def _spots(a, x, y, w, h, c, count):
    """Пятна в один-два пикселя: грязь, кровь, трупные пятна."""
    for _ in range(count):
        i, j = x + a.rng.randrange(w), y + a.rng.randrange(h)
        a.px(i, j, c)
        if a.rng.random() < 0.5:
            a.px(min(i + 1, x + w - 1), j, c)


def _turn(tris, pivot, rx=0.0, ry=0.0, rz=0.0):
    """Поворот куска вокруг точки (градусы): заваленная набок голова."""
    px, py, pz = pivot
    return lm.at(lm.rot(lm.at(tris, -px, -py, -pz), rx, ry, rz), px, py, pz)


# --- Выживший ----------------------------------------------------------------------------------

def zombies_hero():
    """Выживший: красная куртка на молнии, синяя бейсболка с длинным козырьком и белой панелью,
    джинсы с подворотом, белые кроссовки, за спиной кожаный рюкзак с зелёной скаткой."""
    a = lm.Atlas(64, 64, 211)
    # Торс 32×20: середина куска это грудь. Полосы колец сверху вниз: плечи с воротом, грудь,
    # живот, бёдра. Куртка расстёгнута у ворота, лямки рюкзака, карманы, резинка, ремень джинсов.
    a.rect(0, 0, 32, 17, JACKET)
    a.rect(13, 0, 6, 3, SKIN)  # шея
    a.rect(13, 2, 6, 1, SKIN_D)
    a.rect(13, 3, 6, 3, BONE)  # ворот футболки
    a.px(13, 5, JACKET), a.px(18, 5, JACKET)
    a.rect(11, 0, 2, 5, JACKET_L), a.rect(19, 0, 2, 5, JACKET_L)  # отвороты ворота
    a.px(12, 5, JACKET_L), a.px(19, 5, JACKET_L)
    a.rect(15, 6, 2, 10, JACKET_D)  # молния
    for y in range(7, 15, 2):
        a.px(16, y, RAG_D)  # зубцы
    a.px(15, 6, LABEL), a.px(16, 6, LABEL)  # бегунок
    for x in (9, 22):
        a.rect(x, 0, 2, 16, LEATHER)  # лямки рюкзака
        a.rect(x + (1 if x < 16 else 0), 0, 1, 16, LEATHER_D)
        a.rect(x, 8, 2, 1, LABEL_D)  # пряжка
    for x in (11, 18):
        a.rect(x, 11, 3, 1, JACKET_D)  # клапаны карманов
        a.px(x + 1, 12, LABEL_D)
    for x in (4, 27):
        a.rect(x, 2, 1, 13, JACKET_D)  # боковой шов
    a.rect(1, 6, 2, 1, JACKET_D), a.rect(29, 6, 2, 1, JACKET_D)
    a.rect(0, 15, 32, 2, JACKET_D)  # резинка по низу
    for x in range(0, 32, 2):
        a.px(x, 16, mul(JACKET_D, 0.8))
    a.rect(0, 17, 32, 3, DENIM)
    a.rect(0, 17, 32, 1, LEATHER_D)  # ремень
    a.rect(15, 17, 2, 1, LABEL)
    for x in (6, 12, 19, 25):
        a.px(x, 18, DENIM_D)  # шлёвки
    a.rect(15, 18, 1, 2, DENIM_D)  # ширинка
    a.shade(0, 0, 32, 20, 1.08, 0.86, 0.74)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×24, шесть полос по 4 строки: темя кепки, купол, околыш, глаза, рот, шея.
    a.rect(0, 20, 32, 12, DENIM)
    for x in (3, 9, 22, 28):
        a.rect(x, 20, 1, 11, DENIM_D)  # клинья купола
    a.rect(0, 20, 32, 1, DENIM_L)
    a.rect(13, 23, 6, 7, BONE)  # белая панель спереди
    a.rect(13, 29, 6, 1, BONE_D)
    a.rect(15, 25, 2, 3, JACKET), a.px(14, 26, JACKET), a.px(17, 26, JACKET)  # красный крест нашивки
    a.rect(0, 31, 32, 1, DENIM_D)  # кромка кепки
    a.rect(0, 27, 2, 4, LEATHER_D), a.rect(30, 27, 2, 4, LEATHER_D)  # вырез застёжки на затылке
    a.rect(0, 30, 2, 1, RAG_L), a.rect(30, 30, 2, 1, RAG_L)
    a.rect(0, 32, 32, 12, SKIN)
    a.rect(0, 32, 8, 7, LEATHER_D), a.rect(24, 32, 8, 7, LEATHER_D)  # волосы из-под кепки
    a.rect(0, 39, 6, 1, LEATHER_D), a.rect(26, 39, 6, 1, LEATHER_D)
    a.rect(8, 33, 1, 3, SKIN_D), a.rect(23, 33, 1, 3, SKIN_D)  # уши
    a.rect(9, 32, 14, 1, SKIN_D)  # тень козырька на лбу
    a.rect(11, 33, 3, 1, LEATHER_D), a.rect(18, 33, 3, 1, LEATHER_D)  # брови
    a.px(11, 34, BONE), a.px(12, 34, BLACK), a.px(19, 34, BLACK), a.px(20, 34, BONE)
    a.rect(15, 34, 2, 3, mul(SKIN, 0.92))
    a.px(15, 36, SKIN_D), a.px(16, 36, SKIN_D)
    a.rect(13, 38, 6, 1, rgb("9A4A3C"))  # рот
    for _ in range(22):
        a.px(a.rng.randrange(10, 22), a.rng.randrange(37, 41), mul(SKIN, 0.78))  # щетина
    a.rect(10, 35, 2, 1, mul(SKIN, 0.86))  # ссадина на скуле
    a.rect(0, 41, 32, 3, SKIN_D)
    a.rect(12, 41, 8, 1, mul(SKIN_D, 0.85))  # тень подбородка
    a.shade(0, 20, 32, 12, 1.1, 0.9, 0.82)
    a.shade(0, 32, 32, 12, 1.0, 0.9, 0.82)
    a.noise(0, 20, 32, 24, 0.04)
    head = a.region(0, 20, 32, 24)
    # Рука 16×16: рукав куртки со складками и заплатой на локте, вязаный манжет, кисть.
    a.rect(32, 0, 16, 11, JACKET)
    a.rect(32, 0, 16, 1, JACKET_L)
    a.rect(39, 1, 1, 9, JACKET_D)  # шов
    for y in (3, 6):
        a.rect(33 + (y % 4), y, 5, 1, JACKET_D)
    a.rect(42, 5, 4, 4, LEATHER), a.rect(42, 8, 4, 1, LEATHER_D)  # заплата на локте
    a.rect(32, 10, 16, 2, JACKET_D)
    for x in range(32, 48, 2):
        a.px(x, 11, mul(JACKET_D, 0.78))
    a.rect(32, 12, 16, 4, SKIN)
    a.rect(32, 14, 16, 1, SKIN_D)
    for x in (35, 39, 43):
        a.px(x, 15, SKIN_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.76)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: джинсы с потёртым коленом и швом, подворот, белый кроссовок с красной полосой.
    a.rect(48, 0, 16, 18, DENIM)
    a.rect(55, 0, 1, 16, DENIM_D)
    a.rect(49, 1, 4, 1, DENIM_D), a.rect(49, 2, 1, 2, DENIM_D)  # карман
    a.rect(53, 8, 6, 4, DENIM_L)  # потёртое колено
    a.px(54, 9, BONE_D), a.px(56, 10, BONE_D), a.px(57, 9, DENIM)
    for y in (5, 13):
        a.rect(50 + (y % 3), y, 4, 1, DENIM_D)
    a.rect(48, 16, 16, 2, DENIM_L)  # подворот
    a.rect(48, 17, 16, 1, DENIM_D)
    a.rect(48, 18, 16, 6, BONE)
    a.rect(48, 18, 16, 1, RAG)  # носок
    a.rect(48, 21, 16, 1, JACKET)  # красная полоса
    a.rect(54, 19, 4, 2, BONE_D)
    a.px(54, 19, RAG_D), a.px(57, 19, RAG_D), a.px(55, 20, RAG_D), a.px(56, 20, RAG_D)  # шнурки
    a.rect(48, 23, 16, 1, RAG)  # подошва
    a.shade(48, 0, 16, 24, 1.05, 0.86, 0.76)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Рюкзак 16×12 (бока лентой, середина куска это задняя стенка) и клапан 8×8.
    a.rect(32, 16, 16, 12, LEATHER)
    a.rect(32, 16, 16, 1, LEATHER_L)
    a.rect(32, 27, 16, 1, LEATHER_D)
    a.rect(32, 20, 16, 1, LEATHER_D)  # край клапана
    for x in (37, 42):
        a.rect(x, 16, 1, 9, LEATHER_D)  # ремешки
        a.px(x, 22, LABEL), a.px(x, 23, LABEL_D)
    a.rect(38, 23, 4, 3, LEATHER_D), a.rect(38, 23, 4, 1, LEATHER_L)  # карман
    a.rect(33, 22, 2, 4, BONE), a.px(33, 23, JACKET), a.px(34, 23, JACKET)  # нашивка-крест сбоку
    a.rect(45, 21, 2, 5, STEEL), a.px(45, 21, STEEL_L)  # фляга в сетке
    a.noise(32, 16, 16, 12, 0.07)
    pack = a.region(32, 16, 16, 12)
    a.rect(32, 28, 8, 8, LEATHER_L)
    a.rect(33, 29, 6, 6, LEATHER)
    a.rect(34, 28, 1, 8, LEATHER_D), a.rect(37, 28, 1, 8, LEATHER_D)
    a.noise(32, 28, 8, 8, 0.06)
    pack_top = a.region(32, 28, 8, 8)
    a.rect(40, 28, 4, 4, RAG_D)  # подошва
    a.rect(44, 28, 4, 4, DENIM)  # темя с пуговкой
    a.px(45, 29, DENIM_L), a.px(46, 30, DENIM_L)
    sole, crown = a.region(40, 28, 4, 4), a.region(44, 28, 4, 4)
    # Козырёк: верх 8×8 со строчкой, кромка 8×2, испод тёмный.
    a.rect(48, 24, 8, 8, DENIM)
    for y in (26, 28, 30):
        a.rect(48, y, 8, 1, DENIM_D if y != 28 else DENIM_L)
    a.rect(56, 24, 8, 2, DENIM_D)
    a.rect(56, 26, 8, 6, DENIM_D)
    a.noise(48, 24, 16, 8, 0.05)
    visor_top, visor_edge, visor_low = a.region(48, 24, 8, 8), a.region(56, 24, 8, 2), a.region(56, 26, 8, 6)
    # Скатка 16×8: зелёное одеяло с двумя ремнями, торец спиралью.
    a.rect(32, 36, 16, 8, ROT_D)
    for y in (37, 40, 42):
        a.rect(32, y, 16, 1, mul(ROT_D, 1.25))
    for x in (35, 44):
        a.rect(x, 36, 1, 8, LEATHER_D)
    a.noise(32, 36, 16, 8, 0.08)
    roll = a.region(32, 36, 16, 8)
    a.rect(48, 32, 4, 4, ROT_D)
    a.px(49, 33, mul(ROT_D, 1.3)), a.px(50, 34, mul(ROT_D, 0.7))
    roll_end = a.region(48, 32, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown)
    # Плечи куртки шире ворота, чтобы рукава сидели на торсе без щели.
    parts["body"][1] = lm.loft([(0.82, 0.17, 0.115), (1.02, 0.158, 0.102), (1.27, 0.21, 0.128), (1.42, 0.235, 0.108),
                                (1.47, 0.06, 0.06)], torso, 6)
    # Голова в кепке: купол чуть шире головы от линии бровей, сверху пуговка.
    parts["head"][1] = lm.loft([(1.44, 0.055, 0.06), (1.51, 0.088, 0.098, 0.0, -0.005), (1.58, 0.104, 0.114),
                                (1.65, 0.106, 0.116), (1.68, 0.116, 0.126), (1.755, 0.098, 0.108),
                                (1.79, 0.05, 0.055)], head, 6, caps=(None, crown))
    # Длинный плоский козырёк вперёд, корнем утоплен в купол.
    parts["head"][1].extend(lm.at(lm.box((0.17, 0.018, 0.2), visor_edge, visor_top, visor_low), 0.0, 1.668, -0.165))
    # Рюкзак за спиной (спина это +Z), утоплен в куртку; сверху скатка поперёк.
    parts["body"][1].extend(lm.at(lm.box((0.27, 0.36, 0.17), pack, pack_top, pack_top), 0.0, 1.18, 0.18))
    parts["body"][1].extend(lm.at(lm.rot(lm.loft([(-0.17, 0.062, 0.062), (0.17, 0.062, 0.062)], roll, 6,
                                                 caps=(roll_end, roll_end)), rz=90.0), 0.0, 1.41, 0.2))
    return lm.assemble("hero", a, parts)


# --- Зомби-ходок -------------------------------------------------------------------------------

def zombies_enemy():
    """Зомби-ходок: сутулый, голова завалена на плечо, серая рубаха в лохмотьях с пятнами крови,
    рваные штаны до голени, босой; один белый глаз и пустая глазница, в правой руке лопата."""
    a = lm.Atlas(64, 64, 223)
    # Тело 32×20, четыре полосы по 5 строк: плечи с шеей, грудь, живот, бёдра в штанах.
    a.rect(0, 0, 32, 16, RAG)
    a.rect(12, 0, 8, 3, ROT)  # шея
    a.rect(12, 2, 8, 1, ROT_D)
    a.rect(11, 0, 1, 4, RAG_L), a.rect(20, 0, 1, 4, RAG_L)  # растянутый ворот
    a.rect(12, 3, 8, 1, RAG_D)
    a.rect(15, 4, 1, 11, RAG_D)  # планка с оторванными пуговицами
    a.px(16, 6, BONE), a.px(16, 12, BONE)
    # Рана на боку: дыра в рубахе, под ней рёбра.
    a.rect(20, 7, 5, 5, BLOOD_D)
    a.rect(21, 8, 3, 3, BLOOD)
    a.rect(20, 8, 5, 1, BONE), a.rect(21, 10, 4, 1, BONE)
    a.px(19, 9, RAG_D), a.px(25, 8, RAG_D), a.px(22, 12, BLOOD_D), a.px(22, 13, BLOOD_D)
    # Дыры с мёртвой кожей и пятна.
    a.rect(7, 6, 3, 2, ROT), a.px(8, 8, ROT), a.px(7, 6, ROT_D)
    a.rect(27, 4, 2, 3, ROT), a.px(27, 4, ROT_D)
    a.rect(2, 9, 2, 3, ROT), a.px(2, 9, ROT_D)
    a.rect(10, 4, 3, 2, BLOOD), a.px(11, 6, BLOOD), a.px(11, 7, BLOOD_D)  # потёк от рта
    for x in (4, 13, 23, 29):
        a.rect(x, 5, 1, 9, RAG_D)  # складки
    _spots(a, 0, 3, 32, 12, LEATHER, 14)  # грязь
    # Рваный подол клочьями поверх штанов.
    a.rect(0, 15, 32, 5, LEATHER)
    for x in range(32):
        drop = (0, 2, 1, 3, 0, 1, 2, 0, 3, 1, 0)[(x * 7 + 3) % 11]
        a.rect(x, 15, 1, drop, RAG if drop < 3 else RAG_D)
    a.rect(0, 19, 32, 1, LEATHER_D)
    a.rect(15, 17, 1, 3, LEATHER_D)
    a.shade(0, 0, 32, 20, 1.08, 0.82, 0.72)
    a.noise(0, 0, 32, 20, 0.07)
    body = a.region(0, 0, 32, 20)
    # Голова 32×16, четыре полосы по 4 строки: темя с клочьями волос, глаза, рот, челюсть с шеей.
    a.rect(0, 20, 32, 16, ROT)
    a.rect(0, 20, 32, 2, ROT_L)
    for x in range(32):
        tuft = (3, 1, 0, 2, 4, 1, 0, 0, 3, 2, 5, 1, 0)[(x * 5 + 2) % 13]
        if x < 10 or x > 21:
            tuft += 3  # на затылке и висках волос больше
        a.rect(x, 20, 1, min(tuft, 9), LEATHER_D)
    a.rect(13, 20, 3, 2, ROT_L)  # проплешина надо лбом
    a.rect(9, 24, 6, 1, ROT_D), a.rect(17, 24, 6, 1, ROT_D)  # надбровья
    a.rect(10, 25, 4, 3, BONE)  # выкаченный белый глаз
    a.px(12, 26, BLACK), a.px(10, 27, ROT_D), a.px(13, 25, BONE_D)
    a.rect(18, 25, 4, 3, BLACK)  # пустая глазница
    a.px(19, 26, BLOOD_D), a.px(20, 28, BLOOD_D)
    a.rect(15, 27, 2, 2, ROT_D), a.px(15, 29, BLACK), a.px(16, 29, BLACK)  # провал носа
    a.rect(11, 31, 10, 2, BLACK)  # кривой рот с зубами
    a.px(21, 30, BLACK), a.px(10, 32, BLACK)
    for x in (12, 14, 15, 17, 19):
        a.px(x, 31, BONE)
    for x in (13, 16, 18):
        a.px(x, 32, BONE_D)
    a.rect(13, 33, 3, 1, BLOOD), a.px(14, 34, BLOOD), a.px(14, 35, BLOOD_D)  # кровь по подбородку
    a.rect(6, 29, 2, 3, ROT_D), a.rect(24, 28, 2, 3, ROT_D)  # впалые щёки
    a.rect(8, 26, 1, 3, ROT_D), a.rect(23, 26, 1, 3, ROT_D)  # уши
    _spots(a, 0, 24, 32, 10, ROT_D, 10)
    a.rect(0, 34, 13, 2, ROT_D), a.rect(16, 34, 16, 2, ROT_D)
    a.shade(0, 20, 32, 16, 1.08, 0.86, 0.78)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Нога 16×16, четыре полосы по 4 строки: бедро, колено с дырой, рваная кромка и голая голень,
    # босая стопа с пальцами.
    a.rect(32, 0, 16, 16, ROT)
    a.rect(32, 0, 16, 9, LEATHER)
    a.rect(39, 0, 1, 9, LEATHER_D)
    a.rect(38, 4, 4, 3, ROT), a.px(38, 4, LEATHER_D), a.px(41, 6, ROT_D)  # дыра на колене
    for x in range(32, 48):
        drop = (1, 3, 0, 2, 1, 0, 3, 2)[(x * 3) % 8]
        a.rect(x, 9, 1, drop, LEATHER if drop < 3 else LEATHER_D)
    a.rect(34, 2, 3, 1, LEATHER_D), a.rect(43, 5, 3, 1, LEATHER_D)
    a.rect(44, 10, 1, 2, ROT_D), a.px(35, 11, BLOOD_D), a.px(36, 11, BLOOD)  # жила и ссадина
    a.rect(32, 12, 16, 1, ROT_D)  # щиколотка
    a.rect(32, 15, 16, 1, ROT_D)
    for x in (37, 39, 41, 43):
        a.px(x, 14, ROT_D)  # пальцы
    a.shade(32, 0, 16, 16, 1.02, 0.9, 0.72)
    a.noise(32, 0, 16, 16, 0.07)
    limb = a.region(32, 0, 16, 16)
    # Рука 16×16, две полосы по 8 строк: рваный рукав до локтя, голое предплечье с укусом и
    # когтистая кисть.
    a.rect(48, 0, 16, 16, ROT)
    a.rect(48, 0, 16, 6, RAG)
    a.rect(48, 0, 16, 1, RAG_L)
    a.rect(55, 1, 1, 5, RAG_D)
    for x in range(48, 64):
        drop = (2, 0, 1, 3, 1, 0, 2)[(x * 3 + 1) % 7]
        a.rect(x, 6, 1, drop, RAG if drop < 3 else RAG_D)
    a.px(51, 3, LEATHER), a.px(52, 3, LEATHER), a.px(60, 2, BLOOD_D)
    a.rect(58, 9, 3, 2, BLOOD_D), a.px(59, 9, BLOOD), a.px(58, 11, BONE)  # укус
    a.rect(52, 8, 1, 5, ROT_D)  # жила
    a.rect(48, 12, 16, 1, ROT_D)  # запястье
    a.rect(48, 15, 16, 1, BLACK)  # когти
    for x in (51, 55, 59, 63):
        a.rect(x, 13, 1, 2, ROT_D)
    a.shade(48, 0, 16, 16, 1.04, 0.9, 0.72)
    a.noise(48, 0, 16, 16, 0.07)
    arm = a.region(48, 0, 16, 16)
    # Лопата 16×4: рукоять у кисти, черенок, штык с ржавой кромкой; вокруг прозрачно.
    a.rect(32, 17, 12, 2, LEATHER)
    a.rect(32, 17, 12, 1, LEATHER_L)
    a.rect(32, 16, 2, 4, LEATHER_D)  # поперечная рукоять
    a.px(37, 18, LEATHER_D), a.px(41, 17, LEATHER_D)
    a.rect(43, 16, 5, 4, STEEL)
    a.rect(43, 16, 5, 1, STEEL_L)
    a.rect(43, 19, 5, 1, STEEL_D)
    a.px(43, 17, STEEL_D), a.px(43, 18, STEEL_D)  # тулейка
    a.px(46, 18, rgb("8A5A36")), a.px(45, 17, rgb("8A5A36"))  # ржавчина
    a.px(47, 17, BLOOD), a.px(47, 18, BLOOD_D)
    a.clear(47, 16), a.clear(47, 19)
    spade = a.region(32, 16, 16, 4)
    # Клок волос 8×8: пряди торчат над теменем, остальное прозрачно.
    for x, h in ((0, 3), (1, 6), (2, 4), (3, 7), (4, 5), (5, 8), (6, 4), (7, 2)):
        a.rect(32 + x, 28 - h, 1, h, LEATHER_D if x % 2 else mul(LEATHER_D, 1.3))
    tuft = a.region(32, 20, 8, 8)
    a.rect(40, 20, 4, 4, ROT_D)
    a.rect(44, 20, 4, 4, LEATHER_D)
    a.px(45, 21, ROT), a.px(46, 22, ROT_L)
    chip, crown = a.region(40, 20, 4, 4), a.region(44, 20, 4, 4)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.055, 0.12, x, -0.04), (0.08, 0.042, 0.048, x, 0.0), (0.3, 0.056, 0.058, x, 0.005),
                        (0.48, 0.058, 0.06, x, 0.0), (0.88, 0.08, 0.085, x, 0.0)], limb, 5, caps=(chip, None)))
    # Сутулый корпус: плечи и шея уходят вперёд.
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.84, 0.15, 0.1), (0.98, 0.14, 0.095), (1.12, 0.165, 0.11, 0.0, -0.01),
                    (1.36, 0.2, 0.12, 0.0, -0.03), (1.46, 0.055, 0.06, 0.0, -0.025)], body, 6))
    skull = lm.loft([(1.42, 0.05, 0.055, 0.0, -0.01), (1.52, 0.09, 0.1, 0.0, -0.01), (1.62, 0.106, 0.118),
                     (1.7, 0.1, 0.112), (1.76, 0.06, 0.07)], head, 6, caps=(None, crown))
    skull += lm.quad((-0.07, 1.82, 0.03), (0.07, 1.82, 0.03), (0.07, 1.72, 0.03), (-0.07, 1.72, 0.03), tuft)
    # Голова завалена на плечо и вперёд.
    m.part("head", (0.0, 1.46, 0.0), _turn(skull, (0.0, 1.46, 0.0), rx=-9.0, rz=15.0), "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.04, 0.045, -0.225, 0.0), (1.08, 0.045, 0.048, -0.22, 0.0), (1.4, 0.055, 0.06, -0.205, 0.0)],
                   arm, 4, math.pi / 4.0, caps=(chip, None)), "body")
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.04, 0.045, 0.225, 0.0), (1.08, 0.045, 0.048, 0.22, 0.0), (1.4, 0.055, 0.06, 0.205, 0.0)],
                   arm, 4, math.pi / 4.0, caps=(chip, None))
           + lm.quad((0.225, 0.85, -0.02), (0.225, 0.85, -0.72), (0.225, 0.73, -0.72), (0.225, 0.73, -0.02), spade),
           "body")
    return m


# --- Зомби-мясник ------------------------------------------------------------------------------

def zombies_captain():
    """Мясник: второй боец и главарь. Грузный лысый зомби в заляпанном кровью белом фартуке
    поверх майки, голые толстые руки, резиновые сапоги; в темени застрял тесак."""
    a = lm.Atlas(64, 64, 243)
    tank, tank_d = rgb("5E6660"), rgb("3C423E")
    # Торс 32×20: спереди нагрудник фартука с лямками, по бокам и сзади майка и голые плечи,
    # на поясе завязки.
    a.rect(0, 0, 32, 20, tank)
    a.rect(0, 0, 32, 4, ROT)  # голые плечи и загривок
    a.rect(0, 3, 32, 1, ROT_D)
    a.rect(5, 0, 3, 5, tank), a.rect(24, 0, 3, 5, tank)  # лямки майки
    for x in (3, 28):
        a.rect(x, 5, 1, 12, tank_d)
    a.rect(0, 9, 2, 1, tank_d), a.rect(30, 12, 2, 1, tank_d)
    a.rect(10, 3, 12, 17, BONE)  # нагрудник
    a.rect(10, 3, 12, 1, BONE_D)
    a.rect(10, 3, 1, 17, BONE_D), a.rect(21, 3, 1, 17, BONE_D)
    a.rect(11, 0, 1, 3, BONE_D), a.rect(20, 0, 1, 3, BONE_D)  # лямки фартука на шею
    a.rect(13, 0, 6, 2, ROT), a.rect(13, 2, 6, 1, ROT_D)  # шея в складках
    a.rect(14, 12, 5, 4, BONE_D)  # карман
    a.rect(14, 12, 5, 1, RAG_D)
    a.rect(17, 10, 1, 3, STEEL), a.px(17, 9, LEATHER_D)  # нож в кармане
    # Кровь: ладонь, брызги, потёки.
    a.rect(12, 6, 4, 3, BLOOD), a.px(11, 7, BLOOD), a.px(13, 9, BLOOD), a.px(15, 9, BLOOD), a.px(13, 10, BLOOD_D)
    a.rect(18, 5, 2, 2, BLOOD), a.px(19, 7, BLOOD_D), a.px(19, 8, BLOOD_D)
    a.rect(11, 15, 3, 3, BLOOD_D), a.px(12, 18, BLOOD_D), a.px(12, 16, BLOOD)
    a.rect(18, 16, 3, 2, BLOOD), a.px(19, 18, BLOOD_D), a.px(19, 19, BLOOD_D)
    _spots(a, 10, 4, 12, 15, BLOOD, 8)
    a.rect(0, 14, 10, 1, BONE_D), a.rect(22, 14, 10, 1, BONE_D)  # завязки вокруг пояса
    a.rect(0, 13, 2, 3, BONE), a.rect(30, 13, 2, 3, BONE)  # узел на спине
    a.rect(0, 18, 10, 2, RUBBER), a.rect(22, 18, 10, 2, RUBBER)  # штаны под майкой
    a.shade(0, 0, 32, 20, 1.1, 0.84, 0.72)
    a.noise(0, 0, 32, 20, 0.06)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×16, четыре полосы по 4 строки: лысое темя со швом, глаза под тяжёлым лбом,
    # пасть, подбородки.
    a.rect(0, 20, 32, 16, ROT)
    a.rect(0, 20, 32, 2, ROT_L)
    a.rect(16, 20, 2, 5, BLOOD_D)  # рана от тесака
    a.px(15, 22, BLOOD), a.px(18, 23, BLOOD), a.px(17, 25, BLOOD), a.px(17, 26, BLOOD_D)
    for x in (4, 6, 8):
        a.px(x, 22, BLACK), a.px(x, 23, ROT_D)  # шов на виске
    a.rect(3, 23, 7, 1, ROT_D)
    a.rect(8, 24, 16, 2, ROT_D)  # надбровный валик
    a.rect(10, 26, 4, 2, LABEL), a.px(12, 26, BLACK), a.px(12, 27, BLACK)  # жёлтый глаз
    a.rect(18, 26, 4, 2, BONE), a.px(19, 26, BLACK)  # бельмо
    a.rect(10, 28, 4, 1, ROT_D), a.rect(18, 28, 4, 1, ROT_D)  # мешки под глазами
    a.rect(15, 27, 2, 3, ROT_D), a.px(14, 29, BLACK), a.px(17, 29, BLACK)  # приплюснутый нос
    a.rect(10, 31, 12, 2, BLACK)  # широкая пасть
    for x in (11, 13, 16, 18, 20):
        a.px(x, 31, BONE)
    for x in (12, 15, 19):
        a.px(x, 32, BONE_D)
    a.rect(20, 32, 2, 2, BLOOD), a.px(21, 34, BLOOD_D)
    a.rect(6, 29, 2, 4, ROT_D), a.rect(24, 29, 2, 4, ROT_D)  # обвисшие щёки
    a.rect(7, 26, 1, 3, ROT_D), a.rect(24, 26, 1, 3, ROT_D)  # уши
    a.rect(0, 33, 32, 1, ROT_D), a.rect(0, 35, 32, 1, ROT_D)  # складки подбородков и загривка
    a.rect(0, 27, 4, 1, ROT_D), a.rect(28, 27, 4, 1, ROT_D)  # складка на затылке
    _spots(a, 0, 22, 32, 12, ROT_D, 9)
    a.shade(0, 20, 32, 16, 1.1, 0.86, 0.8)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16: голое плечо с наколкой, предплечье в крови, резиновая перчатка до запястья.
    a.rect(32, 0, 16, 16, ROT)
    a.rect(32, 0, 16, 1, tank), a.rect(32, 1, 16, 1, ROT_L)
    a.rect(38, 3, 4, 1, ROT_D), a.rect(39, 2, 2, 4, ROT_D), a.px(39, 3, BLOOD_D), a.px(40, 4, BLOOD_D)  # наколка
    a.rect(32, 7, 16, 1, ROT_D)  # локоть
    a.rect(44, 4, 1, 6, ROT_D)
    a.rect(34, 9, 3, 2, BLOOD), a.px(35, 11, BLOOD_D), a.px(42, 10, BLOOD)
    a.rect(32, 11, 16, 5, rgb("C8B24A"))  # жёлтая перчатка
    a.rect(32, 11, 16, 1, rgb("E4D070"))
    a.rect(32, 13, 16, 3, BLOOD)
    a.rect(32, 15, 16, 1, BLOOD_D)
    for x in (35, 39, 43):
        a.px(x, 14, BLOOD_D)
    a.px(37, 12, BLOOD), a.px(45, 12, BLOOD)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.06)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: тёмные штаны, высокий резиновый сапог с отворотом и бликом, брызги крови.
    a.rect(48, 0, 16, 12, rgb("3A3C44"))
    a.rect(55, 0, 1, 12, rgb("24262C"))
    a.rect(51, 5, 3, 1, rgb("24262C")), a.rect(58, 8, 3, 1, rgb("24262C"))
    a.rect(48, 12, 16, 12, RUBBER)
    a.rect(48, 12, 16, 2, tank)  # отворот сапога
    a.rect(48, 13, 16, 1, tank_d)
    a.rect(53, 15, 1, 6, tank_d)  # блик по голенищу
    a.rect(48, 22, 16, 2, RUBBER_D)
    a.rect(54, 21, 5, 1, tank_d)
    a.px(58, 16, BLOOD), a.px(59, 17, BLOOD), a.px(51, 19, BLOOD_D), a.px(56, 10, BLOOD_D)
    a.shade(48, 0, 16, 24, 1.05, 0.86, 0.76)
    a.noise(48, 0, 16, 24, 0.06)
    leg = a.region(48, 0, 16, 24)
    # Подол фартука 24×20: три полотнища, складки, тёмная кромка, кровь густеет книзу.
    a.rect(0, 44, 24, 20, BONE)
    for x in (4, 11, 15, 20):
        a.rect(x, 45, 1, 18, BONE_D)
    a.rect(0, 44, 24, 1, RAG_D)  # пояс с завязкой
    a.rect(0, 45, 24, 1, BONE_D)
    for x0, y0, w, h in ((2, 49, 4, 3), (9, 47, 3, 2), (13, 53, 5, 4), (19, 50, 3, 3), (5, 57, 4, 3), (17, 59, 4, 2)):
        a.rect(x0, y0, w, h, BLOOD)
        a.rect(x0 + 1, y0 + h, 1, 2, BLOOD_D)
        a.px(x0, y0, BLOOD_D)
    for x in range(24):
        drop = (2, 3, 1, 4, 2, 1, 3)[(x * 5) % 7]
        a.rect(x, 64 - drop, 1, drop, BLOOD_D if drop > 1 else BLOOD)
    _spots(a, 0, 46, 24, 16, BLOOD, 12)
    a.rect(0, 44, 1, 20, BONE_D), a.rect(23, 44, 1, 20, BONE_D)
    a.shade(0, 44, 24, 20, 1.05, 0.82, 0.88)
    a.noise(0, 44, 24, 20, 0.06)
    # Тесак 12×8: широкий клинок с отверстием и кровью по лезвию, деревянная рукоять назад.
    a.rect(32, 17, 8, 7, STEEL)
    a.rect(32, 17, 8, 1, STEEL_L)
    a.rect(33, 18, 1, 5, STEEL_L)
    a.clear(38, 18)
    a.rect(32, 21, 8, 1, BLOOD), a.rect(32, 22, 8, 2, BLOOD_D)
    a.px(34, 20, BLOOD), a.px(37, 20, BLOOD)
    a.rect(40, 17, 4, 2, LEATHER), a.rect(40, 17, 4, 1, LEATHER_L)
    a.px(41, 18, STEEL_L), a.px(43, 18, STEEL_L)  # заклёпки
    cleaver = a.region(32, 16, 12, 8)
    a.rect(44, 16, 4, 4, RUBBER_D)
    a.rect(44, 20, 4, 4, ROT_L)
    a.px(45, 21, BLOOD_D), a.px(46, 22, BLOOD_D)
    sole, crown = a.region(44, 16, 4, 4), a.region(44, 20, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown, 1.18)
    # Грузный корпус: брюхо вперёд, покатые плечи.
    parts["body"][1] = lm.loft([(0.82, 0.215, 0.16), (1.02, 0.25, 0.2, 0.0, -0.025), (1.27, 0.28, 0.17, 0.0, -0.01),
                                (1.42, 0.285, 0.13), (1.47, 0.08, 0.08)], torso, 6)
    # Голова крупная, лысая, с тяжёлой челюстью; шея толстая.
    parts["head"][1] = lm.loft([(1.44, 0.085, 0.09), (1.52, 0.125, 0.13, 0.0, -0.005), (1.63, 0.128, 0.138),
                                (1.73, 0.115, 0.125), (1.79, 0.06, 0.07)], head, 6, caps=(None, crown))
    # Тесак в темени: клинок наискось, рукоять торчит назад и вверх.
    parts["head"][1].extend(lm.quad((-0.05, 1.93, -0.1), (0.07, 1.9, 0.15), (0.07, 1.72, 0.15), (-0.05, 1.75, -0.1),
                                    cleaver))
    # Подол фартука: три полотнища от брюха до колен, книзу шире и дальше от ног.
    apron = []
    top = [(-0.22, -0.12), (-0.09, -0.235), (0.09, -0.235), (0.22, -0.12)]
    low = [(-0.26, -0.13), (-0.11, -0.255), (0.11, -0.255), (0.26, -0.13)]
    for i in range(3):
        apron += lm.quad((top[i][0], 1.04, top[i][1]), (top[i + 1][0], 1.04, top[i + 1][1]),
                         (low[i + 1][0], 0.5, low[i + 1][1]), (low[i][0], 0.5, low[i][1]),
                         a.region(i * 8, 44, 8, 20))
    parts["body"][1].extend(apron)
    return lm.assemble("captain", a, parts)


MODELS = [zombies_hero, zombies_enemy, zombies_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
