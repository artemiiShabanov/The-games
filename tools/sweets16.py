#!/usr/bin/env python3
"""Набор «Сладости» для 16/32-bit (основа, зеркало `space16.py` и `castles16.py`): карамельная
страна в пастели (розовый, мятный, кремовый), обводка и тени шоколадного коричневого. Герой это
пряничный человечек: плоская печенюшка с круглой головой, округлые руки и ноги без кистей и ступней,
белая глазурь волнистой каймой на запястьях и щиколотках, две пуговицы-драже на груди, глаза-точки,
улыбка и красный бантик-бабочка. Враг это мармеладный мишка, полупрозрачно-красный, с круглыми
ушами и бликами. Те же ленты, размеры и число кадров, что у космоса, пиратов и замков
(`castles16.sprites()`); позы героя повторяют рыцаря кадр в кадр, чтобы хитбоксы демок сходились:
меняется рисунок, не геометрия.

Слоты замков и их сладости: рыцарь это пряничный человечек, стражник это мармеладный мишка,
золотая монета это конфета в фантике, знамя это леденец-спираль на палочке (палочка по центру
кадра), окованный ларь это коробка с бантом, валун это кусок сахара-рафинада, кладка это бисквит
под розовой глазурью с потёками. Ленты, которых нет в `sprites()` (зефир с крылышками вместо
попугая-дрона, драже-жук вместо краба, ключ-леденцовая трость, банка конфет вместо аптечки, драже
как снаряд), лежат в `extras()` тех же размеров. Дали: пастельное небо с облаками сахарной ваты,
рожки мороженого и торт на горизонте, леденцы и деревья сахарной ваты.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `sweets_*16.py` берут цвета
по роли): K шоколадная обводка, NAVY тёмная мята, SEA мята, AQUA светлая мята, SKY небо и блики,
WHITE крем и глазурь, GREY розовая тень глазури, SKIN и TAN пряник и его тень, GOLD и BRASS
карамель, METAL розовый зефир и жвачка, DARK шоколад, RED леденцово-красный, VIOLET и PLUM виноград.

    python3 tools/sweets16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/sweets16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Сладости»: 16 цветов, индекс это та же роль, что у пиратов, космоса и замков.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x4A, 0x24, 0x22),  # K      шоколадная обводка
    (0x3F, 0x9C, 0x86),  # NAVY   тёмная мята, тень мяты
    (0x7C, 0xD8, 0xBA),  # SEA    мята
    (0xBE, 0xF2, 0xDC),  # AQUA   светлая мята, блик
    (0xCB, 0xE6, 0xFA),  # SKY    пастельное небо, блик
    (0xFF, 0xF6, 0xE6),  # WHITE  крем, глазурь
    (0xF6, 0xB0, 0xCB),  # GREY   розовая тень глазури, розовая глазурь
    (0xD9, 0x92, 0x52),  # SKIN   пряник
    (0xA3, 0x5E, 0x34),  # TAN    тень пряника, вафля
    (0xFF, 0xD6, 0x7E),  # GOLD   карамель, бисквит
    (0xD8, 0x92, 0x3C),  # BRASS  тень карамели
    (0xEA, 0x6F, 0x9D),  # METAL  розовая жвачка, зефир
    (0x6B, 0x3A, 0x28),  # DARK   шоколад
    (0xE8, 0x3C, 0x52),  # RED    леденцово-красный
    (0xB2, 0x66, 0xD0),  # VIOLET виноградный
    (0x70, 0x3E, 0x92),  # PLUM   тень винограда
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: RED, VIOLET: PLUM}
# Материалы для светотени рампами: тесто одно, глазурь одна, мята, карамель, жвачка, красное, виноград.
GROUPS = {WHITE: "icing", GREY: "icing", SKY: "icing", NAVY: "mint", SEA: "mint", AQUA: "mint",
          SKIN: "dough", TAN: "dough", GOLD: "caramel", BRASS: "caramel", METAL: "gum", DARK: "choco",
          RED: "red", VIOLET: "grape", PLUM: "grape"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Пряничный человечек -----------------------------------------------------------------------
# Силуэт как у рыцаря (те же позы и габариты), но рисунок свой: тело и голова это круглые
# блины теста, конечности толстые, с круглыми концами, концы в белой глазури с волнистой кромкой.

def _cuff(c, ex, ey, dx, dy, t):
    """Глазурь на конце конечности: белый конец и три капли волнистой кромки. (dx, dy) это
    направление конечности, (ex, ey) её конец."""
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    c.line(ex - dx * 1.6, ey - dy * 1.6, ex, ey, WHITE, t)
    px, py = -dy, dx
    for j in (-1, 0, 1):
        d = 3.0 if j == 0 else 2.2
        c.set(ex - dx * d + px * j * (t / 2.0 - 0.4), ey - dy * d + py * j * (t / 2.0 - 0.4), WHITE)


def _limb(c, x0, y0, x1, y1, col, t=3, cuff=True, edge=False):
    """Конечность: толстый отрезок с круглым концом и глазурью на конце, без кисти и ступни. С
    `edge` ближняя конечность обводится шоколадом, чтобы не сливаться с туловищем."""
    if edge:
        c.line(x0, y0, x1, y1, K, t + 2)
    c.line(x0, y0, x1, y1, col, t)
    if cuff:
        _cuff(c, x1, y1, x1 - x0, y1 - y0, t)


def _torso(c, x0, y0, x1, y1, buttons=True, face=1):
    """Круглое туловище-блин; две пуговицы-драже на груди ближе к переднему краю."""
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    c.ellipse(cx, cy, (x1 - x0) / 2.0 + 0.7, (y1 - y0) / 2.0 + 0.7, SKIN)
    if buttons:
        bx = x1 - 2 if face > 0 else x0 + 1
        h = y1 - y0
        c.rect(bx, y0 + h // 2 + 1, bx + 1, y0 + h // 2 + 2, RED)
        c.rect(bx, y0 + h // 2 + 4, bx + 1, y0 + h // 2 + 5, AQUA)


def _bow(c, x, y, w=4):
    """Красный бантик-бабочка: два треугольника и узелок."""
    c.poly([(x - w, y - 2), (x, y), (x - w, y + 3)], RED)
    c.poly([(x + w, y - 2), (x, y), (x + w, y + 3)], RED)
    c.rect(x - 1, y - 1, x + 1, y + 1, RED)


def _head(c, x, y, face=1):
    """Круглая голова лицом вправо при `face` 1: белые глаза-точки, улыбка, бантик под подбородком.
    Центр (x, y), нижний край y+5."""
    c.ellipse(x, y + 0.3, 5.6, 5.0, SKIN)
    f = face
    for dx in (0, 3):
        for dy in (-2, -1):
            c.set(x + (dx + (1 if f < 0 else 0)) * f, y + dy, WHITE)
            c.set(x + (dx + (1 if f > 0 else 0)) * f, y + dy, WHITE)
    for dx, dy in ((-1, 2), (0, 3), (1, 3), (2, 3), (3, 2)):
        c.set(x + dx * f, y + dy, K)
    _bow(c, x + 1 * f, y + 6, 3)


def gm_side(phase, jump=False):
    """Человечек сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _limb(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), TAN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], col, 4)
        _limb(c, knee[0], knee[1], foot[0], foot[1], col, 4, edge=sign > 0)
    _torso(c, 11, 12 - bob, 19, hip_y + 1)
    _limb(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), SKIN, edge=True)
    _head(c, 16, 7 - bob)
    return c.finish()


def gm_back(phase):
    """Со спины: бежит вглубь экрана, на спине волна белой глазури, крылья бантика по бокам шеи."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        _limb(c, 16 + sign * 3, 21 - bob, 16 + sign * 3, 29 - lift, SKIN if sign > 0 else TAN, 4)
        _limb(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, SKIN if sign > 0 else TAN, 3)
    c.ellipse(15.5, 17 - bob, 5.6, 5.8, SKIN)
    for x in range(12, 20):
        c.set(x, 18 - bob + ((x // 2) % 2) * 2, WHITE)
    c.ellipse(15.5, 7.3 - bob, 5.6, 5.0, SKIN)
    c.poly([(10, 11 - bob), (15, 13 - bob), (10, 15 - bob)], RED)
    c.poly([(21, 11 - bob), (16, 13 - bob), (21, 15 - bob)], RED)
    c.rect(14, 12 - bob, 17, 14 - bob, RED)
    return c.finish()


def gm_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _limb(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, TAN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], col, 4)
        _limb(c, knee[0], knee[1], foot[0], foot[1], col, 4)
    _torso(c, 11, 12 + crouch, 19, hip_y + 1)
    _limb(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, SKIN, edge=True)
    _head(c, 16, 7 + crouch)
    return c.finish()


def gm_idle(i):
    """Стойка: два кадра, человечек дышит. Руки чуть в стороны, как у печенья-фигурки."""
    c = Canvas()
    up = i
    for sign, col in ((-1, TAN), (1, SKIN)):
        _limb(c, 15 + sign * 2, 21, 15 + sign * 2, 29, col, 4)
    _limb(c, 11, 15 - up, 9, 21 - up, TAN)
    _torso(c, 11, 12 - up, 20, 22, face=1)
    _limb(c, 20, 15 - up, 22, 21 - up, SKIN)
    _head(c, 16, 7 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: овал от плеч (sx, sy) к бёдрам (hx, hy), ширина w, две пуговицы."""
    c.line(sx, sy, hx, hy, SKIN, w)
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k, col in ((0.3, RED), (0.65, AQUA)):
        x, y = sx + dx * n * k - dy * (w / 2 - 1), sy + dy * n * k + dx * (w / 2 - 1)
        c.rect(x - 1, y - 1, x, y, col)


def gm_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх,
    рука сзади на земле. Макушка головы на 15-й строке. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 26, 24, 22 - i, TAN, 3)
    _limb(c, 24, 22 - i, 27, 26, TAN, 3)
    _limb(c, 13, 24, 19, 23, TAN, 3, cuff=False)
    _lean(c, 12, 24, 19, 27, 6)
    _limb(c, 19, 28, 28, 28, SKIN, 4)
    _limb(c, 11, 25, 6, 29, SKIN, 3)
    _head(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, WHITE)
    return c


def gm_crouch(i):
    """Присед: та же фигура, сложенная вниз, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    _limb(c, 15, 24, 19, 26, TAN, 3, cuff=False)
    for sign, col in ((-1, TAN), (1, SKIN)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], col, 4)
        _limb(c, knee[0], knee[1], foot[0], foot[1], col, 3)
    _torso(c, 11, 22, 18, 27)
    _limb(c, 14, 24, 19, 26, SKIN, 3)
    _head(c, 16, 19)
    return c.finish()


def gm_hang(i):
    """На тросе: руки вверх к точке хвата, ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    _limb(c, 11, 14, 14, 3, TAN)
    _limb(c, 20, 14, 18, 3, SKIN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        _limb(c, 15.5 + sign * 2, 21, 15.5 + sign * 2 + sw * 2, 29, col, 3)
    _torso(c, 11, 13, 20, 22)
    _head(c, 16, 8)
    return c.finish()


# --- Мармеладный мишка -------------------------------------------------------------------------
# Враг: полупрозрачно-красный, круглые уши, блики; дальние части темнее (виноградная тень). Шаг и
# рост повторяют стражника.

def _ear(c, x, y):
    c.ellipse(x, y, 2.6, 2.6, RED)
    c.ellipse(x, y + 0.3, 1.3, 1.3, METAL)


def bear_side(phase):
    """Мишка сбоку, лицом влево (навстречу герою): шаг по фазе, блик на голове и пузе."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    _limb(c, 14, 15 - bob, 14 - 4 * s, 20 - bob, PLUM, 3, cuff=False)
    for sign, col in ((-1, PLUM), (1, RED)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        c.line(16, 22 - bob, 16 - 5 * a, 29 - lift, col, 5)
    c.ellipse(16.5, 18 - bob, 6.2, 5.8, RED)
    c.ellipse(13.5, 19 - bob, 2.8, 3.4, METAL)
    c.line(17, 14 - bob, 17 + 4 * s, 20 - bob, K, 5)
    c.line(17, 14 - bob, 17 + 4 * s, 20 - bob, RED, 3)
    _ear(c, 17, 3 - bob)
    _ear(c, 10, 3 - bob)
    c.ellipse(13, 8 - bob, 6.2, 5.2, K)
    c.ellipse(13, 8 - bob, 5.2, 4.2, RED)
    c.ellipse(8.5, 10 - bob, 2.8, 2.1, METAL)
    c.finish()
    c.set(6, 9 - bob, K)
    c.set(7, 9 - bob, K)
    c.rect(9, 6 - bob, 10, 8 - bob, K)
    c.set(10, 6 - bob, WHITE)
    c.set(11, 5 - bob, WHITE)
    c.set(13, 4 - bob, WHITE)
    c.set(14, 4 - bob, WHITE)
    c.set(15, 5 - bob, WHITE)
    c.set(13, 14 - bob, WHITE)
    c.set(12, 16 - bob, WHITE)
    c.set(12, 17 - bob, WHITE)
    return c


def bear_front(phase):
    """Мишка лицом к камере: идёт на игрока, ноги по очереди, блики на голове и пузе."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    _limb(c, 10, 16 - bob, 7, 21 - bob + s * 2, PLUM, 3, cuff=False)
    _limb(c, 21, 16 - bob, 24, 21 - bob - s * 2, RED, 3, cuff=False)
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        c.line(15.5 + sign * 3.5, 23 - bob, 15.5 + sign * 3.5, 29 - lift, RED if sign > 0 else PLUM, 4)
    c.ellipse(15.5, 19 - bob, 6.6, 6, RED)
    c.ellipse(15.5, 20 - bob, 3.6, 3.6, METAL)
    _ear(c, 9.5, 3 - bob)
    _ear(c, 21.5, 3 - bob)
    c.ellipse(15.5, 8 - bob, 6.8, 5.8, RED)
    c.ellipse(15.5, 11 - bob, 3.4, 2.4, METAL)
    c.finish()
    c.rect(14, 10 - bob, 17, 10 - bob, K)
    c.rect(11, 6 - bob, 11, 7 - bob, K)
    c.rect(20, 6 - bob, 20, 7 - bob, K)
    for p in ((11, 5), (12, 4), (14, 3), (8, 7), (9, 22), (10, 22)):
        c.set(p[0], p[1] - bob, WHITE)
    c.set(12, 6 - bob, WHITE)
    c.set(21, 6 - bob, WHITE)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Конфета в фантике вращается: шесть кадров, ширина по косинусу, концы фантика веером."""
    c = Canvas()
    k = max(0.22, abs(math.cos(math.pi * i / 6.0)))
    cx = 15.5
    for sgn in (-1, 1):
        x0 = cx + sgn * 5.0 * k
        x1 = cx + sgn * 12.0 * k
        c.poly([(x0, 13), (x1, 7), (x1, 25), (x0, 19)], AQUA)
        if k > 0.5:
            c.line(x1 - sgn * 1.5 * k, 9, x1 - sgn * 1.5 * k, 23, SEA, 1)
    c.ellipse(cx, 16, 6.0 * k, 7.5, METAL)
    if k > 0.4:
        c.rect(cx - 6.0 * k + 1, 15, cx + 6.0 * k - 1, 16, WHITE)
        c.set(cx - 2 * k, 11, WHITE)
        c.set(cx - 2 * k - 1, 12, WHITE)
    return c.finish()


def flag(i):
    """Леденец-спираль на палочке вместо полотнища: палочка по центру, диск красной и белой
    спирали вращается, бантик у основания диска. Шесть кадров, цикл замкнут."""
    c = Canvas()
    c.rect(15, 15, 16, 30, WHITE)
    c.ellipse(15.5, 11, 9.5, 9.5, WHITE)
    for y in range(32):
        for x in range(32):
            dx, dy = x - 15.5, y - 11
            r = math.hypot(dx, dy)
            if r <= 9.0:
                ang = math.atan2(dy, dx) + i * math.pi / 3.0
                v = (ang / (2 * math.pi) * 2 + r / 4.5) % 1.0
                c.set(x, y, RED if v < 0.5 else WHITE)
    c.shade()
    c.outline()
    c.poly([(15.5, 22), (11, 20), (11, 24)], METAL)
    c.poly([(15.5, 22), (20, 20), (20, 24)], METAL)
    c.rect(14, 21, 16, 23, METAL)
    c.finish()
    c.set(10, 7, WHITE)
    c.set(11, 6, WHITE)
    return c


def heart():
    """Жизнь в HUD: красное леденцовое сердце с белым бликом и точкой глазури."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    c.set(11, 8, WHITE)
    c.set(15, 22, WHITE)
    return c.finish()


def _sponge(c, from_y):
    """Бисквит: карамельный мякиш с крошками, прослойка шоколада и крема. Тайл 32×32."""
    c.rect(0, from_y, 31, 31, GOLD)
    for y in range(from_y, 32):
        for x in range(32):
            if (x * 7 + y * 13) % 17 == 0:
                c.set(x, y, BRASS)
    c.rect(0, 16, 31, 17, WHITE)
    c.rect(0, 18, 31, 19, DARK)
    c.rect(0, 15, 31, 15, GOLD)
    for x in range(0, 32, 4):
        c.set(x, 17, GREY)
    c.rect(0, 31, 31, 31, BRASS)


def ground(inner=False):
    """Бисквит с прослойкой; у кромки розовая глазурь с потёками сверху."""
    c = Canvas()
    _sponge(c, 0)
    if not inner:
        c.rect(0, 0, 31, 4, GREY)
        c.rect(0, 0, 31, 0, WHITE)
        # Потёки: низ глазури волной, местами капли длиннее, период 32 стыкуется по краям.
        for x in range(32):
            ln = int(round(2.2 + 1.6 * math.sin(x * math.pi * 2 / 32.0 * 2 + 0.5)
                           + 2.0 * max(0.0, math.sin(x * math.pi * 2 / 32.0 * 3 + 1.0)) ** 3))
            c.rect(x, 5, x, 5 + ln - 1, GREY)
            c.set(x, 5 + ln, METAL)
        for x in (4, 13, 21, 28):
            c.set(x, 2, WHITE)
        c.rect(0, 5, 31, 5, GREY)
    return c


def rock():
    """Кусок сахара-рафинада: куб в три грани с искрящимися крупинками."""
    c = Canvas()
    c.poly([(4, 13), (13, 7), (27, 9), (19, 15)], WHITE)
    c.poly([(4, 13), (19, 15), (19, 29), (4, 26)], SKY)
    c.poly([(19, 15), (27, 9), (28, 22), (19, 29)], GREY)
    c.line(4, 13, 19, 15, WHITE, 1)
    c.line(19, 15, 19, 29, SKY, 1)
    for x, y in ((8, 19), (12, 23), (15, 18), (6, 22), (23, 18), (24, 14), (21, 23), (14, 10), (20, 11)):
        c.set(x, y, WHITE)
    return c.finish()


def chest():
    """Подарочная коробка с бантом: розовый короб, мятная крышка, красная лента крест-накрест."""
    c = Canvas()
    c.rect(4, 14, 27, 28, METAL)
    c.rect(3, 10, 28, 15, AQUA)
    c.rect(14, 10, 17, 28, RED)
    c.rect(4, 20, 27, 21, RED)
    c.ellipse(11, 7, 5, 3.4, RED)
    c.ellipse(20, 7, 5, 3.4, RED)
    c.ellipse(11, 7, 2.2, 1.4, GREY)
    c.ellipse(20, 7, 2.2, 1.4, GREY)
    c.rect(14, 6, 17, 10, RED)
    for x, y in ((7, 12), (11, 12), (21, 12), (25, 12), (7, 25), (24, 25), (9, 17)):
        c.set(x, y, WHITE)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали. Высоты периодические (256 делится на период синусов), ленты стыкуются по краям.

def _wrap_ellipse(c, cx, cy, rx, ry, col):
    for k in (0, 256, -256):
        c.ellipse(cx + k, cy, rx, ry, col)


def _puff(c, cx, cy, w, col, hi, lo):
    """Облако сахарной ваты: гроздь шаров с бликом сверху и тенью снизу."""
    for dx, dy, r in ((0, 0, 0.5), (-0.32, 0.12, 0.34), (0.32, 0.1, 0.36), (-0.12, -0.12, 0.34), (0.15, -0.16, 0.3)):
        _wrap_ellipse(c, cx + dx * w, cy + dy * w, w * r, w * r * 0.8, col)
    _wrap_ellipse(c, cx, cy + w * 0.3, w * 0.62, w * 0.12, lo)
    _wrap_ellipse(c, cx - w * 0.15, cy - w * 0.3, w * 0.18, w * 0.07, hi)


def par_sky():
    """Дальний слой: пастельное небо с облаками сахарной ваты, лента 256×48, стыкуется по краям."""
    c = Canvas(256, 48)
    for y in range(48):
        for x in range(256):
            if y < 14:
                col = SKY
            elif y < 22:
                col = WHITE if (x + y) % 2 == 0 else SKY
            elif y < 34:
                col = WHITE
            elif y < 42:
                col = GREY if (x + y) % 2 == 0 else WHITE
            else:
                col = GREY
            c.set(x, y, col)
    for cx, cy, w, col in ((30, 12, 26, GREY), (88, 24, 20, AQUA), (140, 10, 24, WHITE), (196, 22, 28, GREY),
                           (240, 8, 18, AQUA)):
        _puff(c, cx, cy, w, col, WHITE, SKY if col == WHITE else METAL if col == GREY else SEA)
    return c


def _cone(c, x, base, h, w, col, hi):
    """Рожок: вафельный конус остриём вниз, два шарика мороженого с потёками, вишня."""
    top = base - h
    c.poly([(x - w, top + h * 0.5), (x + w, top + h * 0.5), (x, base)], TAN)
    for k in range(-2, 3):
        c.line(x + k * w / 2.0, top + h * 0.5, x + k * w / 4.0, base - 1, BRASS, 1)
    for t in range(1, 4):
        yy = top + h * 0.5 + t * h * 0.12
        c.line(x - w + t * 2, yy, x + w - t * 2, yy + 3, BRASS, 1)
    c.ellipse(x, top + h * 0.4, w + 1.5, h * 0.22, col)
    for dx in (-w, -w * 0.4, w * 0.3, w * 0.8):
        c.ellipse(x + dx, top + h * 0.55, 1.6, 2.6, col)
    c.ellipse(x, top + h * 0.15, w * 0.7, h * 0.18, hi)
    c.ellipse(x - w * 0.3, top + h * 0.38, w * 0.3, h * 0.07, WHITE)
    c.ellipse(x, top - 1, 1.6, 1.6, RED)


def _cake(c, x, base):
    """Торт на горизонте: три яруса с глазурью, вишенки и свечи с огоньками."""
    c.rect(x - 17, base - 11, x + 17, base, GREY)
    c.rect(x - 17, base - 11, x + 17, base - 9, WHITE)
    c.rect(x - 12, base - 21, x + 12, base - 11, SEA)
    c.rect(x - 12, base - 21, x + 12, base - 19, WHITE)
    c.rect(x - 7, base - 29, x + 7, base - 21, METAL)
    c.rect(x - 7, base - 29, x + 7, base - 27, WHITE)
    for dx in range(-16, 17, 4):
        c.rect(x + dx, base - 9, x + dx, base - 7, WHITE)
    for dx in range(-11, 12, 4):
        c.rect(x + dx, base - 19, x + dx, base - 17, WHITE)
    for dx in (-13, -3, 7, 14):
        c.ellipse(x + dx, base - 12, 1.5, 1.5, RED)
    for dx in (-4, 0, 4):
        c.rect(x + dx, base - 33, x + dx, base - 29, GOLD)
        c.set(x + dx, base - 34, RED)
    c.rect(x - 17, base - 2, x + 17, base, DARK)


def par_far():
    """Средний слой: мятные холмы, на них рожки мороженого вместо гор и торт на горизонте, лента
    256×48, низ сплошной."""
    c = Canvas(256, 48)

    def height(x):
        return 8 + 4 * math.sin(x * math.pi / 32.0 + 1.0) + 2 * math.sin(x * math.pi / 16.0)

    for x in range(256):
        top = 47 - int(height(x))
        c.rect(x, top, x, 47, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        c.rect(x, top + 9, x, 47, NAVY)
    gx = 160
    _cake(c, gx, 47 - int(height(gx)) + 2)
    for px, h, w, col, hi in ((22, 36, 8, GREY, WHITE), (66, 30, 7, AQUA, WHITE), (108, 38, 9, METAL, GREY),
                              (214, 34, 8, SKY, WHITE), (240, 26, 6, GOLD, WHITE), (130, 22, 6, GREY, WHITE)):
        _cone(c, px, 47 - int(height(px)) + 3, h, w, col, hi)
    return c


def _lolly(c, x, base, r, c1, c2):
    """Леденец на палочке: тонкая палочка, диск со спиралью."""
    c.rect(x, base - r - 4, x, base, WHITE)
    cy = base - r - 4
    c.ellipse(x, cy, r + 0.6, r + 0.6, DARK)
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for xx in range(int(x - r - 1), int(x + r + 2)):
            dx, dy = xx - x, y - cy
            rr = math.hypot(dx, dy)
            if rr <= r:
                v = (math.atan2(dy, dx) / (2 * math.pi) * 2 + rr / (r / 2.0)) % 1.0
                c.set(xx, y, c1 if v < 0.5 else c2)


def _floss(c, x, base, r, col, hi, lo):
    """Дерево сахарной ваты: палочка-ствол в бумажном конусе и пышная крона из шаров."""
    c.rect(x, base - r - 3, x, base, TAN)
    c.poly([(x - 2, base - r - 4), (x + 2, base - r - 4), (x, base - r + 1)], GOLD)
    for dx, dy, k in ((0, -0.9, 1.0), (-0.7, -0.3, 0.7), (0.7, -0.3, 0.7), (-0.3, -1.5, 0.6), (0.4, -1.4, 0.6)):
        c.ellipse(x + dx * r, base - r - 3 + dy * r, r * k * 0.8, r * k * 0.7, col)
    c.ellipse(x, base - r * 1.6, r * 0.95, r * 0.25, lo)
    c.ellipse(x - r * 0.3, base - r * 2.5, r * 0.3, r * 0.15, hi)


def par_mid():
    """Ближний слой: бугры мятных холмов с леденцами и деревьями сахарной ваты, лента 256×32."""
    c = Canvas(256, 32)
    for x in range(256):
        crest = 8 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0)
        top = int(round(crest))
        c.rect(x, top, x, 31, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        c.rect(x, top + 8, x, 31, NAVY)
        if (x * 7 + top * 3) % 23 == 0:
            c.rect(x, top + 5 + (x % 6), x + 1, top + 5 + (x % 6), AQUA)
    for px, kind in ((14, 1), (58, 0), (96, 1), (140, 0), (178, 1), (222, 0), (246, 1)):
        by = int(round(8 + 3 * math.sin(px * math.pi / 32.0) + 1.5 * math.sin(px * math.pi / 8.0))) + 2
        if kind == 0:
            _lolly(c, px, by, 3, RED if px % 3 else VIOLET, WHITE)
        else:
            _floss(c, px, by, 3, GREY if px % 4 else SKY, WHITE, METAL if px % 4 else SEA)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, мишка, вещи, земля, три
    слоя дали. Ключи, размеры и число кадров те же, что у `castles16.sprites()`. Ленты демок лежат
    в модулях `sweets_*16.py`."""
    return {
        "enemy_walk": strip([bear_side(p) for p in base.phases()]),
        "enemy_front": strip([bear_front(p) for p in base.phases()]),
        "coin": strip([coin(i) for i in range(6)]),
        "flag": strip([flag(i) for i in range(6)]),
        "heart": heart(),
        "ground": ground(),
        "ground_inner": ground(inner=True),
        "rock": rock(),
        "chest": chest(),
        "par_sky": par_sky(),
        "par_far": par_far(),
        "par_mid": par_mid(),
        "hero_run": strip([gm_side(p) for p in base.phases()]),
        "hero_jump": gm_side(0.0, jump=True),
        "hero_leap": strip([gm_leap(i) for i in range(4)]),
        "hero_idle": strip([gm_idle(i) for i in range(2)]),
        "hero_back": strip([gm_back(p) for p in base.phases()]),
        "hero_slide": strip([gm_slide(i) for i in range(2)]),
        "hero_hang": strip([gm_hang(i) for i in range(2)]),
        "hero_crouch": strip([gm_crouch(i) for i in range(2)]),
    }


# --- Остальные слоты (ленты демок «тропа» и «до выхода» их берут) ------------------------------

def marshmallow(i):
    """Зефир с крылышками (слот попугая) летит вправо: четыре кадра взмаха (вверх, середина, вниз,
    середина), тело по центру кадра. Без красной обводки опасности: её кладёт модуль демки."""
    c = Canvas()
    wing = (-9, -3, 6, -3)[i]
    # Дальнее крылышко позади, ближнее поверх: розовая перепонка с белой жилкой.
    for dx, col in ((-3, GREY), (1, METAL)):
        c.poly([(13 + dx, 16), (18 + dx, 16), (20 + dx, 16 + wing * 1.2), (16 + dx, 15 + wing * 1.0),
                (11 + dx, 16 + wing * 1.2)], col)
        c.line(14 + dx, 16, 12 + dx, 16 + wing * 1.1, WHITE, 1)
    c.rect(10, 13, 21, 24, WHITE)
    c.ellipse(15.5, 13.5, 6.5, 2.6, WHITE)
    c.ellipse(15.5, 24, 6.5, 2.6, WHITE)
    c.rect(10, 17, 21, 17, GREY)
    c.rect(10, 21, 21, 21, GREY)
    c.finish()
    c.set(19, 15, K)
    c.set(19, 16, K)
    c.set(15, 15, K)
    c.set(15, 16, K)
    c.set(17, 19, K)
    c.set(18, 19, K)
    c.set(13, 18, METAL)
    c.set(20, 18, METAL)
    return c


def beetle(i):
    """Драже-жук (слот краба-ползуна) идёт вправо: четыре кадра, шесть лапок по очереди, глянцевый
    мятный панцирь с белыми крапинками и шоколадная голова."""
    c = Canvas()
    for k, dx in enumerate((-8, -3, 3)):
        lift = 1 if (k + i) % 2 == 0 else 0
        c.line(16 + dx, 24, 14 + dx - 1, 29 - lift, DARK, 1)
        c.line(16 + dx + 1, 24, 18 + dx + 1, 29 - lift, DARK, 1)
    c.ellipse(15, 20, 10, 7.5, AQUA)
    c.rect(5, 24, 25, 27, None)
    c.ellipse(26, 19.5, 4, 3.8, DARK)
    c.line(27, 16, 29, 12 + (i % 2), DARK, 1)
    c.line(25, 16, 25, 11 - (i % 2), DARK, 1)
    c.ellipse(15, 20, 10, 7.5, AQUA)
    c.finish()
    c.rect(14, 13, 14, 26, SEA)
    for x, y in ((9, 17), (19, 17), (10, 22), (19, 22), (6, 21), (22, 20)):
        c.set(x, y, WHITE)
    c.set(10, 15, WHITE)
    c.set(11, 14, WHITE)
    c.set(27, 19, WHITE)
    c.set(28, 21, GOLD)
    return c


def key():
    """Леденцовая трость-ключ: розовый пончик-кольцо с присыпкой, шаблон в красно-белую полоску."""
    c = Canvas(32, 32)
    c.ellipse(10, 16, 7, 7, METAL)
    c.ellipse(10, 16, 3, 3, None)
    for x in range(16, 30):
        c.rect(x, 14, x, 17, RED if (x // 2) % 2 == 0 else WHITE)
    c.rect(24, 18, 25, 22, RED)
    c.rect(28, 18, 29, 21, WHITE)
    c.set(8, 11, WHITE)
    c.set(12, 11, GOLD)
    c.set(5, 15, AQUA)
    c.set(15, 17, GOLD)
    return c.finish()


def jar():
    """Банка конфет (аптечка): стеклянная банка, розовая крышка, красный крестик из конфет."""
    c = Canvas(32, 32)
    c.ellipse(15.5, 20, 9, 8, SKY)
    c.rect(11, 8, 20, 14, SKY)
    c.rect(10, 5, 21, 8, METAL)
    c.rect(10, 5, 21, 5, GREY)
    c.ellipse(15.5, 22, 7.5, 5.5, GOLD)
    c.rect(14, 16, 17, 26, WHITE)
    c.rect(11, 19, 20, 22, WHITE)
    c.rect(15, 17, 16, 25, RED)
    c.rect(12, 20, 19, 21, RED)
    c.set(10, 16, WHITE)
    c.set(9, 18, WHITE)
    return c.finish()


def dragee():
    """Снаряд-драже летит вправо: красный шарик с белым бликом и хвостом-сахаром. 16×16."""
    c = Canvas(16, 16)
    c.ellipse(10, 8, 4.5, 4.5, RED)
    c.line(1, 6, 5, 7, GREY, 1)
    c.line(1, 10, 5, 9, GREY, 1)
    c.line(2, 8, 6, 8, WHITE, 1)
    c.set(9, 6, WHITE)
    c.set(8, 7, WHITE)
    return c.finish()


def extras():
    """Слоты сладостей вне `sprites()`: ленты и вещи тех же размеров, что у космоса, пиратов и замков."""
    return {
        "parrot_fly": strip([marshmallow(i) for i in range(4)]),
        "crab_walk": strip([beetle(i) for i in range(4)]),
        "key": key(),
        "medkit": jar(),
        "shot": dragee(),
    }


def shaded(items):
    """Ленты в палитре `PALETTE` → {ключ: (холст, палитра)} как в игре: силуэты получают
    светотень рампами (`pixel_sprites16.reshade`), сплошные плитки остаются в палитре сеттинга."""
    out = {}
    for key, canvas in items.items():
        if base.wants_reshade(key, canvas):
            out[key] = base.reshade(canvas, PALETTE, GROUPS)
        else:
            out[key] = (canvas, PALETTE)
    return out


def save_sheet(path, items, scale=3, pad=6, back=(0x1B, 0x1A, 0x33, 255), max_w=640):
    """Лист для просмотра: `items` это {ключ: (холст, палитра)}, лента на строку; ленты шире
    `max_w` режутся на строки по `max_w`."""
    width = (min(max(c.w for c, _ in items.values()), max_w) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for key, (canvas, palette) in items.items():
        for x0 in range(0, canvas.w, max_w):
            part = Canvas(min(max_w, canvas.w - x0), canvas.h)
            for y in range(canvas.h):
                part.px[y] = canvas.px[y][x0:x0 + part.w]
            for row in base.rgba_rows(part, palette, scale, back):
                line = list(back) * pad * scale + row
                rows.append(line + list(back) * ((len(blank) - len(line)) // 4))
            rows.extend(blank[:] for _ in range(pad * scale))
    with open(path, "wb") as f:
        f.write(png_bytes(width, len(rows), rows))
    print("лист: %s" % path)


def preview(path, scale=4, keys=None, back=(0x6E, 0x9C, 0xC0, 255)):
    """Лист набора: лента на строку после светотени, затем `extras()`. Фон голубой, как небо
    за кадром игры: на тёмном не видно, держит ли обводка. `keys` оставляет часть лент."""
    items = shaded(sprites())
    items.update(shaded(extras()))
    if keys:
        items = {k: v for k, v in items.items() if k in keys}
    save_sheet(path, items, scale=scale, back=back, max_w=256)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        args = sys.argv
        scale = 4
        keys = None
        for a in args:
            if a.startswith("--scale="):
                scale = int(a.split("=", 1)[1])
            if a.startswith("--keys="):
                keys = a.split("=", 1)[1].split(",")
        preview(args[args.index("--preview") + 1], scale, keys)
