#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Офис» (#138): зеркало `space_soccer16.py` и `pixel_soccer16.py`.
Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов, 8 «лежит»; мяч 8×8
в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка `sport_bit16.gd` ничего
не заметила: ступни, бёдра и кисти стоят в тех же точках.

Команда героя это клерки из `office16.py`: белая рубашка, красный галстук (в беге летит за
плечо), очки, голубой бейдж, синие брюки и белые носки поверх. Соперники это сотрудники трёх
видов, у каждого своя голова и форма: усач в чёрном костюме с красным галстуком и в рыжих
ботинках, охранник в синей форме и фуражке с козырьком и кокардой, лысый бухгалтер в буром
кардигане с зелёным козырьком-тенью. Вратарь героя в жёлтом жилете со светоотражающей полосой и
в голубых перчатках, вратарь соперников усач в красном пиджаке и белых перчатках. Мяч это жёлтый
мяч-антистресс с рожицей (рожица переворачивается, мяч «катится»), поле это ковролин плитками,
вокруг опенспейс сверху: столы с мигающими мониторами, кресла, фикус, коробка бумаги.

    python3 tools/office_soccer16.py --preview thegames/debug/playtest/env/office_soccer16.png
        [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import office16  # noqa: E402
from office16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                      DARK, RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: вид головы и цвета. `limb`/`limb_far` это рукава и штанины (ближние и
    дальние), `shirt`/`shorts`/`sock` верх, пояс брюк и голень, `shoe` ботинки, `hand` кисти
    (у вратаря вместо них перчатки `glove`), `trim` полоса на груди, `tie` галстук (`fly`: в беге
    летит за плечо, иначе заправлен под пиджак), `collar` белый воротник, `badge` значок на груди,
    `head` вид головы: clerk, suit, guard, visor."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, shoe=DARK, hand=SKIN, trim=None, glove=None,
                 keeper=False, tie=None, fly=False, collar=False, badge=None, leg=None, leg_far=None):
        self.head = head
        self.limb = limb
        self.limb_far = limb_far
        self.leg = limb if leg is None else leg
        self.leg_far = limb_far if leg_far is None else leg_far
        self.shirt = shirt
        self.shorts = shorts
        self.sock = sock
        self.shoe = shoe
        self.hand = hand
        self.trim = trim
        self.glove = glove
        self.keeper = keeper
        self.tie = tie
        self.fly = fly
        self.collar = collar
        self.badge = badge


def _hair(c, x0, x1, y0, y1, v=DARK):
    """Волосы: красит только пиксели головы (кожу) в прямоугольнике."""
    for yy in range(int(y0), int(y1) + 1):
        for xx in range(int(x0), int(x1) + 1):
            if c.get(xx, yy) == SKIN:
                c.set(xx, yy, v)


def _head(c, x, y, look, side, back, sgn):
    """Голова. `x` целый: в профиль это центр, анфас и со спины голова занимает x-3..x+4.
    Возвращает точки, которые ставятся после обводки и тени (очки, глаза, усы, кокарда)."""
    marks = []
    kind = look.head
    x = int(x)
    y = int(y)
    cx = x if side else x + 0.5
    lo, hi = (x - 4, x + 4) if side else (x - 3, x + 4)
    c.ellipse(cx, y, 3.6, 3.6, SKIN)
    if kind in ("clerk", "suit"):
        # Тёмная шапка волос; у клерка чуб торчит вперёд и вверх, у усача волосы зализаны и с
        # висками.
        if back:
            _hair(c, lo, hi, y - 4, y + 1)
        else:
            _hair(c, lo, hi, y - 4, y - 2)
            if side:
                for dx in (-4, -3, -2):
                    _hair(c, x + dx * sgn, x + dx * sgn, y - 1, y + 1)
            elif kind == "suit":
                _hair(c, lo, lo + 1, y - 1, y - 1)
                _hair(c, hi - 1, hi, y - 1, y - 1)
            else:
                _hair(c, lo, lo + 2, y - 1, y - 1)
        if kind == "clerk":
            if side:
                c.set(x + sgn * 2, y - 4, DARK)
                c.set(x + sgn * 3, y - 4, DARK)
                c.set(x + sgn * 4, y - 3, DARK)
            else:
                c.set(x + 2, y - 4, DARK)
                c.set(x + 3, y - 4, DARK)
    elif kind == "guard":
        # Фуражка: высокая тулья шире головы, тёмный околыш, козырёк вперёд.
        _hair(c, lo, hi, y - 4, y - 1 if not back else y)
        c.rect(lo + 1, y - 5, hi - 1, y - 3, SEA)
        c.rect(lo, y - 4, hi, y - 3, SEA)
        c.rect(lo + 1, y - 2, hi - 1, y - 2, NAVY)
        if side:
            c.rect(min(x + sgn * 3, x + sgn * 6), y - 2, max(x + sgn * 3, x + sgn * 6), y - 2, NAVY)
        elif not back:
            c.rect(lo, y - 2, hi, y - 2, NAVY)
            c.rect(lo + 1, y - 1, hi - 1, y - 1, NAVY)
    else:
        # Бухгалтер: лысина, седые виски, зелёный козырёк на резинке.
        if back:
            _hair(c, lo, hi, y + 1, y + 2, GREY)
            _hair(c, lo, lo, y - 1, y, GREY)
            _hair(c, hi, hi, y - 1, y, GREY)
            c.rect(lo + 1, y - 2, hi - 1, y - 2, PLUM)
        elif side:
            for dx in (-4, -3):
                _hair(c, x + dx * sgn, x + dx * sgn, y - 1, y + 1, GREY)
            c.rect(x - 3, y - 2, x + 3, y - 2, PLUM)
            c.rect(min(x + sgn * 1, x + sgn * 6), y - 2, max(x + sgn * 1, x + sgn * 6), y - 2, VIOLET)
            c.rect(min(x + sgn * 3, x + sgn * 6), y - 1, max(x + sgn * 3, x + sgn * 6), y - 1, VIOLET)
        else:
            _hair(c, lo, lo, y - 1, y + 1, GREY)
            _hair(c, hi, hi, y - 1, y + 1, GREY)
            c.rect(lo - 1, y - 2, hi + 1, y - 2, VIOLET)
            c.rect(lo, y - 1, hi, y - 1, VIOLET)
    if back:
        return marks
    if kind == "guard":
        if side:
            marks.append((x + sgn * 2, y - 4, GOLD))
        else:
            marks.append((x, y - 4, GOLD))
            marks.append((x + 1, y - 4, GOLD))
    if side:
        if kind == "clerk":
            # Очки: линза и оправа с дужкой.
            marks.append((x + sgn * 2, y, SKY))
            marks.append((x + sgn * 3, y, SKY))
            marks.append((x + sgn * 1, y, K))
            marks.append((x, y, K))
        else:
            marks.append((x + sgn * 2, y, K))
        if kind in ("suit", "visor"):
            for k in (1, 2, 3):
                marks.append((x + sgn * k, y + 2, DARK if kind == "suit" else GREY))
    else:
        if kind == "clerk":
            for ex in (x - 2, x - 1, x + 2, x + 3):
                marks.append((ex, y, SKY))
            marks.append((x, y, K))
            marks.append((x + 1, y, K))
            marks.append((x - 3, y, K))
            marks.append((x + 4, y, K))
        else:
            marks.append((x - 1, y, K))
            marks.append((x + 2, y, K))
        if kind in ("suit", "visor"):
            for ex in range(x - 1, x + 3):
                marks.append((ex, y + 2, DARK if kind == "suit" else GREY))
    return marks


def _hand(c, look, x, y):
    """Кисть на конце руки; у вратаря перчатка."""
    c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove if look.keeper else look.hand)


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов: стойка и четыре кадра бега по
    восьми направлениям, подкат (у вратаря прыжок за мячом), лежит."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    if mode == "down":
        c.line(18, 17, 22, 15, look.leg, 2)
        c.line(18, 19, 22, 20, look.leg, 2)
        c.rect(21, 14, 22, 15, look.shoe)
        c.rect(21, 20, 22, 21, look.shoe)
        c.line(9, 15, 6, 12, look.limb, 2)
        c.rect(7, 16, 14, 20, look.shirt)
        if look.trim is not None:
            c.rect(10, 16, 10, 20, look.trim)
        if look.collar:
            c.rect(7, 17, 7, 19, WHITE)
        if look.tie is not None:
            # Галстук лежит на груди, у клерка кончик выбился на пол.
            c.rect(8, 18, 11, 18, look.tie)
            if look.fly:
                c.rect(9, 21, 11, 21, look.tie)
                c.set(9, 20, look.tie)
        if look.badge is not None:
            c.rect(12, 16, 13, 17, look.badge)
        c.rect(15, 16, 17, 20, look.shorts)
        marks = _head(c, 4, 18, look, True, False, 1)
        c.rect(5, 11, 6, 12, look.glove if look.keeper else look.hand)
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
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.leg, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.leg, 2)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, look.shirt, 5)
            if look.trim is not None:
                c.line(cx - ux - uy * 2.0, cy - uy + ux * 2.0, cx - ux + uy * 2.0, cy - uy - ux * 2.0, look.trim, 1)
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
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, look.leg_far, 2)
        c.line(cx, cy, fx, fy, look.leg, 2)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, look.sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, look.shoe)
        c.line(tx, ty, cx, cy, look.shirt, 5)
        if look.trim is not None:
            c.line(cx - ux * 3.0 - uy * 2.0, cy - uy * 3.0 + ux * 2.0, cx - ux * 3.0 + uy * 2.0, cy - uy * 3.0 - ux * 2.0, look.trim, 1)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, 5)
        ax, ay = tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0
        c.line(tx, ty, ax, ay, look.limb, 2)
        c.rect(ax - 0.5, ay - 0.5, ax + 0.5, ay + 0.5, look.hand)
        hx, hy = round(tx - ux * 3.0), round(ty - uy * 3.0 - 2.0)
        if look.tie is not None and look.fly:
            # Галстук в подкате летит назад, за голову.
            c.line(hx - ux * 3.0, hy - uy * 3.0 + 3.0, hx - ux * 7.0, hy - uy * 7.0 + 1.0, look.tie, 2)
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
            limb = look.leg if near else look.leg_far
            if frame in (2, 4) and near == (frame == 2):
                foot = (11.5 + sgn * 1.0, 19.0)
                knee = (11.5 + sgn * 2.5, 18.0)
            else:
                foot = (11.5 + sgn * 4.0 * k, 21.0 - (2.0 if k < 0 else 0.0))
                knee = ((11.5 + foot[0]) / 2.0 + sgn * 1.0, (hip + foot[1]) / 2.0)
            c.line(11.5, hip, knee[0], knee[1], limb, 2)
            c.line(knee[0], knee[1], foot[0], foot[1], look.sock, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0, look.shoe)
        front = 14 if sgn > 0 else 9
        rear = 9 if sgn > 0 else 14
        c.rect(9, 10 - bob, 14, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(9, 12 - bob, 14, 12 - bob, look.trim)
        if look.collar:
            c.set(front, 10 - bob, WHITE)
        if look.badge is not None:
            c.rect(front - sgn * 2, 12 - bob, front - sgn * 2, 13 - bob, look.badge)
        if look.tie is not None:
            if look.fly and frame != 0:
                # В беге галстук перекинут через плечо и хвостом торчит за спиной.
                c.rect(9, 10 - bob, 14, 10 - bob, look.tie)
                c.rect(min(rear, rear - sgn * 2), 10 - bob, max(rear, rear - sgn * 2), 10 - bob, look.tie)
                c.set(rear - sgn * 3, 9 - bob - (1 if s else 0), look.tie)
                c.set(rear - sgn * 3, 10 - bob, look.tie)
            else:
                c.rect(front, 11 - bob, front, 13 - bob if look.fly else 12 - bob, look.tie)
        c.rect(9, 16 - bob, 14, 17 - bob, look.shorts)
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        c.line(11.5, 11.0 - bob, hand[0], hand[1], look.limb, 2)
        _hand(c, look, hand[0], hand[1])
        marks = _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.leg)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.shoe)
        c.rect(8, 10 - bob, 15, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(8, 12 - bob, 15, 12 - bob, look.trim)
        if back:
            if look.collar:
                c.rect(10, 10 - bob, 13, 10 - bob, WHITE)
            if look.tie is not None and look.fly and frame != 0:
                # Со спины виден хвост галстука, улетевший за плечо.
                c.rect(13, 10 - bob, 14, 11 - bob, look.tie)
                c.rect(14 + s, 12 - bob, 14 + s, 13 - bob, look.tie)
        else:
            if look.collar:
                c.rect(10, 10 - bob, 13, 10 - bob, WHITE)
            if look.tie is not None:
                c.rect(11, 10 - bob, 12, 12 - bob, look.tie)
                if look.fly:
                    # Кончик качается в такт шагу.
                    c.rect(11 + s, 13 - bob, 12 + s, 14 - bob, look.tie)
            if look.badge is not None:
                c.rect(14, 11 - bob, 14, 12 - bob, look.badge)
        c.rect(8, 16 - bob, 15, 17 - bob, look.shorts)
        for x, k, out in ((6.5, -s, -1), (16.5, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            c.line(x, 11.0 - bob, hand[0], hand[1], look.limb, 2)
            _hand(c, look, hand[0], hand[1])
        marks += _head(c, 11, 6 - bob, look, False, back, sgn)
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


# Команды. Герой: клерк из основы, белая рубашка, летящий красный галстук, бейдж, синие брюки,
# белые носки поверх брюк (форма читается как футбольная).
HERO = Look("clerk", WHITE, GREY, WHITE, SEA, WHITE, tie=RED, fly=True, badge=AQUA, leg=SEA, leg_far=NAVY)
# Вратарь героя: жёлтый жилет со светоотражающей полосой, чтобы не путался с полевыми.
KEEPER_HERO = Look("clerk", WHITE, GREY, GOLD, SEA, WHITE, trim=GREY, glove=AQUA, keeper=True, leg=SEA,
                   leg_far=NAVY)
# Усач в чёрном костюме: воротник, красный галстук под пиджаком, рыжие ботинки.
RIVAL_0 = Look("suit", DARK, NAVY, DARK, DARK, DARK, shoe=BRASS, tie=RED, collar=True)
# Охранник: синяя форма, жёлтая полоса, фуражка.
RIVAL_1 = Look("guard", SEA, NAVY, SEA, NAVY, NAVY, shoe=DARK, trim=GOLD)
# Бухгалтер: бурый кардиган, зелёный козырёк, серые кеды.
RIVAL_2 = Look("visor", BRASS, DARK, BRASS, DARK, DARK, shoe=GREY, collar=True)
KEEPER_RIVAL = Look("suit", RED, DARK, RED, DARK, DARK, shoe=BRASS, collar=True, tie=GOLD, glove=WHITE,
                    keeper=True, leg=DARK, leg_far=NAVY)


# Мяч-антистресс 8×8: жёлтый поролоновый шарик с рожицей. Во втором кадре рожица перевёрнута:
# при качении мяч «вращается». o обод, g жёлтый, b тень, W блик, e глаза и рот.
BALL_MAPS = (
    ("..oooo..",
     ".ogWggo.",
     "ogegegbo",
     "ogegegbo",
     "oggggggo",
     "obeggebo",
     ".obeebo.",
     "..oooo.."),
    ("..oooo..",
     ".ogeego.",
     "ogeWgebo",
     "oggggggo",
     "ogegegbo",
     "obegegbo",
     ".obbbbo.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "g": GOLD, "b": BRASS, "W": WHITE, "e": DARK}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def carpet():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): ковролин плитками,
    полосы по 32 светлее и темнее, швы плиток и ворс крапом."""
    c = Canvas(64, 64)
    for x in range(64):
        for y in range(64):
            band = VIOLET if x < 32 else PLUM
            if x % 16 == 0 or y % 16 == 0:
                band = PLUM if band == VIOLET else NAVY
            elif (x * 3 + y * 5) % 11 == 0:
                band = AQUA if x < 32 else VIOLET
            c.set(x, y, band)
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
        "soccer_grass": carpet(),
    }


# --- Поле и аут ---------------------------------------------------------------------------------
# Тайлы 64×64 бесшовные, в своих палитрах. Ковролин средней тёмности: на нём читаются и белые
# рубашки, и чёрные костюмы, и белая разметка демки. Аут темнее поля, яркое в нём только мелочи.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def carpet_field():
    """Ковролин опенспейса: зелёно-бирюзовый, полосы по 32 (как полосы газона), плитки 32×32 со
    швом, ворс мелким крапом и короткими штрихами, следы от кружки кольцом, пара оброненных
    стикеров и скрепка.
    Палитра: 0 шов, 1 тень ворса, 2 ковролин, 3 светлый ковролин, 4 блик ворса, 5 след кофе,
    6 жёлтый стикер, 7 розовый стикер, 8 скрепка."""
    pal = _pal(0x1F4744, 0x2A5A56, 0x336A64, 0x3C7A72, 0x5C9E90, 0x4A5440, 0xE8C84E, 0xE07A9C, 0xC2CAD8)
    c = Canvas(T, T)
    rng = random.Random(42)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    # Ворс: крап темнее и светлее.
    for _ in range(int(T * T * 0.12)):
        x, y = rng.randrange(T), rng.randrange(T)
        base_ = c.px[y][x]
        c.px[y][x] = base_ - 1 if rng.random() < 0.6 else min(base_ + 1, 3 if x < 32 else 4)
    # Примятый ворс: короткие косые штрихи.
    for _ in range(16):
        x0, y0, ln = rng.randrange(T), rng.randrange(T), rng.randint(3, 6)
        for k in range(ln):
            _wrap(c, x0 + k, y0 + k // 2, 1 if (x0 + k) % T < 32 else 2)
    # Швы плиток: тёмная нитка, рядом светлая кромка.
    for i in range(T):
        for s0 in (0, 32):
            if (i // 2) % 8 != 3:
                _wrap(c, i, s0, 0 if i % T >= 32 else 1)
                _wrap(c, s0, i, 1)
    # Следы от кружки: кольцо с разрывом.
    for cx, cy, rr in ((17, 44, 3.0), (49, 13, 2.5)):
        for a in range(0, 360, 12):
            if 40 < a < 100:
                continue
            _wrap(c, round(cx + math.cos(math.radians(a)) * rr), round(cy + math.sin(math.radians(a)) * rr), 5)
    # Стикеры: квадратик с загнутым тёмным уголком и тенью.
    for sx, sy, v in ((43, 46, 6), (10, 14, 7)):
        for yy in range(3):
            for xx in range(3):
                _wrap(c, sx + xx, sy + yy, v)
        _wrap(c, sx + 2, sy + 2, 0)
        _wrap(c, sx + 3, sy + 3, 1)
    # Скрепка.
    for x, y in ((27, 25), (28, 24), (29, 24), (30, 25), (29, 26), (28, 26)):
        _wrap(c, x, y, 8)
    return c, pal


def openspace(frame):
    """Опенспейс вокруг поля, вид сверху: тёмная плитка, стол с монитором, клавиатурой, кружкой
    и стикерами, кресло, фикус в горшке, коробка бумаги, обронённые листы. По кадрам мигает
    экран (свет на столе) и лампочка системного блока.
    Палитра: 0 шов и тени, 1 плитка, 2 светлая плитка, 3 кофе, 4 дерево, 5 светлое дерево,
    6 серый пластик, 7 чёрный, 8 экран, 9 блик экрана, 10 бумага, 11 жёлтый, 12 обивка кресла,
    13 тёмная листва, 14 листва, 15 розовый, 16 красный, 17 картон, 18 тень бумаги."""
    pal = _pal(0x171A25, 0x272C3C, 0x30364A, 0x5A3A22, 0x74583A, 0x8E7048, 0x6A7284, 0x14141C,
               0x58B2DC, 0xC8EAF5, 0xDADDE6, 0xE8C84E, 0x314A92, 0x2A605C, 0x4F9C86, 0xD86A92,
               0xDA3A36, 0xA07A46, 0x9AA2B4)
    c = Canvas(T, T)
    rng = random.Random(7)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 0 if (x % 32 == 0 or y % 32 == 0) else 1
    for _ in range(90):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.px[y][x] == 1:
            c.px[y][x] = 2

    def rect(x0, y0, x1, y1, v):
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                _wrap(c, xx, yy, v)

    def disc(cx, cy, rx, ry, v):
        for yy in range(int(cy - ry - 1), int(cy + ry + 2)):
            for xx in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    _wrap(c, xx, yy, v)

    # Стол: тень снизу и справа, столешница с кромкой и волокном.
    rect(9, 7, 49, 27, 0)
    rect(8, 6, 47, 25, 4)
    rect(8, 6, 47, 6, 5)
    rect(8, 6, 8, 25, 5)
    for x, y, ln in ((12, 21, 7), (24, 23, 9), (38, 20, 6), (30, 13, 5), (11, 9, 4)):
        rect(x, y, x + ln, y, 5)
    # Монитор у дальнего края: чёрная планка, экран светит на стол.
    rect(19, 8, 36, 10, 7)
    rect(26, 7, 29, 7, 6)
    glow = (8, 9, 8, 8)[frame % 4]
    rect(20, 11, 35, 11, glow)
    for x in range(20, 36):
        if (x + frame) % 4 == 0:
            _wrap(c, x, 11, 9 if glow == 8 else 8)
    for x in range(21, 35, 2):
        _wrap(c, x + (frame % 2), 12, 5)
    # Клавиатура с рядами клавиш и мышь.
    rect(20, 15, 33, 19, 6)
    for yy in (16, 18):
        for x in range(21, 33, 2):
            _wrap(c, x, yy, 18)
    rect(23, 19, 30, 19, 0)
    rect(36, 16, 37, 18, 10)
    _wrap(c, 36, 16, 18)
    # Кружка с кофе и ручкой.
    disc(13, 12, 2.4, 2.4, 10)
    disc(13, 12, 1.2, 1.2, 3)
    _wrap(c, 16, 12, 10)
    _wrap(c, 15, 15, 0)
    # Стикеры и стопка бумаги с загнутым углом.
    rect(40, 9, 42, 11, 11)
    rect(43, 13, 45, 15, 15)
    _wrap(c, 42, 11, 3)
    rect(39, 18, 45, 23, 10)
    rect(40, 20, 44, 20, 18)
    rect(40, 22, 43, 22, 18)
    rect(39, 24, 45, 24, 0)
    # Системный блок под столом: торчит край с лампочкой.
    rect(10, 26, 16, 29, 7)
    rect(10, 26, 16, 26, 6)
    _wrap(c, 14, 28, 16 if frame % 4 == 2 else 14)
    # Кресло: пятилучье с колёсиками, сиденье, спинка дугой со стороны, дальней от стола.
    for a in range(5):
        ang = math.radians(90 + a * 72)
        for k in (5, 6, 7):
            _wrap(c, round(27 + math.cos(ang) * k), round(37 + math.sin(ang) * k), 7)
        _wrap(c, round(27 + math.cos(ang) * 8), round(37 + math.sin(ang) * 8), 6)
    disc(28, 38, 5.0, 4.6, 0)
    rect(22, 32, 32, 40, 12)
    rect(23, 31, 31, 31, 12)
    rect(23, 33, 31, 33, 8)
    rect(23, 34, 23, 38, 8)
    rect(20, 34, 20, 39, 7)
    rect(34, 34, 34, 39, 7)
    rect(21, 35, 21, 38, 6)
    rect(33, 35, 33, 38, 6)
    rect(21, 41, 33, 43, 7)
    rect(22, 44, 32, 44, 7)
    rect(22, 41, 32, 41, 6)
    # Фикус в горшке: тень, горшок с землёй, листья лучами со светлой жилкой.
    disc(54, 51, 4.6, 4.2, 0)
    disc(52, 49, 3.6, 3.4, 17)
    disc(52, 49, 2.6, 2.4, 3)
    for a in range(0, 360, 60):
        ang = math.radians(a + 20)
        for k in range(1, 7):
            lx, ly = 52 + math.cos(ang) * k, 49 + math.sin(ang) * k
            disc(lx, ly, 1.3 if 2 <= k <= 4 else 0.7, 1.3 if 2 <= k <= 4 else 0.7, 13)
        for k in range(1, 6):
            _wrap(c, round(52 + math.cos(ang) * k), round(49 + math.sin(ang) * k), 14)
    _wrap(c, 52, 49, 11)
    # Коробка бумаги: картон, клапаны, пачка внутри.
    rect(7, 47, 19, 57, 0)
    rect(6, 46, 18, 56, 17)
    rect(6, 46, 18, 46, 5)
    rect(8, 48, 16, 54, 10)
    rect(8, 50, 16, 50, 18)
    rect(8, 52, 16, 52, 18)
    rect(6, 51, 7, 51, 4)
    rect(17, 51, 18, 51, 4)
    # Обронённые листы и скомканный комок.
    rect(30, 53, 36, 58, 0)
    rect(29, 52, 35, 57, 10)
    rect(30, 54, 34, 54, 18)
    rect(30, 56, 33, 56, 18)
    for k in range(5):
        rect(34 + k, 49 - k // 2, 38 + k, 50 - k // 2, 10)
    rect(36, 51, 42, 51, 0)
    _wrap(c, 37, 49, 18)
    _wrap(c, 40, 48, 18)
    disc(57, 30, 1.6, 1.6, 10)
    _wrap(c, 57, 30, 18)
    _wrap(c, 58, 32, 0)
    return c, pal


def fields():
    """Тайлы поля и аута офиса → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = carpet_field()
    frames = [openspace(f) for f in range(4)]
    return {
        "soccer_field_office": (cv, pal),
        "soccer_out_office": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path, keys=None):
    items = office16.shaded(sprites())
    items.update(fields())
    if keys:
        items = {k: items[k] for k in keys}
    office16.save_sheet(path, items, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        keys_ = None
        for arg in sys.argv:
            if arg.startswith("--keys="):
                keys_ = [k for k in arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], keys_)
