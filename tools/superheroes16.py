#!/usr/bin/env python3
"""Набор «Супергерои» для 16/32-bit, сравнительная версия основы (#137, состав в
`docs/specs/settings.md`): закатный город, свой герой в синем трико с жёлтым плащом, маской-домино
и хохолком, зелёно-серые роботы-приспешники с одним красным глазом. Те же ленты и кадры, что у
пиратов и космоса (`pixel_sprites16.py`, `space16.py`): позы, габариты и опора ног повторяют
космонавта, чтобы хитбоксы демок сходились, рисунок свой. Небо демки красится из палитры
(NAVY, SEA, AQUA, SKY сверху вниз), поэтому эти четыре роли и есть закат.

    python3 tools/superheroes16.py --preview out.png [--scale=4] [--keys=hero_run,coin]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Супергерои»: 16 цветов, индекс это та же роль, что у космоса и пиратов (ими рисуют HUD
# и мир демки). VIOLET и PLUM здесь корпус роботов: имя слота прежнее, цвет сеттинга.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x15, 0x11, 0x1F),  # K      обводка, маска-домино
    (0x25, 0x1D, 0x5E),  # NAVY   индиго: верх неба, тень трико, ближние небоскрёбы
    (0x2F, 0x58, 0xD6),  # SEA    синее трико, флаг, сумерки
    (0xEF, 0x6F, 0x7C),  # AQUA   коралл заката: облака, отсвет на стенах
    (0xFF, 0xD9, 0xA2),  # SKY    персиковый горизонт, свечение
    (0xF6, 0xF2, 0xEA),  # WHITE  блики, белок глаза, аптечка
    (0xB6, 0xB4, 0xC0),  # GREY   бетон, дирижабль
    (0xF2, 0xC2, 0x94),  # SKIN   кожа
    (0xBE, 0x78, 0x54),  # TAN    тень кожи, кирпич
    (0xFF, 0xD2, 0x3A),  # GOLD   плащ, сапоги, перчатки, звезда, огни окон
    (0xCE, 0x86, 0x1E),  # BRASS  тень жёлтого, ржавая арматура
    (0x76, 0x7C, 0x90),  # METAL  металл: клешни, кейс, дымка дальних домов
    (0x38, 0x39, 0x4E),  # DARK   тёмный металл, волосы, швы кладки
    (0xE4, 0x3A, 0x32),  # RED    глаз робота, сердце, опасность
    (0x88, 0xAA, 0x7E),  # VIOLET зелёно-серый корпус роботов
    (0x47, 0x66, 0x58),  # PLUM   тень корпуса
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: DARK, VIOLET: PLUM}
# Материалы для светотени рампами: трико одна ткань, жёлтое (плащ, сапоги, перчатки, звезда) одна,
# кожа, бетон с белым, металл с волосами, красное, корпус роботов, закатное свечение.
GROUPS = {SEA: "suit", NAVY: "suit", GOLD: "gold", BRASS: "gold", SKIN: "skin", TAN: "skin",
          WHITE: "stone", GREY: "stone", METAL: "metal", DARK: "metal", RED: "red",
          VIOLET: "bot", PLUM: "bot", AQUA: "glow", SKY: "glow"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


def _stamp(c, x, y, rows, col):
    """Рисунок по буквам: `#` ставит цвет, левый верхний угол в (x, y)."""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                c.set(x + dx, y + dy, col)


def _clip(c, y0, y1):
    """Стереть всё выше строки y0 и ниже y1 (плоские срезы у бочонков и куполов)."""
    for y in range(c.h):
        if y < y0 or y > y1:
            for x in range(c.w):
                c.px[y][x] = None


STAR7 = ("...#...",
         "...#...",
         "#######",
         ".#####.",
         "..###..",
         ".##.##.",
         ".#...#.")


# --- Герой -------------------------------------------------------------------------------------
# Силуэт: непокрытая голова с хохолком вперёд, плащ за спиной до колен (в беге летит назад
# клином с вырезом), узкая талия, сапоги с отворотом. Без цвета узнаётся по плащу и хохолку;
# цветом по жёлтому на синем, чёрной маске с белым глазом и звезде на груди.

def _head(c, x, y):
    """Голова лицом вправо, центр (x, y): тёмные волосы шапкой и на затылке, хохолок вперёд, нос."""
    c.ellipse(x, y, 4.6, 4.6, SKIN)
    for yy in range(y - 5, y + 3):
        for xx in range(x - 5, x + 6):
            if c.get(xx, yy) == SKIN and (yy <= y - 3 or (xx <= x - 3 and yy <= y + 1) or (xx <= x - 1 and yy <= y - 2)):
                c.set(xx, yy, DARK)
    c.rect(x - 1, y - 5, x + 3, y - 5, DARK)
    c.rect(x + 1, y - 6, x + 4, y - 6, DARK)
    c.set(x + 5, y + 1, SKIN)


def _face(c, x, y):
    """Маска-домино поверх готовой головы: чёрная полоса от виска до переносицы, белый глаз."""
    c.rect(x, y - 1, x + 4, y, K)
    c.set(x + 3, y - 1, WHITE)
    c.set(x + 3, y, WHITE)
    c.set(x + 3, y + 3, TAN)


def _cape(c, ax, ay, tx, ty, spread=7.0, flutter=0.0):
    """Плащ клином: от шеи (ax, ay) к концу (tx, ty), подол шириной `spread` с вырезом посередине."""
    a = (ax, ay)
    b = (ax - 2, ay + 7)
    t1 = (tx, ty - spread / 2.0)
    t2 = (tx + 1, ty + spread / 2.0)
    mid_top = ((a[0] + t1[0]) / 2.0, (a[1] + t1[1]) / 2.0 - 1 + flutter)
    notch = ((t1[0] + t2[0]) / 2.0 + 2.5, (t1[1] + t2[1]) / 2.0)
    mid_bot = ((b[0] + t2[0]) / 2.0, (b[1] + t2[1]) / 2.0 + 1 + flutter)
    c.poly([a, mid_top, t1, notch, t2, mid_bot, b], GOLD)
    # Складка: тёмная полоса вдоль плаща, от неё он читается тканью, а не щитом.
    c.line(a[0] - 3, a[1] + 4, notch[0] + 1, notch[1], BRASS, 1)


def _torso(c, y0, hip_y, x=0):
    """Корпус в трико: широкая грудь, узкая талия, жёлтый пояс, звезда на груди."""
    c.rect(11 + x, y0, 19 + x, y0 + 3, SEA)
    c.rect(12 + x, y0 + 4, 18 + x, hip_y, SEA)
    c.rect(12 + x, hip_y - 1, 18 + x, hip_y, GOLD)
    c.rect(15 + x, y0 + 1, 19 + x, y0 + 1, GOLD)
    c.rect(16 + x, y0 + 2, 18 + x, y0 + 2, GOLD)
    c.set(17 + x, y0, GOLD)
    c.set(16 + x, y0 + 3, GOLD)
    c.set(18 + x, y0 + 3, GOLD)


def _arm(c, x0, y0, x1, y1, near=True):
    """Рука: синий рукав, жёлтая перчатка до середины предплечья. Ближняя отбита тенью снизу."""
    col, glove = (SEA, GOLD) if near else (NAVY, BRASS)
    if near:
        c.line(x0, y0 + 1, x1, y1 + 1, NAVY, 3)
    c.line(x0, y0, x1, y1, col, 3)
    gx, gy = x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.62
    c.line(gx, gy, x1, y1, glove, 3)
    c.ellipse(x1, y1, 1.5, 1.5, glove)


def _leg(c, hip, knee, foot, near=True, sole=4):
    """Нога: бедро и голень в трико, сапог с отворотом от середины голени, ступня носком вправо."""
    col, boot = (SEA, GOLD) if near else (NAVY, BRASS)
    c.line(hip[0], hip[1], knee[0], knee[1], col, 4)
    c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
    bx, by = knee[0] + (foot[0] - knee[0]) * 0.45, knee[1] + (foot[1] - knee[1]) * 0.45
    c.ellipse(bx, by, 1.9, 1.5, boot)
    c.line(bx, by, foot[0], foot[1], boot, 3)
    c.rect(foot[0] - 1, foot[1], foot[0] + sole - 1, foot[1] + 1, boot)


def hero_side(phase, jump=False):
    """Герой сбоку, лицом вправо: бег по фазе 0..2π или прыжок. Плащ летит назад и полощется."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    wave = 0.0 if jump else math.sin(phase * 2.0 + 0.6)
    _arm(c, 17, 15 - bob, 17 + 5 * swing, 20 - bob - (3 if jump else 0), near=False)
    if jump:
        _cape(c, 14, 12, 4, 19, 6.0, -0.5)
    else:
        _cape(c, 14, 12 - bob, 3.5, 18 + wave * 1.6, 7.0, wave * 0.8)
    for sign in (-1, 1):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        _leg(c, (15 + sign, hip_y), knee, foot, near=sign > 0)
    _torso(c, 13 - bob, hip_y)
    _arm(c, 13, 15 - bob, 13 - 5 * swing, 20 - bob - (4 if jump else 0))
    _head(c, 16, 8 - bob)
    c.finish()
    _face(c, 16, 8 - bob)
    return c


def hero_back(phase):
    """Со спины: бежит вглубь экрана, плащ закрывает спину до колен и качается подолом; над
    воротом шея и уши, хохолок набок."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, SEA if sign > 0 else NAVY)
        c.rect(x - 2, 26 - lift, x + 1, 29 - lift, GOLD if sign > 0 else BRASS)
        _arm(c, 16 + sign * 6, 14 - bob, 16 + sign * 8, 19 - bob + s * sign * 2, near=sign > 0)
    c.rect(11, 13 - bob, 20, 21 - bob, SEA)
    # Плащ: трапеция от плеч, подол зубцами, уходит в сторону шага.
    hem = 23 - bob
    c.poly([(12, 12 - bob), (19, 12 - bob), (22 + s, hem - 1), (20 + s, hem + 1), (17.5 + s, hem - 1),
            (15.5 + s, hem + 1), (13 + s, hem - 1), (11 + s, hem + 1), (9 + s, hem - 1)], GOLD)
    c.line(14, 15 - bob, 13 + s, hem - 2, BRASS, 1)
    c.line(18, 15 - bob, 18.5 + s, hem - 2, BRASS, 1)
    # Затылок: волосы целиком, хохолок сверху, уши и шея кожей.
    c.ellipse(15.5, 8 - bob, 4.6, 4.6, SKIN)
    for y in range(3 - bob, 13 - bob):
        for x in range(10, 22):
            if c.get(x, y) != SKIN:
                continue
            ear = x in (11, 20) and y >= 8 - bob
            nape = y >= 11 - bob or (y == 10 - bob and x in (13, 15, 16, 18))
            if not ear and not nape:
                c.set(x, y, DARK)
    c.rect(14, 12 - bob, 17, 12 - bob, SKIN)
    c.rect(15, 3 - bob, 18, 3 - bob, DARK)
    c.rect(17, 2 - bob, 19, 2 - bob, DARK)
    return c.finish()


def hero_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление. Плащ
    отстаёт от тела: висит, тянется вниз, летит назад, вздувается вверх."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, near=False)
    tip = ((7, 25), (5, 24), (3, 19), (5, 13))[i]
    _cape(c, 14, 12 + crouch, tip[0], tip[1], (6.0, 7.0, 7.0, 8.0)[i], (0.0, 0.5, -0.5, -1.0)[i])
    for sign in (-1, 1):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        _leg(c, (15 + sign, hip_y), knee, foot, near=sign > 0)
    _torso(c, 13 + crouch, hip_y)
    _arm(c, 13 if i in (0, 3) else 16, 15 + crouch, (14 if i in (0, 3) else 20) + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch)
    _head(c, 16, 8 + crouch)
    c.finish()
    _face(c, 16, 8 + crouch)
    return c


def hero_idle(i):
    """Стойка: два кадра, герой дышит, плащ висит за спиной до колен и чуть ходит подолом."""
    c = Canvas()
    up = i
    _arm(c, 18, 15 - up, 19, 20 - up, near=False)
    c.poly([(14, 12 - up), (10, 13 - up), (8, 19), (7 - i, 24), (9 - i, 25), (10, 24), (12, 25), (13, 19)], GOLD)
    c.line(11, 15 - up, 10 - i, 23, BRASS, 1)
    for sign in (-1, 1):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, SEA if sign > 0 else NAVY)
        c.rect(x - 1, 25, x + 1, 28, GOLD if sign > 0 else BRASS)
        c.rect(x - 1, 29, x + 2, 30, GOLD if sign > 0 else BRASS)
    c.rect(16, 24, 19, 24, GOLD)
    _torso(c, 13 - up, 21)
    _arm(c, 13, 15 - up, 13, 21 - up)
    _head(c, 16, 8 - up)
    c.finish()
    _face(c, 16, 8 - up)
    return c


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; жёлтый пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = GOLD if k >= int(n) - 1 else SEA
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def hero_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх, рука
    сзади на земле, плащ бьётся над затылком. Верх хохолка на 15-й строке. Два кадра."""
    c = Canvas()
    c.poly([(12, 23), (7, 18 - i), (2, 16 + i), (4, 19), (1, 21 + i), (5, 23), (9, 26)], GOLD)
    _leg(c, (19, 27), (24, 23 - i), (27, 27), near=False, sole=3)
    c.line(13, 24, 19, 23, NAVY, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 24, 28, SEA, 4)
    c.line(24, 28, 28, 28, GOLD, 4)
    c.rect(28, 25, 30, 29, GOLD)
    _arm(c, 11, 25, 6, 29)
    _head(c, 10, 22)
    c.finish()
    _face(c, 10, 22)
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def hero_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд, плащ лёг на землю за
    спиной. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.poly([(13, 21), (10, 22), (8, 26), (5 - i, 29), (7, 30), (12, 30), (12, 26)], GOLD)
    c.line(11, 23, 9, 28, BRASS, 1)
    for sign in (-1, 1):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        _leg(c, hip, knee, foot, near=sign > 0)
    c.rect(11, 22, 18, 26, SEA)
    c.rect(11, 26, 17, 26, GOLD)
    _arm(c, 14, 24, 19, 26)
    _head(c, 16, 20)
    c.finish()
    _face(c, 16, 20)
    return c


def hero_hang(i):
    """На тросе: руки сведены вверх к точке хвата (центр сверху), голова втянута в плечи, ноги
    свисают и качаются, плащ маятником."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(12, 14, 15, 2, NAVY, 3)
    c.line(14, 6, 15, 2, BRASS, 3)
    c.poly([(13, 12), (10, 13), (8 - sw, 19), (6 - sw * 2, 24), (8 - sw * 2, 25), (9.5 - sw * 2, 24),
            (11 - sw * 2, 25), (13, 19)], GOLD)
    c.line(11, 15, 9 - sw * 2, 23, BRASS, 1)
    for sign in (-1, 1):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        hip = (15.5 + sign * 2, 21)
        knee = ((hip[0] + foot[0]) / 2.0, 25)
        col, boot = (SEA, GOLD) if sign > 0 else (NAVY, BRASS)
        c.line(hip[0], hip[1], foot[0], foot[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], boot, 3)
        c.rect(foot[0] - 1, foot[1], foot[0] + 2, foot[1] + 1, boot)
    _torso(c, 13, 21)
    c.line(19, 14, 17, 2, SEA, 3)
    c.line(18, 6, 17, 2, GOLD, 3)
    c.ellipse(16, 1.5, 2.2, 1.5, GOLD)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 11)
    hd.finish()
    _face(hd, 16, 11)
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 5:
                c.set(x, y, hd.px[y][x])
    return c


# --- Робот-приспешник --------------------------------------------------------------------------
# Корпус-бочонок с обручами на коротких поршневых ногах, один красный глаз в тёмной глазнице,
# руки-клешни, антенна с огоньком. Шаг и рост повторяют скелета пиратов.

def _barrel(c, cx, y0, y1, rx=7.5):
    """Бочонок: выпуклые бока, плоские крышка и дно, два обруча."""
    tmp = Canvas()
    mid = (y0 + y1) / 2.0
    tmp.ellipse(cx, mid, rx, (y1 - y0) / 2.0 + 3.5, VIOLET)
    _clip(tmp, y0, y1)
    c.paste(tmp, 0, 0)
    for y in (y0 + 3, y1 - 3):
        for x in range(32):
            if tmp.get(x, y) is not None:
                c.set(x, y, PLUM)
    for x in range(32):
        if tmp.get(x, y0) is not None:
            c.set(x, y0, METAL)


def _claw(c, x, y, dx, dy, gap, col):
    """Клешня полумесяцем с центром (x, y), раскрыта в сторону (dx, dy); `gap` это раствор:
    при малом крюки почти сомкнуты."""
    tmp = Canvas()
    tmp.ellipse(x, y, 3.7, 3.7, col)
    tmp.ellipse(x + dx * 2.2, y + dy * 2.2, 3.0 if dx else 1.0 + gap, 3.0 if dy else 1.0 + gap, None)
    c.paste(tmp, 0, 0)


def robot_side(phase):
    """Робот сбоку, лицом влево (навстречу герою): шаг по фазе, клешня на шарнире выставлена
    вперёд и щёлкает (вторая за корпусом)."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    snap = 0.6 + 0.9 * abs(math.cos(phase))
    for sign, col in ((-1, DARK), (1, METAL)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        c.line(16 + sign, 22 - bob, foot[0], foot[1], col, 3)
        c.rect(foot[0] - 3, foot[1], foot[0] + 1, foot[1] + 1, DARK)
    _barrel(c, 16, 4 - bob, 22 - bob)
    # Глазница на передней стенке.
    c.ellipse(12, 9 - bob, 3.4, 3.4, DARK)
    c.ellipse(11.6, 9 - bob, 2.3, 2.3, RED)
    # Ближняя клешня: шарнир на боку корпуса, прямая рука вперёд.
    hx, hy = 6 - 2 * s, 18 - bob
    c.line(15, 16 - bob, hx + 3, hy, METAL, 3)
    c.ellipse(15, 16 - bob, 2.3, 2.3, DARK)
    _claw(c, hx, hy, -1, 0, snap * 0.7, METAL)
    # Антенна.
    c.line(18, 3 - bob, 20, 1 - bob, DARK, 1)
    c.finish()
    c.set(20, max(0, 1 - bob), RED)
    c.set(11, 8 - bob, WHITE)
    c.set(15, 16 - bob, GREY)
    return c


def robot_front(phase):
    """Робот лицом к камере: идёт на игрока, ноги по очереди, клешни разведены и щёлкают."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    snap = 0.6 + 0.9 * abs(math.cos(phase))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 15.5 + sign * 3.5
        c.line(x, 22 - bob, x, 28 - lift, METAL, 3)
        c.rect(x - 2, 28 - lift, x + 2, 29 - lift, DARK)
        ex = 15.5 + sign * 11.5
        hy = 20 - bob - s * sign * 2
        c.line(15.5 + sign * 7, 13 - bob, ex, 15 - bob, METAL, 2)
        c.line(ex, 15 - bob, ex, hy - 3, METAL, 2)
        _claw(c, ex, hy, 0, 1, snap * 0.7, METAL)
    _barrel(c, 15.5, 4 - bob, 22 - bob, 8.0)
    for sign in (-1, 1):
        c.ellipse(15.5 + sign * 7.5, 13 - bob, 1.8, 1.8, METAL)
    for y in (15, 17):
        c.rect(13, y - bob, 18, y - bob, PLUM)
    c.ellipse(15.5, 9 - bob, 3.6, 3.6, DARK)
    c.ellipse(15.5, 9 - bob, 2.5, 2.5, RED)
    c.line(15.5, 3 - bob, 15.5, 1 - bob, DARK, 1)
    c.finish()
    c.set(15, max(0, 1 - bob), RED)
    c.set(16, max(0, 1 - bob), RED)
    c.set(14, 8 - bob, WHITE)
    return c


# --- Летун и ползун ----------------------------------------------------------------------------

def drone(i):
    """Дрон-шпион летит вправо: плоский корпус, объектив с красным глазом впереди, два винта
    на стойках, хвостовой киль, антенна снизу. Четыре кадра: винты мелькают, огонёк мигает.
    Корпус по центру кадра и не двигается, чтобы при развороте не прыгал."""
    c = Canvas()
    span = (6, 2, 5, 3)[i]
    # Хвост и киль.
    c.poly([(9, 16), (3, 12), (2, 15), (5, 19), (9, 20)], PLUM)
    # Стойки и винты.
    for x in (10, 20):
        c.rect(x, 9, x, 13, DARK)
        c.rect(x - span, 7, x + span, 8, GREY)
    c.ellipse(15, 17, 8, 4.6, VIOLET)
    c.rect(9, 18, 20, 18, PLUM)
    c.rect(8, 21, 20, 21, DARK)
    # Объектив.
    c.ellipse(22, 17, 4, 4, DARK)
    c.ellipse(22.6, 17, 2.6, 2.6, RED)
    # Антенна-щуп снизу и полозья.
    c.line(12, 21, 10, 26, DARK, 1)
    c.line(17, 21, 19, 25, DARK, 1)
    c.finish()
    c.set(22, 16, WHITE)
    c.set(10, 27, RED if i % 2 == 0 else GOLD)
    c.set(13, 15, GOLD if i < 2 else PLUM)
    return c


def spider(i):
    """Робот-паук, четыре кадра: приплюснутый купол на четырёх высоких коленчатых ногах,
    колени выше корпуса, ноги переступают через одну, три красных глаза в ряд."""
    c = Canvas()
    for k in range(2):
        for sign in (-1, 1):
            lift = 2 if (k + i + (0 if sign > 0 else 1)) % 2 == 0 else 0
            root = (15.5 + sign * (4.5 + k), 21)
            knee = (15.5 + sign * (8.5 + k * 4), 13 + k * 3 - lift // 2)
            foot = (15.5 + sign * (8.5 + k * 5), 30 - lift)
            c.line(root[0], root[1], knee[0], knee[1], METAL, 2)
            # Голень в два пикселя: два тонких отрезка рядом (толстый на целых x выпадает).
            for d in (0, -sign):
                c.line(knee[0] + d, knee[1], foot[0] + d, foot[1], GREY, 1)
            c.ellipse(knee[0], knee[1], 1.5, 1.5, GREY)
    tmp = Canvas()
    tmp.ellipse(15.5, 23, 6.5, 6, VIOLET)
    _clip(tmp, 0, 25)
    c.paste(tmp, 0, 0)
    c.rect(10, 24, 21, 25, PLUM)
    c.rect(11, 26, 20, 26, DARK)
    c.rect(12, 21, 19, 22, DARK)
    c.line(15.5, 17, 15.5, 14, DARK, 1)
    c.finish()
    for x in (13, 15, 18):
        c.set(x, 21, RED)
        c.set(x, 22, RED)
    c.set(16, 21, RED)
    c.set(16, 22, RED)
    c.set(15, 13, GOLD if i % 2 == 0 else RED)
    c.set(16, 13, GOLD if i % 2 == 0 else RED)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def _star_points(cx, cy, r_out, r_in, sx=1.0):
    pts = []
    for k in range(10):
        r = r_out if k % 2 == 0 else r_in
        a = -math.pi / 2.0 + k * math.pi / 5.0
        pts.append((cx + math.cos(a) * r * sx, cy + math.sin(a) * r))
    return pts


def coin(i):
    """Значок-звезда вращается: шесть кадров, ширина по косинусу; лучи гранёные, правая грань
    каждого темнее, в центре блик."""
    c = Canvas()
    sx = abs(math.cos(math.pi * i / 6.0))
    cx, cy = 15.5, 16.5
    if sx < 0.15:
        c.rect(15, 6, 16, 24, GOLD)
        return c.finish()
    pts = _star_points(cx, cy, 11.0, 4.8, sx)
    c.poly(pts, GOLD)
    for k in range(0, 10, 2):
        c.poly([(cx, cy), pts[k], pts[(k + 1) % 10]], BRASS)
    c.poly(pts[:1] + [(cx, cy), pts[9]], GOLD)
    if sx > 0.5:
        c.ellipse(cx, cy, 2.2 * sx, 2.2, GOLD)
    c.finish()
    if sx > 0.5:
        c.set(cx - 1 * sx, cy - 1, WHITE)
        c.set(cx - 1 * sx - 1, cy - 1, WHITE)
        c.set(cx - 1 * sx, cy - 2, WHITE)
    return c


def flag(i):
    """Флаг героя на стальном древке с жёлтым шаром: синее полотнище с вырезом на конце идёт
    волной, на нём жёлтая звезда."""
    c = Canvas()
    c.rect(5, 3, 6, 31, METAL)
    c.ellipse(5.5, 2, 2, 2, GOLD)

    def wave(x):
        return math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0

    top = [(x, 5 + wave(x)) for x in range(8, 30)]
    bottom = [(x, 19 + wave(x)) for x in range(8, 30)]
    c.poly(top + [(25, 12 + wave(25))] + bottom[::-1], SEA)
    c.shade()
    c.outline()
    mid = int(round(wave(16)))
    _stamp(c, 12, 8 + mid, STAR7, GOLD)
    c.set(15, 11 + mid, WHITE)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(8, 9, 10, 10, WHITE)
    c.set(8, 11, WHITE)
    return c.finish()


def ground(inner=False):
    """Крыша: бетонная плита парапета со сколами над кирпичной кладкой; внутри только кирпич.
    Ряды кладки по четыре пикселя со сдвигом на полкирпича, плитка стыкуется по обеим осям."""
    c = Canvas()
    c.rect(0, 0, 31, 31, TAN)
    for row in range(8):
        y = row * 4
        c.rect(0, y + 3, 31, y + 3, DARK)
        off = 0 if row % 2 == 0 else 4
        for x in range(off, 32, 8):
            c.rect(x, y, x, y + 2, DARK)
            # Блик по верху кирпича и редкие тёмные кирпичи.
            c.rect(x + 1, y, x + 7, y, SKIN)
            if (x * 3 + row * 5) % 7 == 0:
                c.rect(x + 1, y + 1, x + 7, y + 2, BRASS)
        if off:
            c.rect(0, y, 3, y, SKIN)
    if not inner:
        c.rect(0, 0, 31, 7, GREY)
        c.rect(0, 0, 31, 1, WHITE)
        c.rect(0, 6, 31, 6, METAL)
        c.rect(0, 7, 31, 7, DARK)
        # Шов плит, сколы и крапинки бетона.
        c.rect(19, 2, 19, 5, METAL)
        for x, y in ((3, 3), (9, 4), (14, 2), (25, 4), (29, 3), (7, 5)):
            c.set(x, y, METAL)
        c.rect(11, 0, 13, 0, GREY)
        c.rect(26, 0, 27, 1, GREY)
    return c


def rock():
    """Обломок бетона: угловатая плита со светлым сколом, трещиной и двумя гнутыми прутьями
    ржавой арматуры сверху."""
    c = Canvas()
    # Арматура без тени: прямой прут с загибом и крюк, обводка своя.
    bars = Canvas()
    bars.line(21, 13, 25, 3, BRASS, 2)
    bars.line(25, 3, 29, 5, BRASS, 2)
    bars.line(9, 14, 8, 5, BRASS, 2)
    bars.line(8, 5, 4, 6, BRASS, 2)
    bars.line(27, 20, 31, 19, BRASS, 2)
    bars.outline()
    for x, y in ((22, 9), (24, 5), (8, 9), (8, 7)):
        bars.set(x, y, TAN)
    # Плита: прямые сколы, плоская верхняя грань, слева ровный излом.
    slab = Canvas()
    slab.poly([(2, 29), (2, 17), (6, 12), (15, 12), (18, 9), (26, 10), (29, 15), (30, 23), (27, 29)], GREY)
    slab.poly([(4, 16), (7, 13), (15, 13), (18, 10), (25, 11), (27, 15), (16, 17)], WHITE)
    slab.line(16, 17, 14, 22, METAL, 1)
    slab.line(14, 22, 17, 28, METAL, 1)
    slab.line(14, 22, 9, 24, METAL, 1)
    for x, y in ((6, 20), (22, 20), (24, 25), (8, 27), (20, 23)):
        slab.set(x, y, METAL)
    slab.rect(10, 19, 11, 19, WHITE)
    slab.finish()
    c.paste(bars, 0, 0)
    c.paste(slab, 0, 0)
    return c


def chest():
    """Бронированный кейс: стальной ящик с ручкой, тёмные угловые накладки с заклёпками, шов
    крышки, жёлтый замок со скважиной и синяя полоса со звездой героя нет: кейс злодейский."""
    c = Canvas()
    # Ручка.
    c.rect(11, 6, 20, 7, DARK)
    c.rect(11, 6, 12, 10, DARK)
    c.rect(19, 6, 20, 10, DARK)
    c.rect(3, 11, 28, 28, METAL)
    c.rect(3, 11, 28, 12, GREY)
    c.rect(3, 17, 28, 17, DARK)
    # Угловые накладки.
    for x0, x1 in ((3, 7), (24, 28)):
        c.rect(x0, 11, x1, 15, DARK)
        c.rect(x0, 24, x1, 28, DARK)
    for x in (5, 26):
        for y in (13, 26):
            c.set(x, y, GREY)
    # Рёбра жёсткости и замок.
    for x in (10, 21):
        c.rect(x, 19, x, 27, DARK)
    c.rect(13, 15, 18, 21, GOLD)
    c.rect(13, 20, 18, 21, BRASS)
    c.finish()
    c.set(15, 17, K)
    c.set(16, 17, K)
    c.set(15, 18, K)
    c.set(16, 18, K)
    c.set(15, 19, K)
    return c


def key():
    """Ключ от кейса: головка звездой с отверстием, стержень с двумя бородками."""
    c = Canvas()
    c.poly(_star_points(10, 16, 8.5, 4.4), GOLD)
    c.ellipse(10, 16.5, 3.4, 3.4, GOLD)
    c.rect(14, 15, 29, 17, GOLD)
    c.rect(23, 18, 24, 22, GOLD)
    c.rect(27, 18, 29, 21, GOLD)
    c.rect(14, 15, 29, 15, WHITE)
    c.ellipse(10, 16.5, 1.6, 1.6, None)
    return c.finish()


def medkit():
    """Аптечка: белый чемоданчик с красным крестом, ручкой и защёлками."""
    c = Canvas()
    c.rect(12, 7, 19, 8, METAL)
    c.rect(12, 7, 13, 11, METAL)
    c.rect(18, 7, 19, 11, METAL)
    c.rect(4, 12, 27, 28, WHITE)
    c.rect(4, 12, 27, 13, GREY)
    c.rect(14, 15, 17, 26, RED)
    c.rect(10, 19, 21, 22, RED)
    for x in (6, 24):
        c.rect(x, 12, x + 1, 14, METAL)
    return c.finish()


def shot():
    """Выстрел робота: красный сгусток с жёлтым ядром и четырьмя короткими лучами."""
    c = Canvas(16, 16)
    for dx, dy in ((0, -6), (0, 6), (-6, 0), (6, 0)):
        c.line(7.5, 7.5, 7.5 + dx, 7.5 + dy, RED, 1)
    c.ellipse(7.5, 7.5, 4.6, 4.6, RED)
    c.ellipse(7.5, 7.5, 2.8, 2.8, GOLD)
    c.ellipse(7, 7, 1.2, 1.2, WHITE)
    return c


# --- Параллакс ---------------------------------------------------------------------------------
# Небо демка красит полосами из палитры (индиго, синий, коралл, персик), слои ложатся на него.

def par_sky():
    """Дальний слой: длинные закатные облака, первые звёзды и дирижабль, лента 256×48, стыкуется
    по краям."""
    c = Canvas(256, 48)
    rng = random.Random(23)
    for _ in range(14):
        c.set(rng.randint(0, 255), rng.randint(0, 13), WHITE if rng.random() < 0.5 else SKY)
    # Облака: тонкие полосы, верх в тени, низ горит от солнца.
    for cx, cy, r in ((34, 30, 26), (70, 36, 16), (118, 12, 20), (206, 34, 24), (236, 27, 14), (250, 40, 18)):
        for k in (0, 256, -256):
            c.ellipse(cx + k, cy, r, 2.6, AQUA)
            c.ellipse(cx + k + r * 0.3, cy - 1.5, r * 0.5, 1.6, AQUA)
            c.rect(cx + k - r * 0.6, cy + 2, cx + k + r * 0.5, cy + 2, SKY)
    # Дирижабль: сигара носом вправо, хвостовое оперение, гондола с огнями.
    bx, by = 160, 20
    c.poly([(bx - 20, by), (bx - 27, by - 7), (bx - 24, by), (bx - 27, by + 7)], RED)
    c.ellipse(bx, by, 22, 7.5, GREY)
    for y in range(by, by + 9):
        for x in range(bx - 23, bx + 24):
            if c.get(x, y) == GREY and y >= by + 2:
                c.set(x, y, METAL)
    for y in range(by - 8, by):
        for x in range(bx - 23, bx + 24):
            if c.get(x, y) == GREY and c.get(x, y - 1) is None:
                c.set(x, y, WHITE)
    c.rect(bx - 17, by, bx + 19, by, RED)
    for x in (bx - 9, bx + 2, bx + 12):
        c.line(x, by - 6, x, by + 6, METAL, 1)
    c.rect(bx - 6, by + 8, bx + 6, by + 10, DARK)
    for x in range(bx - 5, bx + 6, 3):
        c.set(x, by + 9, GOLD)
    _stamp(c, bx - 3, by - 7, ("..#..", "#####", ".###.", ".#.#."), GOLD)
    return c


def _tower(c, rng, x, w, top, wall, lit, rim=None):
    """Небоскрёб: стена до низа ленты, сетка окон (часть горит), на крыше надстройка или шпиль."""
    c.rect(x, top, x + w - 1, 47, wall)
    if rim is not None:
        c.rect(x, top, x, 47, rim)
    kind = rng.randint(0, 3)
    if kind == 0 and w >= 10:
        c.rect(x + 3, top - 3, x + w - 4, top - 1, wall)
        c.line(x + w // 2, top - 4, x + w // 2, top - 9, wall, 1)
        c.set(x + w // 2, top - 10, RED)
    elif kind == 1:
        c.rect(x + 2, top - 2, x + 5, top - 1, wall)
    elif kind == 2 and w >= 8:
        c.line(x + w - 3, top - 1, x + w - 3, top - 6, wall, 1)
    if lit is None:
        return
    for wy in range(top + 3, 46, 4):
        for wx in range(x + 2, x + w - 2, 3):
            r = rng.random()
            if r < 0.42:
                c.rect(wx, wy, wx, wy + 1, lit)
            elif r < 0.5:
                c.rect(wx, wy, wx, wy + 1, SKY)


def par_far():
    """Средний слой: небоскрёбы на горизонте в два плана, дальние в дымке, ближние с горящими
    окнами и коралловым отсветом заката по левой грани; лента 256×48, низ сплошной."""
    c = Canvas(256, 48)
    rng = random.Random(41)
    x = 0
    while x < 256:
        w = min(rng.randint(9, 17), 256 - x)
        _tower(c, rng, x, w, 47 - rng.randint(16, 36), METAL, None)
        x += w
    x = 3
    while x < 250:
        w = min(rng.randint(11, 20), 254 - x)
        if w < 6:
            break
        _tower(c, rng, x, w, 47 - rng.randint(10, 30), NAVY, GOLD, AQUA)
        x += w + rng.choice((0, 2, 5, 8))
    # Высотка-ориентир со ступенчатой макушкой и шпилем.
    c.rect(126, 8, 141, 47, NAVY)
    c.rect(126, 8, 126, 47, AQUA)
    c.rect(129, 4, 138, 7, NAVY)
    c.rect(132, 1, 135, 3, NAVY)
    c.set(133, 0, RED)
    for wy in range(11, 46, 4):
        for wx in range(128, 140, 3):
            if rng.random() < 0.55:
                c.rect(wx, wy, wx, wy + 1, GOLD)
    return c


def par_mid():
    """Ближний слой: тёмные крыши с водонапорными баками, антеннами и рекламным щитом, крупные
    окна; низ растворяется в синем точками, как сумерки над улицей. Лента 256×32."""
    c = Canvas(256, 32)
    rng = random.Random(5)
    x = 0
    while x < 256:
        w = min(rng.randint(18, 34), 256 - x)
        if 256 - (x + w) < 10:
            w = 256 - x
        top = rng.randint(7, 15)
        c.rect(x, top, x + w - 1, 31, DARK)
        c.rect(x, top, x + w - 1, top, METAL)
        c.rect(x, top + 1, x, 31, K)
        kind = rng.randint(0, 3)
        if kind == 0 and w >= 14:
            # Водонапорный бак на ножках с конусом.
            bx = x + w // 2
            c.rect(bx - 3, top - 7, bx + 3, top - 3, DARK)
            c.rect(bx - 3, top - 7, bx + 3, top - 7, METAL)
            c.poly([(bx - 3, top - 8), (bx, top - 10), (bx + 3, top - 8)], DARK)
            c.rect(bx - 3, top - 2, bx - 3, top - 1, DARK)
            c.rect(bx + 3, top - 2, bx + 3, top - 1, DARK)
        elif kind == 1:
            c.line(x + 4, top - 1, x + 4, top - 7, DARK, 1)
            c.rect(x + 2, top - 5, x + 6, top - 5, DARK)
        elif kind == 2 and w >= 16:
            # Рекламный щит.
            c.rect(x + 4, top - 6, x + 14, top - 2, DARK)
            c.rect(x + 5, top - 5, x + 13, top - 3, AQUA)
            c.rect(x + 6, top - 4, x + 9, top - 4, SKY)
            c.set(x + 6, top - 1, DARK)
            c.set(x + 12, top - 1, DARK)
        else:
            c.rect(x + w - 7, top - 3, x + w - 3, top - 1, DARK)
        for wy in range(top + 3, 24, 5):
            for wx in range(x + 3, x + w - 3, 4):
                if rng.random() < 0.38:
                    c.rect(wx, wy, wx + 1, wy + 2, GOLD)
                    c.set(wx, wy, SKY)
        x += w
    # Низ: тёмное переходит в синее шахматкой, под лентой демка красит синим.
    for y in range(24, 32):
        for px in range(256):
            k = y - 24
            if k >= 6 or (k >= 3 and (px + y) % 2 == 0) or (k < 3 and px % 4 == (y * 2) % 4):
                c.set(px, y, SEA)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, робот, вещи, крыша, три слоя
    закатного города. Ключи и размеры те же, что у `space16.sprites()`."""
    return {
        "enemy_walk": strip([robot_side(p) for p in base.phases()]),
        "enemy_front": strip([robot_front(p) for p in base.phases()]),
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
        "hero_run": strip([hero_side(p) for p in base.phases()]),
        "hero_jump": hero_side(0.0, jump=True),
        "hero_leap": strip([hero_leap(i) for i in range(4)]),
        "hero_idle": strip([hero_idle(i) for i in range(2)]),
        "hero_back": strip([hero_back(p) for p in base.phases()]),
        "hero_slide": strip([hero_slide(i) for i in range(2)]),
        "hero_hang": strip([hero_hang(i) for i in range(2)]),
        "hero_crouch": strip([hero_crouch(i) for i in range(2)]),
    }


def extras():
    """Общие слоты демок в палитре набора: летун (дрон-шпион) и ползун (робот-паук) по четыре
    кадра, ключ, аптечка, выстрел врага."""
    return {
        "parrot_fly": strip([drone(i) for i in range(4)]),
        "crab_walk": strip([spider(i) for i in range(4)]),
        "key": key(),
        "medkit": medkit(),
        "shot": shot(),
    }


def shaded(items):
    """Ленты в палитре `PALETTE` → {ключ: (холст, палитра)} как в игре: силуэты получают
    светотень рампами (`pixel_sprites16.reshade`), сплошные плитки остаются в палитре сеттинга."""
    out = {}
    for name, canvas in items.items():
        if base.wants_reshade(name, canvas):
            out[name] = base.reshade(canvas, PALETTE, GROUPS)
        else:
            out[name] = (canvas, PALETTE)
    return out


def save_sheet(path, items, scale=3, pad=6, back=(0x9A, 0x86, 0xA6, 255), max_w=640):
    """Лист для просмотра: `items` это {ключ: (холст, палитра)}, лента на строку; ленты шире
    `max_w` режутся на строки по `max_w`."""
    width = (min(max(c.w for c, _ in items.values()), max_w) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for name, (canvas, palette) in items.items():
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


def preview(path, scale=4, keys=None, back=(0x9A, 0x86, 0xA6, 255)):
    """Лист набора: лента на строку после светотени, затем `extras()`. Фон сиреневый, средний
    по тону: на нём видно и синее с жёлтым, и держит ли обводка. `keys` оставляет часть лент."""
    items = shaded(sprites())
    items.update(shaded(extras()))
    if keys:
        items = {k: items[k] for k in keys if k in items}
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
