#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Динозавры» (#144): зеркало `space_soccer16.py` и
`pixel_soccer16.py`. Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов,
8 «лежит»; мяч 8×8 в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка
`sport_bit16.gd` ничего не заметила: ступни, бёдра и кисти стоят в тех же точках.

Команда героя это пещерные люди в оранжевой пятнистой шкуре через плечо, с лохматой копной и
костью в волосах, босые. Соперники это прямоходящие ящеры трёх видов, у каждого хвост и своя
голова: зелёный раптор с длинной мордой, жёлтый ящер с красным гребнем, бирюзовый толстолобый с
костяным куполом. Вратарь героя в белой мамонтовой шкуре с красными обмотками на кистях, вратарь
ящеров мятный с костяными когтями. Мяч это яйцо динозавра в крапинку, поле это плита тёмного
лавового камня с трещинами и отпечатками, вокруг течёт лава.

    python3 tools/dinosaurs_soccer16.py --preview thegames/debug/playtest/env/dinosaurs_soccer16.png
        [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dinosaurs16  # noqa: E402
from dinosaurs16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                         DARK, RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и вид головы. `limb`/`limb_far` это руки и ноги (у человека кожа, у
    ящера чешуя), `shirt`/`shorts` корпус и бёдра (шкура или чешуя), `sock` голень, `foot` ступня,
    `belly` светлое брюхо ящера, `spot` пятна шкуры или полосы по хребту, `glove` кисти вратаря,
    `head` вид головы, `tail` есть ли хвост, `crest` цвет гребня или купола."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, foot, belly=None, spot=None, glove=None,
                 keeper=False, tail=False, crest=None):
        self.head = head
        self.limb = limb
        self.limb_far = limb_far
        self.shirt = shirt
        self.shorts = shorts
        self.sock = sock
        self.foot = foot
        self.belly = belly
        self.spot = spot
        self.glove = glove
        self.keeper = keeper
        self.tail = tail
        self.crest = crest


def _cols(x):
    """Столбцы головы анфас: (левый глаз, правый глаз, левая середина, правая середина). Центр
    бывает на стыке пикселей (11.5) и на пикселе."""
    if x != int(x):
        m = int(math.floor(x))
        return m - 1, m + 2, m, m + 1
    x = int(x)
    return x - 2, x + 2, x, x


def _bone(c, x0, y0, x1, y1):
    """Кость в волосах наискось: нижний конец торчит у уха, верхний над макушкой. Концы с
    утолщением рисуются до обводки, середина возвращается точками поверх копны."""
    for x, y in ((x0, y0), (x0, y0 - 1), (x1, y1), (x1, y1 + 1)):
        c.set(x, y, WHITE)
    n = int(abs(x1 - x0))
    return [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n, WHITE) for k in range(n + 1)]


def _head_cave(c, x, y, side, back, sgn):
    """Пещерный человек: копна волос шире головы, чёлка до бровей, тяжёлая челюсть, кость в
    волосах торчит концами наружу."""
    marks = []
    if side:
        # Копна сдвинута к затылку, прядь на шее.
        c.ellipse(x - sgn * 0.8, y - 0.5, 4.2, 3.8, DARK)
        marks += _bone(c, x - sgn * 5, y, x + sgn * 2, y - 5)
        c.rect(x - sgn * 4, y + 3, x - sgn * 4, y + 4, DARK)
        if back:
            # Вполоборота от камеры: видна только скула.
            c.rect(x + sgn * 3, y + 1, x + sgn * 3, y + 2, SKIN)
            c.set(x + sgn * 4, y + 1, SKIN)
        else:
            c.ellipse(x + sgn * 1.2, y + 1, 2.8, 2.8, SKIN)
            c.rect(min(x + sgn, x + sgn * 3), y + 2, max(x + sgn, x + sgn * 3), y + 3, SKIN)
            for yy in range(y - 4, y):
                for xx in range(x - 6, x + 7):
                    if c.get(xx, yy) == SKIN:
                        c.set(xx, yy, DARK)
            c.set(x + sgn * 4, y + 1, SKIN)
            marks.append((x + sgn * 2, y, K))
            marks.append((x + sgn * 3, y + 3, TAN))
        return marks
    le, re, ml, mr = _cols(x)
    c.ellipse(x, y - 0.5, 4.4, 3.8, DARK)
    if back:
        marks += _bone(c, re + 3, y, le - 2, y - 5)
    else:
        marks += _bone(c, le - 3, y, re + 2, y - 5)
    c.set(le - 2, y + 3, DARK)
    c.set(re + 2, y + 3, DARK)
    if back:
        # Затылок: пряди свисают на шею.
        c.rect(ml - 1, y + 3, mr + 1, y + 3, DARK)
        return marks
    c.rect(le, y, re, y + 2, SKIN)
    c.rect(le + 1, y + 3, re - 1, y + 3, SKIN)
    marks.append((le + 0, y + 1, K))
    marks.append((re - 0, y + 1, K))
    marks.append((ml, y + 3, TAN))
    marks.append((mr, y + 3, TAN))
    return marks


def _head_dino(c, x, y, look, side, back, sgn):
    """Ящер трёх видов: `raptor` узкая длинная морда с зубами, `crest` короткая морда и гребень,
    `dome` широкая голова с костяным куполом и шипами по краю."""
    marks = []
    kind = look.head
    col = look.limb
    far = look.limb_far
    if side:
        if kind == "raptor":
            c.ellipse(x - sgn * 0.5, y, 3.0, 3.0, col)
            if back:
                c.rect(min(x + sgn * 2, x + sgn * 4), y - 1, max(x + sgn * 2, x + sgn * 4), y, col)
            else:
                c.rect(min(x + sgn * 2, x + sgn * 5), y, max(x + sgn * 2, x + sgn * 5), y + 2, col)
                c.set(x + sgn * 5, y, None)
                for k in (2, 3, 4):
                    marks.append((x + sgn * k, y + 2, K))
                marks.append((x + sgn * 3, y + 2, WHITE))
                marks.append((x + sgn, y - 1, GOLD))
                marks.append((x + sgn * 2, y - 1, K))
            for k in (1, 3):
                marks.append((x - sgn * k, y - 2, far))
        elif kind == "crest":
            # Гребень полукругом над затылком.
            c.ellipse(x - sgn * 1.0, y - 2.5, 3.4, 3.2, look.crest)
            c.ellipse(x, y + 0.5, 3.2, 2.8, col)
            if back:
                c.rect(min(x + sgn * 2, x + sgn * 3), y, max(x + sgn * 2, x + sgn * 3), y + 1, col)
            else:
                c.rect(min(x + sgn * 2, x + sgn * 4), y, max(x + sgn * 2, x + sgn * 4), y + 2, col)
                marks.append((x + sgn * 3, y + 2, K))
                marks.append((x + sgn * 4, y + 2, K))
                marks.append((x + sgn * 2, y, K))
            marks.append((x - sgn * 2, y - 4, WHITE))
            marks.append((x - sgn * 0, y - 5, WHITE))
        else:
            c.ellipse(x, y + 1, 3.6, 2.8, col)
            c.ellipse(x - sgn * 0.5, y - 1.5, 3.2, 2.8, look.crest)
            # Шипы по краю купола на затылке.
            c.set(x - sgn * 4, y + 1, GOLD)
            c.set(x - sgn * 4, y - 1, GOLD)
            if not back:
                c.rect(min(x + sgn * 3, x + sgn * 4), y + 1, max(x + sgn * 3, x + sgn * 4), y + 2, col)
                marks.append((x + sgn * 2, y + 1, K))
                marks.append((x + sgn * 4, y + 2, K))
            marks.append((x - sgn * 1, y - 3, WHITE))
        return marks
    le, re, ml, mr = _cols(x)
    if kind == "raptor":
        c.ellipse(x, y - 0.5, 3.6, 3.0, col)
        if back:
            for yy in (y - 3, y - 1, y + 1):
                marks.append((ml, yy, far))
                marks.append((mr, yy, far))
            return marks
        # Морда клином вниз.
        c.rect(le + 1, y + 2, re - 1, y + 3, col)
        c.rect(ml, y + 4, mr, y + 4, col)
        marks.append((le, y - 1, GOLD))
        marks.append((re, y - 1, GOLD))
        marks.append((le + 1, y - 1, K))
        marks.append((re - 1, y - 1, K))
        marks.append((ml, y + 4, K))
        marks.append((mr, y + 4, K))
        marks.append((le + 1, y + 3, WHITE))
        marks.append((re - 1, y + 3, WHITE))
    elif kind == "crest":
        # Два гребня рогами над головой.
        c.line(le + 1, y - 2, le - 1, y - 5, look.crest, 2)
        c.line(re - 1, y - 2, re + 1, y - 5, look.crest, 2)
        c.ellipse(x, y, 3.6, 3.0, col)
        if back:
            marks.append((ml, y - 1, far))
            marks.append((mr, y + 1, far))
            return marks
        c.rect(le + 1, y + 3, re - 1, y + 3, col)
        marks.append((le, y, K))
        marks.append((re, y, K))
        marks.append((ml, y + 3, K))
        marks.append((mr, y + 3, K))
    else:
        c.ellipse(x, y + 1, 4.2, 2.8, col)
        c.ellipse(x, y - 1.5, 3.2, 2.6, look.crest)
        # Шипы венцом по бокам купола.
        c.set(le - 2, y - 1, GOLD)
        c.set(re + 2, y - 1, GOLD)
        c.set(le - 3, y + 1, GOLD)
        c.set(re + 3, y + 1, GOLD)
        marks.append((ml - 1, y - 3, WHITE))
        if back:
            return marks
        c.rect(le + 1, y + 4, re - 1, y + 4, col)
        marks.append((le, y + 2, K))
        marks.append((re, y + 2, K))
        marks.append((ml, y + 4, K))
        marks.append((mr, y + 4, K))
    return marks


def _head(c, x, y, look, side, back, sgn):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (глаза, зубы, кость)."""
    if x == int(x):
        x = int(x)
    y = int(y)
    if look.head == "cave":
        return _head_cave(c, x, y, side, back, sgn)
    return _head_dino(c, x, y, look, side, back, sgn)


def _glove(c, look, x, y):
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)
    elif look.tail:
        # Коготь на кисти ящера.
        c.set(x, y + 1.0, WHITE)


def _torso_front(c, look, bob, back, marks):
    """Корпус анфас и со спины: 8..15 × 10..17, как у зеркала."""
    c.rect(8, 10 - bob, 15, 15 - bob, look.shirt)
    c.rect(8, 16 - bob, 15, 17 - bob, look.shorts)
    if look.tail:
        if back:
            for yy in (11, 13, 15):
                marks.append((11, yy - bob, look.spot))
                marks.append((12, yy - bob, look.spot))
        else:
            c.rect(10, 11 - bob, 13, 16 - bob, look.belly)
            for yy in (13, 15):
                marks.append((10, yy - bob, look.spot))
                marks.append((13, yy - bob, look.spot))
        return
    # Шкура через одно плечо: второе голое, пятна, рваный подол между ног и по бокам.
    bare = ((13, 10), (14, 10), (15, 10), (14, 11), (15, 11), (15, 12)) if back else \
        ((8, 10), (9, 10), (10, 10), (8, 11), (9, 11), (8, 12))
    for x, y in bare:
        c.set(x, y - bob, SKIN)
    for x in (8, 11, 12, 15):
        c.set(x, 18 - bob, look.shorts)
    for x, y in ((13, 13), (12, 14), (10, 15), (9, 16), (14, 16)):
        marks.append(((23 - x) if back else x, y - bob, look.spot))


def _torso_side(c, look, bob, sgn, marks):
    """Корпус в профиль: 9..14 × 10..17."""
    c.rect(9, 10 - bob, 14, 15 - bob, look.shirt)
    c.rect(9, 16 - bob, 14, 17 - bob, look.shorts)
    front = 14 if sgn > 0 else 9
    rear = 9 if sgn > 0 else 14
    if look.tail:
        c.rect(min(front, front - sgn), 11 - bob, max(front, front - sgn), 16 - bob, look.belly)
        for yy in (11, 13, 15):
            marks.append((rear, yy - bob, look.spot))
        return
    for x, y in ((rear, 10), (rear + sgn, 10), (rear, 11)):
        c.set(x, y - bob, SKIN)
    for x in (9, 12, 14):
        c.set(x, 18 - bob, look.shorts)
    for x, y in ((front - sgn, 13), (front - sgn * 2, 14), (rear + sgn, 15), (front, 16)):
        marks.append((x, y - bob, look.spot))


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов: стойка и четыре кадра бега по
    восьми направлениям, подкат (у вратаря прыжок за мячом), лежит. У ящера добавлен хвост."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    if mode == "down":
        if look.tail:
            # Хвост задран вверх дугой.
            c.line(16, 16, 19, 12, look.limb, 2)
            c.line(19, 12, 21, 11, look.limb, 1)
        c.line(18, 17, 22, 15, look.limb, 2)
        c.line(18, 19, 22, 20, look.limb, 2)
        c.rect(21, 14, 22, 15, look.foot)
        c.rect(21, 20, 22, 21, look.foot)
        c.line(9, 15, 6, 12, look.limb, 2)
        c.rect(7, 16, 14, 20, look.shirt)
        c.rect(15, 16, 17, 20, look.shorts)
        if look.tail:
            c.rect(8, 17, 15, 19, look.belly)
            for x in (10, 13):
                marks.append((x, 17, look.spot))
                marks.append((x, 19, look.spot))
        else:
            # Голое плечо у головы, зубцы подола на бёдрах.
            c.rect(7, 16, 8, 17, SKIN)
            for y in (16, 18, 20):
                c.set(18, y, look.shorts)
            for x, y in ((10, 19), (12, 17), (13, 19), (15, 18)):
                marks.append((x, y, look.spot))
        marks += _head(c, 4, 18, look, False, False, 1)
        if look.keeper:
            c.rect(5, 11, 6, 12, look.glove)
        elif look.tail:
            c.set(5, 11, WHITE)
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
            if look.tail:
                c.line(tx, ty, tx - ux * 5.0 + uy * 3.0, ty - uy * 5.0 - ux * 3.0, look.limb, 2)
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.limb, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.limb, 2)
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
        if look.tail:
            # Хвост в сторону от дальней ноги, для равновесия.
            c.line(cx - ux, cy - uy, cx + uy * 4.0 - ux * 3.0, cy - ux * 4.0 - uy * 3.0, look.limb, 2)
            c.line(cx + uy * 4.0 - ux * 3.0, cy - ux * 4.0 - uy * 3.0, cx + uy * 5.0 - ux * 6.0, cy - ux * 5.0 - uy * 6.0, look.limb, 1)
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, look.limb_far, 2)
        c.line(cx, cy, fx, fy, look.limb, 2)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, look.sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, look.foot)
        c.line(tx, ty, cx, cy, look.shirt, 5)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, 5)
        if look.tail:
            c.line(tx + ux, ty + uy, cx, cy, look.belly, 2)
        else:
            marks.append((tx + ux * 2.0 + uy, ty + uy * 2.0 - ux, look.spot))
            marks.append((tx + ux * 4.0 - uy, ty + uy * 4.0 + ux, look.spot))
        c.line(tx, ty, tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0, look.limb, 2)
        marks += _head(c, round(tx - ux * 3.0), round(ty - uy * 3.0 - 2.0), look, side, back, sgn)
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
        if look.tail:
            # Хвост назад от крестца, кончик ходит в такт шагу.
            c.line(11.5 - sgn * 2.0, 16 - bob, 11.5 - sgn * 7.0, 18 - bob + s * 0.6, look.limb, 2)
            c.line(11.5 - sgn * 7.0, 18 - bob + s * 0.6, 11.5 - sgn * 9.5, 16 - bob + s, look.limb, 1)
        for near, k in ((False, -s), (True, s)):
            hand = (11.5 - sgn * 4.0 * k, 15.0 - bob - abs(k))
            if not near:
                c.line(11.5, 11.0 - bob, hand[0], hand[1], look.limb_far, 2)
                _glove(c, look, hand[0], hand[1])
        for near, k in ((False, -s), (True, s)):
            limb = look.limb if near else look.limb_far
            if frame in (2, 4) and near == (frame == 2):
                foot = (11.5 + sgn * 1.0, 19.0)
                knee = (11.5 + sgn * 2.5, 18.0)
            else:
                foot = (11.5 + sgn * 4.0 * k, 21.0 - (2.0 if k < 0 else 0.0))
                knee = ((11.5 + foot[0]) / 2.0 + sgn * 1.0, (hip + foot[1]) / 2.0)
            c.line(11.5, hip, knee[0], knee[1], limb, 2)
            c.line(knee[0], knee[1], foot[0], foot[1], look.sock if near else look.limb_far, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0, look.foot)
        _torso_side(c, look, bob, sgn, marks)
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        c.line(11.5, 11.0 - bob, hand[0], hand[1], look.limb, 2)
        _glove(c, look, hand[0], hand[1])
        marks += _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        if look.tail and not back:
            # Лицом к камере: хвост выглядывает сбоку из-за бёдер.
            c.line(14, 17 - bob, 18, 20 - bob, look.limb_far, 2)
            c.line(18, 20 - bob, 20 + s, 18 - bob, look.limb_far, 1)
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.limb)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.foot)
        _torso_front(c, look, bob, back, marks)
        if look.tail and back:
            # Спиной к камере: хвост поверх бёдер свисает между ног и качается.
            c.line(11.5, 16 - bob, 11.5 + s * 1.5, 21, look.shirt, 2)
            c.set(11.5 + s * 2.0 + 0.5, 22, look.shirt)
            marks.append((11.5 + s * 0.8 + 0.5, 19, look.spot))
        for x, k, out in ((6.5, -s, -1), (16.5, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            c.line(x, 11.0 - bob, hand[0], hand[1], look.limb, 2)
            _glove(c, look, hand[0], hand[1])
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


# Команды. Герой: оранжевая шкура в тёмных пятнах, голые руки и ноги, босые ступни.
HERO = Look("cave", SKIN, TAN, RED, RED, SKIN, TAN, spot=DARK)
# Вратарь героя: белая мамонтовая шкура и красные обмотки на кистях, чтобы не путался с полевыми.
KEEPER_HERO = Look("cave", SKIN, TAN, WHITE, WHITE, SKIN, TAN, spot=METAL, glove=RED, keeper=True)
# Ящеры: зелёный раптор, жёлтый с красным гребнем, бирюзовый толстолобый с костяным куполом.
RIVAL_0 = Look("raptor", VIOLET, PLUM, VIOLET, VIOLET, VIOLET, PLUM, belly=GOLD, spot=PLUM, tail=True)
RIVAL_1 = Look("crest", GOLD, BRASS, GOLD, GOLD, GOLD, BRASS, belly=WHITE, spot=DARK, tail=True, crest=RED)
RIVAL_2 = Look("dome", SEA, NAVY, SEA, SEA, SEA, NAVY, belly=SKY, spot=NAVY, tail=True, crest=WHITE)
# Вратарь ящеров: мятный раптор с костяными когтями-перчатками.
KEEPER_RIVAL = Look("raptor", AQUA, SEA, AQUA, AQUA, AQUA, SEA, belly=WHITE, spot=SEA, glove=WHITE, keeper=True,
                    tail=True)


# Яйцо динозавра 8×8: кремовая скорлупа, острый конец вверх, зелёные и бурые крапины бегут по
# кругу (два кадра, при качении яйцо «вращается»). o обвод, w скорлупа, g тень, s блик,
# t бурая крапина, v зелёная.
BALL_MAPS = (
    ("..oooo..",
     ".owsswo.",
     "owstwwwo",
     "owwwwvwo",
     "owvwwwgo",
     "ogwwtwgo",
     ".oggggo.",
     "..oooo.."),
    ("..oooo..",
     ".owsswo.",
     "owswwvwo",
     "owtwwwwo",
     "owwwvwgo",
     "ogtwwggo",
     ".oggggo.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "w": WHITE, "g": GREY, "s": SKY, "t": TAN, "v": VIOLET}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def slab():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): плита лавового камня,
    полосы по 32 светлее и темнее, ломаные трещины, галька и осколки кости."""
    c = Canvas(64, 64)
    for y in range(64):
        for x in range(64):
            c.px[y][x] = METAL if x < 32 else DARK
    rng = random.Random(44)
    # Трещины: ломаные сверху вниз и поперёк, с переходом через край тайла.
    for k in range(5):
        x, y = rng.randrange(64), rng.randrange(64)
        for _ in range(rng.randint(14, 26)):
            c.px[y % 64][x % 64] = DARK if x % 64 < 32 else K
            if k % 2:
                x += 1
                y += rng.choice((-1, 0, 0, 1))
            else:
                y += 1
                x += rng.choice((-1, 0, 0, 1))
    for _ in range(26):
        x, y = rng.randrange(64), rng.randrange(64)
        c.px[y][x] = GREY if x < 32 else METAL
    for _ in range(5):
        x, y = rng.randrange(1, 62), rng.randrange(1, 62)
        c.px[y][x] = WHITE
        c.px[y][x + 1] = GREY
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
        "soccer_grass": slab(),
    }


# --- Поле и аут ---------------------------------------------------------------------------------
# Тайлы 64×64 бесшовные, в своих палитрах. Поле это тёмный тёплый камень: на нём читаются и
# оранжевые шкуры, и зелёные, жёлтые и бирюзовые ящеры, и белая разметка демки.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def basalt():
    """Плита лавового камня: буро-лиловый, полосы по 32 (как полосы газона), мелкая крошка,
    тонкие ломаные трещины, отпечаток аммонита и трёхпалые следы, редкая галька.
    Палитра: 0 трещина, 1 тень, 2 камень, 3 светлый камень, 4 блик, 5 отпечаток."""
    pal = _pal(0x2C1E22, 0x40303A, 0x54424A, 0x64525A, 0x8E7A7E, 0x4A3840)
    c = Canvas(T, T)
    rng = random.Random(57)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    for _ in range(int(T * T * 0.09)):
        x, y = rng.randrange(T), rng.randrange(T)
        base = c.px[y][x]
        c.px[y][x] = base - 1 if rng.random() < 0.65 else min(base + 1, 3 if x < 32 else 4)
    # Трещины: ломаные с редкими ответвлениями, идут через край тайла.
    for k in range(4):
        x, y = rng.randrange(T), rng.randrange(T)
        for step in range(rng.randint(16, 30)):
            _wrap(c, x, y, 0)
            if step % 7 == 3:
                _wrap(c, x + 1, y + (1 if k % 2 else 0), 1)
            if k % 2:
                x += 1
                y += rng.choice((-1, 0, 0, 0, 1))
            else:
                y += 1
                x += rng.choice((-1, 0, 0, 0, 1))
    # Отпечаток аммонита: спираль в полтора витка.
    ax, ay = 46, 20
    for i in range(40):
        a = i / 40.0 * math.pi * 3.2
        r = 0.8 + i / 40.0 * 4.6
        _wrap(c, ax + math.cos(a) * r, ay + math.sin(a) * r, 5 if i % 5 else 1)
    # Трёхпалые следы цепочкой наискось.
    for fx, fy in ((10, 44), (17, 52), (24, 42)):
        for dx, dy in ((0, 0), (0, 1), (-1, -1), (1, -1), (-2, -2), (2, -2), (0, -2), (0, -3)):
            _wrap(c, fx + dx, fy + dy, 1 if (dx, dy) != (0, 0) else 0)
    for _ in range(6):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 4)
        _wrap(c, x + 1, y, 3)
        _wrap(c, x + 1, y + 1, 0)
        _wrap(c, x, y + 1, 1)
    return c, pal


def lava(frame):
    """Лава вокруг поля: тёмные плиты корки, между ними жилы от багрового к жёлтому, жилы медленно
    ползут по кадрам, пузыри вздуваются и лопаются. Палитра: 0 корка, 1 светлая корка,
    2 багровый, 3 оранжевый, 4 жёлтый, 5 раскалённый."""
    pal = _pal(0x24100E, 0x3C1A14, 0x8A2412, 0xD84C1C, 0xF4A030, 0xFFE890)
    c = Canvas(T, T)
    t = frame * math.pi / 2.0
    w = 2.0 * math.pi / T
    for y in range(T):
        for x in range(T):
            f = (math.sin(x * w * 2.0 + 1.3 * math.sin(y * w + t)) +
                 math.sin(y * w * 3.0 + 1.1 * math.sin(x * w * 2.0 - t) + 0.7) +
                 0.6 * math.sin((x + y) * w * 2.0 + t))
            a = abs(f)
            if a < 0.07:
                v = 4
            elif a < 0.17:
                v = 3
            elif a < 0.30:
                v = 2
            else:
                # Корка: шашечка светлых крапин ближе к середине плит.
                v = 1 if a > 1.1 and (x * 5 + y * 3) % 7 < 2 else 0
            c.px[y][x] = v
    rng = random.Random(23)
    for k in range(7):
        x, y = rng.randrange(T), rng.randrange(T)
        ph = (k + frame) % 4
        if c.px[y][x] < 2:
            continue
        # Пузырь: точка, кольцо, брызги, пусто.
        if ph == 0:
            _wrap(c, x, y, 5)
        elif ph == 1:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                _wrap(c, x + dx, y + dy, 5)
            _wrap(c, x, y, 4)
        elif ph == 2:
            for dx, dy in ((2, -1), (-2, -1), (0, -2)):
                _wrap(c, x + dx, y + dy, 4)
    return c, pal


def fields():
    """Тайлы поля и аута динозавров → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = basalt()
    frames = [lava(f) for f in range(4)]
    return {
        "soccer_field_dinosaurs": (cv, pal),
        "soccer_out_dinosaurs": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path, keys=None):
    items = dinosaurs16.shaded(sprites())
    items.update(fields())
    if keys:
        items = {k: items[k] for k in keys}
    dinosaurs16.save_sheet(path, items, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        keys_ = None
        for arg in sys.argv[1:]:
            if arg.startswith("--keys="):
                keys_ = [k for k in arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], keys_)
