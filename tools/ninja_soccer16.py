#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Ниндзя» (#137): зеркало `space_soccer16.py` и `pixel_soccer16.py`.
Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов, 8 «лежит»; мяч 8×8
в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка `sport_bit16.gd` ничего
не заметила.

Команда героя это ниндзя из `ninja16.py`: тёмно-синий костюм, капюшон с прорезью глаз, красный
шарф с двумя концами за спиной, рукоять меча над плечом, белые обмотки на голенях, тёмные таби.
Соперники это чужой клан трёх видов: ниндзя в красном с чёрной маской и красной повязкой с
завязками, сумоист (широкий, голый торс, пучок волос, красный пояс маваси, босой), самурай в
чёрном лаковом доспехе (шлем с золотым полумесяцем и назатыльником, красная полумаска и шнуровка).
Вратарь героя в белой куртке и соломенной шляпе касе, перчатки красные; вратарь соперника это
ниндзя чужого клана в жёлтой куртке, перчатки белые. Мяч это расшитый тэмари (красные и золотые
клинья по белому, при качении поворачиваются), поле это сад камней на закате: гравий расчёсан
полосами по 32 то вдоль, то поперёк, камни в кругах, мох и кленовые листья; вокруг тёмный пруд:
рябь бежит по кадрам, блики заката мерцают, кувшинки, карп шевелит хвостом.

    python3 tools/ninja_soccer16.py --preview thegames/debug/playtest/env/ninja_soccer16.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ninja16  # noqa: E402
from ninja16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK,  # noqa: E402
                     RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и одежды и вид головы. `limb`/`limb_far` это рукава (у сумоиста
    кожа), `thigh`/`thigh_far` штанины до колена, `shirt`/`shorts` верх и низ, `sock` голени
    (обмотки), `boot` обувь, `belt` пояс, `trim` полоса на груди, `lapel` запах куртки, `hand`
    кисть полевого игрока, `glove` перчатки вратаря, `head` вид головы, `hood` цвет капюшона или
    маски, `scarf` ворот. Флаги рисунка: `tails` концы шарфа за спиной, `sword` рукоять меча над
    плечом, `wide` широкий корпус сумоиста."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, trim=None, glove=None, keeper=False,
                 thigh=None, thigh_far=None, boot=DARK, belt=None, lapel=None, hand=None, hood=SEA,
                 scarf=None, tails=False, sword=False, wide=False):
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
        self.lapel = lapel
        self.hand = hand
        self.hood = hood
        self.scarf = scarf
        self.tails = tails
        self.sword = sword
        self.wide = wide


def _span(x):
    """Крайние столбцы головы: у целого центра 7 пикселей, у центра на стыке 8."""
    if abs(x - round(x)) > 0.25:
        return int(math.floor(x)) - 3, int(math.floor(x)) + 4
    return int(round(x)) - 3, int(round(x)) + 3


def _slit(c, x, y, look, side, sgn, marks, rows=(-1, 0)):
    """Прорезь глаз в капюшоне или маске: два ряда кожи, глаза ставятся после обводки."""
    lo, hi = _span(x)
    if side:
        xc = int(round(x))
        cols = range(xc, hi + 1) if sgn > 0 else range(lo, xc + 1)
        eyes = (xc + sgn * 2,)
    else:
        cols = range(lo + 1, hi)
        eyes = (lo + 2, hi - 2)
    for dy in rows:
        for xx in cols:
            if c.get(xx, y + dy) == look.hood:
                c.set(xx, y + dy, SKIN)
    for ex in eyes:
        for dy in rows:
            marks.append((ex, y + dy, K))


def _head(c, x, y, look, side, back, sgn):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (глаза, шнуровка)."""
    marks = []
    kind = look.head
    lo, hi = _span(x)
    xc = int(round(x)) if side else None
    if kind in ("ninja", "mask", "kasa"):
        # Капюшон или маска, ниже ворот-шарф.
        c.ellipse(x, y, 3.6, 3.6, look.hood)
        if look.scarf is not None:
            c.rect(lo + 1, y + 4, hi - 1, y + 4, look.scarf)
        if not back:
            _slit(c, x, y, look, side, sgn, marks)
        if kind == "mask":
            # Красная повязка поверх маски, завязки на затылке.
            for xx in range(lo, hi + 1):
                if c.get(xx, y - 2) == look.hood:
                    c.set(xx, y - 2, RED)
            if side:
                bx = lo - 1 if sgn > 0 else hi + 1
                c.set(bx, y - 2, RED)
                c.set(bx - sgn, y - 1, RED)
                c.set(bx, y, RED)
            elif back:
                mid = (lo + hi) // 2
                c.rect(mid, y - 2, mid + 1, y - 1, RED)
                marks.append((mid - 1, y, RED))
                marks.append((mid + 2, y, RED))
                marks.append((mid - 1, y + 1, RED))
        elif kind == "kasa":
            # Соломенная шляпа конусом: шире головы, макушка узкая.
            mid = (lo + hi) / 2.0
            for dy, half in ((-4, 1.0), (-3, 3.0), (-2, 5.0)):
                c.rect(math.ceil(mid - half), y + dy, math.floor(mid + half), y + dy, GOLD)
            marks.append((int(mid), y - 4, BRASS))
            for xx in range(int(math.ceil(mid - 5.0)) + 1, int(math.floor(mid + 5.0)), 3):
                marks.append((xx, y - 2, BRASS))
        elif back:
            # Узел шарфа на затылке.
            mid = (lo + hi) // 2
            marks.append((mid, y + 2, NAVY))
            marks.append((mid + 1, y + 1, NAVY))
        return marks
    if kind == "sumo":
        # Широкое лицо, чёрные волосы шапкой и пучок на макушке.
        c.ellipse(x, y + 0.5, 3.9, 3.2, SKIN)
        rows = (-3, -2, -1, 0, 1) if back else (-3, -2)
        for dy in rows:
            for xx in range(lo - 1, hi + 2):
                if c.get(xx, y + dy) == SKIN:
                    c.set(xx, y + dy, DARK)
        if side:
            c.rect(min(xc, xc - sgn), y - 4, max(xc, xc - sgn), y - 4, DARK)
            if not back:
                c.set(xc - sgn * 3, y - 1, DARK)
                marks.append((xc + sgn * 2, y, K))
                marks.append((xc + sgn * 2, y + 1, K))
                marks.append((xc + sgn * 3, y + 2, TAN))
        else:
            mid = (lo + hi) // 2
            c.rect(mid, y - 4, mid + 1, y - 4, DARK)
            if not back:
                for ex in (lo + 2, hi - 2):
                    marks.append((ex, y, K))
                marks.append((mid, y + 2, TAN))
                marks.append((mid + 1, y + 2, TAN))
            else:
                marks.append((mid, y - 3, METAL))
                marks.append((mid + 1, y - 3, METAL))
        return marks
    # Самурай: шлем куполом, назатыльник шире головы, золотой полумесяц, красная полумаска.
    c.ellipse(x, y + 0.5, 3.2, 3.0, SKIN)
    for dy, cut in ((-3, 1), (-2, 0), (-1, 0)):
        c.rect(lo + cut, y + dy, hi - cut, y + dy, DARK)
    if side:
        # Назатыльник за головой, рог полумесяца вперёд.
        bx = xc - sgn * 3
        c.rect(min(bx, bx - sgn), y, max(bx, bx - sgn), y + 2, DARK)
        c.set(xc, y, DARK) if back else None
        c.set(xc + sgn, y - 4, GOLD)
        c.set(xc + sgn * 2, y - 4, GOLD)
        c.set(xc - sgn, y - 4, GOLD)
        if back:
            for dy in (0, 1, 2):
                for xx in range(lo, hi + 1):
                    if c.get(xx, y + dy) == SKIN:
                        c.set(xx, y + dy, DARK)
            marks.append((bx, y + 1, RED))
        else:
            for dy in (2, 3):
                for xx in range(lo, hi + 1):
                    if c.get(xx, y + dy) == SKIN:
                        c.set(xx, y + dy, RED)
            marks.append((xc + sgn * 2, y, K))
            marks.append((bx, y + 1, RED))
    else:
        c.rect(lo - 1, y, lo, y + 2, DARK)
        c.rect(hi, y, hi + 1, y + 2, DARK)
        for xx in (lo + 1, hi - 1):
            c.set(xx, y - 4, GOLD)
        c.rect(lo + 2, y - 3, hi - 2, y - 3, GOLD)
        if back:
            c.rect(lo, y, hi, y + 2, DARK)
            for xx in range(lo, hi + 1, 2):
                marks.append((xx, y + 1, RED))
        else:
            for dy in (2, 3):
                for xx in range(lo + 1, hi):
                    if c.get(xx, y + dy) == SKIN:
                        c.set(xx, y + dy, RED)
            for ex in (lo + 2, hi - 2):
                marks.append((ex, y, K))
            marks.append((lo - 1, y + 1, RED))
            marks.append((hi + 1, y + 1, RED))
    return marks


def _hand(c, look, x, y):
    """Кисть: у вратаря перчатка 2×2, у полевого ряд кожи на конце рукава."""
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)
    elif look.hand is not None:
        c.rect(x - 0.5, y + 1.0, x + 0.5, y + 1.0, look.hand)


def _tails_side(c, x, y, sgn, w):
    """Два конца шарфа назад от шеи (x, y): верхний длиннее, оба качаются на шаг."""
    for k, dy in ((0, 0), (1, 0), (2, w), (3, w)):
        c.set(x - sgn * k, y + dy, RED)
    for k, dy in ((0, 1), (1, 1 + max(w, 0)), (2, 2)):
        c.set(x - sgn * k, y + dy, RED)


def _hilt(c, x, y, sgn):
    """Рукоять меча наискось вверх и назад от плеча (x, y): оплётка тёмная, навершие золотом."""
    c.set(x, y, DARK)
    c.set(x - sgn, y - 1, DARK)
    c.set(x - sgn * 2, y - 2, GOLD)


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов и космоса: стойка и четыре кадра
    бега по восьми направлениям, подкат (у вратаря прыжок за мячом), лежит."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    wide = 1 if look.wide else 0
    if mode == "down":
        c.line(18, 17, 22, 15, look.thigh, 2)
        c.line(18, 19, 22, 20, look.thigh, 2)
        c.line(20, 16, 22, 15, look.sock, 2)
        c.line(20, 19.5, 22, 20, look.sock, 2)
        c.rect(21, 14, 22, 15, look.boot)
        c.rect(21, 20, 22, 21, look.boot)
        c.line(9, 15, 6, 12, look.limb, 2)
        c.rect(7, 16 - wide, 14, 20, look.shirt)
        if look.trim is not None:
            c.rect(10, 16, 10, 20, look.trim)
        if look.lapel is not None:
            c.line(8, 17, 11, 20, look.lapel, 1)
        if look.belt is not None:
            c.rect(14, 16 - wide, 14, 20, look.belt)
        c.rect(15, 16 - wide, 17, 20, look.shorts)
        if look.tails:
            # Шарф упал на землю перед головой.
            for x, y in ((6, 21), (5, 22), (4, 22), (3, 22), (7, 22), (8, 22)):
                c.set(x, y, RED)
        if look.sword:
            _hilt(c, 9, 15, -1)
        marks = _head(c, 4, 18, look, True, False, 1)
        if look.keeper:
            c.rect(5, 11, 6, 12, look.glove)
        elif look.hand is not None:
            c.rect(5, 11, 6, 11, look.hand)
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
        if look.keeper:
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.thigh, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.thigh, 2)
            for q in (0.0, 1.0):
                ex, ey = tx - ux * 6.0 - uy * 3.0 * q, ty - uy * 6.0 + 1.0 - q + ux * 3.0 * q
                c.rect(ex - 0.5, ey - 0.5, ex + 0.5, ey + 0.5, look.boot)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, look.shirt, 5)
            c.line(tx - ux, ty - uy, tx, ty, look.shorts, 5)
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
        fx, fy = cx + ux * 8.0, cy + uy * 8.0
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, look.thigh_far, 2 + wide)
        c.line(cx, cy, fx, fy, look.thigh, 2 + wide)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, look.sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, look.boot)
        hx, hy = round(tx - ux * 3.0), round(ty - uy * 3.0 - 2.0)
        if look.tails:
            # Шарф летит за головой против хода.
            c.line(hx - ux * 3.0, hy + 3.0, hx - ux * 8.0 - uy * 1.0, hy + 2.0 - uy * 4.0, RED, 1)
            c.line(hx - ux * 3.0, hy + 4.0, hx - ux * 6.0 + uy * 2.0, hy + 5.0 - uy * 3.0, RED, 1)
        c.line(tx, ty, cx, cy, look.shirt, 5 + wide)
        if look.trim is not None:
            c.line((tx + cx) / 2.0 - uy * 2.0, (ty + cy) / 2.0 + ux * 2.0, (tx + cx) / 2.0 + uy * 2.0, (ty + cy) / 2.0 - ux * 2.0, look.trim, 1)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, 5 + wide)
        ax, ay = tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0
        c.line(tx, ty, ax, ay, look.limb, 2)
        if look.hand is not None:
            c.rect(ax - 0.5, ay - 0.5, ax + 0.5, ay - 0.5, look.hand)
        marks = _head(c, hx, hy, look, side, back, sgn)
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
        for near, k in ((False, -s), (True, s)):
            hand = (11.5 - sgn * 4.0 * k, 15.0 - bob - abs(k))
            if not near:
                c.line(11.5, 11.0 - bob, hand[0], hand[1], look.limb_far, 2)
                _hand(c, look, hand[0], hand[1])
        for near, k in ((False, -s), (True, s)):
            limb = look.thigh if near else look.thigh_far
            if frame in (2, 4) and near == (frame == 2):
                foot = (11.5 + sgn * 1.0, 19.0)
                knee = (11.5 + sgn * 2.5, 18.0)
            else:
                foot = (11.5 + sgn * 4.0 * k, 21.0 - (2.0 if k < 0 else 0.0))
                knee = ((11.5 + foot[0]) / 2.0 + sgn * 1.0, (hip + foot[1]) / 2.0)
            c.line(11.5, hip, knee[0], knee[1], limb, 2 + wide)
            c.line(knee[0], knee[1], foot[0], foot[1], look.sock, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0, look.boot)
        rear = 8 if sgn > 0 else 15
        if look.sword:
            _hilt(c, rear, 9 - bob, sgn)
        if look.tails:
            _tails_side(c, rear, 10 - bob, sgn, (0, -1, 0, 1, 0)[frame])
        # Корпус: у сумоиста живот вперёд.
        x0 = 9 - (wide if sgn < 0 else 0)
        x1 = 14 + (wide if sgn > 0 else 0)
        c.rect(9, 10 - bob, 14, 15 - bob, look.shirt)
        if wide:
            c.rect(x0, 12 - bob, x1, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(9, 12 - bob, 14, 12 - bob, look.trim)
        if look.lapel is not None:
            fx0 = 13 if sgn > 0 else 10
            c.line(fx0, 10 - bob, fx0 - sgn, 13 - bob, look.lapel, 1)
        if look.belt is not None:
            c.rect(9, 15 - bob, 14, 15 - bob, look.belt)
        c.rect(x0, 16 - bob, x1, 17 - bob, look.shorts)
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        c.line(11.5, 11.0 - bob, hand[0], hand[1], look.limb, 2)
        _hand(c, look, hand[0], hand[1])
        marks = _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            lx0 = x - 0.5 - (wide if x < 12 else 0)
            lx1 = x + 0.5 + (wide if x > 12 else 0)
            c.rect(lx0, hip, lx1, foot_y - 2.0, look.thigh)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.boot)
        if look.sword:
            # Рукоять над плечом: спереди справа, со спины слева.
            if back:
                _hilt(c, 8, 9 - bob, 1)
            else:
                _hilt(c, 15, 9 - bob, -1)
        if look.tails and not back:
            # Спереди концы шарфа отлетают вбок от шеи.
            w = (0, -1, 0, 1, 0)[frame]
            for x, y in ((8, 9), (7, 9), (6, 9 + w), (5, 9 + w), (7, 10)):
                c.set(x, y - bob, RED)
        c.rect(8 - wide, 10 - bob, 15 + wide, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(8 - wide, 12 - bob, 15 + wide, 12 - bob, look.trim)
        if look.lapel is not None and not back:
            c.line(13, 10 - bob, 10, 13 - bob, look.lapel, 1)
        if look.belt is not None:
            c.rect(8 - wide, 15 - bob, 15 + wide, 15 - bob, look.belt)
            if not back:
                marks.append((11, 15 - bob, GOLD))
        c.rect(8 - wide, 16 - bob, 15 + wide, 17 - bob, look.shorts)
        if wide and not back:
            # Сумоист: тень под грудью и узел маваси спереди.
            marks.append((10, 12 - bob, TAN))
            marks.append((13, 12 - bob, TAN))
            marks.append((11, 14 - bob, TAN))
            c.rect(11, 18 - bob, 12, 18 - bob, look.shorts)
        if look.tails and back:
            # Со спины концы шарфа висят вдоль куртки.
            w = (0, -1, 0, 1, 0)[frame]
            for x, y in ((11, 10), (11, 11), (11, 12), (11 + w, 13), (13, 10), (13, 11), (13 - w, 12)):
                c.set(x, y - bob, RED)
        for x, k, out in ((6.5 - wide, -s, -1), (16.5 + wide, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            c.line(x, 11.0 - bob, hand[0], hand[1], look.limb, 2)
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


# Команды. Герой: синий костюм, красный шарф с концами, меч за спиной, белые обмотки, таби.
HERO = Look("ninja", SEA, NAVY, SEA, SEA, WHITE, belt=DARK, lapel=NAVY, hand=SKIN, scarf=RED, tails=True,
            sword=True)
# Вратарь героя: белая куртка и соломенная каса, синие штаны, красные перчатки.
KEEPER_HERO = Look("kasa", WHITE, GREY, WHITE, SEA, WHITE, belt=RED, lapel=GREY, glove=RED, keeper=True,
                   thigh=SEA, thigh_far=NAVY, scarf=RED)
# Чужой клан: красная куртка, чёрные маска, штаны и обмотки, красная повязка.
RIVAL_0 = Look("mask", RED, TAN, RED, DARK, DARK, belt=DARK, lapel=TAN, hand=SKIN, hood=DARK, scarf=DARK,
               thigh=DARK, thigh_far=DARK, boot=K)
# Сумоист: голый торс, красный маваси, босой.
RIVAL_1 = Look("sumo", SKIN, TAN, SKIN, RED, SKIN, boot=TAN, thigh=SKIN, thigh_far=TAN, wide=True)
# Самурай: чёрный лаковый доспех с красной шнуровкой, красные рукава, бурые штаны, серые поножи.
RIVAL_2 = Look("kabuto", RED, TAN, DARK, TAN, METAL, trim=RED, belt=GOLD, hand=SKIN, thigh=TAN, thigh_far=TAN)
# Вратарь чужого клана: жёлтая куртка, чёрная маска с повязкой, белые перчатки.
KEEPER_RIVAL = Look("mask", GOLD, BRASS, GOLD, DARK, DARK, belt=DARK, lapel=BRASS, glove=WHITE, keeper=True,
                    hood=DARK, scarf=RED, thigh=DARK, thigh_far=DARK, boot=K)


def ball(i):
    """Тэмари 8×8: белый шар в обводке, расшит клиньями (красный, белый, золотой, белый по
    кругу), в середине синий узел. Во втором кадре клинья повёрнуты на полшага: мяч «вращается»."""
    c = Canvas(8, 8)
    rot = (i % 2) * math.pi / 4.0
    for y in range(8):
        for x in range(8):
            ox, oy = x - 3.5, y - 3.5
            r = math.hypot(ox, oy)
            if r > 4.1:
                continue
            if r > 3.0:
                c.set(x, y, K)
                continue
            if r < 1.0:
                c.set(x, y, SEA)
                continue
            sector = int(math.floor((math.atan2(oy, ox) + rot + math.pi / 8.0) / (math.pi / 4.0))) % 4
            col = (RED, WHITE, GOLD, WHITE)[sector]
            if col == WHITE and ox + oy > 2.0:
                col = GREY
            c.set(x, y, col)
    return c


def deck():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): расчёсанный гравий,
    полосы по 32 (борозды вдоль и поперёк), крошка, два пятна мха."""
    c = Canvas(64, 64)
    rng = random.Random(5)
    for x in range(64):
        for y in range(64):
            if x < 32:
                v = DARK if x % 4 == 0 else METAL
            else:
                v = DARK if y % 4 == 2 else METAL
            c.set(x, y, v)
    for _ in range(90):
        x, y = rng.randrange(64), rng.randrange(64)
        if c.px[y][x] == METAL:
            c.px[y][x] = GREY
    for mx, my, rr in ((14, 20, 4.0), (47, 45, 5.0)):
        for y in range(64):
            for x in range(64):
                d = math.hypot(x - mx, (y - my) * 1.3)
                if d <= rr:
                    c.px[y][x] = VIOLET if (x - mx) + (y - my) < 1 else PLUM
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
        "soccer_grass": deck(),
    }


# --- Поле и аут ---------------------------------------------------------------------------------
# Тайлы 64×64 бесшовные, в своих палитрах. Поле это сумеречный серо-сиреневый гравий: на нём
# читаются и синие ниндзя, и красный клан, и белая разметка демки. Аут это тёмный пруд.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def _wrap_dist(a, b):
    d = abs(a - b) % T
    return min(d, T - d)


# Камни сада: центр, радиус камня, число кругов вокруг.
_STONES = ((17, 44, 3.2, 2), (50, 13, 2.4, 2))
# Кленовые листья на гравии: (x, y, поворот).
_LEAVES = ((6, 9, 0), (38, 30, 1), (27, 58, 0), (58, 49, 1), (44, 3, 1))


def gravel():
    """Сад камней: гравий расчёсан граблями, полосы по 32 (как полосы газона): в тёмной борозды
    идут вдоль, в светлой поперёк. Вокруг двух камней борозды кругами, на камнях мох, на гравии
    редкая крошка и кленовые листья.
    Палитра: 0 глубокая тень, 1 борозда, 2 гравий, 3 светлый гравий, 4 гребень, 5 камень,
    6 блик камня, 7 тень мха, 8 мох, 9 лист, 10 тёмный лист."""
    pal = _pal(0x413C52, 0x5E5870, 0x6E6982, 0x7C7790, 0x9690AA, 0x4A4658, 0xA8A2B4, 0x2C5540, 0x5E9448,
               0xD9433A, 0x8E2C30)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            base = 2 if x < 32 else 3
            if x < 32:
                k = x % 4
            else:
                k = (y + 2) % 4
            # Борозда и гребень рядом: тень слева или сверху, свет за ней.
            c.px[y][x] = base - 1 if k == 0 else base + 1 if k == 1 and (x + y) % 3 else base
    rng = random.Random(23)
    for _ in range(int(T * T * 0.03)):
        x, y = rng.randrange(T), rng.randrange(T)
        v = c.px[y][x]
        c.px[y][x] = max(1, v - 1) if rng.random() < 0.5 else min(4, v + 1)
    for sx, sy, rr, rings in _STONES:
        reach = rr + 3.0 * rings + 1.5
        for y in range(int(sy - reach - 1), int(sy + reach + 2)):
            for x in range(int(sx - reach - 1), int(sx + reach + 2)):
                d = math.hypot(x - sx, (y - sy) * 1.15)
                if d > reach:
                    continue
                base = 2 if (x % T) < 32 else 3
                if d <= rr:
                    # Камень: мох сверху слева, тень снизу справа.
                    lit = (x - sx) + (y - sy)
                    v = 8 if lit < -2.0 else 7 if lit < -0.5 else 6 if lit < 0.6 else 5
                elif d <= rr + 1.0:
                    v = 0 if (x - sx) + (y - sy) > 0 else 1
                else:
                    k = int((d - rr - 1.0)) % 3
                    v = base - 1 if k == 1 else base + 1 if k == 2 else base
                _wrap(c, x, y, v)
    for x, y, turn in _LEAVES:
        # Лист клёна: крестик с черешком.
        for ox, oy in ((0, 0), (-1, 0), (1, 0), (0, -1)):
            _wrap(c, x + (ox if not turn else oy), y + (oy if not turn else ox), 9)
        _wrap(c, x + (0 if not turn else 1), y + (1 if not turn else 0), 10)
        _wrap(c, x + 1, y + 1, 0)
    return c, pal


# Кувшинки пруда: центр, радиус, цветок.
_PADS = ((13, 12, 3.6, True), (20, 17, 2.4, False), (47, 40, 3.2, False), (40, 53, 2.2, True))
# Блики заката на воде: (x, y, длина, фаза).
_GLINTS = ((30, 8, 4, 0), (34, 11, 6, 1), (29, 14, 3, 2), (55, 24, 4, 3), (5, 33, 5, 1), (9, 36, 3, 3),
           (26, 44, 4, 2), (58, 58, 4, 0), (17, 60, 3, 1))


def pond(frame):
    """Тёмный пруд вокруг поля: рябь волнами бежит по кадрам, блики заката мерцают, листья
    кувшинок с вырезом и цветами, под водой рыжий карп шевелит хвостом, плывёт кленовый лист.
    Палитра: 0 глубина, 1 вода, 2 рябь, 3 светлая рябь, 4 блик заката, 5 тень кувшинки,
    6 кувшинка, 7 цветок, 8 карп, 9 пятно карпа, 10 лист клёна, 11 яркий блик."""
    pal = _pal(0x0A0C20, 0x11183C, 0x1D2A5C, 0x3A4C92, 0xE97B52, 0x1C4636, 0x3F8048, 0xF7DDE0, 0xE06A32,
               0xF3EEE2, 0xC8362E, 0xFBDC92)
    c = Canvas(T, T)
    ph = frame * math.pi / 2.0
    for y in range(T):
        for x in range(T):
            # Рябь: длинные пологие волны, по кадрам фаза уходит на полный круг за четыре кадра.
            v = (math.sin((y * 4 + math.sin(x / 64.0 * 2 * math.pi * 2) * 5.0) / 64.0 * 2 * math.pi + ph) +
                 math.sin((x + y * 3) / 64.0 * 2 * math.pi * 2 - ph) * 0.6)
            cell = 1
            if v > 1.25 and (x + y // 2) % 3:
                cell = 2
            elif v < -1.1:
                cell = 0
            c.px[y][x] = cell
    # Карп под водой: тело вдоль диагонали, хвост по кадрам в две стороны.
    kx, ky = 44, 22
    for k, col in enumerate((9, 8, 8, 9, 8, 8)):
        _wrap(c, kx + k, ky + k // 2, col)
        if 0 < k < 5:
            _wrap(c, kx + k, ky + k // 2 + 1, 8)
    wag = (-1, 0, 1, 0)[frame]
    _wrap(c, kx + 6, ky + 3 + wag, 8)
    _wrap(c, kx + 7, ky + 3 + wag * 2, 8)
    _wrap(c, kx + 7, ky + 4 + wag * 2, 9)
    _wrap(c, kx - 1, ky, 3)
    for gx, gy, ln, tw in _GLINTS:
        t = (tw + frame) % 4
        if t == 3:
            continue
        for k in range(ln if t != 2 else max(2, ln - 2)):
            _wrap(c, gx + k + (1 if t == 2 else 0), gy, 11 if t == 0 and 0 < k < ln - 1 else 4)
    for px_, py_, rr, bloom in _PADS:
        for y in range(int(py_ - rr - 2), int(py_ + rr + 3)):
            for x in range(int(px_ - rr - 2), int(px_ + rr + 3)):
                ox, oy = x - px_, (y - py_) * 1.25
                d = math.hypot(ox, oy)
                if d <= rr:
                    # Вырез листа клином вправо вниз.
                    if ox > 0.5 and 0.0 <= oy <= ox * 0.7:
                        continue
                    _wrap(c, x, y, 5 if ox + oy > rr * 0.5 or d > rr - 0.9 and oy > 0 else 6)
                elif d <= rr + 1.0 and oy > 0 and c.px[y % T][x % T] in (1, 2):
                    _wrap(c, x, y, 0)
        if bloom:
            _wrap(c, px_ - 1, py_ - 1, 7)
            _wrap(c, px_, py_ - 1, 7)
            _wrap(c, px_ - 1, py_ - 2, 7)
            _wrap(c, px_ - 2, py_ - 1, 7)
            _wrap(c, px_ - 1, py_, 11)
    # Кленовый лист на воде, круг ряби от него дышит по кадрам.
    lx, ly = 10, 50
    rr = 3.0 + (frame % 2)
    for a in range(24):
        ang = a / 24.0 * 2 * math.pi
        if (a + frame) % 3 == 0:
            continue
        _wrap(c, round(lx + math.cos(ang) * rr * 1.3), round(ly + math.sin(ang) * rr * 0.8), 3 if math.sin(ang) < 0 else 2)
    for ox, oy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        _wrap(c, lx + ox, ly + oy, 10)
    return c, pal


def fields():
    """Тайлы поля и аута ниндзя → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = gravel()
    frames = [pond(f) for f in range(4)]
    return {
        "soccer_field_ninja": (cv, pal),
        "soccer_out_ninja": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    items = ninja16.shaded(sprites())
    items.update(fields())
    ninja16.save_sheet(path, items, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
