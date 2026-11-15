"""Рисунок футбола × 16/32-bit «один на одного» (#101) для pixel_sprites16.py, графика по
Sensible Soccer (решение 2026-11-12): вид сверху, стоящие игроки 24×24 в восьми направлениях
(стойка и четыре кадра бега, подкат, лежит; с плейтеста 2026-11-15 крупнее и подробнее), формы
четырёх цветов и двух вратарей в перчатках, мяч, трава полосами.
Всё в палитре спрайтов сеттинга.
"""
import math

from pixel_sprites16 import (Canvas, strip, K, NAVY, SEA, AQUA, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD, BARK,
                             RED, LEAF, PINE)

F = 24
# Направления по кругу: 0 вправо, дальше по часовой (y вниз), как угол atan2.
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]
# Кадров на направление: стойка и четыре кадра бега (шаг, пролёт, шаг другой ногой, пролёт).
RUN = 5


def _head(c, x, y, hair, side, back, sgn):
    """Голова 7×7: волосы шапкой, сзади затылок целиком, в профиль ещё и за ухом."""
    c.ellipse(x, y, 3.4, 3.4, SKIN)
    for yy in range(int(y - 4), int(y + 5)):
        for xx in range(int(x - 4), int(x + 5)):
            if c.get(xx, yy) != SKIN:
                continue
            if back or yy <= y - 2 or (side and (xx - x) * sgn <= -2 and yy <= y + 1):
                c.set(xx, yy, hair)


def player(d, frame, shirt, shorts, hair=BARK, mode="run", shirt2=None, keeper=False):
    """Игрок 24×24 (плейтест 2026-11-15, #132: крупнее, с выраженными руками и ногами, чтобы бег
    читался). Стоящая фигурка под крутым углом: голова, футболка с рукавами, трусы, ноги с
    гетрами и бутсами. Взгляд вниз: лицо; вверх: затылок; вбок: профиль. Бег в четыре кадра: ноги
    и руки в противофазе, на пролёте тело выше на пиксель. У вратаря длинные рукава и перчатки."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    sgn = 1 if dx >= 0 else -1
    sleeve = shirt if keeper else SKIN
    sock = shirt2 if shirt2 is not None else shirt
    if mode == "down":
        # Лежит на спине поперёк: голова слева, ноги справа, рука откинута.
        c.line(18, 17, 22, 15, SKIN, 2)
        c.line(18, 19, 22, 20, SKIN, 2)
        c.rect(21, 14, 22, 15, K)
        c.rect(21, 20, 22, 21, K)
        c.line(9, 15, 6, 12, sleeve, 2)
        c.rect(7, 16, 14, 20, shirt)
        if shirt2 is not None:
            for xx in (8, 10, 12, 14):
                c.rect(xx, 16, xx, 20, shirt2)
        c.rect(15, 16, 17, 20, shorts)
        _head(c, 4, 18, hair, True, False, 1)
        if keeper:
            c.rect(5, 11, 6, 12, WHITE)
        return c.finish()
    if mode == "slide":
        # Подкат по ходу: нога вытянута вперёд, вторая согнута, тело сзади низко. У вратаря это
        # прыжок за мячом: руки в перчатках вытянуты вперёд, ноги сзади.
        n = math.hypot(dx, dy * 0.7)
        ux, uy = dx / n, dy * 0.7 / n
        cx, cy = 12.0, 16.0
        tx, ty = cx - ux * 5.0, cy - uy * 5.0
        if keeper:
            c.line(tx, ty, tx - ux * 6.0, ty - uy * 6.0 + 1.0, SKIN, 2)
            c.line(tx - uy * 2.0, ty + ux * 2.0, tx - ux * 6.0 - uy * 3.0, ty - uy * 6.0 + ux * 3.0, SKIN, 2)
            c.line(tx, ty, cx + ux * 2.0, cy + uy * 2.0, shirt, 5)
            c.line(tx - ux, ty - uy, tx, ty, shorts, 5)
            hx, hy = cx + ux * 5.0, cy + uy * 5.0 - 1.0
            c.line(cx + ux * 2.0 - uy * 2.0, cy + uy * 2.0 + ux * 2.0, hx + ux * 5.0 - uy * 2.0, hy + uy * 5.0 + ux * 2.0, shirt, 2)
            c.line(cx + ux * 2.0 + uy * 2.0, cy + uy * 2.0 - ux * 2.0, hx + ux * 5.0 + uy * 2.0, hy + uy * 5.0 - ux * 2.0, shirt, 2)
            _head(c, hx, hy, hair, abs(dx) > 0.38, dy < -0.38, sgn)
            c.finish()
            for q in (-2.0, 2.0):
                gx, gy = hx + ux * 5.5 - uy * q, hy + uy * 5.5 + ux * q
                c.rect(gx - 0.5, gy - 0.5, gx + 0.5, gy + 0.5, WHITE)
            return c
        fx, fy = cx + ux * 8.0, cy + uy * 8.0
        c.line(cx, cy, cx + ux * 4.0 - uy * 3.0, cy + uy * 4.0 + ux * 3.0, TAN, 2)
        c.line(cx, cy, fx, fy, SKIN, 2)
        c.line(cx + ux * 4.0, cy + uy * 4.0, fx, fy, sock, 2)
        c.rect(fx - 0.5, fy - 0.5, fx + 1.0, fy + 1.0, K)
        c.line(tx, ty, cx, cy, shirt, 5)
        c.line(cx - ux, cy - uy, cx + ux, cy + uy, shorts, 5)
        c.line(tx, ty, tx - uy * 4.0 - ux * 2.0, ty + ux * 4.0 - uy * 2.0 - 1.0, sleeve, 2)
        _head(c, tx - ux * 3.0, ty - uy * 3.0 - 2.0, hair, abs(dx) > 0.38, dy < -0.38, sgn)
        return c.finish()
    side = abs(dx) > 0.38
    back = dy < -0.38
    s = (0, 1, 0, -1, 0)[frame]
    bob = 1 if frame in (2, 4) else 0
    hip = 18 - bob
    eyes = []
    if side:
        # Профиль: дальние рука и нога темнее и рисуются первыми; шаг вперёд и назад по ходу.
        far, near = (TAN, SKIN)
        for limb, k in ((far, -s), (near, s)):
            hand = (11.5 - sgn * 4.0 * k, 15.0 - bob - abs(k))
            c.line(11.5, 11.0 - bob, hand[0], hand[1], sleeve if limb == near or keeper else TAN, 2)
            if keeper:
                c.rect(hand[0] - 0.5, hand[1], hand[0] + 0.5, hand[1] + 1.0, WHITE)
            if limb == far:
                continue
        for limb, k in ((far, -s), (near, s)):
            if frame in (2, 4) and (limb == near) == (frame == 2):
                foot = (11.5 + sgn * 1.0, 19.0)
                knee = (11.5 + sgn * 2.5, 18.0)
            else:
                foot = (11.5 + sgn * 4.0 * k, 21.0 - (2.0 if k < 0 else 0.0))
                knee = ((11.5 + foot[0]) / 2.0 + sgn * 1.0, (hip + foot[1]) / 2.0)
            c.line(11.5, hip, knee[0], knee[1], limb, 2)
            c.line(knee[0], knee[1], foot[0], foot[1], sock, 2)
            c.rect(min(foot[0], foot[0] + sgn * 2.0) - 0.5, foot[1], max(foot[0], foot[0] + sgn * 2.0), foot[1] + 1.0, K)
        c.rect(9, 10 - bob, 14, 15 - bob, shirt)
        if shirt2 is not None:
            for yy in (11, 13, 15):
                c.rect(9, yy - bob, 14, yy - bob, shirt2)
        c.rect(9, 16 - bob, 14, 17 - bob, shorts)
        # Ближняя рука поверх футболки.
        hand = (11.5 - sgn * 4.0 * s, 15.0 - bob - abs(s))
        c.line(11.5, 11.0 - bob, hand[0], hand[1], sleeve, 2)
        if keeper:
            c.rect(hand[0] - 0.5, hand[1], hand[0] + 0.5, hand[1] + 1.0, WHITE)
        _head(c, 11.5 + sgn * 0.5, 6 - bob, hair, True, back, sgn)
        if not back:
            eyes.append((12 + sgn * 2, 6 - bob))
    else:
        # Анфас и со спины: ноги по очереди поднимаются, руки машут в противофазе.
        for x, k in ((10.0, s), (14.0, -s)):
            lift = 3.0 if k > 0 else 0.0
            foot_y = 21.0 - lift
            c.rect(x - 0.5, hip, x + 0.5, foot_y - 2.0, SKIN)
            c.rect(x - 0.5, foot_y - 2.0, x + 0.5, foot_y, sock)
            c.rect(x - 0.5, foot_y, x + 0.5, foot_y + 1.0, K)
        c.rect(8, 10 - bob, 15, 15 - bob, shirt)
        if shirt2 is not None:
            for yy in (11, 13, 15):
                c.rect(8, yy - bob, 15, yy - bob, shirt2)
        c.rect(8, 16 - bob, 15, 17 - bob, shorts)
        for x, k, out in ((6.5, -s, -1), (16.5, s, 1)):
            up = 2.0 if k > 0 else 0.0
            hand = (x + out * (1.0 if k > 0 else 0.0), 15.0 - bob - up)
            c.line(x, 11.0 - bob, hand[0], hand[1], sleeve, 2)
            if keeper:
                c.rect(hand[0] - 0.5, hand[1], hand[0] + 0.5, hand[1] + 1.0, WHITE)
        _head(c, 11.5, 6 - bob, hair, False, back, sgn)
        if not back:
            eyes = [(10, 6 - bob), (13, 6 - bob)]
    c.finish()
    for e in eyes:
        c.set(e[0], e[1], K)
    return c


def kit_strip(shirt, shorts, hair=BARK, shirt2=None, keeper=False):
    frames = []
    for d in range(8):
        for fr in range(RUN):
            frames.append(player(d, fr, shirt, shorts, hair, shirt2=shirt2, keeper=keeper))
    for d in range(8):
        frames.append(player(d, 0, shirt, shorts, hair, "slide", shirt2, keeper))
    for d in range(8):
        frames.append(player(d, 0, shirt, shorts, hair, "down", shirt2, keeper))
    return strip(frames)


# Мяч 8×8 попиксельно (плейтест 2026-11-12: размер прежний, но чтобы читался как футбольный):
# чёрный пятиугольник в центре, пятна по краю, тень снизу справа, блик; во втором кадре пятна
# сдвинуты, при качении мяч крутится. o обводка, W белый, g тень, k пятно.
BALL_MAPS = (
    ("..oooo..",
     ".oWWkWo.",
     "oWWkkWWo",
     "okWkkWgo",
     "oWWWWWko",
     "oWkWWgWo",
     ".oWggWo.",
     "..oooo.."),
    ("..oooo..",
     ".okWWWo.",
     "oWWWkkWo",
     "oWWkkkgo",
     "okWWkWgo",
     "oWWWWWko",
     ".ogWkgo.",
     "..oooo.."),
)


def ball(i):
    c = Canvas(8, 8)
    ink = {"o": K, "W": WHITE, "g": GREY, "k": K}
    for y, row in enumerate(BALL_MAPS[i % 2]):
        for x, ch in enumerate(row):
            if ch in ink:
                c.set(x, y, ink[ch])
    c.set(2, 1, WHITE)
    return c


def grass():
    """Трава 64×64: полоса светлая и тёмная по 32, мелкие травинки."""
    c = Canvas(64, 64)
    for x in range(64):
        for y in range(64):
            band = LEAF if x < 32 else PINE
            if (x * 7 + y * 13) % 17 == 0:
                band = PINE if band == LEAF else LEAF
            c.set(x, y, band)
    return c


def sprites():
    # Пираты (плейтест 2026-11-12): герой в тельняшке, синих штанах и красной бандане, соперники
    # в красных камзолах, чёрном и золотом, у вратарей свои цвета.
    return {
        "soccer_hero": kit_strip(WHITE, NAVY, RED, SEA),
        "soccer_rival_0": kit_strip(RED, BARK, K),
        "soccer_rival_1": kit_strip(GOLD, NAVY, BARK),
        "soccer_rival_2": kit_strip(K, GREY, RED),
        "soccer_keeper_hero": kit_strip(LEAF, K, BARK, PINE, keeper=True),
        "soccer_keeper_rival": kit_strip(GREY, K, K, AQUA, keeper=True),
        "soccer_ball": strip([ball(i) for i in range(2)]),
        "soccer_grass": grass(),
    }


# --- Поле и аут по сеттингу (плейтест 2026-11-12) ---------------------------------------------
# Вид издалека, поэтому сеттинг держится на поле и том, что вокруг: у пиратов песок и море, у
# замков трава и брусчатка двора, у космоса реголит и звёзды. Тайлы 64×64 бесшовные, в своих
# палитрах; разметка, ворота и игроки общие.

import random  # noqa: E402

T = 64


def _pal(*hexes):
    return [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in hexes]


def _wrap(c, x, y, v):
    c.px[y % T][x % T] = v


def _noise_tile(base, spots, seed, density=0.08):
    c = Canvas(T, T)
    rng = random.Random(seed)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = base
    for _ in range(int(T * T * density)):
        c.px[rng.randrange(T)][rng.randrange(T)] = rng.choice(spots)
    return c


def sand():
    """Песок: тёплый, граблёные полосы светлее и темнее по 32 (как полосы газона), рябь от ветра,
    ракушки и камешки. Палитра: 0 тень, 1 тёмный, 2 песок, 3 светлый, 4 блик, 5 ракушка, 6 камень."""
    pal = _pal(0x8A6A3E, 0xC9A267, 0xE2C084, 0xF0D6A0, 0xFFF0CC, 0xF4D8D0, 0x9A8A78)
    c = _noise_tile(2, [1, 3], 11, 0.10)
    for y in range(T):
        for x in range(T):
            if x >= 32 and c.px[y][x] == 2:
                c.px[y][x] = 3 if (x + y) % 3 else 2
    # Рябь от ветра: короткие волнистые штрихи вразброс, тёмный низ и светлый гребень.
    rng = random.Random(5)
    for _ in range(26):
        x0, y0, ln = rng.randrange(T), rng.randrange(T), rng.randint(4, 10)
        ph = rng.random() * 6.0
        for k in range(ln):
            y = y0 + int(round(0.8 * math.sin(k * 0.7 + ph)))
            _wrap(c, x0 + k, y, 1)
            if 0 < k < ln - 1:
                _wrap(c, x0 + k, y - 1, 4 if (x0 + k) % T >= 32 else 3)
    for _ in range(3):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 5)
        _wrap(c, x + 1, y, 5)
        _wrap(c, x, y + 1, 0)
        _wrap(c, x + 1, y + 1, 1)
    for _ in range(4):
        x, y = rng.randrange(T), rng.randrange(T)
        _wrap(c, x, y, 6)
        _wrap(c, x + 1, y + 1, 0)
    return c, pal


def sea(frame):
    """Море в ауте: глубокая синева, барашки бегут по кадрам. 0 глубина, 1 вода, 2 светлая, 3 гребень,
    4 пена."""
    pal = _pal(0x15306A, 0x2156A0, 0x3A7CC4, 0x7FC0EC, 0xEAF6FF)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            # Пятна глубины плавными волнами, без косой штриховки.
            v = math.sin(x / 64.0 * 2 * math.pi) + math.sin(y / 64.0 * 4 * math.pi + x / 64.0 * 2 * math.pi)
            c.px[y][x] = 0 if v < -1.2 or (v < -0.8 and (x + y) % 2 == 0) else 1
    for row in range(6, T, 16):
        for x in range(T):
            ph = x / 64.0 * 2 * math.pi + frame * math.pi / 2 + row
            y = row + int(round(2.0 * math.sin(ph)))
            _wrap(c, x, y, 2)
            if math.sin(ph) > 0.6:
                _wrap(c, x, y - 1, 3)
            if math.sin(ph) > 0.9:
                _wrap(c, x, y - 2, 4)
    return c, pal


def grass_field():
    """Трава замкового двора: полосы стрижки по 32, травинки."""
    pal = _pal(0x1E4A24, 0x2E6E32, 0x3E8C3E, 0x5AA84C, 0x86C870)
    c = _noise_tile(2, [1, 3], 21, 0.12)
    for y in range(T):
        for x in range(T):
            if x >= 32 and c.px[y][x] == 2:
                c.px[y][x] = 3
            if (x * 7 + y * 13) % 29 == 0:
                c.px[y][x] = 4 if x >= 32 else 1
    return c, pal


def cobbles():
    """Брусчатка двора вокруг поля: камни с фаской, тёмные швы."""
    pal = _pal(0x1E1C24, 0x3C3A44, 0x5A5662, 0x7C7682, 0x9C96A0)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 0
    rng = random.Random(3)
    for row in range(0, T, 8):
        off = 0 if (row // 8) % 2 == 0 else 6
        for x0 in range(-off, T, 12):
            t = rng.choice((2, 2, 3))
            for y in range(row + 1, row + 7):
                for x in range(x0 + 1, x0 + 11):
                    v = t
                    if y == row + 1 or x == x0 + 1:
                        v = min(t + 1, 4)
                    if y == row + 6 or x == x0 + 10:
                        v = 1
                    _wrap(c, x, y, v)
    return c, pal


def regolith():
    """Реголит: серый грунт с кратерами (тень сверху слева, вал снизу справа)."""
    pal = _pal(0x2C2C34, 0x4E4E58, 0x6E6E78, 0x8E8E98, 0xB4B4BC)
    c = _noise_tile(2, [1, 3], 31, 0.12)
    for y in range(T):
        for x in range(T):
            if x >= 32 and c.px[y][x] == 2:
                c.px[y][x] = 3 if (x + y) % 4 else 2
    rng = random.Random(9)
    for _ in range(5):
        cx, cy, rr = rng.randrange(T), rng.randrange(T), rng.uniform(2.5, 5.5)
        for y in range(int(cy - rr - 2), int(cy + rr + 3)):
            for x in range(int(cx - rr - 2), int(cx + rr + 3)):
                d = math.hypot(x - cx, y - cy)
                if d <= rr:
                    _wrap(c, x, y, 1 if (x - cx) + (y - cy) < 0 else 2)
                elif d <= rr + 1.2:
                    _wrap(c, x, y, 4 if (x - cx) + (y - cy) > 0 else 0)
    return c, pal


def stars(frame):
    """Космос вокруг поля: тёмно-синяя пустота, звёзды мерцают по кадрам."""
    pal = _pal(0x06060E, 0x0E1028, 0x3A4070, 0x9AA8E0, 0xFFFFFF)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.px[y][x] = 1 if ((x + y * 3) // 11) % 3 else 0
    rng = random.Random(17)
    for k in range(24):
        x, y = rng.randrange(T), rng.randrange(T)
        tw = (k + frame) % 4
        c.px[y][x] = 4 if tw == 0 else 3 if tw < 3 else 2
        if k % 6 == 0 and tw == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                _wrap(c, x + dx, y + dy, 2)
    return c, pal


def fields():
    """Тайлы поля и аута по сеттингу → (холст, палитра). Аут лентой из 4 кадров."""
    out = {}
    for setting, field, around in (("pirates", sand, sea), ("castles", grass_field, lambda f: cobbles()),
                                   ("space", regolith, stars)):
        cv, pal = field()
        out["soccer_field_" + setting] = (cv, pal)
        frames = [around(f) for f in range(4)]
        out["soccer_out_" + setting] = (strip([fr[0] for fr in frames]), frames[0][1])
    return out
