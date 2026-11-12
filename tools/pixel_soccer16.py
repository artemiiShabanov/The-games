"""Рисунок футбола × 16/32-bit «один на одного» (#101) для pixel_sprites16.py, графика по
Sensible Soccer (решение 2026-11-12): вид сверху, крошечные стоящие игроки 16×16 в восьми
направлениях
(три кадра бега, подкат, лежит), формы четырёх цветов и двух вратарей, мяч, трава полосами.
Всё в палитре спрайтов сеттинга.
"""
import math

from pixel_sprites16 import (Canvas, strip, K, NAVY, SEA, AQUA, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD, BARK,
                             RED, LEAF, PINE)

F = 16
# Направления по кругу: 0 вправо, дальше по часовой (y вниз), как угол atan2.
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]


def player(d, frame, shirt, shorts, hair=BARK, mode="run", shirt2=None):
    """Игрок маленькой стоящей фигуркой под крутым углом, как в Sensible Soccer: ноги, трусы,
    футболка, голова. Взгляд вниз: лицо; вверх: затылок; вбок: профиль, руки и ноги шагают."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    if mode == "down":
        # Лежит на траве поперёк.
        c.rect(3, 10, 12, 12, shirt)
        c.rect(10, 10, 12, 12, shorts)
        c.ellipse(3, 11, 2, 1.5, SKIN)
        c.rect(1, 10, 3, 10, hair)
        return c.finish()
    if mode == "slide":
        # Подкат: тело низко, нога вытянута по ходу.
        sgn = 1 if dx >= 0 else -1
        c.rect(5, 10, 10, 12, shirt)
        c.line(8, 12, 8 + sgn * 6, 13, shorts, 2)
        c.ellipse(8 - sgn * 4, 10, 2, 2, SKIN)
        c.rect(8 - sgn * 5, 8, 8 - sgn * 3, 8, hair)
        return c.finish()
    side = abs(dx) > 0.38
    back = dy < -0.38
    sgn = 1 if dx >= 0 else -1
    step = (0, 1, -1)[frame]
    # Ноги.
    if side:
        c.rect(7 + step * sgn, 12, 7 + step * sgn, 14, SKIN)
        c.rect(8 - step * sgn, 12, 8 - step * sgn, 14, SKIN)
        c.set(7 + step * sgn + sgn, 15, K)
        c.set(8 - step * sgn + sgn, 15, K)
    else:
        c.rect(6, 12, 6, 14 - (1 if step > 0 else 0), SKIN)
        c.rect(9, 12, 9, 14 - (1 if step < 0 else 0), SKIN)
        c.set(6, 15 - (1 if step > 0 else 0), K)
        c.set(9, 15 - (1 if step < 0 else 0), K)
    # Трусы, футболка (тельняшка полосами через строку), руки.
    c.rect(5 if not side else 6, 10, 10 if not side else 9, 11, shorts)
    c.rect(5 if not side else 6, 6, 10 if not side else 9, 9, shirt)
    if shirt2 is not None:
        for yy in (7, 9):
            c.rect(5 if not side else 6, yy, 10 if not side else 9, yy, shirt2)
    if side:
        c.set(7 - step * sgn, 9, SKIN)
    else:
        c.rect(4, 7 + (1 if step > 0 else 0), 4, 8 + (1 if step > 0 else 0), SKIN)
        c.rect(11, 7 + (1 if step < 0 else 0), 11, 8 + (1 if step < 0 else 0), SKIN)
    # Голова.
    c.rect(6, 2, 9, 5, SKIN)
    if back:
        c.rect(6, 2, 9, 5, hair)
    elif side:
        c.rect(6, 2, 9, 3, hair)
        c.rect(6 if sgn > 0 else 9, 2, 6 if sgn > 0 else 9, 5, hair)
        c.set(8 + (1 if sgn > 0 else -2), 4, K)
    else:
        c.rect(6, 2, 9, 2, hair)
        c.set(7, 4, K)
        c.set(8, 4, K)
    return c.finish()


def kit_strip(shirt, shorts, hair=BARK, shirt2=None):
    frames = []
    for d in range(8):
        for fr in range(3):
            frames.append(player(d, fr, shirt, shorts, hair, shirt2=shirt2))
    for d in range(8):
        frames.append(player(d, 0, shirt, shorts, hair, "slide", shirt2))
    for d in range(8):
        frames.append(player(d, 0, shirt, shorts, hair, "down", shirt2))
    return strip(frames)


def ball(i):
    c = Canvas(8, 8)
    c.ellipse(3.5, 3.5, 3, 3, WHITE)
    for k, (x, y) in enumerate(((2, 2), (5, 3), (3, 5))):
        if (k + i) % 2 == 0:
            c.set(x, y, K)
    return c.finish()


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
        "soccer_keeper_hero": kit_strip(PINE, K),
        "soccer_keeper_rival": kit_strip(GREY, K, K),
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
