# -*- coding: utf-8 -*-
"""Набор «Замки» для битемапа × 16/32-bit (#137): зеркало `pixel_brawl16.py` и `space_brawl16.py`.
Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты из `pixel_brawl16`
как есть (демка `fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и улица свои.

Бойцы: герой это рыцарь основы (`castles16.py`): стальные латы, ведёрный шлем с прорезью,
красный плюмаж хвостом назад, красный табард с золотой короной и золотой пояс, ножны за бедром;
громила это наёмник-здоровяк: конический шлем с наносником, рыжая борода, клёпаная кожанка,
голые руки и молот в ближней руке; враг с ножом это разбойник: зелёный капюшон с хвостом,
платок на лице, кинжал; босс это чёрный рыцарь: шлем с клювом и двумя рогами, горящая щель
забрала, багровый плащ с золотой каймой. Улица это улица под стеной замка: куртина с бойницами
и знамёнами, кузница с горном и наковальней, ворота с решёткой, часовня с витражами,
фахверковый дом, арка с видом на холмы; у стены плиты, бордюр тёсаным камнем, дальше брусчатка.

    python3 tools/castles_brawl16.py --preview out.png   # листы: out.png, out_b.png, out_c.png
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

# Обводка основы «Замков» (`castles16.PALETTE[K]`).
OUTLINE = 0x15131A

# Рампы от цветов основы: сталь лат (GREY, WHITE), красный табарда (RED, тень TAN), золото
# (GOLD, тень BRASS), железо (DARK), багровый стражи (TAN), кожа (SKIN).
STEEL = [0x4A5068, 0x7A8498, 0x9EA8BA, 0xE8ECF2]
IRON = [0x1E1E2A, 0x2C3040, 0x3C4050, 0x5A6074]
RED = [0x5E1626, 0x942838, 0xD2302C, 0xF46A50]
GOLD = [0x6A421C, 0x9C642C, 0xF4C84A, 0xFFF0A8]
SKIN = [0x7A4A34, 0xB87C58, 0xF0C498, 0xFFE2C4]
WOOD = [0x3A2414, 0x5E3C1E, 0x8A5A2C, 0xB8824A]


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("steel", STEEL)
    p.add("iron", IRON)
    p.add("red", RED)
    p.add("gold", GOLD)
    p.add("wood", WOOD)
    return Look("knight", p, Body(1.0, 1.1))


def thug_look():
    p = Pal(OUTLINE)
    p.add("skin", SKIN)
    p.add("leather", [0x2E1C14, 0x4E3220, 0x744C2C, 0x9C7040])
    p.add("pants", [0x1C2A22, 0x2E4434, 0x466248, 0x668462])
    p.add("boots", [0x1C1410, 0x34241A, 0x503826, 0x745438])
    p.add("iron", [0x2C3040, 0x4E566A, 0x7C8498, 0xB4BCCC])
    p.add("beard", [0x5A2410, 0x8E3E18, 0xC4622A, 0xE8904A])
    p.add("wood", WOOD)
    p.add("eye", [0x15131A, 0x15131A, 0x2C3040, 0xFFFFFF])
    return Look("merc", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("skin", SKIN)
    p.add("hood", [0x143024, 0x22503A, 0x347A4E, 0x5CA868])
    p.add("pants", [0x2A1C14, 0x46301E, 0x68482A, 0x8C683E])
    p.add("boots", [0x1C1410, 0x30221A, 0x4A3424, 0x6A4C34])
    p.add("mask", [0x3E0E1C, 0x6A1828, 0x942838, 0xC04A4A])
    p.add("steel", STEEL)
    p.add("gold", GOLD)
    p.add("eye", [0x15131A, 0x15131A, 0x2C3040, 0xFFFFFF])
    return Look("rogue", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("black", [0x0E0E16, 0x22243A, 0x3C4058, 0x6A7290])
    p.add("cloak", [0x3E0E1C, 0x6A1828, 0x942838, 0xC84A50])
    p.add("gold", GOLD)
    p.add("bone", [0x6E5A44, 0xA89674, 0xD8CCA8, 0xF8F2E0])
    p.add("glow", [0x7A1010, 0xD2302C, 0xFF7A40, 0xFFE0A0])
    return Look("black", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _dot(c, q, col, dx=0, dy=0):
    c.set(int(round(q[0])) + dx, int(round(q[1])) + dy, col)


def _hammer(c, pal, fist, d, s):
    """Молот наёмника: рукоять поперёк кулака, вверх и чуть вперёд от предплечья, на конце
    железный боёк бруском с ободами. Когда рука выброшена вперёд, молот заваливается назад к
    плечу: кулак в этих кадрах у края холста, и боёк не режется краем."""
    perp = (d[1], -d[0])
    fw = 0.38 if d[0] < 0.75 else -0.8
    t = (perp[0] * 0.92 + d[0] * fw, perp[1] * 0.92 + d[1] * fw)
    n = math.hypot(*t)
    t = (t[0] / n, t[1] / n)
    nrm = (-t[1], t[0])
    top = add(fist, t, 15 * s)
    put(c, pal, capsule(add(fist, t, -5 * s), top, 1.3, 1.3), pal["wood"], cast=False)

    def Q(a, b):
        return add(add(top, nrm, a * s), t, b * s)

    head = poly([Q(-6.5, -3.4), Q(6.5, -3.4), Q(6.5, 3.4), Q(-6.5, 3.4)])
    put(c, pal, head, pal["iron"], soft=True)
    I = pal["iron"]
    for a in (-5.0, 5.0):
        for b in range(-3, 4):
            q = Q(a, b)
            if (int(round(q[0])), int(round(q[1]))) in head:
                _dot(c, q, I[0])
    _dot(c, Q(-2.0, -1.5), I[3])
    _dot(c, Q(-1.0, -1.5), I[3])


def _dagger(c, pal, fist, d, s):
    """Кинжал разбойника остриём вдоль предплечья: рукоять, золотая гарда поперёк, клинок."""
    perp = (d[1], -d[0])
    tip = add(fist, d, 13 * s)
    put(c, pal, capsule(add(fist, d, -2.0), add(fist, d, 3.0), 1.3, 1.3), pal["boots"], cast=False)
    put(c, pal, capsule(add(fist, d, 3.4), tip, 1.8, 0.5), pal["steel"], cast=False)
    g = add(fist, d, 3.4)
    for k in (-3, -2, -1, 0, 1, 2, 3):
        _dot(c, add(g, perp, k), pal["gold"][3 if k < 0 else 2])
    _dot(c, add(fist, d, 7 * s), pal["steel"][3])


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    upper_ramp = {"knight": "steel", "merc": "skin", "rogue": "hood", "black": "black"}[kind]
    fore_ramp = {"knight": "steel", "merc": "skin", "rogue": "hood", "black": "black"}[kind]
    upper = capsule(sh, el, 4.3 * s * b, 3.5 * s * b) | ellipse(sh[0], sh[1] + 1, 4.7 * s * b, 4.5 * s * b)
    if kind == "merc":
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.2 * s * b, 3.5 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
    put(c, pal, upper, pal[upper_ramp], far=far, soft=True)
    fore = capsule(el, ha, 3.6 * s * b, 3.0 * s * b)
    put(c, pal, fore, pal[fore_ramp], far=far)
    if kind == "knight":
        # Наплечник куполом с ободом, налокотник, железная крага перчатки.
        put(c, pal, ellipse(sh[0], sh[1] - 0.5, 5.6 * s * b, 5.0 * s * b), pal["steel"], far=far, soft=True)
        rim = capsule(add(sh, (-4.6 * s, 3.6 * s)), add(sh, (4.6 * s, 3.6 * s)), 0.9, 0.9)
        put(c, pal, rim, pal["iron"], far=far, cast=False)
        put(c, pal, ellipse(el[0], el[1], 3.6 * s, 3.6 * s), pal["steel"], far=far, cast=False)
        if not far:
            _dot(c, el, pal["iron"][2])
        put(c, pal, capsule(add(ha, d, -5.0 * s), add(ha, d, -2.2 * s), 4.1 * s, 3.8 * s), pal["iron"], far=far)
    elif kind == "merc":
        # Голое плечо с кожаным ремнём-браслетом на бицепсе, кожаный наруч с клёпками.
        if not far:
            u = _unit(sh, el)
            q = lerp(sh, el, 0.55)
            put(c, pal, capsule(add(q, u, -1.0), add(q, u, 1.0), 4.5 * s * b, 4.4 * s * b), pal["leather"], cast=False)
            _dot(c, add(q, (u[1], -u[0]), 1.5), pal["iron"][3])
        put(c, pal, capsule(add(ha, d, -8.0 * s), add(ha, d, -3.0 * s), 4.1 * s * b, 3.8 * s * b), pal["leather"], far=far)
        for k in (-7.0, -4.2):
            _dot(c, add(ha, d, k * s), pal["iron"][3 if not far else 1])
    elif kind == "rogue":
        # Кожаный наруч со шнуровкой.
        put(c, pal, capsule(lerp(el, ha, 0.35), add(ha, d, -2.0 * s), 3.5 * s * b, 3.2 * s * b), pal["boots"], far=far)
        if not far:
            for k in (0.45, 0.62, 0.79):
                _dot(c, lerp(el, ha, k), pal["boots"][3])
    elif kind == "black":
        # Наплечник с шипом и багровой каймой, золотая манжета.
        put(c, pal, ellipse(sh[0], sh[1] - 0.5, 5.6 * s * b, 4.8 * s * b), pal["black"], far=far, soft=True)
        spike = poly([add(sh, (-3.4 * s, -3.6 * s)), add(sh, (-1.0 * s, -10.5 * s)), add(sh, (2.0 * s, -4.4 * s))])
        put(c, pal, spike, pal["black"], far=far, cast=False)
        rim = capsule(add(sh, (-5.4 * s, 4.2 * s)), add(sh, (5.4 * s, 4.2 * s)), 1.0, 1.0)
        put(c, pal, rim, pal["cloak"], far=far, cast=False)
        put(c, pal, capsule(add(ha, d, -5.0 * s), add(ha, d, -2.4 * s), 4.2 * s * b, 4.2 * s * b), pal["gold"], far=far)
        put(c, pal, ellipse(el[0], el[1], 3.4 * s, 3.4 * s), pal["black"], far=far, cast=False)
    fist = add(ha, d, 1.2 * s)
    if kind == "merc" and side == "n":
        _hammer(c, pal, fist, d, s)
    fr = min(b, 1.15) * (1.15 if kind == "merc" else 1.0)
    fs = ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr)
    fist_ramp = {"knight": "iron", "merc": "skin", "rogue": "skin", "black": "black"}[kind]
    put(c, pal, fs, pal[fist_ramp], far=far)
    if kind == "rogue" and side == "n":
        _dagger(c, pal, fist, d, s)


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    pants = {"knight": "steel", "merc": "pants", "rogue": "pants", "black": "black"}[kind]
    boots = {"knight": "iron", "merc": "boots", "rogue": "boots", "black": "black"}[kind]
    thigh = capsule(hp, kn, 6.0 * s * b, 4.8 * s * b)
    put(c, pal, thigh, pal[pants], far=far, soft=True)
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    top_h = {"knight": 9, "merc": 7, "rogue": 8, "black": 9}[kind] * s
    boot = capsule(add(an, sd, -top_h), an, 4.5 * s * b, 4.1 * s * b)
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
    shin = capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b, 4.0 * s * b)
    put(c, pal, boot | foot, pal[boots], far=far)
    put(c, pal, shin, pal[pants], far=far)
    if kind == "knight":
        # Стальная поножь поверх сапога, наколенник с крылом, блик по гребню голени.
        greave = capsule(add(kn, sd, 3.0 * s), add(an, sd, -1.5 * s), 4.6 * s * b, 4.0 * s * b)
        put(c, pal, greave, pal["steel"], far=far, cast=False)
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 3.4 * s, 3.6 * s), pal["steel"], far=far,
            cast=False)
        if not far:
            _dot(c, add(kn, fwd, 2.0), pal["iron"][2])
            band = add(an, sd, -1.0 * s)
            for k in range(-4, 5):
                _dot(c, add(band, fwd, k), pal["iron"][1])
    elif kind == "merc":
        # Отворот сапога и ремешок под коленом.
        put(c, pal, capsule(add(an, sd, -top_h - 0.6), add(an, sd, -top_h + 1.2), 4.9 * s * b, 4.9 * s * b),
            pal["leather"], far=far, cast=False)
        if not far:
            q = add(kn, sd, 3.0 * s)
            for k in range(-4, 5):
                _dot(c, add(q, fwd, k), pal["leather"][2])
    elif kind == "rogue":
        # Мягкий сапог с отворотом, заплата на колене.
        put(c, pal, capsule(add(an, sd, -top_h - 0.4), add(an, sd, -top_h + 1.0), 4.4 * s * b, 4.4 * s * b),
            pal["boots"], far=far, cast=False)
        if not far:
            q = add(kn, fwd, 1.5)
            _dot(c, q, pal["pants"][3])
            _dot(c, q, pal["pants"][3], 1, 0)
            _dot(c, q, pal["pants"][3], 0, 1)
    elif kind == "black":
        # Наколенник с золотым шипом, багровая кромка сабатона.
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 3.2 * s, 3.4 * s), pal["black"], far=far,
            cast=False)
        tip = add(kn, fwd, 6.5 * s)
        put(c, pal, capsule(add(kn, fwd, 3.0 * s), tip, 1.2, 0.5), pal["gold"], far=far, cast=False)
        if not far:
            band = add(an, sd, -top_h)
            for k in range(-5, 6):
                _dot(c, add(band, fwd, k), pal["cloak"][2])
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    recolor(c, sole, lambda x, y, e: pal[boots][0])


def _scabbard(c, look, j):
    """Ножны рыцаря за бедром: тёмная полоса наискось назад, золотое устье и наконечник,
    рукоять меча торчит над поясом. Рисуются до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    a = add(add(H, rt, -4.0 * s * b), up, 3.0 * s)
    e = add(add(H, rt, -17.0 * s * b), up, -15.0 * s)
    put(c, pal, capsule(a, e, 2.3 * s, 1.5 * s), pal["wood"], soft=False)
    put(c, pal, ellipse(e[0], e[1], 2.0, 2.0), pal["gold"], cast=False)
    hilt = add(add(H, rt, -1.5 * s * b), up, 7.5 * s)
    put(c, pal, capsule(a, hilt, 1.3, 1.3), pal["iron"], cast=False)
    put(c, pal, ellipse(hilt[0], hilt[1], 1.9, 1.9), pal["gold"], cast=False)


def _cape(c, look, j):
    """Верх плаща чёрного рыцаря: полоса за спиной от ворота до пояса, рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    S = poly([P(N, -3.0, 1), P(N, -10.5, -1), P(lerp(N, H, 0.5), -12.0, 0), P(H, -9.5, 0), P(H, -3.0, 0)])
    put(c, pal, S, pal["cloak"], soft=True)


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    pants = {"knight": "red", "merc": "pants", "rogue": "hood", "black": "black"}[kind]
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[pants], soft=True)
    belly = {"knight": 0.6, "merc": 1.8, "rogue": 0.0, "black": 1.2}[kind]
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "merc":
        tor |= ellipse(*P(lerp(N, H, 0.64), 3.6, 0), 7.2 * s * b, 6.4 * s)

    def mat(x, y):
        lx = ((x - N[0]) * rt[0] + (y - N[1]) * rt[1]) / (s * b)
        ly = -((x - N[0]) * up[0] + (y - N[1]) * up[1]) / s
        if kind == "knight":
            # Стальной горжет у шеи, ниже красный табард с золотой каймой по переднему краю.
            if ly < 4.2:
                return pal["steel"]
            return pal["red"]
        if kind == "merc":
            # Кожанка, перевязь наискось через грудь тёмным ремнём.
            if abs(lx * 1.5 + ly * 0.9 - 13.0) < 1.9:
                return pal["boots"]
            return pal["leather"]
        if kind == "rogue":
            # Зелёная туника, кожаный ремень сумки наискось.
            if abs(lx * 1.3 - ly * 0.8 + 8.0) < 1.5:
                return pal["boots"]
            return pal["hood"]
        # Чёрная кираса с багровой полосой по груди.
        if 1.6 < lx < 4.6 and ly > 5.0:
            return pal["cloak"]
        return pal["black"]

    put(c, pal, tor, None, soft=True, mat=mat)
    # Пояс с пряжкой.
    belt = poly([P(H, 6.8 + belly * 0.6, 5.8), P(H, 7.0 + belly * 0.6, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    belt_ramp = {"knight": "gold", "merc": "boots", "rogue": "boots", "black": "gold"}[kind]
    put(c, pal, belt, pal[belt_ramp], cast=False)
    bk = P(H, 4.6, 4.1)
    buckle = {"knight": "steel", "merc": "iron", "rogue": "gold", "black": "glow"}[kind]
    put(c, pal, ellipse(bk[0], bk[1], 1.8 * s, 1.6 * s), pal[buckle], cast=False)
    if kind == "knight":
        # Золотая корона на груди табарда: обруч и три зубца.
        q = P(lerp(N, H, 0.5), 3.2, 0)
        qx, qy = int(round(q[0])), int(round(q[1]))
        G = pal["gold"]
        for dx in range(-3, 4):
            if (qx + dx, qy) in tor:
                c.set(qx + dx, qy, G[2])
                c.set(qx + dx, qy + 1, G[1])
        for dx in (-3, 0, 3):
            if (qx + dx, qy - 2) in tor:
                c.set(qx + dx, qy - 1, G[2])
                c.set(qx + dx, qy - 2, G[3])
        # Заклёпки горжета.
        for r in (-3.0, 1.0, 5.0):
            _dot(c, P(N, r, -3.2), pal["iron"][2])
    elif kind == "merc":
        # Клёпки кожанки рядами и пряжка перевязи.
        I = pal["iron"]
        for row in range(4):
            for col in range(4):
                q = P(lerp(N, H, 0.2 + row * 0.17), -5.0 + col * 3.6 + (row % 2) * 1.6, 0)
                qq = (int(round(q[0])), int(round(q[1])))
                if qq in tor and c.get(*qq) in (pal["leather"][2], pal["leather"][3]):
                    c.set(qq[0], qq[1], I[3])
                    if (qq[0] + 1, qq[1] + 1) in tor:
                        c.set(qq[0] + 1, qq[1] + 1, pal["leather"][0])
        _dot(c, P(lerp(N, H, 0.34), 4.6, 0), pal["wood"][3])
    elif kind == "rogue":
        # Шнуровка ворота и сумка на ремне у пояса.
        for k in range(3):
            q = P(lerp(N, H, 0.18 + k * 0.1), 4.6, 0)
            _dot(c, q, pal["hood"][0])
            _dot(c, q, pal["skin"][2], 1, 0)
        q = P(H, -3.0, 6.5)
        put(c, pal, ellipse(q[0], q[1], 3.4 * s, 3.0 * s), pal["boots"], cast=False)
        _dot(c, q, pal["gold"][2])
    elif kind == "black":
        # Золотой кант кирасы и знак на груди: перевёрнутая корона.
        for k in range(9):
            q = P(lerp(N, H, 0.1 + k * 0.1), 7.2 - k * 0.1 + (0.9 if 2 < k < 7 else 0), 0)
            qq = (int(round(q[0])), int(round(q[1])))
            if qq in tor:
                c.set(qq[0], qq[1], pal["gold"][2])
        q = P(lerp(N, H, 0.32), 3.1, 0)
        put(c, pal, ellipse(q[0], q[1], 2.3 * s, 2.3 * s), pal["gold"], cast=False)
        _dot(c, q, pal["glow"][1])
        # Пластины набрюшника: тёмные швы.
        for k in (0.62, 0.78):
            for r in range(-6, 7):
                q = P(lerp(N, H, k), r, 0)
                qq = (int(round(q[0])), int(round(q[1])))
                if qq in tor and c.get(*qq) == pal["black"][2]:
                    c.set(qq[0], qq[1], pal["black"][1])


def _tails(c, look, j, p, long, ramp, hem=None):
    """Юбка табарда и туники (короткая) и плащ чёрного рыцаря (длинный); `hem` красит кайму."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = (33 if long else 15) * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 6.0 * s * b), up, 3 * s),
           (H[0] + 4 * s * b + sway * 0.3, H[1] + ln * 0.85), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - (13 if long else 10) * s * b + sway, H[1] + ln * 0.9)]
    S = poly(pts)
    put(c, pal, S, pal[ramp], soft=True)
    if long:
        # Складки плаща: тёмные косые штрихи.
        R_ = pal[ramp]
        for (x, y) in S:
            if c.get(x, y) == R_[2] and (x * 2 + y) % 11 == 0 and y > H[1] + 6:
                c.set(x, y, R_[1])
    if hem:
        edge = {q for q in S if (q[0], q[1] + 1) not in S or (q[0], q[1] + 2) not in S}
        recolor(c, edge, lambda x, y, e: pal[hem][2] if (x + y) % 3 else pal[hem][1])


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

    def line(a, b, col, S=None):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 1.5) + 1
        for k in range(n + 1):
            q = lerp(a, b, k / n)
            qq = (int(round(q[0])), int(round(q[1])))
            if S is None or qq in S:
                c.set(qq[0], qq[1], col)

    if kind == "knight":
        # Плюмаж: хвост за затылком качается, при ударе обвисает. Рисуется до шлема.
        drop = 5.0 if hurt else 0.0
        t0, t1, t2 = H(-3.0, -11.0), H(-11.5, -8.5 + wave + drop * 0.4), H(-14.5, 0.5 + wave * 2 + drop)
        put(c, pal, capsule(t0, t1, 2.6 * s, 2.8 * s) | capsule(t1, t2, 2.8 * s, 1.2 * s), pal["red"], soft=True)
        # Горжет под шлемом и сам шлем: ведро с плоским верхом, книзу чуть шире.
        ring = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.45), 5.0 * s, 4.8 * s)
        put(c, pal, ring, pal["steel"])
        helm = poly([H(-7.2, -9.6), H(6.8, -9.6), H(7.8, 6.4), H(-7.8, 6.4)])
        put(c, pal, helm, pal["steel"], soft=True)
        # Гребень плюмажа по темени.
        put(c, pal, capsule(H(-4.5, -11.0), H(3.0, -11.0), 1.7 * s, 1.7 * s), pal["red"], cast=False)
        St, Ir = pal["steel"], pal["iron"]
        # Обод понизу и крышка сверху тёмной сталью, усиление крестом по лицевой грани.
        for (x, y) in helm:
            lx, ly = local(x, y)
            if ly > 5.0:
                c.set(x, y, St[1] if ly < 5.9 else St[0])
            elif ly < -8.4 and c.get(x, y) != St[3]:
                c.set(x, y, St[3] if lx < 2 else St[2])
            elif 3.4 < lx < 4.5 and (ly < -3.2 or ly > -0.4):
                c.set(x, y, St[3] if c.get(x, y) != St[0] else St[1])
        # Прорезь для глаз и дыхательные отверстия.
        if hurt:
            line(H(0.0, -3.0), H(3.6, -1.2), 0, helm)
            line(H(3.6, -1.2), H(7.8, -2.8), 0, helm)
            for q in ((-3.5, -5.5), (-2.5, -4.5), (-4.5, -4.5), (-3.5, -3.5)):
                _dot(c, H(*q), St[3])
        else:
            for dy in (-2.4, -1.5):
                line(H(-0.5, dy), H(7.8, dy), 0, helm)
        for q in ((1.6, 1.6), (5.6, 1.6), (3.6, 3.2), (1.6, 3.2), (5.6, 3.2)):
            qq = H(*q)
            if (int(round(qq[0])), int(round(qq[1]))) in helm:
                _dot(c, qq, Ir[1])
        # Заклёпки по ободу.
        for dx in (-5.5, -2.5, 0.5):
            _dot(c, H(dx, 4.2), Ir[3])
        return
    if kind == "black":
        # Высокий ворот плаща за шеей с золотой кромкой.
        col = poly([H(-9, 9), H(-10.5, -1), H(-5, 3), H(2, 9)])
        put(c, pal, col, pal["cloak"], soft=True)
        edge = {q for q in col if (q[0] - 1, q[1]) not in col or (q[0], q[1] - 1) not in col}
        recolor(c, edge, lambda x, y, e: pal["gold"][2])
        # Дальний рог за шлемом.
        Bn = pal["bone"]
        f0, f1, f2 = H(-3.5, -7.0), H(-8.5, -12.5), H(-7.0, -19.0 - wave * 0.3)
        put(c, pal, capsule(f0, f1, 2.4 * s, 1.8 * s) | capsule(f1, f2, 1.8 * s, 0.4 * s), Bn, far=True)
        ring = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.5), 4.8 * s, 4.6 * s)
        put(c, pal, ring, pal["black"])
        # Шлем: купол и клюв забрала вперёд.
        dome = ellipse(*H(-0.5, -2.0), 8.0 * s, 8.6 * s, ang)
        beak = poly([H(0.5, -4.5), H(6.0, -3.2), H(10.5, 1.4), H(6.4, 5.6), H(0.0, 7.4), H(-5.0, 6.0)])
        helm = dome | beak
        put(c, pal, helm, pal["black"], soft=True)
        Bk = pal["black"]
        # Гребень золотом по темени и нащёчник швом.
        for k in range(0, 13):
            a = math.radians(200 + k * 11)
            q = H(-0.5 + math.cos(a) * 7.4, -2.0 + math.sin(a) * 8.0)
            if (int(round(q[0])), int(round(q[1]))) in helm:
                _dot(c, q, pal["gold"][2 if k % 3 else 3])
        line(H(0.2, -3.0), H(-0.8, 6.4), Bk[0], helm)
        for q in ((3.0, 2.6), (5.0, 3.4), (3.6, 4.6)):
            _dot(c, H(*q), Bk[0])
        # Щель забрала: горит, при ударе гаснет и рвётся.
        G = pal["glow"]
        if hurt:
            line(H(1.6, -1.8), H(4.0, -0.4), G[0], helm)
            line(H(5.4, -1.0), H(7.0, 0.2), G[0], helm)
        else:
            line(H(1.4, -2.0), H(7.6, -0.2), G[2], helm)
            line(H(1.4, -1.0), H(7.0, 0.6), G[1], helm)
            _dot(c, H(4.6, -1.2), G[3])
            _dot(c, H(5.6, -0.9), G[3])
        # Ближний рог: от виска вверх и вперёд дугой.
        n0, n1, n2 = H(-1.5, -8.0), H(3.8, -14.5), H(1.6, -21.0 - wave * 0.3)
        put(c, pal, capsule(n0, n1, 2.7 * s, 2.0 * s) | capsule(n1, n2, 2.0 * s, 0.4 * s), Bn, soft=False)
        for k in (0.3, 0.6, 0.9):
            _dot(c, lerp(n0, n1, k), Bn[1], 1, 0)
        put(c, pal, ellipse(n0[0], n0[1], 2.9 * s, 2.5 * s), pal["gold"], cast=False)
        return
    sk = pal["skin"]
    E = pal["eye"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
    put(c, pal, neck, sk)
    if kind == "merc":
        # Меховой ворот кожанки вокруг шеи.
        fur = capsule(add(j["neck"], j["rt"], -6.5 * s), add(j["neck"], j["rt"], 5.5 * s), 3.2 * s, 2.8 * s)
        put(c, pal, fur, pal["beard"], far=True, soft=True)
        skull = ellipse(*H(-0.2, -2.6), 7.8 * s, 8.2 * s, ang)
        jaw = poly([H(-4.0, 1.0), H(7.2, 0.6), H(6.8, 5.0), H(3.0, 8.4), H(-3.4, 7.2)])
        face = skull | jaw
        put(c, pal, face, sk, soft=True)
        # Нос картошкой и ухо.
        put(c, pal, ellipse(*H(7.6, 0.6), 1.9 * s, 1.7 * s), sk, cast=False)
        _dot(c, H(-3.4, -0.2), sk[1])
        _dot(c, H(-3.4, 0.8), sk[1])
        # Рыжая борода лопатой.
        beard = poly([H(-3.6, 2.4), H(1.0, 3.0), H(7.0, 2.6), H(7.4, 7.0), H(3.4, 13.0), H(-2.8, 9.0)])
        put(c, pal, beard, pal["beard"], soft=True, cast=False)
        for q in ((1.0, 6.0), (3.0, 8.5), (4.5, 5.5), (0.0, 8.0), (2.4, 10.6)):
            _dot(c, H(*q), pal["beard"][1])
        # Конический шлем с ободом и наносником.
        cap = poly([H(-8.4, -4.0), H(8.4, -4.0), H(5.0, -10.5), H(0.4, -16.0), H(-5.6, -10.0)])
        put(c, pal, cap, pal["iron"], soft=True)
        I = pal["iron"]
        band = capsule(H(-8.2, -3.6), H(8.4, -3.6), 1.3 * s, 1.3 * s)
        put(c, pal, band, [I[1], I[2], I[3], I[3]], cast=False)
        for dx in (-6.0, -2.0, 2.0, 6.0):
            _dot(c, H(dx, -3.6), I[0])
        line(H(0.4, -15.0), H(0.0, -5.4), I[1], cap)
        put(c, pal, capsule(H(7.6, -3.0), H(8.0, 1.6), 1.1 * s, 0.9 * s), I, cast=False)
        # Глаз под ободом, насупленная бровь; при ударе зажмурен, рот открыт.
        ex, ey = H(4.2, -0.6)
        ex, ey = int(round(ex)), int(round(ey))
        if hurt:
            for k in range(-1, 3):
                c.set(ex + k, ey, sk[0])
            mq = H(4.6, 5.4)
            put(c, pal, ellipse(mq[0], mq[1], 1.6, 1.4), [0, 0, 0, 0], cast=False)
        else:
            c.set(ex, ey, E[3])
            c.set(ex + 1, ey, E[0])
            c.set(ex - 1, ey - 1, pal["beard"][0])
            c.set(ex, ey - 1, pal["beard"][0])
            c.set(ex + 1, ey - 1, pal["beard"][0])
            c.set(ex + 2, ey, pal["beard"][0])
        return
    # Разбойник: хвост капюшона качается за затылком, пелерина на плечах, платок на лице.
    Hd = pal["hood"]
    t0, t1 = H(-6.5, -7.5), H(-13.5, -1.0 + wave * 1.5 + (4.0 if hurt else 0.0))
    put(c, pal, capsule(t0, t1, 3.0 * s, 0.9 * s), Hd, soft=True)
    cape = capsule(add(j["neck"], j["rt"], -7.0 * s), add(j["neck"], j["rt"], 5.5 * s), 4.0 * s, 3.4 * s)
    put(c, pal, cape, Hd, soft=True)
    edge = {q for q in cape if (q[0], q[1] + 1) not in cape}
    recolor(c, edge, lambda x, y, e: Hd[0] if (x // 2) % 2 else Hd[1])
    hood = ellipse(*H(-1.4, -2.6), 8.6 * s, 9.0 * s, ang) | poly([H(-7.0, -8.0), H(-2.0, -13.6), H(3.0, -9.5)]) \
        | poly([H(-6.5, 2.0), H(4.0, 3.0), H(2.6, 8.4), H(-6.0, 7.4)])
    put(c, pal, hood, Hd, soft=True)
    hole = (ellipse(*H(4.4, -0.6), 4.6 * s, 5.4 * s, ang) | poly([H(1.5, 1.5), H(7.6, 1.0), H(6.2, 6.0), H(2.6, 7.6)]))
    hole |= ellipse(*H(7.6, 0.8), 1.5 * s, 1.4 * s)
    put(c, pal, hole, sk, cast=False)
    # Тень капюшона на лбу.
    for (x, y) in hole:
        lx, ly = local(x, y)
        if ly < -3.2 and (x, y) in hood:
            c.set(x, y, sk[1] if ly > -4.4 else sk[0])
    # Платок: от переносицы вниз, узел складкой.
    scarf = {q for q in hole if local(*q)[1] > 1.0}
    put(c, pal, scarf, pal["mask"], cast=False)
    for q in ((4.0, 3.4), (5.4, 4.6), (3.0, 5.4)):
        qq = H(*q)
        if (int(round(qq[0])), int(round(qq[1]))) in scarf:
            _dot(c, qq, pal["mask"][1])
    ex, ey = H(4.6, -1.0)
    ex, ey = int(round(ex)), int(round(ey))
    if hurt:
        for k in range(-1, 3):
            c.set(ex + k, ey, sk[0])
    else:
        c.set(ex, ey, E[3])
        c.set(ex + 1, ey, E[0])
        c.set(ex - 1, ey - 1, sk[0])
        c.set(ex, ey - 1, sk[0])
        c.set(ex + 1, ey - 1, sk[0])


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if kind == "knight":
        _scabbard(c, look, j)
    if kind == "black":
        _cape(c, look, j)
        _tails(c, look, j, p, True, "cloak", "gold")
    _torso(c, look, j, p)
    if kind == "knight":
        _tails(c, look, j, p, False, "red", "gold")
    if kind == "rogue":
        _tails(c, look, j, p, False, "hood")
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
    for key, look, frame, w, h, left, up in (("hero", hero_look(), pb.hero_frames()[0], FW, FH, 17, 17),
                                             ("thug", thug_look(), pb.foe_frames()[0], FW, FH, 15, 19),
                                             ("knife", knife_look(), pb.foe_frames(knife=True)[0], FW, FH, 17, 17),
                                             ("boss", boss_look(), pb.foe_frames(boss=True)[0], BW, BH, 15, 23)):
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


# --- Улица под стеной замка ------------------------------------------------------------------------

def street_pal():
    p = Pal(0x15131A)
    p.add("stone", [0x3A3840, 0x5C5A5E, 0x7C7876, 0xA09C96])
    p.add("light", [0x5E5E68, 0x868892, 0xAAB0BC, 0xD4D8E0])
    p.add("iron", [0x1C1C26, 0x2C3040, 0x3C4050, 0x5A6074])
    p.add("wood", WOOD)
    p.add("plaster", [0x8A7A5E, 0xB8A680, 0xDCCCA0, 0xF2E8C8])
    p.add("red", RED)
    p.add("gold", [0x7A5A1C, 0xB08A2C, 0xF4C84A, 0xFFF0A8])
    p.add("green", [0x163E2A, 0x2A6A3E, 0x5CAE4A, 0x9AD86A])
    p.add("sky", [0x273B76, 0x4676C0, 0x86BEE8, 0xD3ECF6])
    p.add("fire", [0x94283A, 0xE0561C, 0xF8A030, 0xFFE68A])
    p.add("slab", [0x4A443E, 0x6C645A, 0x8E8676, 0xB0A894])
    p.add("cobble", [0x2E2E38, 0x45464F, 0x5E5F68, 0x7E8088])
    return p


def arch_mask(x0, x1, top, bottom, pointed=False):
    """Проём под аркой: прямоугольник до пят свода и свод, круглый или стрельчатый."""
    w = x1 - x0
    S = set()
    if pointed:
        r = w * 0.86
        spring = top + int(math.sqrt(max(r * r - (r - w / 2.0) ** 2, 0)))
        for y in range(top, spring):
            for x in range(x0, x1 + 1):
                if (x - (x1 - r)) ** 2 + (y - spring) ** 2 <= r * r and (x - (x0 + r)) ** 2 + (y - spring) ** 2 <= r * r:
                    S.add((x, y))
    else:
        spring = top + w // 2
        cx = (x0 + x1) / 2.0
        for y in range(top, spring):
            for x in range(x0, x1 + 1):
                if (x - cx) ** 2 + (y - spring) ** 2 <= (w / 2.0 + 0.3) ** 2:
                    S.add((x, y))
    for y in range(spring, bottom + 1):
        for x in range(x0, x1 + 1):
            S.add((x, y))
    return S


def grow(S, n):
    out = set(S)
    for _ in range(n):
        out |= {(x + dx, y + dy) for (x, y) in out for dx, dy in ((1, 0), (-1, 0), (0, -1))}
    return out


class Castle(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(137)

    def fill(self, S, col):
        for (x, y) in S:
            if 0 <= x < SW and 0 <= y < SH:
                self.c.px[y][x] = col

    def masonry(self, x0, y0, x1, y1, bw=40, bh=20, ramp="stone", moss=0.12):
        """Кладка тёсаным камнем: ряды со сдвигом, блоки разной ширины и тона, фаска, сколы,
        мох в швах понизу."""
        R_ = self.R(ramp)
        G = self.R("green")
        r = self.rng
        self.rect(x0, y0, x1, y1, R_[0])
        for row, y in enumerate(range(y0, y1 + 1, bh)):
            x = x0 - (0 if row % 2 == 0 else bw // 2) - r.randint(0, 6)
            while x <= x1:
                w = bw + r.randint(-8, 8)
                a, b = max(x + 1, x0), min(x + w - 1, x1)
                yb = min(y + bh - 2, y1)
                if b - a > 2 and yb - y > 2:
                    v = r.random()
                    tone_ = R_ if v < 0.6 else [R_[0], R_[1], R_[1], R_[2]] if v < 0.82 else [R_[1], R_[2], R_[3], R_[3]]
                    self.bevel(a, y, b, yb, tone_)
                    self.noise(a + 1, y + 1, b - 1, yb - 1, tone_, 0.05)
                    if r.random() < 0.22 and b - a > 12:
                        # Скол или трещина.
                        cx, cy = r.randint(a + 3, b - 6), r.randint(y + 2, yb - 3)
                        for k in range(r.randint(3, 7)):
                            self.c.set(cx + k, cy + (k // 2) % 2, tone_[0 if k % 3 else 1])
                    if r.random() < moss * (0.4 + (y - y0) / float(max(y1 - y0, 1))):
                        for xx in range(a, b + 1):
                            if r.random() < 0.6:
                                self.c.set(xx, yb + 1, G[1 if r.random() < 0.6 else 2])
                                if r.random() < 0.3:
                                    self.c.set(xx, yb, G[1])
                x += w

    def course(self, x0, x1, y, h=5):
        """Поясок светлого камня поперёк стены."""
        L = self.R("light")
        self.rect(x0, y, x1, y + h - 1, L[2])
        self.rect(x0, y, x1, y, L[3])
        self.rect(x0, y + h - 1, x1, y + h - 1, L[1])
        for xx in range(x0 + 18, x1, 44):
            self.rect(xx, y + 1, xx, y + h - 2, L[1])
        self.dark(x0, y + h, x1, y + h + 1, 1)

    def slit(self, cx, y0, h):
        """Бойница крестом: светлая рама, тёмная щель с перекладиной и круглым низом."""
        L, I = self.R("light"), self.R("iron")
        self.bevel(cx - 9, y0 - 6, cx + 9, y0 + h + 9, L)
        self.rect(cx - 9, y0 + h // 2, cx + 9, y0 + h // 2, L[1])
        S = set((x, y) for x in range(cx - 2, cx + 3) for y in range(y0, y0 + h + 1))
        S |= set((x, y) for x in range(cx - 6, cx + 7) for y in range(y0 + h // 3 - 2, y0 + h // 3 + 3))
        S |= ellipse(cx, y0 + h, 4, 4)
        self.fill(S, I[0])
        for (x, y) in S:
            if (x + 1, y) not in S or (x, y + 1) not in S:
                self.c.set(x, y, I[1])

    def banner(self, x, y, w, h, ramp="red", emblem="crown"):
        """Знамя на перекладине: полотнище со складками и ласточкиным хвостом, кайма, герб."""
        R_, G, Wd = self.R(ramp), self.R("gold"), self.R("wood")
        cx = x + w // 2
        self.dark(x + 4, y + 6, x + w + 4, y + h - 4, 1)
        for xx in range(x, x + w + 1):
            bottom = y + h - int((w / 2.0 - abs(xx - cx)) * 0.8)
            fold = math.sin((xx - x) * 0.55 + 0.6)
            for yy in range(y + 3, bottom + 1):
                t = 3 if fold > 0.75 else 2 if fold > -0.35 else 1
                if xx in (x, x + w) or yy == bottom:
                    t = max(t - 1, 0)
                self.c.set(xx, yy, R_[t])
            # Золотая кайма по бокам и по низу.
            if xx in (x + 2, x + w - 2):
                for yy in range(y + 4, bottom - 1):
                    self.c.set(xx, yy, G[2 if yy % 4 else 1])
            if x + 2 < xx < x + w - 2:
                self.c.set(xx, bottom - 2, G[2])
        ey = y + h // 2 - 4
        if emblem == "crown":
            self.rect(cx - 7, ey + 4, cx + 7, ey + 8, G[2])
            self.rect(cx - 7, ey + 4, cx + 7, ey + 4, G[3])
            self.rect(cx - 7, ey + 8, cx + 7, ey + 8, G[1])
            for dx in (-7, -1, 5):
                self.fill(poly([(cx + dx, ey + 4), (cx + dx + 1, ey - 4), (cx + dx + 2, ey + 4)]), G[2])
                self.c.set(cx + dx + 1, ey - 5, G[3])
            for dx in (-4, 0, 4):
                self.c.set(cx + dx, ey + 6, self.R("red" if ramp != "red" else "sky")[2])
        elif emblem == "tower":
            self.rect(cx - 5, ey - 2, cx + 5, ey + 10, G[2])
            for dx in (-6, -1, 4):
                self.rect(cx + dx, ey - 6, cx + dx + 2, ey - 3, G[2])
                self.c.set(cx + dx, ey - 6, G[3])
            self.rect(cx - 5, ey - 2, cx - 5, ey + 10, G[3])
            self.rect(cx + 5, ey - 2, cx + 5, ey + 10, G[1])
            self.fill(arch_mask(cx - 2, cx + 2, ey + 4, ey + 10), R_[0])
        else:
            for k in range(-9, 10):
                for t in range(4):
                    self.c.set(cx + k, ey + abs(k) + t, G[3 if t == 0 else 2 if t < 3 else 1])
        # Перекладина с золотыми шишками на кованых крюках.
        self.rect(x - 5, y, x + w + 5, y + 2, Wd[2])
        self.rect(x - 5, y, x + w + 5, y, Wd[3])
        self.rect(x - 5, y + 2, x + w + 5, y + 2, Wd[0])
        for xx in (x - 6, x + w + 5):
            self.fill(ellipse(xx, y + 1, 2, 2), G[2])
            self.c.set(xx - 1, y, G[3])
        for xx in (x + 5, x + w - 5):
            self.rect(xx, y - 5, xx, y - 1, self.R("iron")[1])

    def torch(self, x, y):
        """Факел в кованом держателе, пламя и тёплое пятно света на кладке."""
        I, F, Wd = self.R("iron"), self.R("fire"), self.R("wood")
        for (xx, yy) in ellipse(x, y - 8, 26, 26):
            e = self.c.get(xx, yy)
            if e is None:
                continue
            near = (xx - x) ** 2 + (yy - y + 8) ** 2 < 14 * 14
            for name in ("stone", "light", "plaster"):
                R_ = self.R(name)
                if e in R_ and R_.index(e) < 3 and (near or (xx + yy) % 2 == 0):
                    self.c.set(xx, yy, R_[R_.index(e) + 1])
        self.rect(x - 1, y, x + 1, y + 14, Wd[1])
        self.rect(x - 1, y, x - 1, y + 14, Wd[3])
        self.bevel(x - 4, y - 2, x + 4, y + 2, I)
        self.rect(x - 7, y + 8, x + 2, y + 9, I[2])
        self.rect(x - 8, y + 4, x - 7, y + 12, I[1])
        flame = ellipse(x, y - 8, 4.2, 6.5) | poly([(x - 3, y - 11), (x + 1, y - 20), (x + 3, y - 10)])
        self.fill(flame, F[1])
        self.fill(ellipse(x, y - 6, 3.0, 4.6) | poly([(x - 2, y - 9), (x, y - 15), (x + 2, y - 9)]), F[2])
        self.fill(ellipse(x, y - 5, 1.6, 2.8), F[3])
        self.c.set(x - 4, y - 16, F[2])
        self.c.set(x + 4, y - 20, F[1])

    def planks(self, S, x0, step=8, ramp="wood"):
        """Доски по маске: швы, блик у шва, сучки."""
        Wd = self.R(ramp)
        for (x, y) in S:
            k = (x - x0) % step
            self.c.set(x, y, Wd[1] if k == 0 else Wd[3] if k == 1 else Wd[2])
        for (x, y) in S:
            if (x * 7 + y * 13) % 97 == 0 and (x - x0) % step > 2:
                self.c.set(x, y, Wd[1])
                self.c.set(x, y + 1, Wd[1])

    def door(self, x, y, w, h, pointed=False, ramp="light"):
        """Дверь в арке: клинчатые камни рамы, доски, кованые петли с завитком, кольцо."""
        I, L = self.R("iron"), self.R(ramp)
        S = arch_mask(x, x + w, y, y + h, pointed)
        frame = grow(S, 6) - S
        frame = {q for q in frame if q[1] <= y + h}
        self.put(frame, L, soft=False)
        cx, cy = x + w / 2.0, y + w * 0.6
        for (xx, yy) in frame:
            if yy < y + w // 2 + 4:
                a = math.atan2(yy - cy, xx - cx)
                if int(a * 9) % 2 == 0 and abs(a * 9 - int(a * 9)) < 0.22:
                    self.c.set(xx, yy, L[1])
            elif (yy - y) % 16 == 0:
                self.c.set(xx, yy, L[1])
        self.planks(S, x, 8)
        for hy in (y + h // 3, y + h * 3 // 4):
            for xx in range(x + 1, x + w - 6):
                if (xx, hy) in S:
                    self.c.set(xx, hy - 1, I[3])
                    self.c.set(xx, hy, I[2])
                    self.c.set(xx, hy + 1, I[0])
            for xx in range(x + 6, x + w - 8, 8):
                self.c.set(xx, hy, I[0])
            self.fill(ellipse(x + w - 7, hy, 2.5, 2.5) - ellipse(x + w - 7, hy, 1, 1), I[2])
        ring = ellipse(x + w - 8, y + h // 2 + 4, 4, 4) - ellipse(x + w - 8, y + h // 2 + 4, 2.4, 2.4)
        self.fill(ring, I[3])
        self.c.set(x + w - 8, y + h // 2, I[0])
        # Тень проёма сверху и слева, порог.
        for (xx, yy) in S:
            if (xx - 2, yy - 3) not in S:
                e = self.c.get(xx, yy)
                self.c.set(xx, yy, self.p.darker.get(e, e))
        self.bevel(x - 8, y + h + 1, x + w + 8, y + h + 4, L)

    def glass(self, x, y, w, h):
        """Стрельчатый витраж: свинцовая сетка ромбами, цветные стёкла, средник и рама камнем."""
        I, L = self.R("iron"), self.R("light")
        S = arch_mask(x, x + w, y, y + h, True)
        frame = grow(S, 5) - S
        self.put(frame, L, soft=False)
        cols = (self.R("red")[2], self.R("sky")[2], self.R("gold")[2], self.R("green")[2], self.R("sky")[1],
                self.R("red")[1], self.R("sky")[3])
        cx = x + w // 2
        for (xx, yy) in S:
            u, v = (xx + yy) // 7, (xx - yy) // 7
            if (xx + yy) % 7 == 0 or (xx - yy) % 7 == 0 or xx == cx:
                self.c.set(xx, yy, I[0])
            else:
                # Роза в центре окна собрана из красных и золотых стёкол, по краям синие.
                d = math.hypot(xx - cx, yy - (y + h * 0.42))
                k = cols[(u * 3 + v * 5) % 7] if d > w * 0.42 else cols[(u + v) % 2 * 2] if d > w * 0.2 else cols[2]
                self.c.set(xx, yy, k)
        for (xx, yy) in S:
            if (xx - 2, yy - 2) not in S:
                e = self.c.get(xx, yy)
                self.c.set(xx, yy, self.p.darker.get(e, e))
        self.bevel(x - 7, y + h + 1, x + w + 7, y + h + 5, L)
        self.dark(x - 5, y + h + 6, x + w + 8, y + h + 7, 1)

    def fachwerk(self, x0, y0, x1, y1):
        """Фахверк: светлая штукатурка в тёмном брусе, стойки, ригели и раскосы."""
        P = self.R("plaster")
        Wd = self.R("wood")
        self.rect(x0, y0, x1, y1, P[2])
        self.noise(x0, y0, x1, y1, P, 0.05)
        r = self.rng
        for _ in range((x1 - x0) // 40):
            sx = r.randint(x0 + 4, x1 - 4)
            for y in range(y0 + 6, y0 + r.randint(20, 46)):
                if r.random() < 0.7:
                    self.c.set(sx, y, P[1])
        beam = [Wd[0], Wd[1], Wd[2], Wd[3]]
        mid = (y0 + y1) // 2 + 14
        posts = list(range(x0, x1 - 6, 51)) + [x1 - 6]
        for i in range(len(posts) - 1):
            a, b = posts[i] + 6, posts[i + 1]
            if i % 2 == 0:
                self.put(capsule((a, mid - 2), (b, y0 + 8), 2.6, 2.6), beam, soft=False)
            else:
                self.put(capsule((a, y0 + 8), (b, mid - 2), 2.6, 2.6), beam, soft=False)
        for yy in (y0, mid, y1 - 6):
            self.bevel(x0, yy, x1, yy + 6, beam)
            for xx in range(x0 + 5, x1, 9):
                if r.random() < 0.5:
                    self.rect(xx, yy + 3, xx + r.randint(2, 5), yy + 3, Wd[1])
        for xx in posts:
            self.bevel(xx, y0, xx + 6, y1, beam)
            for yy in (y0 + 3, mid + 3, y1 - 3):
                self.c.set(xx + 3, yy, Wd[0])

    def window(self, x, y, w, h):
        """Окно с ромбами свинцовой сетки, ставни по бокам, под ним ящик с розами."""
        Wd, S_, I = self.R("wood"), self.R("sky"), self.R("iron")
        for sx in (x - 15, x + w + 3):
            self.bevel(sx, y - 1, sx + 12, y + h + 1, Wd)
            for xx in range(sx + 4, sx + 12, 4):
                self.rect(xx, y, xx, y + h, Wd[1])
            for k in range(11):
                self.c.set(sx + 1 + k, y + 4 + k * (h - 8) // 11, Wd[3])
            self.rect(sx + 1, y + 3, sx + 11, y + 3, Wd[1])
            self.rect(sx + 1, y + h - 3, sx + 11, y + h - 3, Wd[1])
        self.bevel(x - 2, y - 2, x + w + 2, y + h + 2, Wd)
        for yy in range(y, y + h + 1):
            for xx in range(x, x + w + 1):
                if (xx + yy) % 6 == 0 or (xx - yy) % 6 == 0:
                    self.c.set(xx, yy, I[1])
                else:
                    k = (xx - x) + (yy - y)
                    self.c.set(xx, yy, S_[2] if abs(k - (w + h) * 0.35) < 5 else S_[0] if k > (w + h) * 0.7 else S_[1])
        self.rect(x + w // 2, y, x + w // 2, y + h, Wd[1])
        self.dark(x, y, x + w, y + 2, 1)
        self.bevel(x - 6, y + h + 5, x + w + 6, y + h + 12, Wd)
        self.roses(x - 6, y + h + 6, w + 12, 9)

    def roses(self, x, y, w, h):
        """Куст роз: листва шапками до строки `y`, красные цветы с бликом."""
        G, R_ = self.R("green"), self.R("red")
        r = self.rng
        S = set()
        for k in range(max(2, w // 7)):
            S |= ellipse(x + 4 + k * (w - 8) / max(1, w // 7 - 1), y - h * 0.45 + r.randint(-2, 2), 5.5, h * 0.6)
        S = {q for q in S if q[1] <= y}
        self.put(S, G, soft=True)
        for q in sorted(S):
            v = r.random()
            if v < 0.05 and (q[0] + 1, q[1] + 1) in S and (q[0] - 1, q[1] - 1) in S:
                self.c.set(q[0], q[1], R_[2])
                self.c.set(q[0] + 1, q[1], R_[1])
                self.c.set(q[0], q[1] - 1, R_[3])
            elif v < 0.1:
                self.c.set(q[0], q[1], G[1])

    def ivy(self, x, y0, y1, spread=10):
        """Плющ по стене: плеть вниз с листьями в обе стороны."""
        G = self.R("green")
        r = self.rng
        xx = x
        for yy in range(y0, y1):
            xx += r.choice((-1, 0, 0, 1))
            xx = max(x - spread, min(x + spread, xx))
            self.c.set(xx, yy, G[0])
            if r.random() < 0.6:
                d = r.choice((-1, 1))
                ln = r.randint(2, 5)
                for k in range(1, ln + 1):
                    self.c.set(xx + d * k, yy - k // 2, G[1 if k < ln else 2])
                self.c.set(xx + d * ln, yy - ln // 2 - 1, G[3 if r.random() < 0.4 else 2])
                self.c.set(xx + d * (ln - 1), yy - ln // 2 - 1, G[2])

    def shield(self, cx, cy, ramp="red", ramp2="gold", size=1.0):
        """Гербовый щит: тарч с каймой, поле рассечено надвое."""
        R_, G, I = self.R(ramp), self.R(ramp2), self.R("iron")
        k = size
        S = poly([(cx - 9 * k, cy - 10 * k), (cx + 9 * k, cy - 10 * k), (cx + 9 * k, cy + 1 * k), (cx, cy + 12 * k),
                  (cx - 9 * k, cy + 1 * k)])
        self.dark(cx - 7 * k, cy - 7 * k, cx + 12 * k, cy + 8 * k, 1)
        self.put(S, R_, soft=True)
        for (x, y) in S:
            if x > cx and c_inner(S, x, y):
                self.c.set(x, y, G[2] if (x + 1, y + 1) in S and (x + 2, y + 2) in S else G[1])
        edge = {q for q in S if not c_inner(S, *q)}
        self.fill(edge, I[2])
        for q in edge:
            if (q[0] - 1, q[1]) not in S or (q[0], q[1] - 1) not in S:
                self.c.set(q[0], q[1], I[3])
        self.c.set(int(cx), int(cy - 2 * k), I[3])

    def portcullis(self, x0, x1, y0, y1):
        """Подъёмная решётка: кованые прутья, поперечины, острые зубья понизу."""
        I = self.R("iron")
        for xx in range(x0 + 6, x1 - 2, 14):
            self.rect(xx, y0, xx + 2, y1, I[2])
            self.rect(xx, y0, xx, y1, I[3])
            self.rect(xx + 3, y0, xx + 3, y1, I[0])
            self.fill(poly([(xx - 1, y1), (xx + 3, y1), (xx + 1, y1 + 7)]), I[2])
            self.c.set(xx, y1 + 1, I[3])
        for yy in range(y0 + 6, y1, 14):
            self.rect(x0, yy, x1, yy + 2, I[2])
            self.rect(x0, yy, x1, yy, I[3])
            self.rect(x0, yy + 3, x1, yy + 3, I[0])
            for xx in range(x0 + 7, x1 - 2, 14):
                self.c.set(xx, yy + 1, I[3])

    # Предметы у стены -------------------------------------------------------------------------

    def sack(self, x, y, w=20, h=26):
        """Мешок с зерном: пузатый, с завязанной горловиной и заплатой."""
        P, Wd = self.R("plaster"), self.R("wood")
        S = ellipse(x, y - h * 0.42, w / 2.0, h * 0.45) | poly([(x - w / 2.0, y - h * 0.3), (x + w / 2.0, y - h * 0.3),
                                                               (x + w / 2.0 - 1, y), (x - w / 2.0 + 1, y)])
        S |= poly([(x - 3, y - h * 0.8), (x + 3, y - h * 0.8), (x + 5, y - h), (x - 5, y - h)])
        S = {q for q in S if q[1] <= y}
        self.put(S, [P[0], P[1], P[2], P[3]], soft=True)
        for xx in range(int(x - 3), int(x + 4)):
            self.c.set(xx, int(y - h * 0.8), Wd[1])
        self.rect(x - 5, y - h // 2, x - 1, y - h // 2 + 4, P[1])
        self.c.set(x - 5, y - h // 2, Wd[2])
        self.c.set(x - 1, y - h // 2 + 4, Wd[2])
        for k in range(3):
            self.c.set(x + 3 + k, y - h // 3 + k * 2, P[1])

    def pail(self, x, y, w=14, h=16):
        """Деревянное ведро с обручами и дужкой, внутри вода."""
        Wd, I, S_ = self.R("wood"), self.R("iron"), self.R("sky")
        S = poly([(x - w / 2.0, y - h), (x + w / 2.0, y - h), (x + w / 2.0 - 2, y), (x - w / 2.0 + 2, y)])
        self.put(S, Wd, soft=False)
        for (xx, yy) in S:
            if (xx - x) % 4 == 0 and self.c.get(xx, yy) == Wd[2]:
                self.c.set(xx, yy, Wd[1])
        for hy in (y - h + 4, y - 3):
            for (xx, yy) in S:
                if yy == hy:
                    self.c.set(xx, yy, I[3] if xx < x else I[2])
        self.fill(ellipse(x, y - h, w / 2.0, 2.2), S_[1])
        self.fill(ellipse(x - 1, y - h, w / 2.0 - 2, 1.0), S_[2])
        arc = ellipse(x, y - h, w / 2.0, 8) - ellipse(x, y - h, w / 2.0 - 1.2, 7)
        self.fill({q for q in arc if q[1] < y - h - 1}, I[2])

    def coffer(self, x, y, w=30, h=22):
        """Окованный ларь: доски, выпуклая крышка, железные полосы с клёпками, замок."""
        Wd, I, G = self.R("wood"), self.R("iron"), self.R("gold")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h + 6, y + 1))
        lid = {q for q in ellipse(x + w / 2.0, y - h + 7, w / 2.0 + 0.5, 8) if q[1] <= y - h + 7}
        self.put(S | lid, Wd, soft=False)
        for yy in range(y - h + 11, y, 5):
            self.rect(x + 1, yy, x + w - 1, yy, Wd[1])
        self.rect(x, y - h + 7, x + w, y - h + 8, I[1])
        for bx in (x + 4, x + w - 7):
            for (xx, yy) in S | lid:
                if bx <= xx <= bx + 3:
                    self.c.set(xx, yy, I[3] if xx == bx else I[2] if xx < bx + 3 else I[1])
            for yy in range(y - h + 3, y, 5):
                self.c.set(bx + 1, yy, I[0])
        self.rect(x + w // 2 - 2, y - h + 7, x + w // 2 + 2, y - h + 12, G[2])
        self.rect(x + w // 2 - 2, y - h + 7, x + w // 2 + 2, y - h + 7, G[3])
        self.c.set(x + w // 2, y - h + 10, I[0])
        self.rect(x, y - 1, x + w, y, I[1])

    def wheel(self, x, y, r=13):
        """Тележное колесо, прислонённое к стене: обод с железной шиной, ступица, спицы."""
        Wd, I = self.R("wood"), self.R("iron")
        cy = y - r
        rim = ellipse(x, cy, r, r) - ellipse(x, cy, r - 3.2, r - 3.2)
        self.dark(x - r + 3, cy - r + 3, x + r + 3, y, 1, dither=True)
        self.put(rim, Wd, soft=False)
        for q in rim:
            if (q[0] - x) ** 2 + (q[1] - cy) ** 2 > (r - 1.3) ** 2:
                self.c.set(q[0], q[1], I[3] if q[0] + q[1] < x + cy else I[1])
        for k in range(8):
            a = k * math.pi / 4 + 0.2
            for t in range(3, int(r - 3)):
                self.c.set(int(round(x + math.cos(a) * t)), int(round(cy + math.sin(a) * t)), Wd[3 if k in (4, 5, 6) else 1])
        self.fill(ellipse(x, cy, 3, 3), Wd[2])
        self.fill(ellipse(x, cy, 1.2, 1.2), I[1])
        self.c.set(x - 1, cy - 2, Wd[3])


# Имя класса улицы у зеркала (`space_brawl16.Deck`): сборщик и листы берут его по этому имени.
Deck = Castle


def c_inner(S, x, y):
    return all((x + dx, y + dy) in S for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)))


def build_street():
    """Улица под стеной замка той же ширины и с теми же строками пола, что улица пиратов: стена
    до `WALL_Y`, плиты у стены до `CURB_Y`, бордюр тёсаным камнем, брусчатка от `ROAD_Y`."""
    st = Castle()
    c, rng = st.c, st.rng
    S_, L, I, Wd, G, Gr = st.R("stone"), st.R("light"), st.R("iron"), st.R("wood"), st.R("gold"), st.R("green")
    Sk, F = st.R("sky"), st.R("fire")
    x = 0
    modules = [("wall", 320), ("smithy", 288), ("gate", 352), ("chapel", 256), ("house", 256), ("arch", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        # Верх: дощатый настил боевого хода с торцами балок, под ним каменные кронштейны.
        st.rect(x0, 0, x1, 19, Wd[1])
        for yy in (5, 12):
            st.rect(x0, yy, x1, yy, Wd[0])
            st.rect(x0, yy + 1, x1, yy + 1, Wd[2])
        for xx in range(x0, x1, 5):
            if rng.random() < 0.3:
                st.rect(xx, rng.randint(2, 17), xx + rng.randint(4, 12), rng.randint(2, 17), Wd[0])
        st.bevel(x0, 20, x1, 25, L)
        st.rect(x0, 26, x1, 31, S_[0])
        for xx in range(x0 + 4, x1 - 10, 32):
            st.bevel(xx, 9, xx + 9, 19, Wd)
            c.set(xx + 4, 14, Wd[1])
            st.bevel(xx - 1, 26, xx + 10, 31, L)
            st.rect(xx + 1, 30, xx + 8, 31, L[1])
        if kind == "wall":
            st.masonry(x0, 32, x1, WALL_Y, 46, 22)
            st.course(x0, x1, 172)
            st.slit(x0 + 164, 86, 46)
            st.banner(x0 + 42, 58, 46, 96, "red", "crown")
            st.banner(x0 + 236, 58, 46, 96, "sky", "tower")
            st.torch(x0 + 118, 120)
            st.torch(x0 + 210, 120)
            # Кольцо коновязи и решётка стока понизу.
            st.bevel(x0 + 22, 192, x0 + 56, 214, I, inset=True)
            for xx in range(x0 + 26, x0 + 54, 5):
                st.rect(xx, 194, xx + 1, 212, I[3])
            ring = ellipse(x0 + 150, 204, 6, 6) - ellipse(x0 + 150, 204, 4, 4)
            st.fill(ring, I[3])
            st.rect(x0 + 148, 194, x0 + 152, 198, I[2])
            st.shield(x0 + 256, 198, "sky", "light", 0.9)
            st.ivy(x1 - 12, 34, 200, 9)
            st.ivy(x1 - 30, 34, 120, 7)
        elif kind == "smithy":
            st.masonry(x0, 32, x1, WALL_Y, 38, 19, "light", 0.05)
            # Горн в арочной нише: копоть над сводом, угли, огонь; перед ним наковальня на колоде.
            fx0, fx1 = x0 + 22, x0 + 126
            niche = arch_mask(fx0, fx1, 84, WALL_Y)
            frame = grow(niche, 7) - niche
            st.put(frame, S_, soft=False)
            for (xx, yy) in frame:
                if (xx + yy * 2) % 17 == 0:
                    c.set(xx, yy, S_[1])
            for (xx, yy) in niche:
                d = math.hypot(xx - (fx0 + fx1) / 2.0, (yy - (WALL_Y - 26)) * 1.3)
                c.set(xx, yy, F[0] if d < 30 and (d < 22 or (xx + yy) % 2) else I[0] if d > 40 or (xx + yy) % 2 else I[1])
            for (xx, yy) in ellipse((fx0 + fx1) // 2, 76, 34, 14):
                e = c.get(xx, yy)
                if e is not None and (xx, yy) not in niche and (xx + yy) % 2 == 0:
                    c.set(xx, yy, st.p.darker.get(e, e))
            hx = (fx0 + fx1) // 2 - 14
            st.bevel(hx - 22, WALL_Y - 30, hx + 22, WALL_Y, S_)
            for k in range(5):
                bx = hx - 16 + k * 8
                st.fill(poly([(bx - 4, WALL_Y - 31), (bx, WALL_Y - 44 - (k * 7) % 11), (bx + 4, WALL_Y - 31)]), F[1])
                st.fill(poly([(bx - 2, WALL_Y - 31), (bx, WALL_Y - 38 - (k * 5) % 7), (bx + 2, WALL_Y - 31)]), F[2])
                c.set(bx, WALL_Y - 32, F[3])
                c.set(bx + 1, WALL_Y - 32, F[3])
            st.rect(hx - 20, WALL_Y - 31, hx + 20, WALL_Y - 30, F[2])
            ax = fx1 - 24
            st.bevel(ax - 8, WALL_Y - 14, ax + 8, WALL_Y, Wd)
            anvil = poly([(ax - 18, WALL_Y - 26), (ax + 12, WALL_Y - 26), (ax + 12, WALL_Y - 21), (ax + 5, WALL_Y - 19),
                          (ax + 5, WALL_Y - 15), (ax - 6, WALL_Y - 15), (ax - 6, WALL_Y - 19), (ax - 10, WALL_Y - 21)])
            st.put(anvil, [I[1], I[2], I[3], L[2]], soft=False)
            # Вывеска кузнеца: молот на кованом кронштейне.
            sx = x0 + 150
            st.rect(sx, 62, sx + 34, 63, I[2])
            st.rect(sx, 62, sx + 1, 74, I[2])
            for k in range(8):
                c.set(sx + 3 + k, 72 - k, I[3])
            for xx in (sx + 10, sx + 28):
                st.rect(xx, 64, xx, 69, I[3])
            st.bevel(sx + 4, 70, sx + 34, 98, Wd)
            st.rect(sx + 18, 76, sx + 20, 94, L[2])
            st.bevel(sx + 11, 74, sx + 27, 81, [I[1], I[2], I[3], L[3]])
            st.dark(sx + 8, 99, sx + 38, 101, 1)
            # Доска с подковами, клещами и клинком.
            st.bevel(x0 + 142, 122, x0 + 216, 127, Wd)
            for k, hx2 in enumerate((x0 + 152, x0 + 168, x0 + 184)):
                shoe = ellipse(hx2, 140, 6, 7) - ellipse(hx2, 142, 3.4, 6)
                st.put({q for q in shoe if q[1] < 147}, [I[1], I[2], I[3], L[2]], soft=False)
                c.set(hx2, 128, I[3])
                c.set(hx2, 129, I[3])
            st.rect(x0 + 200, 128, x0 + 201, 170, L[2])
            st.rect(x0 + 202, 128, x0 + 202, 170, L[1])
            st.rect(x0 + 196, 134, x0 + 206, 135, G[2])
            st.rect(x0 + 200, 128, x0 + 202, 133, Wd[1])
            st.fill(poly([(x0 + 200, 170), (x0 + 202, 170), (x0 + 201, 175)]), L[2])
            st.door(x0 + 234, 110, 42, WALL_Y - 115, ramp="stone")
            st.torch(x0 + 222, 96)
            # Бочонок с водой для закалки заменён корытом: каменная колода у стены.
            st.bevel(x0 + 146, WALL_Y - 22, x0 + 212, WALL_Y, S_)
            st.rect(x0 + 150, WALL_Y - 20, x0 + 208, WALL_Y - 16, Sk[1])
            st.rect(x0 + 154, WALL_Y - 19, x0 + 176, WALL_Y - 19, Sk[2])
        elif kind == "gate":
            st.masonry(x0, 32, x1, WALL_Y, 50, 24)
            # Контрфорсы по бокам ворот.
            for bx in (x0 + 34, x0 + 266):
                st.masonry(bx, 40, bx + 24, WALL_Y, 24, 16, "light", 0.04)
                st.rect(bx, 40, bx, WALL_Y, L[3])
                st.rect(bx + 24, 40, bx + 24, WALL_Y, L[0])
                st.fill(poly([(bx - 1, 46), (bx + 25, 46), (bx + 25, 40), (bx + 12, 34), (bx - 1, 40)]), L[2])
                st.dark(bx + 25, 40, bx + 28, WALL_Y, 1)
            gx0, gx1 = x0 + 78, x0 + 246
            gate = arch_mask(gx0, gx1, 58, WALL_Y)
            frame = grow(gate, 9) - gate
            st.put(frame, L, soft=False)
            cx, cy = (gx0 + gx1) / 2.0, 58 + (gx1 - gx0) / 2.0
            for (xx, yy) in frame:
                if yy < cy:
                    a = math.atan2(yy - cy, xx - cx) * 12
                    if abs(a - round(a)) < 0.12:
                        c.set(xx, yy, L[1])
                elif (yy - 58) % 18 == 0:
                    c.set(xx, yy, L[1])
            # Створки: доски, кованые полосы с клёпками, калитка; над ними поднятая решётка.
            st.planks(gate, gx0, 10)
            mid = (gx0 + gx1) // 2
            st.rect(mid - 1, 58, mid + 1, WALL_Y, I[0])
            for yy in (126, 168, 212):
                for xx in range(gx0, gx1 + 1):
                    if (xx, yy) in gate and abs(xx - mid) > 2:
                        c.set(xx, yy - 2, I[3])
                        c.set(xx, yy - 1, I[2])
                        c.set(xx, yy, I[2])
                        c.set(xx, yy + 1, I[0])
                        if (xx - gx0) % 10 == 5:
                            c.set(xx, yy - 1, L[3])
                            c.set(xx + 1, yy, I[0])
            for sx in (mid - 12, mid + 12):
                ring = ellipse(sx, 150, 5, 5) - ellipse(sx, 150, 3, 3)
                st.fill(ring, I[3])
                st.c.set(sx, 145, I[0])
            top = {q for q in gate if q[1] < 104}
            st.fill(top, I[0])
            st.portcullis(gx0 + 2, gx1 - 2, 62, 96)
            for (xx, yy) in gate:
                if 104 <= yy < 112 or xx < gx0 + 7:
                    e = c.get(xx, yy)
                    if yy < 108 or (xx + yy) % 2 == 0 or xx < gx0 + 4:
                        c.set(xx, yy, st.p.darker.get(e, e))
            # Герб над замковым камнем и факелы у контрфорсов.
            st.shield(int(cx), 48, "red", "gold", 1.1)
            st.torch(x0 + 18, 130)
            # Доска объявлений справа: пергаменты с печатями.
            bx = x0 + 298
            st.dark(bx + 3, 93, bx + 45, 151, 1)
            st.bevel(bx, 90, bx + 42, 148, Wd)
            Pl = st.R("plaster")
            for (px, py, pw, ph) in ((bx + 4, 95, 16, 22), (bx + 23, 98, 15, 18), (bx + 6, 121, 30, 22)):
                st.bevel(px, py, px + pw, py + ph, Pl)
                for yy in range(py + 3, py + ph - 3, 3):
                    st.rect(px + 2, yy, px + pw - 2 - (yy * 3) % 5, yy, I[2])
                c.set(px + pw - 3, py + ph - 3, st.R("red")[2])
                c.set(px + pw - 4, py + ph - 3, st.R("red")[2])
                c.set(px + pw // 2, py + 1, I[1])
            st.roses(x0 + 296, WALL_Y - 2, 46, 22)
            st.ivy(x0 + 10, 34, 96, 6)
        elif kind == "chapel":
            st.masonry(x0, 32, x1, WALL_Y, 36, 18, "light", 0.06)
            st.course(x0, x1, 62, 4)
            st.glass(x0 + 32, 84, 40, 96)
            st.glass(x0 + 190, 84, 40, 96)
            st.door(x0 + 108, 104, 46, WALL_Y - 109, pointed=True, ramp="stone")
            # Круглое окно-роза над дверью.
            rc = (x0 + 131, 80)
            st.put(ellipse(rc[0], rc[1], 15, 15), S_, soft=False)
            cols = (st.R("red")[2], Sk[2], G[2], Sk[1])
            for (xx, yy) in ellipse(rc[0], rc[1], 11, 11):
                a = math.atan2(yy - rc[1], xx - rc[0]) * 4 / math.pi
                d = math.hypot(xx - rc[0], yy - rc[1])
                c.set(xx, yy, I[0] if abs(a - round(a)) < 0.14 or abs(d - 5) < 0.6 else cols[int(a + 4) % 4] if d > 5 else G[3])
            st.roses(x0 + 14, WALL_Y - 1, 70, 20)
            st.roses(x0 + 176, WALL_Y - 1, 66, 18)
            st.torch(x0 + 92, 128)
            st.torch(x0 + 170, 128)
        elif kind == "house":
            st.fachwerk(x0, 32, x1, WALL_Y - 34)
            st.masonry(x0, WALL_Y - 33, x1, WALL_Y, 30, 17, "stone", 0.3)
            st.window(x0 + 28, 70, 40, 46)
            st.window(x0 + 116, 70, 40, 46)
            # Дверь с каменным порталом и вывеска с золотым ключом.
            st.door(x0 + 194, 104, 44, WALL_Y - 109, ramp="stone")
            sx = x0 + 198
            st.rect(sx + 4, 58, sx + 36, 59, I[2])
            for xx in (sx + 10, sx + 30):
                st.rect(xx, 60, xx, 64, I[3])
            st.dark(sx + 5, 67, sx + 39, 91, 1)
            st.bevel(sx + 2, 64, sx + 36, 88, Wd)
            ring = ellipse(sx + 10, 76, 5, 5) - ellipse(sx + 10, 76, 2.4, 2.4)
            st.fill(ring, G[2])
            st.rect(sx + 14, 75, sx + 31, 76, G[2])
            st.rect(sx + 14, 75, sx + 31, 75, G[3])
            st.rect(sx + 26, 77, sx + 27, 81, G[2])
            st.rect(sx + 30, 77, sx + 31, 80, G[2])
            # Кованый фонарь у двери.
            st.torch(x0 + 178, 132)
            st.ivy(x0 + 8, 34, 150, 6)
        elif kind == "arch":
            st.masonry(x0, 32, x1, WALL_Y, 34, 20)
            # Арка в стене: за ней небо, холмы, дальняя башня и дорога к ней.
            ax0, ax1 = x0 + 36, x1 - 36
            hole = arch_mask(ax0, ax1, 62, WALL_Y)
            frame = grow(hole, 8) - hole
            st.put(frame, L, soft=False)
            cx, cy = (ax0 + ax1) / 2.0, 62 + (ax1 - ax0) / 2.0
            for (xx, yy) in frame:
                if yy < cy:
                    a = math.atan2(yy - cy, xx - cx) * 9
                    if abs(a - round(a)) < 0.14:
                        c.set(xx, yy, L[1])
                elif (yy - 62) % 18 == 0:
                    c.set(xx, yy, L[1])
            for (xx, yy) in hole:
                k = (yy - 62) / float(WALL_Y - 62)
                hill1 = 168 + math.sin((xx - x0) * 0.045) * 9
                hill2 = 190 + math.sin((xx - x0) * 0.07 + 2.0) * 7
                if yy > hill2:
                    c.set(xx, yy, Gr[2] if (xx * 3 + yy * 5) % 11 else Gr[3])
                elif yy > hill1:
                    c.set(xx, yy, Gr[1] if (xx + yy) % 7 else Gr[2])
                else:
                    c.set(xx, yy, Sk[3] if k > 0.5 or (k > 0.42 and (xx + yy) % 2) else Sk[2] if k > 0.22 or (
                        k > 0.16 and (xx + yy) % 2) else Sk[1])
            # Облако, башня с красной крышей и флажком, дорога.
            for (xx, yy) in ellipse(cx - 18, 108, 12, 4) | ellipse(cx - 10, 104, 8, 4):
                if (xx, yy) in hole:
                    c.set(xx, yy, L[3])
            tx = int(cx) + 14
            tower = set((xx, yy) for xx in range(tx - 6, tx + 7) for yy in range(134, 178))
            for (xx, yy) in tower & hole:
                c.set(xx, yy, L[3] if xx < tx - 3 else L[2] if xx < tx + 4 else L[1])
            for dx in (-7, -2, 3):
                st.rect(tx + dx, 130, tx + dx + 3, 134, L[2])
            st.fill(poly([(tx - 5, 130), (tx + 5, 130), (tx, 114)]) & hole, st.R("red")[2])
            st.rect(tx, 106, tx, 114, I[2])
            st.fill(poly([(tx + 1, 106), (tx + 8, 108), (tx + 1, 111)]), G[2])
            st.rect(tx - 1, 146, tx, 151, I[1])
            st.rect(tx - 1, 162, tx + 1, 177, I[1])
            for yy in range(192, WALL_Y + 1):
                k = (yy - 192) / float(WALL_Y - 192)
                for xx in range(int(cx - 4 - k * 22), int(cx + 6 + k * 26)):
                    if (xx, yy) in hole:
                        c.set(xx, yy, st.R("plaster")[1 if (xx + yy) % 5 else 2])
            # Толща стены: тёмная внутренняя грань арки слева и сверху.
            for (xx, yy) in hole:
                if (xx - 9, yy) not in hole or (xx - 5, yy - 7) not in hole:
                    c.set(xx, yy, S_[1] if (xx - 3, yy - 2) in hole else S_[0])
            st.portcullis(ax0 + 9, ax1, 70, 84)
            st.torch(x0 + 16, 128)
            st.shield(x1 - 17, 120, "gold", "red", 0.9)
            st.ivy(x1 - 8, 34, 180, 6)
        st.dark(x0, 32, x1, 35, 1)
        st.dark(x0, 36, x1, 38, 1, dither=True)
        x += w
    # Цоколь и тень у пола.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Полоса у стены: тёсаные плиты разной ширины рядами, мох и трава в швах.
    Sl = st.R("slab")
    st.rect(0, WALL_Y + 1, SW - 1, CURB_Y - 1, Sl[0])
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        xx = -((ri * 23) % 40)
        while xx < SW:
            w = rng.choice((34, 44, 52, 60)) + ri * 4
            a, b = max(xx + 1, 0), min(xx + w - 1, SW - 1)
            yb = min(y0 + h - 2, CURB_Y - 1)
            if b > a:
                v = rng.random()
                ramp = Sl if v < 0.6 else [Sl[0], Sl[1], Sl[1], Sl[2]] if v < 0.8 else [Sl[1], Sl[2], Sl[3], Sl[3]]
                st.bevel(a, y0, b, yb, ramp)
                st.noise(a + 1, y0 + 1, b - 1, yb - 1, ramp, 0.05)
                if rng.random() < 0.3 and b - a > 20:
                    cx_ = rng.randint(a + 4, b - 12)
                    for k in range(rng.randint(5, 11)):
                        c.set(cx_ + k, y0 + 3 + (k * 5) % (h - 6), ramp[0])
                if rng.random() < 0.4:
                    for k in range(a, b, 2):
                        if rng.random() < 0.5:
                            c.set(k, yb + 1, Gr[1])
                            if rng.random() < 0.4:
                                c.set(k, yb, Gr[2])
            xx += w
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Бордюр: уступ тёсаным светлым камнем, стыки, мох понизу.
    for xx in range(SW):
        c.set(xx, CURB_Y, L[3])
        c.set(xx, CURB_Y + 1, L[2])
        joint = xx % 26 == 0
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, S_[0] if joint else S_[2] if yy < ROAD_Y - 3 else S_[1])
        if xx % 26 == 1:
            for yy in range(CURB_Y + 2, ROAD_Y - 3):
                c.set(xx, yy, S_[3])
        if rng.random() < 0.25:
            c.set(xx, ROAD_Y - 1, Gr[1])
            if rng.random() < 0.4:
                c.set(xx, ROAD_Y - 2, Gr[2])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, I[0])
    # Брусчатка: округлые камни рядами, к зрителю крупнее, тёплые и холодные вперемешку.
    Cb = st.R("cobble")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Cb[0])
    y = ROAD_Y + 2
    h = 9
    row = 0
    while y < SH:
        xx = -rng.randint(0, 10)
        while xx < SW:
            pw = rng.randint(12, 18) + row * 2
            a, b = xx + 1, xx + pw - 1
            yb = min(y + h - 2, SH - 1)
            v = rng.random()
            ramp = Cb if v < 0.5 else [Cb[0], Cb[1], Cb[1], Cb[2]] if v < 0.75 else [Sl[0], Sl[0], Sl[1], Sl[2]] if v < 0.9 \
                else [Cb[1], Cb[2], Cb[3], Cb[3]]
            for yy in range(y, yb + 1):
                for px in range(a, b + 1):
                    corner = (yy in (y, yb)) and (px in (a, b))
                    if corner or not 0 <= px < SW:
                        continue
                    t = 3 if (yy == y or px == a) else 1 if (yy == yb or px == b) else 2
                    if t == 2 and (yy == y + 1 and px < a + pw // 2) and v > 0.3:
                        t = 3
                    c.set(px, yy, ramp[t])
            if rng.random() < 0.4 and pw > 8:
                c.set(min(max(a + rng.randint(3, pw - 4), 0), SW - 1), min(y + rng.randint(2, max(3, h - 4)), SH - 1), ramp[1])
            if rng.random() < 0.07:
                # Травинки в шве.
                for k in range(3):
                    c.set(xx + k * 2, yb + 1, Gr[1])
                c.set(xx + 2, yb, Gr[2])
            xx += pw
        y += h
        h += 2
        row += 1
    # Солома на плитах и брусчатке.
    Hy = st.R("gold")
    for _ in range(150):
        sx, sy = rng.randint(0, SW - 8), rng.randint(WALL_Y + 6, SH - 4)
        if CURB_Y - 2 <= sy <= ROAD_Y + 2:
            continue
        ln, dy = rng.randint(3, 6), rng.choice((-1, 0, 0, 1))
        for k in range(ln):
            c.set(sx + k, sy + (k * dy) // 3, Hy[2 if k % 3 else 3] if rng.random() < 0.8 else Hy[1])
    # Лужи после дождя: в них небо.
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            e = c.get(px, py)
            if e is None:
                continue
            c.set(px, py, Sk[1] if e in (Cb[2], Cb[3], Sl[1], Sl[2]) else Sk[0])
        for k in range(px0 - 30, px0 + 30, 9):
            c.set(k, 369, Sk[3])
            c.set(k + 1, 369, Sk[2])
            c.set(k + 2, 369, Sk[2])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("sack", 20), ("sack", 44), ("box", 290), ("pail", 600), ("pail", 618), ("wheel", 680),
                       ("box", 870), ("box", 898), ("sack", 1150), ("wheel", 1400), ("sack", 1590)):
        yb = WALL_Y + 8
        st.dark(px - 12, yb, px + 22 if kind == "box" else px + 14, yb + 2, 1)
        if kind == "sack":
            st.sack(px, yb)
        elif kind == "pail":
            st.pail(px, yb)
        elif kind == "box":
            st.coffer(px, yb)
        else:
            st.wheel(px, yb)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки это искры стали о сталь: тёплый белый и золото; волна
    багровая, в цвет плаща чёрного рыцаря; пыль дорожная, с соломой; стрелка «вперёд» красная
    с бликом, как вымпел, чтобы не терялась на сером камне."""
    p = Pal(OUTLINE)
    p.add("white", [0xC8BCA0, 0xE8E0C8, 0xFFF8E4, 0xFFFFFF])
    if go:
        p.add("gold", [0x5E1626, 0xB82830, 0xE84434, 0xFFB080])
    else:
        p.add("gold", [0x9C642C, 0xD89A30, 0xF4C84A, 0xFFF4B8])
    p.add("blue", [0x5E1626, 0x942838, 0xD25048, 0xFFC0A8])
    p.add("dust", [0x5C4630, 0x8E7450, 0xBCA47C, 0xE2D4A8])
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
    import castles16
    items = sprites_own()
    root, ext = os.path.splitext(path)
    groups = (("", ("brawl_hero", "brawl_thug", "brawl_knife")),
              ("_b", ("brawl_boss",) + tuple(k for k in items if k.startswith("brawl_face_"))),
              ("_c", tuple(k for k in items if k == "brawl_street" or k.startswith("brawl_fx") or k == "brawl_go")))
    for suffix, keys in groups:
        castles16.save_sheet(root + suffix + ext, {k: items[k] for k in keys}, scale=1, max_w=FW * 12)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
