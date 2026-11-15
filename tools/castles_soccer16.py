#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Замки» (#137): зеркало `space_soccer16.py` (то зеркалит
`pixel_soccer16.py`). Те же ленты и кадры (игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов,
8 «лежит»; мяч 8×8 в два кадра; тайлы 64×64), позы повторяют космических и пиратских игроков,
чтобы демка `sport_bit16.gd` ничего не заметила.

Команда героя это рыцари в стальных латах с красными табардами и красным плюмажем, соперники это
люди чужого замка трёх видов (стражник в котелке и багровой тунике, чёрный рыцарь с рогатым шлемом,
наёмник в кожаном капюшоне), вратари в своих цветах (у героя золотой сюрко, у соперника каменно-
серая стёганка и глухой горшкообразный шлем), мяч это кожаный набивной мяч со швом, поле это
стриженый луг в полосах, вокруг кроны дубов с розами. Цвета те же роли, что у `castles16.py`.

    python3 tools/castles_soccer16.py --preview thegames/debug/playtest/env/castles_soccer16.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import castles16  # noqa: E402
from castles16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                       METAL, DARK, RED, VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и формы и вид головы. `limb`/`limb_far` это руки и ноги (у рыцаря
    латы, у стражника кольчуга, у наёмника кожа), `shirt`/`shorts`/`sock` форма, `trim` пояс на
    груди, `glove` перчатки вратаря, `head` вид головы (knight, kettle, horned, coif, bucket)."""

    def __init__(self, head, limb, limb_far, shirt, shorts, sock, trim=None, glove=None, keeper=False):
        self.head = head
        self.limb = limb
        self.limb_far = limb_far
        self.shirt = shirt
        self.shorts = shorts
        self.sock = sock
        self.trim = trim
        self.glove = glove
        self.keeper = keeper


def _head(c, x, y, look, side, back, sgn):
    """Голова. Возвращает точки, которые ставятся после обводки и тени (прорези, глаза, блики)."""
    marks = []
    kind = look.head
    if kind == "knight":
        # Стальной шлем с красным гребнем по верху и хвостом назад, тёмная прорезь забрала.
        c.ellipse(x, y, 3.6, 3.6, WHITE)
        c.rect(x - 2, y + 4, x + 2, y + 4, METAL)
        if back:
            c.rect(x - 1, y - 5, x, y - 3, RED)
            c.rect(x - 1, y - 2, x, y + 2, RED)
            for xx in range(int(x - 2), int(x + 3)):
                marks.append((xx, y + 3, GREY))
        elif side:
            c.rect(x - sgn * 3 if sgn > 0 else x - 1, y - 5, x - sgn * 1 if sgn > 0 else x + 3, y - 4, RED)
            c.rect(x - 3 if sgn > 0 else x + 2, y - 3, x - 2 if sgn > 0 else x + 3, y - 1, RED)
            for k in (1, 2, 3):
                marks.append((x + sgn * k, y, K))
                marks.append((x + sgn * k, y + 1, GREY))
            marks.append((x + sgn * 3, y - 2, SKY))
        else:
            c.rect(x - 1, y - 5, x, y - 3, RED)
            for xx in range(int(x - 2), int(x + 3)):
                marks.append((xx, y, K))
            for xx in (x - 1, x):
                marks.append((xx, y + 1, GREY))
                marks.append((xx, y + 2, METAL))
            marks.append((x - 2, y - 2, SKY))
        return marks
    if kind == "kettle":
        # Стражник: лицо, кольчужный подворотник, котелок с полями.
        c.ellipse(x, y + 1.2, 3.2, 2.8, SKIN)
        c.rect(x - 3, y + 3, x + 3, y + 4, DARK)
        c.ellipse(x, y - 1.6, 4.0, 2.4, METAL)
        c.rect(x - 5, y, x + 5, y, GREY)
        marks.append((x - 2, y - 2, WHITE))
        marks.append((x - 1, y - 3, WHITE))
        if back:
            c.rect(x - 3, y + 1, x + 3, y + 3, DARK)
            return marks
    elif kind == "horned":
        # Чёрный рыцарь: тёмный глухой шлем и два рога из кости, красные глаза.
        c.ellipse(x, y, 3.8, 3.6, DARK)
        c.rect(x - 2, y + 4, x + 2, y + 4, DARK)
        for s2 in (-1, 1):
            c.line(x + s2 * 3, y - 2, x + s2 * 5, y - 4, WHITE, 1)
            c.line(x + s2 * 5, y - 4, x + s2 * 5, y - 6, WHITE, 1)
        for xx, yy in ((x - 3, y - 2), (x - 2, y - 3), (x - 1, y - 3)):
            marks.append((xx, yy, METAL))
        if back:
            return marks
    elif kind == "coif":
        # Наёмник: кожаный капюшон, лицо в прорези, рыжая щетина.
        c.ellipse(x, y, 3.8, 3.6, TAN)
        c.ellipse(x, y - 2.5, 3.0, 1.6, BRASS)
        if not back:
            fx = x + (sgn if side else 0)
            c.ellipse(fx, y + 1, 2.4 if not side else 2.0, 2.4, SKIN)
        if back:
            return marks
    else:
        # Вратарь соперника: глухой горшкообразный шлем с узкой щелью и гребнем-ободом.
        c.rect(x - 3, y - 4, x + 3, y + 3, METAL)
        c.rect(x - 4, y - 1, x + 4, y - 1, GREY)
        c.rect(x - 4, y + 3, x + 4, y + 3, GREY)
        marks.append((x - 2, y - 3, WHITE))
        marks.append((x - 1, y - 3, WHITE))
        if back:
            return marks
    if kind == "kettle" or kind == "coif":
        if side:
            marks.append((x + sgn * 2, y + 1, K))
            marks.append((x + sgn * 2, y + 2, BRASS if kind == "coif" else TAN))
        else:
            for ex in (x - 2, x + 1):
                marks.append((ex, y + 1, K))
            marks.append((x - 1, y + 3, BRASS if kind == "coif" else TAN))
            marks.append((x, y + 3, BRASS if kind == "coif" else TAN))
    elif kind == "horned":
        if side:
            marks.append((x + sgn * 2, y, RED))
            marks.append((x + sgn * 3, y, RED))
        else:
            for ex in (x - 2, x + 1):
                marks.append((ex, y, RED))
                marks.append((ex, y + 1, RED))
    else:
        for dx in ((1, 2, 3) if side else (-2, -1, 0, 1, 2)):
            marks.append(((x + sgn * dx) if side else (x + dx), y + 1, K))
    return marks


def _glove(c, look, x, y):
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)


def player(d, frame, look, mode="run"):
    """Игрок 24×24, та же фигура и те же кадры, что у пиратов и космоса: стойка и четыре кадра бега по
    восьми направлениям, подкат (у вратаря прыжок за мячом), лежит."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    marks = []
    if mode == "down":
        c.line(18, 17, 22, 15, look.limb, 2)
        c.line(18, 19, 22, 20, look.limb, 2)
        c.rect(21, 14, 22, 15, DARK)
        c.rect(21, 20, 22, 21, DARK)
        c.line(9, 15, 6, 12, look.limb, 2)
        c.rect(7, 16, 14, 20, look.shirt)
        if look.trim is not None:
            c.rect(10, 16, 10, 20, look.trim)
        c.rect(15, 16, 17, 20, look.shorts)
        marks = _head(c, 4, 18, look, True, False, 1)
        if look.keeper:
            c.rect(5, 11, 6, 12, look.glove)
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
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, look.limb, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, look.limb, 2)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, look.shirt, 5)
            c.line(tx - ux, ty - uy, tx, ty, look.shorts, 5)
            hx, hy = cx + ux * 5.0, cy + uy * 5.0 - 1.0
            c.line(cx + ux * 2.0 - uy * 2.0, cy + uy * 2.0 + ux * 2.0, hx + ux * 5.0 - uy * 2.0, hy + uy * 5.0 + ux * 2.0, look.shirt, 2)
            c.line(cx + ux * 2.0 + uy * 2.0, cy + uy * 2.0 - ux * 2.0, hx + ux * 5.0 + uy * 2.0, hy + uy * 5.0 - ux * 2.0, look.shirt, 2)
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
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, DARK)
        c.line(tx, ty, cx, cy, look.shirt, 5)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, look.shorts, 5)
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
            c.line(knee[0], knee[1], foot[0], foot[1], look.sock, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0, DARK)
        if look.head == "knight":
            # Плащ за спиной узкой полосой.
            bx = 8 if sgn > 0 else 15
            c.rect(bx - (1 if sgn > 0 else 0), 10 - bob, bx + (0 if sgn > 0 else 1), 16 - bob, PLUM)
        c.rect(9, 10 - bob, 14, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(9, 12 - bob, 14, 12 - bob, look.trim)
        c.rect(9, 16 - bob, 14, 17 - bob, look.shorts)
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        c.line(11.5, 11.0 - bob, hand[0], hand[1], look.limb, 2)
        _glove(c, look, hand[0], hand[1])
        marks = _head(c, 12 if sgn > 0 else 11, 6 - bob, look, True, back, sgn)
    else:
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, look.limb)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, look.sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, DARK)
        c.rect(8, 10 - bob, 15, 15 - bob, look.shirt)
        if look.trim is not None:
            c.rect(8, 12 - bob, 15, 12 - bob, look.trim)
        c.rect(8, 16 - bob, 15, 17 - bob, look.shorts)
        if look.head == "knight" and back:
            # Плащ на спине: широкая полоса и золотая застёжка.
            c.rect(9, 10 - bob, 14, 16 - bob, PLUM)
            marks.append((11, 11 - bob, GOLD))
            marks.append((12, 11 - bob, GOLD))
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
# Команды. Герой: стальные латы, красный табард с золотым поясом, серые набедренники, плащ.
HERO = Look("knight", WHITE, GREY, RED, GREY, METAL, trim=GOLD)
# Вратарь героя: золотой сюрко, чтобы не путался с полевыми, золотые перчатки.
KEEPER_HERO = Look("knight", WHITE, GREY, GOLD, DARK, GREY, trim=RED, glove=GOLD, keeper=True)
RIVAL_0 = Look("kettle", METAL, PLUM, VIOLET, DARK, PLUM, trim=GOLD)
RIVAL_1 = Look("horned", DARK, PLUM, PLUM, DARK, DARK, trim=RED)
RIVAL_2 = Look("coif", SKIN, TAN, TAN, PLUM, BRASS, trim=DARK)
KEEPER_RIVAL = Look("bucket", METAL, GREY, METAL, PLUM, DARK, trim=VIOLET, glove=GOLD, keeper=True)


# Кожаный набивной мяч 8×8: тёмный обод, кожа, светлый блик, крест-накрест шов из стежков
# (два кадра, шов поворачивается, мяч «катится»). o обод, a кожа, s блик, q шов, n тень.
BALL_MAPS = (
    ("..oooo..",
     ".oasaao.",
     "osssaqao",
     "oaaaqaao",
     "oaqqqqao",
     "onaqaano",
     ".onqanao",
     "..oooo.."),
    ("..oooo..",
     ".oasaao.",
     "oassqaao",
     "oqaqaaao",
     "oaqaqaao",
     "oaaqaano",
     ".onaqnno",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "a": TAN, "s": SKIN, "q": DARK, "n": BRASS}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def deck():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): стриженый луг,
    правая половина светлее, кустики травы."""
    c = Canvas(64, 64)
    rng = random.Random(5)
    for x in range(64):
        for y in range(64):
            c.set(x, y, SEA if x < 32 or (x * 7 + y * 3) % 5 else AQUA)
    for _ in range(90):
        x, y = rng.randrange(64), rng.randrange(64)
        if x < 32:
            c.set(x, y, NAVY)
            c.set(x, (y + 1) % 64, NAVY)
        else:
            c.set(x, y, SEA)
            c.set(x, (y + 1) % 64, SEA)
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
# Тайлы 64×64 бесшовные, в своих палитрах. Луг средней яркости: на нём читаются и стальные латы,
# и багровая стража, и белая разметка демки.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def meadow():
    """Стриженый луг: полосы по 32 (как полосы газона), короткие штрихи травинок с бликом,
    клевер, редкие ромашки и жёлтые цветки, пара проплешин. Палитра: 0 глубокая тень, 1 тень,
    2 трава, 3 светлая трава, 4 блик травинки, 5 ромашка, 6 цветок, 7 земля."""
    pal = _pal(0x24502B, 0x2F6E37, 0x3C8843, 0x4F9F4C, 0x82C65F, 0xF4F0E0, 0xF4D35E, 0x8B6A45)
    c = Canvas(T, T)
    rng = random.Random(23)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    # Травинки: вертикальный штрих из двух-трёх пикселей, внизу тень, на конце блик.
    for _ in range(95):
        x, y = rng.randrange(T), rng.randrange(T)
        base = 2 if x % T < 32 else 3
        _wrap(c, x, y + 2, base - 1)
        _wrap(c, x, y + 1, base)
        _wrap(c, x, y, 4)
    # Клевер: тройка тёмных точек.
    for _ in range(9):
        x, y = rng.randrange(T), rng.randrange(T)
        for dx, dy in ((0, 0), (2, 1), (1, 2)):
            _wrap(c, x + dx, y + dy, 1 if x % T < 32 else 2)
    # Проплешины: маленькое пятно земли с тёмной кромкой снизу.
    for _ in range(2):
        cx, cy = rng.randrange(T), rng.randrange(T)
        for y in range(-2, 3):
            for x in range(-3, 4):
                if (x / 3.2) ** 2 + (y / 2.2) ** 2 <= 1:
                    _wrap(c, cx + x, cy + y, 7)
        for x in range(-2, 3):
            _wrap(c, cx + x, cy + 3, 0)
    # Цветы.
    for k in range(8):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 5 if k % 2 == 0 else 6)
        if k % 2 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                _wrap(c, x + dx, y + dy, 5)
            _wrap(c, x, y, 6)
    return c, pal


def canopy(frame):
    """Окружение поля: вид сверху на кроны дубов, в ветре листва шевелится (4 кадра). Круглые
    кроны с тенью снизу справа и светлой кромкой сверху слева, мелкая листва бликует по кадрам,
    между кронами тёмные просветы, на ветках редкие красные розы. Палитра: 0 просвет, 1 тень,
    2 листва, 3 светлая листва, 4 блик, 5 яркий блик, 6 роза."""
    pal = _pal(0x14301F, 0x1C4034, 0x2A6A37, 0x3A8442, 0x5CA84C, 0x9ADB62, 0xD03438)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 0
    rng = random.Random(41)
    crowns = [(rng.randrange(T), rng.randrange(T), rng.uniform(8.0, 11.5)) for _ in range(11)]
    for cx, cy, r in crowns:
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(x - cx, y - cy)
                if d <= r:
                    v = 2
                    if (x - cx) + (y - cy) > r * 0.55:
                        v = 1
                    elif (x - cx) + (y - cy) < -r * 0.7 and d > r * 0.45:
                        v = 3
                    _wrap(c, x, y, v)
    rng = random.Random(7)
    for k in range(120):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.px[y][x] == 0:
            continue
        tw = (k + frame) % 4
        c.px[y][x] = 5 if tw == 0 else 4 if tw == 1 else c.px[y][x]
        if tw == 0:
            _wrap(c, x + 1, y, 4)
    for k in range(9):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.px[y][x] != 0:
            _wrap(c, x, y, 6 if (k + frame) % 4 else 4)
    return c, pal


def fields():
    """Тайлы поля и аута замков → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = meadow()
    frames = [canopy(f) for f in range(4)]
    return {
        "soccer_field_castles": (cv, pal),
        "soccer_out_castles": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    items = castles16.shaded(sprites())
    items.update(fields())
    # Лист высок: игроки отдельно, мяч с тайлами отдельно (суффикс _b у второго файла).
    keys = list(items)
    first = {k: items[k] for k in keys[:3]}
    second = {k: items[k] for k in keys[3:6]}
    third = {k: items[k] for k in keys[6:]}
    base, ext = os.path.splitext(path)
    castles16.save_sheet(path, first, scale=3, max_w=480)
    castles16.save_sheet(base + "_b" + ext, second, scale=3, max_w=480)
    castles16.save_sheet(base + "_c" + ext, third, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
