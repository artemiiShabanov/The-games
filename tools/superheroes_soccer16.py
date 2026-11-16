#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Супергерои» (#137): зеркало `space_soccer16.py` и
`pixel_soccer16.py`. Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов,
8 «лежит»; мяч 8×8 в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка
`sport_bit16.gd` ничего не заметила.

Команда героя это герои из `superheroes16.py`: синее трико, жёлтый плащ (в беге летит клином
назад, со спины закрывает её до колен), жёлтые сапоги, перчатки и пояс, звезда на груди, тёмные
волосы с хохолком вперёд, чёрная маска-домино с белым глазом. Соперники это зелёно-серые роботы
злодея трёх видов: приспешник (корпус-бочонок с обручами, один красный глаз в тёмной глазнице,
антенна с огоньком), телеголовый (квадратная серая голова-экран с усами антенны и жёлтыми
глазами, жёлтая полоса и пояс), громила (широкий, маленькая голова утоплена между двумя
выхлопными трубами, светящийся визор). Вратарь героя это напарник в белом трико с красным плащом
и светлыми волосами, вратарь соперника это жёлтый робот-охранник с мигалкой на макушке,
чёрно-жёлтой полосой «опасно» на груди и белыми клешнями. Мяч белый с жёлтой звездой и синим клином (при
качении звезда уходит вбок), поле это бетон крыши в закатных сумерках: плиты со швами, полосы
по 32, трещины, заплаты гудрона, решётка стока; вокруг улицы далеко внизу: крыши кварталов,
окна мигают, по улицам едут огни машин.

    python3 tools/superheroes_soccer16.py --preview thegames/debug/playtest/env/superheroes_soccer16.png

Лист выходит высоким, поэтому пишется тремя файлами: сам путь (команда героя и два соперника),
`_b` (третий соперник и вратари), `_c` (мяч и тайлы).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import superheroes16  # noqa: E402
from superheroes16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                           DARK, RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и одежды и вид головы. `limb`/`limb_far` это руки (рукав трико или
    стальной рычаг), `thigh`/`thigh_far` бёдра, `shirt`/`shorts` верх и низ, `sock` голени (у
    героя сапоги), `boot` ступни, `belt` пояс, `trim` полоса на груди, `hand` кисть полевого
    игрока, `glove` перчатки вратаря, `head` вид головы, `hair` цвет волос героя. Флаги рисунка:
    `cape` цвет плаща, `hoops` цвет обручей бочонка, `wide` громила, `pipes` выхлопные трубы
    над плечами, `emblem` знак на груди (`star`, `lamp`, `hazard`)."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, trim=None, glove=None, keeper=False,
                 thigh=None, thigh_far=None, boot=DARK, belt=None, hand=None, hair=DARK, cape=None,
                 hoops=None, wide=False, pipes=False, emblem=None):
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
        self.hair = hair
        self.cape = cape
        self.hoops = hoops
        self.wide = wide
        self.pipes = pipes
        self.emblem = emblem


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


def _head_hero(c, x, y, look, side, back, sgn, marks):
    """Герой: непокрытая голова, волосы шапкой, хохолок вперёд, маска-домино с белым глазом."""
    xl, xr = _cols(x, side)
    hair = look.hair
    c.ellipse(x, y, 3.6, 3.6, SKIN)
    _recolor(c, xl, xr, y - 3, y - 2, SKIN, hair)
    if side:
        # Хохолок торчит вперёд над лбом, затылок в волосах.
        c.rect(min(x + sgn, x + sgn * 3), y - 4, max(x + sgn, x + sgn * 3), y - 4, hair)
        if back:
            _recolor(c, xl, xr, y - 1, y + 1, SKIN, hair, lambda xx, yy: (xx - x) * sgn <= 1)
            return
        _recolor(c, xl, xr, y - 1, y + 1, SKIN, hair, lambda xx, yy: (xx - x) * sgn <= -2)
        c.set(x + sgn * 4, y + 1, SKIN)
        for k in range(0, 4):
            marks.append((x + sgn * k, y, K))
        marks.append((x + sgn * 2, y, WHITE))
        marks.append((x + sgn * 2, y + 2, TAN))
        return
    c.rect(xl + 4, y - 4, xl + 5, y - 4, hair)
    if back:
        # Затылок целиком в волосах, ниже шея и уши.
        _recolor(c, xl, xr, y - 1, y + 1, SKIN, hair, lambda xx, yy: xl < xx < xr or yy < y)
        return
    for xx in range(xl + 1, xr):
        marks.append((xx, y, K))
    marks.append((xl + 2, y, WHITE))
    marks.append((xr - 2, y, WHITE))
    marks.append((xl + 3, y + 2, TAN))
    marks.append((xl + 4, y + 2, TAN))


def _head_bot(c, x, y, look, side, back, sgn, marks):
    """Приспешник: купол бочонка без шеи, стальная крышка, антенна с огоньком набок, один
    красный глаз в тёмной глазнице. У охранника (`siren`) вместо антенны мигалка."""
    xl, xr = _cols(x, side)
    c.ellipse(x, y, 3.6, 3.6, look.shirt)
    c.rect(xl + 1, y + 3, xr - 1, y + 3, look.shirt)
    _recolor(c, xl, xr, y - 3, y - 3, look.shirt, METAL)
    if look.head == "siren":
        # Мигалка: красный колпак на стальном цоколе.
        m0 = int(x) - 1 if side else xl + 3
        top = max(1, y - 5)
        c.rect(m0, top, m0 + (2 if side else 1), y - 4, RED)
        marks.append((m0, top, WHITE))
    else:
        ax = int(x) - sgn if side else xl + 5
        # Огонёк не выше первой строки кадра: на шаге вверх антенна короче, обводка цела.
        top = max(1, y - 6)
        c.line(ax, y - 4, ax - (sgn if side else -1), top, DARK, 1)
        marks.append((ax - (sgn if side else -1), top, RED))
    if back:
        # Затылок: решётка охлаждения.
        for xx in range(xl + 2, xr - 1):
            marks.append((xx, y - 1, PLUM if look.shirt == VIOLET else DARK))
            marks.append((xx, y + 1, PLUM if look.shirt == VIOLET else DARK))
        return
    if side:
        for k in (1, 2, 3):
            for yy in (y - 1, y, y + 1):
                marks.append((x + sgn * k, yy, DARK))
        marks.append((x + sgn * 2, y, RED))
        marks.append((x + sgn * 3, y, RED))
        marks.append((x + sgn * 2, y - 1, RED))
        marks.append((x + sgn * 3, y - 1, WHITE))
    else:
        for xx in range(xl + 2, xr - 1):
            for yy in (y - 1, y, y + 1):
                marks.append((xx, yy, DARK))
        for xx in (xl + 3, xl + 4):
            marks.append((xx, y - 1, RED))
            marks.append((xx, y, RED))
        marks.append((xl + 3, y - 1, WHITE))


def _head_tv(c, x, y, look, side, back, sgn, marks):
    """Телеголовый: квадратная серая голова-экран, усы антенны, болты по бокам, жёлтые глаза."""
    xl, xr = _cols(x, side)
    c.rect(xl, y - 3, xr, y + 2, GREY)
    c.rect(xl + 2, y + 3, xr - 2, y + 3, METAL)
    mid = (xl + xr) // 2
    top = max(1, y - 6)
    c.line(mid, y - 4, mid - 2, top, DARK, 1)
    c.line(mid + 1, y - 4, mid + 3, top, DARK, 1)
    if back:
        # Задняя крышка: винты по углам и решётка.
        for xx in range(xl + 2, xr - 1):
            marks.append((xx, y - 1, METAL))
            marks.append((xx, y + 1, METAL))
        marks.append((xl + 1, y - 2, DARK))
        marks.append((xr - 1, y - 2, DARK))
        return
    if side:
        # Экран виден с торца: тёмная полоса у переднего края, один глаз.
        front = xr if sgn > 0 else xl
        for k in (0, 1, 2):
            for yy in range(y - 2, y + 2):
                marks.append((front - sgn * k, yy, DARK))
        marks.append((front - sgn, y - 1, GOLD))
        marks.append((front - sgn, y + 1, GOLD))
        marks.append((front - sgn * 4, y - 1, METAL))
        marks.append((front - sgn * 4, y, METAL))
    else:
        c.set(xl - 1, y, METAL)
        c.set(xr + 1, y, METAL)
        for xx in range(xl + 1, xr):
            for yy in range(y - 2, y + 2):
                marks.append((xx, yy, DARK))
        marks.append((xl + 2, y - 1, GOLD))
        marks.append((xr - 2, y - 1, GOLD))
        for xx in range(xl + 2, xr - 1):
            marks.append((xx, y + 1, GOLD if (xx - xl) % 2 == 0 else BRASS))


def _head_brute(c, x, y, look, side, back, sgn, marks):
    """Громила: маленькая приплюснутая голова утоплена в плечи, поперёк светящийся персиковый визор."""
    xl, xr = _cols(x, side)
    c.ellipse(x, y + 1.5, 3.4, 2.6, PLUM)
    c.rect(xl + 1, y + 3, xr - 1, y + 3, PLUM)
    if back:
        marks.append(((xl + xr) // 2, y + 1, METAL))
        marks.append(((xl + xr) // 2 + 1, y + 1, METAL))
        return
    if side:
        for k in (0, 1, 2, 3):
            marks.append((x + sgn * k, y + 1, SKY))
        marks.append((x + sgn * 3, y + 1, WHITE))
    else:
        for xx in range(xl + 1, xr):
            marks.append((xx, y + 1, SKY))
        marks.append((xl + 2, y + 1, WHITE))
        marks.append((xr - 2, y + 1, WHITE))


_HEADS = {"hero": _head_hero, "bot": _head_bot, "siren": _head_bot, "tv": _head_tv, "brute": _head_brute}


def _head(c, x, y, look, side, back, sgn):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (маска, глаза, огни)."""
    marks = []
    if side:
        x = int(round(x))
    _HEADS[look.head](c, x, int(y), look, side, back, sgn, marks)
    return marks


def _hand(c, look, x, y):
    """Кисть: у вратаря перчатка на два пикселя, у полевого кулак или клешня."""
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)
    elif look.hand is not None:
        c.rect(x - 0.5, y + 0.5, x + 0.5, y + 1.0, look.hand)


def _arm(c, x0, y0, x1, y1, col):
    """Рука стоящего игрока: отрезок чуть толще двух пикселей, чтобы отвесная рука шла сплошной
    полосой от плеча до кисти, без разрывов между строками."""
    c.line(x0, y0, x1, y1, col, 2.5)


def _cape_side(c, look, frame, bob, sgn):
    """Плащ в профиль: в стойке висит за спиной до колен, в беге летит назад клином с вырезом и
    полощется по кадрам."""
    if frame == 0:
        pts = [(10, 10), (10, 15), (8, 19), (6, 19), (7, 14), (8, 10)]
    else:
        wv = (-1, 0, 1, 0)[frame - 1]
        pts = [(10, 10 - bob), (3, 11 + wv), (5.5, 13.5 + wv), (3, 16 + wv), (10, 15 - bob)]
    if sgn < 0:
        pts = [(23 - x, y) for x, y in pts]
    c.poly(pts, look.cape)


def _emblem(look, side, back, sgn, bob, marks):
    """Знак на груди: ставится после обводки. Звезда героя, лампа приспешника, полоса «опасно»."""
    if back or look.emblem is None:
        return
    w = 1 if look.wide else 0
    if look.emblem == "star":
        col = look.belt
        if side:
            f = 13 if sgn > 0 else 10
            for x, y in ((f, 11), (f - sgn, 12), (f, 12), (f + sgn, 12), (f - sgn, 13), (f + sgn, 13)):
                marks.append((x, y - bob, col))
        else:
            for x, y in ((11, 11), (12, 11), (10, 12), (11, 12), (12, 12), (13, 12), (10, 13), (13, 13)):
                marks.append((x, y - bob, col))
    elif look.emblem == "lamp":
        if side:
            marks.append((14 if sgn > 0 else 9, 12 - bob, RED))
            marks.append((14 if sgn > 0 else 9, 13 - bob, RED))
        else:
            for x, y, v in ((11, 12, RED), (12, 12, RED), (11, 13, RED), (12, 13, DARK)):
                marks.append((x, y - bob, v))
    elif look.emblem == "hazard":
        x0, x1 = (9, 14) if side else (8, 15)
        for x in range(x0 - w, x1 + w + 1, 2):
            marks.append((x, 12 - bob, GOLD))


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов: стойка и четыре кадра бега по
    восьми направлениям, подкат (у вратаря прыжок за мячом), лежит."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    w = 1 if look.wide else 0
    if mode == "down":
        # Лежит на спине поперёк: голова слева, ноги справа, рука откинута, плащ расстелен.
        if look.cape is not None:
            c.poly([(7, 14), (15, 15), (18, 22), (7, 21)], look.cape)
        c.line(18, 17, 22, 15, look.sock, 2)
        c.line(18, 19, 22, 20, look.sock, 2)
        c.rect(21, 14, 22, 15, look.boot)
        c.rect(21, 20, 22, 21, look.boot)
        c.line(9, 15, 6, 12, look.limb, 2)
        c.rect(7, 16 - w, 14, 20 + w, look.shirt)
        if look.hoops is not None:
            c.rect(8, 16 - w, 8, 20 + w, look.hoops)
            c.rect(13, 16 - w, 13, 20 + w, look.hoops)
        if look.trim is not None:
            c.rect(10, 16 - w, 10, 20 + w, look.trim)
        if look.belt is not None:
            c.rect(14, 16 - w, 14, 20 + w, look.belt)
        c.rect(15, 16 - w, 17, 20 + w, look.shorts)
        if look.emblem == "star":
            for x, y in ((10, 18), (11, 17), (11, 18), (11, 19), (12, 17), (12, 19)):
                marks.append((x, y, look.belt))
        elif look.emblem == "lamp":
            marks.append((10, 18, RED))
            marks.append((11, 18, RED))
        elif look.emblem == "hazard":
            for y in range(16, 21, 2):
                marks.append((10, y, GOLD))
        # Широкие головы сдвинуты на пиксель, чтобы обводка не ушла за край.
        marks += _head(c, 4 if look.head == "hero" else 5, 18, look, True, False, 1)
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
            # Прыжок за мячом: руки в перчатках вытянуты вперёд, ноги сзади, плащ вьётся над ними.
            if look.cape is not None and not back:
                c.line(cx + ux, cy + uy - 1.0, tx - ux * 2.0, ty - uy * 2.0 - 4.0, look.cape, 3)
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.sock, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.sock, 2)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, look.shirt, body)
            if look.trim is not None:
                c.line(cx - uy * 2.0, cy + ux * 2.0, cx + uy * 2.0, cy - ux * 2.0, look.trim, 1)
            c.line(tx - ux, ty - uy, tx, ty, look.shorts, body)
            if look.cape is not None and back:
                c.line(cx + ux, cy + uy, tx - ux * 2.0, ty - uy * 2.0, look.cape, 3)
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
        # Подкат по ходу: нога вытянута вперёд, вторая согнута, тело сзади низко, плащ бьётся
        # над спиной.
        if look.cape is not None and not back:
            c.line(tx + ux, ty + uy - 1.0, cx - ux * 0.5, cy - uy * 0.5 - 4.5, look.cape, 3)
        fx, fy = cx + ux * 8.0, cy + uy * 8.0
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, look.thigh_far, 2)
        c.line(cx, cy, fx, fy, look.thigh, 2)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, look.sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, look.boot)
        c.line(tx, ty, cx, cy, look.shirt, body)
        if look.hoops is not None:
            c.line(tx + ux - uy * 3.0, ty + uy + ux * 3.0, tx + ux + uy * 3.0, ty + uy - ux * 3.0, look.hoops, 1)
        if look.trim is not None:
            c.line(tx + ux * 2.0 - uy * 3.0, ty + uy * 2.0 + ux * 3.0, tx + ux * 2.0 + uy * 3.0, ty + uy * 2.0 - ux * 3.0,
                   look.trim, 1)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, body)
        if look.belt is not None:
            c.line(cx - ux * 2.0 - uy * 2.0, cy - uy * 2.0 + ux * 2.0, cx - ux * 2.0 + uy * 2.0, cy - uy * 2.0 - ux * 2.0,
                   look.belt, 1)
        if look.cape is not None and back:
            c.line(tx, ty, cx - ux, cy - uy, look.cape, 3)
        ax, ay = tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0
        c.line(tx, ty, ax, ay, look.limb, 2)
        if look.hand is not None:
            c.set(ax, ay, look.hand)
        # Широкая голова и антенна не выходят за край кадра.
        hx = min(max(round(tx - ux * 3.0), 5), 18)
        hy = max(round(ty - uy * 3.0 - 2.0), 7 if look.head in ("bot", "tv", "siren") else 5)
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
        if look.cape is not None:
            _cape_side(c, look, frame, bob, sgn)
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
            c.line(knee[0], knee[1], foot[0], foot[1], look.sock, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0,
                   look.boot)
        if look.pipes:
            # Выхлопная труба за плечом, из неё уголёк.
            px = 7 if sgn > 0 else 16
            c.rect(px, 6 - bob, px, 11 - bob, METAL)
            marks.append((px, 6 - bob, DARK))
        c.rect(9 - w, 10 - bob, 14 + w, 15 - bob, look.shirt)
        if look.hoops is not None:
            c.rect(9 - w, 11 - bob, 14 + w, 11 - bob, look.hoops)
            c.rect(9 - w, 14 - bob, 14 + w, 14 - bob, look.hoops)
        if look.trim is not None:
            c.rect(9 - w, 12 - bob, 14 + w, 12 - bob, look.trim)
        if look.belt is not None:
            c.rect(9 - w, 15 - bob, 14 + w, 15 - bob, look.belt)
        c.rect(9 - w, 16 - bob, 14 + w, 17 - bob, look.shorts)
        _emblem(look, True, back, sgn, bob, marks)
        _arm(c, 11.5, 11.0 - bob, near_hand[0], near_hand[1], look.limb)
        _hand(c, look, near_hand[0], near_hand[1])
        marks += _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        if look.cape is not None and not back:
            # Анфас плащ за спиной: видны только концы подола по бокам от бёдер.
            c.poly([(7, 13 - bob), (9, 13 - bob), (9, 19 - bob), (6 + s, 19 - bob)], look.cape)
            c.poly([(14, 13 - bob), (16, 13 - bob), (17 + s, 19 - bob), (14, 19 - bob)], look.cape)
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.thigh)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.boot)
        if look.pipes:
            for px in (6, 17):
                c.rect(px, 6 - bob, px, 10 - bob, METAL)
                marks.append((px, 6 - bob, DARK))
        c.rect(8 - w, 10 - bob, 15 + w, 15 - bob, look.shirt)
        if look.hoops is not None:
            c.rect(8 - w, 11 - bob, 15 + w, 11 - bob, look.hoops)
            c.rect(8 - w, 14 - bob, 15 + w, 14 - bob, look.hoops)
        if look.trim is not None:
            c.rect(8 - w, 12 - bob, 15 + w, 12 - bob, look.trim)
        if look.belt is not None:
            c.rect(8 - w, 15 - bob, 15 + w, 15 - bob, look.belt)
        c.rect(8 - w, 16 - bob, 15 + w, 17 - bob, look.shorts)
        _emblem(look, False, back, sgn, bob, marks)
        if look.cape is not None and back:
            # Со спины плащ закрывает её до колен, подол зубцами уходит в сторону шага.
            hem = 19 - bob
            c.poly([(8, 10 - bob), (15, 10 - bob), (16 + s, hem), (7 + s, hem)], look.cape)
            for x in (9 + s, 12 + s, 14 + s):
                c.px[hem][x] = None
            dark = superheroes16.SHADOW.get(look.cape, DARK)
            for yy in range(12 - bob, hem):
                marks.append((10, yy, dark))
            for yy in range(13 - bob, hem - 1):
                marks.append((13, yy, dark))
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


# Команды. Герой: синее трико, жёлтые плащ, пояс, сапоги и перчатки, звезда на груди.
HERO = Look("hero", SEA, NAVY, SEA, SEA, GOLD, thigh=SEA, thigh_far=NAVY, boot=BRASS, belt=GOLD, hand=GOLD,
            cape=GOLD, emblem="star")
# Вратарь героя: напарник в белом трико с красным плащом и поясом, волосы светлые.
KEEPER_HERO = Look("hero", WHITE, GREY, WHITE, WHITE, RED, glove=RED, keeper=True, thigh=WHITE, thigh_far=GREY,
                   boot=RED, belt=RED, hair=BRASS, cape=RED, emblem="star")
# Приспешник: бочонок с обручами, красный глаз и лампа, стальные ноги-поршни.
RIVAL_0 = Look("bot", METAL, DARK, VIOLET, PLUM, GREY, thigh=METAL, thigh_far=DARK, boot=METAL, hand=GREY,
               hoops=PLUM, emblem="lamp")
# Телеголовый: серая голова-экран, жёлтая полоса и пояс, жёлтые голени.
RIVAL_1 = Look("tv", VIOLET, PLUM, VIOLET, DARK, GOLD, trim=GOLD, thigh=METAL, thigh_far=DARK, boot=METAL,
               belt=BRASS, hand=GREY)
# Громила: широкий корпус, трубы над плечами, светящийся персиковый визор и полоса.
RIVAL_2 = Look("brute", VIOLET, PLUM, VIOLET, DARK, METAL, trim=SKY, thigh=PLUM, thigh_far=DARK, boot=METAL,
               hand=GREY, wide=True, pipes=True)
# Вратарь соперника: жёлтый робот-охранник с мигалкой, чёрно-жёлтая полоса «опасно», белые клешни.
KEEPER_RIVAL = Look("siren", METAL, DARK, GOLD, DARK, GREY, trim=DARK, glove=WHITE, keeper=True, thigh=METAL,
                    thigh_far=DARK, boot=METAL, emblem="hazard")


# Мяч со звездой 8×8: тёмный обод, белая кожа, жёлтая звезда, синий клин, серая тень снизу. Два
# кадра: звезда к камере и ушла вверх-влево, клин вышел справа снизу (при качении мяч
# «вращается»). o обод, W кожа, G звезда, g тень звезды, b клин, s тень.
BALL_MAPS = (
    ("..oooo..",
     ".oWWWWo.",
     "oWWGGWWo",
     "oWGGGGbo",
     "oWWGGWbo",
     "oWGssGso",
     ".osssso.",
     "..oooo.."),
    ("..oooo..",
     ".oGGWWo.",
     "oGGGGWWo",
     "oWGGWWWo",
     "oGWWGbbo",
     "osWWbbso",
     ".ossbso.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "W": WHITE, "G": GOLD, "g": BRASS, "b": SEA, "s": GREY}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def deck():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): бетонная плитка крыши
    вперевязку 16×8, полосы по 32 светлее и темнее, сколы и жёлтые метки разметки."""
    c = Canvas(64, 64)
    for y in range(64):
        row = y // 8
        off = 0 if row % 2 == 0 else 8
        for x in range(64):
            light = x < 32
            seam = y % 8 == 7 or (x + off) % 16 == 0
            if seam:
                v = DARK if light else NAVY
            elif y % 8 == 0:
                v = GREY if light else METAL
            else:
                v = METAL if light else DARK
            c.set(x, y, v)
    rng = random.Random(11)
    for _ in range(26):
        x, y = rng.randrange(64), rng.randrange(64)
        if y % 8 not in (0, 7):
            c.set(x, y, DARK if x < 32 else K)
    for x, y in ((5, 20), (37, 52)):
        c.rect(x, y, x + 5, y + 1, GOLD)
        c.rect(x + 2, y, x + 3, y + 1, BRASS)
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
# Тайлы 64×64 бесшовные, в своих палитрах. Поле это тёмный сумеречный бетон: на нём читаются и
# синие герои с жёлтым, и светлые зелёно-серые роботы, и белая разметка демки.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def rooftop():
    """Бетон крыши на закате: сиренево-серые плиты 64×32 вперевязку, полосы по 32 (как полосы
    газона), крошка, трещины, заплаты гудрона с тёплым бликом, решётка стока, жёлтая метка.
    Палитра: 0 глубокая тень, 1 тень и швы, 2 бетон, 3 светлый бетон, 4 блик кромки, 5 тёплый
    отсвет заката, 6 жёлтая краска."""
    pal = _pal(0x221A30, 0x2F2540, 0x3D3252, 0x473B5E, 0x6A5C80, 0x8A5468, 0xB88C3A)
    c = Canvas(T, T)
    rng = random.Random(47)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    # Крошка: чаще тёмная, изредка светлая.
    for _ in range(int(T * T * 0.08)):
        x, y = rng.randrange(T), rng.randrange(T)
        base = 2 if x < 32 else 3
        c.px[y][x] = base - 1 if rng.random() < 0.65 else base + 1
    # Заплаты гудрона: тёмное пятно, по верхней кромке отсвет заката.
    for cx, cy, rx, ry in ((14, 46, 5.0, 3.0), (49, 13, 4.0, 2.6)):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                q = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if q <= 1.0:
                    _wrap(c, x, y, 1 if (x * 7 + y * 3) % 5 else 0)
                elif q <= 1.5 and y < cy and (x + y) % 2 == 0:
                    _wrap(c, x, y, 5)
    # Швы плит: по горизонтали через 32, по вертикали вперевязку; под швом светлая кромка.
    for x in range(T):
        for y0 in (0, 32):
            c.px[y0][x] = 1
            if x % 7 != 3:
                c.px[y0 + 1][x] = 4 if x >= 32 else 3
    for y in range(1, 32):
        c.px[y][0] = 1
        c.px[y + 32][32] = 1
    # Трещины: ломаные от шва вглубь плиты.
    for x0, y0, steps in ((22, 2, 13), (44, 34, 11), (8, 33, 7)):
        x, y = x0, y0
        for k in range(steps):
            _wrap(c, x, y, 0)
            y += 1
            x += rng.choice((-1, 0, 0, 1))
            if k == steps // 2:
                _wrap(c, x + 1, y, 0)
                _wrap(c, x + 2, y - 1, 0)
    # Решётка стока: тёмный квадрат с прутьями и светлой рамкой снизу справа.
    gx, gy = 40, 50
    for y in range(6):
        for x in range(6):
            _wrap(c, gx + x, gy + y, 0 if x % 2 == 0 else 1)
    for k in range(7):
        _wrap(c, gx + k, gy + 6, 4)
        _wrap(c, gx + 6, gy + k, 4)
        _wrap(c, gx + k - 1, gy - 1, 1)
        _wrap(c, gx - 1, gy + k - 1, 1)
    # Старая жёлтая метка, стёртая через пиксель.
    for k in range(9):
        if k % 4 != 3:
            _wrap(c, 6 + k, 14, 6)
            _wrap(c, 6 + k, 15, 6 if k % 2 else 5)
    # Заклёпки по углам плит.
    for x, y in ((3, 4), (60, 4), (35, 36), (28, 36), (3, 29), (60, 29), (35, 61), (28, 61)):
        _wrap(c, x, y, 0)
        _wrap(c, x, y - 1, 4)
    return c, pal


# Кварталы внизу: (x, y, ширина, глубина, высота стены, тон крыши, надстройка). Тайл это один
# квартал 52×52 между улицами, улицы шириной 12 идут крестом через середину тайла.
_ROOFS = (
    (40, 40, 22, 15, 5, 2, "tank"),
    (0, 40, 24, 12, 4, 1, "vent"),
    (40, 60, 14, 22, 6, 1, "sign"),
    (56, 58, 30, 9, 3, 2, "vent"),
    (60, 72, 26, 14, 4, 1, "pad"),
)
STREET0, STREET1 = 26, 37


def streets(frame):
    """Улицы далеко внизу: крыши кварталов с южной стеной в огнях окон, надстройки (бак, короба,
    неоновая вывеска, площадка с крестом), крест улиц с пунктиром и зеброй, фары и стоп-огни
    машин едут по 8 пикселей на кадр (через 4 кадра лента сходится), окна мигают.
    Палитра: 0 чернота улиц, 1 тёмная крыша, 2 крыша, 3 кромка крыши, 4 стена, 5 горящее окно,
    6 тусклое окно, 7 фары, 8 стоп-огни, 9 неон, 10 разметка."""
    pal = _pal(0x0B0916, 0x17122B, 0x221A3C, 0x3A2C58, 0x100C20, 0xFFD23A, 0xA8641E, 0xFFF2D0, 0xE43A32,
               0xEF6F7C, 0x322A52)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 0
    rng = random.Random(77)
    for x0, y0, w, d, hgt, tone, top in _ROOFS:
        # Крыша: заливка, светлая кромка сверху и слева, редкая крошка.
        for y in range(d):
            for x in range(w):
                v = tone
                if y == 0 or x == 0:
                    v = 3
                elif (x * 5 + y * 3 + x0) % 11 == 0:
                    v = 1 if tone == 2 else 2
                _wrap(c, x0 + x, y0 + y, v)
        # Южная стена под крышей: окна сеткой, часть горит, часть мигает по кадрам.
        for y in range(hgt):
            for x in range(w):
                v = 4
                if y % 2 == 0 and x % 2 == 1 and 0 < x < w - 1 and y < hgt - 1:
                    r = rng.random()
                    if r < 0.34:
                        v = 5
                    elif r < 0.5:
                        v = 6
                    elif r < 0.6:
                        v = 5 if (frame + x) % 4 < 2 else 4
                _wrap(c, x0 + x, y0 + d + y, v)
        cx, cy = x0 + w // 2, y0 + d // 2
        if top == "tank":
            # Водяной бак: круг с бликом и тенью.
            for y in range(-3, 4):
                for x in range(-3, 4):
                    if x * x + y * y <= 10:
                        _wrap(c, cx + x, cy + y, 3 if x + y < 0 else 1)
            _wrap(c, cx - 1, cy - 1, 10)
            for k in range(4):
                _wrap(c, cx + 4 + k, cy + 2 + k // 2, 4)
        elif top == "vent":
            # Короба вентиляции: два ящика с тенью справа снизу.
            for bx in (cx - 6, cx + 3):
                for y in range(3):
                    for x in range(4):
                        _wrap(c, bx + x, cy - 1 + y, 3 if y == 0 else 10)
                for x in range(1, 5):
                    _wrap(c, bx + x, cy + 2, 4)
        elif top == "sign":
            # Неоновая вывеска вдоль края: трубка мигает через кадр.
            for y in range(3, d - 3):
                _wrap(c, x0 + w - 3, y0 + y, 9 if (y + frame) % 4 else 4)
                _wrap(c, x0 + w - 4, y0 + y, 4)
            for y in range(4, d - 4, 3):
                _wrap(c, x0 + 3, y0 + y, 10)
                _wrap(c, x0 + 4, y0 + y, 10)
        elif top == "pad":
            # Площадка героя: кольцо и крест, по углам сигнальные огни по очереди.
            for a in range(32):
                _wrap(c, cx + round(math.cos(a * math.pi / 16.0) * 5.0), cy + round(math.sin(a * math.pi / 16.0) * 5.0), 10)
            for k in range(-2, 3):
                _wrap(c, cx + k, cy, 3)
                _wrap(c, cx, cy + k, 3)
            for i, (ox, oy) in enumerate(((-7, -5), (7, -5), (7, 5), (-7, 5))):
                _wrap(c, cx + ox, cy + oy, 8 if i == frame else 4)
    # Улицы: крест, тротуарная кромка, пунктир осевой, зебра у перекрёстка.
    for k in range(T):
        for q in range(STREET0, STREET1 + 1):
            c.px[q][k] = 0
            c.px[k][q] = 0
    for k in range(T):
        if not STREET0 - 1 <= k <= STREET1 + 1:
            if k % 8 < 4:
                c.px[(STREET0 + STREET1) // 2][k] = 10
                c.px[k][(STREET0 + STREET1) // 2] = 10
    for q in range(STREET0 + 1, STREET1, 2):
        for z in (STREET0 - 4, STREET0 - 3, STREET1 + 3, STREET1 + 4):
            c.px[q][z] = 10
            c.px[z][q] = 10
    # Машины: в каждой полосе две на тайл через 32, фары по ходу, стоп-огни сзади.
    step = frame * 8
    for lane, way, start in ((STREET0 + 2, 1, 5), (STREET1 - 3, -1, 20)):
        for n in range(2):
            p = (start + n * 32 + way * step) % T
            for q in (lane, lane + 1):
                _wrap(c, p, q, 7)
                _wrap(c, p + way, q, 5 if q == lane else 6)
                _wrap(c, p - way * 3, q, 8)
                _wrap(c, q, p + 11, 7)
                _wrap(c, q, p + 11 - way, 5 if q == lane else 6)
                _wrap(c, q, p + 11 + way * 3, 8)
    return c, pal


def fields():
    """Тайлы поля и аута супергероев → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = rooftop()
    frames = [streets(f) for f in range(4)]
    return {
        "soccer_field_superheroes": (cv, pal),
        "soccer_out_superheroes": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    items = superheroes16.shaded(sprites())
    items.update(fields())
    # Лист целиком выше полутора тысяч пикселей: три файла, `_b` и `_c` рядом с первым.
    root, ext = os.path.splitext(path)
    groups = (("", ("soccer_hero", "soccer_rival_0", "soccer_rival_1")),
              ("_b", ("soccer_rival_2", "soccer_keeper_hero", "soccer_keeper_rival")),
              ("_c", ("soccer_ball", "soccer_grass", "soccer_field_superheroes", "soccer_out_superheroes")))
    for suffix, keys in groups:
        superheroes16.save_sheet(root + suffix + ext, {k: items[k] for k in keys}, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
