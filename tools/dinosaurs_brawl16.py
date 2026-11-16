# -*- coding: utf-8 -*-
"""Набор «Динозавры» для битемапа × 16/32-bit (#144): зеркало `space_brawl16.py` и
`pixel_brawl16.py`. Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты
оттуда как есть (демка `fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и
улица свои.

Бойцы: герой это пещерный человек: оранжевая пятнистая шкура через переднее плечо с рваным
подолом на бёдрах, лохматая копна с вихрами, кость в волосах, босые ступни; громила это дикарь с
дубиной: голый торс в белой раскраске, грива и борода, пучок волос на темени, кость в носу,
меховая юбка, в руке дубина с шипами; враг с ножом это прямоходящий раптор: зелёная чешуя с
полосами, жёлтое брюхо, длинная зубастая морда, хвост, серп когтя на лапе; босс это вождь-шаман:
на голове череп тираннозавра с зубами над лицом и перьями на затылке, нагрудник из рёбер, седая
борода, тёмная шкура-плащ с бахромой из перьев. Улица это стойбище под скалой: пещера с
росписью и факелом, хижина из шкур и бивней с сушилкой, прогал в джунглях с вулканом и шеей
зауропода, рёбра и череп ящера с тотемом, глиняный уступ с гнездом и шатром, расщелина с
лавопадом; у стены тропа с плоскими камнями, уступ из лавового камня, растрескавшаяся красная
глина со следами лап.

    python3 tools/dinosaurs_brawl16.py --preview out.png   # лист всех лент
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_brawl16 as pb  # noqa: E402
from pixel_brawl16 import (Pal, Body, capsule, ellipse, poly, put, recolor, add, lerp, skeleton, FW, FH, BW, BH,  # noqa: E402
                           FOOT, SW, SH, WALL_Y, CURB_Y, ROAD_Y)
from pixel_sprites16 import Canvas, strip  # noqa: E402

# Обводка та же, что K в `dinosaurs16.PALETTE`; рампы ниже растянуты из её же цветов.
OUTLINE = 0x181010

BONE = [0x7C686E, 0xBCB09A, 0xF4EEDA, 0xFFFFFF]
HIDE = [0x7A2410, 0xB8401C, 0xEC5E24, 0xFFA058]
DARK = [0x1E100E, 0x34201A, 0x523028, 0x7A4E3C]
WOOD = [0x2A1810, 0x50301C, 0x80542C, 0xB07E44]
FUR = [0x2A1C18, 0x4A342A, 0x74584A, 0xA08670]
SCALE = [0x123A22, 0x266C3A, 0x60B440, 0xA8E070]
GOLD = [0x7A5014, 0xBC822C, 0xF4CC52, 0xFFF0A0]
TEAL = [0x123040, 0x1C465A, 0x2C8084, 0x7CCCB4]


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x6E3220, 0xB05434, 0xDC9862, 0xF6C492])
    p.add("hide", HIDE)
    p.add("hair", DARK)
    p.add("bone", BONE)
    p.add("cord", WOOD)
    return Look("cave", p, Body(1.0, 1.12))


def thug_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x4E2418, 0x8A4428, 0xBC6C40, 0xE09868])
    p.add("fur", FUR)
    p.add("hair", [0x120C0C, 0x241818, 0x3C2A26, 0x5C4238])
    p.add("bone", BONE)
    p.add("wood", WOOD)
    p.add("hide", HIDE)
    return Look("savage", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("scale", SCALE)
    p.add("belly", GOLD)
    p.add("bone", BONE)
    p.add("mouth", [0x4A0E10, 0x8A1C1C, 0xD03A2C, 0xFF8466])
    p.add("crest", HIDE)
    p.add("eye", [0x100808, 0x7A5014, 0xF4CC52, 0xFFF8C0])
    return Look("raptor", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x5C2A1C, 0x9C4C2E, 0xCC8052, 0xECB082])
    p.add("cloak", [0x24100E, 0x48201A, 0x703426, 0x9C5438])
    p.add("fur", FUR)
    p.add("bone", BONE)
    p.add("feather", TEAL)
    p.add("gold", GOLD)
    p.add("red", HIDE)
    p.add("hair", [0x4A4650, 0x8A8690, 0xC8C4C8, 0xF0ECEC])
    return Look("shaman", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _dot(c, q, col):
    c.set(int(round(q[0])), int(round(q[1])), col)


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    n = (d[1], -d[0])
    ramp = "scale" if kind == "raptor" else "skin"
    thin = 0.86 if kind == "raptor" else 1.0
    upper = capsule(sh, el, 4.3 * s * b * thin, 3.5 * s * b * thin) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b * thin,
                                                                             4.5 * s * b * thin)
    if kind == "savage":
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.4 * s * b, 3.6 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
    put(c, pal, upper, pal[ramp], far=far, soft=True)
    fore = capsule(el, ha, 3.6 * s * b * thin, 3.0 * s * b * thin)
    put(c, pal, fore, pal[ramp], far=far)
    if kind == "cave":
        # Кожаный ремешок на запястье, у ближней руки ещё и на плече, с костяной бусиной.
        put(c, pal, capsule(add(ha, d, -4.4 * s), add(ha, d, -2.8 * s), 3.5 * s * b, 3.4 * s * b), pal["cord"], far=far,
            cast=False)
        if not far:
            q = lerp(sh, el, 0.62)
            put(c, pal, capsule(add(q, n, -3.4 * s * b), add(q, n, 3.4 * s * b), 1.0, 1.0), pal["cord"], cast=False)
            _dot(c, add(q, n, 1.0), pal["bone"][2])
    elif kind == "savage":
        # Меховой наруч и белая полоса раскраски на плече.
        put(c, pal, capsule(add(ha, d, -8.0 * s), add(ha, d, -3.2 * s), 4.3 * s * b, 4.0 * s * b), pal["fur"], far=far)
        q = lerp(sh, el, 0.5)
        for k in range(-4, 5):
            for w in (0, 1):
                t = add(add(q, n, k * 1.05 * b), _unit(sh, el), w)
                if c.get(int(round(t[0])), int(round(t[1]))) in pal["skin"]:
                    _dot(c, t, pal["bone"][1 if far else 2])
    elif kind == "raptor":
        # Тёмные полосы поперёк лапы.
        for t_ in (0.35, 0.7):
            q = lerp(sh, el, t_)
            for k in range(-3, 1):
                t = add(q, n, k)
                if c.get(int(round(t[0])), int(round(t[1]))) in pal["scale"][2:]:
                    _dot(c, t, pal["scale"][1])
    elif kind == "shaman":
        # Костяные браслеты на запястье и перевязь с перьями на плече.
        for off in (-7.0, -4.0):
            put(c, pal, capsule(add(ha, d, (off - 0.8) * s), add(ha, d, off * s), 3.3 * s * b, 3.3 * s * b), pal["bone"],
                far=far, cast=False)
        q = lerp(sh, el, 0.55)
        put(c, pal, capsule(add(q, n, -4.2 * s * b), add(q, n, 4.2 * s * b), 1.3 * s, 1.3 * s), pal["gold"], far=far,
            cast=False)
        if not far:
            u = _unit(sh, el)
            for k in (-2.5, 0.0, 2.5):
                a0 = add(add(q, n, k * s), u, 1.0)
                put(c, pal, capsule(a0, add(a0, u, 5.5 * s), 1.5 * s, 0.6), pal["feather" if k else "red"], cast=False)
    fist = add(ha, d, 1.2 * s)
    fr = min(b, 1.15) * (1.15 if kind == "savage" else 1.0) * thin
    fs = ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr)
    if kind == "savage" and side == "n" and getattr(look, "club", True):
        # Дубина торчит из кулака вверх от предплечья; при прямой руке ложится вперёд, в удар.
        # В стойке стоит столбом перед грудью, в замахе уходит за голову, при прямой руке
        # (удар) поднята над кулаком: вперёд кадр её срезал бы.
        straight = max(0.0, 1.0 - abs(p["fa_n"]) / 40.0)
        th = math.radians((120.0 if p["ua_n"] < -20.0 else 32.0) + 82.0 * straight)
        cd = (d[0] * math.cos(th) + n[0] * math.sin(th), d[1] * math.cos(th) + n[1] * math.sin(th))
        cn = (cd[1], -cd[0])
        grip0, grip1, tip = add(fist, cd, -4.0), add(fist, cd, 6.0), add(fist, cd, 21.0)
        put(c, pal, capsule(grip0, grip1, 1.7, 1.9), pal["wood"], cast=False)
        club = capsule(grip1, tip, 2.6, 5.4)
        put(c, pal, club, pal["wood"], soft=True)
        # Обмотка рукояти, кольца дерева и костяные шипы на утолщении.
        for k in (-1.5, 0.5, 2.5):
            for w in (-1, 0, 1):
                _dot(c, add(add(fist, cd, k), cn, w), pal["hide"][1])
        for t_ in (10.0, 14.5, 18.5):
            for w in range(-5, 6):
                q = add(add(fist, cd, t_), cn, w)
                if c.get(int(round(q[0])), int(round(q[1]))) in pal["wood"][2:]:
                    _dot(c, q, pal["wood"][1])
        for t_, sgn in ((13.0, 1), (17.5, -1), (19.5, 1)):
            q = add(add(fist, cd, t_), cn, sgn * 5.0)
            put(c, pal, poly([add(q, cd, -1.6), add(q, cn, sgn * 3.6), add(q, cd, 1.6)]) | ellipse(q[0], q[1], 1.2, 1.2),
                pal["bone"], cast=False)
    put(c, pal, fs, pal[ramp], far=far)
    if kind == "raptor":
        # Когти: два коротких на пальцах, у ближней лапы длинный серп вперёд и вниз.
        cl = pal["bone"]
        for k in (-1.6, 1.4):
            q = add(add(fist, d, 3.0), n, k)
            _dot(c, q, cl[1 if far else 2])
            _dot(c, add(q, d, 1.0), cl[1 if far else 3])
        if side == "n":
            a0 = add(add(fist, d, 1.5), n, 2.0)
            a1 = add(add(fist, d, 7.0), n, 2.6)
            a2 = add(add(fist, d, 11.5), n, -0.6)
            put(c, pal, capsule(a0, a1, 2.0, 1.5) | capsule(a1, a2, 1.5, 0.6), cl, cast=False)


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    skin = "scale" if kind == "raptor" else "skin"
    fat = 1.14 if kind == "raptor" else 1.0
    thigh = capsule(hp, kn, 6.0 * s * b * fat, 4.8 * s * b * fat)
    put(c, pal, thigh, pal[skin], far=far, soft=True)
    td = _unit(hp, kn)
    tn = (td[1], -td[0])
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    flen = 9.5 if kind == "raptor" else 8.0
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, flen * s), 3.4 * s, 2.7 * s)
    ankle = capsule(add(an, sd, -3.0 * s), an, 4.0 * s * b, 3.8 * s * b)
    shin = capsule(kn, add(an, sd, -2.0 * s), 4.5 * s * b, 3.7 * s * b)
    put(c, pal, ankle | foot, pal[skin], far=far)
    put(c, pal, shin, pal[skin], far=far)
    if kind in ("cave", "savage", "shaman"):
        # Шкура на бёдрах: накрывает верх бедра и кончается рваными зубцами.
        cover = {"cave": 0.5, "savage": 0.62, "shaman": 0.72}[kind]
        e = lerp(hp, kn, cover)
        S = capsule(hp, e, 6.5 * s * b, 5.7 * s * b)
        for k in (-4.6, -1.6, 1.6, 4.6):
            q = add(add(e, tn, k * b), td, 2.0)
            S |= poly([add(q, tn, -1.6), add(q, td, 3.4), add(q, tn, 1.6)])
        ramp = pal["hide"] if kind == "cave" else pal["fur"]
        put(c, pal, S, ramp, far=far, soft=True)
        if kind == "cave":
            # Тёмные пятна шкуры.
            for (t_, k, r) in ((0.16, 2.2, 1.9), (0.34, -2.4, 1.6)):
                q = add(lerp(hp, kn, t_), tn, k * b)
                put(c, pal, ellipse(q[0], q[1], r, r * 0.85) & S, pal["hair"][1:] + [pal["hair"][3]], far=far, cast=False)
        else:
            # Пряди меха штрихами, у дикаря ещё меховая обмотка на голени.
            for (x, y) in S:
                if (x * 3 + y) % 7 == 0 and c.get(x, y) == ramp[1 if far else 2]:
                    c.set(x, y, ramp[0 if far else 1])
        if kind == "savage":
            wrap = capsule(add(an, sd, -8.5 * s), add(an, sd, -2.5 * s), 4.9 * s * b, 4.5 * s * b)
            put(c, pal, wrap, pal["fur"], far=far)
            for k in (-6.5, -4.0):
                q = add(an, sd, k * s)
                for w in range(-4, 5):
                    t = add(q, fwd, w * b)
                    if c.get(int(round(t[0])), int(round(t[1]))) in pal["fur"]:
                        _dot(c, t, pal["hide"][0 if far else 1])
    if kind == "raptor":
        # Тёмные полосы на бедре.
        for t_ in (0.25, 0.5, 0.75):
            q = lerp(hp, kn, t_)
            for k in range(-5, 0):
                t = add(q, tn, -k * b)
                if c.get(int(round(t[0])), int(round(t[1]))) in pal["scale"][2:]:
                    _dot(c, add(t, td, (k % 2) * 0.6), pal["scale"][1])
    if kind == "shaman":
        # Меховые сапоги с костяными завязками и костяной наколенник.
        boot = capsule(add(an, sd, -10.0 * s), an, 4.9 * s * b, 4.4 * s * b)
        put(c, pal, boot | foot, pal["fur"], far=far)
        for k in (-8.0, -4.5):
            q = add(an, sd, k * s)
            for w in range(-5, 6):
                t = add(q, fwd, w * b)
                if c.get(int(round(t[0])), int(round(t[1]))) in pal["fur"]:
                    _dot(c, t, pal["bone"][1 if far else 2])
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 3.0 * s, 3.3 * s), pal["bone"], far=far, cast=False)
    # Пальцы: у людей тёмные щели, у раптора белые когти и серп над ступнёй.
    toe = add(add(an, sd, 2.6 * s), fwd, flen * s)
    if kind == "raptor":
        cl = pal["bone"]
        for k in (0.0, 1.6):
            q = add(add(toe, fwd, 2.6 * s), sd, k - 0.6)
            _dot(c, q, cl[1 if far else 2])
            _dot(c, add(q, fwd, 1.0), cl[1 if far else 3])
        q = add(add(toe, fwd, -1.0), sd, -3.0)
        put(c, pal, capsule(q, add(add(q, fwd, 2.6), sd, -2.6), 1.3, 0.6), cl, far=far, cast=False)
    elif kind != "shaman" and not far:
        for k in (0.4, 2.4):
            q = add(add(toe, fwd, k * s), sd, -1.2)
            if c.get(int(round(q[0])), int(round(q[1]))) in pal["skin"]:
                _dot(c, q, pal["skin"][1])
    sole = set()
    solid = foot | ankle
    for (x, y) in foot:
        if (x, y + 1) not in solid:
            sole.add((x, y))
    base = pal["fur"] if kind == "shaman" else pal[skin]
    recolor(c, sole, lambda x, y, e: base[0])


def _tail(c, look, j, p):
    """Хвост раптора: от крестца назад, сужается, кончик качается; у лежащего тянется вдоль тела."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    w = max(0.0, min(1.0, -p["lean"] / 80.0))
    back = (-rt[0] * (1.0 - w) - up[0] * (0.18 + w), -rt[1] * (1.0 - w) - up[1] * (0.18 + w))
    n_ = math.hypot(*back) or 1.0
    back = (back[0] / n_, back[1] / n_)
    side = (-back[1], back[0])
    sway = p.get("wave", 0.0) * 1.2 + (p["th_n"] - p["th_f"]) * 0.03
    a0 = add(H, up, 1.0)
    a1 = add(add(a0, back, 11.0 * s), side, -1.0)
    a2 = add(add(a0, back, 21.0 * s), side, 1.5 + sway * 0.5)
    a3 = add(add(a0, back, 30.0 * s), side, 5.5 + sway)
    S = capsule(a0, a1, 6.0 * s * b, 4.6 * s) | capsule(a1, a2, 4.6 * s, 2.8 * s) | capsule(a2, a3, 2.8 * s, 1.0)
    put(c, pal, S, pal["scale"], soft=True)
    # Жёлтая полоса снизу и тёмные кольца.
    low = {q for q in S if (q[0], q[1] + 1) in S and (q[0], q[1] + 2) not in S}
    recolor(c, low, lambda x, y, e: pal["belly"][1])
    for t_ in (7.0, 12.0, 17.0, 22.0, 26.0):
        q = add(a0, back, t_ * s)
        for k in range(-6, 3):
            t = add(q, side, k)
            if c.get(int(round(t[0])), int(round(t[1]))) in pal["scale"][2:]:
                _dot(c, t, pal["scale"][1])


def _cloak(c, look, j, p):
    """Плащ шамана: тёмная шкура до голеней, по низу бахрома из бирюзовых и рыжих перьев."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = 33 * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 6.0 * s * b), up, 3 * s),
           (H[0] + 4 * s * b + sway * 0.3, H[1] + ln * 0.85), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - 13 * s * b + sway, H[1] + ln * 0.9)]
    S = poly(pts)
    put(c, pal, S, pal["cloak"], soft=True)
    # Ворс шкуры: редкие вертикальные штрихи.
    ck = pal["cloak"]
    for (x, y) in S:
        if (x * 5 + y * 2) % 11 == 0 and c.get(x, y) == ck[2]:
            c.set(x, y, ck[1])
            if c.get(x, y + 1) == ck[2]:
                c.set(x, y + 1, ck[1])
    # Перья по подолу: зубцы вниз от нижней кромки.
    lo, hi = pts[4], pts[2]
    nfe = 7
    for k in range(nfe):
        t = (k + 0.5) / nfe
        if t < 0.72:
            q = lerp(lo, pts[3], t / 0.72)
        else:
            q = lerp(pts[3], hi, (t - 0.72) / 0.28)
        q = (q[0], q[1] - 2.0)
        fe = capsule(q, (q[0] - 0.8, q[1] + 6.5 * s), 2.0 * s, 0.7)
        put(c, pal, fe, pal["feather" if k % 3 else "red"], cast=False)
        c.set(int(round(q[0])), int(round(q[1] + 1)), pal["bone"][2])


def _flap(c, look, j, p):
    """Передник дикаря: лоскут шкуры на поясе спереди, с костяной каймой."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    a = add(add(H, rt, 7.4 * s * b), up, 3.0 * s)
    e = add(add(H, rt, 0.5 * s * b), up, 3.0 * s)
    sway = -p["lean"] * 0.12
    S = poly([a, e, (e[0] + 1 + sway, e[1] + 13 * s), (a[0] - 1 + sway, a[1] + 16 * s)])
    put(c, pal, S, pal["hide"], soft=True)
    hem = {q for q in S if (q[0], q[1] + 1) not in S}
    recolor(c, hem, lambda x, y, e_: pal["bone"][2] if x % 3 else pal["hide"][0])


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    low = {"cave": "hide", "savage": "fur", "raptor": "scale", "shaman": "fur"}[kind]
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[low], soft=True)
    belly = {"cave": 0.3, "savage": 1.0, "raptor": 0.6, "shaman": 1.6}[kind]
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "shaman":
        tor |= ellipse(*P(lerp(N, H, 0.62), 4.0, 0), 7.5 * s * b, 7.0 * s)
    spots = ((5.0, 9.0, 2.2), (0.5, 17.0, 2.6), (5.5, 22.0, 2.0), (-4.5, 25.0, 2.3), (2.0, 27.5, 1.6))

    def mat(x, y):
        lx = ((x - N[0]) * rt[0] + (y - N[1]) * rt[1]) / (s * b)
        ly = -((x - N[0]) * up[0] + (y - N[1]) * up[1]) / s
        if kind == "cave":
            # Шкура через переднее плечо: кромка идёт наискось от плеча к спине у пояса.
            edge = ly - (15.0 - lx * 1.25)
            if edge < 0.0:
                return pal["skin"]
            if edge < 1.1:
                return [pal["hide"][0]] * 2 + [pal["hide"][1]] * 2
            for (sx, sy, r) in spots:
                if (lx - sx) ** 2 + ((ly - sy) * 0.9) ** 2 < r * r:
                    return pal["hair"][1:] + [pal["hair"][3]]
            return pal["hide"]
        if kind == "savage":
            # Меховая накидка на дальнем плече, белые шевроны раскраски на груди.
            if ly < 4.0 and lx < -1.0:
                return pal["fur"]
            if lx > -1.0 and ly > 6.0 and (abs(ly - 9.5 - abs(lx - 4.0) * 0.8) < 0.8
                                           or abs(ly - 13.5 - abs(lx - 4.0) * 0.8) < 0.8):
                return pal["bone"][1:] + [pal["bone"][3]]
            return pal["skin"]
        if kind == "raptor":
            # Жёлтое брюхо пластинами спереди, тёмные полосы по спине.
            front = lx - (1.8 - ly * 0.03)
            if front > 0.0:
                bl = pal["belly"]
                return [bl[0], bl[1], bl[1], bl[2]] if int(ly) % 4 == 0 else bl
            sc = pal["scale"]
            if lx < -2.0 and int(ly + lx * 0.5) % 6 < 2:
                return [sc[0], sc[1], sc[1], sc[2]]
            return sc
        # Шаман: голая грудь, нагрудник из рёбер, плечи под шкурой.
        if ly < 3.4 or lx < -5.0:
            return pal["cloak"]
        if 5.5 < ly < 18.5 and lx > -1.5:
            if abs(lx - 3.6) < 0.7:
                return pal["bone"]
            if int(ly - 5.5) % 4 < 2 and lx < 8.6 - abs(ly - 11.0) * 0.12:
                return pal["bone"]
        return pal["skin"]

    put(c, pal, tor, None, soft=True, mat=mat)
    if kind != "raptor":
        # Пояс: ремень с пряжкой-зубом, у дикаря с черепком, у шамана с аммонитом.
        belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
        belt_ramp = {"cave": "cord", "savage": "wood", "shaman": "gold"}[kind]
        put(c, pal, belt, pal[belt_ramp], cast=False)
        bk = P(H, 4.6, 4.1)
        if kind == "shaman":
            put(c, pal, ellipse(bk[0], bk[1], 2.6 * s, 2.4 * s), pal["bone"], cast=False)
            _dot(c, bk, pal["gold"][1])
            _dot(c, (bk[0] + 1, bk[1] - 1), pal["gold"][1])
            _dot(c, (bk[0] - 1, bk[1] + 1), pal["gold"][1])
        else:
            put(c, pal, ellipse(bk[0], bk[1], 1.9 * s, 1.7 * s), pal["bone"], cast=False)
            if kind == "savage":
                _dot(c, bk, pal["hair"][0])
    if kind == "cave":
        # Клык на шнурке под шеей.
        q = P(lerp(N, H, 0.2), 4.4, 0)
        _dot(c, (q[0] - 1, q[1] - 2), pal["cord"][1])
        _dot(c, (q[0], q[1] - 1), pal["cord"][1])
        _dot(c, q, pal["bone"][2])
        _dot(c, (q[0], q[1] + 1), pal["bone"][3])
        _dot(c, (q[0], q[1] + 2), pal["bone"][1])
    elif kind == "savage":
        # Ожерелье из зубов дугой под шеей.
        for k in range(6):
            q = P(lerp(N, H, 0.1 + 0.045 * math.sin(k / 5.0 * math.pi) * 2.2), -1.0 + k * 1.7, 0)
            _dot(c, q, pal["bone"][2])
            _dot(c, (q[0], q[1] + 1), pal["bone"][1] if k % 2 else pal["bone"][3])
        q = P(lerp(N, H, 0.62), 4.6, 0)
        _dot(c, q, pal["skin"][1])
        _dot(c, (q[0], q[1] + 1), pal["skin"][1])
    elif kind == "shaman":
        # Амулет-аммонит на груди поверх рёбер и полосы раскраски на животе.
        q = P(lerp(N, H, 0.2), 3.6, 0)
        put(c, pal, ellipse(q[0], q[1], 2.6 * s, 2.6 * s), pal["gold"], cast=False)
        _dot(c, q, pal["gold"][0])
        _dot(c, (q[0] + 1, q[1]), pal["gold"][0])
        _dot(c, (q[0] + 1, q[1] - 1), pal["gold"][0])
        for k in range(3):
            q = P(lerp(N, H, 0.68 + k * 0.07), 6.5, 0)
            for w in range(4):
                if c.get(int(round(q[0])) + w, int(round(q[1]))) in pal["skin"]:
                    c.set(int(round(q[0])) + w, int(round(q[1])), pal["red"][2])


def _head(c, look, j, p, hurt=False):
    pal, s, kind = look.pal, look.body.s, look.kind
    hc = j["head"]
    ang = p["lean"] + p["tilt"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    wave = p.get("wave", 0.0)

    def H(dx, dy):
        return (hc[0] + (dx * ca - dy * sa) * s, hc[1] + (dx * sa + dy * ca) * s)

    def tri(a, b_, e):
        return poly([H(*a), H(*b_), H(*e)])

    def dot(dx, dy, col):
        q = H(dx, dy)
        c.set(int(round(q[0])), int(round(q[1])), col)

    if kind == "raptor":
        sc, bl, mo, bo, ey = pal["scale"], pal["belly"], pal["mouth"], pal["bone"], pal["eye"]
        # Шея дугой: толстая у плеч, жёлтое горло спереди.
        neck = capsule(lerp(j["neck"], hc, -0.1), lerp(j["neck"], hc, 0.75), 4.8 * s, 3.9 * s)
        put(c, pal, neck, sc, soft=True)
        thr = capsule(add(lerp(j["neck"], hc, 0.05), j["rt"], 3.0), add(lerp(j["neck"], hc, 0.7), j["rt"], 2.6), 1.5, 1.3)
        put(c, pal, thr & neck, bl, cast=False)
        # Гребень из перьев на затылке.
        for k, (a, b_, e) in enumerate((((-5.5, -5.5), (-11.5 - wave, -9.5), (-3.0, -7.5)),
                                        ((-6.5, -2.5), (-12.5, -4.5 - wave), (-5.5, -5.5)),
                                        ((-6.0, 0.5), (-11.0, 1.0 + wave), (-6.5, -2.5)))):
            put(c, pal, tri(a, b_, e), pal["crest"], cast=False)
        op = 3.6 if hurt else 0.8
        skull = ellipse(*H(-0.5, -2.2), 6.6 * s, 6.0 * s, ang)
        # Пасть: красная глотка, нижняя челюсть, сверху длинная морда.
        gap = poly([H(1.0, 0.0), H(13.0, 0.4), H(12.2, 2.4 + op), H(2.0, 3.6 + op * 0.4)])
        put(c, pal, gap, [mo[0], mo[0], mo[1], mo[2]], cast=False)
        low = poly([H(-3.0, 1.0), H(1.5, 2.2 + op * 0.3), H(12.6, 1.8 + op), H(12.0, 3.8 + op), H(3.0, 6.0 + op * 0.5),
                    H(-3.0, 5.0)])
        put(c, pal, low, sc)
        chin = {q for q in low if (q[0], q[1] + 1) in low and (q[0], q[1] + 2) not in low}
        recolor(c, chin, lambda x, y, e: bl[1])
        snout = poly([H(1.0, -7.2), H(9.0, -5.6), H(14.0, -3.4), H(14.8, -0.8), H(13.4, 1.0), H(1.0, 1.4)])
        put(c, pal, skull | snout, sc, soft=True)
        # Зубы сверху и снизу, ноздря, полосы на темени, глаз с вертикальным зрачком.
        for k in range(5):
            dot(4.4 + k * 2.1, 1.8, bo[3])
            dot(4.4 + k * 2.1, 2.6, bo[2])
        for k in range(4):
            dot(5.4 + k * 2.1, 1.2 + op, bo[2])
        dot(13.0, -2.2, sc[0])
        dot(12.4, -2.4, sc[0])
        for (dx, dy) in ((-2.0, -7.4), (-1.0, -7.6), (2.0, -6.4), (3.0, -6.2), (-4.4, -4.6), (-3.6, -5.2), (6.0, -5.2)):
            dot(dx, dy, sc[1])
        # Надбровье тёмной дугой.
        for k in range(5):
            dot(1.6 + k, -5.2 + abs(k - 1.5) * 0.3, sc[0])
        if hurt:
            for k in range(-2, 3):
                dot(3.4 + k, -3.2, sc[0])
        else:
            eye = ellipse(*H(3.4, -3.2), 2.3 * s, 1.9 * s, ang)
            put(c, pal, eye, [ey[1], ey[2], ey[2], ey[3]], cast=False)
            dot(3.6, -3.6, ey[0])
            dot(3.6, -2.8, ey[0])
        return

    sk = pal["skin"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
    put(c, pal, neck, sk)
    hr = pal["hair"]
    if kind == "cave":
        # Копна за головой: масса на затылке, пряди на шею, вихры сверху.
        mop = ellipse(*H(-2.6, -2.4), 9.0 * s, 8.6 * s, ang)
        mop |= capsule(H(-6.0, 2.0), H(-8.8 - wave * 0.6, 8.6), 2.8 * s, 1.3)
        mop |= capsule(H(-3.0, 4.0), H(-4.6, 9.6 + wave * 0.5), 2.3 * s, 1.1)
        mop |= tri((-9.5, -6.0), (-13.0, -11.5 - wave * 0.5), (-5.0, -9.5))
        mop |= tri((-4.5, -9.5), (-4.0, -15.0), (1.0, -10.0))
        mop |= tri((0.5, -10.0), (4.5, -14.0), (5.5, -8.0))
        mop |= tri((-10.5, -2.0), (-14.0, -3.5), (-10.0, 2.0))
        put(c, pal, mop, hr, soft=True)
        face = ellipse(*H(1.4, -0.6), 6.6 * s, 6.8 * s, ang) | poly([H(-2.0, 1.0), H(7.4, 0.4), H(7.8, 5.2), H(4.6, 8.8),
                                                                    H(-1.6, 7.6)])
        put(c, pal, face, sk, soft=True)
        put(c, pal, ellipse(*H(8.4, 1.4), 1.9 * s, 1.7 * s), sk, cast=False)
        # Тяжёлое надбровье и чёлка зубцами до бровей.
        put(c, pal, capsule(H(2.6, -3.0), H(7.6, -2.6), 1.2 * s, 1.0 * s), [sk[0], sk[1], sk[1], sk[2]], cast=False)
        fringe = poly([H(-5.0, -8.5), H(6.6, -7.4), H(8.2, -4.4), H(5.6, -5.2), H(4.2, -3.4), H(1.8, -5.4), H(-0.4, -3.2),
                       H(-2.2, -5.0), H(-3.6, 0.6), H(-5.6, -1.0)])
        put(c, pal, fringe, hr, cast=False)
        # Ухо под прядью и щетина по челюсти.
        put(c, pal, ellipse(*H(-1.4, 1.2), 1.5 * s, 2.0 * s), [sk[0], sk[1], sk[2], sk[2]], cast=False)
        for (dx, dy) in ((1.0, 6.4), (2.6, 7.2), (4.2, 7.4), (5.8, 6.0), (0.0, 4.8), (6.6, 4.4)):
            dot(dx, dy, sk[1])
        # Кость в волосах: концы с головками торчат по обе стороны вихра.
        b0, b1 = H(-11.5, -8.0), H(-0.5, -13.5)
        bone = capsule(b0, b1, 1.3, 1.3) | ellipse(b0[0], b0[1] - 1, 2.0, 1.6) | ellipse(b0[0] - 1, b0[1] + 1, 1.6, 2.0) \
            | ellipse(b1[0], b1[1] - 1, 2.0, 1.6) | ellipse(b1[0] + 1, b1[1] + 1, 1.6, 2.0)
        put(c, pal, bone, pal["bone"], cast=False)
        put(c, pal, ellipse(*H(-5.8, -10.6), 2.8 * s, 2.4 * s, ang), hr, cast=False)
        ex, ey_, mx, my = 4.8, -0.8, 5.0, 5.2
    elif kind == "savage":
        # Грива на затылке и плечах, пучок на темени перехвачен костью.
        mane = ellipse(*H(-3.2, -1.0), 9.4 * s, 9.8 * s, ang)
        mane |= capsule(H(-7.0, 3.0), H(-10.5 - wave * 0.6, 11.0), 3.4 * s, 1.6)
        mane |= capsule(H(-3.5, 5.0), H(-6.0, 12.0 + wave * 0.5), 2.8 * s, 1.4)
        mane |= capsule(H(-1.5, -9.0), H(-2.6, -14.0), 2.6 * s, 2.0 * s)
        mane |= ellipse(*H(-3.4 - wave * 0.5, -16.4), 4.0 * s, 2.8 * s, ang - 20)
        mane |= tri((-5.0, -15.0), (-9.5, -18.5), (-5.5, -18.0))
        put(c, pal, mane, hr, soft=True)
        put(c, pal, capsule(H(-4.6, -11.4), H(1.4, -10.6), 1.2, 1.2) | ellipse(*H(-5.2, -11.6), 1.7, 1.7)
            | ellipse(*H(2.0, -10.6), 1.7, 1.7), pal["bone"], cast=False)
        face = ellipse(*H(1.0, -1.6), 7.4 * s, 7.4 * s, ang) | poly([H(-3.0, 1.0), H(7.8, 0.4), H(8.2, 5.6), H(4.6, 9.4),
                                                                    H(-2.0, 8.4)])
        put(c, pal, face, sk, soft=True)
        hairline = poly([H(-6.5, -9.0), H(5.6, -8.4), H(7.6, -5.6), H(3.0, -6.4), H(-1.0, -5.2), H(-4.0, -1.0),
                         H(-6.5, -2.0)])
        put(c, pal, hairline, hr, cast=False)
        # Борода лопатой до груди.
        beard = poly([H(-2.6, 3.0), H(1.0, 3.6), H(4.0, 3.0), H(8.4, 4.0), H(8.4, 7.4), H(6.6, 12.6), H(3.2, 15.0),
                      H(0.0, 11.5), H(-2.8, 7.0)])
        put(c, pal, beard, hr, soft=True, cast=False)
        for (dx, dy) in ((2.0, 9.0), (4.0, 11.5), (5.6, 8.6), (0.6, 6.4), (3.0, 13.0)):
            dot(dx, dy, hr[3])
        # Нос картошкой, кость сквозь него, надбровье, белая полоса раскраски под глазом.
        put(c, pal, ellipse(*H(8.6, 1.0), 2.1 * s, 1.9 * s), sk, cast=False)
        put(c, pal, capsule(H(6.4, 2.8), H(11.4, 2.6), 0.8, 0.8), pal["bone"], cast=False)
        put(c, pal, capsule(H(2.4, -3.4), H(8.0, -3.0), 1.5 * s, 1.2 * s), [sk[0], sk[0], sk[1], sk[2]], cast=False)
        for k in range(5):
            dot(1.4 + k, 1.4, pal["bone"][2])
        ex, ey_, mx, my = 4.8, -1.0, 5.4, 5.6
    else:
        fe, rd, bo = pal["feather"], pal["red"], pal["bone"]
        # Перья за черепом веером и меховой ворот плаща на загривке.
        for k, (a, b_, e) in enumerate((((-7.0, -11.5), (-15.5, -16.0 - wave), (-10.0, -8.5)),
                                        ((-9.0, -8.5), (-17.0, -9.0 - wave), (-10.0, -4.5)),
                                        ((-9.5, -4.5), (-15.5, -2.0 + wave), (-8.5, -1.0)),
                                        ((-5.0, -12.5), (-10.0, -19.0), (-2.5, -13.5)))):
            put(c, pal, tri(a, b_, e), rd if k % 2 else fe, soft=False)
        col = poly([H(-9, 9), H(-11.0, 0.5), H(-5, 3), H(2, 9)])
        put(c, pal, col, pal["fur"], soft=True)
        face = ellipse(*H(0.5, -0.6), 7.0 * s, 6.2 * s, ang) | poly([H(-3.5, 1.5), H(6.6, 1.0), H(6.4, 5.2), H(2.8, 8.4),
                                                                    H(-2.8, 7.4)])
        put(c, pal, face, sk, soft=True)
        put(c, pal, ellipse(*H(7.4, 1.6), 1.7 * s, 1.6 * s), sk, cast=False)
        # Седая борода клином и красные полосы раскраски на скуле.
        beard = poly([H(-1.0, 5.4), H(2.0, 4.6), H(6.6, 5.2), H(6.0, 9.5), H(4.0, 15.0), H(1.6, 10.5)])
        put(c, pal, beard, hr, soft=True, cast=False)
        for k in range(4):
            dot(0.6 + k, 2.2, rd[2])
            dot(0.2 + k, 3.8, rd[2])
        # Череп тираннозавра шлемом: затылок, свод, длинная верхняя челюсть над лбом.
        helm = ellipse(*H(-2.5, -9.6), 8.8 * s, 6.0 * s, ang)
        helm |= poly([H(-3.0, -14.6), H(7.5, -13.8), H(13.0, -10.6), H(14.0, -7.6), H(12.4, -5.6), H(3.0, -5.2),
                      H(-3.0, -5.2)])
        helm |= poly([H(-8.0, -12.0), H(-11.6, -6.0), H(-9.4, -0.6), H(-5.6, -1.6), H(-5.0, -5.0)])
        put(c, pal, helm, bo, soft=True)
        for k in range(5):
            put(c, pal, tri((3.2 + k * 2.1, -5.6), (4.2 + k * 2.1, -2.6 - (k % 2) * 0.5), (5.2 + k * 2.1, -5.6)), bo,
                cast=False)
        # Глазница, окно перед ней, ноздря, трещины и шов скулы.
        put(c, pal, ellipse(*H(0.6, -9.8), 2.7 * s, 2.3 * s, ang), [0, 0, 0, bo[0]], cast=False)
        put(c, pal, ellipse(*H(6.0, -9.4), 2.0 * s, 1.5 * s, ang), [bo[0], bo[0], bo[0], bo[1]], cast=False)
        dot(11.4, -9.6, bo[0])
        dot(12.2, -9.4, bo[0])
        for (dx, dy) in ((-6.0, -12.0), (-5.2, -11.2), (-5.6, -10.2), (9.0, -7.4), (8.2, -7.0), (-8.6, -6.0), (-8.2, -5.0)):
            dot(dx, dy, bo[1])
        for k in range(9):
            dot(-3.0 + k * 1.6, -5.8, bo[1])
        ex, ey_, mx, my = 3.8, 0.2, 4.2, 5.6
    # Глаз: белок и зрачок; при ударе зажмурен в черту. Рот: черта, при ударе раскрыт.
    q = H(ex, ey_)
    x, y = int(round(q[0])), int(round(q[1]))
    if hurt:
        for k in range(-2, 2):
            c.set(x + k, y, sk[0])
        c.set(x - 2, y - 1, sk[0])
    else:
        c.set(x - 1, y, pal["bone"][3])
        c.set(x, y, 0)
        c.set(x, y - 1, 0)
        c.set(x - 1, y - 1, pal["bone"][2])
    q = H(mx, my)
    x, y = int(round(q[0])), int(round(q[1]))
    lip = pal["hair"][0] if kind == "savage" else sk[0]
    c.set(x, y, lip)
    c.set(x + 1, y, lip)
    c.set(x - 1, y, lip)
    if kind == "savage":
        # Клык снизу.
        c.set(x + 1, y - 1, pal["bone"][3])
    if hurt:
        c.set(x, y + 1, lip)
        c.set(x + 1, y + 1, 0)
        c.set(x, y - 1, pal["bone"][3])


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if kind == "raptor":
        _tail(c, look, j, p)
    if kind == "shaman":
        _cloak(c, look, j, p)
    _torso(c, look, j, p)
    _leg(c, look, j, "n", False, p)
    if kind == "savage":
        _flap(c, look, j, p)
    _head(c, look, j, p, hurt)
    _arm(c, look, j, "n", False, p)
    c.outline(0)
    bottom = max(y for y in range(c.h) for x in range(c.w) if c.px[y][x] is not None)
    out = Canvas(w, h)
    out.paste(c, 0, (h - FOOT) - bottom)
    out.head = (j["head"][0], j["head"][1] + (h - FOOT) - bottom)
    return out


def render(frames, look, w, h, hurt_set):
    return strip([fighter(p, look, w, h, hurt=(k in hurt_set or p["eyes"] < 0.5)) for k, p in enumerate(frames)])


def fighters():
    """Ленты бойцов → (холст, палитра). Кадры и их порядок из `pixel_brawl16` (HERO_ANIM, FOE_ANIM)."""
    out = {}
    hl = hero_look()
    out["brawl_hero"] = (render(pb.hero_frames(), hl, FW, FH, pb.HURT_FRAMES["hero"]), hl.pal.colors)
    tl = thug_look()
    out["brawl_thug"] = (render(pb.foe_frames(), tl, FW, FH, pb.HURT_FRAMES["foe"]), tl.pal.colors)
    kl = knife_look()
    out["brawl_knife"] = (render(pb.foe_frames(knife=True), kl, FW, FH, pb.HURT_FRAMES["foe"]), kl.pal.colors)
    bl = boss_look()
    out["brawl_boss"] = (render(pb.foe_frames(boss=True), bl, BW, BH, pb.HURT_FRAMES["foe"]), bl.pal.colors)
    return out


def faces():
    """Лица для HUD: голова из первого кадра стойки, 32×32, в палитре бойца."""
    out = {}
    for key, look, frame, w, h, up in (("hero", hero_look(), pb.hero_frames()[0], FW, FH, 17),
                                       ("thug", thug_look(), pb.foe_frames()[0], FW, FH, 19),
                                       ("knife", knife_look(), pb.foe_frames(knife=True)[0], FW, FH, 17),
                                       ("boss", boss_look(), pb.foe_frames(boss=True)[0], BW, BH, 22)):
        look.club = False  # дубина закрыла бы лицо на портрете
        f = fighter(frame, look, w, h)
        hx, hy = int(round(f.head[0])), int(round(f.head[1]))
        ox = {"knife": 13, "boss": 13}.get(key, 15)
        c = Canvas(32, 32)
        for y in range(32):
            for x in range(32):
                sx, sy = hx - ox + x, hy - up + y
                if 0 <= sx < w and 0 <= sy < h:
                    c.px[y][x] = f.px[sy][sx]
        out["brawl_face_" + key] = (c, look.pal.colors)
    return out


# --- Стойбище под скалой --------------------------------------------------------------------------

def street_pal():
    p = Pal(0x100A0C)
    p.add("rock", [0x2E2428, 0x4E3E44, 0x7C686E, 0xA8949A])
    p.add("clay", [0x4A1E16, 0x7C3422, 0xB05434, 0xD8805A])
    p.add("dirt", [0x3A1A14, 0x5E2C1E, 0x8A442E, 0xAE6446])
    p.add("sand", [0x6A4424, 0x9A6C38, 0xC89858, 0xE8C48A])
    p.add("bone", BONE)
    p.add("wood", WOOD)
    p.add("hide", HIDE)
    p.add("fur", FUR)
    p.add("leaf", SCALE)
    p.add("deep", [0x0E2A30, 0x1C465A, 0x2C8084, 0x7CCCB4])
    p.add("lava", [0x8A1C10, 0xEC5E24, 0xF4CC52, 0xFFF4B0])
    p.add("dark", [0x140C0E, 0x20161A, 0x34262A, 0x4E3C3C])
    p.add("haze", [0x58A8A0, 0x9CD4B4, 0xF4E8B6, 0xFFF8E0])
    p.add("egg", [0x8A7A5A, 0xC8BC98, 0xF4EEDA, 0xFFFFFF])
    return p


class Camp(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(144)

    def line(self, a, b, col, r=0.6):
        for q in capsule(a, b, r, r):
            self.c.set(q[0], q[1], col)

    def lift(self, S, names=("rock", "clay", "dirt", "sand", "wood", "fur", "hide", "leaf", "dark"), dither=None):
        """Свет: пиксели названных рамп на тон светлее."""
        for (x, y) in S:
            if dither is not None and not dither(x, y):
                continue
            e = self.c.get(x, y)
            if e is None:
                continue
            for name in names:
                R_ = self.R(name)
                if e in R_ and R_.index(e) < 3:
                    self.c.set(x, y, R_[R_.index(e) + 1])
                    break

    def cliff(self, x0, y0, x1, y1, ramp="rock", band=26):
        """Скала пластами: волнистые слои, трещины-швы между глыбами, сколы и осыпь."""
        R_ = self.R(ramp)
        r = self.rng
        ph = r.random() * 6.0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                v = math.sin(x * 0.045 + math.sin(y * 0.05 + ph) * 1.5) + math.sin(y * 0.21 + x * 0.012) * 0.6 \
                    + math.sin((x + y) * 0.09 + ph) * 0.3
                t = 2
                if v > 1.1 and (x + y) % 2 == 0:
                    t = 3
                elif v < -0.95 and (x + y) % 2 == 0:
                    t = 1
                yy = y + int(round(math.sin(x * 0.021 + ph) * 5 + math.sin(x * 0.13) * 1.2))
                row = yy // band
                k = yy % band
                if k == 0:
                    t = 0
                elif k == 1:
                    t = 3
                elif k == band - 1:
                    t = 1
                else:
                    # Вертикальные швы глыб: в каждом пласте свой шаг и сдвиг.
                    step = (46 + (row * 17) % 30) * (2 if ramp == "clay" else 1)
                    jx = (x + row * 37 + int(math.sin(yy * 0.4 + row) * 1.6)) % step
                    if jx == 0:
                        t = 0
                    elif jx == 1:
                        t = 3
                    elif jx == step - 1:
                        t = 1
                self.c.set(x, y, R_[t])
        self.noise(x0, y0, x1, y1, R_, 0.035)
        # Короткие косые трещины и сколы.
        for _ in range(max(2, (x1 - x0) * (y1 - y0) // 2600)):
            x, y = r.randint(x0 + 4, x1 - 4), r.randint(y0 + 4, max(y0 + 5, y1 - 22))
            for _k in range(r.randint(6, 16)):
                if x0 < x < x1 and y0 < y < y1:
                    self.c.set(x, y, R_[0])
                    self.c.set(x + 1, y, R_[3])
                y += 1
                x += r.choice((-1, 0, 0, 1))

    def overhang(self, x0, x1, vines=True):
        """Козырёк скалы над стеной: тёмный камень, кромка со мхом, свисающие лианы."""
        R_, L = self.R("rock"), self.R("leaf")
        r = self.rng
        self.cliff(x0, 0, x1, 31, "rock", 14)
        self.dark(x0, 0, x1, 19, 1)
        self.dark(x0, 0, x1, 8, 1, dither=True)
        for x in range(x0, x1 + 1):
            d = 2 + int((math.sin(x * 0.19) + math.sin(x * 0.07 + 1.0)) * 1.6 + 2.2)
            self.c.set(x, 20, R_[3])
            for y in range(31 - 1, 31 + d):
                self.c.set(x, y, L[1] if y < 31 + d - 1 else L[0])
            self.c.set(x, 29, L[2] if x % 3 else L[3])
        self.dark(x0, 32, x1, 37, 1)
        self.dark(x0, 38, x1, 41, 1, dither=True)
        if vines:
            x = x0 + r.randint(6, 30)
            while x < x1 - 4:
                ln = r.randint(12, 58)
                for y in range(30, 30 + ln):
                    xx = x + int(round(math.sin(y * 0.16 + x) * 1.6))
                    self.c.set(xx, y, L[1])
                    if y % 5 == 0:
                        self.c.set(xx - 1, y, L[2])
                        self.c.set(xx - 2, y + 1, L[2])
                    if y % 5 == 3:
                        self.c.set(xx + 1, y, L[2])
                        self.c.set(xx + 2, y + 1, L[3])
                x += r.randint(22, 70)

    def glow(self, cx, cy, rx, ry):
        """Пятно света от огня: ядро светлее целиком, край шахматкой."""
        self.lift(ellipse(cx, cy, rx, ry), dither=lambda x, y: (x + y) % 2 == 0)
        self.lift(ellipse(cx, cy, rx * 0.55, ry * 0.55))

    def torch(self, x, y):
        """Факел в расщелине: палка с обмоткой, пламя, свет на камне."""
        W, Lv = self.R("wood"), self.R("lava")
        self.glow(x, y - 6, 34, 30)
        self.line((x, y + 22), (x + 1, y + 2), W[2], 1.2)
        self.line((x - 1, y + 22), (x, y + 4), W[1], 0.5)
        self.rect(x - 2, y + 1, x + 3, y + 4, self.R("fur")[2])
        self.rect(x - 2, y + 4, x + 3, y + 4, self.R("fur")[0])
        fl = poly([(x - 4, y), (x - 3, y - 7), (x - 1, y - 5), (x + 1, y - 14), (x + 3, y - 6), (x + 5, y - 9), (x + 5, y)])
        for (px, py) in fl | ellipse(x + 0.5, y - 2, 4.5, 3.5):
            d = abs(px - x - 0.5) * 1.2 + (y - py) * 0.55
            self.c.set(px, py, Lv[3] if d < 2.6 else Lv[2] if d < 5.0 else Lv[1])
        self.c.set(x - 5, y - 12, Lv[2])
        self.c.set(x + 6, y - 15, Lv[1])

    def cave(self, cx, top, w):
        """Вход в пещеру: арка с глыбами по краю, темнота, сталактиты, отсвет костра в глубине."""
        D, R_, Lv = self.R("dark"), self.R("rock"), self.R("lava")
        hole = set()
        for y in range(top, WALL_Y + 1):
            k = min(1.0, (y - top) / (w * 0.55))
            half = w * 0.5 * math.sqrt(max(0.0, 1.0 - (1.0 - k) ** 2)) + math.sin(y * 0.3) * 1.5
            for x in range(int(cx - half), int(cx + half) + 1):
                hole.add((x, y))
        rim = set()
        for (x, y) in hole:
            for dx in range(-5, 6):
                for dy in range(-5, 2):
                    q = (x + dx, y + dy)
                    if q not in hole and q[1] <= WALL_Y:
                        rim.add(q)
        self.put(rim, R_, soft=True, cast=False)
        for (x, y) in rim:
            if (x * 7 + y * 3) % 23 == 0:
                self.c.set(x, y, R_[0])
        for (x, y) in hole:
            k = (y - top) / float(WALL_Y - top)
            near = min(abs(x - cx) / (w * 0.5), 1.0)
            t = 0 if k < 0.45 or near > 0.75 else 1 if (x + y) % 2 or k < 0.7 else 2
            self.c.set(x, y, D[t])
        # Отсвет костра в глубине и дальняя стена.
        for (x, y) in ellipse(cx + w * 0.12, WALL_Y - 26, w * 0.22, 16) & hole:
            d = math.hypot((x - cx - w * 0.12) / (w * 0.22), (y - WALL_Y + 26) / 16.0)
            self.c.set(x, y, Lv[1] if d < 0.35 else Lv[0] if d < 0.7 or (x + y) % 2 else D[2])
        for (x, y) in poly([(cx + w * 0.12 - 3, WALL_Y - 24), (cx + w * 0.12, WALL_Y - 34), (cx + w * 0.12 + 3, WALL_Y - 24)]):
            self.c.set(x, y, Lv[2])
        # Сталактиты с кромки свода.
        for k in range(-3, 4):
            sx = int(cx + k * w * 0.12)
            ty = min(y for (x, y) in hole if x == sx)
            ln = 8 + (k * k * 5 + 7) % 12
            for (x, y) in poly([(sx - 3, ty - 1), (sx + 3, ty - 1), (sx, ty + ln)]):
                self.c.set(x, y, R_[1] if x >= sx else R_[2])
        # Порог: плоский камень у входа.
        self.bevel(int(cx - w * 0.5) - 6, WALL_Y - 3, int(cx + w * 0.5) + 6, WALL_Y, R_)

    def painting(self, x, y, kind):
        """Наскальная роспись охрой и углём."""
        O, Hd, D = self.R("sand")[3], self.R("hide")[1], self.R("dark")[1]
        if kind == "mammoth":
            body = ellipse(x + 13, y + 9, 12, 8) | ellipse(x + 3, y + 6, 5, 6)
            for (px, py) in body:
                self.c.set(px, py, Hd if (px + py) % 3 else self.R("hide")[0])
            for lx in (x + 6, x + 11, x + 17, x + 22):
                self.rect(lx, y + 15, lx + 1, y + 22, Hd)
            self.line((x, y + 9), (x - 3, y + 17), Hd, 0.9)
            self.line((x - 3, y + 17), (x - 1, y + 19), Hd, 0.6)
            self.line((x + 1, y + 11), (x - 6, y + 13), O, 0.6)
            self.line((x - 6, y + 13), (x - 7, y + 9), O, 0.5)
            self.c.set(x + 2, y + 5, D)
        elif kind == "hunter":
            self.line((x, y + 4), (x, y + 12), D, 0.6)
            self.line((x, y + 12), (x - 3, y + 18), D, 0.5)
            self.line((x, y + 12), (x + 3, y + 18), D, 0.5)
            self.line((x, y + 6), (x + 5, y + 3), D, 0.5)
            self.line((x + 2, y - 3), (x + 9, y + 9), D, 0.4)
            for (px, py) in ellipse(x, y + 1, 2, 2):
                self.c.set(px, py, D)
        elif kind == "hand":
            for (px, py) in ellipse(x, y + 5, 4, 4):
                self.c.set(px, py, O)
            for k, dx in enumerate((-4, -2, 0, 2)):
                self.line((x + dx, y + 2), (x + dx - 1 + k * 0.5, y - 5 + abs(k - 1.5) * 1.2), O, 0.6)
            self.line((x + 4, y + 5), (x + 7, y + 2), O, 0.6)
        elif kind == "dino":
            self.line((x, y + 6), (x + 14, y + 8), Hd, 2.2)
            self.line((x + 14, y + 8), (x + 26, y + 3), Hd, 1.0)
            self.line((x, y + 6), (x - 5, y - 2), Hd, 1.4)
            self.line((x - 5, y - 2), (x - 11, y - 1), Hd, 1.6)
            for lx in (x + 3, x + 9):
                self.line((lx, y + 8), (lx - 1, y + 17), Hd, 0.9)
            for k in range(4):
                self.c.set(x - 10 + k * 2, y + 1, O)
            self.c.set(x - 7, y - 3, D)
        else:
            # Спираль-солнце.
            for k in range(60):
                a = k * 0.33
                rr = 1.0 + k * 0.13
                self.c.set(x + math.cos(a) * rr, y + math.sin(a) * rr, O)
            for k in range(8):
                a = k * math.pi / 4
                self.line((x + math.cos(a) * 11, y + math.sin(a) * 11), (x + math.cos(a) * 14, y + math.sin(a) * 14), Hd, 0.5)

    def stretched(self, x, y, w, h, ramp="hide"):
        """Шкура на раме из жердей: растянута ремешками за углы, пятна, штопка."""
        W, Hr = self.R("wood"), self.R(ramp)
        self.dark(x + 3, y + 3, x + w + 3, y + h + 4, 1)
        for (a, b) in (((x, y), (x + w, y)), ((x, y + h), (x + w, y + h)), ((x + 2, y - 4), (x + 2, y + h + 6)),
                       ((x + w - 2, y - 4), (x + w - 2, y + h + 6))):
            self.line(a, b, W[2], 1.3)
            self.line((a[0], a[1] - 1), (b[0], b[1] - 1), W[3], 0.4)
        S = poly([(x + 9, y + 7), (x + w * 0.5, y + 10), (x + w - 9, y + 6), (x + w - 12, y + h * 0.5), (x + w - 8, y + h - 7),
                  (x + w * 0.5, y + h - 10), (x + 8, y + h - 6), (x + 12, y + h * 0.5)])
        self.put(S, Hr, soft=True, cast=False)
        for (cx_, cy_) in ((x + 9, y + 7), (x + w - 9, y + 6), (x + w - 8, y + h - 7), (x + 8, y + h - 6)):
            ex = x + 2 if cx_ < x + w / 2 else x + w - 2
            ey = y if cy_ < y + h / 2 else y + h
            self.line((cx_, cy_), (ex, ey), self.R("bone")[1], 0.4)
        r = self.rng
        for _ in range(int(w * h / 110)):
            px, py = r.randint(x + 12, x + w - 12), r.randint(y + 12, y + h - 12)
            for q in ellipse(px, py, r.uniform(1.5, 3.2), r.uniform(1.2, 2.4)) & S:
                self.c.set(q[0], q[1], self.R("dark")[2] if ramp == "hide" else Hr[1])

    def hut(self, cx, w, h):
        """Хижина: купол из сшитых шкур на бивнях, вход в рамке из двух бивней, дымник с жердями."""
        Hd, Fu, W, B, D = self.R("hide"), self.R("fur"), self.R("wood"), self.R("bone"), self.R("dark")
        yb = WALL_Y
        self.dark(cx - w // 2 + 6, yb - h + 8, cx + w // 2 + 8, yb, 1, dither=True)
        # Жерди дымника торчат над куполом.
        for dx in (-9, -3, 4, 10):
            self.line((cx + dx * 0.4, yb - h + 6), (cx + dx * 1.6, yb - h - 16), W[2], 1.2)
            self.line((cx + dx * 0.4 - 1, yb - h + 6), (cx + dx * 1.6 - 1, yb - h - 16), W[3], 0.4)
        patches = {}
        for y in range(yb - h, yb + 1):
            for x in range(cx - w // 2, cx + w // 2 + 1):
                u, v = (x - cx) / (w * 0.5), (yb - y) / float(h)
                if u * u + v * v > 1.0:
                    continue
                a = math.atan2(v, u)
                ring = int(math.hypot(u, v) * 3.0 + math.sin(a * 5.0) * 0.12)
                sect = int((a + ring * 0.33) / (math.pi / (5 + ring * 2)))
                patches.setdefault((ring, sect), set()).add((x, y))
        for (ring, sect), S in sorted(patches.items()):
            ramp = (Hd, Fu, [Hd[0], Hd[1], Hd[1], Hd[2]], [Fu[1], Fu[2], Fu[3], Fu[3]])[(ring * 3 + sect * 5) % 4]
            self.put(S, ramp, soft=True, cast=False)
            if ramp is Hd:
                for q in S:
                    if (q[0] * 13 + q[1] * 7) % 41 == 0:
                        for t in ellipse(q[0], q[1], 2, 1.5) & S:
                            self.c.set(t[0], t[1], D[2])
            # Стежки по левому краю лоскута.
            for q in S:
                if (q[0] - 1, q[1]) not in S and q[1] % 4 == 0 and q[1] < yb - 3:
                    self.c.set(q[0], q[1], B[1])
                    self.c.set(q[0] - 1, q[1], B[1])
        # Тень купола справа и свет слева сверху.
        for y in range(yb - h, yb + 1):
            for x in range(cx, cx + w // 2 + 1):
                u, v = (x - cx) / (w * 0.5), (yb - y) / float(h)
                if 0.62 < u * u + v * v <= 1.0 and u > 0.35 and (x + y) % 2 == 0:
                    e = self.c.get(x, y)
                    self.c.set(x, y, self.p.darker.get(e, e))
        # Вход: тёмный проём, полог из шкуры откинут, бивни дугами.
        dw, dh = int(w * 0.17), int(h * 0.56)
        door = set()
        for y in range(yb - dh, yb + 1):
            k = min(1.0, (y - (yb - dh)) / (dw * 0.9))
            half = dw * math.sqrt(max(0.0, 1.0 - (1.0 - k) ** 2))
            for x in range(int(cx - half), int(cx + half) + 1):
                door.add((x, y))
        for (x, y) in door:
            self.c.set(x, y, D[0] if (x - cx) < dw * 0.2 or (x + y) % 2 else D[1])
        flap = poly([(cx + dw * 0.1, yb - dh + 2), (cx + dw, yb - dh * 0.6), (cx + dw + 2, yb), (cx + dw * 0.45, yb)])
        self.put(flap & door, Fu, soft=True, cast=False)
        for sgn in (-1, 1):
            pts = []
            for k in range(13):
                t = k / 12.0
                a = math.pi * 0.5 * t
                pts.append((cx + sgn * (dw + 7 - (dw + 9) * math.sin(a) ** 1.6), yb - (dh + 16) * math.sin(a * 0.98) ** 0.8))
            tusk = set()
            for k in range(12):
                tusk |= capsule(pts[k], pts[k + 1], 4.2 - k * 0.27, 4.0 - k * 0.27)
            self.put(tusk, B, soft=True)
        # Череп над входом.
        sk = ellipse(cx, yb - dh - 22, 7, 6) | poly([(cx - 5, yb - dh - 19), (cx + 5, yb - dh - 19), (cx + 3, yb - dh - 11),
                                                     (cx - 3, yb - dh - 11)])
        self.put(sk, B, soft=True)
        for sx in (cx - 4, cx + 2):
            self.rect(sx, yb - dh - 23, sx + 2, yb - dh - 21, D[0])
        self.rect(cx - 2, yb - dh - 13, cx + 2, yb - dh - 13, D[0])
        self.c.set(cx, yb - dh - 17, D[0])
        # Камни-грузы по низу купола.
        for x in range(cx - w // 2 + 4, cx + w // 2 - 2, 15):
            if abs(x - cx) > dw + 12:
                self.put(ellipse(x, yb - 3, 7, 4.5), self.R("rock"), soft=True)

    def rack(self, x, y, w, h):
        """Сушилка: две рогатины, перекладина, на ней рыба, окорок и связка листьев."""
        W, B, Hd = self.R("wood"), self.R("bone"), self.R("hide")
        for px in (x, x + w):
            self.dark(px + 2, y, px + 4, WALL_Y, 1)
            self.line((px, WALL_Y), (px, y + 2), W[2], 1.6)
            self.line((px - 1, WALL_Y), (px - 1, y + 2), W[3], 0.4)
            self.line((px, y + 4), (px - 4, y - 5), W[2], 1.1)
            self.line((px, y + 4), (px + 4, y - 5), W[1], 1.1)
        self.line((x - 6, y + 2), (x + w + 6, y), W[2], 1.5)
        self.line((x - 6, y + 1), (x + w + 6, y - 1), W[3], 0.4)
        n = max(2, (w - 8) // 13)
        for k in range(n):
            px = x + 9 + k * (w - 18) // max(1, n - 1)
            self.line((px, y + 2), (px, y + 8), B[1], 0.4)
            kind = (k + x) % 3
            if kind == 0:
                fish = ellipse(px, y + 18, 3.6, 10) | poly([(px - 4, y + 32), (px, y + 25), (px + 4, y + 32)])
                self.put(fish, self.R("deep")[1:] + [self.R("haze")[1]], soft=True)
                self.c.set(px - 1, y + 12, self.R("dark")[0])
                for yy in range(y + 15, y + 26, 3):
                    self.c.set(px + 1, yy, self.R("deep")[1])
            elif kind == 1:
                ham = ellipse(px, y + 17, 6, 8)
                self.put(ham, Hd, soft=True)
                self.put(capsule((px, y + 8), (px, y + 11), 1.3, 1.3) | ellipse(px, y + 7, 2.2, 1.6), B, cast=False)
                self.put(ellipse(px - 1, y + 16, 2.2, 3), [Hd[2], Hd[3], Hd[3], B[2]], cast=False)
            else:
                L = self.R("leaf")
                for dx in (-3, 0, 3):
                    self.line((px, y + 8), (px + dx, y + 24), L[1], 1.0)
                    self.line((px, y + 8), (px + dx * 0.8, y + 20), L[2], 0.5)
                self.rect(px - 1, y + 8, px + 1, y + 9, B[1])

    def frond(self, x, y, ang, ln, droop=0.5, ramp="leaf", k=1.0):
        """Вайя папоротника: жилка дугой и листочки по обе стороны, к концу короче."""
        L = self.R(ramp)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        prev = None
        for i in range(int(ln) + 1):
            t = i / float(ln)
            px = x + ca * i
            py = y + sa * i + t * t * ln * droop
            if prev is not None:
                dx, dy = px - prev[0], py - prev[1]
                n_ = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / n_, dx / n_
                if i % 2 == 0:
                    ll = (1.0 - abs(t * 1.7 - 0.7)) * 6.0 * k + 1.5
                    for sgn in (-1, 1):
                        col = L[2] if (ny * sgn < 0) else L[1]
                        for m in range(1, int(ll) + 1):
                            self.c.set(px + nx * sgn * m + dx / n_ * m * 0.45, py + ny * sgn * m + dy / n_ * m * 0.45, col)
                        self.c.set(px + nx * sgn * ll + dx / n_ * ll * 0.45, py + ny * sgn * ll + dy / n_ * ll * 0.45,
                                   L[3] if ny * sgn < 0 else L[1])
                self.c.set(px, py, L[3])
                self.c.set(px, py + 1, L[0])
            prev = (px, py)

    def fern(self, x, yb, n=7, ln=26, ramp="leaf"):
        for k in range(n):
            a = -165 + k * (150.0 / max(1, n - 1)) + self.rng.uniform(-6, 6)
            self.frond(x, yb - 2, a, ln * self.rng.uniform(0.75, 1.1), 0.45 + abs(a + 90) / 300.0, ramp, ln / 26.0)

    def cycad(self, x, yb, h, w=13):
        """Саговник: бочонок-ствол в ромбах коры, наверху шапка длинных вай."""
        W, r = self.R("wood"), self.rng
        self.dark(x + w // 2, yb - h + 4, x + w // 2 + 4, yb, 1)
        S = set()
        for y in range(yb - h, yb + 1):
            k = (yb - y) / float(h)
            half = w * 0.5 * (0.82 + 0.3 * math.sin(k * 3.0))
            for xx in range(int(x - half), int(x + half) + 1):
                S.add((xx, y))
        self.put(S, W, soft=True, cast=False)
        for (xx, y) in S:
            if ((xx - x) + (y - yb)) % 7 == 0 or ((xx - x) - (y - yb)) % 7 == 0:
                e = self.c.get(xx, y)
                self.c.set(xx, y, self.p.darker.get(e, e))
        for k in range(9):
            a = -172 + k * 20.5 + r.uniform(-5, 5)
            self.frond(x, yb - h + 2, a, r.uniform(30, 40), 0.42 + abs(a + 90) / 260.0, "leaf", 1.25)
        self.put(ellipse(x, yb - h, 4.5, 3.5), [W[1], W[2], W[3], self.R("sand")[2]], cast=False)

    def horsetail(self, x, yb, h):
        """Хвощ: членистый стебель с мутовками тонких веточек."""
        L = self.R("leaf")
        for y in range(yb - h, yb + 1):
            self.c.set(x, y, L[2])
            self.c.set(x + 1, y, L[1])
        for k, y in enumerate(range(yb - 5, yb - h, -7)):
            self.rect(x - 1, y, x + 2, y, L[0])
            ll = max(2, int((1.0 - abs(k * 7.0 / h - 0.45)) * 9))
            for m in range(1, ll):
                self.c.set(x - m, y - 1 - m * 0.7, L[2])
                self.c.set(x + 1 + m, y - 1 - m * 0.7, L[1])
        tip = ellipse(x + 0.5, yb - h - 4, 2.2, 5)
        self.put(tip, [L[0], L[1], self.R("sand")[1], self.R("sand")[3]], cast=False)

    def totem(self, x, yb, h=120, w=18, hide=True):
        """Тотем: резной столб с личинами, крылья-доски, череп с рогами наверху, сбоку шкура."""
        W, B, Hd, D = self.R("wood"), self.R("bone"), self.R("hide"), self.R("dark")
        self.dark(x + w // 2 + 1, yb - h + 6, x + w // 2 + 5, yb, 1)
        y1 = yb
        seg = 0
        while y1 > yb - h + 6:
            y0 = max(yb - h, y1 - 27)
            ww = w // 2 + (1 if seg % 2 == 0 else -1)
            self.bevel(x - ww, y0, x + ww, y1, W)
            self.noise(x - ww + 1, y0 + 1, x + ww - 1, y1 - 1, W, 0.05)
            self.rect(x - ww, y1, x + ww, y1, W[0])
            cy = (y0 + y1) // 2
            if y1 - y0 > 18:
                # Личина: глаза-кольца, нос клином, пасть с зубами, полосы краски.
                for sx in (x - 5, x + 3):
                    self.rect(sx, cy - 6, sx + 2, cy - 4, B[2])
                    self.c.set(sx + 1, cy - 5, D[0])
                    self.rect(sx - 1, cy - 8, sx + 3, cy - 8, W[0])
                self.rect(x - 1, cy - 4, x, cy + 1, W[3])
                self.rect(x + 1, cy - 4, x + 1, cy + 1, W[0])
                self.rect(x - 6, cy + 4, x + 6, cy + 7, D[0])
                for tx in range(x - 5, x + 6, 3):
                    self.rect(tx, cy + 4, tx + 1, cy + 5, B[2])
                col = (Hd[2], self.R("deep")[2], self.R("lava")[2])[seg % 3]
                self.rect(x - ww + 1, y0 + 2, x + ww - 1, y0 + 3, col)
            if seg == 2:
                for sgn in (-1, 1):
                    wing = poly([(x + sgn * ww, cy - 5), (x + sgn * (ww + 20), cy - 11), (x + sgn * (ww + 22), cy - 3),
                                 (x + sgn * ww, cy + 4)])
                    self.put(wing, W, soft=False)
                    for k in range(4):
                        self.line((x + sgn * (ww + 4 + k * 5), cy - 6 - k), (x + sgn * (ww + 4 + k * 5), cy + 1 - k * 0.6),
                                  (Hd[2], self.R("deep")[2])[k % 2], 0.6)
            y1 = y0 - 1
            seg += 1
        top = yb - h
        skull = ellipse(x, top - 7, 9, 7) | poly([(x - 6, top - 3), (x + 6, top - 3), (x + 4, top + 5), (x - 4, top + 5)])
        for sgn in (-1, 1):
            skull |= capsule((x + sgn * 7, top - 9), (x + sgn * 14, top - 14), 2.2, 1.6) \
                | capsule((x + sgn * 14, top - 14), (x + sgn * 15, top - 22), 1.6, 0.6)
        self.put(skull, B, soft=True)
        for sx in (x - 6, x + 3):
            self.rect(sx, top - 9, sx + 3, top - 6, D[0])
        self.rect(x - 1, top - 3, x, top - 1, D[0])
        for tx in range(x - 3, x + 4, 2):
            self.c.set(tx, top + 4, D[0])
        if hide:
            # Шкура на жерди сбоку.
            self.line((x + w // 2, yb - h + 34), (x + w // 2 + 30, yb - h + 30), W[2], 1.2)
            S = poly([(x + w // 2 + 4, yb - h + 34), (x + w // 2 + 29, yb - h + 31), (x + w // 2 + 31, yb - h + 62),
                      (x + w // 2 + 24, yb - h + 70), (x + w // 2 + 17, yb - h + 61), (x + w // 2 + 10, yb - h + 72),
                      (x + w // 2 + 5, yb - h + 60)])
            self.put(S, Hd, soft=True)
            for (px, py) in ((x + w // 2 + 12, yb - h + 42), (x + w // 2 + 22, yb - h + 50), (x + w // 2 + 14, yb - h + 56),
                             (x + w // 2 + 24, yb - h + 38)):
                for q in ellipse(px, py, 2.6, 2.0) & S:
                    self.c.set(q[0], q[1], D[2])

    def ribs(self, x0, yb, n=6, step=30, h=150):
        """Рёбра ящера дугами из земли и хребет поверху: дальний ряд темнее, ближний светлый."""
        B = self.R("bone")
        far = [B[0], B[0], B[1], B[2]]
        for layer, ramp in ((0, far), (1, B)):
            for i in range(n):
                bx = x0 + i * step + (0 if layer else 13)
                hh = h * (1.0 - 0.35 * abs(i - (n - 1) * 0.4) / n) - (0 if layer else 10)
                rx = 30.0 if layer else 24.0
                pts = []
                for k in range(19):
                    a = math.pi * (1.0 + 0.62 * k / 18.0)
                    pts.append((bx + rx + math.cos(a) * rx, yb + math.sin(a) * hh))
                rib = set()
                for k in range(18):
                    r0 = (4.6 if layer else 3.6) * (1.0 - k / 26.0)
                    rib |= capsule(pts[k], pts[k + 1], r0, r0 * 0.97)
                if layer:
                    self.dark(bx + 5, int(yb - hh * 0.7), bx + 8, yb, 1, dither=True)
                self.put({q for q in rib if q[1] <= yb}, ramp, soft=True, cast=bool(layer))
                if layer:
                    for k in range(3, 16, 4):
                        self.c.set(pts[k][0] + 1, pts[k][1], B[1])
                        self.c.set(pts[k][0] + 1, pts[k][1] + 1, B[1])
        # Хребет: позвонки с отростками над вершинами рёбер.
        for i in range(n * 2 + 1):
            vx = x0 + 28 + i * step * 0.5
            vy = yb - h * (1.0 - 0.35 * abs(i * 0.5 - (n - 1) * 0.4) / n) + 2
            v = ellipse(vx, vy, 7.5, 5.5) | poly([(vx - 3, vy - 4), (vx + 1, vy - 13), (vx + 4, vy - 4)])
            self.put(v, B, soft=True)

    def rex_skull(self, x, yb, k=1.0):
        """Череп тираннозавра на земле мордой влево: свод, глазница, окна, челюсти с зубами."""
        B, D = self.R("bone"), self.R("dark")

        def q(dx, dy):
            return (x + dx * k, yb - dy * k)

        self.dark(int(x - 4), yb - 3, int(x + 78 * k), yb, 1, dither=True)
        low = poly([q(6, 12), q(52, 16), q(66, 10), (x + 64 * k, yb), (x + 10 * k, yb), q(2, 6)])
        self.put(low, [B[0], B[1], B[2], B[2]], soft=True, cast=False)
        up = poly([q(0, 22), q(4, 34), q(22, 44), q(44, 52), q(62, 50), q(74, 38), q(72, 22), q(60, 16), q(52, 20),
                   q(10, 18)])
        self.put(up, B, soft=True)
        for (cx_, cy_, rx, ry, a) in ((54, 38, 6.5, 6.0, 0), (38, 34, 7.5, 5.5, 15), (65, 28, 4.5, 6.5, 0), (10, 30, 3.0, 2.2, 20)):
            c0 = q(cx_, cy_)
            hole = ellipse(c0[0], c0[1], rx * k, ry * k, a)
            for (px, py) in hole:
                self.c.set(px, py, D[0] if (px - 2, py - 2) in hole else D[2])
        for i in range(9):
            t0 = q(6 + i * 5.2, 19)
            ln = (6.5 if i % 2 == 0 else 5.0) * k
            for (px, py) in poly([(t0[0] - 2 * k, t0[1] - 1), (t0[0] + 2 * k, t0[1] - 1), (t0[0], t0[1] + ln)]):
                self.c.set(px, py, B[3] if px <= t0[0] else B[1])
        for i in range(7):
            t0 = q(10 + i * 5.6, 12)
            for (px, py) in poly([(t0[0] - 1.6 * k, t0[1] + 1), (t0[0] + 1.6 * k, t0[1] + 1), (t0[0], t0[1] - 4 * k)]):
                self.c.set(px, py, B[2] if px <= t0[0] else B[1])
        # Трещины и швы.
        for (a, b_) in ((q(22, 43), q(28, 36)), (q(28, 36), q(26, 30)), (q(46, 50), q(46, 44)), (q(70, 36), q(64, 36)),
                        (q(30, 14), q(44, 15)), (q(14, 24), q(26, 26))):
            self.line(a, b_, B[1], 0.4)

    def nest(self, x, yb, w=34, eggs=3):
        """Гнездо: плетёнка из прутьев, внутри пятнистые яйца."""
        W, E, S_ = self.R("wood"), self.R("egg"), self.R("sand")
        for k in range(eggs):
            ex = x - (eggs - 1) * 4.5 + k * 9
            egg = ellipse(ex, yb - 11 - (k % 2), 4.6, 6.4, (k - 1) * 12)
            self.put(egg, E, soft=True)
            for (dx, dy) in ((-1, -3), (2, -1), (-2, 1), (1, 3), (0, -6)):
                if (ex + dx, yb - 11 + dy) != (ex, yb):
                    self.c.set(ex + dx, yb - 11 - (k % 2) + dy, self.R("deep")[2])
        bowl = {q for q in ellipse(x, yb - 4, w * 0.5, 7.5) if q[1] >= yb - 9 and q[1] <= yb}
        self.put(bowl, W, soft=True)
        r = self.rng
        for _ in range(int(w * 1.3)):
            px = r.randint(int(x - w * 0.5), int(x + w * 0.5))
            py = r.randint(yb - 9, yb - 1)
            if (px, py) in bowl:
                dx = r.choice((-3, -2, 2, 3))
                self.line((px, py), (px + dx, py - r.choice((0, 1, 2))), r.choice((W[1], W[3], S_[1], S_[2])), 0.4)
        for sx in (int(x - w * 0.5) - 2, int(x + w * 0.5) + 2):
            self.line((sx, yb - 7), (sx + (3 if sx > x else -3), yb - 12), W[2], 0.5)

    def tent(self, x, yb, w, h):
        """Шатёр: три жерди, шкура с пятнами натянута конусом, тёмный вход."""
        W, Hd, D = self.R("wood"), self.R("hide"), self.R("dark")
        ax, ay = x + w // 2, yb - h
        self.dark(x + w // 2, yb - h + 12, x + w + 6, yb, 1, dither=True)
        for dx in (-8, 0, 8):
            self.line((ax - dx * 0.2, ay + 8), (ax + dx, ay - 12), W[2], 1.1)
        left = poly([(ax, ay), (x, yb), (ax - 6, yb)])
        right = poly([(ax, ay), (ax - 6, yb), (x + w, yb)])
        self.put(left, Hd, soft=True, cast=False)
        self.put(right - left, [Hd[0], Hd[0], Hd[1], Hd[2]], soft=True, cast=False)
        r = self.rng
        for _ in range(int(w * h / 150)):
            px, py = r.randint(x + 4, x + w - 4), r.randint(yb - h + 14, yb - 4)
            for q in ellipse(px, py, r.uniform(1.6, 3.4), r.uniform(1.2, 2.4)) & (left | right):
                self.c.set(q[0], q[1], D[2] if q in left else D[1])
        door = poly([(ax - 5, yb - h * 0.52), (ax - 16, yb), (ax + 4, yb)])
        for (px, py) in door:
            self.c.set(px, py, D[0] if (px + py) % 2 or px < ax - 8 else D[1])
        # Шов и костяные застёжки над входом.
        for k in range(5):
            self.c.set(ax - 4 - k * 0.2, yb - h * 0.52 - 5 - k * 8, self.R("bone")[2])
            self.c.set(ax - 3 - k * 0.2, yb - h * 0.52 - 5 - k * 8, self.R("bone")[1])
        for sx in range(x + 2, x + w - 2, 14):
            if not (ax - 18 < sx < ax + 6):
                self.put(ellipse(sx, yb - 2, 5, 3.4), self.R("rock"), soft=True)

    # Предметы у стены -------------------------------------------------------------------------

    def basket(self, x, y, w=20, h=30):
        """Плетёная корзина: бочонок с плетением, обод, сверху плоды."""
        S_, W, Hd = self.R("sand"), self.R("wood"), self.R("hide")
        for k, dx in enumerate((-5, 1, 6)):
            self.put(ellipse(x + dx, y - h - 2 - (k % 2) * 2, 4.2, 4.0), (Hd, self.R("lava"), self.R("leaf"))[k], soft=True)
        S = set()
        for yy in range(y - h, y + 1):
            k = (y - yy) / float(h)
            half = w * 0.5 * (0.78 + 0.26 * math.sin(k * 2.6 + 0.3))
            for xx in range(int(x - half), int(x + half) + 1):
                S.add((xx, yy))
        self.put(S, S_, soft=True)
        for (xx, yy) in S:
            cell = ((xx - int(x)) // 3 + (yy - y) // 3) % 2
            e = self.c.get(xx, yy)
            if cell and e in (S_[2], S_[3]):
                self.c.set(xx, yy, S_[1] if e == S_[2] else S_[2])
            if (yy - y) % 3 == 0 and e == S_[2]:
                self.c.set(xx, yy, S_[1])
        for hy in (y - h, y - h + 1, y - 1):
            for xx in range(int(x - w * 0.42), int(x + w * 0.42) + 1):
                if (xx, hy) in S:
                    self.c.set(xx, hy, W[2] if hy != y - h else W[3])

    def lava_rock(self, x, y, w=14, h=22):
        """Глыба лавы: тёмный камень с раскалёнными трещинами и свечением у подножия."""
        R_, Lv = self.R("rock"), self.R("lava")
        S = poly([(x - w * 0.5, y), (x - w * 0.62, y - h * 0.45), (x - w * 0.2, y - h), (x + w * 0.3, y - h * 0.9),
                  (x + w * 0.62, y - h * 0.4), (x + w * 0.5, y)])
        self.put(S, [self.R("dark")[1], R_[0], R_[1], R_[2]], soft=True)
        r = random.Random(int(x) * 7 + w)
        for _ in range(3):
            px, py = x + r.uniform(-w * 0.3, w * 0.3), y - h * 0.85
            while py < y - 1:
                if (int(round(px)), int(round(py))) in S:
                    self.c.set(px, py, Lv[2] if r.random() < 0.6 else Lv[1])
                    self.c.set(px + 1, py, Lv[0])
                py += 1
                px += r.choice((-1, 0, 0, 1))
        for xx in range(int(x - w * 0.6), int(x + w * 0.6) + 1):
            if xx % 2 == 0:
                self.c.set(xx, y + 1, Lv[1])

    def bones(self, x, y, w=30):
        """Гигантская кость на подпорке из камней, под ней мелкие кости."""
        B = self.R("bone")
        self.put(ellipse(x + 5, y - 3, 7, 4.5) | ellipse(x + w - 4, y - 4, 6, 5), self.R("rock"), soft=True)
        a, b_ = (x + 1, y - 9), (x + w, y - 19)
        big = capsule(a, b_, 3.4, 3.0)
        for (e, sg) in ((a, -1), (b_, 1)):
            big |= ellipse(e[0] + sg * 2, e[1] - 3, 4.2, 3.6) | ellipse(e[0] + sg * 2.5, e[1] + 3, 4.0, 3.6)
        self.dark(x + 3, y - 6, x + w, y - 4, 1, dither=True)
        self.put(big, B, soft=True)
        for k in range(3):
            self.c.set(x + 8 + k * 6, y - 12 - k * 2, B[1])
        self.line((x + 12, y), (x + 22, y - 2), B[2], 0.8)
        self.line((x + 14, y - 2), (x + 19, y + 1), B[1], 0.7)


def build_street():
    """Стойбище той же ширины и с теми же строками пола, что улица пиратов: стена до `WALL_Y`,
    тропа с плоскими камнями до `CURB_Y`, уступ из лавового камня, глина от `ROAD_Y`."""
    st = Camp()
    c, rng = st.c, st.rng
    R_, Cl, B, L, D, Lv = st.R("rock"), st.R("clay"), st.R("bone"), st.R("leaf"), st.R("dark"), st.R("lava")
    x = 0
    modules = [("cave", 320), ("hut", 288), ("jungle", 352), ("ribs", 256), ("nest", 256), ("lava", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        if kind == "cave":
            st.cliff(x0, 32, x1, WALL_Y)
            st.cave(x0 + 96, 84, 128)
            st.painting(x0 + 188, 96, "mammoth")
            st.painting(x0 + 226, 100, "hunter")
            st.painting(x0 + 240, 104, "hunter")
            st.painting(x0 + 204, 138, "hand")
            st.painting(x0 + 222, 142, "hand")
            st.painting(x0 + 26, 70, "sun")
            st.painting(x0 + 262, 62, "dino")
            st.torch(x0 + 178, 150)
            st.stretched(x0 + 252, 132, 56, 72)
            st.fern(x0 + 12, WALL_Y, 6, 22)
        elif kind == "hut":
            st.cliff(x0, 32, x1, WALL_Y, "clay", 30)
            st.painting(x0 + 244, 60, "sun")
            st.hut(x0 + 108, 196, 150)
            st.rack(x0 + 222, 128, 52, 100)
            st.horsetail(x0 + 6, WALL_Y, 60)
            st.horsetail(x0 + 14, WALL_Y, 44)
        elif kind == "jungle":
            # Прогал: дымка, вулкан с лавой и дымом, шея зауропода, три слоя зелени.
            Hz, Dp = st.R("haze"), st.R("deep")
            for yy in range(32, WALL_Y + 1):
                for xx in range(x0, x1 + 1):
                    k = (yy - 32) / 110.0
                    t = 0 if k < 0.16 else 1 if k < 0.42 or (k < 0.52 and (xx + yy) % 2) else 2 if k < 0.9 or (xx + yy) % 2 else 3
                    c.set(xx, yy, Hz[t])
            vx = x0 + 232
            vol = poly([(vx - 96, 170), (vx - 34, 78), (vx - 22, 62), (vx - 10, 66), (vx + 2, 58), (vx + 14, 64), (vx + 30, 84),
                        (vx + 100, 170)])
            for (px, py) in vol:
                if x0 <= px <= x1:
                    d = (px - vx) * 0.6 + (py - 60) * 0.25
                    c.set(px, py, Dp[1] if d < -6 or (d < 4 and (px + py) % 2) else Dp[0])
            for (a, b_) in (((vx - 4, 60), (vx - 12, 88)), ((vx - 12, 88), (vx - 8, 112)), ((vx + 6, 60), (vx + 14, 80)),
                            ((vx + 14, 80), (vx + 30, 104)), ((vx - 8, 112), (vx - 20, 140))):
                st.line(a, b_, Lv[1], 1.0)
                st.line(a, b_, Lv[2], 0.3)
            for (sx, sy, sr) in ((vx - 2, 50, 8), (vx + 8, 42, 9), (vx + 22, 36, 8), (vx + 38, 34, 6)):
                for (px, py) in ellipse(sx, sy, sr, sr * 0.7):
                    if py >= 32 and x0 <= px <= x1:
                        c.set(px, py, Hz[3] if (px - sx) + (py - sy) < 0 else Hz[1])
            # Зауропод: шея дугой над лесом, маленькая голова.
            nk = [(x0 + 60, 172), (x0 + 70, 132), (x0 + 82, 100), (x0 + 98, 82), (x0 + 112, 80)]
            S = set()
            for k in range(4):
                S |= capsule(nk[k], nk[k + 1], 9 - k * 1.8, 7.2 - k * 1.8)
            S |= ellipse(x0 + 116, 81, 7, 3.6) | ellipse(x0 + 34, 176, 34, 18)
            for (px, py) in S:
                if x0 <= px <= x1:
                    c.set(px, py, Dp[2] if (px - 2, py - 2) not in S else Dp[1])
            c.set(x0 + 117, 80, D[0])
            # Дальний и средний лес: кроны буграми.
            for (base, amp, ramp, shift) in ((150, 9, [Dp[0], Dp[1]], 0.0), (176, 12, [L[0], L[1]], 2.0)):
                for xx in range(x0, x1 + 1):
                    top = base - abs(math.sin(xx * 0.09 + shift)) * amp - math.sin(xx * 0.31 + shift) * 3
                    for yy in range(int(top), WALL_Y + 1):
                        c.set(xx, yy, ramp[1] if yy - top < 3 or (yy - top < 9 and (xx + yy) % 2) else ramp[0])
                for xx in range(x0 + 6, x1, 17):
                    top = base - abs(math.sin(xx * 0.09 + shift)) * amp
                    st.frond(xx, top + 1, -150, 9, 0.6, "deep" if base < 160 else "leaf", 0.6)
                    st.frond(xx, top + 1, -30, 9, 0.6, "deep" if base < 160 else "leaf", 0.6)
            # Скальные косяки по краям прогала.
            st.cliff(x0, 32, x0 + 26, WALL_Y)
            st.cliff(x1 - 30, 32, x1, WALL_Y)
            for (ex, sg) in ((x0 + 27, 1), (x1 - 31, -1)):
                for yy in range(32, WALL_Y + 1):
                    jag = int(math.sin(yy * 0.23) * 3 + math.sin(yy * 0.9) * 1.2 + 3)
                    for k in range(jag):
                        c.set(ex + sg * k, yy, R_[1 if sg > 0 else 2])
                    c.set(ex + sg * jag, yy, R_[0])
            st.cycad(x0 + 78, WALL_Y, 96, 15)
            st.cycad(x0 + 276, WALL_Y, 70, 13)
            st.cycad(x0 + 176, WALL_Y, 44, 12)
            for hx, hh in ((x0 + 122, 74), (x0 + 132, 52), (x0 + 228, 60), (x0 + 310, 46)):
                st.horsetail(hx, WALL_Y, hh)
            for fx_, n_, ln in ((x0 + 40, 7, 28), (x0 + 146, 6, 22), (x0 + 214, 7, 26), (x0 + 252, 6, 20), (x0 + 318, 6, 22)):
                st.fern(fx_, WALL_Y, n_, ln)
        elif kind == "ribs":
            st.cliff(x0, 32, x1, WALL_Y)
            st.painting(x0 + 214, 70, "hand")
            st.painting(x0 + 232, 76, "hand")
            st.ribs(x0 + 6, WALL_Y, 5, 30, 152)
            st.rex_skull(x0 + 168, WALL_Y, 1.05)
            st.fern(x0 + 250, WALL_Y, 5, 18)
            st.torch(x0 + 226, 128)
        elif kind == "nest":
            st.cliff(x0, 32, x1, WALL_Y, "clay", 30)
            # Каменный уступ с гнездом и скорлупой.
            st.dark(x0 + 20, 134, x0 + 96, 142, 1)
            st.bevel(x0 + 14, 126, x0 + 92, 134, R_)
            st.noise(x0 + 15, 127, x0 + 91, 133, R_, 0.08)
            st.nest(x0 + 52, 126, 44, 3)
            st.painting(x0 + 40, 66, "dino")
            st.painting(x0 + 34, 164, "hunter")
            st.painting(x0 + 50, 168, "hunter")
            st.tent(x0 + 108, WALL_Y, 96, 136)
            st.totem(x0 + 226, WALL_Y, 128, 18)
            st.horsetail(x0 + 100, WALL_Y, 40)
        elif kind == "lava":
            st.cliff(x0, 32, x1, WALL_Y)
            # Расщелина с лавопадом: тёмные стенки, раскалённая струя, озерцо и жар на краях.
            mid = (x0 + x1) // 2
            gap = set()
            for yy in range(32, WALL_Y + 1):
                half = 26 + math.sin(yy * 0.11) * 6 + math.sin(yy * 0.47) * 2 + (yy - 32) * 0.05
                off = math.sin(yy * 0.06) * 6
                for xx in range(int(mid + off - half), int(mid + off + half) + 1):
                    gap.add((xx, yy))
            for (xx, yy) in gap:
                edge = (xx - 5, yy) not in gap or (xx + 5, yy) not in gap
                c.set(xx, yy, D[2] if edge and (xx + yy) % 2 else D[1] if edge or (xx * 3 + yy) % 5 == 0 else D[0])
            for yy in range(32, WALL_Y - 8):
                cx_ = mid + math.sin(yy * 0.06) * 6 + math.sin(yy * 0.35) * 1.5
                wd = 5 + math.sin(yy * 0.21) * 1.5
                for xx in range(int(cx_ - wd - 2), int(cx_ + wd + 3)):
                    d = abs(xx - cx_)
                    if d < wd * 0.45:
                        c.set(xx, yy, Lv[3] if (yy // 3 + xx) % 4 else Lv[2])
                    elif d < wd:
                        c.set(xx, yy, Lv[2] if (yy + xx) % 3 else Lv[1])
                    elif (xx + yy) % 2 == 0:
                        c.set(xx, yy, Lv[0])
            pool = ellipse(mid + 2, WALL_Y - 5, 34, 8) & gap
            for (xx, yy) in pool:
                d = math.hypot((xx - mid - 2) / 34.0, (yy - WALL_Y + 5) / 8.0)
                c.set(xx, yy, Lv[3] if d < 0.3 else Lv[2] if d < 0.62 or (xx + yy) % 2 == 0 and d < 0.8 else Lv[1])
            # Жар на кромках расщелины.
            hot = set()
            for (xx, yy) in gap:
                for dx in (-9, -6, -3, 3, 6, 9):
                    if (xx + dx, yy) not in gap:
                        hot.add((xx + dx, yy))
            for (xx, yy) in hot:
                e = c.get(xx, yy)
                if e in (R_[0], R_[1]) or (e == R_[2] and (xx + yy) % 2 == 0 and yy > 120):
                    c.set(xx, yy, Lv[0] if e != R_[2] or yy > 180 else Cl[1])
            st.glow(mid, WALL_Y - 30, 70, 60)
            st.lava_rock(x0 + 30, WALL_Y, 26, 34)
            st.lava_rock(x1 - 26, WALL_Y, 22, 26)
            st.horsetail(x0 + 8, WALL_Y, 36)
        st.overhang(x0, x1, vines=(kind != "jungle"))
        x += w
    # Тень у подножия стены.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0) and e not in Lv:
                c.set(xx, yy, st.p.darker.get(e, e))
    # Тропа у стены: утоптанный песок, три ряда плоских камней, галька и травинки.
    Sd = st.R("sand")
    st.rect(0, WALL_Y + 1, SW - 1, CURB_Y - 1, Sd[1])
    for yy in range(WALL_Y + 1, CURB_Y):
        for xx in range(SW):
            v = math.sin(xx * 0.05 + yy * 0.3) + math.sin(xx * 0.013 + yy * 0.11) * 0.8
            if v > 0.5 and (xx + yy) % 2 == 0:
                c.set(xx, yy, Sd[2])
            elif v < -1.0 and (xx + yy) % 2 == 0:
                c.set(xx, yy, Sd[0])
    st.noise(0, WALL_Y + 1, SW - 1, CURB_Y - 1, Sd, 0.04)
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        xx = -((ri * 23) % 48)
        while xx < SW:
            wd = rng.randint(34, 50)
            if rng.random() < 0.82:
                cx_, cy_ = xx + wd * 0.5, y0 + h * 0.5
                S = ellipse(cx_, cy_, wd * 0.46, h * 0.42, rng.uniform(-4, 4))
                S |= ellipse(cx_ + rng.uniform(-6, 6), cy_ + rng.uniform(-1, 1), wd * 0.34, h * 0.46)
                S = {q for q in S if y0 <= q[1] < min(y0 + h, CURB_Y)}
                ramp = R_ if rng.random() < 0.7 else [R_[0], R_[1], R_[1], R_[2]]
                st.put(S, ramp, soft=True)
                for _ in range(2):
                    px, py = int(cx_ + rng.uniform(-wd * 0.3, wd * 0.3)), int(cy_ + rng.uniform(-2, 2))
                    if (px, py) in S and (px + 3, py + 1) in S:
                        c.set(px, py, R_[0])
                        c.set(px + 1, py + 1, R_[0])
                        c.set(px + 2, py + 1, R_[0])
            else:
                # Между камнями кость или пучок травы.
                if rng.random() < 0.5:
                    st.line((xx + 10, y0 + h // 2), (xx + 22, y0 + h // 2 - 2), B[2], 0.8)
                    st.put(ellipse(xx + 9, y0 + h // 2, 1.8, 1.8) | ellipse(xx + 23, y0 + h // 2 - 2, 1.8, 1.8), B, cast=False)
                else:
                    for k in range(-3, 4):
                        st.line((xx + 16, y0 + h - 4), (xx + 16 + k * 2, y0 + h - 10 - (3 - abs(k))), L[2 if k < 1 else 1], 0.4)
            xx += wd + rng.randint(2, 8)
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Уступ: кромка лавового камня глыбами, в швах кости.
    for xx in range(SW):
        c.set(xx, CURB_Y, R_[3])
        c.set(xx, CURB_Y + 1, R_[2])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, R_[1] if yy < ROAD_Y - 2 else R_[0])
    xx = 0
    while xx < SW:
        wd = rng.randint(18, 34)
        c.set(xx, CURB_Y, R_[1])
        for yy in range(CURB_Y + 1, ROAD_Y):
            c.set(xx + (1 if yy % 4 == 0 else 0), yy, R_[0])
            c.set(xx + 1 + (1 if yy % 4 == 0 else 0), yy, R_[2])
        if rng.random() < 0.22:
            st.line((xx + 5, CURB_Y + 5), (xx + wd - 6, CURB_Y + 4), B[2], 0.8)
            c.set(xx + 4, CURB_Y + 4, B[2])
            c.set(xx + 4, CURB_Y + 6, B[1])
        elif rng.random() < 0.3:
            for k in range(3):
                c.set(xx + 6 + k * 4, CURB_Y + 3 + k % 2, L[1])
                c.set(xx + 7 + k * 4, CURB_Y + 2 + k % 2, L[2])
        xx += wd
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, D[0])
    # Площадка: растрескавшаяся красная глина плитами, ряды к зрителю выше.
    Dk = st.R("dirt")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Dk[2])
    for yy in range(ROAD_Y + 2, SH):
        for xx in range(SW):
            v = math.sin(xx * 0.031 + yy * 0.17) + math.sin(xx * 0.008 - yy * 0.05) * 0.9
            if v > 1.0 and (xx + yy) % 2 == 0:
                c.set(xx, yy, Dk[3])
            elif v < -0.7 and (xx + yy) % 2 == 0:
                c.set(xx, yy, Dk[1])
    st.noise(0, ROAD_Y + 2, SW - 1, SH - 1, Dk, 0.03)
    y = ROAD_Y + 2
    h = 14
    row = 0
    seams = []
    while y < SH:
        # Горизонтальная трещина ряда: волной, с бликом по нижней кромке.
        for xx in range(SW):
            yy = y + int(round(math.sin(xx * 0.06 + row * 1.7) * 1.6 + math.sin(xx * 0.23 + row) * 0.8))
            if ROAD_Y + 2 <= yy < SH:
                c.set(xx, yy, Dk[0])
                if yy + 1 < SH:
                    c.set(xx, yy + 1, Dk[3] if xx % 5 else Dk[2])
                if yy - 1 > ROAD_Y + 1 and xx % 2:
                    c.set(xx, yy - 1, Dk[1])
        pw = 52 + row * 6
        xx = -((row * 19) % pw)
        while xx < SW:
            sx = float(xx + rng.randint(-8, 8))
            for yy in range(y + 1, min(y + h, SH)):
                c.set(sx, yy, Dk[0])
                c.set(sx + 1, yy, Dk[3] if yy % 3 else Dk[2])
                sx += rng.choice((-1, 0, 0, 0, 1))
            # Мелкие трещинки от шва внутрь плиты.
            if rng.random() < 0.5:
                bx, by = xx + rng.randint(8, pw - 8), y + rng.randint(3, max(4, h - 4))
                for k in range(rng.randint(4, 9)):
                    c.set(bx + k, by + (k // 3), Dk[1])
            if rng.random() < 0.22:
                px, py = xx + rng.randint(6, pw - 6), y + rng.randint(3, max(4, h - 3))
                if py < SH - 3:
                    st.put(ellipse(px, py, rng.uniform(2.0, 3.6), rng.uniform(1.4, 2.2)), R_, soft=False)
            xx += pw
        seams.append(y)
        y += h
        h += 3
        row += 1
    # Следы трёхпалых лап наискось через площадку.
    for (fx_, fy_, sg) in ((150, 326, 1), (196, 352, -1), (250, 384, 1), (930, 322, -1), (980, 350, 1), (1040, 386, -1),
                           (1470, 330, 1), (1520, 362, -1)):
        k = 0.8 + (fy_ - ROAD_Y) / 110.0
        pr = ellipse(fx_, fy_, 4.5 * k, 2.6 * k)
        for dx in (-7, 0, 7):
            pr |= capsule((fx_ + dx * 0.4 * k, fy_ - 1 * k), (fx_ + dx * k + sg * 3 * k, fy_ - 7 * k), 1.9 * k, 1.0 * k)
        for (px, py) in pr:
            if ROAD_Y + 2 < py < SH:
                rim = (px + 1, py + 1) not in pr
                c.set(px, py, Dk[3] if rim else Dk[0] if (px - 1, py - 1) not in pr else Dk[1])
    # Лужи после дождя: бирюзовая вода с бликами.
    Dp = st.R("deep")
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            if c.get(px, py) is None:
                continue
            rim = (px, py - 1) not in P_ or (px - 1, py) not in P_
            c.set(px, py, Dk[0] if rim else Dp[2] if (px + py * 2) % 9 < 2 else Dp[1])
        for k in range(px0 - 30, px0 + 30, 9):
            c.set(k, 369, Dp[3])
            c.set(k + 1, 369, Dp[3])
            c.set(k + 3, 374, Dp[2])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("can", 20), ("can", 44), ("box", 290), ("can2", 600), ("can2", 618), ("coil", 680),
                       ("box", 870), ("box", 898), ("can", 1150), ("coil", 1400), ("can", 1590)):
        yb = WALL_Y + 8
        if kind == "can":
            st.dark(px - 8, yb - 1, px + 13, yb + 1, 1)
            st.basket(px, yb)
        elif kind == "can2":
            st.lava_rock(px, yb)
        elif kind == "box":
            st.bones(px, yb)
        else:
            st.dark(px - 14, yb, px + 18, yb + 1, 1)
            st.nest(px, yb, 30, 2)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки цвета лавы и кости, волна бирюзовая, пыль красной глиной;
    стрелка «вперёд» зелёная, чтобы не терялась на тёплой глине и скале."""
    p = Pal(OUTLINE)
    p.add("white", [0xD8C8A0, 0xF4EEDA, 0xFFF8E8, 0xFFFFFF])
    if go:
        p.add("gold", [0x1E5A2C, 0x3C9A3A, 0x86D84C, 0xE0FFA0])
    else:
        p.add("gold", [0xB8401C, 0xEC5E24, 0xF4CC52, 0xFFF4B0])
    p.add("blue", [0x1C465A, 0x2C8084, 0x7CCCB4, 0xD8FFF0])
    p.add("dust", [0x7C3422, 0xB0684A, 0xD8A07A, 0xF0D0B0])
    return p.colors


def fx():
    """Эффекты: формы и кадры общие с пиратами (демка берёт те же размеры), цвета свои."""
    out = {}
    for key, (canvas, _) in pb.fx().items():
        out[key] = (canvas, fx_colors(go=(key == "brawl_go")))
    return out


def sprites_own():
    """Все ленты битемапа → (холст, палитра)."""
    out = fighters()
    out.update(faces())
    out["brawl_street"] = build_street()
    out.update(fx())
    return out


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import dinosaurs16
        dinosaurs16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own(), scale=1, max_w=FW * 12)
