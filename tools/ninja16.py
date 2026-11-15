#!/usr/bin/env python3
"""Набор «Ниндзя» для 16/32-bit, сравнительная версия основы (#138, состав в
`docs/specs/settings.md`): закат над замком, ниндзя в тёмно-синем с красным шарфом, чужой клан
в красном с серпами. Те же ленты и кадры, что у пиратов и космоса (`pixel_sprites16.py`,
`space16.py`), позы и опора ног повторяют матроса и космонавта, чтобы хитбоксы демок сходились,
но рисунок свой: узкая фигура, капюшон с прорезью глаз, два конца шарфа за спиной, рукоять меча
над плечом, светлые обмотки на голенях. Сам ничего в проект не пишет, только лист на просмотр.

    python3 tools/ninja16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Ниндзя»: 16 цветов, индекс это та же роль, что у пиратов и космоса (ими рисуют HUD и
# мир демки). Небо демки идёт полосами NAVY, SEA, AQUA, SKY сверху вниз, поэтому эти четыре
# цвета и есть закат: индиго, сумеречный синий, коралл, бледное золото у горизонта.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x12, 0x10, 0x18),  # K      обводка
    (0x1A, 0x1C, 0x48),  # NAVY   верх неба, тень синего, силуэты вдали
    (0x38, 0x46, 0x9C),  # SEA    костюм героя, сумерки, дымка у воды
    (0xE9, 0x7B, 0x52),  # AQUA   коралл заката, облака
    (0xFB, 0xDC, 0x92),  # SKY    золото у горизонта, брюхо жабы, свет
    (0xF3, 0xEE, 0xE2),  # WHITE  обмотки, знамя, сталь на свету
    (0xB7, 0xB4, 0xB2),  # GREY   тень белого, светлый камень
    (0xF2, 0xC8, 0x9A),  # SKIN   кожа
    (0xB0, 0x52, 0x44),  # TAN    тень кожи и красного: терракота
    (0xF4, 0xCB, 0x52),  # GOLD   монета, огонь фонаря, накладки
    (0xB2, 0x76, 0x2E),  # BRASS  тень золота, дерево, бамбук
    (0x78, 0x7A, 0x8A),  # METAL  камень, сталь
    (0x35, 0x31, 0x43),  # DARK   чёрный лак, маска врага, таби
    (0xD9, 0x36, 0x32),  # RED    шарф, чужой клан, солнце знамени
    (0x6F, 0xA9, 0x4B),  # VIOLET мох, жаба, хвоя на свету
    (0x27, 0x56, 0x40),  # PLUM   тень зелени, сосны
]
# Красное в таблицу не входит: тонкий шарф от неё дробится, светотень ему дают рампы.
SHADOW = {SEA: NAVY, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, GOLD: BRASS, METAL: DARK,
          VIOLET: PLUM}
# Материалы для светотени рампами: синяя ткань героя, белое, камень и сталь с чёрным лаком,
# кожа, золото с деревом, красная ткань, зелень, закатный свет.
GROUPS = {SEA: "cloth", NAVY: "cloth", WHITE: "white", GREY: "stone", METAL: "stone", DARK: "stone",
          SKIN: "skin", RED: "red", TAN: "red", GOLD: "gold", BRASS: "gold", VIOLET: "green",
          PLUM: "green", AQUA: "glow", SKY: "glow"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


def _danger(c):
    """Враг тропы, которого нельзя убить: тень как у всех, обводка красная."""
    c.shade()
    c.outline(RED)
    return c


# --- Ниндзя ------------------------------------------------------------------------------------
# Силуэт: голова в капюшоне без шлема и ранца, за затылком вилка из двух концов шарфа, над
# плечом наискось торчит рукоять меча, корпус узкий, штаны широкие до колена, ниже белые обмотки
# и тёмные таби. Центр головы, бёдра и ступни стоят там же, где у матроса и космонавта.

def _ribbon(c, pts, col):
    """Лента в два пикселя по ломаной: вдоль горизонтали толщина идёт вниз, вдоль вертикали вбок."""
    for a, b in zip(pts, pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
        flat = abs(b[0] - a[0]) >= abs(b[1] - a[1])
        for i in range(n + 1):
            x = int(round(a[0] + (b[0] - a[0]) * i / n))
            y = int(round(a[1] + (b[1] - a[1]) * i / n))
            c.set(x, y, col)
            c.set(x, y + 1, col) if flat else c.set(x + 1, y, col)


def _tails(c, x, y, t, u=(-1.0, 0.0), amp=1.0, lens=(10, 8), spread=0.45):
    """Два конца шарфа от узла (x, y) вдоль `u`: верхний идёт прямо, нижний отходит вилкой, оба
    волной по фазе `t`."""
    n = math.hypot(u[0], u[1])
    ux, uy = u[0] / n, u[1] / n
    for j, length in enumerate(lens):
        side = 0.12 if j == 0 else -1.0
        pts = []
        for k in range(length + 1):
            off = side * spread * k + math.sin(k * 0.7 - t + j * 0.9) * amp * k / length
            pts.append((x + ux * k - uy * off, y + j + uy * k + ux * off))
        _ribbon(c, pts, RED)


def _hilt(c, x, y):
    """Рукоять короткого меча над плечом, наискось вверх и назад от (x, y): цуба золотом,
    оплётка тёмная с просветом, навершие золотом."""
    for k in range(8):
        px = x - int(round(k * 0.55))
        col = GOLD if k in (0, 7) else (DARK if k % 2 else METAL)
        c.set(px, y - k, col)
        c.set(px - 1, y - k, col)
    c.set(x + 1, y, GOLD)
    c.set(x - 2, y, GOLD)


def _head(c, x, y):
    """Голова в капюшоне, лицом вправо: прорезь глаз в два ряда кожи, глаз ставится после
    обводки (`_eye`). Центр (x, y), радиус 5, как голова матроса."""
    c.ellipse(x, y, 5, 5, SEA)
    for yy in (y - 1, y):
        for xx in range(x, x + 6):
            if c.get(xx, yy) == SEA:
                c.set(xx, yy, SKIN)
    # Складка капюшона на затылке.
    c.set(x - 3, y + 2, NAVY)
    c.set(x - 2, y + 3, NAVY)


def _eye(c, x, y):
    c.set(x + 3, y - 1, K)
    c.set(x + 3, y, K)
    c.set(x + 5, y - 1, TAN)


def _wrap(c, x, y):
    """Шарф вокруг шеи: закрывает подбородок и ворот."""
    c.ellipse(x + 0.5, y + 5, 4.3, 1.5, RED)


def _torso(c, x0, y0, x1, y1):
    """Корпус: синяя куртка с запахом, ремень меча наискось, тёмный пояс."""
    c.rect(x0, y0, x1, y1, SEA)
    c.line(x1 - 1, y0 + 1, x1 - 3, y1 - 2, NAVY, 1)
    c.line(x0, y0 + 2, x1, y1 - 3, BRASS, 1)
    c.rect(x0, y1 - 1, x1, y1, DARK)


def _tabi(c, x, y):
    c.rect(x - 1, y, x + 3, y + 1, DARK)


def _leg(c, hx, hy, kx, ky, fx, fy, near, shin=3):
    """Нога: широкая штанина до колена, ниже обмотка (белая у ближней, серая у дальней), таби."""
    c.line(hx, hy, kx, ky, SEA if near else NAVY, 4)
    sx, sy = kx + (fx - kx) * 0.15, ky + (fy - ky) * 0.15
    c.line(sx, sy, fx, fy, WHITE if near else GREY, shin)
    _tabi(c, fx, fy)


def _arm(c, x0, y0, x1, y1, near):
    """Рукав с кистью. Ближний рукав отбит от куртки тёмной линией снизу."""
    if near:
        c.line(x0, y0 + 1, x1 - 1, y1 + 1, NAVY, 3)
    c.line(x0, y0, x1, y1, SEA if near else NAVY, 3)
    hx, hy = int(round(x1)), int(round(y1))
    c.rect(hx, hy, hx + 1, hy + 1, SKIN)


def ninja_side(phase, jump=False):
    """Ниндзя сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _tails(c, 12, 12 - bob, phase, u=(-1.0, -0.3) if jump else (-1.0, 0.05))
    _hilt(c, 10, 10 - bob)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), False)
    for sign in (-1, 1):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        _leg(c, 15 + sign, hip_y, knee[0], knee[1], foot[0], foot[1], sign > 0)
    _torso(c, 12, 12 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), True)
    _head(c, 16, 7 - bob)
    _wrap(c, 16, 7 - bob)
    c.finish()
    _eye(c, 16, 7 - bob)
    return c


def ninja_back(phase):
    """Со спины: бежит вглубь экрана, меч наискось через всю спину, концы шарфа сбоку на ветру."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        near = sign > 0
        c.rect(x - 2, 21 - bob, x + 1, 24 - lift * 0.5, SEA if near else NAVY)
        c.rect(x - 2, 25 - lift * 0.5, x + 1, 27 - lift, WHITE if near else GREY)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
        _arm(c, 16 + sign * 5, 15 - bob, 16 + sign * 6, 20 - bob + s * sign * 2, False)
        c.line(16 + sign * 5, 14 - bob, 16 + sign * 6, 18 - bob + s * sign * 2, SEA, 3)
    c.rect(12, 12 - bob, 19, 21 - bob, SEA)
    c.rect(12, 20 - bob, 19, 21 - bob, DARK)
    # Ножны через спину от правого плеча к левому бедру, рукоять выше плеча.
    c.line(20, 11 - bob, 11, 21 - bob, DARK, 2.4)
    c.set(11, 21 - bob, GOLD)
    c.set(10, 22 - bob, GOLD)
    for k in range(6):
        col = GOLD if k in (0, 5) else (METAL if k == 3 else DARK)
        c.set(21 + int(round(k * 0.6)), 10 - bob - k, col)
        c.set(22 + int(round(k * 0.6)), 10 - bob - k, col)
    c.set(20, 9 - bob, GOLD)
    c.set(23, 11 - bob, GOLD)
    c.ellipse(15.5, 7 - bob, 5, 5, SEA)
    c.set(13, 5 - bob, NAVY)
    c.set(18, 5 - bob, NAVY)
    c.rect(15, 3 - bob, 16, 9 - bob, NAVY)
    c.rect(11, 11 - bob, 19, 12 - bob, RED)
    c.rect(11, 11 - bob, 12, 13 - bob, RED)
    _tails(c, 11, 12 - bob, phase, u=(-1.0, 0.3), lens=(7, 6), amp=1.0, spread=0.3)
    return c.finish()


def ninja_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    wind = ((-1.0, 0.25), (-1.0, 0.5), (-1.0, -0.1), (-1.0, -0.6))[i]
    _tails(c, 12, 12 + crouch, i * 1.5, u=wind)
    _hilt(c, 10, 10 + crouch)
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, False)
    for sign in (-1, 1):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        _leg(c, 15 + sign, hip_y, knee[0], knee[1], foot[0], foot[1], sign > 0)
    _torso(c, 12, 12 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, True)
    _head(c, 16, 7 + crouch)
    _wrap(c, 16, 7 + crouch)
    c.finish()
    _eye(c, 16, 7 + crouch)
    return c


def ninja_idle(i):
    """Стойка: два кадра, ниндзя дышит, концы шарфа висят за спиной и качаются."""
    c = Canvas()
    up = i
    _tails(c, 12, 11 - up, i * 2.2, u=(-0.75, 1.0), lens=(9, 7), amp=0.8, spread=0.22)
    _hilt(c, 10, 10 - up)
    for sign in (-1, 1):
        x = 15 + sign * 2
        near = sign > 0
        c.rect(x - 1, 21, x + 1, 24, SEA if near else NAVY)
        c.rect(x - 2, 22, x + 2, 24, SEA if near else NAVY)
        c.rect(x - 1, 25, x + 1, 28, WHITE if near else GREY)
        if near:
            c.set(x, 26, GREY)
        c.rect(x - 1, 29, x + 2, 30, DARK)
    _arm(c, 14, 15 - up, 13, 20 - up, False)
    _torso(c, 12, 12 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 20 - up, True)
    _head(c, 16, 7 - up)
    _wrap(c, 16, 7 - up)
    c.finish()
    _eye(c, 16, 7 - up)
    return c


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = DARK if k >= int(n) - 1 else SEA
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def ninja_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх, рука
    сзади на земле, шарф рвёт назад. Верх кадра на той же строке, что у космонавта. Два кадра."""
    c = Canvas()
    _tails(c, 6, 23, i * 2.0, u=(-1.0, -0.5), lens=(4, 4), amp=0.6, spread=0.5)
    # Дальняя нога коленом вверх.
    c.line(19, 27, 24, 23 - i, NAVY, 4)
    c.line(24.5, 24 - i, 27, 27, GREY, 3)
    _tabi(c, 27, 28)
    _arm(c, 13, 24, 19, 23, False)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(13, 23, 18, 27, BRASS, 1)
    # Ближняя нога вытянута: штанина, обмотка, таби носком вперёд.
    c.line(19, 28, 23, 28, SEA, 4)
    c.line(24, 28.4, 28, 28.4, WHITE, 3)
    c.set(26, 28, GREY)
    c.rect(28, 27, 30, 29, DARK)
    _arm(c, 11, 25, 6, 29, True)
    _head(c, 10, 21)
    _wrap(c, 10, 21)
    c.finish()
    _eye(c, 10, 21)
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def ninja_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    _tails(c, 12, 23, i * 2.2, u=(-1.0, 0.45), lens=(8, 6), amp=0.8, spread=0.25)
    _hilt(c, 10, 22)
    _arm(c, 15, 24, 19, 26, False)
    for sign in (-1, 1):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], SEA if sign > 0 else NAVY, 4)
        c.line(knee[0], knee[1] + 1, foot[0], foot[1], WHITE if sign > 0 else GREY, 3)
        _tabi(c, foot[0], foot[1])
    c.rect(12, 23, 18, 26, SEA)
    c.line(12, 23, 18, 26, BRASS, 1)
    _arm(c, 14, 24, 19, 26, True)
    _head(c, 16, 19)
    _wrap(c, 16, 19)
    c.finish()
    _eye(c, 16, 19)
    return c


def ninja_hang(i):
    """На верёвке: руки вверх к точке хвата (центр сверху), ноги свисают и качаются, концы шарфа
    падают вдоль спины."""
    c = Canvas()
    sw = (-1, 1)[i]
    _tails(c, 12, 12, i * 2.4, u=(-0.45 - 0.2 * sw, 1.0), lens=(10, 8), amp=0.7, spread=0.2)
    _hilt(c, 10, 11)
    c.line(14, 13, 15, 2, NAVY, 3)
    c.line(18, 13, 17, 2, SEA, 3)
    c.ellipse(15, 1.5, 1.3, 1.3, SKIN)
    c.ellipse(17, 1.5, 1.3, 1.3, SKIN)
    _torso(c, 12, 13, 19, 21)
    for sign in (-1, 1):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        mid = ((15.5 + sign * 2 + foot[0]) / 2, 25)
        c.line(15.5 + sign * 2, 21, mid[0], mid[1], SEA if sign > 0 else NAVY, 4)
        c.line(mid[0], mid[1] + 1, foot[0], foot[1], WHITE if sign > 0 else GREY, 3)
        c.rect(foot[0] - 1, foot[1], foot[0] + 2, foot[1] + 1, DARK)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    _wrap(hd, 16, 8)
    hd.finish()
    _eye(hd, 16, 8)
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Чужой клан --------------------------------------------------------------------------------
# Ниндзя в красном, лицом влево (навстречу герою): чёрная маска с завязками на затылке, чёрные
# голени, в поднятой руке серп кама. От героя отличается и без цвета: серп над головой впереди,
# нет шарфа и меча, ноги шире. Шаг и рост повторяют скелета пиратов.

def _kama(c, x, y, face=-1):
    """Серп: древко от кисти (x, y) вверх, наверху клюв лезвия в сторону `face`."""
    c.rect(x, y - 9, x + 1, y + 3, BRASS)
    c.set(x, y + 3, DARK)
    c.set(x + 1, y + 3, DARK)
    f = face
    bx = x if f < 0 else x + 1
    for dx, y0, y1 in ((0, -11, -10), (1, -11, -10), (2, -11, -10), (3, -11, -9), (4, -10, -8), (5, -9, -6),
                       (6, -7, -5)):
        for yy in range(y0, y1 + 1):
            c.set(bx + f * dx, y + yy, GREY)
    c.set(bx + f * 4, y - 8, WHITE)
    c.set(bx + f * 5, y - 6, WHITE)
    c.set(bx + f * 6, y - 5, WHITE)


def rival_side(phase):
    """Ниндзя чужого клана сбоку, лицом влево: шаг по фазе, серп в поднятой руке."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Завязки маски на затылке.
    _ribbon(c, [(20, 4 - bob), (23, 3 - bob + s), (25, 4 - bob + s)], DARK)
    _ribbon(c, [(20, 7 - bob), (23, 8 - bob - s), (24, 10 - bob - s)], DARK)
    c.line(17, 15 - bob, 18 + 4 * s, 20 - bob, TAN, 3)
    c.ellipse(18 + 4 * s, 20 - bob, 1.3, 1.3, DARK)
    for sign, col in ((-1, TAN), (1, RED)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1] + 1, foot[0], foot[1], DARK, 3)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, DARK)
    # Корпус: красная куртка с запахом, чёрный пояс с золотой пряжкой.
    c.rect(12, 12 - bob, 18, 21 - bob, RED)
    c.line(13, 13 - bob, 15, 18 - bob, TAN, 1)
    c.rect(12, 20 - bob, 18, 21 - bob, DARK)
    c.set(13, 20 - bob, GOLD)
    # Рука с серпом поднята вперёд, качается на шаг.
    hy = 14 - bob - int(round(s))
    _kama(c, 8, hy)
    c.line(15, 15 - bob, 10, hy + 2, TAN, 3)
    c.line(15, 14 - bob, 10, hy + 1, RED, 3)
    c.ellipse(9, hy + 1, 1.4, 1.4, DARK)
    # Голова в чёрной маске, прорезь глаз.
    c.ellipse(16, 6 - bob, 5, 4.6, DARK)
    for yy, x0, x1 in ((5 - bob, 12, 15), (6 - bob, 11, 15)):
        c.rect(x0, yy, x1, yy, SKIN)
    c.finish()
    c.set(13, 6 - bob, K)
    c.set(13, 5 - bob, K)
    c.set(12, 5 - bob, DARK)
    return c


def rival_front(phase):
    """Ниндзя чужого клана лицом к камере: идёт на игрока, серп занесён над плечом."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 24 - lift * 0.5, RED)
        c.rect(x - 2, 25 - lift * 0.5, x + 1, 27 - lift, DARK)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
    # Правая рука (слева в кадре) с серпом, левая со сжатым кулаком.
    hy = 14 - bob - int(round(s))
    _kama(c, 8, hy)
    c.line(11, 14 - bob, 9, hy + 2, RED, 3)
    c.ellipse(9, hy + 1, 1.4, 1.4, DARK)
    c.line(21, 14 - bob, 23, 19 - bob + s * 2, RED, 3)
    c.ellipse(23, 20 - bob + s * 2, 1.4, 1.4, DARK)
    c.rect(12, 12 - bob, 19, 21 - bob, RED)
    c.line(13, 12 - bob, 16, 17 - bob, TAN, 1)
    c.line(18, 12 - bob, 15, 17 - bob, TAN, 1)
    c.rect(12, 20 - bob, 19, 21 - bob, DARK)
    c.rect(15, 20 - bob, 16, 21 - bob, GOLD)
    # Маска: чёрная голова, завязки торчат в стороны, прорезь с двумя глазами.
    _ribbon(c, [(20, 4 - bob), (23, 3 - bob + s)], DARK)
    _ribbon(c, [(20, 6 - bob), (24, 7 - bob - s)], DARK)
    c.ellipse(15.5, 6 - bob, 5.5, 4.6, DARK)
    c.rect(11, 5 - bob, 20, 6 - bob, SKIN)
    c.finish()
    # Брови сходятся к переносице, зрачки смотрят на игрока.
    c.rect(14, 5 - bob, 17, 5 - bob, DARK)
    c.rect(15, 6 - bob, 16, 6 - bob, DARK)
    c.set(13, 6 - bob, K)
    c.set(18, 6 - bob, K)
    return c


# --- Летун и ползун ----------------------------------------------------------------------------

def _beak(x, y, cy):
    """Пиксель внутри клюва ворона (тело на высоте `cy`)."""
    if not 25 <= x <= 31:
        return False
    k = (x - 25) / 6.0
    return cy - 6 + 2 * k <= y <= cy - 2 - k or (x == 30 and y == cy - 2)


def raven(i):
    """Ворон-тэнгу летит вправо: чёрная птица с длинным красным клювом-носом, на лбу шапочка
    токин; крылья машут (вверх, середина, вниз, середина). Тело по центру
    кадра, чтобы при развороте не прыгало."""
    c = Canvas()
    wing = (-9, -3, 6, -3)[i]
    dip = (1, 0, -1, 0)[i]
    y = 17 + dip
    # Хвост веером.
    c.poly([(2, y - 2), (9, y - 1), (9, y + 3), (3, y + 4)], DARK)
    c.line(3, y + 1, 8, y + 1, METAL, 1)
    # Лапы поджаты.
    c.rect(13, y + 5, 14, y + 6, GOLD)
    c.rect(17, y + 5, 18, y + 6, GOLD)
    # Тело и голова.
    c.ellipse(15, y + 1, 7.5, 4.6, DARK)
    c.ellipse(22, y - 4, 4.4, 4.2, DARK)
    # Клюв тэнгу: длинный, красный, кончик загнут.
    c.poly([(25, y - 6), (31, y - 4), (31, y - 3), (25, y - 2)], RED)
    c.set(30, y - 2, RED)
    # Шапочка токин.
    c.rect(21, y - 10, 23, y - 9, GOLD)
    # Крыло: широкий веер с пальцами перьев.
    tip = y - 1 + wing
    c.poly([(10, y - 1), (19, y - 1), (17, tip), (7, tip)], METAL)
    for k, x in enumerate((7, 10, 13, 16)):
        c.line(x, tip, x - 1, tip + (2 if wing > 0 else -2), METAL, 2)
    c.line(11, y - 1, 9, tip, DARK, 1)
    c.line(15, y - 1, 13, tip, DARK, 1)
    _danger(c)
    # Клюв в чёрной обводке, иначе сливается с красной обводкой врага.
    for by in range(32):
        for bx in range(25, 32):
            if c.get(bx, by) == RED and any(c.get(bx + dx, by + dy) in (RED, TAN) and 25 <= bx + dx and y - 6 <= by + dy <= y - 2
                                            and _beak(bx + dx, by + dy, y) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                if not _beak(bx, by, y):
                    c.set(bx, by, K)
    # Глаз: жёлтый с зрачком.
    c.set(23, y - 5, GOLD)
    c.set(24, y - 5, K)
    c.set(26, y - 5, WHITE)
    return c


def toad(i):
    """Жаба-ползун анфас, четыре кадра: приседает и подаётся вверх, горло раздувается, передние
    лапы переступают. Лапы всегда на земле."""
    c = Canvas()
    up = (0, 1, 2, 1)[i]
    puff = (0, 0, 1.5, 0.5)[i]
    step = (0, 1, 0, -1)[i]
    # Задние лапы сложены по бокам.
    for sign in (-1, 1):
        c.ellipse(16 + sign * 10, 25 - up * 0.5, 3.5, 3.5, PLUM)
        c.rect(16 + sign * 11 - 2, 28, 16 + sign * 11 + 2, 29, VIOLET)
    # Тело: широкая лепёшка, светлое брюхо.
    c.ellipse(16, 22 - up, 10.5, 6.5, VIOLET)
    c.ellipse(16, 25 - up, 6 + puff, 3.6 + puff * 0.5, SKY)
    # Бугры глаз.
    for sign in (-1, 1):
        c.ellipse(16 + sign * 5.5, 15 - up, 3.2, 3.2, VIOLET)
    # Передние лапы с пальцами.
    for sign in (-1, 1):
        fx = 16 + sign * 6 + (step if sign > 0 else -step) * sign
        c.line(16 + sign * 7, 24 - up, fx, 28, VIOLET, 3)
        c.rect(fx - 2, 28, fx + 2, 29, VIOLET)
    # Бородавки.
    for x, y in ((9, 20), (23, 21), (13, 17), (20, 18), (16, 16)):
        c.set(x, y - up, PLUM)
    _danger(c)
    # Глаза: золотые с горизонтальным зрачком, рот широкой дугой.
    for sign in (-1, 1):
        ex = int(round(16 + sign * 5.5))
        c.rect(ex - 1, 14 - up, ex + 1, 15 - up, GOLD)
        c.rect(ex - 1, 15 - up, ex + 1, 15 - up, K)
        c.set(ex, 14 - up, GOLD)
    c.rect(9, 20 - up, 23, 20 - up, K)
    c.set(8, 19 - up, K)
    c.set(24, 19 - up, K)
    c.set(14, 18 - up, K)
    c.set(18, 18 - up, K)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Монета с квадратным отверстием вращается: шесть кадров, ширина по косинусу, в ребро
    отверстия не видно."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 8.0)
    cx, cy = 15.5, 16
    c.ellipse(cx, cy, rx, 8, GOLD)
    if rx > 4:
        c.ellipse(cx, cy, rx - 1.2, 6.8, BRASS)
        c.ellipse(cx, cy, rx - 2.2, 5.8, GOLD)
    hw = int(round(2 * rx / 8.0))
    if hw >= 1:
        c.rect(16 - hw, 14, 15 + hw, 17, None)
        # Знаки над и под отверстием.
        if hw >= 2:
            for dy in (-4, 4):
                c.rect(15, cy + dy, 16, cy + dy, BRASS)
            for dx in (-5, 4):
                c.rect(15.5 + dx, 15, 15.5 + dx, 16, BRASS)
    c.finish()
    if rx > 4:
        c.set(cx - rx * 0.55, 11, WHITE)
        c.set(cx - rx * 0.55 - 1, 12, WHITE)
    return c


def flag(i):
    """Нобори: узкое белое знамя на бамбуковом шесте с перекладиной, красный круг и чёрные
    знаки; свободный край идёт волной."""
    c = Canvas()
    c.rect(5, 2, 6, 31, BRASS)
    for y in (8, 15, 22, 29):
        c.rect(5, y, 6, y, GOLD)
    c.ellipse(5.5, 1.5, 1.5, 1.5, GOLD)
    c.rect(5, 4, 22, 4, BRASS)

    def ripple(y):
        return math.sin(y * 0.5 - i * math.pi / 3.0) * 1.5 * (0.25 + 0.75 * (y - 5) / 22.0)

    for y in range(5, 28):
        right = int(round(20 + ripple(y)))
        c.rect(8, y, right, y, WHITE)
        # Складка: где край уходит внутрь, полотно в тени.
        if math.cos(y * 0.5 - i * math.pi / 3.0) < -0.35:
            c.set(right - 2, y, GREY)
            c.set(right - 3, y, GREY)
    # Петли к шесту.
    for y in (7, 13, 19, 25):
        c.set(7, y, RED)
    c.shade()
    c.outline()
    mid = ripple(11) * 0.5
    c.ellipse(14 + mid, 10.5, 3.6, 3.6, RED)
    # Знаки тушью под кругом.
    for x0, y0, x1, y1 in ((12, 17, 16, 17), (14, 16, 14, 20), (12, 22, 16, 22), (13, 20, 15, 20), (14, 22, 14, 25),
                           (12, 25, 13, 25), (16, 24, 16, 25)):
        d = int(round(ripple((y0 + y1) / 2) * 0.5))
        c.rect(x0 + d, y0, x1 + d, y1, K)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    return c.finish()


# Глубина мха по столбцам плитки и швы камней по рядам: плитка стыкуется сама с собой.
_MOSS = (3, 3, 4, 5, 4, 3, 3, 2, 3, 4, 6, 5, 3, 3, 2, 3, 3, 4, 4, 3, 5, 6, 4, 3, 3, 2, 3, 4, 5, 3, 3, 3)
_JOINTS = ((0, 11, 22), (6, 17, 27), (2, 13, 24), (9, 19, 29))


def ground(inner=False):
    """Каменная дорожка: тёсаные плиты в перевязку, в швах мох; у кромки моховая шапка с
    потёками. Внутренняя плитка без шапки."""
    c = Canvas()
    c.rect(0, 0, 31, 31, DARK)
    for band, joints in enumerate(_JOINTS):
        y0 = band * 8
        for n, x in enumerate(joints):
            w = (joints[(n + 1) % 3] - x) % 32
            light = (band * 2 + n) % 3 == 0
            for dx in range(1, w):
                xx = (x + dx) % 32
                for y in range(y0, y0 + 7):
                    corner = dx in (1, w - 1) and y in (y0, y0 + 6)
                    if corner:
                        continue
                    col = GREY if light else METAL
                    if y == y0 and not light:
                        col = GREY
                    if y == y0 + 6 and light:
                        col = METAL
                    c.set(xx, y, col)
            # Трещина и щербина на каждой плите.
            c.set((x + 3 + band) % 32, y0 + 3, DARK if not light else METAL)
            c.set((x + 4 + band) % 32, y0 + 4, DARK if not light else METAL)
            # Мох в шве.
            c.set(x, y0 + 5, PLUM)
            c.set(x, y0 + 6, VIOLET if (band + n) % 2 == 0 else PLUM)
            c.set((x + 1 + w // 2) % 32, y0 + 7, PLUM)
    if not inner:
        for x, d in enumerate(_MOSS):
            c.rect(x, 0, x, d, PLUM)
            c.rect(x, 0, x, 1, VIOLET)
            if (x * 7) % 5 == 0:
                c.set(x, 2, VIOLET)
            if (x * 3) % 11 == 0:
                c.set(x, 0, SKY)
            c.set(x, d + 1, DARK)
    return c


def rock():
    """Каменный фонарь торо: навершие, шляпа с загнутыми углами, домик с огнём в окне, полка,
    ножка и плита основания; на камне мох."""
    c = Canvas()
    c.ellipse(16, 3.6, 1.7, 2.1, GREY)
    c.poly([(13, 6), (19, 6), (28, 12), (4, 12)], GREY)
    c.rect(3, 11, 4, 11, GREY)
    c.rect(28, 11, 29, 11, GREY)
    c.set(2, 10, GREY)
    c.set(30, 10, GREY)
    c.rect(6, 13, 26, 13, METAL)
    c.rect(10, 14, 22, 20, METAL)
    c.rect(13, 15, 19, 19, GOLD)
    c.rect(14, 16, 18, 19, SKY)
    c.rect(15, 17, 17, 19, WHITE)
    c.rect(8, 21, 24, 22, GREY)
    c.rect(13, 23, 19, 25, METAL)
    c.rect(7, 26, 25, 28, GREY)
    # Мох на шляпе и основании.
    for x, y in ((8, 10), (9, 10), (10, 9), (22, 10), (8, 26), (9, 26), (10, 26), (23, 26)):
        c.set(x, y, VIOLET)
    c.set(9, 11, PLUM)
    c.set(9, 27, PLUM)
    return c.finish()


def chest():
    """Чёрный лаковый ларец: крышка с выносом, золотые уголки и гербы, красный шнур
    крест-накрест с бантом и кистями."""
    c = Canvas()
    c.rect(4, 14, 27, 28, DARK)
    c.poly([(4, 9), (27, 9), (29, 11), (29, 14), (2, 14), (2, 11)], DARK)
    # Блик лака.
    c.rect(5, 10, 12, 10, METAL)
    c.rect(5, 16, 5, 22, METAL)
    c.rect(2, 14, 29, 14, K)
    # Золотые уголки и ножки.
    for x in (4, 26):
        c.rect(x, 26, x + 1, 28, GOLD)
        c.rect(x, 15, x + 1, 16, GOLD)
    c.rect(2, 12, 3, 13, GOLD)
    c.rect(28, 12, 29, 13, GOLD)
    # Гербы золотом на стенке.
    for x in (8, 22):
        for dx, dy in ((1, 0), (0, 1), (2, 1), (1, 2)):
            c.set(x + dx, 22 + dy, GOLD)
    # Шнур: вокруг ларца и через крышку, бант спереди.
    c.rect(15, 9, 16, 19, RED)
    c.rect(4, 19, 27, 20, RED)
    c.ellipse(12.5, 19.5, 2.4, 2.0, RED)
    c.ellipse(18.5, 19.5, 2.4, 2.0, RED)
    c.set(12, 19, DARK)
    c.set(19, 19, DARK)
    c.rect(14, 21, 14, 25, RED)
    c.rect(17, 21, 17, 25, RED)
    c.rect(13, 25, 14, 26, GOLD)
    c.rect(17, 25, 18, 26, GOLD)
    return c.finish()


def key():
    """Ключ: головка как монета с квадратным отверстием, бородка в два зуба, красная кисть."""
    c = Canvas(32, 32)
    c.ellipse(9.5, 14.5, 5.6, 5.6, GOLD)
    c.rect(8, 13, 11, 16, None)
    c.rect(14, 14, 28, 15, GOLD)
    c.rect(22, 16, 23, 19, GOLD)
    c.rect(26, 16, 27, 20, GOLD)
    c.rect(17, 13, 18, 16, BRASS)
    # Кисть на шнуре.
    c.line(7, 19, 6, 23, RED, 1)
    c.rect(4, 23, 7, 28, RED)
    c.rect(4, 24, 7, 24, WHITE)
    c.finish()
    c.set(6, 11, WHITE)
    c.set(7, 10, WHITE)
    return c


def medkit():
    """Аптечка: деревянный ящичек лекаря с железной ручкой и ящиком, на бумажном ярлыке красный
    крест."""
    c = Canvas(32, 32)
    c.rect(5, 11, 26, 28, BRASS)
    c.rect(4, 10, 27, 12, GOLD)
    # Ручка.
    c.rect(11, 5, 20, 6, METAL)
    c.rect(11, 5, 12, 9, METAL)
    c.rect(19, 5, 20, 9, METAL)
    # Железные уголки.
    for x in (5, 25):
        c.rect(x, 26, x + 1, 28, DARK)
        c.rect(x, 13, x + 1, 14, DARK)
    c.rect(6, 20, 9, 20, DARK)
    c.rect(22, 20, 25, 20, DARK)
    # Ярлык с крестом.
    c.rect(10, 14, 21, 26, WHITE)
    c.rect(14, 15, 17, 25, RED)
    c.rect(11, 18, 20, 21, RED)
    return c.finish()


def shot():
    """Снаряд чужого клана: сюрикен в четыре луча с красным кольцом у отверстия, обводка красная."""
    c = Canvas(16, 16)
    c.poly([(7.5, 1), (9.6, 5.4), (14, 7.5), (9.6, 9.6), (7.5, 14), (5.4, 9.6), (1, 7.5), (5.4, 5.4)], GREY)
    c.rect(7, 1, 8, 14, GREY)
    c.rect(1, 7, 14, 8, GREY)
    c.rect(6, 6, 9, 9, RED)
    c.rect(7, 7, 8, 8, K)
    c.set(7, 3, WHITE)
    c.set(3, 7, WHITE)
    c.set(6, 5, WHITE)
    return _danger(c)


# --- Параллакс ---------------------------------------------------------------------------------
# Небо демка красит сама полосами NAVY, SEA, AQUA, SKY; ниже горизонта заливка SEA. Поэтому
# облака лежат в верхних полосах, силуэты дальнего слоя тёмные на золоте, а ближний слой внизу
# сходит в озеро цвета SEA.

def par_sky():
    """Дальний слой: длинные закатные облака, подсвеченные снизу, и стая ворон; лента 256×48,
    стыкуется по краям."""
    c = Canvas(256, 48)
    for cx, cy, ln, th in ((34, 12, 30, 2.6), (96, 30, 22, 2.0), (150, 18, 36, 3.2), (214, 36, 26, 2.2),
                           (236, 8, 20, 1.8), (70, 41, 16, 1.6)):
        for k in (0, 256, -256):
            c.ellipse(cx + k, cy, ln, th, AQUA)
            c.ellipse(cx + k - ln * 0.45, cy + 1.5, ln * 0.55, th * 0.7, AQUA)
            c.ellipse(cx + k + ln * 0.5, cy - 1.5, ln * 0.45, th * 0.6, AQUA)
    src = [row[:] for row in c.px]
    for y in range(48):
        for x in range(256):
            if src[y][x] is None:
                continue
            if y + 1 >= 48 or src[y + 1][x] is None:
                c.px[y][x] = SKY
            elif y == 0 or src[y - 1][x] is None:
                c.px[y][x] = TAN
    # Вороны галочками.
    for x, y in ((120, 6), (127, 9), (114, 10), (190, 26), (197, 24)):
        for dx, dy in ((-2, -1), (-1, 0), (0, 1), (1, 0), (2, -1)):
            c.set(x + dx, y + dy, K)
    return c


def _wrap_d(x, at):
    d = abs(x - at) % 256
    return min(d, 256 - d)


def _cliff_h(x):
    """Утёс замка: слева обрыв, сверху площадка, справа склон."""
    if 54 <= x <= 88:
        return 20.0
    if 44 <= x < 54:
        return 20.0 * ((x - 44) / 10.0) ** 0.6
    if 88 < x <= 110:
        return 20.0 * (1.0 - (x - 88) / 22.0) ** 1.4
    return 0.0


def _near_h(x):
    """Ближние тёмные холмы дальнего слоя: утёс, холм пагоды, низкая гряда."""
    hill = 14.0 * max(0.0, math.cos(_wrap_d(x, 160) * math.pi / 76.0)) ** 2 if _wrap_d(x, 160) < 38 else 0.0
    return max(_cliff_h(x), hill, 4.0 + 2.0 * math.sin(x * math.pi / 32.0))


def par_far():
    """Средний слой: гора со снежной шапкой в дымке, замок на утёсе, пагода на холме; лента
    256×48, низ сплошной."""
    c = Canvas(256, 48)
    # Дальняя гряда и гора в дымке.
    for x in range(256):
        d = _wrap_d(x, 216)
        cone = 35.0 * max(0.0, 1.0 - d / 62.0) ** 2.1 if d > 3 else 31.5
        h = max(cone, 9 + 4 * math.sin(x * math.pi / 64.0) + 2 * math.sin(x * math.pi / 16.0 + 1.0))
        top = 47 - int(h)
        c.rect(x, top, x, 47, SEA)
        if cone >= 25.0:
            c.rect(x, top, x, top + int(cone - 25.0) - (x % 3 == 0) * 2, WHITE)
            if x > 217:
                c.set(x, top, GREY)
                c.set(x, top + 1, GREY)
    # Тёмные холмы.
    for x in range(256):
        top = 47 - int(round(_near_h(x)))
        c.rect(x, top, x, 47, NAVY)
    # Слои породы на обрыве.
    for x, y, n in ((47, 40, 5), (50, 34, 4), (49, 44, 7), (92, 36, 5), (97, 42, 6), (53, 30, 3)):
        c.rect(x, y, x + n, y, SEA)
    # Замок: каменное основание, три яруса, крыши с загнутыми углами, рыбы на коньке.
    c.poly([(60, 27), (82, 27), (80, 22), (62, 22)], NAVY)
    for x, y in ((63, 24), (67, 25), (72, 23), (76, 25), (79, 24)):
        c.set(x, y, SEA)
    for y0, x0, x1 in ((19, 62, 80), (15, 65, 77), (11, 68, 74)):
        c.rect(x0, y0, x1, y0 + 2, SEA)
        c.rect(x0 - 3, y0 - 1, x1 + 3, y0 - 1, NAVY)
        c.rect(x0 - 1, y0 - 2, x1 + 1, y0 - 2, NAVY)
        c.set(x0 - 4, y0 - 2, NAVY)
        c.set(x1 + 4, y0 - 2, NAVY)
    c.rect(68, 8, 74, 8, NAVY)
    c.rect(70, 7, 72, 7, NAVY)
    c.set(68, 7, GOLD)
    c.set(74, 7, GOLD)
    for x, y in ((65, 20), (69, 20), (73, 20), (77, 20), (68, 16), (71, 16), (74, 16), (71, 12)):
        c.set(x, y, GOLD)
    # Пагода: пять ярусов, красные стены, шпиль с кольцами.
    base_y = 47 - int(round(_near_h(160)))
    for k in range(5):
        yb = base_y - 4 * k
        hw = 4 - k // 2
        c.rect(160 - hw, yb - 1, 160 + hw, yb, RED)
        c.rect(160 - hw, yb - 2, 160 + hw, yb - 2, NAVY)
        rw = 8 - k
        c.rect(160 - rw, yb - 3, 160 + rw, yb - 3, NAVY)
        c.set(160 - rw - 1, yb - 4, NAVY)
        c.set(160 + rw + 1, yb - 4, NAVY)
        c.set(160, yb, GOLD if k == 0 else NAVY)
    top = base_y - 20
    c.rect(160, top - 7, 160, top, NAVY)
    for y in (top - 2, top - 4):
        c.rect(159, y, 161, y, NAVY)
    c.set(160, top - 8, GOLD)
    # Сосенки на гребнях.
    for px in (8, 26, 57, 86, 118, 134, 184, 198, 240):
        y = 47 - int(round(_near_h(px)))
        c.rect(px, y - 5, px, y, NAVY)
        for k, w in enumerate((1, 2, 3)):
            c.rect(px - w, y - 5 + k * 2, px + w, y - 5 + k * 2, PLUM)
    # Дымка у подножия: тёмное сходит в цвет воды.
    for x in range(256):
        if (x + 1) % 4 == 0:
            c.set(x, 45, SEA)
        if x % 2 == 0:
            c.set(x, 46, SEA)
        c.set(x, 47, SEA)
    return c


def _pine(c, x, y, lean=1, big=True):
    """Японская сосна: гнутый ствол и плоские ярусы хвои. (x, y) подножие."""
    h = 12 if big else 8
    for k in range(h):
        bend = int(round(math.sin(k / float(h) * math.pi) * 2 * lean))
        c.set(x + bend, y - k, DARK)
        if k < 3:
            c.set(x + bend + 1, y - k, DARK)
    tiers = ((h, 0, 5), (h - 3, 3 * lean, 4), (h - 5, -3 * lean, 4)) if big else ((h, 0, 4), (h - 3, 2 * lean, 3))
    for dy, dx, rx in tiers:
        c.ellipse(x + dx, y - dy, rx, 1.7, PLUM)
        c.rect(x + dx - rx + 2, y - dy - 1, x + dx + rx - 3, y - dy - 1, VIOLET)


def par_mid():
    """Ближний слой: берег с соснами и воротами тории, под ним озеро с закатными бликами; лента
    256×32, низ сходит в заливку."""
    c = Canvas(256, 32)

    def crest(x):
        return int(round(17 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0 + 1.0)))

    for px, lean, big in ((14, 1, True), (44, -1, False), (72, 1, True), (150, -1, True), (171, 1, False),
                          (203, 1, True), (238, -1, False)):
        _pine(c, px, crest(px) + 1, lean, big)
    # Тории на бугре.
    tx, ty = 112, crest(112)
    c.rect(tx - 4, ty - 8, tx - 3, ty, RED)
    c.rect(tx + 3, ty - 8, tx + 4, ty, RED)
    c.rect(tx - 7, ty - 10, tx + 7, ty - 9, RED)
    c.set(tx - 8, ty - 11, RED)
    c.set(tx + 8, ty - 11, RED)
    c.rect(tx - 7, ty - 11, tx + 7, ty - 11, DARK)
    c.rect(tx - 5, ty - 6, tx + 5, ty - 6, RED)
    for x in range(256):
        top = crest(x)
        c.rect(x, top, x, 27, PLUM)
        c.set(x, top, VIOLET)
        if (x * 5 + top) % 7 == 0:
            c.set(x, top + 1, VIOLET)
        if (x * 3 + top * 5) % 13 == 0:
            c.set(x, top + 4 + x % 5, DARK)
        # Кромка берега и вода.
        c.set(x, 28, NAVY)
        c.rect(x, 29, x, 31, SEA)
    for x, y, n, col in ((6, 29, 5, AQUA), (30, 30, 7, SKY), (58, 29, 4, AQUA), (84, 31, 6, AQUA), (108, 29, 8, SKY),
                         (140, 30, 5, AQUA), (166, 29, 6, SKY), (196, 30, 4, AQUA), (222, 29, 7, AQUA), (246, 31, 5, SKY)):
        c.rect(x, y, x + n, y, col)
    return c


# --- Наборы и лист -----------------------------------------------------------------------------

def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, чужой клан, вещи, земля, три
    слоя дали."""
    return {
        "enemy_walk": strip([rival_side(p) for p in base.phases()]),
        "enemy_front": strip([rival_front(p) for p in base.phases()]),
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
        "hero_run": strip([ninja_side(p) for p in base.phases()]),
        "hero_jump": ninja_side(0.0, jump=True),
        "hero_leap": strip([ninja_leap(i) for i in range(4)]),
        "hero_idle": strip([ninja_idle(i) for i in range(2)]),
        "hero_back": strip([ninja_back(p) for p in base.phases()]),
        "hero_slide": strip([ninja_slide(i) for i in range(2)]),
        "hero_hang": strip([ninja_hang(i) for i in range(2)]),
        "hero_crouch": strip([ninja_crouch(i) for i in range(2)]),
    }


def extras():
    """Ленты, которые у пиратов и космоса лежат в модулях демок, а образцу сеттинга нужны уже
    на листе: летун и ползун тропы, ключ, аптечка и снаряд врага из «до выхода»."""
    return {
        "parrot_fly": strip([raven(i) for i in range(4)]),
        "crab_walk": strip([toad(i) for i in range(4)]),
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


def save_sheet(path, items, scale=3, pad=6, back=(0x1B, 0x1A, 0x33, 255), max_w=640):
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


def preview(path, scale=4, keys=None, back=(0x1B, 0x1A, 0x33, 255)):
    """Лист набора: лента на строку, как в игре, после светотени. `keys` оставляет только
    названные ленты, в названном порядке."""
    items = dict(sprites())
    items.update(extras())
    if keys:
        items = {k: items[k] for k in keys}
    save_sheet(path, shaded(items), scale, back=back)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        _scale = 4
        _keys = None
        for _arg in sys.argv[1:]:
            if _arg.startswith("--scale="):
                _scale = int(_arg.split("=", 1)[1])
            elif _arg.startswith("--keys="):
                _keys = [k for k in _arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], _scale, _keys)
