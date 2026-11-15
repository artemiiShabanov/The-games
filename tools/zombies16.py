#!/usr/bin/env python3
"""Набор «Зомби» для 16/32-bit, сравнительная версия основы (#137, состав в
`docs/specs/settings.md`): ночное кладбище, выживший в красной куртке и синей бейсболке с
рюкзаком, зомби-ходоки в лохмотьях. Те же ленты и кадры, что у пиратов и космоса
(`pixel_sprites16.py`, `space16.py`): позы, габариты и опора ног героя повторяют космонавта,
чтобы хитбоксы демок сходились, рисунок свой. Модуль ничего не пишет в проект, только лист.

    python3 tools/zombies16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Зомби»: 16 цветов, индекс это та же роль, что у пиратов и космоса (ими рисуют HUD,
# небо и мир демки: NAVY, SEA, AQUA, SKY идут полосами неба сверху вниз).
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x12, 0x10, 0x14),  # K      обводка
    (0x18, 0x21, 0x42),  # NAVY   ночное небо, силуэты, тень джинсов
    (0x2E, 0x4E, 0x92),  # SEA    джинсы, бейсболка, середина неба
    (0x4B, 0x74, 0xAE),  # AQUA   блик синего, облака, низ неба
    (0x93, 0xB2, 0xCE),  # SKY    лунная дымка у горизонта
    (0xEE, 0xEB, 0xDD),  # WHITE  луна, кость, крест, кроссовки
    (0xA6, 0xA8, 0xA0),  # GREY   камень, жесть, лохмотья
    (0xF0, 0xC0, 0x94),  # SKIN   кожа
    (0xC2, 0x86, 0x5C),  # TAN    тень кожи
    (0xE8, 0xC2, 0x4A),  # GOLD   этикетка банки, свет в окне, сухая трава
    (0xB0, 0x82, 0x2E),  # BRASS  тень золота, жухлая трава
    (0x86, 0x62, 0x46),  # METAL  грязь, кожа рюкзака, дерево
    (0x4A, 0x2D, 0x2B),  # DARK   тёмная грязь, волосы, тень красного
    (0xD2, 0x3B, 0x2E),  # RED    куртка, кровь, крест аптечки
    (0x7F, 0xA8, 0x62),  # VIOLET мёртвая кожа, флаг убежища, армейская краска
    (0x3F, 0x63, 0x45),  # PLUM   тень зелёного
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: DARK, VIOLET: PLUM}
# Материалы для светотени рампами: куртка, джинса, белое с камнем, кожа, золото, кожа рюкзака
# с грязью, мёртвая плоть.
GROUPS = {RED: "jacket", SEA: "denim", NAVY: "denim", AQUA: "denim", SKY: "denim", WHITE: "pale",
          GREY: "pale", SKIN: "skin", TAN: "skin", GOLD: "gold", BRASS: "gold", METAL: "leather",
          DARK: "leather", VIOLET: "rot", PLUM: "rot"}


class Canvas(base.Canvas):
    """Холст набора: своя таблица теней и метки, которые ставятся после тени и обводки (глаз,
    пряжка, блик)."""

    shadow = SHADOW

    def __init__(self, w=base.FRAME, h=base.FRAME):
        super().__init__(w, h)
        self.marks = []

    def mark(self, x, y, c):
        self.marks.append((x, y, c))

    def finish(self):
        self.shade()
        self.outline()
        for x, y, col in self.marks:
            self.set(x, y, col)
        return self


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


def _oval(c, cx, cy, rx, ry, ang, col):
    """Эллипс с поворотом на `ang` радиан: наклонённая голова."""
    ca, sa = math.cos(ang), math.sin(ang)
    r = int(max(rx, ry)) + 2
    for y in range(int(cy) - r, int(cy) + r + 1):
        for x in range(int(cx) - r, int(cx) + r + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                c.set(x, y, col)


# --- Выживший ----------------------------------------------------------------------------------
# Силуэт: бейсболка с длинным козырьком вперёд, рюкзак со скаткой за спиной, узкие ноги в
# джинсах, белые кроссовки. Узнаётся по козырьку и горбу рюкзака, цвет это красная куртка.

def _head(c, x, y, face=1):
    """Голова в бейсболке сбоку, центр (x, y), лицо в сторону `face`. Занимает строки y-5..y+4,
    козырёк торчит вперёд на четыре пикселя."""
    c.ellipse(x, y + 0.5, 4.3, 4.3, SKIN)
    # Волосы на затылке из-под кепки.
    for yy in range(y - 1, y + 3):
        for d in range(3, 6):
            if c.get(x - d * face, yy) == SKIN:
                c.set(x - d * face, yy, DARK)
    c.set(x - face, y + 1, TAN)
    # Нос.
    c.set(x + 5 * face, y + 2, SKIN)
    # Купол кепки шире головы, спереди панель.
    for row, (back, front) in zip(range(y - 5, y - 1), ((-2, 2), (-4, 4), (-5, 5), (-5, 5))):
        for d in range(back, front + 1):
            c.set(x + d * face, row, SEA)
    # Козырёк: по нижней кромке купола, длинный и плоский.
    for d in range(5, 10):
        c.set(x + d * face, y - 2, SEA)
    for d in range(4, 9):
        c.set(x + d * face, y - 1, SEA)
    c.mark(x + 3 * face, y - 4, WHITE)
    c.mark(x + 2 * face, y - 4, WHITE)
    c.mark(x + 2 * face, y + 1, K)
    c.mark(x + 3 * face, y + 3, TAN)


def _head_back(c, y):
    """Затылок: кепка с вырезом застёжки, волосы, уши. Центр по x между 15 и 16."""
    c.ellipse(15.5, y + 0.5, 4.3, 4.3, SKIN)
    for yy in range(y - 1, y + 3):
        for x in range(10, 22):
            if c.get(x, yy) == SKIN:
                c.set(x, yy, DARK)
    c.set(11, y + 1, SKIN)
    c.set(20, y + 1, SKIN)
    for row, (x0, x1) in zip(range(y - 5, y - 1), ((13, 18), (12, 19), (11, 20), (11, 20))):
        c.rect(x0, row, x1, row, SEA)
    c.mark(15, y - 2, DARK)
    c.mark(16, y - 2, DARK)
    c.mark(15, y - 3, NAVY)
    c.mark(16, y - 3, NAVY)


def _pack(c, y0, h=7):
    """Рюкзак за спиной: кожаный мешок с клапаном и пряжкой, сверху зелёная скатка."""
    c.rect(7, y0 + 1, 10, y0 + h, METAL)
    c.rect(6, y0 + 2, 6, y0 + h - 1, METAL)
    c.rect(6, y0 + 3, 10, y0 + 3, DARK)
    c.rect(6, y0 - 1, 10, y0, VIOLET)
    c.mark(8, y0 + 5, GOLD)
    c.mark(6, y0 - 1, PLUM)


def _torso(c, y0, y1, x1=19):
    """Куртка от плеч `y0` до пояса `y1`: красная, белый ворот футболки, лямка рюкзака, джинсы
    на поясе."""
    c.rect(11, y0, x1, y1 - 1, RED)
    c.rect(11, y1, x1, y1, SEA)
    c.rect(15, y0, 18, y0, WHITE)
    c.line(13, y0, 12, y0 + 5, DARK, 1)
    # Резинка куртки по низу.
    c.rect(11, y1 - 1, x1, y1 - 1, DARK)


def _arm(c, x0, y0, x1, y1, near=True):
    """Рукав куртки с кистью. Ближний рукав поверх куртки отбит тёмной кромкой снизу, дальний
    целиком в тени."""
    if near:
        c.line(x0, y0 + 1, x1 - 1, y1 + 1, DARK, 3)
        c.line(x0, y0, x1, y1, RED, 3)
        c.ellipse(x1, y1, 1.4, 1.4, SKIN)
    else:
        c.line(x0, y0, x1, y1, DARK, 3)
        c.ellipse(x1, y1, 1.4, 1.4, TAN)


def _shoe(c, x, y, near=True):
    """Кроссовок: белый, подошва уходит в тень, на ближнем красная полоска."""
    c.rect(x - 1, y, x + 3, y + 1, WHITE if near else GREY)
    if near:
        c.mark(x + 1, y, RED)


def survivor_side(phase, jump=False):
    """Выживший сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), near=False)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _shoe(c, int(round(foot[0])), int(round(foot[1])), sign > 0)
    _pack(c, 13 - bob)
    _torso(c, 13 - bob, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0))
    _head(c, 16, 8 - bob)
    return c.finish()


def survivor_back(phase):
    """Со спины: бежит вглубь экрана, виден рюкзак со скаткой и затылок кепки."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = int(round(max(0.0, s * sign) * 4.0))
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, SEA if sign > 0 else NAVY)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, WHITE)
        c.mark(x - 1 if sign < 0 else x, 28 - lift, RED)
        hand_y = 20 - bob + s * sign * 2
        c.line(16 + sign * 6, 15 - bob, 16 + sign * 7, hand_y, RED, 3)
        c.ellipse(16 + sign * 7, hand_y, 1.4, 1.4, SKIN)
    c.rect(11, 13 - bob, 20, 20 - bob, RED)
    c.rect(11, 20 - bob, 20, 20 - bob, DARK)
    c.rect(11, 21 - bob, 20, 21 - bob, SEA)
    # Рюкзак: мешок, клапан, карман с пряжкой, скатка сверху.
    c.rect(12, 14 - bob, 19, 20 - bob, METAL)
    c.rect(12, 16 - bob, 19, 16 - bob, DARK)
    c.rect(14, 18 - bob, 17, 19 - bob, DARK)
    c.rect(11, 12 - bob, 20, 13 - bob, VIOLET)
    c.mark(15, 17 - bob, GOLD)
    c.mark(16, 17 - bob, GOLD)
    c.mark(13, 12 - bob, PLUM)
    c.mark(18, 12 - bob, PLUM)
    _head_back(c, 8 - bob)
    return c.finish()


def survivor_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    up = i in (1, 2)
    _arm(c, 15, 15 + crouch, 21 if up else 12 - i % 2, (16 if up else 20) + crouch, near=False)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _shoe(c, foot[0], foot[1], sign > 0)
    _pack(c, 13 + crouch)
    _torso(c, 13 + crouch, hip_y)
    _arm(c, 16, 15 + crouch, 23 if up else 20 + i % 2, (12 if up else 20) + crouch)
    _head(c, 16, 8 + crouch)
    return c.finish()


def survivor_idle(i):
    """Стойка: два кадра, выживший дышит, плечи и голова ходят на пиксель."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, cloth)
        _shoe(c, x, 29, sign > 0)
    _arm(c, 14, 15 - up, 13, 21 - up, near=False)
    _pack(c, 13 - up)
    _torso(c, 13 - up, 21)
    _arm(c, 17, 15 - up, 18, 21 - up)
    _head(c, 16, 8 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Куртка под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; у бёдер джинсы."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = SEA if k >= int(n) - 1 else RED
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def survivor_slide(i):
    """Подкат ногами вперёд: корпус откинут на рюкзак, ближняя нога вытянута, дальняя коленом
    вверх, рука упёрта в землю. Макушка кепки на 16-й строке. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, NAVY, 3)
    c.line(24, 23 - i, 27, 27, NAVY, 3)
    _shoe(c, 27, 27, near=False)
    c.line(13, 24, 19, 23, DARK, 2)
    c.rect(4, 26, 9, 29, METAL)
    c.rect(5, 25, 8, 25, METAL)
    c.rect(4, 27, 9, 27, DARK)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, SEA, 4)
    c.rect(28, 26, 30, 29, WHITE)
    _arm(c, 12, 25, 15, 29)
    _head(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((1, 30), (3, 31), (0, 28), (2, 26))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def survivor_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, DARK, 2)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _shoe(c, foot[0], foot[1], sign > 0)
    _pack(c, 21, h=5)
    c.rect(11, 22, 18, 26, RED)
    c.line(13, 22, 12, 26, DARK, 1)
    _arm(c, 14, 24, 19, 26)
    _head(c, 16, 18)
    return c.finish()


def survivor_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, DARK, 3)
    c.ellipse(15, 1, 1.2, 1.2, TAN)
    _pack(c, 13)
    _torso(c, 13, 21)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], cloth, 3)
        _shoe(c, int(foot[0]), 29, sign > 0)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 2:
                c.set(x, y, hd.px[y][x])
    # Ближняя рука идёт к хвату поверх затылка, лицо и козырёк открыты.
    arm = Canvas()
    arm.line(13, 15, 16, 2, RED, 3)
    arm.ellipse(16.5, 1.5, 1.3, 1.3, SKIN)
    arm.finish()
    c.paste(arm, 0, 0)
    return c


# --- Зомби-ходок -------------------------------------------------------------------------------
# Сутулый, обе руки вытянуты вперёд, голова завалена набок, рубаха и штаны в лохмотьях, босой.
# Шаг и рост повторяют скелета пиратов и пришельца.

def zombie_side(phase):
    """Зомби сбоку, лицом влево (навстречу герою): шаркающий шаг по фазе."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Дальняя рука: вперёд и чуть вверх.
    c.line(12, 14 - bob, 5, 13 - bob - s * 1.5, PLUM, 2)
    c.rect(3, 13 - bob - s * 1.5, 4, 14 - bob - s * 1.5, PLUM)
    for sign, cloth, skin in ((-1, DARK, PLUM), (1, METAL, VIOLET)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        mid = ((knee[0] + foot[0]) / 2, (knee[1] + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], cloth, 3)
        c.line(knee[0], knee[1], mid[0], mid[1], cloth, 3)
        c.line(mid[0], mid[1], foot[0], foot[1], skin, 2)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, skin)
    # Корпус сутулый: плечи уходят вперёд на три пикселя.
    for k in range(10):
        off = int(round(-3.0 * (1 - k / 9.0)))
        c.rect(13 + off, 12 - bob + k, 18 + off, 12 - bob + k, GREY)
    # Рваный подол: клочья свисают на штаны.
    for x in (13, 15, 16, 18):
        c.set(x, 22 - bob, GREY)
    c.set(15, 23 - bob, GREY)
    # Шея и голова, заваленная вперёд и набок.
    c.line(12, 10 - bob, 12, 12 - bob, VIOLET, 3)
    _oval(c, 10.5, 6.5 - bob, 4.8, 4.2, 0.45, VIOLET)
    # Клочья волос по макушке и затылку.
    for x in range(10, 16):
        for y in range(0, 9):
            if c.get(x, y) == VIOLET:
                c.set(x, y, DARK)
                if x >= 13:
                    c.set(x, y + 1, DARK)
                break
    # Ближняя рука: обрывок рукава и голое предплечье, кисть свисает.
    hy = 16 - bob + s * 1.5
    c.line(11, 15 - bob, 9, 15.5 - bob, GREY, 3)
    c.line(9, 16 - bob, 4, hy, VIOLET, 2)
    c.rect(2, hy, 3, hy + 2, VIOLET)
    c.mark(8, 6 - bob, WHITE)
    c.mark(9, 6 - bob, K)
    c.mark(7, 9 - bob, K)
    c.mark(8, 9 - bob, K)
    c.mark(8, 10 - bob, RED)
    c.mark(14, 16 - bob, RED)
    c.mark(14, 17 - bob, RED)
    c.mark(15, 17 - bob, RED)
    c.mark(16, 20 - bob, PLUM)
    return c.finish()


def zombie_front(phase):
    """Зомби лицом к камере: идёт на игрока, руки тянутся вперёд, голова на плече."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = int(round(max(0.0, s * sign) * 3.0))
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 25 - lift, METAL, 3)
        c.line(x, 26 - lift, x, 28 - lift, VIOLET, 2)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, VIOLET)
        c.set(x + sign, 26 - lift, METAL)
    c.rect(12, 12 - bob, 19, 21 - bob, GREY)
    # Рваный подол и дыра на боку.
    for x in (12, 14, 15, 18, 19):
        c.set(x, 22 - bob, GREY)
    c.set(14, 23 - bob, GREY)
    # Шея и голова набок: к правому плечу.
    c.rect(14, 10 - bob, 17, 12 - bob, VIOLET)
    _oval(c, 17.5, 6.5 - bob, 5.4, 4.8, 0.42, VIOLET)
    for x in range(13, 23):
        for y in range(0, 9):
            if c.get(x, y) == VIOLET:
                c.set(x, y, DARK)
                if x % 3 == 0:
                    c.set(x, y + 1, DARK)
                break
    # Руки к камере: левая поднята когтями вверх, правая тянется вперёд и вниз (голова
    # лежит на правом плече, там руке тесно). Рукава рваные, предплечья голые.
    ly = 12 - bob - s * 1.5
    c.line(11.5, 13 - bob, 9, 16.5 - bob, GREY, 3)
    c.line(9, 16.5 - bob, 8.5, ly + 2, VIOLET, 2)
    c.ellipse(8.5, ly, 1.9, 1.9, VIOLET)
    for d, up in ((-2, 3), (0, 4), (2, 3)):
        c.rect(8.5 + d, ly - up, 8.5 + d, ly - 2, VIOLET)
    ry = 19 - bob + s * 1.5
    c.line(20, 14 - bob, 21.5, 15 - bob, GREY, 3)
    c.line(21.5, 16 - bob, 21, ry, VIOLET, 3)
    c.ellipse(21, ry + 1.5, 2.4, 2.2, VIOLET)
    for d in (-2, 0, 2):
        c.set(21 + d, ry + 4, VIOLET)
    c.mark(21, int(round(ry + 2)), PLUM)
    # Лицо по наклону головы: белый глаз, пустая глазница, кривой рот с кровью.
    c.mark(15, 5 - bob, WHITE)
    c.mark(16, 5 - bob, WHITE)
    c.mark(15, 6 - bob, WHITE)
    c.mark(16, 6 - bob, K)
    c.mark(19, 7 - bob, K)
    c.mark(20, 7 - bob, K)
    c.mark(20, 8 - bob, K)
    c.mark(15, 9 - bob, K)
    c.mark(16, 10 - bob, K)
    c.mark(17, 10 - bob, K)
    c.mark(18, 10 - bob, WHITE)
    c.mark(16, 11 - bob, RED)
    c.mark(14, 15 - bob, RED)
    c.mark(15, 15 - bob, RED)
    c.mark(15, 16 - bob, RED)
    c.mark(17, 19 - bob, PLUM)
    c.mark(18, 19 - bob, PLUM)
    return c.finish()


# --- Летун и ползун ----------------------------------------------------------------------------

def raven(i):
    """Ворон летит вправо, четыре кадра взмаха (вверх, середина, вниз, середина): иссиня-чёрный,
    толстый клюв, хвост клином, большое крыло с маховыми перьями зубцами, красный глаз. Тело по
    центру кадра."""
    c = Canvas()
    # Хвост клином с вырезом.
    c.poly([(9, 16), (1, 14), (3, 17), (0, 19), (3, 20), (9, 20)], NAVY)
    c.ellipse(15, 18, 6.5, 3.5, NAVY)
    c.ellipse(22, 15, 3.4, 3.2, NAVY)
    c.set(21, 20, NAVY)
    # Клюв толстый.
    c.poly([(25, 13), (30, 15.5), (25, 17)], GREY)
    # Крыло по кадрам: основание на спине, дальняя кромка зубцами маховых перьев.
    wing = (
        [(11, 16), (7, 6), (10, 8), (11, 3), (14, 7), (16, 2), (18, 7), (20, 4), (21, 10), (20, 16)],
        [(12, 16), (5, 10), (8, 11), (8, 8), (12, 11), (13, 8), (16, 12), (20, 15)],
        [(11, 19), (8, 27), (11, 26), (12, 30), (15, 26), (17, 30), (19, 25), (21, 27), (21, 21), (20, 19)],
        [(12, 19), (6, 24), (9, 24), (9, 27), (13, 24), (14, 26), (16, 23), (20, 20)],
    )[i]
    c.poly(wing, NAVY)
    c.finish()
    # Отлив: стержни перьев от основания к зубцам, кромка крыла на теле.
    root = (16, 16 if i < 2 else 19)
    tips = ((1, 3, 5, 7), (1, 3, 5), (1, 3, 5, 7), (1, 3, 5))[i]
    for k in tips:
        tx, ty = wing[k]
        c.line(root[0] + (tx - root[0]) * 0.25, root[1] + (ty - root[1]) * 0.25,
               root[0] + (tx - root[0]) * 0.8, root[1] + (ty - root[1]) * 0.8, SEA, 1)
    c.line(12, root[1], 19, root[1], SEA, 1)
    c.set(23, 14, RED)
    c.set(21, 13, AQUA)
    c.set(26, 14, WHITE)
    c.set(27, 15, WHITE)
    return c


def hand(i):
    """Ползущая кисть: отрубленная рука идёт на кончиках пальцев влево. Четыре кадра: четыре
    пальца впереди переступают по очереди, большой упирается под ладонью, запястье с обрывком
    рукава и костью волочится сзади."""
    c = Canvas()
    # Запястье волочится по земле, на конце срез.
    c.line(20, 19, 27, 25, VIOLET, 6)
    c.line(27, 21, 23, 27, GREY, 3)
    c.ellipse(28.5, 26, 1.8, 2.6, RED)
    # Большой палец под ладонью.
    lift = 1 if i % 2 else 0
    c.line(17, 21, 18, 25, PLUM, 3)
    c.line(18, 25, 16 + lift, 29 - lift, PLUM, 2)
    c.mark(16 + lift, 30 - lift, WHITE)
    # Четыре пальца от дальнего к ближнему: костяшка высоко, кончик на земле.
    fingers = (((13.5, 15), 14, VIOLET), ((11, 13.5), 10, VIOLET), ((8.5, 13.5), 6, VIOLET), ((6, 15), 2, VIOLET))
    for k, (joint, tip_x, col) in enumerate(fingers):
        step = (1, 0, -1, 0)[(i + k) % 4]
        up = 2 if step == 1 else 0
        jx, jy = joint[0] + step * 0.5, joint[1] - up * 0.5
        tx, ty = tip_x + step, 29 - up
        mx, my = (jx + tx) / 2 - 0.5, (jy + ty) / 2
        c.line(14, 17, jx, jy, col, 3)
        c.line(jx, jy, mx, my, col, 2)
        c.line(mx, my, tx, ty, col, 2)
        c.mark(tx, ty + 1, WHITE)
        c.mark(int(round(mx)), int(round(my)), PLUM)
        c.mark(int(round(mx)) + 1, int(round(my)), PLUM)
    # Тыльная сторона ладони поверх оснований пальцев, жилы к костяшкам.
    c.ellipse(16.5, 18, 5.2, 3.8, VIOLET)
    for x, y in ((13, 17), (15, 16), (17, 16), (19, 17), (14, 19), (17, 19)):
        c.mark(x, y, PLUM)
    c.mark(28, 26, WHITE)
    c.mark(29, 25, WHITE)
    return c.finish()


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Банка консервов крутится вокруг оси: шесть кадров, по этикетке едет красный помидор, с
    другой стороны строчки состава."""
    c = Canvas()
    a = 2.0 * math.pi * i / 6.0
    c.rect(9, 8, 22, 25, GREY)
    c.ellipse(15.5, 25, 6.5, 2.0, GREY)
    c.rect(9, 12, 22, 22, GOLD)
    for phase, kind in ((a, 0), (a + math.pi, 1)):
        d = math.cos(phase)
        if d <= 0.1:
            continue
        x = 15.5 + 6.0 * math.sin(phase)
        w = 3.2 * d
        if kind == 0:
            c.ellipse(x, 17.3, max(w, 0.6), 3.0, RED)
            c.set(x, 14, PLUM)
        else:
            for y in (14, 17, 20):
                c.rect(max(9, x - w), y, min(22, x + w), y, DARK)
    # Рёбра жести над и под этикеткой, блик вдоль бока.
    c.rect(9, 10, 22, 10, WHITE)
    c.rect(9, 24, 22, 24, WHITE)
    c.rect(11, 12, 11, 22, WHITE)
    # Крышка с кольцом.
    c.ellipse(15.5, 7.5, 6.5, 2.4, WHITE)
    c.ellipse(15.5, 7.5, 4.2, 1.2, GREY)
    c.finish()
    c.set(15, 7, DARK)
    c.set(16, 7, DARK)
    return c


def flag(i):
    """Флаг убежища на древке: зелёное полотнище с белым крестом идёт волной."""
    c = Canvas()
    c.rect(5, 3, 6, 31, METAL)
    c.ellipse(5.5, 2, 2, 2, GREY)

    def wave(x):
        return math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0

    top = [(x, 5 + wave(x)) for x in range(8, 29)]
    bottom = [(x, 19 + wave(x)) for x in range(8, 29)]
    c.poly(top + bottom[::-1], VIOLET)
    c.shade()
    c.outline()
    # Крест следует волне по столбцам.
    for x in range(12, 25):
        w = wave(x)
        if 17 <= x <= 19:
            for y in range(7, 18):
                c.set(x, y + w, WHITE)
        else:
            for y in range(11, 14):
                c.set(x, y + w, WHITE)
    for x in range(12, 25):
        w = wave(x)
        c.set(x, (17 if 17 <= x <= 19 else 13) + w, GREY)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    c.set(11, 9, WHITE)
    return c.finish()


def ground(inner=False):
    """Кладбищенская грязь: комья, камешки, корешки; у кромки жухлая трава клочьями."""
    c = Canvas()
    c.rect(0, 0, 31, 31, METAL)
    rng = random.Random(7 if inner else 5)
    # Тёмные комья и борозды, стыкуются по краям.
    for _ in range(11):
        x, y, w = rng.randint(0, 31), rng.randint(6, 30), rng.randint(2, 5)
        for d in range(w):
            c.set((x + d) % 32, y, DARK)
        if rng.random() < 0.5:
            c.set((x + 1) % 32, y + 1, DARK)
    # Камешки со светлым верхом.
    for _ in range(4):
        x, y = rng.randint(1, 29), rng.randint(9, 28)
        c.rect(x, y, x + 1, y, GREY)
        c.rect(x, y + 1, x + 1, y + 1, DARK)
    # Светлые крошки сухой глины.
    for _ in range(8):
        c.set(rng.randint(0, 31), rng.randint(7, 30), BRASS)
    if inner:
        # В глубине кость и корень.
        c.rect(8, 14, 13, 14, WHITE)
        c.set(7, 13, WHITE)
        c.set(7, 15, WHITE)
        c.set(14, 13, WHITE)
        c.set(14, 15, WHITE)
        c.line(22, 3, 25, 9, DARK, 1)
        c.line(25, 9, 23, 13, DARK, 1)
    else:
        # Трава: плотный сухой слой и клочья разной длины, кое-где ещё зелёные стебли.
        lengths = (3, 2, 4, 2, 3, 5, 2, 3, 2, 4, 3, 2, 6, 3, 2, 3)
        for x in range(32):
            n = lengths[x % 16] if x < 16 else lengths[(x * 5 + 3) % 16]
            c.rect(x, 0, x, n, BRASS)
            c.set(x, n + 1, DARK)
            if (x * 3) % 7 < 3:
                c.set(x, 0, GOLD)
            if x % 11 == 4:
                c.rect(x, 0, x, n, PLUM)
            if x % 13 == 8:
                c.rect(x, 1, x, n, VIOLET)
        c.rect(0, 1, 31, 1, BRASS)
    return c


def rock():
    """Надгробие: покосившаяся плита с высеченным крестом, трещина, мох у земли, холмик."""
    c = Canvas()
    c.ellipse(15.5, 28.5, 13, 2.4, METAL)
    c.poly([(8, 28), (9, 11), (11, 7), (15, 4.5), (20, 5), (23.5, 8), (25, 12), (24, 28)], GREY)
    c.finish()
    # Светлая грань слева сверху, как у тёсаного камня.
    for x, y in ((10, 11), (10, 12), (10, 13), (11, 9), (12, 8), (13, 7), (14, 6), (15, 6)):
        if c.get(x, y) == GREY:
            c.set(x, y, WHITE)
    # Крест высечен в камне.
    c.rect(16, 9, 17, 20, DARK)
    c.rect(13, 12, 20, 13, DARK)
    c.rect(12, 23, 21, 23, METAL)
    # Трещина от края.
    for x, y in ((23, 9), (22, 10), (22, 11), (21, 12), (22, 15), (21, 16)):
        c.set(x, y, DARK)
    # Мох и трава у основания.
    for x, y in ((9, 26), (10, 26), (10, 25), (11, 27), (9, 27), (10, 27), (22, 27), (23, 26), (23, 27), (21, 27)):
        c.set(x, y, VIOLET)
    for x, y in ((8, 27), (11, 26), (22, 26)):
        c.set(x, y, PLUM)
    return c


def chest():
    """Армейский ящик: зелёные доски, тёмные стяжки, защёлки, белая звезда по трафарету."""
    c = Canvas()
    c.rect(3, 13, 28, 28, VIOLET)
    c.rect(2, 9, 29, 13, VIOLET)
    c.finish()
    # Щель под крышкой и швы досок.
    c.rect(3, 14, 28, 14, PLUM)
    c.rect(3, 19, 28, 19, PLUM)
    c.rect(3, 24, 28, 24, PLUM)
    # Стяжки и уголки.
    for x in (6, 24):
        c.rect(x, 9, x + 1, 28, DARK)
    # Защёлки.
    for x in (10, 20):
        c.rect(x, 12, x + 1, 15, GOLD)
        c.set(x, 16, BRASS)
        c.set(x + 1, 16, BRASS)
    # Звезда.
    for x, y in ((15, 17), (16, 17), (15, 18), (16, 18), (12, 19), (13, 19), (14, 19), (15, 19), (16, 19), (17, 19),
                 (18, 19), (19, 19), (13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20), (14, 21), (15, 21),
                 (16, 21), (17, 21), (14, 22), (17, 22), (13, 23), (18, 23)):
        c.set(x, y, WHITE)
    # Тёмная кромка крышки.
    c.rect(2, 13, 2, 13, PLUM)
    c.rect(29, 13, 29, 13, PLUM)
    return c


def key():
    """Ключ от убежища: латунный, с красной биркой на кольце."""
    c = Canvas()
    c.ellipse(10, 13, 6, 6, GOLD)
    c.ellipse(10, 13, 2.6, 2.6, None)
    c.rect(15, 12, 28, 14, GOLD)
    c.rect(23, 15, 24, 19, GOLD)
    c.rect(27, 15, 28, 18, GOLD)
    c.line(8, 18, 8, 21, GREY, 1)
    c.poly([(5, 22), (11, 22), (11, 29), (5, 29)], RED)
    c.finish()
    c.rect(15, 12, 28, 12, WHITE)
    c.set(7, 9, WHITE)
    c.set(8, 24, K)
    c.rect(7, 26, 9, 26, WHITE)
    return c


def medkit():
    """Аптечка: белая сумка с красным крестом, тёмная ручка, застёжки."""
    c = Canvas()
    c.rect(4, 12, 27, 28, WHITE)
    c.rect(12, 7, 19, 8, DARK)
    c.rect(12, 9, 13, 11, DARK)
    c.rect(18, 9, 19, 11, DARK)
    c.finish()
    c.rect(4, 12, 27, 13, GREY)
    c.rect(13, 16, 18, 27, RED)
    c.rect(9, 19, 22, 24, RED)
    for x in (7, 24):
        c.rect(x, 12, x, 14, GOLD)
    return c


def shot():
    """Плевок зомби: ядовитый зелёный сгусток с блестящим пузырём, 16×16."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, PLUM)
    c.ellipse(8, 8, 4.2, 4.2, VIOLET)
    c.ellipse(7, 7, 1.8, 1.8, WHITE)
    c.set(10, 10, GOLD)
    return c


# --- Параллакс ---------------------------------------------------------------------------------

def par_sky():
    """Дальний слой: луна в дымке, рваные облака и звёзды, лента 256×48, стыкуется по краям."""
    c = Canvas(256, 48)
    rng = random.Random(31)
    mx, my, r = 196, 19, 11
    for _ in range(44):
        x, y = rng.randint(0, 255), rng.randint(0, 47)
        if math.hypot(x - mx, y - my) > r + 5:
            c.set(x, y, WHITE if rng.random() < 0.5 else SKY)
    for x, y in ((24, 9), (118, 6), (150, 33), (62, 40)):
        c.rect(x - 1, y, x + 1, y, SKY)
        c.rect(x, y - 1, x, y + 1, SKY)
        c.set(x, y, WHITE)
    # Ореол: кольцо через пиксель.
    for y in range(my - r - 4, my + r + 5):
        for x in range(mx - r - 4, mx + r + 5):
            d = math.hypot(x - mx, y - my)
            if r + 1.2 < d < r + 3.4 and (x + y) % 2 == 0:
                c.set(x, y, AQUA)
    c.ellipse(mx, my, r, r, WHITE)
    # Объём: дальний от света край в дымке, кратеры.
    for y in range(my - r, my + r + 1):
        for x in range(mx - r, mx + r + 1):
            if c.get(x, y) == WHITE and math.hypot(x - (mx - 4), y - (my - 4)) > r + 2.5:
                c.set(x, y, SKY)
    c.ellipse(mx - 4, my - 3, 2.4, 2.0, SKY)
    c.ellipse(mx + 3, my + 1, 1.6, 1.4, SKY)
    c.ellipse(mx - 2, my + 5, 1.8, 1.2, SKY)
    c.set(mx + 5, my - 5, SKY)
    c.set(mx - 5, my - 3, GREY)
    c.set(mx + 3, my + 2, GREY)
    # Облака: длинные рваные полосы, одна режет луну понизу.
    for cx, cy, w in ((40, 14, 30), (104, 36, 24), (186, 27, 27), (236, 42, 18)):
        for k in (0, 256, -256):
            c.ellipse(cx + k + 5, cy + 2, w * 0.75, 1.6, SEA)
            c.ellipse(cx + k, cy, w, 2.0, AQUA)
            c.ellipse(cx + k - 9, cy - 2, w * 0.4, 1.3, AQUA)
            c.ellipse(cx + k + 12, cy - 1, w * 0.3, 1.2, SKY)
    return c


def _tree(c, x, y, h, lean, seed):
    """Мёртвое дерево силуэтом: ствол и три яруса голых ветвей."""
    rng = random.Random(seed)

    def branch(x0, y0, ang, length, depth):
        x1 = x0 + math.cos(ang) * length
        y1 = y0 - math.sin(ang) * length
        c.line(x0, y0, x1, y1, NAVY, 2 if depth == 0 else 1)
        if depth == 0:
            c.line(x0 + 1, y0, x1 + 1, y1 + length * 0.4, NAVY, 1)
        if depth < 3:
            for d in (-0.65, 0.55):
                branch(x1, y1, ang + d + rng.uniform(-0.2, 0.2), length * 0.62, depth + 1)

    branch(x, y, math.pi / 2 + lean, h, 0)


def par_far():
    """Средний слой: дальняя гряда и тёмный холм с часовней, мёртвыми деревьями и крестами,
    лента 256×48, низ сплошной."""
    c = Canvas(256, 48)
    t = 2.0 * math.pi / 256.0

    def back(x):
        return 15 + 5 * math.sin(x * t * 2 + 1.0) + 2.5 * math.sin(x * t * 7 + 0.5)

    def hill(x):
        return 7 + 3 * math.sin(x * t * 3 + 2.0) + 1.5 * math.sin(x * t * 9) + 17 * math.exp(-((x - 128) / 36.0) ** 2)

    def top(x):
        return 47 - int(hill(x))

    for x in range(256):
        c.rect(x, 47 - int(back(x)), x, 47, SEA)
    # Деревья и кресты стоят на холме, поэтому рисуются до него: корни уходят в землю.
    for x, h, lean, seed in ((30, 7, 0.15, 3), (72, 9, -0.2, 5), (97, 8, 0.25, 8), (163, 9, -0.15, 13), (206, 8, 0.2, 21)):
        _tree(c, x, top(x) + 2, h, lean, seed)
    for x in (50, 84, 150, 178, 228):
        c.rect(x, top(x) - 4, x, top(x), NAVY)
        c.rect(x - 1, top(x) - 3, x + 1, top(x) - 3, NAVY)
    # Часовня на вершине: башня со шпилем и крестом, неф с двускатной крышей.
    gy = top(128)
    c.rect(123, gy - 7, 137, gy + 1, NAVY)
    c.poly([(121, gy - 7), (130, gy - 13), (139, gy - 7)], NAVY)
    c.rect(118, gy - 15, 123, gy + 1, NAVY)
    c.poly([(117, gy - 15), (120.5, gy - 22), (124, gy - 15)], NAVY)
    c.rect(120, gy - 25, 121, gy - 22, NAVY)
    c.rect(119, gy - 24, 122, gy - 24, NAVY)
    for x in range(256):
        c.rect(x, top(x), x, 47, NAVY)
        c.set(x, top(x), PLUM)
    # Лунный свет по левым скатам, окна: одно горит.
    c.line(122, gy - 8, 129, gy - 13, SEA, 1)
    c.line(118, gy - 16, 120, gy - 21, SEA, 1)
    c.rect(118, gy - 14, 118, gy - 1, SEA)
    c.rect(120, gy - 12, 121, gy - 10, GOLD)
    c.set(120, gy - 13, GOLD)
    c.set(121, gy - 13, BRASS)
    c.rect(127, gy - 4, 128, gy - 2, BRASS)
    c.rect(133, gy - 4, 134, gy - 2, GOLD)
    c.rect(120, gy - 3, 121, gy, K)
    return c


def par_mid():
    """Ближний слой: кладбищенское поле с кованой оградой, плитами и крестами, понизу туман,
    лента 256×32."""
    c = Canvas(256, 32)
    t = 2.0 * math.pi / 256.0

    def top(x):
        return int(round(12 + 2 * math.sin(x * t * 4) + math.sin(x * t * 11 + 1.0)))

    # Ограда: секции прутьев с пиками, одна секция завалена.
    for x0 in (4, 68, 132, 196):
        broken = x0 == 132
        for k in range(12):
            x = x0 + k * 4
            if broken and k in (5, 6):
                continue
            tip = 2 + (1 if k % 3 else 0) + (k if broken and k > 6 else 0) // 3
            c.rect(x, tip, x, top(x), NAVY)
            c.set(x, tip - 1, SEA)
        for y in (5, 9):
            if broken:
                c.rect(x0, y, x0 + 16, y, NAVY)
                c.line(x0 + 28, y + 1, x0 + 44, y + 3, NAVY, 1)
            else:
                c.rect(x0, y, x0 + 44, y, NAVY)
        c.rect(x0 - 1, 1, x0, top(x0), NAVY)
        c.rect(x0 + 44, 1, x0 + 45, top(x0 + 44), NAVY)
    for x in range(256):
        y = top(x)
        c.rect(x, y, x, 31, PLUM)
        c.set(x, y, VIOLET)
        if x % 9 == 2 or x % 23 == 7:
            c.rect(x, y - 2, x, y, VIOLET)
        if x % 9 == 3:
            c.set(x, y - 1, VIOLET)
    # Плиты и кресты в поле.
    for x, kind in ((22, 0), (56, 1), (90, 0), (118, 2), (160, 1), (186, 0), (224, 2), (246, 1)):
        y = top(x) + 9
        if kind == 0:
            c.rect(x, y - 7, x + 5, y, GREY)
            c.rect(x + 1, y - 8, x + 4, y - 8, GREY)
            c.rect(x + 5, y - 6, x + 5, y, METAL)
            c.rect(x + 2, y - 5, x + 3, y - 5, DARK)
            c.rect(x + 2, y - 3, x + 3, y - 3, DARK)
        elif kind == 1:
            c.rect(x + 2, y - 9, x + 3, y, GREY)
            c.rect(x, y - 7, x + 5, y - 6, GREY)
            c.rect(x + 3, y - 5, x + 3, y, METAL)
        else:
            c.poly([(x, y), (x + 1, y - 5), (x + 6, y - 6), (x + 7, y)], GREY)
            c.rect(x + 6, y - 4, x + 7, y, METAL)
    # Туман стелется по низу и уходит в синеву под горизонтом.
    for y in range(24, 32):
        for x in range(256):
            wisp = math.sin(x * t * 3 + y * 0.6) + math.sin(x * t * 7 - y)
            if y >= 30 or (y >= 27 and (x + y) % 2 == 0) or (wisp > 1.1 and (x + y) % 2 == 0):
                c.set(x, y, SEA)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, зомби, вещи, земля, три слоя
    дали."""
    return {
        "enemy_walk": strip([zombie_side(p) for p in base.phases()]),
        "enemy_front": strip([zombie_front(p) for p in base.phases()]),
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
        "hero_run": strip([survivor_side(p) for p in base.phases()]),
        "hero_jump": survivor_side(0.0, jump=True),
        "hero_leap": strip([survivor_leap(i) for i in range(4)]),
        "hero_idle": strip([survivor_idle(i) for i in range(2)]),
        "hero_back": strip([survivor_back(p) for p in base.phases()]),
        "hero_slide": strip([survivor_slide(i) for i in range(2)]),
        "hero_hang": strip([survivor_hang(i) for i in range(2)]),
        "hero_crouch": strip([survivor_crouch(i) for i in range(2)]),
    }


def extras():
    """Слоты тропы и шутера, которые у пиратов лежат в модулях демок: летун (ворон), ползун
    (кисть руки), ключ, аптечка, снаряд врага."""
    return {
        "parrot_fly": strip([raven(i) for i in range(4)]),
        "crab_walk": strip([hand(i) for i in range(4)]),
        "key": key(),
        "medkit": medkit(),
        "shot": shot(),
    }


def shaded(items):
    """Ленты в палитре `PALETTE` → {ключ: (холст, палитра)} как в игре: силуэты получают
    светотень рампами (`pixel_sprites16.reshade`), сплошные плитки остаются в палитре сеттинга."""
    out = {}
    for key_, canvas in items.items():
        if base.wants_reshade(key_, canvas):
            out[key_] = base.reshade(canvas, PALETTE, GROUPS)
        else:
            out[key_] = (canvas, PALETTE)
    return out


def save_sheet(path, items, scale=3, pad=6, back=(0x34, 0x3A, 0x52, 255), max_w=640):
    """Лист для просмотра: `items` это {ключ: (холст, палитра)}, лента на строку; ленты шире
    `max_w` режутся на строки по `max_w`."""
    width = (min(max(c.w for c, _ in items.values()), max_w) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for _, (canvas, palette) in items.items():
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


def preview(path, scale=4, keys=None):
    """Лист набора: лента на строку, как в игре, после светотени. `keys`: только эти ленты."""
    items = dict(sprites())
    items.update(extras())
    if keys:
        items = {k: items[k] for k in keys}
    save_sheet(path, shaded(items), scale=scale)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        scale_ = 4
        keys_ = None
        for arg in sys.argv[1:]:
            if arg.startswith("--scale="):
                scale_ = int(arg.split("=", 1)[1])
            if arg.startswith("--keys="):
                keys_ = [k for k in arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], scale_, keys_)
