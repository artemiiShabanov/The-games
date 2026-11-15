#!/usr/bin/env python3
"""Футбол × 16/32-bit, набор «Космос» (#136): зеркало `pixel_soccer16.py`. Те же ленты и кадры
(игрок 24×24: 8 направлений × 5 кадров бега, 8 подкатов, 8 «лежит»; мяч 8×8 в два кадра; тайлы
64×64), позы повторяют пиратских игроков, чтобы демка `sport_bit16.gd` ничего не заметила.

Команда героя это космонавты в белых скафандрах с бирюзовым визором, соперники это фиолетовые
пришельцы трёх видов (антенны и красная форма, вытянутая голова и золотая форма, циклоп в тёмной
форме), вратари в своих цветах, мяч это энергосфера, поле это тёмный реголит, вокруг звёзды.

    python3 tools/space_soccer16.py --preview thegames/debug/playtest/env/space_soccer16.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import space16  # noqa: E402
from space16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, GOLD, BRASS, METAL, DARK, RED,  # noqa: E402
                     VIOLET, PLUM)

F = 24
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
RUN = 5


class Look:
    """Кто играет: цвета тела и формы и вид головы. `limb`/`limb_far` это руки и ноги (у космонавта
    рукава и штанины скафандра, у пришельца кожа), `shirt`/`shorts`/`sock` форма, `trim` полоса на
    груди, `glove` перчатки вратаря, `head` вид головы."""

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
    """Голова. Возвращает точки, которые ставятся после обводки и тени (визор, глаза)."""
    marks = []
    kind = look.head
    if kind == "astro":
        c.ellipse(x, y, 3.6, 3.6, WHITE)
        c.rect(x - 2, y + 4, x + 2, y + 4, METAL)
        if back:
            # Затылок: полоса ранца-шлема.
            for xx in range(int(x - 2), int(x + 3)):
                marks.append((xx, y, GREY))
        elif side:
            for yy in (y - 1, y, y + 1):
                for k in (1, 2, 3):
                    marks.append((x + sgn * k, yy, AQUA))
            marks.append((x + sgn * 2, y - 1, SKY))
        else:
            for yy in (y - 1, y, y + 1):
                for xx in range(int(x - 2), int(x + 3)):
                    marks.append((xx, yy, AQUA))
            marks.append((x - 1, y - 1, SKY))
            marks.append((x, y - 1, SKY))
        return marks
    if kind == "antenna":
        c.ellipse(x, y, 3.6, 3.4, VIOLET)
        c.line(x - 2, y - 3, x - 3, y - 6, VIOLET, 1)
        c.line(x + 2, y - 3, x + 3, y - 6, VIOLET, 1)
        marks.append((x - 3, y - 6, GOLD))
        marks.append((x + 3, y - 6, GOLD))
    elif kind == "cone":
        # Вытянутая вверх голова.
        c.ellipse(x, y + 0.5, 3.2, 3.0, VIOLET)
        c.ellipse(x, y - 2.5, 2.4, 3.6, VIOLET)
    else:
        # Циклоп: широкая приплюснутая голова.
        c.ellipse(x, y + 0.5, 4.2, 3.0, VIOLET)
    if back:
        return marks
    if kind == "cyclops":
        ex = x + (sgn * 2 if side else 0)
        for dx in (-1, 0, 1):
            marks.append((ex + dx, y, WHITE))
            marks.append((ex + dx, y + 1, WHITE))
        marks.append((ex + (sgn if side else 0), y + 1, K))
    elif side:
        marks.append((x + sgn * 2, y, K))
        marks.append((x + sgn * 2, y + 1, K))
    else:
        for ex in (x - 2, x + 1):
            marks.append((ex, y, K))
            marks.append((ex, y + 1, K))
    return marks


def _glove(c, look, x, y):
    if look.keeper:
        c.rect(x - 0.5, y, x + 0.5, y + 1.0, look.glove)


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
        if look.head == "astro":
            # Ранец за спиной.
            bx = 8 if sgn > 0 else 15
            c.rect(bx - (1 if sgn > 0 else 0), 10 - bob, bx + (0 if sgn > 0 else 1), 14 - bob, METAL)
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
        if look.head == "astro" and back:
            # Ранец на спине: блок и огонёк.
            c.rect(10, 10 - bob, 13, 14 - bob, METAL)
            marks.append((11, 11 - bob, AQUA))
            marks.append((12, 11 - bob, AQUA))
        for x, k, out in ((6.5, -s, -1), (16.5, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            c.line(x, 11.0 - bob, hand[0], hand[1], look.limb, 2)
            _glove(c, look, hand[0], hand[1])
        marks += _head(c, 11.5 if look.head != "astro" else 11.5, 6 - bob, look, False, back, sgn)
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


# Команды. Герой: белый скафандр, оранжевая полоса, серые «трусы»-пояс, бирюзовые голени.
HERO = Look("astro", WHITE, GREY, WHITE, METAL, AQUA, trim=RED)
# Вратарь героя: жёлтый скафандр, чтобы не путался с полевыми.
KEEPER_HERO = Look("astro", GOLD, BRASS, GOLD, DARK, WHITE, glove=SKY, keeper=True)
RIVAL_0 = Look("antenna", VIOLET, PLUM, RED, DARK, RED)
RIVAL_1 = Look("cone", VIOLET, PLUM, GOLD, NAVY, GOLD)
RIVAL_2 = Look("cyclops", VIOLET, PLUM, DARK, METAL, AQUA, trim=AQUA)
KEEPER_RIVAL = Look("antenna", VIOLET, PLUM, SEA, NAVY, SKY, trim=SKY, glove=WHITE, keeper=True)


# Энергосфера 8×8: тёмный обод, бирюзовое ядро, белая искра бежит по кругу (два кадра, при
# качении мяч «вращается»). o обод, a энергия, s светлая, W искра, n тень.
BALL_MAPS = (
    ("..oooo..",
     ".oasWao.",
     "oasWWsao",
     "oassssao",
     "oaassaao",
     "onaaaano",
     ".onaano.",
     "..oooo.."),
    ("..oooo..",
     ".oaaaao.",
     "oaassaao",
     "oassWsao",
     "oasWWsao",
     "onasssno",
     ".onaano.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "a": AQUA, "s": SKY, "W": WHITE, "n": SEA}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    return c


def deck():
    """Запасной тайл поля в палитре сеттинга 64×64 (ключ `soccer_grass`): настил станции,
    полосы по 32 светлее и темнее, швы плит и заклёпки."""
    c = Canvas(64, 64)
    for x in range(64):
        for y in range(64):
            band = METAL if x < 32 else DARK
            if x % 16 == 0 or y % 16 == 0:
                band = DARK if band == METAL else NAVY
            elif (x % 16, y % 16) in ((2, 2), (13, 13)):
                band = GREY if x < 32 else METAL
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
        "soccer_grass": deck(),
    }


# --- Поле и аут ---------------------------------------------------------------------------------
# Тайлы 64×64 бесшовные, в своих палитрах. Поле темнее пиратского песка: на нём читаются и белые
# скафандры, и фиолетовые пришельцы, и белая разметка демки.

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[int(y) % T][int(x) % T] = v


def regolith():
    """Лунный грунт: сине-серый, укатанные полосы по 32 (как полосы газона), мелкая крошка,
    неглубокие кратеры (тень сверху слева, светлый вал снизу справа), редкие камешки.
    Палитра: 0 глубокая тень, 1 тень, 2 грунт, 3 светлый грунт, 4 блик, 5 камень."""
    pal = _pal(0x23263A, 0x343A54, 0x464E6C, 0x586284, 0x8C98BC, 0x6E6A80)
    c = Canvas(T, T)
    rng = random.Random(31)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 2 if x < 32 else 3
    for _ in range(int(T * T * 0.10)):
        x, y = rng.randrange(T), rng.randrange(T)
        base = c.px[y][x]
        c.px[y][x] = base - 1 if rng.random() < 0.6 else min(base + 1, 3 if x < 32 else 4)
    # Следы укатки: короткие штрихи вдоль полос.
    for _ in range(18):
        x0, y0, ln = rng.randrange(T), rng.randrange(T), rng.randint(3, 7)
        for k in range(ln):
            _wrap(c, x0, y0 + k, 1 if x0 % T < 32 else 2)
    rng = random.Random(9)
    for _ in range(4):
        cx, cy, rr = rng.randrange(T), rng.randrange(T), rng.uniform(2.2, 4.2)
        for y in range(int(cy - rr - 2), int(cy + rr + 3)):
            for x in range(int(cx - rr - 2), int(cx + rr + 3)):
                d = math.hypot(x - cx, y - cy)
                if d <= rr:
                    _wrap(c, x, y, 0 if (x - cx) + (y - cy) < -1 else 1)
                elif d <= rr + 1.1:
                    _wrap(c, x, y, 4 if (x - cx) + (y - cy) > 0 else 1)
    for _ in range(5):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 5)
        _wrap(c, x + 1, y, 4)
        _wrap(c, x + 1, y + 1, 0)
    return c, pal


def stars(frame):
    """Пустота вокруг поля: почти чёрная синева с облаками туманности, звёзды трёх яркостей
    мерцают по кадрам, у ярких крестик. Палитра: 0 чернота, 1 синева, 2 туманность, 3 тусклая
    звезда, 4 звезда, 5 яркая, 6 бирюзовая."""
    pal = _pal(0x05050C, 0x0B0C22, 0x1A1440, 0x3A4070, 0x9AA8E0, 0xFFFFFF, 0x4FC3D9)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            v = (math.sin(x / 64.0 * 2 * math.pi + 1.0) + math.sin(y / 64.0 * 2 * math.pi) +
                 math.sin((x + y) / 64.0 * 4 * math.pi))
            # Туманность едва заметна: редкая штриховка, без сплошных пятен (иначе виден повтор тайла).
            cell = 0
            if v > 1.9 and (x + y) % 2 == 0:
                cell = 2
            elif v > 1.2 and (x * 3 + y) % 4 == 0:
                cell = 1
            c.px[y][x] = cell
    rng = random.Random(17)
    for k in range(34):
        x, y = rng.randrange(T), rng.randrange(T)
        tw = (k + frame) % 4
        if k % 9 == 4:
            c.px[y][x] = 6 if tw < 2 else 3
            continue
        c.px[y][x] = 5 if tw == 0 else 4 if tw < 3 else 3
        if k % 6 == 0 and tw == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                _wrap(c, x + dx, y + dy, 3)
    return c, pal


def fields():
    """Тайлы поля и аута космоса → (холст, палитра). Аут лентой из 4 кадров."""
    cv, pal = regolith()
    frames = [stars(f) for f in range(4)]
    return {
        "soccer_field_space": (cv, pal),
        "soccer_out_space": (strip([fr[0] for fr in frames]), frames[0][1]),
    }


def preview(path):
    items = space16.shaded(sprites())
    items.update(fields())
    space16.save_sheet(path, items, scale=3, max_w=480)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
