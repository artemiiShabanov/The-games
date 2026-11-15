#!/usr/bin/env python3
"""Набор «Космос» для 16/32-bit (#136, состав в `docs/specs/settings.md`): ретро-фантастика,
космонавт в белом скафандре с бирюзовым визором, фиолетовые пришельцы. Те же ленты и кадры, что
у пиратов (`pixel_sprites16.py` и модули демок), позы повторяют матроса, чтобы хитбоксы демок
сходились. Пишется вместе с пиратами: `python3 tools/pixel_sprites16.py`.

    python3 tools/space16.py --preview out.png   # лист набора в 4 раза крупнее
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Космос»: 16 цветов, индекс это та же роль, что у пиратов (ими рисуют HUD и мир демки).
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x12, 0x10, 0x18),  # K      обводка
    (0x17, 0x16, 0x3C),  # NAVY   глубокий космос, тень синего
    (0x45, 0x4A, 0xB8),  # SEA    сине-фиолетовый: даль, тень энергии
    (0x4F, 0xC3, 0xD9),  # AQUA   визор, энергия
    (0xC2, 0xEE, 0xF4),  # SKY    блик визора, свечение
    (0xEE, 0xF1, 0xF6),  # WHITE  скафандр
    (0xB3, 0xBA, 0xCB),  # GREY   тень скафандра, реголит
    (0xF2, 0xC8, 0x9A),  # SKIN   кожа
    (0xC9, 0x8F, 0x5E),  # TAN    тень кожи
    (0xF4, 0xD3, 0x5E),  # GOLD   кристалл, бонус
    (0xC0, 0x8A, 0x2A),  # BRASS  тень золота
    (0x74, 0x7D, 0x92),  # METAL  металл: ранец, перчатки, настил
    (0x3A, 0x40, 0x54),  # DARK   тёмный металл, подошвы
    (0xF0, 0x6A, 0x3A),  # RED    оранжевые нашивки, опасность
    (0x9A, 0x5F, 0xE0),  # VIOLET пришельцы, мох
    (0x55, 0x2F, 0x98),  # PLUM   тень фиолетового
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: DARK, VIOLET: PLUM}
# Материалы для светотени рампами: скафандр одна ткань, визор стекло, металл, нашивки, пришельцы.
GROUPS = {WHITE: "suit", GREY: "suit", AQUA: "glass", SKY: "glass", SEA: "glass", NAVY: "glass",
          SKIN: "skin", TAN: "skin", GOLD: "gold", BRASS: "gold", METAL: "metal", DARK: "metal", RED: "red",
          VIOLET: "alien", PLUM: "alien"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Космонавт ---------------------------------------------------------------------------------
# Силуэт: большой круглый шлем, ранец за спиной, толстые рукава и штанины, тёмные подошвы.
# Узнаётся по визору (бирюзовое стекло спереди) и оранжевой нашивке на плече.

def _helmet(c, x, y, face=1):
    """Шлем с визором, лицом вправо при `face` 1. Центр (x, y), радиус 6."""
    c.ellipse(x, y, 5.7, 5.7, WHITE)
    # Визор: стекло в передней половине шлема, обод темнее, блик сверху.
    c.ellipse(x + 2.5 * face, y + 0.5, 3.4, 3.2, DARK)
    c.ellipse(x + 2.8 * face, y + 0.5, 2.6, 2.4, AQUA)
    c.set(x + 3 * face, y - 1, SKY)
    c.set(x + 4 * face, y - 1, SKY)
    # Кольцо шеи.
    c.rect(x - 3, y + 5, x + 3, y + 5, METAL)


def _pack(c, x, y0, y1):
    """Ранец за спиной: металлический блок с огоньком."""
    c.rect(x, y0, x + 2, y1, METAL)
    c.set(x + 1, y0 + 1, AQUA)


def _body(c, x0, y0, x1, y1):
    """Корпус скафандра: белый, пояс металлом, нагрудный пульт."""
    c.rect(x0, y0, x1, y1, WHITE)
    c.rect(x0, y1 - 1, x1, y1, METAL)
    c.rect(x1 - 3, y0 + 3, x1 - 1, y0 + 4, GREY)
    c.set(x1 - 2, y0 + 3, RED)


def _boot(c, x, y, w=4):
    c.rect(x - 1, y - 1, x + w - 2, y - 1, METAL)
    c.rect(x - 1, y, x + w - 1, y + 1, DARK)


def _arm(c, x0, y0, x1, y1, col):
    """Рукав с перчаткой на конце. Белый рукав поверх белого корпуса отбит тенью снизу."""
    if col == WHITE:
        c.line(x0, y0 + 1, x1 - 1, y1 + 1, GREY, 3)
    c.line(x0, y0, x1, y1, col, 3)
    c.ellipse(x1, y1, 1.4, 1.4, METAL)


def astro_side(phase, jump=False):
    """Космонавт сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), GREY)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 13 - bob, 19 - bob)
    _body(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), WHITE)
    c.rect(15, 14 - bob, 17, 15 - bob, RED)
    _helmet(c, 16, 7 - bob)
    return c.finish()


def astro_back(phase):
    """Со спины: бежит вглубь экрана, виден ранец с двумя баллонами."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, WHITE if sign > 0 else GREY)
        _boot(c, x - 1, 28 - lift)
        _arm(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, WHITE)
    c.rect(11, 13 - bob, 20, 21 - bob, WHITE)
    c.rect(11, 20 - bob, 20, 21 - bob, METAL)
    # Ранец: блок и два баллона.
    c.rect(12, 13 - bob, 19, 19 - bob, METAL)
    c.rect(13, 14 - bob, 14, 18 - bob, GREY)
    c.rect(17, 14 - bob, 18, 18 - bob, GREY)
    c.set(15, 15 - bob, AQUA)
    c.set(16, 15 - bob, AQUA)
    c.ellipse(15.5, 7 - bob, 5.7, 5.7, WHITE)
    c.rect(13, 12 - bob, 18, 12 - bob, METAL)
    c.rect(12, 5 - bob, 19, 5 - bob, GREY)
    return c.finish()


def astro_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, GREY)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 13 + crouch, 19 + crouch)
    _body(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, WHITE)
    c.rect(15, 14 + crouch, 17, 15 + crouch, RED)
    _helmet(c, 16, 7 + crouch)
    c.finish()
    # Выхлоп ранца на толчке и в полёте.
    if i in (1, 2):
        c.set(8, 21 + crouch, AQUA)
        c.set(9, 22 + crouch, SKY)
        c.set(8, 23 + crouch, AQUA)
    return c


def astro_idle(i):
    """Стойка: два кадра, космонавт дышит, огонёк ранца мигает."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, cloth)
        _boot(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, GREY)
    _pack(c, 8, 13 - up, 19 - up)
    _body(c, 11, 13 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 21 - up, WHITE)
    c.rect(15, 14 - up, 17, 15 - up, RED)
    _helmet(c, 16, 7 - up)
    c.finish()
    if i == 1:
        c.set(9, 14 - up, SKY)
    return c


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = METAL if k >= int(n) - 1 else WHITE
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def astro_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх, рука
    сзади на земле. Макушка шлема на 15-й строке, как у матроса. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, GREY, 3)
    c.line(24, 23 - i, 27, 27, GREY, 3)
    _boot(c, 27, 27)
    c.line(13, 24, 19, 23, GREY, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, WHITE, 4)
    c.rect(28, 26, 30, 29, DARK)
    _arm(c, 11, 25, 6, 29, WHITE)
    _helmet(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def astro_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, GREY, 2)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 22, 26)
    c.rect(11, 22, 18, 26, WHITE)
    _arm(c, 14, 24, 19, 26, WHITE)
    _helmet(c, 16, 19)
    return c.finish()


def astro_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, GREY, 3)
    c.line(18, 13, 17, 1, WHITE, 3)
    c.ellipse(15, 1, 1.2, 1.2, METAL)
    c.ellipse(17, 1, 1.2, 1.2, METAL)
    _pack(c, 8, 13, 19)
    _body(c, 11, 13, 20, 21)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], cloth, 3)
        _boot(c, foot[0], foot[1], 3)
    c.finish()
    hd = Canvas()
    _helmet(hd, 16, 8)
    hd.finish()
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Пришелец ----------------------------------------------------------------------------------
# Пехотинец: большая фиолетовая голова с чёрными миндалевидными глазами, тонкое тело в
# металлическом нагруднике, усик с огоньком. Шаг и рост повторяют скелета пиратов.

def alien_side(phase):
    """Пришелец сбоку, лицом влево (навстречу герою): шаг по фазе."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(16, 15 - bob, 16 - 5 * s, 20 - bob, PLUM, 2)
    for sign, col in ((-1, PLUM), (1, VIOLET)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 2)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, DARK)
    # Тело: тонкая шея, нагрудник, пояс.
    c.rect(13, 12 - bob, 18, 21 - bob, VIOLET)
    c.rect(13, 14 - bob, 18, 18 - bob, METAL)
    c.set(14, 15 - bob, AQUA)
    c.rect(13, 21 - bob, 18, 22 - bob, DARK)
    c.line(16, 14 - bob, 16 + 5 * s, 20 - bob, VIOLET, 2)
    # Голова вытянута назад, усик с огоньком.
    c.ellipse(16, 6 - bob, 6.5, 5, VIOLET)
    c.ellipse(19, 4 - bob, 4, 3.5, VIOLET)
    c.line(18, 1 - bob, 21, -1 - bob, PLUM, 1)
    c.finish()
    c.set(21, 0 - bob, AQUA)
    # Глаз: чёрная миндалина с бликом, рот щелью.
    c.poly([(10, 6 - bob), (13, 4 - bob), (15, 6 - bob), (13, 8 - bob)], K)
    c.set(12, 5 - bob, SKY)
    c.rect(11, 10 - bob, 13, 10 - bob, K)
    return c


def alien_front(phase):
    """Пришелец лицом к камере: идёт на игрока, ноги по очереди."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, VIOLET, 3)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
        c.line(16 + sign * 5, 14 - bob, 16 + sign * 8, 20 - bob - s * sign * 2, VIOLET, 2)
    c.rect(12, 12 - bob, 19, 21 - bob, VIOLET)
    c.rect(12, 14 - bob, 19, 18 - bob, METAL)
    c.rect(15, 15 - bob, 16, 16 - bob, AQUA)
    c.rect(12, 21 - bob, 19, 22 - bob, DARK)
    c.ellipse(15.5, 6 - bob, 7, 5.5, VIOLET)
    c.line(11, 1 - bob, 9, -1 - bob, PLUM, 1)
    c.line(20, 1 - bob, 22, -1 - bob, PLUM, 1)
    c.finish()
    for x0, d in ((10, 1), (17, -1)):
        c.poly([(x0, 6 - bob - d), (x0 + 2, 4 - bob), (x0 + 4, 6 - bob + d), (x0 + 2, 8 - bob)], K)
        c.set(x0 + 1, 5 - bob, SKY)
    c.rect(14, 10 - bob, 17, 10 - bob, K)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Кристалл вращается: шесть кадров, ширина по косинусу, грани темнее к краю."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 7.0)
    cx = 15.5
    c.poly([(cx, 5), (cx + rx, 12), (cx + rx * 0.7, 22), (cx, 27), (cx - rx * 0.7, 22), (cx - rx, 12)], GOLD)
    if rx > 3:
        c.poly([(cx, 12), (cx + rx, 12), (cx + rx * 0.7, 22), (cx, 27)], BRASS)
        c.line(cx - rx * 0.5, 10, cx - rx * 0.35, 16, WHITE, 1)
    return c.finish()


def flag(i):
    """Флаг экспедиции на штанге с маячком: оранжевое полотнище с белой планетой идёт волной."""
    c = Canvas()
    c.rect(5, 3, 6, 31, METAL)
    c.ellipse(5.5, 2, 2, 2, AQUA)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        bottom.append((x, 18 + w))
    c.poly(top + bottom[::-1], RED)
    c.shade()
    c.outline()
    mid = math.sin(17 * 0.45 - i * math.pi / 3.0) * 0.8
    c.ellipse(17, 11.5 + mid, 3, 3, WHITE)
    c.line(12, 13 + mid, 22, 10 + mid, WHITE, 1)
    c.set(16, 10 + mid, GREY)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    return c.finish()


def ground(inner=False):
    """Настил станции: металлические панели со швами и заклёпками; у кромки светлая полоса."""
    c = Canvas()
    c.rect(0, 0, 31, 31, METAL)
    for y in (15, 31):
        c.rect(0, y, 31, y, DARK)
    for row, y in enumerate((0, 16)):
        x = (row * 16 + 7) % 32
        c.rect(x, y, x, y + 14, DARK)
        c.rect(x + 1, y, x + 1, y + 14, GREY)
        for dx in (3, 20):
            c.set((x + dx) % 32, y + 2, GREY)
            c.set((x + dx) % 32, y + 12, GREY)
        # Решётка вентиляции на каждой второй панели.
        for k in range(3):
            c.rect((x + 9) % 32, y + 5 + k * 2, (x + 14) % 32 if (x + 14) % 32 > (x + 9) % 32 else 31, y + 5 + k * 2, DARK)
    if not inner:
        c.rect(0, 0, 31, 1, WHITE)
        c.rect(0, 2, 31, 2, GREY)
        for x in range(2, 32, 8):
            c.rect(x, 0, x + 3, 1, RED if (x // 8) % 2 == 0 else WHITE)
    return c


def rock():
    """Метеорит: угловатая глыба с кратерами и жилой кристалла."""
    c = Canvas()
    c.poly([(4, 28), (2, 18), (8, 9), (17, 5), (26, 10), (30, 20), (27, 28)], GREY)
    c.poly([(8, 14), (14, 9), (20, 10), (15, 15)], WHITE)
    c.ellipse(21, 19, 3, 2, METAL)
    c.ellipse(10, 22, 2, 1.5, METAL)
    c.line(14, 20, 18, 26, VIOLET, 1)
    return c.finish()


def chest():
    """Грузовая капсула: металлический бочонок с окошком и оранжевой полосой."""
    c = Canvas()
    c.rect(4, 12, 27, 28, METAL)
    c.ellipse(15.5, 12, 12, 6, METAL)
    c.rect(4, 19, 27, 21, RED)
    for x in (8, 23):
        c.rect(x, 7, x + 1, 28, DARK)
    c.ellipse(15.5, 13, 3.5, 3, AQUA)
    c.set(14, 12, SKY)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------

def par_sky():
    """Дальний слой: туманности и звёзды, лента 256×48, стыкуется по краям."""
    import random
    c = Canvas(256, 48)
    for cx, cy, r in ((30, 18, 13), (52, 22, 9), (130, 30, 14), (226, 14, 12), (246, 19, 8)):
        for k in (0, 256, -256):
            c.ellipse(cx + k, cy, r, r * 0.4, SEA)
            c.ellipse(cx + k - r * 0.4, cy + 2, r * 0.6, r * 0.25, PLUM)
    rng = random.Random(11)
    for _ in range(46):
        c.set(rng.randint(0, 255), rng.randint(0, 47), WHITE if rng.random() < 0.6 else SKY)
    return c


def par_far():
    """Средний слой: гряда кратеров на горизонте с куполами станции, лента 256×48, низ сплошной."""
    c = Canvas(256, 48)

    def height(x):
        h = 9 + 9 * max(0.0, math.sin(x * math.pi / 64.0)) ** 2 + 4 * math.sin(x * math.pi / 16.0 + 1.0)
        return h + 12 * max(0.0, math.sin((x - 40) * math.pi / 128.0)) ** 6

    for x in range(256):
        top = 47 - int(max(height(x), 3))
        c.rect(x, top, x, 47, PLUM)
        c.rect(x, top, x, top + 1, VIOLET)
    # Купола станции с огнями и мачта антенны.
    for px, r in ((32, 7), (100, 5), (168, 8), (232, 6)):
        ground_y = 47 - int(height(px))
        c.ellipse(px, ground_y, r, r * 0.8, SEA)
        c.rect(px - r, ground_y, px + r, ground_y + 2, PLUM)
        for dx in (-r // 2, 0, r // 2):
            c.set(px + dx, ground_y - 2, AQUA)
    c.line(134, 47 - int(height(134)), 134, 47 - int(height(134)) - 12, SEA, 1)
    c.set(134, 47 - int(height(134)) - 13, RED)
    return c


def par_mid():
    """Ближний слой: бугры реголита с камнями, лента 256×32."""
    c = Canvas(256, 32)
    for x in range(256):
        crest = 6 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0)
        top = int(round(crest))
        c.rect(x, top, x, 31, METAL)
        c.rect(x, top, x, top + 1, GREY)
        if (x * 7 + top * 3) % 23 == 0:
            c.rect(x, top + 6 + (x % 9), x + 1, top + 6 + (x % 9), DARK)
        if x % 41 == 5:
            c.ellipse(x, top + 12, 3, 1.5, DARK)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, пришелец, вещи, земля, три
    слоя дали. Ленты демок лежат в модулях `space_*16.py`."""
    return {
        "enemy_walk": strip([alien_side(p) for p in base.phases()]),
        "enemy_front": strip([alien_front(p) for p in base.phases()]),
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
        "hero_run": strip([astro_side(p) for p in base.phases()]),
        "hero_jump": astro_side(0.0, jump=True),
        "hero_leap": strip([astro_leap(i) for i in range(4)]),
        "hero_idle": strip([astro_idle(i) for i in range(2)]),
        "hero_back": strip([astro_back(p) for p in base.phases()]),
        "hero_slide": strip([astro_slide(i) for i in range(2)]),
        "hero_hang": strip([astro_hang(i) for i in range(2)]),
        "hero_crouch": strip([astro_crouch(i) for i in range(2)]),
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


def preview(path, scale=4, pad=6, back=(0x1B, 0x1A, 0x33, 255)):
    """Лист набора: лента на строку, как в игре, после светотени."""
    palette, items, own = base.space_set()
    width = (max(c.w for c in items.values()) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for key, canvas in items.items():
        for row in base.rgba_rows(canvas, own.get(key, palette), scale, back):
            line = list(back) * pad * scale + row
            rows.append(line + list(back) * ((len(blank) - len(line)) // 4))
        rows.extend(blank[:] for _ in range(pad * scale))
    with open(path, "wb") as f:
        f.write(png_bytes(width, len(rows), rows))
    print("превью: %s" % path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
