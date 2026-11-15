#!/usr/bin/env python3
"""Набор «Замки» для 16/32-bit, сравнительная версия основы (#137, состав в
`docs/specs/settings.md`): рыцарь в стальных латах с ведёрным шлемом, красным плюмажем и красным
табардом, стражник чужого замка в чёрной кольчуге и багровой тунике с алебардой, летучая мышь,
кабан. Те же ленты и кадры, что у пиратов и космоса (`pixel_sprites16.py`, `space16.py`): позы и
опора ног повторяют матроса, чтобы хитбоксы демок сходились, а рисунок свой.

    python3 tools/castles16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Замки»: 16 цветов, индекс это та же роль, что у пиратов и космоса (ими рисуют HUD и
# мир демки). Имена констант общие с космосом; что за ними стоит здесь, написано справа.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x15, 0x13, 0x1A),  # K      обводка
    (0x27, 0x3B, 0x76),  # NAVY   верх неба, тень синего, перепонки мыши
    (0x46, 0x76, 0xC0),  # SEA    небо, дальние горы, река
    (0x86, 0xBE, 0xE8),  # AQUA   светлое небо, блик воды
    (0xD3, 0xEC, 0xF6),  # SKY    небо у горизонта, стекло
    (0xE8, 0xEC, 0xF2),  # WHITE  блик стали, облака
    (0x9E, 0xA8, 0xBA),  # GREY   сталь лат, светлый камень
    (0xF0, 0xC4, 0x98),  # SKIN   кожа
    (0x94, 0x28, 0x38),  # TAN    багровый: туника стражи, тень красного
    (0xF4, 0xC8, 0x4A),  # GOLD   золото: пояс, монета, герб
    (0x9C, 0x64, 0x2C),  # BRASS  тень золота, дерево, щетина кабана
    (0x7C, 0x78, 0x76),  # METAL  камень кладки, тёмная сталь
    (0x3C, 0x40, 0x50),  # DARK   чёрная кольчуга, железо, швы кладки
    (0xD2, 0x30, 0x2C),  # RED    табард, плюмаж, опасность
    (0x5C, 0xAE, 0x4A),  # VIOLET трава, мох, листва
    (0x2A, 0x6A, 0x3E),  # PLUM   тень зелени, ели
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: BRASS, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: TAN, VIOLET: PLUM}
# Материалы для светотени рампами: латы одна сталь, камень и железо, табард, багровая туника,
# золото, дерево, зелень.
GROUPS = {WHITE: "steel", GREY: "steel", AQUA: "blue", SKY: "blue", SEA: "blue", NAVY: "blue",
          SKIN: "skin", TAN: "crimson", GOLD: "gold", BRASS: "wood", METAL: "iron", DARK: "iron", RED: "red",
          VIOLET: "green", PLUM: "green"}


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
    """Враг тропы: тень как у всех, обводка красная, а не чёрная: опасен, убить нельзя."""
    c.shade()
    c.outline(RED)
    return c


# --- Рыцарь ------------------------------------------------------------------------------------
# Силуэт: плоский сверху ведёрный шлем, над ним гребень, хвост плюмажа летит за затылком, табард
# с юбкой ниже пояса, за бедром ножны. Узнаётся по прорези шлема и красному хвосту плюмажа.

def _helm(c, x, y, wave=0, tail=1.0, comb=3):
    """Ведёрный шлем лицом вправо: коробка 10×10 с центром (x, y), гребень сверху и хвост
    плюмажа назад (`wave` качает хвост по вертикали, `tail` его длина, `comb` полуширина
    гребня)."""
    c.line(x - 4, y - 5, x - 5 - 2 * tail, y - 3 + wave, RED, 3)
    c.line(x - 5 - 2 * tail, y - 3 + wave, x - 6 - 2 * tail, y + 1 + wave * 2, RED, 3)
    c.rect(x - comb, y - 6, x + comb - 1, y - 5, RED)
    c.rect(x - 5, y - 4, x + 4, y + 5, WHITE)
    # Тёмный обод по низу и ребро через прорезь: вместе с прорезью дают крест ведёрного шлема.
    c.rect(x - 5, y + 4, x + 4, y + 4, GREY)
    c.rect(x - 5, y + 5, x + 4, y + 5, METAL)
    c.rect(x + 1, y - 3, x + 1, y + 4, METAL)


def _visor(c, x, y):
    """Прорезь и дыхательные отверстия: ставятся после обводки, чтобы остались чёрными."""
    c.rect(x - 2, y, x + 3, y, K)
    c.set(x + 3, y + 2, K)
    c.set(x - 1, y + 2, K)
    c.set(x + 3, y + 3, K)


def _scabbard(c, x, y):
    """Ножны за бедром: тёмная полоса наискось с золотым наконечником."""
    c.line(x, y, x - 5, y + 5, DARK, 3)
    c.set(x - 6, y + 6, GOLD)
    c.set(x - 5, y + 6, GOLD)


def _body(c, x0, y0, x1, y1):
    """Корпус: красный табард с юбкой на два пикселя ниже бёдер, золотой пояс, стальной ворот."""
    c.rect(x0, y0, x1, y1 + 2, RED)
    c.rect(x0, y1 - 2, x1, y1 - 1, GOLD)
    c.rect(x0 + 1, y0, x1 - 1, y0, GREY)


def _boot(c, x, y, w=4):
    c.rect(x - 1, y - 1, x + w - 2, y - 1, METAL)
    c.rect(x - 1, y, x + w - 1, y + 1, DARK)


def _inlay(c, draw):
    """Деталь поверх фигуры с чёрной кромкой там, где она ложится на уже нарисованное: так
    стальная рука не сливается с табардом и шлемом."""
    t = Canvas(c.w, c.h)
    draw(t)
    for y in range(t.h):
        for x in range(t.w):
            if t.px[y][x] is None:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if t.get(x + dx, y + dy) is None and c.get(x + dx, y + dy) is not None:
                    c.set(x + dx, y + dy, K)
    c.paste(t, 0, 0)


def _arm(c, x0, y0, x1, y1, col):
    """Латная рука: наплечник у плеча, рукав, тёмная перчатка на конце. Ближняя (светлая)
    ложится на корпус с кромкой."""
    def draw(t):
        t.line(x0, y0, x1, y1, col, 3)
        t.ellipse(x0, y0, 2, 2, col)
        t.ellipse(x1, y1, 1.4, 1.4, METAL)

    if col == WHITE:
        _inlay(c, draw)
    else:
        draw(c)


def _leg(c, hip, knee, foot, col):
    """Латная нога: набедренник толще, наголенник тоньше, наколенник темнее, сабатон."""
    c.line(hip[0], hip[1], knee[0], knee[1], col, 4)
    c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
    c.set(knee[0] + 1, knee[1], METAL)
    _boot(c, foot[0], foot[1])


def knight_side(phase, jump=False):
    """Рыцарь сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _scabbard(c, 12, hip_y - 2)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), GREY)
    for sign, steel in ((-1, GREY), (1, WHITE)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        _leg(c, (15 + sign, hip_y), knee, foot, steel)
    _body(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), WHITE)
    wave = -2 if jump else int(round(math.cos(phase)))
    _helm(c, 16, 7 - bob, wave, 1.0 if jump else 1.5)
    c.finish()
    _visor(c, 16, 7 - bob)
    return c


def knight_back(phase):
    """Со спины: бежит вглубь экрана, плюмаж падает на затылок, табард с золотым поясом."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, WHITE if sign > 0 else GREY)
        _boot(c, x - 1, 28 - lift)
        _arm(c, 16 + sign * 6 - (1 if sign < 0 else 0), 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, WHITE)
    c.rect(11, 13 - bob, 20, 23 - bob, RED)
    c.rect(11, 19 - bob, 20, 20 - bob, GOLD)
    # Разрез юбки табарда посередине.
    c.rect(15, 22 - bob, 16, 23 - bob, TAN)
    c.rect(12, 13 - bob, 19, 13 - bob, GREY)
    # Шлем со спины: коробка, пояс по низу, плюмаж от гребня вниз по затылку.
    c.rect(11, 3 - bob, 20, 12 - bob, WHITE)
    c.rect(11, 11 - bob, 20, 12 - bob, GREY)
    c.rect(13, 1 - bob, 18, 2 - bob, RED)
    c.rect(15, 3 - bob, 16, 7 - bob, RED)
    c.rect(15 + int(round(s)), 8 - bob, 16 + int(round(s)), 9 - bob, RED)
    return c.finish()


def knight_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _scabbard(c, 12, hip_y - 2)
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, GREY)
    for sign, steel in ((-1, GREY), (1, WHITE)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        _leg(c, (15 + sign, hip_y), knee, foot, steel)
    _body(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, WHITE)
    # Плюмаж: при толчке хвост тянет вниз, в полёте и на приземлении его подбрасывает.
    _helm(c, 16, 7 + crouch, (0, 2, 0, -2)[i], (1.0, 1.0, 1.5, 1.0)[i])
    c.finish()
    _visor(c, 16, 7 + crouch)
    return c


def knight_idle(i):
    """Стойка: два кадра, рыцарь дышит, плюмаж чуть качается."""
    c = Canvas()
    up = i
    _scabbard(c, 12, 19)
    for sign, steel in ((-1, GREY), (1, WHITE)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, steel)
        c.set(x + 1, 25, METAL)
        _boot(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, GREY)
    _body(c, 11, 13 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 21 - up, WHITE)
    _helm(c, 16, 7 - up, 1 - i, 1.0)
    c.finish()
    _visor(c, 16, 7 - up)
    return c


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = GOLD if k >= int(n) - 1 else RED
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def knight_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх, рука
    сзади на земле, плюмаж летит назад. Верх гребня на 15-й строке, как макушка матроса. Два
    кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, GREY, 3)
    c.line(24, 23 - i, 27, 27, GREY, 3)
    _boot(c, 27, 27)
    c.line(13, 24, 19, 23, GREY, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, WHITE, 3)
    c.set(24, 27, METAL)
    c.rect(28, 26, 30, 29, DARK)
    _arm(c, 12, 25, 7, 29, WHITE)
    _helm(c, 10, 21, -1 + i, 0.5)
    c.finish()
    _visor(c, 10, 21)
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def knight_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, GREY, 2)
    for sign, steel in ((-1, GREY), (1, WHITE)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], steel, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], steel, 3)
        _boot(c, foot[0], foot[1])
    c.rect(11, 22, 18, 27, RED)
    c.rect(11, 26, 16, 27, GOLD)
    _arm(c, 13, 24, 19, 26, WHITE)
    _helm(c, 16, 19, i, 1.0)
    c.finish()
    _visor(c, 16, 19)
    return c


def knight_hang(i):
    """На тросе: руки по бокам шлема сходятся вверх к точке хвата (центр сверху), плечи
    подтянуты к шлему, ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    _scabbard(c, 12, 20 + (1 if sw > 0 else 0))
    for sign, steel in ((-1, GREY), (1, WHITE)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 22, foot[0], foot[1], steel, 3)
        _boot(c, foot[0], foot[1], 3)
    _body(c, 11, 17, 20, 22)
    _helm(c, 16, 12, 2 - i, 0.0, 2)
    # Руки: от наплечника вверх вдоль шлема с зазором под обводку, над шлемом сходятся к хвату.
    for side, steel in ((-1, GREY), (1, WHITE)):
        x = 15.5 + side * 7
        c.rect(x - 0.5, 9, x + 0.5, 19, steel)
        c.rect(x - 0.5 - (side < 0), 17, x + 0.5 + (side > 0), 19, steel)
        for k in range(1, 8):
            xk = x - side * k * 0.8
            c.rect(xk - 0.5, 9 - k, xk + 0.5, 9 - k, steel)
    c.rect(14, 0, 17, 1, METAL)
    c.finish()
    _visor(c, 16, 12)
    return c


# --- Стражник ----------------------------------------------------------------------------------
# Пехотинец чужого замка: шлем-котелок с широкими полями, чёрная кольчуга с капюшоном, багровая
# туника, алебарда выше головы. Шаг и рост повторяют скелета пиратов.

def _halberd(c, x, top, bottom, face=-1):
    """Алебарда: древко от `top` до `bottom`, лезвие топора в сторону `face`, пика и крюк."""
    c.rect(x, top, x, bottom, BRASS)
    c.poly([(x + face, top + 3), (x + face * 4, top), (x + face * 6, top + 1), (x + face * 6, top + 7),
            (x + face * 4, top + 8), (x + face, top + 5)], WHITE)
    c.rect(min(x - face, x - face * 2), top + 3, max(x - face, x - face * 2), top + 4, GREY)
    c.rect(x, top - 2, x, top, GREY)


def _kettle(c, x, y, x0, x1):
    """Шлем-котелок: купол над полями от x0 до x1, поля на строках y и y+1."""
    c.ellipse(x, y - 1, 4.6, 4, GREY)
    c.ellipse(x - 1.5, y - 2.5, 1.6, 1.2, WHITE)
    c.rect(x0, y, x1, y + 1, GREY)
    c.rect(x0 + 1, y, x1 - 3, y, WHITE)


def guard_side(phase):
    """Стражник сбоку, лицом влево (навстречу герою): шаг по фазе, алебарда в передней руке."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(17, 15 - bob, 17 - 4 * s, 20 - bob, DARK, 3)
    for sign in (-1, 1):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], DARK, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], DARK, 3)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, BRASS)
    # Туника поверх кольчуги: кольчужный ворот и подол, ремень с пряжкой.
    c.rect(12, 12 - bob, 19, 24 - bob, DARK)
    c.rect(12, 13 - bob, 19, 23 - bob, TAN)
    c.rect(12, 19 - bob, 19, 19 - bob, DARK)
    c.set(13, 19 - bob, GOLD)
    _halberd(c, 7, 3 - bob, 30)
    # Ближняя рука держит древко.
    c.line(16, 14 - bob, 9, 17 - bob, DARK, 3)
    c.ellipse(8, 17 - bob, 1.4, 1.4, SKIN)
    # Голова: лицо под полями, кольчужный капюшон на затылке и под подбородком.
    c.rect(12, 8 - bob, 20, 12 - bob, DARK)
    c.rect(12, 8 - bob, 16, 11 - bob, SKIN)
    c.set(11, 10 - bob, SKIN)
    _kettle(c, 16, 6 - bob, 10, 22)
    c.finish()
    c.set(13, 9 - bob, K)
    c.rect(12, 11 - bob, 13, 11 - bob, K)
    return c


def guard_front(phase):
    """Стражник лицом к камере: идёт на игрока, ноги по очереди, алебарда сбоку."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, DARK, 3)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, BRASS)
    # Рука с алебардой слева, свободная качается.
    c.line(20, 14 - bob, 23, 20 - bob + s * 2, DARK, 3)
    c.ellipse(23, 21 - bob + s * 2, 1.2, 1.2, SKIN)
    c.rect(12, 12 - bob, 19, 24 - bob, DARK)
    c.rect(12, 13 - bob, 19, 23 - bob, TAN)
    c.rect(12, 19 - bob, 19, 19 - bob, DARK)
    c.rect(15, 19 - bob, 16, 19 - bob, GOLD)
    _halberd(c, 7, 3 - bob, 30)
    c.line(11, 14 - bob, 9, 18 - bob, DARK, 3)
    c.ellipse(8, 18 - bob, 1.4, 1.4, SKIN)
    c.rect(12, 8 - bob, 19, 12 - bob, DARK)
    c.rect(13, 8 - bob, 18, 11 - bob, SKIN)
    _kettle(c, 15.5, 6 - bob, 9, 22)
    c.finish()
    c.set(14, 9 - bob, K)
    c.set(17, 9 - bob, K)
    c.rect(14, 11 - bob, 17, 11 - bob, K)
    return c


# --- Летун и ползун ----------------------------------------------------------------------------

def bat(i):
    """Летучая мышь летит на игрока, четыре кадра взмаха (вверх, середина, вниз, середина):
    тёмное тело с ушами, синие перепонки с зубцами по нижнему краю, жёлтые глаза. Тело по
    центру кадра, чтобы при развороте не прыгало; обводка опасности красная."""
    c = Canvas()
    wing = (-8, -2, 6, -2)[i]
    dy = (1, 0, -1, 0)[i]
    for sign in (-1, 1):
        sx = 16 + sign * 3
        tip = (16 + sign * 13, 14 + wing)
        f2 = (16 + sign * 10, 19 + wing * 0.6)
        f3 = (16 + sign * 6, 21 + wing * 0.3)
        c.poly([(sx, 12 + dy), tip, ((tip[0] + f2[0]) / 2 - sign, (tip[1] + f2[1]) / 2 - 2), f2,
                ((f2[0] + f3[0]) / 2, (f2[1] + f3[1]) / 2 - 2.5), f3, (sx, 18 + dy)], NAVY)
        for end in (tip, f2, f3):
            c.line(sx, 13 + dy, end[0], end[1], DARK, 1)
    c.ellipse(16, 16 + dy, 3.5, 4.5, DARK)
    c.ellipse(16, 11.5 + dy, 3.2, 2.8, DARK)
    for sign in (-1, 1):
        c.poly([(16 + sign * 3, 11 + dy), (16 + sign * 4, 5 + dy), (16 + sign, 9 + dy)], DARK)
    _danger(c)
    c.set(15, 11 + dy, GOLD)
    c.set(17, 11 + dy, GOLD)
    c.set(15, 13 + dy, WHITE)
    c.set(17, 13 + dy, WHITE)
    return c


def boar(i):
    """Кабан идёт влево, четыре кадра: ноги по очереди, холка горбом с тёмной щетиной, рыло с
    пятачком и белым клыком, хвост крючком. Обводка опасности красная."""
    c = Canvas()
    up = i % 2
    for k, x in enumerate((9, 13, 21, 25)):
        fwd = (k + i) % 2
        c.rect(x - fwd, 24, x + 1 - fwd, 29 - (1 - fwd), DARK)
    c.line(27, 18 - up, 29, 15 - up, BRASS, 1)
    c.set(30, 16 - up, BRASS)
    c.ellipse(18, 20 - up, 9.5, 5.5, BRASS)
    c.ellipse(12, 19 - up, 6, 6.5, BRASS)
    # Голова клином вниз, рыло с пятачком.
    c.poly([(9, 15 - up), (3, 20 - up), (1, 23 - up), (2, 26 - up), (9, 26 - up)], BRASS)
    c.rect(1, 23 - up, 2, 25 - up, SKIN)
    # Щетина гребнем по холке и спине.
    for x in range(8, 23):
        y0 = 13 - up + max(0, x - 13) * 0.25
        c.rect(x, y0 - (1 if x % 3 == 0 else 0), x, y0 + 1, DARK)
    c.poly([(9, 16 - up), (10, 12 - up), (12, 16 - up)], DARK)
    c.ellipse(18, 25 - up, 6, 1, DARK)
    _danger(c)
    c.set(6, 20 - up, K)
    for x, y in ((4, 24), (4, 23), (5, 22)):
        c.set(x, y - up, WHITE)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Золотая монета с короной вращается: шесть кадров, ширина по косинусу, корона чеканкой."""
    c = Canvas()
    k = abs(math.cos(math.pi * i / 6.0))
    rx = max(1.0, k * 8.0)
    cx = 15.5
    c.ellipse(cx, 16, rx, 9.5, GOLD)
    if rx > 3:
        w = 5.0 * k
        c.poly([(cx - w, 20), (cx - w, 12), (cx - w / 2, 16), (cx, 11.5), (cx + w / 2, 16), (cx + w, 12),
                (cx + w, 20)], BRASS)
        c.rect(cx - w, 18, cx + w, 18, GOLD)
        c.line(cx - rx * 0.55, 8.5, cx - rx * 0.8, 11.5, WHITE, 1)
    return c.finish()


def flag(i):
    """Знамя на древке с золотым навершием: красное полотнище с косицами идёт волной, на нём
    герб, золотой щит с синим крестом."""
    c = Canvas()
    c.rect(5, 4, 6, 31, BRASS)
    c.poly([(4, 4), (5.5, 0), (7, 4)], GOLD)
    c.rect(4, 4, 7, 4, GOLD)

    def wave(x):
        return math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0

    top = [(x, 5 + wave(x)) for x in range(8, 30)]
    bottom = [(x, 19 + wave(x)) for x in range(8, 30)]
    c.poly(top + [(24, 12 + wave(24))] + bottom[::-1], RED)
    c.shade()
    c.outline()
    sy = int(round(8 + wave(15) * 0.8))
    for row, (x0, x1) in enumerate(((12, 18), (12, 18), (12, 18), (12, 18), (12, 18), (13, 17), (14, 16), (15, 15))):
        c.rect(x0, sy + row, x1, sy + row, GOLD)
    c.rect(15, sy, 15, sy + 6, SEA)
    c.rect(12, sy + 2, 18, sy + 2, SEA)
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
    """Каменная кладка: ряды тёсаных блоков вперевязку, тёмные швы, светлая грань сверху; у
    кромки шапка дёрна с бахромой травы и цветами. Плитка стыкуется со всех сторон."""
    c = Canvas()
    c.rect(0, 0, 31, 31, METAL)
    for r in range(4):
        y0 = r * 8
        light = (r * 3 + 1) % 4
        for k in range(2):
            x0 = ((r % 2) * 8 + k * 16) % 32
            for x in range(x0 + 1, x0 + 16):
                c.set(x % 32, y0, GREY)
                if (r + k) % 3 == 0 and y0 + 6 < 32:
                    # Отдельные блоки светлее: кладка не выглядит обоями.
                    for y in range(y0 + 1, y0 + 6):
                        if (x + y * 2 + light) % 7 != 0:
                            c.set(x % 32, y, GREY)
                    c.set(x % 32, y0, WHITE)
            c.rect(x0, y0, x0, y0 + 6, DARK)
            # Щербины и мох в швах.
            c.set((x0 + 5 + r * 3) % 32, y0 + 3, DARK)
            c.set((x0 + 11 + r) % 32, y0 + 5, DARK)
            if (r + k) % 2 == 1:
                c.set((x0 + 2) % 32, y0 + 6, PLUM)
                c.set((x0 + 3) % 32, y0 + 6, PLUM)
        c.rect(0, y0 + 7, 31, y0 + 7, DARK)
    if not inner:
        c.rect(0, 0, 31, 2, VIOLET)
        for x in range(32):
            d = (1, 2, 1, 3, 2, 1, 2, 4)[x % 8]
            c.rect(x, 3, x, 2 + d, PLUM)
            if x % 4 == 1:
                c.set(x, 1, PLUM)
        for x, col in ((6, GOLD), (21, WHITE), (27, GOLD)):
            c.set(x, 1, col)
    return c


def rock():
    """Замшелый валун: округлая серая глыба с трещиной, сверху сползает шапка мха."""
    c = Canvas()
    c.ellipse(16, 19, 13, 9, GREY)
    c.ellipse(12, 15, 8, 7, GREY)
    c.ellipse(21, 16, 7, 6.5, GREY)
    c.rect(5, 26, 27, 28, GREY)
    c.line(7, 17, 10, 14, WHITE, 1)
    c.line(8, 18, 9, 17, WHITE, 1)
    c.rect(8, 28, 26, 28, METAL)
    c.line(19, 17, 22, 21, METAL, 1)
    c.line(22, 21, 20, 25, METAL, 1)
    c.line(22, 21, 25, 22, METAL, 1)
    # Мох: по каждому столбцу от верхней кромки вниз на свою глубину, нижний пиксель темнее.
    for x in range(9, 28):
        top = next((y for y in range(32) if c.px[y][x] is not None), None)
        if top is None:
            continue
        depth = (2, 3, 2, 4, 3, 5, 3, 2, 4)[x % 9]
        if x < 12 or x > 25:
            depth = 1
        c.rect(x, top, x, top + depth - 1, VIOLET)
        c.set(x, top + depth, PLUM)
    c.ellipse(6, 23, 2, 1.2, VIOLET)
    return c.finish()


def chest():
    """Окованный ларь: дубовые доски, выпуклая крышка, железные полосы с заклёпками, золотой
    замок с тёмной скважиной."""
    c = Canvas()
    c.rect(4, 14, 27, 28, BRASS)
    c.ellipse(15.5, 14, 12, 6.5, BRASS)
    for y in (10, 20, 24):
        c.rect(5, y, 26, y, DARK)
    c.rect(4, 14, 27, 15, METAL)
    c.rect(4, 27, 27, 28, METAL)
    for x in (7, 22):
        c.rect(x, 9, x + 2, 28, METAL)
        for y in (11, 18, 22, 25):
            c.set(x + 1, y, WHITE)
    c.rect(13, 13, 18, 19, GOLD)
    c.finish()
    c.rect(15, 15, 16, 16, K)
    c.rect(15, 17, 15, 17, K)
    return c


def key():
    """Ключ от ворот: золотой, головка трилистником, две бородки."""
    c = Canvas(32, 32)
    for cx, cy in ((7, 16), (11, 11), (11, 21)):
        c.ellipse(cx, cy, 4, 4, GOLD)
    for cx, cy in ((7, 16), (11, 11), (11, 21)):
        c.ellipse(cx, cy, 1.5, 1.5, None)
    c.rect(11, 14, 14, 18, GOLD)
    c.rect(13, 15, 29, 17, GOLD)
    c.rect(16, 13, 17, 19, GOLD)
    c.rect(22, 18, 24, 23, GOLD)
    c.rect(27, 18, 29, 21, GOLD)
    c.set(23, 21, None)
    c.rect(13, 15, 29, 15, WHITE)
    return c.finish()


def medkit():
    """Лечебное зелье: пузатая склянка с красным настоем и белым крестом, пробка сверху."""
    c = Canvas(32, 32)
    c.rect(13, 7, 18, 13, SKY)
    c.rect(12, 6, 19, 7, GREY)
    c.rect(14, 2, 17, 5, BRASS)
    c.ellipse(15.5, 20, 9.5, 8.5, SKY)
    for y in range(16, 29):
        for x in range(32):
            if ((x - 15.5) / 8.0) ** 2 + ((y - 20) / 7.0) ** 2 <= 1.0:
                c.set(x, y, RED)
    c.rect(15, 18, 16, 25, WHITE)
    c.rect(12, 21, 19, 22, WHITE)
    c.finish()
    c.set(10, 15, WHITE)
    c.set(9, 16, WHITE)
    return c


def shot():
    """Снаряд стражи летит в игрока: шипастое железное ядро с бликом, обводка опасности."""
    c = Canvas(16, 16)
    c.rect(7, 1, 8, 14, GREY)
    c.rect(1, 7, 14, 8, GREY)
    for dx in (-1, 1):
        for dy in (-1, 1):
            c.set(7.5 + dx * 3.5, 7.5 + dy * 3.5, GREY)
    c.ellipse(7.5, 7.5, 3.6, 3.6, METAL)
    c.ellipse(6.5, 6.5, 1.2, 1.2, WHITE)
    c.shade()
    c.outline(RED)
    return c


# --- Параллакс ---------------------------------------------------------------------------------

def _cloud(c, cx, cy, r):
    """Кучевое облако: три горба, плоский низ, синеватая тень по брюху."""
    for k in (0, 256, -256):
        x = cx + k
        c.ellipse(x, cy, r, r * 0.42, WHITE)
        c.ellipse(x - r * 0.4, cy - r * 0.22, r * 0.5, r * 0.4, WHITE)
        c.ellipse(x + r * 0.25, cy - r * 0.35, r * 0.45, r * 0.42, WHITE)
        c.ellipse(x + r * 0.1, cy + r * 0.3, r * 0.75, r * 0.14, SKY)
        c.ellipse(x + r * 0.3, cy + r * 0.38, r * 0.4, r * 0.08, AQUA)


def par_sky():
    """Дальний слой: кучевые облака и стая птиц, лента 256×48, стыкуется по краям."""
    c = Canvas(256, 48)
    for cx, cy, r in ((34, 16, 17), (72, 30, 10), (128, 12, 12), (168, 32, 18), (222, 18, 14), (250, 36, 8)):
        _cloud(c, cx, cy, r)
    for x, y in ((98, 22), (104, 19), (111, 23), (198, 8)):
        c.set(x - 1, y - 1, DARK)
        c.set(x, y, DARK)
        c.set(x + 1, y - 1, DARK)
    return c


def _hill(x):
    return (11 + 4 * math.sin(x * math.pi / 64.0 + 1.2) + 2 * math.sin(x * math.pi / 32.0)
            + 9 * max(0.0, math.cos((x - 96) * math.pi / 128.0)) ** 10)


def _tower(c, x0, x1, top, bottom, roof):
    """Башня замка: зубцы или шатёр, светлая грань слева, тень справа, бойница."""
    c.rect(x0, top, x1, bottom, GREY)
    c.rect(x1 - 1, top, x1, bottom, METAL)
    c.rect(x0, top, x0, bottom, WHITE)
    mid = (x0 + x1) / 2.0
    if roof:
        c.poly([(x0 - 1, top), (mid, top - roof), (x1 + 1, top)], RED)
        c.poly([(mid + 1, top - roof + 2), (x1 + 1, top), (mid + 1, top)], TAN)
    else:
        for x in range(x0, x1 + 1, 2):
            c.set(x, top - 1, GREY)
    c.rect(int(mid), top + 3, int(mid), top + 5, DARK)


def par_far():
    """Средний слой: синие горы, перед ними зелёные холмы с замком на главном и сторожевой
    башней на дальнем, лента 256×48, низ сплошной."""
    c = Canvas(256, 48)

    def ridge(x):
        return 25 + 7 * math.sin(x * math.pi / 64.0 + 0.6) + 4 * abs(math.sin(x * math.pi / 32.0 + 2.1)) + 2 * math.sin(x * math.pi / 16.0 + 1.0)

    for x in range(256):
        top = 47 - int(ridge(x))
        c.rect(x, top, x, 47, SEA)
        # Освещённый склон смотрит влево, снег на самых высоких гребнях.
        if ridge(x + 1) > ridge(x):
            c.rect(x, top, x, top + 2, AQUA)
        if ridge(x) > 33:
            c.rect(x, top, x, top + 1, SKY)
    # Замок рисуется до холма: холм закрывает подошву стен.
    b = 47 - int(_hill(96))
    c.rect(82, b - 8, 110, b + 6, GREY)
    for x in range(82, 111, 3):
        c.rect(x, b - 10, x + 1, b - 9, GREY)
    for x in range(84, 110, 5):
        c.set(x, b - 5, METAL)
        c.set(x + 2, b - 2, METAL)
    c.rect(94, b - 4, 97, b + 6, DARK)
    c.rect(95, b - 5, 96, b - 5, DARK)
    _tower(c, 90, 101, b - 16, b - 9, 8)
    _tower(c, 77, 83, b - 15, b + 6, 7)
    _tower(c, 108, 113, b - 12, b + 6, 6)
    c.rect(95, b - 27, 95, b - 24, DARK)
    c.rect(96, b - 27, 98, b - 26, GOLD)
    b2 = 47 - int(_hill(214))
    _tower(c, 211, 216, b2 - 10, b2 + 6, 5)
    for x in range(256):
        top = 47 - int(_hill(x))
        c.rect(x, top, x, 47, VIOLET)
        for y in range(top + 3, 48):
            # Тень склона вниз: сначала через пиксель, потом сплошная.
            if y >= top + 9 or (x + y) % 2 == 0 and (y >= top + 5 or _hill(x + 1) < _hill(x)):
                c.set(x, y, PLUM)
    # Мелкие ели по гребням холмов.
    for x in (12, 18, 40, 46, 52, 132, 140, 146, 170, 190, 196, 236, 242):
        top = 47 - int(_hill(x))
        for r in range(5):
            c.rect(x - r // 2, top - 4 + r, x + r // 2, top - 4 + r, PLUM)
    return c


def _fir(c, x, ground_y, h):
    """Ель: три яруса лапника, тёмная, свет по левому краю, короткий ствол."""
    c.rect(x, ground_y - 2, x, ground_y, BRASS)
    n = h - 2
    for r in range(n):
        tier = r * 3 // n
        within = r - tier * n / 3.0
        half = int(0.6 + within * 0.8 + tier * 0.9)
        y = ground_y - h + r
        c.rect(x - half, y, x + half, y, PLUM)
        if half >= 1 and r % 2 == 0:
            c.set(x - half, y, VIOLET)
            c.set(x - half + 1, y, VIOLET)


def _oak(c, x, ground_y, h):
    """Дуб: круглая светлая крона из трёх шапок с тенью снизу справа, толстый ствол."""
    r = h * 0.42
    cy = ground_y - h + r
    c.rect(x, cy, x + 1, ground_y, BRASS)
    c.rect(x + 1, cy, x + 1, ground_y, DARK)
    c.ellipse(x + 0.5, cy, r + 2, r, PLUM)
    c.ellipse(x - r * 0.7, cy + 1, r * 0.8, r * 0.7, PLUM)
    c.ellipse(x + 0.5 - 1, cy - 1, r + 1, r - 1, VIOLET)
    c.ellipse(x - r * 0.7 - 1, cy, r * 0.7, r * 0.5, VIOLET)
    for k in range(int(r) + 1):
        c.set(x - 1 + k * 2 - int(r * 0.5), cy + (k % 2), PLUM)


def par_mid():
    """Ближний слой: луг с ельником и дубами над берегом реки, лента 256×32; под ним демка
    заливает экран цветом SEA, это вода."""
    c = Canvas(256, 32)

    def crest(x):
        return int(round(17 + 2.5 * math.sin(x * math.pi / 64.0) + 1.2 * math.sin(x * math.pi / 16.0)))

    for x in range(256):
        top = crest(x)
        c.rect(x, top, x, 27, VIOLET)
        c.set(x, top, PLUM)
        # Кочки и тени травы, редкие цветы.
        if (x * 7 + top * 3) % 11 == 0:
            c.rect(x, top + 3 + (x % 5), x + 1, top + 3 + (x % 5), PLUM)
        if (x * 5 + top) % 37 == 0:
            c.set(x, top + 4 + (x % 3), GOLD if x % 2 else WHITE)
        # Берег и вода с бликами.
        c.set(x, 27, PLUM)
        c.rect(x, 28, x, 31, SEA)
        if (x // 5 + (x // 16)) % 3 == 0:
            c.set(x, 29 + (x // 5) % 2 * 2, AQUA)
        if x % 23 in (3, 4):
            c.rect(x, 25, x, 27, PLUM)
    for x, kind, h in ((10, 1, 11), (27, 0, 13), (35, 0, 10), (58, 1, 13), (84, 0, 12), (100, 1, 10),
                       (120, 0, 14), (129, 0, 10), (151, 1, 12), (176, 0, 11), (197, 1, 14), (214, 0, 13),
                       (223, 0, 9), (243, 1, 10)):
        gy = crest(x) + 1
        h = min(h, gy - 1)
        if kind:
            _oak(c, x, gy, h)
        else:
            _fir(c, x, gy, h)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: рыцарь платформера, стражник, вещи, кладка, три
    слоя дали."""
    return {
        "enemy_walk": strip([guard_side(p) for p in base.phases()]),
        "enemy_front": strip([guard_front(p) for p in base.phases()]),
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
        "hero_run": strip([knight_side(p) for p in base.phases()]),
        "hero_jump": knight_side(0.0, jump=True),
        "hero_leap": strip([knight_leap(i) for i in range(4)]),
        "hero_idle": strip([knight_idle(i) for i in range(2)]),
        "hero_back": strip([knight_back(p) for p in base.phases()]),
        "hero_slide": strip([knight_slide(i) for i in range(2)]),
        "hero_hang": strip([knight_hang(i) for i in range(2)]),
        "hero_crouch": strip([knight_crouch(i) for i in range(2)]),
    }


def extras():
    """Ленты, без которых демки набора берут пиратские: летун и ползун тропы, ключ, зелье и
    снаряд шутера."""
    return {
        "parrot_fly": strip([bat(i) for i in range(4)]),
        "crab_walk": strip([boar(i) for i in range(4)]),
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


def save_sheet(path, items, scale=3, pad=6, back=(0x5E, 0x78, 0x8E, 255), max_w=640):
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
    """Лист набора: лента на строку, как в игре, после светотени; `keys` оставляет нужные."""
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
