#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Замки» (#137): зеркало `space_soccer16.py` и `pixel_soccer16.py`.
Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов, 8 «лежит»; мяч 8×8
в два кадра; тайлы 64×64), позы повторяют пиратских игроков, чтобы демка `sport_bit16.gd` ничего
не заметила.

Команда героя это рыцари из `castles16.py`: стальные латы, ведёрный шлем с красным плюмажем,
красный табард с золотым поясом. Соперники трёх видов, все в тёмном, чтобы не путались со сталью
героя: стражник чужого замка (шлем-котелок с полями, чёрная кольчуга, багровая туника),
разбойник (бурый капюшон с острым верхом, повязка на лице, голые руки, горчичная куртка),
чёрный рыцарь (тёмный шлем с костяными рогами, красная щель забрала). Вратарь героя в золотом
табарде, вратарь соперника стражник в синей тунике, оба в светлых рукавицах. Мяч кожаный
набивной со швом и стежками, поле это турнирный газон замкового двора с полосами стрижки,
вокруг брусчатка с мхом, соломой и лужами, в лужах по кадрам бежит блик.

    python3 tools/castles_soccer16.py --preview thegames/debug/playtest/env/castles_soccer16.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import castles16  # noqa: E402
from castles16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK,  # noqa: E402
                       RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и формы и вид головы. `limb`/`limb_far` это руки и бёдра (у рыцаря
    сталь, у стражи кольчуга, у разбойника кожа), `shirt`/`shorts` туника и её подол, `sock`
    голени, `boot` обувь, `belt` пояс, `trim` полоса на груди, `hand` кисть полевого игрока,
    `glove` рукавицы вратаря, `head` вид головы, `crest` цвет герба на груди."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, trim=None, glove=None, keeper=False,
                 belt=None, boot=DARK, hand=None, crest=None):
        self.head = head
        self.limb = limb
        self.limb_far = limb_far
        self.shirt = shirt
        self.shorts = shorts
        self.sock = sock
        self.trim = trim
        self.glove = glove
        self.keeper = keeper
        self.belt = belt
        self.boot = boot
        self.hand = hand
        self.crest = crest


def _span(x, half):
    """Целые края полосы с центром `x` (целым или на полпикселя) и полушириной `half`."""
    return int(math.ceil(x - half)), int(math.floor(x + half))


def _helm(c, x, y, steel, rim, side, back, sgn, marks):
    """Ведёрный шлем: коробка с плоским верхом, уже плеч, обод понизу. Прорезь ставится после
    обводки: анфас во всю ширину, в профиль от середины до передней грани."""
    x0, x1 = _span(x, 3.1 if side else 2.6)
    c.rect(x0, y - 3, x1, y + 3, steel)
    c.rect(x0, y + 3, x1, y + 3, rim)
    c.rect(x0 + 1, y + 4, x1 - 1, y + 4, rim)
    if back:
        return x0, x1
    if side:
        front = x1 if sgn > 0 else x0
        for k in range(4):
            marks.append((front - sgn * k, y, K))
        marks.append((front - sgn, y + 2, rim))
    else:
        for xx in range(x0 + 1, x1):
            marks.append((xx, y, K))
        marks.append((x0 + 1, y + 2, rim))
        marks.append((x1 - 1, y + 2, rim))
    return x0, x1


def _head(c, x, y, look, side, back, sgn):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (прорезь, глаза)."""
    marks = []
    kind = look.head
    if kind == "knight":
        # Хвост плюмажа летит за затылком, гребень стоит на темени.
        if side:
            c.line(x - sgn * 2, y - 4, x - sgn * 5, y - 2, RED, 2)
            c.line(x - sgn * 5, y - 2, x - sgn * 5, y, RED, 2)
        x0, x1 = _helm(c, x, y, GREY, METAL, side, back, sgn, marks)
        c.rect(x0 + 1, y - 5, x1 - 1, y - 4, RED)
        marks.append((x0 + 1, y - 3, WHITE))
        marks.append((x0 + 2, y - 3, WHITE))
        if back:
            # Со спины плюмаж падает от гребня на затылок.
            mid = (x0 + x1) // 2
            for yy in range(int(y - 3), int(y + 2)):
                marks.append((mid, yy, RED))
                marks.append((mid + 1, yy, RED if yy < y + 1 else TAN))
        return marks
    if kind == "horned":
        # Рога: от висков в стороны и вверх, костяные, кончики светлее.
        for q in (-1, 1):
            if side and q == sgn:
                continue
            c.line(x + q * 3, y - 2, x + q * 5, y - 3, WHITE, 1)
            c.line(x + q * 5, y - 3, x + q * 5, y - 6, WHITE, 1)
        if side:
            c.line(x, y - 4, x - sgn, y - 7, WHITE, 1)
        x0, x1 = _helm(c, x, y, DARK, K, side, back, sgn, marks)
        # Прорезь у чёрного рыцаря светится красным.
        marks[:] = [(mx, my, RED if v == K else TAN) for mx, my, v in marks]
        marks.append((x0 + 1, y - 3, METAL))
        if back:
            # Багровый гребень вдоль затылка.
            mid = (x0 + x1) // 2
            for yy in range(int(y - 3), int(y + 3)):
                marks.append((mid, yy, TAN))
        return marks
    if kind == "kettle":
        # Кольчужный капюшон, лицо под широкими полями шлема-котелка.
        c.ellipse(x, y + 0.5, 3.4, 3.4, DARK)
        if not back:
            if side:
                f0, f1 = sorted((int(round(x)), int(round(x + sgn * 3))))
            else:
                f0, f1 = _span(x, 2.4)
            c.rect(f0, y, f1, y + 2, SKIN)
        b0, b1 = _span(x, 4.6)
        c.ellipse(x, y - 2, 3.3, 2.3, GREY)
        c.rect(b0, y - 1, b1, y - 1, GREY)
        marks.append((int(math.ceil(x - 1.5)), y - 3, WHITE))
        marks.append((b0 + 1, y - 1, WHITE))
        marks.append((b0 + 2, y - 1, WHITE))
        if back:
            return marks
        if side:
            marks.append((x + sgn * 2, y + 1, K))
        else:
            marks.append((f0, y + 1, K))
            marks.append((f1, y + 1, K))
        return marks
    # Разбойник: капюшон с острым верхом, сбитым назад, лицо до глаз закрыто тёмной повязкой.
    c.ellipse(x, y, 3.6, 3.6, BRASS)
    tip = x - (sgn * 2 if side else 0)
    c.poly([(x - 2, y - 3), (x + 2, y - 3), (tip, y - 6)], BRASS)
    c.set(tip, y - 6, BRASS)
    if back:
        # Шов капюшона по затылку.
        for yy in range(int(y - 2), int(y + 3)):
            marks.append((int(round(x)), yy, DARK))
        return marks
    if side:
        f0, f1 = sorted((int(round(x + sgn)), int(round(x + sgn * 3))))
    else:
        f0, f1 = _span(x, 2.4)
    c.rect(f0, y, f1, y, SKIN)
    c.rect(f0, y + 1, f1, y + 2, DARK)
    if side:
        marks.append((x + sgn * 2, y, K))
    else:
        marks.append((f0, y, K))
        marks.append((f1, y, K))
    return marks


def _hand(c, look, x, y):
    """Кисть: у вратаря рукавица на два пикселя, у полевого латная перчатка или кулак."""
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
    if mode == "down":
        # Лежит на спине поперёк: голова слева, ноги справа, рука откинута.
        c.line(18, 17, 22, 15, look.sock, 2)
        c.line(18, 19, 22, 20, look.sock, 2)
        c.rect(21, 14, 22, 15, look.boot)
        c.rect(21, 20, 22, 21, look.boot)
        c.line(9, 15, 6, 12, look.limb, 2)
        c.rect(7, 16, 14, 20, look.shirt)
        if look.trim is not None:
            c.rect(10, 16, 10, 20, look.trim)
        if look.belt is not None:
            c.rect(14, 16, 14, 20, look.belt)
        c.rect(15, 16, 17, 20, look.shorts)
        marks = _head(c, 4, 18, look, True, False, 1)
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
        if look.keeper:
            # Прыжок за мячом: руки в рукавицах вытянуты вперёд, ноги сзади.
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.sock, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.sock, 2)
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
        # Подкат по ходу: нога вытянута вперёд, вторая согнута, тело сзади низко.
        fx, fy = cx + ux * 8.0, cy + uy * 8.0
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, look.limb_far, 2)
        c.line(cx, cy, fx, fy, look.limb, 2)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, look.sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, look.boot)
        c.line(tx, ty, cx, cy, look.shirt, 5)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, 5)
        if look.belt is not None:
            c.line(cx - ux * 2.0 - uy * 2.0, cy - uy * 2.0 + ux * 2.0, cx - ux * 2.0 + uy * 2.0, cy - uy * 2.0 - ux * 2.0,
                   look.belt, 1)
        c.line(tx, ty, tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0, look.limb, 2)
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
                _arm(c, 11.5, 11.0 - bob, hand[0], hand[1], look.limb_far)
                _hand(c, look, hand[0], hand[1])
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
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0,
                   look.boot)
        c.rect(9, 10 - bob, 14, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(9, 12 - bob, 14, 12 - bob, look.trim)
        c.rect(9, 16 - bob, 14, 17 - bob, look.shorts)
        if look.belt is not None:
            c.rect(9, 15 - bob, 14, 15 - bob, look.belt)
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        _arm(c, 11.5, 11.0 - bob, hand[0], hand[1], look.limb)
        _hand(c, look, hand[0], hand[1])
        marks = _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.limb)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, look.boot)
        c.rect(8, 10 - bob, 15, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(8, 12 - bob, 15, 12 - bob, look.trim)
        c.rect(8, 16 - bob, 15, 17 - bob, look.shorts)
        if look.belt is not None:
            c.rect(8, 15 - bob, 15, 15 - bob, look.belt)
        if back:
            # Разрез подола по спине.
            marks.append((11, 17 - bob, K))
            marks.append((12, 17 - bob, K))
        elif look.crest is not None:
            # Герб на груди: ромб в четыре пикселя.
            for px, py in ((11, 12), (12, 12), (11, 13), (12, 13)):
                marks.append((px, py - bob, look.crest))
        for x, k, out in ((6.5, -s, -1), (16.5, s, 1)):
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


# Команды. Герой: рыцарь из основы, стальные руки и ноги, красный табард, золотой пояс и герб.
HERO = Look("knight", GREY, METAL, RED, RED, GREY, belt=GOLD, hand=METAL, crest=GOLD)
# Вратарь героя: золотой табард с красным поясом, чтобы не путался с полевыми.
KEEPER_HERO = Look("knight", GREY, METAL, GOLD, GOLD, GREY, belt=RED, glove=WHITE, keeper=True)
# Стражник чужого замка: кольчуга, багровая туника под ремнём, бурые сапоги.
RIVAL_0 = Look("kettle", METAL, DARK, TAN, TAN, DARK, belt=DARK, boot=BRASS, hand=SKIN)
# Разбойник: голые руки, горчичная куртка с бурой перевязью, тёмные штаны.
RIVAL_1 = Look("hood", SKIN, BRASS, GOLD, DARK, DARK, trim=BRASS, belt=BRASS, boot=BRASS, hand=SKIN)
# Чёрный рыцарь: тёмные латы, багровая полоса и подол.
RIVAL_2 = Look("horned", METAL, DARK, DARK, TAN, METAL, trim=TAN, boot=K, hand=DARK)
KEEPER_RIVAL = Look("kettle", SEA, NAVY, SEA, NAVY, DARK, trim=SKY, belt=DARK, boot=BRASS, glove=WHITE, keeper=True)


# Кожаный набивной мяч 8×8: светлая кожа, шов из тёмной нити со стежками по бокам; во втором
# кадре шов лёг поперёк (при качении мяч «вращается»). o обод, l кожа, L блик, b тень кожи,
# d шов, s стежок.
BALL_MAPS = (
    ("..oooo..",
     ".oLldbo.",
     "oLlldlbo",
     "ollsdslo",
     "ollldlbo",
     "olbsdsbo",
     ".obbdbo.",
     "..oooo.."),
    ("..oooo..",
     ".oLllbo.",
     "oLlslsbo",
     "oddddddo",
     "ollslsbo",
     "ollllbbo",
     ".obbbbo.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "l": SKIN, "L": WHITE, "b": BRASS, "d": DARK, "s": BRASS}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def lawn():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): газон, полосы стрижки
    по 32 (светлая сплошная и тёмная штриховкой), травинки и редкие одуванчики."""
    c = Canvas(64, 64)
    rng = random.Random(5)
    for x in range(64):
        for y in range(64):
            v = VIOLET
            if x >= 32 and x % 2 == 0 and (y + x // 2) % 2 == 0:
                v = PLUM
            elif x < 32 and rng.random() < 0.05:
                v = PLUM
            c.set(x, y, v)
    for _ in range(7):
        x, y = rng.randrange(1, 63), rng.randrange(1, 63)
        c.set(x, y, GOLD)
        c.set(x, y + 1, PLUM)
    return c


# Имена зеркала: сборщик и соседние модули могут звать тайлы по ним.
deck = lawn


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
# Тайлы 64×64 бесшовные, в своих палитрах. Газон приглушён и темнее травы платформера: на нём
# читаются и сталь с красным, и тёмные соперники, и светлая разметка демки.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def turf():
    """Турнирный газон: полосы стрижки по 32, травинки в два пикселя (тёмный корень, светлый
    кончик), пятна клевера, вытоптанные проплешины и редкие одуванчики.
    Палитра: 0 глубокая тень, 1 тёмная трава, 2 трава, 3 светлая полоса, 4 кончик травинки,
    5 одуванчик."""
    pal = _pal(0x21523A, 0x2C6A3E, 0x3A8442, 0x479646, 0x74BC5C, 0xF4C84A)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    rng = random.Random(21)
    # Травинки: корень на тон темнее полосы, кончик светлее.
    for _ in range(210):
        x, y = rng.randrange(T), rng.randrange(T)
        base = 2 if x < 32 else 3
        _wrap(c, x, y, base - 1)
        if rng.random() < 0.45:
            _wrap(c, x, y - 1, 4 if rng.random() < 0.5 else base + (1 if base == 2 else 0))
    # Клевер: тёмные розетки в три листка.
    for _ in range(7):
        x, y = rng.randrange(T), rng.randrange(T)
        for ox, oy in ((0, 0), (1, 1), (-1, 1), (0, 2)):
            _wrap(c, x + ox, y + oy, 1)
        _wrap(c, x, y + 1, 0)
    # Проплешины от копыт и сапог: короткие тёмные дуги.
    for _ in range(5):
        x, y = rng.randrange(T), rng.randrange(T)
        for k in range(4):
            _wrap(c, x + k, y + (1 if k in (0, 3) else 0), 0 if k in (1, 2) else 1)
    for _ in range(4):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 5)
        _wrap(c, x, y + 1, 0)
    return c, pal


# Ряды брусчатки: ширины камней в сумме 64, ряды сдвинуты, чтобы швы не вставали в столбик.
_ROWS = ((12, 10, 14, 12, 16), (16, 12, 10, 14, 12), (10, 14, 16, 12, 12), (14, 12, 12, 16, 10))
# Лужи: центр и полуоси. Лежат в просевших местах поверх камней.
_PUDDLES = ((19, 21, 6.5, 2.6), (47, 52, 5.0, 2.2))


def cobbles(frame):
    """Брусчатка двора вокруг поля: камни разной ширины со скруглёнными углами и фаской (свет
    сверху слева), мох в швах, соломинки, две лужи с небом; блик в лужах бежит по кадрам.
    Палитра: 0 шов, 1 тень камня, 2 камень, 3 светлый камень, 4 блик фаски, 5 мох, 6 солома,
    7 вода, 8 блик воды."""
    pal = _pal(0x1E1C24, 0x4A474E, 0x65625F, 0x7C7876, 0x9E9CA0, 0x2A6A3E, 0xD8C080, 0x3A5C98, 0xD3ECF6)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 0
    rng = random.Random(3)
    for r in range(8):
        row = r * 8
        x0 = -(r * 5 % 9)
        for w in _ROWS[r % 4]:
            t = rng.choice((2, 2, 3))
            for y in range(row + 1, row + 8):
                for x in range(x0 + 1, x0 + w):
                    v = t
                    edge_x = x in (x0 + 1, x0 + w - 1)
                    edge_y = y in (row + 1, row + 7)
                    if edge_x and edge_y:
                        continue
                    if y == row + 1 or x == x0 + 1:
                        v = t + 1
                    if y == row + 7 or x == x0 + w - 1:
                        v = 1
                    _wrap(c, x, y, v)
            # Щербина на камне.
            if rng.random() < 0.5:
                sx, sy = x0 + rng.randint(3, w - 4), row + rng.randint(3, 5)
                _wrap(c, sx, sy, 1)
                _wrap(c, sx + 1, sy + 1, 1)
            x0 += w
    # Мох растёт в швах.
    for _ in range(46):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.px[y][x] == 0:
            _wrap(c, x, y, 5)
            if c.px[y][(x + 1) % T] == 0:
                _wrap(c, x + 1, y, 5)
    # Солома с турнира: короткие косые штрихи.
    for _ in range(6):
        x, y, lean = rng.randrange(T), rng.randrange(T), rng.choice((-1, 1))
        for k in range(3):
            _wrap(c, x + k, y + (k * lean) // 2, 6)
    for cx, cy, rx, ry in _PUDDLES:
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                q = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if q <= 1.0:
                    # Кромка сверху тёмная: край камня над водой.
                    _wrap(c, x, y, 0 if q > 0.72 and y < cy else 7)
        # Блик: штрих в два-три пикселя, по кадрам переходит слева направо.
        gx = cx - rx * 0.5 + frame * rx * 0.33
        _wrap(c, gx, cy, 8)
        _wrap(c, gx + 1, cy, 8)
        if frame % 2 == 0:
            _wrap(c, gx + 2, cy + 1, 8)
    return c, pal


# Имена зеркала для тех же ролей: грунт поля и аут вокруг.
regolith = turf
stars = cobbles


def fields():
    """Тайлы поля и аута замков → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = turf()
    frames = [cobbles(f) for f in range(4)]
    return {
        "soccer_field_castles": (cv, pal),
        "soccer_out_castles": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    """Лист набора. Он выше 1500 пикселей, поэтому делится: четыре команды в `path`, вратарь
    соперника, мяч и тайлы в файле с суффиксом `_b`."""
    items = castles16.shaded(sprites())
    items.update(fields())
    keys = list(items)
    cut = 4
    root, ext = os.path.splitext(path)
    castles16.save_sheet(path, {k: items[k] for k in keys[:cut]}, scale=3, max_w=480)
    castles16.save_sheet(root + "_b" + ext, {k: items[k] for k in keys[cut:]}, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
