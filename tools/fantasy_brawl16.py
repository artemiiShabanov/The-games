# -*- coding: utf-8 -*-
"""Набор «Фэнтези» для битемапа × 16/32-bit (#137): зеркало `pixel_brawl16.py` и `space_brawl16.py`.
Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты из `pixel_brawl16`
как есть (демка `fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и улица свои.

Бойцы: герой это юный маг основы (`fantasy16.py`): синяя мантия до колен с золотой каймой,
остроконечная шляпа с широкими полями и загнутым назад кончиком, посох с бирюзовым кристаллом
за спиной на перевязи; громила это тролль: серо-синяя каменная шкура, мох на загривке, нос
картошкой, клыки из нижней челюсти, меховая повязка, босые лапы; враг с ножом это гоблин-шаман:
зелёная кожа, ухо шире головы, перья в повязке, полосатое пончо, в ближней руке погремушка с
черепом; босс это тёмный чародей: рогатая золотая корона, длинная белая борода клином, горящие
глаза, чёрно-лиловая мантия с золотой каймой и амулетом. Улица это тропа под великим деревом:
жилой ствол с круглой дверью и окнами, лавка зелий, рунная арка портала, зал гильдии со
знамёнами, грот с кристаллами, просвет с летающими островами; у стены рунные плиты во мху,
бордюр тёсаным камнем с рунами, дальше каменная тропа.

    python3 tools/fantasy_brawl16.py --preview out.png   # листы: out.png, out_b.png, out_c.png
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

# Обводка основы «Фэнтези» (`fantasy16.PALETTE[K]`).
OUTLINE = 0x15101E

# Рампы от цветов основы: мантия (SEA, тень NAVY), золото (GOLD, тень BRASS), кожа (SKIN),
# кристалл (AQUA, блик SKY), дерево (METAL, тень DARK), зелень гоблинов (TAN), фиолетовый
# гильдии (VIOLET, тень PLUM).
ROBE = [0x1A1848, 0x282466, 0x3A5ACC, 0x7C9CF4]
GOLD = [0x7A4E1C, 0xC2862C, 0xF6D058, 0xFFF4B8]
SKIN = [0x8A5440, 0xC08A66, 0xF2C89A, 0xFFE8CC]
CRYSTAL = [0x1E6A7A, 0x2AA09A, 0x3AD4C2, 0xC8F8EC]
WOOD = [0x2E1C24, 0x482E36, 0x9A643C, 0xC8925A]
GREEN = [0x1E4428, 0x3C7A38, 0x6EB44C, 0xA6DC78]
VIOLET = [0x2E1A5A, 0x522E8E, 0x9C5ED8, 0xC89CF4]
BONE = [0x6E6278, 0xA89CA8, 0xE2DAD2, 0xFFFFFF]
EYE = [0x15101E, 0x15101E, 0x2A2238, 0xFFFFFF]


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("robe", ROBE)
    p.add("gold", GOLD)
    p.add("skin", SKIN)
    p.add("crystal", CRYSTAL)
    p.add("wood", WOOD)
    p.add("hose", [0x1C1630, 0x30284E, 0x4A4274, 0x6E66A0])
    p.add("boots", [0x2A161C, 0x4E2A28, 0x7A4A32, 0xA8704A])
    p.add("eye", EYE)
    return Look("mage", p, Body(1.0, 1.12))


def thug_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x26344E, 0x43597A, 0x6A86A4, 0x9CB8CC])
    p.add("belly", [0x43597A, 0x6A86A4, 0x94AEC0, 0xC2D6DE])
    p.add("moss", [0x1E4428, 0x34703A, 0x5EA448, 0x9AD470])
    p.add("fur", [0x2E1C24, 0x52342E, 0x805438, 0xB0804E])
    p.add("bone", BONE)
    p.add("eye", [0x15101E, 0x6A3A10, 0xF6D058, 0xFFF4B8])
    return Look("troll", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("skin", GREEN)
    p.add("poncho", VIOLET)
    p.add("gold", GOLD)
    p.add("red", [0x5A1630, 0x9A2A44, 0xDC465A, 0xFF8C8C])
    p.add("cloth", WOOD)
    p.add("bone", BONE)
    p.add("crystal", CRYSTAL)
    p.add("eye", [0x15101E, 0x7A4E1C, 0xF6D058, 0xFFF4B8])
    return Look("shaman", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("cloak", [0x0E0A1E, 0x1E1838, 0x342C5E, 0x564C90])
    p.add("robe", [0x2E1244, 0x4A2478, 0x7440AC, 0xA474D8])
    p.add("gold", GOLD)
    p.add("skin", [0x322C54, 0x5A5282, 0x847AAC, 0xAAA2CC])
    p.add("beard", [0x6E6890, 0xA8A2C4, 0xDCD8EC, 0xFFFFFF])
    p.add("horn", [0x1E1420, 0x482E36, 0x7C5C58, 0xB49488])
    p.add("glow", [0x7A1030, 0xDC465A, 0xFF8CA0, 0xFFE4EA])
    p.add("boots", [0x0E0A16, 0x1E1626, 0x34283A, 0x524058])
    return Look("warlock", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _dot(c, q, col, dx=0, dy=0):
    c.set(int(round(q[0])) + dx, int(round(q[1])) + dy, col)


def _along(q, o, d):
    return (q[0] - o[0]) * d[0] + (q[1] - o[1]) * d[1]


def _band(S, o, d, t0, t1):
    """Пояс поперёк части: пиксели маски, у которых проекция на ось `d` от точки `o` в [t0, t1]."""
    return {q for q in S if t0 <= _along(q, o, d) <= t1}


def _rattle(c, pal, fist, d, s):
    """Погремушка шамана вдоль предплечья вперёд: палка, череп на конце с бирюзовыми глазницами,
    красное перо на шнурке."""
    perp = (d[1], -d[0])
    tip = add(fist, d, 11.5 * s)
    put(c, pal, capsule(add(fist, d, -2.5), tip, 1.2, 1.0), pal["cloth"], cast=False)
    feather = capsule(add(tip, d, -3.5), add(add(tip, d, -6.5), perp, -5.5), 1.5, 0.7)
    put(c, pal, feather, pal["red"], cast=False)
    skull = ellipse(tip[0], tip[1], 3.3, 3.0) | ellipse(tip[0] + d[0] * 1.6 - perp[0] * 1.4, tip[1] + d[1] * 1.6 - perp[1] * 1.4,
                                                       2.0, 1.8)
    put(c, pal, skull, pal["bone"], cast=False)
    q = add(add(tip, d, 0.6), perp, 0.6)
    _dot(c, q, pal["crystal"][2])
    _dot(c, q, pal["crystal"][3], -1, 0)
    _dot(c, add(q, d, 1.8), pal["bone"][0])


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    fist = add(ha, d, 1.2 * s)
    if kind in ("mage", "warlock"):
        # Рукав колоколом: плечо, раструб к запястью, золотой обшлаг; кулак выглядывает из раструба.
        ramp = pal["robe"] if kind == "mage" else pal["cloak"]
        upper = capsule(sh, el, 4.5 * s * b, 3.9 * s * b) | ellipse(sh[0], sh[1] + 1, 4.9 * s * b, 4.6 * s * b)
        put(c, pal, upper, ramp, far=far, soft=True)
        bell = {q for q in capsule(el, add(ha, d, -2.0 * s), 3.7 * s * b, 5.2 * s) if _along(q, ha, d) <= -0.4 * s}
        put(c, pal, bell, ramp, far=far, soft=True)
        cuff = _band(bell, ha, d, -3.0 * s, 0.0)
        put(c, pal, cuff, pal["gold"], far=far, cast=False)
        if kind == "warlock":
            # Золотой шов оплечья поперёк рукава.
            seam = _band(upper, sh, _unit(sh, el), 4.0 * s, 5.2 * s)
            recolor(c, seam, lambda x, y, e: pal["gold"][1 if far or (x + y) % 3 == 0 else 2])
        elif not far:
            # Золотая звезда-нашивка на плече.
            q = lerp(sh, el, 0.35)
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                _dot(c, q, pal["gold"][3 if (dx, dy) == (0, 0) else 2], dx, dy)
        fs = ellipse(fist[0], fist[1], 3.3 * s, 3.0 * s)
        put(c, pal, fs, pal["skin"], far=far)
        if kind == "warlock":
            # Когти.
            for k in (-1.2, 1.2):
                q = add(add(fist, d, 3.4 * s), (d[1], -d[0]), k * s)
                _dot(c, q, pal["horn"][0])
    elif kind == "troll":
        # Лапа тролля: бугор плеча, предплечье толще к кисти, кожаная обмотка с костью, кулак-валун.
        upper = capsule(sh, el, 5.0 * s * b, 4.2 * s * b) | ellipse(sh[0], sh[1] + 1, 5.4 * s * b, 5.0 * s * b)
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.6 * s * b, 3.8 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
        put(c, pal, upper, pal["skin"], far=far, soft=True)
        fore = capsule(el, ha, 3.9 * s * b, 4.3 * s * b)
        put(c, pal, fore, pal["skin"], far=far)
        wrap = _band(fore, ha, d, -7.0 * s, -2.6 * s)
        put(c, pal, wrap, pal["fur"], far=far, cast=False)
        _dot(c, add(ha, d, -4.8 * s), pal["bone"][1 if far else 3])
        fs = ellipse(fist[0] + d[0], fist[1] + d[1], 4.6 * s, 4.3 * s)
        put(c, pal, fs, pal["skin"], far=far)
        if not far:
            # Костяшки и мох на плече.
            perp = (d[1], -d[0])
            for k in (-2.0, 0.0, 2.0):
                _dot(c, add(add(fist, d, 3.6 * s), perp, k * s), pal["skin"][1])
            for dx, dy in ((-2, -3), (0, -4), (2, -3), (-1, -2), (1, -1), (-3, -1)):
                q = (int(round(sh[0])) + dx, int(round(sh[1])) + dy)
                if q in upper:
                    c.set(q[0], q[1], pal["moss"][2 if (dx + dy) % 2 else 3])
    else:
        # Тонкая рука шамана: край пончо на плече, золотой браслет, в ближней руке погремушка.
        upper = capsule(sh, el, 3.4 * s * b, 2.9 * s * b)
        put(c, pal, upper, pal["skin"], far=far, soft=True)
        fore = capsule(el, ha, 2.9 * s * b, 2.6 * s * b)
        put(c, pal, fore, pal["skin"], far=far)
        put(c, pal, _band(fore, ha, d, -4.4 * s, -2.4 * s), pal["gold"], far=far, cast=False)
        cap = ellipse(sh[0], sh[1], 5.0 * s * b, 3.8 * s * b)
        put(c, pal, cap, pal["poncho"], far=far, soft=True)
        fringe = {q for q in cap if (q[0], q[1] + 1) not in cap and q[0] % 2 == 0}
        recolor(c, fringe, lambda x, y, e: pal["gold"][1 if far else 2])
        fs = ellipse(fist[0], fist[1], 3.1 * s, 2.9 * s)
        if side == "n":
            _rattle(c, pal, fist, d, s)
        put(c, pal, fs, pal["skin"], far=far)


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    if kind in ("mage", "warlock"):
        # Чулки или штаны, сапог с отворотом и острым носком, загнутым вверх.
        pants = "hose" if kind == "mage" else "cloak"
        top_h = (7 if kind == "mage" else 9) * s
        thigh = capsule(hp, kn, 5.6 * s * b, 4.6 * s * b)
        put(c, pal, thigh, pal[pants], far=far, soft=True)
        boot = capsule(add(an, sd, -top_h), an, 4.5 * s * b, 4.0 * s * b)
        foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.4 * s), fwd, 8.0 * s), 3.3 * s, 2.0 * s)
        toe = capsule(add(add(an, sd, 2.2 * s), fwd, 8.0 * s), add(add(an, sd, 0.2 * s), fwd, 10.2 * s), 1.6 * s, 0.9 * s)
        shin = capsule(kn, add(an, sd, -top_h + 1), 4.3 * s * b, 3.8 * s * b)
        put(c, pal, boot | foot | toe, pal["boots"], far=far)
        put(c, pal, shin, pal[pants], far=far)
        cuff = _band(boot | shin, an, sd, -top_h - (6 if kind == "mage" else 1.2) * s, -top_h + 1.6 * s)
        if kind == "mage":
            cuff &= boot
        put(c, pal, cuff, pal["gold"] if kind == "warlock" else [pal["boots"][1], pal["boots"][2], pal["boots"][3],
                                                                  pal["boots"][3]], far=far, cast=False)
        if kind == "warlock":
            _dot(c, add(kn, fwd, 2.4 * s), pal["cloak"][3 if not far else 2])
        elif not far:
            # Золотая пряжка на подъёме.
            _dot(c, add(add(an, sd, -0.5 * s), fwd, 2.6 * s), pal["gold"][2])
            _dot(c, add(add(an, sd, -0.5 * s), fwd, 3.6 * s), pal["gold"][3])
    else:
        # Босые ноги: у тролля тумбы с широкой ступнёй и ногтями, у гоблина тонкие, с браслетом.
        troll = kind == "troll"
        thigh = capsule(hp, kn, (6.4 if troll else 4.4) * s * b, (5.2 if troll else 3.4) * s * b)
        put(c, pal, thigh, pal["skin"], far=far, soft=True)
        shin = capsule(kn, an, (5.0 if troll else 3.3) * s * b, (4.5 if troll else 2.7) * s * b)
        foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, (8.5 if troll else 7.5) * s),
                       (3.7 if troll else 2.7) * s, (3.2 if troll else 2.1) * s)
        put(c, pal, shin | foot, pal["skin"], far=far)
        if troll:
            put(c, pal, _band(shin, an, sd, -6.0 * s, -2.2 * s), pal["fur"], far=far, cast=False)
            put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 3.0 * s, 3.2 * s),
                [pal["skin"][0], pal["skin"][1], pal["skin"][1], pal["skin"][2]], far=far, cast=False)
            for k in (5.2, 8.0, 10.6):
                _dot(c, add(add(an, sd, 2.8 * s), fwd, k * s), pal["bone"][1 if far else 2])
        else:
            put(c, pal, _band(shin, an, sd, -4.6 * s, -2.8 * s), pal["gold"], far=far, cast=False)
            if not far:
                _dot(c, add(kn, fwd, 2.0), pal["skin"][3])
        boot = shin
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    ramp = pal["boots"] if kind in ("mage", "warlock") else pal["skin"]
    recolor(c, sole, lambda x, y, e: ramp[0])


def _staff(c, look, j):
    """Посох мага за спиной наискось: древко, золотая оправа и ромб кристалла над плечом;
    рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    a, e = P(H, -5.0, -9.0), P(N, -12.0, 4.5)
    d = _unit(a, e)
    perp = (d[1], -d[0])
    put(c, pal, capsule(a, e, 1.5, 1.3), pal["wood"], soft=False)
    put(c, pal, capsule(add(e, d, -1.0), add(e, d, 1.4), 2.2, 2.2), pal["gold"], cast=False)
    k = add(e, d, 6.0 * s)
    gem = poly([add(k, d, 4.6 * s), add(k, perp, 3.0 * s), add(k, d, -4.2 * s), add(k, perp, -3.0 * s)])
    put(c, pal, gem, pal["crystal"], soft=False)
    _dot(c, add(add(k, d, 1.0), perp, 0.8), pal["crystal"][3])
    _dot(c, add(add(k, d, 2.0), perp, 0.4), pal["crystal"][3])


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    pelvis_ramp = {"mage": "robe", "troll": "fur", "shaman": "cloth", "warlock": "cloak"}[kind]
    put(c, pal, pelvis, pal[pelvis_ramp], soft=True)
    belly = {"mage": 0.0, "troll": 2.6, "shaman": 0.6, "warlock": 0.4}[kind]
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.7, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "troll":
        tor |= ellipse(*P(lerp(N, H, 0.64), 3.6, 0), 8.0 * s * b, 7.6 * s)
        # Горб загривка.
        tor |= ellipse(*P(N, -5.5, -2.5), 6.0 * s * b, 5.0 * s)

    def mat(x, y):
        u = ((x - N[0]) * rt[0] + (y - N[1]) * rt[1]) / (s * b)
        v = -((x - N[0]) * up[0] + (y - N[1]) * up[1]) / s
        if kind == "mage":
            # Золотой ворот и планка мантии, перевязь посоха через грудь.
            if v < 2.4 or 3.4 < u < 5.2:
                return pal["gold"]
            if abs(2.0 * u - v + 15.0) < 2.4:
                return pal["wood"]
            return pal["robe"]
        if kind == "troll":
            if u < -3.6 and v < 14 and (x * 3 + y * 5) % 7 < 3:
                return pal["moss"]
            if ((u - 4.2) / 5.4) ** 2 + ((v - 19.0) / 10.0) ** 2 < 1.0:
                return pal["belly"]
            return pal["skin"]
        if kind == "shaman":
            return pal["skin"]
        if 1.4 < u < 6.4:
            return pal["robe"]
        return pal["cloak"]

    put(c, pal, tor, None, soft=True, mat=mat)
    if kind == "shaman":
        # Пончо: клин до середины живота, полосы зигзагом, бахрома по краю.
        mid, low = lerp(N, H, 0.5), lerp(N, H, 0.8)
        pon = poly([P(N, 5.0, 2), P(N, 11.0, -4), P(mid, 10.6, 0), P(low, 3.0, 0), P(mid, -10.4, 0), P(N, -11.0, -3),
                    P(N, -5.0, 2)])

        def pmat(x, y):
            u = ((x - N[0]) * rt[0] + (y - N[1]) * rt[1]) / (s * b)
            v = -((x - N[0]) * up[0] + (y - N[1]) * up[1]) / s
            k = int((v + abs((u % 6.0) - 3.0)) / 2.2) % 5
            return pal["gold"] if k == 2 else pal["red"] if k == 4 else pal["poncho"]

        put(c, pal, pon, None, soft=True, mat=pmat)
        fringe = {q for q in pon if (q[0], q[1] + 1) not in pon and (q[0] + q[1]) % 2 == 0}
        recolor(c, fringe, lambda x, y, e: pal["gold"][3])
    # Пояс с пряжкой.
    belt = poly([P(H, 6.8 + belly * 0.7, 5.8), P(H, 7.0 + belly * 0.7, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    belt_ramp = {"mage": "gold", "troll": "fur", "shaman": "cloth", "warlock": "gold"}[kind]
    put(c, pal, belt & (tor | pelvis), pal[belt_ramp], cast=False)
    bk = P(H, 4.6 + belly * 0.5, 4.1)
    buckle = {"mage": "crystal", "troll": "bone", "shaman": "bone", "warlock": "glow"}[kind]
    put(c, pal, ellipse(bk[0], bk[1], (2.6 if kind == "troll" else 1.9) * s, (2.4 if kind == "troll" else 1.7) * s),
        pal[buckle], cast=False)
    if kind == "mage":
        _dot(c, bk, pal["crystal"][3], -1, -1)
    elif kind == "troll":
        # Череп на поясе, ожерелье из клыков, складка груди и пупок.
        _dot(c, bk, pal["bone"][0], -1, 0)
        _dot(c, bk, pal["bone"][0], 1, 0)
        for k in range(5):
            q = P(lerp(N, H, 0.2 + 0.035 * (2 - abs(k - 2))), -1.0 + k * 2.2, 0)
            _dot(c, q, pal["bone"][3])
            _dot(c, q, pal["bone"][2], 0, 1)
        for k in range(4):
            _dot(c, P(lerp(N, H, 0.36), 2.0 + k, 0), pal["skin"][1])
        _dot(c, P(lerp(N, H, 0.7), 6.4, 0), pal["skin"][1])
    elif kind == "shaman":
        # Ожерелье из зубов поверх пончо.
        for k in range(4):
            _dot(c, P(lerp(N, H, 0.1 + 0.03 * k), 0.5 + k * 1.8, 0), pal["bone"][3])
    elif kind == "warlock":
        # Золотая кайма лиловой вставки, цепь и горящий амулет.
        for k in range(10):
            for r_ in (1.4, 6.4):
                q = P(lerp(N, H, 0.06 + k * 0.085), r_, 0)
                _dot(c, q, pal["gold"][2 if k % 2 else 1])
        for k in range(5):
            _dot(c, P(lerp(N, H, 0.04 + k * 0.045), 2.0 + k * 0.5, 0), pal["gold"][3 if k % 2 else 2])
        q = P(lerp(N, H, 0.3), 4.2, 0)
        put(c, pal, ellipse(q[0], q[1], 2.6 * s, 2.6 * s), pal["gold"], cast=False)
        put(c, pal, ellipse(q[0], q[1], 1.4 * s, 1.4 * s), pal["glow"], cast=False)
        _dot(c, q, pal["glow"][3])


def _tails(c, look, j, p, ln, ramp, hem=None, jag=False):
    """Полы от пояса вниз: длинная мантия чародея с золотой каймой, рваная повязка тролля и шамана."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = ln * s
    long = ln > 24 * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 6.8 * s * b), up, 3 * s),
           (H[0] + 5 * s * b + sway * 0.3, H[1] + ln * 0.85), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - (13 if long else 9) * s * b + sway, H[1] + ln * 0.9)]
    S = poly(pts)
    if jag:
        S -= {q for q in S if ((q[0], q[1] + 3) not in S) and (q[0] // 2) % 2 == 0}
    put(c, pal, S, pal[ramp], soft=True)
    if long:
        # Складки.
        for k in (0.3, 0.62):
            a, e = lerp(pts[0], pts[1], k), lerp(pts[4], pts[2], k)
            for t in range(4, 20):
                q = lerp(a, e, t / 20.0)
                if (int(round(q[0])), int(round(q[1]))) in S and t % 5:
                    _dot(c, q, pal[ramp][1])
    if hem:
        edge = {q for q in S if (q[0], q[1] + 1) not in S or (q[0], q[1] + 2) not in S}
        recolor(c, edge, lambda x, y, e: pal[hem][2] if (x + y) % 3 else pal[hem][1])


def _skirt(c, look, j):
    """Подол мантии мага: колокол от пояса до колен, тянется за бёдрами, золотая кайма понизу.
    Рисуется после ближней ноги: из-под подола видны колени, чулки и сапоги."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    S, ends, hem = set(), [], set()
    L = 0.8 * look.body.thigh
    for side in ("f", "n"):
        hp, kn = j["hp_" + side], j["kn_" + side]
        d = _unit(hp, kn)
        part = {q for q in capsule(hp, add(hp, d, L), 7.6 * s * b, 7.2 * s * b) if _along(q, hp, d) <= L + 0.5}
        S |= part
        hem |= _band(part, hp, d, L - 2.2, L + 0.5)
        ends.append(add(hp, d, L))
    ends.sort()
    back, front = ends
    top_b, top_f = add(add(H, rt, -7.4 * s * b), up, 2 * s), add(add(H, rt, 7.0 * s * b), up, 2 * s)
    web = poly([top_b, top_f, front, back])
    S |= web
    hem |= capsule(back, front, 1.6, 1.6) & web
    # Кайма только по нижнему краю: полоса, ниже которой подол кончается.
    hem = {q for q in hem if any((q[0], q[1] + k) not in S for k in (1, 2, 3)) or q in web}
    put(c, pal, S, pal["robe"], soft=True)
    G = pal["gold"]
    recolor(c, hem, lambda x, y, e: G[1] if e in (pal["robe"][0], pal["robe"][1]) else G[3] if (x + y) % 4 == 0 else G[2])
    # Складки от пояса к подолу.
    mid = lerp(back, front, 0.5)
    for k in (0.28, 0.6):
        a, e = lerp(top_b, top_f, k), lerp(back, front, k)
        for t in range(3, 15):
            q = lerp(a, e, t / 18.0)
            if (int(round(q[0])), int(round(q[1]))) in S:
                _dot(c, q, pal["robe"][1])
    _dot(c, mid, G[1])


def _head(c, look, j, p, hurt=False):
    pal, s, kind = look.pal, look.body.s, look.kind
    hc = j["head"]
    ang = p["lean"] + p["tilt"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    w = p.get("wave", 0.0)

    def H(dx, dy):
        return (hc[0] + (dx * ca - dy * sa) * s, hc[1] + (dx * sa + dy * ca) * s)

    def local(x, y):
        dx, dy = (x - hc[0]) / s, (y - hc[1]) / s
        return (dx * ca + dy * sa, -dx * sa + dy * ca)

    def line(a, e, col, S=None):
        n = int(max(abs(e[0] - a[0]), abs(e[1] - a[1])) * 2) + 1
        for i in range(n + 1):
            q = lerp(a, e, i / n)
            q = (int(round(q[0])), int(round(q[1])))
            if S is None or q in S:
                c.set(q[0], q[1], col)

    sk = pal["skin"]
    if kind == "mage":
        neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
        put(c, pal, neck, sk)
        # Каштановые волосы из-под шляпы на затылке.
        put(c, pal, capsule(H(-4.5, -2), H(-5.8, 5.4), 3.4 * s, 2.4 * s), pal["boots"], soft=True)
        skull = ellipse(*H(0, -0.5), 6.9 * s, 7.6 * s, ang)
        jaw = poly([H(-3, 2), H(6.0, 1.5), H(6.2, 4.6), H(3.4, 8.0), H(-2.5, 7.4)])
        nose = poly([H(5.4, -1.2), H(7.8, 2.0), H(5.6, 2.8)])
        face = skull | jaw | nose
        put(c, pal, face, sk, soft=True)
        hair = {q for q in skull if local(*q)[0] < -2.4 and local(*q)[1] < 5.5}
        put(c, pal, hair, pal["boots"], cast=False, soft=True)
        ex, ey = H(-1.2, 1.4)
        put(c, pal, ellipse(ex, ey, 1.6 * s, 2.0 * s), [sk[0], sk[1], sk[2], sk[2]], cast=False)
        # Шляпа: тулья клонится назад, кончик загнут и качается, золотая лента со звездой, поля.
        cone = poly([H(6.6, -6.0), H(3.2, -11.4), H(-0.4, -16.2), H(-3.4, -16.4), H(-5.6, -12.0), H(-7.6, -5.4)])
        cone |= capsule(H(-2.0, -15.0), H(-9.0 - w * 0.6, -13.2 + w * 0.9), 2.1 * s, 1.0 * s)
        put(c, pal, cone, pal["robe"], soft=True)
        band = {q for q in cone if -8.6 < local(*q)[1] < -6.2}
        put(c, pal, band, pal["gold"], cast=False)
        q = H(0.5, -11.0)
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            _dot(c, q, pal["gold"][3 if (dx, dy) == (0, 0) else 2], dx, dy)
        brim = ellipse(*H(-0.6, -5.0), 12.0 * s, 2.5 * s, ang - 7)
        put(c, pal, brim, pal["robe"], soft=True)
        low = {q for q in brim if (q[0], q[1] + 1) not in brim}
        recolor(c, low, lambda x, y, e: pal["robe"][0])
        # Глаз, бровь, рот.
        ex, ey = H(3.3, -0.6)
        ex, ey = int(round(ex)), int(round(ey))
        E = pal["eye"]
        if hurt:
            c.set(ex, ey, sk[0])
            c.set(ex + 1, ey, sk[0])
            c.set(ex - 1, ey - 1, sk[0])
        else:
            c.set(ex, ey, E[3])
            c.set(ex + 1, ey, E[0])
            c.set(ex + 1, ey - 1, E[0])
            c.set(ex, ey - 1, E[3])
        mx, my = H(4.0, 5.0)
        mx, my = int(round(mx)), int(round(my))
        c.set(mx, my, sk[0])
        c.set(mx + 1, my, sk[0])
        if hurt:
            c.set(mx, my + 1, sk[0])
            c.set(mx + 1, my + 1, 0)
        return
    if kind == "troll":
        neck = capsule(lerp(j["neck"], hc, 0.0), lerp(j["neck"], hc, 0.6), 5.4 * s * look.body.b, 5.0 * s)
        put(c, pal, neck, sk)
        # Рваное ухо торчит назад.
        ear = poly([H(-6.0, -5.0), H(-14.0, -9.0 - w), H(-12.0, -3.4), H(-7.0, 1.4)])
        put(c, pal, ear, sk, soft=True)
        line(H(-7.5, -3.6), H(-11.6, -6.0 - w * 0.6), sk[0], ear)
        # Гребень мха на темени.
        for k in range(4):
            put(c, pal, poly([H(-8.0 + k * 3.7, -9.6), H(-7.2 + k * 3.7, -15.2 - (k % 2) * 1.2), H(-4.0 + k * 3.7, -10.0)]),
                pal["moss"], cast=False)
        # Плоский череп, тяжёлая нижняя челюсть вперёд.
        skull = ellipse(*H(-1.0, -4.0), 9.2 * s, 7.6 * s, ang)
        jaw = poly([H(-5, 0), H(7.5, 0), H(10.6, 3.4), H(10.2, 8.6), H(2.0, 11.2), H(-5.0, 8.0)])
        face = skull | jaw
        put(c, pal, face, sk, soft=True)
        # Бородавки и трещины камня.
        for dx, dy in ((-4, -8), (-6, -3), (-1, -9), (-3, 5), (0, 8), (-2, 1)):
            q = H(dx, dy)
            if (int(round(q[0])), int(round(q[1]))) in face:
                _dot(c, q, sk[1])
                _dot(c, q, sk[3], -1, -1)
        # Нависшая бровь и нос картошкой светлее шкуры.
        put(c, pal, capsule(H(1.0, -5.4), H(7.6, -4.6), 1.8 * s, 1.5 * s), [sk[0], sk[1], sk[1], sk[2]], cast=False)
        nose = ellipse(*H(8.8, -0.4), 3.5 * s, 3.7 * s, ang)
        put(c, pal, nose, pal["belly"], soft=False)
        _dot(c, H(9.4, 1.6), sk[0])
        # Пасть во всю челюсть и два клыка вверх.
        line(H(1.6, 5.0), H(10.2, 4.6), 0, face)
        line(H(2.2, 6.0), H(9.8, 5.6), sk[1], face)
        put(c, pal, poly([H(3.6, 5.2), H(4.9, -1.2), H(6.4, 5.2)]), pal["bone"], soft=False, cast=False)
        put(c, pal, poly([H(7.4, 5.0), H(8.3, 2.6), H(9.4, 5.0)]), pal["bone"], soft=False, cast=False)
        E = pal["eye"]
        ex, ey = H(3.2, -2.6)
        if hurt:
            line(H(1.6, -2.8), H(5.2, -2.4), sk[0], face)
            line(H(2.4, 7.2), H(8.6, 7.0), sk[0], face)
        else:
            for q in ellipse(ex, ey, 2.5 * s, 1.6 * s, ang) & face:
                c.set(q[0], q[1], sk[0])
            _dot(c, (ex, ey), E[2])
            _dot(c, (ex + 1, ey), E[3])
        return
    if kind == "shaman":
        neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 2.9 * s, 2.7 * s)
        put(c, pal, neck, sk)
        # Перья в повязке: фиолетовое, бирюзовое, красное, кончики белые.
        for k, ramp in enumerate(("poncho", "crystal", "red")):
            a, e = H(-3.4 + k * 2.6, -6.0), H(-7.5 + k * 3.6 - w * 0.5, -15.6 + abs(k - 1) * 1.4)
            put(c, pal, capsule(a, e, 1.9 * s, 1.0 * s), pal[ramp], soft=False)
            _dot(c, e, pal["bone"][3])
            _dot(c, lerp(a, e, 0.8), pal["bone"][3])
        skull = ellipse(*H(0, -2.0), 7.0 * s, 6.4 * s, ang)
        jaw = poly([H(-3, 1), H(5.6, 0.8), H(6.2, 4.2), H(4.6, 8.4), H(-2.2, 6.2)])
        nose = poly([H(4.6, -2.4), H(12.2, 1.8), H(5.4, 3.2)])
        face = skull | jaw | nose
        put(c, pal, face, sk, soft=True)
        # Ухо шире головы: назад и вверх, качается; золотая серьга.
        ear = poly([H(-2.2, -3.6), H(-14.0, -8.2 - w), H(-4.2, 1.8)])
        put(c, pal, ear, sk, soft=True)
        line(H(-4.0, -2.6), H(-10.5, -6.6 - w * 0.7), sk[0], ear)
        _dot(c, H(-5.4, 1.6), pal["gold"][2])
        _dot(c, H(-5.4, 2.6), pal["gold"][3])
        # Красная повязка на лбу.
        band = {q for q in skull if -6.6 < local(*q)[1] < -4.2}
        put(c, pal, band, pal["red"], cast=False)
        # Боевая раскраска: белые точки на скуле.
        for dx, dy in ((1.0, 2.2), (2.6, 2.8), (-0.6, 1.6)):
            _dot(c, H(dx, dy), pal["bone"][3])
        E = pal["eye"]
        ex, ey = H(3.2, -1.2)
        if hurt:
            line(H(1.6, -1.4), H(5.2, -1.0), sk[0], face)
            _dot(c, H(1.8, -2.2), sk[0])
        else:
            eye = ellipse(ex, ey, 2.3 * s, 1.9 * s, ang) & face
            put(c, pal, eye, [E[1], E[2], E[2], E[3]], cast=False)
            _dot(c, (ex + 0.6, ey), E[0])
            line(H(1.2, -3.8), H(5.2, -2.6), sk[0], face)
        # Оскал: тёмная пасть с зубами через один.
        a, e = H(2.6, 4.8), H(6.2, 4.4)
        line(a, e, sk[0], face)
        for t in (0.2, 0.6, 1.0):
            _dot(c, lerp(a, e, t), pal["bone"][3])
        if hurt:
            line(H(3.0, 5.8), H(5.8, 5.6), sk[0], face)
        return
    # Тёмный чародей: высокий ворот, седые пряди, впалое лицо, борода клином, корона с рогами.
    col = poly([H(-9, 9), H(-10.5, -1), H(-5, 3), H(2, 9)])
    put(c, pal, col, pal["cloak"], soft=True)
    edge = {q for q in col if (q[0] - 1, q[1]) not in col or (q[0], q[1] - 1) not in col}
    recolor(c, edge, lambda x, y, e: pal["gold"][2])
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
    put(c, pal, neck, sk)
    grey = [pal["beard"][0], pal["beard"][0], pal["beard"][1], pal["beard"][2]]
    put(c, pal, capsule(H(-5.2, -2), H(-8.2 - w * 0.6, 6.5), 3.0 * s, 1.5 * s), grey, soft=True)

    def horn(x0, far):
        pts = [H(x0, -6.6), H(x0 - 4.2, -10.6), H(x0 - 5.0, -14.6), H(x0 - 2.0, -17.4)]
        rad = [2.6, 2.2, 1.5, 0.6]
        S = set()
        for k in range(3):
            S |= capsule(pts[k], pts[k + 1], rad[k] * s, rad[k + 1] * s)
        put(c, pal, S, pal["horn"], far=far, soft=False)
        for t in (0.35, 0.7):
            q = lerp(pts[0], pts[1], t)
            _dot(c, q, pal["horn"][0 if far else 1], 1, 0)
        _dot(c, lerp(pts[1], pts[2], 0.6), pal["horn"][0 if far else 1], 1, 0)

    horn(4.2, True)
    skull = ellipse(*H(0, -0.8), 6.8 * s, 7.4 * s, ang)
    jaw = poly([H(-3, 2), H(6.0, 1.5), H(6.2, 5.0), H(3.8, 8.6), H(-2.5, 7.6)])
    nose = poly([H(5.2, -2.6), H(9.4, 2.2), H(5.6, 3.2)])
    face = skull | jaw | nose
    put(c, pal, face, sk, soft=True)
    hair = {q for q in skull if local(*q)[0] < -3.6 and local(*q)[1] < 6.0}
    put(c, pal, hair, grey, cast=False, soft=True)
    # Борода клином от скулы до груди и ус над ней.
    beard = poly([H(-1.6, 4.6), H(2.0, 4.2), H(6.6, 4.4), H(7.0, 7.0), H(4.6, 16.5), H(-0.4, 9.6)])
    put(c, pal, beard, pal["beard"], soft=True)
    line(H(2.4, 7.0), H(4.2, 14.0), pal["beard"][1], beard)
    line(H(3.4, 5.6), H(6.4, 5.6), pal["beard"][0], beard)
    # Впалая щека.
    line(H(0.8, 0.6), H(2.2, 3.4), sk[1], face)
    line(H(1.8, 0.6), H(3.2, 3.4), sk[1], face)
    # Корона: золотой обод, три зубца, красный камень; ближний рог поверх.
    crown = capsule(H(-6.6, -5.6), H(6.8, -5.8), 1.8 * s, 1.8 * s)
    for k in range(3):
        crown |= poly([H(-3.6 + k * 3.6, -6.6), H(-2.2 + k * 3.6, -11.2), H(-0.6 + k * 3.6, -6.6)])
    put(c, pal, crown, pal["gold"], soft=False)
    q = H(2.0, -5.8)
    _dot(c, q, pal["glow"][2])
    _dot(c, q, pal["glow"][3], -1, 0)
    horn(-2.6, False)
    # Глаз: тёмная глазница под обручем, в ней горит красный огонь.
    G = pal["glow"]
    ex, ey = H(3.6, -1.6)
    socket = ellipse(ex, ey, 2.7 * s, 1.7 * s, ang) & face
    if hurt:
        line(H(1.8, -1.6), H(5.4, -1.2), sk[0], face)
        line(H(3.8, 6.8), H(6.0, 7.0), pal["beard"][0], beard)
    else:
        for q in socket:
            c.set(q[0], q[1], sk[0])
        _dot(c, (ex, ey), G[2])
        _dot(c, (ex + 1, ey), G[3])
        _dot(c, (ex, ey - 1), G[1])
        _dot(c, (ex + 1, ey - 1), G[2])


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if kind == "mage":
        _staff(c, look, j)
    if kind == "warlock":
        _tails(c, look, j, p, 33, "cloak", hem="gold")
    _torso(c, look, j, p)
    if kind == "troll":
        _tails(c, look, j, p, 15, "fur", jag=True)
    elif kind == "shaman":
        _tails(c, look, j, p, 14, "cloth", jag=True)
    _leg(c, look, j, "n", False, p)
    if kind == "mage":
        _skirt(c, look, j)
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
    for key, look, frame, w, h, up, left in (("hero", hero_look(), pb.hero_frames()[0], FW, FH, 21, 17),
                                             ("thug", thug_look(), pb.foe_frames()[0], FW, FH, 19, 15),
                                             ("knife", knife_look(), pb.foe_frames(knife=True)[0], FW, FH, 20, 17),
                                             ("boss", boss_look(), pb.foe_frames(boss=True)[0], BW, BH, 22, 16)):
        f = fighter(frame, look, w, h)
        hx, hy = int(round(f.head[0])), int(round(f.head[1]))
        c = Canvas(32, 32)
        for y in range(32):
            for x in range(32):
                sx, sy = hx - left + x, hy - up + y
                if 0 <= sx < w and 0 <= sy < h:
                    c.px[y][x] = f.px[sy][sx]
        out["brawl_face_" + key] = (c, look.pal.colors)
    return out


# --- Тропа под великим деревом -----------------------------------------------------------------

# Руны 3×5 для резьбы на камне и плитах.
RUNES = ("X.XX.X.X..X..X.", ".X.XXXX.X.X..X.", "X.XX.X.X.X.XX.X", "X..XX.X.XXX.X..", ".X.X.XX.XX.X.X.",
         ".X.X.X.X.X.X.X.", "XX.X.XXX.X..X..", "..X.XXX.XXX.X..")


def street_pal():
    p = Pal(0x0E0A16)
    p.add("bark", [0x1E1420, 0x3A2630, 0x5E3E3C, 0x86604A])
    p.add("wood", [0x482E36, 0x744A38, 0x9A643C, 0xC8925A])
    p.add("stone", [0x3A3456, 0x625A86, 0x8E86AE, 0xBEB6D6])
    p.add("moss", [0x1C3A2A, 0x2E6238, 0x4E9444, 0x86C860])
    p.add("leaf", [0x2E1A5A, 0x522E8E, 0x8250C4, 0xB684EA])
    p.add("glow", [0x146A70, 0x24A8A0, 0x3AD4C2, 0xC8F8EC])
    p.add("gold", [0x7A4E1C, 0xC2862C, 0xF6D058, 0xFFF4B8])
    p.add("warm", [0x8A3A1C, 0xD8782C, 0xF8B84C, 0xFFEEA8])
    p.add("red", [0x5A1630, 0x9A2A44, 0xDC465A, 0xFF8C8C])
    p.add("night", [0x1A1644, 0x2E2A70, 0x5048A0, 0x8474CC])
    p.add("pink", [0x6A3C8E, 0xA45CAE, 0xE08CC0, 0xFFCCDC])
    p.add("earth", [0x2A2030, 0x43343E, 0x5E4A50, 0x7C6664])
    p.add("slab", [0x34304E, 0x524C74, 0x746E98, 0x9C96BC])
    p.add("dark", [0x0E0A16, 0x1A1426, 0x2A2238, 0x40364E])
    p.add("cream", [0x8A7A8E, 0xB8AAB6, 0xE2D8D4, 0xFAF4EA])
    return p


def arch_mask(x0, x1, top, bottom, pointed=False):
    """Проём с аркой: полукруглой или стрельчатой."""
    S = set()
    cx, hw = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    rise = hw * (1.5 if pointed else 1.0)
    for x in range(int(x0), int(x1) + 1):
        k = min(1.0, abs(x - cx) / hw)
        y0 = top + rise * ((k ** 1.5) if pointed else (1.0 - math.sqrt(max(0.0, 1.0 - k * k))))
        for y in range(int(round(y0)), int(bottom) + 1):
            S.add((x, y))
    return S


def grow(S, n):
    for _ in range(n):
        S = S | {(x + dx, y + dy) for (x, y) in S for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    return S


class Grove(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(137)
        self.up = {}
        for idx in self.p.ramp.values():
            for i in range(3):
                self.up[idx[i]] = idx[i + 1]

    def fill(self, S, col):
        for (x, y) in S:
            self.c.set(x, y, col)

    def light(self, S, dither=True):
        """Свет на то, что уже нарисовано: тон на ступень светлее."""
        for (x, y) in S:
            if dither and (x + y) % 2:
                continue
            e = self.c.get(x, y)
            if e in self.up:
                self.c.set(x, y, self.up[e])

    def halo(self, cx, cy, rx, ry):
        self.light(ellipse(cx, cy, rx, ry))
        self.light(ellipse(cx, cy, rx * 0.6, ry * 0.6), dither=False)

    def rune(self, x, y, i, col, k=1):
        bits = RUNES[i % len(RUNES)]
        for n, ch in enumerate(bits):
            if ch == "X":
                self.rect(x + (n % 3) * k, y + (n // 3) * k, x + (n % 3) * k + k - 1, y + (n // 3) * k + k - 1, col)

    # Стены ------------------------------------------------------------------------------------

    def bark(self, x0, y0, x1, y1):
        """Кора великого дерева: волнистые борозды сверху вниз, поперечные трещины, сучки, мох."""
        B, r = self.R("bark"), self.rng
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g = math.sin(x * 0.42 + 2.4 * math.sin(y * 0.045 + x * 0.11))
                t = 3 if g > 0.92 else 0 if g < -0.9 else 1 if g < -0.45 else 2
                self.c.set(x, y, B[t])
        for _ in range((x1 - x0) * (y1 - y0) // 500):
            x, y = r.randint(x0 + 2, x1 - 8), r.randint(y0 + 2, y1 - 2)
            ln = r.randint(3, 7)
            self.rect(x, y, x + ln, y, B[0])
            self.rect(x, y + 1, x + ln, y + 1, B[3])
        for _ in range((x1 - x0) // 70):
            x, y = r.randint(x0 + 12, x1 - 12), r.randint(y0 + 20, y1 - 30)
            self.put(ellipse(x, y, 6, 8) - ellipse(x, y, 3.2, 5), B, soft=False, cast=False)
            self.fill(ellipse(x, y, 3.2, 5), B[0])

    def masonry(self, x0, y0, x1, y1, bw=40, bh=20, ramp="stone", moss=0.15, runes=0.06):
        """Сиреневая кладка: блоки с фаской, сколы, мох по верхним швам, редкая резная руна."""
        R_, M, r = self.R(ramp), self.R("moss"), self.rng
        self.rect(x0, y0, x1, y1, R_[0])
        for row, y in enumerate(range(y0, y1 + 1, bh)):
            x = x0 - (0 if row % 2 == 0 else bw // 2) - r.randint(0, 6)
            while x <= x1:
                wv = bw + r.randint(-8, 8)
                a, b = max(x + 1, x0), min(x + wv - 1, x1)
                yb = min(y + bh - 1, y1)
                if b - a > 3 and yb - y > 3:
                    rr = R_ if r.random() < 0.75 else [R_[0], R_[1], R_[1], R_[2]]
                    self.bevel(a, y + 1, b, yb, rr)
                    self.noise(a + 1, y + 2, b - 1, yb - 1, rr, 0.05)
                    if r.random() < 0.25:
                        sx = r.randint(a + 2, max(a + 3, b - 8))
                        self.rect(sx, yb - 3, sx + r.randint(2, 5), yb - 3, rr[1])
                    if r.random() < runes and b - a > 12 and yb - y > 10:
                        rx, ry = (a + b) // 2 - 1, (y + yb) // 2 - 2
                        self.rune(rx + 1, ry + 1, r.randint(0, 7), rr[3])
                        self.rune(rx, ry, r.randint(0, 7), rr[0])
                    if r.random() < moss:
                        for xx in range(a, b + 1):
                            d = r.randint(0, 3)
                            for yy in range(y, y + d):
                                self.c.set(xx, yy, M[1 if yy > y else 2])
                x += wv

    def rock(self, x0, y0, x1, y1):
        """Скала грота: валуны внахлёст, тёмные щели."""
        E, r = self.R("dark"), self.rng
        self.rect(x0, y0, x1, y1, E[1])
        ramp = [E[1], E[2], E[3], self.R("earth")[2]]
        blobs = [(r.randint(y0, y1), r.randint(x0, x1), r.randint(12, 26), r.randint(8, 16)) for _ in
                 range((x1 - x0) * (y1 - y0) // 420)]
        for (y, x, rx, ry) in sorted(blobs):
            S = {q for q in ellipse(x, y, rx, ry, r.randint(-20, 20)) if x0 <= q[0] <= x1 and y0 <= q[1] <= y1}
            self.put(S, ramp, soft=True, cast=False)

    def canopy(self, x0, x1):
        """Верх кадра: сиреневая листва гроздьями, под ней толстая ветвь со мхом."""
        L, B, M, r = self.R("leaf"), self.R("bark"), self.R("moss"), self.rng
        self.rect(x0, 0, x1, 19, L[0])
        for _ in range((x1 - x0) // 7):
            cx, cy = r.randint(x0, x1), r.randint(-2, 15)
            S = {q for q in ellipse(cx, cy, r.randint(7, 15), r.randint(4, 7)) if x0 <= q[0] <= x1 and 0 <= q[1] <= 21}
            self.put(S, L if r.random() < 0.7 else [L[0], L[1], L[1], L[2]], soft=True, cast=False)
        for _ in range((x1 - x0) // 24):
            self.c.set(r.randint(x0, x1), r.randint(2, 17), self.R("pink")[3])
        for y in range(20, 32):
            for x in range(x0, x1 + 1):
                g = math.sin(y * 1.1 + 1.6 * math.sin(x * 0.07))
                t = 3 if y == 20 else 0 if y == 31 else 1 if g < -0.5 or y > 28 else 3 if g > 0.85 else 2
                self.c.set(x, y, B[t])
        for x in range(x0, x1 + 1):
            d = int(1.5 + 1.5 * math.sin(x * 0.21) + r.random())
            for y in range(19, 19 + d):
                self.c.set(x, y, M[2 if y == 19 else 1])
        self.dark(x0, 32, x1, 35, 1)
        self.dark(x0, 36, x1, 38, 1, dither=True)

    # Детали стены ------------------------------------------------------------------------------

    def liana(self, x, y0, y1, flower=True):
        M, P_ = self.R("moss"), self.R("pink")
        for y in range(y0, y1):
            xx = x + int(round(math.sin((y - y0) * 0.16 + x) * 2.5))
            self.c.set(xx, y, M[1])
            self.c.set(xx + 1, y, M[0])
            if (y - y0) % 7 == 3:
                side = 1 if ((y - y0) // 7) % 2 else -1
                self.rect(xx + side * 2, y - 1, xx + side * 4, y, M[2])
                self.c.set(xx + side * 4, y - 1, M[3])
                self.c.set(xx + side * 3, y + 1, M[1])
            if flower and (y - y0) % 23 == 12:
                self.rect(xx - 1, y, xx, y + 1, P_[2])
                self.c.set(xx - 1, y, P_[3])
        self.rect(x - 1, y1, x + 1, y1 + 1, M[2])

    def bell(self, x, y0, ln):
        """Фонарь-цветок: стебель с ветви, колокол лепестков, тёплый огонёк и пятно света."""
        M, P_, W = self.R("moss"), self.R("pink"), self.R("warm")
        y = y0 + ln
        self.halo(x, y + 8, 26, 22)
        for yy in range(y0, y):
            self.c.set(x + int(round(math.sin(yy * 0.2) * 1.2)), yy, M[1])
        self.rect(x - 2, y - 1, x + 2, y, M[2])
        S = poly([(x - 3, y + 1), (x + 3, y + 1), (x + 7, y + 11), (x + 4, y + 9), (x + 1, y + 12), (x - 2, y + 9),
                  (x - 5, y + 12), (x - 7, y + 10)])
        self.put(S, P_, soft=True, cast=False)
        self.fill(ellipse(x, y + 10, 2.4, 2.6), W[3])
        self.fill(ellipse(x, y + 13, 1.6, 1.4), W[2])

    def round_window(self, cx, cy, r, lit=True):
        """Круглое окно в коре: деревянная рама, переплёт крестом, внутри тёплый свет."""
        Wd, W, G = self.R("wood"), self.R("warm"), self.R("night")
        if lit:
            self.halo(cx, cy, r + 14, r + 14)
        self.put(ellipse(cx, cy, r + 5, r + 5), Wd, soft=True)
        inner = ellipse(cx, cy, r, r)
        for (x, y) in inner:
            d = math.hypot(x - cx, y - cy - r * 0.3) / r
            if lit:
                t = 3 if d < 0.45 else 2 if d < 0.8 or (x + y) % 2 else 1
                self.c.set(x, y, W[t])
            else:
                self.c.set(x, y, G[1] if d < 0.6 and (x + y) % 2 else G[0])
            if (x - 3, y - 3) not in inner:
                self.c.set(x, y, W[1] if lit else self.R("dark")[0])
        self.fill({q for q in inner if abs(q[0] - cx) < 1.5 or abs(q[1] - cy) < 1.5}, Wd[1])
        self.fill({q for q in inner if q[0] == cx - 1 or q[1] == cy - 1}, Wd[3])
        for k in range(6):
            a = k * math.pi / 3 + 0.5
            self.c.set(cx + math.cos(a) * (r + 3), cy + math.sin(a) * (r + 3), Wd[0])
        self.dark(cx - r - 3, cy + r + 6, cx + r + 7, cy + r + 8, 1)

    def round_door(self, cx, by, r):
        """Круглая дверь жилого ствола: каменный обод, доски, кованые петли, золотая ручка в центре."""
        S_, Wd, I, G = self.R("stone"), self.R("wood"), self.R("dark"), self.R("gold")
        cy = by - int(r * 0.82)
        rim = {q for q in ellipse(cx, cy, r + 7, r + 7) if q[1] <= by}
        self.put(rim, S_, soft=True)
        for k in range(12):
            a = math.pi + k * math.pi / 11 * 1.25 - 0.4
            for t in range(r + 1, r + 7):
                q = (int(round(cx + math.cos(a) * t)), int(round(cy + math.sin(a) * t)))
                if q in rim:
                    self.c.set(q[0], q[1], S_[0])
        door = {q for q in ellipse(cx, cy, r, r) if q[1] <= by}
        self.put(door, Wd, soft=True, cast=False)
        for (x, y) in door:
            k = (x - cx + 200) % 9
            if k == 0:
                self.c.set(x, y, Wd[0])
            elif k == 1 and self.c.get(x, y) == Wd[2]:
                self.c.set(x, y, Wd[3])
        for yy in (cy - r // 2, cy + r // 3):
            bar = {q for q in door if yy <= q[1] <= yy + 3 and q[0] < cx + r * 0.45}
            self.fill(bar, I[2])
            self.fill({q for q in bar if q[1] == yy}, I[3])
            self.fill({q for q in bar if q[1] == yy + 3}, I[0])
            for xx in range(cx - r + 6, int(cx + r * 0.4), 8):
                if (xx, yy + 1) in bar:
                    self.c.set(xx, yy + 1, self.R("stone")[3])
        self.put(ellipse(cx, cy, 4, 4), G, soft=False)
        self.c.set(cx - 1, cy - 1, G[3])
        self.fill({q for q in door if (q[0] - 3, q[1] - 3) not in door}, Wd[0])
        self.bevel(cx - r - 12, by + 1, cx + r + 12, by + 5, S_)

    def arch_door(self, x, y, w, h, ramp="wood"):
        """Дверь со стрельчатой аркой: каменный наличник, доски, петли, кольцо."""
        S_, Wd, I, G = self.R("stone"), self.R(ramp), self.R("dark"), self.R("gold")
        frame = arch_mask(x - 7, x + w + 7, y - 10, y + h, True)
        self.put(frame, S_, soft=True)
        door = arch_mask(x, x + w, y, y + h, True)
        self.fill(door, Wd[2])
        for (xx, yy) in door:
            k = (xx - x) % 8
            if k == 0:
                self.c.set(xx, yy, Wd[0])
            elif k == 1:
                self.c.set(xx, yy, Wd[3])
            elif (xx * 7 + yy * 3) % 23 == 0:
                self.c.set(xx, yy, Wd[1])
        for yy in (y + h // 3, y + h - 22):
            self.rect(x + 1, yy, x + w - 10, yy + 2, I[2])
            self.rect(x + 1, yy, x + w - 10, yy, I[3])
            for xx in range(x + 4, x + w - 10, 7):
                self.c.set(xx, yy + 1, S_[3])
        ring = ellipse(x + w - 8, y + h // 2 + 8, 4, 4) - ellipse(x + w - 8, y + h // 2 + 8, 2, 2)
        self.fill(ring, G[2])
        self.c.set(x + w - 10, y + h // 2 + 5, G[3])
        self.fill({q for q in door if (q[0] - 4, q[1] - 4) not in door}, Wd[0])
        self.bevel(x - 12, y + h + 1, x + w + 12, y + h + 5, S_)

    def star_window(self, x, y, w, h):
        """Стрельчатое окно гильдии: каменная рама, синее стекло со звёздами и месяцем, переплёт."""
        S_, N, G, P_ = self.R("stone"), self.R("night"), self.R("gold"), self.R("pink")
        r = self.rng
        self.put(arch_mask(x - 6, x + w + 6, y - 9, y + h + 5, True), S_, soft=True)
        glass = arch_mask(x, x + w, y, y + h, True)
        for (xx, yy) in glass:
            k = (yy - y) / float(h)
            t = N[0] if k < 0.3 else N[1] if k < 0.62 or (xx + yy) % 2 else N[2]
            if k > 0.86:
                t = P_[0] if (xx + yy) % 2 else N[2]
            self.c.set(xx, yy, t)
        for _ in range(w * h // 60):
            q = (r.randint(x, x + w), r.randint(y, y + h))
            if q in glass:
                self.c.set(q[0], q[1], G[3] if r.random() < 0.5 else self.R("cream")[3])
        moon = ellipse(x + w * 0.5, y + h * 0.42, 5, 5) - ellipse(x + w * 0.5 + 2.5, y + h * 0.42 - 1.5, 4.4, 4.4)
        self.fill(moon & glass, G[2])
        for (xx, yy) in glass:
            if (xx - x + yy - y) % 12 == 0 or (xx - x - (yy - y)) % 12 == 0:
                self.c.set(xx, yy, self.R("dark")[1])
            if (xx - 3, yy - 3) not in glass:
                self.c.set(xx, yy, self.R("dark")[0])
        self.bevel(x - 8, y + h + 4, x + w + 8, y + h + 8, S_)
        self.dark(x - 6, y + h + 9, x + w + 10, y + h + 11, 1)

    def banner(self, x, y, w, h, ramp="leaf", i=0):
        """Знамя гильдии: золотая перекладина, полотнище с ласточкиным хвостом, звезда и руна."""
        R_, G = self.R(ramp), self.R("gold")
        cloth = {(xx, yy) for xx in range(x, x + w + 1) for yy in range(y, y + h + 1)
                 if yy <= y + h - (w / 2.0 - abs(xx - x - w / 2.0)) * 0.7}
        self.dark(x + 3, y + 3, x + w + 3, y + h - 6, 1)
        for (xx, yy) in cloth:
            k = (xx - x) * 4 // (w + 1)
            self.c.set(xx, yy, R_[(2, 3, 2, 1)[k]])
            if xx in (x, x + w) or (xx, yy + 1) not in cloth:
                self.c.set(xx, yy, G[2 if (xx + yy) % 3 else 1])
        cx, cy = x + w // 2, y + h // 3
        for k in range(-5, 6):
            wd = max(0, 2 - abs(k))
            self.rect(cx - wd, cy + k, cx + wd, cy + k, G[2])
            self.rect(cx + k, cy - wd, cx + k, cy + wd, G[2])
        self.c.set(cx, cy, G[3])
        self.rune(cx - 2, cy + 10, i, G[3], 2)
        self.rect(x - 4, y - 3, x + w + 4, y - 1, G[2])
        self.rect(x - 4, y - 3, x + w + 4, y - 3, G[3])
        self.rect(x - 5, y - 4, x - 4, y, G[1])
        self.rect(x + w + 4, y - 4, x + w + 5, y, G[1])

    def bottle(self, x, y, kind, ramp):
        """Склянка на полке, дно в строке `y`: колба, реторта или высокий флакон."""
        R_, Cr = self.R(ramp), self.R("cream")
        if kind == 0:
            body = ellipse(x, y - 5, 5, 5)
            self.rect(x - 1, y - 14, x + 1, y - 9, Cr[1])
            self.rect(x - 2, y - 16, x + 2, y - 15, self.R("wood")[2])
        elif kind == 1:
            body = poly([(x - 5, y), (x + 5, y), (x + 2, y - 9), (x - 2, y - 9)])
            self.rect(x - 1, y - 14, x + 1, y - 10, Cr[1])
            self.rect(x - 2, y - 15, x + 2, y - 15, self.R("wood")[2])
        else:
            body = {(xx, yy) for xx in range(x - 3, x + 4) for yy in range(y - 13, y + 1)}
            self.rect(x - 1, y - 17, x + 1, y - 14, Cr[1])
            self.rect(x - 2, y - 18, x + 2, y - 18, self.R("wood")[2])
        top = min(q[1] for q in body)
        for (xx, yy) in body:
            self.c.set(xx, yy, Cr[0] if yy < top + 3 else R_[2] if xx <= x + 1 else R_[1])
        self.fill({q for q in body if (q[0], q[1] + 1) not in body}, R_[0])
        self.c.set(x - 2, top + 4, R_[3])
        self.c.set(x - 2, top + 5, R_[3])
        self.c.set(x - 1, top + 1, Cr[3])

    def potions(self, x, y, w, h):
        """Витрина лавки зелий: рама, тёмная ниша, полки со склянками, свет свечи изнутри."""
        Wd, I, r = self.R("wood"), self.R("dark"), self.rng
        self.bevel(x - 6, y - 6, x + w + 6, y + h + 6, Wd)
        self.rect(x, y, x + w, y + h, I[1])
        for yy in range(y, y + h + 1):
            for xx in range(x, x + w + 1):
                d = math.hypot((xx - x - w * 0.5) / (w * 0.5), (yy - y - h * 0.55) / (h * 0.5))
                if d < 0.55 or d < 0.85 and (xx + yy) % 2:
                    self.c.set(xx, yy, I[2])
        self.dark(x, y, x + w, y + 3, 1)
        self.rect(x, y, x + 2, y + h, I[0])
        n = max(2, h // 26)
        for k in range(n):
            sy = y + (k + 1) * h // n - 3
            xx = x + 9
            while xx < x + w - 6:
                self.bottle(xx, sy - 1, r.randint(0, 2), r.choice(("glow", "red", "leaf", "gold", "moss", "pink")))
                xx += r.randint(12, 16)
            self.rect(x, sy, x + w, sy + 2, Wd[2])
            self.rect(x, sy, x + w, sy, Wd[3])
            self.rect(x, sy + 2, x + w, sy + 2, Wd[0])
        self.rect(x + w // 2 - 1, y, x + w // 2 + 1, y + h, Wd[1])
        self.rect(x + w // 2 - 1, y, x + w // 2 - 1, y + h, Wd[3])
        self.bevel(x - 9, y + h + 7, x + w + 9, y + h + 11, Wd)
        self.dark(x - 6, y + h + 12, x + w + 10, y + h + 14, 1)

    def sign(self, x, y, kind):
        """Вывеска на кованом кронштейне: колба лавки, руна гильдии или лист жилого ствола."""
        Wd, I, G = self.R("wood"), self.R("dark"), self.R("gold")
        self.rect(x - 4, y - 8, x + 30, y - 7, I[2])
        self.rect(x - 4, y - 8, x - 3, y + 4, I[2])
        for xx in (x + 3, x + 23):
            self.rect(xx, y - 6, xx, y - 1, I[3])
        self.rect(x + 2, y + 2, x + 28, y + 26, I[0])
        self.bevel(x, y, x + 26, y + 24, Wd)
        self.rect(x + 2, y + 2, x + 24, y + 22, Wd[1])
        cx, cy = x + 13, y + 12
        if kind == "flask":
            Gl = self.R("glow")
            self.fill(ellipse(cx, cy + 3, 6, 6), Gl[2])
            self.fill({q for q in ellipse(cx, cy + 3, 6, 6) if q[1] < cy + 1}, self.R("cream")[2])
            self.rect(cx - 1, cy - 8, cx + 1, cy - 3, self.R("cream")[2])
            self.rect(cx - 2, cy - 9, cx + 2, cy - 9, G[2])
            self.c.set(cx - 3, cy + 2, Gl[3])
        elif kind == "rune":
            self.rune(cx - 4, cy - 7, 4, G[2], 3)
        else:
            M = self.R("moss")
            self.put(ellipse(cx, cy, 8, 5, -35), M, soft=False, cast=False)
            for k in range(-6, 7):
                self.c.set(cx + k, cy - int(k * 0.7), M[0])

    def bracket(self, x, y, w, ramp="cream"):
        """Трутовик на коре: полка-полукруг."""
        R_ = self.R(ramp)
        S = {q for q in ellipse(x, y, w, 5) if q[1] <= y}
        self.put(S, R_, soft=True)
        self.rect(x - w + 2, y + 1, x + w - 2, y + 1, R_[0])
        self.rect(x - w + 4, y + 2, x + w - 5, y + 2, self.R("dark")[1])

    def shroom(self, x, y, h, r, ramp="glow"):
        """Гриб: светлая ножка, шляпка куполом с крапинами."""
        Cr, R_ = self.R("cream"), self.R(ramp)
        self.rect(x - 1, y - h, x + 1, y, Cr[2])
        self.rect(x + 1, y - h, x + 1, y, Cr[1])
        cap = {q for q in ellipse(x, y - h, r, r * 0.8) if q[1] <= y - h}
        self.put(cap, R_, soft=True, cast=False)
        self.rect(x - r + 1, y - h + 1, x + r - 1, y - h + 1, R_[0])
        for dx, dy in ((-r * 0.4, -r * 0.35), (r * 0.3, -r * 0.5), (0, -r * 0.15)):
            if r >= 4:
                self.c.set(x + dx, y - h + dy, Cr[3])

    def crystals(self, x, y, n=4, hmax=34, halo=True):
        """Друза кристаллов: шпили веером, светлая грань слева, тёмная справа, свечение на стене."""
        G, r = self.R("glow"), self.rng
        if halo:
            self.halo(x, y - hmax * 0.5, n * 7 + 14, hmax * 0.8)
        spires = []
        for k in range(n):
            t = (k - (n - 1) / 2.0) / max(1.0, (n - 1) / 2.0)
            spires.append((abs(t), x + t * n * 4.5, hmax * (1.0 - 0.45 * abs(t)) * r.uniform(0.8, 1.0), t * 0.5, r.randint(4, 6)))
        for (_, bx, hh, lean, bw) in sorted(spires, reverse=True):
            tip = (bx + lean * hh, y - hh)
            mid = (bx + lean * hh * 0.8, y - hh * 0.8)
            left = poly([(bx - bw, y), (bx, y), mid, tip, (mid[0] - bw * 0.9, mid[1] + 1)])
            right = poly([(bx, y), (bx + bw, y), (mid[0] + bw * 0.9, mid[1] + 1), tip, mid])
            self.fill(right, G[1])
            self.fill(left, G[2])
            self.fill({q for q in right if (q[0] + 1, q[1]) not in right and q not in left}, G[0])
            self.fill({q for q in left if (q[0] - 1, q[1]) not in left}, G[3])
            for t in range(2, int(hh * 0.7), 5):
                self.c.set(bx - 1 + lean * t, y - t, G[3])

    def portal(self, x0, x1, top, by):
        """Рунная арка портала: клинчатые камни с горящими рунами, замок с золотом, в проёме вихрь."""
        S_, G, L, N, Au = self.R("stone"), self.R("glow"), self.R("leaf"), self.R("night"), self.R("gold")
        r = self.rng
        cx, hw = (x0 + x1) / 2.0, (x1 - x0) / 2.0
        outer = arch_mask(x0 - 20, x1 + 20, top - 20, by)
        inner = arch_mask(x0, x1, top, by)
        ring = outer - inner
        self.halo(cx, top + hw, hw + 46, hw + 40)
        self.put(ring, S_, soft=True)
        cy = top + hw
        # Швы клинчатых камней и руны на них.
        for k in range(13):
            a = math.pi + k * math.pi / 12
            for t in range(int(hw), int(hw) + 21):
                q = (int(round(cx + math.cos(a) * t)), int(round(cy + math.sin(a) * t)))
                if q in ring:
                    self.c.set(q[0], q[1], S_[0])
                    if (q[0] + 1, q[1]) in ring:
                        self.c.set(q[0] + 1, q[1], S_[3])
            if k < 12:
                am = a + math.pi / 24
                q = (int(round(cx + math.cos(am) * (hw + 10))), int(round(cy + math.sin(am) * (hw + 10))))
                self.rune(q[0] - 1, q[1] - 2, k, G[2] if k % 2 else G[3])
        for yy in range(int(cy) + 14, by - 6, 24):
            for (a, b) in ((x0 - 20, x0 - 1), (x1 + 1, x1 + 20)):
                self.rect(a, yy, b, yy, S_[0])
                self.rect(a, yy + 1, b, yy + 1, S_[3])
                self.rune(a + 9, yy + 8, yy // 24 + a, G[2])
        key = poly([(cx - 9, top - 24), (cx + 9, top - 24), (cx + 6, top + 2), (cx - 6, top + 2)])
        self.put(key, Au, soft=True)
        self.fill(ellipse(cx, top - 11, 3, 4), G[2])
        self.c.set(cx - 1, top - 13, G[3])
        # Вихрь: рукава спирали от тёмно-лилового к бирюзе, яркая сердцевина, искры.
        for (x, y) in inner:
            dx, dy = x - cx, (y - cy - 20) * 0.8
            d = math.hypot(dx, dy)
            v = math.sin(math.atan2(dy, dx) * 3.0 + d * 0.16)
            if d < 9:
                col = G[3]
            elif d < 16:
                col = G[3] if v > 0 or (x + y) % 2 else G[2]
            elif v > 0.72:
                col = G[3] if d < 44 else G[2]
            elif v > 0.3:
                col = G[2] if d < 60 else G[1]
            elif v > -0.2:
                col = L[2] if d < 70 or (x + y) % 2 else L[1]
            elif v > -0.65:
                col = L[1]
            else:
                col = N[0] if d > 30 else L[0]
            self.c.set(x, y, col)
        for _ in range(60):
            q = (r.randint(x0, x1), r.randint(top, by))
            if q in inner:
                self.c.set(q[0], q[1], self.R("cream")[3])
        self.fill({q for q in inner if (q[0] - 4, q[1] - 4) not in inner}, N[0])
        self.fill({q for q in inner if (q[0] - 4, q[1] - 4) in inner and (q[0] - 6, q[1] - 6) not in inner
                   and (q[0] + q[1]) % 2}, N[0])
        self.bevel(x0 - 30, by + 1, x1 + 30, by + 6, S_)

    def vista(self, x0, x1, y0, y1):
        """Просвет между стволами: сумеречное небо, великое дерево вдали, летающие острова с
        водопадами и башней мага, облака под ними."""
        N, P_, L, M, S_, G, r = (self.R("night"), self.R("pink"), self.R("leaf"), self.R("moss"), self.R("stone"),
                                 self.R("glow"), self.rng)
        tones = [N[0], N[1], N[2], L[2], P_[1], P_[2], P_[3]]
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                k = (y - y0) / float(y1 - y0) * (len(tones) - 1.01)
                i = int(k)
                self.c.set(x, y, tones[i + 1] if (k - i) > 0.5 + 0.25 * (1 if (x + y) % 2 else -1) else tones[i])
        for _ in range(40):
            self.c.set(r.randint(x0, x1), r.randint(y0, y0 + (y1 - y0) // 2), self.R("cream")[3])
        cx = (x0 + x1) // 2
        # Великое дерево на горизонте.
        tree = capsule((cx + 34, y1), (cx + 30, y1 - 70), 7, 4) | ellipse(cx + 30, y1 - 86, 30, 20) \
            | ellipse(cx + 8, y1 - 74, 16, 11) | ellipse(cx + 52, y1 - 72, 14, 10)
        self.fill({q for q in tree if x0 <= q[0] <= x1 and y0 <= q[1] <= y1}, L[1])
        self.fill({q for q in tree if x0 <= q[0] <= x1 and (q[0] - 2, q[1] - 2) not in tree}, L[2])

        def island(ix, iy, w, tower=False, fall=True):
            top = ellipse(ix, iy, w, 4)
            base = poly([(ix - w, iy), (ix + w, iy), (ix + w * 0.35, iy + w * 0.9), (ix - w * 0.2, iy + w * 1.2),
                         (ix - w * 0.6, iy + w * 0.5)])
            for (x, y) in base:
                if x0 <= x <= x1:
                    self.c.set(x, y, S_[1] if x < ix or (x + y) % 2 else S_[0])
            for (x, y) in top:
                if x0 <= x <= x1:
                    self.c.set(x, y, M[3] if y < iy - 1 else M[2] if y <= iy else M[1])
            for k in range(-1, 2):
                tx = ix + k * w * 0.5
                self.fill({q for q in ellipse(tx, iy - 7, 5, 5) if x0 <= q[0] <= x1}, L[2])
                self.fill({q for q in ellipse(tx - 1, iy - 8, 3, 3) if x0 <= q[0] <= x1}, L[3])
                self.rect(tx, iy - 3, tx, iy - 1, self.R("bark")[1])
            if tower:
                self.rect(ix - 3, iy - 26, ix + 3, iy - 1, S_[2])
                self.rect(ix + 2, iy - 26, ix + 3, iy - 1, S_[1])
                self.fill(poly([(ix - 5, iy - 26), (ix + 5, iy - 26), (ix, iy - 38)]), L[1])
                self.rect(ix - 1, iy - 21, ix, iy - 18, self.R("warm")[3])
                self.rect(ix - 1, iy - 11, ix, iy - 9, self.R("warm")[2])
            if fall:
                fx = ix + w * 0.5
                for y in range(iy + 1, iy + 46):
                    if x0 <= fx <= x1 and y <= y1 and (y < iy + 30 or y % 2):
                        self.c.set(fx, y, G[3] if y < iy + 16 else G[2])
                        if y < iy + 22:
                            self.c.set(fx + 1, y, G[2])

        island(cx - 22, y0 + 74, 26, tower=True)
        island(cx + 26, y0 + 40, 13, fall=False)
        island(cx - 40, y0 + 132, 12)
        for (ex, ey, rx) in ((cx - 30, y1 - 8, 34), (cx + 30, y1 - 4, 40), (cx, y1 - 18, 22)):
            S = {q for q in ellipse(ex, ey, rx, 7) if x0 <= q[0] <= x1 and q[1] <= y1}
            self.fill(S, P_[3])
            self.fill({q for q in S if (q[0], q[1] + 2) not in S}, P_[2])

    # Предметы у стены -------------------------------------------------------------------------

    def stump(self, x, y, w=22, h=20):
        """Пень: кора с бороздами, срез с годовыми кольцами, корни в стороны, мох."""
        B, Wd, M = self.R("bark"), self.R("wood"), self.R("moss")
        hw = w // 2
        S = {(xx, yy) for xx in range(x - hw, x + hw + 1) for yy in range(y - h, y + 1)}
        S |= poly([(x - hw - 5, y), (x - hw, y - 7), (x - hw, y)]) | poly([(x + hw + 5, y), (x + hw, y - 7), (x + hw, y)])
        self.put(S, B, soft=True)
        for xx in range(x - hw + 3, x + hw - 1, 4):
            self.rect(xx, y - h + 4, xx, y - 2, B[1])
        top = ellipse(x, y - h, hw, 4)
        self.put(top, Wd, soft=False)
        self.fill(ellipse(x, y - h, hw - 3, 2.4) - ellipse(x, y - h, hw - 4.5, 1.6), Wd[1])
        self.c.set(x, y - h, Wd[1])
        for xx in range(x - hw, x - hw + 8):
            self.c.set(xx, y - h + 4 + (xx % 2), M[2])
            self.c.set(xx, y - h + 5 + (xx % 2), M[1])

    def hamper(self, x, y, w=30, h=24):
        """Плетёный короб: лоза в шахмат, обручи, крышка с ручкой."""
        Wd, G, B = self.R("wood"), self.R("gold"), self.R("bark")
        self.rect(x - 1, y - h - 1, x + w + 1, y + 1, 0)
        for yy in range(y - h, y + 1):
            for xx in range(x, x + w + 1):
                k = ((xx - x) // 3 + (yy - y + h) // 2) % 2
                t = Wd[3] if k and (yy - y + h) % 2 == 0 else Wd[2] if k else Wd[1]
                self.c.set(xx, yy, t)
        self.rect(x + w - 2, y - h, x + w, y, Wd[0])
        for yy in (y - h + 7, y - 4):
            self.rect(x, yy, x + w, yy, B[1])
            self.rect(x, yy - 1, x + w, yy - 1, G[1])
        self.bevel(x - 1, y - h - 4, x + w + 1, y - h, Wd)
        handle = ellipse(x + w / 2.0, y - h - 4, 6, 5) - ellipse(x + w / 2.0, y - h - 4, 4, 3)
        self.fill({q for q in handle if q[1] < y - h - 4}, B[2])

    def runestone(self, x, y, w=14, h=24, i=0):
        """Рунный камень: тёсаный столбик со скруглённым верхом, горящая руна, мох у основания."""
        S_, G, M = self.R("stone"), self.R("glow"), self.R("moss")
        hw = w // 2
        S = poly([(x - hw, y), (x + hw, y), (x + hw - 2, y - h + 5), (x - hw + 2, y - h + 5)]) | ellipse(x, y - h + 5, hw - 2, 5)
        self.put(S, S_, soft=True)
        self.rune(x - 2, y - h + 6, i, G[3], 2)
        self.rune(x - 1, y - h + 7, i, G[2], 2)
        for xx in range(x - hw - 1, x + hw + 2):
            self.c.set(xx, y - (xx % 3), M[2])
            self.c.set(xx, y, M[1])

    def shrooms(self, x, y):
        self.shroom(x - 8, y, 7, 5, "red")
        self.shroom(x + 7, y, 9, 6, "glow")
        self.shroom(x, y, 15, 8, "leaf")
        self.shroom(x + 13, y, 4, 3, "glow")


def build_street():
    """Тропа под великим деревом той же ширины и с теми же строками пола, что улица пиратов:
    стена до `WALL_Y`, рунные плиты во мху до `CURB_Y`, каменный бордюр, тропа от `ROAD_Y`."""
    st = Grove()
    c, rng = st.c, st.rng
    S_, Wd, M, G, B, I = st.R("stone"), st.R("wood"), st.R("moss"), st.R("glow"), st.R("bark"), st.R("dark")
    x = 0
    st.canopy(0, SW - 1)
    modules = [("hollow", 320), ("alchemy", 288), ("portal", 352), ("guild", 256), ("grotto", 256), ("vista", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        if kind == "hollow":
            # Жилой ствол: круглая дверь, два окна со светом, трутовики, лианы, вывеска.
            st.bark(x0, 32, x1, WALL_Y)
            st.dark(x0, 32, x1, 38, 1)
            st.round_window(x0 + 58, 112, 24)
            st.round_door(x0 + 160, WALL_Y - 4, 50)
            st.round_window(x0 + 262, 104, 19)
            st.sign(x0 + 98, 62, "leaf")
            for (bx, by, bw) in ((x0 + 24, 176, 12), (x0 + 30, 190, 8), (x0 + 286, 160, 11), (x0 + 240, 196, 9)):
                st.bracket(bx, by, bw, "cream" if bw != 11 else "warm")
            st.liana(x0 + 12, 30, 150)
            st.liana(x0 + 140, 30, 70, False)
            st.liana(x0 + 222, 30, 120)
            st.liana(x1 - 8, 30, 176)
            st.bell(x0 + 200, 30, 22)
            st.shroom(x0 + 232, WALL_Y, 9, 6, "red")
            st.shroom(x0 + 242, WALL_Y, 5, 4, "red")
        elif kind == "alchemy":
            # Лавка зелий: кладка, витрина со склянками, дверь, вывеска с колбой, котёл у стены.
            st.masonry(x0, 32, x1, WALL_Y, 44, 22)
            st.dark(x0, 32, x1, 38, 1)
            st.potions(x0 + 30, 96, 124, 86)
            st.arch_door(x0 + 200, 104, 50, WALL_Y - 110)
            st.sign(x0 + 160, 60, "flask")
            st.liana(x0 + 10, 30, 130)
            st.liana(x1 - 14, 30, 96)
            st.bell(x0 + 92, 30, 20)
            # Котёл с бурлящим зельем.
            kx, ky = x0 + 172, WALL_Y - 2
            st.put(ellipse(kx, ky - 13, 15, 13), I, soft=True)
            st.fill(ellipse(kx, ky - 24, 12, 3), G[2])
            st.fill(ellipse(kx - 3, ky - 25, 5, 1.4), G[3])
            st.rect(kx - 14, ky - 23, kx + 14, ky - 22, I[3])
            for (bx, by) in ((kx - 5, ky - 31), (kx + 4, ky - 36), (kx - 1, ky - 43)):
                st.fill(ellipse(bx, by, 2, 2) - ellipse(bx, by, 1, 1), G[3])
            st.rect(kx - 10, ky, kx - 8, ky + 2, I[1])
            st.rect(kx + 8, ky, kx + 10, ky + 2, I[1])
        elif kind == "portal":
            # Рунная арка портала в кладке, кристаллы на постаментах, знамёна.
            st.masonry(x0, 32, x1, WALL_Y, 56, 24, runes=0.1)
            st.dark(x0, 32, x1, 38, 1)
            st.portal(x0 + 96, x0 + 256, 74, WALL_Y)
            for px in (x0 + 38, x1 - 38):
                st.bevel(px - 16, WALL_Y - 26, px + 16, WALL_Y, S_)
                st.bevel(px - 19, WALL_Y - 30, px + 19, WALL_Y - 26, S_)
                st.rune(px - 3, WALL_Y - 20, px, G[2], 2)
                st.crystals(px, WALL_Y - 31, 5, 44)
            st.banner(x0 + 26, 62, 24, 62, "leaf", 2)
            st.banner(x1 - 50, 62, 24, 62, "leaf", 5)
            st.liana(x0 + 6, 30, 110)
            st.liana(x1 - 6, 30, 140)
        elif kind == "guild":
            # Зал гильдии: два звёздных окна, дверь, знамёна, вывеска с руной.
            st.masonry(x0, 32, x1, WALL_Y, 40, 20, moss=0.08)
            st.dark(x0, 32, x1, 38, 1)
            st.rect(x0, 56, x1, 61, S_[1])
            st.rect(x0, 56, x1, 56, S_[3])
            st.rect(x0, 61, x1, 61, S_[0])
            st.star_window(x0 + 26, 96, 40, 84)
            st.star_window(x0 + 190, 96, 40, 84)
            st.arch_door(x0 + 104, 100, 48, WALL_Y - 106, "bark")
            st.banner(x0 + 76, 74, 18, 54, "red", 3)
            st.banner(x0 + 162, 74, 18, 54, "red", 6)
            st.sign(x0 + 115, 44, "rune")
            st.bell(x0 + 16, 30, 26)
            st.bell(x0 + 244, 30, 18)
            st.liana(x1 - 4, 30, 100)
        elif kind == "grotto":
            # Грот: скала, друзы кристаллов, светящиеся грибы, рунный камень в нише, струйка воды.
            st.rock(x0, 32, x1, WALL_Y)
            st.dark(x0, 32, x1, 40, 1)
            hole = arch_mask(x0 + 84, x0 + 172, 96, WALL_Y)
            st.fill(hole, I[0])
            st.fill({q for q in hole if (q[0] + 5, q[1] - 5) in hole and (q[0] + q[1]) % 2 and q[1] > 150}, I[1])
            st.crystals(x0 + 128, WALL_Y - 2, 5, 56)
            st.crystals(x0 + 40, WALL_Y - 4, 4, 38)
            st.crystals(x0 + 218, WALL_Y - 2, 3, 30)
            st.crystals(x0 + 196, 84, 3, 18, halo=False)
            st.crystals(x0 + 60, 70, 3, 14, halo=False)
            for yy in range(40, WALL_Y):
                xx = x0 + 236 + int(round(math.sin(yy * 0.09) * 2))
                c.set(xx, yy, G[3] if yy % 3 else G[2])
                c.set(xx + 1, yy, G[1])
            for (sx, sy, sh_, sr) in ((x0 + 14, WALL_Y, 8, 6), (x0 + 24, WALL_Y, 5, 4), (x0 + 180, WALL_Y, 7, 5),
                                      (x0 + 248, WALL_Y, 6, 5)):
                st.shroom(sx, sy, sh_, sr, "glow")
            st.liana(x0 + 100, 30, 70)
            st.liana(x0 + 150, 30, 58, False)
        elif kind == "vista":
            # Просвет: два ствола по краям, между ними небо с островами, перила из жердей и каната.
            st.bark(x0, 32, x0 + 30, WALL_Y)
            st.bark(x1 - 30, 32, x1, WALL_Y)
            st.vista(x0 + 31, x1 - 31, 32, WALL_Y)
            st.dark(x0 + 31, 32, x0 + 34, WALL_Y, 1)
            st.dark(x0 + 31, 32, x1 - 31, 40, 1, dither=True)
            for px in range(x0 + 34, x1 - 30, 31):
                st.rect(px, WALL_Y - 34, px + 4, WALL_Y, Wd[2])
                st.rect(px, WALL_Y - 34, px, WALL_Y, Wd[3])
                st.rect(px + 4, WALL_Y - 34, px + 4, WALL_Y, Wd[0])
                st.rect(px - 1, WALL_Y - 36, px + 5, WALL_Y - 34, Wd[3])
                if px + 31 < x1 - 30:
                    for k in range(5, 31):
                        sag = int(round(4 * math.sin((k - 5) / 26.0 * math.pi)))
                        c.set(px + k, WALL_Y - 28 + sag, st.R("gold")[1])
                        c.set(px + k, WALL_Y - 14 + sag, st.R("gold")[1] if k % 3 else Wd[0])
            st.liana(x0 + 40, 30, 96)
            st.liana(x1 - 42, 30, 64)
            st.bell(x0 + 96, 30, 14)
            st.bracket(x0 + 18, 150, 9)
            st.bracket(x1 - 14, 120, 8, "warm")
        x += w
    # Тень у основания стены.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Полоса у стены: рунные плиты рядами, швы во мху, на части плит резные руны.
    Sl = st.R("slab")
    st.rect(0, WALL_Y + 1, SW - 1, CURB_Y - 1, M[0])
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        xx = -((ri * 23) % 48)
        while xx < SW:
            w = rng.randint(40, 58)
            a, b = max(xx + 1, 0), min(xx + w - 2, SW - 1)
            yb = min(y0 + h - 2, CURB_Y - 1)
            if b - a > 4:
                ramp = Sl if rng.random() < 0.7 else [Sl[0], Sl[1], Sl[1], Sl[2]]
                st.bevel(a, y0, b, yb, ramp)
                st.noise(a + 1, y0 + 1, b - 1, yb - 1, ramp, 0.04)
                for (qx, qy) in ((a, y0), (b, y0), (a, yb), (b, yb)):
                    c.set(qx, qy, M[1])
                v = rng.random()
                if v < 0.3 and b - a > 16:
                    rx, ry = (a + b) // 2 - 3, y0 + (yb - y0) // 2 - 4
                    k = rng.randint(0, 7)
                    if v < 0.07:
                        st.rune(rx, ry, k, G[1], 2)
                    else:
                        st.rune(rx + 1, ry + 1, k, ramp[3], 2)
                        st.rune(rx, ry, k, ramp[0], 2)
                elif v < 0.5:
                    sx = rng.randint(a + 3, max(a + 4, b - 10))
                    for k in range(rng.randint(4, 9)):
                        c.set(sx + k, y0 + 3 + (k * 5) % max(1, yb - y0 - 5), ramp[1])
                # Мох наползает на край плиты.
                if rng.random() < 0.5:
                    for k in range(a, a + rng.randint(4, 14)):
                        for d in range(rng.randint(0, 2)):
                            c.set(k, yb - d, M[2 if d else 1])
            xx += w
    for _ in range(90):
        fx_, fy_ = rng.randint(0, SW - 1), rng.randint(WALL_Y + 6, CURB_Y - 3)
        if c.get(fx_, fy_) in (M[0], M[1]):
            c.set(fx_, fy_, st.R("pink")[rng.choice((2, 3))])
            c.set(fx_, fy_ + 1, M[2])
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Бордюр: тёсаные камни, на каждом четвёртом горит руна.
    for xx in range(SW):
        c.set(xx, CURB_Y, S_[3])
        c.set(xx, CURB_Y + 1, S_[2])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, S_[0] if xx % 32 == 0 else S_[2] if xx % 32 == 1 else S_[1])
    for k, xx in enumerate(range(0, SW, 32)):
        if k % 4 == 1:
            st.rune(xx + 14, CURB_Y + 3, k, G[3])
            st.light({(xx + 14 + dx, CURB_Y + 2 + dy) for dx in range(-3, 6) for dy in range(0, 7)})
            st.rune(xx + 14, CURB_Y + 3, k, G[3])
        elif k % 2 == 0:
            for d in range(rng.randint(2, 5)):
                c.set(xx + 6 + d * 3, CURB_Y + rng.randint(0, 2), M[2])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, I[0])
    # Тропа: каменные плиты рядами, ряды к зрителю выше, сбитые углы, трещины, мох в швах.
    E = st.R("earth")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, E[0])
    y = ROAD_Y + 2
    h = 14
    row = 0
    while y < SH:
        pw = 50 + row * 6
        xx = -((row * 19) % pw)
        while xx < SW:
            w = pw + rng.randint(-10, 10)
            a, b = max(xx + 1, 0), min(xx + w - 2, SW - 1)
            yb = min(y + h - 2, SH - 1)
            if b - a > 3 and yb > y:
                t = rng.choice((0, 0, 0, 1))
                ramp = E if t == 0 else [E[0], E[1], E[1], E[2]]
                st.bevel(a, y, b, yb, ramp)
                st.noise(a + 1, y + 1, b - 1, yb - 1, ramp, 0.04)
                for (qx, qy) in ((a, y), (b, y), (a, yb), (b, yb)):
                    c.set(qx, qy, E[0])
                if rng.random() < 0.3 and b - a > 20:
                    sx, sy = rng.randint(a + 5, b - 12), y + 2
                    for k in range(min(yb - y - 3, rng.randint(4, 10))):
                        sx += rng.choice((-1, 0, 1, 1))
                        c.set(sx, sy + k, ramp[1])
                        c.set(sx + 1, sy + k, ramp[3])
                if rng.random() < 0.4:
                    for k in range(a, min(b, a + rng.randint(5, 18))):
                        c.set(k, yb + 1, M[1])
                        if rng.random() < 0.4:
                            c.set(k, yb, M[2])
            xx += w
        y += h
        h += 3
        row += 1
    # Руны вдоль бордюра едва светятся на плитах тропы.
    for k, xx in enumerate(range(18, SW, 104)):
        st.rune(xx, ROAD_Y + 5, k, G[0], 2)
        st.rune(xx, ROAD_Y + 5, k + 3, G[1], 1)
    # Моховые кочки с цветами на местах луж пиратов.
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            e = c.get(px, py)
            if e is None:
                continue
            c.set(px, py, M[2] if e == E[3] else M[1] if e in (E[2], E[1]) else M[0])
        for k in range(px0 - 30, px0 + 40, 11):
            c.set(k, 370 + (k % 5), st.R("pink")[3])
            c.set(k + 1, 370 + (k % 5), st.R("pink")[2])
            c.set(k + 5, 374 + (k % 3), st.R("cream")[3])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for n, (kind, px) in enumerate((("stump", 20), ("stump", 44), ("hamper", 290), ("stone", 600), ("stone", 618),
                                    ("shrooms", 680), ("hamper", 870), ("hamper", 898), ("stump", 1150),
                                    ("shrooms", 1400), ("stump", 1590))):
        yb = WALL_Y + 8
        if kind == "stump":
            st.stump(px, yb, 22 if n % 2 == 0 else 18, 22 if n % 2 == 0 else 15)
        elif kind == "stone":
            st.runestone(px, yb, 14, 26 if n % 2 else 20, n)
        elif kind == "hamper":
            st.hamper(px, yb, 26, 22 if n % 2 == 0 else 17)
        else:
            st.shrooms(px, yb)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки ударов розово-лиловой магией, волна бирюзой кристалла, пыль
    сиреневая; стрелка «вперёд» золотая, как руна-бонус, чтобы не терялась в сумерках."""
    p = Pal(OUTLINE)
    p.add("white", [0xC8B8E0, 0xE8DCF4, 0xFAF4FF, 0xFFFFFF])
    if go:
        p.add("gold", [0x9A5A10, 0xD8962C, 0xF6D058, 0xFFF6C0])
    else:
        p.add("gold", [0x7A2A8E, 0xB850D0, 0xEE94F0, 0xFFE4FF])
    p.add("blue", [0x1E6A7A, 0x2AA8A0, 0x3AD4C2, 0xC8F8EC])
    p.add("dust", [0x4E4660, 0x7A7090, 0xA69CB8, 0xD0C8DC])
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


def preview(path):
    """Листы для просмотра: лист всех лент выше 1500 пикселей, поэтому делится на три файла:
    герой и два врага, босс с лицами, улица с эффектами (суффиксы `_b`, `_c`)."""
    import fantasy16
    items = sprites_own()
    root, ext = os.path.splitext(path)
    groups = (("", ("brawl_hero", "brawl_thug", "brawl_knife")),
              ("_b", ("brawl_boss",) + tuple(k for k in items if k.startswith("brawl_face_"))),
              ("_c", tuple(k for k in items if k == "brawl_street" or k.startswith("brawl_fx") or k == "brawl_go")))
    for suffix, keys in groups:
        fantasy16.save_sheet(root + suffix + ext, {k: items[k] for k in keys}, scale=1, max_w=FW * 12)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
