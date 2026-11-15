#!/usr/bin/env python3
"""Набор «Сладости» для 16/32-bit, сравнительная версия основы (#137, состав в
`docs/specs/settings.md`): пряничный человечек с белой глазурью и красным бантиком, красные
мармеладные мишки, зефир с крылышками, драже-жук. Те же ленты и кадры, что у пиратов и космоса
(`pixel_sprites16.py`, `space16.py`), позы и опора ног повторяют космонавта, чтобы хитбоксы демок
сходились; рисунок свой. В проект ничего не пишет: только лист для просмотра.

    python3 tools/sweets16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Сладости»: 16 цветов, индекс это та же роль, что у пиратов и космоса (ими рисуют HUD
# и мир демки). Четыре «синих» роли это небо сверху вниз, поэтому мята живёт в них.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x2B, 0x16, 0x1E),  # K      обводка: горький шоколад
    (0x2F, 0x6C, 0x94),  # NAVY   верх неба, тень мяты
    (0x3F, 0xA9, 0x9C),  # SEA    мятная карамель: ближние холмы
    (0x86, 0xDB, 0xBE),  # AQUA   мята: дальние холмы, коробка
    (0xD3, 0xF6, 0xE4),  # SKY    мятный крем, небо у горизонта
    (0xFF, 0xF7, 0xEC),  # WHITE  глазурь, зефир, сахар
    (0xD6, 0xBF, 0xCC),  # GREY   тень белого
    (0xC9, 0x80, 0x3E),  # SKIN   пряник
    (0x94, 0x52, 0x28),  # TAN    тень пряника
    (0xF8, 0xCF, 0x6A),  # GOLD   карамель, бисквит, бонус
    (0xD0, 0x90, 0x38),  # BRASS  тень карамели, вафля
    (0x7C, 0x48, 0x38),  # METAL  молочный шоколад
    (0x4A, 0x28, 0x26),  # DARK   тёмный шоколад
    (0xE6, 0x35, 0x45),  # RED    мармелад, бант, опасность
    (0xFF, 0x8E, 0xB6),  # VIOLET розовая глазурь
    (0xB7, 0x3A, 0x70),  # PLUM   малина: тень розового и красного
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: METAL, METAL: DARK, RED: PLUM, VIOLET: PLUM}
# Материалы для светотени рампами: пряник, глазурь, мята, карамель, шоколад, мармелад, розовое.
GROUPS = {SKIN: "bread", TAN: "bread", WHITE: "icing", GREY: "icing", AQUA: "mint", SKY: "mint",
          SEA: "mint", NAVY: "mint", GOLD: "caramel", BRASS: "caramel", METAL: "choco", DARK: "choco",
          RED: "jelly", VIOLET: "pink", PLUM: "pink"}


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
# Силуэт: круглая голова без шеи, овальное тело, толстые руки и ноги с круглыми концами, без
# кистей и ступней. Узнаётся по белой кайме глазури у концов рук и ног, двум пуговицам-драже,
# белой улыбке и красному бантику под подбородком.

def _cuff(c, x0, y0, x1, y1, t, limb, col, back=2.4):
    """Кайма глазури поперёк конечности, за `back` пикселя до её конца."""
    n = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / n, (y1 - y0) / n
    mx, my = x1 - ux * min(back, n * 0.6), y1 - uy * min(back, n * 0.6)
    r = (t - 1) / 2.0 + 0.45
    for y in range(int(my - r - 1), int(my + r + 2)):
        for x in range(int(mx - r - 1), int(mx + r + 2)):
            along = (x - mx) * ux + (y - my) * uy
            across = -(x - mx) * uy + (y - my) * ux
            if abs(along) <= 0.71 and abs(across) <= r and c.get(x, y) == limb:
                c.set(x, y, col)


def _limb(c, x0, y0, x1, y1, near=True, t=4, sep=False, back=2.4):
    """Рука или нога: толстый отрезок с круглым концом и каймой глазури. Дальняя темнее.
    `sep`: ближняя рука поверх тела отбита тенью снизу."""
    col = SKIN if near else TAN
    if sep:
        c.line(x0, y0 + 1, x1, y1 + 1, TAN, t)
    c.line(x0, y0, x1, y1, col, t)
    _cuff(c, x0, y0, x1, y1, t, col, WHITE if near else GREY, back)


def _foot(c, fx, fy, near=True, w=5, toe=1):
    """Ступня-обрубок: брусок в три строки с каймой глазури над ним. `toe` 1 носком вправо
    (скруглена пятка), -1 влево, 0 без скругления."""
    col = SKIN if near else TAN
    x0 = int(math.floor(fx - (w - 1) / 2.0 + 0.5))
    y0 = int(round(fy))
    c.rect(x0, y0, x0 + w - 1, y0 + 1, col)
    c.rect(x0 + (1 if toe > 0 else 0), y0 + 2, x0 + w - 1 - (1 if toe < 0 else 0), y0 + 2, col)
    for x in range(x0, x0 + w):
        if c.get(x, y0 - 1) == col:
            c.set(x, y0 - 1, WHITE if near else GREY)


def _leg(c, hx, hy, kx, ky, fx, fy, near=True, t=5):
    """Нога: бедро, голень, ступня с каймой."""
    col = SKIN if near else TAN
    c.line(hx, hy, kx, ky, col, t)
    c.line(kx, ky, fx, fy, col, t)
    _foot(c, fx, fy, near, t)


def _head(c, x, y):
    c.ellipse(x, y, 5.6, 5.6, SKIN)


def _face(c, x, y):
    """Лицо в три четверти вправо: два глаза и белая улыбка глазурью. Ставится после обводки."""
    c.rect(x + 1, y - 2, x + 1, y - 1, K)
    c.rect(x + 4, y - 2, x + 4, y - 1, K)
    c.set(x, y + 1, WHITE)
    c.rect(x + 1, y + 2, x + 3, y + 2, WHITE)
    c.set(x + 4, y + 1, WHITE)


def _bow(c, x, y):
    """Бантик под подбородком: узел и два крыла, семь на три пикселя."""
    for sign in (-1, 1):
        c.rect(x + sign * 3, y - 1, x + sign * 2, y + 1, RED)
        c.rect(x + sign * 2, y - 1, x + sign * 2, y + 1, RED)
        c.set(x + sign, y, RED)
    c.set(x, y, RED)


def _torso(c, x, y):
    c.ellipse(x, y, 5, 5.6, SKIN)


def _buttons(c, x, y):
    """Две пуговицы-драже: мятная и розовая."""
    c.rect(x, y, x + 1, y + 1, AQUA)
    c.rect(x, y + 3, x + 1, y + 4, VIOLET)


def ginger_side(phase, jump=False):
    """Пряник сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _limb(c, 16, 15 - bob, 16 + 5.5 * swing, 20 - bob - (3 if jump else 0), False)
    for sign, near in ((-1, False), (1, True)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 28 - lift)
        knee = ((15 + foot[0]) / 2 + 1.5, (hip_y + foot[1]) / 2)
        _leg(c, 15 + sign, hip_y, knee[0], knee[1], foot[0], foot[1], near)
    _torso(c, 15.5, 17 - bob)
    _buttons(c, 17, 16 - bob)
    _limb(c, 14, 15 - bob, 14 - 5.5 * swing, 20 - bob - (4 if jump else 0), True, sep=True)
    _head(c, 16, 7 - bob)
    _bow(c, 17, 12 - bob)
    c.finish()
    _face(c, 16, 7 - bob)
    return c


def ginger_back(phase):
    """Со спины: бежит вглубь экрана, на спине зигзаг глазури, из-за шеи торчат концы банта."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 15.5 + sign * 3
        # Со спины ступни на строку выше, как у матроса и космонавта.
        c.line(x, 21 - bob, x, 27 - lift, SKIN if sign > 0 else TAN, 5)
        _foot(c, x, 27 - lift, sign > 0, 4, 0)
        _limb(c, 15.5 + sign * 5, 15 - bob, 15.5 + sign * 7.5, 20 - bob + s * sign * 2, True)
    _torso(c, 15.5, 17 - bob)
    for k, x in enumerate(range(12, 20)):
        c.set(x, 17 - bob + (k // 2) % 2, WHITE)
    c.rect(10, 11 - bob, 21, 12 - bob, RED)
    c.rect(10, 13 - bob, 11, 13 - bob, RED)
    c.rect(20, 13 - bob, 21, 13 - bob, RED)
    c.ellipse(15.5, 7 - bob, 5.6, 5.6, SKIN)
    return c.finish()


def ginger_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    up = i in (1, 2)
    if up:
        _limb(c, 14, 16 + crouch, 8.5, 11.5 + crouch, False)
    else:
        _limb(c, 14, 15 + crouch, 10.5, 20 + crouch, False)
    for sign, near in ((-1, False), (1, True)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 28 if i in (0, 3) else 26 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        _leg(c, 15 + sign, hip_y, knee[0], knee[1], foot[0], foot[1], near)
    _torso(c, 15.5, 17 + crouch)
    _buttons(c, 17, 16 + crouch)
    if up:
        _limb(c, 17, 16 + crouch, 23.5, 11.5 + crouch, True)
    else:
        _limb(c, 17, 15 + crouch, 21.5, 20 + crouch, True, sep=True)
    _head(c, 16, 7 + crouch)
    _bow(c, 17, 12 + crouch)
    c.finish()
    _face(c, 16, 7 + crouch)
    # Крошки из-под ног на толчке и приземлении.
    if i in (1, 3):
        for x, y in ((9, 30), (12, 31), (22, 31)) if i == 1 else ((7, 30), (24, 30), (26, 31)):
            c.set(x, y, GOLD)
    return c


def ginger_idle(i):
    """Стойка: два кадра, пряник дышит, руки чуть в стороны."""
    c = Canvas()
    up = i
    _limb(c, 13, 15 - up, 9.5, 19 - up, False)
    for sign, near in ((-1, False), (1, True)):
        x = 15.5 + sign * 3
        _leg(c, 15.5 + sign * 1.5, 21, x, 25, x, 28, near)
    _torso(c, 15.5, 17 - up)
    _buttons(c, 17, 16 - up)
    _limb(c, 19, 15 - up, 22.5, 19 - up, True)
    _head(c, 16, 7 - up)
    _bow(c, 17, 12 - up)
    c.finish()
    _face(c, 16, 7 - up)
    return c


def ginger_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх, рука
    сзади на земле. Макушка на 15-й строке, как у матроса и космонавта. Два кадра: колено и
    крошки."""
    c = Canvas()
    c.line(19, 26, 24, 22 - i, TAN, 4)
    _limb(c, 24, 22 - i, 27.5, 26, False, 4, back=2.0)
    _limb(c, 12, 25, 6, 28, True)
    c.line(13.5, 24.5, 19, 26.5, SKIN, 7)
    c.rect(17, 24, 18, 25, AQUA)
    c.rect(20, 25, 21, 26, VIOLET)
    # Ближняя нога по земле, подошвой вперёд; кайма поперёк.
    c.line(19, 28, 26, 28, SKIN, 5)
    c.rect(26, 26, 28, 30, SKIN)
    c.rect(29, 27, 29, 29, SKIN)
    c.rect(25, 26, 25, 30, WHITE)
    _head(c, 10, 21)
    _bow(c, 13, 26)
    c.finish()
    _face(c, 10, 21)
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GOLD)
    return c


def ginger_crouch(i):
    """Присед: та же фигура, сложенная вниз, колени вперёд, рука отведена назад. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.ellipse(13.5, 25.5, 4.6, 3.4, SKIN)
    for sign, near in ((-1, False), (1, True)):
        fx = 17 + sign * 2 + step * sign
        _leg(c, 14, 26.5, fx + 1.5, 25.5, fx, 28, near, 4)
    _limb(c, 11.5, 24.5, 7.5, 27, True, sep=True)
    _head(c, 16, 19)
    _bow(c, 17, 24)
    c.finish()
    _face(c, 16, 19)
    return c


def ginger_hang(i):
    """Вис: руки вверх широким хватом к точке сверху, ноги свисают и качаются. Голова на четыре
    пикселя ниже, чем у космонавта, фигура вытянута: иначе руки над круглой головой читаются
    как ушки."""
    c = Canvas()
    sw = (-1, 1)[i]
    _limb(c, 12.5, 18, 11, 2.5, False, back=3.0)
    _limb(c, 19, 18, 21, 2.5, True, back=3.0)
    c.ellipse(15.5, 21.5, 5, 5, SKIN)
    _buttons(c, 17, 20)
    for sign, near in ((-1, False), (1, True)):
        x = 15.5 + sign * 2
        _leg(c, x, 24.5, x + sw, 26, x + sw * 2, 28, near)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 12)
    _bow(hd, 17, 17)
    hd.finish()
    _face(hd, 16, 12)
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Мармеладный мишка -------------------------------------------------------------------------
# Литой мишка: голова с круглыми ушами, тело грушей, короткие лапы-обрубки. Красный, блики
# белые сверху слева, розовый просвет снизу справа, как у желе на свету. Шаг и рост как у скелета.

def _gloss(c, pts, col=WHITE):
    for x, y in pts:
        if c.get(x, y) not in (None, K):
            c.set(x, y, col)


def _paw(c, fx, fy, col, w=5, toe=0):
    """Задняя лапа-брусок; `toe` сдвигает её носком влево."""
    x0 = int(math.floor(fx - (w - 1) / 2.0 + 0.5)) - toe
    y0 = int(round(fy))
    c.rect(x0, y0, x0 + w - 1 + toe, y0 + 2, col)


def bear_side(phase):
    """Мишка сбоку, лицом влево (навстречу герою): идёт вразвалку по фазе."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(14, 18 - bob, 9.5, 19 - bob + 2 * s, PLUM, 4)
    for sign, col in ((-1, PLUM), (1, RED)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        fx, fy = 16.5 - 4 * a, 28 - lift
        c.line(16.5 + sign, 24 - bob, fx, fy, col, 5)
        _paw(c, fx, fy, col, 5, 1)
    c.ellipse(22.5, 22.5 - bob, 1.7, 1.7, RED)
    c.ellipse(16.5, 20 - bob, 6, 6.2, RED)
    c.ellipse(14.5, 21 - bob, 5.5, 4.6, RED)
    c.ellipse(11.5, 4.8 - bob, 2.2, 2.2, PLUM)
    c.ellipse(14.5, 9 - bob, 6.5, 6, RED)
    c.ellipse(8.5, 11 - bob, 2.8, 2.3, RED)
    c.ellipse(18, 4.8 - bob, 2.7, 2.7, RED)
    c.rect(18, 4 - bob, 18, 5 - bob, PLUM)
    # Ближняя лапа вперёд, отбита тенью снизу.
    c.line(14.5, 18.5 - bob, 8.5, 21 - bob - 2 * s, PLUM, 4)
    c.line(14.5, 17.5 - bob, 8.5, 20 - bob - 2 * s, RED, 4)
    c.finish()
    # Глаз с блестящим зрачком под хмурой бровью, нос, пасть.
    c.rect(11, 8 - bob, 12, 9 - bob, K)
    c.set(11, 8 - bob, WHITE)
    c.rect(10, 6 - bob, 11, 6 - bob, K)
    c.rect(12, 5 - bob, 13, 5 - bob, K)
    c.rect(6, 10 - bob, 7, 10 - bob, K)
    c.rect(8, 13 - bob, 9, 13 - bob, K)
    _gloss(c, ((15, 4 - bob), (16, 5 - bob), (16, 6 - bob), (19, 15 - bob), (20, 16 - bob), (20, 17 - bob)))
    _gloss(c, ((20, 22 - bob), (19, 23 - bob), (18, 24 - bob), (17, 12 - bob), (18, 11 - bob)), VIOLET)
    return c


def bear_front(phase):
    """Мишка лицом к камере: идёт на игрока, лапы по очереди."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 15.5 + sign * 3.5
        c.line(x, 24 - bob, x, 28 - lift, RED, 5)
        _paw(c, x, 28 - lift, RED)
        c.line(15.5 + sign * 5, 17.5 - bob, 15.5 + sign * 8.5, 19.5 - bob - s * sign * 2, RED, 5)
        c.ellipse(15.5 + sign * 5.5, 4.8 - bob, 2.7, 2.7, RED)
    c.ellipse(15.5, 20 - bob, 6.5, 6, RED)
    c.ellipse(15.5, 9.5 - bob, 7, 5.8, RED)
    c.finish()
    # Морда: розовый пятачок с носом и два глаза; брови на таком размере давали кашу.
    c.ellipse(15.5, 12 - bob, 2.6, 1.7, VIOLET)
    c.rect(15, 11 - bob, 16, 11 - bob, K)
    for sign, x in ((-1, 12), (1, 19)):
        c.rect(x, 8 - bob, x, 9 - bob, K)
        ear = 10 if sign < 0 else 20
        c.rect(ear, 5 - bob, ear + 1, 5 - bob, PLUM)
    _gloss(c, ((14, 5 - bob), (15, 5 - bob), (16, 5 - bob), (11, 18 - bob), (11, 19 - bob), (12, 17 - bob)))
    _gloss(c, ((20, 22 - bob), (20, 23 - bob), (19, 24 - bob), (18, 25 - bob)), VIOLET)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def candy(i):
    """Конфета в фантике вращается вокруг стойки: шесть кадров, ширина по косинусу. Карамель в
    золотой обёртке с красным пояском, хвосты фантика белые веером."""
    c = Canvas()
    k = abs(math.cos(math.pi * i / 6.0))
    cx, cy = 15.5, 16
    if k < 0.2:
        # Ребром: виден один хвост фантика, круглый веер.
        c.ellipse(cx, cy, 2.6, 5.5, WHITE)
        c.rect(15, cy - 3, 16, cy + 3, GOLD)
        c.finish()
        c.rect(15, cy - 1, 16, cy, RED)
        return c
    rb = 6.5 * k
    for sign in (-1, 1):
        tip = cx + sign * rb * 0.85
        far = cx + sign * (rb + 6.0 * k)
        pts = [(tip, cy - 1), (far, cy - 5), (far, cy + 5), (tip, cy + 1)]
        c.poly(pts if sign > 0 else [pts[1], pts[0], pts[3], pts[2]], WHITE)
        if k > 0.6:
            c.line(tip + sign * 2, cy - 1, far, cy - 2, GREY, 1)
            c.line(tip + sign * 2, cy + 1, far, cy + 3, GREY, 1)
    c.ellipse(cx, cy, rb, 6, GOLD)
    band = max(0.6, 1.6 * k)
    for y in range(int(cy - 6), int(cy + 7)):
        for x in range(int(cx - band + 0.5), int(cx + band + 0.5) + 1):
            if c.get(x, y) == GOLD:
                c.set(x, y, RED)
    c.finish()
    if k > 0.4:
        c.set(cx - rb * 0.55, cy - 3, WHITE)
        c.set(cx - rb * 0.55, cy - 2, WHITE)
    return c


def lolly(i):
    """Леденец-спираль на палочке вместо флага: красно-белая спираль крутится, шесть кадров
    на оборот."""
    c = Canvas()
    c.rect(15, 20, 16, 31, WHITE)
    cx, cy, r = 15.5, 11.5, 9.6
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - cx, y - cy)
            if d > r:
                continue
            t = (math.atan2(y - cy, x - cx) + d * 0.72 - i * math.pi / 3.0) % (2 * math.pi)
            c.set(x, y, RED if t < math.pi else WHITE)
    c.finish()
    # Блик на стекле леденца.
    c.set(10, 6, SKY)
    c.set(9, 7, SKY)
    c.set(9, 8, SKY)
    return c


def heart():
    """Жизнь в HUD: леденец-сердце с бликом и розовым просветом."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.finish()
    _gloss(c, ((8, 10), (9, 9), (10, 9), (8, 11), (18, 9), (19, 9)))
    _gloss(c, ((22, 16), (21, 17), (20, 18), (19, 19), (18, 20)), VIOLET)
    return c


def ground(inner=False):
    """Срез торта: бисквит, прослойка крема, шоколадный корж, снова крем; плитка стыкуется по
    вертикали. У кромки сверху розовая глазурь с потёками и посыпкой."""
    c = Canvas()
    c.rect(0, 0, 31, 12, GOLD)
    c.rect(0, 13, 31, 14, WHITE)
    c.rect(0, 15, 31, 15, GREY)
    c.rect(0, 16, 31, 28, METAL)
    c.rect(0, 29, 31, 30, WHITE)
    c.rect(0, 31, 31, 31, GREY)
    # Поры бисквита и коржа: редкие, чтобы плитка не рябила.
    for x, y, w in ((3, 3, 2), (11, 9, 1), (18, 4, 1), (26, 8, 2), (8, 6, 1), (22, 11, 1), (29, 2, 1), (14, 1, 2)):
        c.rect(x, y, x + w - 1, y, BRASS)
    for x, y, w in ((5, 19, 2), (13, 24, 1), (20, 18, 1), (27, 22, 2), (9, 26, 1), (17, 21, 2), (24, 26, 1), (1, 23, 1)):
        c.rect(x, y, x + w - 1, y, DARK)
    c.rect(0, 16, 31, 16, DARK)
    if not inner:
        # Потёки: глубина глазури по x, период 32.
        drips = {3: 4, 4: 6, 5: 6, 6: 4, 12: 5, 13: 9, 14: 10, 15: 9, 16: 5, 21: 3, 22: 4, 23: 3, 27: 5, 28: 7,
                 29: 7, 30: 5}
        for x in range(32):
            depth = 5 + drips.get(x, 0)
            c.rect(x, 0, x, depth, VIOLET)
            c.set(x, depth + 1, PLUM)
        for x in range(32):
            # Тень на стенках потёков.
            if c.get(x, 8) == VIOLET and c.get((x + 1) % 32, 8) != VIOLET:
                for y in range(7, 16):
                    if c.get(x, y) == VIOLET:
                        c.set(x, y, PLUM)
        for x in range(1, 32, 8):
            c.rect(x, 1, x + 4, 1, WHITE)
        for x, y, col in ((4, 3, SKY), (9, 4, GOLD), (17, 3, WHITE), (20, 5, AQUA), (25, 3, GOLD), (30, 4, SKY)):
            c.set(x, y, col)
    return c


def sugar():
    """Кусок рафинада вместо камня: белый куб углом к зрителю, три грани разного тона, зёрна
    сахара и два отколотых кубика у подножия."""
    c = Canvas()
    c.poly([(4, 10), (16, 15), (16, 28), (4, 23)], SKY)
    c.poly([(16, 15), (28, 10), (28, 23), (16, 28)], GREY)
    c.poly([(16, 4), (28, 10), (16, 15), (4, 10)], WHITE)
    # Ближнее ребро ловит свет.
    c.line(16, 15, 16, 27, WHITE, 1)
    for x, y in ((7, 14), (10, 19), (13, 23), (6, 20), (12, 16), (9, 24)):
        c.set(x, y, WHITE)
    for x, y in ((20, 17), (24, 15), (22, 22), (26, 19), (19, 24)):
        c.set(x, y, WHITE)
    for x, y in ((12, 8), (18, 7), (21, 10), (15, 12), (10, 10)):
        c.set(x, y, GREY)
    c.rect(1, 27, 2, 28, WHITE)
    c.rect(29, 26, 30, 27, WHITE)
    c.set(30, 27, GREY)
    c.outline()
    return c


def gift():
    """Коробка с бантом вместо сундука: мятная коробка под крышкой, красная лента крест-накрест
    и пышный бант сверху."""
    c = Canvas()
    c.rect(5, 16, 26, 28, AQUA)
    c.rect(5, 16, 26, 17, SEA)
    c.rect(3, 11, 28, 15, SKY)
    c.rect(14, 11, 17, 28, RED)
    for x, y in ((8, 21), (10, 25), (21, 20), (23, 25)):
        c.set(x, y, WHITE)
    # Бант: две петли с просветом, узел, короткие хвосты.
    for sign in (-1, 1):
        c.ellipse(15.5 + sign * 5.5, 7, 4.6, 3.4, RED)
        c.ellipse(15.5 + sign * 6, 7, 1.8, 1.2, PLUM)
        c.line(15.5 + sign * 2, 10, 15.5 + sign * 6, 13, RED, 2)
    c.rect(14, 5, 17, 10, RED)
    c.finish()
    c.set(8, 5, WHITE)
    c.set(9, 5, WHITE)
    c.set(15, 6, VIOLET)
    return c


# --- Слоты демок: летун, ползун, ключ, аптечка, выстрел ----------------------------------------

def zefir(i):
    """Зефир с крылышками летит вправо: белая розочка в три яруса с завитком на макушке (каждый
    ярус шире верхнего, между ними бороздка), крылья розовые из трёх перьев; четыре кадра взмаха
    (вверх, середина, вниз, середина). Тело по центру кадра, чтобы при развороте не прыгало."""
    c = Canvas()
    ang = (-108, -160, 140, -160)[i]

    def wing(rx, ry, col):
        # Крыло сплошной лопастью: веер из трёх перьев с круглыми концами, между ними заливка.
        tips = []
        for da, ln in ((-30, 7.0), (0, 9.0), (30, 7.0)):
            a = math.radians(ang + da)
            tips.append((rx + ln * math.cos(a), ry + ln * math.sin(a)))
        c.poly([(rx, ry)] + tips, col)
        for tx, ty in tips:
            c.line(rx, ry, tx, ty, col, 3)

    wing(15, 15, PLUM)
    c.ellipse(15.5, 21.5, 8, 3.9, WHITE)
    c.ellipse(15.5, 17.5, 6, 3.0, GREY)
    c.ellipse(15.5, 16.5, 6, 3.0, WHITE)
    c.ellipse(15.5, 13.4, 3.7, 2.4, GREY)
    c.ellipse(15.5, 12.4, 3.7, 2.4, WHITE)
    c.rect(15, 8, 17, 10, WHITE)
    c.rect(17, 7, 18, 8, WHITE)
    wing(9.5, 18, VIOLET)
    c.finish()
    # Глаза, румянец, рот.
    c.rect(15, 21, 15, 22, K)
    c.rect(20, 21, 20, 22, K)
    c.rect(17, 23, 18, 23, K)
    c.rect(12, 23, 13, 23, VIOLET)
    c.rect(22, 23, 22, 23, VIOLET)
    return c


def _dome(c, cx, cy, rx, ry, col, y_max):
    """Верхняя часть эллипса до строки `y_max`: панцирь с плоским низом."""
    for y in range(int(cy - ry - 1), int(y_max) + 1):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                c.set(x, y, col)


def bug(i):
    """Драже-жук, четыре кадра: розовая глянцевая половинка драже со швом и крапинами, под ней
    шоколадная голова с глазами, шесть ножек по очереди, усики с карамельными шариками."""
    c = Canvas()
    for k in range(3):
        for sign in (-1, 1):
            lift = 1 if (k + i) % 2 == 0 else 0
            x = 16 + sign * (5 + k * 4)
            c.line(16 + sign * (4 + k * 3), 25, x, 29 - lift, DARK, 1)
            c.rect(min(x, x + sign), 30 - lift, max(x, x + sign), 30 - lift, DARK)
    for sign in (-1, 1):
        wig = (i % 2) * sign
        c.line(16 + sign * 3, 14, 16 + sign * 6 + wig, 9, DARK, 1)
        c.ellipse(16 + sign * 6 + wig, 8, 1.3, 1.3, GOLD)
    _dome(c, 16, 21, 10.4, 8.6, VIOLET, 25)
    c.line(16, 13, 16, 22, PLUM, 1)
    for x, y in ((10, 20), (22, 20), (12, 16), (20, 16)):
        c.rect(x - 1, y, x, y + 1, PLUM)
    c.ellipse(16, 25.5, 4.6, 3, DARK)
    c.finish()
    for x in (13, 18):
        c.rect(x, 24, x + 1, 25, WHITE)
    c.set(14, 25, K)
    c.set(18, 25, K)
    _gloss(c, ((9, 17), (10, 16), (11, 15), (12, 14), (8, 19)))
    return c


def key():
    """Ключ: карамельный бублик в розовой глазури с посыпкой, бородка из карамели."""
    c = Canvas()
    c.rect(16, 14, 29, 17, GOLD)
    c.rect(24, 18, 25, 22, GOLD)
    c.rect(28, 18, 29, 21, GOLD)
    c.ellipse(10, 16, 7.4, 7.4, GOLD)
    for y in range(7, 26):
        for x in range(2, 19):
            d = math.hypot(x - 10, y - 16)
            if 3.4 < d < 6.6 and c.get(x, y) == GOLD and (y < 19 or (x % 3 == 0 and y < 21)):
                c.set(x, y, VIOLET)
    c.ellipse(10, 16, 2.6, 2.6, None)
    c.finish()
    for x, y, col in ((6, 12, WHITE), (13, 11, SKY), (10, 10, GOLD), (5, 16, SKY), (15, 15, WHITE), (14, 18, GOLD)):
        c.set(x, y, col)
    c.rect(19, 15, 27, 15, WHITE)
    return c


def cupcake():
    """Аптечка: капкейк в белой формочке с красным крестом, розовый крем горкой и вишня."""
    c = Canvas()
    c.poly([(7, 18), (24, 18), (22, 29), (9, 29)], WHITE)
    for x in (9, 11, 20, 22):
        c.line(x, 20, x + (1 if x < 16 else -1) * 0.4, 28, GREY, 1)
    c.rect(14, 20, 17, 27, RED)
    c.rect(11, 22, 20, 25, RED)
    c.ellipse(15.5, 16.4, 10, 3.6, PLUM)
    c.ellipse(15.5, 15.6, 10, 3.4, VIOLET)
    c.ellipse(15.5, 12.4, 7.4, 3.2, PLUM)
    c.ellipse(15.5, 11.6, 7.4, 3.0, VIOLET)
    c.ellipse(15.5, 8.6, 4.6, 2.8, PLUM)
    c.ellipse(15.5, 7.9, 4.6, 2.6, VIOLET)
    c.ellipse(16, 4, 2.4, 2.4, RED)
    c.finish()
    c.set(15, 3, WHITE)
    c.set(9, 14, WHITE)
    c.set(10, 13, WHITE)
    c.set(11, 10, WHITE)
    return c


def mint_shot():
    """Выстрел: мятный леденец-вертушка, красно-белые дольки."""
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d > 5.7:
                continue
            t = math.atan2(y - 7.5, x - 7.5) + d * 0.32
            c.set(x, y, RED if int(math.floor(t / (math.pi / 3.0))) % 2 == 0 else WHITE)
    c.finish()
    c.set(5, 4, SKY)
    return c


# --- Параллакс ---------------------------------------------------------------------------------

def _cloud(c, cx, cy, s):
    """Облако сахарной ваты: белые клубы, розовый низ, дно плоское."""
    puffs = ((-9, 0, 5), (-3, -4, 7), (5, -2, 6), (11, 1, 4))
    cells = set()
    for dx, dy, r in puffs:
        px, py, pr = cx + dx * s, cy + dy * s, r * s
        for y in range(int(py - pr - 1), int(py + pr + 2)):
            for x in range(int(px - pr - 1), int(px + pr + 2)):
                if (x - px) ** 2 + (y - py) ** 2 <= pr * pr and y <= cy + 2 * s:
                    cells.add((x, y))
    for x, y in cells:
        low = (x, y + 1) not in cells or (x, y + 2) not in cells
        c.set(x, y, VIOLET if low else WHITE)


def par_sky():
    """Дальний слой: облака сахарной ваты и блёстки сахарной пудры, лента 256×48, стыкуется по
    краям."""
    import random
    c = Canvas(256, 48)
    rng = random.Random(7)
    for _ in range(26):
        c.set(rng.randint(0, 255), rng.randint(0, 47), WHITE if rng.random() < 0.7 else GOLD)
    for cx, cy, s in ((34, 20, 1.5), (98, 34, 1.0), (150, 16, 1.2), (214, 30, 1.6), (250, 12, 0.8)):
        for k in (0, 256, -256):
            _cloud(c, cx + k, cy, s)
    return c


def _far_height(x):
    return 10 + 9 * abs(math.sin(x * math.pi / 64.0 + 0.5)) + 3 * math.sin(x * math.pi / 32.0)


def _cone(c, x, tip_y, r, scoops):
    """Рожок мороженого остриём в холм: вафля в клетку, шарики и вишня."""
    h = int(r * 2.4)
    y0 = tip_y - h
    for dy in range(h + 1):
        half = r * (1.0 - dy / float(h))
        for dx in range(int(-half), int(half) + 1):
            waffle = (dx + dy) % 3 == 0 or (dx - dy) % 3 == 0
            c.set(x + dx, y0 + dy, BRASS if waffle else GOLD)
    cy = y0 + 1.0
    rr = r + 1.0
    for col in scoops:
        cy -= rr * 0.75
        c.ellipse(x, cy, rr, rr * 0.85, col)
        c.rect(x - rr * 0.55, cy - rr * 0.45, x - rr * 0.55 + 1, cy - rr * 0.45, WHITE if col != WHITE else SKY)
        # Тень под шариком: нижний ряд темнее.
        for dx in range(int(-rr), int(rr) + 1):
            if c.get(x + dx, int(cy + rr * 0.85)) == col:
                c.set(x + dx, int(cy + rr * 0.85), PLUM if col == VIOLET else GREY if col == WHITE else BRASS)
        cy -= rr * 0.55
        rr -= 1.0
    c.ellipse(x, cy - 0.6, 1.3, 1.3, RED)


def par_far():
    """Средний слой: мятные холмы под шапками крема, рожки мороженого в ложбинах и торт в два
    яруса на вершине, лента 256×48, низ сплошной."""
    c = Canvas(256, 48)
    tops = [47 - int(_far_height(x)) for x in range(256)]
    for x, top in enumerate(tops):
        c.rect(x, top, x, 47, AQUA)
        c.rect(x, top, x, top + 1, WHITE)
        # Свет на склоне слева от вершины, тень у подножия.
        if tops[(x + 3) % 256] < top:
            c.rect(x, top + 3, x, top + 4, SKY)
        for y in range(43, 48):
            if y >= 46 or (x + y) % 2 == 0:
                c.set(x, y, SEA)
    # Торт: два яруса, розовая глазурь с потёками, прослойка, вишня.
    cake_x = 86
    base_y = max(tops[cake_x - 18], tops[cake_x + 18]) + 2
    for half, y0, y1 in ((18, base_y - 10, base_y), (11, base_y - 18, base_y - 11)):
        x0, x1 = cake_x - half, cake_x + half
        c.rect(x0, y0, x1, y1, WHITE)
        c.rect(x1 - 3, y0, x1, y1, GREY)
        c.rect(x0, y0 + 6, x1, y0 + 6, GOLD)
        c.rect(x0, y0, x1, y0 + 1, VIOLET)
        for x in range(x0, x1 + 1):
            if (x - x0) % 5 in (1, 2):
                c.rect(x, y0 + 2, x, y0 + 2 + ((x - x0) // 5) % 2, VIOLET)
    c.ellipse(cake_x, base_y - 20.6, 2.2, 2.2, RED)
    c.set(cake_x - 1, base_y - 22, WHITE)
    # Рожки: остриё утоплено в холм.
    for x, r, scoops in ((22, 4, (VIOLET,)), (54, 6, (WHITE, VIOLET)), (118, 5, (GOLD,)), (150, 4, (WHITE,)),
                         (182, 6, (VIOLET, WHITE)), (214, 4, (GOLD,)), (246, 5, (VIOLET,))):
        _cone(c, x, tops[x] + 5, r, scoops)
    return c


def par_mid():
    """Ближний слой: гряда мятной карамели с мармеладками на гребне, лента 256×32; низ заливка,
    сходится с цветом под горизонтом."""
    c = Canvas(256, 32)
    tops = []
    for x in range(256):
        crest = 9 + 3.5 * math.sin(x * math.pi / 64.0) + 1.5 * math.sin(x * math.pi / 16.0 + 1.0)
        tops.append(int(round(crest)))
    for x, top in enumerate(tops):
        c.rect(x, top, x, 31, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        c.set(x, top, SKY)
        for y in range(top + 3, top + 9):
            if (x + 2 * (y - top)) % 32 < 2:
                c.set(x, y, AQUA)
        if (x * 7 + top * 3) % 29 == 0:
            c.set(x, top + 12 + (x % 7), NAVY)
    # Мармеладки: полукруглые дольки в сахаре.
    for x, col in ((22, RED), (70, GOLD), (121, VIOLET), (171, RED), (228, GOLD)):
        top = tops[x] + 1
        for dy, half in enumerate((2, 4, 5, 5, 5)):
            c.rect(x - half, top - 5 + dy, x + half, top - 5 + dy, col)
        c.rect(x - 2, top - 4, x - 1, top - 4, WHITE)
        c.set(x + 3, top - 2, WHITE)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, мишка, вещи, земля, три слоя
    дали. Ключи и размеры те же, что у `space16.sprites()`."""
    return {
        "enemy_walk": strip([bear_side(p) for p in base.phases()]),
        "enemy_front": strip([bear_front(p) for p in base.phases()]),
        "coin": strip([candy(i) for i in range(6)]),
        "flag": strip([lolly(i) for i in range(6)]),
        "heart": heart(),
        "ground": ground(),
        "ground_inner": ground(inner=True),
        "rock": sugar(),
        "chest": gift(),
        "par_sky": par_sky(),
        "par_far": par_far(),
        "par_mid": par_mid(),
        "hero_run": strip([ginger_side(p) for p in base.phases()]),
        "hero_jump": ginger_side(0.0, jump=True),
        "hero_leap": strip([ginger_leap(i) for i in range(4)]),
        "hero_idle": strip([ginger_idle(i) for i in range(2)]),
        "hero_back": strip([ginger_back(p) for p in base.phases()]),
        "hero_slide": strip([ginger_slide(i) for i in range(2)]),
        "hero_hang": strip([ginger_hang(i) for i in range(2)]),
        "hero_crouch": strip([ginger_crouch(i) for i in range(2)]),
    }


def extras():
    """Слоты сладостей вне `sprites()`: летун, ползун и вещи тех же размеров, что у космоса и
    пиратов."""
    return {
        "parrot_fly": strip([zefir(i) for i in range(4)]),
        "crab_walk": strip([bug(i) for i in range(4)]),
        "key": key(),
        "medkit": cupcake(),
        "shot": mint_shot(),
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


def save_sheet(path, items, scale=3, pad=6, back=(0x5F, 0xBD, 0xB4, 255), max_w=640):
    """Лист для просмотра: `items` это {ключ: (холст, палитра)}, лента на строку; ленты шире
    `max_w` режутся на строки по `max_w`."""
    width = (min(max(c.w for c, _ in items.values()), max_w) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for key_, (canvas, palette) in items.items():
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


def preview(path, scale=4, keys=None, back=(0x5F, 0xBD, 0xB4, 255)):
    """Лист набора после светотени: лента на строку, как в игре; `keys` оставляет только
    названные ленты в названном порядке. Фон листа это середина неба сеттинга."""
    items = dict(sprites())
    items.update(extras())
    if keys:
        items = {k: items[k] for k in keys}
    save_sheet(path, shaded(items), scale, back=back)


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
