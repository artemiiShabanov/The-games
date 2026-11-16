# -*- coding: utf-8 -*-
"""Набор «Ниндзя» для битемапа × 16/32-bit (#137): зеркало `space_brawl16.py` и `pixel_brawl16.py`.
Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты оттуда как есть (демка
`fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и улица свои.

Бойцы: герой это ниндзя в тёмно-синем: капюшон с прорезью глаз, красный шарф с двумя концами за
спиной, рукоять меча над плечом, белые обмотки на голенях, таби; громила это сумоист: голый торс
с животом, красный пояс маваси с кистями, пучок волос на темени; враг с ножом это ниндзя чужого
клана в красном, чёрная маска с завязками, в руке серп на цепи с гирькой (кусаригама); босс это
сёгун: чёрный лаковый доспех с золотой шнуровкой, шлем с двумя золотыми рогами, красная маска
демона с клыками и белыми усами, меч за поясом. Улица это старый городок на закате: чайный дом с
бумажными ширмами и занавесью норэн, садовая стена с круглым окном и клёнами, ворота усадьбы,
додзё, лавка сакэ с бочками в соломе, проулок с тории и замком на утёсе; настил из досок, каменная
дорожка с мхом и кленовыми листьями.

    python3 tools/ninja_brawl16.py --preview out.png   # лист всех лент
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

# Обводка та же, что K в `ninja16.PALETTE`.
OUTLINE = 0x121018


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    """Ниндзя: синий костюм (SEA и NAVY основы), красный шарф, белые обмотки, тёмные таби."""
    p = Pal(OUTLINE)
    p.add("suit", [0x1A1C48, 0x2A3378, 0x3E4EA8, 0x6E84DC])
    p.add("scarf", [0x6A1418, 0xA62226, 0xD93632, 0xF9765A])
    p.add("wrap", [0x787A8A, 0xB7B4B2, 0xF3EEE2, 0xFFFFFF])
    p.add("skin", [0x7A3A30, 0xB8785A, 0xF2C89A, 0xFFE6C8])
    p.add("dark", [0x0E0C16, 0x1E1A2A, 0x353143, 0x565068])
    p.add("gold", [0x6E4A14, 0xB2762E, 0xF4CB52, 0xFFF0A8])
    return Look("ninja", p, Body(1.0, 1.0))


def thug_look():
    """Сумоист: кожа, красный маваси, чёрные волосы, белые бинты на запястьях и щиколотках."""
    p = Pal(OUTLINE)
    p.add("skin", [0x7A4634, 0xB87A58, 0xE8B088, 0xFFD8B4])
    p.add("belt", [0x5A1014, 0x961E20, 0xD93632, 0xF8765A])
    p.add("hair", [0x08080E, 0x14121C, 0x26222E, 0x4A4658])
    p.add("tape", [0x787A8A, 0xB7B4B2, 0xF3EEE2, 0xFFFFFF])
    p.add("gold", [0x6E4A14, 0xB2762E, 0xF4CB52, 0xFFF0A8])
    return Look("sumo", p, Body(1.0, 1.24))


def knife_look():
    """Ниндзя чужого клана: красная куртка, чёрные маска, штаны и перчатки, серп на цепи."""
    p = Pal(OUTLINE)
    p.add("robe", [0x5A1014, 0x961E20, 0xD93632, 0xF8765A])
    p.add("dark", [0x0E0C16, 0x1E1A2A, 0x353143, 0x565068])
    p.add("skin", [0x7A3A30, 0xB8785A, 0xF2C89A, 0xFFE6C8])
    p.add("metal", [0x3A3C4C, 0x787A8A, 0xB7B4B2, 0xF3EEE2])
    p.add("wood", [0x4A2C12, 0x7E5020, 0xB2762E, 0xDCA858])
    p.add("gold", [0x6E4A14, 0xB2762E, 0xF4CB52, 0xFFF0A8])
    return Look("chain", p, Body(1.0, 0.9))


def boss_look():
    """Сёгун: чёрный лак доспеха, золото шнуровки и рогов, багровая ткань, красная маска демона."""
    p = Pal(OUTLINE)
    p.add("armor", [0x0E0C16, 0x201C2E, 0x38344A, 0x646080])
    p.add("gold", [0x6E4A14, 0xB2762E, 0xF4CB52, 0xFFF0A8])
    p.add("cloth", [0x3A0C1C, 0x661630, 0x94243C, 0xC24C54])
    p.add("mask", [0x5A1014, 0xA01E1E, 0xE23A2E, 0xFF8A62])
    p.add("bone", [0x787A8A, 0xB7B4B2, 0xF3EEE2, 0xFFFFFF])
    p.add("skin", [0x7A3A30, 0xB8785A, 0xF2C89A, 0xFFE6C8])
    p.add("eye", [0x08060C, 0x3A2A08, 0xF4CB52, 0xFFF6B0])
    return Look("shogun", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _dots(c, a, b, col, S=None, alt=None):
    """Пиксельная линия от `a` к `b`; `S` маска, в которой она видна, `alt` цвет через пиксель."""
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for i in range(n + 1):
        q = lerp(a, b, i / n)
        xy = (int(round(q[0])), int(round(q[1])))
        if S is None or xy in S:
            c.set(xy[0], xy[1], col if alt is None or i % 2 == 0 else alt)


def _floor(j):
    """Строка, ниже которой не опускаются шарф и цепь: иначе лежащий боец приподнялся бы над полом
    (кадр ставится на пол по нижнему пикселю)."""
    return max(j[k][1] for k in ("an_n", "an_f", "kn_n", "kn_f", "hip", "neck", "head")) + 3


def _band(S, origin, axis, t0, t1):
    """Поясок на конечности: пиксели маски `S`, у которых проекция на ось от `origin` в [t0, t1]."""
    return {q for q in S if t0 <= (q[0] - origin[0]) * axis[0] + (q[1] - origin[1]) * axis[1] <= t1}


def _rows(c, S, origin, axis, step, col, alt=None, phase=0.0):
    """Ряды шнуровки доспеха: полосы поперёк оси `axis` через `step` пикселей, пунктиром."""
    for (x, y) in S:
        t = (x - origin[0]) * axis[0] + (y - origin[1]) * axis[1] + phase
        if int(math.floor(t)) % step == 0 and c.get(x, y) is not None:
            if (x + y) % 2 == 0:
                c.set(x, y, col)
            elif alt is not None:
                c.set(x, y, alt)


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    du = _unit(sh, el)
    upper_ramp = {"ninja": "suit", "sumo": "skin", "chain": "robe", "shogun": "cloth"}[kind]
    fore_ramp = {"ninja": "suit", "sumo": "skin", "chain": "robe", "shogun": "armor"}[kind]
    fat = 1.12 if kind == "sumo" else 1.0
    upper = capsule(sh, el, 4.3 * s * b * fat, 3.5 * s * b * fat) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b * fat,
                                                                           4.5 * s * b * fat)
    if kind == "sumo":
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.6 * s * b, 3.9 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
    put(c, pal, upper, pal[upper_ramp], far=far, soft=True)
    fore = capsule(el, ha, 3.6 * s * b * fat, 3.0 * s * b * fat)
    put(c, pal, fore, pal[fore_ramp], far=far)
    if kind == "ninja":
        # Наруч тэкко: тёмная накладка от середины предплечья до кисти, белая тесьма у запястья.
        put(c, pal, capsule(add(ha, d, -7.5 * s), add(ha, d, -2.6 * s), 3.7 * s, 3.4 * s), pal["dark"], far=far)
        q = add(ha, d, -2.8 * s)
        n = (d[1], -d[0])
        _dots(c, add(q, n, -2.6), add(q, n, 2.6), pal["wrap"][1 if far else 2])
    elif kind == "sumo":
        # Бинт на запястье.
        put(c, pal, _band(fore, ha, d, -6.0 * s, -1.5 * s), pal["tape"], far=far, cast=False)
    elif kind == "chain":
        # Чёрный наруч с красной перевязью.
        put(c, pal, capsule(add(ha, d, -8.0 * s), add(ha, d, -2.6 * s), 3.5 * s * b, 3.3 * s * b), pal["dark"], far=far)
        q = add(ha, d, -5.2 * s)
        n = (d[1], -d[0])
        _dots(c, add(q, n, -2.2), add(q, n, 2.2), pal["robe"][1 if far else 2])
    elif kind == "shogun":
        # Золотая манжета наруча и наплечник содэ: пластина поверх плеча с рядами шнуровки.
        put(c, pal, capsule(add(ha, d, -5.0 * s), add(ha, d, -2.4 * s), 4.2 * s * b, 4.2 * s * b), pal["gold"], far=far)
        n = (du[1], -du[0])
        a0, a1 = add(sh, du, -4.0 * s), add(sh, du, 10.5 * s)
        w0, w1 = 6.4 * s * b, 7.0 * s * b
        plate = poly([add(a0, n, -w0), add(a0, n, w0), add(a1, n, w1), add(a1, n, -w1)])
        put(c, pal, plate, pal["armor"], far=far, soft=True)
        _rows(c, plate, a0, du, 4, pal["gold"][1 if far else 2], phase=1.0)
        hem = {q for q in plate if ((q[0] - a1[0]) * du[0] + (q[1] - a1[1]) * du[1]) > -1.6}
        recolor(c, hem, lambda x, y, e: pal["gold"][1 if far else 2])
    fist = add(ha, d, 1.2 * s)
    fr = min(b, 1.15) * (1.15 if kind == "sumo" else 1.0)
    fs = ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr)
    fist_ramp = {"ninja": "skin", "sumo": "skin", "chain": "dark", "shogun": "armor"}[kind]
    put(c, pal, fs, pal[fist_ramp], far=far)
    if kind == "chain" and side == "n":
        # Кусаригама вдоль предплечья вперёд: древко, на конце клюв серпа, от пятки древка
        # свисает цепь с гирькой.
        n = (d[1], -d[0])
        if n[1] > 0:
            n = (-n[0], -n[1])
        butt, tip = add(fist, d, -3.5), add(fist, d, 9.0 * s)
        lim = _floor(j)
        wv = p.get("wave", 0.0)
        w_end = (butt[0] - 4.0 - wv, min(butt[1] + 17.0, lim - 3))
        mid = (butt[0] - 0.5, min(butt[1] + 9.0, lim - 3))
        _dots(c, butt, mid, pal["metal"][3], alt=pal["metal"][1])
        _dots(c, mid, w_end, pal["metal"][1], alt=pal["metal"][3])
        put(c, pal, ellipse(w_end[0], w_end[1], 2.9, 2.9), pal["metal"], cast=False)
        put(c, pal, capsule(butt, tip, 1.5, 1.4), pal["wood"], cast=False)
        blade = poly([add(tip, d, -2.0), add(tip, d, 1.8), add(add(tip, d, 1.6), n, 5.0), add(add(tip, d, -0.6), n, 9.0),
                      add(add(tip, d, -4.4), n, 12.5), add(add(tip, d, -2.6), n, 7.5), add(add(tip, d, -1.8), n, 3.0)])
        put(c, pal, blade, pal["metal"], cast=False)
        put(c, pal, capsule(add(tip, d, -2.6), add(tip, d, -1.4), 1.9, 1.9), pal["gold"], cast=False)


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    pants = {"ninja": "suit", "sumo": "skin", "chain": "robe", "shogun": "cloth"}[kind]
    shins = {"ninja": "wrap", "sumo": "skin", "chain": "dark", "shogun": "armor"}[kind]
    boots = {"ninja": "dark", "sumo": "skin", "chain": "dark", "shogun": "armor"}[kind]
    fat = {"ninja": 1.08, "sumo": 1.14, "chain": 1.04, "shogun": 1.1}[kind]
    thigh = capsule(hp, kn, 6.0 * s * b * fat, 4.8 * s * b * fat)
    put(c, pal, thigh, pal[pants], far=far, soft=True)
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    top_h = {"ninja": 4, "sumo": 4, "chain": 6, "shogun": 6}[kind] * s
    boot = capsule(add(an, sd, -top_h), an, 4.5 * s * b, 4.1 * s * b)
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
    shin = capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b * (fat if kind != "ninja" else 1.0), 4.0 * s * b)
    put(c, pal, boot | foot, pal[boots], far=far)
    put(c, pal, shin, pal[shins], far=far)
    if kind == "ninja":
        # Обмотки голени: косые витки тенью, штанина нависает над коленом.
        W = pal["wrap"]
        for k in range(3, 17, 4):
            q = add(kn, sd, (k + 2.0) * s)
            for t in range(-4, 5):
                xy = (int(round(q[0] + fwd[0] * t + sd[0] * t * 0.35)), int(round(q[1] + fwd[1] * t + sd[1] * t * 0.35)))
                if xy in shin and c.get(*xy) in (W[1], W[2], W[3]):
                    c.set(xy[0], xy[1], W[0])
        put(c, pal, ellipse(kn[0], kn[1], 5.2 * s, 4.6 * s), pal["suit"], far=far, soft=True, cast=False)
        if not far:
            # Разрез таби между пальцами.
            q = add(add(an, sd, 2.4 * s), fwd, 5.0 * s)
            c.set(round(q[0]), round(q[1]), pal["dark"][0])
    elif kind == "sumo":
        # Бинт на щиколотке.
        put(c, pal, _band(shin | boot, an, sd, -7.0 * s, -2.5 * s), pal["tape"], far=far, cast=False)
    elif kind == "chain":
        # Красная перевязь под коленом.
        q = add(kn, sd, 4.0 * s)
        _dots(c, add(q, fwd, -4.0), add(q, fwd, 4.0), pal["robe"][1 if far else 2], S=shin)
    elif kind == "shogun":
        # Набедренник хайдатэ с рядами шнуровки, золотой наколенник, полоса на поноже.
        th = _unit(hp, kn)
        n = (th[1], -th[0])
        a0, a1 = add(hp, th, 2.0 * s), add(hp, th, 13.0 * s)
        w = 7.4 * s * b
        plate = poly([add(a0, n, -w * 0.9), add(a0, n, w * 0.9), add(a1, n, w), add(a1, n, -w)]) & (thigh | capsule(
            a0, a1, w, w))
        put(c, pal, plate, pal["armor"], far=far, soft=True, cast=False)
        _rows(c, plate, a0, th, 4, pal["gold"][1 if far else 2], phase=2.0)
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 3.0 * s, 3.2 * s), pal["gold"], far=far, cast=False)
        if not far:
            _dots(c, add(add(kn, sd, 5.0 * s), fwd, 2.0 * s), add(add(an, sd, -top_h), fwd, 2.0 * s), pal["gold"][2],
                  S=shin, alt=pal["gold"][1])
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    recolor(c, sole, lambda x, y, e: pal[boots][0])


def _back(c, look, j, p):
    """То, что за спиной, рисуется до туловища: у ниндзя два конца шарфа и рукоять меча над
    плечом, у сёгуна ножны меча за поясом."""
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    if kind == "ninja":
        lim = _floor(j)
        wv = p.get("wave", 0.0)
        base = P(N, -5.0, 1.0)
        for (ln, dy, r0) in ((24.0, 1.0 + wv, 2.7), (17.0, 9.0 - wv * 0.6, 2.3)):
            mid = (base[0] - ln * 0.5, base[1] + dy * 0.15 - 1.5)
            end = (base[0] - ln, base[1] + dy)
            S = capsule(base, mid, r0, r0 * 0.9) | capsule(mid, end, r0 * 0.9, 1.5)
            S = {q for q in S if q[1] <= lim and q[0] >= 2}
            put(c, pal, S, pal["scarf"], cast=False)
        # Рукоять меча: оплётка тёмная с золотыми ромбами, цуба и навершие золотом.
        g0, g1 = P(N, -9.6, 7.0), P(N, -15.0, 18.5)
        put(c, pal, capsule(g0, g1, 1.6, 1.5), pal["dark"], cast=False)
        for k in (0.3, 0.55, 0.8):
            q = lerp(g0, g1, k)
            c.set(round(q[0]), round(q[1]), pal["gold"][2])
        put(c, pal, ellipse(g1[0], g1[1], 1.9, 1.9), pal["gold"], cast=False)
        gd = _unit(g0, g1)
        gn = (gd[1], -gd[0])
        put(c, pal, capsule(add(g0, gn, -3.2), add(g0, gn, 3.2), 1.3, 1.3), pal["gold"], cast=False)
    elif kind == "shogun":
        # Ножны уходят от пояса назад и чуть вниз.
        a0, a1 = P(H, -3.0, 4.5), P(H, -19.0, -1.5)
        put(c, pal, capsule(a0, a1, 1.9 * s, 1.5 * s), pal["armor"], soft=False)
        q = lerp(a0, a1, 0.55)
        put(c, pal, capsule(add(q, _unit(a0, a1), -1.0), add(q, _unit(a0, a1), 1.0), 2.2 * s, 2.2 * s), pal["gold"],
            cast=False)
        put(c, pal, ellipse(a1[0], a1[1], 1.9 * s, 1.9 * s), pal["gold"], cast=False)


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    pelvis_ramp = {"ninja": "suit", "sumo": "belt", "chain": "dark", "shogun": "cloth"}[kind]
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[pelvis_ramp], soft=True)
    belly = {"ninja": 0.0, "sumo": 2.6, "chain": 0.0, "shogun": 1.4}[kind]
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "sumo":
        # Живот нависает над поясом, грудь тяжёлая.
        tor |= ellipse(*P(lerp(N, H, 0.63), 6.0, 0), 10.0 * s * b, 10.6 * s)
        tor |= ellipse(*P(lerp(N, H, 0.27), 3.6, 0), 7.4 * s * b, 6.0 * s)
    elif kind == "shogun":
        tor |= ellipse(*P(lerp(N, H, 0.6), 3.6, 0), 7.4 * s * b, 7.0 * s)
    main = {"ninja": "suit", "sumo": "skin", "chain": "robe", "shogun": "armor"}[kind]
    put(c, pal, tor, pal[main], soft=True)
    # Пояс.
    if kind == "sumo":
        belt = _sumo_belt(P, H)
    else:
        belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    belt_ramp = {"ninja": "dark", "sumo": "belt", "chain": "dark", "shogun": "gold"}[kind]
    put(c, pal, belt, pal[belt_ramp], cast=False)
    bk = P(H, 4.6, 4.1)
    if kind == "ninja":
        # Запах куртки, ремень меча наискось, красный узел пояса.
        _dots(c, P(N, 4.6, -1), P(lerp(N, H, 0.62), 0.5, 0), pal["suit"][1], S=tor)
        _dots(c, P(N, 5.6, -1), P(lerp(N, H, 0.62), 1.5, 0), pal["suit"][3], S=tor)
        _dots(c, P(N, -7.0, -4), P(lerp(N, H, 0.86), 6.4, 0), pal["gold"][1], S=tor, alt=pal["gold"][2])
        put(c, pal, ellipse(bk[0], bk[1], 2.0 * s, 1.8 * s), pal["scarf"], cast=False)
        q = add(bk, up, -3.2 * s)
        put(c, pal, capsule(bk, q, 1.2, 0.9), pal["scarf"], cast=False)
    elif kind == "sumo":
        # Складка под грудью, пупок, узел маваси спереди и кисти сагари под ним.
        Sk = pal["skin"]
        a = P(lerp(N, H, 0.4), 2.0, 0)
        for k in range(7):
            q = add(add(a, rt, k * 1.25 * s * b), up, -abs(k - 3.6) * 0.5 + 1.0)
            if c.get(round(q[0]), round(q[1])) in (Sk[2], Sk[3]):
                c.set(round(q[0]), round(q[1]), Sk[1])
        q = P(lerp(N, H, 0.7), 14.0, 0)
        c.set(round(q[0]), round(q[1]), Sk[0])
        c.set(round(q[0]), round(q[1]) - 1, Sk[1])
    elif kind == "chain":
        # Запах куртки тенью, чёрный ворот у шеи, золотая пряжка, сюрикен за поясом.
        _dots(c, P(N, 4.4, -1), P(lerp(N, H, 0.62), 0.4, 0), pal["robe"][0], S=tor)
        _dots(c, P(N, 5.4, -1), P(lerp(N, H, 0.62), 1.4, 0), pal["robe"][3], S=tor)
        collar = poly([P(N, -2.0, 1), P(N, 5.0, 1), P(N, 3.4, -4), P(N, 1.0, -5.5)]) & tor
        put(c, pal, collar, pal["dark"], cast=False)
        put(c, pal, ellipse(bk[0], bk[1], 1.6 * s, 1.5 * s), pal["gold"], cast=False)
        q = P(H, 0.5, 4.1)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            c.set(round(q[0]) + dx, round(q[1]) + dy, pal["metal"][3 if (dx, dy) == (0, 0) else 2])
    elif kind == "shogun":
        # Ряды золотой шнуровки по кирасе, герб на груди, красная пряжка, рукоять меча у пояса.
        _rows(c, tor - belt, N, (-up[0], -up[1]), 5, pal["gold"][2], alt=pal["gold"][1], phase=1.0)
        q = P(lerp(N, H, 0.3), 5.2, 0)
        put(c, pal, ellipse(q[0], q[1], 3.2 * s, 3.2 * s), pal["gold"], cast=False)
        put(c, pal, ellipse(q[0], q[1], 1.5 * s, 1.5 * s), pal["mask"], cast=False)
        put(c, pal, ellipse(bk[0], bk[1], 1.9 * s, 1.7 * s), pal["mask"], cast=False)
        g0, g1 = P(H, 5.0, 5.4), P(H, 13.0, 8.2)
        put(c, pal, capsule(g0, g1, 1.5 * s, 1.4 * s), pal["cloth"], cast=False)
        for k in (0.3, 0.6):
            q = lerp(g0, g1, k)
            c.set(round(q[0]), round(q[1]), pal["gold"][2])
        put(c, pal, ellipse(g1[0], g1[1], 1.8 * s, 1.8 * s), pal["gold"], cast=False)
        gd = _unit(g0, g1)
        put(c, pal, capsule(add(g0, (gd[1], -gd[0]), -3.0 * s), add(g0, (gd[1], -gd[0]), 3.0 * s), 1.3, 1.3), pal["gold"],
            cast=False)


def _sumo_belt(P, H):
    return poly([P(H, 12.6, 9.4), P(H, 12.0, 3.0), P(H, -7.6, 2.4), P(H, -7.4, 8.4)])


def _front(c, look, j, p):
    """Пояс маваси сумоиста поверх ближнего бедра: широкая лента вокруг живота, узел спереди,
    кисти сагари свисают под ним."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    for k in range(5):
        a0 = P(H, 6.0 + k * 1.5, 3.4)
        a1 = (a0[0] + (k - 2) * 0.4, a0[1] + 10.0 * s)
        _dots(c, a0, a1, pal["tape"][2 if k % 2 == 0 else 1])
        c.set(round(a1[0]), round(a1[1]), pal["gold"][2])
    belt = _sumo_belt(P, H)
    put(c, pal, belt, pal["belt"], soft=True)
    # Складки ленты и золотая кайма сверху.
    _dots(c, P(H, -7.0, 5.4), P(H, 12.0, 6.2), pal["belt"][1], S=belt)
    _dots(c, P(H, -7.2, 8.2), P(H, 12.4, 9.2), pal["gold"][2], S=belt, alt=pal["gold"][1])
    put(c, pal, ellipse(*P(H, 12.4, 5.8), 2.4 * s, 3.2 * s), pal["belt"], cast=False)


def _tails(c, look, j, p, long):
    """Полы куртки чужого ниндзя (короткие) и юбка доспеха сёгуна кусадзури (длинная, пластинами,
    с золотой каймой по низу)."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = (21 if long else 11) * s
    sway = -p["lean"] * 0.2 - (p["th_n"] + p["th_f"]) * 0.05
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 7.0 * s * b), up, 3 * s),
           (H[0] + (9 if long else 6) * s * b + sway * 0.3, H[1] + ln * 0.9), (H[0] - 1 * s + sway, H[1] + ln),
           (H[0] - (12 if long else 9) * s * b + sway, H[1] + ln * 0.92)]
    S = poly(pts)
    put(c, pal, S, pal["armor" if long else "robe"], soft=True)
    if long:
        # Пластины: вертикальные швы, ряды шнуровки, кайма.
        A = pal["armor"]
        for (x, y) in S:
            if int(round(x - H[0] - sway * (y - H[1]) / ln)) % 7 == 0 and c.get(x, y) in (A[2], A[3]):
                c.set(x, y, A[1])
        _rows(c, S, H, (0.0, 1.0), 6, pal["gold"][2], alt=pal["gold"][1], phase=2.0)
        hem = {q for q in S if (q[0], q[1] + 1) not in S or (q[0], q[1] + 2) not in S}
        recolor(c, hem, lambda x, y, e: pal["gold"][2] if (x + y) % 3 else pal["gold"][1])
    else:
        hem = {q for q in S if (q[0], q[1] + 1) not in S or (q[0], q[1] + 2) not in S}
        recolor(c, hem, lambda x, y, e: pal["dark"][2])


def _head(c, look, j, p, hurt=False):
    pal, s, kind = look.pal, look.body.s, look.kind
    hc = j["head"]
    ang = p["lean"] + p["tilt"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    wv = p.get("wave", 0.0)

    def H(dx, dy):
        return (hc[0] + (dx * ca - dy * sa) * s, hc[1] + (dx * sa + dy * ca) * s)

    def local(x, y):
        dx, dy = (x - hc[0]) / s, (y - hc[1]) / s
        return (dx * ca + dy * sa, -dx * sa + dy * ca)

    def dot(dx, dy, col, S=None):
        q = H(dx, dy)
        xy = (int(round(q[0])), int(round(q[1])))
        if S is None or xy in S:
            c.set(xy[0], xy[1], col)

    if kind in ("ninja", "chain"):
        cloth = pal["suit" if kind == "ninja" else "dark"]
        sk = pal["skin"]
        neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
        put(c, pal, neck, cloth)
        if kind == "chain":
            # Завязки маски на затылке: две красные ленты, качаются.
            for (ex, ey, r0) in ((-15.0 - wv, -6.5, 1.5), (-13.5 - wv * 0.6, 1.5, 1.3)):
                put(c, pal, capsule(H(-6.5, -3.0), H(ex, ey), r0, 0.8), pal["robe"], cast=False)
        hood = ellipse(*H(-0.3, -2.0), 7.8 * s, 8.3 * s, ang)
        if kind == "ninja":
            # Капюшон чуть оттянут назад складкой.
            hood |= poly([H(-6.0, -6.0), H(-9.4, 1.5), H(-5.0, 5.5), H(0.0, 0.0)])
        put(c, pal, hood, cloth, soft=True)
        # Прорезь глаз: полоса кожи спереди, сверху тень от капюшона.
        top, bot = (-4.9, -0.6) if kind == "ninja" else (-3.9, -1.1)
        slit = {q for q in hood if local(*q)[0] > (-0.6 if kind == "ninja" else 0.2) and top <= local(*q)[1] <= bot}
        put(c, pal, slit, sk, cast=False)
        recolor(c, {q for q in slit if (q[0], q[1] - 1) not in slit}, lambda x, y, e: sk[1])
        if kind == "ninja":
            # Красный шарф закрывает подбородок и шею, сзади узел.
            wrap = ellipse(*H(0.6, 6.6), 6.6 * s, 3.5 * s, ang)
            put(c, pal, wrap, pal["scarf"], soft=True)
            put(c, pal, ellipse(*H(-6.4, 6.0), 2.3 * s, 2.5 * s), pal["scarf"], cast=False)
            # Складки капюшона.
            for dx, dy in ((-4.6, -6.6), (-5.6, -5.4), (-6.2, -4.0), (-3.2, 2.6), (-4.4, 1.6)):
                dot(dx, dy, cloth[1], hood)
        else:
            # Стальная пластина на лбу, складка маски на переносице.
            plate = {q for q in hood if local(*q)[0] > 0.8 and -7.4 <= local(*q)[1] <= -5.0}
            put(c, pal, plate, pal["metal"], cast=False)
            dot(4.0, -6.2, pal["metal"][0], plate)
            for dx, dy in ((2.2, 1.2), (3.4, 2.2), (4.6, 3.2)):
                dot(dx, dy, cloth[3], hood)
        ex, ey = (4.6, -2.4) if kind == "ninja" else (4.4, -2.3)
        if hurt:
            for k in (-1.4, -0.4, 0.6, 1.6):
                dot(ex + k, ey + 0.2, sk[0], slit)
        else:
            dot(ex, ey, pal["dark"][0], slit)
            dot(ex, ey + 1.0, pal["dark"][0], slit)
            dot(ex + 1.0, ey, pal["wrap"][3] if kind == "ninja" else pal["metal"][3], slit)
            dot(ex + 1.0, ey + 1.0, sk[3], slit)
            if kind == "chain":
                # Сведённая бровь.
                dot(ex - 1.0, ey - 1.2, pal["dark"][0], slit)
                dot(ex, ey - 1.0, pal["dark"][0], slit)
                dot(ex + 1.0, ey - 0.6, pal["dark"][1], slit)
        return
    sk = pal["skin"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
    put(c, pal, neck, sk)
    if kind == "sumo":
        H_ = pal["hair"]
        skull = ellipse(*H(0.0, -2.6), 8.5 * s, 8.5 * s, ang)
        jaw = poly([H(-4.2, 1.0), H(7.4, 0.4), H(7.6, 4.8), H(3.6, 8.8), H(-3.6, 7.8)])
        nose = poly([H(7.2, -1.6), H(9.6, 1.4), H(7.2, 2.6)])
        face = skull | jaw | nose
        put(c, pal, face, sk, soft=True)
        # Волосы гладко назад, пучок тёнмагэ уложен на темя, белая перевязь.
        hair = {q for q in skull if local(*q)[1] < -6.6 or (local(*q)[0] < -3.4 and local(*q)[1] < 1.6)}
        put(c, pal, hair, H_, soft=True, cast=False)
        knot = capsule(H(-6.4, -9.6), H(1.6, -12.4), 2.1 * s, 1.7 * s)
        put(c, pal, knot, H_, cast=False)
        dot(-3.4, -10.8, pal["tape"][2])
        dot(-3.0, -11.8, pal["tape"][2])
        # Ухо, второй подбородок, румянец.
        dot(-1.6, -1.2, sk[1], face)
        dot(-1.6, -0.2, sk[1], face)
        dot(-0.8, 0.6, sk[1], face)
        for k in range(5):
            dot(0.6 + k * 1.1, 6.6 - abs(k - 2) * 0.3, sk[1], face)
        dot(3.4, 2.4, pal["belt"][3], face)
        dot(4.4, 2.8, pal["belt"][3], face)
        ex, ey = 5.0, -1.6
        if hurt:
            for k in (-1.5, -0.5, 0.5, 1.5):
                dot(ex + k, ey, sk[0], face)
            dot(ex - 1.5, ey - 1.0, sk[0], face)
        else:
            # Тяжёлая бровь и узкий глаз.
            put(c, pal, capsule(H(2.4, -4.2), H(7.0, -3.0), 1.1 * s, 0.9 * s) & face, H_, cast=False)
            dot(ex, ey, H_[0], face)
            dot(ex - 1.0, ey, H_[0], face)
            dot(ex + 1.0, ey, pal["tape"][3], face)
        # Рот углами вниз.
        dot(4.6, 5.0, sk[0], face)
        dot(5.6, 4.6, sk[0], face)
        dot(6.6, 5.0, sk[0], face)
        dot(3.8, 5.8, sk[0], face)
        if hurt:
            dot(5.6, 5.6, sk[0], face)
        return
    # Сёгун. Назатыльник шлема за шеей, пластинами.
    A, G, M, B_ = pal["armor"], pal["gold"], pal["mask"], pal["bone"]
    guard = poly([H(-10.2, -4.5), H(-14.0, 7.5), H(-3.0, 9.5), H(1.0, -3.0)])
    put(c, pal, guard, A, soft=True)
    _rows(c, guard, H(0, 0), (-sa, ca), 4, G[2], alt=G[1])
    # Дальний рог за шлемом.
    put(c, pal, poly([H(-1.5, -9.0), H(-6.6, -13.5), H(-9.0, -18.0), H(-3.6, -15.0), H(1.6, -10.5)]), G, far=True,
        cast=False)
    # Маска демона: красное лицо, нос крюком, тяжёлая челюсть.
    skull = ellipse(*H(0.5, -1.0), 7.3 * s, 6.6 * s, ang)
    jaw = poly([H(-3.0, 1.5), H(6.6, 0.8), H(7.2, 5.4), H(3.2, 9.2), H(-2.6, 7.6)])
    nose = poly([H(6.4, -2.2), H(10.4, 1.8), H(6.6, 3.0)])
    face = skull | jaw | nose
    put(c, pal, face, M, soft=True)
    # Складки маски у скулы.
    for dx, dy in ((1.0, 2.0), (2.0, 3.0), (3.0, 3.6), (0.2, 4.6), (1.2, 5.6)):
        dot(dx, dy, M[1], face)
    # Купол шлема с рёбрами и золотой козырёк.
    dome = ellipse(*H(-0.5, -6.0), 9.3 * s, 7.8 * s, ang)
    dome = {q for q in dome if local(*q)[1] < -3.2}
    put(c, pal, dome, A, soft=True, cast=False)
    for q in dome:
        lx, ly = local(*q)
        if abs(((lx + 6.0) % 3.6) - 1.8) < 0.45 / s and c.get(*q) == A[2]:
            c.set(q[0], q[1], A[3] if ly < -8 else A[1])
    put(c, pal, capsule(H(-9.6, -3.6), H(9.4, -3.2), 1.3 * s, 1.3 * s), G, cast=False)
    put(c, pal, poly([H(8.0, -4.6), H(12.4, -2.2), H(8.0, -1.8)]), G, cast=False)
    # Ближний рог кувагата и круглый знак на лбу.
    put(c, pal, poly([H(2.6, -10.5), H(6.6, -14.0), H(7.4, -18.0), H(10.4, -14.0), H(7.4, -9.5)]), G, cast=False)
    put(c, pal, ellipse(*H(4.4, -8.6), 2.4 * s, 2.4 * s), G, cast=False)
    dot(4.4, -8.6, M[2])
    # Глаз: тёмная глазница, жёлтый огонь; при ударе гаснет.
    E = pal["eye"]
    eye = ellipse(*H(4.2, -0.6), 2.9 * s, 1.9 * s, ang + 18) & face
    recolor(c, eye, lambda x, y, e: E[0])
    if hurt:
        dot(3.6, -0.6, M[0], eye)
        dot(4.8, -0.4, M[0], eye)
    else:
        dot(4.0, -0.8, E[2], eye)
        dot(5.0, -0.6, E[3], eye)
        dot(5.0, 0.2, E[2], eye)
    dot(2.6, -2.6, M[0], face)
    dot(3.8, -2.6, M[0], face)
    dot(5.0, -2.2, M[0], face)
    # Оскал: тёмная щель рта, два клыка, белые усы торчат вперёд и вниз.
    for k in range(5):
        dot(3.0 + k, 5.4 - (0.4 if k > 2 else 0.0), M[0], face)
    dot(4.0, 6.4, B_[3], face)
    dot(6.0, 6.0, B_[3], face)
    dot(4.0, 4.4, B_[2], face)
    if hurt:
        dot(5.0, 6.4, M[0], face)
    put(c, pal, capsule(H(6.4, 3.8), H(11.0, 6.6 + wv * 0.3), 1.2 * s, 0.6), B_, cast=False)


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    _back(c, look, j, p)
    if kind == "shogun":
        _tails(c, look, j, p, True)
    _torso(c, look, j, p)
    if kind == "chain":
        _tails(c, look, j, p, False)
    _leg(c, look, j, "n", False, p)
    if kind == "sumo":
        _front(c, look, j, p)
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
        # Руки опущены, чтобы кулак и оружие не попадали в рамку портрета.
        f = fighter(dict(frame, ua_n=0.0, fa_n=8.0, ua_f=0.0, fa_f=8.0), look, w, h)
        hx, hy = int(round(f.head[0])), int(round(f.head[1]))
        c = Canvas(32, 32)
        for y in range(32):
            for x in range(32):
                sx, sy = hx - 15 + x, hy - up + y
                if 0 <= sx < w and 0 <= sy < h:
                    c.px[y][x] = f.px[sy][sx]
        out["brawl_face_" + key] = (c, look.pal.colors)
    return out


# --- Улица старого городка ----------------------------------------------------------------------

def street_pal():
    p = Pal(0x0E0C14)
    p.add("wood", [0x1E130E, 0x38241A, 0x563826, 0x7C5634])
    p.add("beam", [0x2A1512, 0x4A241C, 0x6E3628, 0x985238])
    p.add("plaster", [0x7A6C60, 0xA89A88, 0xD4C8B0, 0xF0E8D4])
    p.add("paper", [0xA8642E, 0xDE9A48, 0xF8D488, 0xFFF4D0])
    p.add("tile", [0x14162A, 0x242842, 0x3A4060, 0x5C6488])
    p.add("stone", [0x2A2A36, 0x464654, 0x686876, 0x8E8E9A])
    p.add("red", [0x5A1014, 0x961E20, 0xD93632, 0xF8765A])
    p.add("gold", [0x6E4A14, 0xB2762E, 0xF4CB52, 0xFFF0A8])
    p.add("moss", [0x14301E, 0x275640, 0x4A8046, 0x6FA94B])
    p.add("straw", [0x5A4420, 0x8E7036, 0xC4A458, 0xE8D090])
    p.add("ink", [0x0A0810, 0x16141E, 0x26222E, 0x3E3A4A])
    p.add("sky", [0x522A60, 0x9A3E5C, 0xE97B52, 0xFBDC92])
    p.add("slab", [0x2C2A34, 0x45424E, 0x625E6A, 0x847E88])
    p.add("deck", [0x2C1C14, 0x4A3020, 0x6E4C2E, 0x967040])
    p.add("indigo", [0x141638, 0x222A66, 0x38469C, 0x6276C8])
    p.add("white", [0x787A8A, 0xB7B4B2, 0xF3EEE2, 0xFFFFFF])
    return p


_BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


class Lane(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(137)
        self.lighter = {}
        for idx in self.p.ramp.values():
            for i in range(3):
                self.lighter[idx[i]] = idx[i + 1]

    def glow(self, cx, cy, rx, ry, skip=()):
        """Пятно света: пиксели внутри эллипса светлеют на тон, к краю через один."""
        skip = set(sum((self.R(n) for n in ("sky",) + tuple(skip)), []))
        for (x, y) in ellipse(cx, cy, rx, ry):
            e = self.c.get(x, y)
            if e is None or e in skip:
                continue
            k = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if k < 0.45 or (x + y) % 2 == 0:
                self.c.set(x, y, self.lighter.get(e, e))

    def sky(self, x0, y0, x1, y1, horizon=150):
        """Закат: сверху сумеречный пурпур (тон `street_top` сеттинга), ниже роза, коралл и
        золото у горизонта, переходы упорядоченным дизерингом, полосы облаков."""
        S = self.R("sky")
        for y in range(y0, y1 + 1):
            k = max(0.0, min(2.999, y / float(horizon) * 3.0))
            i, f = int(k), k - int(k)
            for x in range(x0, x1 + 1):
                self.c.set(x, y, S[i + 1] if f * 16 > _BAYER[y % 4][x % 4] + 0.5 else S[i])
        r = self.rng
        for _ in range(max(2, (x1 - x0) // 40)):
            cx, cy = r.randint(x0, x1), r.randint(y0 + 6, max(y0 + 7, min(y1, horizon) - 10))
            ln = r.randint(14, 40)
            k = max(0, min(2, int(cy / float(horizon) * 3.0)))
            for dy in range(3):
                for x in range(cx - ln // 2 + dy * 3, cx + ln // 2 - dy * 2):
                    if x0 <= x <= x1 and y0 <= cy + dy <= y1:
                        self.c.set(x, cy + dy, S[min(k + 1, 3)] if dy < 2 or x % 2 else S[k])

    def planks(self, x0, y0, x1, y1, pw=11, ramp="wood"):
        """Стена из вертикальных досок: шов, блик кромки, волокна, редкие сучки."""
        W = self.R(ramp)
        r = self.rng
        self.rect(x0, y0, x1, y1, W[2])
        for x in range(x0, x1 + 1, pw):
            self.rect(x, y0, x, y1, W[0])
            if x + 1 <= x1:
                self.rect(x + 1, y0, x + 1, y1, W[3])
            for _ in range(max(1, (y1 - y0) // 14)):
                gx = r.randint(x + 3, x + pw - 2)
                gy = r.randint(y0, y1)
                if gx <= x1:
                    self.rect(gx, gy, gx, min(gy + r.randint(5, 16), y1), W[1])
            if r.random() < 0.3 and x + 6 <= x1 and y1 - y0 > 20:
                ky = r.randint(y0 + 4, y1 - 6)
                self.rect(x + 4, ky, x + 6, ky + 2, W[1])
                self.c.set(x + 5, ky + 1, W[0])

    def post(self, x, y0, y1, w=7, ramp="beam"):
        """Столб: тёмное дерево, блик слева, тень справа на стене."""
        W = self.R(ramp)
        self.rect(x, y0, x + w - 1, y1, W[2])
        self.rect(x, y0, x, y1, W[3])
        self.rect(x + w - 1, y0, x + w - 1, y1, W[0])
        self.rect(x + w - 2, y0, x + w - 2, y1, W[1])
        for y in range(y0 + 7, y1, 23):
            self.rect(x + 2, y, x + 2, min(y + 9, y1), W[1])
        self.dark(x + w, y0, x + w + 1, y1, 1)

    def hbeam(self, x0, x1, y, h=6, ramp="beam"):
        W = self.R(ramp)
        self.rect(x0, y, x1, y + h - 1, W[2])
        self.rect(x0, y, x1, y, W[3])
        self.rect(x0, y + h - 1, x1, y + h - 1, W[0])
        self.dark(x0, y + h, x1, y + h + 1, 1)

    def roof(self, x0, x1):
        """Край черепичной крыши над стеной: ряды черепицы, круглые торцы, балка карниза с
        побелёнными торцами стропил и тень под ней."""
        T, W, Pl = self.R("tile"), self.R("beam"), self.R("plaster")
        self.rect(x0, 0, x1, 19, T[1])
        for x in range(x0, x1 + 1):
            k = x % 10
            for y in range(0, 15):
                col = T[3] if k == 2 else T[2] if k in (1, 3, 4) else T[0] if k in (8, 9) else T[1]
                if y % 7 == 6:
                    col = T[0] if k not in (2, 3) else T[1]
                self.c.set(x, y, col)
        for x in range(x0 - (x0 % 10), x1 + 1, 10):
            for (px, py) in ellipse(x + 3, 16, 3.6, 3.2):
                if x0 <= px <= x1:
                    self.c.set(px, py, T[2])
            for (px, py) in ((x + 2, 15), (x + 3, 14), (x + 2, 14)):
                if x0 <= px <= x1:
                    self.c.set(px, py, T[3])
            if x0 <= x + 3 <= x1:
                self.c.set(x + 3, 16, T[0])
                self.c.set(x + 4, 17, T[0])
            for px in (x + 7, x + 8):
                if x0 <= px <= x1:
                    self.rect(px, 13, px, 19, T[0])
        self.rect(x0, 20, x1, 31, W[2])
        self.rect(x0, 20, x1, 20, W[0])
        self.rect(x0, 21, x1, 21, W[3])
        self.rect(x0, 31, x1, 31, W[0])
        for x in range(x0 + 5, x1 - 5, 16):
            self.rect(x, 23, x + 5, 29, W[1])
            self.rect(x + 1, 24, x + 4, 28, Pl[2])
            self.rect(x + 1, 24, x + 4, 24, Pl[3])
            self.rect(x + 4, 25, x + 4, 28, Pl[1])
        self.dark(x0, 32, x1, 36, 1)
        self.dark(x0, 37, x1, 40, 1, dither=True)

    def shoji(self, x0, y0, x1, y1, cw=12, ch=15, lit=True):
        """Бумажная ширма: тёплый свет изнутри (ярче к середине), решётка из реек, рама."""
        Pp, W = self.R("paper"), self.R("beam")
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                k = ((x - cx) / max(1.0, (x1 - x0) * 0.5)) ** 2 + ((y - cy) / max(1.0, (y1 - y0) * 0.55)) ** 2
                k += (y - cy) / float(max(1, y1 - y0)) * 0.3
                d = _BAYER[y % 4][x % 4] / 16.0
                t = 3 if k < 0.06 + d * 0.22 else 2 if k < 0.6 + d * 0.4 else 1
                if not lit:
                    t = max(t - 1, 0) if t < 3 else 1
                self.c.set(x, y, Pp[t] if lit else self.R("plaster")[t + 1 if t < 3 else 3])
        for x in range(x0 + cw, x1 - 2, cw):
            self.rect(x, y0, x, y1, W[1])
        for y in range(y0 + ch, y1 - 2, ch):
            self.rect(x0, y, x1, y, W[1])
        self.rect(x0 - 2, y0 - 2, x1 + 2, y0 - 1, W[3])
        self.rect(x0 - 2, y1 + 1, x1 + 2, y1 + 2, W[1])
        self.rect(x0 - 2, y0 - 2, x0 - 1, y1 + 2, W[2])
        self.rect(x1 + 1, y0 - 2, x1 + 2, y1 + 2, W[1])
        self.dark(x0, y0, x1, y0 + 1, 1)

    def lattice(self, x0, y0, x1, y1):
        """Окно додзё: частые вертикальные рейки, за ними тёплый свет."""
        Pp, W = self.R("paper"), self.R("beam")
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                k = abs(y - (y0 + y1) / 2.0) / float(y1 - y0)
                self.c.set(x, y, Pp[2] if k < 0.2 else Pp[1] if k < 0.4 or (x + y) % 2 else Pp[0])
        for x in range(x0, x1 + 1, 5):
            self.rect(x, y0, x + 1, y1, W[2])
            self.rect(x, y0, x, y1, W[3])
            self.rect(x + 2, y0, min(x + 2, x1), y1, W[0])
        for y in (y0 + (y1 - y0) // 3, y0 + 2 * (y1 - y0) // 3):
            self.rect(x0, y, x1, y + 1, W[1])
        self.bevel(x0 - 3, y0 - 4, x1 + 3, y0 - 1, W)
        self.bevel(x0 - 3, y1 + 1, x1 + 3, y1 + 4, W)
        self.dark(x0 - 2, y1 + 5, x1 + 4, y1 + 6, 1)

    def strokes(self, x0, y0, x1, y1, col, n=2):
        """Знаки кистью: столбик из `n` условных иероглифов (черты разной толщины)."""
        r = self.rng
        h = (y1 - y0 + 1) / float(n)
        for k in range(n):
            a, b = int(y0 + k * h) + 1, int(y0 + (k + 1) * h) - 2
            mx = (x0 + x1) // 2
            kind = r.randint(0, 3)
            self.rect(x0 + 1, a + (b - a) // 3, x1 - 1, a + (b - a) // 3, col)
            self.rect(mx, a, mx, b, col)
            if kind in (0, 2):
                self.rect(x0 + 1, b, x1 - 1, b, col)
            if kind in (1, 2):
                for t in range(0, (b - a) // 2 + 1):
                    self.c.set(mx - t, a + (b - a) // 2 + t, col)
                    self.c.set(mx + t, a + (b - a) // 2 + t, col)
            if kind == 3:
                self.rect(x0 + 1, a, x0 + 1, b, col)
                self.rect(x1 - 1, a, x1 - 1, b, col)
                self.rect(x0 + 1, a, x1 - 1, a, col)

    def signboard(self, x, y, w, h, n=3):
        """Вывеска: светлая доска в тёмной раме, знаки тушью."""
        W, Pl, I = self.R("beam"), self.R("plaster"), self.R("ink")
        self.rect(x + 2, y + 2, x + w + 2, y + h + 2, self.R("wood")[0])
        self.bevel(x, y, x + w, y + h, W)
        self.rect(x + 2, y + 2, x + w - 2, y + h - 2, Pl[2])
        self.rect(x + 2, y + 2, x + w - 2, y + 2, Pl[3])
        self.rect(x + w - 2, y + 3, x + w - 2, y + h - 2, Pl[1])
        if w > h:
            cw = (w - 6) // n
            for k in range(n):
                self.strokes(x + 4 + k * cw, y + 4, x + 2 + (k + 1) * cw - 1, y + h - 4, I[1], 1)
        else:
            self.strokes(x + 4, y + 4, x + w - 4, y + h - 4, I[1], n)

    def noren(self, x0, y, x1, h, ramp="indigo", parts=3, mark="ring"):
        """Занавесь норэн над входом: перекладина, полотнища с разрезами, белый знак."""
        C_, Wh, W = self.R(ramp), self.R("white"), self.R("straw")
        pw = (x1 - x0 + 1) / float(parts)
        for k in range(parts):
            a, b = int(x0 + k * pw) + (1 if k else 0), int(x0 + (k + 1) * pw) - 1
            for x in range(a, b + 1):
                bot = y + h + int(round(math.sin((x - a) * 0.5 + k * 1.7) * 1.4)) - (2 if k % 2 else 0)
                for yy in range(y + 2, bot + 1):
                    u = (x - a) / float(max(1, b - a))
                    t = 3 if u < 0.08 else 2 if u < 0.62 else 1 if u < 0.92 else 0
                    if yy >= bot - 1:
                        t = max(t - 1, 0)
                    self.c.set(x, yy, C_[t])
            mx, my = (a + b) // 2, y + h // 2 + 1
            if mark == "ring":
                for (px, py) in ellipse(mx, my, 5.2, 5.2) - ellipse(mx, my, 3.0, 3.0):
                    if a <= px <= b:
                        self.c.set(px, py, Wh[2])
            else:
                self.strokes(mx - 4, my - 6, mx + 4, my + 6, Wh[2], 1)
        self.rect(x0 - 4, y, x1 + 4, y + 2, W[2])
        self.rect(x0 - 4, y, x1 + 4, y, W[3])
        self.rect(x0 - 4, y + 2, x1 + 4, y + 2, W[0])
        self.dark(x0, y + 3, x1, y + 4, 1)

    def chochin(self, cx, cy, rx=9, ry=13, ramp="red", mark=True):
        """Бумажный фонарь: рёбра, чёрные обручи сверху и снизу, знак тушью, кисть, свет вокруг."""
        R_, I, G = self.R(ramp), self.R("ink"), self.R("gold")
        self.glow(cx, cy + 4, rx * 3.2, ry * 2.6)
        self.rect(cx, cy - ry - 9, cx, cy - ry - 2, I[1])
        body = ellipse(cx, cy, rx, ry)
        for (x, y) in body:
            u = (x - cx) / float(rx)
            t = 3 if -0.55 < u < -0.1 and abs(y - cy) < ry * 0.7 else 2 if u < 0.45 else 1
            if (y - cy) % 4 == 0:
                t = max(t - 1, 0)
            self.c.set(x, y, R_[t])
        if mark:
            self.rect(cx - 2, cy - 4, cx + 2, cy - 4, I[0])
            self.rect(cx, cy - 6, cx, cy + 5, I[0])
            self.rect(cx - 3, cy + 1, cx + 3, cy + 1, I[0])
        for yy, col in ((cy - ry - 1, I[2]), (cy - ry, I[1]), (cy + ry, I[1]), (cy + ry + 1, I[0])):
            self.rect(cx - rx // 2 - 1, yy, cx + rx // 2 + 1, yy, col)
        self.rect(cx, cy + ry + 2, cx, cy + ry + 7, G[2])
        self.rect(cx - 1, cy + ry + 5, cx + 1, cy + ry + 8, R_[2])

    def toro(self, x, yb, h=74):
        """Каменный фонарь: основание, столб, камера с огнём, шляпа с загнутыми краями, навершие."""
        S_, G, M = self.R("stone"), self.R("gold"), self.R("moss")
        top = yb - h
        self.glow(x, top + 26, 34, 30)
        self.put(poly([(x - 13, yb), (x - 10, yb - 7), (x + 10, yb - 7), (x + 13, yb)]), S_, soft=True)
        self.put(set((xx, yy) for xx in range(x - 5, x + 6) for yy in range(top + 40, yb - 6)), S_, soft=True)
        self.put(poly([(x - 11, top + 40), (x - 8, top + 34), (x + 8, top + 34), (x + 11, top + 40)]), S_, soft=True)
        self.put(set((xx, yy) for xx in range(x - 8, x + 9) for yy in range(top + 19, top + 35)), S_, soft=False)
        self.rect(x - 4, top + 22, x + 4, top + 31, G[2])
        self.rect(x - 4, top + 22, x + 4, top + 23, G[3])
        self.rect(x - 4, top + 30, x + 4, top + 31, G[1])
        self.rect(x, top + 22, x, top + 31, S_[1])
        self.rect(x - 4, top + 26, x + 4, top + 26, S_[1])
        self.put(poly([(x - 19, top + 19), (x - 15, top + 13), (x - 5, top + 8), (x + 5, top + 8), (x + 15, top + 13),
                       (x + 19, top + 19)]), S_, soft=True)
        self.c.set(x - 19, top + 17, S_[2])
        self.c.set(x + 19, top + 17, S_[1])
        self.put(ellipse(x, top + 4, 3.4, 4.2), S_, soft=True)
        for (dx, dy) in ((-9, -4), (-8, -5), (-7, -5), (8, -3), (-3, -8), (-2, -8), (4, -46), (5, -46), (-14, 0), (-13, -1)):
            self.c.set(x + dx, yb + dy, M[2 if (dx + dy) % 2 else 3])
        self.dark(x + 13, yb - 5, x + 18, yb, 1, dither=True)

    def maple(self, cx, cy, r, clip=None):
        """Крона клёна: красные облака листвы тремя тонами, светлые листья сверху слева."""
        R_ = self.R("red")
        rg = self.rng
        blobs = [(cx, cy, r)]
        for _ in range(6):
            a = rg.random() * math.tau
            blobs.append((cx + math.cos(a) * r * 0.7, cy + math.sin(a) * r * 0.45, r * rg.uniform(0.4, 0.65)))
        S = set()
        for (bx, by, br) in blobs:
            S |= ellipse(bx, by, br, br * 0.72)
        if clip is not None:
            S = {q for q in S if clip(*q)}
        for (x, y) in S:
            lit = (x - 3, y - 3) not in S or (x - 5, y - 2) not in S
            shade = (x + 2, y + 3) not in S or (x + 4, y + 2) not in S
            v = rg.random()
            t = 3 if lit and v < 0.7 else 0 if shade and v < 0.75 else 1 if v < 0.3 else 2 if v < 0.9 else 3
            self.c.set(x, y, R_[t])
        # Зубчатый край: отдельные листья вокруг.
        for _ in range(int(r * 1.6)):
            a = rg.random() * math.tau
            x, y = int(cx + math.cos(a) * r * 1.25), int(cy + math.sin(a) * r * 0.85)
            if clip is None or clip(x, y):
                self.c.set(x, y, R_[2])
                self.c.set(x + 1, y, R_[1])

    def bamboo(self, x, y0, yb, w=4, leaves=True):
        """Стебель бамбука: колена, блик, пучки узких листьев."""
        M = self.R("moss")
        self.rect(x, y0, x + w - 1, yb, M[2])
        self.rect(x, y0, x, yb, M[3])
        self.rect(x + w - 1, y0, x + w - 1, yb, M[1])
        for y in range(yb - 9, y0, -19):
            self.rect(x - 1, y, x + w, y, M[0])
            self.rect(x, y - 1, x + w - 1, y - 1, M[3])
            if leaves and self.rng.random() < 0.7:
                side = self.rng.choice((-1, 1))
                for k in range(3):
                    ln = self.rng.randint(7, 13)
                    for t in range(ln):
                        px = x + (w if side > 0 else -1) + side * t
                        py = y - 2 + int(t * (0.25 + k * 0.4)) - k
                        self.c.set(px, py, M[3 if t < ln // 2 else 2])
                        if 1 < t < ln - 2:
                            self.c.set(px, py + 1, M[1])

    def namako(self, x0, y0, x1, y1):
        """Низ садовой стены: тёмная плитка, белые швы ромбами."""
        T, Wh = self.R("tile"), self.R("white")
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                a, b = (x + y) % 20, (x - y) % 20
                seam = a < 2 or b < 2
                edge = a == 2 or b == 2
                self.c.set(x, y, Wh[2 if a == 0 or b == 0 else 1] if seam else T[0] if edge else
                           T[3] if a == 19 or b == 19 else T[2])
        self.rect(x0, y0, x1, y0, self.R("beam")[1])

    def gate_door(self, x0, y0, x1, y1):
        """Створка ворот: толстые доски, полосы железа с заклёпками, золотой герб клана."""
        W, I, G = self.R("wood"), self.R("ink"), self.R("gold")
        self.planks(x0, y0, x1, y1, 13, "wood")
        for y in (y0 + 14, (y0 + y1) // 2 + 30, y1 - 16):
            self.rect(x0, y, x1, y + 6, I[2])
            self.rect(x0, y, x1, y, I[3])
            self.rect(x0, y + 6, x1, y + 6, I[0])
            for x in range(x0 + 5, x1 - 2, 10):
                self.c.set(x, y + 3, G[2])
                self.c.set(x + 1, y + 3, G[1])
                self.c.set(x, y + 2, G[3])
        cx, cy = (x0 + x1) // 2, y0 + 62
        ring = ellipse(cx, cy, 15, 15)
        for (x, y) in ring:
            d = math.hypot(x - cx, y - cy)
            if d > 12.2:
                self.c.set(x, y, G[3] if x + y < cx + cy - 6 else G[2] if x + y < cx + cy + 8 else G[1])
            else:
                self.c.set(x, y, I[1])
        # Герб: три запятые томоэ, упрощённо тремя каплями по кругу.
        for k in range(3):
            a = k * math.tau / 3 - 0.5
            bx, by = cx + math.cos(a) * 5.4, cy + math.sin(a) * 5.4
            for (x, y) in ellipse(bx, by, 3.6, 3.6) | capsule((bx, by), (cx + math.cos(a + 1.5) * 9.5,
                                                                           cy + math.sin(a + 1.5) * 9.5), 2.2, 0.6):
                if math.hypot(x - cx, y - cy) <= 11.6:
                    self.c.set(x, y, G[2] if (x - bx) + (y - by) < 1 else G[1])
        self.dark(x0, y0, x1, y0 + 5, 1)
        self.dark(x0, y0 + 6, x1, y0 + 9, 1, dither=True)

    def nobori(self, x, y0, yb, w=22):
        """Знамя нобори: шест, перекладина, узкое белое полотнище с красным солнцем и знаками."""
        Wh, R_, W, I = self.R("white"), self.R("red"), self.R("straw"), self.R("ink")
        self.rect(x, y0 - 6, x + 2, yb, W[2])
        self.rect(x, y0 - 6, x, yb, W[3])
        self.rect(x + 2, y0 - 6, x + 2, yb, W[0])
        self.rect(x, y0, x + w + 5, y0 + 1, W[2])
        h = yb - y0 - 46
        for yy in range(y0 + 3, y0 + h):
            wob = int(round(math.sin(yy * 0.11) * 1.5))
            for xx in range(x + 5, x + 5 + w):
                u = (xx - x - 5) / float(w)
                t = 3 if u < 0.2 else 2 if u < 0.7 else 1
                if (yy + wob * 3) % 31 > 27:
                    t = max(t - 1, 0)
                self.c.set(xx + wob, yy, Wh[t])
        cx, cy = x + 5 + w // 2, y0 + 20
        for (px, py) in ellipse(cx, cy, 7, 7):
            self.c.set(px, py, R_[3] if px + py < cx + cy - 4 else R_[2] if px + py < cx + cy + 5 else R_[1])
        self.strokes(cx - 5, y0 + 36, cx + 5, y0 + h - 8, I[1], 3)
        self.rect(x + 5, y0 + h, x + 5 + w, y0 + h + 1, R_[2])
        for yy in range(y0 + 10, y0 + h, 22):
            self.rect(x + 3, yy, x + 5, yy + 1, R_[2])
        self.dark(x + 3, y0 + 2, x + 4, yb, 1)

    def sugidama(self, cx, cy, r=13):
        """Шар из кедровых веток под карнизом лавки сакэ."""
        M, W = self.R("moss"), self.R("straw")
        self.rect(cx, cy - r - 8, cx, cy - r, W[1])
        for (x, y) in ellipse(cx, cy, r, r):
            d = (x - cx) + (y - cy)
            v = self.rng.random()
            t = 3 if d < -r * 0.7 and v < 0.6 else 2 if d < 0 else 1 if d < r * 0.8 or v < 0.4 else 0
            if v > 0.9:
                t = max(t - 1, 0)
            self.c.set(x, y, M[t])
        self.dark(cx - r + 3, cy + r + 1, cx + r + 2, cy + r + 2, 1)

    def rack(self, x, yb, h=92):
        """Стойка у стены додзё: два шеста, копьё яри с красной кистью, деревянный меч."""
        W, S_, M_, R_ = self.R("straw"), self.R("beam"), self.R("white"), self.R("red")
        self.bevel(x - 2, yb - 16, x + 44, yb - 12, S_)
        self.bevel(x - 2, yb - 58, x + 44, yb - 54, S_)
        for k, (dx, top) in enumerate(((4, h), (14, h - 8), (26, h + 14), (37, h - 30))):
            x0, x1 = x + dx, x + dx + (3 if k % 2 else -2)
            for yy in range(yb - top, yb + 1):
                px = int(round(x1 + (x0 - x1) * (yy - (yb - top)) / float(top)))
                self.c.set(px - 1, yy, self.R("wood")[0])
                self.c.set(px, yy, W[3])
                self.c.set(px + 1, yy, W[2])
                self.c.set(px + 2, yy, W[1])
                self.c.set(px + 3, yy, self.R("wood")[0])
            tx = x1
            if k == 2:
                for t in range(14):
                    ww = 3 if t > 6 else 2 if t > 3 else 1 if t > 0 else 0
                    for d in range(-ww - 1, ww + 2):
                        self.c.set(tx + 1 + d, yb - top - 14 + t, self.R("ink")[0] if abs(d) > ww else
                                   M_[3 if d < 0 else 2 if d == 0 else 1])
                self.rect(tx - 1, yb - top, tx + 3, yb - top + 4, R_[2])
                self.rect(tx, yb - top + 5, tx + 2, yb - top + 8, R_[1])
            elif k == 3:
                self.rect(tx - 2, yb - top + 16, tx + 4, yb - top + 17, S_[3])

    # Предметы у стены -------------------------------------------------------------------------

    def komodaru(self, x, y, w=22, h=30):
        """Бочка сакэ в соломе: циновка, верёвки накрест, белый круг с красным знаком."""
        St, Wh, R_, I = self.R("straw"), self.R("white"), self.R("red"), self.R("ink")
        S = set((xx, yy) for xx in range(int(x - w / 2), int(x + w / 2) + 1) for yy in range(y - h + 3, y + 1))
        S |= ellipse(x, y - h + 3, w / 2, 3.4)
        self.put(S, St, soft=True)
        for (xx, yy) in S:
            if (xx + yy * 2) % 5 == 0 and self.c.get(xx, yy) == St[2]:
                self.c.set(xx, yy, St[1])
        for hy in (y - h + 8, y - 6):
            for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                self.c.set(xx, hy, St[0])
                self.c.set(xx, hy - 1, St[3])
                if (xx // 2) % 2:
                    self.c.set(xx, hy - 1, St[1])
        r = min(w, h) * 0.3
        for (xx, yy) in ellipse(x, y - h / 2 + 1, r, r):
            self.c.set(xx, yy, Wh[2] if (xx - x) + (yy - y + h / 2) < r * 0.6 else Wh[1])
        cy = int(y - h / 2 + 1)
        self.rect(x - int(r * 0.5), cy - 1, x + int(r * 0.5), cy - 1, R_[2])
        self.rect(x, cy - int(r * 0.6), x, cy + int(r * 0.6), R_[2])
        self.c.set(x - 1, cy + 2, I[1])
        self.c.set(x + 2, cy + 2, I[1])
        top = ellipse(x, y - h + 3, w / 2 - 2, 2.2)
        for (xx, yy) in top:
            self.c.set(xx, yy, St[3] if xx < x else St[2])

    def bucket(self, x, y, w=14, h=20):
        """Деревянная кадка: клёпки, два бамбуковых обруча, дужка."""
        W, M = self.R("deck"), self.R("moss")
        S = poly([(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2 - 2, y), (x - w / 2 + 2, y)])
        self.put(S, W, soft=True)
        for xx in range(int(x - w / 2) + 3, int(x + w / 2), 4):
            self.rect(xx, y - h + 1, xx, y - 1, W[1])
        for hy in (y - h + 5, y - 5):
            for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                if (xx, hy) in S:
                    self.c.set(xx, hy, M[2 if xx < x + 2 else 1])
                    self.c.set(xx, hy - 1, M[3 if xx < x else 2])
        handle = ellipse(x, y - h, w / 2 - 1, 7) - ellipse(x, y - h + 1, w / 2 - 2.6, 6)
        for (xx, yy) in handle:
            if yy < y - h:
                self.c.set(xx, yy, W[3] if xx < x else W[1])

    def basket(self, x, y, w=30, h=24):
        """Бамбуковая корзина-клетка: плетение ромбами, обруч сверху и снизу."""
        St, W = self.R("straw"), self.R("wood")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h, y + 1))
        self.put(S, St, soft=False)
        for yy in range(y - h + 3, y - 2):
            for xx in range(x + 1, x + w):
                a, b = (xx + yy) % 6, (xx - yy) % 6
                if a == 0 or b == 0:
                    self.c.set(xx, yy, St[3] if a == 0 else St[2])
                elif a == 1 or b == 1:
                    self.c.set(xx, yy, St[1])
                else:
                    self.c.set(xx, yy, W[0] if (a + b) % 2 else W[1])
        self.rect(x, y - h, x + w, y - h + 2, St[2])
        self.rect(x, y - h, x + w, y - h, St[3])
        self.rect(x, y - h + 2, x + w, y - h + 2, St[0])
        self.rect(x, y - 2, x + w, y, St[1])
        self.rect(x, y, x + w, y, St[0])
        self.rect(x + w, y - h, x + w, y, St[0])

    def kasa(self, x, y):
        """Соломенная шляпа конусом, прислонена к стене."""
        St = self.R("straw")
        S = poly([(x - 13, y), (x + 1, y - 13), (x + 14, y)]) | ellipse(x, y, 13.5, 2.2)
        self.put(S, St, soft=True)
        for k in range(-10, 12, 4):
            for t in range(11):
                px, py = x + 1 + (k - 1) * t / 11.0, y - 12 + t * 1.1
                if (int(round(px)), int(round(py))) in S:
                    self.c.set(px, py, St[1])
        for k in (4, 8):
            for xx in range(x - 13, x + 15):
                yy = y - 13 + k + abs(xx - x) // 6
                if (xx, yy) in S and abs(xx - x - 1) < k * 1.1:
                    self.c.set(xx, yy, St[0])
        self.c.set(x + 1, y - 13, self.R("red")[2])


# Имя класса улицы как у космоса: кто берёт инструменты по имени, найдёт их.
Deck = Lane


def build_street():
    """Улица старого городка той же ширины и с теми же строками пола, что улица пиратов: стена до
    `WALL_Y`, настил из досок до `CURB_Y`, каменный бордюр со мхом, дорожка из плит от `ROAD_Y`."""
    st = Lane()
    c, rng = st.c, st.rng
    W, Bm, Pl, T, I = st.R("wood"), st.R("beam"), st.R("plaster"), st.R("tile"), st.R("ink")
    G, R_, M, S_ = st.R("gold"), st.R("red"), st.R("moss"), st.R("stone")
    x = 0
    modules = [("tea", 320), ("garden", 288), ("gate", 352), ("dojo", 256), ("sake", 256), ("alley", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        if kind == "tea":
            # Чайный дом: ширмы сёдзи светятся, вход под норэн, красный фонарь, вывеска.
            st.rect(x0, 32, x1, WALL_Y, Pl[2])
            st.noise(x0, 32, x1, 58, Pl, 0.04)
            st.roof(x0, x1)
            st.hbeam(x0, x1, 56, 6)
            st.planks(x0, WALL_Y - 30, x1, WALL_Y, 12)
            st.hbeam(x0, x1, WALL_Y - 34, 5)
            st.shoji(x0 + 18, 70, x0 + 114, WALL_Y - 40)
            st.shoji(x0 + 212, 70, x0 + 300, WALL_Y - 40)
            # Тень чайника и чашки за бумагой.
            Pp = st.R("paper")
            sil = ellipse(x0 + 250, 178, 11, 9) | poly([(x0 + 260, 172), (x0 + 270, 166), (x0 + 271, 169), (x0 + 261, 178)]) \
                | ellipse(x0 + 250, 167, 4, 3) | set((xx, yy) for xx in range(x0 + 226, x0 + 235) for yy in range(180, 188))
            for (px, py) in sil:
                if c.get(px, py) in (Pp[2], Pp[3]):
                    c.set(px, py, Pp[1])
                elif c.get(px, py) == Pp[1]:
                    c.set(px, py, Pp[0])
            # Вход: тёмный проём, в глубине полоса света, порог.
            st.rect(x0 + 130, 64, x0 + 196, WALL_Y, I[1])
            for yy in range(150, WALL_Y):
                for xx in range(x0 + 132, x0 + 195):
                    if (xx + yy) % 2 == 0 and yy > 190 or yy > 214:
                        c.set(xx, yy, W[1])
            st.rect(x0 + 150, 120, x0 + 176, 178, st.R("paper")[0])
            st.rect(x0 + 152, 122, x0 + 174, 176, st.R("paper")[1])
            st.rect(x0 + 163, 120, x0 + 163, 178, I[1])
            st.noren(x0 + 132, 64, x0 + 194, 44)
            st.post(x0 + 122, 32, WALL_Y, 8)
            st.post(x0 + 196, 32, WALL_Y, 8)
            st.post(x0 + 2, 32, WALL_Y, 7)
            st.post(x1 - 8, 32, WALL_Y, 7)
            st.signboard(x0 + 136, 37, 54, 17, 3)
            st.chochin(x0 + 206, 96, 8, 12)
            st.chochin(x0 + 116, 96, 8, 12)
        elif kind == "garden":
            # Садовая стена: над ней закат, клёны и бамбук, в стене круглое окно, у стены фонарь.
            st.sky(x0, 0, x1, 110)
            # Дальний холм с пагодой.
            for xx in range(x0, x1 + 1):
                hy = 78 + int(math.sin((xx - x0) * 0.021 + 1.0) * 9 + math.sin((xx - x0) * 0.07) * 3)
                for yy in range(hy, 100):
                    c.set(xx, yy, st.R("sky")[0] if (xx + yy) % 2 or yy > hy + 6 else st.R("sky")[1])
            px = x0 + 196
            for k, (pw_, py) in enumerate(((17, 66), (14, 54), (11, 42), (8, 31))):
                st.rect(px - pw_ // 2 + 2, py + 3, px + pw_ // 2 - 2, py + 12, T[0])
                for d in range(-pw_, pw_ + 1):
                    c.set(px + d, py + 2 - (1 if abs(d) > pw_ - 2 else 0), T[0])
                    c.set(px + d, py + 3, T[0] if abs(d) < pw_ - 1 else None or st.R("sky")[1])
            st.rect(px, 18, px, 31, T[0])
            st.maple(x0 + 58, 52, 34)
            st.maple(x0 + 262, 44, 28)
            st.maple(x0 + 128, 74, 16)
            # Ствол клёна за стеной.
            for yy in range(60, 96):
                st.rect(x0 + 60 + (yy - 60) // 9, yy, x0 + 63 + (yy - 60) // 9, yy, W[0])
            # Черепичный гребень стены.
            for xx in range(x0, x1 + 1):
                k = xx % 8
                for yy in range(90, 103):
                    c.set(xx, yy, T[3] if k == 1 and yy < 100 else T[2] if k in (0, 2, 3) and yy < 100 else T[0] if k > 5
                          else T[1])
                c.set(xx, 89, T[3] if k < 4 else T[1])
            for xx in range(x0 + 2, x1, 8):
                for (px_, py_) in ellipse(xx + 1, 101, 2.6, 2.4):
                    if x0 <= px_ <= x1:
                        c.set(px_, py_, T[2])
                c.set(xx, 100, T[3])
            st.rect(x0, 104, x1, WALL_Y, Pl[2])
            st.noise(x0, 104, x1, 176, Pl, 0.05)
            st.dark(x0, 104, x1, 107, 1)
            st.dark(x0, 108, x1, 111, 1, dither=True)
            # Потёки под гребнем.
            for _ in range(7):
                sx = rng.randint(x0 + 6, x1 - 6)
                for yy in range(108, 108 + rng.randint(14, 40)):
                    if rng.random() < 0.8:
                        c.set(sx + (yy // 11) % 2, yy, Pl[1])
            st.namako(x0, 178, x1, WALL_Y)
            # Круглое окно: рама, за ней сад в закатном свете, решётка из бамбука, ветка клёна.
            wx, wy, wr = x0 + 150, 140, 27
            st.put(ellipse(wx, wy, wr + 5, wr + 5), Bm, soft=True)
            inner = ellipse(wx, wy, wr, wr)
            Sk = st.R("sky")
            for (px_, py_) in inner:
                k = (py_ - (wy - wr)) / float(2 * wr)
                col = Sk[3] if k < 0.3 else Sk[2] if k < 0.5 or (k < 0.6 and (px_ + py_) % 2) else M[1] if k < 0.8 else M[0]
                c.set(px_, py_, col)
            for (px_, py_) in ellipse(wx + 10, wy - 12, 5, 5) & inner:
                c.set(px_, py_, st.R("white")[3])
            st.maple(wx - 12, wy - 10, 12, clip=lambda a, b: (a, b) in inner)
            for xx in (wx - 14, wx, wx + 14):
                for yy in range(wy - wr, wy + wr + 1):
                    if (xx, yy) in inner:
                        c.set(xx, yy, I[2])
                        c.set(xx + 1, yy, I[0])
            for yy in (wy - 9, wy + 11):
                for xx in range(wx - wr, wx + wr + 1):
                    if (xx, yy) in inner:
                        c.set(xx, yy, I[2])
                        c.set(xx, yy + 1, I[0])
            for (px_, py_) in inner:
                if (px_ - 3, py_ - 3) not in inner:
                    c.set(px_, py_, I[0])
            for xx in (x0 + 226, x0 + 238, x0 + 251, x0 + 262):
                st.bamboo(xx, 62 + (xx * 7) % 23, WALL_Y, 4 + (xx % 2))
            st.toro(x0 + 66, WALL_Y)
        elif kind == "gate":
            # Ворота усадьбы: красные столбы, тяжёлые створки с гербом, знамя нобори, доска указов.
            st.rect(x0, 32, x1, WALL_Y, Pl[2])
            st.noise(x0, 32, x1, WALL_Y, Pl, 0.04)
            st.roof(x0, x1)
            st.planks(x0, WALL_Y - 44, x1, WALL_Y, 12)
            st.hbeam(x0, x1, WALL_Y - 48, 5)
            gx0, gx1 = x0 + 70, x0 + 250
            mid = (gx0 + gx1) // 2
            st.rect(gx0, 60, gx1, WALL_Y, I[0])
            st.gate_door(gx0, 62, mid - 2, WALL_Y)
            st.gate_door(mid + 2, 62, gx1, WALL_Y)
            st.rect(mid - 1, 62, mid + 1, WALL_Y, I[0])
            # Засов и кольца.
            for hx in (mid - 12, mid + 12):
                ring = ellipse(hx, 150, 5, 6) - ellipse(hx, 150, 3, 4)
                for (px_, py_) in ring:
                    c.set(px_, py_, G[3] if px_ + py_ < hx + 148 else G[1])
                c.set(hx, 143, G[2])
            # Красные столбы и перекладины ворот с золотыми оковками.
            for px_ in (gx0 - 14, gx1 + 2):
                st.post(px_, 32, WALL_Y, 13, "red")
                st.rect(px_, WALL_Y - 12, px_ + 12, WALL_Y, I[2])
                st.rect(px_, WALL_Y - 12, px_ + 12, WALL_Y - 12, I[3])
                st.rect(px_, 60, px_ + 12, 63, G[2])
                st.rect(px_, 60, px_ + 12, 60, G[3])
            st.hbeam(gx0 - 22, gx1 + 22, 40, 10, "red")
            st.hbeam(gx0 - 14, gx1 + 14, 54, 7, "red")
            for xx in (gx0 - 22, gx1 + 18):
                st.rect(xx, 40, xx + 4, 49, G[2])
                st.rect(xx, 40, xx + 4, 40, G[3])
            st.signboard(mid - 20, 36, 40, 17, 2)
            st.nobori(x0 + 18, 50, WALL_Y, 22)
            # Доска указов под своим навесом.
            bx0, bx1 = x0 + 274, x1 - 16
            st.post(bx0 + 4, 96, WALL_Y, 5)
            st.post(bx1 - 9, 96, WALL_Y, 5)
            st.put(poly([(bx0 - 6, 92), ((bx0 + bx1) // 2, 78), (bx1 + 6, 92), (bx1 + 6, 96), (bx0 - 6, 96)]), T, soft=True)
            st.bevel(bx0, 100, bx1, 158, W)
            st.rect(bx0 + 3, 103, bx1 - 3, 155, Pl[3])
            for k in range(5):
                st.strokes(bx1 - 15 - k * 10, 106, bx1 - 7 - k * 10, 152 - (k * 7) % 16, I[1], 3)
            st.chochin(x0 + 262, 70, 6, 9, "paper", mark=False)
        elif kind == "dojo":
            # Додзё: дощатая стена, окно с частой решёткой, раздвижная дверь, стойка с оружием.
            st.planks(x0, 32, x1, WALL_Y, 13)
            st.roof(x0, x1)
            st.hbeam(x0, x1, 58, 6)
            st.lattice(x0 + 24, 84, x0 + 102, 170)
            st.hbeam(x0, x1, WALL_Y - 34, 5)
            dx0, dx1 = x0 + 122, x0 + 170
            st.rect(dx0 - 4, 76, dx1 + 4, WALL_Y, Bm[1])
            st.shoji(dx0, 82, dx1, 168, 12, 14)
            st.planks(dx0, 172, dx1, WALL_Y, 8, "beam")
            st.rect((dx0 + dx1) // 2, 80, (dx0 + dx1) // 2 + 1, WALL_Y, Bm[0])
            st.c.set((dx0 + dx1) // 2 - 4, 150, I[0])
            st.rect((dx0 + dx1) // 2 + 4, 146, (dx0 + dx1) // 2 + 5, 154, I[1])
            st.signboard(dx0 + 4, 38, dx1 - dx0 - 8, 17, 3)
            # Вертикальная вывеска школы и мишень из соломы.
            st.signboard(x0 + 108, 84, 11, 62, 3)
            st.rack(x0 + 190, WALL_Y)
            st.post(x0 + 2, 32, WALL_Y, 7)
            st.post(x1 - 9, 32, WALL_Y, 7)
            st.chochin(x0 + 180, 82, 6, 9, "paper", mark=False)
        elif kind == "sake":
            # Лавка сакэ: пирамида бочек в соломе на полке, шар из кедра, вход под красным норэн.
            st.rect(x0, 32, x1, WALL_Y, Pl[2])
            st.noise(x0, 32, x1, WALL_Y, Pl, 0.04)
            st.roof(x0, x1)
            st.hbeam(x0, x1, 56, 6)
            st.planks(x0, WALL_Y - 44, x1, WALL_Y, 12)
            # Ниша с бочками.
            st.rect(x0 + 18, 70, x0 + 168, 190, W[0])
            st.rect(x0 + 20, 72, x0 + 166, 188, W[1])
            st.dark(x0 + 20, 72, x0 + 166, 84, 1)
            for row, (n, by) in enumerate(((5, 188), (4, 152), (3, 116))):
                for k in range(n):
                    st.komodaru(x0 + 36 + row * 14 + k * 28, by - 1, 25, 34)
            st.bevel(x0 + 14, 189, x0 + 172, 195, Bm)
            st.bevel(x0 + 14, 64, x0 + 172, 70, Bm)
            st.post(x0 + 12, 64, WALL_Y, 6)
            st.post(x0 + 168, 64, WALL_Y, 6)
            # Вход.
            st.rect(x0 + 186, 66, x0 + 236, WALL_Y, I[1])
            for yy in range(170, WALL_Y):
                for xx in range(x0 + 187, x0 + 236):
                    if (xx + yy) % 2 == 0 or yy > 216:
                        c.set(xx, yy, W[1])
            st.noren(x0 + 187, 66, x0 + 235, 40, "red", 2, mark="sign")
            st.post(x0 + 178, 32, WALL_Y, 8)
            st.post(x0 + 236, 32, WALL_Y, 8)
            st.sugidama(x0 + 210, 50, 9)
            st.signboard(x0 + 60, 36, 66, 18, 4)
            st.post(x1 - 8, 32, WALL_Y, 7)
            st.chochin(x0 + 26, 54, 6, 9, "paper", mark=False)
        elif kind == "alley":
            # Проулок: между домами лестница к тории, за ним горы в дымке и замок на утёсе.
            ax0, ax1 = x0 + 31, x1 - 31
            st.sky(ax0, 0, ax1, 160, 150)
            Sk = st.R("sky")
            # Дальние горы в тумане двумя планами.
            for xx in range(ax0, ax1 + 1):
                u = xx - ax0
                h1 = 96 - int(26 * math.exp(-((u - 38) / 26.0) ** 2) + 14 * math.exp(-((u - 104) / 20.0) ** 2))
                for yy in range(h1, 150):
                    c.set(xx, yy, Sk[1] if (yy - h1 < 5 or (xx + yy) % 2) and yy < 132 else Sk[2])
                h2 = 126 - int(30 * math.exp(-((u - 24) / 15.0) ** 2) + 10 * math.exp(-((u - 110) / 16.0) ** 2))
                for yy in range(h2, 152):
                    c.set(xx, yy, Sk[0] if yy < 142 or (xx + yy) % 2 else Sk[1])
            # Замок на утёсе: ярусы с загнутыми крышами.
            cx_ = ax0 + 24
            for k, (hw, ty) in enumerate(((13, 87), (10, 77), (7, 68))):
                st.rect(cx_ - hw + 3, ty + 3, cx_ + hw - 3, ty + 10, T[1])
                for d in range(-hw, hw + 1):
                    c.set(cx_ + d, ty + 2 - (1 if abs(d) > hw - 2 else 0), T[0])
                    if abs(d) < hw - 1:
                        c.set(cx_ + d, ty + 3, T[0])
                if k < 2:
                    c.set(cx_ - 2, ty + 7, G[2])
                    c.set(cx_ + 3, ty + 7, G[2])
            st.rect(cx_ - 3, 63, cx_ + 3, 69, T[0])
            for d in range(-4, 5):
                c.set(cx_ + d, 63 + abs(d) // 2, T[0])
            # Склоны по бокам лестницы.
            for yy in range(150, WALL_Y + 1):
                k = (yy - 150) / float(WALL_Y - 150)
                half = 22 + k * 44
                mx = (ax0 + ax1) // 2
                for xx in range(ax0, ax1 + 1):
                    if abs(xx - mx) > half:
                        v = (xx * 7 + yy * 13) % 11
                        c.set(xx, yy, M[0] if v < 6 else M[1] if v < 10 else M[2])
                    else:
                        step = int((yy - 150) / (3.0 + k * 6.0))
                        edge = int((yy - 150) - step * (3.0 + k * 6.0)) == 0
                        c.set(xx, yy, S_[3] if edge else S_[1] if (xx + step * 9) % 23 == 0 else S_[2])
                for sgn in (-1, 1):
                    c.set(int(mx + sgn * half), yy, S_[0])
            st.dark(ax0, 150, ax1, 156, 1, dither=True)
            # Тории наверху лестницы.
            mx = (ax0 + ax1) // 2
            for px_ in (mx - 20, mx + 16):
                st.rect(px_, 98, px_ + 4, 152, R_[2])
                st.rect(px_, 98, px_, 152, R_[3])
                st.rect(px_ + 4, 98, px_ + 4, 152, R_[0])
                st.rect(px_ - 1, 148, px_ + 5, 152, I[1])
            st.rect(mx - 25, 108, mx + 25, 111, R_[2])
            st.rect(mx - 25, 108, mx + 25, 108, R_[3])
            st.rect(mx - 25, 111, mx + 25, 111, R_[0])
            for d in range(-31, 32):
                lift = (abs(d) - 18) // 4 if abs(d) > 18 else 0
                c.set(mx + d, 93 - lift, I[1])
                c.set(mx + d, 94 - lift, I[0])
                c.set(mx + d, 95 - lift, R_[3])
                c.set(mx + d, 96 - lift, R_[2])
                c.set(mx + d, 97 - lift, R_[1])
            st.rect(mx - 2, 98, mx + 2, 107, R_[1])
            st.c.set(mx, 102, G[2])
            # Стены домов по бокам, клён свесился в проулок.
            st.planks(x0, 0, x0 + 30, WALL_Y, 10)
            st.planks(x1 - 30, 0, x1, WALL_Y, 10)
            st.rect(x0, 0, x0 + 30, 3, T[1])
            st.rect(x1 - 30, 0, x1, 3, T[1])
            st.post(x0 + 25, 0, WALL_Y, 6)
            st.post(x1 - 31, 0, WALL_Y, 6)
            st.dark(ax0 + 1, 0, ax0 + 6, WALL_Y, 1, dither=True)
            for t in range(40):
                bx, by = x1 - 31 - t, 58 - int(t * 0.75 - t * t * 0.006)
                st.rect(bx, by, bx, by + (2 if t < 22 else 1), W[0])
            st.maple(x1 - 56, 26, 24)
            st.chochin(x0 + 16, 74, 7, 10)
            st.chochin(x1 - 15, 96, 6, 9, "paper", mark=False)
        x += w
    # Тень у пола: низ стены темнеет.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Настил у стены: длинные доски рядами, швы вразбежку, гвозди, волокна.
    Dk = st.R("deck")
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    st.rect(0, WALL_Y + 1, SW - 1, CURB_Y - 1, Dk[0])
    for ri, (y0, h) in enumerate(rows):
        yb = min(y0 + h - 1, CURB_Y - 1)
        xx = -((ri * 37) % 90)
        while xx < SW:
            bw = rng.randint(70, 130)
            a, b = max(xx + 1, 0), min(xx + bw - 1, SW - 1)
            if b > a:
                ramp = Dk if rng.random() < 0.7 else [Dk[0], Dk[1], Dk[1], Dk[2]]
                st.bevel(a, y0, b, yb, ramp)
                for _ in range(bw // 9):
                    gx, gy = rng.randint(a + 2, max(a + 3, b - 14)), rng.randint(y0 + 2, yb - 2)
                    st.rect(gx, gy, min(gx + rng.randint(6, 22), b - 1), gy, ramp[1])
                for nx in (a + 3, b - 3):
                    c.set(nx, y0 + 3, Dk[0])
                    c.set(nx, yb - 3, Dk[0])
                    c.set(nx - 1, y0 + 2, Dk[3])
            xx += bw
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Бордюр: тёсаный камень блоками, мох в швах и по верху.
    for xx in range(SW):
        c.set(xx, CURB_Y, S_[3])
        c.set(xx, CURB_Y + 1, S_[2])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, S_[0] if xx % 42 == (yy // 4) * 17 % 42 else S_[2 if yy < ROAD_Y - 3 else 1])
        v = (xx * 31 + (xx // 9) * 17) % 53
        if v < 9:
            c.set(xx, CURB_Y + 1, M[2])
            if v < 5:
                c.set(xx, CURB_Y, M[3])
                c.set(xx, CURB_Y + 2, M[1])
            if v < 2:
                c.set(xx, CURB_Y + 3, M[1])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, I[1])
    # Дорожка: плиты неровной ширины рядами, ряды к зрителю выше, мох в швах.
    Sl = st.R("slab")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Sl[0])
    y = ROAD_Y + 2
    h = 14
    row = 0
    while y < SH:
        xx = -((row * 29) % 60)
        while xx < SW:
            pw = rng.randint(40, 78) + row * 5
            a, b = max(xx + 1, 0), min(xx + pw - 1, SW - 1)
            yb = min(y + h - 1, SH - 1)
            if b > a and yb > y:
                t = rng.choice((0, 0, 0, 1, 2))
                ramp = Sl if t == 0 else [Sl[0], Sl[1], Sl[1], Sl[2]] if t == 1 else [Sl[0], Sl[1], Sl[2], Sl[2]]
                st.bevel(a, y, b, yb, ramp)
                st.noise(a + 1, y + 1, b - 1, yb - 1, ramp, 0.04)
                # Сколотый угол и трещина.
                if rng.random() < 0.3 and b - a > 20:
                    for d in range(4):
                        st.rect(a, y + d, a + 3 - d, y + d, Sl[0])
                if rng.random() < 0.25 and b - a > 26 and yb - y > 8:
                    tx = rng.randint(a + 8, b - 8)
                    for d in range(yb - y - 2):
                        tx += rng.choice((-1, 0, 0, 1))
                        if a < tx < b:
                            c.set(tx, y + 1 + d, Sl[0])
                # Мох в швах.
                if rng.random() < 0.6:
                    mx0 = rng.randint(a, max(a, b - 12))
                    for d in range(rng.randint(8, 24)):
                        if mx0 + d < SW:
                            c.set(mx0 + d, yb, M[1 if d % 3 else 2])
                            if yb + 1 < SH:
                                c.set(mx0 + d, yb + 1, M[0 if d % 2 else 1])
                            if d % 2 and yb - 1 > y:
                                c.set(mx0 + d, yb - 1, M[2 if d % 4 == 1 else 3])
                            if d % 5 == 2 and yb - 2 > y:
                                c.set(mx0 + d, yb - 2, M[2])
            xx += pw
        y += h
        h += 3
        row += 1
    # Кленовые листья на дорожке: кучки под клёнами и одиночные.
    def leaf(lx, ly, big=True):
        col = R_[rng.choice((1, 2, 2, 3))]
        if not (0 <= lx < SW - 3 and ROAD_Y + 3 <= ly < SH - 2):
            return
        c.set(lx, ly, col)
        c.set(lx + 1, ly, col)
        if big:
            # Лист звёздочкой: лучи в стороны и вверх, черешок.
            c.set(lx - 1, ly, col)
            c.set(lx + 2, ly, col)
            c.set(lx, ly - 1, col)
            c.set(lx + 1, ly - 1, R_[3])
            c.set(lx - 2, ly - 1, R_[2])
            c.set(lx + 3, ly - 1, R_[2])
            c.set(lx + 1, ly + 1, R_[1])
            c.set(lx + 2, ly + 2, R_[0])
        c.set(lx, ly + 1, R_[0])

    for px0 in (220, 760, 1310):
        for _ in range(26):
            a = rng.random() * math.tau
            d = rng.random()
            leaf(int(px0 + math.cos(a) * 44 * d), int(372 + math.sin(a) * 9 * d), rng.random() < 0.6)
    for _ in range(90):
        leaf(rng.randint(0, SW - 4), rng.randint(ROAD_Y + 4, SH - 4), rng.random() < 0.4)
    for _ in range(40):
        lx, ly = rng.randint(0, SW - 4), rng.randint(WALL_Y + 6, CURB_Y - 3)
        c.set(lx, ly, R_[2])
        c.set(lx + 1, ly, R_[1])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("can", 20), ("can", 44), ("box", 290), ("can2", 600), ("can2", 618), ("coil", 680),
                       ("box", 870), ("box", 898), ("can", 1150), ("coil", 1400), ("can", 1590)):
        yb = WALL_Y + 8
        st.dark(px - 14 if kind != "box" else px - 2, yb + 1, px + (16 if kind != "box" else 36), yb + 2, 1)
        if kind == "can":
            st.komodaru(px, yb)
        elif kind == "can2":
            st.bucket(px, yb)
        elif kind == "box":
            st.basket(px, yb)
        else:
            st.kasa(px, yb)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки закатные, золото с кораллом, волна сумеречно-синяя, как
    костюм героя, пыль тёплая дорожная; стрелка «вперёд» красная с золотом, как шарф."""
    p = Pal(OUTLINE)
    p.add("white", [0xE8C8A0, 0xF6E6C8, 0xFFF8E8, 0xFFFFFF])
    if go:
        p.add("gold", [0x7E1418, 0xD93632, 0xF4CB52, 0xFFF0A8])
    else:
        p.add("gold", [0xB03A28, 0xE97B52, 0xF4CB52, 0xFFF4B8])
    p.add("blue", [0x1A1C48, 0x38469C, 0x6E84DC, 0xC8D4FF])
    p.add("dust", [0x5A4A40, 0x8A7868, 0xB7A894, 0xDCD0BC])
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
        import ninja16
        ninja16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own(), scale=1, max_w=FW * 12)
