#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Фэнтези» (#137): зеркало `space_soccer16.py` и `pixel_soccer16.py`.
Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов, 8 «лежит»; мяч 8×8
в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка `sport_bit16.gd` ничего
не заметила.

Команда героя это юные маги из `fantasy16.py`: синяя мантия колоколом с золотым поясом и золотой
каймой подола, остроконечная шляпа с полями и золотой лентой, кончик загнут назад, каштановые
волосы, белые чулки. Соперники это лесная нечисть трёх видов: гоблин (лысая зелёная голова,
острые уши в стороны, красная рубаха), гоблин-шаман (веер перьев, белая маска-череп, сиреневая
роба с золотым ожерельем), тролль (широкий, каменно-серый, голова без шеи, моховая шапка, клыки
вверх, бурая шкура с ремнём). Вратарь героя это ученик в золотой мантии и фиолетовой шляпе с
бирюзовыми рукавицами, вратарь соперника это гоблин с медным котелком на голове и в белых
костяных рукавицах. Мяч это хрустальный шар: блик стекла стоит, сиреневый туман внутри при
качении переворачивается. Поле это сумеречный луг с сиреневой травой: укатанные полосы по 32,
травинки, клевер, светящиеся цветы; на нём читаются и синие мантии, и зелёные гоблины, и белая
разметка демки. Вокруг пропасть под летающим островом: облака внизу дышат по кадрам, светляки
мерцают.

    python3 tools/fantasy_soccer16.py --preview thegames/debug/playtest/env/fantasy_soccer16.png

Лист высокий, поэтому пишется тремя файлами: сам путь (герой и два соперника), `_b` (третий
соперник и вратари), `_c` (мяч и тайлы).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fantasy16  # noqa: E402
from fantasy16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                       DARK, RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и одежды и вид головы. `limb`/`limb_far` это ноги (чулки мага или
    кожа), `arm`/`arm_far` руки (рукав или кожа; без них берутся цвета ног), `hand` кисть полевого
    игрока, `shirt`/`shorts`/`sock` верх, низ и голени, `boot` ступни, `trim` полоса на груди,
    `belt` пояс, `hem` кайма подола (с ней низ это мантия колоколом), `glove` рукавицы вратаря,
    `head` вид головы (`mage`, `goblin`, `shaman`, `troll`, `pot`), `hat` цвет шляпы мага, `wide`
    широкий корпус тролля."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, trim=None, glove=None, keeper=False,
                 arm=None, arm_far=None, hand=None, boot=DARK, belt=None, hem=None, hat=SEA, wide=False):
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
        self.hand = hand
        self.boot = boot
        self.belt = belt
        self.hem = hem
        self.hat = hat
        self.wide = wide


def _head_mage(c, x, y, look, side, back, sgn, marks):
    """Маг: лицо под полями, каштановые волосы, шляпа конусом с золотой лентой, кончик назад."""
    c.ellipse(x, y + 1, 3.2, 2.8, METAL if back else SKIN)
    if not back:
        if side:
            c.rect(min(x - sgn * 3, x - sgn), y, max(x - sgn * 3, x - sgn), y + 2, METAL)
        else:
            c.rect(x - 3, y, x - 3, y + 2, METAL)
            c.rect(x + 3, y, x + 3, y + 2, METAL)
    # Шляпа: поля, тулья в три ступени, кончик уходит назад (в анфас вбок).
    c.rect(x - 4, y - 1, x + 4, y - 1, look.hat)
    c.rect(x - 2, y - 3, x + 2, y - 2, look.hat)
    c.rect(x - 1, y - 4, x + 1, y - 4, look.hat)
    tip = -sgn if side else 1
    c.rect(min(x, x + tip), y - 5, max(x, x + tip), y - 5, look.hat)
    c.set(x + tip * 2, y - 4, look.hat)
    for xx in range(int(x - 2), int(x + 3)):
        marks.append((xx, y - 2, GOLD))
    if back:
        return
    if side:
        marks.append((x + sgn * 2, y + 1, K))
        marks.append((x + sgn * 2, y + 2, K))
    else:
        for ex in (x - 2, x + 1):
            marks.append((ex, y + 1, K))
            marks.append((ex, y + 2, K))


def _ears(c, x, y, side, sgn, col, reach=4.0):
    """Острые уши гоблина: в анфас в стороны и вверх, сбоку одно назад."""
    if side:
        c.poly([(x - sgn * 2, y - 1), (x - sgn * (2 + reach), y - 3), (x - sgn * 2, y + 1)], col)
        c.line(x - sgn * 2, y, x - sgn * (2 + reach), y - 3, col, 1)
    else:
        for o in (-1, 1):
            c.poly([(x + o * 3, y - 1), (x + o * (3 + reach), y - 3), (x + o * 3, y + 1)], col)
            c.line(x + o * 3, y, x + o * (3 + reach), y - 3, col, 1)


def _head_goblin(c, x, y, look, side, back, sgn, marks, kind):
    skin = look.limb
    c.ellipse(x, y + 0.5, 3.4, 3.2, skin)
    _ears(c, x, y, side, sgn, skin, 4.0 if kind == "goblin" else 3.0)
    if side and not back:
        # Нос крючком вперёд.
        c.rect(min(x + sgn * 3, x + sgn * 4), y + 1, max(x + sgn * 3, x + sgn * 4), y + 1, skin)
    if kind == "shaman":
        # Веер перьев над головой: красные по краям, золотое в середине.
        lean = -sgn if side else 0
        c.line(x - 2, y - 3, x - 4 + lean, y - 6, RED, 1)
        c.line(x + 2, y - 3, x + 4 + lean, y - 6, RED, 1)
        c.line(x, y - 3, x + lean, y - 6, GOLD, 1)
        c.line(x - 1, y - 3, x - 2 + lean, y - 5, GOLD, 1)
        c.line(x + 1, y - 3, x + 2 + lean, y - 5, GOLD, 1)
        c.rect(x - 3, y - 3, x + 3, y - 3, METAL)
    elif kind == "pot":
        # Медный котелок вместо шлема: купол и золотой обод, сверху ручка.
        c.rect(x - 3, y - 3, x + 3, y - 1, BRASS)
        c.rect(x - 2, y - 4, x + 2, y - 4, BRASS)
        c.rect(x - 4, y - 1, x + 4, y - 1, GOLD)
        c.rect(x - 1, y - 5, x + 1, y - 5, METAL)
        marks.append((x - 2, y - 3, GOLD))
    if back:
        return
    if kind == "shaman":
        # Маска-череп: белая кость на лице, чёрные глазницы, зубы.
        if side:
            for yy in (y - 1, y, y + 1, y + 2):
                for k in (1, 2, 3):
                    marks.append((x + sgn * k, yy, WHITE))
            marks.append((x + sgn * 2, y, K))
            marks.append((x + sgn * 2, y + 1, K))
            marks.append((x + sgn * 3, y + 3, GREY))
        else:
            for yy in (y - 1, y, y + 1, y + 2):
                for xx in range(int(x - 2), int(x + 3)):
                    marks.append((xx, yy, WHITE))
            for ex in (x - 2, x + 1):
                marks.append((ex, y, K))
                marks.append((ex, y + 1, K))
            marks.append((x - 1, y + 3, GREY))
            marks.append((x + 1, y + 3, GREY))
        return
    # Жёлтый глаз с чёрным зрачком, белый клык.
    if side:
        marks.append((x + sgn * 2, y, GOLD))
        marks.append((x + sgn * 2, y + 1, K))
        marks.append((x + sgn * 2, y + 3, WHITE))
    else:
        for ex in (x - 2, x + 1):
            marks.append((ex, y, GOLD))
            marks.append((ex, y + 1, K))
        marks.append((x - 1, y + 3, WHITE))
        marks.append((x + 1, y + 3, WHITE))


def _head_troll(c, x, y, look, side, back, sgn, marks):
    """Тролль: широкая приплюснутая каменная голова, моховая шапка, клыки снизу вверх."""
    c.ellipse(x, y + 1, 4.4, 3.0, look.limb)
    c.ellipse(x, y - 1.6, 3.4, 1.4, TAN)
    c.set(x - 2, y - 4, TAN)
    c.set(x + 1, y - 4, TAN)
    if back:
        return
    if side:
        marks.append((x + sgn * 2, y, K))
        marks.append((x + sgn * 1, y - 1, PLUM))
        marks.append((x + sgn * 2, y - 1, PLUM))
        marks.append((x + sgn * 1, y + 2, K))
        marks.append((x + sgn * 2, y + 2, K))
        marks.append((x + sgn * 3, y + 2, WHITE))
        marks.append((x + sgn * 3, y + 1, WHITE))
    else:
        for ex, o in ((x - 2, -1), (x + 1, 1)):
            marks.append((ex, y, K))
            marks.append((ex, y - 1, PLUM))
            marks.append((ex + o, y - 1, PLUM))
        for mx in range(x - 2, x + 2):
            marks.append((mx, y + 2, K))
        for tx in (x - 3, x + 2):
            marks.append((tx, y + 2, WHITE))
            marks.append((tx, y + 1, WHITE))


def _head(c, x, y, look, side, back, sgn):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (глаза, маска, лента)."""
    marks = []
    x = int(math.floor(x))
    y = int(round(y))
    if look.head == "mage":
        _head_mage(c, x, y, look, side, back, sgn, marks)
    elif look.head == "troll":
        _head_troll(c, x, y, look, side, back, sgn, marks)
    else:
        _head_goblin(c, x, y, look, side, back, sgn, marks, look.head)
    return marks


def _glove(c, look, x, y):
    """Кисть: рукавица вратаря или ладонь из рукава."""
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)
    elif look.hand is not None:
        c.set(x, y + 0.5, look.hand)


def _skirt(c, look, x0, x1, bob):
    """Низ: трусы, а у мантии подол колоколом на строку ниже и на пиксель шире, с каймой."""
    if look.belt is not None:
        c.rect(x0, 15 - bob, x1, 15 - bob, look.belt)
    if look.hem is None:
        c.rect(x0, 16 - bob, x1, 17 - bob, look.shorts)
        return
    c.rect(x0, 16 - bob, x1, 16 - bob, look.shorts)
    c.rect(x0 - 1, 17 - bob, x1 + 1, 17 - bob, look.shorts)
    c.rect(x0 - 1, 18 - bob, x1 + 1, 18 - bob, look.hem)


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов: стойка и четыре кадра бега по
    восьми направлениям, подкат (у вратаря прыжок за мячом), лежит."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    w = 1 if look.wide else 0
    if mode == "down":
        c.line(18, 17, 22, 15, look.limb, 2)
        c.line(18, 19, 22, 20, look.limb, 2)
        c.rect(21, 14, 22, 15, look.boot)
        c.rect(21, 20, 22, 21, look.boot)
        c.line(9, 15, 6, 12, look.arm, 2)
        c.rect(7, 16 - w, 14, 20, look.shirt)
        if look.trim is not None:
            c.rect(10, 16 - w, 10, 20, look.trim)
        if look.belt is not None:
            c.rect(14, 16 - w, 14, 20, look.belt)
        c.rect(15, 16 - w, 17, 20, look.shorts)
        if look.hem is not None:
            c.rect(18, 15, 18, 21, look.hem)
        marks = _head(c, 4, 18, look, True, False, 1)
        if look.keeper:
            c.rect(5, 11, 6, 12, look.glove)
        elif look.hand is not None:
            c.set(6, 12, look.hand)
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
        body = 6 if look.wide else 5
        if look.keeper:
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.limb, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.limb, 2)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, look.shirt, body)
            c.line(tx - ux, ty - uy, tx, ty, look.shorts, body)
            if look.hem is not None:
                c.line(tx - ux * 2.0 - uy * 3.0, ty - uy * 2.0 + ux * 3.0, tx - ux * 2.0 + uy * 3.0, ty - uy * 2.0 - ux * 3.0,
                       look.hem, 1)
            hx, hy = cx + ux * 5.0, cy + uy * 5.0 - 1.0
            c.line(cx + ux * 2.0 - uy * 2.0, cy + uy * 2.0 + ux * 2.0, hx + ux * 5.0 - uy * 2.0, hy + uy * 5.0 + ux * 2.0, look.arm, 2)
            c.line(cx + ux * 2.0 + uy * 2.0, cy + uy * 2.0 - ux * 2.0, hx + ux * 5.0 + uy * 2.0, hy + uy * 5.0 - ux * 2.0, look.arm, 2)
            marks = _head(c, round(hx), round(hy), look, side, back, sgn)
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
        c.line(tx, ty, cx, cy, look.shirt, body)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, body)
        if look.hem is not None:
            c.line(cx + ux * 2.0 - uy * 3.0, cy + uy * 2.0 + ux * 3.0, cx + ux * 2.0 + uy * 3.0, cy + uy * 2.0 - ux * 3.0,
                   look.hem, 1)
        ax, ay = tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0
        c.line(tx, ty, ax, ay, look.arm, 2)
        if look.hand is not None:
            c.set(ax, ay, look.hand)
        marks = _head(c, round(tx - ux * 3.0), round(ty - uy * 3.0 - 2.0), look, side, back, sgn)
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
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0,
                   look.boot)
        c.rect(9 - w, 10 - bob, 14 + w, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(9 - w, 12 - bob, 14 + w, 12 - bob, look.trim)
        _skirt(c, look, 9 - w, 14 + w, bob)
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        c.line(11.5, 11.0 - bob, hand[0], hand[1], look.arm, 2)
        _glove(c, look, hand[0], hand[1])
        marks = _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.limb)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.boot)
        c.rect(8 - w, 10 - bob, 15 + w, 15 - bob, look.shirt)
        if look.trim is not None:
            if look.wide:
                # Ремень шкуры через плечо.
                c.line(8 - w, 10 - bob, 15 + w, 15 - bob, look.trim, 1)
            else:
                c.rect(8, 12 - bob, 15, 12 - bob, look.trim)
        _skirt(c, look, 8 - w, 15 + w, bob)
        for x, k, out in ((6.5 - w, -s, -1), (16.5 + w, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            c.line(x, 11.0 - bob, hand[0], hand[1], look.arm, 2)
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


# Команды. Герой: синяя мантия с золотым поясом и каймой, синяя шляпа, белые чулки.
HERO = Look("mage", WHITE, GREY, SEA, SEA, WHITE, arm=SEA, arm_far=NAVY, hand=SKIN, belt=GOLD, hem=GOLD,
            hat=SEA)
# Вратарь героя: золотая мантия и фиолетовая шляпа, чтобы не путался с полевыми.
KEEPER_HERO = Look("mage", WHITE, GREY, GOLD, GOLD, WHITE, arm=GOLD, arm_far=BRASS, glove=AQUA, keeper=True,
                   belt=VIOLET, hem=VIOLET, hat=VIOLET)
RIVAL_0 = Look("goblin", TAN, TAN, RED, METAL, TAN, belt=DARK)
RIVAL_1 = Look("shaman", TAN, TAN, VIOLET, VIOLET, TAN, trim=GOLD, arm=VIOLET, arm_far=PLUM, hand=TAN,
               hem=WHITE, boot=METAL)
RIVAL_2 = Look("troll", GREY, PLUM, METAL, DARK, GREY, trim=DARK, boot=PLUM, wide=True)
KEEPER_RIVAL = Look("pot", TAN, TAN, DARK, PLUM, METAL, trim=GOLD, glove=WHITE, keeper=True)


# Хрустальный шар 8×8: тёмный обод, бирюзовое стекло, белый блик стоит слева сверху, сиреневый
# туман внутри переворачивается (два кадра, при качении шар «вращается»). o обод, a стекло,
# s светлое, W блик, v туман, p тень тумана, n тень стекла.
BALL_MAPS = (
    ("..oooo..",
     ".oWsaao.",
     "oWssvvao",
     "osavvpao",
     "oaavpaao",
     "onaaaano",
     ".onaano.",
     "..oooo.."),
    ("..oooo..",
     ".oWsaao.",
     "oWsaaaao",
     "osaaavao",
     "oapvvvao",
     "onpvvano",
     ".onaano.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "a": AQUA, "s": SKY, "W": WHITE, "n": SEA, "v": VIOLET, "p": PLUM}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def flagstones():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): плиты двора гильдии,
    полосы по 32 светлее и темнее, швы вперевязку, в углах плит бирюзовые руны-точки."""
    c = Canvas(64, 64)
    for x in range(64):
        for y in range(64):
            light = x < 32
            row = y // 16
            sx = (x + (8 if row % 2 else 0)) % 16
            band = PLUM if light else NAVY
            if sx == 0 or y % 16 == 0:
                band = NAVY if light else K
            elif (sx, y % 16) in ((1, 1), (2, 1), (1, 2)):
                band = VIOLET if light else PLUM
            elif (sx, y % 16) == (8, 8) and (x // 16 + row) % 2 == 0:
                band = AQUA
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
        "soccer_grass": flagstones(),
    }


# --- Поле и аут ---------------------------------------------------------------------------------
# Тайлы 64×64 бесшовные, в своих палитрах. Поле тёмное сиреневое: на нём читаются и синие мантии
# с золотом, и зелёные гоблины, и серый тролль, и белая разметка демки.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def _spots(rng, nx, ny, skip=0.0):
    """Точки по сетке со сдвигом: разбросаны ровно, без куч и пустот, на шве тайла не слипаются."""
    out = []
    for gy in range(ny):
        for gx in range(nx):
            if rng.random() < skip:
                continue
            out.append((int((gx + 0.15 + rng.random() * 0.7) * T / nx), int((gy + 0.15 + rng.random() * 0.7) * T / ny)))
    return out


def meadow():
    """Сумеречный луг: сиреневая трава, укатанные полосы по 32 (как полосы газона), пучки
    травинок галочкой со светлыми кончиками, тёмные кочки клевера, редкие светящиеся цветы и
    золотая пыльца. Палитра: 0 глубокая тень, 1 тень, 2 трава, 3 светлая трава, 4 кончик
    травинки, 5 бирюзовый цветок, 6 его сердцевина, 7 пыльца."""
    pal = _pal(0x241A40, 0x30244F, 0x3C2D62, 0x463470, 0x6E58A6, 0x3AD4C2, 0xC8F8EC, 0xC2A04C)
    c = Canvas(T, T)
    rng = random.Random(23)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    # Крошка: трава неровная, чуть темнее или светлее основы.
    for _ in range(int(T * T * 0.05)):
        x, y = rng.randrange(T), rng.randrange(T)
        c.px[y][x] = (1 if rng.random() < 0.5 else 3) if x < 32 else 2
    # Пучки: две-три травинки галочкой, кончики светлые, под пучком тень.
    for x, y in _spots(rng, 6, 6, 0.15):
        base = 2 if x % T < 32 else 3
        mid = 3 if base == 2 else 4
        _wrap(c, x, y, 4)
        _wrap(c, x, y + 1, mid)
        _wrap(c, x - 2, y + 1, 4)
        _wrap(c, x - 1, y + 2, mid)
        if rng.random() < 0.6:
            _wrap(c, x + 2, y + 1, 4)
            _wrap(c, x + 1, y + 2, mid)
        for ox in (-1, 0, 1):
            _wrap(c, x + ox, y + 3, 1)
    # Кочки клевера: три тёмных листка вокруг точки.
    for x, y in _spots(rng, 3, 3, 0.2):
        for ox, oy in ((0, -1), (-1, 0), (1, 0)):
            _wrap(c, x + ox, y + oy, 1)
        _wrap(c, x, y, 0)
        _wrap(c, x, y + 1, 0)
    # Светящиеся цветы: крестик лепестков, светлая сердцевина, стебель и тень снизу.
    for x, y in _spots(rng, 2, 2):
        for ox, oy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            _wrap(c, x + ox, y + oy, 5)
        _wrap(c, x, y, 6)
        _wrap(c, x, y + 2, 1)
        _wrap(c, x - 1, y + 3, 0)
        _wrap(c, x, y + 3, 0)
    for x, y in _spots(rng, 3, 3, 0.3):
        _wrap(c, x, y, 7)
    return c, pal


# Облака пропасти: центр дна, затем кучи (сдвиг, радиус). Расставлены так, чтобы повтор тайла не
# читался рядами, и не касаются друг друга.
CLOUDS = (
    (14, 15, ((-6, 4), (0, 7), (7, 4))),
    (47, 27, ((-7, 3), (-1, 6), (6, 5), (11, 3))),
    (20, 42, ((-5, 3), (1, 5), (7, 3))),
    (50, 56, ((-6, 4), (1, 6), (8, 3))),
)


def abyss(frame):
    """Пропасть под летающим островом: густые сумерки, внизу плывут кучевые облака с плоским
    дном (светлая кромка дышит по кадрам), под ними штриховка тени, между ними мерцают светляки
    и блуждающие огоньки. Палитра: 0 глубина, 1 дымка, 2 тень облака, 3 облако, 4 свет облака,
    5 кромка, 6 светляк, 7 огонёк, 8 тусклый светляк."""
    pal = _pal(0x171034, 0x221A4C, 0x392E78, 0x5A4CA4, 0x8878C8, 0xCCC0F0, 0xF6D058, 0x3AD4C2, 0x6A5A8C)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            v = math.sin(x / 64.0 * 2 * math.pi + 2.0) + math.sin(y / 64.0 * 4 * math.pi + 0.5)
            c.px[y][x] = 1 if v > 1.2 and (x + y) % 2 == 0 else 0
    for i, (cx, cy, puffs) in enumerate(CLOUDS):
        breathe = (frame + i) % 4 in (1, 2)
        inside = set()
        for ox, r in puffs:
            for yy in range(-r, 1):
                for xx in range(-r, r + 1):
                    if xx * xx + yy * yy <= r * r + 0.5:
                        inside.add((ox + xx, yy))
        lo = min(x for x, _ in inside)
        hi = max(x for x, _ in inside)
        # Дно скруглено: крайние пиксели нижней строки сняты.
        inside.discard((lo, 0))
        inside.discard((hi, 0))
        for xx, yy in inside:
            depth = 0
            while (xx, yy - depth - 1) in inside:
                depth += 1
            if depth == 0:
                v = 5
            elif depth <= (2 if breathe else 1) or ((xx - 1, yy) not in inside and yy < -1):
                v = 4
            elif yy >= -1:
                v = 2
            else:
                v = 3
            _wrap(c, cx + xx, cy + yy, v)
        # Тень под облаком: штриховка уходит вниз и вправо.
        for xx in range(lo + 2, hi):
            for k in (1, 2, 3):
                if (xx + k) % 2 == 0 and k <= 1 + (hi - xx) // 3:
                    _wrap(c, cx + xx + k, cy + k, 1)
    rng = random.Random(41)
    k = 0
    for x, y in _spots(rng, 4, 4):
        if any(c.px[(y + oy) % T][(x + ox) % T] > 1 for ox in (-2, -1, 0, 1, 2) for oy in (-2, -1, 0, 1, 2)):
            continue
        tw = (k + frame) % 4
        if k % 4 == 2:
            _wrap(c, x, y, 7 if tw < 3 else 8)
            if tw == 0:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    _wrap(c, x + ox, y + oy, 2)
        else:
            _wrap(c, x, y, 6 if tw < 2 else 8)
        k += 1
    return c, pal


# Имена зеркала космоса: кто берёт тайлы по ним, получает здешние.
deck = flagstones
regolith = meadow
stars = abyss


def fields():
    """Тайлы поля и аута фэнтези → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = meadow()
    frames = [abyss(f) for f in range(4)]
    return {
        "soccer_field_fantasy": (cv, pal),
        "soccer_out_fantasy": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    items = fantasy16.shaded(sprites())
    items.update(fields())
    # Лист целиком выше полутора тысяч пикселей: три файла, `_b` и `_c` рядом с первым.
    root, ext = os.path.splitext(path)
    groups = (("", ("soccer_hero", "soccer_rival_0", "soccer_rival_1")),
              ("_b", ("soccer_rival_2", "soccer_keeper_hero", "soccer_keeper_rival")),
              ("_c", ("soccer_ball", "soccer_grass", "soccer_field_fantasy", "soccer_out_fantasy")))
    for suffix, keys in groups:
        fantasy16.save_sheet(root + suffix + ext, {k: items[k] for k in keys}, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
