#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Зомби» (#137): зеркало `space_soccer16.py` и `pixel_soccer16.py`.
Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов, 8 «лежит»; мяч 8×8
в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка `sport_bit16.gd` ничего
не заметила.

Команда героя это выжившие из `zombies16.py`: красная куртка, синяя бейсболка с козырьком,
джинсы, белые кроссовки, за спиной рюкзак со скаткой. Соперники это зомби с зелёной кожей трёх
видов: ходок (клочья волос, серые лохмотья, босой, руки тянутся вперёд), толстяк (широкая лысая
голова со швом, белая майка в крови не сходится на животе), бегун (голубая толстовка с острым
капюшоном, красные глаза). Вратарь героя в жёлтом дождевике со светлой полосой и красных
рабочих перчатках, вратарь соперника это зомби-полицейский в синей форме и фуражке с кокардой,
перчатки белые. Мяч это череп (глазницы поворачиваются при качении), поле это жухлый
кладбищенский газон с полосами стрижки, проплешинами, листьями и костями, вокруг ночное
кладбище: надгробия с холмиками, свечи и блуждающие огоньки мерцают по кадрам, стелется туман.

    python3 tools/zombies_soccer16.py --preview thegames/debug/playtest/env/zombies_soccer16.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zombies16  # noqa: E402
from zombies16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK,  # noqa: E402
                       RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и одежды и вид головы. `limb`/`limb_far` это руки (рукав куртки или
    голая кожа зомби), `thigh`/`thigh_far` бёдра, `shirt`/`shorts` верх и низ, `sock` голени,
    `boot` обувь, `belt` кромка куртки, `trim` полоса на груди, `hand` кисть полевого игрока,
    `glove` перчатки вратаря, `head` вид головы. Флаги рисунка: `pack` рюкзак, `wide` толстяк,
    `belly` голый живот под короткой майкой, `rags` рваный подол, `reach` руки тянутся вперёд,
    `blood` пятна на груди."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, trim=None, glove=None, keeper=False,
                 thigh=None, thigh_far=None, boot=DARK, belt=None, hand=None, pack=False, wide=False,
                 belly=None, rags=False, reach=False, blood=False):
        self.head = head
        self.limb = limb
        self.limb_far = limb_far
        self.shirt = shirt
        self.shorts = shorts
        self.sock = sock
        self.trim = trim
        self.glove = glove
        self.keeper = keeper
        self.thigh = thigh if thigh is not None else limb
        self.thigh_far = thigh_far if thigh_far is not None else limb_far
        self.boot = boot
        self.belt = belt
        self.hand = hand
        self.pack = pack
        self.wide = wide
        self.belly = belly
        self.rags = rags
        self.reach = reach
        self.blood = blood


def _cols(x, side):
    """Крайние столбцы головы: в профиль центр целый (семь столбцов), анфас и со спины центр на
    полпикселя (восемь столбцов)."""
    if side:
        return int(x) - 3, int(x) + 3
    return int(math.floor(x)) - 3, int(math.floor(x)) + 4


def _recolor(c, x0, x1, y0, y1, src, col, test=None):
    """Перекрасить пиксели цвета `src` в прямоугольнике, если `test(x, y)` согласен."""
    for yy in range(int(y0), int(y1) + 1):
        for xx in range(x0, x1 + 1):
            if c.get(xx, yy) == src and (test is None or test(xx, yy)):
                c.set(xx, yy, col)


def _head_survivor(c, x, y, side, back, sgn, marks):
    """Выживший: бейсболка с куполом выше макушки и козырьком вперёд, из-под неё тёмные волосы."""
    xl, xr = _cols(x, side)
    c.ellipse(x, y, 3.6, 3.6, SKIN)
    if back:
        # Затылок: волосы под кепкой, ниже шея.
        _recolor(c, xl, xr, y - 1, y + 1, SKIN, DARK)
    elif side:
        _recolor(c, xl, xr, y - 1, y + 1, SKIN, DARK, lambda xx, yy: (xx - x) * sgn <= -2)
    # Купол кепки: три строки, верхняя над макушкой.
    c.rect(xl + 2, y - 4, xr - 2, y - 4, SEA)
    c.rect(xl + 1, y - 3, xr - 1, y - 3, SEA)
    c.rect(xl, y - 2, xr, y - 2, SEA)
    if back:
        c.rect(xl, y - 1, xr, y - 1, SEA)
        # Вырез застёжки и пуговка на макушке.
        mid = (xl + xr) // 2
        marks.append((mid, y - 1, DARK))
        marks.append((mid + 1, y - 1, DARK))
        marks.append((mid, y - 4, AQUA))
        return
    if side:
        # Козырёк: длинный и плоский, по нижней кромке купола.
        front = xr if sgn > 0 else xl
        c.rect(min(front, front + sgn * 3), y - 2, max(front, front + sgn * 3), y - 2, SEA)
        marks.append((front + sgn, y - 1, NAVY))
        marks.append((x + sgn, y - 3, WHITE))
        marks.append((x + sgn * 2, y, K))
        marks.append((x + sgn * 2, y + 2, TAN))
    else:
        # Козырёк к камере: тёмная полоса над глазами шире купола.
        for xx in range(xl, xr + 1):
            marks.append((xx, y - 1, NAVY))
        marks.append((xl + 3, y - 3, WHITE))
        marks.append((xl + 4, y - 3, WHITE))
        marks.append((xl + 2, y + 1, K))
        marks.append((xr - 2, y + 1, K))
        marks.append((xl + 3, y + 3, TAN))
        marks.append((xl + 4, y + 3, TAN))


def _head_walker(c, x, y, side, back, sgn, marks):
    """Ходок: зелёная голова, клочья волос торчат неровно, один глаз белый, второй вытек."""
    xl, xr = _cols(x, side)
    c.ellipse(x, y, 3.6, 3.5, VIOLET)
    # Волосы: макушка целиком, ниже через столбец, два клока торчат вверх.
    _recolor(c, xl, xr, y - 3, y - 3, VIOLET, DARK)
    _recolor(c, xl, xr, y - 2, y - 2, VIOLET, DARK, lambda xx, yy: (xx - xl) % 3 != 1)
    c.set(xl + 1, y - 4, DARK)
    c.set(xl + 2, y - 4, DARK)
    c.set(xr - 2, y - 4, DARK)
    if back:
        _recolor(c, xl, xr, y - 1, y, VIOLET, DARK, lambda xx, yy: (xx + yy) % 3 != 0)
        # Проплешина с раной на затылке.
        marks.append((xl + 3, y - 1, PLUM))
        marks.append((xl + 4, y - 1, RED))
        return
    if side:
        _recolor(c, xl, xr, y - 1, y, VIOLET, DARK, lambda xx, yy: (xx - x) * sgn <= -2)
        marks.append((x + sgn * 2, y, WHITE))
        marks.append((x + sgn * 2, y + 2, K))
        marks.append((x + sgn * 3, y + 2, K))
        marks.append((x + sgn * 2, y + 3, RED))
    else:
        marks.append((xl + 2, y, WHITE))
        marks.append((xl + 2, y + 1, WHITE))
        marks.append((xr - 2, y, K))
        marks.append((xr - 2, y + 1, K))
        marks.append((xl + 3, y + 2, K))
        marks.append((xl + 4, y + 2, K))
        marks.append((xl + 4, y + 3, RED))


def _head_fat(c, x, y, side, back, sgn, marks):
    """Толстяк: широкая приплюснутая лысая голова, шов через темя, щёки шире плеч ходока."""
    c.ellipse(x, y + 0.5, 4.2 if side else 4.6, 3.3, VIOLET)
    xl, xr = _cols(x, side)
    mid = (xl + xr) // 2
    # Шов со стежками поперёк темени.
    for k in range(-2, 4, 2):
        marks.append((mid + k, y - 2, K))
    marks.append((mid + 1, y - 1, RED))
    if back:
        # Складка на затылке.
        for xx in range(xl + 1, xr):
            marks.append((xx, y + 2, PLUM))
        return
    if side:
        marks.append((x + sgn * 2, y, K))
        marks.append((x + sgn * 3, y, WHITE))
        for k in (1, 2, 3):
            marks.append((x + sgn * k, y + 2, K))
        marks.append((x + sgn * 3, y + 2, WHITE))
    else:
        marks.append((xl + 1, y, WHITE))
        marks.append((xl + 2, y, K))
        marks.append((xr - 1, y, WHITE))
        marks.append((xr - 2, y, K))
        # Широкий рот с зубом.
        for xx in range(xl + 2, xr - 1):
            marks.append((xx, y + 2, K))
        marks.append((xl + 3, y + 2, WHITE))
        marks.append((xr - 3, y + 3, RED))


def _head_runner(c, x, y, side, back, sgn, marks):
    """Бегун: толстовка с капюшоном, острый верх сбит назад, в проёме зелёное лицо и красные
    глаза."""
    xl, xr = _cols(x, side)
    c.ellipse(x, y, 3.6, 3.6, SKY)
    # Острый верх капюшона.
    if side:
        tip = x - sgn * 4
        c.rect(min(x - sgn, tip), y - 4, max(x - sgn, tip), y - 4, SKY)
        c.set(tip, y - 3, SKY)
        c.set(tip + sgn, y - 3, SKY)
    else:
        c.rect(xl + 3, y - 4, xl + 4, y - 4, SKY)
    if back:
        # Шов капюшона по затылку.
        for yy in range(int(y - 3), int(y + 3)):
            marks.append((xl + 3, yy, AQUA))
        return
    if side:
        f0, f1 = sorted((int(x + sgn), int(x + sgn * 3)))
        c.rect(f0, y - 1, f1, y + 2, VIOLET)
        marks.append((x + sgn * 2, y, RED))
        marks.append((x + sgn * 3, y + 2, K))
    else:
        c.rect(xl + 2, y - 1, xr - 2, y + 2, VIOLET)
        marks.append((xl + 2, y, RED))
        marks.append((xr - 2, y, RED))
        marks.append((xl + 3, y + 2, K))
        marks.append((xl + 4, y + 2, K))
        # Шнурки капюшона.
        marks.append((xl + 2, y + 3, WHITE))
        marks.append((xr - 2, y + 3, WHITE))


def _head_cop(c, x, y, side, back, sgn, marks):
    """Зомби-полицейский: фуражка с тульёй шире головы, кокарда, лакированный козырёк."""
    xl, xr = _cols(x, side)
    c.ellipse(x, y, 3.6, 3.6, VIOLET)
    # Тулья: верх шире околыша.
    c.rect(xl, y - 4, xr, y - 4, SEA)
    c.rect(xl - 1, y - 3, xr + 1, y - 3, SEA)
    c.rect(xl, y - 2, xr, y - 2, NAVY)
    if back:
        _recolor(c, xl, xr, y - 1, y, VIOLET, DARK)
        return
    if side:
        front = xr if sgn > 0 else xl
        c.rect(min(front, front + sgn * 2), y - 1, max(front, front + sgn * 2), y - 1, NAVY)
        _recolor(c, xl, xr, y - 1, y, VIOLET, DARK, lambda xx, yy: (xx - x) * sgn <= -2)
        marks.append((front, y - 3, GOLD))
        marks.append((x + sgn * 2, y, WHITE))
        marks.append((x + sgn * 2, y + 2, K))
        marks.append((x + sgn * 3, y + 2, K))
    else:
        for xx in range(xl + 1, xr):
            marks.append((xx, y - 1, K))
        marks.append((xl + 3, y - 3, GOLD))
        marks.append((xl + 4, y - 3, GOLD))
        marks.append((xl + 2, y, WHITE))
        marks.append((xr - 2, y, K))
        marks.append((xl + 3, y + 2, K))
        marks.append((xl + 4, y + 2, K))
        marks.append((xl + 5, y + 3, RED))


_HEADS = {"survivor": _head_survivor, "walker": _head_walker, "fat": _head_fat, "runner": _head_runner,
          "cop": _head_cop}


def _head(c, x, y, look, side, back, sgn):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (глаза, козырёк, швы)."""
    marks = []
    if side:
        x = int(round(x))
    _HEADS[look.head](c, x, int(y), side, back, sgn, marks)
    return marks


def _hand(c, look, x, y):
    """Кисть: у вратаря перчатка на два пикселя, у полевого кулак."""
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)
    elif look.hand is not None:
        c.rect(x - 0.5, y + 0.5, x + 0.5, y + 1.0, look.hand)


def _arm(c, x0, y0, x1, y1, col):
    """Рука стоящего игрока: отрезок чуть толще двух пикселей, чтобы отвесная рука шла сплошной
    полосой от плеча до кисти, без разрывов между строками."""
    c.line(x0, y0, x1, y1, col, 2.5)


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов: стойка и четыре кадра бега по
    восьми направлениям, подкат (у вратаря прыжок за мячом), лежит."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    w = 1 if look.wide else 0
    if mode == "down":
        # Лежит на спине поперёк: голова слева, ноги справа, рука откинута.
        c.line(18, 17, 22, 15, look.sock, 2)
        c.line(18, 19, 22, 20, look.sock, 2)
        c.rect(21, 14, 22, 15, look.boot)
        c.rect(21, 20, 22, 21, look.boot)
        c.line(9, 15, 6, 12, look.limb, 2)
        c.rect(7, 16 - w, 14, 20 + w, look.shirt)
        if look.trim is not None:
            c.rect(10, 16 - w, 10, 20 + w, look.trim)
        if look.belly is not None:
            c.rect(13, 16 - w, 14, 20 + w, look.belly)
        if look.belt is not None:
            c.rect(14, 16, 14, 20, look.belt)
        c.rect(15, 16 - w, 17, 20 + w, look.shorts)
        if look.rags:
            c.set(15, 17, look.shirt)
            c.set(15, 20, look.shirt)
        if look.blood:
            marks.append((9, 18, RED))
            marks.append((10, 19, RED))
        # Голова зомби шире кепки: сдвинута на пиксель, чтобы обводка не ушла за край.
        marks += _head(c, 4 if look.head == "survivor" else 5, 18, look, True, False, 1)
        if look.keeper:
            c.rect(5, 11, 6, 12, look.glove)
        elif look.hand is not None:
            c.rect(5, 11, 6, 12, look.hand)
        c.finish()
        for x, y, v in marks:
            c.set(x, y, v)
        return c
    if mode == "slide":
        n = math.hypot(dx, dy * 0.7)
        ux, uy = dx / n, dy * 0.7 / n
        cx, cy = 12.0, 16.0
        tx, ty = cx - ux * 5.0, cy - uy * 5.0
        side = abs(dx) > 0.38
        back = dy < -0.38
        body = 5 + w
        if look.keeper:
            # Прыжок за мячом: руки в перчатках вытянуты вперёд, ноги сзади.
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.sock, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.sock, 2)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, look.shirt, body)
            c.line(tx - ux, ty - uy, tx, ty, look.shorts, body)
            hx, hy = cx + ux * 5.0, cy + uy * 5.0 - 1.0
            c.line(cx + ux * 2.0 - uy * 2.0, cy + uy * 2.0 + ux * 2.0, hx + ux * 5.0 - uy * 2.0, hy + uy * 5.0 + ux * 2.0, look.limb, 2)
            c.line(cx + ux * 2.0 + uy * 2.0, cy + uy * 2.0 - ux * 2.0, hx + ux * 5.0 + uy * 2.0, hy + uy * 5.0 - ux * 2.0, look.limb, 2)
            marks = _head(c, round(hx), round(hy), look, side, back, sgn)
            c.finish()
            for q in (-2.0, 2.0):
                gx, gy = hx + ux * 5.5 - uy * q, hy + uy * 5.5 + ux * q
                c.rect(gx - 0.5, gy - 0.5, gx + 0.5, gy + 0.5, look.glove)
            for x, y, v in marks:
                c.set(x, y, v)
            return c
        # Подкат по ходу: нога вытянута вперёд, вторая согнута, тело сзади низко.
        fx, fy = cx + ux * 8.0, cy + uy * 8.0
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, look.thigh_far, 2)
        c.line(cx, cy, fx, fy, look.thigh, 2)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, look.sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, look.boot)
        c.line(tx, ty, cx, cy, look.shirt, body)
        if look.belly is not None:
            c.line(cx - ux * 2.0, cy - uy * 2.0, cx - ux, cy - uy, look.belly, body)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, body)
        if look.belt is not None:
            c.line(cx - ux * 2.0 - uy * 2.0, cy - uy * 2.0 + ux * 2.0, cx - ux * 2.0 + uy * 2.0, cy - uy * 2.0 - ux * 2.0,
                   look.belt, 1)
        ax, ay = tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0
        c.line(tx, ty, ax, ay, look.limb, 2)
        if look.hand is not None:
            c.set(ax, ay, look.hand)
        # Широкая голова и капюшон не выходят за край кадра.
        hx = min(max(round(tx - ux * 3.0), 5), 18)
        marks = _head(c, hx, round(ty - uy * 3.0 - 2.0), look, side, back, sgn)
        c.finish()
        for x, y, v in marks:
            c.set(x, y, v)
        return c
    side = abs(dx) > 0.38
    back = dy < -0.38
    s = (0, 1, 0, -1, 0)[frame]
    bob = 1 if frame in (2, 4) else 0
    hip = 18 - bob
    if side:
        if look.reach:
            # Зомби тянет руки вперёд: дальняя ниже, ближняя выше, на шаге покачиваются.
            far_hand = (11.5 + sgn * 5.0, 14.5 - bob - s)
            near_hand = (11.5 + sgn * 5.5, 12.0 - bob + s)
        else:
            far_hand = (11.5 + sgn * 4.0 * s, 15.0 - bob - abs(s))
            near_hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        _arm(c, 11.5, 11.0 - bob, far_hand[0], far_hand[1], look.limb_far)
        _hand(c, look, far_hand[0], far_hand[1])
        for near, k in ((False, -s), (True, s)):
            thigh = look.thigh if near else look.thigh_far
            if frame in (2, 4) and near == (frame == 2):
                foot = (11.5 + sgn * 1.0, 19.0)
                knee = (11.5 + sgn * 2.5, 18.0)
            else:
                foot = (11.5 + sgn * 4.0 * k, 21.0 - (2.0 if k < 0 else 0.0))
                knee = ((11.5 + foot[0]) / 2.0 + sgn * 1.0, (hip + foot[1]) / 2.0)
            c.line(11.5, hip, knee[0], knee[1], thigh, 2)
            c.line(knee[0], knee[1], foot[0], foot[1], look.sock if near else look.thigh_far, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0,
                   look.boot)
        if look.pack:
            # Рюкзак за спиной: кожаный мешок, сверху зелёная скатка, пряжка.
            b0, b1 = (6, 8) if sgn > 0 else (15, 17)
            c.rect(b0, 11 - bob, b1, 14 - bob, METAL)
            c.rect(b0, 9 - bob, b1, 10 - bob, VIOLET)
            marks.append(((b0 + b1) // 2, 13 - bob, GOLD))
        c.rect(9 - w, 10 - bob, 14 + w, 15 - bob, look.shirt)
        if look.wide:
            # Живот выпирает вперёд.
            bx = 16 if sgn > 0 else 7
            c.rect(bx, 12 - bob, bx, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(9 - w, 12 - bob, 14 + w, 12 - bob, look.trim)
        if look.belly is not None:
            b0, b1 = (9, 16) if sgn > 0 else (7, 14)
            c.rect(b0, 14 - bob, b1, 15 - bob, look.belly)
        if look.belt is not None:
            c.rect(9, 15 - bob, 14, 15 - bob, look.belt)
        c.rect(9 - w, 16 - bob, 14 + w, 17 - bob, look.shorts)
        if look.rags:
            # Рваный подол свисает клочьями.
            for x, y in ((9, 16), (11, 16), (11, 17), (14, 16)):
                c.set(x, y - bob, look.shirt)
        if look.blood:
            marks.append((12 + sgn, 12 - bob, RED))
            marks.append((12 + sgn, 13 - bob, RED))
            marks.append((12, 13 - bob, RED))
        if look.head == "survivor":
            # Белый ворот футболки у горла.
            marks.append((13 if sgn > 0 else 10, 10 - bob, WHITE))
        if look.head == "cop":
            marks.append((13 if sgn > 0 else 10, 11 - bob, GOLD))
        _arm(c, 11.5, 11.0 - bob, near_hand[0], near_hand[1], look.limb)
        _hand(c, look, near_hand[0], near_hand[1])
        marks += _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.thigh)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.boot)
        c.rect(8 - w, 10 - bob, 15 + w, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(8 - w, 12 - bob, 15 + w, 12 - bob, look.trim)
        if look.belly is not None:
            c.rect(8 - w, 14 - bob, 15 + w, 15 - bob, look.belly)
            if not back:
                marks.append((12, 15 - bob, PLUM))
        if look.belt is not None:
            c.rect(8, 15 - bob, 15, 15 - bob, look.belt)
        c.rect(8 - w, 16 - bob, 15 + w, 17 - bob, look.shorts)
        if look.rags:
            for x, y in ((8, 16), (10, 16), (10, 17), (13, 16), (15, 16), (15, 17)):
                c.set(x, y - bob, look.shirt)
        if look.pack:
            if back:
                # Рюкзак на спине: мешок с клапаном, сверху скатка от плеча до плеча.
                c.rect(9, 11 - bob, 14, 15 - bob, METAL)
                c.rect(8, 10 - bob, 15, 10 - bob, VIOLET)
                for xx in range(9, 15):
                    marks.append((xx, 12 - bob, DARK))
                marks.append((11, 13 - bob, GOLD))
                marks.append((12, 13 - bob, GOLD))
            else:
                # Лямки рюкзака и молния куртки.
                for yy in range(10, 14):
                    marks.append((9, yy - bob, DARK))
                    marks.append((14, yy - bob, DARK))
        if not back:
            if look.head == "survivor":
                marks.append((11, 10 - bob, WHITE))
                marks.append((12, 10 - bob, WHITE))
            if look.head == "cop":
                marks.append((13, 11 - bob, GOLD))
                marks.append((11, 12 - bob, NAVY))
                marks.append((11, 13 - bob, NAVY))
            if look.blood:
                for x, y in ((10, 11), (11, 12), (10, 12), (13, 13)):
                    marks.append((x, y - bob, RED))
        for x, k, out in ((6.5 - w, -s, -1), (16.5 + w, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            _arm(c, x, 11.0 - bob, hand[0], hand[1], look.limb)
            _hand(c, look, hand[0], hand[1])
        marks += _head(c, 11.5, 6 - bob, look, False, back, sgn)
    c.finish()
    for x, y, v in marks:
        c.set(x, y, v)
    return c


def kit_strip(look):
    frames = []
    for d in range(8):
        for fr in range(RUN):
            frames.append(player(d, fr, look))
    for d in range(8):
        frames.append(player(d, 0, look, "slide"))
    for d in range(8):
        frames.append(player(d, 0, look, "down"))
    return strip(frames)


# Команды. Герой: красная куртка с тёмной резинкой понизу, джинсы, белые кроссовки, рюкзак.
HERO = Look("survivor", RED, DARK, RED, SEA, SEA, thigh=SEA, thigh_far=NAVY, boot=WHITE, belt=DARK, hand=SKIN,
            pack=True)
# Вратарь героя: жёлтый дождевик со светлой полосой, красные рабочие перчатки, без рюкзака.
KEEPER_HERO = Look("survivor", GOLD, BRASS, GOLD, SEA, SEA, trim=WHITE, glove=RED, keeper=True, thigh=SEA,
                   thigh_far=NAVY, boot=WHITE)
# Ходок: серые лохмотья в крови, бурые штаны, босой, руки тянутся вперёд.
RIVAL_0 = Look("walker", VIOLET, PLUM, GREY, METAL, VIOLET, thigh=METAL, thigh_far=DARK, boot=VIOLET, hand=VIOLET,
               rags=True, reach=True, blood=True)
# Толстяк: белая майка в крови не сходится на животе, тёмные штаны.
RIVAL_1 = Look("fat", VIOLET, PLUM, WHITE, DARK, VIOLET, thigh=DARK, thigh_far=DARK, boot=METAL, hand=VIOLET,
               wide=True, belly=VIOLET, blood=True)
# Бегун: голубая толстовка с капюшоном, синие шорты, голые ноги, серые кеды.
RIVAL_2 = Look("runner", SKY, AQUA, SKY, NAVY, VIOLET, trim=AQUA, thigh=VIOLET, thigh_far=PLUM, boot=GREY,
               hand=VIOLET)
# Вратарь соперника: зомби-полицейский в синей форме, фуражка, белые перчатки.
KEEPER_RIVAL = Look("cop", SEA, NAVY, SEA, NAVY, NAVY, glove=WHITE, keeper=True, thigh=NAVY, thigh_far=NAVY,
                    boot=DARK, belt=DARK)


# Череп 8×8: тёмный обод, кость, глазницы и зубы. Два кадра: лицом вверх и на боку, при качении
# череп «вращается». o обод, W кость, g тень кости, k провал, r трещина.
BALL_MAPS = (
    ("..oooo..",
     ".oWWWWo.",
     "oWWWWWWo",
     "okkWWkko",
     "okkWWkkg",
     "oWWkWWgo",
     ".okWkgo.",
     "..oooo.."),
    ("..oooo..",
     ".oWWkko.",
     "oWWWkkWo",
     "oWWWWWko",
     "oWWrWWWk",
     "oWWWkkgo",
     ".ogWkko.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "W": WHITE, "g": GREY, "k": K, "r": TAN}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def lawn():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): жухлый газон, полосы
    по 32 темнее и светлее, пучки сухой травы, редкие косточки."""
    c = Canvas(64, 64)
    rng = random.Random(23)
    for y in range(64):
        for x in range(64):
            # Тёмная полоса: по зелени редкие точки грязи, светлая чистая.
            c.set(x, y, DARK if x < 32 and (x + y) % 4 == 0 and (x - y) % 4 == 0 else PLUM)
    for _ in range(70):
        x, y = rng.randrange(64), rng.randrange(1, 64)
        c.set(x, y, VIOLET if rng.random() < 0.5 else BRASS)
        c.set(x, y - 1, PLUM)
    for _ in range(5):
        x, y = rng.randrange(2, 60), rng.randrange(2, 62)
        c.rect(x, y, x + 2, y, WHITE)
        c.set(x, y + 1, GREY)
        c.set(x + 2, y - 1, WHITE)
    return c


def sprites():
    return {
        "soccer_hero": kit_strip(HERO),
        "soccer_rival_0": kit_strip(RIVAL_0),
        "soccer_rival_1": kit_strip(RIVAL_1),
        "soccer_rival_2": kit_strip(RIVAL_2),
        "soccer_keeper_hero": kit_strip(KEEPER_HERO),
        "soccer_keeper_rival": kit_strip(KEEPER_RIVAL),
        "soccer_ball": strip([ball(i) for i in range(2)]),
        "soccer_grass": lawn(),
    }


# --- Поле и аут ---------------------------------------------------------------------------------
# Тайлы 64×64 бесшовные, в своих палитрах. Поле тёмное и тусклое: на нём читаются и красные
# куртки, и ярко-зелёная кожа зомби, и белая разметка демки. Аут холоднее и темнее поля.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def turf():
    """Кладбищенский газон: жухлая оливковая трава, полосы стрижки по 32, штрихи травинок,
    вытоптанные проплешины земли, палые листья и мелкие кости.
    Палитра: 0 глубокая тень, 1 тень, 2 трава, 3 светлая трава, 4 травинка, 5 сухая трава,
    6 кость, 7 земля, 8 лист."""
    pal = _pal(0x25291F, 0x333A2A, 0x414A33, 0x4B5539, 0x66704A, 0x8C8250, 0xCFCBB4, 0x4A3B30, 0x8A4A2E)
    c = Canvas(T, T)
    rng = random.Random(41)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    for _ in range(int(T * T * 0.09)):
        x, y = rng.randrange(T), rng.randrange(T)
        base = c.px[y][x]
        c.px[y][x] = base - 1 if rng.random() < 0.65 else base + 1
    # Проплешины: земля с тёмным краем сверху слева и редкой травой внутри.
    rng = random.Random(6)
    for cx, cy, rx, ry in ((14, 46, 5.0, 3.0), (49, 17, 4.0, 2.6), (37, 56, 3.0, 2.0)):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                q = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if q <= 1.0 and rng.random() < 0.86:
                    _wrap(c, x, y, 1 if q > 0.55 and (x - cx) + (y - cy) < 0 else 7)
    # Травинки: светлый штрих с тенью под ним, сухие пучки по два-три стебля.
    for _ in range(46):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 4)
        _wrap(c, x, y - 1, 4)
        _wrap(c, x + 1, y + 1, 1)
    for _ in range(9):
        x, y = rng.randrange(T), rng.randrange(T)
        for k, h in ((0, 2), (1, 3), (2, 2)):
            for j in range(h):
                _wrap(c, x + k, y - j, 5)
        _wrap(c, x + 3, y, 0)
        _wrap(c, x + 1, y + 1, 0)
    # Палые листья и кости.
    for _ in range(7):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 8)
        _wrap(c, x + 1, y, 8)
        _wrap(c, x + 1, y + 1, 0)
    for x, y in ((24, 13), (55, 40), (6, 27)):
        for k in range(4):
            _wrap(c, x + k, y, 6)
        _wrap(c, x, y - 1, 6)
        _wrap(c, x + 3, y + 1, 6)
        _wrap(c, x + 1, y + 1, 0)
        _wrap(c, x + 2, y + 1, 0)
    return c, pal


# Могилы аута: (x, y, вид) левого верхнего угла камня; холмик лежит ниже камня.
_GRAVES = ((9, 4, "slab"), (41, 10, "cross"), (24, 37, "slab"), (52, 42, "stump"))
# Свечи у камней и блуждающие огоньки: (x, y).
_CANDLES = ((18, 14), (22, 47))
_WISPS = ((34, 27), (58, 6), (6, 58))


def _grave(c, x, y, kind):
    """Могила видом сверху под углом, как игроки: камень стоит, тень падает вправо вниз, под
    камнем холмик земли. Цвета: 3 тень камня, 4 камень, 5 свет камня, 6 земля, 7 свет земли,
    0 тень на траве."""
    # Холмик: овал земли с бликом по левому краю.
    for yy in range(y + 8, y + 19):
        for xx in range(x - 1, x + 9):
            q = ((xx - (x + 3.5)) / 4.4) ** 2 + ((yy - (y + 13.0)) / 5.4) ** 2
            if q <= 1.0:
                _wrap(c, xx, yy, 7 if q > 0.45 and xx < x + 3 and yy < y + 13 else 6)
            elif q <= 1.5 and xx > x + 3 and yy > y + 12:
                _wrap(c, xx, yy, 0)
    if kind == "slab":
        # Плита с круглым верхом, надпись в две строки.
        for yy in range(y, y + 10):
            for xx in range(x, x + 8):
                if yy == y and xx in (x, x + 1, x + 6, x + 7):
                    continue
                if yy == y + 1 and xx in (x, x + 7):
                    continue
                _wrap(c, xx, yy, 5 if xx == x or yy <= y + 1 and xx < x + 6 else 3 if xx >= x + 6 else 4)
        for xx in range(x + 2, x + 6):
            _wrap(c, xx, y + 4, 3)
        for xx in range(x + 2, x + 5):
            _wrap(c, xx, y + 6, 3)
        for yy in range(y + 2, y + 11):
            _wrap(c, x + 8, yy, 0)
        for xx in range(x + 1, x + 9):
            _wrap(c, xx, y + 10, 0)
    elif kind == "cross":
        # Каменный крест на тумбе.
        for yy in range(y, y + 9):
            for xx in range(x + 3, x + 6):
                _wrap(c, xx, yy, 5 if xx == x + 3 else 3 if xx == x + 5 else 4)
        for yy in range(y + 2, y + 5):
            for xx in range(x, x + 9):
                _wrap(c, xx, yy, 5 if yy == y + 2 else 3 if yy == y + 4 or xx == x + 8 else 4)
        for xx in range(x + 1, x + 8):
            _wrap(c, xx, y + 9, 4 if xx < x + 6 else 3)
            _wrap(c, xx + 1, y + 10, 0)
        for xx in range(x + 1, x + 10):
            _wrap(c, xx, y + 5, 0 if c.px[(y + 5) % T][xx % T] < 3 else c.px[(y + 5) % T][xx % T])
    else:
        # Обломок плиты: косой скол, рядом осколок.
        for yy in range(y + 4, y + 10):
            for xx in range(x, x + 8):
                if xx - x > (yy - y - 3) * 2 + 1:
                    continue
                _wrap(c, xx, yy, 5 if yy == y + 4 + max(0, (xx - x) // 2) or xx == x else 3 if xx >= x + 6 else 4)
        for xx in range(x + 1, x + 9):
            _wrap(c, xx, y + 10, 0)
        _wrap(c, x + 9, y + 8, 4)
        _wrap(c, x + 10, y + 8, 3)
        _wrap(c, x + 10, y + 9, 0)


def graveyard(frame):
    """Кладбище вокруг поля: сине-чёрная ночная трава, надгробия с холмиками, свечи мигают по
    кадрам, блуждающие огоньки разгораются и гаснут, редкий туман дышит. Палитра: 0 чернота,
    1 ночная трава, 2 травинка, 3 тень камня, 4 камень, 5 свет камня, 6 земля, 7 свет земли,
    8 туман, 9 отсвет свечи, 10 пламя, 11 огонёк, 12 яркий огонёк."""
    pal = _pal(0x0C1016, 0x141C22, 0x1E2C30, 0x3C4250, 0x6C7484, 0xA8B0BE, 0x2E2424, 0x45342E, 0x2A3848,
               0x6A4A26, 0xFFD46A, 0x5FB890, 0xD8FFE0)
    c = Canvas(T, T)
    rng = random.Random(13)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 1
    for _ in range(int(T * T * 0.12)):
        c.px[rng.randrange(T)][rng.randrange(T)] = 0
    for _ in range(60):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 2)
        _wrap(c, x, y - 1, 2)
        _wrap(c, x + 1, y - 2, 2)
    # Туман: редкая штриховка по волнам, порог дышит по кадрам (плотнее и реже).
    edge = 1.25 + 0.2 * math.sin(frame * math.pi / 2.0)
    for y in range(T):
        for x in range(T):
            v = (math.sin(x / 64.0 * 2 * math.pi + 2.0 * math.sin(y / 64.0 * 2 * math.pi)) +
                 math.sin((x + 2 * y) / 64.0 * 2 * math.pi + 1.3))
            if v > edge and (x + y) % 2 == 0:
                c.px[y][x] = 8
    for x, y, kind in _GRAVES:
        _grave(c, x, y, kind)
    # Свечи: белый столбик, пламя прыгает, отсвет на траве то шире, то уже.
    for i, (x, y) in enumerate(_CANDLES):
        big = (frame + i) % 2 == 0
        rr = 3.2 if big else 2.2
        for yy in range(y - 4, y + 5):
            for xx in range(x - 4, x + 5):
                d = math.hypot(xx - x, yy - y)
                if d <= rr and (xx + yy) % 2 == 0 and c.px[yy % T][xx % T] in (0, 1, 2, 8):
                    _wrap(c, xx, yy, 9)
        _wrap(c, x, y, 5)
        _wrap(c, x, y + 1, 4)
        _wrap(c, x, y - 1, 10)
        if big:
            _wrap(c, x + (i % 2), y - 2, 10)
    # Блуждающие огоньки: у каждого своя фаза, ярким он бывает один кадр из четырёх.
    for i, (x, y) in enumerate(_WISPS):
        tw = (frame + i) % 4
        if tw == 0:
            _wrap(c, x, y, 12)
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                _wrap(c, x + ddx, y + ddy, 11)
        elif tw in (1, 3):
            _wrap(c, x, y, 11)
            _wrap(c, x, y - 1 if tw == 1 else y + 1, 8)
        else:
            _wrap(c, x, y, 8)
    return c, pal


def fields():
    """Тайлы поля и аута зомби → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = turf()
    frames = [graveyard(f) for f in range(4)]
    return {
        "soccer_field_zombies": (cv, pal),
        "soccer_out_zombies": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    """Лист модуля: ленты игроков, мяч и тайлы. Лист выше 1500 пикселей делится на файлы с
    суффиксами `_b`, `_c`."""
    scale, pad, max_w, limit = 3, 6, 480, 1500
    items = zombies16.shaded(sprites())
    items.update(fields())
    pages, page, height = [], {}, pad * scale
    for key, (canvas, palette) in items.items():
        rows = (canvas.w + max_w - 1) // max_w
        h = rows * (canvas.h + pad) * scale
        if page and height + h > limit:
            pages.append(page)
            page, height = {}, pad * scale
        page[key] = (canvas, palette)
        height += h
    pages.append(page)
    stem, ext = os.path.splitext(path)
    for i, page in enumerate(pages):
        name = path if i == 0 else "%s_%s%s" % (stem, chr(ord("a") + i), ext)
        zombies16.save_sheet(name, page, scale=scale, pad=pad, max_w=max_w)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
