#!/usr/bin/env python3
"""Набор «Офис» для 16/32-bit, сравнительная версия (#138, состав в `docs/specs/settings.md`):
клерк в белой рубашке с красным галстуком и в очках, одинаковые сотрудники в чёрных костюмах с
усами и папкой под мышкой, бумажный самолётик, робот-пылесос, жетон на кофе. Те же ленты и
кадры, что у пиратов и космоса (`pixel_sprites16.py`, `space16.py`), позы и точка опоры ног
повторяют космонавта, чтобы хитбоксы демок сходились, рисунок свой.

    python3 tools/office16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Офис»: 16 цветов, индекс это та же роль, что у пиратов и космоса (ими рисуют HUD и мир
# демки: NAVY, SEA, AQUA, SKY идут градиентом стены сверху вниз, SEA заливает низ под далью).
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x14, 0x14, 0x1C),  # K      обводка
    (0x1A, 0x22, 0x48),  # NAVY   тень брюк, верх стены
    (0x31, 0x4A, 0x92),  # SEA    тёмно-синие брюки, ткань перегородок
    (0x58, 0xB2, 0xDC),  # AQUA   экран монитора, бейдж
    (0xC8, 0xEA, 0xF5),  # SKY    блик экрана, стекло очков, свет ламп
    (0xF4, 0xF5, 0xF8),  # WHITE  рубашка, бумага
    (0xB7, 0xBF, 0xCF),  # GREY   тень рубашки и бумаги, пластик
    (0xF2, 0xC8, 0x9A),  # SKIN   кожа
    (0xC9, 0x8F, 0x5E),  # TAN    тень кожи
    (0xF6, 0xCD, 0x4C),  # GOLD   жетон, стикер, папка
    (0xBB, 0x84, 0x3A),  # BRASS  тень золота, картон
    (0x7A, 0x82, 0x94),  # METAL  серый металл и пластик: сейф, плита, пылесос
    (0x2E, 0x31, 0x40),  # DARK   чёрный костюм, волосы, ботинки
    (0xDA, 0x3A, 0x36),  # RED    галстук, опасность
    (0x4F, 0x9C, 0x86),  # VIOLET ковролин, зелень в горшках
    (0x2A, 0x60, 0x5C),  # PLUM   тень ковролина
]
# Красное без тени: галстук тонкий, от тени по краю от него осталась бы одна тёмная нитка.
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, VIOLET: PLUM}
# Материалы для светотени рампами: рубашка и бумага, брюки, стекло, кожа, золото и картон,
# серый пластик, чёрный костюм отдельно от пластика (иначе папка и пиджак сливаются кромкой).
GROUPS = {WHITE: "paper", GREY: "paper", SEA: "pants", NAVY: "pants", AQUA: "glass", SKY: "glass",
          SKIN: "skin", TAN: "skin", GOLD: "gold", BRASS: "gold", METAL: "metal", DARK: "suit", RED: "red",
          VIOLET: "carpet", PLUM: "carpet"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Клерк -------------------------------------------------------------------------------------
# Силуэт: голова без шлема с чубом вперёд, узкие плечи, тонкие руки с закатанными рукавами,
# галстук, который в беге летит за спину, и ботинки с носком. Узнаётся по красному галстуку,
# очкам и голубому бейджу на груди.

def _head(c, x, y, face=1):
    """Голова в профиль, лицом вправо при `face` 1. Центр (x, y): волосы шапкой сверху и на
    затылке, чуб выдаётся вперёд надо лбом, нос."""
    c.ellipse(x, y, 4.8, 5, SKIN)
    for yy in range(int(y) - 6, int(y) + 3):
        for xx in range(int(x) - 6, int(x) + 7):
            if c.get(xx, yy) != SKIN:
                continue
            back = (xx - x) * face
            if yy <= y - 3 or (back <= -3 and yy <= y + 1) or (back <= -4 and yy <= y + 2):
                c.set(xx, yy, DARK)
    c.ellipse(x + 2.5 * face, y - 4, 3.6, 1.5, DARK)
    c.set(x + 5 * face, y + 1, SKIN)
    # Ухо за дужкой очков.
    c.set(x - 2 * face, y, TAN)


def _face(c, x, y, face=1):
    """Поверх обводки: очки (светлая линза в тёмной оправе, дужка к уху), пробор, рот."""
    c.rect(min(x + 2 * face, x + 3 * face), y - 1, max(x + 2 * face, x + 3 * face), y, SKY)
    c.set(x + 3 * face, y, WHITE)
    for dx in (1, 2, 3, 4):
        c.set(x + dx * face, y - 2, K)
    c.set(x + 4 * face, y - 1, K)
    c.set(x + 1 * face, y - 1, K)
    c.set(x + 1 * face, y, K)
    c.set(x + 2 * face, y + 1, K)
    c.set(x + 3 * face, y + 1, K)
    c.set(x, y - 1, K)
    c.set(x - 1 * face, y - 1, K)
    # Пробор: светлая косая черта в волосах.
    c.set(x + 1 * face, y - 5, METAL)
    c.set(x, y - 4, METAL)
    c.set(x + 3 * face, y + 3, TAN)


def _arm(c, x0, y0, x1, y1, far=False):
    """Рука: закатанный рукав до локтя, дальше голое предплечье и кисть. Белый рукав поверх белой
    рубашки отбит тенью снизу."""
    mx, my = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.5
    if not far:
        c.line(x0 - 1, y0 + 1, mx - 1, my + 1, GREY, 3)
    c.line(mx, my, x1, y1, TAN if far else SKIN, 2)
    c.line(x0, y0, mx, my, GREY if far else WHITE, 3)
    c.ellipse(x1, y1, 1.1, 1.1, TAN if far else SKIN)


def _shoe(c, x, y):
    """Ботинок с носком вперёд; (x, y) точка стопы, подошва на y + 1."""
    c.rect(x - 1, y, x + 3, y + 1, DARK)


def _torso(c, x0, y0, x1, y1):
    """Рубашка до пояса, ремень с пряжкой, верх брюк; (y1 это линия бёдер)."""
    c.rect(x0, y0, x1, y1 - 2, WHITE)
    c.rect(x0, y1 - 1, x1, y1 - 1, DARK)
    c.set(x1 - 1, y1 - 1, GOLD)
    c.rect(x0, y1, x1, y1, SEA)


def _badge(c, x, y):
    """Бейдж на груди: голубая карточка."""
    c.rect(x, y, x + 1, y + 2, AQUA)


def _tie(c, pts):
    """Галстук ломаной от узла к кончику: лента в два пикселя, кончик шире."""
    for a, b in zip(pts, pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
        for k in range(n + 1):
            x = int(round(a[0] + (b[0] - a[0]) * k / n))
            y = int(round(a[1] + (b[1] - a[1]) * k / n))
            c.rect(x, y, x + 1, y + 1, RED)
    c.ellipse(pts[-1][0] + 0.5, pts[-1][1] + 0.5, 1.5, 1.5, RED)


def clerk_side(phase, jump=False):
    """Клерк сбоку, лицом вправо: бег по фазе 0..2π или прыжок. Галстук летит за спину."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 14 - bob, 15 + 5 * swing, 19 - bob - (3 if jump else 0), far=True)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _shoe(c, foot[0], foot[1])
    _torso(c, 12, 12 - bob, 19, hip_y)
    _badge(c, 17, 16 - bob)
    if jump:
        _tie(c, [(18, 12), (13, 11), (9, 8)])
    else:
        wave = math.sin(phase * 2.0 + 0.6) * 1.3
        _tie(c, [(18, 12 - bob), (13, 11 - bob), (9, 11 - bob + wave)])
    _arm(c, 15, 14 - bob, 15 - 5 * swing, 19 - bob - (4 if jump else 0))
    _head(c, 16, 7 - bob)
    c.finish()
    _face(c, 16, 7 - bob)
    return c


def clerk_back(phase):
    """Со спины: бежит вглубь экрана. Затылок, лента бейджа на шее, галстук закинуло на плечо."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, SEA if sign > 0 else NAVY)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
        ax = 16 + sign * 6 - (1 if sign < 0 else 0)
        c.line(ax, 14 - bob, ax + sign * 0.5, 16 - bob, WHITE, 3)
        c.line(ax + sign * 0.5, 17 - bob, ax + sign, 19 - bob + s * sign * 2, SKIN, 2)
    _tie(c, [(19, 12 - bob), (22, 11 - bob), (24, 9 - bob + s)])
    c.rect(11, 12 - bob, 20, 19 - bob, WHITE)
    c.rect(11, 20 - bob, 20, 20 - bob, DARK)
    c.rect(11, 21 - bob, 20, 21 - bob, SEA)
    # Складка рубашки по хребту и лента бейджа под воротником.
    c.rect(15, 15 - bob, 15, 18 - bob, GREY)
    c.ellipse(15.5, 7 - bob, 5, 5, SKIN)
    for y in range(1 - bob, 9 - bob):
        for x in range(9, 23):
            if c.get(x, y) == SKIN:
                c.set(x, y, DARK)
    c.set(10, 8 - bob, SKIN)
    c.set(21, 8 - bob, SKIN)
    c.rect(13, 12 - bob, 18, 12 - bob, AQUA)
    c.finish()
    # Пробор виден и с затылка.
    c.set(18, 2 - bob, METAL)
    c.set(18, 3 - bob, METAL)
    c.set(17, 4 - bob, METAL)
    # Дужки очков за ушами.
    c.set(11, 7 - bob, K)
    c.set(20, 7 - bob, K)
    return c


def clerk_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление. Галстук
    запаздывает: висит, прижат, взлетает, падает."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 14 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 19 + crouch, far=True)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _shoe(c, foot[0], foot[1])
    _torso(c, 12, 12 + crouch, 19, hip_y)
    _badge(c, 17, 16 + crouch)
    tie = ([(18, 13), (18, 16), (19, 18)], [(18, 13), (18, 17), (18, 19)],
           [(18, 12), (13, 12), (10, 15)], [(18, 13), (20, 15), (23, 15)])[i]
    _tie(c, [(x, y + crouch) for x, y in tie])
    _arm(c, 15, 14 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 19 + crouch)
    _head(c, 16, 7 + crouch)
    c.finish()
    _face(c, 16, 7 + crouch)
    return c


def clerk_idle(i):
    """Стойка: два кадра, клерк дышит, галстук и бейдж чуть качаются."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 29, cloth)
        c.rect(x - 1, 29, x + 2, 30, DARK)
    _arm(c, 13, 14 - up, 12, 20 - up, far=True)
    _torso(c, 12, 12 - up, 19, 21)
    _badge(c, 16, 16 - up)
    _tie(c, [(18, 13 - up), (18, 16 - up), (18 + i, 18 - up)])
    _arm(c, 14, 14 - up, 14, 20 - up)
    _head(c, 16, 7 - up)
    c.finish()
    _face(c, 16, 7 - up)
    return c


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; ремень у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = DARK if k >= int(n) - 1 else WHITE
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def clerk_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх, рука
    сзади на полу, галстук задрало вверх. Макушка на 15-й строке, как у космонавта."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, NAVY, 3)
    c.line(24, 23 - i, 27, 27, NAVY, 3)
    c.rect(26, 27, 29, 28, DARK)
    _arm(c, 13, 24, 19, 23, far=True)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 27, 28, SEA, 4)
    c.rect(28, 26, 30, 29, DARK)
    _tie(c, [(15, 24), (17, 21), (17 - i, 18)])
    _arm(c, 11, 25, 6, 29)
    _head(c, 10, 21)
    c.finish()
    _face(c, 10, 21)
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def clerk_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    _arm(c, 15, 24, 19, 26, far=True)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _shoe(c, foot[0], foot[1])
    c.rect(11, 22, 18, 26, WHITE)
    _arm(c, 13, 24, 18, 27)
    _tie(c, [(19, 24), (21, 25 + i)])
    _head(c, 16, 19)
    c.finish()
    _face(c, 16, 19)
    return c


def clerk_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги и галстук свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 14.5, 8, GREY, 3)
    c.line(14.5, 8, 15, 2, TAN, 2)
    c.line(18, 13, 17.5, 8, WHITE, 3)
    c.line(17.5, 8, 17, 2, SKIN, 2)
    c.rect(14, 0, 18, 2, SKIN)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], cloth, 3)
        c.rect(foot[0] - 1, 29, foot[0] + 2, 30, DARK)
    _torso(c, 12, 13, 19, 21)
    _badge(c, 15, 17)
    _tie(c, [(18, 14), (18, 17), (18 + sw, 19)])
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    _face(hd, 16, 8)
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    # Пальцы сцеплены на тросе.
    c.set(16, 1, K)
    return c


# --- Сотрудник в костюме -----------------------------------------------------------------------
# Клон: квадратные плечи чёрного пиджака, зализанные волосы, крупные усы, которые торчат за
# контур лица, жёлтая папка под мышкой. Шаг и рост повторяют скелета пиратов.

def suit_side(phase):
    """Сотрудник сбоку, лицом влево (навстречу герою): шаг по фазе, папка прижата локтем."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Дальняя рука машет.
    c.line(15, 14 - bob, 15 - 5 * s, 19 - bob, NAVY, 3)
    c.ellipse(15 - 5 * s, 20 - bob, 1.2, 1.2, TAN)
    for sign, col in ((-1, NAVY), (1, DARK)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
        c.rect(foot[0] - 3, foot[1], foot[0] + 1, foot[1] + 1, K)
    # Пиджак: плечи шире бёдер, у горла белый воротник.
    c.rect(12, 12 - bob, 19, 22 - bob, DARK)
    c.rect(11, 12 - bob, 20, 14 - bob, DARK)
    c.rect(11, 12 - bob, 12, 14 - bob, WHITE)
    # Папка под мышкой: жёлтый прямоугольник чуть наискось, спереди торчит край бумаг.
    c.poly([(9, 16 - bob), (17, 15 - bob), (18, 22 - bob), (10, 23 - bob)], GOLD)
    c.rect(8, 17 - bob, 8, 21 - bob, WHITE)
    c.line(10, 17 - bob, 16, 16 - bob, BRASS, 1)
    # Ближняя рука прижимает папку: плечо вниз, предплечье поперёк, кисть спереди.
    c.line(18, 14 - bob, 18, 18 - bob, DARK, 3)
    c.line(18, 19 - bob, 12, 20 - bob, DARK, 3)
    c.ellipse(11, 20 - bob, 1.3, 1.3, SKIN)
    # Голова: зализанные волосы, усы щёткой вперёд за контур лица, под ними подбородок.
    hx, hy = 15.5, 6 - bob
    c.ellipse(hx, hy, 4.6, 5, SKIN)
    for yy in range(int(hy) - 6, int(hy) + 2):
        for xx in range(9, 23):
            if c.get(xx, yy) == SKIN and (yy <= hy - 4 or (xx >= hx + 3 and yy <= hy)):
                c.set(xx, yy, DARK)
    c.set(10, hy + 1, SKIN)
    c.rect(11, hy + 4, 12, hy + 4, SKIN)
    c.rect(10, hy + 2, 13, hy + 3, DARK)
    c.rect(9, hy + 3, 9, hy + 4, DARK)
    c.finish()
    c.set(13, hy - 1, K)
    c.rect(11, hy - 2, 14, hy - 2, K)
    return c


def suit_front(phase):
    """Сотрудник лицом к камере: идёт на игрока, ноги по очереди, усы шире лица."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, DARK, 4)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, K)
    # Папка под левой рукой (на экране справа), поверх неё рукав.
    c.rect(20, 14 - bob, 24, 22 - bob, GOLD)
    c.rect(20, 13 - bob, 23, 13 - bob, WHITE)
    c.line(10, 14 - bob, 8, 20 - bob - s * 2, DARK, 3)
    c.ellipse(8, 21 - bob - s * 2, 1.3, 1.3, SKIN)
    c.rect(10, 12 - bob, 21, 15 - bob, DARK)
    c.rect(11, 12 - bob, 20, 22 - bob, DARK)
    c.line(21, 14 - bob, 22, 18 - bob, DARK, 3)
    c.ellipse(22, 19 - bob, 1.3, 1.3, SKIN)
    # Манишка клином и чёрный галстук.
    c.poly([(13, 12 - bob), (18, 12 - bob), (15.5, 18 - bob)], WHITE)
    c.rect(15, 13 - bob, 16, 17 - bob, K)
    hy = 6 - bob
    c.ellipse(15.5, hy, 5, 5, SKIN)
    for yy in range(hy - 6, hy + 1):
        for xx in range(9, 23):
            if c.get(xx, yy) == SKIN and yy <= hy - 4:
                c.set(xx, yy, DARK)
    # Усы: шире лица, кончики вниз.
    c.rect(11, hy + 2, 20, hy + 2, DARK)
    c.rect(10, hy + 3, 13, hy + 3, DARK)
    c.rect(18, hy + 3, 21, hy + 3, DARK)
    c.set(9, hy + 4, DARK)
    c.set(22, hy + 4, DARK)
    c.rect(15, hy + 1, 16, hy + 1, TAN)
    c.finish()
    for x0 in (12, 17):
        c.rect(x0, hy - 2, x0 + 2, hy - 2, K)
        c.set(x0 + 1, hy - 1, K)
    return c


# --- Летун и ползун ----------------------------------------------------------------------------

def paper_plane(i):
    """Бумажный самолётик летит вправо, четыре кадра: крылья машут (вверх, середина, вниз,
    середина), нос чуть клюёт. Тело по центру кадра, чтобы при развороте не прыгало."""
    c = Canvas()
    f = (-3, 0, 3, 0)[i]
    dip = (0, 1, 0, -1)[i]
    nose = (29, 16 + dip)
    root = (9, 16)
    # Киль снизу, дальнее крыло, ближнее крыло.
    c.poly([nose, root, (12, 24 - abs(f) * 0.3)], METAL)
    c.poly([nose, (10, 15), (4, 8 + f)], GREY)
    c.poly([nose, root, (2, 13 + f * 1.6), (5, 17 + f)], WHITE)
    c.finish()
    # Линовка тетрадного листа и красное поле у хвоста.
    for k in (0.35, 0.6):
        x = int(round(nose[0] + (3.5 - nose[0]) * k))
        y = int(round(nose[1] + (15 + f * 1.3 - nose[1]) * k))
        if c.get(x, y) not in (None, K):
            c.set(x, y, AQUA)
    mark = (8, int(round(15 + f * 0.8)))
    if c.get(mark[0], mark[1]) not in (None, K):
        c.set(mark[0], mark[1], RED)
    return c


def vacuum(i):
    """Робот-пылесос ползёт, четыре кадра: плоская шайба с башенкой датчика, красные огни-глаза
    на борту, боковые щётки крутятся, корпус подрагивает."""
    c = Canvas()
    up = i % 2
    # Щётки по бокам и колёса.
    for sign in (-1, 1):
        ang = (i * 0.8 + (0 if sign > 0 else 1.6))
        for k in range(3):
            a = ang + k * 2.094
            c.line(16 + sign * 10, 28, 16 + sign * 10 + math.cos(a) * 4, 28.5 + math.sin(a) * 1.5, GOLD, 1)
        c.rect(16 + sign * 6 - 1, 28, 16 + sign * 6 + 1, 29, K)
    # Шайба: борт и крышка.
    c.ellipse(16, 25 - up, 11.5, 4, DARK)
    c.rect(5, 21 - up, 27, 25 - up, DARK)
    c.ellipse(16, 21 - up, 11.5, 4, GREY)
    c.ellipse(16, 21 - up, 8, 2.4, METAL)
    # Башенка датчика.
    c.rect(13, 15 - up, 19, 19 - up, DARK)
    c.ellipse(16, 15 - up, 3.5, 1.5, METAL)
    c.finish()
    c.rect(14, 17 - up, 18, 17 - up, AQUA)
    c.set(14 + i, 17 - up, SKY)
    # Огни-глаза на борту и бампер.
    for x in (11, 12, 20, 21):
        c.set(x, 26 - up, RED)
    c.rect(14, 27 - up, 18, 27 - up, METAL)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Жетон на кофе вращается: шесть кадров, ширина по косинусу; на лице чашка с паром."""
    c = Canvas()
    k = abs(math.cos(math.pi * i / 6.0))
    rx = max(1.0, k * 8.0)
    cx = 15.5
    c.ellipse(cx, 16, rx, 9, BRASS)
    if rx > 2.5:
        c.ellipse(cx, 16, rx - 1.6, 7.4, GOLD)
    c.finish()
    if rx > 4:
        w = rx / 8.0
        # Белая чашка с кофе, ручкой и блюдцем, над ней пар.
        c.rect(cx - 3 * w, 15, cx + 2 * w, 19, WHITE)
        c.rect(cx - 3 * w, 15, cx + 2 * w, 15, DARK)
        c.rect(cx - 2 * w, 19, cx + 1 * w, 19, GREY)
        c.rect(cx + 3 * w, 16, cx + 4 * w, 17, WHITE)
        c.rect(cx - 4 * w, 21, cx + 3 * w, 21, WHITE)
        for dx in (-2, 1):
            c.set(cx + dx * w, 13, BRASS)
            c.set(cx + (dx + 1) * w, 12, BRASS)
            c.set(cx + dx * w, 11, BRASS)
    return c


def flag(i):
    """Флажок-стикер на подставке: жёлтый листок на стойке с зажимом, нижний край гуляет волной,
    угол загнут. На листке строчки и красная галочка."""
    c = Canvas()
    c.rect(5, 4, 6, 31, METAL)
    c.rect(2, 29, 10, 31, DARK)
    c.rect(4, 2, 8, 4, DARK)
    top = []
    bottom = []
    for x in range(8, 27):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.5 * (x - 8) / 18.0
        top.append((x, 5 + w * 0.4))
        bottom.append((x, 21 + w))
    c.poly(top + bottom[::-1], GOLD)
    c.shade()
    c.outline()
    mid = math.sin(17 * 0.45 - i * math.pi / 3.0) * 0.6
    for row, x1 in enumerate((22, 20, 17)):
        c.rect(11, 8 + row * 3 + mid, x1, 8 + row * 3 + mid, BRASS)
    c.line(18, 17 + mid, 20, 19 + mid, RED, 1)
    c.line(20, 19 + mid, 24, 14 + mid, RED, 1)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(10.5, 12, 5.5, 5.5, RED)
    c.ellipse(20.5, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(8, 9, 10, 10, WHITE)
    c.set(8, 11, WHITE)
    return c.finish()


def _slab(c, y0):
    """Плита фальшпола от строки `y0` до низа: серые панели со швами, в двух лотках кабели."""
    c.rect(0, y0, 31, 31, METAL)
    c.rect(0, y0, 31, y0, GREY)
    # Лотки на строках 12..16 и 24..28: тёмный жёлоб, в нём цветные кабели волной.
    for ty, cols in ((12, (RED, AQUA)), (24, (GOLD, VIOLET))):
        if ty < y0 + 1:
            continue
        c.rect(0, ty, 31, ty + 4, DARK)
        c.rect(0, ty + 5, 31, ty + 5, GREY)
        for x in range(32):
            a = math.sin(x * math.pi / 16.0 + ty)
            c.set(x, ty + 1.5 + a, cols[0])
            c.set(x, ty + 2.5 - a, cols[1])
        # Стяжка на пучке.
        c.rect(7 if ty == 12 else 23, ty + 1, 7 if ty == 12 else 23, ty + 3, WHITE)
    # Швы панелей и винты по углам.
    for x, ya, yb in ((15, y0 + 1, 11), (31, 18, 23), (15, 30, 31)):
        if yb >= ya:
            c.rect(x, ya, x, yb, DARK)
    c.rect(0, 20, 31, 20, DARK) if y0 < 20 else None
    for x, y in ((2, 21), (28, 21), (2, 9), (28, 9), (18, 21), (12, 9)):
        if y > y0 + 1:
            c.set(x, y, GREY)


def ground(inner=False):
    """Пол офиса: ковролин с ворсом над плитой фальшпола, под ним лотки с кабелями. Внутренняя
    плитка без ковролина: та же плита, швы и кабели продолжаются вниз."""
    c = Canvas()
    if inner:
        _slab(c, 0)
        c.rect(0, 0, 31, 0, METAL)
        c.rect(0, 5, 31, 5, DARK)
        return c
    _slab(c, 7)
    # Ковролин: светлая кромка ворса, крап петель, тёмный подгиб.
    c.rect(0, 0, 31, 5, VIOLET)
    c.rect(0, 6, 31, 6, PLUM)
    for x in range(32):
        if x % 2 == 0:
            c.set(x, 0, SKY)
        for y in range(1, 6):
            if (x * 3 + y * 5) % 7 == 0:
                c.set(x, y, PLUM)
            elif (x * 5 + y * 3) % 11 == 0:
                c.set(x, y, AQUA)
    return c


def rock():
    """Коробка с бумагой: открытая картонная коробка, из неё торчит стопка листов, клапаны
    отогнуты, на боку наклейка и прорезь ручки."""
    c = Canvas()
    # Стопка бумаги, верхние листы съехали.
    c.rect(8, 7, 23, 15, WHITE)
    c.poly([(9, 4), (22, 6), (22, 9), (9, 8)], WHITE)
    # Клапаны и короб.
    c.poly([(4, 14), (0, 10), (3, 8), (8, 13)], GOLD)
    c.poly([(27, 14), (31, 9), (28, 7), (23, 13)], GOLD)
    c.rect(3, 14, 28, 28, BRASS)
    c.rect(3, 14, 28, 15, GOLD)
    c.finish()
    # Листы в стопке, наклейка, ручка, скотч.
    for y in (9, 11, 13):
        c.rect(9, y, 22, y, GREY)
    c.rect(12, 19, 19, 20, K)
    c.rect(6, 22, 11, 25, WHITE)
    c.rect(7, 23, 10, 23, METAL)
    c.rect(15, 16, 16, 18, GOLD)
    c.rect(15, 22, 16, 27, GOLD)
    return c


def chest():
    """Сейф: стальной ящик на ножках, утопленная дверца, круглый лимб с рисками, золотая ручка."""
    c = Canvas()
    c.rect(6, 28, 10, 29, DARK)
    c.rect(21, 28, 25, 29, DARK)
    c.rect(4, 6, 27, 27, METAL)
    c.rect(7, 9, 24, 24, GREY)
    c.rect(8, 10, 24, 24, METAL)
    # Петли справа.
    c.rect(25, 11, 26, 13, DARK)
    c.rect(25, 20, 26, 22, DARK)
    # Лимб и ручка.
    c.ellipse(13, 17, 4, 4, DARK)
    c.ellipse(13, 17, 2.5, 2.5, GREY)
    c.rect(19, 13, 20, 21, GOLD)
    c.rect(18, 16, 21, 18, GOLD)
    c.finish()
    c.set(13, 17, RED)
    c.set(13, 15, K)
    for x, y in ((13, 12), (13, 22), (8, 17), (18, 17)):
        c.set(x, y, WHITE)
    c.rect(9, 11, 12, 11, WHITE)
    return c


def key():
    """Ключ от кабинета: золотой, с круглой головкой и бородкой, на кольце красная бирка."""
    c = Canvas()
    c.rect(13, 12, 28, 14, GOLD)
    c.rect(22, 15, 23, 18, GOLD)
    c.rect(26, 15, 27, 17, GOLD)
    c.ellipse(9, 13, 5.5, 5.5, GOLD)
    c.ellipse(8, 13, 2, 2, None)
    # Бирка на шнурке.
    c.line(8, 16, 11, 20, METAL, 1)
    c.poly([(8, 20), (15, 20), (17, 23), (17, 28), (8, 28)], RED)
    c.finish()
    c.rect(10, 23, 14, 23, WHITE)
    c.rect(10, 25, 13, 25, WHITE)
    return c


def medkit():
    """Аптечка: белый чемоданчик с ручкой и защёлками, красный крест."""
    c = Canvas()
    c.rect(11, 6, 20, 7, DARK)
    c.rect(11, 8, 12, 10, DARK)
    c.rect(19, 8, 20, 10, DARK)
    c.rect(3, 11, 28, 28, WHITE)
    c.rect(3, 11, 28, 13, GREY)
    c.rect(7, 12, 9, 14, METAL)
    c.rect(22, 12, 24, 14, METAL)
    c.rect(13, 16, 18, 26, RED)
    c.rect(10, 19, 21, 23, RED)
    return c.finish()


def shot():
    """Снаряд сотрудника: скомканный лист с красным штампом, 16×16."""
    c = Canvas(16, 16)
    c.poly([(3, 5), (7, 2), (12, 4), (13, 9), (10, 13), (5, 12), (2, 9)], WHITE)
    c.finish()
    c.line(5, 5, 8, 8, GREY, 1)
    c.line(8, 8, 11, 6, GREY, 1)
    c.line(8, 8, 7, 11, GREY, 1)
    c.rect(9, 9, 10, 10, RED)
    c.set(5, 8, RED)
    return c


# --- Параллакс ---------------------------------------------------------------------------------
# Фон демки: градиент стены из палитры (NAVY, SEA, AQUA, SKY сверху вниз), на нём лента ламп,
# у горизонта дальний ряд перегородок, ниже ближние перегородки в цвет заливки низа (SEA).

def par_sky():
    """Дальний слой: потолочные светильники на подвесах, табличка выхода и часы, лента 256×48."""
    c = Canvas(256, 48)
    for x0 in range(10, 256, 64):
        for dx in (6, 33):
            c.rect(x0 + dx, 0, x0 + dx, 7, METAL)
        c.rect(x0, 8, x0 + 39, 12, GREY)
        c.rect(x0 + 1, 10, x0 + 38, 12, WHITE)
        c.rect(x0 + 2, 13, x0 + 37, 13, SKY)
        # Свет под лампой: редкий растр.
        for y in range(14, 22):
            for x in range(x0 + 4 + (y - 14), x0 + 36 - (y - 14)):
                if (x + y) % 2 == 0 and y % 2 == 0:
                    c.set(x, y, SKY)
    # Табличка выхода и часы между лампами.
    c.rect(56, 0, 56, 20, METAL)
    c.rect(66, 0, 66, 20, METAL)
    c.rect(53, 21, 69, 28, VIOLET)
    c.rect(53, 21, 69, 21, PLUM)
    c.rect(56, 24, 60, 25, WHITE)
    c.poly([(62, 23), (66, 24.5), (62, 26)], WHITE)
    c.ellipse(184, 30, 6, 6, METAL)
    c.ellipse(184, 30, 4.6, 4.6, WHITE)
    c.line(184, 30, 184, 27, K, 1)
    c.line(184, 30, 186, 31, K, 1)
    return c


def par_far():
    """Средний слой: дальний ряд перегородок с мониторами, кулером и цветами, лента 256×48,
    низ сплошной."""
    c = Canvas(256, 48)
    # Перегородки ступенями по 32: высота меняется, сверху светлая планка.
    for k in range(8):
        x0 = k * 32
        top = (22, 22, 26, 22, 20, 20, 26, 22)[k]
        c.rect(x0, top, x0 + 31, 47, METAL)
        c.rect(x0, top, x0 + 31, top + 1, GREY)
        c.rect(x0 + 31, top + 2, x0 + 31, 47, DARK)
        # Панели ткани: редкий крап.
        for y in range(top + 5, 47, 4):
            for x in range(x0 + 3 + (y % 8) // 2, x0 + 29, 7):
                c.set(x, y, DARK)
    # Мониторы над планкой: экран к нам или затылком.
    for x0, top, lit in ((6, 22, True), (44, 22, False), (104, 22, True), (136, 20, True), (170, 20, False),
                         (232, 22, True)):
        c.rect(x0, top - 11, x0 + 15, top - 2, DARK)
        if lit:
            c.rect(x0 + 1, top - 10, x0 + 14, top - 3, AQUA)
            c.rect(x0 + 2, top - 9, x0 + 9, top - 9, SKY)
            c.rect(x0 + 2, top - 7, x0 + 12, top - 7, SEA)
            c.rect(x0 + 2, top - 5, x0 + 7, top - 5, SEA)
        else:
            c.rect(x0 + 6, top - 7, x0 + 9, top - 6, METAL)
        c.rect(x0 + 6, top - 1, x0 + 9, top - 1, DARK)
    # Кулер в низком проёме и цветок в горшке.
    c.rect(72, 12, 79, 19, SKY)
    c.rect(73, 13, 74, 17, WHITE)
    c.rect(71, 20, 80, 25, WHITE)
    c.set(74, 22, RED)
    c.set(77, 22, AQUA)
    c.rect(204, 22, 211, 25, BRASS)
    for dx, dy in ((-3, -6), (0, -9), (3, -7), (5, -4), (-5, -3)):
        c.line(207, 22, 207 + dx, 22 + dy, VIOLET, 2)
    c.line(207, 22, 207, 15, PLUM, 1)
    # Стикеры на перегородках.
    for x, y, col in ((20, 30, GOLD), (25, 33, RED), (58, 29, GOLD), (118, 31, WHITE), (150, 28, GOLD),
                      (155, 32, AQUA), (188, 27, GOLD), (240, 30, WHITE), (246, 33, GOLD)):
        c.rect(x, y, x + 3, y + 3, col)
    return c


def par_mid():
    """Ближний слой: синие перегородки опенспейса с алюминиевой планкой, над ней торчат мониторы
    и лампы, на ткани стикеры и листки; лента 256×32, низ в цвет заливки."""
    c = Canvas(256, 32)
    c.rect(0, 8, 255, 31, SEA)
    c.rect(0, 6, 255, 7, GREY)
    c.rect(0, 8, 255, 8, METAL)
    for x in range(0, 256, 64):
        # Стойка между секциями.
        c.rect(x, 5, x + 2, 31, METAL)
        c.rect(x, 5, x + 2, 5, GREY)
        c.rect(x + 3, 9, x + 3, 31, NAVY)
    # Крап ткани.
    for y in range(10, 32, 2):
        for x in range((y // 2) % 4, 256, 6):
            if c.get(x, y) == SEA:
                c.set(x, y, NAVY)
    # Мониторы над планкой.
    for x0, lit in ((12, True), (84, True), (150, False), (210, True)):
        c.rect(x0, 0, x0 + 19, 5, DARK)
        if lit:
            c.rect(x0 + 1, 0, x0 + 18, 4, AQUA)
            c.rect(x0 + 3, 1, x0 + 12, 1, SKY)
            c.rect(x0 + 3, 3, x0 + 8, 3, WHITE)
    # Кружка и настольная лампа на планке.
    c.rect(44, 2, 47, 5, WHITE)
    c.set(48, 3, WHITE)
    c.set(45, 1, GREY)
    c.line(120, 5, 123, 1, DARK, 1)
    c.rect(123, 0, 128, 1, RED)
    c.rect(182, 3, 190, 5, WHITE)
    c.rect(182, 4, 190, 4, GREY)
    # Стикеры и листки на ткани.
    for x, y, col in ((10, 11, GOLD), (16, 13, GOLD), (22, 11, RED), (74, 12, GOLD), (100, 11, AQUA),
                      (106, 14, GOLD), (140, 12, GOLD), (170, 11, RED), (176, 14, GOLD), (220, 12, GOLD),
                      (240, 11, AQUA)):
        c.rect(x, y, x + 4, y + 4, col)
        c.rect(x + 1, y + 2, x + 3, y + 2, BRASS if col == GOLD else K)
    for x in (36, 124, 196):
        c.rect(x, 11, x + 8, 21, WHITE)
        for yy in (13, 15, 17, 19):
            c.rect(x + 1, yy, x + 6, yy, GREY)
        c.set(x + 4, 11, RED)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, сотрудник, вещи, пол, три
    слоя дали."""
    return {
        "enemy_walk": strip([suit_side(p) for p in base.phases()]),
        "enemy_front": strip([suit_front(p) for p in base.phases()]),
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
        "hero_run": strip([clerk_side(p) for p in base.phases()]),
        "hero_jump": clerk_side(0.0, jump=True),
        "hero_leap": strip([clerk_leap(i) for i in range(4)]),
        "hero_idle": strip([clerk_idle(i) for i in range(2)]),
        "hero_back": strip([clerk_back(p) for p in base.phases()]),
        "hero_slide": strip([clerk_slide(i) for i in range(2)]),
        "hero_hang": strip([clerk_hang(i) for i in range(2)]),
        "hero_crouch": strip([clerk_crouch(i) for i in range(2)]),
    }


def extras():
    """Ленты вне основы, которые ждут демки: летун, ползун, ключ, аптечка, снаряд врага."""
    return {
        "parrot_fly": strip([paper_plane(i) for i in range(4)]),
        "crab_walk": strip([vacuum(i) for i in range(4)]),
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


def save_sheet(path, items, scale=3, pad=6, back=(0x6C, 0x7A, 0x8E, 255), max_w=640):
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


def preview(path, scale=4, keys=None):
    """Лист набора после светотени: лента на строку, как в игре. `keys` оставляет только
    названные ленты (в этом порядке)."""
    items = dict(sprites())
    items.update(extras())
    if keys:
        items = {k: items[k] for k in keys}
    save_sheet(path, shaded(items), scale)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        scale_ = 4
        keys_ = None
        for arg in sys.argv:
            if arg.startswith("--scale="):
                scale_ = int(arg.split("=", 1)[1])
            if arg.startswith("--keys="):
                keys_ = [k for k in arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], scale_, keys_)
