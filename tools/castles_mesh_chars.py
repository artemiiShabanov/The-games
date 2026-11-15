#!/usr/bin/env python3
"""Персонажи «Замков» для low poly и «продвинутых»: рыцарь, стражник вражеского замка, чёрный
рыцарь. Зеркала `pirate_hero`, `pirate_enemy`, `pirate_captain` из `lowpoly_meshes.py` (так же,
как `space_mesh_chars.py`): те же имена частей, родители и точки вращения (демки анимируют части),
рост в человеческих пределах (не выше 1,93 м с плюмажем и рогами), взгляд в −Z, ноль в подошвах;
у стражника оружие в правой руке на месте сабли скелета. Плотный набор «продвинутых» получается
из этих же функций (плотность и размер атласа задаёт `lowpoly_meshes`), поэтому геометрия
собирается его помощниками.

    python3 tools/castles_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Сталь, красный герб, золото, воронёная сталь, кольчуга, кожа.
STEEL, STEEL_D, STEEL_L, STEEL_DD = rgb("A9B1BE"), rgb("626A7A"), rgb("DCE2EC"), rgb("3C4150")
RED, RED_D, RED_L = rgb("B02A2E"), rgb("6E1618"), rgb("DA4A4C")
GOLD, GOLD_D, GOLD_L = rgb("E0B040"), rgb("9A7020"), rgb("F6DC86")
RAV, RAV_D, RAV_L = rgb("2A2C38"), rgb("14151D"), rgb("505570")
MAIL, MAIL_D, MAIL_L = rgb("3C404E"), rgb("1B1C23"), rgb("626880")
CRIM, CRIM_D, CRIM_L = rgb("8E1F3A"), rgb("55101F"), rgb("B53656")
LEATHER, LEATHER_L, LEATHER_D = rgb("4A3222"), rgb("6C4A34"), rgb("2E1E16")
SKIN, SKIN_D = rgb("D9A27C"), rgb("A8704F")
HAIR = rgb("3A2A20")
BLACK = rgb("0E0D14")
BONE, BONE_D = rgb("D8D2BC"), rgb("8E8872")
WHITE = rgb("EEF0F4")
EMBER = rgb("D03048")


def _rivets(a, x, y, w, c, step=4):
    for i in range(x + 1, x + w, step):
        a.px(i, y, c)


def _mail(a, x, y, w, h, base=MAIL, light=MAIL_L, dark=MAIL_D):
    """Кольчуга: шахматка колец, тёмные просветы между рядами, редкие блики."""
    a.rect(x, y, w, h, dark)
    for j in range(h):
        for i in range(w):
            if (i + j) % 2 == 0:
                a.px(x + i, y + j, base)
            if i % 4 == 0 and j % 4 == 0:
                a.px(x + i, y + j, light)
            elif (i + 2) % 4 == 0 and (j + 2) % 4 == 0:
                a.px(x + i, y + j, light)


def _skirt(region, k, top, bottom, zt, zb):
    """Подол табарда или туники: два полотнища спереди и сзади, книзу шире."""
    wt, wb = 0.15 * k, 0.17 * k
    front = lm.quad((-wt, top, -zt), (wt, top, -zt), (wb, bottom, -zb), (-wb, bottom, -zb), region)
    back = lm.quad((wt, top, zt), (-wt, top, zt), (-wb, bottom, zb), (wb, bottom, zb), region)
    return front + back


def _pauldron(region, cap, x, k, peak=0.0, n=5):
    """Наплечник: купол на плече, заходит на тело, шарнир тот же, что у руки. `peak` больше нуля
    заостряет верх в шип (у чёрного рыцаря)."""
    top = (1.46 + peak, 0.06 * k * (1.0 - min(peak * 12.0, 1.0)) + 0.002, 0.065 * k * (1.0 - min(peak * 12.0, 1.0)) + 0.002)
    return lm.loft([(1.3, 0.08 * k, 0.085 * k, x, 0.0), (1.385, 0.105 * k, 0.11 * k, x, 0.0),
                    (top[0], top[1], top[2], x, 0.0)], region, n, caps=(None, cap if peak <= 0.0 else None))


# --- Рыцарь ------------------------------------------------------------------------------------

def castle_hero():
    """Рыцарь: стальные латы со швами и заклёпками, шлем с тёмной прорезью-забралом и красным
    плюмажем, красный табард с золотым поясом и гербом на груди, латные перчатки и сапоги."""
    a = lm.Atlas(64, 64, 211)
    # Торс 32×20: середина куска это грудь. Горжет сверху, красный табард спереди и сзади,
    # стальные пластины на боках, герб-щит с золотым крестом, золотой пояс с пряжкой.
    a.rect(0, 0, 32, 20, STEEL)
    for x0, w in ((0, 4), (9, 14), (28, 4)):
        a.rect(x0, 3, w, 14, RED)
    for x in (11, 20):
        a.rect(x, 12, 1, 5, RED_D), a.rect(x + 1, 12, 1, 5, RED_L)  # складки ниже герба
    a.rect(9, 3, 1, 14, RED_D), a.rect(22, 3, 1, 14, RED_D)  # кромка табарда
    a.rect(2, 3, 1, 14, RED_D), a.rect(29, 3, 1, 14, RED_D)
    for x0 in (4, 23):
        for y in (6, 10, 14):
            a.rect(x0, y, 5, 1, STEEL_D)  # пластины боков
            a.px(x0 + 1, y - 1, STEEL_L), a.px(x0 + 3, y - 1, STEEL_L)
    # Герб: щит с золотой каймой, багровым полем и крестом.
    a.rect(12, 4, 8, 6, GOLD)
    a.rect(13, 5, 6, 5, RED_D)
    for y, x0, w in ((10, 12, 8), (11, 13, 6), (12, 14, 4), (13, 15, 2)):
        a.rect(x0, y, w, 1, GOLD)
    a.rect(13, 10, 6, 1, RED_D), a.rect(14, 11, 4, 1, RED_D), a.rect(15, 12, 2, 1, RED_D)
    a.rect(15, 5, 2, 7, GOLD_L), a.rect(13, 7, 6, 2, GOLD_L)
    a.rect(15, 11, 2, 1, GOLD_D)
    a.px(15, 7, GOLD), a.px(16, 8, GOLD_D)
    # Горжет (ворот и плечи): две пластины и заклёпки.
    a.rect(0, 0, 32, 3, STEEL_L)
    a.rect(0, 2, 32, 1, STEEL_D)
    _rivets(a, 0, 1, 32, STEEL_DD, 3)
    # Пояс: золотая лента, пряжка со щитком, заклёпки.
    a.rect(0, 17, 32, 3, GOLD)
    a.rect(0, 17, 32, 1, GOLD_L)
    a.rect(0, 19, 32, 1, GOLD_D)
    _rivets(a, 0, 18, 32, GOLD_D, 3)
    a.rect(13, 17, 6, 3, STEEL_L), a.rect(14, 18, 4, 1, STEEL_DD), a.rect(14, 17, 4, 1, STEEL)
    a.shade(0, 0, 32, 20, 1.08, 0.84, 0.72)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Шлем 32×16: купол с гребнем, брови, тёмная прорезь-забрало (в ней проблеск глаз),
    # лицевая планка с отверстиями, шов на затылке, заклёпки и горжет у шеи.
    a.rect(0, 20, 32, 16, STEEL)
    a.rect(0, 20, 32, 2, STEEL_L)
    a.rect(14, 20, 4, 7, STEEL_D), a.rect(15, 20, 2, 7, STEEL_L)  # гребень
    for y in (23, 25):
        a.rect(0, y, 14, 1, STEEL_D), a.rect(18, y, 14, 1, STEEL_D)  # пояса купола
    a.rect(7, 26, 18, 1, STEEL_DD)
    a.rect(8, 27, 16, 3, BLACK)  # прорезь
    a.rect(7, 30, 18, 1, STEEL_DD)
    a.px(12, 28, rgb("8CA2C8")), a.px(19, 28, rgb("8CA2C8"))
    a.rect(15, 30, 2, 4, STEEL_D)  # планка вниз от прорези
    for x in (10, 12, 19, 21):
        for y in (31, 33):
            a.px(x, y, BLACK)  # отверстия для дыхания
    for x, y in ((6, 24), (25, 24), (8, 31), (23, 31)):
        a.px(x, y, STEEL_L)  # заклёпки
    for x in (0, 1, 30, 31):
        a.rect(x, 22, 1, 10, STEEL_D)  # шов на затылке
    a.rect(0, 33, 32, 3, STEEL_D)  # горжет под шлемом
    a.rect(0, 33, 32, 1, STEEL)
    _rivets(a, 0, 34, 32, STEEL_L, 3)
    a.shade(0, 20, 32, 16, 1.1, 0.88, 0.76)
    a.noise(0, 20, 32, 16, 0.04)
    helmet = a.region(0, 20, 32, 16)
    # Рука 16×16: наплечье, налокотник-«чашка», наруч, латная перчатка с пальцами.
    a.rect(32, 0, 16, 16, STEEL)
    a.rect(32, 4, 16, 1, STEEL_D), a.rect(32, 5, 16, 1, STEEL_L)
    a.rect(32, 6, 16, 4, STEEL_L), a.rect(32, 9, 16, 1, STEEL_D)  # налокотник
    for x in (34, 40, 46):
        a.px(x, 7, STEEL_DD)
    a.rect(32, 11, 16, 1, GOLD_D)  # край наруча
    a.rect(32, 12, 16, 4, STEEL_D)
    a.rect(32, 12, 16, 1, STEEL)
    for x in (34, 37, 40, 43, 46):
        a.px(x, 14, STEEL_DD), a.px(x, 15, STEEL_DD)  # пальцы
    a.rect(32, 13, 16, 1, STEEL_L)
    a.shade(32, 0, 16, 16, 1.06, 0.88, 0.74)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: набедренник из полос, наколенник, поножа с гребнем, сапог с ремнём.
    a.rect(48, 0, 16, 24, STEEL)
    for y in (3, 6):
        a.rect(48, y, 16, 1, STEEL_D)
    a.rect(55, 0, 2, 9, STEEL_D)
    a.rect(51, 9, 10, 4, STEEL_L), a.rect(52, 12, 8, 1, STEEL_D)  # наколенник
    a.px(55, 10, GOLD), a.px(56, 10, GOLD_D)
    a.rect(55, 13, 2, 5, STEEL_L)  # гребень поножи
    a.rect(48, 18, 16, 6, STEEL_D)  # сапог
    a.rect(48, 18, 16, 1, STEEL_L)
    a.rect(48, 20, 16, 1, LEATHER)
    a.rect(54, 20, 4, 1, GOLD)
    _rivets(a, 48, 15, 16, STEEL_DD, 4)
    a.shade(48, 0, 16, 24, 1.06, 0.85, 0.74)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Плюмаж 16×12: красные пряди по диагонали, тёмные прожилки, рваный хвост.
    a.rect(32, 16, 16, 12, RED)
    for y in range(12):
        for x in range(16):
            s = (x + y * 2) % 5
            if s == 0:
                a.px(32 + x, 16 + y, RED_D)
            elif s == 2:
                a.px(32 + x, 16 + y, RED_L)
    a.rect(32, 16, 16, 1, RED_L)
    a.shade(32, 16, 16, 12, 1.05, 0.82, 0.9)
    for y in range(7, 12):
        a.clear(48 - (y - 6) * 2, 16 + y, (y - 6) * 2, 1)
    a.clear(32, 27), a.clear(34, 27), a.clear(37, 27), a.clear(41, 27)
    plume = a.region(32, 16, 16, 12)
    # Подошва, темя, наплечник 16×10 с золотой каймой, подол табарда 24×14.
    a.rect(32, 28, 4, 4, STEEL_L)
    a.rect(36, 28, 4, 4, STEEL_DD)
    crown, sole = a.region(32, 28, 4, 4), a.region(36, 28, 4, 4)
    a.rect(48, 24, 16, 10, STEEL)
    for y in (3, 6):
        a.rect(48, y, 16, 1, STEEL_D)
        a.rect(48, y + 1, 16, 1, STEEL_L)
    a.rect(48, 9, 16, 1, GOLD)
    _rivets(a, 48, 1, 16, STEEL_DD, 3)
    a.noise(48, 24, 16, 10, 0.05)
    shoulder = a.region(48, 24, 16, 10)
    a.rect(0, 36, 24, 14, RED)
    for x in (3, 8, 13, 18):
        a.rect(x, 36, 1, 11, RED_D), a.rect(x + 1, 37, 1, 9, RED_L)
    a.rect(0, 47, 24, 3, GOLD), a.rect(0, 47, 24, 1, GOLD_L), a.rect(0, 49, 24, 1, GOLD_D)
    a.shade(0, 36, 24, 14, 1.04, 0.82, 0.85)
    a.noise(0, 36, 24, 14, 0.05)
    skirt = a.region(0, 36, 24, 14)

    parts = lm.biped(leg, torso, helmet, arm, sole, crown)
    # Шлем вместо головы: купол шире шеи, тёмная прорезь на уровне глаз.
    parts["head"][1] = lm.loft([(1.44, 0.065, 0.07), (1.52, 0.105, 0.115), (1.62, 0.125, 0.13), (1.71, 0.125, 0.13),
                                (1.78, 0.09, 0.095), (1.82, 0.035, 0.04)], helmet, 6, caps=(None, crown))
    # Плюмаж: две плоскости гребнем от лба к затылку, у основания в куполе.
    for dx in (-0.02, 0.02):
        parts["head"][1].extend(lm.quad((dx, 1.92, -0.09), (dx, 1.91, 0.12), (dx, 1.68, 0.24), (dx, 1.78, -0.1), plume))
    for side, x in (("l", -0.255), ("r", 0.255)):
        parts["arm_" + side][1].extend(_pauldron(shoulder, crown, x, 1.0))
    parts["body"][1].extend(_skirt(skirt, 1.0, 0.9, 0.58, 0.125, 0.15))
    return lm.assemble("hero", a, parts)


# --- Стражник вражеского замка -----------------------------------------------------------------

def castle_enemy():
    """Стражник вражеского замка: чёрная кольчуга с мелкими кольцами, багровая туника с поясом,
    шлем-котелок с широкими полями, лицо с усами, в правой руке топор на месте сабли скелета."""
    a = lm.Atlas(64, 64, 223)
    # Тело 32×20: кольчужные бока и ворот, багровая туника спереди и сзади, ремень с пряжкой.
    _mail(a, 0, 0, 32, 20)
    for x0, w in ((0, 3), (8, 16), (29, 3)):
        a.rect(x0, 4, w, 13, CRIM)
    for x in (10, 14, 18, 21):
        a.rect(x, 5, 1, 12, CRIM_D), a.rect(x + 1, 6, 1, 10, CRIM_L)  # складки
    a.rect(8, 4, 1, 13, CRIM_D), a.rect(23, 4, 1, 13, CRIM_D)
    a.rect(14, 4, 4, 1, CRIM_D)  # вырез у ворота
    a.rect(0, 0, 32, 4, MAIL)  # кольчужный воротник
    _mail(a, 0, 0, 32, 4, MAIL, MAIL_L, MAIL_D)
    a.rect(0, 3, 32, 1, MAIL_D)
    a.rect(0, 17, 32, 3, LEATHER)
    a.rect(0, 17, 32, 1, LEATHER_L)
    a.rect(13, 17, 6, 3, STEEL_D), a.rect(14, 18, 4, 1, LEATHER_D), a.rect(13, 17, 6, 1, STEEL)
    for x in range(1, 32, 4):
        a.px(x, 19, LEATHER_D)
    # Нашитый знак на груди: чёрный ворон-клин на багровом.
    a.rect(14, 8, 4, 1, BLACK), a.rect(15, 9, 2, 3, BLACK), a.px(13, 7, BLACK), a.px(18, 7, BLACK)
    a.px(15, 8, CRIM_L)
    a.shade(0, 0, 32, 20, 1.1, 0.84, 0.72)
    a.noise(0, 0, 32, 20, 0.06)
    body = a.region(0, 0, 32, 20)
    # Голова 32×16: лицо под полями, кольчужный капюшон с боков и на шее.
    a.rect(0, 20, 32, 16, SKIN)
    _mail(a, 0, 20, 8, 16), _mail(a, 24, 20, 8, 16)
    _mail(a, 0, 33, 32, 3)
    a.rect(0, 20, 32, 3, SKIN_D)  # тень от полей
    a.rect(8, 20, 1, 13, SKIN_D), a.rect(23, 20, 1, 13, SKIN_D)
    a.rect(10, 24, 4, 1, HAIR), a.rect(18, 24, 4, 1, HAIR)  # брови
    a.px(11, 25, WHITE), a.px(12, 25, BLACK), a.px(19, 25, WHITE), a.px(20, 25, BLACK)
    a.px(11, 26, SKIN_D), a.px(20, 26, SKIN_D)
    a.rect(15, 25, 2, 4, mul(SKIN, 0.88)), a.px(15, 28, SKIN_D), a.px(16, 28, SKIN_D)
    a.rect(11, 29, 10, 2, HAIR), a.rect(14, 29, 4, 1, mul(HAIR, 1.4))  # усы
    a.rect(14, 31, 4, 1, RED_D)
    for _ in range(18):
        a.px(a.rng.randrange(10, 22), a.rng.randrange(31, 34), mul(SKIN, 0.78))
    a.shade(0, 20, 32, 16, 1.06, 0.9, 0.8)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16: багровый рукав до локтя, кольчуга, кожаная перчатка.
    _mail(a, 32, 0, 16, 16)
    a.rect(32, 0, 16, 5, CRIM)
    a.rect(32, 3, 16, 1, CRIM_D), a.rect(32, 4, 16, 1, CRIM_L)
    a.rect(32, 12, 16, 4, LEATHER)
    a.rect(32, 12, 16, 1, LEATHER_L), a.rect(32, 15, 16, 1, LEATHER_D)
    for x in (35, 39, 43):
        a.px(x, 14, LEATHER_D)
    a.shade(32, 0, 16, 16, 1.05, 0.88, 0.74)
    a.noise(32, 0, 16, 16, 0.06)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: кольчужные штаны, кожаный сапог с ремнём и пряжкой.
    _mail(a, 48, 0, 16, 24)
    a.rect(48, 0, 16, 3, CRIM_D)
    a.rect(55, 0, 1, 12, MAIL_D)
    a.rect(48, 12, 16, 12, LEATHER)
    a.rect(48, 12, 16, 1, LEATHER_L)
    a.rect(48, 16, 16, 1, LEATHER_D)
    a.rect(54, 14, 4, 1, STEEL_D), a.px(55, 14, STEEL_L)
    a.rect(48, 21, 16, 3, LEATHER_D)
    a.shade(48, 0, 16, 24, 1.05, 0.85, 0.74)
    a.noise(48, 0, 16, 24, 0.06)
    leg = a.region(48, 0, 16, 24)
    # Котелок 16×8: чугунный купол с шарниром шва и заклёпками; поля 8×8.
    a.rect(32, 16, 16, 8, STEEL_D)
    a.rect(32, 16, 16, 2, STEEL)
    a.rect(32, 22, 16, 2, STEEL_DD)
    a.rect(39, 16, 2, 6, STEEL), a.rect(39, 16, 1, 6, STEEL_L)
    _rivets(a, 32, 21, 16, STEEL_L, 3)
    a.noise(32, 16, 16, 8, 0.07)
    pot = a.region(32, 16, 16, 8)
    a.rect(48, 24, 8, 8, STEEL_D)
    a.rect(48, 24, 8, 1, STEEL), a.rect(48, 31, 8, 1, STEEL_DD)
    a.rect(48, 24, 1, 8, STEEL), a.rect(55, 24, 1, 8, STEEL_DD)
    a.px(51, 27, STEEL_L), a.px(52, 28, STEEL_DD)
    a.noise(48, 24, 8, 8, 0.07)
    brim = a.region(48, 24, 8, 8)
    # Топор: древко 16×4 с кожаной обмоткой и лезвие 16×8 с прозрачным вырезом полумесяцем.
    a.rect(32, 24, 16, 4, LEATHER_L)
    a.rect(32, 24, 16, 1, rgb("8A6446")), a.rect(32, 27, 16, 1, LEATHER_D)
    for x in range(34, 48, 4):
        a.rect(x, 24, 1, 4, LEATHER_D)
    a.rect(32, 24, 3, 4, STEEL_D)  # торец
    haft = a.region(32, 24, 16, 4)
    a.rect(32, 28, 16, 8, STEEL)
    a.rect(32, 28, 16, 1, STEEL_L)
    a.rect(32, 35, 16, 1, STEEL_D)
    a.rect(32, 28, 5, 8, STEEL_D)  # втулка у древка
    a.rect(34, 30, 1, 4, STEEL_L)
    for y in range(28, 36):
        cut = int(7 - abs(y - 31.5) * 1.2)  # полумесяц: на кромке выбрано
        a.clear(48 - max(cut, 0), y, max(cut, 0), 1)
    a.rect(37, 30, 8, 1, STEEL_L)  # блик на лезвии
    for y in range(28, 36):
        a.px(44 - int(abs(y - 31.5) * 1.1), y, STEEL_L)
    axe = a.region(32, 28, 16, 8)
    a.rect(56, 24, 4, 4, STEEL_D)
    a.rect(60, 24, 4, 4, STEEL)
    chip, crown = a.region(56, 24, 4, 4), a.region(60, 24, 4, 4)
    a.rect(0, 36, 24, 14, CRIM)
    for x in (3, 8, 13, 18):
        a.rect(x, 36, 1, 11, CRIM_D), a.rect(x + 1, 37, 1, 9, CRIM_L)
    a.rect(0, 47, 24, 3, CRIM_D), a.rect(0, 47, 24, 1, BLACK)
    a.shade(0, 36, 24, 14, 1.04, 0.82, 0.85)
    a.noise(0, 36, 24, 14, 0.06)
    skirt = a.region(0, 36, 24, 14)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.065, 0.12, x, -0.04), (0.08, 0.065, 0.075, x, -0.005), (0.46, 0.07, 0.075, x, 0.0),
                        (0.88, 0.095, 0.1, x, 0.0)], leg, 4, math.pi / 4.0, caps=(chip, None)))
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.84, 0.17, 0.115), (1.0, 0.155, 0.1), (1.27, 0.205, 0.13), (1.42, 0.17, 0.105), (1.47, 0.06, 0.06)],
                   body, 6) + _skirt(skirt, 1.0, 0.9, 0.58, 0.125, 0.15))
    helmet = lm.loft([(1.44, 0.06, 0.065), (1.52, 0.1, 0.105), (1.62, 0.11, 0.12), (1.68, 0.1, 0.11)], head, 6)
    helmet += lm.loft([(1.65, 0.125, 0.13), (1.73, 0.125, 0.13), (1.8, 0.085, 0.09), (1.84, 0.03, 0.03)], pot, 6,
                      caps=(None, crown))
    helmet += lm.loft([(1.655, 0.2, 0.2), (1.675, 0.2, 0.2)], brim, 8, math.pi / 8.0, caps=(brim, brim), flat=True)
    m.part("head", (0.0, 1.46, 0.0), helmet, "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.045, 0.045, -0.22, 0.0), (1.08, 0.05, 0.05, -0.215, 0.0), (1.4, 0.065, 0.065, -0.2, 0.0)],
                   arm, 4, math.pi / 4.0, caps=(chip, None)), "body")
    # Топор в правой руке на месте сабли: древко крестом из двух плоскостей, лезвие впереди.
    axe_tris = (lm.quad((0.22, 0.85, 0.05), (0.22, 0.85, -0.58), (0.22, 0.79, -0.58), (0.22, 0.79, 0.05), haft)
                + lm.quad((0.19, 0.82, 0.05), (0.25, 0.82, 0.05), (0.25, 0.82, -0.58), (0.19, 0.82, -0.58), haft)
                + lm.quad((0.22, 1.0, -0.62), (0.22, 1.0, -0.36), (0.22, 0.64, -0.36), (0.22, 0.64, -0.62), axe))
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.045, 0.045, 0.22, 0.0), (1.08, 0.05, 0.05, 0.215, 0.0), (1.4, 0.065, 0.065, 0.2, 0.0)],
                   arm, 4, math.pi / 4.0, caps=(chip, None)) + axe_tris, "body")
    return m


# --- Чёрный рыцарь -----------------------------------------------------------------------------

def castle_captain():
    """Чёрный рыцарь: второй боец и главарь. Вороновые латы с золотой окантовкой, рогатый шлем
    с красным огнём в прорези, наплечники с шипами, за спиной багровый плащ до колен."""
    a = lm.Atlas(64, 64, 233)
    cloak_c, cloak_d, cloak_l = rgb("8A1632"), rgb("4A0C1C"), rgb("B02C4C")
    # Торс 32×20: нагрудник с гребнем и золотыми кромками, горжет, красный камень на груди,
    # пояс с золотой пряжкой.
    a.rect(0, 0, 32, 17, RAV)
    a.rect(15, 3, 2, 13, RAV_L), a.rect(14, 3, 1, 13, RAV_D), a.rect(17, 3, 1, 13, RAV_D)  # гребень
    a.rect(9, 3, 1, 13, GOLD), a.rect(22, 3, 1, 13, GOLD)  # окантовка нагрудника
    for y in (12, 14):
        a.rect(10, y, 12, 1, RAV_D), a.rect(10, y + 1, 12, 1, RAV_L)
    a.rect(10, 16, 12, 1, GOLD_D)
    a.rect(14, 6, 4, 4, GOLD), a.rect(15, 7, 2, 2, EMBER)
    a.px(14, 6, GOLD_L), a.px(17, 9, GOLD_D)
    for x0 in (3, 24):
        for y in (6, 10, 14):
            a.rect(x0, y, 5, 1, RAV_D), a.px(x0 + 1, y - 1, RAV_L), a.px(x0 + 3, y - 1, RAV_L)  # бока
    for x, y in ((11, 5), (20, 5), (11, 9), (20, 9)):
        a.px(x, y, GOLD)
    a.rect(0, 0, 32, 3, RAV_L)  # горжет
    a.rect(0, 2, 32, 1, GOLD)
    _rivets(a, 0, 1, 32, RAV_D, 3)
    a.rect(0, 17, 32, 3, RAV_D)
    a.rect(0, 17, 32, 1, GOLD)
    a.rect(0, 19, 32, 1, GOLD_D)
    a.rect(13, 17, 6, 3, GOLD), a.rect(14, 18, 4, 1, RAV_D), a.rect(13, 17, 6, 1, GOLD_L)
    a.shade(0, 0, 32, 20, 1.14, 0.8, 0.7)
    a.noise(0, 0, 32, 20, 0.06)
    torso = a.region(0, 0, 32, 20)
    # Шлем 32×24 (шире, чем у героя, голова 1,44-1,84): прорезь с красным огнём, золотой обод,
    # гребень, гнёзда рогов на висках, лицевая планка с отверстиями, горжет.
    a.rect(0, 20, 32, 24, RAV)
    a.rect(0, 20, 32, 3, RAV_L)
    a.rect(14, 20, 4, 11, RAV_D), a.rect(15, 20, 2, 11, GOLD), a.rect(15, 22, 2, 1, GOLD_D)  # гребень
    for y in (25, 28):
        a.rect(0, y, 14, 1, RAV_D), a.rect(18, y, 14, 1, RAV_D)
    a.rect(6, 30, 20, 1, GOLD)  # обод над прорезью
    a.rect(7, 31, 18, 1, RAV_D)
    a.rect(8, 32, 16, 4, BLACK)  # прорезь
    a.rect(7, 36, 18, 1, RAV_D), a.rect(6, 37, 20, 1, GOLD_D)
    a.rect(10, 33, 3, 2, EMBER), a.px(11, 33, rgb("FF8A6A"))
    a.rect(19, 33, 3, 2, EMBER), a.px(20, 33, rgb("FF8A6A"))
    a.rect(15, 37, 2, 5, RAV_L)
    for x in (10, 12, 19, 21):
        for y in (38, 40):
            a.px(x, y, BLACK)
    for x0 in (7, 23):
        a.rect(x0, 27, 3, 3, GOLD), a.px(x0 + 1, 28, GOLD_D), a.px(x0, 27, GOLD_L)  # гнёзда рогов
    for x in (0, 1, 30, 31):
        a.rect(x, 24, 1, 14, RAV_D)  # шов на затылке
    a.rect(0, 41, 32, 3, RAV_L)
    a.rect(0, 41, 32, 1, GOLD)
    _rivets(a, 0, 42, 32, RAV_D, 3)
    a.shade(0, 20, 32, 24, 1.12, 0.84, 0.74)
    a.noise(0, 20, 32, 24, 0.05)
    head = a.region(0, 20, 32, 24)
    # Рука 16×16: наплечье с золотой каймой, налокотник, наруч, перчатка.
    a.rect(32, 0, 16, 16, RAV)
    a.rect(32, 4, 16, 1, GOLD_D)
    a.rect(32, 6, 16, 3, RAV_L), a.rect(32, 9, 16, 1, GOLD)
    for x in (34, 40, 46):
        a.px(x, 7, GOLD)
    a.rect(32, 11, 16, 1, GOLD)
    a.rect(32, 12, 16, 4, RAV_D)
    a.rect(32, 13, 16, 1, RAV_L)
    for x in (34, 37, 40, 43, 46):
        a.px(x, 14, BLACK), a.px(x, 15, BLACK)
    a.shade(32, 0, 16, 16, 1.1, 0.82, 0.72)
    a.noise(32, 0, 16, 16, 0.06)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: набедренник, наколенник с золотым кольцом, поножа, сапог.
    a.rect(48, 0, 16, 24, RAV)
    for y in (3, 6):
        a.rect(48, y, 16, 1, RAV_D)
    a.rect(55, 0, 2, 9, RAV_D)
    a.rect(51, 9, 10, 4, RAV_L), a.rect(52, 12, 8, 1, GOLD_D)
    a.px(55, 10, GOLD), a.px(56, 10, GOLD), a.px(55, 11, GOLD_D)
    a.rect(55, 13, 2, 5, RAV_L)
    a.rect(48, 13, 16, 1, GOLD)
    a.rect(48, 18, 16, 6, RAV_D)
    a.rect(48, 18, 16, 1, GOLD)
    a.rect(54, 21, 4, 1, GOLD_D)
    a.shade(48, 0, 16, 24, 1.1, 0.82, 0.72)
    a.noise(48, 0, 16, 24, 0.06)
    leg = a.region(48, 0, 16, 24)
    # Плащ 24×20: складки, золотая кайма по краям и низу.
    a.rect(0, 44, 24, 20, cloak_c)
    for x in (3, 7, 12, 16, 20):
        a.rect(x, 46, 1, 16, cloak_d)
        a.rect(x + 1, 47, 1, 14, cloak_l)
    a.rect(0, 44, 24, 2, GOLD), a.rect(0, 45, 24, 1, GOLD_D)
    a.rect(0, 62, 24, 2, GOLD), a.rect(0, 62, 24, 1, GOLD_D)
    a.rect(0, 44, 1, 20, GOLD), a.rect(23, 44, 1, 20, GOLD)
    a.shade(0, 44, 24, 20, 1.05, 0.8, 0.85)
    a.noise(0, 44, 24, 20, 0.06)
    # Подошва, темя, рог 8×12, наплечник 16×10, подол 16×12.
    a.rect(32, 16, 4, 4, RAV_D)
    a.rect(36, 16, 4, 4, RAV_L)
    sole, crown = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4)
    a.rect(40, 16, 8, 12, BONE)
    for y in (2, 5, 8):
        a.rect(40, 16 + y, 8, 1, BONE_D)
    a.rect(40, 16, 8, 2, GOLD)  # золотой башмак рога
    a.rect(40, 25, 8, 3, RAV_D)  # потемневший кончик
    for x in range(40, 48, 3):
        a.rect(x, 18, 1, 7, mul(BONE, 1.08))
    a.noise(40, 16, 8, 12, 0.06)
    horn = a.region(40, 16, 8, 12)
    a.rect(48, 24, 16, 10, RAV)
    for y in (3, 6):
        a.rect(48, y + 24, 16, 1, RAV_D), a.rect(48, y + 25, 16, 1, RAV_L)
    a.rect(48, 33, 16, 1, GOLD)
    a.rect(48, 24, 16, 1, GOLD)
    _rivets(a, 48, 26, 16, GOLD, 3)
    a.noise(48, 24, 16, 10, 0.06)
    shoulder = a.region(48, 24, 16, 10)
    a.rect(24, 44, 16, 12, RAV)
    for x in (4, 8, 12):
        a.rect(24 + x, 44, 1, 9, RAV_D), a.rect(25 + x, 45, 1, 7, RAV_L)
    a.rect(24, 53, 16, 3, GOLD), a.rect(24, 53, 16, 1, GOLD_L), a.rect(24, 55, 16, 1, GOLD_D)
    a.shade(24, 44, 16, 12, 1.05, 0.82, 0.85)
    a.noise(24, 44, 16, 12, 0.06)
    skirt = a.region(24, 44, 16, 12)

    parts = lm.biped(leg, torso, head, arm, sole, crown, 1.18)
    # Шлем: прорезь на уровне глаз, купол шире лица.
    parts["head"][1] = lm.loft([(1.44, 0.065, 0.07), (1.52, 0.11, 0.12), (1.62, 0.13, 0.14), (1.72, 0.135, 0.14),
                                (1.79, 0.095, 0.1), (1.83, 0.035, 0.04)], head, 5, caps=(None, crown))
    # Рога: от висков наружу и вверх, кончики не выше 1,92.
    for s in (-1, 1):
        parts["head"][1].extend(lm.loft([(1.7, 0.034, 0.034, 0.13 * s, 0.0), (1.79, 0.026, 0.026, 0.185 * s, 0.0),
                                         (1.915, 0.004, 0.004, 0.235 * s, 0.0)], horn, 3))
    for side, x in (("l", -0.295), ("r", 0.295)):
        parts["arm_" + side][1].extend(_pauldron(shoulder, crown, x, 1.18, 0.09, 4))
    # Подол только спереди: сзади его закрывает плащ.
    parts["body"][1].extend(_skirt(skirt, 1.18, 0.9, 0.56, 0.15, 0.175)[:4])
    # Плащ: три полотнища от плеч до колен, книзу шире и дальше от спины.
    top = [(0.3, 0.2), (0.1, 0.215), (-0.1, 0.215), (-0.3, 0.2)]
    low = [(0.35, 0.28), (0.13, 0.32), (-0.13, 0.32), (-0.35, 0.28)]
    for i in range(3):
        parts["body"][1].extend(lm.quad((top[i][0], 1.42, top[i][1]), (top[i + 1][0], 1.42, top[i + 1][1]),
                                        (low[i + 1][0], 0.5, low[i + 1][1]), (low[i][0], 0.5, low[i][1]),
                                        a.region(i * 8, 44, 8, 20)))
    return lm.assemble("captain", a, parts)


MODELS = [castle_hero, castle_enemy, castle_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
