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


# --- Игроки 24×24 (плейтест 2026-11-12: крупнее, видно удар, бег реалистичнее) -----------------
# Кукла в объёме: точки суставов на поле (x вправо, y вниз по полю) и высота z, поворот по
# направлению взгляда, проекция сверху под углом (y сжат вдвое, z вверх). Части рисуются от
# дальних к ближним; бег в шесть фаз (нога выносится вперёд с подъёмом стопы, руки навстречу,
# корпус качается), замах ногой назад, удар ногой вперёд, подкат, лежит. Светотень и своя
# палитра у всех лент даёт `reshade` в pixel_sprites16.py.

P = 24


def _proj(v):
    return (P / 2 + v[0], P - 3 - (v[1] * 0.5 + v[2]))


def _pt(base, f, s, along, side, z):
    return (base[0] + f[0] * along + s[0] * side, base[1] + f[1] * along + s[1] * side, z)


def puppet(d, shirt, shorts, hair, shirt2=None, pose="idle", phase=0.0):
    c = Canvas(P, P)
    a = d * math.pi / 4.0
    f = (math.cos(a), math.sin(a))
    s_ = (-math.sin(a), math.cos(a))
    o = (0.0, 0.0)
    bob = 0.0
    lean = 0.0
    legs = {}
    arms = {}
    if pose in ("idle", "run"):
        sw = math.sin(phase) if pose == "run" else 0.0
        bob = abs(math.cos(phase)) * 0.8 if pose == "run" else 0.0
        lean = 0.8 if pose == "run" else 0.0
        for side, sg in (("l", -1), ("r", 1)):
            k = sw * sg
            lift = max(0.0, math.cos(phase) * sg) * 2.2 if pose == "run" else 0.0
            legs[side] = (k * 5.0, sg * 1.8, lift * 1.3)
            arms[side] = (-k * 4.0, sg * 4.0, 9.5 + bob)
    elif pose == "windup":
        lean = -0.6
        legs["l"] = (1.5, -2.0, 0.0)
        legs["r"] = (-6.0, 1.8, 4.0)
        arms["l"] = (3.5, -5.0, 11.5)
        arms["r"] = (-2.5, 5.0, 12.0)
    elif pose == "kick":
        lean = 1.4
        legs["l"] = (-1.5, -2.0, 0.0)
        legs["r"] = (8.5, 1.2, 4.5)
        arms["l"] = (-3.5, -5.4, 12.0)
        arms["r"] = (2.5, 5.6, 11.5)
    hip = (o[0] + f[0] * lean * 0.3, o[1] + f[1] * lean * 0.3, 8.0 + bob)
    neck = _pt(hip, f, s_, lean * 1.3, 0.0, 14.5 + bob)
    head = _pt(neck, f, s_, lean * 0.4, 0.0, 18.0 + bob)
    parts = []
    if pose in ("idle", "run", "windup", "kick"):
        for side, sg in (("l", -1), ("r", 1)):
            fa, fs, fz = legs[side]
            hp = _pt(hip, f, s_, 0.0, sg * 1.8, hip[2])
            foot = _pt(o, f, s_, fa, fs, fz)
            knee = ((hp[0] + foot[0]) / 2 + f[0] * 0.8, (hp[1] + foot[1]) / 2 + f[1] * 0.8, (hp[2] + foot[2]) / 2 + 0.6)
            parts.append(("leg", foot[1], (hp, knee, foot)))
            sh = _pt(neck, f, s_, 0.0, sg * 3.0, neck[2] - 1.0)
            aa, asd, az = arms[side]
            hand = _pt(hip, f, s_, aa, asd, az)
            parts.append(("arm", sh[1] + 0.1, (sh, hand)))
        parts.append(("torso", hip[1] + 0.05, (hip, neck)))
        parts.append(("head", head[1] + 0.2, (head,)))
    # Дальние раньше: меньше y на поле и для торса после ног одной глубины.
    order = {"leg": 0, "torso": 1, "arm": 2, "head": 3}
    parts.sort(key=lambda q: (round(q[1], 1), order[q[0]]))
    for kind, _, pts in parts:
        if kind == "leg":
            hp, knee, foot = (_proj(q) for q in pts)
            c.line(hp[0], hp[1], knee[0], knee[1], shorts, 3)
            c.line(knee[0], knee[1], foot[0], foot[1] - 1, SKIN, 2)
            mid = ((knee[0] + foot[0]) / 2, (knee[1] + foot[1]) / 2)
            c.line(mid[0], mid[1], foot[0], foot[1] - 1, shirt, 2)
            c.rect(foot[0] - 1, foot[1] - 1, foot[0] + 1 + (1 if f[0] > 0.3 else 0), foot[1], K)
        elif kind == "arm":
            sh, hand = (_proj(q) for q in pts)
            c.line(sh[0], sh[1], hand[0], hand[1], SKIN, 2)
            c.line(sh[0], sh[1], (sh[0] * 2 + hand[0]) / 3, (sh[1] * 2 + hand[1]) / 3, shirt, 3)
        elif kind == "torso":
            hp, nk = (_proj(q) for q in pts)
            c.line(hp[0], hp[1] + 1, hp[0], hp[1], shorts, 6)
            for k in range(7):
                t = k / 6.0
                x = hp[0] + (nk[0] - hp[0]) * t
                y = hp[1] + (nk[1] - hp[1]) * t
                c.ellipse(x, y, 3.4 + t * 0.4, 1.6, shirt)
            if shirt2 is not None:
                for y in range(int(nk[1]), int(hp[1]) + 1):
                    if (y - int(nk[1])) % 2 == 1:
                        for x in range(int(hp[0]) - 5, int(hp[0]) + 6):
                            if c.get(x, y) == shirt:
                                c.set(x, y, shirt2)
        else:
            (hd,) = (_proj(q) for q in pts)
            c.ellipse(hd[0], hd[1], 3.0, 3.0, SKIN)
            # Волосы или бандана: сверху и с затылка (против взгляда).
            for y in range(int(hd[1]) - 4, int(hd[1]) + 4):
                for x in range(int(hd[0]) - 4, int(hd[0]) + 5):
                    if c.get(x, y) != SKIN:
                        continue
                    back = (x - hd[0]) * f[0] + (y - hd[1]) * f[1] * 2.0
                    if y < hd[1] - 0.5 or back < -0.8:
                        c.set(x, y, hair)
            if f[1] > -0.3:
                ex = hd[0] + f[0] * 1.6
                c.set(ex - 0.8 * abs(f[1]), hd[1] + 0.5, K)
                if abs(f[0]) < 0.8:
                    c.set(ex + 1.0, hd[1] + 0.5, K)
    c.outline()
    return c


def puppet_lying(d, shirt, shorts, hair, shirt2=None, slide=False):
    """Подкат (нога вперёд по ходу, корпус откинут) или лежит поперёк."""
    c = Canvas(P, P)
    a = d * math.pi / 4.0
    f = (math.cos(a), math.sin(a))
    if slide:
        sx, sy = f[0], f[1] * 0.5
        hip = (P / 2, P - 7)
        c.line(hip[0] - sx * 5, hip[1] - sy * 5 - 3, hip[0], hip[1] - 2, shirt, 4)
        c.line(hip[0], hip[1], hip[0] + sx * 7, hip[1] + sy * 7, SKIN, 2)
        c.line(hip[0], hip[1], hip[0] + sx * 3, hip[1] + sy * 3, shorts, 3)
        c.rect(hip[0] + sx * 7 - 1, hip[1] + sy * 7 - 1, hip[0] + sx * 7 + 1, hip[1] + sy * 7, K)
        c.line(hip[0] - 1, hip[1] - 1, hip[0] - sx * 3 + 2, hip[1] + 2, SKIN, 2)
        hx, hy = hip[0] - sx * 7, hip[1] - sy * 7 - 4
        c.ellipse(hx, hy, 2.4, 2.4, SKIN)
        c.rect(hx - 2, hy - 2, hx + 2, hy - 1, hair)
    else:
        y = P - 6
        c.rect(5, y - 2, 13, y + 1, shirt)
        if shirt2 is not None:
            for x in range(5, 14, 2):
                c.rect(x, y - 2, x, y + 1, shirt2)
        c.rect(13, y - 2, 15, y + 1, shorts)
        c.line(15, y - 1, 21, y - 2, SKIN, 2)
        c.line(15, y + 1, 21, y + 2, SKIN, 2)
        c.ellipse(3, y, 2.4, 2.4, SKIN)
        c.rect(1, y - 2, 2, y + 2, hair)
        c.line(7, y - 3, 9, y - 6, SKIN, 2)
    c.outline()
    return c


def kit_strip(shirt, shorts, hair=BARK, shirt2=None):
    """Лента игрока: на каждое из 8 направлений 9 кадров (стоит, бег 6 фаз, замах, удар), потом
    8 подкатов и 8 лежит."""
    frames = []
    for d in range(8):
        frames.append(puppet(d, shirt, shorts, hair, shirt2, "idle"))
        for k in range(6):
            frames.append(puppet(d, shirt, shorts, hair, shirt2, "run", k * math.pi / 3.0))
        frames.append(puppet(d, shirt, shorts, hair, shirt2, "windup"))
        frames.append(puppet(d, shirt, shorts, hair, shirt2, "kick"))
    for d in range(8):
        frames.append(puppet_lying(d, shirt, shorts, hair, shirt2, True))
    for d in range(8):
        frames.append(puppet_lying(d, shirt, shorts, hair, shirt2, False))
    return strip(frames)


def _pentagon(cx, cy, rad, rot):
    return [(cx + math.cos(rot + k * 2 * math.pi / 5) * rad, cy + math.sin(rot + k * 2 * math.pi / 5) * rad) for k in range(5)]


def ball12(i):
    """Мяч 12×12: белый шар, тень полумесяцем снизу справа, блик; чёрный пятиугольник и пять
    половинок по краю, при качении сдвигаются по кадрам."""
    c = Canvas(12, 12)
    inside = set()
    for y in range(12):
        for x in range(12):
            dx, dy = x - 5.5, y - 5.5
            if dx * dx + dy * dy <= 5.4 * 5.4:
                inside.add((x, y))
                c.set(x, y, GREY if (dx + 0.8) ** 2 + (dy + 0.8) ** 2 > 5.4 * 5.4 else WHITE)
    rot = i * (2 * math.pi / 5) / 4
    shift = (i - 1.5) * 0.6
    patches = [_pentagon(5.5 + shift, 5.5, 1.7, rot - math.pi / 2)]
    for k in range(5):
        a = rot + k * 2 * math.pi / 5 - math.pi / 2
        patches.append(_pentagon(5.5 + shift + math.cos(a) * 4.9, 5.5 + math.sin(a) * 4.9, 1.2, a + math.pi))
    for pts in patches:
        ys = [q[1] for q in pts]
        for y in range(int(min(ys)), int(max(ys)) + 2):
            xs = []
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                if (a_[1] <= y + 0.5 < b_[1]) or (b_[1] <= y + 0.5 < a_[1]):
                    xs.append(a_[0] + (y + 0.5 - a_[1]) * (b_[0] - a_[0]) / (b_[1] - a_[1]))
            xs.sort()
            for m in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[m])), int(round(xs[m + 1])) + 1):
                    if (x, y) in inside:
                        c.set(x, y, K)
    c.set(3, 2, WHITE)
    c.set(2, 3, WHITE)
    c.outline()
    return c


def grass():
    """Трава 64×64 (запасная, если у сеттинга нет поля): полосы по 32, травинки."""
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
        "soccer_ball": strip([ball12(i) for i in range(4)]),
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
