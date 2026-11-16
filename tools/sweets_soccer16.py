#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Сладости» (#137): зеркало `space_soccer16.py` и `pixel_soccer16.py`.
Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов, 8 «лежит»; мяч 8×8
в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка `sport_bit16.gd` ничего
не заметила.

Команда героя это пряничные человечки из `sweets16.py`: круглая голова с белой улыбкой глазурью,
красный бантик под подбородком, две пуговицы-драже, зубчатая кайма глазури по поясу, белые
«гетры» глазури и круглые пряничные ступни без бутс. Соперники это три вида сладостей:
мармеладный мишка (литой красный, круглые уши, розовая морда, блик желе), зефир (белая голова в
два яруса с завитком, розовые крылышки за плечами, румянец), пончик-громила (широкая голова в
розовой глазури с подтёками, посыпкой и дыркой, шоколадная форма с карамельной полосой).
Вратарь героя это пряник, облитый карамелью, в красных прихватках, вратарь соперника это
малиновый мишка в белых рукавицах. Мяч это шар жвачки: блик стоит, малиновая прожилка при
качении переезжает. Поле это мятная глазурь: укатанные полосы по 32, блики, ямки и редкая
посыпка; на ней читаются и коричневые пряники, и красные мишки, и белый зефир, и белая разметка
демки. Вокруг розовый сироп (основание мира сеттинга): волны блика идут по кадрам, пузыри растут
и лопаются.

    python3 tools/sweets_soccer16.py --preview thegames/debug/playtest/env/sweets_soccer16.png

Лист высокий, поэтому пишется тремя файлами: сам путь (герой и два соперника), `_b` (третий
соперник и вратари), `_c` (мяч и тайлы).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweets16  # noqa: E402
from sweets16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                      DARK, RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и формы и вид головы. `limb`/`limb_far` это ноги и, если не задано
    `arm`, руки (у пряника тесто, у мишки мармелад), `shirt`/`shorts`/`sock` форма, `boot` ступня
    (у сладостей своя, не бутса), `trim` полоса на груди, `glove` перчатки вратаря, `head` вид
    головы: ginger, bear, zefir, donut."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, trim=None, glove=None, keeper=False,
                 arm=None, arm_far=None, boot=DARK):
        self.head = head
        self.limb = limb
        self.limb_far = limb_far
        self.shirt = shirt
        self.shorts = shorts
        self.sock = sock
        self.trim = trim
        self.glove = glove
        self.keeper = keeper
        self.arm = limb if arm is None else arm
        self.arm_far = limb_far if arm_far is None else arm_far
        self.boot = boot


def _mid(x):
    """Два средних столбца головы: у центра на полпикселя это пара, у целого один и тот же."""
    return int(math.floor(x)), int(math.ceil(x))


def _head(c, x, y, look, side, back, sgn, body=True):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (лицо, глазурь, посыпка).
    `body`: голова стоит над плечами (бег), можно рисовать то, что ложится на грудь (бантик)."""
    marks = []
    kind = look.head
    lo, hi = _mid(x)
    if kind == "ginger":
        c.ellipse(x, y, 3.6, 3.6, SKIN)
        if back:
            # Затылок: пропечённое пятно.
            for xx in range(lo - 1, hi + 2):
                marks.append((xx, y - 1, TAN))
            for xx in range(lo, hi + 1):
                marks.append((xx, y, TAN))
            return marks
        if side:
            marks.append((x + sgn * 2, y - 1, K))
            marks.append((x + sgn * 2, y + 1, WHITE))
            marks.append((x + sgn * 1, y + 1, WHITE))
            if body:
                marks.append((x + sgn * 1, y + 4, RED))
                marks.append((x + sgn * 2, y + 4, RED))
                marks.append((x + sgn * 2, y + 5, RED))
            return marks
        marks.append((lo - 1, y - 1, K))
        marks.append((hi + 1, y - 1, K))
        marks.append((lo - 1, y + 1, WHITE))
        marks.append((hi + 1, y + 1, WHITE))
        for xx in range(lo, hi + 1):
            marks.append((xx, y + 2, WHITE))
        if body:
            # Бантик: два крыла и малиновый узел.
            for xx in (lo - 2, lo - 1, hi + 1, hi + 2):
                marks.append((xx, y + 4, RED))
            marks.append((lo - 2, y + 5, RED))
            marks.append((hi + 2, y + 5, RED))
            for xx in range(lo, hi + 1):
                marks.append((xx, y + 4, PLUM))
        return marks
    if kind == "bear":
        tone = look.limb
        dark = look.limb_far
        if side:
            # Дальнее ухо темнее, ближнее поверх головы, морда вперёд.
            c.ellipse(x + sgn * 1.5, y - 3.4, 1.4, 1.4, dark)
            c.ellipse(x, y, 3.6, 3.4, tone)
            c.ellipse(x - sgn * 1.5, y - 3.2, 1.7, 1.7, tone)
            c.ellipse(x + sgn * 3.2, y + 1.2, 1.5, 1.2, tone)
            if not back:
                marks.append((x + sgn * 2, y - 1, K))
                marks.append((x + sgn * 4, y + 1, K))
                marks.append((x + sgn * 3, y + 2, VIOLET if tone == RED else WHITE))
            marks.append((x - sgn * 2, y - 3, dark))
            marks.append((x - sgn * 1, y - 2, WHITE))
            return marks
        for q in (-3.0, 3.0):
            c.ellipse(x + q, y - 3.0, 1.7, 1.7, tone)
        c.ellipse(x, y, 3.6, 3.4, tone)
        marks.append((lo - 2, y - 2, WHITE))
        if back:
            marks.append((lo - 1, y - 2, WHITE))
            return marks
        marks.append((lo - 3, y - 3, dark))
        marks.append((hi + 3, y - 3, dark))
        marks.append((lo - 1, y - 1, K))
        marks.append((hi + 1, y - 1, K))
        # Светлая морда с носом.
        muzzle = VIOLET if tone == RED else WHITE
        for xx in range(lo - 1, hi + 2):
            marks.append((xx, y + 2, muzzle))
        for xx in range(lo, hi + 1):
            marks.append((xx, y + 1, K))
        return marks
    if kind == "zefir":
        # Два яруса и завиток: нижний ярус шире, между ними бороздка.
        c.ellipse(x, y + 1.5, 3.9, 2.4, WHITE)
        c.ellipse(x, y - 1.5, 2.6, 1.8, WHITE)
        c.set(hi, y - 4, WHITE)
        for xx in range(lo - 2, hi + 3):
            marks.append((xx, y, GREY))
        if back:
            marks.append((lo, y + 2, GREY))
            marks.append((hi, y + 2, GREY))
            return marks
        if side:
            marks.append((x + sgn * 2, y + 1, K))
            marks.append((x + sgn * 1, y + 2, VIOLET))
            return marks
        marks.append((lo - 1, y + 1, K))
        marks.append((hi + 1, y + 1, K))
        marks.append((lo - 2, y + 2, VIOLET))
        marks.append((hi + 2, y + 2, VIOLET))
        return marks
    # Пончик: широкая приплюснутая голова, сверху розовая глазурь с подтёками.
    c.ellipse(x, y + 0.5, 4.2, 3.0, GOLD)
    edge = y + 2 if back else y
    for yy in range(int(y - 4), int(y + 5)):
        for xx in range(int(x - 6), int(x + 7)):
            if c.get(xx, yy) != GOLD:
                continue
            if yy <= edge or (yy == edge + 1 and (xx - lo) % 3 == 0):
                c.set(xx, yy, VIOLET)
    if back:
        for xx in range(lo, hi + 1):
            marks.append((xx, y, DARK))
        marks.append((lo - 2, y - 1, WHITE))
        marks.append((hi + 2, y + 1, AQUA))
        marks.append((lo - 1, y + 2, GOLD))
        marks.append((hi + 1, y - 1, RED))
        return marks
    for xx in range(lo, hi + 1):
        marks.append((xx, y - 1, DARK))
    marks.append((lo - 2, y - 1, WHITE))
    marks.append((hi + 2, y, AQUA))
    marks.append((lo - 2, y, RED) if not side else (x - sgn * 2, y, RED))
    if side:
        marks.append((x + sgn * 2, y + 2, K))
    else:
        marks.append((lo - 1, y + 2, K))
        marks.append((hi + 1, y + 2, K))
    return marks


def _glove(c, look, x, y):
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)


def _clamp_head(look, x, y):
    """Широкие головы не выходят за кадр: иначе обводка рвётся о край."""
    r = 4 if look.head == "donut" else 3
    return max(r + 1, min(F - 2 - r, x)), max(6, min(F - 5, y))


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов: стойка и четыре кадра бега по
    восьми направлениям, подкат (у вратаря прыжок за мячом), лежит."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    if mode == "down":
        c.line(18, 17, 22, 15, look.limb, 2)
        c.line(18, 19, 22, 20, look.limb, 2)
        c.rect(21, 14, 22, 15, look.boot)
        c.rect(21, 20, 22, 21, look.boot)
        c.line(9, 15, 6, 12, look.arm, 2)
        c.rect(7, 16, 14, 20, look.shirt)
        if look.trim is not None:
            c.rect(10, 16, 10, 20, look.trim)
        c.rect(15, 16, 17, 20, look.shorts)
        hx, hy = _clamp_head(look, 4, 18)
        marks = _head(c, hx, hy, look, True, False, 1, body=False)
        if look.keeper:
            c.rect(5, 11, 6, 12, look.glove)
        c.finish()
        if look.head == "ginger":
            # Кайма глазури по поясу и пуговица видны и у лежащего.
            for yy in (16, 18, 20):
                c.set(14, yy, WHITE)
            c.rect(11, 18, 12, 18, AQUA)
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
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.limb, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.limb, 2)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, look.shirt, 5)
            c.line(tx - ux, ty - uy, tx, ty, look.shorts, 5)
            hx, hy = cx + ux * 5.0, cy + uy * 5.0 - 1.0
            c.line(cx + ux * 2.0 - uy * 2.0, cy + uy * 2.0 + ux * 2.0, hx + ux * 5.0 - uy * 2.0, hy + uy * 5.0 + ux * 2.0, look.arm, 2)
            c.line(cx + ux * 2.0 + uy * 2.0, cy + uy * 2.0 - ux * 2.0, hx + ux * 5.0 + uy * 2.0, hy + uy * 5.0 - ux * 2.0, look.arm, 2)
            px, py = _clamp_head(look, round(hx), round(hy))
            marks = _head(c, px, py, look, side, back, sgn, body=False)
            c.finish()
            for q in (-2.0, 2.0):
                gx, gy = hx + ux * 5.5 - uy * q, hy + uy * 5.5 + ux * q
                c.rect(gx - 0.5, gy - 0.5, gx + 0.5, gy + 0.5, look.glove)
            for x, y, v in marks:
                c.set(x, y, v)
            return c
        fx, fy = cx + ux * 8.0, cy + uy * 8.0
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, look.limb_far, 2)
        c.line(cx, cy, fx, fy, look.limb, 2)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, look.sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, look.boot)
        c.line(tx, ty, cx, cy, look.shirt, 5)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, 5)
        c.line(tx, ty, tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0, look.arm, 2)
        px, py = _clamp_head(look, round(tx - ux * 3.0), round(ty - uy * 3.0 - 2.0))
        marks = _head(c, px, py, look, side, back, sgn, body=False)
        c.finish()
        for x, y, v in marks:
            c.set(x, y, v)
        return c
    side = abs(dx) > 0.38
    back = dy < -0.38
    s = (0, 1, 0, -1, 0)[frame]
    bob = 1 if frame in (2, 4) else 0
    hip = 18 - bob
    late = []
    # Кайма глазури у концов рук пряника: ставится только поверх теста, обводку не трогает.
    cuffs = []
    if side:
        for near, k in ((False, -s), (True, s)):
            hand = (11.5 - sgn * 4.0 * k, 15.0 - bob - abs(k))
            if not near:
                c.line(11.5, 11.0 - bob, hand[0], hand[1], look.arm_far, 2)
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
            c.line(knee[0], knee[1], foot[0], foot[1], look.sock, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0, look.boot)
        if look.head == "zefir":
            # Крылышко за спиной: два пера вверх и назад.
            bx = 8.5 if sgn > 0 else 14.5
            c.line(bx, 12 - bob, bx - sgn * 3.0, 9 - bob, PLUM, 2)
            c.line(bx, 11 - bob, bx - sgn * 2.0, 7 - bob, VIOLET, 2)
        c.rect(9, 10 - bob, 14, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(9, 12 - bob, 14, 12 - bob, look.trim)
        c.rect(9, 16 - bob, 14, 17 - bob, look.shorts)
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        c.line(11.5, 11.0 - bob, hand[0], hand[1], look.arm, 2)
        _glove(c, look, hand[0], hand[1])
        if look.head == "ginger" and not look.keeper:
            cuffs.append((11.5 + (hand[0] - 11.5) * 0.6, 11.0 - bob + (hand[1] - 11.0 + bob) * 0.6))
        if look.head == "ginger":
            for xx in (9, 11, 13):
                late.append((xx, 15 - bob, WHITE))
            late.append((13 if sgn > 0 else 10, 13 - bob, AQUA))
        elif look.head == "bear":
            late.append((10 if sgn > 0 else 13, 11 - bob, WHITE))
        marks = _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.limb)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.boot)
        if look.head == "zefir":
            # Крылышки из-за плеч, видны и спереди, и со спины.
            for q in (-1, 1):
                c.line(11.5 + q * 3.5, 11 - bob, 11.5 + q * 6.5, 7 - bob, VIOLET, 2)
        c.rect(8, 10 - bob, 15, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(8, 12 - bob, 15, 12 - bob, look.trim)
        c.rect(8, 16 - bob, 15, 17 - bob, look.shorts)
        for x, k, out in ((6.5, -s, -1), (16.5, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            c.line(x, 11.0 - bob, hand[0], hand[1], look.arm, 2)
            _glove(c, look, hand[0], hand[1])
            if look.head == "ginger" and not look.keeper:
                for xx in (math.floor(hand[0]), math.ceil(hand[0])):
                    cuffs.append((xx, hand[1] - 1.0))
        if look.head == "ginger":
            # Зубчатая кайма глазури по поясу; спереди две пуговицы-драже.
            for xx in (8, 10, 12, 14):
                late.append((xx, 15 - bob, WHITE))
            for xx in (9, 11, 13):
                late.append((xx, 16 - bob, WHITE))
            if not back:
                late.append((11, 12 - bob, AQUA))
                late.append((12, 12 - bob, AQUA))
                late.append((11, 14 - bob, VIOLET))
                late.append((12, 14 - bob, VIOLET))
        elif look.head == "bear":
            # Блик желе на плече и светлый просвет у бока.
            late.append((9, 11 - bob, WHITE))
            late.append((9, 12 - bob, WHITE))
            late.append((13, 14 - bob, VIOLET if look.limb == RED else WHITE))
        elif look.head == "zefir" and back:
            # Крылья сходятся на спине.
            for q in (0, 1):
                late.append((10 + q * 3, 11 - bob, VIOLET))
                late.append((11 + q, 12 - bob, VIOLET))
        marks = _head(c, 11.5, 6 - bob, look, False, back, sgn)
    c.finish()
    for x, y in cuffs:
        tone = c.get(int(round(x)), int(round(y)))
        if tone in (SKIN, TAN):
            c.set(x, y, WHITE if tone == SKIN else GREY)
    for x, y, v in late + marks:
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


# Команды. Герой: пряник целиком, форму заменяет глазурь (кайма по поясу, белые гетры, бантик).
HERO = Look("ginger", SKIN, TAN, SKIN, SKIN, WHITE, boot=SKIN)
# Вратарь героя: облит карамелью, шоколадные трусы, красные прихватки.
KEEPER_HERO = Look("ginger", SKIN, TAN, GOLD, DARK, WHITE, glove=RED, keeper=True, arm=GOLD, arm_far=BRASS,
                   boot=SKIN)
# Мармеладный мишка: литой красный, малиновые «трусы» и лапы.
RIVAL_0 = Look("bear", RED, PLUM, RED, PLUM, RED, boot=PLUM)
# Зефир: белое тело с бороздкой, розовые руки и ноги, белые гетры.
RIVAL_1 = Look("zefir", VIOLET, PLUM, WHITE, VIOLET, WHITE, trim=GREY, boot=PLUM)
# Пончик-громила: тесто, шоколадная форма с карамельной полосой, розовые гетры.
RIVAL_2 = Look("donut", GOLD, BRASS, DARK, METAL, VIOLET, trim=GOLD)
# Вратарь соперника: малиновый мишка в мятной майке и белых рукавицах.
KEEPER_RIVAL = Look("bear", VIOLET, PLUM, VIOLET, PLUM, WHITE, trim=WHITE, glove=WHITE, keeper=True, boot=PLUM)


# Шар жвачки 8×8: розовый, белый блик стоит на месте, малиновая прожилка при качении переезжает
# (два кадра, мяч «вращается»). o обвод, p жвачка, d прожилка, W блик.
BALL_MAPS = (
    ("..oooo..",
     ".opppdo.",
     "opWppdpo",
     "opWpdppo",
     "oppdpppo",
     "opdppppo",
     ".odpppo.",
     "..oooo.."),
    ("..oooo..",
     ".odpppo.",
     "odWppppo",
     "opWpppdo",
     "oppppdpo",
     "opppdppo",
     ".opdppo.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "p": VIOLET, "d": PLUM, "W": WHITE}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def wafer():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): мятная вафля, полосы
    по 32 темнее и светлее, клетка вафли по 16 и блик в углу каждой клетки."""
    c = Canvas(64, 64)
    for x in range(64):
        for y in range(64):
            left = x < 32
            cell = SEA
            if x % 16 == 0 or y % 16 == 0:
                cell = NAVY if left else SEA
            elif not left and (x + y) % 2 == 0:
                # Светлая полоса: мята в шахматку с мятной карамелью.
                cell = AQUA
            if (x % 16, y % 16) in ((2, 2), (3, 2), (2, 3)):
                cell = AQUA if left else SKY
            c.set(x, y, cell)
    return c


deck = wafer


def sprites():
    return {
        "soccer_hero": kit_strip(HERO),
        "soccer_rival_0": kit_strip(RIVAL_0),
        "soccer_rival_1": kit_strip(RIVAL_1),
        "soccer_rival_2": kit_strip(RIVAL_2),
        "soccer_keeper_hero": kit_strip(KEEPER_HERO),
        "soccer_keeper_rival": kit_strip(KEEPER_RIVAL),
        "soccer_ball": strip([ball(i) for i in range(2)]),
        "soccer_grass": wafer(),
    }


# --- Поле и аут ---------------------------------------------------------------------------------
# Тайлы 64×64 бесшовные, в своих палитрах. Поле средней яркости и холодное: на нём читаются и
# тёплые пряники, и красные мишки, и белый зефир, и белая разметка демки.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def glaze():
    """Мятная глазурь: укатанные полосы по 32 (как полосы газона), мелкая рябь, косые блики
    глянца, ямки от пузырьков (тень сверху слева, светлый край снизу справа), редкая посыпка
    приглушённых цветов. Палитра: 0 глубокая тень, 1 тень, 2 глазурь, 3 светлая глазурь, 4 блик,
    5 розовая посыпка, 6 карамельная посыпка, 7 белая посыпка."""
    pal = _pal(0x1F7468, 0x2B8A7B, 0x379C8B, 0x45AA98, 0x7CCDB8, 0xC7789C, 0xC9B36A, 0xD9F2E6)
    c = Canvas(T, T)
    rng = random.Random(47)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    for _ in range(int(T * T * 0.07)):
        x, y = rng.randrange(T), rng.randrange(T)
        base = c.px[y][x]
        c.px[y][x] = base - 1 if rng.random() < 0.65 else base + 1
    # Блики глянца: короткие косые штрихи, светлее полосы на тон.
    for _ in range(14):
        x0, y0, ln = rng.randrange(T), rng.randrange(T), rng.randint(3, 6)
        tone = 3 if x0 < 32 else 4
        for k in range(ln):
            _wrap(c, x0 + k, y0 - k, tone)
    # Ямки от пузырьков.
    rng = random.Random(5)
    for _ in range(5):
        cx, cy, rr = rng.randrange(T), rng.randrange(T), rng.uniform(1.4, 2.6)
        for y in range(int(cy - rr - 2), int(cy + rr + 3)):
            for x in range(int(cx - rr - 2), int(cx + rr + 3)):
                d = math.hypot(x - cx, y - cy)
                if d <= rr:
                    _wrap(c, x, y, 0 if (x - cx) + (y - cy) < 0 else 1)
                elif d <= rr + 1.0 and (x - cx) + (y - cy) > 0:
                    _wrap(c, x, y, 4)
    # Посыпка: палочки в два пикселя с тенью под ними.
    for k in range(11):
        x, y = rng.randrange(T), rng.randrange(T)
        tone = 5 + k % 3
        hx, hy = ((1, 0), (0, 1), (1, 1), (1, -1))[k % 4]
        _wrap(c, x, y, tone)
        _wrap(c, x + hx, y + hy, tone)
        _wrap(c, x + hx, y + hy + 1, 1)
    return c, pal


def syrup(frame):
    """Розовый сироп вокруг поля: густая малиновая гладь, по ней медленно ползут волны блика
    (сдвиг на четверть периода за кадр), пузыри растут и лопаются по кадрам. Палитра: 0 глубина,
    1 тёмный сироп, 2 сироп, 3 светлый сироп, 4 блик, 5 белая искра."""
    pal = _pal(0x8E2458, 0xB2356C, 0xD04C82, 0xE9719E, 0xFFA6C4, 0xFFF1F4)
    c = Canvas(T, T)
    ph = frame / 4.0 * 2 * math.pi
    for y in range(T):
        for x in range(T):
            u = x / 64.0 * 2 * math.pi
            v = y / 64.0 * 2 * math.pi
            # Тягучие складки: длинные вдоль x, изгибаются по y, фаза идёт по кадрам.
            w = (math.sin(v * 4 + math.sin(u) * 1.8 + ph) +
                 0.6 * math.sin(v * 2 - u + math.sin(u * 2) - ph) +
                 0.4 * math.sin(u * 2 + v * 3 + ph))
            cell = 2
            if w > 1.7:
                cell = 4
            elif w > 1.25:
                cell = 3
            elif w < -1.75:
                cell = 0
            elif w < -1.3:
                cell = 1
            c.px[y][x] = cell
    rng = random.Random(23)
    for k in range(7):
        x, y = rng.randrange(T), rng.randrange(T)
        age = (k + frame) % 4
        if age == 0:
            # Зарождается: светлая точка.
            _wrap(c, x, y, 4)
        elif age == 1:
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                _wrap(c, x + ox, y + oy, 3)
            _wrap(c, x, y, 5)
            _wrap(c, x + 1, y + 2, 1)
            _wrap(c, x + 2, y + 1, 1)
        elif age == 2:
            # Пузырь: кольцо с искрой и тенью снизу справа.
            for ox, oy in ((0, -1), (1, -1), (-1, 0), (-1, 1), (0, 2), (1, 2)):
                _wrap(c, x + ox, y + oy, 4)
            for ox, oy in ((2, 0), (2, 1)):
                _wrap(c, x + ox, y + oy, 1)
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                _wrap(c, x + ox, y + oy, 3)
            _wrap(c, x, y, 5)
        else:
            # Лопнул: брызги крестом.
            for ox, oy in ((-2, 0), (3, 0), (0, -2), (1, 3)):
                _wrap(c, x + ox, y + oy, 4)
            _wrap(c, x, y, 1)
            _wrap(c, x + 1, y + 1, 1)
    return c, pal


regolith = glaze
stars = syrup


def fields():
    """Тайлы поля и аута сладостей → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = glaze()
    frames = [syrup(f) for f in range(4)]
    return {
        "soccer_field_sweets": (cv, pal),
        "soccer_out_sweets": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    items = sweets16.shaded(sprites())
    items.update(fields())
    # Лист целиком выше полутора тысяч пикселей: три файла, `_b` и `_c` рядом с первым.
    root, ext = os.path.splitext(path)
    groups = (("", ("soccer_hero", "soccer_rival_0", "soccer_rival_1")),
              ("_b", ("soccer_rival_2", "soccer_keeper_hero", "soccer_keeper_rival")),
              ("_c", ("soccer_ball", "soccer_grass", "soccer_field_sweets", "soccer_out_sweets")))
    for suffix, keys in groups:
        sweets16.save_sheet(root + suffix + ext, {k: items[k] for k in keys}, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
