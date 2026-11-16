# -*- coding: utf-8 -*-
"""Набор «Сладости» для битемапа × 16/32-bit (#137): зеркало `pixel_brawl16.py` и
`space_brawl16.py`. Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты из
`pixel_brawl16` как есть (демка `fighting_bit16.gd` рассчитана на них), рисунок частей тела,
палитры и улица свои; цвета и облик героя из основы `sweets16.py`.

Бойцы: герой это пряничный человечек: круглая голова с белой улыбкой глазурью, красный бантик
под подбородком, две пуговицы-драже, кайма глазури у кистей и ступней; громила это
пончик-здоровяк: туловище пончиком в розовой глазури с посыпкой и дыркой, на макушке вишня; враг
с ножом это боец с карамельной тростью: полосатые рукава и штаны, ягодный жилет, хвост фантика на
затылке, трость крюком вперёд; босс это шоколадный король: торс плиткой шоколада с потёками
глазури, белые усы и борода, корона из глазури с драже, малиновая мантия в кремовой опушке.
Улица это квартал карамельной страны: пряничная пекарня, лавка под полосатым навесом, ворота
шоколадной фабрики, вафельный дом, киоск мороженого и проулок с видом на горы мороженого;
тротуар плитками печенья, бордюр карамельной полосой, мостовая мятной глазурью.

    python3 tools/sweets_brawl16.py --preview out.png [--keys=a,b]   # лист всех лент
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

# Обводка: горький шоколад, как `sweets16.PALETTE[K]`.
OUTLINE = 0x2B161E

# Рампы по четыре тона вокруг цветов `sweets16.PALETTE`.
R_BREAD = [0x6A3418, 0x945228, 0xC9803E, 0xE8AC6A]
R_ICING = [0xA890A4, 0xD6BFCC, 0xFFF7EC, 0xFFFFFF]
R_RED = [0x7A1430, 0xB7243A, 0xE63545, 0xFF8490]
R_MINT = [0x2F6C94, 0x3FA99C, 0x86DBBE, 0xD3F6E4]
R_PINK = [0x7A2450, 0xB73A70, 0xFF8EB6, 0xFFC8DC]
R_CHOCO = [0x341A1C, 0x4A2826, 0x7C4838, 0xA86C50]
R_GOLD = [0x8A5418, 0xD09038, 0xF8CF6A, 0xFFF0B0]
R_EYE = [0x1A0C12, 0x2B161E, 0x4A2826, 0xFFFFFF]


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("bread", R_BREAD)
    p.add("icing", R_ICING)
    p.add("red", R_RED)
    p.add("mint", R_MINT)
    p.add("pink", R_PINK)
    p.add("eye", R_EYE)
    return Look("ginger", p, Body(1.0, 1.12))


def thug_look():
    p = Pal(OUTLINE)
    p.add("dough", [0x7A4418, 0xB8742C, 0xE8AC54, 0xFFD68C])
    p.add("glaze", R_PINK)
    p.add("choco", R_CHOCO)
    p.add("icing", R_ICING)
    p.add("mint", R_MINT)
    p.add("gold", R_GOLD)
    p.add("red", R_RED)
    p.add("eye", R_EYE)
    return Look("donut", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x9A5E4C, 0xD69A7C, 0xF8D2AE, 0xFFF0DC])
    p.add("red", R_RED)
    p.add("icing", R_ICING)
    p.add("vest", [0x3A1C60, 0x623A9C, 0x9466D0, 0xC4A2F0])
    p.add("choco", R_CHOCO)
    p.add("gold", R_GOLD)
    p.add("eye", R_EYE)
    return Look("cane", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("choco", [0x3E2020, 0x5C3428, 0x8A5440, 0xB88060])
    p.add("dark", [0x1E1014, 0x341A1C, 0x4E2C28, 0x70443A])
    p.add("icing", R_ICING)
    p.add("mantle", [0x5A1438, 0x8E2250, 0xC23C74, 0xEE74A2])
    p.add("gold", R_GOLD)
    p.add("mint", R_MINT)
    p.add("red", R_RED)
    p.add("eye", R_EYE)
    return Look("king", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _stripes(pal, a, d, w=3.2, slant=0.7, ra="red", rb="icing"):
    """Материал карамельной трости: косые полосы поперёк оси `d` от точки `a`."""
    n = (-d[1], d[0])

    def mat(x, y):
        dx, dy = x - a[0], y - a[1]
        t = dx * d[0] + dy * d[1] + (dx * n[0] + dy * n[1]) * slant
        return pal[ra] if int(math.floor(t / w)) % 2 == 0 else pal[rb]

    return mat


def _band(S, center, d, half):
    """Поясок поперёк конечности: пиксели маски `S` не дальше `half` от точки вдоль оси `d`."""
    return {q for q in S if abs((q[0] - center[0]) * d[0] + (q[1] - center[1]) * d[1]) <= half}


def _drip(lx):
    """Неровный край потёка глазури вдоль оси, в пикселях."""
    return 2.2 * math.sin(lx * 0.62) + 1.4 * math.sin(lx * 0.27 + 1.0) + (2.4 if int(math.floor(lx / 4.0)) % 3 == 0 else 0.0)


def _cane(c, look, fist, d):
    """Карамельная трость вдоль предплечья вперёд: стержень в красно-белую полосу и крюк на
    конце, загнутый вверх и назад. Длина как у ножа пиратов и жезла пришельца."""
    pal, s = look.pal, look.body.s
    n = (d[1], -d[0])
    r = 3.0 * s
    pts = []
    k = -3.0
    while k <= 10.0 * s:
        pts.append(add(fist, d, k))
        k += 0.5
    end = add(fist, d, 10.0 * s)
    cen = add(end, n, r)
    a = 0.0
    while a <= 215.0:
        ra = math.radians(a)
        pts.append((cen[0] - n[0] * r * math.cos(ra) + d[0] * r * math.sin(ra),
                    cen[1] - n[1] * r * math.cos(ra) + d[1] * r * math.sin(ra)))
        a += 9.0
    owner = {}
    for i, q in enumerate(pts):
        for cell in ellipse(q[0], q[1], 1.35, 1.35):
            dist = (cell[0] - q[0]) ** 2 + (cell[1] - q[1]) ** 2
            if cell not in owner or dist < owner[cell][0]:
                owner[cell] = (dist, i)
    S = set(owner)
    put(c, pal, S, None, cast=False, mat=lambda x, y: pal["red"] if (owner[(x, y)][1] // 6) % 2 == 0 else pal["icing"])


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    ud = _unit(sh, el)
    if kind == "ginger":
        # Рука пряника: толстая, с круглым концом без кисти и каймой глазури перед ним.
        upper = capsule(sh, el, 4.8 * s * b, 4.2 * s * b) | ellipse(sh[0], sh[1] + 1, 5.2 * s * b, 4.8 * s * b)
        put(c, pal, upper, pal["bread"], far=far, soft=True)
        end = add(ha, d, 1.6 * s)
        fore = capsule(el, end, 4.2 * s * b, 3.9 * s * b)
        put(c, pal, fore, pal["bread"], far=far, soft=True)
        cuff = _band(fore, add(ha, d, -1.8 * s), d, 1.2 * s)
        put(c, pal, cuff, pal["icing"], far=far, cast=False)
        if not far:
            # Зигзаг глазури на плече.
            nrm = (-ud[1], ud[0])
            for k in range(-4, 5):
                q = add(add(lerp(sh, el, 0.5), nrm, k * 0.9 * s), ud, (1.2 if k % 2 else -1.2) * s)
                if (round(q[0]), round(q[1])) in upper:
                    c.set(q[0], q[1], pal["icing"][2])
        return
    if kind == "donut":
        upper = capsule(sh, el, 4.4 * s * b, 3.6 * s * b) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b, 4.5 * s * b)
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.3 * s * b, 3.6 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
        put(c, pal, upper, pal["dough"], far=far, soft=True)
        # Наплыв глазури на плече: шапка сверху и короткий потёк.
        cap = {q for q in ellipse(sh[0], sh[1] + 0.5, 5.4 * s * b, 5.0 * s * b)
               if (q[0] - sh[0]) * ud[0] + (q[1] - sh[1]) * ud[1] < 1.5 * s + _drip(q[0] + q[1]) * 0.6}
        put(c, pal, cap & (upper | cap), pal["glaze"], far=far, cast=False)
        fore = capsule(el, ha, 3.7 * s * b, 3.1 * s * b)
        put(c, pal, fore, pal["dough"], far=far)
        # Шоколадный напульсник с белой строчкой.
        band = capsule(add(ha, d, -7.5 * s), add(ha, d, -3.2 * s), 4.1 * s * b, 3.8 * s * b)
        put(c, pal, band, pal["choco"], far=far)
        q = add(ha, d, -5.4 * s)
        c.set(q[0], q[1], pal["icing"][1 if far else 2])
        fist = add(ha, d, 1.4 * s)
        fs = ellipse(fist[0], fist[1], 3.4 * s * 1.3, 3.1 * s * 1.3)
        put(c, pal, fs, pal["dough"], far=far)
        return
    if kind == "cane":
        upper = capsule(sh, el, 4.3 * s * b, 3.5 * s * b) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b, 4.5 * s * b)
        put(c, pal, upper, None, far=far, soft=True, mat=_stripes(pal, sh, ud))
        fore = capsule(el, ha, 3.6 * s * b, 3.0 * s * b)
        put(c, pal, fore, None, far=far, mat=_stripes(pal, el, d))
        # Ягодный наплечник жилета.
        put(c, pal, ellipse(sh[0], sh[1], 4.9 * s * b, 3.6 * s * b), pal["vest"], far=far, cast=False)
        fist = add(ha, d, 1.2 * s)
        fs = ellipse(fist[0], fist[1], 3.4 * s * b, 3.1 * s * b)
        put(c, pal, fs, pal["skin"], far=far)
        if side == "n":
            _cane(c, look, fist, d)
            # Пальцы поверх трости.
            put(c, pal, ellipse(fist[0], fist[1], 2.6 * s * b, 2.4 * s * b), pal["skin"], cast=False)
        return
    # Король: шоколадные руки, потёк глазури с плеча, карамельная манжета.
    upper = capsule(sh, el, 4.3 * s * b, 3.5 * s * b) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b, 4.5 * s * b)
    put(c, pal, upper, pal["choco"], far=far, soft=True)
    cap = {q for q in ellipse(sh[0], sh[1] + 0.5, 5.3 * s * b, 5.0 * s * b)
           if (q[0] - sh[0]) * ud[0] + (q[1] - sh[1]) * ud[1] < 1.0 * s + _drip(q[0] - q[1]) * 0.7}
    put(c, pal, cap, pal["icing"], far=far, cast=False)
    fore = capsule(el, ha, 3.6 * s * b, 3.0 * s * b)
    put(c, pal, fore, pal["choco"], far=far)
    put(c, pal, _band(fore, add(ha, d, -3.4 * s), d, 1.6 * s), pal["gold"], far=far, cast=False)
    fist = add(ha, d, 1.2 * s)
    fr = min(b, 1.15)
    put(c, pal, ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr), pal["choco"], far=far)


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    if kind == "ginger":
        # Нога пряника: толстая, ступня коротким круглым обрубком, над ней кайма глазури.
        thigh = capsule(hp, kn, 6.4 * s * b, 5.2 * s * b)
        put(c, pal, thigh, pal["bread"], far=far, soft=True)
        foot = capsule(add(add(an, sd, 1.6 * s), fwd, -1.5 * s), add(add(an, sd, 2.2 * s), fwd, 6.0 * s), 3.9 * s, 3.4 * s)
        shin = capsule(kn, add(an, sd, 1.0 * s), 5.0 * s * b, 4.5 * s * b)
        put(c, pal, shin | foot, pal["bread"], far=far, soft=True)
        cuff = _band(shin, add(an, sd, -3.6 * s), sd, 1.2 * s)
        put(c, pal, cuff, pal["icing"], far=far, cast=False)
        sole = {q for q in foot if (q[0], q[1] + 1) not in foot and (q[0], q[1] + 1) not in shin}
        recolor(c, sole, lambda x, y, e: pal["bread"][0])
        return
    pants = {"donut": "choco", "cane": None, "king": "choco"}[kind]
    boots = {"donut": "choco", "cane": "choco", "king": "dark"}[kind]
    thigh = capsule(hp, kn, 6.0 * s * b, 4.8 * s * b)
    if kind == "cane":
        put(c, pal, thigh, None, far=far, soft=True, mat=_stripes(pal, hp, _unit(hp, kn), 3.4))
    else:
        put(c, pal, thigh, pal[pants], far=far, soft=True)
    top_h = (9 if kind == "king" else 6) * s
    boot = capsule(add(an, sd, -top_h), an, 4.5 * s * b, 4.1 * s * b)
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
    shin = capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b, 4.0 * s * b)
    put(c, pal, boot | foot, pal[boots], far=far)
    if kind == "donut":
        # Шорты до колена, ниже голое тесто.
        put(c, pal, shin, pal["dough"], far=far)
        put(c, pal, _band(thigh, lerp(hp, kn, 0.9), _unit(hp, kn), 1.0 * s), pal["icing"], far=far, cast=False)
        # Розовая кайма голенища.
        put(c, pal, _band(boot, add(an, sd, -top_h + 0.5 * s), sd, 1.1 * s), pal["glaze"], far=far, cast=False)
    elif kind == "cane":
        put(c, pal, shin, None, far=far, mat=_stripes(pal, kn, sd, 3.4))
        put(c, pal, _band(boot, add(an, sd, -top_h + 0.5 * s), sd, 1.1 * s), pal["gold"], far=far, cast=False)
    else:
        put(c, pal, shin, pal[pants], far=far)
        # Карамельный наколенник и отворот сапога.
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 2.3 * s, 2.5 * s), pal["gold"], far=far, cast=False)
        put(c, pal, _band(boot, add(an, sd, -top_h + 0.6 * s), sd, 1.4 * s), pal["gold"], far=far, cast=False)
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    recolor(c, sole, lambda x, y, e: pal[boots][0])


# Посыпка пончика: место вдоль плеч и вниз от шеи (в долях ширины и роста), цвет, лежит ли стоймя.
SPRINKLES = ((-8, 3, "mint", 0), (-3, 1, "icing", 1), (2, 5, "gold", 0), (7, 3, "mint", 1), (-6, 9, "icing", 0),
             (-1, 10, "gold", 1), (8, 9, "icing", 0), (-10, 7, "gold", 1), (4, 0, "icing", 0), (-5, -1, "mint", 1),
             (0, 14, "mint", 0), (-9, 13, "icing", 1), (9, 13, "gold", 0), (5, 11, "mint", 1))


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    def local(x, y):
        return ((x - N[0]) * rt[0] + (y - N[1]) * rt[1], -((x - N[0]) * up[0] + (y - N[1]) * up[1]))

    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    pelvis_ramp = {"ginger": "bread", "donut": "choco", "cane": "red", "king": "choco"}[kind]
    put(c, pal, pelvis, pal[pelvis_ramp], soft=True)
    belly = {"king": 1.6, "ginger": 0.8}.get(kind, 0.0)
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "king":
        tor |= ellipse(*P(lerp(N, H, 0.62), 4.0, 0), 7.5 * s * b, 7.0 * s)
    if kind == "ginger":
        # Тело печеньем: бока скруглены.
        tor |= ellipse(*P(lerp(N, H, 0.52), 0.0, 0), 9.2 * s * b, 15.0 * s, p["lean"])
    if kind == "donut":
        # Туловище пончиком: круглое, шире плеч.
        tor = ellipse(*P(lerp(N, H, 0.5), 0.2, 0), 11.6 * s * b, 18.6 * s, p["lean"])

    def mat(x, y):
        lx, ly = local(x, y)
        if kind == "ginger":
            return pal["bread"]
        if kind == "donut":
            return pal["glaze"] if ly < 17.0 * s + _drip(lx) else pal["dough"]
        if kind == "cane":
            # Жилет нараспашку, под ним полосатая фуфайка.
            if 0.5 * s * b < lx < 4.6 * s * b:
                return pal["red"] if int(math.floor((ly + lx * 0.5) / 3.2)) % 2 == 0 else pal["icing"]
            return pal["vest"]
        return pal["icing"] if ly < 1.5 * s + _drip(lx) * 0.6 else pal["choco"]

    put(c, pal, tor, None, soft=True, mat=mat)
    if kind == "ginger":
        # Волна глазури по поясу, две пуговицы-драже, блик на каждой.
        for k in range(-16, 17):
            q = P(H, k * 0.45, 3.4 + math.sin(k * 0.9) * 1.3)
            if (round(q[0]), round(q[1])) in tor | pelvis:
                c.set(q[0], q[1], pal["icing"][2])
        for t, r, ramp in ((0.36, 4.0, "mint"), (0.62, 4.4, "pink")):
            q = P(lerp(N, H, t), r, 0)
            put(c, pal, ellipse(q[0], q[1], 2.2 * s, 2.2 * s), pal[ramp], cast=False)
            c.set(q[0] - 1, q[1] - 1, pal[ramp][3])
        return
    if kind == "donut":
        # Дырка пончика вмятиной спереди, посыпка по глазури, белая кромка шорт.
        hole = ellipse(*P(lerp(N, H, 0.55), 3.4, 0), 2.8 * s, 4.2 * s, p["lean"])
        D = pal["dough"]
        put(c, pal, hole, [D[1], D[0], D[0], D[1]], cast=False)
        rim = {q for q in ellipse(*P(lerp(N, H, 0.55), 3.4, 0), 4.0 * s, 5.4 * s, p["lean"]) if q not in hole}
        recolor(c, rim, lambda x, y, e: pal["glaze"][3] if e == pal["glaze"][2] else D[3] if e == D[2] else None)
        glaze = set(pal["glaze"])
        for (lx, ly, ramp, vert) in SPRINKLES:
            q = add(add(N, rt, lx * s * b), up, -ly * s)
            x, y = round(q[0]), round(q[1])
            if c.get(x, y) in glaze and c.get(x + (0 if vert else 1), y + (1 if vert else 0)) in glaze:
                c.set(x, y, pal[ramp][2])
                c.set(x + (0 if vert else 1), y + (1 if vert else 0), pal[ramp][1 if ramp != "icing" else 2])
        for k in range(-14, 15):
            q = P(H, k * 0.5, 3.6)
            if (round(q[0]), round(q[1])) in pelvis and (round(q[0]), round(q[1])) not in tor:
                c.set(q[0], q[1], pal["icing"][2])
        return
    # Пояс с пряжкой.
    belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    put(c, pal, belt, pal["choco" if kind == "cane" else "gold"], cast=False)
    bk = P(H, 4.6, 4.1)
    put(c, pal, ellipse(bk[0], bk[1], 1.8 * s, 1.6 * s), pal["gold" if kind == "cane" else "red"], cast=False)
    if kind == "cane":
        # Карамельные пуговицы на борту жилета.
        for k in range(3):
            q = P(lerp(N, H, 0.34 + k * 0.17), 5.8, 0)
            c.set(q[0], q[1], pal["gold"][2])
            c.set(q[0], q[1] + 1, pal["gold"][1])
    else:
        # Дольки плитки: борозды с фаской; карамельные пуговицы, мятный орден-драже.
        Ch = pal["choco"]
        step = 7.0 * s
        for q in tor:
            e = c.get(*q)
            if e not in (Ch[2], Ch[3]):
                continue
            lx, ly = local(*q)
            if (lx + 40) % step < 1.0 or (ly + 2.0) % step < 1.0:
                c.set(q[0], q[1], Ch[1])
            elif (lx + 40) % step < 2.0 or (ly + 2.0) % step < 2.0:
                c.set(q[0], q[1], Ch[3])
        for k in range(3):
            q = P(lerp(N, H, 0.3 + k * 0.2), 4.2 - k * 0.15, 0)
            put(c, pal, ellipse(q[0], q[1], 1.5 * s, 1.5 * s), pal["gold"], cast=False)
        q = P(lerp(N, H, 0.36), 7.4, 0)
        put(c, pal, ellipse(q[0], q[1], 2.0 * s, 2.0 * s), pal["mint"], cast=False)
        c.set(q[0] - 1, q[1] - 1, pal["mint"][3])


def _tails(c, look, j, p, long):
    """Полы жилета (короткие) и мантия короля (длинная, по низу кремовая опушка в крапину)."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = (33 if long else 15) * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 6.0 * s * b), up, 3 * s),
           (H[0] + 4 * s * b + sway * 0.3, H[1] + ln * 0.85), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - (13 if long else 10) * s * b + sway, H[1] + ln * 0.9)]
    S = poly(pts)
    put(c, pal, S, pal["mantle" if long else "vest"], soft=True)
    if long:
        hem = {q for q in S if (q[0], q[1] + 1) not in S or (q[0], q[1] + 2) not in S or (q[0], q[1] + 3) not in S}
        recolor(c, hem, lambda x, y, e: pal["dark"][1] if (x * 3 + y) % 7 == 0 else pal["icing"][2])
        # Складки мантии.
        for k in (0.3, 0.62):
            a, e = lerp(pts[0], pts[1], k), lerp(pts[4], pts[2], k)
            for t in range(4, 22):
                q = lerp(a, e, t / 24.0)
                if (round(q[0]), round(q[1])) in S and (round(q[0]), round(q[1])) not in hem:
                    c.set(q[0], q[1], pal["mantle"][1])
    else:
        edge = {q for q in S if (q[0], q[1] + 1) not in S}
        recolor(c, edge, lambda x, y, e: pal["gold"][2])


def _head(c, look, j, p, hurt=False):
    pal, s, kind = look.pal, look.body.s, look.kind
    hc = j["head"]
    ang = p["lean"] + p["tilt"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    wave = p.get("wave", 0.0)

    def H(dx, dy):
        return (hc[0] + (dx * ca - dy * sa) * s, hc[1] + (dx * sa + dy * ca) * s)

    def local(x, y):
        dx, dy = (x - hc[0]) / s, (y - hc[1]) / s
        return (dx * ca + dy * sa, -dx * sa + dy * ca)

    def dot(q, col, S=None):
        if S is None or (round(q[0]), round(q[1])) in S:
            c.set(q[0], q[1], col)

    E = pal["eye"]
    if kind == "ginger":
        B, I = pal["bread"], pal["icing"]
        # Короткая толстая шея и большая круглая голова печеньем.
        neck = capsule(lerp(j["neck"], hc, 0.0), lerp(j["neck"], hc, 0.5), 4.6 * s, 4.4 * s)
        put(c, pal, neck, B)
        head = ellipse(*H(0.4, -1.0), 9.6 * s, 9.3 * s, ang)
        put(c, pal, head, B, soft=True)
        # Завиток глазури на затылке и макушке.
        for k in range(0, 30):
            q = H(-7.6 + k * 0.36, -5.6 - math.sin(k * 0.21) * 2.2 + math.sin(k * 1.05) * 1.1)
            dot(q, I[2], head)
        if hurt:
            # Глаза крестиками, рот кружком, трещина от макушки, крошки.
            for ex in (1.4, 5.8):
                for k in (-1, 0, 1):
                    dot(H(ex + k, -1.8 + k), E[1], head)
                    dot(H(ex + k, -1.8 - k), E[1], head)
            mo = ellipse(*H(4.0, 3.8), 1.9 * s, 2.1 * s)
            put(c, pal, mo & head, [E[1], E[1], E[2], E[2]], cast=False)
            for k, (dx, dy) in enumerate(((-2.0, -10.0), (-1.0, -8.6), (-2.4, -7.4), (-1.2, -6.0), (-2.2, -4.8))):
                dot(H(dx, dy), B[0], head)
            for dx, dy in ((-12.0, -7.0), (-13.0, -2.0), (-10.5, -11.5)):
                dot(H(dx, dy), B[3])
        else:
            # Два глаза в три четверти, белая улыбка глазурью, розовый румянец.
            for ex, rx in ((1.4, 1.2), (5.8, 1.5)):
                eye = ellipse(*H(ex, -1.8), rx * s, 2.0 * s, ang) & head
                recolor(c, eye, lambda x, y, e: E[1])
                dot(H(ex + 0.4, -2.6), E[3], eye)
            for k in range(0, 15):
                t = k / 14.0
                q = H(0.2 + t * 7.2, 2.4 + math.sin(t * math.pi) * 2.6)
                dot(q, I[3], head)
                dot((q[0], q[1] + 1), I[1], head)
            for dx in (-1.6, 8.0):
                q = H(dx, 1.2)
                dot(q, pal["pink"][2], head)
                dot((q[0], q[1] + 1), pal["pink"][2], head)
        # Бантик под подбородком: узел, два крыла, концы ленты качаются.
        kx, ky = H(4.6, 9.2)
        R_ = pal["red"]
        tails = capsule((kx, ky), H(2.2 - wave * 0.6, 14.6), 1.5 * s, 1.1 * s) | capsule((kx, ky), H(7.0 + wave * 0.6, 14.4),
                                                                                     1.5 * s, 1.1 * s)
        put(c, pal, tails, [R_[0], R_[0], R_[1], R_[2]], cast=False)
        wings = poly([(kx, ky), H(-1.6, 5.6), H(-2.2, 12.2)]) | poly([(kx, ky), H(10.6, 5.8), H(11.0, 12.4)])
        put(c, pal, wings, R_, soft=True)
        put(c, pal, ellipse(kx, ky, 2.2 * s, 2.2 * s), R_, cast=False)
        c.set(kx - 1, ky - 1, R_[3])
        return
    if kind == "donut":
        D, G = pal["dough"], pal["glaze"]
        neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 4.2 * s * look.body.b, 4.0 * s)
        put(c, pal, neck, D)
        skull = ellipse(*H(-0.5, -3.4), 9.6 * s, 9.2 * s, ang)
        jaw = poly([H(-4.5, 1.0), H(7.4, 0.6), H(7.8, 5.6), H(4.0, 9.0), H(-3.6, 8.0)])
        face = skull | jaw
        put(c, pal, face, D, soft=True)
        # Шапка глазури с потёками на лоб и затылок, посыпка.
        cap = {q for q in skull if local(*q)[1] < -5.4 + _drip(local(*q)[0] * 1.7) * 0.55 + (1.8 if local(*q)[0] < -4 else 0)}
        put(c, pal, cap, G, soft=True, cast=False)
        for dx, dy, ramp, vert in ((-5, -8, "mint", 0), (-1, -10, "icing", 1), (3, -8, "gold", 0), (6, -6.6, "icing", 1),
                                   (-7.4, -5, "gold", 1), (0.6, -6.8, "mint", 0)):
            q = H(dx, dy)
            x, y = round(q[0]), round(q[1])
            x2, y2 = x + (0 if vert else 1), y + (1 if vert else 0)
            if (x, y) in cap and (x2, y2) in cap:
                c.set(x, y, pal[ramp][2])
                c.set(x2, y2, pal[ramp][1 if ramp != "icing" else 2])
        # Вишня на макушке: ягода с бликом и черенок.
        ch = H(-1.0, -13.2)
        st0, st1 = H(-0.4, -15.4), H(2.2 + wave * 0.8, -17.6)
        put(c, pal, capsule(st0, st1, 0.8, 0.7), pal["choco"], cast=False)
        put(c, pal, ellipse(ch[0], ch[1], 3.0 * s, 2.8 * s), pal["red"], soft=True)
        c.set(ch[0] - 1, ch[1] - 1, pal["red"][3])
        # Сахарная пудра на тяжёлой челюсти.
        for q in jaw:
            lx, ly = local(*q)
            if ly > 4.0 and (q[0] + q[1]) % 2 == 0 and c.get(*q) in (D[2], D[3]):
                c.set(q[0], q[1], D[1])
        # Хмурая бровь, маленький глаз, широкая пасть с зубом.
        ex, ey = H(4.2, -1.2)
        put(c, pal, capsule(H(1.0, -4.0), H(7.6, -2.2), 1.2 * s, 1.0 * s), [D[0], D[0], D[1], D[1]], cast=False)
        if hurt:
            for k in range(-2, 3):
                c.set(ex + k * ca, ey + k * sa, D[0])
            mo = ellipse(*H(4.6, 5.0), 2.4 * s, 2.0 * s) & face
            put(c, pal, mo, [E[1], E[1], E[2], E[2]], cast=False)
        else:
            c.set(ex, ey, E[1])
            c.set(ex + 1, ey, E[1])
            c.set(ex, ey - 1, E[3])
            c.set(ex + 1, ey + 1, E[1])
            for k in range(0, 6):
                q = H(2.2 + k, 5.0 + (0.8 if k in (0, 5) else 0.0))
                dot(q, D[0], face)
            dot(H(5.4, 4.2), pal["icing"][3], face)
            dot(H(3.2, 4.2), pal["icing"][3], face)
        return
    sk = pal["skin" if kind == "cane" else "choco"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.5 * s * look.body.b, 3.3 * s)
    put(c, pal, neck, sk)
    if kind == "king":
        # Ворот мантии за шеей с кремовой кромкой.
        col = poly([H(-9.5, 10), H(-10.5, 1.5), H(-4.5, 4), H(3, 10)])
        put(c, pal, col, pal["mantle"], soft=True)
        edge = {q for q in col if (q[0] - 1, q[1]) not in col or (q[0], q[1] - 1) not in col or (q[0] - 2, q[1]) not in col}
        recolor(c, edge, lambda x, y, e: pal["icing"][2])
    skull = ellipse(*H(0, -0.5), 7.2 * s, 7.8 * s, ang)
    jaw = poly([H(-3, 2), H(6.2, 1.5), H(6.6, 5), H(3.5, 8.6), H(-2.5, 8)])
    nose = poly([H(5.5, -1.5), H(8.4, 2.4), H(5.6, 3.2)]) if kind == "cane" else ellipse(*H(7.0, 1.6), 2.4 * s, 2.2 * s)
    face = skull | jaw | nose
    put(c, pal, face, sk, soft=True)
    ex, ey = H(3.2, -1.2)
    ex, ey = round(ex), round(ey)
    if kind == "cane":
        V, I = pal["vest"], pal["icing"]
        # Хвост фантика на затылке: узел и веер в складку, качается.
        kx, ky = H(-7.2, -2.6)
        fan = poly([(kx, ky), H(-13.0, -8.4 - wave), H(-15.6, -3.0), H(-13.6, 2.6 + wave)])
        put(c, pal, fan, I, soft=True)
        for t in (0.3, 0.55, 0.8):
            a = lerp(H(-13.0, -8.4 - wave), H(-13.6, 2.6 + wave), t)
            for k in range(2, 9):
                dot(lerp((kx, ky), a, k / 9.0), I[1], fan)
        put(c, pal, ellipse(kx, ky, 2.0 * s, 2.2 * s), pal["red"])
        # Обёртка шапочкой: ягодная, с белым краем и красной полосой.
        cap = {q for q in skull if local(*q)[1] < -2.4 or (local(*q)[0] < -3.4 and local(*q)[1] < 2.0)}
        put(c, pal, cap, V, soft=True, cast=False)
        brim = {q for q in cap if -3.6 < local(*q)[1] < -2.2 and local(*q)[0] > -3.6}
        recolor(c, brim, lambda x, y, e: I[2])
        band = {q for q in cap if -6.4 < local(*q)[1] < -5.0}
        recolor(c, band, lambda x, y, e: pal["red"][2])
        # Ухо.
        q = H(-1.0, 1.4)
        put(c, pal, ellipse(q[0], q[1], 1.5 * s, 1.9 * s), [sk[0], sk[1], sk[2], sk[2]], cast=False)
        if hurt:
            c.set(ex, ey, sk[0])
            c.set(ex + 1, ey, sk[0])
            c.set(ex - 1, ey - 1, sk[0])
        else:
            c.set(ex, ey, E[3])
            c.set(ex + 1, ey, E[1])
            c.set(ex + 1, ey - 1, E[1])
            for k in range(-1, 3):
                c.set(ex + k, ey - 2 - (1 if k < 1 else 0), E[2])
        # Ухмылка.
        mx, my = H(4.0, 5.2)
        mx, my = round(mx), round(my)
        c.set(mx, my, sk[0])
        c.set(mx + 1, my, sk[0])
        c.set(mx + 2, my - 1, sk[0])
        if hurt:
            c.set(mx, my + 1, sk[0])
            c.set(mx + 1, my + 1, E[1])
        return
    # Король: корона из глазури раструбом кверху, зубцы с каплями, обод с драже.
    I, Gd = pal["icing"], pal["gold"]
    flare = poly([H(-7.4, -6.6), H(7.6, -6.6), H(9.4, -11.8), H(-9.2, -11.8)])
    put(c, pal, flare, I, soft=True)
    for k in range(4):
        x0 = -9.2 + k * 4.75
        put(c, pal, poly([H(x0, -11.2), H(x0 + 2.2, -15.6), H(x0 + 4.4, -11.2)]), I, cast=False)
        tip = H(x0 + 2.2, -16.0)
        put(c, pal, ellipse(tip[0], tip[1], 1.4 * s, 1.4 * s), pal["mantle" if k % 2 == 0 else "mint"], cast=False)
    band = poly([H(-7.6, -5.4), H(7.8, -5.4), H(8.0, -8.0), H(-7.8, -8.0)])
    put(c, pal, band, Gd, cast=False)
    for k, ramp in enumerate(("red", "mint", "mantle", "mint", "red")):
        q = H(-6.0 + k * 3.2, -6.8)
        c.set(q[0], q[1], pal[ramp][2])
        c.set(q[0] + 1, q[1], pal[ramp][3])
    # Белая борода клином и ус.
    beard = poly([H(-2.0, 4.6), H(6.4, 5.0), H(6.6, 8.0), H(3.6, 13.6), H(-1.6, 9.6)])
    put(c, pal, beard, I, soft=True)
    must = capsule(H(4.6, 4.4), H(10.4, 5.8 - (0 if hurt else 1.4)), 1.6 * s, 0.9 * s)
    put(c, pal, must, I, cast=False)
    for k in range(3):
        dot(H(0.4 + k * 1.6, 7.0 + k * 1.8), I[1], beard)
    # Глаз под белой бровью.
    brow = capsule(H(1.4, -3.4), H(6.0, -2.8 + (1.0 if hurt else 0.0)), 0.9 * s, 0.7 * s)
    if hurt:
        c.set(ex, ey, sk[0])
        c.set(ex + 1, ey, sk[0])
        c.set(ex - 1, ey, sk[0])
        mo = ellipse(*H(5.0, 5.6), 1.6 * s, 1.4 * s)
        put(c, pal, mo, [E[1], E[1], E[2], E[2]], cast=False)
    else:
        c.set(ex, ey, E[3])
        c.set(ex + 1, ey, E[0])
        c.set(ex + 1, ey - 1, E[0])
        c.set(ex, ey + 1, sk[1])
    put(c, pal, brow, [I[1], I[1], I[2], I[3]], cast=False)


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if kind == "king":
        _tails(c, look, j, p, True)
    _torso(c, look, j, p)
    if kind == "cane":
        _tails(c, look, j, p, False)
    _leg(c, look, j, "n", False, p)
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
    for key, look, frame, w, h, up in (("hero", hero_look(), pb.hero_frames()[0], FW, FH, 15),
                                       ("thug", thug_look(), pb.foe_frames()[0], FW, FH, 20),
                                       ("knife", knife_look(), pb.foe_frames(knife=True)[0], FW, FH, 16),
                                       ("boss", boss_look(), pb.foe_frames(boss=True)[0], BW, BH, 23)):
        f = fighter(frame, look, w, h)
        hx, hy = int(round(f.head[0])), int(round(f.head[1]))
        c = Canvas(32, 32)
        for y in range(32):
            for x in range(32):
                sx, sy = hx - 15 + x, hy - up + y
                if 0 <= sx < w and 0 <= sy < h:
                    c.px[y][x] = f.px[sy][sx]
        out["brawl_face_" + key] = (c, look.pal.colors)
    return out


# --- Улица карамельной страны ----------------------------------------------------------------------

def street_pal():
    p = Pal(0x24121A)
    p.add("cream", [0x9A7A5A, 0xD0AE84, 0xF2DCB0, 0xFFF4D8])
    p.add("bread", [0x5E3018, 0x8A4C24, 0xB87238, 0xDC9C58])
    p.add("icing", [0xB098AC, 0xD6BFCC, 0xFFF7EC, 0xFFFFFF])
    p.add("pink", [0x8A2C58, 0xC8508A, 0xFF8EB6, 0xFFC8DC])
    p.add("mint", [0x2F7C80, 0x3FA99C, 0x86DBBE, 0xD3F6E4])
    p.add("choco", [0x2E1818, 0x4A2826, 0x7C4838, 0xA86C50])
    p.add("gold", [0x8A5418, 0xD09038, 0xF8CF6A, 0xFFF0B0])
    p.add("red", [0x7A1430, 0xB7243A, 0xE63545, 0xFF8490])
    p.add("waffle", [0x8A5A20, 0xB8832E, 0xDEB058, 0xF6D88C])
    p.add("glass", [0x2A3A5C, 0x4A6A94, 0x86B4D0, 0xD8F0F8])
    p.add("glow", [0xB8641C, 0xF0A030, 0xFFD870, 0xFFF8C8])
    p.add("berry", [0x3A1C60, 0x623A9C, 0x9466D0, 0xC4A2F0])
    p.add("slab", [0x8E7A70, 0xBCA690, 0xE4D0B4, 0xFAECD4])
    p.add("road", [0x1E4E5C, 0x2B7078, 0x44988E, 0x74C8AC])
    return p


class Town(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(137)

    def fill(self, S, col):
        for (x, y) in S:
            self.c.set(x, y, col)

    # Стены ------------------------------------------------------------------------------------

    def tiles(self, x0, y0, x1, y1, pw=40, ph=26, ramp="choco", dot=True):
        """Стена дольками плитки: фаска у каждой дольки, ряды вразбежку, тиснение точкой."""
        R_ = self.R(ramp)
        self.rect(x0, y0, x1, y1, R_[0])
        for row, y in enumerate(range(y0, y1 + 1, ph)):
            x = x0 - (0 if row % 2 == 0 else pw // 2)
            while x <= x1:
                a, b = max(x + 1, x0), min(x + pw - 1, x1)
                yb = min(y + ph - 1, y1)
                if b - a > 3 and yb - y > 3:
                    self.bevel(a, y + 1, b, yb, R_)
                    self.noise(a + 1, y + 2, b - 1, yb - 1, R_, 0.02)
                    if dot and b - a > 14 and yb - y > 12:
                        self.bevel(a + 5, y + 6, b - 5, yb - 5, R_, inset=True)
                x += pw

    def ginger(self, x0, y0, x1, y1):
        """Пряничная стена: тёплый корж с порами, по нему узоры глазурью: волны и горошины."""
        B, I = self.R("bread"), self.R("icing")
        self.rect(x0, y0, x1, y1, B[2])
        self.noise(x0, y0, x1, y1, B, 0.05)
        for yy in (y0 + 26, y1 - 46):
            self.wave(x0, x1, yy, 3, 14)
        for row, yy in enumerate(range(y0 + 48, y1 - 56, 22)):
            for xx in range(x0 + 10 + (row % 2) * 11, x1 - 4, 22):
                self.rect(xx, yy, xx + 1, yy + 1, I[2])
                self.c.set(xx + 2, yy + 2, B[1])
                self.c.set(xx + 1, yy + 2, B[1])

    def waffle(self, x0, y0, x1, y1, cell=16):
        """Вафельная стена: клетки с вдавленным дном."""
        W = self.R("waffle")
        self.rect(x0, y0, x1, y1, W[2])
        for y in range(y0, y1 + 1, cell):
            for x in range(x0, x1 + 1, cell):
                a, b, yb = x + 2, min(x + cell - 3, x1), min(y + cell - 3, y1)
                if b - a > 2 and yb - y > 4:
                    self.bevel(a, y + 2, b, yb, [W[0], W[3], W[1], W[0]], inset=False)
                    self.c.set(a + 1, y + 3, W[0])
        for y in range(y0, y1 + 1, cell):
            self.rect(x0, y, x1, y, W[3])
        for x in range(x0, x1 + 1, cell):
            self.rect(x, y0, x, y1, W[3])

    def plain(self, x0, y0, x1, y1, ramp="cream", foot="pink"):
        """Гладкая стена кремом, понизу цоколь из плиток глазури."""
        R_ = self.R(ramp)
        self.rect(x0, y0, x1, y1, R_[2])
        self.noise(x0, y0, x1, y1, R_, 0.04)
        for yy in range(y0 + 40, y1 - 50, 34):
            for xx in range(x0, x1 + 1):
                if (xx // 3) % 2 == 0:
                    self.c.set(xx, yy, R_[1])
        self.tiles(x0, y1 - 40, x1, y1, 24, 20, foot, dot=False)
        self.rect(x0, y1 - 43, x1, y1 - 41, self.R("icing")[2])
        self.rect(x0, y1 - 41, x1, y1 - 41, self.R("icing")[1])

    def wave(self, x0, x1, y, amp=3, period=12, ramp="icing"):
        """Волна глазури в два пикселя с тенью под ней."""
        I = self.R(ramp)
        for xx in range(x0, x1 + 1):
            yy = y + int(round(math.sin(xx * 2 * math.pi / period) * amp))
            self.dark(xx, yy + 2, xx, yy + 2, 1)
            self.c.set(xx, yy, I[3])
            self.c.set(xx, yy + 1, I[2])

    def eave(self, x0, x1, ramp="choco"):
        """Крыша над первым этажом: черепица печеньем в два ряда, по карнизу наплыв глазури с
        потёками на стену."""
        R_, I = self.R(ramp), self.R("icing")
        self.rect(x0, 0, x1, 19, R_[0])
        for row in (0, 1):
            xx = x0 - row * 9
            while xx <= x1:
                a, b = max(xx, x0), min(xx + 17, x1)
                if b - a > 2:
                    S = {(x, y) for x in range(a, b + 1) for y in range(row * 10, row * 10 + 9)}
                    S |= ellipse((xx + xx + 17) / 2.0, row * 10 + 7, 8.5, 3.2)
                    S = {q for q in S if a <= q[0] <= b and q[1] < row * 10 + 10}
                    self.put(S, R_, soft=False, cast=False)
                xx += 18
        self.dark(x0, 32, x1, 36, 1)
        self.dark(x0, 37, x1, 40, 1, dither=True)
        self.rect(x0, 20, x1, 31, I[2])
        self.rect(x0, 20, x1, 20, I[3])
        for xx in range(x0, x1 + 1):
            depth = int(round(3 + 2.5 * math.sin(xx * 0.21) + 2.0 * math.sin(xx * 0.057 + 1.0)
                              + (5 if (xx // 6) % 7 == 3 else 0)))
            depth = max(depth, 0)
            self.rect(xx, 32, xx, 32 + depth, I[2])
            self.c.set(xx, 33 + depth, I[1])
            if (xx // 6) % 7 == 3 and xx % 6 == 1:
                self.rect(xx, 30, xx, 31 + depth, I[3])
        for xx in range(x0 + 5, x1 - 2, 14):
            col = (self.R("pink"), self.R("mint"), self.R("gold"), self.R("red"))[(xx // 14) % 4]
            self.rect(xx, 24, xx + 2, 26, col[2])
            self.c.set(xx, 24, col[3])
            self.rect(xx, 27, xx + 2, 27, I[1])

    def cane(self, x, y0, y1, w=9):
        """Столб карамельной тростью: красно-белая полоса наискось, блик слева, тень справа."""
        Rd, I = self.R("red"), self.R("icing")
        for yy in range(y0, y1 + 1):
            for k in range(w):
                ramp = Rd if ((yy + k * 2) // 9) % 2 == 0 else I
                t = 3 if k == 1 else 1 if k >= w - 2 else 2
                self.c.set(x + k, yy, ramp[t])
        self.dark(x + w, y0, x + w + 1, y1, 1)

    def hcane(self, x0, x1, y, h=6):
        Rd, I = self.R("red"), self.R("icing")
        for xx in range(x0, x1 + 1):
            for k in range(h):
                ramp = Rd if ((xx + k * 2) // 9) % 2 == 0 else I
                t = 3 if k == 1 else 1 if k >= h - 1 else 2
                self.c.set(xx, y + k, ramp[t])
        self.dark(x0, y + h, x1, y + h + 1, 1)

    # Товар в витринах --------------------------------------------------------------------------

    def cake(self, cx, by, w=20, top="pink"):
        """Торт в два яруса: бисквит с прослойкой, глазурь с потёками, вишня."""
        Cr, T, Rd = self.R("cream"), self.R(top), self.R("red")
        for half, y0, y1 in ((w // 2, by - 9, by), (w // 2 - 4, by - 17, by - 10)):
            self.rect(cx - half, y0, cx + half, y1, Cr[2])
            self.rect(cx + half - 2, y0, cx + half, y1, Cr[1])
            self.rect(cx - half, y0 + 5, cx + half, y0 + 5, self.R("choco")[2])
            self.rect(cx - half, y0, cx + half, y0 + 2, T[2])
            self.rect(cx - half, y0, cx + half, y0, T[3])
            for xx in range(cx - half, cx + half + 1, 3):
                self.c.set(xx, y0 + 3, T[2])
        self.fill(ellipse(cx, by - 20, 2.2, 2.2), Rd[2])
        self.c.set(cx - 1, by - 21, Rd[3])

    def jar(self, cx, by, ramp="red"):
        """Банка с драже: стекло, цветные шарики, карамельная крышка."""
        G, Gd = self.R("glass"), self.R("gold")
        self.rect(cx - 6, by - 15, cx + 6, by, G[2])
        self.rect(cx - 6, by - 15, cx - 6, by, G[3])
        self.rect(cx + 6, by - 15, cx + 6, by, G[1])
        r = self.rng
        for yy in range(by - 12, by, 3):
            for xx in range(cx - 4, cx + 5, 3):
                col = self.R(r.choice((ramp, ramp, "mint", "gold", "pink")))
                self.rect(xx, yy, xx + 1, yy + 1, col[2])
                self.c.set(xx, yy, col[3])
        self.rect(cx - 7, by - 18, cx + 7, by - 16, Gd[2])
        self.rect(cx - 7, by - 18, cx + 7, by - 18, Gd[3])
        self.rect(cx - 4, by - 9, cx - 4, by - 3, G[3])

    def cone(self, cx, by, scoops=("pink", "icing")):
        """Рожок мороженого в подставке: вафля в клетку, шарики горкой."""
        W = self.R("waffle")
        for (x, y) in poly([(cx - 5, by - 14), (cx + 5, by - 14), (cx, by)]):
            self.c.set(x, y, W[1] if (x + y) % 3 == 0 or (x - y) % 3 == 0 else W[2])
        yy = by - 17
        for k, name in enumerate(scoops):
            S = ellipse(cx, yy, 5.6 - k, 4.6 - k * 0.6)
            self.put(S, self.R(name), soft=False, cast=False)
            yy -= 6 - k

    # Проёмы ------------------------------------------------------------------------------------

    def window(self, x, y, w, h, show="cakes", frame="icing"):
        """Витрина: рама глазурью, тёплый свет изнутри, полка с товаром, блики на стекле,
        подоконник."""
        F, G, Ch = self.R(frame), self.R("glow"), self.R("choco")
        self.bevel(x - 5, y - 5, x + w + 5, y + h + 5, F)
        for yy in range(y, y + h + 1):
            for xx in range(x, x + w + 1):
                k = (yy - y) / float(h)
                self.c.set(xx, yy, G[3] if k < 0.22 and (xx + yy) % 2 == 0 else G[2] if k < 0.6 or (xx + yy) % 2 else G[1])
        shelf = y + h - 5
        self.rect(x, shelf, x + w, y + h, Ch[2])
        self.rect(x, shelf, x + w, shelf, Ch[3])
        step = 26 if show == "cakes" else 18
        k = 0
        xx = x + step // 2 + 1
        while xx < x + w - step // 2 + 3:
            if show == "cakes":
                self.cake(xx, shelf - 1, 20, ("pink", "mint", "icing", "berry")[k % 4])
            elif show == "jars":
                self.jar(xx, shelf - 1, ("red", "berry", "mint", "pink")[k % 4])
            else:
                self.cone(xx, shelf - 1, (("pink", "icing"), ("mint", "pink"), ("cream", "berry"))[k % 3])
            xx += step
            k += 1
        # Блики на стекле: две косые полосы.
        for k in range(h - 4):
            for dx in (0, 1, 7):
                xx, yy = x + 6 + dx + (h - 4 - k) // 2, y + 2 + k
                if x < xx < x + w and (dx != 7 or k % 2 == 0):
                    e = self.c.get(xx, yy)
                    if e in (G[1], G[2]):
                        self.c.set(xx, yy, G[3])
        if w > 70:
            mid = x + w // 2
            self.rect(mid - 1, y, mid + 1, y + h, F[2])
            self.rect(mid + 1, y, mid + 1, y + h, F[1])
        self.dark(x, y, x + w, y + 2, 1)
        self.dark(x, y + 3, x + 1, y + h, 1)
        self.bevel(x - 9, y + h + 6, x + w + 9, y + h + 10, F)
        self.dark(x - 7, y + h + 11, x + w + 10, y + h + 13, 1)

    def round_window(self, cx, cy, r, ramp="pink"):
        """Круглое окно в раме-пончике: глазурь с посыпкой, за стеклом тёплый свет."""
        T, G, D = self.R(ramp), self.R("glow"), self.R("waffle")
        self.put(ellipse(cx, cy, r + 8, r + 8), D, soft=True)
        ring = ellipse(cx, cy, r + 6, r + 6) - ellipse(cx, cy, r + 1, r + 1)
        self.put(ring, T, soft=True, cast=False)
        inner = ellipse(cx, cy, r, r)
        for (x, y) in inner:
            k = ((x - cx) + (y - cy)) / (2.0 * r)
            self.c.set(x, y, G[3] if k < -0.35 else G[2] if k < 0.2 or (x + y) % 2 else G[1])
        for (x, y) in inner:
            if (x - 2, y - 2) not in inner:
                self.c.set(x, y, G[0])
        self.rect(cx - r, cy, cx + r, cy, D[1])
        self.rect(cx, cy - r, cx, cy + r, D[1])
        for k in range(10):
            a = k * math.pi / 5 + 0.3
            bx, by = cx + math.cos(a) * (r + 3.5), cy + math.sin(a) * (r + 3.5)
            col = (self.R("icing"), self.R("mint"), self.R("gold"))[k % 3]
            self.c.set(bx, by, col[2])
            self.c.set(bx + (k % 2), by + ((k + 1) % 2), col[2])
        self.dark(cx - r - 5, cy + r + 9, cx + r + 9, cy + r + 11, 1)

    def door(self, x, y, w, h, ramp="choco", arch=False, frame="icing"):
        """Дверь плиткой шоколада или печеньем: дольки с фаской, окошко сердцем, карамельная
        ручка, рама глазурью, порог."""
        F, R_, Gd = self.R(frame), self.R(ramp), self.R("gold")
        self.bevel(x - 7, y - 7, x + w + 7, y + h, F)
        if arch:
            self.put({q for q in ellipse(x + w / 2.0, y - 2, w / 2.0 + 7, 18) if q[1] <= y}, F, soft=False, cast=False)
        self.rect(x, y, x + w, y + h, R_[1])
        if arch:
            self.fill({q for q in ellipse(x + w / 2.0, y, w / 2.0, 11) if q[1] <= y}, R_[1])
        cols = 2
        cw = (w - 3) // cols
        for cx in range(cols):
            for ry in range(y + 30, y + h - 6, 26):
                a = x + 2 + cx * (cw + 1)
                self.bevel(a, ry, a + cw - 2, min(ry + 22, y + h - 3), R_)
                self.bevel(a + 4, ry + 4, a + cw - 6, min(ry + 18, y + h - 7), R_, inset=True)
        # Окошко сердцем.
        hx, hy = x + w // 2, y + 14
        heart = ellipse(hx - 4, hy - 2, 4.6, 4.6) | ellipse(hx + 4, hy - 2, 4.6, 4.6) | poly([(hx - 8, hy), (hx + 8, hy),
                                                                                             (hx, hy + 9)])
        self.fill({(q[0] + d, q[1] + e) for q in heart for d in (-1, 0, 1) for e in (-1, 0, 1)}, F[2])
        G = self.R("glow")
        for (xx, yy) in heart:
            self.c.set(xx, yy, G[3] if yy < hy - 3 else G[2] if (xx + yy) % 2 else G[1])
        self.rect(x + w - 8, y + h // 2 + 6, x + w - 5, y + h // 2 + 9, Gd[2])
        self.c.set(x + w - 8, y + h // 2 + 6, Gd[3])
        self.rect(x + w - 8, y + h // 2 + 10, x + w - 5, y + h // 2 + 10, R_[0])
        self.dark(x, y, x + w, y + 3, 1)
        self.dark(x, y + 4, x + w, y + 7, 1, dither=True)
        self.bevel(x - 10, y + h + 1, x + w + 10, y + h + 5, self.R("slab"))

    def awning(self, x0, x1, y, h=22, a="pink", b="icing"):
        """Навес в полоску с фестонами по краю и тенью на стене."""
        A, B = self.R(a), self.R(b)
        self.dark(x0 - 2, y + h + 4, x1 + 4, y + h + 12, 1)
        self.dark(x0 - 2, y + h + 13, x1 + 4, y + h + 18, 1, dither=True)
        for k in range(h):
            out = k // 4
            for xx in range(x0 - out, x1 + out + 1):
                ramp = A if ((xx - x0 + 400) // 12) % 2 == 0 else B
                self.c.set(xx, y + k, ramp[3] if k == 0 else ramp[2] if k < h - 5 else ramp[1])
        out = h // 4
        xx = x0 - out
        while xx <= x1 + out:
            ramp = A if ((xx - x0 + 400) // 12) % 2 == 0 else B
            cxx = xx + 5.5 - ((xx - x0 + 400) % 12)
            for (px, py) in ellipse(cxx + 0.5, y + h, 6, 6):
                if py >= y + h and x0 - out <= px <= x1 + out:
                    self.c.set(px, py, ramp[2] if py < y + h + 4 else ramp[1])
            xx += 12 - ((xx - x0 + 400) % 12)

    def lolly(self, cx, cy, r, ramp="red", stick=0):
        """Леденец-спираль: диск в два цвета завитком, блик, тёмная кромка; палочка вниз."""
        A, I = self.R(ramp), self.R("icing")
        if stick:
            self.rect(cx - 1, cy, cx, cy + r + stick, I[2])
            self.rect(cx + 1, cy, cx + 1, cy + r + stick, I[1])
        for (x, y) in ellipse(cx, cy, r, r):
            d = math.hypot(x - cx, y - cy)
            t = (math.atan2(y - cy, x - cx) + d * 0.62) % (2 * math.pi)
            col = A if t < math.pi else I
            edge = d > r - 1.6
            self.c.set(x, y, col[1] if edge and (x - cx) + (y - cy) > 0 else col[3] if edge else col[2])
        for k in range(12, 70, 6):
            a = math.radians(180 + k)
            self.c.set(cx + math.cos(a) * (r - 3), cy + math.sin(a) * (r - 3), I[3])

    def board(self, x, y, w=34, h=30, kind="pretzel"):
        """Вывеска-доска на цепочках: вафельная рама, кремовое поле, знак лавки."""
        W, Cr, Ch = self.R("waffle"), self.R("cream"), self.R("choco")
        for cx in (x + 5, x + w - 5):
            for yy in range(y - 12, y):
                self.c.set(cx, yy, Ch[1] if yy % 2 else Ch[3])
        self.rect(x + 2, y + 2, x + w + 2, y + h + 2, self.p.darker[self.R("cream")[1]])
        self.dark(x + 2, y + 2, x + w + 2, y + h + 2, 1)
        self.bevel(x, y, x + w, y + h, W)
        self.bevel(x + 3, y + 3, x + w - 3, y + h - 3, Cr, inset=True)
        cx, cy = x + w // 2, y + h // 2
        if kind == "pretzel":
            B = self.R("bread")
            S = (ellipse(cx - 5, cy - 1, 6, 6) - ellipse(cx - 5, cy - 1, 3, 3)) | (ellipse(cx + 5, cy - 1, 6, 6)
                                                                                 - ellipse(cx + 5, cy - 1, 3, 3))
            S |= capsule((cx - 8, cy + 6), (cx + 5, cy - 4), 1.5, 1.5) | capsule((cx + 8, cy + 6), (cx - 5, cy - 4), 1.5, 1.5)
            self.put(S, B, soft=False, cast=False)
            for dx, dy in ((-7, -5), (4, -6), (0, 1), (-3, 5), (7, 3)):
                self.c.set(cx + dx, cy + dy, self.R("icing")[3])
        elif kind == "cupcake":
            self.fill(poly([(cx - 7, cy + 1), (cx + 7, cy + 1), (cx + 5, cy + 10), (cx - 5, cy + 10)]), self.R("mint")[2])
            for xx in (cx - 4, cx, cx + 4):
                self.rect(xx, cy + 2, xx, cy + 9, self.R("mint")[1])
            self.put(ellipse(cx, cy - 1, 9, 4) | ellipse(cx, cy - 5, 6, 3.4) | ellipse(cx, cy - 8, 3, 2.4), self.R("pink"),
                     soft=False, cast=False)
            self.fill(ellipse(cx, cy - 11, 1.8, 1.8), self.R("red")[2])
        else:
            self.cone(cx, cy + 12, ("pink", "mint"))

    def lamp(self, x, y):
        """Фонарь на карамельном крюке: светящийся мармеладный колпак и пятно света на стене."""
        G = self.R("glow")
        for (xx, yy) in ellipse(x, y + 22, 34, 30):
            e = self.c.get(xx, yy)
            if e is None or yy < y + 4:
                continue
            for name in ("cream", "bread", "waffle", "choco", "mint", "pink"):
                R_ = self.R(name)
                if e in R_ and R_.index(e) < 3 and ((xx + yy) % 2 == 0 or math.hypot(xx - x, (yy - y - 14) * 1.2) < 17):
                    self.c.set(xx, yy, R_[R_.index(e) + 1])
        Rd, I = self.R("red"), self.R("icing")
        for k in range(14):
            ramp = Rd if (k // 3) % 2 == 0 else I
            self.rect(x - 12 + k, y - 9, x - 12 + k, y - 7, ramp[2])
            self.c.set(x - 12 + k, y - 9, ramp[3])
        self.rect(x - 1, y - 8, x + 1, y - 2, I[2])
        dome = {q for q in ellipse(x, y + 6, 7, 9) if q[1] <= y + 8}
        for (xx, yy) in dome:
            self.c.set(xx, yy, G[3] if xx < x and yy < y + 4 else G[2] if (xx - x) + (yy - y) < 7 else G[1])
        self.rect(x - 8, y + 9, x + 8, y + 10, self.R("gold")[1])
        self.rect(x - 8, y + 9, x + 8, y + 9, self.R("gold")[3])

    # Предметы у стены -------------------------------------------------------------------------

    def jelly(self, x, y, w=22, h=22, ramp="red"):
        """Кубик желе: прозрачный брусок с верхней гранью, бликом и зёрнами сахара."""
        R_, I = self.R(ramp), self.R("icing")
        x0 = int(x - w / 2)
        S = set((xx, yy) for xx in range(x0, x0 + w + 1) for yy in range(y - h, y + 1))
        S -= {(x0, y - h), (x0 + w, y - h), (x0, y), (x0 + w, y)}
        self.put(S, R_, soft=True)
        for yy in range(y - h + 8, y - 3):
            for xx in range(x0 + 4, x0 + w - 5):
                if (xx + yy) % 2 == 0:
                    self.c.set(xx, yy, R_[3])
        self.rect(x0 + 1, y - h, x0 + w - 1, y - h + 4, R_[3])
        self.rect(x0 + 2, y - h + 5, x0 + w - 2, y - h + 5, R_[1])
        self.rect(x0 + 3, y - h + 8, x0 + 4, y - 8, I[3])
        self.rect(x0 + 6, y - h + 8, x0 + 6, y - 14, I[3])
        for k in range(x0 + 3, x0 + w - 1, 4):
            self.c.set(k, y - h + 1 + (k % 3), I[3])

    def candy_box(self, x, y, w=30, h=24):
        """Коробка конфет: розовая, под белой крышкой, красная лента крест-накрест и бант."""
        Pk, I, Rd = self.R("pink"), self.R("icing"), self.R("red")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h + 7, y + 1))
        self.put(S, Pk, soft=False)
        for xx in range(x + 4, x + w - 2, 6):
            self.c.set(xx, y - 5, I[3])
            self.c.set(xx + 3, y - 11, I[3])
        self.bevel(x - 2, y - h, x + w + 2, y - h + 7, I)
        self.rect(x + w // 2 - 2, y - h, x + w // 2 + 2, y, Rd[2])
        self.rect(x + w // 2 - 2, y - h, x + w // 2 - 2, y, Rd[3])
        self.rect(x + w // 2 + 2, y - h, x + w // 2 + 2, y, Rd[1])
        cx = x + w // 2
        bow = ellipse(cx - 6, y - h - 3, 5.4, 3.6) | ellipse(cx + 6, y - h - 3, 5.4, 3.6)
        self.put(bow, Rd, soft=False, cast=False)
        self.fill(ellipse(cx - 6, y - h - 3, 2, 1.2) | ellipse(cx + 6, y - h - 3, 2, 1.2), Rd[0])
        self.rect(cx - 2, y - h - 5, cx + 2, y - h - 1, Rd[2])
        self.c.set(cx - 2, y - h - 5, Rd[3])

    def sugar(self, x, y):
        """Горка рафинада: три белых куба с гранями и искрой."""
        I = self.R("icing")
        for (dx, dy, w) in ((-11, 0, 12), (2, 0, 11), (-5, -11, 12)):
            a, b = x + dx, y + dy
            S = set((xx, yy) for xx in range(a, a + w + 1) for yy in range(b - 10, b + 1))
            self.put(S, [I[0], I[1], I[2], I[3]], soft=False)
            self.rect(a + 1, b - 10, a + w - 1, b - 8, I[3])
            self.rect(a + w - 2, b - 7, a + w - 1, b - 1, I[1])
            self.c.set(a + 3, b - 5, I[3])
            self.c.set(a + 6, b - 3, I[1])

    def stand_lolly(self, x, y, ramp="red", h=18):
        """Леденец на палочке, воткнутый у стены."""
        self.dark(x - 6, y - 1, x + 8, y, 1)
        self.lolly(x, y - h - 9, 9, ramp, stick=h)


# Имя класса улицы у космоса: оставлено для тех, кто берёт его по имени.
Deck = Town


def build_street():
    """Улица той же ширины и с теми же строками пола, что у пиратов: стена до `WALL_Y`, тротуар
    плитками печенья до `CURB_Y`, бордюр карамельной полосой, мостовая мятной глазурью от
    `ROAD_Y`."""
    st = Town()
    c, rng = st.c, st.rng
    I, Pk, Mn, Ch, Gd, Rd = st.R("icing"), st.R("pink"), st.R("mint"), st.R("choco"), st.R("gold"), st.R("red")
    x = 0
    modules = [("bakery", 320), ("candy", 288), ("factory", 352), ("waffle", 256), ("ice", 256), ("alley", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        if kind == "bakery":
            # Пряничная пекарня: витрина с тортами, арочная дверь, вывеска с кренделем.
            st.ginger(x0, 32, x1, WALL_Y)
            st.window(x0 + 30, 92, 118, 78, "cakes")
            st.awning(x0 + 22, x0 + 156, 62, 20, "red", "icing")
            st.door(x0 + 186, 104, 48, WALL_Y - 108, "choco", arch=True)
            st.board(x0 + 252, 74, 36, 32, "pretzel")
            st.round_window(x0 + 270, 150, 13, "pink")
            st.lamp(x0 + 170, 58)
            st.cane(x1 - 10, 32, WALL_Y)
            st.eave(x0, x1, "choco")
        elif kind == "candy":
            # Лавка сладостей: кремовая стена, навес в розовую полоску, банки с драже, леденец.
            st.plain(x0, 32, x1, WALL_Y, "cream", "pink")
            st.window(x0 + 22, 96, 92, 72, "jars")
            st.door(x0 + 140, 100, 46, WALL_Y - 104, "pink")
            st.window(x0 + 208, 96, 56, 72, "jars")
            st.awning(x0 + 10, x0 + 276, 58, 24, "pink", "icing")
            st.hcane(x0, x1, 46, 6)
            st.lolly(x0 + 162, 82, 12, "red")
            st.eave(x0, x1, "pink")
        elif kind == "factory":
            # Шоколадная фабрика: стена плиткой, ворота двумя плитками, вафельные трубы.
            st.tiles(x0, 32, x1, WALL_Y, 44, 30, "choco")
            gx0, gx1 = x0 + 70, x0 + 250
            st.bevel(gx0 - 10, 50, gx1 + 10, WALL_Y, I)
            for xx in range(gx0 - 10, gx1 + 11):
                for yy in range(50, 58):
                    c.set(xx, yy, Rd[2] if ((xx + yy) // 7) % 2 == 0 else I[2])
            st.rect(gx0, 60, gx1, WALL_Y, Ch[0])
            mid = (gx0 + gx1) // 2
            for (a, b) in ((gx0, mid - 2), (mid + 2, gx1)):
                cw = (b - a - 2) // 3
                for col in range(3):
                    for ry in range(62, WALL_Y - 6, 44):
                        ax = a + 1 + col * (cw + 1)
                        st.bevel(ax, ry, ax + cw - 1, min(ry + 41, WALL_Y - 1), [Ch[0], Ch[2], Ch[3], st.R("bread")[3]])
                        st.bevel(ax + 5, ry + 5, ax + cw - 6, min(ry + 36, WALL_Y - 6), [Ch[0], Ch[2], Ch[3], st.R("bread")[3]],
                                 inset=True)
            for a in (mid - 14, mid + 8):
                st.rect(a, 148, a + 5, 160, Gd[2])
                st.rect(a, 148, a + 5, 148, Gd[3])
                st.rect(a, 160, a + 5, 160, Gd[0])
            st.dark(gx0, 60, gx1, 68, 1)
            st.dark(gx0, 69, gx1, 76, 1, dither=True)
            st.dark(gx0, 60, gx0 + 6, WALL_Y, 1)
            # Вывеска фабрики: плитка с откушенным углом на кремовом поле.
            st.bevel(x0 + 268, 66, x1 - 14, 104, st.R("cream"))
            bx = x0 + 280
            st.tiles(bx, 72, bx + 41, 97, 14, 13, "choco", dot=False)
            st.fill(ellipse(bx + 42, 71, 9, 8) & {(xx, yy) for xx in range(bx, bx + 42) for yy in range(72, 98)},
                    st.R("cream")[2])
            st.round_window(x0 + 300, 150, 14, "mint")
            # Вафельные трубы слева.
            for tx, tw in ((x0 + 8, 12), (x0 + 30, 8)):
                for yy in range(32, WALL_Y + 1):
                    for k in range(tw):
                        W = st.R("waffle")
                        c.set(tx + k, yy, W[3] if k == 1 else W[0] if k == tw - 1 else W[1] if (yy + k) % 6 == 0
                              or (yy - k) % 6 == 0 else W[2])
                st.dark(tx + tw, 32, tx + tw + 1, WALL_Y, 1)
            st.board(x0 + 26, 150, 30, 28, "cupcake")
            st.lamp(x0 + 290, 54)
            st.eave(x0, x1, "bread")
        elif kind == "waffle":
            # Вафельный дом: стена в клетку, два окна-пончика, дверь печеньем.
            st.waffle(x0, 32, x1, WALL_Y)
            st.round_window(x0 + 54, 124, 24, "pink")
            st.door(x0 + 106, 98, 46, WALL_Y - 102, "bread", arch=True)
            st.round_window(x0 + 206, 124, 22, "berry")
            st.wave(x0, x1, 60, 3, 16)
            st.hcane(x0 + 14, x0 + 96, 196, 5)
            st.hcane(x0 + 168, x1 - 14, 196, 5)
            st.cane(x1 - 10, 32, WALL_Y)
            st.cane(x0, 32, WALL_Y, 8)
            st.eave(x0, x1, "waffle")
        elif kind == "ice":
            # Киоск мороженого: мятная стена плитками, окно выдачи с рожками, прилавок.
            st.tiles(x0, 32, x1, WALL_Y, 30, 24, "mint", dot=False)
            st.window(x0 + 22, 92, 130, 70, "cones")
            st.bevel(x0 + 12, 174, x0 + 162, 182, st.R("cream"))
            st.rect(x0 + 20, 183, x0 + 154, WALL_Y - 4, st.R("waffle")[1])
            for k in range(8):
                bx = x0 + 24 + k * 16
                st.bevel(bx, 188, bx + 12, 202, st.R("waffle"))
            st.awning(x0 + 14, x0 + 160, 60, 22, "mint", "icing")
            st.door(x0 + 184, 100, 46, WALL_Y - 104, "pink")
            st.board(x0 + 190, 56, 34, 32, "cone")
            st.lamp(x0 + 170, 70)
            st.eave(x0, x1, "pink")
        elif kind == "alley":
            # Проулок: за низкой оградой из тростей мятное небо, облака ваты и горы мороженого.
            st.ginger(x0, 32, x0 + 30, WALL_Y)
            st.ginger(x1 - 30, 32, x1, WALL_Y)
            a, b = x0 + 31, x1 - 31
            for yy in range(32, WALL_Y + 1):
                for xx in range(a, b + 1):
                    k = (yy - 32) / float(WALL_Y - 32)
                    c.set(xx, yy, Mn[2] if k < 0.3 or (k < 0.5 and (xx + yy) % 2) else Mn[3])
            for (cx, cy, sc) in ((a + 30, 70, 1.0), (a + 96, 54, 1.3), (a + 60, 104, 0.8)):
                puff = set()
                for dx, dy, r in ((-10, 0, 6), (-3, -4, 8), (6, -2, 7), (13, 1, 5)):
                    puff |= ellipse(cx + dx * sc, cy + dy * sc, r * sc, r * sc)
                puff = {q for q in puff if q[1] <= cy + 3 * sc and a <= q[0] <= b}
                for q in puff:
                    low = (q[0], q[1] + 1) not in puff or (q[0], q[1] + 2) not in puff
                    c.set(q[0], q[1], Pk[3] if low else I[3])
            for (cx, top, rx, ramp) in ((a + 22, 150, 30, "pink"), (a + 104, 138, 36, "cream"), (a + 62, 162, 40, "berry")):
                hill = {q for q in ellipse(cx, top + 60, rx, 62) if a <= q[0] <= b and q[1] <= WALL_Y}
                R_ = st.R(ramp)
                for q in hill:
                    d = (q[0] - cx) / float(rx)
                    c.set(q[0], q[1], R_[3] if d < -0.45 else R_[2] if d < 0.35 or (q[0] + q[1]) % 2 else R_[1])
                for q in hill:
                    if q[1] < top + 9 + 3 * math.sin(q[0] * 0.5):
                        c.set(q[0], q[1], I[3] if (q[0] - cx) < rx * 0.2 else I[1])
                st.fill({q for q in ellipse(cx, top - 2, 3, 3) if a <= q[0] <= b}, Rd[2])
            # Ограда из карамельных тростей и перила.
            for xx in range(a + 6, b - 4, 16):
                st.cane(xx, WALL_Y - 30, WALL_Y, 5)
            st.hcane(a, b, WALL_Y - 34, 5)
            st.dark(a, 32, a + 3, WALL_Y, 1)
            st.cane(x0 + 26, 32, WALL_Y, 6)
            st.cane(x1 - 31, 32, WALL_Y, 6)
            st.eave(x0, x0 + 31, "choco")
            st.eave(x1 - 31, x1, "choco")
            st.rect(a, 0, b, 31, Mn[2])
            st.hcane(a, b, 22, 7)
            for k, xx in enumerate(range(a + 8, b - 4, 14)):
                col = (Pk, Gd, Mn, Rd)[k % 4]
                flag = poly([(xx, 29), (xx + 9, 29), (xx + 4.5, 41)])
                st.fill(flag, col[2])
                st.fill({q for q in flag if q[0] > xx + 5}, col[1])
        x += w
    # Тень у пола.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Тротуар: плитки печенья рядами, зубчатый край и дырочки.
    Sl = st.R("slab")
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    st.rect(0, WALL_Y + 1, SW - 1, CURB_Y - 1, Sl[0])
    for ri, (y0, h) in enumerate(rows):
        pw = 40 + ri * 6
        xx = -((ri * 23) % pw)
        while xx < SW:
            a, b = max(xx + 1, 0), min(xx + pw - 1, SW - 1)
            yb = min(y0 + h - 1, CURB_Y - 1)
            st.bevel(a, y0, b, yb, Sl)
            st.noise(a + 1, y0 + 1, b - 1, yb - 1, Sl, 0.03)
            for gx in range(a + 3, b - 2, 4):
                c.set(gx, y0, Sl[1])
                c.set(gx, yb, Sl[0])
            for gy in range(y0 + 4, yb - 2, 5 + ri):
                for gx in range(a + 7, b - 5, 9 + ri * 2):
                    c.set(gx, gy, Sl[1])
                    c.set(gx + 1, gy + 1, Sl[3])
            xx += pw
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Бордюр: кромка глазури и карамельная полоса наискось.
    for xx in range(SW):
        c.set(xx, CURB_Y, I[3])
        c.set(xx, CURB_Y + 1, I[2])
        for yy in range(CURB_Y + 2, ROAD_Y):
            ramp = Pk if ((xx + yy) // 8) % 2 == 0 else I
            c.set(xx, yy, ramp[2 if yy < ROAD_Y - 2 else 1])
    Rr = st.R("road")
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, Rr[0])
    # Мостовая: плитки мятной глазури рядами, ряды к зрителю выше, глянец и посыпка.
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Rr[0])
    y = ROAD_Y + 2
    h = 14
    row = 0
    while y < SH:
        pw = 52 + row * 6
        xx = -((row * 19) % pw)
        while xx < SW:
            a, b = max(xx + 1, 0), min(xx + pw - 1, SW - 1)
            yb = min(y + h - 1, SH - 1)
            if b > a and yb > y:
                t = rng.choice((0, 0, 0, 1))
                ramp = Rr if t == 0 else [Rr[0], Rr[1], Rr[1], Rr[2]]
                st.bevel(a, y, b, yb, ramp)
                st.noise(a + 1, y + 1, b - 1, yb - 1, ramp, 0.02)
                # Глянец леденца: две косые черты.
                if rng.random() < 0.45:
                    for k in range(min(8, yb - y - 4)):
                        c.set(a + 6 + k, yb - 3 - k, Rr[3])
                        if k % 2 == 0:
                            c.set(a + 10 + k, yb - 3 - k, Rr[3])
                # Посыпка.
                if rng.random() < 0.3 and b - a > 20 and yb - y > 8:
                    sx, sy = rng.randint(a + 8, b - 8), rng.randint(y + 4, yb - 4)
                    col = rng.choice((Pk, Gd, I, Rd))
                    c.set(sx, sy, col[2])
                    c.set(sx + 1, sy, col[2])
                    c.set(sx + 1, sy + 1, Rr[0])
            xx += pw
        y += h
        h += 3
        row += 1
    # Белый пунктир глазурью вдоль бордюра.
    for xx in range(0, SW, 40):
        st.rect(xx + 6, ROAD_Y + 5, xx + 26, ROAD_Y + 6, I[2])
        st.rect(xx + 6, ROAD_Y + 5, xx + 26, ROAD_Y + 5, I[3])
        st.rect(xx + 5, ROAD_Y + 7, xx + 27, ROAD_Y + 7, Rr[0])
    # Лужи розового сиропа.
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            e = c.get(px, py)
            if e is None:
                continue
            c.set(px, py, Pk[2] if e in (Rr[2], Rr[3]) else Pk[1])
        for k in range(px0 - 30, px0 + 30, 9):
            c.set(k, 368, Pk[3])
            c.set(k + 1, 368, Pk[3])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("jelly", 20), ("jelly2", 44), ("box", 290), ("lolly", 600), ("lolly2", 618), ("sugar", 680),
                       ("box", 870), ("box", 898), ("jelly2", 1150), ("sugar", 1400), ("jelly", 1590)):
        yb = WALL_Y + 8
        if kind == "jelly":
            st.jelly(px, yb, 22, 24, "red")
        elif kind == "jelly2":
            st.jelly(px, yb, 20, 18, "berry")
        elif kind == "box":
            st.candy_box(px, yb)
        elif kind == "lolly":
            st.stand_lolly(px, yb, "red", 20)
        elif kind == "lolly2":
            st.stand_lolly(px, yb, "mint", 12)
        else:
            st.sugar(px, yb)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки карамельные и белые, волна малиновая, пыль сахарной пудрой
    и крошкой; стрелка «вперёд» красная, как бант героя, чтобы не терялась на пастельной улице."""
    p = Pal(OUTLINE)
    p.add("white", [0xD6BFCC, 0xF4E4E0, 0xFFF7EC, 0xFFFFFF])
    if go:
        p.add("gold", [0x7A1430, 0xB7243A, 0xE63545, 0xFFB0A8])
    else:
        p.add("gold", [0xB8641C, 0xF0A030, 0xF8CF6A, 0xFFF4C0])
    p.add("blue", [0x8E2250, 0xD04E88, 0xFF8EB6, 0xFFD6E6])
    p.add("dust", [0x9A7A5A, 0xD0AE84, 0xF2DCB0, 0xFFF7EC])
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
        import sweets16
        items = sprites_own()
        for arg in sys.argv:
            if arg.startswith("--keys="):
                items = {k: items[k] for k in arg.split("=", 1)[1].split(",")}
        sweets16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], items, scale=1, max_w=FW * 12)
