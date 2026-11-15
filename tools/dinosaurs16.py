#!/usr/bin/env python3
"""Набор «Динозавры» для 16/32-bit, основа (#144, состав в `docs/specs/settings.md`):
доисторический день, вулканы и джунгли. Пещерный человек в оранжевой пятнистой шкуре через одно
плечо, с костью в лохматых волосах, против зелёных рапторов. Те же ленты и кадры, что у пиратов
и космоса (`pixel_sprites16.py`, `space16.py`): позы и опора ног повторяют космонавта, чтобы
хитбоксы демок сходились, рисунок свой. Сравнительная версия основы: в игру не подключена.

    python3 tools/dinosaurs16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Динозавры»: 16 цветов, индекс это та же роль, что у пиратов и космоса (ими рисуют HUD
# и мир демки). Небо демок идёт сверху вниз NAVY, SEA, AQUA, SKY: бирюза к тёплой дымке у
# горизонта; SEA же заливает низ под горизонтом, поэтому это цвет дальних джунглей.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x18, 0x10, 0x10),  # K      обводка
    (0x1C, 0x46, 0x5A),  # NAVY   верх неба, тень бирюзы, шеи зауроподов вдали
    (0x2C, 0x80, 0x84),  # SEA    дальние джунгли, панцирь трилобита
    (0x7C, 0xCC, 0xB4),  # AQUA   небо, блик панциря
    (0xF4, 0xE8, 0xB6),  # SKY    дымка у горизонта, свечение
    (0xF4, 0xEE, 0xDA),  # WHITE  кость, скорлупа, когти
    (0xBC, 0xB0, 0x9A),  # GREY   тень кости, пепел
    (0xDC, 0x98, 0x62),  # SKIN   загорелая кожа
    (0xB0, 0x54, 0x34),  # TAN    тень кожи, красная глина
    (0xF4, 0xCC, 0x52),  # GOLD   брюхо раптора, аммонит, жар лавы
    (0xBC, 0x82, 0x2C),  # BRASS  тень золота, прутья гнезда
    (0x7C, 0x68, 0x6E),  # METAL  лавовый камень
    (0x52, 0x30, 0x28),  # DARK   волосы, пятна шкуры, тёмная глина
    (0xEC, 0x5E, 0x24),  # RED    оранжевая шкура, лава, опасность
    (0x60, 0xB4, 0x40),  # VIOLET рапторы, листва
    (0x26, 0x6C, 0x3A),  # PLUM   тень зелёного
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, VIOLET: PLUM}
# Шкура без тени по таблице: её красит рампа. Материалы для светотени рампами: кость, кожа,
# шкура (с ней тёмные пятна и волосы, чтобы пятна не давали рельефа), чешуя, панцирь, камень.
GROUPS = {WHITE: "bone", GREY: "bone", SEA: "shell", NAVY: "shell", AQUA: "shell", SKY: "shell",
          SKIN: "skin", TAN: "skin", GOLD: "gold", BRASS: "gold", METAL: "stone", DARK: "hide", RED: "hide",
          VIOLET: "scale", PLUM: "scale"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Пещерный человек --------------------------------------------------------------------------
# Силуэт: лохматая копна волос шире головы с прядями на затылке, сзади торчит конец кости,
# тяжёлая челюсть и нос, шкура с рваным подолом ниже бёдер, голые руки и ноги, крупные босые
# ступни. Узнаётся по зубцам подола, вихрам и кости, даже залитый одним цветом.

# Глубина зубцов подола по столбцам.
_HEM = (2, 1, 3, 1, 2, 0, 2, 1, 2, 1)


def _head(c, x, y, face=1):
    """Голова лицом вправо при `face` 1, центр (x, y): копна волос, чёлка до бровей, челюсть."""
    x = int(round(x))
    y = int(round(y))
    f = face
    # Копна сдвинута к затылку, пряди свисают на шею.
    c.ellipse(x - 1.5 * f, y - 0.5, 5.2, 4.4, DARK)
    c.line(x - 5 * f, y + 1, x - 7 * f, y + 4, DARK, 2)
    c.line(x - 3 * f, y + 2, x - 4 * f, y + 5, DARK, 2)
    # Лицо и квадратная челюсть.
    c.ellipse(x + 0.5 * f, y + 0.5, 4.2, 4.2, SKIN)
    c.rect(min(x + f, x + 4 * f), y + 2, max(x + f, x + 4 * f), y + 4, SKIN)
    # Всё выше бровей закрыто чёлкой.
    for yy in range(y - 5, y - 1):
        for xx in range(x - 8, x + 9):
            if c.get(xx, yy) == SKIN:
                c.set(xx, yy, DARK)
    # Вихры на макушке, бровь козырьком, нос.
    for dx in (-4, -1, 2):
        c.set(x + dx * f, y - 5, DARK)
    c.set(x + 5 * f, y - 1, DARK)
    c.set(x + 5 * f, y + 1, SKIN)
    # Кость в волосах: наискось, нижний конец торчит за затылок.
    for dx, dy in ((-8, -1), (-7, -2), (-6, -2), (-5, -3), (-4, -3), (-3, -4)):
        c.set(x + dx * f, y + dy, WHITE)
    for dx, dy in ((-9, -2), (-8, 0), (-2, -4), (-3, -3)):
        c.set(x + dx * f, y + dy, WHITE)


def _face(c, x, y, face=1):
    """Глаз и рот поверх готового силуэта."""
    x = int(round(x))
    y = int(round(y))
    c.set(x + 3 * face, y, K)
    c.set(x + 4 * face, y + 3, TAN)


def _hem(c, x0, x1, y, shift=0):
    """Рваный подол: зубцы разной длины вниз от строки y."""
    for i, x in enumerate(range(int(x0), int(x1) + 1)):
        d = _HEM[(i + shift) % len(_HEM)]
        if d:
            c.rect(x, y, x, y + d - 1, RED)


def _hide(c, x0, y0, x1, y1):
    """Корпус сбоку: шкура через переднее плечо наискось, лопатка голая, пятна, рваный подол."""
    c.rect(x0, y0, x1, y1, SKIN)
    c.poly([(x1, y0), (x1 - 3, y0), (x0, y0 + 5), (x0, y1 + 1), (x1, y1 + 1)], RED)
    c.rect(x1 - 3, y0, x1, y0, RED)
    _hem(c, x0, x1, y1 + 1)
    for dx, dy in ((1, 6), (2, 6), (1, 7), (6, 3), (7, 3), (7, 4), (5, 8), (6, 8)):
        if y0 + dy <= y1:
            c.set(x0 + dx, y0 + dy, DARK)


def _foot(c, x, y, col, w=4):
    """Босая ступня: пятка под голенью, пальцы вперёд. Те же строки, что у ботинка космонавта."""
    c.rect(x - 1, y, x + w - 2, y + 1, col)
    c.set(x + w - 1, y + 1, col)


def _arm(c, x0, y0, x1, y1, col):
    """Голая рука с кулаком. Ближняя рука поверх шкуры отбита тёмной тенью снизу."""
    if col == SKIN:
        c.line(x0, y0 + 1, x1 - 1, y1 + 1, DARK, 3)
    c.line(x0, y0, x1, y1, col, 3)
    c.ellipse(x1, y1, 1.4, 1.4, col)


def caveman_side(phase, jump=False):
    """Пещерный человек сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    # Дальняя рука и дальняя нога темнее, рисуются первыми.
    _arm(c, 15, 14 - bob, 15 + 5 * swing, 19 - bob - (3 if jump else 0), TAN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
        _foot(c, foot[0], foot[1], col)
    _hide(c, 11, 12 - bob, 19, hip_y)
    _arm(c, 16, 14 - bob, 16 - 5 * swing, 19 - bob - (4 if jump else 0), SKIN)
    _head(c, 16, 7 - bob)
    c.finish()
    _face(c, 16, 7 - bob)
    return c


def caveman_back(phase):
    """Со спины: бежит вглубь экрана. Копна до плеч, кость поперёк затылка, лямка шкуры наискось."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        col = SKIN if sign > 0 else TAN
        c.rect(x - 2, 21 - bob, x + 1, 29 - lift, col)
        # Поднятая нога показывает тёмную подошву.
        if lift > 1.5:
            c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
        _arm(c, 16 + sign * 6, 14 - bob, 16 + sign * 7, 19 - bob + s * sign * 2, SKIN)
    c.rect(11, 12 - bob, 20, 21 - bob, SKIN)
    c.poly([(11, 12 - bob), (14, 12 - bob), (20, 17 - bob), (20, 22 - bob), (11, 22 - bob)], RED)
    _hem(c, 11, 20, 22 - bob, 3)
    for dx, dy in ((1, 4), (2, 4), (4, 7), (7, 8), (8, 8), (2, 9)):
        c.set(11 + dx, 12 - bob + dy, DARK)
    # Голова: уши, копна, пряди на плечи.
    c.ellipse(15.5, 7 - bob, 5, 5, SKIN)
    c.ellipse(15.5, 6.5 - bob, 5.6, 4.8, DARK)
    for x, n in ((10, 2), (12, 4), (14, 2), (16, 3), (18, 2), (20, 4), (21, 1)):
        c.rect(x, 9 - bob, x, 10 - bob + n, DARK)
    for x in (12, 15, 18):
        c.set(x, max(1, 1 - bob), DARK)
    c.finish()
    # Кость поверх готовой копны: белая на тёмном, концы шире.
    c.line(11, 5 - bob, 20, 3 - bob, WHITE, 1)
    for x, y in ((10, 4), (10, 6), (11, 6), (21, 2), (21, 4), (20, 2)):
        c.set(x, y - bob, WHITE)
    return c


def caveman_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 14 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 19 + crouch, TAN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
        _foot(c, foot[0], foot[1], col)
    _hide(c, 11, 12 + crouch, 19, hip_y)
    _arm(c, 16, 14 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 19 + crouch, SKIN)
    _head(c, 16, 7 + crouch)
    c.finish()
    _face(c, 16, 7 + crouch)
    return c


def caveman_idle(i):
    """Стойка: два кадра, дышит, плечи и голова ходят на пиксель."""
    c = Canvas()
    up = i
    for sign, col in ((-1, TAN), (1, SKIN)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, col)
        _foot(c, x, 29, col)
    _arm(c, 14, 14 - up, 13, 20 - up, TAN)
    _hide(c, 11, 12 - up, 19, 21)
    _arm(c, 17, 14 - up, 18, 20 - up, SKIN)
    _head(c, 16, 7 - up)
    c.finish()
    _face(c, 16, 7 - up)
    return c


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; у плеч кожа, ниже шкура."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = SKIN if k < 2 else RED
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def caveman_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута пяткой вперёд, дальняя коленом
    вверх, рука сзади на земле. Макушка на 15-й строке, как у матроса. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, TAN, 3)
    c.line(24, 23 - i, 27, 27, TAN, 3)
    _foot(c, 27, 27, TAN)
    c.line(13, 24, 19, 23, TAN, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, SKIN, 4)
    # Подол лёг на бедро зубцами.
    c.rect(18, 26, 21, 29, RED)
    for x, y in ((22, 26), (22, 27), (23, 26), (22, 29), (24, 29), (15, 26), (17, 28)):
        c.set(x, y, DARK if x < 18 else RED)
    # Ступня подошвой вперёд, пальцы вверх.
    c.rect(28, 26, 29, 29, SKIN)
    c.set(30, 26, SKIN)
    c.set(30, 27, SKIN)
    _arm(c, 11, 25, 6, 29, SKIN)
    _head(c, 10, 21)
    c.finish()
    _face(c, 10, 21)
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def caveman_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, TAN, 2)
    for sign, col in ((-1, TAN), (1, SKIN)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
        _foot(c, foot[0], foot[1], col)
    c.rect(11, 22, 18, 26, SKIN)
    c.poly([(11, 22), (13, 22), (18, 25), (18, 28), (11, 28)], RED)
    _hem(c, 11, 16, 28, 4)
    c.set(13, 25, DARK)
    c.set(12, 27, DARK)
    c.set(16, 27, DARK)
    _arm(c, 14, 24, 19, 26, SKIN)
    _head(c, 16, 19)
    c.finish()
    _face(c, 16, 19)
    return c


def caveman_hang(i):
    """На лиане: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, TAN, 3)
    c.line(18, 13, 17, 1, SKIN, 3)
    c.ellipse(15, 1, 1.2, 1.2, TAN)
    c.ellipse(17, 1, 1.2, 1.2, SKIN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], col, 3)
        _foot(c, foot[0], foot[1], col, 3)
    _hide(c, 11, 13, 20, 21)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    _face(hd, 16, 8)
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Раптор ------------------------------------------------------------------------------------
# Прямоходящий, ростом с героя: узкая длинная морда, шея дугой, жёлтое брюхо, короткие лапы с
# когтями, ноги коленом вперёд и пяткой назад, белый серп когтя над ступнёй, хвост за спиной.
# Шаг и рост повторяют скелета пиратов.

def raptor_side(phase):
    """Раптор сбоку, мордой влево (навстречу герою): шаг по фазе, хвост качается."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Хвост: от крестца назад и вверх, сужается, кончик ходит.
    tail = [(19, 20 - bob), (23, 21 - bob), (27, 19 - bob + s * 0.8), (30, 16 - bob + s * 1.6)]
    for k in range(3):
        c.line(tail[k][0], tail[k][1], tail[k + 1][0], tail[k + 1][1], VIOLET, (5, 3, 2)[k])
    c.line(21, 22 - bob, 26, 21 - bob + s * 0.6, GOLD, 1)
    # Дальняя лапа.
    c.line(14, 15 - bob, 10, 17 - bob - s, PLUM, 2)
    for sign, col in ((-1, PLUM), (1, VIOLET)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        fx, fy = 15 - 5 * a, 29 - lift
        knee = (16 - 2 * a, 24.5 - bob)
        ankle = (fx + 3, fy - 2)
        # Мощное бедро, голень назад к пятке, ступня вперёд.
        c.ellipse(17.5 - a, 22 - bob, 3, 3.4, col)
        c.line(knee[0], knee[1], ankle[0], ankle[1], col, 3)
        c.rect(fx - 2, fy, fx + 2, fy + 1, col)
        c.set(fx - 3, fy + 1, WHITE)
        if sign > 0:
            # Серповидный коготь поднят над пальцами.
            c.set(fx - 2, fy - 1, WHITE)
            c.set(fx - 3, fy - 2, WHITE)
            c.set(fx - 4, fy - 2, WHITE)
    # Корпус наклонён вперёд: грудь и круп, брюхо жёлтое.
    c.ellipse(15, 15 - bob, 4, 4.2, VIOLET)
    c.ellipse(18, 19 - bob, 4.4, 4, VIOLET)
    c.ellipse(13.5, 16 - bob, 1.8, 3.4, GOLD)
    c.line(14, 19 - bob, 16, 22 - bob, GOLD, 2)
    # Шея дугой и голова с узкой мордой.
    c.line(14.5, 12 - bob, 13, 8 - bob, VIOLET, 5)
    c.line(11.5, 12 - bob, 11, 9 - bob, GOLD, 2)
    c.ellipse(13, 5 - bob, 3.2, 2.8, VIOLET)
    c.poly([(2, 5 - bob), (11, 3 - bob), (12, 8 - bob), (3, 8 - bob)], VIOLET)
    c.rect(4, 7 - bob, 10, 7 - bob, GOLD)
    # Полосы по спине.
    for x, y in ((17, 12), (18, 12), (19, 15), (20, 15), (20, 18), (21, 18), (24, 19), (14, 3), (15, 4)):
        c.set(x, y - bob, PLUM)
    # Ближняя лапа с когтями поверх брюха.
    c.line(15, 15 - bob, 10, 18 - bob + s, VIOLET, 2)
    c.set(9, 19 - bob + s, WHITE)
    c.set(9, 17 - bob + s, WHITE)
    c.finish()
    # Пасть щелью с зубами, глаз, ноздря.
    c.rect(3, 6 - bob, 9, 6 - bob, K)
    c.set(5, 6 - bob, WHITE)
    c.set(7, 6 - bob, WHITE)
    c.set(12, 4 - bob, GOLD)
    c.set(11, 4 - bob, K)
    return c


def raptor_front(phase):
    """Раптор мордой к камере: идёт на игрока, голова клином, хвост качается за спиной."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Хвост за спиной уходит вбок и вверх.
    c.line(17, 20 - bob, 24 + s, 19 - bob, VIOLET, 4)
    c.line(24 + s, 19 - bob, 27 + s * 2, 14 - bob, VIOLET, 3)
    c.line(27 + s * 2, 14 - bob, 27 + s * 3, 10 - bob, VIOLET, 2)
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 4
        c.ellipse(x, 23 - bob, 2.6, 3, VIOLET)
        c.line(x, 24 - bob, x, 28 - lift, VIOLET, 2)
        c.rect(x - 2, 28 - lift, x + 2, 29 - lift, VIOLET)
        for dx in (-2, 0, 2):
            c.set(x + dx, 30 - lift, WHITE)
        # Серп когтя с внутренней стороны.
        c.set(x - sign * 3, 28 - lift, WHITE)
        c.set(x - sign * 3, 27 - lift, WHITE)
        # Лапы в стороны, когти вниз.
        hx, hy = 16 + sign * 8, 18 - bob - s * sign * 2
        c.line(16 + sign * 4, 14 - bob, hx, hy, VIOLET, 2)
        c.set(hx - 1, hy + 1, WHITE)
        c.set(hx + 1, hy + 1, WHITE)
    c.ellipse(16, 17 - bob, 5.2, 6, VIOLET)
    c.ellipse(16, 18 - bob, 2.8, 4.6, GOLD)
    for y in (16, 18, 20):
        c.rect(14, y - bob, 18, y - bob, BRASS)
    c.rect(14, 9 - bob, 18, 12 - bob, VIOLET)
    c.rect(15, 10 - bob, 17, 12 - bob, GOLD)
    # Голова: широкий череп сверху, морда клином вниз.
    c.ellipse(16, 4.5 - bob, 5.4, 3, VIOLET)
    c.poly([(11, 5 - bob), (21, 5 - bob), (18, 12 - bob), (14, 12 - bob)], VIOLET)
    c.rect(15, 2 - bob, 17, 4 - bob, PLUM)
    c.finish()
    for sign in (-1, 1):
        c.set(16 + sign * 4, 5 - bob, GOLD)
        c.set(16 + sign * 3, 5 - bob, K)
        c.set(16 + sign * 4, 4 - bob, K)
        c.set(16 + sign * 5, 3 - bob, K)
        c.set(16 + sign, 9 - bob, K)
    c.rect(14, 11 - bob, 18, 11 - bob, K)
    c.set(15, 11 - bob, WHITE)
    c.set(17, 11 - bob, WHITE)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Аммонит вращается: шесть кадров, ширина по косинусу. Спираль завитка, рёбра по краю."""
    c = Canvas()
    k = abs(math.cos(math.pi * i / 6.0))
    rx = max(1.2, k * 9.0)
    cx, cy = 15.5, 16.0
    c.ellipse(cx, cy, rx, 9, GOLD)
    if rx > 3:
        # Устье: раструб раковины выступает из круга.
        c.ellipse(cx + rx * 0.82, cy + 4.5, rx * 0.3, 3.2, GOLD)
        c.finish()
        # Рёбра от края внутрь по наружному завитку.
        for n in range(11):
            a = 0.9 + n * 0.5
            for r in (7.4, 6.2):
                c.set(cx + math.cos(a) * r * k, cy + math.sin(a) * r, BRASS)
        # Спираль: от устья к центру.
        t = 0.0
        while t < 4.3 * math.pi:
            r = 8.6 * math.exp(-0.15 * t) - 3.4 + 3.4 * math.exp(-0.02 * t)
            c.set(cx + math.cos(t + 0.5) * r * k, cy + math.sin(t + 0.5) * r, DARK if t < 0.25 else BRASS)
            t += 0.06
        c.line(cx - rx * 0.55, cy - 5, cx - rx * 0.2, cy - 6.5, WHITE, 1)
        c.set(cx + rx * 0.82, cy + 5, DARK)
    else:
        c.finish()
        c.rect(cx, cy - 6, cx, cy + 6, BRASS)
    return c


def flag(i):
    """Шкура на шесте: растянута за углы, край рваный, посередине оранжевый отпечаток ладони.
    Шест из жерди с костью на верхушке, полотнище идёт волной."""
    c = Canvas()
    c.rect(5, 4, 6, 31, BRASS)
    for y in (9, 16, 23, 29):
        c.set(5, y, DARK)
    c.ellipse(5.5, 2.5, 2.4, 1.6, WHITE)
    c.set(3, 1, WHITE)
    c.set(8, 1, WHITE)
    top = []
    bottom = []
    for x in range(8, 30):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        # Углы оттянуты, между ними край провисает; справа зубцы.
        sag = 2.2 * math.sin((x - 8) * math.pi / 21.0)
        rag = ((x * 5) % 3) * 0.6 if x > 10 else 0
        top.append((x, 4 + w + sag))
        bottom.append((x, 21 + w - sag - rag))
    c.poly(top + bottom[::-1], WHITE)
    # Ремешки к шесту.
    c.rect(7, 6, 8, 6, DARK)
    c.rect(7, 18, 8, 18, DARK)
    c.shade()
    c.outline()
    mid = int(round(math.sin(18 * 0.45 - i * math.pi / 3.0) * 0.8))
    # Отпечаток: ладонь, четыре пальца, большой в сторону.
    c.rect(15, 12 + mid, 20, 15 + mid, RED)
    c.rect(16, 16 + mid, 19, 16 + mid, RED)
    for x, n in ((14, 3), (16, 4), (18, 4), (20, 3)):
        c.rect(x, 11 + mid - n, x, 11 + mid, RED)
    c.set(22, 13 + mid, RED)
    c.set(23, 12 + mid, RED)
    c.set(21, 14 + mid, RED)
    c.set(12, 9 + mid, GREY)
    c.set(25, 17 + mid, GREY)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    c.set(11, 9, GOLD)
    return c.finish()


def _bone(c, x0, y0, x1, y1, col=WHITE):
    """Косточка: стержень и по два бугорка на концах."""
    c.line(x0, y0, x1, y1, col, 1)
    n = math.hypot(x1 - x0, y1 - y0)
    px, py = -(y1 - y0) / n, (x1 - x0) / n
    for ex, ey in ((x0, y0), (x1, y1)):
        c.set(ex + px, ey + py, col)
        c.set(ex - px, ey - py, col)


def ground(inner=False):
    """Красная глина пластами, в ней кости; у кромки лесная подстилка свисает неровным краем.
    Внутренняя плитка без подстилки, с отпечатком аммонита."""
    c = Canvas()
    c.rect(0, 0, 31, 31, TAN)
    for x in range(32):
        # Пласты: тёмные прожилки и светлая полоса, стыкуются по краям плитки.
        c.set(x, 13 + round(1.4 * math.sin(2 * math.pi * x / 32.0)), DARK)
        c.set(x, 24 + round(1.2 * math.sin(2 * math.pi * x / 16.0 + 1.0)), DARK)
        if (x * 7) % 5 < 2:
            c.set(x, 18 + round(1.2 * math.sin(2 * math.pi * x / 32.0 + 2.0)), RED)
        if (x * 3) % 7 == 0:
            c.set(x, 29 + (x % 2), DARK)
    c.rect(0, 31, 31, 31, DARK)
    # Галька.
    for x, y in ((3, 21), (27, 15), (14, 28), (20, 10)):
        c.rect(x, y, x + 1, y, METAL)
        c.set(x, y - 1, GREY)
    # Кости: косточка, рёбра дугами, зуб.
    _bone(c, 5, 17, 12, 15)
    for k in range(3):
        x = 19 + k * 3
        c.set(x, 22, GREY)
        c.set(x, 21, WHITE)
        c.set(x + 1, 20, WHITE)
        c.set(x + 2, 20, WHITE)
        c.set(x + 3, 21, GREY)
    c.set(9, 26, WHITE)
    c.set(10, 27, WHITE)
    c.set(10, 26, GREY)
    if inner:
        _bone(c, 22, 5, 28, 7, GREY)
        # Отпечаток аммонита.
        t = 0.0
        while t < 3.6 * math.pi:
            r = 4.6 * math.exp(-0.16 * t)
            c.set(9 + math.cos(t) * r, 6 + math.sin(t) * r, GREY if t < 2.2 * math.pi else DARK)
            t += 0.1
        return c
    # Подстилка: тёмная прель, сверху свежая зелень, сухие листья и травинки.
    for x in range(32):
        d = 5 + round(1.6 * math.sin(2 * math.pi * x / 8.0) + 1.2 * math.sin(2 * math.pi * x * 3 / 32.0 + 1.0))
        c.rect(x, 0, x, d, PLUM)
        c.rect(x, 0, x, 1 + (1 if (x * 5) % 4 == 0 else 0), VIOLET)
        c.set(x, d + 1, DARK)
    for x, y in ((4, 3), (5, 3), (12, 4), (19, 3), (20, 4), (27, 3)):
        c.set(x, y, VIOLET)
    for x, y in ((8, 2), (9, 2), (16, 1), (23, 2), (24, 3), (30, 1)):
        c.set(x, y, GOLD)
    for x, y in ((2, 0), (14, 0), (26, 0)):
        c.set(x, y, AQUA)
    return c


def rock():
    """Глыба лавы: угловатый тёмный камень, по граням светящиеся трещины."""
    c = Canvas()
    c.poly([(3, 29), (1, 20), (5, 11), (12, 5), (21, 4), (27, 9), (30, 19), (28, 29)], METAL)
    c.poly([(19, 13), (27, 10), (30, 19), (28, 29), (17, 29), (21, 21)], DARK)
    c.poly([(6, 12), (12, 6), (20, 6), (14, 12)], GREY)
    c.finish()
    # Трещины: оранжевый жар, жёлтая сердцевина в узлах.
    cracks = (((12, 12), (15, 18)), ((15, 18), (10, 24)), ((15, 18), (21, 21)), ((21, 21), (24, 27)),
              ((21, 21), (26, 17)), ((10, 24), (6, 26)), ((8, 16), (12, 12)))
    for a, b in cracks:
        c.line(a[0], a[1], b[0], b[1], RED, 1)
    for x, y in ((15, 18), (14, 17), (21, 21), (10, 24), (13, 14), (22, 23)):
        c.set(x, y, GOLD)
    return c


def chest():
    """Гнездо с яйцами: плетёная из прутьев чаша, в ней три крапчатых яйца."""
    c = Canvas()
    # Торчащие прутья по краям.
    for x0, y0, x1, y1 in ((4, 22, 1, 17), (6, 21, 4, 15), (27, 22, 30, 17), (25, 21, 28, 15), (9, 27, 3, 26)):
        c.line(x0, y0, x1, y1, BRASS, 1)
    c.ellipse(15.5, 23, 13, 6, BRASS)
    c.ellipse(15.5, 20, 11, 3.5, DARK)
    # Яйца: дальние по бокам, ближнее посередине выше.
    for ex, ey, rx, ry in ((9, 15, 3.6, 4.8), (22, 15.5, 3.6, 4.8), (15.5, 13, 4.2, 5.6)):
        egg = Canvas()
        egg.ellipse(ex, ey, rx, ry, WHITE)
        c.paste(egg.finish(), 0, 0)
    # Передний борт чаши закрывает низ яиц.
    for y in range(20, 30):
        for x in range(2, 30):
            if ((x - 15.5) / 13.0) ** 2 + ((y - 23) / 6.0) ** 2 <= 1.0 and ((x - 15.5) / 11.0) ** 2 + ((y - 19) / 3.6) ** 2 > 1.0:
                c.set(x, y, BRASS)
    c.finish()
    # Плетение: светлые и тёмные прутья крест-накрест.
    for k in range(-2, 9):
        x = 2 + k * 4
        for n in range(8):
            px, py = x + n, 28 - n
            if c.get(px, py) == BRASS:
                c.set(px, py, GOLD if k % 2 == 0 else DARK)
    for x in range(4, 28, 3):
        if c.get(x, 22) == BRASS:
            c.set(x, 22, DARK)
    # Крапины на скорлупе.
    for x, y in ((8, 13), (10, 16), (7, 16), (21, 13), (23, 16), (24, 14), (14, 10), (17, 12), (15, 15), (13, 13), (18, 16)):
        if c.get(x, y) == WHITE:
            c.set(x, y, SEA)
    return c


# --- Летун, ползун и предметы шутера -----------------------------------------------------------

def _danger(c):
    """Враг, которого нельзя убить: тень как у всех, обводка оранжевая вместо чёрной."""
    c.shade()
    c.outline(RED)
    return c


def pterodactyl(i):
    """Птеродактиль летит вправо: длинный клюв, гребень назад, перепончатые крылья углом, ноги
    вытянуты. Четыре кадра взмаха (вверх, середина, вниз, середина), тело по центру кадра."""
    c = Canvas()
    wing = (-10, -6, 8, -6)[i]
    # Дальнее крыло темнее и чуть впереди.
    c.poly([(22, 15), (18, 15 + wing * 0.6), (8, 15 + wing * 0.9), (14, 17)], DARK)
    # Ноги вытянуты назад.
    c.line(11, 18, 6, 20, METAL, 1)
    c.line(11, 17, 5, 18, METAL, 1)
    # Тело, шея, голова.
    c.ellipse(15, 17, 5.5, 2.6, METAL)
    c.line(19, 16, 22, 13, METAL, 3)
    c.ellipse(23, 12, 2.4, 2.2, METAL)
    # Гребень назад и клюв вперёд.
    c.poly([(23, 10), (15, 6), (16, 8), (21, 13)], GOLD)
    c.poly([(24, 10), (29.4, 13), (24, 15)], GOLD)
    c.line(25, 13, 28, 13, BRASS, 1)
    # Ближнее крыло: перепонка от плеча до кончика пальца, задний край с выемкой.
    tip = (3, 15 + wing)
    wrist = (14, 15 + wing * 0.7)
    c.poly([(20, 16), wrist, tip, (9, 17 + wing * 0.4), (11, 19)], SKIN)
    c.line(20, 16, wrist[0], wrist[1], METAL, 2)
    c.line(wrist[0], wrist[1], tip[0], tip[1], METAL, 1)
    c.line(wrist[0], wrist[1], 9, 17 + wing * 0.4, METAL, 1)
    _danger(c)
    c.set(23, 12, K)
    return c


def trilobite(i):
    """Трилобит ползёт вправо: полукруглый головной щит с глазом и шипом назад, панцирь из
    сегментов с тремя долями, хвостовые шипы. Четыре кадра: ножки волной, усики ходят."""
    c = Canvas()
    # Ножки под панцирем, волна бежит от хвоста к голове.
    for k in range(7):
        lift = 1 if (k + i) % 4 < 2 else 0
        x = 5 + k * 3
        c.line(x, 26, x + (1 if lift else -1), 29 - lift, NAVY, 2)
    # Хвостовые шипы.
    c.line(5, 22, 2, 21, SEA, 2)
    c.line(5, 25, 2, 26, SEA, 2)
    # Панцирь: туловище и крупный головной щит.
    c.ellipse(13, 23, 10, 5, SEA)
    c.ellipse(22, 22.5, 6.5, 6, SEA)
    # Щёчный шип щита тянется назад вдоль края.
    c.line(21, 28, 14, 29, SEA, 2)
    # Усики.
    c.line(27, 19, 29, 16 + (i % 2), SEA, 2)
    _danger(c)
    # Осевая доля: светлый валик вдоль спины.
    for x in range(4, 19):
        for y in (21, 22):
            if c.get(x, y) in (SEA, NAVY):
                c.set(x, y, AQUA)
    # Сегменты: тёмные борозды поперёк.
    for x in range(5, 18, 3):
        for y in range(18, 29):
            if c.get(x, y) in (SEA, AQUA):
                c.set(x, y, NAVY)
    # Шов головного щита и его валик.
    for y in range(17, 29):
        if c.get(18, y) in (SEA, AQUA):
            c.set(18, y, NAVY)
    # Блик по верхней кромке щита.
    for x in range(20, 27):
        for y in range(15, 22):
            if c.get(x, y) == SEA:
                c.set(x, y, AQUA)
                break
    # Глаз на стебельке-бугорке.
    c.ellipse(22, 18.5, 1.6, 1.4, GOLD)
    c.set(23, 18, K)
    return c


def key():
    """Ключ из кости: кольцо с бугорками, стержень, два зубца, оранжевая обмотка."""
    c = Canvas(32, 32)
    c.ellipse(10, 16, 7, 7, WHITE)
    c.ellipse(10, 16, 3, 3, None)
    c.ellipse(4, 11, 2, 2, WHITE)
    c.ellipse(4, 21, 2, 2, WHITE)
    c.rect(16, 14, 28, 17, WHITE)
    c.ellipse(28.5, 14, 2, 2, WHITE)
    c.rect(22, 18, 23, 22, WHITE)
    c.rect(26, 18, 27, 21, WHITE)
    c.rect(17, 14, 19, 17, RED)
    c.finish()
    c.set(18, 15, DARK)
    c.set(17, 16, DARK)
    c.set(19, 16, DARK)
    return c


def medkit():
    """Лечение: жареный окорок на кости, корочка тёмная, срез светлый."""
    c = Canvas(32, 32)
    # Кость торчит вверх вправо, на конце два бугорка.
    c.line(18, 13, 25, 6, WHITE, 3)
    c.ellipse(25, 4, 2.2, 2.2, WHITE)
    c.ellipse(28, 7, 2.2, 2.2, WHITE)
    # Мясо: капля, широкая снизу.
    c.ellipse(13, 19, 10, 8.5, TAN)
    c.poly([(9, 12), (20, 10), (22, 16), (12, 16)], TAN)
    c.ellipse(11.5, 18, 8, 6.5, RED)
    c.finish()
    # Блик и срез у кости.
    c.line(7, 15, 11, 12, GOLD, 1)
    c.set(6, 17, GOLD)
    c.ellipse(19, 13, 2, 1.4, SKIN)
    for x, y in ((17, 24), (19, 22), (14, 26), (20, 19)):
        c.set(x, y, DARK)
    return c


def shot():
    """Снаряд врага 16×16: сгусток лавы, жёлтая сердцевина, тёмная корка каплями."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, RED)
    c.ellipse(8, 8, 4, 4, GOLD)
    c.ellipse(7, 7, 2, 2, WHITE)
    for x, y in ((12, 11), (11, 12), (4, 12), (12, 4)):
        c.set(x, y, TAN)
    return c


# --- Параллакс ---------------------------------------------------------------------------------

def par_sky():
    """Дальний слой: кучевые облака, полоса пепла и пара птеродактилей вдали, лента 256×48,
    стыкуется по краям."""
    c = Canvas(256, 48)
    for k in (0, 256, -256):
        # Полоса вулканического пепла.
        for cx, cy, r in ((96, 9, 20), (120, 7, 14), (140, 10, 10)):
            c.ellipse(cx + k, cy, r, 2.2, GREY)
        # Облака: белый верх, тёплый низ.
        for cx, cy, r in ((28, 24, 12), (44, 27, 9), (170, 30, 15), (190, 33, 9), (236, 18, 10), (250, 21, 7)):
            c.ellipse(cx + k, cy + 2, r * 1.3, r * 0.3, SKY)
            c.ellipse(cx + k, cy, r, r * 0.34, WHITE)
            c.ellipse(cx + k - r * 0.3, cy - r * 0.22, r * 0.5, r * 0.3, WHITE)
            c.ellipse(cx + k + r * 0.35, cy - r * 0.12, r * 0.36, r * 0.22, WHITE)
    # Птеродактили: галочки с клювом.
    for x, y in ((74, 30), (86, 36), (212, 40)):
        for dx, dy in ((-3, -1), (-2, 0), (-1, 1), (0, 0), (1, 0), (2, -1), (3, -2), (1, 1), (2, 1)):
            c.set(x + dx, y + dy, NAVY)
    return c


def _far_height(x):
    """Кромка дальних джунглей над низом ленты: кроны буграми, период 256."""
    return 9 + 3 * abs(math.sin(x * math.pi / 16.0)) + 2 * math.sin(x * math.pi / 32.0 + 1.0) + 2 * abs(math.sin(x * math.pi / 8.0 + 0.5))


def par_far():
    """Средний слой: вулкан с лавой и дымом, второй поменьше, шеи зауроподов над дальними
    джунглями. Лента 256×48, низ сплошной, стыкуется по краям."""
    c = Canvas(256, 48)

    def cone(cx, top, half_top, half_base, lava):
        for y in range(top, 48):
            k = (y - top) / float(47 - top)
            half = half_top + (half_base - half_top) * k ** 1.7
            for x in range(int(cx - half), int(cx + half) + 1):
                side = (x - cx) / max(half, 1.0)
                col = DARK if side > 0.25 + 0.2 * math.sin(y * 0.9) else METAL
                if side < -0.72 and (x + y) % 3 != 0:
                    col = GREY
                c.set(x % 256, y, col)
        if not lava:
            return
        # Жерло светится, лава течёт по склону двумя языками.
        c.rect(cx - half_top + 1, top, cx + half_top - 1, top, GOLD)
        c.rect(cx - half_top, top + 1, cx + half_top, top + 1, RED)
        for start, drift, n in ((-2, -0.55, 24), (2, 0.4, 16), (0, 0.08, 9)):
            x = float(cx + start)
            for j in range(n):
                y = top + 1 + j
                x += drift + 0.8 * math.sin(j * 0.7 + start)
                c.set(x, y, GOLD if j < n // 3 else RED)
                c.set(x + 1, y, RED)

    cone(64, 9, 5, 54, True)
    cone(204, 25, 4, 30, False)
    c.rect(202, 25, 206, 25, RED)
    # Дым над жерлом: клубы уходят вверх и вбок.
    for cx, cy, r in ((66, 6, 4), (71, 3, 4), (78, 2, 3), (62, 4, 2.5), (205, 22, 2.5), (209, 19, 2)):
        c.ellipse(cx, cy, r, r * 0.75, GREY)
        c.ellipse(cx - 1, cy - 1, r * 0.55, r * 0.4, WHITE)

    def sauropod(x0, height, lean, face):
        """Спина горбом и длинная шея с маленькой головой."""
        base_y = 47 - int(_far_height(x0)) + 3
        c.ellipse(x0 - face * 9, base_y + 1, 11, 6, NAVY)
        n = height * 2
        for j in range(n + 1):
            t = j / float(n)
            x = x0 + face * lean * t * t
            y = base_y - height * t
            r = 2.2 - 1.1 * t
            c.ellipse(x, y, r, r, NAVY)
        hx, hy = x0 + face * lean, base_y - height
        c.ellipse(hx + face * 2, hy, 3, 1.6, NAVY)
        c.set(hx + face * 2, hy - 1, SEA)

    sauropod(136, 24, 5, 1)
    sauropod(160, 17, 4, 1)
    sauropod(246, 20, 5, -1)
    # Дальние джунгли: кроны буграми, блики на макушках, внизу тень.
    for x in range(256):
        top = 47 - int(_far_height(x))
        c.rect(x, top, x, 47, SEA)
        if abs(math.sin(x * math.pi / 8.0 + 0.5)) > 0.8:
            c.set(x, top, AQUA)
            c.set(x, top + 1, AQUA)
        for y in range(top + 5, 48):
            if (x + y) % 2 == 0 or y > 44:
                c.set(x, y, NAVY)
    # Древовидные папоротники торчат из крон.
    for x0 in (20, 112, 180, 226):
        top = 47 - int(_far_height(x0)) - 5
        c.rect(x0, top, x0, top + 6, NAVY)
        for d in (-4, -2, 2, 4):
            c.line(x0, top, x0 + d, top + (1 if abs(d) < 3 else 2) - 2, SEA, 1)
            c.set(x0 + d + (1 if d > 0 else -1), top + 1, SEA)
    return c


def par_mid():
    """Ближний слой: стена джунглей, пальмы-саговники и хвощи над кронами; книзу растворяется в
    цвете дали. Лента 256×32, стыкуется по краям."""
    c = Canvas(256, 32)

    def crest(x):
        return 12 - 3.5 * abs(math.sin(x * math.pi / 16.0 + 0.4)) - 2.0 * abs(math.sin(x * math.pi / 8.0)) + 1.5 * math.sin(x * math.pi / 64.0)

    # Саговники: ствол и веер листьев.
    for x0, h in ((22, 10), (97, 12), (150, 9), (215, 11)):
        y0 = int(crest(x0)) - h + 6
        c.rect(x0, y0, x0 + 1, 14, DARK)
        for d in (-7, -5, -2, 2, 5, 7):
            c.line(x0, y0, x0 + d, y0 - 3 + abs(d) * 0.75, PLUM, 2)
            c.line(x0, y0 - 1, x0 + d * 0.8, y0 - 4 + abs(d) * 0.7, VIOLET, 1)
    # Хвощи: тонкие членистые стебли.
    for x0 in (60, 66, 128, 184, 190, 246):
        y0 = int(crest(x0)) - 5 - (x0 % 3)
        c.rect(x0, y0, x0, 12, PLUM)
        for y in range(y0 + 1, 10, 2):
            c.set(x0 - 1, y, VIOLET)
            c.set(x0 + 1, y, VIOLET)
    for x in range(256):
        top = int(round(crest(x)))
        c.rect(x, top, x, 31, PLUM)
        c.rect(x, top, x, top + 1, VIOLET)
        # Листья пятнами в толще.
        for y in range(top + 3, 24):
            if (x * 5 + y * 9) % 17 == 0:
                c.rect(x, y, x + 1, y, VIOLET)
            if (x * 3 + y * 7) % 29 == 0:
                c.set(x, y, NAVY)
        # Низ уходит в дымку цвета дали.
        for y in range(22, 32):
            if y >= 28 or (y >= 25 and (x + y) % 2 == 0) or (x + y * 2) % 4 == 0:
                c.set(x, y, SEA)
    # Папоротник свисает перьями поверх стены.
    for x0 in (40, 110, 168, 232):
        y0 = int(crest(x0)) + 5
        for d in (-6, -3, 3, 6):
            c.line(x0, y0, x0 + d, y0 + 5 - abs(d) * 0.3, VIOLET, 1)
        c.set(x0, y0 - 1, GOLD)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, раптор, вещи, земля, три
    слоя дали. Ключи и размеры те же, что у `space16.sprites()`."""
    return {
        "enemy_walk": strip([raptor_side(p) for p in base.phases()]),
        "enemy_front": strip([raptor_front(p) for p in base.phases()]),
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
        "hero_run": strip([caveman_side(p) for p in base.phases()]),
        "hero_jump": caveman_side(0.0, jump=True),
        "hero_leap": strip([caveman_leap(i) for i in range(4)]),
        "hero_idle": strip([caveman_idle(i) for i in range(2)]),
        "hero_back": strip([caveman_back(p) for p in base.phases()]),
        "hero_slide": strip([caveman_slide(i) for i in range(2)]),
        "hero_hang": strip([caveman_hang(i) for i in range(2)]),
        "hero_crouch": strip([caveman_crouch(i) for i in range(2)]),
    }


def extras():
    """Летун, ползун и предметы, которые у пиратов лежат в модулях демок: птеродактиль и
    трилобит тропы, костяной ключ, окорок-аптечка и сгусток лавы шутера."""
    return {
        "parrot_fly": strip([pterodactyl(i) for i in range(4)]),
        "crab_walk": strip([trilobite(i) for i in range(4)]),
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


def save_sheet(path, items, scale=3, pad=6, back=(0x4E, 0x9A, 0x9C, 255), max_w=640):
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
    """Лист набора: лента на строку, как в игре, после светотени. `keys`: только эти ленты."""
    items = dict(sprites())
    items.update(extras())
    if keys:
        items = {k: items[k] for k in keys}
    save_sheet(path, shaded(items), scale)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        scale_ = 4
        keys_ = None
        for arg in sys.argv[1:]:
            if arg.startswith("--scale="):
                scale_ = int(arg.split("=", 1)[1])
            elif arg.startswith("--keys="):
                keys_ = [k for k in arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], scale_, keys_)
