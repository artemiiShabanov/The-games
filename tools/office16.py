#!/usr/bin/env python3
"""Набор «Офис» для 16/32-bit (основа, зеркало `space16.py` и `castles16.py`): сатира про контору,
ровный свет ламп, серо-бежевые стены и ковролин, яркие акценты стикеров (жёлтый, розовый,
бирюзовый). Герой это клерк: белая рубашка с закатанными рукавами, красный галстук-флажок,
тёмно-синие брюки, коричневые туфли, очки, аккуратный пробор, бейдж на поясе. Враг это сотрудник в
сером костюме с папкой под мышкой, без лица, одинаковый как клон. Те же ленты, размеры и число
кадров, что у космоса, пиратов и замков (`castles16.sprites()`); позы и точка опоры ног героя
повторяют прежних кадр в кадр, чтобы хитбоксы демок сходились: меняется рисунок, не геометрия.

Слоты и их офисные замки: космонавт это клерк, пришелец это клон в сером костюме, кристалл это
жетон на кофе, флаг экспедиции это стикер на подставке, грузовая капсула это сейф, метеорит это
коробка с бумагой, настил станции это ковролин над плитой перекрытия с кабелями. Ленты, которых
нет в `sprites()` (бумажный самолётик вместо попугая-дрона, робот-пылесос вместо краба, ключ-карта,
стакан кофе вместо аптечки, скрепка вместо снаряда), лежат в `extras()` тех же размеров. Слои
дали: окна во всю стену с городом, ряды перегородок опенспейса с мониторами, фикусы, кулеры и
вешалки.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `office_*16.py` берут цвета
по роли): K обводка, NAVY брюки и глубокая тень, SEA ковролин и перегородки, AQUA бирюзовый
стикер и листва фикуса, SKY стекло и блики, WHITE рубашка и бумага, GREY беж стен и тень белого,
SKIN кожа, TAN коричневые туфли, дерево и картон, GOLD и BRASS жёлтый стикер и жетон, METAL серый
костюм и сталь, DARK графит, волосы и подошвы, RED галстук, VIOLET и PLUM розовый стикер.

    python3 tools/office16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/office16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Офис»: 16 цветов, индекс это та же роль, что у пиратов, космоса и замков.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x17, 0x15, 0x1E),  # K      обводка
    (0x33, 0x4C, 0x9C),  # NAVY   тёмно-синие брюки, глубокая тень
    (0x7A, 0x8C, 0xA6),  # SEA    серо-синий ковролин, перегородки
    (0x2E, 0xC4, 0xBE),  # AQUA   бирюзовый стикер, листва фикуса
    (0xCF, 0xE6, 0xF2),  # SKY    стекло, блики, небо за окном
    (0xF6, 0xF3, 0xEA),  # WHITE  рубашка, бумага
    (0xC8, 0xC3, 0xB4),  # GREY   беж стен, тень белого
    (0xF2, 0xC8, 0x9A),  # SKIN   кожа
    (0xA2, 0x66, 0x3E),  # TAN    коричневые туфли, картон, дерево
    (0xFF, 0xD9, 0x3C),  # GOLD   жёлтый стикер, жетон
    (0xC9, 0x96, 0x1E),  # BRASS  тень жёлтого, картон
    (0x8E, 0x92, 0x9C),  # METAL  серый костюм, сталь
    (0x3A, 0x3D, 0x4A),  # DARK   графит, волосы, подошвы
    (0xD8, 0x2E, 0x3A),  # RED    галстук
    (0xF2, 0x7A, 0xB6),  # VIOLET розовый стикер
    (0xA2, 0x3C, 0x78),  # PLUM   тень розового
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: PLUM, VIOLET: PLUM}
# Материалы для светотени рампами: ткань рубашки и бумага, брюки, кожа, картон и кожа обуви,
# жёлтое, серый костюм и сталь, графит, красное, розовое, бирюза.
GROUPS = {WHITE: "paper", GREY: "paper", SKY: "glass", NAVY: "trousers", SEA: "carpet", AQUA: "teal",
          SKIN: "skin", TAN: "leather", GOLD: "yellow", BRASS: "yellow", METAL: "suit", DARK: "graphite",
          RED: "red", VIOLET: "pink", PLUM: "pink"}


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
# Силуэт узкий, без головного убора: голова с тёмной причёской на тонкой шее, белая рубашка, красный
# галстук-флажок (в беге развевается назад, на месте висит), тёмно-синие брюки, коричневые туфли.
# Позы и габариты те же, что у рыцаря и космонавта, но фигура уже на пиксель-два.

def _head(c, x, y, face=1):
    """Голова лицом вправо при `face` 1: овал лица, тёмные волосы с пробором, очки (две линзы-блика
    под тонкой оправой, дужка к уху), нос, ухо. Центр (x, y), шея до y+6."""
    f = face
    c.rect(x - 1, y + 4, x + 1, y + 6, SKIN)
    c.ellipse(x + 0.5 * f, y + 0.5, 4.2, 4.7, SKIN)
    # Волосы: невысокая шапка на макушке и затылке, лоб и висок открыты.
    c.ellipse(x - 0.8 * f, y - 2.2, 4.8, 2.7, DARK)
    a, b = sorted((x - 5 * f, x - 3 * f))
    c.rect(a, y - 2, b, y + 0, DARK)
    c.set(x + 3 * f, y - 3, DARK)
    # Пробор: светлая линия на темени.
    c.set(x + 1 * f, y - 4, METAL)
    c.set(x + 2 * f, y - 4, METAL)
    c.set(x + 1 * f, y - 3, SKIN)
    # Очки: тонкая оправа над линзами, мостик, дужка к уху.
    a, b = sorted((x - 1 * f, x + 5 * f))
    c.rect(a, y - 1, b, y - 1, K)
    for dx in (0, 1, 3, 4):
        c.set(x + dx * f, y, SKY)
        c.set(x + dx * f, y + 1, SKY if dx in (0, 3) else WHITE)
    c.set(x + 2 * f, y, K)
    c.set(x + 5 * f, y, K)
    a, b = sorted((x - 3 * f, x - 1 * f))
    c.rect(a, y - 1, b, y - 1, K)
    c.set(x + 5 * f, y + 2, SKIN)
    c.set(x + 4 * f, y + 3, TAN)
    c.set(x - 2 * f, y + 1, TAN)


def _tie_fly(c, x, y, phase, face=1, length=10, lift=0.0):
    """Галстук-флажок: узел на груди и полотнище, летящее назад за плечо волной."""
    f = face
    c.rect(x, y, x + 1 * f, y + 1, RED)
    px, py = x, y + 1
    for k in range(1, length + 1):
        nx = x - k * f
        ny = y + 1 + math.sin(phase + k * 0.55) * 1.3 - lift * k * 0.18
        c.line(px, py, nx, ny, RED, 2 if k < length - 2 else 3)
        px, py = nx, ny
    c.poly([(px, py - 2), (px - 3 * f, py + 0.5), (px, py + 2.5)], RED)


def _tie_hang(c, x, y0, y1, sway=0):
    """Галстук висит: узел, клин книзу с острым концом, качается на `sway` пикселей."""
    c.rect(x, y0, x + 1, y0 + 1, RED)
    c.poly([(x - 1 + sway, y0 + 2), (x + 2 + sway, y0 + 2), (x + 3 + sway, y1 - 2), (x + 0.5 + sway, y1 + 1),
            (x - 2 + sway, y1 - 2)], RED)


def _shirt(c, x0, y0, x1, y1, badge=True, front=1):
    """Рубашка от плеч до пояса: белая, тень у спины, воротник, тёмный ремень с бляхой и бейдж на
    ремне у переднего края (светлая карточка с бирюзовой шапкой)."""
    c.rect(x0, y0, x1, y1, WHITE)
    if front > 0:
        c.rect(x0, y0 + 1, x0 + 1, y1 - 2, GREY)
        c.rect(x1 - 1, y0, x1, y0 + 1, GREY)
        c.rect(x1 - 2, y0 - 1, x1 + 0, y0, SKIN)
        c.set(x1 - 3, y0, GREY)
        c.set(x1 - 3, y0 + 1, GREY)
    c.rect(x0, y1 - 1, x1, y1, DARK)
    if badge:
        bx = x1 - 1 if front > 0 else x0 + 1
        c.rect(bx - 1, y1 + 1, bx + 1, y1 + 4, WHITE)
        c.rect(bx - 1, y1 + 1, bx + 1, y1 + 1, AQUA)
        c.set(bx, y1 + 3, METAL)
        c.set(bx - 1, y1 - 1, GOLD)


def _shoe(c, x, y, face=1):
    """Коричневая туфля с острым носком и тёмной подошвой; носок смотрит по `face`."""
    f = face
    a, b = sorted((x - 1 * f, x + 3 * f))
    c.rect(a, y - 1, b, y, TAN)
    a, b = sorted((x - 1 * f, x + 4 * f))
    c.rect(a, y + 1, b, y + 1, DARK)
    c.set(x + 3 * f, y - 1, SKIN if False else TAN)
    c.set(x + 3 * f, y - 1, GOLD if False else TAN)


def _leg(c, hip, knee, foot, col, face=1):
    c.line(hip[0], hip[1], knee[0], knee[1], col, 3)
    c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
    _shoe(c, foot[0], foot[1], face)


def _arm(c, x0, y0, x1, y1, near=True):
    """Рука с закатанным рукавом: короткий белый рукав, на сгибе светлая манжета, ниже голое
    предплечье и кисть. Дальняя рука темнее."""
    ex, ey = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.5
    c.line(x0, y0, ex, ey, WHITE if near else GREY, 3)
    c.line(ex, ey, x1, y1, SKIN if near else TAN, 2)
    c.set(x1, y1 + 1, SKIN if near else TAN)
    c.set(ex, ey, GREY if near else METAL)


def clerk_side(phase, jump=False):
    """Клерк сбоку, лицом вправо: бег по фазе 0..2π или прыжок; галстук летит назад."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), near=False)
    for sign, col in ((-1, NAVY), (1, NAVY)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        _leg(c, (15 + sign * 0.5, hip_y), knee, foot, col)
    _shirt(c, 12, 13 - bob, 18, hip_y)
    _tie_fly(c, 17, 14 - bob, phase, length=9, lift=3.0 if jump else 0.0)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0))
    _head(c, 16, 7 - bob)
    return c.finish()


def clerk_back(phase):
    """Со спины: бежит вглубь экрана, белая спина с швом, затылок с причёской, уши, закатанные
    рукава; галстука не видно."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 1, 21 - bob, x + 1, 28 - lift, NAVY)
        _shoe(c, x - 1, 29 - lift, 1)
        c.rect(x - 1, 29 - lift, x + 1, 29 - lift, TAN)
        _arm(c, 16 + sign * 5, 15 - bob, 16 + sign * 6, 20 - bob + s * sign * 2, near=sign > 0)
    c.rect(12, 13 - bob, 19, 21 - bob, WHITE)
    c.rect(12, 13 - bob, 13, 20 - bob, GREY)
    c.rect(15, 15 - bob, 16, 20 - bob, GREY)
    c.rect(12, 20 - bob, 19, 21 - bob, DARK)
    c.set(15, 21 - bob, GOLD)
    c.rect(14, 11 - bob, 17, 13 - bob, SKIN)
    c.ellipse(15.5, 7.5 - bob, 4.3, 4.8, DARK)
    c.set(11, 8 - bob, SKIN)
    c.set(20, 8 - bob, SKIN)
    c.set(11, 9 - bob, TAN)
    c.set(20, 9 - bob, TAN)
    c.rect(13, 3 - bob, 16, 3 - bob, METAL)
    c.rect(14, 4 - bob, 14, 5 - bob, METAL)
    c.rect(13, 11 - bob, 18, 11 - bob, DARK)
    return c.finish()


def clerk_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, near=False)
    for sign, col in ((-1, NAVY), (1, NAVY)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        _leg(c, (15 + sign * 0.5, hip_y), knee, foot, col)
    _shirt(c, 12, 13 + crouch, 18, hip_y)
    _tie_fly(c, 17, 14 + crouch, i * 1.3, length=8, lift=(1.0, 3.0, 1.0, -1.0)[i])
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch)
    _head(c, 16, 7 + crouch)
    return c.finish()


def clerk_idle(i):
    """Стойка: два кадра, клерк дышит, галстук чуть качается."""
    c = Canvas()
    up = i
    for sign, col in ((-1, NAVY), (1, NAVY)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, col)
        _shoe(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, near=False)
    _shirt(c, 12, 13 - up, 18, 21)
    _tie_hang(c, 16, 14 - up, 20 - up, sway=i)
    _arm(c, 16, 15 - up, 17, 21 - up)
    _head(c, 16, 7 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; белая рубашка, тёмный
    ремень у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = DARK if k >= int(n) - 1 else WHITE
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def clerk_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх,
    рука сзади на земле, галстук летит назад. Макушка на 15-й строке. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, DARK, 3)
    c.line(24, 23 - i, 27, 27, DARK, 3)
    _shoe(c, 26, 27)
    c.line(13, 24, 19, 23, WHITE, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 27, 28, NAVY, 3)
    c.line(20, 27, 26, 27, METAL, 1)
    c.rect(27, 26, 30, 29, TAN)
    c.rect(27, 29, 31, 29, DARK)
    c.rect(28, 25, 28, 25, TAN)
    _arm(c, 11, 25, 6, 29, near=True)
    _tie_fly(c, 12, 22, 0.8 + i * 1.5, length=6, lift=-1.0)
    _head(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def clerk_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    _arm(c, 15, 24, 19, 26, near=False)
    for sign, col in ((-1, NAVY), (1, NAVY)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
        _shoe(c, foot[0], foot[1])
    _shirt(c, 12, 22, 18, 26, badge=False)
    _tie_hang(c, 16, 23, 25)
    _arm(c, 14, 24, 19, 26)
    _head(c, 16, 19)
    return c.finish()


def clerk_hang(i):
    """На тросе: руки вверх к точке хвата, ноги свисают и качаются, галстук болтается."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, GREY, 3)
    c.line(14, 8, 15, 4, SKIN, 2)
    c.line(18, 13, 17, 1, WHITE, 2)
    c.line(17, 6, 17, 2, SKIN, 2)
    c.rect(11, 0, 21, 0, METAL)
    c.ellipse(15, 1, 1.2, 1.2, SKIN)
    c.ellipse(17, 1, 1.2, 1.2, SKIN)
    _shirt(c, 12, 13, 19, 21, badge=False)
    _tie_hang(c, 18, 14, 20, sway=sw)
    for sign, col in ((-1, NAVY), (1, NAVY)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], col, 3)
        _shoe(c, foot[0], foot[1])
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Сотрудник в сером костюме -----------------------------------------------------------------
# Клон из отдела согласований: серый костюм с белым клином рубашки и тёмным галстуком, папка под
# мышкой, голова гладкая, без лица, только две линзы очков бликуют. Шаг и рост повторяют пришельца.

def _blank_head(c, x, y, face=-1):
    """Безликая голова: гладкий овал кожи, аккуратная причёска, две линзы-блика без глаз, ни носа,
    ни рта. Центр (x, y), шея до y+6."""
    f = face
    c.rect(x - 1, y + 4, x + 1, y + 6, SKIN)
    c.ellipse(x, y + 0.5, 4.3, 4.7, SKIN)
    c.ellipse(x - 0.5 * f, y - 2.4, 4.4, 2.3, DARK)
    c.rect(x - 2, y - 4, x + 1, y - 4, METAL)
    for lx in (x + 3 * f, x + 2 * f, x - 1 * f, x - 2 * f):
        c.set(lx, y, WHITE)
        c.set(lx, y + 1, SKY)
    a, b = sorted((x - 3 * f, x + 4 * f))
    c.rect(a, y - 1, b, y - 1, K)
    c.set(x + 0 * f, y, K)


def _suit_legs(c, hx, hy, specs):
    for hip, knee, foot, col in specs:
        c.line(hip[0], hip[1], knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 2)
        a, b = sorted((foot[0] - 3, foot[0] + 1))
        c.rect(foot[0] - 3, foot[1], foot[0] + 1, foot[1] + 1, NAVY)
        c.set(foot[0] - 3, foot[1], METAL)


def clone_side(phase):
    """Клон сбоку, лицом влево (навстречу герою): шаг по фазе, папка под ближней рукой."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign, col in ((-1, DARK), (1, METAL)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
        c.rect(foot[0] - 3, foot[1] - 1, foot[0] + 1, foot[1], DARK)
        c.rect(foot[0] - 3, foot[1] + 1, foot[0] + 1, foot[1] + 1, NAVY)
    # Пиджак, клин рубашки спереди, тёмный галстук, нижний край и пуговица.
    c.rect(12, 12 - bob, 19, 23 - bob, METAL)
    c.rect(18, 12 - bob, 19, 23 - bob, DARK)
    c.poly([(12, 12 - bob), (15, 12 - bob), (13, 17 - bob), (12, 15 - bob)], WHITE)
    c.rect(13, 13 - bob, 14, 19 - bob, DARK)
    c.rect(12, 23 - bob, 19, 23 - bob, DARK)
    c.set(15, 20 - bob, DARK)
    # Задняя рука вдоль тела, ближняя прижимает папку.
    c.line(17, 14 - bob, 18 + 2 * s, 21 - bob, DARK, 2)
    c.rect(8, 15 - bob, 14, 21 - bob, GOLD)
    c.rect(8, 15 - bob, 14, 15 - bob, BRASS)
    c.rect(9, 17 - bob, 12, 17 - bob, WHITE)
    c.rect(9, 19 - bob, 11, 19 - bob, BRASS)
    c.line(15, 14 - bob, 12, 19 - bob, METAL, 3)
    c.set(11, 20 - bob, SKIN)
    c.set(11, 19 - bob, SKIN)
    _blank_head(c, 15, 6 - bob, -1)
    return c.finish()


def clone_front(phase):
    """Клон лицом к камере: идёт на игрока, ноги по очереди, папка под левой рукой."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, METAL if sign > 0 else DARK, 3)
        c.rect(x - 2, 28 - lift, x + 1, 28 - lift, DARK)
        c.rect(x - 2, 29 - lift, x + 2, 29 - lift, NAVY)
    c.rect(11, 12 - bob, 20, 23 - bob, METAL)
    c.rect(19, 12 - bob, 20, 23 - bob, DARK)
    c.poly([(14, 12 - bob), (17, 12 - bob), (15.5, 19 - bob)], WHITE)
    c.rect(15, 14 - bob, 16, 20 - bob, DARK)
    c.rect(11, 23 - bob, 20, 23 - bob, DARK)
    c.rect(16, 21 - bob, 16, 21 - bob, DARK)
    # Папка под левой рукой (справа на кадре) и опущенная правая.
    c.rect(21, 15 - bob, 25, 24 - bob, GOLD)
    c.rect(21, 15 - bob, 25, 15 - bob, BRASS)
    c.rect(22, 18 - bob, 24, 18 - bob, WHITE)
    c.rect(22, 21 - bob, 23, 21 - bob, BRASS)
    c.line(19, 14 - bob, 21, 20 - bob, METAL, 3)
    c.set(21, 21 - bob, SKIN)
    c.line(11, 14 - bob, 9, 20 - bob + s * 2, DARK, 2)
    c.set(9, 21 - bob + s * 2, SKIN)
    _blank_head(c, 15.5, 6 - bob, 1)
    return c.finish()


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Жетон на кофе вращается: шесть кадров, ширина по косинусу, ребро темнее; на лицевой
    стороне чашка с парком."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 7.0)
    cx = 15.5
    c.ellipse(cx, 16, rx, 10.5, BRASS)
    if rx > 2:
        c.ellipse(cx, 16, rx - 1.3, 9.2, GOLD)
    if rx > 3:
        k = rx / 7.0
        # Чашка: трапеция, ручка, блюдце и два завитка пара.
        c.poly([(cx - 4 * k, 15), (cx + 3 * k, 15), (cx + 2 * k, 21), (cx - 3 * k, 21)], BRASS)
        c.rect(cx - 4 * k, 15, cx + 3 * k, 15, DARK)
        c.rect(cx - 4 * k, 22, cx + 3 * k, 22, BRASS)
        c.line(cx + 3.5 * k, 16, cx + 5 * k, 18, BRASS, 1)
        c.line(cx - 2 * k, 13, cx - 1 * k, 10, WHITE, 1)
        c.line(cx + 1 * k, 13, cx + 2 * k, 10, WHITE, 1)
        c.line(cx - 4.5 * k, 9, cx - 2.5 * k, 8, WHITE, 1)
    return c.finish()


def flag(i):
    """Флажок-стикер на подставке: тёмная утяжелённая основа, тонкая стойка, жёлтый листок с
    клеевой полоской, строчками-штрихами и галочкой идёт волной; нижний угол слегка загнут."""
    c = Canvas()
    c.ellipse(5.5, 30, 5, 1.6, DARK)
    c.rect(5, 3, 6, 29, METAL)
    c.rect(5, 3, 5, 29, SKY)
    c.rect(4, 2, 7, 3, DARK)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        bottom.append((x, 21 + w))
    c.poly(top + bottom[::-1], GOLD)
    c.shade()
    c.outline()
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        c.set(x, 5 + w, BRASS)
        c.set(x, 6 + w, BRASS)
    # Строчки-штрихи: три разной длины, красная галочка в углу.
    for k, (y, a, b) in enumerate(((9, 11, 25), (12, 11, 22), (15, 11, 24))):
        for x in range(a, b + 1):
            w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
            if (x + k) % 5 != 4:
                c.set(x, y + w, DARK)
    mid = math.sin(24 * 0.45 - i * math.pi / 3.0) * 1.2
    c.line(21, 18 + mid, 22, 19 + mid, RED, 1)
    c.line(22, 19 + mid, 25, 16 + mid, RED, 1)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    return c.finish()


def _cables(c):
    """Слой под ковром: бетонная плита и три кабеля вдоль, с хомутами; период 32 по x."""
    for y in range(7, 32):
        for x in range(32):
            col = METAL
            if (x * 7 + y * 13) % 17 == 0:
                col = GREY
            elif (x * 5 + y * 11) % 19 == 0:
                col = DARK
            c.set(x, y, col)
    c.rect(0, 7, 31, 7, DARK)
    c.rect(0, 8, 31, 8, GREY)
    c.rect(0, 29, 31, 29, DARK)
    c.rect(0, 30, 31, 31, NAVY)
    for y0, col, hi in ((12, RED, VIOLET), (17, AQUA, SKY), (23, GOLD, WHITE)):
        for x in range(32):
            w = int(round(math.sin(x * math.pi / 16.0 + y0) * 1.0))
            c.rect(x, y0 + w, x, y0 + w + 2, col)
            c.set(x, y0 + w - 1, DARK)
            c.set(x, y0 + w + 3, DARK)
            c.set(x, y0 + w, hi)
    # Хомуты: тёмные стяжки через пучок.
    for x in (6, 22):
        c.rect(x, 10, x + 1, 28, DARK)
        c.set(x, 11, GREY)
        c.set(x, 21, GREY)


def ground(inner=False):
    """Серо-синий ковролин сверху (ворс точками, светлая кромка), ниже плита перекрытия с
    пучками кабелей; в `inner` ковра нет, только плита."""
    c = Canvas()
    _cables(c)
    if inner:
        c.rect(0, 0, 31, 6, METAL)
        for y in range(0, 7):
            for x in range(32):
                if (x * 7 + y * 13) % 17 == 0:
                    c.set(x, y, GREY)
                elif (x * 5 + y * 11) % 19 == 0:
                    c.set(x, y, DARK)
        c.rect(0, 6, 31, 6, DARK)
        return c
    c.rect(0, 0, 31, 6, SEA)
    for x in range(32):
        c.set(x, 0, SKY if (x * 3) % 5 < 3 else SEA)
        c.set(x, 1, SEA)
        if (x * 7) % 4 == 0:
            c.set(x, 2, METAL)
        if (x * 5 + 2) % 6 == 0:
            c.set(x, 3, SKY)
        if (x * 3 + 1) % 5 == 0:
            c.set(x, 4, METAL)
        c.set(x, 5, NAVY if (x + 1) % 3 else METAL)
        c.set(x, 6, DARK)
    # Шов между плитками ковра.
    c.rect(15, 1, 15, 5, METAL)
    return c


def rock():
    """Коробка с бумагой: картонный ящик с лентой, наклейкой-стикером и торчащей стопкой листов."""
    c = Canvas()
    # Стопка листов над коробкой, лист чуть набок.
    c.poly([(8, 9), (23, 6), (25, 11), (10, 13)], WHITE)
    c.poly([(7, 5), (20, 4), (21, 9), (8, 10)], WHITE)
    c.line(9, 7, 17, 6, METAL, 1)
    c.line(10, 8, 18, 7, METAL, 1)
    c.line(9, 12, 22, 9, GREY, 1)
    # Верхняя грань, лицевая и правая.
    c.poly([(3, 14), (8, 9), (30, 9), (27, 14)], BRASS)
    c.rect(3, 14, 27, 28, TAN)
    c.poly([(27, 14), (30, 9), (30, 23), (27, 28)], DARK)
    c.rect(13, 14, 17, 28, GREY)
    c.rect(13, 14, 17, 14, WHITE)
    c.rect(4, 15, 26, 15, BRASS)
    # Стикер и строчки на лицевой стороне.
    c.rect(19, 19, 25, 24, VIOLET)
    c.rect(19, 19, 25, 19, PLUM)
    c.rect(20, 21, 24, 21, WHITE)
    c.rect(20, 23, 23, 23, WHITE)
    c.rect(4, 25, 11, 25, BRASS)
    c.rect(4, 27, 9, 27, BRASS)
    return c.finish()


def chest():
    """Сейф: графитовый короб с дверцей, поворотным кодовым диском, панелью с бирюзовым экраном и
    розовым стикером с паролем на углу."""
    c = Canvas()
    c.rect(3, 4, 28, 27, DARK)
    c.rect(5, 6, 26, 25, METAL)
    c.rect(5, 6, 26, 6, GREY)
    c.rect(5, 6, 5, 25, GREY)
    c.rect(24, 6, 26, 25, DARK)
    # Диск: кольцо, шкала по кругу, ручка из трёх спиц.
    c.ellipse(13.5, 16, 6.5, 6.5, DARK)
    c.ellipse(13.5, 16, 5.2, 5.2, GREY)
    c.ellipse(13.5, 16, 3.2, 3.2, METAL)
    for a in range(0, 360, 60):
        c.line(13.5, 16, 13.5 + 5 * math.cos(math.radians(a + 30)), 16 + 5 * math.sin(math.radians(a + 30)), DARK, 1)
    c.ellipse(13.5, 16, 1.6, 1.6, GOLD)
    # Панель с экраном и кнопками.
    c.rect(20, 10, 25, 13, DARK)
    c.rect(21, 11, 24, 12, AQUA)
    for x in (20, 22, 24):
        c.set(x, 16, WHITE)
        c.set(x, 18, WHITE)
        c.set(x, 20, WHITE)
    # Петли слева, ножки, стикер.
    c.rect(2, 9, 3, 11, DARK)
    c.rect(2, 20, 3, 22, DARK)
    c.rect(4, 28, 8, 29, DARK)
    c.rect(23, 28, 27, 29, DARK)
    c.rect(22, 22, 27, 26, VIOLET)
    c.rect(22, 22, 27, 22, PLUM)
    c.rect(23, 24, 26, 24, DARK)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали: окна с городом, перегородки опенспейса, комнатные растения и мебель. Все ленты
# 256 по ширине, рисунок периодический (период делит 256), стыкуются по краям. Низ слоёв сплошной.

def _wrap_rect(c, x0, y0, x1, y1, col):
    for k in (0, 256, -256):
        c.rect(x0 + k, y0, x1 + k, y1, col)


def _wrap_ellipse(c, cx, cy, rx, ry, col):
    for k in (0, 256, -256):
        c.ellipse(cx + k, cy, rx, ry, col)


def par_sky():
    """Дальний слой: окна во всю стену, за стеклом город с офисными башнями и редкими облаками,
    стойки каждые 64 пикселя, подоконник внизу; лента 256×48, стыкуется по краям."""
    c = Canvas(256, 48)
    c.rect(0, 0, 255, 47, SKY)
    for y in range(26, 44):
        if (y - 26) % 3 == 0:
            c.rect(0, y, 255, y, WHITE)
    for cx, cy, rx in ((40, 10, 14), (150, 7, 18), (226, 13, 12)):
        _wrap_ellipse(c, cx, cy, rx, 2.5, WHITE)
        _wrap_ellipse(c, cx + 4, cy - 2, rx * 0.55, 2.2, WHITE)
    # Далёкий ряд: низкие башни в дымке.
    for x0, w, h in ((4, 14, 18), (22, 10, 24), (36, 16, 15), (60, 12, 22), (84, 18, 17), (110, 10, 26),
                     (124, 14, 19), (148, 12, 23), (164, 16, 16), (188, 10, 25), (202, 14, 18), (226, 18, 21)):
        _wrap_rect(c, x0, 44 - h, x0 + w - 1, 44, GREY)
        _wrap_rect(c, x0, 44 - h, x0, 44, WHITE)
    # Ближний ряд: тёмные башни с рядами горящих окон, одна с антенной.
    for x0, w, h, ant in ((12, 18, 26, False), (46, 14, 31, True), (70, 20, 22, False), (100, 16, 29, False),
                          (134, 20, 33, True), (170, 14, 24, False), (194, 18, 30, False), (232, 16, 27, True)):
        _wrap_rect(c, x0, 44 - h, x0 + w - 1, 44, SEA)
        _wrap_rect(c, x0, 44 - h, x0 + 1, 44, METAL)
        _wrap_rect(c, x0 + w - 2, 44 - h, x0 + w - 1, 44, NAVY)
        if ant:
            _wrap_rect(c, x0 + w // 2, 44 - h - 6, x0 + w // 2, 44 - h, METAL)
            _wrap_rect(c, x0 + w // 2, 44 - h - 7, x0 + w // 2, 44 - h - 7, RED)
        for wy in range(44 - h + 3, 42, 4):
            for wx in range(x0 + 3, x0 + w - 3, 4):
                lit = ((wx * 3 + wy * 7) // 2) % 5
                for k in (0, 256, -256):
                    c.set(wx + k, wy, GOLD if lit == 0 else (SKY if lit < 3 else NAVY))
                    c.set(wx + k + 1, wy, GOLD if lit == 0 else (SKY if lit < 3 else NAVY))
    # Рама: стойки через 64, горизонтальная перекладина вверху и подоконник.
    for x0 in (0, 64, 128, 192):
        c.rect(x0, 0, x0 + 2, 47, GREY)
        c.rect(x0, 0, x0, 47, WHITE)
        c.rect(x0 + 3, 0, x0 + 3, 47, METAL)
    c.rect(0, 0, 255, 1, GREY)
    c.rect(0, 2, 255, 2, METAL)
    c.rect(0, 44, 255, 44, METAL)
    c.rect(0, 45, 255, 45, GREY)
    c.rect(0, 46, 255, 47, SEA)
    # Блик по стеклу: косые полосы.
    for x0 in (20, 84, 148, 212):
        for k in range(10):
            c.set(x0 + k, 6 + k, WHITE)
            c.set(x0 + k + 3, 6 + k, WHITE)
    return c


def _monitor(c, x, y, kind):
    """Монитор на подставке 12×10: графитовая рамка, экран с графиком, текстом или пустой."""
    c.rect(x, y, x + 11, y + 8, DARK)
    c.rect(x + 1, y + 1, x + 10, y + 7, SKY if kind != 2 else NAVY)
    if kind == 0:
        for i, h in enumerate((2, 4, 3, 5)):
            c.rect(x + 2 + i * 2, y + 7 - h, x + 3 + i * 2, y + 7, AQUA if i % 2 == 0 else RED)
    elif kind == 1:
        for yy in (2, 4, 6):
            c.rect(x + 2, y + yy, x + 9 - (yy % 3) * 2, y + yy, METAL)
    else:
        c.rect(x + 2, y + 2, x + 9, y + 2, AQUA)
        c.rect(x + 2, y + 4, x + 6, y + 4, AQUA)
        c.set(x + 8, y + 4, WHITE)
    c.rect(x + 5, y + 9, x + 6, y + 10, DARK)
    c.rect(x + 3, y + 11, x + 8, y + 11, DARK)


def par_far():
    """Средний слой: ряд перегородок опенспейса с мониторами, столами, стикерами и спинками
    кресел, лента 256×48, период 32, над перегородками пусто, низ сплошной."""
    c = Canvas(256, 48)
    tops = (13, 9, 15, 11, 14, 8, 16, 10)
    kinds = (0, 1, 2, 1, 0, 2, 1, 0)
    for u in range(8):
        x0 = u * 32
        top = tops[u]
        c.rect(x0, top, x0 + 31, 47, SEA)
        c.rect(x0, top, x0 + 31, top, GREY)
        c.rect(x0, top + 1, x0 + 31, top + 1, METAL)
        c.rect(x0, top + 2, x0 + 1, 47, METAL)
        c.rect(x0, top + 2, x0, 47, GREY)
        c.rect(x0 + 2, top + 2, x0 + 2, 47, NAVY)
        # Стикеры на перегородке: жёлтые, розовый, бирюзовый.
        c.rect(x0 + 5, top + 4, x0 + 8, top + 7, GOLD if u % 2 == 0 else AQUA)
        c.rect(x0 + 5, top + 4, x0 + 8, top + 4, BRASS if u % 2 == 0 else SEA)
        c.rect(x0 + 23, top + 6, x0 + 26, top + 9, VIOLET if u % 3 else GOLD)
        c.rect(x0 + 23, top + 6, x0 + 26, top + 6, PLUM if u % 3 else BRASS)
        if u % 2 == 1:
            c.rect(x0 + 10, top + 4, x0 + 12, top + 6, GOLD)
        # Монитор, стол, тёмный низ под столом и спинка кресла.
        _monitor(c, x0 + 10 + (u % 3), 22 + (u % 2), kinds[u])
        c.rect(x0 + 3, 35, x0 + 31, 36, TAN)
        c.rect(x0 + 3, 35, x0 + 31, 35, SKIN)
        c.rect(x0 + 3, 37, x0 + 31, 47, NAVY)
        c.rect(x0 + 8 + (u % 3) * 3, 33, x0 + 13 + (u % 3) * 3, 34, WHITE)
        c.rect(x0 + 17, 40, x0 + 24, 47, DARK)
        c.ellipse(x0 + 20.5, 40, 4.5, 2.5, DARK)
        c.rect(x0 + 17, 40, x0 + 24, 40, METAL)
        if u % 4 == 2:
            c.rect(x0 + 27, 31, x0 + 29, 34, WHITE)
            c.rect(x0 + 27, 31, x0 + 29, 31, SKY)
    return c


def _ficus(c, x, base, h):
    """Фикус в белом горшке: тонкие стволы и круглая листва бирюзой с тенью и бликами."""
    c.rect(x - 4, base - 6, x + 4, base, WHITE)
    c.rect(x - 4, base - 6, x + 4, base - 6, GREY)
    c.rect(x + 2, base - 5, x + 4, base, GREY)
    c.rect(x - 3, base - 6, x + 3, base - 5, DARK)
    c.rect(x - 1, base - h, x, base - 6, TAN)
    for dx, dy, r in ((-4, 5, 4.6), (4, 4, 4.4), (0, 0, 5.4), (-2, 8, 3.6), (4, 9, 3.5)):
        cy = base - h + dy
        _wrap_ellipse(c, x + dx - 0.5, cy, r, r * 0.9, NAVY)
        _wrap_ellipse(c, x + dx - 0.5, cy - 0.8, r - 0.8, (r - 0.8) * 0.9, AQUA)
        _wrap_ellipse(c, x + dx - 1.5, cy - 2, 1.6, 1.0, SKY)


def _cooler(c, x, base):
    """Кулер с бутылью: белый корпус с тенью, голубая бутыль, два краника, поддон."""
    c.rect(x - 4, base - 15, x + 4, base, WHITE)
    c.rect(x + 2, base - 15, x + 4, base, GREY)
    c.rect(x - 4, base - 15, x + 4, base - 15, GREY)
    c.ellipse(x, base - 21, 4.8, 6, SKY)
    c.ellipse(x - 1.5, base - 23, 1.4, 2.4, WHITE)
    c.rect(x - 4, base - 16, x + 4, base - 16, METAL)
    c.rect(x - 3, base - 11, x - 1, base - 10, AQUA)
    c.rect(x + 1, base - 11, x + 3, base - 10, RED)
    c.rect(x - 3, base - 7, x + 3, base - 6, DARK)
    c.rect(x - 4, base - 3, x + 4, base - 2, METAL)
    c.rect(x - 4, base - 1, x + 4, base, DARK)


def _rack(c, x, base):
    """Вешалка: стойка на ножках, крючки, серый пиджак и красный шарф-галстук на них."""
    c.rect(x, base - 26, x + 1, base, DARK)
    c.line(x + 0.5, base, x - 4, base, DARK, 2)
    c.line(x + 0.5, base, x + 5, base, DARK, 2)
    c.line(x + 0.5, base - 26, x - 4, base - 23, DARK, 1)
    c.line(x + 0.5, base - 26, x + 5, base - 23, DARK, 1)
    c.poly([(x - 6, base - 22), (x - 2, base - 22), (x - 2, base - 11), (x - 6, base - 11)], METAL)
    c.rect(x - 6, base - 22, x - 6, base - 11, DARK)
    c.rect(x - 2, base - 21, x - 2, base - 12, GREY)
    c.rect(x + 3, base - 21, x + 4, base - 11, RED)
    c.rect(x + 3, base - 21, x + 3, base - 11, PLUM)
    c.rect(x + 3, base - 12, x + 4, base - 11, PLUM)


def par_mid():
    """Ближний слой: фикусы в горшках, кулеры и вешалки у плинтуса, лента 256×32, низ сплошной
    (ковёр с плинтусом)."""
    c = Canvas(256, 32)
    base = 26
    c.rect(0, base, 255, 31, SEA)
    c.rect(0, base, 255, base, GREY)
    c.rect(0, base + 1, 255, base + 1, METAL)
    for x in range(256):
        if (x * 7) % 9 == 0:
            c.set(x, base + 4, NAVY)
        if (x * 5) % 11 == 0:
            c.set(x, base + 3, METAL)
    for x, kind in ((24, 0), (60, 1), (104, 2), (150, 0), (190, 1), (222, 2)):
        if kind == 0:
            _ficus(c, x, base, 22)
        elif kind == 1:
            _cooler(c, x, base)
        else:
            _rack(c, x, base)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, клон в сером костюме, вещи,
    земля, три слоя дали. Ключи, размеры и число кадров те же, что у `castles16.sprites()`. Ленты
    демок лежат в модулях `office_*16.py`."""
    return {
        "enemy_walk": strip([clone_side(p) for p in base.phases()]),
        "enemy_front": strip([clone_front(p) for p in base.phases()]),
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


# --- Остальные слоты (ленты демок «тропа» и «до выхода» их берут) ------------------------------

def plane(i):
    """Бумажный самолётик (слот попугая) летит вправо: четыре кадра, крылья складываются вверх и
    вниз (вверх, середина, вниз, середина), тело по центру кадра. Без красной обводки опасности."""
    c = Canvas()
    w = (-6, -2, 4, -2)[i]
    # Дальнее крыло позади, ближнее впереди; ровный белый лист со складкой по килю.
    c.poly([(8, 17), (26, 17), (12, 17 + w * 1.6 - 1)], GREY)
    c.poly([(3, 15), (29, 18), (9, 21)], WHITE)
    c.poly([(9, 17), (27, 18.5), (13, 17 + w * 2.0 + 4)], WHITE)
    c.line(4, 15, 29, 18, METAL, 1)
    c.line(9, 19, 27, 18, GREY, 1)
    # Строчки печатного текста на крыле и красная печать.
    c.line(12, 19, 20, 19, METAL, 1)
    c.line(13, 20, 18, 20, METAL, 1)
    c.finish()
    c.set(24, 17, RED)
    c.set(6, 16, METAL)
    return c


def vacuum(i):
    """Робот-пылесос (слот краба-ползуна) едет вправо: четыре кадра, боковая щётка вращается,
    колёса и пыль сзади. Дымчатый корпус, дальнобойный датчик на макушке, бирюзовая кнопка,
    розовый стикер."""
    c = Canvas()
    c.rect(5, 29, 7, 29, GREY if i % 2 == 0 else METAL)
    c.set(3, 28 - i % 2, GREY)
    c.set(2, 27 + i % 2, METAL)
    c.rect(6, 27, 9, 28, DARK)
    c.rect(21, 27, 24, 28, DARK)
    c.ellipse(16, 23.5, 12.5, 5.6, METAL)
    c.rect(4, 24, 28, 28, METAL)
    c.rect(4, 27, 28, 28, DARK)
    c.ellipse(15, 21.5, 10, 4.3, DARK)
    c.ellipse(15, 20.8, 8.4, 3.4, METAL)
    c.rect(8, 20, 22, 21, GREY)
    c.ellipse(15, 18, 2.5, 1.8, SKY)
    c.set(14, 17, WHITE)
    c.rect(10, 22, 12, 22, AQUA)
    c.rect(18, 21, 21, 23, VIOLET)
    c.rect(18, 21, 21, 21, PLUM)
    # Щётка спереди: четыре щетинки по кругу, поворот по кадру.
    for k in range(4):
        a = math.radians(i * 45 + k * 90)
        c.line(27, 28, 27 + 3 * math.cos(a), 28 + 1.2 * math.sin(a), RED if k % 2 == 0 else WHITE, 1)
    c.finish()
    c.set(14, 18, K)
    return c


def card():
    """Ключ-карта: бирюзовая пластиковая карточка с фото-квадратом, золотым чипом, магнитной
    полосой и ушком для шнурка."""
    c = Canvas(32, 32)
    c.line(16, 3, 14, 8, METAL, 1)
    c.rect(4, 9, 27, 26, DARK)
    c.rect(5, 10, 26, 25, AQUA)
    c.rect(5, 10, 26, 11, SKY)
    c.rect(14, 5, 17, 9, DARK)
    c.rect(15, 6, 16, 8, SKY)
    c.rect(7, 14, 13, 21, WHITE)
    c.ellipse(10, 16, 1.6, 1.6, SKIN)
    c.rect(8, 19, 12, 21, METAL)
    c.rect(17, 14, 22, 18, GOLD)
    c.rect(17, 14, 22, 14, WHITE)
    c.rect(19, 14, 19, 18, BRASS)
    c.rect(5, 23, 26, 24, DARK)
    c.rect(16, 20, 23, 20, WHITE)
    return c.finish()


def coffee():
    """Стакан кофе с рукавом (аптечка): белый бумажный стакан, крышка, картонный рукав с красным
    крестом и пар над крышкой."""
    c = Canvas(32, 32)
    c.line(13, 9, 14, 5, SKY, 1)
    c.line(14, 5, 12, 2, SKY, 1)
    c.line(18, 9, 17, 5, SKY, 1)
    c.line(17, 5, 19, 2, SKY, 1)
    c.poly([(7, 12), (24, 12), (21, 29), (10, 29)], WHITE)
    c.poly([(8, 17), (23, 17), (22, 24), (9, 24)], TAN)
    c.rect(8, 17, 23, 17, BRASS)
    c.rect(14, 18, 17, 23, RED)
    c.rect(12, 20, 19, 21, RED)
    c.rect(6, 10, 25, 12, DARK)
    c.rect(8, 8, 23, 9, DARK)
    c.rect(8, 8, 23, 8, METAL)
    c.rect(8, 13, 9, 28, GREY)
    c.rect(10, 28, 21, 29, GREY)
    return c.finish()


def clip():
    """Скрепка летит вправо: двойной проволочный виток, блеск по верхней кромке. 16×16."""
    c = Canvas(16, 16)
    pts = [(10, 8), (3, 8), (3, 4), (13, 4), (13, 11), (6, 11), (6, 6)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], SKY, 1)
    c.line(3, 4, 13, 4, WHITE, 1)
    return c.finish()


def extras():
    """Слоты офиса вне `sprites()`: ленты и вещи тех же размеров, что у космоса, пиратов и замков."""
    return {
        "parrot_fly": strip([plane(i) for i in range(4)]),
        "crab_walk": strip([vacuum(i) for i in range(4)]),
        "key": card(),
        "medkit": coffee(),
        "shot": clip(),
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
