# -*- coding: utf-8 -*-
"""Набор «Офис» для битемапа × 16/32-bit (#138): зеркало `space_brawl16.py` и `pixel_brawl16.py`.
Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты оттуда как есть (демка
`fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и улица свои.

Бойцы: герой это клерк из `office16.py`: белая рубашка с закатанными рукавами, красный галстук,
очки, голубой бейдж, чуб вперёд; громила это охранник-здоровяк в голубой форменной рубашке, в
фуражке с козырьком и в тёмных очках; враг с ножом это рыжий стажёр в жёлтом худи и наушниках
с красным степлером в руке; босс это директор: лысина с седым венчиком, усы, костюм в полоску,
золотой галстук и кружка «№1» в кулаке. Улица это этаж конторы: окна с городом и жалюзи, кухня
с кулером и автоматом, переговорная за стеклом, перегородки опенспейса, пробковая доска, копир
и лифт, боковой коридор; у стены плитка, дальше порожек и ковролин плитами.

    python3 tools/office_brawl16.py --preview out.png   # лист всех лент
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

# Обводка и опорные цвета из `office16.PALETTE`: рампы ниже растянуты вокруг них на четыре тона.
OUTLINE = 0x14141C
SKIN = [0x7A4A34, 0xC98F5E, 0xF2C89A, 0xFFE4C4]
SHIRT = [0x7A8294, 0xB7BFCF, 0xF4F5F8, 0xFFFFFF]
DARK = [0x14141C, 0x1E2030, 0x2E3140, 0x4A4E62]
GOLD = [0x7A5418, 0xBB843A, 0xF6CD4C, 0xFFF0A0]
RED = [0x6A1418, 0xA02428, 0xDA3A36, 0xF87A6A]
GLASS = [0x314A92, 0x58B2DC, 0xC8EAF5, 0xFFFFFF]


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("skin", SKIN)
    p.add("shirt", SHIRT)
    p.add("pants", [0x141A36, 0x1A2248, 0x314A92, 0x4E6CB8])
    p.add("dark", DARK)
    p.add("red", RED)
    p.add("glass", GLASS)
    p.add("gold", GOLD)
    return Look("clerk", p, Body(1.0, 1.0))


def thug_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x6A3A2A, 0xB07A50, 0xDCAE84, 0xF4D4B0])
    p.add("shirt", [0x2A3E5E, 0x46648C, 0x7098C0, 0xA8C8E4])
    p.add("pants", [0x0E0E16, 0x1A1C28, 0x2A2D3A, 0x444858])
    p.add("dark", DARK)
    p.add("gold", GOLD)
    p.add("glass", GLASS)
    p.add("metal", [0x3A4050, 0x5A6274, 0x7A8294, 0xB7BFCF])
    return Look("guard", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x8A5238, 0xD49A6C, 0xF8D2A8, 0xFFECD2])
    p.add("hoodie", [0x7A5418, 0xBB843A, 0xF0C040, 0xFFE888])
    p.add("pants", [0x3A4050, 0x5A6274, 0x7A8294, 0xA4ACBC])
    p.add("shoe", SHIRT)
    p.add("hair", [0x5A1E0C, 0x963A14, 0xD8621E, 0xF89A48])
    p.add("dark", DARK)
    p.add("red", RED)
    p.add("glass", GLASS)
    p.add("metal", [0x3A4050, 0x6A7284, 0xA4ACBC, 0xE4E8F0])
    return Look("intern", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x7A3E30, 0xC07E5A, 0xEEB48C, 0xFFD8B8])
    p.add("suit", [0x16131E, 0x29253A, 0x403A56, 0x625A7C])
    p.add("shirt", SHIRT)
    p.add("gold", GOLD)
    p.add("grey", [0x4E5464, 0x868E9E, 0xC4CAD6, 0xF0F2F6])
    p.add("dark", DARK)
    p.add("red", RED)
    return Look("boss", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _px(c, q, col, dx=0, dy=0):
    c.set(round(q[0]) + dx, round(q[1]) + dy, col)


def _stapler(c, pal, fist, d):
    """Степлер вдоль предплечья вперёд: стальное основание, красная крышка приоткрыта клювом."""
    n = (d[1], -d[0])
    if n[1] > 0:
        n = (-n[0], -n[1])
    base = capsule(add(add(fist, d, -3.5), n, -1.0), add(add(fist, d, 13.0), n, -1.6), 1.3, 1.1)
    put(c, pal, base, pal["metal"], cast=False)
    top = capsule(add(add(fist, d, -3.5), n, 1.6), add(add(fist, d, 13.0), n, 4.2), 2.5, 2.0)
    put(c, pal, top, pal["red"], cast=False)
    # Шарнир сзади и блик вдоль крышки.
    hinge = add(add(fist, d, -4.0), n, 0.4)
    put(c, pal, ellipse(hinge[0], hinge[1], 2.2, 2.4), pal["dark"], cast=False)
    for k in (4, 6, 8, 10):
        _px(c, add(add(fist, d, k), n, 2.6 + k * 0.2), pal["red"][3])
    _px(c, add(add(fist, d, 12.0), n, -1.6), pal["metal"][3])


def _mug(c, look, j, fist, d):
    """Кружка «№1» над кулаком: белый цилиндр стоит по оси корпуса, ручка в кулаке, красная
    единица на боку, тёмный кофе в горле."""
    pal, s = look.pal, look.body.s
    up, rt = j["up"], j["rt"]
    m = add(add(fist, d, 2.5 * s), up, 6.0 * s)

    def M(r, u):
        return add(add(m, rt, r * s), up, u * s)

    handle = ellipse(*M(-4.2, -0.6), 2.6 * s, 3.0 * s)
    put(c, pal, handle, pal["shirt"], cast=False)
    body = poly([M(-3.8, -4.6), M(3.8, -4.6), M(4.2, 4.4), M(-4.2, 4.4)])
    put(c, pal, body, pal["shirt"], soft=True)
    lip = capsule(M(-3.4, 4.2), M(3.4, 4.2), 1.0, 1.0)
    put(c, pal, lip & body, pal["dark"], cast=False)
    # Единица: палка, флажок и подставка, двойной толщины, чтобы читалась в кадре.
    for u in (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0):
        q = M(0.6, u)
        _px(c, q, pal["red"][2])
        _px(c, q, pal["red"][2], 1, 0)
    _px(c, M(-0.6, 1.2), pal["red"][2])
    _px(c, M(-0.8, -3.0), pal["red"][1])
    _px(c, M(2.0, -3.0), pal["red"][1])


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    upper_ramp = {"clerk": "shirt", "guard": "shirt", "intern": "hoodie", "boss": "suit"}[kind]
    fore_ramp = {"clerk": "skin", "guard": "skin", "intern": "hoodie", "boss": "suit"}[kind]
    fat = 1.1 if kind == "intern" else 1.0
    upper = capsule(sh, el, 4.3 * s * b * fat, 3.5 * s * b * fat) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b * fat,
                                                                           4.5 * s * b * fat)
    if kind == "guard":
        # Бицепс под коротким рукавом.
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.4 * s * b, 3.6 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
    put(c, pal, upper, pal[upper_ramp], far=far, soft=True)
    fore = capsule(el, ha, 3.5 * s * b * fat, 2.9 * s * b * fat)
    put(c, pal, fore, pal[fore_ramp], far=far)
    if kind == "clerk":
        # Закатанный рукав: валик на локте; на ближней руке часы.
        put(c, pal, capsule(add(el, d, -1.6), add(el, d, 1.4), 4.1 * s, 4.0 * s), pal["shirt"], far=far, cast=False)
        cuff = capsule(add(el, d, 1.6), add(el, d, 2.2), 3.9 * s, 3.9 * s) & fore
        recolor(c, cuff, lambda x, y, e: pal["shirt"][1 if not far else 0])
        if not far:
            put(c, pal, capsule(add(ha, d, -4.0 * s), add(ha, d, -3.2 * s), 3.2 * s, 3.2 * s), pal["dark"], cast=False)
            _px(c, add(ha, d, -3.6 * s), pal["glass"][2])
    elif kind == "guard":
        # Рукав кончается над локтем кантом, на плече нашивка, на запястье чёрная перчатка с крагой.
        hem = capsule(lerp(sh, el, 0.72), el, 4.0 * s * b, 3.7 * s * b)
        put(c, pal, hem, pal["skin"], far=far, cast=False)
        edge = capsule(lerp(sh, el, 0.66), lerp(sh, el, 0.7), 4.3 * s * b, 4.3 * s * b) & upper
        recolor(c, edge, lambda x, y, e: pal["shirt"][0])
        put(c, pal, capsule(add(ha, d, -6.0 * s), add(ha, d, -2.6 * s), 3.9 * s * b, 3.6 * s * b), pal["dark"], far=far)
        if not far:
            q = lerp(sh, el, 0.3)
            put(c, pal, ellipse(q[0], q[1], 2.8 * s, 2.6 * s), pal["gold"], cast=False)
            _px(c, q, pal["dark"][1])
    elif kind == "intern":
        # Резинка рукава худи.
        put(c, pal, capsule(add(ha, d, -4.4 * s), add(ha, d, -2.6 * s), 3.6 * s * b, 3.4 * s * b),
            [pal["hoodie"][0], pal["hoodie"][0], pal["hoodie"][1], pal["hoodie"][2]], far=far, cast=False)
    elif kind == "boss":
        # Белая манжета с золотой запонкой, пуговицы на рукаве.
        put(c, pal, capsule(add(ha, d, -4.6 * s), add(ha, d, -2.4 * s), 3.9 * s * b, 3.8 * s * b), pal["shirt"], far=far)
        if not far:
            _px(c, add(ha, d, -3.6 * s), pal["gold"][2])
            _px(c, add(ha, d, -7.0 * s), pal["suit"][3])
            _px(c, add(ha, d, -9.4 * s), pal["suit"][3])
    fist = add(ha, d, 1.2 * s)
    fr = min(b, 1.15) * (1.15 if kind == "guard" else 1.0)
    fs = ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr)
    if kind == "intern" and side == "n":
        _stapler(c, pal, fist, d)
    if kind == "boss" and side == "n":
        _mug(c, look, j, fist, d)
    put(c, pal, fs, pal["dark"] if kind == "guard" else pal["skin"], far=far)


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    pants = "suit" if kind == "boss" else "pants"
    boots = "shoe" if kind == "intern" else "dark"
    thigh = capsule(hp, kn, 6.0 * s * b, 4.8 * s * b)
    put(c, pal, thigh, pal[pants], far=far, soft=True)
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    top_h = (7 if kind == "guard" else 4 if kind == "intern" else 3) * s
    boot = capsule(add(an, sd, -top_h), an, 4.4 * s * b, 4.1 * s * b)
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
    shin = capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b, 4.2 * s * b)
    put(c, pal, boot | foot, pal[boots], far=far)
    put(c, pal, shin, pal[pants], far=far)
    if kind == "clerk" or kind == "boss":
        # Стрелка на брюках: светлая нитка спереди по бедру и голени; блик на носке ботинка.
        if not far:
            hi = pal[pants][3]
            for a, e, r in ((hp, kn, 3.2), (kn, an, 2.4)):
                for k in range(3, 14):
                    q = add(lerp(a, e, k / 16.0), fwd, r * s * b)
                    if c.get(round(q[0]), round(q[1])) == pal[pants][2]:
                        _px(c, q, hi)
            q = add(add(an, sd, 1.6 * s), fwd, 6.0 * s)
            _px(c, q, pal["dark"][3])
            _px(c, q, pal["dark"][3], -1, 0)
    elif kind == "guard":
        # Берцы: шнуровка светлыми точками, клапан кармана на бедре.
        if not far:
            for k in (1.5, 3.5, 5.5):
                _px(c, add(add(an, sd, -k * s), fwd, 2.6 * s), pal["metal"][2])
            q = add(lerp(hp, kn, 0.55), fwd, -1.0)
            put(c, pal, capsule(q, add(q, sd, 4.0 * s), 3.2 * s, 3.0 * s), pal["pants"], cast=False)
            _px(c, add(q, sd, 0.5), pal["pants"][3])
    elif kind == "intern":
        # Подворот джинсов и красная полоска на кеде.
        roll = capsule(add(an, sd, -top_h - 1.4), add(an, sd, -top_h + 0.6), 4.7 * s * b, 4.7 * s * b)
        put(c, pal, roll, [pal["pants"][1], pal["pants"][2], pal["pants"][3], pal["pants"][3]], far=far, cast=False)
        if not far:
            for k in (2.0, 3.0, 4.0):
                _px(c, add(add(an, sd, 1.4 * s), fwd, k * s), pal["red"][2])
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    recolor(c, sole, lambda x, y, e: pal["dark"][0] if kind != "intern" else pal["red"][1])


def _hood(c, look, j):
    """Капюшон худи за шеей, рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, up, rt = j["neck"], j["up"], j["rt"]
    q = add(add(N, rt, -7.0 * s * b), up, -1.5 * s)
    hood = ellipse(q[0], q[1], 6.4 * s, 5.4 * s, math.degrees(math.atan2(rt[1], rt[0])) + 30)
    put(c, pal, hood, pal["hoodie"], soft=True)


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    pants = "suit" if kind == "boss" else "pants"
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[pants], soft=True)
    belly = 2.2 if kind == "boss" else (0.8 if kind == "guard" else 0.0)
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "boss":
        tor |= ellipse(*P(lerp(N, H, 0.64), 4.4, 0), 7.8 * s * b, 7.2 * s)
    if kind == "intern":
        # Худи навыпуск: подол закрывает пояс.
        tor |= poly([P(H, 7.2, 4), P(H, 7.4, -2.5), P(H, -7.4, -2.5), P(H, -7.0, 4)])

    def mat(x, y):
        lx = ((x - N[0]) * rt[0] + (y - N[1]) * rt[1]) / (s * b)
        ly = -((x - N[0]) * up[0] + (y - N[1]) * up[1]) / s
        if kind == "clerk" or kind == "guard":
            return pal["shirt"]
        if kind == "intern":
            return pal["hoodie"]
        # Директор: белая манишка клином от ворота, остальное пиджак.
        if lx > 1.6 + ly * 0.22 and lx < 7.6 and ly < 17:
            return pal["shirt"]
        return pal["suit"]

    put(c, pal, tor, None, soft=True, mat=mat)
    if kind != "intern":
        # Пояс с пряжкой.
        belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
        put(c, pal, belt & (tor | pelvis), pal["dark"], cast=False)
        bk = P(H, 4.6, 4.1)
        put(c, pal, ellipse(bk[0], bk[1], 1.8 * s, 1.6 * s), pal["gold"], cast=False)
    if kind == "clerk":
        # Воротник, планка с пуговицами, нагрудный карман с ручкой и бейдж на клипсе.
        col = poly([P(N, 2.0, 2.2), P(N, 7.2, 0.4), P(N, 5.6, -3.6), P(N, 2.6, -2.0)])
        put(c, pal, col & tor, [SHIRT_I(pal, 0), SHIRT_I(pal, 1), SHIRT_I(pal, 3), SHIRT_I(pal, 3)], cast=False)
        bq = P(lerp(N, H, 0.44), -0.6, 0)
        bx, by = round(bq[0]), round(bq[1])
        g = pal["glass"]
        for dy in range(5):
            for dx in range(4):
                if (bx + dx, by + dy) in tor:
                    c.set(bx + dx, by + dy, g[1] if dy > 1 else g[2])
        c.set(bx + 1, by + 3, pal["shirt"][3])
        c.set(bx + 2, by + 3, pal["shirt"][3])
        c.set(bx + 1, by - 1, pal["dark"][2])
        c.set(bx + 2, by - 1, pal["dark"][2])
        # Галстук: узел у ворота, полотно висит между осью корпуса и отвесом, в ударе отлетает.
        knot = P(N, 5.4, -2.6)
        down = (-up[0] * 0.55, -up[1] * 0.55 + 0.45)
        n = math.hypot(*down) or 1.0
        down = (down[0] / n + rt[0] * 0.14, down[1] / n + rt[1] * 0.14)
        w = p.get("wave", 0.0)
        mid = add(add(knot, down, 9.0 * s), rt, 0.6 * s)
        end = add(add(knot, down, 17.0 * s), rt, (1.0 + w * 0.5) * s)
        tie = capsule(knot, mid, 1.5 * s, 2.3 * s) | capsule(mid, end, 2.3 * s, 0.7 * s)
        put(c, pal, tie, pal["red"])
        put(c, pal, ellipse(knot[0], knot[1], 2.0 * s, 1.8 * s), [pal["red"][0], pal["red"][1], pal["red"][1],
                                                                 pal["red"][2]], cast=False)
    elif kind == "guard":
        # Карманы с клапанами, золотой жетон, рация на плече с антенной, погон.
        for r0 in (1.2, -5.6):
            a = P(lerp(N, H, 0.34), r0, 0)
            e = P(lerp(N, H, 0.56), r0 + 4.4, 0)
            pk = poly([a, (e[0], a[1]), e, (a[0], e[1])]) & tor
            recolor(c, {q for q in pk if (q[0], q[1] - 1) not in pk or (q[0] - 1, q[1]) not in pk},
                    lambda x, y, e_: pal["shirt"][1])
        q = P(lerp(N, H, 0.26), 4.4, 0)
        put(c, pal, ellipse(q[0], q[1], 2.2 * s, 2.5 * s), pal["gold"], cast=False)
        _px(c, q, pal["gold"][3])
        r0 = P(N, -4.6, -4.0)
        radio = poly([r0, add(r0, rt, 4.2 * s), add(add(r0, rt, 4.2 * s), up, -6.6 * s), add(r0, up, -6.6 * s)])
        put(c, pal, radio, pal["dark"], cast=False)
        _px(c, add(add(r0, rt, 1.2 * s), up, -2.0 * s), pal["glass"][1])
        ant = capsule(add(r0, rt, 0.8 * s), add(add(r0, rt, 0.4 * s), up, 6.0 * s), 0.6, 0.5)
        put(c, pal, ant, pal["dark"], cast=False)
        # Тёмный форменный галстук-регат по планке.
        for k in range(8):
            q = P(lerp(N, H, 0.04 + k * 0.07), 6.4 + k * 0.1, 0)
            if (round(q[0]), round(q[1])) in tor:
                _px(c, q, pal["dark"][2])
                _px(c, q, pal["dark"][1], -1, 0)
    elif kind == "intern":
        # Карман-кенгуру, шнурки капюшона, красная лента с бейджем.
        a = P(lerp(N, H, 0.66), 0.5, 0)
        e = P(lerp(N, H, 0.96), 7.2, 0)
        pocket = poly([a, P(lerp(N, H, 0.7), 7.0, 0), e, P(lerp(N, H, 0.96), -1.0, 0)]) & tor
        edge = {q for q in pocket if (q[0], q[1] - 1) not in pocket or (q[0] - 1, q[1]) not in pocket}
        recolor(c, edge, lambda x, y, e_: pal["hoodie"][1])
        for k in range(7):
            q = P(lerp(N, H, 0.06 + k * 0.06), 4.2 + k * 0.5, 0)
            if (round(q[0]), round(q[1])) in tor:
                _px(c, q, pal["red"][2])
        bq = P(lerp(N, H, 0.48), 5.6, 0)
        bx, by = round(bq[0]), round(bq[1])
        for dy in range(4):
            for dx in range(3):
                if (bx + dx, by + dy) in tor:
                    c.set(bx + dx, by + dy, pal["glass"][2] if dy < 1 else pal["glass"][1])
        for r0 in (1.6, 3.0):
            for k in range(5):
                q = P(lerp(N, H, 0.12 + k * 0.05), r0, 0)
                if (round(q[0]), round(q[1])) in tor and k % 2 == 0:
                    _px(c, q, pal["shoe"][2])
    elif kind == "boss":
        # Тонкая полоска костюма, лацкан, золотой галстук по манишке, платок в кармане.
        su = pal["suit"]
        for (x, y) in tor:
            lx = ((x - N[0]) * rt[0] + (y - N[1]) * rt[1]) / (s * b)
            if c.get(x, y) == su[2] and int(math.floor(lx * b * s)) % 4 == 0:
                c.set(x, y, su[3] if (x + y) % 2 else su[2])
        for k in range(12):
            t = k / 11.0
            q = P(lerp(N, H, 0.02 + t * 0.52), 1.4 + t * 3.6, 0)
            _px(c, q, su[0])
            _px(c, q, su[3], -1, 0)
        knot = P(N, 5.4, -2.6)
        end = P(lerp(N, H, 0.6), 7.2, 0)
        mid = lerp(knot, end, 0.55)
        tie = capsule(knot, mid, 1.4 * s, 2.3 * s) | capsule(mid, end, 2.3 * s, 0.8 * s)
        put(c, pal, tie & tor, pal["gold"], cast=False)
        for k in range(1, 6):
            q = lerp(knot, end, k / 6.5)
            if (round(q[0]), round(q[1])) in tie:
                _px(c, q, pal["gold"][1], -1 if k % 2 else 0, 0)
        q = P(lerp(N, H, 0.34), -3.0, 0)
        hk = poly([q, add(q, rt, 3.6 * s), add(add(q, rt, 2.0 * s), up, 2.6 * s)])
        put(c, pal, hk, pal["gold"], cast=False)
        for k in range(2):
            q = P(lerp(N, H, 0.7 + k * 0.12), 6.6, 0)
            if (round(q[0]), round(q[1])) in tor:
                _px(c, q, pal["gold"][2])


def SHIRT_I(pal, i):
    return pal["shirt"][i]


def _tails(c, look, j, p):
    """Полы пиджака директора: короткий подол с разрезом, качается с шагом."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = 15 * s
    sway = -p["lean"] * 0.18 - (p["th_n"] + p["th_f"]) * 0.04
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 7.6 * s * b), up, 3 * s),
           (H[0] + 7.4 * s * b + sway * 0.3, H[1] + ln * 0.8), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - 10.5 * s * b + sway, H[1] + ln * 0.92)]
    S = poly(pts)
    put(c, pal, S, pal["suit"], soft=True)
    su = pal["suit"]
    for (x, y) in S:
        if c.get(x, y) == su[2] and (x - round(H[0])) % 4 == 0 and (x + y) % 2:
            c.set(x, y, su[3])


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

    sk = pal["skin"]
    thick = {"clerk": 3.3, "guard": 4.6, "intern": 2.9, "boss": 4.4}[kind]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), thick * s, (thick - 0.2) * s)
    put(c, pal, neck, sk)
    if kind == "guard":
        skull = ellipse(*H(-0.4, -0.6), 7.8 * s, 7.8 * s, ang)
        jaw = poly([H(-4.4, 2), H(6.6, 1.5), H(7.4, 5.4), H(5.0, 9.4), H(-3.6, 9.0)])
    elif kind == "intern":
        skull = ellipse(*H(0, -0.8), 6.6 * s, 7.4 * s, ang)
        jaw = poly([H(-2.6, 2), H(5.8, 1.5), H(6.0, 4.6), H(3.2, 8.0), H(-2.0, 7.2)])
    elif kind == "boss":
        skull = ellipse(*H(-0.2, -0.8), 7.4 * s, 7.8 * s, ang)
        jaw = poly([H(-4.4, 2), H(6.4, 1.5), H(7.0, 5.6), H(4.6, 9.6), H(-4.4, 9.8)])
    else:
        skull = ellipse(*H(0, -0.5), 7.0 * s, 7.6 * s, ang)
        jaw = poly([H(-3, 2), H(6.2, 1.5), H(6.5, 5), H(3.6, 8.6), H(-2.5, 8)])
    nose = poly([H(5.5, -1.5), H(8.4 if kind != "boss" else 9.0, 2.2), H(5.6, 3.2)])
    face = skull | jaw | nose
    put(c, pal, face, sk, soft=True)
    # Ухо.
    ex, ey = H(-1.2, 1.2)
    put(c, pal, ellipse(ex, ey, 1.6 * s, 2.0 * s), [sk[0], sk[1], sk[2], sk[2]], cast=False)
    c.set(round(ex), round(ey), sk[0])
    brow = pal["dark"][0]
    if kind == "clerk":
        # Тёмные волосы шапкой, виски и затылок; чуб торчит вперёд надо лбом и качается.
        hair = {q for q in skull if local(*q)[1] < -3.2 or (local(*q)[0] < -3.0 and local(*q)[1] < 2.6)}
        put(c, pal, hair, pal["dark"], soft=True, cast=False)
        tuft = capsule(H(-1.0, -7.4), H(7.4, -8.0 - wave * 0.5), 2.6 * s, 1.5 * s)
        put(c, pal, tuft, pal["dark"], soft=True)
        _px(c, H(2.0, -8.6), pal["dark"][3])
        _px(c, H(3.2, -8.8), pal["dark"][3])
    elif kind == "guard":
        # Фуражка: тулья, околыш, козырёк вперёд, кокарда; под ней стриженый затылок.
        nape = {q for q in skull if local(*q)[0] < -3.4 and -4.0 <= local(*q)[1] < 3.0}
        put(c, pal, nape, pal["dark"], cast=False)
        crown = poly([H(-8.6, -4.0), H(8.2, -4.6), H(9.2, -9.6), H(2.0, -12.0), H(-8.8, -10.2)])
        put(c, pal, crown, pal["dark"], soft=True)
        band = poly([H(-8.6, -3.6), H(8.4, -4.2), H(8.4, -6.2), H(-8.6, -5.6)])
        put(c, pal, band, [pal["dark"][0], pal["dark"][0], pal["dark"][1], pal["dark"][2]], cast=False)
        visor = capsule(H(6.0, -3.8), H(13.0, -2.6), 1.6 * s, 1.1 * s)
        put(c, pal, visor, pal["dark"])
        q = H(6.2, -7.4)
        put(c, pal, ellipse(q[0], q[1], 2.0 * s, 2.2 * s), pal["gold"], cast=False)
        # Щетина на челюсти.
        for q in jaw:
            lx, ly = local(*q)
            if ly > 3.4 and (q[0] + q[1]) % 2 == 0 and c.get(*q) in (sk[2], sk[3]):
                c.set(q[0], q[1], sk[1])
        # Витой провод наушника от уха за ворот.
        for k in range(6):
            q = H(-2.2 - (k % 2) * 1.0, 3.4 + k * 1.2)
            _px(c, q, pal["glass"][2])
    elif kind == "intern":
        # Рыжие вихры: шапка волос и три пряди торчком; наушники: дуга через темя и чашка на ухе.
        hair = {q for q in skull if local(*q)[1] < -3.0 or (local(*q)[0] < -3.4 and local(*q)[1] < 1.0)}
        put(c, pal, hair, pal["hair"], soft=True, cast=False)
        for k, (bx, tx, ty) in enumerate(((-5.0, -7.4, -11.0), (-0.8, -1.2, -12.6), (3.2, 5.8, -11.0))):
            spike = poly([H(bx - 2.2, -6.0), H(tx - wave * 0.4, ty), H(bx + 2.6, -6.4)])
            put(c, pal, spike, pal["hair"], cast=False)
        fringe = capsule(H(3.0, -5.4), H(7.0, -4.0), 1.8 * s, 1.0 * s)
        put(c, pal, fringe, pal["hair"], cast=False)
        band = capsule(H(-1.6, -1.0), H(-0.6, -9.4), 1.2 * s, 1.2 * s)
        put(c, pal, band, pal["dark"], cast=False)
        q = H(-1.4, 0.8)
        put(c, pal, ellipse(q[0], q[1], 3.3 * s, 3.8 * s), pal["dark"])
        put(c, pal, ellipse(q[0], q[1], 1.5 * s, 2.0 * s), pal["red"], cast=False)
        # Веснушки.
        _px(c, H(2.6, 2.0), sk[1])
        _px(c, H(4.4, 2.6), sk[1])
        brow = pal["hair"][0]
    else:
        # Лысина с бликом, седой венчик от виска к затылку, двойной подбородок.
        ring = {q for q in skull if local(*q)[0] < -1.8 and -2.6 <= local(*q)[1] < 4.6}
        put(c, pal, ring, pal["grey"], soft=True, cast=False)
        for dx in (-2.0, -1.0, 0.0):
            _px(c, H(dx, -6.6), sk[3])
        chin = capsule(H(0.0, 8.6), H(4.6, 7.6), 1.0, 1.0)
        recolor(c, chin & face, lambda x, y, e: sk[1])
        brow = pal["grey"][1]
    # Глаз и бровь; при ударе глаз зажмурен, рот открыт.
    ex, ey = H(3.2, -1.2)
    ex, ey = round(ex), round(ey)
    if kind == "guard":
        # Тёмные очки: планка от переносицы к уху, блик на стекле; от удара съезжают набок.
        a, e = (H(2.0, -1.6), H(7.4, -1.2)) if not hurt else (H(1.6, 0.2), H(7.2, -2.6))
        lens = capsule(a, e, 2.0 * s, 1.8 * s) & face
        put(c, pal, lens, [pal["dark"][0], pal["dark"][0], pal["dark"][1], pal["dark"][2]], cast=False)
        for k in range(1, 6):
            _px(c, lerp(a, H(-1.6, -0.6), k / 5.0), pal["dark"][0])
        if not hurt:
            _px(c, lerp(a, e, 0.45), pal["glass"][1], 0, -1)
            _px(c, lerp(a, e, 0.62), pal["glass"][2], 0, -1)
    elif hurt:
        c.set(ex, ey, sk[0])
        c.set(ex + 1, ey, sk[0])
        c.set(ex - 1, ey - 1, sk[0])
        c.set(ex + 2, ey - 1, sk[0])
    else:
        c.set(ex, ey, pal["shirt"][2] if "shirt" in pal.ramp else pal["shoe"][2])
        c.set(ex + 1, ey, 0)
        c.set(ex + 1, ey - 1, 0)
        if kind == "intern":
            # Круглый удивлённый глаз.
            c.set(ex, ey - 1, pal["shoe"][3])
            c.set(ex, ey + 1, pal["shoe"][2])
        for k in range(-1, 3):
            c.set(ex + k, ey - (3 if kind == "intern" else 2) - (1 if kind == "boss" and k < 1 else 0), brow)
        if kind == "boss":
            c.set(ex + 2, ey - 3, brow)
            c.set(ex + 3, ey - 2, brow)
    if kind == "clerk":
        # Очки: тёмная оправа прямоугольником, стекло с бликом, дужка к уху. От удара взлетают на лоб.
        o = -4.2 if hurt else 0.0
        t = 0.9 if hurt else 0.0
        g = pal["glass"]
        fr = poly([H(1.0, -3.6 + o - t), H(6.6, -3.6 + o + t), H(6.6, 1.4 + o + t), H(1.0, 1.4 + o - t)])
        inner = poly([H(2.0, -2.6 + o - t), H(5.6, -2.6 + o + t), H(5.6, 0.4 + o + t), H(2.0, 0.4 + o - t)])
        for q in fr - inner:
            c.set(q[0], q[1], pal["dark"][1])
        for q in inner:
            e = c.get(*q)
            if hurt:
                c.set(q[0], q[1], g[2])
            elif e in (sk[1], sk[2], sk[3]):
                c.set(q[0], q[1], g[2] if local(*q)[1] < -1.6 else e)
        _px(c, H(2.4, -2.4 + o), g[3])
        for k in range(1, 5):
            _px(c, lerp(H(1.0, -1.6 + o), H(-1.4, -0.4 + o * 0.5), k / 4.0), pal["dark"][1])
    mx, my = H(4.0, 5.2)
    mx, my = round(mx), round(my)
    if kind == "boss":
        # Седые усы щёткой под носом закрывают рот.
        mu = capsule(H(3.6, 3.8), H(8.2, 4.8), 1.7 * s, 1.3 * s)
        put(c, pal, mu, pal["grey"], cast=False)
        if hurt:
            c.set(mx + 1, my + 3, sk[0])
            c.set(mx + 2, my + 3, sk[0])
    else:
        c.set(mx, my, sk[0])
        c.set(mx + 1, my, sk[0])
        if kind == "guard":
            # Сжатый рот уголком вниз.
            c.set(mx + 2, my, sk[0])
            c.set(mx - 1, my + 1, sk[0])
        if hurt:
            c.set(mx, my + 1, sk[0])
            c.set(mx + 1, my + 1, 0)


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if kind == "intern":
        _hood(c, look, j)
    if kind == "boss":
        _tails(c, look, j, p)
    _torso(c, look, j, p)
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
                                       ("thug", thug_look(), pb.foe_frames()[0], FW, FH, 17),
                                       ("knife", knife_look(), pb.foe_frames(knife=True)[0], FW, FH, 17),
                                       ("boss", boss_look(), pb.foe_frames(boss=True)[0], BW, BH, 14)):
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


# --- Этаж конторы ---------------------------------------------------------------------------------

def street_pal():
    p = Pal(0x10101A)
    p.add("wall", [0x6A7080, 0x8E96A6, 0xB4BCCA, 0xD4DAE4])
    p.add("white", [0x7A8294, 0xA4ACBC, 0xD6DAE4, 0xF4F5F8])
    p.add("dark", [0x14141C, 0x22242E, 0x2E3140, 0x4A4E62])
    p.add("metal", [0x3A4050, 0x5A6274, 0x7A8294, 0xA4ACBC])
    p.add("blue", [0x141A36, 0x1A2248, 0x314A92, 0x4E6CB8])
    p.add("sky", [0x3E6AA8, 0x58B2DC, 0x9AD4EC, 0xC8EAF5])
    p.add("lamp", [0x9AA8B8, 0xC8EAF5, 0xEAF8FC, 0xFFFFFF])
    p.add("gold", [0x7A5418, 0xBB843A, 0xF6CD4C, 0xFFF0A0])
    p.add("red", [0x6A1418, 0xA02428, 0xDA3A36, 0xF87A6A])
    p.add("wood", [0x4A2E1C, 0x7A5030, 0xA8743E, 0xD09A5A])
    p.add("card", [0x5A3C1C, 0x8A6030, 0xBB843A, 0xDCAE68])
    p.add("carpet", [0x163A3A, 0x2A605C, 0x3C7E70, 0x4F9C86])
    p.add("tile", [0x565E70, 0x7A8294, 0x9EA6B6, 0xC0C6D2])
    p.add("green", [0x12362A, 0x1E5A40, 0x3A8A56, 0x74BE6E])
    p.add("pink", [0x7A2A56, 0xC0508A, 0xF07AB0, 0xFFC0DC])
    return p


class Floor(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(138)

    def paint(self, x0, x1, ramp="wall", rail=178):
        """Крашеная стена: ровный тон с редкой крапиной, ниже рейки панели с пазами."""
        R_, Wh = self.R(ramp), self.R("white")
        self.rect(x0, 32, x1, WALL_Y, R_[2])
        self.noise(x0, 32, x1, rail - 1, R_, 0.012)
        self.rect(x0, rail + 4, x1, WALL_Y, R_[1])
        for xx in range(x0 + 20, x1, 44):
            self.rect(xx, rail + 8, xx, WALL_Y - 12, R_[0])
            self.rect(xx + 1, rail + 8, xx + 1, WALL_Y - 12, R_[2])
        self.bevel(x0, rail, x1, rail + 3, Wh)
        self.dark(x0, rail + 4, x1, rail + 5, 1)

    def fabric(self, x0, y0, x1, y1, pw=58):
        """Перегородки опенспейса: синяя ткань в рамах, по верху алюминиевый профиль."""
        B, M = self.R("blue"), self.R("metal")
        self.rect(x0, y0, x1, y1, B[2])
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                if (xx + yy * 3) % 4 == 0:
                    self.c.set(xx, yy, B[1] if (xx // 2 + yy) % 3 else B[3])
        x = x0
        while x <= x1:
            self.rect(x, y0, min(x + 2, x1), y1, M[2])
            self.rect(x, y0, x, y1, M[3])
            self.dark(min(x + 3, x1), y0, min(x + 4, x1), y1, 1)
            x += pw
        self.bevel(x0, y0 - 4, x1, y0, M)
        self.dark(x0, y0 + 1, x1, y0 + 3, 1)

    def sticker(self, x, y, ramp="gold", w=7, text=True):
        """Стикер: квадратик с загнутым уголком и строчками."""
        R_ = self.R(ramp)
        self.rect(x + 1, y + 1, x + w, y + w, self.R("dark")[1])
        self.rect(x, y, x + w - 1, y + w - 1, R_[2])
        self.rect(x, y, x + w - 1, y, R_[3])
        self.c.set(x + w - 1, y + w - 1, R_[1])
        self.c.set(x + w - 2, y + w - 1, R_[1])
        if text:
            for yy in range(y + 2, y + w - 2, 2):
                self.rect(x + 1, yy, x + w - 3 - (yy % 3), yy, R_[1])

    def window(self, x, y, w, h, blinds=0.3):
        """Окно с городом: белая рама, небо, два ряда домов с огнями окон, жалюзи сверху, подоконник."""
        Wh, S_, B, M, G = self.R("white"), self.R("sky"), self.R("blue"), self.R("metal"), self.R("gold")
        r = self.rng
        self.bevel(x - 6, y - 6, x + w + 6, y + h + 6, Wh)
        for yy in range(y, y + h + 1):
            k = (yy - y) / float(h)
            for xx in range(x, x + w + 1):
                self.c.set(xx, yy, S_[2] if k < 0.3 or (k < 0.5 and (xx + yy) % 2) else S_[3])
        # Дальний ряд домов светлее, ближний темнее.
        for layer, (lo, hi, col, lit) in enumerate(((0.3, 0.62, S_[1], S_[3]), (0.12, 0.45, B[2], G[2]))):
            xx = x - r.randint(0, 6)
            while xx <= x + w:
                bw = r.randint(9, 20)
                bh = int(h * r.uniform(lo, hi))
                a, b = max(xx, x), min(xx + bw - 1, x + w)
                if b >= a:
                    self.rect(a, y + h - bh, b, y + h, col)
                    if layer:
                        self.rect(b, y + h - bh, b, y + h, B[1])
                        if r.random() < 0.4 and b - a > 6:
                            self.rect(a + 3, y + h - bh - 5, a + 4, y + h - bh, B[1])
                    for wy in range(y + h - bh + 3, y + h - 1, 4):
                        for wx in range(a + 2, b - 1, 3):
                            if r.random() < (0.45 if layer else 0.25):
                                self.c.set(wx, wy, lit)
                                if layer:
                                    self.c.set(wx, wy + 1, S_[1])
                xx += bw + r.randint(0, 3)
        # Блики стекла наискось.
        for k in range(0, h, 2):
            for off in (int(w * 0.2), int(w * 0.2) + 5, int(w * 0.62)):
                xx, yy = x + off + k // 2, y + h - k
                if x <= xx <= x + w and self.c.get(xx, yy) in (S_[2], S_[3]):
                    self.c.set(xx, yy, self.R("lamp")[3])
        # Переплёт.
        mid = x + w // 2
        self.rect(mid - 1, y, mid + 1, y + h, Wh[2])
        self.rect(mid - 1, y, mid - 1, y + h, Wh[3])
        self.rect(mid + 1, y, mid + 1, y + h, Wh[1])
        # Жалюзи: ламели через строку, шнур сбоку.
        bh = int(h * blinds)
        for yy in range(y, y + bh + 1):
            ph = (yy - y) % 4
            self.rect(x, yy, x + w, yy, Wh[3] if ph == 0 else Wh[2] if ph == 1 else Wh[1] if ph == 2 else Wh[0])
        self.rect(x, y + bh + 1, x + w, y + bh + 2, Wh[1])
        self.rect(x + w - 4, y + bh + 2, x + w - 4, y + int(h * 0.78), Wh[1])
        self.rect(x + w - 5, y + int(h * 0.78), x + w - 3, y + int(h * 0.78) + 3, Wh[3])
        self.dark(x, y + bh + 3, x + w, y + bh + 4, 1)
        self.dark(x, y, x + 2, y + h, 1, dither=True)
        # Подоконник и тень под ним.
        self.bevel(x - 10, y + h + 7, x + w + 10, y + h + 10, Wh)
        self.dark(x - 8, y + h + 11, x + w + 12, y + h + 13, 1)

    def radiator(self, x, y, w, h):
        Wh = self.R("white")
        self.rect(x, y, x + w, y + h, Wh[1])
        for xx in range(x, x + w - 2, 6):
            self.rect(xx, y, xx + 3, y + h, Wh[2])
            self.rect(xx, y, xx, y + h, Wh[3])
            self.rect(xx + 4, y, xx + 4, y + h, Wh[0])
        self.rect(x, y, x + w, y, Wh[3])
        self.rect(x, y + h, x + w, y + h, Wh[0])
        self.dark(x + 2, y + h + 1, x + w + 2, y + h + 2, 1)

    def lift(self, x, y, w, h):
        """Лифт: стальная рама, две створки со швом, табло этажа со стрелкой, кнопка вызова."""
        M, D, Wh, Rd = self.R("metal"), self.R("dark"), self.R("white"), self.R("red")
        self.bevel(x - 8, y - 16, x + w + 8, y + h, M)
        self.rect(x, y, x + w, y + h, M[1])
        mid = x + w // 2
        for (a, b) in ((x + 1, mid - 1), (mid + 1, x + w - 1)):
            self.bevel(a, y + 1, b, y + h - 1, [M[1], M[2], M[3], Wh[3]])
            for xx in range(a + 3, b - 1, 3):
                self.rect(xx, y + 4, xx, y + h - 4, Wh[2] if (xx - a) % 6 else M[3])
            self.bevel(a + 3, y + h - 22, b - 3, y + h - 6, M, inset=True)
        self.rect(mid, y, mid, y + h, D[0])
        self.dark(x, y, x + w, y + 4, 1)
        self.dark(x, y + 5, x + w, y + 8, 1, dither=True)
        # Табло: чёрное окно, красная цифра и стрелка вверх.
        self.rect(mid - 11, y - 13, mid + 11, y - 4, D[0])
        for (dx, dy) in ((-7, -6), (-6, -7), (-5, -8), (-4, -7), (-3, -6), (-5, -7), (-5, -6), (-5, -5)):
            self.c.set(mid + dx, y - 3 + dy, Rd[3])
        for dy in range(6):
            self.c.set(mid + 4, y - 11 + dy, Rd[2])
            self.c.set(mid + 5, y - 11 + dy, Rd[3])
        self.c.set(mid + 3, y - 10, Rd[2])
        self.rect(mid + 2, y - 5, mid + 7, y - 5, Rd[2])
        # Кнопка вызова справа от рамы.
        self.bevel(x + w + 12, y + h // 2 - 8, x + w + 19, y + h // 2 + 6, M)
        self.c.set(x + w + 15, y + h // 2 - 4, self.R("gold")[3])
        self.c.set(x + w + 16, y + h // 2 - 4, self.R("gold")[2])
        self.rect(x + w + 15, y + h // 2 + 1, x + w + 16, y + h // 2 + 2, D[1])
        # Порог.
        self.bevel(x - 10, y + h + 1, x + w + 10, y + h + 5, M)

    def door(self, x, y, w, h, color="wood", glass=True, plate="gold"):
        """Дверь кабинета: белый наличник, полотно с филёнками, матовое окно, ручка, табличка."""
        Wh, W_, M, S_ = self.R("white"), self.R(color), self.R("metal"), self.R("sky")
        self.bevel(x - 6, y - 6, x + w + 6, y + h, Wh)
        self.bevel(x, y, x + w, y + h, W_)
        for xx in range(x + 2, x + w - 1, 5):
            self.rect(xx, y + 2, xx, y + h - 2, W_[1] if (xx // 5) % 2 else W_[3])
        self.bevel(x + 5, y + int(h * 0.58), x + w - 5, y + h - 8, W_, inset=True)
        if glass:
            self.bevel(x + 5, y + 8, x + w - 5, y + int(h * 0.44), W_, inset=True)
            for yy in range(y + 10, y + int(h * 0.44) - 1):
                for xx in range(x + 7, x + w - 6):
                    self.c.set(xx, yy, S_[2] if (xx - yy) % 7 < 3 else S_[3] if (xx + yy) % 2 else S_[2])
            self.dark(x + 7, y + 10, x + w - 7, y + 12, 1)
        else:
            self.bevel(x + 5, y + 8, x + w - 5, y + int(h * 0.44), W_, inset=True)
        # Ручка и замок.
        hy = y + int(h * 0.52)
        self.rect(x + w - 11, hy, x + w - 5, hy + 1, M[3])
        self.rect(x + w - 11, hy + 2, x + w - 5, hy + 2, M[0])
        self.c.set(x + w - 6, hy + 5, M[0])
        if plate:
            P_ = self.R(plate)
            self.rect(x + w // 2 - 8, y - 16, x + w // 2 + 8, y - 10, P_[2])
            self.rect(x + w // 2 - 8, y - 16, x + w // 2 + 8, y - 16, P_[3])
            self.rect(x + w // 2 - 5, y - 13, x + w // 2 + 4, y - 13, P_[0])
        self.dark(x, y, x + w, y + 3, 1)
        self.bevel(x - 8, y + h + 1, x + w + 8, y + h + 4, M)

    def cooler(self, x, yb):
        """Кулер: белая тумба с кранами, сверху перевёрнутая голубая бутыль с водой."""
        Wh, S_, D, Rd, B = self.R("white"), self.R("sky"), self.R("dark"), self.R("red"), self.R("blue")
        self.bevel(x - 11, yb - 56, x + 11, yb, Wh)
        self.rect(x - 9, yb - 38, x + 9, yb - 26, D[1])
        self.rect(x - 9, yb - 38, x + 9, yb - 38, D[0])
        self.rect(x - 6, yb - 37, x - 4, yb - 33, B[3])
        self.rect(x + 4, yb - 37, x + 6, yb - 33, Rd[2])
        self.rect(x - 8, yb - 27, x + 8, yb - 26, self.R("metal")[2])
        self.rect(x - 8, yb - 20, x + 8, yb - 20, Wh[1])
        self.bevel(x - 7, yb - 16, x + 7, yb - 4, Wh, inset=True)
        jug = set((xx, yy) for xx in range(x - 9, x + 10) for yy in range(yb - 88, yb - 64))
        jug |= ellipse(x, yb - 88, 9, 4) | poly([(x - 9, yb - 64), (x + 9, yb - 64), (x + 4, yb - 57), (x - 4, yb - 57)])
        self.put(jug, S_, soft=True)
        for (xx, yy) in jug:
            if yy < yb - 82:
                self.c.set(xx, yy, self.R("lamp")[1] if (xx + yy) % 2 else S_[3])
        self.rect(x - 9, yb - 82, x + 9, yb - 82, S_[0])
        for yy in (yb - 76, yb - 70):
            self.rect(x - 9, yy, x + 9, yy, S_[1])
        self.rect(x - 6, yb - 86, x - 6, yb - 66, self.R("lamp")[3])
        self.c.set(x + 3, yb - 74, self.R("lamp")[3])
        self.c.set(x + 5, yb - 79, self.R("lamp")[3])
        # Стопка стаканчиков сбоку.
        self.rect(x + 13, yb - 50, x + 16, yb - 34, Wh[2])
        for yy in range(yb - 50, yb - 34, 3):
            self.rect(x + 13, yy, x + 16, yy, Wh[0])
        self.dark(x + 12, yb - 56, x + 13, yb, 1)

    def vending(self, x, y, w, h):
        """Автомат с перекусом: тёмный корпус, витрина с рядами пачек, пульт, лоток выдачи."""
        D, Rd, G, Wh = self.R("dark"), self.R("red"), self.R("lamp"), self.R("white")
        r = self.rng
        self.bevel(x, y, x + w, y + h, D)
        self.rect(x + 2, y + 2, x + w - 2, y + 12, Rd[2])
        self.rect(x + 2, y + 2, x + w - 2, y + 2, Rd[3])
        for xx in range(x + 6, x + w - 6):
            yy = y + 7 + int(round(math.sin((xx - x) * 0.55) * 2))
            self.c.set(xx, yy, Wh[3])
        gx1 = x + w - 16
        self.rect(x + 4, y + 16, gx1, y + h - 22, self.R("blue")[0])
        ramps = ("gold", "red", "pink", "green", "sky", "white")
        for row, yy in enumerate(range(y + 18, y + h - 34, 13)):
            for xx in range(x + 6, gx1 - 5, 7):
                R_ = self.R(ramps[r.randint(0, 5)])
                self.rect(xx, yy, xx + 4, yy + 8, R_[2])
                self.rect(xx, yy, xx + 4, yy, R_[3])
                self.rect(xx + 4, yy + 1, xx + 4, yy + 8, R_[1])
                self.rect(xx + 1, yy + 4, xx + 3, yy + 4, R_[0])
            self.rect(x + 4, yy + 10, gx1, yy + 10, self.R("metal")[2])
            self.rect(x + 4, yy + 11, gx1, yy + 11, D[0])
        for k in range(0, h - 40, 3):
            xx, yy = x + 8 + k // 3, y + h - 24 - k
            if x + 4 <= xx <= gx1:
                self.c.set(xx, yy, G[1])
        # Пульт: экран, кнопки, щель для монет.
        self.rect(gx1 + 4, y + 20, x + w - 4, y + 28, self.R("green")[0])
        self.rect(gx1 + 5, y + 23, x + w - 6, y + 23, self.R("green")[3])
        for row in range(4):
            for col in range(3):
                self.c.set(gx1 + 5 + col * 3, y + 34 + row * 4, Wh[2])
        self.rect(gx1 + 6, y + 56, gx1 + 9, y + 57, self.R("metal")[3])
        self.rect(x + 6, y + h - 16, gx1 - 2, y + h - 6, D[0])
        self.rect(x + 6, y + h - 16, gx1 - 2, y + h - 16, D[3])
        self.dark(x + w + 1, y + 4, x + w + 3, y + h, 1)

    def counter(self, x, y, w):
        """Кухонная стойка: столешница, дверцы, на ней кофемашина и кружки, сверху шкафчик."""
        Wh, D, Wd, Rd, M = self.R("white"), self.R("dark"), self.R("wood"), self.R("red"), self.R("metal")
        self.bevel(x, y, x + w, y + 5, Wd)
        self.rect(x + 2, y + 6, x + w - 2, WALL_Y - 4, Wh[2])
        for xx in range(x + 2, x + w - 4, 24):
            self.bevel(xx, y + 8, min(xx + 21, x + w - 2), WALL_Y - 6, Wh)
            self.rect(xx + 9, y + 12, xx + 13, y + 13, M[1])
        self.dark(x + 2, y + 6, x + w - 2, y + 7, 1)
        # Кофемашина: чёрный корпус, красный огонёк, носик, чашка под ним.
        self.bevel(x + 8, y - 30, x + 34, y - 1, D)
        self.rect(x + 12, y - 26, x + 30, y - 20, M[2])
        self.rect(x + 12, y - 26, x + 30, y - 26, M[3])
        self.c.set(x + 28, y - 16, Rd[3])
        self.c.set(x + 24, y - 16, self.R("green")[3])
        self.rect(x + 14, y - 14, x + 28, y - 3, D[0])
        self.rect(x + 20, y - 14, x + 22, y - 11, M[3])
        self.rect(x + 18, y - 8, x + 24, y - 3, Wh[3])
        self.rect(x + 24, y - 8, x + 24, y - 3, Wh[1])
        self.rect(x + 19, y - 8, x + 23, y - 8, Wd[0])
        # Кружки и коробка с чаем.
        for k, (mx, ramp) in enumerate(((x + 44, "red"), (x + 54, "sky"), (x + 64, "gold"))):
            if mx + 8 > x + w:
                break
            R_ = self.R(ramp)
            self.rect(mx, y - 8, mx + 5, y - 1, R_[2])
            self.rect(mx, y - 8, mx, y - 1, R_[3])
            self.rect(mx + 5, y - 8, mx + 5, y - 1, R_[1])
            self.rect(mx + 6, y - 6, mx + 7, y - 3, R_[1])
            self.rect(mx, y - 8, mx + 5, y - 8, D[1])
        # Навесной шкафчик.
        self.rect(x + 4, y - 80, x + w - 2, y - 46, D[1])
        self.bevel(x + 2, y - 82, x + w - 4, y - 48, Wh)
        mid = x + w // 2
        self.rect(mid, y - 81, mid, y - 49, Wh[1])
        self.rect(mid - 5, y - 54, mid - 3, y - 53, M[1])
        self.rect(mid + 3, y - 54, mid + 5, y - 53, M[1])

    def board(self, x, y, w, h):
        """Пробковая доска: рама, пробка крапом, стикеры четырёх цветов, листы, график."""
        Wd, Cd, Wh, Rd = self.R("wood"), self.R("card"), self.R("white"), self.R("red")
        r = self.rng
        self.rect(x + 2, y + 2, x + w + 3, y + h + 3, self.R("wall")[0])
        self.bevel(x, y, x + w, y + h, Wd)
        self.rect(x + 3, y + 3, x + w - 3, y + h - 3, Cd[2])
        self.noise(x + 3, y + 3, x + w - 3, y + h - 3, Cd, 0.14)
        # Лист с графиком продаж: красная линия уверенно идёт вниз.
        self.rect(x + 9, y + 9, x + 46, y + 44, Wh[0])
        self.rect(x + 8, y + 8, x + 44, y + 42, Wh[3])
        self.rect(x + 12, y + 12, x + 12, y + 38, Wh[0])
        self.rect(x + 12, y + 38, x + 41, y + 38, Wh[0])
        py = y + 15
        for xx in range(x + 14, x + 41):
            py += r.choice((0, 1, 1, 0, 2, -1))
            py = min(py, y + 36)
            self.c.set(xx, py, Rd[2])
            self.c.set(xx, py + 1, Rd[2])
        self.c.set(x + 26, y + 8, Rd[2])
        # Листы с текстом.
        for (px, py) in ((x + 52, y + 10), (x + 10, y + 50)):
            if px + 24 < x + w - 3 and py + 24 < y + h - 3:
                self.rect(px + 1, py + 1, px + 23, py + 27, Cd[0])
                self.rect(px, py, px + 22, py + 26, Wh[3])
                for yy in range(py + 4, py + 24, 3):
                    self.rect(px + 3, yy, px + 19 - r.randint(0, 8), yy, Wh[0])
                self.c.set(px + 11, py + 1, self.R("blue")[3])
        # Стикеры россыпью по свободному месту.
        ramps = ("gold", "pink", "sky", "green", "gold")
        for k in range(int(w * h / 420)):
            sx, sy = r.randint(x + 5, x + w - 13), r.randint(y + 5, y + h - 13)
            if all(self.c.get(sx + dx, sy + dy) in Cd for dx in (0, 8) for dy in (0, 8)):
                self.sticker(sx, sy, ramps[k % 5])
        self.dark(x + 3, y + 3, x + w - 3, y + 4, 1)

    def screen(self, x, y, w, h):
        """Панель на стене: тёмная рамка, слайд с диаграммой и столбиками."""
        D, S_, G, Rd = self.R("dark"), self.R("sky"), self.R("gold"), self.R("red")
        self.rect(x + 2, y + 2, x + w + 2, y + h + 2, self.R("wall")[0])
        self.bevel(x, y, x + w, y + h, D)
        self.rect(x + 3, y + 3, x + w - 3, y + h - 3, self.R("blue")[1])
        self.rect(x + 6, y + 6, x + w // 2, y + 7, S_[3])
        self.rect(x + 6, y + 10, x + w // 2 - 8, y + 10, S_[1])
        for (px, py) in ellipse(x + w - 16, y + h // 2, 9, 9):
            a = math.atan2(py - y - h // 2, px - x - w + 16)
            self.c.set(px, py, G[2] if a < -0.6 else Rd[2] if a < 1.4 else S_[1])
        for k, bh in enumerate((6, 10, 8, 14, 5)):
            bx = x + 7 + k * 6
            if bx + 3 < x + w - 28:
                self.rect(bx, y + h - 6 - bh, bx + 3, y + h - 6, S_[2])
                self.c.set(bx, y + h - 6 - bh, S_[3])
        for yy in range(y + 4, y + h - 3, 3):
            self.dark(x + 3, yy, x + w - 3, yy, 0)
        self.c.set(x + w - 4, y + h - 1, Rd[3])

    def clock(self, cx, cy, r=9):
        Wh, D = self.R("white"), self.R("dark")
        self.put(ellipse(cx, cy, r + 2, r + 2), D, soft=False)
        for (x, y) in ellipse(cx, cy, r, r):
            self.c.set(x, y, Wh[3] if (x - cx) + (y - cy) < r * 0.6 else Wh[2])
        for k in range(12):
            a = k * math.pi / 6
            self.c.set(cx + math.cos(a) * (r - 1.5), cy + math.sin(a) * (r - 1.5), D[2])
        for k in range(r - 3):
            self.c.set(cx, cy - k, D[0])
        for k in range(r - 4):
            self.c.set(cx + k, cy + k * 0.4, D[0])
        self.c.set(cx, cy, self.R("red")[2])

    def exit_sign(self, x, y):
        """Зелёный указатель выхода: стрелка и дверной проём."""
        Gn, Wh = self.R("green"), self.R("white")
        self.rect(x + 1, y + 1, x + 27, y + 12, self.R("dark")[1])
        self.rect(x, y, x + 26, y + 11, Gn[2])
        self.rect(x, y, x + 26, y, Gn[3])
        self.rect(x, y + 11, x + 26, y + 11, Gn[1])
        self.rect(x + 4, y + 5, x + 13, y + 6, Wh[3])
        for k in range(4):
            self.c.set(x + 4 + k, y + 5 - k, Wh[3])
            self.c.set(x + 4 + k, y + 6 + k, Wh[3])
        self.rect(x + 17, y + 2, x + 22, y + 9, Wh[3])
        self.rect(x + 19, y + 4, x + 22, y + 9, Gn[0])

    def extinguisher(self, x, yb):
        """Огнетушитель на стене под табличкой."""
        Rd, D, Wh = self.R("red"), self.R("dark"), self.R("white")
        self.bevel(x - 9, yb - 54, x + 9, yb - 40, Rd)
        for (px, py) in poly([(x, yb - 51), (x + 5, yb - 43), (x - 5, yb - 43)]):
            self.c.set(px, py, Wh[3])
        self.rect(x, yb - 48, x, yb - 46, Rd[1])
        body = set((xx, yy) for xx in range(x - 5, x + 6) for yy in range(yb - 26, yb + 1)) | ellipse(x, yb - 26, 5, 3)
        self.put(body, Rd, soft=True)
        self.rect(x - 5, yb - 16, x + 5, yb - 11, Wh[2])
        self.rect(x - 2, yb - 33, x + 2, yb - 29, D[2])
        self.rect(x - 6, yb - 35, x + 3, yb - 34, D[1])
        for k in range(8):
            self.c.set(x + 6 + (1 if 1 < k < 6 else 0), yb - 30 + k, D[0])

    def vent(self, x, y, w, h):
        Wh, D = self.R("white"), self.R("dark")
        self.bevel(x, y, x + w, y + h, Wh)
        for yy in range(y + 3, y + h - 1, 4):
            self.rect(x + 3, yy, x + w - 3, yy + 1, D[2])
            self.rect(x + 3, yy + 2, x + w - 3, yy + 2, Wh[3])
        self.dark(x + 1, y + h + 1, x + w + 2, y + h + 2, 1)

    def lamp(self, x, y, w=40):
        """Плафон дневного света под потолком и пятно света на стене под ним."""
        G = self.R("lamp")
        for (xx, yy) in ellipse(x + w / 2, y + 26, w * 0.75, 30):
            e = self.c.get(xx, yy)
            if e is None or yy < y + 6:
                continue
            for name in ("wall", "white", "blue"):
                R_ = self.R(name)
                if e in R_ and R_.index(e) < 3 and ((xx + yy) % 2 == 0 or abs(xx - x - w / 2) < w * 0.35 and yy < y + 30):
                    self.c.set(xx, yy, R_[R_.index(e) + 1])
        self.bevel(x - 2, y - 1, x + w + 2, y + 6, self.R("metal"))
        self.rect(x, y + 1, x + w, y + 4, G[3])
        self.rect(x, y + 4, x + w, y + 4, G[1])
        for xx in range(x + 8, x + w, 10):
            self.rect(xx, y + 1, xx, y + 4, G[1])

    # Предметы у стены -------------------------------------------------------------------------

    def jug(self, x, y, w=18, h=30):
        """Запасная бутыль для кулера: голубой цилиндр с рёбрами и синей крышкой."""
        S_, B = self.R("sky"), self.R("blue")
        S = set()
        for yy in range(y - h + 5, y + 1):
            for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                S.add((xx, yy))
        S |= ellipse(x, y - h + 5, w / 2, 5)
        self.put(S, S_, soft=True)
        for hy in (y - h + 12, y - h + 19, y - 5):
            for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                self.c.set(xx, hy, S_[1] if xx > x - w / 2 + 2 else S_[2])
        self.rect(x - w // 2 + 3, y - h + 6, x - w // 2 + 3, y - 3, self.R("lamp")[3])
        self.rect(x - 3, y - h - 5, x + 3, y - h, B[2])
        self.rect(x - 3, y - h - 5, x + 3, y - h - 5, B[3])
        self.rect(x + 3, y - h - 4, x + 3, y - h, B[1])
        self.rect(x - 5, y - h + 14, x + 5, y - h + 17, self.R("white")[3])
        self.rect(x - 3, y - h + 15, x + 2, y - h + 15, B[2])

    def bin(self, x, y, w=14, h=20):
        """Сетчатая корзина для бумаг, сверху торчат комки."""
        M, Wh, D = self.R("metal"), self.R("white"), self.R("dark")
        for k, (dx, dy) in enumerate(((-3, -2), (2, -4), (5, -1))):
            self.put(ellipse(x + dx, y - h + dy, 4, 3.4), Wh, soft=False)
            self.c.set(x + dx - 1, y - h + dy, Wh[1])
        for yy in range(y - h, y + 1):
            half = w / 2.0 - (yy - (y - h)) * 0.12
            for xx in range(int(round(x - half)), int(round(x + half)) + 1):
                on = (xx + yy) % 3 == 0 or (xx - yy) % 3 == 0
                self.c.set(xx, yy, (M[3] if xx < x - 1 else M[2]) if on else D[1])
        self.rect(int(x - w / 2), y - h, int(x + w / 2), y - h, M[3])
        self.rect(int(x - w / 2), y - h + 1, int(x + w / 2), y - h + 1, M[1])
        self.rect(int(x - w / 2 + 2), y, int(x + w / 2 - 2), y, M[0])

    def carton(self, x, y, w=30, h=24):
        """Коробка бумаги: картон, клапаны крышки, скотч, белый ярлык со строками."""
        Cd, Wh = self.R("card"), self.R("white")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h, y + 1))
        self.put(S, Cd, soft=False)
        self.noise(x + 1, y - h + 1, x + w - 2, y - 2, Cd, 0.04)
        self.rect(x, y - h, x + w, y - h + 1, Cd[3])
        self.rect(x, y - h + 5, x + w, y - h + 5, Cd[1])
        self.rect(x + w // 2 - 2, y - h, x + w // 2 + 2, y - h + 9, Cd[3])
        self.rect(x + w // 2 + 2, y - h + 1, x + w // 2 + 2, y - h + 9, Cd[1])
        self.rect(x + 4, y - 13, x + 17, y - 4, Wh[3])
        self.rect(x + 6, y - 11, x + 11, y - 9, self.R("blue")[2])
        self.rect(x + 6, y - 7, x + 15, y - 7, Wh[0])
        self.rect(x + w - 8, y - 12, x + w - 4, y - 8, self.R("red")[2])

    def folders(self, x, y):
        """Стопка папок: корешки разного цвета лежат друг на друге, сверху стикер."""
        ramps = ("blue", "gold", "red", "green", "white")
        yy = y
        for k, ramp in enumerate(ramps):
            R_ = self.R(ramp)
            off = (0, 2, -1, 1, -2)[k]
            self.rect(x - 11 + off, yy - 3, x + 11 + off, yy, R_[2])
            self.rect(x - 11 + off, yy - 3, x + 11 + off, yy - 3, R_[3])
            self.rect(x - 11 + off, yy, x + 11 + off, yy, R_[0] if ramp != "white" else R_[1])
            self.rect(x - 8 + off, yy - 2, x - 4 + off, yy - 1, self.R("white")[3])
            self.c.set(x + 11 + off, yy - 2, R_[1])
            yy -= 4
        self.sticker(x - 2, yy - 4, "pink", 6, text=False)

    def ficus(self, x, y, h=62):
        """Фикус в горшке: белый горшок, ствол, крупные листья веером."""
        Gn, Wh, Wd = self.R("green"), self.R("white"), self.R("wood")
        r = self.rng
        pot = poly([(x - 9, y - 16), (x + 9, y - 16), (x + 7, y), (x - 7, y)])
        self.rect(x - 1, y - h + 18, x + 1, y - 16, Wd[1])
        self.rect(x - 1, y - h + 18, x - 1, y - 16, Wd[2])
        leaves = []
        for k in range(15):
            a = math.radians(-90 + (k - 7) * 19 + r.uniform(-8, 8))
            d = r.uniform(7, 15)
            cy = y - h + 22 - r.uniform(0, 12)
            leaves.append((cy + math.sin(a) * d, x + math.cos(a) * d, cy + math.sin(a) * d, math.degrees(a)))
        leaves.sort()
        for (_, lx, ly, ang) in leaves:
            leaf = ellipse(lx, ly, 7.5, 3.6, ang)
            self.put(leaf, Gn, soft=False)
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for t in range(-5, 6):
                self.c.set(lx + ca * t, ly + sa * t, Gn[3] if t > -3 else Gn[1])
        self.put(pot, Wh, soft=True)
        self.rect(x - 10, y - 17, x + 10, y - 15, Wh[3])
        self.rect(x - 10, y - 14, x + 10, y - 14, Wh[1])
        self.rect(x - 7, y - 18, x + 7, y - 18, Wd[0])


def build_street():
    """Этаж конторы той же ширины и с теми же строками пола, что улица пиратов: стена до
    `WALL_Y`, полоса плитки до `CURB_Y`, алюминиевый порожек, ковролин от `ROAD_Y`."""
    st = Floor()
    c, rng = st.c, st.rng
    W_, Wh, D, M, G = st.R("wall"), st.R("white"), st.R("dark"), st.R("metal"), st.R("lamp")
    B, S_ = st.R("blue"), st.R("sky")
    x = 0
    modules = [("windows", 320), ("kitchen", 288), ("meeting", 352), ("cubes", 256), ("print", 256), ("hall", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        # Подвесной потолок: белые плиты в сетке профиля, решётки вентиляции, карниз.
        st.rect(x0, 0, x1, 19, Wh[2])
        for xx in range(x0, x1 + 1, 32):
            st.rect(xx, 0, xx, 19, Wh[1])
            st.rect(xx + 1, 0, xx + 1, 19, Wh[3])
        st.rect(x0, 9, x1, 9, Wh[1])
        st.rect(x0, 10, x1, 10, Wh[3])
        for xx in range(x0 + 3, x1 - 28, 32):
            if rng.random() < 0.22:
                for yy in range(12, 18, 2):
                    st.rect(xx + 4, yy, xx + 24, yy, M[2])
            elif rng.random() < 0.5:
                for _ in range(5):
                    c.set(xx + rng.randint(2, 26), rng.randint(1, 18), Wh[1])
        st.bevel(x0, 20, x1, 31, Wh)
        st.rect(x0, 26, x1, 26, Wh[1])
        st.dark(x0, 0, x1, 19, 1, dither=True)
        st.dark(x0, 32, x1, 35, 1)
        st.dark(x0, 36, x1, 38, 1, dither=True)
        if kind == "windows":
            st.paint(x0, x1)
            for wx in (x0 + 26, x0 + 126, x0 + 226):
                st.window(wx, 62, 72, 92, blinds=(0.22, 0.5, 0.3)[(wx - x0) // 100])
            for wx in (x0 + 30, x0 + 230):
                st.radiator(wx, 192, 62, 26)
            st.vent(x0 + 132, 196, 56, 18)
            st.lamp(x0 + 86, 40, 44)
            st.lamp(x0 + 190, 40, 44)
            st.ficus(x0 + 112, WALL_Y, 66)
            st.sticker(x0 + 104, 120, "gold")
            st.sticker(x0 + 208, 96, "pink")
        elif kind == "kitchen":
            st.paint(x0, x1, rail=WALL_Y + 20)
            # Фартук плиткой над стойкой.
            for yy in range(96, 152):
                for xx in range(x0 + 108, x0 + 216):
                    c.set(xx, yy, Wh[1] if (xx - x0) % 12 == 0 or yy % 12 == 0 else Wh[3] if ((xx - x0) // 12 + yy // 12) % 3 else S_[3])
            st.cooler(x0 + 30, WALL_Y)
            st.vending(x0 + 52, 92, 50, WALL_Y - 92)
            st.counter(x0 + 110, 172, 104)
            st.clock(x0 + 162, 64, 10)
            st.door(x0 + 232, 92, 46, WALL_Y - 96, color="red", glass=False, plate=None)
            st.exit_sign(x0 + 242, 66)
            st.lamp(x0 + 60, 40, 40)
            st.sticker(x0 + 8, 100, "gold")
            st.sticker(x0 + 14, 112, "sky")
        elif kind == "meeting":
            st.paint(x0, x1)
            # Переговорная за стеклом: тёмная комната, стол со стульями, доска с графиком,
            # матовая полоса на стекле, стальные стойки.
            gx0, gx1 = x0 + 70, x0 + 250
            st.bevel(gx0 - 10, 50, gx1 + 10, WALL_Y, M)
            for xx in range(gx0, gx1 + 1):
                for yy in range(60, WALL_Y + 1):
                    c.set(xx, yy, B[1] if (xx + yy) % 2 or yy < 110 else B[2])
            # Доска на дальней стене.
            st.bevel(gx0 + 24, 78, gx0 + 96, 124, Wh)
            py = 88
            for xx in range(gx0 + 30, gx0 + 90):
                py += rng.choice((0, 0, 1, 1, -1, 1))
                py = min(py, 118)
                c.set(xx, py, st.R("red")[2])
            for k in range(4):
                st.rect(gx0 + 34 + k * 8, 114 - k * 3, gx0 + 37 + k * 8, 120, S_[1])
            st.sticker(gx0 + 84, 82, "gold", 6, text=False)
            # Экран проектора светится справа.
            st.rect(gx0 + 116, 82, gx0 + 164, 116, S_[2])
            st.rect(gx0 + 116, 82, gx0 + 164, 83, G[3])
            for k in range(5):
                st.rect(gx0 + 122, 90 + k * 5, gx0 + 152 - k * 4, 90 + k * 5, S_[0])
            # Стол и спинки стульев силуэтом.
            st.rect(gx0 + 12, 176, gx1 - 30, 181, st.R("wood")[2])
            st.rect(gx0 + 12, 176, gx1 - 30, 176, st.R("wood")[3])
            st.rect(gx0 + 18, 182, gx0 + 21, WALL_Y - 6, st.R("wood")[0])
            st.rect(gx1 - 40, 182, gx1 - 37, WALL_Y - 6, st.R("wood")[0])
            for cx in range(gx0 + 28, gx1 - 44, 30):
                S = ellipse(cx + 6, 160, 9, 12) | set((xx, yy) for xx in range(cx + 4, cx + 9) for yy in range(170, 177))
                for (xx, yy) in S:
                    c.set(xx, yy, D[1] if (xx, yy - 1) in S and (xx - 1, yy) in S else D[3])
            # Стекло: матовая полоса, блики наискось, стойки и дверь.
            for yy in range(132, 156):
                for xx in range(gx0, gx1 + 1):
                    if (xx + yy) % 2 == 0 or yy in (132, 155):
                        c.set(xx, yy, Wh[2] if yy not in (132, 155) else Wh[3])
            for k in range(0, 170, 2):
                for off in (30, 36, 118):
                    xx, yy = gx0 + off + k // 2, WALL_Y - 4 - k
                    if gx0 < xx < gx1 and yy > 60 and c.get(xx, yy) in (B[1], B[2]):
                        c.set(xx, yy, B[3])
            for xx in (gx0 + 58, gx0 + 118):
                st.rect(xx, 60, xx + 2, WALL_Y, M[2])
                st.rect(xx, 60, xx, WALL_Y, M[3])
            dx0 = gx1 - 44
            st.bevel(dx0 - 3, 76, gx1, WALL_Y, M)
            for xx in range(dx0, gx1 - 2):
                for yy in range(80, WALL_Y - 2):
                    c.set(xx, yy, B[2] if (xx - yy) % 9 < 3 else B[1] if yy < 132 or yy > 155 else Wh[2])
            st.rect(dx0 + 3, 150, dx0 + 5, 172, M[3])
            st.rect(dx0 + 6, 150, dx0 + 6, 172, M[0])
            st.dark(gx0, 60, gx1, 68, 1)
            st.dark(gx0, 69, gx1, 74, 1, dither=True)
            # Номер комнаты: белая табличка с цифрами.
            st.rect(x0 + 268, 70, x1 - 18, 98, D[1])
            st.rect(x0 + 266, 68, x1 - 20, 96, Wh[3])
            for k in range(3):
                bx = x0 + 276 + k * 16
                st.rect(bx, 75, bx + 9, 89, B[2])
                st.rect(bx + 2, 77, bx + 7, 87 if k != 1 else 80, Wh[3])
            st.screen(x0 + 270, 118, 62, 44)
            st.extinguisher(x0 + 34, WALL_Y - 6)
            st.lamp(x0 + 14, 44, 34)
            st.sticker(x0 + 282, 170, "pink")
            st.sticker(x0 + 300, 166, "gold")
        elif kind == "cubes":
            st.paint(x0, x1, rail=WALL_Y + 20)
            st.window(x0 + 20, 58, 60, 62, blinds=0.6)
            st.clock(x0 + 122, 70, 9)
            st.window(x0 + 176, 58, 60, 62, blinds=0.25)
            # Над перегородками видны мониторы и настольная лампа.
            for (mx, lit) in ((x0 + 22, True), (x0 + 96, False), (x0 + 196, True)):
                st.bevel(mx, 124, mx + 30, 144, D)
                if lit:
                    st.rect(mx + 2, 126, mx + 28, 142, S_[1])
                    for yy in range(128, 142, 3):
                        st.rect(mx + 4, yy, mx + 24 - (yy % 7), yy, S_[3])
                else:
                    st.rect(mx + 2, 126, mx + 28, 142, D[0])
                    st.sticker(mx + 20, 127, "gold", 6, text=False)
                st.rect(mx + 13, 145, mx + 17, 148, M[1])
            st.rect(x0 + 150, 126, x0 + 152, 148, M[2])
            for (px, py) in poly([(x0 + 140, 126), (x0 + 156, 120), (x0 + 160, 128), (x0 + 146, 134)]):
                c.set(px, py, st.R("red")[2] if py < 128 else st.R("red")[1])
            st.fabric(x0, 152, x1, WALL_Y)
            for (sx, sy, ramp) in ((x0 + 12, 162, "gold"), (x0 + 24, 170, "pink"), (x0 + 70, 160, "sky"),
                                   (x0 + 82, 176, "gold"), (x0 + 128, 164, "green"), (x0 + 186, 160, "pink"),
                                   (x0 + 198, 172, "gold"), (x0 + 232, 166, "sky")):
                st.sticker(sx, sy, ramp)
            # Лист «план на квартал» на кнопке.
            st.rect(x0 + 141, 181, x0 + 163, 207, B[0])
            st.rect(x0 + 140, 180, x0 + 162, 206, Wh[3])
            for yy in range(185, 204, 3):
                st.rect(x0 + 143, yy, x0 + 158 - (yy % 6), yy, Wh[0])
            c.set(x0 + 151, 181, st.R("red")[2])
            st.lamp(x0 + 100, 40, 48)
        elif kind == "print":
            st.paint(x0, x1)
            st.board(x0 + 20, 62, 134, 96)
            # Копир под доской: корпус, крышка сканера, пульт, лоток с листами.
            cx = x0 + 44
            st.bevel(cx, 176, cx + 56, WALL_Y - 2, Wh)
            st.bevel(cx - 2, 166, cx + 58, 176, M)
            st.rect(cx + 2, 174, cx + 40, 175, G[1])
            st.rect(cx + 42, 168, cx + 55, 173, D[1])
            c.set(cx + 45, 170, st.R("green")[3])
            c.set(cx + 49, 170, st.R("red")[3])
            c.set(cx + 53, 170, st.R("gold")[2])
            for yy in (190, 206, 220):
                st.bevel(cx + 4, yy, cx + 52, yy + 11, Wh, inset=True)
                st.rect(cx + 22, yy + 3, cx + 34, yy + 4, M[1])
            for k in range(4):
                st.rect(cx - 16 + k, 182 + k * 2, cx - 1, 183 + k * 2, Wh[3] if k % 2 == 0 else Wh[1])
            st.rect(cx - 18, 190, cx - 1, 191, M[1])
            st.dark(cx + 57, 178, cx + 59, WALL_Y - 2, 1)
            st.carton(x0 + 112, WALL_Y, 28, 22)
            st.carton(x0 + 116, WALL_Y - 23, 24, 18)
            st.lift(x0 + 184, 96, 46, WALL_Y - 100)
            st.lamp(x0 + 70, 42, 50)
            st.ficus(x0 + 168, WALL_Y, 58)
        elif kind == "hall":
            st.paint(x0, x0 + 30)
            st.paint(x1 - 30, x1)
            # Боковой коридор: тёмная глубина, плафоны уходят вдаль, в конце дверь под зелёным
            # указателем, полоса ковролина сходится к ней.
            for yy in range(32, WALL_Y + 1):
                for xx in range(x0 + 31, x1 - 30):
                    k = (yy - 32) / float(WALL_Y - 32)
                    c.set(xx, yy, B[0] if k < 0.5 or (xx + yy) % 2 else B[1])
            mid = (x0 + x1) // 2
            for k, yy in enumerate((40, 54, 64, 71)):
                half = 40 - k * 9
                st.rect(mid - half, yy, mid + half, yy + max(1, 3 - k), G[3] if k < 2 else G[1])
                st.rect(mid - half, yy + max(1, 3 - k), mid + half, yy + max(1, 3 - k), G[0])
            st.bevel(x0 + 62, 86, x1 - 62, WALL_Y - 28, W_)
            st.bevel(mid - 14, 112, mid + 14, WALL_Y - 28, st.R("wood"))
            st.rect(mid + 8, 160, mid + 10, 161, M[3])
            st.rect(mid - 13, 94, mid + 13, 105, st.R("green")[2])
            st.rect(mid - 13, 94, mid + 13, 94, st.R("green")[3])
            st.rect(mid - 8, 99, mid + 2, 100, Wh[3])
            for k_ in range(3):
                c.set(mid + 2 - k_, 99 - k_, Wh[3])
                c.set(mid + 2 - k_, 100 + k_, Wh[3])
            Cp = st.R("carpet")
            for k, yy in enumerate(range(WALL_Y - 26, WALL_Y + 1, 4)):
                st.rect(x0 + 62 - k * 4, yy, x1 - 62 + k * 4, yy + 3, Cp[1] if k % 2 else Cp[0])
            st.rect(x0 + 31, 32, x1 - 31, 39, B[0])
            for xx in (x0 + 31, x1 - 33):
                st.rect(xx, 40, xx + 2, WALL_Y, Wh[2])
                st.rect(xx, 40, xx, WALL_Y, Wh[3])
            st.sticker(x0 + 10, 110, "gold")
            st.clock(x1 - 15, 84, 8)
            st.carton(x0 + 36, WALL_Y, 26, 22)
            st.bin(x1 - 46, WALL_Y, 16, 24)
        x += w
    # Плинтус и тень у пола.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Полоса у стены: светлая плитка рядами, швы, редкие плитки темнее.
    Tl = st.R("tile")
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        off = (ri * 23) % 48
        xx = -off
        while xx < SW:
            w = 48
            a, b = max(xx + 1, 0), min(xx + w - 1, SW - 1)
            yb = min(y0 + h - 1, CURB_Y - 1)
            ramp = Tl if rng.random() < 0.8 else [Tl[0], Tl[1], Tl[1], Tl[2]]
            st.bevel(a, y0, b, yb, ramp)
            st.noise(a + 1, y0 + 1, b - 1, yb - 1, ramp, 0.02)
            # Блик лампы на глянце.
            if rng.random() < 0.4 and b - a > 30:
                for k in range(8):
                    c.set(a + 12 + k * 2, yb - 3 - k // 2, Tl[3])
            xx += w
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Порожек: алюминиевый профиль с рифлением и винтами.
    for xx in range(SW):
        c.set(xx, CURB_Y, Wh[3])
        c.set(xx, CURB_Y + 1, M[3])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, M[2] if (yy - CURB_Y) % 3 else M[1])
        if xx % 64 == 20:
            c.set(xx, CURB_Y + 5, D[1])
            c.set(xx + 1, CURB_Y + 5, D[1])
            c.set(xx, CURB_Y + 4, Wh[3])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, D[0])
    # Ковролин плитами: ряды к зрителю выше, ворс крапом, плиты через одну темнее.
    Cp = st.R("carpet")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Cp[1])
    y = ROAD_Y + 2
    h = 14
    row = 0
    while y < SH:
        pw = 52 + row * 6
        xx = -((row * 19) % pw)
        col = 0
        while xx < SW:
            a, b = max(xx, 0), min(xx + pw - 1, SW - 1)
            yb = min(y + h - 1, SH - 1)
            if b > a and yb > y:
                alt = (col + row) % 2 == 0
                base = Cp[2] if alt else Cp[1]
                st.rect(a, y, b, yb, base)
                for py in range(y, yb + 1):
                    for px in range(a, b + 1):
                        v = rng.random()
                        if v < 0.16:
                            c.set(px, py, Cp[1] if alt else Cp[0])
                        elif v < 0.24:
                            c.set(px, py, Cp[3] if alt else Cp[2])
                st.rect(a, yb, b, yb, Cp[0])
                st.rect(b, y, b, yb, Cp[0])
                # Узор плиты: тонкие диагональные штрихи.
                if rng.random() < 0.3:
                    for k in range(a + 8, b - 10, 7):
                        for d in range(4):
                            if y + 3 + d < yb - 2:
                                c.set(k + d, y + 3 + d, Cp[3] if alt else Cp[2])
            xx += pw
            col += 1
        y += h
        h += 3
        row += 1
    st.dark(0, ROAD_Y + 2, SW - 1, ROAD_Y + 4, 1, dither=True)
    # На ковролине: разлетевшиеся листы, стикеры и пятна кофе.
    Wd = st.R("wood")
    for px0 in (220, 760, 1310):
        stain = ellipse(px0 - 44, 384, 15, 5) | ellipse(px0 - 34, 387, 8, 3)
        for (px, py) in stain:
            e = c.get(px, py)
            if e is not None and ((px, py + 1) not in stain or (px + py) % 2 == 0 or (px - 1, py) not in stain):
                c.set(px, py, Cp[0])
        for k, (dx, dy, sk) in enumerate(((0, 0, 5), (30, 6, -4), (-14, -10, 3))):
            sheet = poly([(px0 + dx, 366 + dy), (px0 + dx + 18, 366 + dy), (px0 + dx + 18 + sk, 375 + dy),
                          (px0 + dx + sk, 375 + dy)])
            for (px, py) in sheet:
                edge = (px, py + 1) not in sheet or (px + 1, py) not in sheet
                c.set(px, py, Wh[1] if edge else Wh[3])
            for ly in range(368 + dy, 374 + dy, 2):
                st.rect(px0 + dx + 4 + sk * (ly - 366 - dy) // 9, ly, px0 + dx + 13 + sk * (ly - 366 - dy) // 9, ly, Wh[0])
            st.dark(px0 + dx + sk, 376 + dy, px0 + dx + 18 + sk, 376 + dy, 1)
        st.sticker(px0 + 58, 380, "gold", 6, text=False)
        st.sticker(px0 - 24, 394, "pink", 6, text=False)
    # Предметы у стены на тех же местах, что бочки и ящики пиратов (стопка у лифта сдвинута влево).
    for (kind, px) in (("jug", 20), ("jug", 44), ("box", 290), ("bin", 600), ("bin", 618), ("pile", 680),
                       ("box", 870), ("box", 898), ("jug", 1150), ("pile", 1380), ("jug", 1590)):
        yb = WALL_Y + 8
        st.dark(px - 12 if kind != "box" else px, yb + 1, px + (14 if kind != "box" else 34), yb + 2, 1, dither=True)
        if kind == "jug":
            st.jug(px, yb)
        elif kind == "bin":
            st.bin(px, yb)
        elif kind == "box":
            st.carton(px, yb)
        else:
            st.folders(px, yb)
    return st.c, st.p.colors


# Имя класса улицы у зеркала (`space_brawl16.Deck`): то же публичное имя для сборщика.
Deck = Floor


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки цвета стикера и бумаги, волна голубая как экран, пыль
    бумажной трухой; стрелка «вперёд» красная, чтобы не терялась на зелёном ковролине."""
    p = Pal(OUTLINE)
    p.add("white", [0xB7BFCF, 0xDCE2EC, 0xF4F5F8, 0xFFFFFF])
    if go:
        p.add("gold", [0x8A1A1C, 0xDA3A36, 0xF87A5A, 0xFFD0B0])
    else:
        p.add("gold", [0x9A6414, 0xE0A428, 0xF6CD4C, 0xFFF6B0])
    p.add("blue", [0x314A92, 0x58B2DC, 0x9AD4EC, 0xE0F6FC])
    p.add("dust", [0x7A8294, 0xA4ACBC, 0xC8CEDA, 0xE8EAF0])
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
        import office16
        office16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own(), scale=1, max_w=FW * 12)
