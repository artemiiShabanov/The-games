#!/usr/bin/env python3
"""Набор «Динозавры» для 16/32-bit (основа, зеркало `space16.py` и `castles16.py`): доисторический
мир днём, вулканы и джунгли, тёплые охра и красная глина, сочная зелень, оранжевая лава. Герой
это пещерный человек: загорелая кожа, лохматые тёмные волосы с белой костью поперёк, оранжевая
шкура с тёмными пятнами через плечо до середины бедра с рваным подолом, босые ноги, голые руки.
Враг это прямоходящий раптор. Те же ленты, размеры и число кадров, что у космоса, пиратов и
замков (`castles16.sprites()`); позы героя повторяют их кадр в кадр, чтобы хитбоксы демок
сходились: меняется рисунок, не геометрия. Неба нет: над холмами и джунглями пусто.

Слоты космоса и их динозавры: космонавт это пещерный человек, пришелец это раптор, кристалл это
раковина аммонита, флаг экспедиции это шкура на шесте с отпечатком ладони, грузовая капсула это
гнездо с яйцами, метеорит это глыба застывшей лавы с оранжевыми трещинами, настил станции это
папоротниковая подстилка над красной глиной с костями. Ленты, которых нет в `sprites()`
(птеродактиль вместо попугая-дрона, трилобит вместо краба, костяной ключ, кокос вместо аптечки,
камень-снаряд), лежат в `extras()` тех же размеров, что у остальных сеттингов.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `dinosaurs_*16.py` берут
цвета по роли): K обводка, NAVY тёмный лес, SEA зелень джунглей и шкура раптора, AQUA молодой
папоротник, SKY дымка и пепел, WHITE кость, GREY тень кости, SKIN и TAN кожа и красная глина,
GOLD и BRASS охра и жёлтое брюхо, METAL камень и пепел, DARK волосы и застывшая лава, RED красная
глина и жар, VIOLET и PLUM оранжевая шкура и её тень.

    python3 tools/dinosaurs16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/dinosaurs16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Динозавры»: 16 цветов, индекс это та же роль, что у пиратов, космоса и замков.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x1A, 0x10, 0x0E),  # K      обводка
    (0x1E, 0x46, 0x2E),  # NAVY   тёмный лес, тень зелени
    (0x3C, 0x9A, 0x3C),  # SEA    джунгли, шкура раптора
    (0xA4, 0xD8, 0x48),  # AQUA   молодой папоротник, блик листвы
    (0xF4, 0xDE, 0xAE),  # SKY    дымка вдали, пепел, пар
    (0xF2, 0xEA, 0xD4),  # WHITE  кость, зубы, яйцо
    (0xC8, 0xB6, 0x94),  # GREY   тень кости
    (0xD4, 0x8E, 0x58),  # SKIN   загорелая кожа
    (0xA2, 0x56, 0x34),  # TAN    красная глина, тень кожи
    (0xF0, 0xB8, 0x38),  # GOLD   охра, жёлтое брюхо
    (0xB4, 0x7A, 0x24),  # BRASS  тень охры
    (0x76, 0x62, 0x58),  # METAL  камень, пепел
    (0x38, 0x26, 0x24),  # DARK   волосы, застывшая лава
    (0xCC, 0x44, 0x26),  # RED    красная глина, жар
    (0xF0, 0x7C, 0x22),  # VIOLET оранжевая шкура, лава
    (0x8C, 0x34, 0x1E),  # PLUM   тень шкуры
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: GREY, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: PLUM, VIOLET: PLUM, PLUM: DARK}
# Материалы для светотени рампами: зелень, кость, кожа, глина, охра, камень и лава, шкура.
GROUPS = {NAVY: "leaf", SEA: "leaf", AQUA: "leaf", SKY: "bone", WHITE: "bone", GREY: "bone",
          SKIN: "skin", TAN: "clay", GOLD: "ochre", BRASS: "ochre", METAL: "stone", DARK: "rock",
          RED: "heat", VIOLET: "pelt", PLUM: "pelt"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


def _mirror(c):
    """Зеркало кадра по горизонтали (до `finish`)."""
    for row in c.px:
        row.reverse()
    return c


# --- Пещерный человек --------------------------------------------------------------------------
# Силуэт как у космонавта и рыцаря (те же позы и габариты), но рисунок свой: огромная лохматая
# голова с белой костью в волосах (кость торчит назад и вперёд), голая загорелая кожа, оранжевая
# шкура с тёмными пятнами наискось через плечо и рваный подол ниже пояса, босые ноги с пальцами,
# за спиной каменная дубина.

def _head(c, x, y, face=1):
    """Голова лицом вправо при `face` 1: круглая, около десяти пикселей, лохматая шапка волос с
    четырьмя прядями назад, кость короткая поперёк макушки, открытое лицо с бровью, глазом и
    носом. Центр (x, y), нижний край y+5."""
    f = face
    c.ellipse(x + 1.2 * f, y + 1.5, 3.9, 3.8, SKIN)
    c.ellipse(x - 2.6 * f, y - 1.8, 3.4, 3.0, DARK)
    c.rect(x - 4 * f, y - 1, x - 2 * f, y + 3, DARK)
    # Пряди торчат назад и вверх.
    for x0, y0, x1, y1 in ((-4, -2, -8, -4), (-4, 0, -8, 1), (-4, 2, -7, 5), (-2, -4, -4, -6)):
        c.line(x + x0 * f, y + y0, x + x1 * f, y + y1, DARK, 1)
    # Неровная чёлка над лбом.
    for dx in range(-1, 3):
        c.set(x + dx * f, y - 2, DARK)
    c.set(x + 0 * f, y - 1, DARK)
    c.rect(x + 2 * f, y, x + 4 * f, y, TAN)
    c.set(x + 5 * f, y + 2, SKIN)
    c.set(x + 5 * f, y + 3, SKIN)
    c.rect(x + 1 * f, y + 4, x + 3 * f, y + 4, TAN)
    c.set(x + 3 * f, y + 3, TAN)
    # Кость поперёк макушки: шафт и по набалдашнику с краёв.
    a, b = sorted((x - 4 * f, x + 3 * f))
    c.rect(a, y - 5, b, y - 5, WHITE)
    c.rect(a, y - 4, b, y - 4, GREY)
    for ex in (x - 5 * f, x + 4 * f):
        c.ellipse(ex, y - 5.5, 1.1, 1.1, WHITE)
        c.ellipse(ex, y - 3.5, 1.1, 1.1, WHITE)
    c.set(x + 3 * f, y + 1, K)


def _club(c, x, y0, y1):
    """За спиной: каменная дубина, рукоять вдоль спины и тяжёлая головка внизу."""
    c.line(x + 3, y0 + 1, x - 2, y1 + 5, TAN, 2)
    c.ellipse(x - 2.5, y1 + 5.5, 2.2, 2.4, METAL)
    c.set(x - 3, y1 + 4, GREY)


def _body(c, x0, y0, x1, y1, skirt=2):
    """Корпус: голая грудь и плечо, оранжевая шкура с пятнами наискось от дальнего плеча до
    середины бедра, обводка-лямка по косому краю, рваный подол зубьями."""
    c.rect(x0, y0, x1, y1, SKIN)
    hem = y1 + skirt + 2
    c.poly([(x0 - 1, y0), (x0 + 4, y0), (x1 + 1, y0 + 6), (x1 + 1, hem - 1), (x0 - 1, hem - 1)], VIOLET)
    c.line(x0 + 4, y0, x1 + 1, y0 + 6, PLUM, 1)
    teeth = (0, 2, 1, 3, 1, 2, 0)
    for i, x in enumerate(range(x0 - 1, x1 + 2)):
        n = teeth[i % len(teeth)]
        for k in range(n):
            c.set(x, hem + k, VIOLET if k < n - 1 else PLUM)
    for dx, dy in ((1, 7), (5, 11)):
        px, py = x0 + dx, y0 + dy
        if c.get(px, py) == VIOLET:
            c.rect(px, py, px + 2, py + 1, DARK)
    c.set(x1 - 1, y0 + 2, TAN)
    c.set(x1, y0 + 3, TAN)


def _foot(c, x, y, w=4):
    """Босая нога: ступня, пальцы, светлая пятка."""
    c.rect(x - 1, y - 1, x + w - 1, y, SKIN)
    c.rect(x - 1, y + 1, x + w - 1, y + 1, TAN)
    c.set(x + w, y + 1, TAN)
    c.set(x + w - 1, y - 1, SKIN)
    c.set(x + w - 2, y, TAN)


def _arm(c, x0, y0, x1, y1, col):
    """Голая рука с кулаком. Ближняя (SKIN) узкая в два пикселя, дальняя (TAN) в три."""
    c.line(x0, y0, x1, y1, col, 2 if col == SKIN else 3)
    c.ellipse(x1, y1, 1.5, 1.5, col)


def caveman_side(phase, jump=False):
    """Пещерный человек сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), TAN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 4)
        _foot(c, foot[0], foot[1])
    _club(c, 8, 13 - bob, 19 - bob)
    _body(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), SKIN)
    _head(c, 16, 7 - bob)
    return c.finish()


def caveman_back(phase):
    """Со спины: бежит вглубь экрана, шкура наискось через спину, лохматый затылок, кость
    поперёк головы торчит с обеих сторон, лица нет."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, SKIN if sign > 0 else TAN)
        _foot(c, x - 1, 28 - lift)
        _arm(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, SKIN if sign > 0 else TAN)
    c.rect(11, 13 - bob, 20, 21 - bob, SKIN)
    hem = 25 - bob
    c.poly([(10, 13 - bob), (15, 13 - bob), (21, 19 - bob), (21, hem - 1), (10, hem - 1)], VIOLET)
    c.line(15, 13 - bob, 21, 19 - bob, PLUM, 1)
    for i, x in enumerate(range(10, 22)):
        n = (0, 2, 1, 3, 1, 2)[i % 6]
        for k in range(n):
            c.set(x, hem + k, VIOLET if k < n - 1 else PLUM)
    for dx, dy in ((1, 5), (6, 8), (3, 11)):
        px, py = 10 + dx, 13 - bob + dy
        if c.get(px, py) == VIOLET:
            c.rect(px, py, px + 2, py + 1, DARK)
    # Шея и уши, потом круглая лохматая шапка.
    c.rect(14, 11 - bob, 17, 13 - bob, TAN)
    c.set(10, 9 - bob, SKIN)
    c.set(21, 9 - bob, SKIN)
    c.ellipse(15.5, 8 - bob, 4.6, 4.4, DARK)
    for x0, y0, x1, y1 in ((10, 6, 7, 4), (10, 9, 7, 10), (21, 6, 24, 4), (21, 9, 24, 10), (14, 3, 13, 1), (18, 3, 19, 1)):
        c.line(x0, y0 - bob, x1, y1 - bob, DARK, 1)
    c.poly([(11, 11 - bob), (13, 14 - bob), (15, 12 - bob), (17, 14 - bob), (20, 11 - bob)], DARK)
    c.rect(9, 4 - bob, 22, 4 - bob, WHITE)
    c.rect(10, 5 - bob, 21, 5 - bob, GREY)
    for ex in (8.5, 22.5):
        c.ellipse(ex, 3 - bob, 1.1, 1.1, WHITE)
        c.ellipse(ex, 5.5 - bob, 1.1, 1.1, WHITE)
    return c.finish()


def caveman_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, TAN)
    for sign, col in ((-1, TAN), (1, SKIN)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 4)
        _foot(c, foot[0], foot[1])
    _club(c, 8, 13 + crouch, 19 + crouch)
    _body(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, SKIN)
    _head(c, 16, 7 + crouch)
    return c.finish()


def caveman_idle(i):
    """Стойка: два кадра, пещерный человек дышит."""
    c = Canvas()
    up = i
    for sign, col in ((-1, TAN), (1, SKIN)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, col)
        _foot(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, TAN)
    _club(c, 8, 13 - up, 19 - up)
    _body(c, 11, 13 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 21 - up, SKIN)
    _head(c, 16, 7 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; кожа по краям, шкура с
    пятнами посередине, рваный тёмный край у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = PLUM if k >= int(n) - 1 else SKIN
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)
        if k < int(n) - 1:
            c.line(x + dy * (w / 2 - 1), y - dx * (w / 2 - 1), x - dy * (w / 2 - 1), y + dx * (w / 2 - 1), VIOLET, 2)
            if k == 2:
                c.rect(x, y, x + 1, y, DARK)


def caveman_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх,
    рука сзади на земле. Макушка на 15-й строке, как у матроса. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, TAN, 3)
    c.line(24, 23 - i, 27, 27, TAN, 3)
    _foot(c, 27, 27)
    c.line(13, 24, 19, 23, TAN, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, SKIN, 4)
    c.rect(28, 26, 30, 29, SKIN)
    c.set(30, 29, TAN)
    c.set(29, 29, TAN)
    _arm(c, 11, 25, 6, 29, SKIN)
    _head(c, 10, 21)
    c.finish()
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
        _foot(c, foot[0], foot[1])
    _club(c, 8, 22, 26)
    _body(c, 11, 22, 18, 26, skirt=0)
    _arm(c, 14, 24, 19, 26, SKIN)
    _head(c, 16, 19)
    return c.finish()


def caveman_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, TAN, 3)
    c.line(18, 13, 17, 1, SKIN, 2)
    c.ellipse(15, 1, 1.4, 1.4, TAN)
    c.ellipse(17, 1, 1.4, 1.4, SKIN)
    _club(c, 8, 13, 19)
    _body(c, 11, 13, 20, 21, skirt=0)
    for sign, col in ((-1, TAN), (1, SKIN)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], col, 3)
        _foot(c, foot[0], foot[1], 3)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Раптор ------------------------------------------------------------------------------------
# Прямоходящий хищник: зелёный, жёлтое брюхо, тёмные полосы на спине, длинная морда с зубами,
# короткие лапки с когтями, толстый хвост назад. Шаг и рост повторяют пришельца и стражника.

def raptor_side(phase):
    """Раптор сбоку, лицом влево (навстречу герою): шаг по фазе, хвост покачивается. Рисуется
    лицом вправо и зеркалится, детали (глаз, зубы, когти) ставятся после обводки."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    wag = int(round(math.sin(phase + 1.0) * 1.5))
    # Хвост: основание потоньше и длинный кончик.
    c.line(10, 17 - bob, 5, 18 - bob + wag, SEA, 4)
    c.line(5, 18 - bob + wag, 1, 20 + wag, SEA, 2)
    for sign, col in ((-1, NAVY), (1, SEA)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (14 + 5 * a, 28 - lift)
        hip = (14, 20 - bob)
        knee = ((hip[0] + foot[0]) / 2 + 3, (hip[1] + foot[1]) / 2 - 1)
        c.line(hip[0], hip[1], knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 2)
        c.rect(foot[0] - 1, foot[1], foot[0] + 3, foot[1] + 1, col)
    # Стройное туловище, длинная шея, маленькая узкая голова.
    c.ellipse(13, 17 - bob, 7, 3.8, SEA)
    c.ellipse(14, 19 - bob, 5, 1.8, GOLD)
    for x in (8, 11, 14):
        c.line(x, 13.5 - bob, x + 1, 15.5 - bob, NAVY, 1)
    c.ellipse(18, 15 - bob, 3, 3.2, SEA)
    c.line(19, 13 - bob, 25, 6 - bob, SEA, 3)
    c.ellipse(26, 4.5 - bob, 2.6, 2, SEA)
    c.poly([(26, 3.5 - bob), (31, 4.5 - bob), (31, 6.5 - bob), (26, 7 - bob)], SEA)
    c.poly([(26, 7.5 - bob), (30, 7.5 - bob), (29, 9 - bob), (26, 9 - bob)], GOLD)
    for x, y in ((22, 9), (21, 11), (20, 13)):
        c.set(x, y - bob, GOLD)
    # Короткая лапка с тремя пальцами вперёд.
    c.line(18, 17 - bob, 22, 19 - bob, SEA, 2)
    c.finish()
    _mirror(c)
    for x, y, col in ((26, 4 - bob, GOLD), (27, 4 - bob, K), (30, 4.5 - bob, K),
                      (27, 7 - bob, WHITE), (28, 7 - bob, K), (29, 7 - bob, WHITE), (30, 7 - bob, K),
                      (23, 18 - bob, WHITE), (24, 18 - bob, WHITE), (23, 19 - bob, WHITE),
                      (23, 20 - bob, WHITE)):
        c.set(31 - x, y, col)
    for sign in (-1, 1):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        fx, fy = 14 + 5 * a, 28 - lift
        c.set(31 - (fx + 4), fy + 1, WHITE)
        # Большой серповидный коготь: крюк вверх и вперёд над ступнёй.
        for dx, dy in ((2, -1), (3, -2), (4, -3), (5, -3)):
            c.set(31 - (fx + dx), fy + dy, WHITE)
    return c


def raptor_front(phase):
    """Раптор лицом к камере: идёт на игрока, ноги по очереди, пасть с зубами, жёлтое брюхо
    полосками, лапки по бокам."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(21, 25, 28, 27 + (1 if s > 0 else 0), NAVY, 3)
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 4
        col = SEA if sign > 0 else NAVY
        c.ellipse(x, 23 - bob, 3, 4, col)
        c.line(x, 25 - bob, x, 28 - lift, col, 2)
        c.rect(x - 2, 28 - lift, x + 2, 29 - lift, col)
    c.ellipse(16, 19 - bob, 5.5, 6.5, SEA)
    c.ellipse(16, 20 - bob, 3, 5.5, GOLD)
    for y in (17, 20, 23):
        c.rect(14, y - bob, 18, y - bob, BRASS)
    c.line(11, 17 - bob, 9, 21 - bob, SEA, 2)
    c.line(21, 17 - bob, 23, 21 - bob, SEA, 2)
    c.ellipse(16, 13 - bob, 2.8, 3, SEA)
    c.ellipse(16, 8 - bob, 3.8, 3.6, SEA)
    c.ellipse(16, 11 - bob, 2.4, 2.4, SEA)
    c.ellipse(16, 12.5 - bob, 2.2, 1.2, GOLD)
    c.line(16, 5 - bob, 16, 9 - bob, AQUA, 1)
    c.rect(13, 5 - bob, 14, 5 - bob, NAVY)
    c.rect(17, 5 - bob, 18, 5 - bob, NAVY)
    c.finish()
    for x, y, col in ((13, 7, GOLD), (14, 7, K), (17, 7, K), (18, 7, GOLD),
                      (15, 10, K), (17, 10, K),
                      (14, 12, K), (15, 12, WHITE), (16, 12, K), (17, 12, WHITE), (18, 12, K),
                      (8, 22, WHITE), (9, 22, WHITE), (10, 22, WHITE),
                      (22, 22, WHITE), (23, 22, WHITE), (24, 22, WHITE)):
        c.set(x, y - bob, col)
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 4
        for dx in (-2, 0, 2):
            c.set(x + dx, 30 - lift, WHITE)
        c.set(x + sign * 3, 28 - lift, WHITE)
        c.set(x + sign * 3, 27 - lift, WHITE)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Раковина аммонита вращается: шесть кадров, ширина по косинусу; спираль рёбер от центра,
    у ребра оболочка темнее."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 7.0)
    cx = 15.5
    cy = 16
    ry = 10.5
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            u = (x - cx) / rx
            v = (y - cy) / ry
            r = math.hypot(u, v)
            if r > 1.0:
                continue
            if rx <= 2:
                c.set(x, y, BRASS)
                continue
            th = math.atan2(v, u)
            band = (r * 3.2 - th / (2 * math.pi)) % 1.0
            col = GOLD if band < 0.55 else BRASS
            if r > 0.86:
                col = BRASS
            if r < 0.14:
                col = RED
            c.set(x, y, col)
    if rx > 3:
        k = rx / 7.0
        c.set(cx - 3 * k, 10, WHITE)
        c.set(cx - 2 * k, 9, WHITE)
        c.set(cx - 4 * k, 12, SKY)
        c.set(cx + 3 * k, 21, BRASS)
    return c.finish()


def flag(i):
    """Шкура на костяном шесте: оранжевое полотнище с тёмными пятнами и рваным нижним краем идёт
    волной, посередине светлый отпечаток ладони."""
    c = Canvas()
    c.rect(5, 3, 6, 31, WHITE)
    c.rect(6, 3, 6, 31, GREY)
    c.ellipse(5.5, 2, 2, 2, WHITE)
    c.set(5, 1, GREY)
    c.rect(4, 29, 7, 30, GREY)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        tooth = (0, 3, 1, 4, 1, 3, 0)[(x - 8) % 7]
        bottom.append((x, 17 + tooth + w))
    c.poly(top + bottom[::-1], VIOLET)
    for dx, dy in ((2, 3), (7, 2), (13, 4), (17, 3), (4, 11), (10, 12), (16, 10), (18, 13)):
        x = 8 + dx
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        c.rect(x, 5 + dy + w, x + 1, 5 + dy + w, DARK)
        c.set(x, 6 + dy + w, DARK)
    # Лапы шкуры: две перевязи у шеста.
    c.rect(7, 6, 7, 7, PLUM)
    c.rect(7, 15, 7, 16, PLUM)
    c.shade()
    c.outline()
    mid = math.sin(17 * 0.45 - i * math.pi / 3.0) * 0.9
    # Отпечаток ладони: ладонь, четыре пальца вверх, большой палец сбоку.
    px, py = 17, 14 + mid
    c.ellipse(px, py, 3, 2.6, SKY)
    for dx, h in ((-2, 3), (-0.5, 4), (1, 4), (2.5, 3)):
        c.line(px + dx, py - 2, px + dx, py - 2 - h, SKY, 1)
    c.line(px - 3, py, px - 5, py - 3, SKY, 1)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    c.set(8, 11, SKY)
    return c.finish()


def _bones(c):
    """Кости в глине: бедренная, рёбра дугой."""
    c.rect(7, 19, 15, 19, WHITE)
    c.rect(7, 20, 15, 20, GREY)
    for ex in (5, 17):
        c.ellipse(ex, 18.5, 1.8, 1.8, WHITE)
        c.ellipse(ex, 21, 1.8, 1.8, GREY)
    pts = ((22, 11), (26, 12), (29, 16), (29, 22), (26, 26))
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], WHITE, 1)
        c.line(a[0] + 1, a[1], b[0] + 1, b[1], GREY, 1)
    c.ellipse(22, 11, 1.2, 1.2, WHITE)


def ground(inner=False):
    """Папоротниковая подстилка сверху, ниже красная глина с прослойками и костями. Плитка
    стыкуется по краям: узоры периодичны по 32."""
    c = Canvas()
    c.rect(0, 0, 31, 31, TAN)
    for y in range(6, 32):
        for x in range(32):
            v = (x * 7 + y * 13 + (x * y) % 5) % 17
            if v == 0:
                c.set(x, y, RED)
            elif v == 9:
                c.set(x, y, BRASS)
    for x in range(32):
        c.set(x, 13 + int(round(1.5 * math.sin(x * math.tau / 32.0))), RED)
        c.set(x, 28 + int(round(1.0 * math.sin(x * math.tau / 32.0 + 1.0))), PLUM)
    _bones(c)
    if not inner:
        for y in range(0, 5):
            for x in range(32):
                c.set(x, y, AQUA if (x + y * 2) % 4 in (0, 1) else SEA)
        for x in range(32):
            c.set(x, 4, NAVY if x % 3 else SEA)
            n = (x * 5 + 3) % 7
            if n < 4:
                c.set(x, 5, SEA if n < 2 else NAVY)
            if n < 1:
                c.set(x, 6, NAVY)
    return c


def rock():
    """Глыба застывшей лавы: тёмная корка с гранями и светящимися оранжевыми трещинами."""
    c = Canvas()
    c.poly([(4, 28), (2, 18), (8, 9), (17, 5), (26, 10), (30, 20), (27, 28)], DARK)
    c.poly([(8, 14), (14, 9), (20, 10), (15, 15)], METAL)
    c.poly([(5, 14), (9, 9), (17, 6), (24, 9), (20, 11), (15, 10), (10, 13)], METAL)
    c.line(9, 10, 16, 7, GREY, 1)
    cracks = (((16, 10), (14, 15), (17, 19), (15, 26)), ((22, 14), (20, 20), (23, 25)),
              ((7, 19), (11, 22), (10, 27)))
    for pts in cracks:
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], VIOLET, 1)
            c.line(a[0] + 1, a[1], b[0] + 1, b[1], RED, 1)
    for x, y in ((14, 15), (17, 19), (20, 20), (11, 22)):
        c.set(x, y, GOLD)
    c.ellipse(24, 20, 2, 1.5, METAL)
    return c.finish()


def _egg(c, x, y, body, spot):
    """Яйцо: вытянутое по вертикали, светлое пятнышко и пятна цвета `spot`."""
    c.ellipse(x, y, 4.2, 5.6, body)
    c.ellipse(x, y - 2.6, 3.2, 3.2, body)
    c.set(x - 2, y - 3, WHITE)
    c.set(x - 2, y - 2, WHITE)
    c.set(x + 1, y + 1, spot)
    c.set(x - 1, y + 3, spot)
    c.set(x + 2, y - 2, spot)


def chest():
    """Гнездо с яйцами: плетёная чаша из веток, три яйца разных цветов торчат над краем."""
    c = Canvas()
    _egg(c, 9.5, 13, SKY, TAN)
    _egg(c, 22.5, 13, AQUA, SEA)
    _egg(c, 16, 10, WHITE, RED)
    c.ellipse(15.5, 23, 13.5, 6, TAN)
    c.rect(2, 22, 29, 23, TAN)
    for k in range(0, 30, 4):
        c.line(2 + k, 19, 6 + k, 28, BRASS, 1)
        c.line(6 + k, 19, 2 + k, 28, DARK, 1)
    c.line(2, 22, 29, 22, GOLD, 1)
    c.line(3, 25, 28, 25, BRASS, 1)
    for x in range(3, 29, 5):
        c.set(x, 20, GOLD)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали без неба: нет заливки сверху. Высоты периодические (256 делится на период
# синусов), ленты стыкуются по краям. Низ слоя сплошной.

def _wrap_ellipse(c, cx, cy, rx, ry, col):
    for k in (0, 256, -256):
        c.ellipse(cx + k, cy, rx, ry, col)


def _smoke(c, x, y, n, drift, col, hi):
    """Столб дыма над кратером: n клубов вверх, шире и бледнее, наклон по ветру."""
    for k in range(n):
        r = 2.2 + k * 0.9
        cx = x + drift * k * 1.6
        cy = y - k * 3.2
        c.ellipse(cx, cy, r, r * 0.8, col)
        c.ellipse(cx - r * 0.3, cy - r * 0.3, r * 0.5, r * 0.4, hi)


def _volcano(c, x, base, w, h, body, shade, glow, streak):
    """Вулкан: усечённый конус, правая половина в тени, жерло с жаром и ручьи лавы по склону."""
    top = base - h
    c.poly([(x - w, base), (x - 4, top), (x + 4, top), (x + w, base)], body)
    c.poly([(x + 1, top), (x + 4, top), (x + w, base), (x + 3, base)], shade)
    c.ellipse(x, top, 4.5, 1.6, glow)
    for dx, ln in ((-2, 0.45), (1, 0.7), (3, 0.35)):
        c.line(x + dx, top + 1, x + dx * 3, top + h * ln, streak, 1)


def par_sky():
    """Дальний слой: дымчатые холмы и два вулкана с дымящими жерлами, лента 256×48, стыкуется по
    краям, неба нет (над холмами пусто, дым уходит вверх)."""
    c = Canvas(256, 48)

    def height(x):
        return 14 + 5 * math.sin(x * math.pi * 2 / 256.0 * 2 + 0.6) + 3 * math.sin(x * math.pi * 2 / 256.0 * 5 + 2.0)

    _volcano(c, 62, 40, 28, 24, GREY, METAL, VIOLET, RED)
    _smoke(c, 64, 15, 4, 0.5, SKY, WHITE)
    _volcano(c, 196, 38, 20, 16, GREY, METAL, VIOLET, RED)
    _smoke(c, 198, 22, 3, 0.4, SKY, WHITE)
    for x in range(256):
        top = 47 - int(height(x))
        c.rect(x, top, x, 47, SKY)
        c.rect(x, top + 1, x, 47, GOLD)
        c.rect(x, top + 6, x, 47, AQUA)
        c.rect(x, top + 14, x, 47, SEA)
    for cx, cy, r in ((24, 36, 11), (110, 38, 14), (150, 34, 9), (236, 36, 12)):
        _wrap_ellipse(c, cx, cy, r, r * 0.35, SKY)
    return c


def _canopy(c, x, y, r, col, hi):
    """Крона джунглей: кочка листвы с бликом."""
    c.ellipse(x, y, r, r * 0.75, col)
    c.ellipse(x - r * 0.3, y - r * 0.3, r * 0.5, r * 0.3, hi)


def _neck(c, x, base, dirn, h, col, hi):
    """Шея зауропода над джунглями: лебединой дугой вверх и вперёд, голова с глазом, спина и
    хвост едва видны из-за крон."""
    c.ellipse(x - dirn * 8, base + 1, 11, 5, col)
    c.line(x - dirn * 14, base, x - dirn * 24, base + 2, col, 3)
    pts = []
    for k in range(h + 1):
        t = k / float(h)
        pts.append((x + dirn * (2 * t + 9 * t ** 4), base - k))
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        c.line(a[0], a[1], b[0], b[1], col, 5 if k < h * 0.4 else 3)
    hx, hy = pts[-1]
    c.ellipse(hx + dirn * 1.5, hy, 3, 2, col)
    c.rect(min(hx + dirn * 3, hx + dirn * 5), hy, max(hx + dirn * 3, hx + dirn * 5), hy + 1, col)
    c.set(hx + dirn * 2, hy - 1, K)
    c.line(x - dirn * 12, base - 3, x, base - 3, hi, 1)


def par_far():
    """Средний слой: джунгли на холмах, вулкан с алой кромкой жерла и дымом, шеи двух зауроподов
    над кронами, лента 256×48, низ сплошной."""
    c = Canvas(256, 48)

    def height(x):
        h = 10 + 8 * max(0.0, math.sin(x * math.pi / 64.0)) ** 2 + 3 * math.sin(x * math.pi / 16.0 + 1.0)
        return h + 10 * max(0.0, math.sin((x - 40) * math.pi / 128.0)) ** 4

    for x in range(256):
        top = 47 - int(max(height(x), 3))
        c.rect(x, top, x, 47, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        c.rect(x, top + 10, x, 47, NAVY)
    gx = 168
    by = 47 - int(height(gx)) + 3
    _volcano(c, gx, by + 6, 30, 32, METAL, DARK, VIOLET, RED)
    _smoke(c, gx + 1, by - 29, 2, 0.5, GREY, SKY)
    for nx, d, h in ((44, 1, 24), (214, -1, 18)):
        nb = 47 - int(height(nx)) + 4
        _neck(c, nx, nb, d, h, METAL, GREY)
    for px, r in ((8, 6), (22, 5), (36, 7), (158, 6), (170, 7), (180, 6), (52, 6), (66, 5), (86, 7), (102, 6), (120, 5), (136, 7),
                  (150, 6), (190, 7), (204, 5), (236, 6), (250, 5)):
        by = 47 - int(height(px)) + 3
        _canopy(c, px, by, r, SEA if px % 3 else NAVY, AQUA)
    return c


def _fern(c, x, base, n, ln, col, hi):
    """Папоротник: пучок дугой изогнутых вайй, кончики светлее."""
    for k in range(n):
        d = (k - (n - 1) / 2.0) / ((n - 1) / 2.0)
        px, py = x, base
        for t in range(1, ln + 1):
            nx = x + d * t * 0.9
            ny = base - t * (1.0 - 0.5 * abs(d)) + (t * t) * 0.05 * abs(d)
            c.line(px, py, nx, ny, col, 1)
            px, py = nx, ny
        c.set(px, py, hi)
        c.set(px - d, py + 1, hi)


def _horsetail(c, x, base, h, col, hi):
    """Хвощ: тонкий членистый ствол с мутовками иголок."""
    c.rect(x, base - h, x, base, col)
    for k in range(base - 2, base - h, -3):
        c.rect(x - 2, k, x + 2, k, hi)
        c.set(x - 2, k - 1, col)
        c.set(x + 2, k - 1, col)
    c.set(x, base - h - 1, hi)


def _cycad(c, x, base, h, trunk, col, hi):
    """Саговник: короткий чешуйчатый ствол и венец жёстких вайй."""
    c.rect(x - 1, base - h, x + 1, base, trunk)
    for k in range(base - 1, base - h, -2):
        c.set(x - 1, k, DARK)
    top = base - h
    for dx, dy in ((-6, 2), (-4, -1), (-2, -3), (0, -4), (2, -3), (4, -1), (6, 2)):
        c.line(x, top, x + dx, top + dy, col, 1)
        c.set(x + dx, top + dy, hi)


def par_mid():
    """Ближний слой: бугры подлеска с папоротниками, хвощами и саговниками, лента 256×32."""
    c = Canvas(256, 32)

    def crest(x):
        return int(round(11 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0)))

    for x in range(256):
        top = crest(x)
        c.rect(x, top, x, 31, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        c.rect(x, top + 8, x, 31, NAVY)
        if (x * 7 + top * 3) % 23 == 0:
            c.rect(x, top + 5 + (x % 6), x + 1, top + 5 + (x % 6), AQUA)
    for px, kind in ((14, 0), (30, 1), (52, 2), (76, 0), (96, 1), (118, 2), (140, 0), (160, 1), (180, 2),
                     (204, 0), (224, 1), (242, 2)):
        by = crest(px) + 2
        if kind == 0:
            _fern(c, px, by, 5, 9, NAVY, AQUA)
        elif kind == 1:
            _horsetail(c, px, by, 11, NAVY, SEA)
        else:
            _cycad(c, px, by, 5, TAN, NAVY, AQUA)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, раптор, вещи, земля, три слоя
    дали. Ключи, размеры и число кадров те же, что у `castles16.sprites()`. Ленты демок лежат в
    модулях `dinosaurs_*16.py`."""
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


# --- Остальные слоты (ленты демок «тропа» и «до выхода» их берут) ------------------------------

def pterosaur(i):
    """Птеродактиль (слот попугая) летит вправо: четыре кадра взмаха (вверх, середина, вниз,
    середина), тело по центру кадра. Кожистые крылья с костью по передней кромке, длинный клюв,
    гребень назад. Без красной обводки опасности: её кладёт модуль демки."""
    c = Canvas()
    wing = (-9, -3, 6, -3)[i]
    for dx, k, col in ((-3, 0.8, BRASS), (0, 1.0, GOLD)):
        w = wing * k
        tip = (5 + dx, 17 + w * 1.7)
        c.poly([(19 + dx, 17), tip, (8 + dx, 17 + w * 0.8 + 5), (12 + dx, 17 + w * 0.4 + 4),
                (14 + dx, 17 + w * 0.2 + 4), (15 + dx, 19.5)], col)
        c.line(19 + dx, 17, tip[0], tip[1], DARK, 1)
        c.line(15 + dx, 18, (tip[0] + 8 + dx) / 2, (tip[1] + 17 + w * 0.8 + 5) / 2, DARK, 1)
    c.ellipse(15.5, 18, 4.5, 2.8, TAN)
    c.line(11, 19, 5, 21, TAN, 2)
    c.ellipse(21, 16, 2.6, 2.2, TAN)
    c.poly([(21, 14.5), (31, 16.5), (21, 18.5)], METAL)
    c.poly([(19, 14), (13, 11), (18, 16)], RED)
    c.finish()
    c.set(22, 15, K)
    c.set(25, 17, WHITE)
    c.set(28, 17, WHITE)
    return c


def trilobite(i):
    """Трилобит (слот краба-ползуна) идёт вправо: четыре кадра, лапки под панцирем по очереди,
    ребристый купол и щит-голова с двумя глазами."""
    c = Canvas()
    for k, dx in enumerate((-9, -6, -3, 0, 3, 6)):
        lift = 1 if (k + i) % 2 == 0 else 0
        c.line(16 + dx, 25, 15 + dx + (1 if lift else -1), 29 - lift, TAN, 1)
    c.ellipse(14, 21.5, 12, 7.5, TAN)
    c.rect(2, 24, 26, 26, TAN)
    for x in range(4, 22, 3):
        c.line(x, 15, x - 1, 26, DARK, 1)
        c.line(x + 1, 16, x, 21, GOLD, 1)
    c.line(14, 14, 14, 26, BRASS, 1)
    c.ellipse(4, 23.5, 3, 3, BRASS)
    c.ellipse(24.5, 21.5, 5.5, 6.2, BRASS)
    c.line(21, 17, 28, 17, GOLD, 1)
    c.ellipse(23.5, 16, 1.8, 1.8, GOLD)
    c.ellipse(27, 17, 1.6, 1.6, GOLD)
    c.line(29, 19, 31, 15, TAN, 1)
    c.finish()
    c.set(24, 16, K)
    c.set(27, 17, K)
    return c


def key():
    """Костяной ключ: кольцо-головка с красной верёвкой, длинный стержень, зубцы и набалдашник."""
    c = Canvas(32, 32)
    c.ellipse(10, 16, 7, 7, WHITE)
    c.ellipse(10, 16, 3, 3, None)
    c.rect(16, 14, 28, 17, WHITE)
    c.rect(16, 17, 28, 17, GREY)
    for ex in (29, 29):
        c.ellipse(ex, 13.5, 1.6, 1.6, WHITE)
        c.ellipse(ex, 18.5, 1.6, 1.6, GREY)
    c.rect(22, 18, 23, 22, WHITE)
    c.rect(26, 18, 27, 21, WHITE)
    c.set(10, 10, RED)
    c.set(11, 10, RED)
    c.set(10, 11, TAN)
    return c.finish()


def coconut():
    """Кокос (аптечка): мохнатый бурый шар с тремя глазками, срезанная крышка с молоком и красный
    крест на белой заплатке."""
    c = Canvas(32, 32)
    c.ellipse(15.5, 19, 9.5, 9, TAN)
    for x, y in ((8, 16), (11, 23), (21, 24), (23, 17), (14, 27), (18, 13), (9, 21)):
        c.line(x, y, x + 1, y + 2, DARK, 1)
    c.ellipse(15.5, 11.5, 5.2, 2.2, WHITE)
    c.ellipse(15.5, 11.5, 3.4, 1.2, SKY)
    c.set(9, 10, AQUA)
    c.set(10, 9, AQUA)
    c.set(21, 9, GOLD)
    c.rect(13, 16, 18, 25, WHITE)
    c.rect(11, 19, 20, 22, WHITE)
    c.rect(15, 17, 16, 24, RED)
    c.rect(12, 20, 19, 21, RED)
    return c.finish()


def stone_shot():
    """Камень-снаряд летит вправо: бугристый булыжник с бликом и пыльным следом. 16×16."""
    c = Canvas(16, 16)
    c.line(1, 5, 5, 6, TAN, 1)
    c.line(0, 8, 5, 8, SKY, 1)
    c.line(1, 11, 5, 10, TAN, 1)
    c.poly([(6, 4), (11, 3), (15, 6), (15, 10), (11, 13), (7, 12), (5, 8)], METAL)
    c.poly([(7, 5), (11, 4), (13, 6), (9, 8)], GREY)
    c.set(11, 10, DARK)
    c.set(12, 10, DARK)
    return c.finish()


def extras():
    """Слоты динозавров вне `sprites()`: ленты и вещи тех же размеров, что у космоса и пиратов."""
    return {
        "parrot_fly": strip([pterosaur(i) for i in range(4)]),
        "crab_walk": strip([trilobite(i) for i in range(4)]),
        "key": key(),
        "medkit": coconut(),
        "shot": stone_shot(),
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
