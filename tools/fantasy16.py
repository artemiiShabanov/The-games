#!/usr/bin/env python3
"""Набор «Фэнтези» для 16/32-bit, сравнительная версия основы (состав в `docs/specs/settings.md`):
волшебный лес в сиреневых сумерках, юный маг в синей мантии с золотой каймой, в остроконечной
шляпе и с посохом, зелёные гоблины с дубинками. Те же ленты и кадры, что у пиратов и космоса
(`pixel_sprites16.py`, `space16.py`): позы, габариты и опора ног героя повторяют космонавта,
чтобы хитбоксы демок сходились, а рисунок свой. Модуль ничего не пишет в проект, только лист.

    python3 tools/fantasy16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Фэнтези»: 16 цветов, имена и порядок как у космоса (индекс это роль в HUD и мире
# демки). Зелень гоблинов и мха живёт в слоте TAN: тень кожи героя даёт рампа светотени.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x15, 0x10, 0x1E),  # K      обводка
    (0x28, 0x24, 0x66),  # NAVY   индиго: тень мантии, глубокие сумерки
    (0x3A, 0x5A, 0xCC),  # SEA    синяя мантия и шляпа
    (0x3A, 0xD4, 0xC2),  # AQUA   бирюза: кристалл посоха, руны, водопады
    (0xC8, 0xF8, 0xEC),  # SKY    блик кристалла, свечение
    (0xF4, 0xEE, 0xE4),  # WHITE  зубы, пена, сердцевина огонька
    (0xAE, 0xA6, 0xC6),  # GREY   сиреневый камень
    (0xF2, 0xC8, 0x9A),  # SKIN   кожа
    (0x6E, 0xB4, 0x4C),  # TAN    зелень: гоблин, слизь, мох
    (0xF6, 0xD0, 0x58),  # GOLD   кайма, руна, бонус
    (0xC2, 0x86, 0x2C),  # BRASS  тень золота, свет на дереве
    (0x9A, 0x64, 0x3C),  # METAL  дерево: посох, сундук, корни
    (0x48, 0x2E, 0x36),  # DARK   тёмная кора, башмаки, пасть
    (0xDC, 0x46, 0x5A),  # RED    сердце, язык мимика, огонь
    (0x9C, 0x5E, 0xD8),  # VIOLET знамя гильдии, сиреневая листва
    (0x52, 0x2E, 0x8E),  # PLUM   тень фиолетового, дальний лес
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GOLD: BRASS, BRASS: DARK, METAL: DARK, RED: PLUM,
          VIOLET: PLUM}
# Материалы для светотени рампами: мантия одна ткань, кристалл, камень и зубы, зелень, дерево.
GROUPS = {SEA: "robe", NAVY: "robe", AQUA: "crystal", SKY: "crystal", WHITE: "pale", GREY: "pale",
          SKIN: "skin", TAN: "green", GOLD: "gold", BRASS: "gold", METAL: "wood", DARK: "wood", RED: "red",
          VIOLET: "violet", PLUM: "violet"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


def _px(c, points, col):
    for x, y in points:
        c.set(x, y, col)


# --- Маг ---------------------------------------------------------------------------------------
# Силуэт: шляпа с широкими полями и загнутым назад кончиком, мантия колоколом до щиколоток,
# посох с ромбом кристалла впереди. Узнаётся без цвета по шляпе и посоху; цветом по золотой
# кайме подола и бирюзе кристалла.

def _hat(c, y, ox=0, tip=0):
    """Шляпа сбоку, лицом вправо: поля в строке `y`, тулья клонится назад. `tip`: 0 кончик
    загнут вниз, 1 вытянут назад (на бегу), 2 взлетел вверх (в падении)."""
    for r, right in ((-6, 14), (-5, 15), (-4, 16), (-3, 17), (-2, 18)):
        c.rect(12 + ox, y + r, right + ox, y + r, SEA)
    c.rect(12 + ox, y - 1, 20 + ox, y - 1, GOLD)
    c.rect(10 + ox, y, 23 + ox, y, SEA)
    if tip == 0:
        _px(c, ((11, -6), (10, -6), (10, -5), (9, -5), (9, -4)), None)
        for dx, dy in ((11, -6), (10, -6), (10, -5), (9, -5), (9, -4)):
            c.set(dx + ox, y + dy, SEA)
    elif tip == 1:
        for dx, dy in ((11, -6), (10, -6), (9, -6), (8, -6), (8, -5)):
            c.set(dx + ox, y + dy, SEA)
    else:
        for dx, dy in ((11, -6), (11, -7), (10, -7), (10, -8)):
            c.set(dx + ox, y + dy, SEA)


def _head(c, y, ox=0, tip=0):
    """Голова под шляпой: каштановые волосы на затылке, лицо вправо, нос. Поля в строке `y`."""
    c.rect(12 + ox, y + 1, 14 + ox, y + 4, METAL)
    c.rect(13 + ox, y + 5, 15 + ox, y + 5, METAL)
    c.rect(15 + ox, y + 1, 21 + ox, y + 4, SKIN)
    c.rect(16 + ox, y + 5, 20 + ox, y + 5, SKIN)
    c.set(22 + ox, y + 3, SKIN)
    _hat(c, y, ox, tip)


def _eye(c, y, ox=0):
    """Глаз в два пикселя, ставится после обводки."""
    c.set(19 + ox, y + 2, K)
    c.set(19 + ox, y + 3, K)


def _crystal(c, x, y):
    """Кристалл посоха: бирюзовый ромб с бликом, центр (x, y), золотая оправа снизу."""
    for dy, half in ((-3, 0), (-2, 1), (-1, 2), (0, 2), (1, 1), (2, 0)):
        c.rect(x - half, y + dy, x + half, y + dy, AQUA)
    c.set(x - 1, y - 1, SKY)
    c.set(x, y - 2, SKY)
    c.rect(x - 1, y + 3, x + 1, y + 3, GOLD)


def _staff(c, bx, by, tx, ty):
    """Посох в два пикселя от пяты (bx, by) до оправы (tx, ty), кристалл над оправой."""
    c.line(bx, by, tx, ty, METAL, 1)
    c.line(bx + 1, by, tx + 1, ty, METAL, 1)
    _crystal(c, int(round(tx)) + (1 if tx >= bx else 0), int(round(ty)) - 3)


def _boot(c, x, y):
    """Башмак носком вправо: подошва в строках y и y+1, голенище над ней."""
    x = int(round(x))
    y = int(round(y))
    c.rect(x - 1, y - 1, x + 1, y - 1, DARK)
    c.rect(x - 1, y, x + 3, y + 1, DARK)


def _robe(c, top, hem, xl, xr, sl=12, sr=20, belt=True):
    """Мантия колоколом: от плеч (sl..sr в строке `top`) к подолу (xl..xr в строке `hem`).
    Отдаёт края подола для каймы."""
    top = int(round(top))
    hem = int(round(hem))
    n = max(1, hem - top)
    for y in range(top, hem + 1):
        e = ((y - top) / n) ** 2
        lo = int(round(sl + (xl - sl) * e))
        hi = int(round(sr + (xr - sr) * e))
        c.rect(lo, y, hi, y, GOLD if belt and y == top + 6 and n > 8 else SEA)
    return int(round(xl)), int(round(xr)), hem


def _fold(c, x0, y0, x1, y1):
    """Складка мантии: тёмная линия от пояса к подолу."""
    c.line(x0, y0, x1, y1, NAVY, 1)


def _trim(c, hem):
    """Золотая кайма по нижней строке подола, после тени: остаётся яркой."""
    xl, xr, y = hem
    for x in range(xl - 1, xr + 2):
        if c.get(x, y) in (SEA, NAVY):
            c.set(x, y, GOLD)


def _sleeve(c, x0, y0, x1, y1, col=SEA):
    """Широкий рукав с золотым манжетом и кистью. Ближний отбит от мантии тенью снизу."""
    if col == SEA:
        c.line(x0, y0 + 1, x1 - 1, y1 + 1, NAVY, 3)
    c.line(x0, y0, x1, y1, col, 3)
    kx = x1 + (1 if x1 >= x0 else -1)
    if col == SEA:
        c.rect(int(round(x1)), int(round(y1)) - 1, int(round(x1)), int(round(y1)) + 1, GOLD)
    c.rect(int(round(kx)), int(round(y1)) - 1, int(round(kx)) + (1 if x1 >= x0 else -1), int(round(y1)), SKIN)


def _mage(dy, feet, hem_y, far_hand, hand, staff, tip=0, flare=0):
    """Маг сбоку, лицом вправо. `dy` сдвиг корпуса, `feet` ступни (дальняя, ближняя), `hem_y`
    строка подола, руки до точек `far_hand` и `hand`, `staff` это (пята x, y, оправа x, y)."""
    c = Canvas()
    top = 14 + dy
    _sleeve(c, 14, top + 2, far_hand[0], far_hand[1], NAVY)
    for fx, fy in feet:
        c.line(15, min(21 + dy, fy - 2), fx, fy - 1, NAVY, 3)
        _boot(c, fx, fy)
    lo = min(f[0] for f in feet)
    hi = max(f[0] for f in feet)
    hem = _robe(c, top, hem_y, min(11, lo - 2) - flare, max(21, hi + 2))
    # Складки: к дальней ноге и по середине подола.
    if hem_y - top > 8:
        _fold(c, 15, top + 8, feet[0][0], hem_y - 1)
        _fold(c, 17, top + 9, (hem[0] + hem[1]) / 2.0 + 2, hem_y - 1)
    c.set(19, top, GOLD)
    _staff(c, *staff)
    _sleeve(c, 17, top + 2, hand[0], hand[1])
    _head(c, 8 + dy, 0, tip)
    c.shade()
    _trim(c, hem)
    c.outline()
    _eye(c, 8 + dy)
    return c


def mage_side(phase, jump=False):
    """Маг сбоку, лицом вправо: бег по фазе 0..2π или прыжок. Подол растягивается шагом,
    кончик шляпы отстаёт."""
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    swing = 0.9 if jump else math.sin(phase)
    feet = []
    for sign in (-1, 1):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        feet.append((15 + 6 * a, 29 - lift))
    if jump:
        return _mage(0, feet, 24, (10, 17), (24, 16), (25, 24, 25, 10), tip=1, flare=1)
    return _mage(-bob, feet, 26 - bob, (14 + 4 * swing, 20 - bob), (24, 18 - bob),
                 (25, 26 - bob, 25, 10 - bob), tip=1 if bob else 0)


def mage_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    feet = []
    for sign in (-1, 1):
        feet.append((15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0)))
    hem_y = (27, 24, 22, 27)[i]
    up = i in (1, 2)
    far = (12 - i % 2, 12 + crouch) if up else (12, 20 + crouch)
    hand = (24, 15 + crouch) if up else (24, 18 + crouch)
    staff = (25, 23 + crouch, 25, 10 + max(crouch, 0)) if up else (25, 26 + min(crouch, 1), 25, 10 + crouch)
    return _mage(crouch, feet, hem_y, far, hand, staff, tip=(0, 1, 2, 2)[i], flare=1 if i in (0, 3) else 0)


def mage_idle(i):
    """Стойка: два кадра, маг дышит, посох упёрт в землю, кристалл мерцает."""
    up = i
    c = _mage(-up, [(13, 29), (17, 29)], 27, (12, 21 - up), (24, 18 - up), (25, 30, 25, 10), tip=0)
    if i == 1:
        _px(c, ((23, 4), (29, 6), (26, 2)), SKY)
    return c


def mage_back(phase):
    """Со спины: бежит вглубь экрана, шляпа с кончиком набок, мантия качается, посох справа."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    top = 14 - bob
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 22 - bob, x + 1, 26 - lift, NAVY)
        c.rect(x - 2, int(27 - lift), x + 1, int(29 - lift), DARK)
    # Посох в правой руке, левая качается.
    c.rect(25, 10 - bob, 26, 25 - bob, METAL)
    _crystal(c, 26, 7 - bob)
    c.line(11, top + 2, 8, top + 6 + s * 2, SEA, 3)
    c.rect(7, int(round(top + 7 + s * 2)), 8, int(round(top + 8 + s * 2)), SKIN)
    sway = int(round(s))
    hem = _robe(c, top, 26 - bob, 9 + sway, 22 + sway, 11, 20)
    _fold(c, 15, top + 8, 15 + sway, 25 - bob)
    _fold(c, 12, top + 9, 11 + sway, 25 - bob)
    c.line(20, top + 2, 24, top + 5, SEA, 3)
    c.rect(24, top + 4, 24, top + 6, GOLD)
    c.rect(25, top + 4, 26, top + 5, SKIN)
    # Затылок: волосы до воротника, поля шляпы шире плеч, тулья с кончиком вправо.
    y = 8 - bob
    c.rect(12, y + 1, 19, y + 4, METAL)
    c.rect(13, y + 5, 18, y + 5, METAL)
    c.rect(8, y, 23, y, SEA)
    c.rect(11, y - 1, 20, y - 1, GOLD)
    for r, lo, hi in ((-2, 12, 19), (-3, 12, 18), (-4, 13, 18), (-5, 13, 17), (-6, 14, 18)):
        c.rect(lo, y + r, hi, y + r, SEA)
    _px(c, ((19, y - 6), (20, y - 5), (20, y - 4)), SEA)
    c.shade()
    _trim(c, hem)
    c.outline()
    return c


def mage_slide(i):
    """Подкат ногами вперёд: корпус откинут, шляпа съехала назад, посох выставлен вперёд над коленями.
    Макушка шляпы на 15-й строке, как шлем космонавта. Два кадра: колено и пыль."""
    c = Canvas()
    # Дальняя нога коленом вверх.
    c.line(19, 26, 24, 23 - i, NAVY, 3)
    c.line(24, 23 - i, 27, 27, NAVY, 3)
    _boot(c, 27, 28)
    # Посох наискось, кристалл впереди вверху.
    c.line(15, 25, 25, 22, METAL, 1)
    c.line(15, 26, 25, 23, METAL, 1)
    _crystal(c, 27, 19)
    # Мантия вдоль земли, подол у щиколотки.
    c.poly([(12, 23), (17, 22), (26, 25), (26, 29), (10, 29)], SEA)
    _fold(c, 16, 25, 24, 27)
    c.rect(26, 25, 26, 29, GOLD)
    c.rect(27, 27, 30, 29, DARK)
    c.rect(29, 25, 30, 26, DARK)
    c.line(20, 25, 23, 22 - i, NAVY, 3)
    c.line(23, 22 - i, 25, 24, NAVY, 3)
    # Рука сзади упёрта в землю, ближняя держит посох.
    _sleeve(c, 12, 25, 7, 28)
    c.line(15, 24, 18, 23, SEA, 3)
    c.rect(18, 22, 19, 23, SKIN)
    # Голова откинута: лицо, волосы и шляпа, съехавшая на затылок.
    c.rect(9, 21, 11, 25, METAL)
    c.rect(11, 21, 16, 24, SKIN)
    c.rect(12, 25, 15, 25, SKIN)
    c.set(17, 23, SKIN)
    c.line(6, 22, 17, 19, SEA, 1)
    c.line(6, 23, 12, 21, SEA, 1)
    c.poly([(8, 21), (15, 19), (10, 16), (7, 17)], SEA)
    c.line(8, 20, 15, 18, GOLD, 1)
    _px(c, ((6, 17), (5, 18), (5, 19)), SEA)
    c.finish()
    c.set(15, 22, K)
    c.set(15, 23, K)
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def mage_crouch(i):
    """Присед: мантия собрана у земли, шляпа опущена, посох вперёд наискось. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    for sign in (-1, 1):
        _boot(c, 15 + sign * 3 + step * sign, 29)
    c.line(20, 27, 27, 21, METAL, 1)
    c.line(21, 27, 28, 21, METAL, 1)
    _crystal(c, 28, 18)
    _head(c, 20, 0, i)
    hem = _robe(c, 24, 28, 8, 22, 11, 17, belt=False)
    _fold(c, 14, 26, 13 - step, 27)
    c.line(16, 26, 20, 26, NAVY, 3)
    c.line(16, 25, 20, 25, SEA, 3)
    c.rect(21, 24, 21, 26, GOLD)
    c.rect(22, 24, 23, 25, SKIN)
    c.shade()
    _trim(c, hem)
    c.outline()
    _eye(c, 20)
    return c


def mage_hang(i):
    """На лиане: руки вверх к точке хвата (центр сверху), голова запрокинута, посох за спиной,
    подол и ноги качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    # Посох за спиной наискось, кристалл над правым плечом.
    c.line(8, 25, 23, 11, METAL, 1)
    c.line(9, 25, 24, 11, METAL, 1)
    _crystal(c, 25, 8)
    c.line(13, 15, 15, 2, NAVY, 3)
    for sign in (-1, 1):
        fx = 15 + sign * 2 + sw * 2
        c.line(15 + sign * 2, 22, fx, 28, NAVY, 3)
        _boot(c, fx, 29)
    hem = _robe(c, 14, 26, 10 + sw, 21 + sw)
    _fold(c, 15, 22, 15 + sw, 25)
    _head(c, 9, -3, 0)
    # Ближняя рука поверх полей шляпы, манжет у кисти.
    c.line(19, 16, 17, 3, NAVY, 3)
    c.line(19, 15, 17, 2, SEA, 3)
    c.rect(16, 4, 18, 4, GOLD)
    c.rect(14, 1, 15, 2, SKIN)
    c.rect(16, 1, 18, 3, SKIN)
    c.shade()
    _trim(c, hem)
    c.outline()
    _eye(c, 9, -3)
    return c


# --- Гоблин ------------------------------------------------------------------------------------
# Сутулый зелёный коротышка: большая голова, длинный нос, огромное острое ухо, бурая рубаха,
# дубинка с шипами. Шаг и рост повторяют скелета пиратов.

def goblin_side(phase):
    """Гоблин сбоку, лицом влево (навстречу герою): шаг по фазе, дубинка впереди."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(18, 16 - bob, 18 - 4 * s, 21 - bob, TAN, 2)
    for sign in (-1, 1):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (23 - bob + foot[1]) / 2)
        c.line(16, 23 - bob, knee[0], knee[1], TAN, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], TAN, 2)
        c.rect(foot[0] - 3, foot[1], foot[0] + 1, foot[1] + 1, TAN)
    # Горб и рубаха с рваным подолом, пояс.
    c.ellipse(17, 17 - bob, 4.5, 4.5, TAN)
    c.rect(12, 15 - bob, 20, 22 - bob, METAL)
    for x in range(12, 21, 2):
        c.set(x, 23 - bob, METAL)
    c.rect(12, 20 - bob, 20, 20 - bob, DARK)
    # Дубинка: рукоять и толстый конец с шипами.
    tip = (3, 16 - bob + s)
    c.line(11, 20 - bob, tip[0], tip[1], METAL, 2)
    c.line(8, 18.3 - bob + s * 0.4, tip[0], tip[1], METAL, 4)
    c.line(5.5, 17.4 - bob + s * 0.8, tip[0] - 1, tip[1], METAL, 5)
    c.line(15, 16 - bob, 11, 20 - bob, TAN, 3)
    # Голова: челюсть вперёд, нос крючком, ухо назад и вверх.
    c.ellipse(14, 9 - bob, 5.5, 4.8, TAN)
    c.rect(10, 11 - bob, 16, 13 - bob, TAN)
    c.poly([(10, 8 - bob), (4, 11 - bob), (10, 12 - bob)], TAN)
    c.poly([(16, 6 - bob), (27, 1 - bob), (25, 6 - bob), (19, 11 - bob)], TAN)
    c.finish()
    c.line(19, 7 - bob, 24, 4 - bob, PLUM, 1)
    c.rect(11, 7 - bob, 12, 8 - bob, GOLD)
    c.set(11, 8 - bob, K)
    _px(c, ((10, 6 - bob), (11, 6 - bob), (12, 5 - bob), (13, 5 - bob)), K)
    c.rect(8, 13 - bob, 12, 13 - bob, K)
    c.set(9, 12 - bob, WHITE)
    c.set(12, 12 - bob, WHITE)
    _px(c, ((tip[0] - 2, tip[1] - 2), (tip[0] + 1, tip[1] - 3), (tip[0] - 3, tip[1] + 1)), GREY)
    return c


def goblin_front(phase):
    """Гоблин лицом к камере: идёт на игрока, уши в стороны, дубинка в поднятой руке."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, TAN, 3)
        c.rect(x - 2, 28 - lift, x + 2, 29 - lift, TAN)
    # Дубинка в правой (для зрителя) руке, левая висит.
    top = (27, 13 - bob - s)
    c.line(24, 20 - bob, top[0], top[1], METAL, 2)
    c.line(25.5, 16.5 - bob, top[0], top[1], METAL, 4)
    c.line(26.5, 14 - bob, top[0], top[1] - 1, METAL, 5)
    c.line(11, 15 - bob, 8, 20 - bob + s * 2, TAN, 3)
    c.line(20, 15 - bob, 24, 20 - bob, TAN, 3)
    c.rect(12, 14 - bob, 19, 22 - bob, METAL)
    for x in range(12, 20, 2):
        c.set(x, 23 - bob, METAL)
    c.rect(12, 20 - bob, 19, 20 - bob, DARK)
    # Уши шире плеч, голова с тяжёлой челюстью.
    c.poly([(10, 6 - bob), (1, 2 - bob), (4, 8 - bob), (10, 11 - bob)], TAN)
    c.poly([(21, 6 - bob), (30, 2 - bob), (27, 8 - bob), (21, 11 - bob)], TAN)
    c.ellipse(15.5, 8 - bob, 6, 5, TAN)
    c.rect(11, 10 - bob, 20, 13 - bob, TAN)
    c.finish()
    c.line(4, 4 - bob, 8, 7 - bob, PLUM, 1)
    c.line(27, 4 - bob, 23, 7 - bob, PLUM, 1)
    for x0, d in ((12, 1), (18, -1)):
        c.rect(x0, 7 - bob, x0 + 1, 8 - bob, GOLD)
        c.set(x0 + (1 if d > 0 else 0), 8 - bob, K)
        c.set(x0 + (0 if d > 0 else 1), 6 - bob, K)
        c.set(x0 + (1 if d > 0 else 0), 5 - bob + 1, K)
    c.rect(15, 9 - bob, 16, 10 - bob, TAN)
    c.rect(12, 12 - bob, 19, 12 - bob, K)
    c.set(13, 11 - bob, WHITE)
    c.set(18, 11 - bob, WHITE)
    _px(c, ((top[0] - 2, top[1] - 2), (top[0] + 2, top[1] - 2), (top[0], top[1] - 3)), GREY)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Золотая руна вращается: шесть кадров, восьмигранная плашка с вырезанным знаком."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 8.0)
    cx = 15.5
    c.poly([(cx - rx * 0.6, 5), (cx + rx * 0.6, 5), (cx + rx, 9), (cx + rx, 22), (cx + rx * 0.6, 26),
            (cx - rx * 0.6, 26), (cx - rx, 22), (cx - rx, 9)], GOLD)
    c.finish()
    if rx > 3.5:
        k = rx / 8.0
        # Знак: ствол с двумя ветвями вверх.
        for x0, y0, x1, y1 in ((-0.5, 9, -0.5, 22), (0.5, 9, 0.5, 22), (0, 16, 4, 10), (0, 16, -4, 10),
                               (0, 17, 4, 11), (0, 17, -4, 11)):
            c.line(cx + x0 * k, y0, cx + x1 * k, y1, DARK, 1)
        c.line(cx - rx + 2, 9, cx - rx + 2, 13, WHITE, 1)
    return c


def flag(i):
    """Знамя гильдии на древке с кристаллом: фиолетовое полотнище с ласточкиным хвостом,
    золотая кайма и полумесяц, идёт волной."""
    c = Canvas()
    c.rect(5, 4, 6, 31, METAL)
    for dy, half in ((-3, 0), (-2, 1), (-1, 1), (0, 0)):
        c.rect(5 - half, 3 + dy, 6 + half, 3 + dy, AQUA)
    top = []
    bottom = []

    def wave(x):
        return math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0

    for x in range(8, 30):
        top.append((x, 6 + wave(x)))
        bottom.append((x, 19 + wave(x)))
    notch = [(25, 12.5 + wave(25))]
    c.poly(top + notch + bottom[::-1], VIOLET)
    c.shade()
    # Кайма по верхней и нижней кромке.
    for x in range(8, 30):
        col = [y for y in range(32) if c.get(x, y) in (VIOLET, PLUM)]
        if col:
            c.set(x, col[0], GOLD)
            c.set(x, col[-1], BRASS)
    c.outline()
    mid = wave(16) * 0.6
    c.ellipse(15.5, 12.5 + mid, 3.2, 3.2, GOLD)
    c.ellipse(17, 11.5 + mid, 2.6, 2.6, VIOLET)
    c.set(20, 11 + mid, SKY)
    c.set(21, 14 + mid, GOLD)
    c.set(5, 1, SKY)
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


def _root(c, y0, amp, shift, thick=3):
    """Корень поперёк плитки: волна с периодом в плитку, свет сверху, тень снизу."""
    for x in range(32):
        y = int(round(y0 + amp * math.sin(2 * math.pi * x / 32.0 + shift)))
        c.rect(x, y, x, y + thick - 1, METAL)
        c.set(x, y, BRASS)
        c.set(x, y + thick, K)


def ground(inner=False):
    """Земля: корни великого дерева в тёмной почве; у кромки сверху шапка мха с каплями росы."""
    c = Canvas()
    c.rect(0, 0, 31, 31, DARK)
    rng = random.Random(7 if inner else 3)
    for _ in range(26):
        x, y = rng.randint(0, 31), rng.randint(0, 31)
        c.set(x, y, PLUM)
        if rng.random() < 0.3:
            c.set((x + 1) % 32, y, PLUM)
    for x, y in ((4, 20), (22, 29), (27, 8)) if inner else ((6, 19), (25, 29)):
        c.rect(x, y, x + 1, y, GREY)
        c.set(x + 1, y + 1, PLUM)
    if inner:
        _root(c, 3, 1.5, 0.5)
        _root(c, 13, 2.5, 2.6, 4)
        _root(c, 24, 2.0, 4.4)
        # Отросток между корнями.
        c.line(9, 17, 12, 22, METAL, 1)
        c.line(10, 17, 13, 22, DARK, 1)
    else:
        _root(c, 12, 2.0, 1.0, 4)
        _root(c, 23, 2.5, 3.6)
        c.line(20, 16, 23, 21, METAL, 1)
        # Мох: шапка в шесть строк с неровным краем, свисающие пряди.
        for x in range(32):
            depth = 5 + int(round(1.5 * math.sin(2 * math.pi * x / 16.0) + 0.8 * math.sin(2 * math.pi * x / 32.0 * 3 + 1)))
            c.rect(x, 0, x, depth, TAN)
            c.set(x, depth + 1, K)
        for x, n in ((3, 3), (12, 2), (19, 4), (28, 2)):
            c.rect(x, 5, x, 6 + n, TAN)
            c.set(x, 7 + n, K)
        c.rect(0, 0, 31, 0, SKY)
        for x in range(0, 32, 2):
            c.set(x + (1 if (x // 2) % 3 == 0 else 0), 1, SKY)
        for x, y in ((5, 3), (14, 4), (22, 2), (29, 4), (9, 2)):
            c.set(x, y, PLUM)
        for x, y in ((17, 3), (26, 3)):
            c.set(x, y, GOLD)
    return c


def rock():
    """Рунный камень: сиреневый менгир со светящимся знаком, мох у подножия и на макушке."""
    c = Canvas()
    c.poly([(5, 29), (5, 17), (8, 8), (14, 3), (21, 5), (26, 13), (27, 29)], GREY)
    c.ellipse(8, 28, 4, 2, TAN)
    c.ellipse(24, 28.5, 3, 1.5, TAN)
    c.poly([(10, 7), (14, 4), (18, 5), (13, 8)], TAN)
    c.finish()
    # Трещины и знак: ствол с двумя ветвями, вокруг искры.
    c.line(21, 9, 23, 15, PLUM, 1)
    c.line(8, 17, 10, 22, PLUM, 1)
    c.rect(14, 11, 15, 23, AQUA)
    c.line(15, 13, 19, 10, AQUA, 1)
    c.line(16, 13, 20, 10, AQUA, 1)
    c.line(15, 18, 19, 15, AQUA, 1)
    c.line(16, 18, 20, 15, AQUA, 1)
    c.rect(14, 13, 14, 19, SKY)
    c.set(11, 12, SKY)
    c.set(22, 19, SKY)
    return c


def chest():
    """Сундук-мимик: крышка приподнята, в щели два ряда зубов, язык наружу, глаза на крышке."""
    c = Canvas()
    c.ellipse(15.5, 12, 12, 7, METAL)
    c.rect(4, 12, 27, 28, METAL)
    for x in (8, 22):
        c.rect(x, 6, x + 1, 28, BRASS)
    c.rect(4, 20, 27, 20, BRASS)
    c.finish()
    # Пасть и зубы: верхние висят с крышки, нижние торчат навстречу.
    c.rect(5, 13, 26, 19, K)
    c.rect(4, 12, 27, 12, DARK)
    for x in (6, 11, 16, 21):
        c.rect(x, 13, x + 3, 13, WHITE)
        c.rect(x + 1, 14, x + 2, 15, WHITE)
        c.set(x + 3, 13, GREY)
    for x in (8, 13, 19, 23):
        c.rect(x, 19, x + 2, 19, WHITE)
        c.rect(x + 1, 17, x + 1, 18, WHITE)
        c.set(x + 2, 19, GREY)
    # Язык через край до пола.
    c.rect(14, 17, 18, 24, RED)
    c.ellipse(17, 25, 2.6, 2.2, RED)
    c.line(16, 18, 17, 25, PLUM, 1)
    c.rect(13, 17, 13, 24, K)
    c.rect(19, 17, 19, 22, K)
    # Глаза исподлобья.
    for x in (11, 18):
        c.rect(x, 8, x + 2, 9, GOLD)
        c.set(x + 1, 9, K)
    _px(c, ((10, 6), (11, 7), (12, 7), (13, 7), (21, 6), (20, 7), (19, 7), (18, 7)), K)
    return c


# --- Слоты вне основы: летун, ползун, ключ, зелье, снаряд --------------------------------------

def wisp(i):
    """Блуждающий огонёк летит вправо: бирюзовое пламя с белой сердцевиной и глазами, языки
    пламени тянутся назад и вверх. Четыре кадра мерцания, тело по центру кадра."""
    c = Canvas()
    tails = (((6, 9), (4, 17), (9, 3)), ((5, 11), (3, 19), (10, 5)), ((7, 8), (5, 16), (8, 4)),
             ((4, 10), (4, 18), (11, 4)))[i]
    for tx, ty in tails:
        c.poly([(13, 12), (tx, ty), (12, 20)], AQUA)
    c.poly([(11, 21), (tails[1][0] + 2, 23), (15, 23)], AQUA)
    c.ellipse(17, 16, 7.5, 7, AQUA)
    c.ellipse(18, 16.5, 5.2, 4.8, SKY)
    c.ellipse(18.5, 17, 3.6, 3.2, WHITE)
    c.finish()
    # Глаза и искры.
    for x in (17, 21):
        c.rect(x, 15, x, 17, K)
    sparks = (((3, 6), (27, 5)), ((2, 13), (26, 26)), ((5, 25), (28, 8)), ((2, 8), (25, 27)))[i]
    for x, y in sparks:
        c.set(x, y, SKY)
    return c


def slime(i):
    """Слизь ползёт: купол сжимается и вытягивается, четыре кадра. Блик, глаза, пузыри, внизу
    лужица шире купола."""
    c = Canvas()
    rx, ry = ((10.5, 12), (12, 9.5), (10.5, 12), (9, 14.5))[i]
    for x in range(32):
        d = (x - 15.5) / rx
        if abs(d) < 1.0:
            top = 30 - ry * math.sqrt(1.0 - d * d) ** 0.8
            c.rect(x, int(round(top)), x, 30, TAN)
    lo, hi = int(round(15.5 - rx)) - 2, int(round(15.5 + rx)) + 2
    c.rect(lo, 29, hi, 30, TAN)
    c.rect(lo - 1, 30, hi + 1, 30, TAN)
    c.finish()
    ey = int(round(30 - ry * 0.55))
    for x in (12, 19):
        c.rect(x, ey - 1, x + 1, ey + 1, WHITE)
        c.rect(x + 1, ey, x + 1, ey + 1, K)
    c.rect(14, ey + 3, 18, ey + 3, K)
    c.set(13, ey + 2, K)
    c.set(19, ey + 2, K)
    # Блик слева сверху и пузыри внутри.
    hy = int(round(30 - ry * 0.85))
    c.rect(9, hy + 1, 10, hy + 2, SKY)
    c.set(11, hy, SKY)
    for x, y in ((22, ey + 4), (8, 27), (24, 26 - i % 2)):
        c.set(x, y, SKY)
    return c


def key():
    """Золотой ключ: головка ромбом с бирюзовым камнем, бородка в два зубца."""
    c = Canvas()
    c.poly([(3, 16), (10, 8), (17, 16), (10, 24)], GOLD)
    c.rect(16, 15, 29, 17, GOLD)
    c.rect(23, 18, 24, 22, GOLD)
    c.rect(27, 18, 28, 21, GOLD)
    c.rect(16, 15, 29, 15, WHITE)
    c.finish()
    for dy, half in ((-3, 0), (-2, 1), (-1, 2), (0, 2), (1, 2), (2, 1), (3, 0)):
        c.rect(10 - half, 16 + dy, 10 + half, 16 + dy, AQUA)
    c.set(9, 14, SKY)
    c.set(9, 15, SKY)
    return c


def potion():
    """Зелье маны: круглая колба с синей жидкостью, горлышко с пробкой, золотая звезда."""
    c = Canvas()
    c.ellipse(15.5, 20, 9, 8.5, GREY)
    c.rect(13, 6, 18, 12, GREY)
    c.rect(11, 8, 20, 9, GREY)
    c.rect(13, 3, 18, 6, METAL)
    c.finish()
    # Жидкость до плеч колбы, пена, блик стекла.
    for y in range(16, 28):
        for x in range(6, 26):
            if ((x - 15.5) / 7.5) ** 2 + ((y - 20) / 7.0) ** 2 <= 1.0:
                c.set(x, y, AQUA if y == 16 else SEA)
    c.rect(10, 17, 11, 21, SKY)
    c.set(11, 23, SKY)
    c.set(14, 7, WHITE)
    c.set(14, 10, WHITE)
    _px(c, ((17, 20), (16, 21), (17, 21), (18, 21), (17, 22), (15, 21), (19, 21), (17, 19), (17, 23)), GOLD)
    c.set(20, 18, AQUA)
    c.set(18, 24, AQUA)
    return c


def fireball():
    """Снаряд 16×16: огненный шар с белым ядром и языками пламени по кругу."""
    c = Canvas(16, 16)
    for k in range(6):
        a = k * math.pi / 3.0 + 0.3
        c.line(8, 8, 8 + math.cos(a) * 7, 8 + math.sin(a) * 7, RED, 2)
    c.ellipse(8, 8, 5.5, 5.5, RED)
    c.ellipse(8, 8, 4, 4, GOLD)
    c.ellipse(7, 7, 2, 2, WHITE)
    return c


# --- Параллакс ---------------------------------------------------------------------------------

def par_sky():
    """Дальний слой: сумеречные облака полосами, луна и первые звёзды. Лента 256×48, стыкуется
    по краям."""
    c = Canvas(256, 48)
    rng = random.Random(23)
    for _ in range(40):
        x, y = rng.randint(0, 255), rng.randint(0, 40)
        c.set(x, y, WHITE if rng.random() < 0.5 else SKY)
    for x, y in ((44, 8), (150, 5), (232, 30)):
        _px(c, ((x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)), SKY)
        c.set(x, y, WHITE)
    # Луна с тенью по правому краю и кратерами.
    c.ellipse(196, 14, 9, 9, GREY)
    c.ellipse(194.5, 13, 7.5, 7.5, WHITE)
    c.ellipse(192, 10, 2, 1.5, GREY)
    c.ellipse(197, 16, 1.5, 1.5, GREY)
    c.set(190, 16, GREY)
    # Облака: длинные полосы, верх сиреневый со светом, низ в тени.
    for cx, cy, r in ((28, 20, 20), (62, 26, 14), (112, 14, 17), (140, 34, 22), (176, 28, 13), (236, 22, 18),
                      (88, 40, 16), (212, 40, 15)):
        for k in (0, 256, -256):
            c.ellipse(cx + k, cy + 1, r, 1.6, PLUM)
            c.ellipse(cx + k + r * 0.5, cy + 2.5, r * 0.6, 1, PLUM)
            c.ellipse(cx + k - r * 0.2, cy, r * 0.8, 1.6, VIOLET)
            c.ellipse(cx + k - r * 0.5, cy - 1.5, r * 0.45, 1, VIOLET)
            c.ellipse(cx + k - r * 0.45, cy - 2, r * 0.3, 0.5, GREY)
    return c


def _island(c, cx, cy, w, h, fall=None, seed=1):
    """Летающий остров: трава сверху, скала клином вниз, сбоку водопад в пустоту."""
    rng = random.Random(seed)
    half = w
    for d in range(h):
        k = 1.0 - d / float(h)
        half = max(0.0, min(half, w * k ** 0.6 + rng.uniform(-1.0, 0.6)))
        lo, hi = int(round(cx - half)), int(round(cx + half * 0.9))
        if hi < lo:
            break
        c.rect(lo, cy + d, hi, cy + d, VIOLET)
        c.rect(lo, cy + d, lo + max(0, int(half * 0.25)), cy + d, GREY)
        c.rect(hi - max(0, int(half * 0.35)), cy + d, hi, cy + d, PLUM)
    c.rect(cx - w, cy - 1, cx + w - 1, cy, TAN)
    c.rect(cx - w + 2, cy - 2, cx + w - 4, cy - 2, TAN)
    if fall is not None:
        fx, length = fall
        for d in range(length):
            y = cy + d
            if y > 47:
                break
            fade = d > length * 0.6
            if fade and d % 3 == 0:
                continue
            c.set(fx, y, WHITE if d < 2 else AQUA)
            if not fade or d % 2 == 0:
                c.set(fx + 1, y, SKY if d % 4 == 1 else AQUA)
        for dx, dy in ((-2, 0), (3, 1), (0, 2), (-1, -2), (4, -1)):
            c.set(fx + dx, min(47, cy + length + dy), SKY)


def par_far():
    """Средний слой: великое дерево с сиреневой кроной, летающие острова с водопадами и башней
    мага, внизу сплошная кромка дальнего леса. Лента 256×48."""
    c = Canvas(256, 48)

    def ridge(x):
        return 8 + 3 * math.sin(2 * math.pi * x / 128.0) + 2 * math.sin(2 * math.pi * x / 64.0 + 1.0) \
            + 2.5 * abs(math.sin(2 * math.pi * x / 32.0 + 0.4))

    # Великое дерево: ствол с корнями, ветви, крона гроздьями.
    for y in range(18, 48):
        k = (y - 18) / 29.0
        half = 4.5 + 7.0 * k ** 3
        c.rect(int(128 - half), y, int(128 + half), y, NAVY)
        c.rect(int(128 - half), y, int(128 - half) + 1, y, PLUM)
    for x1, y1, t in ((100, 15, 3), (156, 14, 3), (114, 9, 2), (143, 8, 2), (88, 19, 2), (170, 18, 2)):
        c.line(128, 24, x1, y1, NAVY, t)
    crown = ((128, 9, 23, 7), (103, 14, 15, 6), (154, 13, 16, 6), (117, 6, 12, 5), (141, 6, 12, 5),
             (89, 18, 8, 4), (169, 17, 9, 4))
    for cx, cy, rx, ry in crown:
        c.ellipse(cx + 1, cy + 2, rx, ry, PLUM)
    for cx, cy, rx, ry in crown:
        c.ellipse(cx, cy, rx, ry, VIOLET)
    for cx, cy, rx, ry in crown:
        c.ellipse(cx - rx * 0.3, cy - ry * 0.45, rx * 0.5, ry * 0.3, GREY)
        for k in range(3):
            c.set(cx + rx * (0.2 * k - 0.1), cy + ry * 0.3 - k % 2, PLUM)
    # Лианы под кроной и огни в листве.
    for x, n in ((96, 6), (110, 9), (146, 8), (160, 5), (120, 5), (137, 4)):
        c.line(x, 19, x, 19 + n, PLUM, 1)
    for x, y in ((106, 12), (124, 5), (150, 11), (134, 12), (92, 17), (166, 15)):
        c.set(x, y, GOLD)
    # Острова: большой с башней слева, с рощей справа, два малых.
    _island(c, 38, 17, 15, 13, fall=(47, 22), seed=4)
    c.rect(31, 6, 34, 15, GREY)
    c.rect(34, 6, 34, 15, VIOLET)
    c.poly([(29, 6), (32.5, 0), (36, 6)], PLUM)
    c.set(32, 9, GOLD)
    c.set(32, 13, GOLD)
    for x in (41, 45):
        c.ellipse(x, 13, 2.5, 2.5, VIOLET)
        c.set(x - 1, 12, GREY)
    _island(c, 214, 13, 17, 14, fall=(203, 26), seed=9)
    for x, r in ((207, 3), (214, 4), (222, 3)):
        c.ellipse(x, 10 - r * 0.5, r, r, VIOLET)
        c.ellipse(x - 1, 9 - r * 0.6, r * 0.5, r * 0.4, GREY)
    _island(c, 72, 30, 7, 6, seed=2)
    _island(c, 180, 27, 6, 6, fall=(183, 12), seed=6)
    _island(c, 244, 33, 6, 5, seed=5)
    # Дальний лес: зубчатая кромка, свет по макушкам, туман между стволами.
    for x in range(256):
        top = 47 - int(ridge(x))
        c.rect(x, top, x, 47, PLUM)
        c.set(x, top, VIOLET)
        if ridge(x) - ridge(x - 1) > 0.25:
            c.set(x, top + 1, VIOLET)
    for y in range(40, 48):
        k = (y - 18) / 29.0
        half = 4.5 + 7.0 * k ** 3
        c.rect(int(128 - half) + 2, y, int(128 + half) - 1, y, NAVY)
    return c


def par_mid():
    """Ближний слой: тёмные кусты подлеска с сиреневой кромкой, светящиеся грибы и светлячки.
    Лента 256×32."""
    c = Canvas(256, 32)
    for x in range(256):
        crest = 8 + 3 * math.sin(x * math.pi / 32.0) - 3.0 * abs(math.sin(x * math.pi / 8.0 + 0.3))
        top = int(round(crest))
        c.rect(x, top, x, 31, NAVY)
        c.set(x, top, VIOLET)
        c.set(x, top + 1, PLUM)
        if abs(math.sin(x * math.pi / 8.0 + 0.3)) > 0.8:
            c.set(x, top + 2, PLUM)
        if (x * 7 + top * 3) % 19 == 0:
            c.rect(x, top + 6 + (x % 9), x + 1, top + 6 + (x % 9), PLUM)
    for x, y in ((14, 20), (58, 24), (101, 19), (147, 25), (190, 21), (233, 23)):
        c.rect(x, y + 2, x, y + 4, GREY)
        c.rect(x - 2, y + 1, x + 2, y + 1, AQUA)
        c.rect(x - 1, y, x + 1, y, AQUA)
        c.set(x - 1, y, SKY)
        c.set(x + 3, y + 5, SEA)
        c.set(x - 3, y + 5, SEA)
    for x, y in ((30, 14), (77, 17), (122, 13), (168, 18), (212, 14), (250, 16)):
        c.set(x, y, GOLD)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: маг платформера, гоблин, вещи, земля, три слоя
    дали. Ключи и размеры те же, что у `space16.sprites()`."""
    return {
        "enemy_walk": strip([goblin_side(p) for p in base.phases()]),
        "enemy_front": strip([goblin_front(p) for p in base.phases()]),
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
        "hero_run": strip([mage_side(p) for p in base.phases()]),
        "hero_jump": mage_side(0.0, jump=True),
        "hero_leap": strip([mage_leap(i) for i in range(4)]),
        "hero_idle": strip([mage_idle(i) for i in range(2)]),
        "hero_back": strip([mage_back(p) for p in base.phases()]),
        "hero_slide": strip([mage_slide(i) for i in range(2)]),
        "hero_hang": strip([mage_hang(i) for i in range(2)]),
        "hero_crouch": strip([mage_crouch(i) for i in range(2)]),
    }


def extras():
    """Слоты вне `sprites()`: летун (блуждающий огонёк), ползун (слизь), ключ, зелье маны и
    снаряд (огненный шар) тех же размеров, что у остальных сеттингов."""
    return {
        "parrot_fly": strip([wisp(i) for i in range(4)]),
        "crab_walk": strip([slime(i) for i in range(4)]),
        "key": key(),
        "medkit": potion(),
        "shot": fireball(),
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


def save_sheet(path, items, scale=3, pad=6, back=(0x6C, 0x66, 0xA4, 255), max_w=640):
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


def preview(path, scale=4, keys=None, back=(0x6C, 0x66, 0xA4, 255)):
    """Лист набора: лента на строку после светотени, затем `extras()`. Фон сиреневый, как
    сумерки за кадром игры: на нём видно, держит ли обводка. `keys` оставляет часть лент."""
    items = shaded(sprites())
    items.update(shaded(extras()))
    if keys:
        items = {k: items[k] for k in keys if k in items}
    save_sheet(path, items, scale=scale, back=back, max_w=256)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        args = sys.argv
        scale_ = 4
        keys_ = None
        for a in args:
            if a.startswith("--scale="):
                scale_ = int(a.split("=", 1)[1])
            if a.startswith("--keys="):
                keys_ = a.split("=", 1)[1].split(",")
        preview(args[args.index("--preview") + 1], scale_, keys_)
